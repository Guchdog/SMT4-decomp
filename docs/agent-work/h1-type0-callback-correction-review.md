# Correction review: type-0 callback unordered VFP semantics

## Verdict: partial

The corrected semantic explanation is right. Pinned `VCMPE` unordered flags
are `NZCV=0011` (`N=0,Z=0,C=1,V=1`); ARM `GT` (`!Z && N==V`) and `LO`
(`!C`) are both false. Therefore the upper branch is not taken for unordered
operands, and the lower conditional move is not taken if its comparison is
unordered. The corrected candidate and function record now describe this
accurately. The fresh producer report retains all 17 case results and records
the four ordered-comparison mutant cases with identical `s0` and differing
FPSCR invalid status.

I did not compile or execute anything. Fourteen packet inputs hash-match. The
pinned image remains SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Corrected candidate source hash is
`6d7573062f2df84e9aba2387667804d52ea15a25220f6d1d5c6fa5f26d9fb103`, runner
hash `762b4d1b56a3018e9c86ad9ffd880bd10c7c0bbceda024f559bc3237236cbba3`, test
hash `e624d3078c7bd5bd74a9347d4d32634c86eb53b5a33ddd851ba256e845b78c86`,
object hash `ee094897c154f1171aaf52c308f0ef12a027ffd16ef55cc6ada8f273db748eae`,
fresh report hash
`760c366f7ddd9a784ada8bf3a03ed2855f9e9293cae72c7b055ed1f365c5b26b`, and
correction handoff hash
`a4d965911f09ca40500fd2a476bbc91dcd117b9a1328aeb354d75859ffe519b1`.
The object and candidate code hashes match the prior compile because the
correction changed comments/names/documentation, not generated behavior.

## Corrected contract and report cases

Pinned code still has the direct callback entry at `0x0015555C`, immediately
after the predecessor's `pop {r4,pc}` at `0x00155558`. It compares `value`
against `upper` first, uses GT for the upper clamp/early return, then compares
against `lower` and uses LO for the lower clamp. This order explains reversed
bounds. Inputs are hard-float `(lower=s0, upper=s1, value=s2)` and the result is
in `s0`. The candidate's `vfp_greater_than`/`vfp_less` names and comments now
state the proper unordered behavior; the function record and candidate work
note also state that NaNs are not clamped by GT/LO. The review's source/work
search found no active source, function-record, or candidate-work statement
claiming unordered GT takes the upper branch.

All 17 fresh report rows say `matched=true`, no fault, identical result bits
and FPSCR, preserved compared callee-saved state/SP, no memory writes, and
unchanged data/stack. The four unordered rows are:

| Control case | Original/wrong `s0` | Original FPSCR | Wrong FPSCR |
| --- | --- | --- | --- |
| unordered value | `0x7FC00001` / `0x7FC00001` | `0x30000001` | `0x30000000` |
| unordered negative value | `0xFFC00001` / `0xFFC00001` | `0x30000001` | `0x30000000` |
| unordered upper bound | `0x3F000000` / `0x3F000000` | `0x20000001` | `0x20000000` |
| unordered lower bound | `0x3F000000` / `0x3F000000` | `0x30000001` | `0x30000000` |

The corrected test now explicitly asserts same `s0` and different FPSCR for each
of these four controls. These are four input cases for one ordered-C++ mutant,
not four independent mutants.

## Remaining measurement caveat

The request that the controls “differ only in FPSCR” is true only for the
reported contract projection. The runner's comparison records `s0`, FPSCR,
`r4-r11`, SP, `d8-d15`, writes, and data/stack unchanged flags; it does not
capture caller-saved VFP registers `s1-s15`. Static object inspection shows
the original executes `vmov s3,s0` on entry, while the wrong-comparison object
does not write `s3`. Thus the control and original may also differ in caller-
saved `s3`; this is allowed by the callback ABI, but it prevents claiming full
register-state difference is limited to FPSCR. Rephrase that claim as
“same `s0` and other checked ABI/memory fields, with FPSCR differing,” or add a
separate caller-saved-register observation if exact full-state evidence is
desired.

The earlier review note
`docs/agent-work/h1-type0-callback-review.md` still has a historical section
phrased “These artifacts currently contain incorrect wording” and lists the
old claims. It does not describe the corrected contract as true, but should be
marked as superseded or updated so the review history does not look current.

## Evidence boundary and next step

This is read-only static review of the corrected source/docs, pinned ARM, fresh
object and report; the run-02 compile/differential and 3-test result are
producer-reported, not rerun by this reviewer. Runtime target selection remains
unknown. No integrated caller, physical hardware, renderer, emulator title
session, or whole-game equivalence is established.

Recommendation: accept the corrected unordered semantics and all 17 reported
candidate cases as bounded experimental evidence. Keep the negative-control
claim scoped to checked fields and FPSCR, mark the prior review note as
superseded, and retain caller/runtime limitations before considering
integration.
