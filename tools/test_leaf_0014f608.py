#!/usr/bin/env python3
"""Differential test for func_0014f608 (0x0014f608) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_0014f608 body, and
runs the pinned original (extracted/exefs/code.bin) against the candidate in a
single reusable Unicorn ARM machine with identical fixtures.

The function is a leaf (no direct or indirect calls), so there is no helper
call log to compare; instead the code hook records every executed PC and the
runner asserts that neither version transfers outside the 0x400-byte function
window.  The fifth argument is read from the incoming stack slot.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the two words above the entry SP (the fifth argument and its neighbour,
    which must stay untouched);
  * the complete 64 KiB heap page, pre-filled with a distinct sentinel word
    per address so every write, zero-fill gap and untouched byte is visible;
  * any emulated write outside the heap page and the private stack;
  * any executed PC outside the function window (proves there is no call).

Coverage: leading-remnant threshold 0x13/0x14/0x15 and 0..3-byte padding, plus
the wrapped-gap unsigned case; trailing-remnant threshold 3/4/0x13/0x14/0x15
and the wrapped-tail case; direction 0, 1, 2, 0x100, 0x101, 0xFFFFFFFE and
0xFFFFFFFF with the split-padding byte 0 and non-zero; every 7-bit preamble
offset form (0, 3, 8, 0x12, 0x7F, plus bit 15 and the low attribute byte set);
free-list head / middle / tail / single-node positions; empty, one-node,
two-node and degenerate used lists (tail with a non-null next, head with a null
tail, tail aliasing the new header, node inside the zeroed span); attribute
source 0x0000..0xFFFF; option word bit 0 and neighbouring bits; fill lengths
0..0x41 around the floor-to-word rounding; size wraps below the header; and an
unmapped-write check.  Negative controls mutate each recovered constant and
branch predicate and must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0014f608"

FUNC_ADDR = 0x0014F608
FUNC_SIZE = 484
FUNC_WINDOW = 0x400  # both bodies fit; also bounds the no-call PC check

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x00100000..0x00300000 (function 0x0014F608)
HEAP_ADDR = 0x00500000
HEAP_SIZE = 0x00010000  # one 64 KiB page holds the list, blocks and neighbours
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Block-list view passed in r0.  The fixture page stands in for the caller's
# heapBase: the list occupies +0x24 and the zero-fill option word is read from
# four bytes before it (`ldr r3,[r0,#-4]`), i.e. fixture + 0x20.
LIST_OFF = 0x24
OPTIONS_OFF = LIST_OFF - 4

# Fixture placement inside the heap page.
FREE_OFF = 0x200
LEFT_FREE_OFF = 0x100
RIGHT_FREE_OFF = 0x500
USED_A_OFF = 0x900
USED_B_OFF = 0xA00
USED_C_OFF = 0xB00

SIGNATURE_FREE = 0x4652
SIGNATURE_USED = 0x5544

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

# One distinct sentinel word per address; every unmodified byte is compared.
SENTINEL_PAGE = b"".join(
    struct.pack("<I", 0xA5A50000 | offset)
    for offset in range(0, HEAP_SIZE, 4)
)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("func_0014f608")
    if candidate is None:
        raise RuntimeError(
            f"func_0014f608 not found in {obj_file}: {sorted(funcs)}"
        )
    code_raw, relocs = candidate
    if relocs:
        raise RuntimeError(
            "func_0014f608 must be a leaf with no relocations, found: "
            + repr([(rel.relocation_type, rel.symbol_name) for rel in relocs])
        )
    return bytes(code_raw)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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
# A block is (offset, signature, attribute, size, prev_offset, next_offset);
# every offset is relative to HEAP_ADDR and None means a null link.
def free_block(off, prev=None, next_=None, size=0x40, attribute=0,
               signature=SIGNATURE_FREE):
    return (off, signature, attribute, size, prev, next_)


def used_block(off, prev=None, next_=None, size=0x40, attribute=0):
    return (off, SIGNATURE_USED, attribute, size, prev, next_)


def build_heap(case: dict) -> bytes:
    page = bytearray(SENTINEL_PAGE)
    base = HEAP_ADDR

    def address(off):
        return 0 if off is None else base + off

    struct.pack_into("<I", page, OPTIONS_OFF, case["options"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, LIST_OFF + 0x00, address(case["free_head"]))
    struct.pack_into("<I", page, LIST_OFF + 0x04, address(case["free_tail"]))
    struct.pack_into("<I", page, LIST_OFF + 0x08, address(case["used_head"]))
    struct.pack_into("<I", page, LIST_OFF + 0x0C, address(case["used_tail"]))
    struct.pack_into("<H", page, LIST_OFF + 0x10, case["attribute_source"] & 0xFFFF)
    struct.pack_into("<H", page, LIST_OFF + 0x12, 0x5A5A)  # never read
    page[LIST_OFF + 0x14] = case["split_padding"] & 0xFF
    page[LIST_OFF + 0x15] = 0x5A  # never read

    for off, signature, attribute, size, prev, next_ in case["blocks"]:
        struct.pack_into(
            "<HHIII",
            page,
            off,
            signature & 0xFFFF,
            attribute & 0xFFFF,
            size & 0xFFFFFFFF,
            address(prev),
            address(next_),
        )
    return bytes(page)


def make_case(name: str, *, blocks, free_head, free_tail, used_head=None,
              used_tail=None, payload_off: int = 0x210, size: int = 0x40,
              mode: int = 0, options: int = 0, attribute_source: int = 0,
              split_padding: int = 0) -> dict:
    case = {
        "name": name,
        "options": options,
        "attribute_source": attribute_source,
        "split_padding": split_padding,
        "blocks": list(blocks),
        "free_head": free_head,
        "free_tail": free_tail,
        "used_head": used_head,
        "used_tail": used_tail,
        "payload_off": payload_off,
        "size": size,
        "mode": mode,
    }
    case["heap"] = build_heap(case)
    return case


def single(name: str, *, free_size: int = 0x100, free_attribute: int = 0,
           free_signature: int = SIGNATURE_FREE, **kw) -> dict:
    """Selected free block is the only node and both links are null."""
    blocks = [free_block(FREE_OFF, None, None, free_size, free_attribute,
                         free_signature)]
    return make_case(
        name,
        blocks=blocks,
        free_head=FREE_OFF,
        free_tail=FREE_OFF,
        **kw,
    )


def chained(name: str, position: str, *, free_size: int = 0x100,
            free_attribute: int = 0, **kw) -> dict:
    """Selected free block at the head, middle or tail of three nodes."""
    if position == "head":
        blocks = [
            free_block(FREE_OFF, None, RIGHT_FREE_OFF, free_size, free_attribute),
            free_block(RIGHT_FREE_OFF, FREE_OFF, None, 0x40),
        ]
        head, tail = FREE_OFF, RIGHT_FREE_OFF
    elif position == "middle":
        blocks = [
            free_block(LEFT_FREE_OFF, None, FREE_OFF, 0x40),
            free_block(FREE_OFF, LEFT_FREE_OFF, RIGHT_FREE_OFF, free_size,
                       free_attribute),
            free_block(RIGHT_FREE_OFF, FREE_OFF, None, 0x40),
        ]
        head, tail = LEFT_FREE_OFF, RIGHT_FREE_OFF
    elif position == "tail":
        blocks = [
            free_block(LEFT_FREE_OFF, None, FREE_OFF, 0x40),
            free_block(FREE_OFF, LEFT_FREE_OFF, None, free_size, free_attribute),
        ]
        head, tail = LEFT_FREE_OFF, FREE_OFF
    else:  # pragma: no cover - guarded by callers
        raise AssertionError(position)
    return make_case(
        name,
        blocks=blocks,
        free_head=head,
        free_tail=tail,
        **kw,
    )


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- geometry: exact fit, padding absorption, minimum remnant boundaries
    cases.append(single("exact fit absorbs the whole free block",
                        free_size=0x100, payload_off=0x210, size=0x100))
    cases.append(single("exact fit with zero fill", free_size=0x100,
                        payload_off=0x210, size=0x100, options=1))
    cases.append(single("4-byte upward padding is absorbed", free_size=0x100,
                        payload_off=0x214, size=0x40, options=1))
    cases.append(single("leading and trailing remnants at the 0x14 minimum",
                        free_size=0x54, payload_off=0x224, size=0x2c,
                        options=1))
    cases.append(single("leading gap 3 is absorbed", free_size=0x100,
                        free_attribute=3 << 8, payload_off=0x210, size=0x40))
    cases.append(single("leading gap 8 absorbed, fill starts at region start",
                        free_size=0x100, free_attribute=8 << 8,
                        payload_off=0x210, size=0x40, options=1))
    cases.append(single("leading gap 0x13 is absorbed", free_size=0x100,
                        free_attribute=0x13 << 8, payload_off=0x210, size=0x40))
    cases.append(single("leading gap 0x14 splits", free_size=0x100,
                        free_attribute=0x14 << 8, payload_off=0x210, size=0x40,
                        options=1))
    cases.append(single("leading gap 0x15 splits", free_size=0x100,
                        free_attribute=0x15 << 8, payload_off=0x210, size=0x40))
    cases.append(single("wrapped leading gap creates a huge remnant",
                        free_size=0x100, payload_off=0x1F0, size=0x40,
                        mode=1))

    # --- direction forms and the split-padding byte
    cases.append(single("mode 0 padding 0 absorbs the leading padding",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        options=1))
    cases.append(single("mode 0 padding 1 splits the leading padding",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        split_padding=1, options=1))
    cases.append(single("mode 1 padding 0 splits leading, absorbs trailing",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        mode=1, options=1))
    cases.append(single("mode 1 padding 1 splits both", free_size=0x100,
                        payload_off=0x230, size=0x40, mode=1,
                        split_padding=1, options=1))
    cases.append(single("mode 2 splits both", free_size=0x100,
                        payload_off=0x230, size=0x40, mode=2))
    cases.append(single("mode 0xffffffff splits both and sets bit 15",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        mode=0xFFFFFFFF))
    cases.append(single("mode 0xfffffffe splits both without bit 15",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        mode=0xFFFFFFFE))
    cases.append(single("mode 0x100 splits both", free_size=0x100,
                        payload_off=0x230, size=0x40, mode=0x100))
    cases.append(single("mode 0x101 splits both and sets bit 15",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        mode=0x101))
    cases.append(single("mode 0x80 splits both without bit 15",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        mode=0x80))
    cases.append(single("padding byte 0xff keeps both remnants (mode 0)",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        split_padding=0xFF))
    cases.append(single("padding byte 0x80 keeps both remnants (mode 1)",
                        free_size=0x100, payload_off=0x230, size=0x40,
                        mode=1, split_padding=0x80))

    # --- trailing-remnant boundaries (leading gap is zero)
    for free_size, label in ((0x43, "3"), (0x44, "4"), (0x53, "0x13"),
                             (0x54, "0x14"), (0x55, "0x15"),
                             (0x100, "0xc0")):
        cases.append(single(f"trailing gap {label} (size 0x40)",
                            free_size=free_size, payload_off=0x210,
                            size=0x40, options=1))
    cases.append(single("wrapped trailing gap creates a huge remnant",
                        free_size=0x30, payload_off=0x230, size=0x40))
    cases.append(single("zero-size free block with wrapped tail",
                        free_size=0, payload_off=0x210, size=0x40, options=1))

    # --- preamble offset forms (attribute bits 8..14)
    cases.append(single("preamble offset 0x7f absorbed (mode 0, padding 0)",
                        free_size=0x100, free_attribute=0x7F << 8,
                        payload_off=0x210, size=0x40))
    cases.append(single("preamble offset 0x7f split (mode 1)",
                        free_size=0x100, free_attribute=0x7F << 8,
                        payload_off=0x210, size=0x40, mode=1))
    cases.append(single("attribute bit 15 and low byte are not the offset",
                        free_size=0x100, free_attribute=0x80FF,
                        payload_off=0x230, size=0x40, mode=1))
    cases.append(single("attribute 0xffff reads offset 0x7f",
                        free_size=0x100, free_attribute=0xFFFF,
                        payload_off=0x210, size=0x40))
    cases.append(single("attribute 0x1234 reads offset 0x12",
                        free_size=0x100, free_attribute=0x1234,
                        payload_off=0x210, size=0x40))
    cases.append(single("free signature word is not read", free_size=0x100,
                        free_signature=0xDEAD, payload_off=0x230, size=0x40,
                        mode=1))

    # --- free-list positions around the unlink and both insertions
    cases.append(chained("head node with leading and trailing remnants", "head",
                         payload_off=0x230, size=0x40, mode=1,
                         split_padding=1))
    cases.append(chained("middle node with leading and trailing remnants",
                         "middle", payload_off=0x230, size=0x40, mode=1,
                         split_padding=1, options=1))
    cases.append(chained("tail node with leading and trailing remnants",
                         "tail", payload_off=0x230, size=0x40, mode=1,
                         split_padding=1))
    cases.append(chained("tail node mode 1 absorbs the trailing gap", "tail",
                         payload_off=0x230, size=0x40, mode=1))
    cases.append(chained("head node with left absorbed inserts at the head",
                         "head", payload_off=0x230, size=0x40))
    cases.append(chained("middle node keeps the address order", "middle",
                         payload_off=0x230, size=0x40, split_padding=1))

    # --- used-list states
    cases.append(single("empty used list", free_size=0x100, payload_off=0x230,
                        size=0x40, mode=1, split_padding=1))
    cases.append(make_case(
        "one used node",
        blocks=[free_block(FREE_OFF, None, None, 0x100),
                used_block(USED_A_OFF)],
        free_head=FREE_OFF, free_tail=FREE_OFF,
        used_head=USED_A_OFF, used_tail=USED_A_OFF,
        payload_off=0x230, size=0x40, mode=1, split_padding=1))
    cases.append(make_case(
        "two used nodes",
        blocks=[free_block(FREE_OFF, None, None, 0x100),
                used_block(USED_A_OFF, None, USED_B_OFF),
                used_block(USED_B_OFF, USED_A_OFF, None)],
        free_head=FREE_OFF, free_tail=FREE_OFF,
        used_head=USED_A_OFF, used_tail=USED_B_OFF,
        payload_off=0x230, size=0x40, mode=1, split_padding=1))
    cases.append(make_case(
        "degenerate head-only used list",
        blocks=[free_block(FREE_OFF, None, None, 0x100),
                used_block(USED_A_OFF)],
        free_head=FREE_OFF, free_tail=FREE_OFF,
        used_head=USED_A_OFF, used_tail=None,
        payload_off=0x230, size=0x40))
    cases.append(make_case(
        "degenerate tail node with a non-null next",
        blocks=[free_block(FREE_OFF, None, None, 0x100),
                used_block(USED_A_OFF, None, USED_B_OFF),
                used_block(USED_B_OFF, USED_A_OFF, USED_C_OFF),
                used_block(USED_C_OFF, USED_B_OFF, None)],
        free_head=FREE_OFF, free_tail=FREE_OFF,
        used_head=USED_A_OFF, used_tail=USED_B_OFF,
        payload_off=0x230, size=0x40))
    cases.append(make_case(
        "used tail aliases the new used header",
        blocks=[free_block(FREE_OFF, None, None, 0x100),
                used_block(FREE_OFF)],
        free_head=FREE_OFF, free_tail=FREE_OFF,
        used_head=FREE_OFF, used_tail=FREE_OFF,
        payload_off=0x210, size=0x100))
    cases.append(make_case(
        "used node inside the zero-filled span",
        blocks=[free_block(FREE_OFF, None, None, 0x100),
                used_block(0x214)],
        free_head=FREE_OFF, free_tail=FREE_OFF,
        used_head=0x214, used_tail=0x214,
        payload_off=0x210, size=0x100, options=1))

    # --- attribute-source low byte
    for source in (0x0000, 0x00FF, 0xFF00, 0x1234, 0xFFFF):
        cases.append(single(f"attribute source 0x{source:04x}",
                            free_size=0x100, payload_off=0x230, size=0x40,
                            attribute_source=source, mode=1,
                            split_padding=1))

    # --- option word bit 0 and neighbouring bits
    for options in (0, 1, 2, 0xFFFFFFFE, 0x80000001, 0x40000000, 0xFFFFFFFF):
        cases.append(single(f"options 0x{options:08x}", free_size=0x100,
                            payload_off=0x210, size=0x100, options=options))

    # --- zero-fill length: mode 0 + padding 1 splits both, so the fill span is
    # exactly `size` and starts at the used header.
    for size in (0, 1, 2, 3, 4, 5, 6, 7, 8, 0xB, 0xC, 0x10, 0x41):
        cases.append(single(f"fill length {size} (size 0x{size:02x})",
                            free_size=0x100, payload_off=0x230, size=size,
                            split_padding=1, options=1))

    # --- size wrap: the requested end falls below the header
    cases.append(single("requested end wraps below the header",
                        free_size=0x100, payload_off=0x210,
                        size=0xFFFFFF00, options=0))
    cases.append(single("fill length 4 with a wrapped used end",
                        free_size=0x100, free_attribute=3 << 8,
                        payload_off=0x210, size=0xFFFFFFF1, options=1))

    return cases


class Runner:
    """One reusable Unicorn machine with no helper stubs (the routine is a leaf)."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(HEAP_ADDR, HEAP_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_code, begin=CODE_ADDR,
            end=CODE_ADDR + CODE_SIZE - 1,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.pcs: list[int] = []
        self.writes: list[tuple[int, int]] = []

    def _on_code(self, uc, address: int, size: int, user_data) -> None:
        self.pcs.append(address)

    def _on_write(self, uc, access, address: int, size: int, value,
                  user_data) -> None:
        self.writes.append((address, size))

    def run(self, code: bytes, case: dict) -> dict:
        self.pcs = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_WINDOW)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(HEAP_ADDR, case["heap"])
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        # Both versions live at the same guest address; drop translations of the
        # previous code image before executing the new one.
        self.uc.ctl_flush_tb()
        # Fifth argument at the caller's stack slot, plus an untouched guard.
        self.uc.mem_write(ENTRY_SP, struct.pack("<II", case["mode"] & 0xFFFFFFFF,
                                                0xCAFEBABE))

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, HEAP_ADDR + LIST_OFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, HEAP_ADDR + FREE_OFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, HEAP_ADDR + case["payload_off"])
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["size"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=2_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        outside_pcs = sorted(
            {pc for pc in self.pcs
             if not (FUNC_ADDR <= pc < FUNC_ADDR + FUNC_WINDOW)}
        )
        unexpected_writes = sorted(
            {(address, size) for address, size in self.writes
             if not (HEAP_ADDR <= address < HEAP_ADDR + HEAP_SIZE)
             and not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)}
        )

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "stack_args": bytes(self.uc.mem_read(ENTRY_SP, 8)),
            "heap": bytes(self.uc.mem_read(HEAP_ADDR, HEAP_SIZE)),
            "outside_pcs": outside_pcs,
            "unexpected_writes": unexpected_writes,
            "call_log": [],  # the routine performs no calls
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "stack_args", "call_log",
                "outside_pcs", "unexpected_writes"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["heap"] != cand["heap"]:
        diffs = [
            (index, left, right)
            for index, (left, right) in enumerate(zip(orig["heap"], cand["heap"]))
            if left != right
        ]
        problems.append(
            "heap differs at "
            + ", ".join(
                f"+0x{index:04x}: orig=0x{left:02x} cand=0x{right:02x}"
                for index, left, right in diffs[:12]
            )
            + (f" (+{len(diffs) - 12} more)" if len(diffs) > 12 else "")
        )
    return problems


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    runner = Runner()
    passed = 0
    for case in cases:
        orig = runner.run(orig_code, case)
        cand = runner.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"(ret=0x{orig['ret']:08x}, {len(orig['heap'])} B heap)"
        )
    return passed


