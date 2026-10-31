#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h7.json for Milestone H7."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'ui-comwin-init',
        'func': '0x0010a748',
        'name': 'ComWin_Init',
        'desc': 'Dialog window manager initialization and viewport draw passes registration',
        'cand_src': 'experiments/semantic_equivalence/h7_ui_comwin_init_candidate.cpp',
        'test_src': 'tools/h7_ui_comwin_init_experiment.py',
        'contract_doc': 'docs/agent-work/h7-ui-comwin-init-contract.md',
        'cand_doc': 'docs/agent-work/h7-ui-comwin-init-candidate.md',
    },
    {
        'id': 'ui-comwin-reset',
        'func': '0x0010aee4',
        'name': 'ComWin_Reset',
        'desc': 'Dialog response slot teardown and choice state reset',
        'cand_src': 'experiments/semantic_equivalence/h7_ui_comwin_reset_candidate.cpp',
        'test_src': 'tools/h7_ui_comwin_reset_experiment.py',
        'contract_doc': 'docs/agent-work/h7-ui-comwin-reset-contract.md',
        'cand_doc': 'docs/agent-work/h7-ui-comwin-reset-candidate.md',
    },
    {
        'id': 'ui-infowin-init',
        'func': '0x0010af84',
        'name': 'InfoWin_Init',
        'desc': 'Event subtitle and info notification window task registration',
        'cand_src': 'experiments/semantic_equivalence/h7_ui_infowin_init_candidate.cpp',
        'test_src': 'tools/h7_ui_infowin_init_experiment.py',
        'contract_doc': 'docs/agent-work/h7-ui-infowin-init-contract.md',
        'cand_doc': 'docs/agent-work/h7-ui-infowin-init-candidate.md',
    },
    {
        'id': 'ui-guestwin-init',
        'func': '0x0010b350',
        'name': 'GuestWin_Init',
        'desc': 'Event guest dialog window frame and animation setup',
        'cand_src': 'experiments/semantic_equivalence/h7_ui_guestwin_init_candidate.cpp',
        'test_src': 'tools/h7_ui_guestwin_init_experiment.py',
        'contract_doc': 'docs/agent-work/h7-ui-guestwin-init-contract.md',
        'cand_doc': 'docs/agent-work/h7-ui-guestwin-init-candidate.md',
    },
    {
        'id': 'script-namemain-init',
        'func': '0x001d374c',
        'name': 'nameMain_Init',
        'desc': 'FlowScript character naming lifecycle and touchscreen keyboard registration',
        'cand_src': 'experiments/semantic_equivalence/h7_script_namemain_init_candidate.cpp',
        'test_src': 'tools/h7_script_namemain_init_experiment.py',
        'contract_doc': 'docs/agent-work/h7-script-namemain-init-contract.md',
        'cand_doc': 'docs/agent-work/h7-script-namemain-init-candidate.md',
    },
    {
        'id': 'script-onesroom-init',
        'func': '0x001d38fc',
        'name': 'onesRoom_Init',
        'desc': 'Barracks event room script VM runner and task registration',
        'cand_src': 'experiments/semantic_equivalence/h7_script_onesroom_init_candidate.cpp',
        'test_src': 'tools/h7_script_onesroom_init_experiment.py',
        'contract_doc': 'docs/agent-work/h7-script-onesroom-init-contract.md',
        'cand_doc': 'docs/agent-work/h7-script-onesroom-init-candidate.md',
    },
    {
        'id': 'script-eventcmd-fade',
        'func': '0x0025955c',
        'name': 'eventCommand_func_0025955c',
        'desc': 'Event command parameter evaluation and screen fade transition machine',
        'cand_src': 'experiments/semantic_equivalence/h7_script_eventcmd_fade_candidate.cpp',
        'test_src': 'tools/h7_script_eventcmd_fade_experiment.py',
        'contract_doc': 'docs/agent-work/h7-script-eventcmd-fade-contract.md',
        'cand_doc': 'docs/agent-work/h7-script-eventcmd-fade-candidate.md',
    },
    {
        'id': 'script-eventeffect-init',
        'func': '0x0030a4fc',
        'name': 'EventEffect_func_0030a4fc',
        'desc': 'Event visual effect blink and fade task initialization',
        'cand_src': 'experiments/semantic_equivalence/h7_script_eventeffect_init_candidate.cpp',
        'test_src': 'tools/h7_script_eventeffect_init_experiment.py',
        'contract_doc': 'docs/agent-work/h7-script-eventeffect-init-contract.md',
        'cand_doc': 'docs/agent-work/h7-script-eventeffect-init-candidate.md',
    },
]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h7-event-script-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H7 Script VM and Event Runtime.',
    'depends_on': [],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'src/ui/window.cpp',
        'src/script/script_vm.cpp',
        'src/script/script_extras.cpp',
        'include/script/flowscript.h',
        'docs/reconstruction-milestones.md',
        'docs/milestones/H6-save-and-reload.md'
    ],
    'write_paths': [
        'docs/agent-work/h7-event-script-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H7 script VM and event subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h7-event-script-recon-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of script VM and event runtime architecture reconnaissance and subsystem boundary definitions.',
    'depends_on': ['h7-event-script-recon'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'docs/agent-work/h7-event-script-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h7-event-script-recon-review.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify contract boundaries, calling conventions, and ABI preservation expectations.',
        'Approve task division and candidate scope for H7 script VM and event runtime milestone.'
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
    diff_doc = f"docs/agent-work/h7-{sid}-differential.md"
    diff_review_doc = f"docs/agent-work/h7-{sid}-differential-review.md"
    comp_doc = f"docs/agent-work/h7-{sid}-composition.md"
    comp_review_doc = f"docs/agent-work/h7-{sid}-composition-review.md"
    stag_doc = f"docs/agent-work/h7-{sid}-staging.md"
    stag_review_doc = f"docs/agent-work/h7-{sid}-staging-review.md"

    # Contract
    tasks.append({
        'id': f'h7-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Formalize contract, parameters, registers, and memory effects for {sname} ({sfunc}).',
        'depends_on': ['h7-event-script-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['src/ui/window.cpp', 'src/script/script_vm.cpp', 'src/script/script_extras.cpp'],
        'write_paths': [s['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Accurately specify semantics of {sname}.', 'Specify test fixtures and mutation controls.'],
        'validation_plan': ['Static disassembly and register effect verification against code.bin.']
    })

    # Contract Review
    tasks.append({
        'id': f'h7-{sid}-contract-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of {sname} contract specification.',
        'depends_on': [f'h7-{sid}-contract'],
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
        'id': f'h7-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement readable, editable C++ candidate for {sname} with mutation control.',
        'depends_on': [f'h7-{sid}-contract-review'],
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
        'id': f'h7-{sid}-candidate-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent code review of C++ reconstruction for {sname}.',
        'depends_on': [f'h7-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['cand_doc']],
        'write_paths': [cand_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Validate readable C++ idioms, absent UB, and exact ABI compatibility.'],
        'validation_plan': ['Static analysis of C++ code, type checks, and assembly review.']
    })

    # Differential
    tasks.append({
        'id': f'h7-{sid}-differential',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Execute offline ARM Unicorn differential test cases for {sname}.',
        'depends_on': [f'h7-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['test_src']],
        'write_paths': [diff_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            f'Pass 100% paired differential cases for {sname} against original ROM binary.',
            'Confirm mutation control triggers expected discrepancy (negative control).'
        ],
        'validation_plan': [f'Run python {s["test_src"]}.']
    })

    # Differential Review
    tasks.append({
        'id': f'h7-{sid}-differential-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of differential test report for {sname}.',
        'depends_on': [f'h7-{sid}-differential'],
        'function_claims': fclaim,
        'read_paths': [diff_doc],
        'write_paths': [diff_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm boundary coverage, register comparisons, and negative control verification.'],
        'validation_plan': ['Audit report.json generated by offline runner.']
    })

    # Composition
    tasks.append({
        'id': f'h7-{sid}-composition',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Validate caller composition and ABI integration for {sname}.',
        'depends_on': [f'h7-{sid}-differential-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [comp_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [f'Verify {sname} callers preserve register invariants and memory bounds.'],
        'validation_plan': ['Audit callers and stack layout compatibility.']
    })

    # Composition Review
    tasks.append({
        'id': f'h7-{sid}-composition-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of caller composition for {sname}.',
        'depends_on': [f'h7-{sid}-composition'],
        'function_claims': fclaim,
        'read_paths': [comp_doc],
        'write_paths': [comp_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm calling conventions, argument passing, and stack teardown.'],
        'validation_plan': ['Verify absence of stack corruption or clobbered caller-saved registers.']
    })

    # Staging
    tasks.append({
        'id': f'h7-{sid}-staging',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Verify binary staging and relocation patching for {sname}.',
        'depends_on': [f'h7-{sid}-composition-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [stag_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [f'Ensure patched candidate {sname} integrates cleanly into binary layout.'],
        'validation_plan': ['Verify relocation targets and binary window padding.']
    })

    # Staging Review
    tasks.append({
        'id': f'h7-{sid}-staging-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of binary staging for {sname}.',
        'depends_on': [f'h7-{sid}-staging'],
        'function_claims': fclaim,
        'read_paths': [stag_doc],
        'write_paths': [stag_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify binary window margin and IPS patch offset integrity.'],
        'validation_plan': ['Cross-check ELF symbol map with target VMA.']
    })

# Staged Image Patch
tasks.append({
    'id': 'h7-staged-image-patch',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 validated H7 candidate replacements into unified executable and produce code.h7-final.ips.',
    'depends_on': [f'h7-{s["id"]}-staging-review' for s in subsystems],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [s['cand_src'] for s in subsystems] + ['tools/h7_staged_image_patch.py'],
    'write_paths': ['docs/agent-work/h7-staged-image-patch.md', 'code.h7-final.ips'],
    'compiler_slots': 1,
    'exclusive_resources': ['staged_binary'],
    'acceptance': [
        'Produce code.h7-final.bin and code.h7-final.ips over H6 baseline.',
        'Zero overflow across all 8 function windows (+margins padded with NOP).',
        'Verify round-trip IPS patch identity.'
    ],
    'validation_plan': ['Run python tools/h7_staged_image_patch.py.']
})

tasks.append({
    'id': 'h7-staged-image-patch-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of composite image staging and IPS patch generation for Milestone H7.',
    'depends_on': ['h7-staged-image-patch'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h7-staged-image-patch.md'],
    'write_paths': ['docs/agent-work/h7-staged-image-patch-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Validate SHA-256 hashes, patch size, and byte-replacement boundaries.'],
    'validation_plan': ['Audit staging manifest and IPS patch offsets.']
})

# Offline Composite Gates
tasks.append({
    'id': 'h7-offline-composite-gates',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Run comprehensive offline composite gate validation across all 8 subsystems.',
    'depends_on': ['h7-staged-image-patch-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h7-staged-image-patch.md'],
    'write_paths': ['docs/agent-work/h7-offline-composite-gates.md'],
    'compiler_slots': 1,
    'exclusive_resources': [],
    'acceptance': [
        'Confirm interworking ARM/Thumb bits for all call sites.',
        'Confirm all 8 offline differential tests pass synchronously.'
    ],
    'validation_plan': ['Execute offline validation test suite.']
})

tasks.append({
    'id': 'h7-offline-composite-gates-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of offline composite gate test results.',
    'depends_on': ['h7-offline-composite-gates'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h7-offline-composite-gates.md'],
    'write_paths': ['docs/agent-work/h7-offline-composite-gates-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Verify offline gate pass certificates.'],
    'validation_plan': ['Audit gate execution log.']
})

# Autonomous Runtime Verification
tasks.append({
    'id': 'h7-autonomous-script-verify',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Autonomous runtime verification in Azahar emulator: Title, Save Load, Field, and Script VM sequences.',
    'depends_on': ['h7-offline-composite-gates-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['tools/h3_autonomous_verify.py', 'code.h7-final.ips'],
    'write_paths': ['docs/agent-work/h7-autonomous-script-verify.md'],
    'compiler_slots': 0,
    'exclusive_resources': ['emulator_session'],
    'acceptance': [
        'Run paired autonomous test via GDB RSP loopback stub.',
        '0 register differences across Title, Save Load, 250 Field scene ticks, and dialogue/event script VM dispatch.'
    ],
    'validation_plan': ['Execute autonomous verify script and generate paired report.json.']
})

tasks.append({
    'id': 'h7-autonomous-script-verify-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of autonomous paired runtime verification for Milestone H7.',
    'depends_on': ['h7-autonomous-script-verify'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h7-autonomous-script-verify.md'],
    'write_paths': ['docs/agent-work/h7-autonomous-script-verify-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm 100% paired equivalence with zero register or state differences.'],
    'validation_plan': ['Audit runtime report metrics and save file hash integrity.']
})

tasks.append({
    'id': 'h7-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Formalize closure of Milestone H7 across documentation and ledger tracking.',
    'depends_on': ['h7-autonomous-script-verify-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/milestones/H7-event-script-vm.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'write_paths': ['docs/milestones/H7-event-script-vm.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Update documentation marking Milestone H7 as completed and closed.',
        'Ensure clean git state and 0 errors from tools/agent_workflow.py check.'
    ],
    'validation_plan': ['Run python tools/agent_workflow.py check.']
})

board = {
    'schema_version': 1,
    'batch': 'batch-h7-001',
    'milestone': 'H7',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H7 (Script VM and Event Runtime), covering dialogue window lifecycle and slot reset (ComWin, InfoWin, GuestWin), FlowScript character naming and barracks event runner (nameMain, onesRoom), and event command screen fades and visual effect presentation (eventCommand_func_0025955c, EventEffect_func_0030a4fc) with full offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h7.json',
        'config/reconstruction.json',
        'docs/milestones/H7-event-script-vm.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_path = ROOT / 'config/agent-workflows/h7.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(board, f, indent=2)

print(f'Successfully wrote h7.json with {len(tasks)} tasks to {out_path}')
