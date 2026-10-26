# Independent review — preview-helper branch coverage expansion

## Verdict

**Partial; the added fixtures and reported outcomes match the cited local ARM
branches, with the stated synthetic boundaries.** All packet-declared hashes
matched. The frozen report has 21 cases, all marked passed; the compiled
candidate source and linked ELF hashes match the earlier candidate identity.
The negative control removes the disabled-sequence completion store and is
detected by the endpoint fixture through the expected return and memory
difference. I did not compile, rerun Unicorn, or execute tests; these are
read-only checks of the frozen artifacts.

No counterexample appears in the reported 21-case projection. This is not full
branch coverage or validation of the five real callee bodies. The local fixture
set still uses index zero, small row coordinates/durations, default-true
completion bytes `+0x87..+0x89`, and deterministic stubs. The projection also
does not record individual memory reads/writes or compare all machine state.

## Provenance cross-check

The 14 input hashes in the review packet matched current files. The pinned
image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the helper
body SHA-256 at `0x002BF9F0` is
`9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e`.

The coverage report SHA-256 is
`31f961f48cc54d4e615d9d48347fe672bda71313d9d503082650a768fdae6b81`; it records
21/21 passed, candidate source SHA-256
`64c3964b0abae2c0ff6e51d1e9ef5961c8e8d0769e177c528a878d4b094b3282`, and
linked candidate ELF SHA-256
`8c5dbdc24e7b86652f3c6604f3c830758c83aa1ddfbfc73f365eaa708decf33b`. I hashed
the actual candidate source and coverage ELF read-only and confirmed both
values; the ELF also matches the prior candidate run's linked ELF. The expanded
runner hash is
`adf2647b43b72469f516936f0c875ccc470e89c12df51b82f5fed5454b44f4b3`; focused
test source hash is
`04f5d8a2c712dbaa8addca5d4fc104ce3c7bbbcb947fce34d738ffd7825fbdf6`. The
implementer handoff hash is
`f89cf1e8ce059f869b732f3734abb5fc9ad82325182c72ae020f60f094243d85` and records
the two focused tests as exit 0. I inspected the test source but did not rerun
it.

## Added fixture mapping to the pinned body

The helper body was independently decoded from the pinned ARM image. The eight
added cases (cases 4–7, 12–13, 15, and 20 in the report) cover these local gaps:

| Added case | Fixture values / observed projection | Pinned branch it exercises | Review |
|---|---|---|---|
| First gate zero, second negative continues | `+4=0`, `+8=-1`; common tail, result 0 | `0x002BFA00..0x002BFA0C`: the `LDRLT`/compare is not taken and `BGE` continues | Values and result are consistent. The report has no read trace, so this does not independently demonstrate whether candidate/pinned execution read `+8`; the pinned instructions specify that access ordering. |
| Signed minimum pair early return | `INT32_MIN/INT32_MIN`; result 1, no tail calls | `0x002BFA04`, `0x002BFA08`, `0x002BFA0C` | Correct boundary fixture for both signed comparisons. |
| Signed minimum then maximum continues | `INT32_MIN/INT32_MAX`; result 0, common tail | Same signed conditional gate | Correct boundary result for the exercised path. |
| Signed maximum then minimum continues without second gate | `INT32_MAX/INT32_MIN`; result 0, common tail | `0x002BFA04` conditionally skips the `+8` load; `0x002BFA0C` continues | Final output is consistent. Because reads are not instrumented, the `without second gate` access claim is supported by the pinned decode and C++ short-circuit source, not proven by this dynamic projection. |
| Row-mode zero, direction one endpoint | Mode 0, direction 1; stored x/y are row `+0/+2` as 12.12 fixed point | `0x002BFA60` branches to `0x002BFAA8`; nonzero direction follows `0x002BFAAC` fallthrough to first endpoint | Matches the `0x002BFAA8` block. |
| Row-mode nonzero, direction one endpoint | Mode 1, direction 1; stored x/y are row `+4/+6` | `0x002BFA60` falls through; `0x002BFA68` is not taken; endpoint writes at `0x002BFA6C..0x002BFA80` | Matches the selected opposite endpoint. The valid sequence fixture is intentionally bypassed on this row-mode path. |
| Direction one interpolation uses reversed deltas | Mode 0, duration 8, progress 1, direction 1, coordinates `(1,3,5,7)`; both stub deltas are `-0x4000` | `0x002BFB90` falls through to x/y subtractions and calls at `0x002BFBA4`/`0x002BFBC8` | The captured negative deltas and resulting fixed-point updates agree under the report's `delta/duration` stub. |
| Next sequence `-3` completion | Current entry is ordinary, then index increments to entry 1 containing `-3`; result 1 and `+0x86=1` | `0x002BFB30` checks next word `-1`/`-3`, then branches to `0x002BFB58` store | Correctly covers the distinct next-entry `-3` sentinel. |

