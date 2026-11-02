#!/usr/bin/env python3
"""Pinned ARM differential for the H2 manager-table selector."""
from __future__ import annotations

import hashlib
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

IMAGE = (ROOT / "extracted/exefs/code.bin").read_bytes()
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch39_a.cpp"
CALLER_SOURCE = ROOT / "src/engine/leaf_batch32_c.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-ui-helper-002b0188-manager-resolver-convert/run001"
FUNCTION = 0x002B0188
SPAN = 24
TAIL = 0x00138B90
CANDIDATE = 0x00800000
STOP = 0x0080F000
TEXT = 0x00100000
TABLE_PTR = 0x0044EA28
TABLE = 0x00900000
MANAGER_A = 0x00901000
MANAGER_B = 0x00902000
STACK = 0x00A0FF00


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_function(function: str, name: str, entry: int):
    OUT.mkdir(parents=True, exist_ok=True)
    obj = OUT / name
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)[function]
    fixed = bytearray(body)
    resolved = []
    expected = {"func_00138b90": TAIL}
    for rel in relocs:
        if rel.relocation_type not in (28, 29) or rel.symbol_name not in expected or rel.explicit_addend is not None:
            raise AssertionError(f"unsupported relocation: {rel}")
        place = entry + rel.offset
        ins = struct.unpack_from("<I", fixed, rel.offset)[0]
        if ins & 0x0F000000 not in (0x0A000000,):
            raise AssertionError(f"expected ARM B/BL at {rel.offset:#x}, got {ins:#010x}")
        delta = TAIL - (place + 8)
        struct.pack_into("<I", fixed, rel.offset, (ins & 0xFF000000) | ((delta >> 2) & 0xFFFFFF))
        resolved.append({"offset": rel.offset, "target": hex(TAIL), "type": rel.relocation_type,
                         "link": bool(ins & 0x01000000)})
    if len(fixed) > SPAN or len(fixed) % 4:
        raise AssertionError(f"body {len(fixed)} exceeds slot {SPAN}")
    if len(relocs) != 1:
        raise AssertionError(f"expected one tail relocation, got {relocs}")
    return bytes(fixed), resolved


def setup(candidate_body=None, candidate_entry=CANDIDATE):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(TEXT, 0x00500000)
    uc.mem_write(TEXT, IMAGE)
    uc.mem_map(0x00800000, 0x10000)
    uc.mem_map(0x00900000, 0x10000)
    uc.mem_map(0x00A00000, 0x10000)
    uc.mem_write(TABLE_PTR, struct.pack("<I", TABLE))
    if candidate_body is not None:
        uc.mem_write(candidate_entry, candidate_body)
    state = {"done": False, "writes": [], "tail_args": [], "events": []}

    def on_code(machine, address, _size, _data):
        if address == TAIL:
            state["tail_args"].append((machine.reg_read(UC_ARM_REG_R0), machine.reg_read(UC_ARM_REG_R1)))
            state["events"].append("tail")
        elif address == STOP:
            state["done"] = True
            machine.emu_stop()

    def on_write(_machine, _kind, address, size, value, _data):
        state["writes"].append((address, size, value & 0xFFFFFFFF))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    uc._state = state
    return uc


def execute(uc, entry: int, group: int, index: int, null_entry=False):
    state = uc._state
    state.update(done=False, writes=[], tail_args=[], events=[])
    manager = MANAGER_A if group & 1 == 0 else MANAGER_B
    base = 0x00905000 if group & 1 == 0 else 0x00906000
    uc.mem_write(TABLE + group * 24, struct.pack("<I", 0 if null_entry else manager))
    uc.mem_write(manager, struct.pack("<I", base))
    before = {reg: (0x11110000 + i * 0x01010101) & 0xFFFFFFFF for i, reg in enumerate(
        (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11))}
    uc.reg_write(UC_ARM_REG_SP, STACK)
    uc.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in before.items():
        uc.reg_write(reg, value)
    uc.reg_write(UC_ARM_REG_R0, group)
    uc.reg_write(UC_ARM_REG_R1, index & 0xFFFFFFFF)
    try:
        uc.emu_start(entry, 0, count=100)
        fault = None
    except (UcError, OSError) as exc:
        fault = str(exc)
    signed = index if index < 0x80000000 else index - 0x100000000
    quotient = abs(signed) // 1000 * (-1 if signed < 0 else 1)
    expected = 0 if null_entry else (base + quotient * 32) & 0xFFFFFFFF
    observed = {
        "return": uc.reg_read(UC_ARM_REG_R0), "expected": expected,
        "callee_saved": all(uc.reg_read(reg) == value for reg, value in before.items()),
        "sp": uc.reg_read(UC_ARM_REG_SP) == STACK,
        "tail_args": tuple(state["tail_args"]), "writes": tuple(state["writes"]),
        "done": state["done"], "fault": fault,
    }
    if not observed["done"] or fault or observed["return"] != expected or not observed["callee_saved"] or not observed["sp"]:
        raise AssertionError(f"execution/ABI failure group={group} index={signed}: {observed}")
    if observed["writes"]:
        raise AssertionError(f"unexpected memory writes: {observed['writes']}")
    expected_tail = ((0 if null_entry else manager, index & 0xFFFFFFFF),)
    if observed["tail_args"] != expected_tail:
        raise AssertionError(f"tail arguments differ: {observed['tail_args']}")
    return observed


