# H2 `0x0011C5EC` production C++ conversion

## Scope

This conversion replaces the 304-byte ARM input-state reader with typed C++ and
retains its seven original callees. It claims only the bounded ordinary-memory
behavior documented in the [function record](../function-records/0x0011c5ec.md).

## Validation

```powershell
python tools/h2_11c5ec_experiment.py --out build/agent-work/H2-semantic/h2-input-state-reader-cpp-0011c5ec/run001/checks/direct --seed 20261110
python tools/build_check.py --out-dir build/agent-work/H2-semantic/h2-input-state-reader-cpp-0011c5ec/run001/checks/tu --tu src/engine/leaf_batch30_a.cpp --jobs 1
```

The `--seed` argument controls the random context, output, and ring sample bytes
for each deterministic branch-matrix fixture, so independent seed values vary
those data while preserving branch coverage. The pinned image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The
production body is 304/304 bytes, has seven `R_ARM_CALL` relocations to even ARM
entries, and passes 288 direct comparisons, 32 original-caller compositions,
three mutation controls, exact-slot IPS replay, and affected-TU compilation.
The ring-reader dependency is controlled in the direct runner; the other six
direct callees execute pinned original code. Compiler barriers preserve the
originally observed ordering of state/context stores and emit no instructions.

The differential is limited to valid, disjoint synthetic ordinary memory.
Physical input identity, cadence, scheduling, alias/fault/concurrency behavior,
and runtime behavior remain unverified. This is not whole-title equivalence.
