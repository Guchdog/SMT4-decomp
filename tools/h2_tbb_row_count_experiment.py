#!/usr/bin/env python3
"""Final-VMA differential and selector composition for Tbb_GetRowCount."""
from __future__ import annotations

import argparse
import csv
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

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/ui/tbb_loader.cpp"
ENTRY, SLOT = 0x002C0E4C, 56
SELECTOR = 0x002AEA28
DIVIDER = 0x002C6C10
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00020000
GLOBAL_BASE, GLOBAL_SIZE = 0x00493000, 0x00003000
GLOBAL_SLOTS = 0x0049382C
TABLE, CONTAINER, STACK = DATA_BASE + 0x1000, DATA_BASE + 0x8000, 0x08000000
CHILD = CONTAINER + 0x10
STACK_SIZE, SP, STOP = 0x10000, STACK + 0x8000, STACK + 0x9000
TBL1, TBCR, U32 = 0x314C4254, 0x52434254, 0xFFFFFFFF
SYMBOLS = {"ui_func_002c6c10": DIVIDER}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ledger_addresses():
    with (ROOT / "config/functions.csv").open(encoding="utf-8-sig", newline="") as f:
        return {row["name"]: int(row["address"], 0) for row in csv.DictReader(f)}


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / source.name.replace(".cpp", ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K translation unit compile failed")
    symbols = extract_elf_functions_detailed(obj)
    body, relocs = symbols["_ZN4smt42ui15Tbb_GetRowCountEPKNS0_10Tbl1HeaderE"]
    if len(body) > SLOT or len(body) % 4:
        raise ValueError(f"function body does not fit original slot: {len(body)}/{SLOT}")
    return body, relocs, list(result.args), obj


def stage_image(original: bytes, body: bytes, relocs):
    staged = bytearray(original)
    resolved = []
    fixed = bytearray(body)
    for reloc in relocs:
        target = SYMBOLS.get(reloc.symbol_name)
        if target is None or reloc.relocation_type not in (28, 29):
            raise ValueError(f"unsupported relocation: {reloc}")
        site = ENTRY + reloc.offset
        delta = target - (site + 8)
        if delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f"ARM branch out of range/alignment: {site:#x}->{target:#x}")
        word = struct.unpack_from("<I", fixed, reloc.offset)[0]
        word = (word & 0xFF000000) | ((delta >> 2) & 0x00FFFFFF)
        struct.pack_into("<I", fixed, reloc.offset, word)
        resolved.append({"offset": reloc.offset, "type": reloc.relocation_type,
                         "symbol": reloc.symbol_name, "target": hex(target),
                         "target_bit0_clear": (target & 1) == 0})
    off = ENTRY - CODE_BASE
    if len(fixed) > SLOT:
        raise ValueError(f"body exceeds {SLOT}-byte slot")
    payload = bytes(fixed) + original[off + len(fixed):off + SLOT]
    staged[off:off + SLOT] = payload
    patch = encode_ips([(off, payload)], len(original))
    if apply_ips(original, patch) != bytes(staged):
        raise AssertionError("slot IPS replay failed")
    return bytes(staged), patch, resolved


