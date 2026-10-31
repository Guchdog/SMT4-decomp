#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h19.json for Milestone H19."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'crt-start',
        'func': '0x00100000',
        'name': '__start',
        'desc': 'CRT process entry point and subsystem dispatcher sequence',
        'cand_src': 'src/crt/start.cpp',
        'test_src': 'tools/h19_crt_start_experiment.py',
        'contract_doc': 'docs/agent-work/h19-crt-start-contract.md',
        'cand_doc': 'docs/agent-work/h19-crt-start-candidate.md',
    },
    {
        'id': 'crt-init-bss',
        'func': '0x00100024',
        'name': '__init_bss',
        'desc': 'CRT BSS section zeroing loop across 0x00477000..0x004EFE34',
        'cand_src': 'src/crt/start.cpp',
        'test_src': 'tools/h19_crt_start_experiment.py',
        'contract_doc': 'docs/agent-work/h19-crt-init-bss-contract.md',
        'cand_doc': 'docs/agent-work/h19-crt-init-bss-candidate.md',
    },
]

tasks = []
all_funcs = [s['func'] for s in subsystems]

# 1. Full Link Recon & Review
tasks.append({
    'id': 'h19-full-link-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Map whole-executable memory layout, text boundaries, BSS boundaries, and CRT bootstrap in code.bin.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': ['docs/reconstruction-milestones.md', 'src/crt/start.cpp'],
    'write_paths': ['docs/agent-work/h19-full-link-recon.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Map 0x00100000 entry point, section layout (.text, .rodata, .data, .bss) and CRT init steps.'],
    'validation_plan': ['python tools/build_h19_all.py']
})

