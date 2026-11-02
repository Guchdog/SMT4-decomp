#!/usr/bin/env python3
"""Run the autonomous H2 comparison and record runtime hits at 0x00286928."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import h2_autonomous_gdb_verify as base

HELPER = 0x00286928
ACTIVE: dict | None = None
BREAKPOINTS: dict[int, set[int]] = {}
TARGETS: dict[int, int] = {}
ORIGINAL_SET_BP = base.rsp_set_bp
ORIGINAL_CLEAR_BP = base.rsp_clear_bp
ORIGINAL_RUN_TO_BP = base.run_to_bp
ORIGINAL_CONTINUE = base.Rsp.continue_to_stop
ORIGINAL_EXECUTE = base.execute_h2_scenario
ORIGINAL_CALL_SET = base.rsp_call_set_selected_row


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bp_set(rsp, addr: int, length: int = 4) -> None:
    ORIGINAL_SET_BP(rsp, addr, length)
    BREAKPOINTS.setdefault(id(rsp), set()).add(addr)


def bp_clear(rsp, addr: int, length: int = 4) -> None:
    ORIGINAL_CLEAR_BP(rsp, addr, length)
    BREAKPOINTS.setdefault(id(rsp), set()).discard(addr)


def read_reg(rsp, index: int) -> int:
    return base.decode_r0(rsp.request(f"p{index:02x}".encode("ascii")))


def capture_entry(rsp) -> dict:
    sp = read_reg(rsp, 13)
    return {
        "r0": read_reg(rsp, 0), "r1": read_reg(rsp, 1),
        "r2": read_reg(rsp, 2), "r3": read_reg(rsp, 3),
        "sp": sp, "lr": read_reg(rsp, 14),
        "stack_words": [base.rsp_read_u32(rsp, sp), base.rsp_read_u32(rsp, sp + 4)],
    }


def probed_continue_to_stop(rsp) -> bytes:
    """Handle helper-entry stops transparently, then resume to the caller's BP."""
    reply = ORIGINAL_CONTINUE(rsp)
    if ACTIVE is None or HELPER not in BREAKPOINTS.get(id(rsp), set()):
        return reply
    target = TARGETS.get(id(rsp))
    if target is None:
        raise base.ProbeError("helper probe has no enclosing GDB stop target")

    def service_entry() -> tuple[bytes | None, bool]:
        entry = capture_entry(rsp)
        event = {"entry": entry, "return": None}
        ACTIVE["events"].append(event)

        # The original and C++ function both begin with an ARM PUSH. Remove
        # the software breakpoint, execute that instruction once, then re-arm.
        bp_clear(rsp, HELPER)
        step_reply = rsp.request(b"s")
        stepped_pc = read_reg(rsp, 15)
        if not step_reply.startswith(b"T") or stepped_pc != HELPER + 4:
            raise base.ProbeError(
                f"single-step off helper entry failed: reply={step_reply!r}, pc={stepped_pc:#x}"
            )
        bp_set(rsp, HELPER)

        return_pc = entry["lr"]
        transient_return_bp = return_pc != target
        if transient_return_bp:
            bp_set(rsp, return_pc)

        while True:
            reply = ORIGINAL_CONTINUE(rsp)
            stopped_pc = read_reg(rsp, 15)
            if stopped_pc == HELPER:
                outer_stop, completed = service_entry()
                if completed:
                    return outer_stop, True
                continue
            if stopped_pc == return_pc:
                event["return"] = {"pc": stopped_pc, "r0": read_reg(rsp, 0)}
                if transient_return_bp:
                    bp_clear(rsp, return_pc)
                if return_pc == target:
                    return reply, True
                return None, False
            if stopped_pc == target:
                return reply, True
            raise base.ProbeError(f"unexpected runtime stop during helper probe: {stopped_pc:#x}")

    while True:
        pc = read_reg(rsp, 15)
        if pc != HELPER:
            return reply
        stop_reply, reached_target = service_entry()
        if reached_target:
            return stop_reply
        reply = ORIGINAL_CONTINUE(rsp)


def instrumented_run_to_bp(rsp, addr: int, length: int = 4) -> int:
    TARGETS[id(rsp)] = addr
    if ACTIVE is not None and HELPER not in BREAKPOINTS.get(id(rsp), set()):
        bp_set(rsp, HELPER)
    return ORIGINAL_RUN_TO_BP(rsp, addr, length)


def instrumented_call_set_selected_row(rsp, cursor: int, row: int) -> dict:
    TARGETS[id(rsp)] = base.ADDR_TITLE_CONFIG_CALC
    return ORIGINAL_CALL_SET(rsp, cursor, row)


def instrumented_execute(*args, **kwargs) -> dict:
    global ACTIVE
    ACTIVE = {"events": []}
    try:
        result = ORIGINAL_EXECUTE(*args, **kwargs)
        result["helper_probe"] = {"address": hex(HELPER), "events": ACTIVE["events"]}
        return result
    finally:
        ACTIVE = None


base.rsp_set_bp = bp_set
base.rsp_clear_bp = bp_clear
base.Rsp.continue_to_stop = probed_continue_to_stop
base.run_to_bp = instrumented_run_to_bp
base.execute_h2_scenario = instrumented_execute
base.rsp_call_set_selected_row = instrumented_call_set_selected_row


def event_signature(event: dict) -> tuple:
    entry = event["entry"]
    returned = event["return"]
    if returned is None:
        return ()
    return (entry["r0"], entry["r1"], entry["r2"], entry["r3"],
            tuple(entry["stack_words"]), returned["r0"])


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    status = base.main(argv)
    output_arg = None
    for i, value in enumerate(argv):
        if value == "--output-dir" and i + 1 < len(argv):
            output_arg = argv[i + 1]
            break
    if output_arg is None:
        raise SystemExit("--output-dir is required")
    report_path = Path(output_arg).resolve() / "autonomous-gdb-verification.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    original_events = report["original_run"].get("helper_probe", {}).get("events", [])
    patched_events = report["patched_run"].get("helper_probe", {}).get("events", [])
    signatures_equal = (
        len(original_events) == len(patched_events)
        and all(event["return"] is not None for event in original_events + patched_events)
        and [event_signature(x) for x in original_events]
        == [event_signature(x) for x in patched_events]
    )
    report["helper_runtime_probe"] = {
        "address": hex(HELPER),
        "original_hit_count": len(original_events),
        "patched_hit_count": len(patched_events),
        "entry_arguments_and_raw_returns_matched": signatures_equal,
        "original_events": original_events,
        "patched_events": patched_events,
        "interworking": "breakpoint at even ARM entry; raw six ABI words captured",
    }
    report["helper_runtime_probe_sha256"] = sha(
        json.dumps(report["helper_runtime_probe"], sort_keys=True).encode("utf-8")
    )
    report["runner_wrapper_path"] = str(Path(__file__).resolve())
    report["runner_wrapper_sha256"] = sha(Path(__file__).read_bytes())
    report["passed"] = bool(report.get("passed")) and signatures_equal and len(original_events) > 0
    report["paired_scripted_behavior_matched"] = report["passed"]
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"HELPER PROBE original={len(original_events)} patched={len(patched_events)} args/returns_match={signatures_equal}")
    print(f"UPDATED REPORT {report_path} SHA256 {sha(report_path.read_bytes())}")
    return status if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
