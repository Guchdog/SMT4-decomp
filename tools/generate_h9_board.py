#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h9.json for Milestone H9."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'camp-uniteeffect-init',
        'func': '0x002e315c',
        'name': 'UniteEffect_Init',
        'desc': 'Cathedral of Shadows 3D fusion summoning circle and lighting particle effect setup',
        'cand_src': 'experiments/semantic_equivalence/h9_camp_uniteeffect_init_candidate.cpp',
        'test_src': 'tools/h9_camp_uniteeffect_init_experiment.py',
        'contract_doc': 'docs/agent-work/h9-camp-uniteeffect-init-contract.md',
        'cand_doc': 'docs/agent-work/h9-camp-uniteeffect-init-candidate.md',
    },
    {
        'id': 'camp-biblemain-init',
        'func': '0x00269cc8',
        'name': 'bibleMain_Init',
        'desc': 'Demon Compendium Devil Book manager initialization and stereoscopic dual-screen draw tasks registration',
        'cand_src': 'experiments/semantic_equivalence/h9_camp_biblemain_init_candidate.cpp',
        'test_src': 'tools/h9_camp_biblemain_init_experiment.py',
        'contract_doc': 'docs/agent-work/h9-camp-biblemain-init-contract.md',
        'cand_doc': 'docs/agent-work/h9-camp-biblemain-init-candidate.md',
    },
    {
        'id': 'camp-biblelegionskill-init',
        'func': '0x003ab770',
        'name': 'bibleLegionSkill_Init',
        'desc': 'Cathedral of Shadows Legion Skill setup, task registration, and UI list initialization',
        'cand_src': 'experiments/semantic_equivalence/h9_camp_biblelegionskill_init_candidate.cpp',
        'test_src': 'tools/h9_camp_biblelegionskill_init_experiment.py',
        'contract_doc': 'docs/agent-work/h9-camp-biblelegionskill-init-contract.md',
        'cand_doc': 'docs/agent-work/h9-camp-biblelegionskill-init-candidate.md',
    },
    {
        'id': 'camp-biblelegiondraw-init',
        'func': '0x003ad300',
        'name': 'bibleLegionDraw_Init',
        'desc': 'Cathedral of Shadows Legion upper/lower stereoscopic draw manager, sprite binding and node setup',
        'cand_src': 'experiments/semantic_equivalence/h9_camp_biblelegiondraw_init_candidate.cpp',
        'test_src': 'tools/h9_camp_biblelegiondraw_init_experiment.py',
        'contract_doc': 'docs/agent-work/h9-camp-biblelegiondraw-init-contract.md',
        'cand_doc': 'docs/agent-work/h9-camp-biblelegiondraw-init-candidate.md',
    },
    {
        'id': 'camp-sortmenu-init',
        'func': '0x0029e63c',
        'name': 'SortMenu_Init',
        'desc': 'Demon fusion and compendium sorting modal and comparator dispatcher',
        'cand_src': 'experiments/semantic_equivalence/h9_camp_sortmenu_init_candidate.cpp',
        'test_src': 'tools/h9_camp_sortmenu_init_experiment.py',
        'contract_doc': 'docs/agent-work/h9-camp-sortmenu-init-contract.md',
        'cand_doc': 'docs/agent-work/h9-camp-sortmenu-init-candidate.md',
    },
    {
        'id': 'camp-unitectrl-roster',
        'func': '0x003c9ebc',
        'name': 'UniteCtrl_RosterPopulate',
        'desc': 'Demon fusion candidate roster counter, race bucket allocator, and qsort sorter',
        'cand_src': 'experiments/semantic_equivalence/h9_camp_unitectrl_roster_candidate.cpp',
        'test_src': 'tools/h9_camp_unitectrl_roster_experiment.py',
        'contract_doc': 'docs/agent-work/h9-camp-unitectrl-roster-contract.md',
        'cand_doc': 'docs/agent-work/h9-camp-unitectrl-roster-candidate.md',
    },
    {
        'id': 'camp-bibledevil-init',
        'func': '0x003a7ad8',
        'name': 'bibleDevil_Init',
        'desc': 'Compendium demon inspector, 3D model task registration, and UI list population',
        'cand_src': 'experiments/semantic_equivalence/h9_camp_bibledevil_init_candidate.cpp',
        'test_src': 'tools/h9_camp_bibledevil_init_experiment.py',
        'contract_doc': 'docs/agent-work/h9-camp-bibledevil-init-contract.md',
        'cand_doc': 'docs/agent-work/h9-camp-bibledevil-init-candidate.md',
    },
    {
        'id': 'camp-buttonhelp-init',
        'func': '0x0028d974',
        'name': 'ButtonHelp_Init',
        'desc': 'Cathedral of Shadows dynamic button prompt HUD and input helper',
        'cand_src': 'experiments/semantic_equivalence/h9_camp_buttonhelp_init_candidate.cpp',
        'test_src': 'tools/h9_camp_buttonhelp_init_experiment.py',
        'contract_doc': 'docs/agent-work/h9-camp-buttonhelp-init-contract.md',
        'cand_doc': 'docs/agent-work/h9-camp-buttonhelp-init-candidate.md',
    },
]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h9-cathedral-fusion-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H9 Cathedral of Shadows: Fusion and Compendium.',
    'depends_on': [],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'src/camp/unite.cpp',
        'src/camp/unite_extras.cpp',
        'src/camp/bible.cpp',
        'src/camp/compendium_search.cpp',
        'src/camp/whisper_event.cpp',
        'docs/reconstruction-milestones.md',
        'docs/milestones/H8-camp-menu-inventory-party.md'
    ],
    'write_paths': [
        'docs/agent-work/h9-cathedral-fusion-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H9 fusion and compendium subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h9-cathedral-fusion-recon-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of Cathedral of Shadows fusion and compendium architecture reconnaissance and boundary definitions.',
    'depends_on': ['h9-cathedral-fusion-recon'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'docs/agent-work/h9-cathedral-fusion-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h9-cathedral-fusion-recon-review.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify contract boundaries, calling conventions, and ABI preservation expectations.',
        'Approve task division and candidate scope for H9 Cathedral of Shadows milestone.'
    ],
    'validation_plan': [
        'Confirm completeness of architecture reconnaissance and absence of unsupported assumptions.'
    ]
})

