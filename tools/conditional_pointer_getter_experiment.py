#!/usr/bin/env python3
"""Differential-test conditional pointer-like word getters at two pinned sites."""
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
from tools.build_check import find_clang
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

FUNCTIONS = {
    0x00240EA4: {"flag_offset": 0x62, "pointer_offset": 0x48,
                 "callers": (0x0023062C, 0x00230C14, 0x002337F4, 0x00332414,
                             0x00332790, 0x0039793C, 0x00397950, 0x00397974,
                             0x00397C0C, 0x00397C40, 0x00397C6C, 0x00399298,
                             0x00399318, 0x00399388, 0x003993DC, 0x00399428,
                             0x003C2E40, 0x003C2F28)},
    0x0029E3BC: {"flag_offset": 0x62, "pointer_offset": 0x20,
                 "callers": (0x00182314, 0x001B0280, 0x001B02A4, 0x001CA66C,
                             0x001CAB80, 0x001CABC8, 0x001CAD6C, 0x001CADD4,
                             0x001CB1D4, 0x001CB23C, 0x002305FC, 0x00230BBC,
                             0x002337D0, 0x00329BE4, 0x00397BF4, 0x00397C4C,
                             0x00397C78, 0x003992A4, 0x00399324, 0x00399394,
                             0x003993A0, 0x003993E8, 0x0039943C, 0x003C2DCC,
                             0x003C2EC4)},
}

# Manually inspected in the pinned ARM image: the immediately preceding ADD
# computes the same object base from r4; both BLs return a word that the caller
# stores in separate r4-relative result slots before returning.
CALLER_WINDOW = {
    "start": 0x00397C3C,
    "stop": 0x00397C54,
    "calls": ((0x00397C40, 0x00240EA4), (0x00397C4C, 0x0029E3BC)),
    "description": "add r0,r4,#0x580; BL getter; store result; repeat for second getter; store; pop",
}
U32_MASK = 0xFFFFFFFF


def _instructions(image: bytes, address: int, size: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    offset = address - TEXT
    decoded = list(decoder.disasm(image[offset:offset + size], address))
    return tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded), sum(
        item.size for item in decoded
    )


def _direct_callers(image: bytes, targets: set[int]) -> dict[int, tuple[int, ...]]:
    found = {address: [] for address in targets}
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if (word & 0x0F000000) != 0x0B000000 or (word >> 28) == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        site = TEXT + index * 4
        target = (site + 8 + displacement) & U32_MASK
        if target in found:
            found[target].append(site)
    return {address: tuple(sites) for address, sites in found.items()}


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    functions = {}
    for address, details in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 20:
            raise ValueError(f"Missing matching 20-byte ledger row at {address:#010x}")
        pointer_offset = details["pointer_offset"]
        expected = (
            ("ldrb", "r1, [r0, #0x62]"),
            ("cmp", "r1, #0"),
            ("ldreq", f"r0, [r0, #0x{pointer_offset:x}]"),
            ("movne", "r0, #0"),
            ("bx", "lr"),
        )
        actual, size = _instructions(image, address, 20)
        if actual != expected or size != 20:
            raise ValueError(f"Original instruction sequence changed at {address:#010x}: {actual}")
        functions[hex(address)] = {
            "flag_offset": hex(details["flag_offset"]),
            "pointer_offset": hex(pointer_offset), "size": size,
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in actual],
            "function_sha256": hashlib.sha256(image[address - TEXT:address - TEXT + size]).hexdigest(),
            "ledger_name": row["name"], "category": row["category"],
        }

    callers = _direct_callers(image, set(FUNCTIONS))
    for address, details in FUNCTIONS.items():
        if callers[address] != details["callers"]:
            raise ValueError(f"Direct caller set changed at {address:#010x}: {callers[address]}")
    # Pin all instructions in the chosen window, not just heuristic xrefs.
    start, stop = CALLER_WINDOW["start"], CALLER_WINDOW["stop"]
    expected_window = (
        ("add", "r0, r4, #0x580"),
        ("bl", "#0x240ea4"),
        ("str", "r0, [r4, #0x10]"),
        ("add", "r0, r4, #0x580"),
        ("bl", "#0x29e3bc"),
        ("str", "r0, [r4, #0x14]"),
    )
    actual_window, window_size = _instructions(image, start, stop - start)
    if actual_window != expected_window or window_size != stop - start:
        raise ValueError(f"Manually reviewed caller window changed: {actual_window}")
    return {
        "code_sha256": digest,
        "functions": functions,
        "callers": {hex(address): [hex(site) for site in sites]
                    for address, sites in callers.items()},
        "caller_window": {
            "start": hex(start), "stop": hex(stop),
            "description": CALLER_WINDOW["description"],
            "calls": [{"site": hex(site), "callee": hex(callee)}
                      for site, callee in CALLER_WINDOW["calls"]],
            "scope": "Window starts at the pinned ADD; caller setup before it is excluded.",
        },
    }


