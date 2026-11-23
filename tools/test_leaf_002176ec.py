#!/usr/bin/env python3
"""Differential test for battle_func_002176ec (0x002176ec, 436 B).

Compiles src/engine/leaf_batch45_b.cpp, extracts battle_func_002176ec and the
unnamed 72-byte tail entry func_00217858, resolves the fourteen direct calls to
deterministic stubs placed at their original addresses, and executes the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
ARM machines with identical fixtures.

Compared results:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * ordered call log with every register argument and every architected stack
    word (21 for 0x002553ec, 3 each for 0x00250800 / 0x003dddf8, plus the s0
    bit pattern for 0x003dde9c);
  * the global word at 0x0043427c, the base table at +0x1E98, the 648-byte
    slot fields, the path-B camp row halfword, and every fixture page;
  * the 72-byte tail entry func_00217858 (all-zero, each flag, unaligned word).

Coverage: index boundaries 0 / 108 / 109 / 110, 32-bit signed wrap
(0xFFFFFFFF, 0x80000000), large positive indices, signed s16 field boundaries
(-0x8000, 0x7FFF, -1, 0), null and non-null helper results, two base and slot
offsets, two camp offsets, and the unchanged global load word.

Negative controls mutate the action id, the opaque 0x10178 constant, one stack
word, the field offset and the tail scale; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_002176ec"

FUNC_ADDR = 0x002176EC
FUNC_SIZE = 436
TAIL_ADDR = 0x00217858
TAIL_SIZE = 72

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every stub up to 0x3dddf8
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00020000
BASE_ADDR = 0x00700000
BASE_SIZE = 0x00020000
UNITS_ADDR = 0x00720000
UNITS_SIZE = 0x00020000
SLOT_ADDR = 0x00740000
SLOT_SIZE = 0x00010000
CAMP_ADDR = 0x00760000
CAMP_SIZE = 0x00010000
GLOBAL_ADDR = 0x00780000
GLOBAL_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_296F60 = 0x00296F60
STUB_27EB98 = 0x0027EB98
STUB_293C98 = 0x00293C98
STUB_282B94 = 0x00282B94
STUB_250960 = 0x00250960
STUB_2553EC = 0x002553EC
STUB_2508C0 = 0x002508C0
STUB_2A89E4 = 0x002A89E4
STUB_26E88C = 0x0026E88C
STUB_3DDE9C = 0x003DDE9C
STUB_250800 = 0x00250800
STUB_3DDDF8 = 0x003DDDF8

STUB_NAMES = {
    STUB_296F60: "engine_func_00296f60",
    STUB_27EB98: "script_vm_func_0027eb98",
    STUB_293C98: "ui_func_00293c98",
    STUB_282B94: "ui_func_00282b94",
    STUB_250960: "func_00250960",
    STUB_2553EC: "battle_func_002553ec",
    STUB_2508C0: "battle_func_002508c0",
    STUB_2A89E4: "camp_func_002a89e4",
    STUB_26E88C: "battle_func_0026e88c",
    STUB_3DDE9C: "battle_func_003dde9c",
    STUB_250800: "battle_func_00250800",
    STUB_3DDDF8: "battle_func_003dddf8",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_296F60: 0,
    STUB_27EB98: 0,
    STUB_293C98: 0,
    STUB_282B94: 0,
    STUB_250960: 0,
    STUB_2553EC: 21,
    STUB_2508C0: 0,
    STUB_2A89E4: 0,
    STUB_26E88C: 0,
    STUB_3DDE9C: 0,
    STUB_250800: 3,
    STUB_3DDDF8: 3,
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


def get_orig_tail() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(TAIL_ADDR - 0x00100000)
        return handle.read(TAIL_SIZE)


def find_symbol(obj_file: Path, needle: str) -> tuple[bytes, list]:
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if needle in name:
            return value
    raise RuntimeError(f"{needle} not found in {obj_file}: {sorted(funcs)}")


def relocate_main(obj_file: Path) -> bytes:
    code_raw, relocs = find_symbol(obj_file, "002176ec")
    code = bytearray(code_raw)
    for rel in relocs:
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    main_code = relocate_main(obj_file)
    tail_code, tail_relocs = find_symbol(obj_file, "00217858")
    if tail_relocs:
        raise RuntimeError("tail entry unexpectedly has relocations")
    return main_code, tail_code


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_main(obj_file), find_symbol(obj_file, "00217858")[0]


# --------------------------------------------------------------------- fixtures
def build_base(case: dict) -> bytes:
    page = bytearray(BASE_SIZE)
    offset = case.get("base_off", 0)
    struct.pack_into("<I", page, offset + 0x1E98, UNITS_ADDR)
    return bytes(page)


def build_slot(case: dict) -> bytes:
    page = bytearray(SLOT_SIZE)
    offset = case.get("slot_off", 0)
    struct.pack_into("<h", page, offset + 0x1B4, case.get("field_b4", 0))
    struct.pack_into("<h", page, offset + 0x1B6, case.get("field_b6", 0))
    return bytes(page)


def build_camp() -> bytes:
    page = bytearray(CAMP_SIZE)
    # Non-zero filler so the halfword clear at +0x2A and the bit OR at +0x44
    # are observable and independent.
    for offset in range(0, CAMP_SIZE - 0x48, 0x40):
        page[offset + 0x2A] = 0x5A
        page[offset + 0x2B] = 0xA5
        page[offset + 0x44] = 0x00
        page[offset + 0x45] = 0x00
    return bytes(page)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(BASE_ADDR, BASE_SIZE)
        self.uc.mem_map(UNITS_ADDR, UNITS_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(CAMP_ADDR, CAMP_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        # This Unicorn build has no VFP execution unit.  The only VFP
        # instruction reachable from the function is a PC-relative
        # `vldr s0, [pc, #imm8*4]`; emulate it and skip the instruction.
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_vfp,
            begin=FUNC_ADDR,
            end=FUNC_ADDR + 0x400,
        )

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_vfp(self, uc, address: int, size: int, user_data) -> None:
        instruction = struct.unpack("<I", uc.mem_read(address, 4))[0]
        if (instruction & 0xFFFF0F00) != 0xED9F0A00:
            return
        literal = address + 8 + ((instruction & 0xFF) * 4)
        value = struct.unpack("<I", uc.mem_read(literal, 4))[0]
        uc.reg_write(arm.UC_ARM_REG_S0, value)
        uc.reg_write(arm.UC_ARM_REG_PC, address + 4)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_296F60:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["index"] & 0xFFFFFFFF)
        elif address == STUB_27EB98:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("ref", 0) & 0xFFFFFFFF)
        elif address == STUB_293C98:
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                BASE_ADDR + self.case.get("base_off", 0),
            )
        elif address == STUB_282B94:
            self._log(address, r0, r1)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                SLOT_ADDR + self.case.get("slot_off", 0),
            )
        elif address == STUB_250960:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2553EC:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2508C0:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_2A89E4:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                CAMP_ADDR + self.case.get("camp_off", 0),
            )
        elif address == STUB_26E88C:
            self._log(address, r0, r1)
            if r0:
                current = struct.unpack("<H", uc.mem_read(r0 + 0x44, 2))[0]
                updated = current | ((1 << (r1 & 31)) & 0xFFFF)
                uc.mem_write(r0 + 0x44, struct.pack("<H", updated))
        elif address == STUB_3DDE9C:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self._log(address, r0, r1, r2, s0 & 0xFFFFFFFF)
        elif address == STUB_250800:
            self._log(address, r0, r1, r2, r3)
        elif address == STUB_3DDDF8:
            self._log(address, r0, r1, r2, r3)
        else:  # pragma: no cover - guarded by registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, entry: int, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        clear = max(FUNC_SIZE, len(code))
        self.uc.mem_write(FUNC_ADDR, b"\x00" * clear)
        if entry == FUNC_ADDR:
            self.uc.mem_write(FUNC_ADDR, code)
        else:
            self.uc.mem_write(TAIL_ADDR, b"\x00" * max(TAIL_SIZE, len(code)))
            self.uc.mem_write(TAIL_ADDR, code)

        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(BASE_ADDR, build_base(case))
        self.uc.mem_write(UNITS_ADDR, b"\x11" * UNITS_SIZE)
        self.uc.mem_write(SLOT_ADDR, build_slot(case))
        self.uc.mem_write(CAMP_ADDR, build_camp())
        self.uc.mem_write(GLOBAL_ADDR, b"\x22" * GLOBAL_SIZE)
        self.uc.mem_write(
            0x0043427C,
            struct.pack("<I", case.get("global_word", GLOBAL_ADDR) & 0xFFFFFFFF),
        )
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("r0", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(entry, TRAP_ADDR, timeout=5_000_000)
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
            "call_log": self._normalise(self.call_log),
            "writes": unexpected_writes,
            "memory": {
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "base": bytes(self.uc.mem_read(BASE_ADDR, BASE_SIZE)),
                "units": bytes(self.uc.mem_read(UNITS_ADDR, UNITS_SIZE)),
                "slot": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
                "camp": bytes(self.uc.mem_read(CAMP_ADDR, CAMP_SIZE)),
            },
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
    if orig["writes"] != cand["writes"]:
        problems.append(
            f"writes:\n    orig={orig['writes']!r}\n    cand={cand['writes']!r}"
        )
    for key, value in orig["memory"].items():
        if value != cand["memory"][key]:
            problems.append(f"memory {key} was modified differently")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "index": 0,
        "ref": GLOBAL_ADDR + 0x1000,
        "base_off": 0,
        "slot_off": 0,
        "field_b4": 0,
        "field_b6": 0,
        "camp_off": 0,
        "global_word": GLOBAL_ADDR,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- index boundaries and both paths
    cases.append(base_case("index 0", index=0,
                           field_b4=0x1234, field_b6=-0x2345))
    cases.append(base_case("index 0x6c last path A", index=0x6C,
                           field_b4=-0x8000, field_b6=0x7FFF))
    cases.append(base_case("index 0x6d first path B", index=0x6D))
    cases.append(base_case("index 0x6e path B", index=0x6E, camp_off=0x40))
    cases.append(base_case("index 0x6d with camp offset", index=0x6D,
                           camp_off=0x80))
    cases.append(base_case("index 0x100", index=0x100, camp_off=0xC0))

    # --- 32-bit signed comparison boundaries
    cases.append(base_case("index -1 stays path A", index=0xFFFFFFFF,
                           field_b4=-1, field_b6=0))
    cases.append(base_case("index INT_MIN stays path A", index=0x80000000,
                           field_b4=0, field_b6=-1))
    cases.append(base_case("index INT_MAX path B", index=0x7FFFFFFF,
                           camp_off=0x40))
    cases.append(base_case("index 0xFFFFFF00 path A", index=0xFFFFFF00,
                           field_b4=0x7FFF, field_b6=-0x8000))

    # --- signed s16 field boundaries / null and non-null helper results
    for b4, b6 in (
        (-0x8000, 0x7FFF),
        (0x7FFF, -0x8000),
        (-1, 0),
        (0, -1),
        (0x0100, -0x0100),
    ):
        cases.append(base_case(f"fields b4={b4} b6={b6}", index=5,
                               field_b4=b4, field_b6=b6))
    cases.append(base_case("null ref, path A", index=7, ref=0,
                           field_b4=-2, field_b6=2))
    cases.append(base_case("null ref, path B", index=0x6D, ref=0))
    cases.append(base_case("base/slot offsets", index=42, base_off=0x40,
                           slot_off=0x20, field_b4=-0x1234,
                           field_b6=0x4321))
    cases.append(base_case("large base/slot offsets", index=108,
                           base_off=0x1F00, slot_off=0x8000,
                           field_b4=0x7FFF, field_b6=-0x8000))

    # --- global word load is forwarded verbatim
    for value in (0x00000000, 0x12345678, 0xFFFFFFFF, 0x00440000):
        cases.append(base_case(f"global word 0x{value:08x}",
                               global_word=value, index=3))

    return cases


def make_tail_cases() -> list[dict]:
    cases: list[dict] = []

    # 0x25..0x29 are absolute offsets in the fixture page (q = p + 0x5900);
    # p is the fixture page base.
    def tail_case(name, **fields):
        data = bytearray(0x6000)
        for name_, value in fields.items():
            offset = int(name_[1:], 16)
            data[offset] = value & 0xFF
            if value > 0xFF:
                data[offset + 1] = (value >> 8) & 0xFF
        return {"name": name, "page": bytes(data)}

    cases.append(tail_case("tail all zero"))
    for offset in (0x5925, 0x5926, 0x5927, 0x5928):
        cases.append(tail_case(f"tail flag 0x{offset:x} set", **{f"x{offset:x}": 1}))
    for value in (0x00000001, 0x80000000, 0x00010000, 0xFFFFFFFF):
        cases.append(
            tail_case(
                f"tail word 0x{value:08x}",
                x5925=0,
                x5926=0,
                x5927=0,
                x5928=0,
                x5929=value,
            )
        )
    cases.append(tail_case("tail word low byte only", x5929=0x7F))
    return cases


def run_main_cases(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(FUNC_ADDR, orig_code, case)
        cand = Runner().run(FUNC_ADDR, cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def run_tail_cases(orig_tail, cand_tail, cases) -> int:
    passed = 0
    for case in cases:
        fixture = case["page"]
        orig = Runner()
        orig.uc.mem_write(TAIL_ADDR, orig_tail)
        orig.uc.mem_write(DATA_ADDR, fixture)
        orig.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        orig.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        orig.uc.reg_write(arm.UC_ARM_REG_R0, DATA_ADDR)
        try:
            orig.uc.emu_start(TAIL_ADDR, TRAP_ADDR, timeout=1_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = orig.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"tail crash at PC=0x{pc:08x}: {error}") from error
        orig_result = (
            orig.uc.reg_read(arm.UC_ARM_REG_R0),
            orig.uc.reg_read(arm.UC_ARM_REG_PC),
            orig.uc.reg_read(arm.UC_ARM_REG_SP),
            bytes(orig.uc.mem_read(DATA_ADDR, 0x6000)),
        )

        cand = Runner()
        cand.uc.mem_write(TAIL_ADDR, b"\x00" * max(TAIL_SIZE, len(cand_tail)))
        cand.uc.mem_write(TAIL_ADDR, cand_tail)
        cand.uc.mem_write(DATA_ADDR, fixture)
        cand.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        cand.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        cand.uc.reg_write(arm.UC_ARM_REG_R0, DATA_ADDR)
        try:
            cand.uc.emu_start(TAIL_ADDR, TRAP_ADDR, timeout=1_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = cand.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"tail crash at PC=0x{pc:08x}: {error}") from error
        cand_result = (
            cand.uc.reg_read(arm.UC_ARM_REG_R0),
            cand.uc.reg_read(arm.UC_ARM_REG_PC),
            cand.uc.reg_read(arm.UC_ARM_REG_SP),
            bytes(cand.uc.mem_read(DATA_ADDR, 0x6000)),
        )

        if orig_result != cand_result:
            print(f"  [FAIL] {case['name']}")
            print(f"    orig={orig_result[:3]!r} cand={cand_result[:3]!r}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  (r0={orig_result[0]})")
    return passed


def main() -> None:
    print("Testing battle_func_002176ec (0x002176ec) and tail func_00217858...")
    orig_code = get_orig_bytes()
    orig_tail = get_orig_tail()
    cand_code, cand_tail = compile_candidate()
    print(
        f"Original {len(orig_code)} B (+{len(orig_tail)} B tail), "
        f"candidate {len(cand_code)} B (+{len(cand_tail)} B tail)."
    )

    cases = make_cases()
    passed = run_main_cases(orig_code, cand_code, cases)

    tail_cases = make_tail_cases()
    tail_passed = run_tail_cases(orig_tail, cand_tail, tail_cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("action_id", "battle_func_002508c0(0x19, ref, row);",
         "battle_func_002508c0(0x1A, ref, row);"),
        ("opaque_id", "0x01000178u, 0, 0, 0, 0);",
         "0x01000179u, 0, 0, 0, 0);"),
        ("stack_word", "battle_func_003dddf8(0, ref, 0, 1, 2, 0xB4, 3);",
         "battle_func_003dddf8(0, ref, 0, 1, 2, 0xB5, 3);"),
        ("field_offset", "slot + 0x1B6)", "slot + 0x1B4)"),
        ("tail_scale", "battle_func_003dde9c(0, reinterpret_cast<u32>(ref), 0xF, 8.0f);",
         "battle_func_003dde9c(0, reinterpret_cast<u32>(ref), 0xF, 4.0f);"),
    ):
        mutant_code, mutant_tail = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(FUNC_ADDR, orig_code, case)
            bad = Runner().run(FUNC_ADDR, mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} main differential cases PASSED.")
    print(f"All {tail_passed}/{len(tail_cases)} tail differential cases PASSED.")


if __name__ == "__main__":
    main()
