#!/usr/bin/env python3
"""Pinned offline differential for H2 selector-2 normalizer 0x0013BAE0."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

import unicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools import h2_11c5ec_experiment as reader

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch44_c.cpp"
ADDRESS = 0x0013BAE0
SLOT_SIZE = 460
CONTEXT = 0x00500000
STOP = reader.STOP
REGS = [getattr(reader.arm, f"UC_ARM_REG_R{i}") for i in range(13)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE) -> tuple[bytes, list[dict], list[str]]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch44_c.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["func_0013bae0"]
    if len(body) > SLOT_SIZE:
        raise ValueError(f"production body {len(body)} exceeds original slot {SLOT_SIZE}")
    if relocations:
        raise ValueError(f"candidate must be self-contained, got relocations: {relocations}")
    if len(body) % 4:
        raise ValueError("ARM body is not word aligned")
    return body, [], list(result.args)


def stage_image(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    if len(body) > SLOT_SIZE or (SLOT_SIZE - len(body)) % 4:
        raise ValueError("body does not fit the original ARM slot")
    payload = body + struct.pack("<I", 0xE320F000) * ((SLOT_SIZE - len(body)) // 4)
    staged = bytearray(original)
    offset = ADDRESS - reader.CODE_BASE
    staged[offset:offset + SLOT_SIZE] = payload
    return bytes(staged), payload


def make_direct_case(index: int, seed: int, x: int, y: int,
                     calibration_a: int, calibration_b: int) -> dict:
    case = reader.make_case(index, 0, 1, 2, 0, 0, 1, seed)
    out = bytearray(case["output_bytes"])
    struct.pack_into("<hh", out, 0x0C, 0x6A35, -0x2487)
    case["output_bytes"] = bytes(out)
    case["direct_samples"] = (x, y)
    case["direct_calibration"] = (calibration_a, calibration_b)
    return case


class DirectMachine(reader.Machine):
    pass


def direct_result(image: bytes, case: dict) -> dict:
    machine = DirectMachine(image, case["count"], case["record"])
    machine.setup(case)
    uc = machine.uc
    x, y = case["direct_samples"]
    calibration_a, calibration_b = case["direct_calibration"]
    uc.reg_write(reader.arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(reader.arm.UC_ARM_REG_FPSCR, 0)
    for i, reg in enumerate(REGS):
        uc.reg_write(reg, (0xB7000000 + i * 0x00010203) & 0xFFFFFFFF)
    uc.reg_write(reader.arm.UC_ARM_REG_R0, reader.STATE + 0x0C)
    uc.reg_write(reader.arm.UC_ARM_REG_R1, reader.STATE + 0x0E)
    uc.reg_write(reader.arm.UC_ARM_REG_R2, x & 0xFFFFFFFF)
    uc.reg_write(reader.arm.UC_ARM_REG_R3, y & 0xFFFFFFFF)
    uc.reg_write(reader.arm.UC_ARM_REG_SP, reader.SP)
    uc.mem_write(reader.SP, struct.pack("<II", calibration_a & 0xFFFFFFFF,
                                         calibration_b & 0xFFFFFFFF))
    uc.reg_write(reader.arm.UC_ARM_REG_LR, STOP)
    machine.writes.clear()
    before = [uc.reg_read(reg) for reg in REGS]
    fault = None
    try:
        uc.emu_start(ADDRESS, 0, count=1000000)
    except unicorn.UcError as error:
        fault = type(error).__name__ + ": " + str(error)
    after = [uc.reg_read(reg) for reg in REGS]
    return {
        "fault": fault, "raw_r0": after[0],
        "callee_saved_registers": after[4:12],
        "callee_saved_preserved": after[4:12] == before[4:12],
        "sp": uc.reg_read(reader.arm.UC_ARM_REG_SP),
        "fpscr": uc.reg_read(reader.arm.UC_ARM_REG_FPSCR),
        "context": bytes(uc.mem_read(CONTEXT, 0x60)).hex(),
        "output": bytes(uc.mem_read(reader.STATE, 0x20)).hex(),
        "writes": [row for row in machine.writes if
                   CONTEXT <= row[0] < CONTEXT + 0x60 or
                   reader.STATE <= row[0] < reader.STATE + 0x20],
    }


def compare_view(result: dict) -> dict:
    return {key: result[key] for key in (
        "fault", "raw_r0", "callee_saved_registers", "callee_saved_preserved",
        "sp", "context", "output", "writes")}


def compile_mutant(out: Path, name: str, before: str, after: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise ValueError(f"mutation {name} source needle is not unique")
    path = out / "mutants" / f"{name}.cpp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace(before, after), encoding="utf-8")
    body, _relocs, _args = compile_body(out / "mutants" / f"{name}-compile", path)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261107)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned code.bin hash mismatch")

    body, relocations, compiler_args = compile_body(args.out / "compile")
    staged, payload = stage_image(original, body)
    offset = ADDRESS - reader.CODE_BASE
    ips = encode_ips([(offset, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("exact-slot IPS replay failed")
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-slot.ips").write_bytes(ips)

    cases: list[dict] = []
    index = 0
    calibration_pairs = ((40, 145), (40, 80), (80, 40), (0, 145),
                         (-1, 145), (-32768, 32767), (32767, -32768),
                         (40, 40), (36, 36), (200, 200))
    samples = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
               (39, 0), (40, 0), (41, 0), (-40, 0), (0, 39), (0, 40),
               (0, 41), (0, -40), (24, 32), (-24, 32), (24, -32),
               (-24, -32), (48, 64), (80, 0), (100, 0), (144, 0),
               (145, 0), (146, 0), (100, 100), (32767, -32768),
               (-32768, 32767), (32767, 32767), (-32768, -32768))
    for calibration_a, calibration_b in calibration_pairs:
        for x, y in samples:
            cases.append(make_direct_case(index, args.seed, x, y,
                                          calibration_a, calibration_b)); index += 1
    rng = random.Random(args.seed ^ 0xBADC0DE)
    for _ in range(72):
        cases.append(make_direct_case(index, args.seed ^ 0x7213,
                                      rng.randint(-32768, 32767),
                                      rng.randint(-32768, 32767),
                                      rng.randint(-32768, 32767),
                                      rng.randint(-32768, 32767)))
        index += 1

    direct_mismatches = []
    direct_rows = []
    for i, case in enumerate(cases):
        ref = direct_result(original, case)
        got = direct_result(staged, case)
        equal = compare_view(ref) == compare_view(got)
        if not equal:
            direct_mismatches.append({"case": i, "inputs": {
                "x": case["direct_samples"][0], "y": case["direct_samples"][1],
                "calibration_a": case["direct_calibration"][0],
                "calibration_b": case["direct_calibration"][1]},
                "original": ref, "candidate": got})
        direct_rows.append({"case": i, "equal": equal,
                            "inputs": [*case["direct_samples"],
                                       *case["direct_calibration"]]})

    caller_cases = []
    for seed in (args.seed, args.seed ^ 0x76E291):
        for i, (count, selector, x, y) in enumerate((
                (1, 2, 0, 0), (1, 2, 39, 0), (1, 2, 41, 2),
                (1, 2, 100, -100), (1, 2, 32767, -32768),
                (0, 2, 100, 100), (-1, 2, 100, 100), (1, 1, 100, 100),
                (1, 3, 100, 100))):
            case = reader.make_case(i, 0, count, selector, 0, 0, 1, seed)
            raw = bytearray(case["context_bytes"])
            struct.pack_into("<h", raw, 0x10, 40)
            struct.pack_into("<h", raw, 0x16, 145)
            case["context_bytes"] = bytes(raw)
            record = list(case["record"])
            record[3], record[4] = x, y
            case["record"] = tuple(record)
            ref = reader.run_one(original, case, True)
            got = reader.run_one(staged, case, True)
            caller_cases.append({"seed": seed, "index": i, "count": count,
                                 "selector": selector, "sample": [x, y],
                                 "equal": ref == got,
                                 "original": ref, "candidate": got})

    controls_spec = [
        ("boundary_extent", "const float boundary_extent = 36.0f;",
         "const float boundary_extent = 35.0f;",
         make_direct_case(800, args.seed ^ 0xD01, 50, 0, 40, 145)),
        ("boundary_clamp", "if (!(boundary_squared < 1600.0f)) boundary_squared = 1600.0f;",
         "if (!(boundary_squared < 1600.0f)) boundary_squared = boundary_squared;",
         make_direct_case(801, args.seed ^ 0xD02, 50, 50, 40, 145)),
        ("truncation_vs_rounding", "static_cast<s32>(scaled_x)",
         "static_cast<s32>(scaled_x + 0.99f)",
         make_direct_case(802, args.seed ^ 0xD03, 50, 0, 40, 145)),
    ]
    controls = {}
    for name, before, after, case in controls_spec:
        mutant_body = compile_mutant(args.out, name, before, after)
        mutant_image, _ = stage_image(original, mutant_body)
        ref = direct_result(original, case)
        mutant = direct_result(mutant_image, case)
        controls[name] = {"mutation_applied": True,
                          "detected": compare_view(ref) != compare_view(mutant),
                          "original": ref, "mutant": mutant}

    dispatch_site = 0x00128658
    dispatch_word = struct.unpack_from("<I", original,
                                       dispatch_site - reader.CODE_BASE)[0]
    if dispatch_word & 0xFF000000 != 0xEB000000:
        raise ValueError(f"expected selector-2 ARM BL at {dispatch_site:#x}")
    displacement = dispatch_word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    dispatch_target = dispatch_site + 8 + (displacement << 2)
    if dispatch_target != ADDRESS or dispatch_target & 1:
        raise ValueError(f"dispatcher targets {dispatch_target:#x}, not even ARM {ADDRESS:#x}")

    report = {
        "image_sha256": sha(original), "source_sha256": sha(SOURCE.read_bytes()),
        "candidate_body_sha256": sha(body), "candidate_body_bytes": len(body),
        "original_slot_bytes": SLOT_SIZE, "byte_identical": body == original[offset:offset + SLOT_SIZE],
        "seed": args.seed, "direct_cases": len(cases),
        "direct_mismatches": direct_mismatches, "direct_case_summary": direct_rows,
        "caller_cases": caller_cases, "mutation_controls": controls,
        "relocations": relocations, "all_relocations_even_arm": True,
        "selector2_callsite": {"site": hex(dispatch_site), "word": hex(dispatch_word),
                                "target": hex(dispatch_target), "bit0": dispatch_target & 1},
        "ips_replay": apply_ips(original, ips) == staged,
        "only_original_slot_changed": original[:offset] == staged[:offset]
            and original[offset + SLOT_SIZE:] == staged[offset + SLOT_SIZE:],
        "compiler_args": compiler_args,
        "fixture_sha256": sha(json.dumps(cases, sort_keys=True, separators=(",", ":"),
                                          default=lambda x: x.hex()).encode()),
        "caller_scope": "original dispatcher 0x00128610 with only selector-2 child 0x0013BAE0 staged; controlled ring-reader seam; pinned code.bin",
        "limits": ["valid disjoint synthetic RAM fixtures", "parent-reachable signed-halfword domain emphasized",
                   "FPSCR is recorded but excluded from the acceptance predicate", "no physical input or title-runtime claim"]
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"direct_cases": len(cases), "direct_mismatches": len(direct_mismatches),
                      "caller_cases": len(caller_cases),
                      "caller_mismatches": sum(not x["equal"] for x in caller_cases),
                      "body_bytes": len(body), "slot_bytes": SLOT_SIZE,
                      "controls": {k: v["detected"] for k, v in controls.items()},
                      "ips_replay": report["ips_replay"],
                      "only_original_slot_changed": report["only_original_slot_changed"]}, indent=2))
    return 0 if not direct_mismatches and all(x["equal"] for x in caller_cases) \
        and all(x["detected"] for x in controls.values()) and report["only_original_slot_changed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
