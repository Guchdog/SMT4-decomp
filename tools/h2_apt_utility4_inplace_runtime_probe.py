"""Bounded runtime probe of the APT utility-4 entry and wrapper call.

Compares the reviewed H2 base IPS with the candidate package IPS, using fresh
isolated profiles and the private loopback-bound Azahar binary. It stops at the
original wrapper entry, before the APT service executes; it makes no game input.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import h2_apt_utility4_caller_probe as apt_probe
from tools import h2_autonomous_gdb_verify as h2
from tools.h2_azahar_rsp_probe import ProbeError, Rsp, decode_r0, listener_owner, reserve_port, sha256
from tools.h2_calc_code_patch import apply_ips

ENTRY = 0x002C0EFC
WRAPPER = 0x002B5A1C
ENTRY_SPAN = 44
CANDIDATE_BODY_SIZE = 40
IMAGE_BASE = 0x00100000
WRAPPER_ARGS = [4, 0, 0, 0, 0, 0]
ENTRY_LR = 0x00103E84
WRAPPER_LR = 0x002C0F20
EXPECTED = {
    "azahar": "8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a",
    "cci": "9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2",
    "original": "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558",
    "base_image": "acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446",
    "base_ips": "67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb",
    "candidate_image": "788530a1b1ad7d4f361228cbd0e4b87885b37606a8f3485c52e5390ae3223179",
    "candidate_ips": "9c4f38fbdefc9c52bc745e4cbb1e6425d5822db7c2ed2267331d582c5a841c88",
    "candidate_source": "1f7228e30cfdb3c14497f96fdce3bc65845ad65bb4b3b5491c5ab2b382742e06",
    "fixture_save": "6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9",
    "protected_save": "6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9",
}
EXECUTION_SOURCE_PATHS = (
    "tools/h2_apt_utility4_inplace_runtime_probe.py",
    "tools/h2_apt_utility4_caller_probe.py",
    "tools/h2_autonomous_gdb_verify.py",
    "tools/h2_azahar_rsp_probe.py",
    "tools/h2_calc_code_patch.py",
    "tools/h2_calc_experiment.py",
    "tools/asm_diff.py",
    "tools/build_check.py",
    "tools/semantic_experiment.py",
)
SAVE_REL = Path(
    "sdmc/Nintendo 3DS/00000000000000000000000000000000/"
    "00000000000000000000000000000000/title/00040000/000e5c00/"
    "data/00000001/sdds4game1.sav"
)

DEFAULT_AZAHAR = ROOT / "build/h2-runtime/autonomous-verify-run001/original/app/azahar.exe"
DEFAULT_DLL_SOURCE = Path("E:/emulador3ds/azahar.exe")
DEFAULT_CCI = Path("E:/emulador3ds/00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci")
DEFAULT_ORIGINAL = ROOT / "build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/reference/code.bin"
DEFAULT_BASE_IMAGE = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin"
DEFAULT_BASE_IPS = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.ips"
DEFAULT_CANDIDATE_IMAGE = ROOT / "build/agent-work/H2-semantic/h2-apt-utility4-final-image-package/run-001/package/code.h2-apt-utility4-inplace.bin"
DEFAULT_CANDIDATE_IPS = ROOT / "build/agent-work/H2-semantic/h2-apt-utility4-final-image-package/run-001/package/code.h2-apt-utility4-inplace.ips"
DEFAULT_PACKAGE_MANIFEST = ROOT / "build/agent-work/H2-semantic/h2-apt-utility4-final-image-package/run-001/package/manifest.json"
DEFAULT_BASE_MANIFEST = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/manifest.json"
DEFAULT_PROFILE = ROOT / "build/h2-runtime/profile-pristine-user"
DEFAULT_FIXTURE = ROOT / "build/h3-fixture/source/sdds4game1.sav"
DEFAULT_PROTECTED_SAVE = Path("E:/emulador3ds/sdds4game1.sav")

GATE_PATHS = {
    "direct_differential": "build/agent-work/H2-semantic/h2-apt-utility4-inplace-candidate/run-001/inplace-differential-002/report.json",
    "caller_original": "build/agent-work/H2-semantic/h2-apt-utility4-inplace-candidate/run-001/caller-original-005/composition/report.json",
    "caller_composed_h2": "build/agent-work/H2-semantic/h2-apt-utility4-inplace-candidate/run-001/caller-final-h2-005/composition/report.json",
    "observed_caller_context": "build/agent-work/H2-semantic/h2-apt-utility4-observed-caller-context/run-001/context-002/report.json",
    "arm_thumb_scan": "build/agent-work/H2-semantic/h2-apt-utility4-interworking-static-audit/run-001/scan.json",
    "independent_package_review": "build/agent-work/H2-semantic/h2-apt-utility4-final-image-package-review/run-001/checks/independent-ips-audit.json",
}

def wrapper_arguments(registers: dict[str, int], stack_words: list[int]) -> list[int]:
    if len(stack_words) != 2:
        raise ValueError("AAPCS wrapper call has exactly two stack argument words")
    return [registers[f"r{i}"] for i in range(4)] + list(stack_words)


def candidate_delta(base: bytes, candidate: bytes, file_offset: int) -> dict:
    if len(base) != len(candidate):
        raise ValueError("base and candidate images differ in length")
    changed = [i for i, (left, right) in enumerate(zip(base, candidate)) if left != right]
    allowed = set(range(file_offset, file_offset + CANDIDATE_BODY_SIZE))
    return {
        "changed_byte_count": len(changed),
        "all_changes_inside_candidate_body": all(offset in allowed for offset in changed),
        "changed_file_offsets": changed,
    }


def mark_software_breakpoint_cleared(capture: dict, address: int) -> None:
    target = f"0x{address:08x}"
    for breakpoint in capture.get("software_breakpoints", []):
        if breakpoint.get("address") == target:
            breakpoint["cleared"] = True
            breakpoint["clear_acknowledged"] = True
            return
    raise ProbeError(f"no recorded software breakpoint at {target}")


def execution_source_hashes() -> dict[str, str]:
    return {relative: sha256(ROOT / relative) for relative in EXECUTION_SOURCE_PATHS}


def read_r32(rsp: Rsp, addr: int) -> int:
    raw = h2.rsp_read_mem(rsp, addr, 4)
    return int.from_bytes(raw, "little")


def read_registers(rsp: Rsp) -> dict[str, int]:
    return apt_probe.read_registers(rsp)


def attach(rsp: Rsp) -> str:
    supported = rsp.request(b"qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+")
    if not supported or supported.startswith(b"E"):
        raise ProbeError(f"qSupported failed: {supported!r}")
    if rsp.request(b"!") != b"OK":
        raise ProbeError("extended mode rejected")
    proc_info = rsp.request(b"qfProcessInfo")
    if not proc_info.startswith(b"pid:"):
        raise ProbeError(f"qfProcessInfo failed: {proc_info!r}")
    pid_hex = proc_info.split(b":", 1)[1].split(b";", 1)[0]
    if not pid_hex or any(c not in b"0123456789abcdefABCDEF" for c in pid_hex):
        raise ProbeError(f"invalid emulated process id {pid_hex!r}")
    stop = rsp.request(b"vAttach;" + pid_hex)
    if not stop.startswith(b"T"):
        raise ProbeError(f"vAttach failed: {stop!r}")
    return pid_hex.decode("ascii")


def preflight(args) -> dict:
    path_values = {
        "azahar": args.azahar,
        "cci": args.game,
        "original": args.original_code,
        "base_image": args.base_image,
        "base_ips": args.base_ips,
        "candidate_image": args.candidate_image,
        "candidate_ips": args.candidate_ips,
        "candidate_source": ROOT / "experiments/semantic_equivalence/h2_apt_utility4_inplace_candidate.cpp",
        "fixture_save": args.save_fixture,
        "protected_save": args.protected_source_save,
    }
    observed = {name: sha256(path.resolve(strict=True)) for name, path in path_values.items()}
    for name, expected in EXPECTED.items():
        if observed[name] != expected:
            raise ProbeError(f"pinned {name} hash mismatch: {observed[name]} != {expected}")
    original = args.original_code.read_bytes()
    base_image = args.base_image.read_bytes()
    candidate_image_bytes = args.candidate_image.read_bytes()
    if apply_ips(original, args.base_ips.read_bytes()) != base_image:
        raise ProbeError("base H2 IPS does not reproduce its pinned image")
    if apply_ips(original, args.candidate_ips.read_bytes()) != candidate_image_bytes:
        raise ProbeError("candidate IPS does not reproduce its pinned image")
    if len(original) != len(base_image) or len(original) != len(candidate_image_bytes):
        raise ProbeError("image size changed")
    entry_offset = ENTRY - IMAGE_BASE
    delta = candidate_delta(base_image, candidate_image_bytes, entry_offset)
    if delta["changed_byte_count"] != 29 or not delta["all_changes_inside_candidate_body"]:
        raise ProbeError(f"candidate package delta is not confined as reviewed: {delta}")
    manifest = json.loads(args.package_manifest.read_text(encoding="utf-8"))
    if (manifest.get("final_image_sha256") != EXPECTED["candidate_image"]
            or manifest.get("ips_sha256") != EXPECTED["candidate_ips"]
            or manifest.get("base_h2_image_sha256") != EXPECTED["base_image"]
            or manifest.get("candidate_source_sha256") != EXPECTED["candidate_source"]
            or manifest.get("kind") != "experimental offline H2 image; not runtime-verified or promoted"):
        raise ProbeError("candidate package manifest identity or experimental label drifted")
    base_manifest = json.loads(args.base_manifest.read_text(encoding="utf-8"))
    source_warnings = base_manifest.get("source_identity_mismatches", [])
    if len(source_warnings) != 4:
        raise ProbeError(f"base source-identity warning count changed: {len(source_warnings)}")

    gates = {}
    for name, relative in GATE_PATHS.items():
        path = ROOT / relative
        raw = path.read_bytes()
        data = json.loads(raw)
        gates[name] = {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest()}
        if name.startswith("direct_differential") or name.startswith("caller_") or name == "observed_caller_context":
            if data.get("passed") is not True or data.get("failures"):
                raise ProbeError(f"offline semantic gate failed or incomplete: {name}")
        elif name == "arm_thumb_scan":
            arm_hits = data.get("arm_scan", {}).get("hits", [])
            thumb_hits = data.get("thumb_scan", {}).get("hits", [])
            if len(arm_hits) != 7 or thumb_hits:
                raise ProbeError("ARM/Thumb static gate no longer matches reviewed target scan")
        elif name == "independent_package_review":
            if (data.get("input_hashes_matched") != 20
                    or data.get("round_trip_exact") is not True
                    or data.get("bytes_added_to_base") != 29
                    or data.get("base_source_identity_mismatch_count") != 4):
                raise ProbeError("independent package review gate failed or drifted")
    return {
        "input_hashes": observed,
        "candidate_delta_from_reviewed_h2_base": {
            "changed_byte_count": delta["changed_byte_count"],
            "all_changes_inside_candidate_body": delta["all_changes_inside_candidate_body"],
            "candidate_file_span_hex": f"[0x{entry_offset:x},0x{entry_offset + CANDIDATE_BODY_SIZE:x})",
        },
        "base_source_identity_warnings": source_warnings,
        "offline_gates": gates,
        "source_save_policy": "original save is hash-checked only; emulator receives a copy of the pinned build fixture",
    }


def run_side(label: str, image: bytes, ips_bytes: bytes | None, args, port: int) -> dict:
    side_dir = args.output_dir / label
    exe, game = h2.stage_portable_dir(
        args.azahar.resolve(strict=True),
        args.dll_source.resolve(strict=True),
        args.game.resolve(strict=True),
        args.profile_seed.resolve(strict=True),
        side_dir,
        ips_bytes,
    )
    user_dir = exe.parent / "user"
    staged_save = user_dir / SAVE_REL
    staged_save.parent.mkdir(parents=True, exist_ok=True)
    if staged_save.exists() or staged_save.is_symlink():
        raise ProbeError(f"refusing to overwrite existing staged save: {staged_save}")
    fixture_hash_before = sha256(args.save_fixture.resolve(strict=True))
    if fixture_hash_before != EXPECTED["fixture_save"]:
        raise ProbeError("disposable save fixture hash changed before staging")
    shutil.copy2(args.save_fixture.resolve(strict=True), staged_save)
    if sha256(staged_save) != fixture_hash_before:
        raise ProbeError("staged disposable save does not match pinned fixture")
    if not staged_save.resolve(strict=True).is_relative_to(user_dir.resolve(strict=True)):
        raise ProbeError("staged save path escaped the isolated profile")
    stage_record = {
        "executable": str(exe.resolve()),
        "executable_sha256": sha256(exe),
        "game_path": str(game.resolve(strict=True)),
        "game_sha256": sha256(game.resolve(strict=True)),
        "profile_root": str(user_dir.resolve()),
        "staged_save_path": str(staged_save.resolve()),
        "staged_save_sha256_before": sha256(staged_save),
        "code_ips_path": str((user_dir / h2.MOD_IPS_RELATIVE).resolve()) if ips_bytes is not None else None,
        "code_ips_sha256": hashlib.sha256(ips_bytes).hexdigest() if ips_bytes is not None else None,
        "profile_seed_contains_save": False,
    }
    launch_exe = apt_probe.windows_short_path(exe)
    launch_game = apt_probe.windows_short_path(game)
    projected_save = launch_exe.parent / "user" / SAVE_REL
    if len(str(projected_save)) >= 260:
        raise ProbeError("8.3 staging alias still exceeds the legacy save-path bound")
    if not os.path.samefile(exe.resolve(strict=True), launch_exe):
        raise ProbeError("short executable alias does not identify the staged child")
    if not os.path.samefile(game.resolve(strict=True), launch_game):
        raise ProbeError("short CCI alias does not identify the pinned game")
    stage_record["launch_executable"] = str(launch_exe)
    stage_record["launch_game"] = str(launch_game)
    stage_record["projected_save_path_length"] = len(str(projected_save))
    stdout_path = side_dir / "azahar.stdout.log"
    stderr_path = side_dir / "azahar.stderr.log"
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
    proc = None
    sock = None
    rsp = None
    entry_bp = False
    wrapper_bp = False
    detached = False
    capture = {"status": "failed"}
    with stdout_path.open("xb") as stdout_file, stderr_path.open("xb") as stderr_file:
        try:
            command = [str(launch_exe), "-g", str(port), str(launch_game)]
            proc = subprocess.Popen(
                command, cwd=launch_exe.parent, stdin=subprocess.DEVNULL,
                stdout=stdout_file, stderr=stderr_file, shell=False,
                startupinfo=startupinfo,
            )
            stage_record["host_pid"] = proc.pid
            stage_record["command"] = command
            deadline = time.monotonic() + args.startup_timeout
            binding = None
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise ProbeError(f"staged Azahar exited early with {proc.returncode}")
                binding = apt_probe.listener_binding(port)
                if binding is not None:
                    break
                time.sleep(0.5)
            if binding is None:
                raise ProbeError(f"staged Azahar did not open loopback port {port}")
            if int(binding["pid"]) != proc.pid or binding["local_address"] != "127.0.0.1":
                raise ProbeError(f"unexpected GDB listener binding: {binding}")
            stage_record["listener_binding"] = binding
            sock = socket.create_connection(("127.0.0.1", port), timeout=args.capture_timeout)
            rsp = Rsp(sock, timeout=args.capture_timeout)
            emulated_pid = attach(rsp)
            stage_record["emulated_pid_hex"] = emulated_pid
            h2.rsp_set_bp(rsp, ENTRY)
            entry_bp = True
            stop_entry = rsp.continue_to_stop()
            entry_regs = read_registers(rsp)
            if entry_regs["r15"] != ENTRY:
                raise ProbeError(f"expected APT candidate entry {ENTRY:#x}, stopped at {entry_regs['r15']:#x}")
            h2.rsp_clear_bp(rsp, ENTRY)
            entry_bp = False
            runtime_code = h2.rsp_read_mem(rsp, ENTRY, ENTRY_SPAN)
            file_offset = ENTRY - IMAGE_BASE
            expected_code = image[file_offset:file_offset + ENTRY_SPAN]
            if runtime_code != expected_code:
                raise ProbeError("runtime APT entry bytes differ from the selected original/base/candidate image")
            h2.rsp_set_bp(rsp, WRAPPER)
            wrapper_bp = True
            stop_wrapper = rsp.continue_to_stop()
            wrapper_regs = read_registers(rsp)
            if wrapper_regs["r15"] != WRAPPER:
                raise ProbeError(f"expected original wrapper {WRAPPER:#x}, stopped at {wrapper_regs['r15']:#x}")
            stack_words_raw = h2.rsp_read_mem(rsp, wrapper_regs["r13"], 8)
            stack_words = [
                int.from_bytes(stack_words_raw[:4], "little"),
                int.from_bytes(stack_words_raw[4:], "little"),
            ]
            call_args = wrapper_arguments(wrapper_regs, stack_words)
            capture = {
                "status": "captured",
                "entry_stop_reply": stop_entry.decode("ascii", "replace"),
                "entry_pc": f"0x{entry_regs['r15']:08x}",
                "entry_lr": f"0x{entry_regs['r14']:08x}",
                "entry_registers": {key: f"0x{value:08x}" for key, value in entry_regs.items()},
                "runtime_entry_bytes_hex": runtime_code.hex(),
                "runtime_entry_bytes_sha256": hashlib.sha256(runtime_code).hexdigest(),
                "runtime_entry_bytes_match_image": True,
                "wrapper_stop_reply": stop_wrapper.decode("ascii", "replace"),
                "wrapper_pc": f"0x{wrapper_regs['r15']:08x}",
                "wrapper_lr": f"0x{wrapper_regs['r14']:08x}",
                "wrapper_sp": f"0x{wrapper_regs['r13']:08x}",
                "wrapper_sp_alignment": wrapper_regs["r13"] & 7,
                "wrapper_registers": {key: f"0x{value:08x}" for key, value in wrapper_regs.items()},
                "wrapper_stack_words": [f"0x{x:08x}" for x in stack_words],
                "wrapper_arguments": [f"0x{x:08x}" for x in call_args],
                "wrapper_arguments_match_expected": call_args == WRAPPER_ARGS,
                "stopped_before_original_wrapper_body": True,
                "explicit_rsp_memory_write_packets": [],
                "logical_input_injections": 0,
                "software_breakpoints": [
                    {"address": f"0x{ENTRY:08x}", "set": True, "cleared": True},
                    {"address": f"0x{WRAPPER:08x}", "set": True, "cleared": False},
                ],
            }
            h2.rsp_clear_bp(rsp, WRAPPER)
            mark_software_breakpoint_cleared(capture, WRAPPER)
            wrapper_bp = False
            try:
                rsp.request(b"D", expected=b"OK")
                detached = True
            except Exception as exc:
                capture["detach_error"] = str(exc)
            stage_record["detached"] = detached
            stage_record["probe_result"] = capture
        except Exception as exc:
            capture = {**capture, "status": "partial", "error": f"{type(exc).__name__}: {exc}"}
        finally:
            if rsp is not None:
                if wrapper_bp:
                    try:
                        h2.rsp_clear_bp(rsp, WRAPPER)
                        capture.setdefault("cleanup", {})["wrapper_breakpoint_cleared"] = True
                        wrapper_bp = False
                    except Exception as exc:
                        capture.setdefault("cleanup_errors", []).append(f"clear wrapper breakpoint: {exc}")
                if entry_bp:
                    try:
                        h2.rsp_clear_bp(rsp, ENTRY)
                        capture.setdefault("cleanup", {})["entry_breakpoint_cleared"] = True
                        entry_bp = False
                    except Exception as exc:
                        capture.setdefault("cleanup_errors", []).append(f"clear entry breakpoint: {exc}")
                if not detached:
                    try:
                        rsp.request(b"D", expected=b"OK")
                        detached = True
                    except Exception:
                        pass
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            if proc is not None:
                stage_record["process_exit_code_after_bounded_termination"] = proc.returncode
                stage_record["process_terminated"] = proc.poll() is not None
            try:
                stage_record["listener_after_cleanup"] = apt_probe.listener_binding(port)
            except Exception as exc:
                stage_record["listener_after_cleanup_error"] = str(exc)
            stage_record["staged_save_sha256_after"] = sha256(staged_save)
            stage_record["fixture_save_sha256_after"] = sha256(args.save_fixture.resolve(strict=True))
            stage_record["fixture_save_unchanged"] = (
                stage_record["fixture_save_sha256_after"] == EXPECTED["fixture_save"]
            )
            stage_record["azahar_user_log_path"] = str(user_dir / "log/azahar_log.txt")
            log_path = user_dir / "log/azahar_log.txt"
            if log_path.is_file():
                log_text = log_path.read_text(encoding="utf-8", errors="replace")
                stage_record["patch_application_logged"] = "patching code.bin" in log_text.lower()
                stage_record["title_id_logged"] = "00040000000E5C00".lower() in log_text.lower()
            else:
                stage_record["patch_application_logged"] = False
                stage_record["title_id_logged"] = False
    return {"label": label, "capture": capture, "stage": stage_record}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--azahar", type=Path, default=DEFAULT_AZAHAR)
    parser.add_argument("--dll-source", type=Path, default=DEFAULT_DLL_SOURCE)
    parser.add_argument("--game", type=Path, default=DEFAULT_CCI)
    parser.add_argument("--original-code", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--base-image", type=Path, default=DEFAULT_BASE_IMAGE)
    parser.add_argument("--base-ips", type=Path, default=DEFAULT_BASE_IPS)
    parser.add_argument("--candidate-image", type=Path, default=DEFAULT_CANDIDATE_IMAGE)
    parser.add_argument("--candidate-ips", type=Path, default=DEFAULT_CANDIDATE_IPS)
    parser.add_argument("--package-manifest", type=Path, default=DEFAULT_PACKAGE_MANIFEST)
    parser.add_argument("--base-manifest", type=Path, default=DEFAULT_BASE_MANIFEST)
    parser.add_argument("--profile-seed", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--save-fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--protected-source-save", type=Path, default=DEFAULT_PROTECTED_SAVE)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--base-port", type=int, default=62180)
    parser.add_argument("--startup-timeout", type=float, default=45.0)
    parser.add_argument("--capture-timeout", type=float, default=45.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.output_dir = args.output_dir.resolve()
    if args.output_dir.exists():
        raise SystemExit(f"output directory already exists: {args.output_dir}")
    if not 1024 <= args.base_port < 65535:
        raise SystemExit("base port must allow two consecutive user-space TCP ports")
    if args.startup_timeout <= 0 or args.capture_timeout <= 0:
        raise SystemExit("timeouts must be positive")
    args.output_dir.mkdir(parents=True)
    execution_sources_before = execution_source_hashes()
    before_protected_save = sha256(args.protected_source_save.resolve(strict=True))
    try:
        gate_record = preflight(args)
    except Exception as exc:
        report = {
            "schema_version": 1,
            "status": "preflight_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "source_save_hash_before": before_protected_save,
            "source_save_hash_after": sha256(args.protected_source_save.resolve(strict=True)),
        }
        (args.output_dir / "preflight-failed.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 2
    (args.output_dir / "offline-gate-attestation.json").write_text(
        json.dumps(gate_record, indent=2) + "\n", encoding="utf-8"
    )
    save_fixture_hash = sha256(args.save_fixture.resolve(strict=True))
    source_save_before = sha256(args.protected_source_save.resolve(strict=True))
    results = []
    errors = []
    for index, (label, image_path, ips_path) in enumerate((
        ("reviewed_h2_base", args.base_image, args.base_ips),
        ("h2_base_plus_apt_candidate", args.candidate_image, args.candidate_ips),
    )):
        try:
            reserve_port(args.base_port + index)
            image = image_path.read_bytes()
            ips = ips_path.read_bytes()
            results.append(run_side(label, image, ips, args, args.base_port + index))
        except Exception as exc:
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
            results.append({"label": label, "capture": {"status": "failed", "error": str(exc)}})
    source_save_after = sha256(args.protected_source_save.resolve(strict=True))
    source_fixture_after = sha256(args.save_fixture.resolve(strict=True))
    execution_sources_after = execution_source_hashes()
    execution_sources_unchanged = execution_sources_before == execution_sources_after
    per_side_captured = all(
        item.get("capture", {}).get("status") == "captured" for item in results
    )
    states = [item.get("capture", {}) for item in results]
    args_equal = per_side_captured and all(
        state.get("wrapper_arguments_match_expected") is True for state in states
    )
    matching_calls = per_side_captured and (
        states[0].get("entry_lr") == states[1].get("entry_lr")
        and states[0].get("wrapper_lr") == states[1].get("wrapper_lr")
        and states[0].get("wrapper_arguments") == states[1].get("wrapper_arguments")
        and states[0].get("wrapper_sp_alignment") == states[1].get("wrapper_sp_alignment")
        and states[0].get("runtime_entry_bytes_match_image") is True
        and states[1].get("runtime_entry_bytes_match_image") is True
    )
    report = {
        "schema_version": 1,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "captured_bounded_runtime_contract" if per_side_captured and args_equal and matching_calls else "partial_or_failed",
        "passed": bool(per_side_captured and args_equal and matching_calls and source_save_before == source_save_after and source_fixture_after == save_fixture_hash and execution_sources_unchanged),
        "scope": "Compare the reviewed H2 base implementation with its 40-byte APT Utility-4 candidate at the actual in-game entry and original wrapper boundary.",
        "claims": [
            "Both images reached 0x002C0EFC in an isolated Azahar process.",
            "Both implementations dispatched to original wrapper 0x002B5A1C with the same six AAPCS argument words.",
            "The candidate IPS was applied by Azahar and the runtime entry bytes matched the pinned candidate image.",
        ] if per_side_captured else [],
        "limits": [
            "Probe stops at the wrapper entry before its SVC/service body; wrapper return, service effects and caller continuation are not observed.",
            "Only this observed ARM caller path is sampled; scan limitations for indirect or alternate-state callers remain.",
            "This does not complete or close H2 TitleConfig behavior, clean emulator shutdown, or restart persistence.",
            "The full H2 paired runner separately failed on original-process WM_CLOSE before starting its patched side; see run-001 output.",
            "The result is bounded runtime evidence, not whole-game equivalence or ledger promotion.",
        ],
        "source_save_used_as_emulator_input": False,
        "source_save_hash_before": source_save_before,
        "source_save_hash_after": source_save_after,
        "source_save_unchanged": source_save_before == source_save_after,
        "disposable_fixture_hash_before": save_fixture_hash,
        "disposable_fixture_hash_after": source_fixture_after,
        "disposable_fixture_unchanged": source_fixture_after == save_fixture_hash == EXPECTED["fixture_save"],
        "execution_source_hashes_before": execution_sources_before,
        "execution_source_hashes_after": execution_sources_after,
        "execution_sources_unchanged": execution_sources_unchanged,
        "offline_gate_attestation": gate_record,
        "sides": results,
        "wrapper_arguments_equal_expected": args_equal,
        "runtime_calls_equivalent_at_wrapper_entry": matching_calls,
        "errors": errors,
    }
    report_path = args.output_dir / "runtime-entry-comparison.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "passed": report["passed"],
        "wrapper_arguments_equal_expected": report["wrapper_arguments_equal_expected"],
        "runtime_calls_equivalent_at_wrapper_entry": report["runtime_calls_equivalent_at_wrapper_entry"],
        "report": str(report_path),
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
