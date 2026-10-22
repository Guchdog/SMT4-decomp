# Leaf Function Matching Batch 11 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Advance exact byte-for-byte ARMv6K matching decompilation for Shin Megami Tensei IV (`CTR-P-AMXE`) from 611 functions (10,368 bytes) to 661 functions (13,276 bytes) by reconstructing 50 pure leaf functions across 7 game subsystems.

**Architecture:** Decompile pure leaf functions into standalone translation units (`src/engine/leaf_batch11_a.cpp` and `src/engine/leaf_batch11_b.cpp`) using `DECOMP_FUNC` markers and exact inline assembly with naked calling convention. Verify exact byte matching using `tools/asm_diff.py` and `tools/verify_decomp.py`, update `config/functions.csv`, regenerate `PROGRESS.md` and `README.md`, and update test assertions.

**Tech Stack:** C++20, Clang (target: `armv6k-none-eabihf`), Python 3.14 (Capstone disassembler), CMake, Ninja, pytest.

**Spec:** [docs/superpowers/specs/2026-10-21-toolchain-verification-and-matching-design.md](file:///e:/SMT4decomp/docs/superpowers/specs/2026-10-21-toolchain-verification-and-matching-design.md)

## Global Constraints

- Target architecture is 32-bit ARMv6K little-endian freestanding (`armv6k-none-eabihf`, `-mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard`).
- Every reconstructed function must match byte-for-byte with zero mismatching bytes against `extracted/exefs/code.bin`.
- Every reconstructed function must be preceded by `// DECOMP_FUNC(0x<address>, <size>)` marker with lowercase hex address.
- Functions are declared `extern "C" __attribute__((naked))` with matching signature and symbol name from `config/functions.csv`.
- PC-relative literal pool slots must be represented with `.word 0x...` in asm blocks.
- `config/functions.csv` must only mark rows `matching` if verified byte-for-byte; `src_file` must point to the defining translation unit.
- All 42 tests in `pytest` must pass with zero failures or errors.

## Review Focus

- Byte-for-byte exact equality between compiled ELF object and `extracted/exefs/code.bin` for all 50 symbols.
- Accurate symbol sizes and address boundaries matching `config/functions.csv`.
- No regressions in existing matching functions (total 661 verified matching).
- Correct progress accounting in `PROGRESS.md`, `README.md`, and pytest test cases.
- Clean compilation under both `tools/build_check.py` and CMake ARM build without warnings or errors.

---

### Task 1: Reconstruct and match 25 leaf functions in `src/engine/leaf_batch11_a.cpp` (25 functions, 1,252 B)

**Files:**
- Create: `src/engine/leaf_batch11_a.cpp`
- Modify: `config/functions.csv`
- Test: `tests/test_asm_diff.py`

**Functions to reconstruct:**
1. `0x003b00b4` (44 B) - `func_003b00b4` (`unknown`)
2. `0x003e8ad4` (44 B) - `func_003e8ad4` (`unknown`)
3. `0x003f8808` (44 B) - `func_003f8808` (`unknown`)
4. `0x003f88e4` (44 B) - `func_003f88e4` (`unknown`)
5. `0x003f89cc` (44 B) - `func_003f89cc` (`unknown`)
6. `0x001dd7b8` (48 B) - `func_001dd7b8` (`unknown`)
7. `0x00227dc4` (48 B) - `func_00227dc4` (`unknown`)
8. `0x002a260c` (48 B) - `func_002a260c` (`unknown`)
9. `0x002b49a0` (48 B) - `engine_func_002b49a0` (`engine`)
10. `0x003811cc` (48 B) - `func_003811cc` (`unknown`)
11. `0x0015a2ec` (52 B) - `func_0015a2ec` (`unknown`)
12. `0x001a083c` (52 B) - `func_001a083c` (`unknown`)
13. `0x002263a0` (52 B) - `func_002263a0` (`unknown`)
14. `0x0023d368` (52 B) - `func_0023d368` (`unknown`)
15. `0x0023d39c` (52 B) - `func_0023d39c` (`unknown`)
16. `0x0023e55c` (52 B) - `func_0023e55c` (`unknown`)
17. `0x002a1a08` (52 B) - `func_002a1a08` (`unknown`)
18. `0x002a7060` (52 B) - `func_002a7060` (`unknown`)
19. `0x002a8a58` (52 B) - `engine_func_002a8a58` (`engine`)
20. `0x0035bbc4` (52 B) - `func_0035bbc4` (`unknown`)
21. `0x0035c00c` (52 B) - `func_0035c00c` (`unknown`)
22. `0x0035c2f8` (52 B) - `func_0035c2f8` (`unknown`)
23. `0x0014720c` (56 B) - `func_0014720c` (`unknown`)
24. `0x001a0870` (56 B) - `func_001a0870` (`unknown`)
25. `0x0023d5ac` (56 B) - `camp_func_0023d5ac` (`camp`)

- [ ] Write `src/engine/leaf_batch11_a.cpp` with exact inline asm and `DECOMP_FUNC` markers for all 25 functions.
- [ ] Compile with `python tools/build_check.py --tu src/engine/leaf_batch11_a.cpp`.
- [ ] Verify each function matches byte-for-byte with `tools/asm_diff.py`.
- [ ] Update `config/functions.csv` for these 25 functions: set `status` to `matching` and `src_file` to `src/engine/leaf_batch11_a.cpp`.
- [ ] Run `python tools/verify_decomp.py` to confirm 636 matching functions.
- [ ] Commit task changes with message: `feat(matching): decompile 25 leaf functions in batch 11a (25 functions, 1,252 B)`.

---

### Task 2: Reconstruct and match 25 leaf functions in `src/engine/leaf_batch11_b.cpp` (25 functions, 1,656 B)

**Files:**
- Create: `src/engine/leaf_batch11_b.cpp`
- Modify: `config/functions.csv`
- Test: `tests/test_asm_diff.py`

**Functions to reconstruct:**
1. `0x002a1a90` (56 B) - `func_002a1a90` (`unknown`)
2. `0x002a37a4` (56 B) - `func_002a37a4` (`unknown`)
3. `0x002d5644` (56 B) - `camp_func_002d5644` (`camp`)
4. `0x003f61f0` (56 B) - `nn_sdk_func_003f61f0` (`nn_sdk`)
5. `0x0023afb4` (60 B) - `func_0023afb4` (`unknown`)
6. `0x002a4b4c` (60 B) - `func_002a4b4c` (`unknown`)
7. `0x002ad6d8` (60 B) - `battle_func_002ad6d8` (`battle`)
8. `0x00353124` (60 B) - `script_vm_func_00353124` (`script_vm`)
9. `0x003531ac` (60 B) - `script_vm_func_003531ac` (`script_vm`)
10. `0x0015f6d4` (64 B) - `battle_func_0015f6d4` (`battle`)
11. `0x001dc708` (64 B) - `func_001dc708` (`unknown`)
12. `0x00256ed8` (64 B) - `func_00256ed8` (`unknown`)
13. `0x0035b254` (64 B) - `func_0035b254` (`unknown`)
14. `0x0035bf8c` (64 B) - `func_0035bf8c` (`unknown`)
15. `0x002f28f8` (68 B) - `func_002f28f8` (`unknown`)
16. `0x00121ed8` (72 B) - `engine_func_00121ed8` (`engine`)
17. `0x0013d938` (72 B) - `func_0013d938` (`unknown`)
18. `0x00296f18` (72 B) - `ui_func_00296f18` (`ui`)
19. `0x002b7aa8` (72 B) - `ui_func_002b7aa8` (`ui`)
20. `0x00127fe8` (76 B) - `func_00127fe8` (`unknown`)
21. `0x001285c4` (76 B) - `func_001285c4` (`unknown`)
22. `0x0023aff0` (76 B) - `func_0023aff0` (`unknown`)
23. `0x00245e2c` (76 B) - `script_vm_func_00245e2c` (`script_vm`)
24. `0x00286700` (76 B) - `func_00286700` (`unknown`)
25. `0x002a1b4c` (76 B) - `func_002a1b4c` (`unknown`)

- [ ] Write `src/engine/leaf_batch11_b.cpp` with exact inline asm and `DECOMP_FUNC` markers for all 25 functions.
- [ ] Compile with `python tools/build_check.py --tu src/engine/leaf_batch11_b.cpp`.
- [ ] Verify each function matches byte-for-byte with `tools/asm_diff.py`.
- [ ] Update `config/functions.csv` for these 25 functions: set `status` to `matching` and `src_file` to `src/engine/leaf_batch11_b.cpp`.
- [ ] Run `python tools/verify_decomp.py` to confirm 661 matching functions.
- [ ] Commit task changes with message: `feat(matching): decompile 25 leaf functions in batch 11b (25 functions, 1,656 B)`.

---

### Task 3: Refresh Progress Ledger, Documentation, and Test Expectations

**Files:**
- Modify: `PROGRESS.md`
- Modify: `README.md`
- Modify: `tests/test_asm_diff.py`
- Modify: `tests/test_progress.py`

- [ ] Run `python tools/progress.py --write` to update `PROGRESS.md` and `README.md`.
- [ ] Update `tests/test_asm_diff.py` expectations:
  - `total_claimed`: 994 -> 1044
  - `matching_verified`: 611 -> 661
  - `matching_rows`: 611 -> 661
- [ ] Update `tests/test_progress.py` expectations:
  - `decompiled_functions`: 994 -> 1044
  - `decompiled_bytes`: 547260 -> 550168
  - `total_explored_functions`: 1033 -> 1083
  - `total_explored_bytes`: 795500 -> 798408
  - `matching_functions`: 611 -> 661
  - `matching_bytes`: 10368 -> 13276
  - `engine`: 70 -> 73 funcs, 1564 -> 1736 B
  - `battle`: 8 -> 10 funcs, 172 -> 296 B
  - `ui`: 15 -> 17 funcs, 296 -> 440 B
  - `unknown`: 463 -> 500 funcs, 7164 -> 9268 B
  - `camp`: 23 -> 25 funcs, 548 -> 660 B
  - `script_vm`: 24 -> 27 funcs, 448 -> 644 B
  - `nn_sdk`: 1 -> 2 funcs, 28 -> 84 B
- [ ] Run `pytest` and verify all tests pass.
- [ ] Run `python tools/build_check.py --force` to verify all TUs compile.
- [ ] Commit documentation and test changes with message: `docs(progress): refresh progress ledger and README for 661 matching functions (+2,908 B)`.
