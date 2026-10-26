# Independent review: H1 type-0 callback `0x0015555C`

> **Superseded for the unordered-semantics finding.** This review examined the
> pre-correction source revision and correctly identified its false statement
> that unordered `GT` takes the upper-clamp branch. The source comments and
> function record were corrected afterward. See
> [`h1-type0-callback-correction-review.md`](h1-type0-callback-correction-review.md)
> for the corrected rule and fresh evidence. The historical finding below is
> retained to preserve review provenance; it does not describe the current
> source.

## Review result: partial

The callback candidate's executable compare sequence is consistent with the
pinned ARM instructions, and all 17 producer-reported differential rows are
internally consistent with the values in the report. I found no return-value,
FPSCR, register-preservation, stack, or memory-write mismatch in those rows.
However, the candidate's comments, function record, and handoff repeatedly
misstate the unordered condition behavior: ARM `GT` is **false** for unordered
`VCMPE` flags. The report data itself shows that the original and candidate do
not clamp a NaN value to the upper bound. Correct the semantic narrative before
accepting the function record. I did not edit candidate/source files, compile,
or rerun the experiment.

All 14 frozen packet input hashes matched. Pinned code image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Reviewed
candidate source hash is
`1ec6d87a0b158d1b6025e8e87e09f723dc0a1a175ba01fce7c8d41568dc3a407`, runner
hash `360e50de38b3a055e04f9cb3e9634300b31621a098b9eab5d96af453cc982ea1`, test
hash `c4faff09f7844bef2a50b32583a1749c7afe1cb06593e631edee85c5b8e8d95d`,
object hash `ee094897c154f1171aaf52c308f0ef12a027ffd16ef55cc6ada8f273db748eae`,
and producer report hash
`320030a2000df944c17515de64b57632bab87bf7816364c8c7abcbe5d4f27f72`.
The producer handoff hash is
`6903a5d052654fd2192af7c1c480cd1bd9d7d89f722228adf50874cf1ae696df`.

## Entry boundary and callable ABI

Pinned disassembly confirms `0x00155540` executes its own prologue and returns
with `pop {r4,pc}` at `0x00155558`. The next instruction, `0x0015555C`, is the
callback body: `vmov s3,s0`, `vmov s0,s2`, two VFP compares, conditional moves,
and `bx lr` at `0x00155580`. The next prologue starts at `0x00155584`. The
candidate enters at `0x0015555C` directly and does not rely on the predecessor's
prologue or state. Although the repository's naked `func_00155540` assembly
partition spans this address range, the return boundary and independent
indirect-call use establish `0x0015555C` as a separately callable interior
entry.

The static setup path at `0x002A6194` stores literal `0x0015555C` to callback
slot `+0x4C`; the setup at `0x002A5CEC..0x002A5D08` selects that default for
type 0 and literal `0x00151404` for type 1. The H1 object callsite at
`0x002872E4` loads callback `+0x4C` and argument `+0x50`; it passes lower in
`s0`, upper in `s1`, and the current/clamped value in `s2`. The indexed-record
callsite at `0x00210010` likewise loads `s0/s1` from a bounds pair, keeps the
value in `s2`, and calls its callback slot with `BLX`. These are static and
synthetic reachability evidence; the active live source object's byte and
selected target remain unknown.

The C++ signature `(float lower, float upper, float value) -> float` therefore
matches the hard-float calling convention. The inline compare uses `s0-s2` and
caller-saved integer registers only. The inspected object has no relocations,
no stack frame or data writes, and returns through `bx lr`; the frozen report
records preservation of `r4-r11`, `d8-d15`, `sp`, and no memory writes.

## Correct VFP unordered semantics

The original sequence is exactly `VCMPE(value, upper); VMRS; VMOVGT upper;
BGT return`, followed, only if GT is false, by `VCMPE(result, lower); VMRS;
VMOVLO lower; BX LR`. Unordered VFP comparison flags have `N=0, Z=0, C=1,
V=1`. ARM `GT` requires `Z==0 && N==V`, so the upper-clamp branch is false on
unordered input. ARM `LO` requires `C==0`, so the lower-clamp move is also
false on an unordered second comparison. Thus an unordered value remains
unchanged; a NaN bound does not by itself take either clamp. `VCMPE` still
updates FPSCR, including the invalid-operation status observed in the report.

