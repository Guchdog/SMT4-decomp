# 21% Decompilation Milestone: UI Scene Runtime Extras Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 8 previously-unmapped UI sprite/scene runtime functions totaling 32,736 bytes, raising total architecture explored from **629,052 bytes (20.0392%)** to **661,788 bytes (21.0820%)** and authentically decompiled code from **380,812 bytes (12.1312%)** to **413,548 bytes (13.1743%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/ui/ui_scene_extras.h` / `src/ui/ui_scene_extras.cpp`: four large UI scene routines (17,108 B).
- `include/ui/ui_runtime2.h` / `src/ui/ui_runtime2.cpp`: four large UI sprite/list routines (15,628 B).
- `config/functions.csv`: flips the 8 rows from `todo` to `non_matching`.
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

- **Compile correctness and call ABI:** every helper call must match the callee's actual register/stack argument shape.
- **Pre-indexed writeback and stride arithmetic:** verify every 4/8/0x10/0x18/0x1C/0x2C/0x8C stride.
- **`.data` initializers and singleton producers:** globals read by the new bodies need observed values and documented producers.
- **UI sprite ownership:** list-box/task/sprite cursor state, layout table reads, and draw-pass ordering must match.
- **Summary stubs:** a 4,380-byte `ui_func_001e83fc` reduced to a few statements is a defect.
- **Progress claims:** exact cumulative counters after each task; regenerate only via `python tools/progress.py --write`.

---

### Task 1: UI scene routines A (4 functions, 17,108 bytes)

**Files:**
- Create: `include/ui/ui_scene_extras.h`
- Create: `src/ui/ui_scene_extras.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `ui_func_001e83fc`: `0x001e83fc` (4,380 B)
- `ui_func_003d7630`: `0x003d7630` (4,308 B)
- `ui_func_00243e8c`: `0x00243e8c` (4,216 B)
- `ui_func_002f150c`: `0x002f150c` (4,204 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 351)
self.assertEqual(stats["decompiled_bytes"], 397920)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 390)
self.assertEqual(stats["total_explored_bytes"], 646160)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `351 != 347`.

- [ ] **Step 3: Disassemble and implement**

Use `python tools/split_asm.py --addr <address>`. Recover each routine's role from its literals/call graph/layout tables. Keep the ledger names and document the recovered role. Preserve all observed calls, branches, and state stores.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/ui/ui_scene_extras.cpp`. Run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: 351 / 397,920 B, 39 / 248,240 B, 390 / 646,160 B; all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(ui): decompile four UI scene runtime routines (+17,108 B, 20.58% explored)"
```

---

### Task 2: UI scene routines B (4 functions, 15,628 bytes)

**Files:**
- Create: `include/ui/ui_runtime2.h`
- Create: `src/ui/ui_runtime2.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `ui_func_00214964`: `0x00214964` (4,020 B)
- `ui_func_001f1fc8`: `0x001f1fc8` (3,960 B)
- `ui_func_001e989c`: `0x001e989c` (3,924 B)
- `ui_func_003eb4f4`: `0x003eb4f4` (3,724 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 355)
self.assertEqual(stats["decompiled_bytes"], 413548)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 394)
self.assertEqual(stats["total_explored_bytes"], 661788)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `355 != 351`.

- [ ] **Step 3: Disassemble and implement**

Preserve sprite/list cursor state, layout table reads, draw-pass ordering, and task ownership. Keep the ledger names and document the recovered roles.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/ui/ui_runtime2.cpp`; expected 355 / 413,548 B, 394 / 661,788 B (21.0820%); all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(ui): decompile four UI sprite/list routines (+15,628 B, 21.0% milestone reached at 21.0820%)"
```
