# Independent hardening review: APT Utility-4 caller probe

## Recommendation

**The requested hardening is independently verified; eligible for coordinator acceptance as a pre-runtime review.** The earlier profile-count discrepancy is resolved in the fresh packet, and the timeout test now drives one shared fake loopback socket through the production `DeadlineRsp`, `capture_session`, and `execute` finalizer. The focused unittest suite passes. This does not authorize or establish a runtime capture: the runtime packet has not been prepared, the four runtime gates have not been repeated for it, and no dynamic caller evidence or APT hardware semantics are established.

## Frozen identity and checks

Review packet: `build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-hardening-review/run-002/task.json`, SHA-256 `003c39794046ace10bcfb82ab1586255c624c454911ff874a55def7f487d5c0e`. All 13 declared input hashes matched.

The producer hardening task packet `build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-hardening/run-003/task.json` declares 24 inputs; all 24 hashes matched. The profile audit input/output hashes also match the review packet. The exact 12 profile paths and SHA-256 values in that task's pin map match the 12 rows in `profile-seed-pin-audit.json`; path sets are identical. The audit reports `live_file_count: 12` and `exact_file_set_match: true`.

Key implementation and evidence hashes:

- Runner `tools/h2_apt_utility4_caller_probe.py`: `16fa1d77bf44fa358fee5620541700d5df4b9538fe7802b1f510228246a1fff4`.
- Tests `tests/test_h2_apt_utility4_caller_probe.py`: `91f54afec302de02791ba307de5d2bead15316e2d776c6f964dbe1d24c034b10`.
- Hardening report: `69f51a89c573cd4b8a5c1ed73ac2f23627e33e49bf0c5e5214b8cd3cebf85f5c`.
- Profile pin audit: `c070946c15dd5f207f0b7a64359cb3dcd83a008eb207fcf804f317d4c4dc786b`.
- Producer test log: `2ea43a4cf46cfe75c7931950b3b2cdb282da8eb88dee5b4c83d0aaf144c0242a`.
- Producer handoff: `6146b79e21618a7cab57dabad70a1d17781d0defa28c82c6bfe271d0bb3db7bb`.
- Prior independent review: `b97daf581391e812b35997ba6fc5b2db551d5b8db31cf5e4e3f611ae42af8a45`.

I ran only the assigned focused command:

`python -m unittest tests.test_h2_apt_utility4_caller_probe -v` — exit 0, 24 tests passed.

## Independent findings

### Packet pins and complete profile seed

`validate_task_and_inputs` calls `verify_packet_inputs` on the complete declared `input_sha256` map, not just selected constants. It requires the runtime executable and delivery manifest plus the provisioned seed paths. The manifest's packet SHA is checked, and the executable's resolved path and content hash must agree with both the manifest and packet input.

`verify_profile_seed_manifest` compares every packet input below the profile seed root with the full live file manifest and requires exact path-set and hash equality. The run-003 frozen task packet provides all 12 profile seed pins, and the accompanying audit matches all 12 paths and hashes. The previous two-file discrepancy is corrected in this packet. This is evidence about the disposable build profile only; no user profile was accessed or staged.

### Deadline and cleanup behavior

The source applies one monotonic capture deadline beginning before loopback connection. Connection uses the lesser of remaining time and per-packet cap and checks the deadline after connect. `DeadlineRsp` applies the same deadline and cap to each send and each fragmented receive, including handshake/attach, breakpoint requests, continue, PC/register reads, and response acknowledgments. It rejects deadline extension.

On an in-flight continue timeout, the client starts one cleanup deadline. `begin_cleanup_grace` is idempotent, so interrupt, breakpoint clear, and detach share the same bounded grace. The `capture_session` finally path closes the socket regardless of cleanup success; `execute` then terminates the owned child, checks listener release, verifies source/staged hashes, and removes only its newly owned stage after confirming the child is stopped. Process and stage teardown are separate from the RSP deadline and are reported separately.

### Timeout test uses the production path

The updated `test_timeout_flows_through_capture_and_execute_finalization` no longer patches `capture_session` or swaps in a second RSP object. `execute` creates the production `DeadlineRsp` around one fake loopback socket; its fake peer completes negotiation/attach and breakpoint insertion, acknowledges continue, then times out the next read. The same object sends the interrupt, receives a stop reply, clears the breakpoint, detaches, and closes. The test observes one continue timeout and one interrupt, `z0` and `D`, then checks child termination, listener release, owned stage removal, the allowed staged-save mutation, unchanged source fixture, and no cleanup errors.

The fake does not exercise a real network scheduler or elapsed-time race, but it does test the production transport/capture/finalization composition without launching the emulator. Separate tests check remaining-deadline clamping for fragmented reads and reject I/O after deadline. Source inspection confirms the socket timeout is reset before each fragment, not only once per packet.

### Save policy and preservation

The runner explicitly permits mutation of the disposable staged save copy and records before/after SHA-256 plus `staged_save_changed`. The fixture source is independently hash-pinned and compared after execution; the fake integration test exercises a changed staged copy while asserting the fixture remains unchanged. The runner records supplied-source-save access as false. I did not open or hash the supplied source save, and no profile/save was staged in this review.

## Remaining limits and next action

No implementation defect surfaced in the requested hardening areas. Evidence remains offline and bounded: the tests use fake sockets/processes, no Azahar/GDB run occurred, the runtime task packet is not yet prepared, and caller identity plus Utility-4 hardware semantics remain unobserved. The coordinator should accept this hardening review, then prepare a fresh runtime packet with all 12 profile pins and repeat the four offline gates with hash attestation before considering one bounded capture. This review alone is not runtime approval.

