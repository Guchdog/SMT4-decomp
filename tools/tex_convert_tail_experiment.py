#!/usr/bin/env python3
"""
Unicorn differential verification harness for tex_convert_tail_exact.cpp:
  - 0x0017f5cc (20 B): func_0017f5cc
  - 0x0017f5e8 (16 B): func_0017f5e8
  - 0x0017f5f8 (16 B): func_0017f5f8
  - 0x0017f608 (20 B): func_0017f608
"""

import struct
import sys
from pathlib import Path
import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / "extracted" / "exefs" / "code.bin"
ORIG_DATA = CODE_PATH.read_bytes()
SRC_PATH = ROOT / "src" / "engine" / "tex_convert_tail_exact.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004A0000
STUB_MAP = {
    'func_002c68bc': STUB_BASE + 0x00,
}

ORIG_ADDR_MAP = {
    0x002c68b4: 'func_002c68bc',
    0x002c68bc: 'func_002c68bc',
}

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    return uc

class StubTracker:
    def __init__(self, uc):
        self.uc = uc
        self.calls = []

    def handle_call(self, uc, address, size, user_data):
        stub_name = user_data
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        self.calls.append({
            'name': stub_name,
            'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3,
        })
        uc.reg_write(UC_ARM_REG_R0, 0)
        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_orig_stubs(uc, tracker):
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1")
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

def setup_stubs(uc, tracker):
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1")
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)
    setup_orig_stubs(uc, tracker)

def apply_relocations(code_bytes, relocs, target_addr, rodata_addr):
    mutable = bytearray(code_bytes)
    syms = dict(STUB_MAP)
    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if not name or name.startswith(".rodata"):
            sym_val = rodata_addr
        elif name in syms:
            sym_val = syms[name]
        elif name.endswith(".cpp"):
            sym_val = target_addr
        else:
            raise ValueError(f"Unknown symbol '{name}'")

        if rel_type in (28, 29): # R_ARM_CALL / R_ARM_JUMP24
            orig = struct.unpack_from('<I', mutable, offset)[0]
            target = sym_val
            pc = target_addr + offset + 8
            new_disp = ((target - pc) >> 2) & 0x00FFFFFF
            inst = (orig & 0xFF000000) | new_disp
            struct.pack_into('<I', mutable, offset, inst)
        elif rel_type in (2, 38): # R_ARM_ABS32 or R_ARM_TARGET1
            orig = struct.unpack_from('<I', mutable, offset)[0]
            val = (sym_val + orig) & 0xFFFFFFFF
            struct.pack_into('<I', mutable, offset, val)
        else:
            raise ValueError(f"Unsupported reloc type {rel_type}")
    return bytes(mutable)

def test_func_0017f5cc(functions):
    print("Testing func_0017f5cc (0x0017f5cc, 20 B)...")
    dec_code, relocs = functions['_Z13func_0017f5ccv']
    TARGET_DECOMP = 0x00380000
    patched = apply_relocations(dec_code, relocs, TARGET_DECOMP, 0x004A0000)

    # Orig
    uc_orig = create_emulator()
    uc_orig.mem_write(CODE_BASE, ORIG_DATA)
    t_orig = StubTracker(uc_orig)
    setup_orig_stubs(uc_orig, t_orig)
    uc_orig.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc_orig.reg_write(UC_ARM_REG_LR, 0x00000000)
    uc_orig.emu_start(0x0017f5cc, 0x00000000, timeout=100000)

    # Dec
    uc_dec = create_emulator()
    uc_dec.mem_write(CODE_BASE, ORIG_DATA)
    uc_dec.mem_write(TARGET_DECOMP, patched)
    t_dec = StubTracker(uc_dec)
    setup_stubs(uc_dec, t_dec)
    uc_dec.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc_dec.reg_write(UC_ARM_REG_LR, 0x00000000)
    uc_dec.emu_start(TARGET_DECOMP, 0x00000000, timeout=100000)

    assert len(t_orig.calls) == len(t_dec.calls) == 1
    assert t_orig.calls[0]['name'] == t_dec.calls[0]['name'] == 'func_002c68bc'
    assert t_orig.calls[0]['r0'] == t_dec.calls[0]['r0'] == 0x004DACE0
    assert t_orig.calls[0]['r1'] == t_dec.calls[0]['r1'] == 0x00361C24
    assert t_orig.calls[0]['r2'] == t_dec.calls[0]['r2'] == 0x40
    assert t_orig.calls[0]['r3'] == t_dec.calls[0]['r3'] == 2
    print("  [PASS] func_0017f5cc passed 100%!")

