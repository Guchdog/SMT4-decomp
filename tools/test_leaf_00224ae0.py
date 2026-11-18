#!/usr/bin/env python3
"""Differential test for aocBootProcess_func_00224ae0 (0x00224ae0) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00224ae0"

FUNC_ADDR = 0x00224AE0
FUNC_SIZE = 276

STUB_ALLOC = 0x002C4B84
STUB_INIT_CALC = 0x002BAACC
STUB_CREATE_CALC = 0x002C5978

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_INIT_CALC: "AocBoot_InitCalc",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
}

ADDR_BOOT_GLOBAL = 0x00432FE0
ADDR_APPLET_GLOBAL = 0x00432FC8
RODATA_BASE = 0x18000000
PTR_PROC_ALLOC = 0x20010000
PTR_PROC_EXIST = 0x20020000
PTR_APPLET = 0x20030000
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
    candidate = next((val for name, val in funcs.items() if "aocBootProcess_func_00224ae0" in name), None)
    if candidate is None:
        raise RuntimeError(f"aocBootProcess_func_00224ae0 not found in {obj_file}")

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
            if "g_AocBootProcess" in sym_name:
                struct.pack_into("<I", code, off, ADDR_BOOT_GLOBAL)
            elif "g_AocAppletState" in sym_name:
                struct.pack_into("<I", code, off, ADDR_APPLET_GLOBAL)
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
        self.uc.mem_map(PTR_PROC_ALLOC, 0x00040000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        *,
        existing_proc: int,
        init_flags: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(ADDR_BOOT_GLOBAL, struct.pack("<II", existing_proc, 0x99))
        uc.mem_write(ADDR_APPLET_GLOBAL, struct.pack("<I", PTR_APPLET))
        uc.mem_write(PTR_PROC_ALLOC, b"\x00" * 0x600)
        uc.mem_write(PTR_PROC_EXIST, b"\x00" * 0x600)
        if existing_proc:
            uc.mem_write(existing_proc + 8, b"\x01\x02")
            uc.mem_write(existing_proc + 0x5F0, struct.pack("<I", 3))
        uc.mem_write(PTR_APPLET, b"\x00" * 0x800)
        uc.mem_write(PTR_APPLET + 0x754, struct.pack("<I", init_flags))

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
                ret_arm(PTR_PROC_ALLOC)
            elif address == STUB_INIT_CALC:
                calls.append(("init_calc", (r0,)))
                ret_arm(None)
            elif address == STUB_CREATE_CALC:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5, a6 = struct.unpack("<III", uc_inst.mem_read(sp, 12))
                calls.append(("create_calc", (read_cstr(uc_inst, r0), r1, r2, r3, a4, a5, a6)))
                ret_arm(PTR_TASK)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        proc_ptr, handle = struct.unpack("<II", uc.mem_read(ADDR_BOOT_GLOBAL, 8))
        task_ptr = struct.unpack("<I", uc.mem_read(proc_ptr, 4))[0]
        f8, f9 = uc.mem_read(proc_ptr + 8, 2)
        f5f0 = struct.unpack("<I", uc.mem_read(proc_ptr + 0x5F0, 4))[0]
        flags_754 = struct.unpack("<I", uc.mem_read(PTR_APPLET + 0x754, 4))[0]

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "proc_ptr": proc_ptr,
            "handle": handle,
            "task_ptr": task_ptr,
            "flags89": (f8, f9),
            "f5f0": f5f0,
            "flags_754": flags_754,
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("ret", "sp", "callee", "proc_ptr", "handle", "task_ptr", "flags89", "f5f0", "flags_754", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("fresh_alloc", {"existing_proc": 0, "init_flags": 0x175}),
        ("reuse_existing", {"existing_proc": PTR_PROC_EXIST, "init_flags": 0xFF}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_alloc_guard", "if (proc == nullptr) {", "if (true) {"),
        ("drop_handle_clear", "g_AocBootProcess.handle = 0;", ""),
        ("drop_init_calc", "AocBoot_InitCalc(proc->calc);", ""),
        ("wrong_task_prio", "\"aocBoot CALC\", 2, 0, 0,", "\"aocBoot CALC\", 3, 0, 0,"),
        ("wrong_flag_mask", "g_AocAppletState->flags_754 &= ~0x70u;", "g_AocAppletState->flags_754 &= ~0x30u;"),
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
        f"PASS: aocBootProcess_func_00224ae0 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
