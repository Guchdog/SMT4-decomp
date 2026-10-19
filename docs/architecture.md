# Shin Megami Tensei IV (`sdds4` / `XRD686`) Engine & HUD Architecture

## 1. Internal Project Hierarchy (`XRD686`)

Static analysis of `.rodata` and inline `ADR` string pools inside `code.bin` recovered the original Atlus source directory structure (`c:\SMT4\XRD686\...`), which splits into two top-level trees:

1. **`c:\SMT4\XRD686\AsdSDK\Source\...` (Atlus 3DS Engine SDK):**
   - `Sys/File/`: `AsdFile.cpp`, `AsdLoadFile.cpp`
   - `Sys/Mem/`: `AsdMemory.cpp` (`0x002c4b84` allocator, `0x002c4b30` zero-fill)
   - `Sys/Kernel/`: `AsdProcess.cpp`, `AsdSequence.cpp` (`0x002c5978` CALC task spawner, `0x002c4c00` DDRAW task spawner)
   - `Sys/Gx/`: `AsdGxRenderSystem.cpp`, `AsdGxCommandList.cpp` (dual-screen LCD pipelines: `DrawULCD2DBegin` for top screen, `DrawDLCD2DBegin` for bottom screen)
   - `Gfx/`: `AsdCamera.cpp`, `AsdModel.cpp`, `AsdMdlManager.cpp`, `AsdTexture.cpp`, `AsdTexTGA.cpp`, `AsdTMSpr.cpp`, `AsdTMTexTable.cpp`, `AsdFont.cpp`, `AsdText.cpp`, `AsdPrimRenderData.cpp`
   - `Util/`: `AsdList.cpp`, `AsdListBox.cpp`

2. **`c:\SMT4\XRD686\sdds4\program\...` (Game & UI Subsystems):**
   - `camp/`: `IfTouch.cpp` (bottom-screen touch controller), `GauntletAppMenu/GauntletAppMenu.cpp`, `CommonBg/CommonBg.cpp`, `Unite/UniteEffect.cpp`, `CampCec/*`
   - `status/`: `StatusDown.cpp` (bottom-screen status HUD / `TMD CALC` & `TMD DDRAW`)
   - `battle/`: `btlMain.cpp`, `btlStage.cpp`, `btlTargetSelect.cpp`, `btlActionReflect.cpp`, `EnemyDraw/*`, `Filter/*`, `Talk/btlTalkCommand.cpp`
   - `font/`: `message.cpp`, `SearchWin/SearchWin.cpp`
   - `gamedata/`: `GameData.cpp`, `SaveLoadProcess.cpp`, `unite/UniteCtrl.cpp`, `nkm/NkmGrowEvent.cpp`
   - `title/`: `titleConfig.cpp`
   - `shop/`: `shopMain.cpp`
   - `bible/`: `bibleDevil.cpp`, `bibleAnalyze.cpp`, `bibleLegionSkill.cpp`, `bibleLegionDraw.cpp`

---

## 2. UI / HUD Table Format (`.tbb` -> `TBCR` / `TBL1`)

Decompilation of `Tbb_GetSubTable` (`0x002ac2f4`), `Tbb_GetGlobalSubTable` (`0x002c0ec4`), `Tbb_GetPayloadData` (`0x002c0e9c`), and `Tbb_GetRowCount` (`0x002c0e4c`) in [`src/ui/tbb_loader.cpp`](../src/ui/tbb_loader.cpp) established the exact binary format of `.tbb` files (such as `battle/UI/BattleComTable.tbb`, `camp/PartyPanelHelp.tbb`, and `saveLoadUI/SaveLoadUITable.tbb`):

- **`TbcrHeader` (`TBCR` Container):**
  - `0x00`: `magic` = `'TBCR'` (`0x52434254`)
  - `0x04`: `header_size` (typically `0x10`)
  - `0x08`: `table_count`
  - `0x0C`: `u32 table_offsets[table_count]` (offsets added to `header_size`)
- **`Tbl1Header` (`TBL1` Sub-Table):**
  - `0x00`: `magic` = `'TBL1'` (`0x314C4254`)
  - `0x04`: `payload_size` (total bytes of row data)
  - `0x08`: `row_stride` (bytes per entry; `row_count = payload_size / row_stride`)
  - `0x0C`: `reserved` (`0x10`)
  - `0x10..`: Row payload array returned by `Tbb_GetPayloadData()`.
- **Global TBB Slot Table (`0x0049382C` in `.bss`):**
  - Holds `0x43` (67) 16-byte `GlobalTbbSlot` entries, indexed by `slot_id` in `Tbb_GetGlobalSubTable(slot_id, table_index)`.
