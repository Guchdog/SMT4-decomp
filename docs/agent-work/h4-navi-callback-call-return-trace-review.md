# H4 Navi callback call/return trace review

## Review result

All 19 frozen input hashes in review packet `001/task.json` match. I independently inspected the pinned runner, integration report/handoff, run-004 paired JSON, offline reports and prior callback contract reviews. The run-004 evidence supports the bounded report: one callback invocation in each process follows the same six-stop path on thread 1, reaches the callback LR `0x001A95E8`, and has `r0=0` at that return boundary. This is a checkpoint observation, not a general return contract or H4 interaction result.

The pinned runner SHA-256 is `55186f05971cabf5abeb6d3c1a5d2ef6c518799785503462e305c672e99a8cbb`. Run-004 `report.json`, `original.json`, and `patched.json` SHA-256 values are respectively `14f6cd141f0401eba53a57b8df0600dc7981570aa9e4edc0a57323830af6b9dc`, `9bf8b03bab8cb7f69f35cd459f4226403cf63782ed6ddba4055a07e510464ff0`, and `47a1062fba05254d08c54c391fc100676e169230c11a701e84b130a4eb23ad18`.

## Runner and trace mechanics

The opt-in `--navi-callback-return-trace` is rejected unless `--field-probe-address` includes `0x00399D60`. At the callback entry probe, the runner captures registers and snapshots, clears the entry breakpoint, then arms nine software breakpoints at the two query return sites, branch points, two later helper returns, three alternate-branch sites, and the caller LR. It continues one stop at a time, records the stop reply's `thread:` field, registers `r0-r4`, LR, SP, and validated snapshots, and clears each reached breakpoint. The `finally` loop attempts to clear every still-armed breakpoint and reports cleanup errors.

The trace stops on the first reached `0x001A95E8`, on an unexpected stop, an RSP timeout, or after 24 stop events. The target callback has no known internal bound; `target_loop_has_internal_bound=false` is accurately recorded. `continue_and_read_pc` relies on the RSP socket timeout and interrupts execution on timeout; the run uses a 60-second socket timeout for the active session. Both run-004 traces have six events, no timeout event, `callback_return_observed`, `breakpoints_removed=true`, and no breakpoint-removal errors. The runner records GDB thread ID `1` at entry and all six stops in each run. It records equality with the entry thread but does not filter a different thread; in these captures every event is on the same recorded thread.

The trace path performs register and memory reads and software-breakpoint/control operations. Its callback-specific code does not call guest register-write or memory-write helpers. This observation applies to the trace probe, not the runner's full checkpoint setup, which uses the controlled load seam described in the integration report.

The snapshot helper validates each dynamic span numerically (`pointer >= 0x10000` and `pointer + size <= 0xFFFFF000`) before issuing an RSP memory read, and records invalid ranges/read errors. Run-004 snapshots validate the callback object span of 0x60 bytes, host fields at `host+0x30/+0x38`, the eight-byte pair at `host+0xB64`, seven input-object bytes at `*[0x0043DA2C]+0x4B8`, and the view span of 0x170 bytes. Successful range checks and RSP reads establish accessibility only for those sampled addresses.

## Run-004 evidence

Original and patched reports both reach the field manager for 250 recorded ticks. The callback entry has `r0=0x086EB3C0`, `r1=0`, `r2=0x00399D60`, `r3=0`, `lr=0x001A95E8`; the host slot is `0x086EB380` and entry object is `host+0x40`. Each trace records these stops, in order, with thread ID 1:

```text
0x00399D88 → 0x00399D98 → 0x00399DAC → 0x00399DB8 → 0x00399DCC → 0x001A95E8
```

The first two sites show query results `r0=1`. Entry snapshots show byte `[object+0x0C]=1` and word `[object+0x10]=0`; the stop at `0x00399DAC` follows the conditional `0x0039C944` call and reports its residual `r0=0`. The trace reaches `0x00399DB8` after `0x00220888`, then sees byte `+0x0C` still 1 and continues to `0x0039AF30`; the `0x00399DCC` stop records `r0=0` after that helper. At the caller LR before its next instruction executes, `r0=0` in both profiles. This establishes the sequence and residuals for this invocation, not the helpers' general contracts.

At all six recorded snapshots, the callback object's +0x0C byte remains 1 and +0x10 word remains zero. The seven bytes at the validated input-object span are zero. The view pointer and 0x170-byte view content match across profiles at each event, and the object prefix is equal across profiles at each stop. These are observations at sampled stops; they do not establish that no other unobserved state changed between stops or explain view semantics.

