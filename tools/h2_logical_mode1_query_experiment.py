#!/usr/bin/env python3
"""Differentially compare the H2 logical mode-1 query helper to typed C++."""
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

ADDRESS = 0x002BFFBC
FLAG = 0x004650A8
COUNTERS = 0x004E3C58
COUNTER_PAGE = 0x004E3000
CODE_BASE = 0x00100000
CODE_MAP_SIZE = 0x00378000
STACK = 0x08000000
STACK_SIZE = 0x8000
SP = STACK + STACK_SIZE // 2
INJECT = 0x01000000
INJECT_SIZE = 0x1000
RETURN = INJECT + INJECT_SIZE - 4
SOURCE = ROOT / "experiments/semantic_equivalence/h2_logical_mode1_query_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
SYMBOLS = {
    "good": "candidate_002bffbc",
    "bad_flag": "candidate_002bffbc_bad_flag",
    "bad_counter": "candidate_002bffbc_bad_counter",
    "bad_bound": "candidate_002bffbc_bad_bound",
}
VALID_IDS = tuple(range(31))
COUNTER_VALUES = (0, 1, 2, 0xFFFFFFFF)
FLAG_VALUES = (0, 1, 2, 3)
INVALID_IDS = (31, 32, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)
CALLEE_SAVED = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_symbols(output: Path) -> tuple[dict[str, bytes], Path, list[str]]:
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "h2_logical_mode1_query_candidate.o"
    build = compile_tu_armv6k(SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    extracted = extract_elf_functions_detailed(obj)
    result = {}
    for key, symbol in SYMBOLS.items():
        if symbol not in extracted:
            raise ValueError(f"candidate object lacks {symbol}")
        body, relocations = extracted[symbol]
        if relocations:
            raise ValueError(f"candidate {symbol} has unsupported relocations: {relocations}")
        result[key] = body
    return result, obj, list(build.args)


def machine(image: bytes, candidate: bytes | None = None) -> tuple[unicorn.Uc, list[dict]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_MAP_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(COUNTER_PAGE, 0x1000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(INJECT, INJECT_SIZE)
    if candidate is not None:
        if len(candidate) > INJECT_SIZE - 4:
            raise ValueError("candidate function exceeds injection page")
        uc.mem_write(INJECT, candidate)
    uc.mem_write(RETURN, b"\x00\x00\xA0\xE1")
    write_events: list[dict] = []

    def on_write(_uc, _access, address, size, value, _user):
        write_events.append({"address": hex(address), "size": size, "value": value})

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    return uc, write_events


def seed_counters(uc: unicorn.Uc, selected_id: int, selected_value: int, seed: int,
                  next_value: int | None = None,
                  boundary_value: int = 0xC0DEC0DE) -> None:
    words = [((seed * 0x10203 + index * 17) ^ 0xA5A50000) & 0xFFFFFFFF
             for index in range(31)]
    if 0 <= selected_id < 31:
        words[selected_id] = selected_value
        if next_value is not None and selected_id + 1 < 31:
            words[selected_id + 1] = next_value
    words.append(boundary_value & 0xFFFFFFFF)
    uc.mem_write(COUNTERS, b"".join(struct.pack("<I", value) for value in words))


def invoke(uc: unicorn.Uc, entry: int, query_id: int, flags: int,
           selected_counter: int = 0, seed: int = 1,
           next_counter: int | None = None,
           boundary_counter: int = 0xC0DEC0DE) -> dict:
    uc.mem_write(FLAG, struct.pack("<I", flags & 0xFFFFFFFF))
    seed_counters(uc, query_id, selected_counter, seed, next_counter,
                  boundary_counter)
    uc.reg_write(arm.UC_ARM_REG_R0, query_id & 0xFFFFFFFF)
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


def compare(first: dict, second: dict) -> str | None:
    for key in ("fault", "return", "pc", "sp", "preserved"):
        if first[key] != second[key]:
            return f"{key} differs"
    return None


def expected(query_id: int, flags: int, counter: int) -> int:
    return int(query_id < 31 and (flags & 1) == 0 and counter == 1)


def run(output: Path, code_path: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    code, obj, compiler_args = compile_symbols(output)
    original, original_writes = machine(image)
    candidate, candidate_writes = machine(image, code["good"])
    bad_flag, bad_flag_writes = machine(image, code["bad_flag"])
    bad_counter, bad_counter_writes = machine(image, code["bad_counter"])
    bad_bound, bad_bound_writes = machine(image, code["bad_bound"])
    cases = 0
    mismatch = None
    start = time.time()

    for query_id in VALID_IDS:
        for flags in FLAG_VALUES:
            for counter in COUNTER_VALUES:
                seed = 1 + (query_id * 13 + flags * 7 + counter) % 0x7FFFFFFE
                ref = invoke(original, ADDRESS, query_id, flags, counter, seed)
                got = invoke(candidate, INJECT, query_id, flags, counter, seed)
                cases += 1
                if ref["fault"] or got["fault"]:
                    mismatch = {"id": query_id, "flags": flags, "counter": counter,
                                "original": ref, "candidate": got, "reason": "fault"}
                elif (got["return"] != expected(query_id, flags, counter)):
                    mismatch = {"id": query_id, "flags": flags, "counter": counter,
                                "original": ref, "candidate": got,
                                "reason": "recovered contract mismatch"}
                else:
                    reason = compare(ref, got)
                    if reason:
                        mismatch = {"id": query_id, "flags": flags, "counter": counter,
                                    "original": ref, "candidate": got, "reason": reason}
                if mismatch:
                    break
            if mismatch:
                break
        if mismatch:
            break

    invalid_results = []
    if mismatch is None:
        for query_id in INVALID_IDS:
            for flags in (0, 1):
                ref = invoke(original, ADDRESS, query_id, flags, 1, 3)
                got = invoke(candidate, INJECT, query_id, flags, 1, 3,
                             boundary_counter=1 if query_id == 31 else 0xC0DEC0DE)
                cases += 1
                reason = compare(ref, got)
                invalid_results.append({"id": query_id, "flags": flags,
                                        "return": got["return"], "match": reason is None})
                if reason or got["return"] != 0:
                    mismatch = {"id": query_id, "flags": flags, "reason": reason or
                                "out-of-range ID must return zero", "original": ref,
                                "candidate": got}
                    break
            if mismatch:
                break

    # Each control has a directed case that makes the wrong behavior observable.
    neg_id = 7
    neg_ref_flag = invoke(original, ADDRESS, neg_id, 1, 1, 5)
    neg_bad_flag = invoke(bad_flag, INJECT, neg_id, 1, 1, 5)
    bad_flag_detected = compare(neg_ref_flag, neg_bad_flag) is not None
    neg_ref_counter = invoke(original, ADDRESS, neg_id, 0, 0, 7)
    neg_bad_counter = invoke(bad_counter, INJECT, neg_id, 0, 0, 7, next_counter=1)
    bad_counter_detected = compare(neg_ref_counter, neg_bad_counter) is not None
    neg_ref_bound = invoke(original, ADDRESS, 31, 0, 0, 11, boundary_counter=1)
    neg_bad_bound = invoke(bad_bound, INJECT, 31, 0, 0, 11, boundary_counter=1)
    bad_bound_detected = compare(neg_ref_bound, neg_bad_bound) is not None
    if mismatch is None and not bad_flag_detected:
        mismatch = {"reason": "wrong-flag-bit negative control escaped"}
    if mismatch is None and not bad_counter_detected:
        mismatch = {"reason": "wrong-counter-index negative control escaped"}
    if mismatch is None and not bad_bound_detected:
        mismatch = {"reason": "off-by-one ID-bound negative control escaped"}
    all_writes = {"original": original_writes, "candidate": candidate_writes,
                  "bad_flag": bad_flag_writes, "bad_counter": bad_counter_writes,
                  "bad_bound": bad_bound_writes}
    if mismatch is None and any(all_writes.values()):
        mismatch = {"reason": "read-only query wrote guest memory", "writes": all_writes}

    report = {
        "schema": 1,
        "status": "passed" if mismatch is None else "failed",
        "scope": "H2 logical mode-1 query; valid unsigned IDs 0..30 and selected invalid IDs",
        "reference": {"address": hex(ADDRESS), "code_sha256": sha256(image)},
        "candidate": {"source": str(SOURCE), "source_sha256": sha256(SOURCE.read_bytes()),
                      "object": str(obj), "object_sha256": sha256(obj.read_bytes()),
                      "function_sizes": {k: len(v) for k, v in code.items()},
                      "compiler_args": compiler_args},
        "coverage": {"valid_id_count": len(VALID_IDS), "valid_ids": [VALID_IDS[0], VALID_IDS[-1]],
                     "flag_values": FLAG_VALUES, "counter_values": COUNTER_VALUES,
                     "valid_matrix_cases": len(VALID_IDS) * len(FLAG_VALUES) * len(COUNTER_VALUES),
                     "invalid_id_results": invalid_results, "total_calls": cases},
        "abi_and_effects": {"callee_saved_registers": [name for name, _ in CALLEE_SAVED],
                             "original_guest_writes": original_writes,
                             "candidate_guest_writes": candidate_writes,
                             "sp_pc_fault_and_return_compared": True},
        "negative_controls": {
            "wrong_flag_bit": {"detected": bad_flag_detected, "flags": 1,
                                "original_return": neg_ref_flag["return"],
                                "mutant_return": neg_bad_flag["return"]},
            "wrong_counter_index": {"detected": bad_counter_detected, "id": neg_id,
                                    "original_return": neg_ref_counter["return"],
                                    "mutant_return": neg_bad_counter["return"]},
            "off_by_one_id_bound": {"detected": bad_bound_detected, "id": 31,
                                    "adjacent_counter": 1,
                                    "original_return": neg_ref_bound["return"],
                                    "mutant_return": neg_bad_bound["return"]}},
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
