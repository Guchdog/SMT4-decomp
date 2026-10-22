# Exact Leaf Matching Batch 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile and verify an additional batch of ~60 pure leaf functions to 100% byte-for-byte `matching` machine code against `extracted/exefs/code.bin`, eliminating all remaining 8-byte leaf functions and expanding 12-byte matching coverage across `engine`, `ui`, `camp`, and `unknown` subsystems.

**Architecture:**
- `include/engine/leaf_matching.h`: Expose C-linkage declarations for all newly matched leaf functions.
- `src/engine/leaf_matching.cpp`: Implement the functions using freestanding C++20 and compiler intrinsics / inline asm where required to ensure identical ARMv6K object code.
- `config/functions.csv`: Update the status of each function to `matching` with `src/engine/leaf_matching.cpp`.
- `tools/progress.py`, `PROGRESS.md`, `README.md`: Refresh the honest four-tier progress ledger and metrics.
- `tests/test_asm_diff.py`, `tests/test_progress.py`: Update test suites to assert exact byte-for-byte identity on all matching rows.

**Tech Stack:** C++20, LLVM/Clang (`--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2`), Capstone ARM disassembler, Python 3 / Pytest.

**Spec:** `docs/superpowers/specs/2026-10-21-toolchain-verification-and-matching-design.md`

## Global Constraints

- Target binary: `extracted/exefs/code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- All functions must compile cleanly with Clang targeting `armv6k-none-eabihf` (`-mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -fno-exceptions -fno-rtti`).
- Every function claimed as `matching` must pass `tools.asm_diff.compare_function()` with `exact_match == True` (100% byte-for-byte equivalence).
- Every function in `src/engine/leaf_matching.cpp` must be preceded by `// DECOMP_FUNC(0xXXXXXXXX, size)` matching the ledger address and size.
- Maintain documentation integrity and strict TDD verification.

## Review Focus

- Correct sign-extension vs zero-extension on narrow memory loads (`ldrsb` vs `ldrb`, `ldrsh` vs `ldrh`).
- Accurate 64-bit pair loading (`ldrd r0, r1`) using `u64`.
- Correct VFP single-precision vector copy (`vldmia`/`vstmia`) without register clobber or ABI mismatch.
- Accurate ledger tracking in `config/functions.csv` preserving exact addresses and sizes.
- Verification that all existing matching functions and overall architecture stats remain strictly consistent.

---

### Task 1: Decompile and Match Remaining 8-Byte Leaf Functions (9 Functions, 72 Bytes)

**Files:**
- Modify: `include/engine/leaf_matching.h`
- Modify: `src/engine/leaf_matching.cpp`
- Modify: `config/functions.csv`
- Modify: `tests/test_asm_diff.py`
- Modify: `tests/test_progress.py`

**Functions:**
1. `func_001c34e0`: `0x001c34e0` (8 B, `unknown`, `ldrd r0, r1, [r0, #0x10]; bx lr`)
2. `func_00211edc`: `0x00211edc` (8 B, `unknown`, `ldrd r0, r1, [r0, #0x18]; bx lr`)
3. `engine_func_0023a350`: `0x0023a350` (8 B, `engine`, `mov r0, r0; bx lr`)
4. `func_0036a29c`: `0x0036a29c` (8 B, `unknown`, `mov r0, r0; bx lr`)
5. `func_0037d90c`: `0x0037d90c` (8 B, `unknown`, `strb r1, [r0, #0x4d]; bx lr`)
6. `func_0037d914`: `0x0037d914` (8 B, `unknown`, `strb r1, [r0, #0x88]; bx lr`)
7. `func_0037dad0`: `0x0037dad0` (8 B, `unknown`, `strb r1, [r0, #0x85]; bx lr`)
8. `func_00381464`: `0x00381464` (8 B, `unknown`, `mov r0, r0; bx lr`)
9. `func_003ad7fc`: `0x003ad7fc` (8 B, `unknown`, `ldrsb r0, [r0, #0x10]; bx lr`)

- [ ] **Step 1: Write declarations in `include/engine/leaf_matching.h` and implementations in `src/engine/leaf_matching.cpp`**
- [ ] **Step 2: Update status in `config/functions.csv` to `matching`**
- [ ] **Step 3: Update `test_asm_diff.py` and `test_progress.py` expectations for +9 matching functions (+72 bytes)**
- [ ] **Step 4: Verify all 9 functions pass `compare_function` exact byte match and tests pass**
- [ ] **Step 5: Commit changes**

---

### Task 2: Decompile and Match 50 12-Byte Leaf Functions (50 Functions, 600 Bytes)

**Files:**
- Modify: `include/engine/leaf_matching.h`
- Modify: `src/engine/leaf_matching.cpp`
- Modify: `config/functions.csv`
- Modify: `tests/test_asm_diff.py`
- Modify: `tests/test_progress.py`

**Functions (50 verified 12-byte leaf functions):**
- Group A (Constant stores & byte stores):
  - `func_0011cbf4`, `func_0014bef8`, `func_0014dbc4`, `func_001b1a7c`, `func_00207c00`, `func_002abde8`, `func_002aecd8`, `func_002b5058`, `func_002e8124`, `func_00368860`, `func_0036fb34`, `func_0036ff08`, `func_00379afc`, `func_00379b08`, `func_00379c08`, `func_00379ed4`, `func_0038c2a0`
- Group B (Relative offset calculations):
  - `func_0014d040`, `func_0014d26c`, `func_0014d278`, `func_0014d284`, `func_0014d4c0`, `func_00152170`, `func_001521a4`, `func_001557b0`, `func_003e6374`, `func_003e6a80`, `func_003e6b74`, `func_003e84b8`, `func_003e8840`
- Group C (Chained pointer accessors & field getters/setters):
  - `func_001e18d0`, `func_002cd964`, `func_002d17e8`, `func_002d18bc`, `func_002dacf0`, `func_002f345c`, `func_00362368`, `func_003e89ec`, `func_003e8a0c`, `func_003e8a7c`, `func_003ea358`, `func_003ea4c4`
- Group D (Vector / Vec4 copies):
  - `func_002c7084`, `func_002dd080`, `func_002f3450`, `func_002f98e0`, `func_002faf08`, `func_00302764`, `func_00315960`, `func_0031ab34`

- [ ] **Step 1: Add declarations to `include/engine/leaf_matching.h`**
- [ ] **Step 2: Add implementations with `// DECOMP_FUNC` markers to `src/engine/leaf_matching.cpp`**
- [ ] **Step 3: Update `config/functions.csv` rows to `matching`**
- [ ] **Step 4: Update test assertions in `tests/test_asm_diff.py` and `tests/test_progress.py`**
- [ ] **Step 5: Run tests and verify 100% exact match on all 50 functions**
- [ ] **Step 6: Commit changes**

---

### Task 3: Refresh Progress Ledger, Documentation, and Full Test Suite Verification

**Files:**
- Modify: `PROGRESS.md`
- Modify: `README.md`
- Test: Full `pytest` suite

- [ ] **Step 1: Run `python tools/progress.py --write` to update `PROGRESS.md` and `README.md`**
- [ ] **Step 2: Run full test suite (`pytest`) to ensure 42/42 tests pass with zero warnings**
- [ ] **Step 3: Verify git status is clean and commit changes**
- [ ] **Step 4: Push branch to GitHub remote (`git push origin main`)**
