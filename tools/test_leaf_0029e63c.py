#!/usr/bin/env python3
"""Differential test for SortMenu_Init (0x0029e63c) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "camp" / "unite.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0029e63c"

FUNC_ADDR = 0x0029E63C
FUNC_SIZE = 644

MGR_ADDR = 0x0043DD20

STUB_ALLOC = 0x002C4B84
STUB_ZERO = 0x002C4B30
STUB_CREATE_CALC = 0x002C5978
STUB_CREATE_DRAW = 0x002C4C00
STUB_2C3344 = 0x002C3344
STUB_2C32F8 = 0x002C32F8
STUB_2BDB2C = 0x002BDB2C
STUB_2AF854 = 0x002AF854
STUB_2BF030 = 0x002BF030
STUB_2BDAC0 = 0x002BDAC0
STUB_2C4450 = 0x002C4450

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_ZERO: "AsdMem_Zero",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
    STUB_CREATE_DRAW: "AsdTask_CreateDraw",
    STUB_2C3344: "func_002c3344",
    STUB_2C32F8: "func_002c32f8",
    STUB_2BDB2C: "func_002bdb2c",
    STUB_2AF854: "func_002af854",
    STUB_2BF030: "func_002bf030",
    STUB_2BDAC0: "func_002bdac0",
    STUB_2C4450: "func_002c4450",
}

PTR_RODATA = 0x00500000
PTR_WORK = 0x20000000
PTR_CALC_TASK = 0x20010000
PTR_DRAW_TASK = 0x20020000
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
    candidate = next((val for name, val in funcs.items() if "SortMenu_Init" in name), None)
    if candidate is None:
        raise RuntimeError(f"SortMenu_Init not found in {obj_file}")

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
            if sym_name == "" or sym_name.startswith(".L.str") or sym_name == ".rodata.str1.1":
                target = PTR_RODATA + addend
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name} +{addend:#x}")
            struct.pack_into("<I", code, off, target)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), _extract_rodata_str(obj_file)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "unite.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"unite_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"unite_mutant_{name}.o"
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
        self.uc.mem_map(PTR_WORK, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, rodata: bytes, ref_count: int, existing_work: int, mode: int, flag: int) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x800)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_RODATA, b"\x00" * 0x1000)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(MGR_ADDR, struct.pack("<B3xI", ref_count & 0xFF, existing_work))
        uc.mem_write(PTR_WORK, b"\xAA" * 0x878)

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
            if addr == STUB_ALLOC:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc", r0, r1, r2, r3, s0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_WORK)
            elif addr == STUB_ZERO:
                calls.append(("zero", r0, r1))
                uc_cb.mem_write(r0, b"\x00" * r1)
            elif addr == STUB_CREATE_CALC:
                s0, s1, s2 = struct.unpack("<III", uc_cb.mem_read(sp, 12))
                calls.append(("create_calc", read_cstr(uc_cb, r0), r1, r2, r3, s0, s1, s2))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_CALC_TASK)
            elif addr == STUB_CREATE_DRAW:
                s0, s1, s2, s3 = struct.unpack("<IIII", uc_cb.mem_read(sp, 16))
                calls.append(("create_draw", read_cstr(uc_cb, r0), r1, r2, r3, s0, s1, s2, s3))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_DRAW_TASK)
            elif addr == STUB_2C3344:
                calls.append(("2c3344", r0))
            elif addr == STUB_2C32F8:
                args = struct.unpack("<7I", uc_cb.mem_read(sp, 28))
                calls.append(("2c32f8", r0, r1, r2, r3) + args)
            elif addr == STUB_2BDB2C:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                s0f = uc_cb.reg_read(arm.UC_ARM_REG_S0)
                calls.append(("2bdb2c", r0, r1, r2, r3, s0, s0f))
            elif addr in (STUB_2AF854, STUB_2BDAC0, STUB_2C4450):
                calls.append((STUB_NAMES[addr], r0, r1, r2))
            elif addr == STUB_2BF030:
                calls.append(("2bf030", r0, r1))

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, mode & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, flag & 0xFFFFFFFF)
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
            "mgr": bytes(uc.mem_read(MGR_ADDR, 0x08)),
            "work": bytes(uc.mem_read(PTR_WORK, 0x878)),
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
    if orig["mgr"] != cand["mgr"]:
        diffs.append("mgr mismatch")
    if orig["work"] != cand["work"]:
        diffs.append("work mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("ref1_skip", 1, PTR_WORK, 5, 1),
        ("ref0_null_m7_f2", 0, 0, 7, 2),
        ("ref0_existing_m11_f0", 0, PTR_WORK, 11, 0),
    ]
    for label, ref_c, ex_w, mode, flag in cases:
        orig_res = Runner().run(orig_bytes, b"", ref_c, ex_w, mode, flag)
        cand_res = Runner().run(cand_bytes, cand_rodata, ref_c, ex_w, mode, flag)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_ref_guard", "if (static_cast<s8>(mgr[0]) <= 0) {\n        auto* work = *reinterpret_cast<u8**>(mgr + 0x04);\n        if (work == nullptr) {\n            work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, sizeof(SortMenuWork), 1));", "if (static_cast<s8>(mgr[0]) < 0) {\n        auto* work = *reinterpret_cast<u8**>(mgr + 0x04);\n        if (work == nullptr) {\n            work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, sizeof(SortMenuWork), 1));"),
        ("wrong_loop_13", "for (s32 i = 0; i < 0x0D; ++i)", "for (s32 i = 0; i < 0x0C; ++i)"),
        ("wrong_flag_74d", "w2[0x74D] = 1;", "w2[0x74D] = 0;"),
        ("wrong_mode_store", "*reinterpret_cast<s32*>(work + 0x750) = mode;", "*reinterpret_cast<s32*>(work + 0x750) = mode + 1;"),
        ("wrong_flag_store", "work[0x74E] = static_cast<u8>(flag);", "work[0x74E] = 0;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, ref_c, ex_w, mode, flag in cases:
            if compare(
                Runner().run(orig_bytes, b"", ref_c, ex_w, mode, flag),
                Runner().run(mut_bytes, mut_rodata, ref_c, ex_w, mode, flag),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: SortMenu_Init (0x0029e63c) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
