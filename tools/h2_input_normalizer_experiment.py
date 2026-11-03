#!/usr/bin/env python3
"""Final-VMA differential for H2 input normalizer dispatcher 0x00128610."""
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
SOURCE = ROOT / "src/engine/leaf_batch29_a.cpp"
CONSUMER = ROOT / "src/engine/leaf_batch30_a.cpp"
ADDRESS = 0x00128610
SLOT_SIZE = 148
CONTEXT = 0x00500000
CALIBRATION = CONTEXT + 0x0C
STOP = reader.STOP
TARGETS = {"ui_func_0013b9fc": 0x0013B9FC,
           "ui_func_0013b8f8": 0x0013B8F8,
           "func_0013bae0": 0x0013BAE0}
SELECTOR_ROUTES = {0: (0x0013B9FC, 0x00, 0x06),
                   1: (0x0013B8F8, 0x02, 0x08),
                   2: (0x0013BAE0, 0x04, 0x0A)}
REGS = [getattr(reader.arm, f"UC_ARM_REG_R{i}") for i in range(13)]
OUT_REG_NAMES = ["r0", "r1", "r2", "r3"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def branch_word(site: int, target: int) -> int:
    delta = target - (site + 8)
    if target & 3 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError(f"invalid ARM call target {site:#x}->{target:#x}")
    return 0xEB000000 | ((delta >> 2) & 0xFFFFFF)


def compile_body(out: Path, source: Path = SOURCE,
                 require_all: bool = True) -> tuple[bytes, list[dict], list[str]]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch29_a.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["func_00128610"]
    if len(body) > SLOT_SIZE:
        raise ValueError(f"production body {len(body)} exceeds original slot {SLOT_SIZE}")
    seen: set[str] = set()
    details = []
    fixed = bytearray(body)
    for reloc in relocations:
        if reloc.relocation_type != 28 or reloc.symbol_name not in TARGETS:
            raise ValueError(f"unexpected call relocation: {reloc}")
        if reloc.symbol_name in seen:
            raise ValueError(f"duplicate relocation for {reloc.symbol_name}")
        seen.add(reloc.symbol_name)
        target = TARGETS[reloc.symbol_name]
        struct.pack_into("<I", fixed, reloc.offset,
                         branch_word(ADDRESS + reloc.offset, target))
        details.append({"offset": reloc.offset, "type": "R_ARM_CALL",
                        "symbol": reloc.symbol_name, "target": hex(target),
                        "entry_bit0": target & 1,
                        "word": hex(struct.unpack_from("<I", fixed, reloc.offset)[0])})
    if require_all and seen != set(TARGETS):
        raise ValueError(f"missing callee relocation(s): {set(TARGETS) - seen}")
    return bytes(fixed), details, list(result.args)


def stage_image(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    if len(body) > SLOT_SIZE or (SLOT_SIZE - len(body)) % 4:
        raise ValueError("body does not fit the original ARM slot")
    payload = body + struct.pack("<I", 0xE320F000) * ((SLOT_SIZE - len(body)) // 4)
    staged = bytearray(original)
    offset = ADDRESS - reader.CODE_BASE
    staged[offset:offset + SLOT_SIZE] = payload
    return bytes(staged), payload


def set_fixture(selector: int, seed: int, index: int, selected: tuple[int, int] | None = None) -> dict:
    case = reader.make_case(index, 0, 1, 0, 0, 0, 1, seed)
    raw = bytearray(case["context_bytes"])
    raw[0x18] = selector & 0xFF
    rng = random.Random((seed & 0xFFFFFFFF) ^ (index * 0x9E3779B1))
    for offset in range(0x0C, 0x18, 2):
        struct.pack_into("<h", raw, offset, rng.randint(-32768, 32767))
    if selected is not None:
        first, second = {0: (0x0C, 0x12), 1: (0x0E, 0x14),
                         2: (0x10, 0x16)}[selector]
        struct.pack_into("<h", raw, first, selected[0])
        struct.pack_into("<h", raw, second, selected[1])
    case["context_bytes"] = bytes(raw)
    # Ensure distinct input halfwords for the direct arguments and caller record.
    out = bytearray(case["output_bytes"])
    struct.pack_into("<hh", out, 0x0C, -12345 + (index % 3), 23456 - (index % 5))
    case["output_bytes"] = bytes(out)
    return case


class TracedMachine(reader.Machine):
    def __init__(self, image: bytes, ring_count: int, record: tuple[int, int, int, int, int]):
        super().__init__(image, ring_count, record)
        self.normalizer_calls: list[dict] = []
        for address in TARGETS.values():
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._normalizer_entry,
                             begin=address, end=address)

    def _normalizer_entry(self, uc, address, _size, _data):
        sp = uc.reg_read(reader.arm.UC_ARM_REG_SP)
        registers = [uc.reg_read(getattr(reader.arm, f"UC_ARM_REG_R{i}"))
                     for i in range(4)]
        stack = struct.unpack("<II", uc.mem_read(sp, 8))
        self.normalizer_calls.append({
            "target": hex(address), "registers": registers,
            "stack_arguments": list(stack), "sp": sp,
            "sp_aligned_8": sp % 8 == 0,
        })


def direct_result(image: bytes, case: dict, sample_x: int, sample_y: int) -> dict:
    machine = TracedMachine(image, case["count"], case["record"])
    machine.setup(case)
    uc = machine.uc
    uc.reg_write(reader.arm.UC_ARM_REG_FPEXC, 0x40000000)
    for i, reg in enumerate(REGS):
        uc.reg_write(reg, (0xD2000000 + i * 0x00010203) & 0xFFFFFFFF)
    uc.reg_write(reader.arm.UC_ARM_REG_R0, CALIBRATION)
    uc.reg_write(reader.arm.UC_ARM_REG_R1, reader.STATE + 0x0C)
    uc.reg_write(reader.arm.UC_ARM_REG_R2, reader.STATE + 0x0E)
    uc.reg_write(reader.arm.UC_ARM_REG_R3, sample_x & 0xFFFFFFFF)
    uc.mem_write(reader.SP, struct.pack("<I", sample_y & 0xFFFFFFFF))
    uc.reg_write(reader.arm.UC_ARM_REG_SP, reader.SP)
    uc.reg_write(reader.arm.UC_ARM_REG_LR, STOP)
    before = [uc.reg_read(reg) for reg in REGS]
    fault = None
    try:
        uc.emu_start(ADDRESS, 0, count=100000)
    except unicorn.UcError as error:
        fault = type(error).__name__ + ": " + str(error)
    after = [uc.reg_read(reg) for reg in REGS]
    return {
        "fault": fault, "registers": after, "registers_before": before,
        "raw_r0": after[0], "callee_saved_registers": after[4:12],
        "callee_saved_preserved": after[4:12] == before[4:12],
        "sp": uc.reg_read(reader.arm.UC_ARM_REG_SP),
        "lr": uc.reg_read(reader.arm.UC_ARM_REG_LR),
        "context": bytes(uc.mem_read(CONTEXT, 0x60)).hex(),
        "output": bytes(uc.mem_read(reader.STATE, 0x20)).hex(),
        "writes": [row for row in machine.writes if
                   CONTEXT <= row[0] < CONTEXT + 0x60 or
                   reader.STATE <= row[0] < reader.STATE + 0x20],
        "normalizer_calls": machine.normalizer_calls,
    }


def comparison_view(result: dict) -> dict:
    # r1-r3/r12/LR are caller-saved or call-site-specific. Compare the raw
    # return, ABI-preserved registers, stack, memory/faults and real callee ABI.
    return {key: result[key] for key in (
        "fault", "raw_r0", "callee_saved_registers",
        "callee_saved_preserved", "sp", "context",
        "output", "writes", "normalizer_calls")}


def check_call_contract(case: dict, result: dict, sample_x: int, sample_y: int) -> bool:
    selector = case["context_bytes"][0x18]
    if selector not in SELECTOR_ROUTES:
        return not result["normalizer_calls"] and result["raw_r0"] == CALIBRATION
    target, first_offset, second_offset = SELECTOR_ROUTES[selector]
    if len(result["normalizer_calls"]) != 1:
        return False
    call = result["normalizer_calls"][0]
    first = struct.unpack_from("<h", case["context_bytes"], 0x0C + first_offset)[0]
    second = struct.unpack_from("<h", case["context_bytes"], 0x0C + second_offset)[0]
    return (int(call["target"], 16) == target
            and call["registers"] == [reader.STATE + 0x0C, reader.STATE + 0x0E,
                                       sample_x & 0xFFFFFFFF, sample_y & 0xFFFFFFFF]
            and call["stack_arguments"] == [first & 0xFFFFFFFF, second & 0xFFFFFFFF]
            and call["sp_aligned_8"])


def compile_mutant(out: Path, name: str, before: str, after: str) -> tuple[bytes, list[dict]]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise ValueError(f"mutation {name} source needle is not unique")
    path = out / "mutants" / f"{name}.cpp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace(before, after), encoding="utf-8")
    body, relocs, _args = compile_body(out / "mutants" / f"{name}-compile", path,
                                       require_all=False)
    return body, relocs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261104)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original code.bin hash mismatch")

    body, relocs, compiler_args = compile_body(args.out / "compile")
    staged, payload = stage_image(original, body)
    offset = ADDRESS - reader.CODE_BASE
    ips = encode_ips([(offset, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("exact-slot IPS replay failed")
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-slot.ips").write_bytes(ips)

    sample_pairs = [(-0x80000000, -0x8000), (-1, -1), (0, 0),
                    (1, 1), (0x7FFFFFFF, 0x7FFF)]
    boundaries = [-32768, -1, 0, 1, 32767]
    cases: list[tuple[dict, int, int]] = []
    for seed in (args.seed, args.seed ^ 0x51A7C3E1):
        index = 0
        for selector in (0, 1, 2):
            for first in boundaries:
                for second in boundaries:
                    sx, sy = sample_pairs[(index + selector) % len(sample_pairs)]
                    cases.append((set_fixture(selector, seed, index, (first, second)), sx, sy))
                    index += 1
        for selector in (3, 127, 128, 255):
            for sx, sy in sample_pairs:
                cases.append((set_fixture(selector, seed, index), sx, sy)); index += 1
        rng = random.Random(seed)
        for _ in range(32):
            selector = rng.choice((0, 1, 2))
            case = set_fixture(selector, seed, index,
                                (rng.randint(-32768, 32767), rng.randint(-32768, 32767)))
            sx, sy = rng.randint(-0x80000000, 0x7FFFFFFF), rng.randint(-0x80000000, 0x7FFFFFFF)
            cases.append((case, sx, sy)); index += 1

    direct_mismatches = []
    call_contract_mismatches = []
    direct_rows = []
    for i, (case, sx, sy) in enumerate(cases):
        ref = direct_result(original, case, sx, sy)
        got = direct_result(staged, case, sx, sy)
        if comparison_view(ref) != comparison_view(got):
            direct_mismatches.append({"case": i, "sample_x": sx, "sample_y": sy,
                                      "original": ref, "candidate": got})
        if not check_call_contract(case, got, sx, sy):
            call_contract_mismatches.append({"case": i, "candidate": got})
        direct_rows.append({"case": i, "selector": case["context_bytes"][0x18],
                            "sample_x": sx, "sample_y": sy,
                            "normalizer_calls": got["normalizer_calls"],
                            "equal": comparison_view(ref) == comparison_view(got)})

    caller_cases = []
    for seed in (args.seed, args.seed ^ 0x51A7C3E1):
        for i, (selector, count) in enumerate(((0, 1), (1, 1), (2, 1), (3, 1), (0, 0), (2, -1))):
            case = reader.make_case(i, 0, count, selector, 0, 0, 1, seed)
            ref = reader.run_one(original, case, True)
            got = reader.run_one(staged, case, True)
            caller_cases.append({"seed": seed, "index": i, "selector": selector,
                                 "count": count, "equal": ref == got,
                                 "original": ref, "candidate": got})

    controls_spec = [
        ("selector_zero_wrong_callee", "return ui_func_0013b9fc(output_x, output_y, sample_x_in_r2, sample_y_in_r3,",
         "return ui_func_0013b8f8(output_x, output_y, sample_x_in_r2, sample_y_in_r3,", 0, (-1234, 5678)),
        ("calibration_sign_extension", "calibration[0], calibration[3]",
         "static_cast<u16>(calibration[0]), calibration[3]", 0, (-1, -145)),
        ("reversed_output_pointers", "return ui_func_0013b9fc(output_x, output_y,",
         "return ui_func_0013b9fc(output_y, output_x,", 0, (-2345, 3456)),
        ("dropped_fifth_input_argument", "sample_x_in_r2, sample_y_in_r3,\n                                calibration[0]",
         "sample_x_in_r2, 0,\n                                calibration[0]", 0, (-32768, 32767)),
    ]
    controls = {}
    for i, (name, before, after, selector, pair) in enumerate(controls_spec):
        mutant_body, _mutant_relocs = compile_mutant(args.out, name, before, after)
        mutant_image, _ = stage_image(original, mutant_body)
        case = set_fixture(selector, args.seed ^ 0xBADCAFE, 800 + i, pair)
        ref = direct_result(original, case, -123456789, 0x7FFFFFFF)
        mutant = direct_result(mutant_image, case, -123456789, 0x7FFFFFFF)
        controls[name] = {"mutation_applied": True,
                          "detected": comparison_view(ref) != comparison_view(mutant),
                          "original": ref, "mutant": mutant}

    callsite = struct.unpack_from("<I", original, 0x0011C668 - reader.CODE_BASE)[0]
    if callsite & 0xFF000000 != 0xEB000000:
        raise ValueError(f"expected original wrapper ARM BL, got {callsite:#010x}")
    delta = callsite & 0x00FFFFFF
    if delta & 0x00800000: delta -= 0x01000000
    call_target = 0x0011C668 + 8 + (delta << 2)
    if call_target != ADDRESS or call_target & 1:
        raise ValueError(f"wrapper call resolves to unexpected/non-ARM target {call_target:#x}")

    report = {
        "image_sha256": sha(original), "source_sha256": sha(SOURCE.read_bytes()),
        "consumer_sha256": sha(CONSUMER.read_bytes()),
        "candidate_body_sha256": sha(body), "candidate_body_bytes": len(body),
        "original_slot_bytes": SLOT_SIZE, "byte_identical": body == original[offset:offset + SLOT_SIZE],
        "seed": args.seed, "direct_cases": len(cases),
        "direct_mismatches": direct_mismatches,
        "call_contract_mismatches": call_contract_mismatches,
        "direct_case_summary": direct_rows,
        "caller_cases": caller_cases, "mutation_controls": controls,
        "relocations": relocs, "all_relocations_even_arm": all(x["entry_bit0"] == 0 for x in relocs),
        "caller_callsite": {"address": hex(0x0011C668), "word": hex(callsite),
                             "target": hex(call_target), "bit0": call_target & 1},
        "ips_replay": apply_ips(original, ips) == staged,
        "only_original_slot_changed": original[:offset] == staged[:offset]
            and original[offset + SLOT_SIZE:] == staged[offset + SLOT_SIZE:],
        "compiler_args": compiler_args,
        "fixture_sha256": sha(json.dumps(cases, sort_keys=True, separators=(",", ":"),
                                          default=lambda x: x.hex()).encode()),
        "caller_scope": "original 0x001078D8 and 0x0011C5EC with only 0x00128610 staged; controlled 0x0012A758 seam; all three normalization callees execute pinned original ARM",
        "limits": ["valid disjoint mapped ordinary RAM fixtures",
                   "original normalizer callees retained; their semantics are not reconstructed",
                   "no physical input provenance or runtime cadence claim"]
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"direct_cases": len(cases), "direct_mismatches": len(direct_mismatches),
                      "call_contract_mismatches": len(call_contract_mismatches),
                      "caller_cases": len(caller_cases),
                      "caller_mismatches": sum(not x["equal"] for x in caller_cases),
                      "body_bytes": len(body), "slot_bytes": SLOT_SIZE,
                      "controls": {k: v["detected"] for k, v in controls.items()},
                      "relocations": relocs, "ips_replay": report["ips_replay"]}, indent=2))
    return 0 if not direct_mismatches and not call_contract_mismatches \
        and all(x["equal"] for x in caller_cases) \
        and all(x["detected"] for x in controls.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
