#!/usr/bin/env python3
"""Differential test for SaveLoadProcess_Init (0x0026b874) with Unicorn ARM.

Compiles src/ui/save_load.cpp, extracts SaveLoadProcess_Init, resolves its
direct calls and .rodata string literals against the pinned target addresses,
and compares the pinned original (extracted/exefs/code.bin) against the
candidate in Unicorn.
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
SOURCE = ROOT / "src" / "ui" / "save_load.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0026b874"

FUNC_ADDR = 0x0026B874
FUNC_SIZE = 304

MGR_ADDR = 0x0043E2F0

STUB_ALLOC = 0x002C4B84
STUB_26B7EC = 0x0026B7EC
STUB_2594CC = 0x002594CC
STUB_2594AC = 0x002594AC
STUB_2C0B94 = 0x002C0B94
STUB_CREATE_CALC = 0x002C5978
STUB_1EC8E4 = 0x001EC8E4

FUNC_002EF9AC = 0x002EF9AC
FUNC_00324D6C = 0x00324D6C

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_26B7EC: "ui_func_0026b7ec",
    STUB_2594CC: "camp_func_002594cc",
    STUB_2594AC: "ui_func_002594ac",
    STUB_2C0B94: "ui_func_002c0b94",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
    STUB_1EC8E4: "ui_func_001ec8e4",
}

PTR_PROC = 0x20000000
PTR_SYS_WORK = 0x20010000
PTR_TASK = 0x20020000
PTR_RODATA = 0x00500000
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
        name = shstr[sh[0] : shstr.find(b"\x00", sh[0])].decode("ascii", "replace")
        if name == ".rodata.str1.1":
            return data[sh[4] : sh[4] + sh[5]]
    return b""


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "SaveLoadProcess_Init" in name), None)
    if candidate is None:
        raise RuntimeError(f"SaveLoadProcess_Init not found in {obj_file}")

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
            insn = struct.unpack_from("<I", code, off)[0]
            disp = ((dst - (FUNC_ADDR + off + 8)) >> 2) & 0x00FFFFFF
            struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        elif rtype == 2:
            addend = struct.unpack_from("<I", code, off)[0]
            if "SaveLoadProcess_Step" in sym_name:
                target_addr = FUNC_002EF9AC + addend
            elif "ui_func_00324d6c" in sym_name:
                target_addr = FUNC_00324D6C + addend
            elif sym_name == "" or sym_name.startswith(".L.str") or sym_name == ".rodata.str1.1":
                target_addr = PTR_RODATA + addend
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name} +{addend:#x}")
            struct.pack_into("<I", code, off, target_addr)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), _extract_rodata_str(obj_file)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "save_load.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"save_load_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"save_load_mutant_{name}.o"
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
        self.uc.mem_map(PTR_PROC, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, rodata: bytes, arg: int, sys_flag: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_RODATA, b"\x00" * 0x1000)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(MGR_ADDR, b"\xAA" * 0x10)
        uc.mem_write(PTR_PROC, b"\xAA" * 0x40)
        uc.mem_write(PTR_SYS_WORK, b"\x00" * 0x20)
        uc.mem_write(PTR_SYS_WORK + 0x03, bytes([sys_flag & 0xFF]))
        uc.mem_write(PTR_TASK, b"\x00" * 0x40)

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
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_PROC)
            elif addr in (STUB_26B7EC, STUB_2594CC, STUB_2594AC):
                calls.append((STUB_NAMES[addr], r0))
            elif addr == STUB_2C0B94:
                calls.append(("sys_work",))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_SYS_WORK)
            elif addr == STUB_CREATE_CALC:
                s0, s1, s2 = struct.unpack("<III", uc_cb.mem_read(sp, 12))
                calls.append(("create_calc", read_cstr(uc_cb, r0), r1, r2, r3, s0, s1, s2))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_TASK)
            elif addr == STUB_1EC8E4:
                calls.append(("1ec8e4", r0, r1, r2))

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, arg)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=2000)
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
            "proc": bytes(uc.mem_read(PTR_PROC, 0x18)),
            "mgr": bytes(uc.mem_read(MGR_ADDR, 0x0C)),
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
        diffs.append(f"calls mismatch (orig {orig['calls']} vs cand {cand['calls']})")
    if orig["proc"] != cand["proc"]:
        diffs.append(f"proc mismatch (orig={orig['proc'].hex()} cand={cand['proc'].hex()})")
    if orig["mgr"] != cand["mgr"]:
        diffs.append(f"mgr mismatch (orig={orig['mgr'].hex()} cand={cand['mgr'].hex()})")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("arg0_flag0", 0, 0),
        ("arg3_flag0", 3, 0),
        ("arg5_flag2", 5, 2),
        ("arg1234_flag1", 0x1234, 1),
    ]
    for label, arg, sys_flag in cases:
        orig_res = Runner().run(orig_bytes, b"", arg, sys_flag)
        cand_res = Runner().run(cand_bytes, cand_rodata, arg, sys_flag)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_alloc_size", "AsdMem_Alloc(0x100, 0x100, 0, 0x18, 1)", "AsdMem_Alloc(0x100, 0x100, 0, 0x1C, 1)"),
        ("wrong_state", "*reinterpret_cast<s32*>(proc + 0x04) = 4;", "*reinterpret_cast<s32*>(proc + 0x04) = 5;"),
        ("wrong_arg_slot", "reinterpret_cast<uintptr_t>(arg)", "reinterpret_cast<uintptr_t>(arg) + 1"),
        ("drop_1ec8e4", "ui_func_001ec8e4(task, 0x80000, 0);\n\n    *reinterpret_cast<u32*>(proc + 0x10) = static_cast<u32>(reinterpret_cast<uintptr_t>(arg));", "*reinterpret_cast<u32*>(proc + 0x10) = static_cast<u32>(reinterpret_cast<uintptr_t>(arg));"),
        ("wrong_mgr_clear", "mgr[0x04] = 0;\n    *reinterpret_cast<u32*>(mgr + 0x08) = 0;", "mgr[0x04] = 1;\n    *reinterpret_cast<u32*>(mgr + 0x08) = 0;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, arg, sys_flag in cases:
            if compare(Runner().run(orig_bytes, b"", arg, sys_flag), Runner().run(mut_bytes, mut_rodata, arg, sys_flag)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: SaveLoadProcess_Init (0x0026b874) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
