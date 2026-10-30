# H1 Menu Slice Integration (`h1-menu-slice-integration`) — 2026-10-25

## 1. Concrete State-5 Slice Definitions

Following the readiness audit (`docs/agent-work/h1-main-callback-editable-readiness.md`) and its independent review (`docs/agent-work/h1-main-callback-editable-readiness-review.md`), whole-function activation of the `#if 0` draft of `ui_func_001e989c` (`0x001E989C..0x001EA7F0`, 3,924 bytes) was rejected because 36 of its 46 declared external helpers have no compiled definitions and the draft has two semantic divergences (State 3 readiness cascade at `0x001E9B90..0x001E9BBC` and State 5 touch loop priority at `0x001E9E4C..0x001E9EB8`).

Instead, we defined, reconstructed, and integrated two bounded C++ slices within the H1 title callback in `src/ui/ui_runtime2.cpp` and `include/camp/title_flow.h`:

1. **State-5 Readiness + Navigation Slice (`0x001E9D08..0x001E9DDC`, 54 words / 216 bytes):**
   - **Production C++ Function `H1_TitleMain_UpdateNavigationSlice(camp::TitleMainWork** captured_work_out)`:**
     - Declared in `include/camp/title_flow.h` and defined in `src/ui/ui_runtime2.cpp` (compiled ARMv6K size: 256 bytes, 0 relocations).
     - Evaluates the two readiness gates (`Script_IsReadyToAdvance` `0x00289924` and `Camp_IsPreviewReady` `0x0025A2BC`) in exact short-circuit order; if either returns `0`, returns `0u` without touching `*captured_work_out` or the workspace.
     - Reads the singleton slot `0x0044E300` (`camp::g_TitleMainWork`), publishes `*captured_work_out = work` (so the caller continuation preserves the exact post-gate `r4` pointer even under external slot mutation), and increments `work->field_64 += 1.0f`.
     - Queries `UiInput_Trigger` (`0x002B902C`) for logical IDs `{5, 0xE}` (decrement `work->field_08`) and `{6, 0xF}` (increment `work->field_08`) with short-circuit semantics.
     - Normalizes `work->field_08` via unsigned `NormalizeSignedRemainderByFour` (matching the ARM signed remainder of `provisional + 4` by 4 without calling `__aeabi_idivmod`), compares against `work->field_0c`, and if changed calls `Script_RequestEvent(0x0100016C)` (`0x002B91C4`) before updating `work->field_0c = selection`.
     - Returns `1u` on ready.
   - **In-Place 54-Word Continuation Shim in `ui_func_001e989c` (`0x001E9D08..0x001E9DDC`):**
     - Replaces the 54 words (`216` bytes) of `0x001E9D08..0x001E9DDC` with an aligned stack-frame call passing `sp` to `bl H1_TitleMain_UpdateNavigationSlice`.
     - On `r0 == 0`, branches to `0x001EA62C` with `r4`, `r8`, and `s17` completely unmodified.
     - On `r0 != 0`, sets `r4 = captured_work`, loads `r8 = 0x0044E300`, sets `s17 = 1.0f`, and branches to `0x001E9DE0`.

