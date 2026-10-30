# Offline H2 caller-composition plan: State 9 to reset

## Proposed first vertical slice

Build a private Unicorn runner that executes the pinned original `ui_func_001e989c` State 9/10 caller on both sides. The original side runs the original `0x002F4CA0` initializer; the patched side replaces only that initializer entry with the compiled `candidate_002f4ca0`. Both sides otherwise use the same pinned `code.bin`, title-caller bytes, helper HLE model, initialized memory, registers, and task-activity schedule. This isolates whether the candidate initializer composes with the real caller's handoff, readiness polling, and reset path.

Do not invoke the registered `TitleConfig_Calc` entry in this slice. The objective is to prove that the initializer forwards and stores the expected Calc task registration, and that the title's real state-10 readiness logic consumes that task handle before reset. The task factory and active-task lookup remain explicit HLE boundaries; they do not implement a scheduler or Calc execution.

## Source and reusable harness material

- Pinned original image: `extracted/exefs/code.bin`, expected SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- State machine/caller source: `src/ui/ui_runtime2.cpp`, `ui_func_001e989c` around State 9 at `0x001EA398` and State 10 at `0x001EA3C4`; `Title_ResetForBoot` begins at `0x001EA3D8` and sets State 5 at `0x001EA470`. The pinned code image is the executed caller for both comparison sides.
- Initializer source/candidate: `src/camp/title_flow.cpp` original wrapper at `0x002F4CA0`; `experiments/semantic_equivalence/h2_init_orchestration_candidate.cpp` patched replacement.
- Registered Calc callback: original ARM at `src/engine/leaf_batch46_b.cpp` (`0x001EA928`, 1796 bytes). Readiness helper: `src/engine/leaf_batch26_b.cpp` (`0x002FC0EC`, 52 bytes), which calls task-active helper `0x002BF41C` using `TitleConfigWork+0`.
- Use the H1 machine layout and capture conventions in `tools/h1_menu_slice_integration_experiment.py` and `tools/h1_navigation_adapter_experiment.py`, plus the helper-call HLE, register seeding, poisoned workspace, and trace projection patterns in `tools/h2_init_orchestration_experiment.py`. The existing H1 execution wrapper `run_full_callback_state5()` is not the entry point for this case: it forces State 5 and stops at State-5 boundaries. Do not edit the shared H1 runner; add a task-local H2 caller-composition runner.

## Machine and fixture layout

Use separate original/patched Unicorn machines mapped from the same verified image and equivalent fresh memory snapshots. Preserve H1's ARM11MPCore/VFP setup and 8-byte-aligned stack conventions. One concrete private layout, compatible with the H1 injection map, is:

| Object | Address / size | Initialization |
|---|---:|---|
| `TitleMainWork` | `DATA+0x100`, `0xA0` bytes | Poison then set `state_9C(+0x9C)=9`, `flag_7c(+0x7C)=0`, and `resource_88(+0x88)` to a harmless recorded token; set remaining reset fields to distinct sentinels. Its size is confirmed by `include/camp/title_flow.h` static assert. |
| Alternate H1 work buffer | `DATA+0x300`, `0xA0` bytes | Preserve H1 layout if its adapter machine is reused; guard against aliasing with the H2 work object. |
| `TitleConfigWork` arena | `DATA+0x2000`, `0x158` bytes | Allocator HLE returns this fixed address and fills it with deterministic poison, matching the current init differential's isolation purpose. It must not overlap the title work, config bytes, stack, HLE tables, or injected code. |
| HLE table/coordinate data | `DATA+0x800` and distinct reserved pages | Seed only the minimal data required by existing original helper bodies, such as the sprite setup table used by `0x002BDAC0`. |
| `g_ConfigBytes` | `0x0044E0F8`, 8 bytes | Seed baseline `3250503000000000`; a second case may use `0113273B4D5F7183`. |
| `g_TitleConfigWork` | `0x0044E2D0` | Start with a non-pointer poison value; require initializer publication of the private config-work pointer. |
| `g_TitleMainWork` | `0x0044E300` | Point to the private `TitleMainWork`. |
| Code/injection/stack | H1 `TEXT`, `INJECT`, `STACK` conventions | Reserve a non-overlapping injection slot (for example `INJECT+0x4000`) for the compiled initializer; keep `LR` return sentinel and poisoned stack scratch away from staged objects. |

The callback starts at `0x001E989C` with `r0` set to a harmless callback-argument sentinel, `LR` set to a return sentinel, and identical initialized GPR/VFP state on both sides. Run the full callback with `state_9C=9`; stop only when it returns to the sentinel. Subsequent ticks reuse that side's memory and machine: invoke the same callback from `0x001E989C` with `state_9C=10`, once while the task is active and again once inactive. Do not start directly inside a case body for the acceptance run; the full entry exercises dispatch and epilogue too.

## Patch and HLE boundaries

For the patched machine only, compile/extract the initializer candidate into the private injection slot and replace `0x002F4CA0` in that machine's code copy with a branch to it. Validate source/reference hashes and supported relocations exactly as the current init runner does. No other code address is replaced.

Execute the original caller, original readiness function, wrapper functions, mapping helpers, pair helpers, and initializer unchanged on the original side. Use matched, observable HLEs on both sides for engine effects outside this slice:

