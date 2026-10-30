# H4 camera-path evidence review

## Scope and provenance

Reviewed the frozen `h4-camera-path-review/run-001` packet and all 13 declared input hashes; all matched. The four paired reports are under `build/agent-work/H4-semantic/h4-live-input-observation/run-001/results/`. Their pinned SHA-256 values are listed in the task packet. The reference code image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. This is a read-only review; no Azahar or runner was launched.

## Caller, ABI, and bounded output slots

Across all paired reports, the observed caller at `0x001FA840` has entry registers `(r0,r1,r2,r3) = (1, 0x801, 0xC19FFFF6, 0x437A0000)` and returns to `0x002767D4`. Its BL at `0x001FA948` reaches helper `0x0027FBC8` with LR `0x001FA94C`. At helper entry the observed ABI is `r0=0x0FFFFCB4` (output 0 pointer), `r1=0x0FFFFCB0` (output 1 pointer), `r2=0` (mode), and `r3=0x437A0000` (250.0f). Helper entry SP is `0x0FFFFCB0`; the two aligned, adjacent four-byte slots occupy `[SP, SP+8)` without overlap. The runner's output override guard permits only the exact caller/mode and pointers within 0x40 bytes of SP. The natural helper result is `r0=1`.

For the positive/negative controls, the runner overwrites only these two caller-stack output slots at the observed helper return boundary, keeps `r0=1`, and records that raw input buffers were left untouched. This establishes a controlled output-to-caller memory path; it does not establish physical input delivery.

## Paired memory evidence

| Report | Applied output slots `(x,y)` | View-state response at `0x002767D4`, offsets `+0x24,+0x30,+0x4C,+0x50` | Original vs patched |
|---|---|---|---|
| `runtime-field-call-probes-049` | Natural helper output `(0,0)` | No controlled camera snapshot delta claimed in this passive probe. | 0x170-byte snapshots at the relevant captured checkpoints match. |
| `runtime-axis-neutral-control-051` | Natural helper output `(0,0)` | `(250,250,270,270)` remains unchanged across the camera call. | Entry and return prefixes are identical; SHA-256 `1eeaa8ef27359e0c2cedee1ced9d4ac7e78267b98ef57b6f22cc08b5ca4c2c99`. |
| `runtime-axis-x-positive-050` | `(0.5,0)`; bytes `0000003f`, `00000000` | `(261.666656,285,300,-0)` | The full 0x170-byte caller-return prefixes match; SHA-256 `124c5fb2c2eca514ed9eecb75ad9598e0fc089c26abb27dc74c25827dd279695`. |
| `runtime-axis-x-negative-052` | `(-0.5,0)`; bytes `000000bf`, `00000000` | `(238.333328,215,240,180)` | The full 0x170-byte caller-return prefixes match; SHA-256 `6cdb23b64cbb2ad4ea06340e89a0a60587b9d57e67bdf42b0d78c1fadc42de38`. |

At caller entry, all four report pairs have the same 0x170-byte view prefix in original and patched (`0x004BCCd0`, SHA-256 `1eeaa8ef27359e0c2cedee1ced9d4ac7e78267b98ef57b6f22cc08b5ca4c2c99`). For the neutral run, the bytes are unchanged across the call. The sign controls show opposite changes in the selected anonymous float fields, and their complete caller-return view prefixes are byte-identical between original and patched. The fields remain unnamed; these bytes do not prove a rendered camera change, player movement, or any input mapping.

The passive and all three controlled probes report the same 151,088-byte save before and after, SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; all report `save_unchanged=true` and `non_mod_profile_unchanged=true` for both runs.

## Event and sampling drift

The paired event streams are exactly equal for passive probe 049 and positive probe 050. Neutral control 051 reports `post_confirm_events_equal=false` solely because `save_load_process_start` register r3 is `0x8265580` original versus `0x29DF` patched. Its 100 `save_load_samples` are nevertheless identical. Negative control 052 differs at two event registers: `save_load_process_start` r3 is `0xE269` original versus `0x8265580` patched, and `save_load_process_step` r3 is `0x46` versus `0x47`. Its load-work samples also diverge: 70 of 100 indices differ, including five `selected_slot` values and one `work_state` value; state-1/state-2 sample counts differ by one. The report's `save_load_callbacks_equal=false` reflects these sampled records, not a claim that callback identities differ. These mismatches leave a scheduling/phase drift in the broader paired trace. They do not change the captured helper ABI or the byte-equal view prefixes at the camera checkpoints, but they limit whole-run equivalence claims and make the negative probe less isolated from unrelated runtime variation.

## Conclusion and limits

The raw reports support a narrow memory-state finding: at the observed camera caller, neutral outputs leave the captured view unchanged, and injected positive/negative X outputs produce opposite changes in selected view-object fields with byte-for-byte original/patched agreement at the captured checkpoints. The stack output slots and return value are consistent across the pair. This is suitable evidence for an axis-output-to-view-state candidate contract with these observed caller arguments and bounded output values.

It does **not** establish physical controls, movement of a player, a visual-camera response, interaction, or transition behavior. No controlled-response screenshot is present. The negative-run event and load-work sample drift remains an asynchronous-equivalence limitation, and the sampled sign values do not cover the helper's full ABI/domain, edge cases, or other callers.

## Read-only checks

- Packet hash verification: all 13 declared inputs matched.
- Parsed paired report JSON for four runs; recomputed 0x170-byte view-prefix hashes and original/patched byte equality at camera/helper/caller-return checkpoints.
- Compared raw event sequences, 100-entry `save_load_samples`, save snapshots, and profile-integrity flags across each pair.
- Inspected the pinned H4 caller/ABI description and `tools/h3_autonomous_verify.py` output-slot guard; no runtime, build, or code-changing check was run.
