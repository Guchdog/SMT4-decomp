# `0x002B787C` (`AsdText_GetLineCount`) — independent read-only review

**Verdict: APPROVED for bounded offline conversion (`engine_func_002b787c`, `src/engine/leaf_batch42_c.cpp:468-508`, `176/176` bytes, `non_matching`). Recommend proceeding to autonomous runtime verification review and commit/push, while preserving unsupported input and natural-reachability limits.**

## 1. Frozen pins, control-code branches, and signed bound

- Read-only audit (`compiler_slots: 0`); no compiler, runner rerun, canonical build, or emulator was run.
- Recomputed all `19/19` `input_sha256` entries in `build/agent-work/H2-semantic/h2-asdtext-line-count-independent-review/run-001/task.json`: `19/19` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `candidate_002b787c` (`experiments/semantic_equivalence/h2_2b787c_candidate.cpp:9-50`) and `engine_func_002b787c` (`src/engine/leaf_batch42_c.cpp:468-508`) match `docs/agent-work/h2-2b787c-contract.md`:
  - `*(handle + 0x14) == 0` returns `0`.
  - `0xFFFF` terminator returns `count`.
  - `engine_func_002ae6b0(code) != 0` constrains `code` to `0xF801..0xF88F`, so `static_cast<uint8_t>(code)` uniquely dispatches `1` (`0xF801`, `count += 1`), `2` (`0xF802`, return `count`), `0x1A` (`0xF81A`, `index += 1`, `count = *(uint16_t*)(table + (index << 5))`), and `else` (`index += func_002ae664(code)`).
  - Signed loop bound uses unsigned `start + 0x3e7` cast to `int32_t` (`static_cast<int32_t>(index) >= signed_limit`), avoiding C++ signed-overflow UB while matching ARM `add r0, r0, #0x3e7; cmp r0, r4; bgt`.

## 2. Relocations, exact-slot patch, ledger, and report verification

- `build/h2-2b787c-integration/staged-image/manifest.json` (`4047dfc8...`): `176/176` bytes (`compiled_body_sha256`: `1f2cd6d6f0487f9c6cb12ce3f2363a19513c13969ac5b96df4d0e6b6e0cc08fe`), `2` `R_ARM_CALL` relocations at offsets `68` (`engine_func_002ae6b0` -> `0x002AE6B0`, `ARM`) and `112` (`func_002ae664` -> `0x002AE664`, `ARM`), `ips_records: 1`, `ips_roundtrip: true`, `only_function_slot_changed: true` (`ips_sha256`: `a501c4b078961d69ac720f252331f29380d4186dfebe1ec333902891e57896c2`, `patched_image_sha256`: `a915d0baee331366636fd9e25d55bfafa3554351f15d242fce3f52f9675d1dec`).
- `config/functions.csv` truthfully marks `0x002b787c` as `non_matching`.
- `build/agent-work/H2-semantic/h2-asdtext-line-count-convert/run003/offline-report.json` (`3e56cf59...`): `515/515` direct cases, `2` `0x00286928` caller compositions (`selectors [11, 19]`), `6/6` negative controls (`sentinel`, `count_control`, `stop_control`, `payload_control`, `mapped_delta`, `signed_bound`), original `0x002AE6B0`/`0x002AE664` executed from pinned image.
- `build/h2-2b787c-integration/staged-validation/production-offline-validation.json` (`5bd5fb16...`): `515/515` direct cases and both `0x00286928` selectors (`11`, `19`, `entry_hit: true`, `stored_line_count: 2`) pass at final address `0x002B787C` (`final_address_execution: true`).
- `build/h2-2b787c-integration/full-build` contains `204` `.o` files, corroborating the 204-TU compile claim.

## 3. Untested domain limits & recommendation

- Untested boundary/negative domains (null/unreadable `handle`, sentinelless tables, signed `start + 0x3e7` wraparound, and unexecuted callers `ui_func_00116954` and `StatusDown_UpdateHelpMessage`) do **not** invalidate this bounded approval provided they remain explicitly documented.
- **Recommendation:** Proceed to autonomous runtime comparison review (note `docs/agent-work/h2-2b787c-implementation.md` records `runtime-probe-001` passing 19/19 H2 checkpoints via direct GDB invocation, while natural selector-6 runtime reachability remains unestablished) and commit/push this bounded conversion once runtime review closes.
