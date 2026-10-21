# 22% Decompilation Milestone: Texture Converters and Event Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 4 previously-unmapped engine functions totaling 29,180 bytes, raising total architecture explored from **661,788 bytes (21.0820%)** to **690,968 bytes (22.0119%)** and authentically decompiled code from **413,548 bytes (13.1741%)** to **442,728 bytes (14.1042%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/engine/tex_convert.h` / `src/engine/tex_convert.cpp`: three large texture/bitmap conversion routines (22,260 B).
- `include/engine/event_runtime.h` / `src/engine/event_runtime.cpp`: one large event/resource runtime routine (6,920 B).
- `config/functions.csv`: flips the 4 rows from `todo` to `non_matching`.
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

- **Texture conversion math:** channel masks, 4bpp/8bpp nibble order, swizzle/tile addressing, `0x7F7F7F7F` masks, and stride constants must match exactly.
- **Pre-indexed writeback and loop strides:** use effective post-writeback bases.
- **Cross-function reuse:** the three converter routines likely share helpers; do not duplicate logic with divergent constants.
- **Event/resource runtime state:** task ownership, resource tables, and observed calls must be preserved.
- **Summary stubs:** a 7,456-byte converter reduced to a few statements is a defect.
- **Progress claims:** exact cumulative counters after each task.

---

### Task 1: Texture/bitmap converters (3 functions, 22,260 bytes)

**Files:**
- Create: `include/engine/tex_convert.h`
- Create: `src/engine/tex_convert.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `func_00170d70`: `0x00170d70` (7,456 B)
- `func_00177370`: `0x00177370` (7,456 B)
- `func_0017d970`: `0x0017d970` (7,348 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 358)
self.assertEqual(stats["decompiled_bytes"], 435808)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 397)
self.assertEqual(stats["total_explored_bytes"], 684048)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `358 != 355`.

- [ ] **Step 3: Disassemble and implement**

Use `python tools/split_asm.py --addr <address>`. The three routines share `0x7F7F7F7F` masks and repeated channel-pack blocks; recover the common conversion core and the per-format differences. Keep the ledger names (lowercase `func_*` is legal) and document the recovered roles. Preserve every observed branch and store.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/tex_convert.cpp`. Run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: 358 / 435,808 B, 39 / 248,240 B, 397 / 684,048 B; all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile three texture conversion routines (+22,260 B, 21.79% explored)"
```

---

### Task 2: Event/resource runtime (1 function, 6,920 bytes)

**Files:**
- Create: `include/engine/event_runtime.h`
- Create: `src/engine/event_runtime.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `func_0011d9fc`: `0x0011d9fc` (6,920 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 359)
self.assertEqual(stats["decompiled_bytes"], 442728)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 398)
self.assertEqual(stats["total_explored_bytes"], 690968)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `359 != 358`.

- [ ] **Step 3: Disassemble and implement**

Recover the routine's role from its call graph/literals (`0x00420d30` table reference). Preserve resource-table traversal, task ownership, and all observed calls.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/event_runtime.cpp`; expected 359 / 442,728 B, 398 / 690,968 B (22.0119%); all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile event/resource runtime (+6,920 B, 22.0% milestone reached at 22.0122%)"
```
