#!/usr/bin/env python3
"""Differential test for ui_func_00150320 (0x00150320) using Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the ui_func_00150320 body,
resolves its direct calls to deterministic stubs at the original call-target
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log (helper name and every register argument; this
    function passes no architected stack arguments);
  * every mapped fixture/output page (scene, unit, entry, node, model, stream,
    part, matrix-set, source data, GPU command stream, GPU cursor) - stack and
    code pages are excluded because the two frames/relocations differ;
  * writes outside the stack, the command stream, the cursor and the unit page
    (the 0x00155584 stub lazily writes unit+0xFC/+0x12C).

Contract coverage: null part early exit; object vtable valid/invalid/null;
object+0x50 variant A/B; object+0x51 call gate; self-relative +0x44 sub-object
null/non-null and its +4 flag; stream selector 0/1 for both the early payload
and the later +0x200 word (including helpers that rewrite it); payload sizes
0,1,2,3,4,5,7,8,16 to exercise four-byte cursor rounding; entry index 0..3;
tail words, model +0xC8/+0xCC boundaries and 32-bit wrap; unit matrix cache
cold/hot; matrix-set slots and unit/entry vectors; negative controls for the
matrix tag, the record size and the stream selector offset.
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
OUT_DIR = ROOT / "build/test_leaf_00150320"

FUNC_ADDR = 0x00150320
FUNC_SIZE = 820

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub below 0x3F0000
ZERO_ADDR = 0x00000000
ZERO_SIZE = 0x00001000
GPU_ADDR = 0x00460000
GPU_SIZE = 0x00010000
SCENE_ADDR = 0x00600000
UNIT_ADDR = 0x00610000
ENTRY_ADDR = 0x00620000
NODE_ADDR = 0x00630000
MODEL_ADDR = 0x00640000
STREAM_ADDR = 0x00650000
PART_ADDR = 0x00660000
MATRIX_ADDR = 0x00670000
SRC_ADDR = 0x00680000
OUT_ADDR = 0x00690000
PAGE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
GPU_CURSOR = GPU_ADDR + 0x52A0  # 0x004652A0
SLOT_STRIDE = 0x400
SLOT_COUNT = 4

DATA_PAGES = (
    (ZERO_ADDR, ZERO_SIZE),
    (SCENE_ADDR, PAGE_SIZE),
    (UNIT_ADDR, PAGE_SIZE),
    (ENTRY_ADDR, PAGE_SIZE),
    (NODE_ADDR, PAGE_SIZE),
    (MODEL_ADDR, PAGE_SIZE),
    (STREAM_ADDR, PAGE_SIZE),
    (PART_ADDR, PAGE_SIZE),
    (MATRIX_ADDR, PAGE_SIZE),
    (SRC_ADDR, PAGE_SIZE),
    (OUT_ADDR, PAGE_SIZE),
    (GPU_ADDR, GPU_SIZE),
)

EXPECTED_WRITE_PAGES = (
    (STACK_ADDR, STACK_SIZE),
    (OUT_ADDR, PAGE_SIZE),
    (GPU_ADDR, GPU_SIZE),
    (UNIT_ADDR, PAGE_SIZE),
)

STUB_155584 = 0x00155584
STUB_2A1A90 = 0x002A1A90
STUB_2A1AC8 = 0x002A1AC8
STUB_2A1B98 = 0x002A1B98
STUB_2A5078 = 0x002A5078
STUB_2ACD38 = 0x002ACD38
STUB_2C255C = 0x002C255C

STUB_NAMES = {
    STUB_155584: "func_00155584",
    STUB_2A1A90: "func_002a1a90",
    STUB_2A1AC8: "func_002a1ac8",
    STUB_2A1B98: "func_002a1b98",
    STUB_2A5078: "battle_func_002a5078",
    STUB_2ACD38: "ui_func_002acd38",
    STUB_2C255C: "func_002c255c",
}

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

DEFAULT_MATRIX = (
    0x3F800000, 0x00000000, 0x00000000, 0x00000000,
    0x00000000, 0x3F800000, 0x00000000, 0x00000000,
    0x00000000, 0x00000000, 0x3F800000, 0x00000000,
)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00150320" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"ui_func_00150320 not found in {obj_file}: {sorted(funcs)}")

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
            condition = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def slot_addr(base: int, index: int) -> int:
    return base + 0x100 + index * SLOT_STRIDE


def build_pages(case: dict) -> dict[int, bytes]:
    pages: dict[int, bytearray] = {}
    for address, size in DATA_PAGES:
        fill = 0x5A if address == OUT_ADDR else 0xA5
        pages[address] = bytearray([fill]) * size

    zero = pages[ZERO_ADDR]
    struct.pack_into("<I", zero, 0x44, case.get("zero_sub_offset", 0) & 0xFFFFFFFF)
    zero[0x50] = case.get("zero_variant", 0) & 0xFF
    zero[0x51] = case.get("zero_gate", 0) & 0xFF

    scene = pages[SCENE_ADDR]
    unit = pages[UNIT_ADDR]
    entry = pages[ENTRY_ADDR]
    node = pages[NODE_ADDR]
    model = pages[MODEL_ADDR]
    stream = pages[STREAM_ADDR]
    part = pages[PART_ADDR]
    matrix_set = pages[MATRIX_ADDR]
    source = pages[SRC_ADDR]

    for offset in range(0, PAGE_SIZE, 4):
        struct.pack_into("<I", source, offset, (offset * 7 + 0x13579BDF) & 0xFFFFFFFF)

    selected_index = case.get("index", 0)
    entry_table = UNIT_ADDR + 0x2000
    stream_table = UNIT_ADDR + 0x2100
    struct.pack_into("<I", unit, 0x100 + 0x22C, entry_table)
    struct.pack_into("<I", unit, 0x100 + 0x240, stream_table)

    for index in range(SLOT_COUNT):
        entry_pointer = slot_addr(ENTRY_ADDR, index)
        node_pointer = slot_addr(NODE_ADDR, index)
        model_pointer = slot_addr(MODEL_ADDR, index)
        stream_pointer = slot_addr(STREAM_ADDR, index)
        struct.pack_into("<I", unit, 0x2000 + index * 4, entry_pointer)
        struct.pack_into("<I", unit, 0x2100 + index * 4, stream_pointer)

        selected = index == selected_index
        selector = case.get("selector", index & 1) if selected else (index & 1)
        variant = case.get("variant", index & 1) if selected else ((index >> 1) & 1)
        gate = case.get("gate", index & 1) if selected else (index & 1)
        object_mode = case.get("object_mode", "valid") if selected else "valid"

        entry_base = entry_pointer - ENTRY_ADDR
        node_base = node_pointer - NODE_ADDR
        model_base = model_pointer - MODEL_ADDR
        stream_base = stream_pointer - STREAM_ADDR

        if object_mode == "null":
            struct.pack_into("<I", entry, entry_base + 0x08, 0)
        else:
            struct.pack_into("<I", entry, entry_base + 0x08, node_pointer)
        struct.pack_into("<I", entry, entry_base + 0x4C, model_pointer)
        for i, word in enumerate(case.get("entry_vec_a", (0x3F800000, 0x40000000, 0x40400000))):
            struct.pack_into("<I", entry, entry_base + 0x74 + i * 4, (word + index) & 0xFFFFFFFF)
        for i, word in enumerate(case.get("entry_vec_b", (0x40A00000, 0x40C00000, 0x40E00000))):
            struct.pack_into("<I", entry, entry_base + 0x80 + i * 4, (word + index) & 0xFFFFFFFF)

        vtable = case.get("vtable", 0x40000001) if selected else 0x40000001
        struct.pack_into("<I", node, node_base + 0x00, vtable & 0xFFFFFFFF)
        sub_offset = case.get("sub_offset", 0xBC) if selected else 0xBC
        struct.pack_into("<I", node, node_base + 0x44, sub_offset & 0xFFFFFFFF)
        node[node_base + 0x50] = variant & 0xFF
        node[node_base + 0x51] = gate & 0xFF

        if sub_offset != 0:
            sub = node_base + 0x44 + sub_offset
            if 0 <= sub and sub + 0x14 <= PAGE_SIZE:
                node[sub + 4] = (case.get("sub_flag", 0) if selected else index & 1) & 0xFF
                for i, word in enumerate(case.get("sub_vec", (0x41200000, 0x41400000, 0x41600000))):
                    struct.pack_into("<I", node, sub + 8 + i * 4, (word + index) & 0xFFFFFFFF)

        struct.pack_into("<I", model, model_base + 0xC8, (case.get("model_c8", 0x100) + index) & 0xFFFFFFFF)
        struct.pack_into("<I", model, model_base + 0xCC, (case.get("model_cc", 0x40) + index) & 0xFFFFFFFF)

        # Stream selector and its four source/size pairs.  +0x2C is an unused
        # sibling byte set to 0xFF so the selector-offset negative control is
        # always visible.
        stream[stream_base + 0x2C] = 0xFF
        stream[stream_base + 0x30] = selector & 0xFF
        struct.pack_into("<I", stream, stream_base + 0x0C, SRC_ADDR + 0x1000 + index * 0x400)
        struct.pack_into("<I", stream, stream_base + 0x10, SRC_ADDR + 0x1400 + index * 0x400)
        struct.pack_into("<I", stream, stream_base + 0x14, 0x10 + index)
        struct.pack_into("<I", stream, stream_base + 0x18, 0x18 + index)
        struct.pack_into("<I", stream, stream_base + 0x1C, SRC_ADDR + 0x1800 + index * 0x400)
        struct.pack_into("<I", stream, stream_base + 0x20, 0x0C + index)
        struct.pack_into("<I", stream, stream_base + 0x24, SRC_ADDR + 0x1C00 + index * 0x400)
        struct.pack_into("<I", stream, stream_base + 0x28, 0x14 + index)
        struct.pack_into("<I", stream, stream_base + 0x200, (0x10000000 + index) & 0xFFFFFFFF)
        struct.pack_into("<I", stream, stream_base + 0x204, (0x20000000 + index) & 0xFFFFFFFF)

        if selected:
            first_size = case.get("first_size")
            if first_size is not None:
                struct.pack_into("<I", stream, stream_base + 0x14 + selector * 4, first_size & 0xFFFFFFFF)
            second_size = case.get("second_size")
            if second_size is not None:
                struct.pack_into("<I", stream, stream_base + 0x28, second_size & 0xFFFFFFFF)
            third_size = case.get("third_size")
            if third_size is not None:
                struct.pack_into("<I", stream, stream_base + 0x20, third_size & 0xFFFFFFFF)
            struct.pack_into("<I", stream, stream_base + 0x200 + selector * 4,
                             case.get("tail_word", 0x10000000 + index) & 0xFFFFFFFF)

    struct.pack_into("<I", scene, 0x108, SCENE_ADDR + 0x800)
    struct.pack_into("<I", scene, 0x800 + 0xA4, MATRIX_ADDR + 0x200)

    struct.pack_into("<I", part, 0x120, case.get("part_20", 0x01234567) & 0xFFFFFFFF)
    struct.pack_into("<I", part, 0x124, case.get("part_24", 0x89ABCDEF) & 0xFFFFFFFF)
    struct.pack_into("<I", part, 0x128, case.get("part_28", 0xFEDCBA98) & 0xFFFFFFFF)

    for offset in range(0x148, 0x1A8, 4):
        struct.pack_into("<I", matrix_set, 0x200 + offset, (0x30000 + offset) & 0xFFFFFFFF)
    for offset in range(0x8C, 0xBC, 4):
        struct.pack_into("<I", unit, 0x100 + offset, (0x50000 + offset) & 0xFFFFFFFF)
    for i, word in enumerate(DEFAULT_MATRIX):
        struct.pack_into("<I", unit, 0x100 + 0xFC + i * 4, word)
    unit[0x100 + 0x12C] = case.get("unit_initialized", 0) & 0xFF

    gpu = pages[GPU_ADDR]
    struct.pack_into("<I", gpu, 0x52A0, OUT_ADDR + 0x100)
    struct.pack_into("<I", gpu, 0x52A4, OUT_ADDR + 0x10000)

    return {address: bytes(page) for address, page in pages.items()}


# ----------------------------------------------------------------------- stubs
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        for address, size in DATA_PAGES:
            self.uc.mem_map(address, size)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Enable the VFP coprocessor (CP10/CP11); the pinned function executes
        # one VLDR and three VSTR for the zero vector at record+0xE4.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.foreign_writes: set = set()
        self.case: dict = {}
        self.stream_address = 0

    # ------------------------------------------------------------------ stubs
    def _read_words(self, address: int, count: int) -> tuple:
        raw = self.uc.mem_read(address, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _write_words(self, address: int, words) -> None:
        self.uc.mem_write(address, struct.pack(f"<{len(words)}I", *words))

    def _read_floats(self, address: int) -> list:
        raw = self.uc.mem_read(address, 48)
        return list(struct.unpack("<12f", raw))

    def _write_floats(self, address: int, values) -> None:
        self.uc.mem_write(address, struct.pack("<12f", *values))

    def _normalise(self, value):
        if isinstance(value, int) and STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], tuple(self._normalise(arg) for arg in args))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        for base, length in EXPECTED_WRITE_PAGES:
            if base <= address < base + length:
                return
        self.foreign_writes.add((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_155584:
            self._log(address, r0)
            if uc.mem_read(r0 + 0x12C, 1)[0] == 0:
                self._write_words(r0 + 0xFC, DEFAULT_MATRIX)
                uc.mem_write(r0 + 0x12C, b"\x01")
            uc.reg_write(arm.UC_ARM_REG_R0, r0 + 0xFC)
        elif address == STUB_2A1A90:
            self._log(address, r0, r1)
            source = self._read_words(r1, 12)
            self._write_words(r0, (source[3], source[2], source[1], source[0],
                                   source[7], source[6], source[5], source[4],
                                   source[11], source[10], source[9], source[8]))
        elif address == STUB_2A1AC8:
            self._log(address, r0, r1, r2)
            source = self._read_words(r1, 12)
            self._write_words(r0, (
                source[3], r2, source[2], source[1],
                source[7], source[6], source[5], source[4],
                source[11], source[10], source[9], source[8]))
            # A later helper rewrites the stream selector; the original reads it
            # again for the +0x200 tail word.
            if self.case.get("late_mutation") is not None:
                self.uc.mem_write(self.stream_address + 0x30,
                                  bytes([self.case["late_mutation"] & 0xFF]))
        elif address == STUB_2A1B98:
            self._log(address, r0, r1)
            source = self._read_words(r1, 3)
            self._write_words(r0, (0, source[2], source[1], source[0]))
        elif address == STUB_2A5078:
            self._log(address, r0, r1, r2)
            matrix = self._read_floats(r1)
            transform = self._read_floats(r2)
            out = [0.0] * 12
            for column in range(3):
                base = column * 4
                x, y, z, w = matrix[base:base + 4]
                out[base + 0] = transform[0] * x + transform[4] * y + transform[8] * z
                out[base + 1] = transform[1] * x + transform[5] * y + transform[9] * z
                out[base + 2] = transform[2] * x + transform[6] * y + transform[10] * z
                out[base + 3] = w + transform[3] * x + transform[7] * y + transform[11] * z
            self._write_floats(r0, out)
        elif address == STUB_2ACD38:
            self._log(address, r0, r1, r2)
            if r2:
                self.uc.mem_write(r0, bytes(self.uc.mem_read(r1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2C255C:
            self._log(address, r0)
            if self.case.get("select_mutation") is not None:
                self.uc.mem_write(self.stream_address + 0x30,
                                  bytes([self.case["select_mutation"] & 0xFF]))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.foreign_writes = set()
        self.case = case

        pages = build_pages(case)
        index = case.get("index", 0)
        self.stream_address = slot_addr(STREAM_ADDR, index)

        self.uc.mem_write(FUNC_ADDR, code)
        for address, page in pages.items():
            self.uc.mem_write(address, page)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        if case.get("part_null", False):
            scene = SCENE_ADDR + 0x100
        else:
            scene = SCENE_ADDR + 0x100
        self.uc.reg_write(arm.UC_ARM_REG_R0, scene)
        self.uc.reg_write(arm.UC_ARM_REG_R1, UNIT_ADDR + 0x100)
        self.uc.reg_write(
            arm.UC_ARM_REG_R2, 0 if case.get("part_null", False) else PART_ADDR + 0x100
        )
        self.uc.reg_write(arm.UC_ARM_REG_R3, index & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
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
                address: bytes(self.uc.mem_read(address, size))
                for address, size in DATA_PAGES
            },
            "foreign_writes": sorted(self.foreign_writes),
        }


PAGE_NAMES = {
    ZERO_ADDR: "zero",
    SCENE_ADDR: "scene",
    UNIT_ADDR: "unit",
    ENTRY_ADDR: "entry",
    NODE_ADDR: "node",
    MODEL_ADDR: "model",
    STREAM_ADDR: "stream",
    PART_ADDR: "part",
    MATRIX_ADDR: "matrix",
    SRC_ADDR: "source",
    OUT_ADDR: "output",
    GPU_ADDR: "gpu",
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
    for address, size in DATA_PAGES:
        left = orig["memory"][address]
        right = cand["memory"][address]
        if left != right:
            first = next(
                (i for i in range(size) if left[i] != right[i]), None
            )
            problems.append(
                f"memory {PAGE_NAMES[address]} differs at +0x{first:x} "
                f"(orig=0x{left[first]:02x}, cand=0x{right[first]:02x})"
            )
    if orig["foreign_writes"] != cand["foreign_writes"]:
        problems.append(
            f"foreign writes orig={orig['foreign_writes']} cand={cand['foreign_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {"name": name, "index": 0}
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    cases.append(base_case("null part", part_null=True))
    cases.append(base_case("variant A selector 0", variant=1, selector=0, gate=0))
    cases.append(base_case("variant B selector 1", variant=0, selector=1, gate=1))
    cases.append(base_case("variant A selector 1", variant=1, selector=1, gate=1))
    cases.append(base_case("variant B selector 0", variant=0, selector=0, gate=0))

    for index in range(SLOT_COUNT):
        cases.append(base_case(f"index {index}", index=index,
                               variant=index & 1, selector=index & 1))

    for size in (0, 1, 2, 3, 4, 5, 7, 8, 16, 0x21):
        cases.append(base_case(f"first size {size}", first_size=size,
                               selector=0, variant=0))
        cases.append(base_case(f"second size {size}", second_size=size,
                               third_size=size, variant=1, selector=1))

    cases.append(base_case("sub object null", sub_offset=0))
    cases.append(base_case("sub flag 0", sub_flag=0, variant=0))
    cases.append(base_case("sub flag 1", sub_flag=1, variant=0))
    cases.append(base_case("sub flag 0 selector 1", sub_flag=0, selector=1,
                           variant=1))
    cases.append(base_case("model wrap c8=0 cc=max", model_c8=0,
                           model_cc=0xFFFFFFFF, sub_flag=0))
    cases.append(base_case("model wrap c8=max cc=0", model_c8=0xFFFFFFFF,
                           model_cc=0, sub_flag=0))

    cases.append(base_case("unit cache cold", unit_initialized=0, variant=0))
    cases.append(base_case("unit cache hot", unit_initialized=1, variant=0))

    cases.append(base_case("selector rewritten by select call",
                           gate=1, selector=0, select_mutation=1, variant=0))
    cases.append(base_case("selector rewritten by matrix helper",
                           gate=1, selector=1, late_mutation=0, variant=0))
    cases.append(base_case("selector rewritten late to 2",
                           gate=0, selector=0, late_mutation=2, variant=1))

    cases.append(base_case("object pointer null", object_mode="null",
                           zero_variant=1, zero_gate=1, selector=0, variant=1))
    cases.append(base_case("vtable invalid A", object_mode="invalid",
                           vtable=0x00000000, zero_variant=1, zero_gate=1))
    cases.append(base_case("vtable invalid B", object_mode="invalid",
                           vtable=0x40000000, zero_variant=0, zero_gate=0))
    cases.append(base_case("vtable valid high bits", vtable=0xFFFFFFFF,
                           variant=1, selector=1))

    cases.append(base_case("part words boundaries", part_20=0x7FFFFFFF,
                           part_24=0x80000000, part_28=0xFFFFFFFF,
                           variant=1))
    cases.append(base_case("tail word boundaries", tail_word=0xFFFFFFFF,
                           variant=1, selector=1))
    cases.append(base_case("all sizes zero", first_size=0, second_size=0,
                           third_size=0, variant=0, selector=0))
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
    print("Testing ui_func_00150320 (0x00150320)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (relocated).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("matrix_tag", "constexpr u32 kMatrixTag = 0x03BF02C1u;",
         "constexpr u32 kMatrixTag = 0x03BF02C0u;"),
        ("record_size", "constexpr u32 kRecordBytes = 0x128u;",
         "constexpr u32 kRecordBytes = 0x124u;"),
        ("stream_selector", "constexpr u32 kStreamSelector = 0x30u;",
         "constexpr u32 kStreamSelector = 0x2Cu;"),
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
