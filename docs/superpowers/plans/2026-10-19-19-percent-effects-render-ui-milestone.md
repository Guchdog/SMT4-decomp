# 19% Decompilation Milestone: Effects, Render/UI and Runtime UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 28 previously-unmapped effect, render/UI, and runtime UI functions totaling 30,872 bytes, raising total architecture explored from **565,932 bytes (18.0284%)** to **596,804 bytes (19.0119%)** and authentically decompiled code from **317,692 bytes (10.1205%)** to **348,564 bytes (11.1038%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/engine/asd_effect2.h` / `src/engine/asd_effect2.cpp`: particles, polygon thunder/ring/flash/track, object particles, geometry engine (13 functions, 8,440 B).
- `include/engine/asd_render_ui.h` / `src/engine/asd_render_ui.cpp`: AsdGx render system, staff roll, 2D/3D event textures, Whisper/Bustup effects, model manager, Npc2d, filter/behavior primitives (12 functions, 7,564 B).
- `include/ui/ui_runtime.h` / `src/ui/ui_runtime.cpp`: three large unnamed UI runtime functions (3 functions, 14,868 B).
- `config/functions.csv`: flips the 28 rows from `todo` to `non_matching`.
- `tests/test_progress.py`: pins exact cumulative counters after every task.

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

- **Compile correctness and call ABI:** every helper call must match the callee's actual register/stack argument shape; the Python gate cannot catch this.
- **Pre-indexed writeback and stride arithmetic:** use the effective post-writeback base and verify every 4/8/0x10/0x18/0x1C/0x2C stride.
- **`.data` initializers and singleton producers:** globals read by the new bodies must carry their binary initial values; null-initialized pointers need a documented producer.
- **Effect ownership:** particle/polygon clone, link, unlink and free paths must preserve observed ownership and null/fault ordering.
- **Summary stubs:** a 5,764-byte `ui_func_001f0454` or 1,204-byte `effParticle_func_002de41c` reduced to a few statements is a defect.
- **Progress claims:** exact cumulative counters after each task; regenerate only via `python tools/progress.py --write`.

---

### Task 1: Effects part 2 - particles, polygon effects, geometry (13 functions, 8,440 bytes)

**Files:**
- Create: `include/engine/asd_effect2.h`
- Create: `src/engine/asd_effect2.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `effParticle_func_002de41c`: `0x002de41c` (1,204 B)
- `effParticle_func_002e7c30`: `0x002e7c30` (612 B)
- `effPolygonThunder_func_00327d90`: `0x00327d90` (888 B)
- `effPolygonThunder_func_0031596c`: `0x0031596c` (864 B)
- `effPolygonThunder_func_0032170c`: `0x0032170c` (852 B)
- `effPolygonRing_func_0030efb0`: `0x0030efb0` (572 B)
- `effPolygonRing_func_0031551c`: `0x0031551c` (456 B)
- `effPolygonRing_func_00315700`: `0x00315700` (452 B)
- `effPolygonFlash_func_003243bc`: `0x003243bc` (464 B)
- `effPolygonTrack_func_0024fab8`: `0x0024fab8` (600 B)
- `effObjectParticle_func_00313908`: `0x00313908` (412 B)
- `effGeometry_func_002691f0`: `0x002691f0` (532 B)
- `effGeomEngine_func_001f68b0`: `0x001f68b0` (532 B)

- [x] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 324)
self.assertEqual(stats["decompiled_bytes"], 326132)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 363)
self.assertEqual(stats["total_explored_bytes"], 574372)
```

- [x] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `324 != 311`.

- [x] **Step 3: Disassemble and implement**

Use `python tools/split_asm.py --addr <address>` for every function. Preserve particle pool indexing, polygon vertex generation, clone/free ownership, and geometry uploads. Cite every non-obvious offset.

- [x] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/asd_effect2.cpp`. Run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: 324 / 326,132 B, 39 / 248,240 B, 363 / 574,372 B; all tests PASS.

- [x] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile particle and polygon effects part 2 (+8,440 B, 18.29% explored)"
```

---

### Task 2: Render/UI - AsdGx, staff roll, event textures, bustups, filters (12 functions, 7,564 bytes)

**Files:**
- Create: `include/engine/asd_render_ui.h`
- Create: `src/engine/asd_render_ui.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `AsdGxRenderSystem_func_002d595c`: `0x002d595c` (1,144 B)
- `AsdGxRenderSystem_func_002bc570`: `0x002bc570` (468 B)
- `StaffRollMain_func_002cabcc`: `0x002cabcc` (800 B)
- `2dEventTex_func_002ee6a0`: `0x002ee6a0` (784 B)
- `3dEventTex_func_0030a0b8`: `0x0030a0b8` (468 B)
- `WhisperEffect_func_002f6734`: `0x002f6734` (776 B)
- `BustupCutAnim_func_002fc260`: `0x002fc260` (800 B)
- `BustupTex_func_0030ac20`: `0x0030ac20` (412 B)
- `AsdMdlManager_func_002b2928`: `0x002b2928` (592 B)
- `Npc2d_func_00327634`: `0x00327634` (488 B)
- `Filter4Poly_func_0034b920`: `0x0034b920` (432 B)
- `effBehavior_func_00269404`: `0x00269404` (400 B)

- [x] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 336)
self.assertEqual(stats["decompiled_bytes"], 333696)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 375)
self.assertEqual(stats["total_explored_bytes"], 581936)
```

- [x] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `336 != 324`.

- [x] **Step 3: Disassemble and implement**

Preserve render-system state, staff-roll scroll, event texture binding, bustup animation, model-manager refcounts, filter passes, and behavior ticks.

- [x] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/asd_render_ui.cpp`; expected 336 / 333,696 B, 375 / 581,936 B.

- [x] **Step 5: Commit**

```powershell
git commit -m "feat(render): decompile render system, event textures and bustups (+7,564 B, 18.53% explored)"
```

---

### Task 3: Runtime UI - three large UI routines (3 functions, 14,868 bytes)

**Files:**
- Create: `include/ui/ui_runtime.h`
- Create: `src/ui/ui_runtime.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `ui_func_001f0454`: `0x001f0454` (5,764 B)
- `ui_func_00267fb0`: `0x00267fb0` (4,672 B)
- `ui_func_00197d2c`: `0x00197d2c` (4,432 B)

- [x] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 339)
self.assertEqual(stats["decompiled_bytes"], 348564)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 378)
self.assertEqual(stats["total_explored_bytes"], 596804)
```

- [x] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `339 != 336`.

- [x] **Step 3: Disassemble and implement**

These are large UI routines. Use the disassembly's literals (resource ids, `0x0044ea00` GPU state, layout calls) to identify their roles; keep the ledger names and document the recovered role. Preserve the full call/branch structure.

- [x] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/ui/ui_runtime.cpp`; expected 339 / 348,564 B, 378 / 596,804 B (19.0119%); all tests PASS.

- [x] **Step 5: Commit**

```powershell
git commit -m "feat(ui): decompile three large runtime UI routines (+14,868 B, 19.0% milestone reached at 19.0119%)"
```
