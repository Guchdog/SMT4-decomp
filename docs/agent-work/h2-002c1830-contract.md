# 0x002C1830: input query dispatch contract

## Recommendation

Implement this as a bounded non-leaf C++ slice after independent contract review. Its static relevance to H2 is direct: `TitleConfig_Calc` calls it at six ARM PCs in its state-1 path. Preserve all six helper dependencies, fallback call order and returned words; a synthetic input hook alone does not establish real input or runtime equivalence. Slot size is 504 bytes (including embedded table); check ABI, relocation, ARM/Thumb interworking and placement rather than assuming source size or byte identity.

## Exact ARM control flow

Inputs r0=32-bit ID, r1=32-bit mode, both compared as full unsigned words; r4-r6 and LR are pushed (16 bytes) and restored before normal return or tail transfer. Other callee-saved registers and SP are preserved assuming callee ABI. No direct non-stack memory writes and no VFP operations occur in the wrapper; VFP/flags/r0-r3/r12 and memory effects of original callees are not thereby constrained. The 11-entry ARM jump table 0x002C1850..0x002C1878 maps ID to fallback code as follows:

| ID | fallback code | secondary ID |
| --- | --- | --- |
| 0 | 1 | none |
| 1 | 2 | none |
| 2 | 0 | none |
| 3, 4, 5, 6 | 0 | 12, 13, 14, 15 respectively |
| 7 | 6 | none |
| 8 | 5 | none |
| 9 | 3 | none |
| 10 | 4 | none |
| >=11, including high-bit IDs | 0 | none |

Mode 0 first calls 0x002B902C(ID), mode 1 calls 0x002BFFBC(ID), mode 2 calls 0x002C17D4(ID). If that return is nonzero, it immediately returns the word unchanged. If zero, IDs 3..6 call the same selected helper with the mapped secondary ID and immediately return its word if nonzero. If still zero and fallback code !=0, restore registers and tail-branch with r0=fallback code: mode 0 -> 0x00125C10, mode 1 -> 0x00124FA8, mode 2 -> 0x00124F0C. Its return is propagated unchanged. If fallback code=0 return the preceding zero. Any mode other than exactly 0, 1 or 2 makes no helper call and returns zero for any ID. Do not normalize arbitrary nonzero helper returns or reinterpret high values as signed negatives when dispatching.

0x002B902C and 0x002BFFBC are recorded `non_matching` in the ledger; 0x002C17D4 is `matching`. Ledger status alone does not establish current signatures or equivalence; inspect their definitions and validation provenance before integration. The pinned helpers all have an unsigned `ID < 31` guard: 0x002B902C uses global state and can call 0x002C6C10; 0x002BFFBC consults global state/table; 0x002C17D4 consults globals and 8-byte keyed entries. Their original ARM side effects and global state must remain in real composition. Fallbacks use input context and further helpers; 0x00124F0C, 0x00124FA8 and 0x00125C10 are ARM addresses (the last two are recorded matching); exact input system semantics and lifetime are outside this contract. Keep original helpers unless separately reviewed, or instrument deterministic stubs to prove argument/order and return propagation; a separate run with real dependencies is necessary.

## TitleConfig_Calc

The original state jump table at 0x001EA950 maps state 1 to 0x001EAA60. The six sites in that state are:

| PC | ID / mode | role in original control flow |
| --- | --- | --- |
| 0x001EAABC | 9 / 1 | query when earlier touch result is not 6; nonzero enters selected-row action. |
| 0x001EABDC | 4 / 0 | query decrement if prior condition is zero. |
| 0x001EAC20 | 3 / 0 | query increment if decrement did not trigger and prior condition is zero. |
| 0x001EAC50 | 4 / 0 or 3 / 0 | second query after decrement or increment update, return ignored; 4 reaches it through branch at 0x001EAC0C. |
| 0x001EAE64 | 0 / 1 | if nonzero takes edit/confirm path and changes state to 2. |
| 0x001EAF14 | 1 / 1 | if nonzero takes exit/cancel path and changes state to 3. |

These are static paths, not evidence of dynamic input timing, repeat semantics or scenario completion. The C++ caller source already uses typed address calls for these queries; other source files have legacy no-argument `void` declarations, so affected external declarations and ARM callers require ABI audit before a shared typed signature is promoted.

## Direct caller inventory

The pinned-image word-aligned raw ARM scan found 225 BL encodings, no B encoding and no exact aligned pointer to 0x002C1830. This scan can interpret data as instructions and cannot capture Thumb, register-indirect or dynamic calls. Names below are ledger ownership, not a claim each site executes.

