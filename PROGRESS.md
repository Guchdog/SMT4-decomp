# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation Progress

## Overall `.text` Progress Summary

| Category | Functions | Code Size (Bytes) | Progress % | Status Description |
|----------|----------:|------------------:|-----------:|--------------------|
| **Decompiled (Reconstructed)** | 172 | 231,344 B | **7.3697%** | Substantial C++ logic reverse-engineered |
| **Scaffolded (Stubs & Interfaces)** | 39 | 248,240 B | 7.9080% | Headers, structs, and function skeletons |
| **Matching (Byte-for-Byte)** | 0 | 0 B | 0.0000% | 100% compiled machine code match |
| **Total Architecture Explored** | 211 | 479,584 B | **15.2777%** | Total identified & mapped into `src/` |
| **Remaining (Todo)** | 10,138 | 2,659,524 B | 84.7223% | Unmapped functions in `.text` |
| **Total `.text` Segment** | 10,349 | 3,139,108 B | 100.0000% | `0x00100000`–`0x003FE624` |

## Subsystem Breakdown

| Subsystem | Decompiled Funcs | Decompiled Bytes | Stub Funcs | Stub Bytes | Total Funcs | Total Bytes | Decompiled % | Explored % |
|-----------|-----------------:|-----------------:|-----------:|-----------:|------------:|------------:|-------------:|-----------:|
| `engine` | 3 | 224 B | 2 | 22,760 B | 2,363 | 726,520 B | 0.03% | 3.16% |
| `ui` | 133 | 97,148 B | 14 | 96,248 B | 1,238 | 682,348 B | 14.24% | 28.34% |
| `unknown` | 3 | 132 B | 0 | 0 B | 3,823 | 654,480 B | 0.02% | 0.02% |
| `script_vm` | 7 | 99,188 B | 3 | 22,836 B | 1,201 | 446,288 B | 22.23% | 27.34% |
| `camp` | 10 | 17,576 B | 6 | 70,276 B | 918 | 326,396 B | 5.38% | 26.92% |
| `battle` | 11 | 15,340 B | 11 | 32,664 B | 575 | 236,932 B | 6.47% | 20.26% |
| `shop` | 1 | 364 B | 3 | 3,456 B | 111 | 39,976 B | 0.91% | 9.56% |
| `crt` | 2 | 72 B | 0 | 0 B | 26 | 9,484 B | 0.76% | 0.76% |
| `nn_sdk` | 0 | 0 B | 0 | 0 B | 64 | 8,852 B | 0.00% | 0.00% |
| `unite` | 2 | 1,300 B | 0 | 0 B | 30 | 7,832 B | 16.60% | 16.60% |

## Explored Functions Ledger

