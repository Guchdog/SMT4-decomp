"""Build and differentially exercise the production C++ H2 cursor updater."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm

from tools.asm_diff import extract_elf_functions_detailed, load_function_addresses
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips, sha256
from tools.semantic_experiment import arm_branch
from tools import h2_calc_experiment as calc

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch46_b.cpp"
LEDGER = ROOT / "config/functions.csv"
SYMBOL = "camp_func_0029f278"
ENTRY = 0x0029F278
SPAN = 1536
TEXT_BASE = 0x00100000
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CAVE = 0x003FE624
CAVE_CAPACITY = 0x9DC
DATA_BASE = 0x00480000
DATA_SIZE = 0x00200000
CURSOR = DATA_BASE + 0x1000
STACK_BASE = 0x0F000000
STACK_SIZE = 0x20000
SP = STACK_BASE + 0x18000
RETURN = 0x01000000
OBSERVED_CALLS = {
    0x002D5618: ("cursor_begin", 4),
    0x001FF3C4: ("axis_move", 1),
    0x002C615C: ("divide", 2),
    0x002892C0: ("axis_adjust", 2),
    0x002D5644: ("cursor_end", 0),
    0x002BFFBC: ("mode1_query", 1),
    0x002C17D4: ("logical_query", 1),
    0x002BC200: ("sound", 1),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def elf_section(obj: Path, wanted: str) -> bytes:
    """Return bytes for one named ELF32 section, rejecting ambiguous objects."""
    data = obj.read_bytes()
    if len(data) < 52 or data[:4] != b"\x7fELF" or data[4:6] != b"\x01\x01":
        raise ValueError("expected little-endian ELF32 object")
    header = struct.unpack_from("<16sHHIIIIIHHHHHH", data, 0)
    shoff, shentsize, shnum, shstrndx = header[6], header[11], header[12], header[13]
    sections = [struct.unpack_from("<IIIIIIIIII", data, shoff + i * shentsize)
                for i in range(shnum)]
    strings_section = sections[shstrndx]
    strings = data[strings_section[4]:strings_section[4] + strings_section[5]]
    matches = []
    for section in sections:
        name_offset = section[0]
        end = strings.find(b"\0", name_offset)
        name = strings[name_offset:end].decode("utf-8", errors="replace")
        if name == wanted:
            matches.append(section)
    if len(matches) != 1:
        raise ValueError(f"expected one {wanted} section, got {len(matches)}")
    section = matches[0]
    return data[section[4]:section[4] + section[5]]


def resolve_body(obj: Path, body: bytes, relocations) -> tuple[bytes, bytes, list[dict]]:
    """Resolve audited calls to pinned ledger addresses and the local mask table."""
    addresses = load_function_addresses(LEDGER)
    fixed = bytearray(body)
    table = elf_section(obj, ".rodata.cst4")
    if table != bytes((8, 4, 1, 2)):
        raise ValueError(f"cursor bit-mask table changed: {table.hex()}")
    rows = []
    abs32 = []
    for reloc in relocations:
        if reloc.explicit_addend is not None or reloc.offset < 0 or reloc.offset + 4 > len(fixed):
            raise ValueError(f"unexpected relocation shape: {reloc}")
        if reloc.relocation_type == 28 and reloc.symbol_name:
            target = addresses.get(reloc.symbol_name)
            if target is None or target & 1:
                raise ValueError(f"call target is missing or not ARM-aligned: {reloc}")
            instruction = struct.unpack_from("<I", fixed, reloc.offset)[0]
            if instruction & 0x0F000000 != 0x0B000000:
                raise ValueError(f"R_ARM_CALL is not an ARM BL: {instruction:#010x}")
            place = CAVE + reloc.offset
            delta = target - (place + 8)
            if delta & 3 or not -(1 << 25) <= delta < (1 << 25):
                raise ValueError(f"ARM BL target is out of range: {reloc.symbol_name}")
            struct.pack_into("<I", fixed, reloc.offset,
                             (instruction & 0xFF000000) | ((delta >> 2) & 0x00FFFFFF))
            rows.append({"offset": hex(reloc.offset), "kind": "R_ARM_CALL",
                         "symbol": reloc.symbol_name, "target": hex(target)})
        elif reloc.relocation_type == 2 and not reloc.symbol_name:
            abs32.append(reloc)
        else:
            raise ValueError(f"unsupported cursor relocation: {reloc}")
    if len(rows) != 15 or len(abs32) != 1 or abs32[0].offset != 0x3FC:
        raise ValueError(f"unexpected relocation census: calls={len(rows)}, abs32={abs32}")
    # This local relocation points at the dedicated .rodata.cst4 section.
    # The object report pins that section's four bytes and this sole reference.
    struct.pack_into("<I", fixed, abs32[0].offset, CAVE + len(body))
    rows.append({"offset": hex(abs32[0].offset), "kind": "R_ARM_ABS32",
                 "section": ".rodata.cst4", "target": hex(CAVE + len(body)),
                 "bytes": table.hex()})
    return bytes(fixed), table, rows


def patch_image(image: bytes, body: bytes, table: bytes) -> tuple[bytes, bytes, dict]:
    text_offset = CAVE - TEXT_BASE
    image_end = TEXT_BASE + len(image)
    if image_end <= CAVE or CAVE + CAVE_CAPACITY > image_end:
        raise ValueError("reviewed .text tail does not fit in pinned image")
    if any(image[text_offset:text_offset + CAVE_CAPACITY]):
        raise ValueError("cursor code cave is not zero-filled in the pinned image")
    if CAVE + len(body) + len(table) > CAVE + CAVE_CAPACITY:
        raise ValueError("cursor body and local table exceed the reviewed cave")
    branch = arm_branch(ENTRY, CAVE)
    final = bytearray(image)
    final[ENTRY - TEXT_BASE:ENTRY - TEXT_BASE + 4] = branch
    final[text_offset:text_offset + len(body)] = body
    final[text_offset + len(body):text_offset + len(body) + len(table)] = table
    patch = encode_ips([
        (ENTRY - TEXT_BASE, branch),
        (text_offset, body + table),
    ], len(image))
    if apply_ips(image, patch) != bytes(final):
        raise ValueError("cursor IPS roundtrip mismatch")
    suffix_preserved = (
        final[ENTRY - TEXT_BASE + 4:ENTRY - TEXT_BASE + SPAN] ==
        image[ENTRY - TEXT_BASE + 4:ENTRY - TEXT_BASE + SPAN]
    )
    if not suffix_preserved:
        raise ValueError("the original cursor suffix was not retained")
    return bytes(final), patch, {
        "entry_branch": branch.hex(), "entry_target": hex(CAVE),
        "body_bytes": len(body), "body_sha256": sha(body),
        "rodata_bytes": len(table), "rodata_sha256": sha(table),
        "ips_sha256": sha(patch), "original_suffix_preserved": suffix_preserved,
        "interior_entry_census": interior_entry_census(image),
    }


def interior_entry_census(image: bytes) -> dict:
    end = ENTRY + SPAN
    branches, pointers = [], []
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        source = TEXT_BASE + offset
        if word & 0x0E000000 == 0x0A000000 and word >> 28 != 0xF:
            immediate = word & 0x00FFFFFF
            if immediate & 0x00800000:
                immediate -= 0x01000000
            target = source + 8 + (immediate << 2)
            if ENTRY < target < end and not ENTRY <= source < end:
                branches.append((source, target, word))
        if word & 3 == 0 and ENTRY < word < end and not ENTRY <= source < end:
            pointers.append((source, word))
    if branches or pointers:
        raise ValueError(f"external cursor interior entries need preservation audit: {branches}, {pointers}")
    return {
        "external_direct_branches": [], "external_aligned_pointers": [],
        "scan": "word-aligned ARM B/BL and aligned absolute-pointer candidates across pinned code.bin",
        "scope_limit": "does not detect Thumb, computed/indirect branches, or data values that resemble non-aligned pointers",
    }


def put_u32(data: bytearray, offset: int, value: int):
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def fixtures(seed: int, samples: int) -> list[dict]:
    rng = random.Random(seed)
    result = []

    def add(label, **kwargs):
        base = {
            "disabled": 0, "sound": 0, "first_threshold": 1,
            "second_threshold": 1, "first_width": 4, "second_width": 4,
            "first_dim": 8, "second_dim": 8, "first_base": 1,
            "first_offset": 0, "second_base": 1, "total": 3,
            "old_first": 1, "old_second": 1, "first_bits": 0,
            "second_bits": 0, "first_ids": [3, 4, 5, 6, 0, 1, 2, 7],
            "second_ids": [6, 5, 4, 3, 7, 2, 1, 0], "input_state": 0,
            "alternate_state": 0, "mode1_counts": {}, "mode": 0,
        }
        base.update(kwargs)
        base["label"] = label
        result.append(base)

    add("disabled-short-circuit", disabled=1, first_threshold=0,
        second_threshold=0, sound=1, first_ids=[3, 4, 5, 6, 0x20, 0x20, 0x20, 0x20])
    add("enabled-no-movement-stable", total=4)
    add("first-axis-threshold-one", first_threshold=1, first_base=0, old_first=1)
    add("first-axis-active-no-input", first_threshold=2, first_base=0, old_first=1)
    add("second-axis-active-no-input", second_threshold=2, second_base=0, old_second=1)
    add("both-axes-active-no-input", first_threshold=2, second_threshold=2,
        first_base=0, second_base=0, old_first=1, old_second=1)
    add("first-width-one-boundary", first_width=1, total=1, first_base=1)
    add("division-zero-width", second_width=0, total=7, first_base=0)
    add("remainder-zero", first_width=4, total=8, first_base=2, first_offset=0)
    add("remainder-nonzero-wrap-check", first_width=4, total=9, first_base=2,
        first_offset=0, second_base=2, old_second=1, second_bits=0xA)
    add("flat-position-equals-total", first_width=4, total=9, first_base=2,
        first_offset=0, second_base=1)
    add("flat-position-below-total", first_width=4, total=10, first_base=2,
        first_offset=0, second_base=1)
    add("signed-position-high-bit", first_width=4, total=0x80000001,
        first_base=0x80000000, first_offset=1, second_base=3)
    add("bitset-map-and-logical-queries", first_threshold=1, second_threshold=1,
        first_ids=[3, 4, 5, 6, 0x20, 0x20, 0x20, 0x20],
        second_ids=[6, 5, 4, 3, 0x20, 0x20, 0x20, 0x20],
        first_bits=0x5, second_bits=0xA, input_state=0x1F8,
        alternate_state=0x80, mode=0)
    add("mode1-counter-short-circuit", first_threshold=2, first_base=0, mode=0,
        mode1_counts={0: 1, 1: 1, 9: 1}, sound=1)
    add("wrap-query-counter-positive", first_width=4, total=9, first_base=2,
        second_base=2, old_second=1, second_bits=4,
        mode1_counts={0: 1}, sound=1)
    for i in range(samples):
        add(f"seeded-{i}", disabled=0, sound=rng.randrange(2),
            first_threshold=rng.choice((0, 1, 2, 3)),
            second_threshold=rng.choice((0, 1, 2, 3)),
            first_width=rng.choice((0, 1, 2, 3, 4, 7, 0xFFFFFFFF)),
            second_width=rng.choice((0, 1, 2, 4, 8, 0xFFFFFFFF)),
            first_dim=rng.getrandbits(32), second_dim=rng.getrandbits(32),
            first_base=rng.getrandbits(32), first_offset=rng.getrandbits(32),
            second_base=rng.getrandbits(32), total=rng.getrandbits(32),
            old_first=rng.getrandbits(32), old_second=rng.getrandbits(32),
            first_bits=rng.getrandbits(16), second_bits=rng.getrandbits(16),
            first_ids=[rng.choice((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) for _ in range(8)],
            second_ids=[rng.choice((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) for _ in range(8)],
            input_state=rng.getrandbits(32), alternate_state=rng.getrandbits(32),
            mode=rng.randrange(2),
            mode1_counts={k: rng.choice((0, 1, 2)) for k in (0, 1, 3, 4, 5, 6, 9)},
        )
    return result


def initialize_memory(uc, case: dict):
    uc.mem_write(DATA_BASE, bytes(DATA_SIZE))
    obj = bytearray(0x64)
    obj[0x62] = case["disabled"] & 0xFF
    for axis, threshold, width, dimension, base, offset in (
        (0, case["first_threshold"], case["first_width"], case["first_dim"],
         case["first_base"], case["first_offset"]),
        (0x28, case["second_threshold"], case["second_width"], case["second_dim"],
         case["second_base"], 0),
    ):
        put_u32(obj, axis + 0x10, width)
        put_u32(obj, axis + 0x18, threshold)
        put_u32(obj, axis + 0x1C, dimension)
        put_u32(obj, axis + 0x20, base)
        put_u32(obj, axis + 0x24, offset)
    put_u32(obj, 0x50, case["total"])
    put_u32(obj, 0x54, case["old_first"])
    put_u32(obj, 0x58, case["old_second"])
    struct.pack_into("<HH", obj, 0x5C, case["first_bits"], case["second_bits"])
    for i, value in enumerate(case["first_ids"]): obj[4 + i] = value & 0xFF
    for i, value in enumerate(case["second_ids"]): obj[0x2C + i] = value & 0xFF
    uc.mem_write(CURSOR, bytes(obj))
    uc.mem_write(0x00465278, bytes.fromhex("a1a2a3a4b1b2b3b4c1c2c3c4d1d2d3d4e1e2e3e4f1f2f3f4"))
    uc.mem_write(0x004650A8, struct.pack("<I", case["mode"]))
    uc.mem_write(0x004E3C28, struct.pack("<I", case["input_state"]))
    uc.mem_write(0x004E3C48, struct.pack("<I", case["alternate_state"]))
    counts = bytearray(31 * 4)
    for key, value in case["mode1_counts"].items():
        struct.pack_into("<I", counts, key * 4, value)
    uc.mem_write(0x004E3C58, bytes(counts))


class Machine:
    def __init__(self, image: bytes):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        image_map = (len(image) + 0xFFF) & ~0xFFF
        self.uc.mem_map(TEXT_BASE, image_map, unicorn.UC_PROT_ALL)
        self.uc.mem_write(TEXT_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(STACK_BASE, STACK_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(RETURN, 0x1000, unicorn.UC_PROT_ALL)
        self.uc.mem_write(RETURN, b"\x1e\xff\x2f\xe1")
        self.calls = []
        self.writes = []
        self.fault = None
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._write)

    def _code(self, uc, pc, _size, _user):
        if pc == RETURN:
            self.stopped = True
            uc.emu_stop()
            return
        if pc in OBSERVED_CALLS:
            name, count = OBSERVED_CALLS[pc]
            args = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(count)]
            self.calls.append((name, tuple(args)))

    def _write(self, uc, _access, address, size, value, _user):
        if STACK_BASE <= address < STACK_BASE + STACK_SIZE:
            return
        self.writes.append((address, size, value & 0xFFFFFFFF))

    def run(self, case: dict) -> dict:
        initialize_memory(self.uc, case)
        self.uc.mem_write(STACK_BASE, bytes(STACK_SIZE))
        for i in range(13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CURSOR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["sound"])
        before = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                  for i in range(4, 12)}
        before["sp"] = SP
        self.calls, self.writes, self.fault, self.stopped = [], [], None, False
        try:
            self.uc.emu_start(ENTRY, 0, count=500000)
        except unicorn.UcError as exc:
            self.fault = f"{exc}; pc={self.uc.reg_read(arm.UC_ARM_REG_PC):#x}"
        after = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                 for i in range(4, 12)}
        after["sp"] = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return {
            "fault": self.fault, "stopped": self.stopped,
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "preserved_before": before, "preserved_after": after,
            "cursor": bytes(self.uc.mem_read(CURSOR, 0x64)).hex(),
            "input_globals": bytes(self.uc.mem_read(0x00465278, 0x18)).hex(),
            "input_mode": bytes(self.uc.mem_read(0x004650A8, 4)).hex(),
            "input_states": bytes(self.uc.mem_read(0x004E3C28, 0x20)).hex(),
            "mode1_counts": bytes(self.uc.mem_read(0x004E3C58, 31 * 4)).hex(),
            "calls": list(self.calls), "writes": list(self.writes),
        }


def compare(original: dict, candidate: dict) -> list[str]:
    errors = []
    for key in ("fault", "stopped", "pc", "r0", "preserved_after", "cursor",
                "input_globals", "input_mode", "input_states", "mode1_counts",
                "calls", "writes"):
        if original[key] != candidate[key]:
            errors.append(f"{key} differs")
    if original["preserved_after"] != original["preserved_before"]:
        errors.append("original changed callee-saved registers or SP")
    if candidate["preserved_after"] != candidate["preserved_before"]:
        errors.append("candidate changed callee-saved registers or SP")
    return errors


class CalcWithActualCursor(calc.CalcMachine):
    """Keep Calc's modeled outer services but execute the real cursor updater."""

    def _code(self, uc, address, size, user):
        if address == 0x002C615C:
            return_address = uc.reg_read(arm.UC_ARM_REG_LR)
            original_cursor = ENTRY <= return_address < ENTRY + SPAN
            patched_cursor = CAVE <= return_address < CAVE + 1024
            if original_cursor or patched_cursor:
                return
        if address == ENTRY:
            return
        super()._code(uc, address, size, user)

    def initialize_cursor(self, *, first_threshold: int, second_threshold: int,
                          first_base: int, second_base: int, total: int,
                          input_state: int, counts: dict[int, int]):
        cursor = bytearray(0x64)
        for axis, threshold, base, width, dimension, offset in (
            (0, first_threshold, first_base, 4, 8, 0),
            (0x28, second_threshold, second_base, 4, 8, 0),
        ):
            put_u32(cursor, axis + 0x10, width)
            put_u32(cursor, axis + 0x18, threshold)
            put_u32(cursor, axis + 0x1C, dimension)
            put_u32(cursor, axis + 0x20, base)
            put_u32(cursor, axis + 0x24, offset)
        put_u32(cursor, 0x50, total)
        put_u32(cursor, 0x54, first_base)
        put_u32(cursor, 0x58, second_base)
        for i, value in enumerate((3, 4, 5, 6, 0x20, 0x20, 0x20, 0x20)):
            cursor[4 + i] = value
        for i, value in enumerate((6, 5, 4, 3, 0x20, 0x20, 0x20, 0x20)):
            cursor[0x2C + i] = value
        address = calc.WORK + 0xE8
        self.uc.mem_write(address, bytes(cursor))
        self.uc.mem_write(0x004650A8, struct.pack("<I", 0))
        self.uc.mem_write(0x004E3C28, struct.pack("<I", input_state))
        self.uc.mem_write(0x004E3C48, struct.pack("<I", 0))
        mode1 = bytearray(31 * 4)
        for query, value in counts.items():
            struct.pack_into("<I", mode1, query * 4, value)
        self.uc.mem_write(0x004E3C58, bytes(mode1))


