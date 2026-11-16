# `0x002BF030` H2 sentinel-table selector — independent read-only review

**Verdict: ACCEPT bounded typed `uint32_t(uint8_t*, uint32_t)` C++ reconstruction (`camp_func_002bf030` at `src/engine/leaf_batch41_b.cpp:1283-1307`) with original `0x00138934` service delegation and recorded offline differential + `0x002B8D24` index-11 composition evidence.**

## 1. Frozen pins & original ARM disassembly

- Recomputed all 9 `input_sha256` entries in `build/agent-work/H2-semantic/h2-helper-002bf030-review/run-001/task.json`: `9/9` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled pinned `0x002BF030` (120 bytes, ending with `b #0x138934` at `0x002BF0A0` and literal `0x00009249` at `0x002BF0A4`) from `extracted/exefs/code.bin`:
  - Reads `manager = *(object + 0x48)` and halfword `n = *(uint16_t*)(manager + 8)`.
  - Computes `count = ((uint32_t)n * 0x9249 + 0x9249) >> 20` (exact `n / 28` for all `uint16_t` `0..65535`).
  - If `count == 0`, sets `selected = nullptr` (`r1 = 0`).
  - Otherwise reads `table = *(manager + 0x1C)` and scans `i = 0..count-1` with 28-byte stride (`rsb r1, r2, r2, lsl #3; add r1, ip, r1, lsl #2`): compares `markers == selector` before reading `*(uint32_t*)(table + i*28)`; if equal, selects that entry and breaks; else increments `markers` when the first word is `0xFFFFFFFF`. If no match, `selected = nullptr`.
  - Tail-delegates to `0x00138934(object, selected)` (`b #0x138934`) and returns its raw `r0`.
- `camp_func_002bf030` (`src/engine/leaf_batch41_b.cpp:1283-1307`) and `candidate_002bf030` (`experiments/semantic_equivalence/h2_bf030_candidate.cpp:3-20`) have identical C++ bodies and compile to `96/96` bytes (`<= 120`-byte original slot).
- `config/functions.csv:5697` truthfully classifies `0x002bf030` (`120` bytes, `camp`, `camp_func_002bf030`, `src/engine/leaf_batch41_b.cpp`) as `non_matching`.

## 2. Audit of `tools/h2_bf030_experiment.py`, `offline-closure.txt`, & `0x002bf030.md`

- Recorded closure output `build/h2-bf030/offline-closure.txt` (SHA-256 `1970fbf111b01ddc67e6627a9e9a79dc7127b577496b0494b11d6f6dffe71b6a`) and prebuilt `build/h2-bf030/production/engine/leaf_batch41_b.o` are present and match `docs/function-records/0x002bf030.md`.
- **Direct differential (128 cases):** Covers halfword boundaries (`0, 1, 27, 28, 55, 56, 84, 65535`), selector boundaries (`0, 1, 7, count-1, count, 0xffffffff`), `service_word in {-1, 0}`, 24 seeded random cases, and `leading_nonmarker` / `none` / `all` marker patterns, asserting `r0`, `sp`, `r4..r11`, `obj`, `manager`, and non-stack writes with original `0x00138934` active.
- **Negative controls (6 compiled mutants):** `compare_order`, `stride`, `marker`, `increment_unconditionally`, `return`, and `count` all detected.
- **Caller composition (`0x002B8D24` index 11, 24 seeds):** Asserts `calls == 2` to `0x002BF030` with `selector = 7`, verifying `r0`, `sp`, `r4..r11`, `obj`, `manager1/2`, `table1/2`, and non-stack write traces.

## 3. Documented limits & audit notes

- Read-only audit (`compiler_slots: 0`): no compiler or emulator was run during this review.
- `0x00138934` and its deeper callees (including any nested `0x002BDAC0` service branch) remain original.
- Requires valid aligned ordinary-RAM `object`, `manager`, and `table` pointers; no null guards before `manager + 8` or nonempty scan; aliasing, faults, and live Azahar H2 runtime remain outside scope.
