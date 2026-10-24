# H1 second gate: synthetic original-callback candidate comparison

## Result

`tests.test_title_second_gate_candidate_experiment` passes all three tests.
The new isolated runner executes the original pinned ARM code continuously
through the first positive helper, the second positive body at `0x0020FFAC`,
one explicitly selected original callback candidate at `0x00210010`, and the
original TitleTable lookup. It stops at `0x001EA15C`, before the presentation
callee. Each candidate was run in a fresh Unicorn machine and in a separate
invocation. No production source, shared runner, existing test, or function
ledger was changed.

The two candidate scenarios produce distinct track-state values:

| Explicit candidate in synthetic record | Callback path | Returned `s0` | Selected record `+0x38` after helper |
| --- | --- | ---: | ---: |
| `0x0015555C` (default/type-0 candidate) | Ten original instructions; no callback writes | `0.6` | `0.6` |
| `0x00151404` (type-1 candidate) | Original callback plus `0x0014D608` and `0x0015258C` | `0.25` | `0.25` |

Both scenarios reach the same real TBB text, “Start a new game from the
beginning.” This is only a downstream control-flow check; it does not show
rendering or prove either callback is selected by the live title.

## Explicit synthetic setup and evidence

The indexed table selects one synthetic track record with callback argument
`0x02000C00`, initial current value `0.9`, parameters `+0x44 = 0.25` and
`+0x48 = 0.6`, and incoming `s2 = 0.75` (clamped by the original helper to
`0.6`). Only the record's callback pointer changes between runs. The first
positive helper still uses its prior bounded `bx lr` prerequisite stub; the
candidate at the second call is never stubbed or patched, and its instructions
are read from the pinned original image.

The type-0 candidate clamps the incoming value to the `[0.25, 0.6]` interval,
returning `0.6` without memory writes. The type-1 candidate reaches its
original direct callees `0x0014D608` and `0x0015258C`, returns `0.25` for this
finite input, and writes only to its modeled stack frame. It does not reach
the exceptional indirect target `0x002A464E` in this scenario.

| Candidate | Reads | Total writes | Candidate callback writes | Out-of-model reads |
| --- | ---: | ---: | --- | ---: |
| `0x0015555C` | 65 | 16 | none | 0 |
| `0x00151404` | 77 | 25 | stack only | 0 |

All data writes are constrained to the declared transition-state addresses or
the stack frame `0x8000FC0..0x8000FFFF`. Both runs reach the help boundary with
the expected real TBB pointer/color and stop before `Camp_SetSlotMessage`.

Reference `code.bin` SHA-256:
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
`TitleTable.tbb` SHA-256:
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`.

## Limits and reproduction

Both the selected track record, its argument object, and the callback pointer
are explicit synthetic state. This experiment compares two plausible original
callees; it does not determine which pointer/title resource is used at runtime,
establish functional equivalence, or claim an Azahar result. The first helper's
stub remains a deliberately isolated prerequisite. No emulator/save state or
ROM bytes are modified.

Run the tests with:

```powershell
python -m unittest tests.test_title_second_gate_candidate_experiment -v
```

Or run either scenario separately:

```powershell
python tools/title_second_gate_candidate_experiment.py --candidate 15555c
python tools/title_second_gate_candidate_experiment.py --candidate 151404
```

Full traces are written to ignored build outputs
`build/semantic-equivalence/title-second-gate-15555c/report.json` and
`build/semantic-equivalence/title-second-gate-151404/report.json`.
