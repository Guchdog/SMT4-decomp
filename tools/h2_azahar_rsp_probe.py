#!/usr/bin/env python3
"""Bounded same-value ARM r0 RSP probe for an isolated Azahar CLI process.

The command stages a fresh runtime and a minimal local user directory containing
only approved system seed files, launches that staged executable, and never
sends guest memory writes or host input.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import unicodedata
import uuid

EXPECTED_AZAHAR_SHA256 = "c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb"
PINNED_AZAHAR_RPC_SHA256 = "513fa299c51c08645176f1658d277f9d5297e3f12f182075544e35d7284aa765"
TITLE_ID = "00040000000e5c00"
BREAKPOINT = 0x001E989C  # title-main callback entry, exercised without menu input
FORBIDDEN_PORTS = {24689}
PROFILE_SEED_FILES = (
    Path("sysdata/mac.txt"),
    Path("nand/data/00000000000000000000000000000000/sysdata/00010017/00000000/config"),
)


class ProbeError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_manifest(root: Path, excluded_top_level: set[str] | None = None) -> list[dict]:
    excluded = {name.casefold() for name in (excluded_top_level or set())}
    result = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0].casefold() in excluded:
            continue
        result.append({"path": relative.as_posix(), "size": path.stat().st_size, "sha256": sha256(path)})
    return result


def copy_pinned_package_assets(source_root: Path, app_dir: Path) -> list[dict]:
    """Copy only package extras proven present in the pinned build bundle."""
    source = source_root / "scripting" / "AzaharRPC.py"
    if not source.is_file():
        raise ProbeError(f"pinned scripting package asset is missing: {source}")
    source_hash = sha256(source)
    if source_hash != PINNED_AZAHAR_RPC_SHA256:
        raise ProbeError("installed AzaharRPC.py differs from the pinned 2126.2 source")
    destination = app_dir / "scripting" / "AzaharRPC.py"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    staged_hash = sha256(destination)
    if staged_hash != source_hash:
        raise ProbeError("staged AzaharRPC.py hash mismatch")
    return [{
        "relative_path": "scripting/AzaharRPC.py",
        "source": str(source.resolve()),
        "destination": str(destination.resolve()),
        "source_sha256": source_hash,
        "staged_sha256": staged_hash,
        "provenance": "exact SHA-256 match to dist/scripting/AzaharRPC.py at pinned 2126.2 commit; CMake copies dist/scripting into build/bundle and the Windows installer embeds build/bundle verbatim",
        "role": "bundled optional RPC client library; not used by the GDB probe",
    }]


def checksum(payload: bytes) -> int:
    return sum(payload) & 0xFF


def frame(payload: bytes) -> bytes:
    return b"$" + payload + b"#" + f"{checksum(payload):02x}".encode("ascii")


def parse_frame(packet: bytes) -> bytes:
    if len(packet) < 4 or packet[:1] != b"$" or packet[-3:-2] != b"#":
        raise ProbeError("malformed RSP frame")
    payload = packet[1:-3]
    try:
        received = int(packet[-2:], 16)
    except ValueError as exc:
        raise ProbeError("malformed RSP checksum") from exc
    if received != checksum(payload):
        raise ProbeError("RSP checksum mismatch")
    return payload


def r0_raw(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError("r0 must be a 32-bit ARM register")
    return value.to_bytes(4, "little")


def decode_r0(raw_hex: bytes) -> int:
    try:
        raw = bytes.fromhex(raw_hex.decode("ascii"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProbeError("invalid r0 register encoding") from exc
    if len(raw) != 4:
        raise ProbeError(f"expected 4-byte r0 value, got {len(raw)} bytes")
    return int.from_bytes(raw, "little")


class Rsp:
    def __init__(self, sock: socket.socket, timeout: float = 5.0):
        self.sock = sock
        self.timeout = timeout
        self.sock.settimeout(timeout)

    def _exact(self, count: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < count:
            part = self.sock.recv(count - len(chunks))
            if not part:
                raise ProbeError("RSP peer closed the connection")
            chunks.extend(part)
        return bytes(chunks)

    def _packet(self) -> bytes:
        while self._exact(1) != b"$":
            pass
        payload = bytearray()
        while True:
            char = self._exact(1)
            if char == b"#":
                break
            payload.extend(char)
        tail = self._exact(2)
        packet = b"$" + bytes(payload) + b"#" + tail
        decoded = parse_frame(packet)
        self.sock.sendall(b"+")
        return decoded

    def request(self, payload: bytes, expected: bytes | None = None) -> bytes:
        self.sock.sendall(frame(payload))
        ack = self._exact(1)
        if ack != b"+":
            raise ProbeError(f"unexpected RSP acknowledgement {ack!r}")
        reply = self._packet()
        if expected is not None and reply != expected:
            raise ProbeError(f"unexpected RSP reply to {payload!r}: {reply!r}, expected {expected!r}")
        return reply

    def continue_to_stop(self) -> bytes:
        self.sock.sendall(frame(b"c"))
        ack = self._exact(1)
        if ack != b"+":
            raise ProbeError(f"unexpected continue acknowledgement {ack!r}")
        reply = self._packet()
        if not reply.startswith(b"T"):
            raise ProbeError(f"continue returned unexpected stop reply {reply!r}")
        return reply


def reserve_port(port: int) -> None:
    if port in FORBIDDEN_PORTS or not 1024 <= port <= 65535:
        raise ProbeError(f"refusing forbidden or invalid GDB port {port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise ProbeError(f"loopback port {port} is not free") from exc


def provision_profile(seed_root: Path, user_dir: Path) -> list[dict]:
    seed_root = seed_root.resolve(strict=True)
    if not seed_root.is_dir():
        raise ProbeError(f"profile seed is not a directory: {seed_root}")
    if not user_dir.is_dir() or any(user_dir.iterdir()):
        raise ProbeError(f"staged user directory must exist and be empty: {user_dir}")
    records = []
    for relative in PROFILE_SEED_FILES:
        source = seed_root / relative
        if not source.is_file():
            raise ProbeError(f"approved profile seed file is missing: {source}")
        resolved_source = source.resolve(strict=True)
        if not resolved_source.is_relative_to(seed_root):
            raise ProbeError(f"profile seed file resolves outside the seed root: {source}")
        source_before = sha256(resolved_source)
        destination = user_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resolved_source, destination)
        staged_hash = sha256(destination)
        source_after_copy = sha256(resolved_source)
        if staged_hash != source_before or source_after_copy != source_before:
            raise ProbeError(f"profile seed copy/hash check failed: {relative.as_posix()}")
        records.append({
            "relative_path": relative.as_posix(),
            "source": str(resolved_source),
            "destination": str(destination.resolve()),
            "source_sha256_before": source_before,
            "staged_sha256": staged_hash,
            "source_sha256_after_copy": source_after_copy,
            "source_unchanged_after_copy": source_before == source_after_copy,
        })
    actual = {path.relative_to(user_dir).as_posix() for path in user_dir.rglob("*") if path.is_file()}
    expected = {relative.as_posix() for relative in PROFILE_SEED_FILES}
    if actual != expected:
        raise ProbeError(f"staged user tree contains unexpected file set: {sorted(actual)}")
    return records


def _stage_game_file(source: Path, destination: Path, *, hardlink: bool = False) -> None:
    """Stage a game image by copy (default) or immutable same-volume hard link."""
    if hardlink:
        try:
            os.link(source, destination)
        except OSError as exc:
            raise ProbeError(f"could not hard-link staged game image: {exc}") from exc
    else:
        shutil.copy2(source, destination)


def stage_runtime(source_exe: Path, source_game: Path, profile_seed: Path,
                  run_dir: Path, *, hardlink_game: bool = False
                  ) -> tuple[Path, Path, list[dict], list[dict], list[dict], bool]:
    source_exe = source_exe.resolve(strict=True)
    source_game = source_game.resolve(strict=True)
    run_dir = run_dir.resolve()
    if run_dir.exists():
        raise ProbeError(f"staging destination already exists: {run_dir}")
    if source_exe.name.lower() != "azahar.exe":
        raise ProbeError("source executable must be named azahar.exe")
    if sha256(source_exe).lower() != EXPECTED_AZAHAR_SHA256:
        raise ProbeError("source Azahar executable SHA-256 does not match pinned input")
    run_dir.mkdir(parents=True)
    app_dir = run_dir / "app"
    app_dir.mkdir()
    # Qt runtime dependencies are top-level DLLs plus its plugin tree. Do not
    # copy source user data, logs, saves, title images, or other game inputs.
    shutil.copy2(source_exe, app_dir / "azahar.exe")
    for item in source_exe.parent.iterdir():
        if item.is_file() and item.suffix.lower() == ".dll":
            shutil.copy2(item, app_dir / item.name)
    plugins = source_exe.parent / "plugins"
    if plugins.is_dir():
        shutil.copytree(plugins, app_dir / "plugins")
    package_assets = copy_pinned_package_assets(source_exe.parent, app_dir)
    source_qt_conf = source_exe.parent / "qt.conf"
    qt_conf_in_source_package = source_qt_conf.is_file()
    if qt_conf_in_source_package:
        shutil.copy2(source_qt_conf, app_dir / "qt.conf")
    user_dir = app_dir / "user"
    user_dir.mkdir()
    profile_files = provision_profile(profile_seed, user_dir)
    staged_game = run_dir / "pinned-title.cci"
    _stage_game_file(source_game, staged_game, hardlink=hardlink_game)
    runtime_manifest = file_manifest(app_dir, excluded_top_level={"user"})
    return app_dir / "azahar.exe", staged_game, profile_files, package_assets, runtime_manifest, qt_conf_in_source_package


def azahar_command(executable: Path, port: int, game: Path) -> list[str]:
    """Use the short pinned-frontend GDB option and the exact game path."""
    if not 1024 <= port <= 65535:
        raise ProbeError(f"invalid GDB port {port}")
    return [str(executable), "-g", str(port), str(game)]


def listener_owner(port: int) -> int | None:
    """Return the sole loopback TCP listener PID using bounded native netstat."""
    if not 1 <= int(port) <= 65535:
        raise ProbeError(f"invalid GDB port {port}")
    command = ["netstat.exe", "-ano", "-p", "tcp"]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding=_netstat_output_encoding(), errors="strict",
                                timeout=3, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ProbeError("timed out querying Windows TCP listener owners") from exc
    except (UnicodeError, LookupError) as exc:
        raise ProbeError(f"could not decode Windows TCP listener output: {exc}") from exc
    except OSError as exc:
        raise ProbeError(f"could not query Windows TCP listener owners: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or f"netstat exit {result.returncode}"
        raise ProbeError(f"could not verify GDB listener owner: {detail}")
    rows = parse_netstat_listener_rows(result.stdout)
    matches = [(address, owner) for address, local_port, owner in rows
               if local_port == int(port)]
    if not matches:
        return None
    for address, _owner in matches:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ProbeError(f"GDB listener has an invalid local address: {address!r}") from exc
        if not parsed.is_loopback:
            raise ProbeError(f"GDB listener is not loopback-only: {address!r}")
    owners = {owner for _address, owner in matches}
    if len(owners) != 1:
        raise ProbeError(f"selected loopback port {port} has multiple listener owners: {sorted(owners)}")
    return next(iter(owners))


_NETSTAT_STATES = {
    "CLOSED", "CLOSE_WAIT", "CLOSING", "DELETE_TCB", "ESTABLISHED",
    "FIN_WAIT_1", "FIN_WAIT_2", "LAST_ACK", "LISTENING", "SYN_RECEIVED",
    "SYN_SENT", "TIME_WAIT",
}
_NETSTAT_HEADER_FIELDS = (
    "proto", "local", "address", "foreign", "address", "state", "pid",
)
_NETSTAT_HEADER_FIELDS_SPANISH = (
    "proto", "direccion", "local", "direccion", "remota", "estado", "pid",
)


def _netstat_output_encoding() -> str:
    """Use the Windows OEM code page used by netstat.exe."""
    if os.name != "nt":
        return "utf-8"
    get_oem_cp = ctypes.windll.kernel32.GetOEMCP
    get_oem_cp.restype = ctypes.c_uint
    return f"cp{get_oem_cp()}"


def _normalize_header_field(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _parse_netstat_endpoint(value: str) -> tuple[str, int]:
    """Parse a numeric netstat endpoint, including bracketed IPv6 addresses."""
    if value == "*:*":
        return "*", 0
    if ":" not in value:
        raise ProbeError(f"malformed netstat endpoint {value!r}")
    host, port_text = value.rsplit(":", 1)
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    if not host or not port_text.isascii() or not port_text.isdigit():
        raise ProbeError(f"malformed netstat endpoint {value!r}")
    endpoint_port = int(port_text)
    if not 0 <= endpoint_port <= 65535:
        raise ProbeError(f"invalid port in netstat endpoint {value!r}")
    if host != "*":
        try:
            ipaddress.ip_address(host)
        except ValueError as exc:
            raise ProbeError(f"malformed netstat address {host!r}") from exc
    return host, endpoint_port


def parse_netstat_listener_rows(output: str) -> list[tuple[str, int, int]]:
    """Parse `netstat -ano -p tcp` rows as (local_address, port, PID).

    Blank/header lines are ignored, while malformed TCP rows fail closed.
    """
    if not isinstance(output, str):
        raise ProbeError("netstat output must be text")
    saw_header = False
    listeners: list[tuple[str, int, int]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        fields = line.split()
        if fields[0].casefold() == "proto":
            normalized_fields = tuple(_normalize_header_field(field) for field in fields)
            if normalized_fields not in {
                    _NETSTAT_HEADER_FIELDS, _NETSTAT_HEADER_FIELDS_SPANISH}:
                raise ProbeError(f"malformed netstat header {line!r}")
            if saw_header:
                raise ProbeError("netstat output contains a duplicate Proto header")
            saw_header = True
            continue
        if fields[0].casefold() != "tcp":
            continue
        if not saw_header or len(fields) != 5:
            raise ProbeError(f"malformed netstat TCP row {line!r}")
        local_endpoint, foreign_endpoint, state, pid_text = fields[1:]
        if (state.upper() not in _NETSTAT_STATES or not pid_text.isascii()
                or not pid_text.isdigit()):
            raise ProbeError(f"malformed netstat TCP row {line!r}")
        local_address, local_port = _parse_netstat_endpoint(local_endpoint)
        _parse_netstat_endpoint(foreign_endpoint)
        if state.upper() == "LISTENING":
            pid = int(pid_text)
            if pid <= 0 or not 1 <= local_port <= 65535:
                raise ProbeError(f"malformed netstat listener row {line!r}")
            listeners.append((local_address, local_port, pid))
    if not saw_header:
        raise ProbeError("netstat output is missing its Proto header")
    return listeners


def staged_log_evidence(app_dir: Path, game_path: Path) -> tuple[bool, str]:
    user_dir = (app_dir / "user").resolve()
    expected_game = str(game_path.resolve()).lower()
    all_text = []
    for path in user_dir.rglob("*"):
        if not path.is_file() or not (path.suffix.lower() in {".log", ".txt"} and "log" in path.name.lower()):
            continue
        try:
            all_text.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    blob = "\n".join(all_text).lower()
    path_ok = str(user_dir).lower() in blob
    game_ok = expected_game in blob or Path(expected_game).name in blob
    return path_ok and game_ok, blob


def capture_user_tree(user_dir: Path) -> dict:
    files = file_manifest(user_dir)
    directories = sorted(path.relative_to(user_dir).as_posix() for path in user_dir.rglob("*") if path.is_dir())
    selected = {}
    for label, relative in (("azahar_log", Path("log/azahar_log.txt")),
                            ("qt_config", Path("config/qt-config.ini"))):
        path = user_dir / relative
        if path.is_file():
            raw = path.read_bytes()
            selected[label] = {
                "path": str(path.resolve()),
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "text_tail": raw.decode("utf-8", "replace")[-32768:],
            }
        else:
            selected[label] = None
    return {"root": str(user_dir.resolve()), "directories": directories, "files": files, "selected": selected}


def capture_windows_application_errors(pid: int, started_at: datetime, executable: Path) -> dict:
    start_text = started_at.astimezone(timezone.utc).isoformat()
    escaped_path = str(executable).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; try { "
        "$qErrors=@(); "
        f"$start=[DateTimeOffset]::Parse('{start_text}').LocalDateTime; "
        "$events=@(Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=$start} -MaxEvents 500 -ErrorAction SilentlyContinue -ErrorVariable qErrors); "
        "if($qErrors.Count -gt 0 -and !($qErrors.Count -eq 1 -and $qErrors[0].FullyQualifiedErrorId -like 'NoMatchingEventsFound*')) { throw ($qErrors | ForEach-Object { $_.ToString() } | Out-String) }; "
        f"$path='{escaped_path}'; $pidHex=('0x{{0:x}}' -f {int(pid)}); "
        "$hits=@($events | Where-Object { $_.Message -like ('*'+$path+'*') -or $_.Message -like ('*'+$pidHex+'*') -or ($_.ProviderName -in @('Application Error','Windows Error Reporting') -and $_.Message -like '*azahar*') } | Select-Object TimeCreated,Id,ProviderName,LevelDisplayName,Message); "
        "if($hits.Count -eq 0) { [Console]::Out.WriteLine('NO_MATCHING_EVENTS'); exit 0 }; "
        "$hits | ConvertTo-Json -Depth 4 -Compress; exit 0 "
        "} catch { [Console]::Error.WriteLine($_.ToString()); exit 2 }"
    )
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                                capture_output=True, text=True, timeout=12, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "query_failed", "error": str(exc), "events": []}
    if result.returncode != 0:
        return {"status": "query_failed", "exit_code": result.returncode,
                "stderr": result.stderr[-8000:], "events": []}
    output = result.stdout.strip()
    if output == "NO_MATCHING_EVENTS" or not output:
        return {"status": "no_matching_events", "events": []}
    try:
        events = json.loads(output)
    except json.JSONDecodeError:
        return {"status": "captured_unparsed", "raw": output[-32000:], "events": []}
    if isinstance(events, dict):
        events = [events]
    return {"status": "captured", "events": events}


def qt_plugin_diagnostics(stderr_lines: list[str]) -> list[str]:
    return [line for line in stderr_lines if any(token in line.casefold()
            for token in ("qt", "plugin", "qwindows", "platform", "factoryloader"))][-200:]


def connect_and_probe(port: int, timeout: float) -> dict:
    sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    rsp = Rsp(sock, timeout=timeout)
    attached = False
    breakpoint_set = False
    result = {}
    try:
        supported = rsp.request(b"qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+")
        if not supported or supported.startswith(b"E"):
            raise ProbeError(f"unexpected qSupported reply {supported!r}")
        if rsp.request(b"!") != b"OK":
            raise ProbeError("extended-mode request was not accepted")
        proc_reply = rsp.request(b"qfProcessInfo")
        if not proc_reply.startswith(b"pid:"):
            raise ProbeError(f"cannot identify isolated emulated process: {proc_reply!r}")
        fields = dict(part.split(b":", 1) for part in proc_reply.split(b";") if b":" in part)
        pid_hex = fields.get(b"pid", b"")
        if not pid_hex or any(c not in b"0123456789abcdefABCDEF" for c in pid_hex):
            raise ProbeError(f"invalid isolated emulated PID field {pid_hex!r}")
        stop = rsp.request(b"vAttach;" + pid_hex)
        if not stop.startswith(b"T"):
            raise ProbeError(f"attach to isolated emulated PID returned {stop!r}")
        attached = True
        if rsp.request(f"Z0,{BREAKPOINT:x},4".encode("ascii")) != b"OK":
            raise ProbeError("title callback breakpoint was not accepted")
        breakpoint_set = True
        stop = rsp.continue_to_stop()
        pc = decode_r0(rsp.request(b"p0f"))
        if pc != BREAKPOINT:
            raise ProbeError(f"stopped at unexpected PC {pc:#x}, stop reply {stop!r}")
        before_raw = rsp.request(b"p0")
        before = decode_r0(before_raw)
        if rsp.request(b"P0=" + r0_raw(before).hex().encode("ascii")) != b"OK":
            raise ProbeError("same-value r0 P packet was not accepted")
        after = decode_r0(rsp.request(b"p0"))
        if after != before:
            raise ProbeError(f"r0 readback changed: before={before:#x}, after={after:#x}")
        result = {"emulated_pid_hex": pid_hex.decode("ascii"), "stop_reply": stop.decode("ascii", "replace"),
                  "pc": f"0x{pc:08x}",
                  "r0_before": f"0x{before:08x}", "p0_reply": "OK", "r0_after": f"0x{after:08x}"}
    finally:
        try:
            if breakpoint_set:
                rsp.request(f"z0,{BREAKPOINT:x},4".encode("ascii"), expected=b"OK")
        finally:
            try:
                if attached:
                    rsp.request(b"D", expected=b"OK")
            finally:
                sock.close()
    return result


def run(args: argparse.Namespace) -> dict:
    record = {"status": "failed", "error": None}
    process = None
    try:
        return _run(args, record)
    except (ProbeError, OSError, subprocess.SubprocessError) as exc:
        record["status"] = "failed"
        record["error"] = str(exc)
        return record


def _run(args: argparse.Namespace, record: dict) -> dict:
    if args.port in FORBIDDEN_PORTS:
        raise ProbeError("historical GDB port 24689 is forbidden")
    reserve_port(args.port)
    source_exe = Path(args.azahar).resolve(strict=True)
    source_game = Path(args.game).resolve(strict=True)
    profile_seed = Path(args.profile_seed).resolve(strict=True)
    run_dir = Path(args.run_dir) if args.run_dir else Path(args.output_root) / ("probe-" + uuid.uuid4().hex)
    run_dir = run_dir.resolve()
    (executable, staged_game, profile_files, package_assets,
     runtime_files_before, qt_conf_in_source_package) = stage_runtime(
        source_exe, source_game, profile_seed, run_dir)
    record.update({"status": "staged", "run_dir": str(run_dir), "executable": str(executable),
                   "executable_sha256": sha256(executable), "source_executable_sha256": sha256(source_exe),
                   "game": str(staged_game), "source_game_sha256": sha256(source_game),
                   "staged_game_sha256": sha256(staged_game), "user_profile": str(executable.parent / "user"),
                   "profile_seed": str(profile_seed), "profile_seed_files": profile_files,
                   "pinned_package_assets": package_assets,
                   "qt_conf_present_in_source_package": qt_conf_in_source_package,
                   "runtime_files_before": runtime_files_before,
                   "port": args.port, "breakpoint": f"0x{BREAKPOINT:08x}"})
    if record["executable_sha256"] != EXPECTED_AZAHAR_SHA256 or record["staged_game_sha256"] != record["source_game_sha256"]:
        raise ProbeError("staged input hash validation failed")
    reserve_port(args.port)
    env = os.environ.copy()
    stdout_path = run_dir / "azahar.stdout.log"
    stderr_path = run_dir / "azahar.stderr.log"
    stdout_stream = stdout_path.open("x", encoding="utf-8", errors="replace")
    stderr_stream = stderr_path.open("x", encoding="utf-8", errors="replace")
    command = azahar_command(executable, args.port, staged_game)
    launch_started_at = datetime.now(timezone.utc)
    record["launch_started_at"] = launch_started_at.isoformat()
    record["qt_debug_plugins_enabled"] = True
    env["QT_DEBUG_PLUGINS"] = "1"
    process = subprocess.Popen(command,
                               cwd=executable.parent, env=env, stdin=subprocess.DEVNULL,
                               stdout=stdout_stream, stderr=stderr_stream, shell=False)
    record["host_pid"] = process.pid
    record["command"] = command
    record["status"] = "launched"
    deadline = time.monotonic() + args.startup_timeout
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise ProbeError(f"staged probe exited before GDB readiness (code {process.returncode})")
            if listener_owner(args.port) is not None:
                break
            time.sleep(0.25)
        if listener_owner(args.port) != process.pid:
            raise ProbeError("selected port is not owned exclusively by the launched staged process")
        log_ok, _ = staged_log_evidence(executable.parent, staged_game)
        if not log_ok:
            raise ProbeError("staged Azahar logs do not confirm both local profile and pinned game paths")
        record["profile_verified"] = True
        record["listener_owner_pid"] = process.pid
        record.update(connect_and_probe(args.port, args.packet_timeout))
        record["status"] = "passed"
        return record
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        stdout_stream.flush()
        stderr_stream.flush()
        stdout_stream.close()
        stderr_stream.close()
        record["process_exit_code"] = process.returncode
        record["launch_ended_at"] = datetime.now(timezone.utc).isoformat()
        try:
            stdout_lines = stdout_path.read_text(encoding="utf-8", errors="replace").splitlines()
            record["stdout_tail"] = stdout_lines[-40:]
        except OSError as exc:
            record["stdout_tail"] = [f"diagnostic read failed: {exc}"]
        try:
            stderr_lines = stderr_path.read_text(encoding="utf-8", errors="replace").splitlines()
            record["stderr_tail"] = stderr_lines[-40:]
            record["qt_plugin_diagnostics"] = qt_plugin_diagnostics(stderr_lines)
        except OSError as exc:
            stderr_lines = []
            record["stderr_tail"] = [f"diagnostic read failed: {exc}"]
            record["qt_plugin_diagnostics"] = []
        record["windows_application_errors"] = capture_windows_application_errors(
            process.pid, launch_started_at, executable)
        record["user_tree_after_run"] = capture_user_tree(executable.parent / "user")
        source_exe_after = sha256(source_exe)
        staged_exe_after = sha256(executable)
        source_game_after = sha256(source_game)
        staged_game_after = sha256(staged_game)
        record["source_executable_sha256_after_run"] = source_exe_after
        record["staged_executable_sha256_after_run"] = staged_exe_after
        record["source_game_sha256_after_run"] = source_game_after
        record["staged_game_sha256_after_run"] = staged_game_after
        input_hashes_unchanged = (
            source_exe_after == record["source_executable_sha256"] == staged_exe_after
            and source_game_after == record["source_game_sha256"] == staged_game_after
        )
        record["executable_and_game_hashes_unchanged_after_run"] = input_hashes_unchanged
        runtime_files_after = file_manifest(executable.parent, excluded_top_level={"user"})
        record["runtime_files_after"] = runtime_files_after
        record["runtime_files_unchanged_after_run"] = runtime_files_after == runtime_files_before
        unchanged = True
        for item in record.get("profile_seed_files", []):
            after = sha256(Path(item["source"]))
            item["source_sha256_after_run"] = after
            item["source_unchanged_after_run"] = after == item["source_sha256_before"]
            unchanged = unchanged and item["source_unchanged_after_run"]
        record["profile_seed_unchanged_after_run"] = unchanged
        if not unchanged or not input_hashes_unchanged or not record["runtime_files_unchanged_after_run"]:
            record["status"] = "failed"
            record["error"] = "staged/source inputs or runtime file hashes changed during the run"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--azahar", required=True, help="pinned source azahar.exe")
    parser.add_argument("--game", required=True, help="pinned US SMT IV CCI")
    parser.add_argument("--profile-seed", default="build/h2-runtime/profile-pristine-user",
                        help="pristine seed root; only the two approved system files are copied")
    parser.add_argument("--output-root", default="build/h2-runtime/h2-azahar-rsp-probe")
    parser.add_argument("--run-dir", help="new, non-existing staging directory")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--startup-timeout", type=float, default=30.0)
    parser.add_argument("--packet-timeout", type=float, default=5.0)
    parser.add_argument("--record", help="write JSON result to a new record path")
    args = parser.parse_args(argv)
    record = run(args)
    print(json.dumps(record, indent=2), file=sys.stdout if record.get("status") == "passed" else sys.stderr)
    code = 0 if record.get("status") == "passed" else 2
    try:
        return code
    finally:
        if args.record:
            path = Path(args.record)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                print(f"refusing to overwrite record {path}", file=sys.stderr)
            else:
                path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
