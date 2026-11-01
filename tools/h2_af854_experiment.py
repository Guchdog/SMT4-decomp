import hashlib, random, struct, subprocess
from pathlib import Path
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import find_clang

IMAGE = (ROOT / 'extracted/exefs/code.bin').read_bytes()
assert hashlib.sha256(IMAGE).hexdigest() == '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
OUT = ROOT / 'build/agent-work/H2-semantic/h2-helper-002af854-alias-caller-coverage/001'
OUT.mkdir(parents=True, exist_ok=True)
CLANG = str(find_clang())
SOURCE = ROOT / 'experiments/semantic_equivalence/h2_af854_candidate.cpp'
PRODUCTION_OBJECT = ROOT / 'build/agent-work/H2-semantic/h2-helper-002af854-alias-coverage/001/production/engine/leaf_batch13_a.o'


def compile_source(source, name):
    obj = OUT / f'{name}.o'
    subprocess.run([CLANG, '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2',
                    '-mfloat-abi=hard', '-O2', '-std=c++20', '-ffreestanding',
                    '-fno-exceptions', '-fno-rtti', '-c', str(source), '-o', str(obj)], check=True)
    return extract_elf_functions_detailed(obj)

candidate = compile_source(SOURCE, 'candidate')['candidate_002af854'][0]
production = extract_elf_functions_detailed(PRODUCTION_OBJECT)['battle_func_002af854'][0]
original = IMAGE[0x2af854 - 0x100000:0x2af854 - 0x100000 + 64]
if max(len(candidate), len(production)) > 64:
    raise SystemExit(f'candidate does not fit original slot: {len(candidate)}/{len(production)}')


def run_direct(body, seed, is_null, index, mode, alias=None):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x100000, 0x500000)
    u.mem_write(0x100000, IMAGE)
    u.mem_write(0x2af854, body)
    u.mem_map(0x800000, 0x10000)
    u.mem_map(0x900000, 0x20000)
    rng = random.Random(seed)
    obj, entries = 0x900000, 0x910000
    obj_data = bytes(rng.randrange(256) for _ in range(0x100))
    array_data = bytearray(rng.randrange(256) for _ in range(0x1000))
    u.mem_write(obj, obj_data)
    u.mem_write(entries, bytes(array_data))
    u.mem_write(obj + 0x58, struct.pack('<I', 0 if is_null else (obj+alias if alias is not None else entries)))
    sp, lr = 0x80ff00, 0x80f000
    u.reg_write(UC_ARM_REG_SP, sp)
    u.reg_write(UC_ARM_REG_LR, lr)
    u.reg_write(UC_ARM_REG_R0, obj)
    u.reg_write(UC_ARM_REG_R1, index)
    u.reg_write(UC_ARM_REG_R2, mode)
    u.reg_write(UC_ARM_REG_R3, rng.getrandbits(32))
    regs = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
            UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(regs):
        u.reg_write(reg, 0x11220000 + i)
    writes = []
    u.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, address, size, value, data: writes.append((address, size, value)))
    returned = False
    trace = []
    def hook(uc, address, size, data):
        nonlocal returned
        trace.append(address)
        if address == lr:
            returned = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x2af854, 0, count=200)
    if not returned:
        raise AssertionError(f'original 0x002af854 did not return seed={seed} null={is_null} index={index} mode={mode} pc={u.reg_read(UC_ARM_REG_PC):08x} trace={list(map(hex,trace))} r0={u.reg_read(UC_ARM_REG_R0):08x} lr={u.reg_read(UC_ARM_REG_LR):08x} ptr={u.mem_read(obj+0x58,4).hex()} body={body[:8].hex()} code={u.mem_read(0x2af854,8).hex()} r12={u.reg_read(UC_ARM_REG_R12):08x}')
    return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP),
            [u.reg_read(reg) for reg in regs], bytes(u.mem_read(obj, 0x100)),
            bytes(u.mem_read(entries, 0x1000)), tuple(writes))


def run_real_caller(body, seed, cross_alias=False):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x100000, 0x500000)
    u.mem_write(0x100000, IMAGE)
    u.mem_write(0x2af854, body)
    u.mem_map(0x800000, 0x10000)
    u.mem_map(0x900000, 0x20000)
    rng = random.Random(seed)
    obj = 0x900000
    list1, list2 = 0x910000, 0x918000
    object_data = bytearray(rng.randrange(256) for _ in range(0x500))
    struct.pack_into('<I', object_data, 0xc4 + 0x58, obj+0x1dc+0x5c-24 if cross_alias else list1)
    struct.pack_into('<I', object_data, 0x1dc + 0x58, obj+0xc4+0x5c-24 if cross_alias else list2)
    if cross_alias: struct.pack_into('<I', object_data, 0xc4+0x5c, 0x89898989)
    u.mem_write(obj, bytes(object_data))
    u.mem_write(list1, bytes(rng.randrange(256) for _ in range(0x1000)))
    u.mem_write(list2, bytes(rng.randrange(256) for _ in range(0x1000)))
    sp, lr = 0x80ff00, 0x80f000
    u.reg_write(UC_ARM_REG_SP, sp)
    u.reg_write(UC_ARM_REG_LR, lr)
    u.reg_write(UC_ARM_REG_R0, obj)
    u.reg_write(UC_ARM_REG_R1, 2)  # table entries 2-5 run both 0x002af854 calls
    u.reg_write(UC_ARM_REG_R2, 0xfeed1234)
    u.reg_write(UC_ARM_REG_R3, 0xabcddcba)
    regs = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
            UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(regs):
        u.reg_write(reg, 0x33440000 + i)
    writes = []
    u.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, address, size, value, data: writes.append((address, size, value)))
    calls = []
    returned = False
    def hook(uc, address, size, data):
        nonlocal calls, returned
        if address == 0x2af854:
            calls.append((uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R2)))
        if address == lr:
            returned = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x2b8d24, 0, count=3000)
    if not returned:
        raise AssertionError('original 0x002b8d24 caller did not return')
    if calls != [(obj+0xc4,2,0),(obj+0x1dc,2,0)]:
        raise AssertionError(f'expected two 0x002af854 calls, observed {calls}')
    if cross_alias and struct.unpack('<I',u.mem_read(obj+0x1dc+0x20,4))[0] != 2:
        raise AssertionError('second selector did not read first subobject updated halfwords')
    return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP),
            [u.reg_read(reg) for reg in regs], bytes(u.mem_read(obj, 0x500)),
            bytes(u.mem_read(list1, 0x1000)), bytes(u.mem_read(list2, 0x1000)), tuple(writes))


