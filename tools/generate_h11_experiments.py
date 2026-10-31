#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H11."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h11_shop_setselecteditem_experiment.py
(TOOLS / 'h11_shop_setselecteditem_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0022A60C Shop_SetSelectedItem."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_setselecteditem_candidate.cpp'
ORIG_ADDR = 0x0022A60C
ORIG_SIZE = 52
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_setselecteditem.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h11_shop_setselecteditem_candidate']
    raw_mut, _ = funcs['h11_shop_setselecteditem_mutation']
    return raw_cand, raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, is_locked: int, cur_item: int, new_item: int) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    CTX_ADDR = 0x08000000
    uc.mem_map(CTX_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    buf = bytearray(0x100)
    struct.pack_into('<I', buf, 0x4C, cur_item)
    buf[0x61] = 0 # dirty
    buf[0x62] = is_locked
    uc.mem_write(CTX_ADDR, bytes(buf))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, CTX_ADDR)
    uc.reg_write(UC_ARM_REG_R1, new_item)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.mem_read(CTX_ADDR, 0x100)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    cases = [
        (0, 0x10, 0x20),
        (0, 0x20, 0x20),
        (1, 0x10, 0x30),
    ]

    for is_locked, cur, new_i in cases:
        orig_out = run_simulation(image, cand_blob, ORIG_ADDR, is_locked, cur, new_i)
        cand_out = run_simulation(image, cand_blob, CAND_ADDR, is_locked, cur, new_i)
        assert orig_out == cand_out, f'Mismatch in Shop_SetSelectedItem (locked={is_locked}, cur={cur}, new={new_i})'

    # Mutation sensitivity
    orig_out = run_simulation(image, cand_blob, ORIG_ADDR, 0, 0x10, 0x20)
    mut_out = run_simulation(image, mut_blob, CAND_ADDR, 0, 0x10, 0x20)
    assert orig_out != mut_out, 'Mutation failed to produce difference'
    print('h11_shop_setselecteditem: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 2. h11_shop_checkhasnew_experiment.py
(TOOLS / 'h11_shop_checkhasnew_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0022FC98 Shop_CheckHasNewInventoryItem."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_checkhasnew_candidate.cpp'
ORIG_ADDR = 0x0022FC98
ORIG_SIZE = 48
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'shop_func_0026f0d8': 0x0026F0D8,
    'shop_func_002b902c': 0x002B902C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_checkhasnew.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_checkhasnew_candidate']
    raw_mut, _ = funcs['h11_shop_checkhasnew_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, ret1: int, ret2: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub helper functions: mov r0, #ret; bx lr
    stub1 = struct.pack('<II', 0xE3A00000 | (ret1 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x0026F0D8, stub1)
    stub2 = struct.pack('<II', 0xE3A00000 | (ret2 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x002B902C, stub2)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, 0)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    cases = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for r1, r2 in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, r1, r2)
        cand = run_simulation(image, cand_blob, CAND_ADDR, r1, r2)
        assert orig == cand, f'Mismatch in Shop_CheckHasNew ({r1}, {r2}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 0, 0)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 0, 0)
    assert orig != mut, 'Mutation failed'
    print('h11_shop_checkhasnew: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 3. h11_shop_checkhasspecial_experiment.py
(TOOLS / 'h11_shop_checkhasspecial_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0022FCC8 Shop_CheckHasSpecialStockItem."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_checkhasspecial_candidate.cpp'
ORIG_ADDR = 0x0022FCC8
ORIG_SIZE = 48
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'shop_func_0026f0d8': 0x0026F0D8,
    'shop_func_002b902c': 0x002B902C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_checkhasspecial.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_checkhasspecial_candidate']
    raw_mut, _ = funcs['h11_shop_checkhasspecial_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, ret1: int, ret2: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    stub1 = struct.pack('<II', 0xE3A00000 | (ret1 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x0026F0D8, stub1)
    stub2 = struct.pack('<II', 0xE3A00000 | (ret2 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x002B902C, stub2)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, 0)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    cases = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for r1, r2 in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, r1, r2)
        cand = run_simulation(image, cand_blob, CAND_ADDR, r1, r2)
        assert orig == cand, f'Mismatch in Shop_CheckHasSpecial ({r1}, {r2}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 0, 0)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 0, 0)
    assert orig != mut, 'Mutation failed'
    print('h11_shop_checkhasspecial: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 4. h11_shop_pushitemrecord_experiment.py
(TOOLS / 'h11_shop_pushitemrecord_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00230680 Shop_PushItemRecord."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_pushitemrecord_candidate.cpp'
ORIG_ADDR = 0x00230680
ORIG_SIZE = 108
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_pushitemrecord.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h11_shop_pushitemrecord_candidate']
    raw_mut, _ = funcs['h11_shop_pushitemrecord_mutation']
    return raw_cand, raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, items: list[tuple[int, int, int, int]]) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    BUF_ADDR = 0x08000000
    uc.mem_map(BUF_ADDR, 0x2000, unicorn.UC_PROT_ALL)

    RETURN_ADDR = 0x00100004
    for item_id, f1, f2, f3 in items:
        uc.reg_write(UC_ARM_REG_SP, SP_INIT)
        # Push 5th arg to stack at [sp]
        uc.mem_write(SP_INIT, struct.pack('<I', f3))
        uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
        uc.reg_write(UC_ARM_REG_R0, BUF_ADDR)
        uc.reg_write(UC_ARM_REG_R1, item_id)
        uc.reg_write(UC_ARM_REG_R2, f1)
        uc.reg_write(UC_ARM_REG_R3, f2)
        uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)

    return uc.mem_read(BUF_ADDR, 0x1010)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    items = [
        (0x1234, 1, 0, 0x45),
        (0x5678, 0, 1, 0x7A),
        (0x0ABC, 1, 1, 0xFF),
    ]

    orig_out = run_simulation(image, cand_blob, ORIG_ADDR, items)
    cand_out = run_simulation(image, cand_blob, CAND_ADDR, items)
    assert orig_out == cand_out, 'Mismatch in Shop_PushItemRecord'

    mut_out = run_simulation(image, mut_blob, CAND_ADDR, items)
    assert orig_out != mut_out, 'Mutation failed'
    print('h11_shop_pushitemrecord: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 5. h11_shop_isequipslotmatch_experiment.py
(TOOLS / 'h11_shop_isequipslotmatch_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00230D24 Shop_IsEquipSlotMatch."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_isequipslotmatch_candidate.cpp'
ORIG_ADDR = 0x00230D24
ORIG_SIZE = 140
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_2B66EC': 0x002B66EC,
    'sub_2AE64C': 0x002AE64C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_isequipslotmatch.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_isequipslotmatch_candidate']
    raw_mut, _ = funcs['h11_shop_isequipslotmatch_mutation']

    blob_cand = bytearray(raw_cand)
    RODATA_ADDR = 0x08000500
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
        elif r.relocation_type == 2: # R_ARM_ABS32 to local rodata
            struct.pack_into('<I', blob_cand, r.offset, RODATA_ADDR)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, cat: int, item_id: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    TABLE_ADDR = 0x08000000
    uc.mem_map(TABLE_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    # Equipment table entries at offsets 0, 2, 4, 6, 8, 10, 12:
    # 0: 0x100, 2: 0x200, 4: 0x800 (cat 8), 6: 0x300, 8: 0x400, 10: 0x500, 12: 0x600
    table_data = struct.pack('<HHHHHHH', 0x100, 0x200, 0x800, 0x300, 0x400, 0x500, 0x600)
    uc.mem_write(TABLE_ADDR, table_data)

    # Write local rodata table for candidate
    RODATA_ADDR = 0x08000500
    uc.mem_write(RODATA_ADDR, bytes([0, 2, 6, 8, 10, 12, 4]))

    # Mock sub_2B66EC: return TABLE_ADDR
    stub_b6 = struct.pack('<III', 0xE59F0000, 0xE12FFF1E, TABLE_ADDR) # ldr r0, [pc]; bx lr; .word TABLE_ADDR
    uc.mem_write(0x002B66EC, stub_b6)

    # Mock sub_2AE64C: return cat
    stub_ae = struct.pack('<II', 0xE3A00000 | (cat & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x002AE64C, stub_ae)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, 0)
    uc.reg_write(UC_ARM_REG_R1, item_id)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    cases = [
        (2, 0x100), # cat 2 matches offset 0
        (2, 0x999), # mismatch
        (3, 0x200), # cat 3 matches offset 2
        (4, 0x300), # cat 4 matches offset 6
        (5, 0x400), # cat 5 matches offset 8
        (6, 0x500), # cat 6 matches offset 10
        (7, 0x600), # cat 7 matches offset 12
        (8, 0x800), # cat 8 matches offset 4
        (1, 0x100), # out of range cat
        (9, 0x100), # out of range cat
    ]

    for cat, item_id in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, cat, item_id)
        cand = run_simulation(image, cand_blob, CAND_ADDR, cat, item_id)
        assert orig == cand, f'Mismatch in Shop_IsEquipSlotMatch (cat={cat}, id={item_id}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 2, 0x100)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 2, 0x100)
    assert orig != mut, 'Mutation failed'
    print('h11_shop_isequipslotmatch: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 6. h11_shop_calcpurchasableqty_experiment.py
(TOOLS / 'h11_shop_calcpurchasableqty_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00230DB0 Shop_CalcPurchasableQty."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_shop_calcpurchasableqty_candidate.cpp'
ORIG_ADDR = 0x00230DB0
ORIG_SIZE = 100
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_22EBBC': 0x0022EBBC,
    'sub_2C615C': 0x002C615C,
    'sub_2B9100': 0x002B9100,
    'sub_28FDE4': 0x0028FDE4,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_shop_calcpurchasableqty.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_calcpurchasableqty_candidate']
    raw_mut, _ = funcs['h11_shop_calcpurchasableqty_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, stock: int, max_bag: int, cur_bag: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Mock sub_22EBBC -> returns 0
    uc.mem_write(0x0022EBBC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # Mock sub_2C615C -> returns stock
    uc.mem_write(0x002C615C, struct.pack('<III', 0xE59F0000, 0xE12FFF1E, stock & 0xFFFFFFFF))
    # Mock sub_2B9100 -> returns max_bag
    uc.mem_write(0x002B9100, struct.pack('<III', 0xE59F0000, 0xE12FFF1E, max_bag & 0xFFFFFFFF))
    # Mock sub_28FDE4 -> returns cur_bag
    uc.mem_write(0x0028FDE4, struct.pack('<III', 0xE59F0000, 0xE12FFF1E, cur_bag & 0xFFFFFFFF))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, 0x08000000)
    uc.reg_write(UC_ARM_REG_R1, 0x10)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    val = uc.reg_read(UC_ARM_REG_R0)
    if val >= 0x80000000:
        val -= 0x100000000
    return val

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    cases = [
        (10, 50, 20),  # stock 10, remaining 30 -> 10
        (40, 50, 20),  # stock 40, remaining 30 -> 30
        (150, 50, 20), # stock 150 clamped to 99, remaining 30 -> 30
        (-5, 50, 20),  # stock -5 -> 0
        (10, 50, 55),  # stock 10, remaining -5 -> -5 or 0
    ]

    for stock, m_bag, c_bag in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, stock, m_bag, c_bag)
        cand = run_simulation(image, cand_blob, CAND_ADDR, stock, m_bag, c_bag)
        assert orig == cand, f'Mismatch in Shop_CalcPurchasableQty ({stock}, {m_bag}, {c_bag}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 10, 50, 20)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 10, 50, 20)
    assert orig != mut, 'Mutation failed'
    print('h11_shop_calcpurchasableqty: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 7. h11_terminal_setunlockflag_experiment.py
(TOOLS / 'h11_terminal_setunlockflag_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00263734 Terminal_SetUnlockFlag."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_terminal_setunlockflag_candidate.cpp'
ORIG_ADDR = 0x00263734
ORIG_SIZE = 68
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_2BBD40': 0x002BBD40,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_terminal_setunlockflag.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_terminal_setunlockflag_candidate']
    raw_mut, _ = funcs['h11_terminal_setunlockflag_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, initial_bits: bytes, ops: list[tuple[int, int]]) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(WORK_ADDR + 8, initial_bits)

    # Mock sub_2BBD40 -> return WORK_ADDR
    stub = struct.pack('<III', 0xE59F0000, 0xE12FFF1E, WORK_ADDR)
    uc.mem_write(0x002BBD40, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    for term_id, state in ops:
        uc.reg_write(UC_ARM_REG_SP, SP_INIT)
        uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
        uc.reg_write(UC_ARM_REG_R0, term_id)
        uc.reg_write(UC_ARM_REG_R1, state)
        uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)

    return uc.mem_read(WORK_ADDR + 8, 4)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    init_b = b'\\x00\\x00\\x00\\x00'
    ops = [
        (0, 1),
        (7, 1),
        (18, 1),
        (7, 0),
        (35, 1), # out of bounds
    ]

    orig_out = run_simulation(image, cand_blob, ORIG_ADDR, init_b, ops)
    cand_out = run_simulation(image, cand_blob, CAND_ADDR, init_b, ops)
    assert orig_out == cand_out, f'Mismatch in Terminal_SetUnlockFlag: {orig_out.hex()} != {cand_out.hex()}'

    mut_out = run_simulation(image, mut_blob, CAND_ADDR, init_b, ops)
    assert orig_out != mut_out, 'Mutation failed'
    print('h11_terminal_setunlockflag: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 8. h11_terminal_isunlocked_experiment.py
(TOOLS / 'h11_terminal_isunlocked_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00263778 Terminal_IsUnlocked."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h11_terminal_isunlocked_candidate.cpp'
ORIG_ADDR = 0x00263778
ORIG_SIZE = 60
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_2BBD40': 0x002BBD40,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h11_terminal_isunlocked.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_terminal_isunlocked_candidate']
    raw_mut, _ = funcs['h11_terminal_isunlocked_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, bitset: bytes, term_id: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(WORK_ADDR + 8, bitset)

    stub = struct.pack('<III', 0xE59F0000, 0xE12FFF1E, WORK_ADDR)
    uc.mem_write(0x002BBD40, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, term_id)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    with open(CODE_PATH, 'rb') as f:
        image = f.read()

    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h11_differential')

    bitset = bytes([0x81, 0x04, 0x00, 0x80])
    # Bit 0 (1), bit 7 (1), bit 10 (1), bit 31 (1)

    queries = [0, 1, 7, 10, 11, 31, 32, 50]
    for q in queries:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, bitset, q)
        cand = run_simulation(image, cand_blob, CAND_ADDR, bitset, q)
        assert orig == cand, f'Mismatch in Terminal_IsUnlocked ({q}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, bitset, 0)
    mut = run_simulation(image, mut_blob, CAND_ADDR, bitset, 0)
    assert orig != mut, 'Mutation failed'
    print('h11_terminal_isunlocked: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

EXPERIMENTS = [
    'h11_shop_setselecteditem_experiment.py',
    'h11_shop_checkhasnew_experiment.py',
    'h11_shop_checkhasspecial_experiment.py',
    'h11_shop_pushitemrecord_experiment.py',
    'h11_shop_isequipslotmatch_experiment.py',
    'h11_shop_calcpurchasableqty_experiment.py',
    'h11_terminal_setunlockflag_experiment.py',
    'h11_terminal_isunlocked_experiment.py',
]

print("=== Executing all 8 Milestone H11 Unicorn Differential Experiments ===")
all_passed = True
for exp in EXPERIMENTS:
    exp_path = TOOLS / exp
    res = subprocess.run([sys.executable, str(exp_path)], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[PASSED] {exp:<42} : {res.stdout.strip()}")
    else:
        print(f"[FAILED] {exp:<42} : {res.stderr.strip()}")
        all_passed = False

if not all_passed:
    sys.exit(1)
print("\nALL 8 MILESTONE H11 EXPERIMENTS PASSED DIFFERENTIAL VALIDATION WITH 100% PARITY!")
