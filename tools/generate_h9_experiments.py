#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H9."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h9_camp_uniteeffect_init_experiment.py
(TOOLS / 'h9_camp_uniteeffect_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002E315C UniteEffect_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_uniteeffect_init_candidate.cpp'
ORIG_ADDR = 0x002E315C
ORIG_SIZE = 344
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'engine_func_002c0ba8': 0x002C0BA8,
    'engine_func_002976ac': 0x002976AC,
    'g_UniteEffectWork_0043dd90': 0x0043DD90,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_uniteeffect_init.o'
    cmd = [
        r'C:\\msys64\\clang64\\bin\\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\\msys64\\clang64\\lib\\clang\\23\\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h9_camp_uniteeffect_init_candidate']
    raw_mut, _ = funcs['h9_camp_uniteeffect_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x0043DD90, b'\\x00' * 4)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002100))
    uc.mem_write(0x002C0BA8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002976AC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    ptr = uc.mem_read(0x0043DD90, 4)
    return struct.unpack('<I', ptr)[0], bytes(ptr)

def main():
    out_dir = ROOT / 'build/h9_experiments/uniteeff'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 UniteEffect_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 2. h9_camp_biblemain_init_experiment.py
(TOOLS / 'h9_camp_biblemain_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00269CC8 bibleMain_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_biblemain_init_candidate.cpp'
ORIG_ADDR = 0x00269CC8
ORIG_SIZE = 352
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'g_BibleMainWork_0043da10': 0x0043DA10,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_biblemain_init.o'
    cmd = [
        r'C:\\msys64\\clang64\\bin\\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\\msys64\\clang64\\lib\\clang\\23\\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h9_camp_biblemain_init_candidate']
    raw_mut, _ = funcs['h9_camp_biblemain_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x0043DA10, b'\\x00' * 4)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002100))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    ptr = uc.mem_read(0x0043DA10, 4)
    work = uc.mem_read(WORK_ADDR, 0x18)
    return struct.unpack('<I', ptr)[0], bytes(work)

def main():
    out_dir = ROOT / 'build/h9_experiments/biblemain'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 bibleMain_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 3. h9_camp_biblelegionskill_init_experiment.py
(TOOLS / 'h9_camp_biblelegionskill_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003AB770 bibleLegionSkill_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_biblelegionskill_init_candidate.cpp'
ORIG_ADDR = 0x003AB770
ORIG_SIZE = 592
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'unite_func_00232800': 0x00232800,
    'unite_func_00233600': 0x00233600,
    'shop_func_002333d4': 0x002333D4,
    'engine_func_002c23f8': 0x002C23F8,
    'unite_func_002333bc': 0x002333BC,
    'unite_func_003ab0d0': 0x003AB0D0,
    'unite_func_00233804': 0x00233804,
    'camp_func_0029f10c': 0x0029F10C,
    'bibleLegionDraw_func_003ad300': 0x003AD300,
    'g_BibleLegionSkillHandle_0043d9f8': 0x0043D9F8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_biblelegionskill_init.o'
    cmd = [
        r'C:\\msys64\\clang64\\bin\\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\\msys64\\clang64\\lib\\clang\\23\\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h9_camp_biblelegionskill_init_candidate']
    raw_mut, _ = funcs['h9_camp_biblelegionskill_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    WORK_STRUCT = 0x08000000
    uc.mem_map(WORK_STRUCT, 0x20000, unicorn.UC_PROT_ALL)
    uc.mem_write(WORK_STRUCT, b'\\x00' * 0x10000)
    VTBL = 0x08010000
    uc.mem_write(VTBL, struct.pack('<16I', *[0x00100004]*16))
    uc.mem_write(WORK_STRUCT, struct.pack('<I', VTBL))

    HANDLE_ADDR = 0x0043D9F8
    uc.mem_write(HANDLE_ADDR, b'\\x00' * 4)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08005000))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002100))
    uc.mem_write(0x00232800, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00233600, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002333D4, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C23F8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08006000))
    uc.mem_write(0x002333BC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x003AB0D0, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00233804, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0029F10C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x003AD300, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, WORK_STRUCT)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    handle_val = uc.mem_read(HANDLE_ADDR, 4)
    work_val = uc.mem_read(WORK_STRUCT, 0x20)
    return struct.unpack('<I', handle_val)[0], bytes(work_val)

def main():
    out_dir = ROOT / 'build/h9_experiments/legionskill'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 bibleLegionSkill_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 4. h9_camp_biblelegiondraw_init_experiment.py
(TOOLS / 'h9_camp_biblelegiondraw_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003AD300 bibleLegionDraw_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_biblelegiondraw_init_candidate.cpp'
ORIG_ADDR = 0x003AD300
ORIG_SIZE = 596
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdTask_Create_002c5978': 0x002C5978,
    'UiSpriteGroup_Init_002c3344': 0x002C3344,
    'UiSpriteGroup_BindTable_002c32f8': 0x002C32F8,
    'camp_func_002bdb2c': 0x002BDB2C,
    'battle_func_002af854': 0x002AF854,
    'g_BibleLegionDrawManager_0043d9e0': 0x0043D9E0,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_biblelegiondraw_init.o'
    cmd = [
        r'C:\\msys64\\clang64\\bin\\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\\msys64\\clang64\\lib\\clang\\23\\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h9_camp_biblelegiondraw_init_candidate']
    raw_mut, _ = funcs['h9_camp_biblelegiondraw_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    MGR_ADDR = 0x0043D9E0
    uc.mem_write(MGR_ADDR, b'\\x00' * 8)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C3344, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C32F8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDB2C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002AF854, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    mgr_val = uc.mem_read(MGR_ADDR, 8)
    work_val = uc.mem_read(WORK_ADDR, 0x24)
    return struct.unpack('<I', mgr_val[:4])[0], bytes(mgr_val + work_val)

def main():
    out_dir = ROOT / 'build/h9_experiments/legiondraw'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 bibleLegionDraw_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 5. h9_camp_sortmenu_init_experiment.py
(TOOLS / 'h9_camp_sortmenu_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0029E63C SortMenu_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_sortmenu_init_candidate.cpp'
ORIG_ADDR = 0x0029E63C
ORIG_SIZE = 644
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'UiSpriteGroup_Init_002c3344': 0x002C3344,
    'UiSpriteGroup_BindTable_002c32f8': 0x002C32F8,
    'UiAnimSprite_SetupEx_002bdb2c': 0x002BDB2C,
    'UiAnimSprite_SetMode_002bdac0': 0x002BDAC0,
    'g_SortMenuManager_0043dd20': 0x0043DD20,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_sortmenu_init.o'
    cmd = [
        r'C:\\msys64\\clang64\\bin\\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\\msys64\\clang64\\lib\\clang\\23\\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h9_camp_sortmenu_init_candidate']
    raw_mut, _ = funcs['h9_camp_sortmenu_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    MGR_ADDR = 0x0043DD20
    uc.mem_write(MGR_ADDR, b'\\x00' * 8)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002100))

    for a in [0x002C3344, 0x002C32F8, 0x002BDB2C, 0x002AF854, 0x002BF030, 0x002BDAC0, 0x002C4450]:
        uc.mem_write(a, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, 1)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    mgr_val = uc.mem_read(MGR_ADDR, 8)
    work_val = uc.mem_read(WORK_ADDR, 0x20)
    return struct.unpack('<I', mgr_val[:4])[0], bytes(mgr_val + work_val)

def main():
    out_dir = ROOT / 'build/h9_experiments/sortmenu'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 SortMenu_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 6. h9_camp_unitectrl_roster_experiment.py
(TOOLS / 'h9_camp_unitectrl_roster_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003C9EBC UniteCtrl_RosterPopulate."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_unitectrl_roster_candidate.cpp'
ORIG_ADDR = 0x003C9EBC
ORIG_SIZE = 664
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'ui_Tbb_GetGlobalSubTable_001b9a90': 0x001B9A90,
    'ui_Tbb_GetRowCount_001b9aa4': 0x001B9AA4,
    'Battle_GetTalkEntry_00215fa8': 0x00215FA8,
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'qsort_002b7f0a': 0x002B7F0A,
    'g_UniteCtrlRoster_0043dd40': 0x0043DD40,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_unitectrl_roster.o'
    cmd = [
        r'C:\\msys64\\clang64\\bin\\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\\msys64\\clang64\\lib\\clang\\23\\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h9_camp_unitectrl_roster_candidate']
    raw_mut, _ = funcs['h9_camp_unitectrl_roster_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    ROSTER_ADDR = 0x08000000
    uc.mem_map(ROSTER_ADDR, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(ROSTER_ADDR, b'\\x00' * 0x200)

    # Mock helpers
    uc.mem_write(0x001B9A90, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08005000))
    uc.mem_write(0x001B9AC4, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x001B9AA4, struct.pack('<II', 0xE3A00000, 0xE12FFF1E)) # 0 rows initially for simple test
    uc.mem_write(0x00215FA8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08006000))
    uc.mem_write(0x08006000, struct.pack('<HBBI', 0x12, 1, 2, 1))

    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08007000))
    uc.mem_write(0x002B7F0A, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, ROSTER_ADDR)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    counts = uc.mem_read(ROSTER_ADDR, 0x38)
    return struct.unpack('<I', counts[:4])[0], bytes(counts)

def main():
    out_dir = ROOT / 'build/h9_experiments/unitectrl'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 UniteCtrl_RosterPopulate: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 7. h9_camp_bibledevil_init_experiment.py
(TOOLS / 'h9_camp_bibledevil_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003A7AD8 bibleDevil_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_bibledevil_init_candidate.cpp'
ORIG_ADDR = 0x003A7AD8
ORIG_SIZE = 668
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'unite_func_00232800': 0x00232800,
    'engine_func_002c23f8': 0x002C23F8,
    'unite_func_002333bc': 0x002333BC,
    'unite_func_0022d5c8': 0x0022D5C8,
    'unite_func_003aad60': 0x003AAD60,
    'unite_func_0022df7c': 0x0022DF7C,
    'unite_func_002338ac': 0x002338AC,
    'unite_func_00233600': 0x00233600,
    'unite_func_00233804': 0x00233804,
    'camp_func_0029f10c': 0x0029F10C,
    'unite_func_002e32c8': 0x002E32C8,
    'camp_func_0022d33c': 0x0022D33C,
    'g_BibleDevilHandle_0043d9c8': 0x0043D9C8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_bibledevil_init.o'
    cmd = [
        r'C:\\msys64\\clang64\\bin\\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\\msys64\\clang64\\lib\\clang\\23\\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h9_camp_bibledevil_init_candidate']
    raw_mut, _ = funcs['h9_camp_bibledevil_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    WORK_STRUCT = 0x08000000
    uc.mem_map(WORK_STRUCT, 0x20000, unicorn.UC_PROT_ALL)
    uc.mem_write(WORK_STRUCT, b'\\x00' * 0x10000)
    VTBL = 0x08010000
    uc.mem_write(VTBL, struct.pack('<16I', *[0x00100004]*16))
    uc.mem_write(WORK_STRUCT, struct.pack('<I', VTBL))

    HANDLE_ADDR = 0x0043D9C8
    uc.mem_write(HANDLE_ADDR, b'\\x00' * 8)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08005000))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002100))
    uc.mem_write(0x00232800, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C23F8, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08006000))
    uc.mem_write(0x002333BC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0022D5C8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x003AAD60, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0022DF7C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002338AC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00233600, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00233804, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0029F10C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002E32C8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x0022D33C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, WORK_STRUCT)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    handle_val = uc.mem_read(HANDLE_ADDR, 4)
    work_val = uc.mem_read(WORK_STRUCT, 0x20)
    return struct.unpack('<I', handle_val)[0], bytes(work_val)

