# 24% Decompilation Milestone: Script/UI/Battle Runtime Blocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 9 previously-unmapped script/UI/battle/engine functions totaling 31,344 bytes, raising total architecture explored from **722,416 bytes (23.0134%)** to **753,760 bytes (24.0123%)** and authentically decompiled code from **474,176 bytes (15.1054%)** to **505,520 bytes (16.1039%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/script/script_blocks.h` / `src/script/script_blocks.cpp`: script VM blocks (7,060 B).
- `include/ui/ui_blocks.h` / `src/ui/ui_blocks.cpp`: UI blocks (10,540 B).
- `include/engine/engine_blocks.h` / `src/engine/engine_blocks.cpp`: engine/battle blocks (13,744 B).
- `config/functions.csv`: flips the 9 rows from `todo` to `non_matching`.
- `tests/test_progress.py`: pins exact cumulative counters after each task.

**Tech Stack:** C++20, ARMv6K disassembly (`tools/split_asm.py` + Capstone), Python 3.12 progress verifier, MSVC BuildTools x86 compile checks.

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints

- Target binary: `extracted/exefs/code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Never invent struct layouts or behavior: every field offset, branch, call target, and constant must be traceable to the function's disassembly. Pre-indexed loads (`LDR rX,[rY,#imm]!`) must use the effective post-writeback offset.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` immediately above its definition with the exact ledger address/size/name.
- Do not mark a function `non_matching` unless its body implements the observed control flow; comment-only placeholders remain `stub`.
- One declaration per binary address: shared helpers go in `include/engine/asd_symbols.h` or the module header; no duplicate names/signatures/linkage.
- Every assigned global must have exactly one definition with observed initial values (`.data` initializers included).
- Strict TDD: update `tests/test_progress.py` first (RED), implement, then `python tools/progress.py --write` and the full suite (GREEN), then commit. Compile the touched TUs with MSVC BuildTools x86.
- Preserve style: fixed-width types from `include/types.h`, four-space indentation, opaque structs with `static_assert(offsetof(...))`.

## Review Focus

- **Compile correctness and call ABI:** every helper call must match the actual register/stack argument shape.
- **Pre-indexed writeback and strides:** verify every 4/8/0x10/0x18/0x1C/0x2C/0x8C stride.
- **`.data` initializers and producers:** globals need observed values and documented producers.
- **Large block bodies:** do not collapse loops/dispatch into summaries.
- **Progress claims:** exact cumulative counters after each task.

---

### Task 1: Script/UI/engine blocks A (4 functions, 14,360 bytes)

**Files:**
- Create: `include/script/script_blocks.h`
- Create: `src/script/script_blocks.cpp`
- Create: `include/ui/ui_blocks.h`
- Create: `src/ui/ui_blocks.cpp`
- Create: `include/engine/engine_blocks.h`
- Create: `src/engine/engine_blocks.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `script_vm_func_0024c828`: `0x0024c828` (3,616 B)
- `ui_func_001fe590`: `0x001fe590` (3,608 B)
- `ui_func_002ed5d0`: `0x002ed5d0` (3,584 B)
- `engine_func_00236958`: `0x00236958` (3,552 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 371)
self.assertEqual(stats["decompiled_bytes"], 488536)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 410)
self.assertEqual(stats["total_explored_bytes"], 736776)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `371 != 367`.

- [ ] **Step 3: Disassemble and implement**

Use `python tools/split_asm.py --addr <address>`. Recover roles from literals/call graphs. Put script_vm rows in `script_blocks.cpp`, UI rows in `ui_blocks.cpp`, engine row in `engine_blocks.cpp`. Preserve all calls/branches/stores.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set statuses `non_matching` with the matching source files. Run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: 371 / 488,536 B, 39 / 248,240 B, 410 / 736,776 B; all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(script,ui,engine): decompile four runtime blocks A (+14,360 B, 23.47% explored)"
```

---

### Task 2: Script/UI/engine/battle blocks B (5 functions, 16,984 bytes)

**Files:**
- Modify: `include/script/script_blocks.h`, `src/script/script_blocks.cpp`
- Modify: `include/ui/ui_blocks.h`, `src/ui/ui_blocks.cpp`
- Modify: `include/engine/engine_blocks.h`, `src/engine/engine_blocks.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `engine_func_002aad14`: `0x002aad14` (3,484 B)
- `ui_func_0036c0a8`: `0x0036c0a8` (3,480 B)
- `ui_func_00368cf8`: `0x00368cf8` (3,452 B)
- `script_vm_func_0027b8cc`: `0x0027b8cc` (3,444 B)
- `battle_func_002553ec`: `0x002553ec` (3,124 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 376)
self.assertEqual(stats["decompiled_bytes"], 505520)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 415)
self.assertEqual(stats["total_explored_bytes"], 753760)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `376 != 371`.

- [ ] **Step 3: Disassemble and implement**

Preserve full bodies; route script rows to `script_blocks.cpp`, UI rows to `ui_blocks.cpp`, engine/battle rows to `engine_blocks.cpp`.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set statuses `non_matching`; expected 376 / 505,520 B, 415 / 753,760 B (24.0123%); all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(script,ui,engine,battle): decompile five runtime blocks B (+16,984 B, 24.0% milestone reached at 24.0123%)"
```
