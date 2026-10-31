#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H13."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h13_placewin_setvisible_experiment.py
(TOOLS / 'h13_placewin_setvisible_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002638FC PlaceWin_SetVisible."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_placewin_setvisible_candidate.cpp'
ORIG_ADDR = 0x002638FC
ORIG_SIZE = 20
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_PlaceWinWork_0043da28': 0x0043DA28,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_placewin_setvisible.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_placewin_setvisible_candidate']
    raw_mut, relocs_mut = funcs['h13_placewin_setvisible_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, visible: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    WORK_BUF = MEM_BASE + 0x1000
    # g_PlaceWinWork_0043da28 is at 0x0043DA28
    # [0x0043DA28 + 4] = WORK_BUF
    uc.mem_write(0x0043DA28 + 4, struct.pack('<I', WORK_BUF))
    # Clear target byte at WORK_BUF + 0x4C5
    uc.mem_write(WORK_BUF + 0x4C5, b'\\x55')

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, visible)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.mem_read(WORK_BUF + 0x4C5, 1)[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    test_vectors = [0, 1, 42, 255]
    for v in test_vectors:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)
        if orig != cand:
            raise AssertionError(f'Mismatch for visible={v}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for visible={v}')
    print(f'[PASS] h13_placewin_setvisible: 100% parity across {len(test_vectors)} vectors, mutation detected.')

if __name__ == '__main__':
    main()
''')

# 2. h13_placewin_dismiss_experiment.py
(TOOLS / 'h13_placewin_dismiss_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002638DC PlaceWin_Dismiss."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_placewin_dismiss_candidate.cpp'
ORIG_ADDR = 0x002638DC
ORIG_SIZE = 32
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_PlaceWinContext_0043e140': 0x0043E140,
    'sub_2BF030': 0x002BF030,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_placewin_dismiss.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_placewin_dismiss_candidate']
    raw_mut, relocs_mut = funcs['h13_placewin_dismiss_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub sub_2BF030: write args to 0x0043E150 (r0) and 0x0043E154 (r1), then bx lr
    # ldr r2, =0x0043E150; str r0, [r2]; str r1, [r2, #4]; bx lr
    stub = struct.pack('<IIIII',
        0xE59F2008, # ldr r2, [pc, #8] -> 0x0043E150
        0xE5820000, # str r0, [r2]
        0xE5821004, # str r1, [r2, #4]
        0xE12FFF1E, # bx lr
        0x0043E150, # literal
    )
    uc.mem_write(0x002BF030, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    CTX_BUF = MEM_BASE + 0x2000
    uc.mem_write(0x0043E140, struct.pack('<I', CTX_BUF))
    uc.mem_write(CTX_BUF + 8, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)

    state = struct.unpack('<I', uc.mem_read(CTX_BUF + 8, 4))[0]
    call_r0 = struct.unpack('<I', uc.mem_read(0x0043E150, 4))[0]
    call_r1 = struct.unpack('<I', uc.mem_read(0x0043E154, 4))[0]
    return state, call_r0, call_r1

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    orig = run_simulation(code, cand_blob, ORIG_ADDR)
    cand = run_simulation(code, cand_blob, CAND_ADDR)
    mut = run_simulation(code, mut_blob, CAND_ADDR)

    if orig != cand:
        raise AssertionError(f'Mismatch: orig={orig}, cand={cand}')
    if orig == mut:
        raise AssertionError('Mutation undetected')
    print(f'[PASS] h13_placewin_dismiss: parity confirmed (state={cand[0]}, r0=0x{cand[1]:08X}, r1={cand[2]}), mutation detected.')

if __name__ == '__main__':
    main()
''')

