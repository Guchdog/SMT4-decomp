# 0x002B8B78: six-slot transition contract

## Recommendation and H2 relevance

A production C++ reconstruction is supportable as a bounded non-leaf slice only after validating its original dependencies, manager/profile memory domains, machine-visible return and caller composition. Despite a legacy `Sound_PlaySE` alias, the pinned body updates a manager and six slots and invokes several transition services; the name alone does not establish a simple sound-play contract. Preserve the full 32-bit request and ordered effects.

There are two distinct static H2 paths. `titleConfig_func_002f4ca0` calls this function directly at 0x002F4DF0 with r0=0x99. Separately, original callback 0x00221168 calls 0x00286928 at 0x002211EC with r3=6 and fifth/sixth stack words 1/0. If its r2 (returned by 0x00289640) is zero, selected object state+8 is zero, and the 0x002C1F28/0x002B89A0 early-return condition does not apply, 0x00286928 continues setup and can call 0x002B8B78(0xDC) at 0x00286B80 **only** when object byte +9 is 7, 8 or 9 and 0x0028DF70(0) returns 5. If r2 is nonzero this callsite is not in that branch. Thus a direct BL exists inside the helper reachable conditionally from the callback in the static control-flow graph; no runtime capture establishes that the callback actually takes it. Caller H2 inputs, manager state and row are not proven naturally reachable.

## ARM entry and ordered control flow

The 340-byte slot 0x002B8B78..0x002B8CCB includes instructions through 0x002B8CC0 and two literals. Entry uses r0 as a full 32-bit requested profile/ID; r1-r3 and caller stack arguments are not consumed before overwrite. The function saves r4-r8/r9(sb)/lr (28 bytes), allocates 12 local bytes (40 total), restores them and returns through PC. It uses no VFP instructions directly. Callee-saved registers/SP are preserved assuming callees conform; scratch GPRs/CPSR and transitive helper effects are not preserved. This is not a function with a proven normalized boolean return: early r0 values and final helper returns vary; many source callers declare `void`, but machine-visible r0 should be compared in validation.

Literal 0x002B8CC4 is **0x0043DA28**, the address of a manager structure, not an automatically dereferenced global pointer. Read manager+4 to obtain object pointer P, then byte P+0x4C9 and compare its zero-extended value against the entire request. If equal, return immediately with that byte in r0. No null test precedes P+0x4C9.

If unequal, read manager+0x10 as a signed word. If negative, start index 0 and scan bytes P+0x4B8+i for i=0..5. At the first nonzero byte store the full request to manager+0x10 and return, with r0 equal to the found index. If none are nonzero, or manager+0x10 was initially nonnegative, store 0xFFFFFFFF to manager+0x10 and continue. The signed comparison and full-word store matter; scan is not performed at all for initially nonnegative manager+0x10.

Call 0x002B85BC(request), ignoring its return. Reread byte at the **original P**+0x4C9, call 0x002AEA28(current_byte) and save old profile pointer; then call 0x002AEA28(request) and save new profile pointer. Both calls occur even if the first returns null. If either profile pointer is null, return with r0 as the second lookup returned; the prior manager write and effects of 0x002B85BC already occurred. 0x002AEA28 uses unsigned comparison against a resource count and computes table base + 16*index; valid object/table pointers and range must be independently established.

On both profile pointers nonzero, copy P+0x4C9 to P+0x4CA and store the **low byte** of full request to P+0x4C9. Load eight bytes from literal 0x00402548+8 = 0x00402550 onto local stack; pinned initial bytes are `05 06 04 03 02 01 00 00`. In sequence for i=0..5, read unsigned halfword new_profile+2*i. If it is nonzero call 0x002B8794(i, local_priority[i], halfword & 0xFF, 0); if zero call 0x002B8794(i,0x12,0x51,0). A halfword like 0x0100 is nonzero and therefore uses priority[i] and r2=0, not the defaults. All six calls happen in order; their transitive writes/calls are significant.

