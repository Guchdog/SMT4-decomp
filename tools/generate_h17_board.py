#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h17.json for Milestone H17."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'campcec-haseditwork',
        'func': '0x001ffadc',
        'name': 'CampCec_HasEditWork',
        'desc': 'Camp CEC edit work pointer validation',
        'cand_src': 'experiments/semantic_equivalence/h17_campcec_haseditwork_candidate.cpp',
        'test_src': 'tools/h17_campcec_haseditwork_experiment.py',
        'contract_doc': 'docs/agent-work/h17-campcec-haseditwork-contract.md',
        'cand_doc': 'docs/agent-work/h17-campcec-haseditwork-candidate.md',
    },
    {
        'id': 'campcec-copycarddata',
        'func': '0x001ff814',
        'name': 'CampCec_CopyCardData',
        'desc': 'Camp CEC DDS profile card header copy',
        'cand_src': 'experiments/semantic_equivalence/h17_campcec_copycarddata_candidate.cpp',
        'test_src': 'tools/h17_campcec_copycarddata_experiment.py',
        'contract_doc': 'docs/agent-work/h17-campcec-copycarddata-contract.md',
        'cand_doc': 'docs/agent-work/h17-campcec-copycarddata-candidate.md',
    },
    {
        'id': 'aoc-resultisready',
        'func': '0x002a17c0',
        'name': 'Aoc_ResultIsReady',
        'desc': 'AOC result status readiness check (>= 0x64)',
        'cand_src': 'experiments/semantic_equivalence/h17_aoc_resultisready_candidate.cpp',
        'test_src': 'tools/h17_aoc_resultisready_experiment.py',
        'contract_doc': 'docs/agent-work/h17-aoc-resultisready-contract.md',
        'cand_doc': 'docs/agent-work/h17-aoc-resultisready-candidate.md',
    },
    {
        'id': 'aocapplet-isflag10000',
        'func': '0x002a17d4',
        'name': 'AocApplet_IsFlag10000',
        'desc': 'AOC applet state flag 0x10000 test',
        'cand_src': 'experiments/semantic_equivalence/h17_aocapplet_isflag10000_candidate.cpp',
        'test_src': 'tools/h17_aocapplet_isflag10000_experiment.py',
        'contract_doc': 'docs/agent-work/h17-aocapplet-isflag10000-contract.md',
        'cand_doc': 'docs/agent-work/h17-aocapplet-isflag10000-candidate.md',
    },
    {
        'id': 'aoc-resultcopyvalue',
        'func': '0x002a17e4',
        'name': 'Aoc_ResultCopyValue',
        'desc': 'AOC result object pointer value dereference and copy',
        'cand_src': 'experiments/semantic_equivalence/h17_aoc_resultcopyvalue_candidate.cpp',
        'test_src': 'tools/h17_aoc_resultcopyvalue_experiment.py',
        'contract_doc': 'docs/agent-work/h17-aoc-resultcopyvalue-contract.md',
        'cand_doc': 'docs/agent-work/h17-aoc-resultcopyvalue-candidate.md',
    },
    {
        'id': 'aoc-releaseglobal',
        'func': '0x002b2520',
        'name': 'Aoc_ReleaseGlobal',
        'desc': 'AOC global buffer memory release guard',
        'cand_src': 'experiments/semantic_equivalence/h17_aoc_releaseglobal_candidate.cpp',
        'test_src': 'tools/h17_aoc_releaseglobal_experiment.py',
        'contract_doc': 'docs/agent-work/h17-aoc-releaseglobal-contract.md',
        'cand_doc': 'docs/agent-work/h17-aoc-releaseglobal-candidate.md',
    },
    {
        'id': 'campcec-getworkhandle',
        'func': '0x002d73f4',
        'name': 'CampCec_GetWorkHandle',
        'desc': 'Camp CEC setting active flag query',
        'cand_src': 'experiments/semantic_equivalence/h17_campcec_getworkhandle_candidate.cpp',
        'test_src': 'tools/h17_campcec_getworkhandle_experiment.py',
        'contract_doc': 'docs/agent-work/h17-campcec-getworkhandle-contract.md',
        'cand_doc': 'docs/agent-work/h17-campcec-getworkhandle-candidate.md',
    },
    {
        'id': 'aocicon-init',
        'func': '0x0038c248',
        'name': 'AocIcon_Init',
        'desc': 'AOC icon control object vtable and field initialization',
        'cand_src': 'experiments/semantic_equivalence/h17_aocicon_init_candidate.cpp',
        'test_src': 'tools/h17_aocicon_init_experiment.py',
        'contract_doc': 'docs/agent-work/h17-aocicon-init-contract.md',
        'cand_doc': 'docs/agent-work/h17-aocicon-init-candidate.md',
    },
]

