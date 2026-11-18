#!/usr/bin/env python3
"""Differential test for 3dEventTex_func_00317cdc (0x00317cdc) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00317cdc"

FUNC_ADDR = 0x00317CDC
FUNC_SIZE = 476

STUB_ALLOC = 0x002C4B84
STUB_ZERO = 0x002C4B30
STUB_FIND_ROW = 0x002B087C
STUB_LOAD_MODE = 0x002C1F28
STUB_CREATE_SPRITE = 0x00294334
STUB_CREATE_CALC = 0x002C5978
STUB_CREATE_DRAW = 0x002C4C00

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_ZERO: "AsdMem_Zero",
    STUB_FIND_ROW: "AsdTable_FindBattleRow",
    STUB_LOAD_MODE: "AsdScene_LoadMode",
    STUB_CREATE_SPRITE: "Npc2d_CreateSprite",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
    STUB_CREATE_DRAW: "AsdTask_CreateDraw",
}

RODATA_BASE = 0x18000000
PTR_OBJ = 0x20010000
PTR_ROW = 0x20020000
PTR_SPR = 0x20030000
PTR_TASK_CALC = 0x20040000
PTR_TASK_DRAW = 0x20050000
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


def _read_elf_section(obj_file: Path, sec_name: str) -> bytes:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    str_sh_off = e_shoff + e_shstrndx * e_shentsize
    shstr_off, shstr_sz = struct.unpack_from("<II", data, str_sh_off + 16)
    shstr = data[shstr_off : shstr_off + shstr_sz]
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh_name, _sh_type, _flags, _addr, sh_offset, sh_size = struct.unpack_from("<6I", data, off)
        name = shstr[sh_name:].split(b"\x00", 1)[0].decode("ascii", errors="replace")
        if name == sec_name:
            return data[sh_offset : sh_offset + sh_size]
    return b""


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    rodata = _read_elf_section(obj_file, ".rodata.str1.1")
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "3dEventTex_func_00317cdc" in name), None)
    if candidate is None:
        raise RuntimeError(f"3dEventTex_func_00317cdc not found in {obj_file}")

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
            if sym_name == "":
                addend = struct.unpack_from("<I", code, off)[0]
                struct.pack_into("<I", code, off, RODATA_BASE + addend)
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name}")
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    fs = text.index("void* decomp_func_00317cdc(")
    fe = text.index("\n}\n", fs) + 3
    body = text[fs:fe]
    if body.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"leaf_batch45_b_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"leaf_batch45_b_mutant_{name}.o"
    mutant_src.write_text(text[:fs] + body.replace(old, new, 1) + text[fe:], encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    out = bytearray()
    while len(out) < 128:
        b = uc.mem_read(addr + len(out), 1)[0]
        if b == 0:
            break
        out.append(b)
    return out.decode("ascii", errors="replace")


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(RODATA_BASE, 0x00010000)
        self.uc.mem_map(PTR_OBJ, 0x00050000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        *,
        npc_id: int,
        x: float,
        z: float,
        load_mode_ret: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(PTR_OBJ, b"\xAA" * 0x48)
        uc.mem_write(PTR_ROW, b"\x00" * 0x90)
        uc.mem_write(PTR_ROW + 0x88, struct.pack("<h", -15))

        calls: list[tuple[str, tuple[object, ...]]] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
            if address == STUB_ALLOC:
                calls.append(("alloc", (r0, r1, r2, r3)))
                ret_arm(PTR_OBJ)
            elif address == STUB_ZERO:
                uc_inst.mem_write(r0, b"\x00" * r1)
                calls.append(("zero", (r0, r1)))
                ret_arm(None)
            elif address == STUB_FIND_ROW:
                calls.append(("find_row", (r0,)))
                ret_arm(PTR_ROW)
            elif address == STUB_LOAD_MODE:
                calls.append(("load_mode", ()))
                ret_arm(load_mode_ret)
            elif address == STUB_CREATE_SPRITE:
                calls.append(("create_sprite", (r0, r1)))
                ret_arm(PTR_SPR)
            elif address == STUB_CREATE_CALC:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5, a6 = struct.unpack("<III", uc_inst.mem_read(sp, 12))
                calls.append(("create_calc", (read_cstr(uc_inst, r0), r1, r2, r3, a4, a5, a6)))
                ret_arm(PTR_TASK_CALC)
            elif address == STUB_CREATE_DRAW:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5, a6, a7 = struct.unpack("<IIII", uc_inst.mem_read(sp, 16))
                calls.append(("create_draw", (read_cstr(uc_inst, r0), r1, r2, r3, a4, a5, a6, a7)))
                ret_arm(PTR_TASK_DRAW)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_R0, npc_id)
        uc.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", x))[0])
        uc.reg_write(arm.UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", z))[0])
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "obj": bytes(uc.mem_read(PTR_OBJ, 0x48)),
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("ret", "sp", "callee", "obj", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("x_neg4", {"npc_id": 0x10005, "x": -4.0, "z": 1.5, "load_mode_ret": 1}),
        ("x_neg3", {"npc_id": 12, "x": -3.0, "z": 2.0, "load_mode_ret": 0}),
        ("x_pos3", {"npc_id": 13, "x": 3.0, "z": -1.0, "load_mode_ret": 1}),
        ("x_pos1_5", {"npc_id": 14, "x": 1.5, "z": 0.0, "load_mode_ret": 1}),
        ("x_neg0_5", {"npc_id": 15, "x": -0.5, "z": 3.0, "load_mode_ret": 1}),
        ("x_zero", {"npc_id": 16, "x": 0.0, "z": 4.0, "load_mode_ret": 1}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_alloc_size", "AsdMem_Zero(p, 0x48);", "AsdMem_Zero(p, 0x44);"),
        ("wrong_id_mask", "AsdTable_FindBattleRow(id & 0xFFFFu);", "AsdTable_FindBattleRow(id);"),
        ("wrong_neg_id", "*reinterpret_cast<u32*>(p + 0x00) = static_cast<u16>(0u - id);", "*reinterpret_cast<u32*>(p + 0x00) = static_cast<u16>(id);"),
        ("wrong_pose_neg3", "pose = 3u;", "pose = 4u;"),
        ("wrong_draw_prio", "\"EVE_BtlTexDraw\", 0x6Fu,", "\"EVE_BtlTexDraw\", 0x6Eu,"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, kw in cases:
            if compare(Runner().run(orig_bytes, b"", **kw), Runner().run(mut_bytes, mut_rodata, **kw)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: 3dEventTex_func_00317cdc (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
