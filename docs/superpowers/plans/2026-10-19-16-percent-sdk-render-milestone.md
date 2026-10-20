# 16% Decompilation Milestone: SDK Render, Text & Model Primitives Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 28 previously unmapped `AsdSDK`/`AsdGx` support functions totaling 22,720 bytes, raising total architecture explored from **479,584 bytes (15.2777%)** to **502,304 bytes (16.0015%)** across 239 explored functions and authentically decompiled code from **231,344 bytes (7.3697%)** to **254,064 bytes (8.0935%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/engine/asd_model.h` / `src/engine/asd_model.cpp`: 3D model loaders, `ShadowModel.bcmdl` binding, `ATBC` animation-table parsing, model work initialization, and the `EffectEditor` authoring surface (10 functions, 13,276 B).
- `include/engine/asd_text.h` / `src/engine/asd_text.cpp`: `AsdFont` glyph entry points, text layout/measurement, message bundle handling, and `AsdListBox` list geometry (8 functions, 4,640 B).
- `include/engine/asd_texture.h` / `src/engine/asd_texture.cpp`: texture/TMX/TGA upload, texture table lookup, sprite binding, primitive render data, and the tiny memory alignment helper (10 functions, 4,804 B).
- `config/functions.csv`: flips the 28 ledger rows from `todo` to `non_matching` and records the new source files.
- `tests/test_progress.py`: pins the exact byte/function counts after every task.

**Tech Stack:** C++20, ARMv6K disassembly (`tools/split_asm.py` + Capstone), Python 3.12 progress verifier.

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints

- Target binary: `extracted/exefs/code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Never invent struct layouts or behavior: every field offset, branch, call target, and constant in a function body must be traceable to the function's disassembly (`python tools/split_asm.py --addr 0x...`).
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` immediately above its definition and use the exact address/size/name from `config/functions.csv`.
- Do not mark a function `non_matching` unless its body implements the observed control flow; comment-only placeholders remain `stub`.
- Strict TDD: update `tests/test_progress.py` first (RED), implement, then run `python tools/progress.py --write` and the full suite (GREEN), then commit.
- Preserve existing `src/`/`include/` style: `namespace smt4::engine`, fixed-width `u8/u16/u32/s32/f32` from `types.h`, four-space indentation.

## Review Focus

- **Truncated reconstruction:** a 4,000-byte `EffectEditor_func_002fcd20` or 2,028-byte `AsdModel_func_0031dc4c` reduced to a handful of statements is a defect even when the progress verifier accepts it; the reviewer must compare the body against the disassembly's call and branch count.
- **Fabricated offsets:** struct fields or literal offsets that do not appear in `LDR/STR [reg, #imm]` operands of the disassembly are a defect.
- **Shared globals:** accesses to `.bss`/`.data` addresses (for example `0x00464af0` in `AsdModel_func_0010495c`) must be declared once and documented, not re-invented per function.
- **Cross-function contracts:** loaders that return allocated objects or write status fields must define a header contract that later callers can use; no `void*`-only signatures when the disassembly establishes a concrete return register.
- **Progress claims:** `tests/test_progress.py` must assert the exact counts after each task, and `PROGRESS.md`/`README.md` must be regenerated only by `python tools/progress.py --write`.

---

### Task 1: AsdModel loaders and EffectEditor (10 functions, 13,276 bytes)