def main():
    out_dir = ROOT / 'build/h9_experiments/bibledevil'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 bibleDevil_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 8. h9_camp_buttonhelp_init_experiment.py
(TOOLS / 'h9_camp_buttonhelp_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0028D974 ButtonHelp_Init."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h9_camp_buttonhelp_init_candidate.cpp'
ORIG_ADDR = 0x0028D974
ORIG_SIZE = 736
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'UiSpriteGroup_Init_002c3344': 0x002C3344,
    'UiSpriteGroup_BindTable_002c32f8': 0x002C32F8,
    'UiAnimSprite_SetupEx_002bdb2c': 0x002BDB2C,
    'UiAnimSprite_SetMode_002bf030': 0x002BF030,
    'g_ButtonHelpManager_0043da28': 0x0043DA28,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h9_camp_buttonhelp_init.o'
    cmd = [
        r'C:\\msys64\\clang64\\bin\\clang++.exe',
        '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard',
        '-Oz', '-std=c++20', '-fno-exceptions', '-fno-rtti', '-ffreestanding',
        '-nostdinc', '-nostdinc++',
        '-isystem', str(ROOT / 'include/freestanding'),
        '-isystem', r'C:\\msys64\\clang64\\lib\\clang\\23\\include',
        f'-I{ROOT / "include"}',
        '-c', str(SRC_PATH), '-o', str(obj_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h9_camp_buttonhelp_init_candidate']
    raw_mut, _ = funcs['h9_camp_buttonhelp_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            reloc_vma = CAND_ADDR + r.offset
            if r.relocation_type == 2:
                struct.pack_into('<I', blob_cand, r.offset, tgt)
            elif r.relocation_type in (28, 29):
                w = branch_word(reloc_vma, tgt, is_bl=(r.relocation_type == 28))
                struct.pack_into('<I', blob_cand, r.offset, w)

    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, bytes]:
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

    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    MGR_ADDR = 0x0043DA28
    uc.mem_write(MGR_ADDR, b'\\x00' * 8)

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002000))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08002100))

    for a in [0x002C3344, 0x002C32F8, 0x002BDB2C, 0x00262448, 0x00296154, 0x002BDA1C, 0x002BDA10, 0x002BDA00, 0x002972F8, 0x002BF030]:
        uc.mem_write(a, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    mgr_val = uc.mem_read(MGR_ADDR, 8)
    work_val = uc.mem_read(WORK_ADDR, 0x20)
    return struct.unpack('<I', mgr_val[:4])[0], bytes(mgr_val + work_val)

def main():
    out_dir = ROOT / 'build/h9_experiments/buttonhelp'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H9 ButtonHelp_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

print("Successfully updated all 8 Unicorn differential experiment scripts for H9.")
