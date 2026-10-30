# H2 State-2 run-017 — independent runtime capture review

## Decision

**Accept run-017 as bounded original-only runtime evidence; keep H2 open.** The report shows the original title callbacks reaching Audio Settings and a real State-2 script-dispatch loop with handler entries/returns. It does not show State-2 completion, the nested callback behind the repeated top-level handler, a patched-side comparison, or persistence. The 180-second capture timed out after ten readiness checks. That is a bounded pending-callback observation, not evidence of a deadlock.

## Packet and provenance

I recomputed the run-017 task packet SHA-256 as `5c8bc300f0a75eb0ccc8355acd811189172eed6a0e36e7b84f56bbc1c3e69d4a`; the runtime report's `task_packet_sha256` matches. Every declared hash in the run-017 packet matched the current file (zero mismatches). The run report and `runner-console.log` are byte-identical at SHA-256 `9976f6f643dfb9ef08e084cd2d6a92bfebbb7e1826dde761a122810e6aade4a4`. That console file is a duplicate JSON record rather than a separate RSP transcript; chronology is available through the ordered arrays in the JSON, with no per-event timestamps.

The run-017 packet **does not pin** `tools/h2_state2_dispatch_trace.py`, and the runtime JSON has no runner-source SHA field. The review packet freezes the current runner at `fc642f6cef0613138785fcde97f2b2c36eefccf091df4ca3689fc8e3545185cb`; the runtime report contains fields consistent with that runner's dependency-package and disposable-fixture path, but this does not cryptographically prove those exact source bytes were used in run-017. The run report does pin the runtime package document (`bda8e1a43ac9e040e4a8165f1a9eec5a3656ff94d59d85cb50577959815428f9`) and its private executable identity. This runner-source gap limits exact reproducibility, not the observed values recorded in the report.

## Gates, listener, inputs, and cleanup

The recorded prelaunch gates all report passed: run-task input hashes, H2 differential, H2 caller composition, H3 final-image caller composition, and ARM interworking. I recomputed the three offline report hashes and inspected their pass fields; all three hashes match the runtime report's pins. The H2 differential has four retained source-identity warnings, so the gate result should be read with those warnings rather than as a claim that every source pin matched.

The run records one original-only launch using the pinned private executable (`8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`). Its staged executable has the same hash. `listener_verified` records `127.0.0.1:46797`, owner PID 20812 equal to child PID 20812, guest PID `b`, and the GDB-source SHA matching the delivery manifest. The manifest/source hash is `bb345fcaca1e09f41a5d5f6941a4eef5d98e0b0257b15aa98ce993c0a22025d6`; the source contains the loopback bind and no `INADDR_ANY` bind. Afterward the PID was absent and port 46797 had no listener.

The report lists 59 runtime assets. I independently hashed the actual staged asset files at the recorded app path: all 59 match their recorded source, expected, and staged SHA-256 values; the staged executable also matches. The report records supervisor termination, zero active breakpoints, staged-user removal, profile-seed stability, and a preserved stage-local Azahar log. The disposable `app/user` path is absent now; I did not inspect its contents.

The report records the game CCI before/after as `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`, unchanged. It records the supplied source save before/after as `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`, unchanged and not staged or loaded. I did **not** open, hash, or otherwise read that supplied source save. The report separately records a disposable fixture staged to the disposable profile and unchanged; during the required run-task input-hash audit I also SHA-256-read the packet-declared disposable fixture path. No installed profile or staged user files were opened by this review.

## Captured event sequence

Navigation records the normal title callbacks observing State 5 and selection 1 for the right-query, followed by the original A-confirm callback at selection 2. The report records `TitleConfig_Init` at `0x002F4CA0`, the Calc work pointer `0x086E4700`, and transition from Calc state 1 to state 2 after the logical query `(0,1)` was answered once. These are original-only observations with controlled logical-query responses; they do not establish physical host-input mapping or identical input scheduling across original and patched runs.

The report contains 12 top-level script-handler entries and 12 returns for one task pointer (`0x08C0AA80`) and method table (`0x086E5AD0`). For every entry the resolved table target, `r1_handler_target`, and actual guest entry PC agree:

