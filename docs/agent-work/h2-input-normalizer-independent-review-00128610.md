# `0x00128610` (`func_00128610`) — independent review

**Verdict: APPROVED for bounded promotion (`non_matching`) within the observed selector (`0, 1, 2, >=3`), disjoint ordinary-RAM, and original-normalizer-callee domain.**

## 1. Frozen pins, source, & ABI audit

- Recomputed all `14/14` `input_sha256` entries in `build/agent-work/H2-semantic/h2-input-normalizer-review-00128610/run-001/task.json`: `14/14` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `func_00128610` (`src/engine/leaf_batch29_a.cpp:3041-3061`) matches `docs/agent-work/h2-input-normalizer-contract-00128610.md`:
  - Reads `u8` selector at `calibration+0x0C`, passes `output_x`, `output_y`, `sample_x`, `sample_y`, and signed `s16` calibration pairs (`[0],[3]` -> `0x0013B9FC`; `[1],[4]` -> `0x0013B8F8`; `[2],[5]` -> `0x0013BAE0`), and returns `calibration` in `r0` on `default` (`selector >= 3`).
  - No raw-return, ABI, stack-argument, or actual-callee counterexamples found.

## 2. Fresh offline differential, controls, relocations, IPS, & consumer compile

1. **Fresh differential (`python tools/h2_input_normalizer_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-review-00128610/run-001/checks/fresh-diff`, exit 0):**
   - Report: `build/agent-work/H2-semantic/h2-input-normalizer-review-00128610/run-001/checks/fresh-diff/report.json` (SHA-256 `b143ae85010476e1567d39372945072aba4630959ab4895b29f5bd3467811b96`).
   - `254/254` direct cases (`direct_mismatches: 0`, `call_contract_mismatches: 0`) executing all three original normalizers as ARM code.
   - `12/12` caller compositions through original `0x001078D8 -> 0x0011C5EC` (`caller_mismatches: 0`, `0x0011C668` targeting even ARM `0x00128610`).
   - `4/4` negative controls detected: `selector_zero_wrong_callee`, `calibration_sign_extension`, `reversed_output_pointers`, `dropped_fifth_input_argument`.
   - Body: `144/148` bytes; `3` even ARM `R_ARM_CALL` relocations (`0x0013B9FC` at `+72`, `0x0013B8F8` at `+104`, `0x0013BAE0` at `+136`, all `entry_bit0: 0`); `ips_replay: true`.
2. **Affected consumer TU compile (`python tools/build_check.py --tu src/engine/leaf_batch30_a.cpp --out-dir build/agent-work/H2-semantic/h2-input-normalizer-review-00128610/run-001/consumer -j 1`, exit 0):**
   - `leaf_batch30_a.o` SHA-256 `e39b538b01ba53ed49cc5cdd231862d4d25d64a2e255092483b0bd7776a2bf33`.

## 3. Preserved limits

- Valid disjoint ordinary RAM, controlled `0x0012A758` ring seam, and original normalizer callees `0x0013B9FC`, `0x0013B8F8`, `0x0013BAE0`; physical input provenance, freshness, aliasing, malformed pointers, MMIO/device effects, and live Azahar runtime behavior remain unverified.
