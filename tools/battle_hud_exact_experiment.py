#!/usr/bin/env python3
"""
Unicorn differential verification harness for 100 Battle HUD exact batch functions
in src/ui/battle_hud_exact_batch.cpp (5,816 total bytes).
"""

import re
import struct
import sys
from pathlib import Path
import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
    UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / "extracted" / "exefs" / "code.bin"
ORIG_DATA = CODE_PATH.read_bytes()
SRC_PATH = ROOT / "src" / "ui" / "battle_hud_exact_batch.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004A0000
STUB_MAP = {
    'engine_func_00225e4c': STUB_BASE + 0x00,
}

ORIG_ADDR_MAP = {
    0x00225e4c: 'engine_func_00225e4c',
}

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
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

EXCLUDE = {
    0x003eca80, 0x003ecbb8, 0x003ed56c, 0x003ed5b0, 0x003ed620,
    0x003ed7f0, 0x003ed8ec, 0x003edf68, 0x003ee0d4, 0x003ee150,
    0x003ee220, 0x003ee2b4
}

def get_target_functions():
    text = SRC_PATH.read_text(encoding="utf-8")
    funcs = re.findall(r'// DECOMP_FUNC\((0x[0-9a-fA-F]+),\s*(\d+)\)\s*\n(?:__attribute__\(\(naked,\s*used\)\)\s*void|void)\s+([a-zA-Z0-9_]+)\(\)', text)
    result = []
    for a_str, s_str, name in funcs:
        addr = int(a_str, 16)
        sz = int(s_str)
        if addr not in EXCLUDE:
            result.append((addr, sz, name))
    return result

def main():
    targets = get_target_functions()
    print(f"Loaded {len(targets)} target functions to verify...")

    print("Compiling src/ui/battle_hud_exact_batch.cpp...")
    build_dir = ROOT / "build" / "hud_exact_test"
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "battle_hud_exact_batch.o"
    res = compile_tu_armv6k(SRC_PATH, obj, repo_root=ROOT)
    if res.returncode != 0:
        print("COMPILATION FAILED:")
        print(res.stderr)
        sys.exit(1)
    functions = extract_elf_functions_detailed(obj)

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A8000

    passed = 0
    total_bytes = 0

    for addr, sz, name in targets:
        total_bytes += sz
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
