# H2 private live snapshot crash audit

## Result

The pinned observer source contains a direct fatal-dialog path: if a requested manual snapshot returns `false`, `System::RunLoop` returns `ResultStatus::ErrorUnknown`. The Qt result handler maps the generic result to the “Fatal Error” dialog. This establishes a possible source-level cause, but the saved investigation says the second snapshot is absent and the log has no guest exception detail; it does not show that this branch ran or explain the reported dialog.

The manual snapshot's guest-memory reads are guarded and synchronous. The `RunLoop` lambda owns a strong `shared_ptr` to the process obtained from the current thread's weak owner, validates all covered virtual pages before `ReadBlock`, and rejects 32-bit address overflow. `CaptureManualSnapshot` only dereferences the guest `TitleConfigWork` pointer when it lies in the hard-coded guest heap interval and leaves state unavailable when reads fail. I found no source-backed unsafe dereference in this route. The fixed heap interval could yield a false “unavailable” for a valid object outside that assumed region; it is not evidence of a crash.

The Qt hotkey uses an atomic request flag (`release` store; `acquire` load / `acq_rel` exchange), so the request handoff itself is synchronized. Snapshot capture, observer state, and file emission run synchronously on the RunLoop thread. The observer is owned by `System` in a `unique_ptr`; the reviewed code shows construction/configuration before capture and no reset path. The `IsH2ObserverLiveMode()` pointer read is not itself synchronized, so safety depends on the application lifecycle continuing to configure before concurrent hotkey handling and keep `System` alive through the shortcut. The assigned source slice does not independently establish the whole teardown ordering; I found no demonstrated dangling object in the snapshot call.

## Trace and failure branches

1. `GMainWindow` installs an application-context `Ctrl+Shift+F8` shortcut. Its Qt lambda returns unless live mode is enabled, calls `RequestH2ManualSnapshot()`, and displays a status-bar acknowledgement. That message confirms only that a request was queued.
2. `System::RequestH2ManualSnapshot()` sets `h2_manual_snapshot_requested` atomically. At the next eligible RunLoop slice, `observe_h2` loads the flag; it obtains the current thread's process with `owner_process.lock()`, samples the CPU PC/registers and builds a synchronous `ProcessReadFn`.
3. The read function rejects zero-length and wrapping ranges, checks each virtual page with `IsValidVirtualAddress`, then calls `memory->ReadBlock`. Snapshot reads cover `0x0044E0F8` (8 bytes) and `0x0044E2D0` (4-byte pointer), then conditionally the `0x158`-byte work object.
4. `CaptureManualSnapshot` returns success while reads are unavailable; those fields are written as unavailable/empty. It can return `false` for prior observer failure, process identity mismatch (after writing an incomplete terminal record), or `EmitRecord` failure. `EmitRecord` returns false for a closed/failed stream or failed write/flush. Output byte/record limits instead append a truncated terminal record and return success if that write succeeds.
5. When manual capture returns false, the `observe_h2` lambda returns false. Both RunLoop execution branches translate that to `ErrorUnknown` and return early. The Qt generic result branch displays the fatal dialog. Observer failures in `OnBeforeInstruction` can take the same route when a selected observation fails.

## Cause assessment

- **Demonstrated fatal route:** observer false return becomes `ErrorUnknown`, which is presented as a fatal error by the Qt result handler.
- **Plausible but unproven cause:** a write or flush failure on the second JSONL record could return false and enter that route. The first 377-byte snapshot and missing second record are consistent with it, but they do not prove it; abrupt termination or another error also leaves no second flushed line.
- **Other source-backed false returns:** process identity mismatch, an already failed observer, and failures during ordinary allowlisted-PC records. The saved run does not identify any of these.
- **Not supported as the cause by inspected code:** an invalid guest address should make the field unavailable rather than throw/fail capture; a missing/inaccessible guest page is not converted to `ErrorUnknown` in the manual snapshot path. No invalid memory read or object-lifetime defect is demonstrated.
- The archived investigation reports shader-cache `SaveRaw` errors and no matching Application Error/Crash event. Those are not enough to connect the dialog to guest code, graphics, observer output, or the RunLoop false-return path.

## Smallest source-backed fix

Treat optional observer failure separately from guest/core fatal errors. When snapshot emission or observation returns false, log a bounded observer-specific error, mark the observer failed/stopped, and let emulation continue or shut down through an explicitly chosen non-fatal observer policy; do not synthesize `ResultStatus::ErrorUnknown` for it. Keep actual guest/core failures on the existing fatal path. Add a precise reason (identity failure, output open/write/flush failure, or observer state) before returning false so a future saved log distinguishes causes. This removes the demonstrated conflation while retaining honest failed-capture evidence. It does not claim to repair the unknown cause of the prior run.

## Bounded validation plan (future assigned runtime/build task)

1. In a private Azahar build, add a test-only, emulation-thread-owned snapshot request schedule activated only by the private H2 live-capture mode after the target title validates. Schedule exactly two requests at separated RunLoop boundaries; do not synthesize host key or mouse events and do not write guest memory.
2. Use a fresh disposable output path and the already validated target/profile inputs. Capture the process exit/result, observer-specific reason/logs, and JSONL. Require two distinct, parseable `manual_state_snapshot` records with monotonic sequence numbers, valid process identity, and the expected available/unavailable flags.
3. Exercise a normal bounded shutdown on the emulation thread. Require a `complete` terminal record, no `incomplete`/`truncated` record, closed output handle, and clean process exit. Also run one negative-control output-failure case in a unit/integration harness to verify it reports observer failure without producing Azahar’s generic fatal status.
4. Keep this as private observer-path validation only; it cannot establish H2 UI/input equivalence or explain the earlier screenshot without a reproduced saved log/trace tying the dialog to a specific branch.

## Limits

Read-only review of the task packet's declared files only. No build, test, emulator, profile, debugger, network, or host input was used. The saved manual-run artifacts were summarized in the investigation note; this audit did not inspect the private profile or raw JSONL, and therefore cannot establish the second request's actual return path.
