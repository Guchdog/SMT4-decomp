#!/usr/bin/env python3
"""Differential test for batch 31 C part 10:
- script_vm_func_0027ea24 (0x0027EA24, 192 B)
- ui_func_00282944 (0x00282944, 172 B)
- ui_func_002829f0 (0x002829F0, 160 B)
- ui_func_002876d0 (0x002876D0, 192 B)
- engine_func_002891e0 (0x002891E0, 192 B)
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
    UC_ARM_REG_S0,
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
COMPILED_ST_VALUES = {}
SOURCE = ROOT / "src/engine/leaf_batch31_c.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_c.o"
        compile_tu_armv6k(source, obj)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
        data = obj.read_bytes()
        e_shoff = struct.unpack_from('<I', data, 32)[0]
        e_shentsize = struct.unpack_from('<H', data, 46)[0]
        e_shnum = struct.unpack_from('<H', data, 48)[0]
        sections = [struct.unpack_from('<IIIIIIIIII', data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
        symtab_sec = [s for s in sections if s[1] == 2][0]
        strtab_sec = sections[symtab_sec[6]]
        strtab_data = data[strtab_sec[4]:strtab_sec[4]+strtab_sec[5]]
        count = symtab_sec[5] // 16
        for i in range(count):
            st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from('<IIIBBH', data, symtab_sec[4] + i * 16)
            name = strtab_data[st_name:].split(b'\x00')[0].decode('ascii', errors='ignore')
            if name:
                COMPILED_ST_VALUES[name] = st_value
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int], func_name: str = "") -> bytes:
    data = bytearray(body)
    st_val = COMPILED_ST_VALUES.get(func_name, 0)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym == "":
            inst = struct.unpack_from("<I", data, reloc.offset)[0]
            off_in_fn = inst - st_val
            actual_addr = target_addr + off_in_fn
            struct.pack_into("<I", data, reloc.offset, actual_addr)
            continue
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
    uc.mem_map(0x10000000, 0x00100000)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_script_vm_func_0027ea24():
    addr = 0x0027ea24
    print(f"--- Testing script_vm_func_0027ea24 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0027ea24", tmp)

    FN_296D8C = 0x00296D8C
    FN_2594F0 = 0x002594F0
    FN_2BDAC0 = 0x002BDAC0
    FN_2BEF7C = 0x002BEF7C

    sym_map = {
        "func_00296d8c": FN_296D8C,
        "func_002594f0": FN_2594F0,
        "func_002bdac0": FN_2BDAC0,
        "func_002bef7c": FN_2BEF7C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002891e0")

    def run_one(code, arg0: int, arg1: int, f_val: float, r4_f8: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ptr_addr = 0x0043E128
        r4_addr = 0x10050000
        sub_addr = 0x10052000
        uc.mem_write(ptr_addr, struct.pack("<I", r4_addr))

        r4_data = bytearray(0x200)
        struct.pack_into("<I", r4_data, 8, r4_f8)
        struct.pack_into("<I", r4_data, 0x14, 50)
        struct.pack_into("<I", r4_data, 0x1B8, sub_addr)
        uc.mem_write(r4_addr, bytes(r4_data))

        def stub_296(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_259(uc, address, size, user_data):
            f_raw = struct.unpack("<I", struct.pack("<f", f_val))[0]
            uc.reg_write(UC_ARM_REG_S0, f_raw)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_bda(uc, address, size, user_data):
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_bef(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 100) # returns 100
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_296, None, FN_296D8C, FN_296D8C)
        uc.hook_add(UC_HOOK_CODE, stub_259, None, FN_2594F0, FN_2594F0)
        uc.hook_add(UC_HOOK_CODE, stub_bda, None, FN_2BDAC0, FN_2BDAC0)
        uc.hook_add(UC_HOOK_CODE, stub_bef, None, FN_2BEF7C, FN_2BEF7C)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_r4 = uc.mem_read(r4_addr, 0x30)
        return out_r4

    # Case 1: arg0 == 0 -> r4[0x21] = 0
    m_orig = run_one(orig_code, 0, 10, 700.0, 3)
    m_dec = run_one(decomp_code, 0, 10, 700.0, 3)
    assert m_orig == m_dec
    assert m_orig[0x21] == 0

    # Case 2: arg0 != 0, f > 630.0f (e.g. 700.0f), r4[8] == 3 -> r4[8] becomes 2
    m_orig = run_one(orig_code, 5, 10, 700.0, 3)
    m_dec = run_one(decomp_code, 5, 10, 700.0, 3)
    assert m_orig == m_dec
    assert m_orig[0x21] == 1 and m_orig[0x22] == 1
    # r4[0x14] = 700
    assert struct.unpack_from("<i", m_orig, 0x14)[0] == 700
    # r4[0x18] = 100, r4[0x1C] = 100 + 700 + 42 = 842
    assert struct.unpack_from("<i", m_orig, 0x18)[0] == 100
    assert struct.unpack_from("<i", m_orig, 0x1C)[0] == 842
    assert struct.unpack_from("<i", m_orig, 8)[0] == 2

    # Case 3: arg0 != 0, f <= 630.0f (e.g. 500.0f), r4[8] == 1 -> r4[8] stays 1
    m_orig = run_one(orig_code, 5, 10, 500.0, 1)
    m_dec = run_one(decomp_code, 5, 10, 500.0, 1)
    assert m_orig == m_dec
    assert m_orig[0x21] == 1 and m_orig[0x22] == 0
    assert struct.unpack_from("<i", m_orig, 8)[0] == 1

    print("script_vm_func_0027ea24 PASS")

def test_ui_func_00282944():
    addr = 0x00282944
    print(f"--- Testing ui_func_00282944 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 172)
    tmp = ROOT / "build" / "test_31c_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_00282944", tmp)

    FN_2C34A4 = 0x002C34A4
    sym_map = {
        "func_002c34a4": FN_2C34A4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002891e0")

    def run_one(code, arg0, arg1, arg2, arg3, arg4, arg5, is_empty_list: bool):
        uc = create_emulator()
        uc.mem_write(addr, code)

        node_addr = 0x10050000
        uc.mem_write(node_addr, bytes(0x40))

        list_addr = 0x004EA7D4
        list_mem = bytearray(0x30)
        if not is_empty_list:
            old_head = 0x10055000
            old_tail = 0x10056000
            uc.mem_write(old_head, bytes(0x40))
            uc.mem_write(old_tail, bytes(0x40))
            struct.pack_into("<I", list_mem, 0x0C, old_head)
            struct.pack_into("<I", list_mem, 0x20, old_tail)
        uc.mem_write(list_addr, bytes(list_mem))

        def stub_c34(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, node_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_c34, None, FN_2C34A4, FN_2C34A4)

        sp = STACK_BASE + 0x8000
        # Stack args: [sp, 0] = arg4 (float), [sp, 4] = arg5 (float)
        stack_floats = struct.pack("<ff", arg4, arg5)
        uc.mem_write(sp, stack_floats)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_node = uc.mem_read(node_addr, 0x24)
        out_list = uc.mem_read(list_addr, 0x28)
        return out_node, out_list

    # Case 1: empty list
    n_orig, l_orig = run_one(orig_code, 10, 20, 30, 40, 1.5, 2.5, True)
    n_dec, l_dec = run_one(decomp_code, 10, 20, 30, 40, 1.5, 2.5, True)
    assert (n_orig, l_orig) == (n_dec, l_dec)

    # Case 2: non-empty list
    n_orig, l_orig = run_one(orig_code, 11, 22, 33, 44, -3.5, 4.5, False)
    n_dec, l_dec = run_one(decomp_code, 11, 22, 33, 44, -3.5, 4.5, False)
    assert (n_orig, l_orig) == (n_dec, l_dec)

    print("ui_func_00282944 PASS")

def test_ui_func_002829f0():
    addr = 0x002829f0
    print(f"--- Testing ui_func_002829f0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002829f0", tmp)

    FN_2C34A4 = 0x002C34A4
    sym_map = {
        "func_002c34a4": FN_2C34A4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002891e0")

    def run_one(code, arg0, arg1, arg2, arg3, is_empty_list: bool):
        uc = create_emulator()
        uc.mem_write(addr, code)

        node_addr = 0x10050000
        uc.mem_write(node_addr, bytes(0x40))

        list_addr = 0x004EA7D4
        list_mem = bytearray(0x30)
        if not is_empty_list:
            old_head = 0x10055000
            old_tail = 0x10056000
            uc.mem_write(old_head, bytes(0x40))
            uc.mem_write(old_tail, bytes(0x40))
            struct.pack_into("<I", list_mem, 0x0C, old_head)
            struct.pack_into("<I", list_mem, 0x20, old_tail)
        uc.mem_write(list_addr, bytes(list_mem))

        def stub_c34(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, node_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_c34, None, FN_2C34A4, FN_2C34A4)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_node = uc.mem_read(node_addr, 0x24)
        out_list = uc.mem_read(list_addr, 0x28)
        return out_node, out_list

    n_orig, l_orig = run_one(orig_code, 1, 2, 3, 4, True)
    n_dec, l_dec = run_one(decomp_code, 1, 2, 3, 4, True)
    assert (n_orig, l_orig) == (n_dec, l_dec)

    n_orig, l_orig = run_one(orig_code, 5, 6, 7, 8, False)
    n_dec, l_dec = run_one(decomp_code, 5, 6, 7, 8, False)
    assert (n_orig, l_orig) == (n_dec, l_dec)

    print("ui_func_002829f0 PASS")

def test_ui_func_002876d0():
    addr = 0x002876d0
    print(f"--- Testing ui_func_002876d0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002876d0", tmp)

    FN_2C583C = 0x002C583C
    sym_map = {
        "func_002c583c": FN_2C583C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002891e0")

    def run_one(code, arg0: int, ret_c58: int, f1c: int, m_0c: int, m_10: int, f3c: int, m_2c: int, m_30: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        mgr_addr = 0x004C53C4
        mgr_data = bytearray(0x50)
        struct.pack_into("<I", mgr_data, 0x1C, f1c)
        struct.pack_into("<I", mgr_data, 0x0C, m_0c)
        struct.pack_into("<I", mgr_data, 0x10, m_10)
        struct.pack_into("<I", mgr_data, 0x3C, f3c)
        struct.pack_into("<I", mgr_data, 0x2C, m_2c)
        struct.pack_into("<I", mgr_data, 0x30, m_30)
        uc.mem_write(mgr_addr, bytes(mgr_data))

        def stub_c58(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, ret_c58)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_c58, None, FN_2C583C, FN_2C583C)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Cases:
    # 1. ret_c58 != 0 -> returns 0
    assert run_one(orig_code, 10, 1, 0xFF, 10, 10, 0xFF, 10, 10) == run_one(decomp_code, 10, 1, 0xFF, 10, 10, 0xFF, 10, 10) == 0

    # 2. slot 1 m_0c == arg0, f1c has bit 0x10 (0x30) -> returns 3
    assert run_one(orig_code, 10, 0, 0x11, 10, 20, 0, 0, 0) == run_one(decomp_code, 10, 0, 0x11, 10, 20, 0, 0, 0) == 3

    # 3. slot 1 m_0c == arg0, f1c has bit 2 and not 8 -> returns 1
    assert run_one(orig_code, 10, 0, 0x03, 10, 20, 0, 0, 0) == run_one(decomp_code, 10, 0, 0x03, 10, 20, 0, 0, 0) == 1

    # 4. slot 1 m_10 == arg0 -> returns 3
    assert run_one(orig_code, 20, 0, 0x01, 10, 20, 0, 0, 0) == run_one(decomp_code, 20, 0, 0x01, 10, 20, 0, 0, 0) == 3

    # 5. slot 2 m_2c == arg0, f3c has bit 2 and not 8 -> returns 1
    assert run_one(orig_code, 30, 0, 0, 0, 0, 0x03, 30, 40) == run_one(decomp_code, 30, 0, 0, 0, 0, 0x03, 30, 40) == 1

    # 6. slot 2 m_30 == arg0 -> returns 3
    assert run_one(orig_code, 40, 0, 0, 0, 0, 0x01, 30, 40) == run_one(decomp_code, 40, 0, 0, 0, 0, 0x01, 30, 40) == 3

    # 7. no match -> returns 0
    assert run_one(orig_code, 99, 0, 0x01, 10, 20, 0x01, 30, 40) == run_one(decomp_code, 99, 0, 0x01, 10, 20, 0x01, 30, 40) == 0

    print("ui_func_002876d0 PASS")

def test_engine_func_002891e0():
    addr = 0x002891e0
    print(f"--- Testing engine_func_002891e0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part10"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002891e0", tmp)

    FN_2C2B1C = 0x002C2B1C
    FN_2C0BA8 = 0x002C0BA8

    sym_map = {
        "func_002c2b1c": FN_2C2B1C,
        "func_002c0ba8": FN_2C0BA8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002891e0")

    def run_one(code, arg0: int, ret_144: int, ret_15a: int, p_b3: int, p_e3d: int, p_e14_val: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        p_addr = 0x10050000
        p_mem = bytearray(0x1000)
        p_mem[3] = p_b3
        p_mem[0xE3D] = p_e3d
        if arg0 < 0x40:
            p_mem[0xE14 + arg0] = p_e14_val
        uc.mem_write(p_addr, bytes(p_mem))

        def stub_2b1(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, p_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_0ba(uc, address, size, user_data):
            arg = uc.reg_read(UC_ARM_REG_R0)
            ret = ret_144 if arg == 0x144 else ret_15a
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2b1, None, FN_2C2B1C, FN_2C2B1C)
        uc.hook_add(UC_HOOK_CODE, stub_0ba, None, FN_2C0BA8, FN_2C0BA8)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Cases:
    # 1. arg0 = 0x19, 144 returns 0 -> returns 3
    assert run_one(orig_code, 0x19, 0, 1, 0, 0, 0) == run_one(decomp_code, 0x19, 0, 1, 0, 0, 0) == 3

    # 2. arg0 = 0x66, 144 returns 0 -> returns 3
    assert run_one(orig_code, 0x66, 0, 1, 0, 0, 0) == run_one(decomp_code, 0x66, 0, 1, 0, 0, 0) == 3

    # 3. arg0 = 0x1F, 15A returns 0 -> returns 3
    assert run_one(orig_code, 0x1F, 1, 0, 0, 0, 0) == run_one(decomp_code, 0x1F, 1, 0, 0, 0, 0) == 3

    # 4. p[3] == 1, p[0xE3D] != 3 -> returns 1
    assert run_one(orig_code, 5, 1, 1, 1, 0, 0) == run_one(decomp_code, 5, 1, 1, 1, 0, 0) == 1

    # 5. p[3] == 1, p[0xE3D] == 3 -> returns 0
    assert run_one(orig_code, 5, 1, 1, 1, 3, 0) == run_one(decomp_code, 5, 1, 1, 1, 3, 0) == 0

    # 6. p[3] != 1, arg0 == 0x18 -> returns 2
    assert run_one(orig_code, 0x18, 1, 1, 0, 0, 0) == run_one(decomp_code, 0x18, 1, 1, 0, 0, 0) == 2

    # 7. p[3] != 1, arg0 >= 0x40 -> returns 0
    assert run_one(orig_code, 0x45, 1, 1, 0, 0, 0) == run_one(decomp_code, 0x45, 1, 1, 0, 0, 0) == 0

    # 8. p[3] != 1, p[0xE14 + arg0] == 3 -> returns 0
    assert run_one(orig_code, 5, 1, 1, 0, 0, 3) == run_one(decomp_code, 5, 1, 1, 0, 0, 3) == 0

    # 9. p[3] != 1, p[0xE14 + arg0] != 3 -> returns 1
    assert run_one(orig_code, 5, 1, 1, 0, 0, 0) == run_one(decomp_code, 5, 1, 1, 0, 0, 0) == 1

    print("engine_func_002891e0 PASS")

if __name__ == "__main__":
    test_script_vm_func_0027ea24()
    test_ui_func_00282944()
    test_ui_func_002829f0()
    test_ui_func_002876d0()
    test_engine_func_002891e0()
    print("\nALL 5 FUNCTIONS IN PART 10 PASSED PERFECTLY!")
