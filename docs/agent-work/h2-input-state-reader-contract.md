# `0x0011C5EC` H2 input state reader — bounded static contract

## 1. Scope & frozen pins

- Static pinned-image/source audit only (`compiler_slots: 0`); no compiler, tests, or emulator were run.
- Verified `11/11` `input_sha256` pins in `build/agent-work/H2-semantic/h2-input-state-reader-contract-0011c5ec/run-001/task.json` (`extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `config/functions.csv:435` classifies `0x0011c5ec` (`304` bytes, `func_0011c5ec`, `src/engine/leaf_batch30_a.cpp`) as `non_matching`.

## 2. Instruction, callee, and memory-effect trace (`0x0011C5EC`, 304 bytes)

Disassembled `0x0011C5EC..0x0011C71B` from `extracted/exefs/code.bin` (literal `0x00471AD8` at `0x0011C718`):

- **Prologue & stack temporaries:** Saves `{r4, r5, r6, lr}` (`r5 = context`, `r4 = output`), allocates `0x18` bytes on stack. Initializes `timestamp = 0xFFFFFFFFFFFFFFFF` at `SP+0x10..0x17` (`strd r0, r1, [sp, #0x10]`) and `index = 0xFFFFFFFF` at `SP+0x0C` (`str r0, [sp, #0xc]`) before any callee. `count` lives at `SP+8`.
- **Step 1 (`0x0011C60C: bl 0x00128C2C`):** Calls `func_00128c2c()`. If `r0 != 0`, branches to `0x0011C70C` and returns `0` (early exit 1).
- **Step 2 (`0x0011C61C: bl 0x001285C4`):** Calls `func_001285c4(context + 0x0C)` (`s16* calibration`).
- **Step 3 (`0x0011C640: bl 0x0012A758`):** Dereferences `source_object = *(u32*)context`, then `source = *(u32*)(source_object + 4)` (two unguarded pointer loads). Passes `r0 = source`, `r1 = output`, `r2 = 1`, `r3 = &count (SP+8)`, stack args `&timestamp (SP+0x10)`, `&index (SP+0x0C)` to `func_0012a758`. Reads `count` from `SP+8`; if `count <= 0` (signed `ble`), returns `0` (early exit 2).
- **Step 4 (`0x0011C668: bl 0x00128610`):** Reads `sample_x = *(s16*)(output + 0x0C)` and `sample_y = *(s16*)(output + 0x0E)` and calls `func_00128610(context + 0x0C, output + 0x0C, output + 0x0E, sample_x, sample_y)` (`sample_y` on `[SP]`).
- **Step 5 (`0x0011C66C..0x0011C684`):** If `*(u8*)(context + 0x30) != 0`, copies `*(u32*)output` to `*(u32*)(context + 8)`, then clears `*(u8*)(context + 0x30) = 0`.
- **Step 6 (`0x0011C688..0x0011C6AC`):** Reads `new_state = *(u32*)output & ~0x2000u`, writes `*(u32*)output = new_state`. Reads `old_state = *(u32*)(context + 8)`. Writes rising-edge bits `*(u32*)(output + 4) = (new_state ^ old_state) & ~old_state`, then falling-edge bits `*(u32*)(output + 8) = old_state & ~new_state` (preserving store order `+0`, `+4`, `+8`).
- **Step 7 (`0x0011C6B0..0x0011C6E0`):** Calls `func_002bb978()`. If `r0 != 0`, calls `func_002bc9c8()`. If that returns `0`, zeroes `output+0`, `output+8`, `output+4` (32-bit stores), `output+0x0C`, `output+0x0E` (16-bit stores) in that exact order.
- **Step 8 (`0x0011C6E4..0x0011C708`):** Snapshots `*(u32*)(context + 8) = *(u32*)output`. Loads `*(u8*)0x00471AD8`; if `0`, calls `func_0013bcac(output)`. Returns `1` (`r4..r6`, `SP` restored).

## 3. H2 counter refresh vs H4 camera / shared paths

- Image-wide word-aligned ARM `BL` scan of `extracted/exefs/code.bin` found **only one** direct `BL` caller of `0x0011C5EC`: `0x001078E8` inside `func_001078d8` (H2 logical counter refresh, passing `output = 0x004E3C28`).
- `func_001078d8` reads `*(u32*)0x004E3C28` (and writes availability to `0x004650A4`, counters to `0x004E3C58..`), while `engine_func_0010B578` calls `func_001078d8` and `crt_func_00101308` calls `engine_func_0010B578` at `0x00101B8C` (observed in H4 image-wide ARM review).
- No separate H4 camera reader directly `BL`s `0x0011C5EC` in the word-aligned ARM scan; any shared effect with other subsystems is through the state buffer `0x004E3C28` / `0x004E3C58` or indirect/Thumb calls not covered by word-aligned ARM `BL` scanning.

## 4. Concrete bounded fixtures & explicit limits

- **Concrete bounded direct/caller fixtures:**
  1. Mode-4 early return (`func_00128c2c() != 0` -> returns `0`, no writes).
  2. Ring-empty/error early return (`count <= 0` from `func_0012a758` -> returns `0`, `context+0x0C` calibrated).
  3. Normal path with `context[0x30] == 0` vs `context[0x30] != 0`, testing bit `0x2000` masking on `output[0]`, rising/falling edges at `output+4`/`output+8`, and `context+8` snapshot.
  4. Flag-clear path (`func_002bb978() != 0 && func_002bc9c8() == 0` -> ordered zeroing of `output+0/+8/+4/+0x0C/+0x0E`).
  5. Optional postprocess path (`*(u8*)0x00471AD8 == 0` vs `!= 0` gating `func_0013bcac(output)`).
  6. Caller composition through `0x001078D8` (`output = 0x004E3C28`, `0x004650A4`, `0x004E3C58` counters).
- **Limits:** Requires valid non-null aligned ordinary-RAM `context`, `*context`, `*(*context + 4)`, and `output` pointers (no null guards); assumes non-aliasing between `context`, `output`, and `0x00471AD8`; relies on 7 callees (`0x00128C2C`, `0x001285C4`, `0x0012A758`, `0x00128610`, `0x002BB978`, `0x002BC9C8`, `0x0013BCAC`). Physical controls, input freshness, callback cadence, device semantics, and safe runtime writes are **not** inferred or established.
