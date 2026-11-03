#!/usr/bin/env python3
"""Differential test for batch 31 C part 9:
- script_vm_func_0026ac34 (0x0026AC34, 172 B)
- script_vm_func_0026c8c0 (0x0026C8C0, 188 B)
- script_vm_func_002711e0 (0x002711E0, 160 B)
- script_vm_func_00275a8c (0x00275A8C, 188 B)
- script_vm_func_002760bc (0x002760BC, 180 B)
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
    uc.mem_map(0x10000000, 0x00100000)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_script_vm_func_0026ac34():
    addr = 0x0026ac34
    print(f"--- Testing script_vm_func_0026ac34 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 172)
    tmp = ROOT / "build" / "test_31c_part09"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0026ac34", tmp)

    FN_2B9364 = 0x002B9364
    sym_map = {
        "func_002b9364": FN_2B9364,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arg0, arg1, arg2_vals: list[int], entries: list[tuple[int, int]], arg4):
        uc = create_emulator()
        uc.mem_write(addr, code)

        base_addr = 0x10050000
        base_mem = bytearray(0x80)
        for idx, (thresh, val) in enumerate(entries):
            off = 0x4C + idx * 4
            struct.pack_into("<HH", base_mem, off, thresh, val)
        uc.mem_write(base_addr, bytes(base_mem))

        arg2_addr = 0x10051000
        uc.mem_write(arg2_addr, struct.pack("<8H", *arg2_vals))

        arg3_addr = 0x10052000
        uc.mem_write(arg3_addr, bytes(16))

        def stub_2b9(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, base_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2b9, None, FN_2B9364, FN_2B9364)

        sp = STACK_BASE + 0x8000
        uc.mem_write(sp, struct.pack("<I", arg4))

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2_addr)
        uc.reg_write(UC_ARM_REG_R3, arg3_addr)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret_r0 = uc.reg_read(UC_ARM_REG_R0)
        out_vals = struct.unpack(f"<{ret_r0}H", uc.mem_read(arg3_addr, ret_r0 * 2)) if ret_r0 > 0 else ()
        return ret_r0, out_vals

    test_arg2 = [100, 101, 102, 103, 104, 105, 106, 107]
    test_entries = [
        (10, 50),   # thresh 10 > arg1(5), val 50 not in arg2 -> added!
        (2, 51),    # thresh 2 <= arg1(5) -> skipped
        (20, 103),  # thresh 20 > 5, val 103 in arg2 -> skipped
        (15, 0),    # val 0 -> skipped
        (30, 52),   # thresh 30 > 5, val 52 not in arg2 -> added!
        (5, 53),    # thresh 5 <= 5 -> skipped
        (12, 100),  # in arg2 -> skipped
        (40, 54),   # thresh 40 > 5, val 54 not in arg2 -> added!
    ]

    # Case 1: arg4 == 0
    r_orig, o_orig = run_one(orig_code, 1, 5, test_arg2, test_entries, 0)
    r_dec, o_dec = run_one(decomp_code, 1, 5, test_arg2, test_entries, 0)
    assert (r_orig, o_orig) == (r_dec, o_dec) == (3, (50, 52, 54)), f"26ac34 mismatch: {r_orig}, {o_orig} vs {r_dec}, {o_dec}"

    # Case 2: arg4 != 0 -> 0
    r_orig, o_orig = run_one(orig_code, 1, 5, test_arg2, test_entries, 1)
    r_dec, o_dec = run_one(decomp_code, 1, 5, test_arg2, test_entries, 1)
    assert (r_orig, o_orig) == (r_dec, o_dec) == (0, ())

    print("script_vm_func_0026ac34 PASS")

def test_script_vm_func_0026c8c0():
    addr = 0x0026c8c0
    print(f"--- Testing script_vm_func_0026c8c0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 188)
    tmp = ROOT / "build" / "test_31c_part09"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_0026c8c0", tmp)

    FN_2AE3F0 = 0x002AE3F0
    FN_259018 = 0x00259018
    FN_2B66EC = 0x002B66EC
    FN_29AC70 = 0x0029AC70
    FN_2A89E4 = 0x002A89E4
    FN_29ABC0 = 0x0029ABC0

    sym_map = {
        "func_002ae3f0": FN_2AE3F0,
        "func_00259018": FN_259018,
        "func_002b66ec": FN_2B66EC,
        "func_0029ac70": FN_29AC70,
        "func_002a89e4": FN_2A89E4,
        "battle_func_0029abc0": FN_29ABC0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arg0, arg1, arg2, arg3, has_r4: bool, ret_259: int, cur_mp: int, cost: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        r4_addr = 0x10050000 if has_r4 else 0
        if has_r4:
            uc.mem_write(r4_addr + 0x20, struct.pack("<H", 0x123))

        p_addr = 0x10051000
        uc.mem_write(p_addr + 0x2C, struct.pack("<H", cur_mp))

        calls = []
        def stub_2ae(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, r4_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_259(uc, address, size, user_data):
            calls.append("259")
            uc.reg_write(UC_ARM_REG_R0, ret_259)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_b66(uc, address, size, user_data):
            calls.append("b66")
            uc.reg_write(UC_ARM_REG_R0, p_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_9ac(uc, address, size, user_data):
            calls.append("9ac")
            uc.reg_write(UC_ARM_REG_R0, cost)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_9e4(uc, address, size, user_data):
            calls.append("9e4")
            uc.reg_write(UC_ARM_REG_R0, p_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_abc(uc, address, size, user_data):
            calls.append("abc")
            uc.reg_write(UC_ARM_REG_R0, cost)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2ae, None, FN_2AE3F0, FN_2AE3F0)
        uc.hook_add(UC_HOOK_CODE, stub_259, None, FN_259018, FN_259018)
        uc.hook_add(UC_HOOK_CODE, stub_b66, None, FN_2B66EC, FN_2B66EC)
        uc.hook_add(UC_HOOK_CODE, stub_9ac, None, FN_29AC70, FN_29AC70)
        uc.hook_add(UC_HOOK_CODE, stub_9e4, None, FN_2A89E4, FN_2A89E4)
        uc.hook_add(UC_HOOK_CODE, stub_abc, None, FN_29ABC0, FN_29ABC0)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret_r0 = uc.reg_read(UC_ARM_REG_R0)
        final_mp = struct.unpack("<H", uc.mem_read(p_addr + 0x2C, 2))[0]
        return ret_r0, final_mp, calls

    # Case 1: r4 is null -> returns 1
    r_orig, m_orig, c_orig = run_one(orig_code, -1, 1, 2, 0, False, 0, 100, 10)
    r_dec, m_dec, c_dec = run_one(decomp_code, -1, 1, 2, 0, False, 0, 100, 10)
    assert (r_orig, m_orig, c_orig) == (r_dec, m_dec, c_dec) == (1, 100, [])

    # Case 2: arg0 < 0, arg3 == 0, ret_259 == 0, cur_mp=100, cost=30 -> mp=70
    r_orig, m_orig, c_orig = run_one(orig_code, -1, 1, 2, 0, True, 0, 100, 30)
    r_dec, m_dec, c_dec = run_one(decomp_code, -1, 1, 2, 0, True, 0, 100, 30)
    assert (r_orig, m_orig, c_orig) == (r_dec, m_dec, c_dec)
    assert m_orig == 70

    # Case 3: arg0 < 0, cost > cur_mp -> mp=0
    r_orig, m_orig, c_orig = run_one(orig_code, -1, 1, 2, 0, True, 0, 20, 30)
    r_dec, m_dec, c_dec = run_one(decomp_code, -1, 1, 2, 0, True, 0, 20, 30)
    assert (r_orig, m_orig, c_orig) == (r_dec, m_dec, c_dec)
    assert m_orig == 0

    # Case 4: arg0 >= 0, cur_mp=50, cost=15 -> mp=35
    r_orig, m_orig, c_orig = run_one(orig_code, 2, 1, 2, 0, True, 0, 50, 15)
    r_dec, m_dec, c_dec = run_one(decomp_code, 2, 1, 2, 0, True, 0, 50, 15)
    assert (r_orig, m_orig, c_orig) == (r_dec, m_dec, c_dec)
    assert m_orig == 35

    print("script_vm_func_0026c8c0 PASS")

def test_script_vm_func_002711e0():
    addr = 0x002711e0
    print(f"--- Testing script_vm_func_002711e0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part09"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002711e0", tmp)

    FN_27F6FC = 0x0027F6FC
    sym_map = {
        "func_0027f6fc": FN_27F6FC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, in_vec: list[float], hit_on_iter: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        vec_addr = 0x10050000
        uc.mem_write(vec_addr, struct.pack("<3f", *in_vec))

        cur_iter = [0]
        def stub_27f(uc, address, size, user_data):
            cur_iter[0] += 1
            ret = 1 if (cur_iter[0] == hit_on_iter) else 0
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_27f, None, FN_27F6FC, FN_27F6FC)

        uc.reg_write(UC_ARM_REG_R0, vec_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_vec = struct.unpack("<3f", uc.mem_read(vec_addr, 12))
        return [round(v, 4) for v in out_vec], cur_iter[0]

    # Case 1: hits on iter 1 (Y + 1.0f)
    v_orig, it_orig = run_one(orig_code, [10.0, 50.0, 30.0], 1)
    v_dec, it_dec = run_one(decomp_code, [10.0, 50.0, 30.0], 1)
    assert (v_orig, it_orig) == (v_dec, it_dec) == ([10.0, 51.0, 30.0], 1)

    # Case 2: hits on iter 3 (Y + 1.0f - 15.0f - 15.0f = Y - 29.0f)
    v_orig, it_orig = run_one(orig_code, [10.0, 50.0, 30.0], 3)
    v_dec, it_dec = run_one(decomp_code, [10.0, 50.0, 30.0], 3)
    assert (v_orig, it_orig) == (v_dec, it_dec) == ([10.0, 21.0, 30.0], 3)

    # Case 3: never hits (6 total calls: 1 + 5)
    v_orig, it_orig = run_one(orig_code, [10.0, 100.0, 30.0], 99)
    v_dec, it_dec = run_one(decomp_code, [10.0, 100.0, 30.0], 99)
    assert (v_orig, it_orig) == (v_dec, it_dec) == ([10.0, 26.0, 30.0], 6)

    print("script_vm_func_002711e0 PASS")

def test_script_vm_func_00275a8c():
    addr = 0x00275a8c
    print(f"--- Testing script_vm_func_00275a8c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 188)
    tmp = ROOT / "build" / "test_31c_part09"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_00275a8c", tmp)

    FN_287A3C = 0x00287A3C
    sym_map = {
        "func_00287a3c": FN_287A3C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, b9: int, b8: int, items_config: list[tuple[int, int, int, int]]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        mgr_ptr = 0x00448C20
        mgr_addr = 0x10050000
        uc.mem_write(mgr_ptr, struct.pack("<I", mgr_addr))

        mgr_data = bytearray(0x200)
        mgr_data[8] = b8
        mgr_data[9] = b9
        struct.pack_into("<I", mgr_data, 4, len(items_config))
        for i, (act, itype, p14, p18) in enumerate(items_config):
            off = i * 32
            mgr_data[off + 0x0C] = act
            struct.pack_into("<h", mgr_data, off + 0x1C, itype)
            struct.pack_into("<I", mgr_data, off + 0x14, p14)
            struct.pack_into("<I", mgr_data, off + 0x18, p18)
        uc.mem_write(mgr_addr, bytes(mgr_data))

        calls = []
        def stub_287(uc, address, size, user_data):
            arg = uc.reg_read(UC_ARM_REG_R0)
            calls.append(arg)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_287, None, FN_287A3C, FN_287A3C)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_mgr = uc.mem_read(mgr_addr, 0x100)
        return out_mgr, calls

    items = [
        (1, 0, 0x10061000, 0),          # type 0 -> calls with 0x10061000, clears p14
        (1, 1, 0x10062000, 0x10063000), # type 1 (p18!=0) -> calls with 0x10062000, clears p14, p18, f1e
        (1, 1, 0x10064000, 0),          # type 1 (p18==0) -> skips
        (0, 0, 0x10065000, 0),          # inactive -> skips
    ]

    # Case 1: normal processing
    m_orig, c_orig = run_one(orig_code, 1, 0, items)
    m_dec, c_dec = run_one(decomp_code, 1, 0, items)
    assert (m_orig, c_orig) == (m_dec, c_dec)
    assert c_orig == [0x10061000, 0x10062000]

    # Case 2: b9 == 0 -> early return
    m_orig, c_orig = run_one(orig_code, 0, 0, items)
    m_dec, c_dec = run_one(decomp_code, 0, 0, items)
    assert (m_orig, c_orig) == (m_dec, c_dec)
    assert c_orig == []

    # Case 3: b8 == 1 -> already processed
    m_orig, c_orig = run_one(orig_code, 1, 1, items)
    m_dec, c_dec = run_one(decomp_code, 1, 1, items)
    assert (m_orig, c_orig) == (m_dec, c_dec)
    assert c_orig == []

    print("script_vm_func_00275a8c PASS")

def test_script_vm_func_002760bc():
    addr = 0x002760bc
    print(f"--- Testing script_vm_func_002760bc ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 180)
    tmp = ROOT / "build" / "test_31c_part09"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002760bc", tmp)

    sym_map = {}
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, b284: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        objA = 0x0049F91C
        uc.mem_write(objA, bytes(0x350))
        uc.mem_write(objA + 0x284, bytes([b284]))
        uc.mem_write(objA + 8, struct.pack("<I", 0x11223344))

        objB = 0x10050000
        uc.mem_write(0x00447E28, struct.pack("<I", objB))
        uc.mem_write(objB + 0x2C, struct.pack("<II", 0xAABBCCDD, 0x55667788))

        objC = 0x10051000
        uc.mem_write(0x00447E88, struct.pack("<I", objC))
        uc.mem_write(objC + 0x1C, struct.pack("<3f", 1.5, 2.5, 3.5))
        uc.mem_write(objC + 0x4C, struct.pack("<I", 0x99887766))

        objD = 0x10052000
        uc.mem_write(0x004474F4, struct.pack("<I", objD))
        uc.mem_write(objD + 0x18, struct.pack("<I", 0x12345678))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.mem_read(objA, 0x350)

    # Case 1: b284 != 0 -> clears to 0 and exits
    m_orig = run_one(orig_code, 1)
    m_dec = run_one(decomp_code, 1)
    assert m_orig == m_dec
    assert m_orig[0x284] == 0 and m_orig[0x2F8] == 0

    # Case 2: b284 == 0 -> snapshots
    m_orig = run_one(orig_code, 0)
    m_dec = run_one(decomp_code, 0)
    assert m_orig == m_dec
    assert m_orig[0x2F8] == 1

    print("script_vm_func_002760bc PASS")

if __name__ == "__main__":
    test_script_vm_func_0026ac34()
    test_script_vm_func_0026c8c0()
    test_script_vm_func_002711e0()
    test_script_vm_func_00275a8c()
    test_script_vm_func_002760bc()
    print("\nALL 5 FUNCTIONS IN PART 09 PASSED PERFECTLY!")
