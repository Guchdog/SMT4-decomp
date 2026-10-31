#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h10.json for Milestone H10."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'camp-burroughs-getsavedata',
        'func': '0x002a0fac',
        'name': 'Burroughs_GetSaveData',
        'desc': 'Burroughs and Quest save data pointer resolution from main game work',
        'cand_src': 'experiments/semantic_equivalence/h10_camp_burroughs_getsavedata_candidate.cpp',
        'test_src': 'tools/h10_camp_burroughs_getsavedata_experiment.py',
        'contract_doc': 'docs/agent-work/h10-camp-burroughs-getsavedata-contract.md',
        'cand_doc': 'docs/agent-work/h10-camp-burroughs-getsavedata-candidate.md',
    },
    {
        'id': 'camp-burroughs-appdispatch',
        'func': '0x002a0ea8',
        'name': 'Burroughs_AppDispatch',
        'desc': 'Burroughs application selection dispatcher and audio cue trigger',
        'cand_src': 'experiments/semantic_equivalence/h10_camp_burroughs_appdispatch_candidate.cpp',
        'test_src': 'tools/h10_camp_burroughs_appdispatch_experiment.py',
        'contract_doc': 'docs/agent-work/h10-camp-burroughs-appdispatch-contract.md',
        'cand_doc': 'docs/agent-work/h10-camp-burroughs-appdispatch-candidate.md',
    },
    {
        'id': 'camp-quest-resetselection',
        'func': '0x0026a004',
        'name': 'Quest_ResetSelection',
        'desc': 'Quest list selection reset, category flag set, and row counter zeroing',
        'cand_src': 'experiments/semantic_equivalence/h10_camp_quest_resetselection_candidate.cpp',
        'test_src': 'tools/h10_camp_quest_resetselection_experiment.py',
        'contract_doc': 'docs/agent-work/h10-camp-quest-resetselection-contract.md',
        'cand_doc': 'docs/agent-work/h10-camp-quest-resetselection-candidate.md',
    },
    {
        'id': 'camp-quest-evaltarget',
        'func': '0x0026a86c',
        'name': 'Quest_EvaluateTargetCondition',
        'desc': 'Quest objective target condition evaluation and flag matching',
        'cand_src': 'experiments/semantic_equivalence/h10_camp_quest_evaltarget_candidate.cpp',
        'test_src': 'tools/h10_camp_quest_evaltarget_experiment.py',
        'contract_doc': 'docs/agent-work/h10-camp-quest-evaltarget-contract.md',
        'cand_doc': 'docs/agent-work/h10-camp-quest-evaltarget-candidate.md',
    },
    {
        'id': 'camp-quest-getavailability',
        'func': '0x0026a9fc',
        'name': 'Quest_GetAvailability',
        'desc': 'Quest availability checking for main and challenge quests',
        'cand_src': 'experiments/semantic_equivalence/h10_camp_quest_getavailability_candidate.cpp',
        'test_src': 'tools/h10_camp_quest_getavailability_experiment.py',
        'contract_doc': 'docs/agent-work/h10-camp-quest-getavailability-contract.md',
        'cand_doc': 'docs/agent-work/h10-camp-quest-getavailability-candidate.md',
    },
    {
        'id': 'camp-quest-unpackentry',
        'func': '0x0026aac0',
        'name': 'Quest_UnpackEntryData',
        'desc': 'Quest static definition unpack into dynamic UI buffers and formatted strings',
        'cand_src': 'experiments/semantic_equivalence/h10_camp_quest_unpackentry_candidate.cpp',
        'test_src': 'tools/h10_camp_quest_unpackentry_experiment.py',
        'contract_doc': 'docs/agent-work/h10-camp-quest-unpackentry-contract.md',
        'cand_doc': 'docs/agent-work/h10-camp-quest-unpackentry-candidate.md',
    },
    {
        'id': 'camp-appstore-setflag',
        'func': '0x003253d8',
        'name': 'AppStore_SetFlag',
        'desc': 'Burroughs Demonica App Store purchase flag registration and status bit update',
        'cand_src': 'experiments/semantic_equivalence/h10_camp_appstore_setflag_candidate.cpp',
        'test_src': 'tools/h10_camp_appstore_setflag_experiment.py',
        'contract_doc': 'docs/agent-work/h10-camp-appstore-setflag-contract.md',
        'cand_doc': 'docs/agent-work/h10-camp-appstore-setflag-candidate.md',
    },
    {
        'id': 'camp-appstore-getappparam',
        'func': '0x00325444',
        'name': 'AppStore_GetAppParam',
        'desc': 'Burroughs Demonica App Store parameter query and string formatting',
        'cand_src': 'experiments/semantic_equivalence/h10_camp_appstore_getappparam_candidate.cpp',
        'test_src': 'tools/h10_camp_appstore_getappparam_experiment.py',
        'contract_doc': 'docs/agent-work/h10-camp-appstore-getappparam-contract.md',
        'cand_doc': 'docs/agent-work/h10-camp-appstore-getappparam-candidate.md',
    },
]

