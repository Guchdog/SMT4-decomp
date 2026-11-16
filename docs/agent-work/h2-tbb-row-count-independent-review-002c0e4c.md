# Independent Review: `0x002C0E4C` (`Tbb_GetRowCount`)

## Verdict

**Disposition:** **Accept** `Tbb_GetRowCount` (`src/ui/tbb_loader.cpp:80-86`, `matching`, `56/56` bytes, `exact_matching=true` after relocating offset `40` `R_ARM_JUMP24` to `0x002C6C10`) for its bounded synthetic-TBL1 domain and `0x002AEA28` composition.

This review does not claim live TBB resource population, downstream profile validity, or Azahar audio/runtime equivalence.

## 1. Independent Disassembly & Contract Audit (`0x002C0E4C`, 56 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x002C0E4C..0x002C0E84` and verified all 18 `input_sha256` pins:

- **Null, magic & zero-stride guards**:
  1. `cmp r0, #0; beq 0x2c0e78` (`return 0` if `table == nullptr`).
  2. `ldr r1, [r0]; ldr r2, [pc, #0x20]; cmp r1, r2; bne 0x2c0e78` (`0x002C0E80` = `0x314C4254` `'TBL1'`; `return 0` if magic mismatches).
  3. `ldr r1, [r0, #8]; cmp r1, #0; beq 0x2c0e78` (`return 0` if `row_stride == 0`).
- **Unsigned quotient arguments, tail call & ABI**:
  - `ldr r0, [r0, #4]; b 0x2c6c10` tail-calls `ui_func_002c6c10(payload_size, row_stride)` (`u32` quotient returned in `r0`), with no stack frame, no callee-saved spills, and no writes.
  - Unmapped non-null `table` pointers fault at `ldr r1, [r0]`; `Tbb_GetRowCount` (`src/ui/tbb_loader.cpp:80-86`) matches the pinned ARM body byte-for-byte after relocation.

## 2. Fresh Offline Rerun, Controls, Interworking & Ledger/README Counts

- `python tools/h2_tbb_row_count_experiment.py --out build/agent-work/H2-semantic/h2-tbb-row-count-review-002c0e4c/run-001/checks/fresh` (exit `0`, `report.json` SHA-256 `6f88dc5036677775c4e2692687af699cecf8e8a33ce07cd93183533d00508d2c`):
  - `exact_matching: true`, `56/56` bytes, `1` relocation (`offset: 40`, `type: 29` `R_ARM_JUMP24`, `ui_func_002c6c10` `0x2c6c10`, `target_bit0_clear: true`).
  - `13/13` direct final-VMA cases (`mismatch_count=0`).
  - `5/5` compositions through original `0x002AEA28` (`index in {0, 4, 5, 6, 0xffffffff}`, `equal=true`, `divider_calls` `[(0x2c6c10, (0x50, 0x10), sp_aligned=True)]`).
  - `3/3` mutation controls detected (`wrong_magic_literal`, `wrong_zero_stride_boundary`, `swapped_division_operands`).
  - `ips_replay: true`, `changed_outside_slot: false`.
- **Affected-TU & interworking artifacts**: Verified `affected-tus/report.json` (`85258bb9...`: `tbb_loader.cpp`, `leaf_batch24_b.cpp`, `leaf_batch32_c.cpp` all `exit_code: 0`) and `interworking.json` (`1d43f002...`).
- **Ledger vs. README count audit**:
  - `config/functions.csv:5752` truthfully classifies `0x002c0e4c` as `matching`; CSV totals `9,470` `matching` (`2,898,900` B) + `1,489` `non_matching` (`239,724` B) + `8` `matching_span` (`484` B) = `10,959` functions + `8` spans (`3,139,108` B).
  - `README.md` lines 106–110 totals `3,139,108` B across `10,959` functions + `8` spans (`3,117,224 + 21,884`, `10,881 + 78` from the prior baseline snapshot).

## 3. Limits

- Aligned readable synthetic `TBL1` headers in ordinary RAM; original ARM divider `0x002C6C10` retained; live TBB resource population, downstream profile validity, and Azahar audio/runtime remain unverified.
