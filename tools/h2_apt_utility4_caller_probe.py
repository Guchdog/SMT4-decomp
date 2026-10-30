#!/usr/bin/env python3
"""Bounded read-only RSP capture of the APT Utility-4 guest helper.

The runner stages a private Azahar package, a minimal disposable user profile,
and only the hash-pinned disposable save fixture. It sets one ARM software
breakpoint at 0x002C0EE0, reads r0-r15 for at most four hits, then clears the
breakpoint and removes only its own staged child. It sends no explicit RSP
memory-write packets (M/P/X) or logical input. Z0/z0 are separate transient
software-breakpoint operations and are recorded independently.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath, PureWindowsPath
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid

try:
    import h2_azahar_rsp_probe as shared
except ModuleNotFoundError:  # imported as tools.h2_... in unittest
    from tools import h2_azahar_rsp_probe as shared


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "h2-apt-utility4-caller-probe"
RUNTIME_TASK_ID = "h2-apt-utility4-caller-probe-runtime"
ALLOWED_TASK_IDS = {TASK_ID, RUNTIME_TASK_ID}
OUTPUT_REL = Path("build/agent-work/H2-semantic/h2-apt-utility4-caller-probe/run-002")
TASK_REL = OUTPUT_REL / "task.json"
CODE_REL = Path("build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/reference/code.bin")
RUN017_LOG_REL = Path("build/h2-runtime/h2-state2-dispatch-capture/run-017/azahar-user.log")
RUN028_LOG_REL = Path("build/h2-runtime/h2-state2-nested-callback-capture/run-028/azahar-user.log")
BREAKPOINT = 0x002C0EE0
CODE_BASE = 0x00100000
CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
GAME_SHA256 = "9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2"
SAVE_FIXTURE_SHA256 = "6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9"
RUN017_LOG_SHA256 = "987b60d6f3e7361eb59df6fa057ddb981fdb57310effa0d166d70f9b552ad245"
RUN028_LOG_SHA256 = "08ac8e83968aa42b63a0f40de39ff3a42dc86a74bdf6e0308c1f665c05b80439"
UTILITY4_LINE = re.compile(
    rb"called command=0X00000004, input_size=0X00000001, output_size=0X00000001"
)
CALLERS = {0x00102188: 0x00102184, 0x001051E0: 0x001051DC}
EXPECTED_CALLER_ADDRESSES = (0x00102184, 0x001051DC)
SAVE_REL = Path(
    "sdmc/Nintendo 3DS/00000000000000000000000000000000/"
    "00000000000000000000000000000000/title/00040000/000e5c00/"
    "data/00000001/sdds4game1.sav"
)
FORBIDDEN_PORTS = {24689}
REGISTER_NAMES = tuple(f"r{index}" for index in range(16))
AZAHAR_MANIFEST_REL = "build/agent-work/H2-semantic/h2-private-azahar-source/h2-delivery-manifest.json"
AZAHAR_RUNTIME_PACKAGE_PIN_REL = Path("docs/agent-work/h2-azahar-runtime-package-pin.json")
AZAHAR_EXECUTABLE_REL = "build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe"
AZAHAR_COMPAT_EXECUTABLE_REL = "build/h2-runtime/autonomous-verify-run001/original/app/azahar.exe"
AZAHAR_COMPAT_PRIOR_RUN_REL = "build/h2-runtime/autonomous-verify-run001/autonomous-gdb-verification.json"
PROFILE_SEED_ROOT_REL = Path("build/h2-runtime/profile-pristine-user")
PROFILE_SEED_PIN_RELS = tuple((PROFILE_SEED_ROOT_REL / relative).as_posix()
                              for relative in shared.PROFILE_SEED_FILES)
CLEANUP_GRACE_SECONDS = 3.0


class ProbeError(shared.ProbeError):
    pass


def sha256(path: Path) -> str:
    return shared.sha256(path)


class DeadlineExpired(ProbeError):
    """An RSP operation ran out of its shared monotonic budget."""


def verify_packet_inputs(task_packet: dict, repo_root: Path = ROOT,
                         required_paths: tuple[str, ...] = ()) -> dict[str, dict]:
    """Recompute every declared packet input and reject traversal/missing pins."""
    repo_root = repo_root.resolve(strict=True)
    declared = task_packet.get("input_sha256")
    if not isinstance(declared, dict) or not declared:
        raise ProbeError("task packet has no input_sha256 map")
    normalized: dict[str, tuple[str, str]] = {}
    for raw_path, expected in declared.items():
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ProbeError("task packet input path must be a nonempty relative string")
        rel_text = raw_path.replace("\\", "/")
        win_path = PureWindowsPath(rel_text)
        rel_path = Path(rel_text)
        if win_path.is_absolute() or win_path.drive or rel_path.is_absolute() or ".." in rel_path.parts:
            raise ProbeError(f"task packet input escapes repository root: {raw_path}")
        canonical = rel_path.as_posix()
        if canonical in normalized:
            raise ProbeError(f"duplicate normalized task input path: {raw_path}")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise ProbeError(f"invalid SHA-256 pin for task input: {raw_path}")
        normalized[canonical] = (raw_path, expected.lower())

    missing_pins = sorted(set(required_paths) - set(normalized))
    if missing_pins:
        raise ProbeError(f"task packet is missing required runtime input pins: {missing_pins}")

    evidence = {}
    for canonical, (raw_path, expected) in normalized.items():
        candidate = (repo_root / Path(canonical)).resolve(strict=True)
        if not candidate.is_relative_to(repo_root):
            raise ProbeError(f"task packet input resolves outside repository root: {raw_path}")
        if not candidate.is_file():
            raise ProbeError(f"task packet input is not a file: {raw_path}")
        observed = sha256(candidate)
        if observed != expected:
            raise ProbeError(f"task packet input SHA-256 mismatch: {raw_path}")
        evidence[canonical] = {"path": str(candidate), "sha256": observed,
                               "size": candidate.stat().st_size, "matches_packet": True}
    return evidence


def verify_profile_seed_manifest(profile_seed: Path, packet_inputs: dict[str, dict],
                                 repo_root: Path = ROOT) -> dict:
    """Require packet pins to equal the complete live disposable seed tree."""
    repo_root = repo_root.resolve(strict=True)
    seed_root = profile_seed.resolve(strict=True)
    if not seed_root.is_relative_to(repo_root) or not seed_root.is_dir():
        raise ProbeError("profile seed is outside the pinned repository build tree")
    pinned = {}
    for relative, evidence in packet_inputs.items():
        candidate = Path(evidence["path"]).resolve(strict=True)
        if candidate.is_relative_to(seed_root):
            pinned[candidate.relative_to(seed_root).as_posix()] = evidence["sha256"]
    live_rows = shared.file_manifest(seed_root)
    live = {row["path"]: row["sha256"] for row in live_rows}
    if set(pinned) != set(live):
        missing = sorted(set(live) - set(pinned))
        extra = sorted(set(pinned) - set(live))
        raise ProbeError(f"profile seed packet pin set differs from live seed: unpinned={missing}, absent={extra}")
    mismatches = sorted(path for path in live if pinned[path] != live[path])
    if mismatches:
        raise ProbeError(f"profile seed packet hashes differ from live seed: {mismatches}")
    manifest_sha256 = hashlib.sha256(
        json.dumps(live_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return {"status": "passed", "file_count": len(live),
            "manifest_sha256": manifest_sha256,
            "paths": [{"path": path, "sha256": live[path]} for path in sorted(live)]}


def remaining_seconds(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DeadlineExpired("absolute RSP deadline expired")
    return remaining


def connect_to_loopback(port: int, deadline: float, packet_timeout: float) -> socket.socket:
    remaining = min(remaining_seconds(deadline), packet_timeout)
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=remaining)
    except socket.timeout as exc:
        raise DeadlineExpired("RSP connection reached its monotonic deadline") from exc
    if time.monotonic() >= deadline:
        sock.close()
        raise DeadlineExpired("RSP connection completed after its monotonic deadline")
    return sock


class DeadlineRsp:
    """RSP client that clamps every send and recv to one absolute deadline."""

    def __init__(self, sock: socket.socket, deadline: float,
                 cleanup_grace: float = CLEANUP_GRACE_SECONDS,
                 packet_timeout: float = 5.0):
        self.sock = sock
        self.deadline = deadline
        self.cleanup_grace = cleanup_grace
        self.packet_timeout = packet_timeout
        self.cleanup_deadline: float | None = None
        self.continue_inflight = False
        self.deadline_expired = False

    def set_deadline(self, deadline: float) -> None:
        if deadline != self.deadline:
            raise ProbeError("RSP deadline cannot be reset or extended mid-session")

    def _active_deadline(self) -> float:
        return self.cleanup_deadline if self.cleanup_deadline is not None else self.deadline

    def _set_timeout(self) -> None:
        self.sock.settimeout(min(remaining_seconds(self._active_deadline()), self.packet_timeout))

    def _sendall(self, payload: bytes) -> None:
        self._set_timeout()
        try:
            self.sock.sendall(payload)
        except socket.timeout as exc:
            self.deadline_expired = True
            raise DeadlineExpired("RSP send reached its monotonic deadline") from exc
        remaining_seconds(self._active_deadline())

    def _exact(self, count: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < count:
            self._set_timeout()
            try:
                part = self.sock.recv(count - len(chunks))
            except socket.timeout as exc:
                self.deadline_expired = True
                raise DeadlineExpired("RSP receive reached its monotonic deadline") from exc
            if not part:
                raise ProbeError("RSP peer closed the connection")
            chunks.extend(part)
            remaining_seconds(self._active_deadline())
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
        decoded = shared.parse_frame(b"$" + bytes(payload) + b"#" + tail)
        self._sendall(b"+")
        return decoded

    def request(self, payload: bytes, expected: bytes | None = None) -> bytes:
        self._sendall(shared.frame(payload))
        ack = self._exact(1)
        if ack != b"+":
            raise ProbeError(f"unexpected RSP acknowledgement {ack!r}")
        reply = self._packet()
        if expected is not None and reply != expected:
            raise ProbeError(f"unexpected RSP reply to {payload!r}: {reply!r}, expected {expected!r}")
        return reply

    def continue_to_stop(self) -> bytes:
        self.continue_inflight = True
        self._sendall(shared.frame(b"c"))
        ack = self._exact(1)
        if ack != b"+":
            self.continue_inflight = False
            raise ProbeError(f"unexpected continue acknowledgement {ack!r}")
        reply = self._packet()
        self.continue_inflight = False
        if not reply.startswith(b"T"):
            raise ProbeError(f"continue returned unexpected stop reply {reply!r}")
        return reply

    def begin_cleanup_grace(self) -> None:
        if self.cleanup_deadline is None:
            self.cleanup_deadline = time.monotonic() + self.cleanup_grace

    def interrupt_for_cleanup(self) -> bytes:
        self.begin_cleanup_grace()
        self._sendall(b"\x03")
        reply = self._packet()
        self.continue_inflight = False
        return reply

    def close(self) -> None:
        self.sock.close()


def u32_at(data: bytes, address: int) -> int:
    if address & 3:
        raise ProbeError(f"unaligned ARM word address {address:#x}")
    offset = address - CODE_BASE
    if offset < 0 or offset + 4 > len(data):
        raise ProbeError(f"ARM address outside pinned code.bin: {address:#x}")
    return int.from_bytes(data[offset:offset + 4], "little")


def arm_bl_target(address: int, word: int) -> int | None:
    if word & 0x0F000000 != 0x0B000000:
        return None
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 1 << 24
    return (address + 8 + (displacement << 2)) & 0xFFFFFFFF


def direct_arm_bl_callers(data: bytes, target: int) -> list[int]:
    refs = []
    for offset in range(0, len(data) - 3, 4):
        address = CODE_BASE + offset
        word = int.from_bytes(data[offset:offset + 4], "little")
        if arm_bl_target(address, word) == target:
            refs.append(address)
    return refs


def static_contract(code_path: Path, run017_log: Path, run028_log: Path) -> dict:
    raw = code_path.read_bytes()
    code_hash = hashlib.sha256(raw).hexdigest()
    if code_hash != CODE_SHA256:
        raise ProbeError(f"pinned code.bin SHA-256 mismatch: {code_hash}")
    command_word = u32_at(raw, 0x002C0F08)
    wrapper_call = u32_at(raw, 0x002C0F1C)
    wrapper = arm_bl_target(0x002C0F1C, wrapper_call)
    if command_word != 0xE3A00004 or wrapper != 0x002B5A1C:
        raise ProbeError("pinned helper no longer prepares command 4 and calls the APT wrapper")
    callers = direct_arm_bl_callers(raw, BREAKPOINT)
    if tuple(callers) != EXPECTED_CALLER_ADDRESSES:
        raise ProbeError(f"pinned direct A32 BL callers changed: {[hex(pc) for pc in callers]}")
    if any(pc & 3 for pc in callers) or BREAKPOINT & 1:
        raise ProbeError("ARM caller/target alignment check failed")

    logs = []
    for path, expected_hash, expected_count in (
        (run017_log, RUN017_LOG_SHA256, 4), (run028_log, RUN028_LOG_SHA256, 6452)
    ):
        log_hash = sha256(path)
        count = len(UTILITY4_LINE.findall(path.read_bytes()))
        if log_hash != expected_hash or count != expected_count:
            raise ProbeError(f"historical log pin/count mismatch for {path}")
        logs.append({
            "path": str(path.resolve()), "sha256": log_hash,
            "utility4_line_count": count,
            "scope": "HLE log count only; does not identify guest caller or command semantics",
        })
    return {
        "code_bin": {"path": str(code_path.resolve()), "sha256": code_hash,
                     "base": f"0x{CODE_BASE:08x}"},
        "helper": f"0x{BREAKPOINT:08x}",
        "helper_command_word": f"0x{command_word:08x}",
        "wrapper_call_target": f"0x{wrapper:08x}",
        "direct_arm_bl_callers": [f"0x{pc:08x}" for pc in callers],
        "expected_entry_lr": [f"0x{pc + 4:08x}" for pc in callers],
        "historical_utility4_logs": logs,
    }


def classify_lr(lr: int) -> dict:
    caller = CALLERS.get(lr)
    return {
        "lr": f"0x{lr:08x}",
        "classification": "known_direct_caller" if caller is not None else "unexpected_or_indirect",
        "caller_callsite": f"0x{caller:08x}" if caller is not None else None,
    }


def parse_listener_binding(output: str, port: int) -> dict | None:
    rows = [row for row in shared.parse_netstat_listener_rows(output) if row[1] == port]
    if not rows:
        return None
    if len(rows) != 1:
        raise ProbeError(f"expected one listener row for {port}, found {rows!r}")
    address, local_port, pid = rows[0]
    if address != "127.0.0.1":
        raise ProbeError(f"GDB listener must bind exactly 127.0.0.1, observed {address!r}")
    raw_row = None
    for line in output.splitlines():
        fields = line.strip().split()
        if len(fields) != 5 or fields[0].casefold() != "tcp":
            continue
        try:
            candidate_address, candidate_port = shared._parse_netstat_endpoint(fields[1])
        except shared.ProbeError:
            continue
        if (candidate_address == address and candidate_port == local_port
                and fields[3].upper() == "LISTENING" and fields[4] == str(pid)):
            raw_row = line.strip()
            break
    return {"local_address": address, "local_port": local_port, "pid": pid,
            "netstat_row": raw_row}


def listener_binding(port: int) -> dict | None:
    if not 1024 <= port <= 65535:
        raise ProbeError(f"invalid GDB port {port}")
    try:
        result = subprocess.run(["netstat.exe", "-ano", "-p", "tcp"], capture_output=True,
                                text=True, encoding=shared._netstat_output_encoding(), errors="strict",
                                timeout=3, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ProbeError("timed out querying Windows TCP listener binding") from exc
    except (OSError, UnicodeError, LookupError) as exc:
        raise ProbeError(f"could not query exact GDB listener binding: {exc}") from exc
    if result.returncode != 0:
        raise ProbeError(result.stderr.strip() or f"netstat exit {result.returncode}")
    return parse_listener_binding(result.stdout, port)


def validate_max_hits(max_hits: int) -> int:
    if isinstance(max_hits, bool) or not 1 <= max_hits <= 4:
        raise ProbeError("max_hits must be from 1 through 4")
    return max_hits


def derive_output_root(task_id: str, packet_root: Path, requested: Path | None = None) -> Path:
    packet_root = packet_root.resolve()
    default = packet_root if task_id == RUNTIME_TASK_ID else packet_root / "runtime-captures"
    output_root = requested.resolve() if requested is not None else default
    if output_root != packet_root and not output_root.is_relative_to(packet_root):
        raise ProbeError("output_root must remain inside the selected task packet output root")
    if task_id not in ALLOWED_TASK_IDS:
        raise ProbeError("unrecognized task packet output root")
    return output_root


REQUIRED_OFFLINE_GATES = (
    "h2_differential",
    "h2_caller_composition",
    "h3_caller_composition",
    "arm_thumb_interworking",
)
REQUIRED_INTERWORKING_FIELDS = (
    "checked_original_bl_targets",
    "checked_lock_return_site",
    "checked_lock_owner_store_site",
    "checked_lock_owner_poststore_site",
    "checked_dispatch_caller_byte_probe_instructions",
)


def validate_gate_attestation_document(document: dict, attestation_path: Path,
                                       packet_root: Path) -> dict:
    if document.get("schema_version") != 1 or document.get("task_id") != RUNTIME_TASK_ID:
        raise ProbeError("offline-gate attestation is not for the assigned runtime task")
    gates = document.get("gates")
    if not isinstance(gates, dict):
        raise ProbeError("offline-gate attestation has no gates object")
    records = []
    for name in REQUIRED_OFFLINE_GATES:
        entry = gates.get(name)
        if not isinstance(entry, dict) or entry.get("status") != "passed":
            raise ProbeError(f"required offline gate did not pass: {name}")
        result_counts = entry.get("result_counts")
        warnings = entry.get("source_identity_warnings")
        if not isinstance(result_counts, dict) or not result_counts:
            raise ProbeError(f"offline gate is missing result counts: {name}")
        if not isinstance(warnings, list):
            raise ProbeError(f"offline gate is missing the visible source-identity warnings list: {name}")
        interworking_fields = entry.get("interworking_fields")
        if name == "arm_thumb_interworking":
            if not isinstance(interworking_fields, dict) or any(
                    field not in interworking_fields for field in REQUIRED_INTERWORKING_FIELDS):
                raise ProbeError("ARM/Thumb gate is missing exact interworking evidence fields")
        report_path = Path(entry.get("report_path", ""))
        if not report_path.is_absolute():
            report_path = ROOT / report_path
        report_path = report_path.resolve(strict=True)
        if not report_path.is_relative_to(packet_root.resolve(strict=True)):
            raise ProbeError(f"offline gate report is outside the runtime packet output root: {name}")
        observed = sha256(report_path)
        if entry.get("sha256") != observed:
            raise ProbeError(f"offline gate report hash mismatch: {name}")
        records.append({"name": name, "status": "passed", "report_path": str(report_path),
                        "sha256": observed, "result_counts": result_counts,
                        "source_identity_warnings": warnings,
                        "interworking_fields": interworking_fields if name == "arm_thumb_interworking" else None})
    warning_count = sum(len(entry["source_identity_warnings"]) for entry in records)
    return {"path": str(attestation_path.resolve(strict=True)),
            "sha256": sha256(attestation_path), "gates": records,
            "source_identity_warning_count": warning_count,
            "status_summary": "passed_with_warnings" if warning_count else "passed"}


def _decode_reg(raw_hex: bytes, index: int) -> int:
    try:
        raw = bytes.fromhex(raw_hex.decode("ascii"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ProbeError(f"invalid r{index} register encoding") from exc
    if len(raw) != 4:
        raise ProbeError(f"expected 4-byte r{index} value, got {len(raw)} bytes")
    return int.from_bytes(raw, "little")


def read_registers(rsp, deadline: float | None = None) -> dict[str, int]:
    if deadline is not None and hasattr(rsp, "set_deadline"):
        rsp.set_deadline(deadline)
    result = {}
    for index, name in enumerate(REGISTER_NAMES):
        reply = rsp.request(f"p{index:x}".encode("ascii"))
        if not reply or reply.startswith(b"E"):
            raise ProbeError(f"RSP could not read {name}: {reply!r}")
        result[name] = _decode_reg(reply, index)
    return result


def continue_until_stop(rsp, deadline: float) -> tuple[bytes | None, str]:
    try:
        remaining_seconds(deadline)
    except DeadlineExpired:
        return None, "capture_timeout"
    if hasattr(rsp, "set_deadline"):
        rsp.set_deadline(deadline)
    try:
        return rsp.continue_to_stop(), "stopped"
    except (socket.timeout, DeadlineExpired):
        # A continue may already be running when its shared deadline expires.
        # Interrupt and all later cleanup packets share one bounded grace.
        inflight = getattr(rsp, "continue_inflight", True)
        if not inflight:
            return None, "capture_timeout"
        begin_cleanup = getattr(rsp, "begin_cleanup_grace", None)
        if begin_cleanup:
            begin_cleanup()
        try:
            interrupt = getattr(rsp, "interrupt_for_cleanup", None)
            if interrupt:
                interrupt()
            else:
                rsp.sock.sendall(b"\x03")
                rsp.sock.settimeout(CLEANUP_GRACE_SECONDS)
                rsp.timeout = CLEANUP_GRACE_SECONDS
                rsp._packet()
        except (OSError, shared.ProbeError) as exc:
            raise ProbeError(f"could not interrupt timed-out RSP continue: {exc}") from exc
        return None, "capture_timeout"


def collect_hits(rsp, max_hits: int, capture_timeout: float | None = None,
                 deadline: float | None = None) -> tuple[list[dict], str]:
    validate_max_hits(max_hits)
    if deadline is None:
        if capture_timeout is None or capture_timeout <= 0:
            raise ProbeError("capture_timeout must be positive")
        deadline = time.monotonic() + capture_timeout
    if hasattr(rsp, "set_deadline"):
        rsp.set_deadline(deadline)
    hits = []
    while len(hits) < max_hits:
        stop, reason = continue_until_stop(rsp, deadline)
        if stop is None:
            return hits, reason
        pc = _decode_reg(rsp.request(b"p0f"), 15)
        if pc != BREAKPOINT:
            raise ProbeError(f"RSP stopped at {pc:#010x}, expected {BREAKPOINT:#010x}: {stop!r}")
        registers = read_registers(rsp, deadline)
        if registers["r15"] != BREAKPOINT:
            raise ProbeError("PC changed between breakpoint validation and register snapshot")
        hits.append({
            "index": len(hits) + 1,
            "pc": f"0x{pc:08x}",
            "lr": classify_lr(registers["r14"]),
            "registers": {name: f"0x{value:08x}" for name, value in registers.items()},
            "stop_reply": stop.decode("ascii", "replace"),
        })
    return hits, "max_hits_reached"


def capture_session(rsp, max_hits: int, capture_timeout: float | None = None,
                    *, deadline: float | None = None, on_fatal=None) -> dict:
    validate_max_hits(max_hits)
    if deadline is None:
        if capture_timeout is None or capture_timeout <= 0:
            raise ProbeError("capture_timeout must be positive")
        deadline = time.monotonic() + capture_timeout
    if hasattr(rsp, "set_deadline"):
        rsp.set_deadline(deadline)
    result = {"hits": [], "capture_stop": None, "breakpoint_set": False,
              "breakpoint_cleared": False, "attached": False, "detached": False,
              "cleanup_errors": [], "explicit_rsp_memory_write_packets": [],
              "logical_inputs_injected": 0,
              "software_breakpoint": {"address": f"0x{BREAKPOINT:08x}", "insert_packet": "Z0",
                                      "remove_packet": "z0", "transient_target_code_effect": True}}
    original_error = None
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
        result["emulated_pid_hex"] = pid_hex.decode("ascii")
        stop = rsp.request(b"vAttach;" + pid_hex)
        if not stop.startswith(b"T"):
            raise ProbeError(f"attach to isolated emulated PID returned {stop!r}")
        result["attached"] = True
        if rsp.request(f"Z0,{BREAKPOINT:x},4".encode("ascii")) != b"OK":
            raise ProbeError("APT Utility-4 software breakpoint was not accepted")
        result["breakpoint_set"] = True
        result["hits"], result["capture_stop"] = collect_hits(rsp, max_hits, deadline=deadline)
    except Exception as exc:
        original_error = exc
    finally:
        fatal_cleanup = bool(original_error and on_fatal is not None)
        child_stopped = False

        def stop_before_disconnect() -> bool:
            try:
                on_fatal()
                return True
            except Exception as exc:
                result["cleanup_errors"].append(f"terminate child before disconnect: {exc}")
                return False

        begin_cleanup = getattr(rsp, "begin_cleanup_grace", None)
        try:
            if begin_cleanup:
                begin_cleanup()
        except Exception as exc:
            result["cleanup_errors"].append(f"begin cleanup: {exc}")
            fatal_cleanup = on_fatal is not None
        if fatal_cleanup:
            child_stopped = stop_before_disconnect()
        if not fatal_cleanup and result["breakpoint_set"]:
            try:
                rsp.request(f"z0,{BREAKPOINT:x},4".encode("ascii"), expected=b"OK")
                result["breakpoint_cleared"] = True
            except Exception as exc:
                result["cleanup_errors"].append(f"breakpoint clear: {exc}")
                if on_fatal is not None:
                    fatal_cleanup = True
                    child_stopped = stop_before_disconnect()
        if not fatal_cleanup and result["attached"]:
            try:
                rsp.request(b"D", expected=b"OK")
                result["detached"] = True
            except Exception as exc:
                result["cleanup_errors"].append(f"detach: {exc}")
                if on_fatal is not None:
                    fatal_cleanup = True
                    child_stopped = stop_before_disconnect()
        if not fatal_cleanup or child_stopped:
            try:
                rsp.sock.close()
            except Exception as exc:
                result["cleanup_errors"].append(f"socket close: {exc}")
    if original_error:
        details = "; ".join(result["cleanup_errors"])
        raise ProbeError(str(original_error) + (f"; cleanup errors: {details}" if details else "")) from original_error
    if result["cleanup_errors"]:
        raise ProbeError("RSP cleanup failed: " + "; ".join(result["cleanup_errors"]))
    return result


def validate_delivery_manifest(source_exe: Path, manifest_path: Path, record: dict) -> dict:
    source_exe = source_exe.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    binary = manifest.get("binary", {})
    expected_path = (manifest_path.parent / binary.get("path", "")).resolve(strict=True)
    observed_hash = sha256(source_exe)
    pinned_hash = binary.get("sha256")
    details = {
        "path": str(manifest_path), "sha256": sha256(manifest_path),
        "binary_path": str(source_exe), "manifest_binary_path": str(expected_path),
        "manifest_binary_sha256": pinned_hash, "observed_binary_sha256": observed_hash,
        "matches_manifest_path": source_exe == expected_path,
        "matches_manifest_sha256": observed_hash == pinned_hash,
    }
    record["private_azahar"] = details
    if source_exe != expected_path or not pinned_hash or observed_hash != pinned_hash:
        raise ProbeError("private Azahar executable does not match its delivery manifest")
    return details


def preserve_staged_azahar_log(user_dir: Path, output_root: Path, stage_name: str) -> dict:
    """Preserve only the bounded diagnostic log before deleting the owned stage."""
    if not re.fullmatch(r"stage-[0-9a-f]{32}", stage_name):
        raise ProbeError("invalid stage name for diagnostic log")
    user_dir = user_dir.resolve(strict=True)
    output_root = output_root.resolve(strict=True)
    log_dir = user_dir / "log"
    log_path = log_dir / "azahar_log.txt"
    if log_dir.is_symlink() or log_path.is_symlink():
        raise ProbeError("diagnostic log path is a symlink")
    if not log_path.exists():
        return {"status": "absent"}
    if not log_path.is_file() or not log_path.resolve(strict=True).is_relative_to(user_dir):
        raise ProbeError("diagnostic log is outside the staged user directory")
    max_bytes = 8 * 1024 * 1024
    with log_path.open("rb") as source:
        data = source.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ProbeError("diagnostic log exceeds the 8 MiB preservation limit")
    target = output_root / f"{stage_name}.azahar-user.log"
    with target.open("xb") as destination:
        destination.write(data)
    digest = hashlib.sha256(data).hexdigest()
    with log_path.open("rb") as source:
        source_again = source.read(max_bytes + 1)
    with target.open("rb") as destination:
        destination_again = destination.read(max_bytes + 1)
    if source_again != data or destination_again != data:
        raise ProbeError("diagnostic log changed during preservation")
    return {"status": "preserved", "path": str(target), "bytes": len(data), "sha256": digest}


def windows_short_path(path: Path) -> Path:
    """Return an existing Windows short alias only after checking file identity."""
    if os.name != "nt":
        raise ProbeError("short staging paths require Windows")
    original = path.resolve(strict=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_short = kernel.GetShortPathNameW
    get_short.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
    get_short.restype = ctypes.c_uint32
    buffer = ctypes.create_unicode_buffer(32768)
    count = get_short(str(original), buffer, len(buffer))
    if not count or count >= len(buffer):
        raise ProbeError(f"Windows short path is unavailable (error {ctypes.get_last_error()})")
    alias = Path(buffer.value)
    if not os.path.samefile(original, alias):
        raise ProbeError("Windows short path does not identify the staged input")
    return alias


def runtime_launch_paths(staged: dict) -> tuple[Path, Path, int]:
    executable = windows_short_path(staged["executable"])
    game = windows_short_path(staged["game"])
    projected_save = executable.parent / "user" / SAVE_REL
    if len(str(projected_save)) >= 260:
        raise ProbeError("short staging path is still too long for the disposable save path")
    return executable, game, len(str(projected_save))


def validate_launch_command(command: list, executable: Path, port: int, game: Path) -> None:
    if command != [str(executable), "-g", str(port), str(game)]:
        raise ProbeError("child command does not match the verified executable, GDB port and staged CCI")


def staged_alias_log_evidence(staged: dict, launch_executable: Path, launch_game: Path) -> dict:
    """Verify the isolated profile and title ID while retaining the CCI evidence limit."""
    user_dir = staged["user_dir"]
    alias_user = launch_executable.parent / "user"
    if not os.path.samefile(user_dir, alias_user) or not os.path.samefile(staged["game"], launch_game):
        raise ProbeError("launch aliases no longer identify the staged profile and CCI")
    log_dir = user_dir / "log"
    log = log_dir / "azahar_log.txt"
    if log_dir.is_symlink() or log.is_symlink():
        raise ProbeError("staged diagnostic log path is a symlink")
    if not log.exists():
        return {"profile_path_in_log": False, "title_id_in_log": False}
    if not log.is_file() or not log.resolve(strict=True).is_relative_to(user_dir.resolve(strict=True)):
        raise ProbeError("staged diagnostic log is outside the staged profile")
    with log.open("rb") as stream:
        data = stream.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise ProbeError("staged diagnostic log exceeds the 8 MiB limit")
    text = data.decode("utf-8", errors="replace").replace("\\", "/").lower()
    profile = str(alias_user).replace("\\", "/").lower()
    return {"profile_path_in_log": profile in text,
            "title_id_in_log": bool(re.search(r"program id:\s*00040000000e5c00\b", text)),
            "profile_alias_samefile": True, "game_alias_samefile": True,
            "cci_filename_log_check": "not_used",
            "cci_evidence": "same-file-verified staged CCI in child launch argv; title ID in staged log"}


def validate_runtime_compatibility_executable(source_exe: Path, packet_inputs: dict,
                                              record: dict) -> dict:
    """Require the preserved executable that has successful private-loopback evidence."""
    source_exe = source_exe.resolve(strict=True)
    pin_path = (ROOT / AZAHAR_RUNTIME_PACKAGE_PIN_REL).resolve(strict=True)
    pin = json.loads(pin_path.read_text(encoding="utf-8"))
    compatibility = pin.get("compatibility_evidence", {})
    relative_exe = compatibility.get("private_executable")
    relative_run = compatibility.get("successful_prior_run")
    if relative_exe != AZAHAR_COMPAT_EXECUTABLE_REL:
        raise ProbeError("runtime compatibility pin does not name the preserved known-good executable")
    if relative_run != AZAHAR_COMPAT_PRIOR_RUN_REL:
        raise ProbeError("runtime compatibility pin does not name its preserved successful run")

    expected_exe = (ROOT / relative_exe).resolve(strict=True)
    prior_run_path = (ROOT / relative_run).resolve(strict=True)
    if not expected_exe.is_relative_to(ROOT.resolve()) or source_exe != expected_exe:
        raise ProbeError("runtime executable differs from the packet-pinned known-good path")

    expected_hash = compatibility.get("private_executable_sha256")
    observed_hash = sha256(source_exe)
    prior_hash = sha256(prior_run_path)
    if not isinstance(expected_hash, str) or observed_hash != expected_hash:
        raise ProbeError("preserved runtime executable differs from its compatibility hash")
    if prior_hash != compatibility.get("successful_prior_run_sha256"):
        raise ProbeError("successful prior runtime report differs from its compatibility hash")

    for relative, observed in (
        (AZAHAR_RUNTIME_PACKAGE_PIN_REL.as_posix(), sha256(pin_path)),
        (AZAHAR_COMPAT_EXECUTABLE_REL, observed_hash),
        (AZAHAR_COMPAT_PRIOR_RUN_REL, prior_hash),
    ):
        packet_pin = packet_inputs.get(relative)
        if not packet_pin or packet_pin.get("sha256") != observed:
            raise ProbeError(f"runtime compatibility input is not pinned by the task packet: {relative}")

    prior_run = json.loads(prior_run_path.read_text(encoding="utf-8"))
    if (prior_run.get("passed") is not True
            or prior_run.get("private_azahar_sha256") != expected_hash):
        raise ProbeError("compatibility report does not prove a prior successful run of this executable")
    details = {
        "path": str(source_exe),
        "sha256": observed_hash,
        "observed_binary_sha256": observed_hash,
        "matches_compatibility_hash": True,
        "compatibility_pin_path": str(pin_path),
        "compatibility_pin_sha256": sha256(pin_path),
        "successful_prior_run_path": str(prior_run_path),
        "successful_prior_run_sha256": prior_hash,
        "successful_prior_run_passed": True,
        "prior_run_executable_sha256": prior_run.get("private_azahar_sha256"),
    }
    record["private_azahar"] = details
    return details



def verify_runtime_dependency_manifest(manifest_path: Path) -> dict:
    manifest_path = manifest_path.resolve(strict=True)
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise ProbeError("unsupported Azahar runtime dependency pin schema")
    source_root_text = document.get("source_root")
    if not isinstance(source_root_text, str) or not source_root_text:
        raise ProbeError("runtime dependency pin has no source root")
    source_root = Path(source_root_text)
    if not source_root.is_absolute():
        raise ProbeError("runtime dependency source root must be absolute")
    source_root = source_root.resolve(strict=True)
    if not source_root.is_dir():
        raise ProbeError("runtime dependency source root is not a directory")
    rows = document.get("runtime_files")
    if not isinstance(rows, list) or not rows:
        raise ProbeError("runtime dependency pin has no file list")
    if document.get("runtime_file_count") != len(rows):
        raise ProbeError("runtime dependency pin count does not match its file list")

    assets = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ProbeError("runtime dependency pin row must be an object")
        relative_text = row.get("path")
        if (not isinstance(relative_text, str) or not relative_text
                or "\\" in relative_text or ":" in relative_text):
            raise ProbeError("runtime dependency path must be a safe relative POSIX path")
        relative = PurePosixPath(relative_text)
        if (relative.is_absolute() or not relative.parts
                or any(part in ("", ".", "..") for part in relative.parts)):
            raise ProbeError(f"unsafe runtime dependency path: {relative_text!r}")
        relative_text = relative.as_posix()
        key = relative_text.casefold()
        if key in seen:
            raise ProbeError(f"duplicate runtime dependency path: {relative_text}")
        seen.add(key)
        expected_hash = row.get("sha256")
        expected_size = row.get("bytes")
        if (not isinstance(expected_hash, str) or len(expected_hash) != 64
                or any(ch not in "0123456789abcdef" for ch in expected_hash.lower())
                or not isinstance(expected_size, int) or expected_size < 0):
            raise ProbeError(f"invalid runtime dependency pin: {relative_text}")
        source_path = source_root.joinpath(*relative.parts)
        try:
            source_path = source_path.resolve(strict=True)
        except OSError as exc:
            raise ProbeError(f"pinned runtime dependency is missing: {relative_text}") from exc
        if not source_path.is_relative_to(source_root) or not source_path.is_file():
            raise ProbeError(f"runtime dependency escapes its pinned source root: {relative_text}")
        observed_hash = sha256(source_path)
        observed_size = source_path.stat().st_size
        if observed_hash != expected_hash.lower() or observed_size != expected_size:
            raise ProbeError(f"pinned runtime dependency hash/size mismatch: {relative_text}")
        assets.append({
            "relative_path": relative_text,
            "source": str(source_path),
            "sha256": expected_hash.lower(),
            "bytes": expected_size,
        })
    return {
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256(manifest_path),
        "source_root": str(source_root),
        "asset_count": len(assets),
        "assets": assets,
    }


def verify_runtime_dependency_sources(runtime_dependencies: dict) -> dict:
    results = []
    for asset in runtime_dependencies["assets"]:
        source_path = Path(asset["source"])
        try:
            observed_hash = sha256(source_path)
            observed_size = source_path.stat().st_size
            error = None
        except OSError as exc:
            observed_hash = None
            observed_size = None
            error = f"{type(exc).__name__}: {exc}"
        results.append({
            "relative_path": asset["relative_path"],
            "source": str(source_path),
            "expected_sha256": asset["sha256"],
            "observed_sha256": observed_hash,
            "expected_bytes": asset["bytes"],
            "observed_bytes": observed_size,
            "error": error,
            "unchanged": observed_hash == asset["sha256"] and observed_size == asset["bytes"],
        })
    return {
        "source_root": runtime_dependencies["source_root"],
        "asset_count": len(results),
        "unchanged": all(row["unchanged"] for row in results),
        "assets": results,
    }


def copy_pinned_runtime_dependencies(runtime_dependencies: dict, app_dir: Path) -> list[dict]:
    app_dir = app_dir.resolve(strict=True)
    records = []
    for asset in runtime_dependencies["assets"]:
        relative = PurePosixPath(asset["relative_path"])
        if (relative.is_absolute() or not relative.parts
                or any(part in ("", ".", "..") for part in relative.parts)):
            raise ProbeError(f"unsafe runtime dependency path: {asset['relative_path']!r}")
        source_path = Path(asset["source"]).resolve(strict=True)
        source_root = Path(runtime_dependencies["source_root"]).resolve(strict=True)
        if not source_path.is_relative_to(source_root):
            raise ProbeError(f"runtime dependency escapes its pinned source root: {asset['relative_path']}")
        destination = app_dir.joinpath(*relative.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            raise ProbeError(f"runtime dependency destination already exists: {asset['relative_path']}")
        before_hash = sha256(source_path)
        before_size = source_path.stat().st_size
        if before_hash != asset["sha256"] or before_size != asset["bytes"]:
            raise ProbeError(f"runtime dependency changed before staging: {asset['relative_path']}")
        shutil.copy2(source_path, destination)
        destination_resolved = destination.resolve(strict=True)
        if not destination_resolved.is_relative_to(app_dir):
            raise ProbeError(f"staged runtime dependency escapes its app directory: {asset['relative_path']}")
        staged_hash = sha256(destination_resolved)
        staged_size = destination_resolved.stat().st_size
        after_hash = sha256(source_path)
        after_size = source_path.stat().st_size
        unchanged = after_hash == before_hash and after_size == before_size
        if (staged_hash != asset["sha256"] or staged_size != asset["bytes"] or not unchanged):
            raise ProbeError(f"runtime dependency staging hash check failed: {asset['relative_path']}")
        records.append({
            "relative_path": asset["relative_path"],
            "source": str(source_path),
            "destination": str(destination_resolved),
            "sha256_expected": asset["sha256"],
            "source_sha256_before": before_hash,
            "staged_sha256": staged_hash,
            "source_sha256_after_copy": after_hash,
            "bytes_expected": asset["bytes"],
            "staged_bytes": staged_size,
            "source_unchanged_after_copy": unchanged,
        })
    return records

def validate_task_and_inputs(args, record: dict) -> dict:
    task_path = Path(args.task_json).resolve(strict=True)
    task = json.loads(task_path.read_text(encoding="utf-8"))
    task_id = task.get("task", {}).get("id")
    if task_id not in ALLOWED_TASK_IDS:
        raise ProbeError("task packet is not the assigned APT Utility-4 task")
    output_root = Path(task["output_root"])
    packet_root = (ROOT / output_root).resolve()
    expected_agent_root = (ROOT / "build/agent-work/H2-semantic").resolve()
    if not packet_root.is_relative_to(expected_agent_root) or packet_root.parent.name != task_id:
        raise ProbeError("task packet output root is outside its assigned H2 task directory")
    if not task_path.is_relative_to(packet_root):
        raise ProbeError("task packet file is outside its declared output root")
    required_packet_inputs = ()
    if task_id == RUNTIME_TASK_ID:
        required_packet_inputs = (AZAHAR_MANIFEST_REL, AZAHAR_EXECUTABLE_REL,
                                  AZAHAR_RUNTIME_PACKAGE_PIN_REL.as_posix(),
                                  AZAHAR_COMPAT_EXECUTABLE_REL, AZAHAR_COMPAT_PRIOR_RUN_REL,
                                  *PROFILE_SEED_PIN_RELS)
    packet_inputs = verify_packet_inputs(task, ROOT, required_packet_inputs)
    record["task_id"] = task_id
    record["task_packet"] = {"path": str(task_path), "sha256": sha256(task_path), "task_id": task_id}
    record["task_packet_output_root"] = str(packet_root)
    record["output_root"] = str(derive_output_root(
        task_id, packet_root, Path(args.output_root) if args.output_root else None
    ))
    record["packet_input_hashes"] = packet_inputs
    if task_id == RUNTIME_TASK_ID:
        if not args.offline_gate_attestation:
            raise ProbeError("runtime capture requires fresh offline-gate attestation before launch")
        attestation_path = Path(args.offline_gate_attestation).resolve(strict=True)
        if not attestation_path.is_relative_to(packet_root):
            raise ProbeError("offline-gate attestation must be inside the runtime packet output root")
        attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
        record["offline_gates"] = validate_gate_attestation_document(attestation, attestation_path, packet_root)
    runner_path = Path(__file__).resolve()
    record["runner"] = {"path": str(runner_path), "sha256": sha256(runner_path)}

    code = (ROOT / CODE_REL).resolve(strict=True)
    log017 = (ROOT / RUN017_LOG_REL).resolve(strict=True)
    log028 = (ROOT / RUN028_LOG_REL).resolve(strict=True)
    static = static_contract(code, log017, log028)
    record["static_contract"] = static

    game = Path(args.game).resolve(strict=True)
    game_hash = sha256(game)
    record["inputs"] = {"game_path": str(game), "game_sha256": game_hash,
                        "save_fixture_staged": False}
    if game_hash != GAME_SHA256:
        raise ProbeError("CCI SHA-256 does not match the pinned original title")

    fixture = Path(args.save_fixture).resolve(strict=True)
    approved_fixture = (ROOT / "build/h3-fixture/source/sdds4game1.sav").resolve(strict=True)
    build_root = (ROOT / "build").resolve(strict=True)
    if fixture != approved_fixture or not fixture.is_relative_to(build_root):
        raise ProbeError("save input must be the approved disposable build/h3-fixture copy")
    fixture_hash = sha256(fixture)
    if fixture_hash != SAVE_FIXTURE_SHA256:
        raise ProbeError("disposable save fixture SHA-256 does not match its pin")
    record["inputs"].update({"disposable_save_fixture_path": str(fixture),
                             "disposable_save_fixture_sha256": fixture_hash,
                             "supplied_source_save_accessed": False})

    profile_seed = Path(args.profile_seed).resolve(strict=True)
    if not profile_seed.is_dir() or not profile_seed.is_relative_to(build_root):
        raise ProbeError("profile seed must be a disposable seed directory under build/")
    if task_id == RUNTIME_TASK_ID and profile_seed != (ROOT / PROFILE_SEED_ROOT_REL).resolve(strict=True):
        raise ProbeError("runtime profile seed differs from the packet-pinned profile directory")
    record["inputs"]["profile_seed_path"] = str(profile_seed)
    record["inputs"]["profile_seed_files"] = shared.file_manifest(profile_seed)
    if not record["inputs"]["profile_seed_files"]:
        raise ProbeError("profile seed directory is empty")
    record["inputs"]["profile_seed_sha256"] = hashlib.sha256(
        json.dumps(record["inputs"]["profile_seed_files"], sort_keys=True).encode("utf-8")
    ).hexdigest()
    if task_id == RUNTIME_TASK_ID:
        record["inputs"]["profile_seed_packet_manifest"] = verify_profile_seed_manifest(
            profile_seed, packet_inputs)
        seed_files_by_path = {entry["path"]: entry["sha256"]
                              for entry in record["inputs"]["profile_seed_files"]}
        seed_pin_evidence = []
        for relative in shared.PROFILE_SEED_FILES:
            source_relative = (PROFILE_SEED_ROOT_REL / relative).as_posix()
            pinned = packet_inputs.get(source_relative)
            actual = seed_files_by_path.get(relative.as_posix())
            if pinned is None or actual is None or pinned["sha256"] != actual:
                raise ProbeError(f"runtime packet profile-seed pin mismatch or missing seed: {source_relative}")
            seed_pin_evidence.append({"path": source_relative, "sha256": actual,
                                      "matches_packet": True, "staged_by_runner": True})
        record["inputs"]["profile_seed_pins"] = seed_pin_evidence

    source_exe = Path(args.azahar).resolve(strict=True)
    manifest_path = Path(args.delivery_manifest).resolve(strict=True) if args.delivery_manifest else (
        (ROOT / AZAHAR_MANIFEST_REL).resolve(strict=True)
        if task_id == RUNTIME_TASK_ID else source_exe.parents[3] / "h2-delivery-manifest.json"
    )
    if task_id == RUNTIME_TASK_ID:
        if source_exe != (ROOT / AZAHAR_COMPAT_EXECUTABLE_REL).resolve(strict=True):
            raise ProbeError("runtime executable path differs from its packet-pinned known-good path")
        if manifest_path != (ROOT / AZAHAR_MANIFEST_REL).resolve(strict=True):
            raise ProbeError("runtime Azahar manifest path differs from its packet-pinned path")
    if task_id == RUNTIME_TASK_ID:
        source_build_exe = (ROOT / AZAHAR_EXECUTABLE_REL).resolve(strict=True)
        source_delivery = validate_delivery_manifest(source_build_exe, manifest_path, record)
        manifest_pin = packet_inputs[AZAHAR_MANIFEST_REL]["sha256"]
        if source_delivery["sha256"] != manifest_pin:
            raise ProbeError("Azahar source-build manifest does not match runtime packet input pin")
        validate_runtime_compatibility_executable(source_exe, packet_inputs, record)
        record["private_azahar"]["source_build_delivery"] = source_delivery
    else:
        validate_delivery_manifest(source_exe, manifest_path, record)
    runtime_dependencies = None
    if task_id == RUNTIME_TASK_ID:
        dependency_manifest_path = (ROOT / AZAHAR_RUNTIME_PACKAGE_PIN_REL).resolve(strict=True)
        runtime_dependencies = verify_runtime_dependency_manifest(dependency_manifest_path)
        if runtime_dependencies["manifest_sha256"] != packet_inputs[AZAHAR_RUNTIME_PACKAGE_PIN_REL.as_posix()]["sha256"]:
            raise ProbeError("runtime dependency manifest does not match runtime packet input pin")
        record["private_azahar"]["runtime_dependency_package"] = {
            "manifest_path": runtime_dependencies["manifest_path"],
            "manifest_sha256": runtime_dependencies["manifest_sha256"],
            "source_root": runtime_dependencies["source_root"],
            "asset_count": runtime_dependencies["asset_count"],
            "assets": runtime_dependencies["assets"],
        }
    record["inputs"]["code_bin_sha256"] = static["code_bin"]["sha256"]
    return {"task": task, "packet_root": packet_root, "source_exe": source_exe,
            "manifest": manifest_path, "game": game, "fixture": fixture,
            "profile_seed": profile_seed, "runtime_dependencies": runtime_dependencies}


def stage_runtime(source_exe: Path, source_game: Path, profile_seed: Path, fixture: Path,
                  stage_dir: Path, runtime_dependencies: dict | None = None) -> dict:
    if runtime_dependencies is None:
        raise ProbeError("runtime staging requires a verified dependency manifest; unpinned fallback is disabled")
    if (not stage_dir.is_dir() or stage_dir.is_symlink() or any(stage_dir.iterdir())):
        raise ProbeError(f"staging destination is not the newly owned empty directory: {stage_dir}")
    app_dir = stage_dir / "app"
    app_dir.mkdir()
    staged_exe = app_dir / "azahar.exe"
    shutil.copy2(source_exe, staged_exe)
    package_assets = copy_pinned_runtime_dependencies(runtime_dependencies, app_dir)
    user = app_dir / "user"
    user.mkdir()
    profile_files = shared.provision_profile(profile_seed, user)
    save_dest = user / SAVE_REL
    save_dest.parent.mkdir(parents=True, exist_ok=True)
    source_save_hash = sha256(fixture)
    shutil.copy2(fixture, save_dest)
    staged_save_hash = sha256(save_dest)
    if source_save_hash != SAVE_FIXTURE_SHA256 or staged_save_hash != source_save_hash:
        raise ProbeError("disposable save fixture staging hash check failed")
    staged_game = stage_dir / "pinned-title.cci"
    shared._stage_game_file(source_game, staged_game)
    if sha256(staged_exe) != sha256(source_exe) or sha256(staged_game) != sha256(source_game):
        raise ProbeError("staged executable or CCI hash mismatch")
    return {
        "run_dir": str(stage_dir.resolve()), "executable": staged_exe,
        "game": staged_game, "app_dir": app_dir, "user_dir": user,
        "profile_files": profile_files, "package_assets": package_assets,
        "runtime_files_before": shared.file_manifest(app_dir, excluded_top_level={"user"}),
        "save_source_sha256_before": source_save_hash,
        "staged_save_path": save_dest,
        "staged_save_sha256_before": staged_save_hash,
    }


def remove_owned_stage(stage_root: Path, stage_dir: Path) -> bool:
    root = stage_root.resolve(strict=True)
    candidate = stage_dir.resolve(strict=False)
    if candidate.parent != root or not candidate.name.startswith("stage-"):
        raise ProbeError("refusing to remove a staging path outside the owned direct-child namespace")
    if stage_dir.is_symlink():
        raise ProbeError("refusing to remove a symlink staging root")
    if not candidate.exists():
        return True
    for item in candidate.rglob("*"):
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ProbeError(f"refusing recursive cleanup through link: {item}")
    shutil.rmtree(candidate)
    return not candidate.exists()


def stop_child(process) -> dict:
    if process is None:
        return {"terminated": False, "exit_code": None}
    if process.poll() is None:
        try:
            process.terminate()
        except OSError:
            # Still try the stronger termination path below.
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    return {"terminated": True, "exit_code": process.returncode}


def _append_log_tail(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
    except OSError as exc:
        return [f"log read error: {exc}"]


def execute(args, record: dict) -> dict:
    now = datetime.now(timezone.utc)
    record["started_at"] = now.isoformat()
    record["status"] = "failed"
    record["error"] = None
    process = None
    process_stopped = True
    stage_dir = None
    stage_created_by_us = False
    stdout_stream = stderr_stream = None
    rsp_sock = None
    info = validate_task_and_inputs(args, record)
    if info.get("runtime_dependencies") is None:
        raise ProbeError("Azahar execution requires a verified runtime dependency manifest")
    output_root = Path(record["output_root"]).resolve()
    packet_root = info["packet_root"]
    if info["task"]["task"]["id"] == RUNTIME_TASK_ID:
        if args.startup_timeout > 8.0 or args.capture_timeout > 8.0:
            raise ProbeError("runtime task startup and capture bounds may not exceed 8 seconds")
    if args.startup_timeout <= 0 or args.capture_timeout <= 0 or args.packet_timeout <= 0:
        raise ProbeError("startup, capture, and per-packet timeouts must all be positive")
    output_root.mkdir(parents=True, exist_ok=True)
    if args.port in FORBIDDEN_PORTS:
        raise ProbeError("historical GDB port 24689 is forbidden")
    shared.reserve_port(args.port)
    stage_dir = output_root / ("stage-" + uuid.uuid4().hex)
    stdout_path = output_root / (stage_dir.name + ".stdout.log")
    stderr_path = output_root / (stage_dir.name + ".stderr.log")
    record["invocation"] = list(sys.argv)
    record["port"] = args.port
    record["breakpoint"] = f"0x{BREAKPOINT:08x}"
    record["max_hits"] = validate_max_hits(args.max_hits)
    record["capture_timeout_seconds"] = args.capture_timeout
    record["startup_timeout_seconds"] = args.startup_timeout
    record["configured_startup_timeout_seconds"] = args.startup_timeout
    record["configured_rsp_capture_deadline_seconds"] = args.capture_timeout
    record["rsp_cleanup_grace_seconds"] = CLEANUP_GRACE_SECONDS
    record["wallclock_scope_note"] = "startup and all RSP active operations have monotonic deadlines; one separate bounded RSP cleanup grace is recorded; staging and process teardown are reported separately"
    record["explicit_rsp_memory_write_packets"] = []
    record["logical_input_injections"] = 0
    record["stage_cleanup"] = {"attempted": False, "removed": False}
    staged = None
    launch_started = None
    try:
        stage_dir.mkdir(exist_ok=False)
        stage_created_by_us = True
        staged = stage_runtime(info["source_exe"], info["game"], info["profile_seed"],
                               info["fixture"], stage_dir, info.get("runtime_dependencies"))
        record["stage"] = {
            "run_dir": staged["run_dir"], "staged_executable": str(staged["executable"]),
            "staged_executable_sha256": sha256(staged["executable"]),
            "staged_game": str(staged["game"]), "staged_game_sha256": sha256(staged["game"]),
            "profile_files": staged["profile_files"], "package_assets": staged["package_assets"],
            "staged_save_path": str(staged["staged_save_path"]),
            "staged_save_sha256_before": staged["staged_save_sha256_before"],
            "staged_save_mutation_policy": "disposable runtime copy may change; record before/after SHA-256 and changed flag; source fixture must remain unchanged",
        }
        stdout_stream = stdout_path.open("x", encoding="utf-8", errors="replace")
        stderr_stream = stderr_path.open("x", encoding="utf-8", errors="replace")
        launch_executable, launch_game, projected_save_length = runtime_launch_paths(staged)
        record["launch_paths"] = {"executable": str(launch_executable), "game": str(launch_game),
                                  "projected_save_path_length": projected_save_length,
                                  "same_file_identity_verified": True}
        command = shared.azahar_command(launch_executable, args.port, launch_game)
        validate_launch_command(command, launch_executable, args.port, launch_game)
        record["command"] = command
        env = os.environ.copy()
        env["QT_DEBUG_PLUGINS"] = "1"
        launch_started = datetime.now(timezone.utc)
        record["launch_started_at"] = launch_started.isoformat()
        process = subprocess.Popen(command, cwd=launch_executable.parent, env=env,
                                   stdin=subprocess.DEVNULL, stdout=stdout_stream,
                                   stderr=stderr_stream, shell=False)
        record["host_pid"] = process.pid
        deadline = time.monotonic() + args.startup_timeout
        binding = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise ProbeError(f"staged Azahar exited before RSP readiness (code {process.returncode})")
            binding = listener_binding(args.port)
            if binding is not None:
                break
            time.sleep(0.25)
        if binding is None or binding["pid"] != process.pid:
            raise ProbeError("loopback GDB listener is not owned exclusively by the launched child")
        record["listener_binding"] = binding
        record["listener_owner_pid"] = binding["pid"]
        log_deadline = min(deadline, time.monotonic() + 3.0)
        logs_verified = False
        log_evidence = {}
        while time.monotonic() < log_deadline:
            log_evidence = staged_alias_log_evidence(staged, launch_executable, launch_game)
            logs_verified = log_evidence["profile_path_in_log"] and log_evidence["title_id_in_log"]
            if logs_verified:
                break
            time.sleep(0.25)
        record["staged_log_evidence"] = log_evidence
        if not logs_verified:
            raise ProbeError("staged Azahar logs did not confirm local profile and pinned game paths")
        record["profile_verified"] = True
        rsp_deadline = time.monotonic() + args.capture_timeout
        record["rsp_deadline_seconds"] = args.capture_timeout
        rsp_sock = connect_to_loopback(args.port, rsp_deadline, args.packet_timeout)
        rsp = DeadlineRsp(rsp_sock, rsp_deadline, CLEANUP_GRACE_SECONDS, args.packet_timeout)
        def stop_child_on_rsp_error() -> None:
            record["rsp_fatal_process_cleanup"] = stop_child(process)
            if process.poll() is None:
                raise ProbeError("isolated child is still running after termination")

        record["rsp"] = capture_session(rsp, args.max_hits, deadline=rsp_deadline,
                                        on_fatal=stop_child_on_rsp_error)
        record["capture_count"] = len(record["rsp"]["hits"])
        record["status"] = "captured" if record["rsp"]["capture_stop"] == "max_hits_reached" else "captured_partial"
        record["runtime_evidence"] = record["status"]
    finally:
        def cleanup_error(action: str, error: Exception) -> None:
            record.setdefault("cleanup_errors", []).append(f"{action}: {error}")

        if process is not None:
            # Unknown process state must never authorize socket or stage cleanup.
            process_stopped = False
            try:
                record["process_cleanup"] = stop_child(process)
                process_stopped = process.poll() is not None
            except Exception as exc:
                cleanup_error("terminate child", exc)
                try:
                    process_stopped = process.poll() is not None
                except Exception as poll_exc:
                    cleanup_error("verify child termination", poll_exc)
            record.setdefault("process_cleanup", {})["confirmed_stopped"] = process_stopped
        if process_stopped and rsp_sock is not None:
            try:
                rsp_sock.close()
            except Exception as exc:
                cleanup_error("close RSP socket after child termination", exc)
        for label, stream in (("stdout", stdout_stream), ("stderr", stderr_stream)):
            if stream is not None:
                try:
                    stream.flush()
                    stream.close()
                except Exception as exc:
                    cleanup_error(f"close {label}", exc)
        if process is not None:
            try:
                record["listener_binding_after_termination"] = listener_binding(args.port)
                record["listener_released"] = record["listener_binding_after_termination"] is None
            except Exception as exc:
                cleanup_error("verify listener teardown", exc)
            record["stdout_tail"] = _append_log_tail(stdout_path)
            record["stderr_tail"] = _append_log_tail(stderr_path)
        if staged is not None:
            if process_stopped and stage_dir is not None:
                try:
                    record["stage"]["azahar_log"] = preserve_staged_azahar_log(
                        staged["user_dir"], output_root, stage_dir.name)
                except Exception as exc:
                    cleanup_error("preserve staged Azahar log", exc)
            try:
                record["stage"]["staged_save_sha256_after"] = sha256(staged["staged_save_path"])
                record["stage"]["staged_save_changed"] = (
                    record["stage"]["staged_save_sha256_before"]
                    != record["stage"]["staged_save_sha256_after"])
                record["stage"]["user_tree_before_cleanup"] = shared.file_manifest(staged["user_dir"])
                record["stage"]["runtime_files_unchanged_after_run"] = (
                    shared.file_manifest(staged["app_dir"], excluded_top_level={"user"})
                    == staged["runtime_files_before"]
                )
                record["inputs"]["disposable_save_fixture_sha256_after"] = sha256(info["fixture"])
                record["inputs"]["disposable_save_fixture_unchanged"] = (
                    record["inputs"]["disposable_save_fixture_sha256"]
                    == record["inputs"]["disposable_save_fixture_sha256_after"]
                )
                record["inputs"]["game_sha256_after"] = sha256(info["game"])
                record["inputs"]["game_unchanged"] = record["inputs"]["game_sha256"] == record["inputs"]["game_sha256_after"]
                record["inputs"]["source_executable_sha256_after"] = sha256(info["source_exe"])
                record["inputs"]["source_executable_unchanged"] = (
                    record["private_azahar"]["observed_binary_sha256"]
                    == record["inputs"]["source_executable_sha256_after"]
                )
                record["inputs"]["profile_seed_files_after"] = shared.file_manifest(info["profile_seed"])
                record["inputs"]["profile_seed_unchanged"] = (
                    record["inputs"]["profile_seed_files"] == record["inputs"]["profile_seed_files_after"]
                )
                if info.get("runtime_dependencies") is not None:
                    dependency_after = verify_runtime_dependency_sources(info["runtime_dependencies"])
                    record["inputs"]["runtime_dependency_sources_after"] = dependency_after
                    record["inputs"]["runtime_dependency_sources_unchanged"] = dependency_after["unchanged"]
                if not (record["inputs"]["source_executable_unchanged"]
                        and record["inputs"]["profile_seed_unchanged"]
                        and record["inputs"]["game_unchanged"]
                        and record["inputs"]["disposable_save_fixture_unchanged"]
                        and record["inputs"].get("runtime_dependency_sources_unchanged", True)
                        and record["stage"]["runtime_files_unchanged_after_run"]):
                    cleanup_error("verify immutable staged inputs", ProbeError("one or more source/runtime hashes changed"))
            except Exception as exc:
                cleanup_error("capture staged/source hashes", exc)
        if stage_created_by_us and stage_dir is not None and stage_dir.exists():
            record["stage_cleanup"]["attempted"] = True
            if not process_stopped:
                record["stage_cleanup"]["error"] = "staging preserved because the child process may still be running"
                record["stage_cleanup"]["removed"] = False
            else:
                try:
                    record["stage_cleanup"]["removed"] = remove_owned_stage(output_root, stage_dir)
                except Exception as exc:
                    record["stage_cleanup"]["error"] = str(exc)
                    record["stage_cleanup"]["removed"] = False
    record["ended_at"] = datetime.now(timezone.utc).isoformat()
    if record.get("status") not in {"captured", "captured_partial"}:
        return record
    if not record.get("stage_cleanup", {}).get("removed"):
        record["status"] = "failed"
        record["error"] = record.get("stage_cleanup", {}).get("error", "staging cleanup did not complete")
    if record.get("cleanup_errors"):
        record["status"] = "failed"
        record["error"] = "; ".join(record["cleanup_errors"])
    if record.get("listener_released") is False:
        record["status"] = "failed"
        record["error"] = "GDB listener remained after child termination"
    return record


def run(args) -> dict:
    record = {"schema_version": 1, "task_id": TASK_ID, "runner_task_id": TASK_ID,
              "status": "failed", "error": None,
              "runtime_evidence": "not_run", "stage_cleanup": {"attempted": False, "removed": False},
              "listener_owner_pid": None, "explicit_rsp_memory_write_packets": [],
              "logical_input_injections": 0,
              "software_breakpoint": {"address": f"0x{BREAKPOINT:08x}", "insert_packet": "Z0",
                                      "remove_packet": "z0", "transient_target_code_effect": True}}
    try:
        return execute(args, record)
    except Exception as exc:
        record["status"] = "failed"
        record["error"] = str(exc)
        record["ended_at"] = datetime.now(timezone.utc).isoformat()
        return record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--azahar", required=True, help="private loopback Azahar executable")
    parser.add_argument("--delivery-manifest", help="defaults to the private package h2-delivery-manifest.json")
    parser.add_argument("--game", required=True, help="pinned original US CCI")
    parser.add_argument("--save-fixture", default=str(ROOT / "build/h3-fixture/source/sdds4game1.sav"),
                        help="the hash-pinned disposable build/h3-fixture copy only")
    parser.add_argument("--profile-seed", default=str(ROOT / "build/h2-runtime/profile-pristine-user"),
                        help="minimal profile seed under build/")
    parser.add_argument("--task-json", default=str(ROOT / TASK_REL))
    parser.add_argument("--output-root", help="defaults to the selected packet root (runtime) or its runtime-captures child (implementation)")
    parser.add_argument("--offline-gate-attestation", help="required by runtime task; hashes four fresh passed gate reports")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--startup-timeout", type=float, default=8.0)
    parser.add_argument("--capture-timeout", type=float, default=8.0)
    parser.add_argument("--packet-timeout", type=float, help=argparse.SUPPRESS)
    parser.add_argument("--max-hits", type=int, default=4)
    parser.add_argument("--record", help="new JSON report path; defaults to output_root/capture-<id>.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_id = uuid.uuid4().hex
    record = run(args)
    output_root = Path(record.get("output_root", args.output_root or (ROOT / OUTPUT_REL / "runtime-captures")))
    report_path = Path(args.record) if args.record else output_root / f"capture-{run_id}.json"
    try:
        task_root = Path(args.task_json).resolve(strict=True).parent
        if report_path.resolve(strict=False) == task_root or not report_path.resolve(strict=False).is_relative_to(task_root):
            raise OSError("report path must stay under the assigned run-002 output root")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        record["report_path"] = str(report_path.resolve(strict=False))
        with report_path.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
        record["report_sha256"] = sha256(report_path)
        print(json.dumps(record, indent=2))
    except OSError as exc:
        print(json.dumps({**record, "report_write_error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    return 0 if record.get("status") in {"captured", "captured_partial"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