all_funcs = [s['func'] for s in subsystems]

tasks = []

# Global Recon & Review
tasks.append({
    'id': 'h17-cec-aoc-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H17 StreetPass (DDS / CEC) and DLC (AOC) Subsystems.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/reconstruction-milestones.md',
        'docs/milestones/H16-audio-engine.md',
    ],
    'write_paths': [
        'docs/agent-work/h17-cec-aoc-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H17 CEC/AOC subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h17-cec-aoc-recon-review',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H17 CEC/AOC architecture reconnaissance.',
    'depends_on': ['h17-cec-aoc-recon'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h17-cec-aoc-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h17-cec-aoc-recon-review.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Confirm scope boundaries, calling conventions, and offline differential test plans.'
    ],
    'validation_plan': [
        'Verify against function signatures and registers.'
    ]
})

# Subsystem tasks
for sub in subsystems:
    sid = sub['id']
    fclaim = [sub['func']]

    # 1. Contract
    tasks.append({
        'id': f'h17-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Recover precise calling contract, memory boundaries, and semantics for {sub['name']}.",
        'depends_on': ['h17-cec-aoc-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['extracted/exefs/code.bin'],
        'write_paths': [sub['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Recover registers, arguments, preconditions, and return values.'],
        'validation_plan': ['Static disassembly analysis.']
    })

    tasks.append({
        'id': f'h17-{sid}-contract-review',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review contract specification for {sub['name']}.",
        'depends_on': [f'h17-{sid}-contract'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [f'docs/agent-work/h17-{sid}-contract-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve verified contract record.'],
        'validation_plan': ['Compare contract against disassembled original.']
    })

    # 2. Implementation
    tasks.append({
        'id': f'h17-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Implement clean, editable C++ candidate for {sub['name']} within binary window footprint.",
        'depends_on': [f'h17-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [sub['cand_src'], sub['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [sub['cand_src']],
        'acceptance': ['Compile freestanding ARMv6K object within allocated window footprint.'],
        'validation_plan': ['python tools/build_h17_all.py']
    })

    tasks.append({
        'id': f'h17-{sid}-cand-review',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Independent review of candidate implementation for {sub['name']}.",
        'depends_on': [f'h17-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], sub['cand_doc']],
        'write_paths': [f'docs/agent-work/h17-{sid}-cand-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify absence of undefined behavior and correct ABI compliance.'],
        'validation_plan': ['Source inspection.']
    })

    # 3. Differential Test
    tasks.append({
        'id': f'h17-{sid}-diff-test',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Execute offline Unicorn differential test suite for {sub['name']} comparing against pinned binary.",
        'depends_on': [f'h17-{sid}-cand-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], 'extracted/exefs/code.bin'],
        'write_paths': [sub['test_src'], f'docs/agent-work/h17-{sid}-diff-test.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Pass all test vectors with 100% register and memory parity and verify mutation detection.'],
        'validation_plan': [f'python {sub["test_src"]}']
    })

    tasks.append({
        'id': f'h17-{sid}-diff-test-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review differential validation results for {sub['name']}.",
        'depends_on': [f'h17-{sid}-diff-test'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h17-{sid}-diff-test.md'],
        'write_paths': [f'docs/agent-work/h17-{sid}-diff-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve differential validation record.'],
        'validation_plan': ['Audit differential run log.']
    })

    # 4. Promotion
    tasks.append({
        'id': f'h17-{sid}-promotion',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Promote validated C++ candidate for {sub['name']} into milestone staging pipeline.",
        'depends_on': [f'h17-{sid}-diff-test-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src']],
        'write_paths': [f'docs/agent-work/h17-{sid}-promotion.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Record candidate readiness for binary staging composition.'],
        'validation_plan': ['Verify staging eligibility.']
    })

    tasks.append({
        'id': f'h17-{sid}-promotion-review',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review candidate promotion for {sub['name']}.",
        'depends_on': [f'h17-{sid}-promotion'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h17-{sid}-promotion.md'],
        'write_paths': [f'docs/agent-work/h17-{sid}-promotion-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm promotion into milestone integrated stage.'],
        'validation_plan': ['Audit promotion record.']
    })

# Global Milestone Integration & Closure Tasks
tasks.append({
    'id': 'h17-integrated-staging',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 validated H17 candidates over code.h16-final.bin to generate code.h17-final.bin and IPS patch.',
    'depends_on': [f"h17-{s['id']}-promotion-review" for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': [s['cand_src'] for s in subsystems] + ['build/agent-work/H16-semantic/h16-integrated-stage/code.h16-final.bin'],
    'write_paths': [
        'tools/h17_staged_image_patch.py',
        'build/agent-work/H17-semantic/h17-integrated-stage/code.h17-final.bin',
        'build/agent-work/H17-semantic/h17-integrated-stage/code.h17-final.ips',
        'build/agent-work/H17-semantic/h17-integrated-stage/h17_staging_summary.json',
        'docs/agent-work/h17-integrated-staging.md',
    ],
    'compiler_slots': 1,
    'exclusive_resources': ['code.h17-final.bin'],
    'acceptance': [
        'Generate code.h17-final.bin with all 8 candidates cleanly applied within windows.',
        'Produce verified LayeredFS IPS patch code.h17-final.ips passing roundtrip verification.'
    ],
    'validation_plan': ['python tools/h17_staged_image_patch.py']
})

tasks.append({
    'id': 'h17-milestone-closure-review',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review and closure of Milestone H17 (StreetPass / CEC and DLC / AOC).',
    'depends_on': ['h17-integrated-staging'],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H17-semantic/h17-integrated-stage/h17_staging_summary.json',
        'docs/agent-work/h17-integrated-staging.md',
    ],
    'write_paths': [
        'docs/agent-work/h17-milestone-closure-review.md',
        'docs/milestones/H17-cec-aoc.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify that all 8 subsystems have complete contract, implementation, differential test, and promotion records.',
        'Validate offline differential test suite passes 100% and staging IPS patch roundtrip passes.'
    ],
    'validation_plan': [
        'python tools/agent_workflow.py check',
        'python tools/generate_h17_experiments.py',
        'python tools/h17_staged_image_patch.py'
    ]
})

board = {
    'schema_version': 1,
    'batch': 'batch-h17-001',
    'milestone': 'H17',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H17 (StreetPass / CEC and DLC / AOC), covering Camp CEC edit work validation, card data copy, setting flag query, AOC result readiness, applet state flags, result copy value, global buffer release, and icon structure initialization with offline differential validation, staging, and autonomous verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h17.json',
        'config/reconstruction.json',
        'docs/milestones/H17-cec-aoc.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_board = ROOT / 'config/agent-workflows/h17.json'
out_board.parent.mkdir(parents=True, exist_ok=True)
out_board.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Workflow board written to {out_board} with {len(tasks)} tasks.")
