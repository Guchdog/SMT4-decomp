#!/usr/bin/env python3
"""Differential test for ComWin_DrawUp (0x0011a354) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0011a354"

FUNC_ADDR = 0x0011A354
FUNC_SIZE = 1632

G_COMWIN_WORK_PTR = 0x0043E0F8
G_ASD_GPU_STATE_ADDR = 0x0044EA00
G_MTX_GUARD = 0x00476638
G_MTX_DATA = 0x004EFD9C

STUB_BEGIN_PASS = 0x002C3BA8
STUB_VP_PARAMS = 0x002C5F7C
STUB_STEREO = 0x002BA46C
STUB_ALPHA = 0x002BF710
STUB_MTX_COPY = 0x002C0000
STUB_GET_LAYOUT = 0x002BF6D0
STUB_MTX_MUL = 0x002B71F8
STUB_SET_MTX = 0x002B9438
STUB_MODE_VAL = 0x002C5FA4
STUB_2BF558 = 0x002BF558
STUB_TEXT_W = 0x002B7118
STUB_DRAW_TEXT = 0x002BE77C
STUB_DRAW_PANEL = 0x002BF460
STUB_KIND4 = 0x002B70F0
STUB_KIND2 = 0x002B6F74
STUB_KIND3 = 0x002BE548
STUB_KIND5 = 0x002B6ECC
STUB_END_PASS = 0x002C1B64
STUB_VP_CB = 0x003F0100
STUB_MODE_CB = 0x003F0200
STUB_MEMCLR4 = 0x003F0300

STUB_NAMES = {
    STUB_BEGIN_PASS: "UiGpu_BeginPass",
    STUB_VP_PARAMS: "UiGpu_SetViewportParams",
    STUB_STEREO: "ui_func_002ba46c",
    STUB_ALPHA: "UiGpu_SetAlphaBlend",
    STUB_MTX_COPY: "engine_func_002c0000",
    STUB_GET_LAYOUT: "camp_func_002bf6d0",
    STUB_MTX_MUL: "ui_func_002b71f8",
    STUB_SET_MTX: "ui_func_002b9438",
    STUB_MODE_VAL: "battle_func_002c5fa4",
    STUB_2BF558: "func_002bf558",
    STUB_TEXT_W: "ui_func_002b7118",
    STUB_DRAW_TEXT: "ui_func_002be77c",
    STUB_DRAW_PANEL: "UiSprite_DrawPanelDirect",
    STUB_KIND4: "ui_func_002b70f0",
    STUB_KIND2: "ui_func_002b6f74",
    STUB_KIND3: "ui_func_002be548",
    STUB_KIND5: "ui_func_002b6ecc",
    STUB_END_PASS: "ui_func_002c1b64",
    STUB_VP_CB: "vp_cb",
    STUB_MODE_CB: "mode_cb",
    STUB_MEMCLR4: "__aeabi_memclr4",
}

PTR_RODATA = 0x00500000
PTR_WORK = 0x20000000
PTR_GPU = 0x20002000
PTR_LAYOUTS = 0x20006000
PTR_DIMS = 0x20008000
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


def _extract_rodata_sections(obj_file: Path) -> dict[str, bytes]:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr_off, shstr_size = sections[e_shstrndx][4], sections[e_shstrndx][5]
    shstr = data[shstr_off : shstr_off + shstr_size]
    out: dict[str, bytes] = {}
    for sh in sections:
        end = shstr.find(b"\x00", sh[0])
        name = shstr[sh[0] : end].decode("utf-8", errors="replace")
        if name.startswith(".rodata"):
            out[name] = data[sh[4] : sh[4] + sh[5]]
    return out


def _get_symbol_offset(obj_file: Path, substr: str) -> int:
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
        if sh[1] == 2:  # SHT_SYMTAB
            str_sec = sections[sh[6]]
            strtab = data[str_sec[4] : str_sec[4] + str_sec[5]]
            sym_off, sym_size, entsize = sh[4], sh[5], sh[9] or 16
            for pos in range(sym_off, sym_off + sym_size, entsize):
                st_name, st_value, _st_size, _st_info, _st_other, _st_shndx = struct.unpack_from("<IIIBBH", data, pos)
                end = strtab.find(b"\x00", st_name)
                name = strtab[st_name:end].decode("utf-8", errors="replace")
                if substr in name and "Draft" not in name:
                    return st_value
    return 0


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "ComWin_DrawUp" in name), None)
    if candidate is None:
        raise RuntimeError(f"ComWin_DrawUp not found in {obj_file}")
    sym_offset = _get_symbol_offset(obj_file, "ComWin_DrawUp")

    ro_secs = _extract_rodata_sections(obj_file)
    ro_blob = bytearray()
    ro_offsets: dict[str, int] = {}
    for sname, sbytes in ro_secs.items():
        ro_offsets[sname] = len(ro_blob)
        ro_blob.extend(sbytes)
        while len(ro_blob) % 16 != 0:
            ro_blob.append(0)

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
            struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        elif rtype == 2:
            addend = struct.unpack_from("<I", code, off)[0]
            if "g_AsdGpuState" in sym_name:
                target = G_ASD_GPU_STATE_ADDR + addend
            elif sym_name in ro_offsets:
                target = PTR_RODATA + ro_offsets[sym_name] + addend
            elif sym_name == "":
                if addend >= sym_offset:
                    target = FUNC_ADDR + (addend - sym_offset)
                else:
                    base_ro = next(iter(ro_offsets.values()), 0)
                    target = PTR_RODATA + base_ro + addend
            elif sym_name.startswith(".L"):
                base_ro = next(iter(ro_offsets.values()), 0)
                target = PTR_RODATA + base_ro + addend
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name} +{addend:#x}")
            struct.pack_into("<I", code, off, target)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), bytes(ro_blob)


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
        self.uc.mem_map(PTR_RODATA, 0x2000)
        self.uc.mem_map(PTR_WORK, 0x10000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        state: int,
        f10: int,
        f12: int,
        kind: int,
        dirty: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_RODATA, b"\x00" * 0x2000)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(G_COMWIN_WORK_PTR, struct.pack("<I", PTR_WORK))
        uc.mem_write(G_ASD_GPU_STATE_ADDR, struct.pack("<I", PTR_GPU))
        uc.mem_write(G_MTX_GUARD, struct.pack("<I", 1))
        ident = [1.0 if r == c else 0.0 for r in range(4) for c in range(4)]
        uc.mem_write(G_MTX_DATA, struct.pack("<16f", *ident))

        uc.mem_write(PTR_WORK, b"\x00" * 0x200)
        uc.mem_write(PTR_WORK + 0x08, struct.pack("<I", state))
        uc.mem_write(PTR_WORK + 0x10, bytes([f10 & 0xFF, 0xFE, f12 & 0xFF]))
        uc.mem_write(PTR_WORK + 0x14, struct.pack("<I", kind))
        uc.mem_write(PTR_WORK + 0x18, struct.pack("<h", -42))
        uc.mem_write(PTR_WORK + 0x5C, struct.pack("<f", 0.75))
        uc.mem_write(PTR_WORK + 0x60, struct.pack("<f", 1.25))
        uc.mem_write(PTR_WORK + 0xE8, struct.pack("<f", 0.4))
        uc.mem_write(PTR_WORK + 0x154, b"BattleMsg\x00")

        uc.mem_write(PTR_GPU, b"\x00" * 0x2000)
        vp_stack = PTR_GPU + 0x124C
        uc.mem_write(vp_stack + 0x00, struct.pack("<I", 0))
        uc.mem_write(vp_stack + 0x08, struct.pack("<I", 0x11110000))
        uc.mem_write(vp_stack + 0x18, bytes([dirty & 0xFF]))
        uc.mem_write(vp_stack + 0x1C, struct.pack("<I", STUB_VP_CB))

        mode_stack = PTR_GPU + 0x12AC
        uc.mem_write(mode_stack + 0x00, struct.pack("<I", 0))
        uc.mem_write(mode_stack + 0x08, struct.pack("<I", 0xAAAA0000))
        uc.mem_write(mode_stack + 0x18, bytes([dirty & 0xFF]))
        uc.mem_write(mode_stack + 0x1C, struct.pack("<I", STUB_MODE_CB))

        for stub_addr in STUB_NAMES:
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
            if addr in (STUB_BEGIN_PASS, STUB_END_PASS):
                calls.append((STUB_NAMES[addr], r0))
            elif addr == STUB_VP_PARAMS:
                calls.append(("vp_params", r0, r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0x22220000)
            elif addr == STUB_STEREO:
                s0 = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                calls.append(("stereo", r0, s0))
                uc_cb.reg_write(arm.UC_ARM_REG_S0, 0x41200000)  # 10.0f
            elif addr == STUB_ALPHA:
                s0 = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                calls.append(("alpha", s0))
            elif addr == STUB_MTX_COPY:
                uc_cb.mem_write(r0, bytes(uc_cb.mem_read(r1, 64)))
            elif addr == STUB_GET_LAYOUT:
                calls.append(("layout", r0, r1))
                lptr = PTR_LAYOUTS + ((r1 & 0xFF) * 0x10)
                dptr = PTR_DIMS + ((r1 & 0xFF) * 0x10)
                uc_cb.mem_write(dptr, struct.pack("<hh", 120, 40))
                uc_cb.mem_write(lptr, b"\x00" * 0x10)
                uc_cb.mem_write(lptr + 0x08, struct.pack("<hh", (r1 & 0xF) + 2, (r1 & 0xF) + 4))
                uc_cb.mem_write(lptr + 0x0C, struct.pack("<I", dptr))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, lptr)
            elif addr == STUB_MTX_MUL:
                a = struct.unpack("<16f", uc_cb.mem_read(r1, 64))
                b = struct.unpack("<16f", uc_cb.mem_read(r2, 64))
                res = [
                    sum(a[row * 4 + k] * b[k * 4 + col] for k in range(4))
                    for row in range(4)
                    for col in range(4)
                ]
                uc_cb.mem_write(r0, struct.pack("<16f", *res))
            elif addr == STUB_SET_MTX:
                m = struct.unpack("<16f", uc_cb.mem_read(r1, 64))
                calls.append(("set_mtx", r0, tuple(round(x, 3) for x in m)))
            elif addr == STUB_MODE_VAL:
                calls.append(("mode_val", r0, r1, r2))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0xBBBB0000 + r1)
            elif addr in (STUB_2BF558, STUB_DRAW_PANEL):
                s0, s1 = struct.unpack("<II", uc_cb.mem_read(sp, 8))
                calls.append((STUB_NAMES[addr], r0, r1, r2, r3, s0, s1))
            elif addr == STUB_TEXT_W:
                calls.append(("text_w", read_cstr(uc_cb, r0), r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 64)
            elif addr == STUB_DRAW_TEXT:
                s0 = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                s1 = uc_cb.reg_read(arm.UC_ARM_REG_S1)
                s2 = uc_cb.reg_read(arm.UC_ARM_REG_S2)
                s3 = uc_cb.reg_read(arm.UC_ARM_REG_S3)
                s4 = uc_cb.reg_read(arm.UC_ARM_REG_S4)
                calls.append(("draw_text", r0, r1, read_cstr(uc_cb, r2), s0, s1, s2, s3, s4))
            elif addr in (STUB_KIND4, STUB_KIND5):
                calls.append((STUB_NAMES[addr], r0, r1, r2, r3))
            elif addr == STUB_KIND2:
                s0, s1 = struct.unpack("<II", uc_cb.mem_read(sp, 8))
                calls.append(("kind2", r0, r1, r2, r3, s0, s1))
            elif addr == STUB_KIND3:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("kind3", r0, r1, r2, r3, s0))
            elif addr in (STUB_VP_CB, STUB_MODE_CB):
                calls.append((STUB_NAMES[addr], r0))
            elif addr == STUB_MEMCLR4:
                uc_cb.mem_write(r0, b"\x00" * r1)

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, 0)
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
        diffs.append("gpu vp stack mismatch")
    if orig["gpu_mode"] != cand["gpu_mode"]:
        diffs.append("gpu mode stack mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("state0", 0, 1, 0, 1, 0),
        ("state2_k1_m0", 2, 1, 0, 1, 1),
        ("state1_k2_m1", 1, 1, 1, 2, 0),
        ("state1_k3", 1, 1, 0, 3, 0),
        ("state1_k4", 1, 1, 0, 4, 0),
        ("state1_k5_notext", 1, 0, 1, 5, 0),
        ("state1_k5_text", 1, 1, 1, 5, 0),
    ]
    for label, st, f10, f12, kind, dirty in cases:
        orig_res = Runner().run(orig_bytes, b"", st, f10, f12, kind, dirty)
        cand_res = Runner().run(cand_bytes, cand_rodata, st, f10, f12, kind, dirty)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_state0", "auto* const work = *reinterpret_cast<u8**>(0x0043E0F8);\n    if (*reinterpret_cast<const u32*>(work + 0x08) == 0)", "auto* const work = *reinterpret_cast<u8**>(0x0043E0F8);\n    if (false)"),
        ("wrong_stereo", "ui_func_002ba46c(g_AsdGpuState, 0.29f)", "ui_func_002ba46c(g_AsdGpuState, 0.50f)"),
        ("wrong_text_scale", "0.57f,", "0.75f,"),
        ("drop_kind1", "if (kind == 1)", "if (false)"),
        ("wrong_mode_panel", "func_002bf558(2, 0x0E, 3, 0, 0, 0x65);", "func_002bf558(2, 0x0E, 4, 0, 0, 0x65);"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, st, f10, f12, kind, dirty in cases:
            if compare(
                Runner().run(orig_bytes, b"", st, f10, f12, kind, dirty),
                Runner().run(mut_bytes, mut_rodata, st, f10, f12, kind, dirty),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: ComWin_DrawUp (0x0011a354) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
