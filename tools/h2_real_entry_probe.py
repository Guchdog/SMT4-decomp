#!/usr/bin/env python3
"""Bounded H2 probe: enter Audio Settings through real title input.

This probe deliberately does NOT write TitleMainWork state/selection. It hooks
the documented logical input helper for one frame and observes whether the real
state-5 navigation/confirmation path opens titleConfig. Read-only guest state
except for the temporary 8/16-byte input stubs, which are restored.
"""
from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import h2_autonomous_gdb_verify as base  # noqa: E402

ADDR_UI_INPUT_TRIGGER = 0x002B902C
ADDR_UI_INPUT_TRIGGER2 = base.ADDR_UI_INPUT_TRIGGER2
ADDR_TITLE_TOP_READY = base.ADDR_TITLE_TOP_READY
ADDR_TITLE_MAIN_INIT = base.ADDR_TITLE_MAIN_INIT
ADDR_TITLE_CONFIG_INIT = base.ADDR_TITLE_CONFIG_INIT
ADDR_TITLE_CONFIG_CALC = base.ADDR_TITLE_CONFIG_CALC
ADDR_TITLE_CONFIG_DRAW = base.ADDR_TITLE_CONFIG_DRAW
ADDR_G_TITLE_MAIN_WORK = base.ADDR_G_TITLE_MAIN_WORK
ADDR_G_TITLE_CONFIG_WORK = base.ADDR_G_TITLE_CONFIG_WORK


def stub_arm_return_one_if_r0(target: int) -> bytes:
    """cmp r0,#target; moveq r0,#1; movne r0,#0; bx lr"""
    words = [0xE3500000 | (target & 0xFF), 0x03A00001, 0x13A00000, 0xE12FFF1E]
    return struct.pack("<4I", *words)


def stub_arm_return_one() -> bytes:
    """mov r0,#1; bx lr"""
    return struct.pack("<2I", 0x03A00001, 0xE12FFF1E)


def run_to_any(rsp, addresses: list[int], timeout_label: str) -> int:
    for addr in addresses:
        base.rsp_set_bp(rsp, addr)
    try:
        base.Rsp.continue_to_stop(rsp)
        pc = base.decode_r0(rsp.request(b"p0f"))
        return pc
    finally:
        for addr in addresses:
            base.rsp_clear_bp(rsp, addr)


def step_once(rsp) -> int:
    """Execute one guest instruction so a re-added breakpoint at the current
    PC does not immediately re-trigger."""
    rsp.sock.sendall(base.frame(b"s"))
    ack = rsp._exact(1)
    if ack != b"+":
        raise RuntimeError(f"unexpected step ack {ack!r}")
    reply = rsp._packet()
    if not reply.startswith(b"T"):
        raise RuntimeError(f"step returned unexpected stop reply {reply!r}")
    return base.decode_r0(rsp.request(b"p0f"))


def read_title(rsp) -> dict:
    work = base.rsp_read_u32(rsp, ADDR_G_TITLE_MAIN_WORK)
    if not work:
        return {"work": 0, "selected_row": None, "state_9c": None}
    return {
        "work": work,
        "selected_row": base.rsp_read_u32(rsp, work + 0x08),
        "state_9c": base.rsp_read_u32(rsp, work + 0x9C),
        "flag_63": base.rsp_read_mem(rsp, work + 0x63, 1)[0],
    }


def read_config_work(rsp) -> dict:
    work = base.rsp_read_u32(rsp, ADDR_G_TITLE_CONFIG_WORK)
    if not work:
        return {"work": 0}
    state = base.rsp_read_u32(rsp, work + 8)
    raw = base.rsp_read_mem(rsp, work, base.TITLE_CONFIG_WORK_SIZE)
    offs = (0x28, 0x2C, 0x30)
    vals = [struct.unpack_from("<I", raw, off)[0] for off in offs]
    return {"work": work, "state_08": state, "values_28_2c_30": vals}


ADDR_CONFIG_HELPER = 0x00286928
ADDR_TITLE_CONFIG_READY = 0x002FC0EC


def poll_readiness_with_helper(rsp, max_events: int = 400) -> dict:
    """Interleave readiness polls with 0x00286928 hits and field observations."""
    events: list[dict] = []
    for _ in range(max_events):
        pc = run_to_any(rsp, [ADDR_CONFIG_HELPER, ADDR_TITLE_CONFIG_READY], "poll")
        if pc == ADDR_CONFIG_HELPER:
            r0 = base.decode_r0(rsp.request(b"p00"))
            r2 = base.decode_r0(rsp.request(b"p02"))
            lr = base.decode_r0(rsp.request(b"p0e"))
            field_plus8 = base.rsp_read_u32(rsp, r0 + 8) if r0 else None
            step_once(rsp)
            run_to_any(rsp, [lr], "helper return")
            ret = base.decode_r0(rsp.request(b"p00"))
            events.append({
                "kind": "helper", "r0": f"0x{r0:08x}", "r2": r2,
                "field_plus8": field_plus8, "ret": ret,
            })
            step_once(rsp)
            continue
        lr = base.decode_r0(rsp.request(b"p0e"))
        step_once(rsp)
        run_to_any(rsp, [lr], "ready return")
        ready = base.decode_r0(rsp.request(b"p00"))
        events.append({
            "kind": "ready", "ready": ready,
            "config": read_config_work(rsp), "title": read_title(rsp),
        })
        step_once(rsp)
        if ready == 1:
            return {"completed": True, "events": events}
    return {"completed": False, "events": events}


