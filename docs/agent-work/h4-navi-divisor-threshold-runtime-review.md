# H4 Navi threshold runtime review

## Disposition

The paired run-007 artifacts support a bounded trigger-route observation: both images hit `0x0039C9E8` and then the small-delta exit `0x0039CA90`; neither reaches the greater-than continuation, accessor, or divide sites in the requested probes. This is partial runtime evidence, not a divisor observation or whole-load equivalence result. The capture report accurately marks the false load/title comparisons and preserves the unresolved differences.

All 24 run-001 review-packet input hashes match. The pinned ARM image `extracted/exefs/code.bin` has SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Runtime/preflight/postflight artifact hashes are:

- `runtime-007/report.json`: `744a753164b3d37cf90087671e596fe971906ce8935bc2e6511e109aef1c72cf`
- `runtime-007/original.json`: `0f685fa565adc3a7d483898a7aa9afaa5b604ef9acbedee46cfbfc402de8ef3d`
- `runtime-007/patched.json`: `80183a04d8cdc1c97d5fd9a9161849416153fac020baa1677ae40053fad9371c`
- preflight: `206571d7c774dd2374b921ed4d7722e504ce88e598818b3690faef7d243ca081`
- postflight: `27c618d8cf62e8e15a23e8231341c3708f094d39681620f5a641fab3327e802b`

## Runner correction and command

The current `tools/h3_autonomous_verify.py` source assigns `navi_callback_call_return_trace` only under `if navi_callback_return_trace`; the CLI exposes the option as `store_true` and requires a callback-entry probe when enabled. Run-007's raw probe entries contain no nested return-trace field, consistent with its recorded command omitting the flag. The integration handoff records runner AST parsing and `--help` checks as exit 0, and the preflight pins runner SHA-256 `0d58c42bc6936895252201b0c60e1fc0849d1870ae415c6e0990466df1e72e0b`.

The runner file is untracked in this checkout (`git status` reports `?? tools/h3_autonomous_verify.py`), so there is no Git-tracked before/after diff to inspect here. The opt-in guard is directly visible in the pinned current source and is consistent with the capture handoff's one-line correction claim, but the old source body itself is not included in this run packet. This is a provenance limitation on independently reconstructing the textual diff, not a mismatch in the new run's CLI or raw evidence.

## Probes and route

The ordered entry/helper/threshold probes hit in both runs on thread 1. At callback entry, original has `r0=0x086EB4C0`, `r3=0x4E44`; patched has `r0=0x086EB3C0`, `r3=0`. In each run, the callback object is its `0x0044CDF0` host pointer plus `0x40`; the different pointer values are profile relocation. The entry object word `+0x10` and float fields `+0x3C/+0x40` decode to zero in both. The callback-entry `r3` difference is present in the raw data and is not characterized by the report; subsequent helper-route registers match.

| Probe PC | Hit/result in both images | `(r0,r1,r2,r3)` where hit |
|---|---|---|
| `0x00399D60` | Hit; callback entry | Different callback pointer as above; raw `r3` also differs (`0x4E44` original, `0` patched). |
| `0x0039C944` | Hit | `(object,1,6,1)` |
| `0x0039C968` | Hit | `(0,1,6,1)` |
| `0x0039C9E8` | Hit | `(0,1,6,1)` |
| `0x0039CA18` | No hit; bounded stop at `0x002A88A8` | No target registers captured. |
| `0x0039CA90` | Hit; thread 1 | `(0,1,6,1)` |
| `0x0039FA70`, `0x0039FA74`, `0x0039CA64`, `0x0039CA7C` | No hits; bounded stops, mostly `0x002A88A8`; patched final `0x0039CA7C` probe stops at `0x00147C34` | No target registers/accessor result/divisor captured. |

The same ordered hit sequence and the static branch layout support the report's bounded small-delta exit claim at `0x0039CA90`; `0x0039CA18` is the greater-than continuation. Entry deltas are zero, which is consistent with the exit, though that entry snapshot is not a second sample taken at the branch itself. No probe captures host `+0x34`, accessor return `s0`, or either divide. The no-hit stops are bounded interrupted waits, not observations of those target instructions.

## Comparison flags and unresolved differences

`report.json` sets `field_scene_semantics_equal`, `field_scene_ticks_both`, `title_entry_registers_equal`, `post_confirm_progress_equal`, `load_complete_acknowledged_both`, `field_manager_reached_both`, `save_unchanged_both`, and `profile_unchanged_both` true. It sets `title_state8_equal`, `save_load_callbacks_equal`, and `post_confirm_events_equal` false. The remaining false control fields concern optional negative controls that were not requested; they should not be treated as failures in this capture.

The raw 160-byte title state-8 snapshots differ at exactly offsets `0x89`, `0x8D`, and `0x91`. Event names and ordering match, but loader pointer/register values differ: at `save_load_io_worker`, `r3` is `0x0873CE00` original versus `0x0873CD00` patched; at `save_file_reader`, `r0` is `0x08718B80` versus `0x08718A00`, and the recorded reader-global pointer bytes differ accordingly. Repeated save/load work snapshots also contain different raw bytes in pointer-bearing areas. The artifacts establish these differences but do not identify their cause. The report appropriately declines full paired load equivalence.

The tick comparison is only the runner-defined bounded three-value field signature, not whole-scene equality. Each run has 250 field tick snapshots and 249 successful subsequent tick statuses. The overall runner status `observed` does not turn the false title/load comparisons into passes.

## Offline gate, integrity, and cleanup

Preflight confirms its 22 target dispatch inputs matched; the current review packet's 24 declared hashes also all match. H3 entry IPS round trip and unchanged bytes outside the replacement window are recorded passed, H3 caller passed with its negative control captured, and H4 direct-reader/camera reports are passed and hash-pinned. These offline reports were reused, not rerun. Candidate and composition runner hashes match their offline report pins.

Preflight records external source save SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` (151,088 bytes); postflight records the same path/size/hash with `matches_preflight=true`. For both staged profiles, before/after save hashes match and both `save_unchanged` and `profile_unchanged` are true. I did not access the private save or profiles. Postflight records an empty Azahar process list, no listening GDB sockets, and one client-side `TIME_WAIT` connection on 54343. No emulator was launched for this review.

Keep this as one partial paired checkpoint: the small-delta exit is observed, while the greater-than path and divisor are not. It establishes no movement, interaction, transition, general divisor domain, or H4 completion. A useful next capture would follow a naturally occurring non-small delta through the threshold branch and accessor/divide sites, with no forced state.
