# Independent Review: `0x002AF854` (`battle_func_002af854`) Production Contract & Composition

## Verdict

**Disposition:** **Accept** the production C++ reconstruction `battle_func_002af854` (`src/engine/leaf_batch13_a.cpp:119-135`) for its documented ordinary-RAM domain and offline `0x002B8D24` index-2 composition.

This review does not claim live Azahar runtime equivalence or cross-TU LTO type unification.

## 1. Contract & Production Object Verification

- **Inputs & pointer return**: `uint8_t* battle_func_002af854(uint8_t* object, uint32_t index, uint32_t mode)` returns `object` in `r0` on both the null-list and non-null paths.
- **Null branch**: Reads `list = *(const uint32_t* const*)(object + 0x58)`. If `list == nullptr`, returns `object` immediately (`bxeq lr`) with zero memory writes.
- **Field writes & order**: Writes `static_cast<uint16_t>(index)` to `+0x5c`, `0` (`u16`) to `+0x5e`, `0` (`u8`) to `+0x87`, `0` (`u8`) to `+0x8a`, and `static_cast<uint8_t>(mode)` to `+0x60` (all `volatile` to preserve exact original store order ahead of the list read), then writes `selected` (`u32`) to `+0x20`.
- **List indexing**: Reads `*(const volatile uint32_t*)(reinterpret_cast<const uint8_t*>(list) + index * 12u + (mode != 0 ? 4 : 0))` (full 32-bit `mode != 0` test, even when `(mode & 0xFF) == 0`, e.g. `0x100`).
- **Production object & ledger**: `battle_func_002af854` in `build/agent-work/H2-semantic/h2-helper-002af854-alias-coverage/001/production/engine/leaf_batch13_a.o` (SHA-256 `06a038ddcec0acffbf0b49de94125217bb06eb0ed9256ebeb8e6a3127021e162`) is 64 bytes with 0 relocations and byte-identical to `candidate_002af854` (`experiments/semantic_equivalence/h2_af854_candidate.cpp`, object SHA-256 `516c5aed72c5738989545c9a83a9897be7c4358fa907df34954c81e76326d19d`). `config/functions.csv:5359` truthfully marks `0x002af854` as `non_matching`.

## 2. Direct Differential, Alias Domain & Caller Evidence

- **No-alias & alias domains (`tools/h2_af854_experiment.py`, SHA-256 `567daa62...`)**: `503/503` direct cases match original `0x002AF854` across `r0`, `SP`, `r4-r11`, `0x100`-byte object, `0x1000`-byte list, and ordered `UC_HOOK_MEM_WRITE` events (`371` disjoint cases including null-list and `mode=0x100`, plus `132` alias overlaps at `+0x20/+0x58/+0x5c/+0x60/+0x84`).
- **Negative controls**: `4/4` functional mutants (`null`, `selection`, `index`, `return`) and the `mutant_order` nonvolatile control are detected.
- **Callers**: `32` disjoint + `32` cross-alias `0x002B8D24` index-2 compositions pass against original, candidate, and production with asserted callee tuples `[(obj+0xc4, 2, 0), (obj+0x1dc, 2, 0)]`.

## 3. Limits

- Assumes aligned, mapped, writable ordinary RAM and non-overflowing `index * 12`.
- Legacy `void` declarations in other TUs (`docs/function-records/0x002af854.md:11`) remain separate from `leaf_batch13_a.cpp`.
- No live Azahar runtime or H2 audio scenario execution was performed.
