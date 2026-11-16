# `0x002AA268` (`camp_func_002aa268`) — bounded static contract

## 1. Identity & frozen pins

- Pinned static audit and caller search only (`compiler_slots: 0`); no source, ledger, README, milestone, compile, or emulator changes.
- Verified `12/12` `input_sha256` pins in `build/agent-work/H2-semantic/h2-profile-record-copy-contract-002aa268/run-001/task.json` (`extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `config/functions.csv`: `0x002aa268`, `72` bytes, `non_matching`, `camp`, `camp_func_002aa268`, `src/engine/leaf_batch13_b.cpp` (existing C++ at lines `28-51`).

## 2. Disassembled 72-byte ARM body (`0x002AA268..0x002AA2AF`)

- **ABI & prologue:** `u32 camp_func_002aa268(u8* record, u32 index, u32 selector)` (`r0 = record`, `r1 = index`, `r2 = selector`), returns `r0 = record`. Leaf function, no stack frame, no VFP, preserves `r4..r11` and `SP`.
- **Null-table guard:** Reads `table = *(u32*)(record + 0x64)`. If `table == 0`, returns `record` (`r0`) without writes.
- **Ordered metadata writes:**
  1. `*(u16*)(record + 0x68) = (u16)index`
  2. `*(u16*)(record + 0x6A) = 0`
  3. `*(u8*)(record + 0x88) = 0`
  4. `*(u8*)(record + 0x8A) = 0`
  5. `*(u8*)(record + 0x6C) = (u8)selector`
- **Full-width addressing & ordered output writes:**
  - Computes `entry = table + index * 12u` using **full 32-bit `index`** (not truncated `(u16)index`).
  - Tests **full 32-bit `selector == 0`**: loads `selected = *(u32*)(entry + (selector == 0 ? 0 : 4))`.
  - Writes `selected` in order to `*(u32*)(record + 0x24)`, `*(u32*)(record + 0x28)`, and `*(u32*)(record + 0x2C)`, then returns `record`.

## 3. H2 caller mapping & comparison with `0x002BDAC0`

- Word-aligned ARM `BL` scan of `extracted/exefs/code.bin` found `13` direct callers, including H2 site `0x002B86FC` inside `ui_func_002b85bc` (`0x002B85BC`'s 2-slot loop `j = 0..1` when `O[0x4C8] != 1`, passing `(O + 0x37C + 0x8C * j, 0, 1)` and ignoring `r0`).
- **Comparison with `0x002BDAC0` (distinct semantics):**
  - `0x002BDAC0` reads `record+0x4C`, writes `+0x50/+0x52/+0x86/+0x8A/+0x54`, loads two `s16`s (`0/2` or `4/6`), scales each by `4096` mod `2^32`, and writes `+0x0C` then `+0x10`.
  - `0x002AA268` reads `record+0x64`, writes `+0x68/+0x6A/+0x88/+0x8A/+0x6C`, loads one unscaled `u32` (`+0` or `+4`), and writes it to `+0x24`, `+0x28`, `+0x2C`.
  - Both share 12-byte stride, full-width `index`/`selector` semantics, `volatile` ordering for aliasing, and `r0 = record` return.

## 4. Bounded typed-C++ & differential plan

- `camp_func_002aa268` (`src/engine/leaf_batch13_b.cpp:28-51`) already implements the `volatile`-ordered C++ contract.
- Differential plan: test null `record+0x64`, full-width `index` (`0x10000` vs `0`), full-width `selector` (`0, 1, 0x100`), self-aliasing (`table == record + 0x68 - index * 12`), mutation controls (`u16`-truncated index, byte-only selector, omitted `+0x28` store, non-volatile aliasing), `<= 72B` slot, `0` relocs, and `0x002B85BC` (`0x002B86FC`) caller composition.
- **Limits:** Valid aligned ordinary RAM for `record` and `table` assumed; unmapped/invalid pointers, concurrent mutation, and live runtime behavior remain out of scope.
