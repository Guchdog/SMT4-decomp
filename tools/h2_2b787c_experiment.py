#!/usr/bin/env python3
"""Pinned-ARM differential for AsdText_GetLineCount (0x002B787C)."""
from __future__ import annotations

import csv
import hashlib
import json
import random
import struct
from dataclasses import dataclass, field
from pathlib import Path
import sys

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools import h2_86928_experiment as h2_parent

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
IMAGE = IMAGE_PATH.read_bytes()
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SRC = ROOT / "experiments/semantic_equivalence/h2_2b787c_candidate.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-asdtext-line-count-convert/run003"
ENTRY = 0x002B787C
SPAN = 176
CANDIDATE_ENTRY = 0x00800000
STOP = 0x0080F000
TEXT = 0x00100000
HANDLE = 0x00910000
RECORDS = 0x00920000
MAP_TABLE = 0x00464DA8
MAP_SENTINEL = 0xF890
RECORD_STRIDE = 32
RECORD_CAPACITY = 1000
MAP_CAPACITY = 256
CALLEES = {0x002AE6B0, 0x002AE664}
NOP = struct.pack("<I", 0xE320F000)
PARENT_TARGETS = h2_parent.TARGETS


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


@dataclass(frozen=True)
class Case:
    name: str
    start: int = 0
    gate: int = 1
    table_base: int | None = None
    writes: tuple[tuple[int, int], ...] = ()  # (record offset from start, raw u16)
    mappings: tuple[tuple[int, int], ...] = ()  # (raw code, word delta)
    seed: int = 0


def ledger() -> dict[str, int]:
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as f:
        return {row["name"].strip(): int(row["address"], 0) for row in csv.DictReader(f)}


