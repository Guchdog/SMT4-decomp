# Independent Review: `0x002AEA28` (`camp_func_002aea28`) Profile Selector

## Verdict

**Disposition:** **Accept** `camp_func_002aea28` (`src/engine/leaf_batch24_b.cpp:325-340`, `non_matching`, `56/56` bytes, `3` even ARM `R_ARM_CALL` relocations) for its bounded TBB-hooked domain and both exercised caller slices (`0x99` and `0xDC`).

This review does not claim TBB resource-table lifecycle, transitive service equivalence, or live Azahar audio/runtime behavior.

## 1. Independent Disassembly & Contract Audit (`0x002AEA28`, 56 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x002AEA28..0x002AEA60` and verified all 18 `input_sha256` pins:

- **Dependency order & arguments**:
  1. `Tbb_GetGlobalSubTable(0x0E, 0)` (`bl 0x2c0ec4`) -> `table` (`r6`).
  2. `Tbb_GetPayloadData(table)` (`bl 0x2c0e9c`) -> `payload` (`r5`).
  3. `Tbb_GetRowCount(table)` (`bl 0x2c0e4c`) -> `row_count` (`r0`).
- **Unsigned index bound, 16-byte stride, null & raw return**:
  - `cmp r4, r0; movhs r0, #0; addlo r0, r5, r4, lsl #4` returns `0` when `(u32)profile_id >= row_count` (including `row_count == 0` / null-table count `0`), and `payload + profile_id * 16` (32-bit pointer arithmetic) when `(u32)profile_id < row_count`.
  - `camp_func_002aea28` (`src/engine/leaf_batch24_b.cpp:325-340`) matches the exact dependency order, arguments, unsigned `HS/LO` boundary, 16-byte stride, and raw `r0` return.

## 2. Fresh Offline Rerun, Controls, Interworking & Ledger/README Counts

- `python tools/h2_profile_lookup_experiment.py --out build/agent-work/H2-semantic/h2-profile-lookup-review-002aea28/run-001/checks/fresh` (exit `0`, `report.json` SHA-256 `7880f04886e9fb1ae812238933e6568796518513f9a09e8addcd4b502e0e7c22`):
  - `16/16` direct final-VMA cases (`mismatch_count=0`).
  - `2/2` original `0x002B8B78` caller slices (`title_config_init_0x99` at `0x2f4dec..0x2f4df4`, `nested_callback_0xDC` at `0x286b7c..0x286b84`, `equal=true`, `fault=null`, `sp_aligned=true` at all 14 events per slice).
  - `3/3` mutation controls detected (`wrong_subtable_id`, `wrong_index_stride`, `wrong_equal_boundary`).
  - `56/56` bytes, `3` relocations (`Tbb_GetGlobalSubTable` `0x2c0ec4`, `Tbb_GetPayloadData` `0x2c0e9c`, `Tbb_GetRowCount` `0x2c0e4c`, all `target_bit0_clear=true`), `ips_replay=true`, `changed_outside_slot=false`.
- **Affected-TU & interworking artifacts**: Verified `affected-tus/report.json` (`9fb02469...`: `leaf_batch24_b.cpp`, `leaf_batch32_c.cpp`, `tbb_loader.cpp` all `exit_code: 0`) and `interworking.json` (`9293173a...`: all 3 TBB entries `bit0_clear=true` and caller branches `0x2f4df0`, `0x286b80` target even `0x2b8b78`).
- **Ledger vs. README count audit**:
  - `config/functions.csv` (`52e3b05e...`): `9,470` `matching` (`2,898,900` B) + `1,489` `non_matching` (`239,724` B) + `8` `matching_span` (`484` B) = `10,967` rows (`10,959` functions + `8` spans), `3,139,108` total bytes; row `5338` truthfully marks `0x002aea28` as `non_matching`.
  - `README.md` (`97417c4e...`) lines 106–110 totals `3,139,108` bytes across `10,959` functions + `8` spans (`3,117,224 + 21,884`, `10,881 + 78` from the prior baseline snapshot, with `README` batch-closure refresh pending).

## 3. Limits

- TBB helpers (`0x002C0EC4`, `0x002C0E9C`, `0x002C0E4C`) are deterministic hooks in these runs; full TBB lifecycle, invalid-pointer faults, profile data producer, natural runtime reachability, and audio output remain unverified.