def _make_case(address: int, seed: int, label: str, flag: int,
               pointer_word: int, alternate: int = 0) -> Case:
    details = FUNCTIONS[address]
    salt = sum((index + 1) * ord(char) for index, char in enumerate(label))
    rng = random.Random(seed ^ address ^ salt)
    data = bytearray(rng.randbytes(DATA_SIZE))
    obj = DATA + 0x200
    data[obj - DATA + details["flag_offset"]] = flag & 0xFF
    struct.pack_into("<I", data, obj - DATA + details["pointer_offset"], pointer_word & U32_MASK)
    # Distinct nearby fields make wrong-offset and too-wide flag reads visible.
    data[obj - DATA + 0x20] = alternate & 0xFF
    data[obj - DATA + 0x48] = (alternate ^ 0x5A) & 0xFF
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = obj
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def make_cases(address: int, samples: int, seed: int):
    boundaries = ((0, 0), (0, 1), (0, U32_MASK), (1, 0), (1, 0x12345678),
                  (2, 0x87654321), (0x7F, 0xAAAAAAAA),
                  (0x80, 0x55555555), (0xFF, 0xDEADBEEF))
    for flag, word in boundaries:
        yield _make_case(address, seed, f"boundary-{flag:02x}-{word:08x}", flag, word,
                         alternate=word >> 24)
    rng = random.Random(seed ^ address)
    for flag in range(256):
        yield _make_case(address, seed, f"exhaustive-flag-{flag:02x}", flag,
                         rng.getrandbits(32), rng.randrange(256))
    for index in range(samples):
        yield _make_case(address, seed + index, f"random-{index}", rng.randrange(256),
                         rng.getrandbits(32), rng.randrange(256))