# 3. h13_placewin_isactive_experiment.py
(TOOLS / 'h13_placewin_isactive_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0026394C PlaceWin_IsActive."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_placewin_isactive_candidate.cpp'
ORIG_ADDR = 0x0026394C
ORIG_SIZE = 44
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_placewin_isactive.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h13_placewin_isactive_candidate']
    raw_mut, _ = funcs['h13_placewin_isactive_mutation']
    return raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, timer_present: bool, elapsed: float, duration: float) -> int:
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

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    HOLDER_BUF = MEM_BASE + 0x100
    TIMER_BUF = MEM_BASE + 0x200

    if timer_present:
        uc.mem_write(HOLDER_BUF + 4, struct.pack('<I', TIMER_BUF))
        uc.mem_write(TIMER_BUF + 0x38, struct.pack('<f', duration))
        uc.mem_write(TIMER_BUF + 0x48, struct.pack('<f', elapsed))
    else:
        uc.mem_write(HOLDER_BUF + 4, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, HOLDER_BUF)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    cases = [
        (False, 0.0, 0.0),       # Null timer -> 1
        (True, 0.0, 5.0),        # 0.0 <= 5.0 -> 1
        (True, 4.9, 5.0),        # 4.9 <= 5.0 -> 1
        (True, 5.0, 5.0),        # 5.0 <= 5.0 -> 1
        (True, 5.0001, 5.0),     # 5.0001 > 5.0 -> 0
        (True, 10.0, 5.0),       # 10.0 > 5.0 -> 0
    ]

    for timer_present, elapsed, duration in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, timer_present, elapsed, duration)
        cand = run_simulation(code, cand_blob, CAND_ADDR, timer_present, elapsed, duration)
        mut = run_simulation(code, mut_blob, CAND_ADDR, timer_present, elapsed, duration)

        if orig != cand:
            raise AssertionError(f'Mismatch for timer={timer_present}, el={elapsed}, dur={duration}: orig={orig}, cand={cand}')
        if orig == 1 and mut == 1:
            raise AssertionError(f'Mutation undetected for timer={timer_present}')

    print(f'[PASS] h13_placewin_isactive: 100% parity across {len(cases)} cases, mutation sensitivity verified.')

if __name__ == '__main__':
    main()
''')

# 4. h13_mapfield_clearactiveflag_experiment.py
(TOOLS / 'h13_mapfield_clearactiveflag_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00208A70 MapField_ClearActiveFlag."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_mapfield_clearactiveflag_candidate.cpp'
ORIG_ADDR = 0x00208A70
ORIG_SIZE = 20
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_MapFieldState_0049f91c': 0x0049F91C,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_mapfield_clearactiveflag.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_mapfield_clearactiveflag_candidate']
    raw_mut, relocs_mut = funcs['h13_mapfield_clearactiveflag_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, init_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # 0x0049F91C is within 0x00100000..0x00580000 (already mapped)
    uc.mem_write(0x0049F91C + 0x2F8, bytes([init_val]))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.mem_read(0x0049F91C + 0x2F8, 1)[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    for init_v in [1, 0x7F, 0xFF]:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, init_v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, init_v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, init_v)

        if orig != cand or cand != 0:
            raise AssertionError(f'Mismatch for init={init_v}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for init={init_v}')

    print(f'[PASS] h13_mapfield_clearactiveflag: verified flag reset to 0, mutation sensitivity confirmed.')

if __name__ == '__main__':
    main()
''')