| Ledger function | BL PCs |
| --- | --- |
| `engine_func_001066ac` / `0x001066AC` | `0x00106990` |
| `camp_func_0010edd4` / `0x0010EDD4` | `0x0010EDF8`, `0x0010EE10`, `0x0010EE54`, `0x0010EE68`, `0x0010EED8`, `0x0010EF04`, `0x0010EF6C` |
| `camp_func_0010efb4` / `0x0010EFB4` | `0x0010EFC4`, `0x0010EFD8`, `0x0010EFFC`, `0x0010F03C` |
| `camp_func_0010f060` / `0x0010F060` | `0x0010F070`, `0x0010F084`, `0x0010F098`, `0x0010F0AC`, `0x0010F0EC` |
| `Camp_DemonicaArchiveLoad` / `0x00114374` | `0x00114864`, `0x00114888`, `0x00114BB8`, `0x00114C5C`, `0x0011505C`, `0x00115074`, `0x00115904`, `0x00115944` |
| `Camp_MainProc` / `0x0017FE9C` | `0x001801B0`, `0x0018074C`, `0x0018081C`, `0x00180B40`, `0x00180C50`, `0x00180DE8`, `0x001812D4`, `0x001814BC`, `0x00181A94`, `0x00181F84`, `0x00182170`, `0x001821A8`, `0x001821F8`, `0x00182D60`, `0x00182DBC`, `0x00182E04`, `0x0018328C`, `0x00183310`, `0x00183678`, `0x00183764`, `0x00183880`, `0x001838E8`, `0x00183F1C`, `0x00184010`, `0x00184160`, `0x00184E44`, `0x00185054`, `0x0018508C`, `0x0018510C`, `0x001857C8`, `0x00185828`, `0x00185878`, `0x00185DC8` |
| `engine_func_0018844c` / `0x0018844C` | `0x00188A4C`, `0x00188BD0`, `0x00188C28`, `0x00188C54`, `0x00188EB8` |
| `camp_func_0018a2e0` / `0x0018A2E0` | `0x0018A39C`, `0x0018A790`, `0x0018A9D8`, `0x0018AA08` |
| `script_vm_func_0018b878` / `0x0018B878` | `0x0018BB18`, `0x0018BB78`, `0x0018BB90`, `0x0018BBCC`, `0x0018BD00`, `0x0018BD90` |
| `Result_Calc` / `0x0018BFEC` | `0x0018CE98`, `0x0018CEB0`, `0x0018D558`, `0x0018E0BC`, `0x0018E920`, `0x0018E9BC` |
| `Status_CalcTaskCallback` / `0x0018F560` | `0x00190284`, `0x0019035C`, `0x00190438`, `0x00190478` |
| `camp_func_00195044` / `0x00195044` | `0x00195300` |
| `FlowScript_EventVmExecute` / `0x001955BC` | `0x001963F8`, `0x0019665C`, `0x001968E4`, `0x00196944`, `0x001969A4`, `0x001969BC`, `0x00196B10`, `0x00196B70`, `0x00196BE8`, `0x00196C00` |
| `Camp_DrawStereoViews` / `0x0019A3EC` | `0x0019A9E4`, `0x0019AA20`, `0x0019AA6C`, `0x0019AB1C`, `0x0019ADC0`, `0x0019B2C8`, `0x0019B37C`, `0x0019B3C8`, `0x0019B8B0`, `0x0019B9B8`, `0x0019BA0C`, `0x0019BA64`, `0x0019BC5C`, `0x0019BCB8`, `0x0019BD0C`, `0x0019BD5C`, `0x0019C16C`, `0x0019C264`, `0x0019C298`, `0x0019C2B4`, `0x0019C5AC`, `0x0019C640`, `0x0019C854`, `0x0019C8E4`, `0x0019C95C`, `0x0019C9D8`, `0x0019CC58` |
| `btlUI_Calc` / `0x0019E034` | `0x0019E670`, `0x0019ECE0` |
| `camp_func_001a1e7c` / `0x001A1E7C` | `0x001A23F0`, `0x001A247C` |
| `script_vm_func_001afb08` / `0x001AFB08` | `0x001AFB5C`, `0x001AFD68`, `0x001AFDE0`, `0x001AFE44`, `0x001AFEE8`, `0x001AFF70`, `0x001B0210` |
| `script_vm_func_001b5054` / `0x001B5054` | `0x001B5200`, `0x001B52A4`, `0x001B52E8`, `0x001B5330` |
| `FlowScript_EvalStateControl` / `0x001C3ED4` | `0x001C46F4`, `0x001C4798`, `0x001C4E2C`, `0x001C4F50`, `0x001C599C`, `0x001C659C`, `0x001C65E4`, `0x001C6BA0`, `0x001C6BC0`, `0x001C6E18`, `0x001C6E44`, `0x001C7050`, `0x001C7264` |
| `StatusDown_CalcTaskCallback` / `0x001CA648` | `0x001CAAD4`, `0x001CAB14`, `0x001CAE00`, `0x001CAF04`, `0x001CB474`, `0x001CB4B4`, `0x001CB614`, `0x001CB664`, `0x001CB688`, `0x001CB9E4`, `0x001CBA9C`, `0x001CBAC0`, `0x001CBDBC`, `0x001CBDFC`, `0x001CBF80`, `0x001CC0FC`, `0x001CC114`, `0x001CC1C4`, `0x001CC280`, `0x001CC474`, `0x001CC48C` |
| `Ui_StatusScreenSkills` / `0x001CE98C` | `0x001CEFB4`, `0x001CF17C`, `0x001CF1D4`, `0x001CF1EC`, `0x001CF31C`, `0x001CF354`, `0x001CF36C`, `0x001CF384` |
| `Ui_TerminalSceneRender` / `0x001D98C4` | `0x001D9FA0`, `0x001DA5EC`, `0x001DA604`, `0x001DA61C` |
| `script_vm_func_001ea928` / `0x001EA928` | `0x001EAABC`, `0x001EABDC`, `0x001EAC20`, `0x001EAC50`, `0x001EAE64`, `0x001EAF14` |
| `script_vm_func_002041f4` / `0x002041F4` | `0x002047E4`, `0x00204838`, `0x002048A8`, `0x002048D4`, `0x00204AB4`, `0x00204B64` |
| `camp_func_002178a0` / `0x002178A0` | `0x00217DA4`, `0x00217EF0` |
| `engine_func_0026d080` / `0x0026D080` | `0x0026D13C`, `0x0026D188` |
| `camp_func_0026d910` / `0x0026D910` | `0x0026D92C`, `0x0026DCA4` |
| `camp_func_00329404` / `0x00329404` | `0x00329940`, `0x00329A00`, `0x00329A5C` |
| `camp_func_00329da4` / `0x00329DA4` | `0x0032A3A8`, `0x0032A3C8` |
| `Camp_SubModeProcess` / `0x0032CB08` | `0x0032DE10`, `0x0032DED0`, `0x0032DF0C`, `0x0032EB58` |
| `camp_func_0033138c` / `0x0033138C` | `0x003314A8`, `0x003314D0`, `0x003315E8` |
| `Camp_WhisperSkillTransfer` / `0x00332100` | `0x003329F4`, `0x00332E64`, `0x00333264`, `0x00333308`, `0x00333394`, `0x003333D0`, `0x0033341C`, `0x00333450` |
| `script_vm_func_0038315c` / `0x0038315C` | `0x003831E8` |
| `script_vm_func_00384be0` / `0x00384BE0` | `0x00384C7C` |
| `script_vm_func_00392060` / `0x00392060` | `0x0039219C` |
| `script_vm_func_003a334c` / `0x003A334C` | `0x003A33D4` |
| `battle_func_003d1968` / `0x003D1968` | `0x003D19E8` |

