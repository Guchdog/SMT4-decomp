# Implementation Plan: 200-Function Matching Batch 18

## Goal

Advance exact ARMv6K machine code matching by 200 functions from the post-batch-17 baseline
of 1,461 functions (116,484 bytes) to 1,661 functions (122,724 bytes, 3.9095% of `.text`).
The batch decompiles small leaf routines, functions with internal conditional branches, and
subroutine calls to known functions across multiple subsystems.

## Batch 18 Breakdown

The 200 functions are divided into three translation units in `src/engine/`:

| Source | Functions | Bytes |
|---|---:|---:|
| `src/engine/leaf_batch18_a.cpp` | 67 | 2,096 |
| `src/engine/leaf_batch18_b.cpp` | 67 | 2,128 |
| `src/engine/leaf_batch18_c.cpp` | 66 | 2,016 |
| **Batch 18 total** | **200** | **6,240** |

## Subsystem Impact

| Subsystem | Previous Matching | Added Matching | New Matching |
|---|---:|---:|---:|
| `engine` | 162 (11,168 B) | +47 (+1,420 B) | 209 (12,588 B) |
| `unknown` | 1,039 (87,996 B) | +79 (+2,608 B) | 1,118 (90,604 B) |
| `script_vm` | 91 (4,728 B) | +27 (+800 B) | 118 (5,528 B) |
| `ui` | 69 (7,240 B) | +20 (+612 B) | 89 (7,852 B) |
| `battle` | 26 (1,328 B) | +21 (+640 B) | 47 (1,968 B) |
| `camp` | 52 (2,604 B) | +4 (+96 B) | 56 (2,700 B) |
| `nn_sdk` | 5 (264 B) | +1 (+32 B) | 6 (296 B) |
| `crt` | 3 (108 B) | +1 (+32 B) | 4 (140 B) |
| `shop` | 9 (832 B) | +0 (+0 B) | 9 (832 B) |
| `unite` | 5 (216 B) | +0 (+0 B) | 5 (216 B) |
| **Total** | **1,461 (116,484 B)** | **+200 (+6,240 B)** | **1,661 (122,724 B)** |

## Verification

1. Audited all 200 functions byte-for-byte against `extracted/exefs/code.bin` using `tools/asm_diff.py` and `tools/verify_decomp.py`.
2. Verified ARMv6K compilation of translation units via `tests/test_build.py`.
3. Verified progress metrics and ledger consistency via `tests/test_progress.py`.
4. Verified byte-accurate match of all 1,661 functions in ledger via `tests/test_asm_diff.py`.
