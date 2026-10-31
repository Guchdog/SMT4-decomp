#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h8.json for Milestone H8."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'camp-gauntletmenu-init',
        'func': '0x002e2454',
        'name': 'GauntletAppMenu_Init',
        'desc': 'Gauntlet application menu initialization, script/mbm resource loading, and sub-tasks registration',
        'cand_src': 'experiments/semantic_equivalence/h8_camp_gauntletmenu_init_candidate.cpp',
        'test_src': 'tools/h8_camp_gauntletmenu_init_experiment.py',
        'contract_doc': 'docs/agent-work/h8-camp-gauntletmenu-init-contract.md',
        'cand_doc': 'docs/agent-work/h8-camp-gauntletmenu-init-candidate.md',
    },
    {
        'id': 'ui-status-bustup',
        'func': '0x00223a90',
        'name': 'StatusBustUp_Init',
        'desc': 'Status character/demon bust-up portrait visual renderer setup and buffer registration',
        'cand_src': 'experiments/semantic_equivalence/h8_ui_status_bustup_candidate.cpp',
        'test_src': 'tools/h8_ui_status_bustup_experiment.py',
        'contract_doc': 'docs/agent-work/h8-ui-status-bustup-contract.md',
        'cand_doc': 'docs/agent-work/h8-ui-status-bustup-candidate.md',
    },
    {
        'id': 'ui-status-camera',
        'func': '0x00258e38',
        'name': 'StatusCamera_Init',
        'desc': 'Status 3D camera projection matrices, eye/target vectors, and viewport transform setup',
        'cand_src': 'experiments/semantic_equivalence/h8_ui_status_camera_candidate.cpp',
        'test_src': 'tools/h8_ui_status_camera_experiment.py',
        'contract_doc': 'docs/agent-work/h8-ui-status-camera-contract.md',
        'cand_doc': 'docs/agent-work/h8-ui-status-camera-candidate.md',
    },
    {
        'id': 'ui-status-affinity',
        'func': '0x00293e4c',
        'name': 'Status_UpdateAffinityTable',
        'desc': 'Elemental affinity and resistance evaluator table setting display mode across entity states',
        'cand_src': 'experiments/semantic_equivalence/h8_ui_status_affinity_candidate.cpp',
        'test_src': 'tools/h8_ui_status_affinity_experiment.py',
        'contract_doc': 'docs/agent-work/h8-ui-status-affinity-contract.md',
        'cand_doc': 'docs/agent-work/h8-ui-status-affinity-candidate.md',
    },
    {
        'id': 'ui-statusdown-init',
        'func': '0x002d931c',
        'name': 'StatusDown_Init',
        'desc': 'Touchscreen bottom-screen party/status interface workspace setup, TMD tasks, and sprite tables',
        'cand_src': 'experiments/semantic_equivalence/h8_ui_statusdown_init_candidate.cpp',
        'test_src': 'tools/h8_ui_statusdown_init_experiment.py',
        'contract_doc': 'docs/agent-work/h8-ui-statusdown-init-contract.md',
        'cand_doc': 'docs/agent-work/h8-ui-statusdown-init-candidate.md',
    },
    {
        'id': 'ui-statusdown-itemlist',
        'func': '0x001ee7c8',
        'name': 'StatusDown_PopulateItemList',
        'desc': 'Inventory item list population, usable item filter, pagination setup, and sorter dispatch',
        'cand_src': 'experiments/semantic_equivalence/h8_ui_statusdown_itemlist_candidate.cpp',
        'test_src': 'tools/h8_ui_statusdown_itemlist_experiment.py',
        'contract_doc': 'docs/agent-work/h8-ui-statusdown-itemlist-contract.md',
        'cand_doc': 'docs/agent-work/h8-ui-statusdown-itemlist-candidate.md',
    },
    {
        'id': 'ui-statusdown-itemsort',
        'func': '0x0032c4bc',
        'name': 'StatusDown_SortItemList',
        'desc': 'Inventory sorter dispatcher (ID, category, type, cost) using qsort with comparator callbacks',
        'cand_src': 'experiments/semantic_equivalence/h8_ui_statusdown_itemsort_candidate.cpp',
        'test_src': 'tools/h8_ui_statusdown_itemsort_experiment.py',
        'contract_doc': 'docs/agent-work/h8-ui-statusdown-itemsort-contract.md',
        'cand_doc': 'docs/agent-work/h8-ui-statusdown-itemsort-candidate.md',
    },
    {
        'id': 'ui-statusdown-skilllist',
        'func': '0x001ee5a4',
        'name': 'StatusDown_PopulateSkillList',
        'desc': 'Flynn and demon skill list builder, active bitfield evaluation, pagination, and skill sorter',
        'cand_src': 'experiments/semantic_equivalence/h8_ui_statusdown_skilllist_candidate.cpp',
        'test_src': 'tools/h8_ui_statusdown_skilllist_experiment.py',
        'contract_doc': 'docs/agent-work/h8-ui-statusdown-skilllist-contract.md',
        'cand_doc': 'docs/agent-work/h8-ui-statusdown-skilllist-candidate.md',
    },
]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h8-camp-status-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H8 Camp Menu, Inventory, and Party Management.',
    'depends_on': [],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'src/camp/camp.cpp',
        'src/camp/camp_main.cpp',
        'src/camp/camp_inventory.cpp',
        'src/camp/camp_party.cpp',
        'src/ui/status.cpp',
        'src/ui/status_down.cpp',
        'docs/reconstruction-milestones.md',
        'docs/milestones/H7-event-script-vm.md'
    ],
    'write_paths': [
        'docs/agent-work/h8-camp-status-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H8 camp menu, inventory, and status subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

tasks.append({
    'id': 'h8-camp-status-recon-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of camp menu, inventory, and party architecture reconnaissance and subsystem boundary definitions.',
    'depends_on': ['h8-camp-status-recon'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [
        'docs/agent-work/h8-camp-status-recon.md'
    ],
    'write_paths': [
        'docs/agent-work/h8-camp-status-recon-review.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify contract boundaries, calling conventions, and ABI preservation expectations.',
        'Approve task division and candidate scope for H8 camp menu and status management milestone.'
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
    diff_doc = f"docs/agent-work/h8-{sid}-differential.md"
    diff_review_doc = f"docs/agent-work/h8-{sid}-differential-review.md"
    comp_doc = f"docs/agent-work/h8-{sid}-composition.md"
    comp_review_doc = f"docs/agent-work/h8-{sid}-composition-review.md"
    stag_doc = f"docs/agent-work/h8-{sid}-staging.md"
    stag_review_doc = f"docs/agent-work/h8-{sid}-staging-review.md"

    # Contract
    tasks.append({
        'id': f'h8-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Formalize contract, parameters, registers, and memory effects for {sname} ({sfunc}).',
        'depends_on': ['h8-camp-status-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['src/camp/camp.cpp', 'src/ui/status.cpp', 'src/ui/status_down.cpp'],
        'write_paths': [s['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Accurately specify semantics of {sname}.', 'Specify test fixtures and mutation controls.'],
        'validation_plan': ['Static disassembly and register effect verification against code.bin.']
    })

    # Contract Review
    tasks.append({
        'id': f'h8-{sid}-contract-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of {sname} contract specification.',
        'depends_on': [f'h8-{sid}-contract'],
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
        'id': f'h8-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement readable, editable C++ candidate for {sname} with mutation control.',
        'depends_on': [f'h8-{sid}-contract-review'],
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
        'id': f'h8-{sid}-candidate-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent code review of C++ reconstruction for {sname}.',
        'depends_on': [f'h8-{sid}-candidate'],
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
        'id': f'h8-{sid}-differential',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Execute offline ARM Unicorn differential test cases for {sname}.',
        'depends_on': [f'h8-{sid}-candidate-review'],
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
        'id': f'h8-{sid}-differential-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of differential test report for {sname}.',
        'depends_on': [f'h8-{sid}-differential'],
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
        'id': f'h8-{sid}-composition',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Validate caller composition and ABI integration for {sname}.',
        'depends_on': [f'h8-{sid}-differential-review'],
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
        'id': f'h8-{sid}-composition-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of caller composition for {sname}.',
        'depends_on': [f'h8-{sid}-composition'],
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
        'id': f'h8-{sid}-staging',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Verify binary staging and relocation patching for {sname}.',
        'depends_on': [f'h8-{sid}-composition-review'],
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
        'id': f'h8-{sid}-staging-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of binary staging for {sname}.',
        'depends_on': [f'h8-{sid}-staging'],
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
    'id': 'h8-staged-image-patch',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 validated H8 candidate replacements into unified executable and produce code.h8-final.ips.',
    'depends_on': [f'h8-{s["id"]}-staging-review' for s in subsystems],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': [s['cand_src'] for s in subsystems] + ['tools/h8_staged_image_patch.py'],
    'write_paths': ['docs/agent-work/h8-staged-image-patch.md', 'code.h8-final.ips'],
    'compiler_slots': 1,
    'exclusive_resources': ['staged_binary'],
    'acceptance': [
        'Produce code.h8-final.bin and code.h8-final.ips over H7 baseline.',
        'Zero overflow across all 8 function windows (+margins padded with NOP).',
        'Verify round-trip IPS patch identity.'
    ],
    'validation_plan': ['Run python tools/h8_staged_image_patch.py.']
})

tasks.append({
    'id': 'h8-staged-image-patch-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of composite image staging and IPS patch generation for Milestone H8.',
    'depends_on': ['h8-staged-image-patch'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h8-staged-image-patch.md'],
    'write_paths': ['docs/agent-work/h8-staged-image-patch-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Validate SHA-256 hashes, patch size, and byte-replacement boundaries.'],
    'validation_plan': ['Audit staging manifest and IPS patch offsets.']
})

# Offline Composite Gates
tasks.append({
    'id': 'h8-offline-composite-gates',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Run comprehensive offline composite gate validation across all 8 subsystems.',
    'depends_on': ['h8-staged-image-patch-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h8-staged-image-patch.md'],
    'write_paths': ['docs/agent-work/h8-offline-composite-gates.md'],
    'compiler_slots': 1,
    'exclusive_resources': [],
    'acceptance': [
        'Confirm interworking ARM/Thumb bits for all call sites.',
        'Confirm all 8 offline differential tests pass synchronously.'
    ],
    'validation_plan': ['Execute offline validation test suite.']
})

tasks.append({
    'id': 'h8-offline-composite-gates-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of offline composite gate test results.',
    'depends_on': ['h8-offline-composite-gates'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h8-offline-composite-gates.md'],
    'write_paths': ['docs/agent-work/h8-offline-composite-gates-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Verify offline gate pass certificates.'],
    'validation_plan': ['Audit gate execution log.']
})

# Autonomous Runtime Verification
tasks.append({
    'id': 'h8-autonomous-camp-verify',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Autonomous runtime verification in Azahar emulator: Title, Save Load, Field, Camp Menu, and Status sequences.',
    'depends_on': ['h8-offline-composite-gates-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['tools/h3_autonomous_verify.py', 'code.h8-final.ips'],
    'write_paths': ['docs/agent-work/h8-autonomous-camp-verify.md'],
    'compiler_slots': 0,
    'exclusive_resources': ['emulator_session'],
    'acceptance': [
        'Run paired autonomous test via GDB RSP loopback stub.',
        '0 register differences across Title, Save Load, 250 Field scene ticks, Camp application menu, and Status down screens.'
    ],
    'validation_plan': ['Execute autonomous verify script and generate paired report.json.']
})

tasks.append({
    'id': 'h8-autonomous-camp-verify-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of autonomous paired runtime verification for Milestone H8.',
    'depends_on': ['h8-autonomous-camp-verify'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/agent-work/h8-autonomous-camp-verify.md'],
    'write_paths': ['docs/agent-work/h8-autonomous-camp-verify-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm 100% paired equivalence with zero register or state differences.'],
    'validation_plan': ['Audit runtime report metrics and save file hash integrity.']
})

tasks.append({
    'id': 'h8-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Formalize closure of Milestone H8 across documentation and ledger tracking.',
    'depends_on': ['h8-autonomous-camp-verify-review'],
    'function_claims': [s['func'] for s in subsystems],
    'read_paths': ['docs/milestones/H8-camp-menu-inventory-party.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'write_paths': ['docs/milestones/H8-camp-menu-inventory-party.md', 'docs/functional-status.md', 'docs/reconstruction-milestones.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Update documentation marking Milestone H8 as completed and closed.',
        'Ensure clean git state and 0 errors from tools/agent_workflow.py check.'
    ],
    'validation_plan': ['Run python tools/agent_workflow.py check.']
})

board = {
    'schema_version': 1,
    'batch': 'batch-h8-001',
    'milestone': 'H8',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H8 (Camp Menu, Inventory, and Party Management), covering Gauntlet/Burroughs app menu initialization (GauntletAppMenu_Init), status portrait bust-up rendering (StatusBustUp_Init), status 3D camera projection (StatusCamera_Init), elemental affinity resistance table evaluation (Status_UpdateAffinityTable), and touchscreen bottom-screen party/status workspace, item list population, inventory sorting, and skill list building (StatusDown_Init, StatusDown_PopulateItemList, StatusDown_SortItemList, StatusDown_PopulateSkillList) with full offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h8.json',
        'config/reconstruction.json',
        'docs/milestones/H8-camp-menu-inventory-party.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_path = ROOT / 'config/agent-workflows/h8.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(board, f, indent=2)

print(f'Successfully wrote h8.json with {len(tasks)} tasks to {out_path}')
