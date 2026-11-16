# Independent contract review: `0x0011C5EC` H2 input state reader

**Verdict:** **ACCEPT** the recovered static contract in [`h2-input-state-reader-contract.md`](h2-input-state-reader-contract.md) (`6541631d...`) as an accurate instruction-level specification of `0x0011C5EC` for a bounded C++ implementation/validation seam.

## 1. Frozen input verification

Recomputed all `10/10` `input_sha256` pins in `build/agent-work/H2-semantic/h2-input-state-reader-contract-review-0011c5ec/run-001/task.json` (`0` mismatches):
- `extracted/exefs/code.bin`: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- `docs/agent-work/h2-input-state-reader-contract.md`: `6541631d89ecce00255a571239783fdb14f24e03de7236ba05a6229e9b681868`
- `src/engine/leaf_batch30_a.cpp`: `4796f75f521f88d31c4277469d1b1239c9f6f0f8a982991984fb82ee22c8d282`
- `config/functions.csv`: `52e3b05e982a43f32b82ec4a12eb49b3b43e4aefa9a317e4e30634a425740cc7` (`0x0011c5ec,304,non_matching,unknown,func_0011c5ec,src/engine/leaf_batch30_a.cpp` at line 435)
- `docs/function-records/0x001078d8.md`: `a12db3b13a230547aaa543f56c777f4e820bd98078f735aa32b22d226f204b0b`

## 2. Independent disassembly audit (`0x0011C5EC`, 304 bytes)

Disassembled `0x0011C5EC..0x0011C71B` from `extracted/exefs/code.bin` (Capstone ARM mode; literal word `0x00471AD8` at `0x0011C718`):

1. **Prologue & stack temporaries (`0x0011C5EC..0x0011C608`)**: Saves `{r4, r5, r6, lr}`, allocates `0x18` bytes, sets `r5 = context`, `r4 = output`, initializes `timestamp = 0xFFFFFFFFFFFFFFFF` at `[sp, #0x10]` (`strd`) and `index = 0xFFFFFFFF` at `[sp, #0x0C]`, leaving `count` at `[sp, #8]` uninitialized until `0x0012A758`.
2. **Mode check (`0x0011C60C..0x0011C614`)**: `bl 0x00128C2C`; nonzero returns `0` via `0x0011C70C`.
3. **Calibration (`0x0011C618..0x0011C61C`)**: `bl 0x001285C4(context + 0x0C)`.
4. **Ring read (`0x0011C620..0x0011C64C`)**: Unguarded loads `source_object = *(u32*)context` and `source = *(u32*)(source_object + 4)`. Passes `r0 = source`, `r1 = output`, `r2 = 1`, `r3 = sp + 8` (`&count`), `[sp] = sp + 0x10` (`&timestamp`), `[sp + 4] = sp + 0x0C` (`&index`) to `0x0012A758`. Signed `count <= 0` (`cmp r0, #0; ble 0x0011C70C`) returns `0`.
5. **Sample normalization (`0x0011C650..0x0011C668`)**: Reads signed halfwords `sample_x = *(s16*)(output + 0x0C)` and `sample_y = *(s16*)(output + 0x0E)` and calls `0x00128610(context + 0x0C, output + 0x0C, output + 0x0E, sample_x, sample_y)` with `sample_y` on `[sp]`.
6. **Reset-marker snapshot (`0x0011C66C..0x0011C684`)**: If `*(u8*)(context + 0x30) != 0`, copies `*(u32*)output` to `*(u32*)(context + 8)` and then clears `*(u8*)(context + 0x30) = 0`.
7. **Mask & edge derivation (`0x0011C688..0x0011C6AC`)**: Masks `new_state = *(u32*)output & ~0x2000u` and writes `output+0`, then writes `output+4 = (new_state ^ old_state) & ~old_state` and `output+8 = old_state & ~new_state` using `old_state = *(u32*)(context + 8)`, in exact store order `+0, +4, +8`.
8. **Conditional zeroing (`0x0011C6B0..0x0011C6E0`)**: Calls `0x002BB978()`; if nonzero, calls `0x002BC9C8()`; if that returns `0`, zeroes `output+0` (`str`), `output+8` (`str`), `output+4` (`str`), `output+0x0C` (`strh`), `output+0x0E` (`strh`) in that exact order.
9. **Snapshot & optional postprocess (`0x0011C6E4..0x0011C708`)**: Stores `*(u32*)(context + 8) = *(u32*)output`. Reads `*(u8*)0x00471AD8`; if `0`, calls `0x0013BCAC(output)`. Returns `r0 = 1` with `{r4, r5, r6}` and `SP` restored.

Every branch, call order, argument, write ordering, return value, and unguarded-pointer fault assumption in `docs/agent-work/h2-input-state-reader-contract.md` matches the pinned ARM disassembly.

## 3. Recommended bounded implementation seam & open scope

- **No blockers** for a bounded differential validation/conversion task on `0x0011C5EC` (`src/engine/leaf_batch30_a.cpp:4741-4800` already contains a matching-structure C++ `func_0011c5ec` using `asm volatile("" ::: "memory")` barriers).
- **Recommended seam**:
  1. Compile `func_0011c5ec` (`src/engine/leaf_batch30_a.cpp`) and verify whether it fits the 304-byte original slot (or document placement if larger) and resolves all 7 even ARM `BL` relocations (`0x00128C2C`, `0x001285C4`, `0x0012A758`, `0x00128610`, `0x002BB978`, `0x002BC9C8`, `0x0013BCAC`) at final VMA.
  2. Run Unicorn ARM differential tests with the 7 callees retained original or deterministically hooked (recording arguments, stack out-params, and call order), covering all 5 contract paths plus ordered-write and edge-derivation mutation controls, and compose through original `0x001078D8` (`output = 0x004E3C28`).
- **Open scope**: Physical input identity, producer scheduling/cadence, unmapped/aliased pointer behavior, and live Azahar runtime behavior remain open.
