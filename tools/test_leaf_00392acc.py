#!/usr/bin/env python3
"""Differential test for engine_func_00392acc (0x00392ACC) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts engine_func_00392acc, resolves
its direct calls (and the five-word switch table) to deterministic stubs, and
runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0 (gated except on the four documented incidental-residue exits),
    continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log, including the 20-byte message payload each helper
    receives, stack pointers normalised to "<stack>", and nested destructor
    calls;
  * the full context page, heap page, global-root page and the 0x00432FC8
    global slot page;
  * any write outside the private stack / context / heap pages.

Coverage: every state value (0-4, 0x270F, neighbours and 32-bit boundary
values); opcodes 0x00, 0x01, 0x63, 0x64, 0x66, 0x67, 0x68 and 0xFF in both the
state-1 and state-3 tails; null/non-null owned sources; null and non-null
factory results; every countdown boundary; table indices 0, 1, 2, 0x80000000
and 0xFFFFFFFF (32-bit wrap); the root pointer sampled after the entry
constructor and before the state-2 factory; and the unguarded null dereferences
(state 1/3 missing source, state 2 null factory) as fault-address controls.
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
OUT_DIR = ROOT / "build/test_leaf_00392acc"

FUNC_ADDR = 0x00392ACC
FUNC_SIZE = 632

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers 0x00392ACC and every original stub address
CTX_ADDR = 0x00710000
CTX_SIZE = 0x00010000
HEAP_ADDR = 0x00720000
HEAP_SIZE = 0x00010000
GLOBAL_ADDR = 0x00730000
GLOBAL_SIZE = 0x00010000
SLOT_ADDR = 0x00430000        # page containing 0x00432FC8
SLOT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
TRAP_SIZE = 0x00001000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

GLOBAL_SLOT_ADDR = 0x00432FC8
ALT_ROOT = GLOBAL_ADDR + 0x2000
TABLE_A = GLOBAL_ADDR + 0x1000
TABLE_B = GLOBAL_ADDR + 0x3000

SOURCE_A = HEAP_ADDR + 0x100
SOURCE_B = HEAP_ADDR + 0x200
CREATED = HEAP_ADDR + 0x800
VTABLE_ADDR = HEAP_ADDR + 0x400

# Direct-call stubs, placed at the original targets so both the pinned bytes
# and the relocated candidate resolve to them.
STUB_CTOR = 0x00234278
STUB_FACTORY = 0x00234160
STUB_LIST = 0x002337A0
STUB_TERMINATOR = 0x0027EC84
STUB_RANGE = 0x002A17C0
STUB_FORWARD = 0x002342B8
STUB_SIGNAL = 0x00234004

DIRECT_STUBS = {
    "engine_func_00234278": STUB_CTOR,
    "engine_func_00234160": STUB_FACTORY,
    "shop_func_002337a0": STUB_LIST,
    "camp_func_0027ec84": STUB_TERMINATOR,
    "engine_func_002a17c0": STUB_RANGE,
    "func_002342b8": STUB_FORWARD,
    "engine_func_00234004": STUB_SIGNAL,
}

# Vtable slots reached indirectly. Slot 1 is the deleting destructor, slot 3
# the by-value 20-byte message getter; slot 0/2 are never called here.
STUB_FULL_DTOR = 0x00310020
STUB_DELETING_DTOR = 0x00310000
STUB_READ_MESSAGE = 0x00310010

INDIRECT_STUBS = (STUB_FULL_DTOR, STUB_DELETING_DTOR, STUB_READ_MESSAGE)

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


def get_symbol_offset(obj_file: Path, symbol: str) -> int:
    data = Path(obj_file).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + index * e_shentsize)
        for index in range(e_shnum)
    ]
    symtab = next(section for section in sections if section[1] == 2)
    strtab = sections[symtab[6]]
    for index in range(symtab[5] // 16):
        fields = struct.unpack_from("<IIIBBH", data, symtab[4] + index * 16)
        name = data[strtab[4] + fields[0]:].split(b"\x00")[0]
        if name.decode("ascii", errors="replace") == symbol:
            return fields[1]
    raise RuntimeError(f"symbol {symbol} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00392acc" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"engine_func_00392acc not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    func_offset = get_symbol_offset(obj_file, "engine_func_00392acc")
    table_offsets: list[int] = []

    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = DIRECT_STUBS.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(
                    f"unresolved call relocation: {rel.symbol_name}"
                )
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 switch-table word
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if rel.symbol_name not in ("", ".text"):
                raise RuntimeError(
                    f"unexpected data relocation: {rel.symbol_name}"
                )
            target = FUNC_ADDR + (addend - func_offset)
            struct.pack_into("<I", code, rel.offset, target)
            table_offsets.append(rel.offset)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    # The five switch-table words must all point inside the relocated body.
    if len(table_offsets) != 5:
        raise RuntimeError(
            f"expected 5 switch-table words, found {len(table_offsets)}"
        )
    for index, offset in enumerate(table_offsets):
        word = struct.unpack_from("<I", code, offset)[0]
        if not FUNC_ADDR <= word < FUNC_ADDR + len(code):
            raise RuntimeError(
                f"switch table entry {index} resolved outside the body: "
                f"0x{word:08x}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)}x")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures


def pattern_page(size: int, seed: int) -> bytearray:
    return bytearray(((index * 7 + seed) & 0xFF) for index in range(size))


def build_global_page() -> bytes:
    page = pattern_page(GLOBAL_SIZE, 0x11)
    struct.pack_into("<I", page, 0x678, TABLE_A)
    struct.pack_into("<I", page, 0x2000 + 0x678, TABLE_B)
    return bytes(page)


def build_slot_page() -> bytes:
    page = pattern_page(SLOT_SIZE, 0x22)
    struct.pack_into("<I", page, GLOBAL_SLOT_ADDR - SLOT_ADDR, GLOBAL_ADDR)
    return bytes(page)


def build_ctx(case: dict) -> bytes:
    page = pattern_page(CTX_SIZE, 0x33)
    struct.pack_into("<I", page, 0x004, case["result"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x008, case["state"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x00C, case["counter"] & 0xFFFFFFFF)
    struct.pack_into(
        "<I", page, 0x208, (case["source"] or 0) & 0xFFFFFFFF
    )
    struct.pack_into("<I", page, 0x20C, CTX_ADDR + 0x20C)
    struct.pack_into("<I", page, 0x240, CTX_ADDR + 0x240)
    return bytes(page)


def build_heap() -> bytes:
    page = pattern_page(HEAP_SIZE, 0x99)
    for index, source in enumerate((SOURCE_A, SOURCE_B)):
        offset = source - HEAP_ADDR
        struct.pack_into("<I", page, offset + 0x0, VTABLE_ADDR)
        struct.pack_into("<I", page, offset + 0x4, 0x51510000 | index)
        struct.pack_into("<I", page, offset + 0x8, 0x52520000 | index)
    for index, address in enumerate(
        (STUB_FULL_DTOR, STUB_DELETING_DTOR, STUB_DELETING_DTOR,
         STUB_READ_MESSAGE)
    ):
        struct.pack_into("<I", page, VTABLE_ADDR - HEAP_ADDR + index * 4,
                         address)
    return bytes(page)


def make_message(opcode: int, tag: int) -> bytes:
    return bytes((opcode, 0xA0 | (tag & 0x0F), 0xB0 | (tag & 0x0F),
                  0xC0 | (tag & 0x0F))) + struct.pack(
        "<IIII",
        0x10000000 + tag,
        0x20000000 + tag,
        0x30000000 + tag,
        0x40000000 + tag,
    )


# ---------------------------------------------------------------------- runner


class Runner:
    """One Unicorn ARM machine with deterministic stubs at the original sites."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(HEAP_ADDR, HEAP_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, TRAP_SIZE)

        for address in DIRECT_STUBS.values():
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_direct, begin=address,
                end=address
            )
        for address in INDIRECT_STUBS:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_indirect, begin=address,
                end=address
            )

        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_UNMAPPED, self._on_unmapped)

        self.call_log: list = []
        self.writes: list = []
        self.faults: list = []
        self.case: dict = {}

    # -------------------------------------------------------------- utilities
    @staticmethod
    def _norm(address: int) -> object:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        if CTX_ADDR <= address < CTX_ADDR + CTX_SIZE:
            return address - CTX_ADDR
        if HEAP_ADDR <= address < HEAP_ADDR + HEAP_SIZE:
            return ("heap", address - HEAP_ADDR)
        return address

    def _read20(self, address: int) -> bytes:
        return bytes(self.uc.mem_read(address, 20))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_unmapped(self, uc, access, address, size, value,
                     user_data) -> bool:
        self.faults.append((access, address, size))
        return False

    def _destructor(self, source: int) -> int:
        self.call_log.append(("deleting_destructor", self._norm(source)))
        if self.case.get("dtor_marks_source"):
            uc = self.uc
            uc.mem_write(source + 0x0C, struct.pack("<I", 0xD0D00000))
        return self.case["dtor_return"]

    # ----------------------------------------------------------------- stubs
    def _on_direct(self, uc, address, size, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_CTOR:
            self.call_log.append(("engine_func_00234278", self._norm(r0)))
            uc.mem_write(r0, self.case["ctor_bytes"])
            if self.case.get("ctor_mutates_global"):
                uc.mem_write(
                    GLOBAL_SLOT_ADDR, struct.pack("<I", ALT_ROOT)
                )
            uc.reg_write(arm.UC_ARM_REG_R0, 0x12342780)
        elif address == STUB_FACTORY:
            self.call_log.append(
                ("engine_func_00234160", self._norm(r0), r1)
            )
            if self.case.get("factory_mutates_global"):
                uc.mem_write(
                    GLOBAL_SLOT_ADDR, struct.pack("<I", ALT_ROOT)
                )
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["factory_ptr"])
        elif address == STUB_LIST:
            self.call_log.append(("shop_func_002337a0", self._norm(r0)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["list_index"])
        elif address == STUB_TERMINATOR:
            message = self._read20(r0)
            self.call_log.append(
                ("camp_func_0027ec84", self._norm(r0), message)
            )
            if self.case.get("getter_clears_source"):
                uc.mem_write(CTX_ADDR + 0x208, struct.pack("<I", 0))
            result = self.case.get("terminator_result")
            if result is None:
                result = 1 if message[0] == 0 else 0
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_RANGE:
            message = self._read20(r0)
            self.call_log.append(
                ("engine_func_002a17c0", self._norm(r0), message)
            )
            result = self.case.get("range_result")
            if result is None:
                result = 1 if message[0] >= 0x64 else 0
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_FORWARD:
            message = self._read20(r1)
            self.call_log.append(
                ("func_002342b8", self._norm(r0), message)
            )
            uc.mem_write(r0 + 0x224, message[:16])
            uc.mem_write(r0 + 0x234, message[16:20])
            uc.mem_write(r0 + 0x004, struct.pack("<I", 0x13))
            uc.mem_write(r0 + 0x008, struct.pack("<I", 0))
            owned = struct.unpack(
                "<I", uc.mem_read(r0 + 0x208, 4)
            )[0]
            returned = 0x2342B800
            if owned != 0:
                returned = self._destructor(owned)
                uc.mem_write(r0 + 0x208, struct.pack("<I", 0))
            uc.reg_write(arm.UC_ARM_REG_R0, returned)
        elif address == STUB_SIGNAL:
            self.call_log.append(
                ("engine_func_00234004", self._norm(r0), r1, r2, r3)
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0x23400400)
        else:  # pragma: no cover
            raise AssertionError(f"unexpected direct stub {address:#x}")

    def _on_indirect(self, uc, address, size, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        if address == STUB_READ_MESSAGE:
            self.call_log.append(
                ("read_message", self._norm(r0), self._norm(r1))
            )
            uc.mem_write(r0, self.case["message"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0x600D0000)
        elif address == STUB_DELETING_DTOR:
            self._destructor(r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["dtor_return"])
        elif address == STUB_FULL_DTOR:
            self.call_log.append(("full_destructor", self._norm(r0)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0xF00D0000)
        else:  # pragma: no cover
            raise AssertionError(f"unexpected indirect stub {address:#x}")

    # ------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.faults = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(HEAP_ADDR, build_heap())
        self.uc.mem_write(GLOBAL_ADDR, build_global_page())
        self.uc.mem_write(SLOT_ADDR, build_slot_page())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        error = None
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as exception:  # fault cases only
            error = str(exception)

        unexpected_writes = []
        for address, size in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            if CTX_ADDR <= address < CTX_ADDR + CTX_SIZE:
                continue
            if HEAP_ADDR <= address < HEAP_ADDR + HEAP_SIZE:
                continue
            unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "faults": list(self.faults),
            "error": error,
            "unexpected_writes": unexpected_writes,
            "fixtures": {
                "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
                "heap": bytes(self.uc.mem_read(HEAP_ADDR, HEAP_SIZE)),
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "slot": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
            },
        }


def compare(orig: dict, cand: dict, case: dict) -> list[str]:
    problems: list[str] = []

    if orig["faults"] != cand["faults"]:
        problems.append(
            f"faults:\n    orig={orig['faults']} ({orig['error']})"
            f"\n    cand={cand['faults']} ({cand['error']})"
        )
    elif not orig["faults"]:
        for key in ("pc", "sp", "callee_saved"):
            if orig[key] != cand[key]:
                problems.append(
                    f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}"
                )
        if orig["ret"] != cand["ret"] and not case["r0_residue"]:
            problems.append(
                f"ret:\n    orig=0x{orig['ret']:08x}"
                f"\n    cand=0x{cand['ret']:08x}"
            )

    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"]) +
            "\n    cand=" + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            differing = [
                index for index, (left, right)
                in enumerate(zip(value, cand["fixtures"][key]))
                if left != right
            ]
            problems.append(
                f"fixture {key} differs at {differing[:16]}"
            )
    if not orig["faults"] and (
        orig["unexpected_writes"] or cand["unexpected_writes"]
    ):
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ------------------------------------------------------------------------ cases


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 0,
        "result": 0x11111111,
        "counter": 0,
        "source": None,
        "message": make_message(0x01, 1),
        "ctor_bytes": make_message(0x7E, 0x0E),
        "factory_ptr": CREATED,
        "list_index": 0,
        "r0_residue": False,
        "dtor_return": 0xD0D00000,
        "dtor_marks_source": False,
        "ctor_mutates_global": False,
        "factory_mutates_global": False,
        "getter_clears_source": False,
        "terminator_result": None,
        "range_result": None,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []
    add = cases.append

    # --- top-level state dispatch -------------------------------------------
    add(base_case("state 0 creates a source", state=0, r0_residue=True))
    add(base_case("state 0 replaces an owned source", state=0,
                  source=SOURCE_A, r0_residue=True))
    add(base_case("state 0 null factory result", state=0, factory_ptr=0,
                  r0_residue=True))
    for state in (5, 6, 0x270E, 0x2710, 0x7FFFFFFF, 0x80000000,
                  0xFFFFFFFF):
        add(base_case(f"state 0x{state:08x} falls through", state=state,
                      source=SOURCE_A, r0_residue=True))
    add(base_case("state 0x0000270f signals", state=0x270F, source=SOURCE_A))
    add(base_case("state 0x0000270f signals without a source", state=0x270F))

    # --- state 2 creation ----------------------------------------------------
    for source in (None, SOURCE_A, SOURCE_B):
        for index in (0, 1, 2, 0xFFFFFFFF, 0x80000000):
            source_name = "null" if source is None else f"0x{source:x}"
            add(base_case(
                f"state 2 source {source_name} index 0x{index:08x}",
                state=2, source=source, list_index=index,
                r0_residue=True,
            ))
    add(base_case("state 2 root sampled after the constructor", state=2,
                  source=SOURCE_A, ctor_mutates_global=True, list_index=1,
                  r0_residue=True))
    add(base_case("state 2 root is not re-read after the factory", state=2,
                  source=SOURCE_B, factory_mutates_global=True, list_index=2,
                  r0_residue=True))
    add(base_case("state 2 countdown/result bytes preserved", state=2,
                  source=SOURCE_A, result=0xDEADBEEF, counter=0x7FFFFFFF,
                  r0_residue=True))
    add(base_case("state 2 null factory faults on the id store", state=2,
                  source=SOURCE_A, factory_ptr=0, list_index=0))

    # --- states 1 and 3: source query and opcode tail ------------------------
    opcode_cases = (
        (0x00, "opcode 0x00", True),
        (0x01, "opcode 0x01", False),
        (0x63, "opcode 0x63", False),
        (0x64, "opcode 0x64", True),
        (0x66, "opcode 0x66", False),
        (0x67, "opcode 0x67", True),
        (0x68, "opcode 0x68", True),
        (0xFF, "opcode 0xff", True),
    )
    for state in (1, 3):
        for opcode, label, residue in opcode_cases:
            add(base_case(
                f"state {state} {label} source A", state=state,
                source=SOURCE_A, message=make_message(opcode, state),
                r0_residue=residue,
            ))
    # zero opcode with the other source object and a marker destructor return
    for state in (1, 3):
        add(base_case(
            f"state {state} opcode 0x00 source B destructor return",
            state=state, source=SOURCE_B, message=make_message(0x00, 0x42),
            dtor_return=0xD0D0BEEF,
        ))
    # the getter clears the owned pointer: state 3 must re-read it for deletion
    add(base_case("state 3 getter clears source before deletion", state=3,
                  source=SOURCE_A, message=make_message(0x00, 0x55),
                  getter_clears_source=True))
    add(base_case("state 1 getter clears source is unobserved", state=1,
                  source=SOURCE_A, message=make_message(0x66, 0x56),
                  getter_clears_source=True))
    # the destructor marks the source object
    add(base_case("state 3 destructor writes the source", state=3,
                  source=SOURCE_B, message=make_message(0x00, 0x57),
                  dtor_marks_source=True))
    # helper-result overrides prove the caller consumes each result
    add(base_case("state 1 forced non-zero terminator", state=1,
                  source=SOURCE_A, message=make_message(0x01, 0x58),
                  terminator_result=1))
    add(base_case("state 1 forced zero range check", state=1,
                  source=SOURCE_A, message=make_message(0x66, 0x59),
                  range_result=0))
    add(base_case("state 3 forced non-zero terminator", state=3,
                  source=SOURCE_A, message=make_message(0x01, 0x5A),
                  r0_residue=True, terminator_result=1))
    # missing owned source is dereferenced without a null check
    for state in (1, 3):
        add(base_case(f"state {state} null source faults", state=state,
                      source=None, message=make_message(0x00, 0x5B)))

    # --- state 4 countdown ---------------------------------------------------
    for counter in (-2, -1, 0, 1, 2, 3, 0x7FFFFFFE, 0x7FFFFFFF,
                    0x80000000, 0xFFFFFFFF):
        for source in (None, SOURCE_A):
            source_name = "null" if source is None else "A"
            add(base_case(
                f"state 4 counter 0x{counter & 0xFFFFFFFF:08x} "
                f"source {source_name}",
                state=4, counter=counter, source=source,
                result=0xA5A5A5A5,
            ))
    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    residue_names: list[str] = []
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand, case)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        for entry in orig["call_log"]:
            if entry[0] == "full_destructor":
                raise SystemExit(
                    "vtable slot 0 was called; the ARM evidence only reaches "
                    "slot 1"
                )
        if (not orig["faults"]) and orig["ret"] != cand["ret"]:
            residue_names.append(case["name"])
        passed += 1
        suffix = " (fault)" if orig["faults"] else ""
        print(f"  [PASS] {case['name']}{suffix}")
    print(
        f"\n  incidental r0 residue differences: {len(residue_names)} "
        f"(declared paths only)"
    )
    for name in residue_names[:8]:
        print(f"    residue: {name}")
    if len(residue_names) > 8:
        print(f"    ... and {len(residue_names) - 8} more")
    return passed


def main() -> None:
    print("Testing engine_func_00392acc (0x00392acc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("table_lead", "constexpr u32 kTableLead         = 0x9AA;",
         "constexpr u32 kTableLead         = 0x9A8;"),
        ("table_stride", "constexpr u32 kTableStride       = 0x139;",
         "constexpr u32 kTableStride       = 0x13B;"),
        ("created_id_offset", "constexpr u32 kCreatedId     = 0x014;",
         "constexpr u32 kCreatedId     = 0x018;"),
        ("counter_offset", "constexpr u32 kCounter       = 0x00C;",
         "constexpr u32 kCounter       = 0x010;"),
        ("signal_state", "constexpr u32 kStateSignal      = 0x270F;",
         "constexpr u32 kStateSignal      = 0x270E;"),
        ("staged_message_offset",
         "constexpr u32 kStagedMessage = 0x210;",
         "constexpr u32 kStagedMessage = 0x214;"),
        ("terminator_result", "constexpr u32 kResultAfterMessage   = 10;",
         "constexpr u32 kResultAfterMessage   = 11;"),
        ("created_pointer_offset", "constexpr u32 kSource        = 0x208;",
         "constexpr u32 kSource        = 0x20C;"),
        ("opcode_f", "constexpr u8 kOpcodeF = 0x66;",
         "constexpr u8 kOpcodeF = 0x65;"),
        ("countdown_comparison",
         "if (static_cast<s32>(decremented) > 0) return;",
         "if (static_cast<s32>(decremented) > 1) return;"),
        ("factory_kind", "constexpr u32 kFactoryCreateKind    = 4;",
         "constexpr u32 kFactoryCreateKind    = 6;"),
        ("initial_countdown", "constexpr s32 kInitialCountdown     = 3;",
         "constexpr s32 kInitialCountdown     = 4;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad, case):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
