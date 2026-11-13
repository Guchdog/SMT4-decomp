#!/usr/bin/env python3
"""Differential test for camp_func_0029cee4 (0x0029cee4) using Unicorn ARM.

Compiles src/engine/leaf_batch33_c.cpp, extracts the camp_func_0029cee4 body,
resolves its four direct calls to deterministic stubs at the original branch
targets, and runs the pinned original (extracted/exefs/code.bin) against the
compiled candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with the arguments of every helper call;
  * the complete 0x4000-byte panel page (both objects and the spare filler),
    the table page holding 0x0043E188, and the stack outside the dead frame;
  * every write outside the panel page and the private stack.

Coverage: both animation-limit flags alone and together and neither, the exact
wide and narrow clamp boundaries, signed zero/negative sums, 32-bit modular
wrap-around, every ending phase (0-4), close request zero and non-zero, row
index 11 versus other rows, live versus dead presented and default objects, a
null default slot, a default slot that the widget stub replaces during the
call, and both widget modes.  Six recompiled source mutants are detected.
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
FUNC_ADDR = 0x0029CEE4
FUNC_SIZE = 412
TU_PATH = ROOT / "src/engine/leaf_batch33_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0029cee4"

# The pinned image spans 0x00100000..0x00477000 and therefore contains the
# function, both helper targets, and the 0x0043E188 object table.
IMAGE_ADDR = 0x00100000
IMAGE_SIZE = 0x00377000
PANEL_ADDR = 0x00600000
PANEL_SIZE = 0x00004000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

TABLE_ADDR = 0x0043E188
TABLE_PAGE = 0x0043E000
TABLE_PAGE_SIZE = 0x00001000
DEFAULT_SLOT = TABLE_ADDR + 4
PRESENTED_SLOT = TABLE_ADDR + 8

PRESENTED_OFF = 0x000
DEFAULT_OFF = 0x1000
ALT_OFF = 0x2000

# Presented-object fields (ARM evidence only).
STATE = 0x08
ROW_INDEX = 0x09
HIDDEN_FLAG = 0x35
STEP_TIMER = 0x64
DISPLAYED = 0x6C
STEP = 0x70
STEP_RESET = 0x74
ACCUMULATED = 0x78
PHASE = 0x7C
WIDE_STEP_FLAG = 0x7D
NARROW_STEP_FLAG = 0x7E
MODE_FLAG = 0x7F

STUB_2BF030 = 0x002BF030
STUB_2B8D24 = 0x002B8D24
STUB_BY_SYMBOL = {
    "camp_func_002bf030": STUB_2BF030,
    "battle_func_002b8d24": STUB_2B8D24,
}
STUB_NAMES = {
    STUB_2BF030: "CampPanel_SetWidgetMode",
    STUB_2B8D24: "BattleActor_ReleaseRow",
}

WIDE_LIMIT = 999999999
NARROW_LIMIT = 99

CALLEE_SAVED = [
    arm.UC_ARM_REG_R4,
    arm.UC_ARM_REG_R5,
    arm.UC_ARM_REG_R6,
    arm.UC_ARM_REG_R7,
    arm.UC_ARM_REG_R8,
    arm.UC_ARM_REG_R9,
    arm.UC_ARM_REG_R10,
    arm.UC_ARM_REG_R11,
]


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as image:
        image.seek(FUNC_ADDR - 0x00100000)
        return image.read(FUNC_SIZE)


def image_bytes() -> bytes:
    return ORIG_BIN.read_bytes()


def sign_extend_24(value: int) -> int:
    return value - 0x1000000 if value & 0x800000 else value


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get("camp_func_0029cee4")
    if entry is None:
        raise RuntimeError(
            "camp_func_0029cee4 not found in object: " + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            inst = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(inst & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            disp = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset, (inst & 0xFF000000) | (disp & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code)


def compile_candidate() -> bytes:
    return compile_variant(TU_PATH, OUT_DIR / "leaf_batch33_c.o")


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = TU_PATH.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def object_spec(**overrides) -> dict:
    spec = {
        "state": 0x00,
        "row_index": 0x00,
        "hidden_flag": 0x77,
        "step_timer": 0xEE,
        "displayed": 0xDEADBEEF,
        "step": 0,
        "step_reset": 0xCC,
        "accumulated": 0,
        "phase": 0x00,
        "wide_step": 0x00,
        "narrow_step": 0x00,
        "mode_flag": 0x00,
    }
    spec.update(overrides)
    return spec


def put_object(page: bytearray, offset: int, spec: dict) -> None:
    page[offset + STATE] = spec["state"] & 0xFF
    page[offset + ROW_INDEX] = spec["row_index"] & 0xFF
    page[offset + HIDDEN_FLAG] = spec["hidden_flag"] & 0xFF
    page[offset + STEP_TIMER] = spec["step_timer"] & 0xFF
    page[offset + STEP_RESET] = spec["step_reset"] & 0xFF
    page[offset + PHASE] = spec["phase"] & 0xFF
    page[offset + WIDE_STEP_FLAG] = spec["wide_step"] & 0xFF
    page[offset + NARROW_STEP_FLAG] = spec["narrow_step"] & 0xFF
    page[offset + MODE_FLAG] = spec["mode_flag"] & 0xFF
    for field, key in (
        (STEP_TIMER, "step_timer"),
        (DISPLAYED, "displayed"),
        (STEP, "step"),
        (STEP_RESET, "step_reset"),
        (ACCUMULATED, "accumulated"),
    ):
        struct.pack_into("<I", page, offset + field, spec[key] & 0xFFFFFFFF)


def build_panel(case: dict) -> bytes:
    page = bytearray(PANEL_SIZE)
    for index in range(PANEL_SIZE):
        page[index] = (index * 37 + 11) & 0xFF
    put_object(page, PRESENTED_OFF, case["presented"])
    put_object(page, DEFAULT_OFF, case["default"])
    put_object(page, ALT_OFF, case["alt"])
    return bytes(page)


def build_table(case: dict) -> bytes:
    page = bytearray(TABLE_PAGE_SIZE)
    for index in range(TABLE_PAGE_SIZE):
        page[index] = (index * 13 + 5) & 0xFF
    present = case.get("presented_slot")
    if present is None:
        present = PANEL_ADDR + PRESENTED_OFF
    default = case.get("default_slot")
    if default is None:
        default = PANEL_ADDR + DEFAULT_OFF
    struct.pack_into("<I", page, PRESENTED_SLOT - TABLE_PAGE, present)
    struct.pack_into("<I", page, DEFAULT_SLOT - TABLE_PAGE, default)
    return bytes(page)


class Machine:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_SIZE)
        self.uc.mem_map(PANEL_ADDR, PANEL_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(IMAGE_ADDR, image_bytes())

        self.orig_code = get_orig_bytes()
        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self._install_stubs()

    def _install_stubs(self) -> None:
        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address, hook in (
            (STUB_2BF030, self._on_widget_mode),
            (STUB_2B8D24, self._on_release_row),
        ):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # -- stub bodies ------------------------------------------------------
    def _on_widget_mode(self, uc, address, size, user_data) -> None:
        widget = uc.reg_read(arm.UC_ARM_REG_R0)
        mode = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("CampPanel_SetWidgetMode", widget, mode))
        replacement = self.case.get("post_call_default")
        if replacement is not None:
            # 0x002BF030 may publish the panel; the original re-reads the default
            # slot after this call, so the replacement must be visible.
            uc.mem_write(DEFAULT_SLOT, struct.pack("<I", replacement))
        uc.reg_write(arm.UC_ARM_REG_R0, 0x2BF03000)

    def _on_release_row(self, uc, address, size, user_data) -> None:
        obj = uc.reg_read(arm.UC_ARM_REG_R0)
        row = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("BattleActor_ReleaseRow", obj, row))
        # The original ignores the return value; a distinctive pattern proves it.
        uc.reg_write(arm.UC_ARM_REG_R0, 0x8D240000 | (row & 0xFFFF))

    # -- execution --------------------------------------------------------
    def run(self, candidate: bytes | None, case: dict) -> dict:
        uc = self.uc
        self.case = case
        self.call_log = []
        self.writes = []

        uc.mem_write(IMAGE_ADDR, image_bytes())
        # The image rewrite also restores the original bytes at both helper
        # targets, so the stubs have to be reinstalled every run.
        for address in STUB_NAMES:
            uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
        uc.mem_write(PANEL_ADDR, build_panel(case))
        uc.mem_write(TABLE_PAGE, build_table(case))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, self.orig_code if candidate is None else candidate)
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, case["close_request"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, 0xA0000001)
        uc.reg_write(arm.UC_ARM_REG_R2, 0xA0000002)
        uc.reg_write(arm.UC_ARM_REG_R3, 0xA0000003)
        for index, reg in enumerate(CALLEE_SAVED):
            uc.reg_write(reg, 0x11110000 + index * 0x1111)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as exc:  # pragma: no cover - diagnostic path
            raise RuntimeError(
                f"Crash at PC=0x{uc.reg_read(arm.UC_ARM_REG_PC):08x}: {exc}"
            ) from exc
        finally:
            uc.ctl_flush_tb()

        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        unexpected_writes = []
        for address, size, _value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            if PANEL_ADDR <= address < PANEL_ADDR + PANEL_SIZE:
                continue
            if TABLE_PAGE <= address < TABLE_PAGE + TABLE_PAGE_SIZE:
                continue
            unexpected_writes.append((address, size))

        return {
            "call_log": list(self.call_log),
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": sp,
            "callee_saved": [uc.reg_read(reg) for reg in CALLEE_SAVED],
            "panel": bytes(uc.mem_read(PANEL_ADDR, PANEL_SIZE)),
            "table": bytes(uc.mem_read(TABLE_PAGE, TABLE_PAGE_SIZE)),
            "stack_below": bytes(uc.mem_read(STACK_ADDR, sp - 0x40 - STACK_ADDR)),
            "stack_above": bytes(uc.mem_read(sp, STACK_ADDR + STACK_SIZE - sp)),
            "unexpected_writes": unexpected_writes,
        }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def make_case(name: str, presented: dict | None = None, **overrides) -> dict:
    case = {
        "name": name,
        "close_request": 0,
        "presented": presented if presented is not None else object_spec(),
        "default": object_spec(),
        "alt": object_spec(),
    }
    case.update(overrides)
    return case


def build_cases() -> list[dict]:
    cases: list[dict] = []

    # --- animation: which limit flag fires, and the widget request ---------
    cases.append(make_case(
        "phase 3 wide step only",
        object_spec(phase=3, wide_step=1, accumulated=100, step=10),
    ))
    cases.append(make_case(
        "phase 3 narrow step only",
        object_spec(phase=3, narrow_step=1, accumulated=100, step=10),
    ))
    cases.append(make_case(
        "phase 3 both step flags",
        object_spec(phase=3, wide_step=1, narrow_step=1, accumulated=5, step=7),
    ))
    cases.append(make_case(
        "phase 3 both flags, narrow clamps after wide step",
        object_spec(phase=3, wide_step=1, narrow_step=1, accumulated=500, step=10),
    ))
    cases.append(make_case(
        "phase 3 no step flag",
        object_spec(phase=3, accumulated=42, step=8),
    ))
    cases.append(make_case(
        "phase 3 no step flag, close request on closing row",
        object_spec(phase=3, state=1, row_index=11),
        close_request=1,
        default=object_spec(state=1, row_index=5),
    ))
    for phase in (0, 1, 2, 4):
        cases.append(make_case(
            f"phase {phase} no animation",
            object_spec(phase=phase, wide_step=1, narrow_step=1,
                        accumulated=42, step=8),
        ))

    # --- wide clamp boundaries (limit 0x3B9AC9FF) -------------------------
    for accumulated, step in (
        (0, 0),
        (1, 0),
        (999999998, 1),
        (999999999, 1),
        (1000000000, 1),
        (0x7FFFFFFE, 1),
        (0x7FFFFFFF, 0),
        (0x7FFFFFFF, 1),
        (0xFFFFFFFF, 0),
        (1, 0xFFFFFFFE),
        (0x7FFFFFFF, 0x7FFFFFFF),
        (0xFFFFFFFE, 3),
        (12345, -45),
        (0x80000000, 0),
    ):
        cases.append(make_case(
            f"wide acc 0x{accumulated:08x} step 0x{step & 0xFFFFFFFF:08x}",
            object_spec(phase=3, wide_step=1,
                        accumulated=accumulated & 0xFFFFFFFF,
                        step=step & 0xFFFFFFFF),
        ))

    # --- narrow clamp boundaries (limit 99) -------------------------------
    for accumulated, step in (
        (0, 0),
        (98, 1),
        (99, 1),
        (0x7FFFFFFF, 0),
        (0xFFFFFFFF, 0),
        (500, 0),
        (0xFFFFFFFE, 3),
    ):
        cases.append(make_case(
            f"narrow acc 0x{accumulated:08x} step 0x{step & 0xFFFFFFFF:08x}",
            object_spec(phase=3, narrow_step=1,
                        accumulated=accumulated & 0xFFFFFFFF,
                        step=step & 0xFFFFFFFF),
        ))

    # --- dismissal conditions --------------------------------------------
    for phase in (0, 2):
        cases.append(make_case(
            f"dismiss on closing row, phase {phase}",
            object_spec(phase=phase, state=1, row_index=11, mode_flag=0),
            close_request=1,
            default=object_spec(state=1, row_index=5),
        ))
    cases.append(make_case(
        "dismiss with widget mode selected",
        object_spec(phase=0, state=1, row_index=11, mode_flag=1),
        close_request=1,
        default=object_spec(state=1, row_index=5),
    ))
    for mode_flag in (0x80, 0xFF):
        cases.append(make_case(
            f"dismiss mode flag 0x{mode_flag:02x}",
            object_spec(phase=0, state=1, row_index=11, mode_flag=mode_flag),
            close_request=1,
        ))
    for phase in (1, 3, 4):
        cases.append(make_case(
            f"dismiss blocked by phase {phase}",
            object_spec(phase=phase, state=1, row_index=11),
            close_request=1,
            default=object_spec(state=1, row_index=5),
        ))
    cases.append(make_case(
        "close request but other row index",
        object_spec(phase=0, state=1, row_index=10),
        close_request=1,
    ))
    cases.append(make_case(
        "close request but dead presented row",
        object_spec(phase=0, state=0, row_index=11),
        close_request=1,
    ))
    cases.append(make_case(
        "no close request on closing row",
        object_spec(phase=0, state=1, row_index=11),
        close_request=0,
        default=object_spec(state=1, row_index=5),
    ))
    cases.append(make_case(
        "close request 0xffffffff",
        object_spec(phase=0, state=9, row_index=11),
        close_request=0xFFFFFFFF,
        default=object_spec(state=0xFF, row_index=0x11),
    ))
    cases.append(make_case(
        "default slot null",
        object_spec(phase=0, state=1, row_index=11),
        close_request=1,
        default_slot=0,
    ))
    cases.append(make_case(
        "default object dead",
        object_spec(phase=0, state=1, row_index=11),
        close_request=1,
        default=object_spec(state=0, row_index=5),
    ))
    cases.append(make_case(
        "default slot replaced during the widget call",
        object_spec(phase=0, state=1, row_index=11),
        close_request=1,
        default=object_spec(state=1, row_index=5),
        post_call_default=PANEL_ADDR + ALT_OFF,
        alt=object_spec(state=2, row_index=7),
    ))
    cases.append(make_case(
        "default slot cleared during the widget call",
        object_spec(phase=0, state=1, row_index=11),
        close_request=1,
        post_call_default=0,
    ))
    cases.append(make_case(
        "dismiss after animation resets the phase",
        object_spec(phase=3, wide_step=1, state=1, row_index=11,
                    accumulated=250, step=-25),
        close_request=1,
        default=object_spec(state=1, row_index=5),
    ))
    cases.append(make_case(
        "dismiss, displayed and timer preseeded",
        object_spec(phase=1, state=0xFF, row_index=11, displayed=0,
                    step_reset=0x5A5A5A5A, step_timer=0x01020304),
        close_request=1,
        default=object_spec(state=0xFF, row_index=0xFE),
    ))

    return cases


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("r0", "pc", "sp", "callee_saved", "panel", "table",
                "stack_below", "stack_above"):
        if orig[key] != cand[key]:
            problems.append(f"{key} differs")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def run_case_set(machine, orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        res_orig = machine.run(None, case)
        res_cand = machine.run(cand_code, case)
        problems = compare(res_orig, res_cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"(r0={res_orig['r0']}, {len(res_orig['call_log'])} calls)"
        )
    return passed


def main() -> None:
    print("Testing camp_func_0029cee4 (0x0029cee4)...")
    cand = compile_candidate()
    print(
        f"  original: {FUNC_SIZE} B, candidate: {len(cand)} B "
        f"({ORIG_BIN.name} fixture)"
    )

    machine = Machine()
    cases = build_cases()
    passed = run_case_set(machine, machine.orig_code, cand, cases)

    print("\nNegative controls:")
    mutants = [
        ("wide_limit", "kWideValueLimit = 999999999;",
         "kWideValueLimit = 999999998;"),
        ("narrow_limit", "kNarrowValueLimit = 99;", "kNarrowValueLimit = 100;"),
        ("closing_row", "kClosingRowIndex = 0xBu;", "kClosingRowIndex = 0xAu;"),
        ("dismiss_phase_set", "if (phase == 0u || phase == 2u) {",
         "if (phase == 0u || phase == 2u || phase == 1u) {"),
        ("widget_mode", "kWidgetModeWhenFlagSet = 2u;",
         "kWidgetModeWhenFlagSet = 5u;"),
        ("step_sign", "const u32 sum = LoadPanelWord(object, kAccumulatedValueOffset) +",
         "const u32 sum = LoadPanelWord(object, kAccumulatedValueOffset) -"),
    ]
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            res_orig = machine.run(None, case)
            res_mut = machine.run(mutant, case)
            if compare(res_orig, res_mut):
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