def compile_candidate(path: Path = SRC, output_name: str = "candidate.o",
                      entry: int = CANDIDATE_ENTRY) -> tuple[bytes, list[dict]]:
    OUT.mkdir(parents=True, exist_ok=True)
    obj = OUT / output_name
    result = compile_tu_armv6k(path, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    functions = extract_elf_functions_detailed(obj)
    body, relocs = functions["candidate_002b787c"]
    fixed = bytearray(body)
    rows = ledger()
    reloc_rows = []
    for reloc in relocs:
        if reloc.explicit_addend is not None:
            raise ValueError(f"unsupported explicit-addend relocation: {reloc}")
        if reloc.relocation_type not in (28, 29):
            raise ValueError(f"unsupported candidate relocation: {reloc}")
        if not reloc.symbol_name or reloc.symbol_name not in rows:
            raise ValueError(f"unresolved candidate call relocation: {reloc}")
        target = rows[reloc.symbol_name]
        if target & 1:
            raise ValueError(f"direct ARM call target has Thumb bit set: {target:#x}")
        place = entry + reloc.offset
        instruction = struct.unpack_from("<I", fixed, reloc.offset)[0]
        expected = 0xEB000000 if reloc.relocation_type == 28 else 0xEA000000
        if instruction & 0xFF000000 != expected:
            raise ValueError(f"unexpected branch instruction for relocation: {instruction:#x}")
        displacement = target - (place + 8)
        if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
            raise ValueError(f"ARM branch target is unaligned/out of range: {target:#x}")
        struct.pack_into("<I", fixed, reloc.offset,
                         (instruction & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF))
        reloc_rows.append({"offset": reloc.offset, "type": reloc.relocation_type,
                           "symbol": reloc.symbol_name, "target": hex(target)})
    if len(fixed) % 4:
        raise ValueError("candidate body is not ARM-word aligned")
    return bytes(fixed), reloc_rows


def build_mapping(entries: tuple[tuple[int, int], ...]) -> bytes:
    data = bytearray(MAP_CAPACITY * 16)
    if len(entries) >= MAP_CAPACITY:
        raise ValueError("mapping fixture leaves no room for sentinel")
    for i, (code, delta) in enumerate(entries):
        struct.pack_into("<H", data, i * 16, code & 0xFFFF)
        struct.pack_into("<I", data, i * 16 + 4, delta & 0xFFFFFFFF)
    struct.pack_into("<H", data, len(entries) * 16, MAP_SENTINEL)
    return bytes(data)


def record_address(start: int, offset: int, table_base: int = RECORDS) -> int:
    return u32(table_base + (u32(start + offset) << 5))


def initialize_memory(u: Uc, case: Case, candidate: bytes | None = None,
                     candidate_entry: int = CANDIDATE_ENTRY,
                     image: bytes = IMAGE) -> None:
    u.mem_map(TEXT, 0x00500000)
    u.mem_write(TEXT, image)
    u.mem_map(0x00800000, 0x00010000)
    u.mem_map(0x00900000, 0x00060000)
    u.mem_map(0x00A00000, 0x00010000)
    if candidate is not None:
        u.mem_write(candidate_entry, candidate)

    handle = bytearray(0x20)
    table_base = RECORDS if case.table_base is None else u32(case.table_base)
    struct.pack_into("<I", handle, 0, table_base)
    struct.pack_into("<I", handle, 0x0C, u32(case.start))
    struct.pack_into("<I", handle, 0x14, u32(case.gate))
    u.mem_write(HANDLE, bytes(handle))

    # Fill every record the ordinary signed-index domain can visit with a
    # harmless non-control code, then replace directed offsets.
    ordinary = bytearray(RECORD_CAPACITY * RECORD_STRIDE)
    for offset in range(RECORD_CAPACITY):
        struct.pack_into("<H", ordinary, offset * RECORD_STRIDE, 0x0041)
    u.mem_write(RECORDS, bytes(ordinary))
    for offset, code in case.writes:
        address = record_address(case.start, offset, table_base)
        u.mem_write(address, struct.pack("<H", code & 0xFFFF))
    u.mem_write(MAP_TABLE, build_mapping(case.mappings))


def run_helper(case: Case, candidate: bytes | None = None,
               candidate_entry: int = CANDIDATE_ENTRY, image: bytes = IMAGE) -> dict:
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    initialize_memory(u, case, candidate, candidate_entry, image)
    initial = random.Random(case.seed)
    callee_events: list[dict] = []
    pending: list[dict] = []
    writes: list[tuple[int, int, int]] = []
    done = False

    u.reg_write(UC_ARM_REG_SP, 0x00A0FF00)
    u.reg_write(UC_ARM_REG_LR, STOP)
    u.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    u.reg_write(UC_ARM_REG_R0, HANDLE)
    for reg in (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
                UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11):
        u.reg_write(reg, initial.getrandbits(32))
    for reg in (UC_ARM_REG_D8, UC_ARM_REG_D9, UC_ARM_REG_D10, UC_ARM_REG_D11,
                UC_ARM_REG_D12, UC_ARM_REG_D13, UC_ARM_REG_D14, UC_ARM_REG_D15):
        u.reg_write(reg, initial.getrandbits(64))

    def on_code(uc, address, _size, _user_data):
        nonlocal done
        if address == STOP:
            done = True
            uc.emu_stop()
            return
        if address in CALLEES:
            event = {"address": hex(address), "arg_r0": uc.reg_read(UC_ARM_REG_R0),
                     "return_pc": uc.reg_read(UC_ARM_REG_LR), "return_r0": None}
            callee_events.append(event)
            pending.append(event)
            return
        if pending and address == pending[-1]["return_pc"]:
            pending[-1]["return_r0"] = uc.reg_read(UC_ARM_REG_R0)
            pending.pop()

    def on_write(_uc, _kind, address, size, value, _user_data):
        writes.append((address, size, value & 0xFFFFFFFF))

    u.hook_add(UC_HOOK_CODE, on_code)
    u.hook_add(UC_HOOK_MEM_WRITE, on_write)
    fault = None
    pc_start = candidate_entry if candidate is not None else ENTRY
    try:
        u.emu_start(pc_start, 0, count=200000)
    except UcError as error:
        fault = str(error)

    stack_low, stack_high = 0x00A00000, 0x00A10000
    external_writes = tuple(x for x in writes if not stack_low <= x[0] < stack_high)
    memory = (
        bytes(u.mem_read(HANDLE, 0x20)),
        bytes(u.mem_read(RECORDS, RECORD_CAPACITY * RECORD_STRIDE)),
        bytes(u.mem_read(MAP_TABLE, MAP_CAPACITY * 16)),
    )
    regs = tuple(u.reg_read(reg) for reg in (
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
        UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_SP,
        UC_ARM_REG_D8, UC_ARM_REG_D9, UC_ARM_REG_D10, UC_ARM_REG_D11,
        UC_ARM_REG_D12, UC_ARM_REG_D13, UC_ARM_REG_D14, UC_ARM_REG_D15,
    ))
    return {"r0": u.reg_read(UC_ARM_REG_R0), "regs": regs,
            "callees": tuple((e["address"], e["arg_r0"], e["return_r0"]) for e in callee_events),
            "memory": memory, "external_writes": external_writes,
            "fault": fault, "done": done}


def make_cases() -> list[Case]:
    cases = [
        Case("gate-off", gate=0, writes=((0, 0xFFFF),)),
        Case("sentinel-first", writes=((0, 0xFFFF),)),
        Case("ordinary-only", writes=((0, 0x0041), (4, 0x1234), (9, 0xF800), (10, 0xF890), (11, 0xFFFF))),
        Case("count-control", writes=((0, 0xF801), (1, 0x0041), (2, 0xF801), (3, 0xFFFF))),
        Case("stop-control", writes=((0, 0xF801), (1, 0xF802), (2, 0xF801), (3, 0xFFFF))),
        Case("payload-count", writes=((0, 0xF801), (1, 0xF81A), (2, 0x0012), (3, 0x0041), (4, 0xFFFF))),
        Case("mapped-skip-3", writes=((0, 0xF803), (1, 0xF801), (2, 0xF801), (3, 0x0041), (4, 0xFFFF)),
             mappings=((0xF803, 3),)),
        Case("mapped-zero", writes=((0, 0xF804), (1, 0xF801), (2, 0xFFFF)), mappings=((0xF804, 0),)),
        Case("unmapped-control", writes=((0, 0xF87F), (1, 0xF801), (2, 0xFFFF))),
        Case("bound-last-readable", writes=((998, 0xFFFF),)),
        Case("bound-no-sentinel", writes=((998, 0x0041),)),
        Case("signed-bound-wrap", start=0x7FFFFC20,
             table_base=u32(RECORDS - (0x7FFFFC20 << 5)),
             writes=((1, 0xF801), (998, 0xFFFF))),
    ]

    # Exercise both edges and every value of the recognized range using the
    # original 0x002AE664 mapping helper for all non-special values.
    for code in range(0xF801, 0xF890):
        if code in (0xF801, 0xF802, 0xF81A):
            continue
        for delta in (0, 1, 3):
            rows = ((code, delta),)
            cases.append(Case(f"range-{code:04x}-delta-{delta}",
                              writes=((0, code), (1, 0x0041), (2, 0x0041), (3, 0x0041),
                                      (4, 0xFFFF)), mappings=rows))
    for code in (0xF800, 0xF890, 0xFFFF):
        cases.append(Case(f"range-outside-{code:04x}", writes=((0, code), (1, 0xFFFF))))

    for seed in (4729, 20261102):
        rng = random.Random(seed)
        for case_no in range(40):
            start = rng.randrange(0, 32)
            codes = []
            mappings = []
            for i in range(12):
                code = rng.choice((0x0041, 0x1234, 0xF801, 0xF802, 0xF81A,
                                   rng.randrange(0xF803, 0xF890)))
                codes.append((i, code))
                if 0xF803 <= code <= 0xF88F and code != 0xF81A:
                    mappings.append((code, rng.randrange(0, 5)))
            codes.append((12, 0xFFFF))
            # The original table is a sequence; retain the first mapping for
            # duplicate keys, as the ARM helper returns on the first match.
            seen = set()
            unique_mappings = []
            for pair in mappings:
                if pair[0] not in seen:
                    seen.add(pair[0])
                    unique_mappings.append(pair)
            cases.append(Case(f"random-{seed}-{case_no}", start=start,
                              writes=tuple(codes), mappings=tuple(unique_mappings), seed=seed + case_no))
    return cases


def compare_direct(body: bytes, cases: list[Case]) -> None:
    for number, case in enumerate(cases):
        original = run_helper(case)
        candidate = run_helper(case, body)
        if original != candidate:
            raise AssertionError(f"direct mismatch {number} {case.name}: "
                                 f"original={original} candidate={candidate}")
        if not original["done"] or original["fault"] is not None:
            raise AssertionError(f"fixture did not complete normally: {case.name}: {original}")
        if original["external_writes"]:
            raise AssertionError(f"unexpected non-stack writes for {case.name}: "
                                 f"{original['external_writes'][:3]}")


def run_parent_composition(selector: int, candidate_body: bytes | None,
                           image: bytes = IMAGE) -> dict:
    case = h2_parent.Case(seed=selector + 100, selector=selector, incoming_r2=0, state=0,
                          state_2e=0, state_35=1, row=2, arg5=0, arg6=0,
                          query_a=0, query_b=0, service_state=0)
    u = h2_parent.fixture(case, image=image)
    if candidate_body is not None:
        u.mem_write(CANDIDATE_ENTRY, candidate_body)
    parent_records = 0x00952000
    handle = h2_parent.GLOBAL_OBJECT
    u.mem_write(handle, bytes(0x1000))
    u.mem_write(handle, struct.pack("<I", parent_records))
    u.mem_write(handle + 0x0C, struct.pack("<I", 0))
    u.mem_write(handle + 0x14, struct.pack("<I", 1))
    text = bytearray(RECORD_CAPACITY * RECORD_STRIDE)
    for i in range(RECORD_CAPACITY):
        struct.pack_into("<H", text, i * RECORD_STRIDE, 0x0041)
    for i, code in enumerate((0xF801, 0xF801, 0xF802, 0xFFFF)):
        struct.pack_into("<H", text, i * RECORD_STRIDE, code)
    u.mem_write(parent_records, bytes(text))
    u.mem_write(MAP_TABLE, build_mapping(()))

    events: list[tuple] = []
    writes: list[tuple] = []
    candidate_hit = False
    done = False

    def on_code(uc, address, _size, _user_data):
        nonlocal candidate_hit, done
        if address == h2_parent.STOP:
            done = True
            uc.emu_stop()
            return
        if address == ENTRY:
            events.append(("line-count-entry", uc.reg_read(UC_ARM_REG_R0)))
            candidate_hit = True
            if candidate_body is not None:
                uc.reg_write(UC_ARM_REG_PC, CANDIDATE_ENTRY)
            return
        argc = PARENT_TARGETS.get(address)
        if argc is None:
            return
        args = tuple(uc.reg_read(reg) for reg in
                     (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)[:min(argc, 4)])
        events.append((hex(address), args))
        if address == 0x002C1F28:
            result = 0
        elif address == 0x002B89A0:
            result = 0
        elif address in (0x0028DF54, 0x0028DF3C):
            result = args[0] if args else 0
        elif address == 0x002F5B2C:
            result = 0x20 + args[0]
        elif address == 0x002D65B4:
            result = 0x140 + args[0]
        elif address == 0x0028DF70:
            result = 4
        elif address == 0x0028E974:
            result = 0
        elif address == 0x002B8D24:
            result = args[0]
        else:
            result = 0
        uc.reg_write(UC_ARM_REG_R0, result & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def on_write(_uc, _kind, address, size, value, _user_data):
        if not 0x0080F000 <= address < 0x00810000:
            writes.append((address, size, value & 0xFFFFFFFF))

    u.hook_add(UC_HOOK_CODE, on_code)
    u.hook_add(UC_HOOK_MEM_WRITE, on_write)
    u.reg_write(UC_ARM_REG_R0, 0x12345678)
    u.reg_write(UC_ARM_REG_R1, 0x87654321)
    u.reg_write(UC_ARM_REG_R2, 0)
    u.reg_write(UC_ARM_REG_R3, selector)
    try:
        u.emu_start(0x00286928, 0, count=200000)
        fault = None
    except UcError as error:
        fault = str(error)
    object_ptr = h2_parent.OBJECTS[1]
    state = {"r0": u.reg_read(UC_ARM_REG_R0),
             "r4_r11_sp": tuple(u.reg_read(reg) for reg in
                                  (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                                   UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                                   UC_ARM_REG_SP)),
             "object_20": struct.unpack("<I", u.mem_read(object_ptr + 0x20, 4))[0],
             "object": bytes(u.mem_read(object_ptr, 0x1800)),
             "global_handle": bytes(u.mem_read(handle, 0x1000)),
             "events": tuple(events), "writes": tuple(writes),
             "fault": fault, "done": done, "candidate_hit": candidate_hit}
    return state


def composition_checks(body: bytes) -> None:
    for selector in (11, 19):
        original = run_parent_composition(selector, None)
        converted = run_parent_composition(selector, body)
        if original != converted:
            raise AssertionError(f"0x00286928 selector-{selector} composition mismatch: "
                                 f"original={original} candidate={converted}")
        if (not original["done"] or not original["candidate_hit"]
                or not converted["candidate_hit"]
                or original["object_20"] != 2 or converted["object_20"] != 2):
            raise AssertionError(f"caller did not consume line count for selector {selector}: "
                                 f"original={original} candidate={converted}")


def negative_controls(source: str, good_body: bytes) -> dict[str, bool]:
    cases = {
        "sentinel": ("if (code == 0xffff)", "if (code == 0xfffe)", Case("nc-sentinel", writes=((0, 0xFFFF),))),
        "count_control": ("if (control_code == 1)", "if (control_code == 3)",
                          Case("nc-count", writes=((0, 0xF801), (1, 0xFFFF)))),
        "stop_control": ("control_code == 2", "control_code == 3",
                         Case("nc-stop", writes=((0, 0xF801), (1, 0xF802), (2, 0xFFFF)))),
        "payload_control": ("control_code == 0x1a", "control_code == 0x18",
                            Case("nc-payload", writes=((0, 0xF81A), (1, 0x0007), (2, 0xFFFF)))),
        "mapped_delta": ("index += func_002ae664(code);", "index += 0;",
                         Case("nc-map", writes=((0, 0xF803), (1, 0xFFFF)), mappings=((0xF803, 2),))),
        "signed_bound": ("static_cast<int32_t>(index) >= signed_limit",
                         "index >= static_cast<uint32_t>(signed_limit)",
                         Case("nc-bound", start=0x7FFFFC20,
                              table_base=u32(RECORDS - (0x7FFFFC20 << 5)),
                              writes=((0, 0x0041), (1, 0xF801), (998, 0xFFFF)))),
    }
    detected = {}
    for name, (old, new, case) in cases.items():
        if source.count(old) != 1:
            raise AssertionError(f"negative control anchor is not unique: {name}")
        mutant_path = OUT / f"mutant-{name}.cpp"
        mutant_path.write_text(source.replace(old, new, 1), encoding="utf-8")
        mutant_body, _ = compile_candidate(mutant_path, f"mutant-{name}.o")
        if mutant_body == good_body:
            raise AssertionError(f"mutation did not change machine code: {name}")
        try:
            detected[name] = run_helper(case) != run_helper(case, mutant_body)
        except UcError:
            detected[name] = True
        if not detected[name]:
            raise AssertionError(f"negative control was not detected: {name}")
    return detected


def main() -> int:
    if sha(IMAGE) != IMAGE_SHA:
        raise SystemExit("pinned original code.bin hash mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    source = SRC.read_text(encoding="utf-8")
    body, relocations = compile_candidate()
    if len(body) > SPAN:
        raise SystemExit(f"candidate body exceeds original slot: {len(body)}/{SPAN}")
    slot_tail = SPAN - len(body)
    cases = make_cases()
    compare_direct(body, cases)
    composition_checks(body)
    controls = negative_controls(source, body)
    report = {
        "schema_version": 1,
        "candidate": "AsdText_GetLineCount / 0x002B787C",
        "reference_image_sha256": sha(IMAGE),
        "reference_function_sha256": sha(IMAGE[ENTRY - TEXT:ENTRY - TEXT + SPAN]),
        "candidate_source_sha256": sha(SRC.read_bytes()),
        "compiled_candidate_body_sha256": sha(body),
        "compiled_candidate_bytes": len(body),
        "original_span_bytes": SPAN,
        "slot_tail_bytes": slot_tail,
        "slot_tail_nops": slot_tail // 4,
        "relocations": relocations,
        "direct_case_count": len(cases),
        "direct_passed": len(cases),
        "caller_compositions": 2,
        "caller_composition_addresses": ["0x00286928"],
        "caller_selectors": [11, 19],
        "negative_controls_detected": controls,
        "signed_bound_control_fixture": {
            "start_index": hex(0x7FFFFC20),
            "table_base": hex(u32(RECORDS - (0x7FFFFC20 << 5))),
            "first_record_address": hex(record_address(
                0x7FFFFC20, 0, u32(RECORDS - (0x7FFFFC20 << 5)))),
            "initialized_record_count": RECORD_CAPACITY,
            "sentinel_record_offset": 998,
            "negative_control_uses_same_initialized_region": True,
            "negative_control_count_control_offset": 1,
            "traversed_region": "separately initialized records at RECORDS, not code-image bytes",
        },
        "dependencies_executed_from_pinned_image": ["0x002AE6B0", "0x002AE664"],
        "checks": {
            "return_and_fault": "compared",
            "callee_saved_r4_r11_sp_d8_d15": "compared",
            "callee_entry_order_arguments_and_returns": "compared",
            "handle_records_mapping_table": "compared_unchanged",
            "non_stack_guest_writes": "none",
        },
        "limits": [
            "Only initialized mapped handles/tables with a reachable sentinel were used.",
            "No concurrent mutation, MMIO aliasing, malformed handle, absent sentinel, or scheduler behavior is established.",
            "Caller compositions execute original 0x00286928 with deterministic stubs for its other services; they do not prove runtime selector distribution.",
            "The text-control mapping values and their user-facing meanings remain unresolved.",
        ],
    }
    report_path = OUT / "offline-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS direct={len(cases)} caller=2 controls={len(controls)} body={len(body)}/{SPAN} "
          f"bytes; report={report_path}; sha256={sha(report_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
