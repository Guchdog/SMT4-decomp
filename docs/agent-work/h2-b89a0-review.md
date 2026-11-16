# `0x002B89A0` H2 manager-mode predicate — independent read-only review

**Verdict: ACCEPT bounded typed `int32_t()` C++ reconstruction (`camp_func_002b89a0` at `src/engine/leaf_batch26_b.cpp:1602-1610`) and recorded offline differential + nonzero `0x00286928` continuation evidence.**

## 1. Frozen pins & original ARM disassembly

- Recomputed all 9 `input_sha256` entries in `build/agent-work/H2-semantic/h2-helper-002b89a0-review/run-001/task.json`: `9/9` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled pinned `0x002B89A0` (52 bytes: 48 bytes of ARM instructions + 4-byte literal `0x0044DC20` at `0x002B89D0`) from `extracted/exefs/code.bin`:
  - `0x002b89a0`: `ldr r0, [pc, #0x28]` (`0x0044DC20`)
  - `0x002b89a4`: `ldr r0, [r0]` (loads `manager`)
  - `0x002b89a8`: `cmp r0, #0; beq #0x2b89c8` (if `manager == 0`, returns `1`)
  - `0x002b89b0..b8`: `add r0, r0, #0x3400; add r0, r0, #0x12c; ldr r0, [r0]` (loads `uint32_t` at `manager + 0x352C`)
  - `0x002b89bc..cc`: `cmp r0, #0x14; movne r0, #0; bne #0x2b89cc; mov r0, #1; bx lr` (returns `1` iff `mode == 0x14`, else `0`).
- `camp_func_002b89a0` (`src/engine/leaf_batch26_b.cpp:1602-1610`) and `candidate_002b89a0` (`experiments/semantic_equivalence/h2_b89a0_candidate.cpp:3-11`) have identical C++ bodies: null check on `0x0044DC20` returning `1`, otherwise `uint32_t` read at `manager + 0x352C` returning `mode == 0x14 ? 1 : 0`, with zero memory writes.
- `config/functions.csv:5524` truthfully classifies `0x002b89a0` (`52` bytes, `camp`, `camp_func_002b89a0`, `src/engine/leaf_batch26_b.cpp`) as `non_matching`.

## 2. Audit of `tools/h2_b89a0_experiment.py` & `docs/function-records/0x002b89a0.md`

- **Direct differential (139 cases):** Covers `(seed=0, null)` plus 10 directed non-null cases and 128 seeded random cases across `mode in {0, 0x13, 0x14, 0x15, 0xffffffff}`, asserting `r0`, `sp`, `r4..r11`, `0x44DC20` (4B), `state+0x3520..0x3540` (32B), and `UC_HOOK_MEM_WRITE` zero writes for original, candidate, and production (`build/h2-b89a0/production/engine/leaf_batch26_b.o`, present in worktree).
- **Negative controls (3 compiled mutants):** Source-level mutations for `null` (`== nullptr` → `!= nullptr`), `offset` (`+ 0x352c` → `+ 0x3528`), and `value` (`== 0x14` → `== 0x13`) are compiled and verified to diverge (including `UcError` on null dereference).
- **Nonzero `0x00286928` continuation (32 seeds):** Sets `0x0043E0B8` so `0x002C1F28` returns `1`, sets `0x0044DC20 = 0` (`0x002B89A0` returns `1`), and sets `obj[9] = 19` (early exit from `0x002B8D24`), asserting `calls == 1` to `0x002B89A0`, `r0`, `sp`, `r4..r11`, `obj`, `state`, globals, and ordered write traces.

## 3. Documented limits & audit notes

- Read-only audit (`compiler_slots: 0`): no compiler or emulator was run during this review.
- `0x00286928` continuation exercises only the null-manager true case (`0x0044DC20 == 0`) with `obj[9] == 19`; non-null manager continuation in `0x00286928`, other 13 candidate BL sites, the unverified `Camp_IsMenuActive()` alias in `src/battle/battle_extras.cpp`, invalid non-null pointer faults, and live Azahar runtime behavior remain outside scope.
