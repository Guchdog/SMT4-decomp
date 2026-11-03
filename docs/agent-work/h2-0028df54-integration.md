# H2 `0x0028DF54` batch closure

The coordinator froze the reviewed helper, candidate, and runner, then compiled
the complete ARMv6K source set:

```powershell
python tools/build_check.py --repo-root . --out-dir build/agent-work/H2-semantic/h2-helper-0028df54-integration/run001/full-build -j 8
```

Result: **204/204 translation units succeeded**, zero reused objects, eight
workers, 10.71 seconds. Outputs are under the ignored `build/` tree.

Offline evidence is in [run013](h2-0028df54-run011.md): 102 direct cases and
eight original `0x00286928` selector-6/state-5 compositions, each comparing the
pinned original, experimental candidate, and compiled production body. A
wrong-byte-value mutant was detected in all direct and caller cases. The
independent [run004 review](h2-0028df54-independent-review-run012.md) freshly
replayed the matrix with another seed and accepted final-state equivalence for
stable, disjoint fields in ordinary RAM.

Production emits the two stores in the opposite order from original ARM. The
classification remains `non_matching`, and the evidence does not extend to
MMIO, concurrent observers, invalid-pointer faults, other `0x00286928` branches,
runtime lifecycle, or full H2 equivalence.
