#!/usr/bin/env python3
"""Pinned offline differential for the H2 typed resource table resolver."""
from __future__ import annotations

import hashlib
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools import h2_2a63f8_experiment as predicate

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch39_a.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-resource-resolver-002b96f0/run001"
FUNCTION = 0x002B96F0
TAIL = 0x00145798
SPAN = 24
TEXT = 0x00100000
CANDIDATE = 0x00800000
STOP = 0x0080F000
TABLE_PTR = 0x0044EA28
TABLE = 0x00900000
MANAGER_BASE = 0x00910000
STACK = 0x00A0FF00
MASK = 0xFFFFFFFF


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_candidate(name: str, entry: int, source: Path = SOURCE):
    OUT.mkdir(parents=True, exist_ok=True)
    obj = OUT / name
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocations = extract_elf_functions_detailed(obj)["engine_func_002b96f0"]
    fixed = bytearray(body)
    resolved = []
    for relocation in relocations:
        if (relocation.relocation_type != 29 or relocation.symbol_name != ""
                or relocation.explicit_addend is not None):
            raise AssertionError(f"unsupported tail relocation: {relocation}")
        instruction = struct.unpack_from("<I", fixed, relocation.offset)[0]
        if instruction & 0x0F000000 != 0x0A000000 or instruction & 0x01000000:
            raise AssertionError(f"expected ARM B relocation at {relocation.offset:#x}: {instruction:#010x}")
        place = entry + relocation.offset
        delta = TAIL - (place + 8)
        struct.pack_into("<I", fixed, relocation.offset,
                         (instruction & 0xFF000000) | ((delta >> 2) & 0x00FFFFFF))
        resolved.append({"offset": relocation.offset, "type": relocation.relocation_type,
                         "target": hex(TAIL), "instruction": "ARM B, LR preserved"})
    if len(fixed) > SPAN or len(fixed) % 4 or len(relocations) != 1:
        raise AssertionError(f"candidate layout invalid: {len(fixed)} bytes / {relocations}")
    return bytes(fixed), resolved


def setup(candidate: bytes | None = None, candidate_entry: int = CANDIDATE):
    image = IMAGE_PATH.read_bytes()
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(TEXT, (len(image) + 0xFFF) & ~0xFFF)
    uc.mem_write(TEXT, image)
    uc.mem_map(0x00800000, 0x10000)
    uc.mem_map(0x00900000, 0x30000)
    uc.mem_map(0x00A00000, 0x10000)
    uc.mem_write(TABLE_PTR, struct.pack("<I", TABLE))
    if candidate is not None:
        uc.mem_write(candidate_entry, candidate)
    state = {"done": False, "reads": [], "writes": [], "last_pc": None}

    def on_code(machine, address, _size, _data):
        state["last_pc"] = address
        if address == STOP:
            state["done"] = True
            machine.emu_stop()

    def on_read(machine, _kind, address, size, _value, _data):
        state["reads"].append((address, size, bytes(machine.mem_read(address, size))))

    def on_write(_machine, _kind, address, size, value, _data):
        state["writes"].append((address, size, value & MASK))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_MEM_READ, on_read)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    uc._state = state
    return uc


def execute(uc, entry: int, group: int, subindex: int, base: int, null_entry: bool = False):
    state = uc._state
    state.update(done=False, reads=[], writes=[], last_pc=None)
    manager = MANAGER_BASE + (group & 0x7F) * 0x40
    uc.mem_write(TABLE + group * 24, struct.pack("<I", 0 if null_entry else manager))
    uc.mem_write(manager, struct.pack("<I", base & MASK))
    saved = {reg: 0x11110000 + index * 0x01010101 for index, reg in enumerate(
        (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11))}
    uc.reg_write(UC_ARM_REG_SP, STACK)
    uc.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in saved.items():
        uc.reg_write(reg, value)
    uc.reg_write(UC_ARM_REG_R0, group & MASK)
    uc.reg_write(UC_ARM_REG_R1, subindex & MASK)
    fault = None
    try:
        uc.emu_start(entry, 0, count=100)
    except (UcError, OSError) as exc:
        fault = str(exc)
    expected = 0 if null_entry else (base + ((subindex & MASK) << 5)) & MASK
    observed = {
        "return": uc.reg_read(UC_ARM_REG_R0), "expected": expected,
        "r1_preserved": uc.reg_read(UC_ARM_REG_R1) == (subindex & MASK),
        "callee_saved": all(uc.reg_read(reg) == value for reg, value in saved.items()),
        "sp": uc.reg_read(UC_ARM_REG_SP) == STACK,
        "reads": tuple(state["reads"]), "writes": tuple(state["writes"]),
        "done": state["done"], "fault": fault,
    }
    if (fault or not observed["done"] or observed["return"] != expected
            or not observed["r1_preserved"] or not observed["callee_saved"] or not observed["sp"]
            or observed["writes"]):
        raise AssertionError(f"resolver behavior/ABI mismatch group={group:#x} index={subindex:#x}: {observed}")
    return observed


def comparable(result, entry):
    normalized_reads = []
    for address, size, value in result["reads"]:
        if entry <= address < entry + SPAN:
            location = ("function-literal", address - entry)
        else:
            location = address
        normalized_reads.append((location, size, value))
    return {**{key: value for key, value in result.items() if key not in ("expected", "reads")},
            "reads": tuple(normalized_reads)}


