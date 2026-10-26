# Experimental candidate — `0x002BF9F0`

## Result

The leased candidate translates the supported field behavior/control flow into
readable C++ with the original external calls left as explicit dependencies.
The pointer stays opaque; no type or initialization is assigned to H1's
`scene+0xD74` subobject. Source remains unintegrated.

The pinned helper contract and independent static review are in
[`h1-preview-helper-contract.md`](h1-preview-helper-contract.md) and
[`h1-preview-helper-contract-review.md`](h1-preview-helper-contract-review.md).
This candidate recovers the early null/signed gate, unchecked row and sequence
indexing, fixed-point endpoint/interpolation paths, sequence sentinels, the
common completion calls, and `+0x8A`/`+0x85` tail behavior.

## Differential evidence

The private ARM run is
`build/agent-work/H1-semantic/h1-preview-helper-candidate/overnight-20261025-preview-helper-candidate/checks/final-evidence/report.json`.
It compiled the candidate with named stubs and executed both the pinned original
body and linked C++ on Unicorn ARM11 MPCore. Thirteen fresh byte-array fixtures
passed: null and signed early returns, the second-gate continuation, completed
short circuit, null row table, endpoint/completion, row-mode sequence bypass,
interpolation, ordinary sequence entry, null sequence, current-entry `-1`,
next-entry `-1`, and next-entry `-2` restart. Comparison covers r0, r4-r11, SP,
FPSCR, relevant external-call arguments/order, and the full mapped synthetic
data region. A compiled negative control with the disabled-sequence `+0x86`
store removed was detected by the endpoint/completion fixture (r0 and memory
differed).

The interpolation stub returns signed 32-bit `delta / duration`, or zero for
zero duration. Animation and three common-tail stubs return zero; all stubs omit
the original callees' memory effects and transitive calls. This tests the
candidate's call boundaries and surrounding behavior only under that synthetic
stub contract. The fixture row and sequence pointers are valid for the selected
indices; there are no bounds checks in the original. No runtime/caller evidence
is claimed.

During development, the first semantic counterexample was the endpoint case
with sequence feature `+0x84 == 0`: original stores 1 to `+0x86` at `0x002BFB58`
and returns 1, while the first draft left `+0x86` clear and returned 0. That
store was added and the same case is now included in the passing final run and
as a compiled negative control. Subsequent differential inspection corrected
the row-mode branch (nonzero mode bypasses sequence processing) and established
that ordinary sequence animation arguments come from the incremented/next entry.
No mismatch remains in the listed synthetic run; the counterexamples are
recorded as development findings, not as passing evidence for earlier drafts.

## Identity and commands

- Pinned image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Original helper body SHA-256: `9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e`.
- Final candidate SHA-256: `64c3964b0abae2c0ff6e51d1e9ef5961c8e8d0769e177c528a878d4b094b3282`.
- Linked candidate ELF SHA-256: `8c5dbdc24e7b86652f3c6604f3c830758c83aa1ddfbfc73f365eaa708decf33b`.
- Differential report SHA-256: `fe7789fab0d4d130f7fbada09523747eb014295b99e080514f0e2a247d63b35a`.
- Runner command: `python tools/h1_preview_helper_experiment.py --output build/agent-work/H1-semantic/h1-preview-helper-candidate/overnight-20261025-preview-helper-candidate/checks/final-evidence` — exit 0, 13/13 cases and negative control detected.
- Focused test command: `python -m unittest tests.test_h1_preview_helper_experiment` — exit 0, 2 tests.

## Limitations and next action

All five original callee bodies remain unresolved dependencies in this evidence;
they were replaced by deterministic named stubs. Valid synthetic object graphs
do not prove the H1 allocation/constructor path or actual runtime bindings for
`scene+0xD74`. Caller tests, physical runtime behavior, integration, and an
independent candidate review were not run. Next action: assign independent
review against the pinned ARM plus this frozen report, then decide whether a
separate H1 object-lifecycle/callee contract can support a caller-level test.
