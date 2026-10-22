# Implementation Plan: Leaf Function Matching Batch 7 (50 Functions, 956 Bytes)

## Goal
Decompile and byte-match 50 additional ARMv6K leaf functions in Shin Megami Tensei IV (`CTR-P-AMXE`), advancing matching coverage from **361 functions (3,572 bytes)** to **411 functions (4,528 bytes)** across 8 game subsystems (`camp`, `battle`, `shop`, `unite`, `script_vm`, `ui`, `engine`, `unknown`), strictly maintaining 100% exact byte matching against `extracted/exefs/code.bin` and zero regressions across the 42-test pytest suite.

---

## Proposed Changes

### 1. Prototypes Header: `include/engine/leaf_matching.h`
Add `extern "C"` declarations for all 50 Batch 7 functions:
- Task 1: 25 functions (5 12B, 11 16B, 9 20B; 416 B)
- Task 2: 25 functions (15 20B, 10 24B; 540 B)

### 2. Implementation: `src/engine/leaf_matching.cpp`
Implement the 50 functions with preceding `// DECOMP_FUNC(0xXXXXXXXX, size)` markers.

### 3. Symbol Ledger: `config/functions.csv`
Update the 50 corresponding rows from `status = todo` to `status = matching`, with `src_file = src/engine/leaf_matching.cpp`.

### 4. Tests: `tests/test_asm_diff.py` & `tests/test_progress.py`
Update assertions for the new matching counts and byte sizes:
- Total matching functions: 361 -> 411 (+50)
- Total matching bytes: 3,572 -> 4,528 (+956 B)
- Explored functions: 783 -> 833 (+50)
- Explored bytes: 788,704 -> 789,660 (+956 B)
- Decompiled functions: 744 -> 794 (+50)
- Decompiled bytes: 540,464 -> 541,420 (+956 B)
- Category breakdown:
  - `unknown`: 310 -> 328 funcs (+18), 2,832 -> 3,164 B (+332 B)
  - `engine`: 31 -> 42 funcs (+11), 472 -> 704 B (+232 B)
  - `script_vm`: 7 -> 14 funcs (+7), 92 -> 208 B (+116 B)
  - `camp`: 2 -> 7 funcs (+5), 28 -> 136 B (+108 B)
  - `ui`: 7 -> 11 funcs (+4), 96 -> 160 B (+64 B)
  - `battle`: 2 -> 4 funcs (+2), 28 -> 68 B (+40 B)
  - `shop`: 1 -> 3 funcs (+2), 12 -> 52 B (+40 B)
  - `unite`: 1 -> 2 funcs (+1), 12 -> 36 B (+24 B)

### 5. Progress Documentation: `PROGRESS.md` & `README.md`
Run `python tools/progress.py --write` to update progress tables and metrics.

---

## Task Breakdown

### Task 1: Decompile & Match 25 Leaf Functions (25 Functions, 416 B)
- Functions: `func_00138288`, `script_vm_func_002bda10`, `ui_func_00343550`, `func_00343584`, `func_00343590`, `script_vm_func_002668cc`, `script_vm_func_00293a74`, `engine_func_002a17d4`, `script_vm_func_002a3098`, `func_002a3428`, `func_002ae2b4`, `script_vm_func_002b90e0`, `ui_func_002bda00`, `ui_func_002c1774`, `func_0036f990`, `func_003811fc`, `func_001ae2f0`, `func_00231d4c`, `func_00232b00`, `func_00232b14`, `func_00232b28`, `shop_func_00233584`, `engine_func_0023378c`, `func_00235924`, `func_00237efc`.
- Updates: `leaf_matching.h`, `leaf_matching.cpp`, `functions.csv`, `test_asm_diff.py`, `test_progress.py`.
- Verification: `pytest tests/test_asm_diff.py tests/test_progress.py`.

### Task 2: Decompile & Match 25 Leaf Functions (25 Functions, 540 B)
- Functions: `shop_func_00240ea4`, `func_0024faa4`, `battle_func_0026e88c`, `engine_func_0027e9d0`, `camp_func_0027ec84`, `engine_func_0028757c`, `engine_func_00287958`, `camp_func_0029e3bc`, `camp_func_0029ee4c`, `engine_func_002a17c0`, `script_vm_func_002a704c`, `engine_func_002a7fc4`, `battle_func_002a84bc`, `ui_func_002adb40`, `script_vm_func_002bd9ec`, `engine_func_00110c2c`, `engine_func_00121150`, `func_001220ec`, `engine_func_001384b8`, `func_0013fe34`, `engine_func_001524d0`, `func_0017f910`, `unite_func_002338ac`, `camp_func_0027edf8`, `camp_func_0028c124`.
- Updates: `leaf_matching.h`, `leaf_matching.cpp`, `functions.csv`, `test_asm_diff.py`, `test_progress.py`.
- Verification: `pytest tests/test_asm_diff.py tests/test_progress.py`.

### Task 3: Refresh Progress Ledger, Documentation, and Git Remote Push
- Run `python tools/progress.py --write`.
- Run full `pytest` suite (42 tests).
- Commit docs and push `main` to `origin/main`.
- Whole-branch review.
