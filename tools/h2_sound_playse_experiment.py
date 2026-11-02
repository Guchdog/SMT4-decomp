#!/usr/bin/env python3
"""Final-VMA differential and caller slices for H2 Sound_PlaySE."""
from __future__ import annotations

import argparse
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
SOURCE = ROOT / "src/engine/leaf_batch32_c.cpp"
ENTRY, SLOT = 0x002B8B78, 340
ROOT_MANAGER = 0x0043DA28
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00020000
OBJECT, ALT_OBJECT = DATA_BASE + 0x0000, DATA_BASE + 0x2000
OLD_PROFILE, NEW_PROFILE = DATA_BASE + 0x4000, DATA_BASE + 0x6000
OBJECT_SIZE = 0x1000
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000
U32 = 0xFFFFFFFF
PRIORITIES = bytes((5, 6, 4, 3, 2, 1))
PRIORITY_TABLE = 0x00402550

CALLEES = {
    "ui_func_002b85bc": 0x002B85BC,
    "camp_func_002aea28": 0x002AEA28,
    "camp_func_002b8794": 0x002B8794,
    "script_vm_func_0013851c": 0x0013851C,
    "camp_func_002ae874": 0x002AE874,
}
CALL_ARGUMENT_COUNTS = {
    CALLEES["ui_func_002b85bc"]: 1,
    CALLEES["camp_func_002aea28"]: 1,
    CALLEES["camp_func_002b8794"]: 4,
    CALLEES["script_vm_func_0013851c"]: 1,
    CALLEES["camp_func_002ae874"]: 1,
}


@dataclass(frozen=True)
class Case:
    seed: int
    request: int = 0xDC
    current: int = 7
    latch: int = 0
    occupied_index: int = -1
    old_lookup: int = OLD_PROFILE
    new_lookup: int = NEW_PROFILE
    old_enabled: int = 1
    new_enabled: int = 1
    profile_values: tuple[int, ...] = (1, 0x100, 0, 0xFFFF, 2, 0)
    switch_on_prepare: bool = False
    switch_on_apply: bool = False
    object_address: int = OBJECT


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def function_rows():
    import csv
    with (ROOT / "config/functions.csv").open(encoding="utf-8-sig", newline="") as handle:
        return {row["name"]: int(row["address"], 0) for row in csv.DictReader(handle)}


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / source.name.replace(".cpp", ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "affected TU compile failed")
    body, relocations = extract_elf_functions_detailed(obj)["script_vm_func_002b8b78"]
    if len(body) > SLOT or len(body) % 4:
        raise ValueError(f"function body does not fit its ARM slot: {len(body)}/{SLOT}")
    return body, relocations, list(result.args), obj


def stage_image(original: bytes, body: bytes, relocations):
    fixed = bytearray(body)
    rows = function_rows()
    resolved = []
    for relocation in relocations:
        instruction = struct.unpack_from("<I", fixed, relocation.offset)[0]
        if relocation.relocation_type in (28, 29):
            if relocation.symbol_name not in rows:
                raise ValueError(f"unknown call target {relocation.symbol_name!r}")
            target = rows[relocation.symbol_name]
            place = ENTRY + relocation.offset
            displacement = target - (place + 8)
            if target & 1 or displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
                raise ValueError(f"invalid ARM branch relocation: {relocation}")
            expected = 0xEB000000 if relocation.relocation_type == 28 else 0xEA000000
            if instruction & 0xFF000000 != expected:
                raise ValueError(f"unexpected branch opcode at {relocation.offset:#x}: {instruction:#x}")
            struct.pack_into("<I", fixed, relocation.offset,
                             (instruction & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF))
            resolved.append({"offset": relocation.offset, "type": relocation.relocation_type,
                             "symbol": relocation.symbol_name, "target": hex(target)})
        elif relocation.relocation_type == 2 and not relocation.symbol_name:
            table_offset = PRIORITY_TABLE - CODE_BASE
            if original[table_offset:table_offset + len(PRIORITIES)] != PRIORITIES:
                raise ValueError("pinned original priority table changed")
            struct.pack_into("<I", fixed, relocation.offset, PRIORITY_TABLE)
            resolved.append({"offset": relocation.offset, "type": 2, "symbol": "local priority bytes",
                             "target": hex(PRIORITY_TABLE), "verified_bytes": PRIORITIES.hex()})
        else:
            raise ValueError(f"unsupported function relocation: {relocation}")

    if len(fixed) > SLOT:
        raise ValueError("compiled body no longer fits the function slot")
    payload = bytearray(b"\0" * SLOT)
    payload[:len(fixed)] = fixed
    image = bytearray(original)
    offset = ENTRY - CODE_BASE
    image[offset:offset + SLOT] = payload
    staged = bytes(image)
    patch = encode_ips([(offset, bytes(payload))], len(original))
    if apply_ips(original, patch) != staged:
        raise AssertionError("entry-slot IPS replay mismatch")
    return staged, patch, bytes(payload), resolved


