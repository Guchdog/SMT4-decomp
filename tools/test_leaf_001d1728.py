#!/usr/bin/env python3
"""Differential test for camp_func_001d1728 (0x001d1728) using Unicorn ARM.

Compiles ``src/engine/leaf_batch34_c.cpp``, extracts the camp_func_001d1728
body, resolves every direct call to a deterministic stub placed at the pinned
original address, and runs the pinned original (``extracted/exefs/code.bin``)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument and the architected stack
    argument of 0x0029C7C8 (normalising private-stack pointers);
  * the unit-id list handed to Unite_Init (contents, not just the pointer);
  * manager, party, save-record, entry-table, low-page and global memory;
  * every write performed outside the private stack must match.

Coverage: each early return (selected unit null, reject), the find-record loop
(empty count, first/middle/last hit, miss), the 15-bit descriptor fields with
boundary values, zero and 0xFF-filled unit lists, slot counts 0/negative/1/3/8,
already-present ids, filled and partial slot lists, and 16-bit id truncation.
Negative controls mutate the unite-id bit field, the secondary-id shift, the
visible-entry bound and the selected-unit stride; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001d1728"

FUNC_ADDR = 0x001D1728
FUNC_SIZE = 868

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00010000
GLOBAL_ADDR = 0x00430000
GLOBAL_SIZE = 0x00010000
MANAGER_ADDR = 0x00600000
MANAGER_SIZE = 0x00020000
PARTY_ADDR = 0x00630000
PARTY_SIZE = 0x00010000
RECORD_ADDR = 0x00640000
RECORD_SIZE = 0x00020000
SAVE_ADDR = 0x00660000
SAVE_SIZE = 0x00020000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
RECORD_STRIDE = 0x604
RECORD_COUNT = 8

STUB_2A8A08 = 0x002A8A08
STUB_2A8A1C = 0x002A8A1C
STUB_2A89E4 = 0x002A89E4
STUB_2B0824 = 0x002B0824
STUB_269E28 = 0x00269E28
STUB_2626F0 = 0x002626F0
STUB_29DF14 = 0x0029DF14
STUB_29C7C8 = 0x0029C7C8
STUB_29B3CC = 0x0029B3CC
STUB_29CB94 = 0x0029CB94
STUB_29D080 = 0x0029D080
STUB_29C950 = 0x0029C950

STUB_NAMES = {
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_2A8A1C: "camp_func_002a8a1c",
    STUB_2A89E4: "camp_func_002a89e4",
    STUB_2B0824: "camp_func_002b0824",
    STUB_269E28: "camp_func_00269e28",
    STUB_2626F0: "camp_func_002626f0",
    STUB_29DF14: "camp_func_0029df14",
    STUB_29C7C8: "camp_func_0029c7c8",
    STUB_29B3CC: "Unite_Init",
    STUB_29CB94: "script_vm_func_0029cb94",
    STUB_29D080: "camp_func_0029d080",
    STUB_29C950: "script_vm_func_0029c950",
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

# Manager offsets used by the original listing.
OFF_SELECTED_UNITS = 0xB34
OFF_DESCRIPTOR = 0xB48
OFF_RESULT = 0xB50
OFF_PARTY = 0x115C
OFF_RECORD_ID = 0x46
OFF_RECORD_UNITS = 0x34


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def locate_candidate(obj_file: Path):
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if "001d1728" in name:
            return value
    raise RuntimeError(f"camp_func_001d1728 not found in {obj_file}: {sorted(funcs)}")


def relocate_candidate(obj_file: Path) -> bytes:
    code_raw, relocs = locate_candidate(obj_file)
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type != 28:  # R_ARM_CALL
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name == rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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


# --------------------------------------------------------------------- fixtures
def pattern(size: int, seed: int = 0x5B) -> bytes:
    return bytes(((i * 37 + seed) & 0xFF) for i in range(size))


def record_ids(case: dict) -> list[int]:
    return [rec["id"] for rec in case["records"]]


def build_manager(case: dict) -> bytes:
    page = bytearray(pattern(MANAGER_SIZE))
    struct.pack_into("<I", page, OFF_SELECTED_UNITS, case["sel_raw"][0] & 0xFFFFFFFF)
    struct.pack_into("<I", page, OFF_SELECTED_UNITS + 4, case["sel_raw"][1] & 0xFFFFFFFF)
    struct.pack_into("<Q", page, OFF_DESCRIPTOR, case["desc_init"] & 0xFFFFFFFFFFFFFFFF)
    struct.pack_into("<I", page, OFF_PARTY, PARTY_ADDR)
    return bytes(page)


def build_party(case: dict) -> bytes:
    return pattern(PARTY_SIZE, 0xA7)


def build_records(case: dict) -> bytes:
    page = bytearray(pattern(RECORD_SIZE, 0xC3))
    for index, rec in enumerate(case["records"]):
        base = index * RECORD_STRIDE
        struct.pack_into("<H", page, base + OFF_RECORD_ID, rec["id"] & 0xFFFF)
        for slot in range(8):
            struct.pack_into(
                "<H", page, base + OFF_RECORD_UNITS + slot * 2,
                rec["units"][slot] & 0xFFFF,
            )
        # Filler that must stay untouched by the function.
        struct.pack_into("<I", page, base + 0x30, 0xA5A50000 | index)
        page[base + 0x48] = 0xE0 | index
    return bytes(page)


def build_save(case: dict) -> bytes:
    page = bytearray(pattern(SAVE_SIZE, 0x6D))
    count = case["entry_count"]
    for index in range(count):
        page[0x90F0 + index] = index & 0xFF
    return bytes(page)


def build_globals(case: dict) -> bytes:
    page = bytearray(pattern(GLOBAL_SIZE, 0x11))
    struct.pack_into("<I", page, 0x0043DCF0 - GLOBAL_ADDR, MANAGER_ADDR)
    return bytes(page)


def build_low(case: dict) -> bytes:
    # Page zero is read when a record lookup misses; keep it deterministic.
    return pattern(LOW_SIZE, 0x29)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(MANAGER_ADDR, MANAGER_SIZE)
        self.uc.mem_map(PARTY_ADDR, PARTY_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
        self.uc.mem_map(SAVE_ADDR, SAVE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.unite_units: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ helpers
    def _reg(self, name: int) -> int:
        return self.uc.reg_read(name)

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self._reg(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _record_ptr(self, index: int) -> int:
        return RECORD_ADDR + index * RECORD_STRIDE

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # -------------------------------------------------------------------- stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = self._reg(arm.UC_ARM_REG_R0)
        r1 = self._reg(arm.UC_ARM_REG_R1)
        r2 = self._reg(arm.UC_ARM_REG_R2)
        r3 = self._reg(arm.UC_ARM_REG_R3)

        if address == STUB_2A8A08:
            uc.reg_write(arm.UC_ARM_REG_R0, SAVE_ADDR)
        elif address == STUB_2A8A1C:
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["entry_count"])
        elif address == STUB_2A89E4:
            entry = r0
            if entry & 0x80000000:
                entry -= 1 << 32
            self._log(address, entry)
            if 0 <= entry < RECORD_COUNT:
                uc.reg_write(arm.UC_ARM_REG_R0, self._record_ptr(entry))
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2B0824:
            self._log(address, r0)
            index = self.case["unit_map"].get(r0 & 0xFFFF)
            uc.reg_write(
                arm.UC_ARM_REG_R0, 0 if index is None else self._record_ptr(index)
            )
        elif address == STUB_269E28:
            self._log(address, r0)
            uc.mem_write(r0 + 0x178, struct.pack("<I", 0))
        elif address == STUB_2626F0:
            self._log(address, r0, r1, r2, r3)
            if not self.case["pair_accept"]:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
                return
            primary = self.case["primary_id"] & 0x7FFF
            secondary = self.case["secondary_id"] & 0x7FFF
            unite = self.case["unite_id"] & 0x7FFF
            word0 = (
                primary
                | (secondary << 15)
                | ((self.case.get("descriptor_kind", 0x1) & 0x3) << 30)
            )
            word1 = 0x80000001 | (unite << 2)
            uc.mem_write(r3, struct.pack("<II", word0, word1))
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_29DF14:
            self._log(address, r0, r1)
            unite = r0 & 0xFFFF
            page = bytearray(0x604)
            page[OFF_RECORD_ID] = unite & 0xFF
            page[OFF_RECORD_ID + 1] = (unite >> 8) & 0xFF
            for slot, value in enumerate(self.case["seed_slots"]):
                struct.pack_into("<H", page, OFF_RECORD_UNITS + slot * 2, value)
            for slot in range(8):
                page[0x4C + slot] = (unite + slot) & 0xFF
            uc.mem_write(r1, bytes(page))
        elif address == STUB_29C7C8:
            stack0 = self._stack_words(1)[0]
            self._log(address, r0, r1, r2, r3, stack0)
            first_id = self._read_u16(r1 + OFF_RECORD_ID)
            second_id = self._read_u16(r2 + OFF_RECORD_ID)
            fill = (first_id + second_id + r3) & 0xFF
            uc.mem_write(stack0 + 0x4C, bytes([fill]) * 0x40)
        elif address == STUB_29B3CC:
            count = r0
            self._log(address, r0, r1, r2, r3)
            self.unite_units = [
                struct.unpack("<H", self.uc.mem_read(r0 + i * 2, 2))[0]
                for i in range(max(0, r1))
            ]
        elif address == STUB_29CB94:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["slot_count"] & 0xFFFFFFFF)
        elif address == STUB_29D080:
            self._log(address, r0, r1, r2)
            count = r1
            if count & 0x80000000:
                count -= 1 << 32
            found = 0
            for index in range(max(0, count)):
                value = struct.unpack("<H", self.uc.mem_read(r0 + index * 2, 2))[0]
                if value == (r2 & 0xFFFF):
                    found = 1
                    break
            uc.reg_write(arm.UC_ARM_REG_R0, found)
        elif address == STUB_29C950:
            self._log(address, r0)
            uc.mem_write(r0 + 0x300, struct.pack("<I", 0xCAFE0000))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _read_u16(self, address: int) -> int:
        return struct.unpack("<H", self.uc.mem_read(address, 2))[0]

    # ---------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        out = []
        for name, args in log:
            normalised = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    normalised.append("<stack>")
                else:
                    normalised.append(arg)
            out.append((name, tuple(normalised)))
        return out

    @staticmethod
    def _expand_writes(writes) -> list:
        """Normalise store widths to little-endian bytes so a halfword store and
        two byte stores of the same value compare equal."""
        out = []
        for address, size, value in writes:
            for index in range(size):
                out.append((address + index, (value >> (8 * index)) & 0xFF))
        return out

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.unite_units = []
        self.writes = []
        self.case = case

        self.uc.mem_write(LOW_ADDR, build_low(case))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOBAL_ADDR, build_globals(case))
        self.uc.mem_write(MANAGER_ADDR, build_manager(case))
        self.uc.mem_write(PARTY_ADDR, build_party(case))
        self.uc.mem_write(RECORD_ADDR, build_records(case))
        self.uc.mem_write(SAVE_ADDR, build_save(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for register in (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2,
                         arm.UC_ARM_REG_R3, arm.UC_ARM_REG_R12):
            self.uc.reg_write(register, 0xDEADBEEF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        outside_writes = []
        for address, size, value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                outside_writes.append((address, size, value))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "unite_units": self.unite_units,
            "fixtures": {
                "low": bytes(self.uc.mem_read(LOW_ADDR, LOW_SIZE)),
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "manager": bytes(self.uc.mem_read(MANAGER_ADDR, MANAGER_SIZE)),
                "party": bytes(self.uc.mem_read(PARTY_ADDR, PARTY_SIZE)),
                "records": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
                "save": bytes(self.uc.mem_read(SAVE_ADDR, SAVE_SIZE)),
            },
            "outside_writes": self._expand_writes(outside_writes),
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
    if orig["unite_units"] != cand["unite_units"]:
        problems.append(
            "unite_units:\n    orig=" + repr(orig["unite_units"])
            + "\n    cand=" + repr(cand["unite_units"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["outside_writes"] != cand["outside_writes"]:
        problems.append(
            "outside_writes:\n    orig=" + repr(orig["outside_writes"])
            + "\n    cand=" + repr(cand["outside_writes"])
        )
    return problems


def make_records(ids, unit_lists) -> list[dict]:
    records = []
    for index in range(RECORD_COUNT):
        records.append(
            {
                "id": ids[index] if index < len(ids) else 0x7000 + index,
                "units": (
                    unit_lists[index]
                    if index < len(unit_lists)
                    else [0x100 + index * 8 + slot for slot in range(8)]
                ),
            }
        )
    return records


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "sel_raw": [0x0011, 0x0022],
        "unit_map": {0x0011: 0, 0x0022: 1},
        "pair_accept": True,
        "entry_count": 4,
        "primary_id": 0x0101,
        "secondary_id": 0x0102,
        "unite_id": 0x1234,
        "seed_slots": [0, 0, 0, 0, 0, 0, 0, 0],
        "slot_count": 4,
        "desc_init": 0x1122334455667788,
        "records": make_records(
            [0x0101, 0x0102, 0x0103, 0x0104],
            [
                [0x0011, 0x0012, 0, 0x0013, 0, 0, 0, 0],
                [0x0021, 0, 0x0022, 0, 0x0023, 0, 0, 0x0024],
            ],
        ),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Early exits and the pair-validation branch.
    cases.append(base_case("baseline"))
    cases.append(base_case("selected unit 0 null", unit_map={0x0022: 1}))
    cases.append(base_case("selected unit 1 null", unit_map={0x0011: 0}))
    cases.append(base_case("both selected units null", unit_map={}))
    cases.append(base_case("pair rejected", pair_accept=False))

    # Find-record loop: empty count, hit in each position, miss.
    cases.append(base_case("entry count 0", entry_count=0))
    cases.append(base_case("entry count 1 primary at 0", entry_count=1,
                           primary_id=0x0101, secondary_id=0x0102))
    for index in range(6):
        cases.append(
            base_case(
                f"find hits index {index}",
                entry_count=6,
                primary_id=0x0100 + index,
                secondary_id=0x0105,
            )
        )
    cases.append(base_case("primary miss, secondary hit", entry_count=4,
                           primary_id=0x7FFF, secondary_id=0x0103))
    cases.append(base_case("secondary miss, primary hit", entry_count=4,
                           primary_id=0x0104, secondary_id=0x7FFF))
    cases.append(base_case("both records miss", entry_count=4,
                           primary_id=0x7FFE, secondary_id=0x7FFF))

    # Descriptor field boundaries.
    for primary, secondary in (
        (0x0000, 0x0000),
        (0x7FFF, 0x7FFF),
        (0x7FFF, 0x0000),
        (0x0000, 0x7FFF),
        (0x4000, 0x0001),
    ):
        cases.append(
            base_case(
                f"ids 0x{primary:04x}/0x{secondary:04x}",
                entry_count=1,
                primary_id=primary,
                secondary_id=secondary,
            )
        )
    for unite in (0x0000, 0x7FFF, 0x0001, 0x4000, 0x1234, 0x7000):
        cases.append(base_case(f"unite id 0x{unite:04x}", unite_id=unite))

    # Unit-list shapes.
    cases.append(base_case("all units zero", records=make_records(
        [0x0101, 0x0102], [[0] * 8, [0] * 8])))
    cases.append(base_case("full unit lists", records=make_records(
        [0x0101, 0x0102],
        [[0x100 + i for i in range(8)], [0x200 + i for i in range(8)]])))
    cases.append(base_case("high-bit unit ids", records=make_records(
        [0x0101, 0x0102],
        [[0xFFFF, 0x8000, 0x7FFF, 0x0001, 0, 0, 0, 0],
         [0x8001, 0x8002, 0, 0, 0, 0, 0, 0]])))
    cases.append(base_case("sixteen units, eight visible",
                           records=make_records(
                               [0x0101, 0x0102],
                               [[0x100 + i for i in range(8)],
                                [0x200 + i for i in range(8)]]),
                           slot_count=8))
    cases.append(base_case("secondary-only units",
                           records=make_records(
                               [0x0101, 0x0102],
                               [[0] * 8, [0x200 + i for i in range(8)]]),
                           slot_count=8))

    # Slot count / slot-insertion branches.
    for slot_count in (0, -1, 1, 3, 8):
        cases.append(base_case(f"slot count {slot_count}", slot_count=slot_count))
    cases.append(base_case("seed slots full", seed_slots=[0x41, 0x42, 0x43, 0x44,
                                                          0, 0, 0, 0]))
    cases.append(base_case("seed slot already holds unit",
                           seed_slots=[0x11, 0x12, 0, 0, 0, 0, 0, 0]))
    cases.append(base_case("seed slot partial hole",
                           seed_slots=[0xAA, 0, 0xBB, 0xCC, 0, 0, 0, 0],
                           slot_count=4))

    # 16-bit truncation of the selected unit fields.
    cases.append(base_case("selected raw high halfwords",
                           sel_raw=[0xFFFF0011, 0xABCD0022]))
    cases.append(base_case("selected id with 0x8000 bit",
                           sel_raw=[0x00008011, 0x00008022],
                           unit_map={0x8011: 0, 0x8022: 1}))

    # Descriptor kind bits must not affect the id extraction.
    for kind in (0, 1, 2, 3):
        cases.append(base_case(f"descriptor kind {kind}",
                               descriptor_kind=kind))

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
    print("Testing camp_func_001d1728 (0x001d1728)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutations = (
        ("unite_id_shift", "(descriptor >> 34) & kCampUniteIdMask",
         "(descriptor >> 32) & kCampUniteIdMask"),
        ("secondary_shift", "(pair >> 15) & kCampUniteIdMask",
         "(pair >> 14) & kCampUniteIdMask"),
        ("visible_bound", "constexpr u32 kCampVisibleUnitCount = 8;",
         "constexpr u32 kCampVisibleUnitCount = 16;"),
        ("selected_stride", "kCampSelectedUnits + i * 4",
         "kCampSelectedUnits + i * 2"),
        ("membership_skip", "if (unit == 0) {\n            continue;\n        }",
         "if (unit != 0xFFFF) {\n            continue;\n        }"),
    )
    for name, old, new in mutations:
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
