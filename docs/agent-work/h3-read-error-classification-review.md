# H3 read-error result classification review

## Scope and provenance

Reviewed the frozen `h3-read-error-classification-review/run-001` packet. All 21 declared `input_sha256` entries in its `task.json` matched the current bytes, including the original ARM-backed `SaveLoadProcess_Step` at `0x002EF9AC`, the load contract, paired runtime JSON, and the prior runtime notes. No emulator or runner was launched and no input was changed.

## Branch decode and result bytes

The pinned function has two terminal result writes to global `0x0043E2F0`. State 6 writes byte `+3 = 1` and byte `+0 = 1`, then returns `-1`. State 7 writes byte `+3 = 0` and byte `+0 = 1`, then returns `-1`. Thus `global_43e2f0` values `0100000100000000` and `0100000000000000` identify the state-6 and state-7 result markers, respectively. These are distinct from the status-setter call's `r0`: every report below has setter `r0 = 1`, including the state-7 cases. Treating setter `r0` alone as the success/failure result would be incorrect.

| Paired scenario | Setter `r0` (original/patched) | Global bytes at setter (original/patched) | Follow-up evidence |
|---|---:|---|---|
| Happy control, `runtime-field-settle-016` | `1 / 1` | `0100000100000000 / 0100000100000000` (state 6) | `Load complete` acknowledged; field manager reached; save stayed 151,088 bytes with source SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. |
| File removed before confirm, `runtime-missing-before-confirm-037` | `1 / 1` | `0100000000000000 / 0100000000000000` (state 7) | Injection records removal before confirm and restoration at the setter; save before/after has the 151,088-byte source hash above. No acknowledgement or field-manager entry was recorded; captured load-stall screen is black and shows no explicit error text. |
| File removed at process start, `runtime-error-missing-save-030` | `1 / 1` | `0100000000000000 / 0100000000000000` (state 7) | Injection records removal at `save_load_process_start` and restoration before the setter; save before/after has the source hash above. The paired post-read screenshot displays “Load complete,” not an explicit error message. The report's `load_complete_acknowledged_both=false` means no acknowledgement input was recorded; it does not negate the visible dialog. |
| Short-file control, `runtime-short-read-041` | `1 / 1` | `0100000100000000 / 0100000100000000` (state 6) | Each staged file is 256 bytes, SHA-256 `a4adf60a00931196e40d3b457ce37b49c6b75ff6b4b229d033943d793a5ace36`, unchanged before/after. “Load complete” was acknowledged; field manager was not reached. This malformed/short payload does not take the state-7 result branch. |

## Finding

Both missing-file probes reach the state-7 internal result marker in original and patched runs, while the happy and short-file controls reach state 6. The absent-file injection windows and subsequent restoration are recorded in both paired reports. This supports classifying the observed process result as the distinct state-7 failure-result branch for these probes; the setter's `r0=1` is not contrary evidence because it is a separate call argument and is also present in the state-6 controls.

The UI conclusion is narrower. The process-start probe's screenshot explicitly shows “Load complete”; it does not show a user-facing error. The before-confirm capture is a black stall screen without visible error text, and no acknowledgement was recorded. Therefore evidence supports an internal failure-result marker on the two absent-file probes, but not an explicit UI error response. Also, the reports do not capture the lower-level file-open/read return value; they establish that the file was absent during the specified injection interval and that the process emitted state 7, not the exact failing filesystem operation or whether this is the complete user-facing error contract. Keep any claim bounded to this observed internal result branch and these paired runs.

## Checks and limits

- Frozen packet input hashes: 21/21 matched.
- Source-level terminal writes were checked against the in-function ARM words in `src/ui/save_load.cpp`; paired status bytes were read from each report's raw `save_load_status_setter` event.
- Save integrity is supported by report-recorded before/after sizes and SHA-256 values plus the injection restoration events; this review did not inspect or mutate private emulator save files.
- No runtime was repeated. No emulator was launched. This review does not establish whole-game equivalence or prove the lower-level filesystem return value.

## Recommendation

Record H3's internal state-7 result branch as observed for the paired missing-file probes, but do not describe it as an explicit UI error. If the contract requires proof of the actual reader failure, capture the I/O/open/read return at the original boundary while the file is absent and correlate it with the state-7 write.

## Follow-up: direct open-boundary capture

The coordinator supplied a new paired capture, [`runtime-missing-before-confirm-044`](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-002/runtime-missing-before-confirm-044/), after this review recommended tracing the original reader boundary. I independently checked both JSON traces against the original code and found the save removed after slot enumeration and restored before `0x002C5948`. At `0x002D8E60`, immediately after the original file-open call and at its `cmp r0,#0`, both profiles report `r0=0`. Both status setters retain `r0=1` while `global_43e2f0` is `0100000000000000`, whose byte `+3=0` matches the state-7 failure write in `0x002EF9AC`. Neither reaches the field manager.

Both staged saves are 151,088 bytes and retain the fixture SHA-256; source save integrity is independently unchanged. The machine report records `real_read_error_reproduced_both=true` and profile integrity true. The only raw paired-event difference is status-setter `r2` (`0x2A1` original, `0x2A0` patched); its contract is unresolved, so this remains a raw-trace difference. The screen capture failed, and no user-visible error message is established. This direct boundary/result evidence closes the bounded internal error-path criterion without claiming broader equivalence.
