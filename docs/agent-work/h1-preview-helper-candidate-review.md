# Independent candidate review: `0x002BF9F0` preview helper

Task: `h1-preview-helper-candidate-review`; owner: `h1_title_fade`.

## Verdict

**Partial review; the candidate is supported for the reported bounded fixtures.**
I independently decoded the pinned helper body and checked the candidate's
signed gates, row selection, endpoint/interpolation order, sequence sentinels,
common tail, linked placement, hooks, all 13 report cases, and the compiled
`+0x86` omission control. I found no semantic mismatch in the exercised cases.
The evidence does not cover every branch, the five real helper bodies, H1
object construction/lifecycle, a caller-level comparison, or runtime behavior.

## Pinned control flow and candidate correspondence

The pinned image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
664-byte helper body at `0x002BF9F0` hashes to
`9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e`.
The candidate source SHA-256 is
`64c3964b0abae2c0ff6e51d1e9ef5961c8e8d0769e177c528a878d4b094b3282`.

The two early gates are reproduced with short-circuit order: null returns 1;
for non-null objects, signed `+0x08` is read only when signed `+0x04` is
negative, and both negative returns 1. Otherwise execution continues. The
report covers null, both-negative, and `(-1, 0)` continuation, but not a
nonnegative `+0x04` paired with negative `+0x08` or signed extremes.

The `+0x86` nonzero guard and null `+0x4C` table guard both bypass row work
and reach the common tail. With a row, the candidate computes
`table + 12 * signed_s16(+0x50)` without a bounds check. It compares unsigned
row duration (`row+8`, `LDRH`) against signed progress (`+0x52`, `LDRSH`) using
the original signed greater-than condition. If duration is greater, it
interpolates and increments the halfword progress; otherwise it writes the
row endpoint and resets progress. This preserves endpoint versus interpolation
behavior for the checked fixtures.

The endpoint coordinate mappings match the pinned branches: for nonzero
`row+0x0A`, direction selects `(row+4,row+6)` or `(row+0,row+2)`; for zero
mode, direction selects the opposite ordering. The two endpoint fixtures cover
mode/direction pairs `(0,0)` and `(1,0)`; direction 1 in each mode is not
represented. The interpolation case covers direction 0 only; direction 1's
reversed coordinate differences are not separately tested.

Sequence handling is reached only after endpoint mode zero and feature byte
`+0x84` is nonzero. The candidate preserves the `0x1C` stride and signed
halfword index without a range check. Current word `-1` completes before
increment; otherwise it increments the index before reading the next word.
Next `-1` and `-3` complete; next `-2` resets index to zero and uses the first
entry's animation/frame; ordinary next entries supply their own animation and
signed frame byte. A disabled feature (`+0x84 == 0`) on a mode-zero endpoint
stores 1 to `+0x86`; a null sequence pointer and terminal sentinels also store
1. A nonzero row mode bypasses sequence handling. These paths agree with the
pinned branches. The report does not contain a next-word `-3` fixture, nor a
current-word `-3` case (which is deliberately not a current-entry sentinel in
the pinned code).

All continuing paths call `0x002B1FC0`, `0x002B1DFC`, and `0x002B1C8C` in
order, then compute `+0x8A` from the nonzero conjunction of bytes `+0x86..+0x89`,
return the signed byte in `r0`, and write 1 to `+0x85`. The candidate does the
same. The null and both-negative early returns skip those tail calls and the
`+0x85` write. The compiled negative control removes only the disabled-feature
`+0x86` store. The endpoint/completion fixture detects it through differing
`r0` (1 versus 0) and memory (`+0x86`), so this control specifically validates
that repair.

## Linked differential and harness review

