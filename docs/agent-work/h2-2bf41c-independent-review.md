# Independent Review: `0x002BF41C` (`battle_func_002bf41c`) Task-Registry Lookup

## Verdict

**Disposition:** **Accept** the typed `u32(void*)` C++ reconstruction in `src/engine/leaf_batch32_c.cpp` (`battle_func_002bf41c`) and its bounded offline differential + `TitleConfig_IsReady` (`0x002FC0EC`) composition evidence, **with one provenance caveat**: `report.json` (`run001`) records `source_sha256` `f31e0469aae82b0e2bffacf9d4ad59647308257943dd28ec81f43781b685cff3`, whereas `src/engine/leaf_batch32_c.cpp` at HEAD `7e9db4d10fb1fa0a64fc4fa85875311c122f17a4` has SHA-256 `c793ee3c037bca075d7947d5a0bfcb95792795b3039a55bac0cb7a1b995e2fe5`.

This review does not claim whole-game or H2 runtime equivalence.

## 1. Independent Verification of Pinned Original Body (`0x002BF41C`, 68 bytes)

Inspected `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at file offset `0x001BF41C..0x001BF460`:

- **Registry global**: `0x002BF41C: ldr r1, [pc, #0x38]` loads literal `0x004E3CF4` from `0x002BF45C`, then `ldr r2, [r1]` dereferences the bucket table base.
- **Bucket index & table stride**: `0x002BF424: lsr r1, r0, #0x14` computes `handle >> 20` (4,096 buckets); `0x002BF428: ldr r1, [r2, r1, lsl #3]` indexes an 8-byte-stride table and reads the bucket head pointer at offset `+0`.
- **Node offsets**: `0x002BF434: ldr r2, [r1, #0x28]` reads the stored handle at `+0x28`; `0x002BF448: ldr r1, [r1, #0x4c]` advances to the next node at `+0x4C`.
- **Match / miss / null-handle behavior**:
  - Empty bucket (`node == 0`) or list exhaustion (`next == 0`) branches to `mov r0, #0; bx lr`.
  - First node with `node_handle == handle` returns `mov r0, #1; bx lr`.
  - Null handle (`r0 == 0`) is not special-cased: it selects bucket `0` (`0 >> 20 == 0`) and returns `1` if any node in bucket `0` stores `0` at `+0x28`, else `0`.
- **ABI**: Read-only; touches `r0-r2` only; no stack frame, no VFP/NEON instructions, preserves `r4-r11` and `SP`.

### Candidate & Ledger Check

- `src/engine/leaf_batch32_c.cpp:1032-1046` implements the exact `u32 battle_func_002bf41c(void* task)` contract.
- Disassembly of `body_hex` in `build/agent-work/H2-semantic/h2-bf41c-task-registry-convert/run001/report.json` (68 bytes, 0 relocations) uses `mvn r2, #7; and r2, r2, r1, lsr #17` to compute `((u32)handle >> 20) << 3` identically for all 32-bit `u32` inputs, preserves `r4-r11` and `SP`, and performs no writes or VFP operations.
- `config/functions.csv:5704` classifies `0x002bf41c` as `non_matching`, matching `byte_identical: false`.

## 2. Typed Caller Declarations & `TitleConfig_IsReady` Composition

- **Typed declarations**: `leaf_batch19_b.cpp:16`, `leaf_batch19_c.cpp:15`, `leaf_batch20_c.cpp:18`, `leaf_batch24_c.cpp:25`, `leaf_batch26_b.cpp:1773`, `leaf_batch29_c.cpp:24`, `leaf_batch32_c.cpp:26`, and `leaf_batch34_c.cpp:17` all declare `extern "C" u32 battle_func_002bf41c(void* task);`. `asd_render_ui.cpp:47` and `asd_text.cpp:40` declare `u32 AsdUi_IsRegistered(void* handle);`. (`leaf_batch32_c.cpp:2065` still calls `0x002BF41Cu` via raw function-pointer cast.)
- **Original `TitleConfig_IsReady` (`0x002FC0EC`, 52 bytes)**: Verified in `extracted/exefs/code.bin` (`0x001FC0EC..0x001FC120`): loads `g_TitleConfigWork` from `0x0044E2D0`, returns `1` immediately if null, otherwise loads `*(u32*)work`, calls `bl 0x002BF41C`, and returns `0` if nonzero or `1` if zero. Matches `src/engine/leaf_batch26_b.cpp:1775-1783` and `docs/function-records/0x002fc0ec.md`.

## 3. Fixture, Mutation, ABI, and Composition Audit

Inspected `tools/h2_bf41c_experiment.py` and `build/agent-work/H2-semantic/h2-bf41c-task-registry-convert/run001/report.json` (read-only; 0 compiler slots used):

- **Direct coverage**: All 4,096 bucket indices (`0..4095`) hit; 9 empty/boundary handles (`0`, `1`, `0xfffff`, `0x100000`, `0x100001`, `0x7fffffff`, `0x80000000`, `0xfff00000`, `0xffffffff`); 5 chain probes on a 4-node list (head, middle, tail, miss); 64 deterministic 8-node random chains.
- **Negative controls**: Compiled mutations for `bucket-index` (`handle >> 20` -> `handle >> 19`) and `handle-offset` (`node + 0x28` -> `node + 0x2c`) were both detected (`original: 1`, `mutant: 0`).
- **ABI/memory**: `execute()` verifies `r4-r11`, `SP`, normal return to `LR`, zero faults, and zero memory writes (`UC_HOOK_MEM_WRITE`).
- **Caller composition**: Patches the compiled 68-byte candidate into `0x002BF41C` in the pinned image and executes original `0x002FC0EC` across 5 fixtures (`null-work`, `registered`, `unregistered`, `null-task-absent`, `null-task-present`), verifying identical return values, zero faults, and `UC_HOOK_CODE` call-argument traces.

## 4. Limitations & Next Action

1. **Stale `source_sha256` in `report.json`**: `report.json` was generated against an earlier `leaf_batch32_c.cpp` (`f31e0469...`) before later batch-32 edits (`c793ee3c...`). Re-run `python tools/h2_bf41c_experiment.py` during coordinator batch closure (or under an assigned compiler slot) to refresh `report.json`'s `source_sha256` against HEAD.
2. **Offline synthetic domain**: Lists are acyclic and null-terminated; cycles, unreadable pointers, concurrent scheduler mutation, and live Azahar execution remain outside the tested domain.
