# H1 Menu Slice Integration (`h1-menu-slice-integration`) — 2026-10-25

## 1. Concrete State-5 Slice Definition

Following the readiness audit (`docs/agent-work/h1-main-callback-editable-readiness.md`) and its independent review (`docs/agent-work/h1-main-callback-editable-readiness-review.md`), whole-function activation of the `#if 0` draft of `ui_func_001e989c` (`0x001E989C..0x001EA7F0`, 3,924 bytes) was rejected because 36 of its 46 declared external helpers have no compiled definitions and the draft has two semantic divergences (State 3 readiness cascade at `0x001E9B90..0x001E9BBC` and State 5 touch loop priority at `0x001E9E4C..0x001E9EB8`).

Instead, we defined and integrated the bounded **State-5 readiness + cursor navigation/wraparound + event-notification slice** (`0x001E9D08..0x001E9DDC`, 54 words / 216 bytes) inside `src/ui/ui_runtime2.cpp` and `include/camp/title_flow.h`:

1. **Production C++ Function `H1_TitleMain_UpdateNavigationSlice(camp::TitleMainWork** captured_work_out)`:**
   - Declared in `include/camp/title_flow.h` and defined in `src/ui/ui_runtime2.cpp` (compiled ARMv6K size: 256 bytes, 0 relocations).
   - Evaluates the two readiness gates (`Script_IsReadyToAdvance` `0x00289924` and `Camp_IsPreviewReady` `0x0025A2BC`) in exact short-circuit order; if either returns `0`, returns `0u` without touching `*captured_work_out` or the workspace.
   - Reads the singleton slot `0x0044E300` (`camp::g_TitleMainWork`), publishes `*captured_work_out = work` (so the caller continuation preserves the exact post-gate `r4` pointer even under external slot mutation), and increments `work->field_64 += 1.0f`.
   - Queries `UiInput_Trigger` (`0x002B902C`) for logical IDs `{5, 0xE}` (decrement `work->field_08`) and `{6, 0xF}` (increment `work->field_08`) with short-circuit semantics.
   - Normalizes `work->field_08` via unsigned `NormalizeSignedRemainderByFour` (matching the ARM signed remainder of `provisional + 4` by 4 without calling `__aeabi_idivmod`), compares against `work->field_0c`, and if changed calls `Script_RequestEvent(0x0100016C)` (`0x002B91C4`) before updating `work->field_0c = selection`.
   - Returns `1u` on ready.

2. **In-Place 54-Word Continuation Shim in `ui_func_001e989c` (`0x001E9D08..0x001E9DDC`):**
   - Replaces the exact 54 words (`216` bytes) of `0x001E9D08..0x001E9DDC` with a 15-word continuation shim padded with 39 `nop`s (`.word 0xe320f000`) so that `ui_func_001e989c` remains **3,924 bytes** and every instruction, jump-table entry, and literal pool word outside `0x001E9D08..0x001E9DDC` (`0..1132` prefix and `1348..3924` suffix) remains 100% byte-identical to `code.bin`:
     - Allocates an 8-byte aligned stack slot (`sub sp, sp, #8`), passes `r0 = sp` to `bl H1_TitleMain_UpdateNavigationSlice` (`R_ARM_CALL` at offset `1140` / `0x001E9D10`), tests `cmp r0, #0`, loads the captured pointer into `r0` (`ldr r0, [sp]`), restores `add sp, sp, #8`, and on `r0 == 0` branches via `beq 0x001EA62C` (`.word 0x0a000241`) with `r4`, `r8`, and `s17` completely unmodified.
     - On `r0 != 0`, sets `r4 = captured_work`, loads `r8 = 0x0044E300` from the inline literal at `0x001E9D3C`, sets `s17 = 1.0f` (`0x3f800000`), and branches to `0x001E9DE0` (`.word 0xea000029`).
   - Updated `config/functions.csv` row `0x001e989c` from `matching` to `non_matching` to keep the byte-matching ledger truthful.

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
- **Runtime Note on `Tbb_GetPayloadData` (`0x002C0E9C`):** During live GDB cave testing, patching `0x002C0E9C` directly with a branch exposed that `Tbb_GetDefaultTable18Payload` (`0x002C0E84`) falls through into `0x002C0E9C` with `r4` and `lr` still pushed on the stack (`src/ui/tbb_loader.cpp:76-85`), relying on `0x002C0E9C` not modifying `sp` before returning to `0x002C0E90` (`pop {r4, lr}`). The compiled `Tbb_GetPayloadData` pushes `{fp, lr}` on entry, which works for direct calls to `0x002C0E9C` (such as `0x001EA14C` in H1) but breaks the fallthrough caller `0x002C0E84` (used by `Camp_SetSlotMessage` at `0x0029F10C`). Therefore, live runtime patching of `0x002C0E9C` was omitted until `0x002C0E84` is reconstructed as an ordinary C++ call.