def press_and_advance(rsp, stub_addr: int, stub: bytes, anchors: list[int]) -> int:
    original = base.rsp_read_mem(rsp, stub_addr, len(stub))
    base.rsp_write_mem(rsp, stub_addr, stub)
    try:
        return run_to_any(rsp, anchors, "input advance")
    finally:
        base.rsp_write_mem(rsp, stub_addr, original)


def probe(rsp, timeout_s: float, confirm_test: bool = False) -> dict:
    events: list[dict] = []
    start = time.monotonic()

    # Fast-advance the start menu with a one-frame A stub.
    press_and_advance(rsp, ADDR_UI_INPUT_TRIGGER2, stub_arm_return_one(), [ADDR_TITLE_MAIN_INIT])
    events.append({"step": "start_menu_a", "t": time.monotonic() - start})

    # Wait for title state 5.
    base.run_to_bp(rsp, ADDR_TITLE_TOP_READY)
    events.append({"step": "title_state5", "t": time.monotonic() - start, "title": read_title(rsp)})

    # Diagnostic trace of the state-5 control path around the navigation and
    # confirmation slices. This identifies whether the game re-enters the
    # per-tick trigger poll while the title is at the state-5 anchor.
    trace_addrs = [0x001E9D08, 0x001E9D0C, 0x001E9D1C, 0x001E9D48, 0x001E9D78,
                   ADDR_TITLE_TOP_READY]
    pc_trace: list[str] = []
    for _ in range(48):
        pc = run_to_any(rsp, trace_addrs, "pc trace")
        pc_trace.append(f"0x{pc:08x}")
        if pc in (0x001E9D48, 0x001E9D78):
            pc_trace[-1] += f"(r0={base.decode_r0(rsp.request(b'p00'))})"
        step_once(rsp)
    events.append({"step": "pc_trace", "pcs": pc_trace, "title": read_title(rsp)})

    # Move the title cursor down until row 2 is selected. Step over the
    # current anchor first, then keep the logical Down response installed
    # across one full tick; restore it as soon as the row is observed.
    down_stub = stub_arm_return_one_if_r0(6)
    original_down = base.rsp_read_mem(rsp, ADDR_UI_INPUT_TRIGGER, len(down_stub))
    try:
        for index in range(120):
            if read_title(rsp).get("selected_row") == 2:
                break
            step_once(rsp)
            base.rsp_write_mem(rsp, ADDR_UI_INPUT_TRIGGER, down_stub)
            pc = run_to_any(rsp, [ADDR_TITLE_TOP_READY], "down tick")
            events.append({
                "step": f"down_tick_{index + 1}",
                "t": time.monotonic() - start,
                "pc": pc,
                "title": read_title(rsp),
            })
    finally:
        base.rsp_write_mem(rsp, ADDR_UI_INPUT_TRIGGER, original_down)

    before_confirm = read_title(rsp)
    if before_confirm.get("selected_row") != 2:
        return {"entered": False, "reason": "cursor did not reach row 2", "events": events,
                "title": before_confirm, "elapsed_s": time.monotonic() - start}

    # Confirm with the real A helper, then stop at the config initializer or
    # back at the title-state anchor.
    step_once(rsp)
    pc = press_and_advance(
        rsp, ADDR_UI_INPUT_TRIGGER2, stub_arm_return_one(),
        [ADDR_TITLE_CONFIG_INIT, ADDR_TITLE_TOP_READY],
    )
    events.append({
        "step": "a_confirm",
        "t": time.monotonic() - start,
        "pc": pc,
        "title": read_title(rsp),
    })

    entered = pc == ADDR_TITLE_CONFIG_INIT
    result = {
        "entered": entered,
        "events": events,
        "title": read_title(rsp),
        "config": read_config_work(rsp),
        "elapsed_s": time.monotonic() - start,
    }
    if not entered:
        result["reason"] = "A confirm did not reach titleConfig init"
        return result

    # Observe the draw callback and the first Calc state-1 entry.
    base.run_to_bp(rsp, ADDR_TITLE_CONFIG_DRAW)
    calc_entries = []
    for _ in range(base.MAX_CALC_STATE_POLLS):
        base.run_to_bp(rsp, ADDR_TITLE_CONFIG_CALC)
        calc_entries.append(read_config_work(rsp))
        if calc_entries[-1].get("state_08") == 1:
            break
        lr = base.decode_r0(rsp.request(b"p0e"))
        base.run_to_bp(rsp, lr)
    result["calc_entries"] = calc_entries
    result["config_after_calc"] = read_config_work(rsp)

    if not confirm_test:
        return result

    # Edit each option one step down (8 -> 7), confirm with A, and poll the
    # real title readiness gate. This is the exact point that the shortcut
    # entry path could never complete.
    orig_query = base.rsp_read_mem(rsp, base.ADDR_LOGICAL_QUERY, 20)
    actions = []
    step_once(rsp)
    for row in (0, 1, 2):
        snap = base.step_calc_with_query(
            rsp, orig_query, 4, 0, f"real_entry_row{row}_dec", row, 7
        )
        actions.append({
            "label": f"row{row}_dec",
            "values": [snap["bgm_28"], snap["se_2c"], snap["voice_30"]],
            "g_ConfigBytes_hex": snap["g_ConfigBytes_hex"],
            "state": snap["state_08"],
        })
    confirm = base.step_calc_with_query(
        rsp, orig_query, 0, 1, "real_entry_a_confirm", 2, 7
    )
    actions.append({
        "label": "a_confirm",
        "values": [confirm["bgm_28"], confirm["se_2c"], confirm["voice_30"]],
        "g_ConfigBytes_hex": confirm["g_ConfigBytes_hex"],
        "state": confirm["state_08"],
    })
    readiness = poll_readiness_with_helper(rsp, max_events=400)
    result["confirm_test"] = {
        "actions": actions,
        "readiness": readiness,
        "config_after": read_config_work(rsp),
        "title_after": read_title(rsp),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--azahar", type=Path, default=base.DEFAULT_PRIVATE_EXE)
    parser.add_argument("--dll-source", type=Path, default=base.DEFAULT_DLL_SOURCE)
    parser.add_argument("--game", type=Path, default=base.DEFAULT_CCI)
    parser.add_argument("--profile-seed", type=Path, default=base.DEFAULT_SEED)
    parser.add_argument("--stage-root", type=Path, default=Path("C:/h2rt-realentry-001"))
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "build/agent-work/H2-semantic/h2-real-entry-probe/run001")
    parser.add_argument("--base-port", type=int, default=60440)
    parser.add_argument("--startup-timeout", type=float, default=60.0)
    parser.add_argument("--packet-timeout", type=float, default=240.0)
    parser.add_argument("--confirm-test", action="store_true",
                        help="after entry, edit the three options, confirm, and poll readiness")
    args = parser.parse_args(argv)

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stage_root = args.stage_root.resolve()
    if stage_root.exists():
        raise SystemExit(f"stage root already exists: {stage_root}")

    exe, cci = base.stage_portable_dir(
        args.azahar.resolve(strict=True),
        args.dll_source.resolve(strict=True),
        args.game.resolve(strict=True),
        args.profile_seed.resolve(strict=True),
        stage_root,
        ips_bytes=None,
    )

    base.reserve_port(args.base_port)
    log_dir = out_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    command = [str(exe), "-g", str(args.base_port), str(cci)]
    report = {"command": command, "stage_root": str(stage_root)}
    with (log_dir / "azahar.stdout.log").open("w", encoding="utf-8") as out_f, \
         (log_dir / "azahar.stderr.log").open("w", encoding="utf-8") as err_f:
        proc = subprocess.Popen(command, cwd=exe.parent, stdin=subprocess.DEVNULL,
                                stdout=out_f, stderr=err_f, shell=False)
        try:
            deadline = time.monotonic() + args.startup_timeout
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError(f"Azahar exited early: {proc.returncode}")
                if base.listener_owner(args.base_port) == proc.pid:
                    break
                time.sleep(0.2)
            if base.listener_owner(args.base_port) != proc.pid:
                raise RuntimeError("GDB listener owner mismatch")

            sock = __import__("socket").create_connection(("127.0.0.1", args.base_port),
                                                           timeout=args.packet_timeout)
            rsp = base.Rsp(sock, timeout=args.packet_timeout)
            try:
                supported = rsp.request(b"qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+")
                if not supported or supported.startswith(b"E"):
                    raise RuntimeError(f"qSupported failed: {supported!r}")
                if rsp.request(b"!") != b"OK":
                    raise RuntimeError("extended mode rejected")
                proc_info = rsp.request(b"qfProcessInfo")
                pid_hex = proc_info.split(b":", 1)[1].split(b";", 1)[0]
                if not rsp.request(b"vAttach;" + pid_hex).startswith(b"T"):
                    raise RuntimeError("vAttach failed")
                report["probe"] = probe(rsp, args.packet_timeout, args.confirm_test)
            finally:
                try:
                    rsp.request(b"D")
                except Exception:
                    pass
                sock.close()
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass

    report_json = out_dir / "probe-report.json"
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report.get("probe", {}), indent=2))
    return 0 if report.get("probe", {}).get("entered") else 1


if __name__ == "__main__":
    raise SystemExit(main())
