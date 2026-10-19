# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation Progress

## Overall `.text` Progress

| Metric | Decompiled | Total | Remaining | Percentage |
|--------|-----------:|------:|----------:|-----------:|
| **Code Size (Bytes)** | 55,668 B | 3,139,108 B | 3,083,440 B | **1.7734%** |
| **Functions** | 91 | 10,349 | 10,258 | **0.8793%** |

## Subsystem Breakdown

| Subsystem | Decompiled Funcs | Total Funcs | Decompiled Bytes | Total Bytes | Subsystem % |
|-----------|-----------------:|------------:|-----------------:|------------:|------------:|
| `engine` | 0 | 2,368 | 0 B | 735,468 B | 0.000% |
| `ui` | 89 | 1,242 | 55,596 B | 675,556 B | 8.230% |
| `unknown` | 0 | 3,823 | 0 B | 654,480 B | 0.000% |
| `script_vm` | 0 | 1,203 | 0 B | 459,392 B | 0.000% |
| `camp` | 0 | 919 | 0 B | 331,168 B | 0.000% |
| `battle` | 0 | 566 | 0 B | 220,356 B | 0.000% |
| `shop` | 0 | 108 | 0 B | 36,520 B | 0.000% |
| `crt` | 2 | 26 | 72 B | 9,484 B | 0.759% |
| `nn_sdk` | 0 | 64 | 0 B | 8,852 B | 0.000% |
| `unite` | 0 | 30 | 0 B | 7,832 B | 0.000% |

## Decompiled Functions Ledger