**Files:**
- Create: `include/engine/asd_model.h`
- Create: `src/engine/asd_model.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Interfaces:**
- Consumes: `u8/u16/u32/s32/f32` from `include/types.h`; ARM literal-pool evidence from `tools/split_asm.py`.
- Produces: `smt4::engine` declarations for the ten ledger symbols below. The implementer must recover parameter and return types from the prologue/epilogue and call sites, then freeze them in `asd_model.h` for the rest of the plan.

**Functions (must match `config/functions.csv` exactly):**
- `AsdModel_func_0010495c`: `0x0010495c` (1,108 B)
- `AsdModel_func_0014515c`: `0x0014515c` (688 B)
- `AsdModel_func_0014ec68`: `0x0014ec68` (792 B)
- `AsdModel_func_00192594`: `0x00192594` (484 B)
- `AsdModel_func_001fe470`: `0x001fe470` (288 B)
- `AsdModel_func_002a94e8`: `0x002a94e8` (1,508 B)
- `AsdModel_func_002a9acc`: `0x002a9acc` (1,880 B)
- `AsdModel_func_002b2b78`: `0x002b2b78` (340 B)
- `AsdModel_func_0031dc4c`: `0x0031dc4c` (2,028 B)
- `EffectEditor_func_002fcd20`: `0x002fcd20` (4,160 B)

**Reconnaissance anchors:** `AsdModel_func_0010495c` loads `"ShadowModel.bcmdl"` and resolves the `"ShadowModel"` node; `AsdModel_func_0014515c` validates the `"ATBC"` magic before reading animation-table counts. Record every other discovered literal/string in the header comment for its function.

- [ ] **Step 1: Update progress test expectations (RED)**

In `tests/test_progress.py::test_real_repo_progress_matches_text_size`, change the expected values to:

```python
self.assertEqual(stats["decompiled_functions"], 182)
self.assertEqual(stats["decompiled_bytes"], 244620)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 221)
self.assertEqual(stats["total_explored_bytes"], 492860)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `182 != 172` in `test_real_repo_progress_matches_text_size`.

- [ ] **Step 3: Disassemble every function and implement the header/source**

For each of the ten functions run:

```powershell
python tools/split_asm.py --addr 0x0010495c
```

Reconstruct the body from the ARM listing. Keep the ledger symbol name for the C++ symbol; add a comment naming the original Atlus module and the literal strings resolved by the listing. Define only structs/offsets proven by `LDR/STR [reg, #imm]` accesses. `EffectEditor_func_002fcd20` is the authoring/editor entry point; its body must preserve every observed branch and call rather than collapsing to a summary.

- [ ] **Step 4: Update the ledger and verify GREEN**

In `config/functions.csv`, set `status` to `non_matching` and `src_file` to `src/engine/asd_model.cpp` for each of the ten addresses. Then run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: `Verified 182 / 10,349 decompiled functions (244,620 / 3,139,108 bytes, 7.7931%)` and all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add include/engine/asd_model.h src/engine/asd_model.cpp config/functions.csv tests/test_progress.py PROGRESS.md README.md
git commit -m "feat(engine): decompile AsdModel loaders and EffectEditor (+13,276 B, 15.70% explored)"
```

---

### Task 2: AsdText, AsdFont, message layout and AsdListBox (8 functions, 4,640 bytes)

**Files:**
- Create: `include/engine/asd_text.h`
- Create: `src/engine/asd_text.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Interfaces:**
- Consumes: the `smt4::engine` conventions established in Task 1; `include/types.h`.
- Produces: text/font/list-box declarations used by later HUD work. Functions in category `ui` stay in `smt4::engine` only if their disassembly shows `AsdText`/`AsdFont` ownership; otherwise declare them in the same header under `namespace smt4::ui` and note the split in the header comment.

**Functions:**
- `AsdFont_func_0010a588`: `0x0010a588` (152 B, `ui`)
- `AsdFont_func_002c4710`: `0x002c4710` (1,004 B, `ui`)
- `message_func_002c4c2c`: `0x002c4c2c` (508 B, `ui`)
- `AsdListBox_func_002272d0`: `0x002272d0` (172 B, `ui`)
- `AsdListBox_func_0025c550`: `0x0025c550` (628 B, `ui`)
- `AsdListBox_func_00263408`: `0x00263408` (300 B, `ui`)
- `AsdText_func_00286c5c`: `0x00286c5c` (1,596 B, `engine`)
- `AsdText_func_00296de0`: `0x00296de0` (280 B, `engine`)

