#!/usr/bin/env python3
"""Generate and execute all 8 Unicorn offline differential experiment scripts for Milestone H16."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'

# 1. h16_asdsoundeffect_setbuffer_experiment.py
(TOOLS / 'h16_asdsoundeffect_setbuffer_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00110C2C AsdSoundEffect_SetBuffer."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsoundeffect_setbuffer_candidate.cpp'
ORIG_ADDR = 0x00110C2C
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsoundeffect_setbuffer.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h16_asdsoundeffect_setbuffer_candidate']
    raw_mut, _ = funcs['h16_asdsoundeffect_setbuffer_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, buf_ptr: int, size_val: int) -> tuple[int, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    SELF_ADDR = STACK_BASE + 0x4000

    uc.mem_write(SELF_ADDR + 0x1C, struct.pack('<II', 0, 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, buf_ptr)
    uc.reg_write(UC_ARM_REG_R2, size_val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)

    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    stored_buf, stored_sz = struct.unpack('<II', uc.mem_read(SELF_ADDR + 0x1C, 8))
    return ret_r0, stored_buf, stored_sz

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (0x0FFF5000, 1024),
        (0x0FFF6000, 4096),
        (0, 512),
        (0, 0),
    ]

    for buf_ptr, size_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, buf_ptr, size_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, buf_ptr, size_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, buf_ptr, size_val)

        if orig != cand:
            raise AssertionError(f'Mismatch for ({buf_ptr}, {size_val}): orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({buf_ptr}, {size_val})')

    print(f'[PASS] h16_asdsoundeffect_setbuffer: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 2. h16_asdsoundeffect_getbuffersize_experiment.py
(TOOLS / 'h16_asdsoundeffect_getbuffersize_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00110C44 AsdSoundEffect_GetBufferSize."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsoundeffect_getbuffersize_candidate.cpp'
ORIG_ADDR = 0x00110C44
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsoundeffect_getbuffersize.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h16_asdsoundeffect_getbuffersize_candidate']
    raw_mut, _ = funcs['h16_asdsoundeffect_getbuffersize_mutation']
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
    SELF_ADDR = STACK_BASE + 0x4000

    uc.mem_write(SELF_ADDR + 0x44, struct.pack('<I', rate))
    uc.mem_write(SELF_ADDR + 0x5D, struct.pack('<B', channels))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (11025, 1),
        (22050, 2),
        (44100, 2),
        (48000, 2),
        (32000, 1),
    ]

    for rate, channels in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, rate, channels)
        cand = run_simulation(code, cand_blob, CAND_ADDR, rate, channels)
        mut = run_simulation(code, mut_blob, CAND_ADDR, rate, channels)

        expected = ((rate * channels * 5) << 7) + 0x20
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({rate}, {channels}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({rate}, {channels})')

    print(f'[PASS] h16_asdsoundeffect_getbuffersize: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 3. h16_asdsoundeffect2_setbuffer_experiment.py
(TOOLS / 'h16_asdsoundeffect2_setbuffer_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00121150 AsdSoundEffect2_SetBuffer."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsoundeffect2_setbuffer_candidate.cpp'
ORIG_ADDR = 0x00121150
ORIG_SIZE = 24
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsoundeffect2_setbuffer.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h16_asdsoundeffect2_setbuffer_candidate']
    raw_mut, _ = funcs['h16_asdsoundeffect2_setbuffer_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, buf_ptr: int, size_val: int) -> tuple[int, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    SELF_ADDR = STACK_BASE + 0x4000

    uc.mem_write(SELF_ADDR + 0x30, struct.pack('<II', 0, 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(UC_ARM_REG_R1, buf_ptr)
    uc.reg_write(UC_ARM_REG_R2, size_val)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)

    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    stored_buf, stored_sz = struct.unpack('<II', uc.mem_read(SELF_ADDR + 0x30, 8))
    return ret_r0, stored_buf, stored_sz

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (0x0FFF5000, 2048),
        (0x0FFF6000, 8192),
        (0, 1024),
        (0, 0),
    ]

    for buf_ptr, size_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, buf_ptr, size_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, buf_ptr, size_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, buf_ptr, size_val)

        if orig != cand:
            raise AssertionError(f'Mismatch for ({buf_ptr}, {size_val}): orig={orig}, cand={cand}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for ({buf_ptr}, {size_val})')

    print(f'[PASS] h16_asdsoundeffect2_setbuffer: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 4. h16_asdsound_getdatasize_experiment.py
(TOOLS / 'h16_asdsound_getdatasize_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00121F20 AsdSound_GetDataSize."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsound_getdatasize_candidate.cpp'
ORIG_ADDR = 0x00121F20
ORIG_SIZE = 32
CAND_ADDR = 0x00600000

STUB_TARGET = 0x00141924

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsound_getdatasize.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h16_asdsound_getdatasize_candidate']
    raw_mut, _ = funcs['h16_asdsound_getdatasize_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name == 'g_sound_sub_00141924':
            # Relative branch or absolute target
            # bl instruction encoding in ARM:
            offset = STUB_TARGET - (CAND_ADDR + r.offset + 8)
            imm24 = (offset >> 2) & 0x00FFFFFF
            insn = 0xEB000000 | imm24
            struct.pack_into('<I', blob_cand, r.offset, insn)

    return bytes(blob_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, count_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    mod_image = bytearray(image)
    # Stub 0x00141924 with `bx lr` (0xE12FFF1E)
    struct.pack_into('<I', mod_image, STUB_TARGET - 0x00100000, 0xE12FFF1E)

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
    uc.reg_write(UC_ARM_REG_R0, 0x0FFF1234) # this
    uc.reg_write(UC_ARM_REG_R1, count_val)   # obj -> stub returns count_val in r0

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [0, 1, 2, 5, 10, 255]

    for count_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, count_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, count_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, count_val)

        expected = (4 + (count_val * 4) + 3) & ~3
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for {count_val}: orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for {count_val}')

    print(f'[PASS] h16_asdsound_getdatasize: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 5. h16_asdsound_getsamplebytes_experiment.py
(TOOLS / 'h16_asdsound_getsamplebytes_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00122094 AsdSound_GetSampleBytes."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asdsound_getsamplebytes_candidate.cpp'
ORIG_ADDR = 0x00122094
ORIG_SIZE = 48
CAND_ADDR = 0x00600000

STUB_TARGET = 0x001419BC

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asdsound_getsamplebytes.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h16_asdsound_getsamplebytes_candidate']
    raw_mut, _ = funcs['h16_asdsound_getsamplebytes_mutation']

    blob_cand = bytearray(raw_cand)
    for r in relocs_cand:
        if r.symbol_name == 'g_sound_sub_001419bc':
            offset = STUB_TARGET - (CAND_ADDR + r.offset + 8)
            imm24 = (offset >> 2) & 0x00FFFFFF
            insn = 0xEB000000 | imm24
            struct.pack_into('<I', blob_cand, r.offset, insn)

    return bytes(blob_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, sample_count: int, success: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    mod_image = bytearray(image)
    # Stub 0x001419BC:
    # str r0, [r1, #0x10]
    # mov r0, r2 (success)
    # bx lr
    # Instructions:
    # 0xE5810010: str r0, [r1, #0x10]
    # 0xE1A00002: mov r0, r2
    # 0xE12FFF1E: bx lr
    stub_bytes = struct.pack('<III', 0xE5810010, 0xE1A00002, 0xE12FFF1E)
    mod_image[STUB_TARGET - 0x00100000:STUB_TARGET - 0x00100000 + 12] = stub_bytes

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
    uc.reg_write(UC_ARM_REG_R0, 0x0FFF1234)   # this
    uc.reg_write(UC_ARM_REG_R1, sample_count) # obj passed as r0 into stub
    uc.reg_write(UC_ARM_REG_R2, success)      # stub returns success flag

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (10, 1),
        (50, 1),
        (100, 1),
        (200, 0), # failure returns 0
    ]

    for sample_count, success in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, sample_count, success)
        cand = run_simulation(code, cand_blob, CAND_ADDR, sample_count, success)
        mut = run_simulation(code, mut_blob, CAND_ADDR, sample_count, success)

        expected = (sample_count * 5) << 13 if success else 0
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for ({sample_count}, {success}): orig={orig}, cand={cand}, expected={expected}')
        if orig == mut and expected != 0:
            raise AssertionError(f'Mutation undetected for ({sample_count}, {success})')

    print(f'[PASS] h16_asdsound_getsamplebytes: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 6. h16_asddata_getbase_experiment.py
(TOOLS / 'h16_asddata_getbase_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00128F34 AsdData_GetBase."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asddata_getbase_candidate.cpp'
ORIG_ADDR = 0x00128F34
ORIG_SIZE = 16
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asddata_getbase.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h16_asddata_getbase_candidate']
    raw_mut, _ = funcs['h16_asddata_getbase_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, offset_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    SELF_ADDR = STACK_BASE + 0x4000

    uc.mem_write(SELF_ADDR + 0x18, struct.pack('<I', offset_val))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [0, 4, 16, 0x100, 0x1000]

    for offset_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, offset_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, offset_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, offset_val)

        expected = 0x0FFF4000 + 8 + offset_val
        if orig != cand or cand != expected:
            raise AssertionError(f'Mismatch for {offset_val}: orig={orig}, cand={cand}, expected={expected}')
        if orig == mut:
            raise AssertionError(f'Mutation undetected for {offset_val}')

    print(f'[PASS] h16_asddata_getbase: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 7. h16_asddata_getcount_experiment.py
(TOOLS / 'h16_asddata_getcount_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00128F44 AsdData_GetCount."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_asddata_getcount_candidate.cpp'
ORIG_ADDR = 0x00128F44
ORIG_SIZE = 20
CAND_ADDR = 0x00600000

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_asddata_getcount.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, _ = funcs['h16_asddata_getcount_candidate']
    raw_mut, _ = funcs['h16_asddata_getcount_mutation']
    return bytes(raw_cand), bytes(raw_mut)

def run_simulation(image: bytes, cand_blob: bytes, entry: int, count_val: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000
    SELF_ADDR = STACK_BASE + 0x4000

    OFFSET_VAL = 0x20
    uc.mem_write(SELF_ADDR + 0x18, struct.pack('<I', OFFSET_VAL))
    # base = self + 8 + 0x20 = self + 0x28
    # base + 0x14 = self + 0x3C
    uc.mem_write(SELF_ADDR + 0x3C, struct.pack('<I', count_val))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, SELF_ADDR)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)
    return uc.reg_read(UC_ARM_REG_R0)

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [0, 1, 42, 0x12345678, 0xFFFFFFFF]

    for count_val in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, count_val)
        cand = run_simulation(code, cand_blob, CAND_ADDR, count_val)
        mut = run_simulation(code, mut_blob, CAND_ADDR, count_val)

        if orig != cand or cand != count_val:
            raise AssertionError(f'Mismatch for {count_val}: orig={orig}, cand={cand}')
        if orig == mut and count_val != 0:
            raise AssertionError(f'Mutation undetected for {count_val}')

    print(f'[PASS] h16_asddata_getcount: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

# 8. h16_statusdown_setactivesoundid_experiment.py
(TOOLS / 'h16_statusdown_setactivesoundid_experiment.py').write_text('''#!/usr/bin/env python3
"""Offline ARM differential validation for 0x00215A44 StatusDown_SetActiveSoundId."""
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
SRC_PATH = ROOT / 'experiments/semantic_equivalence/h16_statusdown_setactivesoundid_candidate.cpp'
ORIG_ADDR = 0x00215A44
ORIG_SIZE = 28
CAND_ADDR = 0x00600000

TARGET_SYMBOLS = {
    'g_SoundCtx_0044e190': 0x0044E190,
}

def build_candidates(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_path = out_dir / 'h16_statusdown_setactivesoundid.o'
    res = compile_tu_armv6k(SRC_PATH, obj_path, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f'Compilation failed: {res.stderr}')

    funcs = extract_elf_functions_detailed(obj_path)
    raw_cand, relocs_cand = funcs['h16_statusdown_setactivesoundid_candidate']
    raw_mut, relocs_mut = funcs['h16_statusdown_setactivesoundid_mutation']

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

def run_simulation(image: bytes, cand_blob: bytes, entry: int, sound_id: int, ctx_ptr: int) -> int:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x00100000, 0x00480000, unicorn.UC_PROT_ALL)
    uc.mem_write(0x00100000, image)

    uc.mem_map(CAND_ADDR, 0x1000, unicorn.UC_PROT_ALL)
    uc.mem_write(CAND_ADDR, bytes(cand_blob) + b'\\x00' * (0x1000 - len(cand_blob)))

    STACK_BASE = 0x0FFF0000
    uc.mem_map(STACK_BASE, 0x10000, unicorn.UC_PROT_ALL)
    SP_INIT = STACK_BASE + 0x8000

    # Write pointer at 0x0044E190
    uc.mem_write(0x0044E190, struct.pack('<I', ctx_ptr))
    if ctx_ptr != 0:
        uc.mem_write(ctx_ptr + 0x47E, struct.pack('<H', 0))

    RETURN_ADDR = 0x00100004
    uc.reg_write(UC_ARM_REG_SP, SP_INIT)
    uc.reg_write(UC_ARM_REG_LR, RETURN_ADDR)
    uc.reg_write(UC_ARM_REG_R0, sound_id)

    uc.emu_start(entry, RETURN_ADDR, timeout=500000, count=50)

    if ctx_ptr != 0:
        return struct.unpack('<H', uc.mem_read(ctx_ptr + 0x47E, 2))[0]
    return 0

def main():
    code = CODE_PATH.read_bytes()
    cand_blob, mut_blob = build_candidates(ROOT / 'build/h16_tests')

    cases = [
        (0x0123, 0x0FFF2000),
        (0x4567, 0x0FFF2000),
        (0xFFFF, 0x0FFF2000),
        (0x0000, 0x0FFF2000),
        (0x1234, 0), # null ctx
    ]

    for sound_id, ctx_ptr in cases:
        orig = run_simulation(code, cand_blob, ORIG_ADDR, sound_id, ctx_ptr)
        cand = run_simulation(code, cand_blob, CAND_ADDR, sound_id, ctx_ptr)
        mut = run_simulation(code, mut_blob, CAND_ADDR, sound_id, ctx_ptr)

        if orig != cand:
            raise AssertionError(f'Mismatch for ({sound_id}, {ctx_ptr}): orig={orig}, cand={cand}')
        if orig == mut and ctx_ptr != 0:
            raise AssertionError(f'Mutation undetected for ({sound_id}, {ctx_ptr})')

    print(f'[PASS] h16_statusdown_setactivesoundid: 100% parity across {len(cases)} vectors with mutation sensitivity.')

if __name__ == '__main__':
    main()
''', encoding='utf-8')

EXPERIMENTS = [
    'h16_asdsoundeffect_setbuffer_experiment.py',
    'h16_asdsoundeffect_getbuffersize_experiment.py',
    'h16_asdsoundeffect2_setbuffer_experiment.py',
    'h16_asdsound_getdatasize_experiment.py',
    'h16_asdsound_getsamplebytes_experiment.py',
    'h16_asddata_getbase_experiment.py',
    'h16_asddata_getcount_experiment.py',
    'h16_statusdown_setactivesoundid_experiment.py',
]

def main():
    print("=== Executing all 8 Milestone H16 Unicorn Differential Experiments ===")
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
        print("\n=== ALL 8 MILESTONE H16 EXPERIMENTS PASSED WITH 100% PARITY! ===")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
