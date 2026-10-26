# `0x002C615C` interpolation divide candidate

## Result

The pinned 556-byte ARM routine implements sign-aware integer division, not
unsigned quotient semantics for every 32-bit pattern. The candidate in
`experiments/semantic_equivalence/h1_interpolation_divide_candidate.cpp`
implements its quotient and remainder result words with a restoring unsigned
magnitude divide and explicit sign correction. A second C-callable entry
returns only the quotient for callers whose source declarations consume `r0`.
The ARM build has no undefined symbols.

The final private differential report is at
`build/agent-work/H1-semantic/h1-interpolation-divide-candidate/overnight-20261025-interpolation-divide-corrected/checks/seed-20261025-r4/report.json`.
It passes 368 cases: 35 H1 fixed-point caller-domain cases, 77 directed signed
boundary cases, and 256 seeded signed-bit cases. The report includes nine
zero-divisor observations and detects a quotient-plus-one negative control.
There was no first mismatch in the defined comparison projection. This is
finite isolated evidence, not formal proof or H1 runtime evidence.

## Pinned contract

The image hash is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
The exact body begins at `0x002C615C`, has 556 bytes, and has SHA-256
`3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9`.
`BX LR` at `0x002C6384` is the return; the extent ends at `0x002C6388`.

At `0x002C615C`, `ORRS r3,r0,r1` selects a sign-handling path if either input
has its high bit set. The nonnegative path performs unsigned magnitude
division. The signed path converts operands to magnitudes, applies quotient
sign from the operand signs, and gives the remainder the numerator sign.
Outputs are quotient bits in `r0` and remainder bits in `r1`. The H1 callers
consume `r0`; `r1` is caller-saved, although the pinned routine does compute it.
The routine leaves `r4-r11` and SP unchanged on both normal and zero-divisor
returns. It uses `r2`, `r3`, `ip`, flags, and (on divisor zero) a short stack
push/pop.

For denominator zero, the ARM path reaches `0x002C6378`, calls
`0x0014E604`, which branches to `0x001524EC` (`BX LR`). The observed return is
`r0=0`, `r1=original numerator bits`; the push/pop leaves two temporary words
in the restored stack region. The C++ divmod candidate models both return
words, but its compiler-generated stack frame leaves different scratch bytes.
The quotient contract and restored SP/callee-saved state are checked; bytes
below the caller's restored SP are reported as ABI scratch, not equated.

## Caller evidence

The H1 preview helper calls this routine at `0x002BFBA4`, `0x002BFBC8`,
`0x002BFBEC`, and `0x002BFC10`. It forms the numerator by signed-halfword
loads, signed subtraction, and `LSL #12`; the second argument is an unsigned
halfword row duration. The two coordinate differences are in
`[-65535,65535]`, and multiplication by 4096 remains inside signed 32-bit
range. For the intended interpolation branch with positive duration, the
domain is signed fixed-point numerator and duration `1..65535`. The helper's
interpolation stub in its earlier isolated harness is synthetic and is not
evidence for this divide body's behavior.

Other source aliases at `src/camp/unite_extras.cpp` and
`src/script/script_vm_extras.cpp` declare unsigned parameters. The pinned
sign-bit path supersedes that shorthand for negative inputs. Those other
callers are not differentially validated here. No runtime constraints on all
possible row progress/duration state are proven by this task; the H1 tests
exercise the assigned positive-duration domain.

## Differential and controls

The private runner maps the pinned original image and executes the original
routine directly under Unicorn ARM11 MPCore. It separately links and executes
the candidate `uint64_t` divmod entry and its quotient-only C entry. It checks
`r0`, `r1`, `r4-r11`, SP, data memory, return sentinel, and faults. Candidate
stack residue is recorded because a readable compiler implementation uses a
restored stack frame while the original nonzero path does not. Zero-divisor
stack residue also differs as described above. Caller-visible data memory is
unchanged for all cases.

The 35 H1 cases span coordinate deltas `-65535,-32768,-1,0,1,32767,65535`
times 4096 and durations `1,2,3,8,65535`. Directed cases include high-bit
operands, quotient zero, exact quotients, maximum-near values, signed
minimum divided by negative one, and all nine numerator boundary values with
zero divisor. The seed is `20261025`; there are 256 additional nonzero-divisor
signed-bit samples. The wrong-quotient control increments the candidate
quotient and is rejected on `4096/2` because `r0` differs.

Exact commands and artifact hashes are in the private report and structured
handoff. The report records `first_mismatch: null`; all zero-divisor result
words match, but stack residue is not byte-identical. The focused tests assert
report provenance fields, H1-domain coverage, result-word comparisons, zero
behavior and negative-control detection.

## Limits and next step

This is a standalone candidate. It does not modify production sources, the
source ledger, the existing preview helper, or shared runner code. It does not
establish static aliases' complete caller behavior, actual H1 scene/object
lifecycle, runtime binding, concurrent or interrupt behavior, or whole-game
equivalence. The `u64` divmod entry expresses `r0/r1` under the 32-bit ARM ABI;
the quotient-only entry is available for direct C callers that ignore `r1`.
The implementation is not byte-identical and must not alter the ledger's exact
classification.

Keep this as experimental until an independent review checks the report,
zero-divisor path, two-register result convention, H1 positive-duration caller
domain, and stack-memory projection. Promotion would require its own assigned
integration and runtime scenario.

