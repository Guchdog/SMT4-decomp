#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h12.json for Milestone H12."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'battle-initturnsubsystems',
        'func': '0x00123050',
        'name': 'Battle_InitTurnSubsystems',
        'desc': 'Battle turn subsystem initialization and dispatcher registration',
        'cand_src': 'experiments/semantic_equivalence/h12_battle_initturnsubsystems_candidate.cpp',
        'test_src': 'tools/h12_battle_initturnsubsystems_experiment.py',
        'contract_doc': 'docs/agent-work/h12-battle-initturnsubsystems-contract.md',
        'cand_doc': 'docs/agent-work/h12-battle-initturnsubsystems-candidate.md',
    },
    {
        'id': 'battle-getunitsmirkstate',
        'func': '0x00129c58',
        'name': 'Battle_GetUnitSmirkState',
        'desc': 'Party and enemy unit smirk condition state query across active smirk work struct',
        'cand_src': 'experiments/semantic_equivalence/h12_battle_getunitsmirkstate_candidate.cpp',
        'test_src': 'tools/h12_battle_getunitsmirkstate_experiment.py',
        'contract_doc': 'docs/agent-work/h12-battle-getunitsmirkstate-contract.md',
        'cand_doc': 'docs/agent-work/h12-battle-getunitsmirkstate-candidate.md',
    },
    {
        'id': 'battle-getsmirkactor',
        'func': '0x00129cbc',
        'name': 'Battle_GetSmirkActor',
        'desc': 'Active smirk buff owner entity reference lookup',
        'cand_src': 'experiments/semantic_equivalence/h12_battle_getsmirkactor_candidate.cpp',
        'test_src': 'tools/h12_battle_getsmirkactor_experiment.py',
        'contract_doc': 'docs/agent-work/h12-battle-getsmirkactor-contract.md',
        'cand_doc': 'docs/agent-work/h12-battle-getsmirkactor-candidate.md',
    },
    {
        'id': 'battle-exchangesmirkslot',
        'func': '0x00129c70',
        'name': 'Battle_ExchangeSmirkSlot',
        'desc': 'Atomic smirk state slot exchange with boundary validation and lock/unlock guard',
        'cand_src': 'experiments/semantic_equivalence/h12_battle_exchangesmirkslot_candidate.cpp',
        'test_src': 'tools/h12_battle_exchangesmirkslot_experiment.py',
        'contract_doc': 'docs/agent-work/h12-battle-exchangesmirkslot-contract.md',
        'cand_doc': 'docs/agent-work/h12-battle-exchangesmirkslot-candidate.md',
    },
    {
        'id': 'battle-initturndata',
        'func': '0x00136fa4',
        'name': 'Battle_InitTurnData',
        'desc': 'Turn phase data setup and state work bitfield flag configuration',
        'cand_src': 'experiments/semantic_equivalence/h12_battle_initturndata_candidate.cpp',
        'test_src': 'tools/h12_battle_initturndata_experiment.py',
        'contract_doc': 'docs/agent-work/h12-battle-initturndata-contract.md',
        'cand_doc': 'docs/agent-work/h12-battle-initturndata-candidate.md',
    },
    {
        'id': 'result-cleanup',
        'func': '0x001c87d8',
        'name': 'Result_Cleanup',
        'desc': 'Combat victory and defeat result screen resource deallocation and context teardown',
        'cand_src': 'experiments/semantic_equivalence/h12_result_cleanup_candidate.cpp',
        'test_src': 'tools/h12_result_cleanup_experiment.py',
        'contract_doc': 'docs/agent-work/h12-result-cleanup-contract.md',
        'cand_doc': 'docs/agent-work/h12-result-cleanup-candidate.md',
    },
    {
        'id': 'battle-isunitdefeated',
        'func': '0x0028de4c',
        'name': 'Battle_IsUnitDefeated',
        'desc': 'Battle unit defeat status evaluation checking unsummoned/inactive bitfield and remaining HP',
        'cand_src': 'experiments/semantic_equivalence/h12_battle_isunitdefeated_candidate.cpp',
        'test_src': 'tools/h12_battle_isunitdefeated_experiment.py',
        'contract_doc': 'docs/agent-work/h12-battle-isunitdefeated-contract.md',
        'cand_doc': 'docs/agent-work/h12-battle-isunitdefeated-candidate.md',
    },
    {
        'id': 'battle-resetunitstatebuffer',
        'func': '0x00215938',
        'name': 'Battle_ResetUnitStateBuffer',
        'desc': 'Battle unit state work buffer copy and restoration',
        'cand_src': 'experiments/semantic_equivalence/h12_battle_resetunitstatebuffer_candidate.cpp',
        'test_src': 'tools/h12_battle_resetunitstatebuffer_experiment.py',
        'contract_doc': 'docs/agent-work/h12-battle-resetunitstatebuffer-contract.md',
        'cand_doc': 'docs/agent-work/h12-battle-resetunitstatebuffer-candidate.md',
    },
]

