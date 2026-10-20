# Shop Subsystem, UI Modals & FlowScript Bytecode VM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile the Mikado & Tokyo Shop system (`shopMain.cpp`), character naming modal (`nameMain.cpp`), Barracks room (`onesRoom.cpp`), and the core FlowScript Virtual Machine 99-opcode execution engine (`scrScriptProcess.cpp`), totaling 7 functions and 27,140 bytes. Crossing this plan reaches **143,732 bytes** and advances SMT IV decompilation to **4.57%**.

**Architecture:**
- `include/shop/shop.h`: Defines structures for `ShopMainWork` (0x1C bytes, global `g_ShopMainManager` at `0x0044E050`), stereoscopic rendering tasks (UpLeft tag `0x65`, UpRight tag `0xCC`, Down tag `0xE7`), and shop inventory processing (`shopMain_Init`, `shopMain_Proc`, `shopMain_DrawUp`, `shopMain_DrawDown`).
- `include/script/flowscript.h`: Defines structures for `NameMainWork` (0x960 bytes, global `0x0044D180`), `OnesRoomWork` (0x14 bytes, global `0x0044D1C8`), and `FlowScriptContext` (opcodes 0x00..0x63, 99-entry branch table).
- `src/shop/shop.cpp`: Implements the shop buying/selling/equipment lifecycle and stereoscopic UI render passes.
- `src/script/script_vm.cpp`: Implements the FlowScript VM opcode execution dispatch engine (`FlowScript_ExecuteOpcode`), character naming modal (`nameMain_Init`), and barracks script processor (`onesRoom_Init`).
- `config/functions.csv`: Registers all 7 functions with status `non_matching` and their respective source files.
- `tests/test_progress.py`: Enforces byte-accurate and function-accurate progress at each task boundary using strict TDD.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress tracking & test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

---

### Task 1: Mikado & Tokyo Shop Engine (`shopMain.cpp`, 4 functions, 3,820 bytes)

**Files:**
- Create: `include/shop/shop.h`
- Create: `src/shop/shop.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `shopMain_Init`: `0x001d3b10` (364 B)
- `shopMain_Proc`: `0x001d9538` (908 B)
- `shopMain_DrawUp`: `0x001fdf4c` (1,132 B)
- `shopMain_DrawDown`: `0x0021ee14` (1,416 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 165 functions and 120,412 bytes.
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define `ShopMainWork` in `include/shop/shop.h` and implement in `src/shop/shop.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(shop): implement shopMain buying/selling engine and dual-screen renderers (+3,820 B)`.

---

### Task 2: UI Modals & Barracks Subsystems (`nameMain.cpp` & `onesRoom.cpp`, 2 functions, 800 bytes)

**Files:**
- Create: `include/script/flowscript.h`
- Create: `src/script/script_vm.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `nameMain_Init`: `0x001d374c` (408 B)
- `onesRoom_Init`: `0x001d38fc` (392 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 167 functions and 121,212 bytes.
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Define structs in `include/script/flowscript.h` and implement in `src/script/script_vm.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(ui): implement nameMain character naming modal and onesRoom barracks (+800 B)`.

---

### Task 3: FlowScript Bytecode VM & 99-Opcode Dispatcher (`scrScriptProcess.cpp`, 1 function, 22,520 bytes)

**Files:**
- Modify: `include/script/flowscript.h`
- Modify: `src/script/script_vm.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `FlowScript_ExecuteOpcode`: `0x001d3d40` (22,520 B)

- [x] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 168 functions and 143,732 bytes (crossing **4.5% milestone**).
- [x] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [x] **Step 3: Implement `FlowScript_ExecuteOpcode` with 99-case branch table in `src/script/script_vm.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [x] **Step 5: Commit**
  - Commit: `feat(script): implement FlowScript bytecode VM 99-opcode dispatch engine (+22,520 B, 4.5% milestone reached)`.
