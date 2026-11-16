#!/usr/bin/env python3
"""Differential test for script_vm_func_001e0cdc (0x001e0cdc) using Unicorn.

Compiles src/engine/leaf_batch34_c.cpp, extracts the reconstructed body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log, including both register arguments of every helper
    (none of the helpers takes an architected stack argument);
  * the full 24 MiB data region, which contains the script block and every
    140-byte slot reachable from the signed coordinate/source boundaries;
  * any direct write outside the data region or the private stack.

Fixture knobs:
  * base coordinate (+0x218C s16), source coordinate (+0x218E s16);
  * mode flag (+0x2184 u32, all zero/non-zero forms);
  * first/second count arguments, including values whose low halfword differs
    from the full 32-bit sign test;
  * optional helper side effects that rewrite a block field after a chosen call,
    to exercise every reload point in the original instruction stream.

Coverage: zero/positive/negative clamped counts, both clamp directions,
signed-halfword boundaries, both first-block flag sets, zero/non-zero/low-word
second counts, full second-loop and negative third-loop bounds, and helper
mutations of the count, coordinate and source fields.  Negative controls mutate
the low/high markers, a slot offset, the clamp limit, the third-loop selector,
and the two loop-entry conditions; every mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001e0cdc"

FUNC_ADDR = 0x001E0CDC
FUNC_SIZE = 804

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # function plus all three original helper addresses
DATA_ADDR = 0x00400000
DATA_SIZE = 0x01800000  # 24 MiB: covers +-9.2 MiB of slot arithmetic
OBJECT_ADDR = 0x00E00000
OBJECT_OFF = OBJECT_ADDR - DATA_ADDR
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets.  Stubs are placed at the same addresses so the
# original bytes and the relocated candidate reach identical code.
STUB_2B90E0 = 0x002B90E0
STUB_2BF030 = 0x002BF030
STUB_2BF9E8 = 0x002BF9E8

STUB_NAMES = {
    STUB_2B90E0: "script_vm_func_002b90e0",
    STUB_2BF030: "camp_func_002bf030",
    STUB_2BF9E8: "script_vm_func_002bf9e8",
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

# Distinct non-zero pattern so every store and every untouched byte is
# observable in the full-region comparison.
_PATTERN = bytes((index * 73 + 19) & 0xFF for index in range(4096))
BASE_IMAGE = (_PATTERN * (DATA_SIZE // len(_PATTERN) + 1))[:DATA_SIZE]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    entry = None
    for name, value in funcs.items():
        if "001e0cdc" in name:
            entry = value
            break
    if entry is None:
        raise RuntimeError(
            f"script_vm_func_001e0cdc not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = entry
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
        opcode = original & 0xFF000000
        if opcode in (0xFA000000, 0xFB000000):
            raise RuntimeError(f"unexpected BLX call to {rel.symbol_name}")
        struct.pack_into(
            "<I", code, rel.offset, opcode | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


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

    funcs = extract_elf_functions_detailed(obj_file)
    entry = next(value for key, value in funcs.items() if "001e0cdc" in key)
    code_raw, relocs = entry
    code = bytearray(code_raw)
    for rel in relocs:
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        original = struct.unpack_from("<I", code, rel.offset)[0]
        opcode = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset,
            opcode | (((target - pc) >> 2) & 0x00FFFFFF),
        )
    return bytes(code)


def build_image(case: dict) -> bytes:
    image = bytearray(BASE_IMAGE)

    def put_h(offset: int, value: int) -> None:
        struct.pack_into("<h", image, OBJECT_OFF + offset, value)

    def put_u16(offset: int, value: int) -> None:
        struct.pack_into("<H", image, OBJECT_OFF + offset, value)

    def put_u32(offset: int, value: int) -> None:
        struct.pack_into("<I", image, OBJECT_OFF + offset, value & 0xFFFFFFFF)

    put_h(0x218C, case.get("coordinate", 0))
    put_h(0x218E, case.get("source", 0))
    put_u16(0x2190, case.get("initial_count", 0x5A5A))
    put_u16(0x2192, case.get("initial_second", 0x5A5A))
    put_u32(0x2184, case.get("flag", 0))
    put_u32(0x217C, 0xDEADBEEF)
    put_u32(0x2180, 0xDEADBEEF)
    return bytes(image)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address in STUB_NAMES:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.mutation_counts = {"slot": 0, "camp": 0}
        self.mutation_done = {"slot": False, "camp": False}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, name: str, *args) -> None:
        self.call_log.append((name, args + self._stack_words(0)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _maybe_mutate(self, kind: str) -> None:
        spec = self.case.get(f"{kind}_mutate")
        if spec is None:
            return
        self.mutation_counts[kind] += 1
        if self.mutation_counts[kind] != spec["after"]:
            return
        if self.mutation_done[kind]:
            return
        self.mutation_done[kind] = True
        address = OBJECT_ADDR + spec["offset"]
        width = spec["width"]
        value = spec["value"]
        if width == "h":
            payload = struct.pack("<h", value)
        elif width == "H":
            payload = struct.pack("<H", value)
        elif width == "I":
            payload = struct.pack("<I", value & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by case construction
            raise AssertionError(f"bad mutation width {width!r}")
        self.uc.mem_write(address, payload)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_2B90E0:
            # Real helper: add r0,#4; mvn r2,#0; stm r0,{r1,r2}.
            self._log(STUB_NAMES[address], r0, r1)
            uc.mem_write(
                r0 + 4, struct.pack("<II", r1 & 0xFFFFFFFF, 0xFFFFFFFF)
            )
            self._maybe_mutate("slot")
        elif address == STUB_2BF030:
            self._log(STUB_NAMES[address], r0, r1)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("camp_return", 0xCAFE1234)
            )
            self._maybe_mutate("camp")
        elif address == STUB_2BF9E8:
            self._log(STUB_NAMES[address], r0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.mutation_counts = {"slot": 0, "camp": 0}
        self.mutation_done = {"slot": False, "camp": False}

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_image(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("first", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("second", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=20_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_data = DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_data and not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "memory": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def first_difference(left: bytes, right: bytes) -> int | None:
    if left == right:
        return None
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return index
    return min(len(left), len(right))


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        for index, (left, right) in enumerate(
            zip(orig["call_log"], cand["call_log"])
        ):
            if left != right:
                problems.append(
                    f"call_log first diff at {index}:\n"
                    f"    orig={left!r}\n    cand={right!r}"
                )
                break
        else:
            problems.append(
                f"call_log length: orig={len(orig['call_log'])} "
                f"cand={len(cand['call_log'])}"
            )
    difference = first_difference(orig["memory"], cand["memory"])
    if difference is not None:
        problems.append(
            f"memory differs at data+0x{difference:x}: "
            f"orig=0x{orig['memory'][difference]:02x} "
            f"cand=0x{cand['memory'][difference]:02x}"
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def case(name: str, **overrides) -> dict:
    fixture = {
        "name": name,
        "coordinate": 0,
        "source": 0,
        "flag": 0,
        "first": 0,
        "second": 0,
        "camp_return": 0xCAFE1234,
    }
    fixture.update(overrides)
    return fixture


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- clamp and zero/positive/negative count paths (second <= 0)
    cases.append(case("zero count"))
    cases.append(case("count 5 clear flag", first=5))
    cases.append(case("count 3 set flag", first=3, flag=1))
    cases.append(case("flag 2 is non-zero", first=2, flag=2))
    cases.append(case("flag all ones", first=2, flag=0xFFFFFFFF))
    cases.append(case("upper clamp 5", coordinate=5, first=20, flag=1))
    cases.append(case("lower clamp 5", coordinate=-5, first=2))
    cases.append(case("lower clamp to zero", coordinate=0, first=-5))
    cases.append(case("coordinate 10 boundary", coordinate=10, first=0))
    cases.append(case("coordinate 9 plus 1", coordinate=9, first=1))
    cases.append(case("coordinate 10 plus 1 clamps", coordinate=10, first=1))
    cases.append(case("coordinate -1 plus 1", coordinate=-1, first=1))
    cases.append(case("coordinate -2 plus 1", coordinate=-2, first=1))
    cases.append(case("negative count -1", coordinate=11, first=0))
    cases.append(case("negative count -10", coordinate=20, first=0, flag=1))
    cases.append(case("high halfword first", coordinate=3, first=0x00010000))
    cases.append(case("low-halfword -1", coordinate=3, first=0xFFFF))
    cases.append(case("high sign bit first", coordinate=0, first=0xFFFF8000))
    cases.append(case("maximum signed first", coordinate=0, first=0x7FFFFFFF))
    cases.append(case("coordinate -32768 zero count", coordinate=-32768,
                      first=0x10000))
    cases.append(case("sum 9 stays below upper clamp", coordinate=5, first=4))

    # --- first block: second > 0, stored loop count positive/zero/negative
    cases.append(case("second 1 count 5", first=5, second=1))
    cases.append(case("second 2 flag set source -3", first=0, second=2,
                      flag=1, source=-3))
    cases.append(case("second 3 flag clear", first=10, coordinate=-5, second=3))
    cases.append(case("second high word stored zero", first=5, second=0x10000))
    cases.append(case("second 0xffff stored -1", first=5, second=0xFFFF))
    cases.append(case("second -1 skips first block", first=5, second=-1))
    cases.append(case("second max stored -1", first=5, second=0x7FFFFFFF))
    cases.append(case("second min skips first block", first=5,
                      second=-0x80000000))
    cases.append(case("second 0x10001 stored 1", first=3, second=0x10001))
    cases.append(case("source -32768", first=0, second=1, source=-32768))
    cases.append(case("source 32767", first=0, second=1, source=32767))
    cases.append(case("source -32768 coord 10", first=0, coordinate=10,
                      second=1, source=-32768))
    cases.append(case("combined coordinate/source boundaries", first=0x10000,
                      coordinate=-32768, second=1, source=32767,
                      flag=1))

    # --- helper side effects: every reload point in the original stream
    cases.append(case("camp truncates second count", second=3,
                      camp_mutate={"after": 1, "offset": 0x2192,
                                   "width": "h", "value": 1}))
    cases.append(case("camp truncates slot count", first=5,
                      camp_mutate={"after": 1, "offset": 0x2190,
                                   "width": "h", "value": 2}))
    cases.append(case("slot sets count -1", first=5,
                      slot_mutate={"after": 1, "offset": 0x2190,
                                   "width": "h", "value": -1}))
    cases.append(case("camp sets count -1 in third loop", coordinate=20,
                      camp_mutate={"after": 1, "offset": 0x2190,
                                   "width": "h", "value": -1}))
    cases.append(case("camp moves coordinate", first=2,
                      camp_mutate={"after": 1, "offset": 0x218C,
                                   "width": "h", "value": 100}))
    cases.append(case("slot moves source", second=2,
                      slot_mutate={"after": 1, "offset": 0x218E,
                                   "width": "h", "value": 7}))
    cases.append(case("slot moves coordinate", first=2,
                      slot_mutate={"after": 1, "offset": 0x218C,
                                   "width": "h", "value": 3}))
    cases.append(case("camp returns zero", first=2, camp_return=0))
    cases.append(case("camp returns nonzero", first=2,
                      camp_return=0xDEADBEEF))

    # --- full negative-walk boundary: coordinate +32767 clamps to -32757
    cases.append(case("coordinate 32767 negative walk", coordinate=32767,
                      first=0, second=0))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for fixture in cases:
        orig = Runner().run(orig_code, fixture)
        cand = Runner().run(cand_code, fixture)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {fixture['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {fixture['name']}  "
            f"({len(orig['call_log'])} calls)"
        )
    return passed


def main() -> None:
    print("Testing script_vm_func_001e0cdc (0x001e0cdc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutations = (
        ("low_marker", "constexpr u32 kMarkerLow = 0xfa6u;",
         "constexpr u32 kMarkerLow = 0xfa5u;"),
        ("tail_slot_offset", "slot + 0x1600, kTailMarkerSet",
         "slot + 0x1604, kTailMarkerSet"),
        ("clamp_limit", "coordinate > 10) {", "coordinate > 8) {"),
        ("third_loop_selector",
         "leaf34_camp_002bf030(slot + 0xa84, 9);",
         "leaf34_camp_002bf030(slot + 0xa84, 8);"),
        ("second_entry", "if (second > 0) {", "if (second >= 0) {"),
        ("count_entry", "if (count > 0) {", "if (count >= 0) {"),
    )
    for name, old, new in mutations:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for fixture in cases:
            orig = Runner().run(orig_code, fixture)
            bad = Runner().run(mutant_code, fixture)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
