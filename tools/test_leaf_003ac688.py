#!/usr/bin/env python3
"""Differential test for the 680-byte UI chunk at 0x003AC688 (Unicorn ARM).

The ledger row `0x003ac688,680` is a compound chunk with three independently
reachable entry points:

    0x003AC688  set active UI object byte 0x1D to 5, return the object pointer
    0x003AC6A0  UI state/substate updater (state at +0x470, substate at +0x1E)
    0x003AC908  indirect virtual dispatch through the manager at 0x0043D990

Each entry is reconstructed in src/engine/leaf_batch45_a.cpp.  This harness
compiles that translation unit, extracts and relocates the three candidate
bodies, and runs them against the pinned original code.bin in separate Unicorn
machines with identical fixtures.

Compared outputs per run:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log of every direct helper and the indirect virtual target
    with all register arguments;
  * the complete 64 KiB data page (global pointers, manager/vtable chain and
    the UI object) plus any write outside the private stack and data page.

Coverage: every state 0..6+ and substate 0..4+ dispatch, the two-iteration
probe loop with early exits, signed s16 boundaries (+0x8000/+0x7FFF/+0xFFFF)
on every signed test, counter limit 7/8/9 and the negative-value path, the
+0x200..+0x272 counters, both equality directions in substate 1 and 4, both
sides of the +0x8000 sign bit in the +0x18 copy path, and all helper
zero/nonzero results.  Stub side effects deliberately rewrite object fields during a call
to prove that the reconstruction reloads every field the original reloads.

Negative controls mutate eight independent constants/branches in the C++ and
must each be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_003ac688"

FUNC1_ADDR = 0x003AC688
FUNC1_SIZE = 24          # 20 code bytes + literal at 0x003AC69C
FUNC2_ADDR = 0x003AC6A0
FUNC2_SIZE = 616         # 612 code bytes + literal at 0x003AC904
FUNC3_ADDR = 0x003AC908
FUNC3_SIZE = 40          # 36 code bytes + literal at 0x003AC92C

ENTRY_ADDRS = {
    "set5": FUNC1_ADDR,
    "state": FUNC2_ADDR,
    "virtual": FUNC3_ADDR,
}
ENTRY_SIZES = {
    "set5": FUNC1_SIZE,
    "state": FUNC2_SIZE,
    "virtual": FUNC3_SIZE,
}

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SELF_ADDR = 0x00431000
MANAGER_ADDR = 0x00432000
OBJECT_ADDR = 0x00432100
VTABLE_ADDR = 0x00432200

GLOBAL_STATE_OBJECT = 0x0043D9E4   # word read by 0x003AC688 and 0x003AC6A0
GLOBAL_MANAGER = 0x0043D990        # word read by 0x003AC908

STUB_2A63F8 = 0x002A63F8
STUB_2941B4 = 0x002941B4
STUB_2BF9F0 = 0x002BF9F0
STUB_2AF854 = 0x002AF854
STUB_294568 = 0x00294568
STUB_295B9C = 0x00295B9C
VIRTUAL_BASE = 0x00200000
VIRTUAL_SLOT_COUNT = 8
VIRTUAL_CODE_STRIDE = 0x10
VTABLE_SLOT_STRIDE = 4

STUB_NAMES = {
    STUB_2A63F8: "ui_func_002a63f8",
    STUB_2941B4: "ui_func_002941b4",
    STUB_2BF9F0: "ui_func_002bf9f0",
    STUB_2AF854: "battle_func_002af854",
    STUB_294568: "battle_func_00294568",
    STUB_295B9C: "script_vm_func_00295b9c",
}
for _slot in range(VIRTUAL_SLOT_COUNT):
    STUB_NAMES[VIRTUAL_BASE + _slot * VIRTUAL_CODE_STRIDE] = (
        f"virtual_slot{_slot}"
    )

DEFAULT_RETURN = {
    "ui_func_002a63f8": 1,
    "ui_func_002941b4": 1,
    "ui_func_002bf9f0": 1,
    "battle_func_002af854": 0x2AF85400,
    "battle_func_00294568": 0,
    "script_vm_func_00295b9c": 0,
}
for _slot in range(VIRTUAL_SLOT_COUNT):
    DEFAULT_RETURN[f"virtual_slot{_slot}"] = 0

# Number of register arguments each target actually consumes.  Scratch r1..r3
# values are not part of the contract and must not be compared.
ARG_COUNT = {
    "ui_func_002a63f8": 2,
    "ui_func_002941b4": 2,
    "ui_func_002bf9f0": 1,
    "battle_func_002af854": 3,
    "battle_func_00294568": 2,
    "script_vm_func_00295b9c": 2,
}
for _slot in range(VIRTUAL_SLOT_COUNT):
    ARG_COUNT[f"virtual_slot{_slot}"] = 1

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


# --------------------------------------------------------------------- ELF bits
def get_orig_bytes(address: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(address - 0x00100000)
        return handle.read(size)


def elf_symbol_offset(obj_file: Path, sym_name: str) -> int:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = [s for s in sections if s[1] == 2][0]
    strtab = sections[symtab[6]]
    for index in range(symtab[5] // 16):
        st_name, st_value, _size, _info, _other, _shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + index * 16
        )
        name = data[strtab[4] + st_name :].split(b"\x00")[0].decode(
            "ascii", errors="replace"
        )
        if name == sym_name or name == f"_{sym_name}":
            return st_value
    raise RuntimeError(f"symbol {sym_name!r} not found in {obj_file}")


def find_symbol(obj_file: Path, address: int):
    funcs = extract_elf_functions_detailed(obj_file)
    tag = f"{address:08x}"
    for name, value in funcs.items():
        if tag in name.lower():
            return name, value
    raise RuntimeError(f"0x{address:08x} not found in {obj_file}: {sorted(funcs)}")


def relocate(obj_file: Path, address: int, name: str, code_raw, relocs) -> bytes:
    code = bytearray(code_raw)
    func_offset = elf_symbol_offset(obj_file, name)
    for rel in relocs:
        offset = rel.offset
        if rel.relocation_type in (1, 28, 29):
            target = None
            for stub_addr in STUB_NAMES:
                if f"{stub_addr:08x}" in rel.symbol_name:
                    target = stub_addr
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = address + offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, offset)[0]
            condition = original & 0xFF000000
            struct.pack_into(
                "<I", code, offset, condition | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:
            addend = struct.unpack_from("<I", code, offset)[0]
            if rel.symbol_name in ("", ".text"):
                target = address + (addend - func_offset)
            else:
                raise RuntimeError(
                    f"unexpected absolute relocation target {rel.symbol_name!r}"
                )
            struct.pack_into("<I", code, offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_bodies() -> dict[str, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    bodies = {}
    for entry, address in ENTRY_ADDRS.items():
        name, (code_raw, relocs) = find_symbol(obj_file, address)
        bodies[entry] = relocate(obj_file, address, name, code_raw, relocs)
    return bodies


def compile_mutant(name: str, old: str, new: str) -> dict[str, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    bodies = {}
    for entry, address in ENTRY_ADDRS.items():
        symbol, (code_raw, relocs) = find_symbol(obj_file, address)
        bodies[entry] = relocate(obj_file, address, symbol, code_raw, relocs)
    return bodies


# --------------------------------------------------------------------- fixtures
def put32(page: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)


def put16(page: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<H", page, offset, value & 0xFFFF)


def build_self(case: dict) -> bytes:
    page = bytearray(0x800)
    for index in range(len(page)):
        page[index] = (index * 37 + 11) & 0xFF
    page[0x1D] = case.get("b1d", 0) & 0xFF
    page[0x1E] = case.get("b1e", 0) & 0xFF
    page[0x1F] = case.get("b1f", 0) & 0xFF
    page[0x470] = case.get("state", 0) & 0xFF
    put32(page, 0x04, case.get("w04", 0))
    put32(page, 0x08, case.get("w08", 0))
    put32(page, 0x0C, case.get("w0c", 0))
    put32(page, 0x10, case.get("w10", 0))
    put32(page, 0x14, case.get("w14", 0))
    put32(page, 0x18, case.get("w18", 0))
    put16(page, 0x270, case.get("c270", 0))
    put16(page, 0x272, case.get("c272", 0))
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    owner = case.get("owner", MANAGER_ADDR)
    obj = case.get("object", OBJECT_ADDR)
    vtable = case.get("vtable", VTABLE_ADDR)
    put32(page, GLOBAL_STATE_OBJECT - DATA_ADDR, SELF_ADDR)
    put32(page, GLOBAL_MANAGER - DATA_ADDR, owner)
    put32(page, owner - DATA_ADDR, obj)
    put32(page, obj - DATA_ADDR, vtable)
    for slot in range(VIRTUAL_SLOT_COUNT):
        put32(page, vtable - DATA_ADDR + slot * VTABLE_SLOT_STRIDE,
              VIRTUAL_BASE + slot * VIRTUAL_CODE_STRIDE)
    page[SELF_ADDR - DATA_ADDR : SELF_ADDR - DATA_ADDR + 0x800] = build_self(case)
    return bytes(page)


def run_orig(entry: str, case: dict) -> dict:
    address = ENTRY_ADDRS[entry]
    return Machine().run(get_orig_bytes(address, ENTRY_SIZES[entry]), entry, case)


class Machine:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
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

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        name = STUB_NAMES[address]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        self.call_log.append((name, (r0, r1, r2, r3)[: ARG_COUNT[name]]))

        call_index = self.call_counts.get(name, 0)
        self.call_counts[name] = call_index + 1
        effects = self.case.get("effects", {}).get(name, [])
        if call_index < len(effects):
            for offset, width, value in effects[call_index]:
                raw = (value & ((1 << (8 * width)) - 1)).to_bytes(width, "little")
                uc.mem_write(SELF_ADDR + offset, raw)

        queue = self.queues.get(name, [])
        value = queue.pop(0) if queue else DEFAULT_RETURN[name]
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)

    def run(self, code: bytes, entry: str, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.queues = {
            name: list(values)
            for name, values in case.get("returns", {}).items()
        }
        self.call_counts = {}

        address = ENTRY_ADDRS[entry]
        self.uc.mem_write(address, code)
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(address, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(
                f"Crash at PC=0x{pc:08x} entry {entry}: {error}"
            ) from error

        unexpected = []
        for write_address, width, _value in self.writes:
            in_stack = STACK_ADDR <= write_address < STACK_ADDR + STACK_SIZE
            in_data = DATA_ADDR <= write_address < DATA_ADDR + DATA_SIZE
            if not in_stack and not in_data:
                unexpected.append((write_address, width))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected,
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
    if orig["data"] != cand["data"]:
        differing = [
            index
            for index in range(DATA_SIZE)
            if orig["data"][index] != cand["data"][index]
        ]
        problems.append(
            "data page differs at "
            + ", ".join(f"0x{DATA_ADDR + i:08x}" for i in differing[:16])
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ------------------------------------------------------------------------ cases
def case(entry: str, name: str, **fields) -> dict:
    result = {"entry": entry, "name": name}
    result.update(fields)
    return result


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # 0x003AC688: unconditional object-byte write and residual r0.
    cases.append(case("set5", "set5 baseline"))
    cases.append(case("set5", "set5 overwrites existing byte", b1d=0xAA))
    cases.append(case("set5", "set5 with other object fields set",
                      b1e=0x77, b1f=0x88, state=0x99))

    # State 0 and state 1 transitions.
    cases.append(case("state", "state 0 -> 2", state=0, b1d=3, b1e=0))
    cases.append(case("state", "state 0 with unknown substate", state=0, b1e=5))
    cases.append(case("state", "state 1 b1d=4 -> 4", state=1, b1d=4, b1e=0))
    for value in (3, 5, 0, 0xFF):
        cases.append(case("state", f"state 1 b1d={value} unchanged",
                          state=1, b1d=value, b1e=0))

    # State 2: two-probe loop and signed s16 index boundary.
    cases.append(case("state", "state 2 first probe zero",
                      state=2, b1e=0,
                      returns={"ui_func_002a63f8": [0]}))
    cases.append(case("state", "state 2 second probe zero",
                      state=2, b1e=0,
                      returns={"ui_func_002a63f8": [1, 0]}))
    for raw, name in (
        (0x8000, "s16 minimum"),
        (0xFFFF, "minus one"),
        (0x7FFF, "s16 maximum"),
        (0x0000, "zero"),
        (0x0001, "one"),
    ):
        cases.append(case("state", f"state 2 index {name}", state=2, b1e=0,
                          w08=raw, returns={"ui_func_002a63f8": [1, 1]}))
    cases.append(case("state", "state 2 helper zero keeps state", state=2,
                      b1e=0, w08=1,
                      returns={"ui_func_002a63f8": [1, 1],
                               "ui_func_002941b4": [0]}))
    cases.append(case("state", "state 2 helper nonzero -> 1", state=2,
                      b1e=0, w08=0x7FFF,
                      returns={"ui_func_002a63f8": [1, 1],
                               "ui_func_002941b4": [0x17]}))
    cases.append(case("state", "state 2 probe mutates index to negative",
                      state=2, b1e=0, w08=0x0004,
                      returns={"ui_func_002a63f8": [1, 1]},
                      effects={"ui_func_002a63f8":
                               [[], [(0x08, 4, 0xFFFF0008)]]}))

    # State 3 and states >= 6.
    for value in (5, 4, 6, 0xFF):
        cases.append(case("state", f"state 3 b1d={value}", state=3, b1d=value,
                          b1e=0))
    for value in (6, 7, 0xFF):
        cases.append(case("state", f"state {value} default", state=value,
                          b1e=0))

    # State 4: counters and the +0x40 motion helper.
    for left, right, name in (
        (7, 7, "limit-1 increments"),
        (8, 9, "at and above limit unchanged"),
        (0xFFFF, 0x8000, "negative values increment"),
        (0x7FFF, 0x0000, "s16 maximum wraps to 0x8000"),
    ):
        cases.append(case("state", f"state 4 counters {name}", state=4, b1e=0,
                          c270=left, c272=right,
                          returns={"ui_func_002bf9f0": [0]}))
    for flag in (3, 4, 0xFF):
        cases.append(case("state", f"state 4 motion done b1f={flag}",
                          state=4, b1e=0, b1f=flag,
                          c270=1, c272=2, w0c=0x11111111,
                          w10=0x00000009, w14=0x22222222,
                          w18=0x00000007,
                          returns={"ui_func_002bf9f0": [1]}))
    cases.append(case("state", "state 4 motion done negative copy",
                      state=4, b1e=0, b1f=4, w0c=0x11111111,
                      w10=0x80000000, w14=0x22222222, w18=0x00000007,
                      returns={"ui_func_002bf9f0": [1]}))
    cases.append(case("state", "state 4 substate 2 runs after counters",
                      state=4, b1e=2, c270=7, c272=7,
                      returns={"ui_func_002bf9f0": [0, 1]}))
    cases.append(case("state", "state 4 helper mutates cheap counter",
                      state=4, b1e=0, c270=3, c272=3,
                      returns={"ui_func_002bf9f0": [0]},
                      effects={"ui_func_002bf9f0":
                               [[(0x272, 2, 0xFFFE)]]}))

    # State 5: the +0x158 completion helper.
    cases.append(case("state", "state 5 helper zero unchanged", state=5,
                      b1e=0, returns={"ui_func_002bf9f0": [0]}))
    cases.append(case("state", "state 5 helper nonzero -> 6", state=5,
                      b1e=0, returns={"ui_func_002bf9f0": [1]}))
    cases.append(case("state", "state 5 then substate 2", state=5, b1e=2,
                      returns={"ui_func_002bf9f0": [1, 1]}))
    cases.append(case("state", "state 5 then substate 4", state=5, b1e=4,
                      w04=0x10, w14=0x20, w08=0xFFFF,
                      returns={"ui_func_002bf9f0": [1, 0]}))

    # Substates are dispatched from state 6, where the state handler is a no-op.
    cases.append(case("state", "substate 0 no-op", state=6, b1e=0))
    for raw, name in ((0x8000, "s16 minimum"), (0xFFFF, "minus one")):
        cases.append(case("state", f"substate 1 {name}", state=6, b1e=1,
                          w18=raw))
    cases.append(case("state", "substate 1 helper zero", state=6, b1e=1,
                      w18=0,
                      returns={"ui_func_002941b4": [0]}))
    cases.append(case("state", "substate 1 equal pair -> 2", state=6, b1e=1,
                      w0c=0x12345678, w10=0x9ABCDEF0,
                      w14=0x12345678, w18=0x00000005))
    cases.append(case("state", "substate 1 unequal positive new value",
                      state=6, b1e=1, w0c=0x11111111, w10=0x00000003,
                      w14=0x22222222, w18=0x00000005))
    cases.append(case("state", "substate 1 unequal negative new value",
                      state=6, b1e=1, w0c=0x11111111, w10=0x0000FFFF,
                      w14=0x22222222, w18=0x00000005))
    cases.append(case("state", "substate 1 reload sees helper mutation",
                      state=6, b1e=1, w0c=0x11111111, w10=0x00000003,
                      w14=0x22222222, w18=0x00000005,
                      effects={"ui_func_002941b4":
                               [[(0x18, 4, 0x80000002)]]}))
    cases.append(case("state", "substate 2 helper zero", state=6, b1e=2,
                      returns={"ui_func_002bf9f0": [0]}))
    cases.append(case("state", "substate 2 helper nonzero -> 3", state=6, b1e=2,
                      returns={"ui_func_002bf9f0": [1]}))
    for flag in (3, 0xFF):
        cases.append(case("state", f"substate 3 b1f={flag} no-op", state=6,
                          b1e=3, b1f=flag))
    cases.append(case("state", "substate 3 b1f=4 full path", state=6, b1e=3,
                      b1f=4, w0c=0x11111111, w10=0x00000009,
                      w14=0x22222222, w18=0x00000007))
    cases.append(case("state", "substate 3 negative copied value", state=6,
                      b1e=3, b1f=4, w0c=0x11111111, w10=0x80000000,
                      w14=0x22222222, w18=0x00000007))
    cases.append(case("state", "substate 4 helper zero", state=6, b1e=4,
                      returns={"ui_func_002bf9f0": [0]}))
    cases.append(case("state", "substate 4 equal pair", state=6, b1e=4,
                      w04=0x10, w14=0x10, w08=0xFFFF,
                      returns={"ui_func_002bf9f0": [1]}))
    cases.append(case("state", "substate 4 unequal positive +0x08", state=6,
                      b1e=4, w04=0x10, w14=0x20, w08=0x0000,
                      returns={"ui_func_002bf9f0": [1]}))
    cases.append(case("state", "substate 4 unequal negative +0x08", state=6,
                      b1e=4, w04=0x10, w14=0x20, w08=0x8000,
                      returns={"ui_func_002bf9f0": [1]}))
    cases.append(case("state", "substate 4 reload sees helper mutation", state=6,
                      b1e=4, w04=0x10, w14=0x20, w08=0x0000,
                      returns={"ui_func_002bf9f0": [1]},
                      effects={"ui_func_002bf9f0":
                               [[(0x08, 4, 0xFFFF8000)]]}))
    for substate in (5, 0xFF):
        cases.append(case("state", f"substate {substate} default", state=6,
                          b1e=substate))

    # 0x003AC908: manager -> object -> vtable[3] indirect call.
    cases.append(case("virtual", "virtual default chain"))
    cases.append(case("virtual", "virtual alternate chain",
                      owner=0x00433000, object=0x00433040,
                      vtable=0x00433080))
    cases.append(case("virtual", "virtual callee returns nonzero",
                      returns={"virtual_slot3": [0xDEADBEEF]}))
    return cases


# ------------------------------------------------------------------------- main
def main() -> None:
    print("Testing the 0x003AC688 compound chunk (680 B)...")
    orig_code = {
        entry: get_orig_bytes(address, ENTRY_SIZES[entry])
        for entry, address in ENTRY_ADDRS.items()
    }
    bodies = compile_bodies()
    print(
        "Candidate sizes: "
        + ", ".join(f"{entry}={len(code)} B" for entry, code in bodies.items())
    )
    print(
        "Original sizes:  "
        + ", ".join(f"{entry}={len(code)} B" for entry, code in orig_code.items())
    )

    cases = make_cases()
    print(f"\nDifferential cases ({len(cases)}):")
    orig_results = []
    passed = 0
    for index, item in enumerate(cases):
        entry = item["entry"]
        orig = run_orig(entry, item)
        orig_results.append(orig)
        cand = Machine().run(bodies[entry], entry, item)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {item['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {item['name']}  ({len(orig['call_log'])} calls)")

    print("\nNegative controls:")
    controls = (
        ("object_byte", "object[0x1D] = 5;", "object[0x1D] = 4;"),
        ("state0_target", "self[0x470] = 2;", "self[0x470] = 3;"),
        ("counter_limit", "constexpr u32 kCounterLimit = 8;",
         "constexpr u32 kCounterLimit = 7;"),
        ("pair_equality", "if (from14 == from0c)",
         "if (from14 != from0c)"),
        ("state5_helper", "if (ui_func_002bf9f0(self + 0x158) != 0)",
         "if (ui_func_002bf9f0(self + 0x158) == 0)"),
        ("vtable_slot", "vtable + 0x0C", "vtable + 0x10"),
        ("substate3_flag", "if (self[0x1F] != 4)", "if (self[0x1F] != 3)"),
        ("probe_start", "u32 probe = 0;", "u32 probe = 1;"),
    )
    for name, old, new in controls:
        mutant = compile_mutant(name, old, new)
        detected = False
        for index, item in enumerate(cases):
            entry = item["entry"]
            bad = Machine().run(mutant[entry], entry, item)
            if compare(orig_results[index], bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
