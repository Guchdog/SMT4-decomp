#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H18."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h18_h10_burroughs_experiment.py
(TOOLS / 'h18_h10_burroughs_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for H10 Burroughs promoted module (0x002A0FAC)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h10_burroughs_promoted.cpp'
ORIG_ADDR = 0x002A0FAC
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_GameWork_0043e2a8': 0x0043E2A8,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_burroughs_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h10_camp_burroughs_getsavedata_promoted']
    raw_mut, relocs_mut = funcs['h10_camp_burroughs_getsavedata_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)

    blob_mut = bytearray(raw_mut)
    for r in relocs_mut:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_mut, r.offset, tgt)

    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, save_ptr: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # Write save_data pointer at g_GameWork_0043e2a8.save_data (offset +4)
    uc.mem_write(0x0043E2AC, struct.pack('<I', save_ptr))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [0x08000000, 0x08100000, 0x0FFF0000]
    for ptr in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, ptr)
        cand = run_simulation(code, cand_blob, CAND_ADDR, ptr)
        mut = run_simulation(code, mut_blob, CAND_ADDR, ptr)
        assert orig == cand, f'Mismatch for ptr {hex(ptr)}: orig={hex(orig)}, cand={hex(cand)}'
        assert orig != mut, f'Mutation undetected for {hex(ptr)}'

    print('[PASS] H18 Burroughs Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 2. h18_h11_shops_experiment.py
(TOOLS / 'h18_h11_shops_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for H11 Shops promoted module (0x0022FC98)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h11_shops_promoted.cpp'
ORIG_ADDR = 0x0022FC98
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
    obj_path = out_dir / 'h11_shops_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h11_shop_checkhasnew_promoted']
    raw_mut, relocs_mut = funcs['h11_shop_checkhasnew_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)

    blob_mut = bytearray(raw_mut)
    for r in relocs_mut:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_mut, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob_mut, r.offset, tgt)

    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, ret_f6: int, ret_f7: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # Stub 0x0026F0D8: mov r0, #ret_f6; bx lr
    stub_f6 = struct.pack('<II', 0xE3A00000 | (ret_f6 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x0026F0D8, stub_f6)

    # Stub 0x002B902C: mov r0, #ret_f7; bx lr
    stub_f7 = struct.pack('<II', 0xE3A00000 | (ret_f7 & 0xFF), 0xE12FFF1E)
    uc.mem_write(0x002B902C, stub_f7)

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [(0, 0), (1, 0), (0, 1), (1, 1)]
    for f6, f7 in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, f6, f7)
        cand = run_simulation(code, cand_blob, CAND_ADDR, f6, f7)
        mut = run_simulation(code, mut_blob, CAND_ADDR, f6, f7)
        assert orig == cand, f'Mismatch for ({f6}, {f7}): orig={orig}, cand={cand}'
        assert orig != mut, f'Mutation undetected for ({f6}, {f7})'

    print('[PASS] H18 Shops Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 3. h18_h12_combat_experiment.py
(TOOLS / 'h18_h12_combat_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for H12 Combat promoted module (0x00129C58)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h12_combat_promoted.cpp'
ORIG_ADDR = 0x00129C58
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleSmirkWork_00471a70': 0x00471A70,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_combat_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_getunitsmirkstate_promoted']
    raw_mut, relocs_mut = funcs['h12_battle_getunitsmirkstate_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)

    blob_mut = bytearray(raw_mut)
    for r in relocs_mut:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_mut, r.offset, tgt)

    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, smirk_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    SUB_BUF = 0x08002000
    uc.mem_write(0x00471A70 + 0x1C, struct.pack('<I', SUB_BUF))
    uc.mem_write(SUB_BUF + 0x75, struct.pack('b', smirk_val))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    res = uc.reg_read(UC_ARM_REG_R0)
    if res >= 0x80000000:
        res -= 0x100000000
    return res

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [0, 1, -1, 5, -128, 127]
    for val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, val)
        assert orig == cand, f'Mismatch for smirk {val}: orig={orig}, cand={cand}'
        assert orig != mut, f'Mutation undetected for {val}'

    print('[PASS] H18 Combat Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 4. h18_h13_exploration_experiment.py
(TOOLS / 'h18_h13_exploration_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for H13 Exploration promoted module (0x0026394C)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h13_exploration_promoted.cpp'
ORIG_ADDR = 0x0026394C
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_exploration_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_placewin_isactive_promoted']
    raw_mut, relocs_mut = funcs['h13_placewin_isactive_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, has_timer: bool, elapsed: float, duration: float) -> int:
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

    HOLDER_ADDR = 0x0FFF2000
    TIMER_ADDR = 0x0FFF3000

    if has_timer:
        uc.mem_write(HOLDER_ADDR + 4, struct.pack('<I', TIMER_ADDR))
        uc.mem_write(TIMER_ADDR + 0x38, struct.pack('<f', duration))
        uc.mem_write(TIMER_ADDR + 0x48, struct.pack('<f', elapsed))
    else:
        uc.mem_write(HOLDER_ADDR + 4, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, HOLDER_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [
        (False, 0.0, 0.0),
        (True, 1.0, 2.0),
        (True, 2.0, 2.0),
        (True, 3.0, 2.0),
    ]
    for has_timer, elapsed, duration in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, has_timer, elapsed, duration)
        cand = run_simulation(code, cand_blob, CAND_ADDR, has_timer, elapsed, duration)
        mut = run_simulation(code, mut_blob, CAND_ADDR, has_timer, elapsed, duration)
        assert orig == cand, f'Mismatch for ({has_timer}, {elapsed}, {duration}): orig={orig}, cand={cand}'
        if orig != 0:
            assert orig != mut, f'Mutation undetected'

    print('[PASS] H18 Exploration Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 5. h18_h14_graphics_experiment.py
(TOOLS / 'h18_h14_graphics_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for H14 Graphics promoted module (0x002C3B88)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h14_graphics_promoted.cpp'
ORIG_ADDR = 0x002C3B88
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdGpuWork_00471b48': 0x00471B48,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_graphics_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdgpu_heapsize_promoted']
    raw_mut, relocs_mut = funcs['h14_asdgpu_heapsize_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)

    blob_mut = bytearray(raw_mut)
    for r in relocs_mut:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_mut, r.offset, tgt)

    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, heap_size: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.mem_write(0x00471B48 + 4, struct.pack('<I', heap_size))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [0x1000000, 0x2000000, 0x400000]
    for val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, val)
        assert orig == cand, f'Mismatch for {hex(val)}: orig={hex(orig)}, cand={hex(cand)}'
        assert orig != mut, f'Mutation undetected for {hex(val)}'

    print('[PASS] H18 Graphics Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 6. h18_h15_ui_experiment.py
(TOOLS / 'h18_h15_ui_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for H15 UI promoted module (0x00126084)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h15_ui_promoted.cpp'
ORIG_ADDR = 0x00126084
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_2C0AC8': 0x002C0AC8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h15_ui_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uidialog_getstate_promoted']
    raw_mut, relocs_mut = funcs['h15_uidialog_getstate_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)

    blob_mut = bytearray(raw_mut)
    for r in relocs_mut:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_mut, r.offset, w)
            elif r.relocation_type == 2:
                struct.pack_into('<I', blob_mut, r.offset, tgt)

    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, state_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    TARGET_BUF = 0x0FFF3000
    uc.mem_write(TARGET_BUF + 0x8C, struct.pack('b', state_val))

    # Stub sub_2C0AC8: ldr r0, =0x0FFF3000; bx lr
    stub_fn = struct.pack('<III', 0xE59F0000, 0xE12FFF1E, TARGET_BUF)
    uc.mem_write(0x002C0AC8, stub_fn)

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    res = uc.reg_read(UC_ARM_REG_R0)
    if res >= 0x80:
        res -= 0x100
    return res

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [0, 1, 2, 5, 0x7F]
    for val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, val)
        assert orig == cand, f'Mismatch for state {val}: orig={orig}, cand={cand}'
        assert orig != mut, f'Mutation undetected for {val}'

    print('[PASS] H18 UI Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 7. h18_h16_sound_experiment.py
(TOOLS / 'h18_h16_sound_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for H16 Sound promoted module (0x00110C44)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h16_sound_promoted.cpp'
ORIG_ADDR = 0x00110C44
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_sound_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h16_asdsoundeffect_getbuffersize_promoted']
    raw_mut, relocs_mut = funcs['h16_asdsoundeffect_getbuffersize_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, rate: int, channels: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    CONFIG_ADDR = 0x0FFF2000
    uc.mem_write(CONFIG_ADDR + 0x44, struct.pack('<I', rate))
    uc.mem_write(CONFIG_ADDR + 0x5D, struct.pack('B', channels))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, CONFIG_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [(32000, 2), (44100, 1), (16000, 2), (22050, 1)]
    for r, c in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, r, c)
        cand = run_simulation(code, cand_blob, CAND_ADDR, r, c)
        mut = run_simulation(code, mut_blob, CAND_ADDR, r, c)
        assert orig == cand, f'Mismatch for ({r}, {c}): orig={orig}, cand={cand}'
        assert orig != mut, f'Mutation undetected for ({r}, {c})'

    print('[PASS] H18 Sound Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 8. h18_h17_cec_aoc_experiment.py
(TOOLS / 'h18_h17_cec_aoc_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for H17 CEC & AOC promoted module (0x002A17C0)."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'src/semantic/h17_cec_aoc_promoted.cpp'
ORIG_ADDR = 0x002A17C0
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_cec_aoc_promoted.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h17_aoc_resultisready_promoted']
    raw_mut, relocs_mut = funcs['h17_aoc_resultisready_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, byte_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    TARGET_BYTE_ADDR = 0x0FFF2000
    uc.mem_write(TARGET_BYTE_ADDR, bytes([byte_val]))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, TARGET_BYTE_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h18_tests')

    cases = [0, 50, 99, 100, 101, 200, 255]
    for b in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, b)
        cand = run_simulation(code, cand_blob, CAND_ADDR, b)
        mut = run_simulation(code, mut_blob, CAND_ADDR, b)
        assert orig == cand, f'Mismatch for byte {b}: orig={orig}, cand={cand}'
        assert orig != mut, f'Mutation undetected for byte {b}'

    print('[PASS] H18 CEC & AOC Promoted Module: 100% parity across vectors, mutations detected.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

def main():
    print("=== Running all 8 Milestone H18 Promoted Module Differential Experiments ===")
    scripts = [
        'h18_h10_burroughs_experiment.py',
        'h18_h11_shops_experiment.py',
        'h18_h12_combat_experiment.py',
        'h18_h13_exploration_experiment.py',
        'h18_h14_graphics_experiment.py',
        'h18_h15_ui_experiment.py',
        'h18_h16_sound_experiment.py',
        'h18_h17_cec_aoc_experiment.py',
    ]
    for s in scripts:
        res = subprocess.run([sys.executable, str(TOOLS / s)], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[FAIL] {s}:\n{res.stderr}\n{res.stdout}")
            sys.exit(1)
        else:
            print(res.stdout.strip())
    print("\nALL 8 PROMOTED MODULE DIFFERENTIAL EXPERIMENTS PASSED WITH 100% PARITY!")

if __name__ == '__main__':
    main()
