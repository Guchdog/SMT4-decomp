# Battle System & Battle HUD Subsystems Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile the core Battle System (`btlMain.cpp`), Battle HUD & Turn Gauge renderer (`btlUI.cpp`), and combat modal helpers (`btlHelp.cpp`, `btlTalk.cpp`, `btlUnit.cpp`), totaling 14 functions and 19,968 bytes. Crossing this plan reaches **116,592 bytes** and advances SMT IV decompilation to **3.71%**.

**Architecture:**
- `include/battle/battle.h`: Defines structures for `BtlHelpWork` (0x54 bytes), `BtlTalkWork` (0x34 bytes + 0xCC text buffer), `BtlUnitWork` (0x288 bytes), `BtlUIWork` (0x120 bytes, task tags 0x2, 0x7a, 0xd8, 0xe7, 0xe9), and `BtlMainWork` (0x4a58 bytes at global `0x00435d90`).
- `src/battle/btl_ui.cpp`: Implements the lifecycle, stereoscopic Upper/Lower Battle UI rendering passes (`btlUI_Calc`, `btlUI_DrawUp`, `btlUI_DrawDown`, `btlUI_DrawNumber`), and combat modal helpers (`btlHelp_Init`, `btlTalk_Init`, `btlUnit_Init`, `btlUnit_CheckPartyActive`).
- `src/battle/btl_main.cpp`: Implements the top-level battle loop state machine (`btlMain_Calc`), initialization and arena setup (`btlMain_Init`, `btlMain_Setup`), and dual-screen fade/render passes (`btlMain_DrawUp`, `btlMain_DrawDown`).
- `config/functions.csv`: Registers all 14 functions with status `non_matching` and their respective source files.
- `tests/test_progress.py`: Enforces byte-accurate and function-accurate progress at each task boundary using strict TDD.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress tracking & test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

## Review Focus
- Structural alignment: `sizeof(BtlMainWork)` must be `0x4a58` and offsets `+0x60`, `+0xc0`, `+0x13c`, `+0x154` match disassembly.
- `BtlUIWork` must correctly link to task tags `0x7a` (UpLeft), `0xd8` (UpRight), `0xe7` (Down), and `0xe9` (Number).
- Function address boundaries in `config/functions.csv` must match exact offsets from `code.bin`.
- Clean compilation without warnings under C++20.
- Byte progress ledger consistency across `tools/progress.py`.

---

### Task 1: Battle Modal Helpers (`btlHelp`, `btlTalk`, `btlUnit`, 4 functions, 1,424 bytes)

**Files:**
- Create: `include/battle/battle.h`
- Create: `src/battle/btl_ui.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `btlHelp_Init`: `0x001d2528` (232 B)
- `btlTalk_Init`: `0x001d2610` (308 B)
- `btlUnit_Init`: `0x001d2744` (644 B)
- `btlUnit_CheckPartyActive`: `0x001d29c8` (240 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 151 functions and 98,048 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structs in `include/battle/battle.h` and implement helpers in `src/battle/btl_ui.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(battle): implement btlHelp, btlTalk, and btlUnit combat modal helpers (+1,424 B)`.

---

### Task 2: Core Battle UI & Gauge Rendering (`btlUI.cpp`, 5 functions, 9,140 bytes)

**Files:**
- Modify: `include/battle/battle.h`
- Modify: `src/battle/btl_ui.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `btlUI_Init`: `0x001a83c8` (488 B)
- `btlUI_Calc`: `0x0019e034` (4,772 B)
- `btlUI_DrawUp`: `0x001b71e0` (3,224 B)
- `btlUI_DrawDown`: `0x001e4ae4` (360 B)
- `btlUI_DrawNumber`: `0x0020f35c` (296 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 156 functions and 107,188 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define `BtlUIWork` in `include/battle/battle.h` and implement in `src/battle/btl_ui.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(battle): implement btlUI core HUD, gauges, and dual-screen render passes (+9,140 B)`.

---

### Task 3: Battle State Machine & Main Engine (`btlMain.cpp`, 5 functions, 9,404 bytes)

**Files:**
- Modify: `include/battle/battle.h`
- Create: `src/battle/btl_main.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `btlMain_Init`: `0x001b0cb0` (812 B)
- `btlMain_Setup`: `0x001b6a98` (1,824 B)
- `btlMain_Calc`: `0x001b55f0` (5,288 B)
- `btlMain_DrawUp`: `0x001e4990` (340 B)
- `btlMain_DrawDown`: `0x0020eee8` (1,140 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 161 functions and 116,592 bytes (advancing to **3.71% milestone**).
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define `BtlMainWork` in `include/battle/battle.h` and implement in `src/battle/btl_main.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(battle): implement btlMain state machine, arena setup, and dual-screen renderer (+9,404 B, 3.7% milestone reached)`.
