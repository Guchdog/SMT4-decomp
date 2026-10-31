#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H12."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h12_battle_initturnsubsystems_experiment.py
(TOOLS / 'h12_battle_initturnsubsystems_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00123050 Battle_InitTurnSubsystems."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_initturnsubsystems_candidate.cpp'
ORIG_ADDR = 0x00123050
ORIG_SIZE = 64
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleTurnWork_0044e32c': 0x0044E32C,
    'sub_136FA4': 0x00136FA4,
    'sub_132FB8': 0x00132FB8,
    'sub_1423C0': 0x001423C0,
    'sub_13348C': 0x0013348C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_initturnsubsystems.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_initturnsubsystems_candidate']
    raw_mut, _ = funcs['h12_battle_initturnsubsystems_mutation']

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
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, arg_ptr: int) -> tuple[int, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub the 4 subroutines: bx lr
    bx_lr = struct.pack('<I', 0xE12FFF1E)
    uc.mem_write(0x00136FA4, bx_lr)
    uc.mem_write(0x00132FB8, bx_lr)
    uc.mem_write(0x001423C0, bx_lr)
    uc.mem_write(0x0013348C, bx_lr)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, arg_ptr)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    ret_val = uc.reg_read(UC_ARM_REG_R0)
    mem_out = uc.mem_read(0x0044E32C, 4)
    return ret_val, mem_out

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [0x08001000, 0x08002400, 0x08005000]
    for arg in cases:
        orig_r0, orig_mem = run_simulation(image, cand_blob, ORIG_ADDR, arg)
        cand_r0, cand_mem = run_simulation(image, cand_blob, CAND_ADDR, arg)
        assert orig_r0 == cand_r0, f'Return mismatch: {orig_r0} != {cand_r0}'
        assert orig_mem == cand_mem, f'Memory mismatch at 0x0044E32C'

    orig_r0, _ = run_simulation(image, cand_blob, ORIG_ADDR, cases[0])
    mut_r0, _ = run_simulation(image, mut_blob, CAND_ADDR, cases[0])
    assert orig_r0 != mut_r0, 'Mutation check failed'
    print('h12_battle_initturnsubsystems: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 2. h12_battle_getunitsmirkstate_experiment.py
(TOOLS / 'h12_battle_getunitsmirkstate_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00129C58 Battle_GetUnitSmirkState."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_getunitsmirkstate_candidate.cpp'
ORIG_ADDR = 0x00129C58
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleSmirkWork_00471a70': 0x00471A70,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_getunitsmirkstate.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_getunitsmirkstate_candidate']
    raw_mut, _ = funcs['h12_battle_getunitsmirkstate_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, smirk_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    SUB_ADDR = 0x08002000
    uc.mem_write(0x00471A70 + 0x1C, struct.pack('<I', SUB_ADDR))
    uc.mem_write(SUB_ADDR + 0x75, struct.pack('b', smirk_val))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    val = uc.reg_read(UC_ARM_REG_R0)
    if val >= 0x80000000:
        val -= 0x100000000
    return val

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [0, 1, -1, 42, -120]
    for s in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, s)
        cand = run_simulation(image, cand_blob, CAND_ADDR, s)
        assert orig == cand, f'Mismatch in GetUnitSmirkState ({s}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 1)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 1)
    assert orig != mut, 'Mutation failed'
    print('h12_battle_getunitsmirkstate: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 3. h12_battle_getsmirkactor_experiment.py
(TOOLS / 'h12_battle_getsmirkactor_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00129CBC Battle_GetSmirkActor."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_getsmirkactor_candidate.cpp'
ORIG_ADDR = 0x00129CBC
ORIG_SIZE = 20
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleSmirkWork_00471a70': 0x00471A70,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_getsmirkactor.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_getsmirkactor_candidate']
    raw_mut, _ = funcs['h12_battle_getsmirkactor_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, actor_ptr: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    uc.mem_write(0x00471A70 + 0xC, struct.pack('<I', actor_ptr))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [0x08003000, 0x08005000, 0]
    for act in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, act)
        cand = run_simulation(image, cand_blob, CAND_ADDR, act)
        assert orig == cand, f'Mismatch in GetSmirkActor ({act}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 0x08003000)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 0x08003000)
    assert orig != mut, 'Mutation failed'
    print('h12_battle_getsmirkactor: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 4. h12_battle_exchangesmirkslot_experiment.py
(TOOLS / 'h12_battle_exchangesmirkslot_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00129C70 Battle_ExchangeSmirkSlot."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_exchangesmirkslot_candidate.cpp'
ORIG_ADDR = 0x00129C70
ORIG_SIZE = 76
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleSmirkWork_00471a70': 0x00471A70,
    'sub_2C3AA8': 0x002C3AA8,
    'sub_2C3A24': 0x002C3A24,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_exchangesmirkslot.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_exchangesmirkslot_candidate']
    raw_mut, _ = funcs['h12_battle_exchangesmirkslot_mutation']

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
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, val: int, slot: int) -> tuple[int, bytes]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub lock/unlock: bx lr
    bx_lr = struct.pack('<I', 0xE12FFF1E)
    uc.mem_write(0x002C3AA8, bx_lr)
    uc.mem_write(0x002C3A24, bx_lr)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    SUB_ADDR = 0x08002000
    uc.mem_write(0x00471A70 + 0x1C, struct.pack('<I', SUB_ADDR))

    # Initialize 7 slots at SUB_ADDR + 0x10 with values [10, 20, 30, 40, 50, 60, 70]
    initial_slots = struct.pack('<IIIIIII', 10, 20, 30, 40, 50, 60, 70)
    uc.mem_write(SUB_ADDR + 0x10, initial_slots)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, val)
    uc.reg_write(UC_ARM_REG_R1, slot)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    ret_val = uc.reg_read(UC_ARM_REG_R0)
    slots_mem = uc.mem_read(SUB_ADDR + 0x10, 28)
    return ret_val, slots_mem

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [(99, 0), (88, 3), (77, 6), (66, 7), (55, 10)]
    for val, slot in cases:
        orig_r0, orig_m = run_simulation(image, cand_blob, ORIG_ADDR, val, slot)
        cand_r0, cand_m = run_simulation(image, cand_blob, CAND_ADDR, val, slot)
        assert orig_r0 == cand_r0, f'Mismatch in ExchangeSmirkSlot ret ({val}, {slot}): {orig_r0} != {cand_r0}'
        assert orig_m == cand_m, f'Mismatch in ExchangeSmirkSlot mem ({val}, {slot})'

    orig_r0, _ = run_simulation(image, cand_blob, ORIG_ADDR, 99, 0)
    mut_r0, _ = run_simulation(image, mut_blob, CAND_ADDR, 99, 0)
    assert orig_r0 != mut_r0, 'Mutation check failed'
    print('h12_battle_exchangesmirkslot: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 5. h12_battle_initturndata_experiment.py
(TOOLS / 'h12_battle_initturndata_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00136FA4 Battle_InitTurnData."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_initturndata_candidate.cpp'
ORIG_ADDR = 0x00136FA4
ORIG_SIZE = 40
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleStateWork_004655c0': 0x004655C0,
    'sub_1422F8': 0x001422F8,
}

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_initturndata.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_initturndata_candidate']
    raw_mut, _ = funcs['h12_battle_initturndata_mutation']

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
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, init_flags: int) -> tuple[int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub tail call sub_1422F8: bx lr
    bx_lr = struct.pack('<I', 0xE12FFF1E)
    uc.mem_write(0x001422F8, bx_lr)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    ARG_PTR = 0x08001000
    STATE_ADDR = 0x08002000
    uc.mem_write(0x004655C0, struct.pack('<I', STATE_ADDR))
    uc.mem_write(STATE_ADDR + 0x770, struct.pack('<I', init_flags))
    uc.mem_write(ARG_PTR, struct.pack('<I', 0))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, ARG_PTR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    arg_val = struct.unpack('<I', uc.mem_read(ARG_PTR, 4))[0]
    flag_val = struct.unpack('<I', uc.mem_read(STATE_ADDR + 0x770, 4))[0]
    return arg_val, flag_val

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [0x00000000, 0x00002000, 0x00010000, 0x00013000, 0xFFFFFFFF]
    for flags in cases:
        orig_arg, orig_flags = run_simulation(image, cand_blob, ORIG_ADDR, flags)
        cand_arg, cand_flags = run_simulation(image, cand_blob, CAND_ADDR, flags)
        assert orig_arg == cand_arg, f'Mismatch in Battle_InitTurnData arg ({flags:#x}): {orig_arg} != {cand_arg}'
        assert orig_flags == cand_flags, f'Mismatch in Battle_InitTurnData flags ({flags:#x}): {orig_flags:#x} != {cand_flags:#x}'

    orig_arg, orig_flags = run_simulation(image, cand_blob, ORIG_ADDR, 0)
    mut_arg, mut_flags = run_simulation(image, mut_blob, CAND_ADDR, 0)
    assert orig_arg != mut_arg or orig_flags != mut_flags, 'Mutation failed'
    print('h12_battle_initturndata: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 6. h12_result_cleanup_experiment.py
(TOOLS / 'h12_result_cleanup_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001C87D8 Result_Cleanup."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_result_cleanup_candidate.cpp'
ORIG_ADDR = 0x001C87D8
ORIG_SIZE = 156
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_ResultWork_0044dc20': 0x0044DC20,
    'sub_2A755C': 0x002A755C,
    'sub_2C4360': 0x002C4360,
    'sub_2C0128': 0x002C0128,
    'sub_2A497C': 0x002A497C,
    'sub_2AEB2C': 0x002AEB2C,
}

def branch_word(src: int, tgt: int, is_bl: bool = True) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_result_cleanup.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_result_cleanup_candidate']
    raw_mut, relocs_mut = funcs['h12_result_cleanup_mutation']

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

    return bytes(blob_cand), raw_cand, bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, has_work: bool) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Stub the 5 subroutines: bx lr
    bx_lr = struct.pack('<I', 0xE12FFF1E)
    uc.mem_write(0x002A755C, bx_lr)
    uc.mem_write(0x002C4360, bx_lr)
    uc.mem_write(0x002C0128, bx_lr)
    uc.mem_write(0x002A497C, bx_lr)
    uc.mem_write(0x002AEB2C, bx_lr)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    WORK_ADDR = 0x08000000
    if has_work:
        uc.mem_write(0x0044DC20, struct.pack('<I', WORK_ADDR))
        # Set pointers inside work structure
        uc.mem_write(WORK_ADDR + 0x3564, struct.pack('<I', 0x08004000))
        uc.mem_write(WORK_ADDR + 0x3568, struct.pack('<I', 0x08005000))
        uc.mem_write(WORK_ADDR + 0x356C, struct.pack('<I', 0x08006000))
        uc.mem_write(WORK_ADDR + 0x3570, struct.pack('<I', 0x08007000))
    else:
        uc.mem_write(0x0044DC20, struct.pack('<I', 0))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.mem_read(0x0044DC20, 4)

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    for hw in [True, False]:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, hw)
        cand = run_simulation(image, cand_blob, CAND_ADDR, hw)
        assert orig == cand, f'Mismatch in Result_Cleanup (has_work={hw}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, True)
    mut = run_simulation(image, mut_blob, CAND_ADDR, True)
    assert orig != mut, 'Mutation failed'
    print('h12_result_cleanup: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 7. h12_battle_isunitdefeated_experiment.py
(TOOLS / 'h12_battle_isunitdefeated_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0028DE4C Battle_IsUnitDefeated."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_isunitdefeated_candidate.cpp'
ORIG_ADDR = 0x0028DE4C
ORIG_SIZE = 56
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_isunitdefeated.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h12_battle_isunitdefeated_candidate']
    raw_mut, _ = funcs['h12_battle_isunitdefeated_mutation']
    return raw_cand, raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, flags: int, hp: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    UNIT_ADDR = 0x08001000
    uc.mem_write(UNIT_ADDR + 0x44A0, struct.pack('<I', flags))
    uc.mem_write(UNIT_ADDR + 0xC4, struct.pack('<i', hp))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, UNIT_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    cases = [
        (0x02, 100),       # bit 1 set -> 0
        (0x02000000, 100), # bit 25 set -> 1
        (0x02000002, 100), # both set -> bit 1 takes precedence -> 0
        (0x00, 0),         # hp == 0 -> 0
        (0x00, -10),       # hp < 0 -> 1
        (0x00, 100),       # alive and active -> 0
        (0x01, 500),       # other flags -> 0
    ]
    for flags, hp in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, flags, hp)
        cand = run_simulation(image, cand_blob, CAND_ADDR, flags, hp)
        assert orig == cand, f'Mismatch in Battle_IsUnitDefeated (flags={flags:#x}, hp={hp}): {orig} != {cand}'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 0x00, -10)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 0x00, -10)
    assert orig != mut, 'Mutation failed'
    print('h12_battle_isunitdefeated: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 8. h12_battle_resetunitstatebuffer_experiment.py
(TOOLS / 'h12_battle_resetunitstatebuffer_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00215938 Battle_ResetUnitStateBuffer."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h12_battle_resetunitstatebuffer_candidate.cpp'
ORIG_ADDR = 0x00215938
ORIG_SIZE = 32
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_BattleUnitTable_00478000': 0x00478000,
    'sub_2BCF58': 0x002BCF58,
}

def branch_word(src: int, tgt: int, is_bl: bool = False) -> int:
    offset = tgt - (src + 8)
    imm24 = (offset >> 2) & 0x00FFFFFF
    opcode = 0xEB000000 if is_bl else 0xEA000000
    return opcode | imm24

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h12_battle_resetunitstatebuffer.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h12_battle_resetunitstatebuffer_candidate']
    raw_mut, _ = funcs['h12_battle_resetunitstatebuffer_mutation']

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
    return bytes(blob_cand), raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, idx: int, src_data: bytes) -> bytes:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    # Mock sub_2BCF58 (memcpy: r0=dst, r1=src, r2=len):
    # loop: ldrb r3, [r1], #1; strb r3, [r0], #1; subs r2, r2, #1; bne loop; bx lr
    mock_memcpy = struct.pack('<IIIII',
        0xE4D13001,  # ldrb r3, [r1], #1
        0xE4C03001,  # strb r3, [r0], #1
        0xE2522001,  # subs r2, r2, #1
        0x1AFFFFFC,  # bne -4
        0xE12FFF1E   # bx lr
    )
    uc.mem_write(0x002BCF58, mock_memcpy)

    MEM_BASE = 0x08000000
    uc.mem_map(MEM_BASE, 0x10000, unicorn.UC_PROT_ALL)

    SRC_ADDR = 0x08002000
    uc.mem_write(SRC_ADDR, src_data)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, idx)
    uc.reg_write(UC_ARM_REG_R1, SRC_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=500)
    dest_addr = 0x00478000 + idx * 328 + 0x2C
    return uc.mem_read(dest_addr, 0x90)

