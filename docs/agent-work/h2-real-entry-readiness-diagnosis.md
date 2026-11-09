# H2 real-input entry and readiness diagnosis (2026-11-09)

## Decision

The automated H2 scenario's entry shortcut was a real defect, but fixing it does
not close H2. Entering Audio Settings through the state-5 input path now works:
the title cursor moves from row 1 to row 2 with logical Down ID 6, A confirmation
runs the real dispatcher, `TitleConfig_Init` (`0x002F4CA0`) executes, and
`TitleConfig_Calc` (`0x001EA928`) reaches state 1 with option values 8/8/8.

After editing all three options to 7 and confirming with A, Calc reaches state 2
and `g_ConfigBytes` becomes `2d46462800000000`, but `TitleConfig_IsReady`
(`0x002FC0EC`) still returns 0 after **200** polls. During those polls
`0x00286928` is entered **200** times with `r2` increasing 0..199, returns **0**
every time, and the byte state at `[object+8]` remains **0**. The wait/script
state is not progressing. This is now the H2 blocker, not input entry.

## Evidence identities

| Item | Identity |
|---|---|
| Semantic checkout | `C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp` |
| Probe | `tools/h2_real_entry_probe.py`, SHA-256 `bdd322fe721af502e086b945c3247d23734e77606eafde56c1edeb9e28cc5ad4` |
| Report | `build/agent-work/H2-semantic/h2-real-entry-probe/run007/probe-report.json`, SHA-256 `a10f771207f4cead19adcccea8d4dda5204a67c65da829e4bfaeb2530fe2b3fd` |
| Private Azahar | `build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe`, SHA-256 `1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682` |
| Pinned original image | `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Pinned CCI | `E:/emulador3ds/00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci`, SHA-256 `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2` |
| Disposable stage root | `C:/h2rt-realentry-007` |

## Method

`tools/h2_real_entry_probe.py` launches the private loopback-bound Azahar with a
disposable profile, attaches through GDB RSP, and enters Audio Settings without
writing `TitleMainWork` state or selection. It temporarily hooks the documented
logical helpers for one frame:

- `UiInput_Trigger` (`0x002B902C`): `cmp r0,#6; moveq r0,#1; movne r0,#0; bx lr`
  to report one Down edge.
- `UiInput_Trigger2` (`0x002BFFBC`): `mov r0,#1; bx lr` to report an A edge.

The temporary bodies are restored after each tick. The probe single-steps over a
stopped breakpoint before re-arming the same address; without that step,
re-adding a breakpoint at the current PC immediately re-triggers and produces
false "ticks" (this was observed during development and is why earlier
cursor-down attempts showed no movement).

The probe then edits rows 0/1/2 through the existing `step_calc_with_query`
harness, confirms with A (`control_id=0`, `mode=1`), and interleaves
`TitleConfig_IsReady` polls with `0x00286928` entry/return observations.

## Observed sequence

| Step | Observation |
|---|---|
| Title state 5 entry | `TitleMainWork = 0x086E4700`, state `5`, selected row `1`, `flag_63 = 0` |
| Real Down tick | row changes `1 -> 2`; PC trace shows `0x001E9D08 -> 0x001E9D0C -> 0x001E9D1C -> 0x001E9D48(r0=5) -> 0x001E9D78(r0=0) -> 0x001EA15C` |
| Real A confirm | PC `0x002F4CA0` (`TitleConfig_Init`), title state `9` |
| First Calc entry | `TitleConfigWork = 0x086E4700`, state `0`, values `8/8/8`; after 9 entries state `1` |
| Edit rows | `7/8/8`, then `7/7/8`, then `7/7/7`; `g_ConfigBytes` follows to `2d46462800000000` |
| A confirm | Calc state `2`, values `7/7/7`, title state `10` |
| 200 readiness polls | every `ready_return = 0`, `work_state = 2` |
| 200 helper hits | `r0 = 0x086E5D80`, `r2 = 0..199`, `return = 0`, `[r0+8]` word `0x00010000` |

The helper object differs from the historical trace (`0x086E5700`) and the
historical trace reported a helper return of 1 at `r2 = 23`. The current
real-entry run does not reproduce that return.

