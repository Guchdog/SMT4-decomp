# Implementation Plan: Leaf Function Matching Batch 13 (100 Functions, 7,940 Bytes)

## Goal

Advance exact ARMv6K matching from 761 functions (17,412 bytes) to 861 functions
(25,352 bytes) by reconstructing the next 100 no-call leaf functions. The search
includes internal conditional branches and is capped at 128 bytes per function.

## Parallel Work Split

The three groups use separate source files to keep independent implementations
isolated:

- `src/engine/leaf_batch13_a.cpp`: 34 functions, candidates 4–37.
- `src/engine/leaf_batch13_b.cpp`: 33 functions, candidates 38–70.
- `src/engine/leaf_batch13_c.cpp`: 33 functions, candidates 71–103.

The three 28–40-byte Thumb CRT candidates at the start of the scan were skipped;
the 100 selected routines are ARM functions ranging from 56 to 108 bytes.

## Batch Composition

| Size | Functions | Bytes |
|---|---:|---:|
| 56 bytes | 9 | 504 |
| 60 bytes | 10 | 600 |
| 64 bytes | 7 | 448 |
| 68 bytes | 6 | 408 |
| 72 bytes | 5 | 360 |
| 76 bytes | 12 | 912 |
| 80 bytes | 6 | 480 |
| 84 bytes | 8 | 672 |
| 88 bytes | 10 | 880 |
| 92 bytes | 6 | 552 |
| 96 bytes | 6 | 576 |
| 100 bytes | 7 | 700 |
| 104 bytes | 4 | 416 |
| 108 bytes | 4 | 432 |
| **Total** | **100** | **7,940** |

The batch spans `unknown` (71), `engine` (15), `camp` (6), `battle` (4),
`script_vm` (2), `shop` (1), and `unite` (1).

## Verification

Compile and byte-audit each source group, then verify the integrated ledger,
regenerate progress documentation, and run the full tests and ARM/CMake builds
before committing and pushing.