2. **State-5 Confirmation & Transition Slice (`0x001EA160..0x001EA328`, 115 words / 460 bytes):**
   - **Production C++ Function `H1_TitleMain_ProcessConfirmationSlice(camp::TitleMainWork* work)`:**
     - Declared in `include/camp/title_flow.h` and defined in `src/ui/ui_runtime2.cpp` (compiled ARMv6K size: 444 bytes, 0 relocations).
     - Checks sound/cursor readiness via `work->field_90 == 0` and `work->field_94 == 0` (calling `0x002C0514` if needed).
     - Queries trigger confirmation `UiInput_Trigger2(0)` (`0x002BFFBC`).
     - Guards unconfirmed state for selection 1 (`work->field_08 == 1` and `work->field_74 == 0`).
     - Requests confirmation sound event `Script_RequestEvent(0x0100016D)` (`0x002B91C4`).
     - Drives cursor blink progression via `Camp_AdvanceCursorBlink(&work->field_70, 0x14, 0x1E, 0x28)` (`0x002B4FA0`).
     - Performs confirmation dispatch:
       - Selection 0 (New Game): sets `work->state_9C = 6`
       - Selection 1 (Load Game): sets `work->state_9C = 7`
       - Selection 2 (Audio Settings): sets `work->state_9C = 9`
       - Selection 3 (Add-On Content): sets `work->state_9C = 11`
     - Returns status and cleanly transitions `work->state_9C`.
   - **In-Place 115-Word Continuation Shim in `ui_func_001e989c` (`0x001EA160..0x001EA328`):**
     - Replaces the 115 words (`460` bytes) with a direct call: `mov r0, r5`, `bl H1_TitleMain_ProcessConfirmationSlice`, and branch `b 0x001EA62C` (`0xea0000bf`), padded with 112 NOPs.
     - Preserves the exact 3,924-byte function extent, preserving 100% byte identity for prefix `0..1132` (`0x001E989C..0x001E9D04`), intermediate `1348..2244` (`0x001E9DE0..0x001EA15C`), and suffix `2704..3924` (`0x001EA32C..0x001EA7F0`).

3. **Reconstruction of `Tbb_GetDefaultTable18Payload` (`0x002C0E84`, 24 bytes) in `src/ui/tbb_loader.cpp`:**
   - Replaced naked fallthrough into `Tbb_GetPayloadData` (`0x002C0E9C`) with an ordinary C++ call:
     ```cpp
     void* Tbb_GetDefaultTable18Payload() {
         void* table = Tbb_GetGlobalSubTable(0x18, 0);
         return Tbb_GetPayloadData(table);
     }
     ```
   - Updated `config/functions.csv` marking `0x002c0e84` as `non_matching`. Eliminates stack corruption hazard when `Tbb_GetPayloadData` is compiled as C++.

---

## 2. Isolated ARMv6K Differential & Composition Evidence

Executed via `python tools/h1_menu_slice_integration_experiment.py --output build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/differential-matrix` and `python -m unittest tests.test_h1_menu_slice_integration_experiment -v` (both exit 0):

1. **Full Callback Entry (`0x001E989C`) State-5 Navigation Matrix (258/258 cases + adversarial pointer mutation + negative control):**
   - Executes from the callback entry `0x001E989C` with `state_9C = 5` through the jump table at `0x001E98C4` into `0x001E9D08`, stopping at `0x001EA62C` (gate false) or `0x001E9E50` (after the blend ramp and `ldr r6, [r8]` at `0x001E9E4C`).
   - **2/2 false readiness gate cases** (`script_not_ready`, `preview_not_ready`): stop at `0x001EA62C` with identical memory and preserved `r4`/`r8`/`s17`.
   - **256/256 Cartesian matrix cases** (`cursor 0..3 x cached 0..3 x 16 trigger masks` for IDs `5, 0xE, 6, 0xF`): 100% match on stop PC (`0x001E9E50`), helper call order, event `0x0100016C` observations, `TitleMainWork` memory, `r4-r11`, `d8-d15`, `s17`, `r6`, `SP`, and `FPSCR`.
   - **Adversarial singleton mutation case** (`captured-work-survives-global-slot-mutation`): mutates `*0x0044E300` on the first trigger query after readiness; both original and compiled production slice keep `r4 = 0x02000100` for reducer/blend updates and load `r6 = 0x02000300` at `0x001E9E4C`.
   - **Negative control** (`wrong_raw_signed_remainder_for_minus_one`): compiles a mutant `src/ui/ui_runtime2.cpp` replacing `NormalizeSignedRemainderByFour` with `static_cast<s32>(provisional) % 4`; rejected at `cursor = 0, mask = 0x01` (yields `0xFFFFFFFF` instead of `3`).