The compiled candidate object uses the same `vcmpe` and `movgt`/`movlo`
conditions, and the C++ structure preserves the original early return after an
ordered upper clamp. Its behavior appears correct. These artifacts currently
contain incorrect wording that should be fixed:

- Source helper `vfp_greater_or_unordered` and adjacent comment claim GT covers
  unordered values; the source should name/document the actual `GT` condition.
- `docs/function-records/0x0015555c.md` says unordered GT takes the upper path.
- `docs/agent-work/h1-type0-callback-candidate.md` says unordered flags select
  upper for NaN.
- The producer handoff repeats the same claim.

The four “negative controls” are four NaN input cases for one ordinary C++
comparison mutant. For all four, original and mutant `s0` are identical; only
FPSCR differs because ordinary C++ comparisons compile to quiet `VCMP` here,
while original/candidate use signaling `VCMPE`. They are valid controls for
the FPSCR side effect, but they do not demonstrate a changed clamp result or
an incorrect unordered branch outcome. The candidate-vs-original `s0` results
for `unordered-value` (`0x7FC00001`) and `unordered-negative` (`0xFFC00001`)
confirm the NaN value is returned unchanged; `unordered-upper` and
`unordered-lower` both retain `0.5`.

## Producer-reported case audit

I read all 17 report rows. All report `matched=true`, both executions stopped
at the LR sentinel without faults, return `s0` and FPSCR match, callee-saved
integer/VFP state and SP match, and both executions have empty write logs and
unchanged data/stack memory.

| Case | Inputs `(lower, upper, value)` as report bits | Result `s0` | FPSCR |
| --- | --- | --- | --- |
| inside | `0, 1, 0.5` | `0.5` | `0x20000000` |
| at-lower | `0, 1, +0` | `+0` | `0x60000000` |
| below-lower | `0, 1, -0.25` | `+0` | `0x80000000` |
| at-upper | `0, 1, 1` | `1` | `0x20000000` |
| above-upper | `0, 1, 1.25` | `1` | `0x20000000` |
| reversed-inside | `1, 0, 0.5` | `0` (ordered upper clamp) | `0x20000000` |
| reversed-below | `1, 0, -0.5` | `1` (ordered lower clamp) | `0x80000000` |
| reversed-above | `1, 0, 1.5` | `0` (ordered upper clamp) | `0x20000000` |
| equal | `0.5, 0.5, -2` | `0.5` | `0x80000000` |
| unordered-value | `0, 1, qNaN` | original qNaN | `0x30000001` |
| unordered-negative | `-1, 1, negative qNaN` | original negative qNaN | `0x30000001` |
| unordered-upper | `0, qNaN, 0.5` | `0.5` | `0x20000001` |
| unordered-lower | `qNaN, 1, 0.5` | `0.5` | `0x30000001` |
| positive-infinity | `-1, 1, +Inf` | `1` | `0x20000000` |
| negative-infinity | `-1, 1, -Inf` | `-1` | `0x80000000` |
| signed-zero-minus | `-0, 1, -0` | `-0` | `0x60000000` |
| signed-zero-plus | `-0, 1, +0` | `+0` | `0x60000000` |

The runner checks the pinned whole-image SHA and provides direct-entry ARM
executions, but its prose boundary proof is hard-coded rather than derived by
the runner. My independent disassembly confirms that boundary. Its unit test
invokes the runner and compiler; it was inspected but not run in this review.

## Evidence and next action

- Static boundary, callback instructions, setup literals, and caller ABI:
  independently verified against the pinned image.
- Compilation and 17-case differential: producer artifacts inspected only;
  not independently recompiled or rerun. The report lists 17/17 matches and
  rejects the four FPSCR-focused NaN mutant cases.
- Caller/runtime: partial static and synthetic reachability only; live target
  selection is unobserved. No emulator, renderer, or whole-caller equivalence.

Recommendation: preserve the candidate implementation as experimental, correct
the false unordered-GT explanations in source comments, function record, and
producer notes, then have the coordinator decide whether a focused rerun is
needed after those documentation-only corrections. Do not claim NaN clamps to
the upper bound.
