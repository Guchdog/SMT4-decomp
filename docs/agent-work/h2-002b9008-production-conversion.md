# H2 shared helper `0x002B9008` production C++ conversion

## Scope

This replaces only the shared manager halfword helper with typed C++.
`TitleConfig_Secondary` calls it while processing its two signed counters, but
the helper changes a separate manager field and does not drain those counters.
Other camp/UI callers share the same original entry.

## Validation

```powershell
python tools/h2_b9008_experiment.py --out build/agent-work/H2-semantic/h2-manager-counter-adjust-002b9008/run001/checks/direct --seed 20261118
python tools/build_check.py --out-dir build/agent-work/H2-semantic/h2-manager-counter-adjust-002b9008/run001/checks/tu --tu src/engine/leaf_batch23_b.cpp --jobs 1
```

The replacement is 36/36 bytes, has no relocations, and retains the raw original
`r0` value while preserving the void interface. Thirty-two final-VMA fixtures
matched the pinned original. Two compiled negative controls were detected.
The exact-slot IPS replay passed, and only the original 36-byte slot changed.

Valid mapped ordinary memory is the tested domain. Invalid pointers, aliasing,
concurrency, MMIO, scheduler behavior and wider manager lifecycle are not
established. The test does not claim whole H2 runtime equivalence.
