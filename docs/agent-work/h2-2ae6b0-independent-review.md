# Independent Review: `0x002AE6B0` (`AsdText_IsControlCode` / `engine_func_002ae6b0`)

## Verdict

**Disposition:** **Accept** the typed `uint32_t(uint32_t)` C++ reconstruction in `src/engine/leaf_matching.cpp` (`engine_func_002ae6b0`) and its offline differential, negative-control, and `0x00286928 -> 0x002B787C` caller-composition evidence.

This review does not claim live Azahar runtime reach or whole-game H2 equivalence.

## 1. Independent Verification of Pinned Original Body (`0x002AE6B0`, 24 bytes)

Inspected `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at file offset `0x001AE6B0..0x001AE6C8`:

```arm
0x002ae6b0: sub   r0, r0, #0xf800
0x002ae6b4: sub   r0, r0, #1
0x002ae6b8: cmp   r0, #0x8f
0x002ae6bc: movlo r0, #1
0x002ae6c0: movhs r0, #0
0x002ae6c4: bx    lr
```

- **Unsigned interval contract**: Computes `((uint32_t)(code - 0xF801u) < 0x8Fu) ? 1u : 0u`, returning `1` iff `0xF801 <= code <= 0xF88F` (unsigned 32-bit; `0xF801 + 0x8E = 0xF88F` does not wrap), and `0` otherwise.
- **ABI & memory effects**: Pure register arithmetic in `r0`; no stack frame, no VFP/NEON instructions, no memory reads or writes, preserves `r4-r11` and `SP`.

### Candidate, Hashes, and Ledger Check

- `src/engine/leaf_matching.cpp:2956-2959` (`SHA-256 2a59d7aeba7fa2f9f70046b2e9dea87a2e65471a0069886e3b84e1ce2daf58d3`) matches `source_sha256` in `build/agent-work/H2-semantic/h2-ae6b0-convert/run001/report.json`.
- `include/engine/leaf_matching.h:508` declares `u32 engine_func_002ae6b0(u32 code);`, matching the `uint32_t(uint32_t)` definition.
- Disassembly of `candidate_hex` from `report.json` (24 bytes, 0 relocations):
  ```arm
  0x002ae6b0: mvn   r1, #0xf800   @ 0xFFFF07FF == -0xF801 mod 2^32
  0x002ae6b4: add   r1, r0, r1    @ r1 = code - 0xF801 mod 2^32
  0x002ae6b8: mov   r0, #0
  0x002ae6bc: cmp   r1, #0x8f
  0x002ae6c0: movlo r0, #1
  0x002ae6c4: bx    lr
  ```
  Algebraically identical to the original for all $2^{32}$ `uint32_t` inputs, fits the 24-byte slot with 0 relocations, touches only `r0-r1`, and performs no memory accesses.
- `config/functions.csv:5334` truthfully classifies `0x002ae6b0` as `non_matching`.

## 2. Runner, Coverage, Controls, and Caller Composition Audit

Inspected `tools/h2_ae6b0_experiment.py` and `build/agent-work/H2-semantic/h2-ae6b0-convert/run001/report.json` (read-only; 0 compiler slots used):

- **Exhaustive halfword & 32-bit probes**: `66,057` distinct cases covering all `65,536` halfwords (`0x0000..0xFFFF`), `18` directed `u32` boundary/high-bit inputs (including `0xF800`, `0xF801`, `0xF88F`, `0xF890`, `0x10000`, `0x7FFFFFFF`, `0x80000000`, `0xFFFFF801`, `0xFFFFFFFF`), and `512` deterministic random `u32` inputs (`seed=20261102`).
- **ABI/memory observations**: `execute()` verifies `r4-r11` preservation, `SP` restoration, and zero guest memory writes (`UC_HOOK_MEM_WRITE`). (`d8-d15` are not explicitly sampled by `execute()`, though disassembly confirms no VFP/NEON instructions.)
- **Negative controls**: Compiled `upper-bound` (`< 0x8fu` -> `< 0x90u`, tested at `0xF890`) and `lower-bound` (`code - 0xf801u` -> `code - 0xf800u`, tested at `0xF800`) mutants; both were detected (`reference: 0`, `mutant: 1`).
- **Caller composition**: Patches the 24-byte candidate into `0x002AE6B0` in the pinned image and executes `line_count.run_parent_composition` (`0x00286928 -> 0x002B787C -> converted 0x002AE6B0`) for selectors `11` and `19`, verifying identical `done: true`, `object_20: 2`, and `line-count-entry` events.

## 3. Limitations

- Offline Unicorn differential and stubbed `0x00286928` parent composition only; no live Azahar runtime or H2 title audio flow is claimed.