class Machine:
    def __init__(self, image: bytes, seed: int = 1):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM,
                             unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(GLOBAL_BASE, GLOBAL_SIZE)
        self.uc.mem_map(STACK, STACK_SIZE)
        rng = random.Random(seed)
        self.uc.mem_write(DATA_BASE, bytes(rng.randrange(256) for _ in range(DATA_SIZE)))
        self.uc.mem_write(GLOBAL_BASE, bytes(GLOBAL_SIZE))
        self.events, self.writes = [], []
        self.stop = STOP
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_code(self, uc, address, _size, _data):
        if address == self.stop:
            uc.emu_stop()
        elif address == DIVIDER:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            self.events.append({"address": hex(address), "args": [hex(r0), hex(r1)],
                                "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})

    def _on_write(self, _uc, _access, address, size, value, _data):
        if not STACK <= address < STACK + STACK_SIZE:
            self.writes.append([hex(address), size, value & U32])

    def run(self, entry: int, arg0: int, arg1: int = 0, setup=None):
        if setup:
            setup(self.uc)
        regs = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13)]
        initial = [(0xA1000000 + i * 0x01010101) & U32 for i in range(13)]
        for reg, value in zip(regs, initial):
            self.uc.reg_write(reg, value)
        self.uc.reg_write(arm.UC_ARM_REG_R0, arg0 & U32)
        self.uc.reg_write(arm.UC_ARM_REG_R1, arg1 & U32)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, STOP)
        fault = None
        try:
            self.uc.emu_start(entry, 0, count=100000)
        except unicorn.UcError as error:
            fault = str(error)
        after = [self.uc.reg_read(reg) for reg in regs]
        return {"fault": fault, "r0": after[0], "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                "callee_saved": after[4:12] == initial[4:12],
                "data": bytes(self.uc.mem_read(DATA_BASE, DATA_SIZE)),
                "globals": bytes(self.uc.mem_read(GLOBAL_BASE, GLOBAL_SIZE)),
                "events": self.events.copy(), "writes": self.writes.copy()}


def table_setup(ptr: int, magic: int, size: int, stride: int):
    def setup(uc):
        if DATA_BASE <= ptr < DATA_BASE + DATA_SIZE:
            uc.mem_write(ptr, struct.pack("<4I", magic, size, stride, 0))
    return setup


def direct_cases():
    return [
        (0, 0, 0, 0, 1),
        (TABLE, 0, 96, 16, 2),
        (TABLE, TBL1 ^ 1, 96, 16, 3),
        (TABLE, TBL1, 96, 0, 4),
        (TABLE, TBL1, 0, 16, 5),
        (TABLE, TBL1, 1, 1, 6),
        (TABLE, TBL1, 15, 4, 7),
        (TABLE, TBL1, 17, 16, 8),
        (TABLE, TBL1, 0xFFFFFFFF, 1, 9),
        (TABLE, TBL1, 0xFFFFFFFF, 0x80000000, 10),
        (TABLE, TBL1, 0x80000000, 0x7FFFFFFF, 11),
        (TABLE, TBL1, 0x12345678, 0x1234, 12),
        (0x00600000, TBL1, 12, 4, 13),
    ]


def composition_setup(row_count: int):
    def setup(uc):
        slot_offset = GLOBAL_SLOTS - GLOBAL_BASE + 14 * 16 + 4
        uc.mem_write(GLOBAL_BASE + slot_offset, struct.pack("<I", CONTAINER))
        uc.mem_write(CONTAINER, struct.pack("<4I", TBCR, 16, 1, 0))
        uc.mem_write(CHILD, struct.pack("<4I", TBL1, row_count * 16, 16, 0))
    return setup


def invoke(image: bytes, entry: int, args: tuple[int, int], setup):
    return Machine(image, seed=771).run(entry, args[0], args[1], setup)


