# H3 runtime edge evidence independent review

Owner: `h3-final-review`  
Packet: `build/agent-work/H3-semantic/h3-runtime-edge-review/run-005/task.json`  
Reference image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`

## Review result

The empty-slot and cancel comparisons support matching UI gating/checkpoints in the original and patched runs. Save and per-run profile state remain unchanged. The payload-zero and missing-file probes **do not establish a real read-error response**: the zeroed-payload runs still report setter `r0=1` and acknowledge `Load complete`, while the file-absent probe also reports setter `r0=1` and explicitly marks `real_read_error_reproduced_both=false`. The forced-status probe did not produce an error route either. H3 correctly remains open for real read-error behavior.

All hashes listed by the `run-003` packet matched at that review. The `run-004` and `run-005` consistency rechecks also found no input hash mismatches. No emulator was launched and no runner or runtime input was changed.

## Empty slot 1

In both runs the controlled selection is slot 1 with work state 2, `slot_active=0`, and `name_nonzero=false`. After one trigger-0 result both stay in load state 2; the progress record still has state 2. There is no `save_load_process_start`, no load-complete acknowledgment, and no field-manager entry. `empty_slot_rejected_both=true` therefore describes the slot gate, not a downstream error handler. Original and patched event order/progress match. Each save remains 151,088 bytes with source SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; each isolated profile is unchanged within its run.

## Cancel from populated slot 0

Both runs select active slot 0 with nonempty name data, then receive trigger 1 in work state 2. The callback changes the load UI state from 2 to 3; after five callbacks the captured title work state at `+0x9C` is 5. Neither run reaches `save_load_process_start`, the field manager, or a load-complete acknowledgment. The pinned `original/load-stall-screen_small.png` shows the title menu with `Load Game` selected, consistent with the reported return to the title menu. Original/patched callback and progress records match, and save/profile hashes are unchanged.

## Zeroed-payload probe

The mutation manifest records a `0x100`-byte preserved prefix and a zeroed interval `[0x100, 0x24E30)` in each staged save. Both mutated files have SHA-256 `dcf807645d7f9d640f8f0b3f323d79e93111c62756e43d3e49071b4f6129ee1c`. The name remains visible and slot 0 is still recognized. The runs reach the save-load status setter with `r0=1`; both then record a `Load complete` acknowledgment returning 1, but neither reaches the field manager (`post_ack_pc=0x23D04C`). The report calls this a malformed-payload negative control; it is not a read-error pass, and its successful status/dialog are direct counterevidence to describing it as a read failure.

The restore manifest maps both staged save paths back to the source SHA-256. I independently hashed the source save and current original/patched staged files: all are 151,088 bytes and SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. Neither missing-save quarantine path remains present.

## Missing-file and forced-status probes

For the missing-file probe, each report records `requested=true`, removal at `save_load_process_start`, and restoration at `save_load_status_setter`. The setter event still has `r0=1` in both runs; `successful_status_still_observed_both=true` and `real_read_error_reproduced_both=false`. `load_complete_acknowledged_both=false` means no acknowledgment input was recorded in this probe; the narrative detail says the UI displayed `Load complete`. The file being absent during the injected interval does not establish that the game observed a failed filesystem read: the observed result is successful status, with no field-manager route in this bounded capture.

The forced-status report records an injection request at setter entry and original status `r0=1`, but `forced_status_error_response_both=false`; both runs still acknowledge `Load complete` and reach the field manager. The structured report does not record a changed post-injection status value, so the review does not claim that a zero status was effectively observed. Either way, the probe did not produce an error response and is not evidence of real file-read failure handling.

## Claims and remaining limits

The runtime comparison note and milestone keep the real read-error case unresolved; that is accurate. The empty-slot and cancel runs cover UI guards and return behavior for this supplied fixture. The zeroed payload only shows that a damaged body can still enumerate and receive a successful status/dialog before stalling short of the field manager. The missing-file and forced-status probes likewise did not show a read-error response. The original save-reading/I/O implementation remains a dependency; no evidence here reconstructs it or proves error behavior for another save.

The source, staged copies, mutation manifest, restore manifest, and report hashes are identified in `run-003/runtime-edge-review-summary.json`. Retain H3 as open. The next useful evidence is an actually observed read failure at the original reader boundary and its resulting status/UI path, with source/staged fixture hashes before and after.

## Run-004 documentation consistency recheck

The frozen `docs/milestones/H3-load-from-title.md` now says empty-slot and cancel were compared and independently reviewed, and keeps H3 open because an actual read-error response has not been reproduced. `docs/function-records/0x0030a9a4.md` likewise marks empty-slot rejection/cancellation as independently reviewed and leaves only the real read-error response pending. `docs/agent-work/h3-runtime-comparison.md` records that the edge review accepted empty/cancel and that the zero-payload/missing-file/forced-status probes did not establish an actual read failure. These statements match the pinned evidence reviewed above. All `run-004` packet hashes matched; no runtime checks or emulator runs were repeated.

At the run-004 review, two wording issues were noted. The run-005 check confirms both are corrected: the milestone now has one real-read-error pending item, and the function/runtime notes say the runner attempted to write setter `r0=0` but the paired JSON has no post-write register read-back. They correctly avoid claiming an effective write or a read-error pass.

## Run-005 final wording confirmation

All `run-005` task input hashes matched. The milestone now has a single pending item: reproduce a real error at the original read boundary. It explicitly says empty-slot and cancel were already reviewed and does not leave them as separate blockers. The function record says empty-slot rejection/cancellation matched and passed independent review, keeps a real read-error response pending, and clarifies that setter `r0=0` was only attempted: the paired JSON has no post-write read-back. The runtime comparison note makes the same limitation explicit. These edits accurately preserve the evidence boundary: the zeroed payload still reports setter `r0=1`; the missing-file probe reports `r0=1`; the forced write is unverified; no real read-error response has been shown. This was a documentation-only recheck; no runtime evidence was rerun and no frozen input was modified.
