#!/usr/bin/env python3
"""Pinned two-seed differential extension for eight sparse VFP scale leaves."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, get_armv6k_flags
from tools.semantic_experiment import TEXT
from tools.semantic_experiment_support import load_pinned_reference
from tools.vfp_sparse_scale_experiment import Runner, _compare, SPECIAL

# Per-function ordered byte offsets are pinned independently, rather than
# inferred from the four-function parent experiment's lane maps.
FUNCTIONS = {
    0x002DD08C: ("candidate_002dd08c", (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xD0, 0xDC, 0xE4)),
    0x002E5BA4: ("candidate_002e5ba4", (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xD0, 0xD8, 0xDC)),
    0x0030C93C: ("candidate_0030c93c", (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xDC, 0xE4, 0xE8)),
    0x0030C9B0: ("candidate_0030c9b0", (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xD8, 0xE0, 0xE4)),
    0x0031341C: ("candidate_0031341c", (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xD8, 0xE0, 0xE4)),
    0x00313578: ("candidate_00313578", (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xD0, 0xD8, 0xDC)),
    0x002F293C: ("candidate_002f293c", (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xD0, 0xE4)),
    0x00313490: ("candidate_00313490", (0x64, 0x68, 0x74, 0x7C, 0x84, 0xC8, 0xCC, 0xDC)),
}
SIZES = {address: (116 if len(offsets) == 9 else 104)
         for address, (_, offsets) in FUNCTIONS.items()}
SPECIAL_CASES = (
    0x00000000, 0x80000000, 0x00000001, 0x80000001,
    0x007FFFFF, 0x807FFFFF, 0x00800000, 0x80800000,
    0x3F800000, 0xBF800000, 0x7F7FFFFF, 0xFF7FFFFF,
    0x7F800000, 0xFF800000, 0x7FC12345, 0xFFC54321,
    0x7F812345, 0xFF812345,
)
ALL_OFFSETS = tuple(sorted({offset for _, offsets in FUNCTIONS.values() for offset in offsets}))


def expected_instructions(offsets: tuple[int, ...]):
    result = [("ldrd", "r0, r1, [r0, #0x20]")]
    for index, offset in enumerate(offsets):
        value_reg = "s1"
        output_reg = "s0" if index == len(offsets) - 1 else "s1"
        result.extend((("vldr", f"{value_reg}, [r1, #0x{offset:x}]"),
                       ("vmul.f32", f"{output_reg}, {value_reg}, s0"),
                       ("vstr", f"{output_reg}, [r0, #0x{offset:x}]")))
    result.append(("bx", "lr"))
    return tuple(result)


def verify_reference(image: bytes, game_info: dict, ledger_rows: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    ledger = {int(row["address"], 16): row for row in ledger_rows}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    functions = {}
    for address, (symbol, offsets) in FUNCTIONS.items():
        size = SIZES[address]
        row = ledger.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != size:
            raise ValueError(f"missing matching {size}-byte ledger row at {address:#010x}")
        start = address - TEXT
        body = image[start:start + size]
        decoded = tuple((x.mnemonic.lower(), x.op_str.lower())
                        for x in decoder.disasm(body, address))
        expected = expected_instructions(offsets)
        if decoded != expected:
            raise ValueError(f"reference body changed at {address:#010x}: {decoded}")
        functions[hex(address)] = {
            "name": row["name"], "status": row["status"], "size": size,
            "sha256": hashlib.sha256(body).hexdigest(), "bytes": body.hex(),
            "ordered_lane_offsets": [hex(x) for x in offsets],
            "instructions": [f"{mnemonic} {ops}" for mnemonic, ops in expected],
            "observation": "ldrd loads destination/source from object+0x20; each lane is loaded from source, multiplied source-first by incoming s0, and stored to the same destination offset; final product reuses s0; bx lr returns.",
        }
    return {"code_sha256": digest, "functions": functions}


def _case(seed: int, index: int, label: str, source_bits: tuple[int, ...],
          scale_bits: int, fpscr: int, alias_delta: int | None = None,
          late_fault: bool = False) -> dict:
    from tools.semantic_experiment import DATA, STACK_SIZE
    from tools.vfp_sparse_scale_experiment import DATA_SIZE
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    object_off, source_off, destination_off = 0x200, 0x1000, 0x2800
    if alias_delta is not None:
        destination_off = source_off + alias_delta
    if late_fault:
        source_off = DATA_SIZE - 0x80
    struct.pack_into("<II", data, object_off + 0x20,
                     DATA + destination_off, DATA + source_off)
    for lane, offset in enumerate(ALL_OFFSETS):
        if source_off + offset + 4 <= DATA_SIZE:
            struct.pack_into("<I", data, source_off + offset,
                             source_bits[lane % len(source_bits)])
    gp = [rng.getrandbits(32) for _ in range(13)]
    gp[0] = DATA + object_off
    s = [rng.getrandbits(32) for _ in range(32)]
    s[0] = scale_bits
    return {"label": label, "gp": tuple(gp), "s": tuple(s), "fpscr": fpscr,
            "data": bytes(data), "stack": rng.randbytes(STACK_SIZE)}


def make_cases(seed: int) -> list[dict]:
    cases = []
    index = 0
    for special_index, _ in enumerate(SPECIAL_CASES):
        source = tuple(SPECIAL_CASES[(special_index + lane * 5) % len(SPECIAL_CASES)]
                       for lane in range(18))
        scale = SPECIAL_CASES[(special_index * 7 + 3) % len(SPECIAL_CASES)]
        for rounding in range(4):
            for flush in (0, 1):
                for default_nan in (0, 1):
                    fpscr = (rounding << 22) | (flush << 24) | (default_nan << 25) | (index & 0x1F)
                    cases.append(_case(seed, index, f"special-{special_index}-rm{rounding}-fz{flush}-dn{default_nan}", source, scale, fpscr))
                    index += 1
    rng = random.Random(seed)
    for i in range(96):
        source = tuple(rng.getrandbits(32) for _ in range(18))
        scale = rng.getrandbits(32)
        fpscr = ((i % 4) << 22) | (((i // 4) & 1) << 24) | (((i // 8) & 1) << 25) | (i & 0x1F)
        cases.append(_case(seed, index, f"random-{i}", source, scale, fpscr))
        index += 1
    source = tuple(0x3F000001 + i * 0x101 for i in range(18))
    for delta in (0, 4, -4):
        cases.append(_case(seed, index, f"alias-destination-{delta:+d}", source,
                           0x3F812345, 0x1F, alias_delta=delta))
        index += 1
    cases.append(_case(seed, index, "late-source-page-fault", source,
                       0x3F800001, 0x1F, late_fault=True))
    return cases


def run(code_path: Path, output: Path, seed: int) -> dict:
    from tools.semantic_experiment import DATA
    output.mkdir(parents=True, exist_ok=False)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    source_path = ROOT / "experiments/semantic_equivalence/vfp_sparse_scale_extension_candidates.cpp"
    object_path = output / "vfp_sparse_scale_extension_candidates.o"
    controls = {"extension_negative_wrong_lane", "extension_negative_omit_lane"}
    build = compile_tu_armv6k(source_path, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K extension candidate compilation failed")
    symbols = {}
    for name, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"unexpected relocation in {name}: {relocations}")
        symbols[name] = code
    required = {entry[0] for entry in FUNCTIONS.values()} | controls
    if required - symbols.keys():
        raise ValueError(f"missing compiled symbols: {sorted(required - symbols.keys())}")
    flags = get_armv6k_flags(ROOT)
    if any(flag == "-Ofast" or flag.startswith("-ffast-math") for flag in flags):
        raise ValueError("fast-math is disallowed for IEEE-sensitive VFP experiment")
    cases = make_cases(seed)
    function_reports = []
    for address, (symbol, offsets) in FUNCTIONS.items():
        ref_runner = Runner(pinned.image, address)
        candidate_runner = Runner(pinned.image, address, symbols[symbol])
        failure = None
        late_fault_evidence = None
        caller_saved_differences = []
        for case in cases:
            ref, candidate = ref_runner.run(case), candidate_runner.run(case)
            if case["label"] == "late-source-page-fault":
                late_fault_evidence = {
                    "reference_faulted": bool(ref["fault"]), "candidate_faulted": bool(candidate["fault"]),
                    "reference_committed_write_bytes": len(ref["writes"]),
                    "candidate_committed_write_bytes": len(candidate["writes"]),
                    "ordinary_memory_and_access_sets_equal": (ref["data"] == candidate["data"] and ref["reads"] == candidate["reads"] and ref["writes"] == candidate["writes"]),
                }
            changed = [i for i, (a, b) in enumerate(zip(ref["s"][:16], candidate["s"][:16])) if a != b]
            if changed and len(caller_saved_differences) < 6:
                caller_saved_differences.append({"case": case["label"], "s_registers": changed})
            reason = _compare(ref, candidate)
            if reason:
                failure = {"case": case["label"], "field": reason,
                           "reference_fault": ref["fault"], "candidate_fault": candidate["fault"]}
                break
        function_reports.append({"address": hex(address), "candidate": symbol,
                                 "original_bytes": SIZES[address], "candidate_bytes": len(symbols[symbol]),
                                 "lane_offsets": [hex(x) for x in offsets],
                                 "cases": len(cases) if failure is None else cases.index(case) + 1,
                                 "passed": failure is None, "failure": failure,
                                 "caller_saved_s_differences": caller_saved_differences,
                                 "late_fault_evidence": late_fault_evidence})
    control_case = next(case for case in cases if case["label"] == "random-0")
    negative_controls = []
    for symbol, detected_behavior in (("extension_negative_wrong_lane", "wrong source member"),
                                      ("extension_negative_omit_lane", "omitted store")):
        address = next(iter(FUNCTIONS))
        ref = Runner(pinned.image, address).run(control_case)
        wrong = Runner(pinned.image, address, symbols[symbol]).run(control_case)
        negative_controls.append({"control": symbol, "detects": detected_behavior,
                                  "detected": ref["data"] != wrong["data"]})
    report = {
        "schema": 1, "experiment": "vfp_sparse_scale_eight_member_extension",
        "passed": all(item["passed"] for item in function_reports) and all(item["detected"] for item in negative_controls),
        "scope": "eight additional pinned ARM11 sparse VFP leaves; isolated ordinary-memory differential, not game boot",
        "reference_sha256": pinned.game_info["code_sha256"], "reference_functions": reference["functions"],
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler_flags": flags, "fast_math": False, "seed": seed,
        "function_comparisons": sum(item["cases"] for item in function_reports),
        "cases_per_function": len(cases),
        "case_mix": {"special_ieee_fpscr": len(SPECIAL_CASES) * 16, "random": 96,
                     "overlap_alias": 3, "late_source_fault": 1},
        "comparison_policy": ["return/fault outcome", "callee-saved r4-r11 and SP", "FPSCR/FPEXC",
                              "callee-saved s16-s31", "all ordinary RAM and stack bytes", "ordinary-RAM byte read/write sets"],
        "caller_saved_policy": "r0-r3/r12 and s0-s15 differences are diagnostic only, not required equal by ABI.",
        "functions": function_reports, "negative_controls": negative_controls, "caller_windows": [],
        "limitations": ["Finite differential cases are evidence, not proof over all inputs.",
                        "Unicorn ARM11 MPCore VFPv2 and ordinary RAM only; hardware traps, MMIO, timing and concurrency are outside scope.",
                        "No callers, emulator boot, ledger or production code were tested or changed."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed)
    print(json.dumps({"passed": report["passed"], "comparisons": report["function_comparisons"],
                      "functions": report["functions"], "controls": report["negative_controls"],
                      "report": str(args.output / "report.json")}))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
