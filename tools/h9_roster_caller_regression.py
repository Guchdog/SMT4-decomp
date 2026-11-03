from pathlib import Path
import unicorn, struct, json, hashlib, argparse, sys
from unicorn.arm_const import *

root = Path(__file__).resolve().parents[1]

def run(code, rows, fail_alloc_index=None):
    u = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    u.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    u.mem_map(0x100000, 0x480000)
    u.mem_write(0x100000, code)
    u.mem_map(0x8000000, 0x80000)
    u.mem_map(0xfff0000, 0x10000)

    roster = 0x8001000
    u.mem_write(roster, bytes([0xaa]) * 0x180)

    for i, (id, race, field, flags) in enumerate(rows):
        u.mem_write(0x8010000 + i * 16, struct.pack('<HBBxxH', id, race, field, flags) + bytes(8))

    init_regs = {
        UC_ARM_REG_R4: 0x11111111,
        UC_ARM_REG_R5: 0x22222222,
        UC_ARM_REG_R6: 0x33333333,
        UC_ARM_REG_R7: 0x44444444,
        UC_ARM_REG_R8: 0x55555555,
        UC_ARM_REG_R9: 0x66666666,
        UC_ARM_REG_R10: 0x77777777,
        UC_ARM_REG_R11: 0x88888888,
        UC_ARM_REG_SP: 0xfff8000,
        UC_ARM_REG_LR: 0x100004,
    }
    for reg, val in init_regs.items():
        u.reg_write(reg, val)
    u.reg_write(UC_ARM_REG_R0, roster)

    events = []
    alloc = [0]

    def ret(uc, val=None):
        if val is not None:
            uc.reg_write(UC_ARM_REG_R0, val & 0xffffffff)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def hook(uc, addr, size, data):
        if addr == 0x2c0ec4:
            events.append(('open',))
            ret(uc, 0x800a000)
        elif addr == 0x2c0e9c:
            events.append(('prepare',))
            ret(uc)
        elif addr == 0x2c0e4c:
            events.append(('count',))
            ret(uc, len(rows))
        elif addr == 0x2b9364:
            i = uc.reg_read(UC_ARM_REG_R0)
            ret(uc, 0x8010000 + i * 16)
        elif addr == 0x2c4b84:
            idx = alloc[0]
            alloc[0] += 1
            sz = uc.reg_read(UC_ARM_REG_R3)
            events.append(('alloc', sz))
            if fail_alloc_index is not None and idx == fail_alloc_index:
                ret(uc, 0)
            else:
                dst = 0x8040000 + idx * 0x200
                uc.mem_write(dst, bytes([0xcc]) * 0x200)
                ret(uc, dst)
        elif addr == 0x2b7f0a:
            events.append(('qsort', bool(uc.reg_read(UC_ARM_REG_CPSR) & 32), uc.reg_read(UC_ARM_REG_R1), hex(uc.reg_read(UC_ARM_REG_R3))))
        elif addr == 0x219600:
            a = uc.reg_read(UC_ARM_REG_R0)
            b = uc.reg_read(UC_ARM_REG_R1)
            x = struct.unpack('<H', uc.mem_read(a, 2))[0]
            y = struct.unpack('<H', uc.mem_read(b, 2))[0]
            ret(uc, (x > y) - (x < y))

    u.hook_add(unicorn.UC_HOOK_CODE, hook)
    try:
        u.emu_start(0x3c9ebc, 0x100004, count=300000)
        regs_preserved = {
            'r4': u.reg_read(UC_ARM_REG_R4) == init_regs[UC_ARM_REG_R4],
            'r5': u.reg_read(UC_ARM_REG_R5) == init_regs[UC_ARM_REG_R5],
            'r6': u.reg_read(UC_ARM_REG_R6) == init_regs[UC_ARM_REG_R6],
            'r7': u.reg_read(UC_ARM_REG_R7) == init_regs[UC_ARM_REG_R7],
            'r8': u.reg_read(UC_ARM_REG_R8) == init_regs[UC_ARM_REG_R8],
            'r9': u.reg_read(UC_ARM_REG_R9) == init_regs[UC_ARM_REG_R9],
            'r10': u.reg_read(UC_ARM_REG_R10) == init_regs[UC_ARM_REG_R10],
            'r11': u.reg_read(UC_ARM_REG_R11) == init_regs[UC_ARM_REG_R11],
            'sp': u.reg_read(UC_ARM_REG_SP) == init_regs[UC_ARM_REG_SP],
        }
        return {
            'pc': hex(u.reg_read(UC_ARM_REG_PC)),
            'r0': hex(u.reg_read(UC_ARM_REG_R0)),
            'roster': bytes(u.mem_read(roster, 0x180)).hex(),
            'allocated': bytes(u.mem_read(0x8040000, alloc[0] * 0x200)).hex(),
            'events': events,
            'regs_preserved': all(regs_preserved.values()),
        }
    except Exception as e:
        return {'fault': str(e), 'pc': hex(u.reg_read(UC_ARM_REG_PC)), 'events': events}

