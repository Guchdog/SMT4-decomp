#!/usr/bin/env python3
"""Differentially exercise the full 0x00286928 C++ candidate under Unicorn."""
from __future__ import annotations

import csv
import hashlib
import json
import random
import struct
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
import sys

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

OUT = ROOT / "build/agent-work/H2-semantic/h2-helper-00286928-convert/run001"
SRC = ROOT / "experiments/semantic_equivalence/h2_86928_candidate.cpp"
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


def compile_candidate(path: Path = SRC, output_name: str = "candidate.o") -> bytes:
    obj = OUT / output_name
    result = compile_tu_armv6k(path, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)["candidate_00286928"]
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
    return bytes(fixed)


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
        struct.pack_into("<I", data, 4, GLOBAL_OBJECT)
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
    events, writes = [], []
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
            return
        if callback and address in (0x00289640, 0x0028686C, 0x00296F60):
            args = tuple(uc.reg_read(reg) for reg in
                         (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            events.append((address, args, ()))
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
        else:
            result = 0
        uc.reg_write(UC_ARM_REG_R0, result & 0xffffffff)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def on_write(uc, kind, address, size, value, _):
        if not 0x0080F000 <= address < 0x00810000:
            writes.append((address, size, value & 0xffffffff))

    u.hook_add(UC_HOOK_CODE, on_code)
    u.hook_add(UC_HOOK_MEM_WRITE, on_write)
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
             tuple(events), tuple(writes), memories, fault, done)
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


def slot_image(body: bytes) -> bytes:
    if len(body) > SPAN:
        raise ValueError(f"candidate body exceeds original slot: {len(body)}/{SPAN}")
    if len(body) % 4 or (SPAN - len(body)) % 4:
        raise ValueError("candidate body or slot tail is not ARM-word aligned")
    return body + struct.pack("<I", 0xe320f000) * ((SPAN - len(body)) // 4)


def main():
    if sha(IMAGE) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    body = compile_candidate()
    if len(body) != 812:
        raise SystemExit(f"reviewed candidate size changed: {len(body)}")
    candidate = slot_image(body)
    cases = directed_cases()
    for i, case in enumerate(cases):
        original = run(case)
        converted = run(case, candidate)
        if original != converted:
            raise AssertionError(f"differential mismatch case {i}: {case}")
    callback_cases = []
    for seed in (17, 4729):
        callback_cases.append((Case(seed, 6, 0, 1, state_2e=0, state_35=1,
                                    row=8, arg5=0, arg6=0), 0))
        callback_cases.append((Case(seed, 6, 1, 4, state_2e=0, state_35=1,
                                    row=8, arg5=0, arg6=0), 1))
    for i, (case, first_getter) in enumerate(callback_cases):
        original = run(case, callback=True, callback_first_result=first_getter)
        converted = run(case, candidate, callback=True, callback_first_result=first_getter)
        if original != converted:
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
    }
    detected = {}
    for name, (old, new, control_case) in controls.items():
        count = source_text.count(old)
        expected_count = 2 if name == "r2_zero_state_call" else 2 if name == "df54_value" else 1
        if count != expected_count:
            raise AssertionError(f"control {name} source anchor count {count}, expected {expected_count}")
        replacement_count = 2 if name == "r2_zero_state_call" else 1
        mutant_source = OUT / f"mutant-{name}.cpp"
        mutant_source.write_text(source_text.replace(old, new, replacement_count), encoding="utf-8")
        mutant_body = compile_candidate(mutant_source, f"mutant-{name}.o")
        if mutant_body == body:
            raise AssertionError(f"control {name} did not change compiled body")
        mutant = slot_image(mutant_body)
        try:
            detected[name] = run(control_case) != run(control_case, mutant)
        except UcError:
            detected[name] = True
        if not detected[name]:
            raise AssertionError(f"negative control was not detected: {name}")

    obj = OUT / "candidate.o"
    _raw_body, relocations = extract_elf_functions_detailed(obj)["candidate_00286928"]
    ledger = {row["name"]: int(row["address"], 0)
              for row in csv.DictReader((ROOT / "config/functions.csv").open(encoding="utf-8"))}
    relocation_rows = []
    for reloc in relocations:
        target = ledger[reloc.symbol_name]
        relocation_rows.append({"offset": reloc.offset, "type": reloc.relocation_type,
                                "symbol": reloc.symbol_name, "target": hex(target),
                                "target_state": "ARM" if target & 1 == 0 else "Thumb"})
    report = {
        "schema_version": 1,
        "function": "0x00286928",
        "reference_image_sha256": sha(IMAGE),
        "candidate_source_sha256": sha(SRC.read_bytes()),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "object_sha256": sha(obj.read_bytes()),
        "compiled_body_bytes": len(body),
        "compiled_body_sha256": sha(body),
        "slot_bytes": SPAN,
        "nop_tail_bytes": SPAN - len(body),
        "relocations": relocation_rows,
        "direct_cases": len(cases),
        "real_callback_compositions": len(callback_cases),
        "callback_address": "0x00221168",
        "negative_controls": detected,
        "evidence": "original ARM versus compiled C++; every direct callee and callback getter is intercepted by deterministic stubs; callback body itself is original pinned ARM",
        "limitations": [
            "Does not execute original direct callee bodies; 0x002B8D24 in particular is stubbed.",
            "Caller coverage is limited to callback 0x00221168 with synthetic getter returns and valid fixture RAM.",
            "No runtime/emulator or whole-game equivalence claim."
        ]
    }
    report_path = OUT / "offline-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {len(cases)} direct cases and {len(callback_cases)} real 0x00221168 callback compositions; negative controls {detected}; all dependency calls are contract-scoped stubs; body {len(body)}/{SPAN} bytes, 22 ARM calls relocated")
    print(f"REPORT {report_path.relative_to(ROOT)} SHA256 {sha(report_path.read_bytes())}")


if __name__ == "__main__":
    main()
