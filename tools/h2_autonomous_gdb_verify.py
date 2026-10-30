#!/usr/bin/env python3
"""Autonomous GDB RSP runtime verifier for H2 (TitleConfig / Audio Settings).

Stages isolated original and patched Azahar portable directories using the
private loopback-bound azahar.exe (127.0.0.1 GDB stub), drives both through the
complete H2 TitleConfig scenario via GDB RSP without any user interaction, and
verifies byte-for-byte equivalence of g_ConfigBytes and TitleConfigWork across
all checkpoints.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.h2_azahar_rsp_probe import (
    PROFILE_SEED_FILES,
    ProbeError,
    Rsp,
    decode_r0,
    frame,
    listener_owner,
    provision_profile,
    reserve_port,
    sha256,
)
from tools.h2_calc_code_patch import apply_ips

DEFAULT_PRIVATE_EXE = (
    ROOT
    / "build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe"
)
DEFAULT_DLL_SOURCE = Path("E:/emulador3ds/azahar.exe")
DEFAULT_CCI = Path(
    "E:/emulador3ds/00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci"
)
DEFAULT_ORIGINAL_CODE = ROOT / "extracted/exefs/code.bin"
DEFAULT_FINAL_IMAGE = (
    ROOT
    / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin"
)
DEFAULT_FINAL_IPS = (
    ROOT
    / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.ips"
)
DEFAULT_SEED = ROOT / "build/h2-runtime/profile-pristine-user"
MOD_IPS_RELATIVE = Path("load/mods/00040000000E5C00/exefs/code.ips")

# Guest addresses
ADDR_TITLE_TOP_READY = 0x001EA15C       # Title_Top state 5 after help message (flag_94 == 1)
ADDR_TITLE_RESET_FOR_BOOT = 0x001EA3D8  # Title_Top return from TitleConfig
ADDR_TITLE_CONFIG_INIT = 0x002F4CA0     # titleConfig_func_002f4ca0
ADDR_TITLE_CONFIG_CALC = 0x001EA928     # TitleConfig_Calc entry
ADDR_TITLE_CONFIG_CALC_S1 = 0x001EAA60  # TitleConfig_Calc state 1 body
ADDR_TITLE_CONFIG_CALC_RET = 0x001EAFE4 # TitleConfig_Calc common return
ADDR_TITLE_CONFIG_DRAW = 0x002CAFD0     # TitleConfig_Draw entry
ADDR_TITLE_CONFIG_SEC = 0x002CAEF0      # TitleConfig_Secondary entry
ADDR_TITLE_CONFIG_READY = 0x002FC0EC    # TitleConfig_IsReady entry
ADDR_LOGICAL_QUERY = 0x002C1830         # camp_func_002C1830(control_id, mode)
ADDR_UI_LIST_CURSOR_SET_SELECTED_ROW = 0x0029EDFC  # UiListCursor_SetSelectedRow(cursor, row)
ADDR_UI_INPUT_TRIGGER2 = 0x002BFFBC     # UiInput_Trigger2 entry
ADDR_TITLE_MAIN_INIT = 0x001EB02C       # titleMain_func_001eb02c

ADDR_G_TITLE_MAIN_WORK = 0x0044E300
ADDR_G_TITLE_CONFIG_WORK = 0x0044E2D0
ADDR_G_CONFIG_BYTES = 0x0044E0F8
TITLE_CONFIG_WORK_SIZE = 0x158          # 344 bytes
MAX_CALC_STATE_POLLS = 120


def rsp_read_mem(rsp: Rsp, addr: int, size: int) -> bytes:
    raw = rsp.request(f"m{addr:x},{size:x}".encode("ascii"))
    if raw.startswith(b"E") or len(raw) != size * 2:
        raise ProbeError(f"memory read failed at {addr:#x}+{size:#x}: {raw!r}")
    return bytes.fromhex(raw.decode("ascii"))


def rsp_write_mem(rsp: Rsp, addr: int, data: bytes) -> None:
    hex_payload = data.hex().encode("ascii")
    reply = rsp.request(f"M{addr:x},{len(data):x}:".encode("ascii") + hex_payload)
    if reply != b"OK":
        raise ProbeError(f"memory write failed at {addr:#x}+{len(data):#x}: {reply!r}")


def rsp_read_u32(rsp: Rsp, addr: int) -> int:
    return struct.unpack("<I", rsp_read_mem(rsp, addr, 4))[0]


def rsp_write_u32(rsp: Rsp, addr: int, val: int) -> None:
    rsp_write_mem(rsp, addr, struct.pack("<I", val & 0xFFFFFFFF))


def rsp_set_bp(rsp: Rsp, addr: int, length: int = 4) -> None:
    if rsp.request(f"Z0,{addr:x},{length:x}".encode("ascii")) != b"OK":
        raise ProbeError(f"failed to set breakpoint at {addr:#x}")


def rsp_clear_bp(rsp: Rsp, addr: int, length: int = 4) -> None:
    if rsp.request(f"z0,{addr:x},{length:x}".encode("ascii")) != b"OK":
        raise ProbeError(f"failed to clear breakpoint at {addr:#x}")


def run_to_bp(rsp: Rsp, addr: int, length: int = 4) -> int:
    rsp_set_bp(rsp, addr, length)
    try:
        rsp.continue_to_stop()
        pc = decode_r0(rsp.request(b"p0f"))
        if pc != addr:
            raise ProbeError(f"expected stop at {addr:#x}, got {pc:#x}")
        return pc
    finally:
        rsp_clear_bp(rsp, addr, length)


def encode_logical_query_stub(control_id: int, mode: int) -> bytes:
    """5-instruction ARM stub for 0x002C1830:
    cmp r0, #control_id
    cmpeq r1, #mode
    moveq r0, #1
    movne r0, #0
    bx lr
    """
    words = [
        0xE3500000 | (control_id & 0xFF),
        0x03510000 | (mode & 0xFF),
        0x03A00001,
        0x13A00000,
        0xE12FFF1E,
    ]
    return struct.pack("<5I", *words)


def rsp_write_reg(rsp: Rsp, reg_index: int, value: int) -> None:
    """Write one ARM GDB register using the target's little-endian P packet."""
    if not 0 <= reg_index <= 15:
        raise ValueError(f"invalid ARM register index: {reg_index}")
    raw = struct.pack("<I", value & 0xFFFFFFFF).hex().encode("ascii")
    reply = rsp.request(f"P{reg_index:x}=".encode("ascii") + raw)
    if reply != b"OK":
        raise ProbeError(f"register write P{reg_index:x} failed: {reply!r}")


