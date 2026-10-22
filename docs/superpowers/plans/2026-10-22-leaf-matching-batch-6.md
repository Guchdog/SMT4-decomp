# Implementation Plan: Leaf Function Matching Batch 6 (50 Functions, 748 Bytes)

## Goal
Decompile and byte-match 50 additional ARMv6K leaf functions in Shin Megami Tensei IV (`CTR-P-AMXE`), advancing matching coverage from **311 functions (2,824 bytes)** to **361 functions (3,572 bytes)**, strictly maintaining 100% exact byte matching against `extracted/exefs/code.bin` and zero regressions across the 42-test pytest suite.

---

## Proposed Changes

### 1. Prototypes Header: `include/engine/leaf_matching.h`
Add `extern "C"` declarations for all 50 Batch 6 functions:
- Task 1: 25 functions (24 12-byte functions, 1 16-byte function; 304 B)
- Task 2: 25 functions (14 16-byte functions, 11 20-byte functions; 444 B)

### 2. Implementation: `src/engine/leaf_matching.cpp`
Implement the 50 functions with preceding `// DECOMP_FUNC(0xXXXXXXXX, size)` markers.

### 3. Symbol Ledger: `config/functions.csv`
Update the 50 corresponding rows from `status = todo` to `status = matching`, with `src_file = src/engine/leaf_matching.cpp`.

### 4. Tests: `tests/test_asm_diff.py` & `tests/test_progress.py`
Update assertions for the new matching counts and byte sizes:
- Total matching functions: 311 -> 361 (+50)
- Total matching bytes: 2,824 -> 3,572 (+748 B)
- Explored functions: 733 -> 783 (+50)
- Explored bytes: 787,956 -> 788,704 (+748 B)
- Decompiled functions: 694 -> 744 (+50)
- Decompiled bytes: 539,716 -> 540,464 (+748 B)
- Category breakdown:
  - `unknown`: 276 -> 310 funcs (+34), 2,332 -> 2,832 B (+500 B)
  - `engine`: 20 -> 31 funcs (+11), 292 -> 472 B (+180 B)
  - `script_vm`: 4 -> 7 funcs (+3), 52 -> 92 B (+40 B)
  - `unite`: 0 -> 1 funcs (+1), 0 -> 12 B (+12 B)
  - `ui`: 6 -> 7 funcs (+1), 80 -> 96 B (+16 B)
  - `battle`: 2 funcs, 28 B (unchanged)
  - `camp`: 2 funcs, 28 B (unchanged)
  - `shop`: 1 func, 12 B (unchanged)

### 5. Progress Documentation: `PROGRESS.md` & `README.md`
Run `python tools/progress.py --write` to update progress tables and metrics.

---

## Task Breakdown

### Task 1: Decompile & Match 25 12B/16B Leaf Functions (25 Functions, 304 B)
- Functions:
  - 12B: `func_00121d70`, `func_00144ea0`, `engine_func_0014ec5c`, `func_001575c0`, `func_001579cc`, `func_001584d0`, `func_0018f554`, `script_vm_func_002345f0`, `script_vm_func_002345fc`, `engine_func_002355ac`, `func_0023a478`, `func_0023a50c`, `func_0023a54c`, `func_0024c740`, `func_0024c7b4`, `func_00250614`, `func_0037b94c`, `unite_func_003ad8c0`, `func_003b2404`, `func_003c2b04`, `func_003e6368`, `func_003e884c`, `func_003e8878`, `func_003f6b44`
  - 16B: `engine_func_0011b850`
- Updates: `leaf_matching.h`, `leaf_matching.cpp`, `functions.csv`, `test_asm_diff.py`, `test_progress.py`.
- Verification: `pytest tests/test_asm_diff.py tests/test_progress.py`.

### Task 2: Decompile & Match 25 16B/20B Leaf Functions (25 Functions, 444 B)
- Functions:
  - 16B: `func_0011cffc`, `engine_func_00128f34`, `engine_func_00130fe8`, `engine_func_00141468`, `engine_func_00146ce0`, `engine_func_00146d10`, `func_0015c408`, `func_0015cfd4`, `func_001e18dc`, `func_0020fe74`, `script_vm_func_002344b4`, `ui_func_0023e4d4`, `func_0024fa94`, `func_002523c0`
  - 20B: `func_001220c4`, `func_001220d8`, `func_00126430`, `engine_func_00128f44`, `func_001408ac`, `engine_func_0014e634`, `func_001531f4`, `func_00158404`, `engine_func_0017f928`, `func_00192934`, `func_001a08a8`
- Updates: `leaf_matching.h`, `leaf_matching.cpp`, `functions.csv`, `test_asm_diff.py`, `test_progress.py`.
- Verification: `pytest tests/test_asm_diff.py tests/test_progress.py`.

### Task 3: Refresh Progress Ledger, Documentation, and Git Remote Push
- Run `python tools/progress.py --write`.
- Run full `pytest` suite (42 tests).
- Commit docs and push `main` to `origin/main`.
- Whole-branch review.
