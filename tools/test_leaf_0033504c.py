#!/usr/bin/env python3
"""Differential test for camp_func_0033504c (0x0033504c) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the camp_func_0033504c body,
resolves every direct call relocation to a deterministic stub placed at the
original call-target address, and runs the pinned original bytes
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

The generic table search (0x002B48DC, Thumb) and its comparator (0x001455DC)
are executed from the real pinned image rather than stubbed, so the candidate's
5th stack argument and 0x40 stride really drive a binary search over a sorted
0x40-byte record table. The TBB accessors, the two game-work getters, the event
flag test, and the discarded work-word read are stubbed.

Compared outputs:

* continuation PC, final SP, callee-saved r4-r11 (r0 is deliberately excluded:
  this routine has no defined return value and the original leaves r0 as a
  helper leftover);
* the ordered call log with every argument the stubs observe, including the
  0x40-byte search key supplied by script_vm_func_002b48dc through the real
  comparator;
* full game-work bitset page, game-work state page, and the 0x40-byte record
  table page.

Coverage: the whole key range 1..0x8C (keys 0 and 0x8D must stay clear), table
null on the first/second/third search, empty record set, both u16 +0x26 filter
outcomes, the unsigned +0x2B <= state[0x76] boundary (less/equal/greater and
0xFF vs 0x7F), all three flag-id slots (zero skipped, true, false, false on the
second and third slot), all three bit-index slots (zero skipped, set, clear,
byte 0 and byte 0x20), and the third search result being discarded.
"""

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
OUT_DIR = ROOT / "build/test_leaf_0033504c"

FUNC_ADDR = 0x0033504C
FUNC_SIZE = 480

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # pinned image through the camp function and literals
BITS_ADDR = 0x00600000
BITS_SIZE = 0x00010000
STATE_ADDR = 0x00610000
STATE_SIZE = 0x00001000
PAYLOAD_ADDR = 0x00620000
PAYLOAD_SLOT_SIZE = 0x00004000
PAYLOAD_SIZE = 0x00040000
TOKEN_ADDR = 0x00670000
TOKEN_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Pinned helper addresses; stubs overwrite the image at these addresses.
STUB_23F554 = 0x0023F554
STUB_2B66EC = 0x002B66EC
STUB_2C0EC4 = 0x002C0EC4
STUB_2C0E9C = 0x002C0E9C
STUB_2C0E4C = 0x002C0E4C
STUB_2C0BA8 = 0x002C0BA8
STUB_295F90 = 0x00295F90

STUB_NAMES = {
    STUB_23F554: "engine_func_0023f554",
    STUB_2B66EC: "script_vm_func_002b66ec",
    STUB_2C0EC4: "Tbb_GetGlobalSubTable",
    STUB_2C0E9C: "Tbb_GetPayloadData",
    STUB_2C0E4C: "Tbb_GetRowCount",
    STUB_2C0BA8: "script_vm_func_002c0ba8",
    STUB_295F90: "script_vm_func_00295f90",
}

RELOC_TARGETS = {
    "engine_func_0023f554": STUB_23F554,
    "script_vm_func_00295f90": STUB_295F90,
    "Tbb_GetGlobalSubTable": STUB_2C0EC4,
    "Tbb_GetPayloadData": STUB_2C0E9C,
    "Tbb_GetRowCount": STUB_2C0E4C,
    "script_vm_func_002b66ec": STUB_2B66EC,
    "script_vm_func_002c0ba8": STUB_2C0BA8,
}

# 0x002B48DC is Thumb code reached with BLX in the pinned image.
THUMB_RELOC_TARGETS = {"script_vm_func_002b48dc": 0x002B48DC}

KEY_COUNT = 0x8C  # keys 1..0x8C, one 0x40-byte record each
RECORD_STRIDE = 0x40

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
CALLEE_SAVED_REGS = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - CODE_ADDR)
        return handle.read(FUNC_SIZE)


def get_orig_image() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        return handle.read(CODE_SIZE)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0033504c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_0033504c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        thumb_target = None
        for token, address in THUMB_RELOC_TARGETS.items():
            if token in rel.symbol_name:
                thumb_target = address
                break
        if thumb_target is not None:
            pc = FUNC_ADDR + rel.offset + 8
            offset = thumb_target - pc
            if offset & 3:
                raise RuntimeError(f"unaligned Thumb target 0x{thumb_target:08x}")
            instruction = (
                0xFA000000
                | ((offset >> 2) & 0x00FFFFFF)
                | ((offset & 2) << 23)
            )
            struct.pack_into("<I", code, rel.offset, instruction)
            continue

        target = None
        for token, address in RELOC_TARGETS.items():
            if token in rel.symbol_name:
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


