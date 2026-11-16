# `0x002B8794` (`camp_func_002b8794`) — independent review

**Verdict: APPROVED for bounded `non_matching` classification (`272/304` bytes, `0` relocations) within the tested ordinary-RAM manager/registry and `mode=0` H2 caller-slice domain.**

## 1. Frozen pins, ARM disassembly, & H2 caller trace

- Recomputed all `18/18` `input_sha256` entries in `build/agent-work/H2-semantic/h2-profile-slot-registry-review-002b8794/run-001/task.json`: `18/18` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled `0x002B8794..0x002B88C3` (304 bytes) from `extracted/exefs/code.bin` and compared with `camp_func_002b8794` (`src/engine/leaf_batch41_a.cpp:831-884`):
  - **Guards:** Unsigned `slot >= 6` (`cmp r0, #6; bxhs lr`) and null manager (`*(u32*)0x0043DA2C == 0`) return without writes.
  - **Registry branch (`mode != 0`):** Uses `0x0043DA50` (`first_registry`) and `0x0043DA68` (`second_registry`). If `(s32)first_registry[slot] < 0`, scans `manager[0x4B8 + 0..5]` for nonzero; on first nonzero, stores `(priority, value)` and returns. Else if `first_registry[slot] == priority && second_registry[slot] == value`, clears both to `0xFFFFFFFF`.
  - **Manager & row writes:** Writes `u8(priority)` at `manager + 0x494 + slot * 4` and `u16(value)` at `manager + 0x496 + slot * 4`, then updates `row = manager + slot * 0x8C`:
    - `priority == 8`: `+0x3C = 4`, `+0x34 = 0x12`, `+0x38 = 0xFFFFFFFF`.
    - `priority == 7 || (9 <= priority <= 17)`: `+0x3C = 1`, `+0x34 = 0x12`, `+0x38 = 0xFFFFFFFF`.
    - Other priorities: `+0x34 = 0x12`, `+0x38 = 3`, `+0x3C = 0xFFFFFFFF`.
  - **H2 caller (`0x002B8B78`):** Calls `0x002B8794` six times (`slot = 0..5`) with `mode = 0`.

## 2. Fresh differential, controls, IPS, TU builds, & ledger/README

1. **Fresh differential (`python tools/h2_profile_slot_registry_experiment.py --out build/agent-work/H2-semantic/h2-profile-slot-registry-review-002b8794/run-001/checks/fresh-diff`, exit 0):**
   - Report: `build/agent-work/H2-semantic/h2-profile-slot-registry-review-002b8794/run-001/checks/fresh-diff/report.json` (SHA-256 `418b1e66e896c4b658e6cb4bbd246b29e7b88a9ed85f210e93518acf919f3bf0`).
   - `12/12` direct cases (`mismatch_count: 0`) and `2/2` original caller slices (`title_config_init_0x99` at `0x2F4DEC..0x2F4DF4`, `nested_callback_0xDC` at `0x286B7C..0x286B84`), each executing 6 real `0x002B8794` calls with `sp_aligned: true`.
   - `3/3` mutation controls detected: `slot_boundary`, `priority_eight`, `registry_mode`.
   - `272/304` bytes, `0` relocations, `ips_replay: true`, `changed_outside_slot: false`.
2. **Affected TU compiles (`-j 1`, both exit 0):**
   - `src/engine/leaf_batch41_a.cpp` -> `leaf_batch41_a.o` SHA-256 `264362a05d1f50d907784b043780938a4f3417699210edd76ce5ca3d29774787`.
   - `src/engine/leaf_batch32_c.cpp` -> `leaf_batch32_c.o` SHA-256 `9f98ea6a7f0f7c96644e6a2fb4b6503390c66d80f78e14ab1a33b7e926d63b1e`.
3. **Ledger & README:**
   - `config/functions.csv:5522` truthfully classifies `0x002b8794` (`304` bytes) as `non_matching`.
   - `README.md` line 89 documents `0x002B8794`, line 107 lists it, and lines 106–110 arithmetic (`3,117,224 + 21,884 = 3,139,108`, `10,881 + 78 = 10,959`, `99.3029%`) is internally consistent (while `config/functions.csv` reflects wider branch conversions: `9,470` `matching` / `8` `matching_span` / `1,489` `non_matching`).

## 3. Preserved limits

- Synthetic aligned ordinary-RAM manager/registry fixtures and controlled external service hooks in `0x002B8B78` (`mode=0` only in caller slices); manager lifecycle, natural callback reachability, audio output, and live Azahar runtime behavior remain unverified.
