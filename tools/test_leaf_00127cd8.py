#!/usr/bin/env python3
"""Differential test for func_00127cd8 (0x00127cd8, 420 B) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_00127cd8 candidate
body and runs the pinned original (extracted/exefs/code.bin, including its two
literal-pool words) against the candidate in separate Unicorn ARM machines with
identical fixtures.

The function has no direct or indirect calls, so no stubs are needed.  It walks
a u8 slot count at object+0x08, and for each slot:

  * descriptor = *(u32*)(object + 0x0C + 4*slot);
  * descriptor byte +0x06 selects mask word object+0x29C / +0x2A0 and the tag;
  * entry array = descriptor + *(u32*)(descriptor+0x18), count at +0x1C;
  * records are 20 bytes: u16 opcode, u16 parameter, four u32 fields;
  * encoded words go to object + 0x368 + slot*0x928;
  * the emitted word count goes to *(u32*)(object + 0x12868 + 4*slot).

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the full 0xA0000-byte object page (mask words, every output buffer, every
    published word count) and the full descriptor page;
  * any emulated write outside the object page and the private stack.

Coverage: zero, one, several, the 32-slot buffer capacity boundary, the
33-slot crossing into the count table, and the 0xFF (u8 maximum) slot count;
descriptors with zero records; opcode 0 bit indices 0/1/7/8/15/16/30/31/32/33/
63/127/128/255/256/257/0xFFFF with clear and set field bits; opcodes 1 and 2
with zero, maximum and mixed field words; unknown opcodes; both tag/variant
selections and both mask words; and a seeded random sweep.

Negative controls mutate the slot stride, the alternate mask offset, the
parameter bias, the terminator, the ARM shift bound, the opcode-1 byte shift,
the opcode-2 field mask and the buffer base; each mutant must be detected.
"""

from __future__ import annotations

import random
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
OUT_DIR = ROOT / "build/test_leaf_00127cd8"

FUNC_ADDR = 0x00127CD8
FUNC_SIZE = 420

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
OBJECT_ADDR = 0x00710000
OBJECT_SIZE = 0x000A0000  # covers buffers up to the 0xFF slot buffer end
DESC_ADDR = 0x00600000
DESC_SIZE = 0x00040000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Object offsets recovered from the ARM body.
SLOT_COUNT_OFFSET = 0x08
SLOT_DESCRIPTOR_OFFSET = 0x0C
MASK_WORD_OFFSET = 0x29C
MASK_WORD_ALTERNATE_OFFSET = 0x2A0
OUTPUT_BUFFER_OFFSET = 0x368
OUTPUT_SLOT_STRIDE = 0x928
OUTPUT_COUNT_OFFSET = 0x12868

DESCRIPTOR_VARIANT_OFFSET = 0x06
DESCRIPTOR_ENTRY_OFFSET_FIELD = 0x18
DESCRIPTOR_ENTRY_COUNT_FIELD = 0x1C
DESCRIPTOR_ENTRY_OFFSET = 0x40
RECORD_STRIDE = 20

DESC_BASE = 0x1000
DESC_SPACING = 0x200

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

STACK_FILL = 0x5A
OBJECT_FILL = 0xA5
DESC_FILL = 0xA9


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def extract_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00127cd8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"func_00127cd8 not found in {obj_file}: {sorted(funcs)}")
    code_raw, relocs = candidate
    if relocs:
        raise RuntimeError(
            "func_00127cd8 is expected to have no relocations: "
            f"{[(rel.relocation_type, rel.symbol_name) for rel in relocs]}"
        )
    return code_raw


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return extract_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return extract_candidate(obj_file)


def rec(op: int, param: int = 0, f1: int = 0, f2: int = 0, f3: int = 0,
        f4: int = 0) -> tuple:
    return (op, param, f1, f2, f3, f4)


def slot(variant: int = 0, records=()) -> dict:
    return {"variant": variant, "records": list(records)}


