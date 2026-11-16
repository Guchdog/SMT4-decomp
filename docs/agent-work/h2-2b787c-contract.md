# `0x002B787C` (`AsdText_GetLineCount` / `engine_func_002b787c`) — bounded static contract

## 1. Identity & frozen pins

- Static pinned-image/source audit only (`compiler_slots: 0`); no implementation, runner, build, or emulator changes.
- Verified `16/16` `input_sha256` pins in `build/agent-work/H2-semantic/h2-asdtext-line-count-contract/run-001/task.json` (`extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `config/functions.csv`:
  - `0x002b787c`: `176` bytes, `non_matching`, `engine`, `engine_func_002b787c`, `src/engine/leaf_batch42_c.cpp`
  - `0x002ae6b0`: `24` bytes, `non_matching`, `engine`, `engine_func_002ae6b0`, `src/engine/leaf_matching.cpp`
  - `0x002ae664`: `76` bytes, `non_matching`, `unknown`, `func_002ae664`, `src/engine/leaf_batch28_b.cpp`

## 2. Disassembled ARM paths, ABI, and memory effects (`0x002B787C`, 176 bytes)

Disassembled `0x002B787C..0x002B792B` from `extracted/exefs/code.bin` (literal `0x0000FFFF` at `0x002B7928`):

- **Raw ABI:** Takes `r0 = raw_handle`, returns `uint32_t` line count in `r0`. Saves `{r4, r5, r6, r7, r8, lr}`, allocates no stack locals, performs **zero memory writes**, and preserves `r4..r8` and `SP`.
- **Gate & initialization:** Reads `*(uint32_t*)(handle + 0x14)`; if `0`, returns `0` immediately. Otherwise sets `count = 0`, `index = *(uint32_t*)(handle + 0x0C)`, `sentinel = 0xFFFF`.
- **32-byte-stride record loop (`0x002B78A0..0x002B7908`):**
  1. Re-reads `table_base = *(uint32_t*)(handle + 0)` and loads `code = *(uint16_t*)(table_base + (index << 5))`.
  2. If `code == 0xFFFF`, returns `count`.
  3. Calls `0x002AE6B0(code)` (`engine_func_002ae6b0`):
     - If `0`: skips control-code dispatch.
     - If nonzero (`0xF801..0xF88F`):
       - `0xF801` (`(code - 0xF800) - 1 == 0`): `count += 1`.
       - `0xF802` (`== 1`): returns `count` immediately.
       - `0xF81A` (`== 0x19`): increments `index += 1`, re-reads `table_base = *(uint32_t*)handle`, sets `count = *(uint16_t*)(table_base + (index << 5))` (overwrites running count).
       - Otherwise: calls `0x002AE664(code)` (`func_002ae664`) and adds `r0` to `index` (`index += r0`).
  4. Increments `index += 1`, re-reads `start = *(uint32_t*)(handle + 0x0C)`, computes `limit = start + 0x3E7` (`999`), and loops while `(int32_t)limit > (int32_t)index` (`bgt`); otherwise returns `count`.

## 3. Direct callees (`0x002AE6B0` and `0x002AE664`)

- `0x002AE6B0` (24B leaf): computes `(uint32_t)(code - 0xF801) < 0x8F ? 1 : 0` (`0xF801..0xF88F`), no memory reads/writes, no callees.
- `0x002AE664` (76B leaf): scans a 16-byte-stride table in ROM/RAM for `hword == code` until the sentinel halfword (`cmp r3, ip`), returning `*(uint32_t*)(entry + 4)` (parameter skip count) or `0` on sentinel. No memory writes, no callees; table contents beyond the sentinel/skip-count contract are separate from `0x002B787C`'s traversal logic.

## 4. Direct callers & assumptions

Word-aligned ARM `BL` scan of `extracted/exefs/code.bin` found 3 direct callers:

1. `0x00286AD0` in `engine_func_00286928` (`src/engine/leaf_batch45_a.cpp:12805`): on `selector == 11 || selector == 19`, calls `engine_func_002b787c(*(volatile uint32_t*)(object + 4))` and stores `r0` into `*(volatile uint32_t*)(object + 0x20)`. Assumes `*(object + 4)` is a valid non-null handle pointer.
2. `0x002CF5F0` in `StatusDown_UpdateHelpMessage` (`src/ui/status_down.cpp:1072`): calls `AsdText_GetLineCount(work->text_handle)` and passes the `s32` return `line_count` to `UiListCursor_Setup(&work->list_cursor_help, line_count, 8, 1, 0, 1)`.
3. `0x001173F0` in `ui_func_00116954` (`src/engine/leaf_batch44_a.cpp`).

## 5. Unresolved assumptions & limits

- No null check on `handle` (`r0`) or `table_base` (`*(handle + 0)`) when `*(handle + 0x14) != 0`; invalid pointers fault.
- `index` and `start + 0x3E7` use signed `bgt` comparison; signed overflow of `start + 0x3E7` or `index + skip` is outside the normal positive-index domain.
- `0xF81A` assumes `index + 1` points to a readable 32-byte record.
- `src/engine/leaf_batch42_c.cpp:468-508` already contains a typed C++ body for `engine_func_002b787c`; this static contract does not run a compiler, differential, or emulator check.
