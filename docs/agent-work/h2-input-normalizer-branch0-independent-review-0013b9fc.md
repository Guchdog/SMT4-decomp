# Independent Review: `0x0013B9FC` (`ui_func_0013b9fc`) Radial Normalizer

## Verdict

**Disposition:** **Accept** `ui_func_0013b9fc` (`src/engine/leaf_batch30_a.cpp:3108-3175`) for promotion within its tested disjoint ordinary-RAM domain and retaining original signed divider `0x002C615C`.

This review does not claim pointer-aliasing parity, malformed-pointer fault parity, physical input provenance, or live Azahar runtime equivalence.

## 1. Independent Disassembly & Contract Audit (`0x0013B9FC`, 228 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x0013B9FC..0x0013BAE0` and verified all 11 `input_sha256` pins:

- **Signed wrap boundaries**: `R2 = low32(x*x + y*y)`, `A2 = low32(A*A)`, `B2 = low32(B*B)`, `Q = low32(R2 << 14)`, `D`, and `P` all use explicit unsigned 32-bit wrap (`u32`) followed by two's-complement `s32` reinterpretation (`input_bits_as_s32_0013b9fc`), matching ARM `mul`/`mla`/`lsl`/`cmp` signed comparisons (`R2 <= A2`, `Q <= 0`, `B2 <= R2`).
- **Divider return & zero paths**: `Q <= 0` sets `magnitude = 0` and skips the Newton sqrt loop (`0x13BA48..0x13BA4C`); `0x002C615C` (`ui_func_002c615c`) is called with `(u32, u32)` and its low 32-bit quotient `static_cast<u32>(quotient_remainder)` is extracted.
- **Ordered stores & low-halfword return**:
  - Deadzone (`R2 <= A2`): stores `0` (`u16`) to `output_y` then `output_x`, returns `0`.
  - Active (`R2 > A2`): calls `0x002C615C(x*P, M)` -> `*output_x` (`u16`), then `0x002C615C(y*P, M)` -> `*output_y` (`u16`), returns `static_cast<s16>(static_cast<u16>(delta))` (`sxth`).

## 2. Fresh Offline Rerun & Affected Consumer Compile

- `python tools/h2_input_normalizer_branch0_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-branch0-review-0013b9fc/run-001/checks/direct` (exit `0`, `report.json` SHA-256 `5238279c5bd9669367a525dc9de4b3cc00589c15a2ab526e790c28bd7341b53a`):
  - `107/107` direct cases (`0` mismatches), `14` zero-divisor observations.
  - `16/16` original `0x00128610`/`0x0011C5EC` compositions (`0` mismatches).
  - `3/3` negative controls detected (`inner_uses_outer`, `deadzone_store_order`, `divide_denominator_off_by_one`).
  - `208/228` bytes, `3` even ARM `R_ARM_CALL` relocations to `0x002C615C` (`entry_bit0=0`: offsets `96`, `176`, `192`), `ips_replay=true`.
- `python tools/build_check.py --tu src/engine/leaf_batch29_a.cpp --out-dir build/agent-work/H2-semantic/h2-input-normalizer-branch0-review-0013b9fc/run-001/consumer -j 1` (exit `0`, `leaf_batch29_a.o` SHA-256 `48ca198df64bc2812bd9d8d56d1d46b28ff6a76b727314de5161c9a8ac323a52`).

## 3. Limits

- Disjoint valid ordinary-RAM buffers and controlled `0x0012A758` ring seam only; `0x002C615C` remains original ARM; pointer aliasing, malformed pointers, MMIO, and live Azahar runtime remain unresolved.
