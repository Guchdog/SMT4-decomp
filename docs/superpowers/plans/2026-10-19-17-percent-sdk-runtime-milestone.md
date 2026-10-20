# 17% Decompilation Milestone: SDK Runtime, Sound, Scene, Effects & AOC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 70 previously-unmapped `AsdSDK`, effects, and AOC runtime functions totaling 31,512 bytes, raising total architecture explored from **502,304 bytes (16.0015%)** to **533,816 bytes (17.0053%)** and authentically decompiled code from **254,064 bytes (8.0935%)** to **285,576 bytes (9.0973%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/engine/asd_file.h` / `src/engine/asd_file.cpp`: AsdFile/AsdLoadFile/AsdMemory/AsdSaveCommon (14 functions, 5,136 B).
- `include/engine/asd_sound.h` / `src/engine/asd_sound.cpp`: AsdSoundSystem, sound effects, sound test (9 functions, 3,588 B).
- `include/engine/asd_scene.h` / `src/engine/asd_scene.cpp`: AsdCamera, AsdScene, AsdProcess, AsdSequence, task spawner (11 functions, 4,356 B).
- `include/engine/asd_frame.h` / `src/engine/asd_frame.cpp`: FrameTex, Npc2d, SmokeFade, EffectEditor scene helpers (8 functions, 5,376 B).
- `include/nn/mobiclip.h` / `src/nn/mobiclip.cpp` plus `include/engine/aoc.h` / `src/engine/aoc.cpp`: Mobiclip playback and S4 helper layer (5 functions, 2,564 B), AOC file/main/boot/application/texture control (10 functions, 5,204 B).
- `include/engine/asd_effect.h` / `src/engine/asd_effect.cpp`: effParts / effP2A / effTLP particle, geometry and track primitives (13 functions, 5,288 B).
- `config/functions.csv`: flips the 70 rows from `todo` to `non_matching` with the new source files.
- `tests/test_progress.py`: pins exact cumulative counters after every task.

**Tech Stack:** C++20, ARMv6K disassembly (`tools/split_asm.py` + Capstone), Python 3.12 progress verifier.

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints

- Target binary: `extracted/exefs/code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Never invent struct layouts or behavior: every field offset, branch, call target, and constant in a function body must be traceable to the function's disassembly (`python tools/split_asm.py --addr 0x...`). Pre-indexed loads (`LDR rX,[rY,#imm]!`) require citing the effective post-writeback offset.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` immediately above its definition and use the exact address/size/name from `config/functions.csv`.
- Do not mark a function `non_matching` unless its body implements the observed control flow; comment-only placeholders remain `stub`.
- Strict TDD: update `tests/test_progress.py` first (RED), implement, then run `python tools/progress.py --write` and the full suite (GREEN), then commit.
- Preserve existing style: fixed-width types from `include/types.h`, four-space indentation, opaque structs with `static_assert(offsetof(...))` for proven offsets.
- One declaration per binary address across translation units: put shared helper declarations in `include/engine/asd_symbols.h` (created in the 16% milestone) or the new module header, with one name and one linkage.

## Review Focus

- **Pre-indexed writeback offsets:** the most likely failure is reading the displacement of the second instruction as if the base were unchanged. Every `LDR/STR [reg,#imm]!` must be expanded to `base + imm + next_imm` in the code and comment.
- **Descriptor layouts:** object-create descriptors and upload descriptors must preserve field order/size exactly, including unaligned fields. Do not start a descriptor with a `const char*` unless the disassembly's first slot is the name.
- **Summary stubs:** a 1,808-byte `effParts_func_002a51dc` or 2,220-byte `aocFileLoad_func_0015c728` reduced to a few statements is a defect even when the progress verifier accepts it.
- **Sound/AOC boundary contracts:** playback handles, buffer pointers, and state fields written by one function and read by another must be documented in the header.
- **Progress claims:** exact cumulative counters after each task; `PROGRESS.md`/`README.md` regenerated only by `python tools/progress.py --write`.

---

### Task 1: AsdFile, AsdLoadFile, AsdMemory and AsdSaveCommon (14 functions, 5,136 bytes)

**Files:**
- Create: `include/engine/asd_file.h`
- Create: `src/engine/asd_file.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `AsdFile_func_0010250c`: `0x0010250c` (296 B)
- `AsdFile_func_0010d070`: `0x0010d070` (272 B)
- `AsdFile_func_00113d58`: `0x00113d58` (1,564 B)
- `AsdFile_func_002b0434`: `0x002b0434` (480 B)
- `AsdLoadFile_func_002ae6c8`: `0x002ae6c8` (336 B)
- `AsdMemory_func_0010376c`: `0x0010376c` (820 B)
- `AsdMemory_func_00144978`: `0x00144978` (320 B)
- `AsdMemory_func_002c684c`: `0x002c684c` (112 B)
- `AsdMemory_func_00262ac0`: `0x00262ac0` (104 B)
- `AsdMemory_func_00346d38`: `0x00346d38` (120 B)
- `AsdMemory_func_00348a1c`: `0x00348a1c` (120 B)
- `AsdMemory_func_0034b3dc`: `0x0034b3dc` (120 B)
- `AsdSaveCommon_func_0021041c`: `0x0021041c` (204 B)
- `AsdSaveCommon_func_002104e8`: `0x002104e8` (268 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 214)
self.assertEqual(stats["decompiled_bytes"], 259200)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 253)
self.assertEqual(stats["total_explored_bytes"], 507440)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `214 != 200`.

- [ ] **Step 3: Disassemble and implement**

Run `python tools/split_asm.py --addr <address>` for each function. Reconstruct file-open/read/write paths, allocator bookkeeping, and save-common state. Preserve every observed call target and error branch.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching` and `src_file=src/engine/asd_file.cpp` for the 14 rows; run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: 214 / 259,200 B, 39 / 248,240 B, 253 / 507,440 B; all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add include/engine/asd_file.h src/engine/asd_file.cpp config/functions.csv tests/test_progress.py PROGRESS.md README.md
git commit -m "feat(engine): decompile AsdFile, AsdMemory and AsdSaveCommon (+5,136 B, 16.16% explored)"
```

---

### Task 2: AsdSoundSystem, sound effects and sound test (9 functions, 3,588 bytes)

**Files:**
- Create: `include/engine/asd_sound.h`
- Create: `src/engine/asd_sound.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `soundEffect_func_0010368c`: `0x0010368c` (184 B)
- `soundEffect_func_00109524`: `0x00109524` (240 B)
- `AsdSoundSystem_func_00109690`: `0x00109690` (1,040 B)
- `AsdSoundSystem_func_0010b974`: `0x0010b974` (176 B)
- `AsdSoundSystem_func_0010c078`: `0x0010c078` (380 B)
- `AsdSoundSystem_func_0010c5d4`: `0x0010c5d4` (480 B)
- `AsdSoundSystem_func_0010d40c`: `0x0010d40c` (516 B)
- `AsdSoundSystem_func_002c1df4`: `0x002c1df4` (308 B)
- `soundTest_func_001ea808`: `0x001ea808` (264 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 223)
self.assertEqual(stats["decompiled_bytes"], 262788)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 262)
self.assertEqual(stats["total_explored_bytes"], 511028)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `223 != 214`.

