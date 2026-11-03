#!/usr/bin/env python3
"""Final-VMA differential for selector-0 radial helper 0x0013B9FC."""
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
SOURCE = ROOT / "src/engine/leaf_batch30_a.cpp"
ADDRESS = 0x0013B9FC
SLOT_SIZE = 228
DIVIDE = 0x002C615C
CONTEXT = 0x00500000
STOP = reader.STOP
REGS = [getattr(reader.arm, f"UC_ARM_REG_R{i}") for i in range(13)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def arm_bl(site: int, target: int) -> int:
    delta = target - (site + 8)
    if target & 3 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError(f"invalid ARM call target {site:#x}->{target:#x}")
    return 0xEB000000 | ((delta >> 2) & 0xFFFFFF)


def compile_body(out: Path, source: Path = SOURCE) -> tuple[bytes, list[dict], list[str]]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch30_a.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["ui_func_0013b9fc"]
    if len(body) > SLOT_SIZE:
        raise ValueError(f"production body {len(body)} exceeds original slot {SLOT_SIZE}")
    fixed = bytearray(body)
    if len(relocations) != 3:
        raise ValueError(f"expected three divide call relocations, found {len(relocations)}")
    records = []
    for reloc in relocations:
        if reloc.relocation_type != 28 or reloc.symbol_name != "ui_func_002c615c":
            raise ValueError(f"unexpected relocation: {reloc}")
        word = arm_bl(ADDRESS + reloc.offset, DIVIDE)
        struct.pack_into("<I", fixed, reloc.offset, word)
        records.append({"offset": reloc.offset, "type": "R_ARM_CALL",
                        "symbol": reloc.symbol_name, "target": hex(DIVIDE),
                        "entry_bit0": DIVIDE & 1, "word": hex(word)})
    return bytes(fixed), records, list(result.args)


def stage_image(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    if len(body) > SLOT_SIZE or (SLOT_SIZE - len(body)) % 4:
        raise ValueError("body does not fit the original ARM slot")
    payload = body + struct.pack("<I", 0xE320F000) * ((SLOT_SIZE - len(body)) // 4)
    staged = bytearray(original)
    offset = ADDRESS - reader.CODE_BASE
    staged[offset:offset + SLOT_SIZE] = payload
    return bytes(staged), payload


def make_direct_case(index: int, seed: int, x: int, y: int,
                     inner: int, outer: int) -> dict:
    case = reader.make_case(index, 0, 1, 0, 0, 0, 1, seed)
    raw = bytearray(case["context_bytes"])
    struct.pack_into("<ii", raw, 0x0C, inner, 0)
    struct.pack_into("<i", raw, 0x12, outer)
    case["context_bytes"] = bytes(raw)
    out = bytearray(case["output_bytes"])
    struct.pack_into("<hh", out, 0x0C, 0x6A35, -0x2487)
    case["output_bytes"] = bytes(out)
    case["direct_samples"] = (x, y)
    case["direct_calibration"] = (inner, outer)
    return case


class DivideTraceMachine(reader.Machine):
    def __init__(self, image: bytes, case: dict):
        super().__init__(image, case["count"], case["record"])
        self.divide_calls: list[dict] = []
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._divide_entry,
                         begin=DIVIDE, end=DIVIDE)

    def _divide_entry(self, uc, _address, _size, _data):
        sp = uc.reg_read(reader.arm.UC_ARM_REG_SP)
        self.divide_calls.append({
            "numerator_bits": uc.reg_read(reader.arm.UC_ARM_REG_R0),
            "denominator_bits": uc.reg_read(reader.arm.UC_ARM_REG_R1),
            "sp": sp, "sp_aligned_8": sp % 8 == 0,
        })


def direct_result(image: bytes, case: dict) -> dict:
    machine = DivideTraceMachine(image, case)
    machine.setup(case)
    uc = machine.uc
    x, y = case["direct_samples"]
    inner, outer = case["direct_calibration"]
    uc.reg_write(reader.arm.UC_ARM_REG_FPEXC, 0x40000000)
    for i, reg in enumerate(REGS):
        uc.reg_write(reg, (0xB7000000 + i * 0x00010203) & 0xFFFFFFFF)
    uc.reg_write(reader.arm.UC_ARM_REG_R0, reader.STATE + 0x0C)
    uc.reg_write(reader.arm.UC_ARM_REG_R1, reader.STATE + 0x0E)
    uc.reg_write(reader.arm.UC_ARM_REG_R2, x & 0xFFFFFFFF)
    uc.reg_write(reader.arm.UC_ARM_REG_R3, y & 0xFFFFFFFF)
    uc.reg_write(reader.arm.UC_ARM_REG_SP, reader.SP)
    uc.mem_write(reader.SP, struct.pack("<II", inner & 0xFFFFFFFF,
                                         outer & 0xFFFFFFFF))
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
        # AAPCS callee-saved core registers are r4-r11; r12 is caller-saved.
        "callee_saved_registers": after[4:12],
        "callee_saved_preserved": after[4:12] == before[4:12],
        "sp": uc.reg_read(reader.arm.UC_ARM_REG_SP),
        "context": bytes(uc.mem_read(CONTEXT, 0x60)).hex(),
        "output": bytes(uc.mem_read(reader.STATE, 0x20)).hex(),
        "writes": [row for row in machine.writes if
                   CONTEXT <= row[0] < CONTEXT + 0x60 or
                   reader.STATE <= row[0] < reader.STATE + 0x20],
        "divide_calls": machine.divide_calls,
    }


def compare_view(result: dict) -> dict:
    compared = {key: result[key] for key in (
        "fault", "raw_r0", "callee_saved_registers", "callee_saved_preserved",
        "sp", "context", "output", "writes")}
    compared["divide_calls"] = [
        {key: call[key] for key in
         ("numerator_bits", "denominator_bits", "sp_aligned_8")}
        for call in result["divide_calls"]]
    return compared


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
    parser.add_argument("--seed", type=int, default=20261106)
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
    for inner, outer in ((40, 145), (40, 80), (80, 40), (0, 145), (-1, 145)):
        for x, y in ((0, 0), (39, 0), (40, 0), (41, 0), (0, 39), (0, 40),
                     (0, 41), (24, 32), (48, 64), (80, 0), (100, 0),
                     (144, 0), (145, 0), (146, 0), (100, 100), (-41, 0)):
            cases.append(make_direct_case(index, args.seed, x, y, inner, outer)); index += 1
    for x in (361, 362, 363, 400, 500, 32767, -32768,
              0x7FFFFFFF, -0x80000000, 50000, -50000):
        cases.append(make_direct_case(index, args.seed ^ 0x1199, x, 0, 40, 145)); index += 1
    rng = random.Random(args.seed ^ 0xBADC0DE)
    for _ in range(16):
        cases.append(make_direct_case(index, args.seed ^ 0x7213,
                                      rng.randint(-32768, 32767),
                                      rng.randint(-32768, 32767),
                                      rng.randint(0, 200), rng.randint(0, 200)))
        index += 1

    direct_mismatches = []
    zero_divisor_cases = []
    direct_rows = []
    for i, case in enumerate(cases):
        ref = direct_result(original, case)
        got = direct_result(staged, case)
        equal = compare_view(ref) == compare_view(got)
        if not equal:
            direct_mismatches.append({"case": i, "inputs": {
                "x": case["direct_samples"][0], "y": case["direct_samples"][1],
                "inner": case["direct_calibration"][0],
                "outer": case["direct_calibration"][1]},
                "original": ref, "candidate": got})
        zero_calls = [call for call in got["divide_calls"]
                      if call["denominator_bits"] == 0]
        if zero_calls:
            zero_divisor_cases.append({"case": i, "calls": zero_calls})
        direct_rows.append({"case": i, "inputs": {
            "x": case["direct_samples"][0], "y": case["direct_samples"][1],
            "inner": case["direct_calibration"][0],
            "outer": case["direct_calibration"][1]},
            "equal": equal, "divide_call_count": len(got["divide_calls"])})

    caller_cases = []
    for seed in (args.seed, args.seed ^ 0x76E291):
        for i, (count, selector, x, y) in enumerate((
                (1, 0, 0, 0), (1, 0, 39, 0), (1, 0, 41, 2),
                (1, 0, 100, -100), (1, 0, 32767, -32768),
                (0, 0, 100, 100), (-1, 0, 100, 100), (1, 1, 100, 100))):
            case = reader.make_case(i, 0, count, selector, 0, 0, 1, seed)
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
        ("inner_uses_outer", "static_cast<u32>(calibration_a)\n                                 * static_cast<u32>(calibration_a)",
         "static_cast<u32>(calibration_b)\n                                 * static_cast<u32>(calibration_b)",
         make_direct_case(700, args.seed ^ 0xD01, 100, 0, 40, 145)),
        ("deadzone_store_order", "*output_y = 0;\n        *output_x = 0;",
         "*output_x = 0;\n        *output_y = 0;",
         make_direct_case(701, args.seed ^ 0xD02, 39, 0, 40, 145)),
        ("divide_denominator_off_by_one", "numerator_bits, static_cast<u32>(denominator));",
         "numerator_bits, static_cast<u32>(denominator + 1));",
         make_direct_case(702, args.seed ^ 0xD03, 100, 0, 40, 145)),
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

    dispatch_site = 0x00128678
    dispatch_word = struct.unpack_from("<I", original,
                                       dispatch_site - reader.CODE_BASE)[0]
    if dispatch_word & 0xFF000000 != 0xEB000000:
        raise ValueError(f"expected selector-0 ARM BL at {dispatch_site:#x}")
    displacement = dispatch_word & 0x00FFFFFF
    if displacement & 0x00800000: displacement -= 0x01000000
    dispatch_target = dispatch_site + 8 + (displacement << 2)
    if dispatch_target != ADDRESS or dispatch_target & 1:
        raise ValueError(f"normalizer dispatcher targets {dispatch_target:#x}, not even ARM {ADDRESS:#x}")

    report = {
        "image_sha256": sha(original), "source_sha256": sha(SOURCE.read_bytes()),
        "candidate_body_sha256": sha(body), "candidate_body_bytes": len(body),
        "original_slot_bytes": SLOT_SIZE,
        "byte_identical": body == original[offset:offset + SLOT_SIZE],
        "seed": args.seed, "direct_cases": len(cases),
        "direct_mismatches": direct_mismatches,
        "direct_case_summary": direct_rows,
        "zero_divisor_observations": zero_divisor_cases,
        "caller_cases": caller_cases, "mutation_controls": controls,
        "relocations": relocations,
        "all_relocations_even_arm": all(x["entry_bit0"] == 0 for x in relocations),
        "selector0_callsite": {"site": hex(dispatch_site), "word": hex(dispatch_word),
                                "target": hex(dispatch_target), "bit0": dispatch_target & 1},
        "ips_replay": apply_ips(original, ips) == staged,
        "only_original_slot_changed": original[:offset] == staged[:offset]
            and original[offset + SLOT_SIZE:] == staged[offset + SLOT_SIZE:],
        "compiler_args": compiler_args,
        "fixture_sha256": sha(json.dumps(cases, sort_keys=True, separators=(",", ":"),
                                          default=lambda x: x.hex()).encode()),
        "caller_scope": "original 0x001078D8/0x0011C5EC/0x00128610 with only 0x0013B9FC staged; controlled 0x0012A758 reader; original 0x002C615C divider",
        "limits": ["valid disjoint ordinary RAM fixtures",
                   "original signed divide helper retained",
                   "no physical input meaning or runtime cadence claim"]
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"direct_cases": len(cases),
                      "direct_mismatches": len(direct_mismatches),
                      "caller_cases": len(caller_cases),
                      "caller_mismatches": sum(not x["equal"] for x in caller_cases),
                      "zero_divisor_observations": len(zero_divisor_cases),
                      "body_bytes": len(body), "slot_bytes": SLOT_SIZE,
                      "controls": {k: v["detected"] for k, v in controls.items()},
                      "relocations": relocations,
                      "ips_replay": report["ips_replay"]}, indent=2))
    return 0 if not direct_mismatches and all(x["equal"] for x in caller_cases) \
        and all(x["detected"] for x in controls.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
