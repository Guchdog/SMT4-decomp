# `0x00128610` H2 input sample-normalizer dispatcher — bounded static contract

## 1. Identity & frozen pins

- Pinned static ARM audit and caller mapping only (`compiler_slots: 0`); no source, ledger, README, build, or emulator changes.
- Verified `10/10` `input_sha256` pins in `build/agent-work/H2-semantic/h2-input-normalizer-contract-00128610/run-001/task.json` (`extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `config/functions.csv`: `0x00128610`, `148` bytes, `non_matching`, `unknown`, `func_00128610`, `src/engine/leaf_batch29_a.cpp` (existing C++ at `src/engine/leaf_batch29_a.cpp:3041-3061`).

## 2. Disassembled 148-byte ARM body (`0x00128610..0x001286A3`)

- **ABI & prologue:** `u32 func_00128610(s16* calibration, s16* output_x, s16* output_y, s32 sample_x, s32 sample_y)`. Saves `{r4, lr}`, allocates `8` stack bytes (`[SP..SP+7]` for outgoing args 5–6; incoming `sample_y` is at `[SP+0x10]`). Preserves `r4..r11` and `SP`.
- **Selector & argument marshaling:** Reads unsigned byte `selector = *(u8*)(calibration + 0x0C)` (`ldrb r1, [r0, #0xc]`). Sets `r2 = sample_x`, `r3 = sample_y`, `ip = output_x`, `r4 = output_y`.
- **Three calibration routes (all `ldrsh` signed-halfword loads from `s16 calibration[6]`):**
  - `selector == 0`: calls `0x0013B9FC(output_x, output_y, sample_x, sample_y, calibration[0], calibration[3])` (`+0`, `+6`), returns callee `r0`.
  - `selector == 1`: calls `0x0013B8F8(output_x, output_y, sample_x, sample_y, calibration[1], calibration[4])` (`+2`, `+8`), returns callee `r0`.
  - `selector == 2`: calls `0x0013BAE0(output_x, output_y, sample_x, sample_y, calibration[2], calibration[5])` (`+4`, `+0x0A`), returns callee `r0`.
  - `selector >= 3` (default): makes no call, writes nothing outside stack, and returns `r0 = calibration` (original incoming `r0`).
- **Memory writes:** No heap/global writes by `0x00128610` itself; writes only `[SP..SP+7]` and whatever the selected normalizer writes via `output_x`/`output_y`.

## 3. Actual `0x0011C5EC` caller mapping (`0x0011C668`)

- Word-aligned ARM `BL` scan of `extracted/exefs/code.bin` found **one** direct caller: `0x0011C668` inside `func_0011c5ec`.
- After `func_001285c4(context + 0x0C)` clamps the calibration block and `func_0012a758` populates `output`, `0x0011C5EC` passes `calibration = context + 0x0C`, `output_x = output + 0x0C`, `output_y = output + 0x0E`, `sample_x = *(s16*)(output + 0x0C)`, `sample_y = *(s16*)(output + 0x0E)`. `0x0011C5EC` ignores `0x00128610`'s `r0` return.

## 4. Bounded typed-C++ & differential validation plan

- **Slot & interworking:** Compile `src/engine/leaf_batch29_a.cpp` (1 slot); verify `func_00128610 <= 148` bytes and 3 even ARM `R_ARM_CALL` relocations to `0x0013B9FC`, `0x0013B8F8`, `0x0013BAE0` (bit 0 == 0).
- **Direct differential:** Cover selectors `{0, 1, 2, 3, 255}` and signed halfword boundaries `{-32768, -1, 0, 1, 32767}` on `calibration[0..5]` and `sample_x/sample_y`, comparing `r0` (including `r0 == calibration` on `default`), `r4..r11`, `SP`, `output_x`/`output_y`, and callee argument traces.
- **Mutation controls & caller composition:** Inject swapped calibration pair (`calibration[1]`/`calibration[4]`), wrong selector case, and wrong `default` return; compose through original `0x0011C5EC` (`0x0011C668`) and `0x001078D8`.
- **Limits:** Non-aliasing aligned ordinary-RAM `calibration`, `output_x`, `output_y` assumed; normalizers `0x0013B9FC`, `0x0013B8F8`, `0x0013BAE0` (and VFP/divider dependencies) remain separate; invalid pointers and live runtime remain out of scope.
