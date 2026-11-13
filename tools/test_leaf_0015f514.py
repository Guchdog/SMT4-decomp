#!/usr/bin/env python3
"""Differential test for func_0015f514 (0x0015f514) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_0015f514 body,
resolves its single direct call (0x002BB5B4) to a deterministic stub at the
original target address, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return value (this function really returns 0 or 1), continuation PC, final SP
    and the callee-saved r4-r11;
  * the ordered call log (the lone 0x002BB5B4 call; it takes no arguments, so
    only the target is compared -- the original happens to leave base/index in
    r0/r1 and those are not part of its contract);
  * the full 64 KiB base-object page (the +0x131A selector and the +0x1000
    table), the 16 KiB fixture region holding the record / descriptor / payload
    pages, so the u32 stores at +0xAC/+0xB0/+0xA4/+0x00, the u16 stores at
    +0xB4/+0xB6../+0xBC/+0xBE, the read-modify-writes of +0xBC and the six-byte
    payload copy are all pinned;
  * every emulated write outside the private stack, bucketed by fixture page.

Coverage: the global-enable helper returning 0 / 1 / -1 / 0x7FFFFFFF; start
addresses on both sides of [0x14000000, 0x1C000000); computed end addresses on
both sides of the exclusive low bound and the inclusive high bound, including
the 32-bit wrap; all sixteen flags[3:2] x flags[1:0] combinations; the
0x92492493-scaled family for stride 0, 1, 6, 7, 13, 14, small and huge values
(both positive and negative numerators) with end addresses aligned exactly on
0x1C000000 and one past it; selector values 0/1/2/3/0xFFFF; index 0/1/0xFF/
0x1000; flags words whose upper half must be ignored; record flag bytes
0x00/0x01/0x02/0x03/0x7F/0x80/0xFF; record values 0/0x1234/0xFFFF; payload
absent and present with zero and non-zero leading bytes; payload present while
flags[3:2] != 2 (no copy); and two aliasing fixtures where the descriptor is
placed at record-0xAE so the six-byte copy overwrites the record's own +0x08
payload word and the +0xBE store overwrites the record's +0x10 flag byte,
proving the second +0x08 read and the late +0x10 read.

Negative controls mutate the two address limits, the span, the control flags,
the selector offset, the channel stride, the slot pointer offset, the payload
halfword count, the 0x92492493 reciprocal, the scaled unit shift, the bit-1
mask, the +0xA4 clear value and the +0xBE value store; each mutant must be
detected.
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
OUT_DIR = ROOT / "build/test_leaf_0015f514"

FUNC_ADDR = 0x0015F514
FUNC_SIZE = 448

# Free code address; the body is position independent apart from its one call.
CAND_ADDR = 0x00200000

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000          # original, candidate and the stub target
STUB_2BB5B4 = 0x002BB5B4

BASE_PAGE_ADDR = 0x004E0000     # base object at 0x004E6F64 lives here
BASE_PAGE_SIZE = 0x00010000
BASE_ADDR = 0x004E6F64

REGION_ADDR = 0x00720000        # record / descriptor / payload fixtures
REGION_SIZE = 0x00004000
DESC_ADDR = REGION_ADDR + 0x0000
REC_ADDR = REGION_ADDR + 0x1000
DESC2_ADDR = REGION_ADDR + 0x2000
SRC_ADDR = REGION_ADDR + 0x3000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

BASE_OFF = BASE_ADDR - BASE_PAGE_ADDR
SELECTOR_OFF = BASE_OFF + 0x131A
TABLE_OFF = BASE_OFF + 0x1000
CHANNEL_STRIDE = 0x60
SLOT_POINTER_OFF = 0xB0

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


def magic_units(stride: int) -> int:
    """Reference model of 0x0015F5AC..0x0015F5C4 (used to build boundaries)."""
    numerator = (stride + 0x0D) & 0xFFFFFFFF
    signed_numerator = numerator - (1 << 32) if numerator & 0x80000000 else numerator
    product = (signed_numerator * -1840700269) & 0xFFFFFFFFFFFFFFFF
    accumulator = (product + ((numerator << 32) & 0xFFFFFFFFFFFFFFFF)) & 0xFFFFFFFFFFFFFFFF
    high = (accumulator >> 32) & 0xFFFFFFFF
    signed_high = high - (1 << 32) if high & 0x80000000 else high
    units = (signed_high >> 3) + (1 if signed_high < 0 else 0)
    return units & 0xFFFFFFFF


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "func_0015f514" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"func_0015f514 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if rel.symbol_name != "func_002bb5b4":
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = CAND_ADDR + rel.offset + 8
        displacement = (STUB_2BB5B4 - pc) >> 2
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
def pattern(size: int, salt: int) -> bytes:
    return bytes(((index * 7 + salt) & 0xFF) for index in range(size))


def build_base_page(case: dict) -> bytes:
    page = bytearray(pattern(BASE_PAGE_SIZE, 0x13))
    struct.pack_into("<H", page, SELECTOR_OFF, case["selector"] & 0xFFFF)
    selector = case["selector"] & 1
    slot = TABLE_OFF + selector * CHANNEL_STRIDE + (case["index"] & 0xFFFFFFFF) * 4
    struct.pack_into("<I", page, slot + SLOT_POINTER_OFF, case["descriptor"] & 0xFFFFFFFF)
    # Also point the other selector at the second descriptor page so a wrong
    # selector read is caught by the written memory rather than by a fault.
    other = TABLE_OFF + (1 - selector) * CHANNEL_STRIDE + (case["index"] & 0xFFFFFFFF) * 4
    struct.pack_into("<I", page, other + SLOT_POINTER_OFF, (case["descriptor"] + 0x1000) & 0xFFFFFFFF)
    return bytes(page)


def build_region(case: dict) -> bytes:
    region = bytearray(pattern(REGION_SIZE, 0x27))
    # Descriptor control word: bit 0 stays clear by default so the mutant that
    # changes 0x40200000 to 0x40200001 is observable.
    struct.pack_into("<I", region, DESC_ADDR - REGION_ADDR, case["control"] & 0xFFFFFFFF)
    struct.pack_into("<I", region, DESC2_ADDR - REGION_ADDR,
                     (case["control"] ^ 0x80000000) & 0xFFFFFFFF)
    record = bytearray(pattern(0x1000, 0x31))
    struct.pack_into("<I", record, 0x00, case["address"] & 0xFFFFFFFF)
    struct.pack_into("<I", record, 0x04, case["stride"] & 0xFFFFFFFF)
    struct.pack_into("<I", record, 0x08, case["payload"] & 0xFFFFFFFF)
    record[0x10] = case["flag"] & 0xFF
    struct.pack_into("<H", record, 0x12, case["value"] & 0xFFFF)
    region[0x1000:0x2000] = record

    source = bytearray(pattern(0x1000, 0x43))
    source[0:6] = case["src"]
    region[0x3000:0x4000] = source
    return bytes(region)


class Runner:
    """One Unicorn machine with a deterministic 0x002BB5B4 stub."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(BASE_PAGE_ADDR, BASE_PAGE_SIZE)
        self.uc.mem_map(REGION_ADDR, REGION_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(STUB_2BB5B4, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub, begin=STUB_2BB5B4, end=STUB_2BB5B4
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        if address != STUB_2BB5B4:
            raise AssertionError(f"unexpected stub address 0x{address:08x}")
        self.call_log.append(("func_002bb5b4", ()))
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["global_flag"] & 0xFFFFFFFF)

    def run(self, code: bytes, case: dict, addr: int = FUNC_ADDR) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(addr, code)
        self.uc.mem_write(BASE_PAGE_ADDR, build_base_page(case))
        self.uc.mem_write(REGION_ADDR, build_region(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, BASE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["index"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, REC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["flags"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(addr, TRAP_ADDR, timeout=5_000_000, count=1_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        regions = sorted(
            {
                self._region(address)
                for address, _size in self.writes
                if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            }
        )

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "write_regions": regions,
            "fixtures": {
                "base": bytes(self.uc.mem_read(BASE_PAGE_ADDR, BASE_PAGE_SIZE)),
                "region": bytes(self.uc.mem_read(REGION_ADDR, REGION_SIZE)),
            },
        }

    @staticmethod
    def _region(address: int) -> str:
        for name, base, size in (
            ("base", BASE_PAGE_ADDR, BASE_PAGE_SIZE),
            ("desc", DESC_ADDR, 0x1000),
            ("record", REC_ADDR, 0x1000),
            ("desc2", DESC2_ADDR, 0x1000),
            ("payload", SRC_ADDR, 0x1000),
        ):
            if base <= address < base + size:
                return name
        return "unmapped"


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "write_regions", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            for index, (left, right) in enumerate(zip(value, cand["fixtures"][key])):
                if left != right:
                    problems.append(
                        f"fixture {key} first differs at +0x{index:04x}: "
                        f"orig=0x{left:02x} cand=0x{right:02x}"
                    )
                    break
            else:
                problems.append(f"fixture {key} length differs")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "address": 0x15000000,
        "stride": 0x1000,
        "payload": 0,
        "flag": 0x01,
        "value": 0xBEEF,
        "selector": 0,
        "index": 0,
        "descriptor": DESC_ADDR,
        "control": 0x00000000,
        "flags": 0x0,
        "global_flag": 1,
        "src": bytes((0x11, 0x22, 0x33, 0x44, 0x55, 0x66)),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- global enable helper (0x002BB5B4)
    for flag in (0, 1, -1, 0x7FFFFFFF):
        cases.append(base_case(f"global flag 0x{flag & 0xFFFFFFFF:08x}",
                               global_flag=flag))

    # --- start-address window [0x14000000, 0x1C000000)
    for address in (0x14000000, 0x14000001, 0x13FFFFFF, 0x1BFFFFFF,
                    0x1C000000, 0x1C000001, 0x00000000, 0xFFFFFFFF):
        cases.append(base_case(f"address 0x{address:08x}", address=address,
                               flags=0x3))
    cases.append(base_case("address wraps below the window",
                           address=0x13FFFFF0, stride=0x10000000, flags=0x3))

    # --- computed end address bounds (low exclusive, high inclusive)
    cases.append(base_case("end exactly at the exclusive low bound",
                           address=0x14000000, stride=0x10, flags=0x3))
    cases.append(base_case("end one above the low bound",
                           address=0x14000000, stride=0x1, flags=0x1))
    cases.append(base_case("end exactly at the inclusive high bound",
                           address=0x1BFFFFF0, stride=0x10, flags=0x1))
    cases.append(base_case("end one above the high bound",
                           address=0x1BFFFFF0, stride=0x11, flags=0x1))
    cases.append(base_case("end wraps past the high bound",
                           address=0x1BFFFFF0, stride=0x10, flags=0x5))
    cases.append(base_case("end wraps into the high bound",
                           address=0x1BFFFFF0, stride=0x80000008, flags=0x5))

    # --- every stride multiplier pinned against the high bound, so a wrong
    #     multiplier changes the success/failure outcome.
    for flags, multiplier in ((0x1, 1), (0x2, 2), (0x5, 2), (0x6, 4)):
        stride = 0x1000
        step = (stride * multiplier) & 0xFFFFFFFF
        address = (0x1C000000 - step) & 0xFFFFFFFF
        cases.append(base_case(
            f"step x{multiplier} lands on the high bound", address=address,
            stride=stride, flags=flags))
        cases.append(base_case(
            f"step x{multiplier} one past the high bound",
            address=(address + 1) & 0xFFFFFFFF, stride=stride, flags=flags))

    # --- every flags[3:2] x flags[1:0] combination
    for family in range(4):
        for count in range(4):
            cases.append(
                base_case(f"family {family} count {count}",
                          address=0x15000000, stride=0x1000,
                          flags=(family << 2) | count, payload=SRC_ADDR)
            )

    # --- 0x92492493 scaled family
    for stride in (0, 1, 6, 7, 12, 13, 14, 20, 0xFFFF, 0x100000):
        cases.append(base_case(f"scaled stride 0x{stride:x}", stride=stride,
                               flags=0x9, payload=SRC_ADDR))
    # (next: n = stride + 13 == 0x0E00000C, 4/7 scaling is exactly 0x08000000)
    cases.append(base_case("scaled stride lands on the high bound",
                           address=0x14000000, stride=0x0DFFFFFF, flags=0x9,
                           payload=SRC_ADDR))
    cases.append(base_case("scaled stride one past the high bound",
                           address=0x14000001, stride=0x0DFFFFFF, flags=0x9))
    for stride in (0x7FFFFFF3, 0x7FFFFFFF, 0x80000000, 0xFFFFFFF2,
                   0xFFFFFFF3, 0xFFFFFFFF):
        units = magic_units(stride)
        step = (units << 3) & 0xFFFFFFFF
        # Place the start so the scaled end lands on 0x1C000000, and one word
        # past it, for every numerator sign.
        target = 0x1C000000
        aligned = (target - step) & 0xFFFFFFFF
        cases.append(base_case(
            f"scaled stride 0x{stride:08x} aligned (units 0x{units:08x})",
            address=aligned, stride=stride, flags=0x9, payload=SRC_ADDR))
        cases.append(base_case(
            f"scaled stride 0x{stride:08x} one past (units 0x{units:08x})",
            address=(aligned + 1) & 0xFFFFFFFF, stride=stride, flags=0x9))

    # --- selector and index
    for selector in (0, 1, 2, 3, 0xFFFF):
        cases.append(base_case(f"selector 0x{selector:04x}", selector=selector,
                               payload=SRC_ADDR, flags=0x9))
    for index in (0, 1, 0xFF, 0x1000):
        cases.append(base_case(f"index 0x{index:x}", index=index,
                               payload=SRC_ADDR))

    # --- flags word truncation to 16 bits
    for flags in (0x00010001, 0xFFFF0009, 0x12345678, 0xFFFFFFFF, 0x00008009):
        cases.append(base_case(f"flags 0x{flags:08x}", flags=flags,
                               payload=SRC_ADDR))

    # --- record flag byte (signed load at +0x10, bit 0 only)
    for flag in (0x00, 0x01, 0x02, 0x03, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"record flag 0x{flag:02x}", flag=flag,
                               payload=SRC_ADDR, flags=0x9))

    # --- record value (+0x12)
    for value in (0x0000, 0x1234, 0xFFFF):
        cases.append(base_case(f"record value 0x{value:04x}", value=value))

    # --- payload presence
    cases.append(base_case("payload present, zero leading bytes",
                           payload=SRC_ADDR, flags=0x9,
                           src=bytes((0, 0, 0, 0, 0xAA, 0xBB))))
    cases.append(base_case("payload present, high leading bytes",
                           payload=SRC_ADDR, flags=0x9,
                           src=bytes((0x11, 0x22, 0x33, 0x44, 0x55, 0x66))))
    cases.append(base_case("payload absent, family 2 count 0",
                           payload=0, flags=0x8))
    cases.append(base_case("payload absent, family 2 count 2",
                           payload=0, flags=0xA))
    cases.append(base_case("payload present but family 1 (no copy)",
                           payload=SRC_ADDR, flags=0x5))
    cases.append(base_case("payload absent, family 3 (bit 0 untouched)",
                           payload=0, flags=0xD))

    # --- aliasing: descriptor at record-0xAE so +0xBE is record+0x10 and the
    #     payload copy lands on record+0x08.
    alias = REC_ADDR - 0xAE
    cases.append(base_case("alias, copy overwrites the payload word with zero",
                           descriptor=alias, payload=SRC_ADDR, flags=0x9,
                           value=0xBEEE,
                           src=bytes((0, 0, 0, 0, 0xAA, 0xBB))))
    cases.append(base_case("alias, copy leaves a non-zero payload word",
                           descriptor=alias, payload=SRC_ADDR, flags=0x9,
                           value=0xBEED,
                           src=bytes((0x11, 0x22, 0x33, 0x44, 0x55, 0x66))))
    cases.append(base_case("alias, payload absent",
                           descriptor=alias, payload=0, flags=0x9,
                           value=0x0001, flag=0x80))

    # --- success with the second descriptor page
    cases.append(base_case("second descriptor page", descriptor=DESC2_ADDR,
                           payload=SRC_ADDR, flags=0x9))

    # --- descriptor control word read-modify-write
    for control in (0x00000000, 0x00000001, 0x80000000, 0x40200000,
                    0xFFFFFFFF):
        cases.append(base_case(f"control word 0x{control:08x}", control=control,
                               payload=SRC_ADDR, flags=0x9))

    # --- failure combinations that must leave memory untouched
    cases.append(base_case("helper disabled with all sentinels",
                           global_flag=0, address=0, stride=0xFFFFFFFF,
                           flags=0xFFFFFFFF, payload=SRC_ADDR))
    cases.append(base_case("address outside window with payload",
                           address=0x20000000, payload=SRC_ADDR, flags=0x9))
    cases.append(base_case("end outside window with payload",
                           address=0x1BFFFFF0, stride=0x100, payload=SRC_ADDR,
                           flags=0x1))
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    orig_runner = Runner()
    cand_runner = Runner()
    passed = 0
    for case in cases:
        orig = orig_runner.run(orig_code, case)
        cand = cand_runner.run(cand_code, case, CAND_ADDR)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  (ret={orig['ret']}, "
            f"calls={len(orig['call_log'])}, writes={orig['write_regions']})"
        )
    return passed


def main() -> None:
    print("Testing func_0015f514 (0x0015f514)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("address_low", "constexpr u32 kAddressLow = 0x14000000;",
         "constexpr u32 kAddressLow = 0x14000001;"),
        ("address_high", "constexpr u32 kAddressHigh = 0x1C000000;",
         "constexpr u32 kAddressHigh = 0x1C000001;"),
        ("address_span", "constexpr u32 kAddressSpan = 0x08000000;",
         "constexpr u32 kAddressSpan = 0x08000010;"),
        ("control_flags", "constexpr u32 kControlFlags = 0x40200000;",
         "constexpr u32 kControlFlags = 0x40200001;"),
        ("selector_offset", "constexpr u32 kSelectorOffset = 0x131A;",
         "constexpr u32 kSelectorOffset = 0x131B;"),
        ("channel_stride", "constexpr u32 kChannelStride = 0x60;",
         "constexpr u32 kChannelStride = 0x61;"),
        ("slot_offset", "constexpr u32 kSlotPointerOffset = 0xB0;",
         "constexpr u32 kSlotPointerOffset = 0xB1;"),
        ("payload_halfwords", "constexpr u32 kPayloadHalfwords = 3;",
         "constexpr u32 kPayloadHalfwords = 2;"),
        ("seven_magic", "constexpr s32 kSevenScaleMagic = -1840700269;",
         "constexpr s32 kSevenScaleMagic = -1837492268;"),
        ("scaled_shift", "        end = address + (static_cast<u32>(units) << 3);",
         "        end = address + (static_cast<u32>(units) << 2);"),
        ("flag_bit_mask",
         "        ((static_cast<u32>(record->flag) << 1) & 2u));",
         "        ((static_cast<u32>(record->flag) << 1) & 4u));"),
        ("clear_a4", "    descriptor->field_a4 = 0;",
         "    descriptor->field_a4 = 1;"),
        ("value_store", "    descriptor->field_be = value;",
         "    descriptor->field_be = static_cast<u16>(value + 1);"),
        ("count_two_shift",
         "            end = address + (stride << 2);",
         "            end = address + (stride << 1);"),
        # NOTE: the `high < 0 ? 1 : 0` sign correction has no observable effect:
        # a negative high word always yields units >= 0xF0000001, so the scaled
        # step is >= 0x80000000 and the end address always lands above
        # 0x1C000000.  It is transcribed verbatim from `sub r0, ip, r0, asr #31`
        # but cannot be covered by a differential case.
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        orig_runner = Runner()
        cand_runner = Runner()
        detected = False
        for case in cases:
            orig = orig_runner.run(orig_code, case)
            try:
                bad = cand_runner.run(mutant_code, case, CAND_ADDR)
            except Exception:
                # A mutant that faults on a fixture is trivially detected.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
