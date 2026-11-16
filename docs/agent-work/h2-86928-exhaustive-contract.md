# `0x00286928` (`engine_func_00286928`) — exhaustive static contract

## 1. Identity & frozen pins

- Static ARM instruction and caller audit only (`compiler_slots: 0`); no production source, ledger, runner, image, board, or emulator edits.
- Verified `13/13` `input_sha256` pins in `build/agent-work/H2-semantic/h2-helper-00286928-exhaustive-contract/run-001/task.json` (`extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `config/functions.csv`: `0x00286928`, `820` bytes (`0x00286928..0x00286C5B`), `non_matching`, `engine`, `engine_func_00286928`, `src/engine/leaf_batch45_a.cpp`.

## 2. Raw 6-argument ABI & selector dispatch (`0x00286928..0x002869B8`)

- **Raw ABI:** `(r0 = raw_r0, r1 = raw_r1, r2 = incoming_r2, r3 = raw_selector, [SP] = arg5, [SP+4] = arg6)` -> returns `uint32_t` (`0` or `1`) in `r0`. Saves `{r0..r11, lr}` and `vpush {d8}` (`FPEXC.EN` required), allocates `0x0C` bytes on stack (`[SP+0..0x0B]` for 3 stack arguments to `0x0028E974`), preserves `r4..r11`, `d8`, and `SP`.
- **Table & selector normalization (`0x0043E188`):**
  - `default_object = *(u32*)0x0043E18C` (`table[1]`).
  - `raw_selector in {11, 13, 14, 15, 19}` -> `object = table[2]` (`0x0043E190`); `{11, 13, 14, 15}` normalize `selector = 11`, while `19` stays `19`.
  - `raw_selector == 12` -> `object = table[3]` (`0x0043E194`), `selector = 12`.
  - All other selectors -> `object = default_object`, `selector = raw_selector`.
- **Prewrites (always executed in order):**
  1. `*(u8*)(object + 0x2D) = (raw_selector == 13 || raw_selector == 15) ? 1 : 0`.
  2. `*(u8*)(object + 0x5E) = (raw_selector == 11 || raw_selector == 13) ? 1 : 0`.

## 3. Exhaustive branch & memory-effect enumeration

### A. `incoming_r2 != 0` branch (`0x002869BC..0x00286A24`, `0x00286B9C..0x00286C4C`)

- **`object[8] == 4`:** Returns `1` immediately; no further writes or calls.
- **`object[8] == 5`:** Calls `0x0028DF54(*(u32*)(object + 0x18))`, returns `1`.
- **`object[8] == 0`:**
  - If `object[0x2E] == 0`:
    - If `selector in {11, 19}`: if `default_object != nullptr && default_object[8] != 0`, returns `0`; else calls `0x0028DF54(*(u32*)(object + 0x18))`, `0x0028DF3C(0xFFFFFFFF)`, `0x0028DF0C(0)` in order, then returns `1`.
    - Else (`selector not in {11, 19}`): returns `1`.
  - If `object[0x2E] != 0`: writes `object[0x2E] = 0`, calls `0x0028E974(object, raw_r0, raw_r1, selector, 0x1A, 1, 0)`, if `object[0x35] == 0` calls `0x0028DF98(object, object[9])`, returns `0`.
- **`object[8] not in {0, 4, 5}`:**
  - Calls `0x002C1F28()`; if `0`, returns `0`.
  - Calls `0x002B89A0()`; if `0`, returns `0`.
  - Re-reads `state = object[8]`; if `state == 3 || state == 0`, returns `0`.
  - Calls `0x002B8D24(object, object[9])`, writes `object[8] = 3` and `object[0x35] = 0`, returns `0`.

### B. `incoming_r2 == 0` branch (`0x00286A4C..0x00286B98`)

- **Flag write:** If `raw_selector in {11, 13}`, writes `object[0x5F] = 1` and `default_object[0x5F] = 1`.
- **Common writes:** `object[0x36] = (u8)arg5`; `*(u32*)(object + 0x10) = (selector == 6 ? 0x035AB9FF : 0x320202FF)`.
- **`object[8] != 0`:** Writes `object[0x2E] = 1`, calls `0x002B8D24(object, object[9])`, writes `object[8] = 3` and `object[0x35] = 0`, returns `0`.
- **`object[8] == 0`:**
  - Calls `0x002C1F28()`; if nonzero, calls `0x002B89A0()`; if nonzero, returns `1`.
  - Calls `0x0028E974(object, raw_r0, raw_r1, selector, 0x1A, 1, arg6)`.
  - If `selector in {11, 19}`: `*(u32*)(object + 0x20) = 0x002B787C(*(u32*)(object + 4))`.
  - If `object[0x35] == 0`: calls `0x0028DF98(object, object[9])`.
  - If `arg5 != 0`: calls `0x002C4BF0(*(u32*)(object + 4), 0x20)` and `0x002B90F0(*(u32*)(object + 4), 0x40)`.
  - Writes `object[0xA12] = 0`, then loops `i = 0..5`: `object[0xA13 + i] = (u8)0x002F5B2C(i)`, `*(u16*)(object + 0xA1A + 2*i) = (u16)0x002D65B4(i)`.
  - Re-reads `row = object[9]`; if `row in {7, 8, 9}` and `0x0028DF70(0) == 5`: writes `object[0xA26] = 1`, `object[0xA12] = (u8)0x002B8CCC()`, calls `0x002B8B78(0xDC)`.
  - If `selector == 19`: calls `0x002B8584(1)`.
  - Returns `0`.

### C. Path-local vs unknown callee effects

- All 17 unique direct callees (22 `BL` sites) are external to `0x00286928`: `0x002C1F28`, `0x002B89A0`, `0x002B8D24`, `0x0028E974`, `0x002B787C`, `0x0028DF98`, `0x002C4BF0`, `0x002B90F0`, `0x002F5B2C`, `0x002D65B4`, `0x0028DF70`, `0x002B8CCC`, `0x002B8B78`, `0x002B8584`, `0x0028DF54`, `0x0028DF3C`, `0x0028DF0C`. Their internal side effects depend on their own contracts/implementations.

## 4. Complete C++ feasibility & validation plan

- **820-byte slot & rejection of partial fast paths:** Partial fast-path replacements are **rejected** because `r2 == 0` and all `r2 != 0` / selector branches are reachable from callers. Full editable C++ (`engine_func_00286928` at `src/engine/leaf_batch45_a.cpp:12726-12830`) covers every branch above and fits within the 820-byte original slot without fallback.
- **Full-domain offline differential & caller plan:**
  - Compile with `arm-none-eabi` / Clang ARMv6K (`-Os`/`minsize`), verify `<= 820` bytes and 22 even ARM `R_ARM_CALL` relocations (`thumb == False`).
  - Cover all selectors (`6, 11, 12, 13, 14, 15, 19, default`), `r2 in {0, 1, 0xffffffff}`, `object[8] in {0, 3, 4, 5, 1}`, `object[0x2E] in {0, 1}`, `object[0x35] in {0, 1}`, `arg5 in {0, 1}`, `row in {6, 7, 8, 9, 10}`, `0x002C1F28`/`0x002B89A0`/`0x0028DF70` return combinations, and `r4..r11`/`d8`/`SP`/ordered write-trace parity with `FPEXC.EN` set.
  - Mutation controls: omitted `+0x2D`/`+0x5E`/`+0x5F` prewrites, wrong selector table slot, wrong `r2==0` `object+0x10` literal, wrong `0x002F5B2C`/`0x002D65B4` loop bound, and dropped `0x0028DF54` call.
  - Real caller composition: compose through `0x00221168` (`selector=6`, `arg5=1`, `arg6=0`) without asserting uncaptured runtime causes.