def mutate(source_text: str, label: str, old: str, new: str, group: int, index: int):
    if source_text.count(old) != 1:
        raise AssertionError(f"mutant anchor not unique: {label}")
    path = OUT / f"mutant-{label}.cpp"
    path.write_text(source_text.replace(old, new, 1), encoding="utf-8")
    obj = OUT / f"mutant-{label}.o"
    result = compile_tu_armv6k(path, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)["ui_func_002b0188"]
    fixed = bytearray(body)
    for rel in relocs:
        if rel.relocation_type not in (28, 29) or rel.symbol_name != "func_00138b90":
            raise AssertionError(f"unsupported mutant relocation {rel}")
        ins = struct.unpack_from("<I", fixed, rel.offset)[0]
        struct.pack_into("<I", fixed, rel.offset, (ins & 0xFF000000) | (((TAIL - (CANDIDATE + rel.offset + 8)) >> 2) & 0xFFFFFF))
    profile = setup(bytes(fixed))
    try:
        execute(profile, CANDIDATE, group, index)
    except AssertionError:
        return True
    return False


def run():
    temp, temp_relocs = compile_function("ui_func_002b0188", "candidate-temp.o", CANDIDATE)
    final, final_relocs = compile_function("ui_func_002b0188", "candidate-final.o", FUNCTION)
    original, temporary, integrated = setup(), setup(temp), setup(final, FUNCTION)
    directed = [0, 1, 999, 1000, 1001, 1999, 2000, 2001,
                -1, -999, -1000, -1001, -1999, -2000, -2001,
                0x7FFFFFFF, 0x80000000, 0x800003E8, 0xFFFFFFFF]
    cases = [(g, n, False) for g in (0, 1, 2, 3, 7, 19, 31) for n in directed]
    cases += [(g, 1234, True) for g in range(32)]
    rng = random.Random(0x2B0188)
    cases += [(rng.randrange(32), rng.getrandbits(32), False) for _ in range(96)]
    for i, (group, index, null_entry) in enumerate(cases):
        ref = execute(original, FUNCTION, group, index, null_entry)
        cand = execute(temporary, CANDIDATE, group, index, null_entry)
        final_result = execute(integrated, FUNCTION, group, index, null_entry)
        if ref != cand or ref != final_result:
            raise AssertionError(f"case {i} differs: {ref} / {cand} / {final_result}")
    source_text = SOURCE.read_text(encoding="utf-8")
    controls = [
        {"name": "group-stride", "detected": mutate(source_text, "stride", "group * 24u", "group * 20u", 2, 1001)},
        {"name": "forwarded-index", "detected": mutate(source_text, "index", "manager_entry)), node_index", "manager_entry)), group", 3, 1001)},
    ]
    if not all(c["detected"] for c in controls):
        raise AssertionError(f"negative control missed: {controls}")
    return {"cases": len(cases), "directed_indices": directed, "groups": [0, 1, 2, 3, 7, 19, 31],
            "null_entries": 32, "seeded_cases": 96, "negative_controls": controls,
            "tail_behavior": "original 0x00138B90 executes; signed truncating quotient /1000, stride 32",
            "caller_composition": "see h2_b88c4_experiment.py; original 0x002BF6D0 forwards both registers"}, temp, final, temp_relocs, final_relocs


def main():
    if sha(IMAGE) != IMAGE_SHA:
        raise SystemExit("pinned image hash mismatch")
    evidence, temp, final, temp_relocs, final_relocs = run()
    report = {"function": "ui_func_002b0188", "address": hex(FUNCTION),
              "reference_image_sha256": sha(IMAGE), "source_sha256": sha(SOURCE.read_bytes()),
              "body_sha256": sha(temp), "body_size": len(temp),
              "final_body_sha256": sha(final), "final_body_size": len(final),
              "temporary_byte_identical": temp == IMAGE[FUNCTION - TEXT:FUNCTION - TEXT + SPAN],
              "final_byte_identical": final == IMAGE[FUNCTION - TEXT:FUNCTION - TEXT + SPAN],
              "relocations": temp_relocs, "final_relocations": final_relocs,
              "evidence": evidence, "runtime": "not_run; offline pinned-ARM only"}
    path = OUT / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"report: {path}")


if __name__ == "__main__":
    main()
