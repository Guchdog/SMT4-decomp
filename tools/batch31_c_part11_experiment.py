#!/usr/bin/env python3
"""Differential test for batch 31 C part 11:
- camp_func_0028d4f0 (0x0028D4F0, 156 B)
- script_vm_func_00290374 (0x00290374, 156 B)
- script_vm_func_002911ec (0x002911EC, 192 B)
- script_vm_func_002956c0 (0x002956C0, 160 B)
- script_vm_func_00296020 (0x00296020, 168 B)
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

def test_camp_func_0028d4f0():
    addr = 0x0028d4f0
    print(f"--- Testing camp_func_0028d4f0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 156)
    tmp = ROOT / "build" / "test_31c_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("camp_func_0028d4f0", tmp)

    FN_26F25C = 0x0026F25C
    FN_2AE3F0 = 0x002AE3F0

    sym_map = {
        "camp_func_0026f25c": FN_26F25C,
        "battle_func_002ae3f0": FN_2AE3F0,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "camp_func_0028d4f0")

    def run_one(code, r6_init: int, count: int, items: list[int], item_attrs: dict[int, int], slot_counts: list[int]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ctx_addr = 0x10050000
        ctx_data = bytearray(0x4000)
        struct.pack_into("<I", ctx_data, 0x2f34, r6_init)
        struct.pack_into("<h", ctx_data, 0xb4, count)
        for i, it in enumerate(items):
            struct.pack_into("<H", ctx_data, 0x8c + i * 2, it)
        uc.mem_write(ctx_addr, bytes(ctx_data))

        slots_base = 0x10060000
        for i, sc in enumerate(slot_counts):
            s_data = bytearray(0x50)
            struct.pack_into("<H", s_data, 0x48, sc)
            uc.mem_write(slots_base + i * 0x50, bytes(s_data))

        def stub_26f(uc, address, size, user_data):
            idx = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, slots_base + idx * 0x50)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        info_base = 0x10070000
        for it, attr in item_attrs.items():
            i_data = bytearray(0x50)
            i_data[0x4b] = attr
            uc.mem_write(info_base + it * 0x50, bytes(i_data))

        def stub_2ae(uc, address, size, user_data):
            it = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, info_base + it * 0x50)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_26f, None, FN_26F25C, FN_26F25C)
        uc.hook_add(UC_HOOK_CODE, stub_2ae, None, FN_2AE3F0, FN_2AE3F0)

        uc.reg_write(UC_ARM_REG_R0, ctx_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Test case 1: r6 = 2, count = 3, matching item
    r_orig = run_one(orig_code, 2, 3, [10, 20, 30], {10: 1, 20: 2, 30: 3}, [0]*12)
    r_dec = run_one(decomp_code, 2, 3, [10, 20, 30], {10: 1, 20: 2, 30: 3}, [0]*12)
    assert r_orig == r_dec == 20, f"Mismatch case 1: {r_orig} vs {r_dec}"

    # Test case 2: r6 = 0 -> counted from slots (e.g. 3 non-zero slots -> r6 = 3)
    slot_counts = [1, 0, 1, 1] + [0]*8
    r_orig = run_one(orig_code, 0, 3, [10, 20, 30], {10: 1, 20: 2, 30: 3}, slot_counts)
    r_dec = run_one(decomp_code, 0, 3, [10, 20, 30], {10: 1, 20: 2, 30: 3}, slot_counts)
    assert r_orig == r_dec == 30, f"Mismatch case 2: {r_orig} vs {r_dec}"

    # Test case 3: r6 = 5 (out of range 1..4) -> r6 reset to 0, no non-zero slots -> r6 = 0 -> returns 0
    r_orig = run_one(orig_code, 5, 3, [10, 20, 30], {10: 1, 20: 2, 30: 3}, [0]*12)
    r_dec = run_one(decomp_code, 5, 3, [10, 20, 30], {10: 1, 20: 2, 30: 3}, [0]*12)
    assert r_orig == r_dec == 0, f"Mismatch case 3: {r_orig} vs {r_dec}"

    # Test case 4: count <= 0 -> returns 0
    r_orig = run_one(orig_code, 2, 0, [10, 20, 30], {10: 1, 20: 2, 30: 3}, [0]*12)
    r_dec = run_one(decomp_code, 2, 0, [10, 20, 30], {10: 1, 20: 2, 30: 3}, [0]*12)
    assert r_orig == r_dec == 0, f"Mismatch case 4: {r_orig} vs {r_dec}"

    print("  camp_func_0028d4f0: PASS")

def test_script_vm_func_00290374():
    addr = 0x00290374
    print(f"--- Testing script_vm_func_00290374 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 156)
    tmp = ROOT / "build" / "test_31c_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_00290374", tmp)

    FN_2B6E60 = 0x002B6E60
    FN_2899C4 = 0x002899C4

    sym_map = {
        "battle_func_002b6e60": FN_2B6E60,
        "script_vm_func_002899c4": FN_2899C4,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "script_vm_func_00290374")

    def run_one(code, flags: int, val_46: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        buf_addr = 0x10050000
        buf_data = bytearray(0x1000)
        struct.pack_into("<H", buf_data, 0x608, flags)
        struct.pack_into("<H", buf_data, 0x46, val_46)
        struct.pack_into("<H", buf_data, 0x604, 0x1234)
        uc.mem_write(buf_addr, bytes(buf_data))

        calls = []

        def stub_2b6(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, buf_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_289(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            calls.append((r0, r1, r2))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2b6, None, FN_2B6E60, FN_2B6E60)
        uc.hook_add(UC_HOOK_CODE, stub_289, None, FN_2899C4, FN_2899C4)

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        out_mem = uc.mem_read(buf_addr, 0x700)
        return calls, out_mem

    # Case 1: flags & 1 != 0, val == 0x2a3
    c_orig, m_orig = run_one(orig_code, 1, 0x2a3)
    c_dec, m_dec = run_one(decomp_code, 1, 0x2a3)
    assert c_orig == c_dec == [(0x262, 0, 1)], f"Mismatch case 1 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 1 memory"

    # Case 2: flags & 1 != 0, val == 0x2a5
    c_orig, m_orig = run_one(orig_code, 1, 0x2a5)
    c_dec, m_dec = run_one(decomp_code, 1, 0x2a5)
    assert c_orig == c_dec == [(0x263, 0, 1)], f"Mismatch case 2 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 2 memory"

    # Case 3: flags & 1 == 0
    c_orig, m_orig = run_one(orig_code, 0, 0x2a3)
    c_dec, m_dec = run_one(decomp_code, 0, 0x2a3)
    assert c_orig == c_dec == [], f"Mismatch case 3 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 3 memory"

    print("  script_vm_func_00290374: PASS")

def test_script_vm_func_002911ec():
    addr = 0x002911ec
    print(f"--- Testing script_vm_func_002911ec ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 192)
    tmp = ROOT / "build" / "test_31c_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002911ec", tmp)

    FN_2C583C = 0x002C583C

    sym_map = {
        "engine_func_002c583c": FN_2C583C,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "script_vm_func_002911ec")

    def run_one(code, ret_c58: int, arg: int, f1: int, f2: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ch1_addr = 0x004C53C4
        ch2_addr = 0x004C53E4
        out_addr = 0x0044E098

        ch1_data = bytearray(0x20)
        struct.pack_into("<I", ch1_data, 0, 0x1111)
        struct.pack_into("<I", ch1_data, 0x1c, f1)
        uc.mem_write(ch1_addr, bytes(ch1_data))

        ch2_data = bytearray(0x20)
        struct.pack_into("<I", ch2_data, 0, 0x2222)
        struct.pack_into("<I", ch2_data, 0x1c, f2)
        uc.mem_write(ch2_addr, bytes(ch2_data))

        out_data = bytearray(0x10)
        uc.mem_write(out_addr, bytes(out_data))

        def stub_c58(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, ret_c58)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_c58, None, FN_2C583C, FN_2C583C)

        uc.reg_write(UC_ARM_REG_R0, arg)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return (
            uc.mem_read(ch1_addr, 0x20),
            uc.mem_read(ch2_addr, 0x20),
            uc.mem_read(out_addr, 0x10),
        )

    # Case 1: engine_func_002c583c returns 1 -> early exit
    m_orig = run_one(orig_code, 1, 999, 0x22, 0x22)
    m_dec = run_one(decomp_code, 1, 999, 0x22, 0x22)
    assert m_orig == m_dec, "Mismatch case 1"

    # Case 2: engine_func returns 0; ch1 has 0x22 (2 | 0x20), ch2 has 0
    m_orig = run_one(orig_code, 0, 42, 0x22, 0)
    m_dec = run_one(decomp_code, 0, 42, 0x22, 0)
    assert m_orig == m_dec, "Mismatch case 2"

    # Case 3: engine_func returns 0; ch1 has 2 (no 0x20, no 0x400) -> timer=30, f1|=8; ch2 has 0x22
    m_orig = run_one(orig_code, 0, 77, 2, 0x22)
    m_dec = run_one(decomp_code, 0, 77, 2, 0x22)
    assert m_orig == m_dec, "Mismatch case 3"

    # Case 4: ch1 has 0x402 (2 | 0x400) -> nothing done; ch2 has 2
    m_orig = run_one(orig_code, 0, 88, 0x402, 2)
    m_dec = run_one(decomp_code, 0, 88, 0x402, 2)
    assert m_orig == m_dec, "Mismatch case 4"

    print("  script_vm_func_002911ec: PASS")

def test_script_vm_func_002956c0():
    addr = 0x002956c0
    print(f"--- Testing script_vm_func_002956c0 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 160)
    tmp = ROOT / "build" / "test_31c_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_002956c0", tmp)

    FN_2A755C = 0x002A755C
    FN_2C4360 = 0x002C4360
    FN_252630 = 0x00252630
    FN_296A18 = 0x00296A18
    FN_29EB14 = 0x0029EB14
    FN_29EA28 = 0x0029EA28

    sym_map = {
        "script_vm_func_002a755c": FN_2A755C,
        "engine_func_002c4360": FN_2C4360,
        "script_vm_func_00252630": FN_252630,
        "script_vm_func_00296a18": FN_296A18,
        "ui_func_0029eb14": FN_29EB14,
        "camp_func_0029ea28": FN_29EA28,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "script_vm_func_002956c0")

    def run_one(code, count_init: int, limit: int):
        uc = create_emulator()
        uc.mem_write(addr, code)

        ctx_addr = 0x10050000
        ctx_data = bytearray(0xe000)
        struct.pack_into("<I", ctx_data, 0x3574, 0x1111)
        struct.pack_into("<I", ctx_data, 0x3578, 0x2222)
        struct.pack_into("<I", ctx_data, 0xcf74, limit)
        struct.pack_into("<I", ctx_data, 0xcf78, count_init)
        ctx_data[0xd640] = 0x99
        uc.mem_write(ctx_addr, bytes(ctx_data))

        calls = []

        def make_stub(name, num_args):
            def stub(uc, address, size, user_data):
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                if num_args == 0:
                    calls.append((name,))
                elif num_args == 1:
                    calls.append((name, r0))
                else:
                    calls.append((name, r0, r1))
                lr = uc.reg_read(UC_ARM_REG_LR)
                uc.reg_write(UC_ARM_REG_PC, lr)
            return stub

        uc.hook_add(UC_HOOK_CODE, make_stub("2a7", 1), None, FN_2A755C, FN_2A755C)
        uc.hook_add(UC_HOOK_CODE, make_stub("2c4", 1), None, FN_2C4360, FN_2C4360)
        uc.hook_add(UC_HOOK_CODE, make_stub("252", 0), None, FN_252630, FN_252630)
        uc.hook_add(UC_HOOK_CODE, make_stub("296", 2), None, FN_296A18, FN_296A18)
        uc.hook_add(UC_HOOK_CODE, make_stub("29e_b14", 1), None, FN_29EB14, FN_29EB14)
        uc.hook_add(UC_HOOK_CODE, make_stub("29e_a28", 0), None, FN_29EA28, FN_29EA28)

        uc.reg_write(UC_ARM_REG_R0, ctx_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        ret = uc.reg_read(UC_ARM_REG_R0)
        out_ctx = uc.mem_read(ctx_addr + 0xcf70, 0x10)
        d640 = uc.mem_read(ctx_addr + 0xd640, 1)
        return ret, calls, out_ctx, d640

    # Case 1: count_init + 1 == limit -> branch taken, calls 296a18(ctx, 20), returns 0
    r_orig, c_orig, m_orig, d_orig = run_one(orig_code, 4, 5)
    r_dec, c_dec, m_dec, d_dec = run_one(decomp_code, 4, 5)
    assert r_orig == r_dec == 0, f"Mismatch case 1 ret: {r_orig} vs {r_dec}"
    assert c_orig == c_dec, f"Mismatch case 1 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 1 mem"
    assert d_orig == d_dec == b'\x00', "Mismatch case 1 d640"

    # Case 2: count_init + 1 != limit -> branch not taken, calls 29eb14(1), 29ea28(), 296a18(ctx, 9), returns 1
    r_orig, c_orig, m_orig, d_orig = run_one(orig_code, 2, 5)
    r_dec, c_dec, m_dec, d_dec = run_one(decomp_code, 2, 5)
    assert r_orig == r_dec == 1, f"Mismatch case 2 ret: {r_orig} vs {r_dec}"
    assert c_orig == c_dec, f"Mismatch case 2 calls: {c_orig} vs {c_dec}"
    assert m_orig == m_dec, "Mismatch case 2 mem"

    print("  script_vm_func_002956c0: PASS")

def test_script_vm_func_00296020():
    addr = 0x00296020
    print(f"--- Testing script_vm_func_00296020 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 168)
    tmp = ROOT / "build" / "test_31c_part11"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("script_vm_func_00296020", tmp)

    FN_2A8A08 = 0x002A8A08

    sym_map = {
        "camp_func_002a8a08": FN_2A8A08,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "script_vm_func_00296020")

    def run_one(code, target_ptr: int, table_attrs: list[int], slots: list[int]):
        uc = create_emulator()
        uc.mem_write(addr, code)

        base_addr = 0x10050000
        table_data = bytearray(0xa000)
        for i, a in enumerate(table_attrs):
            table_data[0x90 + i * 0x604 + 0x4a] = a
        for i, s in enumerate(slots):
            struct.pack_into("<b", table_data, 0x9108 + i, s)
        uc.mem_write(base_addr, bytes(table_data))

        def stub_2a8(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, base_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2a8, None, FN_2A8A08, FN_2A8A08)

        uc.reg_write(UC_ARM_REG_R0, target_ptr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)

        return uc.reg_read(UC_ARM_REG_R0)

    # Setup 24 table entries
    table_attrs = [i + 10 for i in range(24)]

    # Case 1: target_ptr is NULL -> found_idx = -1 -> returns 0
    r_orig = run_one(orig_code, 0, table_attrs, [0, 1, 2])
    r_dec = run_one(decomp_code, 0, table_attrs, [0, 1, 2])
    assert r_orig == r_dec == 0, f"Mismatch case 1: {r_orig} vs {r_dec}"

    # Case 2: target_ptr matches exact entry address (e.g. entry 5)
    # slots = [1, 5, 2] -> 5 matches slot 1 -> returns 1
    target_5 = 0x10050000 + 0x90 + 5 * 0x604
    r_orig = run_one(orig_code, target_5, table_attrs, [1, 5, 2])
    r_dec = run_one(decomp_code, target_5, table_attrs, [1, 5, 2])
    assert r_orig == r_dec == 1, f"Mismatch case 2: {r_orig} vs {r_dec}"

    # Case 3: target_ptr matches entry 5, but slots = [0, 1, 2] -> no match -> returns 0
    r_orig = run_one(orig_code, target_5, table_attrs, [0, 1, 2])
    r_dec = run_one(decomp_code, target_5, table_attrs, [0, 1, 2])
    assert r_orig == r_dec == 0, f"Mismatch case 3: {r_orig} vs {r_dec}"

    # Case 4: separate buffer whose field_4a matches entry 7
    # slots = [7, -1, -1] -> returns 1
    ext_buf = 0x10040000
    def run_one_ext(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        base_addr = 0x10050000
        table_data = bytearray(0xa000)
        for i, a in enumerate(table_attrs):
            table_data[0x90 + i * 0x604 + 0x4a] = a
        struct.pack_into("<b", table_data, 0x9108, 7)
        struct.pack_into("<b", table_data, 0x9109, -1)
        struct.pack_into("<b", table_data, 0x910a, -1)
        uc.mem_write(base_addr, bytes(table_data))

        ext_data = bytearray(0x100)
        ext_data[0x4a] = table_attrs[7]
        uc.mem_write(ext_buf, bytes(ext_data))

        def stub_2a8(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, base_addr)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_2a8, None, FN_2A8A08, FN_2A8A08)
        uc.reg_write(UC_ARM_REG_R0, ext_buf)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    r_orig = run_one_ext(orig_code)
    r_dec = run_one_ext(decomp_code)
    assert r_orig == r_dec == 1, f"Mismatch case 4: {r_orig} vs {r_dec}"

    print("  script_vm_func_00296020: PASS")

def main():
    print("=== Running Batch 31 Part 11 Tests ===")
    test_camp_func_0028d4f0()
    test_script_vm_func_00290374()
    test_script_vm_func_002911ec()
    test_script_vm_func_002956c0()
    test_script_vm_func_00296020()
    print("=== All 5 Part 11 Functions PASSED ===")

if __name__ == "__main__":
    main()
