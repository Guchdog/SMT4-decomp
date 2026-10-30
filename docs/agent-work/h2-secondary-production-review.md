# Independent review: H2 `TitleConfig_Secondary` production integration

## Decision

The production source is a credible reconstruction of the isolated callback orchestration under the declared helper-entry models. The production object and differential report are hash-consistent with the source and pinned reference, and the extracted symbol is 292 bytes with no ELF relocations. I do **not** recommend placement or promotion yet. Under the latest Calc+Draw split map, the raw byte arithmetic can accommodate it, but leaves only 8 bytes and has not been exercised in a combined final-address image. The production-symbol differential has no production-specific negative control, and the artifact does not carry enough detail to audit all of its helper/ABI comparisons independently.

## Provenance and symbol identity

All declared `run-001/task.json` input hashes matched the current checkout. The relevant hashes are:

- Production TU `src/engine/leaf_batch32_c.cpp`: `3ca4676613634ae91fe980e5e6e3c79fa74aff355e0facc50149749ba10b9c37`.
- Production object `.../run-001/checks/production-tu/engine/leaf_batch32_c.o`: `e04b6dcb9ae560efa2e39202b04763263b03f1f61455efe5b54756ffda81d53e`.
- Extracted `engine_func_002caef0`: 292 bytes, zero ELF relocations, symbol SHA-256 `e2e714f635eee7874699fde891189dfed1298d225a21423554077152e66d4913`.
- Production-symbol differential JSON: `36703fdd9dac8f228ea178e3fcd85273aadc4b60df7c0a481e094cdc38d9ce99`.
- Pinned original: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The integration document agrees with those hashes and reports a successful one-job production-TU build. The reviewed production-differential report records the same source/object/symbol/reference identities, 17/17 cases, seed `20261025`, no first counterexample, and no ELF relocations. I found no `handoff.json` in the production-integration run directory; provenance here is therefore checked against the task packet and the checked-in integration report, rather than a prior structured handoff.

## Source, helper models, and 17-case matrix

The production wrapper preserves the contract's direct orchestration: global work lookup without a null guard, `work+4` flag store, two independent signed-halfword loops with volatile rereads and reset iteration count, conditional cleanup of `+0x154`, `+0x14c`, then `+0x150`, task-registration predicate and state-zero call, and a final reload/release/clear of the global work pointer. Its calls remain at the five documented original helper addresses. The C entry is `void` and does not consume the incoming callback argument; this agrees with the original body's observed use of the global rather than incoming `r0`, and does not assert a meaningful return value.

The 17 cases cover both counters zero; each independently at `-1`, `1`, and `4`; three nullable slots independently null; task predicate false/true; manager halfword `9/10/11/12` with one first-loop call; and both counters positive together (`2/3`). This is useful branch coverage for ordinary stable synthetic state, but it omits signed-halfword extrema, simultaneous null-slot combinations, counter mutation/reentry, invalid global/work pointers, and per-case trace detail for a threshold-crossing sequence. The `both-loops-distinct` case apparently combines multiple calls at manager value 12, but the production report does not serialize its input values or traces, so that interaction is not independently inspectable from the artifact.

The declared `0x002B9008` model captures its direct manager-halfword decrement only when signed value is above 10; the other cleanup/release/task helpers are trace-only. Thus the result supports the caller's call order, guards, direct work/global writes, and the modeled manager effect. It does not validate nested script cleanup, allocator effects, task-state propagation, scheduler timing, callback count, or object lifetime. The earlier candidate review detected wrong-count and wrong-release-order mutants, but those were candidate-level controls. No production-symbol mutant/negative control is present in the production report, so the production extraction/injection path lacks its own sensitivity check.

The prior candidate harness compares callee-saved `r4-r11`, SP, `d8-d15`, the caller-owned stack, work/global memory, manager state, and normalized consumed arguments. The production report is a compact per-case summary and does not embed those comparison details or its own exact runner argv. The integration narrative says it reused the same helper models, but the packet contains no structured integration handoff. I therefore treat the 17-pass result as bounded supporting evidence, not an independently reproducible ABI proof. Preserve a production-specific wrong-count or wrong-order control and publish the exact production runner command/artifact details before relying on it for promotion.

## Cave assessment and recommendation

The documented Calc+Draw split map reserves Calc at `[0x003FE624,0x003FEE54)` (2,096 bytes), then uses 128 bytes at the remaining tail for the Draw cache helper, `%s\0`, and four-byte rounding. That consumes `[0x003FEE54,0x003FEED4)`, leaving 300 bytes. A 4-byte-aligned 292-byte Secondary body beginning at `0x003FEED4` ends at `0x003FEFF8`, leaving 8 bytes in the `[0x003FE624,0x003FF000)` cave. The original Secondary entry at `0x002CAEF0` can in principle be replaced by a direct ARM branch to that body; the entry branch occupies the original function span, not the cave. This arithmetic is feasible on paper.

That does not establish a supported placement. Eight bytes is the entire remaining slack for any overlooked alignment, veneer, literal, or patch record. The zero-relocation object extraction does not prove that every position-dependent instruction is valid after moving the body; relocation/branch semantics must be checked at the assigned VMA. There is no combined placement manifest/builder output, exact disjoint-range audit, final-address Secondary differential, or same-image Calc+Draw+Secondary regression. Existing Calc-only patching cannot simply be applied a second time to the populated cave. Keep Secondary at its original bytes until an owner demonstrates the complete merged map and exact IPS/image identity. If the final builder needs any extra cave bytes, this 292-byte placement no longer fits without changing the layout.

## Recommendation and next action

Keep the source as a reviewed experimental reconstruction, not a promoted production replacement. First add a placement-aware combined builder and manifest that verifies the Draw helper/string range and Secondary body/entry branch, checks all relocations and branch reach, rejects overlaps, and applies one IPS to the pinned original. Run the production-extracted Secondary at its proposed final VMA with the 17 positive cases plus a production negative control, then rerun Calc and Draw against that same merged image. Separately establish the actual callback scheduler/lifetime contract before making runtime cleanup or persistence claims. Do not change the ledger based on this isolated evidence.

