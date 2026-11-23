#!/usr/bin/env python3
"""Differential test for script_vm_func_0027b100 (0x0027b100) using Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the script_vm_func_0027b100
body, resolves its three direct calls to deterministic stubs, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * final r0 (when the last executed slot issues a draw), continuation PC, SP,
    and the callee-saved r4-r11 values;
  * the ordered call log: every sine/cosine input and every 0x00267420 draw with
    r0 plus all seven s-register float arguments as exact bit patterns;
  * the full placement-slot page, screen-state page and context pointer page
    (the routine must not write memory);
  * any emulated write outside the private stack.

Coverage: all-inactive, each behaviour selector (2, 7, 9, 10, 11, 15, 16, 17),
unknown selectors, selector re-read after a draw, the 0x0049F91C == 4 / +4 == 1
suppression matrix, zero/negative/large/NaN/+-inf positions and angles, and the
24-slot loop bound with every slot active.

Negative controls mutate the bob radius, the column offset and the slot count;
each mutant must be detected by the same case set.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0027b100"

FUNC_ADDR = 0x0027B100
FUNC_SIZE = 804
SYMBOL = "script_vm_func_0027b100"

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00100000  # covers the function and every stub below 0x2F0000
CONTEXT_ADDR = 0x00440000
CONTEXT_SIZE = 0x00010000
SCREEN_ADDR = 0x00490000
SCREEN_SIZE = 0x00020000
SLOT_ADDR = 0x00710000
SLOT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

CONTEXT_SLOT_OFFSET = 0x7E70   # 0x00447E70 -> ObjectLoadContext*
SCREEN_STATE_OFFSET = 0xF91C   # 0x0049F91C: two shared state words

SLOT_STRIDE = 0x48
SLOT_COUNT = 24
SLOTS_OFFSET = 0x14

# Direct-call targets, stubbed at their pinned addresses.
STUB_SIN = 0x0028277C
STUB_COS = 0x00282600
STUB_DRAW = 0x00267420

STUB_NAMES = {
    STUB_SIN: "sin_0028277c",
    STUB_COS: "script_vm_func_00282600",
    STUB_DRAW: "battle_func_00267420",
}

DRAW_R0 = 0x26742000

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


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def round_f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if SYMBOL in name or "0027b100" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"{SYMBOL} not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    targets = {
        "script_vm_func_0028277c": STUB_SIN,
        "sin_0028277c": STUB_SIN,
        "script_vm_func_00282600": STUB_COS,
        "battle_func_00267420": STUB_DRAW,
    }
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for symbol, address in targets.items():
            if rel.symbol_name == symbol or symbol in rel.symbol_name:
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
    return bytes(code)


def compile_candidate(source: Path = SOURCE, suffix: str = "leaf_batch45_b") -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / f"{suffix}.o"
    result = compile_tu_armv6k(source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, f"mutant_{name}")


# --------------------------------------------------------------------- fixtures
def slot_bytes(index: int, case: dict) -> bytes:
    """Build one 0x48-byte slot; padding carries a detectable sentinel."""
    buf = bytearray([0xA5] * SLOT_STRIDE)
    for offset in range(SLOT_STRIDE):
        buf[offset] = (0x80 | index) & 0xFF if offset >= 0x28 else 0xA5
    buf[0x00] = case.get("enabled", 0) & 0xFF
    struct.pack_into("<f", buf, 0x04, case.get("x", 0.0))
    struct.pack_into("<f", buf, 0x08, case.get("y", 0.0))
    struct.pack_into("<f", buf, 0x0C, case.get("z", 0.0))
    struct.pack_into("<f", buf, 0x10, case.get("pad10", 0.0))
    struct.pack_into("<f", buf, 0x14, case.get("pad14", 0.0))
    struct.pack_into("<f", buf, 0x18, case.get("pad18", 0.0))
    struct.pack_into("<f", buf, 0x1C, case.get("angle", 0.0))
    struct.pack_into("<I", buf, 0x20, case.get("field20", 0x20202020))
    struct.pack_into("<I", buf, 0x24, case.get("kind", 0) & 0xFFFFFFFF)
    return bytes(buf)


def build_slot_page(case: dict) -> bytes:
    page = bytearray([0x5A] * SLOT_SIZE)
    for index in range(SLOT_COUNT):
        spec = case.get("slots", {}).get(index)
        payload = slot_bytes(index, spec if spec is not None else {})
        base = SLOTS_OFFSET + index * SLOT_STRIDE
        page[base : base + SLOT_STRIDE] = payload
    return bytes(page)


def build_screen(case: dict) -> bytes:
    page = bytearray([0x5A] * SCREEN_SIZE)
    struct.pack_into(
        "<II",
        page,
        SCREEN_STATE_OFFSET,
        case.get("screen0", 0) & 0xFFFFFFFF,
        case.get("screen1", 0) & 0xFFFFFFFF,
    )
    return bytes(page)


def build_context(case: dict) -> bytes:
    page = bytearray([0x5A] * CONTEXT_SIZE)
    struct.pack_into("<I", page, CONTEXT_SLOT_OFFSET, SLOT_ADDR)
    return bytes(page)


class B100Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CONTEXT_ADDR, CONTEXT_SIZE)
        self.uc.mem_map(SCREEN_ADDR, SCREEN_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Enable CP10/CP11 (VFP) so vpush/vldr/vmla translate instead of
        # raising UC_ERR_INSN_INVALID.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.draw_count = 0

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _read_s(self, register: int) -> int:
        return self.uc.reg_read(register) & 0xFFFFFFFF

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        if address == STUB_SIN:
            argument = bits_f32(self._read_s(arm.UC_ARM_REG_S0))
            self.call_log.append(("sin", self._read_s(arm.UC_ARM_REG_S0)))
            result = round_f32(1.5 * argument - 0.25)
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(result))
        elif address == STUB_COS:
            argument = bits_f32(self._read_s(arm.UC_ARM_REG_S0))
            self.call_log.append(("cos", self._read_s(arm.UC_ARM_REG_S0)))
            result = round_f32(-0.75 * argument + 2.0)
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(result))
        elif address == STUB_DRAW:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            floats = tuple(
                self._read_s(getattr(arm, f"UC_ARM_REG_S{i}")) for i in range(7)
            )
            self.call_log.append(("draw", r0 & 0xFFFFFFFF, floats))
            self.draw_count += 1
            uc.reg_write(arm.UC_ARM_REG_R0, DRAW_R0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.draw_count = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CONTEXT_ADDR, build_context(case))
        self.uc.mem_write(SCREEN_ADDR, build_screen(case))
        self.uc.mem_write(SLOT_ADDR, build_slot_page(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0) & 0xFFFFFFFF,
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register) & 0xFFFFFFFF
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "draw_count": self.draw_count,
            "memory": {
                "slots": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
                "screen": bytes(self.uc.mem_read(SCREEN_ADDR, SCREEN_SIZE)),
                "context": bytes(self.uc.mem_read(CONTEXT_ADDR, CONTEXT_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict, compare_ret: bool) -> list[str]:
    problems = []
    keys = ["pc", "sp", "callee_saved", "call_log", "draw_count"]
    if compare_ret:
        keys.append("ret")
    for key in keys:
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for name, value in orig["memory"].items():
        if value != cand["memory"][name]:
            problems.append(f"fixture {name} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "screen0": 0,
        "screen1": 0,
        "slots": {},
        "compare_ret": False,
    }
    case.update(overrides)
    return case


def slot(**fields) -> dict:
    return fields


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- no active slot: the whole loop is gated off.
    cases.append(base_case("all slots inactive"))

    # --- every active flag width.
    for enabled in (0x01, 0x7F, 0x80, 0xFF):
        cases.append(
            base_case(
                f"enabled byte 0x{enabled:02x} kind 15",
                slots={0: slot(enabled=enabled, kind=15)},
            )
        )

    # --- every handled selector with distinct positions and angle.
    for kind in (2, 7, 9, 10, 11, 15, 16, 17):
        cases.append(
            base_case(
                f"kind {kind}",
                slots={
                    5: slot(
                        enabled=1,
                        x=101.5,
                        y=-202.25,
                        z=303.75,
                        angle=45.0,
                        kind=kind,
                    )
                },
            )
        )

    # --- unhandled selectors must not draw.
    for kind in (0, 1, 3, 4, 5, 6, 8, 12, 13, 14, 18, 0x7FFFFFFF,
                 0x80000000, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"unhandled kind 0x{kind:08x}",
                slots={0: slot(enabled=1, x=1.0, y=2.0, z=3.0, angle=10.0,
                               kind=kind)},
            )
        )

    # --- suppression matrix for kinds 2 and 10 (checked before both cases).
    for kind in (2, 10):
        for screen0, screen1 in (
            (0x00000004, 0x00000001),  # suppressed
            (0x00000004, 0x00000000),  # not suppressed
            (0x00000003, 0x00000001),  # not suppressed
            (0x00000004, 0x00000002),  # not suppressed
            (0xFFFFFFFF, 0xFFFFFFFF),
            (0x00000000, 0x00000000),
        ):
            cases.append(
                base_case(
                    f"kind {kind} screen 0x{screen0:08x}/0x{screen1:08x}",
                    screen0=screen0,
                    screen1=screen1,
                    slots={0: slot(enabled=1, x=5.0, y=6.0, z=7.0,
                                   angle=-30.0, kind=kind)},
                )
            )
        # A suppressed 2/10 must not block other selectors in later slots.
        cases.append(
            base_case(
                f"kind {kind} suppressed then kind 17",
                screen0=0x00000004,
                screen1=0x00000001,
                slots={
                    0: slot(enabled=1, kind=kind),
                    1: slot(enabled=1, x=1.0, y=1.0, z=1.0, angle=1.0,
                            kind=17),
                },
            )
        )

    # --- selector re-read after a draw: 15 then 17 in the same slot is
    # impossible (one id), but a draw must not disturb later slots.
    cases.append(
        base_case(
            "draw then inactive then draw",
            slots={
                0: slot(enabled=1, x=10.0, y=20.0, z=30.0, angle=5.0, kind=15),
                1: slot(enabled=0, x=1.0, y=2.0, z=3.0, angle=4.0, kind=17),
                2: slot(enabled=1, x=-10.0, y=-20.0, z=-30.0, angle=-5.0,
                        kind=17),
            },
        )
    )

    # --- signed, zero, boundary and non-finite float inputs.
    special_floats = (
        ("zeros", 0.0, 0.0, 0.0, 0.0),
        ("negative", -123.5, -456.25, -789.125, -90.0),
        ("negative zero", -0.0, -0.0, -0.0, -0.0),
        ("large", 3.0e38, -3.0e38, 1.0e30, 359.999),
        ("tiny", 1.0e-40, -1.0e-40, 1.0e-30, 1.0e-8),
        ("inf", float("inf"), float("-inf"), 1.0, 180.0),
        ("nan", float("nan"), 1.0, 2.0, 3.0),
    )
    for kind in (2, 7, 10, 15, 17):
        for name, x, y, z, angle in special_floats:
            cases.append(
                base_case(
                    f"kind {kind} floats {name}",
                    slots={0: slot(enabled=1, x=x, y=y, z=z, angle=angle,
                                   kind=kind)},
                )
            )

    # --- full 24-slot sweep: every slot active, cycling selectors.  Slot 23
    # draws last, so r0 is the deterministic draw sentinel in both runs.
    cycle = (2, 7, 9, 10, 11, 15, 16, 17, 33)
    slots = {}
    for index in range(SLOT_COUNT):
        slots[index] = slot(
            enabled=1,
            x=float(index) + 0.5,
            y=float(-index) - 0.25,
            z=float(index) * 2.0,
            angle=float(index) * 11.25,
            kind=cycle[index % len(cycle)],
        )
    cases.append(
        base_case("all 24 slots active", slots=slots, compare_ret=True)
    )

    # --- only the last slot active: exercises the loop bound exactly.
    cases.append(
        base_case(
            "only slot 23 active",
            slots={23: slot(enabled=1, x=1.0, y=2.0, z=3.0, angle=4.0,
                            kind=16)},
            compare_ret=True,
        )
    )
    cases.append(
        base_case(
            "only slot 23 active kind 2",
            slots={23: slot(enabled=1, x=1.0, y=2.0, z=3.0, angle=4.0,
                            kind=2)},
            compare_ret=True,
        )
    )

    # --- 24 draws from kind 17, verifying no off-by-one extra iteration.
    full = {
        index: slot(enabled=1, x=float(index), y=0.0, z=0.0, angle=0.0,
                    kind=17)
        for index in range(SLOT_COUNT)
    }
    cases.append(base_case("24 kind 17 draws", slots=full, compare_ret=True))

    return cases


def run_one(code: bytes, case: dict, compare_ret: bool) -> dict:
    # A fresh machine per run: Unicorn keeps translated blocks keyed by address,
    # so reusing a page for a different code image can execute stale opcodes.
    return B100Runner().run(code, case)


def run_case_set(orig_code, cand_code, cases) -> tuple[int, int]:
    passed = 0
    total_calls = 0
    for case in cases:
        orig = run_one(orig_code, case, case["compare_ret"])
        cand = run_one(cand_code, case, case["compare_ret"])
        problems = compare(orig, cand, case["compare_ret"])
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        total_calls += len(orig["call_log"])
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed, total_calls


def main() -> None:
    print("Testing script_vm_func_0027b100 (0x0027b100)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed, total_calls = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("bob_radius", "constexpr f32 kBobRadius = 20.0f;",
         "constexpr f32 kBobRadius = 21.0f;"),
        ("column_offset", "constexpr f32 kColumnOffset = -17.5f;",
         "constexpr f32 kColumnOffset = -17.0f;"),
        ("slot_count", "constexpr s32 kSlotCount = 0x18;",
         "constexpr s32 kSlotCount = 0x17;"),
        ("suppress_state",
         "screen_state[0] == 4u && screen_state[1] == 1u",
         "screen_state[0] == 5u && screen_state[1] == 1u"),
    ):
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = run_one(orig_code, case, case["compare_ret"])
            bad = run_one(mutant_code, case, case["compare_ret"])
            if compare(orig, bad, case["compare_ret"]):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED "
          f"({total_calls} logged calls).")


if __name__ == "__main__":
    main()
