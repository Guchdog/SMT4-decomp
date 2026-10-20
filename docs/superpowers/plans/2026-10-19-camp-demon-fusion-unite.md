# Camp Demon Fusion (Unite) & UI Modals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile the Demonica Camp Menu Demon Fusion (Cathedral of Shadows / Mido `Unite.cpp`, `UniteEffect.cpp`), dynamic button prompt HUD (`ButtonHelp.cpp`), and item/skill sorting modal (`SortMenu.cpp`), totaling 6 functions and 10,124 bytes. Crossing this plan reaches the **3.0% decompilation milestone** of Shin Megami Tensei IV.

**Architecture:**
- `include/camp/unite.h`: Defines structures for `ButtonHelpManager` (0x564 byte work struct, global `0x0043DA28`), `SortMenuManager` (0x878 byte work struct, global `0x0043DD20`), and `UniteWork` (0x1BC8 byte work struct, Mido 3D Cathedral of Shadows fusion engine).
- `src/camp/unite.cpp`: Implements the lifecycle, stereoscopic Upper/Lower fusion rendering passes (`Unite_DrawAndCalc`), setup routines (`Unite_Setup`, `UniteEffect_Init`), and UI helpers (`ButtonHelp_Init`, `SortMenu_Init`).
- `config/functions.csv`: Registers all 6 functions with status `non_matching` and `src/camp/unite.cpp`.
- `tests/test_progress.py`: Enforces byte-accurate and function-accurate progress at each task boundary using strict TDD.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress tracking & test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

---

### Task 1: Camp UI Helpers (`ButtonHelp.cpp` & `SortMenu.cpp`, 2 functions, 1,380 bytes)

**Files:**
- Create: `include/camp/unite.h`
- Create: `src/camp/unite.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `ButtonHelp_Init`: `0x0028d974` (736 B)
- `SortMenu_Init`: `0x0029e63c` (644 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 143 functions and 87,880 bytes.
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `ButtonHelpManager` and `SortMenuManager` in `include/camp/unite.h` and implement in `src/camp/unite.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(camp): implement ButtonHelp and SortMenu modal helpers (+1,380 B)`.

---

### Task 2: Demon Fusion Engine & Cathedral of Shadows (`Unite.cpp` & `UniteEffect.cpp`, 4 functions, 8,744 bytes)

**Files:**
- Modify: `include/camp/unite.h`
- Modify: `src/camp/unite.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Unite_Init`: `0x0029b3cc` (1,676 B)
- `Unite_Setup`: `0x001f2f58` (1,704 B)
- `UniteEffect_Init`: `0x002e315c` (344 B)
- `Unite_DrawAndCalc`: `0x001de238` (5,020 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 147 functions and 96,624 bytes (Crossing the **3.0% milestone**!).
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `UniteWork` in `include/camp/unite.h` and implement Unite functions in `src/camp/unite.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(camp): implement Mido Demon Fusion Unite engine (+8,744 B, 3% milestone reached)`.
