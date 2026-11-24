#!/usr/bin/env python3
"""Differential test for engine_func_0036f49c (0x0036f49c) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the engine_func_0036f49c
body, resolves its four direct calls to deterministic stubs, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in identical
Unicorn machines with identical fixtures.

Compared outputs:
  * return r0 (the original's dead ABI register), continuation PC, final SP and
    the r4-r11 callee-saved sentinels;
  * the ordered call log with every register argument and the architected stack
    arguments (none of these helpers takes a stack argument);
  * the full low page (0x00000-0x0FFFF), object page, source-data page, callback
    output page and the 0x0044E330 function-pointer slot page;
  * every emulated write outside the private stack.

Coverage: null and non-null objects, every tag-mask bit combination, both
container-rewrite paths, the +0x2C re-entrancy guard, six-slot loop bounds
(including a slot whose relative offset wraps across the 32-bit address space),
cached (+0x18) and fresh entries, explicit and derived byte sizes including
32-bit multiply overflow, the 0x02010000 / 0x01010000 / 0x02020000 / 0x02030000
dispatch arms, signed format boundaries, format truncation, zero/absent
relative source offsets, wrap-to-zero resolved sources, and null allocator
results. Negative controls mutate the tag mask, default format, size shift,
kind mask, slot count, relative-data offset, and the source-zero guard; each
mutant must be detected.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0036f49c"

FUNC_ADDR = 0x0036F49C
FUNC_SIZE = 472

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers 0x0036F49C and the stubs below 0x003F0000
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00010000
CB_SLOT_ADDR = 0x00440000
CB_SLOT_SIZE = 0x00010000
OBJECT_ADDR = 0x00710000
OBJECT_SIZE = 0x00010000
DATA_ADDR = 0x00730000
DATA_SIZE = 0x00010000
BUFFER_ADDR = 0x00750000
BUFFER_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2C25F0 = 0x002C25F0
STUB_2A69B0 = 0x002A69B0
STUB_2ACD38 = 0x002ACD38
STUB_CALLBACK = 0x002B0000

STUB_NAMES = {
    STUB_2C25F0: "engine_func_002c25f0",
    STUB_2A69B0: "engine_func_002a69b0",
    STUB_2ACD38: "ui_func_002acd38",
    STUB_CALLBACK: "g_TextureAllocCallback",
}

CALLBACK_SLOT = 0x0044E330

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0036f49c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0036f49c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def source_page() -> bytes:
    return bytes((index * 37 + 11) & 0xFF for index in range(DATA_SIZE))


def default_entry(index: int) -> dict:
    return {
        "w0": 2,
        "w4": 2,
        "size": 0x20,
        "scale": 1,
        "cached": 0,
        "kind": 0xDEAD0000 | index,
        "data": ("data", index),
    }


def write_entry(page: bytearray, offset: int, entry: dict, entry_address: int,
                data: bytearray) -> None:
    struct.pack_into("<I", page, offset + 0x00, entry.get("w0", 2) & 0xFFFFFFFF)
    struct.pack_into("<I", page, offset + 0x04, entry.get("w4", 2) & 0xFFFFFFFF)
    struct.pack_into("<I", page, offset + 0x08, entry.get("size", 0) & 0xFFFFFFFF)
    struct.pack_into(
        "<I", page, offset + 0x14, entry.get("scale", 1) & 0xFFFFFFFF
    )
    struct.pack_into(
        "<I", page, offset + 0x18, entry.get("cached", 0) & 0xFFFFFFFF
    )
    struct.pack_into(
        "<I", page, offset + 0x1C, entry.get("kind", 0) & 0xFFFFFFFF
    )

    field_address = entry_address + 0x0C
    spec = entry.get("data")
    if spec is None:
        relative = 0
    elif spec[0] == "data":
        relative = (DATA_ADDR + 0x200 * spec[1]) - field_address
    elif spec[0] == "low":
        relative = (LOW_ADDR + spec[1]) - field_address
    elif spec[0] == "wrap":
        relative = (0 - field_address) & 0xFFFFFFFF
    else:  # pragma: no cover - fixture bug guard
        raise AssertionError(f"unknown data spec {spec!r}")
    struct.pack_into("<I", page, offset + 0x0C, relative & 0xFFFFFFFF)


def build_fixtures(case: dict) -> dict:
    low = bytearray(LOW_SIZE)
    obj = bytearray(OBJECT_SIZE)
    data = bytearray(source_page())

    for offset, value in case.get("low_words", {}).items():
        struct.pack_into("<I", low, offset, value & 0xFFFFFFFF)

    struct.pack_into("<I", obj, 0x00, case.get("tag", 0x20000009) & 0xFFFFFFFF)
    struct.pack_into("<I", obj, 0x2C, case.get("init_flag", 0) & 0xFFFFFFFF)
    struct.pack_into(
        "<I", obj, 0x30, case.get("format_word", 0x02010000) & 0xFFFFFFFF
    )
    for index, entry in enumerate(case["entries"]):
        if entry is None:
            continue
        slot_offset = 0x38 + 4 * index
        if "low_eoff" in entry:
            entry_address = LOW_ADDR + entry["low_eoff"]
            page = low
            offset = entry["low_eoff"]
        else:
            entry_offset = entry.get("eoff", 0x1000 + index * 0x200)
            entry_address = OBJECT_ADDR + entry_offset
            page = obj
            offset = entry_offset
        relative = (entry_address - (OBJECT_ADDR + slot_offset)) & 0xFFFFFFFF
        struct.pack_into("<I", obj, slot_offset, relative)
        write_entry(page, offset, entry, entry_address, data)

    return {"low": bytes(low), "object": bytes(obj), "data": bytes(data)}


# ---------------------------------------------------------------------- runner
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(CB_SLOT_ADDR, CB_SLOT_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(BUFFER_ADDR, BUFFER_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.callback_index = 0
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C25F0:
            self._log(address, r0, r1)
            result = (
                0xC25F0000
                | ((r0 >> 4) & 0x0FFF)
                | ((r1 & 0xFF) << 12)
            ) & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_2A69B0:
            self._log(address, r0, r1, r2)
        elif address == STUB_2ACD38:
            self._log(address, r0, r1, r2)
            if r2:
                payload = bytes(self.uc.mem_read(r1, r2))
                self.uc.mem_write(r0, payload)
                uc.reg_write(arm.UC_ARM_REG_R0, (r0 + r2) & 0xFFFFFFFF)
        elif address == STUB_CALLBACK:
            self._log(address, r0, r1, r2, r3)
            self.callback_index += 1
            if self.case.get("callback_null", False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    BUFFER_ADDR + 0x100 * (self.callback_index - 1),
                )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.callback_index = 0
        self.case = case

        fixtures = build_fixtures(case)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(LOW_ADDR, fixtures["low"])
        self.uc.mem_write(OBJECT_ADDR, fixtures["object"])
        self.uc.mem_write(DATA_ADDR, fixtures["data"])
        self.uc.mem_write(BUFFER_ADDR, b"\xCC" * BUFFER_SIZE)
        self.uc.mem_write(CB_SLOT_ADDR, b"\x00" * CB_SLOT_SIZE)
        self.uc.mem_write(CALLBACK_SLOT, struct.pack("<I", STUB_CALLBACK))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(
            arm.UC_ARM_REG_R0, case.get("object", OBJECT_ADDR) & 0xFFFFFFFF
        )
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "low": bytes(self.uc.mem_read(LOW_ADDR, LOW_SIZE)),
                "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "buffer": bytes(self.uc.mem_read(BUFFER_ADDR, BUFFER_SIZE)),
                "cb_slot": bytes(self.uc.mem_read(CB_SLOT_ADDR, CB_SLOT_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            first = next(
                index
                for index, (left, right) in enumerate(zip(value, cand["fixtures"][key]))
                if left != right
            )
            problems.append(
                f"fixture {key} differs first at +0x{first:x}:\n"
                f"    orig={value[first:first + 16]!r}\n"
                f"    cand={cand['fixtures'][key][first:first + 16]!r}"
            )
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes:\n    orig="
            + repr(orig["unexpected_writes"])
            + "\n    cand="
            + repr(cand["unexpected_writes"])
        )
    return problems


# ------------------------------------------------------------------- case table
def make_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "tag": 0x20000009,
        "init_flag": 0,
        "format_word": 0x02010000,
        "entries": [default_entry(index) for index in range(6)],
        "low_words": {0x2C: 0, 0x30: 0x12340000, 0x18: 1},
    }
    case.update(overrides)
    return case


def null_entries() -> list:
    return [None] * 6


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- re-entrancy guard and null-object paths
    cases.append(make_case("valid object, init guard already set", init_flag=1))
    cases.append(
        make_case(
            "null object, low init guard set",
            object=0,
            entries=null_entries(),
            low_words={0x2C: 1, 0x30: 0x12340000, 0x18: 1},
        )
    )
    cases.append(
        make_case(
            "null object, six cached low entries",
            object=0,
            entries=null_entries(),
            low_words={0x2C: 0, 0x30: 0x12340000, 0x18: 1},
        )
    )
    cases.append(
        make_case(
            "null object, zero low format word",
            object=0,
            entries=null_entries(),
            low_words={0x2C: 0, 0x30: 0, 0x18: 1},
        )
    )
    # The low page doubles as the container when the tag gate fails: entry 0
    # resolves to address 0, so its +0x18/0x0C fields come from the low page.
    cases.append(
        make_case(
            "null object, low-page default dispatch",
            object=0,
            entries=null_entries(),
            low_words={
                0x2C: 0,
                0x30: 0x02010000,
                0x18: 0,
                0x08: 0x10,
                0x0C: 0x1FF4,  # 0x0C field + 0x1FF4 -> 0x2000
            },
        )
    )
    cases.append(
        make_case(
            "null object, low-page raster dispatch",
            object=0,
            entries=null_entries(),
            low_words={
                0x2C: 0,
                0x30: 0x01010000,
                0x18: 0,
                0x08: 0x10,
                0x0C: 0x1FF4,
            },
        )
    )

    # --- tag mask bits: each required bit and extra bits
    for tag in (
        0x20000008,
        0x20000001,
        0x00000009,
        0x20000000,
        0x00000000,
        0x2000000B,
        0xFFFFFFFF,
    ):
        fail = (tag & 0x20000009) != 0x20000009
        cases.append(
            make_case(
                f"tag 0x{tag:08x}",
                tag=tag,
                low_words={
                    0x2C: 0,
                    0x30: 0x02010000,
                    0x18: 1,
                }
                if fail
                else {0x2C: 0, 0x30: 0x12340000, 0x18: 1},
            )
        )

    # --- format truncation and the default arm
    cases.append(make_case("format word zero selects default"))
    cases.append(make_case("format word truncated 0x0201ABCD", format_word=0x0201ABCD))
    cases.append(
        make_case("format word truncated 0x0101FFFF", format_word=0x0101FFFF)
    )
    cases.append(
        make_case("format word truncated 0x0202FFFF", format_word=0x0202FFFF)
    )

    # --- six-slot loop: cached mix, bound, repeated entries
    mixed = [default_entry(index) for index in range(6)]
    for index in (0, 2, 4):
        mixed[index]["cached"] = 0xAB000000 | index
    cases.append(make_case("mixed cached and fresh entries", entries=mixed))

    all_cached = [default_entry(index) for index in range(6)]
    for entry in all_cached:
        entry["cached"] = 0xCD000000
    cases.append(make_case("all entries cached", entries=all_cached))

    repeated = [None] * 6
    for index in range(6):
        repeated[index] = default_entry(0)
    cases.append(make_case("six slots share one fresh entry", entries=repeated))

    repeated_null = [None] * 6
    for index in range(6):
        repeated_null[index] = {
            "w0": 2,
            "w4": 2,
            "size": 0x08,
            "scale": 1,
            "data": ("data", 0),
            "eoff": 0x1200,
        }
    cases.append(
        make_case(
            "six slots share one entry, null allocator",
            format_word=0x02020000,
            entries=repeated_null,
            callback_null=True,
        )
    )

    # --- explicit and derived sizes
    derived = [default_entry(index) for index in range(6)]
    derived[1]["size"] = 0
    derived[1]["w0"] = 3
    derived[1]["w4"] = 5
    derived[1]["scale"] = 7
    cases.append(make_case("derived size 3*5*7>>3", entries=derived))

    overflow = [default_entry(index) for index in range(6)]
    overflow[2]["size"] = 0
    overflow[2]["w0"] = 0xFFFFFFFF
    overflow[2]["w4"] = 3
    overflow[2]["scale"] = 1
    cases.append(make_case("derived size 32-bit product", entries=overflow))

    zero_product = [default_entry(index) for index in range(6)]
    zero_product[3]["size"] = 0
    zero_product[3]["w0"] = 0x10000
    zero_product[3]["w4"] = 0x10000
    zero_product[3]["scale"] = 0xFFFFFFFF
    cases.append(make_case("derived size wraps to zero", entries=zero_product))

    for size in (0, 1, 0xFFFFFFFF, 0x80000000):
        sized = [default_entry(index) for index in range(6)]
        sized[4]["size"] = size
        cases.append(make_case(f"explicit size 0x{size:08x}", entries=sized))

    # --- relative-source variants for every dispatch arm
    for label, spec in (
        ("absent", None),
        ("present", ("data", 3)),
        ("low page", ("low", 0x3000)),
        ("wrap to zero", ("wrap",)),
    ):
        entries = [default_entry(index) for index in range(6)]
        entries[1]["data"] = spec
        cases.append(
            make_case(f"default arm, source {label}", entries=entries)
        )
        entries = [default_entry(index) for index in range(6)]
        entries[1]["data"] = spec
        cases.append(
            make_case(
                f"raster arm, source {label}",
                format_word=0x01010000,
                entries=entries,
            )
        )
        entries = [default_entry(index) for index in range(6)]
        entries[1]["data"] = spec
        cases.append(
            make_case(
                f"packed 0x20000 arm, source {label}",
                format_word=0x02020000,
                entries=entries,
            )
        )
        entries = [default_entry(index) for index in range(6)]
        entries[1]["data"] = spec
        cases.append(
            make_case(
                f"packed 0x30000 arm, source {label}",
                format_word=0x02030000,
                entries=entries,
            )
        )

    # --- signed format boundaries and non-matching values
    for format in (
        0x00010000,
        0x01000000,
        0x02000000,
        0x0200FFFF,
        0x03000000,
        0x7FFF0000,
        0x80000000,
        0xFF000000,
    ):
        cases.append(make_case(f"non-matching format 0x{format:08x}",
                               format_word=format))

    # --- slot relative offset wraps across the address space into the low page
    wrapped = [None] * 6
    for index in range(6):
        wrapped[index] = None
    wrapped[5] = {
        "low_eoff": 0x1040,
        "cached": 1,
        "w0": 2,
        "w4": 2,
        "size": 0x10,
        "scale": 1,
        "data": ("low", 0x2000),
    }
    cases.append(make_case("slot relative offset wraps below zero",
                           entries=wrapped))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_0036f49c (0x0036f49c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("tag_mask", "constexpr u32 kObjectTypeMask = 0x20000009;",
         "constexpr u32 kObjectTypeMask = 0x20000008;"),
        ("default_format", "constexpr u32 kFormatDefault02010000 = 0x02010000u;",
         "constexpr u32 kFormatDefault02010000 = 0x02010001u;"),
        ("size_shift", "constexpr u32 kDerivedSizeShift = 3;",
         "constexpr u32 kDerivedSizeShift = 4;"),
        ("kind_mask", "constexpr u32 kKindMask = 0x00030000;",
         "constexpr u32 kKindMask = 0x00020000;"),
        ("slot_count", "constexpr u32 kSlotCount = 6;",
         "constexpr u32 kSlotCount = 5;"),
        ("data_offset", "constexpr u32 kEntryData0C = 0x0C;",
         "constexpr u32 kEntryData0C = 0x10;"),
        ("source_guard",
         "if (source != 0) {\n                        engine_func_002a69b0(source, buffer, size);",
         "if (source != 1) {\n                        engine_func_002a69b0(source, buffer, size);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