## Interpretation

The typed `0x00286928` body (`src/engine/leaf_batch45_a.cpp`, current production)
shows the relevant path:

- `incoming_r2 != 0` reads `state = object[8]`.
- With `state == 0`, it runs the selector path, calls
  `engine_func_0028e974(object, raw_r0, raw_r1, selector, 0x1a, 1, 0)`, and
  returns 0.
- With `state == 3` or `state == 0`, it returns 0.
- The return-1 branch (`engine_func_002c1f28() != 0 && camp_func_002b89a0() != 0`)
  belongs to the `incoming_r2 == 0` path.

In the observed run `[object+8]` is 0 for all 200 calls, so the state-0 path
repeats and the script/ComWin object never advances. The remaining question is
what advances `object[8]`: the script engine step at `0x0028E974`, a draw/update
callback, or a task-scheduling event that the automated scenario does not
produce. The historical 0x086E5700 object may have been in a different script or
scene state, or a different path may have set the state.

## Second pass: callback return vs Calc state 2 (2026-11-09)

The follow-up runs refine the failure point.

- Confirming with a **real A edge** (`UiInput_Trigger2(0)` temporary stub,
  `r0==0`) instead of the logical-query stub still reaches Calc state 2 and
  `g_ConfigBytes = 2d46462800000000`, but readiness remains 0 for 200 polls
  (`run010`).
- The flat trace (`run008`) separates two helper callers by LR: the callback
  path (`lr=0x002211F0`, `r1=3`, `r2=0..39`, 40 calls) and another script loop
  (`lr=0x001DC800`, `r1=1`, 350 calls). It also shows `0x0028E974` called only
  twice, and readiness/dispatcher/handler/callback cycling continuously.
- Capturing returns on the callback path (`run011`) shows:
  - helper return 0 for `r2=0..38` and **1 at `r2=39`**;
  - callback return 1 exactly once (the `r2=39` cycle), 0 otherwise;
  - readiness return 0 in all 133 captured polls, including after the callback
    returned 1.
- Capturing dispatcher returns (`run009`) shows `0x0019DFBC` returning **1**
  every cycle while readiness returns 0.

The pinned ARM explains the consequence:

- `TitleConfig_Calc` state 2 at `0x001EAF98` calls `0x0019DFBC` and only acts
  when the result is **2** (`cmp r0,#2; bne common-return`). On 2 it calls
  `0x00297674`; result 0 takes the confirm path (`0x002BDAC0`, state 3,
  config byte +4 = 0), result 1 takes another path, and any other value leaves
  state 2 unchanged.
- `0x0019DFBC` returns 2 only when a script handler returns 0. It advances its
  counters and returns 1 when a handler returns 2, and loops when a handler
  returns 1.
- Handler 8 (`0x001A07CC`) returns 2 when its nested callback returns 0, and
  returns 1 (advancing the task index) when the callback returns nonzero.

Therefore the observed sequence is: callback eventually returns 1 (the ComWin
wait completed at `r2=39`), handler 8 returns 1, the dispatcher advances and
returns 1, but Calc state 2 does not handle 1. It stays in state 2 forever, so
the Calc task is never unregistered and `TitleConfig_IsReady` never returns 1.

This is a **script/state-machine contract mismatch in the scenario**, not an
input-entry failure. The next question is which handler/instruction is supposed
to return 0 (pending) after the wait completes, and what event or window state
makes it do so. The script task data (`/camp/config.bf`), task index/table and
nested IDs around the `r2=39` boundary are the next observation targets.

New evidence identities:

| Item | Identity |
|---|---|
| Real-A confirm report (`run010`) | `build/agent-work/H2-semantic/h2-real-entry-probe/run010/probe-report.json`, SHA-256 `d7aa7931b643ffc4695e6032abb4ae3f357618c052e338e50d298f855e0e71d6` |
| Callback return report (`run011`) | `build/agent-work/H2-semantic/h2-real-entry-probe/run011/probe-report.json`, SHA-256 `b3d24797391377a6defcc94d6261ba2b22ac4899998f15d16e155dda2010b441` |
| Flat trace report (`run008`) | `build/agent-work/H2-semantic/h2-real-entry-probe/run008/probe-report.json`, SHA-256 `e8296c1a8b3d113d7f6c66a132a82234e8453f9c7ccea79a7847f4da77251113` |
| Dispatcher return report (`run009`) | `build/agent-work/H2-semantic/h2-real-entry-probe/run009/probe-report.json`, SHA-256 `74cf61455336fcc8261d3c6023dace2e646b2aa0f147458c5d1207488d8db6a5` |

