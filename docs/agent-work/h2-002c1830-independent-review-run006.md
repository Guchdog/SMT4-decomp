# Independent review: logical query dispatcher `0x002C1830` — run006

## Recommendation

The corrected run006 evidence supports proceeding with the bounded semantic promotion/review of `0x002C1830`. The key caller-composition defect identified in earlier runs is addressed: each caller profile starts from the pinned original image, and the patched profile differs only by the `0x002C1830` slot replacement. In this report, LR-derived wrapper-entry traces and static call-PC hooks both show all six expected call PCs and seven PC/argument combinations, including both `(4,0)` and `(3,0)` at the shared `0x001EAC50` site. This is bounded harness evidence, not natural runtime or whole-game equivalence.

## Frozen inputs and staged image

I recomputed all 25 SHA-256 entries in the run006 packet; all match. Important identities:

- Original image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Candidate source: `a911ca84be625dbc8327b5438e6a6fd81c70831ecf4d66f86343ebe577731a56`
- Candidate object: `0c351edcbb870c45cfaa52d4dc2652e46d1c2a73503a297a8b8d29704e59e411`
- Final object from run005: `0d4541313b1643db5181d2b754f25de358704c66f2649ee16322e228d6927458`
- Differential report: `0bb9c22e9743cb6ef96107ce7480e40c8bf9413673c5c72d5e69aec8cde3ac49`
- Base image: `3afbd263381b66d18f8ac680529fb27e4291899b70cb74401c8b812552df8774`
- Staged image / IPS / manifest: `65d8014821287f2a66a417459dcc105e34c7c6c4af351e7d577051d28616f6ef` / `ee3e9bf5c9561849a63551ea427cd1816d7eacc546e96eb9a155c6414a16c994` / `8fb8f8dd86532df23aae40e19e35385f7f7c3a6d17025ffa798eaba8adc14d2b`

The body is 264 bytes within the 504-byte slot at `0x002C1830`; the report body hash is `1eb7252e4692112f989010f55a0a3e8872794685215c3c649e5fe8ebf0c4088a`. There are six `R_ARM_CALL` relocations at offsets 44, 64, 84, 176, 184, and 192. Reapplying them at final VMA resolves to the intended even ARM helper addresses: `0x002BFFBC`, `0x002B902C`, and `0x002C17D4`, twice each. The manifest reports 410 changed bytes, all inside the declared slot, and successful IPS roundtrip.

## Contract and direct differential

The 114 direct cases cover modes 0, 1, 2 (34 each) and invalid modes 3 and `0xFFFFFFFF` (six each). Valid mode cases include IDs 0–12 and full-width values `0x80000000` and `0xFFFFFFFF`. They compare primary/secondary/fallback call order, short-circuiting, raw 32-bit return propagation, ABI projections and preserved state. The exercised contract is: valid modes dispatch to their respective query/fallback helper families; a nonzero query result is returned unchanged; IDs 3–6 perform the `id + 9` secondary lookup only after a zero primary result; remaining zero results use the observed fallback mapping; other IDs return zero; invalid modes return zero without helper calls. Three controls are detected: secondary ID `+9` changed to `+10`, ID-7 fallback result `6` changed to `5`, and inverted nonzero-return polarity.

The direct callees are deterministic hooks. The differential establishes dispatcher behavior and propagation for the supplied values, not the callee internals or natural game distributions. The ledger row is `non_matching`, appropriately reflecting different bytes.

## Corrected caller composition

The run006 runner explicitly constructs the patched caller image from the pinned original `image` and applies only the wrapper patch to `final_image`. It compares original Calc/original helpers against original Calc/patched wrapper and also includes original wrapper and patched wrapper profiles with typed mode-0/mode-1 helpers. This avoids the earlier cumulative-base issue where Calc had already been converted.

Across 43 scenarios, both `caller_callsite_pairs` (LR-derived wrapper entry, normalized as `LR-4`) and `titleconfig_query_site_pairs` (static PC hooks) report the same seven combinations:

- `0x001EAABC`: `(9,1)`
- `0x001EABDC`: `(4,0)`
- `0x001EAC20`: `(3,0)`
- `0x001EAC50`: `(4,0)` and `(3,0)`
- `0x001EAE64`: `(0,1)`
- `0x001EAF14`: `(1,1)`

The two shared-site alternatives are supported by actual scenario traces: decrement records `(4,0)` at `0x001EAC50`; increment records `(3,0)` there. The report also shows expected preceding query calls in each path. All caller rows report equality for original-helper and typed-helper compositions.

## Limits and next action

This review is static over the frozen report and inputs; I did not compile or execute the harness. Scenario state is scripted and counters are seeded; unrelated services and query helpers are controlled by the harness. The evidence does not cover physical-input production, event timing/scheduling, every natural game state, helper implementation semantics, emulator runtime, or whole-game equivalence. Runtime remains `not_run`. Proceed with the bounded review/integration step and retain these limits in the semantic record; do not describe this as runtime equivalence.