---

## 4. Original Dependencies Still Called & Untested States

- **Original dependencies still called by the integrated State-5 slice:**
  - `Script_IsReadyToAdvance` (`0x00289924`)
  - `Camp_IsPreviewReady` (`0x0025A2BC`) and its internal callee `0x002BF9F0`
  - `UiInput_Trigger` (`0x002B902C`)
  - `Script_RequestEvent` (`0x002B91C4`) for event `0x0100016C`
- **Original ARM blocks still active inside `ui_func_001e989c` (`0x001E989C`):**
  - Function prologue/dispatch (`0x001E989C..0x001E98F4`) and common tail (`0x001EA62C..0x001EA7F0`)
  - States `0, 1, 2, 3, 4` (`0x001E98F8..0x001E9D04`)
  - State 5 blend ramp, touch-region polling loop, fade/help-lookup tail, and confirmation dispatch (`0x001E9DE0..0x001EA1E8`)
  - States `6, 7, 8, 9, 10, 11, 12` (`0x001EA32C..0x001EA628`)
- **Untested / Excluded H1 Paths:**
  - New Game confirmation (State 6 / 12 -> `Script_StartNewGame` `0x0026FA94`), Load Game slot selection (States 7–8 -> `SaveLoad_BeginFromTitle` `0x0030A9A4`), and Add-On Content (States 11–12) remain intentionally unexecuted in Azahar per milestone safety rules.
  - Physical touch-screen coordinate injection in Azahar and full replacement of the remaining 12 states of `ui_func_001e989c` remain open for subsequent slices.

---

## 5. Artifact Hashes

| File | SHA-256 |
| --- | --- |
| `src/ui/ui_runtime2.cpp` | `7d0c4aa573a54e6862fafdb582aef750e27f476b90a09ebb6c9745fb458c1b3a` |
| `include/camp/title_flow.h` | `e099fa067c054bb59d00b30c8bd5eb88502a00869f0d92c38734e37978e61c1a` |
| `config/functions.csv` | `2729777ae50e16341186e341e715ba46f6d12da41dd419d46e16442c7854a757` |
| `tools/h1_menu_slice_integration_experiment.py` | `2afdc55375bce278de118c3bf3f3f249e10ae5349c2d86117c0d445f1296d3c9` |
| `tests/test_h1_menu_slice_integration_experiment.py` | `fe3f8c303c600b636a7b6603330ff43a4e77de5239b2940d18762a08f0c8f016` |
| `build/obj/armv6k/ui/ui_runtime2.o` | `f213661c320c7c39e27f8bea050f79e0313e8ff0fd8118fac5635ff1cde24ff1` |
| `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/differential-matrix/report.json` | `ff430feade8c0eb215b2a0e2f605a22371d21430141357a1285065684feb2c50` |
| `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/azahar-runtime/runtime-report.json` | `665dc7d4f35370063e26ee6a6e7e3f1f68ef7df50b6d8046e7687147ac2196e7` |
