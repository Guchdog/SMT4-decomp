# H4 Navi divisor trigger runtime review

## Disposition

The paired raw artifacts support the bounded ordered checkpoint claim in the integration report: each run hit `0x00399D60`, `0x0039C944`, `0x0039C968`, and `0x0039C9E8` in that order, with matching register values between original and patched. The clear-entry-bit route reaches the threshold block. The evidence does not show the threshold branch destination, either accessor, either divide, or a divisor value. The review is acceptable as partial runtime evidence, with a reproducibility/reporting caveat for the auxiliary callback-return trace described below.

All 24 packet input hashes match. The pinned original image is `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The paired raw files are pinned as follows:

- `report.json`: `62e2adc340be70c5eca9cd77e0e98834a54b9c845b2f6c99f39f27b00b5df96c`
- `original.json`: `bd4109aca7a85cb8b484b31c4fe25631ec9f0b6423998cc0d628491f7e36c40e`
- `patched.json`: `d44a1d6a5adf41cb7675a751b61123d7ce3aea58ae6eae4a7463a41f5daeb152`
- preflight: `88b639ecf701f9fc8012b31c71ff57deda7600c6c26b7635d84b875dcaa3bbdc`
- postflight: `340dc9d4ec136499ff5dcbdef2f4c5eeaef9ee372aae727219bcbfff93dfdff4`

## Probe and route evidence

In both raw runs, all four `field_call_probes` records have `hit=true`, `pc` equal to the requested `address`, and stop replies identifying GDB thread 1. The captured `(r0,r1,r2,r3)` values agree exactly across images:

| PC | Registers | Bounded inference |
|---|---|---|
| `0x00399D60` | `(0x086EB3C0, 0, 0x00399D60, 0)` | Callback entry with object pointer `0x086EB3C0`. |
| `0x0039C944` | `(0x086EB3C0, 1, 6, 1)` | The same object pointer reaches helper entry; LR is `0x00399DAC`, a return site in the callback. |
| `0x0039C968` | `(0, 1, 6, 1)` | The helper route test is reached with the entry bit clear. |
| `0x0039C9E8` | `(0, 1, 6, 1)` | The clear-bit route reaches the threshold block in this sample. |

At callback entry, the raw snapshot has host slot `0x0044CDF0 -> 0x086EB380`, callback object `0x086EB3C0`, table pair `[0x00399D60, 0]`, object word `+0x10 = 0`, and float words at `+0x3C/+0x40` equal to zero. This is consistent with the static trigger recon: a clear entry bit branches directly to `0x0039C9E8` and compares the already stored deltas. Reaching that block does not reveal the comparison outcome or establish whether execution continues to `0x0039CA38` or the coordinate route. There are no hits here at an accessor or divide.

The runner records 250 field-tick snapshots and 249 subsequent tick statuses in each image. `field_scene_semantics_equal` is the runner’s bounded three-value signature equality, not equality of all scene state. Load-complete acknowledgement, field-manager reach, the listed save/load callbacks, progress/event signatures, and the bounded field tick signature compare equal. The overall paired report is `observed`; optional negative-control flags are false because those controls were not requested. This is a single paired checkpoint scenario, not H4 completion, movement, interaction, or transition evidence.

## Auxiliary trace and command provenance caveat

Both raw `0x00399D60` probe records contain `navi_callback_call_return_trace` with status `unexpected_stop` and one event at the entry PC; this auxiliary trace did not observe callback return/dispatch events. Review of the pinned runner explains the result: it emits this field unconditionally for the callback-entry probe. The command correctly omits `--navi-callback-return-trace`; that option only clears the entry breakpoint before starting the nested trace. Without it, the entry breakpoint remains armed and the nested continuation immediately hits it again. This is not callback-return evidence and is excluded from the route claims. The separate ordered `field_call_probes` records remain valid: they hit each requested helper/threshold PC, retain the same object pointer at callback/helper entry, and show LR `0x00399DAC` at helper entry. No command-line mismatch remains.

## Offline gate, integrity, and cleanup

The frozen preflight pins the original image, runtime runner, camera/input candidates and composition runners, and four offline reports. Their expected and actual hashes agree. Those reports state H3 entry/caller and H4 direct-reader/camera checks passed; this runtime task reused them and did not rerun them. This is evidence that the declared offline gate was current for the capture, not a new independent differential run.

Preflight records the external source save `E:/emulador3ds/sdds4game1.sav` as 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. Persisted postflight records the same path, size, and SHA with `matches_preflight=true`. For each staged original/patched profile, pre/post save hashes match that value, and `save_unchanged` and `profile_unchanged` are true. This review did not read the private profile or save. Postflight records no Azahar process and no listening GDB port on 54342/54343; only a closed TIME_WAIT connection is noted.

No emulator was launched for review. The evidence is limited to the existing run artifacts. The next capture should record the threshold comparison’s outgoing branch and accessor/divide entries/returns with register and `s0` values, while retaining explicit no-hit/timeouts. No movement, interaction, transition, divisor-domain, or whole-game equivalence claim is supported here.


## Run-002 correction check

The refreshed packet pins 24 inputs and all 24 hashes match. The updated integration report hash is `abd38d7e512103d7c6687ec0d9580bcf43aa990ff9942cd0ca32f709e9f69000`; updated postflight hash is `b0f4cd80cae27e499ee622c440c5df38e76311f31464798a12e6b23d52032ff6`. The report’s command is unchanged and its explanation of the unconditional auxiliary trace matches the runner implementation. The runtime route claims correctly exclude that failed nested return trace. The refreshed postflight makes process absence and absence of matching/listening sockets explicit at the audit time, while preserving the client-side `TIME_WAIT` note. Preflight and postflight external source-save SHA values still match, as do original/patched staged save hashes before/after and profile manifests. No private profile/save access or runtime rerun was performed for this check. The partial-evidence conclusion and remaining need to observe the threshold outcome and accessor/divide sites are unchanged.
