# `0x00286928` integration & staged-patch review

**Verdict: CONDITIONAL / BLOCKED on stale artifact provenance vs HEAD `src/engine/leaf_batch45_a.cpp`. The `812/820`-byte staged image, `manifest.json`, `production-offline-validation.json`, and `run001/offline-report.json` pass all structural/ABI/slot/IPS checks for `source_sha256` `962c018c...`, but HEAD `leaf_batch45_a.cpp` (`df697fe2...`) contains the newer `q=0` pointer-reload revision (`808/820` bytes).**

## 1. Frozen pins & production identity

- Read-only provenance/hash/source audit (`compiler_slots: 0`); no canonical build, runner rerun, or emulator was run.
- Recomputed all `23/23` `input_sha256` entries in `build/agent-work/H2-semantic/h2-helper-00286928-integration-review/run-001/task.json`: `23/23` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `config/functions.csv` truthfully classifies `0x00286928` (`820` bytes, `engine`, `engine_func_00286928`, `src/engine/leaf_batch45_a.cpp`) as `non_matching`.
- Both raw inline-assembly consumers (`src/engine/leaf_batch18_b.cpp:18` and `src/engine/leaf_batch24_c.cpp:50`) declare the matching six-word ABI `extern "C" uint32_t engine_func_00286928(uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);`.

## 2. Staged image, IPS, differential, and 204-TU build audit

- `build/h2-86928-integration/staged-image/manifest.json` (`ad07d05d...`):
  - `compiled_body_bytes: 812`, `slot_bytes: 820`, `tail_policy: "two ARM NOPs (8 bytes)"`.
  - `22` `R_ARM_CALL` relocations to even ARM addresses (`state: "ARM"`, offsets `184..788`).
  - `original_image_sha256: 1f98884f...`, `patched_image_sha256: 32c7469f...`, `ips_sha256: ace8db84...`, `ips_roundtrip: true`, `only_function_slot_changed: true`.
- `build/h2-86928-integration/staged-validation/production-offline-validation.json` (`222d4c3f...`): `296` direct cases and `4` `0x00221168` callback cases passed (`result: "passed"`), with all 17 direct callees and callback getters stubbed and `0x001A07CC` / emulator runtime excluded.
- `build/agent-work/H2-semantic/h2-helper-00286928-convert/run001/offline-report.json` (`02ce909c...`): `300` comparisons + `6/6` controls recorded for the `812`-byte snapshot.
- `build/h2-86928-integration/full-build` contains `204` `.o` files.

## 3. Concrete provenance blocker & recommendation

- **Blocker:** `manifest.json` (`ad07d05d...`), `production-offline-validation.json` (`222d4c3f...`), and `docs/agent-work/h2-86928-implementation.md` pin `source_sha256 = 962c018c8c02971ed5bf77cca52685dcda4d7cc2634868e8e7640009ddb17dff` (`812` bytes), whereas HEAD `src/engine/leaf_batch45_a.cpp` is `df697fe2126e7920734a36887802697c104a5add266ba9c3b20d9292d6cf1d5d` (containing the `q=0` pointer-reload fix at lines `12808-12813`, which `docs/function-records/0x00286928.md` describes as `808/820` bytes with 3 NOPs).
- **Recommendation:** Do **not** promote or commit/push from the stale `812`-byte `manifest.json` (`ad07d05d...`). First refresh/verify `tools/h2_86928_experiment.py`, `tools/h2_86928_staged_image_patch.py`, `tools/h2_86928_staged_validation.py`, and `build_check.py` against HEAD `leaf_batch45_a.cpp` (`df697fe2...`), then proceed to autonomous runtime verification and commit/push.
