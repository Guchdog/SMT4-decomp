#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h14.json for Milestone H14."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'asdeffect-lockenter',
        'func': '0x00152d7c',
        'name': 'AsdEffect_LockEnter',
        'desc': 'ASD particle effect lock entrance and state preservation',
        'cand_src': 'experiments/semantic_equivalence/h14_asdeffect_lockenter_candidate.cpp',
        'test_src': 'tools/h14_asdeffect_lockenter_experiment.py',
        'contract_doc': 'docs/agent-work/h14-asdeffect-lockenter-contract.md',
        'cand_doc': 'docs/agent-work/h14-asdeffect-lockenter-candidate.md',
    },
    {
        'id': 'asdeffect-lockleave',
        'func': '0x00152dac',
        'name': 'AsdEffect_LockLeave',
        'desc': 'ASD particle effect lock departure and state restoration',
        'cand_src': 'experiments/semantic_equivalence/h14_asdeffect_lockleave_candidate.cpp',
        'test_src': 'tools/h14_asdeffect_lockleave_experiment.py',
        'contract_doc': 'docs/agent-work/h14-asdeffect-lockleave-contract.md',
        'cand_doc': 'docs/agent-work/h14-asdeffect-lockleave-candidate.md',
    },
    {
        'id': 'asdres-getcontext',
        'func': '0x002c31bc',
        'name': 'AsdRes_GetContext',
        'desc': 'ASD resource manager active versus default context resolution',
        'cand_src': 'experiments/semantic_equivalence/h14_asdres_getcontext_candidate.cpp',
        'test_src': 'tools/h14_asdres_getcontext_experiment.py',
        'contract_doc': 'docs/agent-work/h14-asdres-getcontext-contract.md',
        'cand_doc': 'docs/agent-work/h14-asdres-getcontext-candidate.md',
    },
    {
        'id': 'asdgpu-heapsize',
        'func': '0x002c3b88',
        'name': 'AsdGpu_HeapSize',
        'desc': 'ASD GPU heap size parameter query',
        'cand_src': 'experiments/semantic_equivalence/h14_asdgpu_heapsize_candidate.cpp',
        'test_src': 'tools/h14_asdgpu_heapsize_experiment.py',
        'contract_doc': 'docs/agent-work/h14-asdgpu-heapsize-contract.md',
        'cand_doc': 'docs/agent-work/h14-asdgpu-heapsize-candidate.md',
    },
    {
        'id': 'asdtext-setcodefield1c',
        'func': '0x0010a6fc',
        'name': 'AsdText_SetCodeField1C',
        'desc': 'ASD text engine shader code field 0x1C configuration',
        'cand_src': 'experiments/semantic_equivalence/h14_asdtext_setcodefield1c_candidate.cpp',
        'test_src': 'tools/h14_asdtext_setcodefield1c_experiment.py',
        'contract_doc': 'docs/agent-work/h14-asdtext-setcodefield1c-contract.md',
        'cand_doc': 'docs/agent-work/h14-asdtext-setcodefield1c-candidate.md',
    },
    {
        'id': 'asdtext-setcodefield14',
        'func': '0x0010af38',
        'name': 'AsdText_SetCodeField14',
        'desc': 'ASD text engine shader code field 0x14 configuration',
        'cand_src': 'experiments/semantic_equivalence/h14_asdtext_setcodefield14_candidate.cpp',
        'test_src': 'tools/h14_asdtext_setcodefield14_experiment.py',
        'contract_doc': 'docs/agent-work/h14-asdtext-setcodefield14-contract.md',
        'cand_doc': 'docs/agent-work/h14-asdtext-setcodefield14-candidate.md',
    },
    {
        'id': 'asdtext-setcodefield30',
        'func': '0x0010b340',
        'name': 'AsdText_SetCodeField30',
        'desc': 'ASD text engine shader code field 0x30 configuration',
        'cand_src': 'experiments/semantic_equivalence/h14_asdtext_setcodefield30_candidate.cpp',
        'test_src': 'tools/h14_asdtext_setcodefield30_experiment.py',
        'contract_doc': 'docs/agent-work/h14-asdtext-setcodefield30-contract.md',
        'cand_doc': 'docs/agent-work/h14-asdtext-setcodefield30-candidate.md',
    },
    {
        'id': 'texturestreamer-compare',
        'func': '0x003878c0',
        'name': 'TextureStreamer_Compare',
        'desc': 'Texture streaming queue priority halfword key comparison',
        'cand_src': 'experiments/semantic_equivalence/h14_texturestreamer_compare_candidate.cpp',
        'test_src': 'tools/h14_texturestreamer_compare_experiment.py',
        'contract_doc': 'docs/agent-work/h14-texturestreamer-compare-contract.md',
        'cand_doc': 'docs/agent-work/h14-texturestreamer-compare-candidate.md',
    },
]

