# H1 title help-text presentation audit

Scope: the title callback's selection-to-help-text window at
`0x001EA12C..0x001EA15C`. This is an isolated ARM caller-window check, not a
production reconstruction or emulator observation.

## Asset evidence

The extracted `/title/TitleTable.tbb` is 880 bytes with SHA-256
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`.
Its table 0 is `TBL1`, starts at file offset `0x20`, and has a 344-byte payload
starting at `0x30`. At payload offsets `0x16 + 0x56 * index`, indices 0..3
contain these NUL-terminated strings:

| Selection | Payload offset | Text |
| ---: | ---: | --- |
| 0 | `0x16` | `Start a new game from the beginning.` |
| 1 | `0x6C` | `Load a saved game and continue playing.` |
| 2 | `0xC2` | `Configure audio settings.` |
| 3 | `0x118` | `Download additional content.` |

These are the asset's help/description strings. They are not the four menu
labels: the latter are separate strings in the same table records.

## Pinned ARM caller-window experiment

`tools/title_help_presentation_experiment.py` places the real asset in bounded
Unicorn memory, sets the title work-block `+8` field to each valid index, and
executes the pinned original instructions from `0x001EA12C` up to but not
including the call at `0x001EA15C`. The call chain uses original
`Tbb_GetGlobalSubTable`, `Tbb_GetSubTable`, and `Tbb_GetPayloadData` code. For
all four indices, the observed `r0` equals the exact help-string address in the
asset; `r1` is `0x323232FF`, the color argument loaded by the caller. The run
uses `code.bin` SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

Focused tests:

```powershell
python -m unittest tests.test_title_help_presentation_experiment -v
python tools/title_help_presentation_experiment.py --output build/semantic-equivalence/title-help-presentation/seed-20261024.json
```

Both passed for this experiment (3 tests; four selection cases). The existing
`tools/tbb_semantic_experiment.py` separately checks the candidate TBB getters
against original code and already covers the title getter call window at
`0x001E9AB0..0x001E9AC8`. This new run does not claim differential validation
of substituted getters in the later presentation window; it executes the ROM
getters there.

## Evidence boundary

Observed: original ARM arithmetic consumes `work+8`, computes the selected
payload string pointer using stride `0x56` and offset `0x16`, and prepares the
color argument at the `Camp_SetSlotMessage` call boundary. Real-asset contents
match the four selected pointers.

Not observed: `Camp_SetSlotMessage` itself, text layout/rendering, visible
presentation in Azahar, input bindings, or the complete callback's runtime
state. The test stops before entering `0x0029F10C`; emulator verification is
still required to establish what appears on screen and whether the help text
visibly refreshes after navigation.
