#!/usr/bin/env python3
"""Differential test for GauntletAppMenu_Init (0x002e2454) with Unicorn ARM.

Compiles src/camp/camp.cpp, extracts GauntletAppMenu_Init, resolves its calls,
globals, and .rodata string literals against the pinned target addresses, and
compares the pinned original (extracted/exefs/code.bin) against the candidate.
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
SOURCE = ROOT / "src" / "camp" / "camp.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_002e2454"

FUNC_ADDR = 0x002E2454
FUNC_SIZE = 764

G_WORK_ADDR = 0x0043DC88
G_TBL_00402994 = 0x00402994
FUNC_329410 = 0x00329410
FUNC_330024 = 0x00330024
FUNC_32B070 = 0x0032B070

STUB_ALLOC = 0x002C4B84
STUB_ZERO = 0x002C4B30
STUB_CREATE_CALC = 0x002C5978
STUB_CREATE_DRAW = 0x002C4C00
STUB_2C0BA8 = 0x002C0BA8
STUB_2488A8 = 0x002488A8
STUB_2976AC = 0x002976AC
STUB_2C0EC4 = 0x002C0EC4
STUB_2C0E9C = 0x002C0E9C
STUB_2C0E4C = 0x002C0E4C
STUB_2C3344 = 0x002C3344
STUB_2C32F8 = 0x002C32F8
STUB_2BDB2C = 0x002BDB2C
STUB_2BDAC0 = 0x002BDAC0
STUB_2BF030 = 0x002BF030
STUB_2C5E2C = 0x002C5E2C
STUB_2972F8 = 0x002972F8

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_ZERO: "AsdMem_Zero",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
    STUB_CREATE_DRAW: "AsdTask_CreateDraw",
    STUB_2C0BA8: "script_vm_func_002c0ba8",
    STUB_2488A8: "camp_func_002488a8",
    STUB_2976AC: "camp_func_002976ac",
    STUB_2C0EC4: "Tbb_GetGlobalSubTable",
    STUB_2C0E9C: "Tbb_GetPayloadData",
    STUB_2C0E4C: "Tbb_GetRowCount",
    STUB_2C3344: "camp_func_002c3344",
    STUB_2C32F8: "camp_func_002c32f8",
    STUB_2BDB2C: "camp_func_002bdb2c",
    STUB_2BDAC0: "camp_func_002bdac0",
    STUB_2BF030: "camp_func_002bf030",
    STUB_2C5E2C: "script_vm_func_002c5e2c",
    STUB_2972F8: "scrScriptProcess_func_002972f8",
}

PTR_WORK = 0x20000000
WORK_SIZE = 0x534
PTR_CALC_TASK = 0x20010000
PTR_DRAW_TASK = 0x20010100
PTR_TBL = 0x20020000
PTR_PAYLOAD = 0x20021000
PTR_MBM = 0x20030000
PTR_BF = 0x20031000
PTR_PROC = 0x20032000
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
        end = shstr.find(b"\x00", sh[0])
        name = shstr[sh[0] : end].decode("utf-8", errors="replace")
        if name == ".rodata.str1.1":
            return data[sh[4] : sh[4] + sh[5]]
    return b""


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "GauntletAppMenu_Init" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"GauntletAppMenu_Init not found in {obj_file}")

    rodata = _extract_rodata_str(obj_file)
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
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_GauntletAppMenuWork" in rel.symbol_name:
                target = G_WORK_ADDR + addend
            elif "g_GauntletAppMenuTable_00402994" in rel.symbol_name:
                target = G_TBL_00402994 + addend
            elif "func_00329410" in rel.symbol_name:
                target = FUNC_329410 + addend
            elif "engine_func_00330024" in rel.symbol_name:
                target = FUNC_330024 + addend
            elif "ui_func_0032b070" in rel.symbol_name:
                target = FUNC_32B070 + addend
            elif rel.symbol_name == "" or rel.symbol_name.startswith(".L.str") or rel.symbol_name == ".rodata.str1.1":
                target = PTR_RODATA + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {rel.symbol_name!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name!r}"
            )
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "camp.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"camp_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"camp_mutant_{name}.o"
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
        self.uc.mem_map(PTR_RODATA, 0x10000)
        self.uc.mem_map(PTR_WORK, 0x40000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self, code: bytes, rodata: bytes, work_ptr: int, flags: dict[int, int]
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(G_WORK_ADDR, struct.pack("<I", work_ptr))
        uc.mem_write(PTR_WORK, b"\xAA" * WORK_SIZE)
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            uc.mem_write(addr, bx_lr)
        uc.mem_write(LR_SENTINEL, bx_lr)

        calls: list[tuple[object, ...]] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            r3 = emu.reg_read(arm.UC_ARM_REG_R3)
            sp = emu.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_ALLOC:
                sp0 = struct.unpack("<I", emu.mem_read(sp, 4))[0]
                calls.append((addr, r0, r1, r2, r3, sp0))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_WORK)
            elif addr == STUB_ZERO:
                calls.append((addr, r0, r1))
                emu.mem_write(r0, b"\x00" * r1)
            elif addr == STUB_CREATE_CALC:
                sp0, sp4, sp8 = struct.unpack("<III", emu.mem_read(sp, 12))
                calls.append((addr, read_cstr(emu, r0), r1, r2, r3, sp0, sp4, sp8))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_CALC_TASK)
            elif addr == STUB_CREATE_DRAW:
                sp0, sp4, sp8, spc = struct.unpack("<IIII", emu.mem_read(sp, 16))
                calls.append((addr, read_cstr(emu, r0), r1, r2, r3, sp0, sp4, sp8, spc))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_DRAW_TASK)
            elif addr == STUB_2C0BA8:
                calls.append((addr, r0))
                emu.reg_write(arm.UC_ARM_REG_R0, flags.get(r0, 0))
            elif addr in (STUB_2488A8, STUB_2BF030):
                calls.append((addr, r0, r1))
            elif addr == STUB_2976AC:
                calls.append((addr, r0))
            elif addr == STUB_2C0EC4:
                calls.append((addr, r0, r1))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_TBL)
            elif addr == STUB_2C0E9C:
                calls.append((addr, r0))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_PAYLOAD)
            elif addr == STUB_2C0E4C:
                calls.append((addr, r0))
                emu.reg_write(arm.UC_ARM_REG_R0, 42)
            elif addr == STUB_2C3344:
                calls.append((addr, r0))
            elif addr == STUB_2C32F8:
                sp_args = struct.unpack("<7I", emu.mem_read(sp, 28))
                calls.append((addr, r0, r1, r2, r3, *sp_args))
            elif addr == STUB_2BDB2C:
                sp0 = struct.unpack("<I", emu.mem_read(sp, 4))[0]
                s0 = emu.reg_read(arm.UC_ARM_REG_S0)
                calls.append((addr, r0, r1, r2, r3, sp0, s0))
            elif addr == STUB_2BDAC0:
                calls.append((addr, r0, r1, r2))
            elif addr == STUB_2C5E2C:
                path = read_cstr(emu, r0)
                calls.append((addr, path))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_MBM if path.endswith(".mbm") else PTR_BF)
            elif addr == STUB_2972F8:
                calls.append((addr, r0, r1))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_PROC)

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if G_WORK_ADDR <= addr < G_WORK_ADDR + 4:
                return
            if PTR_WORK <= addr < PTR_WORK + WORK_SIZE:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=3000)
        for hook in hooks:
            uc.hook_del(hook)

        callee = {
            name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
            for name in CALLEE_SAVED
        }
        callee["d8"] = uc.reg_read(arm.UC_ARM_REG_D8)
        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "g_work": struct.unpack("<I", uc.mem_read(G_WORK_ADDR, 4))[0],
            "work": bytes(uc.mem_read(PTR_WORK, WORK_SIZE)),
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
    if orig["g_work"] != cand["g_work"]:
        diffs.append("g_work mismatch")
    if orig["work"] != cand["work"]:
        diffs.append("work memory mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("null_all0", 0, {}),
        ("existing_flags1", PTR_WORK, {0x520: 1, 0x526: 1, 0x527: 1}),
        ("null_flag521", 0, {0x521: 1}),
    ]
    for label, wptr, flags in cases:
        orig_res = Runner().run(orig_bytes, b"", wptr, flags)
        cand_res = Runner().run(cand_bytes, cand_rodata, wptr, flags)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_size", "kWorkSize = 0x534;", "kWorkSize = 0x538;"),
        ("wrong_flag_id", "0x526", "0x525"),
        ("wrong_u16_3a", "*reinterpret_cast<u16*>(raw + 0x47C + 0x3A) = 2;", "*reinterpret_cast<u16*>(raw + 0x47C + 0x3A) = 3;"),
        ("wrong_mbm_path", '"camp/gauntletApp.mbm"', '"camp/gauntletApp.xmb"'),
        ("swap_bf_mbm", "scrScriptProcess_func_002972f8(bf, mbm);", "scrScriptProcess_func_002972f8(mbm, bf);"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, wptr, flags in cases:
            if compare(Runner().run(orig_bytes, b"", wptr, flags), Runner().run(mut_bytes, mut_rodata, wptr, flags)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: GauntletAppMenu_Init (0x002e2454) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
