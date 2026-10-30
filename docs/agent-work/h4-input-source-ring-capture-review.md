# Independent review: H4 source-object capture (run-003 final packet check)

## Summary

The run-003 packet's 19 declared input SHA-256 values match. The raw paired reports support a bounded, read-only capture of 0x100 bytes from `r0=0x10000000` at the call probe `0x0011C640`, followed by a second read from that same validated address after all four configured probes. The source span changed between the two reads in both processes. This records sequence changes only; it does not identify a live ring, physical input data, a semantic event count, or which instruction/thread changed those bytes.

The capture report and docs use careful bounds: both original/patched profiles reached the field manager and completed 250 tick observations; the target probe saw `r0=0x10000000`, `r1=0x004E3C28`, `r2=1`, `r3=SP+8`; the primary/alternate input records and counter/calibration snapshots remained unchanged and zero at the captured boundaries. This is source-object/caller-state evidence, not a recovered C++ contract, player movement, or whole-game equivalence.

## Provenance and reports

The packet pins the runner, capture document, aggregate runtime report, both per-run sidecars, the producer's handoff, and four offline reports. All 19 input hashes matched. The aggregate report is `build/agent-work/H4-semantic/h4-input-source-ring-capture/run-002/checks/validated-rerun-003/runtime-report.json`, SHA-256 `1c67789bae77552962b99a025a2b32bfa8d89855d5b8fd0c998afb0ec6d23645`, status `observed`. The frozen sidecar hashes are `original.json` `d24ab88e79dd8e24d43ff3a2eb06ef25da7d0d9dca7f4ed19378e5580733697e` and `patched.json` `7c5c478c5e0d258f5e1a12c6cfe2a1817dbad9cecd5f887032a3e7a4c33411d0`.