| Address | Size (Bytes) | Category | Status | Symbol Name | Source File |
|---------|-------------:|----------|--------|-------------|-------------|
| `0x00100000` | 36 | `crt` | `non_matching` | `__start` | [`src/crt/start.cpp`](src/crt/start.cpp) |
| `0x00100024` | 36 | `crt` | `non_matching` | `__init_bss` | [`src/crt/start.cpp`](src/crt/start.cpp) |
| `0x0010299c` | 260 | `ui` | `non_matching` | `IfTouch_Init` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x00187014` | 5176 | `ui` | `non_matching` | `StatusDown_DrawPartyAndSubViews` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0018f560` | 4912 | `ui` | `non_matching` | `Status_CalcTaskCallback` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001a310c` | 15148 | `ui` | `non_matching` | `Status_DrawUp` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001ca648` | 8908 | `ui` | `non_matching` | `StatusDown_CalcTaskCallback` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001cc914` | 5348 | `ui` | `non_matching` | `StatusDown_DrawTaskCallback` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001cddf8` | 516 | `ui` | `non_matching` | `Status_DrawBackUp` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001ddab4` | 68 | `ui` | `non_matching` | `StatusDown_OpenDefaultView` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001ddaf8` | 36 | `ui` | `non_matching` | `Status_GetField1E64` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001ddb1c` | 36 | `ui` | `non_matching` | `Status_IsState8` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x001ee5a4` | 548 | `ui` | `non_matching` | `StatusDown_PopulateSkillList` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001ee7c8` | 384 | `ui` | `non_matching` | `StatusDown_PopulateItemList` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001f60dc` | 152 | `ui` | `non_matching` | `StatusDown_SkillSortByCostAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x001f6174` | 48 | `ui` | `non_matching` | `StatusDown_SkillSortByNameAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00203338` | 24 | `ui` | `non_matching` | `Status_SetActiveDemonId` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00206be8` | 80 | `ui` | `non_matching` | `StatusDown_SkillSortByIdAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00206c38` | 132 | `ui` | `non_matching` | `StatusDown_ItemSortByTypeAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00206cbc` | 124 | `ui` | `non_matching` | `StatusDown_ItemSortByIdAsc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00215990` | 180 | `ui` | `non_matching` | `StatusDown_SetPartyPrompt` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00215a44` | 28 | `ui` | `non_matching` | `StatusDown_SetActiveSoundId` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00215a68` | 248 | `ui` | `non_matching` | `StatusDown_SetPartySlots` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00223b88` | 40 | `ui` | `non_matching` | `StatusDown_IsState20` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0022e694` | 32 | `ui` | `non_matching` | `Status_SetFlag1E65` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0022e6b4` | 24 | `ui` | `non_matching` | `Status_IsActive` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0026abc0` | 32 | `ui` | `non_matching` | `Status_SetMode1E71` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0026abe0` | 84 | `ui` | `non_matching` | `StatusDown_SetSubIdsA` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026b01c` | 176 | `ui` | `non_matching` | `StatusDown_PopFirstSubIdA` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026b0d0` | 1636 | `ui` | `non_matching` | `StatusDown_SetupTouchRegions` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026b810` | 32 | `ui` | `non_matching` | `Status_SetMode1EB9` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0026c8a8` | 24 | `ui` | `non_matching` | `Status_GetFlag1E63` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0026d8c0` | 28 | `ui` | `non_matching` | `StatusDown_SetVisibility` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026d8dc` | 52 | `ui` | `non_matching` | `Status_ResetAffinityView` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00288408` | 28 | `ui` | `non_matching` | `Status_GetSubMenuState` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x00288718` | 92 | `ui` | `non_matching` | `StatusDown_CanOpenSubScreen` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00289158` | 112 | `ui` | `non_matching` | `Status_Destroy` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0028c2a8` | 1448 | `ui` | `non_matching` | `Status_Init` | [`src/ui/status.cpp`](src/ui/status.cpp) |
| `0x0028cd5c` | 28 | `ui` | `non_matching` | `StatusDown_GetField2384` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0028cd78` | 36 | `ui` | `non_matching` | `StatusDown_IsInactiveOrState0` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
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
| `0x0029bfec` | 152 | `ui` | `non_matching` | `StatusDown_Close` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029c6c4` | 24 | `ui` | `non_matching` | `StatusDown_SetFlag412` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029c70c` | 32 | `ui` | `non_matching` | `StatusDown_IsNotState1` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029c72c` | 32 | `ui` | `non_matching` | `StatusDown_IsNotState2` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002ac2f4` | 92 | `ui` | `non_matching` | `Tbb_GetSubTable` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e4c` | 56 | `ui` | `non_matching` | `Tbb_GetRowCount` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e84` | 24 | `ui` | `non_matching` | `Tbb_GetDefaultTable18Payload` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e9c` | 40 | `ui` | `non_matching` | `Tbb_GetPayloadData` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0ec4` | 28 | `ui` | `non_matching` | `Tbb_GetGlobalSubTable` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002cf4e0` | 352 | `ui` | `non_matching` | `StatusDown_UpdateHelpMessage` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002d931c` | 764 | `ui` | `non_matching` | `StatusDown_Init` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002d9618` | 36 | `ui` | `non_matching` | `StatusDown_EnterState3_Alt` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002dc96c` | 152 | `ui` | `non_matching` | `StatusDown_SkillSortByCostDesc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e2f44` | 408 | `ui` | `non_matching` | `StatusDown_UpdatePartySlotsAndDiff` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e4534` | 80 | `ui` | `non_matching` | `StatusDown_SkillSortByIdDesc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e4584` | 132 | `ui` | `non_matching` | `StatusDown_ItemSortByTypeDesc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002e4608` | 124 | `ui` | `non_matching` | `StatusDown_ItemSortByIdDesc` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efde0` | 44 | `ui` | `non_matching` | `StatusDown_GetPartyMaxIndex` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efe0c` | 32 | `ui` | `non_matching` | `StatusDown_IsNotState4` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efe2c` | 28 | `ui` | `non_matching` | `StatusDown_GetField2388` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efe48` | 68 | `ui` | `non_matching` | `StatusDown_SetSubIdsB` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efe8c` | 24 | `ui` | `non_matching` | `StatusDown_SetFlag411` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002efea4` | 36 | `ui` | `non_matching` | `StatusDown_EnterState4` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f6524` | 44 | `ui` | `non_matching` | `StatusDown_IsState7` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f6550` | 132 | `ui` | `non_matching` | `StatusDown_Destroy` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f65d4` | 76 | `ui` | `non_matching` | `StatusDown_IsCursorAtLastPartySlot` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f6620` | 200 | `ui` | `non_matching` | `StatusDown_SelectLastPartySlotAndEnterState11` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002f66e8` | 36 | `ui` | `non_matching` | `StatusDown_EnterState3` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030aa98` | 40 | `ui` | `non_matching` | `StatusDown_EnterState6_Simple` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030aac0` | 32 | `ui` | `non_matching` | `StatusDown_IsState15` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030aae0` | 32 | `ui` | `non_matching` | `StatusDown_IsState10` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030ab00` | 52 | `ui` | `non_matching` | `StatusDown_EnterState14` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0030ab34` | 60 | `ui` | `non_matching` | `StatusDown_EnterState6` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00311494` | 356 | `ui` | `non_matching` | `StatusDown_OpenCategorySelect` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00317f80` | 36 | `ui` | `non_matching` | `StatusDown_RequestClose` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0032303c` | 40 | `ui` | `non_matching` | `StatusDown_GetSelectedPartyIndex` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0032be34` | 1672 | `ui` | `non_matching` | `StatusDown_DrawSkillList` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0032c4bc` | 372 | `ui` | `non_matching` | `StatusDown_SortItemList` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
