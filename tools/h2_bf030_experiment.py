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
OUT = ROOT / 'build/h2-bf030/experiment'
OUT.mkdir(parents=True, exist_ok=True)
CLANG = str(find_clang())
SOURCE = ROOT / 'experiments/semantic_equivalence/h2_bf030_candidate.cpp'
PRODUCTION_OBJECT = ROOT / 'build/h2-bf030/production/engine/leaf_batch41_b.o'


def compile_source(source, name):
    obj = OUT / f'{name}.o'
    subprocess.run([CLANG, '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2',
                    '-mfloat-abi=hard', '-O2', '-std=c++20', '-ffreestanding',
                    '-fno-exceptions', '-fno-rtti', '-c', str(source), '-o', str(obj)], check=True)
    return extract_elf_functions_detailed(obj)

candidate = compile_source(SOURCE, 'candidate')['candidate_002bf030'][0]
production = extract_elf_functions_detailed(PRODUCTION_OBJECT)['camp_func_002bf030'][0]
original = IMAGE[0x2bf030 - 0x100000:0x2bf030 - 0x100000 + 120]
if max(len(candidate), len(production)) > 120:
    raise SystemExit(f'candidate does not fit original slot: {len(candidate)}/{len(production)}')


def run_direct(body, seed, n, selector, service_word, marker_pattern='all'):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x100000, 0x500000)
    u.mem_write(0x100000, IMAGE)
    u.mem_write(0x2bf030, body)
    u.mem_map(0x800000, 0x20000)
    u.mem_map(0x900000, 0x200000)
    rng = random.Random(seed)
    obj, manager, table = 0x900000, 0x910000, 0x920000
    service_table = 0x930000
    obj_data = bytearray(rng.randrange(256) for _ in range(0x400))
    struct.pack_into('<I', obj_data, 0x48, manager)
    struct.pack_into('<I', obj_data, 0x58, 0)
    struct.pack_into('<I', obj_data, 0x64, 0)
    u.mem_write(obj, bytes(obj_data))
    manager_data = bytearray(0x100)
    struct.pack_into('<H', manager_data, 6, 0)
    struct.pack_into('<H', manager_data, 8, n)
    struct.pack_into('<I', manager_data, 0x18, service_table)
    struct.pack_into('<I', manager_data, 0x1c, table)
    u.mem_write(manager, bytes(manager_data))
    count = n // 28
    table_size = max(count * 28, 28)
    records = bytearray(b'\xff' * table_size)
    for i in range(count):
        is_marker = (marker_pattern == 'all' or
                     (marker_pattern == 'leading_nonmarker' and i != 0) or
                     (marker_pattern == 'none' and False))
        struct.pack_into('<I', records, i * 28, 0xffffffff if is_marker else i + 1)
        struct.pack_into('<i', records, i * 28 + 8, service_word)
        struct.pack_into('<i', records, i * 28 + 0x0c, -1)
        struct.pack_into('<i', records, i * 28 + 0x14, -1)
    u.mem_write(table, bytes(records))
    u.mem_write(service_table, bytes(0x100))
    sp, lr = 0x81ff00, 0x80f000
    u.reg_write(UC_ARM_REG_SP, sp)
    u.reg_write(UC_ARM_REG_LR, lr)
    u.reg_write(UC_ARM_REG_R0, obj)
    u.reg_write(UC_ARM_REG_R1, selector)
    u.reg_write(UC_ARM_REG_R2, rng.getrandbits(32))
    u.reg_write(UC_ARM_REG_R3, rng.getrandbits(32))
    regs = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
            UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(regs):
        u.reg_write(reg, 0x22330000 + i)
    writes = []
    u.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, address, size, value, data: writes.append((address, size, value)))
    returned = False
    def hook(uc, address, size, data):
        nonlocal returned
        if address == lr:
            returned = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x2bf030, 0, count=150000)
    if not returned:
        raise AssertionError(f'0x002bf030 direct case did not return n={n} selector={selector}')
    return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP),
            [u.reg_read(reg) for reg in regs], bytes(u.mem_read(obj, 0x400)),
            bytes(u.mem_read(manager, 0x100)), tuple(w for w in writes if not (0x81f000 <= w[0] < 0x820000)))


