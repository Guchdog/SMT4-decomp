#!/usr/bin/env python3
"""Differential test for batch 31 B part 8:
- func_003e70c8 (0x003E70C8, 48 B)
- engine_func_003f6708 (0x003F6708, 48 B)
- func_00338658 (0x00338658, 52 B)
- func_003e69dc (0x003E69DC, 52 B)
- func_003e6a10 (0x003E6A10, 52 B)
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
SOURCE = ROOT / "src/engine/leaf_batch31_b.cpp"

with open(ORIG_BIN, "rb") as f:
    ORIG_DATA = f.read()

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch31_b.o"
        result = compile_tu_armv6k(source, obj, ROOT)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
    if func_name not in COMPILED_FUNCTIONS:
        raise RuntimeError(f"{func_name} not in object")
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int]) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym not in symbol_map:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = symbol_map[sym]
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        imm24 = (rel_off >> 2) & 0x00FFFFFF
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)

def hook_unmapped(uc, access, address, size, value, user_data):
    aligned = address & ~0xFFF
    try:
        uc.mem_map(aligned, 0x1000)
    except Exception:
        pass
    return True

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    try:
        val = uc.reg_read(UC_ARM_REG_C1_C0_2)
        uc.reg_write(UC_ARM_REG_C1_C0_2, val | (0xF << 20))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def test_func_003e70c8():
    print("--- Testing func_003e70c8 (0x003e70c8) ---")
    addr = 0x003E70C8
    orig_code = load_original_bytes(addr, 48)
    tmp = ROOT / "build" / "test_31b_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_003e70c8", tmp)

    def run_one(code, magic, ver):
        uc = create_emulator()
        uc.mem_write(addr, code)
        hdr = 0x10082000
        uc.mem_write(hdr, struct.pack("<III", magic, 0, ver))
        uc.reg_write(UC_ARM_REG_R1, hdr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    # Valid magic + various versions
    cases = [
        (0x4D545343, 0x02000000, 1),
        (0x4D545343, 0x02008000, 1),
        (0x4D545343, 0x02010000, 1),
        (0x4D545343, 0x02010001, 0),
        (0x4D545343, 0x01FFFFFF, 0),
        (0x12345678, 0x02000000, 0),
    ]
    for magic, ver, expected in cases:
        r_orig = run_one(orig_code, magic, ver)
        r_decomp = run_one(comp, magic, ver)
        assert r_orig == expected, f"orig: {r_orig} != {expected}"
        assert r_decomp == expected, f"decomp: {r_decomp} != {expected}"
    print("func_003e70c8: PASS")

def test_engine_func_003f6708():
    print("--- Testing engine_func_003f6708 (0x003f6708) ---")
    addr = 0x003F6708
    orig_code = load_original_bytes(addr, 48)
    tmp = ROOT / "build" / "test_31b_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, relocs = compile_function("engine_func_003f6708", tmp)

    sym_map = {
        "engine_func_002c3aa8": 0x002C3AA8,
        "engine_func_002c3a24": 0x002C3A24,
    }
    decomp_code = stage_body(comp, relocs, addr, sym_map)

    def run_one(code, val):
        uc = create_emulator()
        uc.mem_write(addr, code)
        try:
            uc.mem_map(0x004D4000, 0x2000)
        except Exception:
            pass
        # Initialize mutex
        uc.mem_write(0x004D4674, b"\x00" * 32)
        
        # Stub mutex functions to return immediately and record calls
        calls = []
        def lock_hook(uc, address, size, user_data):
            calls.append("lock")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, lr)
        def unlock_hook(uc, address, size, user_data):
            calls.append("unlock")
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, lock_hook, None, 0x002C3AA8, 0x002C3AA8)
        h2 = uc.hook_add(UC_HOOK_CODE, unlock_hook, None, 0x002C3A24, 0x002C3A24)

        src_addr = 0x10082000
        out_addr = 0x10083000
        uc.mem_write(src_addr + 0x38, struct.pack("<I", val))
        uc.mem_write(out_addr, struct.pack("<I", 0xDEADBEEF))
        uc.reg_write(UC_ARM_REG_R0, src_addr)
        uc.reg_write(UC_ARM_REG_R1, out_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        r0 = uc.reg_read(UC_ARM_REG_R0)
        out_val = struct.unpack("<I", uc.mem_read(out_addr, 4))[0]
        return r0, out_val, calls

    for test_val in [0, 42, 0x12345678, 0xFFFFFFFF]:
        o_r0, o_val, o_calls = run_one(orig_code, test_val)
        d_r0, d_val, d_calls = run_one(decomp_code, test_val)
        assert o_r0 == 1 and o_val == test_val and o_calls == ["lock", "unlock"]
        assert d_r0 == 1 and d_val == test_val and d_calls == ["lock", "unlock"]
    print("engine_func_003f6708: PASS")

def test_func_00338658():
    print("--- Testing func_00338658 (0x00338658) ---")
    addr = 0x00338658
    orig_code = load_original_bytes(addr, 52)
    tmp = ROOT / "build" / "test_31b_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function("func_00338658", tmp)

    def run_one(code):
        uc = create_emulator()
        uc.mem_write(addr, code)
        obj_addr = 0x10082000
        uc.mem_write(obj_addr + 0x1EA4, b"\xFF" * 28)
        uc.reg_write(UC_ARM_REG_R0, obj_addr)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        floats = struct.unpack("<6f", uc.mem_read(obj_addr + 0x1EA4, 24))
        u32_val = struct.unpack("<I", uc.mem_read(obj_addr + 0x1EBC, 4))[0]
        return floats, u32_val

    orig_fl, orig_u = run_one(orig_code)
    decomp_fl, decomp_u = run_one(comp)
    assert orig_fl == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0) and orig_u == 0
    assert decomp_fl == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0) and decomp_u == 0
    print("func_00338658: PASS")

def test_archive_lookup(name: str, addr: int, expected_tag: int):
    print(f"--- Testing {name} ({hex(addr)}) ---")
    orig_code = load_original_bytes(addr, 52)
    tmp = ROOT / "build" / "test_31b_part8"
    tmp.mkdir(parents=True, exist_ok=True)
    comp, _ = compile_function(name, tmp)

    def run_one(code, archive_addr, idx):
        uc = create_emulator()
        uc.mem_write(addr, code)
        uc.reg_write(UC_ARM_REG_R0, archive_addr)
        uc.reg_write(UC_ARM_REG_R1, idx)
        uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
        uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
        uc.emu_start(addr, 0x003E0000, timeout=1000000)
        return uc.reg_read(UC_ARM_REG_R0)

    arch_addr = 0x10082000
    # Create archive with 3 entries:
    # count = 3
    # entry 0: tag=expected_tag, off=0x100 -> returns arch_addr + 0x100
    # entry 1: tag=0x9999 (mismatch), off=0x200 -> returns 0
    # entry 2: tag=expected_tag, off=0x300 -> returns arch_addr + 0x300
    uc_setup = bytearray(0x400)
    struct.pack_into("<I", uc_setup, 0, 3) # count = 3
    # entry 0 at arch_addr + 0 (ldrh [r1, #4], ldr [r1, #8])
    struct.pack_into("<HHI", uc_setup, 4, expected_tag, 0, 0x100)
    # entry 1 at arch_addr + 8
    struct.pack_into("<HHI", uc_setup, 12, 0x9999, 0, 0x200)
    # entry 2 at arch_addr + 16
    struct.pack_into("<HHI", uc_setup, 20, expected_tag, 0, 0x300)

    # Test all indices
    for idx, exp_off in [(0, arch_addr + 0x100), (1, 0), (2, arch_addr + 0x300), (3, 0), (10, 0)]:
        def test_with_archive(code):
            uc = create_emulator()
            uc.mem_write(arch_addr, bytes(uc_setup))
            uc.mem_write(addr, code)
            uc.reg_write(UC_ARM_REG_R0, arch_addr)
            uc.reg_write(UC_ARM_REG_R1, idx)
            uc.reg_write(UC_ARM_REG_SP, STACK_BASE + 0x8000)
            uc.reg_write(UC_ARM_REG_LR, 0x003E0000)
            uc.emu_start(addr, 0x003E0000, timeout=1000000)
            return uc.reg_read(UC_ARM_REG_R0)

        r_orig = test_with_archive(orig_code)
        r_decomp = test_with_archive(comp)
        assert r_orig == exp_off, f"idx {idx}: orig {hex(r_orig)} != {hex(exp_off)}"
        assert r_decomp == exp_off, f"idx {idx}: decomp {hex(r_decomp)} != {hex(exp_off)}"
    print(f"{name}: PASS")

def main():
    test_func_003e70c8()
    test_engine_func_003f6708()
    test_func_00338658()
    test_archive_lookup("func_003e69dc", 0x003E69DC, 0x4101)
    test_archive_lookup("func_003e6a10", 0x003E6A10, 0x4102)
    print("ALL BATCH 31 B PART 8 TESTS PASSED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
