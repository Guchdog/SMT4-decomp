#!/usr/bin/env python3
"""Differentially test the paired halfword/low-byte record getters."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
    validate_leaf,
)

EXPECTED_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
FUNCTIONS = {
    0x002345F0: {"offset": 0x48, "words": (0xE1D004B8, 0xE20000FF, 0xE12FFF1E),
                 "symbol": "candidate_002345f0", "callers": (0x0038C5F4, 0x0038C670,
                 0x0038C708, 0x0038C8EC, 0x0038CE6C, 0x0038CEB4,
                 0x0038CEFC, 0x0038CF48, 0x0038D8CC, 0x0038D948,
                 0x0038D9F8, 0x0038DBAC, 0x0038DF84, 0x0038DFCC,
                 0x0038E014, 0x0038E060)},
    0x002345FC: {"offset": 0x4A, "words": (0xE1D004BA, 0xE20000FF, 0xE12FFF1E),
                 "symbol": "candidate_002345fc", "callers": (0x0038C5E8, 0x0038C664,
                 0x0038C6FC, 0x0038C8E0, 0x0038CE60, 0x0038CEA8,
                 0x0038CEF0, 0x0038CF3C, 0x0038D8C0, 0x0038D93C,
                 0x0038D9EC, 0x0038DBA0, 0x0038DF78, 0x0038DFC0,
                 0x0038E008, 0x0038E054)},
}
CALLER_WINDOWS = {
    0x002345FC: {"site": 0x0038C5E8, "stop": 0x0038C5F0,
                 "next": (0x0038C5EC, "mov", "r4, r0")},
    0x002345F0: {"site": 0x0038C5F4, "stop": 0x0038C5FC,
                 "next": (0x0038C5F8, "mov", "r2, r0")},
}


def _ledger():
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _direct_bl_targets(image: bytes) -> dict[int, list[int]]:
    refs = {target: [] for target in FUNCTIONS}
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        if word & 0x0F000000 != 0x0B000000:
            continue
        displacement = word & 0xFFFFFF
        if displacement & 0x800000:
            displacement -= 0x1000000
        target = (TEXT + offset + 8 + (displacement << 2)) & 0xFFFFFFFF
        if target in refs:
            refs[target].append(TEXT + offset)
    return refs


def verify_reference(image: bytes, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected code.bin SHA-256: {digest}")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    evidence = {}
    for address, spec in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or int(row["size"]) != 12 or row["status"] != "matching":
            raise ValueError(f"Ledger entry changed at {address:#010x}")
        original = image[address - TEXT:address - TEXT + 12]
        words = struct.unpack("<3I", original)
        if words != spec["words"]:
            raise ValueError(f"Instruction words changed at {address:#010x}: {words}")
        decoded = [(item.mnemonic, item.op_str) for item in decoder.disasm(original, address)]
        expected = [("ldrh", f"r0, [r0, #0x{spec['offset']:x}]"),
                    ("and", "r0, r0, #0xff"), ("bx", "lr")]
        if decoded != expected:
            raise ValueError(f"Instruction contract changed at {address:#010x}: {decoded}")
    actual_refs = _direct_bl_targets(image)
    for address, spec in FUNCTIONS.items():
        expected_refs = spec["callers"]
        if tuple(actual_refs[address]) != expected_refs:
            raise ValueError(f"Direct caller set changed at {address:#010x}: {actual_refs[address]}")
        evidence[hex(address)] = {
            "name": by_address[address]["name"], "size": int(by_address[address]["size"]),
            "offset": hex(spec["offset"]), "instruction_words": [f"0x{x:08x}" for x in spec["words"]],
            "direct_call_count": len(expected_refs), "direct_call_sites": [hex(x) for x in expected_refs],
        }
    return {"code_sha256": digest, "functions": evidence}


def verify_caller_windows(image: bytes) -> dict:
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    windows = {}
    for target, window in CALLER_WINDOWS.items():
        site = window["site"]
        raw = image[site - TEXT - 4:site - TEXT + 8]
        decoded = list(cs.disasm(raw, site - 4))
        expected = [("add", "r0, sl, #0x28"), ("bl", f"#0x{target:x}"),
                    (window["next"][1], window["next"][2])]
        actual = [(item.mnemonic, item.op_str) for item in decoded]
        if actual != expected:
            raise ValueError(f"Caller window changed at {site:#010x}: {actual}")
        windows[hex(target)] = {"caller": "script_vm_func_0038c43c",
                                "setup": hex(site - 4), "call": hex(site),
                                "stop": hex(window["stop"]), "instructions": actual}
    return windows


def make_cases(address: int, samples: int, seed: int):
    offset = FUNCTIONS[address]["offset"]
    rng = random.Random(seed ^ address)
    for index, low in enumerate((0, 1, 0x7F, 0x80, 0xFE, 0xFF)):
        data = bytearray(DATA_SIZE)
        base = 0x100 + (index % 4) * 4
        data[base + offset:base + offset + 2] = bytes((low, 0xA5 ^ index))
        regs = [0] * 13
        regs[0] = DATA + base
        yield Case(f"boundary-{low:02x}-high-{data[base+offset+1]:02x}", tuple(regs),
                   bytes(data), bytes(STACK_SIZE), (index & 0xF) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        base = 0x100 + (index % 8) * 4
        low, high = rng.randrange(256), rng.randrange(1, 256)
        data[base + offset:base + offset + 2] = bytes((low, high))
        regs = [rng.getrandbits(32) for _ in range(13)]
        regs[0] = DATA + base
        yield Case(f"random-{index}-lo-{low:02x}-hi-{high:02x}", tuple(regs),
                   bytes(data), rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _caller_case(address: int, seed: int) -> Case:
    offset = FUNCTIONS[address]["offset"]
    data = bytearray(DATA_SIZE)
    data[0x100 + offset:0x102 + offset] = bytes((0xD3, 0x7E))
    regs = [0] * 13
    regs[0] = DATA + 0x100
    regs[4] = 0x51515151
    return Case(f"caller-{address:08x}-seed-{seed}", tuple(regs), bytes(data),
                bytes(STACK_SIZE), (seed & 0xF) << 28)


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    reference = verify_reference(image, _ledger())
    caller_pins = verify_caller_windows(image)
    source = ROOT / "experiments/semantic_equivalence/halfword_lowbyte_candidates.cpp"
    build = compile_tu_armv6k(source, output / "halfword_lowbyte_candidates.o", ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(
            output / "halfword_lowbyte_candidates.o").items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code

    functions = []
    negatives = []
    caller_results = []
    for address, spec in FUNCTIONS.items():
        symbol = spec["symbol"]
        original = Runner(image, address)
        candidate = Runner(image, address, compiled[symbol])
        negative_runners = {
            control: Runner(image, address, compiled[control])
            for control in (f"wrong_offset_{address:08x}", f"wrong_mask_{address:08x}")
        }
        count = 0
        failure = None
        for case in make_cases(address, samples, seed):
            old, new = original.run(case), candidate.run(case)
            reason = difference(old, new, returns_value=True)
            base = case.registers[0]
            expected_reads = frozenset((base + spec["offset"], base + spec["offset"] + 1))
            if not reason and (old.reads != expected_reads or old.writes):
                reason = "unexpected halfword read footprint or write"
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "candidate": symbol,
                          "original_bytes": 12, "candidate_bytes": len(compiled[symbol]),
                          "cases": count, "passed": failure is None, "failure": failure})

        low_case = next(case for case in make_cases(address, 0, seed)
                        if case.data[case.registers[0] - DATA + spec["offset"] + 1] != 0)
        for control_name in (f"wrong_offset_{address:08x}", f"wrong_mask_{address:08x}"):
            reason = difference(original.run(low_case), negative_runners[control_name].run(low_case))
            negatives.append({"address": hex(address), "control": control_name,
                              "detected": reason is not None, "reason": reason})

        window = CALLER_WINDOWS[address]
        callcase = _caller_case(address, seed)
        old = original.run(callcase, start=window["site"],
                           stops=(window["stop"],), budget=16)
        new = candidate.run(callcase, start=window["site"],
                            stops=(window["stop"],), budget=16)
        caller_reason = difference(old, new, returns_value=False, caller_window=True,
                                   compare_flags=True)
        caller_results.append({"address": hex(address), "callsite": hex(window["site"]),
                               "stopped_at": hex(old.pc), "passed": caller_reason is None,
                               "reason": caller_reason,
                               "result_registers": {"original_r0": hex(old.result),
                                                    "candidate_r0": hex(new.result)}})

    report = {
        "experiment": "paired_halfword_low_byte_getters", "seed": seed,
        "random_samples_per_function": samples, "reference": reference,
        "caller_windows_pinned": caller_pins, "functions": functions,
        "negative_controls": negatives, "caller_window_results": caller_results,
        "passed": all(item["passed"] for item in functions + caller_results)
                  and all(item["detected"] for item in negatives),
        "limitations": [
            "Tests execute the two isolated getters and one original caller fragment per getter.",
            "Caller fragments begin at BL with the observed record pointer supplied in r0; caller setup before BL is pinned but not executed.",
            "The following instruction consumes the return value, but later helper calls are outside the caller window.",
            "This is not whole-program or emulator evidence and does not integrate candidates into production.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/halfword-lowbyte"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "caller_window_results": report["caller_window_results"]}, indent=2))


if __name__ == "__main__":
    main()