2. **State-5 Transition / Fade / Help-Lookup Composition (`0x001E9FD4..0x001EA15C`, 4/4 selections):**
   - Binds the observed runtime track callback from `h1-track-runtime` (`0x00151404` on `child_b`, duration `1200.0f` = `0x44960000`, `callback_arg = 0x00000000`), the reviewed `candidate_0029bdb4` (`0x0029BDB4`) from `h1-alpha-caller-review`, the reviewed `candidate_00151404` (`0x00151404`), and the promoted production `Tbb_GetSubTable` (`0x002AC2F4`) + `Tbb_GetPayloadData` (`0x002C0E9C`) from `src/ui/tbb_loader.cpp` with the real `TitleTable.tbb` asset.
   - Across all four selections `0..3`, original and patched executions produce identical call traces, identical memory state (`data_sha256`), identical target alpha stores (`0.5625` and `0.125`), identical fade value (`work+0x98 = 0.25`), `work+0x94 = 1`, color `r1 = 0x323232FF`, and the exact four English help strings at `0x001EA15C`.

---

## 3. Original-vs-Patched Azahar Runtime Comparison

Executed via `C:/Users/altair/.gemini/antigravity/brain/e75145bb-28b9-4c31-9257-4e168f575dd0/scratch/run_azahar_h1_slice_runtime.py` on `E:\emulador3ds\azahar.exe` with the decrypted US v0.1.0 CCI (`00040000000E5C00`) and GDB stub on `127.0.0.1:24689`, producing `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/azahar-runtime/runtime-report.json`:

- **Live Cave Execution Confirmed:** `H1_TitleMain_UpdateNavigationSlice` installed at `0x003FE720` and linked from the 54-word State-5 shim at `0x001E9D08..0x001E9DDC` hit live in Azahar (`PC = 0x003FE720`, `r0 = 0x0FFFFEA0`, `g_TitleMainWork = 0x15C00080`).
- **11/11 Runtime Steps Matched Between Original and Patched:**
  1. `initial_ready_at_001e9de0`: `state_9c = 5`, initial `selection_08 = 1` (Load Game), `cached_0c = 1`, `r4 = r5 = 0x15c00080`, `r8 = 0x0044e300`, `sp = 0x0ffffea8`.
  2. `help_lookup_sel1` at `0x001EA15C`: `r0 = 0x086c9d1c` (`"Load a saved game and continue playing."`), `r1 = 0x323232ff`.
  3. `move_down_1_to_2_at_001e9de0`: `selection_08 = 2`, `cached_0c = 2`, help at `0x001EA15C` = `0x086c9d72` (`"Configure audio settings."`).
  4. `move_down_2_to_3_at_001e9de0`: `selection_08 = 3`, `cached_0c = 3`, help at `0x001EA15C` = `0x086c9dc8` (`"Download additional content."`).
  5. `wrap_down_3_to_0_at_001e9de0`: forward wraparound `3 -> 0`, `selection_08 = 0`, `cached_0c = 0`, help at `0x001EA15C` = `0x086c9cc6` (`"Start a new game from the beginning."`).
  6. `wrap_up_0_to_3_at_001e9de0`: backward wraparound `0 -> 3`, `selection_08 = 3`, `cached_0c = 3`, help at `0x001EA15C` = `0x086c9dc8` (`"Download additional content."`).
  7. `move_up_3_to_2_at_001e9de0`: `selection_08 = 2`, `cached_0c = 2`, help at `0x001EA15C` = `0x086c9d72` (`"Configure audio settings."`).
  8. `enter_titleConfig_002f4ca0`: confirming selection 2 transitions `state_9c` to `9` and invokes `titleConfig_func_002f4ca0` (`0x002F4CA0`).
  9. `titleConfig_calc_reached`: enters `TitleConfig_Calc` (`0x001EA928`) with `g_TitleConfigWork = 0x086e4700`.
  10. `return_from_audio_settings_reset_001ea3d8`: cancelling Audio Settings enters `Title_ResetForBoot` (`0x001EA3D8`) in `state_9c = 10`.
  11. `returned_to_state5_ready_001e9de0`: returns to `state_9c = 5` at `0x001E9DE0` with `selection_08 = 2`, `cached_0c = 2`, `timer_64 = 1.0`, `blend_68 = 0.0`, `fade_6c = 1.0`, and persisted `g_ConfigBytes` (`0x0044E0F8`) unchanged (`3250503000000000`).
