# 15% Decompilation Milestone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompile 24 functions totaling 163,192 bytes across Engine 3D Field & PICA200 texture streaming, Battle Combat HUD & Ailments, FlowScript VM Interpreter, Camp Demonica Storage & Whisper events, and Facility UIs (Terminal, Quest Board, Shop Catalog, Mikado Castle, Debug HUD). Crossing this plan elevates decompilation progress from **316,392 bytes (10.0790%)** to **479,584 bytes (15.2777%)**, passing the **15.0% decompilation milestone** for Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/engine/map_field.h` & `src/engine/map_field.cpp`: Implements `Map_Field3DManager` (`0x00208ce8`, 16,796 B) and `Engine_TextureStreamer` (`0x00386184`, 5,964 B) for 3D exploration environments, smoke emitters, skyboxes, and PICA200 texture mipmap streaming.
- `include/ui/battle_hud.h` & `src/ui/battle_hud.cpp`: Implements `Ui_NkmBaseTableLoad` (`0x003efa10`, 12,708 B), `Ui_BattleCommandMenu` (`0x0025d3fc`, 7,328 B), `Ui_BattleMessageWindow` (`0x003f34f8`, 7,984 B), and `Ui_BattleActionEffectOverlay` (`0x003ec954`, 6,616 B) for battle encounter tables and real-time combat menus.
- `include/battle/battle_ailment.h` / `battle_scout.h` & `src/battle/...`: Implements `Btl_StatusEffectCalc` (`0x0021c598`, 5,420 B) and `Btl_DemonNegotiationCalc` (`0x003c6714`, 4,724 B) for ailment status affliction (Poison, Sick, Panic, Sleep, Bind) and demon negotiation/scout conversation logic.
- `include/camp/...` & `src/camp/...`: Implements `Camp_DemonicaArchiveLoad` (`0x00114374`, 6,144 B), `Camp_WhisperSkillTransfer` (`0x00332100`, 5,968 B), `Camp_ItemInventorySort` (`0x002d966c`, 5,336 B), `Ui_DemonicaAppStore` (`0x00325478`, 5,072 B), and `Ui_DemonCompendiumSearch` (`0x003b4bc0`, 5,520 B) for Demonica storage, Whisper skill inheritance, and Burroughs app store.
- `include/script/script_vm.h` & `src/script/script_vm.cpp`: Implements `FlowScript_OpcodeEvaluator` (`0x0027154c`, 8,316 B), `FlowScript_EventVmExecute` (`0x001955bc`, 5,812 B), `FlowScript_BranchCondition` (`0x001fc644`, 4,876 B), and `FlowScript_MessageWindowHook` (`0x00307978`, 4,832 B) for FlowScript (`.bf`) VM execution.
- `include/ui/...` & `src/ui/...` / `src/shop/...`: Implements `Ui_DebugStatsRender` (`0x001b1a90`, 8,352 B), `Ui_MemoryArenaAllocate` (`0x00345194`, 7,068 B), `Ui_TerminalSceneRender` (`0x001d98c4`, 5,880 B), `Ui_QuestCenterListRender` (`0x0021243c`, 5,820 B), `Ui_ShopInventoryCatalog` (`0x003b35a8`, 5,656 B), `Ui_MikadoCastleScene` (`0x001eeea0`, 5,556 B), and `Ui_StatusScreenSkills` (`0x001ce98c`, 5,444 B) for town facilities, quest boards, shops, and debug metrics.
- `config/functions.csv`: Registers all 24 functions with status `non_matching` and their source files.
- `tests/test_progress.py`: Enforces byte-accurate and function-accurate progress at each task boundary using strict TDD.

**Tech Stack:** C++20, ARMv6K disassembly, Python 3.12 (progress tracking & test suite).

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints
- Target binary: `code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Strictly adhere to TDD: update test assertion (RED) -> implement minimal matching code -> verify test passes (GREEN) -> commit.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` and match `config/functions.csv`.

---

### Task 1: Engine 3D Field Environment & PICA200 Texture Pipeline (`map_field.cpp`, 2 functions, 22,760 bytes)

