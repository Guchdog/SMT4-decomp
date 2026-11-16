# func_003efacc (0x003efacc)

## Summary
- **Address:** 0x003efacc
- **Size:** 64 bytes
- **Domain:** UI / Battle HUD Channel State Reset
- **Status:** Semantically verified (non_matching in ledger)
- **Source File:** src/ui/battle_hud.cpp
- **Differential Suite:** tools/battle_hud_experiment.py

## Role and Behavior
- **Role:** Clears and resets battle HUD channel states and mask registers.
- **Details:**
  - Writes `(-1, -1)` (64-bit `0xFFFFFFFFFFFFFFFF`) to `0x0044E588`.
  - Writes `(0, 0)` (64-bit 0) to `0x0044E590`.
  - Stores mask constant `0xE7E3FFFF` to `0x004C7024`.
- **Differential Coverage:** Verified in Unicorn emulator against original ARM binary with exact memory image check across all target addresses.
