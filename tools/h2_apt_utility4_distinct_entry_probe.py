#!/usr/bin/env python3
"""Observe distinct entries by stepping past the temporary software breakpoint.

Z0 and z0 transiently modify guest code. No explicit M/P/X packets or logical
inputs are sent. An ambiguous RSP failure terminates the isolated child before
disconnect through the inherited runner's fatal cleanup.
"""
from __future__ import annotations

try:
    import h2_apt_utility4_interior_probe as interior
    import h2_apt_utility4_tailstep_probe as tailstep
except ModuleNotFoundError:
    from tools import h2_apt_utility4_interior_probe as interior
    from tools import h2_apt_utility4_tailstep_probe as tailstep

base = interior.base
ENTRY = interior.ENTRY
AFTER_FIRST_INSTRUCTION = ENTRY + 4
TASK_ID = "h2-apt-utility4-distinct-entry-probe"
RUNTIME_TASK_ID = "h2-apt-utility4-distinct-entry-probe-runtime"


def collect_distinct_entries(rsp, max_hits: int, capture_timeout: float | None = None,
                             deadline: float | None = None) -> tuple[list[dict], str]:
    base.validate_max_hits(max_hits)
    if deadline is None:
        if capture_timeout is None or capture_timeout <= 0:
            raise base.ProbeError("capture_timeout must be positive")
        deadline = base.time.monotonic() + capture_timeout
    if hasattr(rsp, "set_deadline"):
        rsp.set_deadline(deadline)
    hits = []
    while len(hits) < max_hits:
        stop, reason = base.continue_until_stop(rsp, deadline)
        if stop is None:
            return hits, reason
        thread = tailstep.stop_thread(stop)
        rsp.request(b"Hg" + thread, expected=b"OK")
        before = base.read_registers(rsp, deadline)
        if before["r15"] != ENTRY:
            raise base.ProbeError("distinct-entry probe stopped at an unexpected PC")
        rsp.request(f"z0,{ENTRY:x},4".encode("ascii"), expected=b"OK")
        rsp.request(b"Hc" + thread, expected=b"OK")
        stepped = rsp.request(b"s")
        if tailstep.stop_thread(stepped) != thread:
            raise base.ProbeError("entry step stopped on a different thread")
        rsp.request(b"Hg" + thread, expected=b"OK")
        after = base.read_registers(rsp, deadline)
        if (after["r15"] != AFTER_FIRST_INSTRUCTION or after["r14"] != before["r14"]
                or after["r13"] != before["r13"]):
            raise base.ProbeError("entry step did not advance one ARM instruction preserving LR/SP")
        reinserted = len(hits) + 1 < max_hits
        if reinserted:
            rsp.request(f"Z0,{ENTRY:x},4".encode("ascii"), expected=b"OK")
        hits.append({"index": len(hits) + 1, "pc": f"0x{ENTRY:08x}",
                     "thread": thread.decode("ascii"), "lr": interior.classify_entry_lr(before["r14"]),
                     "registers": {name: f"0x{value:08x}" for name, value in before.items()},
                     "stop_reply": stop.decode("ascii", "replace"),
                     "step": {"breakpoint_removed_before_step": True,
                              "stop_reply": stepped.decode("ascii", "replace"),
                              "pc_after": f"0x{after['r15']:08x}",
                              "thread_unchanged": True, "lr_unchanged": True, "sp_unchanged": True,
                              "breakpoint_reinserted": reinserted}})
    return hits, "max_hits_reached"


def configure_runner() -> None:
    interior.configure_runner()
    base.TASK_ID = TASK_ID
    base.RUNTIME_TASK_ID = RUNTIME_TASK_ID
    base.ALLOWED_TASK_IDS = {TASK_ID, RUNTIME_TASK_ID}
    base.collect_hits = collect_distinct_entries


def main() -> int:
    configure_runner()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
