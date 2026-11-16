# Independent Review: `0x001285C4` (`func_001285c4`) Calibration Clamp

## Verdict

**Disposition:** **Accept** `func_001285c4` (`src/engine/leaf_batch11_b.cpp:132-140`) for coordinator promotion to `non_matching` within its tested disjoint ordinary-RAM domain.

This review does not claim pointer-aliasing parity, malformed-pointer fault parity, physical input provenance, or live Azahar runtime equivalence.

## 1. Independent Disassembly & Boundary Audit (`0x001285C4`, 76 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x001285C4..0x00128610` and verified all 14 `input_sha256` pins:

- **Five signed halfword boundaries (`ldrsh`/`cmp`/`strh`)**:
  - `calibration[0]` (`+0x00`): `< 40` (`0x28`) -> `40`
  - `calibration[1]` (`+0x02`): `< 36` (`0x24`) -> `36`
  - `calibration[2]` (`+0x04`): untouched
  - `calibration[3]` (`+0x06`): `> 145` (`0x91`) -> `145`
  - `calibration[4]` (`+0x08`): `> 145` (`0x91`) -> `145`
  - `calibration[5]` (`+0x0a`): `> 145` (`0x91`) -> `145`
- **ABI & unaffected bytes**: Returns via `bx lr` with 0 relocations, 0 stack writes, and no writes outside `calibration[0..1, 3..5]`. Original `0x0011C61C` in `func_0011c5ec` calls even ARM address `0x001285C4` (`entry_bit0=0`).

## 2. Fresh Offline Rerun & Affected TU Compilation

- `python tools/h2_calibration_clamp_experiment.py --out build/agent-work/H2-semantic/h2-calibration-clamp-review-001285c4/run-001/checks/direct` (exit `0`, `report.json` SHA-256 `1a806cf124715c9adfd4e2e1e7382c2abc9923eed15b7a4bf33863fd534b166b`):
  - `334/334` direct cases (`0` mismatches across all 5 signed-halfword boundaries and unaffected bytes).
  - `16/16` original `0x001078D8 -> 0x0011C5EC` compositions (`0` mismatches, controlled `0x0012A758` ring seam).
  - `3/3` negative controls detected (`first_minimum_off_by_one`, `second_field_wrong_offset`, `upper_comparator_includes_boundary`).
  - `76/76` bytes, `0` relocations, `ips_replay=true`.
- `python tools/build_check.py --tu src/engine/leaf_batch11_b.cpp --out-dir build/agent-work/H2-semantic/h2-calibration-clamp-review-001285c4/run-001/tu-compile -j 1` (exit `0`, `leaf_batch11_b.o` SHA-256 `c446d43463ce9b70b49d2819f16d233061ac8789f42b4440ea630e1a52a8cb08`).
- `python tools/build_check.py --tu src/engine/leaf_batch30_a.cpp --out-dir build/agent-work/H2-semantic/h2-calibration-clamp-review-001285c4/run-001/tu-compile -j 1` (exit `0`, `leaf_batch30_a.o` SHA-256 `e39b538b01ba53ed49cc5cdd231862d4d25d64a2e255092483b0bd7776a2bf33`).

## 3. Limits

- Disjoint valid ordinary-RAM buffers and controlled `0x0012A758` ring seam only; aliasing, malformed pointers, MMIO, physical input provenance, and live Azahar runtime remain unresolved.
