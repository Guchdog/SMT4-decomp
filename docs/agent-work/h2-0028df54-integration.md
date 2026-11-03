# H2 `0x0028DF54` batch closure

After the production helper was updated to preserve the original store order,
the coordinator froze the source, candidate, runner and reviewed evidence, then
compiled the complete ARMv6K source set:

```powershell
python tools/build_check.py --repo-root . --out-dir build/agent-work/H2-semantic/h2-helper-0028df54-integration/run002/full-build -j 8
```

Result: **204/204 translation units succeeded**, zero reused objects, eight
workers, 11.71 seconds. Outputs are under the ignored `build/` tree.

Offline evidence is in [run014](h2-0028df54-run011.md): 102 direct cases and
eight original `0x00286928` selector-6/state-5 compositions, each comparing the
pinned original, experimental candidate, and compiled production body. A
wrong-byte-value mutant was detected in all direct and caller cases. Original,
candidate and production bodies also matched the exact byte-then-word write
order. The independent [run005 review](h2-0028df54-independent-review-run014.md)
freshly replayed the matrix with another seed and verified both direct and
caller paths against all three bodies.

The production function remains classified `non_matching`. Volatile stores
preserve observable order for this implementation, but do not establish
thread-safety or MMIO suitability. Invalid-pointer faults, other `0x00286928`
branches, runtime lifecycle, and full H2 equivalence remain outside the tested
scope.
