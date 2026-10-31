#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H14."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h14_asdeffect_lockenter_experiment.py
(TOOLS / 'h14_asdeffect_lockenter_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00152D7C AsdEffect_LockEnter."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdeffect_lockenter_candidate.cpp'
ORIG_ADDR = 0x00152D7C
ORIG_SIZE = 48
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdEffectLockWork_00465120': 0x00465120,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdeffect_lockenter.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdeffect_lockenter_candidate']
    raw_mut, relocs_mut = funcs['h14_asdeffect_lockenter_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, init_depth: int, init_saved: int, init_eff: int, new_id: int) -> tuple[int, int, int]:
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

    INNER_BUF = MEM_BASE + 0x1000
    uc.mem_write(INNER_BUF + 0x38, struct.pack('<H', init_eff))

    # Setup 0x00465120
    uc.mem_write(0x00465120, struct.pack('<HH', init_saved, init_depth))
    uc.mem_write(0x00465120 + 8, struct.pack('<I', INNER_BUF))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, new_id)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)

    out_saved, out_depth = struct.unpack('<HH', uc.mem_read(0x00465120, 4))
    out_eff = struct.unpack('<H', uc.mem_read(INNER_BUF + 0x38, 2))[0]
    return out_depth, out_saved, out_eff

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    cases = [
        (0, 0, 0x1111, 0x2222), # depth 0 -> saves 0x1111, depth becomes 1, eff becomes 0x2222
        (1, 0x1111, 0x2222, 0x3333), # depth 1 -> keeps saved 0x1111, depth becomes 2, eff becomes 0x3333
        (5, 0xAAAA, 0xBBBB, 0xCCCC), # depth 5 -> keeps saved 0xAAAA, depth becomes 6, eff becomes 0xCCCC
    ]

    for init_d, init_s, init_e, new_id in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, init_d, init_s, init_e, new_id)
        cand = run_simulation(code, cand_blob, CAND_ADDR, init_d, init_s, init_e, new_id)
        mut = run_simulation(code, mut_blob, CAND_ADDR, init_d, init_s, init_e, new_id)

        if orig != cand:
            raise AssertionError(f'Mismatch for d={init_d}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for d={init_d}')

    print(f'[PASS] h14_asdeffect_lockenter: 100% parity across {len(cases)} cases, mutation sensitivity confirmed.')

if __name__ == '__main__':
    main()
''')

# 2. h14_asdeffect_lockleave_experiment.py
(TOOLS / 'h14_asdeffect_lockleave_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00152DAC AsdEffect_LockLeave."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdeffect_lockleave_candidate.cpp'
ORIG_ADDR = 0x00152DAC
ORIG_SIZE = 56
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdEffectLockWork_00465120': 0x00465120,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdeffect_lockleave.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdeffect_lockleave_candidate']
    raw_mut, relocs_mut = funcs['h14_asdeffect_lockleave_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, init_depth: int, init_saved: int, init_eff: int) -> tuple[int, int]:
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

    INNER_BUF = MEM_BASE + 0x1000
    uc.mem_write(INNER_BUF + 0x38, struct.pack('<H', init_eff))

    # Setup 0x00465120
    uc.mem_write(0x00465120, struct.pack('<HH', init_saved, init_depth))
    uc.mem_write(0x00465120 + 8, struct.pack('<I', INNER_BUF))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)

    out_depth = struct.unpack('<H', uc.mem_read(0x00465122, 2))[0]
    out_eff = struct.unpack('<H', uc.mem_read(INNER_BUF + 0x38, 2))[0]
    return out_depth, out_eff

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    cases = [
        (0, 0x1111, 0x2222), # depth 0 -> remains 0, eff remains 0x2222
        (1, 0x1111, 0x2222), # depth 1 -> depth 0, restores saved 0x1111 into eff
        (3, 0x1111, 0x2222), # depth 3 -> depth 2, eff unchanged 0x2222
    ]

    for init_d, init_s, init_e in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, init_d, init_s, init_e)
        cand = run_simulation(code, cand_blob, CAND_ADDR, init_d, init_s, init_e)
        mut = run_simulation(code, mut_blob, CAND_ADDR, init_d, init_s, init_e)

        if orig != cand:
            raise AssertionError(f'Mismatch for d={init_d}: orig={orig}, cand={cand}')
        if init_d > 0 and orig == mut:
            raise AssertionError(f'Mutation undetected for d={init_d}')

    print(f'[PASS] h14_asdeffect_lockleave: 100% parity across {len(cases)} cases, restoration confirmed.')

if __name__ == '__main__':
    main()
''')