def main():
    parser = argparse.ArgumentParser(description='Comprehensive differential test for fusion roster caller')
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    original = (root / 'extracted/exefs/code.bin').read_bytes()
    patched = args.image.read_bytes()
    if len(original) != len(patched):
        raise ValueError('image length mismatch')

    test_scenarios = [
        ('empty_rows', []),
        ('single_row', [(5, 1, 2, 1)]),
        ('standard_multi_race', [(8, 2, 3, 1), (3, 2, 1, 1), (9, 1, 4, 1), (10, 2, 2, 0), (4, 60, 2, 1)]),
        ('boundary_race_flags', [
            (3, 0, 1, 1),      # Race 0, flag 1 (valid min)
            (7, 55, 2, 1),     # Race 55, flag 1 (valid max)
            (8, 56, 3, 1),     # Race 56 (OOB, rejected)
            (9, 255, 4, 1),    # Race 255 (OOB, rejected)
            (2, 0, 5, 3),      # Flag 3 (bit 0 set, valid)
            (1, 0, 9, 0),      # Flag 0 (bit 0 unset, rejected)
            (4, 10, 1, 0xFFFE) # Flag 0xFFFE (bit 0 unset, rejected)
        ]),
    ]

    results = []
    # Standard valid input scenarios
    for name, rows in test_scenarios:
        a = run(original, rows)
        b = run(patched, rows)
        passed = (a == b and a.get('pc') == '0x100004' and 'fault' not in a and a.get('regs_preserved') is True)
        results.append({'scenario': name, 'category': 'valid_input', 'passed': passed, 'original': a, 'patched': b})

    # Limit testing 1: Counter overflow (256 demons wrap u8 count to 0 -> allocation skipped -> unmapped write fault)
    rows_overflow = [(i, 5, 1, 1) for i in range(256)]
    a_of = run(original, rows_overflow)
    b_of = run(patched, rows_overflow)
    of_parity = (
        'fault' in a_of and 'fault' in b_of and
        a_of['fault'] == b_of['fault'] and
        a_of['events'] == b_of['events']
    )
    results.append({
        'scenario': 'counter_overflow_256_unmapped_store_parity',
        'category': 'unhandled_limit_parity',
        'passed': of_parity,
        'original': a_of,
        'patched': b_of,
        'note': 'Both original and patched wrap u8 count to 0 and fault with UC_ERR_WRITE_UNMAPPED on pass-3 store due to missing defensive bounds check.'
    })

    # Limit testing 2: Allocation failure (AsdMem_Alloc returns 0 -> pass-3 store to null -> unmapped write fault)
    rows_alloc_fail = [(10, 2, 1, 1)]
    a_fail = run(original, rows_alloc_fail, fail_alloc_index=0)
    b_fail = run(patched, rows_alloc_fail, fail_alloc_index=0)
    alloc_fail_parity = (
        'fault' in a_fail and 'fault' in b_fail and
        a_fail['fault'] == b_fail['fault'] and
        a_fail['events'] == b_fail['events']
    )
    results.append({
        'scenario': 'allocation_failure_unmapped_store_parity',
        'category': 'unhandled_limit_parity',
        'passed': alloc_fail_parity,
        'original': a_fail,
        'patched': b_fail,
        'note': 'Both original and patched fault with UC_ERR_WRITE_UNMAPPED on pass-3 store when alloc returns 0 due to lack of null-check in original design.'
    })

    # Negative control: corrupt Thumb BLX opcode at pinned qsort call site
    mutant = bytearray(patched)
    site = 0x3ca030 - 0x100000
    word = struct.unpack_from('<I', mutant, site)[0]
    if word >> 24 != 0xfb:
        raise ValueError('expected Thumb BLX at pinned site')
    struct.pack_into('<I', mutant, site, (word & 0x00ffffff) | 0xeb000000)
    neg = run(bytes(mutant), test_scenarios[2][1])
    neg_detected = ('fault' in neg or neg.get('pc') != '0x100004' or neg != results[2]['original'])

    all_passed = all(x['passed'] for x in results) and neg_detected

    report = {
        'original_sha256': hashlib.sha256(original).hexdigest(),
        'image_sha256': hashlib.sha256(patched).hexdigest(),
        'scope': 'fusion roster caller, real Thumb qsort, race boundary limits, counter overflow (256 entries), allocation failure fault parity, callee-saved register preservation',
        'passed': all_passed,
        'total_cases': len(results),
        'passed_cases': sum(1 for x in results if x['passed']),
        'negative_control_detected': neg_detected,
        'cases': results,
        'limits': [
            'Table helpers (0x2C0EC4, 0x2C0E9C, 0x2C0E4C, 0x2B9364) and comparator (0x219600) are mocked.',
            'Allocation failure triggers immediate unmapped write fault on both original and patched; graceful recovery is absent by game design.',
            'Counter overflow wraps race count at 256 modulo 256; demons exceeding 255 per race trigger unallocated bucket fault.',
            'Does not establish whole-game equivalence.'
        ]
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps({
        'passed': report['passed'],
        'total_cases': report['total_cases'],
        'passed_cases': report['passed_cases'],
        'negative_control_detected': neg_detected,
        'image_sha256': report['image_sha256']
    }, indent=2))
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
