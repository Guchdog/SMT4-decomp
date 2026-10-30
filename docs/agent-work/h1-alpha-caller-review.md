# H1 alpha caller review — 2026-10-25

## Finding

The frozen `candidate_0029bdb4` agrees with original ARM through the synthetic
caller window `0x001EA070..0x001EA128` for both call sites, the two caller flag
branches, and positive/nonpositive helper gates. A deliberately wrong helper
that writes `child+0x7C` is detected. This supports the candidate's behavior in
this bounded caller setup; it does not establish runtime-normal object layouts
or a rendered title transition.

## Caller contract derived from the pinned instructions

The helper at `0x0029BDB4` takes the child pointer in `r0` and binary32 alpha in
`s0`, and returns no meaningful value. It always stores `s0` at child `+0x78`.
It then treats the signed word at `+0x34` as a gate: values `<= 0` return after
that store; positive values load scale from `+0x74`, load the target pointer
from `+0x4C`, multiply scale by alpha in VFP, and store the product at
`target+0x40` only when target is nonnull.

The title block calls it twice under opposite handle flag conditions:

- **A, call at `0x001EA098`, returns to `0x001EA09C`:** if handle A flag bit 2
  is clear, the caller sets that bit, writes live `s16` to child A `+0x74`,
  loads the existing child A `+0x78` into `s0`, and calls the helper. So the
  product input is `s16 * existing_child_alpha`; the helper's `+0x78` store
  writes the same alpha value the caller just loaded.
- **B, call at `0x001EA124`, returns at the window stop `0x001EA128`:** after
  the preceding block updates handle B's bit 1, bit 2 being set causes the
  caller to clear bit 2, write live `s17` to child B `+0x74`, load child B
  `+0x78` into `s0`, and call the helper. The product input is
  `s17 * existing_child_alpha`.

On both paths the helper's return registers are overwritten or not consumed by
the caller before the stop. The review compares caller-observable memory,
callee-saved GP/VFP state, stack, FPSCR/FPEXC, access sets, call trace, and
stop/fault status; caller-saved `r0-r3/r12`, `s0-s15`, and NZCV are excluded.

## Differential cases and result

The test runs the original caller instructions and replaces only the helper
entry with each compiled helper blob:

1. A bit clear / B bit set, both child gates positive: visits both calls and
   writes target alpha values `0.375` (`0x3EC00000`) and `0.125`
   (`0x3E000000`). Caller flags end at A `6`, B `0`; work `+0x98` receives
   `s16` (`0.5`).
2. Same call gates, child helper gates `0` and `-1`: both calls still happen,
   but both target `+0x40` sentinels remain unchanged.
3. A bit set / B bit clear: both helper calls are skipped; the caller reaches
   the same stop and its other memory effects match.

All three candidate runs match original ARM on compared observable state. The
negative `negative_wrong_offset` control is detected as a data mismatch: it
writes both child `+0x7C` words. Since the real caller loads `s0` from the
existing child `+0x78` just before each call, this caller window cannot show a
distinct value change at `+0x78` for the correct helper's always-store; that
store's distinct-value coverage belongs to the isolated helper tests.

The positive-gate fade helper reaches an indirect callback during this window.
The test supplies an explicit synthetic `bx lr` return-only stub at
`INJECT+0x100` for that callback. It supplies synthetic handles, children,
targets, flags, alpha values, and a work block; none were captured from Azahar.
An initial harness run without the callback target faulted on its poisoned
pointer before reaching call site B; that was fixture setup failure, not a
candidate counterexample. The final report records only the rerun with the
explicit callback stub and successful stop checks.

## Reproduction and provenance

Command: `python -m unittest tests.test_h1_alpha_caller -v` — **exit 0**, one
test. Candidate compilation writes only to the task's private check directory
and uses the one-job ARMv6K compiler helper. Reports and object are under
[`caller-window`](../../build/agent-work/H1-semantic/h1-alpha-caller-review/sleep-20261025/checks/caller-window/).

| Artifact/input | SHA-256 |
| --- | --- |
| Pinned `code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Original helper body, 40 bytes | `34f615df064dc58f59ea2c26df63b07a3f0c34fb75de30ee628acbb6ed1dd3ff` |
| Frozen candidate TU | `a9da3242f2843ce4424b4835206c044d663ca0b2bff44ce9c6cd32fd4529195a` |
| Candidate object | `05cc637f367a4991c21bddcb7f81443e8c06050a56ab35fd3a71a82c9cfad35f` |
| Review test / runner | `8483e81f9bd198a6c8419d379ca646764ccc46a06220888fa138c004970bda44` |
| Existing isolated runner `tools/h1_alpha_experiment.py` | `da6685db12ae65c6ab376795c830524bf0f81a66ed18cf4336e51fe377c1f9c8` |
| Caller-window `report.json` | `7145ffbde981f2da9d3ea9daa4272e6ea8a0c98123a830bdc3199de01350de57` |

Full case results, call-site trace, comparison policy, and synthetic limits:
[`report.json`](../../build/agent-work/H1-semantic/h1-alpha-caller-review/sleep-20261025/checks/caller-window/report.json).

## Limits and next action

This is a synthetic machine-level caller test, starting at `0x001EA070` and
stopping immediately after the second helper returns. It uses a return-only
indirect callback stub and does not execute readiness/fade entry, title help
lookup, `Camp_SetSlotMessage`, rendering, the full callback, an IPS patch, or an
emulator/game scenario. Review the object-layout assumptions against a runtime
capture before treating the caller setup as representative; then integrate the
helper in a reproducible patch/build and perform the scoped original-versus-
patched H1 runtime comparison.

Structured handoff: [`handoff.json`](../../build/agent-work/H1-semantic/h1-alpha-caller-review/sleep-20261025/handoff.json).
