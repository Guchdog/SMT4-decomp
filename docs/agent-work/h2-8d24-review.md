# Independent Review: `0x002B8D24` (`battle_func_002b8d24`) Selector Dispatcher

## Verdict

**Disposition:** **Accept** `battle_func_002b8d24` (`src/engine/leaf_batch46_a.cpp:539-575`) as **ready for production placement** within its documented ordinary-RAM domain and retaining original-address callees (`0x002AF854`, `0x002BF030`, `0x001384F0`).

This review does not claim arbitrary alias coverage beyond the tested selector-12 five-subobject chain, runtime reachability of `0x002B8D24` in H2, or whole-game equivalence.

## 1. Independent Disassembly & Contract Verification (`0x002B8D24`, 360 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x002B8D24..0x002B8E8C`:

- **Selector branches & jump table (`jt[0..18]` at `0x002B8D38..0x002B8D80`)**:
  - `0`, `13..15`, and `>= 19`: returns `object` (`r0`).
  - `1`, `10`: tail-calls `0x002AF854(object + 0xc4, 2, 0)`, returning its `r0`.
  - `2..5`, `16..18`: calls `0x002AF854(object + 0xc4, 2, 0)`, `0x002AF854(object + 0x1dc, 2, 0)`, and tail-calls `0x001384F0(object + 0x150, 0)`.
  - `6`: reads `*(u32*)(object + 0xe4)` (via `vldr s0` + `vmov r0, s0` in original). If `!= 0x3F800000`, returns the raw 32-bit word in `r0` (original also leaves it in `s0`; C++ `uint32_t` read does not update `s0`); if `== 0x3F800000`, tail-calls `0x002AF854(object + 0xc4, 2, 0)`.
  - `7..9`: calls `0x002AF854(object + 0xc4, 2, 0)`, tail-calls `0x002AF854(object + 0x40c, 2, 0)`.
  - `11`: calls `0x002BF030(object + 0xc4, 7)`, `0x002BF030(object + 0x268, 7)`, tail-calls `0x001384F0(object + 0x380, 0)`.
  - `12`: loops `i = 0..4`; if `object[0x37 + i] != 0`, calls `0x002AF854(object + 0x498 + i * 140, 5, 0)` (verified `7 * 5 * 4 = 140` byte stride); clears `*(u32*)(object + 0x28) = 0`; returns `0`.
- **VFP/CPSR & real caller use**: Original has no VFP callee-saved spills (`d8-d15` untouched) and leaves no documented CPSR flag dependency across its 13 statically audited direct `BL` callers (`docs/function-records/0x002b8d24.md:7`).

## 2. Candidate/Preview Identity, Differential Matrix & Controls

- **356-byte identity**: `battle_func_002b8d24` in `build/agent-work/H2-semantic/h2-helper-002b8d24-convert/run-001/production/engine/leaf_batch46_a.o` (`97e5d7a9fd8ef7f325addb9c93f142f8ac103493385fae4a10fe5188254cde58`) is `356` bytes (`<= 360`), `0` relocations, and byte-identical to `candidate_002b8d24` (`candidate-final.o`). `src/engine/leaf_batch46_a.cpp` (`988c31ce...`) matches `production-preview.cpp` (`988c31ce...`). `config/functions.csv:5535` truthfully marks `0x002b8d24` as `non_matching`.
- **Differential & controls (`tools/h2_8d24_experiment.py`, SHA-256 `7d8132d7...`)**:
  - `116` direct cases (`2` seeds x `[0..19, 0x80000000, 0xffffffff]`, `6` selector-6 float bit patterns, `32` selector-12 5-bit masks) comparing `r0`, `SP`, `r4-r11`, `0x1200`-byte object, callee event trace, and ordered `UC_HOOK_MEM_WRITE` writes.
  - `2` original `0x00286928` selector-11 compositions (`seeds 17, 4729`).
  - `2` five-call selector-12 cross-alias chains with `candidate_002af854` (`[0x12345678, 5, 5, 5, 5]`).
  - `7/7` compiled negative controls detected (`return6`, `second`, `stride`, `loop_limit`, `selector`, `tail_byte`, `clear`).

## 3. VM, Caller & Runtime Domain Limits

- Valid, aligned, non-overflowing pointers in mapped ordinary RAM only (no invalid-address fault parity, MMIO, or concurrent mutation).
- Hardcoded absolute callee pointers (`0x002AF854`, `0x002BF030`, `0x001384F0`, all even ARM targets) bypass C++ symbol linkage if those targets move out of slot.
- `s0` is not updated on selector 6 (`!= 0x3F800000`); safe for the 13 statically audited direct callers that ignore return/VFP state, but not if an unknown indirect caller reads `s0`.
- Offline composition covers `0x00286928` selector 11 and one 5-subobject selector-12 chain; live Azahar reachability of `0x002B8D24` and full H2 readiness/persistence remain unverified.
