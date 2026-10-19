# Stereoscopic Window & Notification Dialogs (ComWin, InfoWin, GuestWin) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile the 3DS stereoscopic font window and dialog notification subsystem (`c:\SMT4\XRD686\sdds4\program\font\ComWin\ComWin.cpp`, `InfoWin\InfoWin.cpp`, `GuestWin\GuestWin.cpp`), totaling 21 functions and 7,836 bytes across common message dialogs, system alerts, partner notifications, stereo draw passes, and window task callbacks. Crossing this plan achieves the **2% decompilation milestone** of Shin Megami Tensei IV.

**Architecture:**
- `include/ui/window.h`: Defines structures for `ComWinWork` (0x188 bytes, tag 0x122, global `0x0043E0F8`), `InfoWinWork` (0x1BC bytes, tag 0xFF, global `0x0043E128`), and `GuestWinWork` (0xBC bytes, tag 0xF5, global `0x0043E110`), verified with `static_assert(sizeof(...))` and `static_assert(offsetof(...))`.
- `src/ui/window.cpp`: Implements the lifecycle, stereoscopic rendering passes (`ComWin DrawUpLeft`/`ComWin DrawUpRight`, `InfoWin DrawUpLeft`/`InfoWin DrawUpRight`, `GuestWin DrawUpLeft`/`GuestWin DrawUpRight`), and task calculation callbacks (`ComWin Calc`, `InfoWin Calc`, `GuestWin Calc`).
- `config/functions.csv`: Registers all 21 functions with status `non_matching` and `src/ui/window.cpp`.
- `tests/test_progress.py`: Enforces byte-accurate and function-accurate progress at each task boundary using strict TDD.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress tracking & test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit & push.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

---

### Task 1: Common Message Window (`ComWin.cpp`, 8 functions, 3,744 bytes)

**Files:**
- Create: `include/ui/window.h`
- Create: `src/ui/window.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `ComWin_IsActive`: `0x0010a6fc` (16 B)
- `ComWin_SetState`: `0x0010a70c` (60 B)
- `ComWin_Init`: `0x0010a748` (504 B)
- `ComWin_GetState`: `0x0010a940` (20 B)
- `ComWin_ProcessDialog`: `0x0010a954` (1,352 B)
- `ComWin_CheckFlag`: `0x0010ae9c` (44 B)
- `ComWin_GetResult`: `0x0010aec8` (12 B)
- `ComWin_DrawUp`: `0x0011a354` (1,632 B)
- `ComWin_Reset`: `0x0010aed4` (100 B) [Wait, note: 0x0010aed4 is part of ComWin]
Total for ComWin: 3,740 bytes across 8 functions.

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 100 functions and 59,408 bytes.
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `ComWinWork` in `include/ui/window.h` and implement ComWin functions in `src/ui/window.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Register all 9 ComWin functions in `config/functions.csv` as `non_matching` in `src/ui/window.cpp`.
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit and push**
  - Commit: `feat(ui): implement ComWin stereoscopic dialog window (+3,740 B)`.
  - Push to `origin/main`.

---

### Task 2: Info & Alert Window (`InfoWin.cpp`, 7 functions, 2,192 bytes)

**Files:**
- Modify: `include/ui/window.h`
- Modify: `src/ui/window.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `InfoWin_IsActive`: `0x0010af38` (16 B)
- `InfoWin_SetState`: `0x0010af48` (60 B)
- `InfoWin_Init`: `0x0010af84` (560 B)
- `InfoWin_ShowMessage`: `0x0010b1b4` (172 B)
- `InfoWin_UpdateTimer`: `0x0010b260` (192 B)
- `InfoWin_Dismiss`: `0x0010b320` (32 B)
- `InfoWin_DrawUp`: `0x0011ae10` (792 B)
- `InfoWin_Calc`: `0x0011b128` (588 B) [Shared / adjacent calc dispatcher]

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 108 functions and 61,820 bytes.
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `InfoWinWork` in `include/ui/window.h` and implement InfoWin functions in `src/ui/window.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Register InfoWin functions in `config/functions.csv`.
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit and push**
  - Commit: `feat(ui): implement InfoWin alert & notification window (+2,412 B)`.
  - Push to `origin/main`.

---

### Task 3: Guest Demonica Prompt Window (`GuestWin.cpp`, 4 functions, 1,684 bytes)

**Files:**
- Modify: `include/ui/window.h`
- Modify: `src/ui/window.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `GuestWin_IsActive`: `0x0010b340` (16 B)
- `GuestWin_Init`: `0x0010b350` (448 B)
- `GuestWin_HandlePrompt`: `0x0010b510` (104 B)
- `GuestWin_DrawUp`: `0x0011a9b4` (1,116 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 112 functions and 63,504 bytes (Crossing 2.0% of executable!).
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `GuestWinWork` in `include/ui/window.h` and implement GuestWin functions in `src/ui/window.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Register GuestWin functions in `config/functions.csv`.
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit and push**
  - Commit: `feat(ui): implement GuestWin partner demonica prompt (+1,684 B, 2% milestone reached)`.
  - Push to `origin/main`.
