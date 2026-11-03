#!/usr/bin/env python3
"""Differential test for batch 31 C part 16:
- func_002b5f90 (0x002B5F90, 160 B)
- engine_func_002bb0b4 (0x002BB0B4, 188 B)
- battle_func_002bf8d4 (0x002BF8D4, 176 B)
- ui_func_002c1abc (0x002C1ABC, 168 B)
- ui_func_002c1d3c (0x002C1D3C, 168 B)
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
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(0x10000000, 0x00100000)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_func_002b5f90():
    addr = 0x002B5F90
    size = 160
    print(f"--- Testing func_002b5f90 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("func_002b5f90", tmp)

    # In decompiled code, __int128 multiplication may call __aeabi_ldiv0 or inlined
    # Let's see what relocations exist:
    sym_map = {}
    for r in relocs:
        if r.symbol_name != "":
            raise RuntimeError(f"Unexpected reloc in 002b5f90: {r.symbol_name}")

    decomp_code = stage_body(comp, relocs, addr, sym_map, "func_002b5f90")

    A_ADDR = 0x10020000

    cases = [
        # (a, mul, shift)
        (0, 0x20c49ba5e353f7cf, 7),
        (1, 0x20c49ba5e353f7cf, 7),
        (100, 0x20c49ba5e353f7cf, 7),
        (1000000000, 0x20c49ba5e353f7cf, 7),
        (-100, 0x20c49ba5e353f7cf, 7),
        (-1000000000, 0x20c49ba5e353f7cf, 7),
        (123456789012345, 0x20c49ba5e353f7cf, 7),
        (-98765432101234, 0x20c49ba5e353f7cf, 7),
    ]

    def run_one(code, a, mul, shift):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.mem_write(A_ADDR, struct.pack("<q", a))

        sp = STACK_BASE
        uc.mem_write(sp, struct.pack("<I", shift))

        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, A_ADDR)
        uc.reg_write(UC_ARM_REG_R2, mul & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_R3, (mul >> 32) & 0xFFFFFFFF)

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        return struct.unpack("<q", struct.pack("<II", r0, r1))[0]

    for c in cases:
        r_orig = run_one(orig_code, *c)
        r_decomp = run_one(decomp_code, *c)
        assert r_orig == r_decomp, f"Mismatch in 002b5f90 for {c}: {r_orig} != {r_decomp}"

    print("PASS: func_002b5f90")

def test_engine_func_002bb0b4():
    addr = 0x002BB0B4
    size = 188
    print(f"--- Testing engine_func_002bb0b4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002bb0b4", tmp)

    FN_14DAC8 = 0x0014DAC8
    FN_2B5148 = 0x002B5148
    FN_15250C = 0x0015250C

    sym_map = {
        "func_0014dac8": FN_14DAC8,
        "func_002b5148": FN_2B5148,
        "func_0015250c": FN_15250C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002bb0b4")

    OBJ_ADDR = 0x10020000
    PKT_ADDR = 0x10030000

    def hook_stubs(uc: Uc, alloc_ret: int, f152_ret: int, call_log: list):
        def s_14dac8(uc, address, size, user_data):
            call_log.append("14dac8")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_2b5148(uc, address, size, user_data):
            call_log.append("2b5148")
            uc.mem_write(alloc_ret, b"\x00" * 0x20)
            uc.reg_write(UC_ARM_REG_R0, alloc_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_15250c(uc, address, size, user_data):
            call_log.append("15250c")
            uc.reg_write(UC_ARM_REG_R0, f152_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, s_14dac8, None, FN_14DAC8, FN_14DAC8)
        uc.hook_add(UC_HOOK_CODE, s_2b5148, None, FN_2B5148, FN_2B5148)
        uc.hook_add(UC_HOOK_CODE, s_15250c, None, FN_15250C, FN_15250C)

    cases = [
        # (has_head, mode, f152_ret)
        (False, 0, 0),  # head=null, mode=0 -> returns 0
        (False, 1, 0),  # head=null, mode=1 -> allocates and executes mode!=0
        (True,  0, 1),  # head!=null, mode=0 -> calls 15250c (returns 1) -> success
        (True,  0, 0),  # head!=null, mode=0 -> calls 15250c (returns 0) -> returns 0
        (True,  1, 0),  # head!=null, mode=1 -> calls 14dac8 -> success
    ]

    def run_one(code, has_head, mode, f152_ret):
        uc = create_emulator()
        uc.mem_write(addr, code)
        call_log = []
        hook_stubs(uc, PKT_ADDR, f152_ret, call_log)

        uc.mem_write(OBJ_ADDR, b"\x00" * 0x200)
        uc.mem_write(OBJ_ADDR + 0x174, struct.pack("<I", 100)) # seq = 100
        uc.mem_write(OBJ_ADDR + 0x184, struct.pack("<I", 0x1234))

        if has_head:
            uc.mem_write(PKT_ADDR, b"\x00" * 0x20)
            uc.mem_write(OBJ_ADDR + 0x16C, struct.pack("<I", PKT_ADDR))
            uc.mem_write(OBJ_ADDR + 0x170, struct.pack("<I", PKT_ADDR))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
        uc.reg_write(UC_ARM_REG_R1, mode)

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        obj_state = uc.mem_read(OBJ_ADDR + 0x16C, 0x10)
        pkt_state = uc.mem_read(PKT_ADDR, 0x10)
        return r0, obj_state, pkt_state, call_log

    for c in cases:
        r_orig, obj_orig, pkt_orig, log_orig = run_one(orig_code, *c)
        r_decomp, obj_decomp, pkt_decomp, log_decomp = run_one(decomp_code, *c)
        assert r_orig == r_decomp, f"Return mismatch in 002bb0b4 for {c}: {r_orig} != {r_decomp}"
        assert obj_orig == obj_decomp, f"Obj state mismatch in 002bb0b4 for {c}"
        assert pkt_orig == pkt_decomp, f"Pkt state mismatch in 002bb0b4 for {c}"
        assert log_orig == log_decomp, f"Call log mismatch in 002bb0b4 for {c}"

    print("PASS: engine_func_002bb0b4")

def test_battle_func_002bf8d4():
    addr = 0x002BF8D4
    size = 176
    print(f"--- Testing battle_func_002bf8d4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_002bf8d4", tmp)

    FN_2BF41C = 0x002BF41C
    FN_2B74B4 = 0x002B74B4
    FN_2AED6C = 0x002AED6C

    sym_map = {
        "func_002bf41c": FN_2BF41C,
        "func_002b74b4": FN_2B74B4,
        "func_002aed6c": FN_2AED6C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "battle_func_002bf8d4")

    PARTY_PTR = 0x0043DFC0
    PARTY_ADDR = 0x10020000

    def hook_stubs(uc: Uc, active_members: dict, member_ids: dict, dispatched: list):
        def s_2bf41c(uc, address, size, user_data):
            m = uc.reg_read(UC_ARM_REG_R0)
            is_act = 1 if active_members.get(m, False) else 0
            uc.reg_write(UC_ARM_REG_R0, is_act)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_2b74b4(uc, address, size, user_data):
            m = uc.reg_read(UC_ARM_REG_R0)
            mid = member_ids.get(m, -1)
            uc.reg_write(UC_ARM_REG_R0, mid)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_2aed6c(uc, address, size, user_data):
            m = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            # 5th arg is on stack at sp
            arg4 = struct.unpack("<f", uc.mem_read(sp, 4))[0]
            dispatched.append((m, r1, r2, r3, arg4))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, s_2bf41c, None, FN_2BF41C, FN_2BF41C)
        uc.hook_add(UC_HOOK_CODE, s_2b74b4, None, FN_2B74B4, FN_2B74B4)
        uc.hook_add(UC_HOOK_CODE, s_2aed6c, None, FN_2AED6C, FN_2AED6C)

    cases = [
        # target_id
        10, # matches slot 1
        20, # matches slot 2
        30, # matches slot 3
        99, # not found
    ]

    def run_one(code, target_id):
        uc = create_emulator()
        uc.mem_write(addr, code)

        dispatched = []
        M1 = 0x10030000
        M2 = 0x10031000
        M3 = 0x10032000
        active_map = {M1: True, M2: True, M3: True}
        id_map = {M1: 10, M2: 20, M3: 30}
        hook_stubs(uc, active_map, id_map, dispatched)

        uc.mem_write(PARTY_PTR, struct.pack("<I", PARTY_ADDR))
        uc.mem_write(PARTY_ADDR, b"\x00" * 0x800)
        uc.mem_write(PARTY_ADDR + 0x630 + 1 * 4, struct.pack("<I", M1))
        uc.mem_write(PARTY_ADDR + 0x630 + 2 * 4, struct.pack("<I", M2))
        uc.mem_write(PARTY_ADDR + 0x630 + 3 * 4, struct.pack("<I", M3))

        sp = STACK_BASE
        uc.mem_write(sp, struct.pack("<f", 4.5)) # arg4 on stack

        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, target_id)
        uc.reg_write(UC_ARM_REG_R1, 100)
        uc.reg_write(UC_ARM_REG_R2, 200)
        uc.reg_write(UC_ARM_REG_R3, 300)

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        return r0, dispatched

    for tid in cases:
        r_orig, disp_orig = run_one(orig_code, tid)
        r_decomp, disp_decomp = run_one(decomp_code, tid)
        assert r_orig == r_decomp, f"Return mismatch in 002bf8d4 for tid {tid}: {r_orig} != {r_decomp}"
        assert disp_orig == disp_decomp, f"Dispatch mismatch in 002bf8d4 for tid {tid}"

    print("PASS: battle_func_002bf8d4")

def test_ui_func_002c1abc():
    addr = 0x002C1ABC
    size = 168
    print(f"--- Testing ui_func_002c1abc ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002c1abc", tmp)

    FN_2B668C = 0x002B668C
    sym_map = {
        "func_002b668c": FN_2B668C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "ui_func_002c1abc")

    OBJ_ADDR = 0x10020000

    def hook_stubs(uc: Uc, calls: list):
        def s_2b668c(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append((r0, r1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, s_2b668c, None, FN_2B668C, FN_2B668C)

    cases = [
        # (dirty, s0, s1, s2, s3)
        (0, 1.0, 1.0, 1.0, 1.0), # dirty=0 and all 1.0 -> no sync
        (1, 1.0, 1.0, 1.0, 1.0), # dirty=1 -> sync
        (0, 2.0, 1.0, 1.0, 1.0), # dirty=0, s0!=1 -> sync
        (0, 1.0, 0.5, 1.0, 1.0), # dirty=0, s1!=1 -> sync
        (0, 1.0, 1.0, 3.0, 1.0), # dirty=0, s2!=1 -> sync
        (0, 1.0, 1.0, 1.0, 4.0), # dirty=0, s3!=1 -> sync
    ]

    def run_one(code, dirty, s0, s1, s2, s3):
        uc = create_emulator()
        uc.mem_write(addr, code)
        calls = []
        hook_stubs(uc, calls)

        uc.mem_write(OBJ_ADDR, b"\x00" * 0x1500)
        uc.mem_write(OBJ_ADDR + 0x52C, struct.pack("<I", 0x10030000))
        uc.mem_write(OBJ_ADDR + 0x11CC, struct.pack("<4f", s0, s1, s2, s3))
        uc.mem_write(OBJ_ADDR + 0x11DC, bytes([dirty]))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        mem = uc.mem_read(OBJ_ADDR + 0x11CC, 0x14)
        return mem, calls

    for c in cases:
        mem_orig, calls_orig = run_one(orig_code, *c)
        mem_decomp, calls_decomp = run_one(decomp_code, *c)
        assert mem_orig == mem_decomp, f"Memory mismatch in 002c1abc for case {c}"
        assert calls_orig == calls_decomp, f"Calls mismatch in 002c1abc for case {c}"

    print("PASS: ui_func_002c1abc")

def test_ui_func_002c1d3c():
    addr = 0x002C1D3C
    size = 168
    print(f"--- Testing ui_func_002c1d3c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part16"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002c1d3c", tmp)

    FN_138734 = 0x00138734
    FN_1456D0 = 0x001456D0

    sym_map = {
        "func_00138734": FN_138734,
        "func_001456d0": FN_1456D0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "ui_func_002c1d3c")

    OBJ_ADDR = 0x10020000
    TARGET_ADDR = 0x10030000

    def hook_stubs(uc: Uc, c_138: list, c_145: list):
        def s_138734(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            stk = struct.unpack("<III", uc.mem_read(sp, 12))
            c_138.append((r0, r1, r2, r3, *stk))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def s_1456d0(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            c_145.append(r0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, s_138734, None, FN_138734, FN_138734)
        uc.hook_add(UC_HOOK_CODE, s_1456d0, None, FN_1456D0, FN_1456D0)

    cases = [
        # (dirty, curr_target, new_target, init_state)
        (0, TARGET_ADDR, TARGET_ADDR, 1), # same target, not dirty, state=1 -> no-op
        (1, TARGET_ADDR, TARGET_ADDR, 1), # dirty -> binds target, calls 138734
        (0, 0, TARGET_ADDR, 0),           # null -> target, calls 138734, calls 1456d0(1)
        (0, TARGET_ADDR, 0, 1),           # target -> null, calls 1456d0(0)
    ]

    def run_one(code, dirty, curr_t, new_t, init_st):
        uc = create_emulator()
        uc.mem_write(addr, code)
        c_138 = []
        c_145 = []
        hook_stubs(uc, c_138, c_145)

        uc.mem_write(OBJ_ADDR, b"\x00" * 0x1500)
        uc.mem_write(OBJ_ADDR + 0x11E4, struct.pack("<I", curr_t))
        uc.mem_write(OBJ_ADDR + 0x11E8, bytes([dirty, init_st]))

        uc.mem_write(TARGET_ADDR, b"\x00" * 0x100)
        uc.mem_write(TARGET_ADDR + 0x14, struct.pack("<II", 11, 22))
        uc.mem_write(TARGET_ADDR + 0x30, struct.pack("<II", 33, 44))
        uc.mem_write(TARGET_ADDR + 0x38, struct.pack("<III", 55, 66, 77))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)
        uc.reg_write(UC_ARM_REG_R1, new_t)

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        state_mem = uc.mem_read(OBJ_ADDR + 0x11E4, 8)
        return state_mem, c_138, c_145

    for c in cases:
        st_orig, c138_orig, c145_orig = run_one(orig_code, *c)
        st_decomp, c138_decomp, c145_decomp = run_one(decomp_code, *c)
        assert st_orig == st_decomp, f"State mismatch in 002c1d3c for case {c}"
        assert c138_orig == c138_decomp, f"138734 mismatch in 002c1d3c for case {c}"
        assert c145_orig == c145_decomp, f"1456d0 mismatch in 002c1d3c for case {c}"

    print("PASS: ui_func_002c1d3c")

if __name__ == "__main__":
    test_func_002b5f90()
    test_engine_func_002bb0b4()
    test_battle_func_002bf8d4()
    test_ui_func_002c1abc()
    test_ui_func_002c1d3c()
    print("\n>>> ALL PART 16 TESTS PASSED! <<<")
