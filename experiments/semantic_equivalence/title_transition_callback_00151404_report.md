# H1 first positive gate with alternate callback `0x00151404`

## Result

`tests.test_title_transition_callback_00151404_experiment` passes. One
Unicorn machine executes the pinned original ARM continuously from
`0x001E9FD4`, through the first positive transition body, callback candidate
`0x00151404`, its reached direct callees, and the original TBB help lookup. It
stops at `0x001EA15C`, before `Camp_SetSlotMessage`. The selected help string
is “Start a new game from the beginning.”

The pinned US `code.bin` SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the real
`TitleTable.tbb` SHA-256 is
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`. The
runner uses explicit copies in the worktree's `build/semantic-equivalence/real-assets`
directory. It reuses the prior positive-gate initializer and changes only the
callback pointer field to `0x00151404`.

## Static association and limits

The pointer `0x00151404` appears alongside `0x0015555C` in static callback /
constructor data, including source partitions in `leaf_batch27_b.cpp`,
`leaf_batch29_b.cpp`, and `leaf_batch44_a.cpp`. This makes it a registered
type-1 callback candidate. The experiment does **not** read the live title
asset's type byte or observe the title's runtime callback pointer; static type
association is not proof this menu object uses it.

No replacement callback code or stub was installed. All reached callback and
direct-callee instructions execute from the pinned image. For these finite
inputs, the path inside `0x00151404` branches at `0x00151434` to `0x00151450`;
it skips the earlier `0x002A337C` call and then invokes the original routine at
`0x0014D608`. That routine reaches original helper `0x0015258C` and returns.
The exceptional indirect `BLX` path at `0x0014D6CC` (`0x002A464E`) is not
reached. This bounds coverage to the recorded input path; it is not a full
contract for every callback input.

## Observed ABI, output, and effects

At callback entry, the caller supplied:

| Register | Value |
| --- | --- |
| `r0` | `0x02000C00` |
| `r1` | callback address `0x00151404` |
| `r2` | `0x6` |
| `r3` | `0xA5A50003` (caller residue, not claimed as an argument) |
| `r4` | `0x02000A00` |
| `LR` | `0x002872E8` |
| `s0` | `0.5` (`0x3F000000`) |
| `s1` | `1.0` (`0x3F800000`) |
| `s2` | `0.75` (`0x3F400000`) |

The actual callback code returns with `s0 = 0.75` (`0x3F400000`), and the
original transition caller observes that same value. The callback makes no
object/data writes; it does save `r4,lr` and `d8,d9` on its stack frame. Its
direct callee `0x0014D608` also preserves its frame (`r4,lr,d8-d10`) and
executes original helper `0x0015258C`. The captured helper inputs at
`0x0015258C` include `r0=0x3E800000` and `r1=0x3F000000`; the return is
observed at `0x0014D670`. The callback then returns to `0x002872E8`, where the
original caller stores the result to nested `+0x38`, copies prior `+0x38` to
`+0x3C`, and sets byte `+0x58`.

The trace recorded 62 reads and 20 writes. Reads were within the initialized
synthetic object/TBB graph, stack, original literal constants, and TBB manager
slot. Writes include the outer transition, callback/callee stack frames, and
the caller's nested-state updates. No read fell outside the declared model.
At the help boundary, the expected TBB pointer is in `r0` and color
`0x323232FF` is in `r1`; the presentation routine was not entered.

## Reproduction and evidence file

```powershell
python -m unittest tests.test_title_transition_callback_00151404_experiment -v
python tools/title_transition_callback_00151404_experiment.py
```

Full PC, register, FP, read, and write traces are emitted to the ignored
`build/semantic-equivalence/title-transition-callback-00151404/report.json`.
This is a synthetic instruction-level path only: no runtime-normality, live
callback selection, visible UI, renderer, gameplay, or Azahar result is
established. The function ledger/count is unchanged.