Read old_profile+0x0C as byte. If zero, reload manager+4, store byte 1 to that current object's +0x4C5 and call 0x0013851C(1). If old byte nonzero, inspect new_profile+0x0C: nonzero reloads manager+4, stores 0 to +0x4C5 and calls 0x0013851C(0); zero reloads manager+4, stores 1 and calls 0x002AE874(1). Return with the called service's r0. The object used for final +0x4C5 is reloaded and can differ from original P under mutation; profile pointers and manager/object aliases must not be casually assumed immutable. No direct VFP, sound-API call, or simple r0 success normalization occurs. Stack and transitive writes are separate from the direct writes above.

## Dependencies and boundaries

0x002B85BC performs old/new lookups and can iterate six slots, call 0x002BF030 and other services, and mutate state; it cannot be represented as a pure lookup. 0x002B8794 can write manager/slot state and has its own null/bounds branches. 0x0013851C and 0x002AE874 perform multi-slot operations with further helper calls. For initial bounded tests these remain original or controlled separately validated stubs; traces must assert every call/argument and complete persistent memory effects. `0x002AEA28` obtains resource data through 0x002C0EC4/0x002C0E9C/0x002C0E4C, so its returned pointers, byte +0x0C and 12 bytes of halfwords must be valid. Those helpers' full behavior, potential aliases and mutation are not established by the wrapper. Null/unmapped globals, pointer invalidation, overlap, concurrency, invalid resource counts, and actual sound/audio behavior require separate evidence.

## Caller census

Pinned-image aligned raw ARM scan found 254 BL and 49 B candidates, and no aligned absolute pointer. It may match data and does not exhaust Thumb, indirect or dynamic callers. Ledger function attribution does not establish runtime execution.