def run(output: Path, seed: int, samples: int) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to reuse output directory: {output}")
    output.mkdir(parents=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned original image hash mismatch")
    source_hash = sha(SOURCE.read_bytes())
    obj = output / "leaf_batch46_b.o"
    build = compile_tu_armv6k(SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "cursor production TU failed to compile")
    functions = extract_elf_functions_detailed(obj)
    if SYMBOL not in functions:
        raise ValueError(f"object does not contain {SYMBOL}")
    raw, relocs = functions[SYMBOL]
    if len(raw) != 1024:
        raise ValueError(f"unexpected cursor C++ body size: {len(raw)}")
    body, table, relocation_rows = resolve_body(obj, raw, relocs)
    patched, patch, patch_report = patch_image(image, body, table)
    (output / "code.production.bin").write_bytes(patched)
    (output / "code.production.ips").write_bytes(patch)
    if apply_ips(image, (output / "code.production.ips").read_bytes()) != patched:
        raise ValueError("serialized cursor IPS failed roundtrip")

    case_rows = []
    first = None
    for case in fixtures(seed, samples):
        original = Machine(image).run(case)
        candidate = Machine(patched).run(case)
        errors = compare(original, candidate)
        row = {"label": case["label"], "passed": not errors, "errors": errors,
               "return": hex(original["r0"]), "call_count": len(original["calls"]),
               "calls": original["calls"]}
        case_rows.append(row)
        if errors and first is None:
            first = {"label": case["label"], "errors": errors,
                     "original": original, "candidate": candidate}

    caller_rows = []
    caller_scenarios = [
        ("title-calc-state1-stable-cursor", calc.Scenario("cursor-stable", 1, row=1),
         dict(first_threshold=1, second_threshold=1, first_base=1, second_base=1,
              total=3, input_state=0, counts={})),
        ("title-calc-state1-active-cursor-no-input", calc.Scenario("cursor-active", 1, row=1),
         dict(first_threshold=2, second_threshold=2, first_base=1, second_base=1,
              total=3, input_state=0, counts={})),
        ("title-calc-state1-cursor-logical-bits", calc.Scenario("cursor-bits", 1, row=1),
         dict(first_threshold=1, second_threshold=1, first_base=1, second_base=1,
              total=3, input_state=0x1F8, counts={})),
    ]
    for label, scenario, cursor in caller_scenarios:
        left = CalcWithActualCursor(image, scenario=scenario)
        right = CalcWithActualCursor(patched, scenario=scenario)
        left.initialize_cursor(**cursor)
        right.initialize_cursor(**cursor)
        original = left.run()
        candidate = right.run()
        error = calc.compare(original, candidate)
        row = {"label": label, "passed": error is None, "error": error,
               "original_return": hex(original["return"]),
               "trace_count": len(original["trace"]),
               "cursor_after": original["work"][0xE8:0x14C].hex()}
        caller_rows.append(row)
        if error and first is None:
            first = {"label": label, "errors": [error],
                     "original": original, "candidate": candidate}

    # Wrong-target control ensures the final-address branch check is sensitive.
    bad = bytearray(patched)
    bad[ENTRY - TEXT_BASE:ENTRY - TEXT_BASE + 4] = arm_branch(ENTRY, CAVE + 4)
    negative_case = next(case for case in fixtures(seed, 1)
                         if case["label"] == "enabled-no-movement-stable")
    expected = Machine(image).run(negative_case)
    mutant = Machine(bytes(bad)).run(negative_case)
    negative_detected = compare(expected, mutant) != []
    if not negative_detected:
        raise AssertionError("wrong cave target control escaped the differential")
    if sha(SOURCE.read_bytes()) != source_hash:
        raise RuntimeError("production source changed during experiment")
    report = {
        "schema": 1, "scope": "standalone original image plus production 0x0029F278 trampoline; all helper callees remain pinned original",
        "original_sha256": sha(image), "patched_sha256": sha(patched),
        "source_sha256": source_hash, "object_sha256": sha(obj.read_bytes()),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "candidate_raw_bytes": len(raw), "candidate_relocations": relocation_rows,
        "patch": patch_report, "case_count": len(case_rows),
        "cases_passed": sum(row["passed"] for row in case_rows),
        "title_calc_caller_cases": caller_rows,
        "first_counterexample": first, "negative_wrong_target_detected": negative_detected,
        "cases": case_rows,
        "limits": [
            "Synthetic cursor and input-state fixtures use mapped ordinary RAM. They do not establish physical controls or runtime scheduling.",
            "All helper bodies remain original; the H2 wrapper is not a merged accumulated image.",
            "TitleConfig_Calc caller cases retain its modeled outer service boundaries; only the cursor updater and its direct binary helpers execute from the patched/original image.",
            "Emulator/runtime behavior and physical input delivery are not covered.",
            "Incidental stack scratch below restored SP and read multiplicity/order are not compared; return, preserved registers/SP, ordered non-stack writes, cursor/globals, helper call/argument sequence and fault PC are compared.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    report = run(args.output, args.seed, args.samples)
    print(json.dumps({"report": str(args.output / "report.json"),
                      "cases": report["case_count"],
                      "passed": report["cases_passed"],
                      "first_counterexample": report["first_counterexample"],
                      "negative_wrong_target_detected": report["negative_wrong_target_detected"]}, indent=2))
    return 0 if report["first_counterexample"] is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
