#!/usr/bin/env python3
"""Differential test for engine_func_00120ac8 / AsdSound_InitEngine.

Compiles src/engine/leaf_batch34_c.cpp, extracts the 0x00120AC8 body,
resolves its nineteen direct calls to deterministic stubs, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn ARM machines.

Compared outputs:
  * continuation PC (must be the trap address), final SP, callee-saved r4-r11;
  * the ordered call log with every register and stack argument, including the
    five stack words of 0x00130E6C and the window pair read by 0x00130438;
  * final bytes of every non-code, non-stack region (globals, config, buffer
    and helper objects) and the set of non-stack addresses written.
  * r0 is intentionally not compared: the function is void and the original's
    r0 on the normal path is the last field_1c byte load, while the early-return
    path leaves the config pointer there.

Coverage: the one-shot gate, the first-pass binding flag, field_1c zero and
non-zero, all combinations of field_04/field_1e, field_1d zero/non-zero and
signed field_20 boundaries (0, 1, INT32_MAX, INT32_MIN, -1), sign-extended
field_1d, null and non-null getter returns, null and wrapping buffer bases, and
zero/large entry counts. Four source mutants are negative controls.

There are no loops and no indirect calls or branches in this function.
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
OUT_DIR = ROOT / "build/test_leaf_00120ac8"

FUNC_ADDR = 0x00120AC8
FUNC_SIZE = 540  # ledger size: 528 code bytes + three literal-pool words

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x00300000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
GLOBAL_ADDR = 0x00440000
GLOBAL_SIZE = 0x000C0000  # 0x0044E908/0x0044E910 and 0x004EA168
CONFIG_ADDR = 0x00710000
CONFIG_SIZE = 0x00001000
BUFFER_ADDR = 0x00720000
BUFFER_SIZE = 0x00010000
OBJECT_ADDR = 0x00730000
OBJECT_SIZE = 0x00010000
SCRATCH_ADDR = 0x00740000
SCRATCH_SIZE = 0x00010000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STATE_ADDR = 0x0044E908
WINDOW_ADDR = 0x0044E910
INIT_STATE_ADDR = 0x004EA168
CLEAR_TABLE_ADDR = 0x004EA180

# Original direct-call targets; stubs are placed at the same addresses so the
# original bytes and the relocated candidate reach identical helpers.
STUB_NAMES = {
    0x00130FF8: "engine_func_00130ff8",
    0x002BB218: "engine_func_002bb218",
    0x00130D18: "engine_func_00130d18",
    0x002BB1BC: "engine_func_002bb1bc",
    0x002BD630: "engine_func_002bd630",
    0x00130E10: "engine_func_00130e10",
    0x002BB360: "engine_func_002bb360",
    0x001441DC: "ui_func_001441dc",
    0x002BB270: "engine_func_002bb270",
    0x001311A0: "engine_func_001311a0",
    0x002BB2F0: "engine_func_002bb2f0",
    0x00130FE8: "engine_func_00130fe8",
    0x00131128: "engine_func_00131128",
    0x00130FA8: "engine_func_00130fa8",
    0x001311AC: "engine_func_001311ac",
    0x001303BC: "engine_func_001303bc",
    0x00130438: "engine_func_00130438",
    0x00130E6C: "engine_func_00130e6c",
    0x00130E18: "engine_func_00130e18",
}

GETTERS = {
    0x002BB218: "obj_a",
    0x002BB1BC: "obj_b",
    0x002BD630: "obj_c",
    0x002BB360: "obj_d",
    0x002BB270: "obj_e",
    0x002BB2F0: "obj_f",
    0x001303BC: "obj_g",
}

GETTER_OFFSETS = {
    0x002BB218: 0x000,
    0x002BB1BC: 0x040,
    0x002BD630: 0x080,
    0x002BB360: 0x0C0,
    0x002BB270: 0x100,
    0x002BB2F0: 0x140,
    0x001303BC: 0x180,
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def find_candidate() -> tuple[int, bytes, list]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    functions = extract_elf_functions_detailed(obj_file)
    for name, value in functions.items():
        if "engine_func_00120ac8" in name:
            body, relocs = value
            if len(body) > FUNC_SIZE:
                raise RuntimeError(
                    f"candidate body {len(body)} exceeds ledger size {FUNC_SIZE}"
                )
            return len(body), bytes(body), relocs
    raise RuntimeError(
        f"engine_func_00120ac8 not found in {obj_file}: {sorted(functions)}"
    )


def relocate_candidate(body: bytes, relocs) -> bytes:
    code = bytearray(body)
    known = {}
    for address, name in STUB_NAMES.items():
        known[f"{address:08x}"] = address
    for rel in relocs:
        target = None
        for token, address in known.items():
            if token in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved relocation: {rel.symbol_name}")
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            condition = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def build_config(values: dict) -> bytes:
    page = bytearray(CONFIG_SIZE)
    for index in range(8):
        struct.pack_into("<I", page, index * 4, values.get(f"field_{index * 4:02x}", 0))
    page[0x1C] = values.get("field_1c", 0) & 0xFF
    page[0x1D] = values.get("field_1d", 0) & 0xFF
    page[0x1E] = values.get("field_1e", 0) & 0xFF
    page[0x1F] = values.get("field_1f", 0xA5) & 0xFF
    struct.pack_into("<I", page, 0x20, values.get("field_20", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_global_page(case: dict) -> bytes:
    page = bytearray(GLOBAL_SIZE)
    # Deterministic filler; only the named words are meaningful.
    for offset in range(0, GLOBAL_SIZE, 4):
        struct.pack_into("<I", page, offset, (offset * 0x01010101) & 0xFFFFFFFF)
    state = case.get("state", {})
    struct.pack_into(
        "<I", page, STATE_ADDR - GLOBAL_ADDR,
        (state.get("last_mode", 0x5A) & 0xFF)
        | ((state.get("initialised", 0) & 0xFF) << 8)
        | ((state.get("bound", 0) & 0xFF) << 16)
        | ((state.get("pad_03", 0xA5) & 0xFF) << 24),
    )
    struct.pack_into(
        "<I", page, STATE_ADDR - GLOBAL_ADDR + 4,
        state.get("entry_count", 0) & 0xFFFFFFFF,
    )
    struct.pack_into(
        "<II", page, WINDOW_ADDR - GLOBAL_ADDR,
        case.get("window_base", 0xAAAA5555) & 0xFFFFFFFF,
        case.get("window_size", 0xBBBB6666) & 0xFFFFFFFF,
    )
    page[INIT_STATE_ADDR - GLOBAL_ADDR] = case.get("init_state_byte", 0x3C)
    return bytes(page)


def build_pattern(size: int, seed: int) -> bytes:
    out = bytearray(size)
    value = seed & 0xFFFFFFFF
    for index in range(size):
        value = (value * 1103515245 + 12345) & 0xFFFFFFFF
        out[index] = (value >> 16) & 0xFF
    return bytes(out)


def case(
    name: str,
    *,
    state: dict | None = None,
    config: dict | None = None,
    buffer: int = BUFFER_ADDR,
    getters_null: bool = False,
    bump_entry_count: bool = False,
    bump_field_1c: bool = False,
    init_state_byte: int = 0x3C,
) -> dict:
    return {
        "name": name,
        "state": state or {},
        "config": config or {},
        "buffer": buffer,
        "getters_null": getters_null,
        "bump_entry_count": bump_entry_count,
        "bump_field_1c": bump_field_1c,
        "init_state_byte": init_state_byte,
    }


CASES = [
    case(
        "one-shot gate set: no calls, no writes",
        state={"initialised": 1, "bound": 0, "entry_count": 7},
        config={"field_1c": 1, "field_1d": 1, "field_20": 4},
    ),
    case(
        "one-shot gate 0xff still returns immediately",
        state={"initialised": 0xFF, "bound": 1, "entry_count": 0},
        config={"field_1c": 9, "field_04": 1, "field_1e": 1},
    ),
    case(
        "full first pass, two windows, 0x130e6c, no 0x130e18",
        state={"initialised": 0, "bound": 0, "entry_count": 3},
        config={
            "field_00": 0x11111111,
            "field_04": 1,
            "field_08": 0x20,
            "field_0c": 0x40,
            "field_10": 0x22222222,
            "field_14": 0x80,
            "field_18": 0x30,
            "field_1c": 1,
            "field_1d": 0,
            "field_1e": 1,
            "field_20": 0,
        },
    ),
    case(
        "binding already done: first block skipped",
        state={"initialised": 0, "bound": 1, "entry_count": 2},
        config={
            "field_00": 0x33333333,
            "field_04": 1,
            "field_08": 0x18,
            "field_0c": 0x100,
            "field_10": 0x44444444,
            "field_14": 0x60,
            "field_18": 0x200,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 1,
            "field_20": 0x10,
        },
    ),
    case(
        "field_1c zero: no window block, no 0x130e6c",
        state={"initialised": 0, "bound": 0, "entry_count": 1},
        config={
            "field_04": 1,
            "field_08": 0x40,
            "field_0c": 0x20,
            "field_14": 0x10,
            "field_18": 0x20,
            "field_1c": 0,
            "field_1d": 1,
            "field_1e": 1,
            "field_20": 5,
        },
    ),
    case(
        "field_04 == 1 but field_1e == 0: only first window",
        state={"initialised": 0, "bound": 1, "entry_count": 0},
        config={
            "field_04": 1,
            "field_08": 0x28,
            "field_0c": 0x10,
            "field_14": 0x08,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 0,
            "field_20": 1,
        },
    ),
    case(
        "field_04 != 1: only first window despite field_1e",
        state={"initialised": 0, "bound": 1, "entry_count": 4},
        config={
            "field_04": 2,
            "field_08": 0x30,
            "field_0c": 0x10,
            "field_14": 0x08,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 1,
            "field_20": 2,
        },
    ),
    case(
        "field_20 == 0: no 0x130e18",
        state={"initialised": 0, "bound": 1, "entry_count": 1},
        config={
            "field_04": 1,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 1,
            "field_20": 0,
        },
    ),
    case(
        "field_20 == INT32_MIN: signed <= 0, no 0x130e18",
        state={"initialised": 0, "bound": 1, "entry_count": 1},
        config={
            "field_04": 0,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 0,
            "field_20": 0x80000000,
        },
    ),
    case(
        "field_20 == -1: signed <= 0, no 0x130e18",
        state={"initialised": 0, "bound": 1, "entry_count": 1},
        config={
            "field_04": 1,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 1,
            "field_20": 0xFFFFFFFF,
        },
    ),
    case(
        "field_20 == 1: boundary positive, 0x130e18 runs",
        state={"initialised": 0, "bound": 1, "entry_count": 1},
        config={
            "field_04": 0,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 0,
            "field_20": 1,
        },
    ),
    case(
        "field_20 == INT32_MAX: boundary positive, 0x130e18 runs",
        state={"initialised": 0, "bound": 1, "entry_count": 1},
        config={
            "field_04": 1,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 0,
            "field_20": 0x7FFFFFFF,
        },
    ),
    case(
        "field_1d zero with positive field_20: no 0x130e18",
        state={"initialised": 0, "bound": 1, "entry_count": 1},
        config={
            "field_04": 1,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 0,
            "field_1e": 1,
            "field_20": 0x7FFFFFFF,
        },
    ),
    case(
        "field_1d 0xff: sign-extended stack word 0xffffffff",
        state={"initialised": 0, "bound": 0, "entry_count": 2},
        config={
            "field_00": 0x12345678,
            "field_04": 1,
            "field_08": 0x14,
            "field_0c": 0x24,
            "field_10": 0x87654321,
            "field_14": 0x34,
            "field_18": 0x44,
            "field_1c": 7,
            "field_1d": 0xFF,
            "field_1e": 1,
            "field_20": 0x20,
        },
    ),
    case(
        "null getter results: call chain still identical",
        state={"initialised": 0, "bound": 0, "entry_count": 3},
        config={
            "field_00": 0x0BADF00D,
            "field_04": 1,
            "field_08": 0x20,
            "field_0c": 0x40,
            "field_10": 0x0BADF00D,
            "field_14": 0x80,
            "field_18": 0x30,
            "field_1c": 1,
            "field_1d": 0x80,
            "field_1e": 1,
            "field_20": 0x1234,
        },
        getters_null=True,
    ),
    case(
        "null buffer base with binding already done",
        state={"initialised": 0, "bound": 1, "entry_count": 1},
        config={
            "field_04": 1,
            "field_08": 0x20,
            "field_0c": 0x40,
            "field_14": 0x80,
            "field_18": 0x30,
            "field_1c": 1,
            "field_1d": 0x7F,
            "field_1e": 1,
            "field_20": 3,
        },
        buffer=0,
    ),
    case(
        "32-bit wrapping cursor arithmetic",
        state={"initialised": 0, "bound": 0, "entry_count": 0x10},
        config={
            "field_04": 1,
            "field_08": 0x10000000,
            "field_0c": 0x80000000,
            "field_14": 0x40000000,
            "field_18": 0x40000000,
            "field_1c": 1,
            "field_1d": 0xFF,
            "field_1e": 1,
            "field_20": 0x7FFFFFFF,
        },
        buffer=0xFFFFFFF0,
    ),
    case(
        "entry count zero: region sizes are 0 and 0x144",
        state={"initialised": 0, "bound": 1, "entry_count": 0},
        config={
            "field_04": 0,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 0,
            "field_1e": 0,
            "field_20": 0,
        },
    ),
    case(
        "entry count 0x1000: large strided regions",
        state={"initialised": 0, "bound": 1, "entry_count": 0x1000},
        config={
            "field_04": 1,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 0xFE,
            "field_1d": 1,
            "field_1e": 1,
            "field_20": 0x100,
        },
    ),
    case(
        "getter bumps entry_count: every reload must be observed",
        state={"initialised": 0, "bound": 0, "entry_count": 2},
        config={
            "field_00": 0x10,
            "field_04": 1,
            "field_08": 0x20,
            "field_0c": 0x30,
            "field_10": 0x40,
            "field_14": 0x50,
            "field_18": 0x60,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 1,
            "field_20": 7,
        },
        bump_entry_count=True,
    ),
    case(
        "getter bumps field_1c: branch and final state reloads",
        state={"initialised": 0, "bound": 1, "entry_count": 1},
        config={
            "field_04": 1,
            "field_08": 0x10,
            "field_0c": 0x10,
            "field_14": 0x10,
            "field_18": 0x10,
            "field_1c": 1,
            "field_1d": 1,
            "field_1e": 1,
            "field_20": 9,
        },
        bump_field_1c=True,
    ),
]

MEMORY_REGIONS = [
    (GLOBAL_ADDR, GLOBAL_SIZE),
    (CONFIG_ADDR, CONFIG_SIZE),
    (BUFFER_ADDR, BUFFER_SIZE),
    (OBJECT_ADDR, OBJECT_SIZE),
    (SCRATCH_ADDR, SCRATCH_SIZE),
]


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(CONFIG_ADDR, CONFIG_SIZE)
        self.uc.mem_map(BUFFER_ADDR, BUFFER_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(SCRATCH_ADDR, SCRATCH_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.call_log = []
        self.write_log = []
        self.getter_returns = {}
        self.config = None
        self.buffer = BUFFER_ADDR

        self._install_stubs()
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _install_stubs(self) -> None:
        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

    # ------------------------------------------------------------------ hooks
    def _read_u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _write_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _window_pair(self) -> tuple[int, int]:
        return (self._read_u32(WINDOW_ADDR), self._read_u32(WINDOW_ADDR + 4))

    def _guarded_write_u32(self, address: int, value: int) -> None:
        if address == 0:
            return
        try:
            self._write_u32(address, value)
        except unicorn.UcError:
            # A null / unmapped helper result is itself a valid fixture; the
            # original does not dereference these pointers either.
            pass

    def _on_write(self, uc, access, address, size, value, user_data):
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return
        if CODE_ADDR <= address < CODE_ADDR + CODE_SIZE:
            return
        self.write_log.append((address, size))

    def _on_stub(self, uc, address, size, user_data):
        name = STUB_NAMES[address]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)

        if address in GETTERS:
            if self.bump_entry_count and address in (0x002BB270, 0x002BB2F0):
                count = self._read_u32(STATE_ADDR + 4)
                self._write_u32(STATE_ADDR + 4, count + 1)
            if self.bump_field_1c and address == 0x002BD630:
                current = self.uc.mem_read(CONFIG_ADDR + 0x1C, 1)[0]
                self.uc.mem_write(CONFIG_ADDR + 0x1C, bytes([(current + 1) & 0xFF]))
            value = 0 if self.getter_returns.get("null", False) else (
                OBJECT_ADDR + GETTER_OFFSETS[address]
            )
            self.call_log.append((name, "getter", value) + self._window_pair())
            uc.reg_write(arm.UC_ARM_REG_R0, value)
            return

        if address == 0x00130FF8:
            self.call_log.append((name, r0))
            if r0 != 0:
                try:
                    uc.mem_write(r0, bytes([(r0 >> 4) & 0xFF]))
                except unicorn.UcError:
                    pass
            return

        if address == 0x00130D18:
            self.call_log.append((name, r0, r1, r2))
            self._guarded_write_u32(r0 + 0x17C, r1)
            self._guarded_write_u32(r0 + 0x180, r2 >> 2)
            self._guarded_write_u32(r0 + 0x184, 1)
            return

        if address == 0x00130E10:
            self.call_log.append((name, r0) + self._window_pair())
            self._guarded_write_u32(r0 + 0x24, 1)
            return

        if address == 0x001441DC:
            self.call_log.append((name, r0) + self._window_pair())
            self._guarded_write_u32(r0 + 0x24, 2)
            return

        if address == 0x001311A0:
            result = (0x60 * r1) & 0xFFFFFFFF
            self.call_log.append((name, r0, r1, result))
            uc.reg_write(arm.UC_ARM_REG_R0, result)
            return

        if address == 0x00130FE8:
            result = (0x144 * ((r1 + 1) & 0xFFFFFFFF)) & 0xFFFFFFFF
            self.call_log.append((name, r0, r1, result))
            uc.reg_write(arm.UC_ARM_REG_R0, result)
            return

        if address == 0x00131128:
            self.call_log.append((name, r0, r1, r2))
            self._guarded_write_u32(r0 + 0x20, r1)
            self._guarded_write_u32(r0 + 0x24, r2)
            return

        if address == 0x00130FA8:
            self.call_log.append((name, r0, r1, r2))
            self._guarded_write_u32(r0 + 0x20, r1)
            self._guarded_write_u32(r0 + 0x24, r2)
            self._guarded_write_u32(r0 + 0x28, 1)
            return

        if address == 0x001311AC:
            self.call_log.append((name,))
            for offset in range(0, 32, 2):
                self.uc.mem_write(
                    CLEAR_TABLE_ADDR + offset, struct.pack("<H", 0xFFFF)
                )
            return

        if address == 0x001303BC:
            # Handled by the GETTERS branch above; kept for completeness.
            self.call_log.append((name, "getter"))
            uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR + GETTER_OFFSETS[address])
            return

        if address == 0x00130438:
            window0 = self._read_u32(r2) if r2 != 0 else 0
            window1 = self._read_u32(r2 + 4) if r2 != 0 else 0
            self.call_log.append((name, r0, r1, r2, window0, window1))
            self._guarded_write_u32(r0 + 0x30, r1)
            self._guarded_write_u32(r0 + 0x34, window0)
            self._guarded_write_u32(r0 + 0x38, window1)
            return

        if address == 0x00130E6C:
            stack_args = struct.unpack("<IIIII", uc.mem_read(sp, 20))
            self.call_log.append(
                (name, r0, r1, r2, r3) + stack_args
            )
            return

        if address == 0x00130E18:
            self.call_log.append((name, r0, r1, r2))
            self._guarded_write_u32(r0 + 0x28, r1)
            self._guarded_write_u32(r0 + 0x2C, r2)
            return

        raise AssertionError(f"unhandled stub {name} at 0x{address:08x}")

    # ------------------------------------------------------------------- runs
    def run(self, code: bytes, fixture: dict) -> dict:
        case_state = fixture["state"]
        case_config = fixture["config"]

        self.call_log = []
        self.write_log = []
        self.getter_returns = {
            "null": bool(fixture.get("getters_null", False))
        }
        self.bump_entry_count = bool(fixture.get("bump_entry_count", False))
        self.bump_field_1c = bool(fixture.get("bump_field_1c", False))
        self.config = build_config(case_config)
        self.buffer = fixture.get("buffer", BUFFER_ADDR) & 0xFFFFFFFF

        self.uc.mem_write(CODE_ADDR, b"\x00" * CODE_SIZE)
        for stub_address in STUB_NAMES:
            self.uc.mem_write(stub_address, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(GLOBAL_ADDR, build_global_page(fixture))
        self.uc.mem_write(CONFIG_ADDR, self.config)
        self.uc.mem_write(BUFFER_ADDR, build_pattern(BUFFER_SIZE, 0xC0FFEE))
        self.uc.mem_write(OBJECT_ADDR, build_pattern(OBJECT_SIZE, 0x1234567))
        self.uc.mem_write(SCRATCH_ADDR, build_pattern(SCRATCH_SIZE, 0x7654321))
        self.uc.mem_write(STACK_ADDR, b"\xA5" * STACK_SIZE)
        self.uc.mem_write(FUNC_ADDR, code)
        if len(code) < FUNC_SIZE:
            self.uc.mem_write(
                FUNC_ADDR + len(code),
                struct.pack("<I", 0xE7F000F0) * ((FUNC_SIZE - len(code)) // 4),
            )

        self.uc.ctl_flush_tb()
        for reg, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[reg], value)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CONFIG_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, self.buffer)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0xDEADBEEF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0xCAFEBABE)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"crash at PC=0x{pc:08x}: {error}") from error

        final_pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
        final_sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        saved = {
            reg: self.uc.reg_read(CALLEE_SAVED[reg])
            for reg in CALLEE_SAVED
        }
        memory = {
            (base, size): bytes(self.uc.mem_read(base, size))
            for base, size in MEMORY_REGIONS
        }
        return {
            "pc": final_pc,
            "sp": final_sp,
            "saved": saved,
            "call_log": list(self.call_log),
            "writes": sorted(set(self.write_log)),
            "memory": memory,
        }


def compare(name: str, original: dict, candidate: dict) -> list[str]:
    problems = []
    if original["pc"] != TRAP_ADDR:
        problems.append(f"original PC 0x{original['pc']:08x} != trap")
    if candidate["pc"] != TRAP_ADDR:
        problems.append(f"candidate PC 0x{candidate['pc']:08x} != trap")
    if original["sp"] != candidate["sp"]:
        problems.append(
            f"SP 0x{original['sp']:08x} != 0x{candidate['sp']:08x}"
        )
    if original["saved"] != candidate["saved"]:
        problems.append(f"callee-saved {original['saved']} != {candidate['saved']}")
    if original["call_log"] != candidate["call_log"]:
        problems.append("call log differs")
    if original["writes"] != candidate["writes"]:
        problems.append("write-address set differs")
    for key in original["memory"]:
        if original["memory"][key] != candidate["memory"][key]:
            problems.append(f"memory region 0x{key[0]:08x} differs")
    return problems


def format_call_log(call_log: list, limit: int = 6) -> str:
    if not call_log:
        return "<empty>"
    shown = call_log[:limit]
    suffix = "" if len(call_log) <= limit else f" ... (+{len(call_log) - limit})"
    return " | ".join(str(entry) for entry in shown) + suffix


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"mutant {name} compilation failed: {result.stderr}")
    functions = extract_elf_functions_detailed(obj_file)
    for symbol, value in functions.items():
        if "engine_func_00120ac8" in symbol:
            return relocate_candidate(bytes(value[0]), value[1])
    raise RuntimeError(f"mutant {name} did not define engine_func_00120ac8")


def main() -> int:
    print("Testing engine_func_00120ac8 (0x00120ac8, 540 B)...")
    original_code = get_orig_bytes()
    body_size, body, relocs = find_candidate()
    candidate_code = relocate_candidate(body, relocs)
    print(f"candidate body: {body_size} bytes, {len(relocs)} relocations")

    original_runner = Runner()
    candidate_runner = Runner()

    failures = 0
    for fixture in CASES:
        original = original_runner.run(original_code, fixture)
        candidate = candidate_runner.run(candidate_code, fixture)
        problems = compare(fixture["name"], original, candidate)
        if problems:
            failures += 1
            print(f"FAIL {fixture['name']}: {problems}")
            print(f"  original calls: {format_call_log(original['call_log'])}")
            print(f"  candidate calls: {format_call_log(candidate['call_log'])}")
        else:
            print(
                f"PASS {fixture['name']} "
                f"({len(original['call_log'])} calls, "
                f"{len(original['writes'])} write sites)"
            )

    if failures:
        print(f"{failures} direct case(s) failed")
        return 1

    # Negative controls: every mutant must be detected by at least one case.
    mutants = [
        (
            "outer_window_gate",
            "if (config->field_04 == 1 && config->field_1e != 0) {",
            "if (config->field_04 == 2 && config->field_1e != 0) {",
        ),
        (
            "second_size_field",
            "const u32 second_size = config->field_18;",
            "const u32 second_size = config->field_0c;",
        ),
        (
            "final_gate_inverted",
            "if (config->field_1d != 0 && static_cast<s32>(config->field_20) > 0) {",
            "if (config->field_1d == 0 && static_cast<s32>(config->field_20) > 0) {",
        ),
        (
            "binding_gate_inverted",
            "if (state.bound == 0) {",
            "if (state.bound != 0) {",
        ),
    ]
    for name, old, new in mutants:
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for fixture in CASES:
            original = original_runner.run(original_code, fixture)
            mutant = candidate_runner.run(mutant_code, fixture)
            if compare(fixture["name"], original, mutant):
                detected = True
                break
        if not detected:
            print(f"FAIL negative control {name}: mutant not detected")
            failures += 1
        else:
            print(f"PASS negative control {name} detected")

    if failures:
        print(f"{failures} failure(s)")
        return 1
    print(f"PASS all {len(CASES)} direct cases and {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
