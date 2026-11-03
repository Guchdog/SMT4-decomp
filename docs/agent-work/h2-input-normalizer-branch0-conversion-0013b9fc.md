# H2 selector-0 radial normalizer conversion — `0x0013B9FC`

## Result

Replaced the 228-byte naked ARM body in `src/engine/leaf_batch30_a.cpp` with
typed C++ that preserves 32-bit wrapped square/product arithmetic, signed
branches, the integer Newton square-root estimate, three calls to the original
signed divider `0x002C615C`, deadzone Y-then-X stores, non-deadzone X-then-Y
stores, low-halfword outputs, and the sign-extended low-halfword return.
Updated the reader-side C++ declaration in `leaf_batch29_a.cpp` from `u32` to
`s32` to state the recovered return contract.

## Validation

- Candidate body: 208/228 bytes.
- Direct original-vs-candidate cases: 107/107 matched.
- Original reader/caller compositions: 16/16 matched.
- Zero-divisor coverage: 14 direct fixtures contained zero-denominator cases,
  producing 28 final X/Y quotient-call entries; original and candidate traces
  and results matched.
- Negative controls: 3/3 detected (inner calibration used as outer, deadzone
  write order reversed, and divider denominator incremented).
- Three `R_ARM_CALL` relocations target even ARM address `0x002C615C`; the
  original selector-0 callsite at `0x00128678` is an ARM call.
- Exact-slot IPS replay and the one-slot-only patch audit passed.
- Both affected TUs compiled successfully into private output objects.

Primary report:
`build/agent-work/H2-semantic/h2-input-normalizer-branch0-convert-0013b9fc/run001/checks/coord-final2-20261106/report.json`.

## Scope and remaining limits

Direct cases use valid disjoint synthetic ordinary RAM; caller compositions
use the original dispatcher and reader with a controlled ring-reader seam. The
original divider remains a runtime dependency. Pointer aliasing, malformed
pointers, MMIO, concurrent mutation, physical input provenance, and whole-title
runtime behavior remain untested. Signed reinterpretation of wrapped 32-bit
values and arithmetic right shift are verified for the pinned ARM compiler and
target, not claimed as host-independent C++ semantics.

Independent review found no in-domain counterexample and confirmed the corrected
228-byte span `[0x0013B9FC,0x0013BAE0)`. Its fresh run reported the 14 fixtures
and 28 final quotient-call entries above; the independent seed reported 12
fixtures and 24 entries. Static inspection corrected the contract's epilogue
to `ADD SP,SP,#0x10` at `0x0013BAD4`, followed by `MOV r0,r1` and the register
pop. The independent review is recorded in
`docs/agent-work/h2-input-normalizer-branch0-independent-review-0013b9fc.md`.
