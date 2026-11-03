#!/usr/bin/env python3
"""Differentially exercise the full 0x00286928 C++ candidate under Unicorn."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import struct
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
import sys

from unicorn import (Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE,
                     UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE)
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

OUT = ROOT / "build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix/run001/checks/default"
SRC = ROOT / "experiments/semantic_equivalence/h2_86928_candidate.cpp"
PRODUCTION_SRC = ROOT / "src/engine/leaf_batch45_a.cpp"
IMAGE = (ROOT / "extracted/exefs/code.bin").read_bytes()
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ENTRY = 0x00286928
SPAN = 820
TEXT = 0x00100000
STOP = 0x0080F000
OBJECTS = (0x00910000, 0x00912000, 0x00914000)
SERVICE = 0x00940000
GLOBAL_OBJECT = 0x00950000
TARGETS = {
    0x002C1F28: 0, 0x002B89A0: 0, 0x002B8D24: 2,
    0x0028E974: 7, 0x002B787C: 1, 0x0028DF98: 2,
    0x002C4BF0: 2, 0x002B90F0: 2, 0x002F5B2C: 1,
    0x002D65B4: 1, 0x0028DF70: 1, 0x002B8CCC: 0,
    0x002B8B78: 1, 0x002B8584: 1, 0x0028DF54: 1,
    0x0028DF3C: 1, 0x0028DF0C: 1,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(uc: Uc, addr: int) -> int:
    return struct.unpack("<I", uc.mem_read(addr, 4))[0]


@dataclass(frozen=True)
class Case:
    seed: int
    selector: int
    incoming_r2: int
    state: int
    state_2e: int = 0
    state_35: int = 1
    row: int = 6
    arg5: int = 0
    arg6: int = 0
    query_a: int = 0
    query_b: int = 0
    service_state: int = 0
    alias_default: bool = False
    object_pointer: int = GLOBAL_OBJECT
    mutate_object_pointer: bool = False
    replacement_pointer: int = 0x00958000


def compile_function(path: Path, symbol: str, output_name: str) -> tuple[bytes, list]:
    obj = OUT / output_name
    result = compile_tu_armv6k(path, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)[symbol]
    rows = {row["name"]: int(row["address"], 0)
            for row in csv.DictReader((ROOT / "config/functions.csv").open(encoding="utf-8"))}
    fixed = bytearray(body)
    for reloc in relocs:
        if reloc.explicit_addend is not None:
            raise ValueError(f"unsupported candidate relocation: {reloc}")
        if reloc.relocation_type == 2 and not reloc.symbol_name:
            local_target = struct.unpack_from("<I", fixed, reloc.offset)[0]
            if local_target >= len(fixed):
                raise ValueError(f"local reference leaves candidate body: {local_target:#x}")
            struct.pack_into("<I", fixed, reloc.offset, ENTRY + local_target)
            continue
        if reloc.relocation_type != 28:
            raise ValueError(f"unsupported candidate relocation: {reloc}")
        if reloc.symbol_name not in rows:
            raise ValueError(f"candidate call target is absent from ledger: {reloc.symbol_name}")
        target = rows[reloc.symbol_name]
        if target & 1:
            raise ValueError(f"ARM BL target unexpectedly has Thumb bit: {target:#x}")
        place = ENTRY + reloc.offset
        instruction = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if instruction & 0xFF000000 != 0xEB000000:
            raise ValueError(f"R_ARM_CALL is not an unconditional ARM BL: {instruction:#x}")
        displacement = target - (place + 8)
        if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
            raise ValueError(f"ARM BL target is unaligned or out of range: {target:#x}")
        struct.pack_into("<I", fixed, reloc.offset,
                         (instruction & 0xFF000000) | ((displacement >> 2) & 0x00ffffff))
    if len(fixed) % 4:
        raise ValueError("function tail cannot be padded with ARM NOPs")
    return bytes(fixed), relocs


def fixture(case: Case, code: bytes | None = None, image: bytes = IMAGE):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(TEXT, 0x00500000)
    u.mem_write(TEXT, image)
    if code is not None:
        u.mem_write(ENTRY, code)
    u.mem_map(0x00800000, 0x00010000)
    u.mem_map(0x00900000, 0x00060000)
    rng = random.Random(case.seed)
    for base in OBJECTS:
        data = bytearray(rng.randrange(256) for _ in range(0x1800))
        data[8] = case.state
        data[9] = case.row
        data[0x2e] = case.state_2e
        data[0x35] = case.state_35
        struct.pack_into("<I", data, 4, case.object_pointer)
        struct.pack_into("<I", data, 0x18, 0x13572468)
        u.mem_write(base, bytes(data))
    table = bytearray(u.mem_read(0x0043E188, 0x20))
    default_ptr = OBJECTS[0]
    special_ptr = default_ptr if case.alias_default else OBJECTS[1]
    selector12_ptr = OBJECTS[2]
    struct.pack_into("<III", table, 4, default_ptr, special_ptr, selector12_ptr)
    u.mem_write(0x0043E188, bytes(table))
    u.mem_write(0x0043E0BC, struct.pack("<i", -1 if case.query_a else 0))
    u.mem_write(0x0043E0B8, struct.pack("<I", case.query_a & 0xff))
    u.mem_write(0x0044DC20, struct.pack("<I", SERVICE))
    u.mem_write(SERVICE + 0x352c, struct.pack("<I", 0x14 if case.query_b else 0))
    u.mem_write(0x0044DEB8, struct.pack("<I", SERVICE))
    u.mem_write(GLOBAL_OBJECT, bytes(0x1000))
    struct.pack_into("<I", u.mem_read(0x0044DE98 + 0x20, 4), 0, SERVICE)
    u.mem_write(0x0044DE98 + 0x20, struct.pack("<I", SERVICE))
    # Set the service state byte used by an intentionally simple stub.
    u.mem_write(SERVICE + 0x08, bytes([case.service_state & 0xff]))
    sp = 0x0080FF00
    u.reg_write(UC_ARM_REG_SP, sp)
    u.mem_write(sp, struct.pack("<II", case.arg5, case.arg6))
    u.reg_write(UC_ARM_REG_LR, STOP)
    u.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    u.reg_write(UC_ARM_REG_D8, 0x1122334455667788)
    u.reg_write(UC_ARM_REG_R0, 0x12345678)
    u.reg_write(UC_ARM_REG_R1, 0x87654321)
    u.reg_write(UC_ARM_REG_R2, case.incoming_r2)
    u.reg_write(UC_ARM_REG_R3, case.selector)
    for i, reg in enumerate((UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                             UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)):
        u.reg_write(reg, 0x22330000 + i)
    return u


def run(case: Case, code: bytes | None = None, callback: bool = False,
        callback_first_result: int = 0, image: bytes = IMAGE):
    u = fixture(case, code, image)
    events, writes, reads, trace = [], [], [], []
    done = False
    getter_calls = 0

    def on_code(uc, address, size, _):
        nonlocal done, getter_calls
        if address == STOP:
            done = True
            uc.emu_stop()
            return
        if callback and address == 0x00286928:
            stack_args = struct.unpack("<II", uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 8))
            events.append((address,
                           tuple(uc.reg_read(reg) for reg in
                                 (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)),
                           stack_args))
            trace.append(("helper_entry", address, events[-1][1], stack_args))
            return
        if callback and address in (0x00289640, 0x0028686C, 0x00296F60):
            args = tuple(uc.reg_read(reg) for reg in
                         (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            events.append((address, args, ()))
            trace.append(("call", address, args, ()))
            if address == 0x00289640:
                result = callback_first_result if getter_calls == 0 else case.incoming_r2
                getter_calls += 1
            elif address == 0x0028686C:
                result = 0x12003456
            else:
                result = 0x87654321
            uc.reg_write(UC_ARM_REG_R0, result & 0xffffffff)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            return
        argc = TARGETS.get(address)
        if argc is None:
            return
        args = tuple(uc.reg_read(reg) for reg in
                     (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)[:min(argc, 4)])
        stack_args = ()
        if address == 0x0028E974:
            stack_args = struct.unpack("<III", uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 12))
        events.append((address, args, stack_args))
        trace.append(("call", address, args, stack_args))
        if address == 0x002C1F28:
            result = (uc.reg_read(UC_ARM_REG_R0) & 0xffffffff)
            signed = struct.unpack("<i", uc.mem_read(0x0043E0BC, 4))[0]
            result = (struct.unpack("<b", uc.mem_read(0x0043E0B8, 1))[0] & 0xffffffff) if signed < 0 else 0
        elif address == 0x002B89A0:
            ptr = u32(uc, 0x0044DC20)
            result = 1 if ptr == 0 or u32(uc, ptr + 0x352c) == 0x14 else 0
        elif address == 0x0028DF54:
            ptr = u32(uc, 0x0044DEB8)
            uc.mem_write(ptr + 0x3b, b"\0")
            uc.mem_write(ptr + 0xa8, struct.pack("<I", args[0]))
            result = args[0]
        elif address == 0x0028DF3C:
            uc.mem_write(0x0043E0BC, struct.pack("<I", 0))
            result = args[0]
        elif address == 0x002B787C:
            result = 0x12344321
        elif address == 0x002F5B2C:
            result = 0x20 + args[0]
        elif address == 0x002D65B4:
            result = 0x140 + args[0]
        elif address == 0x0028DF70:
            result = 5 if case.service_state else 4
        elif address == 0x002B8CCC:
            result = 0x5a
        elif address == 0x0028E974:
            result = 0x87654321
        elif address == 0x002B8D24:
            result = args[0]
        elif address == 0x002C4BF0 and case.mutate_object_pointer:
            uc.mem_write(OBJECTS[0] + 4, struct.pack("<I", case.replacement_pointer))
            result = 0
        else:
            result = 0
        uc.reg_write(UC_ARM_REG_R0, result & 0xffffffff)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def on_write(uc, kind, address, size, value, _):
        if not 0x0080F000 <= address < 0x00810000:
            writes.append((address, size, value & 0xffffffff))
            if address in (OBJECTS[0] + 4, OBJECTS[1] + 4, OBJECTS[2] + 4):
                trace.append(("write", address, size, value & 0xffffffff))

    def on_read(uc, kind, address, size, value, _):
        if address in (OBJECTS[0] + 4, OBJECTS[1] + 4, OBJECTS[2] + 4):
            observed = int.from_bytes(uc.mem_read(address, size), "little")
            event = (address, size, observed & 0xffffffff)
            reads.append(event)
            trace.append(("read", *event))

    u.hook_add(UC_HOOK_CODE, on_code)
    u.hook_add(UC_HOOK_MEM_WRITE, on_write)
    u.hook_add(UC_HOOK_MEM_READ, on_read)
    fault = None
    try:
        u.emu_start(0x00221168 if callback else ENTRY, 0, count=10000)
    except UcError as error:
        fault = str(error)
    regs = tuple(u.reg_read(r) for r in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                 UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10,
                 UC_ARM_REG_R11, UC_ARM_REG_D8))
    selected = OBJECTS[2] if case.selector == 12 else (
        OBJECTS[1] if case.selector in (11, 13, 14, 15) and not case.alias_default else OBJECTS[0])
    memories = tuple(bytes(u.mem_read(base, 0x1800)) for base in OBJECTS)
    memories += (bytes(u.mem_read(SERVICE, 0x4000)), bytes(u.mem_read(GLOBAL_OBJECT, 0x1000)))
    state = (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP), regs,
             tuple(events), tuple(writes), memories, fault, done,
             tuple(reads), tuple(trace))
    return state


def directed_cases():
    selectors = list(range(21)) + [0x80000000, 0xffffffff]
    cases = []
    for selector in selectors:
        for r2 in (0, 1):
            for state in (0, 1, 3, 4, 5, 6):
                cases.append(Case(17, selector, r2, state,
                                  state_2e=(state + selector) & 1,
                                  state_35=(state + 1) & 1,
                                  row=(selector + state) & 0xff,
                                  arg5=(selector + state) & 1,
                                  arg6=(selector * 0x1020304 + state) & 0xffffffff,
                                  query_a=(selector + state) & 1,
                                  query_b=(selector ^ state) & 1,
                                  service_state=(selector + state) & 1))
    for seed in (4729, 20261101):
        for selector in (11, 12, 13, 15, 19):
            for r2 in (0, 1):
                cases.append(Case(seed, selector, r2, 0, state_2e=0, state_35=0,
                                  row=8, arg5=1, arg6=0xffffffff, query_a=1,
                                  query_b=1, service_state=1,
                                  alias_default=(seed == 20261101)))
    return cases


def pointer_timing_cases():
    return [
        Case(20261121, 6, 0, 0, state_2e=0, state_35=1, row=6,
             arg5=0, arg6=0, query_a=0, object_pointer=0xDEAD0000),
        Case(20261121, 6, 0, 0, state_2e=0, state_35=1, row=6,
             arg5=1, arg6=0, query_a=0, object_pointer=GLOBAL_OBJECT,
             mutate_object_pointer=True),
        Case(20261121, 6, 0, 0, state_2e=0, state_35=1, row=6,
             arg5=0x100, arg6=0, query_a=0, object_pointer=GLOBAL_OBJECT,
             mutate_object_pointer=True),
    ]


def slot_image(body: bytes) -> bytes:
    if len(body) > SPAN:
        raise ValueError(f"candidate body exceeds original slot: {len(body)}/{SPAN}")
    if len(body) % 4 or (SPAN - len(body)) % 4:
        raise ValueError("candidate body or slot tail is not ARM-word aligned")
    return body + struct.pack("<I", 0xe320f000) * ((SPAN - len(body)) // 4)


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path,
                        default=Path("build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix/run001/checks/default"))
    args = parser.parse_args()
    OUT = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    if sha(IMAGE) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    body, relocations = compile_function(SRC, "candidate_00286928", "candidate.o")
    production_body, production_relocations = compile_function(
        PRODUCTION_SRC, "engine_func_00286928", "production.o")
    if len(body) != len(production_body):
        raise SystemExit(f"candidate/production size mismatch: {len(body)} vs {len(production_body)}")
    if len(body) > SPAN:
        raise SystemExit(f"candidate body exceeds slot: {len(body)}/{SPAN}")
    candidate = slot_image(body)
    production = slot_image(production_body)
    cases = directed_cases()
    for i, case in enumerate(cases):
        original = run(case)
        converted = run(case, candidate)
        if original != converted:
            raise AssertionError(f"differential mismatch case {i}: {case}")
        compiled_production = run(case, production)
        if original != compiled_production:
            raise AssertionError(f"production differential mismatch case {i}: {case}")

    pointer_cases = pointer_timing_cases()
    pointer_results = []
    for case in pointer_cases:
        original = run(case)
        converted = run(case, candidate)
        compiled_production = run(case, production)
        if original != converted or original != compiled_production:
            raise AssertionError(f"pointer timing mismatch: {case}")
        ptr_reads = original[8]
        calls = [event for event in original[3] if event[0] in (0x002C4BF0, 0x002B90F0)]
        if case.arg5 == 0:
            if ptr_reads or calls:
                raise AssertionError(f"arg5=0 read/call was not skipped: reads={ptr_reads}, calls={calls}")
        else:
            if ptr_reads != ((OBJECTS[0] + 4, 4, GLOBAL_OBJECT),
                             (OBJECTS[0] + 4, 4, case.replacement_pointer)):
                raise AssertionError(f"expected first read and post-mutation reload, got {ptr_reads}")
            if calls != [(0x002C4BF0, (GLOBAL_OBJECT, 0x20), ()),
                         (0x002B90F0, (case.replacement_pointer, 0x40), ())]:
                raise AssertionError(f"wrong pointer helper call arguments: {calls}")
        pointer_results.append({
            "arg5": hex(case.arg5),
            "object_plus4_value": hex(case.object_pointer),
            "reads": [[hex(a), n, hex(v)] for a, n, v in ptr_reads],
            "calls": [[hex(a), [hex(x) for x in regs], [hex(x) for x in stack]]
                      for a, regs, stack in calls],
            "replacement_value": hex(case.replacement_pointer if case.mutate_object_pointer else case.object_pointer),
            "candidate_and_production_match_original": True,
        })

    callback_cases = []
    for seed in (17, 4729):
        callback_cases.append((Case(seed, 6, 0, 1, state_2e=0, state_35=1,
                                    row=8, arg5=0, arg6=0), 0))
        callback_cases.append((Case(seed, 6, 1, 4, state_2e=0, state_35=1,
                                    row=8, arg5=0, arg6=0), 1))
    callback_cases.append((Case(20261121, 6, 0, 0, state_2e=0, state_35=1,
                                row=6, arg5=0, arg6=0, query_a=0,
                                mutate_object_pointer=True), 0))
    for i, (case, first_getter) in enumerate(callback_cases):
        original = run(case, callback=True, callback_first_result=first_getter)
        converted = run(case, candidate, callback=True, callback_first_result=first_getter)
        compiled_production = run(case, production, callback=True,
                                  callback_first_result=first_getter)
        if original != converted or original != compiled_production:
            raise AssertionError(f"0x00221168 caller mismatch case {i}: {case}")
        helper = next(event for event in converted[3] if event[0] == ENTRY)
        expected = (0x12003456, 0x87654321, case.incoming_r2, 6)
        if helper[1] != expected or helper[2] != (1, 0):
            raise AssertionError(f"callback supplied wrong helper ABI: {helper}")

    source_text = SRC.read_text(encoding="utf-8")
    controls = {
        "mode_11": ("mode = flag;", "mode = 0;",
                    Case(17, 11, 1, 4)),
        "selector15_prewrite": ("initial_byte = raw_selector == 13 || raw_selector == 15;",
                                "initial_byte = 0;", Case(17, 15, 1, 4)),
        "selector19_pointer": ("const bool remap_to_special = selector_11_to_15 || raw_selector == 19;",
                               "const bool remap_to_special = selector_11_to_15;",
                               Case(17, 19, 1, 4)),
        "r2_zero_state_call": ("battle_func_002b8d24(object, object[9]);", "(void)object;",
                               Case(17, 0, 0, 1, state_2e=0)),
        "df54_value": ("battle_func_0028df54(*reinterpret_cast<volatile uint32_t*>(object + 0x18));",
                       "battle_func_0028df54(0);", Case(17, 11, 1, 5, state_2e=0)),
        "six_iteration_loop": ("i != 6", "i != 5",
                               Case(17, 0, 0, 0, state_2e=0, query_a=0, query_b=0)),
        "unconditional_p4_read": (
            "if (arg5 != 0) {\n        uint32_t global_object = *reinterpret_cast<volatile uint32_t*>(object + 4);",
            "uint32_t global_object = *reinterpret_cast<volatile uint32_t*>(object + 4);\n    if (arg5 != 0) {",
            pointer_cases[0]),
        "stale_pointer_after_2c4bf0": (
            "global_object = *reinterpret_cast<volatile uint32_t*>(object + 4);\n        func_002b90f0(global_object, 0x40);",
            "func_002b90f0(global_object, 0x40);",
            pointer_cases[1]),
    }
    detected = {}
    mutation_counterexamples = {}
    for name, (old, new, control_case) in controls.items():
        count = source_text.count(old)
        expected_count = 2 if name == "r2_zero_state_call" else 2 if name == "df54_value" else 1
        if count != expected_count:
            raise AssertionError(f"control {name} source anchor count {count}, expected {expected_count}")
        replacement_count = 2 if name == "r2_zero_state_call" else 1
        mutant_source = OUT / f"mutant-{name}.cpp"
        mutant_source.write_text(source_text.replace(old, new, replacement_count), encoding="utf-8")
        mutant_body, _ = compile_function(mutant_source, "candidate_00286928",
                                          f"mutant-{name}.o")
        if mutant_body == body:
            raise AssertionError(f"control {name} did not change compiled body")
        mutant = slot_image(mutant_body)
        try:
            original = run(control_case)
            mutated = run(control_case, mutant)
            detected[name] = original != mutated
            if name == "unconditional_p4_read":
                mutation_counterexamples[name] = {
                    "arg5": hex(control_case.arg5),
                    "original_p4_reads": original[8],
                    "mutant_p4_reads": mutated[8],
                }
            if name == "stale_pointer_after_2c4bf0":
                old_call = next(event for event in mutated[3] if event[0] == 0x002B90F0)
                new_call = next(event for event in original[3] if event[0] == 0x002B90F0)
                if old_call[1][0] != GLOBAL_OBJECT or new_call[1][0] != control_case.replacement_pointer:
                    raise AssertionError(f"stale pointer counterexample missing: old={old_call}, original={new_call}")
                mutation_counterexamples[name] = {
                    "arg5": hex(control_case.arg5),
                    "original_0x002B90F0_args": [hex(value) for value in new_call[1]],
                    "stale_mutant_0x002B90F0_args": [hex(value) for value in old_call[1]],
                    "original_reads": [[hex(a), n, hex(v)] for a, n, v in original[8]],
                    "stale_mutant_reads": [[hex(a), n, hex(v)] for a, n, v in mutated[8]],
                }
        except UcError:
            detected[name] = True
        if not detected[name]:
            raise AssertionError(f"negative control was not detected: {name}")

    ledger = {row["name"]: int(row["address"], 0)
              for row in csv.DictReader((ROOT / "config/functions.csv").open(encoding="utf-8"))}
    def relocation_rows_for(items):
        rows = []
        for reloc in items:
            target = ledger[reloc.symbol_name]
            if target & 1:
                raise AssertionError(f"non-ARM call target: {reloc.symbol_name} {target:#x}")
            rows.append({"offset": reloc.offset, "type": reloc.relocation_type,
                         "symbol": reloc.symbol_name, "target": hex(target),
                         "target_state": "ARM"})
        return rows
    candidate_relocation_rows = relocation_rows_for(relocations)
    production_relocation_rows = relocation_rows_for(production_relocations)
    if candidate_relocation_rows != production_relocation_rows:
        raise AssertionError("candidate and production relocation sets differ")
    report = {
        "schema_version": 1,
        "function": "0x00286928",
        "reference_image_sha256": sha(IMAGE),
        "candidate_source_sha256": sha(SRC.read_bytes()),
        "production_source_sha256": sha(PRODUCTION_SRC.read_bytes()),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "candidate_object_sha256": sha((OUT / "candidate.o").read_bytes()),
        "production_object_sha256": sha((OUT / "production.o").read_bytes()),
        "compiled_body_bytes": len(body),
        "compiled_body_sha256": sha(body),
        "production_body_bytes": len(production_body),
        "production_body_sha256": sha(production_body),
        "slot_bytes": SPAN,
        "nop_tail_bytes": SPAN - len(body),
        "relocations": candidate_relocation_rows,
        "production_relocations": production_relocation_rows,
        "direct_cases": len(cases),
        "targeted_pointer_cases": pointer_results,
        "real_callback_compositions": len(callback_cases),
        "callback_address": "0x00221168",
        "negative_controls": detected,
        "mutation_counterexamples": mutation_counterexamples,
        "production_direct_and_callback_match": True,
        "call_trace_includes": ["0x002C4BF0", "0x002B90F0"],
        "read_trace_scope": "ordered P+4 reads, P+4 writes by mutating stub, and helper calls; all writes and final state are also compared",
        "evidence": "original ARM versus compiled C++; every direct callee and callback getter is intercepted by deterministic stubs; callback body itself is original pinned ARM",
        "limitations": [
            "Does not execute original direct callee bodies; 0x002B8D24 in particular is stubbed.",
            "Caller coverage is limited to callback 0x00221168 with synthetic getter returns and valid fixture RAM.",
            "No runtime/emulator or whole-game equivalence claim."
        ]
    }
    report_path = OUT / "offline-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {len(cases)} direct cases, {len(pointer_cases)} pointer cases, and {len(callback_cases)} 0x00221168 compositions across original/candidate/production; controls {detected}; body {len(body)}/{SPAN}; {len(candidate_relocation_rows)} ARM calls")
    print(f"REPORT {report_path.relative_to(ROOT)} SHA256 {sha(report_path.read_bytes())}")


if __name__ == "__main__":
    main()
