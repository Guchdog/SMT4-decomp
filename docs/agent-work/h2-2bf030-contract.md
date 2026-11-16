# `0x002BF030` H2 sentinel-table selector & `0x00138934` service — bounded static contract

## 1. Identity & frozen pins

- Static ARM disassembly/source inspection only (`compiler_slots: 0`); no build, runner, or emulator was run.
- Verified `9/9` `input_sha256` pins in `build/agent-work/H2-semantic/h2-helper-002bf030-contract/run-001/task.json` (`extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `src/engine/leaf_batch41_b.cpp:1283-1307` contains `camp_func_002bf030`; `src/engine/leaf_batch28_a.cpp:6650-6651` contains `camp_func_00138940` (388B, preceded by 12B wrapper at `0x00138934`).

## 2. `0x002BF030` (120 bytes): literals, pointer graph, loop, and ABI

Disassembled `0x002BF030..0x002BF0A7` from `extracted/exefs/code.bin`:

- **Fixed literals:** `0x00009249` at `0x002BF0A4`; unconditional tail branch `b #0x138934` at `0x002BF0A0`. No fixed global addresses are read directly by `0x002BF030`.
- **Raw ABI:** Takes `(r0 = object, r1 = selector)`, saves `{r4, r5}` (restores before tail branch), allocates no stack, writes no memory itself, and tail-calls `0x00138934(object, selected)`, returning `0x00138934`'s raw `r0`.
- **Pointer graph & loop bounds:**
  1. Reads `manager = *(uint8_t**)(object + 0x48)` and `n = *(uint16_t*)(manager + 8)` (no null checks).
  2. Computes `count = ((uint32_t)n * 0x9249u + 0x9249u) >> 20` (exact `n / 28` for all `uint16_t` `0..65535`).
  3. If `count == 0`, sets `selected = nullptr` (`r1 = 0`).
  4. Else reads `table = *(uint8_t**)(manager + 0x1C)` and scans `i = 0..count-1` with 28-byte stride (`table + i * 28`): checks `markers == selector` *before* reading `*(uint32_t*)entry`; on match, sets `selected = entry` and breaks; otherwise increments `markers` if `*(uint32_t*)entry == 0xFFFFFFFFu`. If unmatched, `selected = nullptr`.

## 3. `0x00138934` service behavior (400 bytes: `0x00138934..0x00138AC3`)

Disassembled `0x00138934..0x00138AC3` from `extracted/exefs/code.bin`:

- **Null `selected` fast path (`0x00138934..0x0013893C`):** Unconditionally stores `*(object + 0x78) = selected`; if `selected == nullptr`, returns immediately (`bxeq lr`) with `r0 = object`.
- **Non-null `selected` path (`0x00138940..0x00138AC0`):** Saves `{r4, r5, lr}` (`r4 = object`, `r5 = 0`):
  - Zeroes `object+0x7C/+0x7E/+0x80/+0x82` (`u16`s) and sets `object+0x84 = 1` (`u8`).
  - **Field `+0/+4`:** If `*(s32*)(selected + 0) > -1`, calls `0x002BDAC0(object, (s16)*(s32*)(selected + 0), *(s8*)(selected + 4))`.
  - **Field `+0x0C/+0x10`:** Re-reads `selected = *(object + 0x78)`. If `w = *(s32*)(selected + 0x0C) > -1` and `list1 = *(object + 0x58) != 0`, writes `object+0x5C = (s16)w`, `object+0x5E = 0`, `object+0x87 = 0`, `object+0x8A = 0`, `mode = *(s8*)(selected + 0x10)`, `object+0x60 = mode`, and `*(u32*)(object + 0x20) = *(u32*)(list1 + (s16)w * 12 + (mode != 0 ? 4 : 0))`.
  - **Field `+0x14/+0x18`:** Re-reads `selected = *(object + 0x78)`. If `w = *(s32*)(selected + 0x14) > -1` and `list2 = *(object + 0x64) != 0`, writes `object+0x68 = (s16)w`, `object+0x6A = 0`, `object+0x88 = 0`, `object+0x8A = 0`, `mode = *(s8*)(selected + 0x18)`, `object+0x6C = mode`, and writes `*(u32*)(list2 + (s16)w * 12 + (mode != 0 ? 4 : 0))` to `object+0x24`, `object+0x28`, and `object+0x2C`.
  - **Field `+8` (secondary 4-byte-stride table):** Re-reads `selected = *(object + 0x78)`. If `w = *(s32*)(selected + 8) > -1`, reads `manager = *(object + 0x48)`, `count2 = *(u16*)(manager + 6) >> 2`, `table2 = *(manager + 0x18)`, and scans 4-byte-stride entries matching `markers == (s16)w` before counting `*(s16*)entry == -1`. Stores matched pointer (or `0`) to `object+0x70`. If non-null, zeroes `object+0x74/+0x76` (`u16`s), `object+0x89/+0x8A` (`u8`s), reads `val = *(s16*)entry2`, writes `object+4 = val` and `object+8 = -1` (`strd`), and returns `val`.
- **Observed raw `r0` returns:** `object` pointer (`selected == nullptr`), negative word (`*(s32*)(selected + 8) <= -1`), `0` (secondary scan miss), or sign-extended `*(s16*)entry2` (secondary scan hit).

## 4. Valid RAM domain & unresolved effects

- **Valid domain:** Readable/writable aligned ordinary RAM for `object` (through `+0x8A`), `manager` (`+6`, `+8`, `+0x18`, `+0x1C`), `table` (`count * 28` bytes), `table2` (`count2 * 4` bytes), and `list1`/`list2` when non-null.
- **Unresolved effects:** Deeper behavior of `0x002BDAC0` when `*(s32*)(selected + 0) > -1`, aliasing between `object`/`manager`/`table`, null/invalid pointer faults, and live H2 runtime behavior remain outside this static contract.
