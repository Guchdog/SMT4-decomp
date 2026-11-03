# H2 `0x001078D8` production C++ conversion

## Scope

This conversion makes the logical input counter writer readable C++. The
production function still calls the original ARM `func_0011C5EC`; it claims only
the bounded counter-refresh semantics described in the
[function record](../function-records/0x001078d8.md). It does not identify
physical controls or establish input scheduling/runtime behavior.

## Implementation

`func_001078d8` now normalizes the original reader result, stores availability,
and walks the original 31 table/counter rows. It preserves the fixed state-word
address, nonzero-row reset, signed-positive availability gate, unavailable
counter retention, mask miss reset, and unsigned 32-bit increment wrap. The
compiled C++ body is 160 bytes within the original 164-byte slot, with one
`R_ARM_CALL` to even ARM entry `0x0011C5EC`.

## Validation

The original `run005`/`run006` direct-pass claims are invalid because those
runner versions did not map the direct return sentinel and accepted matching
fetch faults. The runner now maps the sentinel, records its stop address, and
requires fault-free completion. Corrected run `run009` used seed `20261104`:

```powershell
python tools/h2_1078d8_experiment.py --out build/agent-work/H2-semantic/h2-titleconfig-001078d8-counter-refresh-cpp/run009/checks/direct --seed 20261104
```

The pinned original (`extracted/exefs/code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) and the
production C++ staged at `0x001078D8` matched in all 140 direct fixtures with
explicit stop/fault assertions, and four compositions through original caller
`0x0010B578`. The cases cover all rows,
availability zero/nonzero normalization, mask match/miss, row-gate resets,
unavailable retention, wraparound, and the untouched row 31. The loop-bound
mutation was detected. The helper receives the original handle and fixed state
pointer. Exact-slot IPS replay passed, with no changes outside the 164-byte slot.

The affected translation unit compiled with:

```powershell
python tools/build_check.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-001078d8-counter-refresh-cpp/run005/checks/tu --tu src/engine/leaf_batch27_a.cpp --jobs 1
```

The current reports, IPS, and staged image are under the `run009/checks` paths
above. The offline evidence and compilation do not claim full runtime
equivalence.

## Independent review

The first independent review found and documented the unmapped-sentinel bug;
that review is retained as historical evidence in the [review report](h2-001078d8-independent-review.md).
The follow-up review accepted the repaired runner against two fresh seeds
(`20261421`, `20261422`), each passing 140 direct cases and four caller
compositions with explicit successful returns, mutation detection, and
exact-slot IPS replay. Physical input provenance, scheduling/cadence, and
runtime behavior remain open.
