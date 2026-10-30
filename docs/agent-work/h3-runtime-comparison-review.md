# H3 runtime evidence independent review

Owner: `h3-final-review`  
Packet: `build/agent-work/H3-semantic/h3-runtime-evidence-review/run-001/task.json`  
Reference image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`

## Review result

The paired runtime evidence supports the bounded known-save happy path in the report: after the populated slot is selected, both runs record the `Load complete` acknowledgment, reach `Map_Field3DManager`, and capture the same 250 field-manager entries. The field 3D scene is supported by the pinned screenshots. This is one save and one route; it does not close H3 or establish equivalence for cancellation, empty slots, or read errors.

All packet input hashes matched the current files. The paired report status is `observed`, and it correctly marks `post_confirm_events_equal` false rather than describing every event byte/register as identical.

## Sequence and normalized comparison

For both original and patched JSON:

1. The controlled first trigger was issued with work state 2, selected slot 0, and nonempty slot text. Slot 0 text matches in the two records.
2. The second trigger record says it was supplied after observing the `Load complete` dialog. It returned 1, reached the callback exit, left work state 5 and manager flags zero, and recorded `field_manager_reached=true`.
3. The field-manager entry registers match: `r0=0x3B`, `r1=r2=0x4096CBE4`, `r3=3`. Each run has 250 entry snapshots with an identical register sequence: `r0` counts from `0x3B` to zero and remains zero for the remaining snapshots. Each has 249 transition statuses, all returning to the epilogue and reaching the next manager tick.

There are 11 `post_confirm_events` in the same order. The sole field difference is `save_load_io_worker` register `r3`: original `0x873CD00`, patched `0x873CC80` (a `0x80` address delta). The other registers and events match. The subsequent progress records are identical. This is a real pointer difference; the successful matching status and scene path support this one observation, but do not prove the two buffers are interchangeable for other inputs.

The paired JSON records say the logical input was sent only after the dialog was observed, but the pinned screenshots in this packet are the final field captures, not a screenshot of the `Load complete` prompt itself. The input timing is therefore supported by the structured runtime record, not independently image-verified here.

## Fixture and profile integrity

The supplied source fixture and both staged runtime copies were read-only hashed during review. Each is 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. In both original and patched JSON, the staged save's before and after hashes are identical to that value. The 16-entry profile manifest is unchanged within each run, so the claim that the other files in each isolated profile stayed unchanged is accurate.

The original and patched profile manifests are **not byte-identical to each other** at baseline or after the run. Six entries differ: `config/qt-config.ini`, both Azahar logs, both OpenGL shader caches, and `sysdata/play_time.bin`. The docs do not claim that the complete profiles are byte-identical, but `profile_unchanged_both` means each profile stayed unchanged within its own run; it does not establish cross-run profile parity. Keep that distinction in any attribution or performance claim. The save fixture itself is identical.

## Screenshot inspection

The pinned small captures match their packet hashes:

- Original: `09d6c889a868601c0bfabf42efedd7e2be12df59e0a63fb47b6e4f0e65484db2`
- Patched: `c1138ec8aef84b689c56fe270189a11d77431ed71ccfb4a7d852b8ff3f983ab2`

I also compared the full-resolution captures (`1280x540`) visually and pixelwise. The upper 3D viewport is identical pixel for pixel and shows the same Shinjuku Station — Underground entrance. The screenshots differ in 3,666 pixels, all within a lower-screen bounding box from `(480,293)` to `(799,529)`; the map layout and markers remain the same on visual inspection. The lower-screen differences are consistent with capture timing or UI rendering variation, but the image pair alone does not establish their cause. Thus, the documented same-scene statement is supported; exact screenshot equality is not.

## Documented limits

The current runtime report and milestone notes correctly keep H3 open and limit the claim to this one known save. They explicitly leave empty-slot, cancellation, and bounded read-error behavior pending, keep save reading as an original dependency, and make no player-coordinate or orientation claim. The paired JSON contains the context argument (`0x4096CBE4`) but does not include a GDB memory-read failure transcript; the specific `E0E` rejection is documented in the narrative record, not independently reproduced from these pinned machine reports.

The source save, both staged copies, and per-run profile manifests support the stated fixture-preservation claims. The Azahar/CCI identity is stated in the runtime comparison note, but their hashes are not embedded in the paired JSON files reviewed here. No emulator was launched during this review.

## Recommendation

Accept this as evidence for the bounded known-save route reaching the same observed field scene, while keeping the milestone open. Before stronger paired-run causal or performance claims, document/normalize the six cross-profile baseline differences. Continue with isolated empty-slot, cancellation, and bounded-error scenarios; preserve the original reader as an explicit dependency until those behaviors are reconstructed and tested.