# 3. h14_asdres_getcontext_experiment.py
(TOOLS / 'h14_asdres_getcontext_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002C31BC AsdRes_GetContext."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdres_getcontext_candidate.cpp'
ORIG_ADDR = 0x002C31BC
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdResManager_00465170': 0x00465170,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdres_getcontext.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdres_getcontext_candidate']
    raw_mut, _ = funcs['h14_asdres_getcontext_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)

    return bytes(blob_cand), raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, flag: int, active_ctx: int, default_ctx: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # 0x00465170: flag at +0, active_ctx at +8, default_ctx at +0xC
    uc.mem_write(0x00465170, bytes([flag]))
    uc.mem_write(0x00465170 + 8, struct.pack('<II', active_ctx, default_ctx))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    cases = [
        (0, 0x11112222, 0x33334444), # flag 0 -> default_ctx 0x33334444
        (1, 0x11112222, 0x33334444), # flag 1 -> active_ctx 0x11112222
        (0xFF, 0xAAAABBBB, 0xCCCCDDDD), # flag 255 -> active_ctx 0xAAAABBBB
    ]

    for flag, act, dflt in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, flag, act, dflt)
        cand = run_simulation(code, cand_blob, CAND_ADDR, flag, act, dflt)
        mut = run_simulation(code, mut_blob, CAND_ADDR, flag, act, dflt)

        if orig != cand:
            raise AssertionError(f'Mismatch for flag={flag}: orig=0x{orig:08X}, cand=0x{cand:08X}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for flag={flag}')

    print(f'[PASS] h14_asdres_getcontext: 100% parity across {len(cases)} cases, context routing verified.')

if __name__ == '__main__':
    main()
''')

# 4. h14_asdgpu_heapsize_experiment.py
(TOOLS / 'h14_asdgpu_heapsize_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002C3B88 AsdGpu_HeapSize."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdgpu_heapsize_candidate.cpp'
ORIG_ADDR = 0x002C3B88
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdGpuWork_00471b48': 0x00471B48,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdgpu_heapsize.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdgpu_heapsize_candidate']
    raw_mut, _ = funcs['h14_asdgpu_heapsize_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)

    return bytes(blob_cand), raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, heap_sz: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # 0x00471B48 + 4 = heap_size
    uc.mem_write(0x00471B48 + 4, struct.pack('<I', heap_sz))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    sizes = [0x01000000, 0x02800000, 0x04000000, 0x7FFFFFFF]
    for sz in sizes:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, sz)
        cand = run_simulation(code, cand_blob, CAND_ADDR, sz)
        mut = run_simulation(code, mut_blob, CAND_ADDR, sz)

        if orig != cand:
            raise AssertionError(f'Mismatch for sz=0x{sz:08X}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for sz=0x{sz:08X}')

    print(f'[PASS] h14_asdgpu_heapsize: 100% parity across {len(sizes)} heap sizes, mutation verified.')

if __name__ == '__main__':
    main()
''')

# 5. h14_asdtext_setcodefield1c_experiment.py
(TOOLS / 'h14_asdtext_setcodefield1c_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0010A6FC AsdText_SetCodeField1C."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdtext_setcodefield1c_candidate.cpp'
ORIG_ADDR = 0x0010A6FC
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdTextCode_00464d48': 0x00464D48,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdtext_setcodefield1c.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdtext_setcodefield1c_candidate']
    raw_mut, relocs_mut = funcs['h14_asdtext_setcodefield1c_mutation']

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

    uc.mem_write(0x00464D48 + 0x1C, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return struct.unpack('<I', uc.mem_read(0x00464D48 + 0x1C, 4))[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    vals = [0, 1, 0x12345678, 0xFFFFFFFF]
    for v in vals:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)

        if orig != cand or cand != v:
            raise AssertionError(f'Mismatch for v=0x{v:08X}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for v=0x{v:08X}')

    print(f'[PASS] h14_asdtext_setcodefield1c: 100% parity across {len(vals)} values, field store confirmed.')

if __name__ == '__main__':
    main()
''')

# 6. h14_asdtext_setcodefield14_experiment.py
(TOOLS / 'h14_asdtext_setcodefield14_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0010AF38 AsdText_SetCodeField14."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdtext_setcodefield14_candidate.cpp'
ORIG_ADDR = 0x0010AF38
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdTextCode_00464d48': 0x00464D48,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdtext_setcodefield14.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdtext_setcodefield14_candidate']
    raw_mut, relocs_mut = funcs['h14_asdtext_setcodefield14_mutation']

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

    uc.mem_write(0x00464D48 + 0x14, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return struct.unpack('<I', uc.mem_read(0x00464D48 + 0x14, 4))[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    vals = [0, 42, 0xDEADBEEF, 0x7FFFFFFF]
    for v in vals:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)

        if orig != cand or cand != v:
            raise AssertionError(f'Mismatch for v=0x{v:08X}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for v=0x{v:08X}')

    print(f'[PASS] h14_asdtext_setcodefield14: 100% parity across {len(vals)} values, field store confirmed.')

if __name__ == '__main__':
    main()
''')

