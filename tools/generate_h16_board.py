#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h16.json for Milestone H16."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'asdsoundeffect-setbuffer',
        'func': '0x00110c2c',
        'name': 'AsdSoundEffect_SetBuffer',
        'desc': 'Sound effect buffer pointer and size registration',
        'cand_src': 'experiments/semantic_equivalence/h16_asdsoundeffect_setbuffer_candidate.cpp',
        'test_src': 'tools/h16_asdsoundeffect_setbuffer_experiment.py',
        'contract_doc': 'docs/agent-work/h16-asdsoundeffect-setbuffer-contract.md',
        'cand_doc': 'docs/agent-work/h16-asdsoundeffect-setbuffer-candidate.md',
    },
    {
        'id': 'asdsoundeffect-getbuffersize',
        'func': '0x00110c44',
        'name': 'AsdSoundEffect_GetBufferSize',
        'desc': 'Sound effect buffer size calculation from rate and channels',
        'cand_src': 'experiments/semantic_equivalence/h16_asdsoundeffect_getbuffersize_candidate.cpp',
        'test_src': 'tools/h16_asdsoundeffect_getbuffersize_experiment.py',
        'contract_doc': 'docs/agent-work/h16-asdsoundeffect-getbuffersize-contract.md',
        'cand_doc': 'docs/agent-work/h16-asdsoundeffect-getbuffersize-candidate.md',
    },
    {
        'id': 'asdsoundeffect2-setbuffer',
        'func': '0x00121150',
        'name': 'AsdSoundEffect2_SetBuffer',
        'desc': 'Secondary sound effect buffer and length assignment',
        'cand_src': 'experiments/semantic_equivalence/h16_asdsoundeffect2_setbuffer_candidate.cpp',
        'test_src': 'tools/h16_asdsoundeffect2_setbuffer_experiment.py',
        'contract_doc': 'docs/agent-work/h16-asdsoundeffect2-setbuffer-contract.md',
        'cand_doc': 'docs/agent-work/h16-asdsoundeffect2-setbuffer-candidate.md',
    },
    {
        'id': 'asdsound-getdatasize',
        'func': '0x00121f20',
        'name': 'AsdSound_GetDataSize',
        'desc': 'Audio data block size calculation with word alignment',
        'cand_src': 'experiments/semantic_equivalence/h16_asdsound_getdatasize_candidate.cpp',
        'test_src': 'tools/h16_asdsound_getdatasize_experiment.py',
        'contract_doc': 'docs/agent-work/h16-asdsound-getdatasize-contract.md',
        'cand_doc': 'docs/agent-work/h16-asdsound-getdatasize-candidate.md',
    },
    {
        'id': 'asdsound-getsamplebytes',
        'func': '0x00122094',
        'name': 'AsdSound_GetSampleBytes',
        'desc': 'Audio sample buffer byte size calculation from sample count',
        'cand_src': 'experiments/semantic_equivalence/h16_asdsound_getsamplebytes_candidate.cpp',
        'test_src': 'tools/h16_asdsound_getsamplebytes_experiment.py',
        'contract_doc': 'docs/agent-work/h16-asdsound-getsamplebytes-contract.md',
        'cand_doc': 'docs/agent-work/h16-asdsound-getsamplebytes-candidate.md',
    },
    {
        'id': 'asddata-getbase',
        'func': '0x00128f34',
        'name': 'AsdData_GetBase',
        'desc': 'Sound data payload base pointer derivation',
        'cand_src': 'experiments/semantic_equivalence/h16_asddata_getbase_candidate.cpp',
        'test_src': 'tools/h16_asddata_getbase_experiment.py',
        'contract_doc': 'docs/agent-work/h16-asddata-getbase-contract.md',
        'cand_doc': 'docs/agent-work/h16-asddata-getbase-candidate.md',
    },
    {
        'id': 'asddata-getcount',
        'func': '0x00128f44',
        'name': 'AsdData_GetCount',
        'desc': 'Sound data element count lookup from header offset',
        'cand_src': 'experiments/semantic_equivalence/h16_asddata_getcount_candidate.cpp',
        'test_src': 'tools/h16_asddata_getcount_experiment.py',
        'contract_doc': 'docs/agent-work/h16-asddata-getcount-contract.md',
        'cand_doc': 'docs/agent-work/h16-asddata-getcount-candidate.md',
    },
    {
        'id': 'statusdown-setactivesoundid',
        'func': '0x00215a44',
        'name': 'StatusDown_SetActiveSoundId',
        'desc': 'Status sound active track ID update in global sound context',
        'cand_src': 'experiments/semantic_equivalence/h16_statusdown_setactivesoundid_candidate.cpp',
        'test_src': 'tools/h16_statusdown_setactivesoundid_experiment.py',
        'contract_doc': 'docs/agent-work/h16-statusdown-setactivesoundid-contract.md',
        'cand_doc': 'docs/agent-work/h16-statusdown-setactivesoundid-candidate.md',
    },
]

