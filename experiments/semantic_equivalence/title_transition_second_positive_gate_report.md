# H1 title transition: second positive fade gate

## Result and evidence

`tests.test_title_transition_second_positive_gate_experiment` passes. A single
Unicorn machine executes the pinned US ARM image continuously from
`0x001E9FD4` through both positive transition-helper bodies and original TBB
help lookup, stopping immediately before `Camp_SetSlotMessage` at
`0x001EA15C`. The selected help text is “Start a new game from the beginning.”

The binary SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the real
`TitleTable.tbb` SHA-256 is
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`. Inputs
are read from the explicit in-worktree `build/semantic-equivalence/real-assets`
copies. The earlier positive-gate runner was not changed; this experiment
reuses its synthetic work/object initializer and adds a separate indexed table
and second callback.

## Indexed lookup into the second positive body

`childB+0x58 = 1` makes `0x0020FFA0` fall through into its original body at
`0x0020FFAC`. The synthetic graph is:

```text
childB + 0x2C -> descriptor 0x02000A00
descriptor + 0x148 = 1
descriptor + 0x28  -> metadata 0x02000C20
descriptor + 0x14C = 1
metadata + 0x28 = stride 1
metadata + 0x1C  -> table base 0x02000C60
table[1]         -> record 0x02000D00
```

The original lookup reads these effective addresses in order:

| ARM PC | Effective address | Use |
| --- | --- | --- |
| `0x0020FFB0` | `0x0200062C` | child B `+0x2C` descriptor pointer |
| `0x0020FFB8` | `0x02000B48` | descriptor `+0x148` positive gate |
| `0x0020FFC4` | `0x02000A28` | descriptor `+0x28` metadata pointer |
| `0x0020FFC8` | `0x02000B4C` | descriptor `+0x14C` index |
| `0x0020FFCC` | `0x02000C48` | metadata stride |
| `0x0020FFD0` | `0x02000C3C` | table base |
| `0x0020FFD8` | `0x02000C64` | selected `table[index * stride]` pointer |

The table addressing uses `base + (index * stride * 4)`. For index 1 and stride
1, the original load selects record pointer `0x02000D00`. This setup is
synthetic and proves only that the original lookup and body execute for this
graph.

## BLX observations and stub contract

The original second-body call is `BLX r1` at `0x00210010`. The selected record
contains callback `0x01000120`, argument object `0x02000E00`, `+0x44 = 0.25`,
`+0x48 = 0.6`, and old `+0x38 = 0.9`. With outer input `s16 = 0.75`, original
instructions clamp to 0.6 for `s2`, then load callback inputs into `s0/s1`.
At the callback boundary:

| Register | Observed value | Meaning in this trace |
| --- | --- | --- |
| `r0` | `0x02000E00` | record `+0x50` argument object |
| `r1` | `0x01000120` | synthetic callback target |
| `r2` | `0` | value left by original table helper |
| `r3` | `1` | table stride retained by original code |
| `r4` | `0x02000D00` | selected record |
| `LR` | `0x00210014` | original continuation after `BLX` |
| `s0` | `0.25` (`0x3E800000`) | record `+0x44` |
| `s1` | `0.6` (`0x3F19999A`) | record `+0x48` |
| `s2` | `0.6` (`0x3F19999A`) | clamped incoming value |
| `s3` | `0` (`0x00000000`) | additionally observed, not used as an argument here |

The second callback was invoked once. Its isolated stub is one ARM instruction,
`bx lr` (`0xE12FFF1E`), and therefore preserves the recorded registers/FP
values and performs no memory writes. The earlier first-positive helper also
runs once with its own `bx lr` stub, preserving that experiment's callback
contract. Neither stub is asserted to be the game's actual callback or to
represent its behavior.

## Memory effects

There were 65 reads, all within the explicit work/handle/child/descriptor,
metadata, table, record, TBB, stack, manager-slot, or literal-pool regions. No
read fell outside the declared model. Sixteen writes were recorded: twelve
original data writes and four original stack-save writes (each helper pushes
`r4,lr` to the same two stack addresses). The synthetic callback stubs wrote
zero bytes.

The selected record changes are `+0x38 = 0.25` from callback `s0`, `+0x3C =
0.8999999761581421` (the old binary32 `+0x38`), and byte `+0x58 = 1`. The outer
mutator then sets descriptor byte `+0x1F6 = 1` and `work+0x94 = 1`. The trace
also preserves the prior first-helper effects, including nested B `+0x38 =
0.5` and `+0x58 = 1`.

The TBB caller reaches `0x001EA15C` with the expected string pointer
`r0=0x02001046` and color `r1=0x323232FF`; the presentation callee is not
entered. No renderer, Azahar, gameplay, or runtime-normal claim follows from
this synthetic execution. The byte-exact function ledger and function counts
are unchanged.

## Reproduction

From the worktree root:

```powershell
python -m unittest tests.test_title_transition_second_positive_gate_experiment -v
python tools/title_transition_second_positive_gate_experiment.py
```

The JSON trace is written under the ignored
`build/semantic-equivalence/title-transition-second-positive-gate/report.json`.
