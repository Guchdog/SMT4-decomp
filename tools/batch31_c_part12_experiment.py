#!/usr/bin/env python3
"""Differential test for batch 31 C part 12:
- script_vm_func_002971e4 (0x002971E4, 160 B)
- engine_func_002994b4 (0x002994B4, 164 B)
- ui_func_002998d8 (0x002998D8, 156 B)
- battle_func_0029abc0 (0x0029ABC0, 176 B)
- camp_func_0029c49c (0x0029C49C, 156 B)
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
    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(0x10000000, 0x00100000)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_script_vm_func_002971e4():
    addr = 0x002971e4
    print(f"--- Testing script_vm_func_002971e4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002971e4", tmp)

    FN_2C4B30 = 0x002C4B30

    sym_map = {
        "engine_func_002c4b30": FN_2C4B30,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "script_vm_func_002971e4")

    def run_one(code, count: int, idx: int, test_str: str, val_18: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ctx_addr = 0x10050000
        obj_b0_addr = 0x10060000
        src_base_addr = 0x10070000

        # Setup obj_b0
        struct.pack_into("<I", bytearray(0x10), 8, count)
        uc.mem_write(obj_b0_addr, struct.pack("<IIII", 0, 0, count, 0))

        # Setup string array at src_base
        src_data = bytearray(0x1000)
        if idx >= 0 and idx < count:
            str_bytes = test_str.encode('ascii') + b'\x00'
            src_data[idx * 32 : idx * 32 + len(str_bytes)] = str_bytes
            struct.pack_into("<I", src_data, idx * 32 + 0x18, val_18)
        uc.mem_write(src_base_addr, bytes(src_data))

        # Setup ctx
        ctx_data = bytearray(0x200)
        struct.pack_into("<I", ctx_data, 0xb0, obj_b0_addr)
        struct.pack_into("<I", ctx_data, 0xb4, src_base_addr)
        # Pre-fill fields 0x1c..0x38 and 0x3c..0xac with non-zero
        for i in range(0x1c, 0xb0, 4):
            struct.pack_into("<I", ctx_data, i, 0xAAAAAAAA)
        uc.mem_write(ctx_addr, bytes(ctx_data))

        # Stub engine_func_002c4b30: memset(dst, 0, size)
        def stub_2c4(uc, address, size, user_data):
            dst = uc.reg_read(UC_ARM_REG_R0)
            sz = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(dst, b'\x00' * sz)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2c4, None, FN_2C4B30, FN_2C4B30)

        uc.reg_write(UC_ARM_REG_R0, ctx_addr)
        uc.reg_write(UC_ARM_REG_R1, idx)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_ctx = uc.mem_read(ctx_addr, 0xe0)
        return ret, out_ctx

    # Case 1: idx < 0 -> returns 0
    r_orig, m_orig = run_one(orig_code, 5, -1, "Hello", 0x1234)
    r_dec, m_dec = run_one(decomp_code, 5, -1, "Hello", 0x1234)
    assert r_orig == r_dec == 0, f"Mismatch case 1: {r_orig} vs {r_dec}"
    assert m_orig == m_dec, "Mismatch case 1 memory"

    # Case 2: idx >= count -> returns 0
    r_orig, m_orig = run_one(orig_code, 5, 5, "Hello", 0x1234)
    r_dec, m_dec = run_one(decomp_code, 5, 5, "Hello", 0x1234)
    assert r_orig == r_dec == 0, f"Mismatch case 2: {r_orig} vs {r_dec}"
    assert m_orig == m_dec, "Mismatch case 2 memory"

    # Case 3: valid idx = 2, count = 5
    r_orig, m_orig = run_one(orig_code, 5, 2, "TestString123", 0xCAFEBABE)
    r_dec, m_dec = run_one(decomp_code, 5, 2, "TestString123", 0xCAFEBABE)
    assert r_orig == r_dec == 1, f"Mismatch case 3: {r_orig} vs {r_dec}"
    assert m_orig == m_dec, "Mismatch case 3 memory"

    print("  script_vm_func_002971e4: PASS")

def test_engine_func_002994b4():
    addr = 0x002994b4
    print(f"--- Testing engine_func_002994b4 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 164)
    tmp = ROOT / "build" / "test_31c_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002994b4", tmp)

    FN_2116AC = 0x002116AC
    FN_310724 = 0x00310724
    FN_2C0BA8 = 0x002C0BA8
    FN_2931CC = 0x002931CC

    sym_map = {
        "camp_func_002116ac": FN_2116AC,
        "camp_func_00310724": FN_310724,
        "script_vm_func_002c0ba8": FN_2C0BA8,
        "battle_func_002931cc": FN_2931CC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002994b4")

    def run_one(code, total: int, filter_type: int, target_match: int, entries_info: list[tuple[int, int, int, int]]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        base_addr = 0x10050000
        for i, (code_id, entry_type, f1, f2) in enumerate(entries_info):
            e_data = bytearray(0x60)
            e_data[0] = code_id
            e_data[1] = entry_type
            struct.pack_into("<H", e_data, 0x56, f1)
            struct.pack_into("<H", e_data, 0x58, f2)
            uc.mem_write(base_addr + i * 0x60, bytes(e_data))

        def stub_211(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, total)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_310(uc, address, size, user_data):
            idx = uc.reg_read(UC_ARM_REG_R0)
            if idx < len(entries_info):
                uc.reg_write(UC_ARM_REG_R0, base_addr + idx * 0x60)
            else:
                uc.reg_write(UC_ARM_REG_R0, 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_2c0(uc, address, size, user_data):
            f = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, 1 if f != 0x99 else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_293(uc, address, size, user_data):
            f = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, 1 if f != 0x88 else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_211, None, FN_2116AC, FN_2116AC)
        uc.hook_add(UC_HOOK_CODE, stub_310, None, FN_310724, FN_310724)
        uc.hook_add(UC_HOOK_CODE, stub_2c0, None, FN_2C0BA8, FN_2C0BA8)
        uc.hook_add(UC_HOOK_CODE, stub_293, None, FN_2931CC, FN_2931CC)

        uc.reg_write(UC_ARM_REG_R0, filter_type)
        uc.reg_write(UC_ARM_REG_R1, target_match)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Setup entries: (id, type, f1, f2)
    entries = [
        (101, 1, 0, 0),       # match 0
        (102, 2, 0, 0),       # wrong type
        (103, 1, 0x99, 0),    # f1 failed
        (104, 1, 0, 0x88),    # f2 failed
        (105, 1, 0x10, 0x20), # match 1
        (106, 1, 0, 0),       # match 2
    ]

    # Case 1: total <= 0
    r_orig = run_one(orig_code, 0, 1, 0, entries)
    r_dec = run_one(decomp_code, 0, 1, 0, entries)
    assert r_orig == r_dec == 0, f"Mismatch case 1: {r_orig} vs {r_dec}"

    # Case 2: find match 0 -> id 101
    r_orig = run_one(orig_code, len(entries), 1, 0, entries)
    r_dec = run_one(decomp_code, len(entries), 1, 0, entries)
    assert r_orig == r_dec == 101, f"Mismatch case 2: {r_orig} vs {r_dec}"

    # Case 3: find match 1 -> id 105
    r_orig = run_one(orig_code, len(entries), 1, 1, entries)
    r_dec = run_one(decomp_code, len(entries), 1, 1, entries)
    assert r_orig == r_dec == 105, f"Mismatch case 3: {r_orig} vs {r_dec}"

    # Case 4: find match 2 -> id 106
    r_orig = run_one(orig_code, len(entries), 1, 2, entries)
    r_dec = run_one(decomp_code, len(entries), 1, 2, entries)
    assert r_orig == r_dec == 106, f"Mismatch case 4: {r_orig} vs {r_dec}"

    # Case 5: target_match out of bounds -> returns 0
    r_orig = run_one(orig_code, len(entries), 1, 3, entries)
    r_dec = run_one(decomp_code, len(entries), 1, 3, entries)
    assert r_orig == r_dec == 0, f"Mismatch case 5: {r_orig} vs {r_dec}"

    print("  engine_func_002994b4: PASS")

def test_ui_func_002998d8():
    addr = 0x002998d8
    print(f"--- Testing ui_func_002998d8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 156)
    tmp = ROOT / "build" / "test_31c_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002998d8", tmp)

    FN_294848 = 0x00294848

    sym_map = {
        "engine_func_00294848": FN_294848,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "ui_func_002998d8")

    def run_one(code, arg0: int, arg1: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ptr_addr = 0x0044E140
        obj_addr = 0x10050000

        uc.mem_write(ptr_addr + 4, struct.pack("<I", obj_addr))

        obj_data = bytearray(0x2000)
        struct.pack_into("<I", obj_data, 0x1e80, 0x5555)
        struct.pack_into("<I", obj_data, 0x10, 0x9999)
        struct.pack_into("<I", obj_data, 0x12dc, 0xAAAA)
        uc.mem_write(obj_addr, bytes(obj_data))

        calls = []

        def stub_294(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            calls.append((r0, r1, r2, r3))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_294, None, FN_294848, FN_294848)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_obj = uc.mem_read(obj_addr, 0x1300)
        return calls, out_obj

    # Case 1: arg0 = 0
    c_orig, m_orig = run_one(orig_code, 0, 42)
    c_dec, m_dec = run_one(decomp_code, 0, 42)
    assert c_orig == c_dec == [(0x5555, 0, 42, 7)], f"Mismatch case 1 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 1 memory"

    # Case 2: arg0 = 1
    c_orig, m_orig = run_one(orig_code, 1, 88)
    c_dec, m_dec = run_one(decomp_code, 1, 88)
    assert c_orig == c_dec == [(0x5555, 1, 88, 7)], f"Mismatch case 2 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 2 memory"

    # Case 3: arg0 = 2
    c_orig, m_orig = run_one(orig_code, 2, 99)
    c_dec, m_dec = run_one(decomp_code, 2, 99)
    assert c_orig == c_dec == [(0x5555, 2, 99, 7)], f"Mismatch case 3 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 3 memory"

    # Case 4: arg0 = 3 (out of range, no call to 294848)
    c_orig, m_orig = run_one(orig_code, 3, 100)
    c_dec, m_dec = run_one(decomp_code, 3, 100)
    assert c_orig == c_dec == [], f"Mismatch case 4 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 4 memory"

    print("  ui_func_002998d8: PASS")

def test_battle_func_0029abc0():
    addr = 0x0029abc0
    print(f"--- Testing battle_func_0029abc0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 176)
    tmp = ROOT / "build" / "test_31c_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("battle_func_0029abc0", tmp)

    FN_2AE3F0 = 0x002AE3F0
    FN_2931CC = 0x002931CC
    FN_2AE818 = 0x002AE818

    sym_map = {
        "battle_func_002ae3f0": FN_2AE3F0,
        "battle_func_002931cc": FN_2931CC,
        "camp_func_002ae818": FN_2AE818,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "battle_func_0029abc0")

    def run_one(code, has_info: bool, base_val: int, active_map: dict[int, int]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        info_addr = 0x10050000
        if has_info:
            i_data = bytearray(0x50)
            i_data[0x22] = base_val
            uc.mem_write(info_addr, bytes(i_data))

        camp_base = 0x10060000
        for id_val, cost in active_map.items():
            c_data = bytearray(0x50)
            struct.pack_into("<I", c_data, 0x38, cost)
            uc.mem_write(camp_base + id_val * 0x50, bytes(c_data))

        def stub_2ae(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, info_addr if has_info else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_293(uc, address, size, user_data):
            id_val = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, 1 if id_val in active_map else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_ae8(uc, address, size, user_data):
            id_val = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, camp_base + id_val * 0x50)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2ae, None, FN_2AE3F0, FN_2AE3F0)
        uc.hook_add(UC_HOOK_CODE, stub_293, None, FN_2931CC, FN_2931CC)
        uc.hook_add(UC_HOOK_CODE, stub_ae8, None, FN_2AE818, FN_2AE818)

        uc.reg_write(UC_ARM_REG_R0, 0x123)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Case 1: has_info == False -> returns 0
    r_orig = run_one(orig_code, False, 50, {})
    r_dec = run_one(decomp_code, False, 50, {})
    assert r_orig == r_dec == 0, f"Mismatch case 1: {r_orig} vs {r_dec}"

    # Case 2: base_val = 50, active sum = 10 + 20 = 30 -> diff = 20
    r_orig = run_one(orig_code, True, 50, {12: 10, 14: 20})
    r_dec = run_one(decomp_code, True, 50, {12: 10, 14: 20})
    assert r_orig == r_dec == 20, f"Mismatch case 2: {r_orig} vs {r_dec}"

    # Case 3: base_val = 30, active sum = 30 -> diff = 0 -> returns 1 (diff <= 0)
    r_orig = run_one(orig_code, True, 30, {12: 10, 13: 20})
    r_dec = run_one(decomp_code, True, 30, {12: 10, 13: 20})
    assert r_orig == r_dec == 1, f"Mismatch case 3: {r_orig} vs {r_dec}"

    # Case 4: base_val = 20, active sum = 50 -> diff = -30 -> returns 1 (diff <= 0)
    r_orig = run_one(orig_code, True, 20, {12: 25, 13: 25})
    r_dec = run_one(decomp_code, True, 20, {12: 25, 13: 25})
    assert r_orig == r_dec == 1, f"Mismatch case 4: {r_orig} vs {r_dec}"

    print("  battle_func_0029abc0: PASS")

def test_camp_func_0029c49c():
    addr = 0x0029c49c
    print(f"--- Testing camp_func_0029c49c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 156)
    tmp = ROOT / "build" / "test_31c_part12"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0029c49c", tmp)

    FN_2A8A08 = 0x002A8A08
    FN_3BCBE0 = 0x003BCBE0

    sym_map = {
        "camp_func_002a8a08": FN_2A8A08,
        "camp_func_003bcbe0": FN_3BCBE0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "camp_func_0029c49c")

    def run_one(code, slots_90f0: list[int], max_count: int, available_slot: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ctx_addr = 0x10050000
        ctx_data = bytearray(0xa000)
        for i, s in enumerate(slots_90f0):
            struct.pack_into("<b", ctx_data, 0x90f0 + i, s)
        ctx_data[0x910b] = max_count
        uc.mem_write(ctx_addr, bytes(ctx_data))

        def stub_2a8(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, ctx_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_3bc(uc, address, size, user_data):
            entry_ptr = uc.reg_read(UC_ARM_REG_R0)
            idx = (entry_ptr - (ctx_addr + 0x90)) // 0x604
            uc.reg_write(UC_ARM_REG_R0, 0 if idx == available_slot else 1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2a8, None, FN_2A8A08, FN_2A8A08)
        uc.hook_add(UC_HOOK_CODE, stub_3bc, None, FN_3BCBE0, FN_3BCBE0)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        r = uc.reg_read(UC_ARM_REG_R0)
        if r >= 0x80000000:
            r = r - 0x100000000
        return r

    # Case 1: count >= max_count -> returns -1
    # 5 non-negative slots, max_count = 5
    slots = [1, 2, 3, 4, 5, -1] + [-1]*18
    r_orig = run_one(orig_code, slots, 5, 2)
    r_dec = run_one(decomp_code, slots, 5, 2)
    assert r_orig == r_dec == -1, f"Mismatch case 1: {r_orig} vs {r_dec}"

    # Case 2: count < max_count (3 slots, max_count = 5), slot 4 available
    slots = [1, 2, 3, -1] + [-1]*20
    r_orig = run_one(orig_code, slots, 5, 4)
    r_dec = run_one(decomp_code, slots, 5, 4)
    assert r_orig == r_dec == 4, f"Mismatch case 2: {r_orig} vs {r_dec}"

    # Case 3: count < max_count, but none of 24 entries is available (available_slot = -1)
    r_orig = run_one(orig_code, slots, 5, -1)
    r_dec = run_one(decomp_code, slots, 5, -1)
    assert r_orig == r_dec == -1, f"Mismatch case 3: {r_orig} vs {r_dec}"

    print("  camp_func_0029c49c: PASS")

def main():
    print("=== Running Batch 31 Part 12 Tests ===")
    test_script_vm_func_002971e4()
    test_engine_func_002994b4()
    test_ui_func_002998d8()
    test_battle_func_0029abc0()
    test_camp_func_0029c49c()
    print("=== All 5 Part 12 Functions PASSED ===")

if __name__ == "__main__":
    main()
