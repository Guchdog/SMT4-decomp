# H1 TBB source promotion — 2026-10-25

## Result

Integrated readable C++ for `Tbb_GetSubTable` (`0x002AC2F4`) and `Tbb_GetPayloadData` (`0x002C0E9C`) in `src/ui/tbb_loader.cpp`. Both ledger rows are `non_matching`, because their source-generated ARM bytes differ from the pinned original. The independent production-source review approved this bounded promotion; it did not approve an IPS or a live-game equivalence claim.

The subtable accessor now uses an explicit ARM32 address calculation and reads the trailing offset word byte-wise. `TbcrHeader` describes only its fixed three-word prefix, avoiding indexing beyond a one-element C++ trailing-array member. The payload accessor validates TBL1 magic and returns `table + 0x10` with 32-bit address arithmetic. `Tbb_GetRowCount` remains original assembly and is outside this promotion.

## Evidence

- Reference `code.bin` SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Production TU SHA-256: `90d17cb7206c47d5fa5ddfae533a2d946f58815c14b92673f0cde3f838219819`; header: `1eabd1831dca8f8949e53f24ef34be569b8eee2ec768e39949f32fc45f061c5f`.
- Compiled production object SHA-256: `e95866fb2b03fdb83c367ddc260cad0cc1599f26432f633e7db610509032649c`; canonical object at `build/obj/armv6k/ui/tbb_loader.o` has the same hash.
- The production-symbol integration runner compiled the actual `src/ui/tbb_loader.cpp` symbols. Seed 7 and seed 20261024 each passed 70 payload fixtures, 71 subtable fixtures, the real asset’s two tables and boundary index, both targeted negative controls, and title-caller selections 0–3 through `0x001E9AC8`.
- The original getter caller plus real `TitleTable.tbb` is a synthetic ARM caller scenario. It computes selected record/help-field addresses; it does not consume or render help text.
- Focused runner setup/symbol tests: 9 passed. Scoped regression (`test_tbb_semantic_experiment`, `test_asm_diff`, `test_progress`): 35 passed. This includes the audit of remaining `matching` rows and raw spans.
- Canonical ARMv6K translation-unit build: 190/190 succeeded with eight workers; 5 compiled, 185 validated from cache. The generated progress files now report 99.9958% reference byte coverage and two semantic functions in compiled-size coverage.

Full command exits, report hashes and per-report case summaries are in [`closure-evidence.json`](../../build/agent-work/H1-semantic/h1-tbb-promotion/sleep-20261025-tbb-closure/closure-evidence.json). Integration reports:

- [Seed 7](../../build/agent-work/H1-semantic/h1-tbb-promotion/sleep-20261025-tbb/checks/integrated-seed-7b/report.json), SHA-256 `86091087e9533dced582336506892f28bf4e0435f60847346edff86fbbab83c2`.
- [Seed 20261024](../../build/agent-work/H1-semantic/h1-tbb-promotion/sleep-20261025-tbb/checks/integrated-seed-20261024/report.json), SHA-256 `aa2b39b2e92df488594835f1ed42d68835e7a1a220efd39d2e253023c38d6811`.
- Independent review: [`h1-tbb-integration-review.md`](h1-tbb-integration-review.md).

The report-wide `passed` flag also covers a separate RowCount experiment. Promotion here rests on the payload, subtable and caller evidence arrays and their negative controls; RowCount remains excluded.

## Limits and next H1 work

The APIs do not receive allocation lengths. They cannot validate malformed offsets, address wraparound or unreadable memory, matching the original input contract. No IPS or patched executable was produced or applied. The emulator capture has not observed the actual track source type and callback binding; the alpha helper also has only synthetic isolated/caller evidence. H1 main-menu slice integration remains queued until the runtime binding evidence is resolved.

**Next:** resume the exclusive Azahar runtime capture, then integrate a small main-menu transition slice only after the observed callback binding and reviewed prerequisites are available.

Structured handoff: [`handoff.json`](../../build/agent-work/H1-semantic/h1-tbb-promotion/sleep-20261025-tbb-closure/handoff.json).
