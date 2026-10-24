# H1 first positive gate with original callback `0x0015555C`

## Result

`tests.test_title_transition_original_callback_experiment` passes. The
experiment starts at `0x001E9FD4` and executes the pinned original ARM image
continuously through the first positive transition body at `0x002872B0`, its
indirect call into original code at `0x0015555C`, and the real TBB help lookup.
It stops at `0x001EA15C`, before `Camp_SetSlotMessage`. The selected help text
is “Start a new game from the beginning.”

Reference `code.bin` SHA-256:
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
`TitleTable.tbb` SHA-256:
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`.
The script and test use the explicit in-worktree copies under
`build/semantic-equivalence/real-assets/`.

## Static callback candidate and executed path

The `0x00155540` code partition contains its own `pop {r4,pc}` at
`0x00155558`; the following original instructions at `0x0015555C..0x00155580`
are the VFP routine used as the callback candidate. The existing source also
contains pointer references to `0x0015555C` in constructor/dispatch data
(`src/engine/leaf_batch29_b.cpp`, `leaf_batch27_b.cpp`, `leaf_batch44_a.cpp`,
and `leaf_batch43_b.cpp`). This is static evidence that it is a real callback
candidate, not proof that the live title asset selects it. In particular, the
type byte/runtime callback target for the title's actual object was not
captured.

For the synthetic path, only the descriptor's callback pointer at
`childB+0x4C+0x4C` was changed from the earlier test stub to `0x0015555C`. No
bytes were installed or patched at the callback address; the callback body and
the rest of the route came from the pinned original ARM image. It executed all
ten PCs from `0x0015555C` through `0x00155580`; the conditional upper-clamp
branch at `0x00155570` was not taken in this case.

## Callback values and effects

Immediately before the `BLX` at `0x002872E4`, the original caller has clamped
the transition input to `s2 = 0.75` and loads the nested values into `s0/s1`.
At callback entry, the recorded state is:

| Value | At callback entry | At `bx lr` (`0x00155580`) |
| --- | --- | --- |
| `r0` | `0x02000C00` | `0x02000C00` |
| `r1` | `0x0015555C` | `0x0015555C` |
| `r2` | `0x6` | `0x6` |
| `r3` | `0xA5A50003` | `0xA5A50003` |
| `r4` | `0x02000A00` | `0x02000A00` |
| `LR` | `0x002872E8` | `0x002872E8` |
| `s0` | `0.5` (`0x3F000000`) | `0.75` (`0x3F400000`) |
| `s1` | `1.0` (`0x3F800000`) | `1.0` (`0x3F800000`) |
| `s2` | `0.75` (`0x3F400000`) | `0.75` (`0x3F400000`) |
| `s3` | `0` | `0.5` (`0x3F000000`) |

The instruction path therefore clamps the supplied `s2` value between the
original lower bound in `s0` and upper bound in `s1`; for this input the result
is unchanged at `0.75`. FPSCR condition flags are updated by the VFP compares
(`0x80000000` at entry and `0x20000000` at the return instruction). The
callback makes no memory writes. The original caller stores returned `s0`
(`0.75`) to nested `+0x38`, copies old `+0x38` (`1.0`) to `+0x3C`, and sets
nested byte `+0x58` to one. The rest of the original transition completes and
the help getter returns the expected TBB string pointer/color.

The path recorded 50 reads and 11 writes, all within the explicitly modeled
work/handle/child/nested graph, TBB regions, stack, global slot, or original
literal pools. The exact trace is generated at
`build/semantic-equivalence/title-transition-original-callback/report.json`.

## Limits

This is an instruction-level test of one explicit synthetic object graph and
finite FP input. Constructor/dispatch pointer data makes `0x0015555C` a
plausible callback candidate, but the live title's type byte and callback
pointer are unknown. It does not prove runtime-normality, renderer behavior,
visible UI, gameplay, or Azahar behavior. It does not enter the second positive
fade helper body `0x0020FFAC` and does not change the byte-exact ledger or
function counts.

## Reproduction

```powershell
python -m unittest tests.test_title_transition_original_callback_experiment -v
python tools/title_transition_original_callback_experiment.py
```
