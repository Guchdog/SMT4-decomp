# H1 main-menu callback map — `0x001E989C`

Owner: `h1_menu_map`  
Task: `h1-menu-callback-map`  
Reference image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`  
Evidence class for this report: static source/image cross-check plus references to prior bounded synthetic ARM experiments. No emulator was accessed for this task.

## Bounded conclusion

The smallest useful state-machine slice to integrate next is **state 5's keyboard/controller selection reducer**, not the full `0x001E989C` callback:

- State-5 dispatch begins at `0x001E9D08`.
- The two readiness queries are at `0x001E9D0C..0x001E9D2C`.
- The existing reducer's core window is `0x001E9D48..0x001E9DE0`: logical direction queries, signed wrap, cache comparison, and event `0x0100016C` observation/call boundary.
- Resume the original callback at `0x001E9DE0`, before the timer/blend clamp. Touch polling starts later at `0x001E9E4C`; fade/transition and help presentation follow.

This is a **slice proposal**, not an approval to transplant the current experiment unchanged. The experiment's `gate_bits`, `trigger_bits`, and `NavigationEventObservation` are explicit test controls/observation hooks. A production version must call or retain the real readiness/input/event functions, preserve their order and ABI, and must not leave the event observer in the production path. The existing report only supports the reducer contract with its stated stubs and input domain.

## Entry contract and ABI observations

`titleMain_func_001eb02c` (`src/camp/title_flow.cpp`) allocates the `0xA0`-byte `TitleMainWork` at global slot `0x0044E300`, clears/initializes its fields, and registers `0x001E989C` as the calc callback. `include/camp/title_flow.h` records the `0xA0` layout and offsets. The callback's first instructions save `r4-r8,lr` and `d8-d9`, allocate `0x20` stack bytes, load address `0x0044E300`, and dereference it to obtain the work pointer. They do not consume the incoming `r0` before replacing it with the global lookup. The callback therefore uses the global singleton work pointer in its body; the callback-argument value itself remains uncharacterized by this static map. It returns through a common epilogue that restores the saved integer/VFP registers and returns zero in `r0`.

The state word is `TitleMainWork::state_9C` at `work+0x9C`. The callback compares it with `13`, then dispatches through the 13-target table beginning at `0x001E98C4`; out-of-range dispatch takes the default branch. `code.bin` starts at text virtual address `0x00100000`, so callback file offset is `0x000E989C`. A read-only check found its first instruction bytes (`f0 41 2d e9 ...`) and the state table at `0x001E98C4` equal the corresponding words in `src/ui/ui_runtime2.cpp`.

## State/call map

The state targets below are the original table entries, independently read from the pinned image. Labels describe the assembly flow and cross-checked `#if 0` draft; that draft is useful map material but is not compiled C++ evidence.

| State | Entry PC | Main behavior / key data | Important branch or next state |
|---:|---:|---|---|
| 0 | `0x001E98F8` | Loads title layout/TBB slot `0x3A`, caches four layout-node coordinate pairs in `work+0x40..0x5F`, resets fade state. | If `work+0x95 != 0`, set state 2; otherwise optional startup sound and increment to 1. |
| 1 | `0x001E9A10` | Updates the animation at `work+0x14`. | Wait while byte `work+0x17` is zero; otherwise increment state to 2. |
| 2 | `0x001E9A3C` | Requests title BGM/background, chooses initial slot (`work+8`, cached at `work+0xC`), initializes help text, registers four touch regions, requests `.bccam`, two `.bam` models and `.bcenv`. | Preview flag `work+0x60` and launch argument byte `work+0x95` affect initial selection/resources; then state 3. |
| 3 | `0x001E9B90` | Calls the load-status helper for the two `.bam` handles and tests the camera handle at `work+0x88`. | Branches among retry/advance paths based on those results. Preserve the original condition order and confirm the helper's busy/ready polarity before rewriting this state. |
| 4 | `0x001E9BC0` | Binds camera/projection; changes visibility/alpha and flags for handles at `work+0x8C/+0x90`; plays sound. | Increment to state 5. |
| 5 | `0x001E9D08` | Readiness gates, frame/timer and blend updates, keyboard/controller reducer, touch polling, transition fade callbacks, TBB help-string selection, confirmation, and option dispatch. | Selection is `work+8`; cached selection is `work+0xC`; selection-change event is `0x0100016C`, confirm event is `0x0100016D`. Cursor cases choose states 6, 7, 9, or 11. This is the active H1 slice; only a few internal windows have bounded experiments. |
| 6 | `0x001EA48C` | Writes state 12. | Immediate teardown/exit path on next callback. |
| 7 | `0x001EA32C` | If `work+0x7C` is clear, prepares transition and calls save/load entry. | State 8. |
| 8 | `0x001EA358` | Polls save/load busy and title-manager state. | On completion may set state 12, otherwise resets title to state 5. |
| 9 | `0x001EA398` | If `work+0x7C` is clear, prepares transition and calls `titleConfig_func_002f4ca0`. | State 10. |
| 10 | `0x001EA3C4` | Waits for title-config readiness. | On readiness, resets title to state 5. |
| 11 | `0x001EA478` | Waits for script readiness. | Set state 12. |
| 12 | `0x001EA494` | Waits for script, resets title VM, destroys the calc task, sets up the field, then branches on the cursor for New Game, Load/boot, or Add-On Content behavior. | Contains save/game/start/sequence calls. This map does not authorize exercising those routes. |