| Branch | Ledger function | PCs |
| --- | --- | --- |
| BL | `Camp_DemonicaArchiveLoad` / `0x00114374` | `0x0011518C`, `0x00115198`, `0x00115538`, `0x00115634` |
| BL | `Camp_MainProc` / `0x0017FE9C` | `0x0017FF60`, `0x001806CC`, `0x001807F0`, `0x001808FC`, `0x001813F0`, `0x00183E88` |
| BL | `engine_func_0018844c` / `0x0018844C` | `0x00188E5C`, `0x00188E80` |
| BL | `camp_func_0018a2e0` / `0x0018A2E0` | `0x0018A9B8` |
| BL | `Result_Calc` / `0x0018BFEC` | `0x0018E094`, `0x0018E34C`, `0x0018E68C`, `0x0018E748`, `0x0018E984`, `0x0018E9E8`, `0x0018EC1C` |
| BL | `script_vm_func_0019416c` / `0x0019416C` | `0x00194468`, `0x001946D0` |
| BL | `FlowScript_EventVmExecute` / `0x001955BC` | `0x001956BC`, `0x00195704`, `0x00195730`, `0x00195740`, `0x0019575C`, `0x0019576C`, `0x001957B4`, `0x001957C4`, `0x001957E8`, `0x001959C8`, `0x00195A90`, `0x00195ABC`, `0x00195ACC`, `0x00195AE8`, `0x00195AF8`, `0x00195B08`, `0x00195B50`, `0x00195B74`, `0x00195B84`, `0x00195B98`, `0x00195F00`, `0x00196470` |
| BL | `script_vm_func_00198f1c` / `0x00198F1C` | `0x00198FA0` |
| BL | `Camp_DrawStereoViews` / `0x0019A3EC` | `0x0019B288`, `0x0019C108` |
| BL | `script_vm_func_0019f2d8` / `0x0019F2D8` | `0x0019F4A8` |
| BL | `script_vm_func_001afb08` / `0x001AFB08` | `0x001AFF34`, `0x001B0004`, `0x001B0094`, `0x001B00F0` |
| BL | `engine_func_001b0fe0` / `0x001B0FE0` | `0x001B10B0`, `0x001B14D0` |
| BL | `btlMain_Calc` / `0x001B55F0` | `0x001B5A5C`, `0x001B5B04` |
| BL | `FlowScript_DispatchNativeCommands` / `0x001B7E78` | `0x001BB284` |
| BL | `ui_func_001c0b38` / `0x001C0B38` | `0x001C0D34` |
| BL | `FlowScript_EvalStateControl` / `0x001C3ED4` | `0x001C5B4C`, `0x001C5BB0`, `0x001C6818`, `0x001C6A50`, `0x001C6A6C`, `0x001C6EAC`, `0x001C7138`, `0x001C7560` |
| BL | `func_001c8d28` / `0x001C8D28` | `0x001C9C70`, `0x001C9F78`, `0x001CA234` |
| BL | `StatusDown_CalcTaskCallback` / `0x001CA648` | `0x001CAA84`, `0x001CB7C0`, `0x001CBD24` |
| BL | `Ui_StatusScreenSkills` / `0x001CE98C` | `0x001CEAC8`, `0x001CEF14`, `0x001CF1A8`, `0x001CF26C`, `0x001CFBF8` |
| BL | `onesRoom_Init` / `0x001D38FC` | `0x001D396C` |
| BL | `FlowScript_ExecuteOpcode` / `0x001D3D40` | `0x001D74BC` |
| BL | `Ui_TerminalSceneRender` / `0x001D98C4` | `0x001DA150`, `0x001DA25C`, `0x001DA33C`, `0x001DA55C`, `0x001DAA50`, `0x001DAB34` |
| BL | `camp_func_001dbdb0` / `0x001DBDB0` | `0x001DBDDC` |
| BL | `script_vm_func_001dbe2c` / `0x001DBE2C` | `0x001DC29C`, `0x001DC420` |
| BL | `camp_func_001dc500` / `0x001DC500` | `0x001DC52C` |
| BL | `script_vm_func_001e4c7c` / `0x001E4C7C` | `0x001E5190` |
| BL | `ui_func_001e989c` / `0x001E989C` | `0x001E9AA8`, `0x001EA3F0` |
| BL | `script_vm_func_001edc04` / `0x001EDC04` | `0x001EDD5C`, `0x001EDDD8`, `0x001EDE8C` |
| BL | `camp_func_001ee99c` / `0x001EE99C` | `0x001EED6C` |
| BL | `FlowScript_BranchCondition` / `0x001FC644` | `0x001FD4D4` |
| BL | `CampCec_func_001ffaf4` / `0x001FFAF4` | `0x001FFCB8`, `0x001FFCCC` |
| BL | `camp_func_00200064` / `0x00200064` | `0x00200068`, `0x002001E4` |
| BL | `saveLoadUI_Calc` / `0x00202950` | `0x00202CDC` |
| BL | `camp_func_002034dc` / `0x002034DC` | `0x00203538` |
| BL | `script_vm_func_002041f4` / `0x002041F4` | `0x0020442C`, `0x00204AFC`, `0x00204C04`, `0x00204C8C` |
| BL | `camp_func_00211400` / `0x00211400` | `0x0021142C` |
| BL | `ui_func_00213b24` / `0x00213B24` | `0x00213DA8` |
| BL | `StatusDown_SetPartyPrompt` / `0x00215990` | `0x002159D8` |
| BL | `script_vm_func_00216d68` / `0x00216D68` | `0x00216F64`, `0x00216F88`, `0x00216FC4` |
| BL | `camp_func_002178a0` / `0x002178A0` | `0x00217FE4` |
| BL | `camp_func_00218384` / `0x00218384` | `0x002183C4` |
| BL | `ui_func_00220c5c` / `0x00220C5C` | `0x00220D40` |
| BL | `script_vm_func_00223190` / `0x00223190` | `0x002231F0` |
| BL | `script_vm_func_002231fc` / `0x002231FC` | `0x0022325C` |
| BL | `script_vm_func_002250e8` / `0x002250E8` | `0x002250F4` |
| B | `script_vm_func_0022b1f8` / `0x0022B1F8` | `0x0022B25C`, `0x0022B274`, `0x0022B28C`, `0x0022B2C0`, `0x0022B2CC`, `0x0022B2D8` |
| BL | `camp_func_0022cb1c` / `0x0022CB1C` | `0x0022CB44` |
| BL | `camp_func_0022fbc0` / `0x0022FBC0` | `0x0022FC68` |
| B | `shop_func_00230790` / `0x00230790` | `0x00230884` |
| BL | `camp_func_00233ac0` / `0x00233AC0` | `0x00233B4C`, `0x00233B88`, `0x00233C50`, `0x00233E2C` |
| B | `camp_func_00233ac0` / `0x00233AC0` | `0x00233EFC` |
| BL | `camp_func_0023f1d0` / `0x0023F1D0` | `0x0023F228` |
| BL | `camp_func_00241c70` / `0x00241C70` | `0x00241C9C`, `0x00241D08`, `0x00241D20`, `0x00241D40`, `0x00241D58` |
| B | `camp_func_00241c70` / `0x00241C70` | `0x00241CE4` |
| BL | `script_vm_func_0026c480` / `0x0026C480` | `0x0026C4FC`, `0x0026C62C` |
| BL | `FlowScript_OpcodeEvaluator` / `0x0027154C` | `0x0027196C` |
| BL | `script_vm_func_00273760` / `0x00273760` | `0x002737DC` |
| B | `script_vm_func_00273ab0` / `0x00273AB0` | `0x00273AE8`, `0x00273B6C`, `0x00273B8C`, `0x00273BB4`, `0x00273BC0`, `0x00273BCC` |
| BL | `script_vm_func_00273bfc` / `0x00273BFC` | `0x00273D14` |
| B | `script_vm_func_00276170` / `0x00276170` | `0x00276194`, `0x002761B4`, `0x002761DC`, `0x002761E8`, `0x002761F4` |
| BL | `engine_func_00280054` / `0x00280054` | `0x002802A0` |
| BL | `engine_func_00286928` / `0x00286928` | `0x00286B80` |
| BL | `Camp_Calc` / `0x0028AB8C` | `0x0028AF28` |
| BL | `script_vm_func_00290544` / `0x00290544` | `0x0029064C` |
| BL | `script_vm_func_00290874` / `0x00290874` | `0x002908A0`, `0x002908BC`, `0x002908E0`, `0x002908FC`, `0x0029090C`, `0x00290928`, `0x00290938`, `0x00290948` |
| B | `script_vm_func_00290874` / `0x00290874` | `0x002908D4` |
| B | `battle_func_00293074` / `0x00293074` | `0x002930B8`, `0x002930D8`, `0x002930E4`, `0x00293104`, `0x0029313C`, `0x00293148`, `0x0029315C`, `0x00293168`, `0x00293190`, `0x0029319C`, `0x002931B0`, `0x002931BC` |
| BL | `script_vm_func_00296a18` / `0x00296A18` | `0x00296B14`, `0x00296B9C` |
| BL | `shop_func_00297178` / `0x00297178` | `0x002971D0` |
| BL | `camp_func_002983dc` / `0x002983DC` | `0x00298440`, `0x00298464`, `0x002984A4`, `0x00298540` |
| B | `camp_func_0029e48c` / `0x0029E48C` | `0x0029E5B4` |
| BL | `camp_func_0029feac` / `0x0029FEAC` | `0x0029FF70`, `0x0029FF9C`, `0x0029FFA8`, `0x0029FFF8`, `0x002A0174`, `0x002A01C4`, `0x002A0210`, `0x002A0258` |
| BL | `camp_func_002a0ea8` / `0x002A0EA8` | `0x002A0F28` |
| BL | `ui_func_002cdb6c` / `0x002CDB6C` | `0x002CDC8C` |
| BL | `script_vm_func_002cdd1c` / `0x002CDD1C` | `0x002CDD6C` |
| BL | `StatusDown_UpdateHelpMessage` / `0x002CF4E0` | `0x002CF550` |
| B | `camp_func_002cfe24` / `0x002CFE24` | `0x002CFF30` |
| BL | `engine_func_002d41a0` / `0x002D41A0` | `0x002D432C` |
| BL | `engine_func_002d4838` / `0x002D4838` | `0x002D492C` |
| BL | `CampCecEdit_func_002d678c` / `0x002D678C` | `0x002D6A54` |
| BL | `script_vm_func_002d6cd8` / `0x002D6CD8` | `0x002D6FDC`, `0x002D7134`, `0x002D7274` |
| B | `CampCecView_func_002d7410` / `0x002D7410` | `0x002D76FC` |
| BL | `script_vm_func_002e16d0` / `0x002E16D0` | `0x002E1784` |
| BL | `camp_func_002e1824` / `0x002E1824` | `0x002E1890`, `0x002E1954`, `0x002E1978` |
| BL | `ui_func_002e4008` / `0x002E4008` | `0x002E4028` |
| BL | `engine_func_002e8ba0` / `0x002E8BA0` | `0x002E8CF0` |
| BL | `engine_func_002e8f9c` / `0x002E8F9C` | `0x002E9138` |
| BL | `engine_func_002e9b20` / `0x002E9B20` | `0x002E9C50` |
| BL | `script_vm_func_002ea100` / `0x002EA100` | `0x002EA2E4` |
| BL | `engine_func_002ea4c0` / `0x002EA4C0` | `0x002EA65C` |
| BL | `camp_func_002ec530` / `0x002EC530` | `0x002ECCD0` |
| BL | `script_vm_func_002ece08` / `0x002ECE08` | `0x002ECE78` |
| BL | `titleConfig_func_002f4ca0` / `0x002F4CA0` | `0x002F4DF0` |
| B | `CampCecSetting_func_002f5bc0` / `0x002F5BC0` | `0x002F5CF4` |
| BL | `script_vm_func_002fe924` / `0x002FE924` | `0x002FE998` |
| BL | `script_vm_func_00310658` / `0x00310658` | `0x00310698` |
| BL | `StatusDown_OpenCategorySelect` / `0x00311494` | `0x00311538` |
| BL | `script_vm_func_00311618` / `0x00311618` | `0x00311710` |
| BL | `ui_func_003171f8` / `0x003171F8` | `0x00317B80` |
| BL | `script_vm_func_0031c418` / `0x0031C418` | `0x0031C488` |
| BL | `camp_func_00329404` / `0x00329404` | `0x00329490`, `0x00329B18`, `0x00329D28` |
| BL | `camp_func_00329da4` / `0x00329DA4` | `0x0032A244`, `0x0032A87C` |
| BL | `Camp_SubModeProcess` / `0x0032CB08` | `0x0032D06C`, `0x0032D0B8`, `0x0032D0F0`, `0x0032D4BC`, `0x0032D7CC`, `0x0032F5B8`, `0x0032FAA0` |
| B | `Camp_WhisperSkillTransfer` / `0x00332100` | `0x00332210` |
| BL | `Camp_WhisperSkillTransfer` / `0x00332100` | `0x00332260`, `0x003322AC`, `0x003331E0`, `0x003336B4`, `0x00333738` |
| BL | `Ui_MemoryArenaAllocate` / `0x00345194` | `0x00346804`, `0x00346840` |
| BL | `script_vm_func_00382014` / `0x00382014` | `0x00382050`, `0x003820F8`, `0x0038217C` |
| BL | `script_vm_func_003823e8` / `0x003823E8` | `0x00382530`, `0x00382580`, `0x00382648`, `0x00382850` |
| BL | `script_vm_func_00384a10` / `0x00384A10` | `0x00384A38` |
| BL | `script_vm_func_00384be0` / `0x00384BE0` | `0x00384C40` |
| BL | `script_vm_func_00384df8` / `0x00384DF8` | `0x00385164` |
| BL | `script_vm_func_00385658` / `0x00385658` | `0x00385734`, `0x00385840`, `0x00385A28` |
| B | `script_vm_func_00397730` / `0x00397730` | `0x00397768`, `0x00397788`, `0x00397794` |
| B | `script_vm_func_00397d5c` / `0x00397D5C` | `0x00397DB8`, `0x00397FB0`, `0x00397FC0` |
| BL | `script_vm_func_00397d5c` / `0x00397D5C` | `0x00397E00` |
| BL | `ui_func_00398a90` / `0x00398A90` | `0x00398B0C` |
| BL | `script_vm_func_003a0f80` / `0x003A0F80` | `0x003A115C` |
| BL | `shop_func_003a2e64` / `0x003A2E64` | `0x003A2FCC` |
| BL | `script_vm_func_003a334c` / `0x003A334C` | `0x003A33A8` |
| BL | `shop_func_003a4c7c` / `0x003A4C7C` | `0x003A4D20`, `0x003A5428`, `0x003A5450` |
| BL | `shop_func_003a7084` / `0x003A7084` | `0x003A7100`, `0x003A7188` |
| BL | `script_vm_func_003a719c` / `0x003A719C` | `0x003A73B8` |
| BL | `shop_func_003a74c0` / `0x003A74C0` | `0x003A76C8` |
| BL | `script_vm_func_003a78d4` / `0x003A78D4` | `0x003A7960`, `0x003A7A10` |
| BL | `script_vm_func_003a7e04` / `0x003A7E04` | `0x003A7F70` |
| B | `script_vm_func_003a81b8` / `0x003A81B8` | `0x003A8200` |
| BL | `shop_func_003a8314` / `0x003A8314` | `0x003A83C8` |
| B | `camp_func_003a8460` / `0x003A8460` | `0x003A84AC`, `0x003A8520` |
| BL | `camp_func_003a858c` / `0x003A858C` | `0x003A85A8` |
| BL | `camp_func_003a8670` / `0x003A8670` | `0x003A88C0` |
| BL | `shop_func_003a8b14` / `0x003A8B14` | `0x003A8B88` |
| BL | `shop_func_003a8fcc` / `0x003A8FCC` | `0x003A9054` |
| BL | `script_vm_func_003ab2d4` / `0x003AB2D4` | `0x003AB30C` |
| BL | `shop_func_003ab348` / `0x003AB348` | `0x003AB494` |
| BL | `camp_func_003ac020` / `0x003AC020` | `0x003AC03C` |
| BL | `script_vm_func_003b8e60` / `0x003B8E60` | `0x003B8F64` |
| BL | `engine_func_003b9078` / `0x003B9078` | `0x003B91B4`, `0x003B9238` |
| BL | `script_vm_func_003b9ca4` / `0x003B9CA4` | `0x003B9D54` |
| BL | `script_vm_func_003c0aa8` / `0x003C0AA8` | `0x003C0B44` |
| BL | `script_vm_func_003c7a94` / `0x003C7A94` | `0x003C7DB0` |
| BL | `battle_func_003d1968` / `0x003D1968` | `0x003D1DF0` |
| B | `battle_func_003d236c` / `0x003D236C` | `0x003D2534`, `0x003D26E4` |

