#!/usr/bin/env python3
"""Differential test for batch 31 C part 13:
- camp_func_0029e19c (0x0029E19C, 172 B)
- ui_func_0029ec6c (0x0029EC6C, 156 B)
- camp_func_0029ed44 (0x0029ED44, 184 B)
- camp_func_002a0de8 (0x002A0DE8, 192 B)
- engine_func_002a32bc (0x002A32BC, 192 B)
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
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
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
    uc.mem_map(0x00480000, 0x00100000) # Covers 0x00480000..0x00580000
    uc.mem_map(0x10000000, 0x00100000)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, unmapped_hook)

    val = uc.reg_read(UC_ARM_REG_C1_C0_2)
    val |= (0xF << 20)
    uc.reg_write(UC_ARM_REG_C1_C0_2, val)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    return uc

def test_camp_func_0029e19c():
    addr = 0x0029e19c
    print(f"--- Testing camp_func_0029e19c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 172)
    tmp = ROOT / "build" / "test_31c_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0029e19c", tmp)

    FN_2B66EC = 0x002B66EC
    FN_24DB60 = 0x0024DB60
    FN_26AAC0 = 0x0026AAC0
    FN_24D9E4 = 0x0024D9E4
    FN_29DF14 = 0x0029DF14

    sym_map = {
        "func_002b66ec": FN_2B66EC,
        "engine_func_0024db60": FN_24DB60,
        "camp_func_0026aac0": FN_26AAC0,
        "script_vm_func_0024d9e4": FN_24D9E4,
        "camp_func_0029df14": FN_29DF14,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "camp_func_0029e19c")

    def run_one(code, arg0: int, arg1: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ptr_addr = 0x0044E140
        r4_addr = 0x10050000
        uc.mem_write(ptr_addr + 4, struct.pack("<I", r4_addr))

        r4_data = bytearray(0x2000)
        uc.mem_write(r4_addr, bytes(r4_data))

        calls = []

        def stub_b66(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 0x10060000)
            calls.append(("2b6",))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_db6(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("24db60", r0, r1))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_aac(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("26aac0", r0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_d9e(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("24d9e4", r0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_df1(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            calls.append(("29df14", r0))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_b66, None, FN_2B66EC, FN_2B66EC)
        uc.hook_add(UC_HOOK_CODE, stub_db6, None, FN_24DB60, FN_24DB60)
        uc.hook_add(UC_HOOK_CODE, stub_aac, None, FN_26AAC0, FN_26AAC0)
        uc.hook_add(UC_HOOK_CODE, stub_d9e, None, FN_24D9E4, FN_24D9E4)
        uc.hook_add(UC_HOOK_CODE, stub_df1, None, FN_29DF14, FN_29DF14)

        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_r4 = uc.mem_read(r4_addr + 0x1E60, 0x60)
        return calls, out_r4

    # Case 1: arg0 < 0
    c_orig, m_orig = run_one(orig_code, -1, 0)
    c_dec, m_dec = run_one(decomp_code, -1, 0)
    assert c_orig == c_dec, f"Mismatch case 1 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 1 memory"

    # Case 2: arg0 >= 0, arg1 != 0
    c_orig, m_orig = run_one(orig_code, 15, 1)
    c_dec, m_dec = run_one(decomp_code, 15, 1)
    assert c_orig == c_dec, f"Mismatch case 2 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 2 memory"

    # Case 3: arg0 >= 0, arg1 == 0
    c_orig, m_orig = run_one(orig_code, 25, 0)
    c_dec, m_dec = run_one(decomp_code, 25, 0)
    assert c_orig == c_dec, f"Mismatch case 3 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 3 memory"

    print("  camp_func_0029e19c: PASS")

def test_ui_func_0029ec6c():
    addr = 0x0029ec6c
    print(f"--- Testing ui_func_0029ec6c ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 156)
    tmp = ROOT / "build" / "test_31c_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_0029ec6c", tmp)

    FN_2B087C = 0x002B087C

    sym_map = {
        "battle_func_002b087c": FN_2B087C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "ui_func_0029ec6c")

    def run_one(code, entity_id: int, info_flags: int, entry_b: int, sub_ids: list[int], sub_flags: dict[int, int]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        info_addr = 0x10050000
        info_data = bytearray(0x100)
        struct.pack_into("<H", info_data, 0x16, info_flags)
        for i, s_id in enumerate(sub_ids):
            struct.pack_into("<H", info_data, 0x7c + i * 2, s_id)
        uc.mem_write(info_addr, bytes(info_data))

        ptr_addr = 0x0043E2A8
        r2_addr = 0x10060000
        uc.mem_write(ptr_addr + 4, struct.pack("<I", r2_addr))

        # Setup table at r2 + 0xC1F8
        table_size = 0x500 * 52 + 0xD000
        table_data = bytearray(table_size)
        if entity_id <= 0x500:
            table_data[0xc1f8 + entity_id * 52 + 0x16] = entry_b
        for s_id, s_b in sub_flags.items():
            if s_id <= 0x500:
                table_data[0xc1f8 + s_id * 52 + 0x16] = s_b
        uc.mem_write(r2_addr, bytes(table_data))

        def stub_b08(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, info_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_b08, None, FN_2B087C, FN_2B087C)

        uc.reg_write(UC_ARM_REG_R0, entity_id)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Case 1: entity_id > 0x500 -> 0
    r_orig = run_one(orig_code, 0x501, 1, 2, [], {})
    r_dec = run_one(decomp_code, 0x501, 1, 2, [], {})
    assert r_orig == r_dec == 0, f"Mismatch case 1: {r_orig} vs {r_dec}"

    # Case 2: info flags & 1 == 0 -> 0
    r_orig = run_one(orig_code, 10, 0, 2, [], {})
    r_dec = run_one(decomp_code, 10, 0, 2, [], {})
    assert r_orig == r_dec == 0, f"Mismatch case 2: {r_orig} vs {r_dec}"

    # Case 3: entity itself has bit 1 set -> returns 1
    r_orig = run_one(orig_code, 10, 1, 2, [], {})
    r_dec = run_one(decomp_code, 10, 1, 2, [], {})
    assert r_orig == r_dec == 1, f"Mismatch case 3: {r_orig} vs {r_dec}"

    # Case 4: entity doesn't have bit 1, but sub_id 20 has bit 1 -> returns 1
    r_orig = run_one(orig_code, 10, 1, 0, [0, 20, 0], {20: 2})
    r_dec = run_one(decomp_code, 10, 1, 0, [0, 20, 0], {20: 2})
    assert r_orig == r_dec == 1, f"Mismatch case 4: {r_orig} vs {r_dec}"

    # Case 5: neither entity nor sub_ids have bit 1 -> returns 0
    r_orig = run_one(orig_code, 10, 1, 0, [15, 20, 0], {15: 0, 20: 0})
    r_dec = run_one(decomp_code, 10, 1, 0, [15, 20, 0], {15: 0, 20: 0})
    assert r_orig == r_dec == 0, f"Mismatch case 5: {r_orig} vs {r_dec}"

    print("  ui_func_0029ec6c: PASS")

def test_camp_func_0029ed44():
    addr = 0x0029ed44
    print(f"--- Testing camp_func_0029ed44 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 184)
    tmp = ROOT / "build" / "test_31c_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0029ed44", tmp)

    FN_2B9364 = 0x002B9364
    FN_2C0BA8 = 0x002C0BA8
    FN_2883BC = 0x002883BC

    sym_map = {
        "func_002b9364": FN_2B9364,
        "script_vm_func_002c0ba8": FN_2C0BA8,
        "camp_func_002883bc": FN_2883BC,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "camp_func_0029ed44")

    def run_one(code, has_item: bool, flags_2c: int, req1: int, f34: int, f6: int, ret_83bc: int, stack_val: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        item_addr = 0x10050000
        if has_item:
            i_data = bytearray(0x50)
            struct.pack_into("<H", i_data, 0, 0x1122)
            struct.pack_into("<H", i_data, 6, f6)
            struct.pack_into("<I", i_data, 0x2c, flags_2c)
            struct.pack_into("<H", i_data, 0x34, f34)
            struct.pack_into("<H", i_data, 0x36, req1)
            uc.mem_write(item_addr, bytes(i_data))

        def stub_b93(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, item_addr if has_item else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_2c0(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, 1 if r0 != 0x99 else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_83b(uc, address, size, user_data):
            sp_dst = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(sp_dst + 0x2e, struct.pack("<H", stack_val))
            uc.reg_write(UC_ARM_REG_R0, ret_83bc)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_b93, None, FN_2B9364, FN_2B9364)
        uc.hook_add(UC_HOOK_CODE, stub_2c0, None, FN_2C0BA8, FN_2C0BA8)
        uc.hook_add(UC_HOOK_CODE, stub_83b, None, FN_2883BC, FN_2883BC)

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_R1, 0x123)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Case 1: has_item == False -> 0
    r_orig = run_one(orig_code, False, 0, 0, 0, 1, 1, 0xff)
    r_dec = run_one(decomp_code, False, 0, 0, 0, 1, 1, 0xff)
    assert r_orig == r_dec == 0, f"Mismatch case 1: {r_orig} vs {r_dec}"

    # Case 2: flags_2c has 0x200000 -> 0
    r_orig = run_one(orig_code, True, 0x200000, 0, 0, 1, 1, 0xff)
    r_dec = run_one(decomp_code, True, 0x200000, 0, 0, 1, 1, 0xff)
    assert r_orig == r_dec == 0, f"Mismatch case 2: {r_orig} vs {r_dec}"

    # Case 3: req1 = 0x99 (fails 2c0ba8) -> 0
    r_orig = run_one(orig_code, True, 0, 0x99, 0, 1, 1, 0xff)
    r_dec = run_one(decomp_code, True, 0, 0x99, 0, 1, 1, 0xff)
    assert r_orig == r_dec == 0, f"Mismatch case 3: {r_orig} vs {r_dec}"

    # Case 4: f34 = 0 (bit 0 not set), f6 = 1 -> returns 1
    r_orig = run_one(orig_code, True, 0, 0, 0, 1, 1, 0xff)
    r_dec = run_one(decomp_code, True, 0, 0, 0, 1, 1, 0xff)
    assert r_orig == r_dec == 1, f"Mismatch case 4: {r_orig} vs {r_dec}"

    # Case 5: f34 = 1 (bit 0 set, ~1 == 0), ret_83bc = 1, stack_val = 0xfc, f6 = 1 -> returns 1
    r_orig = run_one(orig_code, True, 0, 0, 1, 1, 1, 0xfc)
    r_dec = run_one(decomp_code, True, 0, 0, 1, 1, 1, 0xfc)
    assert r_orig == r_dec == 1, f"Mismatch case 5: {r_orig} vs {r_dec}"

    # Case 6: f34 = 3 (bit 0 set, > 1), stack_val & 0xfc == 0 -> returns 0
    r_orig = run_one(orig_code, True, 0, 0, 3, 1, 1, 0x03)
    r_dec = run_one(decomp_code, True, 0, 0, 3, 1, 1, 0x03)
    assert r_orig == r_dec == 0, f"Mismatch case 6: {r_orig} vs {r_dec}"

    print("  camp_func_0029ed44: PASS")

def test_camp_func_002a0de8():
    addr = 0x002a0de8
    print(f"--- Testing camp_func_002a0de8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_002a0de8", tmp)

    FN_2C20A8 = 0x002C20A8
    FN_1DB28C = 0x001DB28C

    sym_map = {
        "engine_func_002c20a8": FN_2C20A8,
        "ui_func_001db28c": FN_1DB28C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "camp_func_002a0de8")

    def run_one(code, has_r4: bool, pos: list[float], dir_vec: list[float], factor: float, r5_vec: list[float]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ptr_addr = 0x0044E178
        r4_addr = 0x10050000

        uc.mem_write(ptr_addr, struct.pack("<I", r4_addr if has_r4 else 0))

        if has_r4:
            r4_data = bytearray(0x1000)
            struct.pack_into("<fff", r4_data, 0x508, *pos)
            struct.pack_into("<fff", r4_data, 0x514, *dir_vec)
            struct.pack_into("<f", r4_data, 0x52c, factor)
            struct.pack_into("<fff", r4_data, 0x530, *r5_vec)
            uc.mem_write(r4_addr, bytes(r4_data))

        calls = []

        def stub_2c2(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            # Read vectors from memory
            p = struct.unpack("<fff", uc.mem_read(r1, 12))
            t = struct.unpack("<fff", uc.mem_read(r2, 12))
            u = struct.unpack("<fff", uc.mem_read(r3, 12))
            calls.append(("2c2", r0, p, t, u))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_1db(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            s0_raw = uc.reg_read(UC_ARM_REG_S0)
            s1_raw = uc.reg_read(UC_ARM_REG_S1)
            s2_raw = uc.reg_read(UC_ARM_REG_S2)
            s0 = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
            s1 = struct.unpack("<f", struct.pack("<I", s1_raw))[0]
            s2 = struct.unpack("<f", struct.pack("<I", s2_raw))[0]
            calls.append(("1db", r0, r1, (s0, s1, s2)))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2c2, None, FN_2C20A8, FN_2C20A8)
        uc.hook_add(UC_HOOK_CODE, stub_1db, None, FN_1DB28C, FN_1DB28C)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return calls

    # Case 1: has_r4 == False
    c_orig = run_one(orig_code, False, [0,0,0], [0,0,0], 0, [0,0,0])
    c_dec = run_one(decomp_code, False, [0,0,0], [0,0,0], 0, [0,0,0])
    assert c_orig == c_dec == [], f"Mismatch case 1: {c_orig} vs {c_dec}"

    # Case 2: normal vectors
    pos = [10.0, 20.0, 30.0]
    dir_vec = [1.0, 0.0, 2.0]
    factor = 5.0
    r5_vec = [100.0, 200.0, 300.0]
    c_orig = run_one(orig_code, True, pos, dir_vec, factor, r5_vec)
    c_dec = run_one(decomp_code, True, pos, dir_vec, factor, r5_vec)
    assert c_orig == c_dec, f"Mismatch case 2: {c_orig} vs {c_dec}"

    print("  camp_func_002a0de8: PASS")

def test_engine_func_002a32bc():
    addr = 0x002a32bc
    print(f"--- Testing engine_func_002a32bc ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part13"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002a32bc", tmp)

    decomp_code = stage_body(comp, relocs, addr, {}, "engine_func_002a32bc")

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)

        obj_addr = 0x10050000
        # Fill buffer with 0xAA pattern
        uc.mem_write(obj_addr, b'\xAA' * 0x100)

        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_obj = uc.mem_read(obj_addr, 0xC0)
        return out_obj

    m_orig = run_one(orig_code)
    m_dec = run_one(decomp_code)
    assert m_orig == m_dec, f"Mismatch memory:\norig: {m_orig.hex()}\ndec:  {m_dec.hex()}"

    print("  engine_func_002a32bc: PASS")

def main():
    print("=== Running Batch 31 Part 13 Tests ===")
    test_camp_func_0029e19c()
    test_ui_func_0029ec6c()
    test_camp_func_0029ed44()
    test_camp_func_002a0de8()
    test_engine_func_002a32bc()
    print("=== All 5 Part 13 Functions PASSED ===")

if __name__ == "__main__":
    main()
