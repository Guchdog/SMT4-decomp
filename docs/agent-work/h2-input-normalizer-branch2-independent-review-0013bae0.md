# `0x0013BAE0` (`func_0013bae0`) — independent review

**Verdict: APPROVED for bounded promotion (`non_matching`, `368/460` bytes, `0` relocations) within the tested disjoint ordinary-RAM and non-exceptional VFP domain.**

## 1. Frozen pins, VFP instruction sequence, & source audit

- Recomputed all `12/12` `input_sha256` entries in `build/agent-work/H2-semantic/h2-input-normalizer-branch2-review-0013bae0/run-001/task.json`: `12/12` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled `0x0013BAE0..0x0013BCAB` (460 bytes) from `extracted/exefs/code.bin` and compared with `func_0013bae0` (`src/engine/leaf_batch44_c.cpp:720-812`):
  - **Signed-wrap conversions:** `x*x`, `y*y`, `x*x + y*y`, `b*b`, and `b - 40` wrap modulo `2^32` and reinterpret as `s32` before `vcvt.f32.s32`.
  - **VFP compare predicates & clamp:** `vcmp.f32` (`== 0.0f`), `vcmpe.f32` (`!(boundary_squared < 1600.0f)` -> `1600.0f`), `vcmpe.f32` (`radius_squared < boundary_squared`), and `vcmpe.f32` (`radius_squared < b_squared`).
  - **Sqrt/division grouping & outputs:** Inline `vsqrt.f32`, `(x_component * radius_delta) / ((b_value - boundary_radius) * input_radius)` vs `x_component / input_radius`, `vcvt.s32.f32` truncating conversion, `strh` X then Y (`output_x` then `output_y`), and residual `r0 = output_x`.

## 2. Fresh seeded differential (`--seed 20261128`), IPS, & TU compiles

1. **Fresh differential (`python tools/h2_input_normalizer_branch2_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-branch2-review-0013bae0/run-001/checks/fresh-diff --seed 20261128`, exit 0):**
   - Report: `build/agent-work/H2-semantic/h2-input-normalizer-branch2-review-0013bae0/run-001/checks/fresh-diff/report.json` (SHA-256 `b9bdc8cfa10f78a2495589acac307cebe79e1510ee706a73017087f33b886098`).
   - `352/352` direct cases (`direct_mismatches: 0`) and `18/18` `0x00128610`/`0x0011C5EC` caller compositions (`caller_mismatches: 0`).
   - `3/3` negative controls detected: `boundary_extent`, `boundary_clamp`, `truncation_vs_rounding`.
   - `368/460` bytes, `0` relocations (self-contained inline `vsqrt.f32` + constant pool), `0x00128658` selector-2 call targets even ARM `0x0013BAE0`, `ips_replay: true`, `only_original_slot_changed: true`.
2. **Affected TU compiles (`-j 1`, both exit 0):**
   - `src/engine/leaf_batch44_c.cpp` -> `leaf_batch44_c.o` SHA-256 `f46154067a8aca79e270014fc7a26b5e16d5e41f49e5573c34fce34eed8fd7eb`.
   - `src/engine/leaf_batch29_a.cpp` -> `leaf_batch29_a.o` SHA-256 `48ca198df64bc2812bd9d8d56d1d46b28ff6a76b727314de5161c9a8ac323a52`.

## 3. Preserved limits

- Valid disjoint ordinary RAM, controlled `0x0012A758` ring seam, and non-exceptional VFP domain (FPSCR exception flags are recorded but excluded from acceptance); aliasing, invalid pointers, MMIO, physical input provenance, and live Azahar runtime remain unverified.