def rsp_call_set_selected_row(rsp: Rsp, cursor: int, row: int) -> dict:
    """Call the game's cursor setter at a Calc entry and return to that entry."""
    original_lr = decode_r0(rsp.request(b"p0e"))
    rsp_set_bp(rsp, ADDR_TITLE_CONFIG_CALC)
    try:
        rsp_write_reg(rsp, 0, cursor)
        rsp_write_reg(rsp, 1, row)
        rsp_write_reg(rsp, 14, ADDR_TITLE_CONFIG_CALC)
        rsp_write_reg(rsp, 15, ADDR_UI_LIST_CURSOR_SET_SELECTED_ROW)
        stop = rsp.continue_to_stop()
        pc = decode_r0(rsp.request(b"p0f"))
        if pc != ADDR_TITLE_CONFIG_CALC:
            raise ProbeError(
                f"cursor setter returned to {pc:#x}, expected {ADDR_TITLE_CONFIG_CALC:#x}; "
                f"stop={stop!r}"
            )
    finally:
        rsp_clear_bp(rsp, ADDR_TITLE_CONFIG_CALC)
        rsp_write_reg(rsp, 14, original_lr)
    return {
        "function": f"0x{ADDR_UI_LIST_CURSOR_SET_SELECTED_ROW:08x}",
        "cursor": f"0x{cursor:08x}",
        "requested_row": row,
        "return_pc": f"0x{ADDR_TITLE_CONFIG_CALC:08x}",
    }


def wait_for_calc_state(
    rsp: Rsp, target_state: int = 1, max_polls: int = MAX_CALC_STATE_POLLS
) -> int:
    """Wait a bounded number of TitleConfig_Calc entries for a work state."""
    for _ in range(max_polls):
        run_to_bp(rsp, ADDR_TITLE_CONFIG_CALC)
        work_ptr = rsp_read_u32(rsp, ADDR_G_TITLE_CONFIG_WORK)
        state = rsp_read_u32(rsp, work_ptr + 8) if work_ptr else 0
        lr = decode_r0(rsp.request(b"p0e"))
        if state == target_state:
            return work_ptr
        run_to_bp(rsp, lr)
    raise ProbeError(
        f"TitleConfig state {target_state} was not reached after {max_polls} Calc polls"
    )


def wait_for_title_reset_after_confirm(rsp: Rsp, max_ready_checks: int = 40) -> dict:
    """Poll the real title readiness gate for a bounded number of guest frames."""
    observations = []
    for frame in range(max_ready_checks):
        run_to_bp(rsp, ADDR_TITLE_CONFIG_READY)
        work_ptr = rsp_read_u32(rsp, ADDR_G_TITLE_CONFIG_WORK)
        work_state = rsp_read_u32(rsp, work_ptr + 8) if work_ptr else None
        return_pc = decode_r0(rsp.request(b"p0e"))
        run_to_bp(rsp, return_pc)
        ready = decode_r0(rsp.request(b"p00"))
        observations.append({
            "frame": frame + 1,
            "work_ptr": f"0x{work_ptr:08x}",
            "work_state": work_state,
            "ready_return": ready,
            "return_pc": f"0x{return_pc:08x}",
        })
        if ready == 1:
            run_to_bp(rsp, ADDR_TITLE_RESET_FOR_BOOT)
            return {"completed": True, "observations": observations}
    return {"completed": False, "observations": observations}


def enter_audio_settings_from_title(rsp: Rsp) -> bytes:
    """Use the same bounded title caller path and return the original query body."""
    run_to_bp(rsp, ADDR_TITLE_TOP_READY)
    title_work = rsp_read_u32(rsp, ADDR_G_TITLE_MAIN_WORK)
    if not title_work:
        raise ProbeError("TitleMainWork is null at the state-5 gate")
    rsp_write_u32(rsp, title_work + 0x08, 2)
    rsp_write_mem(rsp, title_work + 0x63, b"\x01")
    run_to_bp(rsp, ADDR_TITLE_CONFIG_INIT)
    run_to_bp(rsp, ADDR_TITLE_CONFIG_DRAW)
    work_ptr = wait_for_calc_state(rsp, 1)
    if not work_ptr:
        raise ProbeError("TitleConfigWork is null after entering Audio Settings")
    return rsp_read_mem(rsp, ADDR_LOGICAL_QUERY, 20)


def detach_rsp_for_clean_shutdown(rsp: Rsp) -> str:
    """Detach the debugger so the guest can run while Azahar handles WM_CLOSE."""
    reply = rsp.request(b"D")
    if reply != b"OK":
        raise ProbeError(f"GDB RSP detach failed before clean shutdown: {reply!r}")
    return reply.decode("ascii")


def request_clean_window_close(
    proc: subprocess.Popen,
    timeout: float = 15.0,
    rsp: Rsp | None = None,
    resume_socket: socket.socket | None = None,
) -> dict:
    """Detach/resume the guest, then post WM_CLOSE only to this child."""
    if os.name != "nt":
        return {"requested": False, "clean_exit": False, "reason": "Windows-only close helper"}
    user32 = ctypes.windll.user32
    pid = int(proc.pid)
    window_pids: list[int] = []
    windows: list[int] = []
    enum_proc_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def collect(hwnd, _lparam):
        window_pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if window_pid.value == pid:
            window_pids.append(window_pid.value)
            if user32.IsWindowVisible(hwnd) and not user32.GetWindow(hwnd, 4):
                windows.append(int(hwnd))
        return True

    callback = enum_proc_type(collect)
    user32.EnumWindows(callback, 0)
    if not windows:
        return {
            "requested": False,
            "clean_exit": False,
            "reason": "no visible top-level window owned by staged child PID",
            "owned_window_count": len(window_pids),
        }
    detach_reply = None
    if rsp is not None:
        detach_reply = detach_rsp_for_clean_shutdown(rsp)
    elif resume_socket is not None:
        # Compatibility path for callers without an RSP wrapper.
        resume_socket.sendall(frame(b"c"))
    posted = []
    for hwnd in windows:
        posted.append(bool(user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)))
    try:
        exit_code = proc.wait(timeout=timeout)
        return {
            "requested": any(posted),
            "clean_exit": any(posted),
            "exit_code": exit_code,
            "window_count": len(windows),
            "post_message_results": posted,
            "rsp_detach_reply": detach_reply,
        }
    except subprocess.TimeoutExpired:
        return {
            "requested": any(posted),
            "clean_exit": False,
            "window_count": len(windows),
            "post_message_results": posted,
            "rsp_detach_reply": detach_reply,
            "reason": f"child did not exit within {timeout:g}s after WM_CLOSE",
        }


