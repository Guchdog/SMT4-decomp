#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h18.json for Milestone H18."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'h10-burroughs',
        'func': '0x002a0fac',
        'name': 'Camp_Burroughs_GetSaveData',
        'desc': 'Canonical promotion of Burroughs save data resolver',
        'cand_src': 'src/semantic/h10_burroughs_promoted.cpp',
        'test_src': 'tools/h18_h10_burroughs_experiment.py',
        'contract_doc': 'docs/agent-work/h18-h10-burroughs-contract.md',
        'cand_doc': 'docs/agent-work/h18-h10-burroughs-candidate.md',
    },
    {
        'id': 'h11-shops',
        'func': '0x0022fc98',
        'name': 'Shop_CheckHasNew',
        'desc': 'Canonical promotion of Shop inventory status query',
        'cand_src': 'src/semantic/h11_shops_promoted.cpp',
        'test_src': 'tools/h18_h11_shops_experiment.py',
        'contract_doc': 'docs/agent-work/h18-h11-shops-contract.md',
        'cand_doc': 'docs/agent-work/h18-h11-shops-candidate.md',
    },
    {
        'id': 'h12-combat',
        'func': '0x00129c58',
        'name': 'Battle_GetUnitSmirkState',
        'desc': 'Canonical promotion of Battle unit smirk status getter',
        'cand_src': 'src/semantic/h12_combat_promoted.cpp',
        'test_src': 'tools/h18_h12_combat_experiment.py',
        'contract_doc': 'docs/agent-work/h18-h12-combat-contract.md',
        'cand_doc': 'docs/agent-work/h18-h12-combat-candidate.md',
    },
    {
        'id': 'h13-exploration',
        'func': '0x0026394c',
        'name': 'PlaceWin_IsActive',
        'desc': 'Canonical promotion of PlaceWin UI timer active state',
        'cand_src': 'src/semantic/h13_exploration_promoted.cpp',
        'test_src': 'tools/h18_h13_exploration_experiment.py',
        'contract_doc': 'docs/agent-work/h18-h13-exploration-contract.md',
        'cand_doc': 'docs/agent-work/h18-h13-exploration-candidate.md',
    },
    {
        'id': 'h14-graphics',
        'func': '0x002c3b88',
        'name': 'AsdGpu_HeapSize',
        'desc': 'Canonical promotion of ASD GPU heap size getter',
        'cand_src': 'src/semantic/h14_graphics_promoted.cpp',
        'test_src': 'tools/h18_h14_graphics_experiment.py',
        'contract_doc': 'docs/agent-work/h18-h14-graphics-contract.md',
        'cand_doc': 'docs/agent-work/h18-h14-graphics-candidate.md',
    },
    {
        'id': 'h15-ui',
        'func': '0x00126084',
        'name': 'UiDialog_GetState',
        'desc': 'Canonical promotion of UI Dialog state getter',
        'cand_src': 'src/semantic/h15_ui_promoted.cpp',
        'test_src': 'tools/h18_h15_ui_experiment.py',
        'contract_doc': 'docs/agent-work/h18-h15-ui-contract.md',
        'cand_doc': 'docs/agent-work/h18-h15-ui-candidate.md',
    },
    {
        'id': 'h16-sound',
        'func': '0x00110c44',
        'name': 'AsdSoundEffect_GetBufferSize',
        'desc': 'Canonical promotion of Sound Effect buffer size calculation',
        'cand_src': 'src/semantic/h16_sound_promoted.cpp',
        'test_src': 'tools/h18_h16_sound_experiment.py',
        'contract_doc': 'docs/agent-work/h18-h16-sound-contract.md',
        'cand_doc': 'docs/agent-work/h18-h16-sound-candidate.md',
    },
    {
        'id': 'h17-cec-aoc',
        'func': '0x002a17c0',
        'name': 'Aoc_ResultIsReady',
        'desc': 'Canonical promotion of AOC result status readiness check',
        'cand_src': 'src/semantic/h17_cec_aoc_promoted.cpp',
        'test_src': 'tools/h18_h17_cec_aoc_experiment.py',
        'contract_doc': 'docs/agent-work/h18-h17-cec-aoc-contract.md',
        'cand_doc': 'docs/agent-work/h18-h17-cec-aoc-candidate.md',
    },
]

tasks = []
all_funcs = [s['func'] for s in subsystems]

# 1. Architecture Recon & Review
tasks.append({
    'id': 'h18-module-promotion-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Map canonical source organization in src/semantic/ and verify candidate promotions across H10-H17.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': ['docs/reconstruction-milestones.md', 'src/semantic/'],
    'write_paths': ['docs/agent-work/h18-module-promotion-recon.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Identify canonical promotion targets from H10 to H17 and define contract interfaces.'],
    'validation_plan': ['python tools/build_h18_all.py']
})