def mutation_detected(label: str, old: str, new: str, group: int, subindex: int, base: int) -> bool:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise AssertionError(f"non-unique mutation anchor: {label}")
    mutant = OUT / f"mutant-{label}.cpp"
    mutant.write_text(text.replace(old, new, 1), encoding="utf-8")
    try:
        body, _ = compile_candidate(f"mutant-{label}.o", CANDIDATE, mutant)
    except AssertionError as error:
        if "candidate layout invalid" in str(error):
            return True
        raise
    machine = setup(body)
    try:
        execute(machine, CANDIDATE, group, subindex, base)
    except AssertionError:
        return True
    return False


def main():
    image = IMAGE_PATH.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise SystemExit("pinned code.bin hash mismatch")
    temporary, temp_relocs = compile_candidate("candidate-temp.o", CANDIDATE)
    final, final_relocs = compile_candidate("candidate-final.o", FUNCTION)
    original_machine, temp_machine, final_machine = setup(), setup(temporary), setup(final, FUNCTION)
    original_body = image[FUNCTION - TEXT:FUNCTION - TEXT + SPAN]
    cases = [
        (0, 0, 0x12345000, False), (1, 1, 0, False), (0x2F, 0, 0x00928000, False),
        (7, 3, 0xFFFFFFE0, False), (31, MASK, 0x80000000, False),
        (0x2F, 0, 0x12345678, True), (2, 0x80000000, 0xFFFFFFF0, False),
    ]
    rng = random.Random(0x2B96F0)
    cases.extend((group := rng.randrange(128), rng.getrandbits(32), rng.getrandbits(32), False)
                 for _ in range(96))
    for index, (group, subindex, base, null_entry) in enumerate(cases):
        ref = execute(original_machine, FUNCTION, group, subindex, base, null_entry)
        temp = execute(temp_machine, CANDIDATE, group, subindex, base, null_entry)
        integrated = execute(final_machine, FUNCTION, group, subindex, base, null_entry)
        if (comparable(ref, FUNCTION) != comparable(temp, CANDIDATE)
                or comparable(ref, FUNCTION) != comparable(integrated, FUNCTION)):
            raise AssertionError(f"case {index} differs: {ref} / {temp} / {integrated}")
    mutations = [
        {"name": "group-stride-24-to-32", "detected": mutation_detected("stride", "const u32 manager_entry = *reinterpret_cast<const u32*>(table + group * 24u);\n    return AsdResource_ResolveSubindexTail", "const u32 manager_entry = *reinterpret_cast<const u32*>(table + group * 32u);\n    return AsdResource_ResolveSubindexTail", 3, 0, 0x12345000)},
        {"name": "second-index-forwarding", "detected": mutation_detected("subindex", "return AsdResource_ResolveSubindexTail(manager_entry, subindex);", "return AsdResource_ResolveSubindexTail(manager_entry, group);", 5, 4, 0x12345000), "detection": "mutant no longer fits the 24-byte span"},
    ]
    if not all(item["detected"] for item in mutations):
        raise AssertionError(f"negative control escaped: {mutations}")
    predicate_body, _ = predicate.compile_candidate("predicate-pair-final.o", predicate.FUNCTION)
    pair_caller = predicate.setup(predicate_body, predicate.FUNCTION,
                                  stop_at=predicate.TITLECONFIG_AFTER_TEST)
    pair_caller.mem_write(FUNCTION, final)
    caller_compositions = []
    for flags in (0, 4, MASK):
        old = predicate.titleconfig_caller(
            predicate.setup(stop_at=predicate.TITLECONFIG_AFTER_TEST), flags)
        paired = predicate.titleconfig_caller(pair_caller, flags)
        if old != paired:
            raise AssertionError(f"TitleConfig caller pair differs for flags {flags:#x}: {old} / {paired}")
        caller_compositions.append({"flags": flags, "return_and_zero_flag": old, "same": True})
    report = {
        "function": "engine_func_002b96f0", "address": hex(FUNCTION), "span": SPAN,
        "image_sha256": sha(image), "source_sha256": sha(SOURCE.read_bytes()),
        "candidate_bytes": len(temporary), "temporary_body_sha256": sha(temporary),
        "final_body_sha256": sha(final), "original_body_sha256": sha(original_body),
        "temporary_byte_identical": temporary == original_body,
        "final_byte_identical": final == original_body,
        "temporary_relocations": temp_relocs, "final_relocations": final_relocs,
        "cases": len(cases), "directed_cases": 7, "seeded_cases": 96,
        "coverage": "group*24 table lookup; null table entry; raw 32-bit base plus subindex*32 wrap; preserved r1/callee-saved registers/SP; ordered reads and no writes",
        "negative_controls": mutations,
        "typed_predicate_body_sha256": sha(predicate_body),
        "titleconfig_caller_composition": caller_compositions,
        "pair_composition": "typed 0x002A63F8 calls typed 0x002B96F0 at final VMA; resolver final bytes equal original",
        "tail_helper": {"address": hex(TAIL), "transfer": "ARM B, preserving LR", "implementation": "original four-instruction code in pinned image"},
        "limits": "controlled mapped fixtures and the statically audited internal tail helper; no natural runtime titleConfig scenario",
        "runtime": "not_run",
    }
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"report: {report_path}")


if __name__ == "__main__":
    main()
