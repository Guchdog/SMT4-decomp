#!/usr/bin/env python3
"""Differential test for InfoWin_Calc (0x0011b1bc) with Unicorn ARM.

Compiles src/ui/window.cpp, extracts InfoWin_Calc, resolves its direct calls
and g_InfoWinWork relocation against the pinned target addresses, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log (stub address, register arguments);
  * InfoWinWork (+0x00..+0x1BC);
  * unexpected writes outside InfoWinWork and stack.

Coverage:
  * states 0, 6, 0xFFFFFFFF (default -> increment +0x0C only);
  * state 1 with ui_func_002bf9f0 == 0, != 0 with work[0x23] == 0 and != 0;
  * state 2 with width <= 0 (transitions to state 3) and width > 0;
  * state 3 with counter <= 0x1E, > 0x1E with flag22 == 0, and > 0x1E with
    flag22 != 0 covering both wrap-around and non-wrap-around of x0 and x1;
  * state 4 with timer < 0, timer >= counter, and timer < counter;
  * state 5 with ui_func_002bf9f0 == 0 and != 0;
  * negative/mutation controls on kScrollGap, kScrollDelayFrames, kCloseTimer,
    `work[0x23] != 0`, and `width <= 0`.
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
SOURCE = ROOT / "src/ui/window.cpp"
OUT_DIR = ROOT / "build/test_leaf_0011b1bc"

FUNC_ADDR = 0x0011B1BC
FUNC_SIZE = 440

CODE_ADDR = 0x00110000
CODE_SIZE = 0x001C0000  # covers 0x0011B1BC..0x002C0000
GLOBALS_PAGE = 0x0043E000
PTR_WORK = 0x0043E128
WORK_ADDR = 0x00500000
PAGE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2BF9F0 = 0x002BF9F0
STUB_2BDAC0 = 0x002BDAC0
STUB_2B9220 = 0x002B9220
STUB_2BEF7C = 0x002BEF7C

STUB_NAMES = {
    STUB_2BF9F0: "ui_func_002bf9f0",
    STUB_2BDAC0: "UiAnimSprite_SetMode",
    STUB_2B9220: "engine_func_002b9220",
    STUB_2BEF7C: "ui_func_002bef7c",
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
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _stub_address(symbol_name: str) -> int | None:
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def _get_symbol_offset(obj_file: Path, sym_substr: str) -> int:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum = struct.unpack_from("<HH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    for sh in sections:
        if sh[1] == 2:  # SHT_SYMTAB
            sym_off, sym_size, str_idx, entsize = sh[4], sh[5], sh[6], sh[9]
            str_off, str_size = sections[str_idx][4], sections[str_idx][5]
            strtab = data[str_off : str_off + str_size]
            for pos in range(0, sym_size, entsize):
                st_name, st_value = struct.unpack_from("<II", data, sym_off + pos)
                end = strtab.find(b"\x00", st_name)
                name = strtab[st_name:end].decode("utf-8", errors="replace")
                if sym_substr in name:
                    return st_value
    raise RuntimeError(f"Symbol containing {sym_substr!r} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "InfoWin_Calc" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"InfoWin_Calc not found in {obj_file}: {sorted(funcs)}"
        )

    sym_offset = _get_symbol_offset(obj_file, "InfoWin_Calc")
    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = _stub_address(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if rel.symbol_name == "":
                target = FUNC_ADDR + (addend - sym_offset)
            elif "g_InfoWinWork" in rel.symbol_name:
                target = PTR_WORK + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {rel.symbol_name!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "window.o"
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


class Runner:
    """One Unicorn machine with deterministic stubs for InfoWin_Calc."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE, PAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, PAGE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, bx_lr)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE320F000))

        self.case: dict = {}
        self.call_log: list[tuple] = []
        self.bad_writes: list[tuple[int, int, int]] = []

        for addr in STUB_NAMES:
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, None, addr, addr)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_stub(
        self, uc: unicorn.Uc, address: int, size: int, user_data: object
    ) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_2BF9F0:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("sprite_done", 0))
        elif address == STUB_2BDAC0:
            self.call_log.append((address, r0, r1, r2))
        elif address == STUB_2B9220:
            self.call_log.append((address, r0, r1))
        elif address == STUB_2BEF7C:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("width", 0) & 0xFFFFFFFF)

    def _on_write(
        self,
        uc: unicorn.Uc,
        access: int,
        address: int,
        size: int,
        value: int,
        user_data: object,
    ) -> None:
        allowed = (
            (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            or (WORK_ADDR <= address < WORK_ADDR + 0x1BC)
        )
        if not allowed:
            self.bad_writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.bad_writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * max(FUNC_SIZE, len(code) + 16))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STACK_ADDR, b"\xCD" * STACK_SIZE)
        self.uc.mem_write(GLOBALS_PAGE, b"\x00" * PAGE_SIZE)
        self.uc.mem_write(PTR_WORK, struct.pack("<I", WORK_ADDR))

        work = bytearray(b"\x00" * 0x1BC)
        struct.pack_into("<I", work, 0x08, case["state"] & 0xFFFFFFFF)
        struct.pack_into("<i", work, 0x0C, case.get("counter", 0))
        struct.pack_into("<i", work, 0x10, case.get("timer", 0))
        struct.pack_into("<i", work, 0x14, case.get("span", 100))
        struct.pack_into("<i", work, 0x18, case.get("x0", 0))
        struct.pack_into("<i", work, 0x1C, case.get("x1", 0))
        work[0x22] = case.get("flag22", 0) & 0xFF
        work[0x23] = case.get("flag23", 0) & 0xFF
        self.uc.mem_write(WORK_ADDR, bytes(work))

        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000, count=200_000)

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "calls": list(self.call_log),
            "work": bytes(self.uc.mem_read(WORK_ADDR, 0x1BC)),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {"name": "state_0", "state": 0, "counter": 5},
        {"name": "state_6_oob", "state": 6, "counter": 10},
        {"name": "state_neg1_oob", "state": 0xFFFFFFFF, "counter": 10},
        {"name": "state_1_not_done", "state": 1, "sprite_done": 0, "counter": 3},
        {"name": "state_1_done_flag23_0", "state": 1, "sprite_done": 1, "flag23": 0, "counter": 9},
        {"name": "state_1_done_flag23_1", "state": 1, "sprite_done": 1, "flag23": 1, "counter": 9},
        {"name": "state_2_width_pos", "state": 2, "width": 50, "span": 100, "counter": 4},
        {"name": "state_2_width_zero", "state": 2, "width": 0, "span": 100, "counter": 4},
        {"name": "state_2_width_neg", "state": 2, "width": -5, "span": 100, "counter": 4},
        {"name": "state_3_delay_not_met", "state": 3, "counter": 0x1E, "flag22": 1, "x0": 10, "x1": 20},
        {"name": "state_3_flag22_zero", "state": 3, "counter": 0x1F, "flag22": 0, "x0": 10, "x1": 20},
        {"name": "state_3_scroll_no_wrap", "state": 3, "counter": 0x1F, "flag22": 1, "span": 100, "x0": 10, "x1": 20},
        {"name": "state_3_scroll_wrap_x0", "state": 3, "counter": 0x20, "flag22": 1, "span": 100, "x0": -100, "x1": 50},
        {"name": "state_3_scroll_wrap_x1", "state": 3, "counter": 0x20, "flag22": 1, "span": 100, "x0": 50, "x1": -100},
        {"name": "state_4_timer_neg", "state": 4, "timer": -1, "counter": 100},
        {"name": "state_4_timer_not_elapsed", "state": 4, "timer": 30, "counter": 30},
        {"name": "state_4_timer_elapsed", "state": 4, "timer": 30, "counter": 31},
        {"name": "state_5_not_done", "state": 5, "sprite_done": 0, "flag23": 1, "counter": 7},
        {"name": "state_5_done", "state": 5, "sprite_done": 1, "flag23": 1, "counter": 7},
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee", "calls", "work", "bad_writes"):
        if orig[key] != cand[key]:
            diffs.append(f"{name}: {key} orig={orig[key]!r} cand={cand[key]!r}")
    if cand["sp"] != ENTRY_SP:
        diffs.append(f"{name}: sp not restored: {cand['sp']:#x}")
    if cand["callee"] != CALLEE_SAVED_START:
        diffs.append(f"{name}: callee-saved clobbered: {cand['callee']!r}")
    if cand["bad_writes"]:
        diffs.append(f"{name}: unexpected writes: {cand['bad_writes']!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    orig_runner = Runner()
    cand_runner = Runner()
    cases = build_cases()

    for case in cases:
        orig_res = orig_runner.run(orig_bytes, case)
        cand_res = cand_runner.run(cand_bytes, case)
        diffs = compare_outputs(case["name"], orig_res, cand_res)
        if diffs:
            for d in diffs:
                print("FAIL:", d)
            return 1

    mutants = [
        ("scroll_gap", "kScrollGap = 0x2A;", "kScrollGap = 0x2B;"),
        ("scroll_delay", "kScrollDelayFrames = 0x1E;", "kScrollDelayFrames = 0x1F;"),
        ("close_timer", "kCloseTimer = 0x1E;", "kCloseTimer = 0x1F;"),
        ("flag23_branch", "if (work[0x23] != 0)", "if (work[0x23] == 0)"),
        ("width_cmp", "if (width <= 0)", "if (width < 0)"),
    ]
    for m_name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(m_name, old, new)
        mut_runner = Runner()
        detected = False
        for case in cases:
            orig_res = orig_runner.run(orig_bytes, case)
            mut_res = mut_runner.run(mut_bytes, case)
            if compare_outputs(case["name"], orig_res, mut_res):
                detected = True
                break
        if not detected:
            print(f"FAIL: mutant {m_name} was not detected")
            return 1

    print(
        f"PASS: InfoWin_Calc (0x0011b1bc) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
