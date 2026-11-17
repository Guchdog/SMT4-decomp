#!/usr/bin/env python3
"""Differential test for ComWin_ProcessDialog (0x0010a954) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0010a954"

FUNC_ADDR = 0x0010A954
FUNC_SIZE = 1352

G_CTX_PTR_BASE = 0x0043E188
G_ASD_GPU_STATE_ADDR = 0x0044EA00

STUB_ALPHA = 0x002BF710
STUB_VP_PARAMS = 0x002C5F7C
STUB_PUSH_CTX = 0x002BEFDC
STUB_DRAW_PANEL = 0x002BF460
STUB_POP_CTX = 0x002BEF88
STUB_1260B8 = 0x001260B8
STUB_1188D0 = 0x001188D0
STUB_124C48 = 0x00124C48
STUB_GET_X = 0x002BEF7C
STUB_GET_Y = 0x002BEF70
STUB_2BEF14 = 0x002BEF14
STUB_GET_LAYOUT = 0x002BF6D0
STUB_2BF558 = 0x002BF558
STUB_2BE828 = 0x002BE828
STUB_2BE7FC = 0x002BE7FC  # Thumb
STUB_2BE77C = 0x002BE77C
STUB_2BE548 = 0x002BE548
STUB_2BE4DC = 0x002BE4DC
STUB_2BE16C = 0x002BE16C
STUB_2BDEB8 = 0x002BDEB8

STUB_NAMES = {
    STUB_ALPHA: "UiGpu_SetAlphaBlend",
    STUB_VP_PARAMS: "UiGpu_SetViewportParams",
    STUB_PUSH_CTX: "UiWindow_PushContext",
    STUB_DRAW_PANEL: "UiSprite_DrawPanelDirect",
    STUB_POP_CTX: "UiWindow_PopContext",
    STUB_1260B8: "func_001260b8",
    STUB_1188D0: "func_001188d0",
    STUB_124C48: "func_00124c48",
    STUB_GET_X: "ui_func_002bef7c",
    STUB_GET_Y: "ui_func_002bef70",
    STUB_2BEF14: "script_vm_func_002bef14",
    STUB_GET_LAYOUT: "camp_func_002bf6d0",
    STUB_2BF558: "func_002bf558",
    STUB_2BE828: "ui_func_002be828",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_2BE77C: "ui_func_002be77c",
    STUB_2BE548: "ui_func_002be548",
    STUB_2BE4DC: "ui_func_002be4dc",
    STUB_2BE16C: "ui_func_002be16c",
    STUB_2BDEB8: "ui_func_002bdeb8",
}

PTR_RODATA = 0x00500000
PTR_CTX = 0x20000000
PTR_GPU = 0x20002000
PTR_LAYOUTS = 0x20004000
PTR_STR_RET = 0x20008000
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _stub_address(symbol_name: str) -> int | None:
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def _extract_rodata_str(obj_file: Path) -> bytes:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr_off, shstr_size = sections[e_shstrndx][4], sections[e_shstrndx][5]
    shstr = data[shstr_off : shstr_off + shstr_size]
    for sh in sections:
        end = shstr.find(b"\x00", sh[0])
        name = shstr[sh[0] : end].decode("utf-8", errors="replace")
        if name == ".rodata.str1.1":
            return data[sh[4] : sh[4] + sh[5]]
    return b""


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "ComWin_ProcessDialog" in name), None)
    if candidate is None:
        raise RuntimeError(f"ComWin_ProcessDialog not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        off = rel.offset
        sym_name = rel.symbol_name
        rtype = rel.relocation_type
        if rtype in (28, 29):
            dst = _stub_address(sym_name)
            if dst is None:
                raise RuntimeError(f"Unhandled call relocation: {sym_name}")
            pc = FUNC_ADDR + off + 8
            disp = ((dst - pc) >> 2) & 0x00FFFFFF
            insn = struct.unpack_from("<I", code, off)[0]
            if dst == STUB_2BE7FC and rtype == 28:
                struct.pack_into("<I", code, off, 0xFA000000 | disp)
            else:
                struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        elif rtype == 2:
            addend = struct.unpack_from("<I", code, off)[0]
            if "g_AsdGpuState" in sym_name:
                target = G_ASD_GPU_STATE_ADDR + addend
            elif sym_name == "" or sym_name.startswith(".L.str") or sym_name == ".rodata.str1.1":
                target = PTR_RODATA + addend
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name} +{addend:#x}")
            struct.pack_into("<I", code, off, target)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), _extract_rodata_str(obj_file)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "window.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"window_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"window_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    raw = bytes(uc.mem_read(addr, 32))
    end = raw.find(b"\x00")
    return raw[:end].decode("ascii", "replace") if end >= 0 else raw.decode("ascii", "replace")


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_RODATA, 0x1000)
        self.uc.mem_map(PTR_CTX, 0x10000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        f83: int,
        mode: int,
        f8: int,
        f7d: int,
        f7f: int,
        f7e: int,
        f8c: int,
        val90: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_RODATA, b"\x00" * 0x1000)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(G_CTX_PTR_BASE + 0x08, struct.pack("<I", PTR_CTX))
        uc.mem_write(G_ASD_GPU_STATE_ADDR, struct.pack("<I", PTR_GPU))

        uc.mem_write(PTR_CTX, b"\x00" * 0xB00)
        uc.mem_write(PTR_CTX + 0x08, bytes([f8 & 0xFF, mode & 0xFF]))
        uc.mem_write(PTR_CTX + 0x68, struct.pack("<II", 0x1234, 77))
        uc.mem_write(PTR_CTX + 0x7D, bytes([f7d & 0xFF, f7e & 0xFF, f7f & 0xFF]))
        uc.mem_write(PTR_CTX + 0x83, bytes([f83 & 0xFF]))
        uc.mem_write(PTR_CTX + 0x8C, struct.pack("<I", f8c))
        uc.mem_write(PTR_CTX + 0x90, struct.pack("<H", val90 & 0xFFFF))
        uc.mem_write(PTR_CTX + 0xE4, struct.pack("<f", 0.5))

        uc.mem_write(PTR_STR_RET, b"ItemName\x00")

        for stub_addr in STUB_NAMES:
            if stub_addr == STUB_2BE7FC:
                uc.mem_write(stub_addr, struct.pack("<HH", 0x4770, 0x46C0))
            else:
                uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

        calls: list[tuple[object, ...]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            if addr not in STUB_NAMES:
                return
            r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
            sp = uc_cb.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_ALPHA:
                s0 = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                calls.append(("alpha", s0))
            elif addr == STUB_VP_PARAMS:
                calls.append(("vp", r0, r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 99)
            elif addr == STUB_PUSH_CTX:
                calls.append(("push_ctx", r0, r1, r2))
            elif addr == STUB_POP_CTX:
                calls.append(("pop_ctx", r0, r1))
            elif addr == STUB_DRAW_PANEL:
                s0, s1 = struct.unpack("<II", uc_cb.mem_read(sp, 8))
                calls.append(("panel", r0, r1, r2, r3, s0, s1))
            elif addr in (STUB_1260B8, STUB_1188D0, STUB_124C48, STUB_2BE4DC):
                calls.append((STUB_NAMES[addr], r0))
            elif addr == STUB_GET_X:
                calls.append(("get_x", r0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 100)
            elif addr == STUB_GET_Y:
                calls.append(("get_y", r0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 50)
            elif addr == STUB_2BEF14:
                calls.append(("2bef14",))
            elif addr == STUB_GET_LAYOUT:
                calls.append(("layout", r0, r1))
                layout_ptr = PTR_LAYOUTS + ((r1 & 0xFF) * 0x10)
                uc_cb.mem_write(layout_ptr, b"\x00" * 0x10)
                uc_cb.mem_write(layout_ptr + 0x08, struct.pack("<hh", (r1 & 0xF) + 1, (r1 & 0xF) + 2))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, layout_ptr)
            elif addr == STUB_2BF558:
                s0, s1 = struct.unpack("<II", uc_cb.mem_read(sp, 8))
                calls.append(("2bf558", r0, r1, r2, r3, s0, s1))
            elif addr == STUB_2BE828:
                calls.append(("2be828", r0, r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_STR_RET)
            elif addr == STUB_2BE7FC:
                fmt = read_cstr(uc_cb, r1)
                src = read_cstr(uc_cb, r2)
                calls.append(("2be7fc", fmt, src))
                uc_cb.mem_write(r0, (src + "\x00").encode("ascii"))
            elif addr == STUB_2BE77C:
                s0 = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                s1 = uc_cb.reg_read(arm.UC_ARM_REG_S1)
                s2 = uc_cb.reg_read(arm.UC_ARM_REG_S2)
                s3 = uc_cb.reg_read(arm.UC_ARM_REG_S3)
                s4 = uc_cb.reg_read(arm.UC_ARM_REG_S4)
                calls.append(("2be77c", r0, r1, read_cstr(uc_cb, r2), s0, s1, s2, s3, s4))
            elif addr == STUB_2BE548:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("2be548", r0, r1, r2, r3, s0))
            elif addr == STUB_2BE16C:
                s0, s1, s2, s3 = struct.unpack("<IIII", uc_cb.mem_read(sp, 16))
                fmt = read_cstr(uc_cb, s2)
                extra = (s3,) if fmt == "%d" else ()
                calls.append(("2be16c", r0, r1, r2, r3, s0, s1, fmt) + extra)
            elif addr == STUB_2BDEB8:
                calls.append(("2bdeb8", r0, r1, r2, r3))

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=5000)
        finally:
            uc.hook_del(h_code)
            uc.hook_del(h_mem)

        callee = {
            reg_name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for reg_name in CALLEE_SAVED
        }
        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["r0"] != cand["r0"]:
        diffs.append(f"r0: orig={orig['r0']:#x} cand={cand['r0']:#x}")
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls mismatch (orig {len(orig['calls'])} vs cand {len(cand['calls'])})")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("skip_83", 1, 0x0B, 1, 1, 0, 1, 1, 0),
        ("mode_0b_all", 0, 0x0B, 1, 1, 0, 1, 1, 0),
        ("mode_13_val42", 0, 0x13, 1, 1, 1, 0, 1, 42),
        ("mode_00_val12345", 0, 0x00, 0, 0, 0, 1, 1, 12345),
        ("mode_0b_no8", 0, 0x0B, 0, 0, 0, 0, 0, 0),
    ]
    for label, f83, mode, f8, f7d, f7f, f7e, f8c, val90 in cases:
        orig_res = Runner().run(orig_bytes, b"", f83, mode, f8, f7d, f7f, f7e, f8c, val90)
        cand_res = Runner().run(cand_bytes, cand_rodata, f83, mode, f8, f7d, f7f, f7e, f8c, val90)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_83_guard", "if (ctx[0x83] != 0)", "if (false)"),
        ("wrong_13_panel", "UiSprite_DrawPanelDirect(2, 0x3A, 0x8D, 0, 0, 6);", "UiSprite_DrawPanelDirect(2, 0x0E, 0x8D, 0, 0, 6);"),
        ("drop_7f_guard", "if (cur[0x7D] != 0 && cur[0x7F] == 0)", "if (cur[0x7D] != 0)"),
        ("wrong_star_id", "idx < 0 ? 0x5D : (0x65 - idx)", "idx < 0 ? 0x5D : (0x64 - idx)"),
        ("wrong_count_val", 'ui_func_002be16c(0, count_x, count_y, 1, 4, 0x10, "%d", count_val);', 'ui_func_002be16c(0, count_x, count_y, 1, 4, 0x10, "%d", count_val + 1);'),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, f83, mode, f8, f7d, f7f, f7e, f8c, val90 in cases:
            if compare(
                Runner().run(orig_bytes, b"", f83, mode, f8, f7d, f7f, f7e, f8c, val90),
                Runner().run(mut_bytes, mut_rodata, f83, mode, f8, f7d, f7f, f7e, f8c, val90),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: ComWin_ProcessDialog (0x0010a954) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
