#!/usr/bin/env python3
"""Generate all 8 Unicorn offline differential experiment scripts for Milestone H8."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h8_ui_status_bustup_experiment.py
(TOOLS / 'h8_ui_status_bustup_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00223A90 StatusBustUp_Init."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h8_ui_status_bustup_candidate.cpp'
ORIG_ADDR = 0x00223A90
ORIG_SIZE = 248
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdRes_002c4e28': 0x002C4E28,
    'AsdRes_002c5b04': 0x002C5B04,
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'engine_func_002c3b48': 0x002C3B48,
    'g_StatusBustUpWork_0044e158': 0x0044E158,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h8_ui_status_bustup.o'
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
    raw_cand, relocs_cand = funcs['h8_ui_status_bustup_candidate']
    raw_mut, _ = funcs['h8_ui_status_bustup_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
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

    WORK_ADDR = 0x0044E158
    uc.mem_write(WORK_ADDR, b'\\x00' * 0x20)

    # Mock helpers
    uc.mem_write(0x002C4E28, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5B04, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    # AsdMem_Alloc returns 0x08001000
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', 0x08001000))
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)

    uc.mem_write(0x002C3B48, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    r0 = uc.reg_read(UC_ARM_REG_R0)
    mem = uc.mem_read(WORK_ADDR, 0x10)
    return r0, bytes(mem)

def main():
    out_dir = ROOT / 'build/h8_experiments/bustup'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H8 StatusBustUp_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

    # Mutation test
    mut_blob = bytearray(cand_blob)
    mut_blob[:len(raw_mut)] = raw_mut
    mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR)
    assert mut_mem != orig_mem, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 2. h8_ui_status_camera_experiment.py
(TOOLS / 'h8_ui_status_camera_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00258E38 StatusCamera_Init."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h8_ui_status_camera_candidate.cpp'
ORIG_ADDR = 0x00258E38
ORIG_SIZE = 480
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'engine_func_002bc828': 0x002BC828,
    'engine_func_002c2210': 0x002C2210,
    'engine_func_002c20a8': 0x002C20A8,
    'engine_func_002c1ffc': 0x002C1FFC,
    'engine_func_00298fec': 0x00298FEC,
    'engine_func_002c1740': 0x002C1740,
    'engine_func_002c1774': 0x002C1774,
    'g_StatusCameraWork_0044e178': 0x0044E178,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h8_ui_status_camera.o'
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
    raw_cand, relocs_cand = funcs['h8_ui_status_camera_candidate']
    raw_mut, _ = funcs['h8_ui_status_camera_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
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

    WORK_PTR_ADDR = 0x0044E178
    CAMERA_OBJ = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(WORK_PTR_ADDR, struct.pack('<I', CAMERA_OBJ))

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', CAMERA_OBJ))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BC828, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C2210, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C20A8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C1FFC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00298FEC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C1740, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C1774, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    VEC_ADDR = 0x08005000
    pos_data = struct.pack('<fff', 0.0, 10.0, 20.0)
    target_data = struct.pack('<fff', 0.0, 0.0, 0.0)
    up_data = struct.pack('<fff', 0.0, 1.0, 0.0)
    uc.mem_write(VEC_ADDR, pos_data + target_data + up_data)

    uc.reg_write(UC_ARM_REG_R0, VEC_ADDR)
    uc.reg_write(UC_ARM_REG_R1, VEC_ADDR + 12)
    uc.reg_write(UC_ARM_REG_R2, VEC_ADDR + 24)

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    mem = uc.mem_read(CAMERA_OBJ, 0x53C)
    return 0, bytes(mem)

def main():
    out_dir = ROOT / 'build/h8_experiments/camera'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_mem == cand_mem)
    print(f"H8 StatusCamera_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 3. h8_ui_status_affinity_experiment.py
(TOOLS / 'h8_ui_status_affinity_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00293E4C Status_UpdateAffinityTable."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h8_ui_status_affinity_candidate.cpp'
ORIG_ADDR = 0x00293E4C
ORIG_SIZE = 520
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'StatusDown_SetDisplayMode_00292f44': 0x00292F44,
    'g_StatusContext_0044e140': 0x0044E140,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h8_ui_status_affinity.o'
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
    raw_cand, relocs_cand = funcs['h8_ui_status_affinity_candidate']
    raw_mut, _ = funcs['h8_ui_status_affinity_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
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

    CTX_ADDR = 0x0044E140
    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x20000, unicorn.UC_PROT_ALL)
    uc.mem_write(CTX_ADDR, struct.pack('<II', 0, WORK_ADDR))

    # Mock StatusDown_SetDisplayMode: simply return cleanly
    uc.mem_write(0x00292F44, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    flags = uc.mem_read(WORK_ADDR + 0x1E63, 1)
    return 0, bytes(flags)

def main():
    out_dir = ROOT / 'build/h8_experiments/affinity'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_mem == cand_mem)
    print(f"H8 Status_UpdateAffinityTable: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 4. h8_ui_statusdown_itemsort_experiment.py
(TOOLS / 'h8_ui_statusdown_itemsort_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0032C4BC StatusDown_SortItemList."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h8_ui_statusdown_itemsort_candidate.cpp'
ORIG_ADDR = 0x0032C4BC
ORIG_SIZE = 372
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'UiMenu_GetSortOptions_002a0fac': 0x002A0FAC,
    'qsort_002b7f0a': 0x002B7F0A,
    'qsort_tail_0027f3d4': 0x0027F3D4,
    'g_StatusDownContext_0044e190': 0x0044E190,
    'StatusDown_ItemSortByIdAsc': 0x00206CBC,
    'StatusDown_ItemSortByIdDesc': 0x002E4608,
    'StatusDown_ItemSortByTypeAsc': 0x00206C38,
    'StatusDown_ItemSortByTypeDesc': 0x002E4584,
    'engine_func_002dca98': 0x002DCA98,
    'engine_func_002c6d30': 0x002C6D30,
    'engine_func_001f61a4': 0x001F61A4,
    'engine_func_001d1bb8': 0x001D1BB8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h8_ui_statusdown_itemsort.o'
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
    raw_cand, relocs_cand = funcs['h8_ui_statusdown_itemsort_candidate']
    raw_mut, _ = funcs['h8_ui_statusdown_itemsort_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
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

    CTX_ADDR = 0x0044E190
    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(CTX_ADDR, struct.pack('<I', WORK_ADDR))

    # Mock UiMenu_GetSortOptions (returns pointer with mode_byte at offset 0x16)
    OPT_ADDR = 0x08009000
    uc.mem_write(OPT_ADDR + 0x16, b'\\x00') # no sort to exit cleanly
    uc.mem_write(0x002A0FAC, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', OPT_ADDR))

    # Mock qsort (Thumb code: mov r0, 0; bx lr)
    uc.mem_write(0x002B7F0A & ~1, struct.pack('<HH', 0x2000, 0x4770))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return 0, b''

def main():
    out_dir = ROOT / 'build/h8_experiments/itemsort'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0)
    print(f"H8 StatusDown_SortItemList: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 7. h8_ui_statusdown_init_experiment.py
(TOOLS / 'h8_ui_statusdown_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002D931C StatusDown_Init."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h8_ui_statusdown_init_candidate.cpp'
ORIG_ADDR = 0x002D931C
ORIG_SIZE = 764
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
    'UiAnimSprite_SetMode_002bf030': 0x002BF030,
    'engine_func_002bda1c': 0x002BDA1C,
    'engine_func_002bda10': 0x002BDA10,
    'engine_func_002bda00': 0x002BDA00,
    'engine_func_002c4450': 0x002C4450,
    'g_StatusDownContext_0044e190': 0x0044E190,
    'g_StatusDownSpriteTable_00407d58': 0x00407D58,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h8_ui_statusdown_init.o'
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
    raw_cand, relocs_cand = funcs['h8_ui_statusdown_init_candidate']
    raw_mut, _ = funcs['h8_ui_statusdown_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
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

    CTX_ADDR = 0x0044E190
    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x20000, unicorn.UC_PROT_ALL)
    uc.mem_write(CTX_ADDR, struct.pack('<I', WORK_ADDR))

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE3A00001, 0xE12FFF1E))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE3A00002, 0xE12FFF1E))
    uc.mem_write(0x002C3344, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C32F8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDB2C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDAC0, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BF030, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BF0A8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDA1C, struct.pack('<II', 0xE3A00003, 0xE12FFF1E))
    uc.mem_write(0x002BDA10, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDA00, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C4450, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    flag = uc.mem_read(WORK_ADDR + 0x2392, 1)
    return 0, bytes(flag)

def main():
    out_dir = ROOT / 'build/h8_experiments/statusdown_init'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_mem == cand_mem)
    print(f"H8 StatusDown_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 8. h8_camp_gauntletmenu_init_experiment.py
(TOOLS / 'h8_camp_gauntletmenu_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002E2454 GauntletAppMenu_Init."""
from __future__ import annotations
import argparse, json, struct, subprocess, sys
from pathlib import Path

