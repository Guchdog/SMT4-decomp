#!/usr/bin/env python3
"""Differential test for engine_func_003a604c (0x003a604c) using Unicorn ARM.

Compiles ``src/engine/leaf_batch45_b.cpp``, extracts the
``engine_func_003a604c`` body, resolves every direct call to a deterministic
stub at the original target address, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate in separate Unicorn
machines with identical fixtures.

Compared on every case:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log (helper name plus every register argument, including
    both array-constructor calls and the per-element flag calls);
  * the full 0x20000-byte shop-object page, the 0x1000-byte allocation page
    and the 0x1000-byte 0x002C0C04 lookup page;
  * every emulated write outside the private stack, object and allocation
    pages.

Coverage: type 1 (early return) and non-1; full 32-bit flag == 0, == 1 and
other values; modes 5/6/7/8/9, the 0x1F/0x20 setter boundary and signed
extremes; both outcomes of every 0x002876D0 probe; zero/non-zero allocation;
zero/non-zero 0x002C0C04 halfword; all nine rows with zero counts, mixed
flag bits, u16 value boundaries and the 0x400 element-array boundary.

Negative controls mutate the source for the +0x15D40 store, one UI command
constant, the row stride and the +0x37C selector; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_003a604c"

FUNC_ADDR = 0x003A604C
FUNC_SIZE = 900

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers 0x3A604C plus every stub up to 0x3A4818
OBJ_ADDR = 0x00710000
OBJ_SIZE = 0x00020000  # shop object is 0x15D6C bytes; rows end before 0x9CB0
ALLOC_ADDR = 0x00730000
ALLOC_SIZE = 0x00001000
LOOKUP_ADDR = 0x00740000
LOOKUP_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_22E614 = 0x0022E614
STUB_2C5F58 = 0x002C5F58
STUB_28757C = 0x0028757C
STUB_3A4734 = 0x003A4734
STUB_233600 = 0x00233600
STUB_232800 = 0x00232800
STUB_2C23F8 = 0x002C23F8
STUB_2333BC = 0x002333BC
STUB_2639F4 = 0x002639F4
STUB_2C0C04 = 0x002C0C04
STUB_3A18B8 = 0x003A18B8
STUB_282E6C = 0x00282E6C
STUB_28DC54 = 0x0028DC54
STUB_28D974 = 0x0028D974
STUB_2C4E28 = 0x002C4E28
STUB_2C5AB8 = 0x002C5AB8
STUB_3A4818 = 0x003A4818
STUB_2A0678 = 0x002A0678
STUB_343D40 = 0x00343D40
STUB_343CE4 = 0x00343CE4
STUB_2876D0 = 0x002876D0
STUB_2A0640 = 0x002A0640
STUB_343E44 = 0x00343E44
STUB_29C0FC = 0x0029C0FC

# 0x002C5F58 is Thumb code in the pinned image (the original uses BLX). A real
# linker emits BLX for the candidate's call as well.
THUMB_STUBS = {STUB_2C5F58}

STUB_NAMES = {
    STUB_22E614: "engine_func_0022e614",
    STUB_2C5F58: "ui_func_002c5f58",
    STUB_28757C: "engine_func_0028757c",
    STUB_3A4734: "engine_func_003a4734",
    STUB_233600: "unite_func_00233600",
    STUB_232800: "unite_func_00232800",
    STUB_2C23F8: "AsdMemory_func_002c23f8",
    STUB_2333BC: "unite_func_002333bc",
    STUB_2639F4: "PlaceWin_Init",
    STUB_2C0C04: "engine_func_002c0c04",
    STUB_3A18B8: "shop_func_003a18b8",
    STUB_282E6C: "script_vm_func_00282e6c",
    STUB_28DC54: "camp_func_0028dc54",
    STUB_28D974: "ButtonHelp_Init",
    STUB_2C4E28: "AsdTMTexTable_func_002c4e28",
    STUB_2C5AB8: "AsdRow_LoadNow",
    STUB_3A4818: "engine_func_003a4818",
    STUB_2A0678: "ui_func_002a0678",
    STUB_343D40: "engine_func_00343d40",
    STUB_343CE4: "engine_func_00343ce4",
    STUB_2876D0: "ui_func_002876d0",
    STUB_2A0640: "camp_func_002a0640",
    STUB_343E44: "engine_func_00343e44",
    STUB_29C0FC: "camp_func_0029c0fc",
}

# Symbols that do not carry their address in the name.
NAME_ALIASES = {
    "placewin_init": STUB_2639F4,
    "buttonhelp_init": STUB_28D974,
    "asdrow_loadnow": STUB_2C5AB8,
    "asdtmtextable_func_002c4e28": STUB_2C4E28,
    "asdmemory_func_002c23f8": STUB_2C23F8,
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

ROW_STRIDE = 0x1002
ROW_COUNT_OFFSET = 0x1C94
ROW_ELEMENT_OFFSET = 0x0C94
MAX_ELEMENTS = 0x400


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def resolve_symbol(symbol_name: str) -> int | None:
    lowered = symbol_name.lower()
    for address in STUB_NAMES:
        if f"{address:08x}" in lowered:
            return address
    for name, address in NAME_ALIASES.items():
        if name in lowered:
            return address
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003a604c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_003a604c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 10, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = resolve_symbol(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = target - pc
        if target in THUMB_STUBS:
            if displacement & 3:
                raise RuntimeError(
                    f"unaligned Thumb call target 0x{target:08x}"
                )
            instruction = (
                0xFA000000
                | ((displacement >> 2) & 0x00FFFFFF)
                | ((displacement & 2) << 23)
            )
            struct.pack_into("<I", code, rel.offset, instruction)
        else:
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset,
                cond | ((displacement >> 2) & 0x00FFFFFF),
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {count} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def build_object(case: dict) -> bytes:
    page = bytearray([0xA5]) * OBJ_SIZE
    counts = case.get("counts", [0] * 9)
    elements = case.get("elements", {})
    assert len(counts) == 9
    for row_index, count in enumerate(counts):
        base = row_index * ROW_STRIDE
        # Clear the 0x1000-byte element array so unset entries have flag bit 0
        # clear and the boundary cases stay cheap.
        page[base + ROW_ELEMENT_OFFSET:base + ROW_COUNT_OFFSET] = (
            b"\x00" * (ROW_COUNT_OFFSET - ROW_ELEMENT_OFFSET)
        )
        struct.pack_into("<H", page, base + ROW_COUNT_OFFSET, count & 0xFFFF)
        row_elements = elements.get(row_index, [])
        for index, (value, flags) in enumerate(row_elements):
            struct.pack_into(
                "<HH", page, base + ROW_ELEMENT_OFFSET + index * 4,
                value & 0xFFFF, flags & 0xFFFF,
            )
        # A few set-flag entries just past the fixture: an over-long loop is
        # visible both in the call log and through 0x00343E44's arguments.
        for index in range(len(row_elements), min(len(row_elements) + 2,
                                                  MAX_ELEMENTS)):
            struct.pack_into(
                "<HH", page, base + ROW_ELEMENT_OFFSET + index * 4,
                0xDEAD, 1,
            )
    return bytes(page)


def build_alloc() -> bytes:
    return bytes(ALLOC_SIZE)


def build_lookup(case: dict) -> bytes:
    page = bytearray(LOOKUP_SIZE)
    struct.pack_into("<H", page, 0x10, case.get("lookup_u16", 0) & 0xFFFF)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class ShopFactoryRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(ALLOC_ADDR, ALLOC_SIZE)
        self.uc.mem_map(LOOKUP_ADDR, LOOKUP_SIZE)
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
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.s4818_calls = 0
        self.case: dict = {}

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_22E614:
            self._log(address, r0)
            uc.mem_write(r0, struct.pack("<IIIII", 0, 0, 0, 0, 0xFFFFFFFF))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2C5F58:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_28757C:
            self._log(address, r0)
            self.uc.mem_write(r0 + 0x0D, b"\x00\x01")
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_3A4734:
            self._log(address, r0)
        elif address == STUB_233600:
            self._log(address, r0)
        elif address == STUB_232800:
            self._log(address, r0, r1, r2, r3)
            uc.mem_write(
                r0, struct.pack("<ffII", float(r1), float(r2), 0, 0)
            )
            uc.mem_write(r0 + 0x10, struct.pack("<I", r3))
        elif address == STUB_2C23F8:
            self._log(address, r0)
            if self.case.get("alloc_null", False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.mem_write(ALLOC_ADDR, b"\xCC" * 0x68)
                uc.reg_write(arm.UC_ARM_REG_R0, ALLOC_ADDR)
        elif address == STUB_2333BC:
            self._log(address, r0)
            uc.mem_write(r0, struct.pack("<IH", 0x002333BC, 0))
        elif address == STUB_2639F4:
            self._log(address)
        elif address == STUB_2C0C04:
            self._log(address, r0, r1, r2)
            uc.reg_write(arm.UC_ARM_REG_R0, LOOKUP_ADDR + 0x10)
        elif address == STUB_3A18B8:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x5A18B800)
        elif address == STUB_282E6C:
            self._log(address, r0, r1)
        elif address == STUB_28DC54:
            self._log(address)
        elif address == STUB_28D974:
            self._log(address)
        elif address == STUB_2C4E28:
            self._log(address, r0)
        elif address == STUB_2C5AB8:
            self._log(address, r0, r1)
        elif address == STUB_3A4818:
            self.s4818_calls += 1
            self._log(address, r0, self.s4818_calls)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x48000000 | self.s4818_calls)
        elif address == STUB_2A0678:
            self._log(address, r0, r1)
        elif address == STUB_343D40:
            self._log(address, r0, r1)
        elif address == STUB_343CE4:
            self._log(address, r0, r1)
        elif address == STUB_2876D0:
            returns = {
                0x0100005B: self.case.get("ret_5b", 0),
                0x0100005C: self.case.get("ret_5c", 0),
                0x01000060: self.case.get("ret_60", 0),
            }
            result = returns.get(r0, 0)
            self._log(address, r0, result)
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
        elif address == STUB_2A0640:
            self._log(address, r0, r1, r2)
        elif address == STUB_343E44:
            self._log(address, r0, r1)
        elif address == STUB_29C0FC:
            self._log(address, r0, r1)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.s4818_calls = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJ_ADDR, build_object(case))
        self.uc.mem_write(ALLOC_ADDR, build_alloc())
        self.uc.mem_write(LOOKUP_ADDR, build_lookup(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("object", OBJ_ADDR))
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("type", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("flag", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("mode", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=10_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_object = OBJ_ADDR <= address < OBJ_ADDR + OBJ_SIZE
            in_alloc = ALLOC_ADDR <= address < ALLOC_ADDR + ALLOC_SIZE
            if not (in_stack or in_object or in_alloc):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "object": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
            "alloc": bytes(self.uc.mem_read(ALLOC_ADDR, ALLOC_SIZE)),
            "lookup": bytes(self.uc.mem_read(LOOKUP_ADDR, LOOKUP_SIZE)),
            "unexpected_writes": unexpected_writes,
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
    if orig["object"] != cand["object"]:
        for offset in range(OBJ_SIZE):
            if orig["object"][offset] != cand["object"][offset]:
                break
        problems.append(f"object page differs first at +0x{offset:05x}")
    if orig["alloc"] != cand["alloc"]:
        problems.append("allocation page differs")
    if orig["lookup"] != cand["lookup"]:
        problems.append("lookup page differs")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "type": 0,
        "flag": 0,
        "mode": 0,
        "counts": [0] * 9,
        "elements": {},
        "alloc_null": False,
        "lookup_u16": 0,
        "ret_5b": 0,
        "ret_5c": 0,
        "ret_60": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- type 1 early-return branch
    cases.append(base_case("type 1 flag 0 mode 0", type=1))
    cases.append(base_case("type 1 flag 1 mode 9", type=1, flag=1, mode=9))
    cases.append(base_case("type 1 flag 5 mode 6", type=1, flag=5, mode=6))
    cases.append(base_case("type 1 null allocation", type=1, alloc_null=True))
    cases.append(base_case("type 1 lookup nonzero", type=1, lookup_u16=1))

    # --- type != 1, flag == 0
    cases.append(base_case("flag 0 mode 0 command 5B runs", mode=0))
    cases.append(base_case("flag 0 mode 0 command 5B skipped",
                           mode=0, ret_5b=1))
    cases.append(base_case("flag 0 mode 1", mode=1))
    cases.append(base_case("flag 0 mode 5", mode=5))
    cases.append(base_case("flag 0 mode 6 command 60 runs",
                           mode=6, ret_60=0))
    cases.append(base_case("flag 0 mode 6 command 60 skipped",
                           mode=6, ret_60=1))
    cases.append(base_case("flag 0 mode 7 command 60 runs", mode=7))
    cases.append(base_case("flag 0 mode 8 skips command", mode=8,
                           ret_5b=0))
    cases.append(base_case("flag 0 mode 0x1F setter", mode=0x1F))
    cases.append(base_case("flag 0 mode 0x20 setter boundary", mode=0x20))
    cases.append(base_case("flag 0 mode 0x21", mode=0x21))
    cases.append(base_case("flag 0 mode -1", mode=-1))

    # --- type != 1, flag == 1
    cases.append(base_case("flag 1 mode 5 command 60 runs", flag=1, mode=5))
    cases.append(base_case("flag 1 mode 5 command 60 skipped",
                           flag=1, mode=5, ret_60=1))
    cases.append(base_case("flag 1 mode 9 skips command", flag=1, mode=9,
                           ret_5c=0))
    cases.append(base_case("flag 1 mode 0 command 5C runs", flag=1, mode=0))
    cases.append(base_case("flag 1 mode 0 command 5C skipped",
                           flag=1, mode=0, ret_5c=1))
    cases.append(base_case("flag 1 mode 6", flag=1, mode=6))
    cases.append(base_case("flag 1 mode -1", flag=1, mode=-1))

    # --- other 32-bit flag values: no setter and no command pair, but the
    # stored flag byte still drives the 0x002C0C04 selector.
    cases.append(base_case("flag 2 mode 6", flag=2, mode=6))
    cases.append(base_case("flag 0xFFFFFFFF mode 5", flag=-1, mode=5))
    cases.append(base_case("flag 0x100 byte 0", flag=0x100, mode=0))
    cases.append(base_case("flag 0x101 byte 1", flag=0x101, mode=0,
                           lookup_u16=1))
    cases.append(base_case("flag 0x7F byte 0x7F", flag=0x7F, mode=8))

    # --- type is a full 32-bit comparison
    cases.append(base_case("type 2", type=2))
    cases.append(base_case("type -1", type=-1, flag=1, mode=5))
    cases.append(base_case("type 0xFFFFFFFF", type=0xFFFFFFFF))
    cases.append(base_case("type 1 with flag 0x100", type=1, flag=0x100))

    # --- allocation null / non-null and lookup halfword
    cases.append(base_case("allocation null", alloc_null=True))
    cases.append(base_case("lookup halfword 1", lookup_u16=1))
    cases.append(base_case("lookup halfword 0xFFFF", lookup_u16=0xFFFF))
    cases.append(base_case("lookup halfword 0x8000", lookup_u16=0x8000))

    # --- row scan: zero counts with set-flag entries just past them
    cases.append(base_case("rows all zero", counts=[0] * 9))

    # --- single-element rows and flag-bit selection
    cases.append(base_case(
        "row 0 one flagged entry", counts=[1, 0, 0, 0, 0, 0, 0, 0, 0],
        elements={0: [(0x1234, 1)]},
    ))
    cases.append(base_case(
        "row 0 one clear entry", counts=[1, 0, 0, 0, 0, 0, 0, 0, 0],
        elements={0: [(0x1234, 0)]},
    ))
    cases.append(base_case(
        "row 0 mixed three entries", counts=[3, 0, 0, 0, 0, 0, 0, 0, 0],
        elements={0: [(0x0000, 1), (0xFFFF, 0), (0x8000, 1)]},
    ))
    cases.append(base_case(
        "row 0 odd flags bits", counts=[2, 0, 0, 0, 0, 0, 0, 0, 0],
        elements={0: [(0x7FFF, 0xFFFE), (0x8001, 0xFFFF)]},
    ))
    cases.append(base_case(
        "every row one flagged entry",
        counts=[1] * 9,
        elements={row: [(row * 0x1111, 1)] for row in range(9)},
    ))
    cases.append(base_case(
        "mixed row counts", counts=[0, 1, 2, 3, 4, 5, 6, 7, 8],
        elements={
            row: [(0x1000 + row * 0x100 + index, index & 1)
                  for index in range(count)]
            for row, count in enumerate([0, 1, 2, 3, 4, 5, 6, 7, 8])
        },
    ))
    cases.append(base_case(
        "row 0 count 2 with one fixture entry",
        counts=[2, 0, 0, 0, 0, 0, 0, 0, 0],
        elements={0: [(0xAAAA, 0)]},
    ))

    # --- 0x400 element-array boundary on the last row
    boundary_elements = {8: [(index & 0xFFFF, 0)
                             for index in range(MAX_ELEMENTS)]}
    boundary_elements[8][0] = (0x0001, 1)
    boundary_elements[8][1] = (0x0002, 0)
    boundary_elements[8][MAX_ELEMENTS - 2] = (0xFFFE, 1)
    boundary_elements[8][MAX_ELEMENTS - 1] = (0xFFFF, 0)
    cases.append(base_case(
        "row 8 count 0x400 boundary",
        counts=[0, 0, 0, 0, 0, 0, 0, 0, MAX_ELEMENTS],
        elements=boundary_elements,
    ))

    # --- combined paths
    cases.append(base_case(
        "flag 1 mode 5 with row data", flag=1, mode=5, ret_60=0,
        counts=[1, 2, 0, 0, 0, 0, 0, 0, 1],
        elements={0: [(0x11, 1)], 1: [(0x22, 1), (0x33, 0)],
                  8: [(0x99, 1)]},
    ))
    cases.append(base_case(
        "flag 0 mode 8 with null allocation and rows",
        mode=8, alloc_null=True, lookup_u16=0xFFFF,
        counts=[1, 0, 0, 0, 0, 0, 0, 0, 0],
        elements={0: [(0xCAFE, 1)]},
    ))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = ShopFactoryRunner().run(orig_code, case)
        cand = ShopFactoryRunner().run(cand_code, case)
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
    print("Testing engine_func_003a604c (0x003a604c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(all call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("sprite_store_offset",
         "*reinterpret_cast<u32*>(object + 0x15D40) = 0;",
         "*reinterpret_cast<u32*>(object + 0x15D44) = 0;"),
        ("ui_command_5b", "0x0100005Bu)", "0x0100005Au)"),
        ("row_stride", "row_index * 0x1002u", "row_index * 0x1000u"),
        ("type_selector", "object + 0x37C) = 0x1F;",
         "object + 0x37C) = 0x1E;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = ShopFactoryRunner().run(orig_code, case)
            bad = ShopFactoryRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
