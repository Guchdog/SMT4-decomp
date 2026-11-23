#!/usr/bin/env python3
"""Differential test for func_002313ec (0x002313ec, 456 B) using Unicorn ARM.

Compiles `src/engine/leaf_batch41_c.cpp`, extracts the `func_002313ec` body and
runs the pinned original (`extracted/exefs/code.bin`) against the candidate in
separate Unicorn ARM machines with identical fixtures.  The function has no
direct calls; its only callees are the three overlay flush callbacks loaded from
`*(void**)(slot + 0x1C)`, so those are replaced with deterministic stubs that
log the slot index, `r0` (the value just stored), `r1` (the callback address)
and the stack pointer at the `blx`.

Compared on every case:
  * continuation PC, final SP and the callee-saved r4-r11;
  * the ordered callback log (address read from memory, so both sides use the
    same stub), including the callback's r0/r1/SP;
  * every emulated write outside the private stack frame, in order;
  * the full initial overlay object, a second redirect target object, and the
    0x0044EA00 global pointer word.

`func_002313ec` is a `void` helper, so the caller-visible return value is absent.
r0 is compared unless the third slot's flush callback ran, because in that tail
path the original leaves the stored value in r0 while the candidate zeroes it
(and the caller at 0x0022D994 ignores r0 entirely).

Coverage: every horizontal/vertical clamp branch and its exact 0/320/240
boundaries, negative widths/heights that stay inside the screen, signed 32-bit
wrap boundaries (0x80000000, 0x7FFFFFFF), slot depths 0/1/3, dirty/non-dirty
bytes, matching and non-matching pending values, and callbacks that redirect the
0x0044EA00 base pointer so the per-slot reload is exercised.  Negative controls
mutate both clamp limits, the slot-1 constant, the packed field shift, the
dirty-byte clear, the slot-2 pending comparison and the base-pointer reload.
"""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

from unicorn import (
    UC_ARCH_ARM,
    UC_HOOK_CODE,
    UC_HOOK_MEM_WRITE,
    UC_MODE_ARM,
    Uc,
)
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R4,
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_R7,
    UC_ARM_REG_R8,
    UC_ARM_REG_R9,
    UC_ARM_REG_R10,
    UC_ARM_REG_R11,
    UC_ARM_REG_SP,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = ROOT / "src" / "engine" / "leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_002313ec"

FUNC_ADDR = 0x002313EC
FUNC_SIZE = 456
FUNC_NAME = "func_002313ec"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000  # includes the 0x0044EA00 global word
STUB_BASE = 0x000F1000
STUB_SIZE = 0x1000
STACK_BASE = 0x08000000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100
OBJ_A = 0x00600000
OBJ_B = 0x00610000
OBJ_SIZE = 0x00004000
HALT_ADDR = 0x90000000

GLOBAL_44EA00 = 0x0044EA00

SLOT_OFFSETS = (0x130C, 0x132C, 0x134C)
VALUE_OFFSET = 0x08
DIRTY_OFFSET = 0x18
FLUSH_OFFSET = 0x1C

# One distinct flush stub per slot, plus a redirecting variant per slot.
SLOT_STUBS = {slot: STUB_BASE + 0x40 * slot for slot in range(3)}
REDIRECT_STUBS = {slot: STUB_BASE + 0x40 * slot + 0x10 for slot in range(3)}

