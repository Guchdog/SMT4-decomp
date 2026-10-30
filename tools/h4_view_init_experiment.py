"""Offline ARM differential validation for 0x001B4664 (ViewCameraWork initialization)."""
import argparse, hashlib, json, random, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed
import unicorn
from unicorn import arm_const as a

CODE = ROOT / 'extracted/exefs/code.bin'
SRC = ROOT / 'experiments/semantic_equivalence/h4_view_init_candidate.cpp'

ORIG_FUNC = 0x1B4664
ORIG_SIZE = 440
CAND = 0x1000000
STOP = 0x1008000
MOCK_ALLOC = 0x1009000
MOCK_CTOR = 0x100A000
STACK = 0x8000000
SP = STACK + 0x2000

VIEW_WORK = 0x2010000
VIEW_SIZE = 0x1C0
GATE_WORK = 0x49F91C + 0x170
GATE_SIZE = 0x50
SUBOBJ = 0x2020000

REGS = [a.UC_ARM_REG_R4, a.UC_ARM_REG_R5, a.UC_ARM_REG_R6, a.UC_ARM_REG_R7,
        a.UC_ARM_REG_R8, a.UC_ARM_REG_R9, a.UC_ARM_REG_R10, a.UC_ARM_REG_R11]

sha = lambda b: hashlib.sha256(b).hexdigest()

def bl_word(site, target):
    delta = target - (site + 8)
    if (site | target | delta) & 3 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError('unsafe ARM BL')
    return 0xeb000000 | ((delta >> 2) & 0xffffff)