def main() -> None:
    print("Testing func_0014f608 (0x0014f608)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(leaf, no relocations)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        ("minimum remnant", "constexpr u32 kMinRemnant = 0x14;",
         "constexpr u32 kMinRemnant = 0x13;"),
        ("region offset mask", "constexpr u32 kRegionOffsetMask = 0x7F;",
         "constexpr u32 kRegionOffsetMask = 0xFF;"),
        ("direction bit", "constexpr u32 kDirectionBit = 0x8000;",
         "constexpr u32 kDirectionBit = 0x4000;"),
        ("zero fill option", "constexpr u32 kZeroFillOption = 1;",
         "constexpr u32 kZeroFillOption = 2;"),
        ("free signature", "constexpr u16 kFreeSignature = 0x4652;",
         "constexpr u16 kFreeSignature = 0x4653;"),
        ("used signature", "constexpr u16 kUsedSignature = 0x5544;",
         "constexpr u16 kUsedSignature = 0x5545;"),
        ("leading direction test",
         "(direction != 0 || list->split_padding != 0)",
         "(direction == 0 || list->split_padding != 0)"),
        ("trailing direction test",
         "(direction != 1 || list->split_padding != 0)",
         "(direction != 1 && list->split_padding != 0)"),
        ("used size", "used->size = used_end - header_address - kHeaderSize;",
         "used->size = used_end - header_address;"),
        ("used prev", "used->prev = used_tail;",
         "used->prev = list->used_head;"),
        ("fill threshold", "fill_length > 3", "fill_length > 4"),
        ("fill word count", "fill_length >> 2", "fill_length >> 1"),
        ("attribute source",
         "static_cast<u32>(list->attribute_source) &",
         "static_cast<u32>(list->pad_12) &"),
        ("preamble read shift",
         "block_address - ((static_cast<u32>(block->attribute) >> 8) &",
         "block_address - ((static_cast<u32>(block->attribute) >> 7) &"),
        ("free head unlink", "list->free_head = free_next;",
         "list->free_tail = free_next;"),
        ("used following link",
         ": list->used_head;", ": list->used_tail;"),
    )
    runner = Runner()
    for name, old, new in controls:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = runner.run(orig_code, case)
            bad = runner.run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
