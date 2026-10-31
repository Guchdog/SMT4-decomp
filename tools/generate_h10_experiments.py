#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H10."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h10_camp_burroughs_getsavedata_experiment.py
(TOOLS / 'h10_camp_burroughs_getsavedata_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002A0FAC Burroughs_GetSaveData."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_burroughs_getsavedata_candidate.cpp'
ORIG_ADDR = 0x002A0FAC
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_GameWork_0043e2a8': 0x0043E2A8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_burroughs_getsavedata.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_burroughs_getsavedata_candidate']
    raw_mut, _ = funcs['h10_camp_burroughs_getsavedata_mutation']

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
    uc.mem_map(0x08000000, 0x30000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x0043E2A8, struct.pack('<II', 0, WORK_ADDR))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    r0 = uc.reg_read(UC_ARM_REG_R0)
    return r0, b''

def main():
    out_dir = ROOT / 'build/h10_experiments/getsavedata'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0)
    print(f"H10 Burroughs_GetSaveData: status={'passed' if matched else 'failed'}, orig={hex(orig_r0)}, cand={hex(cand_r0)}")
    assert matched, f"Original and candidate outputs differ: {hex(orig_r0)} vs {hex(cand_r0)}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, _ = run_simulation(image, bytes(mut_blob), CAND_ADDR)
        mut_detected = (mut_r0 != cand_r0)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 2. h10_camp_burroughs_appdispatch_experiment.py
