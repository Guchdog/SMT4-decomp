# H5 Combat Architecture Reconnaissance Record

- **Milestone:** H5 (Minimal Combat / Combate mínimo)
- **Status:** Complete & Reviewed
- **Target Subsystems:** Party Management, Target Selection, Modal Dialogs, Combat Channel Context, State Lifecycle

## 1. Subsystem Boundaries and Mappings

SMT4 combat execution is organized into distinct cooperating subsystems:

1. **Party Status & Roster Activity (`0x001D29C8` - `btlUnit_CheckPartyActive`):**
   Iterates through up to 8 active combat slots (`work->party_slots + 0x34`), 8 reserve slots (`work->reserve_slots + 0x34`), and 8 guest party slots (`sub_party + 0x3C`). Calls `Unit_Lookup_002ae3f0(unit_id)`. Checks status flag `*(unit + 0x23) == 3` (active/alive). Returns 1 if any combatant is active, 0 otherwise.

2. **Demon Unit Classifier (`0x002AE464` - `Btl_IsDemonUnit`):**
   Compares unit ID against threshold `0x190` (400 decimal). IDs > 400 represent demons (`movhi r0, #1`); IDs <= 400 represent human protagonists and special actors (`movls r0, #0`).

3. **Target Selection Screen Rendering (`0x002F4AA4` - `btlTargetSelect_DrawUp`):**
   Reads active mode from `TargetSelect_GetWork_002c0ac8() + 0x08`. Mode 1 invokes `TargetSelect_DrawMode1_00342b54(work->obj0)`; mode 2 invokes `TargetSelect_DrawMode2_0034946c(work->obj1)`.

4. **Target Selection Animation & Reticle Interpolation (`0x002E06BC` - `btlTargetSelect_Calc`):**
   Updates animation via `0x002BF9F0`. Updates UI visibility flags `obj0+0x120` and `obj1+0x54`. In Mode 2, applies rotational float progression:
   `f58 += 1.0f; if (f58 >= 30.0f) f58 -= 30.0f;`
   `f5c += 12.0f; if (f5c > 360.0f) f5c -= 360.0f;`

5. **Combat Help Modal Workspace (`0x001D2528` - `btlHelp_Init`):**
   Verifies existing task via `Task_Destroy_002bf41c`. Allocates task "btlHelp Calc" (tag 2, priority `0x0020ee34`, callback `0x001B5398`). Allocates 12-byte buffer in `g_BtlHelpManager` (`0x00435D78`) and zeroes it.

6. **Combat Negotiation Talk Workspace (`0x001D2610` - `btlTalk_Init`):**
   Cleans up existing talk task. Allocates 0xCC-byte talk buffer in `g_pBtlTalkBuffer` (`0x00439B58`). Allocates task "btlTalk Calc" (tag 2, priority `0x0020f35c`, callback `0x001B71B8`). Sets parent, context, speaker ID, and initializes talk engine via `0x002C4450` and `0x00267F68`.

7. **Combat Sub-object State Lifecycle (`0x002B8A80` - `Btl_ReleaseState`):**
   Safely checks sub-object state via `0x002B2530`. If idle and flag at `+0x0C` is non-zero, releases heap memory via `Free_002c4360` and clears `g_CombatSubWork_00447e28`.

8. **Combat Channel Parameter Dispatch (`0x0011311C` - `Btl_SetChannelParameter`):**
   Sets audio/display channel parameter in `g_CombatChannelContext_004c6290`: mode 0x400 updates channel 0 (`+0x15C`), mode 0x401 updates channel 1 (`+0x160`), mode 0x402 updates both.
