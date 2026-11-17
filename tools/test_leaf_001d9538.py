#!/usr/bin/env python3
"""Differential test for shopMain_Proc (0x001d9538) with Unicorn ARM.

Compiles src/shop/shop.cpp, extracts shopMain_Proc, resolves its calls,
globals, jump table, and .rodata string literal against the pinned target
addresses, and compares the pinned original (extracted/exefs/code.bin) against
the candidate in Unicorn.
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
SOURCE = ROOT / "src" / "shop" / "shop.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_001d9538"

FUNC_ADDR = 0x001D9538
FUNC_SIZE = 908

G_MGR_ADDR = 0x0044E050
G_SLOT_ADDR = 0x0044DF80
G_49F91C_ADDR = 0x0049F91C

STUB_3A6528 = 0x003A6528
STUB_343D28 = 0x00343D28
STUB_343D80 = 0x00343D80
STUB_3A65E4 = 0x003A65E4
STUB_2C23F8 = 0x002C23F8
STUB_3A604C = 0x003A604C
STUB_3A0BB0 = 0x003A0BB0
STUB_3A16C8 = 0x003A16C8
STUB_3A3B30 = 0x003A3B30
STUB_263E60 = 0x00263E60
STUB_2B2520 = 0x002B2520
STUB_3A6614 = 0x003A6614
STUB_2BE7FC = 0x002BE7FC
STUB_2C59B8 = 0x002C59B8
STUB_28756C = 0x0028756C
STUB_28753C = 0x0028753C
STUB_2A0678 = 0x002A0678
STUB_29C650 = 0x0029C650

STUB_NAMES = {
    STUB_3A6528: "battle_func_003a6528",
    STUB_343D28: "engine_func_00343d28",
    STUB_343D80: "engine_func_00343d80",
    STUB_3A65E4: "camp_func_003a65e4",
    STUB_2C23F8: "AsdMemory_func_002c23f8",
    STUB_3A604C: "engine_func_003a604c",
    STUB_3A0BB0: "engine_func_003a0bb0",
    STUB_3A16C8: "script_vm_func_003a16c8",
    STUB_3A3B30: "script_vm_func_003a3b30",
    STUB_263E60: "engine_func_00263e60",
    STUB_2B2520: "engine_func_002b2520",
    STUB_3A6614: "engine_func_003a6614",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_2C59B8: "AsdSequence_func_002c59b8",
    STUB_28756C: "engine_func_0028756c",
    STUB_28753C: "engine_func_0028753c",
    STUB_2A0678: "ui_func_002a0678",
    STUB_29C650: "script_vm_func_0029c650",
}

PTR_WORK = 0x20000000
WORK_SIZE = 0x1C
PTR_DATA = 0x20010000
PTR_DATA_RET = 0x20020000
PTR_G_SLOT_MEM = 0x20030000
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


def _get_symbol_offset(obj_file: Path, sym_substr: str) -> int:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum = struct.unpack_from("<HH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    for sh in sections:
        if sh[1] == 2:  # SHT_SYMTAB
            sym_off, sym_size, str_idx, entsize = sh[4], sh[5], sh[6], sh[9]
            str_off, str_size = sections[str_idx][4], sections[str_idx][5]
            strtab = data[str_off : str_off + str_size]
            for pos in range(0, sym_size, entsize):
                st_name, st_value = struct.unpack_from("<II", data, sym_off + pos)
                end = strtab.find(b"\x00", st_name)
                name = strtab[st_name:end].decode("utf-8", errors="replace")
                if sym_substr in name:
                    return st_value
    raise RuntimeError(f"Symbol containing {sym_substr!r} not found in {obj_file}")


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
        if "shopMain_Proc" in name and "Decompiled" not in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"shopMain_Proc not found in {obj_file}")

    sym_offset = _get_symbol_offset(obj_file, "shopMain_Proc")
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
            cond = 0xFA000000 if target == STUB_2BE7FC else (original & 0xFF000000)
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_ShopMainManager" in rel.symbol_name:
                target = G_MGR_ADDR + addend
            elif rel.symbol_name == "":
                target = (
                    FUNC_ADDR + (addend - sym_offset)
                    if addend >= sym_offset
                    else PTR_RODATA + addend
                )
            elif rel.symbol_name.startswith(".L.str") or rel.symbol_name == ".rodata.str1.1":
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
    obj_file = OUT_DIR / "shop.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"shop_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"shop_mutant_{name}.o"
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
        self,
        code: bytes,
        rodata: bytes,
        flag_05: int,
        shop_type: int = 0,
        shop_mode: int = 1,
        flag_14: int = 0,
        flag_0c: int = 0,
        data_word: int = 0,
        battle_ret: int = 0,
        eng_343d28: int = 0,
        eng_28756c: int = 0,
        eng_28753c: int = 0,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x2000)
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(G_MGR_ADDR, struct.pack("<I", PTR_WORK))
        uc.mem_write(G_SLOT_ADDR, struct.pack("<I", 0))
        uc.mem_write(G_49F91C_ADDR + 0x2FC, struct.pack("<I", 0x1000))

        work_bytes = bytearray(WORK_SIZE)
        work_bytes[0x05] = flag_05
        work_bytes[0x06] = shop_type
        struct.pack_into("<i", work_bytes, 0x08, shop_mode)
        work_bytes[0x0C] = flag_0c
        struct.pack_into("<I", work_bytes, 0x10, 0x77)
        work_bytes[0x14] = flag_14
        struct.pack_into("<I", work_bytes, 0x18, PTR_DATA)
        uc.mem_write(PTR_WORK, bytes(work_bytes))

        uc.mem_write(PTR_DATA, struct.pack("<I", data_word) + b"\x00" * 0x900)
        uc.mem_write(PTR_DATA_RET, b"\x00" * 0x900)
        uc.mem_write(PTR_G_SLOT_MEM, b"\xAA" * 8)
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        thumb_bx_lr = struct.pack("<HH", 0x4770, 0x46C0)
        for addr in STUB_NAMES:
            uc.mem_write(addr, thumb_bx_lr if addr == STUB_2BE7FC else bx_lr)
        uc.mem_write(LR_SENTINEL, bx_lr)

        calls: list[tuple[object, ...]] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            r3 = emu.reg_read(arm.UC_ARM_REG_R3)
            sp = emu.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_3A6528:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, battle_ret)
            elif addr == STUB_343D28:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, eng_343d28)
            elif addr in (STUB_343D80,):
                calls.append((addr,))
            elif addr in (STUB_3A65E4, STUB_3A6614):
                calls.append((addr, "stack_buf"))
            elif addr == STUB_2C23F8:
                calls.append((addr, r0))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_G_SLOT_MEM if r0 == 8 else PTR_DATA)
            elif addr == STUB_3A604C:
                calls.append((addr, r0, r1, r2, r3))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_DATA_RET)
            elif addr in (STUB_3A0BB0, STUB_3A16C8, STUB_3A3B30, STUB_263E60, STUB_2B2520):
                calls.append((addr, r0))
            elif addr == STUB_2BE7FC:
                sp0, sp4 = struct.unpack("<Ii", emu.mem_read(sp, 8))
                fmt = read_cstr(emu, r1)
                calls.append((addr, fmt, r2, r3, sp0, sp4))
                emu.mem_write(r0, b"e075_02\x00")
            elif addr == STUB_2C59B8:
                if r0 == 4:
                    buf_bytes = bytes(emu.mem_read(r1, 16))
                    calls.append((addr, r0, buf_bytes[8:16], r2))
                elif r0 == 0x0E:
                    val = struct.unpack("<I", emu.mem_read(r1, 4))[0]
                    calls.append((addr, r0, val, r2))
                else:
                    calls.append((addr, r0, r1, r2))
            elif addr == STUB_28756C:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, eng_28756c)
            elif addr == STUB_28753C:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, eng_28753c)
            elif addr == STUB_2A0678:
                calls.append((addr, r0, r1))
            elif addr == STUB_29C650:
                calls.append((addr, r0))

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if G_SLOT_ADDR <= addr < G_SLOT_ADDR + 4:
                return
            if PTR_WORK <= addr < PTR_WORK + WORK_SIZE:
                return
            if PTR_DATA_RET <= addr < PTR_DATA_RET + 0x900:
                return
            if PTR_G_SLOT_MEM <= addr < PTR_G_SLOT_MEM + 8:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_R0, 0)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=3000)
        for hook in hooks:
            uc.hook_del(hook)

        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {
                name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
                for name in CALLEE_SAVED
            },
            "calls": calls,
            "work": bytes(uc.mem_read(PTR_WORK, WORK_SIZE)),
            "data_ret_860": struct.unpack("<I", uc.mem_read(PTR_DATA_RET + 0x860, 4))[0],
            "g_slot": struct.unpack("<I", uc.mem_read(G_SLOT_ADDR, 4))[0],
            "g_slot_mem": bytes(uc.mem_read(PTR_G_SLOT_MEM, 8)),
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
        diffs.append(f"calls: orig={orig['calls']} cand={cand['calls']}")
    if orig["work"] != cand["work"]:
        diffs.append("work memory mismatch")
    if orig["data_ret_860"] != cand["data_ret_860"]:
        diffs.append("data_ret_860 mismatch")
    if orig["g_slot"] != cand["g_slot"] or orig["g_slot_mem"] != cand["g_slot_mem"]:
        diffs.append("g_slot mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [
        ("s0_exit", dict(flag_05=0, shop_mode=8, battle_ret=1, eng_343d28=0)),
        ("s0_type0_m69", dict(flag_05=0, shop_type=0, shop_mode=0x69, battle_ret=1, eng_343d28=0)),
        ("s0_type1_m4", dict(flag_05=0, shop_type=1, shop_mode=4, battle_ret=0)),
        ("s1_wait", dict(flag_05=1, data_word=0)),
        ("s1_done", dict(flag_05=1, data_word=1)),
        ("s2_cleanup", dict(flag_05=2)),
        ("s3_f14", dict(flag_05=3, flag_14=1, shop_mode=0x6D)),
        ("s3_seq_e", dict(flag_05=3, flag_14=0, eng_28756c=1, eng_28753c=1)),
        ("s3_seq_6", dict(flag_05=3, flag_14=0, eng_28756c=1, eng_28753c=0)),
        ("s3_close", dict(flag_05=3, flag_14=0, eng_28756c=0, flag_0c=0)),
        ("s4_default", dict(flag_05=4)),
    ]
    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_m69", "mode != 0x69 && ", ""),
        ("wrong_m100_sub", "mode -= 0x64;", "mode -= 0x60;"),
        ("drop_s1_bit", "(*static_cast<const u32*>(work->shop_data) & 1) != 0", "false"),
        ("wrong_m6d_val", "(m == 0x6D) ? 2 : 4", "(m == 0x6D) ? 3 : 4"),
        ("drop_flag0c", "if (work->flag_0c == 0)", "if (false)"),
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
        f"PASS: shopMain_Proc (0x001d9538) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