all_funcs = [s['func'] for s in subsystems]

tasks = []

# Global Recon & Review
tasks.append({
    'id': 'h16-audio-engine-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H16 Audio, Voices, and Video / Mobiclip Subsystem.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/reconstruction-milestones.md',
        'docs/milestones/H15-ui-engine.md',
    ],
    'write_paths': [
        'docs/agent-work/h16-audio-engine-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H16 Audio subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h16-audio-engine-recon-review',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H16 Audio architecture reconnaissance.',
    'depends_on': ['h16-audio-engine-recon'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h16-audio-engine-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h16-audio-engine-recon-review.md'
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
        'id': f'h16-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Recover precise calling contract, memory boundaries, and semantics for {sub['name']}.",
        'depends_on': ['h16-audio-engine-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['extracted/exefs/code.bin'],
        'write_paths': [sub['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Recover registers, arguments, preconditions, and return values.'],
        'validation_plan': ['Static disassembly analysis.']
    })

    tasks.append({
        'id': f'h16-{sid}-contract-review',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review contract specification for {sub['name']}.",
        'depends_on': [f'h16-{sid}-contract'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [f'docs/agent-work/h16-{sid}-contract-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve verified contract record.'],
        'validation_plan': ['Compare contract against disassembled original.']
    })

    # 2. Implementation
    tasks.append({
        'id': f'h16-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Implement clean, editable C++ candidate for {sub['name']} within binary window footprint.",
        'depends_on': [f'h16-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [sub['contract_doc']],
        'write_paths': [sub['cand_src'], sub['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [sub['cand_src']],
        'acceptance': ['Compile freestanding ARMv6K object within allocated window footprint.'],
        'validation_plan': ['python tools/build_h16_all.py']
    })

    tasks.append({
        'id': f'h16-{sid}-cand-review',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Independent review of candidate implementation for {sub['name']}.",
        'depends_on': [f'h16-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], sub['cand_doc']],
        'write_paths': [f'docs/agent-work/h16-{sid}-cand-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify absence of undefined behavior and correct ABI compliance.'],
        'validation_plan': ['Source inspection.']
    })

    # 3. Differential Test
    tasks.append({
        'id': f'h16-{sid}-diff-test',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Execute offline Unicorn differential test suite for {sub['name']} comparing against pinned binary.",
        'depends_on': [f'h16-{sid}-cand-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src'], 'extracted/exefs/code.bin'],
        'write_paths': [sub['test_src'], f'docs/agent-work/h16-{sid}-diff-test.md'],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Pass all test vectors with 100% register and memory parity and verify mutation detection.'],
        'validation_plan': [f'python {sub["test_src"]}']
    })

    tasks.append({
        'id': f'h16-{sid}-diff-test-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review differential validation results for {sub['name']}.",
        'depends_on': [f'h16-{sid}-diff-test'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h16-{sid}-diff-test.md'],
        'write_paths': [f'docs/agent-work/h16-{sid}-diff-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve differential validation record.'],
        'validation_plan': ['Audit differential run log.']
    })

    # 4. Promotion
    tasks.append({
        'id': f'h16-{sid}-promotion',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Promote validated C++ candidate for {sub['name']} into milestone staging pipeline.",
        'depends_on': [f'h16-{sid}-diff-test-review'],
        'function_claims': fclaim,
        'read_paths': [sub['cand_src']],
        'write_paths': [f'docs/agent-work/h16-{sid}-promotion.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Record candidate readiness for binary staging composition.'],
        'validation_plan': ['Verify staging eligibility.']
    })

    tasks.append({
        'id': f'h16-{sid}-promotion-review',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f"Review candidate promotion for {sub['name']}.",
        'depends_on': [f'h16-{sid}-promotion'],
        'function_claims': fclaim,
        'read_paths': [f'docs/agent-work/h16-{sid}-promotion.md'],
        'write_paths': [f'docs/agent-work/h16-{sid}-promotion-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm promotion into milestone integrated stage.'],
        'validation_plan': ['Audit promotion record.']
    })

# Global Milestone Integration & Closure Tasks
tasks.append({
    'id': 'h16-integrated-staging',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 validated H16 candidates over code.h15-final.bin to generate code.h16-final.bin and IPS patch.',
    'depends_on': [f"h16-{s['id']}-promotion-review" for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': [s['cand_src'] for s in subsystems] + ['build/agent-work/H15-semantic/h15-integrated-stage/code.h15-final.bin'],
    'write_paths': [
        'tools/h16_staged_image_patch.py',
        'build/agent-work/H16-semantic/h16-integrated-stage/code.h16-final.bin',
        'build/agent-work/H16-semantic/h16-integrated-stage/code.h16-final.ips',
        'build/agent-work/H16-semantic/h16-integrated-stage/h16_staging_summary.json',
        'docs/agent-work/h16-integrated-staging.md',
    ],
    'compiler_slots': 1,
    'exclusive_resources': ['code.h16-final.bin'],
    'acceptance': [
        'Generate code.h16-final.bin with all 8 candidates cleanly applied within windows.',
        'Produce verified LayeredFS IPS patch code.h16-final.ips passing roundtrip verification.'
    ],
    'validation_plan': ['python tools/h16_staged_image_patch.py']
})

tasks.append({
    'id': 'h16-milestone-closure-review',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review and closure of Milestone H16 (Audio/Video/Mobiclip Subsystem).',
    'depends_on': ['h16-integrated-staging'],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H16-semantic/h16-integrated-stage/h16_staging_summary.json',
        'docs/agent-work/h16-integrated-staging.md',
    ],
    'write_paths': [
        'docs/agent-work/h16-milestone-closure-review.md',
        'docs/milestones/H16-audio-engine.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify that all 8 subsystems have complete contract, implementation, differential test, and promotion records.',
        'Validate offline differential test suite passes 100% and staging IPS patch roundtrip passes.'
    ],
    'validation_plan': [
        'python tools/agent_workflow.py check',
        'python tools/generate_h16_experiments.py',
        'python tools/h16_staged_image_patch.py'
    ]
})

board = {
    'schema_version': 1,
    'batch': 'batch-h16-001',
    'milestone': 'H16',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H16 (Audio/Video/Mobiclip Subsystem), covering sound effect buffer assignment, rate/channel buffer size calculation, secondary buffer assignment, data size calculation, sample byte calculation, data base pointer derivation, data element count lookup, and status sound track ID update with offline differential validation, staging, and autonomous verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h16.json',
        'config/reconstruction.json',
        'docs/milestones/H16-audio-engine.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_board = ROOT / 'config/agent-workflows/h16.json'
out_board.parent.mkdir(parents=True, exist_ok=True)
out_board.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Workflow board written to {out_board} with {len(tasks)} tasks.")
