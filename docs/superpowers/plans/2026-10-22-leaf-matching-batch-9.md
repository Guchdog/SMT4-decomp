# Implementation Plan: Leaf Function Matching Batch 9 (50 Functions, 1,244 Bytes)

## Goal

Advance exact ARMv6K matching from 461 functions (5,512 bytes) to 511 functions
(6,756 bytes) by reconstructing the next 50 pure leaf candidates from the
unexplored ledger.

## Changes

- Add 50 declarations and exact naked inline-assembly implementations in
  `include/engine/leaf_matching.h` and `src/engine/leaf_matching.cpp`.
- Mark all 50 rows `matching` in `config/functions.csv`.
- Update matching/progress test expectations and regenerate `PROGRESS.md` and
  `README.md`.

## Batch Composition

| Size | Functions | Bytes |
|---|---:|---:|
| 24 bytes | 39 | 936 |
| 28 bytes | 11 | 308 |
| **Total** | **50** | **1,244** |

The batch spans `unknown` (30), `camp` (7), `engine` (6), `script_vm` (3),
`battle` (2), `nn_sdk` (1), and `shop` (1).

## Verification

Run the canonical ARMv6K build and byte-level audit, regenerate the progress
reports, then run the full unit suite and CMake ARM build before committing.
