#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h15.json for Milestone H15."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'uitext-setcodefield10',
        'func': '0x0010e570',
        'name': 'UiText_SetCodeField10',
        'desc': 'UI text formatting control field 0x10 configuration',
        'cand_src': 'experiments/semantic_equivalence/h15_uitext_setcodefield10_candidate.cpp',
        'test_src': 'tools/h15_uitext_setcodefield10_experiment.py',
        'contract_doc': 'docs/agent-work/h15-uitext-setcodefield10-contract.md',
        'cand_doc': 'docs/agent-work/h15-uitext-setcodefield10-candidate.md',
    },
    {
        'id': 'uitext-setcodefield28',
        'func': '0x0010e5bc',
        'name': 'UiText_SetCodeField28',
        'desc': 'UI text formatting control field 0x28 configuration',
        'cand_src': 'experiments/semantic_equivalence/h15_uitext_setcodefield28_candidate.cpp',
        'test_src': 'tools/h15_uitext_setcodefield28_experiment.py',
        'contract_doc': 'docs/agent-work/h15-uitext-setcodefield28-contract.md',
        'cand_doc': 'docs/agent-work/h15-uitext-setcodefield28-candidate.md',
    },
    {
        'id': 'uidialog-getstate',
        'func': '0x00126084',
        'name': 'UiDialog_GetState',
        'desc': 'UI dialog active state and result code retrieval',
        'cand_src': 'experiments/semantic_equivalence/h15_uidialog_getstate_candidate.cpp',
        'test_src': 'tools/h15_uidialog_getstate_experiment.py',
        'contract_doc': 'docs/agent-work/h15-uidialog-getstate-contract.md',
        'cand_doc': 'docs/agent-work/h15-uidialog-getstate-candidate.md',
    },
    {
        'id': 'uidialog-getflags',
        'func': '0x001260a8',
        'name': 'UiDialog_GetFlags',
        'desc': 'UI dialog header bitmask flags inspection',
        'cand_src': 'experiments/semantic_equivalence/h15_uidialog_getflags_candidate.cpp',
        'test_src': 'tools/h15_uidialog_getflags_experiment.py',
        'contract_doc': 'docs/agent-work/h15-uidialog-getflags-contract.md',
        'cand_doc': 'docs/agent-work/h15-uidialog-getflags-candidate.md',
    },
    {
        'id': 'uidialog-getcursorindex',
        'func': '0x00126220',
        'name': 'UiDialog_GetCursorIndex',
        'desc': 'UI dialog selection cursor index position query',
        'cand_src': 'experiments/semantic_equivalence/h15_uidialog_getcursorindex_candidate.cpp',
        'test_src': 'tools/h15_uidialog_getcursorindex_experiment.py',
        'contract_doc': 'docs/agent-work/h15-uidialog-getcursorindex-contract.md',
        'cand_doc': 'docs/agent-work/h15-uidialog-getcursorindex-candidate.md',
    },
    {
        'id': 'uitext-getdrawcoordx',
        'func': '0x00126628',
        'name': 'UiText_GetDrawCoordX',
        'desc': 'UI text draw buffer horizontal coordinate retrieval',
        'cand_src': 'experiments/semantic_equivalence/h15_uitext_getdrawcoordx_candidate.cpp',
        'test_src': 'tools/h15_uitext_getdrawcoordx_experiment.py',
        'contract_doc': 'docs/agent-work/h15-uitext-getdrawcoordx-contract.md',
        'cand_doc': 'docs/agent-work/h15-uitext-getdrawcoordx-candidate.md',
    },
    {
        'id': 'uitext-getdrawcoordy',
        'func': '0x00126638',
        'name': 'UiText_GetDrawCoordY',
        'desc': 'UI text draw buffer vertical coordinate retrieval',
        'cand_src': 'experiments/semantic_equivalence/h15_uitext_getdrawcoordy_candidate.cpp',
        'test_src': 'tools/h15_uitext_getdrawcoordy_experiment.py',
        'contract_doc': 'docs/agent-work/h15-uitext-getdrawcoordy-contract.md',
        'cand_doc': 'docs/agent-work/h15-uitext-getdrawcoordy-candidate.md',
    },
    {
        'id': 'uimanager-getcontexthandle',
        'func': '0x0026b844',
        'name': 'UiManager_GetContextHandle',
        'desc': 'UI manager active context instance handle lookup',
        'cand_src': 'experiments/semantic_equivalence/h15_uimanager_getcontexthandle_candidate.cpp',
        'test_src': 'tools/h15_uimanager_getcontexthandle_experiment.py',
        'contract_doc': 'docs/agent-work/h15-uimanager-getcontexthandle-contract.md',
        'cand_doc': 'docs/agent-work/h15-uimanager-getcontexthandle-candidate.md',
    },
]

