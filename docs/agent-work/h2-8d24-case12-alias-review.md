# Independent review: selector-12 cross-alias coverage for 0x002B8D24

## Recommendation

The new selector-12 fixture validly closes the specific five-call cross-alias gap identified in the prior `0x002AF854` record. I found no counterexample in its address construction, call order, alias chain, or candidate/original comparison. The semantic candidate for `0x002B8D24` is supported for the exercised domain and is suitable to proceed to integration review. This is not yet approval to call the production replacement complete: final-image ARM/Thumb interworking checks and the defined original-versus-patched H2 runtime comparison remain outstanding, as do the documented domain limits below.

## Independent fixture review

The pinned original helper at `0x002B8D24` dispatches selector 12 to its loop at `0x002B8E40`. The loop tests flags at object offsets `+0x37..+0x3B` in ascending order. For each set byte it calls `0x002AF854` with `r0 = object + 0x498 + 140*i`, `r1 = 5`, and `r2 = 0`; after the fifth possible call it clears the word at object `+0x28` and returns zero. The candidate expresses this same order and offsets. In the fixture all five flag bytes are set, so exactly five calls are expected.

The concrete subobject offsets are `0x498`, `0x524`, `0x5B0`, `0x63C`, and `0x6C8` (stride `0x8C`, or 140 bytes). Each subobject's list pointer at its `+0x58` is initialized. For the first subobject it is the mapped list at `0x910000`; its selected word at list `+5*12 = +0x3C` is `0x12345678`. For each later subobject, the list pointer is the preceding subobject's `+0x20`, so the helper's selected read at list `+0x3C` aliases the preceding subobject's `+0x5C`.

This is a real sequential cross-alias: each helper writes its own `+0x5C` halfword with index 5 before reading the selected word. Thus call 1 supplies `0x12345678` to the first subobject's `+0x20`; call 2 reads the first subobject's newly written `+0x5C` value 5 and stores it to the second subobject's `+0x20`; calls 3–5 propagate 5 the same way. The runner asserts the ordered call arguments and the resulting selected values `[0x12345678, 5, 5, 5, 5]`. It also compares return, SP, `r4-r11`, the full `0x1200`-byte object fixture, call events, and ordered non-stack writes. Both seeds use this same valid, mapped address topology with distinct deterministic initial bytes.

The alias-aware `0x002AF854` candidate preserves the relevant original ordering: its `+0x5C` index write occurs before the selected list-word read. This ordering is material because the later list bases resolve to the preceding subobject's just-written `+0x5C`. The paired chain compares original `0x002B8D24` plus original `0x002AF854` against candidate `0x002B8D24` plus alias-aware candidate `0x002AF854`; the prior direct and caller matrices separately compare `0x002B8D24` while retaining the original dependencies. This separation makes the new chain useful evidence for the joint alias-aware implementation without pretending the chain alone isolates either candidate.

The preserved output is `build/agent-work/H2-semantic/h2-helper-002b8d24-case12-alias-coverage/001/offline-output.txt` (SHA-256 `7c7873a9c74d907cea2f042955a0213bb8a1fb1ce5d5153cdd603e615b8ca8ce`). It reports 116 direct cases, two `0x00286928` compositions, two five-call cross-alias chains, all seven configured negative controls detected, and function bodies of 356/64 bytes. The direct matrix retains original callees; the new chain intentionally installs the alias-aware `0x002AF854` candidate. The controls cover selector-6 raw return, wrong second subobject, wrong stride, shortened loop, wrong selector, wrong tail byte, and failure to clear `+0x28`. The selected `0x002AF854` mutation controls are also detected by their corresponding existing runner evidence; they are not additional counts in this output.

## Limits and next gate

- The two new chain cases cover one carefully selected alias topology and index/mode pair (`5/0`), not every possible overlap among object fields, list storage, and derived subobject pointers. Invalid addresses, fault parity, MMIO, concurrency, and pointer-wrap domains remain unsupported.
- The `0x00286928` compositions shown by this run exercise the caller's selector-11 route (the runner stores selector 11 in object byte `+9`); they do not establish a real caller composition for selector 12. The five-call fixture enters `0x002B8D24` directly with a synthetic object.
- No emulator or integrated patched-image scenario was run here. Before production promotion, run the required final-image ARM/Thumb interworking checks and the project-defined original-versus-patched H2 runtime comparison, with the `0x002AF854` dependency state explicit. Keep the production byte classification truthful (`non_matching` if the staged bytes differ).
- The helper's documented ordinary-RAM, valid aligned-memory, non-overflowing-pointer assumptions and the broader unresolved semantics of other selectors/dependencies still bound the claim. This review does not establish whole-game equivalence.

## Handoff

Review file: `docs/agent-work/h2-8d24-case12-alias-review.md`. Recommendation: accept this alias-coverage task and allow the `0x002B8D24` candidate to proceed to integration/runtime gates; do not treat those gates as completed by this offline review.
