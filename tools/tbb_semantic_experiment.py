#!/usr/bin/env python3
"""Isolated differential check for simple TBCR/TBL1 accessors; emits no IPS."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

import capstone
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.inspect_assets import parse_tbb_header
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, STACK_SIZE, TEXT, Case, Runner, arm, arm_branch,
    difference, unicorn, validate_local_blob,
)


TBL1 = 0x314C4254
ENTRY = 0x002C0E9C
SUBTABLE_ENTRY = 0x002AC2F4
GLOBAL_SUBTABLE_ENTRY = 0x002C0EC4
TITLE_CALLER_START = 0x001E9AB0
TITLE_CALLER_STOP = 0x001E9AC8
TITLE_TBB_SLOT_BASE = 0x0049382C
TITLE_TBB_SLOT_ID = 0x3A
TITLE_MENU_STRIDE = 0x56


def verify_title_call_sites(image: bytes, reference_hash: str) -> dict:
    """Fail closed on any drift in the hash-pinned title getter call chain."""
    expected = {
        0x001E9AB0: ("mov", "r1, #0"),
        0x001E9AB4: ("mov", "r0, #0x3a"),
        0x001E9AB8: ("bl", "#0x2c0ec4"),
        0x001E9AC4: ("bl", "#0x2c0e9c"),
        0x002C0ED8: ("b", "#0x2ac2f4"),
    }
    if not reference_hash or hashlib.sha256(image).hexdigest() != reference_hash:
        raise ValueError("Title caller reference hash does not match code.bin")
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    actual = {}
    for address, (mnemonic, operands) in expected.items():
        offset = address - TEXT
        decoded = next(cs.disasm(image[offset:offset + 4], address), None)
        if decoded is None or (decoded.mnemonic, decoded.op_str) != (mnemonic, operands):
            raise ValueError(f"Reference title callsite mismatch at {address:#010x}")
        actual[hex(address)] = {"mnemonic": decoded.mnemonic,
                                "operands": decoded.op_str,
                                "bytes": decoded.bytes.hex()}
    return actual


def title_menu_case(selection: int, raw_tbb: bytes, seed: int = 0) -> Case:
    """Build the caller's entry state; r6 is the already-loaded menu selection."""
    if selection not in range(4):
        raise ValueError("Title menu selection must be 0..3")
    if len(raw_tbb) > DATA_SIZE - 0x100:
        raise ValueError("Real TBB file does not fit in the experiment DATA region")
    rng = random.Random(seed ^ selection)
    data = bytearray(rng.randbytes(DATA_SIZE))
    data[0x100:0x100 + len(raw_tbb)] = raw_tbb
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[6] = selection
    return Case(f"title-menu-selection-{selection}", tuple(regs), bytes(data),
                rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def install_title_slot(runner: Runner, container_pointer: int) -> None:
    slot_pointer_address = TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4
    page = slot_pointer_address & ~0xFFF
    runner.uc.mem_protect(page, 0x1000,
                          unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    runner.uc.mem_write(slot_pointer_address, struct.pack("<I", container_pointer))


def run_title_caller(image: bytes, raw_tbb: bytes, subtable_code: bytes,
                     payload_code: bytes, seed: int,
                     reference_hash: str) -> dict:
    """Execute 0x1E9AB0..0x1E9AC8 with original and both candidate getters."""
    sites = verify_title_call_sites(image, reference_hash)
    validate_local_blob(subtable_code)
    validate_local_blob(payload_code)
    original = Runner(image, GLOBAL_SUBTABLE_ENTRY)
    rebuilt = Runner(image, SUBTABLE_ENTRY, subtable_code,
                     replacement_validator=validate_local_blob)
    payload_injection = INJECT + 0x200
    if payload_injection + len(payload_code) >= INJECT + 0x1000:
        raise ValueError("Title caller candidate blobs exceed the reserved injection page")
    rebuilt.uc.mem_write(payload_injection, payload_code)
    rebuilt.uc.mem_write(ENTRY, arm_branch(ENTRY, payload_injection))
    install_title_slot(original, DATA + 0x100)
    install_title_slot(rebuilt, DATA + 0x100)

    parsed = parse_tbb_header(raw_tbb)
    if parsed["table_count"] < 1:
        raise ValueError("TitleTable.tbb has no table 0 for the menu")
    first = parsed["tables"][0]
    if first["magic"] != "TBL1" or first["payload_size"] < 4 * TITLE_MENU_STRIDE:
        raise ValueError("TitleTable.tbb table 0 does not cover menu selections 0..3")
    header_size = parsed["header_size"]
    first_offset = struct.unpack_from("<I", raw_tbb, 0x0C)[0]
    expected_subtable = DATA + 0x100 + header_size + first_offset
    expected_payload = expected_subtable + 0x10

    results = []
    for selection in range(4):
        case = title_menu_case(selection, raw_tbb, seed)
        baseline = original.run(case, start=TITLE_CALLER_START,
                                stops=(TITLE_CALLER_STOP,), budget=512)
        candidate = rebuilt.run(case, start=TITLE_CALLER_START,
                                stops=(TITLE_CALLER_STOP,), budget=512)
        reason = difference(baseline, candidate, caller_window=True)
        baseline_regs = tuple(original.uc.reg_read(reg) for reg in original.reg_ids)
        candidate_regs = tuple(rebuilt.uc.reg_read(reg) for reg in rebuilt.reg_ids)
        baseline_regs += (original.uc.reg_read(arm.UC_ARM_REG_SP),
                          original.uc.reg_read(arm.UC_ARM_REG_LR))
        candidate_regs += (rebuilt.uc.reg_read(arm.UC_ARM_REG_SP),
                           rebuilt.uc.reg_read(arm.UC_ARM_REG_LR))
        register_differences = [
            f"r{index}" for index, (left, right) in
            enumerate(zip(baseline_regs, candidate_regs)) if left != right
        ]
        if baseline.result != expected_payload or candidate.result != expected_payload:
            reason = reason or "caller did not return the TitleTable table-0 payload"
        selected_record = expected_payload + selection * TITLE_MENU_STRIDE
        help_string = selected_record + 0x16
        if baseline_regs[6] != selection or candidate_regs[6] != selection:
            reason = reason or "caller did not preserve the selected menu index in r6"
        if help_string + 1 > expected_payload + first["payload_size"]:
            reason = reason or "selection help-string field is outside table-0 payload"
        results.append({
            "selection": selection,
            "passed": reason is None,
            "stop_pc": hex(baseline.pc),
            "payload_pointer": hex(baseline.result),
            "selected_record": hex(selected_record),
            "help_string_field": hex(help_string),
            "nonobservable_register_differences": register_differences,
            "reason": reason,
        })
    return {
        "passed": all(item["passed"] for item in results),
        "start": hex(TITLE_CALLER_START),
        "stop": hex(TITLE_CALLER_STOP),
        "global_slot_pointer_address": hex(TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4),
        "container_pointer": hex(DATA + 0x100),
        "expected_subtable": hex(expected_subtable),
        "expected_payload": hex(expected_payload),
        "call_sites_verified_against_reference_hash": sites,
        "selections": results,
        "scope": "original Tbb_GetGlobalSubTable plus original/candidate Tbb_GetSubTable and Tbb_GetPayloadData through the title caller stop; RowCount excluded",
        "register_policy": "compare r0, r4-r11, SP, continuation, consumed flags, memory/access footprint; report but do not fail on caller-saved r1-r3/r12 that the continuation overwrites or does not consume",
    }


def make_cases(seed: int, samples: int):
    rng = random.Random(seed ^ ENTRY)
    fixtures = (
        ("null", None),
        ("wrong-magic", (0xDEADBEEF, 0, 0, 0x10)),
        ("valid-empty", (TBL1, 0, 4, 0x10)),
        ("valid-zero-stride", (TBL1, 0, 0, 0x10)),
        ("valid-partial-row", (TBL1, 10, 4, 0x10)),
        ("valid-single-row", (TBL1, 4, 4, 0x10)),
    )
    for label, header in fixtures:
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        if header is None:
            regs[0] = 0
        else:
            regs[0] = DATA + 0x100
            struct.pack_into("<4I", data, 0x100, *header)
        yield Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        base_offset = rng.randrange(0x100, DATA_SIZE - 0x20) & ~3
        magic = TBL1 if rng.randrange(10) else 0xDEADBEEF
        header = (magic, rng.randrange(0x101), rng.randrange(0x21), rng.getrandbits(32))
        regs[0] = DATA + base_offset
        struct.pack_into("<4I", data, base_offset, *header)
        yield Case(f"random-{index}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def make_subtable_cases(seed: int, samples: int):
    rng = random.Random(seed ^ 0x002AC2F4)
    fixtures = (
        ("null-container", None, 0),
        ("wrong-container-magic", 0xDEADBEEF, 0),
        ("empty-container", 0x52434254, 0),
        ("valid-first-index", 0x52434254, 0),
        ("valid-second-index", 0x52434254, 1),
        ("wrong-child-magic", 0x52434254, 1),
        ("index-equals-count", 0x52434254, 2),
    )
    for label, magic, table_index in fixtures:
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        if magic is None:
            regs[0] = 0
        else:
            base_offset = 0x100
            regs[0] = DATA + base_offset
            header_size = 0x20
            count = 0 if label == "empty-container" else 2
            struct.pack_into("<3I", data, base_offset, magic, header_size, count)
            offsets = (0x30, 0x50)
            struct.pack_into("<2I", data, base_offset + 0x0C, *offsets)
            child_magic = 0xDEADBEEF if label == "wrong-child-magic" else 0x314C4254
            for offset in offsets:
                child_offset = base_offset + header_size + offset
                struct.pack_into("<4I", data, child_offset, child_magic, 4, 4, 0x10)
        regs[1] = table_index
        yield Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        base_offset = rng.randrange(0x100, 0x300) & ~3
        count = rng.randrange(0, 5)
        header_size = (0x0C + count * 4 + 0xF) & ~0xF
        offsets = tuple(0x40 + table * 0x20 for table in range(count))
        magic = 0x52434254 if rng.randrange(20) else 0xDEADBEEF
        regs[0] = DATA + base_offset
        regs[1] = rng.randrange(count + 1)
        struct.pack_into("<3I", data, base_offset, magic, header_size, count)
        if offsets:
            struct.pack_into("<" + "I" * count, data, base_offset + 0x0C, *offsets)
        for table, offset in enumerate(offsets):
            child_offset = base_offset + header_size + offset
            child_magic = 0x314C4254 if rng.randrange(5) else 0xDEADBEEF
            struct.pack_into("<4I", data, child_offset, child_magic,
                             rng.randrange(0x101), rng.randrange(0x21), rng.getrandbits(32))
        yield Case(f"random-{index}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def make_row_count_cases(seed: int, samples: int):
    rng = random.Random(seed ^ 0x002C0E4C)
    fixtures = (
        ("null", None),
        ("wrong-magic", (0xDEADBEEF, 10, 4, 0)),
        ("zero-stride", (TBL1, 10, 0, 0)),
        ("zero-payload", (TBL1, 0, 4, 0)),
        ("payload-below-stride", (TBL1, 3, 4, 0)),
        ("exact-divisibility", (TBL1, 16, 4, 0)),
        ("truncated-division", (TBL1, 10, 4, 0)),
        ("large-u32-values", (TBL1, 0xFFFFFFFF, 0x80000001, 0)),
    )
    for label, header in fixtures:
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        if header is None:
            regs[0] = 0
        else:
            regs[0] = DATA + 0x100
            struct.pack_into("<4I", data, 0x100, *header)
        yield Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                   rng.getrandbits(4) << 28)
    for index in range(samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        header = (TBL1 if rng.randrange(20) else 0xDEADBEEF,
                  rng.getrandbits(32), rng.randrange(1, 1 << 32),
                  rng.getrandbits(32))
        regs[0] = DATA + 0x100
        struct.pack_into("<4I", data, 0x100, *header)
        yield Case(f"random-{index}", tuple(regs), bytes(data),
                   rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def real_tbb_case(raw: bytes, label: str, *, table_index: int | None = None,
                  table_pointer: int | None = None, seed: int = 0) -> Case:
    if len(raw) > DATA_SIZE - 0x100:
        raise ValueError("Real TBB file does not fit in the experiment DATA region")
    rng = random.Random(seed)
    data = bytearray(rng.randbytes(DATA_SIZE))
    data[0x100 : 0x100 + len(raw)] = raw
    regs = [rng.getrandbits(32) for _ in range(13)]
    if table_pointer is None:
        regs[0] = DATA + 0x100
        regs[1] = table_index or 0
    else:
        regs[0] = table_pointer
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                rng.getrandbits(4) << 28)


def resolve_integration_symbols(functions: dict[str, tuple[bytes, tuple]]) -> dict[str, str]:
    """Map the two production accessors from their namespace-mangled ELF names."""
    resolved = {}
    for function_name in ("Tbb_GetSubTable", "Tbb_GetPayloadData"):
        matches = [name for name in functions if function_name in name]
        if len(matches) != 1:
            raise ValueError(f"Expected one integrated symbol for {function_name}, found {matches}")
        resolved[function_name] = matches[0]
    return resolved


def run(code_path: Path, output: Path, seed: int, samples: int,
        real_tbb_path: Path | None = None,
        title_caller_tbb_path: Path | None = None,
        integration_tu: Path | None = None):
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    reference_hash = hashlib.sha256(image).hexdigest()
    if len(image) != game["code_bin_size"] or reference_hash != game["code_sha256"]:
        raise ValueError("Private code.bin does not match the configured revision")

    source = ROOT / "experiments/semantic_equivalence/tbb_candidates.cpp"
    object_path = output / "tbb_candidates.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(object_path)
    integration_object_path = None
    integration_source_sha256 = None
    if integration_tu is not None:
        integration_object_path = output / "integrated_tbb.o"
        integration_build = compile_tu_armv6k(integration_tu, integration_object_path, ROOT)
        if integration_build.returncode:
            raise RuntimeError(integration_build.stderr)
        integration_functions = extract_elf_functions_detailed(integration_object_path)
        integration_symbols = resolve_integration_symbols(integration_functions)
        for function_name, symbol_name in integration_symbols.items():
            _, relocations = integration_functions[symbol_name]
            if relocations:
                raise ValueError(f"Unsupported relocation in integrated {function_name}: {relocations}")
            validate_local_blob(integration_functions[symbol_name][0])
        functions.update({function_name: integration_functions[symbol_name]
                          for function_name, symbol_name in integration_symbols.items()})
        integration_source_sha256 = hashlib.sha256(integration_tu.read_bytes()).hexdigest()

    symbol = "Tbb_GetPayloadData" if integration_tu is not None else "candidate_002c0e9c"
    wrong_symbol = "wrong_tbb_payload_magic"
    for name in (symbol, wrong_symbol):
        if name not in functions:
            raise ValueError(f"Missing compiled function: {name}")
        _, relocations = functions[name]
        if relocations:
            raise ValueError(f"Unsupported relocation in {name}: {relocations}")

    candidate_code = functions[symbol][0]
    wrong_code = functions[wrong_symbol][0]
    validate_local_blob(candidate_code)
    validate_local_blob(wrong_code)

    original = Runner(image, ENTRY)
    rebuilt = Runner(image, ENTRY, candidate_code,
                     replacement_validator=validate_local_blob)
    correct_results = []
    for case in make_cases(seed, samples):
        reason = difference(original.run(case), rebuilt.run(case))
        correct_results.append({"case": case.label, "passed": reason is None,
                                "reason": reason})

    wrong_runner = Runner(image, ENTRY, wrong_code,
                          replacement_validator=validate_local_blob)
    negative = None
    for case in make_cases(seed, samples):
        reason = difference(original.run(case), wrong_runner.run(case))
        if reason:
            negative = {"detected": True, "case": case.label, "reason": reason}
            break
    if negative is None:
        negative = {"detected": False}

    subtable_symbol = "Tbb_GetSubTable" if integration_tu is not None else "candidate_002ac2f4"
    wrong_subtable_symbol = "wrong_tbb_subtable_magic"
    for name in (subtable_symbol, wrong_subtable_symbol):
        if name not in functions:
            raise ValueError(f"Missing compiled function: {name}")
        _, relocations = functions[name]
        if relocations:
            raise ValueError(f"Unsupported relocation in {name}: {relocations}")
        validate_local_blob(functions[name][0])
    subtable_code = functions[subtable_symbol][0]
    wrong_subtable_code = functions[wrong_subtable_symbol][0]
    subtable_original = Runner(image, 0x002AC2F4)
    subtable_rebuilt = Runner(image, 0x002AC2F4, subtable_code,
                              replacement_validator=validate_local_blob)
    subtable_results = []
    for case in make_subtable_cases(seed, samples):
        reason = difference(subtable_original.run(case), subtable_rebuilt.run(case))
        subtable_results.append({"case": case.label, "passed": reason is None,
                                 "reason": reason})
    wrong_subtable_runner = Runner(image, 0x002AC2F4, wrong_subtable_code,
                                   replacement_validator=validate_local_blob)
    subtable_negative = None
    for case in make_subtable_cases(seed, samples):
        if case.label != "wrong-child-magic":
            continue
        reason = difference(subtable_original.run(case), wrong_subtable_runner.run(case))
        if reason:
            subtable_negative = {"detected": True, "case": case.label, "reason": reason}
            break
    if subtable_negative is None:
        subtable_negative = {"detected": False}

    row_count_symbol = "candidate_002c0e4c"
    wrong_row_count_symbol = "wrong_tbb_rowcount_divisor"
    for name in (row_count_symbol, wrong_row_count_symbol):
        if name not in functions:
            raise ValueError(f"Missing compiled function: {name}")
        _, relocations = functions[name]
        if relocations:
            raise ValueError(f"Unsupported relocation in {name}: {relocations}")
        validate_local_blob(functions[name][0])
    row_count_code = functions[row_count_symbol][0]
    wrong_row_count_code = functions[wrong_row_count_symbol][0]
    row_count_original = Runner(image, 0x002C0E4C)
    row_count_rebuilt = Runner(image, 0x002C0E4C, row_count_code,
                               replacement_validator=validate_local_blob)
    row_count_results = []
    for case in make_row_count_cases(seed, samples):
        reason = difference(row_count_original.run(case, budget=2048),
                            row_count_rebuilt.run(case, budget=2048))
        row_count_results.append({"case": case.label, "passed": reason is None,
                                  "reason": reason})
    wrong_row_count_runner = Runner(image, 0x002C0E4C, wrong_row_count_code,
                                    replacement_validator=validate_local_blob)
    row_count_negative = None
    for case in make_row_count_cases(seed, samples):
        if case.label != "truncated-division":
            continue
        reason = difference(row_count_original.run(case, budget=2048),
                            wrong_row_count_runner.run(case, budget=2048))
        if reason:
            row_count_negative = {"detected": True, "case": case.label,
                                  "reason": reason}
            break
    if row_count_negative is None:
        row_count_negative = {"detected": False}

    real_tbb_results = []
    real_tbb_sha256 = None
    if real_tbb_path is not None:
        real_tbb = real_tbb_path.read_bytes()
        real_tbb_sha256 = hashlib.sha256(real_tbb).hexdigest()
        parsed_tbb = parse_tbb_header(real_tbb)
        header_size = parsed_tbb["header_size"]
        table_count = parsed_tbb["table_count"]
        for table_index in range(table_count + 1):
            case = real_tbb_case(real_tbb, f"real-tbb-subtable-{table_index}",
                                 table_index=table_index, seed=seed ^ table_index)
            reason = difference(subtable_original.run(case), subtable_rebuilt.run(case))
            expected = None
            if table_index < table_count:
                relative_offset = struct.unpack_from("<I", real_tbb, 0x0C + table_index * 4)[0]
                expected = DATA + 0x100 + header_size + relative_offset
            actual = subtable_rebuilt.run(case).result
            passed = reason is None and actual == (expected or 0)
            real_tbb_results.append({"case": case.label, "passed": passed,
                                     "expected": expected, "actual": actual,
                                     "reason": reason})
        for table_index in range(table_count):
            relative_offset = struct.unpack_from("<I", real_tbb, 0x0C + table_index * 4)[0]
            table_pointer = DATA + 0x100 + header_size + relative_offset
            case = real_tbb_case(real_tbb, f"real-tbb-payload-{table_index}",
                                 table_pointer=table_pointer,
                                 seed=seed ^ 0xC0E9C ^ table_index)
            reason = difference(original.run(case), rebuilt.run(case))
            expected = table_pointer + 0x10
            actual = rebuilt.run(case).result
            passed = reason is None and actual == expected
            real_tbb_results.append({"case": case.label, "passed": passed,
                                     "expected": expected, "actual": actual,
                                     "reason": reason})
            row_case = real_tbb_case(real_tbb, f"real-tbb-row-count-{table_index}",
                                     table_pointer=table_pointer,
                                     seed=seed ^ 0x2C0E4C ^ table_index)
            reason = difference(row_count_original.run(row_case, budget=2048),
                                row_count_rebuilt.run(row_case, budget=2048))
            actual = row_count_rebuilt.run(row_case, budget=2048).result
            passed = reason is None and actual == 0
            real_tbb_results.append({"case": row_case.label, "passed": passed,
                                     "expected": 0, "actual": actual,
                                     "reason": reason})

    title_caller = None
    if title_caller_tbb_path is not None:
        title_caller = run_title_caller(
            image, title_caller_tbb_path.read_bytes(), subtable_code,
            candidate_code, seed, reference_hash,
        )

    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                               text=True, check=True)
    report = {
        "passed": (all(item["passed"] for item in correct_results) and negative["detected"]
                   and all(item["passed"] for item in subtable_results)
                   and subtable_negative["detected"]
                   and all(item["passed"] for item in row_count_results)
                   and row_count_negative["detected"]
                   and all(item["passed"] for item in real_tbb_results)
                   and (title_caller is None or title_caller["passed"])),
        "scope": ("TBB getters; isolated calls plus the title caller window" if title_caller
                  else "TBB getters; isolated calls; row count oracle follows the exact shared helper in the pinned original image"),
        "entry": hex(ENTRY),
        "reference_sha256": reference_hash,
        "candidate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "integration_source": str(integration_tu) if integration_tu else None,
        "integration_source_sha256": integration_source_sha256,
        "integration_object_sha256": (hashlib.sha256(integration_object_path.read_bytes()).hexdigest()
                                       if integration_object_path else None),
        "candidate_symbols": {"payload": symbol, "subtable": subtable_symbol},
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_cases_per_function": samples,
        "candidate_bytes": len(candidate_code),
        "cases": correct_results,
        "negative_control": negative,
        "subtable_entry": hex(0x002AC2F4),
        "subtable_candidate_bytes": len(subtable_code),
        "subtable_cases": subtable_results,
        "subtable_negative_control": subtable_negative,
        "row_count_entry": hex(0x002C0E4C),
        "row_count_candidate_bytes": len(row_count_code),
        "row_count_cases": row_count_results,
        "row_count_negative_control": row_count_negative,
        "real_tbb_path": str(real_tbb_path) if real_tbb_path else None,
        "real_tbb_sha256": real_tbb_sha256,
        "real_tbb_cases": real_tbb_results,
        "title_caller_tbb_path": str(title_caller_tbb_path) if title_caller_tbb_path else None,
        "title_caller_window": title_caller,
        "limitations": [
            "Tbb_GetRowCount oracle executes its exact tail-branch target at 0x002C6C10 in the hash-pinned image",
            "Real TitleTable.tbb coverage exercises only its existing two tables and boundary index",
            "A sampled differential test is not a proof for every input",
            ("No IPS, emulator, or game integration test" if title_caller else
             "No caller-window, IPS, emulator, or game integration test"),
            "Does not validate malformed offsets or payload memory bounds",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, type=Path, help="private extracted code.bin")
    parser.add_argument("--output", required=True, type=Path, help="ignored build output directory")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--real-tbb", type=Path,
                        help="optional extracted TBCR asset for direct getter comparisons")
    parser.add_argument("--title-caller-tbb", type=Path,
                        help="run the real title getter caller window for menu selections 0..3")
    parser.add_argument("--integration-tu", type=Path,
                        help="also compare production Tbb_GetSubTable/PayloadData symbols from this TU")
    args = parser.parse_args()
    run(args.code, args.output, args.seed, args.samples, args.real_tbb,
        args.title_caller_tbb, args.integration_tu)


if __name__ == "__main__":
    main()
