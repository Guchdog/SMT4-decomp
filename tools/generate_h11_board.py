#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h11.json for Milestone H11."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'shop-setselecteditem',
        'func': '0x0022a60c',
        'name': 'Shop_SetSelectedItem',
        'desc': 'Shop inventory item selection state and dirty flag update',
        'cand_src': 'experiments/semantic_equivalence/h11_shop_setselecteditem_candidate.cpp',
        'test_src': 'tools/h11_shop_setselecteditem_experiment.py',
        'contract_doc': 'docs/agent-work/h11-shop-setselecteditem-contract.md',
        'cand_doc': 'docs/agent-work/h11-shop-setselecteditem-candidate.md',
    },
    {
        'id': 'shop-checkhasnew',
        'func': '0x0022fc98',
        'name': 'Shop_CheckHasNewInventoryItem',
        'desc': 'Shop inventory new item arrival and category badge check',
        'cand_src': 'experiments/semantic_equivalence/h11_shop_checkhasnew_candidate.cpp',
        'test_src': 'tools/h11_shop_checkhasnew_experiment.py',
        'contract_doc': 'docs/agent-work/h11-shop-checkhasnew-contract.md',
        'cand_doc': 'docs/agent-work/h11-shop-checkhasnew-candidate.md',
    },
    {
        'id': 'shop-checkhasspecial',
        'func': '0x0022fcc8',
        'name': 'Shop_CheckHasSpecialStockItem',
        'desc': 'Black market and specialty shop exclusive stock availability check',
        'cand_src': 'experiments/semantic_equivalence/h11_shop_checkhasspecial_candidate.cpp',
        'test_src': 'tools/h11_shop_checkhasspecial_experiment.py',
        'contract_doc': 'docs/agent-work/h11-shop-checkhasspecial-contract.md',
        'cand_doc': 'docs/agent-work/h11-shop-checkhasspecial-candidate.md',
    },
    {
        'id': 'shop-pushitemrecord',
        'func': '0x00230680',
        'name': 'Shop_PushItemRecord',
        'desc': 'Shop catalog entry push and bitfield flag packing into active display buffer',
        'cand_src': 'experiments/semantic_equivalence/h11_shop_pushitemrecord_candidate.cpp',
        'test_src': 'tools/h11_shop_pushitemrecord_experiment.py',
        'contract_doc': 'docs/agent-work/h11-shop-pushitemrecord-contract.md',
        'cand_doc': 'docs/agent-work/h11-shop-pushitemrecord-candidate.md',
    },
    {
        'id': 'shop-isequipslotmatch',
        'func': '0x00230d24',
        'name': 'Shop_IsEquipSlotMatch',
        'desc': 'Party unit equipment category slot matching and compatibility verification',
        'cand_src': 'experiments/semantic_equivalence/h11_shop_isequipslotmatch_candidate.cpp',
        'test_src': 'tools/h11_shop_isequipslotmatch_experiment.py',
        'contract_doc': 'docs/agent-work/h11-shop-isequipslotmatch-contract.md',
        'cand_doc': 'docs/agent-work/h11-shop-isequipslotmatch-candidate.md',
    },
    {
        'id': 'shop-calcpurchasableqty',
        'func': '0x00230db0',
        'name': 'Shop_CalcPurchasableQty',
        'desc': 'Shop inventory item purchase quantity limit clamped against bag capacity',
        'cand_src': 'experiments/semantic_equivalence/h11_shop_calcpurchasableqty_candidate.cpp',
        'test_src': 'tools/h11_shop_calcpurchasableqty_experiment.py',
        'contract_doc': 'docs/agent-work/h11-shop-calcpurchasableqty-contract.md',
        'cand_doc': 'docs/agent-work/h11-shop-calcpurchasableqty-candidate.md',
    },
    {
        'id': 'terminal-setunlockflag',
        'func': '0x00263734',
        'name': 'Terminal_SetUnlockFlag',
        'desc': 'Terminal network teleport unlock bitfield registration and status persistence',
        'cand_src': 'experiments/semantic_equivalence/h11_terminal_setunlockflag_candidate.cpp',
        'test_src': 'tools/h11_terminal_setunlockflag_experiment.py',
        'contract_doc': 'docs/agent-work/h11-terminal-setunlockflag-contract.md',
        'cand_doc': 'docs/agent-work/h11-terminal-setunlockflag-candidate.md',
    },
    {
        'id': 'terminal-isunlocked',
        'func': '0x00263778',
        'name': 'Terminal_IsUnlocked',
        'desc': 'Terminal network teleport destination query across 32-node bitset',
        'cand_src': 'experiments/semantic_equivalence/h11_terminal_isunlocked_candidate.cpp',
        'test_src': 'tools/h11_terminal_isunlocked_experiment.py',
        'contract_doc': 'docs/agent-work/h11-terminal-isunlocked-contract.md',
        'cand_doc': 'docs/agent-work/h11-terminal-isunlocked-candidate.md',
    },
]