import unicorn
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h8_camp_gauntletmenu_init_candidate.cpp'
ORIG_ADDR = 0x002E2454
ORIG_SIZE = 764
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Alloc_002c4b84': 0x002C4B84,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'AsdTask_Create_002c5978': 0x002C5978,
    'AsdTask_CreateDraw_002c4c00': 0x002C4C00,
    'engine_func_002c0ba8': 0x002C0BA8,
    'engine_func_002488a8': 0x002488A8,
    'engine_func_002976ac': 0x002976AC,
    'g_GauntletAppWork_0044e1a0': 0x0044E1A0,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h8_camp_gauntletmenu_init.o'
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
    raw_cand, relocs_cand = funcs['h8_camp_gauntletmenu_init_candidate']
    raw_mut, _ = funcs['h8_camp_gauntletmenu_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        tgt = TARGET_SYMBOLS.get(r.symbol_name, 0)
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

    WORK_PTR_ADDR = 0x0044E1A0
    WORK_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(WORK_PTR_ADDR, struct.pack('<I', WORK_ADDR))

    # Mock helpers
    uc.mem_write(0x002C4B84, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5978, struct.pack('<II', 0xE3A00001, 0xE12FFF1E))
    uc.mem_write(0x002C4C00, struct.pack('<II', 0xE3A00002, 0xE12FFF1E))
    uc.mem_write(0x002C0BA8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002488A8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002976AC, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002972F8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C0E4C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C0E9C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C0EC4, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C3344, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C32F8, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDB2C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BDAC0, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BF030, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C5E2C, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    task_ptr = uc.mem_read(WORK_ADDR, 4)
    return struct.unpack('<I', task_ptr)[0], bytes(task_ptr)

def main():
    out_dir = ROOT / 'build/h8_experiments/gauntlet'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0)
    print(f"H8 GauntletAppMenu_Init: status={'passed' if matched else 'failed'}, matched={matched}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

print("All 8 H8 experiment scripts regenerated successfully!")