**Files:**
- Create: `include/engine/map_field.h`
- Create: `src/engine/map_field.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Map_Field3DManager`: `0x00208ce8` (16,796 B)
- `Engine_TextureStreamer`: `0x00386184` (5,964 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 189 functions and 339,152 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in `include/engine/map_field.h` and implement in `src/engine/map_field.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(engine): implement 3D field actor environment and texture streamer (+22,760 B, 10.80% reached)`.

---

### Task 2: Battle Combat HUD, Command Selector & Encounter Loader (`battle_hud.cpp`, 4 functions, 34,636 bytes)

**Files:**
- Create: `include/ui/battle_hud.h`
- Create: `src/ui/battle_hud.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Ui_NkmBaseTableLoad`: `0x003efa10` (12,708 B)
- `Ui_BattleCommandMenu`: `0x0025d3fc` (7,328 B)
- `Ui_BattleMessageWindow`: `0x003f34f8` (7,984 B)
- `Ui_BattleActionEffectOverlay`: `0x003ec954` (6,616 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 193 functions and 373,788 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in `include/ui/battle_hud.h` and implement in `src/ui/battle_hud.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(battle): implement battle command menu, encounter loader and combat HUD (+34,636 B, 11.91% reached)`.

---

### Task 3: Battle Ailment Evaluator & Demon Negotiation Engine (`battle_ailment.cpp` & `battle_scout.cpp`, 2 functions, 10,144 bytes)

**Files:**
- Create: `include/battle/battle_ailment.h`
- Create: `src/battle/battle_ailment.cpp`
- Create: `include/battle/battle_scout.h`
- Create: `src/battle/battle_scout.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Btl_StatusEffectCalc`: `0x0021c598` (5,420 B)
- `Btl_DemonNegotiationCalc`: `0x003c6714` (4,724 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 195 functions and 383,932 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in `include/battle/battle_ailment.h`, `include/battle/battle_scout.h` and implement in `src/battle/battle_ailment.cpp`, `src/battle/battle_scout.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(battle): implement status ailment calculator and demon negotiation engine (+10,144 B, 12.23% reached)`.

---

### Task 4: FlowScript VM Interpreter Core & Event Engine (`script_vm.cpp`, 4 functions, 23,836 bytes)

**Files:**
- Create: `include/script/script_vm.h`
- Create: `src/script/script_vm.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `FlowScript_OpcodeEvaluator`: `0x0027154c` (8,316 B)
- `FlowScript_EventVmExecute`: `0x001955bc` (5,812 B)
- `FlowScript_BranchCondition`: `0x001fc644` (4,876 B)
- `FlowScript_MessageWindowHook`: `0x00307978` (4,832 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 199 functions and 407,768 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in `include/script/script_vm.h` and implement in `src/script/script_vm.cpp`**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(script): implement FlowScript VM opcode evaluator and event engine (+23,836 B, 12.99% reached)`.

---

### Task 5: Camp Demonica Storage, Whisper Transfers & App Store (`camp_archive.cpp`, `whisper_event.cpp`, `camp_inventory.cpp`, `app_store.cpp`, `compendium_search.cpp`, 5 functions, 28,040 bytes)

**Files:**
- Create: `include/camp/camp_archive.h`
- Create: `src/camp/camp_archive.cpp`
- Create: `include/camp/whisper_event.h`
- Create: `src/camp/whisper_event.cpp`
- Create: `include/camp/camp_inventory.h`
- Create: `src/camp/camp_inventory.cpp`
- Create: `include/camp/app_store.h`
- Create: `src/camp/app_store.cpp`
- Create: `include/camp/compendium_search.h`
- Create: `src/camp/compendium_search.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Camp_DemonicaArchiveLoad`: `0x00114374` (6,144 B)
- `Camp_WhisperSkillTransfer`: `0x00332100` (5,968 B)
- `Camp_ItemInventorySort`: `0x002d966c` (5,336 B)
- `Ui_DemonicaAppStore`: `0x00325478` (5,072 B)
- `Ui_DemonCompendiumSearch`: `0x003b4bc0` (5,520 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 204 functions and 435,808 bytes.
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in headers and implement in source files**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(camp): implement Demonica archive loader, whisper events, item inventory, and Burroughs app store (+28,040 B, 13.88% reached)`.

---

### Task 6: Facilities HUD - Terminal, Mikado Castle, Quest Board, Shop Catalog & Debug Profiler (7 functions, 43,776 bytes)

**Files:**
- Create: `include/ui/debug_hud.h`
- Create: `src/ui/debug_hud.cpp`
- Create: `include/ui/ui_memory.h`
- Create: `src/ui/ui_memory.cpp`
- Create: `include/ui/terminal_ui.h`
- Create: `src/ui/terminal_ui.cpp`
- Create: `include/ui/quest_ui.h`
- Create: `src/ui/quest_ui.cpp`
- Create: `include/shop/shop_catalog.h`
- Create: `src/shop/shop_catalog.cpp`
- Create: `include/ui/mikado_ui.h`
- Create: `src/ui/mikado_ui.cpp`
- Create: `include/ui/status_skills.h`
- Create: `src/ui/status_skills.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `Ui_DebugStatsRender`: `0x001b1a90` (8,352 B)
- `Ui_MemoryArenaAllocate`: `0x00345194` (7,068 B)
- `Ui_TerminalSceneRender`: `0x001d98c4` (5,880 B)
- `Ui_QuestCenterListRender`: `0x0021243c` (5,820 B)
- `Ui_ShopInventoryCatalog`: `0x003b35a8` (5,656 B)
- `Ui_MikadoCastleScene`: `0x001eeea0` (5,556 B)
- `Ui_StatusScreenSkills`: `0x001ce98c` (5,444 B)

- [ ] **Step 1: Update progress test expectations (RED)**
  - Update `tests/test_progress.py` to expect 211 functions and 479,584 bytes (reaching **15.2777%**, surpassing the **15.0% milestone**!).
- [ ] **Step 2: Run test to verify it fails**
  - Run `python -m unittest discover -s tests -v`.
- [ ] **Step 3: Define structures in headers and implement in source files**
- [ ] **Step 4: Update `config/functions.csv` and run test to verify it passes (GREEN)**
  - Run `python tools/progress.py --write` and `python -m unittest discover -s tests -v`.
- [ ] **Step 5: Commit**
  - Commit: `feat(ui): implement Terminal 3D portal, Mikado Castle, Quest Board, Shop Catalog and Debug HUD (+43,776 B, 15.0% milestone reached at 15.28%)`.