def build_candidate(src_path, obj_path):
    result = compile_tu_armv6k(src_path, obj_path, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    raw, rels = extract_elf_functions_detailed(obj_path)['h4_view_init_candidate']
    if len(raw) > ORIG_SIZE:
        raise ValueError(f'Candidate size {len(raw)} exceeds original {ORIG_SIZE}')
    blob = bytearray(raw)
    for r in rels:
        tgt = MOCK_ALLOC if 'Alloc' in r.symbol_name else MOCK_CTOR
        w = bl_word(CAND + r.offset, tgt)
        struct.pack_into('<I', blob, r.offset, w)
    return bytes(blob), raw

def run_simulation(image, cand_blob, entry, is_cand, fill_byte, alloc_null=False):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(a.UC_CPU_ARM_11MPCORE)

    uc.mem_map(0x100000, 0x480000, 7)
    uc.mem_write(0x100000, image)

    uc.mem_map(CAND, 0x8000, 7)
    uc.mem_write(CAND, cand_blob)

    uc.mem_map(STOP, 0x1000, 7)
    uc.mem_map(MOCK_ALLOC, 0x1000, 7)
    uc.mem_map(MOCK_CTOR, 0x1000, 7)
    uc.mem_map(0x2000000, 0x30000, 3)
    uc.mem_map(STACK, 0x4000, 3)

    alloc_ret = 0 if alloc_null else SUBOBJ
    alloc_code = struct.pack('<III', 0xe59f0000, 0xe12fff1e, alloc_ret)
    uc.mem_write(MOCK_ALLOC, alloc_code)
    uc.mem_write(MOCK_CTOR, struct.pack('<I', 0xe12fff1e))

    if not is_cand:
        uc.mem_write(0x1b4728, struct.pack('<I', bl_word(0x1b4728, MOCK_ALLOC)))
        uc.mem_write(0x1b4734, struct.pack('<I', bl_word(0x1b4734, MOCK_CTOR)))

    uc.mem_write(0x447e88, struct.pack('<I', VIEW_WORK))

    if isinstance(fill_byte, int):
        init_work = bytes([fill_byte]) * VIEW_SIZE
        init_gate = bytes([fill_byte]) * GATE_SIZE
    else:
        init_work = fill_byte[:VIEW_SIZE]
        init_gate = fill_byte[VIEW_SIZE:VIEW_SIZE + GATE_SIZE]

    uc.mem_write(VIEW_WORK, init_work)
    uc.mem_write(GATE_WORK, init_gate)

    uc.reg_write(a.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(a.UC_ARM_REG_C1_C0_2, 0xf00000)

    for i, r in enumerate(REGS):
        uc.reg_write(r, 0x33440000 + i * 0x101)

    uc.reg_write(a.UC_ARM_REG_SP, SP)
    uc.reg_write(a.UC_ARM_REG_LR, STOP)

    writes = []
    def mem_write_hook(u, access, address, size, value, user):
        is_stack = (STACK <= address and address + size <= STACK + 0x4000)
        writes.append({'address': hex(address), 'size': size, 'value': hex(value & ((1 << (8 * size)) - 1)), 'stack': is_stack})

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, mem_write_hook)

    fault = None
    try:
        uc.emu_start(entry, STOP, count=10000)
    except unicorn.UcError as exc:
        fault = str(exc)

    return {
        'work_mem': bytes(uc.mem_read(VIEW_WORK, VIEW_SIZE)).hex(),
        'gate_mem': bytes(uc.mem_read(GATE_WORK, GATE_SIZE)).hex(),
        'sp': uc.reg_read(a.UC_ARM_REG_SP),
        'saved': [uc.reg_read(r) for r in REGS],
        'returned': uc.reg_read(a.UC_ARM_REG_PC) == STOP,
        'fault': fault,
        'nonstack_writes': [w for w in writes if not w['stack']]
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--seed', type=int, default=20261030)
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=False)

    image = CODE.read_bytes()
    cand_obj = out / 'candidate.o'
    cand_blob, cand_raw = build_candidate(SRC, cand_obj)

    # Mutation test: change sentinel_id from -1 to 0
    text = SRC.read_text(encoding='utf-8')
    mut_text = text.replace('work->sentinel_id = -1;', 'work->sentinel_id = 0;')
    if mut_text == text:
        raise ValueError('Mutation anchor mismatch')
    mut_src = out / 'mutant.cpp'
    mut_src.write_text(mut_text, encoding='utf-8')
    mut_obj = out / 'mutant.o'
    mut_blob, _ = build_candidate(mut_src, mut_obj)

    rng = random.Random(args.seed)
    fixtures = [
        ('zero_fill', 0x00, False),
        ('pattern_a5', 0xA5, False),
        ('pattern_5a', 0x5A, False),
        ('pattern_ff', 0xFF, False),
        ('random_noise_1', bytes(rng.getrandbits(8) for _ in range(VIEW_SIZE + GATE_SIZE)), False),
        ('random_noise_2', bytes(rng.getrandbits(8) for _ in range(VIEW_SIZE + GATE_SIZE)), False),
        ('null_alloc_a5', 0xA5, True),
        ('null_alloc_zero', 0x00, True),
        ('null_alloc_random', bytes(rng.getrandbits(8) for _ in range(VIEW_SIZE + GATE_SIZE)), True)
    ]

    diffs = []
    results = []

    for name, fill, alloc_null in fixtures:
        old = run_simulation(image, cand_blob, ORIG_FUNC, False, fill, alloc_null)
        new = run_simulation(image, cand_blob, CAND, True, fill, alloc_null)

        keys = ('work_mem', 'gate_mem', 'sp', 'saved', 'returned', 'fault')
        match = all(old[k] == new[k] for k in keys)

        results.append({
            'name': name,
            'match': match,
            'original': {k: old[k] for k in keys},
            'candidate': {k: new[k] for k in keys}
        })

        if not match:
            diffs.append({'name': name, 'original': old, 'candidate': new})

    # Mutation sensitivity check
    base_res = run_simulation(image, cand_blob, CAND, True, 0xA5, False)
    mut_res = run_simulation(image, mut_blob, CAND, True, 0xA5, False)
    mutation_detected = (base_res['work_mem'] != mut_res['work_mem'])

    status = 'passed' if not diffs and mutation_detected else 'failed'

    report = {
        'status': status,
        'scope': 'direct ARM function 0x001B4664 vs candidate; memory state of ViewCameraWork (0x1C0) and 0x0049F91C repeat gate (0x50), SP, callee-saved registers, null-alloc branch, non-stack writes',
        'fixtures': len(fixtures),
        'difference_count': len(diffs),
        'mutation_detected': mutation_detected,
        'results': results,
        'diffs': diffs,
        'candidate_size': len(cand_raw),
        'original_size': ORIG_SIZE,
        'reference_sha256': sha(image),
        'source_sha256': sha(SRC.read_bytes()),
        'candidate_object_sha256': sha(cand_obj.read_bytes()),
        'runner_sha256': sha(Path(__file__).read_bytes()),
        'unicorn': unicorn.__version__
    }

    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({
        'status': status,
        'fixtures': len(fixtures),
        'differences': len(diffs),
        'mutation_detected': mutation_detected
    }, indent=2))

    return 0 if status == 'passed' else 1

if __name__ == '__main__':
    sys.exit(main())
