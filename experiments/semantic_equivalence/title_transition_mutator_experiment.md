# H1 title transition mutator: continuous ARM path

This experiment extends the synthetic readiness-to-help path through the
previously uncovered `0x001EA070..0x001EA128` mutator, then through the original
title help/TBB getter window. It uses the pinned US `code.bin` and the real
`TitleTable.tbb`. It stops immediately before `Camp_SetSlotMessage` at
`0x001EA15C`; no rendered UI or Azahar behavior is claimed.

## Result

`tests.test_title_transition_mutator_experiment` passes. One Unicorn machine
executes 111 original ARM PCs continuously from `0x001E9FD4` through the help
caller boundary. Both readiness functions return nonzero from their signed
field `<= 0` early exits, so `work+0x94=0` reaches the mutator. Both transition
fade helpers are entered and take their own `<= 0` early returns. The two
conditional `0x0029BDB4` calls are skipped by explicitly seeded handle bit 4.
No indirect callback is called or stubbed on this route.

The real table selects “Start a new game from the beginning.” The ARM caller
arrives at the presentation boundary with `r0=0x02001046` (the selected string
pointer) and `r1=0x323232FF` (the color argument). The presentation callee is not
entered.

## Explicit synthetic graph

The data block is based at `0x02000000`. Work is at `+0x100`; handles A/B at
`+0x300/+0x340`; children A/B at `+0x400/+0x600`; and their nested objects at
`+0x800/+0xA00`. `work+8=0` selects the first help string. `work+0x94=0`
selects the transition branch. Child A has signed `+0x34=0`, `+0x58=0`, and a
valid nested pointer at `+0x2C`; those early exits make readiness results
nonzero while avoiding deeper unmodeled object reads. Child B has the same
minimal fields, so the fade helpers return before entering their indirect
callback bodies. `s16=0.75` and `s17=0.25` are explicitly seeded finite values.

Handle A starts with bit 4 set (`flags=4`), skipping the first conditional
`0x0029BDB4` call; the mutator ORs bit 2. Handle B starts with bit 4 clear
(`flags=0`), skipping the final conditional call; the mutator clears bit 2.
These choices establish a narrow executable path, not live-game flag values.

## Observed memory accesses

All 38 reads were inside the explicit work/handle/child/TBB object graph or
the original code's literal pools. The table lists each PC and effective
address; all accesses are 4-byte reads except `0x001EA004`, a byte read.
The runner rejects reads outside these explicit ranges/literal addresses and
checks the full six-write sequence, including each PC, width and value.

| PC | Read addresses |
| --- | --- |
| `0x001E9FD4` | `0x0200018C` |
| `0x001E9FD8` | `0x02000308` |
| `0x0025A274` | `0x02000434` |
| `0x001E9FEC` | `0x0200018C` |
| `0x001E9FF0` | `0x02000308` |
| `0x002D569C` | `0x02000458` |
| `0x001EA004` | `0x02000194` (byte) |
| `0x001EA070` | `0x0200018C` |
| `0x001EA074`, `0x001EA0A8` | `0x02000300` |
| `0x001EA09C` | `0x0200018C` |
| `0x001EA0B4` | `0x02000308` |
| `0x001EA0B8` | `0x0200042C` |
| `0x001EA0C4`, `0x001EA0D0`, `0x001EA0E0`, `0x001EA0FC` | `0x02000190` |
| `0x001EA0C8`, `0x001EA0D8`, `0x001EA0F0` | `0x02000348` |
| `0x002872A4` | `0x02000634` |
| `0x0020FFA0` | `0x02000658` |
| `0x001EA0E4`, `0x001EA100` | `0x02000340` |
| `0x001EA0F4` | `0x0200062C` |
| `0x001EA12C` | `0x02000108` |
| `0x002C0EC8` | `0x002C0EDC` (code literal) |
| `0x002C0ED0` | `0x00493BD0` (TBB manager slot) |
| `0x002AC2FC` | `0x02001000` |
| `0x002AC300` | `0x002AC348` (code literal) |
| `0x002AC30C` | `0x02001008` |
| `0x002AC31C` | `0x02001004` |
| `0x002AC320` | `0x0200100C` |
| `0x002AC330` | `0x02001020` |
| `0x002AC334` | `0x002AC34C` (code literal) |
| `0x002C0EA4` | `0x02001020` |
| `0x002C0EA8` | `0x002C0EC0` (code literal) |
| `0x001EA154` | `0x001E9EC4` (code literal) |

Exactly six writes occurred:

| PC | Address | Width | Value | Meaning |
| --- | --- | --- | --- | --- |
| `0x001EA0B0` | `0x02000300` | 4 | `0x6` | Handle A flags: OR bit 2 |
| `0x001EA0BC` | `0x020009F6` | 1 | `0x00` | Nested A transition byte |
| `0x001EA0C0` | `0x02000198` | 4 | `0x3F400000` | `work+0x98 = 0.75` from live `s16` |
| `0x001EA0EC` | `0x02000340` | 4 | `0x0` | Handle B flags: clear bit 2 |
| `0x001EA0F8` | `0x02000BF6` | 1 | `0x01` | Nested B transition byte |
| `0x001EA128` | `0x02000194` | 1 | `0x01` | Set `work+0x94` |

No other memory writes occurred between callback entry and the pre-presentation
boundary. The TBB slot pointer was installed before execution and is excluded
from the observed callback write trace.

## Limits and next increment

This proves instruction-level reachability and the listed effects for one
explicit synthetic early-return branch only. It does not establish that the
object graph, readiness values, handle bits, or FP inputs occur in live title
execution. It does not exercise either positive-gate fade body, the conditional
`0x0029BDB4` calls, dynamic `BLX` callbacks, alternate transition branches,
physical controls, text rendering, or Azahar.

Next useful step: obtain or derive a runtime-normal object/flag/FP snapshot for
the positive-gate fade-body route, then trace its real indirect callback
targets and side effects. Keep those hooks out of equivalence claims until
their contracts are independently established.
