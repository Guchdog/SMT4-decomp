#!/usr/bin/env python3
"""Differential test for script_vm_func_003d9e10 (0x003d9e10) using Unicorn ARM.

The routine is the teardown of the script-VM context object:

  * clears +0x3048 and runs two context resets,
  * drains 11 owned blocks of 0x8C bytes at +0x25C0 (state byte, 0x80-byte
    helper-cleared block, optional freed pointer, tail byte),
  * releases the optional virtual subobject at +0x1CF8 through vtable slot 1,
  * clears +0x2F98, runs two global cleanup helpers, clears bit 27
    (0x08000000) of the u32 at +0x634 of the object pointed to by 0x004342C8,
  * drains 50 entries of 40 bytes at +0x190: virtual +0x20 subobject, then the
    reference-counted +0x00 pointer (conditional 0x00152AF8 followed by
    0x002A7AA0, with a re-load of +0x00 between them),
  * drains 50 entries of 48 bytes at +0x1398 via 0x00241E88.

Every direct callee is replaced with a deterministic stub at its original
address.  Virtual slot 1 is read from a fixture vtable, so the observed
vtable+4 indirect path is exercised for both the +0x1CF8 object and every
+0x20 entry subobject.  Negative controls use vtable slot 2 as the wrong slot.

Each case runs the pinned original and the compiled candidate with an identical
fixture and compares:
  - return r0, continuation PC and SP,
  - callee-saved r4-r11 (and r9-r11, which the original never touches),
  - the ordered call log with every meaningful argument plus field snapshots
    that make store/call ordering observable,
  - the full object, pool, global-object and vtable fixture bytes, and the
    global pointer word at 0x004342C8.
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
FUNC_ADDR = 0x003D9E10
FUNC_SIZE = 400
TU_PATH = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_003d9e10"

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
IMAGE_ADDR = 0x00100000
IMAGE_SIZE = 0x00500000          # 0x00100000..0x00600000 (pinned image)
OBJECT_ADDR = 0x00700000
OBJECT_SIZE = 0x00004000         # needs 0x304C
POOL_ADDR = 0x00710000
POOL_SIZE = 0x00010000
VTABLE_ADDR = 0x00720000
VTABLE_SIZE = 0x00001000
GLOBAL_OBJ_ADDR = 0x00730000
GLOBAL_OBJ_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Global pointer read by the function (within the pinned image).
GLOBAL_PTR_ADDR = 0x004342C8

# Virtual-slot stub bodies (inside the mapped image, after code.bin).
DTOR_STUB = 0x00480000
DTOR_ALT_STUB = 0x00480004

# ---------------------------------------------------------------------------
# Object layout (all offsets are relative to r0)
# ---------------------------------------------------------------------------
OFF_TOP_WORD = 0x3048
OFF_LOW_WORD = 0x2F98
OFF_MID_SLOT = 0x1CF8

POOL_OFF = 0x25C0
POOL_STRIDE = 0x8C
POOL_COUNT = 11

OBJ_OFF = 0x190
OBJ_STRIDE = 40
OBJ_COUNT = 50
OFF_OBJ_PRIMARY = 0x00
OFF_OBJ_MINUS_A = 0x04
OFF_OBJ_MINUS_B = 0x08
OFF_OBJ_ZERO_A = 0x1C
OFF_OBJ_SECONDARY = 0x20
OFF_OBJ_ZERO_B = 0x24
OFF_OBJ_LINK = 0x08
OFF_OBJ_LINK_STATE = 0x0C

TAIL_OFF = 0x1398
TAIL_STRIDE = 48
TAIL_COUNT = 50
OFF_TAIL_MINUS = 0x00
OFF_TAIL_ZERO_A = 0x04
OFF_TAIL_SUB = 0x08
OFF_TAIL_ZERO_B = 0x2C

# Pool object placement.
P0_BASE = 0x1000          # 40-byte reference-counted objects
P0_CTRL_BASE = 0x8000     # their link/control words
P20_BASE = 0x2000         # 40-byte virtual subobjects
MID_OBJ = 0x3000          # the +0x1CF8 virtual subobject
P0_REPL_BASE = 0x4000     # replacements written by stubs
P0_CTRL2_BASE = 0x9000

# Direct-call stubs at their original branch targets.
STUB_227220 = 0x00227220
STUB_3DAABC = 0x003DAABC
STUB_2C4B30 = 0x002C4B30
STUB_2C4360 = 0x002C4360
STUB_22788C = 0x0022788C
STUB_24DE78 = 0x0024DE78
STUB_262C64 = 0x00262C64
STUB_27E094 = 0x0027E094
STUB_152AF8 = 0x00152AF8
STUB_2A7AA0 = 0x002A7AA0
STUB_241E88 = 0x00241E88

STUB_BY_SYMBOL = {
    "script_vm_func_00227220": STUB_227220,
    "engine_func_003daabc": STUB_3DAABC,
    "engine_func_002c4b30": STUB_2C4B30,
    "engine_func_002c4360": STUB_2C4360,
    "engine_func_0022788c": STUB_22788C,
    "engine_func_0024de78": STUB_24DE78,
    "ui_func_00262c64": STUB_262C64,
    "script_vm_func_0027e094": STUB_27E094,
    "script_vm_func_00152af8": STUB_152AF8,
    "script_vm_func_002a7aa0": STUB_2A7AA0,
    "camp_func_00241e88": STUB_241E88,
}

BX_LR = 0xE12FFF1E

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


# ---------------------------------------------------------------------------
# Fixture patterns
# ---------------------------------------------------------------------------
def pat_none(index):
    return False


def pat_all(index):
    return True


def pat_odd(index):
    return (index & 1) == 1


def pat_even(index):
    return (index & 1) == 0


def _pat_first_last(count):
    return lambda index: index == 0 or index == count - 1


def _pat_last(count):
    return lambda index: index == count - 1


PATTERNS = {
    "none": pat_none,
    "all": pat_all,
    "odd": pat_odd,
    "even": pat_even,
    "first_last": _pat_first_last(POOL_COUNT),
    "last": _pat_last(POOL_COUNT),
}
OBJ_PATTERNS = {
    "none": pat_none,
    "all": pat_all,
    "odd": pat_odd,
    "even": pat_even,
    "first_last": _pat_first_last(OBJ_COUNT),
    "last": _pat_last(OBJ_COUNT),
}


def sign_values(case):
    value = case.get("sign_value", 0)
    if isinstance(value, (list, tuple)):
        return value
    return [value] * OBJ_COUNT


def u32(value):
    return value & 0xFFFFFFFF


def s32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def sign_extend_24(value):
    return value - 0x1000000 if value & 0x800000 else value


def write_u32(page, offset, value):
    struct.pack_into("<I", page, offset, u32(value))


def read_u32_from(page, offset):
    return struct.unpack_from("<I", page, offset)[0]


# ---------------------------------------------------------------------------
# Build the original function and compile the candidate/mutants
# ---------------------------------------------------------------------------
def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get("script_vm_func_003d9e10")
    if entry is None:
        raise RuntimeError(
            "script_vm_func_003d9e10 not found in object: "
            + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(f"unsupported relocation: {rel}")
        target = STUB_BY_SYMBOL.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unexpected call relocation: {rel.symbol_name}")
        place = FUNC_ADDR + rel.offset
        inst = struct.unpack_from("<I", code, rel.offset)[0]
        addend = sign_extend_24(inst & 0x00FFFFFF) << 2
        disp = (target + addend - place) >> 2
        struct.pack_into(
            "<I", code, rel.offset, (inst & 0xFF000000) | (disp & 0x00FFFFFF)
        )
        patched = struct.unpack_from("<I", code, rel.offset)[0]
        landed = place + 8 + (sign_extend_24(patched & 0x00FFFFFF) << 2)
        if landed != target:
            raise RuntimeError(
                f"patched call 0x{place:08x} lands on 0x{landed:08x}, "
                f"expected 0x{target:08x}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(TU_PATH, OUT_DIR / "leaf_batch41_c.o")


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = TU_PATH.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def build_object(case: dict) -> bytes:
    fill = case.get("fill", 0xAA) & 0xFF
    page = bytearray([fill]) * OBJECT_SIZE
    write_u32(page, OFF_TOP_WORD, case.get("top_word", 0x11111111))
    write_u32(page, OFF_LOW_WORD, case.get("low_word", 0x22222222))

    pool_pattern = PATTERNS[case.get("pool_pattern", "none")]
    for i in range(POOL_COUNT):
        base = POOL_OFF + i * POOL_STRIDE
        page[base] = (0x10 + i) & 0xFF
        ptr = POOL_ADDR + P0_BASE + i * 0x40 if pool_pattern(i) else 0
        write_u32(page, base + 4, ptr)
        for j in range(0x80):
            page[base + 8 + j] = (0x30 + i) & 0xFF
        page[base + 0x88] = (0x20 + i) & 0xFF

    write_u32(page, OFF_MID_SLOT,
              POOL_ADDR + MID_OBJ if case.get("mid_present", False) else 0)

    obj_pattern = OBJ_PATTERNS[case.get("obj_pattern", "none")]
    p20_pattern = OBJ_PATTERNS[case.get("p20_pattern", "none")]
    for i in range(OBJ_COUNT):
        base = OBJ_OFF + i * OBJ_STRIDE
        write_u32(page, base + OFF_OBJ_PRIMARY,
                  POOL_ADDR + P0_BASE + i * 0x40 if obj_pattern(i) else 0)
        write_u32(page, base + OFF_OBJ_MINUS_A, 0xA0A00000 | i)
        write_u32(page, base + OFF_OBJ_MINUS_B, 0xA0B00000 | i)
        write_u32(page, base + OFF_OBJ_ZERO_A, 0xA0C00000 | i)
        write_u32(page, base + OFF_OBJ_SECONDARY,
                  POOL_ADDR + P20_BASE + i * 0x40 if p20_pattern(i) else 0)
        write_u32(page, base + OFF_OBJ_ZERO_B, 0xA0D00000 | i)

    for i in range(TAIL_COUNT):
        base = TAIL_OFF + i * TAIL_STRIDE
        write_u32(page, base + OFF_TAIL_MINUS, 0xB0A00000 | i)
        write_u32(page, base + OFF_TAIL_ZERO_A, 0xB0B00000 | i)
        for j in range(0x24):
            page[base + OFF_TAIL_SUB + j] = (0x70 + i) & 0xFF
        write_u32(page, base + OFF_TAIL_ZERO_B, 0xB0C00000 | i)
    return bytes(page)


def build_pool(case: dict) -> bytes:
    page = bytearray([0x55]) * POOL_SIZE
    signs = sign_values(case)
    obj_pattern = OBJ_PATTERNS[case.get("obj_pattern", "none")]
    for i in range(OBJ_COUNT):
        p0 = P0_BASE + i * 0x40
        ctrl = P0_CTRL_BASE + i * 0x40
        write_u32(page, p0 + 0x00, 0xF0000000 | i)
        write_u32(page, p0 + 0x08, POOL_ADDR + ctrl)
        write_u32(page, p0 + 0x0C, 0xF0C00000 | i)
        if obj_pattern(i):
            write_u32(page, ctrl + 0x0C, signs[i])

        p20 = P20_BASE + i * 0x40
        write_u32(page, p20 + 0x00, VTABLE_ADDR)
        write_u32(page, p20 + 0x04, 0x50000000 | i)

        repl = P0_REPL_BASE + i * 0x40
        ctrl2 = P0_CTRL2_BASE + i * 0x40
        write_u32(page, repl + 0x00, 0xE0000000 | i)
        write_u32(page, repl + 0x08, POOL_ADDR + ctrl2)
        write_u32(page, ctrl2 + 0x0C, 0xFFFFFFFF)  # signed -1: skip 0x00152AF8

    write_u32(page, MID_OBJ + 0x00, VTABLE_ADDR)
    write_u32(page, MID_OBJ + 0x04, 0x4D000000)
    return bytes(page)


def build_vtable() -> bytes:
    page = bytearray(b"\x00" * VTABLE_SIZE)
    write_u32(page, 0x00, 0)
    write_u32(page, 0x04, DTOR_STUB)
    write_u32(page, 0x08, DTOR_ALT_STUB)
    write_u32(page, 0x0C, 0xBAD0BAD0)
    return bytes(page)


def build_global_obj(case: dict) -> bytes:
    page = bytearray(b"\x00" * GLOBAL_OBJ_SIZE)
    write_u32(page, 0x634, case.get("global_flags", 0))
    write_u32(page, 0x630, 0xC0FFEE00)
    write_u32(page, 0x638, 0x12345678)
    return bytes(page)


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(POOL_ADDR, POOL_SIZE)
        self.uc.mem_map(VTABLE_ADDR, VTABLE_SIZE)
        self.uc.mem_map(GLOBAL_OBJ_ADDR, GLOBAL_OBJ_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.original_image = ORIG_BIN.read_bytes()
        self.uc.mem_write(IMAGE_ADDR, self.original_image)

        self.call_log = []
        self.case = None
        self.dtor_alt_calls = 0
        self._install_stubs()

    # -- stub installation ------------------------------------------------
    def _install_stubs(self):
        bx_lr = struct.pack("<I", BX_LR)
        for address, hook in (
            (STUB_227220, self._on_227220),
            (STUB_3DAABC, self._on_3daabc),
            (STUB_2C4B30, self._on_2c4b30),
            (STUB_2C4360, self._on_2c4360),
            (STUB_22788C, self._on_22788c),
            (STUB_24DE78, self._on_24de78),
            (STUB_262C64, self._on_262c64),
            (STUB_27E094, self._on_27e094),
            (STUB_152AF8, self._on_152af8),
            (STUB_2A7AA0, self._on_2a7aa0),
            (STUB_241E88, self._on_241e88),
        ):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)

        self.uc.mem_write(DTOR_STUB, bx_lr)
        self.uc.mem_write(DTOR_ALT_STUB, bx_lr)
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_dtor, begin=DTOR_STUB, end=DTOR_STUB
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_dtor_alt,
            begin=DTOR_ALT_STUB,
            end=DTOR_ALT_STUB,
        )

    # -- helpers ----------------------------------------------------------
    def _write_u32(self, address, value):
        self.uc.mem_write(address, struct.pack("<I", u32(value)))

    def _read_u32(self, address):
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _read_u8(self, address):
        return self.uc.mem_read(address, 1)[0]

    def _slot_index(self, obj):
        delta = obj - (POOL_ADDR + P0_BASE)
        if 0 <= delta < OBJ_COUNT * 0x40 and delta % 0x40 == 0:
            return delta // 0x40
        return None

    def _secondary_index(self, obj):
        delta = obj - (POOL_ADDR + P20_BASE)
        if 0 <= delta < OBJ_COUNT * 0x40 and delta % 0x40 == 0:
            return delta // 0x40
        return None

    def _return_marker(self, address):
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x90000000 | (address & 0xFFFF))

    # -- stub bodies ------------------------------------------------------
    def _on_227220(self, uc, address, size, user_data):
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(
            ("script_vm_func_00227220", obj, self._read_u32(OBJECT_ADDR + OFF_TOP_WORD))
        )

    def _on_3daabc(self, uc, address, size, user_data):
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(
            ("engine_func_003daabc", obj, self._read_u32(OBJECT_ADDR + OFF_TOP_WORD))
        )

    def _on_2c4b30(self, uc, address, size, user_data):
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        length = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(
            ("engine_func_002c4b30", dst, length, self._read_u8(dst - 8))
        )
        if length:
            uc.mem_write(dst, b"\x00" * length)

    def _on_2c4360(self, uc, address, size, user_data):
        block = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("engine_func_002c4360", block, self._read_u32(block)))
        self._write_u32(block, 0xDEAD0000 | (block & 0xFFFF))

    def _on_22788c(self, uc, address, size, user_data):
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(
            ("engine_func_0022788c", obj, self._read_u32(obj + OFF_LOW_WORD))
        )

    def _on_24de78(self, uc, address, size, user_data):
        # No argument: the original leaves r0 = 0x2F98 from the preceding store.
        self.call_log.append(("engine_func_0024de78",))
        self._return_marker(address)

    def _on_262c64(self, uc, address, size, user_data):
        self.call_log.append(("ui_func_00262c64",))
        self._return_marker(address)

    def _on_27e094(self, uc, address, size, user_data):
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        global_present = self.case.get("global_present", False)
        flags = (
            self._read_u32(GLOBAL_OBJ_ADDR + 0x634) if global_present else None
        )
        self.call_log.append(("script_vm_func_0027e094", obj, flags))

    def _on_152af8(self, uc, address, size, user_data):
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("script_vm_func_00152af8", obj))
        self._write_u32(obj, self._read_u32(obj) | 0x00200000)
        if self.case.get("release_replace", False):
            index = self._slot_index(obj)
            if index is not None:
                self._write_u32(
                    OBJECT_ADDR + OBJ_OFF + index * OBJ_STRIDE,
                    POOL_ADDR + P0_REPL_BASE + index * 0x40,
                )

    def _on_2a7aa0(self, uc, address, size, user_data):
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("script_vm_func_002a7aa0", obj))
        self._write_u32(obj, self._read_u32(obj) | 0x00400000)

    def _on_241e88(self, uc, address, size, user_data):
        ptr = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(
            (
                "camp_func_00241e88",
                ptr,
                self._read_u32(ptr - 8),
                self._read_u32(ptr - 4),
                self._read_u32(ptr + 0x24),
            )
        )

    def _on_dtor(self, uc, address, size, user_data):
        receiver = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("vtable_slot1", receiver))
        if receiver == POOL_ADDR + MID_OBJ:
            if self.case.get("mid_mutate", False):
                self._write_u32(OBJECT_ADDR + OFF_MID_SLOT, 0x99999999)
        elif self.case.get("dtor_replace", False):
            index = self._secondary_index(receiver)
            if index is not None:
                self._write_u32(
                    OBJECT_ADDR + OBJ_OFF + index * OBJ_STRIDE,
                    POOL_ADDR + P0_REPL_BASE + index * 0x40,
                )

    def _on_dtor_alt(self, uc, address, size, user_data):
        receiver = uc.reg_read(arm.UC_ARM_REG_R0)
        self.dtor_alt_calls += 1
        self.call_log.append(("vtable_alt_slot", receiver))

    # -- execution --------------------------------------------------------
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.case = case
        self.dtor_alt_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJECT_ADDR, build_object(case))
        self.uc.mem_write(POOL_ADDR, build_pool(case))
        self.uc.mem_write(VTABLE_ADDR, build_vtable())
        self.uc.mem_write(GLOBAL_OBJ_ADDR, build_global_obj(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(TRAP_ADDR, b"\x00" * 0x1000)
        self._write_u32(
            GLOBAL_PTR_ADDR,
            GLOBAL_OBJ_ADDR if case.get("global_present", False) else 0,
        )

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=10_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
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
            "memory": {
                "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
                "pool": bytes(self.uc.mem_read(POOL_ADDR, POOL_SIZE)),
                "vtable": bytes(self.uc.mem_read(VTABLE_ADDR, VTABLE_SIZE)),
                "global_object": bytes(
                    self.uc.mem_read(GLOBAL_OBJ_ADDR, GLOBAL_OBJ_SIZE)
                ),
                "global_pointer": bytes(self.uc.mem_read(GLOBAL_PTR_ADDR, 4)),
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    for key, value in orig["memory"].items():
        if value != cand["memory"][key]:
            problems.append(f"memory fixture {key} differs")
    return problems


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "fill": 0xAA,
        "top_word": 0x11111111,
        "low_word": 0x22222222,
        "pool_pattern": "odd",
        "obj_pattern": "even",
        "p20_pattern": "odd",
        "sign_value": 0,
        "mid_present": True,
        "mid_mutate": False,
        "global_present": True,
        "global_flags": 0xFFFFFFFF,
        "release_replace": False,
        "dtor_replace": False,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Zeroed object: nothing non-null, no global pointer.
    cases.append(
        base_case(
            "all zero",
            fill=0x00,
            top_word=0,
            low_word=0,
            pool_pattern="none",
            obj_pattern="none",
            p20_pattern="none",
            mid_present=False,
            global_present=False,
            global_flags=0,
        )
    )
    # Every entry present at once.
    cases.append(
        base_case(
            "all entries non-null",
            pool_pattern="all",
            obj_pattern="all",
            p20_pattern="all",
            sign_value=0,
        )
    )
    # First/last slot and entry boundaries.
    cases.append(
        base_case(
            "first and last only",
            pool_pattern="first_last",
            obj_pattern="first_last",
            p20_pattern="first_last",
        )
    )
    cases.append(
        base_case(
            "last only",
            pool_pattern="last",
            obj_pattern="last",
            p20_pattern="last",
        )
    )
    cases.append(
        base_case(
            "first only",
            pool_pattern="first_last",
            obj_pattern="first_last",
            p20_pattern="first_last",
            mid_present=False,
            global_present=False,
        )
    )

    # Signed state boundary for the conditional 0x00152AF8 call.
    for value in (0, 1, -1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE):
        cases.append(
            base_case(
                f"release state 0x{value & 0xFFFFFFFF:08x}",
                pool_pattern="all",
                obj_pattern="all",
                p20_pattern="none",
                sign_value=value,
            )
        )
    # Per-entry state mix so both helper paths run in one pass.
    cases.append(
        base_case(
            "mixed release states",
            obj_pattern="all",
            p20_pattern="none",
            sign_value=[0 if i % 3 == 0 else (0x80000000 if i % 3 == 1 else -1)
                        for i in range(OBJ_COUNT)],
        )
    )

    # Re-load of +0x00 after the conditional release helper.
    cases.append(
        base_case(
            "release helper replaces slot pointer",
            pool_pattern="all",
            obj_pattern="all",
            p20_pattern="none",
            sign_value=0,
            release_replace=True,
        )
    )
    # Re-load of +0x00 after the +0x20 virtual call.
    cases.append(
        base_case(
            "vtable slot writes a new +0x00",
            obj_pattern="none",
            p20_pattern="all",
            sign_value=0,
            dtor_replace=True,
        )
    )
    cases.append(
        base_case(
            "vtable slot replaces an existing +0x00",
            obj_pattern="all",
            p20_pattern="all",
            sign_value=0x80000000,
            dtor_replace=True,
        )
    )
    # The +0x1CF8 virtual object writes its own slot; the original still clears.
    cases.append(
        base_case("mid dtor mutates its slot", mid_present=True, mid_mutate=True)
    )

    # Global pointer / flag variants.
    for flags in (0, 0x08000000, 0x08000001, 0xF7FFFFFF, 0xFFFFFFFF, 0x00000001):
        cases.append(
            base_case(
                f"global flags 0x{flags:08x}",
                pool_pattern="odd",
                obj_pattern="even",
                p20_pattern="odd",
                global_present=True,
                global_flags=flags,
            )
        )
    cases.append(base_case("global pointer null", global_present=False))
    cases.append(base_case("global pointer null, all zero", fill=0x00,
                           pool_pattern="none", obj_pattern="none",
                           p20_pattern="none", mid_present=False,
                           global_present=False))

    # Fill byte variations to catch stray reads/writes.
    cases.append(base_case("fill 0x00", fill=0x00))
    cases.append(base_case("fill 0xFF", fill=0xFF))
    cases.append(base_case("fill 0x5A with empty patterns", fill=0x5A,
                           pool_pattern="none", obj_pattern="none",
                           p20_pattern="none", mid_present=False,
                           global_present=False))
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Machine().run(orig_code, case)
        cand = Machine().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, {len(orig['memory'])} pages)"
        )
    return passed


def main() -> None:
    print("Testing script_vm_func_003d9e10 (0x003d9e10)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("pool_stride",
         "constexpr u32 kPoolStride = 0x8C;",
         "constexpr u32 kPoolStride = 0x88;"),
        ("pool_count",
         "constexpr s32 kPoolCount = 11;",
         "constexpr s32 kPoolCount = 10;"),
        ("pool_block_size",
         "constexpr u32 kPoolBlockSize = 0x80;",
         "constexpr u32 kPoolBlockSize = 0x7C;"),
        ("object_stride",
         "constexpr u32 kObjectStride = 40;",
         "constexpr u32 kObjectStride = 36;"),
        ("object_count",
         "constexpr s32 kObjectCount = 50;",
         "constexpr s32 kObjectCount = 49;"),
        ("tail_stride",
         "constexpr u32 kTailStride = 48;",
         "constexpr u32 kTailStride = 44;"),
        ("tail_count",
         "constexpr s32 kTailCount = 50;",
         "constexpr s32 kTailCount = 49;"),
        ("vtable_slot",
         "    vtable[1](object);",
         "    vtable[2](object);"),
        ("signed_state_test",
         "    return state >= 0;",
         "    return state != 0;"),
        ("global_clear_bit",
         "constexpr u32 kGlobalClearBit = 0x08000000;",
         "constexpr u32 kGlobalClearBit = 0x04000000;"),
        ("no_primary_reload",
         "            void* const reloaded = *reinterpret_cast<void**>(\n"
         "                entry + func_3d9e10::kObjectPrimaryOffset);\n"
         "            script_vm_func_002a7aa0(reloaded);",
         "            script_vm_func_002a7aa0(primary);"),
        ("mid_slot_not_cleared",
         "        *reinterpret_cast<void**>(mid_slot) = nullptr;",
         "        (void)mid_slot;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Machine().run(orig_code, case)
            try:
                bad = Machine().run(mutant_code, case)
            except Exception:
                # A mutant that faults is already observably different.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
