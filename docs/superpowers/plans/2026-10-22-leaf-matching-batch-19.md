# Implementation Plan: 200-Function Matching Batch 19

## Goal

Advance exact ARMv6K machine code matching by 200 functions from the post-batch-18 baseline
of 1,661 functions (122,724 bytes) to 1,861 functions (131,812 bytes, 4.1990% of `.text`).
The batch decompiles small leaf routines, conditional branch blocks, and subroutine calls to
known symbols across multiple subsystems.

## Batch 19 Breakdown

The 200 functions are divided into three translation units in `src/engine/`:

| Source | Functions | Bytes |
|---|---:|---:|
| `src/engine/leaf_batch19_a.cpp` | 67 | 2,752 |
| `src/engine/leaf_batch19_b.cpp` | 67 | 3,148 |
| `src/engine/leaf_batch19_c.cpp` | 66 | 3,188 |
| **Batch 19 total** | **200** | **9,088** |

## Subsystem Impact

| Subsystem | Previous Matching | Added in Batch 19 | New Matching |
|---|---:|---:|---:|
| `engine` | 209 (12,588 B) | +57 (+2,640 B) | 266 (15,228 B) |
| `unknown` | 1,118 (90,604 B) | +66 (+3,004 B) | 1,184 (93,608 B) |
| `script_vm` | 118 (5,528 B) | +24 (+1,032 B) | 142 (6,560 B) |
| `ui` | 89 (7,852 B) | +27 (+1,232 B) | 116 (9,084 B) |
| `battle` | 47 (1,968 B) | +14 (+656 B) | 61 (2,624 B) |
| `camp` | 56 (2,700 B) | +7 (+292 B) | 63 (2,992 B) |
| `shop` | 9 (832 B) | +4 (+188 B) | 13 (1,020 B) |
| `nn_sdk` | 6 (296 B) | +1 (+44 B) | 7 (340 B) |
| `crt` | 4 (140 B) | +0 (+0 B) | 4 (140 B) |
| `unite` | 5 (216 B) | +0 (+0 B) | 5 (216 B) |
| **Total** | **1,661 (122,724 B)** | **+200 (+9,088 B)** | **1,861 (131,812 B)** |

## Verification

1. Audited all 200 functions byte-for-byte against `extracted/exefs/code.bin` using `tools/asm_diff.py` and `tools/verify_decomp.py`.
2. Verified ARMv6K compilation of translation units via `tests/test_build.py`.
3. Verified progress metrics and ledger consistency via `tests/test_progress.py`.
4. Verified byte-accurate match of all 1,861 functions in ledger via `tests/test_asm_diff.py`.