## Differential and caller strategy

Use a controlled call trace to test every ID 0..11 plus large/high-bit IDs and modes 0,1,2,3,0xFFFFFFFF; explicitly test zero/nonzero first return, secondary-ID order and short circuit for 3..6, fallback code and tail destination for 0,1,7..10, no fallback for IDs 2..6/outside range, and raw nonzero return propagation. Seed arbitrary non-boolean stub returns to expose accidental normalization, but do not assert such values are reachable from all original callees. Compare returns, r4-r11/SP, call sequence and visible memory; use negative controls for mode, table mapping, secondary ID, order, return normalization and fallback. Then compose original TitleConfig_Calc at each site, including the two alternative arguments at 0x001EAC50, using same valid input fixtures and real helpers wherever supported; independently test any stubs, global lifetimes, interworking and non-leaf calls. One wide integrated regression and runtime scenario follow independent review.

No build, ARM differential, caller execution or runtime was performed here. The existing callee ledger labels and synthetic caller paths do not establish real game-input behavior.

## Provenance

All declared packet hashes were recomputed and matched. Pinned image `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; wrapper source `src/engine/leaf_batch40_a.cpp` `5263e586f45ef8ce05f2030d7e268108430a9823b18614d31e9c6d8305786215`; TitleConfig source `src/engine/leaf_batch46_b.cpp` `c76ab50c12589404ca81e35373c8b136c50c91eb63c5af805bf05cc44c6081c7`. Read-only Capstone disassembly, aligned image scans and hash verification exited 0.
