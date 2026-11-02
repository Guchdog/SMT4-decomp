# H2 resource-flag predicate `0x002A63F8` follow-up review (run004)

## Recommendation

The ledger classification is now truthful: `config/functions.csv` marks `0x002A63F8` `non_matching`, consistent with the candidate’s differing final bytes and the staging manifest. The run004 packet pins the current CSV hash, and all 25 declared input hashes match.

The reported staged null-fault comparison is still not established. The offline runner executes the null-result case on the staged image and appends its observation as `null_results[3]`, but the equality chain compares only elements 0, 1 and 2 (original, temporary candidate, final-VMA candidate). It never compares the staged observation’s `fault_instruction_offset`. The report nevertheless claims identical exception and faulting instruction offset for all four profiles. This is a concrete evidence/report mismatch, so I recommend holding review acceptance until the comparison includes the staged result and the regenerated report is pinned. I did not edit the runner or report under this lease.

## Provenance and staging

All 25 `task.json` input SHA-256 values were recomputed and matched. The packet’s pinned `config/functions.csv` SHA is `02dcba6984e9d2945960fb4c3d14f2eecc2fdca1a400333c4769927b8d487236`; the row is `0x002a63f8,24,non_matching,ui,ui_func_002a63f8,src/engine/leaf_batch17_c.cpp`.

The pinned differential report hash is `5d746cfee217fed7c35890f38a7bbf13644ac52e8a708f9264997c9475add609`. The staging manifest hash is `2df226682e405c6a2ece308342865794c145d13197091bd1a86f8606950aee0b`; staged image and IPS hashes are `818f8a104e1761860d3967789994990570838cfc2751d21ddca32caeb8c9cf8d` and `652f61bfb85c751bc26a5abb12a22ebbd4b50d17f1fa85acc0bbf474c6e80de0`. Manifest metadata records a 24-byte slot at `0x002A63F8`, 12 changed bytes, `only_function_slot_changed: true`, and successful IPS round-trip. The final relocated replacement hash is `2ee033ab1928a44ac336a9903c208fcd79724692e779ff082f95d31a338c46c2`, versus original span hash `1a78f57641a26d9c82cbe92258e92c23d6cd94ae61d3ff04fe3e54b0bb86f71c`; non-matching classification is therefore correct. The manifest records the relocation at offset 4 as ARM `BL` to even target `0x002B96F0`.

## Null-fault comparison defect

`execute()` captures `fault_instruction_offset` from the last executed PC relative to the entry and checks each null case faults during a read before completion. The runner then creates observations for original, temporary, final VMA, and—when supplied—staged image. However, its equality expression is only:

```python
comparable(null_results[0]) == comparable(null_results[1]) == comparable(null_results[2])
```

The staged observation at index 3 is omitted. The report’s `null_result_fault` sentence therefore overstates what the runner checks. Staged non-null direct fixtures and the staged `TitleConfig_Calc` call slice are compared separately, but that does not prove the staged null-fault instruction offset. This review did not execute the runner or infer equality from the staged slot’s expected identity.

## Bounded semantic findings

The pinned report describes eight direct fixtures, two detected negative controls, and three `TitleConfig_Calc` slice cases using the production `(group=0x2F, subindex=0)` call. Those results support the bit-2 predicate over the exercised mapped-resource domain, subject to the null comparison limitation above. The runner’s positive direct fixtures compare original, temporary candidate, final-VMA candidate, and staged image; the caller slice compares original, final VMA and staged image.

The null input is an unmapped resolved-record dereference, preserving the original fault path in each individually checked profile, but the staged fault offset lacks pairwise comparison. Invalid table/group addresses, malformed non-null pointers, record lifetime, whole TitleConfig state, and natural runtime/audio behavior remain unproven. Runtime is marked `not_run`; this is an offline bounded review, not whole-image equivalence.

## Next action

Update the offline runner to compare the staged null observation (including `fault_instruction_offset`) against the original, regenerate the report and its hash, prepare a fresh packet, and repeat the narrow review. Keep the ledger at `non_matching`.
