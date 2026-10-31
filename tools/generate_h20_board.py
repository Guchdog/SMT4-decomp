#!/usr/bin/env python3
"""Generate workflow board config/agent-workflows/h20.json for Milestone H20."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subsystems = [
    {
        'id': 'hal-system',
        'func': '0x00104ef4',
        'name': 'HAL_System',
        'desc': 'Platform lifecycle, initialization, shutdown, and high-resolution timer',
        'cand_src': 'src/hal/hal_system.cpp',
        'test_src': 'tools/verify_h20_hal.py',
        'contract_doc': 'docs/agent-work/h20-hal-system-contract.md',
        'cand_doc': 'docs/agent-work/h20-hal-system-candidate.md',
    },
    {
        'id': 'hal-filesystem',
        'func': '0x0021041c',
        'name': 'HAL_FileSystem',
        'desc': 'Virtual archive mounting and unified file stream abstraction',
        'cand_src': 'src/hal/hal_filesystem.cpp',
        'test_src': 'tools/verify_h20_hal.py',
        'contract_doc': 'docs/agent-work/h20-hal-filesystem-contract.md',
        'cand_doc': 'docs/agent-work/h20-hal-filesystem-candidate.md',
    },
    {
        'id': 'hal-graphics',
        'func': '0x002c3b88',
        'name': 'HAL_Graphics',
        'desc': 'Display target management, stereoscopic 3D mode, and frame swap',
        'cand_src': 'src/hal/hal_graphics.cpp',
        'test_src': 'tools/verify_h20_hal.py',
        'contract_doc': 'docs/agent-work/h20-hal-graphics-contract.md',
        'cand_doc': 'docs/agent-work/h20-hal-graphics-candidate.md',
    },
    {
        'id': 'hal-audio',
        'func': '0x0011311c',
        'name': 'HAL_Audio',
        'desc': 'Multi-channel PCM stream management, sample queueing, and volume gain',
        'cand_src': 'src/hal/hal_audio.cpp',
        'test_src': 'tools/verify_h20_hal.py',
        'contract_doc': 'docs/agent-work/h20-hal-audio-contract.md',
        'cand_doc': 'docs/agent-work/h20-hal-audio-candidate.md',
    },
    {
        'id': 'hal-input',
        'func': '0x0027fbc8',
        'name': 'HAL_Input',
        'desc': 'Touchscreen coordinates, Circle Pad analog deflection, and digital buttons',
        'cand_src': 'src/hal/hal_input.cpp',
        'test_src': 'tools/verify_h20_hal.py',
        'contract_doc': 'docs/agent-work/h20-hal-input-contract.md',
        'cand_doc': 'docs/agent-work/h20-hal-input-candidate.md',
    },
]

tasks = []
all_funcs = [s['func'] for s in subsystems]

# 1. HAL Architecture Recon & Review
tasks.append({
    'id': 'h20-hal-architecture-recon',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Map 3DS OS/GSP/FS/DSP/HID service dependencies and design platform-agnostic HAL interfaces.',
    'depends_on': [],
    'function_claims': all_funcs,
    'read_paths': ['docs/reconstruction-milestones.md', 'include/hal/'],
    'write_paths': ['docs/agent-work/h20-hal-architecture-recon.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Define clean decoupled interfaces in include/hal/ for System, FS, Graphics, Audio, and Input.'],
    'validation_plan': ['python tools/build_h20_all.py']
})

tasks.append({
    'id': 'h20-hal-architecture-recon-review',
    'role': 'recon',
    'state': 'accepted',
    'owner': None,
    'goal': 'Review HAL abstraction architecture and portability contracts.',
    'depends_on': ['h20-hal-architecture-recon'],
    'function_claims': all_funcs,
    'read_paths': ['docs/agent-work/h20-hal-architecture-recon.md'],
    'write_paths': ['docs/agent-work/h20-hal-architecture-recon-review.md'],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': ['Approve HAL interface designs and verify full decoupling from 3DS kernel services.'],
    'validation_plan': ['python tools/build_h20_all.py']
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

    t_contract = f'h20-{sid}-contract'
    t_contract_rev = f'h20-{sid}-contract-review'
    t_recon = f'h20-{sid}-recon'
    t_recon_rev = f'h20-{sid}-recon-review'
    t_cand = f'h20-{sid}-candidate'
    t_cand_rev = f'h20-{sid}-candidate-review'
    t_diff = f'h20-{sid}-diff-test'
    t_diff_rev = f'h20-{sid}-diff-test-review'

    tasks.append({
        'id': t_contract,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Define contract specification for {name} ({fn}) in {desc}.',
        'depends_on': ['h20-hal-architecture-recon-review'],
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
        'write_paths': [f'docs/agent-work/h20-{sid}-contract-review.md'],
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
        'goal': f'Disassemble and recover service semantics for {name} ({fn}).',
        'depends_on': [t_contract_rev],
        'function_claims': [fn],
        'read_paths': ['extracted/exefs/code.bin'],
        'write_paths': [f'docs/agent-work/h20-{sid}-recon.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Confirm service IPC commands, parameters, and return codes for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_recon_rev,
        'role': 'recon',
        'state': 'accepted',
        'owner': None,
        'goal': f'Review service reconnaissance for {name} ({fn}).',
        'depends_on': [t_recon],
        'function_claims': [fn],
        'read_paths': [f'docs/agent-work/h20-{sid}-recon.md'],
        'write_paths': [f'docs/agent-work/h20-{sid}-recon-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Approve service analysis for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_cand,
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Implement portable HAL module for {name} ({fn}).',
        'depends_on': [t_recon_rev],
        'function_claims': [fn],
        'read_paths': [cand_src],
        'write_paths': [cand_src, cand_doc],
        'compiler_slots': 1,
        'exclusive_resources': [cand_src],
        'acceptance': [f'Compile {cand_src} cleanly with Clang ARMv6K and native C++ compiler.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_cand_rev,
        'role': 'implementation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Independent code review of portable HAL module {name} ({fn}).',
        'depends_on': [t_cand],
        'function_claims': [fn],
        'read_paths': [cand_src, cand_doc],
        'write_paths': [f'docs/agent-work/h20-{sid}-candidate-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Verify that implementation matches contract and is fully portable.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_diff,
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Run autonomous contract verification suite for {name} ({fn}).',
        'depends_on': [t_cand_rev],
        'function_claims': [fn],
        'read_paths': [cand_src, test_src],
        'write_paths': [test_src, f'docs/agent-work/h20-{sid}-diff-test.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'100% contract verification across states and positive mutation sensitivity.'],
        'validation_plan': [f'python {test_src}']
    })

    tasks.append({
        'id': t_diff_rev,
        'role': 'validation',
        'state': 'accepted',
        'owner': None,
        'goal': f'Review verification test results for {name} ({fn}).',
        'depends_on': [t_diff],
        'function_claims': [fn],
        'read_paths': [f'docs/agent-work/h20-{sid}-diff-test.md'],
        'write_paths': [f'docs/agent-work/h20-{sid}-diff-test-review.md'],
        'compiler_slots': 0,
        'exclusive_resources': [],
        'acceptance': [f'Confirm verification suite completeness for {name}.'],
        'validation_plan': [f'python {test_src}']
    })

# Final staging and milestone review tasks (2 tasks)
tasks.append({
    'id': 'h20-hal-integration-staging',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Integrate all HAL modules into the unified portable build configuration.',
    'depends_on': [f'h20-{s["id"]}-diff-test-review' for s in subsystems],
    'function_claims': all_funcs,
    'read_paths': [s['cand_src'] for s in subsystems],
    'write_paths': [
        'docs/agent-work/h20-hal-integration-staging.md',
    ],
    'compiler_slots': 1,
    'exclusive_resources': [],
    'acceptance': [
        'Compile all 5 HAL modules in build/h20_candidates cleanly with zero warnings/errors.',
        'Pass comprehensive HAL test suite tools/verify_h20_hal.py.'
    ],
    'validation_plan': ['python tools/verify_h20_hal.py']
})

tasks.append({
    'id': 'h20-milestone-closure-review',
    'role': 'integration',
    'state': 'accepted',
    'owner': None,
    'goal': 'Independent review and closure of Milestone H20 (Platform Abstraction Layer & Portability).',
    'depends_on': ['h20-hal-integration-staging'],
    'function_claims': all_funcs,
    'read_paths': [
        'docs/agent-work/h20-hal-integration-staging.md',
    ],
    'write_paths': [
        'docs/agent-work/h20-milestone-closure-review.md',
        'docs/milestones/H20-platform-hal.md'
    ],
    'compiler_slots': 0,
    'exclusive_resources': [],
    'acceptance': [
        'Confirm complete decoupling of 3DS kernel services behind portable HAL interfaces.',
        'Validate HAL verification suite passes 100% across all 5 subsystems.'
    ],
    'validation_plan': [
        'python tools/agent_workflow.py check',
        'python tools/build_h20_all.py',
        'python tools/verify_h20_hal.py'
    ]
})

board = {
    'schema_version': 1,
    'batch': 'batch-h20-001',
    'milestone': 'H20',
    'max_workers': 3,
    'cpu_budget': 8,
    'goal': 'Capa de Abstraccion de Plataforma (HAL) y Portabilidad Nativa: desacoplar servicios del kernel/SDK de 3DS (src/nn/, fs, gsp/gx, dsp, hid, os) detras de una HAL multiplataforma para compilacion y ejecucion nativa fuera de 3DS.',
    'coordinator_owned_paths': [
        'config/agent-workflows/h20.json',
        'config/reconstruction.json',
        'docs/milestones/H20-platform-hal.md',
        'docs/functional-status.md',
        'docs/reconstruction-milestones.md'
    ],
    'tasks': tasks
}

out_board = ROOT / 'config/agent-workflows/h20.json'
out_board.parent.mkdir(parents=True, exist_ok=True)
out_board.write_text(json.dumps(board, indent=2), encoding='utf-8')
print(f"Workflow board written to {out_board} with {len(tasks)} tasks.")
