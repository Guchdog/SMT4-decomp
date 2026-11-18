#!/usr/bin/env python3
"""Differential test for aocFileContent_func_0038bd00 (0x0038bd00) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0038bd00"

FUNC_ADDR = 0x0038BD00
FUNC_SIZE = 408

STUB_FREE = 0x002C4360
STUB_PAIR_INIT = 0x002BB09C
STUB_RESULT_CTOR = 0x002BAD80
STUB_GET_SIZE = 0x00355304
STUB_RESULT_VAL = 0x002A1578
STUB_SOUND_ENTRY = 0x002C583C
STUB_CHECK98 = 0x002AD46C
STUB_ALLOC_ALIGN = 0x002C54F0
STUB_WORK_ZERO = 0x002C3B48
STUB_FORMAT = 0x002BE7FC

STUB_NAMES = {
    STUB_FREE: "AsdMem_Free",
    STUB_PAIR_INIT: "AsdFile_Pair_Init",
    STUB_RESULT_CTOR: "Result_Construct",
    STUB_GET_SIZE: "AocContent_GetSize",
    STUB_RESULT_VAL: "Result_Value",
    STUB_SOUND_ENTRY: "AsdSound_GetTableEntry",
    STUB_CHECK98: "AocApplet_Check98",
    STUB_ALLOC_ALIGN: "AsdMem_AllocAlign",
    STUB_WORK_ZERO: "AsdWork_Zero",
    STUB_FORMAT: "UiText_Format",
}

ADDR_APPLET_GLOBAL = 0x00432FC8
RODATA_BASE = 0x18000000
PTR_STATE = 0x20000000
PTR_CONTENT = 0x20001000
PTR_APPLET = 0x20002000
PTR_NEW_BUF = 0x20010000
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
    candidate = next((val for name, val in funcs.items() if "aocFileContent_func_0038bd00" in name), None)
    if candidate is None:
        raise RuntimeError(f"aocFileContent_func_0038bd00 not found in {obj_file}")

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
            if "g_AocAppletState" in sym_name:
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
    while len(out) < 256:
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
        self.uc.mem_map(PTR_STATE, 0x00020000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        *,
        init_buf: int,
        index: int,
        size_res: int,
        size_val: int,
        check98_ret: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(ADDR_APPLET_GLOBAL, struct.pack("<I", PTR_APPLET))
        uc.mem_write(PTR_STATE, b"\x00" * 0x20)
        uc.mem_write(PTR_CONTENT, b"\x00" * 0x40)
        uc.mem_write(PTR_CONTENT + 0x20, struct.pack("<I", init_buf))
        uc.mem_write(PTR_APPLET, b"\x00" * 0x800)
        uc.mem_write(PTR_APPLET + 0x754, struct.pack("<I", 0x00030001))

        calls: list[tuple[str, tuple[int, ...]]] = []

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
            if address == STUB_FREE:
                calls.append(("free", (r0,)))
                ret_arm(None)
            elif address == STUB_PAIR_INIT:
                uc_inst.mem_write(r0, struct.pack("<II", 0xCAFE0001, 0xCAFE0002))
                calls.append(("pair_init", (r0,)))
                ret_arm(r0)
            elif address == STUB_RESULT_CTOR:
                uc_inst.mem_write(r0, struct.pack("<II", r1, 0xBEEF0001 if r1 != 0 else 0))
                calls.append(("result_ctor", (r1,)))
                ret_arm(r0)
            elif address == STUB_GET_SIZE:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
                uc_inst.mem_write(r0, struct.pack("<I", size_val))
                calls.append(("get_size", (r0, r1, r2, r3, a4, a5)))
                ret_arm(size_res)
            elif address == STUB_RESULT_VAL:
                v = struct.unpack("<I", uc_inst.mem_read(r0, 4))[0]
                calls.append(("result_val", (v,)))
                ret_arm(v)
            elif address == STUB_SOUND_ENTRY:
                calls.append(("sound_entry", (r0,)))
                ret_arm(0)
            elif address == STUB_CHECK98:
                calls.append(("check98", (r0,)))
                ret_arm(check98_ret)
            elif address == STUB_ALLOC_ALIGN:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                flag = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
                calls.append(("alloc_align", (r0, r1, r2, r3, flag)))
                ret_arm(PTR_NEW_BUF)
            elif address == STUB_WORK_ZERO:
                calls.append(("work_zero", (r0, r1)))
                ret_arm(None)
            elif address == STUB_FORMAT:
                fmt = read_cstr(uc_inst, r1)
                assert fmt == "aoc%d:", f"Unexpected fmt {fmt!r}"
                out = f"aoc{r2}:"
                uc_inst.mem_write(r0, out.encode("ascii") + b"\x00")
                calls.append(("format", (r0, r2)))
                ret_arm(len(out))

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_R0, PTR_STATE)
        uc.reg_write(arm.UC_ARM_REG_R1, PTR_CONTENT)
        uc.reg_write(arm.UC_ARM_REG_R2, index)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        status = uc.mem_read(PTR_STATE, 1)[0]
        res0, res1, f0c, f10 = struct.unpack("<IIII", uc.mem_read(PTR_STATE + 4, 16))
        buf_ptr = struct.unpack("<I", uc.mem_read(PTR_CONTENT + 0x20, 4))[0]
        mount = read_cstr(uc, PTR_CONTENT + 0x24)
        csize = struct.unpack("<I", uc.mem_read(PTR_CONTENT + 0x34, 4))[0]
        flags_754 = struct.unpack("<I", uc.mem_read(PTR_APPLET + 0x754, 4))[0]

        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "status": status,
            "res": (res0, res1),
            "f0c_f10": (f0c, f10),
            "buf_ptr": buf_ptr,
            "mount": mount,
            "csize": csize,
            "flags_754": flags_754,
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "status", "res", "f0c_f10", "buf_ptr", "mount", "csize", "flags_754", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("success_with_prev_buf", {"init_buf": 0x20009000, "index": 3, "size_res": 0, "size_val": 0x1000, "check98_ret": 0}),
        ("success_no_prev_buf", {"init_buf": 0, "index": 0, "size_res": 0, "size_val": 0x400, "check98_ret": 0}),
        ("fail_special_code", {"init_buf": 0, "index": 1, "size_res": 0xC9413891, "size_val": 0, "check98_ret": 1}),
        ("fail_check98_zero", {"init_buf": 0, "index": 2, "size_res": 0xC0000001, "size_val": 0, "check98_ret": 0}),
        ("fail_check98_nonzero", {"init_buf": 0, "index": 4, "size_res": 0xC0000001, "size_val": 0, "check98_ret": 1}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_free", "AsdMem_Free(content->buffer);", ""),
        ("wrong_a2_const", "AocContent_GetSize(&content->size, 0x0e5c, index,", "AocContent_GetSize(&content->size, 0x0e5d, index,"),
        ("drop_special_code", "if (Result_Value(&size_status) != 0xC9413891u)", "if (true)"),
        ("drop_flag_clear", "g_AocAppletState->flags_754 &= ~0x10000u;\n                state->status = 0xC8;", "state->status = 0xC8;"),
        ("wrong_status_c8", "state->status = 0xC8;", "state->status = 0xC9;"),
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
        f"PASS: aocFileContent_func_0038bd00 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
