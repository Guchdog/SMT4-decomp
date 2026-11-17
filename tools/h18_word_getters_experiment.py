#!/usr/bin/env python3
"""Offline ARM differential check for four 12-byte word getters."""
from __future__ import annotations

import argparse
import capstone
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_check import find_clang
from tools.semantic_experiment import DATA, DATA_SIZE, RETURN, SP, STACK, STACK_SIZE, TEXT, Case, Runner, arm, unicorn, difference
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

ADDRESSES = (0x003F5A68, 0x003F5E34, 0x003F635C, 0x003F6800)
SEEDS = (7, 20261024)
EXPECTED = (('ldr', 'r0, [r0, #4]'), ('mov', 'r0, r0'), ('bx', 'lr'))
WORDS = (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF,
         0x12345678, 0xA5A5A5A5)
MASK32 = 0xFFFFFFFF
CANDIDATE = ROOT / 'experiments/semantic_equivalence/h18_word_getters_candidates.cpp'

def symbol(address):
    return f'candidate_{address:08x}'

def _caller_scan(image, addresses):
    text_size = int(json.loads((ROOT / 'config/game_info.json').read_text(encoding='utf-8'))['segments']['text']['size'], 16)
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    callers = {address: [] for address in addresses}
    for offset in range(0, text_size - 3, 4):
        for insn in decoder.disasm(image[offset:offset + 4], TEXT + offset, count=1):
            if insn.mnemonic not in ('bl', 'blx') or not insn.operands:
                continue
            operand = insn.operands[0]
            if operand.type == capstone.CS_OP_IMM:
                target = operand.imm & MASK32
                if target in callers:
                    callers[target].append(f'0x{insn.address:08x}')
    return {hex(address): sites for address, sites in callers.items()}

