# `0x00207D84` generic UI transform wrapper — independent review

**Verdict: APPROVED for the explicitly generic UI conversion and tested finite/mapped-memory domain ONLY; NOT approved for cumulative H2 image integration at `0x003FEE54` (verified cave collision with Draw/Secondary) and no TitleConfig / Audio Settings reachability is established.**

## 1. Frozen pins & original ARM comparison

- Recomputed all 15 `input_sha256` entries in `build/agent-work/H2-semantic/h2-ui-transform-review-00207d84/run-001/task.json`: `15/15` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled the 128-byte pinned original `0x00207D84` from `extracted/exefs/code.bin` (116 bytes of ARM instructions + 3 literal words `0x004EA81C`, `0x00472550`, `0x00000000`):
  - Calls `0x002C5218()` (`r0` = context).
  - Loads 4 words from `0x004EA81C + 0x100` (`0x004EA91C`) via `vldmia r3, {s0..s3}` and stores them in order to scratch `0x00472550..0x0047255F`.
  - Reads the first 3 scratch words into `SP + 0x10..0x18` and calls `0x0026330C(SP, 0, context, SP + 0x10)`.
  - Writes the 3 output words + `+0.0f` (`0x00000000`) in order to `0x004EA91C..0x004EA928`.
  - Returns `r0 = 0x004EA91C` and `s0 = output[2]` (projected z).
- `ui_func_00207d84` (`src/engine/leaf_batch30_c.cpp:22-48`) preserves the exact global scratch copy order, 3-word projection input, 4-word output order with zero fourth word, `r0` (`return_vector_r0`), and `s0` return contract.

## 2. Fresh VFP-aware differential & caller slices

Command executed (1 compiler slot, fresh output dir, seed `20261125`):

```powershell
python -B tools/ui_transform_00207d84_experiment.py --out build/agent-work/H2-semantic/h2-ui-transform-review-00207d84/run-001/checks/fresh-diff --seed 20261125
```

- Exit code: `0`.
- Report: `build/agent-work/H2-semantic/h2-ui-transform-review-00207d84/run-001/checks/fresh-diff/report.json` (SHA-256 `3e23ce648dc7d2f41ca1dca198c2c725c852ca13aff1ad977ee7197f2b02346c`).
- Direct fixtures: `7/7` matched (`all_direct_equal: true`), including basis, negative, perspective, near-denominator finite, and seeded cases, checking global vector/scratch words, `r0`, `s0`, `r4..r11`, `SP`, `s16..s31`, caller stack, and ordered writes.
- FPSCR rounding modes: `4/4` matched (`RN`, `RP`, `RM`, `RZ`; `all_rounding_equal: true`).
- Caller compositions: `2/2` (`same`, `distinct`; `all_caller_equal: true`) through original `0x0024B874` hitting both real callsites `0x0024B8E0` and `0x0024B908`, with unrelated UI callees `0x002698F4`, `0x00269768`, and `0x0024C62C (fixed s0=0.125)` stubbed.
- Negative controls: `3/3` observation-level controls detected (`all_controls_detected: true`).

## 3. Slot, relocations, interworking, IPS, and ledger

- Compiled body: `156` bytes (`body_sha256`: `55ae2912dc803befe28ed3eee02ba3cb8f3e9e99aad2eaa23bdfe6e2a9960a24`), exceeding the `128`-byte original slot at `0x00207D84`.
- Relocations & interworking: 2 `R_ARM_CALL`s at staged VMAs `0x003FEE68` (`ui_func_002c5218` -> `0x002C5218`, `thumb: false`) and `0x003FEEB0` (`ui_func_0026330c` -> `0x0026330C`, `thumb: false`); both targets are even ARM entries, and the entry trampoline at `0x00207D84` is an aligned ARM `B` to `0x003FEE54`.
- IPS replay: `ips_replays: true`, `changed_outside_entry_and_cave: false` (`ips_sha256`: `366295c270f3fc3f55ae47cd2f8ade7e7e62914926ed76ac9af6316c7a157ca9`).
- Ledger & README: `config/functions.csv:2770` truthfully marks `0x00207d84` (`128` bytes) as `non_matching`. `README.md` lines 106–110 arithmetic (`3,117,224 + 21,884 = 3,139,108`, `10,881 + 78 = 10,959`, `99.3029%`) is internally consistent, and line 108 explicitly records the `0x003FEE54` cumulative-image collision.

## 4. Explicit limits & placement gate

- **No TitleConfig / Audio Settings reachability** is demonstrated; `0x0024B874` is a generic UI caller.
- **Cumulative-image placement blocked at `0x003FEE54`:** `0x003FEE54..0x003FEFF8` is already occupied by Draw helper code/data and Secondary code in the cumulative H2 image. A non-overlapping layout or `<= 128`-byte in-slot body is required before cumulative integration.
- Projection callees `0x002C5218` and `0x0026330C` remain original; nonzero invalid pointers, zero/nonfinite denominators beyond the tested finite near-boundary sample, and runtime emulator behavior remain unverified.
