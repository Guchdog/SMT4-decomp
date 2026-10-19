# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation Progress

## Overall `.text` Progress

| Metric | Decompiled | Total | Remaining | Percentage |
|--------|-----------:|------:|----------:|-----------:|
| **Code Size (Bytes)** | 5,120 B | 3,139,108 B | 3,133,988 B | **0.1631%** |
| **Functions** | 51 | 10,349 | 10,298 | **0.4928%** |

## Subsystem Breakdown

| Subsystem | Decompiled Funcs | Total Funcs | Decompiled Bytes | Total Bytes | Subsystem % |
|-----------|-----------------:|------------:|-----------------:|------------:|------------:|
| `engine` | 0 | 2,368 | 0 B | 735,468 B | 0.000% |
| `ui` | 49 | 1,214 | 5,048 B | 658,880 B | 0.766% |
| `unknown` | 0 | 3,826 | 0 B | 654,596 B | 0.000% |
| `script_vm` | 0 | 1,204 | 0 B | 459,444 B | 0.000% |
| `camp` | 0 | 940 | 0 B | 346,172 B | 0.000% |
| `battle` | 0 | 566 | 0 B | 220,356 B | 0.000% |
| `shop` | 0 | 110 | 0 B | 36,576 B | 0.000% |
| `crt` | 2 | 26 | 72 B | 9,484 B | 0.759% |
| `unite` | 0 | 31 | 0 B | 9,280 B | 0.000% |
| `nn_sdk` | 0 | 64 | 0 B | 8,852 B | 0.000% |

## Decompiled Functions Ledger

| Address | Size (Bytes) | Category | Status | Symbol Name | Source File |
|---------|-------------:|----------|--------|-------------|-------------|
| `0x00100000` | 36 | `crt` | `non_matching` | `__start` | [`src/crt/start.cpp`](src/crt/start.cpp) |
| `0x00100024` | 36 | `crt` | `non_matching` | `__init_bss` | [`src/crt/start.cpp`](src/crt/start.cpp) |
| `0x0010299c` | 260 | `ui` | `non_matching` | `IfTouch_Init` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x001ddab4` | 68 | `ui` | `non_matching` | `StatusDown_OpenDefaultView` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00215990` | 180 | `ui` | `non_matching` | `StatusDown_SetPartyPrompt` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00215a44` | 28 | `ui` | `non_matching` | `StatusDown_SetActiveSoundId` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00215a68` | 248 | `ui` | `non_matching` | `StatusDown_SetPartySlots` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00223b88` | 40 | `ui` | `non_matching` | `StatusDown_IsState20` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026abe0` | 84 | `ui` | `non_matching` | `StatusDown_SetSubIdsA` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026b01c` | 176 | `ui` | `non_matching` | `StatusDown_PopFirstSubIdA` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0026d8c0` | 28 | `ui` | `non_matching` | `StatusDown_SetVisibility` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00288718` | 92 | `ui` | `non_matching` | `StatusDown_CanOpenSubScreen` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0028cd5c` | 28 | `ui` | `non_matching` | `StatusDown_GetField2384` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0028cd78` | 36 | `ui` | `non_matching` | `StatusDown_IsInactiveOrState0` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00292f44` | 304 | `ui` | `non_matching` | `StatusDown_SetDisplayMode` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00293d2c` | 36 | `ui` | `non_matching` | `StatusDown_IsNotTransitioning` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00293d50` | 20 | `ui` | `non_matching` | `StatusDown_GetActiveMode` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x00293e30` | 28 | `ui` | `non_matching` | `StatusDown_GetStatusMode` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x002956ac` | 20 | `ui` | `non_matching` | `StatusDown_GetField53C` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0029adf0` | 320 | `ui` | `non_matching` | `StatusDown_DrawLRPrompts` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
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
| `0x002e2f44` | 408 | `ui` | `non_matching` | `StatusDown_UpdatePartySlotsAndDiff` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
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
| `0x00317f80` | 36 | `ui` | `non_matching` | `StatusDown_RequestClose` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
| `0x0032303c` | 40 | `ui` | `non_matching` | `StatusDown_GetSelectedPartyIndex` | [`src/ui/status_down.cpp`](src/ui/status_down.cpp) |