tasks.append({
    'id': 'h19-full-link-recon-review',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Review executable memory layout and link architecture.',
    'depends_on': ['h19-full-link-recon'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h19-full-link-recon.md'],
    'write_paths': ['docs/agent-work/h19-full-link-recon-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Approve full binary layout and verify section consistency with 3DS ExeFS specifications.'],
    'validation_plan': ['python tools/build_h19_all.py']
})

for s in subsystems:
    sid = s['id']
    fn = s['func']
    name = s['name']
    desc = s['desc']
    cand_src = s['cand_src']
    test_src = s['test_src']
    c_doc = s['contract_doc']
    cand_doc = s['cand_doc']

    t_contract = f'h19-{sid}-contract'
    t_contract_rev = f'h19-{sid}-contract-review'
    t_recon = f'h19-{sid}-recon'
    t_recon_rev = f'h19-{sid}-recon-review'
    t_cand = f'h19-{sid}-candidate'
    t_cand_rev = f'h19-{sid}-candidate-review'
    t_diff = f'h19-{sid}-diff-test'
    t_diff_rev = f'h19-{sid}-diff-test-review'

    tasks.append({
        'id': t_contract,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Define contract specification for {name} ({fn}) in {desc}.',
        'depends_on': ['h19-full-link-recon-review'],
        'function_claims': [fn],
        'read_paths': [cand_src],
        'write_paths': [c_doc],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Specify calling convention, register inputs, preconditions, and return contract for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_contract_rev,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Review contract specification for {name} ({fn}).',
        'depends_on': [t_contract],
        'function_claims': [fn],
        'read_paths': [c_doc],
        'write_paths': [f'docs/agent-work/h19-{sid}-contract-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Verify ABI soundness and contract boundaries for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_recon,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Disassemble and recover assembly semantics for {name} ({fn}).',
        'depends_on': [t_contract_rev],
        'function_claims': [fn],
        'read_paths': ['extracted/exefs/code.bin'],
        'write_paths': [f'docs/agent-work/h19-{sid}-recon.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Confirm ARM instructions, immediate offsets, and calling sequences for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_recon_rev,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Review assembly reconnaissance for {name} ({fn}).',
        'depends_on': [t_recon],
        'function_claims': [fn],
        'read_paths': [f'docs/agent-work/h19-{sid}-recon.md'],
        'write_paths': [f'docs/agent-work/h19-{sid}-recon-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Approve disassembly analysis for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_cand,
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement canonical C++ function for {name} ({fn}).',
        'depends_on': [t_recon_rev],
        'function_claims': [fn],
        'read_paths': [cand_src],
        'write_paths': [cand_src, cand_doc],
        'compiler_slots': 1,
        'exclusive_resources': [cand_src],
        'acceptance': [f'Compile {cand_src} cleanly with Clang ARMv6K within original byte window.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_cand_rev,
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent code review of {name} ({fn}).',
        'depends_on': [t_cand],
        'function_claims': [fn],
        'read_paths': [cand_src, cand_doc],
        'write_paths': [f'docs/agent-work/h19-{sid}-candidate-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Verify that implementation matches contract and has zero UB.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_diff,
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Run offline Unicorn differential test suite for {name} ({fn}).',
        'depends_on': [t_cand_rev],
        'function_claims': [fn],
        'read_paths': [cand_src, test_src],
        'write_paths': [test_src, f'docs/agent-work/h19-{sid}-diff-test.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'100% register/memory parity across input domain and positive mutation sensitivity.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_diff_rev,
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Review differential test results for {name} ({fn}).',
        'depends_on': [t_diff],
        'function_claims': [fn],
        'read_paths': [f'docs/agent-work/h19-{sid}-diff-test.md'],
        'write_paths': [f'docs/agent-work/h19-{sid}-diff-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Confirm differential suite completeness for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

# Final staging and milestone review tasks (2 tasks)
tasks.append({
    'id': 'h19-integrated-staging',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Compose CRT bootstrap and full module tree into code.h19-final.bin and produce verified IPS patch.',
    'depends_on': [f'h19-{s["id"]}-diff-test-review' for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': ['src/crt/start.cpp', 'build/agent-work/H18-semantic/h18-integrated-stage/code.h18-final.bin'],
    'write_paths': [
        'build/agent-work/H19-semantic/h19-integrated-stage/code.h19-final.bin',
        'build/agent-work/H19-semantic/h19-integrated-stage/code.h19-final.ips',
        'build/agent-work/H19-semantic/h19-integrated-stage/h19-staged-summary.json',
        'docs/agent-work/h19-integrated-staging.md',
    ],
    'compiler_slots': 1,
    'exclusive_resources': ['code.h19-final.bin'],
    'acceptance': [
        'Generate code.h19-final.bin with CRT start and all reconstructed modules cleanly linked.',
        'Produce verified LayeredFS IPS patch code.h19-final.ips passing roundtrip verification.'
    ],
    'validation_plan': ['python tools/h19_staged_image_patch.py']
})

tasks.append({
    'id': 'h19-milestone-closure-review',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review and closure of Milestone H19 (Full Link & Executable Synthesis).',
    'depends_on': ['h19-integrated-staging'],
    'function_claims': all_funcs,
    'read_paths': [
        'build/agent-work/H19-semantic/h19-integrated-stage/h19-staged-summary.json',
        'docs/agent-work/h19-integrated-staging.md',
    ],
    'write_paths': [
        'docs/agent-work/h19-milestone-closure-review.md',
        'docs/milestones/H19-full-link.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Confirm complete linkage of reconstructed modules and CRT entry bootstrap.',
        'Validate offline differential test suite and staging IPS patch roundtrip.'
    ],
    'validation_plan': [
        'python tools/agent_workflow.py check',
        'python tools/build_h19_all.py',
        'python tools/h19_crt_start_experiment.py',
        'python tools/h19_staged_image_patch.py'
    ]
})

board = {
    'schema_version': 1,
    'batch': 'batch-h19-001',
    'milestone': 'H19',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Enlace del Ejecutable Reconstruido Completo: generar y enlazar el binario code.bin completo desde codigo fuente C++ reconstruido (crt/start.cpp + subsistemas promovidos), con validacion diferencial, staging acumulativo y verificacion autonoma.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h19.json',
        'config/reconstruction.json',
        'docs/milestones/H19-full-link.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_board = ROOT / 'config/agent-workflows/h19.json'
out_board.parent.mkdir(parents=True, exist_ok=True)
out_board.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Workflow board written to {out_board} with {len(tasks)} tasks.")