tasks.append({
    'id': 'h18-module-promotion-recon-review',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Review module promotion architecture and source promotion layout in src/semantic/.',
    'depends_on': ['h18-module-promotion-recon'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h18-module-promotion-recon.md'],
    'write_paths': ['docs/agent-work/h18-module-promotion-recon-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Approve module promotion strategy and verify zero header/compilation conflicts.'],
    'validation_plan': ['python tools/build_h18_all.py']
})

# Subsystem tasks (8 tasks per subsystem = 64 tasks)
for s in subsystems:
    sid = s['id']
    fn = s['func']
    name = s['name']
    desc = s['desc']
    cand_src = s['cand_src']
    test_src = s['test_src']
    c_doc = s['contract_doc']
    cand_doc = s['cand_doc']

    t_contract = f'h18-{sid}-contract'
    t_contract_rev = f'h18-{sid}-contract-review'
    t_recon = f'h18-{sid}-recon'
    t_recon_rev = f'h18-{sid}-recon-review'
    t_cand = f'h18-{sid}-candidate'
    t_cand_rev = f'h18-{sid}-candidate-review'
    t_diff = f'h18-{sid}-diff-test'
    t_diff_rev = f'h18-{sid}-diff-test-review'

    tasks.append({
        'id': t_contract,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Define contract specification for {name} ({fn}) in {desc}.',
        'depends_on': ['h18-module-promotion-recon-review'],
        'function_claims': [fn],
        'read_paths': [cand_src],
        'write_paths': [c_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Specify calling convention, register inputs, preconditions, and return contract for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_contract_rev,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Review contract specification for {name} ({fn}).',
        'depends_on': [t_contract],
        'function_claims': [fn],
        'read_paths': [c_doc],
        'write_paths': [f'docs/agent-work/h18-{sid}-contract-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Verify ABI soundness and contract boundaries for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_recon,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Disassemble and recover assembly semantics for {name} ({fn}).',
        'depends_on': [t_contract_rev],
        'function_claims': [fn],
        'read_paths': ['extracted/exefs/code.bin'],
        'write_paths': [f'docs/agent-work/h18-{sid}-recon.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Confirm ARM instructions, immediate offsets, and calling sequences for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_recon_rev,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Review assembly reconnaissance for {name} ({fn}).',
        'depends_on': [t_recon],
        'function_claims': [fn],
        'read_paths': [f'docs/agent-work/h18-{sid}-recon.md'],
        'write_paths': [f'docs/agent-work/h18-{sid}-recon-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Approve disassembly analysis for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_cand,
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement canonical C++ promoted function for {name} ({fn}).',
        'depends_on': [t_recon_rev],
        'function_claims': [fn],
        'read_paths': [cand_src],
        'write_paths': [cand_src, cand_doc],
        'compiler_slots': 1,
        'exclusive_resources': [cand_src],
        'acceptance': [f'Compile {cand_src} cleanly with Clang ARMv6K within original byte window.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_cand_rev,
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent code review of canonical promoted C++ for {name} ({fn}).',
        'depends_on': [t_cand],
        'function_claims': [fn],
        'read_paths': [cand_src, cand_doc],
        'write_paths': [f'docs/agent-work/h18-{sid}-candidate-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Verify that implementation matches contract and has zero UB.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_diff,
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Run offline Unicorn differential test suite for {name} ({fn}).',
        'depends_on': [t_cand_rev],
        'function_claims': [fn],
        'read_paths': [cand_src, test_src],
        'write_paths': [test_src, f'docs/agent-work/h18-{sid}-diff-test.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'100% register/memory parity across input domain and positive mutation sensitivity.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_diff_rev,
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Review differential test results for {name} ({fn}).',
        'depends_on': [t_diff],
        'function_claims': [fn],
        'read_paths': [f'docs/agent-work/h18-{sid}-diff-test.md'],
        'write_paths': [f'docs/agent-work/h18-{sid}-diff-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Confirm differential suite completeness for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

# Final staging and milestone review tasks (2 tasks)
tasks.append({
    'id': 'h18-integrated-staging',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 canonical promoted modules over H17 composite image and generate IPS patch.',
    'depends_on': [f'h18-{s["id"]}-diff-test-review' for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': [s['cand_src'] for s in subsystems] + ['build/agent-work/H17-semantic/h17-integrated-stage/code.h17-final.bin'],
    'write_paths': [
        'build/agent-work/H18-semantic/h18-integrated-stage/code.h18-final.bin',
        'build/agent-work/H18-semantic/h18-integrated-stage/code.h18-final.ips',
        'build/agent-work/H18-semantic/h18-integrated-stage/h18-staged-summary.json',
        'docs/agent-work/h18-integrated-staging.md',
    ],
    'compiler_slots': 1,
    'exclusive_resources': ['code.h18-final.bin'],
    'acceptance': [
        'Generate code.h18-final.bin with all 8 canonical promoted modules cleanly applied within windows.',
        'Produce verified LayeredFS IPS patch code.h18-final.ips passing roundtrip verification.'
    ],
    'validation_plan': ['python tools/h18_staged_image_patch.py']
})

tasks.append({
    'id': 'h18-milestone-closure-review',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review and closure of Milestone H18 (Canonical Module Promotion).',
    'depends_on': ['h18-integrated-staging'],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H18-semantic/h18-integrated-stage/h18-staged-summary.json',
        'docs/agent-work/h18-integrated-staging.md',
    ],
    'write_paths': [
        'docs/agent-work/h18-milestone-closure-review.md',
        'docs/milestones/H18-module-promotion.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify that all 8 subsystems have complete contract, implementation, differential test, and promotion records.',
        'Validate offline differential test suite passes 100% and staging IPS patch roundtrip passes.'
    ],
    'validation_plan': [
        'python tools/agent_workflow.py check',
        'python tools/generate_h18_experiments.py',
        'python tools/h18_staged_image_patch.py'
    ]
})

board = {
    'schema_version': 1,
    'batch': 'batch-h18-001',
    'milestone': 'H18',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Promote and integrate all validated semantic modules into src/semantic/ with offline differential validation, staging, and autonomous verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h18.json',
        'config/reconstruction.json',
        'docs/milestones/H18-module-promotion.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_board = ROOT / 'config/agent-workflows/h18.json'
out_board.parent.mkdir(parents=True, exist_ok=True)
out_board.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Workflow board written to {out_board} with {len(tasks)} tasks.")