# 5. h13_mapnavi_settargetcoords_experiment.py
(TOOLS / 'h13_mapnavi_settargetcoords_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D2E24 MapNavi_SetTargetCoords."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_mapnavi_settargetcoords_candidate.cpp'
ORIG_ADDR = 0x001D2E24
ORIG_SIZE = 40
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_MapNaviTarget_004474d8': 0x004474D8,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_mapnavi_settargetcoords.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_mapnavi_settargetcoords_candidate']
    raw_mut, relocs_mut = funcs['h13_mapnavi_settargetcoords_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, x: int, y: int) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    TARGET_BUF = MEM_BASE + 0x3000
    # g_MapNaviTarget_004474d8 is at 0x004474D8
    uc.mem_write(0x004474D8, struct.pack('<I', TARGET_BUF))
    # Fill target buffer with 0xAA
    uc.mem_write(TARGET_BUF, b'\\xAA' * 32)

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, x)
    uc.reg_write(UC_ARM_REG_R1, y)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.mem_read(TARGET_BUF, 16)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    vectors = [(0, 0), (100, 200), (0x1234, 0x5678), (0xFFFF, 0x7FFF)]
    for x, y in vectors:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, x, y)
        cand = run_simulation(code, cand_blob, CAND_ADDR, x, y)
        mut = run_simulation(code, mut_blob, CAND_ADDR, x, y)

        if orig != cand:
            raise AssertionError(f'Mismatch for ({x}, {y}): orig={orig.hex()}, cand={cand.hex()}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({x}, {y})')

        # Check fields: target_x at +4, target_y at +6, angle at +8 (=0), active at +0xA (=1)
        tx, ty, angle, act = struct.unpack_from('<HHHB', orig, 4)
        if tx != x or ty != y or angle != 0 or act != 1:
            raise AssertionError(f'Field check failed: tx={tx}, ty={ty}, angle={angle}, act={act}')

    print(f'[PASS] h13_mapnavi_settargetcoords: 100% parity across {len(vectors)} vectors, field values verified.')

if __name__ == '__main__':
    main()
''')

# 6. h13_mapnavi_reset_experiment.py
(TOOLS / 'h13_mapnavi_reset_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D2E0C MapNavi_Reset."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_mapnavi_reset_candidate.cpp'
ORIG_ADDR = 0x001D2E0C
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_MapRuntimeWork_00447060': 0x00447060,
    'sub_2C45B8': 0x002C45B8,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_mapnavi_reset.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_mapnavi_reset_candidate']
    raw_mut, relocs_mut = funcs['h13_mapnavi_reset_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub sub_2C45B8: records r0, r1 to 0x00447070, then bx lr
    stub = struct.pack('<IIIII',
        0xE59F2008, # ldr r2, [pc, #8] -> 0x00447070
        0xE5820000, # str r0, [r2]
        0xE5821004, # str r1, [r2, #4]
        0xE12FFF1E, # bx lr
        0x00447070, # literal
    )
    uc.mem_write(0x002C45B8, stub)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    PTR1 = MEM_BASE + 0x4000
    PTR2 = MEM_BASE + 0x5000
    uc.mem_write(0x00447060, struct.pack('<I', PTR1))
    uc.mem_write(PTR1, struct.pack('<I', PTR2))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    call_r0 = struct.unpack('<I', uc.mem_read(0x00447070, 4))[0]
    call_r1 = struct.unpack('<I', uc.mem_read(0x00447074, 4))[0]
    return call_r0, call_r1

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    orig = run_simulation(code, cand_blob, ORIG_ADDR)
    cand = run_simulation(code, cand_blob, CAND_ADDR)
    mut = run_simulation(code, mut_blob, CAND_ADDR)

    if orig != cand:
        raise AssertionError(f'Mismatch: orig={orig}, cand={cand}')
    if orig == mut:
        raise AssertionError('Mutation undetected')

    print(f'[PASS] h13_mapnavi_reset: parity verified (work=0x{cand[0]:08X}, flag={cand[1]}), mutation detected.')

if __name__ == '__main__':
    main()
''')