The input-save hash metadata in the capture document is separate from the runtime JSON. Both raw sidecars record the staged profile save at 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` before and after. As a metadata-only cross-check, the earlier `source-save-integrity.json` record (SHA-256 `11d47c141b4cf2c958879a40bd7bb6fbe744d739544da90a8006de0fe8542b29`; not an input declared by this run-003 packet) records that same digest as the known pre-run fixture hash and the separately recorded post-trace hash. I did not open or hash the source-save file; this is verification of the separate hash record, not a direct file check.

The producer handoff pins the offline H3 composed image and IPS hashes and records successful offline H3 entry/caller plus H4 direct/camera checks. The runtime JSON does not embed the executable/image hash actually loaded by each profile, so exact runtime image identity remains less directly bound than the offline artifacts.

## Source-span bounds and access behavior

At `0x0011C640`, both reports show `r0=0x10000000`, `r1=0x004E3C28`, `r2=1`, `r3=0x0FFFFED0`, `SP=0x0FFFFEC8`, and `LR=0x0011C620`. The source span is `[0x10000000,0x10000100)` (256 bytes). The runner accepts it only if `pointer >= 0x10000` and `pointer + 0x100 <= 0xFFFFF000`; the report marks range validation true and contains all 256 captured bytes. The 0x40-byte stack dump is present in both sidecars; `r3` is `SP+8`. Probe `0x0011C644` separately records post-call registers and stack.

The new source capture uses `rsp_read_mem` at entry and for the later reread; it has no `rsp_write_mem`, `write_reg`, or guest register write. The after read occurs after the configured four-probe loop, not immediately at `0x0011C644`. Thus the result brackets a bounded sequence and cannot attribute intermediate changes to the copy call specifically. Other probe code can have optional mutations for an explicitly requested camera-axis override, but this run only configures `0x001078E8`, `0x001078EC`, `0x0011C640`, and `0x0011C644`; the reports contain no `axis_override` entry.

## Recomputed source deltas and type limits

I compared entry and post-probe bytes in each 0x100-byte span. Both processes change only these byte intervals: `+0x00..+0x03`, `+0x08..+0x0B`, `+0x10`, `+0xA8..+0xAB`, `+0xB0..+0xB3`, and `+0xB8`. The raw values confirm the updated capture document:

| Field | Original | Patched |
|---|---|---|
| `+0x10` dword | 3 → 6 | 0 → 4 |
| `+0xB8` dword | 3 → 6 | 0 → 4 |
| `+0x00/+0x08` values | both change | both change |
| `+0xA8/+0xB0` bytes | match `+0x00/+0x08` respectively at each snapshot | match `+0x00/+0x08` respectively at each snapshot |

The capture document now distinguishes `+0x00` and `+0x08` as two 64-bit snapshot/cursor values, and `+0x10` as the count used by the copy helper. This is consistent with the described static use at `0x0012A758`. It correctly leaves the relationship and meaning of the changed `+0xA8/+0xB0` fields unresolved. The value at `+0xB8` tracks the `+0x10` dword in these before/after samples, but equality of values does not establish identity or semantics. These bytes also differ between original and patched process instances; do not read them as equivalent logical state.

The 18 changed bytes in each process are observed after a 250-tick field run and then across the sequential probe sequence. The source snapshot's `source_object_unchanged_through_probes` is false on both sides. No timestamp or per-write instrumentation narrows the change to a specific producer, consumer, or exact instruction interval.

## Paired runtime and integrity scope

Both runs have `field_manager_reached=true`, 250 `field_scene_ticks` (indices 0–249), and 249 subsequent successful next-manager callback statuses. The four configured probes all hit on both sides. The aggregate reports equal title-entry registers, title state-8 bytes, save/load callback signatures, post-confirm progress, field-scene signature/tick count, and within-run save/profile integrity. It also reports `post_confirm_events_equal=false`; the capture document appropriately says some post-confirm event details differ and avoids calling this whole-game equivalence.

Each staged save is 151,088 bytes with the same SHA above before/after each run. Both non-mod profile manifests are unchanged within their respective runs. The starting original/patched manifests differ in six files (Qt config, two logs, two OpenGL shader caches, and `sysdata/play_time.bin`); integrity therefore means within-run preservation, not identical starting profiles. Screen fields are null, so this report is not visual evidence.

The capture document explicitly excludes the preliminary C-drive attempt that stopped before slot confirmation and describes only the validated isolated original/patched pair. The successful sidecars confirm slot 0 load and the “Load complete” logical UI confirmation. This is not an active gameplay/axis-input event; the report does not claim that it is.

## Corrections and remaining limits

The updated source capture document's description of the two 64-bit cursors at `+0/+8`, count at `+0x10`, and unresolved changed fields at `+0xA8/+0xB0` matches the raw bytes and the static helper account. It avoids classifying the object as a ring, joystick sample, or player-state object. Keep the capture strictly as a source-span observation. No data here establishes physical input availability, source-object ownership, repeatable active-input cadence, movement, interactions, transitions, or H4 completion. The broader H4 path still needs an independently delivered and verified input event tied through the source object to a confirmed player-state update.

## Read-only checks performed

- Compared all 19 run-003 `task.json` input hashes; all matched.
- Parsed the aggregate runtime report and both raw sidecars; verified the source span, validation flag, entry registers/stack, changed byte offsets/values, all four probe hits, tick counts, and staged-save/profile results.
- Checked the four pinned offline report summaries and producer handoff for statuses, control results, image/IPS identities, and evidence scope.
- Inspected the `0x11C640` snapshot and post-sequence reread instrumentation; no build, Azahar run, write to guest memory, workflow-board edit, or source-save access occurred.
- Cross-checked the source-save digest against the separate integrity metadata record listed above; its known pre-run fixture hash and separately recorded post-run hash are both the same digest. The runtime sidecars report staged-save hashes only. The underlying source-save file was not opened.

## Final run-003 packet recheck

All 19 hashes in `build/agent-work/H4-semantic/h4-input-source-ring-capture-review/run-003/task.json` match their current inputs. The pinned capture document now states that the known pre-run source-save fixture hash and the separately checked post-run source-save hash are each `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; this is separate metadata from the runtime JSON. The raw sidecars independently show staged saves unchanged before/after and each profile manifest unchanged within its run. The original/patched starting profiles still differ in six files, which the document correctly limits to within-run integrity and does not present as identical baselines. The source-save file was not accessed.