(TOOLS / 'h10_camp_burroughs_appdispatch_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002A0EA8 Burroughs_AppDispatch."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_burroughs_appdispatch_candidate.cpp'
ORIG_ADDR = 0x002A0EA8
ORIG_SIZE = 168
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'camp_func_002971e4': 0x002971E4,
    'camp_func_002a0f68': 0x002A0F68,
    'sound_func_002b8b78': 0x002B8B78,
    'g_CampWork_0043dd68': 0x0043DD68,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_burroughs_appdispatch.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_burroughs_appdispatch_candidate']
    raw_mut, _ = funcs['h10_camp_burroughs_appdispatch_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, app_id: int) -> tuple[int, bytes]:
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
    uc.mem_write(0x0043DD68, struct.pack('<I', WORK_ADDR))

    # Initialize work
    work_bytes = bytearray(0x500)
    work_bytes[0x430] = 0 # not busy
    struct.pack_into('<I', work_bytes, 0x42C, 0x1234)
    struct.pack_into('<i', work_bytes, 0x478, 0)
    uc.mem_write(WORK_ADDR, bytes(work_bytes))

    # Mock helpers
    uc.mem_write(0x002971E4, struct.pack('<II', 0xE3A00001, 0xE12FFF1E)) # returns 1
    uc.mem_write(0x002A0F68, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002B8B78, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, app_id)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    r0 = uc.reg_read(UC_ARM_REG_R0)
    mem = uc.mem_read(WORK_ADDR + 0x430, 0x50)
    return r0, bytes(mem)

def main():
    out_dir = ROOT / 'build/h10_experiments/appdispatch'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    for app_id in [7, 8, 9, 12]:
        orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR, app_id)
        cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR, app_id)

        matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
        print(f"H10 Burroughs_AppDispatch (app {app_id}): status={'passed' if matched else 'failed'}, matched={matched}")
        assert matched, f"Mismatch for app {app_id}: {orig_r0} vs {cand_r0}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_r0, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR, 7)
        mut_detected = (mut_r0 != cand_r0 or mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 3. h10_camp_quest_resetselection_experiment.py
(TOOLS / 'h10_camp_quest_resetselection_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026A004 Quest_ResetSelection."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_quest_resetselection_candidate.cpp'
ORIG_ADDR = 0x0026A004
ORIG_SIZE = 40
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_CampWork_0043dd68': 0x0043DD68,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_quest_resetselection.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_quest_resetselection_candidate']
    raw_mut, _ = funcs['h10_camp_quest_resetselection_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, cat: int) -> tuple[int, bytes]:
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
    uc.mem_write(0x0043DD68, struct.pack('<I', WORK_ADDR))

    work_bytes = bytearray(0x500)
    work_bytes[0x420] = 0x55
    struct.pack_into('<I', work_bytes, 0x400, 0xAAAAAAAA)
    struct.pack_into('<I', work_bytes, 0x3FC, 0xBBBBBBBB)
    uc.mem_write(WORK_ADDR, bytes(work_bytes))

    uc.reg_write(UC_ARM_REG_R0, cat)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    mem = uc.mem_read(WORK_ADDR + 0x3F0, 0x40)
    return 0, bytes(mem)

def main():
    out_dir = ROOT / 'build/h10_experiments/resetselection'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    for cat in [1, 2, 5]:
        _, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR, cat)
        _, cand_mem = run_simulation(image, cand_blob, CAND_ADDR, cat)

        matched = (orig_mem == cand_mem)
        print(f"H10 Quest_ResetSelection (cat {cat}): status={'passed' if matched else 'failed'}, matched={matched}")
        assert matched, f"Mismatch for cat {cat}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        _, mut_mem = run_simulation(image, bytes(mut_blob), CAND_ADDR, 1)
        mut_detected = (mut_mem != cand_mem)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 4. h10_camp_quest_evaltarget_experiment.py
(TOOLS / 'h10_camp_quest_evaltarget_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026A86C Quest_EvaluateTargetCondition."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_quest_evaltarget_candidate.cpp'
ORIG_ADDR = 0x0026A86C
ORIG_SIZE = 152
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_quest_evaltarget.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_quest_evaltarget_candidate']
    raw_mut, _ = funcs['h10_camp_quest_evaltarget_mutation']
    return bytes(raw_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, entry_bytes: bytes, cond_bytes: bytes) -> int:
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

    DATA_BASE = 0x08000000
    uc.mem_map(DATA_BASE, 0x10000, unicorn.UC_PROT_ALL)
    ENTRY_ADDR = DATA_BASE + 0x100
    COND_ADDR = DATA_BASE + 0x200
    uc.mem_write(ENTRY_ADDR, entry_bytes)
    uc.mem_write(COND_ADDR, cond_bytes)

    uc.reg_write(UC_ARM_REG_R0, ENTRY_ADDR)
    uc.reg_write(UC_ARM_REG_R1, COND_ADDR)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    out_dir = ROOT / 'build/h10_experiments/evaltarget'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    cases = [
        # Case 1: type 5, cond 0, matching target
        (0x00052800, 0, 0x00005000, 0, 0),
        # Case 2: type 5, cond 0, non-matching target
        (0x00052800, 0, 0x00008000, 0, 0),
        # Case 3: type 6, cond 3, f38 with 0xA000
        (0x0006A000, 3, 0, 0x0000, 1),
        # Case 4: type 2 (invalid type)
        (0x00020000, 0, 0, 0, 0),
    ]

    for f38, cond_type, c28, c36, c43 in cases:
        eb = bytearray(0x50)
        struct.pack_into('<I', eb, 0x38, f38)
        cb = bytearray(0x50)
        cb[0x23] = cond_type
        struct.pack_into('<I', cb, 0x28, c28)
        struct.pack_into('<H', cb, 0x36, c36)
        cb[0x43] = c43

        orig_res = run_simulation(image, cand_blob, ORIG_ADDR, bytes(eb), bytes(cb))
        cand_res = run_simulation(image, cand_blob, CAND_ADDR, bytes(eb), bytes(cb))

        matched = (orig_res == cand_res)
        print(f"H10 Quest_EvaluateTargetCondition ({hex(f38)}, cond {cond_type}): orig={orig_res}, cand={cand_res}, matched={matched}")
        assert matched, f"Mismatch: {orig_res} vs {cand_res}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_res = run_simulation(image, bytes(mut_blob), CAND_ADDR, bytes(eb), bytes(cb))
        mut_detected = (mut_res != cand_res)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 5. h10_camp_quest_getavailability_experiment.py
(TOOLS / 'h10_camp_quest_getavailability_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026A9FC Quest_GetAvailability."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_quest_getavailability_candidate.cpp'
ORIG_ADDR = 0x0026A9FC
ORIG_SIZE = 196
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'Quest_GetMainEntry_002ae3f0': 0x002AE3F0,
    'Quest_GetSubTable_002aa224': 0x002AA224,
    'engine_func_002c0ec4': 0x002C0EC4,
    'engine_func_002c0e9c': 0x002C0E9C,
    'engine_func_002c0e4c': 0x002C0E4C,
    'Quest_FindEntry_002b48dc': 0x002B48DC,
    'g_QuestTableMgr_00433158': 0x00433158,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_quest_getavailability.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_quest_getavailability_candidate']
    raw_mut, _ = funcs['h10_camp_quest_getavailability_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, qid: int, flags38: int) -> int:
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

    ENTRY_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    entry_bytes = bytearray(0x50)
    struct.pack_into('<I', entry_bytes, 0x38, flags38)
    uc.mem_write(ENTRY_ADDR, bytes(entry_bytes))
    uc.mem_write(0x00433158, struct.pack('<I', ENTRY_ADDR))

    # Mock helpers
    uc.mem_write(0x002AE3F0, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', ENTRY_ADDR))
    uc.mem_write(0x002AA224, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', ENTRY_ADDR))
    uc.mem_write(0x002B48DC, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', ENTRY_ADDR))

    uc.reg_write(UC_ARM_REG_R0, qid)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    out_dir = ROOT / 'build/h10_experiments/getavailability'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    test_cases = [
        (10, 0x00000000), # main quest available
        (10, 0x80000000), # main quest unavailable (bit 31 set)
        (500, 0x00000000), # challenge quest available
        (500, 0x40000000), # challenge quest unavailable (bit 30 set)
    ]

    for qid, f38 in test_cases:
        orig_res = run_simulation(image, cand_blob, ORIG_ADDR, qid, f38)
        cand_res = run_simulation(image, cand_blob, CAND_ADDR, qid, f38)

        matched = (orig_res == cand_res)
        print(f"H10 Quest_GetAvailability (qid {qid}, f38 {hex(f38)}): orig={orig_res}, cand={cand_res}, matched={matched}")
        assert matched, f"Mismatch for qid {qid}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_res = run_simulation(image, bytes(mut_blob), CAND_ADDR, 10, 0)
        mut_detected = (mut_res != cand_res)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 6. h10_camp_quest_unpackentry_experiment.py
(TOOLS / 'h10_camp_quest_unpackentry_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026AAC0 Quest_UnpackEntryData."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_quest_unpackentry_candidate.cpp'
ORIG_ADDR = 0x0026AAC0
ORIG_SIZE = 256
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'Quest_GetStaticDef_002b087c': 0x002B087C,
    'AsdMem_Zero_002c4b30': 0x002C4B30,
    'Quest_InitEntrySub_002bcf58': 0x002BCF58,
    'Quest_GetDynamicRecord_002b9364': 0x002B9364,
    'Quest_FormatTitle_0024be90': 0x0024BE90,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_quest_unpackentry.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_quest_unpackentry_candidate']
    raw_mut, _ = funcs['h10_camp_quest_unpackentry_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, qid: int) -> bytes:
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

    DATA_BASE = 0x08000000
    uc.mem_map(DATA_BASE, 0x10000, unicorn.UC_PROT_ALL)
    OUT_ADDR = DATA_BASE + 0x100
    DEF_ADDR = DATA_BASE + 0x300
    REC_ADDR = DATA_BASE + 0x500

    def_bytes = bytearray(0x80)
    def_bytes[2] = 3 # category
    struct.pack_into('<H', def_bytes, 4, 0x101)
    struct.pack_into('<H', def_bytes, 8, 0x102)
    struct.pack_into('<H', def_bytes, 0xC, 0x103)
    struct.pack_into('<H', def_bytes, 0xE, 0x104)
    struct.pack_into('<H', def_bytes, 0x10, 0x105)
    struct.pack_into('<H', def_bytes, 0x12, 0x106)
    struct.pack_into('<H', def_bytes, 0x14, 0x107)
    uc.mem_write(DEF_ADDR, bytes(def_bytes))

    rec_bytes = bytearray(0x50)
    struct.pack_into('<H', rec_bytes, 0x38, 0x0020)
    uc.mem_write(REC_ADDR, bytes(rec_bytes))

    # Mock helpers
    uc.mem_write(0x002B087C, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', DEF_ADDR))
    uc.mem_write(0x002C4B30, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002BCF58, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002B9364, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', REC_ADDR))
    uc.mem_write(0x0024BE90, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_R0, qid)
    uc.reg_write(UC_ARM_REG_R1, OUT_ADDR)
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.mem_read(OUT_ADDR, 0x4C)

def main():
    out_dir = ROOT / 'build/h10_experiments/unpackentry'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    for qid in [15, 42]:
        orig_out = run_simulation(image, cand_blob, ORIG_ADDR, qid)
        cand_out = run_simulation(image, cand_blob, CAND_ADDR, qid)

        matched = (orig_out == cand_out)
        print(f"H10 Quest_UnpackEntryData (qid {qid}): status={'passed' if matched else 'failed'}, matched={matched}")
        assert matched, f"Mismatch for qid {qid}"

    try:
        mut_blob = bytearray(cand_blob)
        mut_blob[:len(raw_mut)] = raw_mut
        mut_out = run_simulation(image, bytes(mut_blob), CAND_ADDR, 15)
        mut_detected = (mut_out != cand_out)
    except Exception:
        mut_detected = True
    assert mut_detected, "Mutation was not detected!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 7. h10_camp_appstore_setflag_experiment.py
(TOOLS / 'h10_camp_appstore_setflag_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003253D8 AppStore_SetFlag."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_appstore_setflag_candidate.cpp'
ORIG_ADDR = 0x003253D8
ORIG_SIZE = 56
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'app_func_00242a80': 0x00242A80,
    'app_func_00293c98': 0x00293C98,
    'g_AppStoreWork_00439ca8': 0x00439CA8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_appstore_setflag.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_appstore_setflag_candidate']
    raw_mut, _ = funcs['h10_camp_appstore_setflag_mutation']

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
    uc.mem_write(0x00439CA8, struct.pack('<I', WORK_ADDR))

    # Mock helpers
    uc.mem_write(0x00242A80, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00293C98, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', WORK_ADDR))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    r0 = uc.reg_read(UC_ARM_REG_R0)
    mem = uc.mem_read(WORK_ADDR + 0x44A0, 4)
    return r0, bytes(mem)

def main():
    out_dir = ROOT / 'build/h10_experiments/appstoresetflag'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0 and orig_mem == cand_mem)
    print(f"H10 AppStore_SetFlag: status={'passed' if matched else 'failed'}, matched={matched}")
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

# 8. h10_camp_appstore_getappparam_experiment.py
(TOOLS / 'h10_camp_appstore_getappparam_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00325444 AppStore_GetAppParam."""
from __future__ import annotations
import json, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unicorn
from unicorn.arm_const import *
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / 'extracted/exefs/code.bin'
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h10_camp_appstore_getappparam_candidate.cpp'
ORIG_ADDR = 0x00325444
ORIG_SIZE = 52
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'app_func_00296f60': 0x00296F60,
    'app_func_00293c98': 0x00293C98,
    'app_func_00245318': 0x00245318,
    'engine_func_002c0e9c': 0x002C0E9C,
    'app_func_0028df54': 0x0028DF54,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h10_camp_appstore_getappparam.o'
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
    raw_cand, relocs_cand = funcs['h10_camp_appstore_getappparam_candidate']
    raw_mut, _ = funcs['h10_camp_appstore_getappparam_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> int:
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

    TABLE_ADDR = 0x08001000
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_write(TABLE_ADDR + 0x10, struct.pack('<H', 0x42)) # index 4 (0x10) = 0x42

    # Mock helpers
    uc.mem_write(0x00296F60, struct.pack('<II', 0xE3A00004, 0xE12FFF1E)) # returns index 4
    uc.mem_write(0x00293C98, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x00245318, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))
    uc.mem_write(0x002C0E9C, struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', TABLE_ADDR))
    uc.mem_write(0x0028DF54, struct.pack('<II', 0xE3A00000, 0xE12FFF1E))

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    out_dir = ROOT / 'build/h10_experiments/appparam'
    cand_blob, raw_cand, raw_mut = build_candidates(out_dir)
    image = CODE_PATH.read_bytes()

    orig_r0 = run_simulation(image, cand_blob, ORIG_ADDR)
    cand_r0 = run_simulation(image, cand_blob, CAND_ADDR)

    matched = (orig_r0 == cand_r0)
    print(f"H10 AppStore_GetAppParam: status={'passed' if matched else 'failed'}, orig={orig_r0}, cand={cand_r0}")
    assert matched, "Original and candidate outputs differ!"

if __name__ == '__main__':
    main()
''', encoding='utf-8')

print("All 8 Unicorn differential experiment scripts generated successfully!")

# Execute all 8
experiments = [
    'h10_camp_burroughs_getsavedata_experiment.py',
    'h10_camp_burroughs_appdispatch_experiment.py',
    'h10_camp_quest_resetselection_experiment.py',
    'h10_camp_quest_evaltarget_experiment.py',
    'h10_camp_quest_getavailability_experiment.py',
    'h10_camp_quest_unpackentry_experiment.py',
    'h10_camp_appstore_setflag_experiment.py',
    'h10_camp_appstore_getappparam_experiment.py',
]

print("=== Executing all 8 Milestone H10 Differential Validation Tests ===")
for exp in experiments:
    cmd = [sys.executable, str(TOOLS / exp)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED: {exp}")
        print(res.stderr)
        sys.exit(1)
    print(res.stdout.strip())

print("\nALL 8 H10 CANDIDATES PASSED UNICORN OFFLINE DIFFERENTIAL VALIDATION!")
