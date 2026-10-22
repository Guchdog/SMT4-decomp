# Implementation Plan: Leaf Function Matching Batch 8 (50 Functions, 984 Bytes)

## Goal

Advance exact ARMv6K matching from 411 functions (4,528 bytes) to 461 functions
(5,512 bytes) by reconstructing 50 pure, no-call leaf functions selected from the
unexplored ledger with `tools/find_candidates.py`.

## Changes

- Add declarations and exact inline-assembly implementations in
  `include/engine/leaf_matching.h` and `src/engine/leaf_matching.cpp`.
- Mark the 50 functions as `matching` in `config/functions.csv`.
- Update the audit/progress test expectations and regenerate `PROGRESS.md` and
  `README.md`.

## Batch Composition

| Size | Functions | Bytes |
|---|---:|---:|
| 16 bytes | 11 | 176 |
| 20 bytes | 32 | 640 |
| 24 bytes | 7 | 168 |
| **Total** | **50** | **984** |

The selected functions span `unknown` (34), `camp` (5), `script_vm` (5),
`engine` (4), `battle` (1), and `ui` (1).

## Verification

1. Compile the leaf matching translation unit with the canonical ARMv6K flags.
2. Run `tools/verify_decomp.py`; every `matching` ledger entry must be byte-identical.
3. Regenerate progress documentation and run the full test, ARM build, CMake, and
   diff-whitespace checks before committing and pushing.
