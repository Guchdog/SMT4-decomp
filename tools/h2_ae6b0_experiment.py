#!/usr/bin/env python3
"""Exhaustive pinned-ARM differential for AsdText_IsControlCode."""
from __future__ import annotations

import hashlib
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools import h2_2b787c_experiment as line_count

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
IMAGE = IMAGE_PATH.read_bytes()
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_matching.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-ae6b0-convert/run001"
ENTRY = 0x002AE6B0
SPAN = 24
CANDIDATE_ENTRY = 0x00800000
STOP = 0x0080F000
TEXT = 0x00100000
STACK = 0x00A0FF00


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_candidate(source: Path = SOURCE, output_name: str = "leaf_matching.o") -> bytes:
    OUT.mkdir(parents=True, exist_ok=True)
    obj = OUT / output_name
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)["engine_func_002ae6b0"]
    if relocs:
        raise AssertionError(f"unexpected helper relocations: {relocs}")
    if len(body) > SPAN:
        raise AssertionError(f"candidate exceeds original slot: {len(body)}/{SPAN}")
    return body


def reference_body() -> bytes:
    offset = ENTRY - 0x00100000
    return IMAGE[offset:offset + SPAN]


def setup(body: bytes) -> Uc:
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(TEXT, 0x00500000)
    u.mem_write(TEXT, IMAGE)
    u.mem_map(0x00800000, 0x00010000)
    u.mem_map(0x00A00000, 0x00010000)
    u.mem_write(CANDIDATE_ENTRY, body)
    u.hook_add(UC_HOOK_CODE, lambda uc, address, _size, _data:
               uc.emu_stop() if address == STOP else None)
    return u


def execute(u: Uc, entry: int, code: int, seed: int) -> dict:
    rng = random.Random(seed)
    before = {reg: rng.getrandbits(32) for reg in
              (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
               UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
               UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)}
    writes: list[tuple[int, int, int]] = []
    hook = u.hook_add(UC_HOOK_MEM_WRITE,
                      lambda _uc, _kind, address, size, value, _data:
                      writes.append((address, size, value & 0xFFFFFFFF)))
    u.reg_write(UC_ARM_REG_SP, STACK)
    sp = u.reg_read(UC_ARM_REG_SP)
    u.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in before.items():
        u.reg_write(reg, value)
    u.reg_write(UC_ARM_REG_R0, code)
    u.emu_start(entry, 0, count=16)
    actual = {reg: u.reg_read(reg) for reg in before}
    callee_saved = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
    state = {"result": u.reg_read(UC_ARM_REG_R0),
             "preserved": all(actual[reg] == before[reg] for reg in callee_saved),
             "sp_preserved": u.reg_read(UC_ARM_REG_SP) == sp,
             "writes": tuple(writes)}
    u.hook_del(hook)
    return state


def direct_differential(body: bytes) -> dict:
    original, candidate = setup(body), setup(body)
    values = set(range(0x10000))
    values.update((0, 1, 0xF800, 0xF801, 0xF802, 0xF88E, 0xF88F,
                   0xF890, 0xFFFF, 0x10000, 0x10001, 0x10000000,
                   0x7FFFFFFF, 0x80000000, 0xFFFFF800, 0xFFFFF801,
                   0xFFFFFFFE, 0xFFFFFFFF))
    rng = random.Random(20261102)
    values.update(rng.getrandbits(32) for _ in range(512))
    for index, value in enumerate(sorted(values)):
        ref = execute(original, ENTRY, value, index ^ 0x5AE6B0)
        got = execute(candidate, CANDIDATE_ENTRY, value, index ^ 0x5AE6B0)
        if ref != got:
            raise AssertionError(f"direct mismatch for {value:#010x}: ref={ref}, got={got}")
        expected = int(0xF801 <= value <= 0xF88F)
        if ref["result"] != expected or not ref["preserved"] or not ref["sp_preserved"] or ref["writes"]:
            raise AssertionError(f"contract mismatch at {value:#010x}: {ref}, expected={expected}")
    return {"cases": len(values), "halfword_domain": 65536,
            "directed_u32": 18, "random_u32": 512,
            "result_rule": "1 iff unsigned code in [0xF801, 0xF88F], else 0",
            "abi": "r4-r11 and SP preserved; no guest memory writes"}


def negative_controls(good_body: bytes) -> dict:
    source = SOURCE.read_text(encoding="utf-8")
    control = {}
    for name, old, new, value in (
        ("upper-bound", "< 0x8fu", "< 0x90u", 0xF890),
        ("lower-bound", "code - 0xf801u", "code - 0xf800u", 0xF800),
    ):
        if source.count(old) != 1:
            raise AssertionError(f"mutation anchor not unique: {name}")
        mutant_source = OUT / f"mutant-{name}.cpp"
        mutant_source.write_text(source.replace(old, new, 1), encoding="utf-8")
        mutant = compile_candidate(mutant_source, f"mutant-{name}.o")
        if mutant == good_body:
            raise AssertionError(f"mutation did not affect helper bytes: {name}")
        reference = execute(setup(good_body), ENTRY, value, 0xAE6B0)
        changed = execute(setup(mutant), CANDIDATE_ENTRY, value, 0xAE6B0)
        if reference == changed:
            raise AssertionError(f"negative control escaped detection: {name}")
        control[name] = {"input": hex(value), "reference": reference["result"],
                         "mutant": changed["result"], "detected": True}
    return control


def caller_composition(body: bytes) -> dict:
    image = bytearray(IMAGE)
    offset = ENTRY - 0x00100000
    image[offset:offset + SPAN] = body
    checks = []
    for selector in (11, 19):
        original = line_count.run_parent_composition(selector, None, image=IMAGE)
        converted = line_count.run_parent_composition(selector, None, image=bytes(image))
        if original != converted:
            raise AssertionError(f"0x00286928 selector-{selector} changed: original={original}, converted={converted}")
        checks.append({"selector": selector, "done": converted["done"],
                       "helper_events": [e for e in converted["events"] if e[0] == "line-count-entry"],
                       "object_20": converted["object_20"]})
    return {"cases": checks, "path": "0x00286928 -> 0x002B787C -> converted 0x002AE6B0"}


def main() -> int:
    if sha(IMAGE) != IMAGE_SHA:
        raise SystemExit("pinned original code.bin hash mismatch")
    body = compile_candidate()
    direct = direct_differential(body)
    composition = caller_composition(body)
    controls = negative_controls(body)
    report = {"function": "AsdText_IsControlCode", "address": hex(ENTRY),
              "reference_image_sha256": sha(IMAGE), "source_sha256": sha(SOURCE.read_bytes()),
              "candidate_sha256": sha(body), "candidate_hex": body.hex(),
              "candidate_matches_original_bytes": body == reference_body(),
              "direct": direct, "caller_composition": composition,
              "negative_controls": controls,
              "runtime": "not_run; helper-only behavior verified offline; no new runtime claim"}
    path = OUT / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"report: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
