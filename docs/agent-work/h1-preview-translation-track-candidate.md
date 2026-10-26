# H1 translation-track candidate handoff

Task `h1-preview-translation-track-candidate` reconstructs only the pinned
entry `0x002B1DFC`, a direct object update in the `0x002BF9F0` common tail.
The candidate is an opaque-byte C++ model; it does not merge this entry with
other helpers or assign a stronger owner type. The pinned function is 452 bytes
through `0x002B1FBF`, has one `pop {r4,r5}; bx lr` return sequence, and no direct
calls.

The final fresh linked ARM/Unicorn run passed **17/17** fixtures with no stubs. It
covers disabled completion and null table gates, all four endpoint row-mode /
direction combinations, direction-dependent interpolation including reversed
deltas, the exact and just-above duration boundary, sequence disabled/null
paths, current and next sentinels, restart, and normal sequence index/animation
updates. The targeted wrong-`+0x30` common-tail offset mutation was detected by
the object memory comparison. Focused tests passed **4/4**.

## First counterexample and resolution

The first runner invocation (`run-01`) failed before producing a report because
the harness still passed removed fixture keywords; it exited 1. The first
actual ARM differential (`run-02`) had 10/17 cases pass. Its first semantic
counterexample was row mode zero endpoint: pinned ARM preserved `+0x6A` progress
at 8 when sequence processing terminated/was disabled, while the initial C++
cleared it. The code shows that only nonzero-row-mode endpoints clear progress
directly; row-mode-zero paths clear it only if a sequence animation is
installed. That branch distinction was fixed. Afterward, the source used
`__builtin_bit_cast` for exact float-bit access, and the final fresh `run-04`
recompiled and passed all 17 cases.

The comparison checks object memory (including neighboring values and table /
sequence bytes), `r0`, `r4-r11`, SP, caller-owned stack, callee-saved `d8-d15`,
and FPSCR. `s0-s3` are captured for diagnosis but treated as caller-saved;
observable interpolation results are compared exactly in object memory. Stack
bytes below entry SP are private spill space and are not included in the
caller-owned stack projection.

## Evidence limits

Rows and sequence buffers are valid synthetic, non-aliasing allocations.
Unchecked invalid indices/pointers, table/object overlap, sequence/object
overlap, allocation lifetime, the live H1 object at the parent helper's
`scene+0xD74`, and runtime binding remain unproven. There are no direct callees
inside `0x002B1DFC`, so this candidate directly exercises the local VFP and
state behavior without external stubs. This remains isolated candidate evidence;
there is no production integration or Azahar/game-runtime result, and ledger
`matching` is unchanged.

Final report and linked candidate are in
`build/agent-work/H1-semantic/h1-preview-translation-track-candidate/overnight-20261025-translation-track/run-04/`.
See the structured handoff for hashes and exact commands/exits.