- **Profile & Save Integrity:** `saves_before == saves_after == []` (`saves_unchanged: true`), and `g_ConfigBytes` remained `3250503000000000`.
- **Resolved Fallthrough Hazard on `Tbb_GetPayloadData` (`0x002C0E9C`):**
  - Previously, `Tbb_GetDefaultTable18Payload` (`0x002C0E84`) fell through into `0x002C0E9C` with `r4` and `lr` still pushed on the stack (`src/ui/tbb_loader.cpp:76-85`).
  - In this task run, `Tbb_GetDefaultTable18Payload` was reconstructed in `src/ui/tbb_loader.cpp` as clean C++ calling `Tbb_GetGlobalSubTable(0x18, 0)` and `Tbb_GetPayloadData(table)` directly, cleanly eliminating the stack corruption hazard. `config/functions.csv` was updated marking `0x002c0e84` as `non_matching`.

---

## 4. Original Dependencies Still Called & Untested States

- **Original dependencies still called by the integrated State-5 slices:**
  - `Script_IsReadyToAdvance` (`0x00289924`)
  - `Camp_IsPreviewReady` (`0x0025A2BC`) and its internal callee `0x002BF9F0`
  - `UiInput_Trigger` (`0x002B902C`)
  - `UiInput_Trigger2` (`0x002BFFBC`)
  - `Script_RequestEvent` (`0x002B91C4`) for events `0x0100016C` and `0x0100016D`
  - `Camp_AdvanceCursorBlink` (`0x002B4FA0`)
- **Original ARM blocks still active inside `ui_func_001e989c` (`0x001E989C`):**
  - Function prologue/dispatch (`0x001E989C..0x001E98F4`) and common tail (`0x001EA62C..0x001EA7F0`)
  - States `0, 1, 2, 3, 4` (`0x001E98F8..0x001E9D04`)
  - State 5 blend ramp, touch-region polling loop, and fade/help-lookup tail (`0x001E9DE0..0x001EA15C`)
  - States `6, 7, 8, 9, 10, 11, 12` (`0x001EA32C..0x001EA628`)
- **Untested / Excluded H1 Paths:**
  - New Game confirmation (State 6 / 12 -> `Script_StartNewGame` `0x0026FA94`), Load Game slot selection (States 7–8 -> `SaveLoad_BeginFromTitle` `0x0030A9A4`), and Add-On Content (States 11–12) remain intentionally unexecuted in Azahar per milestone safety rules.
  - Physical touch-screen coordinate injection in Azahar and full replacement of the remaining 12 states of `ui_func_001e989c` remain open for subsequent milestones.

---

## 5. Artifact Hashes

| File | SHA-256 |
| --- | --- |
| `src/ui/ui_runtime2.cpp` | `fe0e54416e545514d1d666571a86786c4517ff6d2f506403801e685db565ee6b` |
| `src/ui/tbb_loader.cpp` | `c9628e166e8f03a2a221b5602ebdb3ca0416812e8443f6939913039a708e266e` |
| `include/camp/title_flow.h` | `441e01a885c4963eca1a3221ebce8b7a02938330fd7cca570f3804ead37f8ffe` |
| `config/functions.csv` | `8b88e2b1c356ddb87c8a5b0387cd83c36b6759a79a272e084ad2641b4b723116` |
| `tools/h1_menu_slice_integration_experiment.py` | `0e343b74ebae1e2c73bc1ed3309ff13b3bfe1ea80ae9fc5199f22957a214ce8e` |
| `tests/test_h1_menu_slice_integration_experiment.py` | `fe3f8c303c600b636a7b6603330ff43a4e77de5239b2940d18762a08f0c8f016` |
| `build/obj/armv6k/ui/ui_runtime2.o` | `b4cb252daf0770b9ef6c8e9495e4f404b0807fa7c836ddac16b727f7fbe3b0c3` |
| `build/obj/armv6k/ui/tbb_loader.o` | `87f9affb5a66b05dcab3aaf81504b4824d7a96588cb8f545aeb84d4583b10933` |
| `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/differential-matrix/report.json` | `d1ae9600641ae10ac45dc9226b7bf51c796e2ba421d96ee9cddc45d8c918497d` |
| `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/azahar-runtime/runtime-report.json` | `665dc7d4f35370063e26ee6a6e7e3f1f68ef7df50b6d8046e7687147ac2196e7` |