def _caller_case(seed: int, flag_240ea4: int, flag_29e3bc: int) -> Case:
    # In the reviewed caller, r4+0x580 is the object. r4 and result slots stay
    # inside the mapped DATA page while the getter reads both target fields.
    effective_object = DATA + 0x700
    r4 = effective_object - 0x580
    rng = random.Random(seed ^ 0x397C3C)
    data = bytearray(rng.randbytes(DATA_SIZE))
    struct.pack_into("<I", data, effective_object - DATA + 0x48, 0xA1B2C3D4)
    struct.pack_into("<I", data, effective_object - DATA + 0x20, 0x55667788)
    # The first getter reads its flag then word; update +0x62 before the second
    # call via the second flag fixture is not possible on this shared object.
    # Both sites therefore intentionally receive the same flag value.
    if flag_240ea4 != flag_29e3bc:
        raise ValueError("Shared caller object requires matching flag fixtures")
    data[effective_object - DATA + 0x62] = flag_29e3bc & 0xFF
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[4] = r4
    return Case(f"caller-flags-{flag_240ea4:02x}-{flag_29e3bc:02x}", tuple(regs),
                bytes(data), rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _unmapped_pointer_slot_case(address: int, seed: int, flag: int) -> Case:
    # Place the object immediately before the mapped DATA page. Its +0x62 flag
    # is mapped at DATA, while either pointer slot (+0x20/+0x48) is unmapped.
    # This proves the set-flag path suppresses the load and the clear-flag path
    # faults at the same architectural access in both implementations.
    rng = random.Random(seed ^ address ^ flag)
    data = bytearray(rng.randbytes(DATA_SIZE))
    data[0] = flag & 0xFF
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = DATA - 0x62
    return Case(f"unmapped-pointer-slot-flag-{flag:02x}", tuple(regs), bytes(data),
                rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def run(code_path: Path, output: Path, samples: int = 64, seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    image, game_info, ledger = pinned.image, pinned.game_info, pinned.ledger
    reference = verify_reference(image, game_info, ledger)
    output.mkdir(parents=True, exist_ok=True)
    source_path = ROOT / "experiments/semantic_equivalence/conditional_pointer_getter_candidates.cpp"
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    required = {f"candidate_{address:08x}" for address in FUNCTIONS}
    required |= {"negative_wrong_offset_00240ea4", "negative_wrong_flag_width",
                 "negative_wrong_flag_sense"}
    compiled = compile_candidate_symbols(source_path, output / "conditional_pointer_getter_candidates.o",
                                         ROOT, required)

    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    functions = []
    for address, details in FUNCTIONS.items():
        symbol = f"candidate_{address:08x}"
        candidate_code = compiled[symbol]
        decoded = list(decoder.disasm(candidate_code, 0))
        expected_candidate = (
            ("ldrb", "r2, [r0, #0x62]"), ("mov", "r1, r0"),
            ("mov", "r0, #0"), ("cmp", "r2, #0"),
            ("ldreq", f"r0, [r1, #0x{details['pointer_offset']:x}]"),
            ("bx", "lr"),
        )
        actual_candidate = tuple((ins.mnemonic.lower(), ins.op_str.lower()) for ins in decoded)
        if actual_candidate != expected_candidate:
            raise ValueError(f"Candidate memory/branch shape changed at {address:#010x}: {actual_candidate}")
        original, candidate = Runner(image, address), Runner(image, address, candidate_code)
        count, failure = 0, None
        observed_reads = {}
        for case in make_cases(address, samples, seed):
            baseline = original.run(case)
            rebuilt = candidate.run(case)
            reason = difference(baseline, rebuilt, returns_value=True, compare_flags=False)
            observed_reads[case.label] = [hex(byte) for byte in sorted(baseline.reads)]
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "flag_offset": hex(details["flag_offset"]),
                          "pointer_offset": hex(details["pointer_offset"]),
                          "original_bytes": 20, "candidate_bytes": len(candidate_code),
                          "candidate_instructions": [f"{ins.mnemonic} {ins.op_str}" for ins in decoded],
                          "cases": count, "passed": failure is None, "failure": failure,
                          "example_read_footprints": observed_reads})

    # The same caller window executes both getters. Use flags equal per case;
    # eight variants cover clear/set branches and both returned pointer words.
    caller_results = []
    for index, flag in enumerate((0, 1, 2, 0xFF)):
        case = _caller_case(seed + index, flag, flag)
        for address in FUNCTIONS:
            symbol = f"candidate_{address:08x}"
            original = Runner(image, address)
            candidate = Runner(image, address, compiled[symbol])
            baseline = original.run(case, start=CALLER_WINDOW["start"],
                                   stops=(CALLER_WINDOW["stop"],), budget=128)
            rebuilt = candidate.run(case, start=CALLER_WINDOW["start"],
                                    stops=(CALLER_WINDOW["stop"],), budget=128)
            reason = difference(baseline, rebuilt, returns_value=False,
                                caller_window=True, compare_flags=True)
            caller_results.append({"candidate": hex(address), "flag": hex(flag),
                                   "passed": reason is None, "reason": reason,
                                   "callsite": hex(CALLER_WINDOW["calls"][0 if address == 0x00240EA4 else 1][0])})

    fault_results = []
    for address in FUNCTIONS:
        symbol = f"candidate_{address:08x}"
        for flag in (0, 1):
            case = _unmapped_pointer_slot_case(address, seed, flag)
            baseline = Runner(image, address).run(case)
            rebuilt = Runner(image, address, compiled[symbol]).run(case)
            same_fault = baseline.fault == rebuilt.fault
            expected_fault = flag == 0
            passed = same_fault and (baseline.fault is not None) == expected_fault
            if not expected_fault:
                passed = passed and baseline.result == rebuilt.result == 0
                passed = passed and baseline.reads == rebuilt.reads == frozenset({DATA})
            fault_results.append({"candidate": hex(address), "flag": hex(flag),
                                  "expected_fault": expected_fault,
                                  "original_fault": baseline.fault,
                                  "candidate_fault": rebuilt.fault,
                                  "same_fault": same_fault, "passed": passed})

    controls = (
        ("negative_wrong_offset_00240ea4", 0x00240EA4, 0, 0x10203040, 0x50607080),
        ("negative_wrong_flag_width", 0x00240EA4, 0, 0x01020304, 0x01020304),
        ("negative_wrong_flag_sense", 0x00240EA4, 1, 0x10203040, 0x10203040),
    )
    negative_controls = []
    for symbol, address, flag, pointer, alternate in controls:
        case = _make_case(address, seed, f"control-{symbol}", flag, pointer, alternate)
        if symbol == "negative_wrong_flag_width":
            data = bytearray(case.data)
            obj_offset = DATA + 0x200 - DATA
            data[obj_offset + 0x63:obj_offset + 0x66] = b"\0\0\0"
            case = Case(case.label, case.registers, bytes(data), case.stack, case.nzcv)
        reason = difference(Runner(image, address).run(case),
                            Runner(image, address, compiled[symbol]).run(case),
                            returns_value=True, compare_flags=False)
        negative_controls.append({"name": symbol, "detected": reason is not None,
                                  "reason": reason,
                                  "expected_reason": ("observable read footprint differs"
                                                      if symbol == "negative_wrong_flag_width"
                                                      else "return or read footprint differs")})

    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1, "experiment": "conditional_pointer_like_word_getters",
        "passed": (all(item["passed"] for item in functions)
                   and all(item["passed"] for item in caller_results)
                   and all(item["passed"] for item in fault_results)
                   and all(item["detected"] for item in negative_controls)),
        "scope": "two isolated getters plus a manually pinned paired-caller window",
        "reference": reference, "source_sha256": source_hash,
        "compiler": compiler.stdout.splitlines()[0], "seed": seed,
        "random_samples_per_function": samples,
        "exhaustive_flag_values_per_function": 256,
        "function_comparisons": sum(item["cases"] for item in functions),
        "caller_comparisons": len(caller_results), "functions": functions,
        "negative_controls": negative_controls, "caller_results": caller_results,
        "unmapped_slot_fault_results": fault_results,
        "limitations": [
            "Read-footprint comparison confirms the byte flag read and conditional four-byte pointer-slot read on ordinary mapped RAM.",
            "The targeted boundary fixture verifies mapped flag plus unmapped pointer-slot behavior for clear/set branches; other MMIO, protection, and partial-fault contexts are outside scope.",
            "The caller window starts at the pinned ADD that prepares r0; earlier caller setup and whole-game behavior are not tested.",
            "This is bounded emulator evidence, not whole-game equivalence or byte equivalence.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = run(args.code, args.output, samples=args.samples, seed=args.seed)
    print(json.dumps({"passed": report["passed"],
                      "function_comparisons": report["function_comparisons"],
                      "caller_comparisons": report["caller_comparisons"],
                      "negative_controls": report["negative_controls"]}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
