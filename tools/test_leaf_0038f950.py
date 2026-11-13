#!/usr/bin/env python3
"""Differential test for engine_func_0038f950 (0x0038f950) using Unicorn ARM.

Compiles ``src/engine/leaf_batch36_b.cpp``, extracts the
``engine_func_0038f950`` body, resolves its twelve direct ``bl``/``b``
relocations to deterministic stubs placed at the original helper addresses, and
runs the pinned original (``extracted/exefs/code.bin``) and the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and d8-d15;
  * the ordered call log: every helper's r0-r3 (and s0 raw bits where the
    helper takes a float) plus the architected stack arguments (seven words for
    ``camp_func_002c32f8``, one for ``camp_func_002bdb2c``);
  * the complete ctx block, the global-pointer page, the target of the global
    pointer, the text-object page, the label-node page and the 72-byte shared
    constant/label fixture, all pre-filled with non-zero patterns;
  * any emulated write outside the private stack/ctx/global/text/node pages.

Coverage: the real 24-byte label table and all-zero/all-one/alternating/signed
boundary (0x80, 0x7F, 0xFF) overrides, rect and point label nodes (null and
non-null node pointer), node coordinate boundaries and halfword wrap, non-null
and null ``AsdText_func_002bda1c`` results, two text-object offsets, two global
object pointers, and two ctx base addresses.  Negative controls mutate the
label ids, panel, group stack word, loop count, sprite stride, both absolute
tables, sprite type, text flags/colour, the inner-object byte, the global byte,
the text-handle offset and the unite object offset; each mutant must be
detected.
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
SOURCE = ROOT / "src/engine/leaf_batch36_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0038f950"

FUNC_ADDR = 0x0038F950
FUNC_SIZE = 408

# The code page covers the function, every helper below 0x3F0000 and the
# shared constant/label fixture at 0x003FF12C/0x003FF15C.
CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00210000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00010000  # holds the global object pointer at 0x00432FC8
CTX_ADDR = 0x00710000
CTX_SIZE = 0x00004000
GLOBAL_ADDR = 0x00720000
GLOBAL_SIZE = 0x00002000  # needs global_object + 0xB81
TEXT_ADDR = 0x00740000
TEXT_SIZE = 0x00001000
NODE_ADDR = 0x00750000
NODE_SIZE = 0x00004000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SHARED_TABLE_ADDR = 0x003FF12C
LABEL_TABLE_ADDR = 0x003FF15C
FIXTURE_SIZE = 0x48  # shared constants 0x30 bytes + 24 label bytes

GLOBAL_SLOT_ADDR = 0x00432FC8
GLOBAL_BYTE_OFFSET = 0xB81

TEXT_HANDLE_OFFSET = 0x1C30
SPRITE_COUNT = 24
NODE_STRIDE = 0x20
NODE_FIRST_ID = 0x7D5
LABEL_TABLE_SIZE = 24

# Original helper addresses; stubs live at the same addresses so the pinned
# original and the relocated candidate both reach them directly.  Every helper
# is ARM code in the pinned image (the body uses `bl`, not `blx`).
STUB_NAMES = {
    0x002C3344: "camp_func_002c3344",
    0x002C32F8: "camp_func_002c32f8",
    0x002BDB2C: "camp_func_002bdb2c",
    0x002AF854: "battle_func_002af854",
    0x00296154: "script_vm_func_00296154",
    0x002BAACC: "engine_func_002baacc",
    0x002BDA1C: "AsdText_func_002bda1c",
    0x002BDA10: "script_vm_func_002bda10",
    0x002BDA00: "ui_func_002bda00",
    0x00233600: "unite_func_00233600",
}

# Architected stack words read by each helper.
STACK_ARGS = {
    0x002C3344: 0,
    0x002C32F8: 7,
    0x002BDB2C: 1,
    0x002AF854: 0,
    0x00296154: 0,
    0x002BAACC: 0,
    0x002BDA1C: 0,
    0x002BDA10: 0,
    0x002BDA00: 0,
    0x00233600: 0,
}

# Helpers whose s0 raw bits are part of the call contract.
FLOAT_ARG0 = {0x002BDB2C, 0x002BDA00}

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
VFP_CALLEE_SAVED = {f"d{i}": getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16)}
VFP_CALLEE_SAVED_START = {
    f"d{i}": (0x1111000000000000 * (i - 7)) | (0x0100000000000000 * (i - 7))
    for i in range(8, 16)
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def read_image_bytes(address: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(address - 0x00100000)
        return handle.read(size)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0038f950" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0038f950 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    if len(code) < FUNC_SIZE - 0x20:
        raise RuntimeError(f"candidate body is implausibly short: {len(code)} B")

    for rel in relocs:
        target = None
        for address, name in STUB_NAMES.items():
            if name in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unexpected relocation symbol: {rel.symbol_name}")
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        if rel.relocation_type == 28:  # R_ARM_CALL
            instruction = 0xEB000000 | (displacement & 0x00FFFFFF)
        else:  # R_ARM_JUMP24 (tail call to unite_func_00233600)
            instruction = 0xEA000000 | (displacement & 0x00FFFFFF)
        struct.pack_into("<I", code, rel.offset, instruction)
    return bytes(code)


def compile_candidate(source: Path = SOURCE, obj_name: str = "leaf_batch36_b.o") -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / obj_name
    result = compile_tu_armv6k(source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, f"mutant_{name}.o")


# --------------------------------------------------------------------- fixtures
def build_ctx(case: dict) -> bytes:
    page = bytearray(b"\x5A" * CTX_SIZE)
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(b"\x3C" * DATA_SIZE)
    struct.pack_into(
        "<I", page, GLOBAL_SLOT_ADDR - DATA_ADDR, case["global_object"] & 0xFFFFFFFF
    )
    return bytes(page)


def build_global(case: dict) -> bytes:
    # Byte 0xB81 is written by the function; the rest is filler that must stay.
    page = bytearray(b"\x77" * GLOBAL_SIZE)
    return bytes(page)


def build_text(case: dict) -> bytes:
    return bytes(b"\x11" * TEXT_SIZE)


def build_nodes(case: dict) -> bytes:
    page = bytearray(b"\x22" * NODE_SIZE)
    seed = case["node_seed"] & 0xFFFFFFFF
    for index in range(SPRITE_COUNT):
        base = index * NODE_STRIDE
        w = (0x0100 + index * 3 + (seed & 0xFF)) & 0xFFFF
        h = (0x0200 + index * 5 + ((seed >> 8) & 0xFF)) & 0xFFFF
        x0 = (0x0300 + index * 7 + ((seed >> 16) & 0xFF)) & 0xFFFF
        y0 = (0x0400 + index * 11 + ((seed >> 24) & 0xFF)) & 0xFFFF
        struct.pack_into("<H", page, base + 4, w)
        struct.pack_into("<H", page, base + 6, h)
        struct.pack_into("<H", page, base + 8, x0)
        struct.pack_into("<H", page, base + 0xA, y0)
        if case["node_mode"] == "point":
            p = NODE_ADDR + 0x3000 + index * 8
            struct.pack_into("<I", page, base + 0xC, p)
            struct.pack_into("<H", page, 0x3000 + index * 8,
                             (0x30 + index * 2 + seed) & 0xFFFF)
            struct.pack_into("<H", page, 0x3000 + index * 8 + 2,
                             (-0x30 - index * 3 - seed) & 0xFFFF)
        else:
            struct.pack_into("<I", page, base + 0xC, 0)

    # Deterministic fallback node used when a mutation asks for an out-of-range
    # label id; it is a plain rect node with no point pointer.
    struct.pack_into("<H", page, 0x3804, 0x0100)
    struct.pack_into("<H", page, 0x3806, 0x0100)
    struct.pack_into("<H", page, 0x3808, 0x0040)
    struct.pack_into("<H", page, 0x380A, 0x0050)
    struct.pack_into("<I", page, 0x380C, 0)

    # Case-specific boundary overrides for node 0 (label id 0x7D5).
    for key in ("node_w", "node_h", "node_x", "node_y", "node_dx", "node_dy"):
        if key in case:
            value = case[key] & 0xFFFF
            if key == "node_w":
                struct.pack_into("<H", page, 4, value)
            elif key == "node_h":
                struct.pack_into("<H", page, 6, value)
            elif key == "node_x":
                struct.pack_into("<H", page, 8, value)
            elif key == "node_y":
                struct.pack_into("<H", page, 0xA, value)
            elif key == "node_dx":
                struct.pack_into("<H", page, 0x3000, value)
            elif key == "node_dy":
                struct.pack_into("<H", page, 0x3002, value)
    if case["node_mode"] == "point":
        # Make node 0 always carry a valid point pointer for point mode.
        struct.pack_into("<I", page, 0xC, NODE_ADDR + 0x3000)
    return bytes(page)


def build_label_fixture(case: dict) -> bytes:
    fixture = bytearray(read_image_bytes(SHARED_TABLE_ADDR, FIXTURE_SIZE))
    if case.get("label_table") is not None:
        labels = case["label_table"]
        if len(labels) != LABEL_TABLE_SIZE:
            raise RuntimeError("label_table override must have 24 bytes")
        fixture[LABEL_TABLE_ADDR - SHARED_TABLE_ADDR:] = bytes(
            value & 0xFF for value in labels
        )
    return bytes(fixture)


def node_for(arg1: int, arg2: int) -> int:
    """Python model of camp_func_002bf6d0(29, id) used by the 0x296154 stub."""
    if arg1 == 0x1D and NODE_FIRST_ID <= arg2 < NODE_FIRST_ID + SPRITE_COUNT:
        return NODE_ADDR + (arg2 - NODE_FIRST_ID) * NODE_STRIDE
    return NODE_ADDR + 0x3800


def read_u16(uc, address: int) -> int:
    return struct.unpack("<H", uc.mem_read(address, 2))[0]


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def read_s16(uc, address: int) -> int:
    return struct.unpack("<h", uc.mem_read(address, 2))[0]


class ScreenRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
        # Enable the VFP coprocessor (CP10/CP11) before vpush/vmov.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(TEXT_ADDR, TEXT_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
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
        self.case: dict = {}
        self.bdb2c_calls = 0
        self.ctx = 0

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        count = STACK_ARGS[address]
        stack = ()
        if count:
            stack = struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))
        if address in FLOAT_ARG0:
            self.call_log.append(
                (STUB_NAMES[address], args + (self.uc.reg_read(arm.UC_ARM_REG_S0),)
                 + stack)
            )
        else:
            self.call_log.append((STUB_NAMES[address], args + stack))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    @staticmethod
    def _zero(uc, address: int, size: int) -> None:
        if address:
            uc.mem_write(address, b"\x00" * size)

    @staticmethod
    def _write_u16(uc, address: int, value: int) -> None:
        uc.mem_write(address, struct.pack("<H", value & 0xFFFF))

    @staticmethod
    def _write_u32(uc, address: int, value: int) -> None:
        uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _c3344(self, group: int) -> None:
        self._zero(self.uc, group, 0x20)

    def _c32f8(self, group: int, table: int, count: int, reg_word: int,
               s0: int, s1: int, s2: int, s3: int, s4: int,
               s5: int, s6: int) -> int:
        self._write_u16(self.uc, group + 0x00, count)
        self._write_u16(self.uc, group + 0x02, s0)
        self._write_u16(self.uc, group + 0x04, s2)
        self._write_u16(self.uc, group + 0x06, s4)
        self._write_u16(self.uc, group + 0x08, s6)
        self._write_u32(self.uc, group + 0x0C, table)
        self._write_u32(self.uc, group + 0x10, reg_word)
        self._write_u32(self.uc, group + 0x14, s1)
        self._write_u32(self.uc, group + 0x18, s3)
        self._write_u32(self.uc, group + 0x1C, s5)
        return group + 0x14

    def _bdb2c(self, sprite: int, sprite_type: int, index: int, group: int,
               panel: int, scale_bits: int) -> int:
        self._zero(self.uc, sprite, 0x8C)
        self._write_u32(self.uc, sprite + 0x00, sprite_type)
        self._write_u32(self.uc, sprite + 0x04, index)
        self._write_u32(self.uc, sprite + 0x08, 0xFFFFFFFF)
        self._write_u32(self.uc, sprite + 0x20, scale_bits)
        self._write_u16(self.uc, sprite + 0x38, panel)
        for offset in (0x24, 0x28, 0x2C):
            self._write_u32(self.uc, sprite + offset, 0x3F800000)
        self._write_u32(self.uc, sprite + 0x48, group)
        for field, offset in ((3, 0x4C), (4, 0x58), (5, 0x64),
                              (6, 0x70), (7, 0x78)):
            self._write_u32(self.uc, sprite + offset,
                            read_u32(self.uc, group + field * 4))
        for offset in (0x86, 0x87, 0x88, 0x89, 0x8A):
            self.uc.mem_write(sprite + offset, b"\x01")
        return sprite + 0x8C

    def _af854(self, sprite: int, index: int, mode: int) -> int:
        pointer = read_u32(self.uc, sprite + 0x58)
        if pointer:
            self._write_u16(self.uc, sprite + 0x5C, index)
            self._write_u16(self.uc, sprite + 0x5E, 0)
            self.uc.mem_write(sprite + 0x87, b"\x00")
            self.uc.mem_write(sprite + 0x8A, b"\x00")
            self.uc.mem_write(sprite + 0x60, bytes([mode & 0xFF]))
            entry = pointer + index * 12
            value = read_u32(self.uc, entry + (4 if mode else 0))
            self._write_u32(self.uc, sprite + 0x20, value)
        return sprite

    def _296154(self, dst: int, arg1: int, arg2: int) -> int:
        node = node_for(arg1, arg2)
        pointer = read_u32(self.uc, node + 0xC)
        if pointer:
            x0 = read_u16(self.uc, node + 8)
            y0 = read_u16(self.uc, node + 0xA)
            dx = read_s16(self.uc, pointer)
            dy = read_s16(self.uc, pointer + 2)
            # The original divides by two with truncation toward zero.
            x = x0 + (abs(dx) // 2) * (1 if dx >= 0 else -1)
            y = y0 + (abs(dy) // 2) * (1 if dy >= 0 else -1)
        else:
            w = read_u16(self.uc, node + 4) & 0x7FFF
            h = read_u16(self.uc, node + 6) & 0x7FFF
            x0 = read_u16(self.uc, node + 8)
            y0 = read_u16(self.uc, node + 0xA)
            x = x0 + (w >> 1)
            y = y0 + (h >> 1)
        self._write_u16(self.uc, dst + 0x18, x)
        self._write_u16(self.uc, dst + 0x1A, y)
        return y & 0xFFFFFFFF

    def _baacc(self, obj: int) -> int:
        # Mirrors the original body (0x002BAACC), including its two nested
        # calls, so ctx + 0x15C5 is observably 1 before the later clear.
        self._write_u32(self.uc, obj + 0x00, 0)
        self._write_u32(self.uc, obj + 0x04, 0)
        self._write_u32(self.uc, obj + 0x08, 0)
        self._write_u32(self.uc, obj + 0x0C, 0)
        self._write_u32(self.uc, obj + 0x10, 0)
        self.uc.mem_write(obj + 0x414, b"\x01")
        self.uc.mem_write(obj + 0x415, b"\x01")
        self._write_u32(self.uc, obj + 0x418, 0)
        self._write_u32(self.uc, obj + 0x41C, 0)
        base = 0x003FF3F4
        self._c3344(obj + 0x420)
        return self._c32f8(
            obj + 0x420,
            base - 0x114,
            0x78,
            base - 0x9C,
            0x48,
            base - 0x54,
            0x54,
            0,
            0,
            base,
            0x310,
        )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == 0x002C3344:
            self._log(address, r0)
            self._c3344(r0)
        elif address == 0x002C32F8:
            self._log(address, r0, r1, r2, r3)
            stack = self.call_log[-1][1][4:]
            result = self._c32f8(r0, r1, r2, r3, *stack)
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == 0x002BDB2C:
            self._log(address, r0, r1, r2, r3)
            scale = self.call_log[-1][1][4]
            panel = self.call_log[-1][1][5]
            self.bdb2c_calls += 1
            if self.case.get("label_mutation") and self.bdb2c_calls == 2:
                # Called from the first loop iteration, i.e. after the
                # original has already copied the label table to its stack.
                self.uc.mem_write(LABEL_TABLE_ADDR, b"\xFF" * LABEL_TABLE_SIZE)
            result = self._bdb2c(r0, r1, r2, r3, panel, scale)
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == 0x002AF854:
            self._log(address, r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, self._af854(r0, r1, r2))
        elif address == 0x00296154:
            self._log(address, r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, self._296154(r0, r1, r2))
        elif address == 0x002BAACC:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._baacc(r0))
        elif address == 0x002BDA1C:
            self._log(address, r0)
            object_offset = self.case["text_object"]
            pointer = 0 if object_offset is None else TEXT_ADDR + object_offset
            uc.reg_write(arm.UC_ARM_REG_R0, pointer)
        elif address == 0x002BDA10:
            self._log(address, r0, r1)
            if r0:
                self._write_u32(self.uc, r0 + 0x38, r1 & 0xFFFFFF00)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
            rewrite = self.case.get("text_slot_rewrite")
            if rewrite is not None:
                self._write_u32(self.uc, self.ctx + TEXT_HANDLE_OFFSET, rewrite)
        elif address == 0x002BDA00:
            self._log(address, r0, r1, r2)
            if r0:
                self._write_u32(self.uc, r0 + 0x9C, r1)
                self._write_u32(self.uc, r0 + 0xA0, r2)
                self._write_u32(
                    self.uc, r0 + 0xA8, uc.reg_read(arm.UC_ARM_REG_S0)
                )
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == 0x00233600:
            self._log(address, r0)
            for offset in range(0, 0x40, 4):
                self._write_u32(self.uc, r0 + offset, 0x33600000 + offset)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x5EAD1233)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def _stack_word(self, index: int) -> int:
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack("<I", self.uc.mem_read(sp + 4 * index, 4))[0]

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.bdb2c_calls = 0
        ctx = case["ctx_base"]
        self.ctx = ctx

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(GLOBAL_ADDR, build_global(case))
        self.uc.mem_write(TEXT_ADDR, build_text(case))
        self.uc.mem_write(NODE_ADDR, build_nodes(case))
        self.uc.mem_write(SHARED_TABLE_ADDR, build_label_fixture(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, ctx)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_CALLEE_SAVED_START.items():
            self.uc.reg_write(VFP_CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_fixture = (
                CTX_ADDR <= address < CTX_ADDR + CTX_SIZE
                or GLOBAL_ADDR <= address < GLOBAL_ADDR + GLOBAL_SIZE
                or TEXT_ADDR <= address < TEXT_ADDR + TEXT_SIZE
                or NODE_ADDR <= address < NODE_ADDR + NODE_SIZE
                or DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
            )
            if not (in_stack or in_fixture):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "vfp_callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in VFP_CALLEE_SAVED.items()
            },
            "call_log": [(name, tuple(args)) for name, args in self.call_log],
            "memory": {
                "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "text": bytes(self.uc.mem_read(TEXT_ADDR, TEXT_SIZE)),
                "node": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
                "label_fixture": bytes(
                    self.uc.mem_read(SHARED_TABLE_ADDR, FIXTURE_SIZE)
                ),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for region, left in orig["memory"].items():
        right = cand["memory"][region]
        if left != right:
            first = next(
                (index for index, (a, b) in enumerate(zip(left, right)) if a != b),
                None,
            )
            problems.append(
                f"memory {region} differs at offset {first:#x}: "
                f"orig={left[first]:#04x} cand={right[first]:#04x}"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "ctx_base": CTX_ADDR,
        "global_object": GLOBAL_ADDR,
        "text_object": 0x40,
        "node_mode": "rect",
        "node_seed": 0x03020100,
        "label_table": None,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- label table contents (read as signed bytes, then + 0x7D1)
    cases.append(base_case("real label table / rect nodes / text +0x40"))
    cases.append(base_case("all-zero label table", label_table=[0] * 24))
    cases.append(base_case("all-one label table", label_table=[1] * 24))
    cases.append(
        base_case(
            "signed label boundaries",
            label_table=[
                0x80, 0x7F, 0xFF, 0x00, 0x01, 0xFE, 0x81, 0x40,
                0xC0, 0x3F, 0xBF, 0x02, 0xFD, 0x7E, 0x82, 0x10,
                0xF0, 0x20, 0xE0, 0x30, 0xD0, 0x7F, 0x80, 0xFF,
            ],
        )
    )
    cases.append(
        base_case(
            "alternating label table",
            label_table=[index & 1 for index in range(24)],
        )
    )
    # The label table must be snapshotted before the loop; the stub rewrites
    # 0x003FF15C during the first loop iteration.
    cases.append(base_case("label table rewritten after snapshot",
                           label_mutation=True))
    cases.append(base_case("label table rewritten after snapshot / point nodes",
                           label_mutation=True, node_mode="point"))

    # --- node selection: point node (non-null +0xC pointer) vs rect node
    cases.append(base_case("point nodes", node_mode="point"))
    cases.append(
        base_case("point nodes alternate text", node_mode="point",
                  text_object=0x90)
    )

    # --- node coordinate boundaries for the first sprite (label 0x7D5)
    cases.append(
        base_case("rect node max dimensions", node_w=0xFFFF, node_h=0x8001,
                  node_x=0x7FFF, node_y=0x8000)
    )
    cases.append(
        base_case("point node signed boundaries", node_mode="point",
                  node_dx=-0x8000, node_dy=0x7FFF,
                  node_x=0x7FFF, node_y=0x8000)
    )
    cases.append(
        base_case("point node negative halves", node_mode="point",
                  node_dx=-1, node_dy=-3, node_x=0x0000, node_y=0xFFFF)
    )
    cases.append(
        base_case("rect node masked high bits", node_w=0x8000, node_h=0xFFFF,
                  node_x=0xFFFF, node_y=0x0001)
    )

    # --- helper result / pointer surfaces
    cases.append(base_case("null text object", text_object=None))
    cases.append(base_case("text object at +0x0", text_object=0x00))
    # The original reloads ctx + 0x1C30 after the formatting call; this stub
    # rewrites the slot so only a genuine reload reaches the second helper.
    cases.append(base_case("text handle rewritten during formatting",
                           text_slot_rewrite=TEXT_ADDR + 0x200))
    cases.append(base_case("global object at +0x100",
                           global_object=GLOBAL_ADDR + 0x100))
    cases.append(base_case("ctx base at +0x800", ctx_base=CTX_ADDR + 0x800))
    cases.append(
        base_case(
            "combined boundaries",
            ctx_base=CTX_ADDR + 0x400,
            global_object=GLOBAL_ADDR + 0x80,
            text_object=0xB0,
            node_mode="point",
            node_seed=0xA5A5A5A5,
            label_table=[0xFF] * 12 + [0x00] * 12,
        )
    )
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = ScreenRunner().run(orig_code, case)
        cand = ScreenRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


NEGATIVE_CONTROLS = (
    ("extra_sprite_label", "constexpr u32 kExtraSpriteLabel = 0x7D0;",
     "constexpr u32 kExtraSpriteLabel = 0x7D1;"),
    ("first_sprite_label_delta",
     "constexpr s32 kFirstSpriteLabelDelta = 0x7D1;",
     "constexpr s32 kFirstSpriteLabelDelta = 0x7D2;"),
    ("position_label_base", "constexpr u32 kPositionLabelBase = 0x7D5;",
     "constexpr u32 kPositionLabelBase = 0x7D6;"),
    ("panel", "constexpr u32 kPanel = 0x0B;", "constexpr u32 kPanel = 0x0A;"),
    ("group_stack_word", "constexpr u32 kGroupStackWord = 0x0C;",
     "constexpr u32 kGroupStackWord = 0x0D;"),
    ("sprite_count", "constexpr s32 kSpriteCount = 24;",
     "constexpr s32 kSpriteCount = 25;"),
    ("sprite_stride", "constexpr u32 kSpriteStride = 0x8C;",
     "constexpr u32 kSpriteStride = 0x90;"),
    ("shared_table", "constexpr u32 kSharedTableAddress = 0x003FF12C;",
     "constexpr u32 kSharedTableAddress = 0x003FF130;"),
    ("label_table", "constexpr u32 kLabelTableAddress = 0x003FF15C;",
     "constexpr u32 kLabelTableAddress = 0x003FF160;"),
    ("sprite_type", "constexpr u32 kSpriteType = 0x1D;",
     "constexpr u32 kSpriteType = 0x1E;"),
    ("text_flags", "constexpr u32 kTextFlags = 0x320202FF;",
     "constexpr u32 kTextFlags = 0x320302FF;"),
    ("text_colour", "constexpr u32 kTextColour = 0x646464FF;",
     "constexpr u32 kTextColour = 0x646464FE;"),
    ("inner_object_byte", "constexpr u32 kInnerObjectTailByte = 0x415;",
     "constexpr u32 kInnerObjectTailByte = 0x416;"),
    ("global_object_byte", "constexpr u32 kGlobalObjectByte = 0xB81;",
     "constexpr u32 kGlobalObjectByte = 0xB82;"),
    ("text_handle_offset", "constexpr u32 kTextHandleOffset = 0x1C30;",
     "constexpr u32 kTextHandleOffset = 0x1C34;"),
    ("unite_object_offset", "constexpr u32 kUniteObjectOffset = 0x17B0;",
     "constexpr u32 kUniteObjectOffset = 0x17B4;"),
    # Caches the handle instead of reloading ctx + 0x1C30 after the formatting
    # call; only the "rewritten during formatting" case can catch this.
    ("text_handle_reload",
     "    script_vm_func_002bda10(*text_slot, kTextFlags);\n"
     "    ui_func_002bda00(*text_slot, 0, kTextColour, 0.0f);",
     "    void* const cached_handle = *text_slot;\n"
     "    script_vm_func_002bda10(cached_handle, kTextFlags);\n"
     "    ui_func_002bda00(cached_handle, 0, kTextColour, 0.0f);"),
    # Reads the live table instead of the stack snapshot; only the
    # "rewritten after snapshot" cases can catch this.
    ("label_snapshot",
     "                             static_cast<s32>(entry_ids[i])),",
     "                             static_cast<s32>(reinterpret_cast<const s8*>(\n"
     "                                 kLabelTableAddress)[i])),"),
)


def main() -> None:
    print("Testing engine_func_0038f950 (0x0038f950)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in NEGATIVE_CONTROLS:
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = ScreenRunner().run(orig_code, case)
            bad = ScreenRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
