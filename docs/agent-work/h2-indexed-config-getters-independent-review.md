# H2 indexed configuration getters (`0x002F5B2C`, `0x002D65B4`) — independent review

**Verdict: Approved (for bounded isolated getter contract and `0x00286928` six-entry loop composition).**

## 1. Frozen input pins & original disassembly

- Recomputed all 20 `input_sha256` entries in `build/agent-work/H2-semantic/h2-indexed-config-getters-review/run-001/task.json`: `20/20` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled both pinned original entries from `extracted/exefs/code.bin`:
  - `0x002F5B2C` (44 bytes, literal `0x0043DA28` at `0x002F5B54`):
    - Loads `manager` from `[0x0043DA28 + 4]` (`0x0043DA2C`), branches to `mov r0, #0; bx lr` if `manager == 0`.
    - Compares `r0` unsigned against `6` (`cmp r0, #6`).
    - If `lo` (`index < 6`): `addlo r0, r1, r0, lsl #2` then `ldrblo r0, [r0, #0x494]` (zero-extended byte), then `blo` to `bx lr`.
    - Otherwise returns `0`.
  - `0x002D65B4` (52 bytes, literal `0x0043DA28` at `0x002D65E4`):
    - Loads `manager` from `[0x0043DA28 + 4]` (`0x0043DA2C`), branches to `mov r0, #0; bx lr` if `manager == 0`.
    - Compares `r0` unsigned against `6` (`cmp r0, #6`); `bhs` to `mov r0, #0; bx lr`.
    - Computes `r0 = manager + (index << 2) + 0x400`, then `ldrh r0, [r0, #0x96]` (zero-extended halfword at `manager + index * 4 + 0x496`), then `bx lr`.
- Comparison with production C++ (`func_002f5b2c` in `src/engine/leaf_batch29_b.cpp:471-476` and `func_002d65b4` in `src/engine/leaf_batch32_c.cpp:2743-2748`):
  - Access types (`volatile const uint32_t*` at `0x0043DA2Cu`, `volatile const uint8_t*`, `volatile const uint16_t*`), offsets (`+ index * 4u + 0x494u`, `+ index * 4u + 0x496u`), evaluation order (`manager == 0` then unsigned `index >= 6`), zero-extended `uint32_t` return, and AAPCS ABI (`r0` in/out, no writes, no calls, no callee-saved clobber) all match the ARM originals.

## 2. Fresh seeded final-VMA differential & mutation controls

Command executed (1 compiler slot, fresh output dir, seed `20261124`):

```powershell
python tools/h2_indexed_config_getters_experiment.py --out build/agent-work/H2-semantic/h2-indexed-config-getters-review/run-001/checks/fresh-diff --seed 20261124
```

- Exit code: `0`.
- Report: `build/agent-work/H2-semantic/h2-indexed-config-getters-review/run-001/checks/fresh-diff/report.json` (SHA-256 `290083750c6709fc584613e60601848af5f83a15c5e5d98f5c883d6ddea4512a`).
- Direct cases: `44/44` matched (`mismatch_count: 0`) across both getters, null (`0`) and valid (`0x00500000`) managers, and unsigned indices `0..7`, `0x7FFFFFFF`, `0x80000000`, `0xFFFFFFFF`, verifying `r0`, `sp`, `r4..r11`, manager/global bytes, write traces, and faults.
- Caller compositions: `2/2` (`seeds 20261122, 20261123`) through original `0x00286928` matched (`equal: true`, `valid: true`), exercising 6 calls per getter for indices `0..5` with external callees `0x002C1F28` and `0x0028E974` stubbed to zero.
- Mutation controls: `4/4` detected:
  - `func_002f5b2c_wrong_field_offset` (`index=2`: `0x23` vs `0x24`)
  - `func_002f5b2c_wrong_upper_bound` (`index=6`: `0x0` vs `0xe1`)
  - `func_002d65b4_wrong_field_offset` (`index=2`: `0x6122` vs `0x6123`)
  - `func_002d65b4_wrong_upper_bound` (`index=6`: `0x0` vs `0xe261`)

## 3. Slot scope, IPS replay, ledger labels, README, and limits

- Body sizes & relocations:
  - `func_002f5b2c`: `44 / 44` bytes, `relocations: []`, `byte_identical: false`, `.o` SHA-256 `3779ce6e87203addbffc4af1806a55b349ab28b13e37e7a33ca334fbeee9a9d7`.
  - `func_002d65b4`: `52 / 52` bytes, `relocations: []`, `byte_identical: false`, `.o` SHA-256 `9f98ea6a7f0f7c96644e6a2fb4b6503390c66d80f78e14ab1a33b7e926d63b1e`.
- IPS replay & slot scope: `ips_replay: true`, `changed_slots_only: true`. Fresh `staged-image.bin` (`294db5f615c0c25ed01ceca45f756a08b8b83c805ad5b8d858970db05f74cfdd`) and `staged-slot.ips` (`c7a0526b1f83d0933c561699c80ec864b7f21bc8071ae2681a9db4ca6e6326fd`) match the `run006` artifacts byte-for-byte.
- Ledger labels: `config/functions.csv` truthfully marks both `0x002d65b4` (row 6149, 52 bytes) and `0x002f5b2c` (row 6672, 44 bytes) as `non_matching`.
- README arithmetic & documentation:
  - `README.md` line 85 documents `0x002F5B2C`, `0x002D65B4` and line 107 lists both among typed C++ reconstructions.
  - `README.md` lines 106–110 arithmetic is internally consistent: `3,117,224 + 21,884 = 3,139,108` bytes (`99.3029%`), `10,881 + 78 = 10,959` functions + `8` raw spans. (Note: `config/functions.csv` currently reflects wider branch conversions with `1,489` `non_matching` rows / `239,724` bytes; summary tables are refreshed at batch closure.)
- Caller & domain limits:
  - Nonzero invalid manager pointers remain outside the supported domain (can fault).
  - The `0x00286928` caller composition stubs `0x002C1F28` and `0x0028E974` to zero and exercises only the six-entry loop (`indices 0..5`); the full `0x00286928` state machine, manager lifecycle, field meanings, and runtime H2 behavior remain open.