cases = []
for seed in range(11):
    for index in (0, 1, 2, 7, 19, 127):
        for mode in (0, 1, 0x100, 0xffffffff):
            cases.append((seed * 17 + index, False, index, mode))
    cases.append((seed, True, 2, seed))
rng = random.Random(0x2af854)
for i in range(96):
    cases.append((0x1000 + i, False, rng.randrange(0, 128), rng.choice((0, 1, 0x100, 0xffffffff))))
cases = [(*case, None) for case in cases]
for seed in (0, 17, 4729):
    for offset in (0x20,0x58,0x5c,0x60,0x84):
        for mode in (0,1,0x100,0xffffffff):
            cases.append((seed,False,0,mode,offset))
for seed in (0,17,4729):
    for index in (2,5):
        for selected in (0x5c,0x60,0x84):
            for mode in (0,1,0x100,0xffffffff):
                cases.append((seed,False,index,mode,selected-index*12))
for seed, is_null, index, mode, alias in cases:
    ref = run_direct(original, seed, is_null, index, mode, alias)
    for name, body in (('candidate', candidate), ('production', production)):
        got = run_direct(body, seed, is_null, index, mode, alias)
        if got != ref:
            raise SystemExit(f'{name} mismatch seed={seed} index={index} mode={mode}: r0 {got[0]:08x} != {ref[0]:08x}')

mutations = {
    'null': ('if (list == nullptr)', 'if (list != nullptr)'),
    'selection': ('mode != 0 ? 4 : 0', 'mode == 0 ? 4 : 0'),
    'index': ('index * 12u', 'index * 8u'),
    'return': ('*reinterpret_cast<uint32_t*>(object + 0x20) = selected;\n    return object;', '*reinterpret_cast<uint32_t*>(object + 0x20) = selected;\n    return object + 1;'),
}

def mutant_differs(mutant, seed, is_null, index, mode, alias):
    try:
        return run_direct(mutant, seed, is_null, index, mode, alias) != run_direct(original, seed, is_null, index, mode, alias)
    except UcError:
        return True

for name, (needle, replacement) in mutations.items():
    text = SOURCE.read_text(encoding='utf-8')
    if text.count(needle) != 1:
        raise AssertionError(f'mutant {name} was not applied uniquely')
    mutant_source = OUT / f'mutant_{name}.cpp'
    mutant_source.write_text(text.replace(needle, replacement), encoding='utf-8')
    mutant = compile_source(mutant_source, f'mutant_{name}')['candidate_002af854'][0]
    if not any(mutant_differs(mutant, seed, is_null, index, mode, alias)
               for seed, is_null, index, mode, alias in cases):
        raise SystemExit(f'negative control {name} escaped detection')

old_source=SOURCE.read_text(encoding='utf-8').replace('volatile uint16_t','uint16_t').replace('volatile uint8_t','uint8_t').replace('const volatile uint32_t','const uint32_t')
if old_source==SOURCE.read_text(encoding='utf-8'): raise AssertionError('ordering mutant did not apply')
old_path=OUT/'mutant_order.cpp';old_path.write_text(old_source,encoding='utf-8')
old=compile_source(old_path,'mutant_order')['candidate_002af854'][0]
order_ref=run_direct(original,0,False,0,0,0x5c)
order_got=run_direct(old,0,False,0,0,0x5c)
if order_ref==order_got or order_ref[3][0x20:0x24]==order_got[3][0x20:0x24]: raise AssertionError('alias ordering control did not expose changed selected word')
for seed in range(32):
    if run_real_caller(original, seed) != run_real_caller(candidate, seed):
        raise SystemExit(f'candidate 0x002b8d24 composition mismatch seed={seed}')
    if run_real_caller(original, seed) != run_real_caller(production, seed):
        raise SystemExit(f'production 0x002b8d24 composition mismatch seed={seed}')
    if run_real_caller(original,seed,True)!=run_real_caller(candidate,seed,True):
        raise SystemExit(f'candidate 0x002b8d24 cross-alias mismatch seed={seed}')
    if run_real_caller(original,seed,True)!=run_real_caller(production,seed,True):
        raise SystemExit(f'production 0x002b8d24 cross-alias mismatch seed={seed}')

print(f'PASS {len(cases)}/{len(cases)} direct cases incl 132 alias overlaps; 32/32 disjoint and 32/32 cross-alias original 0x002b8d24 compositions with two asserted callee calls; '
      f'4/4 negative controls and selected-word alias ordering control detected; candidate/production/original bytes '
      f'{len(candidate)}/{len(production)}/{len(original)}; candidate matches production={candidate == production}; '
      f'production matches original={production == original}; reference SHA-256 {hashlib.sha256(IMAGE).hexdigest()}')
