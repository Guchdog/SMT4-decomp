import hashlib, random, struct, subprocess
from pathlib import Path
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang

IMAGE = (ROOT / 'extracted/exefs/code.bin').read_bytes()
assert hashlib.sha256(IMAGE).hexdigest() == '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
OUT = ROOT / 'build/h2-b89a0/experiment'
OUT.mkdir(parents=True, exist_ok=True)
CLANG = str(find_clang())
SOURCE = ROOT / 'experiments/semantic_equivalence/h2_b89a0_candidate.cpp'
PRODUCTION_OBJECT = ROOT / 'build/h2-b89a0/production/engine/leaf_batch26_b.o'


def compile_source(source, name):
    obj = OUT / f'{name}.o'
    subprocess.run([CLANG, '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2',
                    '-mfloat-abi=hard', '-O2', '-std=c++20', '-ffreestanding',
                    '-fno-exceptions', '-fno-rtti', '-c', str(source), '-o', str(obj)], check=True)
    return extract_elf_functions_detailed(obj)

candidate = compile_source(SOURCE, 'candidate')['candidate_002b89a0'][0]
production = extract_elf_functions_detailed(PRODUCTION_OBJECT)['camp_func_002b89a0'][0]
original = IMAGE[0x2b89a0 - 0x100000:0x2b89a0 - 0x100000 + 52]
if max(len(candidate), len(production)) > 52:
    raise SystemExit(f'candidate does not fit original slot: {len(candidate)}/{len(production)}')


def run_direct(body, seed, manager_is_null, mode):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x100000, 0x500000)
    u.mem_write(0x100000, IMAGE)
    u.mem_write(0x2b89a0, body)
    u.mem_map(0x800000, 0x10000)
    u.mem_map(0x900000, 0x10000)
    rng = random.Random(seed)
    state = 0x900000 + (seed % 128) * 0x100
    state_bytes = bytearray(rng.randrange(256) for _ in range(0x3600))
    state_bytes[0x352c:0x3530] = struct.pack('<I', mode)
    u.mem_write(state, bytes(state_bytes))
    manager = 0 if manager_is_null else state
    u.mem_write(0x44dc20, struct.pack('<I', manager))
    sp, lr = 0x80ff00, 0x80f000
    u.reg_write(UC_ARM_REG_SP, sp)
    u.reg_write(UC_ARM_REG_LR, lr)
    regs = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
            UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(regs):
        u.reg_write(reg, 0x11220000 + i)
    writes = []
    u.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, address, size, value, data: writes.append((address, size, value)))
    returned = False
    def hook(uc, address, size, data):
        nonlocal returned
        if address == lr:
            returned = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x2b89a0, 0, count=100)
    if not returned:
        raise AssertionError('callee did not return')
    return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP),
            [u.reg_read(reg) for reg in regs], bytes(u.mem_read(0x44dc20, 4)),
            bytes(u.mem_read(state + 0x3520, 0x20)), tuple(writes))


def run_real_helper(body, seed):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x100000, 0x500000)
    u.mem_write(0x100000, IMAGE)
    u.mem_write(0x2b89a0, body)
    u.mem_map(0x800000, 0x20000)
    u.mem_map(0x900000, 0x10000)
    rng = random.Random(seed)
    obj, state = 0x900000, 0x805000
    obj_data = bytearray(rng.randrange(256) for _ in range(0x1200))
    obj_data[8] = 1
    obj_data[9] = 19  # original 0x002b8d24 exits before its jump table
    u.mem_write(obj, bytes(obj_data))
    u.mem_write(state, bytes(rng.randrange(256) for _ in range(0x200)))
    u.mem_write(0x43e18c, struct.pack('<I', obj))
    u.mem_write(0x43e0b8, b'\x01\x00\x00\x00' + struct.pack('<i', -1))
    u.mem_write(0x44dc20, struct.pack('<I', 0))  # null is the documented true case
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
    writes = []
    u.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, address, size, value, data: writes.append((address, size, value)))
    returned = False
    calls = 0
    def hook(uc, address, size, data):
        nonlocal returned, calls
        if address == 0x2b89a0:
            calls += 1
        if address == lr:
            returned = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x286928, 0, count=6000)
    if not returned:
        raise AssertionError('original 0x00286928 caller did not return')
    if calls != 1:
        raise AssertionError(f'expected one call to 0x002b89a0, observed {calls}')
    return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP),
            [u.reg_read(reg) for reg in regs], bytes(u.mem_read(obj, 0x1200)),
            bytes(u.mem_read(state, 0x200)), bytes(u.mem_read(0x43e0b8, 8)),
            bytes(u.mem_read(0x44dc20, 4)), tuple(writes))


cases = [(0, 0)]
for mode in (0, 0x13, 0x14, 0x15, 0xffffffff):
    cases.append((1 + mode, mode))
    cases.append((0x100 + mode, mode))
rng = random.Random(0x2b89a0)
for i in range(128):
    cases.append((rng.randrange(10000), rng.choice((0, 0x13, 0x14, 0x15, 0xffffffff))))
for seed, mode in cases:
    is_null = seed == 0
    ref = run_direct(original, seed, is_null, mode)
    if ref[-1]:
        raise SystemExit(f'original unexpectedly wrote memory: {ref[-1]}')
    for name, body in (('candidate', candidate), ('production', production)):
        got = run_direct(body, seed, is_null, mode)
        if got[-1]:
            raise SystemExit(f'{name} unexpectedly wrote memory: {got[-1]}')
        if got != ref:
            raise SystemExit(f'{name} mismatch seed={seed} mode={mode}: {got[0]} != {ref[0]}')

mutations = {
    'null': ('if (manager == nullptr)', 'if (manager != nullptr)'),
    'offset': ('manager + 0x352c', 'manager + 0x3528'),
    'value': ('mode == 0x14', 'mode == 0x13'),
}
def mutant_differs(mutant, seed, mode):
    try:
        got = run_direct(mutant, seed, seed == 0, mode)
    except UcError:
        return True
    return got != run_direct(original, seed, seed == 0, mode)


for name, (needle, replacement) in mutations.items():
    source_text = SOURCE.read_text(encoding='utf-8')
    if source_text.count(needle) != 1:
        raise AssertionError(f'mutant {name} did not apply uniquely')
    mutant_source = OUT / f'mutant_{name}.cpp'
    mutant_source.write_text(source_text.replace(needle, replacement), encoding='utf-8')
    mutant = compile_source(mutant_source, f'mutant_{name}')['candidate_002b89a0'][0]
    if not any(mutant_differs(mutant, seed, mode) for seed, mode in cases):
        raise SystemExit(f'negative control {name} escaped detection')

for seed in range(32):
    if run_real_helper(original, seed) != run_real_helper(candidate, seed):
        raise SystemExit(f'candidate 0x00286928 continuation mismatch seed={seed}')
    if run_real_helper(original, seed) != run_real_helper(production, seed):
        raise SystemExit(f'production 0x00286928 continuation mismatch seed={seed}')

print(f'PASS {len(cases)}/{len(cases)} direct cases, zero direct writes, 32/32 nonzero 0x00286928 continuations with callee-entry assertion, '
      f'3/3 negative controls detected; candidate/production/original bytes '
      f'{len(candidate)}/{len(production)}/{len(original)}; candidate matches production={candidate == production}; '
      f'production matches original={production == original}; reference SHA-256 {hashlib.sha256(IMAGE).hexdigest()}')
