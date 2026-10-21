# 25% Decompilation Milestone: Large Runtime Block and Batch Blocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 7 previously-unmapped engine/battle/runtime functions totaling 31,372 bytes, raising total architecture explored from **753,760 bytes (24.0119%)** to **785,132 bytes (25.0114%)** and authentically decompiled code from **505,520 bytes (16.1039%)** to **536,892 bytes (17.1036%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/engine/block_133568.h` / `src/engine/block_133568.cpp`: one 14,908-byte runtime block.
- `include/engine/block_batch.h` / `src/engine/block_batch.cpp`: six runtime/battle blocks (16,464 B).
- `config/functions.csv`: flips the 7 rows from `todo` to `non_matching`.
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

- **Large function completeness:** a 14,908-byte block must preserve every observed loop/branch/call.
- **Compile correctness and call ABI:** helpers must match register/stack argument shapes.
- **Pre-indexed writeback and strides:** verify all observed offsets.
- **`.data` initializers and producers:** globals need observed values and documented producers.
- **Progress claims:** exact cumulative counters after each task.

---

### Task 1: Large runtime block (1 function, 14,908 bytes)

**Files:**
- Create: `include/engine/block_133568.h`
- Create: `src/engine/block_133568.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `func_00133568`: `0x00133568` (14,908 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 377)
self.assertEqual(stats["decompiled_bytes"], 520428)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 416)
self.assertEqual(stats["total_explored_bytes"], 768668)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `377 != 376`.

- [ ] **Step 3: Disassemble and implement**

Use `python tools/split_asm.py --addr 0x00133568`. Recover the role from its call graph/literals. Preserve the full body; do not collapse it into a summary.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/block_133568.cpp`; expected 377 / 520,428 B, 416 / 768,668 B.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile large runtime block 0x00133568 (+14,908 B, 24.48% explored)"
```

---

### Task 2: Runtime/battle batch blocks (6 functions, 16,464 bytes)

**Files:**
- Create: `include/engine/block_batch.h`
- Create: `src/engine/block_batch.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `battle_func_002d2e50`: `0x002d2e50` (3,108 B)
- `battle_func_00267420`: `0x00267420` (2,888 B)
- `battle_func_0034a4e4`: `0x0034a4e4` (2,816 B)
- `battle_func_001fb520`: `0x001fb520` (2,788 B)
- `battle_func_001aac60`: `0x001aac60` (2,448 B)
- `battle_func_0020dc34`: `0x0020dc34` (2,416 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 383)
self.assertEqual(stats["decompiled_bytes"], 536892)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 422)
self.assertEqual(stats["total_explored_bytes"], 785132)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `383 != 377`.

- [ ] **Step 3: Disassemble and implement**

Preserve battle state, action/target selection, and all observed calls. Keep exact ledger names.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/block_batch.cpp`; expected 383 / 536,892 B, 422 / 785,132 B (25.0114%); all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(battle): decompile six runtime blocks (+16,464 B, 25.0% milestone reached at 25.0114%)"
```