The frozen linked ELF SHA-256 is
`8c5dbdc24e7b86652f3c6604f3c830758c83aa1ddfbfc73f365eaa708decf33b`; its
linked text is 1,300 bytes at `0x01000000`, with the candidate entry at that
base and named stub entries within the extracted text. The candidate source is
linked with ARMv6K hard-float flags and `lld`, then the linked `.text` is copied
into the Unicorn injection mapping. The original body runs from pinned address
`0x002BF9F0`. I inspected these artifacts and hashes read-only; I did not
relink or re-run the experiment.

Other frozen artifact hashes: runner
`cf5794b323c08e184b707c0f5646fcb338c3e9af72c2d8abaf8b9ab592012cf8`, tests
`765e3912b03c7d3b9cb67cee62dbc32e47b3dbc20490e21d4f027bb9edc44214`,
implementer report
`fe7789fab0d4d130f7fbada09523747eb014295b99e080514f0e2a247d63b35a`, and
implementer handoff
`c09226b8421e54bf4c7e3bd958980bbc3d04b501373f5559f1ebea04b205ecc3`.

The harness starts a fresh ARM machine for each side of each case, maps the
pinned image, injection text, synthetic object, rows, sequence, and stack, and
stops at its LR sentinel. It compares `r0`, `r4-r11`, SP, FPSCR, the call
sequence and arguments, and the full 0x1000-byte synthetic data mapping. The
13 report cases all pass:

| Case | Checked behavior |
|---|---|
| null early return | constant-one early result |
| both negative early return | signed early gate |
| second gate nonnegative continues | continues through common tail |
| already complete bypasses rows | `+0x86` short-circuit |
| null row table skips animation | null table guard |
| endpoint row and completion tail | endpoint path and disabled-sequence `+0x86` write |
| nonzero row mode bypasses sequence block | row-mode sequence bypass |
| interpolation row invokes two interpolators | x/y call order and fixed-point deltas |
| sequence ordinary entry invokes animation helper | increment then use next entry |
| sequence enabled null pointer marks complete | null sequence completion |
| current sequence end marker marks complete | current `-1` sentinel |
| sequence end marker sets complete | next `-1` sentinel |
| sequence restart marker resets index | next `-2` restart path |

The direct callees are not executed on either side. The original call-address
hooks intercept `0x002BDAC0`, `0x002C615C`, `0x002B1FC0`, `0x002B1DFC`, and
`0x002B1C8C`; candidate linked-symbol hooks intercept the corresponding
candidate stub entries. The synthetic animation and tail stubs return zero and
do not mutate the object. The interpolation hook returns signed `delta /
duration`, or zero for duration zero; the report's interpolation case uses
small values and duration 8. Thus the comparison validates surrounding
register arguments, call ordering, and behavior under that exact synthetic
stub contract. It does not validate actual callee ABI side effects,
transitive callbacks, or the real `0x002C615C` algorithm.

The fixture object is 0x8B bytes, the minimum extent touched by the helper's
direct fields. Row and sequence buffers are mapped at the fixed synthetic
addresses and are large enough for the indices used. These fixtures do not
test unchecked invalid indices, allocations, source constructors, live object
bindings, or scene `+0xD74` lifecycle. In particular, the helper's writes
within its synthetic object say nothing about whether that interior H1 object
has valid nested pointers at the time the real gate calls it.

## Evidence boundary and next action

Packet input hashes match the declared frozen values. The candidate report
records compiled `passed`, differential `partial_synthetic_stubs`, caller
`not_run`, and runtime `not_run`, which is appropriate. No live H1 object
identity, production integration, emulator, renderer, or save state was used.

Review evidence: compiled `not_run`; ARM differential `partial` (inspected
implementer report, not rerun); caller `partial` (static contract and harness
boundary only); runtime `not_run`. No candidate discrepancy was found in the
13 reported cases. Remaining concrete test gaps are the direction-1 endpoint
and interpolation branches, next `-3` sentinel, some early-gate combinations,
and real callee/caller lifecycle behavior. Keep this candidate experimental;
before integration, add targeted cases for those local branches if needed and
recover the actual callee contracts and H1 `scene+0xD74` object lifecycle.
