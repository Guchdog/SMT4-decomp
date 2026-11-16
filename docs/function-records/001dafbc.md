# tmnlMain_func_001dafbc (0x001dafbc)

## Summary
- **Address:** 0x001dafbc
- **Size:** 668 bytes
- **Domain:** Title Flow / Terminal Main Setup & Task Orchestrator
- **Status:** Semantically verified (non_matching in ledger)
- **Source File:** src/camp/title_flow.cpp
- **Differential Suite:** tools/title_flow_experiment.py

## Role and Behavior
- **Role:** Allocates and initializes the terminal main workspace (`g_TerminalMainWork` at `0x00432CE0`), configures UI input flags, sets script event flags, and spawns calculate and draw tasks.
- **Details:**
  - Allocates `0x5E8` bytes via `AsdMem_Alloc(0x100, 0x100, 0, 0x5E8, 1)`.
  - Stores pointer to `g_TerminalMainWork`.
  - Configures input flags:
    - If `UiInput_TestFlag(10) == 0`: sets `UiInput_SetFlag(10, 1)`.
    - If `UiInput_TestFlag(12) == 0`: sets `UiInput_SetFlag(12, 1)`.
    - If `UiInput_TestFlag(11) == 0` and event bit 0x277 is set (`Flag_CheckEventBit(0x277)`): sets `UiInput_SetFlag(11, 1)`.
  - Sets script VM flag via `ScriptVm_SetFlag(0x465, 0, 1)`.
  - Clears initial workspace fields: `flag_05 = 1`, `field_10 = 0`, `field_14 = 0`, `flag_09 = 0`, `field_0c = 0`, `field_20[0..9] = 0`, `field_550 = 0`, `flag_554 = 0`, `field_558 = 0`, `field_568 = 0`, `field_564 = 0`, `field_574 = 0`, `field_570 = 0`, `field_580 = 0`, `field_57c = 0`, `field_58c = 0`, `field_588 = 0`.
  - Clears entry lock via `Ui_SetEntryLock(0)` and clears `flag_04 = 0`.
  - Boot argument handling:
    - If `arg != nullptr`: sets `flag_09 = *arg & 0xFF`, `flag_05 = 0`, calls `UiInput_SetFlag(*arg & 0xFF, 1)`, and increments camp progress value `Camp_AddProgressValue(0x1C, 1)`.
    - If `arg == nullptr`: sets `field_10 = 1`, calls `UiAnimSlot_SetState(0, 0xFF)`.
  - Spawns calculate task `"TMNL C"` (priority 2, primary `0x0021F240`, secondary `0x001D98C4`) via `AsdTask_CreateCalc`. Stores handle to `work->calc_task`.
  - Spawns draw tasks attached to `calc_task`:
    - `"TMNL UD"` (priority 0x75, callback `0x001FE198`).
    - `"TMNL UD"` (priority 0xD3, callback `0x002E08D4`).
    - `"TMNL DD"` (priority 0xE7, callback `0x0021F258`).
- **Differential Coverage:** Verified in Unicorn across null boot arguments (with anim slot reset) and non-null boot arguments (with input flag dispatch and progress increment) against original ARM binary with 100% equivalence.
