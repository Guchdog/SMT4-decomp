# H2 selector-1 normalizer conversion — `0x0013B8F8`

## Result

Replaced the 260-byte naked ARM body in `src/engine/leaf_batch28_a.cpp` with
typed C++ implementing the signed per-axis deadzone transform, wrapped
distance/F comparisons, direct and scaled output branches, original integer
Newton estimate, three calls to the original signed divider, ordered halfword
stores, and signed low-halfword return. Updated the dispatcher-side declaration
in `leaf_batch29_a.cpp` to the recovered `s32` return type.

The historical H4 static contract had conflated sign-extended halfword
`-32768` with signed 32-bit `INT32_MIN`. Corrected the H4 recon/review record:
caller value `-32768` negates to `+32768`; only direct `INT32_MIN` wraps to
`0x80000000`. Both cases are covered in the candidate differential.

## Validation

- Candidate body: 252/260 bytes.
- Direct original-vs-candidate cases: 176/176 matched.
- Original reader/caller compositions: 16/16 matched.
- Zero-denominator paths: 31 direct fixtures observed, original and candidate
  outputs/call traces matched.
- Negative controls: 3/3 detected (unsigned compare after wrapped
  `INT32_MIN` negation, `>=` instead of `>` at the radial boundary, and
  reversed direct-store order).
- Three `R_ARM_CALL` relocations target even ARM address `0x002C615C`; pinned
  selector-1 callsite `0x00128698` targets the even ARM candidate entry.
- Exact-slot IPS replay and one-slot-only audit passed.
- Both implementation and consumer TUs compiled into private output objects.

Primary report:
`build/agent-work/H2-semantic/h2-input-normalizer-branch1-convert-0013b8f8/run004/checks/final-seed-20261110/report.json`.

## Scope and remaining limits

Inputs use valid disjoint synthetic ordinary RAM. Caller composition uses the
original dispatcher/reader and a controlled ring-reader seam; the original
signed divider remains a dependency. Aliasing, malformed pointers, MMIO,
concurrent mutation, physical input provenance, and whole-title runtime
behavior remain untested. Wrapped signed reinterpretation and arithmetic shift
are target-specific to the pinned ARM compiler. Independent review is the next
gate before ledger/README promotion.