class Machine:
    def __init__(self, image: bytes, case: Case):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(STACK, STACK_SIZE)
        self.case = case
        rng = random.Random(case.seed)
        initial = bytearray(rng.randrange(256) for _ in range(OBJECT_SIZE))
        initial[0x4C9] = case.current & 0xFF
        initial[0x4C5] = 0xA5
        if case.occupied_index >= 0:
            initial[0x4B8 + case.occupied_index] = 1
        self.uc.mem_write(OBJECT, bytes(initial))
        self.uc.mem_write(ALT_OBJECT, bytes((0x5A + i) & 0xFF for i in range(OBJECT_SIZE)))
        old_data = bytearray((0x31 + i * 11) & 0xFF for i in range(0x1000))
        new_data = bytearray((0x71 + i * 13) & 0xFF for i in range(0x1000))
        struct.pack_into("<H", old_data, 0x0C, case.old_enabled)
        struct.pack_into("<H", new_data, 0x0C, case.new_enabled)
        for i, value in enumerate(case.profile_values[:6]):
            struct.pack_into("<H", new_data, i * 2, value & 0xFFFF)
        self.uc.mem_write(OLD_PROFILE, bytes(old_data))
        self.uc.mem_write(NEW_PROFILE, bytes(new_data))
        self.uc.mem_write(ROOT_MANAGER + 4, struct.pack("<I", case.object_address & U32))
        self.uc.mem_write(ROOT_MANAGER + 0x10, struct.pack("<I", case.latch & U32))
        self.events = []
        self.writes = []
        self.lookup_index = 0
        self.stop = STOP

        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_write(self, _uc, _access, address, size, value, _data):
        if not STACK <= address < STACK + STACK_SIZE:
            self.writes.append((address, size, value & U32))

    def _on_code(self, uc, address, _size, _data):
        if address == self.stop:
            uc.emu_stop()
            return
        if address not in CALLEES.values():
            return
        args = tuple(uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                     for i in range(CALL_ARGUMENT_COUNTS[address]))
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        self.events.append({"address": address, "args": args, "sp_aligned": (sp & 7) == 0})
        if address == CALLEES["camp_func_002aea28"]:
            result = (self.case.old_lookup if self.lookup_index == 0 else self.case.new_lookup)
            self.lookup_index += 1
        elif address == CALLEES["camp_func_002b8794"]:
            result = 0xB8794000 | (args[0] & 0xFFFF)
            if args[0] == 5 and self.case.switch_on_apply:
                uc.mem_write(ROOT_MANAGER + 4, struct.pack("<I", ALT_OBJECT))
        elif address == CALLEES["ui_func_002b85bc"]:
            result = 0x85BC0001
            if self.case.switch_on_prepare:
                uc.mem_write(ROOT_MANAGER + 4, struct.pack("<I", ALT_OBJECT))
        elif address == CALLEES["script_vm_func_0013851c"]:
            result = 0x13851000 | (args[0] & 0xFFFF)
        elif address == CALLEES["camp_func_002ae874"]:
            result = 0xAE870000 | (args[0] & 0xFFFF)
        else:
            result = 0
        uc.reg_write(arm.UC_ARM_REG_R0, result & U32)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def run(self, start: int = ENTRY, stop: int = STOP):
        self.stop = stop
        regs = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13)]
        initial = [(0xA1000000 + i * 0x01010101) & U32 for i in range(13)]
        for reg, value in zip(regs, initial):
            self.uc.reg_write(reg, value)
        self.uc.reg_write(arm.UC_ARM_REG_R0, self.case.request & U32)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, stop)
        fault = None
        try:
            self.uc.emu_start(start, 0, count=5000)
        except unicorn.UcError as error:
            fault = str(error)
        after_regs = [self.uc.reg_read(reg) for reg in regs]
        return {
            "fault": fault,
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": after_regs[4:12] == initial[4:12],
            "root": bytes(self.uc.mem_read(ROOT_MANAGER, 0x20)).hex(),
            "data": bytes(self.uc.mem_read(DATA_BASE, DATA_SIZE)).hex(),
            "events": self.events.copy(),
            "writes": self.writes.copy(),
        }


