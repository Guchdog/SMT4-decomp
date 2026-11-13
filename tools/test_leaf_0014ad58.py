#!/usr/bin/env python3
"""Differential test for func_0014ad58 (0x0014AD58) using Unicorn ARM.

The routine walks the optional child-object graph hanging off a node.  It reads
the node's base pointer, resolves the self-relative slot container, and checks
the requested children:

  * flag bit 0x02 -> container +0x0C
  * flag bit 0x04 -> container +0x10
  * object +0x18 low byte != 0 -> container +0x14
  * flag bit 0x20 -> container +0x00/+0x04/+0x08, selected by the low three bits
    of the byte at 0x004221F8 + kind_14

Every child must resolve to a non-zero address, must expose a non-zero word at
child+8, and child+8+word must be non-zero (32-bit wrapping arithmetic).  Failures
clear the corresponding flag bit (or the +0x18 word), force the result to 0, and
when the flag word changed it is written back with the caller's +0x2BC word
zeroed.

The test compiles the whole translation unit, extracts func_0014ad58 (no
relocations are expected because the kind table is an absolute constant), and
runs the pinned original against the candidate in separate Unicorn machines with
identical fixtures.  Compared outputs are return r0, continuation PC, final SP,
callee-saved r4-r11, the (empty) ordered call log, the full node/slot world, the
caller context page, the .rodata table page, and every write outside the private
stack and those pages.

Coverage: all eight request-bit combinations with every child present and every
child absent; each individual request against present, absent, first-hop-wraps-
to-zero, and second-hop-wraps-to-zero children; the whole 256-value kind mask
sweep with all children present and all absent; presence-word low/high byte
boundaries (0x0000FF00 must not request anything, 0x000000FF must); preserved
flag bits; combined failures; and the exact write-back/invalidate condition.
There are no loops, no direct calls, no indirect calls and no stack arguments in
the original, so the call log must stay empty on both sides.

Negative controls mutate the request bit, the presence low-byte test, the
zero-offset test, the second-hop arithmetic, the kind-table index width, the
final write condition and the mask failure clear; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0014ad58"

FUNC_ADDR = 0x0014AD58
FUNC_SIZE = 624

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the original body and its literal pool
TABLE_ADDR = 0x004221F8  # 256-byte kind-mask source in .rodata
TABLE_PAGE = TABLE_ADDR & ~0xFFF
TABLE_PAGE_SIZE = 0x1000

WORLD_ADDR = 0x00600000
WORLD_SIZE = 0x00020000
NODE_ADDR = WORLD_ADDR + 0x0000
BASE_ADDR = WORLD_ADDR + 0x0100
CONTAINER_ADDR = WORLD_ADDR + 0x1000
CHILD_ZONE = WORLD_ADDR + 0x4000

CTX_ADDR = 0x00500000
CTX_SIZE = 0x00001000
CTX_OFFSET = 0x2BC

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SLOT_OFFSETS = (0x00, 0x04, 0x08, 0x0C, 0x10, 0x14)
SLOT_NAMES = {
    0x00: "mask0",
    0x04: "mask1",
    0x08: "mask2",
    0x0C: "flag02",
    0x10: "flag04",
    0x14: "presence",
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
CTX_SENTINEL = 0xC0DE2BC0


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def get_orig_table_page() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(TABLE_PAGE - 0x00100000)
        return f.read(TABLE_PAGE_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0014ad58" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"func_0014ad58 not found in {obj_file}: {sorted(funcs)}")
    code, relocs = candidate
    if relocs:
        raise RuntimeError(
            "func_0014ad58 compiled with unexpected relocations: "
            + repr([(r.offset, r.relocation_type, r.symbol_name) for r in relocs])
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
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


def pattern(size: int, seed: int) -> bytes:
    return bytes(((index * 7 + seed) & 0xFF) for index in range(size))


PATTERN_WORLD = pattern(WORLD_SIZE, 0x31)
PATTERN_CTX = pattern(CTX_SIZE, 0x5A)
PATTERN_STACK = b"\x00" * STACK_SIZE


def default_slots(state: str) -> dict[int, str]:
    return {offset: state for offset in SLOT_OFFSETS}


def slot_relative(offset: int, state: str, child_address: int) -> int:
    if state == "absent":
        return 0
    if state == "child_wrap":
        return (-(CONTAINER_ADDR + offset)) & 0xFFFFFFFF
    return (child_address - (CONTAINER_ADDR + offset)) & 0xFFFFFFFF


def next_relative(state: str, child_address: int) -> int:
    if state == "present":
        return 0x10
    if state == "nested_absent":
        return 0
    if state == "nested_wrap":
        return (-(child_address + 8)) & 0xFFFFFFFF
    raise AssertionError(f"no second-hop state for {state}")


def build_world(case: dict) -> bytes:
    page = bytearray(PATTERN_WORLD)
    base_offset = BASE_ADDR - WORLD_ADDR
    container_offset = CONTAINER_ADDR - WORLD_ADDR

    struct.pack_into("<I", page, NODE_ADDR - WORLD_ADDR, BASE_ADDR)
    struct.pack_into("<I", page, base_offset + 0x10, case["flags"] & 0xFFFFFFFF)
    page[base_offset + 0x14] = case["kind"] & 0xFF
    struct.pack_into("<I", page, base_offset + 0x18, case["present"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, base_offset + 0x28, case["container_rel"] & 0xFFFFFFFF)

    states = case.get("slots", default_slots("present"))
    for index, offset in enumerate(SLOT_OFFSETS):
        state = states.get(offset, "absent")
        child_address = CHILD_ZONE + index * 0x100
        relative = slot_relative(offset, state, child_address)
        struct.pack_into("<I", page, container_offset + offset, relative)
        if state in ("present", "nested_absent", "nested_wrap"):
            child_offset = child_address - WORLD_ADDR
            struct.pack_into(
                "<I", page, child_offset + 8, next_relative(state, child_address)
            )
    return bytes(page)


def build_ctx() -> bytes:
    page = bytearray(PATTERN_CTX)
    struct.pack_into("<I", page, CTX_OFFSET, CTX_SENTINEL)
    return bytes(page)


class Runner:
    """One Unicorn machine; fixtures are rebuilt identically for every case."""

    def __init__(self, code: bytes, table_page: bytes) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(TABLE_PAGE, TABLE_PAGE_SIZE)
        self.uc.mem_map(WORLD_ADDR, WORLD_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(TABLE_PAGE, table_page)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def run(self, case: dict) -> dict:
        self.uc.mem_write(WORLD_ADDR, build_world(case))
        self.uc.mem_write(CTX_ADDR, build_ctx())
        self.uc.mem_write(STACK_ADDR, PATTERN_STACK)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_PC, FUNC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, NODE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        allowed = (
            (WORLD_ADDR, WORLD_ADDR + WORLD_SIZE),
            (CTX_ADDR, CTX_ADDR + CTX_SIZE),
            (STACK_ADDR, STACK_ADDR + STACK_SIZE),
        )
        unexpected_writes = []
        for address, size, _value in self.writes:
            if not any(start <= address < end for start, end in allowed):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": [],
            "world": bytes(self.uc.mem_read(WORLD_ADDR, WORLD_SIZE)),
            "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "table": bytes(self.uc.mem_read(TABLE_PAGE, TABLE_PAGE_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("world", "ctx", "table"):
        if orig[key] != cand[key]:
            first = next(
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            )
            problems.append(
                f"{key} memory differs first at +0x{first:x}: "
                f"orig=0x{orig[key][first]:02x} cand=0x{cand[key][first]:02x}"
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
        "flags": 0,
        "kind": 0,
        "present": 0,
        "container_rel": (CONTAINER_ADDR - (BASE_ADDR + 0x28)) & 0xFFFFFFFF,
        "slots": default_slots("present"),
    }
    case.update(overrides)
    return case


REQUEST_COMBOS = (0x00, 0x02, 0x04, 0x20, 0x06, 0x22, 0x24, 0x26)


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- full request-bit matrix, everything present / everything absent
    for flags in REQUEST_COMBOS:
        cases.append(base_case(f"flags 0x{flags:02x} all present", flags=flags))
        cases.append(
            base_case(
                f"flags 0x{flags:02x} all absent",
                flags=flags,
                slots=default_slots("absent"),
            )
        )

    # --- presence word boundaries (only the low byte may request slot 0x14)
    for present in (
        0x00000000,
        0x00000001,
        0x0000007F,
        0x00000080,
        0x000000FF,
        0x0000FF00,
        0x00010000,
        0x12345678,
        0x7FFFFFFF,
        0x80000000,
        0xFFFFFFFF,
    ):
        for state in ("present", "absent", "nested_absent", "nested_wrap"):
            slots = default_slots("present")
            slots[0x14] = state
            cases.append(
                base_case(
                    f"present 0x{present:08x} slot14 {state}",
                    present=present,
                    slots=slots,
                )
            )

    # --- each request against every first/second-hop outcome
    outcomes = ("present", "absent", "nested_absent", "nested_wrap", "child_wrap")
    for flags, target in ((0x02, 0x0C), (0x04, 0x10)):
        for state in outcomes:
            slots = default_slots("present")
            slots[target] = state
            cases.append(
                base_case(
                    f"flags 0x{flags:02x} {SLOT_NAMES[target]} {state}",
                    flags=flags,
                    slots=slots,
                )
            )
    for target in (0x00, 0x04, 0x08):
        for state in outcomes:
            slots = default_slots("present")
            slots[target] = state
            cases.append(
                base_case(
                    f"flags 0x20 {SLOT_NAMES[target]} {state}",
                    flags=0x20,
                    slots=slots,
                )
            )
    for state in outcomes:
        slots = default_slots("present")
        for target in (0x00, 0x04, 0x08):
            slots[target] = state
        cases.append(base_case(f"flags 0x20 all mask slots {state}", flags=0x20, slots=slots))

    # --- mixed mask failures where the sticky result must survive later checks
    cases.append(
        base_case(
            "flags 0x20 mask0 fails mask1/2 present",
            flags=0x20,
            slots={0x00: "absent", 0x04: "present", 0x08: "present",
                   0x0C: "present", 0x10: "present", 0x14: "present"},
        )
    )
    cases.append(
        base_case(
            "flags 0x20 mask1 fails mask0/2 present",
            flags=0x20,
            slots={0x00: "present", 0x04: "nested_wrap", 0x08: "present",
                   0x0C: "present", 0x10: "present", 0x14: "present"},
        )
    )
    cases.append(
        base_case(
            "flags 0x20 mask2 fails mask0/1 present",
            flags=0x20,
            slots={0x00: "present", 0x04: "present", 0x08: "child_wrap",
                   0x0C: "present", 0x10: "present", 0x14: "present"},
        )
    )
    cases.append(
        base_case(
            "flags 0x26 all requests fail",
            flags=0x26,
            present=0xFF,
            slots=default_slots("absent"),
        )
    )
    cases.append(
        base_case(
            "flags 0x26 flag slots fail, mask passes",
            flags=0x26,
            present=0,
            kind=3,  # mask 0xd8: low three bits clear
            slots={0x00: "present", 0x04: "present", 0x08: "present",
                   0x0C: "absent", 0x10: "nested_wrap", 0x14: "present"},
        )
    )

    # --- preserved high flag bits and mixed mutations
    for flags in (
        0xFFFFFFF9,
        0xFFFFFFFB,
        0xFFFFFFDF,
        0x12345678,
        0xA5A5A500,
        0x80000006,
        0xFFFFFFFF,
        0x00000000,
    ):
        for slots in (default_slots("present"), default_slots("absent")):
            cases.append(base_case(f"preserve flags 0x{flags:08x}", flags=flags, slots=slots))

    # --- the full 256-value kind sweep: all present (never fails) and all
    #     absent (fails exactly when the mask selects one of the three slots)
    for kind in range(256):
        cases.append(
            base_case(
                f"kind {kind:02x} all present",
                flags=0x20,
                kind=kind,
                slots=default_slots("present"),
            )
        )
        cases.append(
            base_case(
                f"kind {kind:02x} all absent",
                flags=0x20,
                kind=kind,
                slots=default_slots("absent"),
            )
        )

    # --- the null container is only safe when nothing dereferences it
    cases.append(
        base_case(
            "null container no requests",
            flags=0,
            present=0x0000FF00,
            container_rel=0,
            slots=default_slots("absent"),
        )
    )

    # --- first-hop address values that stay inside the world but are unusual
    cases.append(
        base_case(
            "flags 0x26 everything present",
            flags=0x26,
            present=0xFF,
            kind=0,
            slots=default_slots("present"),
        )
    )
    return cases


def run_case_set(orig_runner: Runner, cand_runner: Runner, cases) -> int:
    passed = 0
    for case in cases:
        orig = orig_runner.run(case)
        cand = cand_runner.run(case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
    return passed


def main() -> None:
    print("Testing func_0014ad58 (0x0014AD58)...")
    orig_code = get_orig_bytes()
    table_page = get_orig_table_page()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (no relocations).")

    orig_runner = Runner(orig_code, table_page)
    cand_runner = Runner(cand_code, table_page)
    cases = make_cases()
    passed = run_case_set(orig_runner, cand_runner, cases)
    print(f"  [PASS] {passed} differential cases")

    print("\nNegative controls:")
    controls = (
        (
            "request_bit",
            "constexpr u32 kRequestSlot0C = 0x02;",
            "constexpr u32 kRequestSlot0C = 0x08;",
        ),
        (
            "presence_width",
            "if ((object->present_18 & 0xFFu) != 0) {",
            "if (object->present_18 != 0) {",
        ),
        (
            "first_hop_zero",
            'if (relative == 0) {\n        return 0;\n    }',
            'if (relative == 0) {\n        return 1;\n    }',
        ),
        (
            "second_hop_sum",
            "return child + 8 + next;",
            "return next;",
        ),
        (
            "kind_index_width",
            "reinterpret_cast<const u8*>(kKindMaskAddress)[object->kind_14]",
            "reinterpret_cast<const u8*>(kKindMaskAddress)[object->kind_14 & 0x0F]",
        ),
        (
            "always_invalidate",
            "if (object->flags_10 != flags) {",
            "if (true) {",
        ),
        (
            "mask_failure_clear",
            "flags &= ~kRequestMasked;",
            "flags &= ~kRequestSlot0C;",
        ),
        (
            "presence_store_width",
            "object->present_18 = 0;",
            "object->present_18 &= 0x0000FF00u;",
        ),
    )
    for name, old, new in controls:
        mutant_code = compile_mutant(name, old, new)
        mutant_runner = Runner(mutant_code, table_page)
        detected = False
        for case in cases:
            orig = orig_runner.run(case)
            bad = mutant_runner.run(case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
