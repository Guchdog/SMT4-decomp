# Independent Review: `0x0013B8F8` (`ui_func_0013b8f8`) Selector-1 Normalizer

## Verdict

**Disposition:** **Accept** `ui_func_0013b8f8` (`src/engine/leaf_batch28_a.cpp:1186-1262`) for coordinator promotion to `non_matching` within its tested disjoint ordinary-RAM domain and retaining original signed divider `0x002C615C`.

This review does not claim pointer-aliasing parity, malformed-pointer fault parity, physical input provenance, or live Azahar runtime equivalence.

## 1. Independent Disassembly & Edge Audit (`0x0013B8F8`, 260 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x0013B8F8..0x0013B9FC` and verified all 13 `input_sha256` pins:

- **`INT32_MIN` wrapped negation vs. `INT16_MIN` caller**:
  - Original `rsb ip, r2, #0; cmp ip, r0` wraps `sample_x = 0x80000000` (`INT32_MIN`) to `0x80000000` and performs a signed `>` comparison against `calibration_a` (false for `calibration_a >= INT32_MIN`, yielding `0`).
  - Caller `0x00128610` passes sign-extended `s16` (`-32768 = 0xFFFF8000`), which negates to `+32768`. `ui_func_0013b8f8` matches both via `0u - x_bits` and signed `negated_x > calibration_a`.
- **Direct & scaled branches, divider zero path, ordered writes, return**:
  - `delta = low32(B - A)`, `radius_squared = low32(tx*tx + ty*ty)`, `delta_squared = low32(delta*delta)`.
  - Direct (`delta_squared > radius_squared`): stores `tx` to `output_x`, `ty` to `output_y`, returns `sxth(delta)`.
  - Scaled (`delta_squared <= radius_squared`): `scaled_radius = low32(radius_squared << 14)`, `<= 0 -> M = 0`; else Newton sqrt via `0x002C615C`, then `0x002C615C(tx * (delta << 7), M)` -> `output_x`, `0x002C615C(ty * (delta << 7), M)` -> `output_y`, returns `sxth(delta)`.

## 2. Fresh Offline Rerun (Distinct Seed `20261126`) & Affected TUs

- `python tools/h2_input_normalizer_branch1_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-branch1-review-0013b8f8/run-001/checks/direct --seed 20261126` (exit `0`, `report.json` SHA-256 `8a43bf686e0984d91b66f19bcc8b2c49dbba1633a659e21f78b265a9136c3462`):
  - `176/176` direct cases (`0` mismatches), `26` zero-divisor observations.
  - `16/16` original `0x00128610`/`0x0011C5EC` caller compositions (`0` mismatches).
  - `3/3` negative controls detected (`int32_min_wrapped_negation`, `equal_radius_direct_branch`, `direct_store_order`).
  - `252/260` bytes, `3` even ARM `R_ARM_CALL` relocations to `0x002C615C` (`entry_bit0=0`: offsets `176`, `216`, `232`), `ips_replay=true`.
- `python tools/build_check.py --tu src/engine/leaf_batch28_a.cpp --out-dir build/agent-work/H2-semantic/h2-input-normalizer-branch1-review-0013b8f8/run-001/tu-compile -j 1` (exit `0`, `leaf_batch28_a.o` SHA-256 `34f9bd8ac6cac4bf94e6b5163cd4d75d540e0837875fb3c4e5606dc9036b470b`).
- `python tools/build_check.py --tu src/engine/leaf_batch29_a.cpp --out-dir build/agent-work/H2-semantic/h2-input-normalizer-branch1-review-0013b8f8/run-001/tu-compile -j 1` (exit `0`, `leaf_batch29_a.o` SHA-256 `48ca198df64bc2812bd9d8d56d1d46b28ff6a76b727314de5161c9a8ac323a52`).

## 3. Limits

- Disjoint valid ordinary-RAM buffers and controlled `0x0012A758` ring seam only; `0x002C615C` remains original ARM; pointer aliasing, malformed pointers, MMIO, and live Azahar runtime remain unresolved.
