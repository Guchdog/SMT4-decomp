# H1 title transition: first positive fade gate

## Result and scope

`tests.test_title_transition_positive_gate_experiment` passes. One Unicorn
machine executed the pinned US ARM image continuously from `0x001E9FD4`, through
the `work+0x94 == 0` transition mutator and the positive body beginning at
`0x002872B0`, then through the original TBB help lookup. It stopped at
`0x001EA15C`, immediately before `Camp_SetSlotMessage`. The real
`TitleTable.tbb` selected “Start a new game from the beginning.”

The binary SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the table
SHA-256 is
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`.
The test and CLI explicitly read the in-worktree copies under
`build/semantic-equivalence/real-assets/`, not the `extracted` link.

## Positive-gate setup and callback boundary

The explicit synthetic state makes the readiness predicate at `0x0025A274`
return nonzero using `childA+0x34 = 1`, a nonnull nested object, clear bit 0,
and equal finite floats at nested `+0x38/+0x48`. The second readiness predicate
uses `childA+0x58 = 0` and returns from its signed-field early exit. The
mutator's `work+0x94` begins at zero, so the transition block runs.

For the resource at `work+0x90`, child B has `+0x34 = 1`; therefore the call
at `0x002872A4` falls through into the original 80-byte body at `0x002872B0`.
Child B `+0x58 = 0`, so the following `0x0020FFA0` helper takes its early
return; the second positive-gate body at `0x0020FFAC` is not covered.

The original first helper performs `BLX r1` at `0x002872E4`. Its nested
`+0x4C` field points to an isolated one-instruction stub at `0x01000100`:
`bx lr` (`0xE12FFF1E`). The call was observed exactly once:

| Point | r0 | r1 | LR | s0 | s2 |
| --- | --- | --- | --- | --- | --- |
| Stub entry | `0x02000C00` | `0x01000100` | `0x002872E8` | `0.5` (`0x3F000000`) | `0.75` (`0x3F400000`) |
| Stub return | `0x02000C00` | — | — | `0.5` (`0x3F000000`) | — |

The stub performs no memory writes and changes no registers or FP values; the
return values above are consequently the preserved inputs. This defines only
the harness stub contract. It does not identify or model the game's real
indirect callee.

## Observed effects and boundary

The run recorded 50 read accesses, all within the explicitly initialized
work/handle/child/nested-object graph, the TBB container/manager slot, bounded
stack save area, or original literal pools. Eleven writes occurred: two stack
saves in the original helper and nine original ARM data writes. The callback
stub itself wrote zero bytes. Data effects include handle A flags `4 -> 6`,
`work+0x98 = 0.75`, nested B `+0x38 = 0.5`, nested B `+0x3C = 1.0`, nested B
`+0x58 = 1`, nested B `+0x1F6 = 1`, and `work+0x94 = 1`.

At the stop, the original caller had selected the expected string pointer
(`r0=0x02001046`) and color (`r1=0x323232FF`). The presentation callee was not
entered. This is instruction-level synthetic-path evidence only: it does not
prove that the setup occurs in a real game session, establish the real BLX
callback's behavior, verify rendered UI or gameplay, or show behavior in
Azahar. No function count or byte-exact ledger changed.

## Reproduction

From the worktree root:

```powershell
python -m unittest tests.test_title_transition_positive_gate_experiment -v
python tools/title_transition_positive_gate_experiment.py
```

The JSON trace is written to the ignored
`build/semantic-equivalence/title-transition-positive-gate/report.json`.