- `0x002A7604` `Script_PrepareTransition`: capture caller PC, `r0-r3`, stack args, and return without scripting effects.
- `0x002C4B84` allocator: capture size/alignment arguments, return the fixed `TitleConfigWork` arena, and poison-fill it.
- `0x00118488` process factory, reached through original `AsdTask_CreateCalc`/`AsdTask_CreateDraw` wrappers: capture tuple/register/stack arguments; return deterministic Calc and Draw task tokens. Assert the Calc tuple contains primary callback `0x001EA928`, secondary callback `0x002CAEF0`, and the allocated work context; assert the Draw tuple contains callback `0x002CAFD0` and its recorded Calc-task handle. This demonstrates registration forwarding, not framework scheduling.
- Preserve the current init runner's explicit HLE boundaries for sprite setup `0x002BDB2C`, cursor setup `0x0029FAE8`, asynchronous table load `0x00297704`, opaque `0x002B8B78` call, and null/reset-mode call `0x0029F10C`. Retain original wrapper, group, animation, mapper, FillPair, and CopyPair bodies where the current init runner already executes them. Treat HLE names as labels only; compare observed addresses and arguments rather than inferring sound/resource/reset semantics.
- Leave the original `TitleConfig_IsReady` body at `0x002FC0EC` executing. Hook only its documented task-activity dependency `0x002BF41C`: require its input handle to equal the Calc token captured from the task-factory tuple, and return `1` (active) on the first State-10 tick, then `0` (inactive) on the next. This should make the real readiness function return `0` then `1` without fabricating readiness behavior in the caller.
- HLE the reset's opaque engine calls as traceable boundaries: `0x002B8B78` (message id argument), `0x002B88C4` (four region registrations; return four deterministic 16-bit handles), `0x00275E58` (cursor mode), `0x002A0C54` (resource string/mode), and `0x002A06DC` (resource handle/mode). Do not execute resource, input, message, or touch-manager internals. Return only values needed for the caller to proceed and state the exact stub effects; do not infer UI or persistence behavior.

## Expected case flow and controls

1. **Primary handoff/readiness/reset:** start in State 9 with `flag_7c=0`. Verify transition preparation precedes initializer entry; record both task registrations and the Calc callback tuple; verify `g_TitleConfigWork` points to the arena and `TitleMainWork.state_9C` becomes 10. On first State-10 tick, the readiness helper sees the captured Calc token as active; verify readiness returns false, State 10 remains, and none of the reset HLE calls occur. On the next tick, return inactive for that same token; verify readiness returns true, reset HLE calls occur in order, and the caller returns with State 5.
2. **State-9 gate control:** repeat with `flag_7c=1`; require no `Script_PrepareTransition`, initializer entry, allocation, or task registration, and require the title to remain State 9.
3. **Not-ready control:** run a State-10 tick with the active result and require no reset calls and no state change. This catches inverted readiness and premature reset.
4. **Registration negative control:** use a disposable wrong-callback initializer mutant (change the recorded primary Calc callback away from `0x001EA928`) and require the exact callback-tuple assertion to fail. Do not alter the production candidate to construct this control.
5. **Config cases:** run the baseline bytes and one all-distinct 8-byte config block through identical original/patched fixtures. This exercises the existing mapper/copy path while checking that the caller sequence is independent of accidental zero data; it does not validate mapper candidates or persistence.

## Comparison outputs

Compare exact ordered trace records by call-site PC, callee address, used `r0-r3`, consumed stack words, relevant VFP args, and modeled return. Specifically assert `Script_PrepareTransition → allocator → Calc factory tuple → Draw factory tuple → state 10 → activity query(active) → activity query(inactive) → reset helper calls` ordering, with the reset helper sequence and arguments checked against the State-10 call site.

Compare, at state-9 return, first pending State-10 return, and post-reset return:

- `TitleMainWork[0..0xA0)`, `TitleConfigWork[0..0x158)`, `g_TitleMainWork`, `g_TitleConfigWork`, and `g_ConfigBytes[0..8)`;
- task-token/callback registration records and task-active query handle/results;
- return value, PC/return sentinel, SP, callee-saved `r4-r11`, and `d8-d15`; compare only the ABI-observable register contract and ignore caller-saved scratch;
- HLE event order, expected reset field changes (`field_64/68`, touch handle slots, flags `+0x61/+0x84/+0x85/+0x96`, and state `+0x9C`), and exact changed-byte footprint in the two work objects.

Original and patched traces/state must match for each case, and each side must satisfy the explicit state/trace assertions above. Passing paired equality without the positive expectations is insufficient.

## Boundary and ownership

This slice does not run `TitleConfig_Calc` at `0x001EA928`, schedule either task, execute State-1 input/cursor logic, model touch/button sources, complete async resources, draw the menu, confirm or cancel settings, or claim save/persistence semantics. It does not establish whether the HLE task-active sequence corresponds to real scheduler lifecycle. Keep those as separate tasks after the current Calc arithmetic batch and input/cursor/service contracts are ready.

Expected owner: the H2 integrator should own the new task-local caller-composition runner and its compile/patch glue because it combines the existing H1 machine conventions with H2 initializer HLEs. An implementation worker can take the already reviewed initializer candidate and exact owned source/report files; an independent validator should review the candidate branch patch, HLE trace schema, and one caught registration mutant before accepting. Any later runtime owner needs a fresh assignment; this design performs no Azahar, RSP, profile/game I/O, or host-input activity.