Together with the prior fixtures, the set now has both directions for endpoint
and interpolation selection, the signed early-gate combinations/extremes listed
in the coverage note, and current/next sequence sentinel paths. It does not
exercise the current-entry `-3` as a sentinel because the pinned body only
recognizes current `-1`; `-3` is checked after increment at `0x002BFB30`.

## Negative control and comparison projection

The negative-control source SHA-256 is
`9bfb433c4ce15e48f3156d7d29bad2ae317243b246f72633e59d7a6d2a9ebc33`; its
linked ELF SHA-256 is
`8feadc999c65ac6c933f36163e57d4c06518a4e291f2c388fb09b541c429cfab`. It
removes only the mode-zero/feature-disabled `+0x86=1` assignment. On the
endpoint fixture, the report records original `r0=1`, mutant `r0=0`, and the
expected `+0x86/+0x8A` memory difference. Thus the control is sensitive to that
specific completion-store mistake rather than merely reporting a passing
mutant run.

The runner starts a fresh Unicorn ARM11 MPCore machine for each original and
candidate case, runs the original at `0x002BF9F0`, links the unchanged C++ source
with named stubs, and runs the candidate blob at `0x01000000`. It compares
`r0`, `r4-r11`, SP, FPSCR, named helper order/arguments/returns, and final bytes
of the 0x1000-byte synthetic data mapping. It does not compare a memory access
trace, transient state, CPSR flags, `r1-r3`, `r12`, LR, or stack bytes. The
function contains no VFP instructions, but the report's register projection is
still bounded. Call traces are normalized to names and arguments rather than
including the individual call PC.

The five real external callees are not executed. In particular, interpolation
returns signed `delta / duration` (or zero for zero duration), and the animation
and common-tail stubs return zero without original side effects. The branch
cases establish surrounding behavior for those stubs only, not real helper
effects or callback behavior.

## Evidence boundary and recommendation

The report's 21/21 result and negative control are consistent with the frozen
candidate, runner, tests, and pinned body. The handoff correctly labels compiled
evidence `passed`, ARM differential `partial`, caller/runtime `not_run`, and
lists synthetic-stub and object-lifecycle limits. The focused test source checks
the final report count, selected branch-case names, all case pass flags, and
negative-control detection; its 2/2 execution claim is the implementer's
record, not a rerun in this review.

Remaining local gaps include row and sequence indices other than zero, index
wrap/invalid bounds, high-bit unsigned durations and other signed progress
boundaries, signed coordinate extremes, nonzero row-mode sequence bypass with
more sentinel variations, and each independent false value in `+0x87..+0x89`.
The full direct effects of `0x002BDAC0`, `0x002C615C`, and the three tail helpers,
real caller behavior, source object lifecycle, H1 `scene+0xD74` bindings, and
runtime behavior remain untested. Keep this as expanded bounded synthetic
evidence and retain independent implementation review/caller-level validation
before promotion.
