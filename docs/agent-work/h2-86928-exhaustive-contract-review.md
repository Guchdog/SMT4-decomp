# `0x00286928` exhaustive static contract — independent review

**Verdict: APPROVED — `docs/agent-work/h2-86928-exhaustive-contract.md` is accurate and suitable for full C++ implementation/validation within the 820-byte slot.**

## 1. Frozen pins & independent ARM verification

- Static ARM review and packet hash verification only (`compiler_slots: 0`); no code, build, test, or emulator changes.
- Recomputed all `13/13` `input_sha256` entries in `build/agent-work/H2-semantic/h2-helper-00286928-contract-review/run-001/task.json`: `13/13` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled all `820` bytes of `0x00286928..0x00286C5B` from `extracted/exefs/code.bin` (literals `0x0043E188`, `0x035AB9FF`, `0x320202FF` at `0x00286C50..0x00286C58`):
  - **Stack & VFP ABI:** `push {r0..r11, lr}`, `vpush {d8}`, `sub sp, sp, #0xc`; `arg5` loaded from `[sp, #0x48]`, `arg6` loaded via `vldr s16, [sp, #0x4c]` (`FPEXC.EN` required). Restores `SP`, `d8`, `r4..r11`.
  - **Selector normalization (`0x0043E188`):** `table[1]` default; `table[2]` for `{11, 13, 14, 15, 19}` with `{13, 14, 15}` normalized to `11` and `19` kept as `19`; `table[3]` for `12`. Prewrites `object+0x2D = (raw == 13 || raw == 15)` and `object+0x5E = (raw == 11 || raw == 13)`.
  - **`r2 != 0` & `r2 == 0` branches:** All `state in {4, 5, 0, 3, other}` and `0x2E == 0 / != 0` paths, `0x0028E974` 7-argument stack marshaling (`[SP]=0x1A`, `[SP+4]=1`, `[SP+8]=arg6` or `0`), `arg5 != 0` double-read of `*(u32*)(object + 4)` around `0x002C4BF0`/`0x002B90F0`, 6-entry `0x002F5B2C`/`0x002D65B4` loop (`0x00286B18..0x00286B44`), `row in {7..9} && 0x0028DF70(0) == 5` -> `0x002B8B78(0xDC)`, and `selector == 19` -> `0x002B8584(1)` match the contract.
  - **22 direct `BL` sites (17 unique callees):** Spot-checked all 22 `BL` addresses (`0x002869E8..0x00286C44`; `0x00286B44` is `blt #0x286b18`, an internal loop branch, not a `BL`).
  - **Runtime trace restraint:** Contract rejects partial fast-path replacements and does not overinterpret uncaptured runtime causes.

## 2. Minor precision notes (non-blocking)

- `object != nullptr` (`table[1/2/3] != 0`) is a precondition across the entire function because the `+0x2D`/`+0x5E` prewrites execute unconditionally before any branch.
- `arg5 != 0` re-reads `*(u32*)(object + 4)` before `0x002B90F0` (already matched by `src/engine/leaf_batch45_a.cpp:12809-12812`).