## Third pass: free-run and the sync-wait boundary (2026-11-09)

Two control runs test whether the stall is an artifact of GDB polling or of the
unthrottled runner config:

- `run015` resumes the guest for 5 seconds with **no breakpoints** after the A
  confirm, then interrupts. The stop is `PC=0x002A88A8`, `LR=0x001465A8`; the
  default object remains `[+8]=4`, the special object `[+8]=2`, and
  `TitleConfigWork[8]=2`. The config-work task is still registered.
- `run016` repeats the same free run with 60 fps/vsync and realtime audio
  enabled. The result is identical: same stop, same object states, same config
  state.
- `run017` extends the free run to 30 seconds. The stop moves to
  `PC=0x00153930`, `LR=0x002A4D9C`, but the objects remain 4/2 and the config
  state remains 2. The lock object at `0x00431C40` reads
  `0xFFFFFFFF / 0x1FF82000 / 1` with byte `+0x76 = 2`, the same raw signature
  documented for the earlier startup sync waits.

This rules out GDB polling, frame pacing, and the realtime-audio setting as the
cause. The title-config thread is parked in the same family of guest
synchronization waits (`SVC #0x22` arbitration / `SendSyncRequest` paths) that
blocked the earlier startup captures. The first ComWin wait does complete (the
callback returns 1 at `r2=39`), but the next wait leaves the default object at
state 4 and never observes the reset to 0. The remaining blocker is therefore a
guest/service synchronization lifecycle question, not a missing C++ slice or an
input-entry shortcut.

New evidence identities:

| Item | Identity |
|---|---|
| 5-second free run (`run015`) | `build/agent-work/H2-semantic/h2-real-entry-probe/run015/probe-report.json` |
| Throttled + realtime free run (`run016`) | `build/agent-work/H2-semantic/h2-real-entry-probe/run016/probe-report.json`, SHA-256 `0a03c86a2bf5c5dcb8bdbe539af7ecf1df796eb06e479f4d8fa7b477ce7fe82c` |
| 30-second free run (`run017`) | `build/agent-work/H2-semantic/h2-real-entry-probe/run017/probe-report.json`, SHA-256 `bb85a53d0779c07d32395fb48de88bb8e2fe84ec91b3525ed959073b08a74f8a` |

## Next experiments

1. Treat the sync wait as the primary blocker. Identify the thread/service that
   owns `0x00431C40` at the `0x002A88A8` / `0x00153930` stops, and which event or
   service callback releases it. The raw signature and caller paths are the same
   family already documented in the startup captures; do not repeat a generic
   startup timeout.
2. Find the writer that resets `default_object + 8` from 4 to 0. The first wait
   (selector 6, nested 33) completes and leaves the default object at 4; the
   second wait (selector 11, nested 5 at script index 14) checks
   `default_object[8]` and blocks while it is nonzero. A breakpoint on writes to
   `default_object + 8` during free run will identify the draw/update/task path
   that should perform the reset.
3. Compare this object lifecycle with the manual run-005 flow, which reached the
   same menu and reportedly confirmed settings. Determine whether the manual
   flow produced the reset through a real audio/task callback or a longer idle
   period that the automated scenario does not reproduce.
4. Only after the sync/reset lifecycle is understood, repeat the paired
   original-versus-patched scenario and then same-session re-entry and restart.

## Limits

- One original-profile run; no patched comparison.
- The input edges are temporary guest stubs, not physical controller input and
  not a human recording.
- The readiness poll uses software breakpoints and single-step; scheduler timing
  is not claimed to be natural.
- No persistence or restart result is established.
- This report does not close H2 and does not promote any C++ candidate.
