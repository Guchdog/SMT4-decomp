# Independent production integration review: `0x002892C0`

**Task:** `h2-titleconfig-002892c0-production-review`, run001
**Recommendation:** The bounded production placement is supported on the exact Calc-only base image. Do not treat it as integrated into the accumulated five-callback H2 image or as runtime/H2 evidence.

## Provenance and independent rerun

All 17 hashes declared in the review packet recompute exactly. The original `code.bin` is pinned at `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

I reran the production builder with one compiler job into the fresh output directory `build/agent-work/H2-semantic/h2-titleconfig-002892c0-production-review/run001/checks/recheck-run004/`. The run exited 0. Its combined image, IPS, manifest, final-address report, production object, helper body, production source, and runner hashes match run003. Combined image SHA-256 is `1d994ed8667ba97c084719d7ecf61934e005e938bdd22c7d160207c9953f4355`; combined IPS SHA-256 is `1419cbfe64feda2062879f1ad14316a6fc7e71704cdab8c78fbe252d8ad100c3`.

The exact base exercised by the helper comparison is the independently validated Calc-only image, SHA-256 `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`, built from the pinned original. The production helper source is `src/engine/leaf_batch16_c.cpp`, SHA-256 `584582c0a9f7831ec985a5ef62c36ca44141c778168dbe256abc72545359402d`; object SHA-256 is `8685537de0589910b26a0b695b50607a791220e5f9e0a277b57a2a8e89ef97ae`; extracted helper body SHA-256 is `32ed9c8c6ad393ddc586da13a9b667115f3847f4928fb0cd54aadf9718f964fc` (136 bytes, zero relocations). The output manifest identifies the compiled symbol and records these values; I independently extracted the symbol from the fresh object and confirmed that the body at the candidate VMA matches it.

The run001 packet omitted the transitive Calc source, but the updated run002 packet now pins `experiments/semantic_equivalence/h2_calc_candidate.cpp` at SHA-256 `16f2af7c953a089ffe277d2f299ea89ab90d028f57d6708ffdc8cf6115844ed2`. I recomputed all 18 run002 input hashes; they match. The added source hash agrees with both the fresh Calc-base manifest and report. The Calc-base output hash remains the expected `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`, so no builder rerun was needed.

## Patch layout and final-address audit

The original helper span is 124 bytes (`[0x002892C0, 0x0028933C)`); its production body is 136 bytes, so in-place replacement would overwrite the adjacent function. The builder keeps the following code and installs the body at `0x003FEE64` in the executable `.text` page tail `[0x003FE624, 0x003FF000)`. The Calc-only base uses the first 2,096 bytes of that tail. The remaining 412-byte reserved helper range is zero-filled; the 136-byte body occupies `[0x003FEE64, 0x003FEEEC)` and leaves 276 bytes.

At the original entry, the emitted bytes `e7d605ea` decode as an unconditional ARM `B`, without link, from `0x002892C0` to `0x003FEE64`. The destination is aligned and even. The combined IPS has four nonoverlapping records: Calc entry (4 bytes at file offset `0x0EA928`), helper entry (4 bytes at `0x1892C0`), Calc cave body (2,096 bytes at `0x2FE624`), and helper body (136 bytes at `0x2FEE64`). I independently reapplied the combined IPS to the pinned original and confirmed byte-for-byte equality with the emitted combined image. The original input remains identified by its pinned hash.

The final-address report compares original and patched helper entry `0x002892C0` across 1,220 cases, runs 360 compositions through the pinned original wrapper at `0x0029EDFC` on both images, and detects a wrong-entry-target control. The wrapper’s disabled path is checked for zero helper entries; the enabled path reaches the helper at its final VMA. The same report says the Calc-only base passed 68 cases. The test caller is the original `0x0029EDFC`; the larger `0x0029F278` cursor body was not executed. Runtime is explicitly `not_run`.

## Promotion boundary

This is sufficient evidence for the helper’s production placement and bounded final-address comparison on the exact Calc-only base. It covers that helper delta with the original `0x0029EDFC` wrapper and documented fixtures; it does not validate every caller domain, invalid or misaligned pointers, MMIO, concurrent access, input timing, or runtime behavior.

The same `.text` tail is allocated by Calc, Draw, and Secondary in the accumulated five-callback H2 patch. The reviewed `0x003FEE64` placement is not merged into that image and would collide with its existing layout. To integrate there, select a separate available executable range or redesign the combined layout, then rerun the final-address differential against the exact resulting image and caller composition. No whole-H2 or runtime claim follows from this review.

## Commands and outcome

- Recomputed all run001 packet input hashes — exit 0, no mismatches.
- `python tools/h2_2892c0_production_integration.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-002892c0-production-review/run001/checks/recheck-run004` — exit 0; fresh production compile and focused integration validation.
- Independently extracted the helper symbol, replayed the IPS, checked the zero cave, decoded the branch, checked sorted record ranges, and compared artifact/source/object/body hashes — exit 0.

**Next action:** The coordinator may accept this bounded helper promotion on the Calc-only base. Keep it separate from the accumulated five-callback image until a non-overlapping combined layout has its own final-address validation. Runtime remains not run.
