#!/usr/bin/env python3
"""Differential test for GuestWin_DrawUp (0x0011a9b4) with Unicorn ARM.

Compiles src/ui/window.cpp, extracts GuestWin_DrawUp, resolves its calls and
globals against the pinned target addresses, and compares the pinned original
(extracted/exefs/code.bin) against the candidate in Unicorn.
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
OUT_DIR = ROOT / "build" / "test_leaf_0011a9b4"

FUNC_ADDR = 0x0011A9B4
FUNC_SIZE = 1116

G_GUEST_WIN_WORK_ADDR = 0x0043E110
G_ASD_GPU_STATE_ADDR = 0x0044EA00

STUB_2B6E78 = 0x002B6E78
STUB_2B6E60 = 0x002B6E60
STUB_BEGIN_PASS = 0x002C3BA8
STUB_SET_VP = 0x002C5F7C
STUB_GET_POS_X = 0x002BEF7C
STUB_TRANSFORM_COORD = 0x002BA46C
STUB_GET_POS_Y = 0x002BEF70
STUB_SET_ALPHA = 0x002BF710
STUB_GET_LAYOUT = 0x002BF6D0
STUB_2B6E44 = 0x002B6E44
STUB_2C5FA4 = 0x002C5FA4
STUB_DRAW_PANEL = 0x002BF460
STUB_2BEAE4 = 0x002BEAE4
STUB_2B6E10 = 0x002B6E10
STUB_2B6D94 = 0x002B6D94
STUB_2B6C80 = 0x002B6C80
STUB_2BD13C = 0x002BD13C
STUB_2BE7FC = 0x002BE7FC
STUB_2B6A98 = 0x002B6A98
STUB_2BD258 = 0x002BD258
STUB_DRAW_TEXT = 0x002BE77C
STUB_2BEF14 = 0x002BEF14
STUB_VP_CB = 0x003F0100
STUB_MODE_CB = 0x003F0200

STUB_NAMES = {
    STUB_2B6E78: "script_vm_func_002b6e78",
    STUB_2B6E60: "battle_func_002b6e60",
    STUB_BEGIN_PASS: "UiGpu_BeginPass",
    STUB_SET_VP: "UiGpu_SetViewportParams",
    STUB_GET_POS_X: "ui_func_002bef7c",
    STUB_TRANSFORM_COORD: "UiGpu_TransformCoord",
    STUB_GET_POS_Y: "ui_func_002bef70",
    STUB_SET_ALPHA: "UiGpu_SetAlphaBlend",
    STUB_GET_LAYOUT: "camp_func_002bf6d0",
    STUB_2B6E44: "script_vm_func_002b6e44",
    STUB_2C5FA4: "battle_func_002c5fa4",
    STUB_DRAW_PANEL: "UiSprite_DrawPanelDirect",
    STUB_2BEAE4: "battle_func_002beae4",
    STUB_2B6E10: "battle_func_002b6e10",
    STUB_2B6D94: "battle_func_002b6d94",
    STUB_2B6C80: "func_002b6c80",
    STUB_2BD13C: "camp_func_002bd13c",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_2B6A98: "ui_func_002b6a98",
    STUB_2BD258: "camp_func_002bd258",
    STUB_DRAW_TEXT: "ui_func_002be77c",
    STUB_2BEF14: "script_vm_func_002bef14",
    STUB_VP_CB: "vp_cb",
    STUB_MODE_CB: "mode_cb",
}

PTR_WORK = 0x20000000
WORK_SIZE = 0x100
PTR_GPU = 0x20010000
GPU_SIZE = 0x1300
PTR_GUEST = 0x20020000
PTR_ENTRY = 0x20021000
PTR_LAYOUT_BASE = 0x20022000
PTR_STR1 = 0x20023000
PTR_STR2 = 0x20023100
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
        if "GuestWin_DrawUp" in name and "Draft" not in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"GuestWin_DrawUp not found in {obj_file}")

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
            cond = 0xFA000000 if target == STUB_2BE7FC else (original & 0xFF000000)
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_GuestWinWork" in rel.symbol_name:
                target = G_GUEST_WIN_WORK_ADDR + addend
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


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    raw = bytes(uc.mem_read(addr, 32))
    end = raw.find(b"\x00")
    return raw[:end].decode("ascii", errors="replace") if end >= 0 else raw.decode("ascii", errors="replace")


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_WORK, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        state: int,
        guest_state: int,
        guest_46: int,
        anchor_flag: int,
        b6e10: int,
        dirty: int,
        new_vp: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(G_GUEST_WIN_WORK_ADDR, struct.pack("<I", PTR_WORK))
        uc.mem_write(G_ASD_GPU_STATE_ADDR, struct.pack("<I", PTR_GPU))

        uc.mem_write(PTR_WORK, b"\x00" * WORK_SIZE)
        uc.mem_write(PTR_WORK + 0x08, struct.pack("<I", state))
        uc.mem_write(PTR_WORK + 0x50, struct.pack("<f", 0.75))

        uc.mem_write(PTR_GUEST, b"\x00" * 0x700)
        uc.mem_write(PTR_GUEST + 0x0E, struct.pack("<h", 12))
        uc.mem_write(PTR_GUEST + 0x2A, struct.pack("<h", 34))
        uc.mem_write(PTR_GUEST + 0x46, struct.pack("<H", guest_46))
        uc.mem_write(PTR_GUEST + 0x604, struct.pack("<HH", 55, 66))

        uc.mem_write(PTR_ENTRY, b"\x00" * 0x80)
        uc.mem_write(PTR_ENTRY + 0x5A, struct.pack("<H", 77))

        uc.mem_write(PTR_STR1, b"GuestDemon\x00")
        uc.mem_write(PTR_STR2, b"GuestNPC\x00")

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

        for i in range(4):
            addr = PTR_LAYOUT_BASE + i * 0x20
            uc.mem_write(addr, b"\x00" * 0x20)
            uc.mem_write(addr + 0x08, struct.pack("<hh", (i + 1) * 5, (i + 1) * -3))

        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        thumb_bx_lr = struct.pack("<HH", 0x4770, 0x46C0)
        for addr in STUB_NAMES:
            uc.mem_write(addr, thumb_bx_lr if addr == STUB_2BE7FC else bx_lr)
        uc.mem_write(LR_SENTINEL, bx_lr)

        calls: list[tuple[object, ...]] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            r3 = emu.reg_read(arm.UC_ARM_REG_R3)
            sp = emu.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_2B6E78:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, guest_state)
            elif addr == STUB_2B6E60:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_GUEST)
            elif addr in (STUB_BEGIN_PASS, STUB_VP_CB, STUB_MODE_CB):
                calls.append((addr, r0))
            elif addr == STUB_SET_VP:
                calls.append((addr, r0, r1))
                emu.reg_write(arm.UC_ARM_REG_R0, new_vp)
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
            elif addr == STUB_GET_LAYOUT:
                calls.append((addr, r0, r1))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_LAYOUT_BASE + (r1 - 0xD8) * 0x20)
            elif addr == STUB_2B6E44:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, anchor_flag)
            elif addr == STUB_2C5FA4:
                calls.append((addr, r0, r1, r2))
                emu.reg_write(arm.UC_ARM_REG_R0, 0x44440000 + r1)
            elif addr == STUB_DRAW_PANEL:
                sp0, sp4 = struct.unpack("<II", emu.mem_read(sp, 8))
                calls.append((addr, r0, r1, r2, r3, sp0, sp4))
            elif addr == STUB_2BEAE4:
                sp_args = struct.unpack("<9I", emu.mem_read(sp, 36))
                calls.append((addr, r0, r1, r2, r3, *sp_args))
            elif addr == STUB_2B6E10:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, b6e10)
            elif addr == STUB_2B6D94:
                calls.append((addr, r0, r1))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_ENTRY)
            elif addr == STUB_2B6C80:
                calls.append((addr, r0, r1, r2, r3))
            elif addr == STUB_2BD13C:
                calls.append((addr, r0))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_STR1)
            elif addr == STUB_2B6A98:
                sp0 = struct.unpack("<I", emu.mem_read(sp, 4))[0]
                calls.append((addr, r0, r1, r2, r3, sp0))
            elif addr == STUB_2BD258:
                calls.append((addr, r0))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_STR2)
            elif addr == STUB_2BE7FC:
                s = read_cstr(emu, r1)
                calls.append((addr, s))
                emu.mem_write(r0, s.encode("ascii") + b"\x00")
            elif addr == STUB_DRAW_TEXT:
                s0 = emu.reg_read(arm.UC_ARM_REG_S0)
                s1 = emu.reg_read(arm.UC_ARM_REG_S1)
                s2 = emu.reg_read(arm.UC_ARM_REG_S2)
                s3 = emu.reg_read(arm.UC_ARM_REG_S3)
                s4 = emu.reg_read(arm.UC_ARM_REG_S4)
                calls.append((addr, r0, r1, read_cstr(emu, r2), s0, s1, s2, s3, s4))
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
        uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=5000)
        for hook in hooks:
            uc.hook_del(hook)

        callee = {
            name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for name, reg_name in zip(CALLEE_SAVED, CALLEE_SAVED)
        }
        callee["d8"] = uc.reg_read(arm.UC_ARM_REG_D8)
        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
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
        ("state0", 0, 2, 7, 0, 0, 0, 0x22220000),
        ("guest1", 1, 1, 7, 0, 0, 0, 0x22220000),
        ("guest46_0", 1, 2, 0, 0, 0, 0, 0x22220000),
        ("npc_da", 1, 2, 7, 0, 0, 0, 0x22220000),
        ("demon_db_dirty", 1, 2, 7, 1, 1, 1, 0x11110000),
    ]
    for label, st, gst, g46, af, b6e10, dirty, new_vp in cases:
        orig_res = Runner().run(orig_bytes, st, gst, g46, af, b6e10, dirty, new_vp)
        cand_res = Runner().run(cand_bytes, st, gst, g46, af, b6e10, dirty, new_vp)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_guest1", "if (guest_state == 0 || guest_state == 1)", "if (guest_state == 0)"),
        ("swap_anchor", "anchor = camp_func_002bf6d0(0x0E, 0xDB);", "anchor = camp_func_002bf6d0(0x0E, 0xDA);"),
        ("wrong_panel_loop", "sub_id <= 0xCD", "sub_id < 0xCD"),
        ("drop_demon_branch", "if (battle_func_002b6e10() != 0)", "if (false)"),
        ("wrong_text_scale", "kTextScale = 0.85f;", "kTextScale = 0.75f;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, st, gst, g46, af, b6e10, dirty, new_vp in cases:
            if compare(Runner().run(orig_bytes, st, gst, g46, af, b6e10, dirty, new_vp), Runner().run(mut_bytes, st, gst, g46, af, b6e10, dirty, new_vp)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: GuestWin_DrawUp (0x0011a9b4) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
