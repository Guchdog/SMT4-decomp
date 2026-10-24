#!/usr/bin/env python3
"""Isolated differential experiment for the uncovered 0x002F28F8 VFP leaf."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, get_armv6k_flags
from tools.semantic_experiment import TEXT
from tools.semantic_experiment_support import load_pinned_reference
from tools.vfp_sparse_scale_experiment import (
    Runner, SPECIAL, _case, _compare, require_unicorn,
)

ADDRESS = 0x002F28F8
SIZE = 68
SYMBOL = "candidate_002f28f8"
FIELDS = (0x64, 0x68, 0x74, 0x7C, 0x84)
SOURCE = ROOT / "experiments/semantic_equivalence/vfp_sparse_scale_002f28f8_candidates.cpp"


def expected_instructions():
    result = [("ldrd", "r0, r1, [r0, #0x20]")]
    for index, offset in enumerate(FIELDS):
        source_reg = "s1"
        result.extend((("vldr", f"{source_reg}, [r1, #0x{offset:x}]"),
                       ("vmul.f32", ("s0" if index == len(FIELDS) - 1 else "s1")
                        + f", {source_reg}, s0"),
                       ("vstr", ("s0" if index == len(FIELDS) - 1 else "s1")
                        + f", [r0, #0x{offset:x}]")))
    result.append(("bx", "lr"))
    return tuple(result)


def verify_reference(image: bytes, game_info: dict, ledger_rows: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    row = next((item for item in ledger_rows
                if int(item["address"], 16) == ADDRESS), None)
    if row is None or row["status"].strip() != "matching" or int(row["size"]) != SIZE:
        raise ValueError("missing matching 68-byte ledger row at 0x002f28f8")
    start = ADDRESS - TEXT
    body = image[start:start + SIZE]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = tuple((x.mnemonic.lower(), x.op_str.lower())
                    for x in decoder.disasm(body, ADDRESS))
    expected = expected_instructions()
    if decoded != expected:
        raise ValueError(f"reference body changed at {ADDRESS:#010x}: {decoded}")
    return {"code_sha256": digest, "functions": {hex(ADDRESS): {
        "name": row["name"], "status": row["status"], "size": SIZE,
        "sha256": hashlib.sha256(body).hexdigest(), "bytes": body.hex(),
        "ordered_lane_offsets": [hex(offset) for offset in FIELDS],
        "instructions": [f"{m} {ops}" for m, ops in expected],
        "observation": "Loads destination/source pointers from object+0x20; for five ordered offsets, loads source float, multiplies source-first by incoming s0 and stores at the same destination offset; final result reuses s0.",
        "unknown": "Caller intent and behavior outside this pinned ordinary-RAM leaf are unknown.",
    }}}


def make_cases(seed: int) -> list[dict]:
    cases = []
    index = 0
    for special_index, _ in enumerate(SPECIAL):
        source_bits = tuple(SPECIAL[(special_index + lane * 5) % len(SPECIAL)]
                            for lane in range(12))
        scale = SPECIAL[(special_index * 7 + 3) % len(SPECIAL)]
        for rounding in range(4):
            for flush in (0, 1):
                for default_nan in (0, 1):
                    fpscr = (rounding << 22) | (flush << 24) | (default_nan << 25) | (index & 0x1F)
                    cases.append(_case(seed, index, f"special-{special_index}-rm{rounding}-fz{flush}-dn{default_nan}",
                                       source_bits, scale, fpscr))
                    index += 1
    import random
    rng = random.Random(seed)
    for i in range(96):
        source_bits = tuple(rng.getrandbits(32) for _ in range(12))
        scale = rng.getrandbits(32)
        fpscr = ((i % 4) << 22) | (((i // 4) & 1) << 24) | (((i // 8) & 1) << 25) | (i & 0x1F)
        cases.append(_case(seed, index, f"random-{i}", source_bits, scale, fpscr))
        index += 1
    for delta in (0, 4, -4):
        source_bits = tuple(0x3F000001 + i * 0x101 for i in range(12))
        cases.append(_case(seed, index, f"alias-destination-{delta:+d}", source_bits,
                           0x3F812345, 0x1F, alias_delta=delta))
        index += 1
    source_bits = tuple(0x3F000001 + i * 0x101 for i in range(12))
    cases.append(_case(seed, index, "late-source-page-fault", source_bits,
                       0x3F800001, 0x1F, late_fault=True))
    return cases


def run(code_path: Path, output: Path, seed: int) -> dict:
    require_unicorn()
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    object_path = output / "vfp_sparse_scale_002f28f8_candidates.o"
    build = compile_tu_armv6k(SOURCE, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    symbols = {}
    for name, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"unexpected relocation in {name}: {relocations}")
        symbols[name] = code
    controls = {"negative_wrong_lane_002f28f8", "negative_omit_lane_002f28f8"}
    required = {SYMBOL} | controls
    if required - symbols.keys():
        raise ValueError(f"missing compiled symbols: {sorted(required - symbols.keys())}")
    flags = get_armv6k_flags(ROOT)
    if any(flag == "-Ofast" or flag.startswith("-ffast-math") for flag in flags):
        raise ValueError("fast-math is disallowed for IEEE-sensitive VFP experiment")
    cases = make_cases(seed)
    runner_ref = Runner(pinned.image, ADDRESS)
    runner_candidate = Runner(pinned.image, ADDRESS, symbols[SYMBOL])
    functions = []
    failure = None
    late = None
    for case in cases:
        ref, candidate = runner_ref.run(case), runner_candidate.run(case)
        if case["label"] == "late-source-page-fault":
            late = {"reference_faulted": bool(ref["fault"]),
                    "candidate_faulted": bool(candidate["fault"]),
                    "ordinary_memory_and_access_sets_equal": (
                        ref["data"] == candidate["data"] and
                        ref["reads"] == candidate["reads"] and
                        ref["writes"] == candidate["writes"])}
        reason = _compare(ref, candidate)
        if reason:
            failure = {"case": case["label"], "field": reason}
            break
    functions.append({"address": hex(ADDRESS), "candidate": SYMBOL,
                      "original_bytes": SIZE, "candidate_bytes": len(symbols[SYMBOL]),
                      "cases": len(cases) if failure is None else cases.index(case) + 1,
                      "passed": failure is None, "failure": failure,
                      "late_fault_evidence": late})
    control_case = next(x for x in cases if x["label"] == "random-0")
    negative_controls = []
    reference_result = Runner(pinned.image, ADDRESS).run(control_case)
    for control, observed in (("negative_wrong_lane_002f28f8", "wrong source member"),
                              ("negative_omit_lane_002f28f8", "omitted stores")):
        wrong = Runner(pinned.image, ADDRESS, symbols[control]).run(control_case)
        negative_controls.append({"control": control, "detects": observed,
                                  "detected": reference_result["data"] != wrong["data"]})
    report = {
        "schema": 1, "experiment": "vfp_sparse_scale_002f28f8_uncovered_leaf",
        "passed": all(item["passed"] for item in functions) and all(item["detected"] for item in negative_controls),
        "scope": "one pinned ARM11 VFP leaf; isolated ordinary-memory differential, not game boot",
        "reference_sha256": pinned.game_info["code_sha256"],
        "reference_functions": reference["functions"],
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler_flags": flags, "fast_math": False, "seed": seed,
        "function_comparisons": functions[0]["cases"],
        "cases_per_function": len(cases),
        "case_mix": {"special_ieee_fpscr": len(SPECIAL) * 16,
                     "random": 96, "overlap_alias": 3, "late_source_fault": 1},
        "functions": functions, "negative_controls": negative_controls,
        "caller_windows": [],
        "limitations": ["Finite differential cases are evidence, not proof over all inputs.",
                        "Unicorn ARM11 MPCore VFPv2 and ordinary RAM only; hardware traps, MMIO, timing and concurrency are outside scope.",
                        "No callers, emulator boot or full game runtime were tested; no ledger or production code changes."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
