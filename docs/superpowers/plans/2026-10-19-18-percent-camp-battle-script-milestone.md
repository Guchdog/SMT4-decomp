# 18% Decompilation Milestone: Camp/Town, Battle, Script & Map Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 41 previously-unmapped camp/town, battle, script/event, map, and unite functions totaling 32,116 bytes, raising total architecture explored from **533,816 bytes (17.0053%)** to **565,932 bytes (18.0288%)** and authentically decompiled code from **285,576 bytes (9.0974%)** to **317,692 bytes (10.1201%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/camp/camp_cec.h` / `src/camp/camp_cec.cpp`: CampCec editor/view/settings (4 functions, 3,948 B).
- `include/camp/title_flow.h` / `src/camp/title_flow.cpp`: title flow, config, play log, terminal main (5 functions, 2,948 B).
- `include/battle/battle_extras.h` / `src/battle/battle_extras.cpp`: enemy draw, effect loading, debug/title battle helpers, filters, talk/help/game-over (10 functions, 9,724 B).
- `include/script/script_extras.h` / `src/script/script_extras.cpp`: NPC room, quest UI, script process, qc main/utility, clear save, event command/effect (8 functions, 7,088 B).
- `include/engine/map_runtime.h` / `src/engine/map_runtime.cpp`: map interface, lmap/map enemy/depart/main, navi, map EPL, 3D event opening, Nkm grow (9 functions, 4,996 B).
- `include/camp/unite_extras.h` / `src/camp/unite_extras.cpp`: unite/bible devil, legion draw/skill, UniteCtrl (5 functions, 3,412 B).
- `config/functions.csv`: flips the 41 rows from `todo` to `non_matching`.
- `tests/test_progress.py`: pins exact cumulative counters after every task.

**Tech Stack:** C++20, ARMv6K disassembly (`tools/split_asm.py` + Capstone), Python 3.12 progress verifier, optional MSVC BuildTools x86 compile checks.

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints

- Target binary: `extracted/exefs/code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Never invent struct layouts or behavior: every field offset, branch, call target, and constant must be traceable to the function's disassembly. Pre-indexed loads (`LDR rX,[rY,#imm]!`) must use the effective post-writeback offset.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` immediately above its definition with the exact ledger address/size/name.
- Do not mark a function `non_matching` unless its body implements the observed control flow; comment-only placeholders remain `stub`.
- One declaration per binary address: shared helpers go in `include/engine/asd_symbols.h` or the module header; no duplicate names/signatures/linkage.
- Every assigned global must have exactly one definition with the observed initial values (`.data` initializers included).
- Strict TDD: update `tests/test_progress.py` first (RED), implement, then `python tools/progress.py --write` and the full suite (GREEN), then commit. Compile the touched TUs with MSVC BuildTools x86 when available.
- Preserve style: fixed-width types from `include/types.h`, four-space indentation, opaque structs with `static_assert(offsetof(...))`.

## Review Focus

- **Compile correctness:** the Python gate cannot catch undeclared members or invalid casts. Every task must compile its TUs or explicitly report no compiler.
- **Pre-indexed writeback and stride arithmetic:** the most common historical defect is using a second displacement without the writeback base, or a 4/8/0x10/0x1C stride mismatch.
- **`.data` initializers:** globals read by the new bodies must carry their binary initial values, not zero-fill.
- **Descriptor/clone paths:** object-create descriptors, callback order, and clone/free ownership must match.
- **Summary stubs:** a 2,256-byte `EnemyDraw_func_0033eadc` or 2,144-byte `EftLoadFile_func_00249fac` reduced to a few statements is a defect.
- **Progress claims:** exact cumulative counters after each task; regenerate only via `python tools/progress.py --write`.

---

### Task 1: CampCec editor/view/settings and title flow (9 functions, 6,896 bytes)

**Files:**
- Create: `include/camp/camp_cec.h`
- Create: `src/camp/camp_cec.cpp`
- Create: `include/camp/title_flow.h`
- Create: `src/camp/title_flow.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions (camp_cec.cpp):**
- `CampCecEdit_func_002d678c`: `0x002d678c` (1,356 B)
- `CampCec_func_001ffaf4`: `0x001ffaf4` (1,068 B)
- `CampCecView_func_002d7410`: `0x002d7410` (1,012 B)
- `CampCecSetting_func_002f5bc0`: `0x002f5bc0` (512 B)

**Functions (title_flow.cpp):**
- `PlayLog_func_00194dbc`: `0x00194dbc` (648 B)
- `tmnlMain_func_001dafbc`: `0x001dafbc` (668 B)
- `titleConfig_func_002f4ca0`: `0x002f4ca0` (572 B)
- `Config_func_0018b660`: `0x0018b660` (536 B)
- `titleMain_func_001eb02c`: `0x001eb02c` (524 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 279)
self.assertEqual(stats["decompiled_bytes"], 292472)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 318)
self.assertEqual(stats["total_explored_bytes"], 540712)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `279 != 270`.

- [ ] **Step 3: Disassemble and implement**

Use `python tools/split_asm.py --addr <address>` for every function. Preserve CEC state transitions, editor row/cursor arithmetic, title menu flow, and config/play-log persistence. Cite every non-obvious offset.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `src_file=src/camp/camp_cec.cpp` for the four CEC rows and `src_file=src/camp/title_flow.cpp` for the five title rows, status `non_matching`. Run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: 279 / 292,472 B, 39 / 248,240 B, 318 / 540,712 B; all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(camp): decompile CampCec UI and title/config flow (+6,896 B, 17.23% explored)"
```

---

### Task 2: Battle extras, enemy draw, effect loading and filters (10 functions, 9,724 bytes)

**Files:**
- Create: `include/battle/battle_extras.h`
- Create: `src/battle/battle_extras.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `EnemyDraw_func_0033eadc`: `0x0033eadc` (2,256 B)
- `EftLoadFile_func_00249fac`: `0x00249fac` (2,144 B)
- `titleDbgBg_func_00117ca4`: `0x00117ca4` (1,292 B)
- `FilterXPoly_func_00348548`: `0x00348548` (1,032 B)
- `EffectProcess_func_002217d8`: `0x002217d8` (648 B)
- `btlTalkCommand_func_00318770`: `0x00318770` (516 B)
- `btlDebug_func_001e1f4c`: `0x001e1f4c` (504 B)
- `btlTalkBustUp_func_002959c4`: `0x002959c4` (472 B)
- `btlEditor_func_001f7f00`: `0x001f7f00` (432 B)
- `btlGameOver_func_0021ae48`: `0x0021ae48` (428 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 289)
self.assertEqual(stats["decompiled_bytes"], 302196)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 328)
self.assertEqual(stats["total_explored_bytes"], 550436)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `289 != 279`.

- [ ] **Step 3: Disassemble and implement**

Preserve enemy model/motion draw loops, effect file chunk loading, filter passes, talk command menu flow, game-over state, and debug/editor hooks. `EnemyDraw_func_0033eadc` and `EftLoadFile_func_00249fac` must retain their loops and error paths.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/battle/battle_extras.cpp`; expected 289 / 302,196 B, 328 / 550,436 B.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(battle): decompile enemy draw, effect loading and battle extras (+9,724 B, 17.54% explored)"
```

---

### Task 3: Script extras - NPC room, quest UI, qc and event (8 functions, 7,088 bytes)

**Files:**
- Create: `include/script/script_extras.h`
- Create: `src/script/script_extras.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `NpcRoom_func_0026df40`: `0x0026df40` (1,620 B)
- `UIQuest_func_0026a02c`: `0x0026a02c` (1,412 B)
- `qcUtility_func_003816e4`: `0x003816e4` (1,012 B)
- `scrScriptProcess_func_002972f8`: `0x002972f8` (892 B)
- `qcMain_func_001a969c`: `0x001a969c` (644 B)
- `eventCommand_func_0025955c`: `0x0025955c` (516 B)
- `EventEffect_func_0030a4fc`: `0x0030a4fc` (504 B)
- `clearSave_func_001e1118`: `0x001e1118` (488 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 297)
self.assertEqual(stats["decompiled_bytes"], 309284)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 336)
self.assertEqual(stats["total_explored_bytes"], 557524)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `297 != 289`.

