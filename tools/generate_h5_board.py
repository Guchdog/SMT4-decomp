#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h5.json for Milestone H5."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'party-active',
        'func': '0x001d29c8',
        'name': 'btlUnit_CheckPartyActive',
        'desc': 'party active status evaluation across active, reserve, and guest slots',
        'cand_src': 'experiments/semantic_equivalence/h5_btl_unit_check_party_active_candidate.cpp',
        'test_src': 'tools/h5_btl_unit_check_party_active_experiment.py',
        'contract_doc': 'docs/agent-work/h5-btl-unit-party-active-contract.md',
        'cand_doc': 'docs/agent-work/h5-btl-unit-party-active-candidate.md',
    },
    {
        'id': 'demon-unit',
        'func': '0x002ae464',
        'name': 'Btl_IsDemonUnit',
        'desc': 'demon unit ID discrimination threshold logic',
        'cand_src': 'experiments/semantic_equivalence/h5_btl_is_demon_unit_candidate.cpp',
        'test_src': 'tools/h5_btl_is_demon_unit_experiment.py',
        'contract_doc': 'docs/agent-work/h5-btl-is-demon-unit-contract.md',
        'cand_doc': 'docs/agent-work/h5-btl-is-demon-unit-candidate.md',
    },
    {
        'id': 'target-select-draw',
        'func': '0x002f4aa4',
        'name': 'btlTargetSelect_DrawUp',
        'desc': 'target selection top screen rendering dispatch for mode 1 and mode 2',
        'cand_src': 'experiments/semantic_equivalence/h5_btl_target_select_draw_up_candidate.cpp',
        'test_src': 'tools/h5_btl_target_select_draw_up_experiment.py',
        'contract_doc': 'docs/agent-work/h5-btl-target-select-draw-contract.md',
        'cand_doc': 'docs/agent-work/h5-btl-target-select-draw-candidate.md',
    },
    {
        'id': 'target-select-calc',
        'func': '0x002e06bc',
        'name': 'btlTargetSelect_Calc',
        'desc': 'target selection cursor animation update and angle interpolation',
        'cand_src': 'experiments/semantic_equivalence/h5_btl_target_select_calc_candidate.cpp',
        'test_src': 'tools/h5_btl_target_select_calc_experiment.py',
        'contract_doc': 'docs/agent-work/h5-btl-target-select-calc-contract.md',
        'cand_doc': 'docs/agent-work/h5-btl-target-select-calc-candidate.md',
    },
    {
        'id': 'help-init',
        'func': '0x001d2528',
        'name': 'btlHelp_Init',
        'desc': 'battle help modal workspace initialization and task registration',
        'cand_src': 'experiments/semantic_equivalence/h5_btl_help_init_candidate.cpp',
        'test_src': 'tools/h5_btl_help_init_experiment.py',
        'contract_doc': 'docs/agent-work/h5-btl-help-init-contract.md',
        'cand_doc': 'docs/agent-work/h5-btl-help-init-candidate.md',
    },
    {
        'id': 'talk-init',
        'func': '0x001d2610',
        'name': 'btlTalk_Init',
        'desc': 'battle demon negotiation talk modal workspace and buffer setup',
        'cand_src': 'experiments/semantic_equivalence/h5_btl_talk_init_candidate.cpp',
        'test_src': 'tools/h5_btl_talk_init_experiment.py',
        'contract_doc': 'docs/agent-work/h5-btl-talk-init-contract.md',
        'cand_doc': 'docs/agent-work/h5-btl-talk-init-candidate.md',
    },
    {
        'id': 'release-state',
        'func': '0x002b8a80',
        'name': 'Btl_ReleaseState',
        'desc': 'combat sub-object state lifecycle checking and safe deallocation',
        'cand_src': 'experiments/semantic_equivalence/h5_btl_release_state_candidate.cpp',
        'test_src': 'tools/h5_btl_release_state_experiment.py',
        'contract_doc': 'docs/agent-work/h5-btl-release-state-contract.md',
        'cand_doc': 'docs/agent-work/h5-btl-release-state-candidate.md',
    },
    {
        'id': 'set-channel-param',
        'func': '0x0011311c',
        'name': 'Btl_SetChannelParameter',
        'desc': 'combat audio and display channel parameter assignment',
        'cand_src': 'experiments/semantic_equivalence/h5_btl_set_channel_param_candidate.cpp',
        'test_src': 'tools/h5_btl_set_channel_param_experiment.py',
        'contract_doc': 'docs/agent-work/h5-btl-set-channel-param-contract.md',
        'cand_doc': 'docs/agent-work/h5-btl-set-channel-param-candidate.md',
    },
]

tasks = []

