# Implementation Plan: Leaf Function Matching Batch 10 (100 Functions, 3,612 Bytes)

## Goal

Advance exact ARMv6K matching from 511 functions (6,756 bytes) to 611 functions
(10,368 bytes) by reconstructing the next 100 pure, no-call leaf candidates.

## Parallel Work Split

Three independent source units isolate the parallel reconstruction work:

- `src/engine/leaf_batch10_a.cpp`: 34 functions, 1,028 bytes.
- `src/engine/leaf_batch10_b.cpp`: 33 functions, 1,168 bytes.
- `src/engine/leaf_batch10_c.cpp`: 33 functions, 1,416 bytes.

## Batch Composition

| Size | Functions | Bytes |
|---|---:|---:|
| 28 bytes | 15 | 420 |
| 32 bytes | 28 | 896 |
| 36 bytes | 20 | 720 |
| 40 bytes | 13 | 520 |
| 44 bytes | 24 | 1,056 |
| **Total** | **100** | **3,612** |

The group spans `unknown` (71), `engine` (18), `camp` (4), `ui` (3),
`script_vm` (2), `battle` (1), and `unite` (1).

## Verification

Each parallel unit is compiled and checked against the extracted executable before
the shared ledger is updated. The integrated batch must then pass the full
byte-level audit, progress regeneration, full unit suite, force ARM build, CMake
ARM build, and whitespace check before commit.
