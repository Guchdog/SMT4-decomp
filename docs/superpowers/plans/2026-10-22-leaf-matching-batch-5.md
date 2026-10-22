# Exact Leaf Matching Batch 5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile and verify 50 leaf functions (20 12-byte and 30 16-byte functions, totaling 720 bytes) to 100% byte-for-byte `matching` machine code against `extracted/exefs/code.bin`, expanding matching coverage across `battle`, `engine`, `ui`, `script_vm`, and `unknown` subsystems to 311 functions (2,824 bytes).

**Architecture:**
- `include/engine/leaf_matching.h`: Expose C-linkage declarations for the 50 newly matched functions.
- `src/engine/leaf_matching.cpp`: Implement all 50 functions with exact ARMv6K object code generation and `// DECOMP_FUNC(0xXXXXXXXX, size)` markers.
- `config/functions.csv`: Update row statuses to `matching` with `src/engine/leaf_matching.cpp`.
- `tools/progress.py`, `PROGRESS.md`, `README.md`: Refresh the progress ledger.
- `tests/test_asm_diff.py`, `tests/test_progress.py`: Update test suites to assert exact byte-for-byte identity on all 311 matching rows.

**Tech Stack:** C++20, LLVM/Clang (`--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2`), Capstone ARM disassembler, Python 3 / Pytest.

**Spec:** `docs/superpowers/specs/2026-10-21-toolchain-verification-and-matching-design.md`

## Global Constraints

- Target binary: `extracted/exefs/code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- All functions must compile cleanly with Clang targeting `armv6k-none-eabihf` (`-mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -fno-exceptions -fno-rtti`).
- Every function claimed as `matching` must pass `tools.asm_diff.compare_function()` with `exact_match == True` (100% byte-for-byte equivalence).
- Every function in `src/engine/leaf_matching.cpp` must be preceded by `// DECOMP_FUNC(0xXXXXXXXX, size)` matching the ledger address and size.
- Maintain documentation integrity and strict TDD verification.

## Review Focus

- Correct parameter passing and sign/zero extension for narrow loads.
- Proper memory clobbers on inline assembly for vector copies and store-multiple (`stm`) operations.
- Accurate ledger accounting in `config/functions.csv` preserving exact addresses and sizes.
- Verification that all 311 matching functions and overall architecture stats remain strictly consistent.

---

### Task 1: Decompile and Match 20 12-Byte Leaf Functions (20 Functions, 240 Bytes)

**Files:**
- Modify: `include/engine/leaf_matching.h`
- Modify: `src/engine/leaf_matching.cpp`
- Modify: `config/functions.csv`
- Modify: `tests/test_asm_diff.py`
- Modify: `tests/test_progress.py`

**Functions (20 12-byte functions):**
1. `func_001328f8`: `0x001328f8` (12 B, `unknown`)
2. `func_001579c0`: `0x001579c0` (12 B, `unknown`)
3. `func_00158784`: `0x00158784` (12 B, `unknown`)
4. `ui_func_00131414`: `0x00131414` (12 B, `ui`)
5. `func_0023347c`: `0x0023347c` (12 B, `unknown`)
6. `script_vm_func_00292e88`: `0x00292e88` (12 B, `script_vm`)
7. `func_0031b9a0`: `0x0031b9a0` (12 B, `unknown`)
8. `func_0031f6b8`: `0x0031f6b8` (12 B, `unknown`)
9. `func_0031f6c4`: `0x0031f6c4` (12 B, `unknown`)
10. `func_0034f610`: `0x0034f610` (12 B, `unknown`)
11. `func_00350cc8`: `0x00350cc8` (12 B, `unknown`)
12. `func_0037981c`: `0x0037981c` (12 B, `unknown`)
13. `func_0037dac4`: `0x0037dac4` (12 B, `unknown`)
14. `func_0037fd88`: `0x0037fd88` (12 B, `unknown`)
15. `func_003e7430`: `0x003e7430` (12 B, `unknown`)
16. `func_003ea24c`: `0x003ea24c` (12 B, `unknown`)
17. `func_003f5a68`: `0x003f5a68` (12 B, `unknown`)
18. `func_003f5e34`: `0x003f5e34` (12 B, `unknown`)
19. `func_003f635c`: `0x003f635c` (12 B, `unknown`)
20. `func_003f6800`: `0x003f6800` (12 B, `unknown`)

