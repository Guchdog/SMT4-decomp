# Top-Screen Status HUD & Status Manager (Status.cpp) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile the top-level Status Manager and Stereoscopic Upper-Screen HUD module (`c:\SMT4\XRD686\sdds4\program\status\Status.cpp`, `g_StatusWork` at `0x0044E140`, totaling `~25,000` bytes across top-screen 3D stereo draw passes, demon stats, affinity charts, and status calc tasks).

**Architecture:** Reconstruct the `0x1EBC`-byte `StatusWork` structure in `include/ui/status.h`, verified with `static_assert(offsetof(...))` checks matching ARMv6K offsets. Implement the top-screen stereoscopic renderer (`Status DrawUpLeft`/`Status DrawUpRight` and `Status DrawBackUpLeft`/`Status DrawBackUpRight`), the status state engine (`Status Calc`), and the top-level status lifecycle coordinator in `src/ui/status.cpp`.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress verifier & unit test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit & push.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

## Review Focus
- Memory layout of `StatusWork` (`0x1EBC` bytes) allocated at `0x0028c2e8` with 0x100 alignment.
- Accurate stereo draw parameter handling: left eye (`prio 0x7D` / `0x65`) vs right eye (`prio 0xDB` / `0xCC`).
- Clean integration with `StatusDown_Init` (`0x002d931c`) called from `Status_Init` (`0x0028c3e0`).

---

### Task 1: StatusWork Structure & Lifecycle (`Status_Init`, `Status_Destroy`, Queries)

**Files:**
- Create: `include/ui/status.h`
- Create: `src/ui/status.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Interfaces:**
- Produces: `smt4::ui::StatusWork`, `smt4::ui::Status_Init`, `smt4::ui::Status_Destroy`, `smt4::ui::g_StatusWork`
- Consumes: `smt4::ui::StatusDown_Init` (`0x002d931c`)

- [x] **Step 1: Update progress test expectations (RED)**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Define `StatusWork` and implement `Status_Init` and queries in `include/ui/status.h` and `src/ui/status.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
- [x] **Step 5: Commit and push**

---

### Task 2: Stereoscopic Upper-Screen HUD Renderer (`Status_DrawBackUp` & `Status_DrawUp`)

**Files:**
- Modify: `include/ui/status.h`
- Modify: `src/ui/status.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Interfaces:**
- Produces: `Status_DrawBackUp` (`0x001cddf8`, 516 B), `Status_DrawUp` (`0x001a310c`, 15,148 B)
- Consumes: `UiLayout_GetNode`, `UiSprite_DrawNode`, `UiSprite_DrawPanel`

- [x] **Step 1: Update progress test expectations (RED)**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Implement `Status_DrawBackUp` and `Status_DrawUp` in `src/ui/status.cpp`**
- [x] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
- [x] **Step 5: Commit and push**

---

### Task 3: Status State & Calc Engine (`Status_Calc` & Related Subroutines)

**Files:**
- Modify: `include/ui/status.h`
- Modify: `src/ui/status.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Interfaces:**
- Produces: `Status_CalcTaskCallback` (`0x0018f560`, 4,912 B), `Status_GetActiveDemonId`, `Status_SetDemon`
- Consumes: `Sound_PlaySE`, `UiAnimSprite_UpdateCalc`

- [ ] **Step 1: Update progress test expectations (RED)**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `Status_CalcTaskCallback` and state handlers in `src/ui/status.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
- [ ] **Step 5: Commit and push**
