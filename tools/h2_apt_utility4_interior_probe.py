#!/usr/bin/env python3
"""Bounded APT Utility-4 probe at its separately entered ARM command-4 block.

The reused runner inserts and removes a Z0 software breakpoint, which modifies
guest instructions transiently. It does not send M/P/X packets or logical input.
LR observations are consistent with callsites, not proof of a tail branch origin.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

try:
    import h2_apt_utility4_caller_probe as base
except ModuleNotFoundError:
    from tools import h2_apt_utility4_caller_probe as base

ENTRY = 0x002C0EFC
DIRECT_BL = (0x002C0F6C, 0x002C1260, 0x002C1304)
TAIL_B = (0x00106F00, 0x0010700C, 0x002A8164, 0x002C5638)
EE0_BL = (0x00102184, 0x001051DC)
TASK_ID = "h2-apt-utility4-interior-probe"
RUNTIME_TASK_ID = "h2-apt-utility4-interior-probe-runtime"


def direct_tail_branches(raw: bytes) -> list[int]:
    result = []
    for offset in range(0, len(raw) - 3, 4):
        pc = base.CODE_BASE + offset
        word = int.from_bytes(raw[offset:offset + 4], "little")
        if word >> 28 == 0xF or word & 0x0F000000 != 0x0A000000:
            continue
        displacement = word & 0x00FFFFFF
        if displacement & 0x00800000:
            displacement -= 1 << 24
        if (pc + 8 + (displacement << 2)) & 0xFFFFFFFF == ENTRY:
            result.append(pc)
    return result


def verify_interior_entry(raw: bytes) -> dict:
    if hashlib.sha256(raw).hexdigest() != base.CODE_SHA256:
        raise base.ProbeError("interior probe original code identity mismatch")
    if ENTRY & 3 or base.u32_at(raw, ENTRY) != 0xE3A01000:
        raise base.ProbeError("interior ARM entry instruction or alignment changed")
    bl = tuple(base.direct_arm_bl_callers(raw, ENTRY))
    tail = tuple(direct_tail_branches(raw))
    if bl != DIRECT_BL or tail != TAIL_B:
        raise base.ProbeError("interior entry direct branch inventory changed")
    return {"entry": f"0x{ENTRY:08x}", "direct_arm_bl": [f"0x{x:08x}" for x in bl],
            "direct_arm_tail_b": [f"0x{x:08x}" for x in tail],
            "limit": "direct aligned ARM branches only; indirect and Thumb routes remain unresolved"}


def classify_entry_lr(lr: int) -> dict:
    direct = {pc + 4: pc for pc in DIRECT_BL}
    earlier_entry = {pc + 4: pc for pc in EE0_BL}
    if lr in direct:
        label, callsite = "consistent_with_direct_bl", direct[lr]
    elif lr in earlier_entry:
        label, callsite = "consistent_with_ee0_fallthrough", earlier_entry[lr]
    else:
        label, callsite = "unresolved_possible_tail_or_indirect", None
    return {"lr": f"0x{lr:08x}", "classification": label,
            "caller_callsite": f"0x{callsite:08x}" if callsite is not None else None,
            "limit": "LR alone cannot prove the origin of a tail branch"}


def configure_runner() -> None:
    original_static_contract = base.static_contract
    base.BREAKPOINT = ENTRY
    base.EXPECTED_CALLER_ADDRESSES = DIRECT_BL
    base.CALLERS = {pc + 4: pc for pc in DIRECT_BL}
    base.classify_lr = classify_entry_lr
    base.TASK_ID = TASK_ID
    base.RUNTIME_TASK_ID = RUNTIME_TASK_ID
    base.ALLOWED_TASK_IDS = {TASK_ID, RUNTIME_TASK_ID}

    def checked_contract(code_path: Path, run017_log: Path, run028_log: Path) -> dict:
        result = original_static_contract(code_path, run017_log, run028_log)
        result["interior_entry"] = verify_interior_entry(code_path.read_bytes())
        return result

    base.static_contract = checked_contract


def main() -> int:
    configure_runner()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
