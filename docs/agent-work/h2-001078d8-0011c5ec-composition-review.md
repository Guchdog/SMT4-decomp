# Independent Review: `0x001078D8` + `0x0011C5EC` Production-Image Composition

## Verdict

**Disposition:** **Accept** the combined `0x001078D8` (logical input counter refresh) and `0x0011C5EC` (input-state reader) two-slot production-image composition within its valid disjoint synthetic ordinary-memory domain and controlled `0x0012A758` ring seam.

This review does not claim physical input provenance, freshness, scheduling, concurrency, or live Azahar runtime equivalence.

## 1. Frozen Pins & Fresh Seed Rerun (`seed 20261117`)

- Verified all `18/18` frozen `input_sha256` pins (`0` mismatches; `extracted/exefs/code.bin` `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `python tools/h2_1078d8_11c5ec_chain.py --out build/agent-work/H2-semantic/h2-input-refresh-reader-integrated-chain-review/run-001/checks/seed-20261117 --seed 20261117` (exit `0`, `report.json` SHA-256 `0decd5f1b5444ee21a3d7a41973a74183bde2af7b65d2049c222e0243ec3b2f5`):
  - **Distinct fixture digest**: `fixture_sha256` `0f315fea270ed7820ace12551ea98a17c0cbf2a68d8e274ae43efe4070c1d9e6` (distinct from `20261116` `d401374d...`).
  - **144/144 compositions passed** (`mismatches: 0`, `all_passed: true`, `all_abi_ok: true`): covers mode `{0, 4}`, ring count `{-1, 0, 1}`, selectors `0..3`, global flag pairs, postprocess gate, 32 counter words, and row-31 sentinel.
  - **72 ring-call ABI traces**: all `72` `0x0012A758` calls verified `sp_aligned_8: true`, `source_is_fixture: true`, and in-frame output pointers.

## 2. Slot Sizes, IPS Scope, Relocations & Affected TUs

- **Slots & IPS**: `0x0011C5EC` reader `304/304` bytes; `0x001078D8` refresher `160/164` bytes (`4`-byte ARM NOP tail). `exact_two_slot_ips_replay: true`, `only_declared_slots_changed: true`.
- **Relocations & interworking**:
  - Refresher `R_ARM_CALL` (`type: 28`, offset `20`) resolves to even ARM `func_0011c5ec` (`0x0011C5EC`, `0xeb00533e`).
  - Reader `7` `R_ARM_CALL` relocations (`0x00128C2C`, `0x001285C4`, `0x0012A758`, `0x00128610`, `0x002BB978`, `0x002BC9C8`, `0x0013BCAC`) all have `entry_bit0: 0`.
- **Affected TUs**: `src/engine/leaf_batch27_a.cpp` (`0x001078D8`) and `src/engine/leaf_batch30_a.cpp` (`0x0011C5EC`) both compiled cleanly during the runner pass.

## 3. Limits

- `0x0012A758` is a controlled ring-seam fixture; the other six reader callees execute pinned original ARM.
- Disjoint valid synthetic ordinary memory only; physical input provenance, freshness, cadence, scheduling, concurrency, MMIO, and live Azahar runtime remain unverified.
