#!/usr/bin/env python3
"""Differential test for batch 31 C part 3:
- battle_func_00221c60 (0x00221C60, 168 B)
- script_vm_func_0022a210 (0x0022A210, 160 B)
- battle_func_0022a76c (0x0022A76C, 184 B)
- engine_func_0022b858 (0x0022B858, 180 B)
- func_0022cc38 (0x0022CC38, 180 B)
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
    UC_HOOK_MEM_UNMAPPED,
    UC_HOOK_CODE,
)
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

COMPILED_FUNCTIONS = None
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_c.o"
        compile_tu_armv6k(source, obj)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int]) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym not in symbol_map:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = symbol_map[sym]
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        if inst == 0:
            struct.pack_into("<I", data, reloc.offset, stub_addr)
            continue
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        if (inst & 0xFE000000) == 0xFA000000:
            h = (rel_off >> 1) & 1
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = 0xFA000000 | (h << 24) | imm24
        else:
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)

def unmapped_hook(uc, access, address, size, value, user_data):
    aligned = address & ~0xFFF
    uc.mem_map(aligned, 0x1000)
    return True

def create_emulator() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_battle_func_00221c60():
    addr = 0x00221C60
    print(f"--- Testing battle_func_00221c60 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 168)
    tmp = ROOT / "build" / "test_31c_part03"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_00221c60", tmp)

    FN_2BF41C = 0x002BF41C
    FN_2D8590 = 0x002D8590
    sym_map = {
        "func_002bf41c": FN_2BF41C,
        "func_002d8590": FN_2D8590,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_mgr: bool, flag: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        holder = 0x0043DED0
        mgr = 0x10082000 if has_mgr else 0
        uc.mem_write(holder, struct.pack("<I", mgr))

        calls = []
        def f_41c(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("41c", arg0))
            ret = 1 if (arg0 & 1) else 0
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_590(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("590", arg0, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_41c, None, FN_2BF41C, FN_2BF41C)
        uc.hook_add(UC_HOOK_CODE, f_590, None, FN_2D8590, FN_2D8590)

        if has_mgr:
            mem = bytearray(0x80)
            mem[0x5C] = 0xAA
            for i in range(10):
                struct.pack_into("<I", mem, 0x34 + i * 4, 0x10084000 + i)
            uc.mem_write(mgr, bytes(mem))

        uc.reg_write(UC_ARM_REG_R0, flag)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        mgr_byte = uc.mem_read(mgr + 0x5C, 1)[0] if has_mgr else None
        return calls, mgr_byte

    for has_mgr in [False, True]:
        for flg in [0, 1, 5]:
            c_o, b_o = run_one(orig_code, has_mgr, flg)
            c_d, b_d = run_one(decomp_code, has_mgr, flg)
            assert c_o == c_d, f"221c60 calls mismatch ({has_mgr}, {flg}): orig {c_o} vs decomp {c_d}"
            assert b_o == b_d, f"221c60 byte mismatch ({has_mgr}, {flg}): orig {b_o} vs decomp {b_d}"

    print("battle_func_00221c60: PASS")

def test_script_vm_func_0022a210():
    addr = 0x0022A210
    print(f"--- Testing script_vm_func_0022a210 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part03"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0022a210", tmp)

    FN_2C4360 = 0x002C4360
    FN_2972F8 = 0x002972F8
    sym_map = {
        "func_002c4360": FN_2C4360,
        "func_002972f8": FN_2972F8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, flags_val: int, has_f8: bool, has_fc: bool, has_f10: bool):
        uc = create_emulator()
        uc.mem_write(addr, code)

        holder = 0x00432FC8
        glob = 0x10082000
        self_obj = 0x10083000
        res_obj = 0x10084000

        uc.mem_write(holder, struct.pack("<I", glob))

        # Glob mem
        glob_mem = bytearray(0x800)
        struct.pack_into("<I", glob_mem, 0x754, flags_val)
        uc.mem_write(glob, bytes(glob_mem))

        # Self mem
        self_mem = bytearray(0x20)
        struct.pack_into("<I", self_mem, 8, 0x10085000 if has_f8 else 0)
        struct.pack_into("<I", self_mem, 0xC, 0x10086000 if has_fc else 0)
        struct.pack_into("<I", self_mem, 0x10, 0x10087000 if has_f10 else 0)
        uc.mem_write(self_obj, bytes(self_mem))

        # Res mem (needs 0x108 bytes mapped)
        uc.mem_write(res_obj, bytes(0x200))

        calls = []
        def f_c4360(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("free", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_972f8(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("create", arg0, arg1))
            uc.reg_write(UC_ARM_REG_R0, res_obj)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_c4360, None, FN_2C4360, FN_2C4360)
        uc.hook_add(UC_HOOK_CODE, f_972f8, None, FN_2972F8, FN_2972F8)

        uc.reg_write(UC_ARM_REG_R0, self_obj)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        glob_res = struct.unpack("<I", uc.mem_read(glob + 0x754, 4))[0]
        self_res = uc.mem_read(self_obj, 0x20)
        res_field108 = struct.unpack("<I", uc.mem_read(res_obj + 0x108, 4))[0]
        return ret, calls, glob_res, self_res, res_field108

    cases = [
        (0x10 | 0x20 | 0x05, True, True, True),
        (0x10 | 0x40, True, False, True),
        (0x05, True, True, True),
        (0x20 | 0x40 | 0x02, False, True, False),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"22a210 mismatch on {c}: orig {r_o} vs decomp {r_d}"

    print("script_vm_func_0022a210: PASS")

def test_battle_func_0022a76c():
    addr = 0x0022A76C
    print(f"--- Testing battle_func_0022a76c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 184)
    tmp = ROOT / "build" / "test_31c_part03"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_0022a76c", tmp)

    FN_293C98 = 0x00293C98
    FN_22A640 = 0x0022A640
    sym_map = {
        "func_00293c98": FN_293C98,
        "func_0022a640": FN_22A640,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, flags: int, arg0: int, arg1: int, arg2: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        base = 0x10082000
        mem = bytearray(0x5000)
        struct.pack_into("<I", mem, 0x44A0, flags)
        struct.pack_into("<I", mem, 0x2230, 0x778899AA)
        uc.mem_write(base, bytes(mem))

        calls = []
        def f_93c98(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, base)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_2a640(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            a2 = uc.reg_read(UC_ARM_REG_R2)
            a3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            sp_words = struct.unpack("<iii", uc.mem_read(sp, 12))
            calls.append((a0, a1, a2, a3, sp_words[0], sp_words[1], sp_words[2]))
            uc.reg_write(UC_ARM_REG_R0, 0x12345678)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_93c98, None, FN_293C98, FN_293C98)
        uc.hook_add(UC_HOOK_CODE, f_2a640, None, FN_22A640, FN_22A640)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        return r0, calls

    cases = [
        (0x40, 10, 20, 30),
        (0x100, 10, 20, 30),
        (0x140, 10, 20, 30),
        (0x00, 10, 20, 30),
        (0x00, 10, 0, 30),
    ]

    for c in cases:
        r_o, cl_o = run_one(orig_code, *c)
        r_d, cl_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"22a76c r0 mismatch on {c}: orig {r_o} vs decomp {r_d}"
        assert cl_o == cl_d, f"22a76c calls mismatch on {c}: orig {cl_o} vs decomp {cl_d}"

    print("battle_func_0022a76c: PASS")

def test_engine_func_0022b858():
    addr = 0x0022B858
    print(f"--- Testing engine_func_0022b858 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 180)
    tmp = ROOT / "build" / "test_31c_part03"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0022b858", tmp)

    FN_2AF854 = 0x002AF854
    FN_2333D4 = 0x002333D4
    FN_2337A0 = 0x002337A0
    FN_2A6214 = 0x002A6214
    sym_map = {
        "func_002af854": FN_2AF854,
        "func_002333d4": FN_2333D4,
        "func_002337a0": FN_2337A0,
        "func_002a6214": FN_2A6214,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, chosen_idx: int, val_5a: int, initial_flag: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_addr = 0x10050000
        mem = bytearray(0x2000)
        sub_obj = 0x10060000
        sub_mem = bytearray(0x100)
        struct.pack_into("<H", sub_mem, 0x5A, val_5a)
        uc.mem_map(sub_obj, 0x1000)
        uc.mem_write(sub_obj, bytes(sub_mem))

        # self + 0x530 + chosen_idx * 4 = sub_obj
        struct.pack_into("<I", mem, 0x530 + chosen_idx * 4, sub_obj)
        r1 = val_5a + 1
        mem[0xC78 + r1] = initial_flag

        uc.mem_map(self_addr, 0x10000)
        uc.mem_write(self_addr, bytes(mem))

        calls = []
        def f_af854(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            arg2 = uc.reg_read(UC_ARM_REG_R2)
            calls.append(("af854", arg0 - self_addr, arg1, arg2))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_333d4(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            arg1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("333d4", arg0 - self_addr, arg1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_337a0(uc, address, size, user_data):
            calls.append(("337a0", chosen_idx))
            uc.reg_write(UC_ARM_REG_R0, chosen_idx)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_a6214(uc, address, size, user_data):
            arg0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("a6214", arg0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_af854, None, FN_2AF854, FN_2AF854)
        uc.hook_add(UC_HOOK_CODE, f_333d4, None, FN_2333D4, FN_2333D4)
        uc.hook_add(UC_HOOK_CODE, f_337a0, None, FN_2337A0, FN_2337A0)
        uc.hook_add(UC_HOOK_CODE, f_a6214, None, FN_2A6214, FN_2A6214)

        uc.reg_write(UC_ARM_REG_R0, self_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        # Read back written fields
        c64 = struct.unpack("<I", uc.mem_read(self_addr + 0xC64, 4))[0]
        c60 = struct.unpack("<I", uc.mem_read(self_addr + 0xC60, 4))[0]
        flag_byte = uc.mem_read(self_addr + 0xC78 + r1, 1)[0]
        f631 = uc.mem_read(self_addr + 0x631, 2)
        c58 = uc.mem_read(self_addr + 0xC58, 8)
        cb8 = uc.mem_read(self_addr + 0xCB8, 4)

        return calls, c64, c60, flag_byte, f631, c58, cb8

    cases = [
        (0, 5, 0),
        (2, 5, 1),
        (1, 12, 0),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"22b858 mismatch on {c}"

    print("engine_func_0022b858: PASS")

def test_func_0022cc38():
    addr = 0x0022CC38
    print(f"--- Testing func_0022cc38 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 180)
    tmp = ROOT / "build" / "test_31c_part03"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_0022cc38", tmp)

    FN_24F7E8 = 0x0024F7E8
    FN_24F7A8 = 0x0024F7A8
    sym_map = {
        "func_0024f7e8": FN_24F7E8,
        "func_0024f7a8": FN_24F7A8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, target_id: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        table_addr = 0x0044CE08
        fallback_holder = 0x0044CDF0
        default_obj = 0x10086000

        uc.mem_write(fallback_holder, struct.pack("<II", 0, default_obj))

        # Setup table at 0x0044CE08 (999 entries of 34 bytes)
        # Entry 0: id 105, payload 0x1111
        # Entry 1: id 110, payload 0x2222
        # Entry 2: id -1 (terminator)
        table_mem = bytearray(999 * 34)
        struct.pack_into("<h", table_mem, 0 * 34, 105)
        struct.pack_into("<h", table_mem, 1 * 34, 110)
        struct.pack_into("<h", table_mem, 2 * 34, -1)
        uc.mem_write(table_addr, bytes(table_mem))

        # Mock pool for target_id < 100
        pool_items = [
            (0x10087000, 10),
            (0x10088000, 25),
            (0x10089000, -1),
        ]
        for p_addr, p_id in pool_items:
            buf = bytearray(0x40)
            struct.pack_into("<h", buf, 0x20, p_id)
            uc.mem_write(p_addr, bytes(buf))

        def f_4f7e8(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, len(pool_items))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_4f7a8(uc, address, size, user_data):
            idx = uc.reg_read(UC_ARM_REG_R0)
            ret = pool_items[idx][0] if idx < len(pool_items) else 0
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_4f7e8, None, FN_24F7E8, FN_24F7E8)
        uc.hook_add(UC_HOOK_CODE, f_4f7a8, None, FN_24F7A8, FN_24F7A8)

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_R1, target_id)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    cases = [
        105, # found in table (entry 0 -> table_addr + 2)
        110, # found in table (entry 1 -> table_addr + 34 + 2)
        120, # not found in table -> default_obj
        10,  # found in pool (item 0 -> 0x10087000)
        25,  # found in pool (item 1 -> 0x10088000)
        30,  # not found in pool -> default_obj
    ]

    for c in cases:
        r_o = run_one(orig_code, c)
        r_d = run_one(decomp_code, c)
        assert r_o == r_d, f"22cc38 mismatch on id={c}: orig {hex(r_o)} vs decomp {hex(r_d)}"

    print("func_0022cc38: PASS")

def main():
    test_battle_func_00221c60()
    test_script_vm_func_0022a210()
    test_battle_func_0022a76c()
    test_engine_func_0022b858()
    test_func_0022cc38()
    print("\nALL 5 FUNCTIONS IN LEAF_BATCH31_C PART 03 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
