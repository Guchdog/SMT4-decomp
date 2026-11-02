#!/usr/bin/env python3
"""Pinned offline differential for the H2 resource loaded-bit predicate."""
from __future__ import annotations

import hashlib
import argparse
import json
import struct
import sys
from pathlib import Path

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch17_c.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-resource-flag-predicate-002a63f8/run001"
FUNCTION = 0x002A63F8
RESOLVER = 0x002B96F0
SPAN = 24
TEXT = 0x00100000
CANDIDATE = 0x00800000
STOP = 0x0080F000
TITLECONFIG_CALLER = 0x001EA964
TITLECONFIG_AFTER_TEST = 0x001EA978
TABLE_PTR = 0x0044EA28
TABLE = 0x00900000
MANAGER = 0x00910000
RESOURCE = 0x00920000
STACK = 0x00A0FF00
MASK = 0xFFFFFFFF


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_candidate(name: str, entry: int, source: Path = SOURCE) -> tuple[bytes, list[dict]]:
    OUT.mkdir(parents=True, exist_ok=True)
    obj = OUT / name
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocations = extract_elf_functions_detailed(obj)["ui_func_002a63f8"]
    patched = bytearray(body)
    resolved = []
    for relocation in relocations:
        if (relocation.relocation_type != 28 or relocation.symbol_name != "engine_func_002b96f0"
                or relocation.explicit_addend is not None):
            raise AssertionError(f"unexpected candidate relocation: {relocation}")
        place = entry + relocation.offset
        instruction = struct.unpack_from("<I", patched, relocation.offset)[0]
        if instruction & 0x0F000000 != 0x0B000000:
            raise AssertionError(f"expected ARM BL at {relocation.offset:#x}: {instruction:#010x}")
        delta = RESOLVER - (place + 8)
        struct.pack_into("<I", patched, relocation.offset,
                         (instruction & 0xFF000000) | ((delta >> 2) & 0xFFFFFF))
        resolved.append({"offset": relocation.offset, "target": hex(RESOLVER), "type": relocation.relocation_type})
    if len(patched) > SPAN or len(patched) % 4 or len(relocations) != 1:
        raise AssertionError(f"candidate layout is not one in-slot ARM BL body: {len(patched)}, {relocations}")
    return bytes(patched), resolved


def mutation_detected(label: str, old: str, new: str) -> bool:
    source_text = SOURCE.read_text(encoding="utf-8")
    if source_text.count(old) != 1:
        raise AssertionError(f"non-unique mutation anchor for {label}")
    mutant_source = OUT / f"mutant-{label}.cpp"
    mutant_source.write_text(source_text.replace(old, new, 1), encoding="utf-8")
    body, _relocs = compile_candidate(f"mutant-{label}.o", CANDIDATE, mutant_source)
    machine = setup(body)
    try:
        execute(machine, CANDIDATE, 0x2F, 0, 4)
    except AssertionError:
        return True
    return False


def setup(candidate: bytes | None = None, candidate_entry: int = CANDIDATE, stop_at: int = STOP,
          image_bytes: bytes | None = None):
    image = image_bytes if image_bytes is not None else IMAGE_PATH.read_bytes()
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    map_size = (len(image) + 0xFFF) & ~0xFFF
    uc.mem_map(TEXT, map_size)
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
        if address == stop_at:
            state["done"] = True
            machine.emu_stop()

    def on_read(_machine, _kind, address, size, _value, _data):
        state["reads"].append((address, size))

    def on_write(_machine, _kind, address, size, value, _data):
        state["writes"].append((address, size, value & MASK))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_MEM_READ, on_read)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    uc._state = state
    return uc


def titleconfig_caller(uc, flag_word: int) -> tuple[int, bool]:
    uc.mem_write(TABLE + 0x2F * 24, struct.pack("<I", MANAGER))
    uc.mem_write(MANAGER, struct.pack("<I", RESOURCE))
    uc.mem_write(RESOURCE + 0x10, struct.pack("<I", flag_word & MASK))
    uc.reg_write(UC_ARM_REG_SP, STACK)
    uc.reg_write(UC_ARM_REG_LR, STOP)
    uc._state.update(done=False, reads=[], writes=[])
    uc.emu_start(TITLECONFIG_CALLER, 0, count=100)
    if not uc._state["done"]:
        raise AssertionError("TitleConfig_Calc call slice did not reach compare")
    cpsr = uc.reg_read(UC_ARM_REG_CPSR)
    return uc.reg_read(UC_ARM_REG_R0), bool(cpsr & (1 << 30))