for s in subsystems:
    sid = s['id']
    sname = s['name']
    sfunc = s['func']
    fclaim = [sfunc]
    c_review_doc = s['contract_doc'].replace('.md', '-review.md')
    cand_review_doc = s['cand_doc'].replace('.md', '-review.md')
    diff_doc = f"docs/agent-work/h9-{sid}-differential.md"
    diff_review_doc = f"docs/agent-work/h9-{sid}-differential-review.md"
    comp_doc = f"docs/agent-work/h9-{sid}-composition.md"
    comp_review_doc = f"docs/agent-work/h9-{sid}-composition-review.md"
    stag_doc = f"docs/agent-work/h9-{sid}-staging.md"
    stag_review_doc = f"docs/agent-work/h9-{sid}-staging-review.md"

    # Contract
    tasks.append({
        'id': f'h9-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Formalize contract, parameters, registers, and memory effects for {sname} ({sfunc}).',
        'depends_on': ['h9-cathedral-fusion-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['src/camp/unite.cpp', 'src/camp/unite_extras.cpp', 'src/camp/bible.cpp'],
        'write_paths': [s['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Accurately specify semantics of {sname}.', 'Specify test fixtures and mutation controls.'],
        'validation_plan': ['Static disassembly and register effect verification against code.bin.']
    })

    # Contract Review
    tasks.append({
        'id': f'h9-{sid}-contract-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of {sname} contract specification.',
        'depends_on': [f'h9-{sid}-contract'],
        'function_claims': fclaim,
        'read_paths': [s['contract_doc']],
        'write_paths': [c_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify contract fidelity against ARM disassembled instructions.'],
        'validation_plan': ['Audit edge cases, register clobbers, and pointer validations.']
    })

    # Candidate
    tasks.append({
        'id': f'h9-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement readable, editable C++ candidate for {sname} with mutation control.',
        'depends_on': [f'h9-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [s['contract_doc']],
        'write_paths': [s['cand_src'], s['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            f'Implement {sname} candidate and verified mutation control.',
            'Ensure compiled ARM size fits strictly within the original binary function window.'
        ],
        'validation_plan': ['Compile with tools/build_check.py (armv6k clang) and check ELF size.']
    })

    # Candidate Review
    tasks.append({
        'id': f'h9-{sid}-candidate-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of {sname} candidate implementation.',
        'depends_on': [f'h9-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['cand_doc']],
        'write_paths': [cand_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [
            'Audit C++ syntax, memory safety, ABI conformance, and headroom margin.',
            'Verify mutation control triggers distinct divergence.'
        ],
        'validation_plan': ['Check ELF symbol tables and relocation bindings.']
    })

    # Differential
    tasks.append({
        'id': f'h9-{sid}-differential',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Execute offline Unicorn differential test for {sname} against original ARM code.',
        'depends_on': [f'h9-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['test_src']],
        'write_paths': [diff_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            f'Pass Unicorn emulation comparing original {sname} against candidate.',
            'Confirm mutation control is detected with non-zero divergence.'
        ],
        'validation_plan': [f'Execute python {s["test_src"]}.']
    })

    # Differential Review
    tasks.append({
        'id': f'h9-{sid}-differential-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of offline differential test results for {sname}.',
        'depends_on': [f'h9-{sid}-differential'],
        'function_claims': fclaim,
        'read_paths': [diff_doc],
        'write_paths': [diff_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm zero divergence in state effects between original and candidate.'],
        'validation_plan': ['Audit differential execution logs and register dump hashes.']
    })

    # Composition
    tasks.append({
        'id': f'h9-{sid}-composition',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Verify caller composition and interworking for {sname} in integrated context.',
        'depends_on': [f'h9-{sid}-differential-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [comp_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            f'Verify caller interface and stack alignment for {sname}.',
            'Ensure all external calls resolve cleanly without ABI violations.'
        ],
        'validation_plan': ['Audit caller sequence and callee stack frame preservation.']
    })

    # Composition Review
    tasks.append({
        'id': f'h9-{sid}-composition-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of caller composition for {sname}.',
        'depends_on': [f'h9-{sid}-composition'],
        'function_claims': fclaim,
        'read_paths': [comp_doc],
        'write_paths': [comp_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Validate absence of stack corruption or register clobbering across callers.'],
        'validation_plan': ['Review composition verification reports.']
    })

    # Staging
    tasks.append({
        'id': f'h9-{sid}-staging',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Stage candidate object and relocation records for {sname} into composite image builder.',
        'depends_on': [f'h9-{sid}-composition-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [stag_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [f'Successfully link and stage {sname} into staging pipeline.'],
        'validation_plan': ['Check ELF relocation resolution and window bounds.']
    })

    # Staging Review
    tasks.append({
        'id': f'h9-{sid}-staging-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of staged candidate {sname}.',
        'depends_on': [f'h9-{sid}-staging'],
        'function_claims': fclaim,
        'read_paths': [stag_doc],
        'write_paths': [stag_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify candidate is properly aligned, relocations patched, and padding clean.'],
        'validation_plan': ['Confirm relocation offset calculations and target VMA mapping.']
    })

# Staging Composite Image
staging_deps = [f"h9-{s['id']}-staging-review" for s in subsystems]

tasks.append({
    'id': 'h9-staged-image-patch',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 validated H9 semantic candidates into final staged executable image and IPS patch.',
    'depends_on': staging_deps,
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['tools/h9_staged_image_patch.py'] + [s['cand_src'] for s in subsystems],
    'write_paths': [
        'build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.bin',
        'build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.ips',
        'build/agent-work/H9-semantic/h9-integrated-stage/report.json',
        'docs/agent-work/h9-staged-image-patch.md'
    ],
    'compiler_slots': 2,
    'exclusive_resources': [],
    'acceptance': [
        'Successfully compile and relocate all 8 candidates onto the H8 base image.',
        'Generate valid code.h9-final.bin and byte-accurate code.h9-final.ips.',
        'Verify 100% round-trip fidelity through apply_ips.'
    ],
    'validation_plan': ['Run tools/h9_staged_image_patch.py.']
})

tasks.append({
    'id': 'h9-staged-image-patch-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H9 final composite binary and IPS patch artifacts.',
    'depends_on': ['h9-staged-image-patch'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h9-staged-image-patch.md', 'build/agent-work/H9-semantic/h9-integrated-stage/report.json'],
    'write_paths': ['docs/agent-work/h9-staged-image-patch-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Verify binary integrity, non-overlapping windows, and SHA-256 hashes.'],
    'validation_plan': ['Audit report.json manifest and verify zero regression outside target windows.']
})

tasks.append({
    'id': 'h9-offline-composite-gates',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Execute full suite of offline composite differential gates and caller compositions for H9 image.',
    'depends_on': ['h9-staged-image-patch-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['tools/build_h9_all.py', 'build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.bin'],
    'write_paths': ['docs/agent-work/h9-offline-composite-gates.md'],
    'compiler_slots': 2,
    'exclusive_resources': [],
    'acceptance': [
        'All 8 candidates pass individual Unicorn offline differential validations.',
        'Zero regressions across combined candidate assembly and ARM/Thumb interworking bits.'
    ],
    'validation_plan': ['Run tools/build_h9_all.py and all 8 experiment scripts.']
})

tasks.append({
    'id': 'h9-offline-composite-gates-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of offline composite gates and interworking integrity.',
    'depends_on': ['h9-offline-composite-gates'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h9-offline-composite-gates.md'],
    'write_paths': ['docs/agent-work/h9-offline-composite-gates-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Approve offline test results prior to emulator runtime verification.'],
    'validation_plan': ['Audit gate execution outputs and mutation sensitivity logs.']
})

tasks.append({
    'id': 'h9-autonomous-fusion-verify',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Autonomous runtime verification in Azahar emulator: Title, Save Load, Field, and Cathedral of Shadows Fusion & Compendium sequences.',
    'depends_on': ['h9-offline-composite-gates-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['tools/h3_autonomous_verify.py', 'code.h9-final.ips'],
    'write_paths': ['docs/agent-work/h9-autonomous-fusion-verify.md'],
    'compiler_slots': 0,
    'exclusive_resources': ['emulator_session'],
    'acceptance': [
        'Run paired autonomous test via GDB RSP loopback stub.',
        '0 register differences across Title, Save Load, 250 Field scene ticks, and Cathedral of Shadows fusion & compendium subsystems.'
    ],
    'validation_plan': ['Execute autonomous verify script and generate paired report.json.']
})

tasks.append({
    'id': 'h9-autonomous-fusion-verify-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of autonomous paired runtime verification for Milestone H9.',
    'depends_on': ['h9-autonomous-fusion-verify'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h9-autonomous-fusion-verify.md'],
    'write_paths': ['docs/agent-work/h9-autonomous-fusion-verify-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm 100% paired equivalence with zero register or state differences.'],
    'validation_plan': ['Audit runtime report metrics and save file hash integrity.']
})

tasks.append({
    'id': 'h9-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Formalize closure of Milestone H9 across documentation and ledger tracking.',
    'depends_on': ['h9-autonomous-fusion-verify-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/milestones/H9-cathedral-fusion-compendium.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'write_paths': ['docs/milestones/H9-cathedral-fusion-compendium.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Update documentation marking Milestone H9 as completed and closed.',
        'Ensure clean git state and 0 errors from tools/agent_workflow.py check.'
    ],
    'validation_plan': ['Run python tools/agent_workflow.py check.']
})

board = {
    'schema_version': 1,
    'batch': 'batch-h9-001',
    'milestone': 'H9',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H9 (Cathedral of Shadows: Fusion & Compendium), covering 3D fusion effect initialization (UniteEffect_Init), Demon Compendium manager (bibleMain_Init), Legion Skill setup and UI registration (bibleLegionSkill_Init), Legion stereo draw manager (bibleLegionDraw_Init), sort menu modal dispatcher (SortMenu_Init), demon fusion candidate roster counting, categorization and sorting (UniteCtrl_RosterPopulate), compendium demon inspector and task registration (bibleDevil_Init), and button prompt HUD helper (ButtonHelp_Init) with full offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h9.json',
        'config/reconstruction.json',
        'docs/milestones/H9-cathedral-fusion-compendium.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_path = ROOT / 'config/agent-workflows/h9.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(board, f, indent=2)

print(f'Successfully wrote h9.json with {len(tasks)} tasks to {out_path}')
