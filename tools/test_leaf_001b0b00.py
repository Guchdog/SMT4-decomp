#!/usr/bin/env python3
"""Differential test for aocMain_func_001b0b00 (0x001b0b00) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "aoc.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_001b0b00"

FUNC_ADDR = 0x001B0B00
FUNC_SIZE = 408

STUB_ALLOC = 0x002C4B84
STUB_MODE_SET = 0x00282E6C
STUB_CREATE_CALC = 0x002C5978
STUB_CREATE_DRAW = 0x002C4C00

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_MODE_SET: "AocMode_Set",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
    STUB_CREATE_DRAW: "AsdTask_CreateDraw",
}

ADDR_MAIN_GLOBAL = 0x00433048
RODATA_BASE = 0x18000000
PTR_MAIN = 0x20010000
PTR_TASK_BASE = 0x20020000
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
    candidate = next((val for name, val in funcs.items() if "aocMain_func_001b0b00" in name), None)
    if candidate is None:
        raise RuntimeError(f"aocMain_func_001b0b00 not found in {obj_file}")

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
            if "g_AocMain" in sym_name:
                struct.pack_into("<I", code, off, ADDR_MAIN_GLOBAL)
            elif sym_name == "":
                addend = struct.unpack_from("<I", code, off)[0]
                struct.pack_into("<I", code, off, RODATA_BASE + addend)
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name}")
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "aoc.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"aoc_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"aoc_mutant_{name}.o"
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
        self.uc.mem_map(PTR_MAIN, 0x00020000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, rodata: bytes, *, mode: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(ADDR_MAIN_GLOBAL, struct.pack("<I", 0))
        uc.mem_write(PTR_MAIN, b"\xAA" * 0x20)

        calls: list[tuple[str, tuple[object, ...]]] = []
        task_seq = [PTR_TASK_BASE]

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
                ret_arm(PTR_MAIN)
            elif address == STUB_MODE_SET:
                calls.append(("mode_set", (r0, r1)))
                ret_arm(None)
            elif address == STUB_CREATE_CALC:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5, a6 = struct.unpack("<III", uc_inst.mem_read(sp, 12))
                calls.append(("create_calc", (read_cstr(uc_inst, r0), r1, r2, r3, a4, a5, a6)))
                t = task_seq[0]
                task_seq[0] += 0x100
                ret_arm(t)
            elif address == STUB_CREATE_DRAW:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5, a6, a7 = struct.unpack("<IIII", uc_inst.mem_read(sp, 16))
                calls.append(("create_draw", (read_cstr(uc_inst, r0), r1, r2, r3, a4, a5, a6, a7)))
                t = task_seq[0]
                task_seq[0] += 0x100
                ret_arm(t)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_R0, mode)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        main_ptr = struct.unpack("<I", uc.mem_read(ADDR_MAIN_GLOBAL, 4))[0]
        main_task = struct.unpack("<I", uc.mem_read(main_ptr, 4))[0]
        draw_task = struct.unpack("<I", uc.mem_read(main_ptr + 0x0C, 4))[0]
        f18, f19, f1a = uc.mem_read(main_ptr + 0x18, 3)
        f1c = struct.unpack("<I", uc.mem_read(main_ptr + 0x1C, 4))[0]

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "main_ptr": main_ptr,
            "main_task": main_task,
            "draw_task": draw_task,
            "flags": (f18, f19, f1a, f1c),
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("ret", "sp", "callee", "main_ptr", "main_task", "draw_task", "flags", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("mode_zero", {"mode": 0}),
        ("mode_nonzero", {"mode": 1}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_mode_zero", "if (mode == 0) {", "if (false) {"),
        ("drop_mode_set1", "AocMode_Set(1, 0xFF);", ""),
        ("wrong_main_prio", "\"AOCMainProc\", 2, 0, 0,", "\"AOCMainProc\", 3, 0, 0,"),
        ("wrong_draw_l_prio", "\"AOCDrawUp L\", 0x7D, 1, 0,", "\"AOCDrawUp L\", 0x7E, 1, 0,"),
        ("wrong_draw_down_cb", "0x0020EBC8u", "0x001E4618u"),
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
        f"PASS: aocMain_func_001b0b00 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
