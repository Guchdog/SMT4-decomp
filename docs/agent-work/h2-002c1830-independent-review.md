# Independent review: logical query dispatcher `0x002C1830`

## Recommendation

The frozen dispatcher reconstruction is supported for the controlled helper-return matrix and the exercised `TitleConfig_Calc` scenarios. The 264-byte body fits the 504-byte span, and its six `R_ARM_CALL` relocations all resolve to the original even ARM helpers. The cumulative IPS round-trips and changes only this function slot. The ledger correctly marks the differing replacement `non_matching`.

One caller-evidence limit remains: the 43 scenario traces record logical `(id, mode)` pairs, not LR/return PCs. They contain both second-query alternatives as repeated pairs in the expected decrement and increment paths, and the pinned static map identifies the shared site at `0x001EAC50`; however, no report field directly records the PC for each call. I recommend adding LR-based callsite tracing before promoting a literal claim that all six PCs/seven site-and-argument combinations were dynamically observed. This does not contradict the dispatcher differential or caller comparisons.

## Frozen identities, body and relocations

All 24 task input hashes match. Key hashes: original image `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; candidate source `experiments/semantic_equivalence/h2_2c1830_candidate.cpp` `a911ca84be625dbc8327b5438e6a6fd81c70831ecf4d66f86343ebe577731a56`; report `4c92bd7162415de72eaf39c4399e1fd5837e4ecff464300a74873cc71b37c1a4`; final object `0d4541313b1643db5181d2b754f25de358704c66f2649ee16322e228d6927458`. The report’s separate `candidate.o` hash is `0c351edcbb870c45cfaa52d4dc2652e46d1c2a73503a297a8b8d29704e59e411`; extracting either object yields the same 264-byte body hash `1eb7252e4692112f989010f55a0a3e8872794685215c3c649e5fe8ebf0c4088a` and six call relocations.

I independently applied each final-VA `R_ARM_CALL` relocation from `0x002C1830`. All are aligned ARM `BL` calls and decode to the intended helper address:

| Body offset | Helper | Resolved target |
| --- | --- | --- |
| `0x2C`, `0xB0` | `ui_func_002BFFBC` | `0x002BFFBC` |
| `0x40`, `0xB8` | `ui_func_002B902C` | `0x002B902C` |
| `0x54`, `0xC0` | `ui_func_002C17D4` | `0x002C17D4` |

Each helper address is even, and no other candidate relocation is present. The candidate uses the full 32-bit ID and mode. Modes 0/1/2 dispatch to those helpers; other modes return zero without helper or fallback calls. A nonzero helper word is returned unchanged. IDs 3–6 make a secondary query with ID+9 only after a zero primary result. Remaining zero results use fallback map `0→1`, `1→2`, `7→6`, `8→5`, `9→3`, `10→4`, tail-calling the mode-specific original fallback at `0x00125C10`, `0x00124FA8`, or `0x00124F0C`. Other IDs return zero. The two signed helper declarations are converted to `u32` without normalizing the returned bits; the third helper returns `u32`.

## Direct differential and controls

The pinned direct matrix contains 114 cases: 34 each for modes 0, 1 and 2, plus six each for invalid modes 3 and `0xFFFFFFFF`. Valid modes cover IDs 0–12 and high-bit IDs `0x80000000` / `0xFFFFFFFF`. The plans test high-bit nonzero primary returns, zero/nonzero secondary results for IDs 3–6, fallback propagation, and no-fallback IDs. The runner verifies call order/short-circuit traces, raw return, stack/callee-saved state, and stack-canary/external-write footprint across original, temporary, final-VMA and staged profiles. Invalid-mode cases require zero return and no calls.

Three compiled controls are detected: secondary ID `+9` changed to `+10`, ID-7 fallback `6` changed to `5`, and nonzero-return polarity inversion. Direct calls to the three query helpers and three fallbacks are deterministic hooks, so these cases validate dispatcher selection, order and value propagation rather than the internals or natural output distributions of those callees.

## TitleConfig caller composition

The 43 scripted runs execute the pinned `TitleConfig_Calc` on the cumulative base and replacement image, with additional runs using typed mode-0/mode-1 query helper profiles. The static call map identifies six state-1 PCs and seven callsite/argument combinations: `(9,1)` at `0x001EAABC`; `(4,0)` at `0x001EABDC`; `(3,0)` at `0x001EAC20`; `(4,0)` or `(3,0)` at shared site `0x001EAC50`; `(0,1)` at `0x001EAE64`; and `(1,1)` at `0x001EAF14`. The report’s five unique argument pairs include all alternatives. In particular, the decrement scenario logs `[(4,0),(4,0)]`, and the increment scenario logs `[(4,0),(3,0),(3,0)]`, showing the two second-query argument alternatives in their expected path order.

The caller harness invokes the actual Calc state machine and compares full caller state, return, trace and ABI across original-wrapper, replacement-wrapper, typed-query, and combined typed profiles. It seeds logical counters directly and keeps unrelated services deterministic. The conversion runner also compiles the mode-0/mode-1 caller profiles and checks their bodies equal their existing production objects; I independently confirmed the current injected object bodies equal the pinned production objects. These helper-profile artifacts are not individually hashed into this dispatcher report, and callsite LR values are not emitted; the caller evidence is therefore bounded and does not prove the physical-input producer, event timing, scheduler, complete natural TitleConfig cycle, or all runtime helper effects.

## Staging and limits

The prior cumulative base SHA-256 is `3afbd263381b66d18f8ac680529fb27e4291899b70cb74401c8b812552df8774`. Staged image SHA-256 is `65d8014821287f2a66a417459dcc105e34c7c6c4af351e7d577051d28616f6ef`; IPS SHA-256 is `ee3e9bf5c9561849a63551ea427cd1816d7eacc546e96eb9a155c6414a16c994`. Reapplying the IPS reproduced the staged image; all 410 changed bytes lie inside the 504-byte slot at `0x002C1830`. Runtime is `not_run`. I did not compile, execute the differential, or launch an emulator; this review recomputed provenance/relocations and statically inspected the frozen harness and report.
