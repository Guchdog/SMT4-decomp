#!/usr/bin/env python3
"""Differential test for batch 31 C part 14:
- engine_func_002a3ff8 (0x002A3FF8, 164 B)
- ui_func_002a4e50 (0x002A4E50, 160 B)
- script_vm_func_002a6fa0 (0x002A6FA0, 172 B)
- func_002a7094 (0x002A7094, 176 B)
- engine_func_002a7e08 (0x002A7E08, 180 B)
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

def test_engine_func_002a3ff8():
    addr = 0x002A3FF8
    size = 164
    print(f"--- Testing engine_func_002a3ff8 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002a3ff8", tmp)

    FN_2C4B30 = 0x002C4B30
    sym_map = {
        "engine_func_002c4b30": FN_2C4B30,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002a3ff8")

    def run_one(code, buf_addr):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, buf_addr)
        uc.mem_write(buf_addr, b"\xaa" * 0x80)
        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        return uc.mem_read(buf_addr, 0x80)

    for buf in [0x10020000, 0x10021000, 0x10022000]:
        mem_orig = run_one(orig_code, buf)
        mem_decomp = run_one(decomp_code, buf)
        assert mem_orig == mem_decomp, f"Mismatch at buf {hex(buf)}"

    print("PASS: engine_func_002a3ff8")

def test_ui_func_002a4e50():
    addr = 0x002A4E50
    size = 160
    print(f"--- Testing ui_func_002a4e50 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("ui_func_002a4e50", tmp)

    FN_2C6C10 = 0x002C6C10
    sym_map = {
        "ui_func_002c6c10": FN_2C6C10,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "ui_func_002a4e50")

    cases = [
        (16, 0x10040000, 128, 4, 100),
        (32, 0x10040010, 256, 16, 200),
        (8,  0x10040020, 64,  8, 300),
        (64, 0x10040000, 512, 32, 400),
        (64, 0x10040000, 10,  16, 500),
    ]

    def run_one(code, arg1, arg2, arg3, arg4, arg5):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10020000
        uc.mem_write(obj_addr, b"\x00" * 0x40)
        uc.mem_write(0x10040000, b"\xbb" * 0x1000)

        sp = STACK_BASE
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_R2, arg2)
        uc.reg_write(UC_ARM_REG_R3, arg3)
        uc.mem_write(sp, struct.pack("<II", arg4, arg5))

        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        return uc.mem_read(obj_addr, 0x40), uc.mem_read(0x10040000, 0x1000)

    for c in cases:
        obj_orig, tgt_orig = run_one(orig_code, *c)
        obj_decomp, tgt_decomp = run_one(decomp_code, *c)
        assert obj_orig == obj_decomp, f"Obj mismatch for case {c}"
        assert tgt_orig == tgt_decomp, f"Target mem mismatch for case {c}"

    print("PASS: ui_func_002a4e50")

def test_script_vm_func_002a6fa0_and_002a7094():
    tmp = ROOT / "build" / "test_31c_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp_6fa0, relocs_6fa0 = compile_function("script_vm_func_002a6fa0", tmp)
    comp_7094, relocs_7094 = compile_function("func_002a7094", tmp)

    addr_6fa0 = 0x002A6FA0
    addr_7094 = 0x002A7094

    orig_6fa0 = load_original_bytes(addr_6fa0, 172)
    orig_7094 = load_original_bytes(addr_7094, 176)

    FN_2AC3B8 = 0x002AC3B8
    FN_2AC384 = 0x002AC384
    FN_2AC350 = 0x002AC350

    sym_map = {
        "func_002ac3b8": FN_2AC3B8,
        "func_002ac384": FN_2AC384,
        "func_002ac350": FN_2AC350,
    }
    decomp_6fa0 = stage_body(comp_6fa0, relocs_6fa0, addr_6fa0, sym_map, "script_vm_func_002a6fa0")
    decomp_7094 = stage_body(comp_7094, relocs_7094, addr_7094, sym_map, "func_002a7094")

    MGR_ADDR = 0x10020000
    GROUPS_ADDR = 0x10021000
    ENTRIES_ADDR = 0x10022000
    DATA_TABLE_ADDR = 0x10023000

    def setup_data(uc: Uc):
        uc.mem_write(MGR_ADDR, b"\x00" * 0x350)
        uc.mem_write(MGR_ADDR + 0x310, struct.pack("<I", 2))
        uc.mem_write(MGR_ADDR + 0x318, struct.pack("<I", GROUPS_ADDR))

        uc.mem_write(GROUPS_ADDR, b"\x00" * 0x100)
        uc.mem_write(GROUPS_ADDR + 0x4C, struct.pack("<I", DATA_TABLE_ADDR))
        uc.mem_write(GROUPS_ADDR + 0x50 + 0x4C, struct.pack("<I", DATA_TABLE_ADDR + 0x100))

        uc.mem_write(ENTRIES_ADDR, b"\x00" * 0x200)
        e0 = ENTRIES_ADDR
        uc.mem_write(e0 + 0x00, struct.pack("b", 5))
        uc.mem_write(e0 + 0x3C, struct.pack("<I", 100))
        e1 = ENTRIES_ADDR + 0x40
        uc.mem_write(e1 + 0x00, struct.pack("b", 12))
        uc.mem_write(e1 + 0x3C, struct.pack("<I", 200))
        e2 = ENTRIES_ADDR + 0x80
        uc.mem_write(e2 + 0x00, struct.pack("b", -5))
        uc.mem_write(e2 + 0x3C, struct.pack("<I", 300))

    def hook_stubs(uc: Uc):
        def stub_3b8(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_384(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, ENTRIES_ADDR)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_350(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 3)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_3b8, None, FN_2AC3B8, FN_2AC3B8)
        uc.hook_add(UC_HOOK_CODE, stub_384, None, FN_2AC384, FN_2AC384)
        uc.hook_add(UC_HOOK_CODE, stub_350, None, FN_2AC350, FN_2AC350)

    test_queries = [
        (-1, 100),
        (5, 100),
        (12, 200),
        (-5, 300),
        (5, 999),
        (99, 100),
    ]

    for target_id, target_tag in test_queries:
        def run_fn(code, f_addr):
            uc = create_emulator()
            uc.mem_write(f_addr, code)
            hook_stubs(uc)
            setup_data(uc)
            uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
            uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
            uc.reg_write(UC_ARM_REG_R0, MGR_ADDR)
            uc.reg_write(UC_ARM_REG_R1, target_id & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R2, target_tag)
            uc.emu_start(f_addr, 0x003F0000, timeout=1000000)
            return uc.reg_read(UC_ARM_REG_R0)

        # Test 6fa0
        r_orig = run_fn(orig_6fa0, addr_6fa0)
        r_decomp = run_fn(decomp_6fa0, addr_6fa0)
        assert r_orig == r_decomp, f"Mismatch in 6fa0 for ({target_id}, {target_tag}): {hex(r_orig)} != {hex(r_decomp)}"

        # Test 7094
        r_orig = run_fn(orig_7094, addr_7094)
        r_decomp = run_fn(decomp_7094, addr_7094)
        assert r_orig == r_decomp, f"Mismatch in 7094 for ({target_id}, {target_tag}): {hex(r_orig)} != {hex(r_decomp)}"

    print("PASS: script_vm_func_002a6fa0 and func_002a7094")

def test_engine_func_002a7e08():
    addr = 0x002A7E08
    size = 180
    print(f"--- Testing engine_func_002a7e08 ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, size)
    tmp = ROOT / "build" / "test_31c_part14"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_002a7e08", tmp)

    FN_1556F4 = 0x001556F4
    FN_2A7DD8 = 0x002A7DD8
    sym_map = {
        "func_001556f4": FN_1556F4,
        "func_002a7dd8": FN_2A7DD8,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map, "engine_func_002a7e08")

    CTX_ADDR = 0x10020000
    ARCH_ADDR = 0x10030000

    def hook_stubs(uc: Uc):
        def stub_155(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, r0 + 0x40)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def stub_2a7(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, 0x60)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(UC_HOOK_CODE, stub_155, None, FN_1556F4, FN_1556F4)
        uc.hook_add(UC_HOOK_CODE, stub_2a7, None, FN_2A7DD8, FN_2A7DD8)

    cases = [
        (0, 0, 0, 0, 0),
        (ARCH_ADDR, 0x12345678, 0x01000000, 0, 0),
        (ARCH_ADDR, 0x52415743, 0x02000000, 0, 0),
        (ARCH_ADDR, 0x52415743, 0x01000000, 0, 0),
        (ARCH_ADDR, 0x52415743, 0x01000000, 1, 0x54415743),
        (ARCH_ADDR, 0x52415743, 0x01000000, 1, 0x11111111),
    ]

    def run_one(code, arch_ptr, magic, ver, enable_cwat, cwat_mag):
        uc = create_emulator()
        uc.mem_write(addr, code)
        hook_stubs(uc)

        uc.mem_write(CTX_ADDR, b"\xdd" * 0x20)
        if arch_ptr != 0:
            buf = bytearray(0x100)
            struct.pack_into("<I", buf, 0x00, magic)
            struct.pack_into("<I", buf, 0x08, ver)
            struct.pack_into("<I", buf, 0x60, cwat_mag)
            uc.mem_write(ARCH_ADDR, bytes(buf))

        uc.reg_write(UC_ARM_REG_SP, STACK_BASE)
        uc.reg_write(UC_ARM_REG_LR, 0x003F0000)
        uc.reg_write(UC_ARM_REG_R0, CTX_ADDR)
        uc.reg_write(UC_ARM_REG_R1, arch_ptr)
        uc.reg_write(UC_ARM_REG_R2, enable_cwat)
        uc.emu_start(addr, 0x003F0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0), uc.mem_read(CTX_ADDR, 0x10)

    for c in cases:
        r_orig, ctx_orig = run_one(orig_code, *c)
        r_decomp, ctx_decomp = run_one(decomp_code, *c)
        assert r_orig == r_decomp, f"Return mismatch in 002a7e08 for case {c}: {hex(r_orig)} != {hex(r_decomp)}"
        assert ctx_orig == ctx_decomp, f"Context mismatch in 002a7e08 for case {c}"

    print("PASS: engine_func_002a7e08")

if __name__ == "__main__":
    test_engine_func_002a3ff8()
    test_ui_func_002a4e50()
    test_script_vm_func_002a6fa0_and_002a7094()
    test_engine_func_002a7e08()
    print("\n>>> ALL PART 14 TESTS PASSED! <<<")