def default_record() -> dict:
    return {"filter": 0, "value": 0, "flags": (0, 0, 0), "bits": (0, 0, 0)}


def build_records(case: dict) -> bytearray:
    overrides = case.get("records", {})
    page = bytearray((i * 29 + 0x11) & 0xFF for i in range(PAYLOAD_SLOT_SIZE))
    for index in range(KEY_COUNT):
        key = index + 1
        record = dict(default_record())
        record.update(overrides.get(key, {}))
        offset = index * RECORD_STRIDE
        struct.pack_into("<H", page, offset + 0x20, key)
        struct.pack_into("<H", page, offset + 0x26, record["filter"] & 0xFFFF)
        page[offset + 0x2B] = record["value"] & 0xFF
        for slot in range(3):
            struct.pack_into(
                "<H", page, offset + 0x2C + slot * 2, record["flags"][slot] & 0xFFFF
            )
            struct.pack_into(
                "<H", page, offset + 0x32 + slot * 2, record["bits"][slot] & 0xFFFF
            )
    return page


def build_bits(case: dict) -> bytes:
    page = bytearray((i * 37 + 0x5B) & 0xFF for i in range(BITS_SIZE))
    for byte_index, bit_index in case.get("bits_set", ()):
        page[byte_index] |= 1 << bit_index
    return bytes(page)


def build_state(case: dict) -> bytes:
    page = bytearray((i * 13 + 0x21) & 0xFF for i in range(STATE_SIZE))
    page[0x76] = case.get("state_byte", 0x20) & 0xFF
    return bytes(page)


class Runner:
    """One Unicorn machine with stubs at the original call-target addresses."""

    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(BITS_ADDR, BITS_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
        self.uc.mem_map(PAYLOAD_ADDR, PAYLOAD_SIZE)
        self.uc.mem_map(TOKEN_ADDR, TOKEN_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(CODE_ADDR, get_orig_image())

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        self.call_log = []
        self.case = {}
        self.global_calls = 0
        self.rows_for_payload = {}

    def _log(self, address, *args):
        self.call_log.append((STUB_NAMES[address],) + args)

    def _on_stub(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_23F554:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, BITS_ADDR)
        elif address == STUB_2B66EC:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
        elif address == STUB_2C0EC4:
            call_index = self.global_calls
            self.global_calls += 1
            is_null = call_index in self.case.get("null_calls", ())
            self._log(address, r0, r1, is_null)
            uc.reg_write(arm.UC_ARM_REG_R0, 0 if is_null else TOKEN_ADDR + call_index * 4)
        elif address == STUB_2C0E9C:
            call_index = (r0 - TOKEN_ADDR) // 4
            payload = PAYLOAD_ADDR
            self.rows_for_payload[payload] = self.case.get("rows_override", {}).get(
                call_index, KEY_COUNT
            )
            self._log(address, call_index, payload - PAYLOAD_ADDR)
            uc.reg_write(arm.UC_ARM_REG_R0, payload)
        elif address == STUB_2C0E4C:
            rows = self.rows_for_payload.get(r0, KEY_COUNT)
            self._log(address, r0 - PAYLOAD_ADDR, rows)
            uc.reg_write(arm.UC_ARM_REG_R0, rows)
        elif address == STUB_2C0BA8:
            false_flags = self.case.get("false_flags", set())
            result = 0 if (r0 & 0xFFFF) in false_flags else 1
            self._log(address, r0 & 0xFFFF, result)
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_295F90:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x295F90)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict):
        self.call_log = []
        self.case = case
        self.global_calls = 0
        self.rows_for_payload = {}

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(BITS_ADDR, build_bits(case))
        self.uc.mem_write(STATE_ADDR, build_state(case))
        self.uc.mem_write(PAYLOAD_ADDR, bytes(build_records(case)))
        self.uc.mem_write(TOKEN_ADDR, b"\x00" * TOKEN_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED_REGS[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=30_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED_REGS.items()
            },
            "call_log": list(self.call_log),
            "bits": bytes(self.uc.mem_read(BITS_ADDR, BITS_SIZE)),
            "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
            "payload": bytes(self.uc.mem_read(PAYLOAD_ADDR, PAYLOAD_SLOT_SIZE)),
        }