- [ ] **Step 3: Disassemble and implement**

Preserve DSP/audio command registers, channel handles, volume/pan arithmetic, and stream-state transitions. Document every handle offset in the header.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching` and `src_file=src/engine/asd_sound.cpp`; run `python tools/progress.py --write` and the suite. Expected: 223 / 262,788 B, 262 / 511,028 B.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile AsdSoundSystem and sound effects (+3,588 B, 16.28% explored)"
```

---

### Task 3: AsdCamera, AsdScene, AsdProcess and AsdSequence (11 functions, 4,356 bytes)

**Files:**
- Create: `include/engine/asd_scene.h`
- Create: `src/engine/asd_scene.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `AsdCamera_func_00105c50`: `0x00105c50` (340 B)
- `AsdCamera_func_00310124`: `0x00310124` (804 B)
- `AsdScene_func_0010bd34`: `0x0010bd34` (300 B)
- `AsdScene_func_0010e5f0`: `0x0010e5f0` (476 B)
- `AsdScene_func_001186b4`: `0x001186b4` (388 B)
- `AsdScene_func_00118c7c`: `0x00118c7c` (448 B)
- `AsdScene_func_002cb788`: `0x002cb788` (204 B)
- `AsdProcess_func_00102e80`: `0x00102e80` (152 B)
- `AsdProcess_func_00118488`: `0x00118488` (556 B)
- `AsdSequence_func_002c59b8`: `0x002c59b8` (180 B)
- `Task_func_002861f8`: `0x002861f8` (508 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 234)
self.assertEqual(stats["decompiled_bytes"], 267144)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 273)
self.assertEqual(stats["total_explored_bytes"], 515384)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `234 != 223`.

- [ ] **Step 3: Disassemble and implement**

Preserve camera matrix/euler updates, scene node traversal, process state transitions, and task spawn arguments. Cite the effective offsets for any pre-indexed load.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching` and `src_file=src/engine/asd_scene.cpp`; expected 234 / 267,144 B, 273 / 515,384 B.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile AsdCamera, AsdScene and task processing (+4,356 B, 16.42% explored)"
```

---

### Task 4: FrameTex, Npc2d, SmokeFade and EffectEditor scene helpers (8 functions, 5,376 bytes)

**Files:**
- Create: `include/engine/asd_frame.h`
- Create: `src/engine/asd_frame.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `FrameTex_func_00104378`: `0x00104378` (1,508 B)
- `FrameTex_func_00280d30`: `0x00280d30` (524 B)
- `Npc2d_func_002523d0`: `0x002523d0` (336 B)
- `Npc2d_func_002860b4`: `0x002860b4` (324 B)
- `Npc2d_func_0031bdd0`: `0x0031bdd0` (508 B)
- `Npc2d_func_002fdfb8`: `0x002fdfb8` (336 B)
- `SmokeFade_func_002cf0a0`: `0x002cf0a0` (568 B)
- `EffectEditor_func_0024246c`: `0x0024246c` (1,272 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 242)
self.assertEqual(stats["decompiled_bytes"], 272520)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 281)
self.assertEqual(stats["total_explored_bytes"], 520760)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `242 != 234`.