def binary_mutation_control(original: bytes, body: bytes, relocs, label: str,
                            edits: tuple[tuple[int, int, int], ...],
                            case: tuple[int, int, int, int, int]):
    mutant_body = bytearray(body)
    for offset, expected, replacement in edits:
        current = struct.unpack_from("<I", mutant_body, offset)[0]
        if current != expected:
            raise ValueError(f"unexpected instruction/literal for {label}: {current:#x}")
        struct.pack_into("<I", mutant_body, offset, replacement)
    mutant = stage_image(original, bytes(mutant_body), relocs)[0]
    ptr, magic, size, stride, seed = case
    setup = table_setup(ptr, magic, size, stride)
    ref = invoke(original, ENTRY, (ptr, 0), setup)
    got = invoke(mutant, ENTRY, (ptr, 0), setup)
    return {"detected": ref != got, "case": {"pointer": hex(ptr), "magic": hex(magic),
            "size": hex(size), "stride": hex(stride), "seed": seed},
            "mutant_fault": got["fault"], "mutant_result": hex(got["r0"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")
    body, relocs, compiler_args, obj = compile_body(args.out / "compile")
    staged, patch, resolved = stage_image(original, body, relocs)
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-entry.ips").write_bytes(patch)

    directs, mismatches = [], []
    for ptr, magic, size, stride, seed in direct_cases():
        setup = table_setup(ptr, magic, size, stride)
        ref = invoke(original, ENTRY, (ptr, 0), setup)
        got = invoke(staged, ENTRY, (ptr, 0), setup)
        equal = ref == got
        directs.append({"pointer": hex(ptr), "magic": hex(magic), "size": hex(size),
                        "stride": hex(stride), "equal": equal, "result": hex(got["r0"]),
                        "fault": got["fault"], "divider_calls": got["events"]})
        if not equal:
            mismatches.append({"case": directs[-1], "original": ref, "candidate": got})

    callers = []
    count = 5
    for index in (0, count - 1, count, count + 1, 0xFFFFFFFF):
        setup = composition_setup(count)
        ref = invoke(original, SELECTOR, (index, 0), setup)
        got = invoke(staged, SELECTOR, (index, 0), setup)
        equal = ref == got
        callers.append({"selector": hex(SELECTOR), "index": hex(index),
                        "row_count": count, "equal": equal,
                        "result": hex(got["r0"]), "fault": got["fault"],
                        "divider_calls": got["events"]})
        if not equal:
            mismatches.append({"caller": callers[-1], "original": ref, "candidate": got})

    controls = {}
    controls["wrong_magic_literal"] = binary_mutation_control(
        original, body, relocs, "wrong_magic_literal", ((52, TBL1, TBL1 ^ 1),),
        (TABLE, TBL1, 96, 16, 301))
    controls["wrong_zero_stride_boundary"] = binary_mutation_control(
        original, body, relocs, "wrong_zero_stride_boundary",
        ((28, 0xE3510000, 0xE3510001),), (TABLE, TBL1, 96, 1, 302))
    controls["swapped_division_operands"] = binary_mutation_control(
        original, body, relocs, "swapped_division_operands",
        ((24, 0xE5901008, 0xE5901004), (36, 0xE5900004, 0xE5900008)),
        (TABLE, TBL1, 17, 4, 303))
    for label, result in controls.items():
        if not result["detected"]:
            mismatches.append({"mutation": label, "case": result})

    changed_outside = any(a != b and not ENTRY - CODE_BASE <= i < ENTRY - CODE_BASE + SLOT
                          for i, (a, b) in enumerate(zip(original, staged)))
    final_slot = staged[ENTRY - CODE_BASE:ENTRY - CODE_BASE + SLOT]
    original_slot = original[ENTRY - CODE_BASE:ENTRY - CODE_BASE + SLOT]
    report = {"schema_version": 1, "image_sha256": sha(original),
              "source_sha256": sha(SOURCE.read_bytes()), "object_sha256": sha(obj.read_bytes()),
              "entry": hex(ENTRY), "slot_size": SLOT, "compiled_body_size": len(body),
              "object_body_exact_matching_before_relocation": body == original_slot,
              "exact_matching": final_slot == original_slot,
              "final_slot_sha256": sha(final_slot),
              "relocations": resolved, "direct_cases": directs, "direct_case_count": len(directs),
              "selector_compositions": callers, "mutation_controls": controls,
              "mismatch_count": len(mismatches), "mismatches": mismatches,
              "ips_replay": apply_ips(original, patch) == staged,
              "changed_outside_slot": changed_outside, "compiler_command": compiler_args}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"body_size": len(body), "exact_matching": report["exact_matching"],
                      "direct_cases": len(directs), "selector_compositions": callers,
                      "mutation_controls": controls, "mismatch_count": len(mismatches), "relocations": resolved,
                      "ips_replay": report["ips_replay"], "changed_outside_slot": changed_outside}, indent=2))
    return 1 if mismatches or changed_outside else 0


if __name__ == "__main__":
    raise SystemExit(main())
