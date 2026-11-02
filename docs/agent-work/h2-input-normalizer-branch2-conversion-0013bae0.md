# H2 selector-2 normalizer conversion — `0x0013BAE0`

## Result

Replaced the 460-byte naked ARM body in `src/engine/leaf_batch44_c.cpp` with
typed C++ for the signed-wrap radius setup, direction-dependent VFP boundary,
clamp, interpolation/direct scaling branches, toward-zero conversions,
ordered halfword stores, and residual output-pointer return. Updated the
dispatcher declaration in `leaf_batch29_a.cpp` to the observed `s16*` return
contract and converted it back to raw `r0` at the parent ABI boundary.

## Validation

- Candidate body: 368/460 bytes, with no relocations.
- Direct original-versus-candidate cases: 352/352 matched.
- Original reader/dispatcher compositions: 18/18 matched across two seeds.
- Mutation controls: 3/3 detected (boundary extent, missing 1600.0 clamp, and
  rounding bias instead of truncating conversion).
- Selector-2 callsite `0x00128658` targets even ARM entry `0x0013BAE0`.
- Exact-slot IPS replay and one-slot-only audit passed.
- `leaf_batch29_a.cpp` and `leaf_batch44_c.cpp` compiled successfully.

The runner records FPSCR values but does not include exception flags in its
acceptance predicate. The currently recovered contract supports output bytes,
write order, raw return, core callee-saved registers and stack restoration for
the tested ordinary finite inputs; it does not establish exceptional FPSCR
behavior.

Primary report:
`build/agent-work/H2-semantic/h2-input-normalizer-branch2-convert-0013bae0/run003/report.json`.

## Scope and remaining limits

Fixtures use valid disjoint synthetic ordinary RAM, original reader/dispatcher
code, and a controlled ring-reader seam. The evidence emphasizes the
parent-reachable signed-halfword domain. Invalid pointers, aliasing, MMIO,
concurrent mutation, unusual floating-point exception domains, physical input
provenance, and whole-title runtime behavior remain untested. Independent
review is required before ledger and milestone promotion.
