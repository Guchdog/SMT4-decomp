# H1 synthetic readiness-to-help path report

This is a bounded execution of original ARM in Unicorn, not a C++ candidate or
an emulator/gameplay observation. It begins at `0x001E9FD4`, continuously
executes both original readiness helpers, branches to the help caller at
`0x001EA12C`, executes the original TBB getters using the real
`TitleTable.tbb`, and stops immediately before the `BL` at `0x001EA15C` to
`Camp_SetSlotMessage` (`0x0029F10C`). It adds no function to either progress
count.

## Synthetic setup and outcome

For each selection 0..3, the isolated machine maps a valid work block, handle,
and child object and explicitly sets:

- `work+8 = selection`, `work+0x8C = handle`, `work+0x94 = 1`;
- `handle+8 = child`, signed `child+0x34 = 0`, signed `child+0x58 = 0`;
- the real title TBB container at `0x02000100`, with global title slot `0x3A`
  (`0x00493BD0`) pointing to it;
- `r4 = r5 = work` for the two register aliases used by this bounded
  mid-callback window.

All four cases passed and stopped at `0x001EA15C`. The synthetic predicates
return nonzero and `work+0x94` takes the direct help branch; the transition
mutation block at `0x001EA070` is skipped. Before the stop, ARM had prepared:

| Selection | `r0` string pointer | `r1` RGBA | Selected real TBB string |
| ---: | ---: | ---: | --- |
| 0 | `0x02000146` | `0x323232FF` | `Start a new game from the beginning.` |
| 1 | `0x0200019C` | `0x323232FF` | `Load a saved game and continue playing.` |
| 2 | `0x020001F2` | `0x323232FF` | `Configure audio settings.` |
| 3 | `0x02000248` | `0x323232FF` | `Download additional content.` |

Each case followed this exact same sequence of 73 instruction PCs (and stopped
before executing the instruction at the last address):

```text
0x1e9fd4, 0x1e9fd8, 0x1e9fdc, 0x25a274, 0x25a278, 0x25a27c, 0x25a2ac,
0x25a2b0, 0x1e9fe0, 0x1e9fe4, 0x1e9fe8, 0x1e9fec, 0x1e9ff0, 0x1e9ff4,
0x2d569c, 0x2d56a0, 0x2d56a4, 0x2d56f4, 0x2d56f8, 0x1e9ff8, 0x1e9ffc,
0x1ea000, 0x1ea004, 0x1ea008, 0x1ea00c, 0x1ea010, 0x1ea12c, 0x1ea130,
0x1ea134, 0x1ea138, 0x2c0ec4, 0x2c0ec8, 0x2c0ecc, 0x2c0ed0, 0x2c0ed4,
0x2c0ed8, 0x2ac2f4, 0x2ac2f8, 0x2ac2fc, 0x2ac300, 0x2ac304, 0x2ac308,
0x2ac30c, 0x2ac310, 0x2ac314, 0x2ac318, 0x2ac31c, 0x2ac320, 0x2ac324,
0x2ac328, 0x2ac32c, 0x2ac330, 0x2ac334, 0x2ac338, 0x2ac33c, 0x2ac344,
0x1ea13c, 0x1ea140, 0x1ea144, 0x2c0e9c, 0x2c0ea0, 0x2c0ea4, 0x2c0ea8,
0x2c0eac, 0x2c0eb0, 0x2c0eb4, 0x2c0ebc, 0x1ea148, 0x1ea14c, 0x1ea150,
0x1ea154, 0x1ea158, 0x1ea15c
```

Observed helper entry order and complete `r0-r3` tuples were:

| Entry | `r0, r1, r2, r3` | `LR` |
| --- | --- | ---: |
| `0x0025A274` readiness helper 1 | `0x02000D00, 0xA5A50001, 0xA5A50002, 0xA5A50003` | `0x001E9FE0` |
| `0x002D569C` readiness helper 2 | `0x02000D00, 0x00000000, 0xA5A50002, 0xA5A50003` | `0x001E9FF8` |
| `0x002C0EC4` global subtable getter | `0x0000003A, 0x00000000, 0xA5A50002, 0xA5A50003` | `0x001EA13C` |
| `0x002AC2F4` subtable getter (tail branch) | `0x02000100, 0x00000000, 0x0049382C, 0xA5A50003` | `0x001EA13C` |
| `0x002C0E9C` payload getter | `0x02000120, 0x314C4254, 0x314C4254, 0x00000020` | `0x001EA148` |

The pre-call boundary tuples `(r0, r1, LR)` were `(0x02000146, 0x323232FF,
0x001EA148)`, `(0x0200019C, 0x323232FF, 0x001EA148)`, `(0x020001F2,
0x323232FF, 0x001EA148)`, and `(0x02000248, 0x323232FF, 0x001EA148)` for
selections 0 through 3 respectively. The machine-readable report at
`build/semantic-equivalence/title-transition-ready-path/report.json` also
records every individual read address, size, PC, and value for each case.

The complete read footprint consists of 20 accesses (17 distinct starting
addresses): work fields `0x0200088C` (twice), `0x02000894`, `0x02000808`;
handle `0x02000C08` (twice); child fields `0x02000D34`, `0x02000D58`; title
slot pointer `0x00493BD0`; TBB words `0x02000100`, `0x02000104`, `0x02000108`,
`0x0200010C`, `0x02000120` (the last twice); and original-code literal words
`0x001E9EC4`, `0x002C0EDC`, `0x002AC348`, `0x002AC34C`, `0x002C0EC0`.
There were no writes on this path. The machine checks fail if any read escapes
the modeled work/handle/child graph, actual TBB/global slot, or those exact
ROM literal addresses.

## Reproduction and boundary

```powershell
python -m unittest tests.test_title_transition_ready_path_experiment -v
python tools/title_transition_ready_path_experiment.py
```

Both original readiness helper entries and original TBB getter entries were
reached; the `0x001EA070` block and `Camp_SetSlotMessage` were not entered.
This does not establish that the synthetic field values are runtime-normal,
that the full transition works, that text is rendered, or that Azahar displays
this state. No production source, ledger, README/MODLOG, ROM, or Azahar data
was changed.