def compare(orig: dict, cand: dict) -> list:
    problems = []
    for key in ("pc", "sp", "callee_saved", "call_log", "bits", "state", "payload"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    return problems


def make_cases() -> list:
    return [
        {
            "name": "every key 1..0x8C succeeds; 0 and 0x8D untouched",
        },
        {
            "name": "filter +0x26 non-zero stops at the first search",
            "records": {2: {"filter": 1}, 3: {"filter": 0xFFFF}},
        },
        {
            "name": "u8 +0x2B vs state[0x76]: less/equal/greater/0xFF",
            "state_byte": 0x20,
            "records": {
                4: {"value": 0x1F},
                5: {"value": 0x20},
                6: {"value": 0x21},
                7: {"value": 0xFF},
                8: {"value": 0x00},
            },
        },
        {
            "name": "flags: zero skipped, true, false on first/second/third",
            "records": {
                10: {"flags": (0, 0x1111, 0)},
                11: {"flags": (0x2222, 0x3333, 0)},
                12: {"flags": (0x4444, 0x5555, 0x6666)},
                13: {"flags": (0, 0, 0)},
            },
            "false_flags": {0x3333, 0x6666},
        },
        {
            "name": "bits: zero skipped, byte 0/byte 0x20 set, clear aborts",
            "bits_set": ((0x00, 3), (0x20, 7), (0x20, 0), (0x2F, 1)),
            "records": {
                20: {"bits": (0, 0x0107, 0)},
                21: {"bits": (0x0000, 0, 0x0003)},
                22: {"bits": (0x0020, 0, 0)},
                23: {"bits": (0, 0, 0)},
                24: {"bits": (0x0100, 0, 0)},
                25: {"bits": (0x017F, 0, 0)},
            },
        },
        {
            "name": "first search table null",
            "null_calls": {0},
        },
        {
            "name": "second search table null",
            "null_calls": {1},
        },
        {
            "name": "third search table null",
            "null_calls": {2},
        },
        {
            "name": "first search record missing (zero rows)",
            "rows_override": {0: 0},
        },
        {
            "name": "second search record missing (zero rows)",
            "rows_override": {1: 0},
        },
        {
            "name": "third search record missing is discarded",
            "rows_override": {2: 0},
        },
        {
            "name": "combined branch mix",
            "state_byte": 0x40,
            "bits_set": ((0x11, 7), (0x20, 0)),
            "records": {
                2: {"filter": 1},
                3: {"filter": 0},
                4: {"value": 0x41},
                5: {"value": 0x40},
                6: {"flags": (0xAAAA, 0, 0)},
                7: {"flags": (0xAAAA, 0xBBBB, 0xCCCC)},
                8: {"bits": (0x0080, 0, 0)},
                9: {"bits": (0x0100, 0, 0)},
                0x8C: {"filter": 0, "value": 0x40},
            },
            "false_flags": {0xBBBB},
        },
    ]


def patch_word(code: bytes, address: int, new_word: int) -> bytes:
    mutated = bytearray(code)
    struct.pack_into("<I", mutated, address - FUNC_ADDR, new_word)
    return bytes(mutated)


def main() -> None:
    print("Testing camp_func_0033504c (0x0033504c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
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

    print("\nNegative controls:")
    controls = [
        (
            "loop upper bound 0x8D -> 0x8B",
            0x00335218,
            0xE357008B,
            "every key 1..0x8C succeeds; 0 and 0x8D untouched",
        ),
        (
            "filter test compares against 1",
            0x003350C4,
            0xE3500001,
            "combined branch mix",
        ),
        (
            "unsigned value test BHI -> BGE",
            0x00335130,
            0xAA000037,
            "combined branch mix",
        ),
        (
            "clear-bit abort removed",
            0x00335184,
            0xE320F000,
            "bits: zero skipped, byte 0/byte 0x20 set, clear aborts",
        ),
        (
            "event flag result test compares against 1",
            0x00335148,
            0xE3500001,
            "combined branch mix",
        ),
    ]
    by_name = {case["name"]: case for case in cases}
    for label, address, word, case_name in controls:
        mutant = patch_word(orig_code, address, word)
        case = by_name[case_name]
        baseline = Runner().run(orig_code, case)
        altered = Runner().run(mutant, case)
        assert compare(baseline, altered), f"negative control not detected: {label}"
        print(f"  [PASS] {label} is detected")

    print(
        f"\nAll {passed}/{len(cases)} differential cases PASSED; "
        f"{len(controls)}/{len(controls)} negative controls detected."
    )


if __name__ == "__main__":
    main()