def main():
    image = CODE_PATH.read_bytes()
    cand_blob, _, mut_blob = build_candidates(ROOT / 'build/h12_test')

    data_sample = bytes([(i * 7 + 13) & 0xFF for i in range(0x90)])
    cases = [0, 1, 3]
    for idx in cases:
        orig = run_simulation(image, cand_blob, ORIG_ADDR, idx, data_sample)
        cand = run_simulation(image, cand_blob, CAND_ADDR, idx, data_sample)
        assert orig == cand, f'Mismatch in Battle_ResetUnitStateBuffer ({idx})'

    orig = run_simulation(image, cand_blob, ORIG_ADDR, 0, data_sample)
    mut = run_simulation(image, mut_blob, CAND_ADDR, 0, data_sample)
    assert orig != mut, 'Mutation failed'
    print('h12_battle_resetunitstatebuffer: ALL CASES PASSED')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

print("All 8 H12 experiment scripts written.")

# Execute all 8 scripts
scripts = [
    'h12_battle_initturnsubsystems_experiment.py',
    'h12_battle_getunitsmirkstate_experiment.py',
    'h12_battle_getsmirkactor_experiment.py',
    'h12_battle_exchangesmirkslot_experiment.py',
    'h12_battle_initturndata_experiment.py',
    'h12_result_cleanup_experiment.py',
    'h12_battle_isunitdefeated_experiment.py',
    'h12_battle_resetunitstatebuffer_experiment.py',
]

print("=== Executing all 8 Milestone H12 Unicorn Differential Experiments ===")
all_ok = True
for s in scripts:
    res = subprocess.run([sys.executable, str(TOOLS / s)], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[PASSED] {s:<45} : {res.stdout.strip()}")
    else:
        print(f"[FAILED] {s:<45} : {res.stderr.strip()}")
        all_ok = False

if all_ok:
    print("\nALL 8 H12 DIFFERENTIAL EXPERIMENTS PASSED WITH 100% PARITY!")
else:
    sys.exit(1)