all_funcs = [s['func'] for s in subsystems]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h11-shops-blackmarket-terminals-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H11 Shops, Black Market, and Terminals.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': [
        'src/shop/shop_runtime.cpp',
        'docs/reconstruction-milestones.md',
        'docs/milestones/H10-burroughs-quests-apps.md',
    ],
    'write_paths': [
        'docs/agent-work/h11-shops-blackmarket-terminals-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H11 Shops, Black Market, and Terminal subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

# Task 2: Architecture Recon Review
tasks.append({
    'id': 'h11-shops-blackmarket-terminals-recon-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of Shops, Black Market, and Terminals architecture reconnaissance and boundary definitions.',
    'depends_on': ['h11-shops-blackmarket-terminals-recon'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h11-shops-blackmarket-terminals-recon.md'],
    'write_paths': ['docs/agent-work/h11-shops-blackmarket-terminals-recon-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify contract boundaries, calling conventions, and ABI preservation expectations.',
        'Approve task division and candidate scope for H11 Shops, Black Market, and Terminals milestone.'
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
    diff_doc = f"docs/agent-work/h11-{sid}-differential.md"
    diff_review_doc = f"docs/agent-work/h11-{sid}-differential-review.md"
    comp_doc = f"docs/agent-work/h11-{sid}-composition.md"
    comp_review_doc = f"docs/agent-work/h11-{sid}-composition-review.md"
    stag_doc = f"docs/agent-work/h11-{sid}-staging.md"
    stag_review_doc = f"docs/agent-work/h11-{sid}-staging-review.md"

    # Contract
    tasks.append({
        'id': f'h11-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Formalize contract, parameters, registers, and memory effects for {sname} ({sfunc}).',
        'depends_on': ['h11-shops-blackmarket-terminals-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['src/shop/shop_runtime.cpp'],
        'write_paths': [s['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Accurately specify semantics of {sname}.', 'Specify test fixtures and mutation controls.'],
        'validation_plan': ['Static disassembly and register effect verification against code.bin.']
    })

    # Contract Review
    tasks.append({
        'id': f'h11-{sid}-contract-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of semantic contract for {sname} ({sfunc}).',
        'depends_on': [f'h11-{sid}-contract'],
        'function_claims': fclaim,
        'read_paths': [s['contract_doc']],
        'write_paths': [c_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve pre/post conditions and side effects.'],
        'validation_plan': ['Independent verification against disassembly.']
    })

    # Implementation
    tasks.append({
        'id': f'h11-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement readable, editable C++ for {sname} ({sfunc}) with positive headroom margin.',
        'depends_on': [f'h11-{sid}-contract-review'],
        'function_claims': fclaim,
        'read_paths': [s['contract_doc']],
        'write_paths': [s['cand_src'], s['cand_doc']],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': ['Compile freestanding ARMv6K object.', 'Size within original window.', 'Headroom positive.'],
        'validation_plan': [f'Compile with clang++ and inspect size and relocations.']
    })

    # Implementation Review
    tasks.append({
        'id': f'h11-{sid}-candidate-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of C++ implementation for {sname} ({sfunc}).',
        'depends_on': [f'h11-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['cand_doc']],
        'write_paths': [cand_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify readable C++ structure.', 'Confirm no undefined behavior.'],
        'validation_plan': ['Static analysis and code inspection.']
    })

    # Differential Validation
    tasks.append({
        'id': f'h11-{sid}-differential',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Offline ARM Unicorn differential testing of {sname} against pinned code.bin.',
        'depends_on': [f'h11-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['test_src']],
        'write_paths': [diff_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Zero register and memory diffs against original implementation.', 'Mutation sensitivity confirmed.'],
        'validation_plan': [f'Run {s["test_src"]}.']
    })

    # Differential Review
    tasks.append({
        'id': f'h11-{sid}-differential-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of differential test results for {sname}.',
        'depends_on': [f'h11-{sid}-differential'],
        'function_claims': fclaim,
        'read_paths': [diff_doc],
        'write_paths': [diff_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve test coverage and mutation sensitivity evidence.'],
        'validation_plan': ['Audit execution logs and mutation outputs.']
    })

    # Caller Composition
    tasks.append({
        'id': f'h11-{sid}-composition',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Validate caller composition and ABI compatibility for {sname}.',
        'depends_on': [f'h11-{sid}-differential-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [comp_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify register conventions and caller expectations.'],
        'validation_plan': ['Composition analysis against calling functions.']
    })

    # Caller Composition Review
    tasks.append({
        'id': f'h11-{sid}-composition-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of caller composition for {sname}.',
        'depends_on': [f'h11-{sid}-composition'],
        'function_claims': fclaim,
        'read_paths': [comp_doc],
        'write_paths': [comp_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve caller composition and interworking proof.'],
        'validation_plan': ['Audit caller composition report.']
    })

    # Staging
    tasks.append({
        'id': f'h11-{sid}-staging',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Stage candidate binary for {sname} into H11 composite build.',
        'depends_on': [f'h11-{sid}-composition-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [stag_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Generate binary patch.', 'Integrate into composite stage.'],
        'validation_plan': ['Verify patch size matches window exactly.']
    })

    # Staging Review
    tasks.append({
        'id': f'h11-{sid}-staging-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of staged candidate for {sname}.',
        'depends_on': [f'h11-{sid}-staging'],
        'function_claims': fclaim,
        'read_paths': [stag_doc],
        'write_paths': [stag_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Approve integration patch and hash validation.'],
        'validation_plan': ['Audit binary diff against window.']
    })

# Whole Milestone Integration Gates
tasks.append({
    'id': 'h11-staged-image-patch',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 H11 semantic candidates over H10 final image and generate LayeredFS IPS mod.',
    'depends_on': [f"h11-{s['id']}-staging-review" for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': ['tools/h11_staged_image_patch.py', 'code.h10-final.bin'],
    'write_paths': [
        'build/agent-work/H11-semantic/h11-integrated-stage/code.h11-final.bin',
        'build/agent-work/H11-semantic/h11-integrated-stage/code.h11-final.ips',
        'docs/agent-work/h11-staged-image-patch.md'
    ],
    'compiler_slots': 1,
    'exclusive_resources': ['staged_image'],
    'acceptance': [
        'Build code.h11-final.bin with all 8 candidates integrated.',
        'Generate and verify code.h11-final.ips against original binary with round-trip proof.'
    ],
    'validation_plan': ['Run python tools/h11_staged_image_patch.py.']
})

tasks.append({
    'id': 'h11-staged-image-patch-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H11 composite staged image and LayeredFS IPS patch.',
    'depends_on': ['h11-staged-image-patch'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h11-staged-image-patch.md'],
    'write_paths': ['docs/agent-work/h11-staged-image-patch-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Verify SHA-256 integrity and IPS round-trip fidelity.'],
    'validation_plan': ['Audit manifest hashes and IPS validation output.']
})

tasks.append({
    'id': 'h11-offline-composite-gates',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Execute combined offline differential and caller composition suite for all 8 candidates.',
    'depends_on': ['h11-staged-image-patch-review'],
    'function_claims': all_funcs,
    'read_paths': ['tools/build_h11_all.py', 'tools/generate_h11_experiments.py'],
    'write_paths': ['docs/agent-work/h11-offline-composite-gates.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        '100% pass across all 8 Unicorn differential validations.',
        'Zero regressions across combined candidate assembly and ARM/Thumb interworking bits.'
    ],
    'validation_plan': ['Run tools/build_h11_all.py and all 8 experiment scripts.']
})

tasks.append({
    'id': 'h11-offline-composite-gates-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of offline composite gates and interworking integrity.',
    'depends_on': ['h11-offline-composite-gates'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h11-offline-composite-gates.md'],
    'write_paths': ['docs/agent-work/h11-offline-composite-gates-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Approve offline test results prior to emulator runtime verification.'],
    'validation_plan': ['Audit gate execution outputs and mutation sensitivity logs.']
})

tasks.append({
    'id': 'h11-autonomous-shops-terminals-verify',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Autonomous runtime verification in Azahar emulator: Title, Save Load, Field, and Shops / Black Market / Terminals sequences.',
    'depends_on': ['h11-offline-composite-gates-review'],
    'function_claims': all_funcs,
    'read_paths': ['tools/h3_autonomous_verify.py', 'code.h11-final.ips'],
    'write_paths': ['docs/agent-work/h11-autonomous-shops-terminals-verify.md'],
    'compiler_slots': 0,
    'exclusive_resources': ['emulator_session'],
    'acceptance': [
        'Run paired autonomous test via GDB RSP loopback stub.',
        '0 register differences across Title, Save Load, 250 Field scene ticks, and Shops / Black Market / Terminals subsystems.'
    ],
    'validation_plan': ['Execute autonomous verify script and generate paired report.json.']
})

tasks.append({
    'id': 'h11-autonomous-shops-terminals-verify-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of autonomous paired runtime verification for Milestone H11.',
    'depends_on': ['h11-autonomous-shops-terminals-verify'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h11-autonomous-shops-terminals-verify.md'],
    'write_paths': ['docs/agent-work/h11-autonomous-shops-terminals-verify-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm 100% paired equivalence with zero register or state differences.'],
    'validation_plan': ['Audit runtime report metrics and save file hash integrity.']
})

# Milestone Closure
tasks.append({
    'id': 'h11-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Formalize closure of Milestone H11 across documentation and ledger tracking.',
    'depends_on': ['h11-autonomous-shops-terminals-verify-review'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/milestones/H11-shops-blackmarket-terminals.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'write_paths': [
        'docs/milestones/H11-shops-blackmarket-terminals.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Update documentation marking Milestone H11 as completed and closed.',
        'Ensure clean git state and 0 errors from tools/agent_workflow.py check.'
    ],
    'validation_plan': ['Run python tools/agent_workflow.py check.']
})

board = {
    'schema_version': 1,
    'batch': 'batch-h11-001',
    'milestone': 'H11',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H11 (Shops, Black Market, and Terminals), covering Shop item selection state and dirty flags (Shop_SetSelectedItem), shop inventory new item check (Shop_CheckHasNewInventoryItem), black market special stock query (Shop_CheckHasSpecialStockItem), catalog entry record packing into display buffers (Shop_PushItemRecord), unit equipment slot validation (Shop_IsEquipSlotMatch), purchase quantity calculation clamped against bag capacity (Shop_CalcPurchasableQty), terminal network unlock bitfield registration (Terminal_SetUnlockFlag), and terminal unlock query across 32-node bitset (Terminal_IsUnlocked) with full offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h11.json',
        'config/reconstruction.json',
        'docs/milestones/H11-shops-blackmarket-terminals.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_path = ROOT / 'config/agent-workflows/h11.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(board, f, indent=2)

print(f"Generated {out_path} with {len(tasks)} tasks.")