def run_real_caller(body, seed):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x100000, 0x500000)
    u.mem_write(0x100000, IMAGE)
    u.mem_write(0x2bf030, body)
    u.mem_map(0x800000, 0x20000)
    u.mem_map(0x900000, 0x200000)
    rng = random.Random(seed)
    obj = 0x900000
    inner1, inner2 = obj + 0xc4, obj + 0x268
    manager1, manager2 = 0x910000, 0x911000
    table1, table2 = 0x920000, 0x921000
    obj_data = bytearray(rng.randrange(256) for _ in range(0x600))
    struct.pack_into('<I', obj_data, 0xc4 + 0x48, manager1)
    struct.pack_into('<I', obj_data, 0x268 + 0x48, manager2)
    u.mem_write(obj, bytes(obj_data))
    for manager, table in ((manager1, table1), (manager2, table2)):
        data = bytearray(0x100)
        struct.pack_into('<H', data, 6, 0)
        struct.pack_into('<H', data, 8, 224)  # eight stride-28 entries
        struct.pack_into('<I', data, 0x1c, table)
        u.mem_write(manager, bytes(data))
        entries = bytearray(b'\xff' * (8 * 28))
        for i in range(8):
            struct.pack_into('<I', entries, i * 28, 0xffffffff)
            struct.pack_into('<i', entries, i * 28 + 8, -1)
            struct.pack_into('<i', entries, i * 28 + 0x0c, -1)
            struct.pack_into('<i', entries, i * 28 + 0x14, -1)
        u.mem_write(table, bytes(entries))
    sp, lr = 0x81ff00, 0x80f000
    u.reg_write(UC_ARM_REG_SP, sp)
    u.reg_write(UC_ARM_REG_LR, lr)
    u.reg_write(UC_ARM_REG_R0, obj)
    u.reg_write(UC_ARM_REG_R1, 11)  # original 0x002b8d24 index-11 branch
    u.reg_write(UC_ARM_REG_R2, rng.getrandbits(32))
    u.reg_write(UC_ARM_REG_R3, rng.getrandbits(32))
    regs = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
            UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(regs):
        u.reg_write(reg, 0x33440000 + i)
    writes = []
    u.hook_add(UC_HOOK_MEM_WRITE, lambda uc, access, address, size, value, data: writes.append((address, size, value)))
    calls = 0
    returned = False
    def hook(uc, address, size, data):
        nonlocal calls, returned
        if address == 0x2bf030:
            calls += 1
        if address == lr:
            returned = True
            uc.emu_stop()
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x2b8d24, 0, count=100000)
    if not returned:
        raise AssertionError('original 0x002b8d24 caller did not return')
    if calls != 2:
        raise AssertionError(f'expected two 0x002bf030 calls, observed {calls}')
    return (u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_SP),
            [u.reg_read(reg) for reg in regs], bytes(u.mem_read(obj, 0x600)),
            bytes(u.mem_read(manager1, 0x100)), bytes(u.mem_read(manager2, 0x100)),
            bytes(u.mem_read(table1, 8 * 28)), bytes(u.mem_read(table2, 8 * 28)), tuple(w for w in writes if not (0x81f000 <= w[0] < 0x820000)))


cases = []
for n in (0, 1, 27, 28, 55, 56, 84, 65535):
    count = n // 28
    for selector in (0, 1, 7, max(0, count - 1), count, 0xffffffff):
        for service_word in (-1, 0):
            cases.append((n * 37 + selector, n, selector, service_word))
rng = random.Random(0x2bf030)
for i in range(24):
    n = rng.choice((28, 56, 84, 112, 224, 65535))
    count = n // 28
    selector = rng.choice((0, 1, 2, 7, count, 0xffffffff))
    cases.append((0x5000 + i, n, selector, rng.choice((-1, 0))))