def execute(uc, entry: int, group: int, subindex: int, flag_word: int, null_result: bool = False):
    state = uc._state
    state.update(done=False, reads=[], writes=[], last_pc=None)
    uc.mem_write(TABLE + group * 24, struct.pack("<I", 0 if null_result else MANAGER))
    uc.mem_write(MANAGER, struct.pack("<I", RESOURCE))
    uc.mem_write(RESOURCE + subindex * 32, struct.pack("<I", 0x12345678))
    uc.mem_write(RESOURCE + subindex * 32 + 0x10, struct.pack("<I", flag_word & MASK))
    saved = {reg: 0x11110000 + index * 0x01010101 for index, reg in enumerate(
        (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11))}
    uc.reg_write(UC_ARM_REG_SP, STACK)
    uc.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in saved.items():
        uc.reg_write(reg, value)
    uc.reg_write(UC_ARM_REG_R0, group)
    uc.reg_write(UC_ARM_REG_R1, subindex)
    fault = None
    try:
        uc.emu_start(entry, 0, count=100)
    except (UcError, OSError) as exc:
        fault = str(exc)
    observed = {
        "return": uc.reg_read(UC_ARM_REG_R0),
        "callee_saved": all(uc.reg_read(reg) == value for reg, value in saved.items()),
        "sp": uc.reg_read(UC_ARM_REG_SP) == STACK,
        "reads": tuple(state["reads"]), "writes": tuple(state["writes"]),
        "done": state["done"], "fault": fault,
        "fault_instruction_offset": (state["last_pc"] - entry) if fault is not None else None,
    }
    if null_result:
        if fault is None or observed["done"] or not observed["reads"]:
            raise AssertionError(f"null-result fault behavior changed: {observed}")
    elif fault or not observed["done"] or observed["return"] != (1 if flag_word & 4 else 0):
        raise AssertionError(f"wrong result for group={group}, subindex={subindex}, flags={flag_word}: {observed}")
    outside_stack = tuple(event for event in observed["writes"]
                          if not (STACK - 0x100 <= event[0] < STACK + 0x100))
    if outside_stack or (fault is None and (not observed["callee_saved"] or not observed["sp"])):
        raise AssertionError(f"ABI or write-footprint mismatch: {observed}")
    return observed