def run_case(image: bytes, case: Case):
    machine = Machine(image, case)
    return machine.run()


def directed_cases():
    cases = [
        Case(11, request=7, current=7, latch=-1, occupied_index=3),
        Case(12, request=0xDEADBEEF, current=7, latch=-1, occupied_index=0),
        Case(13, request=0xFFFFFFFF, current=7, latch=-1, occupied_index=5),
        Case(14, request=0xDC, current=7, latch=-1, occupied_index=-1),
        Case(15, request=0xDC, current=7, latch=0, occupied_index=4),
        Case(16, request=0, current=9, latch=0, profile_values=(0, 0, 0, 0, 0, 0)),
        Case(17, request=0xFF, current=9, latch=3),
        Case(18, request=0x100, current=0, latch=0),
        Case(19, request=0x100, current=9, latch=0),
        Case(20, request=0xDC, current=9, latch=0, old_enabled=0, new_enabled=0),
        Case(21, request=0xDC, current=9, latch=0, old_enabled=1, new_enabled=0),
        Case(22, request=0xDC, current=9, latch=0, old_enabled=1, new_enabled=1),
        Case(23, request=0xDC, current=9, latch=0, old_lookup=0, new_lookup=NEW_PROFILE),
        Case(24, request=0xDC, current=9, latch=0, old_lookup=OLD_PROFILE, new_lookup=0),
        Case(25, request=0xDC, current=9, latch=0, old_lookup=0, new_lookup=0),
        Case(26, request=0xDC, current=9, latch=0, switch_on_prepare=True),
        Case(27, request=0xDC, current=9, latch=0, switch_on_apply=True),
        Case(28, request=0x99, current=9, latch=0, profile_values=(0x100, 1, 0, 0xFFFF, 0, 2)),
        Case(29, request=0x100, current=9, latch=0x7FFFFFFF, occupied_index=2),
        Case(30, request=0xFFFFFFFF, current=9, latch=-2, occupied_index=1),
    ]
    # Each final dependency branch must return its raw service result.
    cases.extend((
        Case(31, request=0xDC, current=9, latch=0, old_enabled=0, new_enabled=1),
        Case(32, request=0xDC, current=9, latch=0, old_enabled=1, new_enabled=1),
        Case(33, request=0xDC, current=9, latch=0, old_enabled=1, new_enabled=0),
    ))
    return cases


def run_caller_slice(image: bytes, case: Case, start: int, stop: int):
    # Caller call slices are instruction-pinned below; this executes their real
    # register setup and BL, then stops at the first instruction after the call.
    return run_case(image, case) if start == ENTRY else run_slice(image, case, start, stop)


def run_slice(image: bytes, case: Case, start: int, stop: int):
    machine = Machine(image, case)
    # Start at the original caller instruction sequence, not at a synthetic BL.
    return machine.run(start, stop)