all_funcs = [s['func'] for s in subsystems]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h14-graphics-engine-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H14 ASD Graphics Engine: Scene, 3D Models, Textures, and Effects.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/reconstruction-milestones.md',
        'docs/milestones/H13-advanced-exploration.md',
    ],
    'write_paths': [
        'docs/agent-work/h14-graphics-engine-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H14 ASD Graphics Engine subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h14-graphics-engine-recon-review',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H14 ASD Graphics Engine architecture reconnaissance.',
    'depends_on': ['h14-graphics-engine-recon'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h14-graphics-engine-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h14-graphics-engine-recon-review.md'
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
        'id': f'h14-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Recover precise calling contract, memory boundaries, and semantics for {sub['name']}.",
        'depends_on': ['h14-graphics-engine-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['extracted/exefs/code.bin'],
        'write_paths': [sub['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Recover registers, arguments, preconditions, and return values.'],
        'validation_plan': ['Static disassembly analysis.']
    })

    tasks.append({
        'id': f'h14-{sid}-contract-review',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review contract specification for {sub['name']}.",
        'depends_on': [f'h14-{sid}-contract'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [f'docs/agent-work/h14-{sid}-contract-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve verified contract record.'],
        'validation_plan': ['Compare contract against disassembled original.']
    })

    # 2. Implementation
    tasks.append({
        'id': f'h14-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Implement clean, editable C++ candidate for {sub['name']} within binary window footprint.",
        'depends_on': [f'h14-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [sub['cand_src'], sub['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [sub['cand_src']],
        'acceptance': ['Compile freestanding ARMv6K object within allocated window footprint.'],
        'validation_plan': ['python tools/build_h14_all.py']
    })

    tasks.append({
        'id': f'h14-{sid}-candidate-review',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review C++ candidate implementation for {sub['name']}.",
        'depends_on': [f'h14-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], sub['cand_doc']],
        'write_paths': [f'docs/agent-work/h14-{sid}-candidate-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm semantic clarity, type safety, and zero window overflow.'],
        'validation_plan': ['Inspect C++ code and compilation metrics.']
    })

    # 3. Test Harness
    tasks.append({
        'id': f'h14-{sid}-test',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Create Unicorn offline differential test harness for {sub['name']}.",
        'depends_on': [f'h14-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], sub['contract_doc']],
        'write_paths': [sub['test_src'], f'docs/agent-work/h14-{sid}-test.md'],
        'compiler_slots': 0,
        'exclusive_resources': [sub['test_src']],
        'acceptance': ['Harness simulates original vs candidate with mutation sensitivity.'],
        'validation_plan': [f'python {sub["test_src"]}']
    })

    tasks.append({
        'id': f'h14-{sid}-test-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review differential test harness for {sub['name']}.",
        'depends_on': [f'h14-{sid}-test'],
        'function_claims': fclaim,
        'read_paths': [sub['test_src'], f'docs/agent-work/h14-{sid}-test.md'],
        'write_paths': [f'docs/agent-work/h14-{sid}-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify boundary cases and mutation probe efficacy.'],
        'validation_plan': ['Validate test harness coverage.']
    })

    # 4. Differential Run
    tasks.append({
        'id': f'h14-{sid}-diff',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Execute offline differential validation run for {sub['name']}.",
        'depends_on': [f'h14-{sid}-test-review'],
        'function_claims': fclaim,
        'read_paths': [sub['test_src']],
        'write_paths': [f'docs/agent-work/h14-{sid}-diff.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Achieve 100% parity across registers and memory effects.'],
        'validation_plan': [f'python {sub["test_src"]}']
    })

    tasks.append({
        'id': f'h14-{sid}-diff-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review differential run results for {sub['name']}.",
        'depends_on': [f'h14-{sid}-diff'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h14-{sid}-diff.md'],
        'write_paths': [f'docs/agent-work/h14-{sid}-diff-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm zero divergence and successful mutation failure.'],
        'validation_plan': ['Inspect differential log.']
    })

    # 5. Integration
    tasks.append({
        'id': f'h14-{sid}-integration',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Integrate candidate {sub['name']} into staging binary image with relocations resolved.",
        'depends_on': [f'h14-{sid}-diff-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src']],
        'write_paths': [f'docs/agent-work/h14-{sid}-integration.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Resolved relocations and patched into code image.'],
        'validation_plan': ['python tools/h14_staged_image_patch.py']
    })

    tasks.append({
        'id': f'h14-{sid}-integration-review',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review subsystem staging integration for {sub['name']}.",
        'depends_on': [f'h14-{sid}-integration'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h14-{sid}-integration.md'],
        'write_paths': [f'docs/agent-work/h14-{sid}-integration-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve staged integration record.'],
        'validation_plan': ['Verify staging summary and binary offsets.']
    })

# Batch integration tasks
tasks.append({
    'id': 'h14-batch-integration',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 H14 subsystems into cumulative staged image code.h14-final.bin and emit LayeredFS IPS mod.',
    'depends_on': [f'h14-{s["id"]}-integration-review' for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H13-semantic/h13-integrated-stage/code.h13-final.bin',
        'tools/h14_staged_image_patch.py'
    ],
    'write_paths': [
        'build/agent-work/H14-semantic/h14-integrated-stage/code.h14-final.bin',
        'build/agent-work/H14-semantic/h14-integrated-stage/code.h14-final.ips',
        'build/agent-work/H14-semantic/h14-integrated-stage/h14_staging_summary.json',
        'docs/agent-work/h14-batch-integration.md'
    ],
    'compiler_slots': 1,
    'exclusive_resources': [],
    'acceptance': [
        'Generate code.h14-final.bin with all H14 patches applied.',
        'Emit LayeredFS IPS mod with roundtrip verification.'
    ],
    'validation_plan': [
        'python tools/h14_staged_image_patch.py'
    ]
})

tasks.append({
    'id': 'h14-batch-integration-review',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Review cumulative batch integration for Milestone H14.',
    'depends_on': ['h14-batch-integration'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h14-batch-integration.md',
        'build/agent-work/H14-semantic/h14-integrated-stage/h14_staging_summary.json'
    ],
    'write_paths': [
        'docs/agent-work/h14-batch-integration-review.md'
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
    'id': 'h14-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Milestone H14 closure, documentation finalization, and transition to Milestone H15.',
    'depends_on': ['h14-batch-integration-review'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h14-batch-integration-review.md',
        'build/agent-work/H14-semantic/h14-integrated-stage/h14_staging_summary.json',
    ],
    'write_paths': [
        'docs/milestones/H14-graphics-engine.md',
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
    'batch': 'batch-h14-001',
    'milestone': 'H14',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H14 (ASD Graphics Engine: Scene, 3D Models, Textures, Effects), covering particle effect lock enter and exit (AsdEffect_LockEnter, AsdEffect_LockLeave), resource manager context routing (AsdRes_GetContext), GPU heap size parameter query (AsdGpu_HeapSize), text shader register code field setters (AsdText_SetCodeField1C, AsdText_SetCodeField14, AsdText_SetCodeField30), and texture streaming comparator (TextureStreamer_Compare) with offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h14.json',
        'config/reconstruction.json',
        'docs/milestones/H14-graphics-engine.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

board_path = ROOT / 'config/agent-workflows/h14.json'
board_path.parent.mkdir(parents=True, exist_ok=True)
board_path.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Board config/agent-workflows/h14.json generated with {len(tasks)} tasks.")
