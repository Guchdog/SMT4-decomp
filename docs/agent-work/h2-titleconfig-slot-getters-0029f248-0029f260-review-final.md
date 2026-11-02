# Independent review: TitleConfig ASD slot getter pair `0x0029F248` / `0x0029F260`

## Recommendation

The pair is supported for the tested gate and field behavior, and the run002 ledger rows truthfully classify both helpers as `non_matching`. Their final-VMA ARM tail branches target the intended original getters at `0x002CB84C` and `0x002D5674`; each 20-byte compiled body plus four bytes of slot padding fits its 24-byte slot. The pinned report exercises 76 cases per helper, two negative controls, and four actual `TitleConfig_Calc` caller-slice fixtures against the cumulative staged image. This supports bounded semantic review, not natural runtime or whole-image equivalence.

## Provenance, ledger and final-VMA relocations

All 16 run002 packet input hashes match. The source SHA-256 for `src/engine/leaf_batch34_b.cpp` is `603c8ced2d641cb71dd9d2bf514d86e2fa1c03f9b59b7a8b4063974a9cd52962`; object `build/h2-slot-getters-full/engine/leaf_batch34_b.o` is `cef2b911015fbd0839a6c1328d650390035ba695186196d4c281be2281385b1f`; original image is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; report is `d8e5a2e7f3227b06842be7a1855cdc9b619e3bffbe22c53a6c1154485183dbee`.

The semantic ledger now marks both `0x0029F248` and `0x0029F260` `non_matching`, consistent with the report’s `final_slot_match:false` and distinct original-slot/candidate hashes. I extracted each body and its ELF relocation from the pinned object and independently rebased at its final VMA:

- `camp_func_0029f248`: 20-byte body, one `R_ARM_JUMP24` at `+0x10`. Place is `0x0029F258`, PC is `0x0029F260`, and rebased instruction `0xEA00B17B` decodes to `0x002CB84C`.
- `camp_func_0029f260`: 20-byte body, one `R_ARM_JUMP24` at `+0x10`. Place is `0x0029F270`, PC is `0x0029F278`, and rebased instruction `0xEA00D8FF` decodes to `0x002D5674`.

Both are unconditional ARM `B` tail transfers, preserving the caller’s LR. The staging builder pads each body to the 24-byte slot with one ARM NOP. Final slot hashes differ from original; the semantic ledger labels are therefore correct.

## Contract, differential and caller composition

Each getter tests the unsigned byte at `slot + 0x62`. Any nonzero gate returns zero. Otherwise `0x0029F248` tail-branches to the original field-20 getter at `0x002CB84C`, which reads the word at `slot + 0x20`; `0x0029F260` tail-branches to `0x002D5674`, which reads `slot + 0x24`. The branch targets remain original code, not newly compiled helper bodies.

The runner constructs 12 directed fixtures spanning gate values `0`, `1`, `0x7F`, `0xFF` and distinct/edge 32-bit field values, plus 64 deterministic seeded fixtures (`Random(0x29F248260)`) per getter. Each compares original, temporary, final-VMA, and cumulative-staged execution, checking result, ordered reads, callee-saved registers/SP, completion, and no writes. Both controls are detected: shifting the gate read from `+0x62` to `+0x61`, and redirecting the field-20 getter to the field-24 tail.

The paired caller slice is `0x001EA9F4..0x001EAA0C`. The runner starts at the actual original instructions, uses the work object at `r4 + 0xE8`, calls both getters, and compares original with the cumulative staged image for four gate/field fixtures. Reported `(sum in r4, second return)` results match: `(18,7)` for the ordinary clear-gate case, `(0,0)` for set gates, and `(2147483647,4294967295)` for the edge-value fixture. I also compared the caller slice and both tail-helper byte ranges in the cumulative run-013 base against the pinned original; those ranges are unchanged. The cumulative stage carries the prior `0x002A63F8` predicate replacement and patches only its declared slots. Its manifest hash is `e9beb0fa72a1a56b3483560c2a4d7b2c891d4d84310c69432d1590d29ed0c971`; staged image and IPS hashes are `b71fece339cc135393f03a4e806bcf5a2d158cfe1ed8402df249c3613d933140` and `ad0999bdc0b93fd16ad8408b03fcfe886175d1e7a7d08dd68459945f8c9a5661`. Applying the IPS reproduces the staged image exactly. The manifest records 28 changed bytes total (including the carried predicate) and `only_declared_function_slots_changed:true`; all changed bytes fall within the two getter slots or the declared predicate slot.

## Limits

The report’s compilation, differential and caller results are pinned evidence; I did not compile or rerun the runner. Runtime is `not_run`. Fixtures use mapped slot memory and do not establish behavior for invalid/unmapped pointers, concurrent mutation, natural title-config lifecycle, or whole-game behavior. The two tail getters remain original-code dependencies.
