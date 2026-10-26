# Independent review: `0x002BDAC0` animation row setter

## Verdict

**Partial approval for the bounded synthetic domain; no promotion/runtime claim.**
The pinned ARM body, candidate source, linked ELF metadata, final report, cases,
and focused test assertions are internally consistent. I found no counterexample
in the eight valid-object fixtures. The null-object case is correctly isolated
as an invalid-pointer fault observation, not a defined C++ contract. This review
did not compile, run the candidate, run tests, or use an emulator.

## Independent ARM and caller checks

The pinned `code.bin` SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
108-byte span `[0x002BDAC0,0x002BDB2C)` SHA-256 is
`e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a`. I
decoded it independently. The first instruction is `ldr ip,[r0,#0x4c]`; a zero
table branches to the early `bx lr` at `0x002BDB0C`. The row path returns at
`0x002BDB28`. There is no original prologue or stack access.

The row address is based on the full 32-bit `r1`: `add r1,r1,r1,lsl #1`
forms `3*r1`, then `add r1,ip,r1,lsl #2` adds `12*r1` to the table pointer
with ARM 32-bit wrap. Separately, `strh r1,[r0,#0x50]` stores only the low
halfword. The target compares the full `r2` against zero, but stores its low
byte at `+0x54`; zero selects signed halfwords at row `+0/+2`, any nonzero
selects `+4/+6`. Each sign-extended coordinate is shifted left 12 modulo
2^32 and stored at object `+0x0C/+0x10`. Both paths clear halfword `+0x52`
and bytes `+0x86/+0x8A` before reading coordinates.

I decoded both calls in the pinned `0x002BF9F0` caller. At `0x002BFB48`, it
passes object `r4`, an `sxth`-converted word in `r1`, and `ldrsb` byte at
`[r1,#4]` in `r2`. At `0x002BFB78`, it passes object `r4`, an `sxth`-converted
word from the selected entry in `r1`, and an `ldrsb` value from entry `+4` in
`r2`. This is static caller evidence only; the actual H1 object/table binding
is not established.

## Candidate, object, report, and stack-projection audit

The candidate source SHA-256 is
`653f143c22f46a30ac2f5fe183f5d305927fca5f4959ef69d9a2f38f477377fc`;
the linked `candidate.elf` SHA-256 is
`fd5bb1b23b2352b34be37607da80f86eec76f160b245c171d9836c78b2022af2`.
Both match the run-02 report's recorded identities. Its recorded reference
image and body hashes match the independently hashed pinned inputs. The candidate
uses explicit bytewise little-endian helpers, unsigned row arithmetic, and
unsigned-before-shift coordinate conversion; these choices match the tested
ordinary-memory result semantics without signed-overflow assumptions.

The final report SHA-256 is
`b1c81d7accde2d2efb81fd9fc0b0071b1d48c0602c6578002bbe94ce0939fdcc`. All
nine entries are marked passed: eight valid-object cases cover null table,
zero/nonzero mode, mode `0x100`, index one/12-byte stride, index `-1` with a
valid preceding row, and signed coordinate extrema; the ninth null-object
fixture faults in both executions. The missing-`+0x86`-clear control is detected
by a synthetic memory difference. The test source checks all-pass/count,
fault labeling, control detection, and presence of the named boundary cases.
Those tests were inspected but not rerun in this review.

The run-02 stack projection compares SP and only bytes at/above the entry SP,
which are caller-owned at function entry. It excludes below-SP temporary spill
bytes used by the candidate's saved-register frame. This is the correct
caller-visible projection for an unchanged SP at return; the original itself
has no stack operations. The report and implementer handoff describe the first
run's mismatch as a below-SP spill comparison and report no other mismatch.

## Limits and recommendation

No production integration, real H1 runtime, captured object, or gameplay
scenario was tested. Valid passing rows are independent ordinary RAM; pointer
validity, arbitrary index domains, aliasing between object and row storage,
unmapped rows, and actual asset selection remain outside evidence. The null
object fault PCs differ (pinned entry versus candidate prologue) and do not
establish C++ null-pointer equivalence. The candidate declares a `void` return;
the inspected linked ELF happens to leave `r0` equal to the object pointer and
the report compares it, while the two pinned caller sequences do not consume
`r0` after the call. Treat that register value as observed machine behavior,
not a promised source-level return value.

Keep the source and exact `matching` ledger entry unchanged pending coordinator
review. A future promotion needs an independent caller-level validation and the
specified H1 scenario; this bounded differential is not whole-function runtime
equivalence.
