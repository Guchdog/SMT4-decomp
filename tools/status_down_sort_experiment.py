#!/usr/bin/env python3
"""
Unicorn differential verification harness for 9 StatusDown sort comparators
in src/ui/status_down.cpp (1,024 total bytes).
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
SRC_PATH = ROOT / "src" / "ui" / "status_down.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004A0000
STUB_MAP = {
    'camp_func_00257744': STUB_BASE + 0x00,
    'camp_func_002b9364': STUB_BASE + 0x10,
    'func_00257678': STUB_BASE + 0x20,
}

ORIG_ADDR_MAP = {
    0x00257744: 'camp_func_00257744',
    0x002b9364: 'camp_func_002b9364',
    0x00257678: 'func_00257678',
}

SORT_FUNCS = [
    (0x001f6174, 48, 'StatusDown_SkillSortByNameAsc'),
    (0x00206be8, 80, 'StatusDown_SkillSortByIdAsc'),
    (0x002e4534, 80, 'StatusDown_SkillSortByIdDesc'),
    (0x001f60dc, 152, 'StatusDown_SkillSortByCostAsc'),
    (0x002dc96c, 152, 'StatusDown_SkillSortByCostDesc'),
    (0x00206c38, 132, 'StatusDown_ItemSortByTypeAsc'),
    (0x002e4584, 132, 'StatusDown_ItemSortByTypeDesc'),
    (0x00206cbc, 124, 'StatusDown_ItemSortByIdAsc'),
    (0x002e4608, 124, 'StatusDown_ItemSortByIdDesc'),
]

# Mock table entries memory region
TABLE_BASE = 0x00480000

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
        self.calls.append({'name': stub_name, 'r0': r0})

        if stub_name == 'camp_func_00257744':
            # Returns pointer to SkillTableEntry for skill_id r0
            # We map entry at TABLE_BASE + (r0 * 0x40)
            entry_addr = TABLE_BASE + (r0 * 0x40)
            uc.reg_write(UC_ARM_REG_R0, entry_addr)
        elif stub_name == 'camp_func_002b9364':
            # Returns pointer to ItemTableEntry for item_id r0
            entry_addr = TABLE_BASE + 0x4000 + (r0 * 0x40)
            uc.reg_write(UC_ARM_REG_R0, entry_addr)
        elif stub_name == 'func_00257678':
            # Calculates cost from cost_raw (e.g. abs or scaled)
            # original does simple integer arithmetic
            cost = r0 if r0 >= 0 else -r0
            uc.reg_write(UC_ARM_REG_R0, cost)
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)

        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_orig_stubs(uc, tracker):
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

def setup_stubs(uc, tracker):
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
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
            matched = False
            for k in syms:
                if k in name or name in k:
                    sym_val = syms[k]
                    matched = True
                    break
            if not matched:
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

def setup_mock_tables(uc):
    # Set up mock skill entries at TABLE_BASE
    # SkillTableEntry: +0x22: s16 cost_raw, +0x32: u16 sort_order
    for skill_id in range(16):
        addr = TABLE_BASE + (skill_id * 0x40)
        uc.mem_write(addr, b'\x00' * 0x40)
        cost_raw = (skill_id + 1) * 5
        sort_order = 100 - skill_id * 3
        uc.mem_write(addr + 0x22, struct.pack('<h', cost_raw))
        uc.mem_write(addr + 0x32, struct.pack('<H', sort_order))

    # Set up mock item entries at TABLE_BASE + 0x4000
    # ItemTableEntry: +0x00: u16 id, +0x02: u8 category, +0x03: u8 rarity
    for item_id in range(16):
        addr = TABLE_BASE + 0x4000 + (item_id * 0x40)
        uc.mem_write(addr, b'\x00' * 0x40)
        cat = (item_id % 4) + 1
        rarity = (item_id % 3) + 1
        uc.mem_write(addr + 0x00, struct.pack('<H', item_id))
        uc.mem_write(addr + 0x02, struct.pack('B', cat))
        uc.mem_write(addr + 0x03, struct.pack('B', rarity))

def main():
    print(f"Loaded {len(SORT_FUNCS)} sort functions to verify...")

    print("Compiling src/ui/status_down.cpp...")
    build_dir = ROOT / "build" / "status_down_sort_test"
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "status_down.o"
    res = compile_tu_armv6k(SRC_PATH, obj, repo_root=ROOT)
    if res.returncode != 0:
        print("COMPILATION FAILED:")
        print(res.stderr)
        sys.exit(1)
    functions = extract_elf_functions_detailed(obj)

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A8000

    # Test pairs (id_a, val_a) vs (id_b, val_b)
    TEST_PAIRS = [
        ((1, 2), (3, 4)),
        ((3, 4), (1, 2)),
        ((1, 2), (1, 2)),
        ((1, 0), (2, 3)),
        ((2, 3), (1, 0)),
        ((1, 0), (2, 0)),
        ((2, 2), (4, 2)), # same val, different id
        ((4, 2), (2, 2)),
    ]

    passed = 0
    total_bytes = 0

    for addr, sz, name in SORT_FUNCS:
        total_bytes += sz
        dec_code = None
        dec_relocs = None
        for mangled, (b, relocs) in functions.items():
            if f"{len(name)}{name}" in mangled or mangled.endswith(name) or name == mangled:
                dec_code = b
                dec_relocs = relocs
                break
        if dec_code is None:
            raise KeyError(f"Function {name} not found in compiled object")

        patched_code = apply_relocations(dec_code, dec_relocs, TARGET_DECOMP, RODATA_ADDR)

        ENTRY_A = 0x0FFFF000
        ENTRY_B = 0x0FFFF010

        for (id_a, val_a), (id_b, val_b) in TEST_PAIRS:
            entry_a_bytes = struct.pack('<HH', id_a, val_a)
            entry_b_bytes = struct.pack('<HH', id_b, val_b)

            # Run orig
            uc_orig = create_emulator()
            uc_orig.mem_write(CODE_BASE, ORIG_DATA)
            setup_mock_tables(uc_orig)
            tracker_orig = StubTracker(uc_orig)
            setup_orig_stubs(uc_orig, tracker_orig)
            uc_orig.mem_write(ENTRY_A, entry_a_bytes)
            uc_orig.mem_write(ENTRY_B, entry_b_bytes)
            uc_orig.reg_write(UC_ARM_REG_R0, ENTRY_A)
            uc_orig.reg_write(UC_ARM_REG_R1, ENTRY_B)
            uc_orig.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc_orig.reg_write(UC_ARM_REG_LR, 0x0)
            uc_orig.emu_start(addr, 0x0, timeout=100000)
            ret_orig = uc_orig.reg_read(UC_ARM_REG_R0)
            ret_orig = struct.unpack('i', struct.pack('I', ret_orig & 0xFFFFFFFF))[0]

            # Run dec
            uc_dec = create_emulator()
            uc_dec.mem_write(CODE_BASE, ORIG_DATA)
            setup_mock_tables(uc_dec)
            tracker_dec = StubTracker(uc_dec)
            setup_stubs(uc_dec, tracker_dec)
            uc_dec.mem_write(TARGET_DECOMP, patched_code)
            uc_dec.mem_write(ENTRY_A, entry_a_bytes)
            uc_dec.mem_write(ENTRY_B, entry_b_bytes)
            uc_dec.reg_write(UC_ARM_REG_R0, ENTRY_A)
            uc_dec.reg_write(UC_ARM_REG_R1, ENTRY_B)
            uc_dec.reg_write(UC_ARM_REG_SP, STACK_TOP)
            uc_dec.reg_write(UC_ARM_REG_LR, 0x0)
            uc_dec.emu_start(TARGET_DECOMP, 0x0, timeout=100000)
            ret_dec = uc_dec.reg_read(UC_ARM_REG_R0)
            ret_dec = struct.unpack('i', struct.pack('I', ret_dec & 0xFFFFFFFF))[0]

            # In qsort comparators: compare sign (negative, zero, positive) or exact value
            # Let's check exact return value
            assert ret_orig == ret_dec, f"Sort return mismatch for {name} on {((id_a, val_a), (id_b, val_b))}: orig={ret_orig}, dec={ret_dec}"

        passed += 1

    print(f"\nALL {passed} STATUS_DOWN SORT FUNCTIONS ({total_bytes} BYTES) PASSED 100% UNICORN DIFFERENTIAL TEST!")

if __name__ == "__main__":
    main()
