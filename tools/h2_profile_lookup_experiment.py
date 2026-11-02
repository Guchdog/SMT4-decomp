#!/usr/bin/env python3
"""Final-VMA differential and H2 caller composition for 0x002AEA28."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import struct
import sys
from dataclasses import dataclass
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
SOURCE = ROOT / "src/engine/leaf_batch24_b.cpp"
ENTRY, SLOT = 0x002AEA28, 56
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00020000
OBJECT, TABLE_HEADER = DATA_BASE, DATA_BASE + 0x8000
PAYLOAD = TABLE_HEADER + 0x10
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000
U32 = 0xFFFFFFFF

CALLEES = {
    0x002C0EC4: 2,
    0x002C0E9C: 1,
    0x002C0E4C: 1,
    0x002B85BC: 1,
    0x002B8794: 4,
    0x0013851C: 1,
    0x002AE874: 1,
}
ALIASES = {
    "_ZN4smt42ui21Tbb_GetGlobalSubTableEjj": "Tbb_GetGlobalSubTable",
    "_ZN4smt42ui18Tbb_GetPayloadDataEPKNS0_10Tbl1HeaderE": "Tbb_GetPayloadData",
    "_ZN4smt42ui15Tbb_GetRowCountEPKNS0_10Tbl1HeaderE": "Tbb_GetRowCount",
}


@dataclass(frozen=True)
class Case:
    seed: int
    index: int
    row_count: int
    table_address: int = TABLE_HEADER
    payload_address: int = PAYLOAD


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rows_by_name():
    with (ROOT / "config/functions.csv").open(encoding="utf-8-sig", newline="") as f:
        return {row["name"]: int(row["address"], 0) for row in csv.DictReader(f)}


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / source.name.replace(".cpp", ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K translation unit compile failed")
    body, relocations = extract_elf_functions_detailed(obj)["camp_func_002aea28"]
    if len(body) > SLOT or len(body) % 4:
        raise ValueError(f"function body does not fit its slot: {len(body)}/{SLOT}")
    return body, relocations, list(result.args), obj


def stage_image(original: bytes, body: bytes, relocations):
    fixed = bytearray(body)
    addresses = rows_by_name()
    resolved = []
    for reloc in relocations:
        word = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if reloc.relocation_type != 28:
            raise ValueError(f"unsupported relocation: {reloc}")
        symbol = ALIASES.get(reloc.symbol_name, reloc.symbol_name)
        if symbol not in addresses:
            raise ValueError(f"unmapped call symbol {reloc.symbol_name}")
        target = addresses[symbol]
        site = ENTRY + reloc.offset
        delta = target - (site + 8)
        if target & 1 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f"invalid ARM call target: {reloc}")
        if word & 0xFF000000 != 0xEB000000:
            raise ValueError(f"expected unconditional ARM BL at {reloc.offset:#x}")
        struct.pack_into("<I", fixed, reloc.offset,
                         (word & 0xFF000000) | ((delta >> 2) & 0x00FFFFFF))
        resolved.append({"offset": reloc.offset, "symbol": symbol, "target": hex(target),
                         "target_bit0_clear": True})
    payload = bytearray(b"\0" * SLOT)
    payload[:len(fixed)] = fixed
    image = bytearray(original)
    offset = ENTRY - CODE_BASE
    image[offset:offset + SLOT] = payload
    staged = bytes(image)
    patch = encode_ips([(offset, bytes(payload))], len(original))
    if apply_ips(original, patch) != staged:
        raise AssertionError("slot IPS replay mismatch")
    return staged, patch, bytes(payload), resolved


class Machine:
    def __init__(self, image: bytes, case: Case, caller_object: bool = False):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM,
                             unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(STACK, STACK_SIZE)
        self.case = case
        rng = random.Random(case.seed)
        data = bytes(rng.randrange(256) for _ in range(DATA_SIZE))
        self.uc.mem_write(DATA_BASE, data)
        self.events, self.writes = [], []
        self.stop = STOP

        if caller_object:
            obj = bytearray(rng.randrange(256) for _ in range(0x1000))
            obj[0x4C9] = 9
            obj[0x4B8:0x4BE] = b"\0" * 6
            self.uc.mem_write(OBJECT, bytes(obj))
            header = bytearray(0x10)
            struct.pack_into("<I", header, 0, 0x314C4254)
            struct.pack_into("<I", header, 4, 0x1000)
            struct.pack_into("<I", header, 8, 0x10)
            self.uc.mem_write(TABLE_HEADER, bytes(header))
            old_profile = PAYLOAD + 9 * 16
            new_profile = PAYLOAD + (case.index & 0xFF) * 16
            old_data = bytearray((0x21 + i * 7) & 0xFF for i in range(16))
            new_data = bytearray((0x49 + i * 11) & 0xFF for i in range(16))
            struct.pack_into("<H", new_data, 0, 1)
            struct.pack_into("<H", new_data, 2, 0x100)
            old_data[0x0C] = 1
            new_data[0x0C] = 0
            self.uc.mem_write(old_profile, bytes(old_data))
            self.uc.mem_write(new_profile, bytes(new_data))
            self.uc.mem_write(0x0043DA2C, struct.pack("<I", OBJECT))
            self.uc.mem_write(0x0043DA38, struct.pack("<I", 0))

        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_write(self, _uc, _access, address, size, value, _data):
        if not STACK <= address < STACK + STACK_SIZE:
            self.writes.append((address, size, value & U32))

    def _on_code(self, uc, address, _size, _data):
        if address == self.stop:
            uc.emu_stop()
            return
        if address not in CALLEES:
            return
        argc = CALLEES[address]
        args = tuple(uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(argc))
        self.events.append({"address": address, "args": args,
                            "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
        if address == 0x002C0EC4:
            result = self.case.table_address
        elif address == 0x002C0E9C:
            result = self.case.payload_address
        elif address == 0x002C0E4C:
            result = self.case.row_count
        elif address == 0x002B85BC:
            result = 0xB85BC000 | (args[0] & 0xFFFF)
        elif address == 0x002B8794:
            result = 0xB8794000 | (args[0] & 0xFFFF)
        elif address == 0x0013851C:
            result = 0x13851000 | (args[0] & 0xFFFF)
        else:
            result = 0xAE870000 | (args[0] & 0xFFFF)
        uc.reg_write(arm.UC_ARM_REG_R0, result & U32)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def run(self, start=ENTRY, stop=STOP, request=None):
        self.stop = stop
        regs = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13)]
        initial = [(0xA1000000 + i * 0x01010101) & U32 for i in range(13)]
        for reg, value in zip(regs, initial):
            self.uc.reg_write(reg, value)
        self.uc.reg_write(arm.UC_ARM_REG_R0,
                          self.case.index if request is None else request)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, stop)
        fault = None
        try:
            self.uc.emu_start(start, 0, count=10000)
        except unicorn.UcError as error:
            fault = str(error)
        after = [self.uc.reg_read(reg) for reg in regs]
        return {
            "fault": fault,
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": after[4:12] == initial[4:12],
            "root": bytes(self.uc.mem_read(0x0043DA28, 0x20)).hex(),
            "data": bytes(self.uc.mem_read(DATA_BASE, DATA_SIZE)).hex(),
            "events": self.events.copy(),
            "writes": self.writes.copy(),
        }


def direct_cases():
    return [Case(100 + i, index, count, table, payload)
            for i, (index, count, table, payload) in enumerate((
                (0, 0, TABLE_HEADER, PAYLOAD),
                (0, 1, TABLE_HEADER, PAYLOAD),
                (1, 1, TABLE_HEADER, PAYLOAD),
                (2, 5, TABLE_HEADER, PAYLOAD),
                (4, 5, TABLE_HEADER, PAYLOAD),
                (5, 5, TABLE_HEADER, PAYLOAD),
                (6, 5, TABLE_HEADER, PAYLOAD),
                (0xFFFFFFFF, 0xFFFFFFFF, TABLE_HEADER, PAYLOAD),
                (0xFFFFFFFF, 0, TABLE_HEADER, PAYLOAD),
                (0, 2, TABLE_HEADER, 0),
                (1, 2, 0, PAYLOAD),
                (0, 1, 0, 0),
                (0x7FFFFFFF, 0x80000000, TABLE_HEADER, PAYLOAD),
                (0x80000000, 0x80000000, TABLE_HEADER, PAYLOAD),
                (0xFFFFFFFE, 0xFFFFFFFF, TABLE_HEADER, PAYLOAD),
                (0xFFFFFFFF, 0xFFFFFFFE, TABLE_HEADER, PAYLOAD),
            ))]


def run_mutant(out: Path, original: bytes, label: str, before: str, after: str, case: Case):
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise ValueError(f"non-unique mutation anchor: {label}")
    source = out / "mutants" / f"{label}.cpp"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(text.replace(before, after), encoding="utf-8")
    body, relocs, _args, _obj = compile_body(out / "mutants" / label / "compile", source)
    mutant = stage_image(original, body, relocs)[0]
    return run_case(original, case), run_case(mutant, case)


def run_case(image: bytes, case: Case):
    return Machine(image, case).run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")
    body, relocs, compiler_args, obj = compile_body(args.out / "compile")
    staged, patch, _slot, resolved = stage_image(original, body, relocs)
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-entry.ips").write_bytes(patch)

    mismatches, directs = [], []
    for case in direct_cases():
        ref, got = run_case(original, case), run_case(staged, case)
        equal = ref == got
        directs.append({"case": case.__dict__, "equal": equal, "r0": hex(got["r0"]),
                        "events": got["events"], "fault": got["fault"]})
        if not equal:
            mismatches.append({"case": case.__dict__, "original": ref, "candidate": got})

    controls = {}
    for label, before, after, case in (
        ("wrong_subtable_id", "Tbb_GetGlobalSubTable(0x0Eu, 0)",
         "Tbb_GetGlobalSubTable(0x0Fu, 0)", Case(141, 2, 5)),
        ("wrong_index_stride", '"addlo %0, %3, %1, lsl #4\\n"',
         '"addlo %0, %3, %1, lsl #3\\n"', Case(142, 2, 5)),
        ("wrong_equal_boundary", '"movhs %0, #0\\n"',
         '"movhi %0, #0\\n"', Case(143, 5, 5)),
    ):
        ref, got = run_mutant(args.out, original, label, before, after, case)
        detected = ref != got
        controls[label] = {"detected": detected, "case": case.__dict__}
        if not detected:
            mismatches.append({"mutation": label, "original": ref, "mutant": got})

    callers = []
    for label, start, stop, request in (
        ("title_config_init_0x99", 0x002F4DEC, 0x002F4DF4, 0x99),
        ("nested_callback_0xDC", 0x00286B7C, 0x00286B84, 0xDC),
    ):
        case = Case(150 if request == 0x99 else 151, request, 0x100)
        ref = Machine(original, case, caller_object=True).run(start, stop, request)
        got = Machine(staged, case, caller_object=True).run(start, stop, request)
        equal = ref == got
        callers.append({"caller": label, "start": hex(start), "stop": hex(stop),
                        "request": hex(request), "equal": equal, "fault": got["fault"],
                        "events": got["events"], "r0": hex(got["r0"])})
        if not equal:
            mismatches.append({"caller": label, "original": ref, "candidate": got})

    changed_outside = any(
        a != b and not ENTRY - CODE_BASE <= offset < ENTRY - CODE_BASE + SLOT
        for offset, (a, b) in enumerate(zip(original, staged)))
    report = {
        "schema_version": 1,
        "image_sha256": sha(original),
        "source_sha256": sha(SOURCE.read_bytes()),
        "object_sha256": sha(obj.read_bytes()),
        "entry": hex(ENTRY),
        "slot_size": SLOT,
        "compiled_body_size": len(body),
        "exact_matching": body == original[ENTRY - CODE_BASE:ENTRY - CODE_BASE + SLOT],
        "relocations": resolved,
        "direct_case_count": len(directs),
        "direct_cases": directs,
        "caller_cases": callers,
        "mutation_controls": controls,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "ips_replay": apply_ips(original, patch) == staged,
        "changed_outside_slot": changed_outside,
        "compiler_command": compiler_args,
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"body_size": len(body), "exact_matching": report["exact_matching"],
                      "direct_cases": len(directs), "caller_cases": callers,
                      "mutation_controls": controls, "mismatch_count": len(mismatches),
                      "relocations": resolved, "ips_replay": report["ips_replay"],
                      "changed_outside_slot": changed_outside}, indent=2))
    return 1 if mismatches or changed_outside else 0


if __name__ == "__main__":
    raise SystemExit(main())