- [ ] **Step 1: Update progress test expectations (RED)**

Change the expected values to:

```python
self.assertEqual(stats["decompiled_functions"], 190)
self.assertEqual(stats["decompiled_bytes"], 249260)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 229)
self.assertEqual(stats["total_explored_bytes"], 497500)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `190 != 182` in `test_real_repo_progress_matches_text_size`.

- [ ] **Step 3: Disassemble and implement**

Run `python tools/split_asm.py --addr <address>` for each of the eight functions. Reconstruct measurement/layout loops exactly, including the `AsdListBox` cursor geometry arithmetic and the `AsdText` message-source handling. Preserve magic strings and table lookups verbatim.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching` and `src_file=src/engine/asd_text.cpp` for all eight rows, then run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: `Verified 190 / 10,349 decompiled functions (249,260 / 3,139,108 bytes, 7.9408%)` and all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add include/engine/asd_text.h src/engine/asd_text.cpp config/functions.csv tests/test_progress.py PROGRESS.md README.md
git commit -m "feat(engine): decompile AsdText, AsdFont and AsdListBox layout (+4,640 B, 15.84% explored)"
```

---

### Task 3: Texture, texture-table, sprite and primitive plumbing (10 functions, 4,804 bytes)

**Files:**
- Create: `include/engine/asd_texture.h`
- Create: `src/engine/asd_texture.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Interfaces:**
- Consumes: Task 1/2 engine conventions; PICA200 upload helpers already declared in `include/ui/status_down.h` where signatures match.
- Produces: texture/TMX/TGA loaders, `AsdTMTexTable` lookup, `AsdTMSpr` binding, `AsdPrimRenderData` setup, and `AsdMemory_func_002c23f8` alignment helper.

**Functions:**
- `AsdPrim_func_001042c8`: `0x001042c8` (176 B)
- `AsdTMSpr_func_00144fbc`: `0x00144fbc` (416 B, `ui`)
- `AsdTexTMX_func_0019fb58`: `0x0019fb58` (756 B)
- `AsdTexTGA_func_00257e6c`: `0x00257e6c` (436 B)
- `AsdTexture_func_002bd730`: `0x002bd730` (528 B)
- `AsdTexture_func_002bd940`: `0x002bd940` (172 B)
- `AsdTMTexTable_func_002c4e28`: `0x002c4e28` (620 B)
- `AsdTMTexTable_func_002c5b04`: `0x002c5b04` (652 B)
- `AsdPrimRenderData_func_00346db0`: `0x00346db0` (992 B)
- `AsdMemory_func_002c23f8`: `0x002c23f8` (56 B)

- [ ] **Step 1: Update progress test expectations (RED)**

Change the expected values to:

```python
self.assertEqual(stats["decompiled_functions"], 200)
self.assertEqual(stats["decompiled_bytes"], 254064)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 239)
self.assertEqual(stats["total_explored_bytes"], 502304)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `200 != 190` in `test_real_repo_progress_matches_text_size`.

- [ ] **Step 3: Disassemble and implement**

Run `python tools/split_asm.py --addr <address>` for each function. Preserve format magic checks (`TMX`, `TGA`, texture-table strides), VRAM/stride arithmetic, and the exact `AsdMemory_func_002c23f8` alignment expression. `AsdPrimRenderData_func_00346db0` must retain its vertex/index upload sequence rather than a summary comment.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching` and `src_file=src/engine/asd_texture.cpp` for all ten rows, then run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: `Verified 200 / 10,349 decompiled functions (254,064 / 3,139,108 bytes, 8.0935%)` and `Total Architecture Explored: 239 functions (502,304 bytes, 16.0015%)`; all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add include/engine/asd_texture.h src/engine/asd_texture.cpp config/functions.csv tests/test_progress.py PROGRESS.md README.md
git commit -m "feat(engine): decompile texture, table and primitive plumbing (+4,804 B, 16.0% milestone reached at 16.0015%)"
```
