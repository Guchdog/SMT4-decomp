# Independent review: corrected H2 RSP row selection

## Finding

**Accept the corrected run as bounded H2 runtime evidence for the scripted BGM, SE, and Voice Calc outcomes. Do not treat it as H2 closure or as evidence of physical controller delivery, input scheduling, or restart persistence.** The defect identified in the earlier run is fixed in the runner: each selected row is explicitly set through the original `UiListCursor_SetSelectedRow` routine at `0x0029EDFC`, and the expected `TitleConfigWork` field is asserted at each Calc frame. The captured original/patched states and action traces agree across all 29 scripted actions and 12 checkpoints.

## Evidence identity

I read the assigned task packet, repository instructions, H2 runtime evidence index, prior H2 composition review, final H2+H3 review, H2 milestone, runner source, and the three offline reports. The 11 packet input hashes were independently recomputed; all matched `task.json`.

| Evidence | Size | SHA-256 | Result |
|---|---:|---|---|
| Corrected autonomous runtime JSON | 93,086 bytes | `cb9c9e123dc4e56961dfe0997d2f671bb35a4254dd6c5018ceedb1d8705cfd4a` | Match |
| H2 differential report | 82,681 bytes | `111b454e4ad68867c9c05815371a8b24e8a9f27c08596ace6e29e804d1a3ea89` | Match |
| H2 caller report | 101,672 bytes | `1f231771662e7f2c3b86667c5dca1565e8d0fb770ae8d113d9239368f7687e57` | Match |
| H3 final-image caller report | 20,714 bytes | `ef83eb50372d02a5bf86bd71039b2758c0fd4466d39249bf5f634da8372e1cc1` | Match |

The corrected run binds the same staged private Azahar executable in both runs (SHA-256 `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`), the pinned original code identity (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`), and the final H2+H3 image (`81c1c6ae72d88b689cde3e9982439c8f8c4a6e8773887547f4cb85b86cd34a20`), IPS (`95846920df9ceb0e6395b6fb7e5358c99b83dd14e5861ffcfa80d8e64208eda5`), and CCI (`9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`). Staged executable and CCI paths and digests in the report are internally consistent. The three offline reports bind to the reviewed H2/H2+H3 image identities and report pass; this review did not rerun their suites.

The runtime report records distinct loopback ports 60940 and 60941, and host process IDs 22888 and 13500. Each recorded listener owner equals its staged process ID. I independently checked both PIDs, all `azahar` processes, and `netstat` for either port: both PIDs were not running, no Azahar process remained, and neither port had a TCP entry. `Get-NetTCPConnection` was denied by the environment, so listener teardown was checked with `netstat` instead.

The supplied save `E:\emulador3ds\sdds4game1.sav` is 151,088 bytes and hashes to the pinned `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. The raw run does not contain before/after save snapshots; the current bytes match the supplied expected hash, but this report cannot independently establish that the file was unchanged across execution. The pinned original `code.bin` is not present in the current game tree, so I could not recompute that source-file digest from the file itself; the CCI digest and the report/config pins were verified.

## Action and checkpoint review

The report contains 29 actions per side. I independently parsed the action records, normalized the recorded fields, and confirmed original/patched traces are equal. Every action’s selected row maps to the expected work offset, every observed value equals the action’s expected value, and each recorded setter event identifies function `0x0029EDFC`, the requested/selected row, and return PC `0x001EA928`.

| Setting | Row | Work offset | Actions | Verified behavior |
|---|---:|---:|---:|---|
| BGM | 0 | `+0x28` | 13 | Decrement, cancel response, minimum clamp, default reset, and value 7 case |
| SE | 1 | `+0x2C` | 1 | Explicitly selects row 1 and observes expected work value 7 |
| Voice | 2 | `+0x30` | 15 | Explicitly selects row 2, observes expected value 7, exercises increase through clamp at 10 and decrement back to 4 |

The action sequence also includes the final A confirmation in state 2. The 12 checkpoint pairs all pass their recorded comparisons: normalized `TitleConfigWork` equality and `g_ConfigBytes` equality. They cover initial entry; BGM decrement and cancel; re-entry; BGM minimum clamp and Y reset; BGM row check; SE row check; Voice row check and maximum clamp; Voice restoration; and A confirmation. Original and patched normalized work hashes and config bytes agree at each checkpoint.

The selected BGM/SE/Voice raw work values are encoded values. For example, the script’s `set_to_4` labels correspond to raw work value 7. The checks establish that the script observed the intended per-setting field, not that raw value 7 is a physical volume level of 4 without an independently validated UI/value mapping.

## Runner and execution scope

The runner sets `r0` to the `TitleConfigWork` cursor at `work+0xE8`, `r1` to the chosen row, and PC to the original `UiListCursor_SetSelectedRow` address `0x0029EDFC`. It executes until the Calc breakpoint and records the setter event. In `step_calc_with_query`, it then temporarily replaces the logical query at `0x002C1830` with a deterministic one-frame response stub, executes one Calc frame, restores the original bytes, and snapshots work/config. It checks the selected field against the per-action expected value after the frame. This is a controlled RSP-driven logical condition, not button delivery through Azahar’s physical-input path or its normal input manager and scheduler.

The run therefore repairs the earlier false SE/Voice row-selection labels and provides credible bounded evidence that the final image preserves the exercised Calc state transitions in the paired profiles. It does not establish physical button mapping, panel/input-manager index correspondence, counter refresh timing, real scheduler cadence, interactive appearance, or behavior under user input. Only one SE action is exercised; the BGM and Voice sequences include boundaries, while this run does not provide a comparable SE boundary sweep. The scripted confirmation and in-session config equality do not prove persistence after a real save/restart cycle.

The offline reports add bounded differential and caller-composition evidence, including H2 State-9/10 caller cases and the final H3 caller. Their HLEs and deterministic inputs remain part of their scope; neither offline evidence nor this RSP run establishes whole-game equivalence. The prior composition reviews correctly keep the H2 milestone open pending the remaining runtime/input/persistence criteria.

## Recommendation and next action

Accept this corrected RSP run as evidence specifically for the selected-row BGM/SE/Voice Calc fields and paired original/patched state equality. Preserve the distinctions above in milestone reporting. H2 should remain open until physical-input mapping/scheduling and the required persistence scenario are independently exercised and reviewed; do not infer those claims from this scripted run.

## Method and command outcomes

Read-only review. JSON/hash checks, source inspection, action/checkpoint parsing, process/PID inspection, `netstat` listener inspection, and save hashing completed successfully. No build, test, debugger, emulator, network, profile modification, board edit, milestone edit, or runner edit was performed. The only unavailable check was `Get-NetTCPConnection`, which returned access denied; `netstat` provided the listener check. The original extracted `code.bin` was absent, limiting independent recomputation of that one input hash.

