#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h13.json for Milestone H13."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'placewin-setvisible',
        'func': '0x002638fc',
        'name': 'PlaceWin_SetVisible',
        'desc': 'Place window banner visibility state update',
        'cand_src': 'experiments/semantic_equivalence/h13_placewin_setvisible_candidate.cpp',
        'test_src': 'tools/h13_placewin_setvisible_experiment.py',
        'contract_doc': 'docs/agent-work/h13-placewin-setvisible-contract.md',
        'cand_doc': 'docs/agent-work/h13-placewin-setvisible-candidate.md',
    },
    {
        'id': 'placewin-dismiss',
        'func': '0x002638dc',
        'name': 'PlaceWin_Dismiss',
        'desc': 'Place window banner dismissal and state transition to inactive',
        'cand_src': 'experiments/semantic_equivalence/h13_placewin_dismiss_candidate.cpp',
        'test_src': 'tools/h13_placewin_dismiss_experiment.py',
        'contract_doc': 'docs/agent-work/h13-placewin-dismiss-contract.md',
        'cand_doc': 'docs/agent-work/h13-placewin-dismiss-candidate.md',
    },
    {
        'id': 'placewin-isactive',
        'func': '0x0026394c',
        'name': 'PlaceWin_IsActive',
        'desc': 'Place window banner timer duration and activity state evaluation',
        'cand_src': 'experiments/semantic_equivalence/h13_placewin_isactive_candidate.cpp',
        'test_src': 'tools/h13_placewin_isactive_experiment.py',
        'contract_doc': 'docs/agent-work/h13-placewin-isactive-contract.md',
        'cand_doc': 'docs/agent-work/h13-placewin-isactive-candidate.md',
    },
    {
        'id': 'mapfield-clearactiveflag',
        'func': '0x00208a70',
        'name': 'MapField_ClearActiveFlag',
        'desc': 'Exploration field active flag clearing and reset',
        'cand_src': 'experiments/semantic_equivalence/h13_mapfield_clearactiveflag_candidate.cpp',
        'test_src': 'tools/h13_mapfield_clearactiveflag_experiment.py',
        'contract_doc': 'docs/agent-work/h13-mapfield-clearactiveflag-contract.md',
        'cand_doc': 'docs/agent-work/h13-mapfield-clearactiveflag-candidate.md',
    },
    {
        'id': 'mapnavi-settargetcoords',
        'func': '0x001d2e24',
        'name': 'MapNavi_SetTargetCoords',
        'desc': 'Minimap navigation marker target coordinates configuration and activation',
        'cand_src': 'experiments/semantic_equivalence/h13_mapnavi_settargetcoords_candidate.cpp',
        'test_src': 'tools/h13_mapnavi_settargetcoords_experiment.py',
        'contract_doc': 'docs/agent-work/h13-mapnavi-settargetcoords-contract.md',
        'cand_doc': 'docs/agent-work/h13-mapnavi-settargetcoords-candidate.md',
    },
    {
        'id': 'mapnavi-reset',
        'func': '0x001d2e0c',
        'name': 'MapNavi_Reset',
        'desc': 'Minimap navigation system state reset and runtime buffer synchronization',
        'cand_src': 'experiments/semantic_equivalence/h13_mapnavi_reset_candidate.cpp',
        'test_src': 'tools/h13_mapnavi_reset_experiment.py',
        'contract_doc': 'docs/agent-work/h13-mapnavi-reset-contract.md',
        'cand_doc': 'docs/agent-work/h13-mapnavi-reset-candidate.md',
    },
    {
        'id': 'mapepl-calcscale',
        'func': '0x00193b28',
        'name': 'MapEpl_CalcScale',
        'desc': 'Map particle effect scaling calculation based on viewport distance and level parameters',
        'cand_src': 'experiments/semantic_equivalence/h13_mapepl_calcscale_candidate.cpp',
        'test_src': 'tools/h13_mapepl_calcscale_experiment.py',
        'contract_doc': 'docs/agent-work/h13-mapepl-calcscale-contract.md',
        'cand_doc': 'docs/agent-work/h13-mapepl-calcscale-candidate.md',
    },
    {
        'id': 'mapcalc-distancetoentity',
        'func': '0x001d3a9c',
        'name': 'MapCalc_DistanceToEntity',
        'desc': 'Overworld entity Euclidean distance computation using hardware VFP square root',
        'cand_src': 'experiments/semantic_equivalence/h13_mapcalc_distancetoentity_candidate.cpp',
        'test_src': 'tools/h13_mapcalc_distancetoentity_experiment.py',
        'contract_doc': 'docs/agent-work/h13-mapcalc-distancetoentity-contract.md',
        'cand_doc': 'docs/agent-work/h13-mapcalc-distancetoentity-candidate.md',
    },
]