## Differential and promotion plan

Use pinned original vs compiled replacement with valid mapped disjoint manager, object and profile fixtures. Direct cases: same ID; manager+0x10 negative/nonnegative; scan first/middle/last nonzero and all zero; requests 0,255,256,0xDC,0xFFFFFFFF (full-width comparison/store vs byte write); both lookup null combinations; both profile pointers nonnull and all old/new +0x0C combinations; six halfwords 0,1,0x100,0xFFFF, with distinct priorities; confirm call order, six argument tuples, global/persistent ordered stores, final r0, SP/r4-r11 and fault cases under explicit mappings. Controls should mutate scan polarity/bounds, full-width vs byte equality, second lookup omission, zero-halfword default and each final branch. Run separately with controlled helper traces and valid real helper/ring/resource fixtures; stubs do not prove transitive equivalence. Compose original TitleConfig_Init call 0x99 and conditional original 0x00286928 call 0xDC, asserting exact reachability and identical state; then independent review, integrated placement/interworking and original-versus-patched runtime scenario. Do not claim alias/concurrent/faulting or physical audio behavior until separately supported. No build, ARM execution, emulator or runtime occurred in this task.

## Provenance

All run002 frozen packet hashes matched on recomputation. The target assembly text is unchanged from dispatch commit `a7f50a1`, text SHA-256 `303dadc1e147417aa5e717f54bf074c68b616754853af6f2fbede57b03771360`. All 85 source instructions/word directives matched pinned disassembly or raw words after symbol/label normalization; no assembly was run, so textual instruction matching alone does not prove re-encoded bytes. Pinned 340-byte span SHA-256 `2ce00a8e6e83b2453e2be4b7e877022b3b2347fdc08ac907a39d94ac10f4e611`. Pinned image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; source `src/engine/leaf_batch32_c.cpp` `cd42f835f48189b1e7700c92bdd2b51ab09dc92b5f59cdc29682c59fdcbd22df`; callback source `src/engine/leaf_batch30_c.cpp` `5d14bc774791213e7198633abcf259704d7606619a8b5e2b5990f3d06dbb829e`; helper source `src/engine/leaf_batch45_a.cpp` `962c018c8c02971ed5bf77cca52685dcda4d7cc2634868e8e7640009ddb17dff`. Read-only `python -` Capstone disassembly of target/callers/dependencies, literal/table reads, aligned ARM B/BL scan and SHA-256 checks exited 0.