def build_fixtures(case: dict) -> tuple[bytes, bytes]:
    """Return (object page, descriptor page) for a case."""
    slots = case["slots"]
    if len(slots) > 0xFF:
        raise RuntimeError("slot count must fit the u8 field")

    object_page = bytearray([OBJECT_FILL]) * OBJECT_SIZE
    object_page[SLOT_COUNT_OFFSET] = len(slots)
    struct.pack_into("<I", object_page, MASK_WORD_OFFSET,
                     case["mask_plain"] & 0xFFFFFFFF)
    struct.pack_into("<I", object_page, MASK_WORD_ALTERNATE_OFFSET,
                     case["mask_variant"] & 0xFFFFFFFF)
    for index in range(len(slots)):
        struct.pack_into("<I", object_page, OUTPUT_COUNT_OFFSET + index * 4,
                         0x5A5A0000 | index)

    desc_page = bytearray([DESC_FILL]) * DESC_SIZE
    for index, spec in enumerate(slots):
        base = DESC_BASE + index * DESC_SPACING
        if base + DESC_SPACING > DESC_SIZE:
            raise RuntimeError(f"descriptor {index} does not fit the page")
        struct.pack_into("<I", object_page, SLOT_DESCRIPTOR_OFFSET + index * 4,
                         DESC_ADDR + base)
        # Unread sentinels around the fields the body does read.
        struct.pack_into("<I", desc_page, base + 0x00, 0xDEAD0000 | index)
        struct.pack_into("<I", desc_page, base + 0x04, 0xBEAD0000 | index)
        desc_page[base + DESCRIPTOR_VARIANT_OFFSET] = spec["variant"] & 0xFF
        struct.pack_into("<I", desc_page, base + DESCRIPTOR_ENTRY_OFFSET_FIELD,
                         DESCRIPTOR_ENTRY_OFFSET)
        struct.pack_into("<I", desc_page, base + DESCRIPTOR_ENTRY_COUNT_FIELD,
                         len(spec["records"]))
        struct.pack_into("<I", desc_page, base + 0x20, 0xC0DE0000 | index)
        struct.pack_into("<I", desc_page, base + 0x3C, 0x3C3C0000 | index)
        for entry, record in enumerate(spec["records"]):
            offset = base + DESCRIPTOR_ENTRY_OFFSET + entry * RECORD_STRIDE
            if offset + RECORD_STRIDE > base + DESC_SPACING:
                raise RuntimeError(f"descriptor {index} record {entry} overflows")
            op, param, f1, f2, f3, f4 = record
            struct.pack_into("<HHIIII", desc_page, offset,
                             op & 0xFFFF, param & 0xFFFF,
                             f1 & 0xFFFFFFFF, f2 & 0xFFFFFFFF,
                             f3 & 0xFFFFFFFF, f4 & 0xFFFFFFFF)
    return bytes(object_page), bytes(desc_page)


