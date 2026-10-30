# H4 Navi divisor: paired passive sample attempt

## Scope and offline-first gate

Used the pinned original and H3-patched images with the isolated `C:\H4NaviProfile` original/patched profiles. The source save SHA-256 was `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` before and after the paired run. The standard controlled title-load seam acknowledged the load-complete dialog. No axis override or physical input was used, and the two divisor probes did not write guest memory or registers.

Before Azahar, the task packet's pinned reference image (`code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`), `tools/h3_autonomous_verify.py` (SHA-256 `55186f05971cabf5abeb6d3c1a5d2ef6c518799785503462e305c672e99a8cbb`), and all four reusable offline H3/H4 reports matched their frozen hashes. The current axis candidate, direct runner and camera composition runner also matched the source/tool hashes recorded by the passing offline reports. The reused evidence covers H3 image/placement and caller composition, H4 direct reader differential, and bounded field-camera caller composition; these checks were not rerun in this sample task.

## Paired observation

Command: `python tools/h3_autonomous_verify.py --output build/agent-work/H4-semantic/h4-navi-divisor-runtime-sample/001/checks/runtime-005 --profile-root C:\H4NaviProfile --callbacks 250 --confirm-load --post-callbacks 60 --field-ticks 250 --field-probe-address 0x0039FA70 --field-probe-address 0x0039FA74 --timeout 90`.

Both profiles acknowledged the controlled title-load confirmation, reached the field manager and completed the recorded 250-tick checkpoint (initial observation plus 249 tick returns). The runner reports equal title/load/callback/progress and field-scene comparison fields for this scenario. Both per-run staged save hashes were unchanged at the source-save hash above; both per-run non-mod profile manifests were unchanged.

The passive probes did **not** hit either `0x0039FA70` (the `VLDR s0,[r0,#0x34]` instruction) or `0x0039FA74` (`BX lr`) in either profile. Each address probe timed out in its bounded continuation and was interrupted by GDB at `PC=0x002A88A8` on thread 1. No target-entry registers were captured. Consequently neither run read host+`0x34`, captured the divisor bits, nor proved that the Navi callback or divisor branch was reached in this particular run. The timeout PC is recorded only as the interrupt location; it is not attributed to a helper or interpreted as a game-state result. The earlier accepted run-004 callback trace is separate evidence and does not fill this sample's missing divisor observation.

That earlier run-004 does provide a plausible bounded explanation for the neutral checkpoint: its accepted callback trace records callback-object `+0x10=0` and float fields `+0x3C/+0x40=0` at entry, with the sampled object prefix unchanged through the callback. In the reviewed `0x0039C944` body, the bit-clear path compares those fields against `0.5` and reaches `0x0039FA68` only if at least one exceeds the threshold. The zero snapshot is consistent with taking the early exit, but it remains prior-run state and not an internal branch trace from this new capture.

The paired scenario comparison reports equal title entry/state, save-load callbacks, post-confirm events/progress, field-manager reachability, field-scene signature/ticks, save hash and profile integrity. These results validate the checkpoint replay and cleanup, not helper reachability or a finite/nonzero divisor domain. After both runs, no Azahar process or listening GDB port remained; only a closed-connection `TIME_WAIT` entry was visible.

## Interpretation and next evidence

This is a **bounded no-hit result**, not a runtime divisor value. It does not contradict the static initializer's straight-line store of `1.0f` at host+`0x34`, but it also does not establish that initializer or value for the runtime object in this run. Keep `0x0039FA68`'s candidate contract blocked on global-slot/host lifetime and numeric edge behavior. The next useful step is to identify a naturally reachable callback state that satisfies the helper's existing branch conditions, then trace callback entry and the accessor/divide sites together. Do not force object flags or divisor memory without a separately supported contract and read-back controls.
