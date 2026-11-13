#!/usr/bin/env python3
"""Differential test for script_vm_func_001f8d04 (0x001F8D04) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the script_vm_func_001f8d04
body, resolves its direct calls to deterministic stubs placed at the original
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: every helper name with r0..r3 (and, for the random
    draw, both the requested bound and the value handed back);
  * the whole owner/record/camp/out fixture pages after the run, i.e. the
    caller's ids/flags/count buffers plus every byte of the input records;
  * any emulated write outside the private stack and the output page.

Coverage: both record resolutions (primary lookup / TBB table-0x21 fallback),
count pairs with min < max, min == max, min > max, zero targets and the
0x002C0BCC draw at both ends of its range; all three item slots with
id == 0, chance == 0, mode != 0, chance boundary accept/reject, chance 255 and
the early "target reached inside the slot loop" return; the camp scan band on
both inclusive boundaries and both reject sides, keys matching each of the four
accepted bytes and a non-matching key, null camp rows, zero matches, a single
candidate (draw bound 0) and many candidates; the second-resolution fallback;
null ids and/or count outputs; and signed/unsigned record-id boundaries.
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
OUT_DIR = ROOT / "build/test_leaf_001f8d04"

FUNC_ADDR = 0x001F8D04
FUNC_SIZE = 796

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x001B0000  # covers the body and every stub below 0x003A0000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00020000  # holds the 0x00433158 owner slot
RECORD_ADDR = 0x00700000
RECORD_SIZE = 0x00010000
CAMP_ADDR = 0x00710000
CAMP_SIZE = 0x00010000
OUT_ADDR = 0x00720000
OUT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

OWNER_SLOT = 0x00433158
OWNER_VALUE = 0x00433200

IDS_OFFSET = 0x0000
FLAGS_OFFSET = 0x0400
COUNT_OFFSET = 0x0500

CAMP_FIRST = 0x3B7
CAMP_LAST = 0x47E
CAMP_STRIDE = 0x40
CAMP_ROWS = CAMP_LAST - CAMP_FIRST + 1  # 200 rows of the scanned window

RECORD_STRIDE = 0x40
RERECORD_OFFSET = 0x400

STUB_LOOKUP = 0x00389E54
STUB_TBB_SUB = 0x002C0EC4
STUB_TBB_PAYLOAD = 0x002C0E9C
STUB_TBB_ROWS = 0x002C0E4C
STUB_RANDOM = 0x002C0BCC
STUB_DIVMOD = 0x002C615C
STUB_ADD_ITEM = 0x00295CBC
STUB_CAMP_ROW = 0x00256A50
STUB_FLAG_TEST = 0x0025B920
STUB_TABLE_ENTRY = 0x002C583C

STUB_NAMES = {
    STUB_LOOKUP: "script_vm_func_00389e54",
    STUB_TBB_SUB: "Tbb_GetGlobalSubTable",
    STUB_TBB_PAYLOAD: "Tbb_GetPayloadData",
    STUB_TBB_ROWS: "Tbb_GetRowCount",
    STUB_RANDOM: "engine_func_002c0bcc",
    STUB_DIVMOD: "ui_func_002c615c",
    STUB_ADD_ITEM: "script_vm_func_00295cbc",
    STUB_CAMP_ROW: "camp_func_00256a50",
    STUB_FLAG_TEST: "script_vm_func_0025b920",
    STUB_TABLE_ENTRY: "engine_func_002c583c",
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
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001f8d04" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_001f8d04 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            if rel.symbol_name in STUB_NAMES.values():
                for address, name in STUB_NAMES.items():
                    if name == rel.symbol_name:
                        target = address
                        break
            else:
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
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
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
def build_record(
    count_min: int = 0,
    count_max: int = 0,
    scan_min: int = 0,
    scan_max: int = 0,
    slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
    accept=(0, 0, 0, 0),
) -> bytes:
    """One 24-byte record as read at 0x001F8D04."""
    record = bytearray(24)
    record[0x00:0x04] = b"\xA5\xA5\xA5\xA5"
    record[0x04] = count_min & 0xFF
    record[0x05] = count_max & 0xFF
    record[0x06] = scan_min & 0xFF
    record[0x07] = scan_max & 0xFF
    for index, (item, mode, chance) in enumerate(slots):
        base = 0x08 + index * 4
        struct.pack_into("<H", record, base, item & 0xFFFF)
        record[base + 2] = mode & 0xFF
        record[base + 3] = chance & 0xFF
    for index, key in enumerate(accept):
        record[0x14 + index] = key & 0xFF
    return bytes(record)


def build_records(case: dict) -> bytes:
    """Record page: primary lookup slot, fallback payload area, second slot."""
    page = bytearray(RECORD_SIZE)
    for offset in (0x100, 0x400, 0x800):
        page[offset : offset + 24] = build_record(
            count_min=0x11, count_max=0x22, scan_min=0x33, scan_max=0x44,
            slots=((0x5A5A, 1, 0), (0x6B6B, 0, 0), (0x7C7C, 0, 0)),
            accept=(0x91, 0x92, 0x93, 0x94),
        )
    primary = case.get("record")
    if primary is not None:
        page[0x100 : 0x100 + 24] = primary
    second = case.get("record_second", primary)
    if second is not None:
        page[RERECORD_OFFSET : RERECORD_OFFSET + 24] = second
    payload = case.get("fallback_record")
    if payload is not None:
        offset = case.get("fallback_payload_offset", 0)
        target = 0x800 + offset + 24 * (case["id"] & 0xFFFFFFFF)
        if not 0 <= target <= RECORD_SIZE - 24:
            raise RuntimeError(f"fallback record out of page: 0x{target:x}")
        page[target : target + 24] = payload
    return bytes(page)


def build_camp(case: dict) -> bytes:
    page = bytearray(CAMP_SIZE)
    rows = case.get("camp_rows", {})
    nulls = set(case.get("camp_null", ()))
    for index in range(CAMP_ROWS):
        base = index * CAMP_STRIDE
        # Default row: a band/key pair that no case selects by accident.
        value, band, key = 0xEE00 | index, 0xEE, 0xEE
        entry = rows.get(CAMP_FIRST + index)
        if entry is not None:
            value, band, key = entry
        if (CAMP_FIRST + index) in nulls:
            continue
        struct.pack_into("<H", page, base + 0x20, value & 0xFFFF)
        page[base + 0x24] = band & 0xFF
        page[base + 0x25] = key & 0xFF
        page[base + 0x00] = 0x5A
        page[base + 0x1F] = 0xA5
    return bytes(page)


def build_scratch(case: dict) -> tuple[bytes, int, int, int]:
    page = bytearray(OUT_SIZE)
    page[IDS_OFFSET : IDS_OFFSET + 0x400] = b"\xCD" * 0x400
    page[FLAGS_OFFSET : FLAGS_OFFSET + 0x100] = b"\xCE" * 0x100
    page[COUNT_OFFSET : COUNT_OFFSET + 4] = struct.pack("<I", case.get("count_seed", 0xDEADBEEF))
    ids = 0 if case.get("ids_null") else OUT_ADDR + IDS_OFFSET
    flags = OUT_ADDR + FLAGS_OFFSET
    count = 0 if case.get("count_null") else OUT_ADDR + COUNT_OFFSET
    return bytes(page), ids, flags, count


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    struct.pack_into("<I", page, OWNER_SLOT - DATA_ADDR, case.get("owner", OWNER_VALUE))
    return bytes(page)


class F18D04Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
        self.uc.mem_map(CAMP_ADDR, CAMP_SIZE)
        self.uc.mem_map(OUT_ADDR, OUT_SIZE)
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
        self.lookup_index = 0
        self.draw_index = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _next_draw(self, bound: int) -> int:
        draws = self.case.get("draws", ())
        if self.draw_index < len(draws):
            value = draws[self.draw_index]
        else:
            value = 0
        self.draw_index += 1
        # 0x002C0BCC returns a value in [0, max] (inclusive); see
        # src/engine/asd_runtime.cpp.  Keep the call in range so a diverging
        # argument is reported by the call log instead of faulting.
        if not 0 <= value <= bound:
            value = max(0, bound)
        return value

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_LOOKUP:
            self._log(address, r0, r1)
            if self.lookup_index == 0:
                record = self.case.get("record")
            else:
                record = self.case.get("record_second", self.case.get("record"))
            self.lookup_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0 if record is None else RECORD_ADDR + (
                0x100 if self.lookup_index == 1 else RERECORD_OFFSET
            ))
        elif address == STUB_TBB_SUB:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("tbb_table", 0x00A50000))
        elif address == STUB_TBB_PAYLOAD:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self.case.get("tbb_payload", RECORD_ADDR + 0x800),
            )
        elif address == STUB_TBB_ROWS:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("tbb_rows", 0))
        elif address == STUB_RANDOM:
            value = self._next_draw(r0)
            self._log(address, r0, value)
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        elif address == STUB_DIVMOD:
            denominator = r1
            if denominator == 0:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
                uc.reg_write(arm.UC_ARM_REG_R1, r0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, r0 // denominator)
                uc.reg_write(arm.UC_ARM_REG_R1, r0 % denominator)
            self._log(address, r0, r1)
        elif address == STUB_ADD_ITEM:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_CAMP_ROW:
            self._log(address, r0)
            if r0 in set(self.case.get("camp_null", ())):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            elif CAMP_FIRST <= r0 <= CAMP_LAST:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    CAMP_ADDR + (r0 - CAMP_FIRST) * CAMP_STRIDE,
                )
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_FLAG_TEST:
            self._log(address, r0)
            table = self.case.get("flag_bits", {})
            uc.reg_write(arm.UC_ARM_REG_R0, table.get(r0, r0 & 1))
        elif address == STUB_TABLE_ENTRY:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x00C50000)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.lookup_index = 0
        self.draw_index = 0
        self.case = case

        scratch, ids, flags, count = build_scratch(case)
        data = build_data(case)
        records = build_records(case)
        camp = build_camp(case)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, data)
        self.uc.mem_write(RECORD_ADDR, records)
        self.uc.mem_write(CAMP_ADDR, camp)
        self.uc.mem_write(OUT_ADDR, scratch)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["id"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, ids)
        self.uc.reg_write(arm.UC_ARM_REG_R2, flags)
        self.uc.reg_write(arm.UC_ARM_REG_R3, count)
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
            in_out = OUT_ADDR <= address < OUT_ADDR + OUT_SIZE
            if not (in_stack or in_out):
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
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "records": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
                "camp": bytes(self.uc.mem_read(CAMP_ADDR, CAMP_SIZE)),
                "out": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        first = None
        for index, (left, right) in enumerate(
            zip(orig["call_log"], cand["call_log"])
        ):
            if left != right:
                first = (index, left, right)
                break
        detail = f"lengths {len(orig['call_log'])}/{len(cand['call_log'])}"
        if first is not None:
            detail += f"; first mismatch #{first[0]}: {first[1]!r} != {first[2]!r}"
        problems.append("call_log: " + detail)
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# -------------------------------------------------------------------- test cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "id": 0x1234,
        "owner": OWNER_VALUE,
        "record": build_record(
            count_min=2,
            count_max=6,
            scan_min=10,
            scan_max=20,
            slots=((0x1111, 0, 50), (0x2222, 0, 50), (0, 0, 0)),
            accept=(0x30, 0x31, 0x32, 0x33),
        ),
        "tbb_rows": 0,
        "draws": (3, 4, 9, 2, 0, 1, 0, 0, 0, 0),
        "camp_rows": {
            0x3B7: (0x0100, 10, 0x30),
            0x3B8: (0x0101, 20, 0x33),
            0x3B9: (0x0102, 15, 0x31),
            0x3BA: (0x0103, 15, 0x99),
            0x3BB: (0x0104, 25, 0x30),
            0x3BC: (0x0105, 9, 0x30),
        },
        "camp_null": (0x400,),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- primary path: two slot adds, three matching camp rows, three picks
    cases.append(base_case("baseline slots + scan picks"))
    cases.append(base_case("null ids buffer", ids_null=True))
    cases.append(base_case("null count buffer", count_null=True))
    cases.append(base_case("null ids and count buffers", ids_null=True,
                           count_null=True))
    cases.append(base_case("owner pointer differs", owner=0x00433240))

    # --- count pair orderings and the early abort
    cases.append(base_case(
        "equal count pair uses the fixed 50 roll",
        record=build_record(count_min=3, count_max=3, scan_min=0, scan_max=0,
                            slots=((0x2001, 0, 1), (0, 0, 0), (0, 0, 0)),
                            accept=(5, 0, 0, 0)),
        draws=(0, 0, 0, 0, 0, 0),
        camp_rows={0x3B7: (0x2002, 0, 5)},
    ))
    cases.append(base_case(
        "swapped count pair (min > max)",
        record=build_record(count_min=8, count_max=3, scan_min=10, scan_max=20,
                            slots=((0x2101, 0, 100), (0, 0, 0), (0, 0, 0)),
                            accept=(0x30, 0, 0, 0)),
        draws=(0, 0, 0, 0, 0),
        camp_rows={0x3B7: (0x2102, 15, 0x30)},
    ))
    cases.append(base_case(
        "zero count pair aborts",
        record=build_record(count_min=0, count_max=0),
        draws=(0,),
    ))
    cases.append(base_case(
        "swapped pair draws a zero target and aborts",
        record=build_record(count_min=1, count_max=0),
        draws=(0,),
    ))
    cases.append(base_case(
        "draw at the top of the span",
        record=build_record(count_min=0, count_max=2, scan_min=10, scan_max=20,
                            slots=((0x2201, 0, 100), (0, 0, 0), (0, 0, 0)),
                            accept=(0x30, 0, 0, 0)),
        draws=(2, 0, 0),
    ))
    cases.append(base_case(
        "item chance 100 accepts the top roll, chance 99 rejects it",
        record=build_record(count_min=2, count_max=2, scan_min=10, scan_max=20,
                            slots=((0x3501, 0, 100), (0x3502, 0, 99),
                                   (0, 0, 0)),
                            accept=(0x30, 0, 0, 0)),
        draws=(99, 99, 0, 0),
    ))
    cases.append(base_case(
        "percentage rounding 1 of 3",
        record=build_record(count_min=0, count_max=3, scan_min=10, scan_max=20,
                            slots=((0x2301, 0, 100), (0, 0, 0), (0, 0, 0)),
                            accept=(0x30, 0, 0, 0)),
        draws=(1, 0, 0),
    ))

    # --- slot gates
    cases.append(base_case(
        "slot gates: chance boundary, chance 255, mode and id rejects",
        record=build_record(count_min=9, count_max=9, scan_min=10, scan_max=20,
                            slots=((0x3101, 0, 1), (0x3102, 0, 1),
                                   (0x3103, 0, 255)),
                            accept=(0x30, 0, 0, 0)),
        draws=(0, 1, 99, 0, 0, 0, 0, 0, 0),
    ))
    cases.append(base_case(
        "slot mode != 0 and chance 0 are skipped",
        record=build_record(count_min=1, count_max=1, scan_min=10, scan_max=20,
                            slots=((0x3201, 1, 255), (0x3202, 0, 0),
                                   (0, 0, 255)),
                            accept=(0x30, 0, 0, 0)),
        draws=(0, 0),
    ))
    cases.append(base_case(
        "target reached inside the slot loop",
        record=build_record(count_min=1, count_max=1, scan_min=10, scan_max=20,
                            slots=((0x3301, 0, 100), (0x3302, 0, 100),
                                   (0x3303, 0, 100)),
                            accept=(0x30, 0, 0, 0)),
        draws=(0, 0),
    ))
    cases.append(base_case(
        "target reached on the second slot",
        record=build_record(count_min=2, count_max=2, scan_min=10, scan_max=20,
                            slots=((0x3401, 0, 0), (0x3402, 0, 100),
                                   (0x3403, 0, 100)),
                            accept=(0x30, 0, 0, 0)),
        draws=(0, 0),
    ))

    # --- camp scan filters
    cases.append(base_case(
        "scan band is swapped (min > max)",
        record=build_record(count_min=1, count_max=2, scan_min=20, scan_max=10,
                            slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                            accept=(0x30, 0x31, 0x32, 0x33)),
        draws=(0, 0, 0, 0),
    ))
    cases.append(base_case(
        "each accepted key matches",
        record=build_record(count_min=4, count_max=4, scan_min=10, scan_max=20,
                            slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                            accept=(0x30, 0x31, 0x32, 0x33)),
        draws=(0, 3, 2, 1, 0),
        camp_rows={
            0x3B7: (0x0A00, 10, 0x30),
            0x3B8: (0x0A01, 20, 0x31),
            0x3B9: (0x0A02, 15, 0x32),
            0x3BA: (0x0A03, 15, 0x33),
            0x3BB: (0x0A04, 15, 0x34),
        },
    ))
    cases.append(base_case(
        "single scan candidate (draw bound 0)",
        record=build_record(count_min=3, count_max=3, scan_min=0, scan_max=0,
                            slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                            accept=(0x77, 0, 0, 0)),
        draws=(0, 0, 0, 0),
        camp_rows={0x47E: (0xF7F7, 0, 0x77)},
        camp_null=(0x3B7, 0x3B8, 0x3B9),
    ))
    cases.append(base_case(
        "no scan candidate aborts",
        record=build_record(count_min=1, count_max=1, scan_min=0, scan_max=0,
                            slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                            accept=(0x77, 0, 0, 0)),
        draws=(0,),
        camp_rows={},
    ))
    cases.append(base_case(
        "scan window boundaries only",
        record=build_record(count_min=2, count_max=2, scan_min=0x40, scan_max=0x40,
                            slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                            accept=(0x42, 0, 0, 0)),
        draws=(0, 0),
        camp_rows={
            0x3B6: (0x1111, 0x40, 0x42),
            0x47F: (0x2222, 0x40, 0x42),
            0x3B7: (0x3333, 0x40, 0x42),
            0x47E: (0x4444, 0x40, 0x42),
        },
    ))
    cases.append(base_case(
        "signed camp values are sign-extended into the output",
        record=build_record(count_min=2, count_max=2, scan_min=0, scan_max=0,
                            slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                            accept=(1, 0, 0, 0)),
        draws=(0, 1, 0),
        camp_rows={0x3B7: (0x8001, 0, 1), 0x3B8: (0xFFFF, 0, 1)},
        flag_bits={-32767 & 0xFFFFFFFF: 1, 0xFFFFFFFF: 0},
    ))

    # --- fallback table (lookup returns null)
    cases.append(base_case(
        "primary lookup null, table-0x21 fallback",
        id=5,
        record=None,
        fallback_payload_offset=0,
        tbb_rows=8,
        fallback_record=build_record(
            count_min=1, count_max=1, scan_min=0, scan_max=0,
            slots=((0x3001, 1, 0), (0, 0, 0), (0x3002, 0, 0)),
            accept=(1, 0, 0, 0)),
        draws=(0, 0),
        camp_rows={0x3B7: (0x3003, 0, 1)},
    ))
    cases.append(base_case(
        "primary lookup null, fallback id out of range",
        id=5,
        record=None,
        tbb_rows=5,
        draws=(0,),
    ))
    cases.append(base_case(
        "primary lookup null, null payload, id 0",
        id=0,
        record=None,
        tbb_payload=0,
        tbb_rows=5,
        draws=(0,),
    ))
    cases.append(base_case(
        "primary lookup null, negative id",
        id=0xFFFFFFFF,
        record=None,
        tbb_rows=8,
        draws=(0,),
    ))
    cases.append(base_case(
        "second lookup null, fallback resolves the scan record",
        record=build_record(count_min=1, count_max=1, scan_min=0, scan_max=0,
                            slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
                            accept=(1, 0, 0, 0)),
        record_second=None,
        id=6,
        tbb_rows=8,
        fallback_record=build_record(
            count_min=0, count_max=0, scan_min=0, scan_max=0,
            slots=((0, 0, 0), (0, 0, 0), (0, 0, 0)),
            accept=(1, 0, 0, 0)),
        draws=(0, 0),
        camp_rows={0x3B7: (0x4001, 0, 1)},
    ))

    # --- id boundaries that still resolve the primary record
    for ident in (0x0000, 0x0001, 0x7FFF, 0x8000, 0xFFFF, 0x7FFFFFFF):
        cases.append(base_case(f"id 0x{ident:08x}", id=ident))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = F18D04Runner().run(orig_code, case)
        cand = F18D04Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
              f"ret={orig['ret']})")
    return passed


def main() -> None:
    print("Testing script_vm_func_001f8d04 (0x001F8D04)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("scan_first", "constexpr u32 kCampScanFirst = 0x3B7;",
         "constexpr u32 kCampScanFirst = 0x3B8;"),
        ("scan_last", "constexpr u32 kCampScanLast = 0x47E;",
         "constexpr u32 kCampScanLast = 0x47D;"),
        ("equal_roll", "constexpr u32 kEqualCountRoll = 50;",
         "constexpr u32 kEqualCountRoll = 49;"),
        ("item_roll_range", "constexpr u32 kItemRollRange = 99;",
         "constexpr u32 kItemRollRange = 98;"),
        ("fallback_slot", "constexpr u32 kFallbackSlotId = 0x21;",
         "constexpr u32 kFallbackSlotId = 0x20;"),
        ("chance_boundary",
         "if (static_cast<u16>(roll + 1u) > candidate.chance) {",
         "if (static_cast<u16>(roll + 1u) >= candidate.chance) {"),
        ("flag_polarity", "        if (flag_test(static_cast<s32>(picked)) == 0) {\n"
         "            flags[produced] = 1;\n"
         "        } else {\n"
         "            flags[produced] = 0;\n"
         "        }",
         "        if (flag_test(static_cast<s32>(picked)) == 0) {\n"
         "            flags[produced] = 0;\n"
         "        } else {\n"
         "            flags[produced] = 1;\n"
         "        }"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = F18D04Runner().run(orig_code, case)
            bad = F18D04Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