all_funcs = [s['func'] for s in subsystems]

tasks = []

# Task 1: Architecture Reconnaissance
tasks.append({
    'id': 'h10-burroughs-quests-apps-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Comprehensive static and architectural reconnaissance of Milestone H10 Burroughs, Quests, and Apps.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': [
        'src/camp/quest_ui.cpp',
        'src/camp/app_store.cpp',
        'src/camp/camp_archive.cpp',
        'docs/reconstruction-milestones.md',
        'docs/milestones/H9-cathedral-fusion-compendium.md',
    ],
    'write_paths': [
        'docs/agent-work/h10-burroughs-quests-apps-recon.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Identify exact entry points, memory structures, and callers for H10 Burroughs, Quest, and App Store subsystems.',
        'Define offline-first differential boundaries, positive/negative controls, and mutation criteria.'
    ],
    'validation_plan': [
        'Cross-check candidate functions against pinned binary code.bin and functions.csv ledger.'
    ]
})

# Task 2: Architecture Recon Review
tasks.append({
    'id': 'h10-burroughs-quests-apps-recon-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of Burroughs, Quests, and Apps architecture reconnaissance and boundary definitions.',
    'depends_on': ['h10-burroughs-quests-apps-recon'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h10-burroughs-quests-apps-recon.md'],
    'write_paths': ['docs/agent-work/h10-burroughs-quests-apps-recon-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Verify contract boundaries, calling conventions, and ABI preservation expectations.',
        'Approve task division and candidate scope for H10 Burroughs, Quests, and Apps milestone.'
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
    diff_doc = f"docs/agent-work/h10-{sid}-differential.md"
    diff_review_doc = f"docs/agent-work/h10-{sid}-differential-review.md"
    comp_doc = f"docs/agent-work/h10-{sid}-composition.md"
    comp_review_doc = f"docs/agent-work/h10-{sid}-composition-review.md"
    stag_doc = f"docs/agent-work/h10-{sid}-staging.md"
    stag_review_doc = f"docs/agent-work/h10-{sid}-staging-review.md"

    # Contract
    tasks.append({
        'id': f'h10-{sid}-contract',
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Formalize contract, parameters, registers, and memory effects for {sname} ({sfunc}).',
        'depends_on': ['h10-burroughs-quests-apps-recon-review'],
        'function_claims': fclaim,
        'read_paths': ['src/camp/quest_ui.cpp', 'src/camp/app_store.cpp', 'src/camp/camp_archive.cpp'],
        'write_paths': [s['contract_doc']],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Accurately specify semantics of {sname}.', 'Specify test fixtures and mutation controls.'],
        'validation_plan': ['Static disassembly and register effect verification against code.bin.']
    })

    # Contract Review
    tasks.append({
        'id': f'h10-{sid}-contract-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of {sname} contract specification.',
        'depends_on': [f'h10-{sid}-contract'],
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
        'id': f'h10-{sid}-candidate',
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement readable, editable C++ candidate for {sname} with mutation control.',
        'depends_on': [f'h10-{sid}-contract-review'],
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
        'id': f'h10-{sid}-candidate-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of {sname} candidate implementation.',
        'depends_on': [f'h10-{sid}-candidate'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['cand_doc']],
        'write_paths': [cand_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [
            'Audit C++ syntax, memory safety, ABI conformance, and headroom margin.',
            'Verify mutation control triggers distinct divergence.'
        ],
        'validation_plan': ['Check ELF symbol tables and relocation bindings.']
    })

    # Differential
    tasks.append({
        'id': f'h10-{sid}-differential',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Execute offline Unicorn differential test for {sname} against original ARM code.',
        'depends_on': [f'h10-{sid}-candidate-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src'], s['test_src']],
        'write_paths': [diff_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            f'Pass Unicorn emulation comparing original {sname} against candidate.',
            'Confirm mutation control is detected with non-zero divergence.'
        ],
        'validation_plan': [f'Execute python {s["test_src"]}.']
    })

    # Differential Review
    tasks.append({
        'id': f'h10-{sid}-differential-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of offline differential test results for {sname}.',
        'depends_on': [f'h10-{sid}-differential'],
        'function_claims': fclaim,
        'read_paths': [diff_doc],
        'write_paths': [diff_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Confirm zero divergence in state effects between original and candidate.'],
        'validation_plan': ['Audit differential execution logs and register dump hashes.']
    })

    # Composition
    tasks.append({
        'id': f'h10-{sid}-composition',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Verify caller composition and interworking for {sname} in integrated context.',
        'depends_on': [f'h10-{sid}-differential-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [comp_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [
            f'Verify caller interface and stack alignment for {sname}.',
            'Ensure all external calls resolve cleanly without ABI violations.'
        ],
        'validation_plan': ['Audit caller sequence and callee stack frame preservation.']
    })

    # Composition Review
    tasks.append({
        'id': f'h10-{sid}-composition-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of caller composition for {sname}.',
        'depends_on': [f'h10-{sid}-composition'],
        'function_claims': fclaim,
        'read_paths': [comp_doc],
        'write_paths': [comp_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Validate absence of stack corruption or register clobbering across callers.'],
        'validation_plan': ['Review composition verification reports.']
    })

    # Staging
    tasks.append({
        'id': f'h10-{sid}-staging',
        'role': 'integration',
        'state': 'accepted',
        'owner': None,
        'goal': f'Stage candidate object and relocation records for {sname} into composite image builder.',
        'depends_on': [f'h10-{sid}-composition-review'],
        'function_claims': fclaim,
        'read_paths': [s['cand_src']],
        'write_paths': [stag_doc],
        'compiler_slots': 1,
        'exclusive_resources': [],
        'acceptance': [f'Successfully link and stage {sname} into staging pipeline.'],
        'validation_plan': ['Check ELF relocation resolution and window bounds.']
    })

    # Staging Review
    tasks.append({
        'id': f'h10-{sid}-staging-review',
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent review of staged candidate {sname}.',
        'depends_on': [f'h10-{sid}-staging'],
        'function_claims': fclaim,
        'read_paths': [stag_doc],
        'write_paths': [stag_review_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': ['Verify candidate is properly aligned, relocations patched, and padding clean.'],
        'validation_plan': ['Confirm relocation offset calculations and target VMA mapping.']
    })

# Staging Composite Image
staging_deps = [f"h10-{s['id']}-staging-review" for s in subsystems]

tasks.append({
    'id': 'h10-staged-image-patch',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose all 8 validated H10 semantic candidates into final staged executable image and IPS patch.',
    'depends_on': staging_deps,
    'function_claims': all_funcs,
    'read_paths': ['tools/h10_staged_image_patch.py'] + [s['cand_src'] for s in subsystems],
    'write_paths': [
        'build/agent-work/H10-semantic/h10-integrated-stage/code.h10-final.bin',
        'build/agent-work/H10-semantic/h10-integrated-stage/code.h10-final.ips',
        'build/agent-work/H10-semantic/h10-integrated-stage/report.json',
        'docs/agent-work/h10-staged-image-patch.md'
    ],
    'compiler_slots': 2,
    'exclusive_resources': [],
    'acceptance': [
        'Successfully compile and relocate all 8 candidates onto the H9 base image.',
        'Generate valid code.h10-final.bin and byte-accurate code.h10-final.ips.',
        'Verify 100% round-trip fidelity through apply_ips.'
    ],
    'validation_plan': ['Run tools/h10_staged_image_patch.py.']
})

tasks.append({
    'id': 'h10-staged-image-patch-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of H10 final composite binary and IPS patch artifacts.',
    'depends_on': ['h10-staged-image-patch'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h10-staged-image-patch.md', 'build/agent-work/H10-semantic/h10-integrated-stage/report.json'],
    'write_paths': ['docs/agent-work/h10-staged-image-patch-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Verify binary integrity, non-overlapping windows, and SHA-256 hashes.'],
    'validation_plan': ['Audit report.json manifest and verify zero regression outside target windows.']
})

tasks.append({
    'id': 'h10-offline-composite-gates',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Execute full suite of offline composite differential gates and caller compositions for H10 image.',
    'depends_on': ['h10-staged-image-patch-review'],
    'function_claims': all_funcs,
    'read_paths': ['tools/build_h10_all.py', 'build/agent-work/H10-semantic/h10-integrated-stage/code.h10-final.bin'],
    'write_paths': ['docs/agent-work/h10-offline-composite-gates.md'],
    'compiler_slots': 2,
    'exclusive_resources': [],
    'acceptance': [
        'All 8 candidates pass individual Unicorn offline differential validations.',
        'Zero regressions across combined candidate assembly and ARM/Thumb interworking bits.'
    ],
    'validation_plan': ['Run tools/build_h10_all.py and all 8 experiment scripts.']
})

tasks.append({
    'id': 'h10-offline-composite-gates-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of offline composite gates and interworking integrity.',
    'depends_on': ['h10-offline-composite-gates'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h10-offline-composite-gates.md'],
    'write_paths': ['docs/agent-work/h10-offline-composite-gates-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Approve offline test results prior to emulator runtime verification.'],
    'validation_plan': ['Audit gate execution outputs and mutation sensitivity logs.']
})

tasks.append({
    'id': 'h10-autonomous-quests-apps-verify',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Autonomous runtime verification in Azahar emulator: Title, Save Load, Field, and Burroughs / Quests / Apps sequences.',
    'depends_on': ['h10-offline-composite-gates-review'],
    'function_claims': all_funcs,
    'read_paths': ['tools/h3_autonomous_verify.py', 'code.h10-final.ips'],
    'write_paths': ['docs/agent-work/h10-autonomous-quests-apps-verify.md'],
    'compiler_slots': 0,
    'exclusive_resources': ['emulator_session'],
    'acceptance': [
        'Run paired autonomous test via GDB RSP loopback stub.',
        '0 register differences across Title, Save Load, 250 Field scene ticks, and Burroughs / Quests / Apps subsystems.'
    ],
    'validation_plan': ['Execute autonomous verify script and generate paired report.json.']
})

tasks.append({
    'id': 'h10-autonomous-quests-apps-verify-review',
    'role': 'validation',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review of autonomous paired runtime verification for Milestone H10.',
    'depends_on': ['h10-autonomous-quests-apps-verify'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h10-autonomous-quests-apps-verify.md'],
    'write_paths': ['docs/agent-work/h10-autonomous-quests-apps-verify-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Confirm 100% paired equivalence with zero register or state differences.'],
    'validation_plan': ['Audit runtime report metrics and save file hash integrity.']
})

# Milestone Closure
tasks.append({
    'id': 'h10-milestone-closure',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Formalize closure of Milestone H10 across documentation and ledger tracking.',
    'depends_on': ['h10-autonomous-quests-apps-verify-review'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/milestones/H10-burroughs-quests-apps.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'write_paths': [
        'docs/milestones/H10-burroughs-quests-apps.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Update documentation marking Milestone H10 as completed and closed.',
        'Ensure clean git state and 0 errors from tools/agent_workflow.py check.'
    ],
    'validation_plan': ['Run python tools/agent_workflow.py check.']
})

board = {
    'schema_version': 1,
    'batch': 'batch-h10-001',
    'milestone': 'H10',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Reconstruct readable, editable C++ for Milestone H10 (Burroughs, Quests, and Apps), covering Burroughs save data resolution (Burroughs_GetSaveData), application selection dispatching (Burroughs_AppDispatch), quest list selection reset (Quest_ResetSelection), quest objective condition evaluation (Quest_EvaluateTargetCondition), quest availability checking for main and challenge quests (Quest_GetAvailability), quest static definition unpacking (Quest_UnpackEntryData), Demonica App Store purchase flag registration (AppStore_SetFlag), and App Store parameter query and string formatting (AppStore_GetAppParam) with full offline differential validation, caller composition, staging, and autonomous runtime verification.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h10.json',
        'config/reconstruction.json',
        'docs/milestones/H10-burroughs-quests-apps.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_path = ROOT / 'config/agent-workflows/h10.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(board, f, indent=2)

print(f"Generated {out_path} with {len(tasks)} tasks.")
