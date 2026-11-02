# Independent review — `0x0027FBC8` calibrated axis reader

## Recommendation

The production conversion is supported for the directly exercised domain: valid mapped global/state/calibration/sample memory and null or valid output pointers, for the selector, mode, flags, calibration, threshold, and sample cases in the reports. My fresh direct audit and fresh final-VMA audit found no counterexample. The reports support keeping the function classified `non_matching` with its semantic evidence; they do not support closing the downstream no-write consumer domain or H2 lifecycle.

## Frozen-input audit

I recomputed every `input_sha256` pin in the assigned packet; all 17 declared entries match. In particular, the original image is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; production TU `src/engine/leaf_batch41_a.cpp` is `4bd04b9071f2b529c2064f5d8205a1c7880f230e8db07959e2a20692d0bf59e5`; experimental candidate is `108b45003ec4908630514b615be7ebe6911fddb83c7448e4a8dacc403dd85aca`. The ledger row is `non_matching`, consistent with the differing production body.

The pinned prior direct, caller, and staged reports and artifacts also hash to the packet values. I did not modify any input, production source, tool, ledger, or board.

## Independent fresh runs

1. `python tools/h4_axis_reader_experiment.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-0027fbc8-independent-review/run001/checks/direct-independent --audit-contract --seed 20261102` — exit 0. The 146-case contract audit reports `passed`, zero differences, no first counterexample, and detects its same-input mode-bound mutation. The two invalid output-pointer probes fault identically and show identical writes; they are explicitly out-of-contract fault observations.
2. `python tools/h2_27fbc8_production_validation.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-0027fbc8-independent-review/run001/checks/final-vma-independent --seed 20261106` — exit 0. It compiles experimental and production objects independently, stages and executes the actual production body at its final VMA, and reports 146 cases, zero differences, a 300-byte body in the 320-byte slot, and exact slot-only IPS replay. Its final report SHA-256 is `7a7c97117a0c3aa5bfe413b91506fd0ae088c3603643242d7fc782f504ca93ee`; staged image SHA-256 is `64175ee8940de6faa132185ba2684af241fe9fa6bfe9c6857287b764c999515c`; slot IPS SHA-256 is `486c8191f83ba2212a66874689c66e43b4b0191fa118cbc6d7006b75c4ade1e8`.

The final-VMA report confirms the production and experimental bodies are byte-identical (body SHA-256 `5a8160055c296e73c46e94fe8a5aaf439e38c8e91a66e5855c9f8c04922dda6a`). The two final-VMA `R_ARM_CALL` instructions are at `0x0027FC80` and `0x0027FC8C`, both resolve to even ARM entry `0x0019FE4C`. The original ARM BL at `0x001FA948` resolves to even ARM entry `0x0027FBC8`. The 320-byte patch changes bytes only within this slot and the IPS replays exactly.

## Contract and control-flow review

The production C++ has ABI `(float* out_x, float* out_y, u32 mode)` and returns signed status in `r0`. It loads the state pointer from `0x004650A0`, then loads calibration and selector before rejecting mode. Thus valid mapped state/calibration are preconditions even for rejected modes. Selector 0 uses axis 0, selector 1 uses axis 1, all other byte values use axis 2. The selected signed-halfword span is `hi - lo`; the full possible signed-halfword difference fits a 32-bit signed intermediate.

It rejects unsigned `mode >= 2`, and then rejects `mode` above state `+4`. State flag bit 0 chooses fixed alternate sample `0x004E3C48`; otherwise it selects `0x004E3C28 + mode*16`. Signed X/Y samples at `+0x0C/+0x0E` are divided by the span. A nonzero threshold invokes the original `0x0019FE4C` deadzone helper in X-then-Y order; if both results compare equal to zero, it returns 0 without output writes. Threshold zero skips that path. On success it stores X then Y, independently skipping a null output pointer, and returns 1.

The fresh direct case set covers mode boundaries including `0xFFFFFFFF`, state maximum bounds, selector values 0/1/2/3/255, alternate-source flags, all null-output combinations, equal/swapped pointers, selected aliases into state/calibration/sample memory, threshold boundaries including signed zero, NaN and infinities, zero/reversed spans, extreme samples, and 100 seeded cases. It compares return, helper calls, output targets, selected state/calibration/sample/output memory, ordered non-stack writes, callee-saved `r4-r11`/`d8-d15`, and FPSCR. The mode-bound mutation is detected. The 2 unmapped-pointer probes only compare fault class and writes; they are not valid caller inputs or proof of fault equivalence in general.

The pinned caller report exercises the actual camera call slice from `0x001FA948` through `0x001FAA84` using a synthetic stack/view fixture: six neutral/positive/negative/half-scale/deadzone cases match, and its mutation at candidate offset `0x30` is detected. This is bounded call-site composition, not a full camera task or physical input/rendering test. Its stack observation is limited to the two local float slots. The direct harness does not compare the entire stack scratch area, SP, condition flags, or every caller-saved register.

## Limits and next action

The function intentionally has a no-write return when the nonzero deadzone suppresses both components. The downstream `0x00254CA8` code can read its local output floats after that return; this assignment does not establish initialization, reachability, or safe behavior for that consumer path. Exceptional floating-point behavior outside the listed fixtures, arbitrary aliasing with globals/device memory, concurrent mutation, MMIO, and every caller state are also not established. Runtime and H2 lifecycle validation were not run.

Proceed with this bounded helper conversion and retain the exact non-matching ledger classification. Keep the no-write consumer unresolved; the next acceptance step is a caller-domain audit at `0x00254CA8` that establishes initialized outputs or bounds the no-write case, followed by the planned scoped integrated runtime scenario.

## Run002 refresh — 2026-11-02

The refreshed packet pins all 17 declared inputs; each recomputed hash matches. I inspected the final conversion note and function record: both now record the independent review result and continue to state that the downstream `0x00254CA8` no-write read and H2 remain unresolved. The production source and ledger row are unchanged; the row remains accurately `non_matching`.

I reran the direct contract audit with seed `20261108` and final-VMA validation with seed `20261109`, writing to run002-owned outputs. Both fresh reports cover 146 cases, report zero differences and no counterexample; the direct run detects the mode-bound mutation. Final-VMA validation confirms the production/experimental body identity, 300-byte body within the 320-byte slot, helper calls at `0x0027FC80` and `0x0027FC8C` to even ARM target `0x0019FE4C`, the original caller BL at `0x001FA948` to even ARM entry `0x0027FBC8`, and exact slot-only IPS replay.

No finding changes the prior recommendation: the bounded helper domain remains supported. Null outputs are valid; the two invalid-pointer probes are fault observations only. The no-write return with both post-deadzone outputs zero still leaves the consumer's local-float read unresolved. Caller evidence remains the pinned six-case synthetic camera slice, not a full camera task. No runtime or H2 lifecycle claim is added.

Run002 report pins: direct report `a27e99baa0f0b30a0ce29e4376e4ae6c8c4cf366b5f237c325dda536af7c4e6a`; final-VMA report `91a817faff8880d2b3985db815c2e287e4b61d90c6c3facca84f2ac102b88b76`; staged image `64175ee8940de6faa132185ba2684af241fe9fa6bfe9c6857287b764c999515c`; slot IPS `486c8191f83ba2212a66874689c66e43b4b0191fa118cbc6d7006b75c4ade1e8`.