- [ ] **Step 3: Disassemble and implement**

Preserve NPC room setup, quest list filtering, QC/script task dispatch, event command arguments, and clear-save state.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/script/script_extras.cpp`; expected 297 / 309,284 B, 336 / 557,524 B.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(script): decompile NPC room, quest UI and script process extras (+7,088 B, 17.76% explored)"
```

---

### Task 4: Map runtime - map interface, enemy/depart/main, navi and events (9 functions, 4,996 bytes)

**Files:**
- Create: `include/engine/map_runtime.h`
- Create: `src/engine/map_runtime.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `lmapMain_func_001d2b14`: `0x001d2b14` (760 B)
- `mapIf_func_0018aba8`: `0x0018aba8` (696 B)
- `NkmGrowEvent_func_0033bb94`: `0x0033bb94` (564 B)
- `mapEnemy_func_001a8924`: `0x001a8924` (552 B)
- `mapDepart_func_0027ee6c`: `0x0027ee6c` (552 B)
- `3dEventOpening_func_002f62d0`: `0x002f62d0` (552 B)
- `mapEpl_func_001fa408`: `0x001fa408` (468 B)
- `mapMain_func_001b4410`: `0x001b4410` (440 B)
- `naviMain_func_00291cac`: `0x00291cac` (412 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 306)
self.assertEqual(stats["decompiled_bytes"], 314280)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 345)
self.assertEqual(stats["total_explored_bytes"], 562520)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `306 != 297`.

- [ ] **Step 3: Disassemble and implement**

Preserve map transition state, enemy spawn/despawn, event opening, EPL lookup, and navi callback wiring.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/map_runtime.cpp`; expected 306 / 314,280 B, 345 / 562,520 B.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile map runtime and navigation hooks (+4,996 B, 17.92% explored)"
```

---

### Task 5: Unite/bible extras (5 functions, 3,412 bytes)

**Files:**
- Create: `include/camp/unite_extras.h`
- Create: `src/camp/unite_extras.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `unite_func_0022d5c8`: `0x0022d5c8` (892 B)
- `bibleDevil_func_003a7ad8`: `0x003a7ad8` (668 B)
- `UniteCtrl_func_003c9ebc`: `0x003c9ebc` (664 B)
- `bibleLegionDraw_func_003ad300`: `0x003ad300` (596 B)
- `bibleLegionSkill_func_003ab770`: `0x003ab770` (592 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 311)
self.assertEqual(stats["decompiled_bytes"], 317692)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 350)
self.assertEqual(stats["total_explored_bytes"], 565932)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `311 != 306`.

- [ ] **Step 3: Disassemble and implement**

Preserve demon fusion result/selection state, compendium entry draw/skill rows, and UniteCtrl state transitions.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/camp/unite_extras.cpp`; expected 311 / 317,692 B, 350 / 565,932 B (18.0288%); all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(camp): decompile unite and bible extras (+3,412 B, 18.0% milestone reached at 18.0288%)"
```
