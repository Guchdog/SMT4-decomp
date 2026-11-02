import hashlib, random, struct, subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang

IMAGE = (ROOT / 'extracted/exefs/code.bin').read_bytes()
assert hashlib.sha256(IMAGE).hexdigest() == '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
OUT = ROOT / 'build/h2-c1f28/experiment'
OUT.mkdir(parents=True, exist_ok=True)
CLANG = str(find_clang())
SOURCE = ROOT / 'experiments/semantic_equivalence/h2_c1f28_candidate.cpp'
PRODUCTION_OBJECT = ROOT / 'build/h2-c1f28/production/engine/leaf_batch22_b.o'


def compile_source(source, name):
    obj = OUT / f'{name}.o'
    subprocess.run([CLANG, '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2',
                    '-mfloat-abi=hard', '-O2', '-std=c++20', '-ffreestanding',
                    '-fno-exceptions', '-fno-rtti', '-c', str(source), '-o', str(obj)], check=True)
    return extract_elf_functions_detailed(obj)

candidate_functions = compile_source(SOURCE, 'candidate')
candidate = candidate_functions['candidate_002c1f28'][0]
production = extract_elf_functions_detailed(PRODUCTION_OBJECT)['engine_func_002c1f28'][0]
original = IMAGE[0x2c1f28 - 0x100000:0x2c1f28 - 0x100000 + 28]


def run_direct(body, threshold, flag_byte):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x100000, 0x500000)
    u.mem_write(0x100000, IMAGE)
    u.mem_write(0x2c1f28, body)
    u.mem_map(0x800000, 0x10000)
    globals_before = bytearray(u.mem_read(0x43e0b8, 0x40))
    globals_before[0] = flag_byte & 0xff
    globals_before[4:8] = struct.pack('<i', threshold)
    u.mem_write(0x43e0b8, bytes(globals_before))
    sp, lr = 0x80ff00, 0x80f000
    u.reg_write(UC_ARM_REG_SP, sp)
    u.reg_write(UC_ARM_REG_LR, lr)
    u.reg_write(UC_ARM_REG_R0, 0xabcdef01)
    regs = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
            UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(regs):
        u.reg_write(reg, 0x11220000 + i)
    returned = False
    writes = []
    def on_write(uc, access, address, size, value, data):
        writes.append((address, size, value))
    u.hook_add(UC_HOOK_MEM_WRITE, on_write)
    def hook(uc, address, size, data):
        nonlocal returned
        if address == lr:
            returned = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x2c1f28, 0, count=100)
    if not returned:
        raise AssertionError('callee did not return')
    return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP),
            [u.reg_read(reg) for reg in regs], bytes(u.mem_read(0x43e0b8, 0x40)), tuple(writes))


def run_real_helper(body, seed, threshold):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x100000, 0x500000)
    u.mem_write(0x100000, IMAGE)
    u.mem_write(0x2c1f28, body)
    u.mem_map(0x800000, 0x20000)
    u.mem_map(0x900000, 0x10000)
    rng = random.Random(seed)
    obj, state = 0x900000, 0x805000
    obj_data = bytearray(rng.randrange(256) for _ in range(0x1200))
    obj_data[8] = 1  # non-fast-path state that calls 0x002c1f28
    u.mem_write(obj, bytes(obj_data))
    u.mem_write(state, bytes(rng.randrange(256) for _ in range(0x200)))
    u.mem_write(obj + 0x2e, b'\x07')
    u.mem_write(0x43e18c, struct.pack('<I', obj))
    globals_data = bytearray(rng.randrange(256) for _ in range(0x40))
    globals_data[0] = 0
    globals_data[4:8] = struct.pack('<i', threshold)
    u.mem_write(0x43e0b8, bytes(globals_data))
    sp, lr = 0x81ff00, 0x80f000
    u.reg_write(UC_ARM_REG_SP, sp)
    u.reg_write(UC_ARM_REG_LR, lr)
    u.reg_write(UC_ARM_REG_R0, 0x13572468)
    u.reg_write(UC_ARM_REG_R1, 0x24681357)
    u.reg_write(UC_ARM_REG_R2, 1 + seed)
    u.reg_write(UC_ARM_REG_R3, 6)
    u.mem_write(sp, struct.pack('<II', 1, 0))
    u.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    regs = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
            UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(regs):
        u.reg_write(reg, 0x22220000 + i)
    returned = False
    writes = []
    def on_write(uc, access, address, size, value, data):
        writes.append((address, size, value))
    u.hook_add(UC_HOOK_MEM_WRITE, on_write)
    def hook(uc, address, size, data):
        nonlocal returned
        if address == lr:
            returned = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x286928, 0, count=5000)
    if not returned:
        raise AssertionError('original 0x00286928 caller did not return')
    return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP),
            [u.reg_read(reg) for reg in regs], bytes(u.mem_read(obj, 0x1200)),
            bytes(u.mem_read(state, 0x200)), bytes(u.mem_read(0x43e0b8, 0x40)), tuple(writes))


cases = [(value, flag) for value in (-0x80000000, -1, 0, 1, 0x7fffffff)
         for flag in (-128, -1, 0, 1, 127)]
rng = random.Random(0x2c1f28)
for _ in range(128):
    cases.append((rng.randint(-0x80000000, 0x7fffffff), rng.randint(-128, 127)))
for threshold, flag in cases:
    ref = run_direct(original, threshold, flag)
    if ref[4]:
        raise SystemExit(f'original unexpectedly wrote memory: {ref[4]}')
    for name, body in (('candidate', candidate), ('production', production)):
        got = run_direct(body, threshold, flag)
        if got[4]:
            raise SystemExit(f'{name} unexpectedly wrote memory: {got[4]}')
        if got != ref:
            raise SystemExit(f'{name} mismatch threshold={threshold} flag={flag}: {got[0]} != {ref[0]}')

mutations = {
    'threshold': ('if (enabled < 0)', 'if (enabled >= 0)'),
    'sign_extend': ('return *reinterpret_cast<const int8_t*>(globals);',
                    'return *reinterpret_cast<const uint8_t*>(globals);'),
    'return': ('return *reinterpret_cast<const int8_t*>(globals);', 'return 0;'),
}
for name, (needle, replacement) in mutations.items():
    source_text = SOURCE.read_text(encoding='utf-8')
    if source_text.count(needle) != 1:
        raise AssertionError(f'mutant {name} did not apply uniquely')
    mutant_source = OUT / f'mutant_{name}.cpp'
    mutant_source.write_text(source_text.replace(needle, replacement), encoding='utf-8')
    mutant = compile_source(mutant_source, f'mutant_{name}')[f'candidate_002c1f28'][0]
    if not any(run_direct(mutant, t, b) != run_direct(original, t, b) for t, b in cases):
        raise SystemExit(f'negative control {name} escaped detection')

for seed in range(32):
    if run_real_helper(original, seed, 0) != run_real_helper(candidate, seed, 0):
        raise SystemExit(f'candidate 0x00286928 caller mismatch seed={seed}')
    if run_real_helper(original, seed, 1) != run_real_helper(production, seed, 1):
        raise SystemExit(f'production 0x00286928 caller mismatch seed={seed}')

print(f'PASS {len(cases)}/{len(cases)} direct cases with zero memory writes; 32/32 original 0x00286928 compositions; '
      f'3/3 negative controls detected; candidate/production/original bytes '
      f'{len(candidate)}/{len(production)}/{len(original)}; candidate matches production={candidate == production}; '
      f'production matches original={production == original}; reference SHA-256 {hashlib.sha256(IMAGE).hexdigest()}')
