#!/usr/bin/env python3
"""Differential test for camp_func_001a7cac (0x001a7cac) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the camp_func_001a7cac body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every observable register argument (the
    zero-fill's forwarded r0 and the 0x002883BC stack destination included);
  * the full self/record/list/low pages (every byte the routine can observe or
    write), so the exact zero-fill length, every field width and the bit-map
    update are checked;
  * any emulated write outside the private stack and the fixture pages.

Coverage: mode 0, 1, 2, 3 and other non-zero modes; every free-slot position
including the 0x17 bound and a full list; signed slot boundaries; all record
field offsets with 0x7FFF/0x8000/0xFFFF values; bit indices 0..0xFFFF; detail
nibble 0x0F/0x07/0x00/0xF0 patterns; null and non-null helper results; and a
final return sentinel sweep.  Negative controls mutate the zero-fill size, the
free-slot bound, the bit-map base, the bit-index offset, the detail mask and
the mode-3 selector; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001a7cac"

FUNC_ADDR = 0x001A7CAC
FUNC_SIZE = 644

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # function plus every stub below 0x300000
SELF_ADDR = 0x00710000
SELF_SIZE = 0x00010000
RECORD_ADDR = 0x00720000
RECORD_SIZE = 0x00010000
BASE_ADDR = 0x00730000
BASE_SIZE = 0x00010000
LOW_ADDR = 0x00000000  # makes a null helper result observable instead of fatal
LOW_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs live at the same addresses.
STUB_2C4B30 = 0x002C4B30
STUB_2A8A08 = 0x002A8A08
STUB_2032B8 = 0x002032B8
STUB_1DD9F4 = 0x001DD9F4
STUB_2B9364 = 0x002B9364
STUB_2883BC = 0x002883BC
STUB_29C950 = 0x0029C950
STUB_29C084 = 0x0029C084

STUB_NAMES = {
    STUB_2C4B30: "engine_func_002c4b30",
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_2032B8: "func_002032b8",
    STUB_1DD9F4: "script_vm_func_001dd9f4",
    STUB_2B9364: "camp_func_002b9364",
    STUB_2883BC: "camp_func_002883bc",
    STUB_29C950: "script_vm_func_0029c950",
    STUB_29C084: "camp_func_0029c084",
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

SLOT_LIST_OFFSET = 0x90F0
SLOT_LIST_COUNT = 0x18
DETAIL_SIZE = 0x34


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def pattern(size: int, seed: int) -> bytearray:
    return bytearray(((seed + i * 0x9D) & 0xFF) for i in range(size))


def build_self() -> bytes:
    # Sentinel fill; the routine's zero-fill must clear exactly 0x604 bytes and
    # the canary bytes after that must stay untouched.
    return bytes(pattern(SELF_SIZE, 0x5A))


def build_record(case: dict) -> bytes:
    page = pattern(RECORD_SIZE, 0x11)
    seed = case.get("record_seed", 0x0131)
    overrides = case.get("record_fields", {})
    for offset in (
        0x14, 0x16, 0x1A, 0x1E, 0x20, 0x22, 0x1C,
        0x3C, 0x3E, 0x40, 0x42, 0x44, 0x46, 0x48, 0x4A,
    ):
        value = overrides.get(offset, (seed + offset * 0x1111) & 0xFFFF)
        struct.pack_into("<H", page, offset, value)
    page[3] = case.get("record_byte3", 0x5A) & 0xFF
    struct.pack_into("<H", page, 0x38, case.get("bit_index", 0x1B) & 0xFFFF)
    return bytes(page)


def build_list(case: dict) -> bytes:
    page = pattern(BASE_SIZE, 0x33)
    slots = case.get("slots")
    if slots is None:
        slots = [0x7F] * SLOT_LIST_COUNT
    if len(slots) != SLOT_LIST_COUNT:
        raise ValueError("slots fixture must have 0x18 entries")
    for index, value in enumerate(slots):
        page[SLOT_LIST_OFFSET + index] = value & 0xFF
    return bytes(page)


def build_low(case: dict) -> bytes:
    # Both a null list base and a null record pointer resolve here, so provide
    # the same fixtures at their respective offsets.
    page = pattern(LOW_SIZE, 0x77)
    record = build_record(case)
    page[0:0x100] = record[0:0x100]
    page[SLOT_LIST_OFFSET:SLOT_LIST_OFFSET + SLOT_LIST_COUNT] = (
        build_list(case)[SLOT_LIST_OFFSET:SLOT_LIST_OFFSET + SLOT_LIST_COUNT]
    )
    return bytes(page)


def build_detail(case: dict) -> bytes:
    page = pattern(DETAIL_SIZE, 0x23)
    for offset, value in case.get("detail_bytes", {}).items():
        page[offset] = value & 0xFF
    struct.pack_into("<I", page, 0x30, case.get("detail_word", 0x12345678))
    return bytes(page)


class A7CACRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
        self.uc.mem_map(BASE_ADDR, BASE_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
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
        self.detail = b""

    # ------------------------------------------------------------------ stubs
    def _normalise(self, value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C4B30:
            self._log(address, r0, r1)
            if not (SELF_ADDR <= r0 < SELF_ADDR + SELF_SIZE):
                raise AssertionError(f"zero-fill dst 0x{r0:08x} is not self")
            if r1 > SELF_SIZE - (r0 - SELF_ADDR):
                raise AssertionError(f"zero-fill size 0x{r1:x} overruns")
            uc.mem_write(r0, b"\x00" * r1)
            uc.reg_write(arm.UC_ARM_REG_R0, (r0 + r1) & 0xFFFFFFFF)
        elif address == STUB_2A8A08:
            # The callee ignores its only register; log it so the forwarded
            # zero-fill return stays part of the contract.
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("base", BASE_ADDR))
        elif address == STUB_2032B8:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_1DD9F4:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_2B9364:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("record", RECORD_ADDR))
        elif address == STUB_2883BC:
            self._log(address, r0, self._normalise(r1))
            uc.mem_write(r1, self.detail)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("detail_ret", 1) & 0xFFFFFFFF
            )
        elif address == STUB_29C950:
            self._log(address, r0)
            uc.mem_write(r0 + 0x0E, struct.pack("<H", self.case["seq_a"]))
            uc.mem_write(r0 + 0x10, struct.pack("<H", self.case["seq_b"]))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_29C084:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("final_ret", 0x29C084A5)
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.detail = build_detail(case)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SELF_ADDR, build_self())
        self.uc.mem_write(RECORD_ADDR, build_record(case))
        self.uc.mem_write(BASE_ADDR, build_list(case))
        self.uc.mem_write(LOW_ADDR, build_low(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("slot", 0))
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("id", 0x1234ABCD))
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("mode", 0))
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_self = SELF_ADDR <= address < SELF_ADDR + SELF_SIZE
            in_record = RECORD_ADDR <= address < RECORD_ADDR + RECORD_SIZE
            in_base = BASE_ADDR <= address < BASE_ADDR + BASE_SIZE
            in_low = LOW_ADDR <= address < LOW_ADDR + LOW_SIZE
            if not (in_stack or in_self or in_record or in_base or in_low):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
                "record": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
                "list": bytes(self.uc.mem_read(BASE_ADDR, BASE_SIZE)),
                "low": bytes(self.uc.mem_read(LOW_ADDR, LOW_SIZE)),
            },
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
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            mismatch = next(
                (i for i, (a, b) in enumerate(zip(value, cand["fixtures"][key])) if a != b),
                None,
            )
            problems.append(
                f"fixture {key} differs at offset {mismatch:#x}"
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
        "slot": 0,
        "id": 0x1234ABCD,
        "mode": 0,
        "seq_a": 0x1122,
        "seq_b": 0x3344,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- mode selection: 0 and 3 copy the table entry, 1 the detail record,
    #     everything else skips the copies but still runs the tail.
    cases.append(base_case("mode 0 baseline"))
    cases.append(base_case("mode 1 baseline", mode=1))
    cases.append(base_case("mode 2 skips copies", mode=2))
    cases.append(base_case("mode 3 skips scan", mode=3))
    cases.append(base_case("mode 4 skips copies", mode=4))
    cases.append(base_case("mode 0xFFFFFFFF", mode=-1))

    # --- free-slot scan: first negative slot at every interesting position.
    for index in (0, 1, 5, 0x16, 0x17):
        slots = [0x7F] * SLOT_LIST_COUNT
        slots[index] = 0x80 if index % 2 else 0xFF
        cases.append(
            base_case(f"first free slot {index}", mode=0, slot=index, slots=slots)
        )
        cases.append(
            base_case(f"first free slot {index} mode 3", mode=3, slot=index,
                      slots=slots)
        )
    cases.append(base_case("no free slot", mode=0))
    cases.append(base_case(
        "no free slot mixed signs", mode=0,
        slots=[0x00, 0x7F, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06,
               0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E,
               0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16]))
    cases.append(base_case(
        "free slot already negative at 0x17 with 0x7F prefix", mode=0,
        slots=[0x7F] * 0x17 + [0x81]))
    cases.append(base_case("slot argument 0x00", slot=0x00, mode=0,
                           slots=[0xFF] + [0x7F] * 0x17))
    cases.append(base_case("slot argument 0xFF", slot=0xFF, mode=0,
                           slots=[0xFF] + [0x7F] * 0x17))

    # --- record field boundaries: every copied u16 sees min/max/sign values.
    for value, label in ((0x7FFF, "0x7fff"), (0x8000, "0x8000"),
                         (0xFFFF, "0xffff"), (0x0000, "0x0000")):
        fields = {
            0x14: value, 0x16: value ^ 0xFFFF, 0x1A: value, 0x1E: value,
            0x20: value ^ 0xAAAA, 0x22: value, 0x1C: value ^ 0x5555,
            0x3C: value, 0x3E: value ^ 0xFFFF, 0x40: value, 0x42: value,
            0x44: value ^ 0xAAAA, 0x46: value, 0x48: value ^ 0x5555,
            0x4A: value,
        }
        cases.append(base_case(f"record fields {label}", mode=0,
                               record_fields=fields))
        cases.append(base_case(f"record fields {label} mode 3", mode=3,
                               record_fields=fields))
    cases.append(base_case("record byte 3 0x00", mode=0, record_byte3=0x00))
    cases.append(base_case("record byte 3 0xFF", mode=0, record_byte3=0xFF))

    # --- bit index: word 0x38 selects byte and bit inside the 0x4C map.
    for bit_index in (0x0000, 0x0007, 0x0008, 0x001F, 0x003F, 0xFFFF):
        cases.append(base_case(f"bit index 0x{bit_index:04x}", mode=0,
                               bit_index=bit_index))
        cases.append(base_case(f"bit index 0x{bit_index:04x} mode 1", mode=1,
                               bit_index=bit_index))

    # --- detail-record path: nibble extraction and 32-bit word copy.
    for value in (0x00, 0x7F, 0x80, 0xF0, 0xB5, 0xFF):
        cases.append(base_case(
            f"detail byte 0x16 = 0x{value:02x}", mode=1,
            detail_bytes={0x16: value}))
    for word in (0x00000000, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 0x12345678):
        cases.append(base_case(f"detail word 0x{word:08x}", mode=1,
                               detail_word=word))
    cases.append(base_case(
        "detail distinct bytes", mode=1,
        detail_bytes={i: (0x80 + i) & 0xFF for i in range(DETAIL_SIZE)},
        detail_word=0xA1B2C3D4))

    # --- id truncation and helper return variants.
    for ident in (0x00000000, 0x0000FFFF, 0x1234ABCD, 0xFFFFFFFF,
                  0x00008000, 0x7FFF8000):
        cases.append(base_case(f"id 0x{ident:08x}", id=ident))
        cases.append(base_case(f"id 0x{ident:08x} mode 1", id=ident, mode=1))
    cases.append(base_case("null list base", mode=0, base=0,
                           slots=[0xFF] + [0x7F] * 0x17))
    cases.append(base_case("null list base mode 3", mode=3, base=0,
                           slots=[0xFF] + [0x7F] * 0x17))
    cases.append(base_case("null record mode 0", mode=0, record=0))
    cases.append(base_case("null record mode 1", mode=1, record=0))
    cases.append(base_case("null record mode 2", mode=2, record=0))
    cases.append(base_case("null detail return mode 1", mode=1, detail_ret=0))
    cases.append(base_case("non-null detail return mode 1", mode=1,
                           detail_ret=0x2883BC00))

    # --- tail state and forwarded return value.
    for a, b in ((0x0000, 0xFFFF), (0xFFFF, 0x0000), (0x8000, 0x7FFF)):
        cases.append(base_case(f"tail pair {a:#06x}/{b:#06x}",
                               seq_a=a, seq_b=b))
    for value in (0x00000000, 0xFFFFFFFF, 0xF0000000, 0x29C084A5):
        cases.append(base_case(f"final return 0x{value:08x}", final_ret=value))

    return cases


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001a7cac" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_001a7cac not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
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
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = A7CACRunner().run(orig_code, case)
        cand = A7CACRunner().run(cand_code, case)
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
    print("Testing camp_func_001a7cac (0x001a7cac)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          "(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("zero_fill_size",
         "constexpr u32 k001a7cacZeroFillSize = 0x604;",
         "constexpr u32 k001a7cacZeroFillSize = 0x600;"),
        ("slot_list_count",
         "constexpr u32 k001a7cacSlotListCount = 0x18;",
         "constexpr u32 k001a7cacSlotListCount = 0x17;"),
        ("bit_map_offset",
         "constexpr u32 k001a7cacBitMapOffset = 0x4C;",
         "constexpr u32 k001a7cacBitMapOffset = 0x4E;"),
        ("bit_index_offset",
         "constexpr u32 k001a7cacEntryBitIndexOffset = 0x38;",
         "constexpr u32 k001a7cacEntryBitIndexOffset = 0x3A;"),
        ("detail_nibble_mask",
         "constexpr u32 k001a7cacDetailNibbleMask = 0x0F;",
         "constexpr u32 k001a7cacDetailNibbleMask = 0x07;"),
        ("mode_no_scan",
         "constexpr u32 k001a7cacModeNoScan = 3;",
         "constexpr u32 k001a7cacModeNoScan = 2;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = A7CACRunner().run(orig_code, case)
            bad = A7CACRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