def compile_mutant(out: Path, label: str, before: str, after: str):
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise ValueError(f"mutation anchor {label} is not unique")
    source = out / "mutants" / f"{label}.cpp"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(text.replace(before, after), encoding="utf-8")
    body, relocs, _args, _obj = compile_body(out / "mutants" / label / "compile", source)
    return stage_image(IMAGE.read_bytes(), body, relocs)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")

    body, relocations, compiler_args, obj = compile_body(args.out / "compile")
    staged, patch, payload, resolved = stage_image(original, body, relocations)
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-entry.ips").write_bytes(patch)

    direct_results, mismatches = [], []
    for case in directed_cases():
        ref = run_case(original, case)
        got = run_case(staged, case)
        equal = ref == got
        if not equal:
            mismatches.append({"case": case.__dict__, "original": ref, "candidate": got})
        direct_results.append({"seed": case.seed, "request": hex(case.request), "equal": equal,
                               "fault": got["fault"], "r0": hex(got["r0"]),
                               "events": got["events"]})

    controls = {}
    mutations = {
        "request_compare_truncated": ("static_cast<u32>(selected_profile) == request",
                                      "static_cast<u32>(selected_profile) == static_cast<u8>(request)",
                                      Case(41, request=0x100, current=0, latch=0)),
        "signed_latch_gate": ("if (*latch < 0)", "if (*latch <= 0)",
                              Case(42, request=0xDEADBEEF, current=7, latch=0, occupied_index=2)),
        "request_store_truncated": ("*latch = static_cast<s32>(request);",
                                    "*latch = static_cast<s32>(static_cast<u8>(request));",
                                    Case(43, request=0xDEADBEEF, current=7, latch=-1, occupied_index=2)),
        "default_profile_argument": ("camp_func_002b8794(slot, 0x12u, 0x51u, 0);",
                                      "camp_func_002b8794(slot, 0x12u, 0x52u, 0);",
                                      Case(44, request=0xDC, current=9, latch=0,
                                           profile_values=(0, 0, 0, 0, 0, 0))),
    }
    for label, (before, after, case) in mutations.items():
        mutant = compile_mutant(args.out, label, before, after)
        ref, got = run_case(original, case), run_case(mutant, case)
        detected = ref != got
        controls[label] = {"detected": detected, "case": case.__dict__}
        if not detected:
            mismatches.append({"mutation": label, "original": ref, "mutant": got})

    caller_cases = []
    for label, start, stop, request in (
        ("title_config_initializer_call_0x99", 0x002F4DEC, 0x002F4DF4, 0x99),
        ("nested_callback_call_0xDC", 0x00286B7C, 0x00286B84, 0xDC),
    ):
        case = Case(50 if request == 0x99 else 51, request=request, current=9, latch=0)
        ref = run_caller_slice(original, case, start, stop)
        got = run_caller_slice(staged, case, start, stop)
        equal = ref == got
        if not equal:
            mismatches.append({"caller": label, "original": ref, "candidate": got})
        caller_cases.append({"caller": label, "start": hex(start), "stop": hex(stop),
                             "request": hex(request), "equal": equal, "events": got["events"],
                             "r0": hex(got["r0"]), "fault": got["fault"]})

    changed_outside_slot = any(
        a != b and not (ENTRY - CODE_BASE <= offset < ENTRY - CODE_BASE + SLOT)
        for offset, (a, b) in enumerate(zip(original, staged))
    )
    report = {
        "schema_version": 1,
        "fixture_seeds": [case.seed for case in directed_cases()],
        "image_sha256": sha(original),
        "source_sha256": sha(SOURCE.read_bytes()),
        "object_sha256": sha(obj.read_bytes()),
        "entry": hex(ENTRY),
        "slot_size": SLOT,
        "compiled_body_size": len(body),
        "relocations": resolved,
        "priority_table": hex(PRIORITY_TABLE),
        "priority_table_bytes": PRIORITIES.hex(),
        "exact_matching": body == original[ENTRY - CODE_BASE:ENTRY - CODE_BASE + SLOT],
        "direct_case_count": len(direct_results),
        "direct_cases": direct_results,
        "caller_cases": caller_cases,
        "mutation_controls": controls,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "ips_replay": apply_ips(original, patch) == staged,
        "changed_outside_slot": changed_outside_slot,
        "compiler_command": compiler_args,
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"compiled_body_size": len(body), "relocations": resolved,
                      "direct_case_count": len(direct_results), "caller_cases": caller_cases,
                      "mutation_controls": controls, "mismatch_count": len(mismatches),
                      "ips_replay": report["ips_replay"], "changed_outside_slot": changed_outside_slot}, indent=2))
    return 1 if mismatches or changed_outside_slot else 0


if __name__ == "__main__":
    raise SystemExit(main())
