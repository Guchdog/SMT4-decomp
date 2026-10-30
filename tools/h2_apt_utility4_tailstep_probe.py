#!/usr/bin/env python3
"""One bounded observation and single step of the APT tail branch.

Z0 temporarily changes guest code. The breakpoint is removed before stepping;
the inherited cleanup removes it again safely and terminates the isolated child.
No explicit M/P/X packets or logical input are sent.
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    import h2_apt_utility4_interior_probe as interior
except ModuleNotFoundError:
    from tools import h2_apt_utility4_interior_probe as interior

base = interior.base
ENTRY = 0x002C5638
TARGET = 0x002C0EFC
TASK_ID = "h2-apt-utility4-tailstep-probe"
RUNTIME_TASK_ID = "h2-apt-utility4-tailstep-probe-runtime"


def verify_tail_contract(raw: bytes) -> dict:
    interior.verify_interior_entry(raw)
    expected = {0x00103E78: 0xE3A00001, 0x00103E80: 0xEB0705E7,
                0x002C5624: 0xE3500000, 0x002C5634: 0x0A000000,
                ENTRY: 0xEAFFEE2F}
    for pc, word in expected.items():
        if base.u32_at(raw, pc) != word:
            raise base.ProbeError(f"tail branch instruction mismatch at {pc:#x}")
    if base.arm_bl_target(0x00103E80, expected[0x00103E80]) != 0x002C5624:
        raise base.ProbeError("upstream ARM BL target changed")
    displacement = expected[ENTRY] & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 1 << 24
    if ENTRY + 8 + (displacement << 2) != TARGET:
        raise base.ProbeError("tail ARM B target changed")
    return {"branch": f"0x{ENTRY:08x}", "destination": f"0x{TARGET:08x}",
            "upstream_bl": "0x00103e80", "upstream_target": "0x002c5624",
            "limit": "static upstream path is conditional; observe the branch and step to confirm execution"}


def stop_thread(stop: bytes) -> bytes:
    match = re.search(rb"(?:^|;)thread:([0-9a-fA-F]+);", stop)
    if not stop.startswith(b"T05") or not match:
        raise base.ProbeError(f"RSP stop lacks SIGTRAP or a simple thread ID: {stop!r}")
    return match.group(1)


def require_one_hit(max_hits: int) -> int:
    if max_hits != 1:
        raise base.ProbeError("tail-step probe requires exactly one hit")
    return max_hits


def collect_one_step(rsp, max_hits: int, capture_timeout: float | None = None,
                     deadline: float | None = None) -> tuple[list[dict], str]:
    require_one_hit(max_hits)
    if deadline is None:
        if capture_timeout is None or capture_timeout <= 0:
            raise base.ProbeError("capture_timeout must be positive")
        deadline = base.time.monotonic() + capture_timeout
    if hasattr(rsp, "set_deadline"):
        rsp.set_deadline(deadline)
    stop, reason = base.continue_until_stop(rsp, deadline)
    if stop is None:
        return [], reason
    thread = stop_thread(stop)
    rsp.request(b"Hg" + thread, expected=b"OK")
    before = base.read_registers(rsp, deadline)
    if before["r15"] != ENTRY:
        raise base.ProbeError("tail-step stopped at an unexpected branch PC")
    rsp.request(f"z0,{ENTRY:x},4".encode("ascii"), expected=b"OK")
    rsp.request(b"Hc" + thread, expected=b"OK")
    stepped = rsp.request(b"s")
    if stop_thread(stepped) != thread:
        raise base.ProbeError("single-step stopped on a different thread")
    rsp.request(b"Hg" + thread, expected=b"OK")
    after = base.read_registers(rsp, deadline)
    if after["r15"] != TARGET or after["r14"] != before["r14"] or after["r13"] != before["r13"]:
        raise base.ProbeError("single-step did not preserve LR/SP and reach the expected target")
    hit = {"index": 1, "pc": f"0x{ENTRY:08x}", "thread": thread.decode("ascii"),
           "lr": interior.classify_entry_lr(before["r14"]),
           "registers": {name: f"0x{value:08x}" for name, value in before.items()},
           "stop_reply": stop.decode("ascii", "replace"),
           "step": {"breakpoint_removed_before_step": True,
                    "stop_reply": stepped.decode("ascii", "replace"),
                    "pc_after": f"0x{after['r15']:08x}",
                    "thread_unchanged": True, "lr_unchanged": True, "sp_unchanged": True}}
    return [hit], "max_hits_reached"


def configure_runner() -> None:
    interior.configure_runner()
    prior_static_contract = base.static_contract
    base.BREAKPOINT = ENTRY
    base.EXPECTED_CALLER_ADDRESSES = ()
    base.TASK_ID = TASK_ID
    base.RUNTIME_TASK_ID = RUNTIME_TASK_ID
    base.ALLOWED_TASK_IDS = {TASK_ID, RUNTIME_TASK_ID}
    base.validate_max_hits = require_one_hit
    base.collect_hits = collect_one_step

    def checked_contract(code_path: Path, run017_log: Path, run028_log: Path) -> dict:
        result = prior_static_contract(code_path, run017_log, run028_log)
        result["tail_step"] = verify_tail_contract(code_path.read_bytes())
        return result

    base.static_contract = checked_contract


def main() -> int:
    configure_runner()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
