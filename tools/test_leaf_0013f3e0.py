#!/usr/bin/env python3
"""Differential test for func_0013f3e0 (0x0013f3e0) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the func_0013f3e0 body,
resolves its direct call to 0x002A7F94, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with the helper's slot pointer (normalised when it is
    the callee's private stack word), the object address, its tag word and the
    value the deterministic helper returns;
  * every write outside the private stack (the original's stack scratch word is
    deliberately excluded: it is below the caller's SP and unobservable);
  * the complete 256 KiB fixture arena.

Coverage: every one of the six references independently takes the null-slot,
null-object, tag-without-bit-30 (0x00000000, 0x3FFFFFFF, 0x7FFFFFFF,
0x80000000), tag-with-bit-30-but-not-0x40000000 (0xC0000000, 0x40000001,
0xFFFFFFFF), exact 0x40000000 with payload, and exact 0x40000000 with a zero
payload displacement (the helper is still called).  Seed fingerprints 0,
0x7FFFFFFF, 0x80000000, 0xFFFFFFFF and 0x12345678 are covered, as is a shared
descriptor (two references resolving to the same object) and both unguarded
fault paths (owner + 0x288 word zero -> read 0x28; record + 0x28 word zero ->
read 0x0C), and an ordering probe where the helper re-points the owner word on
its first call (the original re-reads it before its final store and return).
Negative controls mutate a record-slot offset, a rotation amount, the
accepted-tag bit and the seed word; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0013f3e0"

FUNC_ADDR = 0x0013F3E0
FUNC_SIZE = 684

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and the 0x002A7F94 stub
ARENA_ADDR = 0x00600000
ARENA_SIZE = 0x00040000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Fixture layout inside the arena.
SELF_ADDR = ARENA_ADDR + 0x00000
OWNER_ADDR = ARENA_ADDR + 0x01000
NEW_OWNER_ADDR = ARENA_ADDR + 0x01800  # re-pointed owner used by one probe
TABLE_ADDR = ARENA_ADDR + 0x02000
RECORD_ADDR = ARENA_ADDR + 0x03000
DESC_BASE = ARENA_ADDR + 0x10000

# Direct-call target, stubbed at its original address so the original bytes and
# the relocated candidate resolve to the same deterministic helper.
STUB_2A7F94 = 0x002A7F94
STUB_NAMES = {STUB_2A7F94: "func_002a7f94"}

# Record slots folded by the function, in the original's evaluation order.
SLOT_OFFSETS = (0x0C, 0x10, 0x00, 0x04, 0x08, 0x14)

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
CALLEE_SAVED_START = {name: 0x44444444 + index * 0x11111111 for index, name in
                      enumerate(CALLEE_SAVED)}

# Reference fixtures: None = zero slot displacement, ("none",) = descriptor
# present but its +0x08 displacement is zero, (tag, has_payload) = tagged object.
REF_NULL = None
REF_NO_OBJECT = ("none",)


def ref(tag: int, payload: bool = True):
    return (tag, payload)


REF_PRESENT = ref(0x40000000)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0013f3e0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_0013f3e0 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            if (target - pc) & 3:
                raise RuntimeError(f"unaligned call target 0x{target:08x}")
            if not -(1 << 23) <= displacement < (1 << 23):
                raise RuntimeError(f"call target out of BL range: 0x{target:08x}")
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0xFFFFFF))
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


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
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def build_arena(case: dict) -> bytes:
    arena = bytearray(ARENA_SIZE)

    def put32(address: int, value: int) -> None:
        struct.pack_into("<I", arena, address - ARENA_ADDR, value & 0xFFFFFFFF)

    def relative(target: int, slot_address: int) -> int:
        return (target - slot_address) & 0xFFFFFFFF

    put32(SELF_ADDR, OWNER_ADDR)
    put32(OWNER_ADDR + 0x2C4, case["previous"])
    put32(OWNER_ADDR + 0x2C0, 0xDEADBEEF)
    put32(NEW_OWNER_ADDR + 0x2C0, 0xDEADBEEF)
    put32(
        OWNER_ADDR + 0x288,
        0
        if case.get("owner_slot_null")
        else relative(TABLE_ADDR, OWNER_ADDR + 0x288),
    )
    put32(
        TABLE_ADDR + 0x28,
        0
        if case.get("record_slot_null")
        else relative(RECORD_ADDR, TABLE_ADDR + 0x28),
    )

    descriptor_map = case.get("descriptor_map", list(range(len(SLOT_OFFSETS))))
    for index, slot in enumerate(SLOT_OFFSETS):
        spec = case["refs"][index]
        slot_address = RECORD_ADDR + slot
        if spec is REF_NULL:
            put32(slot_address, 0)
            continue
        descriptor = DESC_BASE + descriptor_map[index] * 0x100
        put32(slot_address, relative(descriptor, slot_address))
        if spec[0] == "none":
            put32(descriptor + 0x08, 0)
            continue
        tag, has_payload = spec
        tagged_object = descriptor + 0x40
        put32(descriptor + 0x08, relative(tagged_object, descriptor + 0x08))
        put32(tagged_object + 0x00, tag)
        if has_payload:
            payload = tagged_object + 0x80
            put32(tagged_object + 0x0C, relative(payload, tagged_object + 0x0C))
            put32(payload, 0xFEED0000 | index)
    return bytes(arena)


# ---------------------------------------------------------------------- machine
class Machine:
    """One Unicorn machine with the deterministic 0x002A7F94 helper."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(ARENA_ADDR, ARENA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(STUB_2A7F94, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub, begin=STUB_2A7F94, end=STUB_2A7F94
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_UNMAPPED, self._on_unmapped)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.fault = None
        self.mutate_self = False

    @staticmethod
    def _normalise(value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _on_unmapped(self, uc, access, address, size, value, user_data) -> bool:
        if self.fault is None:
            self.fault = (address, size, access)
        return False

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return  # the callee's private scratch word
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        slot = uc.reg_read(arm.UC_ARM_REG_R0)
        tagged_object = struct.unpack("<I", uc.mem_read(slot, 4))[0]
        tag = struct.unpack("<I", uc.mem_read(tagged_object, 4))[0]
        result = 0
        if tag == 0x80000000:
            result = tagged_object
        elif tag == 0x40000000:
            displacement = struct.unpack(
                "<I", uc.mem_read(tagged_object + 0x0C, 4)
            )[0]
            if displacement != 0:
                result = tagged_object + 0x0C + displacement
        self.call_log.append(
            (
                STUB_NAMES[address],
                self._normalise(slot),
                tagged_object,
                tag,
                result,
            )
        )
        uc.reg_write(arm.UC_ARM_REG_R0, result)
        if self.mutate_self and len(self.call_log) == 1:
            # Ordering probe: the original re-reads *self after the helper calls
            # before it stores the fingerprint and returns the owner word.
            uc.mem_write(SELF_ADDR, struct.pack("<I", NEW_OWNER_ADDR))

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.fault = None
        self.mutate_self = case.get("mutate_self", False)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(ARENA_ADDR, build_arena(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError:
            if self.fault is None:
                raise

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": list(self.writes),
            "arena": bytes(self.uc.mem_read(ARENA_ADDR, ARENA_SIZE)),
            "fault": self.fault,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems: list[str] = []
    if (orig["fault"] is None) != (cand["fault"] is None):
        problems.append(f"fault presence: orig={orig['fault']} cand={cand['fault']}")
    if orig["fault"] is not None:
        if orig["fault"][0] != cand["fault"][0]:
            problems.append(
                f"fault address: orig=0x{orig['fault'][0]:08x} "
                f"cand=0x{cand['fault'][0]:08x}"
            )
        if orig["call_log"] != cand["call_log"]:
            problems.append(
                "call_log before fault:\n    orig="
                + repr(orig["call_log"])
                + "\n    cand="
                + repr(cand["call_log"])
            )
        return problems

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
            "non-stack writes:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    if orig["arena"] != cand["arena"]:
        first = next(
            index
            for index, (left, right) in enumerate(zip(orig["arena"], cand["arena"]))
            if left != right
        )
        problems.append(
            f"arena mismatch at 0x{ARENA_ADDR + first:08x}: "
            f"orig=0x{orig['arena'][first]:02x} cand=0x{cand['arena'][first]:02x}"
        )
    return problems


# ----------------------------------------------------------------------- cases
def base_case(name: str, refs=None, **overrides) -> dict:
    case = {
        "name": name,
        "previous": 0x12345678,
        "refs": list(refs) if refs is not None else [REF_PRESENT] * 6,
    }
    case.update(overrides)
    return case


def all_refs(spec) -> list:
    return [spec] * 6


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Baseline and the six references independently.
    cases.append(base_case("all references present"))
    for index, slot in enumerate(SLOT_OFFSETS):
        refs = [REF_PRESENT] * 6
        refs[index] = REF_NULL
        cases.append(base_case(f"slot 0x{slot:02x} null", refs))
        refs = [REF_PRESENT] * 6
        refs[index] = REF_NO_OBJECT
        cases.append(base_case(f"slot 0x{slot:02x} null object", refs))
        refs = [REF_PRESENT] * 6
        refs[index] = ref(0x80000000)
        cases.append(base_case(f"slot 0x{slot:02x} tag 0x80000000", refs))

    # Tag words without bit 30: skipped before the helper call.
    for tag in (0x00000000, 0x3FFFFFFF, 0x7FFFFFFF, 0x80000000, 0x00000001):
        cases.append(base_case(f"all tags 0x{tag:08x}", all_refs(ref(tag))))

    # Bit 30 set: the helper is always called; only 0x40000000 resolves.
    for tag in (0x40000000, 0x40000001, 0xC0000000, 0xFFFFFFFF):
        cases.append(
            base_case(f"all tags 0x{tag:08x} with payload", all_refs(ref(tag)))
        )
    cases.append(
        base_case(
            "all tags 0x40000000 zero payload displacement",
            all_refs(ref(0x40000000, False)),
        )
    )

    # Mixed reference results in one record.
    cases.append(
        base_case(
            "mixed states",
            [
                REF_PRESENT,
                REF_NULL,
                ref(0x80000000),
                ref(0x40000000, False),
                ref(0xC0000000),
                REF_NO_OBJECT,
            ],
        )
    )
    cases.append(
        base_case(
            "mixed states reversed",
            [
                REF_NO_OBJECT,
                ref(0xC0000000),
                ref(0x40000000, False),
                ref(0x80000000),
                REF_NULL,
                REF_PRESENT,
            ],
        )
    )

    # Two references resolving through the same descriptor.
    cases.append(
        base_case(
            "shared descriptor",
            [REF_PRESENT, REF_PRESENT, ref(0x40000000, False), REF_NULL,
             ref(0x80000000), REF_PRESENT],
            descriptor_map=[0, 0, 2, 3, 4, 5],
        )
    )

    # Seed word boundaries.
    for previous in (0x00000000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0x00000001):
        cases.append(
            base_case(
                f"seed 0x{previous:08x}",
                [
                    REF_PRESENT,
                    ref(0xC0000000),
                    REF_NULL,
                    ref(0x40000000, False),
                    REF_PRESENT,
                    ref(0x80000000),
                ],
                previous=previous,
            )
        )

    # Unguarded fault paths: the original reads 0x28 / 0x0C.
    cases.append(base_case("owner + 0x288 word zero", owner_slot_null=True))
    cases.append(base_case("record + 0x28 word zero", record_slot_null=True))

    # Ordering probe: the helper re-points the owner word on its first call, so
    # the final store target and the returned owner are the new word.
    cases.append(
        base_case(
            "helper repoints the owner word on the first call",
            [
                REF_PRESENT,
                REF_PRESENT,
                ref(0x40000000, False),
                REF_NULL,
                ref(0xC0000000),
                REF_PRESENT,
            ],
            mutate_self=True,
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Machine().run(orig_code, case)
        cand = Machine().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        suffix = "fault" if orig["fault"] is not None else f"{len(orig['call_log'])} calls"
        print(f"  [PASS] {case['name']}  ({suffix})")
        passed += 1
    return passed


def main() -> None:
    print("Testing func_0013f3e0 (0x0013f3e0)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(call relocation resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("record_slot_b", "constexpr u32 kRecordRefB = 0x10;",
         "constexpr u32 kRecordRefB = 0x14;"),
        ("rotation_b", "constexpr u32 kRotateB = 28;",
         "constexpr u32 kRotateB = 24;"),
        ("tag_present_bit", "constexpr u32 kTagPresent = 0x40000000;",
         "constexpr u32 kTagPresent = 0x80000000;"),
        ("seed_offset", "constexpr u32 kPreviousFingerprint = 0x2c4;",
         "constexpr u32 kPreviousFingerprint = 0x2c0;"),
        (
            "cached_owner",
            "    const u32 final_owner = LoadWord(self);\n"
            "    StoreWord(final_owner + kFingerprint, fingerprint);\n"
            "    return final_owner;",
            "    const u32 final_owner = owner;\n"
            "    StoreWord(final_owner + kFingerprint, fingerprint);\n"
            "    return final_owner;",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Machine().run(orig_code, case)
            bad = Machine().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