def test_func_0017f608(functions):
    print("Testing func_0017f608 (0x0017f608, 20 B)...")
    dec_code, relocs = functions['_Z13func_0017f608v']
    TARGET_DECOMP = 0x00380000
    patched = apply_relocations(dec_code, relocs, TARGET_DECOMP, 0x004A0000)

    # Orig
    uc_orig = create_emulator()
    uc_orig.mem_write(CODE_BASE, ORIG_DATA)
    t_orig = StubTracker(uc_orig)
    setup_orig_stubs(uc_orig, t_orig)
    uc_orig.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc_orig.reg_write(UC_ARM_REG_LR, 0x00000000)
    uc_orig.emu_start(0x0017f608, 0x00000000, timeout=100000)

    # Dec
    uc_dec = create_emulator()
    uc_dec.mem_write(CODE_BASE, ORIG_DATA)
    uc_dec.mem_write(TARGET_DECOMP, patched)
    t_dec = StubTracker(uc_dec)
    setup_stubs(uc_dec, t_dec)
    uc_dec.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc_dec.reg_write(UC_ARM_REG_LR, 0x00000000)
    uc_dec.emu_start(TARGET_DECOMP, 0x00000000, timeout=100000)

    assert len(t_orig.calls) == len(t_dec.calls) == 1
    assert t_orig.calls[0]['name'] == t_dec.calls[0]['name'] == 'func_002c68bc'
    assert t_orig.calls[0]['r0'] == t_dec.calls[0]['r0'] == 0x004E5290
    assert t_orig.calls[0]['r1'] == t_dec.calls[0]['r1'] == 0x003578E8
    assert t_orig.calls[0]['r2'] == t_dec.calls[0]['r2'] == 4
    assert t_orig.calls[0]['r3'] == t_dec.calls[0]['r3'] == 3
    print("  [PASS] func_0017f608 passed 100%!")

def test_clear_func(functions, name, mangled, addr, sz):
    print(f"Testing {name} ({hex(addr)}, {sz} B)...")
    dec_code, relocs = functions[mangled]
    TARGET_DECOMP = 0x00380000

    TARGET_MEM = 0x00470000

    for init_val in [0x12345678, 0xFFFFFFFF, 0x00000000]:
        uc_orig = create_emulator()
        uc_orig.mem_write(CODE_BASE, ORIG_DATA)
        uc_orig.mem_write(TARGET_MEM, struct.pack('<II', init_val, init_val))
        uc_orig.reg_write(UC_ARM_REG_R0, TARGET_MEM)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc_orig.reg_write(UC_ARM_REG_LR, 0x00000000)
        uc_orig.emu_start(addr, 0x00000000, timeout=100000)

        uc_dec = create_emulator()
        uc_dec.mem_write(CODE_BASE, ORIG_DATA)
        uc_dec.mem_write(TARGET_DECOMP, dec_code)
        uc_dec.mem_write(TARGET_MEM, struct.pack('<II', init_val, init_val))
        uc_dec.reg_write(UC_ARM_REG_R0, TARGET_MEM)
        uc_dec.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc_dec.reg_write(UC_ARM_REG_LR, 0x00000000)
        uc_dec.emu_start(TARGET_DECOMP, 0x00000000, timeout=100000)

        val_orig = uc_orig.mem_read(TARGET_MEM, 8)
        val_dec = uc_dec.mem_read(TARGET_MEM, 8)
        assert val_orig == val_dec == b"\x00" * 8

    print(f"  [PASS] {name} passed 100%!")

def main():
    print("Compiling src/engine/tex_convert_tail_exact.cpp...")
    build_dir = ROOT / "build" / "tex_convert_tail_test"
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "tex_convert_tail_exact.o"
    res = compile_tu_armv6k(SRC_PATH, obj, repo_root=ROOT)
    if res.returncode != 0:
        print("COMPILATION FAILED:")
        print(res.stderr)
        sys.exit(1)
    functions = extract_elf_functions_detailed(obj)

    test_func_0017f5cc(functions)
    test_clear_func(functions, 'func_0017f5e8', '_Z13func_0017f5e8Pj', 0x0017f5e8, 16)
    test_clear_func(functions, 'func_0017f5f8', '_Z13func_0017f5f8Pj', 0x0017f5f8, 16)
    test_func_0017f608(functions)

    print("\nALL 4 TEX CONVERT TAIL FUNCTIONS (72 BYTES) PASSED 100%!")

if __name__ == "__main__":
    main()
