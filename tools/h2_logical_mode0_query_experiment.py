#!/usr/bin/env python3
"""Differentially compare the H2 logical mode-0 query with typed C++."""
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

ADDRESS = 0x002B902C
DIVMOD = 0x002C6C10
FLAG = 0x004650A8
THRESHOLD = 0x004650AC
SELECTOR = 0x004650B0
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
SOURCE = ROOT / "experiments/semantic_equivalence/h2_logical_mode0_query_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
SYMBOLS = {
    "good": "candidate_002b902c",
    "bad_counter": "candidate_002b902c_bad_counter",
    "bad_threshold": "candidate_002b902c_bad_threshold",
    "bad_selector": "candidate_002b902c_bad_selector",
}
VALID_IDS = tuple(range(31))
INVALID_IDS = (31, 32, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)
FLAGS_VALUES = (0, 1, 2, 3)
THRESHOLDS = (0, 7, 31, 64)
SELECTORS = (1, 2, 3, 7)
COUNTER_VALUES = tuple(range(66)) + (127, 255, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)
CALLEE_SAVED = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_symbols(output: Path) -> tuple[dict[str, bytes], Path, list[str]]:
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "h2_logical_mode0_query_candidate.o"
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


def machine(image: bytes, candidate: bytes | None = None) -> tuple[unicorn.Uc, list[dict], list[tuple[int, int]]]:
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
    writes: list[dict] = []
    helper_calls: list[tuple[int, int]] = []

    def on_write(_uc, _access, address, size, value, _user):
        writes.append({"address": hex(address), "size": size, "value": value,
                       "stack": STACK <= address < STACK + STACK_SIZE})

    def on_helper(_uc, _address, _size, _user):
        helper_calls.append((_uc.reg_read(arm.UC_ARM_REG_R0),
                             _uc.reg_read(arm.UC_ARM_REG_R1)))

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_helper, begin=DIVMOD, end=DIVMOD)
    return uc, writes, helper_calls


def seed_counters(uc: unicorn.Uc, query_id: int, value: int, seed: int,
                  adjacent_value: int = 0xD00DFEED) -> None:
    words = [((seed * 0x10203 + index * 17) ^ 0x5A5A0000) & 0xFFFFFFFF
             for index in range(32)]
    if 0 <= query_id < 31:
        words[query_id] = value & 0xFFFFFFFF
        if adjacent_value is not None and query_id + 1 < 32:
            words[query_id + 1] = adjacent_value & 0xFFFFFFFF
    uc.mem_write(COUNTERS, b"".join(struct.pack("<I", item) for item in words))


def invoke(uc: unicorn.Uc, entry: int, query_id: int, flags: int, counter: int,
           threshold: int, selector: int, seed: int = 1,
           adjacent_value: int = 0xD00DFEED) -> dict:
    uc.mem_write(FLAG, struct.pack("<I", flags & 0xFFFFFFFF))
    uc.mem_write(THRESHOLD, struct.pack("<I", threshold & 0xFFFFFFFF))
    uc.mem_write(SELECTOR, struct.pack("<I", selector & 0xFFFFFFFF))
    seed_counters(uc, query_id, counter, seed, adjacent_value)
    uc.reg_write(arm.UC_ARM_REG_R0, query_id & 0xFFFFFFFF)
    for index, (_, reg) in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0x66000000 | (index + 1))
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    for reg in (arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3):
        uc.reg_write(reg, 0x77000000 | (reg & 0xFFFF))
    fault = None
    try:
        uc.emu_start(entry, RETURN + 4, count=2048)
    except unicorn.UcError as error:
        fault = str(error)
    return {
        "fault": fault,
        "return": uc.reg_read(arm.UC_ARM_REG_R0),
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "preserved": {name: uc.reg_read(reg) == (0x66000000 | (index + 1))
                      for index, (name, reg) in enumerate(CALLEE_SAVED)},
        "division_helper_calls": 0,
    }


def invoke_recorded(uc: unicorn.Uc, entry: int, query_id: int, flags: int,
                    counter: int, threshold: int, selector: int, seed: int = 1,
                    adjacent_value: int = 0xD00DFEED,
                    helper_calls: list[tuple[int, int]] | None = None) -> dict:
    start_calls = len(helper_calls) if helper_calls is not None else 0
    result = invoke(uc, entry, query_id, flags, counter, threshold, selector,
                    seed, adjacent_value)
    if helper_calls is not None:
        result["division_helper_trace"] = helper_calls[start_calls:]
        result["division_helper_calls"] = len(result["division_helper_trace"])
    return result


