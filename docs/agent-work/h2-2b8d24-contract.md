# 0x002B8D24: static contract and branch map for full C++ conversion decision

## Scope and identity

- **Original binary**: `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`), ARM function at `0x002B8D24`, 360 bytes (`0x002B8D24..0x002B8E8B`).
- **Production source**: `src/engine/leaf_batch46_a.cpp` (SHA-256 `988c31cebe3e4413156f3805eecc84e40695bf5597a6159f771ffd68ac9c33b9`), symbol `battle_func_002b8d24` (classified `non_matching` in `config/functions.csv:5535`).
- **Supporting read sources**: `src/engine/leaf_batch13_a.cpp` (`0x002AF854`, SHA-256 `f7f0fe79b857e70ee672d291c3793dd96cca635ce48245eb20aaac6ee07318d8`), `src/engine/leaf_batch41_b.cpp` (`0x002BF030`, SHA-256 `7a3b1952bc0a40b66da9e392bd7a954ed48500e1bede7fab4bbbf37698345575`).
- **Method**: Static Capstone ARM disassembly and source inspection only; no compilation, Unicorn execution, or emulator run.

## Entry, index boundaries, and jump table

On entry (`0x002B8D24..0x002B8D34`), `r0 = object`, `r1 = selector` (unsigned 32-bit):

1. `push {r4, r5, r6, lr}`
2. `cmp r1, #0x13` (unsigned compare against 19)
3. `mov r5, r0` (`r5` caches `object`; `r0` remains `object`)
4. `ldrlo pc, [pc, r1, lsl #2]` (if `selector < 19`, dispatch via 19-entry jump table at `0x002B8D38..0x002B8D80`)
5. `0x002B8D34`: `pop {r4, r5, r6, pc}` (fallback for `selector >= 19` and shared return for no-op selectors; returns `r0 = object`)

### Complete jump-table mapping (`0x002B8D38..0x002B8D80`)

| Selector(s) | Table Entry VMA | Target VMA | Behavior Summary |
| --- | --- | --- | --- |
| `0` | `0x002B8D38` | `0x002B8D34` | No-op; returns `r0 = object` |
| `1`, `10` | `0x002B8D3C`, `0x002B8D60` | `0x002B8E04` | Tail-call `0x002AF854(object + 0xC4, 2, 0)` |
| `2..5`, `16..18` | `0x002B8D40..0x002B8D4C`, `0x002B8D78..0x002B8D80` | `0x002B8D84` | `0x002AF854(object + 0xC4, 2, 0)`, `0x002AF854(object + 0x1DC, 2, 0)`, tail-call `0x001384F0(object + 0x150, 0)` |
| `6` | `0x002B8D50` | `0x002B8DB4` | Load `u32` at `object + 0xE4` into `s0`/`r0`; if `!= 0x3F800000`, return `value` (`r0` & `s0`), else tail-call `0x002AF854(object + 0xC4, 2, 0)` |
| `7..9` | `0x002B8D54..0x002B8D5C` | `0x002B8DDC` | `0x002AF854(object + 0xC4, 2, 0)`, tail-call `0x002AF854(object + 0x40C, 2, 0)` |
| `11` | `0x002B8D64` | `0x002B8E18` | `0x002BF030(object + 0xC4, 7)`, `0x002BF030(object + 0x268, 7)`, tail-call `0x001384F0(object + 0x380, 0)` |
| `12` | `0x002B8D68` | `0x002B8E40` | Loop `i = 0..4`: if `object[0x37 + i] != 0`, call `0x002AF854(object + 0x498 + i * 140, 5, 0)`; then `*(u32*)(object + 0x28) = 0`, return `r0 = 0` |
| `13`, `14`, `15` | `0x002B8D6C..0x002B8D74` | `0x002B8D34` | No-op; returns `r0 = object` |
| `>= 19` (unsigned) | — (falls through) | `0x002B8D34` | No-op; returns `r0 = object` |

## Branch details, memory writes, and return values

1. **`selector in {0, 13, 14, 15}` or `selector >= 19` (`0x002B8D34`)**
   - **Writes / calls**: None.
   - **Return**: `r0 = object`.
2. **`selector in {1, 10}` (`0x002B8E04..0x002B8E14`)**
   - Restores `{r4, r5, r6, lr}` and tail-branches (`b #0x2af854`) with `r0 = object + 0xC4`, `r1 = 2`, `r2 = 0`.
   - **Writes / return**: All writes are inside `0x002AF854`; returns `0x002AF854`'s `r0` (`object + 0xC4`).
3. **`selector in {2, 3, 4, 5, 16, 17, 18}` (`0x002B8D84..0x002B8DB0`)**
   - Calls `0x002AF854(object + 0xC4, 2, 0)`.
   - Calls `0x002AF854(object + 0x1DC, 2, 0)`.
   - Restores `{r4, r5, r6, lr}` and tail-branches (`b #0x1384f0`) with `r0 = object + 0x150`, `r1 = 0`.
   - **Writes / return**: Sequential `0x002AF854` updates on subobjects `+0xC4` and `+0x1DC`, followed by `0x001384F0` writing `0` to `*(uint8_t*)(object + 0x1D5)` (`(object + 0x150) + 0x85`). Returns `r0 = object + 0x150`.