cases = [(seed, n, selector, service_word, 'all') for seed, n, selector, service_word in cases]
# The marker word is not a property of every table entry. These directed cases
# make the ordinal scan skip ordinary entries and also cover a table with no
# markers, where only selector zero can select an entry.
for pattern, n, selectors in (
        ('leading_nonmarker', 224, (1, 2, 3, 7)),
        ('none', 224, (1,)),
        ('leading_nonmarker', 65535, (1, 7, 0xffffffff))):
    for selector in selectors:
        cases.append((0x5bf030 + n + selector, n, selector, -1, pattern))

for seed, n, selector, service_word, marker_pattern in cases:
    try:
        ref = run_direct(original, seed, n, selector, service_word, marker_pattern)
    except UcError as exc:
        raise SystemExit(f'original fault seed={seed} n={n} selector={selector} pattern={marker_pattern}: {exc}')
    for name, body in (('candidate', candidate), ('production', production)):
        got = run_direct(body, seed, n, selector, service_word, marker_pattern)
        if got != ref:
            raise SystemExit(f'{name} mismatch n={n} selector={selector} service_word={service_word}: fields={[i for i,(a,b) in enumerate(zip(got,ref)) if a!=b]} r0/sp={got[:2]} ref={ref[:2]} writes={got[-1]} / {ref[-1]}')

mutations = {
    'compare_order': ('if (markers == selector)', 'if (markers + 1u == selector)'),
    'stride': ('i * 28u', 'i * 24u'),
    'marker': ('== 0xffffffffu', '== 0xfffffffeu'),
    'increment_unconditionally': ('if (*reinterpret_cast<const uint32_t*>(entry) == 0xffffffffu) ++markers;', '++markers;'),
    'return': ('return service(object, selected);', 'service(object, selected); return reinterpret_cast<uint32_t>(object);'),
    'count': ('auto count = (static_cast<uint32_t>(n) * 0x9249u + 0x9249u) >> 20;', 'auto count = ((static_cast<uint32_t>(n) * 0x9249u + 0x9249u) >> 20) + 1u;'),
}

def mutant_differs(mutant, seed, n, selector, service_word, marker_pattern):
    try:
        return run_direct(mutant, seed, n, selector, service_word, marker_pattern) != run_direct(original, seed, n, selector, service_word, marker_pattern)
    except UcError:
        return True

for name, (needle, replacement) in mutations.items():
    source_text = SOURCE.read_text(encoding='utf-8')
    if source_text.count(needle) != 1:
        raise AssertionError(f'mutant {name} not applied uniquely')
    mutant_source = OUT / f'mutant_{name}.cpp'
    mutant_source.write_text(source_text.replace(needle, replacement), encoding='utf-8')
    mutant = compile_source(mutant_source, f'mutant_{name}')['candidate_002bf030'][0]
    if not any(mutant_differs(mutant, seed, n, selector, service_word, marker_pattern)
               for seed, n, selector, service_word, marker_pattern in cases):
        raise SystemExit(f'negative control {name} escaped detection')

for seed in range(24):
    if run_real_caller(original, seed) != run_real_caller(candidate, seed):
        raise SystemExit(f'candidate 0x002b8d24 caller mismatch seed={seed}')
    if run_real_caller(original, seed) != run_real_caller(production, seed):
        raise SystemExit(f'production 0x002b8d24 caller mismatch seed={seed}')

print(f'PASS {len(cases)}/{len(cases)} direct cases with original 0x00138934 service; '
      f'24/24 original 0x002b8d24 index-11 compositions with two asserted callee entries; '
      f'{len(mutations)}/{len(mutations)} negative controls detected; candidate/production/original bytes '
      f'{len(candidate)}/{len(production)}/{len(original)}; candidate matches production={candidate == production}; '
      f'production matches original={production == original}; reference SHA-256 {hashlib.sha256(IMAGE).hexdigest()}')