class Runner:
    """One Unicorn machine; the function issues no calls."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(DESC_ADDR, DESC_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        object_page, desc_page = build_fixtures(case)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJECT_ADDR, object_page)
        self.uc.mem_write(DESC_ADDR, desc_page)
        self.uc.mem_write(STACK_ADDR, bytes([STACK_FILL]) * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        # r1-r3 are never read by the body.
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=20_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = [
            (address, size)
            for address, size, _value in self.writes
            if not (OBJECT_ADDR <= address < OBJECT_ADDR + OBJECT_SIZE)
            and not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
            "desc": bytes(self.uc.mem_read(DESC_ADDR, DESC_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("object", "desc"):
        if orig[key] != cand[key]:
            differing = [
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            ]
            detail = []
            for index in differing[:8]:
                detail.append(
                    f"0x{index:x}: orig=0x{orig[key][index]:02x} "
                    f"cand=0x{cand[key][index]:02x}"
                )
            problems.append(
                f"{key} page differs at {len(differing)} offsets: "
                + ", ".join(detail)
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, slots=(), mask_plain=0, mask_variant=0) -> dict:
    return {
        "name": name,
        "slots": list(slots),
        "mask_plain": mask_plain,
        "mask_variant": mask_variant,
    }


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- outer-loop bounds: u8 slot count zero, one, and small values.
    cases.append(base_case("zero slots", slots=[]))
    cases.append(base_case("one slot, no records, variant 0",
                           slots=[slot(0, [])]))
    cases.append(base_case("one slot, no records, variant 1",
                           slots=[slot(1, [])]))

    # --- opcode 0: bit index boundaries and set/clear field bits.
    bit_indices = (0, 1, 7, 8, 15, 16, 30, 31, 32, 33, 63, 127, 128, 255,
                   256, 257, 0xFFFF)
    bit_records = []
    for position, index in enumerate(bit_indices):
        # Force set bits at both sides of the 32-bit shift boundary so the
        # `shift < 32` guard is exercised for 31 (set) and 32 (dropped).
        set_bit = index in (0, 1, 31, 33, 256, 0xFFFF) or position % 2 == 0
        value = 0xFFFFFFFF if set_bit else 0xFFFFFFFE
        bit_records.append(rec(0, index, value))
    cases.append(base_case(
        "opcode 0 bit index boundaries accumulate",
        slots=[slot(0, bit_records)], mask_plain=0x00000000))
    cases.append(base_case(
        "opcode 0 starts from non-zero mask",
        slots=[slot(0, bit_records)], mask_plain=0xA5A5000F))

    # A clear bit on an empty mask must leave it untouched (but still store).
    cases.append(base_case(
        "opcode 0 clear bit on empty mask",
        slots=[slot(0, [rec(0, 5, 0), rec(0, 31, 2), rec(0, 300, 0)])]))
    # Variant descriptors must accumulate into the alternate word only.
    cases.append(base_case(
        "opcode 0 variant mask word",
        slots=[slot(1, [rec(0, 0, 1), rec(0, 9, 1), rec(0, 31, 1)])],
        mask_plain=0x12345678, mask_variant=0x80000000))
    cases.append(base_case(
        "opcode 0 two slots different variants",
        slots=[
            slot(0, [rec(0, 1, 1)]),
            slot(1, [rec(0, 2, 1)]),
            slot(0, [rec(0, 3, 1)]),
        ],
        mask_plain=0x0F0F0F0F, mask_variant=0xF0F0F0F0))

    # --- opcode 1: byte packing and the biased parameter word.
    op1_records = [
        rec(1, 0x0000, 0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00),
        rec(1, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
        rec(1, 0x7FFF, 0x00000000, 0x00000000, 0x00000000, 0x00000000),
        rec(1, 0x0102, 0x80000001, 0x00000080, 0x00008000, 0x00800000),
    ]
    cases.append(base_case("opcode 1 packing variant 0",
                           slots=[slot(0, op1_records)]))
    cases.append(base_case("opcode 1 packing variant 1",
                           slots=[slot(1, op1_records)]))

    # --- opcode 2: six-word stream, both variants, extreme fields.
    op2_records = [
        rec(2, 0x0000, 0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00),
        rec(2, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
        rec(2, 0x0001, 0x00FF0000, 0x0000FF00, 0xFF0000FF, 0x00000000),
        rec(2, 0x8000, 0x80000000, 0x00000001, 0x00000002, 0x7FFFFFFF),
    ]
    cases.append(base_case("opcode 2 stream variant 0",
                           slots=[slot(0, op2_records)]))
    cases.append(base_case("opcode 2 stream variant 1",
                           slots=[slot(1, op2_records)]))

    # --- mixed opcodes in one slot: exact cursor advance and final count.
    cases.append(base_case(
        "mixed opcodes one slot",
        slots=[slot(0, [
            rec(0, 3, 1),
            rec(1, 0x1234, 1, 2, 3, 4),
            rec(2, 0x4321, 5, 6, 7, 8),
            rec(3, 0xFFFF, 9, 10, 11, 12),
            rec(2, 0x0000, 13, 14, 15, 16),
            rec(1, 0xFFFF, 17, 18, 19, 20),
        ])]))
    cases.append(base_case(
        "mixed opcodes one slot variant 1",
        slots=[slot(1, [
            rec(2, 0x0000, 0x01020304, 0x05060708, 0x090A0B0C, 0x0D0E0F10),
            rec(1, 0x0000, 0x11121314, 0x15161718, 0x191A1B1C, 0x1D1E1F20),
        ])],
        mask_plain=0x11111111, mask_variant=0x22222222))

    # --- unknown opcodes only: no output words, count 0, mask untouched.
    cases.append(base_case(
        "unknown opcodes ignored",
        slots=[slot(0, [rec(3), rec(4, 5, 6, 7, 8, 9), rec(0xFFFF),
                        rec(0x8000, 1, 2, 3, 4, 5)])],
        mask_plain=0xDEADBEEF))

    # --- multi-slot: buffers, counts and masks are independent per slot.
    cases.append(base_case(
        "three slots mixed",
        slots=[
            slot(0, [rec(1, 0x1111, 1, 2, 3, 4), rec(0, 0, 1)]),
            slot(1, []),
            slot(0, [rec(2, 0x2222, 5, 6, 7, 8), rec(2, 0x3333, 9, 10, 11, 12),
                     rec(1, 0x4444, 13, 14, 15, 16)]),
        ],
        mask_plain=0x01020304, mask_variant=0x05060708))

    # --- outer-loop boundary: 32 buffers exactly fill the table before the
    # count array, then 33 slots cross into it, then the u8 maximum.
    def uniform_slots(count: int, record: tuple, variant: int) -> list:
        return [slot(variant if index & 1 else 0, [record])
                for index in range(count)]

    cases.append(base_case(
        "32 slots one opcode 2 each",
        slots=uniform_slots(32, rec(2, 0x1111, 1, 2, 3, 4), 1)))
    cases.append(base_case(
        "33 slots cross into count table",
        slots=uniform_slots(33, rec(2, 0x2222, 5, 6, 7, 8), 0)))

    # 255 slots (u8 maximum).  Low slots emit nothing so their buffers cannot
    # clobber the descriptor-pointer table; the high slots exercise the largest
    # buffer and count offsets.
    max_slots = []
    for index in range(0xFF):
        if index >= 215:
            max_slots.append(slot(index & 1, [rec(1, 0x3333, 9, 10, 11, 12)]))
        else:
            max_slots.append(slot(index & 1, []))
    cases.append(base_case("255 slots one opcode 1 in high slots",
                           slots=max_slots))

    # --- seeded random sweep over slot count, variants, opcodes and fields.
    rng = random.Random(0x00127CD8)
    interesting = (0x00000000, 0x00000001, 0x000000FF, 0x0000FFFF,
                   0x00FF00FF, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF,
                   0xDEADBEEF, 0x5A5A5A5A)
    for sweep in range(16):
        slot_count = rng.choice((0, 1, 2, 3, 4))
        slots = []
        for index in range(slot_count):
            records = []
            for _ in range(rng.randrange(0, 6)):
                opcode = rng.choice((0, 1, 2, 3, 0xFFFF))
                records.append(rec(
                    opcode,
                    rng.randrange(0, 0x10000),
                    rng.choice(interesting),
                    rng.choice(interesting),
                    rng.choice(interesting),
                    rng.choice(interesting)))
            slots.append(slot(1 if (index + sweep) & 1 else 0, records))
        cases.append(base_case(
            f"sweep {sweep:02d} slots={slot_count}",
            slots=slots,
            mask_plain=rng.choice(interesting),
            mask_variant=rng.choice(interesting)))

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
        print(f"  [PASS] {case['name']}  ({len(case['slots'])} slots)")
    return passed


def main() -> None:
    print("Testing func_00127cd8 (0x00127cd8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(no relocations).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("slot_stride",
         "constexpr u32 kOutputSlotStride = kSlotStrideFactor * 8;",
         "constexpr u32 kOutputSlotStride = kSlotStrideFactor * 4;"),
        ("alternate_mask_offset",
         "constexpr u32 kMaskWordAlternateOffset = 0x2A0;",
         "constexpr u32 kMaskWordAlternateOffset = 0x2A4;"),
        ("parameter_bias",
         "constexpr u32 kParameterBias = 0xF;",
         "constexpr u32 kParameterBias = 0xE;"),
        ("stream_terminator",
         "constexpr u32 kStreamTerminator = 0xEAD0FEAD;",
         "constexpr u32 kStreamTerminator = 0xEAD0FEAE;"),
        ("shift_bound",
         "return amount < 32u ? value << amount : 0u;",
         "return amount < 31u ? value << amount : 0u;"),
        ("opcode1_byte_shift",
         "*out++ = field_a | (field_b << 8) | (field_c << 16) |",
         "*out++ = field_a | (field_b << 9) | (field_c << 16) |"),
        ("opcode2_field_mask",
         "*out++ = (field_a & 0x00FFFFFFu) | (field_b_second << 24);",
         "*out++ = (field_a & 0x000FFFFFu) | (field_b_second << 24);"),
        ("output_buffer_base",
         "constexpr u32 kOutputBufferOffset = 0x368;",
         "constexpr u32 kOutputBufferOffset = 0x36C;"),
    ):
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