4. **`selector == 6` (`0x002B8DB4..0x002B8DD8`)**
   - Forms `r0 = object + 0xC4`, executes `vldr s0, [r0, #0x20]` (reads `*(uint32_t*)(object + 0xE4)`), `vmov r0, s0`, `cmp r0, #0x3f800000`.
   - If `!= 0x3F800000` (1.0f): branches to `0x002B8D34` (`pop {r4, r5, r6, pc}`). No writes, no calls; returns `r0 = *(uint32_t*)(object + 0xE4)` and leaves `s0` holding that same 32-bit word.
   - If `== 0x3F800000`: restores `{r4, r5, r6, lr}` and tail-branches `0x002AF854(object + 0xC4, 2, 0)`; returns `r0 = object + 0xC4`.
5. **`selector in {7, 8, 9}` (`0x002B8DDC..0x002B8E00`)**
   - Calls `0x002AF854(object + 0xC4, 2, 0)`.
   - Restores `{r4, r5, r6, lr}` and tail-branches `0x002AF854(object + 0x40C, 2, 0)`.
   - **Writes / return**: Sequential `0x002AF854` updates on `+0xC4` then `+0x40C`; returns `r0 = object + 0x40C`.
6. **`selector == 11` (`0x002B8E18..0x002B8E3C`)**
   - Calls `0x002BF030(object + 0xC4, 7)`.
   - Calls `0x002BF030(object + 0x268, 7)`.
   - Restores `{r4, r5, r6, lr}` and tail-branches `0x001384F0(object + 0x380, 0)`.
   - **Writes / return**: Effects of both `0x002BF030` calls plus `*(uint8_t*)(object + 0x405) = 0` (`(object + 0x380) + 0x85`); returns `r0 = object + 0x380`.
7. **`selector == 12` (`0x002B8E40..0x002B8E88`)**
   - Loops `r4 = 0..4`: reads `*(uint8_t*)(object + 0x37 + r4)`. If nonzero, computes `r0 = object + 0x498 + r4 * 140` (`rsb r0, r4, r4, lsl #3` = `7*r4`; `add r0, r0, r0, lsl #2` = `35*r4`; `lsl #2` = `140*r4`) and calls `0x002AF854(r0, 5, 0)`.
   - After the loop: `mov r0, #0; str r0, [r5, #0x28]; pop {r4, r5, r6, pc}`.
   - **Writes / return**: Zero to five `0x002AF854(..., 5, 0)` calls in ascending `i` order, then `*(uint32_t*)(object + 0x28) = 0`; returns `r0 = 0`.

## Pointer preconditions and ABI notes

- Neither `0x002B8D24` nor its direct callees (`0x002AF854`, `0x001384F0`, `0x002BF030`) null-check `object` or subobject pointers.
- Required valid mapped/aligned memory depends on `selector`:
  - `0, 13..15, >=19`: no memory dereferences.
  - `6`: readable 4-byte aligned `object + 0xE4` and VFP enabled (`FPEXC.EN = 1`) for original `vldr s0`; if `0x3F800000`, `object + 0xC4` valid for `0x002AF854`.
  - `1, 10`: `object + 0xC4` valid for `0x002AF854(..., 2, 0)`.
  - `2..5, 16..18`: `object + 0xC4` and `object + 0x1DC` valid for `0x002AF854(..., 2, 0)`, plus writable `object + 0x1D5`.
  - `7..9`: `object + 0xC4` and `object + 0x40C` valid for `0x002AF854(..., 2, 0)`.
  - `11`: `object + 0xC4` and `object + 0x268` valid for `0x002BF030(..., 7)`, plus writable `object + 0x405`.
  - `12`: readable bytes `object + 0x37..0x3B`, writable 4-byte aligned `object + 0x28`, and for each nonzero `object[0x37 + i]`, `object + 0x498 + i * 140` valid for `0x002AF854(..., 5, 0)`.

## Direct facts vs. unresolved helper effects

- **Directly verified**:
  - All 19 jump-table entries and `>= 19` fallback of `0x002B8D24`.
  - `0x001384F0` is an 8-byte leaf (`strb r1, [r0, #0x85]; bx lr`) returning `r0` unchanged.
  - `0x002AF854` contract is separately established and verified.
  - Existing C++ `battle_func_002b8d24` in `src/engine/leaf_batch46_a.cpp:539-575` already mirrors all 19 cases and `>= 19` fallback, except:
    1. On `selector == 6` (`!= 0x3F800000`), C++ loads `uint32_t` without `vldr s0`, so `s0` is not updated as in original.
    2. C++ currently calls hardcoded literal addresses (`0x002af854`, `0x002bf030`, `0x001384f0`) rather than relocatable extern symbols.
- **Unresolved by this static recon**:
  - Full runtime behavior of `0x002BF030` (`camp_func_002bf030`) and its downstream callee `0x00138934` (invoked on `selector == 11`).
  - Whether any caller of `0x002B8D24` with `selector == 6` consumes `s0` after return.
  - Cross-subobject alias layouts for `selector == 11` and multi-call `selector == 12` chains beyond the already tested `0x002AF854` index-2 and five-call fixtures.

## Conversion decision

`battle_func_002b8d24` in `src/engine/leaf_batch46_a.cpp` is structurally complete for all selector branches. Before promoting a full C++ conversion:
1. Audit whether any caller of `0x002B8D24` (`selector == 6`) reads `s0`.
2. Replace hardcoded callee addresses with relocatable extern declarations (or verify staging/relocation) and run differential + caller-composition tests covering all selector classes (`0`, `1/10`, `2..5/16..18`, `6` both branches, `7..9`, `11`, `12`, `13..15`, `>=19`).
