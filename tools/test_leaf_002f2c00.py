#!/usr/bin/env python3
"""Differential test for the 0x002F2C00 span of leaf_batch45_b.cpp.

The 572-byte ledger row is the second half of the text-entry routine that begins
at ui_func_002f2a5c (0x002F2A5C).  Its predecessor raw block branches into three
internal entry points of the span, so the reconstruction exposes one ordinary
C++ function per entry point:

    0x002F2C00  ui_func_002f2c00   key-input entry
    0x002F2C94  ui_func_002f2c94   cursor-move entry
    0x002F2CF8  ui_func_002f2cf8   redraw-only entry (state == 1)

For each entry point the pinned original is emulated from that address with the
register and stack context the first half establishes (r4 = object, r5 = -1,
r6 = obj->x, r7 = obj->y, r8 = object + 0x21, sb = glyph table, sl = 0x27), and
the candidate is executed as a normal AAPCS function.  Compared outputs:

  * the return value r0 and the continuation PC (TRAP);
  * the callee-saved r4-r11 after return (sentinel values on both sides) and
    the expected stack-reclamation difference (the original pops its caller's
    frame; the candidate balances its own);
  * the ordered helper log: key predicate, both draw calls, and the sprintf
    call with the format string and the two arguments read as C strings;
  * the bytes written into the sprintf destination;
  * the whole 0x1000-byte object page and the whole 0x1000-byte .data page that
    holds the glyph table and the shared probe byte at 0x004724C9.

Coverage: both key-predicate short-circuit orders, the state-2 paths, "OK" with
empty and non-empty name, "BS" with positive/zero/negative length, the filler
cursor (0x26 -> 0x27), every glyph index 0..0x25, index boundaries 0x29/0x2A/
0x1000/0x7FFFFFFF/0x80000000, length == capacity and length > capacity,
suppress_draw zero and non-zero, and signed x/y wrap-around.

Negative controls mutate the grid bound, the "OK" cursor value and the returned
x offset; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_002f2c00"

IMG_BASE = 0x00100000
FUNC_ADDR = 0x002F2C00
FUNC_SIZE = 572

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
OBJ_ADDR = 0x00700000
OBJ_SIZE = 0x00001000
DATA_ADDR = 0x00472000  # covers 0x004724C9 and 0x004724F0
DATA_SIZE = 0x00001000
RODATA_ADDR = 0x00750000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
FAKE_FRAME = STACK_ADDR + STACK_SIZE - 0x200

# Original helper targets; stubs sit at the same addresses for both machines.
STUB_KEY = 0x002BFFBC
STUB_DRAW = 0x002829F0
STUB_SPRINTF = 0x002BE7FC

STUB_NAMES = {
    STUB_KEY: "ui_func_002bffbc",
    STUB_DRAW: "ui_func_002829f0",
    STUB_SPRINTF: "ui_func_002be7fc",
}
THUMB_STUBS = {STUB_SPRINTF}

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
SENTINEL = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}

GLYPH_TABLE_ADDR = 0x004724F0
PROBE_ADDR = 0x004724C9

# Object layout (see the reconstruction comment in leaf_batch45_b.cpp).
OFF_NAME = 0x21
OFF_EXT = 0x1C
NAME_CAPACITY = 9

ENTRIES = (
    ("key-input", 0x002F2C00, "ui_func_002f2c00"),
    ("cursor-move", 0x002F2C94, "ui_func_002f2c94"),
    ("redraw", 0x002F2CF8, "ui_func_002f2cf8"),
)


_ORIG_CODE: bytes | None = None


def get_orig_bytes() -> bytes:
    global _ORIG_CODE
    if _ORIG_CODE is None:
        with open(ORIG_BIN, "rb") as handle:
            handle.seek(FUNC_ADDR - IMG_BASE)
            _ORIG_CODE = handle.read(FUNC_SIZE)
    return _ORIG_CODE


def orig_data_page() -> bytes:
    """The pinned .data page holding the glyph table and the probe byte."""
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(DATA_ADDR - IMG_BASE)
        return handle.read(DATA_SIZE)


def elf_parts(path: Path):
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]

    def name_at(offset: int) -> str:
        end = shstrtab.find(b"\x00", offset)
        return shstrtab[offset:end].decode("ascii", errors="replace")

    named = {}
    for section in sections:
        named[name_at(section[0])] = data[section[4] : section[4] + section[5]]
    return named


def build_image(obj_file: Path, entry_name: str,
                base: int) -> tuple[bytes, bytes]:
    """Extract one entry symbol and resolve its relocations at `base`."""
    funcs = extract_elf_functions_detailed(obj_file)
    found = None
    for name, value in funcs.items():
        if entry_name in name:
            found = value
            break
    if found is None:
        raise RuntimeError(f"{entry_name} not found in {obj_file}: {sorted(funcs)}")

    raw, relocs = found
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation {rel.symbol_name}")
            offset = target - (base + rel.offset + 8)
            if target in THUMB_STUBS:
                if offset & 3:
                    raise RuntimeError(f"unaligned Thumb target 0x{target:08x}")
                instruction = (
                    0xFA000000
                    | ((offset >> 2) & 0x00FFFFFF)
                    | ((offset & 2) << 23)
                )
                struct.pack_into("<I", code, rel.offset, instruction)
            else:
                original = struct.unpack_from("<I", code, rel.offset)[0]
                struct.pack_into(
                    "<I",
                    code,
                    rel.offset,
                    (original & 0xFF000000) | ((offset >> 2) & 0x00FFFFFF),
                )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 to .rodata.str1.1
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"({rel.symbol_name})"
            )

    rodata = elf_parts(obj_file).get(".rodata.str1.1", b"")
    return bytes(code), rodata


def compile_candidate() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return obj_file


def compile_mutant(name: str, old: str, new: str) -> Path:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return obj_file


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        self.call_log: list = []
        self.case: dict = {}
        self.sprintf_buffers: list = []

    def _on_stub(self, uc, address, size, user_data) -> None:
        if address == STUB_KEY:
            key = uc.reg_read(arm.UC_ARM_REG_R0)
            self.call_log.append((STUB_NAMES[address], (key,)))
            pressed = self.case.get("pressed", {}).get(key & 0xFFFFFFFF, 0)
            uc.reg_write(arm.UC_ARM_REG_R0, pressed & 0xFFFFFFFF)
        elif address == STUB_DRAW:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc.reg_read(arm.UC_ARM_REG_R3)
            self.call_log.append((STUB_NAMES[address], (r0, r1, r2, r3)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x28290200)
        elif address == STUB_SPRINTF:
            dst = uc.reg_read(arm.UC_ARM_REG_R0)
            fmt = read_c_string(uc, uc.reg_read(arm.UC_ARM_REG_R1))
            first = read_c_string(uc, uc.reg_read(arm.UC_ARM_REG_R2))
            second = read_c_string(uc, uc.reg_read(arm.UC_ARM_REG_R3))
            self.call_log.append((STUB_NAMES[address], (fmt, first, second)))
            payload = first + second
            uc.mem_write(dst, payload + b"\x00")
            self.sprintf_buffers.append(bytes(uc.mem_read(dst, 0x14)))
            uc.reg_write(arm.UC_ARM_REG_R0, len(payload))
        else:  # pragma: no cover
            raise AssertionError(f"unexpected stub 0x{address:08x}")

    def run_original(self, code: bytes, data_page: bytes, case: dict) -> dict:
        return self._run(code, data_page, case, original=True)

    def run_candidate(self, code: bytes, data_page: bytes, case: dict) -> dict:
        return self._run(code, data_page, case, original=False)

    def _run(self, code: bytes, data_page: bytes, case: dict, original: bool) -> dict:
        self.call_log = []
        self.case = case
        self.sprintf_buffers = []

        entry = case["entry_addr"]
        # The original span (including its literal pool) is always laid out at
        # its pinned address.  Only the candidate body is moved to the entry.
        self.uc.mem_write(FUNC_ADDR, get_orig_bytes())
        if not original:
            self.uc.mem_write(entry, code)
        self.uc.mem_write(OBJ_ADDR, build_object(case))
        self.uc.mem_write(DATA_ADDR, data_page)
        self.uc.mem_write(RODATA_ADDR, b"\x00" * RODATA_SIZE)
        if case.get("rodata"):
            self.uc.mem_write(RODATA_ADDR, case["rodata"])
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        x = to_u32(case["x"])
        y = to_u32(case["y"])

        if original:
            # r4-r11 must survive through the shared epilogue pop.
            frame = struct.pack(
                "<9I",
                SENTINEL["r4"], SENTINEL["r5"], SENTINEL["r6"], SENTINEL["r7"],
                SENTINEL["r8"], SENTINEL["r9"], SENTINEL["r10"], SENTINEL["r11"],
                TRAP_ADDR,
            )
            self.uc.mem_write(FAKE_FRAME, frame)
            self.uc.reg_write(arm.UC_ARM_REG_SP, FAKE_FRAME - 0x14)
            self.uc.reg_write(arm.UC_ARM_REG_R4, OBJ_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R5, 0xFFFFFFFF)
            self.uc.reg_write(arm.UC_ARM_REG_R6, x)
            self.uc.reg_write(arm.UC_ARM_REG_R7, y)
            self.uc.reg_write(arm.UC_ARM_REG_R8, OBJ_ADDR + OFF_NAME)
            self.uc.reg_write(arm.UC_ARM_REG_R9, GLYPH_TABLE_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R10, 0x27)
            self.uc.reg_write(arm.UC_ARM_REG_R11, 0)
            self.uc.reg_write(arm.UC_ARM_REG_R0, 0)
            self.uc.reg_write(arm.UC_ARM_REG_R1, 0)
            self.uc.reg_write(arm.UC_ARM_REG_R2, 0)
            self.uc.reg_write(arm.UC_ARM_REG_R3, 0)
        else:
            self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
            self.uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, 0)
            self.uc.reg_write(arm.UC_ARM_REG_R2, 0)
            self.uc.reg_write(arm.UC_ARM_REG_R3, 0)
            for name, value in SENTINEL.items():
                self.uc.reg_write(CALLEE_SAVED[name], value)

        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

        try:
            self.uc.emu_start(entry, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "sprintf_buffers": list(self.sprintf_buffers),
            "object": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
        }


def to_u32(value: int) -> int:
    return value & 0xFFFFFFFF


def build_object(case: dict) -> bytes:
    page = bytearray(OBJ_SIZE)
    struct.pack_into("<i", page, 0x00, case["x"])
    struct.pack_into("<i", page, 0x04, case["y"])
    struct.pack_into("<i", page, 0x08, case["state"])
    struct.pack_into("<i", page, 0x0C, case["cursor"])
    struct.pack_into("<i", page, 0x10, case["length"])
    struct.pack_into("<i", page, 0x14, case["capacity"])
    struct.pack_into("<i", page, 0x18, case["suppress"])
    extension = case.get("extension", b".EP")
    page[OFF_EXT : OFF_EXT + 5] = (extension + b"\x00" * 5)[:5]
    name = case.get("name", b"ABC")
    page[OFF_NAME : OFF_NAME + 10] = (name + b"\x00" * 10)[:10]
    # Sentinels around the live fields must stay untouched.
    page[0x100:0x110] = b"\xA5" * 0x10
    return bytes(page)


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc"):
        if orig[key] != cand[key]:
            problems.append(f"{key}: orig={orig[key]!r} cand={cand[key]!r}")
    if orig["callee_saved"] != cand["callee_saved"]:
        problems.append(
            f"callee_saved: orig={orig['callee_saved']!r} "
            f"cand={cand['callee_saved']!r}"
        )
    if orig["sp"] != FAKE_FRAME + 0x24:
        problems.append(f"original did not pop its frame: sp={orig['sp']:#x}")
    if cand["sp"] != ENTRY_SP:
        problems.append(f"candidate stack unbalanced: sp={cand['sp']:#x}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    if orig["sprintf_buffers"] != cand["sprintf_buffers"]:
        problems.append(
            "sprintf buffers:\n    orig=" + repr(orig["sprintf_buffers"])
            + "\n    cand=" + repr(cand["sprintf_buffers"])
        )
    if orig["object"] != cand["object"]:
        for index, (left, right) in enumerate(
            zip(orig["object"], cand["object"])
        ):
            if left != right:
                problems.append(
                    f"object page differs at +0x{index:03x}: "
                    f"orig=0x{left:02x} cand=0x{right:02x}"
                )
                break
    if orig["data"] != cand["data"]:
        for index, (left, right) in enumerate(zip(orig["data"], cand["data"])):
            if left != right:
                problems.append(
                    f".data page differs at +0x{index:03x}: "
                    f"orig=0x{left:02x} cand=0x{right:02x}"
                )
                break
    return problems


def base_case(entry, title: str, **overrides) -> dict:
    case = {
        "title": title,
        "entry_addr": entry[1],
        "entry_symbol": entry[2],
        "x": 0xB6,
        "y": 0x64,
        "state": 0,
        "cursor": 0,
        "length": 3,
        "capacity": NAME_CAPACITY,
        "suppress": 0,
        "pressed": {},
        "extension": b".EP",
        "name_bytes": b"ABC",
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    keys, cursor, redraw = ENTRIES
    cases: list[dict] = []

    # ---- key-input entry: predicate short-circuit orders
    cases.append(base_case(keys, "key 0 pressed, append at cursor 0",
                           pressed={0: 1}, cursor=0))
    cases.append(base_case(keys, "key 0 released, key 0x14 pressed",
                           pressed={0x14: 1}, cursor=7, length=0))
    cases.append(base_case(keys, "both navigation keys released",
                           pressed={}, cursor=11, length=4))
    cases.append(base_case(keys, "key 1 pressed -> state 2",
                           pressed={1: 1}, cursor=0x26, length=2))
    cases.append(base_case(keys, "key 0x16 pressed -> state 2",
                           pressed={0x16: 1}, cursor=0x26, length=2))
    cases.append(base_case(keys, "key 1 short-circuits key 0x16",
                           pressed={1: 1, 0x16: 1}, cursor=5))
    cases.append(base_case(keys, "key 0 short-circuits key 0x14",
                           pressed={0: 1, 0x14: 1}, cursor=5))
    cases.append(base_case(keys, "key predicate non-unit value",
                           pressed={0: 0x80000000}, cursor=5))

    # ---- "OK" cursor 0x28
    cases.append(base_case(keys, "OK with non-empty name", pressed={0: 1},
                           cursor=0x28, length=9, name_bytes=b"ABCDEFGHI"))
    cases.append(base_case(keys, "OK with empty name", pressed={0: 1},
                           cursor=0x28, length=0))
    cases.append(base_case(keys, "OK with negative length", pressed={0: 1},
                           cursor=0x28, length=-1))

    # ---- "BS" cursor 0x27 (delete path, signed length compare)
    cases.append(base_case(keys, "BS with length 3", pressed={0: 1},
                           cursor=0x27, length=3))
    cases.append(base_case(keys, "BS with length 1", pressed={0: 1},
                           cursor=0x27, length=1))
    cases.append(base_case(keys, "BS with length 0", pressed={0: 1},
                           cursor=0x27, length=0))
    cases.append(base_case(keys, "BS with negative length", pressed={0: 1},
                           cursor=0x27, length=-2))

    # ---- filler cursor 0x26
    cases.append(base_case(keys, "filler cursor with key 0", pressed={0: 1},
                           cursor=0x26, length=2))
    cases.append(base_case(keys, "filler cursor without key", pressed={},
                           cursor=0x26, length=2))

    # ---- every glyph index plus signed/unsigned index boundaries
    for index in (0, 1, 25, 26, 35, 36, 37):
        cases.append(base_case(keys, f"append glyph {index}", pressed={0: 1},
                               cursor=index, length=0))
    for index in (0x29, 0x2A, 0x1000, 0x7FFFFFFF, -1, -2, -0x1000,
                  -0x80000000):
        cases.append(base_case(keys, f"cursor boundary {index}", pressed={0: 1},
                               cursor=index, length=4))

    # ---- length / capacity boundaries
    for length in (0, 8, 9, 10, -1):
        cases.append(base_case(keys, f"append with length {length}",
                               pressed={0: 1}, cursor=5, length=length))
    cases.append(base_case(keys, "capacity zero", pressed={0: 1}, cursor=5,
                           length=0, capacity=0))
    cases.append(base_case(keys, "negative capacity", pressed={0: 1}, cursor=5,
                           length=-1, capacity=-1))

    # ---- cursor-move entry
    for index in (0x26, 0x27, 0x28, 0, 0x25, 0x29):
        cases.append(base_case(cursor, f"move entry cursor {index}",
                               cursor=index, length=3))
    cases.append(base_case(cursor, "move entry with empty name", cursor=5,
                           length=0))
    cases.append(base_case(cursor, "move entry with full name", cursor=5,
                           length=9, name_bytes=b"ABCDEFGHI"))

    # ---- redraw entry: suppress_draw zero and non-zero, signed returns
    for suppress in (0, 1, -1, 0x7FFFFFFF, -0x80000000):
        cases.append(base_case(redraw, f"redraw suppress {suppress}",
                               suppress=suppress, length=3))
    for x, y in ((0, 0), (-1, -1), (0x7FFFFFFF, 0x7FFFFFFF),
                 (-0x80000000, -0x80000000), (0x7FFFFFFF, -0x80000000),
                 (0xB6, 0x64)):
        cases.append(base_case(redraw, f"redraw origin {x}/{y}", x=x, y=y,
                               suppress=0))
    cases.append(base_case(redraw, "redraw with empty name", length=0))
    cases.append(base_case(redraw, "redraw with long name", length=9,
                           name_bytes=b"ABCDEFGHI"))
    cases.append(base_case(redraw, "redraw with out-of-range length", length=10,
                           name_bytes=b"ABCDEFGHIJ"))

    return cases


def run_case(orig_code, cand_code, data_page, rodata, case) -> list[str]:
    original = Runner().run_original(orig_code, data_page, case)
    candidate_case = dict(case)
    candidate_case["rodata"] = rodata
    candidate = Runner().run_candidate(cand_code, data_page, candidate_case)
    return compare(original, candidate)


def main() -> None:
    print("Testing the 0x002F2C00 span (three entry points)...")
    obj_file = compile_candidate()
    orig_code = get_orig_bytes()
    data_page = orig_data_page()
    if data_page[GLYPH_TABLE_ADDR - DATA_ADDR : GLYPH_TABLE_ADDR - DATA_ADDR + 38] != (
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    ):
        raise RuntimeError("glyph table mismatch in the pinned image")

    images = {}
    for entry in ENTRIES:
        code, rodata = build_image(obj_file, entry[2], entry[1])
        images[entry[1]] = (code, rodata)
        print(f"  {entry[0]:12s} 0x{entry[1]:08x} {entry[2]} "
              f"({len(code)} B candidate, relocations resolved)")

    cases = make_cases()
    passed = 0
    for case in cases:
        code, rodata = images[case["entry_addr"]]
        problems = run_case(orig_code, code, data_page, rodata, case)
        if problems:
            print(f"  [FAIL] {case['title']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['title']}")

    print("\nNegative controls:")
    for name, old, new in (
        ("grid_bound", "constexpr u32 kGridFiller = 0x26u;",
         "constexpr u32 kGridFiller = 0x25u;"),
        ("confirm_cursor", "constexpr u32 kConfirm = 0x28u;",
         "constexpr u32 kConfirm = 0x27u;"),
        ("return_offset", "return static_cast<u32>(obj->x) + 0x72u;",
         "return static_cast<u32>(obj->x) + 0x70u;"),
    ):
        mutant_obj = compile_mutant(name, old, new)
        detected = False
        for entry in ENTRIES:
            code, mutant_rodata = build_image(mutant_obj, entry[2], entry[1])
            for case in cases:
                if case["entry_addr"] != entry[1]:
                    continue
                original = Runner().run_original(orig_code, data_page, case)
                mutant_case = dict(case)
                mutant_case["rodata"] = mutant_rodata
                bad = Runner().run_candidate(code, data_page, mutant_case)
                if compare(original, bad):
                    detected = True
                    break
            if detected:
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
