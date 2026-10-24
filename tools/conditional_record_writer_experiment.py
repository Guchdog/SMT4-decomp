#!/usr/bin/env python3
"""Differential-test two signed-conditional record writers in isolation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
import unicorn
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.build_check import find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
    validate_local_blob,
)
from tools.semantic_experiment_support import load_pinned_reference

FUNCTIONS = {
    0x0035B254: {"nonpositive_byte": 0x07, "positive_halfword": 0x002E,
                 "positive_return_flags": "CMP ip,#0; preserved through BX LR"},
    0x0035BF8C: {"nonpositive_byte": 0x11, "positive_halfword": 0x005E,
                 "positive_return_flags": "CMP ip,#0; preserved through BX LR"},
}
U32_MASK = 0xFFFFFFFF


def _instructions(image: bytes, address: int, size: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    decoded = list(decoder.disasm(image[offset:offset + size], address))
    return tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded), sum(
        item.size for item in decoded
    )


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    result = {}
    for address, values in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 64:
            raise ValueError(f"Missing matching 64-byte ledger row at {address:#010x}")
        constant_b = values["nonpositive_byte"]
        constant_h = values["positive_halfword"]
        fmt = lambda value: str(value) if value < 10 else f"0x{value:x}"
        expected = (
            ("ldr", "ip, [r0, #0x18]"), ("ldr", "r2, [r1]"),
            ("mov", "r3, #0"), ("cmp", "ip, #0"),
            ("movle", f"ip, #{fmt(constant_b)}"),
            ("strbgt", "r3, [r2, #8]"), ("strble", "ip, [r2, #8]"),
            ("ldr", "r1, [r1]"), ("movgt", f"ip, #0x{constant_h:x}"),
            ("strhgt", "ip, [r1, #0xa]"), ("strble", "r3, [r1, #0xa]"),
            ("ldr", "r1, [r0, #0x10]"), ("add", "r1, r1, #1"),
            ("str", "r1, [r0, #0x10]"), ("mov", "r0, #0"),
            ("bx", "lr"),
        )
        actual, size = _instructions(image, address, 64)
        if actual != expected or size != 64:
            raise ValueError(f"Original instruction sequence changed at {address:#010x}: expected={expected}; actual={actual}")
        result[hex(address)] = {
            "size": size,
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in actual],
            "function_sha256": hashlib.sha256(
                image[address - TEXT:address - TEXT + size]
            ).hexdigest(),
            "ledger_name": row["name"], "category": row["category"],
            "observed_contract": {
                "condition": "signed *(int32_t *)(r0+0x18) > 0",
                "handle_cell": "loads *(u32 *)r1 before first write and reloads it before second conditional write",
                "positive_writes": ["STRB 0 to first_target+8",
                                    f"STRH 0x{constant_h:x} to reloaded_target+0xA"],
                "nonpositive_writes": [f"STRB 0x{constant_b:x} to first_target+8",
                                        "STRB 0 to reloaded_target+0xA"],
                "counter": "u32 at r0+0x10 incremented modulo 2^32 after both record writes",
                "return": "r0=0",
                "nzcv": "CMP signed value against zero; MOV/STR/ADD-without-S preserve those flags through BX LR",
            },
        }
    return {"code_sha256": digest, "functions": result}


def _make_case(address: int, seed: int, label: str, condition: int,
               counter: int, target: int = DATA + 0x240,
               byte_after: int | None = None) -> Case:
    salt = sum((index + 1) * ord(char) for index, char in enumerate(label))
    rng = random.Random(seed ^ address ^ salt)
    data = bytearray(rng.randbytes(DATA_SIZE))
    record = DATA + 0x100
    handle_cell = DATA + 0x80
    struct.pack_into("<I", data, record - DATA + 0x18, condition & U32_MASK)
    struct.pack_into("<I", data, record - DATA + 0x10, counter & U32_MASK)
    struct.pack_into("<I", data, handle_cell - DATA, target & U32_MASK)
    if byte_after is not None and target + 0xB < DATA + DATA_SIZE:
        data[target - DATA + 0xB] = byte_after & 0xFF
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0], registers[1] = record, handle_cell
    return Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def make_cases(address: int, samples: int, seed: int):
    # Include signed-boundary values around zero and both signed extremes.
    boundaries = (
        (0, 0, "zero-counter-zero"),
        (1, 1, "positive-one-counter-one"),
        (2, U32_MASK - 1, "positive-two-counter-wrap"),
        (0x7FFFFFFF, 0x12345678, "positive-int-max"),
        (0x80000000, 0x87654321, "negative-int-min"),
        (0xFFFFFFFF, 0xFFFFFFFF, "negative-minus-one-wrap"),
        (0xFFFFFFFE, 7, "negative-minus-two"),
        (0x10203040, 0xFFFFFFFE, "positive-random-pattern"),
    )
    for condition, counter, label in boundaries:
        yield _make_case(address, seed, label, condition, counter,
                         byte_after=0xA5)
    rng = random.Random(seed ^ address)
    for index in range(samples):
        yield _make_case(address, seed + index, f"random-{index}",
                         rng.getrandbits(32), rng.getrandbits(32),
                         byte_after=rng.randrange(1, 256))


def _expected_cmp_nzcv(value: int) -> int:
    value &= U32_MASK
    # CMP x,#0 is SUBS x,0: N is x[31], Z reflects zero, C is always set,
    # and V is clear. The original routine has no later S-setting instruction.
    return (0x80000000 if value & 0x80000000 else 0) | (0x40000000 if value == 0 else 0) | 0x20000000


def _run_with_access_trace(runner: Runner, case: Case):
    events = []

    def record(_uc, access, address, size, _value, _user_data):
        if DATA <= address < DATA + DATA_SIZE:
            kind = "read" if access == unicorn.UC_MEM_READ else "write"
            events.append((kind, address, size))

    def record_invalid(_uc, access, address, size, _value, _user_data):
        events.append(("fault_write", address, size, access))
        return False

    hook = runner.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE,
                              record)
    invalid_hook = runner.uc.hook_add(unicorn.UC_HOOK_MEM_INVALID, record_invalid)
    try:
        result = runner.run(case)
    finally:
        runner.uc.hook_del(hook)
        runner.uc.hook_del(invalid_hook)
    return result, tuple(events)


def _compile_candidate_symbols(source_path: Path, object_path: Path) -> dict[str, bytes]:
    """Compile branch-bearing candidates and validate their local code blobs."""
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    extracted = extract_elf_functions_detailed(object_path)
    expected = {"candidate_0035b254", "candidate_0035bf8c", "negative_wide_zero_on_else"}
    compiled = {}
    for symbol, (code, relocations) in extracted.items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_local_blob(code)
        compiled[symbol] = code
    missing = expected - compiled.keys()
    if missing:
        raise ValueError(f"Missing required candidate symbols: {sorted(missing)}")
    return compiled


def _run_fault_case(image: bytes, compiled: dict, address: int, seed: int,
                    condition: int, label: str) -> dict:
    # +8 is the penultimate mapped byte; aligned +0xA begins at the unmapped
    # boundary. This checks the observable prefix store and that the later
    # fault prevents the counter increment without introducing misalignment.
    case = _make_case(address, seed, label, condition, 0xCAFEBABE,
                      target=DATA + DATA_SIZE - 10, byte_after=None)
    original, original_trace = _run_with_access_trace(Runner(image, address), case)
    rebuilt, rebuilt_trace = _run_with_access_trace(
        Runner(image, address, compiled[f"candidate_{address:08x}"],
               replacement_validator=validate_local_blob), case
    )
    first_value = (0 if condition > 0 else FUNCTIONS[address]["nonpositive_byte"])
    return {
        "label": label,
        "condition": f"0x{condition & U32_MASK:08x}",
        "both_faulted": bool(original.fault and rebuilt.fault),
        "original_fault": original.fault,
        "candidate_fault": rebuilt.fault,
        "same_faulting_access": original_trace[-1:] == rebuilt_trace[-1:],
        "same_partial_data": original.data == rebuilt.data,
        "same_write_footprint": original.writes == rebuilt.writes,
        "same_ordered_accesses": original_trace == rebuilt_trace,
        "ordered_accesses": [[event[0], hex(event[1]), event[2], *event[3:]]
                              for event in original_trace],
        "first_store_survived": original.data[DATA_SIZE - 2] == first_value
                                and rebuilt.data[DATA_SIZE - 2] == first_value,
        "counter_not_incremented": struct.unpack_from("<I", original.data,
            case.registers[0] - DATA + 0x10)[0] == 0xCAFEBABE
            and struct.unpack_from("<I", rebuilt.data,
                case.registers[0] - DATA + 0x10)[0] == 0xCAFEBABE,
    }


def run(code_path: Path, output: Path, samples: int = 128,
        seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    image, game_info, ledger = pinned.image, pinned.game_info, pinned.ledger
    reference = verify_reference(image, game_info, ledger)
    output.mkdir(parents=True, exist_ok=True)
    source_path = ROOT / "experiments/semantic_equivalence/conditional_record_writer_candidates.cpp"
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    compiled = _compile_candidate_symbols(
        source_path, output / "conditional_record_writer_candidates.o"
    )

    functions = []
    flag_checks = []
    for address in FUNCTIONS:
        symbol = f"candidate_{address:08x}"
        original, candidate = Runner(
            image, address), Runner(image, address, compiled[symbol],
                                   replacement_validator=validate_local_blob)
        count, failure = 0, None
        path_traces = {}
        for case in make_cases(address, samples, seed):
            expected_flags = _expected_cmp_nzcv(
                struct.unpack_from("<I", case.data,
                    case.registers[0] - DATA + 0x18)[0]
            )
            reference_result, reference_trace = _run_with_access_trace(original, case)
            if reference_result.nzcv != expected_flags:
                failure = {"case": case.label, "reason": "pinned output NZCV did not match CMP x,#0"}
                count += 1
                break
            rebuilt, candidate_trace = _run_with_access_trace(candidate, case)
            reason = difference(reference_result, rebuilt, returns_value=True,
                                compare_flags=False)
            if reference_trace != candidate_trace:
                reason = "ordered memory access trace differs"
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason,
                           "reference_nzcv": hex(reference_result.nzcv),
                           "candidate_nzcv": hex(rebuilt.nzcv)}
                break
            if case.label in ("zero-counter-zero", "positive-one-counter-one"):
                path_traces[case.label] = [[kind, hex(addr), size]
                                           for kind, addr, size in reference_trace]
            if case.label in ("zero-counter-zero", "positive-one-counter-one",
                              "positive-int-max", "negative-int-min",
                              "negative-minus-one-wrap"):
                flag_checks.append({"address": hex(address), "case": case.label,
                                    "expected_original_nzcv": hex(expected_flags),
                                    "observed_original_nzcv": hex(reference_result.nzcv),
                                    "candidate_nzcv_not_abi_constrained": hex(rebuilt.nzcv),
                                    "original_flags_passed": reference_result.nzcv == expected_flags})
        functions.append({"address": hex(address),
                          "nonpositive_byte": hex(FUNCTIONS[address]["nonpositive_byte"]),
                          "positive_halfword": hex(FUNCTIONS[address]["positive_halfword"]),
                          "original_bytes": 64,
                          "candidate_bytes": len(compiled[symbol]),
                          "cases": count, "passed": failure is None,
                          "ordered_access_traces": path_traces,
                          "failure": failure})

    # Force the else path's one-byte clear to distinguish it from an incorrect
    # halfword clear that would clobber the seeded byte at field +0xB.
    negative_case = _make_case(0x0035B254, seed, "negative-width-control",
                               0, 0x11112222, byte_after=0xA5)
    original_negative = Runner(image, 0x0035B254)
    wide_negative = Runner(image, 0x0035B254, compiled["negative_wide_zero_on_else"],
                           replacement_validator=validate_local_blob)
    negative_reason = difference(original_negative.run(negative_case),
                                wide_negative.run(negative_case), returns_value=True,
                                compare_flags=False)
    negative_controls = [{"name": "negative_wide_zero_on_else",
                          "detected": negative_reason is not None,
                          "reason": negative_reason,
                          "expected_reason": "data memory differs"}]

    fault_results = []
    for address in FUNCTIONS:
        for condition, label in ((1, "positive-store-prefix-then-halfword-fault"),
                                 (0, "nonpositive-store-prefix-then-byte-fault")):
            outcome = _run_fault_case(image, compiled, address, seed, condition,
                                      f"{address:08x}-{label}")
            outcome["address"] = hex(address)
            fault_results.append(outcome)

    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1,
        "experiment": "conditional_record_writers",
        "passed": (all(item["passed"] for item in functions)
                   and all(item["detected"] for item in negative_controls)
                   and all(item["both_faulted"] and item["same_faulting_access"]
                           and item["same_partial_data"] and item["same_write_footprint"]
                           and item["same_ordered_accesses"] and item["first_store_survived"]
                           and item["counter_not_incremented"] for item in fault_results)),
        "scope": "two isolated signed-conditional record writers; no caller windows",
        "reference": reference,
        "source_sha256": source_hash,
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_samples_per_function": samples,
        "function_comparisons": sum(item["cases"] for item in functions),
        "functions": functions,
        "flag_checks": flag_checks,
        "negative_controls": negative_controls,
        "partial_fault_cases": fault_results,
        "callers": {
            "verified": [],
            "note": "No callsite was manually verified in this experiment. Scaffold's BL scan found no ARM direct callers; Thumb/indirect references remain unsearched.",
        },
        "limitations": [
            "Only pinned static instruction evidence and bounded Unicorn differential execution on aligned ordinary RAM are included.",
            "MMIO semantics, concurrent mutation of the handle cell, and externally observable intermediate stores are not modeled.",
            "Partial-fault probes cover one valid prefix store followed by an unmapped second store; they do not characterize all bus/OS fault behavior.",
            "The register-level ABI is intentionally inferred only as r0=record and r1=handle-cell from direct LDR offsets; no verified caller establishes higher-level object meaning.",
            "The original leaves NZCV from CMP ip,#0; the C++ candidate need not reproduce that volatile condition state because AAPCS does not make NZCV caller-preserved across a call.",
            "No whole-game equivalence or emulator behavior is established.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = run(args.code, args.output, samples=args.samples, seed=args.seed)
    print(json.dumps({"passed": report["passed"],
                      "function_comparisons": report["function_comparisons"],
                      "negative_controls": report["negative_controls"],
                      "partial_fault_cases": report["partial_fault_cases"]}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