all_funcs = [s['func'] for s in subsystems]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h15-ui-engine-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H15 UI Engine, Fonts, and 2D Rendering.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/reconstruction-milestones.md',
        'docs/milestones/H14-graphics-engine.md',
    ],
    'write_paths': [
        'docs/agent-work/h15-ui-engine-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H15 UI Engine subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h15-ui-engine-recon-review',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H15 UI Engine architecture reconnaissance.',
    'depends_on': ['h15-ui-engine-recon'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h15-ui-engine-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h15-ui-engine-recon-review.md'
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
        'id': f'h15-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Recover precise calling contract, memory boundaries, and semantics for {sub['name']}.",
        'depends_on': ['h15-ui-engine-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['extracted/exefs/code.bin'],
        'write_paths': [sub['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Recover registers, arguments, preconditions, and return values.'],
        'validation_plan': ['Static disassembly analysis.']
    })

    tasks.append({
        'id': f'h15-{sid}-contract-review',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review contract specification for {sub['name']}.",
        'depends_on': [f'h15-{sid}-contract'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [f'docs/agent-work/h15-{sid}-contract-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve verified contract record.'],
        'validation_plan': ['Compare contract against disassembled original.']
    })

    # 2. Implementation
    tasks.append({
        'id': f'h15-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Implement clean, editable C++ candidate for {sub['name']} within binary window footprint.",
        'depends_on': [f'h15-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [sub['cand_src'], sub['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [sub['cand_src']],
        'acceptance': ['Compile freestanding ARMv6K object within allocated window footprint.'],
        'validation_plan': ['python tools/build_h15_all.py']
    })

    tasks.append({
        'id': f'h15-{sid}-candidate-review',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review C++ candidate implementation for {sub['name']}.",
        'depends_on': [f'h15-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], sub['cand_doc']],
        'write_paths': [f'docs/agent-work/h15-{sid}-candidate-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm semantic clarity, type safety, and zero window overflow.'],
        'validation_plan': ['Inspect C++ code and compilation metrics.']
    })

    # 3. Test Harness
    tasks.append({
        'id': f'h15-{sid}-test',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Create Unicorn offline differential test harness for {sub['name']}.",
        'depends_on': [f'h15-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], sub['contract_doc']],
        'write_paths': [sub['test_src'], f'docs/agent-work/h15-{sid}-test.md'],
        'compiler_slots': 0,
        'exclusive_resources': [sub['test_src']],
        'acceptance': ['Harness simulates original vs candidate with mutation sensitivity.'],
        'validation_plan': [f'python {sub["test_src"]}']
    })

    tasks.append({
        'id': f'h15-{sid}-test-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review differential test harness for {sub['name']}.",
        'depends_on': [f'h15-{sid}-test'],
        'function_claims': fclaim,
        'read_paths': [sub['test_src'], f'docs/agent-work/h15-{sid}-test.md'],
        'write_paths': [f'docs/agent-work/h15-{sid}-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify boundary cases and mutation probe efficacy.'],
        'validation_plan': ['Validate test harness coverage.']
    })

    # 4. Differential Run
    tasks.append({
        'id': f'h15-{sid}-diff',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Execute offline differential validation run for {sub['name']}.",
        'depends_on': [f'h15-{sid}-test-review'],
        'function_claims': fclaim,
        'read_paths': [sub['test_src']],
        'write_paths': [f'docs/agent-work/h15-{sid}-diff.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Achieve 100% parity across registers and memory effects.'],
        'validation_plan': [f'python {sub["test_src"]}']
    })

    tasks.append({
        'id': f'h15-{sid}-diff-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review differential run results for {sub['name']}.",
        'depends_on': [f'h15-{sid}-diff'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h15-{sid}-diff.md'],
        'write_paths': [f'docs/agent-work/h15-{sid}-diff-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm zero divergence and successful mutation failure.'],
        'validation_plan': ['Inspect differential log.']
    })

    # 5. Integration
    tasks.append({
        'id': f'h15-{sid}-integration',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Integrate candidate {sub['name']} into staging binary image with relocations resolved.",
        'depends_on': [f'h15-{sid}-diff-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src']],
        'write_paths': [f'docs/agent-work/h15-{sid}-integration.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Resolved relocations and patched into code image.'],
        'validation_plan': ['python tools/h15_staged_image_patch.py']
    })

    tasks.append({
        'id': f'h15-{sid}-integration-review',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review subsystem staging integration for {sub['name']}.",
        'depends_on': [f'h15-{sid}-integration'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h15-{sid}-integration.md'],
        'write_paths': [f'docs/agent-work/h15-{sid}-integration-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve staged integration record.'],
        'validation_plan': ['Verify staging summary and binary offsets.']
    })

# Batch integration tasks
tasks.append({
    'id': 'h15-batch-integration',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 H15 subsystems into cumulative staged image code.h15-final.bin and emit LayeredFS IPS mod.',
    'depends_on': [f'h15-{s["id"]}-integration-review' for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H14-semantic/h14-integrated-stage/code.h14-final.bin',
        'tools/h15_staged_image_patch.py'
    ],
    'write_paths': [
        'build/agent-work/H15-semantic/h15-integrated-stage/code.h15-final.bin',
        'build/agent-work/H15-semantic/h15-integrated-stage/code.h15-final.ips',
        'build/agent-work/H15-semantic/h15-integrated-stage/h15_staging_summary.json',
        'docs/agent-work/h15-batch-integration.md'
    ],
    'compiler_slots': 1,
    'exclusive_resources': [],
    'acceptance': [
        'Generate code.h15-final.bin with all H15 patches applied.',
        'Emit LayeredFS IPS mod with roundtrip verification.'
    ],
    'validation_plan': [
        'python tools/h15_staged_image_patch.py'
    ]
})

tasks.append({
    'id': 'h15-batch-integration-review',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Review cumulative batch integration for Milestone H15.',
    'depends_on': ['h15-batch-integration'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h15-batch-integration.md',
        'build/agent-work/H15-semantic/h15-integrated-stage/h15_staging_summary.json'
    ],
    'write_paths': [
        'docs/agent-work/h15-batch-integration-review.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Validate SHA256 hashes and IPS roundtrip verification.'
    ],
    'validation_plan': [
        'Inspect staging summary and verify SHA256 integrity.'
    ]
})

tasks.append({
    'id': 'h15-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Milestone H15 closure, documentation finalization, and transition to Milestone H16.',
    'depends_on': ['h15-batch-integration-review'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h15-batch-integration-review.md',
        'build/agent-work/H15-semantic/h15-integrated-stage/h15_staging_summary.json',
    ],
    'write_paths': [
        'docs/milestones/H15-ui-engine.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md',
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Milestone documentation complete with candidate metrics, validation proof, and status ledger updates.'
    ],
    'validation_plan': [
        'python tools/agent_workflow.py check'
    ]
})

board = {
    'schema_version': 1,
    'batch': 'batch-h15-001',
    'milestone': 'H15',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H15 (UI Engine, Fonts, and 2D Rendering), covering text formatting code setup (UiText_SetCodeField10, UiText_SetCodeField28), dialog state/flag/cursor extraction (UiDialog_GetState, UiDialog_GetFlags, UiDialog_GetCursorIndex), text draw buffer coordinate retrieval (UiText_GetDrawCoordX, UiText_GetDrawCoordY), and UI context manager handle lookup (UiManager_GetContextHandle) with offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h15.json',
        'config/reconstruction.json',
        'docs/milestones/H15-ui-engine.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

board_path = ROOT / 'config/agent-workflows/h15.json'
board_path.parent.mkdir(parents=True, exist_ok=True)
board_path.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Board config/agent-workflows/h15.json generated with {len(tasks)} tasks.")
