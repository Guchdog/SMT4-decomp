#!/usr/bin/env python3
"""Differential test for SearchWin_DrawUpAndCalc (0x001accd4) with Unicorn ARM.

Compiles src/ui/window.cpp, extracts SearchWin_DrawUpAndCalc, resolves its
calls and globals against the pinned target addresses, and compares the pinned
original (extracted/exefs/code.bin) against the candidate in Unicorn.
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

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "ui" / "window.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_001accd4"

FUNC_ADDR = 0x001ACCD4
FUNC_SIZE = 1104

G_SEARCH_WIN_WORK_ADDR = 0x0043E170
G_ASD_GPU_STATE_ADDR = 0x0044EA00

STUB_BEGIN_PASS = 0x002C3BA8
STUB_SET_VP = 0x002C5F7C
STUB_GET_POS_X = 0x002BEF7C
STUB_TRANSFORM_COORD = 0x002BA46C
STUB_GET_POS_Y = 0x002BEF70
STUB_SET_ALPHA = 0x002BF710
STUB_2BF558 = 0x002BF558
STUB_2C5FA4 = 0x002C5FA4
STUB_GET_LAYOUT = 0x002BF6D0
STUB_DRAW_TEXT = 0x002BE77C
STUB_DRAW_PANEL = 0x002BF460
STUB_2BEF14 = 0x002BEF14
STUB_VP_CB = 0x003F0100
STUB_MODE_CB = 0x003F0200

STUB_NAMES = {
    STUB_BEGIN_PASS: "UiGpu_BeginPass",
    STUB_SET_VP: "UiGpu_SetViewportParams",
    STUB_GET_POS_X: "ui_func_002bef7c",
    STUB_TRANSFORM_COORD: "UiGpu_TransformCoord",
    STUB_GET_POS_Y: "ui_func_002bef70",
    STUB_SET_ALPHA: "UiGpu_SetAlphaBlend",
    STUB_2BF558: "func_002bf558",
    STUB_2C5FA4: "battle_func_002c5fa4",
    STUB_GET_LAYOUT: "camp_func_002bf6d0",
    STUB_DRAW_TEXT: "ui_func_002be77c",
    STUB_DRAW_PANEL: "UiSprite_DrawPanelDirect",
    STUB_2BEF14: "script_vm_func_002bef14",
    STUB_VP_CB: "vp_cb",
    STUB_MODE_CB: "mode_cb",
}

PTR_WORK = 0x20000000
WORK_SIZE = 0xE4
PTR_GPU = 0x20010000
GPU_SIZE = 0x1300
PTR_LAYOUT_BASE = 0x20020000
STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def f32_bits(val: float) -> int:
    return struct.unpack("<I", struct.pack("<f", val))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _stub_address(symbol_name: str) -> int | None:
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "SearchWin_DrawUpAndCalc" in name and "Draft" not in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"SearchWin_DrawUpAndCalc not found in {obj_file}")

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
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_SearchWinWork" in rel.symbol_name:
                target = G_SEARCH_WIN_WORK_ADDR + addend
            elif "g_AsdGpuState" in rel.symbol_name:
                target = G_ASD_GPU_STATE_ADDR + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {rel.symbol_name!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name!r}"
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
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"window_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"window_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed: {result.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_WORK, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self, code: bytes, state: int, flag14: int, timer: int, dirty: int, new_vp: int, new_mode: int
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(G_SEARCH_WIN_WORK_ADDR, struct.pack("<I", PTR_WORK))
        uc.mem_write(G_ASD_GPU_STATE_ADDR, struct.pack("<I", PTR_GPU))

        uc.mem_write(PTR_WORK, b"\x00" * WORK_SIZE)
        uc.mem_write(PTR_WORK + 0x08, struct.pack("<I", state))
        uc.mem_write(PTR_WORK + 0x10, struct.pack("<i", timer))
        uc.mem_write(PTR_WORK + 0x14, bytes([flag14 & 0xFF]))
        uc.mem_write(PTR_WORK + 0x58, struct.pack("<f", 0.75))

        uc.mem_write(PTR_GPU, b"\x00" * GPU_SIZE)
        vp_stack = PTR_GPU + 0x124C
        uc.mem_write(vp_stack + 0x00, struct.pack("<I", 0))
        uc.mem_write(vp_stack + 0x08, struct.pack("<I", 0x11110000))
        uc.mem_write(vp_stack + 0x18, bytes([dirty & 0xFF]))
        uc.mem_write(vp_stack + 0x1C, struct.pack("<I", STUB_VP_CB))

        mode_stack = PTR_GPU + 0x12AC
        uc.mem_write(mode_stack + 0x00, struct.pack("<I", 0))
        uc.mem_write(mode_stack + 0x08, struct.pack("<I", 0x33330000))
        uc.mem_write(mode_stack + 0x18, bytes([dirty & 0xFF]))
        uc.mem_write(mode_stack + 0x1C, struct.pack("<I", STUB_MODE_CB))

        for i in range(16):
            addr = PTR_LAYOUT_BASE + i * 0x20
            uc.mem_write(addr, b"\x00" * 0x20)
            uc.mem_write(addr + 0x08, struct.pack("<hh", (i + 1) * 5, (i + 1) * -3))

        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            uc.mem_write(addr, bx_lr)
        uc.mem_write(LR_SENTINEL, bx_lr)

        calls: list[tuple[object, ...]] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            r3 = emu.reg_read(arm.UC_ARM_REG_R3)
            sp = emu.reg_read(arm.UC_ARM_REG_SP)
            if addr in (STUB_BEGIN_PASS, STUB_VP_CB, STUB_MODE_CB):
                calls.append((addr, r0))
            elif addr == STUB_SET_VP:
                calls.append((addr, r0, r1))
                emu.reg_write(arm.UC_ARM_REG_R0, new_vp)
            elif addr in (STUB_DRAW_PANEL, STUB_2BF558):
                sp0, sp4 = struct.unpack("<II", emu.mem_read(sp, 8))
                calls.append((addr, r0, r1, r2, r3, sp0, sp4))
            elif addr == STUB_GET_POS_X:
                calls.append((addr, r0))
                emu.reg_write(arm.UC_ARM_REG_R0, 50)
            elif addr == STUB_TRANSFORM_COORD:
                s0 = emu.reg_read(arm.UC_ARM_REG_S0)
                calls.append((addr, r0, s0))
                emu.reg_write(arm.UC_ARM_REG_S0, f32_bits(bits_f32(s0) * 100.0))
            elif addr == STUB_GET_POS_Y:
                calls.append((addr, r0))
                emu.reg_write(arm.UC_ARM_REG_R0, 90)
            elif addr == STUB_SET_ALPHA:
                calls.append((addr, emu.reg_read(arm.UC_ARM_REG_S0)))
            elif addr == STUB_2C5FA4:
                calls.append((addr, r0, r1, r2))
                emu.reg_write(arm.UC_ARM_REG_R0, new_mode)
            elif addr == STUB_GET_LAYOUT:
                calls.append((addr, r0, r1))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_LAYOUT_BASE + (r1 - 0x16F) * 0x20)
            elif addr == STUB_DRAW_TEXT:
                s0 = emu.reg_read(arm.UC_ARM_REG_S0)
                s1 = emu.reg_read(arm.UC_ARM_REG_S1)
                s2 = emu.reg_read(arm.UC_ARM_REG_S2)
                s3 = emu.reg_read(arm.UC_ARM_REG_S3)
                s4 = emu.reg_read(arm.UC_ARM_REG_S4)
                calls.append((addr, r0, r1, r2, s0, s1, s2, s3, s4))
            elif addr == STUB_2BEF14:
                calls.append((addr,))

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if PTR_GPU <= addr < PTR_GPU + GPU_SIZE:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_R0, 0)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=5000)
        for hook in hooks:
            uc.hook_del(hook)

        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {
                name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
                for name in CALLEE_SAVED
            },
            "calls": calls,
            "gpu_vp": bytes(uc.mem_read(PTR_GPU + 0x124C, 0x24)),
            "gpu_mode": bytes(uc.mem_read(PTR_GPU + 0x12AC, 0x24)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls mismatch (orig {len(orig['calls'])} vs cand {len(cand['calls'])})")
    if orig["gpu_vp"] != cand["gpu_vp"]:
        diffs.append("gpu viewport stack mismatch")
    if orig["gpu_mode"] != cand["gpu_mode"]:
        diffs.append("gpu mode stack mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("state0", 0, 1, 0, 0, 0x22220000, 0x44440000),
        ("f14_0", 1, 0, 0, 0, 0x22220000, 0x44440000),
        ("t0_diff", 1, 1, 0, 0, 0x22220000, 0x44440000),
        ("t17_same", 1, 1, 17, 0, 0x11110000, 0x33330000),
        ("neg_t12_dirty", 1, 1, -12, 1, 0x11110000, 0x33330000),
    ]
    for label, st, f14, timer, dirty, new_vp, new_mode in cases:
        orig_res = Runner().run(orig_bytes, st, f14, timer, dirty, new_vp, new_mode)
        cand_res = Runner().run(cand_bytes, st, f14, timer, dirty, new_vp, new_mode)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_text_layout", "0x16F", "0x16E"),
        ("wrong_cell_layout", "0x170 + idx", "0x171 + idx"),
        ("wrong_flag_65", "func_002bf558(2, 0x0E, 0x14, base_x, base_y, 0x65);", "func_002bf558(2, 0x0E, 0x14, base_x, base_y, 0x64);"),
        ("wrong_flag_66", "func_002bf558(2, 0x0E, 0x15, base_x, base_y, 0x66);", "func_002bf558(2, 0x0E, 0x15, base_x, base_y, 0x67);"),
        ("drop_vp_pop", "pop_stack(0x124C);", ""),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, st, f14, timer, dirty, new_vp, new_mode in cases:
            if compare(Runner().run(orig_bytes, st, f14, timer, dirty, new_vp, new_mode), Runner().run(mut_bytes, st, f14, timer, dirty, new_vp, new_mode)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: SearchWin_DrawUpAndCalc (0x001accd4) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
