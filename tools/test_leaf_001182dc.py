#!/usr/bin/env python3
"""Differential test for engine_func_001182dc (0x001182dc) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the engine_func_001182dc body,
resolves its eight direct `bl` relocations to deterministic stubs placed at the
pinned targets, and runs the original bytes (extracted/exefs/code.bin) against
the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0 (the early exit at 0x00118314 returns the whole activity word,
    not a boolean), continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with the four register arguments of every helper plus
    the dereferenced value word handed to 0x002B780C (its fourth argument is a
    stack pointer and the two frames use different stack slots);
  * every guest write outside the private stack, as an ordered list;
  * the manager page, the frame-sync page, the GPU pointer page, the object
    heap (view/work/registry/token objects, registry vector elements) and the
    stub journal page.

Coverage:
  * master enable byte 0 / non-zero;
  * signed frame-sync count > 0, == 0, negative, INT_MAX and INT_MIN;
  * activity word with bit 0 clear/set, including values whose return is not 0
    (0x00000002, 0x00000100, 0xFFFFFFFE);
  * registered/inited byte matrix, including non-canonical non-zero values;
  * slot flag byte +0x14 zero and non-zero;
  * registry vector: empty, no match, match first/middle/last, single element,
    all elements equal, interleaved duplicates (the helper must compact *all*
    trailing duplicates and the token's +0x0C word must be cleared only when the
    end word moved);
  * view payload null and non-null, GPU state pointer null and non-null, and
    manager value boundaries.
Negative controls mutate the slot index, the activity bit mask, the 0x00132240
selector, the token clear offset and the signed count comparison; every mutant
must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001182dc"

FUNC_ADDR = 0x001182DC
FUNC_SIZE = 428

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x300000
GPU_ADDR = 0x0044E000
GPU_SIZE = 0x00001000
MGR_ADDR = 0x00464000
MGR_SIZE = 0x00004000  # manager 0x00464AF0 .. slot tables 0x00464BB8
FS_ADDR = 0x004DA000
FS_SIZE = 0x00002000  # frame-sync block 0x004DAD80 .. slot 1 at 0x004DAD98
HEAP_ADDR = 0x00500000
HEAP_SIZE = 0x00010000
JOURNAL_ADDR = 0x00600000
JOURNAL_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_1324E8 = 0x001324E8
STUB_2B780C = 0x002B780C
STUB_2ABDB0 = 0x002ABDB0
STUB_131BBC = 0x00131BBC
STUB_2C028C = 0x002C028C
STUB_132240 = 0x00132240
STUB_2B77B8 = 0x002B77B8
STUB_2C3C18 = 0x002C3C18
# Statically dead in the pinned image: the guard at 0x0011844C is `mov r0,#0`
# followed by `cmp r0,#0`.  The stub only exists so a mutant that falls into it
# is reported instead of executing zeroed code.
STUB_2BF2CC = 0x002BF2CC

STUB_ADDRESSES = {
    STUB_1324E8,
    STUB_2B780C,
    STUB_2ABDB0,
    STUB_131BBC,
    STUB_2C028C,
    STUB_132240,
    STUB_2B77B8,
    STUB_2C3C18,
    STUB_2BF2CC,
}

STUB_NAMES = {
    STUB_1324E8: "func_001324e8",
    STUB_2B780C: "script_vm_func_002b780c",
    STUB_2ABDB0: "engine_func_002abdb0",
    STUB_131BBC: "func_00131bbc",
    STUB_2C028C: "engine_func_002c028c",
    STUB_132240: "engine_func_00132240",
    STUB_2B77B8: "func_002b77b8",
    STUB_2C3C18: "engine_func_002c3c18",
    STUB_2BF2CC: "engine_func_002bf2cc",
}

STUB_BY_SYMBOL = {name: address for address, name in STUB_NAMES.items()}

# Number of architected arguments each helper consumes.  Scratch registers are
# not part of any contract and legitimately differ between the two builds, so
# the journal and the call log only record these words.
ARG_COUNT = {
    STUB_1324E8: 4,
    STUB_2B780C: 4,
    STUB_2ABDB0: 2,
    STUB_131BBC: 3,
    STUB_2C028C: 2,
    STUB_132240: 4,
    STUB_2B77B8: 1,
    STUB_2C3C18: 1,
    STUB_2BF2CC: 1,
}

# Architected stack words consumed by each helper (none of them is variadic and
# the routine never pushes an outgoing argument).
STACK_ARGS = {address: 0 for address in STUB_ADDRESSES}

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

# --------------------------------------------------------------------- fixture
# Global offsets (guest addresses).
MANAGER = 0x00464AF0
MGR_FLAG_00 = 0x00
MGR_RELEASE_18 = 0x18
MGR_VALUE_2C = 0x2C
MGR_ACTIVE_88 = 0x88

WORK_TABLE = 0x00464B7C      # A[0], A[1]
REGISTRY_TABLE = 0x00464B84  # R[0], R[1]
TOKEN_TABLE = 0x00464B8C     # T[0], T[1]
VIEW_TABLE = 0x00464BB4      # V[0], V[1]

FRAME_SYNC = 0x004DAD80
FRAME_SLOT_STRIDE = 0x18
GPU_POINTER = 0x0044EA00

# Heap layout for the objects the slot tables point at.
V1_OBJ = HEAP_ADDR + 0x100
V1_PAYLOAD = HEAP_ADDR + 0x180
V1_DISPATCH = HEAP_ADDR + 0x1C0
A1_OBJ = HEAP_ADDR + 0x200
R1_OBJ = HEAP_ADDR + 0x240
T1_OBJ = HEAP_ADDR + 0x300
V0_OBJ = HEAP_ADDR + 0x400
V0_PAYLOAD = HEAP_ADDR + 0x180 + 0x1C0
V0_DISPATCH = HEAP_ADDR + 0x1C0 + 0x20
A0_OBJ = HEAP_ADDR + 0x440
R0_OBJ = HEAP_ADDR + 0x480
T0_OBJ = HEAP_ADDR + 0x500
VECTOR = HEAP_ADDR + 0x600
ELEMENT_POOL = HEAP_ADDR + 0x700
GPU_BLOCK = HEAP_ADDR + 0x800

WORD = "<I"


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "001182dc" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_001182dc not found in {obj_file}: {sorted(functions)}"
        )

    code_raw, relocations = candidate
    code = bytearray(code_raw)
    for relocation in relocations:
        if relocation.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {relocation.relocation_type} for "
                f"{relocation.symbol_name}"
            )
        target = STUB_BY_SYMBOL.get(relocation.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {relocation.symbol_name}")
        pc = FUNC_ADDR + relocation.offset + 8
        displacement = target - pc
        if displacement & 3:
            raise RuntimeError(f"unaligned call displacement to 0x{target:08x}")
        original = struct.unpack_from("<I", code, relocation.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, relocation.offset,
            condition | ((displacement >> 2) & 0x00FFFFFF),
        )
    return bytes(code)


def compile_candidate(source: Path = SOURCE, suffix: str = "") -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"leaf_batch41_c{suffix}"
    obj_file = OUT_DIR / f"{stem}.o"
    result = compile_tu_armv6k(source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_source, f"_mutant_{name}")


def put_u32(page: bytearray, base: int, offset: int, value: int) -> None:
    struct.pack_into(WORD, page, base + offset, value & 0xFFFFFFFF)


def build_manager(case: dict) -> bytes:
    page = bytearray(MGR_SIZE)
    base = MANAGER - MGR_ADDR
    page[base + MGR_FLAG_00] = case.get("manager_flag", 1) & 0xFF
    put_u32(page, base, MGR_RELEASE_18, case.get("release_word", 0xDEADBEEF))
    put_u32(page, base, MGR_VALUE_2C, case.get("slot_value", 0x11223344))
    put_u32(page, base, MGR_ACTIVE_88, case.get("active_word", 0x00000003))

    # Both entries of every table are distinct so a wrong slot index is visible.
    tables = (
        (WORK_TABLE, A0_OBJ, A1_OBJ),
        (REGISTRY_TABLE, R0_OBJ, R1_OBJ),
        (TOKEN_TABLE, T0_OBJ, T1_OBJ),
        (VIEW_TABLE, V0_OBJ, V1_OBJ),
    )
    for table, entry0, entry1 in tables:
        put_u32(page, table - MGR_ADDR, 0x00, entry0)
        put_u32(page, table - MGR_ADDR, 0x04, entry1)
    return bytes(page)


def build_gpu(case: dict) -> bytes:
    page = bytearray(GPU_SIZE)
    if case.get("gpu_null", False):
        value = 0
    else:
        value = GPU_BLOCK
    put_u32(page, GPU_POINTER - GPU_ADDR, 0x00, value)
    return bytes(page)


def build_framesync(case: dict) -> bytes:
    page = bytearray(FS_SIZE)
    base = FRAME_SYNC - FS_ADDR
    # Slot 0 is never used by this routine; give it a deliberately different
    # state so a slot-index mutant is caught.
    put_u32(page, base, 0x00, -1)
    page[base + 0x04] = 1
    page[base + 0x05] = 1
    page[base + 0x14] = 1

    slot = base + FRAME_SLOT_STRIDE
    put_u32(page, slot, 0x00, case.get("count", 1))
    page[slot + 0x04] = case.get("registered", 1) & 0xFF
    page[slot + 0x05] = case.get("inited", 0) & 0xFF
    put_u32(page, slot, 0x08, 0x88880000)
    put_u32(page, slot, 0x0C, 0x8888000C)
    put_u32(page, slot, 0x10, 0x88880010)
    page[slot + 0x14] = case.get("slot_flag", 0) & 0xFF
    return bytes(page)


def build_heap(case: dict) -> bytes:
    page = bytearray(HEAP_SIZE)

    def put(address: int, offset: int, value: int) -> None:
        put_u32(page, address - HEAP_ADDR, offset, value)

    # View object slot 1 and its payload.
    put(V1_OBJ, 0x00, 0x11110000)
    put(V1_OBJ, 0x04, 0 if case.get("payload_null", False) else V1_PAYLOAD)
    put(V1_PAYLOAD, 0xAC, V1_DISPATCH)
    for offset in (0x00, 0x40, 0xA8, 0xB0):
        put(V1_PAYLOAD, offset, 0x9A9A0000 | offset)
    put(V1_DISPATCH, 0x00, 0x0D0D0000)
    put(V1_DISPATCH, 0x04, 0x0D0D0004)

    # Work object slot 1: +0x04 and +0x08 are the two handles forwarded by
    # 0x002ABDB0.
    put(A1_OBJ, 0x00, 0xAA110000)
    put(A1_OBJ, 0x04, 0xAA110004)
    put(A1_OBJ, 0x08, 0xAA110008)
    # Registry object slot 1: pointer vector lives at +0x14.
    put(R1_OBJ, 0x00, 0xBB110000)
    put(R1_OBJ, 0x04, 0xBB110004)
    put(R1_OBJ, 0x08, 0xBB110008)
    put(R1_OBJ, 0x14, 0x00000000)          # vector context
    elements = case.get("vector", ["pad0", "token", "pad1"])
    element_addresses = {
        "token": T1_OBJ,
        "pad0": ELEMENT_POOL + 0x00,
        "pad1": ELEMENT_POOL + 0x20,
        "pad2": ELEMENT_POOL + 0x40,
        "pad3": ELEMENT_POOL + 0x60,
        "alias": T0_OBJ,
    }
    begin = VECTOR
    for index, name in enumerate(elements):
        put(VECTOR, index * 4, element_addresses[name])
    end = VECTOR + 4 * len(elements)
    put(R1_OBJ, 0x18, begin)
    put(R1_OBJ, 0x1C, end)
    put(R1_OBJ, 0x20, 0x40000000 | (len(elements) * 4))

    # Token objects: +0x0C is the word the routine clears when the end moved.
    put(T1_OBJ, 0x00, 0xCC110000)
    put(T1_OBJ, 0x04, 0xCC110004)
    put(T1_OBJ, 0x08, 0xCC110008)
    put(T1_OBJ, 0x0C, 0xABCD1234)
    put(T1_OBJ, 0x10, 0xCC110010)
    put(T0_OBJ, 0x00, 0xDD000000)
    put(T0_OBJ, 0x04, 0xDD000004)
    put(T0_OBJ, 0x08, 0xDD000008)
    put(T0_OBJ, 0x0C, 0x0BADF00D)
    put(T0_OBJ, 0x10, 0xDD000010)

    # Slot 0 objects (never used unless the slot index is wrong).  They are kept
    # fully valid so a wrong-index mutant is reported as a behavioural
    # difference instead of a harness fault.
    put(V0_OBJ, 0x00, 0x11100000)
    put(V0_OBJ, 0x04, V0_PAYLOAD)
    put(V0_PAYLOAD, 0xAC, V0_DISPATCH)
    put(V0_DISPATCH, 0x00, 0x0C0C0000)
    put(V0_DISPATCH, 0x04, 0x0C0C0004)
    put(A0_OBJ, 0x00, 0xAA000000)
    put(A0_OBJ, 0x04, 0xAA000004)
    put(A0_OBJ, 0x08, 0xAA000008)
    put(R0_OBJ, 0x00, 0xBB000000)
    put(R0_OBJ, 0x08, 0xBB000008)
    put(R0_OBJ, 0x14, 0x00000000)
    put(R0_OBJ, 0x18, VECTOR + 0x80)
    put(R0_OBJ, 0x1C, VECTOR + 0x80)

    # Reference elements used by the vector fixtures.
    for index, name in enumerate(("pad0", "pad1", "pad2", "pad3")):
        put(element_addresses[name], 0x00, 0xE0E00000 | (index << 8))
        put(element_addresses[name], 0x0C, 0xE0E00C00 | (index << 8))

    put(GPU_BLOCK, 0x00, 0x6B6B0000)
    put(GPU_BLOCK, 0x04, 0x6B6B0004)
    return bytes(page)


def read_word(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (GPU_ADDR, GPU_SIZE),
            (MGR_ADDR, MGR_SIZE),
            (FS_ADDR, FS_SIZE),
            (HEAP_ADDR, HEAP_SIZE),
            (JOURNAL_ADDR, JOURNAL_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        for address in STUB_ADDRESSES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.journal_index = 0
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _journal(self, address: int, args: tuple) -> None:
        words = list(args) + [0] * (4 - len(args))
        record = struct.pack("<IIIII", address, *words)
        self.uc.mem_write(JOURNAL_ADDR + 0x10 * self.journal_index, record)
        self.journal_index += 1

    @staticmethod
    def _norm(value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _arguments(self, uc, address: int, r0: int, r1: int, r2: int,
                   r3: int) -> tuple:
        if address == STUB_2B780C:
            # The fourth argument is `&token`; both builds use a different stack
            # slot, so record the pointed-to value instead of the address.
            value = read_word(uc, r3)
            return (self._norm(r0), self._norm(r1), self._norm(r2), value)
        return (r0, r1, r2, r3)[: ARG_COUNT[address]]

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return
        self.writes.append((address, size, value & 0xFFFFFFFF))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        args = self._arguments(uc, address, r0, r1, r2, r3)
        self._journal(address, args)
        self.call_log.append((STUB_NAMES[address], args))

        if address == STUB_1324E8:
            # Real body stores the value word into payload->dispatch[index]
            # before dispatching; reproduce only that store.
            if r0 != 0:
                payload = read_word(uc, r0 + 4)
                if payload != 0:
                    table = read_word(uc, payload + 0xAC)
                    if table != 0:
                        uc.mem_write(table + 4 * r3, struct.pack("<I", r2))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x1324E800)
        elif address == STUB_2B780C:
            # Real body: forward-copy every element that differs from *value and
            # return the final destination pointer.
            value = read_word(uc, r3)
            destination = r2
            position = r0
            while position < r1:
                element = read_word(uc, position)
                if element != value:
                    uc.mem_write(destination, struct.pack("<I", element))
                    destination += 4
                position += 4
            uc.reg_write(arm.UC_ARM_REG_R0, destination)
        elif address == STUB_2ABDB0:
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2ABDB000)
        elif address == STUB_131BBC:
            uc.reg_write(arm.UC_ARM_REG_R0, 0x131BBC00)
        elif address == STUB_2C028C:
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C028C00)
        elif address == STUB_132240:
            uc.reg_write(arm.UC_ARM_REG_R0, 0x13224000)
        elif address == STUB_2B77B8:
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2B77B800)
        elif address == STUB_2C3C18:
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2C3C1800)
        elif address == STUB_2BF2CC:
            # Statically dead path: reaching it is a failure, not a comparison.
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2BF2CC00)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.journal_index = 0
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(MGR_ADDR, build_manager(case))
        self.uc.mem_write(GPU_ADDR, build_gpu(case))
        self.uc.mem_write(FS_ADDR, build_framesync(case))
        self.uc.mem_write(HEAP_ADDR, build_heap(case))
        self.uc.mem_write(JOURNAL_ADDR, b"\x00" * JOURNAL_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # a fault is a comparable outcome, not a crash
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            return {"crash": f"PC=0x{pc:08x}: {error}"}

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": list(self.writes),
            "fixtures": {
                "manager": bytes(self.uc.mem_read(MGR_ADDR, MGR_SIZE)),
                "gpu": bytes(self.uc.mem_read(GPU_ADDR, GPU_SIZE)),
                "framesync": bytes(self.uc.mem_read(FS_ADDR, FS_SIZE)),
                "heap": bytes(self.uc.mem_read(HEAP_ADDR, HEAP_SIZE)),
                "journal": bytes(self.uc.mem_read(JOURNAL_ADDR, JOURNAL_SIZE)),
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if "crash" in orig or "crash" in cand:
        # A fault is a legal outcome (the slot pointers are dereferenced without
        # null checks); it only counts as equal when both builds fault at the
        # same address for the same reason.
        if orig.get("crash") != cand.get("crash"):
            problems.append(
                f"fault:\n    orig={orig.get('crash')!r}\n"
                f"    cand={cand.get('crash')!r}"
            )
        return problems
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"]) +
            "\n    cand=" + repr(cand["call_log"])
        )
    if orig["writes"] != cand["writes"]:
        problems.append(
            "guest writes:\n    orig=" + repr(orig["writes"]) +
            "\n    cand=" + repr(cand["writes"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "manager_flag": 1,
        "active_word": 0x00000003,
        "slot_value": 0x11223344,
        "release_word": 0xDEADBEEF,
        "count": 1,
        "registered": 1,
        "inited": 0,
        "slot_flag": 0,
        "vector": ["pad0", "token", "pad1"],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- master enable ------------------------------------------------
    cases.append(base_case("enable byte 0 returns immediately", manager_flag=0))
    cases.append(base_case("enable byte 2", manager_flag=2))
    cases.append(base_case("enable byte 0xFF", manager_flag=0xFF))

    # --- signed count and activity word -------------------------------
    for count in (1, 0, -1, 2, 0x7FFFFFFF, 0x80000000):
        cases.append(base_case(f"count {count} active bit set", count=count))
        cases.append(
            base_case(f"count {count} active bit clear", count=count,
                      active_word=0x00000100)
        )
    for active in (0x00000000, 0x00000001, 0x00000002, 0x00000100,
                   0xFFFFFFFE, 0xFFFFFFFF):
        cases.append(
            base_case(f"count 0 active word 0x{active:08x}", count=0,
                      active_word=active)
        )
    cases.append(
        base_case("count -1 active word 0xFFFFFFFE", count=-1,
                  active_word=0xFFFFFFFE)
    )

    # --- registered / inited matrix -----------------------------------
    for registered, inited in ((0, 0), (0, 1), (1, 1), (2, 0), (0xFF, 0)):
        cases.append(
            base_case(f"registered {registered} inited {inited}",
                      registered=registered, inited=inited)
        )

    # --- slot flag +0x14 ----------------------------------------------
    for flag in (1, 2, 0xFF):
        cases.append(base_case(f"slot flag 0x{flag:02x}", slot_flag=flag))

    # --- registry vector shapes ---------------------------------------
    vectors = {
        "empty": [],
        "no match": ["pad0", "pad1"],
        "single token": ["token"],
        "match first": ["token", "pad0", "pad1"],
        "match middle": ["pad0", "token", "pad1"],
        "match last": ["pad0", "pad1", "token"],
        "all token": ["token", "token", "token"],
        "interleaved": ["pad0", "token", "token", "pad1", "token"],
        "alias is not the token": ["pad0", "alias", "pad1"],
        "four pads": ["pad0", "pad1", "pad2", "pad3"],
    }
    for name, vector in vectors.items():
        cases.append(base_case(f"vector {name}", vector=vector))
        cases.append(
            base_case(f"vector {name} (not registered)", vector=vector,
                      registered=0)
        )
        cases.append(
            base_case(f"vector {name} (already initialised)", vector=vector,
                      inited=1)
        )

    # --- null pointers and value boundaries ---------------------------
    cases.append(base_case("view payload null", payload_null=True))
    cases.append(
        base_case("view payload null not registered", payload_null=True,
                  registered=0)
    )
    cases.append(base_case("gpu state pointer null", gpu_null=True))
    for value in (0x00000000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"slot value 0x{value:08x}", slot_value=value))
    cases.append(base_case("release word already zero", release_word=0))

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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
              f"{len(orig['writes'])} writes)")
    return passed


def main() -> None:
    print("Testing engine_func_001182dc (0x001182dc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          "(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("frame_sync_slot_index",
         "constexpr u32 kFrameSyncSlotIndex = 1;",
         "constexpr u32 kFrameSyncSlotIndex = 0;"),
        ("slot_table_index",
         "constexpr u32 kSlotIndex = 1;",
         "constexpr u32 kSlotIndex = 0;"),
        ("activity_bit",
         "constexpr u32 kManagerActiveBit = 0x01;",
         "constexpr u32 kManagerActiveBit = 0x02;"),
        ("sync_selector",
         "constexpr u32 kSyncSelector = 2;",
         "constexpr u32 kSyncSelector = 1;"),
        ("token_clear_offset",
         "constexpr u32 kTokenClearOffset = 0x0C;",
         "constexpr u32 kTokenClearOffset = 0x10;"),
        ("signed_count_bound",
         "if (slot->count_00 <= 0) {",
         "if (slot->count_00 < 0) {"),
    )
    for name, old, new in mutants:
        mutant_code = compile_mutant(name, old, new)
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