def persistent_profile_snapshot(user_dir: Path) -> dict[str, str]:
    """Hash profile files outside runtime logs, shader cache, and the patch file."""
    result = {}
    for path in sorted(user_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(user_dir).as_posix()
        if relative.startswith(("log/", "shaders/")) or relative == MOD_IPS_RELATIVE.as_posix():
            continue
        result[relative] = sha256(path)
    return result


def profile_snapshot_delta(before: dict[str, str], after: dict[str, str]) -> dict[str, list[str]]:
    """Report persistent profile files added, removed, or changed between snapshots."""
    before_paths, after_paths = set(before), set(after)
    return {
        "added": sorted(after_paths - before_paths),
        "removed": sorted(before_paths - after_paths),
        "changed": sorted(
            path for path in before_paths & after_paths if before[path] != after[path]
        ),
    }


def runtime_dependency_manifest(dll_source_exe: Path) -> list[dict]:
    """Hash the DLL/plugin assets copied beside each staged private executable."""
    root = dll_source_exe.resolve(strict=True).parent
    candidates = [
        path for path in root.iterdir()
        if path.is_file() and path.suffix.lower() == ".dll"
    ]
    plugins = root / "plugins"
    if plugins.is_dir():
        candidates.extend(path for path in plugins.rglob("*") if path.is_file())
    return [
        {
            "source_path": str(path.resolve(strict=True)),
            "staged_relative_path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(candidates)
    ]


def _config_state_signature(state: dict | None) -> tuple | None:
    if not isinstance(state, dict):
        return None
    config = state.get("g_ConfigBytes_hex")
    work_hash = state.get("TitleConfigWork_normalized_sha256")
    if not isinstance(config, str) or not isinstance(work_hash, str):
        return None
    return (
        config,
        work_hash,
        state.get("state_08"),
        state.get("bgm_28"),
        state.get("se_2c"),
        state.get("voice_30"),
    )


def compare_h2_lifecycle(original: dict, patched: dict) -> dict:
    """Compare observed lifecycle behavior without requiring the game to persist settings."""
    original_reentered = bool(original.get("same_session_reentry_proven"))
    patched_reentered = bool(patched.get("same_session_reentry_proven"))
    original_reentry = original.get("same_session_reentry")
    patched_reentry = patched.get("same_session_reentry")
    same_session_reentry_matches = original_reentered == patched_reentered
    if same_session_reentry_matches and original_reentered:
        original_signature = _config_state_signature(original_reentry)
        patched_signature = _config_state_signature(patched_reentry)
        same_session_reentry_matches = (
            original_signature is not None and original_signature == patched_signature
        )

    original_readiness = original.get("post_confirm_readiness_trace")
    patched_readiness = patched.get("post_confirm_readiness_trace")
    original_ready = (
        original_readiness.get("completed") if isinstance(original_readiness, dict) else None
    )
    patched_ready = (
        patched_readiness.get("completed") if isinstance(patched_readiness, dict) else None
    )
    readiness_outcome_matches = (
        isinstance(original_ready, bool)
        and isinstance(patched_ready, bool)
        and original_ready == patched_ready
    )

    original_restart = _config_state_signature(original.get("restart_reentry"))
    patched_restart = _config_state_signature(patched.get("restart_reentry"))
    restart_state_matches = (
        original_restart is not None and original_restart == patched_restart
    )
    original_persisted = original.get("restart_persistence_match")
    patched_persisted = patched.get("restart_persistence_match")
    persistence_outcome_matches = (
        isinstance(original_persisted, bool)
        and isinstance(patched_persisted, bool)
        and original_persisted == patched_persisted
    )
    clean_shutdowns_match = all(
        isinstance(run.get(key), dict) and run[key].get("clean_exit") is True
        for run in (original, patched)
        for key in ("clean_shutdown", "restart_clean_shutdown")
    )
    paired_lifecycle_behavior_matched = all((
        same_session_reentry_matches,
        readiness_outcome_matches,
        restart_state_matches,
        persistence_outcome_matches,
        clean_shutdowns_match,
    ))
    full_controlled_lifecycle_completed = all((
        paired_lifecycle_behavior_matched,
        original_reentered,
        patched_reentered,
        original_ready is True,
        patched_ready is True,
    ))
    return {
        "paired_lifecycle_behavior_matched": paired_lifecycle_behavior_matched,
        "same_session_reentry_outcome_matched": same_session_reentry_matches,
        "same_session_reentry_original": original_reentered,
        "same_session_reentry_patched": patched_reentered,
        "readiness_outcome_matched": readiness_outcome_matches,
        "readiness_completed_original": original_ready,
        "readiness_completed_patched": patched_ready,
        "restart_state_matched_original_vs_patched": restart_state_matches,
        "restart_matches_confirmation_original": original_persisted,
        "restart_matches_confirmation_patched": patched_persisted,
        "restart_persistence_outcome_matched": persistence_outcome_matches,
        "clean_shutdowns_matched": clean_shutdowns_match,
        "full_controlled_lifecycle_completed": full_controlled_lifecycle_completed,
    }


def attach_to_staged_child(proc: subprocess.Popen, port: int, packet_timeout: float):
    deadline = time.monotonic() + 45.0
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise ProbeError(f"restarted Azahar exited prematurely with code {proc.returncode}")
        owner = listener_owner(port)
        if owner is not None:
            break
        time.sleep(0.2)
    owner = listener_owner(port)
    if owner != proc.pid:
        raise ProbeError(f"restarted loopback port {port} owner mismatch: {owner} != {proc.pid}")
    sock = socket.create_connection(("127.0.0.1", port), timeout=packet_timeout)
    rsp = Rsp(sock, timeout=packet_timeout)
    try:
        supported = rsp.request(b"qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+")
        if not supported or supported.startswith(b"E"):
            raise ProbeError(f"restarted qSupported failed: {supported!r}")
        if rsp.request(b"!") != b"OK":
            raise ProbeError("restarted extended mode rejected")
        proc_info = rsp.request(b"qfProcessInfo")
        if not proc_info.startswith(b"pid:"):
            raise ProbeError(f"restarted qfProcessInfo failed: {proc_info!r}")
        pid_hex = proc_info.split(b":", 1)[1].split(b";", 1)[0]
        stop = rsp.request(b"vAttach;" + pid_hex)
        if not stop.startswith(b"T"):
            raise ProbeError(f"restarted vAttach failed: {stop!r}")
        return sock, rsp, pid_hex.decode("ascii")
    except BaseException:
        sock.close()
        raise


def snapshot_config_state(rsp: Rsp, label: str) -> dict:
    config_bytes = rsp_read_mem(rsp, ADDR_G_CONFIG_BYTES, 8)
    work_ptr = rsp_read_u32(rsp, ADDR_G_TITLE_CONFIG_WORK)
    work_bytes = rsp_read_mem(rsp, work_ptr, TITLE_CONFIG_WORK_SIZE) if work_ptr else b""
    # Extract key fields from TitleConfigWork while zeroing heap pointer fields
    # (offset 0x00 calc_task, 0x14C script_bf, 0x150 msg_mbm, 0x154 script_ctx)
    # for deterministic structural comparison, plus full raw hex.
    normalized = bytearray(work_bytes)
    if len(normalized) == TITLE_CONFIG_WORK_SIZE:
        for ptr_off in (0x00, 0x14C, 0x150, 0x154):
            normalized[ptr_off:ptr_off + 4] = b"\x00\x00\x00\x00"
    state = struct.unpack_from("<I", work_bytes, 0x08)[0] if work_bytes else None
    bgm = struct.unpack_from("<I", work_bytes, 0x28)[0] if work_bytes else None
    se = struct.unpack_from("<I", work_bytes, 0x2C)[0] if work_bytes else None
    voice = struct.unpack_from("<I", work_bytes, 0x30)[0] if work_bytes else None
    backup = work_bytes[0x34:0x3C].hex() if work_bytes else ""
    return {
        "label": label,
        "g_ConfigBytes_hex": config_bytes.hex(),
        "work_ptr": f"0x{work_ptr:08x}",
        "state_08": state,
        "bgm_28": bgm,
        "se_2c": se,
        "voice_30": voice,
        "backup_34_hex": backup,
        "TitleConfigWork_normalized_sha256": hashlib.sha256(normalized).hexdigest(),
        "TitleConfigWork_normalized_hex": bytes(normalized).hex(),
        "TitleConfigWork_raw_hex": work_bytes.hex(),
    }


def step_calc_with_query(
    rsp: Rsp, orig_query_bytes: bytes, control_id: int, mode: int, label: str,
    selected_row: int, expected_option_value: int | None = None,
) -> dict:
    """Execute exactly one TitleConfig_Calc State-1 frame with (control_id, mode) active."""
    run_to_bp(rsp, ADDR_TITLE_CONFIG_CALC)
    lr = decode_r0(rsp.request(b"p0e"))
    row_event = None
    work_ptr = rsp_read_u32(rsp, ADDR_G_TITLE_CONFIG_WORK)
    if not work_ptr:
        raise ProbeError("TitleConfigWork is null while selecting an option row")
    row_event = rsp_call_set_selected_row(rsp, work_ptr + 0xE8, selected_row)
    # The callback's original caller LR is required for the one-frame stop.
    rsp_write_reg(rsp, 14, lr)
    rsp_write_mem(rsp, ADDR_LOGICAL_QUERY, encode_logical_query_stub(control_id, mode))
    try:
        run_to_bp(rsp, lr)
    finally:
        rsp_write_mem(rsp, ADDR_LOGICAL_QUERY, orig_query_bytes)
    state = snapshot_config_state(rsp, label)
    state["scripted_query"] = {
        "control_id": control_id,
        "mode": mode,
        "stub_return": 1,
        "all_other_queries_return": 0,
    }
    if row_event is not None:
        state["cursor_setter_event"] = row_event
    if expected_option_value is not None:
        field = (0x28, 0x2C, 0x30)[selected_row]
        actual = struct.unpack_from("<I", bytes.fromhex(state["TitleConfigWork_raw_hex"]), field)[0]
        if actual != expected_option_value:
            raise ProbeError(
                f"{label}: option row {selected_row} at work+{field:#x} was {actual}, "
                f"expected {expected_option_value}"
            )
        state["expected_selected_work_value"] = expected_option_value
    return state


def prepare_runtime_qt_config(raw: bytes) -> bytes:
    """Set unthrottled emulation and suppress only the disposable-profile exit prompt."""
    return (
        raw.replace(b"frame_limit\\default=true", b"frame_limit\\default=false")
        .replace(b"frame_limit=100", b"frame_limit=0")
        .replace(b"use_vsync\\default=true", b"use_vsync\\default=false")
        .replace(b"use_vsync=true", b"use_vsync=false")
        .replace(b"confirmClose\\default=true", b"confirmClose\\default=false")
        .replace(b"confirmClose=true", b"confirmClose=false")
    )


def stage_portable_dir(
    private_exe: Path,
    dll_source_exe: Path,
    cci_path: Path,
    seed_root: Path,
    stage_dir: Path,
    ips_bytes: bytes | None,
) -> tuple[Path, Path]:
    stage_dir.mkdir(parents=True)
    app_dir = stage_dir / "app"
    app_dir.mkdir()
    shutil.copy2(private_exe, app_dir / "azahar.exe")
    dll_root = dll_source_exe.parent
    for item in dll_root.iterdir():
        if item.is_file() and item.suffix.lower() == ".dll":
            shutil.copy2(item, app_dir / item.name)
    plugins = dll_root / "plugins"
    if plugins.is_dir():
        shutil.copytree(plugins, app_dir / "plugins")
    user_dir = app_dir / "user"
    user_dir.mkdir()
    provision_profile(seed_root, user_dir)
    # Copy seed config to staged user dir
    config_src = seed_root / "config"
    if config_src.is_dir():
        shutil.copytree(config_src, user_dir / "config", dirs_exist_ok=True)
    # Force unthrottled frame rate (frame_limit = 0, no vsync) in both global and per-game config
    qt_ini = user_dir / "config/qt-config.ini"
    if qt_ini.exists():
        qt_ini.write_bytes(prepare_runtime_qt_config(qt_ini.read_bytes()))
    game_ini = user_dir / "config/custom/00040000000E5C00.ini"
    if game_ini.exists():
        raw = game_ini.read_bytes()
        crlf = b"\r\n" if b"\r\n" in raw else b"\n"
        raw = (
            raw.replace(b"frame_limit\\use_global=true", b"frame_limit\\use_global=false" + crlf + b"frame_limit=0")
            .replace(b"use_vsync\\use_global=true", b"use_vsync\\use_global=false" + crlf + b"use_vsync=false")
        )
        game_ini.write_bytes(raw)
    if ips_bytes is not None:
        ips_dest = user_dir / MOD_IPS_RELATIVE
        ips_dest.parent.mkdir(parents=True, exist_ok=True)
        ips_dest.write_bytes(ips_bytes)
    return app_dir / "azahar.exe", cci_path


def execute_h2_scenario(
    executable: Path,
    staged_cci: Path,
    port: int,
    startup_timeout: float,
    packet_timeout: float,
) -> dict:
    profile_at_start = persistent_profile_snapshot(executable.parent / "user")
    reserve_port(port)
    stdout_path = executable.parent.parent / "azahar.stdout.log"
    stderr_path = executable.parent.parent / "azahar.stderr.log"
    command = [str(executable), "-g", str(port), str(staged_cci)]
    with stdout_path.open("w", encoding="utf-8") as out_f, stderr_path.open("w", encoding="utf-8") as err_f:
        proc = subprocess.Popen(
            command,
            cwd=executable.parent,
            stdin=subprocess.DEVNULL,
            stdout=out_f,
            stderr=err_f,
            shell=False,
        )
        try:
            deadline = time.monotonic() + startup_timeout
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise ProbeError(f"Azahar exited prematurely with code {proc.returncode}")
                owner = listener_owner(port)
                if owner is not None:
                    break
                time.sleep(0.2)
            owner = listener_owner(port)
            if owner != proc.pid:
                raise ProbeError(f"loopback port {port} owner mismatch: {owner} != {proc.pid}")

            sock = socket.create_connection(("127.0.0.1", port), timeout=packet_timeout)
            rsp = Rsp(sock, timeout=packet_timeout)
            try:
                supported = rsp.request(b"qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+")
                if not supported or supported.startswith(b"E"):
                    raise ProbeError(f"qSupported failed: {supported!r}")
                if rsp.request(b"!") != b"OK":
                    raise ProbeError("extended mode rejected")
                proc_info = rsp.request(b"qfProcessInfo")
                if not proc_info.startswith(b"pid:"):
                    raise ProbeError(f"qfProcessInfo failed: {proc_info!r}")
                pid_hex = proc_info.split(b":", 1)[1].split(b";", 1)[0]
                stop = rsp.request(b"vAttach;" + pid_hex)
                if not stop.startswith(b"T"):
                    raise ProbeError(f"vAttach failed: {stop!r}")

                # 0. Fast-advance past the initial "Touch Screen / Press A" StartMenu
                orig_trigger2 = rsp_read_mem(rsp, ADDR_UI_INPUT_TRIGGER2, 8)
                stub_trigger2 = bytes([0x01, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1])  # mov r0, #1; bx lr
                rsp_write_mem(rsp, ADDR_UI_INPUT_TRIGGER2, stub_trigger2)
                try:
                    run_to_bp(rsp, ADDR_TITLE_MAIN_INIT)
                finally:
                    rsp_write_mem(rsp, ADDR_UI_INPUT_TRIGGER2, orig_trigger2)

                # 1. Run until Title_Top State 5 ready
                run_to_bp(rsp, ADDR_TITLE_TOP_READY)
                title_work = rsp_read_u32(rsp, ADDR_G_TITLE_MAIN_WORK)

                # Select row 2 (Audio Settings) and trigger touch confirmation (flag_63 = 1)
                rsp_write_u32(rsp, title_work + 0x08, 2)
                rsp_write_mem(rsp, title_work + 0x63, b"\x01")

                # 2. Verify TitleConfig_Init (0x002F4CA0) and TitleConfig_Draw (0x002CAFD0)
                run_to_bp(rsp, ADDR_TITLE_CONFIG_INIT)
                run_to_bp(rsp, ADDR_TITLE_CONFIG_DRAW)

                # 3. Reach TitleConfig_Calc (0x001EA928) until State == 1
                orig_query_bytes = rsp_read_mem(rsp, ADDR_LOGICAL_QUERY, 20)
                wait_for_calc_state(rsp, target_state=1)

                checkpoints: list[dict] = []
                scripted_actions: list[dict] = []

                def do_step(
                    control_id: int, mode: int, label: str, row: int, expected_value: int
                ) -> dict:
                    snap = step_calc_with_query(
                        rsp, orig_query_bytes, control_id, mode, label, row, expected_value
                    )
                    work_offset = (0x28, 0x2C, 0x30)[row]
                    scripted_actions.append({
                        "label": label,
                        "input": snap["scripted_query"],
                        "cursor_setter_event": snap["cursor_setter_event"],
                        "selected_row": row,
                        "selected_work_offset": f"0x{work_offset:02x}",
                        "expected_work_value": expected_value,
                        "observed_work_value": struct.unpack_from(
                            "<I", bytes.fromhex(snap["TitleConfigWork_raw_hex"]), work_offset
                        )[0],
                        "all_option_values": [snap["bgm_28"], snap["se_2c"], snap["voice_30"]],
                        "work_snapshot_sha256": snap["TitleConfigWork_normalized_sha256"],
                        "g_ConfigBytes_hex": snap["g_ConfigBytes_hex"],
                    })
                    return snap

                initial = snapshot_config_state(rsp, "initial_entry")
                if initial["g_ConfigBytes_hex"] != "3250503000000000":
                    raise ProbeError(
                        f"initial config differs from pinned scenario: {initial['g_ConfigBytes_hex']}"
                    )
                initial_work = bytes.fromhex(initial["TitleConfigWork_raw_hex"])
                if tuple(struct.unpack_from("<I", initial_work, off)[0] for off in (0x28, 0x2C, 0x30)) != (8, 8, 8):
                    raise ProbeError("initial BGM/SE/Voice work values are not all 8")
                checkpoints.append(initial)

                # 4. BGM Left (decrement from 5 -> 4)
                checkpoints.append(
                    do_step(4, 0, "bgm_dec_5_to_4", 0, 7)
                )

                # 5. B-cancel (control_id=1, mode=1): restores g_ConfigBytes and exits
                checkpoints.append(
                    do_step(1, 1, "bgm_b_cancel_triggered", 0, 7)
                )

                # Verify TitleConfig_IsReady (0x002FC0EC), TitleConfig_Secondary (0x002CAEF0),
                # and return to Title_ResetForBoot (0x001EA3D8)
                run_to_bp(rsp, ADDR_TITLE_CONFIG_READY)
                run_to_bp(rsp, ADDR_TITLE_RESET_FOR_BOOT)

                # 6. Re-enter TitleConfig from Title_Top
                run_to_bp(rsp, ADDR_TITLE_TOP_READY)
                title_work = rsp_read_u32(rsp, ADDR_G_TITLE_MAIN_WORK)
                rsp_write_u32(rsp, title_work + 0x08, 2)
                rsp_write_mem(rsp, title_work + 0x63, b"\x01")
                wait_for_calc_state(rsp, target_state=1)
                checkpoints.append(snapshot_config_state(rsp, "reentry_after_cancel"))

                # 7. Both directions and clamp endpoints on each row. The extra
                # endpoint input is an explicit stability check after the clamp.
                row_names = ("bgm", "se", "voice")
                for row, row_name in enumerate(row_names):
                    for step_idx in range(9):  # 8 -> 0, then one more decrement at 0
                        value = max(0, 8 - (step_idx + 1))
                        snap = do_step(
                            4, 0, f"{row_name}_min_clamp_step_{step_idx + 1}", row, value
                        )
                    checkpoints.append(snap)

                    snap = do_step(9, 1, f"{row_name}_y_default_reset", row, 8)
                    checkpoints.append(snap)
                    for step_idx in range(3):  # 8 -> 10, then one more increment at 10
                        value = min(10, 8 + (step_idx + 1))
                        snap = do_step(
                            3, 0, f"{row_name}_max_clamp_step_{step_idx + 1}", row, value
                        )
                    checkpoints.append(snap)

                    for step_idx, value in enumerate((9, 8, 7), 1):
                        snap = do_step(
                            4, 0, f"{row_name}_return_to_7_step_{step_idx}", row, value
                        )
                    checkpoints.append(snap)

                # 11. Trigger A-confirm (control_id=0, mode=1) -> transitions to state 2
                checkpoints.append(
                    do_step(0, 1, "a_confirm_state2", 2, 7)
                )

                # Confirm should commit all three selected values into g_ConfigBytes.
                confirmed = snapshot_config_state(rsp, "confirmed_before_restart")
                if (confirmed["bgm_28"], confirmed["se_2c"], confirmed["voice_30"]) != (7, 7, 7):
                    raise ProbeError("confirmed TitleConfigWork values were not all 7")
                checkpoints.append(confirmed)
                # Poll the real title readiness gate and bound the transition.
                readiness_result = wait_for_title_reset_after_confirm(rsp)
                confirmed_reentry_query = None
                confirmed_reentry = None
                if readiness_result["completed"]:
                    confirmed_reentry_query = enter_audio_settings_from_title(rsp)
                    confirmed_reentry = snapshot_config_state(
                        rsp, "reentry_after_confirm_same_process"
                    )
                    checkpoints.append(confirmed_reentry)
                pre_restart_profile = persistent_profile_snapshot(executable.parent / "user")

                first_close = request_clean_window_close(proc, rsp=rsp)
                sock.close()
                if not first_close["clean_exit"]:
                    raise ProbeError(f"first Azahar process did not close cleanly: {first_close}")
                first_listener_after_exit = listener_owner(port)
                if first_listener_after_exit is not None:
                    raise ProbeError(f"GDB listener remained after first clean exit: {first_listener_after_exit}")
                profile_after_first_clean_exit = persistent_profile_snapshot(
                    executable.parent / "user"
                )

                # Relaunch this exact staged profile and observe the game config again.
                restart_proc = subprocess.Popen(
                    [str(executable), "-g", str(port), str(staged_cci)],
                    cwd=executable.parent,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=False,
                )
                restart_sock = None
                try:
                    restart_sock, restart_rsp, restart_pid_hex = attach_to_staged_child(
                        restart_proc, port, packet_timeout
                    )
                    restart_trigger = rsp_read_mem(restart_rsp, ADDR_UI_INPUT_TRIGGER2, 8)
                    rsp_write_mem(restart_rsp, ADDR_UI_INPUT_TRIGGER2, stub_trigger2)
                    try:
                        run_to_bp(restart_rsp, ADDR_TITLE_MAIN_INIT)
                    finally:
                        rsp_write_mem(restart_rsp, ADDR_UI_INPUT_TRIGGER2, restart_trigger)
                    restart_query = enter_audio_settings_from_title(restart_rsp)
                    restart_state = snapshot_config_state(restart_rsp, "reentry_after_process_restart")
                    restart_persistence_match = (
                        restart_state["g_ConfigBytes_hex"] == confirmed["g_ConfigBytes_hex"]
                        and (restart_state["bgm_28"], restart_state["se_2c"], restart_state["voice_30"])
                        == (7, 7, 7)
                    )
                    checkpoints.append(restart_state)
                    post_restart_profile = persistent_profile_snapshot(executable.parent / "user")
                    second_close = request_clean_window_close(
                        restart_proc, rsp=restart_rsp
                    )
                    restart_sock.close()
                    restart_sock = None
                    profile_after_restart_clean_exit = persistent_profile_snapshot(
                        executable.parent / "user"
                    )
                finally:
                    if restart_sock is not None:
                        restart_sock.close()
                    if restart_proc.poll() is None:
                        restart_proc.terminate()
                        try:
                            restart_proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            restart_proc.kill()
                            restart_proc.wait(timeout=5)
                if not second_close["clean_exit"]:
                    raise ProbeError(f"restarted Azahar process did not close cleanly: {second_close}")
                restart_listener_after_exit = listener_owner(port)
                if restart_listener_after_exit is not None:
                    raise ProbeError(f"GDB listener remained after restart exit: {restart_listener_after_exit}")
                out_f.flush()
                err_f.flush()
                return {
                    "host_pid": proc.pid,
                    "argv": command,
                    "working_directory": str(executable.parent.resolve()),
                    "stdout_path": str(stdout_path.resolve()),
                    "stdout_sha256": sha256(stdout_path),
                    "stderr_path": str(stderr_path.resolve()),
                    "stderr_sha256": sha256(stderr_path),
                    "emulated_pid_hex": pid_hex.decode("ascii"),
                    "loopback_port": port,
                    "staged_executable_path": str(executable.resolve()),
                    "staged_executable_sha256": sha256(executable),
                    "staged_cci_path": str(staged_cci.resolve()),
                    "staged_cci_sha256": sha256(staged_cci),
                    "checkpoints": checkpoints,
                    "scripted_actions": scripted_actions,
                    "same_session_confirmation": confirmed,
                    "same_session_reentry": confirmed_reentry,
                    "same_session_reentry_proven": confirmed_reentry is not None,
                    "post_confirm_readiness_trace": readiness_result,
                    "restart_reentry": restart_state,
                    "restart_persistence_match": restart_persistence_match,
                    "restart_emulated_pid_hex": restart_pid_hex,
                    "restart_host_pid": restart_proc.pid,
                    "restart_argv": [str(executable), "-g", str(port), str(staged_cci)],
                    "restart_working_directory": str(executable.parent.resolve()),
                    "restart_executable_sha256": sha256(executable),
                    "listener_owner_after_first_exit": first_listener_after_exit,
                    "listener_owner_after_restart_exit": restart_listener_after_exit,
                    "clean_shutdown": first_close,
                    "restart_clean_shutdown": second_close,
                    "profile_at_scenario_start": profile_at_start,
                    "profile_before_restart": pre_restart_profile,
                    "profile_after_first_clean_exit": profile_after_first_clean_exit,
                    "profile_after_restart_before_exit": post_restart_profile,
                    "profile_after_restart_clean_exit": profile_after_restart_clean_exit,
                    "persistent_profile_deltas": {
                        "start_to_confirmation": profile_snapshot_delta(
                            profile_at_start, pre_restart_profile
                        ),
                        "confirmation_to_first_clean_exit": profile_snapshot_delta(
                            pre_restart_profile, profile_after_first_clean_exit
                        ),
                        "first_exit_to_restart_observation": profile_snapshot_delta(
                            profile_after_first_clean_exit, post_restart_profile
                        ),
                        "restart_observation_to_clean_exit": profile_snapshot_delta(
                            post_restart_profile, profile_after_restart_clean_exit
                        ),
                    },
                    "confirmed_reentry_query_body_sha256": (
                        hashlib.sha256(confirmed_reentry_query).hexdigest()
                        if confirmed_reentry_query is not None else None
                    ),
                    "restart_query_body_sha256": hashlib.sha256(restart_query).hexdigest(),
                }
            finally:
                sock.close()
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--azahar", type=Path, default=DEFAULT_PRIVATE_EXE)
    parser.add_argument("--dll-source", type=Path, default=DEFAULT_DLL_SOURCE)
    parser.add_argument("--game", type=Path, default=DEFAULT_CCI)
    parser.add_argument("--original-code", type=Path, default=DEFAULT_ORIGINAL_CODE)
    parser.add_argument("--final-image", type=Path, default=DEFAULT_FINAL_IMAGE)
    parser.add_argument("--final-ips", type=Path, default=DEFAULT_FINAL_IPS)
    parser.add_argument("--profile-seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--base-port", type=int, default=59940)
    parser.add_argument("--startup-timeout", type=float, default=45.0)
    parser.add_argument("--packet-timeout", type=float, default=240.0)
    args = parser.parse_args(argv)

    out_dir = args.output_dir.resolve()
    if out_dir.exists():
        raise SystemExit(f"Output directory already exists: {out_dir}")
    out_dir.mkdir(parents=True)

    original_code = args.original_code.read_bytes()
    final_image = args.final_image.read_bytes()
    ips_bytes = args.final_ips.read_bytes()
    if apply_ips(original_code, ips_bytes) != final_image:
        raise SystemExit("IPS application onto original code.bin did not reproduce code.h2-final.bin")

    profile_seed_path = args.profile_seed.resolve(strict=True)
    profile_seed_hashes_before = persistent_profile_snapshot(profile_seed_path)
    runtime_support_assets_before = runtime_dependency_manifest(args.dll_source)
    private_azahar_sha256_before = sha256(args.azahar.resolve(strict=True))

    orig_exe, orig_cci = stage_portable_dir(
        args.azahar.resolve(strict=True),
        args.dll_source.resolve(strict=True),
        args.game.resolve(strict=True),
        args.profile_seed.resolve(strict=True),
        out_dir / "original",
        ips_bytes=None,
    )
    patch_exe, patch_cci = stage_portable_dir(
        args.azahar.resolve(strict=True),
        args.dll_source.resolve(strict=True),
        args.game.resolve(strict=True),
        args.profile_seed.resolve(strict=True),
        out_dir / "patched",
        ips_bytes=ips_bytes,
    )

    print("Running autonomous GDB RSP scenario on ORIGINAL profile...", flush=True)
    orig_res = execute_h2_scenario(
        orig_exe, orig_cci, args.base_port, args.startup_timeout, args.packet_timeout
    )
    print("Running autonomous GDB RSP scenario on PATCHED (code.h2-final.ips) profile...", flush=True)
    patch_res = execute_h2_scenario(
        patch_exe, patch_cci, args.base_port + 1, args.startup_timeout, args.packet_timeout
    )

    comparisons = []
    all_matched = len(orig_res["checkpoints"]) == len(patch_res["checkpoints"])
    for o_cp, p_cp in zip(orig_res["checkpoints"], patch_res["checkpoints"]):
        cfg_eq = o_cp["g_ConfigBytes_hex"] == p_cp["g_ConfigBytes_hex"]
        work_eq = (
            o_cp["TitleConfigWork_normalized_sha256"]
            == p_cp["TitleConfigWork_normalized_sha256"]
        )
        step_ok = o_cp["label"] == p_cp["label"] and cfg_eq and work_eq
        all_matched = all_matched and step_ok
        comparisons.append({
            "label": o_cp["label"],
            "passed": step_ok,
            "g_ConfigBytes_equal": cfg_eq,
            "g_ConfigBytes_hex": o_cp["g_ConfigBytes_hex"],
            "patched_g_ConfigBytes_hex": p_cp["g_ConfigBytes_hex"],
            "TitleConfigWork_normalized_equal": work_eq,
            "state_08": o_cp["state_08"],
            "bgm_28": o_cp["bgm_28"],
            "se_2c": o_cp["se_2c"],
            "voice_30": o_cp["voice_30"],
        })

    def normalized_actions(run: dict) -> list[dict]:
        return [
            {
                key: event[key]
                for key in (
                    "label", "input", "selected_row", "selected_work_offset",
                    "expected_work_value", "observed_work_value", "all_option_values",
                    "work_snapshot_sha256", "g_ConfigBytes_hex",
                )
            }
            for event in run["scripted_actions"]
        ]

    input_trace_equal = normalized_actions(orig_res) == normalized_actions(patch_res)
    all_matched = all_matched and input_trace_equal
    lifecycle = compare_h2_lifecycle(orig_res, patch_res)
    lifecycle_ok = lifecycle["paired_lifecycle_behavior_matched"]
    profile_seed_hashes_after = persistent_profile_snapshot(profile_seed_path)
    runtime_support_assets_after = runtime_dependency_manifest(args.dll_source)
    private_azahar_sha256_after = sha256(args.azahar.resolve(strict=True))
    profile_seed_unchanged = profile_seed_hashes_before == profile_seed_hashes_after
    runtime_support_assets_unchanged = runtime_support_assets_before == runtime_support_assets_after
    private_azahar_unchanged = private_azahar_sha256_before == private_azahar_sha256_after
    all_matched = all((
        all_matched,
        lifecycle_ok,
        profile_seed_unchanged,
        runtime_support_assets_unchanged,
        private_azahar_unchanged,
    ))

    report = {
        "schema_version": 1,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "passed": all_matched,
        "paired_scripted_behavior_matched": all_matched,
        "controlled_lifecycle": lifecycle,
        "h2_full_acceptance_supported": False,
        "physical_input_mapping_proven": False,
        "input_scheduling_proven": False,
        "input_method": (
            "The RSP driver calls the original UiListCursor_SetSelectedRow helper and "
            "temporarily replaces the logical query with a deterministic one-frame "
            "response stub. This verifies the Calc behavior for the scripted logical "
            "conditions; it does not prove physical controller mapping or input scheduling."
        ),
        "scripted_action_count": len(orig_res["scripted_actions"]),
        "scripted_input_traces_equal": input_trace_equal,
        "lifecycle_and_restart_behavior_matched": lifecycle_ok,
        "controlled_lifecycle_completed": lifecycle["full_controlled_lifecycle_completed"],
        "same_session_reentry_both": all(
            run["same_session_reentry_proven"] for run in (orig_res, patch_res)
        ),
        "restart_persistence_outcome_matches_original": lifecycle[
            "restart_persistence_outcome_matched"
        ],
        "runner_path": str(Path(__file__).resolve()),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "startup_timeout_seconds": args.startup_timeout,
        "packet_timeout_seconds": args.packet_timeout,
        "base_port": args.base_port,
        "private_azahar_exe": str(args.azahar.resolve()),
        "private_azahar_sha256": sha256(args.azahar.resolve()),
        "original_code_sha256": hashlib.sha256(original_code).hexdigest(),
        "final_image_sha256": hashlib.sha256(final_image).hexdigest(),
        "final_ips_sha256": hashlib.sha256(ips_bytes).hexdigest(),
        "cci_path": str(args.game.resolve()),
        "cci_sha256": sha256(args.game.resolve()),
        "profile_seed_path": str(profile_seed_path),
        "profile_seed_files_before": profile_seed_hashes_before,
        "profile_seed_files_after": profile_seed_hashes_after,
        "profile_seed_unchanged": profile_seed_unchanged,
        "runtime_support_root": str(args.dll_source.resolve(strict=True).parent),
        "runtime_support_assets_before": runtime_support_assets_before,
        "runtime_support_assets_after": runtime_support_assets_after,
        "runtime_support_assets_unchanged": runtime_support_assets_unchanged,
        "private_azahar_sha256_before": private_azahar_sha256_before,
        "private_azahar_sha256_after": private_azahar_sha256_after,
        "private_azahar_unchanged": private_azahar_unchanged,
        "original_run": orig_res,
        "patched_run": patch_res,
        "checkpoint_comparisons": comparisons,
    }
    report_path = out_dir / "autonomous-gdb-verification.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote verification report: {report_path}", flush=True)
    if not all_matched:
        print("VERIFICATION FAILED: mismatch detected", file=sys.stderr)
        return 1
    print(f"VERIFICATION PASSED: {sum(c['passed'] for c in comparisons)}/{len(comparisons)} checkpoints passed byte-for-byte!", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
