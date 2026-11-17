#!/usr/bin/env python3
"""Differential experiment for 21 four-byte ARM MOV r0,r0 callback stubs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.build_check import find_clang
from tools.semantic_experiment import DATA, DATA_SIZE, STACK, STACK_SIZE, TEXT, Case, Runner
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

ADDRESSES = (
    0x00235DF4, 0x0023DE14, 0x0026B0CC, 0x0027375C, 0x002767AC,
    0x002819F4, 0x0028EC74, 0x0028FDE0, 0x00295EA8, 0x002A4DB0,
    0x002AD46C, 0x002AE64C, 0x002B0204, 0x002B6E40, 0x002BAC24,
    0x002BBB28, 0x002BCE44, 0x002BD258, 0x002BDD1C, 0x002BF2B0,
    0x002BF9E4,
)
SEEDS = (7, 20261024)
U32_MASK = 0xFFFFFFFF

class StubRunner(Runner):
    """Use address+4 as the continuation for both the one-op original and C++ stub."""
    def __init__(self, image, entry, replacement=None):
        super().__init__(image, entry, replacement)
        self.continuation = entry + 4
        self._first_instruction = True

    def _instruction(self, uc, address, size, _):
        if self._first_instruction and address == self.entry:
            uc.reg_write(__import__('unicorn').arm_const.UC_ARM_REG_LR, self.continuation)
            self._first_instruction = False
        super()._instruction(uc, address, size, _)

    def run(self, case, **kwargs):
        self._first_instruction = True
        return super().run(case, stops=(self.continuation,), **kwargs)

class FullStateRunner(StubRunner):
    def run(self, case, **kwargs):
        execution = super().run(case, **kwargs)
        from tools.semantic_experiment import arm
        self.observed_gprs = tuple(self.uc.reg_read(getattr(arm, f'UC_ARM_REG_R{i}')) for i in range(13)) + (
            self.uc.reg_read(arm.UC_ARM_REG_SP), self.uc.reg_read(arm.UC_ARM_REG_LR))
        return execution

def symbol(address):
    return f'candidate_{address:08x}'

def verify_reference(image, game_info, ledger):
    digest = hashlib.sha256(image).hexdigest()
    if digest != str(game_info.get('code_sha256', '')).lower():
        raise ValueError('code.bin SHA-256 does not match the pinned game revision')
    if len(image) != int(game_info['code_bin_size']):
        raise ValueError('code.bin size does not match the pinned game revision')
    rows = {int(row['address'], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    functions = {}
    for address in ADDRESSES:
        row = rows.get(address)
        if row is None or row['status'].strip() != 'matching' or int(row['size']) != 4:
            raise ValueError(f'Missing matching 4-byte ledger row at {address:#010x}')
        raw = image[address - TEXT:address - TEXT + 4]
        insns = list(decoder.disasm(raw, address))
        actual = tuple((i.mnemonic.lower(), i.op_str.lower()) for i in insns)
        if actual != (('mov', 'r0, r0'),) or sum(i.size for i in insns) != 4:
            raise ValueError(f'Original instruction changed at {address:#010x}: {actual}')
        following = image[address - TEXT + 4:address - TEXT + 16]
        fallthrough = [f'{i.mnemonic} {i.op_str}'.strip() for i in decoder.disasm(following, address + 4)]
        functions[hex(address)] = {
            'name': row['name'], 'category': row['category'], 'size': 4,
            'original_bytes_hex': raw.hex(),
            'original_bytes_sha256': hashlib.sha256(raw).hexdigest(),
            'instructions': ['mov r0, r0'],
            'fallthrough_preview': fallthrough,
            'contract_under_test': 'isolated MOV instruction effect only; synthetic continuation at address+4 is not real function behavior',
        }
    return {'code_sha256': digest, 'functions': functions}

def make_case(address, seed, index):
    rng = random.Random(seed ^ address ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = (0, 1, 0x12345678, 0x80000000, U32_MASK)[index % 5]
    flags = (0, 0x40000000, 0x80000000, 0xC0000000)[index % 4]
    return Case(f'case-{index}', tuple(regs), bytes(data), rng.randbytes(STACK_SIZE), flags)

def compare(a, b, case):
    original, candidate = a.run(case), b.run(case)
    for label, result in (('original', original), ('candidate', candidate)):
        if result.fault: return f'{label} fault: {result.fault}'
        if not result.stopped: return f'{label} did not reach continuation'
    if a.observed_gprs != b.observed_gprs: return 'GPR/SP/LR state differs'
    if original.nzcv != candidate.nzcv: return 'NZCV differs'
    if original.data != candidate.data: return 'RAM differs'
    if original.live_stack != candidate.live_stack: return 'live stack differs'
    if original.reads != candidate.reads or original.writes != candidate.writes: return 'memory access footprint differs'
    if original.pc != candidate.pc: return 'continuation differs'
    return None

def run(code_path: Path, output: Path, samples=64, seed=20261024):
    if samples < 0: raise ValueError('samples must be non-negative')
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / 'config/game_info.json', ROOT / 'config/functions.csv')
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    source = ROOT / 'experiments/semantic_equivalence/h18_nop_stub_candidates.cpp'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    names = {symbol(addr) for addr in ADDRESSES} | {'negative_clobber_r0', 'negative_clobber_r1', 'negative_clobber_flags', 'negative_write_memory'}
    object_path = output / 'h18_nop_stub_candidates.o'
    compiled = compile_candidate_symbols(source, object_path, ROOT, names)
    results = []
    for address in ADDRESSES:
        original = FullStateRunner(pinned.image, address)
        replacement = FullStateRunner(pinned.image, address, compiled[symbol(address)])
        failure = None
        cases = 0
        for index in range(4 + samples):
            case = make_case(address, seed, index)
            failure = compare(original, replacement, case)
            cases += 1
            if failure: break
        results.append({'address': hex(address), 'candidate': symbol(address), 'passed': failure is None,
                        'cases': cases, 'failure': failure, 'original_size': 4,
                        'candidate_size': len(compiled[symbol(address)]),
                        'candidate_bytes_match_claim': False})
    controls = []
    specs = [('negative_clobber_r0', 'r0'), ('negative_clobber_r1', 'r1'), ('negative_clobber_flags', 'nzcv'), ('negative_write_memory', 'memory')]
    for idx, (name, target) in enumerate(specs):
        address = ADDRESSES[idx]
        case = make_case(address, seed + 91, 7)
        regs = list(case.registers)
        if target == 'memory':
            regs[0] = DATA + 0x100
            data = bytearray(case.data)
            data[0x100:0x104] = b'\x5a\xa5\x5a\xa5'
            case = Case(case.label, tuple(regs), bytes(data), case.stack, case.nzcv)
        elif target == 'nzcv':
            regs[0] = 0
            case = Case(case.label, tuple(regs), case.data, case.stack, 0x40000000)
        elif target == 'r0': regs[0] = 0x12345678
        else: regs[1] = 0x12345678
        controls_runner = FullStateRunner(pinned.image, address, compiled[name])
        reference_runner = FullStateRunner(pinned.image, address)
        reason = compare(reference_runner, controls_runner, case)
        controls.append({'name': name, 'target': hex(address), 'state_targeted': target, 'detected': reason is not None, 'reason': reason})
    if hashlib.sha256(source.read_bytes()).hexdigest() != before: raise RuntimeError('candidate source changed during experiment')
    compiler = subprocess.run([str(find_clang()), '--version'], capture_output=True, text=True, check=True)
    report = {
        'schema': 1, 'passed': all(x['passed'] for x in results) and all(x['detected'] for x in controls),
        'scope': 'instruction-effect experiment only; all targets are MOV prefixes that fall through into meaningful code, so synthetic address+4 comparisons are invalid for promotion',
        'reference_sha256': reference['code_sha256'], 'pinned_functions': reference['functions'],
        'source_sha256': before, 'object_sha256': hashlib.sha256(object_path.read_bytes()).hexdigest(),
        'compiler': compiler.stdout.splitlines()[0], 'seed': seed, 'random_samples_per_function': samples,
        'function_comparisons': sum(x['cases'] for x in results), 'functions': results,
        'caller_windows_executed': 0, 'candidate_bytes_match_claim': False, 'whole_function_equivalence_claim': False, 'functional_evidence_level': 'partial',
        'negative_controls': controls,
        'first_counterexample': {'address': '0x0028ec74', 'original_entry': 'mov r0, r0', 'fallthrough': ['push {r4, lr}', 'bl 0x0028fde4'], 'candidate_effect': 'empty C++ function returns via bx lr instead of executing fallthrough'},
        'limitations': [
            'The void/no-argument function type is provisional. Final context inspection shows every entry is followed at address+4 by meaningful ARM code, often a prologue or function body; these are not established as standalone callbacks.',
            'The original 4-byte ledger row is one non-terminating ARM MOV embedded before further code. The harness deliberately forces address+4 as a synthetic continuation for an instruction-effect-only check; this does not model the real function control flow.',
            'C++ empty functions compile to a return sequence; their bytes are not claimed to match the original instruction.',
            'Bounded Unicorn evidence does not cover function bodies after address+4, actual callers, MMIO, concurrency, faults, timing, or game runtime.',
            'Candidates are isolated and do not alter production sources, ledger, or image.',
        ],
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code', type=Path, default=ROOT / 'extracted/exefs/code.bin')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/semantic-equivalence/h18-nop')
    parser.add_argument('--samples', type=int, default=64)
    parser.add_argument('--seed', type=int, default=20261024)
    args = parser.parse_args()
    try: report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError) as error: parser.exit(2, f'Experiment error: {error}\n')
    print(f'H18 no-op experiment {"PASS" if report["passed"] else "FAIL"}; {report["function_comparisons"]} cases; report: {args.output / "report.json"}')
    raise SystemExit(0 if report['passed'] else 1)

if __name__ == '__main__': main()
