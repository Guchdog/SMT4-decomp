#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h6.json for Milestone H6."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'save-common-read',
        'func': '0x0021041c',
        'name': 'AsdSaveCommon_Read',
        'desc': 'common save container read unpacking 0x80-byte header and payload via AsdSave_Read',
        'cand_src': 'experiments/semantic_equivalence/h6_asd_save_common_read_candidate.cpp',
        'test_src': 'tools/h6_asd_save_common_read_experiment.py',
        'contract_doc': 'docs/agent-work/h6-asd-save-common-read-contract.md',
        'cand_doc': 'docs/agent-work/h6-asd-save-common-read-candidate.md',
    },
    {
        'id': 'save-common-write',
        'func': '0x002104e8',
        'name': 'AsdSaveCommon_Write',
        'desc': 'common save container write packing 0x80-byte header and payload via AsdSave_Write',
        'cand_src': 'experiments/semantic_equivalence/h6_asd_save_common_write_candidate.cpp',
        'test_src': 'tools/h6_asd_save_common_write_experiment.py',
        'contract_doc': 'docs/agent-work/h6-asd-save-common-write-contract.md',
        'cand_doc': 'docs/agent-work/h6-asd-save-common-write-candidate.md',
    },
    {
        'id': 'saveload-process-init',
        'func': '0x0026b874',
        'name': 'SaveLoadProcess_Init',
        'desc': 'save/load worker process state initialization, heap allocation, and task creation',
        'cand_src': 'experiments/semantic_equivalence/h6_saveload_process_init_candidate.cpp',
        'test_src': 'tools/h6_saveload_process_init_experiment.py',
        'contract_doc': 'docs/agent-work/h6-saveload-process-init-contract.md',
        'cand_doc': 'docs/agent-work/h6-saveload-process-init-candidate.md',
    },
    {
        'id': 'saveload-process-step',
        'func': '0x002ef9ac',
        'name': 'SaveLoadProcess_Step',
        'desc': 'save/load async worker execution step handling states 4, 5, 6, 7 and completion callbacks',
        'cand_src': 'experiments/semantic_equivalence/h6_saveload_process_step_candidate.cpp',
        'test_src': 'tools/h6_saveload_process_step_experiment.py',
        'contract_doc': 'docs/agent-work/h6-saveload-process-step-contract.md',
        'cand_doc': 'docs/agent-work/h6-saveload-process-step-candidate.md',
    },
    {
        'id': 'saveload-process-write',
        'func': '0x002efb50',
        'name': 'SaveLoadProcess_Write',
        'desc': 'save/load worker write state machine handling stages 0, 1, 2, 3 and dispatch',
        'cand_src': 'experiments/semantic_equivalence/h6_saveload_process_write_candidate.cpp',
        'test_src': 'tools/h6_saveload_process_write_experiment.py',
        'contract_doc': 'docs/agent-work/h6-saveload-process-write-contract.md',
        'cand_doc': 'docs/agent-work/h6-saveload-process-write-candidate.md',
    },
    {
        'id': 'saveload-process-read',
        'func': '0x00322d70',
        'name': 'SaveLoadProcess_Read',
        'desc': 'save/load worker read operation dispatcher and buffer setup',
        'cand_src': 'experiments/semantic_equivalence/h6_saveload_process_read_candidate.cpp',
        'test_src': 'tools/h6_saveload_process_read_experiment.py',
        'contract_doc': 'docs/agent-work/h6-saveload-process-read-contract.md',
        'cand_doc': 'docs/agent-work/h6-saveload-process-read-candidate.md',
    },
    {
        'id': 'saveload-process-close',
        'func': '0x00322f0c',
        'name': 'SaveLoadProcess_Close',
        'desc': 'save/load worker process spawn routine for Save task',
        'cand_src': 'experiments/semantic_equivalence/h6_saveload_process_close_candidate.cpp',
        'test_src': 'tools/h6_saveload_process_close_experiment.py',
        'contract_doc': 'docs/agent-work/h6-saveload-process-close-contract.md',
        'cand_doc': 'docs/agent-work/h6-saveload-process-close-candidate.md',
    },
    {
        'id': 'saveload-ui-init',
        'func': '0x00191eac',
        'name': 'saveLoadUI_Init',
        'desc': 'save/load UI manager workspace allocation and BOOT Calc task setup',
        'cand_src': 'experiments/semantic_equivalence/h6_saveload_ui_init_candidate.cpp',
        'test_src': 'tools/h6_saveload_ui_init_experiment.py',
        'contract_doc': 'docs/agent-work/h6-saveload-ui-init-contract.md',
        'cand_doc': 'docs/agent-work/h6-saveload-ui-init-candidate.md',
    },
]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h6-save-persistence-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H6 Save and Reload systems.',
    'depends_on': [],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'src/ui/save_load.cpp',
        'src/engine/asd_file.cpp',
        'include/ui/save_load.h',
        'docs/reconstruction-milestones.md',
        'docs/milestones/H5-combat-minimum.md'
    ],
    'write_paths': [
        'docs/agent-work/h6-save-persistence-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H6 save/load subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h6-save-persistence-recon-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of save and reload architecture reconnaissance and subsystem boundary definitions.',
    'depends_on': ['h6-save-persistence-recon'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'docs/agent-work/h6-save-persistence-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h6-save-persistence-recon-review.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify contract boundaries, calling conventions, and ABI preservation expectations.',
        'Approve task division and candidate scope for H6 save and reload milestone.'
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
    diff_doc = f"docs/agent-work/h6-{sid}-differential.md"
    diff_review_doc = f"docs/agent-work/h6-{sid}-differential-review.md"
    comp_doc = f"docs/agent-work/h6-{sid}-composition.md"
    comp_review_doc = f"docs/agent-work/h6-{sid}-composition-review.md"
    stag_doc = f"docs/agent-work/h6-{sid}-staging.md"
    stag_review_doc = f"docs/agent-work/h6-{sid}-staging-review.md"

    # Contract
    tasks.append({
        'id': f'h6-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Formalize contract, parameters, registers, and memory effects for {sname} ({sfunc}).',
        'depends_on': ['h6-save-persistence-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['src/ui/save_load.cpp', 'src/engine/asd_file.cpp', 'include/ui/save_load.h'],
        'write_paths': [s['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Accurately specify semantics of {sname}.', 'Specify test fixtures and mutation controls.'],
        'validation_plan': ['Static disassembly and register effect verification against code.bin.']
    })

    # Contract Review
    tasks.append({
        'id': f'h6-{sid}-contract-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of {sname} contract specification.',
        'depends_on': [f'h6-{sid}-contract'],
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
        'id': f'h6-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement readable, editable C++ candidate for {sname} ({sfunc}) fitting binary window.',
        'depends_on': [f'h6-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [s['contract_doc']],
        'write_paths': [s['cand_src'], s['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            f'Candidate for {sname} compiles cleanly under Clang ARMv6K.',
            'Size in bytes does not exceed original function window in code.bin.'
        ],
        'validation_plan': ['Compile with clang -target arm-none-eabi -march=armv6k and measure text section size.']
    })

    # Candidate Review
    tasks.append({
        'id': f'h6-{sid}-candidate-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of C++ semantic candidate for {sname} ({sfunc}).',
        'depends_on': [f'h6-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['cand_doc']],
        'write_paths': [cand_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify C++ implementation readability, semantic correctness, and ABI compliance.'],
        'validation_plan': ['Independent source audit and disassembly inspection.']
    })

    # Differential Test
    tasks.append({
        'id': f'h6-{sid}-differential',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Unicorn differential test comparing compiled C++ candidate vs original ARM binary for {sname} ({sfunc}).',
        'depends_on': [f'h6-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], 'extracted/exefs/code.bin'],
        'write_paths': [s['test_src'], diff_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            'All differential test cases pass with 0 register and memory differences.',
            'Negative mutation controls fail, proving test sensitivity.'
        ],
        'validation_plan': [f'Execute python {s["test_src"]}.']
    })

    # Differential Review
    tasks.append({
        'id': f'h6-{sid}-differential-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of differential test results and mutation sensitivity for {sname}.',
        'depends_on': [f'h6-{sid}-differential'],
        'function_claims': fclaim,
        'read_paths': [s['test_src'], diff_doc],
        'write_paths': [diff_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm 100% test pass and verified mutation sensitivity.'],
        'validation_plan': ['Independent review of test output logs and mutation test cases.']
    })

    # Composition
    tasks.append({
        'id': f'h6-{sid}-composition',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Caller composition verification for {sname} ({sfunc}) with surrounding callers.',
        'depends_on': [f'h6-{sid}-differential-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], 'src/ui/save_load.cpp'],
        'write_paths': [comp_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify caller stack frame compatibility, register preservation, and return values.'],
        'validation_plan': ['Static caller-callee call graph and stack layout inspection.']
    })

    # Composition Review
    tasks.append({
        'id': f'h6-{sid}-composition-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of caller composition for {sname}.',
        'depends_on': [f'h6-{sid}-composition'],
        'function_claims': fclaim,
        'read_paths': [comp_doc],
        'write_paths': [comp_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm no ABI violations or calling convention mismatches.'],
        'validation_plan': ['Review call site argument setups and caller epilogues.']
    })

    # Staging
    tasks.append({
        'id': f'h6-{sid}-staging',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Stage {sname} ({sfunc}) candidate into composite binary overlay.',
        'depends_on': [f'h6-{sid}-composition-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [stag_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Verify candidate byte size fits within binary boundary at {sfunc}.'],
        'validation_plan': ['Compare binary patch range against original executable address space.']
    })

    # Staging Review
    tasks.append({
        'id': f'h6-{sid}-staging-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of staging overlay for {sname}.',
        'depends_on': [f'h6-{sid}-staging'],
        'function_claims': fclaim,
        'read_paths': [stag_doc],
        'write_paths': [stag_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm clean overlay without corrupting adjacent code or literal pools.'],
        'validation_plan': ['Verify byte boundaries and patch offset alignment.']
    })

staging_task_ids = [f'h6-{s["id"]}-staging-review' for s in subsystems]

tasks.append({
    'id': 'h6-staged-image-patch',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Generate composite patched binary code.h6-final.bin and IPS mod patch code.h6-final.ips.',
    'depends_on': staging_task_ids,
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['tools/h6_staged_image_patch.py', 'code.h5-final.bin'],
    'write_paths': ['tools/h6_staged_image_patch.py', 'docs/agent-work/h6-staged-image-patch.md'],
    'compiler_slots': 1,
    'exclusive_resources': [],
    'acceptance': [
        'Produce code.h6-final.bin containing all H0-H5 + H6 reconstructions.',
        'Generate valid code.h6-final.ips and verify round-trip application.'
    ],
    'validation_plan': ['Run python tools/h6_staged_image_patch.py and verify hashes.']
})

tasks.append({
    'id': 'h6-staged-image-patch-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of composite image patch and IPS verification.',
    'depends_on': ['h6-staged-image-patch'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h6-staged-image-patch.md'],
    'write_paths': ['docs/agent-work/h6-staged-image-patch-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Verify patch byte offsets and SHA-256 round-trip integrity.'],
    'validation_plan': ['Audit IPS encoder/decoder output and binary diffs.']
})

tasks.append({
    'id': 'h6-offline-composite-gates',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Execute all offline validation gates across all 8 candidates prior to emulator launch.',
    'depends_on': ['h6-staged-image-patch-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [s['test_src'] for s in subsystems],
    'write_paths': ['docs/agent-work/h6-offline-composite-gates.md'],
    'compiler_slots': 2,
    'exclusive_resources': [],
    'acceptance': ['All 8 candidate differential test runners pass with 0 errors.'],
    'validation_plan': ['Run each test script in succession and verify pass status.']
})

tasks.append({
    'id': 'h6-offline-composite-gates-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of offline composite gates validation.',
    'depends_on': ['h6-offline-composite-gates'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h6-offline-composite-gates.md'],
    'write_paths': ['docs/agent-work/h6-offline-composite-gates-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm all 8 test suites pass with complete mutation sensitivity.'],
    'validation_plan': ['Review gate logs and test reports.']
})

tasks.append({
    'id': 'h6-autonomous-save-verify',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Autonomous runtime verification in Azahar emulator loopback stub comparing original vs code.h6-final.ips.',
    'depends_on': ['h6-offline-composite-gates-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['tools/h3_autonomous_verify.py', 'code.h6-final.ips'],
    'write_paths': ['docs/agent-work/h6-autonomous-save-verify.md'],
    'compiler_slots': 0,
    'exclusive_resources': ['emulator_session'],
    'acceptance': [
        'Run paired autonomous test via GDB RSP loopback stub.',
        '0 register differences across Title, Save Load, and 250 Field scene ticks.'
    ],
    'validation_plan': ['Execute autonomous verify script and generate paired report.json.']
})

tasks.append({
    'id': 'h6-autonomous-save-verify-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of autonomous paired runtime verification for Milestone H6.',
    'depends_on': ['h6-autonomous-save-verify'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h6-autonomous-save-verify.md'],
    'write_paths': ['docs/agent-work/h6-autonomous-save-verify-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm 100% paired equivalence with zero register or state differences.'],
    'validation_plan': ['Audit runtime report metrics and save file hash integrity.']
})

tasks.append({
    'id': 'h6-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Formalize closure of Milestone H6 across documentation and ledger tracking.',
    'depends_on': ['h6-autonomous-save-verify-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/milestones/H6-save-and-reload.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'write_paths': ['docs/milestones/H6-save-and-reload.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Update documentation marking Milestone H6 as completed and closed.',
        'Ensure clean git state and 0 errors from tools/agent_workflow.py check.'
    ],
    'validation_plan': ['Run python tools/agent_workflow.py check.']
})

board = {
    'schema_version': 1,
    'batch': 'batch-h6-001',
    'milestone': 'H6',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H6 (Save and Reload), covering save common read/write container packing, worker process lifecycle and task setup, asynchronous step execution machine, and UI workspace initialization with full offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h6.json',
        'config/reconstruction.json',
        'docs/milestones/H6-save-and-reload.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_path = ROOT / 'config/agent-workflows/h6.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(board, f, indent=2)

print(f'Successfully wrote h6.json with {len(tasks)} tasks to {out_path}')
