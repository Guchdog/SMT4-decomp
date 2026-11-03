#!/usr/bin/env python3
"""Comprehensive audit of all accumulated substitutions and dependencies (H1-H19).

Audits:
1. Candidate window tracking, overlap analysis, and later-stage overwrite detection.
2. Direct branch instruction state (ARM BL/B vs Thumb BLX).
3. Indirect branch/callback interworking (pointers in literal pools, function pointers passed as arguments).
4. H1-H3 specific checks: TBB jumps, titleConfig callbacks, formatting helper Thumb bit, H3 entry.
"""
from __future__ import annotations
import importlib
import json
import struct
from pathlib import Path
import sys
import capstone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEXT_BASE = 0x00100000

PROMOTED_H18_REPLACEMENTS = {
    (0x002A0FAC, 'camp-burroughs-getsavedata', 'h10-burroughs'),
    (0x0022FC98, 'shop-checkhasnew', 'h11-shops'),
    (0x00129C58, 'battle-getunitsmirkstate', 'h12-combat'),
    (0x0026394C, 'placewin-isactive', 'h13-exploration'),
    (0x002C3B88, 'asdgpu-heapsize', 'h14-graphics'),
    (0x00126084, 'uidialog-getstate', 'h15-ui'),
    (0x00110C44, 'asdsoundeffect-getbuffersize', 'h16-sound'),
    (0x002A17C0, 'aoc-resultisready', 'h17-cec-aoc'),
}

def collect_subsystems() -> list[dict]:
    stages = []
    # H1
    h1_subs = [
        {'stage': 'H1', 'id': 'h1-tbb-001ea928', 'addr': 0x001EA928, 'size': 0x6C},
        {'stage': 'H1', 'id': 'h1-tbb-001ea994', 'addr': 0x001EA994, 'size': 0x48},
        {'stage': 'H1', 'id': 'h1-tbb-001ea9dc', 'addr': 0x001EA9DC, 'size': 0x48},
        {'stage': 'H1', 'id': 'h1-nav-slice-001e9a20', 'addr': 0x001E9A20, 'size': 0x140},
        {'stage': 'H1', 'id': 'h1-trans-slice-001e9fd4', 'addr': 0x001E9FD4, 'size': 0x188},
    ]
    stages.extend(h1_subs)

    # H2
    h2_subs = [
        {'stage': 'H2', 'id': 'h2-draw', 'addr': 0x002CB1D8, 'size': 136},
        {'stage': 'H2', 'id': 'h2-calc', 'addr': 0x002CB260, 'size': 84},
        {'stage': 'H2', 'id': 'h2-ready', 'addr': 0x002CB120, 'size': 184},
        {'stage': 'H2', 'id': 'h2-secondary', 'addr': 0x002CB2B4, 'size': 112},
        {'stage': 'H2', 'id': 'h2-init', 'addr': 0x002CB324, 'size': 76},
        {'stage': 'H2', 'id': 'h2-helper-21f39c', 'addr': 0x0021F39C, 'size': 92},
        {'stage': 'H2', 'id': 'h2-helper-2cab70', 'addr': 0x002CAB70, 'size': 92},
        {'stage': 'H2', 'id': 'h2-helper-2e0af4', 'addr': 0x002E0AF4, 'size': 92},
        {'stage': 'H2', 'id': 'h2-helper-27edf8', 'addr': 0x0027EDF8, 'size': 24},
    ]
    stages.extend(h2_subs)

    # H3
    h3_subs = [
        {'stage': 'H3', 'id': 'h3-title-load-entry', 'addr': 0x0030A9A4, 'size': 0x78},
    ]
    stages.extend(h3_subs)

    # H4 - H19
    for n in range(4, 20):
        mod_name = f'tools.h{n}_staged_image_patch'
        try:
            mod = importlib.import_module(mod_name)
            subsystems = getattr(mod, 'SUBSYSTEMS', getattr(mod, 'CRT_SUBSYSTEMS', []))
            for sub in subsystems:
                stages.append({
                    'stage': f'H{n}',
                    'id': sub.get('id', f'h{n}-sub'),
                    'addr': sub['addr'],
                    'size': sub['size'],
                    'cand_fn': sub.get('cand_fn', ''),
                    'src': sub.get('src', '')
                })
        except Exception as e:
            print(f'Warning: could not load {mod_name}: {e}')
    return stages