all_funcs = [s['func'] for s in subsystems]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h12-advanced-combat-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H12 Advanced Combat (Press Turn, Smirk, Negotiation, Results).',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': [
        'src/battle/battle_runtime.cpp',
        'docs/reconstruction-milestones.md',
        'docs/milestones/H11-shops-blackmarket-terminals.md',
    ],
    'write_paths': [
        'docs/agent-work/h12-advanced-combat-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H12 Advanced Combat subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

# Task 2: Architecture Review
tasks.append({
    'id': 'h12-advanced-combat-recon-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H12 Advanced Combat architecture reconnaissance and differential boundary definitions.',
    'depends_on': ['h12-advanced-combat-recon'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h12-advanced-combat-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h12-advanced-combat-recon-review.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Validate candidate function selections against milestone goals and footprint requirements.'
    ],
    'validation_plan': [
        'Inspect address ranges, calling conventions, and struct layouts.'
    ]
})

# Per-subsystem tasks: 10 tasks per subsystem (contract, contract-rev, cand, cand-rev, test, test-rev, diff, diff-rev, int, int-rev)
for s in subsystems:
    sid = s['id']
    fn = s['func']
    name = s['name']
    desc = s['desc']
    fclaim = [fn]

    # Contract
    tasks.append({
        'id': f'h12-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Recover formal semantic contract, types, and ABI for {name} ({fn}).',
        'depends_on': ['h12-advanced-combat-recon-review'],
        'function_claims': fclaim,
        'read_paths': [
            'docs/agent-work/h12-advanced-combat-recon.md',
            'extracted/exefs/code.bin',
        ],
        'write_paths': [
            s['contract_doc']
        ],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [
            f'Document contract, pre/postconditions, parameter semantics, and mutations for {name}.'
        ],
        'validation_plan': [
            'Audit ARM assembly in code.bin at target address.'
        ]
    })

    # Contract Review
    tasks.append({
        'id': f'h12-{sid}-contract-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of formal semantic contract for {name} ({fn}).',
        'depends_on': [f'h12-{sid}-contract'],
        'function_claims': fclaim,
        'read_paths': [s['contract_doc']],
        'write_paths': [f'docs/agent-work/h12-{sid}-contract-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify contract accuracy against disassembly.'],
        'validation_plan': ['Cross-check against Capstone disassembly.']
    })

    # Candidate
    tasks.append({
        'id': f'h12-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement clean C++ semantic candidate and mutation probe for {name} ({fn}).',
        'depends_on': [f'h12-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [s['contract_doc']],
        'write_paths': [
            s['cand_src'],
            s['cand_doc'],
        ],
        'compiler_slots': 1,
        'exclusive_resources': [s['cand_src']],
        'acceptance': [
            f'Candidate compiles cleanly with clang++ ARMv6K and fits within target window.'
        ],
        'validation_plan': [
            'Compile candidate TU to object file and check binary footprint.'
        ]
    })

    # Candidate Review
    tasks.append({
        'id': f'h12-{sid}-candidate-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of C++ candidate implementation for {name} ({fn}).',
        'depends_on': [f'h12-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['cand_doc']],
        'write_paths': [f'docs/agent-work/h12-{sid}-candidate-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify C++ readability, contract adherence, and footprint safety.'],
        'validation_plan': ['Review source code and compiler diagnostic output.']
    })

    # Test
    tasks.append({
        'id': f'h12-{sid}-test',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement standalone Unicorn differential test harness for {name} ({fn}).',
        'depends_on': [f'h12-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['contract_doc']],
        'write_paths': [
            s['test_src'],
            f'docs/agent-work/h12-{sid}-test.md',
        ],
        'compiler_slots': 1,
        'exclusive_resources': [s['test_src']],
        'acceptance': [
            f'Harness executes original vs candidate across test vectors with register/memory verification.'
        ],
        'validation_plan': [
            'Run script under python with Unicorn engine.'
        ]
    })

    # Test Review
    tasks.append({
        'id': f'h12-{sid}-test-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of differential test harness for {name} ({fn}).',
        'depends_on': [f'h12-{sid}-test'],
        'function_claims': fclaim,
        'read_paths': [s['test_src'], f'docs/agent-work/h12-{sid}-test.md'],
        'write_paths': [f'docs/agent-work/h12-{sid}-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify test coverage, boundary cases, and mutation sensitivity check.'],
        'validation_plan': ['Audit test logic and execution trace.']
    })

    # Diff
    tasks.append({
        'id': f'h12-{sid}-diff',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Execute offline Unicorn differential validation suite for {name} ({fn}).',
        'depends_on': [f'h12-{sid}-test-review'],
        'function_claims': fclaim,
        'read_paths': [s['test_src'], s['cand_src']],
        'write_paths': [f'docs/agent-work/h12-{sid}-diff.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            'All differential test cases pass with 100% register/memory parity; mutation probe triggers mismatch.'
        ],
        'validation_plan': [
            f'python {s["test_src"]}'
        ]
    })

    # Diff Review
    tasks.append({
        'id': f'h12-{sid}-diff-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent audit of differential execution results for {name} ({fn}).',
        'depends_on': [f'h12-{sid}-diff'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h12-{sid}-diff.md'],
        'write_paths': [f'docs/agent-work/h12-{sid}-diff-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm 100% equivalence and mutation sensitivity.'],
        'validation_plan': ['Verify differential test logs and assertion proofs.']
    })

    # Subsystem Integration
    tasks.append({
        'id': f'h12-{sid}-integration',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Stage binary candidate {name} ({fn}) into composite image.',
        'depends_on': [f'h12-{sid}-diff-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [f'docs/agent-work/h12-{sid}-integration.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            'Candidate integrated into staged binary with relocations resolved.'
        ],
        'validation_plan': [
            'Verify relocations and memory offset layout.'
        ]
    })

    # Subsystem Integration Review
    tasks.append({
        'id': f'h12-{sid}-integration-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent audit of staged candidate integration for {name} ({fn}).',
        'depends_on': [f'h12-{sid}-integration'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h12-{sid}-integration.md'],
        'write_paths': [f'docs/agent-work/h12-{sid}-integration-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify candidate footprint compliance in composite stage.'],
        'validation_plan': ['Audit integration record.']
    })

# Final Integration & Verification Tasks
tasks.append({
    'id': 'h12-batch-integration',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 H12 candidates over H11 staged baseline image and build IPS LayeredFS patch.',
    'depends_on': [f'h12-{s["id"]}-integration-review' for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H11-semantic/h11-integrated-stage/code.h11-final.bin',
        'tools/h12_staged_image_patch.py',
    ],
    'write_paths': [
        'build/agent-work/H12-semantic/h12-integrated-stage/code.h12-final.bin',
        'build/agent-work/H12-semantic/h12-integrated-stage/code.h12-final.ips',
        'build/agent-work/H12-semantic/h12-integrated-stage/h12_staging_summary.json',
        'docs/agent-work/h12-batch-integration.md',
    ],
    'compiler_slots': 2,
    'exclusive_resources': [],
    'acceptance': [
        'code.h12-final.bin successfully generated with all 8 functions patched.',
        'code.h12-final.ips successfully generated with round-trip fidelity verified.',
    ],
    'validation_plan': [
        'python tools/h12_staged_image_patch.py'
    ]
})

tasks.append({
    'id': 'h12-batch-integration-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review and verification of H12 composite binary, IPS patch, and staging summary.',
    'depends_on': ['h12-batch-integration'],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H12-semantic/h12-integrated-stage/h12_staging_summary.json',
        'docs/agent-work/h12-batch-integration.md',
    ],
    'write_paths': [
        'docs/agent-work/h12-batch-integration-review.md'
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
    'id': 'h12-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Milestone H12 closure, documentation finalization, and transition to Milestone H13.',
    'depends_on': ['h12-batch-integration-review'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h12-batch-integration-review.md',
        'build/agent-work/H12-semantic/h12-integrated-stage/h12_staging_summary.json',
    ],
    'write_paths': [
        'docs/milestones/H12-advanced-combat.md',
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
    'batch': 'batch-h12-001',
    'milestone': 'H12',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H12 (Advanced Combat: Press Turn, Smirk, Negotiation, Results), covering turn subsystems initialization (Battle_InitTurnSubsystems), smirk condition query (Battle_GetUnitSmirkState), smirk actor owner lookup (Battle_GetSmirkActor), atomic smirk slot exchange (Battle_ExchangeSmirkSlot), turn phase data setup (Battle_InitTurnData), victory/defeat result screen teardown (Result_Cleanup), battle unit defeat evaluation (Battle_IsUnitDefeated), and unit state buffer restoration (Battle_ResetUnitStateBuffer) with offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h12.json',
        'config/reconstruction.json',
        'docs/milestones/H12-advanced-combat.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

board_path = ROOT / 'config/agent-workflows/h12.json'
board_path.parent.mkdir(parents=True, exist_ok=True)
board_path.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Board config/agent-workflows/h12.json generated with {len(tasks)} tasks.")
