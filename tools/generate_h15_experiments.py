#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H15."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h15_uitext_setcodefield10_experiment.py
(TOOLS / 'h15_uitext_setcodefield10_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0010E570 UiText_SetCodeField10."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uitext_setcodefield10_candidate.cpp'
ORIG_ADDR = 0x0010E570
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_UiTextCode_00464d48': 0x00464D48,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h15_uitext_setcodefield10.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uitext_setcodefield10_candidate']
    raw_mut, relocs_mut = funcs['h15_uitext_setcodefield10_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.mem_write(0x00464D48 + 0x10, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return struct.unpack('<I', uc.mem_read(0x00464D48 + 0x10, 4))[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    vals = [0, 0x10, 0x55AA55AA, 0xFFFFFFFF]
    for v in vals:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)

        if orig != cand or cand != v:
            raise AssertionError(f'Mismatch for v=0x{v:08X}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for v=0x{v:08X}')

    print(f'[PASS] h15_uitext_setcodefield10: 100% parity across {len(vals)} values, field store confirmed.')

if __name__ == '__main__':
    main()
''')

# 2. h15_uitext_setcodefield28_experiment.py
(TOOLS / 'h15_uitext_setcodefield28_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0010E5BC UiText_SetCodeField28."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uitext_setcodefield28_candidate.cpp'
ORIG_ADDR = 0x0010E5BC
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_UiTextCode_00464d48': 0x00464D48,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h15_uitext_setcodefield28.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uitext_setcodefield28_candidate']
    raw_mut, relocs_mut = funcs['h15_uitext_setcodefield28_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.mem_write(0x00464D48 + 0x28, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return struct.unpack('<I', uc.mem_read(0x00464D48 + 0x28, 4))[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    vals = [0, 0x28, 0xABCDEF01, 0xFFFFFFFF]
    for v in vals:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)

        if orig != cand or cand != v:
            raise AssertionError(f'Mismatch for v=0x{v:08X}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for v=0x{v:08X}')

    print(f'[PASS] h15_uitext_setcodefield28: 100% parity across {len(vals)} values, field store confirmed.')

if __name__ == '__main__':
    main()
''')

# 3. h15_uidialog_getstate_experiment.py
(TOOLS / 'h15_uidialog_getstate_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00126084 UiDialog_GetState."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uidialog_getstate_candidate.cpp'
ORIG_ADDR = 0x00126084
ORIG_SIZE = 16
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
    obj_path = out_dir / 'h15_uidialog_getstate.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uidialog_getstate_candidate']
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

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)
    CTX_BUF = MEM_BASE + 0x1000
    uc.mem_write(CTX_BUF + 0x8C, struct.pack('<b', state_val))

    # Stub sub_2C0AC8: returns CTX_BUF in r0
    # ldr r0, =CTX_BUF; bx lr
    stub = struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CTX_BUF)
    uc.mem_write(0x002C0AC8, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    ret = uc.reg_read(UC_ARM_REG_R0)
    if ret >= 0x80000000:
        ret -= 0x100000000
    return ret

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    vals = [0, 1, 42, -1, -50]
    for v in vals:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)

        if orig != cand or cand != v:
            raise AssertionError(f'Mismatch for v={v}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for v={v}')

    print(f'[PASS] h15_uidialog_getstate: 100% parity across {len(vals)} states, sign-extension verified.')

if __name__ == '__main__':
    main()
''')

# 4. h15_uidialog_getflags_experiment.py
(TOOLS / 'h15_uidialog_getflags_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001260A8 UiDialog_GetFlags."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uidialog_getflags_candidate.cpp'
ORIG_ADDR = 0x001260A8
ORIG_SIZE = 16
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
    obj_path = out_dir / 'h15_uidialog_getflags.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uidialog_getflags_candidate']
    raw_mut, relocs_mut = funcs['h15_uidialog_getflags_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, flags_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)
    CTX_BUF = MEM_BASE + 0x1000
    uc.mem_write(CTX_BUF, struct.pack('<I', flags_val))

    # Stub sub_2C0AC8
    stub = struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CTX_BUF)
    uc.mem_write(0x002C0AC8, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    flags = [0, 1, 0x80000000, 0x12345678, 0xFFFFFFFF]
    for flg in flags:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, flg)
        cand = run_simulation(code, cand_blob, CAND_ADDR, flg)
        mut = run_simulation(code, mut_blob, CAND_ADDR, flg)

        if orig != cand or cand != flg:
            raise AssertionError(f'Mismatch for flg=0x{flg:08X}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for flg=0x{flg:08X}')

    print(f'[PASS] h15_uidialog_getflags: 100% parity across {len(flags)} flag masks, word read verified.')

if __name__ == '__main__':
    main()
''')

# 5. h15_uidialog_getcursorindex_experiment.py
(TOOLS / 'h15_uidialog_getcursorindex_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00126220 UiDialog_GetCursorIndex."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uidialog_getcursorindex_candidate.cpp'
ORIG_ADDR = 0x00126220
ORIG_SIZE = 16
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
    obj_path = out_dir / 'h15_uidialog_getcursorindex.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uidialog_getcursorindex_candidate']
    raw_mut, relocs_mut = funcs['h15_uidialog_getcursorindex_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, cursor_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)
    CTX_BUF = MEM_BASE + 0x1000
    uc.mem_write(CTX_BUF + 0x94, struct.pack('<b', cursor_val))

    # Stub sub_2C0AC8
    stub = struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CTX_BUF)
    uc.mem_write(0x002C0AC8, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    ret = uc.reg_read(UC_ARM_REG_R0)
    if ret >= 0x80000000:
        ret -= 0x100000000
    return ret

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    vals = [0, 1, 2, 3, -1]
    for v in vals:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)

        if orig != cand or cand != v:
            raise AssertionError(f'Mismatch for v={v}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for v={v}')

    print(f'[PASS] h15_uidialog_getcursorindex: 100% parity across {len(vals)} cursor values, signed index verified.')

