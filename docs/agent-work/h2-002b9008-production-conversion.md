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

## Current-TU refresh

The original run001 is tied to an earlier `leaf_batch23_b.cpp` hash. Run002
recompiled the current TU and repeated the same final-VMA suite with seed
`20261120`; all 32 cases and both mutations passed, and the affected TU built.
Current object SHA-256 is
`8b4be8a9e2193fc9c11fcca7f3d66ec4d386403044255fc032a386ba19f12625`; staged
image SHA-256 is `9efadb93e56b09f34bb50e0446815d2b8b66cd5a54bc941f227e855006ab51be`;
IPS SHA-256 is `ff9265eba1f390a8afb56d2034045e72679a5e7c9a4d3fa51a9a934af8c1807c`.
The current run002 was independently reviewed with a fresh seed; that review
accepted the bounded direct behavior and preserved the valid ordinary-memory
and caller-lifecycle limits above. See the [independent review](h2-002b9008-independent-review.md).
