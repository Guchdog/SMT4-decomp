from pathlib import Path
import unicorn, struct, json, hashlib, argparse, sys
from unicorn.arm_const import *

root = Path(__file__).resolve().parents[1]
cmps = {0x206be8, 0x2e4534, 0x1f60dc, 0x2dc96c, 0x1f6174, 0x2dca04}

def run(code, mode, relocate_work=False, mutate_opt_to=None, bitfield_pattern=0xFF):
    u = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    u.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    u.mem_map(0x100000, 0x480000)
    u.mem_write(0x100000, code)
    u.mem_map(0x8000000, 0x50000)
    u.mem_map(0xfff0000, 0x10000)

    work = 0x8001000
    work2 = 0x8025000 # relocation target
    opt = 0x8009000
    bitfield = 0x800a000

    u.mem_write(0x44e190, struct.pack('<I', work))
    u.mem_write(opt + 0x15, bytes([mode]))
    u.mem_write(bitfield, bytes([bitfield_pattern]) * 256)

    for i in range(3):
        x = bytearray(0x40)
        struct.pack_into('<H', x, 0, i + 4)
        struct.pack_into('<H', x, 6, 1)
        struct.pack_into('<H', x, 0x38, i + 1)
        u.mem_write(0x8010000 + i * 0x40, bytes(x))

    # Initial register values to verify preservation
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
    u.reg_write(UC_ARM_REG_R0, bitfield)

    events = []

    def ret(uc, value=None):
        if value is not None:
            uc.reg_write(UC_ARM_REG_R0, value & 0xffffffff)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def hook(uc, addr, size, data):
        if addr == 0x2c4b30:
            dest = uc.reg_read(UC_ARM_REG_R0)
            n = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(dest, bytes(n))
            ret(uc)
        elif addr == 0x2b9364:
            i = uc.reg_read(UC_ARM_REG_R0)
            ret(uc, 0x8010000 + i * 0x40 if i < 3 else 0)
        elif addr == 0x29fae8:
            events.append(('page', uc.reg_read(UC_ARM_REG_R1)))
            if relocate_work:
                # Simulate work pointer relocation during setup
                old_bytes = bytes(uc.mem_read(work, 0x2000))
                uc.mem_write(work2, old_bytes)
                uc.mem_write(0x44e190, struct.pack('<I', work2))
                events.append(('relocate_work', hex(work2)))
            ret(uc)
        elif addr == 0x2a0fac:
            if mutate_opt_to is not None:
                uc.mem_write(opt + 0x15, bytes([mutate_opt_to]))
                events.append(('mutate_opt', mutate_opt_to))
            ret(uc, opt)
        elif addr == 0x2b7f0a:
            events.append(('qsort', bool(uc.reg_read(UC_ARM_REG_CPSR) & 32)))
        elif addr in cmps:
            events.append(('cmp', hex(addr)))
            a = uc.reg_read(UC_ARM_REG_R0)
            b = uc.reg_read(UC_ARM_REG_R1)
            x = struct.unpack('<I', uc.mem_read(a, 4))[0]
            y = struct.unpack('<I', uc.mem_read(b, 4))[0]
            cur_mode = uc.mem_read(opt + 0x15, 1)[0]
            val = (x > y) - (x < y)
            ret(uc, -val if cur_mode & 128 else val)

    u.hook_add(unicorn.UC_HOOK_CODE, hook)
    try:
        u.emu_start(0x1ee5a4, 0x100004, count=250000)
        target_work = work2 if relocate_work else work
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
        all_preserved = all(regs_preserved.values())
        return {
            'pc': hex(u.reg_read(UC_ARM_REG_PC)),
            'target_work_mem': bytes(u.mem_read(target_work + 0x5c8, 0x820)).hex(),
            'initial_work_flag': bytes(u.mem_read(work + 0x410, 1)).hex(),
            'events': events,
            'regs_preserved': all_preserved,
        }
    except Exception as e:
        return {'fault': str(e), 'pc': hex(u.reg_read(UC_ARM_REG_PC)), 'events': events}

def main():
    parser = argparse.ArgumentParser(description='Comprehensive skill-list caller and differential regression')
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    original = (root / 'extracted/exefs/code.bin').read_bytes()
    patched = args.image.read_bytes()
    if len(original) != len(patched):
        raise ValueError('image length mismatch')

    results = []

    # 1. Standard mode sweep
    modes = [0, 1, 129, 3, 131, 33, 161, 2, 4, 32, 0x80, 0xFF]
    for mode in modes:
        a = run(original, mode)
        b = run(patched, mode)
        passed = (a == b and a.get('pc') == '0x100004' and 'fault' not in a and a.get('regs_preserved') is True)
        results.append({'scenario': f'mode_{mode}', 'passed': passed, 'original': a, 'patched': b})

    # 2. Dynamic work relocation during UiPage_Setup
    for mode in (1, 33, 3):
        a = run(original, mode, relocate_work=True)
        b = run(patched, mode, relocate_work=True)
        passed = (a == b and a.get('pc') == '0x100004' and 'fault' not in a and a.get('regs_preserved') is True)
        results.append({'scenario': f'relocate_work_mode_{mode}', 'passed': passed, 'original': a, 'patched': b})

    # 3. Dynamic options mutation during UiMenu_GetSortOptions
    for mode in (1, 33):
        a = run(original, mode, mutate_opt_to=3)
        b = run(patched, mode, mutate_opt_to=3)
        passed = (a == b and a.get('pc') == '0x100004' and 'fault' not in a and a.get('regs_preserved') is True)
        results.append({'scenario': f'mutate_opt_{mode}_to_3', 'passed': passed, 'original': a, 'patched': b})

    # 4. Empty bitfield (no skills active)
    a = run(original, 1, bitfield_pattern=0x00)
    b = run(patched, 1, bitfield_pattern=0x00)
    passed = (a == b and a.get('pc') == '0x100004' and 'fault' not in a and a.get('regs_preserved') is True)
    results.append({'scenario': 'empty_bitfield', 'passed': passed, 'original': a, 'patched': b})

    # Negative control: corrupt comparator selection / call
    mutant = bytearray(patched)
    site = 0x1ee6e4 - 0x100000
    mutant[site:site+4] = struct.pack('<I', 0xeb032607)
    neg = run(bytes(mutant), 1)
    neg_detected = ('fault' in neg or neg.get('pc') != '0x100004' or neg != results[1]['original'])

    all_passed = all(x['passed'] for x in results) and neg_detected

    report = {
        'original_sha256': hashlib.sha256(original).hexdigest(),
        'image_sha256': hashlib.sha256(patched).hexdigest(),
        'scope': 'skill-list caller, real Thumb qsort, work-pointer relocation, mutable options, bitfield boundaries, ABI preservation',
        'passed': all_passed,
        'total_cases': len(results),
        'passed_cases': sum(1 for x in results if x['passed']),
        'negative_control_detected': neg_detected,
        'cases': results,
        'limits': [
            'Only synthetic skills and mocked table lookup are tested.',
            'Underlying hardware interrupts and multithreading are not simulated.',
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
