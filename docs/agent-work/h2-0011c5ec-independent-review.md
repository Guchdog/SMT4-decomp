# `0x0011C5EC` (`func_0011c5ec`) — independent review

**Verdict: APPROVED for bounded ordinary-memory contract (`non_matching`, `304/304` bytes) with controlled `0x0012A758` ring seam and six original ARM callees.**

## 1. Frozen pins, source, & ABI audit

- Recomputed all `19/19` `input_sha256` entries in `build/agent-work/H2-semantic/h2-input-state-reader-independent-review-0011c5ec/run-001/task.json`: `19/19` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `func_0011c5ec` (`src/engine/leaf_batch30_a.cpp:4741-4800`) matches `docs/agent-work/h2-input-state-reader-contract.md`:
  - Stack out-params (`timestamp = 0xFFFFFFFFFFFFFFFF`, `index = 0xFFFFFFFF`, `&count`), mode-4 early return (`func_00128c2c() != 0`), calibration clamp (`func_001285c4`), two-step source dereference (`*(*context + 4)`), ring read (`func_0012a758`), `count <= 0` early return, normalizer (`func_00128610`), `context[0x30]` snapshot/clear, `~0x2000u` mask and ordered `+0/+4/+8` edge stores, short-circuit flag clear (`func_002bb978() != 0 && func_002bc9c8() == 0`) with ordered `+0/+8/+4/+0x0C/+0x0E` zeroing, `context+8` snapshot, and `*(u8*)0x00471AD8 == 0` postprocess (`func_0013bcac`).
- `config/functions.csv:435` truthfully classifies `0x0011c5ec` as `non_matching`.

## 2. Fresh seeded final-VMA differential (`--seed 20261127`)

Command (1 compiler slot, fresh output):

```powershell
python tools/h2_11c5ec_experiment.py --out build/agent-work/H2-semantic/h2-input-state-reader-independent-review-0011c5ec/run-001/checks/fresh-diff --seed 20261127
```

- Exit code: `0`.
- Report: `build/agent-work/H2-semantic/h2-input-state-reader-independent-review-0011c5ec/run-001/checks/fresh-diff/report.json` (SHA-256 `a078b79e5c52572666e980974821437c0f28108132c0cb0301292d54235266ea`).
- `288/288` direct cases (`direct_mismatches: 0`) and `32/32` `0x001078D8` caller compositions (`0` mismatches, `all_passed: true`), verifying `r0`, `SP`, `r4..r11`, `sp_aligned_8: true`, `timestamp_initial`, `index_initial`, ordered global/output writes, and faults.
- `3/3` mutation controls detected: `wrong_cleared_state_bit`, `reversed_context_marker_branch`, `omitted_short_circuit_output_clear`.
- Body & slot: `304/304` bytes, `7` even ARM `R_ARM_CALL` relocations (`0x00128C2C`, `0x001285C4`, `0x0012A758`, `0x00128610`, `0x002BB978`, `0x002BC9C8`, `0x0013BCAC`, all `entry_bit0: 0`).
- IPS & slot scope: `exact_slot_ips_replay: true`, `only_slot_changed: true`; `staged-image.bin` (`68bd138851294c4abec31c7cf3d79f310ec2d3a91c50c7e311fa56be0e677c69`) and `staged-slot.ips` (`91c4444ab65da98f03312b150436a4e91cac71753085b8177364ec6dc4bdb220`) match `run002` byte-for-byte.

## 3. Preserved limits

- Valid disjoint ordinary memory, controlled `0x0012A758` ring seam, and six original ARM callees; physical input provenance, buffer freshness, cadence, scheduling, concurrency, aliasing, malformed pointers/ring states, MMIO/device effects, and live Azahar runtime behavior remain unverified.
