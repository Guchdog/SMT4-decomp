#!/usr/bin/env python3
"""
Unicorn differential verification harness for 27 Battle HUD reset and initialization
routines in src/ui/battle_hud_gap_batch.cpp (1,232 total bytes).
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
SRC_PATH = ROOT / "src" / "ui" / "battle_hud_gap_batch.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004A0000
STUB_MAP = {
    'engine_func_00225e4c': STUB_BASE + 0x00,
    'engine_func_002c3b00': STUB_BASE + 0x08,
}

ORIG_ADDR_MAP = {
    0x00225e4c: 'engine_func_00225e4c',
    0x002c3b00: 'engine_func_002c3b00',
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

FUNCS_27 = [
    (0x003f142c, 44, 'func_003f142c'),
    (0x003f1464, 52, 'func_003f1464'),
    (0x003f1498, 60, 'func_003f1498'),
    (0x003f1558, 60, 'func_003f1558'),
    (0x003f1730, 44, 'func_003f1730'),
    (0x003f175c, 28, 'func_003f175c'),
    (0x003f1778, 28, 'func_003f1778'),
    (0x003f1818, 56, 'func_003f1818'),
    (0x003f1b98, 20, 'func_003f1b98'),
    (0x003f1cb4, 60, 'func_003f1cb4'),
    (0x003f1cf0, 20, 'func_003f1cf0'),
    (0x003f1d30, 24, 'func_003f1d30'),
    (0x003f1df8, 20, 'func_003f1df8'),
    (0x003f1e38, 24, 'func_003f1e38'),
    (0x003f24e8, 52, 'func_003f24e8'),
    (0x003f25a0, 20, 'func_003f25a0'),
    (0x003f28f0, 60, 'func_003f28f0'),
    (0x003f2984, 60, 'func_003f2984'),
    (0x003f29c0, 56, 'func_003f29c0'),
    (0x003f2a50, 52, 'func_003f2a50'),
    (0x003f2a84, 60, 'func_003f2a84'),
    (0x003f1594, 48, 'func_003f1594'),
    (0x003f15c4, 56, 'func_003f15c4'),
    (0x003f2b44, 68, 'func_003f2b44'),
    (0x003f0000, 48, 'func_003f0000'),
    (0x003f2210, 68, 'func_003f2210'),
    (0x003f2254, 92, 'func_003f2254'),
]

def main():
    print("Compiling src/ui/battle_hud_gap_batch.cpp...")
    build_dir = ROOT / "build" / "gap27_test"
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "battle_hud_gap_batch.o"
    res = compile_tu_armv6k(SRC_PATH, obj, repo_root=ROOT)
    if res.returncode != 0:
        print("COMPILATION FAILED:")
        print(res.stderr)
        sys.exit(1)
    print("Compiled successfully. Extracting functions...")
    functions = extract_elf_functions_detailed(obj)

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000

    passed = 0
    total_bytes = 0

    for addr, sz, name in FUNCS_27:
        total_bytes += sz
        # Find compiled function bytes & relocs
        dec_code = None
        dec_relocs = None
        for mangled, (b, relocs) in functions.items():
            if name in mangled:
                dec_code = b
                dec_relocs = relocs
                break
        if dec_code is None:
            raise KeyError(f"Function {name} not found in compiled object")

        patched_code = apply_relocations(dec_code, dec_relocs, TARGET_DECOMP, RODATA_ADDR)

        # Run original
        uc_orig = create_emulator()
        uc_orig.mem_write(CODE_BASE, ORIG_DATA)
        tracker_orig = StubTracker(uc_orig)
        setup_orig_stubs(uc_orig, tracker_orig)
        writes_orig = []
        def hook_orig(uc, access, address, size, value, user_data):
            if not (0x0FFFF000 <= address < 0x10000000):
                writes_orig.append((address, size, value))
        uc_orig.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_orig)
        uc_orig.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc_orig.reg_write(UC_ARM_REG_LR, 0x00000000)
        uc_orig.emu_start(addr, 0x00000000, timeout=100000)

        # Run decompiled
        uc_dec = create_emulator()
        uc_dec.mem_write(CODE_BASE, ORIG_DATA)
        uc_dec.mem_write(TARGET_DECOMP, patched_code)
        tracker_dec = StubTracker(uc_dec)
        setup_stubs(uc_dec, tracker_dec)
        writes_dec = []
        def hook_dec(uc, access, address, size, value, user_data):
            if not (0x0FFFF000 <= address < 0x10000000):
                writes_dec.append((address, size, value))
        uc_dec.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_dec)
        uc_dec.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc_dec.reg_write(UC_ARM_REG_LR, 0x00000000)
        uc_dec.emu_start(TARGET_DECOMP, 0x00000000, timeout=100000)

        # Check calls match
        assert len(tracker_orig.calls) == len(tracker_dec.calls), f"Call count mismatch for {name}: orig={tracker_orig.calls}, dec={tracker_dec.calls}"
        for i in range(len(tracker_orig.calls)):
            c1 = tracker_orig.calls[i]
            c2 = tracker_dec.calls[i]
            assert c1['name'] == c2['name'], f"Call name mismatch for {name}: {c1} vs {c2}"
            assert c1['r0'] == c2['r0'], f"Call r0 mismatch for {name}: {c1} vs {c2}"
            if c1['name'] == 'engine_func_00225e4c':
                assert c1['r1'] == c2['r1'], f"Call r1 mismatch for {name}: {c1} vs {c2}"
                assert c1['r2'] == c2['r2'], f"Call r2 mismatch for {name}: {c1} vs {c2}"

        # Check written memory matches
        all_written_addrs = set(a for a, s, v in writes_orig) | set(a for a, s, v in writes_dec)
        for written_addr in all_written_addrs:
            val_orig = uc_orig.mem_read(written_addr, 4)
            val_dec = uc_dec.mem_read(written_addr, 4)
            assert val_orig == val_dec, f"Memory mismatch at {hex(written_addr)} for {name}: orig={val_orig.hex()}, dec={val_dec.hex()}"

        passed += 1

    print(f"\nALL {passed} FUNCTIONS ({total_bytes} BYTES) PASSED 100% UNICORN DIFFERENTIAL TEST!")

if __name__ == "__main__":
    main()
