#!/usr/bin/env python3
"""Paired original-vs-cumulative-patched full-lifecycle GDB RSP verifier for H2.

Drives both original and cumulative-patched SMT IV in the private loopback-bound
Azahar build through:
  1. Initial TitleMain -> Audio Settings entry (8/8/8)
  2. B-cancel -> Title_ResetForBoot -> same-session re-entry (8/8/8)
  3. Min/Y-default/Max/7 sweep across BGM, SE, and Voice
  4. A-confirm -> State 2 ComWin wait (instruction 12 + instruction 14) ->
     State 3 -> State 4 -> Title_ResetForBoot
  5. Same-session re-entry into Audio Settings (7/7/7, 2d46462800000000)
  6. Clean WM_CLOSE shutdown -> cold-restart persistence check (8/8/8) ->
     second clean WM_CLOSE shutdown
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import h2_autonomous_gdb_verify as base
from tools.h2_azahar_rsp_probe import (
    ProbeError,
    Rsp,
    decode_r0,
    listener_owner,
    reserve_port,
    sha256,
)
from tools.h2_calc_code_patch import apply_ips

DEFAULT_CUMULATIVE_IMAGE = (
    ROOT
    / "build/agent-work/H2-semantic/h2-full-lifecycle-runtime/run-001/staged-image/code.h2-cumulative.bin"
)
DEFAULT_CUMULATIVE_IPS = (
    ROOT
    / "build/agent-work/H2-semantic/h2-full-lifecycle-runtime/run-001/staged-image/code.h2-cumulative.ips"
)

ADDR_COMWIN_DEFAULT_PTR = 0x0043E18C
ADDR_COMWIN_SPECIAL_PTR = 0x0043E190


def wait_for_title_reset_after_confirm_with_comwin(
    rsp: Rsp,
    orig_query_bytes: bytes,
    max_ready_checks: int = 120,
) -> dict:
    """Poll TitleConfig_IsReady while resolving State-2 ComWin confirmation waits.

    In State 2, /camp/config.bf SoundConfig_Change executes:
      - Instruction 12 (handler 8 -> 0x00221168 -> 0x00286928, selector 6):
        auto-advances default_object[8] to 4 around frame 39.
      - Instruction 14 (handler 8 -> 0x001DC7B4 -> 0x00286928, selector 11):
        opens special_object while default_object[8] == 4; ComWin_Calc waits for
        logical A trigger (0x002C1830(0, 1) == 1) to close default_object (4->3->0)
        and advance special_object (2->1->5), transitioning TitleConfigWork.state
        from 2 -> 3 -> 4 and returning TitleConfig_IsReady() == 1.
    """
    observations: list[dict] = []
    query_a_active = False
    stub_a = base.encode_logical_query_stub(0, 1)

    try:
        for frame_idx in range(max_ready_checks):
            base.run_to_bp(rsp, base.ADDR_TITLE_CONFIG_READY)
            work_ptr = base.rsp_read_u32(rsp, base.ADDR_G_TITLE_CONFIG_WORK)
            work_state = base.rsp_read_u32(rsp, work_ptr + 8) if work_ptr else None

            default_obj = base.rsp_read_u32(rsp, ADDR_COMWIN_DEFAULT_PTR)
            special_obj = base.rsp_read_u32(rsp, ADDR_COMWIN_SPECIAL_PTR)
            default_state = (
                base.rsp_read_mem(rsp, default_obj + 8, 1)[0] if default_obj else None
            )
            special_state = (
                base.rsp_read_mem(rsp, special_obj + 8, 1)[0] if special_obj else None
            )

            return_pc = decode_r0(rsp.request(b"p0e"))
            base.run_to_bp(rsp, return_pc)
            ready = decode_r0(rsp.request(b"p00"))

            observations.append({
                "frame": frame_idx + 1,
                "work_ptr": f"0x{work_ptr:08x}",
                "work_state": work_state,
                "ready_return": ready,
                "return_pc": f"0x{return_pc:08x}",
                "default_obj": f"0x{default_obj:08x}",
                "default_state": default_state,
                "special_obj": f"0x{special_obj:08x}",
                "special_state": special_state,
                "query_a_active": query_a_active,
            })

            if ready == 1:
                if query_a_active:
                    base.rsp_write_mem(rsp, base.ADDR_LOGICAL_QUERY, orig_query_bytes)
                    query_a_active = False
                base.run_to_bp(rsp, base.ADDR_TITLE_RESET_FOR_BOOT)
                return {"completed": True, "observations": observations}

            should_supply_a = (
                work_state == 2
                and (default_state == 4 or special_state in (1, 2))
            )
            if should_supply_a and not query_a_active:
                base.rsp_write_mem(rsp, base.ADDR_LOGICAL_QUERY, stub_a)
                query_a_active = True
            elif not should_supply_a and query_a_active:
                base.rsp_write_mem(rsp, base.ADDR_LOGICAL_QUERY, orig_query_bytes)
                query_a_active = False

        return {"completed": False, "observations": observations}
    finally:
        if query_a_active:
            base.rsp_write_mem(rsp, base.ADDR_LOGICAL_QUERY, orig_query_bytes)


def execute_full_lifecycle(
    executable: Path,
    staged_cci: Path,
    log_copy_dir: Path,
    port: int,
    startup_timeout: float,
    packet_timeout: float,
) -> dict:
    log_copy_dir.mkdir(parents=True, exist_ok=True)
    profile_at_start = base.persistent_profile_snapshot(executable.parent / "user")
    reserve_port(port)
    stdout_path = executable.parent.parent / "azahar.stdout.log"
    stderr_path = executable.parent.parent / "azahar.stderr.log"
    command = [str(executable), "-g", str(port), str(staged_cci)]

    with stdout_path.open("w", encoding="utf-8") as out_f, stderr_path.open(
        "w", encoding="utf-8"
    ) as err_f:
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
                    raise ProbeError(
                        f"Azahar exited prematurely with code {proc.returncode}"
                    )
                if listener_owner(port) is not None:
                    break
                time.sleep(0.2)
            owner = listener_owner(port)
            if owner != proc.pid:
                raise ProbeError(
                    f"loopback port {port} owner mismatch: {owner} != {proc.pid}"
                )

            sock = socket.create_connection(("127.0.0.1", port), timeout=packet_timeout)
            rsp = Rsp(sock, timeout=packet_timeout)
            try:
                supported = rsp.request(
                    b"qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+"
                )
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

                # 0. Fast-advance past initial StartMenu
                orig_trigger2 = base.rsp_read_mem(rsp, base.ADDR_UI_INPUT_TRIGGER2, 8)
                stub_trigger2 = bytes([0x01, 0x00, 0xA0, 0xE3, 0x1E, 0xFF, 0x2F, 0xE1])
                base.rsp_write_mem(rsp, base.ADDR_UI_INPUT_TRIGGER2, stub_trigger2)
                try:
                    base.run_to_bp(rsp, base.ADDR_TITLE_MAIN_INIT)
                finally:
                    base.rsp_write_mem(rsp, base.ADDR_UI_INPUT_TRIGGER2, orig_trigger2)

                # 1. Enter Audio Settings from Title_Top State 5
                orig_query_bytes = base.enter_audio_settings_from_title(rsp)

                checkpoints: list[dict] = []
                scripted_actions: list[dict] = []

                def do_step(
                    control_id: int,
                    mode: int,
                    label: str,
                    row: int,
                    expected_value: int,
                ) -> dict:
                    snap = base.step_calc_with_query(
                        rsp,
                        orig_query_bytes,
                        control_id,
                        mode,
                        label,
                        row,
                        expected_value,
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
                            "<I",
                            bytes.fromhex(snap["TitleConfigWork_raw_hex"]),
                            work_offset,
                        )[0],
                        "all_option_values": [
                            snap["bgm_28"],
                            snap["se_2c"],
                            snap["voice_30"],
                        ],
                        "work_snapshot_sha256": snap["TitleConfigWork_normalized_sha256"],
                        "g_ConfigBytes_hex": snap["g_ConfigBytes_hex"],
                    })
                    return snap

                initial = base.snapshot_config_state(rsp, "initial_entry")
                if initial["g_ConfigBytes_hex"] != "3250503000000000":
                    raise ProbeError(
                        f"initial config differs from pinned scenario: {initial['g_ConfigBytes_hex']}"
                    )
                if (initial["bgm_28"], initial["se_2c"], initial["voice_30"]) != (8, 8, 8):
                    raise ProbeError("initial BGM/SE/Voice work values are not all 8")
                checkpoints.append(initial)

                # 2. BGM Left (8 -> 7), then B-cancel -> Title_ResetForBoot -> re-entry
                checkpoints.append(do_step(4, 0, "bgm_dec_5_to_4", 0, 7))
                checkpoints.append(do_step(1, 1, "bgm_b_cancel_triggered", 0, 7))
                base.run_to_bp(rsp, base.ADDR_TITLE_CONFIG_READY)
                base.run_to_bp(rsp, base.ADDR_TITLE_RESET_FOR_BOOT)

                base.enter_audio_settings_from_title(rsp)
                checkpoints.append(base.snapshot_config_state(rsp, "reentry_after_cancel"))

                # 3. Min / Y-default / Max / 7 sweep across BGM, SE, Voice
                for row, row_name in enumerate(("bgm", "se", "voice")):
                    for step_idx in range(9):
                        value = max(0, 8 - (step_idx + 1))
                        snap = do_step(
                            4, 0, f"{row_name}_min_clamp_step_{step_idx + 1}", row, value
                        )
                    checkpoints.append(snap)

                    snap = do_step(9, 1, f"{row_name}_y_default_reset", row, 8)
                    checkpoints.append(snap)
                    for step_idx in range(3):
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

                # 4. A-confirm -> State 2 -> ComWin wait -> State 3 -> State 4 -> Title_ResetForBoot
                checkpoints.append(do_step(0, 1, "a_confirm_state2", 2, 7))
                confirmed = base.snapshot_config_state(rsp, "confirmed_before_restart")
                if (confirmed["bgm_28"], confirmed["se_2c"], confirmed["voice_30"]) != (7, 7, 7):
                    raise ProbeError("confirmed TitleConfigWork values were not all 7")
                checkpoints.append(confirmed)

                readiness_result = wait_for_title_reset_after_confirm_with_comwin(
                    rsp, orig_query_bytes
                )
                if not readiness_result["completed"]:
                    raise ProbeError(
                        "State-2 ComWin wait did not complete Title_ResetForBoot within poll bound"
                    )

                # 5. Same-session re-entry into Audio Settings after Title_ResetForBoot
                confirmed_reentry_query = base.enter_audio_settings_from_title(rsp)
                confirmed_reentry = base.snapshot_config_state(
                    rsp, "reentry_after_confirm_same_process"
                )
                if (
                    confirmed_reentry["bgm_28"],
                    confirmed_reentry["se_2c"],
                    confirmed_reentry["voice_30"],
                ) != (7, 7, 7):
                    raise ProbeError(
                        f"same-session re-entry values were {(confirmed_reentry['bgm_28'], confirmed_reentry['se_2c'], confirmed_reentry['voice_30'])}, expected (7, 7, 7)"
                    )
                checkpoints.append(confirmed_reentry)
                pre_restart_profile = base.persistent_profile_snapshot(
                    executable.parent / "user"
                )

                # 6. First clean WM_CLOSE shutdown
                first_close = base.request_clean_window_close(proc, rsp=rsp)
                sock.close()
                if not first_close["clean_exit"]:
                    raise ProbeError(
                        f"first Azahar process did not close cleanly: {first_close}"
                    )
                first_listener_after_exit = listener_owner(port)
                if first_listener_after_exit is not None:
                    raise ProbeError(
                        f"GDB listener remained after first clean exit: {first_listener_after_exit}"
                    )
                profile_after_first_clean_exit = base.persistent_profile_snapshot(
                    executable.parent / "user"
                )

                # 7. Cold restart persistence check
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
                    restart_sock, restart_rsp, restart_pid_hex = base.attach_to_staged_child(
                        restart_proc, port, packet_timeout
                    )
                    restart_trigger = base.rsp_read_mem(
                        restart_rsp, base.ADDR_UI_INPUT_TRIGGER2, 8
                    )
                    base.rsp_write_mem(
                        restart_rsp, base.ADDR_UI_INPUT_TRIGGER2, stub_trigger2
                    )
                    try:
                        base.run_to_bp(restart_rsp, base.ADDR_TITLE_MAIN_INIT)
                    finally:
                        base.rsp_write_mem(
                            restart_rsp, base.ADDR_UI_INPUT_TRIGGER2, restart_trigger
                        )
                    restart_query = base.enter_audio_settings_from_title(restart_rsp)
                    restart_state = base.snapshot_config_state(
                        restart_rsp, "reentry_after_process_restart"
                    )
                    restart_persistence_match = (
                        restart_state["g_ConfigBytes_hex"] == confirmed["g_ConfigBytes_hex"]
                        and (
                            restart_state["bgm_28"],
                            restart_state["se_2c"],
                            restart_state["voice_30"],
                        )
                        == (7, 7, 7)
                    )
                    checkpoints.append(restart_state)
                    post_restart_profile = base.persistent_profile_snapshot(
                        executable.parent / "user"
                    )
                    second_close = base.request_clean_window_close(
                        restart_proc, rsp=restart_rsp
                    )
                    restart_sock.close()
                    restart_sock = None
                    profile_after_restart_clean_exit = base.persistent_profile_snapshot(
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
                    raise ProbeError(
                        f"restarted Azahar process did not close cleanly: {second_close}"
                    )
                restart_listener_after_exit = listener_owner(port)
                if restart_listener_after_exit is not None:
                    raise ProbeError(
                        f"GDB listener remained after restart exit: {restart_listener_after_exit}"
                    )

                out_f.flush()
                err_f.flush()
                copied_stdout = log_copy_dir / "azahar.stdout.log"
                copied_stderr = log_copy_dir / "azahar.stderr.log"
                shutil.copy2(stdout_path, copied_stdout)
                shutil.copy2(stderr_path, copied_stderr)

                return {
                    "host_pid": proc.pid,
                    "argv": command,
                    "emulated_pid_hex": pid_hex.decode("ascii"),
                    "loopback_port": port,
                    "staged_executable_sha256": sha256(executable),
                    "staged_cci_sha256": sha256(staged_cci),
                    "stdout_path": str(copied_stdout.resolve()),
                    "stdout_sha256": sha256(copied_stdout),
                    "stderr_path": str(copied_stderr.resolve()),
                    "stderr_sha256": sha256(copied_stderr),
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
                        "start_to_confirmation": base.profile_snapshot_delta(
                            profile_at_start, pre_restart_profile
                        ),
                        "confirmation_to_first_clean_exit": base.profile_snapshot_delta(
                            pre_restart_profile, profile_after_first_clean_exit
                        ),
                        "first_exit_to_restart_observation": base.profile_snapshot_delta(
                            profile_after_first_clean_exit, post_restart_profile
                        ),
                        "restart_observation_to_clean_exit": base.profile_snapshot_delta(
                            post_restart_profile, profile_after_restart_clean_exit
                        ),
                    },
                    "confirmed_reentry_query_body_sha256": hashlib.sha256(
                        confirmed_reentry_query
                    ).hexdigest(),
                    "restart_query_body_sha256": hashlib.sha256(
                        restart_query
                    ).hexdigest(),
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
    parser.add_argument("--azahar", type=Path, default=base.DEFAULT_PRIVATE_EXE)
    parser.add_argument("--dll-source", type=Path, default=base.DEFAULT_DLL_SOURCE)
    parser.add_argument("--game", type=Path, default=base.DEFAULT_CCI)
    parser.add_argument("--original-code", type=Path, default=base.DEFAULT_ORIGINAL_CODE)
    parser.add_argument("--final-image", type=Path, default=DEFAULT_CUMULATIVE_IMAGE)
    parser.add_argument("--final-ips", type=Path, default=DEFAULT_CUMULATIVE_IPS)
    parser.add_argument("--profile-seed", type=Path, default=base.DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--base-port", type=int, default=59960)
    parser.add_argument("--startup-timeout", type=float, default=45.0)
    parser.add_argument("--packet-timeout", type=float, default=240.0)
    args = parser.parse_args(argv)

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    original_code = args.original_code.read_bytes()
    final_image = args.final_image.read_bytes()
    ips_bytes = args.final_ips.read_bytes()
    if apply_ips(original_code, ips_bytes) != final_image:
        raise SystemExit("IPS application onto original code.bin did not reproduce final image")

    profile_seed_path = args.profile_seed.resolve(strict=True)
    profile_seed_hashes_before = base.persistent_profile_snapshot(profile_seed_path)
    runtime_support_assets_before = base.runtime_dependency_manifest(args.dll_source)
    private_azahar_sha256_before = sha256(args.azahar.resolve(strict=True))

    temp_root = Path(tempfile.mkdtemp(prefix="h2lc-"))
    try:
        orig_exe, orig_cci = base.stage_portable_dir(
            args.azahar.resolve(strict=True),
            args.dll_source.resolve(strict=True),
            args.game.resolve(strict=True),
            profile_seed_path,
            temp_root / "orig",
            ips_bytes=None,
        )
        patch_exe, patch_cci = base.stage_portable_dir(
            args.azahar.resolve(strict=True),
            args.dll_source.resolve(strict=True),
            args.game.resolve(strict=True),
            profile_seed_path,
            temp_root / "patch",
            ips_bytes=ips_bytes,
        )

        print("Running full-lifecycle GDB RSP scenario on ORIGINAL profile...", flush=True)
        orig_res = execute_full_lifecycle(
            orig_exe,
            orig_cci,
            out_dir / "original",
            args.base_port,
            args.startup_timeout,
            args.packet_timeout,
        )
        print("Running full-lifecycle GDB RSP scenario on CUMULATIVE PATCHED profile...", flush=True)
        patch_res = execute_full_lifecycle(
            patch_exe,
            patch_cci,
            out_dir / "patched",
            args.base_port + 1,
            args.startup_timeout,
            args.packet_timeout,
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

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
                    "label",
                    "input",
                    "selected_row",
                    "selected_work_offset",
                    "expected_work_value",
                    "observed_work_value",
                    "all_option_values",
                    "work_snapshot_sha256",
                    "g_ConfigBytes_hex",
                )
            }
            for event in run["scripted_actions"]
        ]

    input_trace_equal = normalized_actions(orig_res) == normalized_actions(patch_res)
    lifecycle = base.compare_h2_lifecycle(orig_res, patch_res)
    lifecycle_ok = lifecycle["paired_lifecycle_behavior_matched"]
    profile_seed_hashes_after = base.persistent_profile_snapshot(profile_seed_path)
    runtime_support_assets_after = base.runtime_dependency_manifest(args.dll_source)
    private_azahar_sha256_after = sha256(args.azahar.resolve(strict=True))
    profile_seed_unchanged = profile_seed_hashes_before == profile_seed_hashes_after
    runtime_support_assets_unchanged = runtime_support_assets_before == runtime_support_assets_after
    private_azahar_unchanged = private_azahar_sha256_before == private_azahar_sha256_after

    all_matched = all((
        all_matched,
        input_trace_equal,
        lifecycle_ok,
        lifecycle["full_controlled_lifecycle_completed"],
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
        "private_azahar_exe": str(args.azahar.resolve()),
        "private_azahar_sha256": sha256(args.azahar.resolve()),
        "original_code_sha256": hashlib.sha256(original_code).hexdigest(),
        "final_image_sha256": hashlib.sha256(final_image).hexdigest(),
        "final_ips_sha256": hashlib.sha256(ips_bytes).hexdigest(),
        "cci_path": str(args.game.resolve()),
        "cci_sha256": sha256(args.game.resolve()),
        "profile_seed_unchanged": profile_seed_unchanged,
        "runtime_support_assets_unchanged": runtime_support_assets_unchanged,
        "private_azahar_unchanged": private_azahar_unchanged,
        "original_run": orig_res,
        "patched_run": patch_res,
        "checkpoint_comparisons": comparisons,
    }
    report_path = out_dir / "autonomous-gdb-verification.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote verification report: {report_path}", flush=True)
    if not all_matched:
        print("VERIFICATION FAILED: mismatch or incomplete lifecycle", file=sys.stderr)
        return 1
    print(
        f"VERIFICATION PASSED: {sum(c['passed'] for c in comparisons)}/{len(comparisons)} checkpoints, full controlled lifecycle completed!",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
