# Independent Review: `0x002AE664` (`func_002ae664`) ASD Control-Code Table Mapping

## Verdict

**Disposition:** **Accept** the typed `u32(u32)` C++ reconstruction in `src/engine/leaf_batch28_b.cpp` (`func_002ae664`) and its offline differential, negative-control, and cumulative (`0x002AE664` + `0x002AE6B0` -> `0x002B787C` -> `0x00286928`) composition evidence, **with one minor provenance note**: `report.json` (`run001`) pins `harness_sha256["h2_86928_experiment.py"]` as `e41a245675dd1ad8282f83733d8deaa3d0aabb2d3858b0e6a9ce782bff43c040`, whereas `tools/h2_86928_experiment.py` at HEAD `7e9db4d1` has SHA-256 `340f9c5ca81f41f48b5892b2cb73926304543466781dca617d716829792b29ae`.

This review does not claim live Azahar runtime reach or whole-game H2 equivalence.

## 1. Independent Verification of Pinned Original Body (`0x002AE664`, 76 bytes)

Inspected `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at file offset `0x001AE664..0x001AE6B0`:

- **Prologue & stack spill**: `str r4, [sp, #-4]!` spills `r4` to `SP-4`, restored by `pop {r4}` at `0x002AE6A0`.
- **Table base & sentinel**: `ldr r4, [pc, #0x38]` loads `0x00464DA8` (table base); `ldr ip, [pc, #0x38]` loads `0x0000F890` (sentinel) from `0x002AE6AC`.
- **Loop & sentinel-before-match**: Scans 16-byte entries (`add r1, r4, r2, lsl #4`). Reads `u16` key via `ldrh r3, [r1]` and checks `cmp r3, ip; beq 0x2ae69c` (`return 0`) **before** `cmp r3, r0` (`key == code`). Thus `code == 0xF890` returns `0` when the sentinel is reached first.
- **Unsigned 32-bit input domain**: `cmp r3, r0` compares the zero-extended `u16` key against the full 32-bit `r0`, so any `code > 0xFFFF` cannot match. On match, `ldr r0, [r1, #4]` returns the `u32` value at `+4` (`cmp r1, #0` guard is always non-zero for valid table entries).

### Candidate & Ledger Check

- `src/engine/leaf_batch28_b.cpp:57-65` (`SHA-256 ecdd96c82116e87d6fc27b97809bd5a779b0a3de5cb81fef3b3123e7abe3017a`) matches `source_sha256` in `build/agent-work/H2-semantic/h2-ae664-convert/run001/report.json`.
- Disassembly of `body_hex` from `report.json` (56 bytes, 0 relocations, fits 76-byte slot): loads `0x00464DAC` (`table + 4`) into `r3`, constructs `0xF890` in `ip`, reads `ldrh r1, [r3, #-4]`, checks sentinel `0xF890` before `cmp r0, r1`, returns `*(u32*)(entry + 4)` on match, and advances `r3` by `0x10`. Uses no stack spill, touches only `r0-r3, ip`, preserves `r4-r11` and `SP`, and performs zero memory writes.
- `config/functions.csv:5333` truthfully classifies `0x002ae664` as `non_matching`.

## 2. Differential, Layouts, Controls, and Cumulative Composition Audit

Inspected `tools/h2_ae664_experiment.py` and `build/agent-work/H2-semantic/h2-ae664-convert/run001/report.json` (read-only; 0 compiler slots used):

- **Direct coverage**: `65,798` distinct inputs (all `65,536` `u16` values, `6` directed `u32` values `0x10000..0xffffffff`, `256` seeded `u32` values) plus `3` table layouts (`sentinel-first`, `late-match`, `duplicate-first-wins`).
- **ABI/memory observations**: `execute()` verifies `r0`, `r4-r11`, `SP`, `done`, zero faults, and `external_writes == ()` (allowing the original's `SP-4` spill in `stack_writes`).
- **Negative controls**: Compiled `key-match` (`key == code` -> `key == code + 1u` at `0xF802`: `0` vs `3`) and `sentinel` (`0xf890` -> `0xf891` at `0xF890`: `0` vs `0xDEADBEEF`) mutants were both detected.
- **Cumulative composition**: Patches both converted `0x002AE664` (56B + 5 NOPs) and converted `0x002AE6B0` (24B) into `IMAGE`, then passes all `515` `0x002B787C` line-count cases and `0x00286928` selectors `11` and `19` (`done: true`, `object_20: 2`).

## 3. Limitations

- Offline synthetic tables only (sentinel-terminated, `<= 255` entries); absent/unreadable sentinels, concurrent table mutation, and live Azahar execution remain outside the tested domain.
- Refresh `tools/h2_ae664_experiment.py` during batch closure if an updated `h2_86928_experiment.py` hash pin in `report.json` is desired.
