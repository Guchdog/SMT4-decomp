# H4 Navi threshold and divisor runtime capture

## Offline gate and runner correction

The original/patched pair used the pinned `code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) and isolated profiles at `C:\H4NaviProfile`. Before launching Azahar, all 22 dispatch packet input hashes matched. The accepted offline H3 entry/caller and H4 direct-reader/camera reports remained at their pinned hashes; H3 entry confirms the IPS round trip and unchanged bytes outside the replacement window, and the H3 caller report retains its passed caller checks and negative control. These reports were reused, not rerun. Current H4 candidate and runner hashes also match the source/tool values in the offline reports. See `checks/preflight.json`.

This run includes a one-line runner correction: `navi_callback_call_return_trace` is now captured only when its documented `--navi-callback-return-trace` option is set. The option was omitted in this runtime command, and the raw records contain no nested return trace. Runner AST parsing and `--help` both succeeded. The correction changes debugger instrumentation only; game image, C++ candidate, callbacks, and passive memory/register observations remain unchanged.

Source save `E:\emulador3ds\sdds4game1.sav` was 151,088 bytes and SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` before and after the pair. Both staged saves had that same hash before and after; both tracked profile manifests remained unchanged. No axis override, physical input, synthetic game-state change, or guest/register writes were used at the probes. The normal title-load confirmation seam was used.

## Paired route observations

Command: `python tools/h3_autonomous_verify.py --output build/agent-work/H4-semantic/h4-navi-divisor-threshold-runtime-capture/001/checks/runtime-007 --profile-root C:\H4NaviProfile --callbacks 250 --confirm-load --post-callbacks 60 --field-ticks 250 --field-probe-address 0x00399D60 --field-probe-address 0x0039C944 --field-probe-address 0x0039C968 --field-probe-address 0x0039C9E8 --field-probe-address 0x0039CA18 --field-probe-address 0x0039CA90 --field-probe-address 0x0039FA70 --field-probe-address 0x0039FA74 --field-probe-address 0x0039CA64 --field-probe-address 0x0039CA7C --timeout 90`.

In both profiles the four callback/helper entry stops hit in order on GDB thread 1: `0x00399D60 → 0x0039C944 → 0x0039C968 → 0x0039C9E8`. The callback object was `0x086EB4C0` in original and `0x086EB3C0` in patched; each equals the corresponding `0x0044CDF0` host pointer plus `0x40`. At entry, word `+0x10=0` and floats `+0x3C/+0x40=0.0` in both. At `0x0039C944`, `(r0,r1,r2,r3)=(object,1,6,1)`; at `0x0039C968` and `0x0039C9E8`, `(r0,r1,r2,r3)=(0,1,6,1)` in both.

The requested `0x0039CA18` probe did not hit in either run; each bounded wait was interrupted at `PC=0x002A88A8`, thread 1. The next probe, `0x0039CA90`, hit in both runs with `(r0,r1,r2,r3)=(0,1,6,1)`. In the reviewed static flow, `0x0039CA90` is the small-delta exit target of `BLE` at `0x0039CA14`, while `0x0039CA18` is the continuation when the absolute delta exceeds `0.5`. Thus this invocation directly observed the small-delta exit route after entering the threshold block. The raw callback snapshot’s zero deltas are consistent with that stop.

Neither `0x0039FA70`/`0x0039FA74` nor divide instructions `0x0039CA64`/`0x0039CA7C` hit in either profile; each was a bounded no-hit interrupted at `PC=0x002A88A8` (one final patched probe stopped at `0x00147C34`). No host `+0x34` bytes, accessor return value, or divisor was observed. The next task should stop before or at the threshold conditional and inspect the natural source of those deltas if the goal is to reach a non-small delta; do not force them.

## Paired comparison and limits

Each run reached the field manager and recorded 250 tick snapshots plus 249 successful tick statuses. The runner’s bounded field signature/tick comparison is equal, as are title-entry registers, load-complete acknowledgement, post-confirm progress, and save/profile integrity. However, `title_state8_equal`, `save_load_callbacks_equal`, and `post_confirm_events_equal` are false in `report.json`. The raw differences include three state-8 bytes and later loader registers/pointer fields (for example the save I/O worker’s `r3` buffer address differs); their cause is not established here. Therefore this is not evidence of full paired load-path equivalence. The identical Navi stops establish only that both sampled invocations reached the small-delta exit in this checkpoint.

The overall runner status is `observed`. These results do not establish movement, interaction, zone transition, accessor/divide behavior, a general divisor domain, or H4 completion. After both runs, Azahar was absent, no GDB port was listening, and the external save hash was unchanged; persistent raw hashes and cleanup are in `checks/postflight.json`.