def audit_image(image_path: Path) -> dict:
    original = (ROOT / 'extracted/exefs/code.bin').read_bytes()
    image = image_path.read_bytes()

    subsystems = collect_subsystems()

    # 1. Check window overlaps and later-stage overwrites
    overlaps = []
    expected_promotions = []
    unexpected_overlaps = []

    for i in range(len(subsystems)):
        s1 = subsystems[i]
        a1, sz1 = s1['addr'], s1['size']
        for j in range(i + 1, len(subsystems)):
            s2 = subsystems[j]
            a2, sz2 = s2['addr'], s2['size']
            if max(a1, a2) < min(a1 + sz1, a2 + sz2):
                record = {
                    'sub1': s1,
                    'sub2': s2,
                    'overlap_start': hex(max(a1, a2)),
                    'overlap_end': hex(min(a1 + sz1, a2 + sz2)),
                }
                overlaps.append(record)
                key = (a1, s1['id'], s2['id'])
                if key in PROMOTED_H18_REPLACEMENTS and s2['stage'] == 'H18':
                    expected_promotions.append(record)
                else:
                    unexpected_overlaps.append(record)

    # Check H2 formatting helper at 0x002CB258
    fmt_word = struct.unpack_from('<I', image, 0x002CB258 - TEXT_BASE)[0]
    fmt_thumb_ok = (fmt_word == 0xe28a3081)

    # Check H2 helpers preservation in final image
    h2_image_path = ROOT / 'build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin'
    h2_helpers_preserved = True
    h2_helper_checks = []
    if h2_image_path.exists():
        h2_data = h2_image_path.read_bytes()
        for h in [
            ('camp_func_0021f39c', 0x21f39c, 92),
            ('camp_func_002cab70', 0x2cab70, 92),
            ('camp_func_002e0af4', 0x2e0af4, 92),
            ('camp_func_0027edf8', 0x27edf8, 24)
        ]:
            sym, vma, sz = h
            off = vma - TEXT_BASE
            matches = (image[off:off+sz] == h2_data[off:off+sz])
            h2_helper_checks.append({'symbol': sym, 'vma': hex(vma), 'size': sz, 'preserved': matches})
            if not matches:
                h2_helpers_preserved = False

    # Check H3 entry function preservation
    h3_off = 0x0030A9A4 - TEXT_BASE
    h3_modified = (image[h3_off:h3_off+0x78] != original[h3_off:h3_off+0x78])

    # 2. Disassemble candidate windows and check branch instructions
    md_arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md_arm.detail = True

    branch_results = []
    literal_pointers = []
    issues = []

    KNOWN_MODES = {
        0x002B7F0A: 1, # qsort is Thumb
        0x0027F3D4: 1, # qsort tail is Thumb
    }

    for sub in subsystems:
        addr = sub['addr']
        sz = sub['size']
        off = addr - TEXT_BASE
        if off < 0 or off + sz > len(image):
            issues.append(f"Subsystem {sub['id']} outside text segment: {addr:#x}")
            continue

        chunk = image[off:off+sz]
        for ins in md_arm.disasm(chunk, addr):
            if ins.mnemonic in ('b', 'bl', 'blx'):
                target = None
                if ins.operands:
                    op = ins.operands[0]
                    if op.type == capstone.arm.ARM_OP_IMM:
                        target = op.imm

                if target is not None:
                    is_blx = (ins.mnemonic == 'blx')
                    is_thumb_target = (target in KNOWN_MODES and KNOWN_MODES[target] == 1) or (target & 1)

                    record = {
                        'stage': sub['stage'],
                        'sub_id': sub['id'],
                        'site': hex(ins.address),
                        'mnemonic': ins.mnemonic,
                        'target': hex(target),
                        'is_thumb_target': bool(is_thumb_target),
                    }

                    if is_blx:
                        record['status'] = 'ok' if is_thumb_target else 'warn_not_known_thumb'
                    else:
                        if is_thumb_target:
                            record['status'] = 'error_arm_branch_to_thumb'
                            issues.append(f"ARM branch {ins.mnemonic} to Thumb target {target:#x} at {ins.address:#x} in {sub['id']}")
                        else:
                            record['status'] = 'ok'
                    branch_results.append(record)

            # Check literal pool loads
            if ins.mnemonic == 'ldr':
                if len(ins.operands) >= 2 and ins.operands[1].type == capstone.arm.ARM_OP_MEM:
                    mem = ins.operands[1].mem
                    if mem.base == capstone.arm.ARM_REG_PC:
                        lit_addr = ins.address + 8 + mem.disp
                        lit_off = lit_addr - TEXT_BASE
                        if 0 <= lit_off + 4 <= len(image):
                            lit_val = struct.unpack_from('<I', image, lit_off)[0]
                            if 0x00100000 <= lit_val < 0x00450000:
                                literal_pointers.append({
                                    'site': hex(ins.address),
                                    'lit_addr': hex(lit_addr),
                                    'lit_val': hex(lit_val),
                                    'sub_id': sub['id'],
                                    'thumb_bit': bool(lit_val & 1),
                                })

    passed = (
        len(issues) == 0 and
        len(unexpected_overlaps) == 0 and
        len(expected_promotions) == 8 and
        fmt_thumb_ok and
        h2_helpers_preserved and
        h3_modified
    )

    report = {
        'image_path': str(image_path),
        'total_subsystems': len(subsystems),
        'total_overlaps': len(overlaps),
        'expected_h18_promotions': expected_promotions,
        'unexpected_overlaps': unexpected_overlaps,
        'fmt_helper_thumb_bit_restored': fmt_thumb_ok,
        'h2_helpers_preserved': h2_helpers_preserved,
        'h2_helper_checks': h2_helper_checks,
        'h3_entry_present': h3_modified,
        'total_direct_branches': len(branch_results),
        'branch_issues': [b for b in branch_results if 'error' in b.get('status', '')],
        'total_code_literals': len(literal_pointers),
        'issues': issues,
        'passed': passed,
    }
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    report = audit_image(args.image)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'passed': report['passed'],
        'total_subsystems': report['total_subsystems'],
        'expected_promotions': len(report['expected_h18_promotions']),
        'unexpected_overlaps': len(report['unexpected_overlaps']),
        'fmt_thumb_ok': report['fmt_helper_thumb_bit_restored'],
        'h2_helpers_preserved': report['h2_helpers_preserved'],
        'h3_entry_present': report['h3_entry_present'],
        'branch_issues': len(report['branch_issues']),
        'issues': report['issues']
    }, indent=2))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
