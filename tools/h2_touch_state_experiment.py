#!/usr/bin/env python3
"""Differentially compare UiTouch_GetRegionTouchState to bounded C++ candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ADDRESS = 0x0029D8FC
GLOBAL_PTR = 0x0043DCB4
CODE_BASE = 0x00100000
CODE_MAP_SIZE = 0x00378000
MANAGER = 0x00500000
MANAGER_SIZE = 0x1000
STACK = 0x08000000
STACK_SIZE = 0x8000
SP = STACK + STACK_SIZE // 2
INJECT = 0x01000000
INJECT_SIZE = 0x1000
RETURN = INJECT + INJECT_SIZE - 4
SOURCE = ROOT / "experiments/semantic_equivalence/h2_touch_state_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
SYMBOL = "candidate_0029d8fc"
BAD_SYMBOL = "candidate_0029d8fc_bad"
ACTIVE_VALUES = (-32768, -1, 0, 1, 9, 10, 11, 12, 32767)
STATE_VALUES = (0, 1, 2, 6, 255)
CALLEE_SAVED = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_symbols(output: Path) -> tuple[dict[str, bytes], Path, list[str]]:
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "h2_touch_state_candidate.o"
    build = compile_tu_armv6k(SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    extracted = extract_elf_functions_detailed(obj)
    result = {}
    for symbol in (SYMBOL, BAD_SYMBOL):
        if symbol not in extracted:
            raise ValueError(f"candidate object lacks {symbol}")
        code, relocations = extracted[symbol]
        if relocations:
            raise ValueError(f"candidate {symbol} has unsupported relocations: {relocations}")
        result[symbol] = code
    return result, obj, list(build.args)


def machine(image: bytes, candidate: bytes | None = None) -> tuple[unicorn.Uc, list[dict]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_MAP_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(MANAGER, MANAGER_SIZE)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(INJECT, INJECT_SIZE)
    if candidate is not None:
        if len(candidate) > INJECT_SIZE - 4:
            raise ValueError("candidate function exceeds injection page")
        uc.mem_write(INJECT, candidate)
    uc.mem_write(RETURN, b"\x00\x00\xA0\xE1")
    uc.mem_write(GLOBAL_PTR, struct.pack("<I", MANAGER))
    write_events: list[dict] = []

    def on_write(_uc, access, address, size, value, _user):
        write_events.append({"address": hex(address), "size": size, "value": value})

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    return uc, write_events


def invoke(uc: unicorn.Uc, entry: int, handle: int, active: int, state: int) -> dict:
    uc.mem_write(MANAGER + 0x08, bytes([state & 0xFF]))
    uc.mem_write(MANAGER + 0x64E, struct.pack("<h", active))
    # H2 callers use LDRSH before BL, so negative s16 handles arrive sign-extended.
    uc.reg_write(arm.UC_ARM_REG_R0, handle & 0xFFFFFFFF)
    for index, (_, reg) in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0x55000000 | (index + 1))
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    fault = None
    try:
        uc.emu_start(entry, RETURN + 4, count=64)
    except unicorn.UcError as error:
        fault = str(error)
    return {
        "fault": fault,
        "return": uc.reg_read(arm.UC_ARM_REG_R0),
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "preserved": {name: uc.reg_read(reg) == (0x55000000 | (index + 1))
                      for index, (name, reg) in enumerate(CALLEE_SAVED)},
    }


def expected(handle: int, active: int, state: int) -> int:
    return state if handle == active else 0


def compare(first: dict, second: dict) -> str | None:
    for key in ("fault", "return", "pc", "sp", "preserved"):
        if first[key] != second[key]:
            return f"{key} differs"
    return None


def run(output: Path, code_path: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    code, obj, compiler_args = compile_symbols(output)
    original, original_writes = machine(image)
    candidate, candidate_writes = machine(image, code[SYMBOL])
    negative, negative_writes = machine(image, code[BAD_SYMBOL])
    cases = 0
    mismatch = None
    state_counts = {str(s): 0 for s in STATE_VALUES}
    start = time.time()
    for active in ACTIVE_VALUES:
        for signed_handle in range(-32768, 32768):
            handle = signed_handle
            state = STATE_VALUES[(signed_handle + 32768) % len(STATE_VALUES)]
            ref = invoke(original, ADDRESS, handle, active, state)
            got = invoke(candidate, INJECT, handle, active, state)
            state_counts[str(state)] += 1
            cases += 1
            if ref["fault"] or got["fault"]:
                mismatch = {"case": cases, "active": active, "handle": signed_handle,
                            "state": state, "original": ref, "candidate": got,
                            "reason": "fault"}
                break
            if not all(ref["preserved"].values()) or not all(got["preserved"].values()):
                mismatch = {"case": cases, "active": active, "handle": signed_handle,
                            "state": state, "original": ref, "candidate": got,
                            "reason": "callee-saved register or SP contract violated"}
                break
            if got["return"] != expected(signed_handle, active, state):
                mismatch = {"case": cases, "active": active, "handle": signed_handle,
                            "state": state, "original": ref, "candidate": got,
                            "reason": "pinned behavior disagrees with recovered contract"}
                break
            reason = compare(ref, got)
            if reason:
                mismatch = {"case": cases, "active": active, "handle": signed_handle,
                            "state": state, "original": ref, "candidate": got,
                            "reason": reason}
                break
        if mismatch:
            break

    # Ensure every sampled raw byte is also exercised on the equality path.
    directed_match_cases = []
    if mismatch is None:
        for active in ACTIVE_VALUES:
            for state in STATE_VALUES:
                ref = invoke(original, ADDRESS, active, active, state)
                got = invoke(candidate, INJECT, active, active, state)
                reason = compare(ref, got)
                expected_value = expected(active, active, state)
                if (reason is None and (ref["return"] != expected_value or
                                        not all(ref["preserved"].values()) or
                                        not all(got["preserved"].values()))):
                    reason = "directed matching-handle contract failed"
                directed_match_cases.append({"active": active, "handle": active,
                                             "state": state, "return": got["return"],
                                             "match": reason is None})
                if reason and mismatch is None:
                    mismatch = {"active": active, "handle": active, "state": state,
                                "reason": reason, "original": ref, "candidate": got}

    # Sensitivity check: wrong candidate ignores the active index and must drift.
    active, handle, state = 10, 11, 6
    neg_ref = invoke(original, ADDRESS, handle & 0xFFFF, active, state)
    neg_bad = invoke(negative, INJECT, handle & 0xFFFF, active, state)
    negative_control_detected = compare(neg_ref, neg_bad) is not None
    if not negative_control_detected and mismatch is None:
        mismatch = {"reason": "wrong-index negative control escaped", "original": neg_ref,
                    "mutant": neg_bad}
    if (original_writes or candidate_writes) and mismatch is None:
        mismatch = {"reason": "read-only getter wrote guest memory",
                    "original_writes": original_writes,
                    "candidate_writes": candidate_writes}

    report = {
        "schema": 1,
        "status": "passed" if mismatch is None else "failed",
        "scope": "initialized IfTouch manager; signed s16 handle; read-only getter",
        "reference": {"address": hex(ADDRESS), "code_sha256": sha256(image)},
        "candidate": {"source": str(SOURCE), "source_sha256": sha256(SOURCE.read_bytes()),
                      "object": str(obj), "object_sha256": sha256(obj.read_bytes()),
                      "function_size": len(code[SYMBOL]), "negative_function_size": len(code[BAD_SYMBOL]),
                      "compiler_args": compiler_args},
        "coverage": {"cases": cases, "active_indices": list(ACTIVE_VALUES),
                     "handle_domain_per_active": "all 65,536 signed-16 bit patterns",
                     "state_values": STATE_VALUES, "state_case_counts": state_counts,
                     "directed_matching_handle_cases": len(directed_match_cases),
                     "directed_matching_handle_results": directed_match_cases},
        "abi_and_effects": {"callee_saved_registers_preserved": not original_writes and not candidate_writes,
                             "original_guest_writes": original_writes,
                             "candidate_guest_writes": candidate_writes,
                             "sp_return_pc_and_faults_compared": True},
        "negative_control": {"detected": negative_control_detected, "active": active,
                             "handle": handle, "state": state,
                             "original_return": neg_ref["return"], "mutant_return": neg_bad["return"]},
        "elapsed_seconds": round(time.time() - start, 3),
        "first_mismatch": mismatch,
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["report_sha256"] = sha256(report_path.read_bytes())
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    args = parser.parse_args()
    report = run(args.output, args.code)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