if __name__ == '__main__':
    main()
''')

# 6. h15_uitext_getdrawcoordx_experiment.py
(TOOLS / 'h15_uitext_getdrawcoordx_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00126628 UiText_GetDrawCoordX."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uitext_getdrawcoordx_candidate.cpp'
ORIG_ADDR = 0x00126628
ORIG_SIZE = 16
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
    obj_path = out_dir / 'h15_uitext_getdrawcoordx.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uitext_getdrawcoordx_candidate']
    raw_mut, relocs_mut = funcs['h15_uitext_getdrawcoordx_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, coord_x: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)
    CTX_BUF = MEM_BASE + 0x1000
    uc.mem_write(CTX_BUF + 0x38, struct.pack('<I', coord_x))

    # Stub sub_2C0AC8
    stub = struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CTX_BUF)
    uc.mem_write(0x002C0AC8, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    coords = [0, 100, 320, 400]
    for c in coords:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, c)
        cand = run_simulation(code, cand_blob, CAND_ADDR, c)
        mut = run_simulation(code, mut_blob, CAND_ADDR, c)

        if orig != cand or cand != c:
            raise AssertionError(f'Mismatch for c={c}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for c={c}')

    print(f'[PASS] h15_uitext_getdrawcoordx: 100% parity across {len(coords)} coordinates, X load verified.')

if __name__ == '__main__':
    main()
''')

# 7. h15_uitext_getdrawcoordy_experiment.py
(TOOLS / 'h15_uitext_getdrawcoordy_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00126638 UiText_GetDrawCoordY."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uitext_getdrawcoordy_candidate.cpp'
ORIG_ADDR = 0x00126638
ORIG_SIZE = 16
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
    obj_path = out_dir / 'h15_uitext_getdrawcoordy.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uitext_getdrawcoordy_candidate']
    raw_mut, relocs_mut = funcs['h15_uitext_getdrawcoordy_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, coord_y: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)
    CTX_BUF = MEM_BASE + 0x1000
    uc.mem_write(CTX_BUF + 0x3C, struct.pack('<I', coord_y))

    # Stub sub_2C0AC8
    stub = struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CTX_BUF)
    uc.mem_write(0x002C0AC8, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    coords = [0, 50, 240, 480]
    for c in coords:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, c)
        cand = run_simulation(code, cand_blob, CAND_ADDR, c)
        mut = run_simulation(code, mut_blob, CAND_ADDR, c)

        if orig != cand or cand != c:
            raise AssertionError(f'Mismatch for c={c}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for c={c}')

    print(f'[PASS] h15_uitext_getdrawcoordy: 100% parity across {len(coords)} coordinates, Y load verified.')

if __name__ == '__main__':
    main()
''')

# 8. h15_uimanager_getcontexthandle_experiment.py
(TOOLS / 'h15_uimanager_getcontexthandle_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026B844 UiManager_GetContextHandle."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h15_uimanager_getcontexthandle_candidate.cpp'
ORIG_ADDR = 0x0026B844
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_UiContextManager_0043e2a8': 0x0043E2A8,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h15_uimanager_getcontexthandle.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h15_uimanager_getcontexthandle_candidate']
    raw_mut, relocs_mut = funcs['h15_uimanager_getcontexthandle_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, handle_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # 0x0043E2A8 + 4 = handle
    uc.mem_write(0x0043E2A8 + 4, struct.pack('<I', handle_val))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h15_tests')

    handles = [0, 1, 0x778899AA, 0xFFFFFFFF]
    for h in handles:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, h)
        cand = run_simulation(code, cand_blob, CAND_ADDR, h)
        mut = run_simulation(code, mut_blob, CAND_ADDR, h)

        if orig != cand or cand != h:
            raise AssertionError(f'Mismatch for h=0x{h:08X}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for h=0x{h:08X}')

    print(f'[PASS] h15_uimanager_getcontexthandle: 100% parity across {len(handles)} handles, handle read verified.')

if __name__ == '__main__':
    main()
''')

# Execute all 8 scripts
scripts = [
    'h15_uitext_setcodefield10_experiment.py',
    'h15_uitext_setcodefield28_experiment.py',
    'h15_uidialog_getstate_experiment.py',
    'h15_uidialog_getflags_experiment.py',
    'h15_uidialog_getcursorindex_experiment.py',
    'h15_uitext_getdrawcoordx_experiment.py',
    'h15_uitext_getdrawcoordy_experiment.py',
    'h15_uimanager_getcontexthandle_experiment.py',
]

print('=== Executing all 8 Unicorn differential validation experiments for Milestone H15 ===')
for s in scripts:
    res = subprocess.run([sys.executable, str(TOOLS / s)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f'FAIL in {s}:')
        print(res.stdout)
        print(res.stderr)
        sys.exit(1)
    else:
        print(res.stdout.strip())

print('=== ALL 8 H15 DIFFERENTIAL EXPERIMENTS PASSED WITH 100% PARITY! ===')
