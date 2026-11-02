#!/usr/bin/env python3
"""Final-VMA direct and H2 reader-chain differential for 0x001285C4."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools import h2_11c5ec_experiment as reader

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch11_b.cpp"
ADDRESS = 0x001285C4
SLOT_SIZE = 76
CONTEXT = 0x00500000
CALIBRATION = CONTEXT + 0x0C
STOP = reader.STOP
REGS = [getattr(reader.arm, f"UC_ARM_REG_R{i}") for i in range(13)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE) -> tuple[bytes, list[str]]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch11_b.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["func_001285c4"]
    if relocations:
        raise ValueError(f"unexpected relocations in leaf clamp: {relocations}")
    if len(body) > SLOT_SIZE:
        raise ValueError(f"production body {len(body)} exceeds original slot {SLOT_SIZE}")
    return body, list(result.args)


def stage_image(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    if len(body) > SLOT_SIZE or (SLOT_SIZE - len(body)) % 4:
        raise ValueError("body does not fit the original ARM slot")
    payload = body + struct.pack("<I", 0xE320F000) * ((SLOT_SIZE - len(body)) // 4)
    staged = bytearray(original)
    offset = ADDRESS - reader.CODE_BASE
    staged[offset:offset + SLOT_SIZE] = payload
    return bytes(staged), payload


def verify_original_callsite(original: bytes) -> dict:
    site = 0x0011C61C
    word = struct.unpack_from("<I", original, site - reader.CODE_BASE)[0]
    if word & 0xFF000000 != 0xEB000000:
        raise ValueError(f"expected ARM BL at {site:#x}, got {word:#010x}")
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    target = site + 8 + (displacement << 2)
    if target != ADDRESS or target & 1:
        raise ValueError(f"caller reaches {target:#x}; expected even ARM entry {ADDRESS:#x}")
    return {"site": hex(site), "instruction": hex(word),
            "target": hex(target), "target_bit0": target & 1,
            "state": "ARM"}


def case_for(field: int, value: int, seed: int, index: int) -> dict:
    case = reader.make_case(index, 0, 1, 0, 0, 1, 1, seed)
    raw = bytearray(case["context_bytes"])
    # Vary all untouched halfwords so the whole record is compared, not just
    # the five fields that the clamp is expected to modify.
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    for offset in range(0, 0x30, 2):
        struct.pack_into("<h", raw, offset, rng.randint(-32768, 32767))
    struct.pack_into("<h", raw, 0x0C + field * 2, value)
    case["context_bytes"] = bytes(raw)
    return case


def direct_result(image: bytes, case: dict) -> dict:
    machine = reader.Machine(image, case["count"], case["record"])
    machine.setup(case)
    uc = machine.uc
    uc.reg_write(reader.arm.UC_ARM_REG_FPEXC, 0x40000000)
    for i, reg in enumerate(REGS):
        uc.reg_write(reg, (0xA5000000 + i * 0x010203) & 0xFFFFFFFF)
    uc.reg_write(reader.arm.UC_ARM_REG_R0, CALIBRATION)
    uc.reg_write(reader.arm.UC_ARM_REG_R1, reader.STATE)
    uc.reg_write(reader.arm.UC_ARM_REG_SP, reader.SP)
    uc.reg_write(reader.arm.UC_ARM_REG_LR, STOP)
    before = [uc.reg_read(reg) for reg in REGS]
    fault = None
    try:
        uc.emu_start(ADDRESS, 0, count=5000)
    except Exception as exc:  # retain matching fault classes as evidence
        fault = type(exc).__name__ + ": " + str(exc)
    after = [uc.reg_read(reg) for reg in REGS]
    context = bytes(uc.mem_read(CONTEXT, 0x60))
    writes = [row for row in machine.writes
              if CONTEXT <= row[0] < CONTEXT + 0x60]
    return {"fault": fault, "registers": after, "registers_before": before,
            "sp": uc.reg_read(reader.arm.UC_ARM_REG_SP),
            "lr": uc.reg_read(reader.arm.UC_ARM_REG_LR),
            "context": context.hex(), "writes": writes}


def compile_mutant(out: Path, name: str, before: str, after: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise ValueError(f"mutation {name} source needle is not unique")
    path = out / "mutants" / f"{name}.cpp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace(before, after), encoding="utf-8")
    body, _args = compile_body(out / "mutants" / f"{name}-compile", path)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261102)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original code.bin hash mismatch")
    original_callsite = verify_original_callsite(original)

    body, compiler_args = compile_body(args.out / "compile")
    staged, payload = stage_image(original, body)
    offset = ADDRESS - reader.CODE_BASE
    ips = encode_ips([(offset, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("exact-slot IPS replay failed")
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-slot.ips").write_bytes(ips)

    boundaries = {
        0: [-32768, -1, 0, 39, 40, 41, 144, 145, 32767],
        1: [-32768, -1, 0, 35, 36, 37, 144, 145, 32767],
        3: [-32768, -1, 0, 144, 145, 146, 32767],
        4: [-32768, -1, 0, 144, 145, 146, 32767],
        5: [-32768, -1, 0, 144, 145, 146, 32767],
    }
    cases = []
    for seed in (args.seed, args.seed ^ 0x5A17C3E1):
        index = 0
        for field, values in boundaries.items():
            for value in values:
                cases.append(case_for(field, value, seed, index)); index += 1
        rng = random.Random(seed)
        for _ in range(128):
            case = case_for(0, rng.randint(-32768, 32767), seed, index)
            raw = bytearray(case["context_bytes"])
            for field in (0, 1, 3, 4, 5):
                struct.pack_into("<h", raw, 0x0C + field * 2,
                                 rng.randint(-32768, 32767))
            case["context_bytes"] = bytes(raw)
            cases.append(case); index += 1

    direct_mismatches = []
    for index, case in enumerate(cases):
        ref = direct_result(original, case)
        got = direct_result(staged, case)
        if ref != got:
            direct_mismatches.append({"case": index, "original": ref, "candidate": got})

    # The original caller and reader execute unchanged; only their direct
    # calibration dependency is replaced by the candidate at its real VMA.
    caller_cases = []
    for seed in (args.seed, args.seed ^ 0x5A17C3E1):
        for i, (mode, count, selector, flags, gate) in enumerate([
            (0, 1, 0, (0, 0), 0), (3, 1, 1, (1, 0), 0),
            (255, 1, 2, (1, 1), 1), (0, 0, 3, (0, 1), 1),
            (0, -1, 1, (1, 0), 1), (4, 1, 2, (0, 0), 0),
            (0, 1, 3, (1, 1), 1), (3, 0, 0, (1, 0), 0),
        ]):
            case = reader.make_case(i, mode, count, selector,
                                    flags[0], flags[1], gate, seed)
            ref = reader.run_one(original, case, True)
            got = reader.run_one(staged, case, True)
            caller_cases.append({"seed": seed, "index": i, "equal": ref == got,
                                 "original": ref, "candidate": got})

    control_specs = [
        ("first_minimum_off_by_one", "calibration[0] < 40", "calibration[0] < 39", 0, 39),
        ("second_field_wrong_offset", "calibration[1] = 36", "calibration[2] = 36", 1, 0),
        ("upper_comparator_includes_boundary", "calibration[3] > maximum", "calibration[3] >= maximum", 3, 145),
    ]
    controls = {}
    for name, before, after, field, value in control_specs:
        mutant_body = compile_mutant(args.out, name, before, after)
        mutant_image, _ = stage_image(original, mutant_body)
        case = case_for(field, value, args.seed ^ 0xBADC0DE, 900 + field)
        ref = direct_result(original, case)
        mutant = direct_result(mutant_image, case)
        controls[name] = {"mutation_applied": True, "detected": ref != mutant,
                          "original": ref, "mutant": mutant}

    report = {
        "image_sha256": sha(original), "source_sha256": sha(SOURCE.read_bytes()),
        "candidate_body_sha256": sha(body), "candidate_body_bytes": len(body),
        "original_slot_bytes": SLOT_SIZE, "seed": args.seed,
        "byte_identical": body == original[offset:offset + SLOT_SIZE],
        "direct_cases": len(cases), "direct_mismatches": direct_mismatches,
        "caller_cases": caller_cases, "mutation_controls": controls,
        "ips_replay": apply_ips(original, ips) == staged,
        "only_original_slot_changed": original[:offset] == staged[:offset]
            and original[offset + SLOT_SIZE:] == staged[offset + SLOT_SIZE:],
        "candidate_relocations": [], "entry_arm_even": ADDRESS % 2 == 0,
        "original_reader_callsite": original_callsite,
        "compiler_args": compiler_args,
        "fixture_sha256": sha(json.dumps(cases, sort_keys=True,
                                          separators=(",", ":"),
                                          default=lambda x: x.hex()).encode()),
        "caller_composition_scope": "original 0x001078D8 and 0x0011C5EC; controlled 0x0012A758 seam; only 0x001285C4 staged",
        "limits": ["valid, disjoint ordinary RAM fixtures",
                   "no runtime or physical input provenance claim"]
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"direct_cases": len(cases),
                      "direct_mismatches": len(direct_mismatches),
                      "caller_cases": len(caller_cases),
                      "caller_mismatches": sum(not x["equal"] for x in caller_cases),
                      "body_bytes": len(body), "slot_bytes": SLOT_SIZE,
                      "controls": {k: v["detected"] for k, v in controls.items()},
                      "ips_replay": report["ips_replay"]}, indent=2))
    return 0 if not direct_mismatches and all(x["equal"] for x in caller_cases) \
        and all(x["detected"] for x in controls.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