def compare(first: dict, second: dict) -> str | None:
    for key in ("fault", "return", "pc", "sp", "preserved",
                "division_helper_calls", "division_helper_trace"):
        if first[key] != second[key]:
            return f"{key} differs"
    return None


def expected(query_id: int, flags: int, counter: int, threshold: int, selector: int) -> int:
    if query_id >= 31 or (flags & 1) != 0:
        return 0
    if counter == 1:
        return 1
    if counter <= threshold:
        return 0
    if selector == 0:
        raise ValueError("zero selector is outside the tested initialized profile")
    return int((counter - threshold) % selector == 0)


def helper_calls_expected(query_id: int, flags: int, counter: int, threshold: int) -> bool:
    return query_id < 31 and (flags & 1) == 0 and counter != 1 and counter > threshold


def helper_arguments_expected(query_id: int, flags: int, counter: int,
                              threshold: int, selector: int) -> list[tuple[int, int]]:
    if helper_calls_expected(query_id, flags, counter, threshold):
        return [(counter - threshold, selector)]
    return []


def run(output: Path, code_path: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    code, obj, compiler_args = compile_symbols(output)
    original, original_writes, original_calls = machine(image)
    candidate, candidate_writes, candidate_calls = machine(image, code["good"])
    mutants = {}
    for name in ("bad_counter", "bad_threshold", "bad_selector"):
        mutants[name] = machine(image, code[name])
    cases = 0
    mismatch = None
    helper_calls_seen = 0
    original_trace_hash = hashlib.sha256()
    candidate_trace_hash = hashlib.sha256()
    start = time.time()

    for query_id in VALID_IDS:
        for flags in FLAGS_VALUES:
            for threshold in THRESHOLDS:
                for selector in SELECTORS:
                    for counter in COUNTER_VALUES:
                        seed = 1 + ((query_id * 101 + flags * 23 + threshold * 7 +
                                     selector * 3 + counter) % 0x7FFFFFFE)
                        ref = invoke_recorded(original, ADDRESS, query_id, flags,
                                              counter, threshold, selector, seed,
                                              helper_calls=original_calls)
                        got = invoke_recorded(candidate, INJECT, query_id, flags,
                                              counter, threshold, selector, seed,
                                              helper_calls=candidate_calls)
                        cases += 1
                        helper_calls_seen += ref["division_helper_calls"]
                        for args in ref["division_helper_trace"]:
                            original_trace_hash.update(struct.pack("<II", *args))
                        for args in got["division_helper_trace"]:
                            candidate_trace_hash.update(struct.pack("<II", *args))
                        if ref["fault"] or got["fault"]:
                            mismatch = {"id": query_id, "flags": flags, "counter": counter,
                                        "threshold": threshold, "selector": selector,
                                        "original": ref, "candidate": got, "reason": "fault"}
                        else:
                            reason = compare(ref, got)
                            expected_return = expected(query_id, flags, counter,
                                                       threshold, selector)
                            expected_service = int(helper_calls_expected(
                                query_id, flags, counter, threshold))
                            if reason is None and got["return"] != expected_return:
                                reason = "recovered contract mismatch"
                            if reason is None and got["division_helper_calls"] != expected_service:
                                reason = "division fallback call-path mismatch"
                            if reason is None and got["division_helper_trace"] != helper_arguments_expected(
                                    query_id, flags, counter, threshold, selector):
                                reason = "division fallback argument mismatch"
                            if reason:
                                mismatch = {"id": query_id, "flags": flags, "counter": counter,
                                            "threshold": threshold, "selector": selector,
                                            "original": ref, "candidate": got, "reason": reason}
                        if mismatch:
                            break
                    if mismatch: break
                if mismatch: break
            if mismatch: break
        if mismatch: break

    invalid_cases = 0
    if mismatch is None:
        for query_id in INVALID_IDS:
            for flags in FLAGS_VALUES:
                ref = invoke_recorded(original, ADDRESS, query_id, flags, 1, 7, 2,
                                      seed=19, helper_calls=original_calls)
                got = invoke_recorded(candidate, INJECT, query_id, flags, 1, 7, 2,
                                      seed=19, helper_calls=candidate_calls)
                invalid_cases += 1
                cases += 1
                for args in ref["division_helper_trace"]:
                    original_trace_hash.update(struct.pack("<II", *args))
                for args in got["division_helper_trace"]:
                    candidate_trace_hash.update(struct.pack("<II", *args))
                reason = compare(ref, got)
                if reason or got["return"] != 0:
                    mismatch = {"id": query_id, "flags": flags,
                                "reason": reason or "invalid ID must return zero",
                                "original": ref, "candidate": got}
                    break
            if mismatch: break

    # Each mutation has one case where its changed input matters.
    directed = {
        "bad_counter": (4, 0, 0, 7, 2, 31, 1),
        "bad_threshold": (4, 0, 10, 7, 2, 37, 0xD00DFEED),
        "bad_selector": (4, 0, 9, 7, 2, 41, 0xD00DFEED),
    }
    negative_results = {}
    for name, (query_id, flags, counter, threshold, selector, seed, adjacent) in directed.items():
        ref = invoke_recorded(original, ADDRESS, query_id, flags, counter, threshold,
                              selector, seed, adjacent, original_calls)
        uc, _writes, calls = mutants[name]
        got = invoke_recorded(uc, INJECT, query_id, flags, counter, threshold,
                              selector, seed, adjacent, calls)
        detected = compare(ref, got) is not None
        negative_results[name] = {"detected": detected, "original_return": ref["return"],
                                  "mutant_return": got["return"], "original": ref,
                                  "mutant": got}
        if not detected and mismatch is None:
            mismatch = {"reason": f"{name} negative control escaped", "case": directed[name]}

    non_stack_writes = {
        "original": [event for event in original_writes if not event["stack"]],
        "candidate": [event for event in candidate_writes if not event["stack"]],
    }
    stack_writes_below_sp = all(
        int(event["address"], 16) + event["size"] <= SP
        for events in (original_writes, candidate_writes)
        for event in events if event["stack"])
    if mismatch is None and any(non_stack_writes.values()):
        mismatch = {"reason": "query path wrote guest data", "writes": non_stack_writes}
    if mismatch is None and any(not item["detected"] for item in negative_results.values()):
        mismatch = {"reason": "negative control escaped", "controls": negative_results}

    report = {
        "schema": 1,
        "status": "passed" if mismatch is None else "failed",
        "scope": "logical mode-0 query for valid unsigned IDs, initialized nonzero divisor profiles and bounded counter sweep",
        "reference": {"address": hex(ADDRESS), "code_sha256": sha256(image),
                      "retained_service": hex(DIVMOD)},
        "candidate": {"source": str(SOURCE), "source_sha256": sha256(SOURCE.read_bytes()),
                      "object": str(obj), "object_sha256": sha256(obj.read_bytes()),
                      "function_sizes": {key: len(body) for key, body in code.items()},
                      "compiler_args": compiler_args},
        "coverage": {"valid_ids": [VALID_IDS[0], VALID_IDS[-1], len(VALID_IDS)],
                     "flags": FLAGS_VALUES, "thresholds": THRESHOLDS,
                     "selectors_nonzero": SELECTORS,
                     "counter_value_count": len(COUNTER_VALUES),
                     "counter_values": [COUNTER_VALUES[0], COUNTER_VALUES[65], *COUNTER_VALUES[66:]],
                     "valid_cases": len(VALID_IDS) * len(FLAGS_VALUES) * len(THRESHOLDS) *
                                    len(SELECTORS) * len(COUNTER_VALUES),
                     "invalid_ids": INVALID_IDS, "invalid_cases": invalid_cases,
                     "total_cases": cases,
                     "division_fallback_entries": helper_calls_seen,
                     "division_fallback_compared": True,
                     "division_argument_trace": {
                         "original_sha256": original_trace_hash.hexdigest(),
                         "candidate_sha256": candidate_trace_hash.hexdigest(),
                         "hashes_match": original_trace_hash.digest() == candidate_trace_hash.digest(),
                         "entry_count": helper_calls_seen}},
        "effects": {"original_data_writes": non_stack_writes["original"],
                    "candidate_data_writes": non_stack_writes["candidate"],
                    "stack_write_counts": {"original": sum(x["stack"] for x in original_writes),
                                           "candidate": sum(x["stack"] for x in candidate_writes)},
                    "stack_writes_stay_below_entry_sp": stack_writes_below_sp,
                    "sp_pc_return_fault_and_r4_r11_compared": True},
        "negative_controls": negative_results,
        "limitations": ["Selector zero is excluded: the pinned divide service takes its divide-by-zero error path.",
                        "The candidate deliberately calls the original 0x002c6c10 quotient/remainder service; this service is not reconstructed by this task.",
                        "Stack scratch writes below entry SP may differ; SP restoration and callee-saved registers are compared.",
                        "The matrix covers counters through 65 plus directed high values, but does not prove producer scheduling, physical input mapping or H2 runtime behavior."],
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
