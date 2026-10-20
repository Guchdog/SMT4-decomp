# Battle Target Select, Demon Compendium (Bible) & Result System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile the Battle Target Selection system (`btlTargetSelect.cpp`), Demon Compendium Devil Book (`bibleMain.cpp`, `bibleAnalyze.cpp`), and the Battle/Quest Result subsystem (`Result.cpp`), totaling 9 functions and 17,464 bytes. Crossing this plan reaches **161,196 bytes** and achieves the **5.0% decompilation milestone** of Shin Megami Tensei IV.

**Architecture:**
- `include/battle/target_select.h`: Defines structures for `BtlTargetSelectWork` (0xB8 bytes, global `0x00439C60`), targeting cursor, and stereo draw callbacks.
- `include/camp/bible.h`: Defines structures for `BibleMainWork` (0x20 bytes, global `0x0043DA10`) and `BibleAnalyzeWork` (0x180 bytes) for Compendium summon rates, stats, and fusion preview.
- `include/ui/result.h`: Defines structures for `ResultWork` (0xD658 bytes, global `0x0044DC20`), EXP allocation, Macca tally, item drop lists, level-up bonuses, and stereoscopic result draw passes.
- `src/battle/btl_target_select.cpp`: Implements target cursor positioning, target cycling, and stereoscopic reticle rendering.
- `src/camp/bible.cpp`: Implements Demon Compendium registration, lookup, and demon analysis.
- `src/ui/result.cpp`: Implements the post-combat reward processing, level-up stat distribution, and dual-screen reward HUD.
- `config/functions.csv`: Registers all 9 functions with status `non_matching` and their respective source files.
- `tests/test_progress.py`: Enforces byte-accurate and function-accurate progress at each task boundary using strict TDD.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress tracking & test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

---

### Task 1: Battle Target Selection Subsystem (`btlTargetSelect.cpp`, 3 functions, 1,760 bytes)

**Files:**
- Create: `include/battle/target_select.h`
- Create: `src/battle/btl_target_select.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `btlTargetSelect_Init`: `0x002e8294` (604 B)
- `btlTargetSelect_Calc`: `0x002e06bc` (1,080 B)
- `btlTargetSelect_DrawUp`: `0x002f4aa4` (76 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 171 functions and 145,492 bytes.
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `BtlTargetSelectWork` in `include/battle/target_select.h` and implement in `src/battle/btl_target_select.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(battle): implement btlTargetSelect target reticle and cursor system (+1,760 B)`.

---

### Task 2: Demon Compendium & Devil Book (`bibleMain.cpp` & `bibleAnalyze.cpp`, 2 functions, 1,300 bytes)

**Files:**
- Create: `include/camp/bible.h`
- Create: `src/camp/bible.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `bibleMain_Init`: `0x00269cc8` (352 B)
- `bibleAnalyze_Init`: `0x003a9200` (948 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 173 functions and 146,792 bytes.
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `BibleMainWork` in `include/camp/bible.h` and implement in `src/camp/bible.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(camp): implement bibleMain demon compendium and bibleAnalyze inspection (+1,300 B)`.

---

### Task 3: Battle Result & Level-Up Subsystem (`Result.cpp`, 4 functions, 14,404 bytes)

**Files:**
- Create: `include/ui/result.h`
- Create: `src/ui/result.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Result_Init`: `0x0029bc38` (368 B)
- `Result_Calc`: `0x0018bfec` (12,684 B)
- `Result_DrawUp`: `0x001a15b0` (932 B)
- `Result_DrawDown`: `0x001c87d8` (420 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 177 functions and 161,196 bytes (crossing the **5.0% decompilation milestone**!).
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `ResultWork` in `include/ui/result.h` and implement in `src/ui/result.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(ui): implement Result post-combat rewards, level-up logic, and dual-screen HUD (+14,404 B, 5.0% milestone reached)`.