- [ ] **Step 3: Disassemble and implement**

Preserve texture-frame selection, 2D NPC sprite transforms, fade alpha interpolation, and editor scene hooks.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching` and `src_file=src/engine/asd_frame.cpp`; expected 242 / 272,520 B, 281 / 520,760 B.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile frame textures, Npc2d and SmokeFade (+5,376 B, 16.59% explored)"
```

---

### Task 5: Mobiclip playback and AOC runtime (15 functions, 7,768 bytes)

**Files:**
- Create: `include/nn/mobiclip.h`
- Create: `src/nn/mobiclip.cpp`
- Create: `include/engine/aoc.h`
- Create: `src/engine/aoc.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions (nn, `src/nn/mobiclip.cpp`):**
- `MobiclipCtrl_func_0017fb6c`: `0x0017fb6c` (584 B)
- `MobiclipCtrlProcess_func_002ef664`: `0x002ef664` (432 B)
- `helper_S4FsReader_func_0034e028`: `0x0034e028` (520 B)
- `helper_S4AudioDevice_func_0034e64c`: `0x0034e64c` (476 B)
- `helper_S4Player_func_003516a8`: `0x003516a8` (552 B)

**Functions (engine, `src/engine/aoc.cpp`):**
- `aocFileLoad_func_0015c728`: `0x0015c728` (2,220 B)
- `aocMain_func_001b0b00`: `0x001b0b00` (408 B)
- `aocBootProcess_func_00224ae0`: `0x00224ae0` (276 B)
- `aocApplication_func_0038b384`: `0x0038b384` (236 B)
- `aocApplication_func_0038b510`: `0x0038b510` (240 B)
- `aocFileContent_func_0038bd00`: `0x0038bd00` (408 B)
- `aocTexCtrl_func_00234ca8`: `0x00234ca8` (164 B)
- `aocTexCtrl_func_002a465c`: `0x002a465c` (460 B)
- `aocTexCtrl_func_003936e8`: `0x003936e8` (336 B)
- `aocTexCtrl_func_00393838`: `0x00393838` (456 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 257)
self.assertEqual(stats["decompiled_bytes"], 280288)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 296)
self.assertEqual(stats["total_explored_bytes"], 528528)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `257 != 242`.

- [ ] **Step 3: Disassemble and implement**

Preserve Mobiclip frame/audio ring-buffer state, `S4FsReader` file callbacks, AOC mount/load handles, and texture-control state. `aocFileLoad_func_0015c728` (2,220 B) must retain its chunk loop and error paths.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `src_file=src/nn/mobiclip.cpp` for the five nn rows and `src_file=src/engine/aoc.cpp` for the ten engine rows; expected 257 / 280,288 B, 296 / 528,528 B.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile Mobiclip playback and AOC runtime (+7,768 B, 16.84% explored)"
```

---

### Task 6: Particle and effect primitives (13 functions, 5,288 bytes)

**Files:**
- Create: `include/engine/asd_effect.h`
- Create: `src/engine/asd_effect.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `effParts_func_002a51dc`: `0x002a51dc` (1,808 B)
- `effParts_func_002490e0`: `0x002490e0` (580 B)
- `effP2A_func_00249324`: `0x00249324` (484 B)
- `effTLP_func_00249588`: `0x00249588` (420 B)
- `effParts_func_0024972c`: `0x0024972c` (164 B)
- `effParts_func_0024fda4`: `0x0024fda4` (192 B)
- `effParts_func_0024fe64`: `0x0024fe64` (196 B)
- `effParts_func_0025caa8`: `0x0025caa8` (128 B)
- `effParts_func_0025cc14`: `0x0025cc14` (164 B)
- `effParts_func_0028c920`: `0x0028c920` (348 B)
- `effParts_func_00192168`: `0x00192168` (124 B)
- `effParts_func_001d2460`: `0x001d2460` (104 B)
- `effParts_func_001e1970`: `0x001e1970` (576 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 270)
self.assertEqual(stats["decompiled_bytes"], 285576)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 309)
self.assertEqual(stats["total_explored_bytes"], 533816)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `270 != 257`.

- [ ] **Step 3: Disassemble and implement**

Preserve particle pool indexing, P2A/TLP animation curves, emitter lifetimes, and render-state toggles. `effParts_func_002a51dc` (1,808 B) must retain its observed loops and branches.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching` and `src_file=src/engine/asd_effect.cpp`; expected 270 / 285,576 B, 309 / 533,816 B (17.0053%); all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile particle and effect primitives (+5,288 B, 17.0% milestone reached at 17.0053%)"
```