def verify_reference(code_path: Path) -> dict:
    pinned = load_pinned_reference(code_path, ROOT / 'config/game_info.json', ROOT / 'config/functions.csv')
    image = pinned.image
    rows = {int(row['address'], 16): row for row in pinned.ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    functions = {}
    for address in ADDRESSES:
        row = rows.get(address)
        if row is None or int(row['size']) != 12 or row['status'].strip() != 'matching':
            raise ValueError(f'Missing matching 12-byte ledger row at {address:#010x}')
        raw = image[address - TEXT:address - TEXT + 12]
        insns = list(decoder.disasm(raw, address))
        actual = tuple((i.mnemonic.lower(), i.op_str.lower()) for i in insns)
        if actual != EXPECTED or sum(i.size for i in insns) != 12:
            raise ValueError(f'Original is not the expected complete getter at {address:#010x}: {actual}')
        functions[hex(address)] = {
            'name': row['name'], 'size': 12, 'original_bytes_hex': raw.hex(),
            'original_bytes_sha256': hashlib.sha256(raw).hexdigest(),
            'instructions': [f'{m} {o}' for m, o in actual],
            'contract_under_test': 'read aligned uint32 at p+4; return it in r0; preserve r1-r12, SP, LR and NZCV; no writes; return to LR',
        }
    return {'image_sha256': hashlib.sha256(image).hexdigest(), 'functions': functions,
            'direct_callers': _caller_scan(image, ADDRESSES),
            'caller_search_limitations': 'Aligned ARM BL/BLX immediate scan of text only; indirect, Thumb, computed, unaligned and relocated calls are not found. Direct targets may include data decoded as instructions.'}

def make_cases(seed: int, samples: int = 128, address: int = ADDRESSES[0]):
    if samples < 0:
        raise ValueError('samples must be nonnegative')
    rng = random.Random(seed ^ address)
    offsets = (0, DATA_SIZE - 8, 4, DATA_SIZE - 12, 0x100, 0x104, 0x200, 0x204)
    for index in range(len(WORDS) + samples):
        data = bytearray(rng.randbytes(DATA_SIZE))
        regs = [rng.getrandbits(32) for _ in range(13)]
        if index < len(WORDS):
            offset, word = offsets[index], WORDS[index]
        else:
            offset = rng.randrange((DATA_SIZE - 8) // 4 + 1) * 4
            word = rng.getrandbits(32)
        struct.pack_into('<I', data, offset + 4, word)
        regs[0] = DATA + offset
        flags = (0, 0x40000000, 0x80000000, 0xC0000000)[index % 4]
        yield Case(f'case-{index}-word-{word:08x}-offset-{offset:x}', tuple(regs), bytes(data), rng.randbytes(STACK_SIZE), flags)

def _expected_read(case):
    offset = case.registers[0] - DATA
    return frozenset(range(case.registers[0] + 4, case.registers[0] + 8))

def compare(original_runner, candidate_runner, case):
    original = original_runner.run(case)
    rebuilt = candidate_runner.run(case)
    for label, result in (('original', original), ('candidate', rebuilt)):
        if result.fault:
            return f'{label} fault: {result.fault}'
        if not result.stopped:
            return f'{label} did not return to LR'
        expected_word = struct.unpack_from('<I', case.data, case.registers[0] - DATA + 4)[0]
        if result.result != expected_word:
            return f'{label} returned {result.result:#010x}, expected {expected_word:#010x}'
        if result.pc != RETURN:
            return f'{label} continuation was {result.pc:#010x}, expected {RETURN:#010x}'
        if result.nzcv != case.nzcv:
            return f'{label} changed NZCV'
        if result.data != case.data:
            return f'{label} changed RAM'
        if result.writes:
            return f'{label} wrote RAM/stack'
        if result.reads != _expected_read(case):
            return f'{label} read footprint differs from exactly p+4..p+7'
    issue = difference(original, rebuilt, returns_value=True, compare_flags=True)
    if issue:
        return issue
    return None

def _negative_controls():
    word = lambda instruction: struct.pack('<I', instruction)
    bx_lr = word(0xE12FFF1E)
    return {
        'negative_wrong_return': word(0xE3A00000) + bx_lr,
        'negative_changed_flags': word(0xE5900004) + word(0xE3500000) + bx_lr,
        'negative_write_memory': word(0xE5800000) + word(0xE5900004) + bx_lr,
        # Caller-saved r1 may differ under AAPCS; this is a scope control, not
        # an invalid implementation. It must remain accepted by the comparator.
        'control_caller_saved_clobber': word(0xE3A01000) + word(0xE5900004) + bx_lr,
    }

def run(code_path: Path, output: Path, seed: int = 20261024, samples: int = 128):
    if unicorn is None or arm is None:
        raise RuntimeError('Unicorn is required for ARM differential execution')
    if samples < 0:
        raise ValueError('samples must be nonnegative')
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / 'config/game_info.json', ROOT / 'config/functions.csv')
    reference = verify_reference(code_path)
    before = hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
    required = {symbol(address) for address in ADDRESSES} | set(_negative_controls())
    object_path = output / 'h18_word_getters_candidates.o'
    compiled = compile_candidate_symbols(CANDIDATE, object_path, ROOT, required)
    results = []
    for address in ADDRESSES:
        original_runner = Runner(pinned.image, address)
        candidate_runner = Runner(pinned.image, address, compiled[symbol(address)])
        failure = None
        count = 0
        for case in make_cases(seed, samples, address):
            count += 1
            failure = compare(original_runner, candidate_runner, case)
            if failure:
                break
        results.append({'address': hex(address), 'candidate': symbol(address), 'passed': failure is None,
                        'cases': count, 'failure': failure, 'original_bytes': 12,
                        'candidate_bytes': len(compiled[symbol(address)]),
                        'candidate_bytes_hex': compiled[symbol(address)].hex(),
                        'candidate_bytes_match_original': compiled[symbol(address)] ==
                        pinned.image[address - TEXT:address - TEXT + 12]})
    controls = []
    scope_control = None
    for idx, (name, body) in enumerate(_negative_controls().items()):
        address = ADDRESSES[idx % len(ADDRESSES)]
        value = 1 if name == 'negative_changed_flags' else 0xA5A55A5A
        case = next(make_cases(seed + 31, 1, address))
        data = bytearray(case.data)
        pointer = case.registers[0]
        struct.pack_into('<I', data, pointer - DATA + 4, value)
        if name == 'negative_write_memory':
            struct.pack_into('<I', data, pointer - DATA, 0x11223344)
        flags = 0 if name == 'negative_changed_flags' else case.nzcv
        targeted = Case(case.label + '-control', case.registers, bytes(data), case.stack, flags)
        baseline_runner = Runner(pinned.image, address)
        control_runner = Runner(pinned.image, address, body)
        reason = compare(baseline_runner, control_runner, targeted)
        if name == 'control_caller_saved_clobber':
            scope_control = {'name': name, 'address': hex(address), 'accepted': reason is None,
                             'reason': reason, 'r1_may_differ': True}
        else:
            controls.append({'name': name, 'address': hex(address), 'detected': reason is not None, 'reason': reason})
    if hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() != before:
        raise RuntimeError('candidate source changed during experiment')
    compiler = subprocess.run([str(find_clang()), '--version'], capture_output=True, text=True, check=True)
    report = {
        'schema_version': 1, 'passed': all(item['passed'] for item in results) and all(item['detected'] for item in controls) and scope_control['accepted'],
        'scope': 'four isolated 12-byte aligned ordinary-RAM word getters; no production integration or runtime claim',
        'reference_sha256': reference['image_sha256'], 'functions': reference['functions'],
        'direct_callers': reference['direct_callers'], 'caller_search_limitations': reference['caller_search_limitations'],
        'source_sha256': before, 'object_sha256': hashlib.sha256(object_path.read_bytes()).hexdigest(),
        'compiler': compiler.stdout.splitlines()[0], 'seed': seed, 'random_samples_per_function': samples,
        'comparison_contract': 'r0 return, LR continuation via final PC, NZCV, data/stack and read/write footprint; AAPCS-preserved r4-r11, SP and d8-d15 checked by shared comparator. Caller-saved GPR differences are permitted.',
        'directed_cases_per_function': len(WORDS), 'function_comparisons': sum(item['cases'] for item in results),
        'results': results, 'negative_controls': controls, 'caller_saved_scope_control': scope_control,
        'limitations': [
            'Only aligned p values in ordinary emulated RAM with a readable uint32 at p+4 are tested; null, misaligned, MMIO, unmapped and concurrent cases are outside the contract.',
            'The direct caller search is a bounded ARM BL/BLX pattern scan and may miss indirect, Thumb, computed or relocated call sites.',
            'No caller-composition or game-runtime comparison was run; return-value meaning and higher-level object layout remain unconfirmed.',
            'This isolated differential evidence is not formal equivalence and does not change production source or the matching ledger.',
        ],
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code', type=Path, default=ROOT / 'extracted/exefs/code.bin')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=20261024)
    parser.add_argument('--samples', type=int, default=128)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.seed, args.samples)
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    print(f'Word getter experiment {"PASS" if report["passed"] else "FAIL"}; {report["function_comparisons"]} comparisons; {args.output / "report.json"}')
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