The state-5 label “previous/next” is based on static data flow at these call sites: IDs `5` and `0xE` decrement; IDs `6` and `0xF` increment, with each pair short-circuited. The constructor normally selects index 1 because it sets `work+0x60=1`; a nonzero argument byte at `work+0x95` changes the state-2 selection to 3. Four touch registrations and the TBB payload stride support the normal menu index domain `{0,1,2,3}`. They do not prove how physical devices map to logical IDs.

## State-5 call/data-flow map

1. At `0x001E9D0C`, `Script_IsReadyToAdvance` (`0x00289924`) gates the update. A false result skips the preview gate and input polling. `Camp_IsPreviewReady` (`0x0025A2BC`) is then checked; false also skips input polling. The callback already increments `work+0x64` before this gate window, so a whole-state integration must preserve its timing.
2. From `0x001E9D48`, `UiInput_Trigger` (`0x002B902C`) is called for IDs 5, `0xE`, 6, and `0xF`. First result wins within each previous/next pair. Both direction pairs may run in one update; previous runs before next.
3. `0x001E9DAC..0x001E9DC0` normalizes the provisional cursor using signed remainder-by-four logic. For valid cursor values it wraps 0→3 and 3→0. For arbitrary corrupt values it does **not** guarantee a general clamp to `[0,3]`.
4. `0x001E9DC4..0x001E9DDC` compares `work+8` to `work+0xC`. Only a changed selection requests event `0x0100016C`; the event boundary precedes updating the cached value. The interior queue effect of `UiEvent_Request` (`0x002B91C4`) is outside the current experiment.
5. Frame/blend work at `0x001E9DE0..0x001E9E48` uses VFP operations on `work+0x64/+0x68`. Touch polling at `0x001E9E4C..0x001E9EB8` can overwrite the cursor and set confirmation byte `work+0x63`. This explains why the proposed key-selection slice must stop before `0x001E9DE0` and why it cannot stand in for the whole state-5 update.
6. The later transition path at `0x001E9F4C..0x001EA128` reads/writes `work+0x94/+0x96/+0x98`, follows handles and child/model pointers from `work+0x8C/+0x90`, uses VFP state, and calls readiness/fade functions. Conditional `BLX` callbacks occur through nested object callback slots inside the two gate bodies. The H1 track contract at `0x001EA0CC`/`0x001EA0DC` requires actual slot and source-pointer observation; serialized CANM categories or synthetic stubs cannot identify a live target.
7. At `0x001EA12C..0x001EA15C`, the callback uses the real TBB getter route to select a help string at payload offset `0x16 + 0x56 * work[+8]`, then prepares `Camp_SetSlotMessage` (`0x0029F10C`) arguments. Existing caller-window evidence stops before that callee: it does not prove renderer side effects or visible UI by itself.
8. Confirmation is checked after help selection: touch flag `work+0x63` or `UiMenu_CheckCursorSound`/`UiInput_Trigger2(0)` (`0x002BFFBC`) can allow dispatch. Successful confirmation requests `0x0100016D`, then cursor values select route states. The option handlers are not part of the navigation-only proposal.

## Proposed integration boundary and validation contract

**Candidate boundary:** preserve the surrounding original state-5 entry and downstream callback. Replace only the direction/cursor/cache reducer contract represented by `0x001E9D48..0x001E9DE0`, after preserving the preceding readiness/timer work and returning before original blend/touch processing. Keep the real `UiInput_Trigger` and event request behavior in the integrated caller. Do not replace touch, fade callbacks, help TBB reads, or dispatch as a side effect of this slice.

Before promotion, the integrator should define the actual caller/C++ adapter boundary and run a same-state comparison with valid initial work fields. Required cases:

- readiness gate matrix: script false (preview helper not called), preview false (no input calls), both true;
- all 16 logical trigger-response masks for IDs `{5,0xE,6,0xF}` and explicit order/short-circuit checks;
- cursor/cache boundaries 0 and 3 in both directions, unchanged/net-zero moves, and changed-vs-unchanged cache;
- observe `work+8`, `work+0xC`, helper call sequence, event ID `0x0100016C`, event arguments at call time, return register(s), preserved callee-saved integer/VFP state and untouched neighboring bytes;
- negative controls: raw unsigned `cursor % 4` instead of original signed normalization for `-1`, reversed alias priority, wrong cursor/cache offset, or emitting the event when the final cursor equals the cache. At least one wrong behavior must be rejected for the intended reason.

The current family harness already exercises false/false/true readiness combinations, eleven named reducer boundaries, and 256 valid cursor/cache/trigger-mask combinations against original ARM, with a wrong-normalization control. However, it supplies gate and trigger responses and a recording event stub. That is **synthetic bounded differential evidence** for reducer semantics, not an integrated callback comparison. The prior Azahar keyboard probe reports that the menu moves and help text updates for one configured profile, but it did not trace which logical trigger fired and is not this reducer's compiled-C++ runtime validation. Keep those evidence levels separate.

## Dependencies and unresolved paths

- Global work pointer `0x0044E300`; exact `TitleMainWork` offsets declared in `include/camp/title_flow.h`.
- `Script_IsReadyToAdvance` `0x00289924`, `Camp_IsPreviewReady` `0x0025A2BC`, `UiInput_Trigger` `0x002B902C`, event request `0x002B91C4`.
- Downstream state-5 regions: VFP timer/blend, touch helper `0x0029D8FC`, handles/child/model object graph, fade/readiness functions, callbacks whose live pointer targets are unresolved, TBB manager and real `TitleTable.tbb`, and `Camp_SetSlotMessage` `0x0029F10C`.
- Confirm/dispatch dependencies: cursor-sound/UI-input checks, event `0x0100016D`, per-option states and destinations.
- No runtime pointer/target identity is established for either transition gate by this report. No renderer contract, visible-layout differential, full menu callback C++ replacement, or original-vs-patched H1 scenario is established.

## Provenance checks and limits

Read-only check performed for this task:

- `extracted/exefs/code.bin` size: `3,633,152` bytes; SHA-256 equals configured reference `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- `src/ui/ui_runtime2.cpp` SHA-256: `cb40fc26bee67596a289da5bec6223585afce51e993d93289fe347db058f5215`.
- `include/camp/title_flow.h` SHA-256: `92bc500bac3dd82167f5ed29e14e13d929531898f14fe378077f2931dfc9b7e7`.
- `docs/agent-work/h1-track-contract.md` SHA-256: `73c72706300966b439aea19dc56b127999d3242dd6c0d91a7bcd01cf248af6dc`.
- `title_callback_composition_audit.md` SHA-256: `a5c6b1c9c2ed487d00f1838597383996153c47c28f27b43a51befdaf8eb7c1d3`.
- `title_transition_mutator_experiment.md` SHA-256: `9cb03fb2fb2905c9d062c5fb9fa35a6e5fee4fb196acbe80c94977908f537500`.
- Command exits: PowerShell `Get-FileHash`/read-only byte-offset check exited 0. No compiler, tests, emulator, or debugger command was run for this mapping task.

The callback source's readable body remains under `#if 0`, and `ui_func_001e989c` still compiles as inline ARM words. This document maps the original and proposes a small path toward C++; it does not itself reconstruct or validate C++ behavior.

## Structured handoff

- **Task/owner:** `h1-menu-callback-map` / `h1_menu_map`
- **Outcome:** `ready_for_review`
- **Changed file:** `docs/agent-work/h1-menu-callback-map.md` (SHA-256 recorded in the task's private handoff JSON)
- **Commands:** read-only pinned-image byte/hash verification; exit 0. No compile/test/runtime commands run.
- **Evidence:** compiled `not_run`; ARM differential `partial` (references existing reducer evidence, not newly run); caller `partial` (static callback/state map and prior synthetic windows only); runtime `not_run` by this task.
- **Limitations:** full callback remains ARM; candidate helper stubs external inputs/event behavior; touch/fade/presentation/dispatch are separate; live transition callback targets unresolved; no renderer/runtime result.
- **Next action:** independent review of this map and its slice boundary, then an integrator-owned task to make the reducer call real helpers and compare the same caller window while preserving all surrounding ARM behavior.
