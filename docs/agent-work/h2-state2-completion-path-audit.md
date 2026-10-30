# Independent audit: H2 State-2 completion path

## Finding

The preserved evidence shows `TitleConfigWork.state == 2` while `TitleConfig_IsReady` returned zero. Under the documented readiness contract, that means the task-activity lookup still reported the registered Calc task active. It does **not** reveal the script handler’s return value, prove that its instruction/counters were progressing, or show whether `TitleConfig_Secondary` ran. The State-2 report is right to keep H2 open and persistence unresolved.

The proposed next observation should capture the original dispatcher, actual indirect handler, downstream State-2 decision, Secondary callback, and task-activity lookup as they execute. It should preserve all original script results and state/config bytes, and stop at a fixed event/time bound. A repeated handler with no observed progress is evidence of no progress in that sample, not by itself proof that the game is stalled: the handler contract and expected wait conditions remain unknown.

## Evidence identity and method

All 17 input hashes in the prepared `001/task.json` were independently recomputed; none differed. The original code image is the pinned `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` (3,633,152 bytes). I disassembled the original ARM ranges directly from that file with Capstone. I also read the reviewed Calc and Secondary contracts, the script-step integration report and function record, the current RSP runner, the updated partial report, and the two assigned runtime logs. No build, test, emulator, debugger session, profile, or save access was performed.

The dispatcher integration is bounded offline evidence, not live script evidence. Its five original-versus-candidate Unicorn sequences used synthetic handlers/results; its own report explicitly leaves real script tables, callbacks, runtime scheduling, State-2 meanings, and persistence unvalidated. The separately reviewed Calc contract supports the static branch/memory map; the Secondary review accepts a cleanup/control-flow map but says when the scheduler invokes it remains unknown. These reviews do not promote a State-2 meaning such as “confirm,” “save,” or “commit.”

## Pinned original control flow

### Calc State 2 and script-step dispatcher

At `0x001EA940`, `TitleConfig_Calc` loads the state from `work+0x08` and dispatches state 2 to `0x001EAF98`. The pinned instructions there are:

1. Load `work+0x154` and call `script_vm_func_0019DFBC` (`0x0019DFBC`).
2. Compare its returned `r0` with 2. Any other result returns through the common `r0=0` epilogue without changing the Calc state word.
3. Only on return 2, call `script_vm_func_00297674` (`0x00297674`).
4. If that helper returns 1, write state 1 at `work+0x08`. If it returns 0, call `camp_func_002BDAC0(work+0x5C, 1, 0)`, store state 3 at `work+0x08`, and write byte 1 at `0x0044E0FC` (config block `+4`). Other helper values take the common return and leave the state word at 2.

The pinned `0x0019DFBC` body reads the script instruction index at `task+0x18`, the method-table pointer at `task+0xBC`, loads a halfword handler ID from `method_table + 4*instruction`, and loads the callback pointer from `0x0044DED0 + 4*handler_id`. It calls that callback with the same task pointer. Its observed result branches are:

- Handler result 0: clear `task+0xD0`; return 2 to Calc.
- Handler result 2: increment `task+0xCC` and `task+0xD0`; return 1 to Calc.
- Handler result 1: clear `task+0xD0` and dispatch again.
- Any other result: dispatch again without this dispatcher changing those counters; the handler may still mutate the record.

The function saves/restores `r4-r6` and its stack. Since Calc only proceeds on dispatcher result 2, a handler result 2 is **not** itself the State-2 exit condition: it yields dispatcher result 1 and the Calc callback returns with its state still 2. Likewise, handler result 0 is the dispatcher’s terminal return 2, after which the separate `0x00297674` result still decides between Calc states 1, 3, or remaining in 2.

`0x00297674` is only 20 bytes. Its pinned instructions load the word at literal address `0x0043E188`, dereference `+8`, load `+0x1C`, and return that value. The current contract does not establish what that field means or why its values 0/1 are selected by Calc. The separate dispatcher experiment tested synthetic callbacks; it cannot identify the live handler ID, real handler return, actual task fields, or the semantic meaning of this follow-up value.

### State 3/4, Secondary cleanup, and outer title readiness

State 3 at `0x001EAFEC` calls `0x002BF9F0(work+0x5C)`: zero returns with state 3 unchanged; nonzero sets state 4. State 4 at `0x001EB004` returns `-1`. The fact that state 4 returns `-1` does not by itself prove how the task scheduler interprets that return or when it invokes the second callback.

The initializer registers `TitleConfig_Calc` (`0x001EA928`) and `TitleConfig_Secondary` (`0x002CAEF0`) in the Calc task setup. Pinned Secondary instructions set `work+4` to 1; drain the counters at `+0x1A` and `+0x24` through calls to `0x002B9008`; conditionally release and clear pointers at `+0x154`, `+0x14C`, and `+0x150`; query `work+0` via `0x002BF41C`; conditionally call `0x002C45B8(task,0)`; then release and clear the global `g_TitleConfigWork` pointer. The reviewed contract supports this sequence, but not the scheduler timing, number of invocations, whether state-4 return triggers it, or whether each helper has the inferred lifecycle semantics. The RSP logs do not capture Secondary entry or cleanup.

`TitleConfig_IsReady` (`0x002FC0EC`) reads `g_TitleConfigWork` at `0x0044E2D0`. If null, it returns 1. Otherwise it passes `work+0` (`calc_task`) to `0x002BF41C`: a nonzero task-activity result is converted to ready result 0; zero is converted to ready result 1. The TitleMain state-10 caller at `0x001EA3C8` waits while this function returns 0 and calls `Title_ResetForBoot` at `0x001EA3D8` only on a nonzero result. This is an outer task-completion gate. It does not read the State-2 handler result or directly inspect the script task’s instruction/counter fields.