def comparable(result):
    # The compiler may use a different caller-saved scratch register in its
    # stack alignment pair; both implementations keep SP and callee-saved state.
    return {key: value for key, value in result.items() if key != "writes"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged-image", type=Path)
    args = parser.parse_args()
    image = IMAGE_PATH.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise SystemExit("pinned code.bin hash mismatch")
    staged_image = args.staged_image.read_bytes() if args.staged_image else None
    temporary, temp_relocs = compile_candidate("candidate-temp.o", CANDIDATE)
    final, final_relocs = compile_candidate("candidate-final.o", FUNCTION)
    original_machine = setup()
    temp_machine = setup(temporary)
    final_machine = setup(final, FUNCTION)
    staged_machine = setup(stop_at=STOP, image_bytes=staged_image) if staged_image is not None else None
    cases = []
    # Covers H2's real (group=0x2f, subindex=0) call and varied resolver indexing.
    for group, subindex, flags in [
        (0x2F, 0, 0), (0x2F, 0, 4), (0x2F, 0, 0xFFFFFFFF),
        (0, 1, 1), (1, 2, 2), (7, 3, 8), (0x2F, 7, 0xFFFFFFFB),
        (31, 0, 0x100),
    ]:
        old = execute(original_machine, FUNCTION, group, subindex, flags)
        temp = execute(temp_machine, CANDIDATE, group, subindex, flags)
        integrated = execute(final_machine, FUNCTION, group, subindex, flags)
        staged_result = execute(staged_machine, FUNCTION, group, subindex, flags) if staged_machine else old
        if (comparable(old) != comparable(temp) or comparable(old) != comparable(integrated)
                or comparable(old) != comparable(staged_result)):
            raise AssertionError(f"differential mismatch {group}/{subindex}/{flags}: {old} / {temp} / {integrated} / {staged_result}")
        cases.append({"group": group, "subindex": subindex, "flags": flags, "same": True})
    null_results = [
        execute(original_machine, FUNCTION, 0x2F, 0, 0, True),
        execute(temp_machine, CANDIDATE, 0x2F, 0, 0, True),
        execute(final_machine, FUNCTION, 0x2F, 0, 0, True),
    ]
    if staged_machine is not None:
        null_results.append(execute(staged_machine, FUNCTION, 0x2F, 0, 0, True))
    if any(comparable(result) != comparable(null_results[0]) for result in null_results[1:]):
        raise AssertionError(f"null-result fault behavior differs: {null_results}")
    null_profiles = ["original", "temporary", "final-vma"] + (["staged"] if staged_machine else [])
    null_fault_observations = [
        {"profile": profile, "exception": result["fault"],
         "instruction_offset": result["fault_instruction_offset"]}
        for profile, result in zip(null_profiles, null_results)
    ]
    caller_rows = []
    for flags in (0, 4, 0xFFFFFFFF):
        old_caller = titleconfig_caller(setup(stop_at=TITLECONFIG_AFTER_TEST), flags)
        new_caller = titleconfig_caller(setup(final, FUNCTION, stop_at=TITLECONFIG_AFTER_TEST), flags)
        staged_caller = titleconfig_caller(setup(stop_at=TITLECONFIG_AFTER_TEST, image_bytes=staged_image), flags) if staged_image is not None else old_caller
        if old_caller != new_caller or old_caller != staged_caller:
            raise AssertionError(f"TitleConfig_Calc caller differs for flags {flags:#x}: {old_caller} / {new_caller} / {staged_caller}")
        caller_rows.append({"flags": flags, "return_and_zero_flag": old_caller, "same": True})
    negative_controls = [
        {"name": "bit-mask-4-to-8", "detected": mutation_detected("mask", "& 4u", "& 8u")},
        {"name": "predicate-polarity", "detected": mutation_detected("polarity", "!= 0", "== 0")},
    ]
    if not all(control["detected"] for control in negative_controls):
        raise AssertionError(f"negative control escaped: {negative_controls}")
    candidate_temp = image[FUNCTION - TEXT:FUNCTION - TEXT + SPAN]
    candidate_final = image[FUNCTION - TEXT:FUNCTION - TEXT + SPAN]
    report = {
        "function": "ui_func_002a63f8", "address": hex(FUNCTION), "span": SPAN,
        "image_sha256": sha(image), "source_sha256": sha(SOURCE.read_bytes()),
        "candidate_size": len(temporary), "candidate_sha256": sha(temporary),
        "final_candidate_size": len(final), "final_candidate_sha256": sha(final),
        "original_sha256": sha(candidate_temp), "final_original_sha256": sha(candidate_final),
        "temporary_byte_identical": temporary == candidate_temp,
        "final_byte_identical": final == candidate_final,
        "relocations": temp_relocs, "final_relocations": final_relocs,
        "cases": cases,
        "null_result_fault": "same exception and faulting instruction offset at original, temporary candidate, final VMA, and staged image when supplied",
        "null_fault_observations": null_fault_observations,
        "negative_controls": negative_controls,
        "titleconfig_caller_composition": caller_rows,
        "staged_image_sha256": sha(staged_image) if staged_image is not None else None,
        "staged_image_differential": "passed: direct cases and actual TitleConfig_Calc call slice" if staged_image is not None else "not_run",
        "coverage": "H2 titleConfig group 0x2f/subindex 0; bit clear/set, unrelated bits, varied indices, and null resolved record fault.",
        "limits": "offline Unicorn differential only; no natural scheduler/runtime titleConfig scenario",
    }
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.staged_image:
        manifest_path = args.staged_image.parent / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["evidence"]["offline_differential"] = "passed: 8 direct fixtures plus null fault; original/temp/final/staged comparison"
        manifest["evidence"]["caller"] = "passed: original TitleConfig_Calc call slice 0x001EA964-0x001EA978, including the production 0x002F/0 arguments"
        manifest["evidence"]["review"] = "pending independent review"
        manifest["validation_report"] = str(report_path.relative_to(ROOT))
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"report: {report_path}")


if __name__ == "__main__":
    main()
