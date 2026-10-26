# Independent review: `0x002B1DFC` translation-track candidate

## Review result

**Partial bounded confirmation.** The pinned body, candidate, final report, and
the recorded correction agree for the tested valid, synthetic, non-aliasing
fixtures. The final report passes 17/17 cases; the wrong-neighbor-offset
control is detected. This supports the isolated translation-track behavior
covered by those fixtures. It does not establish arbitrary memory aliasing,
all floating-point encodings, live H1 object lifetime/binding, or runtime
behavior.

All 14 packet input hashes matched. The pinned image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
452-byte body SHA-256 is
`092706575055bba00e8aab90e9ef2a45c2761fb7d12fa0f0b54dbecd35b7439a`.
Candidate source SHA-256 is
`add9c202a734341338068d7ec0c72a3555df2779bb75582eda3d345a6d294e50`;
run-04 report SHA-256 is
`257e04c7da52ea6fcff5d57264ed340579adf1bb116f503d5cc0bdf75a777407`.
The candidate ELF hash in the report and handoff is
`6173d06e1dd7a5b3cee273dfe8cab1904295c301a92b4b4dcaf09c6b8cf32884`.

## Pinned boundary and state

The image bytes at `0x002B1DFC` decode as a 452-byte ARM body ending at the
exclusive address `0x002B1FC0`. Entry `0x002B1DFC` pushes `{r4,r5}`. Early
returns at `0x002B1E08`/`0x002B1E14` branch to the shared `pop {r4,r5}` at
`0x002B1FB8`, followed by `bx lr` at `0x002B1FBC`. There are no direct calls.
The local frame is only the saved register pair; SP is balanced. `r4-r5` are
restored. The candidate returns no formal value and the comparison confirms
the observed `r0` object pointer on all fixtures.

The first gate tests byte `object+0x88`; nonzero returns without the normal
tail. The next gate loads the row table from `+0x64`; null also returns
unchanged. Otherwise, signed halfword animation and progress at `+0x68` and
`+0x6A` select a 12-byte row (`table + 12 * sign_extended_animation`). Row
duration is unsigned `LDRH` at `+8`, compared with signed progress by `BGT`.

- **Interpolation (`duration > progress`):** direction `+0x6C` selects row
  float order. Nonzero direction subtracts row `+4` from row `+0`; zero
  direction subtracts row `+0` from row `+4`. The pinned VFP sequence is
  `VMOV`, row loads, `VSUB.F32`, unsigned-duration `VCVT`, `VDIV.F32`, current
  value load, progress halfword increment/store, then `VADD.F32` and `VSTR` at
  `object+0x24`. The candidate preserves the arithmetic order and the final
  object float bits match in its interpolation fixtures.
- **Endpoint (`duration <= progress`):** row mode and direction choose the raw
  row word stored at `+0x24`. Nonzero row mode clears progress and skips
  sequence handling. Zero row mode preserves progress unless a sequence
  animation is installed.
- **Sequence handling in zero row mode:** disabled feature `+0x84`, null
  sequence `+0x78`, current `-1`, and next `-1`/`-3` set completion `+0x88`.
  The signed halfword sequence index at `+0x80` increments before the next
  entry check. Next `-2` resets the index and installs entry zero. Ordinary
  next entries install their signed-halfword animation and signed direction.
  Installation clears progress and `+0x8A` and copies a selected translation
  row endpoint to `+0x24`, `+0x28`, and `+0x2C`.
- **Common tail:** paths after both early guards copy `+0x24` into `+0x28` and
  `+0x2C`; the early-return gates do not.

I independently decoded the parent helper window: `0x002BF9F0` passes its
track object in `r4` as `r0` to `0x002B1DFC` at `0x002BFC3C`. The return is
ignored. This establishes a static call edge and argument, not a live H1
object binding.

## First counterexample and correction

The implementation handoff accurately separates a harness setup failure from
the first semantic mismatch. Run-01 exited 1 because an obsolete fixture
keyword raised `TypeError` before a differential report existed. In run-02,
the first semantic counterexample was **mode zero, direction zero endpoint**:
original memory retained signed progress `+0x6A == 8`; the first C++ draft
cleared it to zero. The endpoint float at `+0x24` matched; object memory did
not. This is consistent with the pinned branch at `0x002B1E60`: zero row mode
enters sequence handling, and terminal/disabled sequence paths do not clear
progress. The fix leaves `+0x6A` unchanged on those paths and clears it only
for nonzero-row-mode endpoints or an installed sequence animation.

Run-04 has `first_mismatch: null`, all 17 cases passed, and covers both
direction endpoint selections for both row modes, both interpolation
directions, duration equality and just-above-progress boundaries, sequence
disabled/null gates, current/next sentinels, restart and ordinary next entry.
The deliberately wrong `+0x30` common-tail neighbor offset is rejected by a
full-memory difference. The negative control is a useful check of the memory
projection, not a proof for every state.

## Comparison projection gaps and limits

The runner compares final `r0`, callee-saved GPRs `r4-r11`, SP, `d8-d15`,
FPSCR, caller-owned stack bytes, and the complete mapped object/table/sequence
data. VFP `s0-s3` are captured as diagnostics but not required to match because
they are caller-saved. It does not compare other caller-saved registers
(`r1-r3`, `r12`), condition flags, or the instruction-by-instruction memory
read/write trace. It compares final bytes, not access multiplicity/order.
That matters for overlapping object, row and sequence buffers; the report
explicitly limits fixtures to valid non-aliasing buffers, so those cases are
outside the demonstrated domain.

The floating-point fixtures use selected ordinary finite values under a fixed
FPSCR setup. They do not systematically cover NaN payloads, infinities,
subnormals/flush-to-zero, signed-zero corner cases, rounding modes, or enabled
exception traps. Final FPSCR equality and the tested output float bits are
useful evidence for these fixtures, not a full VFP semantic proof. No H1 scene
construction, allocation lifetime, dynamic callback binding, Azahar/game
runtime or production integration was tested. The source ledger and exact
classification remain untouched.

## Recommendation

Retain this as an experimental local candidate with the recorded +0x6A fix.
Before promotion, preserve the above projection limits and independently
validate caller object lifetime/binding and the relevant runtime scenario.