## What run-003 and run-005 preserve

The copied log hashes and sizes match the task packet:

| Runtime log | Bytes | SHA-256 | Complete RSP observations relevant here |
|---|---:|---|---|
| run-003 | 652,165 | `5b74f3c40e8285492e189d46bcbac75d58c3a543ecca52c71610ac31a52fd56d` | 39 complete reads of `TitleConfigWork+0x08`, each `2`; 39 complete `r0` (`p00`) replies from the readiness function, each `0`. There are 41 readiness-entry stop replies overall. The file ends mid-log-line during the final memory exchange, so the 40th poll’s return value is not fully preserved. |
| run-005 | 654,505 | `3951e2d66891305e0b7dfa89e11bde8e38c69f4f1b9a343d87d9ea3d34c02696` | 40 complete reads of `TitleConfigWork+0x08`, each `2`; 40 complete readiness `r0` (`p00`) replies, each `0`. The log ends with the complete GDB-stub socket error `recv failed : 10054` after the RSP continue. |

The runner source shows why these packets are readiness evidence: `wait_for_title_reset_after_confirm` sets a breakpoint at `TitleConfig_IsReady`, reads only `g_TitleConfigWork` and `work+0x08`, runs to the function’s return PC, then reads `r0`. The count of 41 readiness entries includes the earlier readiness wait in the cancel/re-entry sequence plus the post-confirm polling in the bounded runs. The persisted work-state samples prove that this field was 2 at those captured reads. The readiness returns, under the accepted function contract, prove that the queried Calc task still appeared active. Neither observation proves a dispatcher result, handler result, instruction-index/counter movement, callback scheduling, or Secondary cleanup.

The logs contain no recorded breakpoint/return at `0x0019DFBC`, `0x0019DFEC`, `0x001EAFA0`, `0x001EAFB0`, or `0x002CAEF0`; the runner does not set those breakpoints. Consequently, do not infer a script callback result from `TitleConfig_IsReady()==0`, or claim the script handler itself returned zero. The updated run report also notes that the original-side run failed before the runner wrote its paired JSON report and before launching the patched process; the live action/assertion trace is therefore not available as a standalone report.

## Close behavior and its limits

The runner’s `request_clean_window_close` enumerates visible top-level windows owned by the staged child PID. When given the RSP socket, it sends the continue packet `c`, posts `WM_CLOSE`, and waits up to 15 seconds. A timeout returns `clean_exit=false`. The enclosing execution `finally` then terminates only the staged process and uses a five-second wait followed by kill fallback if needed. In run-005 the GDB log records `c` at 43.116 seconds and the socket reset at 58.129 seconds, consistent with the reported 15-second timeout and subsequent process teardown. It does not record the Windows `PostMessageW` result or a clean Azahar exit. No `D` detach is present in this sequence, and no inference that detach would resume the guest is warranted. The report’s conclusion that shutdown was not clean and no restart snapshot exists is appropriately conservative.

## Recommended single bounded observation

Use one original-only run with the pinned original image and disposable task-local profile, after the existing offline gates. Drive the normal title and settings path through the game’s original title callback logic; do not reuse the current runner helper that writes `TitleMainWork.state`/flag to force re-entry. If scripted logical input is retained to reach A-confirm, confine it to the already documented input-query boundary. Once A-confirm is generated by original Calc, do not replace the script handler or `0x00297674` result, write `g_ConfigBytes`, alter `TitleConfigWork`/script state words, or access the user save/profile.

Install read-only RSP breakpoints at dispatcher entry `0x0019DFBC`, just before the handler `BLX` at `0x0019DFE8`, after the handler returns at `0x0019DFEC`, and at the State-2 return/decision sites `0x001EAFA0` and `0x001EAFB0`. For each real handler call, record call PC, task pointer, `task+0x18` instruction index, `task+0xBC` method table, resolved handler ID/target from `0x0044DED0`, handler `r0` on return, dispatcher `r0`, `task+0xCC/+0xD0`, and `TitleConfigWork.state`. Also observe Secondary entry/exit (`0x002CAEF0`/`0x002CAFC8`) and task activity at the ready helper call/return (`0x002FC104`/`0x002FC108`), including the actual `calc_task` argument and `0x002BF41C` result.

Bound the capture to the first 40 outer readiness checks or 128 actual handler returns, whichever occurs first, with a wall-clock packet timeout. Stop early only on an observed Calc state transition, cleared global/work pointer, or task-unregistered result. A changing instruction index/counters and observed handler returns would demonstrate script progress; repeated handler inputs/results with unchanged task fields would demonstrate no observed progress in that bounded sample, but should not be labeled a bug until the real handler’s wait contract is known. If a handler never returns, record the last entry and timeout separately. No clean shutdown or persistence claim is needed for this one observation; after capture, end only the disposable staged process through the supervisor and record whether it was terminated rather than cleanly closed.

## Handoff

- **Outcome:** ready for independent review as a static contract/path audit.
- **Changed file:** only `docs/agent-work/h2-state2-completion-path-audit.md`.
- **Evidence:** original ARM disassembly and packet/log hashes rechecked; RSP log observations are partial as detailed above. No compiled, differential rerun, caller rerun, or new runtime evidence was generated.
- **Limitations:** real script handler ID/return/side effects, state-2 follow-up field meaning, callback scheduling, Secondary timing, and task-state progress remain unobserved. Logs do not preserve the last run-003 readiness return or any dispatcher/handler trace.
- **Next action:** run the single bounded original-side RSP observation described above and retain the per-handler/task/readiness trace; keep H2 open until runtime input, completion, shutdown, and persistence criteria are independently supported.
