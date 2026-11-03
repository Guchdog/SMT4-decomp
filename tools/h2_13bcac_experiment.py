#!/usr/bin/env python3
"""Offline final-VMA differential for the H2 input postprocessor 0x0013BCAC."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools import h2_11c5ec_experiment as reader

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch16_c.cpp"
ADDRESS = 0x0013BCAC
SPAN = 212
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000
DATA_BASE = 0x00500000
DATA_SIZE = 0x00040000
STACK = 0x08000000
STACK_SIZE = 0x10000
SP = STACK + 0x8000
STOP = STACK + 0x9000
RECORD = DATA_BASE + 0x1000
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
NOP = struct.pack("<I", 0xE320F000)
SAVED = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4, 12)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE) -> tuple[bytes, Path]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch16_c.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["func_0013bcac"]
    if relocations:
        raise AssertionError(f"postprocessor unexpectedly has relocations: {relocations}")
    return body, obj


def stage(image: bytes, body: bytes) -> tuple[bytes, bytes, bytes]:
    if len(body) > SPAN or (SPAN - len(body)) % 4:
        raise AssertionError(f"body size {len(body)} does not fit {SPAN}-byte ARM slot")
    payload = body + NOP * ((SPAN - len(body)) // 4)
    offset = ADDRESS - CODE_BASE
    staged = bytearray(image)
    staged[offset:offset + SPAN] = payload
    ips = encode_ips([(offset, payload)], len(image))
    if apply_ips(image, ips) != bytes(staged):
        raise AssertionError("slot IPS replay did not reproduce the staged image")
    changed = [i for i, (a, b) in enumerate(zip(image, staged)) if a != b]
    if changed and (min(changed) < offset or max(changed) >= offset + SPAN):
        raise AssertionError("staged image differs outside the 0x0013BCAC slot")
    return bytes(staged), payload, ips


def invoke(image: bytes, words: tuple[int, int, int]) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM,
                    unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_write(RECORD, struct.pack("<III", *(x & 0xFFFFFFFF for x in words)))
    writes: list[tuple[int, int, int]] = []
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,
                lambda _uc, _access, addr, size, value, _data:
                writes.append((addr, size, value & 0xFFFFFFFF)))
    uc.hook_add(unicorn.UC_HOOK_CODE,
                lambda machine, address, _size, _data:
                machine.emu_stop() if address == STOP else None,
                begin=STOP, end=STOP)
    uc.reg_write(arm.UC_ARM_REG_R0, RECORD)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(SAVED):
        uc.reg_write(reg, 0xC1000000 + i * 0x01010101)
    before = [uc.reg_read(reg) for reg in SAVED]
    fault = None
    try:
        uc.emu_start(ADDRESS, 0, count=2000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {
        "fault": fault,
        "r0": uc.reg_read(arm.UC_ARM_REG_R0),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "callee_saved": [uc.reg_read(reg) for reg in SAVED] == before,
        "record": bytes(uc.mem_read(RECORD, 12)).hex(),
        "writes": [row for row in writes if not STACK <= row[0] < STACK + STACK_SIZE],
    }


def direct_cases(seed: int) -> list[tuple[str, tuple[int, int, int]]]:
    rows = []
    patterns = (0, 4, 8, 12)
    for a in patterns:
        for b in patterns:
            for c in patterns:
                rows.append((f"bit-matrix-{a:02x}-{b:02x}-{c:02x}",
                             (0xA5310000 | a, 0x13570000 | b, 0xC0DE0000 | c)))
    rng = random.Random(seed)
    for i in range(128):
        rows.append((f"random-{i}", tuple(rng.getrandbits(32) for _ in range(3))))
    return rows


def parent_case(image: bytes, case: dict, seed: int) -> tuple[dict, dict]:
    machine = reader.Machine(image, case["count"], case["record"])
    machine.setup(case)
    hook_state: dict = {"hits": 0, "context_snapshot": None, "record_before": None}

    def on_postprocess(uc, _address, _size, _data):
        hook_state["hits"] += 1
        hook_state["context_snapshot"] = struct.unpack(
            "<I", uc.mem_read(case["context"] + 8, 4))[0]
        hook_state["record_before"] = struct.unpack(
            "<I", uc.mem_read(reader.STATE, 4))[0]

    machine.uc.hook_add(unicorn.UC_HOOK_CODE, on_postprocess,
                        begin=ADDRESS, end=ADDRESS)
    result = machine.invoke(reader.ADDRESS, case["context"], False)
    expected_hits = 1 if case["post_gate"] == 0 and case["count"] > 0 and case["mode"] != 4 else 0
    if hook_state["hits"] != expected_hits:
        raise AssertionError(f"optional postprocessor hit count {hook_state['hits']} != {expected_hits}")
    if hook_state["hits"] and hook_state["context_snapshot"] != hook_state["record_before"]:
        raise AssertionError("parent did not save output word +0 to context+8 before postprocessing")
    return result, hook_state


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261207)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)

    image = IMAGE_PATH.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise AssertionError("pinned original image hash mismatch")
    body, obj = compile_body(args.out / "compile")
    staged, payload, ips = stage(image, body)
    (args.out / "production.o").write_bytes(obj.read_bytes())
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-slot.ips").write_bytes(ips)

    caller_site = 0x0011C6FC
    caller_word = struct.unpack_from("<I", image, caller_site - CODE_BASE)[0]
    caller_imm = caller_word & 0x00FFFFFF
    if caller_imm & 0x00800000:
        caller_imm -= 0x01000000
    caller_target = caller_site + 8 + (caller_imm << 2)
    if caller_word & 0xFF000000 != 0x0B000000 or caller_target != ADDRESS or ADDRESS & 1:
        raise AssertionError(f"optional reader call is not conditional ARM BL to target: {caller_word:#x}->{caller_target:#x}")

    direct = []
    for name, words in direct_cases(args.seed):
        original = invoke(image, words)
        candidate = invoke(staged, words)
        direct.append({"name": name, "equal": original == candidate,
                       "original": original, "candidate": candidate})
    failures = [row for row in direct if not row["equal"]]
    if failures:
        raise AssertionError(f"direct differential mismatch: {failures[0]}")

    composition = []
    composition_results = []
    rng = random.Random(args.seed ^ 0x13BCAC)
    for i in range(32):
        case = reader.make_case(i, 0, 1, 3, 0, 0, 0 if i % 2 == 0 else 1,
                                rng.getrandbits(32))
        original, original_hook = parent_case(image, case, args.seed)
        candidate, candidate_hook = parent_case(staged, case, args.seed)
        composition_results.append({"case": i, "post_gate": case["post_gate"],
                                   "equal": original == candidate and original_hook == candidate_hook,
                                   "postprocess_hits": original_hook["hits"],
                                   "saved_before_call": original_hook["context_snapshot"] == original_hook["record_before"]
                                   if original_hook["hits"] else None})
        if original != candidate or original_hook != candidate_hook:
            composition.append({"case": i, "equal": False, "original": original,
                                "candidate": candidate, "original_hook": original_hook,
                                "candidate_hook": candidate_hook})
    if composition:
        raise AssertionError(f"original 0x0011C5EC composition mismatch: {composition[0]}")

    source_text = SOURCE.read_text(encoding="utf-8")
    needle = "const u32 set_bit8 = ((current4 & current8) |"
    if source_text.count(needle) != 1:
        raise AssertionError("mutation source needle is not unique")
    mutant_source = args.out / "mutant.cpp"
    mutant_source.write_text(source_text.replace(needle,
        "const u32 set_bit8 = ((current8) |", 1), encoding="utf-8")
    mutant_body, _mutant_obj = compile_body(args.out / "mutant-compile", mutant_source)
    mutant_image, _mutant_payload, _mutant_ips = stage(image, mutant_body)
    controls = 0
    control_case = None
    for name, words in direct_cases(args.seed):
        if invoke(image, words) != invoke(mutant_image, words):
            controls += 1
            control_case = name
            break
    if controls != 1:
        raise AssertionError("bit transition mutation was not detected")

    report = {
        "status": "passed",
        "target": hex(ADDRESS),
        "reference_sha256": sha(image),
        "production_source_sha256": sha(SOURCE.read_bytes()),
        "production_object_sha256": sha(obj.read_bytes()),
        "production_body_sha256": sha(body),
        "production_body_size": len(body),
        "slot_size": SPAN,
        "relocations": [],
        "caller_site": hex(caller_site),
        "caller_word": hex(caller_word),
        "caller_target": hex(caller_target),
        "seed": args.seed,
        "direct_case_count": len(direct),
        "direct_differences": 0,
        "direct_cases": direct,
        "parent_composition_case_count": 32,
        "parent_composition_differences": 0,
        "parent_composition_cases": composition_results,
        "parent_composition": "original 0x0011C5EC; controlled 0x0012A758 ring seam; optional 0x0013BCAC called in half the cases",
        "save_before_postprocess_assertion": True,
        "negative_control": {"mutation": "omit current bit4-and-bit8 conjunction", "detected": True, "first_case": control_case},
        "ips_roundtrip": apply_ips(image, ips) == staged,
        "ips_sha256": sha(ips),
        "staged_image_sha256": sha(staged),
        "domain": "aligned three-word ordinary mapped RAM records; ABI save/restore writes in callee stack scratch are excluded from the memory trace; concurrent observers, MMIO, invalid mappings and runtime input provenance are outside scope",
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS direct={len(direct)} parent=32/32 mutation=detected body={len(body)}/{SPAN} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
