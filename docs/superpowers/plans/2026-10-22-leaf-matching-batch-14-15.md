# Implementation Plan: Two 100-Function Matching Batches

## Goal

Advance exact ARMv6K matching by 200 functions from the post-batch-13 baseline
of 861 functions and 25,352 bytes. The work is split between 100 remaining
pure leaf routines and 100 additional small routines that use only indirect
calls, system calls, internal branches, or register tail transfers; no external
direct-call relocations are accepted as proof of a match.

## Batch 14: Remaining Pure Leaves

The candidate scan was widened to 4,096 bytes. Three Thumb CRT routines were
excluded; candidates 4–103 are 100 ARM functions ranging from 112 to 2,344
bytes.

| Source | Functions | Bytes |
|---|---:|---:|
| `src/engine/leaf_batch14_a.cpp` | 33 | 4,116 |
| `src/engine/leaf_batch14_b.cpp` | 33 | 6,224 |
| `src/engine/leaf_batch14_c.cpp` | 34 | 23,412 |
| **Batch 14 total** | **100** | **33,752** |

## Batch 15: Indirect/System-Call Leaf Routines

The supplemental scan selected 100 other fully decoded TODO functions, excluding
the batch-14 addresses. Their sizes range from 8 to 68 bytes. This set includes
SVC instructions, register-indirect `BLX`, and register-indirect tail transfers;
direct external branches are excluded because unresolved relocations cannot
establish an exact linked match.

| Source | Functions | Bytes |
|---|---:|---:|
| `src/engine/leaf_batch15_a.cpp` | 34 | 792 |
| `src/engine/leaf_batch15_b.cpp` | 33 | 1,504 |
| `src/engine/leaf_batch15_c.cpp` | 33 | 2,036 |
| **Batch 15 total** | **100** | **4,332** |

## Verification

Compile and byte-audit each source group against `code.bin`, register only
marker/address/size-matched TODO ledger rows, regenerate progress documentation,
then run the full test suite, forced ARMv6K build, and CMake ARM build before
committing and pushing.
