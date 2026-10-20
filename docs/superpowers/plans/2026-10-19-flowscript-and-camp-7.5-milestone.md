# FlowScript VM & Demonica Camp Menu 7.5% Milestone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile the FlowScript bytecode virtual machine command dispatchers (`script_exec.cpp`) and the Demonica Camp core menu processor & stereoscopic renderer (`camp_main.cpp`), totaling 4 functions and 93,552 bytes. Crossing this plan reaches **254,748 bytes** and hits **8.1153%** decompilation progress, achieving the user's 7.5% goal for Shin Megami Tensei IV.

**Architecture:**
- `include/script/script_exec.h` & `src/script/script_exec.cpp`: Defines structures for `FlowScriptExecContext` (managing script program counter, call stack frames, variable table, flag bank, and host command jump table) and implements `FlowScript_DispatchNativeCommands` (`0x001b7e78`, 34,684 B) and `FlowScript_EvalStateControl` (`0x001c3ed4`, 18,660 B).
- `include/camp/camp_main.h` & `src/camp/camp_main.cpp`: Defines structures for `CampMainContext` (managing Demonica UI page transitions, party slot navigation, inventory tab sorting, and sub-app launch contexts) and implements `Camp_MainProc` (`0x0017fe9c`, 27,308 B) and `Camp_DrawStereoViews` (`0x0019a3ec`, 12,900 B).
- `config/functions.csv`: Registers the 4 functions with status `non_matching` and their respective source files.
- `tests/test_progress.py`: Enforces byte-accurate and function-accurate progress at each task boundary using strict TDD.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress tracking & test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

---

### Task 1: FlowScript VM Native Command Dispatcher & State Control (`script_exec.cpp`, 2 functions, 53,344 bytes)

**Files:**
- Create: `include/script/script_exec.h`
- Create: `src/script/script_exec.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `FlowScript_DispatchNativeCommands`: `0x001b7e78` (34,684 B)
- `FlowScript_EvalStateControl`: `0x001c3ed4` (18,660 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 179 functions and 214,540 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define `FlowScriptExecContext` in `include/script/script_exec.h` and implement in `src/script/script_exec.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(script): implement FlowScript native command dispatcher and state control (+53,344 B, 6.83% reached)`.

---

### Task 2: Demonica Camp Menu Core Processor & Stereoscopic Renderer (`camp_main.cpp`, 2 functions, 40,208 bytes)

**Files:**
- Create: `include/camp/camp_main.h`
- Create: `src/camp/camp_main.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Camp_MainProc`: `0x0017fe9c` (27,308 B)
- `Camp_DrawStereoViews`: `0x0019a3ec` (12,900 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 181 functions and 254,748 bytes (crossing the **7.5% decompilation milestone** to 8.11%!).
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define `CampMainContext` in `include/camp/camp_main.h` and implement in `src/camp/camp_main.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(camp): implement Demonica Camp menu core processor and stereoscopic views (+40,208 B, 7.5% milestone reached at 8.11%)`.
