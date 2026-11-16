# `0x002AA268` (`camp_func_002aa268`) — independent review

**Verdict: APPROVED for bounded `non_matching` promotion (`68/72` bytes, `0` relocations) within the tested aligned ordinary-RAM, aliasing, and `0x002B85BC` two-slot caller domain.**

## 1. Frozen pins, source/ABI, & caller audit

- Recomputed all `14/14` `input_sha256` entries in `build/agent-work/H2-semantic/h2-profile-record-copy-review-002aa268/run-001/task.json`: `14/14` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- `camp_func_002aa268` (`src/engine/leaf_batch13_b.cpp:28-51`) matches the pinned 72-byte ARM body:
  - Null `record+0x64` returns `record` (`r0`) without writes.
  - Ordered `volatile` stores (`+0x68 = (u16)index`, `+0x6A = 0`, `+0x88 = 0`, `+0x8A = 0`, `+0x6C = (u8)selector`) precede the `volatile` load at `table + (index * 3 + (selector != 0 ? 1 : 0)) * 4` (equivalent mod `2^32` to `table + index * 12 + (selector == 0 ? 0 : 4)`).
  - Ordered `volatile` stores of `selected_value` to `+0x24`, `+0x28`, `+0x2C`, returning `record`.
- `config/functions.csv:5243` truthfully classifies `0x002aa268` (`72` bytes) as `non_matching`; `README.md` line 107 lists `0x002AA268` and lines 106–110 arithmetic (`3,117,224 + 21,884 = 3,139,108`, `10,881 + 78 = 10,959`, `99.3029%`) is internally consistent.

## 2. Fresh final-VMA/caller differential, controls, & IPS

Command (1 compiler slot, fresh output):

```powershell
python tools/h2_profile_record_copy_experiment.py --out build/agent-work/H2-semantic/h2-profile-record-copy-review-002aa268/run-001/checks/fresh-diff
```

- Exit code: `0`.
- Report: `build/agent-work/H2-semantic/h2-profile-record-copy-review-002aa268/run-001/checks/fresh-diff/report.json` (SHA-256 `22fc2d60af1aaf56404a1492f7147a5af4ecadfcc3535f45e7b4a2dea5ad00f7`).
- `12/12` direct cases (`equal: true`, `mismatch_count: 0`), including null table, full-width `index` (`0x10000`, wrap), full-width `selector` (`0x100`, high), two self-alias cases (`+0x68`, `+0x6C`), and two matching unmapped fault cases (`invalid_record_fault`, `invalid_selected_table_fault_after_metadata`).
- `caller_equal: true`: original `0x002B85BC` executes both `(object+0x37C, 0, 1)` and `(object+0x408, 0, 1)` callsites (`0x002B86FC`) with `sp_aligned: true`.
- `4/4` mutation controls detected: `stride`, `branch`, `field_offset`, `store_order`.
- `68/72` bytes, `0` relocations (even ARM entry `0x002AA268`), `ips_replay: true`, `changed_outside_slot: false` (`staged-image.bin` `e1c0e48e...`, `staged-entry.ips` `b80f240f...`).

## 3. Preserved limits

- Synthetic aligned ordinary RAM, controlled sibling hooks in `0x002B85BC`, and no table-length/bounds check; live table population, pointer lifetime, concurrency, and Azahar runtime behavior remain unverified.
