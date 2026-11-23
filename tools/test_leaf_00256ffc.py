#!/usr/bin/env python3
"""Differential test for ui_func_00256ffc (0x00256ffc) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_00256ffc body and
runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn ARM machines with identical fixtures.

The function is a true leaf: no `bl`/`blx`, no indirect call and no read-only
literals outside its own pool word (0.5f).  There is therefore no helper to
stub.

Compared outputs:
  * continuation PC, final SP and callee-saved r4-r11;
  * the entire 64 KiB data page holding the self/state/control/root objects,
    the record array, the texture table, the texture objects and the output
    block (full observable memory);
  * every emulated write outside the private stack, which must stay inside the
    data page.

r0 is excluded on purpose: the function is `void`, and the original leaves the
last sign-extended halfword of record+0x0E in it while the reconstruction's
residue is compiler-dependent.

Coverage: the bit-28 suppression gate, hold > 0 / 0 / negative (including
INT_MIN and INT_MAX), index advance below/at/past the count, the +0x10 wrap
clear versus index reset, unsigned 32-bit wrap around count = 0xFFFFFFFF, the
value-table bit with -1 and table results, every 1/2/3 style flag combination,
signed texture indices (including negative table offsets), signed 16-bit record
boundaries with the arithmetic >>4, zero and extreme texture scales, and
record 0 versus record 1 after a wrap.  Negative controls mutate five constants
/ comparisons and must each be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_00256ffc"

FUNC_ADDR = 0x00256FFC
FUNC_SIZE = 460

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000
DATA_ADDR = 0x00700000
DATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Layout inside the single data page (all offsets are page-relative).
SELF_OFF = 0x1000
STATE_OFF = 0x2000
CONTROL_OFF = 0x3000
ROOT_OFF = 0x4000
OUTPUT_OFF = 0x5000
RECORDS_OFF = 0x6000
TEX_TABLE_OFF = 0x7100
TEXTURES_OFF = 0x7400
VALUE_TABLE_OFF = 0xA000

SELF_ADDR = DATA_ADDR + SELF_OFF
STATE_ADDR = DATA_ADDR + STATE_OFF
CONTROL_ADDR = DATA_ADDR + CONTROL_OFF
ROOT_ADDR = DATA_ADDR + ROOT_OFF
OUTPUT_ADDR = DATA_ADDR + OUTPUT_OFF
RECORDS_ADDR = DATA_ADDR + RECORDS_OFF
TEX_TABLE_ADDR = DATA_ADDR + TEX_TABLE_OFF
TEXTURES_ADDR = DATA_ADDR + TEXTURES_OFF
VALUE_TABLE_ADDR = DATA_ADDR + VALUE_TABLE_OFF

RECORD_STRIDE = 24
RECORD_SLOTS = 8
TEXTURE_SLOTS = 16
TEX_TABLE_MIN_INDEX = -4

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

FILLER = bytes((index * 7 + 3) & 0xFF for index in range(DATA_SIZE))


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00256ffc" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_00256ffc not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    # A correct reconstruction of this leaf has no relocations.  Anything else
    # means the C++ pulled in a call or a pool relocation that the fixture
    # below does not model.
    if relocs:
        raise RuntimeError(
            "unexpected relocations: "
            + ", ".join(f"{rel.symbol_name}:{rel.relocation_type}" for rel in relocs)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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
def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def put_u16(page: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<H", page, offset, value & 0xFFFF)


def put_s16(page: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<h", page, offset, s16(value))


def put_u32(page: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)


def default_record(index: int) -> dict:
    return {
        "x": 0x0100 + index * 0x11,
        "y": -0x0100 - index * 0x13,
        "px": 0x20 + index,
        "py": -0x30 - index,
        "e0": 0x0010 * (index + 1),
        "e1": -0x0010 * (index + 1),
        "e2": 0x0020 * (index + 1),
        "e3": -0x0020 * (index + 1),
        "meta": 0xA1A10000 | index,
        "tex": index,
    }


def build_data(case: dict) -> bytes:
    page = bytearray(FILLER)

    # self
    put_u32(page, SELF_OFF + 0x00, ROOT_ADDR)
    put_u32(page, SELF_OFF + 0x10, STATE_ADDR)
    put_u16(page, SELF_OFF + 0x14, case.get("loop_initial", 0xBEEF))

    # state
    put_u32(page, STATE_OFF + 0x04, case.get("index", 0))
    put_u32(page, STATE_OFF + 0x08, case.get("hold", 0))
    put_u32(page, STATE_OFF + 0x0C, CONTROL_ADDR)
    put_u32(page, STATE_OFF + 0x10, RECORDS_ADDR)

    # control
    put_u32(page, CONTROL_OFF + 0x04, case.get("value_offset", 0x100))
    put_u32(page, CONTROL_OFF + 0x0C, case.get("count", 4))
    put_u32(page, CONTROL_OFF + 0x10, case.get("flags", 0))

    # root: +0x00 is dereferenced into the value-table base; +0x14 is the
    # texture pointer table.
    put_u32(page, ROOT_OFF + 0x00, VALUE_TABLE_ADDR)
    put_u32(page, ROOT_OFF + 0x14, TEX_TABLE_ADDR)
    for offset in range(0, 0x400, 4):
        put_u32(page, VALUE_TABLE_OFF + offset, 0xC0DE0000 ^ offset)

    # records
    overrides = case.get("records", {})
    for index in range(RECORD_SLOTS):
        record = default_record(index)
        record.update(overrides.get(index, {}))
        base = RECORDS_OFF + index * RECORD_STRIDE
        for field, offset in (
            ("x", 0x00), ("y", 0x02), ("px", 0x04), ("py", 0x06),
            ("e0", 0x08), ("e1", 0x0A), ("e2", 0x0C), ("e3", 0x0E),
            ("tex", 0x10),
        ):
            put_s16(page, base + offset, record[field])
        put_u32(page, base + 0x14, record["meta"])

    # texture pointer table (negative entries address earlier words)
    for index in range(TEX_TABLE_MIN_INDEX, TEXTURE_SLOTS):
        slot = index - TEX_TABLE_MIN_INDEX
        put_u32(page, TEX_TABLE_OFF + index * 4,
                TEXTURES_ADDR + slot * 0x100)

    # texture objects: only the two integer scale words matter
    textures = case.get("textures", [])
    for slot in range(TEXTURE_SLOTS):
        base = TEXTURES_OFF + slot * 0x100
        if slot < len(textures):
            scale_u, scale_v = textures[slot]
        else:
            scale_u, scale_v = 16 + slot, 8 - slot
        put_u32(page, base + 0x14, scale_u)
        put_u32(page, base + 0x18, scale_v)

    return bytes(page)


class Runner:
    """Builds a fresh Unicorn machine per run.

    Reusing one machine with different code at the same address is unsafe here:
    Unicorn may keep a translated block for the function after the code bytes
    change, which would silently compare the previous variant.  A new machine
    per run keeps the comparison honest.
    """

    def __init__(self) -> None:
        self.uc = None
        self.writes: list = []

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (size * 8)) - 1)))

    def run(self, code: bytes, case: dict) -> dict:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The function uses VFP (vldmia/vdiv/vstmia), so emulate the 3DS ARM11
        # MPCore and enable CP10/CP11.
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (DATA_ADDR, DATA_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x200)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, OUTPUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        fault = None
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError:  # pragma: no cover - diagnostic path
            fault = self.uc.reg_read(arm.UC_ARM_REG_PC)

        snapshot = bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE))

        unexpected_writes = []
        for address, size, _value in self.writes:
            if (
                DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
                or STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            ):
                continue
            unexpected_writes.append((address, size))

        if fault is not None:
            return {"fault": True, "pc": fault, "data": snapshot}

        return {
            "fault": False,
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "data": snapshot,
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if orig["fault"] != cand["fault"]:
        problems.append(f"fault: orig={orig['fault']} cand={cand['fault']}")
        return problems
    if orig["fault"]:
        if orig["data"] != cand["data"]:
            problems.append("faulting data page differs")
        return problems

    for key in ("pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["data"] != cand["data"]:
        first = next(
            i for i, (a, b) in enumerate(zip(orig["data"], cand["data"])) if a != b
        )
        problems.append(
            f"data page differs first at offset 0x{first:04x}: "
            f"orig=0x{orig['data'][first]:02x} cand=0x{cand['data'][first]:02x}"
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def case(name: str, **overrides) -> dict:
    out = {"name": name}
    out.update(overrides)
    return out


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- bit-28 suppression gate
    cases.append(case("suppress bit 28 alone", flags=0x10000000, index=2, hold=3))
    cases.append(case("suppress with value/style bits",
                      flags=0x90000006, index=1, hold=1))
    cases.append(case("suppress with every other bit",
                      flags=0xEFFFFFFF, index=0, hold=0))

    # --- hold path (index untouched)
    cases.append(case("hold 5 -> 4", hold=5, index=2, count=4))
    cases.append(case("hold 1 -> 0", hold=1, index=3, count=4))
    cases.append(case("hold INT_MAX", hold=0x7FFFFFFF, index=3, count=4))
    cases.append(case("hold INT_MIN takes advance path", hold=-0x80000000,
                      index=0, count=4))

    # --- index advance without wrap
    cases.append(case("advance 0->1", hold=0, index=0, count=4))
    cases.append(case("advance 2->3", hold=-1, index=2, count=4))
    cases.append(case("advance wraps s32 to u32 0x80000000",
                      hold=-0x80000000, index=0x7FFFFFFF, count=0xFFFFFFFF))

    # --- wrap: count <= next
    cases.append(case("wrap at count-1 keeps count-1 and clears +0x14",
                      hold=0, index=3, count=4, flags=0x10))
    cases.append(case("wrap at count-1 resets to 0 without clear",
                      hold=0, index=3, count=4, flags=0x00))
    cases.append(case("index == count wraps to count-1 with clear",
                      hold=0, index=4, count=4, flags=0x10))
    cases.append(case("index > count resets to 0",
                      hold=0, index=9, count=4, flags=0x00))
    cases.append(case("count 0 resets to 0", hold=0, index=0, count=0))
    cases.append(case("count 1 wraps to 0 and clears", hold=0, index=0,
                      count=1, flags=0x10))
    cases.append(case("u32 boundary 0xFFFFFFFE -> 0xFFFFFFFF wraps to 0",
                      hold=0, index=0xFFFFFFFE, count=0xFFFFFFFF, flags=0x00))

    # --- value-table bit and style bits
    cases.append(case("value from table, style 1", flags=0x01, index=1))
    cases.append(case("value -1, style 1", flags=0x00, index=1))
    cases.append(case("value from table, style 2", flags=0x03, index=2))
    cases.append(case("value from table, style 3", flags=0x05, index=2))
    cases.append(case("style 2 wins over style 3", flags=0x07, index=2))
    cases.append(case("style 3 plus wrap clear", flags=0x14, index=3, count=4,
                      hold=0))
    cases.append(case("value table with large offset", flags=0x01,
                      value_offset=0x240, index=3))

    # --- signed texture index
    cases.append(case("texture index -1", records={0: {"tex": -1}}))
    cases.append(case("texture index -4", records={0: {"tex": -4}}))
    cases.append(case("texture index 12", records={0: {"tex": 12}}))

    # --- record selection across a wrap
    cases.append(case("wrap selects record 0, not record 1",
                      hold=0, index=3, count=4, flags=0x00,
                      records={0: {"meta": 0x11110000, "tex": 1},
                               1: {"meta": 0x22220000, "tex": 2}}))
    cases.append(case("no wrap keeps record 1",
                      hold=0, index=0, count=4,
                      records={0: {"meta": 0x11110000},
                               1: {"meta": 0x22220000}}))

    # --- signed halfword boundaries and shifts
    cases.append(case("s16 min/max fields", records={0: {
        "x": 0x7FFF, "y": -0x8000, "px": -0x8000, "py": 0x7FFF,
        "e0": 0x7FFF, "e1": -0x8000, "e2": 0x7FFF, "e3": -0x8000}}))
    cases.append(case("negative shifts round toward -inf", records={0: {
        "e0": -1, "e1": -15, "e2": -16, "e3": -17}}))
    cases.append(case("zero shifts", records={0: {
        "e0": 15, "e1": 16, "e2": -16, "e3": 0}}))

    # --- scale boundaries
    cases.append(case("zero scales yield infinities",
                      records={0: {"e0": 1, "e1": -1, "e2": 1, "e3": -1}},
                      textures=[(0, 0)]))
    cases.append(case("signed scales", textures=[(-2, 3)]))
    cases.append(case("scale INT_MIN / INT_MAX",
                      textures=[(-0x80000000, 0x7FFFFFFF)]))
    cases.append(case("scale -1 / 1 with large edges",
                      records={0: {"e0": 0x7FFF, "e1": -0x8000,
                                   "e2": -0x8000, "e3": 0x7FFF}},
                      textures=[(-1, 1)]))

    return cases


MUTATIONS = [
    ("half_constant",
     "constexpr f32 kHalf = 0.5f;                // pool word at 0x002571C4",
     "constexpr f32 kHalf = 0.25f;               // pool word at 0x002571C4"),
    ("default_value", "    s32 value = -1;", "    s32 value = -2;"),
    ("suppress_bit", "constexpr u32 kFlagSuppress = 0x10000000;",
     "constexpr u32 kFlagSuppress = 0x20000000;"),
    ("style3", "        style = 3;", "        style = 4;"),
    ("wrap_compare", "        if (count <= next) {", "        if (count < next) {"),
]


def main() -> None:
    print("Testing ui_func_00256ffc (0x00256ffc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"  original {len(orig_code)} B, candidate {len(cand_code)} B")

    runner = Runner()
    cases = make_cases()

    failures = 0
    for tc in cases:
        problems = compare(runner.run(orig_code, tc), runner.run(cand_code, tc))
        if problems:
            failures += 1
            print(f"  [FAIL] {tc['name']}")
            for problem in problems:
                print(f"      {problem}")
        else:
            print(f"  [PASS] {tc['name']}")

    print(f"\n{len(cases) - failures}/{len(cases)} differential cases passed")

    mutant_failures = 0
    for name, old, new in MUTATIONS:
        mutant = compile_candidate_mutant(name, old, new)
        detected = False
        for tc in cases:
            if compare(runner.run(orig_code, tc), runner.run(mutant, tc)):
                detected = True
                break
        if detected:
            print(f"  [PASS] negative control '{name}' detected")
        else:
            mutant_failures += 1
            print(f"  [FAIL] negative control '{name}' NOT detected")

    print(f"{len(MUTATIONS) - mutant_failures}/{len(MUTATIONS)} negative controls detected")
    if failures or mutant_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
