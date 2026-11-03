#!/usr/bin/env python3
"""Differential test for batch 31 C part 6:
- ui_func_00243234 (0x00243234, 180 B)
- ui_func_002432e8 (0x002432E8, 168 B)
- battle_func_0024558c (0x0024558C, 164 B)
- battle_func_002461ec (0x002461EC, 180 B)
- camp_func_00246ab0 (0x00246AB0, 168 B)
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

def test_ui_func_00243234():
    addr = 0x00243234
    print(f"--- Testing ui_func_00243234 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 180)
    tmp = ROOT / "build" / "test_31c_part06"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_00243234", tmp)

    FN_2F8270 = 0x002F8270
    FN_323660 = 0x00323660
    FN_318DF8 = 0x00318DF8
    FN_3243BC = 0x003243BC
    FN_2473AC = 0x002473AC
    FN_24736C = 0x0024736C
    FN_30ED58 = 0x0030ED58

    sym_map = {
        "func_002f8270": FN_2F8270,
        "func_00323660": FN_323660,
        "func_00318df8": FN_318DF8,
        "func_003243bc": FN_3243BC,
        "func_002473ac": FN_2473AC,
        "func_0024736c": FN_24736C,
        "func_0030ed58": FN_30ED58,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, has_p_f3c: bool, val8: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        glob_addr = 0x0044EA80
        out_addr = 0x10082000
        obj40_addr = 0x10083000
        p_f3c_addr = 0x10084000
        new_obj_addr = 0x10085000

        uc.mem_write(out_addr, bytes(0x200))
        uc.mem_write(obj40_addr, bytes(0x20))
        struct.pack_into("<I", uc.mem_read(obj40_addr, 12), 8, val8)
        uc.mem_write(obj40_addr + 8, struct.pack("<I", val8))
        uc.mem_write(new_obj_addr, bytes(0x20))

        glob_mem = bytearray(0x50)
        struct.pack_into("<I", glob_mem, 0x3C, p_f3c_addr if has_p_f3c else 0)
        struct.pack_into("<I", glob_mem, 0x40, obj40_addr)
        uc.mem_write(glob_addr, bytes(glob_mem))

        calls = []
        def stub(name, ret=None):
            def handler(uc, address, size, user_data):
                calls.append(name)
                if ret is not None:
                    uc.reg_write(UC_ARM_REG_R0, ret)
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return handler

        uc.hook_add(UC_HOOK_CODE, stub("2f8270"), None, FN_2F8270, FN_2F8270)
        uc.hook_add(UC_HOOK_CODE, stub("323660", 0x123), None, FN_323660, FN_323660)
        uc.hook_add(UC_HOOK_CODE, stub("318df8", 0x456), None, FN_318DF8, FN_318DF8)
        uc.hook_add(UC_HOOK_CODE, stub("3243bc"), None, FN_3243BC, FN_3243BC)
        uc.hook_add(UC_HOOK_CODE, stub("2473ac"), None, FN_2473AC, FN_2473AC)
        uc.hook_add(UC_HOOK_CODE, stub("24736c"), None, FN_24736C, FN_24736C)
        uc.hook_add(UC_HOOK_CODE, stub("30ed58", new_obj_addr), None, FN_30ED58, FN_30ED58)

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_R1, 0x99)
        uc.reg_write(UC_ARM_REG_R2, out_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_res = uc.mem_read(out_addr, 0x110)
        glob_res = uc.mem_read(glob_addr + 0x3C, 8)
        new_obj_res = uc.mem_read(new_obj_addr, 8)
        return calls, out_res, glob_res, new_obj_res

    cases = [
        (True, 1),
        (True, 2),
        (False, 0),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"243234 mismatch on {c}"

    print("ui_func_00243234: PASS")

def test_ui_func_002432e8():
    addr = 0x002432E8
    print(f"--- Testing ui_func_002432e8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 168)
    tmp = ROOT / "build" / "test_31c_part06"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002432e8", tmp)

    decomp_code = stage_body(comp, relocs, addr, {})

    def run_one(code, v_in, m_in):
        uc = create_emulator()
        uc.mem_write(addr, code)

        base = 0x004EA81C
        v_addr = base + 0x100
        m_addr = base + 0x140

        v_mem = bytearray(16)
        struct.pack_into("<ffff", v_mem, 0, *v_in)
        uc.mem_write(v_addr, bytes(v_mem))

        m_mem = bytearray(64)
        struct.pack_into("<16f", m_mem, 0, *m_in)
        uc.mem_write(m_addr, bytes(m_mem))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        v_out = struct.unpack("<ffff", uc.mem_read(v_addr, 16))
        return v_out

    v1 = (1.0, 2.0, 3.0, 1.0)
    # Scale x2, translate by (10, 20, 30)
    m1 = (
        2.0, 0.0, 0.0, 0.0,
        0.0, 2.0, 0.0, 0.0,
        0.0, 0.0, 2.0, 0.0,
        10.0, 20.0, 30.0, 1.0,
    )

    v2 = (-5.5, 3.2, 0.5, 1.0)
    # General matrix
    m2 = (
        1.1, 0.2, -0.3, 0.0,
        -0.4, 1.5, 0.6, 0.0,
        0.7, -0.8, 1.9, 0.0,
        15.0, -25.0, 35.0, 1.0,
    )

    for v, m in [(v1, m1), (v2, m2)]:
        r_o = run_one(orig_code, v, m)
        r_d = run_one(decomp_code, v, m)
        for i in range(4):
            assert abs(r_o[i] - r_d[i]) < 1e-4, f"2432e8 mismatch: orig {r_o} vs decomp {r_d}"

    print("ui_func_002432e8: PASS")

def test_battle_func_0024558c():
    addr = 0x0024558C
    print(f"--- Testing battle_func_0024558c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 164)
    tmp = ROOT / "build" / "test_31c_part06"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_0024558c", tmp)

    FN_226B2C = 0x00226B2C
    FN_293C98 = 0x00293C98
    FN_282B94 = 0x00282B94
    sym_map = {
        "func_00226b2c": FN_226B2C,
        "func_00293c98": FN_293C98,
        "func_00282b94": FN_282B94,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arg0, arg1, arg3, arg4, arg5, arg6, has_sub: bool):
        uc = create_emulator()
        uc.mem_write(addr, code)

        holder = 0x00434290
        mgr_addr = 0x10082000
        uc.mem_write(holder, struct.pack("<I", mgr_addr))

        obj1 = 0x10083000
        obj2 = 0x10084000
        sub_obj = 0x10085000 if has_sub else 0
        arg2_addr = 0x10086000

        uc.mem_write(obj1, bytes(0x80))
        uc.mem_write(obj2, bytes(0x80))
        arg2_mem = bytearray(0x80)
        struct.pack_into("<h", arg2_mem, 0x62, 0x77)
        uc.mem_write(arg2_addr, bytes(arg2_mem))

        calls = []
        def f_26b2c(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            a2 = uc.reg_read(UC_ARM_REG_R2)
            a3 = uc.reg_read(UC_ARM_REG_R3)
            calls.append(("26b2c", a0, a1, a2, a3))
            ret = obj1 if len(calls) == 1 else obj2
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_93c98(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 0x10087000)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_82b94(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("82b94", a0, a1))
            uc.reg_write(UC_ARM_REG_R0, sub_obj)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_26b2c, None, FN_226B2C, FN_226B2C)
        uc.hook_add(UC_HOOK_CODE, f_93c98, None, FN_293C98, FN_293C98)
        uc.hook_add(UC_HOOK_CODE, f_82b94, None, FN_282B94, FN_282B94)

        sp_base = STACK_BASE + 0x8000
        sp_mem = bytearray(16)
        struct.pack_into("<Iii", sp_mem, 0, arg4, arg5, arg6)
        uc.mem_write(sp_base, bytes(sp_mem))

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2_addr)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        uc.reg_write(UC_ARM_REG_SP, sp_base)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        m1 = uc.mem_read(obj1, 0x60)
        m2 = uc.mem_read(obj2, 0x60)
        return ret, calls, m1, m2

    cases = [
        (10, 2, 0x111, 0x222, 5, 8, True),
        (10, 2, 0x111, 0x222, -1, 8, True),
        (10, 2, 0x111, 0x222, 5, -1, True),
        (10, 2, 0x111, 0x222, 5, 8, False),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"24558c mismatch on {c}"

    print("battle_func_0024558c: PASS")

def test_battle_func_002461ec():
    addr = 0x002461EC
    print(f"--- Testing battle_func_002461ec ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 180)
    tmp = ROOT / "build" / "test_31c_part06"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002461ec", tmp)

    FN_226B2C = 0x00226B2C
    FN_255398 = 0x00255398
    FN_293C98 = 0x00293C98
    FN_2934D4 = 0x002934D4
    sym_map = {
        "func_00226b2c": FN_226B2C,
        "func_00255398": FN_255398,
        "func_00293c98": FN_293C98,
        "func_002934d4": FN_2934D4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, arg0, arg1, arg2, arg4, func_34d4_ret: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        holder = 0x00434290
        mgr_addr = 0x10082000
        uc.mem_write(holder, struct.pack("<I", mgr_addr))

        mgr_mem = bytearray(0x20)
        node1 = 0x10083000
        node2 = 0x10084000
        struct.pack_into("<I", mgr_mem, 8, node1)
        uc.mem_write(mgr_addr, bytes(mgr_mem))

        n1_mem = bytearray(0x20)
        struct.pack_into("<I", n1_mem, 0xC, node2)
        uc.mem_write(node1, bytes(n1_mem))
        uc.mem_write(node2, bytes(0x20))

        arg3_addr = 0x10085000
        arg3_mem = bytearray(0x80)
        struct.pack_into("<h", arg3_mem, 0x62, 0x55)
        uc.mem_write(arg3_addr, bytes(arg3_mem))

        obj = 0x10086000
        uc.mem_write(obj, bytes(0x80))

        calls = []
        def f_26b2c(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            a2 = uc.reg_read(UC_ARM_REG_R2)
            a3 = uc.reg_read(UC_ARM_REG_R3)
            calls.append(("26b2c", a0, a1, a2, a3))
            uc.reg_write(UC_ARM_REG_R0, obj)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_55398(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("55398", a0, a1))
            uc.reg_write(UC_ARM_REG_R0, 10)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_93c98(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 0x10087000)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_934d4(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, func_34d4_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_26b2c, None, FN_226B2C, FN_226B2C)
        uc.hook_add(UC_HOOK_CODE, f_55398, None, FN_255398, FN_255398)
        uc.hook_add(UC_HOOK_CODE, f_93c98, None, FN_293C98, FN_293C98)
        uc.hook_add(UC_HOOK_CODE, f_934d4, None, FN_2934D4, FN_2934D4)

        sp_base = STACK_BASE + 0x8000
        uc.mem_write(sp_base, struct.pack("<I", arg4))

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3_addr)
        uc.reg_write(UC_ARM_REG_SP, sp_base)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        obj_res = uc.mem_read(obj, 0x40)
        return ret, calls, obj_res

    cases = [
        (10, 20, 30, 4, 0),
        (10, 20, 30, 3, 1),
        (10, 20, 30, 3, 0),
        (10, 20, 30, 1, 0),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"2461ec mismatch on {c}"

    print("battle_func_002461ec: PASS")

def test_camp_func_00246ab0():
    addr = 0x00246AB0
    print(f"--- Testing camp_func_00246ab0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 168)
    tmp = ROOT / "build" / "test_31c_part06"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_00246ab0", tmp)

    FN_2C0EC4 = 0x002C0EC4
    FN_2C0E4C = 0x002C0E4C
    FN_2C0E9C = 0x002C0E9C
    sym_map = {
        "func_002c0ec4": FN_2C0EC4,
        "func_002c0e4c": FN_2C0E4C,
        "func_002c0e9c": FN_2C0E9C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, target_id: int, row_ids: list[int]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        sub_tbl_addr = 0x10082000
        payload_addr = 0x10083000

        # Create row entries (44 bytes each)
        p_mem = bytearray(44 * max(1, len(row_ids)))
        for i, rid in enumerate(row_ids):
            struct.pack_into("<h", p_mem, i * 44 + 0x20, rid)
        uc.mem_write(payload_addr, bytes(p_mem))

        calls = []
        def f_ec4(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("ec4", a0, a1))
            uc.reg_write(UC_ARM_REG_R0, sub_tbl_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_e4c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, len(row_ids))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def f_e9c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, payload_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, f_ec4, None, FN_2C0EC4, FN_2C0EC4)
        uc.hook_add(UC_HOOK_CODE, f_e4c, None, FN_2C0E4C, FN_2C0E4C)
        uc.hook_add(UC_HOOK_CODE, f_e9c, None, FN_2C0E9C, FN_2C0E9C)

        uc.reg_write(UC_ARM_REG_R0, target_id)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    cases = [
        # Target in row 0
        (10, [10, 20, -1]),
        # Target in row 1
        (20, [10, 20, -1]),
        # Target not found (-1 terminator)
        (30, [10, 20, -1]),
        # Empty table
        (10, []),
    ]

    for c in cases:
        r_o = run_one(orig_code, *c)
        r_d = run_one(decomp_code, *c)
        assert r_o == r_d, f"246ab0 mismatch on {c}: orig {hex(r_o)} vs decomp {hex(r_d)}"

    print("camp_func_00246ab0: PASS")

def main():
    test_ui_func_00243234()
    test_ui_func_002432e8()
    test_battle_func_0024558c()
    test_battle_func_002461ec()
    test_camp_func_00246ab0()
    print("\nALL 5 FUNCTIONS IN LEAF_BATCH31_C PART 06 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
