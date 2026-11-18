#!/usr/bin/env python3
"""Differential test for Npc2d_func_002523d0 (0x002523d0) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "asd_frame.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_002523d0"

FUNC_ADDR = 0x002523D0
FUNC_SIZE = 336

STUB_ALLOC = 0x002C4B84
STUB_ZERO = 0x002C4B30
STUB_FIND_ROW = 0x002B087C
STUB_LOAD_MODE = 0x002C1F28
STUB_CREATE_SPRITE = 0x00294334
STUB_CREATE_CALC = 0x002C5978

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_ZERO: "AsdMem_Zero",
    STUB_FIND_ROW: "AsdTable_FindBattleRow",
    STUB_LOAD_MODE: "AsdScene_LoadMode",
    STUB_CREATE_SPRITE: "Npc2d_CreateSprite",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
}

RODATA_BASE = 0x18000000
PTR_SPRITE = 0x20010000
PTR_ROW = 0x20020000
PTR_CREATED_SPR = 0x20030000
PTR_TASK = 0x20040000
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
    candidate = next((val for name, val in funcs.items() if "Npc2d_func_002523d0" in name), None)
    if candidate is None:
        raise RuntimeError(f"Npc2d_func_002523d0 not found in {obj_file}")

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
    obj = OUT_DIR / "asd_frame.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"asd_frame_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"asd_frame_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
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
        self.uc.mem_map(PTR_SPRITE, 0x00040000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        *,
        npc_id: int,
        arg1: int,
        pose_arg: int,
        load_mode_ret: int,
        row_4c: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(PTR_SPRITE, b"\xAA" * 0x98)
        uc.mem_write(PTR_ROW, b"\x00" * 0xA0)
        uc.mem_write(PTR_ROW + 0x88, struct.pack("<h", row_4c))

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
                ret_arm(PTR_SPRITE)
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
                ret_arm(PTR_CREATED_SPR)
            elif address == STUB_CREATE_CALC:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5, a6 = struct.unpack("<III", uc_inst.mem_read(sp, 12))
                calls.append(("create_calc", (read_cstr(uc_inst, r0), r1, r2, r3, a4, a5, a6)))
                ret_arm(PTR_TASK)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_R0, npc_id & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, arg1 & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R2, pose_arg & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        sprite_mem = bytes(uc.mem_read(PTR_SPRITE, 0x98))
        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "sprite_mem": sprite_mem,
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("ret", "sp", "callee", "sprite_mem", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("load_mode_nz_pose_neg100", {"npc_id": 0x10005, "arg1": 0x77, "pose_arg": -100, "load_mode_ret": 1, "row_4c": -12}),
        ("load_mode_z_pose_neg60", {"npc_id": 0x12, "arg1": 0x88, "pose_arg": -60, "load_mode_ret": 0, "row_4c": 42}),
        ("pose_pos100", {"npc_id": 0x20, "arg1": 0x11, "pose_arg": 100, "load_mode_ret": 1, "row_4c": 7}),
        ("pose_pos40", {"npc_id": 0x21, "arg1": 0x22, "pose_arg": 40, "load_mode_ret": 1, "row_4c": 8}),
        ("pose_neg10", {"npc_id": 0x22, "arg1": 0x33, "pose_arg": -10, "load_mode_ret": 1, "row_4c": 9}),
        ("pose_zero", {"npc_id": 0x23, "arg1": 0x44, "pose_arg": 0, "load_mode_ret": 1, "row_4c": 10}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_alloc_size", "AsdMem_Zero(sprite, 0x98);\n\n    sprite->field_20 = 1.0f;", "AsdMem_Zero(sprite, 0x94);\n\n    sprite->field_20 = 1.0f;"),
        ("wrong_f28", "sprite->field_28 = 0.25f;\n    sprite->field_04 = 0x1F;\n    sprite->field_08 = arg1;\n    sprite->field_10 = pose_arg;\n    sprite->field_30 = 0;\n    sprite->field_5c = 1;\n\n    void* row = AsdTable_FindBattleRow", "sprite->field_28 = 0.5f;\n    sprite->field_04 = 0x1F;\n    sprite->field_08 = arg1;\n    sprite->field_10 = pose_arg;\n    sprite->field_30 = 0;\n    sprite->field_5c = 1;\n\n    void* row = AsdTable_FindBattleRow"),
        ("wrong_id_mask", "AsdTable_FindBattleRow(id & 0xFFFFu);", "AsdTable_FindBattleRow(id);"),
        ("wrong_neg_id", "sprite->field_00 = static_cast<u16>(0u - id);\n    sprite->field_38 = static_cast<u32>(Npc2d_PoseFromArgument(pose_arg));\n    sprite->field_18 = 0.33f;", "sprite->field_00 = static_cast<u16>(id);\n    sprite->field_38 = static_cast<u32>(Npc2d_PoseFromArgument(pose_arg));\n    sprite->field_18 = 0.33f;"),
        ("wrong_f18", "sprite->field_00 = static_cast<u16>(0u - id);\n    sprite->field_38 = static_cast<u32>(Npc2d_PoseFromArgument(pose_arg));\n    sprite->field_18 = 0.33f;", "sprite->field_00 = static_cast<u16>(0u - id);\n    sprite->field_38 = static_cast<u32>(Npc2d_PoseFromArgument(pose_arg));\n    sprite->field_18 = 0.34f;"),
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
        f"PASS: Npc2d_func_002523d0 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