- [ ] **Step 1: Add declarations to `include/engine/leaf_matching.h`**
- [ ] **Step 2: Add implementations with `// DECOMP_FUNC` markers to `src/engine/leaf_matching.cpp`**
- [ ] **Step 3: Update `config/functions.csv` rows to `matching`**
- [ ] **Step 4: Update test assertions in `tests/test_asm_diff.py` and `tests/test_progress.py`**
- [ ] **Step 5: Run tests and verify 100% exact match on all 20 functions**
- [ ] **Step 6: Commit changes**

---

### Task 2: Decompile and Match 30 16-Byte Leaf Functions (30 Functions, 480 Bytes)

**Files:**
- Modify: `include/engine/leaf_matching.h`
- Modify: `src/engine/leaf_matching.cpp`
- Modify: `config/functions.csv`
- Modify: `tests/test_asm_diff.py`
- Modify: `tests/test_progress.py`

**Functions (30 16-byte functions):**
1. `func_0010f464`: `0x0010f464` (16 B, `unknown`)
2. `func_001215dc`: `0x001215dc` (16 B, `unknown`)
3. `func_00150e28`: `0x00150e28` (16 B, `unknown`)
4. `func_0023a774`: `0x0023a774` (16 B, `unknown`)
5. `script_vm_func_002912f4`: `0x002912f4` (16 B, `script_vm`)
6. `battle_func_002ae464`: `0x002ae464` (16 B, `battle`)
7. `engine_func_002b0408`: `0x002b0408` (16 B, `engine`)
8. `func_002b8574`: `0x002b8574` (16 B, `unknown`)
9. `func_002b90c0`: `0x002b90c0` (16 B, `unknown`)
10. `func_002b90d0`: `0x002b90d0` (16 B, `unknown`)
11. `func_002b90f0`: `0x002b90f0` (16 B, `unknown`)
12. `engine_func_002bf85c`: `0x002bf85c` (16 B, `engine`)
13. `ui_func_002c4bf0`: `0x002c4bf0` (16 B, `ui`)
14. `func_002c6eb0`: `0x002c6eb0` (16 B, `unknown`)
15. `func_002c8698`: `0x002c8698` (16 B, `unknown`)
16. `ui_func_002d567c`: `0x002d567c` (16 B, `ui`)
17. `func_002df400`: `0x002df400` (16 B, `unknown`)
18. `func_002e8114`: `0x002e8114` (16 B, `unknown`)
19. `func_002e8284`: `0x002e8284` (16 B, `unknown`)
20. `func_002f3280`: `0x002f3280` (16 B, `unknown`)
21. `func_00304154`: `0x00304154` (16 B, `unknown`)
22. `func_0030f234`: `0x0030f234` (16 B, `unknown`)
23. `func_00348ab0`: `0x00348ab0` (16 B, `unknown`)
24. `func_0035c64c`: `0x0035c64c` (16 B, `unknown`)
25. `func_0035cd7c`: `0x0035cd7c` (16 B, `unknown`)
26. `func_0035d1e4`: `0x0035d1e4` (16 B, `unknown`)
27. `func_00379bd4`: `0x00379bd4` (16 B, `unknown`)
28. `func_00379c14`: `0x00379c14` (16 B, `unknown`)
29. `func_003842f4`: `0x003842f4` (16 B, `unknown`)
30. `func_00396250`: `0x00396250` (16 B, `unknown`)

- [ ] **Step 1: Add declarations to `include/engine/leaf_matching.h`**
- [ ] **Step 2: Add implementations with `// DECOMP_FUNC` markers to `src/engine/leaf_matching.cpp`**
- [ ] **Step 3: Update `config/functions.csv` rows to `matching`**
- [ ] **Step 4: Update test assertions in `tests/test_asm_diff.py` and `tests/test_progress.py`**
- [ ] **Step 5: Run tests and verify 100% exact match on all 30 functions**
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
