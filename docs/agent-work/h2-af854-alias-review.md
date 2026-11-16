# Independent Review: `0x002AF854` (`battle_func_002af854`) Alias-Aware Ordering & Caller Composition

## Verdict

**Disposition:** **Accept** the alias-aware `battle_func_002af854` production body (`src/engine/leaf_batch13_a.cpp:119-135`) and its offline differential, alias-ordering control, and `0x002B8D24` index-2 caller-composition evidence. **Yes**, it supports `0x002B8D24`'s documented ordinary-RAM domain (valid aligned writable subobjects and mapped list arrays without pointer wraparound).

This review does not claim thread synchronization, MMIO semantics, arbitrary unmapped-pointer fault parity, or live Azahar runtime equivalence.

## 1. Independent Disassembly & Volatile Ordering Verification

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x002AF854..0x002AF894` (64 bytes) and compared against the compiled 64-byte bodies in:
- `build/agent-work/H2-semantic/h2-helper-002af854-alias-coverage/001/production/engine/leaf_batch13_a.o` (`battle_func_002af854`, SHA-256 `06a038ddcec0acffbf0b49de94125217bb06eb0ed9256ebeb8e6a3127021e162`)
- `build/agent-work/H2-semantic/h2-helper-002af854-alias-caller-coverage/001/candidate.o` (`candidate_002af854`, SHA-256 `516c5aed72c5738989545c9a83a9897be7c4358fa907df34954c81e76326d19d`)

- **Candidate/production identity**: Both 64-byte machine-code bodies are byte-for-byte identical (`0` relocations).
- **Alias counterexample & exact volatile ordering**: Without `volatile`, the compiler can hoist the list-element load ahead of the object stores; for `list = object + 0x5c`, `index = 0`, `mode = 0`, that reads stale memory instead of the newly written `((uint32_t)0 << 16) | (uint16_t)index`. Using `volatile` on the five stores (`+0x5c`, `+0x5e`, `+0x87`, `+0x8a`, `+0x60`) and the selected-word load (`entry + (mode != 0 ? 4 : 0)`) produces the exact same 10-step memory-event sequence as the original:
  1. `ldr ip, [r0, #0x58]` (if `0`, `bxeq lr`)
  2. `strh r1, [r0, #0x5c]`
  3. `strh r1, [r0, #0x5e]` (`r1 = 0`)
  4. `strb r1, [r0, #0x87]`
  5. `strb r1, [r0, #0x8a]`
  6. `strb r2, [r0, #0x60]`
  7. `ldr r1, [r3]` (`r3 = ip + index * 12 + (mode != 0 ? 4 : 0)`)
  8. `str r1, [r0, #0x20]`
- **Mutated nonvolatile control**: `tools/h2_af854_experiment.py:181-187` strips `volatile` from those six accesses and confirms `order_ref != order_got` and a different `+0x20` selected word on `(seed=0, is_null=False, index=0, mode=0, alias=0x5c)`.

## 2. Exact Tested Alias Set & Caller Evidence

Inspected `tools/h2_af854_experiment.py` (SHA-256 `567daa627d1dfb373d20b8ad63b0f3d0bb9c07f719437ef98d9ea5bef6ee10c1`) and `build/agent-work/H2-semantic/h2-helper-002af854-alias-caller-coverage/001/offline-output.txt`:

- **503/503 direct cases** (original vs candidate vs production), including **132 alias overlaps**:
  - **60 index-0 cases**: seeds `{0, 17, 4729}` x offsets `{+0x20, +0x58, +0x5c, +0x60, +0x84}` x modes `{0, 1, 0x100, 0xffffffff}`.
  - **72 index-2 and index-5 cases**: seeds `{0, 17, 4729}` x indices `{2, 5}` x selected-word offsets `{+0x5c, +0x60, +0x84}` x modes `{0, 1, 0x100, 0xffffffff}` (`list = object + selected_offset - index * 12`).
- **4/4 functional mutants + alias-order mutant detected**: `null`, `selection`, `index`, `return`, and `mutant_order`.
- **0x002B8D24 index-2 caller composition**: `32` disjoint + `32` cross-alias seeds (`obj+0xc4+0x58 -> obj+0x1dc+0x5c-24`, `obj+0x1dc+0x58 -> obj+0xc4+0x5c-24`), asserting both callee entry tuples `[(obj+0xc4, 2, 0), (obj+0x1dc, 2, 0)]`, matching `r0`, `SP`, `r4-r11`, `0x500`-byte object, `list1`/`list2`, ordered `writes`, and `*(obj+0x1dc+0x20) == 2` in cross-alias mode.

## 3. ABI & Domain Limitations

- Touches `r0-r3, ip` only; no stack frame, no VFP/NEON instructions, preserves `r4-r11` and `SP` (`d8-d15` not explicitly sampled by `run_direct`/`run_real_caller`, though absent from disassembly).
- `src/engine/leaf_batch13_a.cpp:119` uses `uint8_t* battle_func_002af854(uint8_t*, uint32_t, uint32_t)`, whereas `docs/function-records/0x002af854.md:11` notes legacy `void` declarations in other TUs; cross-TU declaration cleanup/LTO remains separate.
- Tested domain assumes valid aligned writable ordinary RAM and non-overflowing `index * 12`; concurrency, MMIO, invalid-pointer faults, and live Azahar execution remain outside scope.
