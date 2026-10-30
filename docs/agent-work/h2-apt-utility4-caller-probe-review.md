# Independent review: APT Utility-4 caller probe

## Result

**Recommendation: ready for coordinator review after the bounded fixes below; do not treat this as runtime approval.** The implementation is intentionally narrow: it sets one software execution breakpoint at `0x002C0EE0`, records up to four caller hits, reads PC/LR and registers, and makes no explicit guest memory/register writes or logical input injections. The static source and offline validation evidence support those implementation claims. The reviewer did not run the tests, build, emulator, or GDB.

## Evidence identity

The assigned review packet is `build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-review/run-001/task.json`, SHA-256 `6d490f254a9ffb8002569b7ce132f4857924c3e1f2765b32626e9f7913639914`. All 15 declared `input_sha256` entries were recomputed and matched. Key reviewed hashes:

- Probe runner: `927c00c3a50f5de86cf15d1565106b60c27a340a71b5729672db358bae2110b2`
- Focused tests: `c69dca99d10346ba9e878002edff5938bd839f72a060d4eb652026e9fe627569`
- Producer offline-validation report: `559de33ae024d310d575ab3ed8f75a699cdd407f5be8b2ff7e404fbf365ffdd9`
- Producer handoff: `4d6c88c51f5bee234bd0b770f8fd62ea77c84a66751f4024ee5bdfdcc08ccb12`
- Private delivery manifest: `2d84d83fee84b4d1588d310084e0dc919cbd4c92fa41d4432497e696e2b0f286`
- Private Azahar executable: `1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682`
- Pinned `code.bin`: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Log comparison note: `fbd035ec4038a4c3100293085c41697d1bbb10be395a6f194c213e4d43d5fd1c`

The executable hash agrees with the delivery manifest and the private build output hash record. The runner pins the executable path/hash and separately pins `code.bin`, the CCI, disposable fixture, and HLE log data. No runtime report exists for this implementation task; the producer states it has not been launched.

## Implementation review

- **Breakpoint and hit bounds:** The runner uses one exact ARM Z0 breakpoint, `Z0,2c0ee0,4`, and validates returned PC/LR/register data. It constrains `max_hits` to 1–4 (default 4); the helper disassembly at `0x002C0EE0` shows the command-4 argument and a call to the wrapper at `0x002B5A1C`.
- **Caller identity:** Direct A32 BL references to the helper are `0x00102184` and `0x001051DC`, with expected return LRs `0x00102188` and `0x001051E0`. This is a static direct-call scan, not proof that these are all possible indirect callers or that either was dynamically observed.
- **RSP scope:** The packet set is limited to capability/attach/process queries, continue, register reads, breakpoint set/clear, and detach. I found no M/P/X packets or host-input injection in the reviewed path. The Z0 breakpoint is a software breakpoint and therefore temporarily changes guest code while active; cleanup attempts to remove it.
- **Timeout and cleanup:** The code sends an interrupt on continue timeout; `finally` paths clear the breakpoint, detach, close the socket, terminate the owned child with a kill fallback, check listener release, hash inputs, and remove only its newly-created private stage directory. Stage cleanup is refused if the child remains alive. Listener checks require exactly one `127.0.0.1` row on the selected port and the launched child PID; the port is rechecked after shutdown.
- **Offline gate attestation:** The runner requires four passed, hashed offline gate reports rooted under the selected runtime packet output root and retains source-identity warnings. The producer report/handoff says 19 focused tests passed; I counted 19 test methods in the test file. This is inspected producer evidence, not a rerun by this reviewer.

## Findings requiring correction before runtime

1. **Runtime packet input pins are not enforced.** The runner validates the runtime task packet identity/path/output root, but does not iterate and recompute its `input_sha256` map. `validate_delivery_manifest` verifies the manifest’s own hash for reporting and checks executable path/hash against manifest contents, but does not compare the manifest hash to the runtime packet’s declared pin. The profile seed’s live file manifest is captured and preserved, but is not compared with its packet pin. Separate constants cover some inputs, not all declared packet inputs. Before a runtime packet can authorize capture, validate every declared input hash (including manifest and profile seed) against that packet and fail closed on mismatch.

2. **The capture wall-clock bound is not applied to every RSP operation.** `continue_until_stop` configures a socket timeout from the remaining deadline, but after a hit the runner issues separate PC and register reads under that timeout value; the timeout is not recomputed from the monotonic deadline for each request. A slow sequence can therefore exceed the declared capture budget. Also, packet timeout is only required to be positive and can exceed the stated maximum wall-clock budget during handshake. Enforce one monotonic deadline across handshake, continue, and each read, clamping every socket operation to remaining time.

3. **Timeout cleanup lacks an end-to-end test.** The timeout unit test exercises interrupt behavior through `collect_hits`, but does not show a timeout flowing through `capture_session` and proving breakpoint clear, detach, socket close, and child/stage cleanup. Add a focused fake-RSP/process test that asserts these finalizers on timeout and interruption. Keep the current claim limited to source-path inspection until such a test exists.

4. **Disposable staged-save preservation is not asserted.** The source disposable fixture is hash-pinned and checked after the run, and the user-supplied source save is not opened by this path. The runner reports before/after staged-save hashes but does not fail if they differ. That can be acceptable for a disposable runtime copy, but the report must label this as a recorded delta, not unchanged persistence; add an explicit expected-mutation policy or equality check if immutability is intended.

The tests also do not cover a task-packet input-pin mismatch, profile-seed mismatch, manifest substitution with the same executable, actual listener PID mismatch/post-run release, or the full timeout cleanup sequence. The existing 19-test result should not be described as covering those cases.

## Static evidence limits

The authorized comparison note and offline report contain historical HLE command-4 log counts of 4 for Run-017 and 6452 for Run-028. I did not open the raw logs. Those counts are HLE-log evidence only: they do not establish guest caller identity, a stall, its cause, or hardware Utility-4 semantics. The current review establishes only that the probe is statically bounded and that direct A32 callers exist. It does not establish a runtime hit, successful command completion, or semantic equivalence.

## Commands and scope

Read-only inspection was limited to the assigned packet’s declared paths and the listed producer evidence. I recomputed declared input hashes and inspected runner, tests, disassembly, offline report/handoff, manifest, build-output hash record, log-comparison note, and emulator guide. I did not run tests, build, Azahar, GDB, stage a profile/save, inspect the supplied source save, or modify implementation/shared files.

## Next action

Have the implementation owner make the three minimal runner/test changes: enforce all runtime packet input pins, apply one monotonic deadline to every RSP operation, and add an end-to-end timeout-finalization test. Clarify staged-save mutation semantics in the report. Then regenerate offline evidence and hashes in a fresh runtime packet; only after independent review should the coordinator decide whether to authorize one bounded runtime capture.
