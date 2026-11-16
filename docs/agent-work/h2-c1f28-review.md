# `0x002C1F28` H2 signed global predicate — independent read-only review

**Verdict: ACCEPT bounded typed `int32_t()` C++ reconstruction (`engine_func_002c1f28` at `src/engine/leaf_batch22_b.cpp:865-872`) and recorded offline differential + zero-path `0x00286928` caller composition evidence.**

## 1. Frozen pins & original ARM disassembly

- Recomputed all 9 `input_sha256` entries in `build/agent-work/H2-semantic/h2-helper-002c1f28-review/run-001/task.json`: `9/9` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled pinned `0x002C1F28` (28 bytes: 24 bytes of ARM instructions + 4-byte literal `0x0043E0B8` at `0x002C1F40`) from `extracted/exefs/code.bin`:
  - `0x002c1f28`: `ldr r0, [pc, #0x10]` (`0x0043E0B8`)
  - `0x002c1f2c`: `ldr r1, [r0, #4]` (signed 32-bit word at `0x0043E0BC`)
  - `0x002c1f30`: `cmp r1, #0`
  - `0x002c1f34`: `ldrsblt r0, [r0]` (if `< 0`, sign-extended byte at `0x0043E0B8` into `r0`)
  - `0x002c1f38`: `movge r0, #0` (if `>= 0`, `r0 = 0`)
  - `0x002c1f3c`: `bx lr`
- `engine_func_002c1f28` (`src/engine/leaf_batch22_b.cpp:865-872`) and `candidate_002c1f28` (`experiments/semantic_equivalence/h2_c1f28_candidate.cpp:3-10`) share the exact same C++ body: signed `int32_t` read at `0x0043E0BC`, signed `int8_t` read at `0x0043E0B8` when negative, `0` otherwise, `int32_t` return in `r0`, and zero memory writes.
- `config/functions.csv:5782` truthfully classifies `0x002c1f28` (`28` bytes, `engine`, `engine_func_002c1f28`, `src/engine/leaf_batch22_b.cpp`) as `non_matching`.

## 2. Audit of `tools/h2_c1f28_experiment.py` & `docs/function-records/0x002c1f28.md`

- **Direct differential (153 cases):** Covers all 25 `(threshold, flag)` boundary pairs (`{-0x80000000, -1, 0, 1, 0x7fffffff}` × `{-128, -1, 0, 1, 127}`) plus 128 seeded random pairs (`random.Random(0x2c1f28)`), asserting `r0`, `sp`, `r4..r11`, unchanged `0x43E0B8..0x43E0F8` bytes, and `UC_HOOK_MEM_WRITE` zero writes for original, candidate, and production (`build/h2-c1f28/production/engine/leaf_batch22_b.o`, present in worktree).
- **Negative controls (3 compiled mutants):** Source-level mutations for predicate (`< 0` → `>= 0`), sign extension (`int8_t` → `uint8_t`), and return value (`*int8_t` → `0`) are compiled and verified to diverge from original.
- **Caller composition (`0x00286928`, 32 seeds):** Exercises `0x00286928` with `obj[8] = 1` and `obj[0x2e] = 7` across 32 seeds for `threshold=0` (candidate) and `threshold=1` (production), verifying `r0`, `sp`, `r4..r11`, `obj`, `state`, `0x43E0B8..0x43E0F8`, and ordered memory writes.

## 3. Documented limits & audit notes

- Read-only audit (`compiler_slots: 0`): no compiler or emulator was run during this review.
- `0x00286928` caller composition exercises only the `enabled >= 0` (zero-return) path; nonzero return (`enabled < 0`) in `0x00286928` and other callers is not exercised (documented in `docs/function-records/0x002c1f28.md`).
- Valid domain is readable ordinary memory at `0x0043E0B8` and `0x0043E0BC`; no unmapped fault equivalence, cross-TU LTO type compatibility for `extern "C" void` raw-asm caller declarations, or live Azahar runtime behavior is claimed.