| Address | Size (Bytes) | Category | Status | Symbol Name | Source File |
|---------|-------------:|----------|--------|-------------|-------------|
| `0x00100000` | 36 | `crt` | `non_matching` | `__start` | [`src/crt/start.cpp`](src/crt/start.cpp) |
| `0x00100024` | 36 | `crt` | `non_matching` | `__init_bss` | [`src/crt/start.cpp`](src/crt/start.cpp) |
| `0x0010299c` | 260 | `ui` | `non_matching` | `IfTouch_Init` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x0010a6fc` | 16 | `ui` | `non_matching` | `ComWin_SetParam1C` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010a70c` | 60 | `unknown` | `non_matching` | `ComWin_SetState` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010a748` | 504 | `ui` | `non_matching` | `ComWin_Init` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010a940` | 20 | `engine` | `non_matching` | `ComWin_GetState` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010a954` | 1352 | `ui` | `non_matching` | `ComWin_ProcessDialog` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010ae9c` | 44 | `battle` | `non_matching` | `ComWin_CheckFlag` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010aec8` | 12 | `unknown` | `non_matching` | `ComWin_GetResult` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010aed4` | 100 | `engine` | `non_matching` | `ComWin_Reset` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010af38` | 16 | `ui` | `non_matching` | `InfoWin_IsActive` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010af48` | 60 | `unknown` | `non_matching` | `InfoWin_SetState` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010af84` | 560 | `ui` | `non_matching` | `InfoWin_Init` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010b1b4` | 172 | `ui` | `non_matching` | `InfoWin_ShowMessage` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010b260` | 192 | `ui` | `non_matching` | `InfoWin_UpdateTimer` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010b320` | 32 | `ui` | `non_matching` | `InfoWin_Dismiss` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010b340` | 16 | `ui` | `non_matching` | `GuestWin_IsActive` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010b350` | 448 | `ui` | `non_matching` | `GuestWin_Init` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0010b510` | 104 | `engine` | `non_matching` | `GuestWin_HandlePrompt` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x00114374` | 6144 | `camp` | `stub` | `Camp_DemonicaArchiveLoad` | [`src/camp/camp_archive.cpp`](src/camp/camp_archive.cpp) |
| `0x0011a354` | 1632 | `ui` | `non_matching` | `ComWin_DrawUp` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0011a9b4` | 1116 | `ui` | `non_matching` | `GuestWin_DrawUp` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0011ae10` | 792 | `ui` | `non_matching` | `InfoWin_DrawUp` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0011b128` | 588 | `ui` | `non_matching` | `InfoWin_Calc` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0017fe9c` | 27308 | `camp` | `stub` | `Camp_MainProc` | [`src/camp/camp_main.cpp`](src/camp/camp_main.cpp) |
| `0x00187014` | 5176 | `ui` | `non_matching` | `StatusDown_DrawPartyAndSubViews` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0018bfec` | 12684 | `ui` | `stub` | `Result_Calc` | [`src/ui/result.cpp`](src/ui/result.cpp) |
| `0x0018f178` | 988 | `ui` | `non_matching` | `RunWin_DrawDownAndCalc` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0018f560` | 4912 | `ui` | `non_matching` | `Status_CalcTaskCallback` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00191eac` | 208 | `ui` | `non_matching` | `saveLoadUI_Init` | [`src/ui/save_load.cpp`](src/ui/save_load.cpp) |
| `0x001955bc` | 5812 | `script_vm` | `stub` | `FlowScript_EventVmExecute` | [`src/script/script_vm.cpp`](src/script/script_vm.cpp) |
| `0x0019a3ec` | 12900 | `camp` | `stub` | `Camp_DrawStereoViews` | [`src/camp/camp_main.cpp`](src/camp/camp_main.cpp) |
| `0x0019e034` | 4772 | `battle` | `stub` | `btlUI_Calc` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x001a15b0` | 932 | `ui` | `stub` | `Result_DrawUp` | [`src/ui/result.cpp`](src/ui/result.cpp) |
| `0x001a310c` | 15148 | `ui` | `non_matching` | `Status_DrawUp` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001a83c8` | 488 | `battle` | `non_matching` | `btlUI_Init` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x001accd4` | 1104 | `ui` | `non_matching` | `SearchWin_DrawUpAndCalc` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x001b0cb0` | 812 | `battle` | `non_matching` | `btlMain_Init` | [`src/battle/btl_main.cpp`](src/battle/btl_main.cpp) |
| `0x001b1a90` | 8352 | `ui` | `stub` | `Ui_DebugStatsRender` | [`src/ui/debug_hud.cpp`](src/ui/debug_hud.cpp) |
| `0x001b55f0` | 5288 | `battle` | `stub` | `btlMain_Calc` | [`src/battle/btl_main.cpp`](src/battle/btl_main.cpp) |
| `0x001b6a98` | 1824 | `battle` | `non_matching` | `btlMain_Setup` | [`src/battle/btl_main.cpp`](src/battle/btl_main.cpp) |
| `0x001b71e0` | 3224 | `battle` | `stub` | `btlUI_DrawUp` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x001b7e78` | 34684 | `script_vm` | `non_matching` | `FlowScript_DispatchNativeCommands` | [`src/script/script_exec.cpp`](src/script/script_exec.cpp) |
| `0x001c3ed4` | 18660 | `script_vm` | `non_matching` | `FlowScript_EvalStateControl` | [`src/script/script_exec.cpp`](src/script/script_exec.cpp) |
| `0x001c87d8` | 420 | `ui` | `stub` | `Result_DrawDown` | [`src/ui/result.cpp`](src/ui/result.cpp) |
| `0x001c897c` | 7048 | `ui` | `non_matching` | `saveLoadUI_DrawMain` | [`src/ui/save_load.cpp`](src/ui/save_load.cpp) |
| `0x001ca648` | 8908 | `ui` | `non_matching` | `StatusDown_CalcTaskCallback` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001cc914` | 5348 | `ui` | `non_matching` | `StatusDown_DrawTaskCallback` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001cddf8` | 516 | `ui` | `non_matching` | `Status_DrawBackUp` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001ce98c` | 5444 | `ui` | `stub` | `Ui_StatusScreenSkills` | [`src/ui/status_skills.cpp`](src/ui/status_skills.cpp) |
| `0x001d2528` | 232 | `battle` | `non_matching` | `btlHelp_Init` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x001d2610` | 308 | `battle` | `non_matching` | `btlTalk_Init` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x001d2744` | 644 | `battle` | `non_matching` | `btlUnit_Init` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x001d29c8` | 240 | `battle` | `non_matching` | `btlUnit_CheckPartyActive` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x001d374c` | 408 | `ui` | `non_matching` | `nameMain_Init` | [`src/script/script_vm.cpp`](src/script/script_vm.cpp) |
| `0x001d38fc` | 392 | `script_vm` | `non_matching` | `onesRoom_Init` | [`src/script/script_vm.cpp`](src/script/script_vm.cpp) |
| `0x001d3b10` | 364 | `shop` | `non_matching` | `shopMain_Init` | [`src/shop/shop.cpp`](src/shop/shop.cpp) |
| `0x001d3d40` | 22520 | `script_vm` | `non_matching` | `FlowScript_ExecuteOpcode` | [`src/script/script_vm.cpp`](src/script/script_vm.cpp) |
| `0x001d9538` | 908 | `shop` | `stub` | `shopMain_Proc` | [`src/shop/shop.cpp`](src/shop/shop.cpp) |
| `0x001d98c4` | 5880 | `ui` | `stub` | `Ui_TerminalSceneRender` | [`src/ui/terminal_ui.cpp`](src/ui/terminal_ui.cpp) |
| `0x001ddab4` | 68 | `ui` | `non_matching` | `StatusDown_OpenDefaultView` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001ddaf8` | 36 | `ui` | `non_matching` | `Status_GetField1E64` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001ddb1c` | 36 | `ui` | `non_matching` | `Status_IsState8` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001de238` | 5020 | `camp` | `non_matching` | `Unite_DrawAndCalc` | [`src/camp/unite.cpp`](src/camp/unite.cpp) |
| `0x001e4990` | 340 | `battle` | `stub` | `btlMain_DrawUp` | [`src/battle/btl_main.cpp`](src/battle/btl_main.cpp) |
| `0x001e4ae4` | 360 | `battle` | `stub` | `btlUI_DrawDown` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x001e5d84` | 9740 | `script_vm` | `non_matching` | `FlowScript_ProcessFlagBank` | [`src/script/script_runtime.cpp`](src/script/script_runtime.cpp) |
| `0x001ee5a4` | 548 | `ui` | `non_matching` | `StatusDown_PopulateSkillList` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001ee7c8` | 384 | `ui` | `non_matching` | `StatusDown_PopulateItemList` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001eeea0` | 5556 | `ui` | `stub` | `Ui_MikadoCastleScene` | [`src/ui/mikado_ui.cpp`](src/ui/mikado_ui.cpp) |
| `0x001f2f58` | 1704 | `camp` | `non_matching` | `Unite_Setup` | [`src/camp/unite.cpp`](src/camp/unite.cpp) |
| `0x001f60dc` | 152 | `ui` | `non_matching` | `StatusDown_SkillSortByCostAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001f6174` | 48 | `ui` | `non_matching` | `StatusDown_SkillSortByNameAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001fc644` | 4876 | `script_vm` | `non_matching` | `FlowScript_BranchCondition` | [`src/script/script_vm.cpp`](src/script/script_vm.cpp) |
| `0x001fdf4c` | 1132 | `shop` | `stub` | `shopMain_DrawUp` | [`src/shop/shop.cpp`](src/shop/shop.cpp) |
| `0x002027dc` | 372 | `ui` | `non_matching` | `RunWin_Init` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x00202950` | 1256 | `ui` | `non_matching` | `saveLoadUI_Calc` | [`src/ui/save_load.cpp`](src/ui/save_load.cpp) |
| `0x00203338` | 24 | `ui` | `non_matching` | `Status_SetActiveDemonId` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00206be8` | 80 | `ui` | `non_matching` | `StatusDown_SkillSortByIdAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00206c38` | 132 | `ui` | `non_matching` | `StatusDown_ItemSortByTypeAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00206cbc` | 124 | `ui` | `non_matching` | `StatusDown_ItemSortByIdAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00208ce8` | 16796 | `engine` | `stub` | `Map_Field3DManager` | [`src/engine/map_field.cpp`](src/engine/map_field.cpp) |
| `0x0020eee8` | 1140 | `battle` | `stub` | `btlMain_DrawDown` | [`src/battle/btl_main.cpp`](src/battle/btl_main.cpp) |
| `0x0020f35c` | 296 | `battle` | `stub` | `btlUI_DrawNumber` | [`src/battle/btl_ui.cpp`](src/battle/btl_ui.cpp) |
| `0x0021243c` | 5820 | `ui` | `stub` | `Ui_QuestCenterListRender` | [`src/ui/quest_ui.cpp`](src/ui/quest_ui.cpp) |
| `0x00215990` | 180 | `ui` | `non_matching` | `StatusDown_SetPartyPrompt` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00215a44` | 28 | `ui` | `non_matching` | `StatusDown_SetActiveSoundId` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00215a68` | 248 | `ui` | `non_matching` | `StatusDown_SetPartySlots` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0021c598` | 5420 | `battle` | `non_matching` | `Btl_StatusEffectCalc` | [`src/battle/battle_ailment.cpp`](src/battle/battle_ailment.cpp) |
| `0x0021ee14` | 1416 | `shop` | `stub` | `shopMain_DrawDown` | [`src/shop/shop.cpp`](src/shop/shop.cpp) |
| `0x00223a90` | 248 | `ui` | `non_matching` | `StatusBustUp_Init` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00223b88` | 40 | `ui` | `non_matching` | `StatusDown_IsState20` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0022e694` | 32 | `ui` | `non_matching` | `Status_SetFlag1E65` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0022e6b4` | 24 | `ui` | `non_matching` | `Status_IsActive` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00258e38` | 480 | `ui` | `non_matching` | `StatusCamera_Init` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0025d3fc` | 7328 | `ui` | `stub` | `Ui_BattleCommandMenu` | [`src/ui/battle_hud.cpp`](src/ui/battle_hud.cpp) |
| `0x0025f8f0` | 11004 | `ui` | `stub` | `Ui_MiniMapRender` | [`src/ui/minimap.cpp`](src/ui/minimap.cpp) |
| `0x0026385c` | 64 | `ui` | `non_matching` | `PlaceWin_SetPos` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0026389c` | 64 | `ui` | `non_matching` | `PlaceWin_SetScale` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x002638dc` | 32 | `ui` | `non_matching` | `PlaceWin_Dismiss` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x002638fc` | 20 | `ui` | `non_matching` | `PlaceWin_SetVisible` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x00263910` | 60 | `ui` | `non_matching` | `PlaceWin_CheckState` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x0026394c` | 44 | `ui` | `non_matching` | `PlaceWin_IsActive` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x00263978` | 124 | `ui` | `non_matching` | `PlaceWin_ShowMessage` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x002639f4` | 448 | `ui` | `non_matching` | `PlaceWin_Init` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x00263bb4` | 660 | `ui` | `non_matching` | `PlaceWin_Calc` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x00269cc8` | 352 | `unite` | `non_matching` | `bibleMain_Init` | [`src/camp/bible.cpp`](src/camp/bible.cpp) |
| `0x0026abc0` | 32 | `ui` | `non_matching` | `Status_SetMode1E71` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0026abe0` | 84 | `ui` | `non_matching` | `StatusDown_SetSubIdsA` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026b01c` | 176 | `ui` | `non_matching` | `StatusDown_PopFirstSubIdA` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026b0d0` | 1636 | `ui` | `non_matching` | `StatusDown_SetupTouchRegions` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026b810` | 32 | `ui` | `non_matching` | `Status_SetMode1EB9` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0026b874` | 304 | `ui` | `non_matching` | `SaveLoadProcess_Init` | [`src/ui/save_load.cpp`](src/ui/save_load.cpp) |
| `0x0026c8a8` | 24 | `ui` | `non_matching` | `Status_GetFlag1E63` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0026d8c0` | 28 | `ui` | `non_matching` | `StatusDown_SetVisibility` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026d8dc` | 52 | `ui` | `non_matching` | `Status_ResetAffinityView` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0027154c` | 8316 | `script_vm` | `non_matching` | `FlowScript_OpcodeEvaluator` | [`src/script/script_vm.cpp`](src/script/script_vm.cpp) |
| `0x00277f9c` | 12192 | `script_vm` | `stub` | `FlowScript_InitRuntimeMemory` | [`src/script/script_runtime.cpp`](src/script/script_runtime.cpp) |
| `0x00288408` | 28 | `ui` | `non_matching` | `Status_GetSubMenuState` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00288718` | 92 | `ui` | `non_matching` | `StatusDown_CanOpenSubScreen` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00289158` | 112 | `ui` | `non_matching` | `Status_Destroy` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0028a688` | 1284 | `camp` | `non_matching` | `Camp_Init` | [`src/camp/camp.cpp`](src/camp/camp.cpp) |
| `0x0028ab8c` | 3796 | `camp` | `non_matching` | `Camp_Calc` | [`src/camp/camp.cpp`](src/camp/camp.cpp) |
| `0x0028ba60` | 1608 | `camp` | `non_matching` | `PartyPanel_DrawAndCalc` | [`src/camp/camp.cpp`](src/camp/camp.cpp) |
| `0x0028c2a8` | 1448 | `ui` | `non_matching` | `Status_Init` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0028cd5c` | 28 | `ui` | `non_matching` | `StatusDown_GetField2384` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0028cd78` | 36 | `ui` | `non_matching` | `StatusDown_IsInactiveOrState0` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0028d974` | 736 | `camp` | `non_matching` | `ButtonHelp_Init` | [`src/camp/unite.cpp`](src/camp/unite.cpp) |
| `0x00292f44` | 304 | `ui` | `non_matching` | `StatusDown_SetDisplayMode` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00293d2c` | 36 | `ui` | `non_matching` | `StatusDown_IsNotTransitioning` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00293d50` | 20 | `ui` | `non_matching` | `StatusDown_GetActiveMode` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00293d64` | 204 | `ui` | `non_matching` | `Status_HandleLRPrompt` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00293e30` | 28 | `ui` | `non_matching` | `StatusDown_GetStatusMode` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00293e4c` | 520 | `ui` | `non_matching` | `Status_UpdateAffinityTable` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00295010` | 172 | `ui` | `non_matching` | `Status_GetCalculatedScale` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x002956ac` | 20 | `ui` | `non_matching` | `StatusDown_GetField53C` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029a520` | 1696 | `ui` | `non_matching` | `StatusDown_DrawPartySlotRow` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029adf0` | 320 | `ui` | `non_matching` | `StatusDown_DrawLRPrompts` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029af30` | 28 | `ui` | `non_matching` | `Status_GetMainMenuId` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0029af4c` | 20 | `ui` | `non_matching` | `Status_GetSelectedActorPtr` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0029b0e0` | 28 | `ui` | `non_matching` | `Status_GetSubState` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0029b3cc` | 1676 | `camp` | `non_matching` | `Unite_Init` | [`src/camp/unite.cpp`](src/camp/unite.cpp) |
| `0x0029bc38` | 368 | `ui` | `non_matching` | `Result_Init` | [`src/ui/result.cpp`](src/ui/result.cpp) |
| `0x0029bfec` | 152 | `ui` | `non_matching` | `StatusDown_Close` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029c6c4` | 24 | `ui` | `non_matching` | `StatusDown_SetFlag412` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029c70c` | 32 | `ui` | `non_matching` | `StatusDown_IsNotState1` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029c72c` | 32 | `ui` | `non_matching` | `StatusDown_IsNotState2` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029e63c` | 644 | `camp` | `non_matching` | `SortMenu_Init` | [`src/camp/unite.cpp`](src/camp/unite.cpp) |
| `0x002ac2f4` | 92 | `ui` | `non_matching` | `Tbb_GetSubTable` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e4c` | 56 | `ui` | `non_matching` | `Tbb_GetRowCount` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e84` | 24 | `ui` | `non_matching` | `Tbb_GetDefaultTable18Payload` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e9c` | 40 | `ui` | `non_matching` | `Tbb_GetPayloadData` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0ec4` | 28 | `ui` | `non_matching` | `Tbb_GetGlobalSubTable` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002cecd8` | 52 | `ui` | `non_matching` | `SearchWin_IsActive` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x002ced0c` | 28 | `ui` | `non_matching` | `SearchWin_Dismiss` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x002ced28` | 348 | `ui` | `non_matching` | `SearchWin_Init` | [`src/ui/window.cpp`](src/ui/window.cpp) |
| `0x002cf4e0` | 352 | `ui` | `non_matching` | `StatusDown_UpdateHelpMessage` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002d931c` | 764 | `ui` | `non_matching` | `StatusDown_Init` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002d9618` | 36 | `ui` | `non_matching` | `StatusDown_EnterState3_Alt` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002d966c` | 5336 | `camp` | `stub` | `Camp_ItemInventorySort` | [`src/camp/camp_inventory.cpp`](src/camp/camp_inventory.cpp) |
| `0x002dc96c` | 152 | `ui` | `non_matching` | `StatusDown_SkillSortByCostDesc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e06bc` | 1080 | `battle` | `stub` | `btlTargetSelect_Calc` | [`src/battle/btl_target_select.cpp`](src/battle/btl_target_select.cpp) |
| `0x002e2454` | 764 | `camp` | `non_matching` | `GauntletAppMenu_Init` | [`src/camp/camp.cpp`](src/camp/camp.cpp) |
| `0x002e2f44` | 408 | `ui` | `non_matching` | `StatusDown_UpdatePartySlotsAndDiff` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e315c` | 344 | `camp` | `non_matching` | `UniteEffect_Init` | [`src/camp/unite.cpp`](src/camp/unite.cpp) |
| `0x002e4534` | 80 | `ui` | `non_matching` | `StatusDown_SkillSortByIdDesc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e4584` | 132 | `ui` | `non_matching` | `StatusDown_ItemSortByTypeDesc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e4608` | 124 | `ui` | `non_matching` | `StatusDown_ItemSortByIdDesc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e8294` | 604 | `battle` | `non_matching` | `btlTargetSelect_Init` | [`src/battle/btl_target_select.cpp`](src/battle/btl_target_select.cpp) |
| `0x002ef9ac` | 420 | `ui` | `non_matching` | `SaveLoadProcess_Step` | [`src/ui/save_load.cpp`](src/ui/save_load.cpp) |
| `0x002efb50` | 456 | `ui` | `non_matching` | `SaveLoadProcess_Write` | [`src/ui/save_load.cpp`](src/ui/save_load.cpp) |
| `0x002efde0` | 44 | `ui` | `non_matching` | `StatusDown_GetPartyMaxIndex` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efe0c` | 32 | `ui` | `non_matching` | `StatusDown_IsNotState4` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efe2c` | 28 | `ui` | `non_matching` | `StatusDown_GetField2388` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efe48` | 68 | `ui` | `non_matching` | `StatusDown_SetSubIdsB` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efe8c` | 24 | `ui` | `non_matching` | `StatusDown_SetFlag411` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efea4` | 36 | `ui` | `non_matching` | `StatusDown_EnterState4` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f4aa4` | 76 | `battle` | `stub` | `btlTargetSelect_DrawUp` | [`src/battle/btl_target_select.cpp`](src/battle/btl_target_select.cpp) |
| `0x002f6524` | 44 | `ui` | `non_matching` | `StatusDown_IsState7` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f6550` | 132 | `ui` | `non_matching` | `StatusDown_Destroy` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f65d4` | 76 | `ui` | `non_matching` | `StatusDown_IsCursorAtLastPartySlot` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f6620` | 200 | `ui` | `non_matching` | `StatusDown_SelectLastPartySlotAndEnterState11` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f66e8` | 36 | `ui` | `non_matching` | `StatusDown_EnterState3` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00307978` | 4832 | `script_vm` | `stub` | `FlowScript_MessageWindowHook` | [`src/script/script_vm.cpp`](src/script/script_vm.cpp) |
| `0x0030aa98` | 40 | `ui` | `non_matching` | `StatusDown_EnterState6_Simple` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030aac0` | 32 | `ui` | `non_matching` | `StatusDown_IsState15` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030aae0` | 32 | `ui` | `non_matching` | `StatusDown_IsState10` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030ab00` | 52 | `ui` | `non_matching` | `StatusDown_EnterState14` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030ab34` | 60 | `ui` | `non_matching` | `StatusDown_EnterState6` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00311494` | 356 | `ui` | `non_matching` | `StatusDown_OpenCategorySelect` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00317f80` | 36 | `ui` | `non_matching` | `StatusDown_RequestClose` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00322d70` | 412 | `ui` | `non_matching` | `SaveLoadProcess_Read` | [`src/ui/save_load.cpp`](src/ui/save_load.cpp) |
| `0x00322f0c` | 304 | `ui` | `non_matching` | `SaveLoadProcess_Close` | [`src/ui/save_load.cpp`](src/ui/save_load.cpp) |
| `0x0032303c` | 40 | `ui` | `non_matching` | `StatusDown_GetSelectedPartyIndex` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00325478` | 5072 | `ui` | `non_matching` | `Ui_DemonicaAppStore` | [`src/camp/app_store.cpp`](src/camp/app_store.cpp) |
| `0x0032be34` | 1672 | `ui` | `non_matching` | `StatusDown_DrawSkillList` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0032c4bc` | 372 | `ui` | `non_matching` | `StatusDown_SortItemList` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0032cb08` | 12620 | `camp` | `stub` | `Camp_SubModeProcess` | [`src/camp/camp_party.cpp`](src/camp/camp_party.cpp) |
| `0x00332100` | 5968 | `camp` | `stub` | `Camp_WhisperSkillTransfer` | [`src/camp/whisper_event.cpp`](src/camp/whisper_event.cpp) |
| `0x00345194` | 7068 | `ui` | `non_matching` | `Ui_MemoryArenaAllocate` | [`src/ui/ui_memory.cpp`](src/ui/ui_memory.cpp) |
| `0x00386184` | 5964 | `engine` | `stub` | `Engine_TextureStreamer` | [`src/engine/map_field.cpp`](src/engine/map_field.cpp) |
| `0x003a9200` | 948 | `unite` | `non_matching` | `bibleAnalyze_Init` | [`src/camp/bible.cpp`](src/camp/bible.cpp) |
| `0x003b35a8` | 5656 | `ui` | `non_matching` | `Ui_ShopInventoryCatalog` | [`src/shop/shop_catalog.cpp`](src/shop/shop_catalog.cpp) |
| `0x003b4bc0` | 5520 | `ui` | `stub` | `Ui_DemonCompendiumSearch` | [`src/camp/compendium_search.cpp`](src/camp/compendium_search.cpp) |
| `0x003c6714` | 4724 | `battle` | `non_matching` | `Btl_DemonNegotiationCalc` | [`src/battle/battle_scout.cpp`](src/battle/battle_scout.cpp) |
| `0x003cccd8` | 9192 | `battle` | `stub` | `Btl_ActionCalc` | [`src/battle/btl_main.cpp`](src/battle/btl_main.cpp) |
| `0x003d3dd4` | 6896 | `battle` | `stub` | `Btl_CameraCalc` | [`src/battle/btl_main.cpp`](src/battle/btl_main.cpp) |
| `0x003ec954` | 6616 | `ui` | `stub` | `Ui_BattleActionEffectOverlay` | [`src/ui/battle_hud.cpp`](src/ui/battle_hud.cpp) |
| `0x003efa10` | 12708 | `ui` | `stub` | `Ui_NkmBaseTableLoad` | [`src/ui/battle_hud.cpp`](src/ui/battle_hud.cpp) |
| `0x003f34f8` | 7984 | `ui` | `stub` | `Ui_BattleMessageWindow` | [`src/ui/battle_hud.cpp`](src/ui/battle_hud.cpp) |
