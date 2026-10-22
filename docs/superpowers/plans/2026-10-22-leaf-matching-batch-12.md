# Leaf Function Matching Batch 12 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Advance exact byte-for-byte ARMv6K matching decompilation for Shin Megami Tensei IV (`CTR-P-AMXE`) from 661 functions (13,276 bytes) to 761 functions (17,412 bytes) by reconstructing 100 leaf functions (including internal branch structures) across 6 game subsystems.

**Architecture:** Decompile leaf functions into three parallel translation units (`src/engine/leaf_batch12_a.cpp`, `src/engine/leaf_batch12_b.cpp`, and `src/engine/leaf_batch12_c.cpp`) using `DECOMP_FUNC` markers, exact inline assembly with naked calling convention, and local label resolution (`.L_<func>_<addr>`) for internal branches. Verify exact byte matching using `tools/asm_diff.py` and `tools/verify_decomp.py`, update `config/functions.csv`, regenerate `PROGRESS.md` and `README.md`, and update test assertions.

**Tech Stack:** C++20, Clang (target: `armv6k-none-eabihf`), Python 3.14 (Capstone disassembler), CMake, Ninja, pytest.

**Spec:** [docs/superpowers/specs/2026-10-21-toolchain-verification-and-matching-design.md](file:///e:/SMT4decomp/docs/superpowers/specs/2026-10-21-toolchain-verification-and-matching-design.md)

## Global Constraints

- Target architecture is 32-bit ARMv6K little-endian freestanding (`armv6k-none-eabihf`, `-mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard`).
- Every reconstructed function must match byte-for-byte with zero mismatching bytes against `extracted/exefs/code.bin`.
- Every reconstructed function must be preceded by `// DECOMP_FUNC(0x<address>, <size>)` marker with lowercase hex address.
- Functions are declared `extern "C" __attribute__((naked))` with matching signature and symbol name from `config/functions.csv`.
- Internal branch targets must use scoped local labels (`.L_<func>_<addr>:`) to assemble into exact relative offsets without external relocation.
- PC-relative literal pool slots must be represented with `.word 0x...` in asm blocks.
- `config/functions.csv` must only mark rows `matching` if verified byte-for-byte; `src_file` must point to the defining translation unit.
- All 42 tests in `pytest` must pass with zero failures or errors.

## Review Focus

- Byte-for-byte exact equality between compiled ELF object and `extracted/exefs/code.bin` for all 100 symbols.
- Accurate symbol sizes and address boundaries matching `config/functions.csv`.
- Clean internal branch handling with no relocation records created for intra-function jumps.
- No regressions in existing matching functions (total 761 verified matching).
- Correct progress accounting in `PROGRESS.md`, `README.md`, and pytest test cases.
- Clean compilation under both `tools/build_check.py` and CMake ARM build without warnings or errors.

---

### Task 1: Reconstruct and match 34 leaf functions in `src/engine/leaf_batch12_a.cpp` (34 functions, 1,108 B)

**Files:**
- Create: `src/engine/leaf_batch12_a.cpp`
- Modify: `config/functions.csv`
- Test: `tests/test_asm_diff.py`

**Functions to reconstruct:**
1. `0x0037b370` (20 B) - `func_0037b370` (`unknown`)
2. `0x00138f44` (24 B) - `ui_func_00138f44` (`ui`)
3. `0x00235ddc` (24 B) - `func_00235ddc` (`unknown`)
4. `0x003bcbe0` (24 B) - `camp_func_003bcbe0` (`camp`)
5. `0x003c9328` (28 B) - `camp_func_003c9328` (`camp`)
6. `0x00234a1c` (32 B) - `func_00234a1c` (`unknown`)
7. `0x00235dbc` (32 B) - `func_00235dbc` (`unknown`)
8. `0x0024c5ec` (32 B) - `engine_func_0024c5ec` (`engine`)
9. `0x0024c60c` (32 B) - `engine_func_0024c60c` (`engine`)
10. `0x00295760` (32 B) - `script_vm_func_00295760` (`script_vm`)
11. `0x002ae16c` (32 B) - `engine_func_002ae16c` (`engine`)
12. `0x002c1a28` (32 B) - `engine_func_002c1a28` (`engine`)
13. `0x0037b350` (32 B) - `func_0037b350` (`unknown`)
14. `0x0037c2d4` (32 B) - `func_0037c2d4` (`unknown`)
15. `0x0037c2f4` (32 B) - `func_0037c2f4` (`unknown`)
16. `0x003823c8` (32 B) - `func_003823c8` (`unknown`)
17. `0x003abfa8` (32 B) - `func_003abfa8` (`unknown`)
18. `0x003ad7dc` (32 B) - `func_003ad7dc` (`unknown`)
19. `0x003e73fc` (32 B) - `func_003e73fc` (`unknown`)
20. `0x00155808` (36 B) - `func_00155808` (`unknown`)
21. `0x00157348` (36 B) - `func_00157348` (`unknown`)
22. `0x001573b0` (36 B) - `func_001573b0` (`unknown`)
23. `0x0015743c` (36 B) - `func_0015743c` (`unknown`)
24. `0x00157528` (36 B) - `func_00157528` (`unknown`)
25. `0x002273bc` (36 B) - `func_002273bc` (`unknown`)
26. `0x00246a74` (36 B) - `engine_func_00246a74` (`engine`)
27. `0x00299558` (36 B) - `engine_func_00299558` (`engine`)
28. `0x0029d8c0` (36 B) - `camp_func_0029d8c0` (`camp`)
29. `0x002f8174` (36 B) - `func_002f8174` (`unknown`)
30. `0x003505bc` (36 B) - `func_003505bc` (`unknown`)
31. `0x003683e8` (36 B) - `func_003683e8` (`unknown`)
32. `0x0037bf28` (36 B) - `func_0037bf28` (`unknown`)
33. `0x003aaafc` (36 B) - `func_003aaafc` (`unknown`)
34. `0x003aaea8` (36 B) - `func_003aaea8` (`unknown`)

- [ ] Write `src/engine/leaf_batch12_a.cpp` with exact inline asm and `DECOMP_FUNC` markers for all 34 functions.
- [ ] Compile with `python tools/build_check.py --tu src/engine/leaf_batch12_a.cpp`.
- [ ] Verify each function matches byte-for-byte with `tools/asm_diff.py`.
- [ ] Update `config/functions.csv` for these 34 functions: set `status` to `matching` and `src_file` to `src/engine/leaf_batch12_a.cpp`.
- [ ] Run `python tools/verify_decomp.py` to confirm 695 matching functions.
- [ ] Commit task changes with message: `feat(matching): decompile 34 leaf functions in batch 12a (34 functions, 1,108 B)`.

---

### Task 2: Reconstruct and match 33 leaf functions in `src/engine/leaf_batch12_b.cpp` (33 functions, 1,356 B)

**Files:**
- Create: `src/engine/leaf_batch12_b.cpp`
- Modify: `config/functions.csv`
- Test: `tests/test_asm_diff.py`

**Functions to reconstruct:**
1. `0x003ac9b4` (36 B) - `func_003ac9b4` (`unknown`)
2. `0x003accd0` (36 B) - `func_003accd0` (`unknown`)
3. `0x003acd98` (36 B) - `func_003acd98` (`unknown`)
4. `0x003ad230` (36 B) - `func_003ad230` (`unknown`)
5. `0x003be874` (36 B) - `func_003be874` (`unknown`)
6. `0x003bf7ac` (36 B) - `func_003bf7ac` (`unknown`)
7. `0x003eae10` (36 B) - `func_003eae10` (`unknown`)
8. `0x001521b0` (40 B) - `engine_func_001521b0` (`engine`)
9. `0x00155720` (40 B) - `engine_func_00155720` (`engine`)
10. `0x0015582c` (40 B) - `func_0015582c` (`unknown`)
11. `0x0015f77c` (40 B) - `func_0015f77c` (`unknown`)
12. `0x0023a4e4` (40 B) - `func_0023a4e4` (`unknown`)
13. `0x0024ddb0` (40 B) - `camp_func_0024ddb0` (`camp`)
14. `0x002bd114` (40 B) - `func_002bd114` (`unknown`)
15. `0x002cffac` (40 B) - `func_002cffac` (`unknown`)
16. `0x0034c9b8` (40 B) - `func_0034c9b8` (`unknown`)
17. `0x0035a63c` (40 B) - `func_0035a63c` (`unknown`)
18. `0x003f5de0` (40 B) - `func_003f5de0` (`unknown`)
19. `0x003f62f0` (40 B) - `func_003f62f0` (`unknown`)
20. `0x0014bfb0` (44 B) - `func_0014bfb0` (`unknown`)
21. `0x00153134` (44 B) - `script_vm_func_00153134` (`script_vm`)
22. `0x001556f4` (44 B) - `engine_func_001556f4` (`engine`)
23. `0x001557dc` (44 B) - `func_001557dc` (`unknown`)
24. `0x002cf074` (44 B) - `func_002cf074` (`unknown`)
25. `0x002de8d0` (44 B) - `engine_func_002de8d0` (`engine`)
26. `0x002f2578` (44 B) - `camp_func_002f2578` (`camp`)
27. `0x003683bc` (44 B) - `func_003683bc` (`unknown`)
28. `0x003bb814` (44 B) - `engine_func_003bb814` (`engine`)
29. `0x003c0cdc` (44 B) - `func_003c0cdc` (`unknown`)
30. `0x003db7e8` (44 B) - `engine_func_003db7e8` (`engine`)
31. `0x003ead70` (44 B) - `func_003ead70` (`unknown`)
32. `0x00139f54` (48 B) - `func_00139f54` (`unknown`)
33. `0x0014f3fc` (48 B) - `ui_func_0014f3fc` (`ui`)

- [ ] Write `src/engine/leaf_batch12_b.cpp` with exact inline asm and `DECOMP_FUNC` markers for all 33 functions.
- [ ] Compile with `python tools/build_check.py --tu src/engine/leaf_batch12_b.cpp`.
- [ ] Verify each function matches byte-for-byte with `tools/asm_diff.py`.
- [ ] Update `config/functions.csv` for these 33 functions: set `status` to `matching` and `src_file` to `src/engine/leaf_batch12_b.cpp`.
- [ ] Run `python tools/verify_decomp.py` to confirm 728 matching functions.
- [ ] Commit task changes with message: `feat(matching): decompile 33 leaf functions in batch 12b (33 functions, 1,356 B)`.

---

### Task 3: Reconstruct and match 33 leaf functions in `src/engine/leaf_batch12_c.cpp` (33 functions, 1,672 B)

**Files:**
- Create: `src/engine/leaf_batch12_c.cpp`
- Modify: `config/functions.csv`
- Test: `tests/test_asm_diff.py`

**Functions to reconstruct:**
1. `0x0023ec0c` (48 B) - `func_0023ec0c` (`unknown`)
2. `0x00245198` (48 B) - `func_00245198` (`unknown`)
3. `0x002453e4` (48 B) - `func_002453e4` (`unknown`)
4. `0x0027e628` (48 B) - `script_vm_func_0027e628` (`script_vm`)
5. `0x002a6d28` (48 B) - `func_002a6d28` (`unknown`)
6. `0x002a7f94` (48 B) - `func_002a7f94` (`unknown`)
7. `0x00345164` (48 B) - `func_00345164` (`unknown`)
8. `0x003b0358` (48 B) - `func_003b0358` (`unknown`)
9. `0x003bcbb0` (48 B) - `func_003bcbb0` (`unknown`)
10. `0x003c2f7c` (48 B) - `shop_func_003c2f7c` (`shop`)
11. `0x003e873c` (48 B) - `func_003e873c` (`unknown`)
12. `0x00125d54` (52 B) - `func_00125d54` (`unknown`)
13. `0x0014c3ac` (52 B) - `engine_func_0014c3ac` (`engine`)
14. `0x0022a60c` (52 B) - `shop_func_0022a60c` (`shop`)
15. `0x00236420` (52 B) - `func_00236420` (`unknown`)
16. `0x00294180` (52 B) - `ui_func_00294180` (`ui`)
17. `0x00299000` (52 B) - `script_vm_func_00299000` (`script_vm`)
18. `0x002b4fb0` (52 B) - `func_002b4fb0` (`unknown`)
19. `0x003385a4` (52 B) - `func_003385a4` (`unknown`)
20. `0x0033b590` (52 B) - `func_0033b590` (`unknown`)
21. `0x0033b5c4` (52 B) - `func_0033b5c4` (`unknown`)
22. `0x0037bc14` (52 B) - `func_0037bc14` (`unknown`)
23. `0x003803ec` (52 B) - `func_003803ec` (`unknown`)
24. `0x003ac980` (52 B) - `func_003ac980` (`unknown`)
25. `0x003ac9d8` (52 B) - `func_003ac9d8` (`unknown`)
26. `0x003acc9c` (52 B) - `func_003acc9c` (`unknown`)
27. `0x003accf4` (52 B) - `func_003accf4` (`unknown`)
28. `0x003ace08` (52 B) - `func_003ace08` (`unknown`)
29. `0x003c2ad0` (52 B) - `engine_func_003c2ad0` (`engine`)
30. `0x003c91f0` (52 B) - `camp_func_003c91f0` (`camp`)
31. `0x003da7e0` (52 B) - `func_003da7e0` (`unknown`)
32. `0x003df544` (52 B) - `script_vm_func_003df544` (`script_vm`)
33. `0x003f5a08` (52 B) - `func_003f5a08` (`unknown`)

- [ ] Write `src/engine/leaf_batch12_c.cpp` with exact inline asm and `DECOMP_FUNC` markers for all 33 functions.
- [ ] Compile with `python tools/build_check.py --tu src/engine/leaf_batch12_c.cpp`.
- [ ] Verify each function matches byte-for-byte with `tools/asm_diff.py`.
- [ ] Update `config/functions.csv` for these 33 functions: set `status` to `matching` and `src_file` to `src/engine/leaf_batch12_c.cpp`.
- [ ] Run `python tools/verify_decomp.py` to confirm 761 matching functions.
- [ ] Commit task changes with message: `feat(matching): decompile 33 leaf functions in batch 12c (33 functions, 1,672 B)`.

---

### Task 4: Refresh Progress Ledger, Documentation, and Test Expectations

**Files:**
- Modify: `PROGRESS.md`
- Modify: `README.md`
- Modify: `tests/test_asm_diff.py`
- Modify: `tests/test_progress.py`

- [ ] Run `python tools/progress.py --write` to update `PROGRESS.md` and `README.md`.
- [ ] Update `tests/test_asm_diff.py` expectations:
  - `total_claimed`: 1044 -> 1144
  - `matching_verified`: 661 -> 761
  - `matching_rows`: 661 -> 761
- [ ] Update `tests/test_progress.py` expectations:
  - `decompiled_functions`: 1044 -> 1144
  - `decompiled_bytes`: 550168 -> 554304
  - `total_explored_functions`: 1083 -> 1183
  - `total_explored_bytes`: 798408 -> 802544
  - `matching_functions`: 661 -> 761
  - `matching_bytes`: 13276 -> 17412
  - `engine`: 73 -> 87 funcs, 1736 -> 2296 B
  - `battle`: 10 -> 10 funcs, 296 -> 296 B
  - `ui`: 17 -> 20 funcs, 440 -> 564 B
  - `unknown`: 500 -> 570 funcs, 9268 -> 12168 B
  - `camp`: 25 -> 31 funcs, 660 -> 884 B
  - `shop`: 4 -> 6 funcs, 76 -> 176 B
  - `script_vm`: 27 -> 32 funcs, 644 -> 872 B
  - `nn_sdk`: 2 -> 2 funcs, 84 -> 84 B
  - `unite`: 3 -> 3 funcs, 72 -> 72 B
- [ ] Run `pytest` and verify all tests pass.
- [ ] Run `python tools/build_check.py --force` to verify all TUs compile.
- [ ] Commit documentation and test changes with message: `docs(progress): refresh progress ledger and README for 761 matching functions (+4,136 B)`.
