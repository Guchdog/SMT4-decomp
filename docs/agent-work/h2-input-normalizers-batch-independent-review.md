# H2 three-selector input-normalizer batch integration — independent review

**Verdict: APPROVED for bounded three-slot staged integration (`0x0013B9FC`, `0x0013B8F8`, `0x0013BAE0`) with original `0x0011C5EC` reader, original `0x00128610` dispatcher, and original `0x002C615C` divider.**

## 1. Frozen pins & even ARM selector callsites

- Recomputed all `11/11` `input_sha256` entries in `build/agent-work/H2-semantic/h2-input-normalizers-all-selector-review/run-001/task.json`: `11/11` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently verified all three `0x00128610` `BL` callsites in `extracted/exefs/code.bin`:
  - `0x00128678` (`0xeb004cdf`) -> `0x0013B9FC` (`bit0 = 0`)
  - `0x00128698` (`0xeb004c96`) -> `0x0013B8F8` (`bit0 = 0`)
  - `0x00128658` (`0xeb004d20`) -> `0x0013BAE0` (`bit0 = 0`)

## 2. Fresh seeded three-slot batch run (`--seed 20261129`) & TU compiles

1. **Batch differential (`python tools/h2_input_normalizers_batch_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizers-all-selector-review/run-001/checks/fresh-batch --seed 20261129`, exit 0):**
   - Report: `build/agent-work/H2-semantic/h2-input-normalizers-all-selector-review/run-001/checks/fresh-batch/report.json` (SHA-256 `75850f3d3b504cde40a8f612ca7e9d926f5377d4f9febe5f03e985c2c42ca33e`).
   - Three-slot staged image (`staged_image_sha256`: `5ba67461679f3efc83bd482d26da897f549b722d3f82614919c2ff945d1475c4`), three-slot IPS (`ips_sha256`: `acc4b06f03598b06697ee9ec15d25c5e9299c4b801b1586817bc4cca75bad950`):
     - Selector 0 (`0x0013B9FC`): `208/228` bytes, `3` even ARM `R_ARM_CALL` relocs to `0x002C615C` (`entry_bit0: 0`).
     - Selector 1 (`0x0013B8F8`): `252/260` bytes, `3` even ARM `R_ARM_CALL` relocs to `0x002C615C` (`entry_bit0: 0`).
     - Selector 2 (`0x0013BAE0`): `368/460` bytes, `0` relocations.
   - `ips_replay: true`, `only_three_declared_slots_changed: true`.
   - `402/402` caller compositions through original `0x0011C5EC` & `0x00128610` (`caller_mismatches: 0`: `132` each for selectors `0`, `1`, `2` + `6` gate/unsupported cases).
2. **Affected TU compiles (`-j 1`, all 4 exit 0):**
   - `src/engine/leaf_batch30_a.cpp` -> `e39b538b01ba53ed49cc5cdd231862d4d25d64a2e255092483b0bd7776a2bf33`
   - `src/engine/leaf_batch28_a.cpp` -> `34f9bd8ac6cac4bf94e6b5163cd4d75d540e0837875fb3c4e5606dc9036b470b`
   - `src/engine/leaf_batch44_c.cpp` -> `f46154067a8aca79e270014fc7a26b5e16d5e41f49e5573c34fce34eed8fd7eb`
   - `src/engine/leaf_batch29_a.cpp` -> `48ca198df64bc2812bd9d8d56d1d46b28ff6a76b727314de5161c9a8ac323a52`

## 3. Preserved limits

- Valid disjoint ordinary RAM, controlled `0x0012A758` ring seam, and pinned original reader/dispatcher/divider `0x002C615C`; FPSCR exception-flag parity, physical input provenance, cadence, live Azahar runtime, and whole-title equivalence remain unverified.