Staged original and patched saves are each unchanged within their own run (151,088 bytes; SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`). The non-mod profile manifest is unchanged within each process. These are not claims that the two profile baselines are identical. The runner's `save_snapshot(user)` checks the staged profile save, not the separate source-save path.

## Diagnostic mismatch and offline gates

The report discloses the earlier run-003 difference, and the available run-003 raw JSON confirms it: `post_confirm_events_equal=false`; the save-status-setter `r2` was `0x338` in original and `0x337` in patched; the first callback-stop view bytes at offsets `0x164..0x166` were `80 4a 76` versus `00 64 71`. In run-004, the paired comparison reports equal post-confirm events, and callback-stop view snapshots match. The final pair therefore does not erase the prior timing-sensitive difference. Run-003 raw files are not declared input pins in this review packet, so that independent check is contextual rather than frozen provenance.

The packet-pinned offline reports hash-match their declared inputs: H3 title diff has four cases; H3 placement passed and records final image SHA-256 `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8`; H3 caller composition passed; H4 reader passed 119 cases; H4 camera passed six cases. These are scoped offline gates, not evidence of full H4 behavior or whole-game equivalence.

## Corrections and limits

The integration report states that the external source save remained at the known SHA-256. The pinned run-004 raw JSON contains only staged-profile save snapshots; it does not contain the source-save audit output. The integrator handoff mentions a `source save audit` check but supplies descriptive labels rather than an executable command or hashed audit report. The runner itself snapshots staged profile paths and does not read the separate source-save path. I did not access that source save. The exact external source-save unchanged claim is therefore not independently verifiable from this frozen packet; pin a separate audit artifact if that provenance is required. Likewise, the process/port cleanup statement is in the integration record rather than raw JSON; the runner has `finally` termination/wait/kill cleanup, but the packet does not include a process/port evidence artifact.

No axis override or physical input is injected by this run, and no evidence establishes logical input semantics, player movement or ownership, view effect, H4 target interaction, zone transition, or whole-game equivalence. No candidate or production replacement is claimed. The bounded runtime result is acceptable as reported with the source-save and process/port evidence provenance caveats above.

## Run-002 provenance refresh

All 20 declared run-002 input hashes match. The new `runtime-post-run-audit.json` is pinned at SHA-256 `72cb084da2db9b28f59c6fe36718e894f911d0e63815ea4136d4b683ab28e980`; its audit timestamp is `2026-10-28T12:38:31.820863+00:00`. Its recorded run-004 artifact hashes match the original, patched and report files already reviewed. The unchanged run-004 evidence still supports the six-stop callback path, the observed return `r0=0`, and per-run staged-save/profile integrity.

The external source-save integrity claim is now **partly evidenced, not fully independently verified**. The hashed audit records a pre-run SHA-256 and explicitly says it was observed before run 004, but the contemporaneous console output was not persisted. It also records the post-run SHA-256 as the same value. This provides a pinned post-run sample and a durable record of the prior observation, but the pre-run read's contemporaneous provenance cannot be independently checked from the packet. The runner's `save_snapshot(user)` reads only staged profile saves, so it does not itself access the external source-save path. I did not read that file.

Process and port status are now pinned as assertions at that audit time: the audit records an empty Azahar process list and `listener_absent=true` for `127.0.0.1:54342` and `:54343`. The JSON reports `connect_ex=10035` for each port; on Windows this is `WSAEWOULDBLOCK`, which can denote a nonblocking connection still in progress. Since the audit artifact does not include the probe method or any completion/error check, the empty process-list claim is directly recorded, while the port-absence booleans are time-stamped assertions whose derivation is not independently inspectable from this artifact alone. This qualifies the prior review's port-evidence caveat without changing the callback trace result.

The revised integration report now discloses the pre-run-output limitation and links the audit. No runtime, build, test, or save access was performed for this refresh.

## Run-003 final artifact check

All 23 declared run-003 input hashes match. The refreshed audit artifact at `build/agent-work/H4-semantic/h4-navi-callback-call-return-trace/002/checks/runtime-post-run-audit.json` is pinned at SHA-256 `e3ca024fb4206910287d32577b62fa259604a2259a2e4e228b638b734ba1620d`; its timestamp is `2026-10-28T12:41:24.707289+00:00`. Its embedded hashes still match the reviewed run-004 report and paired raw JSON. No run-004 runtime conclusions changed.

The process/port evidence is now adequate for absence at that audit timestamp. The artifact records an empty Azahar process list; blocking TCP `connect_ex` to both loopback ports returned the expected closed-port error `10061`; and `netstat -ano` exited 0 with no relevant or listener lines. These are time-bounded post-run checks, not claims about later process state.

The external source-save claim remains **partly evidenced**. The pinned audit records the pre-run SHA-256 as observed before run 004 and explicitly states the original console output was not persisted contemporaneously; its post-run hash matches that recorded value. The post-run value and the assertion about the earlier read are durable, but the earlier read's contemporaneous evidence is unavailable for independent verification. The integration report states this caveat accurately. The runtime runner uses only staged profile saves, and I did not read the external source save.

