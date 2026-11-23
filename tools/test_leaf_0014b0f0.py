#!/usr/bin/env python3
"""Differential test for func_0014b0f0 (0x0014B0F0) using Unicorn ARM.

The routine receives r0 = address of a word that holds the resolved slot
container (the caller 0x0013F68C builds that word and passes its address), an
unused r1, and r2/`tag`, which is forwarded unchanged to func_002b5318.

It walks the six container slot words in the order 0x0C, 0x10, 0x00, 0x04, 0x08,
0x14.  Each slot word is a self-relative offset added to its own address; a zero
word or a first hop that wraps to zero skips the slot.  The first hop must then
expose a second self-relative offset at +0x08 (same wrapped-zero rule).  The
second-hop child is accepted only when its first word has bit 30 (0x40000000)
set, otherwise a null child is queried.  func_002b5318(child, tag) is called
first; only when its result has bit 31 clear is the plain, unfiltered child
resolved a second time, stored in a stack word and passed by address to
func_002b52c8.  Both results are OR-ed into the return value.

Both callees are stubbed deterministically at their original addresses and every
call is logged:

  func_002b5318(child, tag):
      child == 0  -> 0x80000000 when tag is even, 0x00000000 when tag is odd
      child != 0  -> 0x80000004 when (*(u32*)(child+4) & 0x80000000), else
                     0x40000004
  func_002b52c8(&child):
      value of child, then 0x00000100 when non-zero, else 0x80000008

Compared outputs are return r0, continuation PC, final SP, callee-saved r4-r11,
the ordered call log (arguments included), the whole node/container/child world,
and every write outside the private stack and that world.
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
OUT_DIR = ROOT / "build/test_leaf_0014b0f0"

FUNC_ADDR = 0x0014B0F0
FUNC_SIZE = 984

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00100000  # 0x00100000..0x00200000, holds the body + literals
STUB_PAGE = 0x002B5000  # holds the two stubbed callees
STUB_PAGE_SIZE = 0x1000
STUB_QUERY = 0x002B5318
STUB_DISPATCH = 0x002B52C8

WORLD_ADDR = 0x00600000
WORLD_SIZE = 0x00020000
SLOTREF_ADDR = WORLD_ADDR + 0x0000  # r0 points here; word holds the container
CONTAINER_ADDR = WORLD_ADDR + 0x1000
ALT_CONTAINER_ADDR = WORLD_ADDR + 0x2000
HOP1_ZONE = WORLD_ADDR + 0x4000  # each first-hop object lives here
CAND_ZONE = WORLD_ADDR + 0x8000  # each second-hop child lives here
ALT_HOP1_ZONE = WORLD_ADDR + 0x6000  # distinct objects for the alternate container
ALT_CAND_ZONE = WORLD_ADDR + 0xA000
STRIDE = 0x100

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Slot order exactly as the original walks it.
SLOT_ORDER = (0x0C, 0x10, 0x00, 0x04, 0x08, 0x14)
SLOT_NAMES = {
    0x00: "slot00",
    0x04: "slot04",
    0x08: "slot08",
    0x0C: "slot0C",
    0x10: "slot10",
    0x14: "slot14",
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
    entry = None
    for name, value in funcs.items():
        if "0014b0f0" in name:
            entry = value
            break
    if entry is None:
        raise RuntimeError(f"func_0014b0f0 not found in {obj_file}: {sorted(funcs)}")
    code, relocs = entry
    code = bytearray(code)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            symbol = rel.symbol_name or ""
            if "002b5318" in symbol:
                target = STUB_QUERY
            elif "002b52c8" in symbol:
                target = STUB_DISPATCH
            else:
                raise RuntimeError(f"unexpected call relocation target {symbol!r}")
            pc = FUNC_ADDR + rel.offset + 8
            disp = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | (disp & 0x00FFFFFF))
        else:
            raise RuntimeError(
                "unexpected relocation "
                f"{(rel.offset, rel.relocation_type, rel.symbol_name)}"
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
PATTERN_STACK = b"\x00" * STACK_SIZE

ABSENT = "absent"
FIRST_WRAP = "first_wrap"
NESTED_ABSENT = "nested_absent"
NESTED_WRAP = "nested_wrap"
PRESENT = "present"
HOP_STATES = (ABSENT, FIRST_WRAP, NESTED_ABSENT, NESTED_WRAP, PRESENT)


def hop1_address(index: int, base: int = HOP1_ZONE) -> int:
    return base + index * STRIDE


def cand_address(index: int, base: int = CAND_ZONE) -> int:
    return base + index * STRIDE


def write_container(page: bytearray, container: int, case: dict,
                    hop1_base: int = HOP1_ZONE,
                    cand_base: int = CAND_ZONE) -> None:
    container_offset = container - WORLD_ADDR
    states = case.get("slots", {})
    for index, offset in enumerate(SLOT_ORDER):
        state = states.get(offset, PRESENT)
        hop1 = hop1_address(index, hop1_base)
        if state == ABSENT:
            relative = 0
        elif state == FIRST_WRAP:
            relative = (-(container + offset)) & 0xFFFFFFFF
        else:
            relative = (hop1 - (container + offset)) & 0xFFFFFFFF
        struct.pack_into("<I", page, container_offset + offset, relative)

        if state in (NESTED_ABSENT, NESTED_WRAP, PRESENT):
            hop1_offset = hop1 - WORLD_ADDR
            if state == NESTED_ABSENT:
                next_relative = 0
            elif state == NESTED_WRAP:
                next_relative = (-(hop1 + 8)) & 0xFFFFFFFF
            else:
                next_relative = (cand_address(index, cand_base) - (hop1 + 8)) & 0xFFFFFFFF
            struct.pack_into("<I", page, hop1_offset + 8, next_relative)

        if state == PRESENT:
            cand_offset = cand_address(index, cand_base) - WORLD_ADDR
            keep = case.get("keep_bit30", {}).get(offset, True)
            word0 = case.get("word0", {}).get(offset, 0)
            word0 = (word0 & ~0x40000000) | (0x40000000 if keep else 0)
            struct.pack_into("<I", page, cand_offset, word0)
            negative = case.get("query_negative", {}).get(offset, False)
            word4 = case.get("word4", {}).get(offset, 0)
            word4 = (word4 & 0x7FFFFFFF) | (0x80000000 if negative else 0)
            struct.pack_into("<I", page, cand_offset + 4, word4)


def build_world(case: dict) -> bytes:
    page = bytearray(PATTERN_WORLD)
    struct.pack_into("<I", page, SLOTREF_ADDR - WORLD_ADDR,
                     case.get("slotref", CONTAINER_ADDR) & 0xFFFFFFFF)
    write_container(page, CONTAINER_ADDR, case)
    if case.get("alternate") is not None:
        alt = dict(case["alternate"])
        alt.setdefault("slots", {offset: ABSENT for offset in SLOT_ORDER})
        write_container(page, ALT_CONTAINER_ADDR, alt,
                        ALT_HOP1_ZONE, ALT_CAND_ZONE)
    return bytes(page)


class Runner:
    """One Unicorn machine; fixtures are rebuilt identically for every case."""

    def __init__(self, code: bytes) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(STUB_PAGE, STUB_PAGE_SIZE)
        self.uc.mem_map(WORLD_ADDR, WORLD_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(FUNC_ADDR, code)
        bx_lr = struct.pack("<I", 0xE12FFF1E)
        self.uc.mem_write(STUB_QUERY, bx_lr)
        self.uc.mem_write(STUB_DISPATCH, bx_lr)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_query,
                         begin=STUB_QUERY, end=STUB_QUERY)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_dispatch,
                         begin=STUB_DISPATCH, end=STUB_DISPATCH)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.mutated = False

    @staticmethod
    def _read_u32(uc, address: int) -> int:
        return struct.unpack("<I", uc.mem_read(address, 4))[0]

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_query(self, uc, address, size, user_data) -> None:
        child = uc.reg_read(arm.UC_ARM_REG_R0)
        tag = uc.reg_read(arm.UC_ARM_REG_R1)
        if child == 0:
            result = 0x00000000 if (tag & 1) else 0x80000000
        else:
            word4 = self._read_u32(uc, child + 4)
            result = 0x80000004 if (word4 & 0x80000000) else 0x40000004
        self.call_log.append(("query", child, tag, result))
        uc.reg_write(arm.UC_ARM_REG_R0, result)
        if self.case.get("mutate_slotref") and not self.mutated:
            self.mutated = True
            uc.mem_write(SLOTREF_ADDR,
                         struct.pack("<I", self.case["mutate_slotref"]))

    def _on_dispatch(self, uc, address, size, user_data) -> None:
        pointer = uc.reg_read(arm.UC_ARM_REG_R0)
        child = self._read_u32(uc, pointer)
        result = 0x00000100 if child != 0 else 0x80000008
        self.call_log.append(("dispatch", child, result))
        uc.reg_write(arm.UC_ARM_REG_R0, result)

    def run(self, case: dict) -> dict:
        self.case = case
        self.mutated = False
        self.call_log = []
        self.writes = []
        self.uc.mem_write(WORLD_ADDR, build_world(case))
        self.uc.mem_write(STACK_ADDR, PATTERN_STACK)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_PC, FUNC_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SLOTREF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("tag", 0))
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
            "call_log": list(self.call_log),
            "world": bytes(self.uc.mem_read(WORLD_ADDR, WORLD_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["world"] != cand["world"]:
        first = next(
            index
            for index, (left, right) in enumerate(zip(orig["world"], cand["world"]))
            if left != right
        )
        problems.append(
            f"world memory differs first at +0x{first:x}: "
            f"orig=0x{orig['world'][first]:02x} cand=0x{cand['world'][first]:02x}"
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
        "slots": {offset: PRESENT for offset in SLOT_ORDER},
        "tag": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- every slot present / every slot absent
    cases.append(base_case("all present, all positive"))
    cases.append(base_case("all absent", slots={o: ABSENT for o in SLOT_ORDER}))
    cases.append(
        base_case("all first-hop wrap",
                  slots={o: FIRST_WRAP for o in SLOT_ORDER})
    )
    cases.append(
        base_case("all nested absent",
                  slots={o: NESTED_ABSENT for o in SLOT_ORDER})
    )
    cases.append(
        base_case("all nested wrap",
                  slots={o: NESTED_WRAP for o in SLOT_ORDER})
    )

    # --- each slot against every hop outcome
    for offset in SLOT_ORDER:
        for state in HOP_STATES:
            slots = {o: PRESENT for o in SLOT_ORDER}
            slots[offset] = state
            cases.append(
                base_case(f"{SLOT_NAMES[offset]} {state}", slots=slots)
            )

    # --- bit-30 filter and query-sign matrix, per slot
    for offset in SLOT_ORDER:
        for keep in (True, False):
            for negative in (False, True):
                for tag in (0, 1):
                    cases.append(
                        base_case(
                            f"{SLOT_NAMES[offset]} keep={keep} "
                            f"neg={negative} tag={tag}",
                            keep_bit30={offset: keep},
                            query_negative={offset: negative},
                            tag=tag,
                        )
                    )

    # --- the null-child query path: filtered child, non-negative result
    for tag in (0, 1, 2, 3):
        slots = {o: PRESENT for o in SLOT_ORDER}
        cases.append(
            base_case(
                f"all filtered, tag={tag}",
                slots=slots,
                keep_bit30={o: False for o in SLOT_ORDER},
                tag=tag,
            )
        )

    # --- mixed keep/negative patterns across all six slots
    patterns = (
        (True, False, True, False, True, False),
        (False, True, False, True, False, True),
        (True, True, False, False, True, True),
        (False, False, False, False, False, False),
    )
    for pattern_index, pattern in enumerate(patterns):
        for negative_pattern in (0, 1):
            keep = {}
            negative = {}
            for index, offset in enumerate(SLOT_ORDER):
                keep[offset] = pattern[index]
                negative[offset] = bool((index + negative_pattern) % 2)
            cases.append(
                base_case(
                    f"mixed pattern {pattern_index}/{negative_pattern}",
                    keep_bit30=keep,
                    query_negative=negative,
                    tag=negative_pattern,
                )
            )

    # --- non-zero low words at the child (bit 30 must be the only filter)
    for offset in SLOT_ORDER:
        for word0 in (0xFFFFFFFF, 0x80000000, 0x00000001, 0x3FFFFFFF):
            cases.append(
                base_case(
                    f"{SLOT_NAMES[offset]} word0 0x{word0:08x}",
                    word0={offset: word0},
                )
            )

    # --- the container pointer is re-read between and within slot groups
    cases.append(
        base_case(
            "slotref rewritten after first query",
            tag=1,
            keep_bit30={o: False for o in SLOT_ORDER},
            mutate_slotref=ALT_CONTAINER_ADDR,
            alternate={"slots": {o: PRESENT for o in SLOT_ORDER}},
        )
    )
    cases.append(
        base_case(
            "slotref rewritten to alt with slots",
            mutate_slotref=ALT_CONTAINER_ADDR,
            alternate={
                "slots": {o: PRESENT for o in SLOT_ORDER},
                "keep_bit30": {o: False for o in SLOT_ORDER},
            },
            tag=1,
        )
    )
    cases.append(
        base_case(
            "slotref rewritten with only first slot present",
            keep_bit30={o: False for o in SLOT_ORDER},
            tag=1,
            mutate_slotref=ALT_CONTAINER_ADDR,
            alternate={
                "slots": {
                    o: (NESTED_ABSENT if o == 0x0C else ABSENT)
                    for o in SLOT_ORDER
                }
            },
        )
    )

    # --- no slot resolves at all, plus a zero tag and a high tag
    cases.append(
        base_case("all absent tag 0xffffffff",
                  slots={o: ABSENT for o in SLOT_ORDER}, tag=0xFFFFFFFF)
    )
    cases.append(base_case("all present tag 0xffffffff", tag=0xFFFFFFFF))
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
    print("Testing func_0014b0f0 (0x0014B0F0)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (relocated calls).")

    orig_runner = Runner(orig_code)
    cand_runner = Runner(cand_code)
    cases = make_cases()
    passed = run_case_set(orig_runner, cand_runner, cases)
    print(f"  [PASS] {passed} differential cases")

    print("\nNegative controls:")
    controls = (
        (
            "filter_bit",
            "& 0x40000000u) == 0",
            "& 0x20000000u) == 0",
        ),
        (
            "filtered_dispatch",
            "u32 child = second_hop(first_hop(*reinterpret_cast<const u32*>(slot_ref),\n"
            "                                         slot_offset));",
            "u32 child = candidate;",
        ),
        (
            "guard_condition",
            "if (first == 0) {",
            "if (first == 0xFFFFFFFFu) {",
        ),
        (
            "drop_status",
            "result |= status;",
            "result |= 0;",
        ),
        (
            "second_hop_sum",
            "return first + 8 + relative;",
            "return relative;",
        ),
        (
            "always_dispatch",
            "if ((status & 0x80000000u) == 0) {",
            "if (true) {",
        ),
        (
            "slot_order",
            "inspect_slot(slot_ref, 0x0C, tag, result);\n"
            "    func_0014b0f0_detail::inspect_slot(slot_ref, 0x10, tag, result);",
            "inspect_slot(slot_ref, 0x10, tag, result);\n"
            "    func_0014b0f0_detail::inspect_slot(slot_ref, 0x0C, tag, result);",
        ),
        (
            "first_hop_sum",
            "return container + slot_offset + relative;",
            "return container + slot_offset;",
        ),
        (
            "cached_container",
            "u32 child = second_hop(first_hop(*reinterpret_cast<const u32*>(slot_ref),",
            "u32 child = second_hop(first_hop(container,",
        ),
        (
            "second_hop_offset",
            "*reinterpret_cast<const u32*>(first + 8);",
            "*reinterpret_cast<const u32*>(first + 0x0C);",
        ),
    )
    for name, old, new in controls:
        mutant_code = compile_mutant(name, old, new)
        mutant_runner = Runner(mutant_code)
        detected = False
        for case in cases:
            orig = orig_runner.run(case)
            try:
                bad = mutant_runner.run(case)
            except Exception:
                # A guard mutation can turn a skipped slot into a bad load; a
                # fault where the original completes is itself a divergence.
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
