#!/usr/bin/env python3
"""Differential test for script_vm_func_0029ccf8 (0x0029CCF8) using Unicorn.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the reconstructed
``script_vm_func_0029ccf8`` body, resolves each direct call to a deterministic
stub placed at the pinned target address, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate in separate Unicorn ARM
machines with identical fixtures.

Compared outputs:
  * final r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log, including every architected register argument, the
    exact 12-byte stack record passed to 0x0029411C and the indirect
    vtable-slot-1 target;
  * full work / manager / view / entity / vtable memory images;
  * every non-stack write, in order.

Coverage: the state-3 early return; sub-menu states 3/9 versus every other
byte; the 0x002A0DD4 view-subobject gate; the null model at each check; the
0x002B8ADC and manager +0x02 gates; a helper clearing the model before the
vtable call; float bit patterns including -0.0, infinity and NaN; the ten-slot
list loop; and a helper retargeting the manager work pointer, which must be
reloaded for the final two stores.

Negative controls mutate the state compare, the sub-menu set, the 1000.0f
lift, the loop bound, the first widget offset, the 0x0029BC1C argument and the
vtable slot index; each mutant must be detected.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm
from unicorn.arm_const import (
    UC_CPU_ARM_11MPCORE,
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0029ccf8"

FUNC_ADDR = 0x0029CCF8
FUNC_SIZE = 484

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
MANAGER_PAGE = 0x0044E000
MANAGER_SIZE = 0x00001000
MANAGER_ADDR = 0x0044E140
VIEW_PAGE = 0x00447000
VIEW_SIZE = 0x00002000
VIEW_WORK_ADDR = 0x00447E88
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00030000
ALT_WORK_ADDR = 0x00520000
ENTITY_ADDR = 0x00600000
ENTITY_SIZE = 0x00001000
VTABLE_ADDR = 0x00601000
VTABLE_SIZE = 0x00001000
VT_SLOT1_ADDR = 0x00602000
VT_SLOT0_ADDR = 0xDEAD0000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2A0DD4 = 0x002A0DD4
STUB_29411C = 0x0029411C
STUB_29BC1C = 0x0029BC1C
STUB_288990 = 0x00288990
STUB_2B8ADC = 0x002B8ADC
STUB_2A7604 = 0x002A7604
STUB_288948 = 0x00288948
STUB_2BDAC0 = 0x002BDAC0
STUB_2BF030 = 0x002BF030

STUB_BY_NAME = {
    "camp_func_002a0dd4": STUB_2A0DD4,
    "ui_func_0029411c": STUB_29411C,
    "camp_func_0029bc1c": STUB_29BC1C,
    "ui_func_00288990": STUB_288990,
    "ui_func_002b8adc": STUB_2B8ADC,
    "script_vm_func_002a7604": STUB_2A7604,
    "camp_func_00288948": STUB_288948,
    "camp_func_002bdac0": STUB_2BDAC0,
    "camp_func_002bf030": STUB_2BF030,
}
STUB_NAMES = {address: name for name, address in STUB_BY_NAME.items()}
STUB_NAMES[VT_SLOT1_ADDR] = "model_vtable_slot_1"
STUB_NAMES[VT_SLOT0_ADDR] = "model_vtable_slot_0"

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

STATE_OFFSET = 0x12DC
SUB_MENU_OFFSET = 0x1E67
MODEL_OFFSET = 0x1E80
PARAMS_OFFSET = 0x1E84
WIDGET_OFFSETS = (0x038C, 0x0418, 0x04A4, 0x0530,
                  0x05BC, 0x0648, 0x06D4, 0x0760)
LIST_STRIDE = 0x8C
LIST_OFFSETS = (0x07EC, 0x0D64)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0029ccf8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_0029ccf8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type != 28:  # R_ARM_CALL
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = STUB_BY_NAME.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        delta = target - pc
        if delta % 4:
            raise RuntimeError(f"unaligned call target 0x{target:08x}")
        displacement = delta >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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
def build_manager(case: dict) -> bytes:
    page = bytearray(MANAGER_SIZE)
    base = MANAGER_ADDR - MANAGER_PAGE
    page[base + 0] = case.get("ref_count", 1) & 0xFF
    page[base + 1] = 0x5A
    page[base + 2] = case.get("flag_02", 0) & 0xFF
    page[base + 3] = 0xA5
    struct.pack_into("<I", page, base + 4, WORK_ADDR)
    return bytes(page)


def build_view(case: dict) -> bytes:
    page = bytearray(VIEW_SIZE)
    offset = VIEW_WORK_ADDR - VIEW_PAGE
    struct.pack_into("<I", page, offset, ENTITY_ADDR)
    # Sentinels the stubbed helpers would touch with their real bodies.
    struct.pack_into("<I", page, offset + 0x134, 0x11223344)
    struct.pack_into("<I", page, offset + 0x194, 0xAABBCCDD)
    return bytes(page)


def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    struct.pack_into("<I", page, STATE_OFFSET, case.get("state", 0) & 0xFFFFFFFF)
    page[SUB_MENU_OFFSET] = case.get("sub", 0) & 0xFF
    struct.pack_into("<I", page, MODEL_OFFSET, case.get("model", ENTITY_ADDR) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PARAMS_OFFSET, case.get("f1e84", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PARAMS_OFFSET + 4,
                     case.get("f1e88_bits", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, PARAMS_OFFSET + 8,
                     case.get("f1e8c_bits", 0) & 0xFFFFFFFF)
    # Fill the reset targets with distinct canaries; the stubs must not touch
    # them and the two final stores are the only writes expected in the area.
    for index, offset in enumerate(WIDGET_OFFSETS):
        page[offset] = 0xC0 | index
    for slot in range(10):
        base = slot * LIST_STRIDE
        page[base + LIST_OFFSETS[0]] = 0xE0 | slot
        page[base + LIST_OFFSETS[1]] = 0x70 | slot
    return bytes(page)


def build_entity(case: dict) -> tuple[bytes, bytes]:
    entity = bytearray(ENTITY_SIZE)
    struct.pack_into("<I", entity, 0, VTABLE_ADDR)
    struct.pack_into("<I", entity, 4, 0xEEEE0004)
    vtable = bytearray(VTABLE_SIZE)
    struct.pack_into("<I", vtable, 0, 0xDEAD0000)
    struct.pack_into("<I", vtable, 4, VT_SLOT1_ADDR)
    struct.pack_into("<I", vtable, 8, 0xDEAD0008)
    return bytes(entity), bytes(vtable)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
        # Enable the VFP coprocessor (CP10/CP11) used by the 0x0029411C record
        # preparation at 0x0029CD4C..0x0029CD68.
        self.uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(MANAGER_PAGE, MANAGER_SIZE)
        self.uc.mem_map(VIEW_PAGE, VIEW_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(ENTITY_ADDR, ENTITY_SIZE)
        self.uc.mem_map(VTABLE_ADDR, VTABLE_SIZE)
        self.uc.mem_map(VT_SLOT1_ADDR, 0x1000)
        self.uc.mem_map(VT_SLOT0_ADDR, 0x1000)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.counts: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES.get(address, hex(address)), args))

    def _maybe_retarget(self, stub_name: str) -> None:
        retarget = self.case.get("retarget")
        if not retarget:
            return
        target_stub, call_index, new_work = retarget
        if target_stub != stub_name:
            return
        count = self.counts.get(stub_name, 0)
        if count == call_index:
            self.uc.mem_write(MANAGER_ADDR + 4, struct.pack("<I", new_work))

    def _maybe_clear_model(self, source: str) -> None:
        if self.case.get("clear_model_at") == source:
            self.uc.mem_write(WORK_ADDR + MODEL_OFFSET, struct.pack("<I", 0))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_2A0DD4:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("view_subobject", 1) & 0xFFFFFFFF)
        elif address == STUB_29411C:
            record = bytes(uc.mem_read(r1, 12))
            self._log(address, r0, record)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x29411000)
        elif address == STUB_29BC1C:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_288990:
            self._log(address, r0)
            self._maybe_clear_model("288990")
        elif address == STUB_2B8ADC:
            self.counts["2b8adc"] = self.counts.get("2b8adc", 0) + 1
            self._log(address)
            self._maybe_clear_model("b8adc")
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("b8adc_result", 1) & 0xFFFFFFFF)
        elif address == STUB_2A7604:
            self._log(address, r0)
            self._maybe_clear_model("2a7604")
        elif address == STUB_288948:
            self._log(address, r0)
        elif address == STUB_2BDAC0:
            self.counts["bdac0"] = self.counts.get("bdac0", 0) + 1
            self._log(address, r0, r1, r2)
            self._maybe_retarget("bdac0")
        elif address == STUB_2BF030:
            self.counts["bf030"] = self.counts.get("bf030", 0) + 1
            self._log(address, r0, r1)
            self._maybe_retarget("bf030")
        elif address == VT_SLOT1_ADDR:
            self._log(address, r0)
        elif address == VT_SLOT0_ADDR:
            self._log(address, r0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.counts = {}
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(MANAGER_PAGE, build_manager(case))
        self.uc.mem_write(VIEW_PAGE, build_view(case))
        self.uc.mem_write(WORK_ADDR, build_work(case))
        entity, vtable = build_entity(case)
        self.uc.mem_write(ENTITY_ADDR, entity)
        self.uc.mem_write(VTABLE_ADDR, vtable)
        self.uc.mem_write(VT_SLOT1_ADDR, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(ALT_WORK_ADDR, b"\x00" * 0x1000)
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

        non_stack_writes = [
            (address, size, value)
            for address, size, value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "manager": bytes(self.uc.mem_read(MANAGER_PAGE, MANAGER_SIZE)),
                "view": bytes(self.uc.mem_read(VIEW_PAGE, VIEW_SIZE)),
                "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
                "entity": bytes(self.uc.mem_read(ENTITY_ADDR, ENTITY_SIZE)),
                "vtable": bytes(self.uc.mem_read(VTABLE_ADDR, VTABLE_SIZE)),
            },
            "writes": non_stack_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
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
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    # The only two architected data stores target disjoint fields (+0x10 and
    # +0x12DC), so their relative order is not observable; compare the writes
    # as a multiset while the full memory image above still proves the values
    # and addresses exactly.
    if sorted(orig["writes"]) != sorted(cand["writes"]):
        problems.append(
            "writes:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 0,
        "sub": 0,
        "model": ENTITY_ADDR,
        "flag_02": 0,
        "view_subobject": 1,
        "b8adc_result": 1,
        "f1e84": 0x11111111,
        "f1e88_bits": 0x00000000,
        "f1e8c_bits": 0x00000000,
        "clear_model_at": None,
        "retarget": None,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- state-3 early return (no helper calls, no writes)
    cases.append(base_case("state 3 early return", state=3, sub=3))
    cases.append(base_case("state 3 with other sub-menu", state=3, sub=0))
    cases.append(base_case("state 3 with model null", state=3, sub=9, model=0))

    # --- reset-only paths: sub-menu state is not 3 or 9
    for state in (0, 1, 2, 4, 0xFFFFFFFF, 0x80000000, 0x00030000):
        cases.append(base_case(f"reset only state 0x{state:08x}",
                               state=state, sub=0))
    for sub in (0, 1, 2, 4, 5, 6, 7, 8, 10, 11, 0x7F, 0xFF):
        cases.append(base_case(f"reset only sub 0x{sub:02x}", state=2, sub=sub))

    # --- teardown path A: 0x002A0DD4 returns a nonzero view subobject
    for sub in (3, 9):
        cases.append(base_case(f"path A sub {sub}", state=0, sub=sub,
                               view_subobject=1, model=ENTITY_ADDR))
        cases.append(base_case(f"path A sub {sub} model null", state=0, sub=sub,
                               view_subobject=1, model=0))
        cases.append(base_case(f"path A sub {sub} gate 0xFFFFFFFF", state=0,
                               sub=sub, view_subobject=0xFFFFFFFF))
        cases.append(base_case(f"path B sub {sub}", state=0, sub=sub,
                               view_subobject=0, model=ENTITY_ADDR,
                               b8adc_result=1, flag_02=0))
        cases.append(base_case(f"path B sub {sub} model null", state=0, sub=sub,
                               view_subobject=0, model=0))
        for result in (0, 1, 2, 0xFFFFFFFF):
            cases.append(base_case(
                f"path B sub {sub} b8adc 0x{result:08x}", state=0, sub=sub,
                view_subobject=0, b8adc_result=result, flag_02=0))
            cases.append(base_case(
                f"path B sub {sub} b8adc 0x{result:08x} flag 1", state=0,
                sub=sub, view_subobject=0, b8adc_result=result, flag_02=1))
        cases.append(base_case(f"path B sub {sub} flag 0xFF", state=0, sub=sub,
                               view_subobject=0, flag_02=0xFF))

    # --- null model discovered by a helper between the checks
    for source in ("288990", "b8adc", "2a7604"):
        for flag in (0, 1):
            cases.append(base_case(
                f"model cleared at {source} flag {flag}", state=0, sub=3,
                view_subobject=0, b8adc_result=0 if source == "2a7604" else 1,
                flag_02=flag, clear_model_at=source))

    # --- float bit patterns for the 0x0029411C stack record
    for bits in (0x00000000, 0x80000000, 0x447A0000, 0x7F7FFFFF, 0xFF800000,
                 0x7FC00001, 0xC47A0000):
        cases.append(base_case(f"path A params 0x{bits:08x}", state=0, sub=3,
                               view_subobject=1, f1e84=bits ^ 0x5A5A5A5A,
                               f1e88_bits=bits, f1e8c_bits=bits ^ 0xFFFFFFFF))

    # --- manager work retargeted during the reset (final stores must reload)
    cases.append(base_case("retarget work on 5th bdac0", state=0, sub=0,
                           retarget=("bdac0", 5, ALT_WORK_ADDR)))
    cases.append(base_case("retarget work on 2nd bf030", state=0, sub=0,
                           retarget=("bf030", 2, ALT_WORK_ADDR)))
    cases.append(base_case("retarget work after teardown", state=0, sub=3,
                           retarget=("bdac0", 27, ALT_WORK_ADDR)))
    cases.append(base_case("retarget work after teardown B", state=0, sub=3,
                           view_subobject=0, retarget=("bdac0", 8,
                                                       ALT_WORK_ADDR)))

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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing script_vm_func_0029ccf8 (0x0029ccf8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("state_compare", "if (state == 3u) {", "if (state == 4u) {"),
        ("sub_menu_nine", "sub_menu_state == 9u", "sub_menu_state == 10u"),
        ("subobject_lift", "constexpr f32 kSubobjectLift = 1000.0f;",
         "constexpr f32 kSubobjectLift = 100.0f;"),
        ("list_bound", "constexpr s32 kListCount  = 10;",
         "constexpr s32 kListCount  = 9;"),
        ("first_widget", "camp_func_002bdac0(work + 0x038Cu, 5u, 0u);",
         "camp_func_002bdac0(work + 0x0388u, 5u, 0u);"),
        ("publish_value", "camp_func_0029bc1c(1u);",
         "camp_func_0029bc1c(2u);"),
        ("vtable_slot", "reinterpret_cast<VirtualSlot1>(vtable[1]);",
         "reinterpret_cast<VirtualSlot1>(vtable[0]);"),
    )
    for name, old, new in mutants:
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