| Entries | Instruction index / handler ID | Target and return | Counter snapshot at entry |
|---|---|---|---|
| 1 | 10 / 7 | `0x001A08A8`, return 1 | `task+0xCC/+0xD0 = 0/0` |
| 2 | 11 / 29 | `0x001C1D2C`, return 1 | `0/0` |
| 3–12 | 12 / 8 | `0x001A07CC`, return 2 each | `0/0` through `9/9` |

The pinned review source `leaf_matching.cpp` maps `0x001A08A8` to a function that increments `task+0x18` and returns 1. `leaf_batch25_a.cpp` maps `0x001A07CC` to the 112-byte wrapper that calls an indirect callback. The runtime trace corroborates the top-level targets and returns, but it does not record that wrapper's nested `BLX r0` target or return. The `0x001C1D2C` target is directly corroborated by the runtime method-table/target/PC equality; no semantic inference about its callback is needed for this review.

The ten Calc State-2 dispatch-return observations all have `r0=1`, state 2, and the same work pointer. There are no `calc_followup_results` and no Secondary entry/exit observations. Ten readiness cycles each record task-activity call `task=0x200061` returning 1, followed by outer readiness result 0 while State 2 and the same work pointer remain. Thus the task-activity helper continues to say the task is active and the outer ready helper does not report ready in this sample. The instruction index remains at 12 across the repeated ID-8 calls while the recorded task counters advance; this is evidence of repeated work/counter progression, not full script-step completion.

The capture stops with `stop_reason=timeout` after 12 handler returns and ten readiness checks—before either the 128-return or 40-readiness bound. The current runner default is 180 seconds; run-017 does not pin the runner or record the Python invocation arguments, so the exact timeout passed to this run is not independently bound. No unchanged-sample-only stall claim is justified: the nested callback and its wait condition were not observed, and the counter snapshots changed.

## Comparison with the earlier attempt and remaining limits

The earlier run-001 report (`261398eeb37cadc4a28d04ee4d32f74d763a9c63982dff2b8d1e692021d5f485`) records `partial_failed`, one launch exiting with `0xC0000135` before listener readiness, an empty trace, and no RSP connection. Run-017 supersedes that failed startup as the latest original-only capture: it verifies loopback ownership and records a real partial trace. It does not retroactively make run-001 a successful capture.

H2 remains open. This evidence is original-side only and uses logical query stubs for navigation. There is no patched-side run, physical input mapping/scheduling proof, completion or downstream State-2 follow-up, Secondary timing, clean restart, or persistence result. The source-save hash is reported by the runner; this review did not read the supplied save.

## Next bounded investigation

Use a fresh packet that pins the exact runner source hash. In one original-only, read-only RSP observation, instrument the nested indirect call inside the ID-8 wrapper at `0x001A07FC` and its return at `0x001A0800`. Record the nested target, arguments/return, task instruction/counters before and after, and corresponding readiness result; stop at 20 such calls or 40 readiness checks, with the existing wall-clock bound. Preserve original results/state and the disposable-profile boundary. This directly tests what the repeated return-2 loop is waiting for without labeling the current timeout a deadlock. Do not claim H2 completion or persistence from that follow-up alone.

## Hashes

- Run-017 task packet: `5c8bc300f0a75eb0ccc8355acd811189172eed6a0e36e7b84f56bbc1c3e69d4a`.
- Run-017 runtime report / console mirror: `9976f6f643dfb9ef08e084cd2d6a92bfebbb7e1826dde761a122810e6aade4a4`.
- Current runner hash frozen by this review packet: `fc642f6cef0613138785fcde97f2b2c36eefccf091df4ca3689fc8e3545185cb` (not pinned by the run-017 packet).
- `src/engine/leaf_batch25_a.cpp`: `12e1a027ab15354c8b19a77cb242c7ec2e10b342579afa6ad0e6bd3e7c962df1`.
- `src/engine/leaf_matching.cpp`: `90238ffc67607cdb8578d1ce65aa6370389deb527423d3b0b278e43f6f621da2`.
- Earlier blocked run-001 report: `261398eeb37cadc4a28d04ee4d32f74d763a9c63982dff2b8d1e692021d5f485`.

