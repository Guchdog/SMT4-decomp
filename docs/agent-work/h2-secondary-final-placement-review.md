# Independent review: H2 Calc + Draw + Secondary final placement — run-001

## Decision

The run-012 merged artifact is identity-consistent and its IPS round-trips exactly to the patched image. The production Secondary body is present at its final VMA, unchanged from the extracted 292-byte object, and the original entry branches to it. The placement fits the audited page-tail cave with exactly 8 bytes remaining. Both-seed final-address comparisons pass for Calc, Draw, and Secondary, with detected negative controls including a wrong-count Secondary mutant at the same VMA. I recommend retaining/promoting Secondary's byte classification as `non_matching`, limited to this reconstructed callback and its declared HLEs. This is not title/runtime acceptance.

## Identity and independent patch check

Every `input_sha256` in `build/agent-work/H2-semantic/h2-secondary-final-placement-review/run-001/task.json` matched the checkout before review. Recomputed identities also match the manifest and task packet:

| Artifact | SHA-256 |
| --- | --- |
| Pinned `code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Combined `code.bin` | `84c6eb66a6f9a2a23d46e08df4eb04d723fef852c0b8bd3405945f9dbdd5ae32` |
| Serialized IPS | `f5369e77ddfe48f93d46ffbb8670819cc432039589c51aac6e6c67af9d9b8376` |
| Manifest | `28de5a9c2530792dc7307c657d814af86bf6affa6e1404972a78e62a12a536fc` |
| Final-address validation report | `2d7a40f720cd5ca994423c2b7e4fe712a8f85517231f8cc1edcede77036fc968` |
| State-9/10 caller report | `74f83e4caf3c0af5a44509dd080c618936065a05cef32f05eed0291f9d86309f` |

I independently decoded the IPS stream and applied its records to the pinned original. There are no trailing bytes after `EOF`; all four record offsets, lengths, and payload hashes equal the manifest. Reapplication reproduces the combined image byte-for-byte. The 3,413 differing bytes all lie inside the four authorized records; no changed byte lies outside them:

| File offset | Length | Purpose |
| --- | ---: | --- |
| `0x000EA928` | 4 | Calc entry branch |
| `0x001CAEF0` | 4 | Secondary entry branch |
| `0x001CAFD0` | 1,464 | Draw replacement body |
| `0x002FE624` | 2,524 | Entire audited text-tail cave |

Source and object identities from the manifest were checked against the current files:

| Component | Source SHA-256 | Object SHA-256 | Extracted symbol |
| --- | --- | --- | --- |
| Calc | `c76ab50c12589404ca81e35373c8b136c50c91eb63c5af805bf05cc44c6081c7` | `94197ad141393099a25e679b73457f127c54c7155fa4d8c2ff25270f8ca620fd` | `script_vm_func_001ea928`, 2,096 B |
| Draw | `e5c6414cd37d2d6fc9928ca85eb5466a8c07bcec224a887616cb383ac408d64c` | `0513196e3d93398036feba0177fc92cadadba87589068dc0605da64b0658ede2` | `ui_func_002cafd0`, 1,464 B |
| Secondary | `3ca4676613634ae91fe980e5e6e3c79fa74aff355e0facc50149749ba10b9c37` | `e04b6dcb9ae560efa2e39202b04763263b03f1f61455efe5b54756ffda81d53e` | `engine_func_002caef0`, 292 B |

The extracted Secondary symbol hash is `e2e714f635eee7874699fde891189dfed1298d225a21423554077152e66d4913`; it has zero ELF relocations. Its 292 bytes in the combined image at file offset `0x002FEED4` are byte-for-byte identical to the extracted object symbol. The Calc source/object identity is consistent with its four manifest `R_ARM_ABS32` relocations; the combined image words at body offsets 60, 64, 68, and 72 are respectively `0x003FE670`, `0x003FE7E4`, `0x003FE790`, and `0x003FE7C8`. The Draw object has seven `R_ARM_CALL` relocations and one format-literal relocation; the combined image's seven call words target `0x003FEE54`, and its format literal at offset 1460 is `0x003FEED0`.

## Address map and branches

The combined builder's map is internally consistent:

- Calc body: `[0x003FE624, 0x003FEE54)`, 2,096 bytes.
- Draw helper: `[0x003FEE54, 0x003FEED0)`, 124 bytes.
- `%s\0`: `0x003FEED0` through `0x003FEED2`, then one byte of alignment padding.
- Secondary body: `[0x003FEED4, 0x003FEFF8)`, 292 bytes.
- Audited cave: `[0x003FE624, 0x003FF000)`, 2,524 bytes; 2,516 bytes occupied after alignment and 8 bytes left.

Decoding the patched ARM entry words gives `0x001EA928 -> 0x003FE624` (`0xEA084F3D`) and `0x002CAEF0 -> 0x003FEED4` (`0xEA04CFF7`). The Secondary entry branch is within the original 224-byte function span and the body is four-byte aligned. The no-relocation assumption is additionally supported by exact object-to-final-image byte equality and the final-VMA differential. The cave has only 8 bytes of margin, so any future payload or changed alignment requires a new layout review.

Draw remains an in-place replacement at its original entry. It returns at `0x002CB55C`, before the retained suffix starts at `0x002CB588`. The manifest's prior reachability audit records the two old main-to-suffix edges as overwritten, no aligned absolute pointer hits into the suffix, and a suffix back-edge into the replacement body. The current review did not repeat the complete direct-reference/interior-entry audit; placement relies on that separate audit and its bounded indirect-entry limitation.

## Final-address results and negative controls

The final-validation report is bound to the pinned original, combined image, and frozen `tools/h2_combined_offline_validation.py` hash. It records:

- **Calc:** 16/16 persistent sequences, 54/54 ticks pass; the wrong logical-map control is detected as a work-state mismatch.
- **Draw:** 46/46 directed cases pass; the helper-target-plus-four mutant faults on `active-selected-row-0`.
- **Secondary:** 34/34 cases pass, 17 each on seeds 7 and 20261024. Cases cover zero/negative/one/four counters independently, each nullable cleanup slot, both task predicate outcomes, manager values 9–12, and distinct simultaneous loop counts. The wrong-count mutant was placed at the same `0x003FEED4` VMA and reached through the patched entry; the `both-loops-distinct` case detects its changed helper arguments/order. The mutant body is 296 bytes, which still fits in the remaining post-Secondary 300-byte area for the control run.

All three component reports have no first counterexample. Their results support the callback behavior under the harness's stated models, not full engine services.

## Caller composition and promotion boundary

The caller report passes all 3 State-9/10 cases and detects the wrong primary Calc-callback address. It explicitly runs the pinned MainTitle caller/readiness path against the combined image, but compiles and injects the separate initializer experiment candidate at synthetic VMA `0x01004000`; it does not use the production initializer or its proposed string pool. It compares registration tuples and work/handle linkage. It does **not** schedule or execute the registered Calc, Draw, or Secondary callbacks.

The `non_matching` Secondary ledger label is appropriate: the production source differs from the original bytes, and the final image places that source-derived body at the audited final address with a same-address sensitivity control. This supports a bounded production-callback promotion, not H2 end-to-end completion. Helper cleanup/release/task internals and the callback scheduler remain HLE/trace boundaries. No real task lifetime or callback timing/count, visible UI, settings edit flow, save/persistence, profile, Azahar, or runtime behavior was tested. The merged image also excludes the production initializer, and the ready-gate body remains excluded pending its size/span issue.

## Next action

Keep the Secondary classification `non_matching` and retain the linked bounded function evidence. Integrate a reviewed production initializer/string-pool and resolve the ready-gate span before claiming a complete H2 caller path. A separate scheduler/runtime task must observe when callbacks run and whether their cleanup effects match the HLE model; UI and persistence remain independent acceptance evidence.
