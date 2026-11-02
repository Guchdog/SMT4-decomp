# Independent review: `0x00207D84` generic UI transform

## Recommendation

The C++ candidate passes the fresh bounded direct and caller comparisons for the exercised finite, valid-pointer domain. It is suitable as a semantic candidate for that generic UI transform. **Do not promote this staging patch into the current cumulative H2 image.** Its proposed cave address overlaps code/data already allocated by the combined Draw/Secondary image, and the review does not establish any direct TitleConfig/Audio Settings reachability. A new complete-image placement is required before integration; runtime and screen-level behavior remain unverified.

## Provenance and fresh differential

All declared `input_sha256` entries in `build/agent-work/H2-semantic/h2-ui-transform-review-00207d84/run001/task.json` were checked against disk and matched. The assigned run used a distinct output directory:

```text
python -B tools/ui_transform_00207d84_experiment.py --out build/agent-work/H2-semantic/h2-ui-transform-review-00207d84/run001/checks/review-001 --seed 20261103
```

Exit code 0. The fresh report is `build/agent-work/H2-semantic/h2-ui-transform-review-00207d84/run001/checks/review-001/report.json` (SHA-256 `b8888d743ef699c7a704642a48b676ed8a10e94acf29c031789b307147ebcb49`). It binds to the pinned original image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, candidate body SHA-256 `c4a9946b65102674b3c438d1ec5b541a62dfa5b0dc98cc5c5f2b6397b405f8f6`, 156-byte body and 128-byte original slot.

All 7 direct fixtures and all four FPSCR rounding modes RN/RP/RM/RZ matched. The comparisons include the four vector words, four scratch words, ordered writes to both global ranges, `r0`, `s0`, FPSCR, SP, r4-r11, s16-s31 and caller-owned stack. Both original `0x0024B874` callsites at `0x0024B8E0` and `0x0024B908` executed in the `[r4+0x9C] == 2` path, and both caller compositions matched. The generic helper calls `0x002698F4` and `0x00269768` and final service `0x0024C62C` were stubbed; the latter returned fixed `s0=0.125`. Projection callees `0x002C5218` and `0x0026330C` remained original. Thus caller evidence is partial and does not validate those external services.

The three declared controls (x/y swap, omitted zero-word store, and scratch mutation) were detected. They are comparator-observation controls, not independently compiled semantic mutants. IPS replay passed and the report says no writes outside the entry plus cave. The candidate has two ARM `R_ARM_CALL` relocations: `0x003FEE68 -> 0x002C5218` and `0x003FEEB0 -> 0x0026330C`; both targets are even ARM addresses. The entry word at `0x00207D84` is `0xEA07DC32`, an ARM `B` whose decoded target is `0x003FEE54`; this is within ARM B range and preserves incoming LR. The cave scan reports 428 zero bytes and no aligned pointer/static branch/literal references in the pinned base image. This proves only the synthetic base-image placement, not availability in the cumulative package.

## Cumulative image collision — integration blocker

The current final H2 manifest is `build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/combined-build-final/manifest.json` (SHA-256 `4002ab29da801d36eafd17fd728d0473f50d7d10ec6c786ba3135b6b431140cf`) and binds to combined image SHA-256 `cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4`. It allocates the same tail as follows:

- Calc body: `[0x003FE624, 0x003FEE54)`, 2,096 bytes.
- Draw helper: `[0x003FEE54, 0x003FEED0)`, 124 bytes.
- Draw format literal `%s\0`: `0x003FEED0..0x003FEED2`, followed by alignment to `0x003FEED4`.
- Secondary body: `[0x003FEED4, 0x003FEFF8)`, 292 bytes; the complete cave has only 8 bytes left.

The candidate staged at `0x003FEE54` ends at `0x003FEEF0`. It would overwrite the full Draw helper, its format string/alignment region, and the first 28 bytes of Secondary. The separate Calc-only staging's 428-byte zero-tail observation is therefore not cumulative free space. No existing cumulative package can accept this placement as-is; the 156-byte body cannot fit the remaining 8 bytes. Move/repack the combined cave or redesign the integration as a complete-image change, then rerun the integrated offline validation and caller checks before any runtime test.

## Compile evidence and ledger

The conversion handoff records four affected-TU compiles with exit 0. The saved objects are present and their hashes match that record: `leaf_batch30_c.o` `7d1bf2461543ccb0e7d3b2fd82c9edcdabe58a4d59e926dbd43cda65fd671829`; `leaf_batch21_b.o` `857958e88c81502be6bbcb17686b7dfd94964d2f4c7ca96ce8ee19b3ab8cb34b`; `leaf_batch40_b.o` `73c7d0d4433f5cbab917cc66cfb74f00d5fde62f7571300a90accb6191266eb4`; and `leaf_batch41_a.o` `264362a05d1f50d907784b043780938a4f3417699210edd76ce5ca3d29774787`. This is affected-TU compile evidence, not a full build.

The 10,967-row ledger currently totals 10,904 `matching`, 55 `non_matching`, and 8 `matching_span`. `0x00207D84` is still labeled `matching` despite its 156-byte non-identical candidate. A truthful row change to `non_matching` would yield 10,903 matching, 56 non-matching, and 8 matching-span rows, preserving 10,967 total. This coordinator-owned correction is required if/when promoted.

## Claim boundary

The target remains a generic UI transform. Contract review identifies only generic consumer `0x0024B874` and the two guarded callsites. No direct TitleConfig/Audio Settings path, natural H2 scheduling, runtime reachability, visible-screen behavior, or whole-game equivalence was established. The fresh run was offline; no emulator or runtime was used.

## Next action

Keep the semantic candidate and its bounded evidence. Block promotion at the current cave address. Ask the integrator to produce a non-overlapping complete H2 layout (or an in-slot implementation), update the truthful ledger classification as part of promotion, and rerun the cumulative offline gate. Preserve the generic UI/no Audio Settings claim unless a concrete caller/runtime trace establishes more.