CALLEE_SAVED = {
    "r4": UC_ARM_REG_R4,
    "r5": UC_ARM_REG_R5,
    "r6": UC_ARM_REG_R6,
    "r7": UC_ARM_REG_R7,
    "r8": UC_ARM_REG_R8,
    "r9": UC_ARM_REG_R9,
    "r10": UC_ARM_REG_R10,
    "r11": UC_ARM_REG_R11,
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

BX_LR = struct.pack("<I", 0xE12FFF1E)


def get_orig_bytes() -> bytes:
    with open(CODE_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def extract_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = None
    for name, value in funcs.items():
        if FUNC_NAME in name:
            entry = value
            break
    if entry is None:
        raise RuntimeError(f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}")
    code, relocs = entry
    if relocs:
        raise RuntimeError(
            f"unexpected relocations in {FUNC_NAME}: "
            f"{[(r.relocation_type, r.symbol_name) for r in relocs]}"
        )
    return code


def compile_candidate(cpp_text: str) -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUT_DIR) as td:
        td_path = Path(td)
        src = td_path / "cand.cpp"
        obj = td_path / "cand.o"
        src.write_text(cpp_text, encoding="utf-8")
        result = compile_tu_armv6k(src, obj, ROOT)
        if result.returncode != 0:
            raise RuntimeError(f"Candidate compilation failed: {result.stderr}")
        return extract_candidate(obj)


def build_object(case: dict, prefix: str) -> bytes:
    buf = bytearray(OBJ_SIZE)
    for slot, base in enumerate(SLOT_OFFSETS):
        depth = case.get(f"{prefix}_depth_{slot}", 0)
        struct.pack_into("<I", buf, base, depth)
        values = case.get(f"{prefix}_values_{slot}", [0, 0, 0, 0])
        for index, value in enumerate(values):
            struct.pack_into("<I", buf, base + VALUE_OFFSET + 4 * index,
                             value & 0xFFFFFFFF)
        buf[base + DIRTY_OFFSET] = case.get(f"{prefix}_dirty_{slot}", 0) & 0xFF
        redirect = case.get(f"{prefix}_redirect_{slot}", False)
        stub = REDIRECT_STUBS[slot] if redirect else SLOT_STUBS[slot]
        struct.pack_into("<I", buf, base + FLUSH_OFFSET, stub)
    return bytes(buf)


def value2_for(x: int, y: int, w: int, h: int) -> int:
    """Expected packed slot-2 value for an interior (unclamped) rectangle."""
    right = 320 - (x + w)
    bottom = 240 - (y + h)
    return (right & 0xFFFFFFFF) | ((bottom & 0xFFFFFFFF) << 16)


def value3_for(w: int, h: int) -> int:
    return (w & 0xFFFFFFFF) | ((h & 0xFFFFFFFF) << 16)


class Runner:
    def __init__(self) -> None:
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_map(STUB_BASE, STUB_SIZE)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(OBJ_A, OBJ_SIZE)
        self.uc.mem_map(OBJ_B, OBJ_SIZE)
        self.uc.mem_map(HALT_ADDR, 0x1000)

        for address in list(SLOT_STUBS.values()) + list(REDIRECT_STUBS.values()):
            self.uc.mem_write(address, BX_LR)
            self.uc.hook_add(
                UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(UC_HOOK_CODE, self._on_halt, begin=HALT_ADDR,
                         end=HALT_ADDR)
        self.uc.hook_add(UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []

    def _on_halt(self, uc, address, size, user_data) -> None:
        uc.emu_stop()

    @staticmethod
    def _slot_of(address: int) -> tuple[int, bool]:
        for slot in range(3):
            if address == SLOT_STUBS[slot]:
                return slot, False
            if address == REDIRECT_STUBS[slot]:
                return slot, True
        raise AssertionError(f"unexpected stub 0x{address:08x}")

    def _on_stub(self, uc, address, size, user_data) -> None:
        slot, redirect = self._slot_of(address)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        sp = uc.reg_read(UC_ARM_REG_SP)
        self.call_log.append(
            ("redirect" if redirect else "flush", slot, r0, r1, sp)
        )
        if redirect:
            # Redirect every later slot to the second overlay object.
            uc.mem_write(GLOBAL_44EA00, struct.pack("<I", OBJ_B))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_BASE <= address < STACK_BASE + STACK_SIZE:
            return
        self.writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.uc.mem_write(FUNC_ADDR, code)
        # Fresh global pointer and both overlay objects for this run.
        self.uc.mem_write(GLOBAL_44EA00, struct.pack("<I", OBJ_A))
        self.uc.mem_write(OBJ_A, build_object(case, "a"))
        self.uc.mem_write(OBJ_B, build_object(case, "b"))
        self.uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        self.uc.reg_write(UC_ARM_REG_LR, HALT_ADDR)
        self.uc.reg_write(UC_ARM_REG_R0, case["x"] & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM_REG_R1, case["y"] & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM_REG_R2, case["w"] & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM_REG_R3, case["h"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, HALT_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "r0": self.uc.reg_read(UC_ARM_REG_R0),
            "pc": self.uc.reg_read(UC_ARM_REG_PC),
            "sp": self.uc.reg_read(UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": list(self.writes),
            "obj_a": bytes(self.uc.mem_read(OBJ_A, OBJ_SIZE)),
            "obj_b": bytes(self.uc.mem_read(OBJ_B, OBJ_SIZE)),
            "global": bytes(self.uc.mem_read(GLOBAL_44EA00, 4)),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "call_log", "writes"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("obj_a", "obj_b", "global"):
        if orig[key] != cand[key]:
            problems.append(f"{key} memory differs")
    # void helper: r0 is caller-saved; ignore only the tail where the third
    # callback fires (see module docstring).
    third_flushed = any(entry[1] == 2 for entry in orig["call_log"])
    if not third_flushed and orig["r0"] != cand["r0"]:
        problems.append(f"r0:\n    orig=0x{orig['r0']:08x}\n    cand=0x{cand['r0']:08x}")
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    def add(name: str, x: int, y: int, w: int, h: int, **extra) -> None:
        case = {"name": name, "x": x, "y": y, "w": w, "h": h}
        case.update(extra)
        cases.append(case)

    # --- horizontal clamp branches
    add("interior", 10, 20, 30, 40)
    add("x_plus_w_negative", -100, 20, 50, 40)
    add("x_plus_w_negative_exact", -50, 20, 49, 40)
    add("x_negative_w_partial", -20, 20, 50, 40)
    add("x_negative_sum_zero", -50, 20, 50, 40)
    add("x_negative_minus_one", -1, 20, 1, 40)
    add("x_negative_large_width", -5, 20, 0x7FFFFFFF, 40)
    add("x_above_screen", 321, 20, 10, 40)
    add("x_at_screen_edge", 320, 20, 0, 40)
    add("x_above_screen_zero_w", 0x7FFFFFFF, 20, 0, 40)
    add("x_plus_w_over", 300, 20, 50, 40)
    add("x_plus_w_exact_screen", 100, 20, 220, 40)
    add("x_plus_w_one_over", 100, 20, 221, 40)
    add("negative_width_inside", 100, 20, -50, 40)
    add("negative_width_zero_sum", 100, 20, -100, 40)
    add("negative_width_outside", 0, 20, -1, 40)
    add("x_wrap_positive", 0x7FFFFFFF, 20, 1, 40)
    add("x_min_int", -0x80000000, 20, 0, 40)
    add("both_huge_positive", 0x7FFFFFFF, 20, 0x7FFFFFFF, 40)
    add("x_min_int_plus_minus_one", -0x80000000, 20, -1, 40)
    add("zero_rectangle", 0, 0, 0, 0)

    # --- vertical clamp branches (horizontal interior)
    add("y_plus_h_negative", 10, -100, 30, 50)
    add("y_plus_h_negative_exact", 10, -50, 30, 49)
    add("y_negative_h_partial", 10, -20, 30, 50)
    add("y_negative_sum_zero", 10, -50, 30, 50)
    add("y_negative_minus_one", 10, -1, 30, 1)
    add("y_negative_large_height", 10, -5, 30, 0x7FFFFFFF)
    add("y_above_screen", 10, 241, 30, 5)
    add("y_at_screen_edge", 10, 240, 30, 0)
    add("y_plus_h_over", 10, 230, 30, 20)
    add("y_plus_h_exact_screen", 10, 140, 30, 100)
    add("y_plus_h_one_over", 10, 140, 30, 101)
    add("negative_height_inside", 10, 100, 30, -50)
    add("negative_height_zero_sum", 10, 100, 30, -100)
    add("height_wrap_positive", 10, 0x7FFFFFFF, 30, 1)
    add("y_min_int", 10, -0x80000000, 30, 0)
    add("both_huge_positive_y", 10, 0x7FFFFFFF, 30, 0x7FFFFFFF)

    # --- combined extremes
    add("both_min_int", -0x80000000, -0x80000000, 0, 0)
    add("both_negative_out", -300, -300, 50, 50)
    add("both_negative_inside", -10, -10, 300, 200)
    add("both_over", 400, 300, 50, 50)
    add("negative_w_h_inside", 50, 50, -10, -10)
    add("right_bottom_zero", 320, 240, 0, 0)

    # --- slot state: depths, dirty bytes, matching pending values.
    v2 = value2_for(10, 20, 30, 40)
    v3 = value3_for(30, 40)
    add("all_slots_skip", 10, 20, 30, 40,
        a_values_0=[3, 0, 0, 0], a_dirty_0=0,
        a_values_1=[v2, 0, 0, 0], a_dirty_1=0,
        a_values_2=[v3, 0, 0, 0], a_dirty_2=0)
    add("slot0_skip_only", 10, 20, 30, 40,
        a_values_0=[3, 0, 0, 0], a_dirty_0=0)
    add("slot0_dirty_force", 10, 20, 30, 40,
        a_values_0=[3, 0, 0, 0], a_dirty_0=1)
    add("slot1_skip_only", 10, 20, 30, 40,
        a_values_1=[v2, 0, 0, 0], a_dirty_1=0)
    add("slot1_dirty_force", 10, 20, 30, 40,
        a_values_1=[v2, 0, 0, 0], a_dirty_1=1)
    add("slot2_skip_only", 10, 20, 30, 40,
        a_values_2=[v3, 0, 0, 0], a_dirty_2=0)
    add("slot2_dirty_force", 10, 20, 30, 40,
        a_values_2=[v3, 0, 0, 0], a_dirty_2=1)
    add("slot2_mismatch_high_word", 10, 20, 30, 40,
        a_values_2=[(v3 ^ 0xFFFF0000) & 0xFFFFFFFF, 0, 0, 0], a_dirty_2=0)
    add("slot1_mismatch_low_word", 10, 20, 30, 40,
        a_values_1=[(v2 ^ 0x1) & 0xFFFFFFFF, 0, 0, 0], a_dirty_1=0)
    add("slot0_previous_two", 10, 20, 30, 40,
        a_values_0=[2, 0, 0, 0], a_dirty_0=0)
    add("all_dirty", 10, 20, 30, 40,
        a_dirty_0=1, a_dirty_1=1, a_dirty_2=1)

    for depth in (1, 2, 3):
        add(f"depth_{depth}", 10, 20, 30, 40,
            a_depth_0=depth, a_depth_1=depth, a_depth_2=depth,
            a_values_0=[0, 0, 0, 0], a_values_1=[0, 0, 0, 0],
            a_values_2=[0, 0, 0, 0])

    # --- callbacks that redirect the 0x0044EA00 base pointer.
    add("redirect_at_slot0", 10, 20, 30, 40,
        a_redirect_0=True, a_dirty_0=1)
    add("redirect_at_slot1", 10, 20, 30, 40,
        a_redirect_1=True, a_dirty_1=1)
    add("redirect_at_slot2", 10, 20, 30, 40,
        a_redirect_2=True, a_dirty_2=1)
    add("redirect_at_slot0_clamped", 300, 230, 50, 20,
        a_redirect_0=True, a_dirty_0=1)

    return cases


def main() -> int:
    print(f"Testing {FUNC_NAME} (0x{FUNC_ADDR:08x})...")
    orig_code = get_orig_bytes()
    cpp_text = SRC_CPP.read_text(encoding="utf-8")
    cand_code = compile_candidate(cpp_text)
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

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
            return 1
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} callbacks)")

    print("\nNegative controls:")
    mutants = [
        ("x_limit", "static_cast<s32>(static_cast<u32>(x) + static_cast<u32>(w)) > 0x140",
         "static_cast<s32>(static_cast<u32>(x) + static_cast<u32>(w)) > 0x141"),
        ("y_limit", "static_cast<s32>(static_cast<u32>(y) + static_cast<u32>(h)) > 0xF0",
         "static_cast<s32>(static_cast<u32>(y) + static_cast<u32>(h)) > 0xF1"),
        ("slot0_constant", "*pending = 3u;", "*pending = 2u;"),
        ("packed_shift", "(static_cast<u32>(bottom) << 16)",
         "(static_cast<u32>(bottom) << 15)"),
        ("dirty_clear", "        base[kSlot2Offset + kSlotDirtyOffset] = 0u;",
         "        base[kSlot2Offset + kSlotDirtyOffset] = 1u;"),
        ("slot2_compare", "previous2 != value2", "previous2 != (value2 ^ 0x1u)"),
        ("base_reload",
         "    // The original reloads the overlay base pointer before each slot.\n"
         "    base = *reinterpret_cast<u8* const*>(kOverlayGlobal);",
         "    // mutation: keep the previous base pointer"),
    ]
    for name, old, new in mutants:
        if cpp_text.count(old) != 1:
            raise RuntimeError(
                f"mutation anchor {name} occurs {cpp_text.count(old)} times"
            )
        mutant = compile_candidate(cpp_text.replace(old, new))
        caught = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant, case)
            if compare(orig, bad):
                caught = True
                break
        if not caught:
            print(f"  [FAIL] {name} mutant was not detected")
            return 1
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
