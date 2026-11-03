#!/usr/bin/env python3
"""Differential test for batch 31 C part 7:
- battle_func_00247170 (0x00247170, 164 B)
- ui_func_00248650 (0x00248650, 156 B)
- engine_func_0024f9e8 (0x0024F9E8, 172 B)
- battle_func_00250800 (0x00250800, 192 B)
- battle_func_002508c0 (0x002508C0, 160 B)
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys
import math

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
    UC_ARM_REG_S1,
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

def test_battle_func_00247170():
    addr = 0x00247170
    print(f"--- Testing battle_func_00247170 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 164)
    tmp = ROOT / "build" / "test_31c_part07"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_00247170", tmp)

    FN_2AE3F0 = 0x002AE3F0
    FN_1EE3AC = 0x001EE3AC

    sym_map = {
        "func_002ae3f0": FN_2AE3F0,
        "func_001ee3ac": FN_1EE3AC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, flags: int, slot_data: bytes, ret_2ae: int, ret_1ee: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        self_addr = 0x10050000
        mem = bytearray(0x300)
        struct.pack_into("<I", mem, 0, flags)
        mem[0x220:0x220 + len(slot_data)] = slot_data
        uc.mem_write(self_addr, bytes(mem))

        calls = []
        def stub_2ae(uc, address, size, user_data):
            arg = struct.unpack("<h", struct.pack("<H", uc.reg_read(UC_ARM_REG_R0) & 0xFFFF))[0]
            calls.append(("2ae", arg))
            uc.reg_write(UC_ARM_REG_R0, ret_2ae)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_1ee(uc, address, size, user_data):
            calls.append(("1ee",))
            uc.reg_write(UC_ARM_REG_R0, ret_1ee)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2ae, None, FN_2AE3F0, FN_2AE3F0)
        uc.hook_add(UC_HOOK_CODE, stub_1ee, None, FN_1EE3AC, FN_1EE3AC)

        uc.reg_write(UC_ARM_REG_R0, self_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        return r0, calls

    # Test cases:
    # 1. flags & 0x10 != 0, type 2, both pass -> 1
    slot_buf = bytearray(0x80)
    struct.pack_into("<hh", slot_buf, 0, 2, 0x123) # at 0x220
    r_orig, c_orig = run_one(orig_code, 0x10, slot_buf, 1, 1)
    r_dec, c_dec = run_one(decomp_code, 0x10, slot_buf, 1, 1)
    assert (r_orig, c_orig) == (r_dec, c_dec), f"247170 case 1 mismatch: {r_orig} vs {r_dec}"

    # 2. flags & 0x10 != 0, type 3, 2ae fails -> 0
    struct.pack_into("<hh", slot_buf, 0, 3, 0x123)
    r_orig, c_orig = run_one(orig_code, 0x10, slot_buf, 0, 1)
    r_dec, c_dec = run_one(decomp_code, 0x10, slot_buf, 0, 1)
    assert (r_orig, c_orig) == (r_dec, c_dec), f"247170 case 2 mismatch: {r_orig} vs {r_dec}"

    # 3. flags & 0x10 == 0, loop match at slot 2
    slot_buf = bytearray(0x80)
    # slots at 0x228, 0x230, 0x238...
    # offset in slot_buf: 0x228 - 0x220 = 8.
    # slot 0 at 8: type 1
    struct.pack_into("<hh", slot_buf, 8, 1, 0x10)
    # slot 1 at 16: type 4
    struct.pack_into("<hh", slot_buf, 16, 4, 0x20)
    # slot 2 at 24: type 2, arg 0x55
    struct.pack_into("<hh", slot_buf, 24, 2, 0x55)
    r_orig, c_orig = run_one(orig_code, 0, slot_buf, 1, 1)
    r_dec, c_dec = run_one(decomp_code, 0, slot_buf, 1, 1)
    assert (r_orig, c_orig) == (r_dec, c_dec), f"247170 case 3 mismatch: {r_orig} vs {r_dec}"

    # 4. flags & 0x10 == 0, no match
    slot_buf = bytearray(0x80)
    r_orig, c_orig = run_one(orig_code, 0, slot_buf, 1, 1)
    r_dec, c_dec = run_one(decomp_code, 0, slot_buf, 1, 1)
    assert (r_orig, c_orig) == (r_dec, c_dec), f"247170 case 4 mismatch: {r_orig} vs {r_dec}"

    print("battle_func_00247170 PASS")

def test_ui_func_00248650():
    addr = 0x00248650
    print(f"--- Testing ui_func_00248650 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 156)
    tmp = ROOT / "build" / "test_31c_part07"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_00248650", tmp)

    FN_2B73A4 = 0x002B73A4
    FN_2B740C = 0x002B740C
    FN_256C3C = 0x00256C3C

    sym_map = {
        "func_002b73a4": FN_2B73A4,
        "func_002b740c": FN_2B740C,
        "engine_func_00256c3c": FN_256C3C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, angle: float):
        uc = create_emulator()
        uc.mem_write(addr, code)

        dst_addr = 0x004EA95C
        uc.mem_write(dst_addr, bytes(64))

        calls = []
        def stub_cos(uc, address, size, user_data):
            # arg in s0
            s0_raw = uc.reg_read(UC_ARM_REG_S0)
            val = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
            calls.append(("cos", round(val, 4)))
            cos_val = math.cos(val)
            cos_raw = struct.unpack("<I", struct.pack("<f", cos_val))[0]
            uc.reg_write(UC_ARM_REG_S0, cos_raw)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_sin(uc, address, size, user_data):
            s0_raw = uc.reg_read(UC_ARM_REG_S0)
            val = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
            calls.append(("sin", round(val, 4)))
            sin_val = math.sin(val)
            sin_raw = struct.unpack("<I", struct.pack("<f", sin_val))[0]
            uc.reg_write(UC_ARM_REG_S0, sin_raw)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_identity(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            # identity 4x4 matrix
            ident = [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0
            ]
            uc.mem_write(r0, struct.pack("<16f", *ident))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_cos, None, FN_2B73A4, FN_2B73A4)
        uc.hook_add(UC_HOOK_CODE, stub_sin, None, FN_2B740C, FN_2B740C)
        uc.hook_add(UC_HOOK_CODE, stub_identity, None, FN_256C3C, FN_256C3C)

        angle_raw = struct.unpack("<I", struct.pack("<f", angle))[0]
        uc.reg_write(UC_ARM_REG_S0, angle_raw)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_mat = uc.mem_read(dst_addr, 64)
        return out_mat, calls

    for test_angle in [0.0, 1.25, -2.5]:
        m_orig, c_orig = run_one(orig_code, test_angle)
        m_dec, c_dec = run_one(decomp_code, test_angle)
        assert c_orig == c_dec, f"248650 calls mismatch for {test_angle}: {c_orig} vs {c_dec}"
        assert m_orig == m_dec, f"248650 matrix mismatch for {test_angle}"

    print("ui_func_00248650 PASS")

def test_engine_func_0024f9e8():
    addr = 0x0024f9e8
    print(f"--- Testing engine_func_0024f9e8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 172)
    tmp = ROOT / "build" / "test_31c_part07"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_0024f9e8", tmp)

    FN_2502E8 = 0x002502E8
    FN_256C3C = 0x00256C3C
    FN_250108 = 0x00250108
    FN_24FFBC = 0x0024FFBC
    FN_24FF28 = 0x0024FF28

    sym_map = {
        "engine_func_002502e8": FN_2502E8,
        "engine_func_00256c3c": FN_256C3C,
        "func_00250108": FN_250108,
        "func_0024ffbc": FN_24FFBC,
        "func_0024ff28": FN_24FF28,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, opt_vec3: list[float] | None, flag: int, scale: float):
        uc = create_emulator()
        uc.mem_write(addr, code)

        dst_addr = 0x10050000
        uc.mem_write(dst_addr, bytes(0x100))

        vec3_addr = 0
        if opt_vec3 is not None:
            vec3_addr = 0x10051000
            uc.mem_write(vec3_addr, struct.pack("<3f", *opt_vec3))

        calls = []
        def stub(name):
            def handler(uc, address, size, user_data):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                calls.append((name, r0, r1, r2))
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return handler

        uc.hook_add(UC_HOOK_CODE, stub("2502e8"), None, FN_2502E8, FN_2502E8)
        uc.hook_add(UC_HOOK_CODE, stub("256c3c"), None, FN_256C3C, FN_256C3C)
        uc.hook_add(UC_HOOK_CODE, stub("250108"), None, FN_250108, FN_250108)
        uc.hook_add(UC_HOOK_CODE, stub("24ffbc"), None, FN_24FFBC, FN_24FFBC)
        uc.hook_add(UC_HOOK_CODE, stub("24ff28"), None, FN_24FF28, FN_24FF28)

        scale_raw = struct.unpack("<I", struct.pack("<f", scale))[0]
        uc.reg_write(UC_ARM_REG_S0, scale_raw)
        uc.reg_write(UC_ARM_REG_R0, dst_addr)
        uc.reg_write(UC_ARM_REG_R1, vec3_addr)
        uc.reg_write(UC_ARM_REG_R2, flag)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        # In call to 24ff28, check r0 was dst_addr + 0x18
        return calls

    cases = [
        (None, 0, 1.0),
        ([10.0, 20.0, 30.0], 1, 2.5),
        ([1.0, 2.0, 3.0], 0, 0.5),
        (None, 2, 3.0),
    ]

    for v3, flg, sc in cases:
        c_orig = run_one(orig_code, v3, flg, sc)
        c_dec = run_one(decomp_code, v3, flg, sc)
        # Check function sequence and dst arguments
        orig_seq = [c[0] for c in c_orig]
        dec_seq = [c[0] for c in c_dec]
        assert orig_seq == dec_seq, f"24f9e8 call sequence mismatch: {orig_seq} vs {dec_seq}"
        # Check final 24ff28 destination was dst + 0x18 and r2 was 0
        assert c_orig[-1][1] == 0x10050018 and c_dec[-1][1] == 0x10050018
        assert c_orig[-1][3] == 0 and c_dec[-1][3] == 0

    print("engine_func_0024f9e8 PASS")

def test_battle_func_00250800():
    addr = 0x00250800
    print(f"--- Testing battle_func_00250800 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part07"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_00250800", tmp)

    FN_226B2C = 0x00226B2C
    sym_map = {
        "func_00226b2c": FN_226B2C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arg0, arg1, arg2, arg3, arg4, arg5, arg6, list_nodes: list[tuple[int, int, int]] | None):
        uc = create_emulator()
        uc.mem_write(addr, code)

        mgr_ptr_addr = 0x00434290
        mgr_addr = 0x10050000
        uc.mem_write(mgr_ptr_addr, struct.pack("<I", mgr_addr))

        created_obj_addr = 0x10055000
        obj_mem = bytearray(0x80)
        struct.pack_into("<hh", obj_mem, 0, arg0 & 0xFFFF, 5) # id=arg0, f2=5
        uc.mem_write(created_obj_addr, bytes(obj_mem))

        # Build linked list at mgr + 8
        if list_nodes:
            curr_addr = 0x10052000
            uc.mem_write(mgr_addr + 8, struct.pack("<I", curr_addr))
            for i, (ntype, nid, nf2c) in enumerate(list_nodes):
                next_addr = (curr_addr + 0x40) if (i + 1 < len(list_nodes)) else 0
                node = bytearray(0x40)
                struct.pack_into("<h", node, 0, nid)
                node[4] = ntype
                struct.pack_into("<I", node, 0x0C, next_addr)
                struct.pack_into("<I", node, 0x2C, nf2c)
                uc.mem_write(curr_addr, bytes(node))
                curr_addr = next_addr
        else:
            uc.mem_write(mgr_addr, bytes(0x20))

        calls = []
        def stub_226(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            calls.append((r0, r1, r2, r3))
            uc.reg_write(UC_ARM_REG_R0, created_obj_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_226, None, FN_226B2C, FN_226B2C)

        sp = STACK_BASE + 0x8000
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)

        # Stack args: [sp, 0] = arg4, [sp, 4] = arg5, [sp, 8] = arg6
        stack_data = struct.pack("<III", arg4, arg5, arg6)
        uc.mem_write(sp, stack_data)

        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret_r0 = uc.reg_read(UC_ARM_REG_R0)
        obj_res = uc.mem_read(created_obj_addr, 0x60)
        return ret_r0, obj_res, calls

    # Case 1: arg4 = 0, arg3 = 0
    r_orig, m_orig, c_orig = run_one(orig_code, 0x12, 0x34, 0x56, 0, 0, 0x78, 0x9A, None)
    r_dec, m_dec, c_dec = run_one(decomp_code, 0x12, 0x34, 0x56, 0, 0, 0x78, 0x9A, None)
    assert (r_orig, m_orig, c_orig) == (r_dec, m_dec, c_dec), f"250800 case 1 mismatch"

    # Case 2: arg4 = 0, arg3 = 1
    r_orig, m_orig, c_orig = run_one(orig_code, 0x12, 0x34, 0x56, 1, 0, 0x78, 0x9A, None)
    r_dec, m_dec, c_dec = run_one(decomp_code, 0x12, 0x34, 0x56, 1, 0, 0x78, 0x9A, None)
    assert (r_orig, m_orig, c_orig) == (r_dec, m_dec, c_dec), f"250800 case 2 mismatch"

    # Case 3: arg4 = 1, list matches!
    nodes = [
        (0x10, 0x12, 0x56), # wrong type
        (0x31, 0x99, 0x56), # wrong id
        (0x31, 0x12, 0x99), # wrong f2c
        (0x31, 0x12, 0x56), # match!
    ]
    r_orig, m_orig, c_orig = run_one(orig_code, 0x12, 0x34, 0x56, 1, 1, 0x78, 0x9A, nodes)
    r_dec, m_dec, c_dec = run_one(decomp_code, 0x12, 0x34, 0x56, 1, 1, 0x78, 0x9A, nodes)
    assert (r_orig, m_orig, c_orig) == (r_dec, m_dec, c_dec), f"250800 case 3 mismatch"
    # verify f2 was set to -1
    assert struct.unpack_from("<h", m_orig, 2)[0] == -1

    print("battle_func_00250800 PASS")

def test_battle_func_002508c0():
    addr = 0x002508c0
    print(f"--- Testing battle_func_002508c0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part07"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002508c0", tmp)

    FN_293C98 = 0x00293C98
    FN_282B94 = 0x00282B94
    FN_27E658 = 0x0027E658
    FN_226B2C = 0x00226B2C

    sym_map = {
        "func_00293c98": FN_293C98,
        "func_00282b94": FN_282B94,
        "func_0027e658": FN_27E658,
        "func_00226b2c": FN_226B2C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, flags_50: int, sub_initial_flags: int, ret_27e: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        p2_addr = 0x10050000
        p2_mem = bytearray(0x80)
        struct.pack_into("<I", p2_mem, 0x50, flags_50)
        struct.pack_into("<h", p2_mem, 0x62, 0x123)
        uc.mem_write(p2_addr, bytes(p2_mem))

        sub_addr = 0x10052000
        uc.mem_write(sub_addr, struct.pack("<I", sub_initial_flags))

        ctx_addr = 0x10053000
        obj_addr = 0x10054000
        uc.mem_write(obj_addr, bytes(0x40))

        # Globals
        uc.mem_write(0x00435D48, struct.pack("<I", 0x10056000))
        uc.mem_write(0x00434290, struct.pack("<I", 0x10057000))

        calls = []
        def stub(name, ret=None):
            def handler(uc, address, size, user_data):
                calls.append(name)
                if ret is not None:
                    uc.reg_write(UC_ARM_REG_R0, ret)
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return handler

        uc.hook_add(UC_HOOK_CODE, stub("293c98", ctx_addr), None, FN_293C98, FN_293C98)
        uc.hook_add(UC_HOOK_CODE, stub("282b94", sub_addr), None, FN_282B94, FN_282B94)
        uc.hook_add(UC_HOOK_CODE, stub("27e658", ret_27e), None, FN_27E658, FN_27E658)
        uc.hook_add(UC_HOOK_CODE, stub("226b2c", obj_addr), None, FN_226B2C, FN_226B2C)

        uc.reg_write(UC_ARM_REG_R0, 0x45)
        uc.reg_write(UC_ARM_REG_R1, 0x67)
        uc.reg_write(UC_ARM_REG_R2, p2_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret_r0 = uc.reg_read(UC_ARM_REG_R0)
        sub_res = uc.mem_read(sub_addr, 4)
        obj_res = uc.mem_read(obj_addr, 0x30)
        return ret_r0, sub_res, obj_res, calls

    # Case 1: bit 0 not set
    r_orig, s_orig, o_orig, c_orig = run_one(orig_code, 0x80, 0, 0)
    r_dec, s_dec, o_dec, c_dec = run_one(decomp_code, 0x80, 0, 0)
    assert (r_orig, s_orig, o_orig, c_orig) == (r_dec, s_dec, o_dec, c_dec)

    # Case 2: bit 7 not set
    r_orig, s_orig, o_orig, c_orig = run_one(orig_code, 0x01, 0, 0)
    r_dec, s_dec, o_dec, c_dec = run_one(decomp_code, 0x01, 0, 0)
    assert (r_orig, s_orig, o_orig, c_orig) == (r_dec, s_dec, o_dec, c_dec)

    # Case 3: flags valid, ret_27e == 0 -> instantiates
    r_orig, s_orig, o_orig, c_orig = run_one(orig_code, 0x81, 0, 0)
    r_dec, s_dec, o_dec, c_dec = run_one(decomp_code, 0x81, 0, 0)
    assert (r_orig, s_orig, o_orig, c_orig) == (r_dec, s_dec, o_dec, c_dec)

    # Case 4: flags valid, ret_27e == 1, sub & 0x10 == 0 -> instantiates
    r_orig, s_orig, o_orig, c_orig = run_one(orig_code, 0x81, 0x00, 1)
    r_dec, s_dec, o_dec, c_dec = run_one(decomp_code, 0x81, 0x00, 1)
    assert (r_orig, s_orig, o_orig, c_orig) == (r_dec, s_dec, o_dec, c_dec)

    # Case 5: flags valid, ret_27e == 1, sub & 0x10 != 0 -> skips instantiate
    r_orig, s_orig, o_orig, c_orig = run_one(orig_code, 0x81, 0x10, 1)
    r_dec, s_dec, o_dec, c_dec = run_one(decomp_code, 0x81, 0x10, 1)
    assert (r_orig, s_orig, o_orig, c_orig) == (r_dec, s_dec, o_dec, c_dec)

    print("battle_func_002508c0 PASS")

if __name__ == "__main__":
    test_battle_func_00247170()
    test_ui_func_00248650()
    test_engine_func_0024f9e8()
    test_battle_func_00250800()
    test_battle_func_002508c0()
    print("\nALL 5 FUNCTIONS IN PART 07 PASSED PERFECTLY!")