# Overall recon
tasks.append({
    'id': 'h5-combat-architecture-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Map minimal combat subsystem architecture, entry points, unit manager, target selection, modal dialogs, and channel parameters.',
    'depends_on': [],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'src/battle/btl_main.cpp',
        'src/battle/btl_ui.cpp',
        'src/battle/btl_target_select.cpp',
        'include/battle/battle.h',
        'include/battle/btl_main.h',
        'docs/reconstruction-milestones.md',
        'docs/milestones/H4-exploration-minimum.md'
    ],
    'write_paths': [
        'docs/agent-work/h5-combat-architecture-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H5 minimal combat subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h5-combat-architecture-recon-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of minimal combat architecture reconnaissance and subsystem boundary definitions.',
    'depends_on': ['h5-combat-architecture-recon'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'docs/agent-work/h5-combat-architecture-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h5-combat-architecture-recon-review.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify contract boundaries, calling conventions, and ABI preservation expectations.',
        'Approve task division and candidate scope for H5 minimal combat milestone.'
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
    diff_doc = f"docs/agent-work/h5-{sid}-differential.md"
    diff_review_doc = f"docs/agent-work/h5-{sid}-differential-review.md"
    comp_doc = f"docs/agent-work/h5-{sid}-composition.md"
    comp_review_doc = f"docs/agent-work/h5-{sid}-composition-review.md"
    stag_doc = f"docs/agent-work/h5-{sid}-staging.md"
    stag_review_doc = f"docs/agent-work/h5-{sid}-staging-review.md"

    # Contract
    tasks.append({
        'id': f'h5-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Formalize contract, parameters, registers, and memory effects for {sname} ({sfunc}).',
        'depends_on': ['h5-combat-architecture-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['src/battle/btl_main.cpp', 'src/battle/btl_ui.cpp', 'include/battle/battle.h'],
        'write_paths': [s['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Accurately specify semantics of {sname}.', 'Specify test fixtures and mutation controls.'],
        'validation_plan': ['Static disassembly and register effect verification against code.bin.']
    })

    # Contract Review
    tasks.append({
        'id': f'h5-{sid}-contract-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of {sname} contract specification.',
        'depends_on': [f'h5-{sid}-contract'],
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
        'id': f'h5-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Implement readable C++ candidate for {sname} in {s['cand_src']}.",
        'depends_on': [f'h5-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [s['contract_doc'], c_review_doc],
        'write_paths': [s['cand_src'], s['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [f'Generate clean C++ compiling with Clang ARMv6K under {sfunc} window size.'],
        'validation_plan': ['Compile with tools/build_check.py compile_tu_armv6k.']
    })

    # Candidate Review
    tasks.append({
        'id': f'h5-{sid}-candidate-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of C++ candidate implementation for {sname}.',
        'depends_on': [f'h5-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['cand_doc']],
        'write_paths': [cand_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify candidate readability, types, and compiler artifact size.'],
        'validation_plan': ['Inspect code and verify object section boundaries.']
    })

    # Differential
    tasks.append({
        'id': f'h5-{sid}-differential',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Execute offline Unicorn differential test runner {s['test_src']}.",
        'depends_on': [f'h5-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['test_src']],
        'write_paths': [diff_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Pass all differential fixtures with 0 mismatches and detect mutation control.'],
        'validation_plan': ['Execute Python test script and capture JSON report.']
    })

    # Differential Review
    tasks.append({
        'id': f'h5-{sid}-differential-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of differential test results for {sname}.',
        'depends_on': [f'h5-{sid}-differential'],
        'function_claims': fclaim,
        'read_paths': [diff_doc],
        'write_paths': [diff_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify differential execution logs and confirm mutation failure.'],
        'validation_plan': ['Audit report metrics and hash integrity.']
    })

    # Composition
    tasks.append({
        'id': f'h5-{sid}-composition',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Test caller integration and context composition for {sname}.',
        'depends_on': [f'h5-{sid}-differential-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['test_src']],
        'write_paths': [comp_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Verify caller-composition contract under real memory layout.'],
        'validation_plan': ['Run caller composition suites and check register preservation.']
    })

    # Composition Review
    tasks.append({
        'id': f'h5-{sid}-composition-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of caller composition for {sname}.',
        'depends_on': [f'h5-{sid}-composition'],
        'function_claims': fclaim,
        'read_paths': [comp_doc],
        'write_paths': [comp_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Audit caller composition evidence and side effect preservation.'],
        'validation_plan': ['Verify caller context preservation.']
    })

    # Staging
    tasks.append({
        'id': f'h5-{sid}-staging',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Stage candidate {sname} into composite H5 mod image.',
        'depends_on': [f'h5-{sid}-composition-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [stag_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Verify patch window bounds and symbol resolution.'],
        'validation_plan': ['Verify candidate fits in original binary window.']
    })

    # Staging Review
    tasks.append({
        'id': f'h5-{sid}-staging-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of staging for {sname}.',
        'depends_on': [f'h5-{sid}-staging'],
        'function_claims': fclaim,
        'read_paths': [stag_doc],
        'write_paths': [stag_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve candidate inclusion in composite binary image.'],
        'validation_plan': ['Verify candidate footprint and absence of relocations.']
    })

# Final integrated tasks
tasks.append({
    'id': 'h5-staged-image-patch',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 H5 combat candidates over H4 final base and generate code.h5-final.bin and code.h5-final.ips.',
    'depends_on': [f"h5-{s['id']}-staging-review" for s in subsystems],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [s['cand_src'] for s in subsystems] + ['tools/h5_staged_image_patch.py'],
    'write_paths': ['docs/agent-work/h5-staged-image-patch.md'],
    'compiler_slots': 2,
    'exclusive_resources': [],
    'acceptance': [
        'Compile all 8 candidate translation units and resolve target symbols.',
        'Produce code.h5-final.bin and verified code.h5-final.ips patch.'
    ],
    'validation_plan': ['Run tools/h5_staged_image_patch.py and verify IPS round-trip.']
})

tasks.append({
    'id': 'h5-staged-image-patch-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H5 staged composite binary image and IPS patch.',
    'depends_on': ['h5-staged-image-patch'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h5-staged-image-patch.md'],
    'write_paths': ['docs/agent-work/h5-staged-image-patch-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Verify composite image SHA-256 and IPS patch validity.'],
    'validation_plan': ['Check binary hash pins and candidate window sizes.']
})

tasks.append({
    'id': 'h5-offline-composite-gates',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Verify offline-first gates (ARM/Thumb interworking, 4-byte alignment, 0 relocations) for composite H5.',
    'depends_on': ['h5-staged-image-patch-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h5-staged-image-patch.md'],
    'write_paths': ['docs/agent-work/h5-offline-composite-gates.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['All 8 candidate windows verify ARM mode (bit 0 = 0) and 4-byte aligned.'],
    'validation_plan': ['Inspect entry points and symbol alignments in staged ELF/binary.']
})

tasks.append({
    'id': 'h5-offline-composite-gates-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of offline-first composite gates for H5.',
    'depends_on': ['h5-offline-composite-gates'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h5-offline-composite-gates.md'],
    'write_paths': ['docs/agent-work/h5-offline-composite-gates-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm pass of all offline interworking and alignment gates.'],
    'validation_plan': ['Audit gate execution logs.']
})

tasks.append({
    'id': 'h5-autonomous-combat-verify',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Execute autonomous paired runtime verification in Azahar emulator loopback stub with code.h5-final.ips.',
    'depends_on': ['h5-offline-composite-gates-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['tools/h3_autonomous_verify.py'],
    'write_paths': ['docs/agent-work/h5-autonomous-combat-verify.md'],
    'compiler_slots': 0,
    'exclusive_resources': ['emulator_loopback'],
    'acceptance': [
        'Complete paired execution of original vs patched game with 0 functional regressions.',
        'Verify Title Screen, Save loading, Field scene callbacks (250 ticks), and save data integrity.'
    ],
    'validation_plan': ['Run tools/h3_autonomous_verify.py and record runtime JSON report.']
})

tasks.append({
    'id': 'h5-autonomous-combat-verify-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of autonomous paired runtime verification for Milestone H5.',
    'depends_on': ['h5-autonomous-combat-verify'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h5-autonomous-combat-verify.md'],
    'write_paths': ['docs/agent-work/h5-autonomous-combat-verify-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm 100% paired equivalence with zero register or state differences.'],
    'validation_plan': ['Audit runtime report metrics and save file hash integrity.']
})

tasks.append({
    'id': 'h5-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Formalize closure of Milestone H5 across documentation and ledger tracking.',
    'depends_on': ['h5-autonomous-combat-verify-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/milestones/H5-combat-minimum.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'write_paths': ['docs/milestones/H5-combat-minimum.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Update documentation marking Milestone H5 as completed and closed.',
        'Ensure clean git state and 0 errors from tools/agent_workflow.py check.'
    ],
    'validation_plan': ['Run python tools/agent_workflow.py check.']
})

board = {
    'schema_version': 1,
    'batch': 'batch-h5-001',
    'milestone': 'H5',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H5 (Minimal Combat), covering party activity evaluation, demon unit discrimination, target selection rendering and interpolation, help and negotiation modal workspaces, combat state release, and channel parameter dispatch with full offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h5.json',
        'config/reconstruction.json',
        'docs/milestones/H5-combat-minimum.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_path = ROOT / 'config/agent-workflows/h5.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(board, f, indent=2)

print(f'Successfully wrote h5.json with {len(tasks)} tasks to {out_path}')
