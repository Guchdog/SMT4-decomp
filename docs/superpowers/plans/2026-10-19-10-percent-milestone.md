# 10% Decompilation Milestone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile the Battle Press Turn Combat & Camera System, Demonica Party Stock Sub-Mode Manager, FlowScript VM Runtime Memory & Flag Banks, and HUD MiniMap Radar Renderer, totaling 6 functions and 61,644 bytes. Crossing this plan reaches **316,392 bytes** and achieves the **10.0% decompilation milestone (10.0790%)** for Shin Megami Tensei IV.

**Architecture:**
- `include/battle/btl_main.h` & `src/battle/btl_main.cpp`: Implements `Btl_ActionCalc` (`0x003cccd8`, 9,192 B) and `Btl_CameraCalc` (`0x003d3dd4`, 6,896 B) for Press Turn icon management, weakness exploitation, smirk status, and dynamic 3D battle cameras.
- `include/camp/camp_party.h` & `src/camp/camp_party.cpp`: Implements `Camp_SubModeProcess` (`0x0032cb08`, 12,620 B) for Demonica party slot summoning, skill inheritance inspection, whisper events, and sub-mode flow.
- `include/script/script_runtime.h` & `src/script/script_runtime.cpp`: Implements `FlowScript_InitRuntimeMemory` (`0x00277f9c`, 12,192 B) and `FlowScript_ProcessFlagBank` (`0x001e5d84`, 9,740 B) for runtime execution frames, heap allocation, and global/local flag banks.
- `include/ui/minimap.h` & `src/ui/minimap.cpp`: Implements `Ui_MiniMapRender` (`0x0025f8f0`, 11,004 B) for lower touchscreen radar display, compass rotation, and 2D map projection.
- `config/functions.csv`: Registers all 6 functions with status `non_matching` and their respective source files.
- `tests/test_progress.py`: Enforces byte-accurate and function-accurate progress at each task boundary using strict TDD.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress tracking & test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

---

### Task 1: Battle Press Turn & Dynamic Camera System (`btl_main.cpp`, 2 functions, 16,088 bytes)

**Files:**
- Create: `include/battle/btl_main.h`
- Create: `src/battle/btl_main.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Btl_ActionCalc`: `0x003cccd8` (9,192 B)
- `Btl_CameraCalc`: `0x003d3dd4` (6,896 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 183 functions and 270,836 bytes.
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define structures in `include/battle/btl_main.h` and implement in `src/battle/btl_main.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(battle): implement Press Turn action calculator and dynamic 3D camera (+16,088 B, 8.63% reached)`.

---

### Task 2: Demonica Camp Sub-Mode & Demon Party Stock Manager (`camp_party.cpp`, 1 function, 12,620 bytes)

**Files:**
- Create: `include/camp/camp_party.h`
- Create: `src/camp/camp_party.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Camp_SubModeProcess`: `0x0032cb08` (12,620 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 184 functions and 283,456 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in `include/camp/camp_party.h` and implement in `src/camp/camp_party.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(camp): implement Demonica sub-mode and demon party stock manager (+12,620 B, 9.03% reached)`.

---

### Task 3: FlowScript VM Runtime Memory & Global Flag Bank (`script_runtime.cpp`, 2 functions, 21,932 bytes)

**Files:**
- Create: `include/script/script_runtime.h`
- Create: `src/script/script_runtime.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `FlowScript_InitRuntimeMemory`: `0x00277f9c` (12,192 B)
- `FlowScript_ProcessFlagBank`: `0x001e5d84` (9,740 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 186 functions and 305,388 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in `include/script/script_runtime.h` and implement in `src/script/script_runtime.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(script): implement FlowScript runtime memory and global flag bank (+21,932 B, 9.73% reached)`.

---

### Task 4: HUD Touchscreen MiniMap Radar & 2D Projection Pipeline (`minimap.cpp`, 1 function, 11,004 bytes)

**Files:**
- Create: `include/ui/minimap.h`
- Create: `src/ui/minimap.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Ui_MiniMapRender`: `0x0025f8f0` (11,004 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 187 functions and 316,392 bytes (crossing the **10.0% decompilation milestone** to 10.0790%!).
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in `include/ui/minimap.h` and implement in `src/ui/minimap.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(ui): implement touchscreen minimap radar and 2D projection pipeline (+11,004 B, 10.0% milestone reached at 10.08%)`.