# 7. h14_asdtext_setcodefield30_experiment.py
(TOOLS / 'h14_asdtext_setcodefield30_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0010B340 AsdText_SetCodeField30."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_asdtext_setcodefield30_candidate.cpp'
ORIG_ADDR = 0x0010B340
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_AsdTextCode_00464d48': 0x00464D48,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_asdtext_setcodefield30.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h14_asdtext_setcodefield30_candidate']
    raw_mut, relocs_mut = funcs['h14_asdtext_setcodefield30_mutation']

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

    uc.mem_write(0x00464D48 + 0x30, struct.pack('<I', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    return struct.unpack('<I', uc.mem_read(0x00464D48 + 0x30, 4))[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    vals = [0, 999, 0xCAFEBABE, 0x80000000]
    for v in vals:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, v)
        cand = run_simulation(code, cand_blob, CAND_ADDR, v)
        mut = run_simulation(code, mut_blob, CAND_ADDR, v)

        if orig != cand or cand != v:
            raise AssertionError(f'Mismatch for v=0x{v:08X}: orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for v=0x{v:08X}')

    print(f'[PASS] h14_asdtext_setcodefield30: 100% parity across {len(vals)} values, field store confirmed.')

if __name__ == '__main__':
    main()
''')

# 8. h14_texturestreamer_compare_experiment.py
(TOOLS / 'h14_texturestreamer_compare_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x003878C0 TextureStreamer_Compare."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h14_texturestreamer_compare_candidate.cpp'
ORIG_ADDR = 0x003878C0
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h14_texturestreamer_compare.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h14_texturestreamer_compare_candidate']
    raw_mut, _ = funcs['h14_texturestreamer_compare_mutation']
    return raw_cand, raw_mut

def run_simulation(image: bytes, cand_blob: bytes, entry: int, val_a: int, val_b: int) -> int:
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

    PTR_A = MEM_BASE + 0x100
    PTR_B = MEM_BASE + 0x200
    uc.mem_write(PTR_A, struct.pack('<H', val_a))
    uc.mem_write(PTR_B, struct.pack('<H', val_b))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, PTR_A)
    uc.reg_write(UC_ARM_REG_R1, PTR_B)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=100)
    # Read signed 32-bit result
    ret = uc.reg_read(UC_ARM_REG_R0)
    if ret >= 0x80000000:
        ret -= 0x100000000
    return ret

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h14_tests')

    pairs = [
        (10, 10),    # 0
        (50, 20),    # +30
        (20, 50),    # -30
        (0, 0xFFFF), # negative
        (0xFFFF, 0), # positive
    ]

    for a, b in pairs:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, a, b)
        cand = run_simulation(code, cand_blob, CAND_ADDR, a, b)
        mut = run_simulation(code, mut_blob, CAND_ADDR, a, b)

        if orig != cand or cand != (a - b):
            raise AssertionError(f'Mismatch for ({a}, {b}): orig={orig}, cand={cand}')
        if a != b and orig == mut:
            raise AssertionError(f'Mutation undetected for ({a}, {b})')

    print(f'[PASS] h14_texturestreamer_compare: 100% parity across {len(pairs)} pairs, comparator verified.')

if __name__ == '__main__':
    main()
''')

# Execute all 8 scripts
scripts = [
    'h14_asdeffect_lockenter_experiment.py',
    'h14_asdeffect_lockleave_experiment.py',
    'h14_asdres_getcontext_experiment.py',
    'h14_asdgpu_heapsize_experiment.py',
    'h14_asdtext_setcodefield1c_experiment.py',
    'h14_asdtext_setcodefield14_experiment.py',
    'h14_asdtext_setcodefield30_experiment.py',
    'h14_texturestreamer_compare_experiment.py',
]

print('=== Executing all 8 Unicorn differential validation experiments for Milestone H14 ===')
for s in scripts:
    res = subprocess.run([sys.executable, str(TOOLS / s)], capture_output=True, text=True)
    if res.returncode != 0:
        print(f'FAIL in {s}:')
        print(res.stdout)
        print(res.stderr)
        sys.exit(1)
    else:
        print(res.stdout.strip())

print('=== ALL 8 H14 DIFFERENTIAL EXPERIMENTS PASSED WITH 100% PARITY! ===')