all_funcs = [s['func'] for s in subsystems]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h13-advanced-exploration-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H13 Advanced Exploration, Minimap, and Overworld.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/reconstruction-milestones.md',
        'docs/milestones/H12-advanced-combat.md',
    ],
    'write_paths': [
        'docs/agent-work/h13-advanced-exploration-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H13 Advanced Exploration subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h13-advanced-exploration-recon-review',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H13 Advanced Exploration architecture reconnaissance.',
    'depends_on': ['h13-advanced-exploration-recon'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h13-advanced-exploration-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h13-advanced-exploration-recon-review.md'
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
        'id': f'h13-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Recover precise calling contract, memory boundaries, and semantics for {sub['name']}.",
        'depends_on': ['h13-advanced-exploration-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['extracted/exefs/code.bin'],
        'write_paths': [sub['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Recover registers, arguments, preconditions, and return values.'],
        'validation_plan': ['Static disassembly analysis.']
    })

    tasks.append({
        'id': f'h13-{sid}-contract-review',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review contract specification for {sub['name']}.",
        'depends_on': [f'h13-{sid}-contract'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [f'docs/agent-work/h13-{sid}-contract-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve verified contract record.'],
        'validation_plan': ['Compare contract against disassembled original.']
    })

    # 2. Implementation
    tasks.append({
        'id': f'h13-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Implement clean, editable C++ candidate for {sub['name']} within binary window footprint.",
        'depends_on': [f'h13-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [sub['cand_src'], sub['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [sub['cand_src']],
        'acceptance': ['Compile freestanding ARMv6K object within allocated window footprint.'],
        'validation_plan': ['python tools/build_h13_all.py']
    })

    tasks.append({
        'id': f'h13-{sid}-candidate-review',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review C++ candidate implementation for {sub['name']}.",
        'depends_on': [f'h13-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], sub['cand_doc']],
        'write_paths': [f'docs/agent-work/h13-{sid}-candidate-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm semantic clarity, type safety, and zero window overflow.'],
        'validation_plan': ['Inspect C++ code and compilation metrics.']
    })

    # 3. Test Harness
    tasks.append({
        'id': f'h13-{sid}-test',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Create Unicorn offline differential test harness for {sub['name']}.",
        'depends_on': [f'h13-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], sub['contract_doc']],
        'write_paths': [sub['test_src'], f'docs/agent-work/h13-{sid}-test.md'],
        'compiler_slots': 0,
        'exclusive_resources': [sub['test_src']],
        'acceptance': ['Harness simulates original vs candidate with mutation sensitivity.'],
        'validation_plan': [f'python {sub["test_src"]}']
    })

    tasks.append({
        'id': f'h13-{sid}-test-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review differential test harness for {sub['name']}.",
        'depends_on': [f'h13-{sid}-test'],
        'function_claims': fclaim,
        'read_paths': [sub['test_src'], f'docs/agent-work/h13-{sid}-test.md'],
        'write_paths': [f'docs/agent-work/h13-{sid}-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify boundary cases and mutation probe efficacy.'],
        'validation_plan': ['Validate test harness coverage.']
    })

    # 4. Differential Run
    tasks.append({
        'id': f'h13-{sid}-diff',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Execute offline differential validation run for {sub['name']}.",
        'depends_on': [f'h13-{sid}-test-review'],
        'function_claims': fclaim,
        'read_paths': [sub['test_src']],
        'write_paths': [f'docs/agent-work/h13-{sid}-diff.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Achieve 100% parity across registers and memory effects.'],
        'validation_plan': [f'python {sub["test_src"]}']
    })

    tasks.append({
        'id': f'h13-{sid}-diff-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review differential run results for {sub['name']}.",
        'depends_on': [f'h13-{sid}-diff'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h13-{sid}-diff.md'],
        'write_paths': [f'docs/agent-work/h13-{sid}-diff-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm zero divergence and successful mutation failure.'],
        'validation_plan': ['Inspect differential log.']
    })

    # 5. Integration
    tasks.append({
        'id': f'h13-{sid}-integration',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Integrate candidate {sub['name']} into staging binary image with relocations resolved.",
        'depends_on': [f'h13-{sid}-diff-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src']],
        'write_paths': [f'docs/agent-work/h13-{sid}-integration.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Resolved relocations and patched into code image.'],
        'validation_plan': ['python tools/h13_staged_image_patch.py']
    })

    tasks.append({
        'id': f'h13-{sid}-integration-review',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review subsystem staging integration for {sub['name']}.",
        'depends_on': [f'h13-{sid}-integration'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h13-{sid}-integration.md'],
        'write_paths': [f'docs/agent-work/h13-{sid}-integration-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve staged integration record.'],
        'validation_plan': ['Verify staging summary and binary offsets.']
    })

# Batch integration tasks
tasks.append({
    'id': 'h13-batch-integration',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 H13 subsystems into cumulative staged image code.h13-final.bin and emit LayeredFS IPS mod.',
    'depends_on': [f'h13-{s["id"]}-integration-review' for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H12-semantic/h12-integrated-stage/code.h12-final.bin',
        'tools/h13_staged_image_patch.py'
    ],
    'write_paths': [
        'build/agent-work/H13-semantic/h13-integrated-stage/code.h13-final.bin',
        'build/agent-work/H13-semantic/h13-integrated-stage/code.h13-final.ips',
        'build/agent-work/H13-semantic/h13-integrated-stage/h13_staging_summary.json',
        'docs/agent-work/h13-batch-integration.md'
    ],
    'compiler_slots': 1,
    'exclusive_resources': [],
    'acceptance': [
        'Generate code.h13-final.bin with all H13 patches applied.',
        'Emit LayeredFS IPS mod with roundtrip verification.'
    ],
    'validation_plan': [
        'python tools/h13_staged_image_patch.py'
    ]
})

tasks.append({
    'id': 'h13-batch-integration-review',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Review cumulative batch integration for Milestone H13.',
    'depends_on': ['h13-batch-integration'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h13-batch-integration.md',
        'build/agent-work/H13-semantic/h13-integrated-stage/h13_staging_summary.json'
    ],
    'write_paths': [
        'docs/agent-work/h13-batch-integration-review.md'
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
    'id': 'h13-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Milestone H13 closure, documentation finalization, and transition to Milestone H14.',
    'depends_on': ['h13-batch-integration-review'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h13-batch-integration-review.md',
        'build/agent-work/H13-semantic/h13-integrated-stage/h13_staging_summary.json',
    ],
    'write_paths': [
        'docs/milestones/H13-advanced-exploration.md',
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
    'batch': 'batch-h13-001',
    'milestone': 'H13',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H13 (Advanced Exploration, Minimap, and Overworld), covering place window banner visibility update (PlaceWin_SetVisible), place window banner dismissal (PlaceWin_Dismiss), place window activity state evaluation (PlaceWin_IsActive), exploration field active flag clearing (MapField_ClearActiveFlag), minimap navigation target coordinates configuration (MapNavi_SetTargetCoords), minimap navigation runtime reset (MapNavi_Reset), map particle effect scaling calculation (MapEpl_CalcScale), and overworld entity Euclidean distance computation (MapCalc_DistanceToEntity) with offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h13.json',
        'config/reconstruction.json',
        'docs/milestones/H13-advanced-exploration.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

board_path = ROOT / 'config/agent-workflows/h13.json'
board_path.parent.mkdir(parents=True, exist_ok=True)
board_path.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Board config/agent-workflows/h13.json generated with {len(tasks)} tasks.")