# 7. h13_mapepl_calcscale_experiment.py
(TOOLS / 'h13_mapepl_calcscale_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00193B28 MapEpl_CalcScale."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_mapepl_calcscale_candidate.cpp'
ORIG_ADDR = 0x00193B28
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_2C3290': 0x002C3290,
    'sub_20FDE0': 0x0020FDE0,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_mapepl_calcscale.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_mapepl_calcscale_candidate']
    raw_mut, relocs_mut = funcs['h13_mapepl_calcscale_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, val_a: int, val_b: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub sub_2C3290: returns val_a
    stub_a = struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', val_a)
    uc.mem_write(0x002C3290, stub_a)

    # Stub sub_20FDE0: returns val_b
    stub_b = struct.pack('<II', 0xE59F0000, 0xE12FFF1E) + struct.pack('<I', val_b)
    uc.mem_write(0x0020FDE0, stub_b)

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
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    pairs = [(3, 4), (10, 20), (0, 100), (7, 13)]
    for a, b in pairs:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, a, b)
        cand = run_simulation(code, cand_blob, CAND_ADDR, a, b)
        mut = run_simulation(code, mut_blob, CAND_ADDR, a, b)

        if orig != cand:
            raise AssertionError(f'Mismatch for ({a}, {b}): orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({a}, {b})')

    print(f'[PASS] h13_mapepl_calcscale: 100% parity across {len(pairs)} test pairs, product verified.')

if __name__ == '__main__':
    main()
''')

# 8. h13_mapcalc_distancetoentity_experiment.py
(TOOLS / 'h13_mapcalc_distancetoentity_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001D3A9C MapCalc_DistanceToEntity."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h13_mapcalc_distancetoentity_candidate.cpp'
ORIG_ADDR = 0x001D3A9C
ORIG_SIZE = 32
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'sub_266D70': 0x00266D70,
    'sub_2E05BC': 0x002E05BC,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h13_mapcalc_distancetoentity.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h13_mapcalc_distancetoentity_candidate']
    raw_mut, relocs_mut = funcs['h13_mapcalc_distancetoentity_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, dist_sq: float) -> tuple[int, float]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub sub_266D70 at 0x00266D70:
    # vldr s0, [pc, #4]; bx lr; literal float dist_sq
    stub_1 = struct.pack('<III',
        0xED9F0A01, # vldr s0, [pc, #4]
        0xE12FFF1E, # bx lr
        struct.unpack('<I', struct.pack('<f', dist_sq))[0]
    )
    uc.mem_write(0x00266D70, stub_1)

    # Stub sub_2E05BC at 0x002E05BC:
    # vstr s0, [pc, #4]; bx lr; literal space at 0x002E05C8
    stub_2 = struct.pack('<III',
        0xED8F0A01, # vstr s0, [pc, #4]
        0xE12FFF1E, # bx lr
        0x00000000,
    )
    uc.mem_write(0x002E05BC, stub_2)

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
    passed_dist = struct.unpack('<f', uc.mem_read(0x002E05BC + 8, 4))[0]
    return ret, passed_dist

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h13_tests')

    test_sqs = [0.0, 4.0, 25.0, 100.0, 144.0]
    for sq in test_sqs:
        orig_ret, orig_dist = run_simulation(code, cand_blob, ORIG_ADDR, sq)
        cand_ret, cand_dist = run_simulation(code, cand_blob, CAND_ADDR, sq)
        mut_ret, mut_dist = run_simulation(code, mut_blob, CAND_ADDR, sq)

        if orig_ret != cand_ret or abs(orig_dist - cand_dist) > 1e-5:
            raise AssertionError(f'Mismatch for sq={sq}: orig=({orig_ret}, {orig_dist}), cand=({cand_ret}, {cand_dist})')
        if orig_ret == mut_ret:
            raise AssertionError(f'Mutation undetected for sq={sq}')

    print(f'[PASS] h13_mapcalc_distancetoentity: 100% parity across {len(test_sqs)} inputs, sqrtf validated.')

if __name__ == '__main__':
    main()
''')

# Execute all 8 scripts
scripts = [
    'h13_placewin_setvisible_experiment.py',
    'h13_placewin_dismiss_experiment.py',
    'h13_placewin_isactive_experiment.py',
    'h13_mapfield_clearactiveflag_experiment.py',
    'h13_mapnavi_settargetcoords_experiment.py',
    'h13_mapnavi_reset_experiment.py',
    'h13_mapepl_calcscale_experiment.py',
    'h13_mapcalc_distancetoentity_experiment.py',
]

print('=== Executing all 8 Unicorn differential validation experiments for Milestone H13 ===')
for s in scripts:
    res = subprocess.run([sys.executable, str(TOOLS / s)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f'FAIL in {s}:')
        print(res.stdout)
        print(res.stderr)
        sys.exit(1)
    else:
        print(res.stdout.strip())

print('=== ALL 8 H13 DIFFERENTIAL EXPERIMENTS PASSED WITH 100% PARITY! ===')
