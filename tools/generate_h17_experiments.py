#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H17."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h17_campcec_haseditwork_experiment.py
(TOOLS / 'h17_campcec_haseditwork_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001FFADC CampCec_HasEditWork."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_campcec_haseditwork_candidate.cpp'
ORIG_ADDR = 0x001FFADC
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_CecEditWork_0043dad0': 0x0043DAD0,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_campcec_haseditwork.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h17_campcec_haseditwork_candidate']
    raw_mut, relocs_mut = funcs['h17_campcec_haseditwork_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, edit_work_ptr: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.mem_write(0x0043DAD0, struct.pack('<I', edit_work_ptr))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [
        0x0FFF3000,
        0x0FFF4000,
        0,
    ]

    for edit_work_ptr in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, edit_work_ptr)
        cand = run_simulation(code, cand_blob, CAND_ADDR, edit_work_ptr)
        mut = run_simulation(code, mut_blob, CAND_ADDR, edit_work_ptr)

        expected = 1 if edit_work_ptr != 0 else 0
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ptr=0x{edit_work_ptr:08X}: orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ptr=0x{edit_work_ptr:08X}')

    print(f'[PASS] h17_campcec_haseditwork: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 2. h17_campcec_copycarddata_experiment.py
(TOOLS / 'h17_campcec_copycarddata_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x001FF814 CampCec_CopyCardData."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_campcec_copycarddata_candidate.cpp'
ORIG_ADDR = 0x001FF814
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_campcec_copycarddata.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h17_campcec_copycarddata_candidate']
    raw_mut, _ = funcs['h17_campcec_copycarddata_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, w0: int, w1: int, w2: int) -> tuple[int, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    SRC_ADDR = STACK_BASE + 0x1000
    INNER_ADDR = STACK_BASE + 0x2000
    DST_ADDR = STACK_BASE + 0x3000

    uc.mem_write(SRC_ADDR + 0x2C, struct.pack('<I', INNER_ADDR))
    uc.mem_write(INNER_ADDR + 0x7C, struct.pack('<II', w0, w1))
    uc.mem_write(INNER_ADDR + 0x84, struct.pack('<I', w2))
    uc.mem_write(DST_ADDR, struct.pack('<III', 0, 0, 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SRC_ADDR)
    uc.reg_write(UC_ARM_REG_R1, 0)
    uc.reg_write(UC_ARM_REG_R2, DST_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)

    res = struct.unpack('<III', uc.mem_read(DST_ADDR, 12))
    return res

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [
        (0x11111111, 0x22222222, 0x33333333),
        (0x55AA55AA, 0xAA55AA55, 0x12345678),
        (0xFFFFFFFF, 0x00000000, 0x80000001),
    ]

    for w0, w1, w2 in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, w0, w1, w2)
        cand = run_simulation(code, cand_blob, CAND_ADDR, w0, w1, w2)
        mut = run_simulation(code, mut_blob, CAND_ADDR, w0, w1, w2)

        expected = (w0, w1, w2)
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({w0}, {w1}, {w2}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({w0}, {w1}, {w2})')

    print(f'[PASS] h17_campcec_copycarddata: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 3. h17_aoc_resultisready_experiment.py
(TOOLS / 'h17_aoc_resultisready_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002A17C0 Aoc_ResultIsReady."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_aoc_resultisready_candidate.cpp'
ORIG_ADDR = 0x002A17C0
ORIG_SIZE = 20
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_aoc_resultisready.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h17_aoc_resultisready_candidate']
    raw_mut, _ = funcs['h17_aoc_resultisready_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, status_byte: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    OBJ_ADDR = STACK_BASE + 0x1000

    uc.mem_write(OBJ_ADDR, struct.pack('<B', status_byte))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [0, 50, 99, 100, 101, 200, 255]

    for status_byte in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, status_byte)
        cand = run_simulation(code, cand_blob, CAND_ADDR, status_byte)
        mut = run_simulation(code, mut_blob, CAND_ADDR, status_byte)

        expected = 1 if status_byte >= 0x64 else 0
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for {status_byte}: orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for {status_byte}')

    print(f'[PASS] h17_aoc_resultisready: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 4. h17_aocapplet_isflag10000_experiment.py
(TOOLS / 'h17_aocapplet_isflag10000_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002A17D4 AocApplet_IsFlag10000."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_aocapplet_isflag10000_candidate.cpp'
ORIG_ADDR = 0x002A17D4
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_aocapplet_isflag10000.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h17_aocapplet_isflag10000_candidate']
    raw_mut, _ = funcs['h17_aocapplet_isflag10000_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, flags_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    APPLET_ADDR = STACK_BASE + 0x1000

    uc.mem_write(APPLET_ADDR + 0x754, struct.pack('<I', flags_val))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, APPLET_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [0, 0x10000, 0x10004, 0xFEFE0000, 0xFFFFFFFF]

    for flags_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, flags_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, flags_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, flags_val)

        expected = (flags_val & 0x10000) >> 16
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for 0x{flags_val:08X}: orig={orig}, cand={cand}, expected={expected}')
        if orig == mut and expected != 0:
            raise AssertionError(f'Mutation undetected for 0x{flags_val:08X}')

    print(f'[PASS] h17_aocapplet_isflag10000: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 5. h17_aoc_resultcopyvalue_experiment.py
(TOOLS / 'h17_aoc_resultcopyvalue_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002A17E4 Aoc_ResultCopyValue."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_aoc_resultcopyvalue_candidate.cpp'
ORIG_ADDR = 0x002A17E4
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_aoc_resultcopyvalue.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h17_aoc_resultcopyvalue_candidate']
    raw_mut, _ = funcs['h17_aoc_resultcopyvalue_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, inner_ptr: int, inner_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    TARGET_ADDR = STACK_BASE + 0x1000

    uc.mem_write(TARGET_ADDR, struct.pack('<I', inner_ptr))
    if inner_ptr != 0:
        uc.mem_write(inner_ptr, struct.pack('<I', inner_val))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, TARGET_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return struct.unpack('<I', uc.mem_read(TARGET_ADDR, 4))[0]

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [
        (0x0FFF3000, 0x12345678),
        (0x0FFF4000, 0x55AA55AA),
        (0, 0),
    ]

    for inner_ptr, inner_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, inner_ptr, inner_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, inner_ptr, inner_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, inner_ptr, inner_val)

        expected = inner_val if inner_ptr != 0 else 0
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({inner_ptr}, {inner_val}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut and expected != 0:
            raise AssertionError(f'Mutation undetected for ({inner_ptr}, {inner_val})')

    print(f'[PASS] h17_aoc_resultcopyvalue: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 6. h17_aoc_releaseglobal_experiment.py
(TOOLS / 'h17_aoc_releaseglobal_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002B2520 Aoc_ReleaseGlobal."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_aoc_releaseglobal_candidate.cpp'
ORIG_ADDR = 0x002B2520
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'AsdMem_Free': 0x002C4360,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_aoc_releaseglobal.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h17_aoc_releaseglobal_candidate']
    raw_mut, _ = funcs['h17_aoc_releaseglobal_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            offset = tgt - (CAND_ADDR + r.offset + 8)
            imm24 = (offset >> 2) & 0x00FFFFFF
            insn = 0xEB000000 | imm24
            struct.pack_into('<I', blob_cand, r.offset, insn)

    blob_mut = bytearray(raw_mut)
    blob_mut = bytearray(raw_mut)
    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, ptr_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    mod_image = bytearray(image)
    # Stub 0x002C4360: mov r0, #0x42; bx lr
    # 0xE3A00042: mov r0, #0x42
    # 0xE12FFF1E: bx lr
    stub = struct.pack('<II', 0xE3A00042, 0xE12FFF1E)
    mod_image[0x002C4360 - 0x00100000:0x002C4360 - 0x00100000 + 8] = stub

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, bytes(mod_image))

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, ptr_val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [0x0FFF3000, 0x0FFF4000, 0]

    for ptr_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, ptr_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, ptr_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, ptr_val)

        if orig != cand:
            raise AssertionError(f'Mismatch for ptr=0x{ptr_val:08X}: orig={orig}, cand={cand}')
        if orig == mut and ptr_val != 0:
            raise AssertionError(f'Mutation undetected for ptr=0x{ptr_val:08X}')

    print(f'[PASS] h17_aoc_releaseglobal: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 7. h17_campcec_getworkhandle_experiment.py
(TOOLS / 'h17_campcec_getworkhandle_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x002D73F4 CampCec_GetWorkHandle."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_campcec_getworkhandle_candidate.cpp'
ORIG_ADDR = 0x002D73F4
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_CecSettingWork_0043daf8': 0x0043DAF8,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_campcec_getworkhandle.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h17_campcec_getworkhandle_candidate']
    raw_mut, relocs_mut = funcs['h17_campcec_getworkhandle_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, setting_ptr: int, flag_byte: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    uc.mem_write(0x0043DAF8, struct.pack('<I', setting_ptr))
    if setting_ptr != 0:
        uc.mem_write(setting_ptr + 0x40, struct.pack('<B', flag_byte))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    cases = [
        (0x0FFF3000, 1),
        (0x0FFF3000, 42),
        (0x0FFF3000, 0),
    ]

    for setting_ptr, flag_byte in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, setting_ptr, flag_byte)
        cand = run_simulation(code, cand_blob, CAND_ADDR, setting_ptr, flag_byte)
        mut = run_simulation(code, mut_blob, CAND_ADDR, setting_ptr, flag_byte)

        expected = 1 if flag_byte != 0 else 0
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({setting_ptr}, {flag_byte}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({setting_ptr}, {flag_byte})')

    print(f'[PASS] h17_campcec_getworkhandle: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 8. h17_aocicon_init_experiment.py
(TOOLS / 'h17_aocicon_init_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x0038C248 AocIcon_Init."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h17_aocicon_init_candidate.cpp'
ORIG_ADDR = 0x0038C248
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    '_ZTV7AocIcon_00421e64': 0x00421E64,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h17_aocicon_init.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h17_aocicon_init_candidate']
    raw_mut, _ = funcs['h17_aocicon_init_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name in TARGET_SYMBOLS:
            tgt = TARGET_SYMBOLS[r.symbol_name]
            struct.pack_into('<I', blob_cand, r.offset, tgt)

    blob_mut = bytearray(raw_mut)
    return bytes(blob_cand), bytes(blob_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int) -> tuple[int, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    OBJ_ADDR = STACK_BASE + 0x1000

    uc.mem_write(OBJ_ADDR, struct.pack('<III', 0xCCCCCCCC, 0xCCCCCCCC, 0xCCCCCCCC))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, OBJ_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)

    f0, f4, f8 = struct.unpack('<III', uc.mem_read(OBJ_ADDR, 12))
    return f0, f4, f8

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h17_tests')

    orig = run_simulation(code, cand_blob, ORIG_ADDR)
    cand = run_simulation(code, cand_blob, CAND_ADDR)
    mut = run_simulation(code, mut_blob, CAND_ADDR)

    expected = (0x00421E64, 0, 0)
    if orig != cand or cand != expected:
        raise AssertionError(f'Mismatch: orig={orig}, cand={cand}, expected={expected}')
    if orig == mut:
        raise AssertionError('Mutation undetected')

    print(f'[PASS] h17_aocicon_init: 100% parity across vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

EXPERIMENTS = [
    'h17_campcec_haseditwork_experiment.py',
    'h17_campcec_copycarddata_experiment.py',
    'h17_aoc_resultisready_experiment.py',
    'h17_aocapplet_isflag10000_experiment.py',
    'h17_aoc_resultcopyvalue_experiment.py',
    'h17_aoc_releaseglobal_experiment.py',
    'h17_campcec_getworkhandle_experiment.py',
    'h17_aocicon_init_experiment.py',
]

def main():
    print("=== Executing all 8 Milestone H17 Unicorn Differential Experiments ===")
    all_passed = True
    for exp in EXPERIMENTS:
        p = TOOLS / exp
        print(f"--- Running {exp} ---")
        res = subprocess.run([sys.executable, str(p)], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[FAIL] {exp} failed:\n{res.stderr}\n{res.stdout}")
            all_passed = False
        else:
            print(res.stdout.strip())

    if all_passed:
        print("\n=== ALL 8 MILESTONE H17 EXPERIMENTS PASSED WITH 100% PARITY! ===")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
