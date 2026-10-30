# H2 TitleConfig_Secondary production-source integration

## Result

Replaced only the ledgered `engine_func_002caef0` assembly wrapper in `src/engine/leaf_batch32_c.cpp` with readable C++. The implementation preserves its no-argument C entry / `void` callback ABI, reads `g_TitleConfigWork` through `0x0044E2D0` without adding a null guard, sets byte `work+4`, performs the two signed-halfword reread loops, releases and clears the three conditional resource slots in original order, gates task state 0 on `0x002BF41C`, then reloads/releases/clears the global work pointer.

The helper entries remain original absolute-address dependencies: `0x002B9008`, `0x002A755C`, `0x002C4360`, `0x002BF41C`, and `0x002C45B8`. The new source remains in the existing ledger TU and symbol; no header, runner, patch builder, or ledger edit was made by this task. In particular, the current `config/functions.csv` change is the coordinator's separate Draw reclassification; the Secondary row remains `0x002caef0,224,matching,engine,engine_func_002caef0,src/engine/leaf_batch32_c.cpp`.

## Production TU build and symbol extraction

Command:

```powershell
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch32_c.cpp `
  --out-dir build/agent-work/H2-semantic/h2-secondary-production-integration/run-001/checks/production-tu `
  --jobs 1 --force
```

Exit code: 0. Compiler: Clang 23.1.3, target ARMv6K hard-float with the repository flags in the object manifest. The focused object is `build/agent-work/H2-semantic/h2-secondary-production-integration/run-001/checks/production-tu/engine/leaf_batch32_c.o`, SHA-256 `e04b6dcb9ae560efa2e39202b04763263b03f1f61455efe5b54756ffda81d53e`. Extracting exact symbol `engine_func_002caef0` from that object yielded 292 bytes and no relocations. The current translation-unit SHA-256 is `3ca4676613634ae91fe980e5e6e3c79fa74aff355e0facc50149749ba10b9c37`.

The production symbol is 8 bytes larger than the 284-byte experimental candidate and exceeds the task's 284-byte target. It has zero unsupported relocations. The reviewed Calc+Draw map records 300 bytes after the Draw helper and format string; raw arithmetic would leave 8 bytes if this 292-byte body were placed there. This is only a size comparison, not a claim that the combined cave layout or final branch patch fits: no Secondary cave patch, placement manifest, relocation/branch application, final-address run, or merged IPS was built here.

## Production-symbol differential

The exact extracted production symbol was run against the pinned original through the existing Secondary differential's matched explicit helper-entry models, injected at that runner's synthetic candidate address. The task-local report is `build/agent-work/H2-semantic/h2-secondary-production-integration/run-001/checks/production-symbol-differential.json`, SHA-256 `36703fdd9dac8f228ea178e3fcd85273aadc4b60df7c0a481e094cdc38d9ce99`.

All 17 directed cases passed: both zero counters; each counter independently negative, one, and four; independent positive counters 2 and 3; each nullable cleanup slot; task predicate false/true; and manager halfword values 9, 10, 11, and 12. The report records the source, production object, symbol, and reference hashes; there was no first counterexample. This reuses the existing helper models, including the direct modeled manager-halfword effect for `0x002B9008` and trace-only models for `0x002A755C`, `0x002C4360`, and `0x002C45B8`.

This is production-source ARM differential evidence at a synthetic address. It does not test the new body at an assigned final VMA, a cave branch from `0x002CAEF0`, the merged Calc/Draw/Secondary image, task scheduling, callback timing/count, resource freeing, work lifetime, runtime UI, or persistence. The earlier candidate's wrong-call-count and wrong-release-order negative controls remain candidate-level evidence; no production-symbol mutant was exercised in this task.

## Next action and limits

Freeze this TU for independent production review. Before any integrated patch, the coordinator should resolve the exact remaining cave interval and account for the 292-byte body plus its entry branch and any alignment, then build a reproducible combined artifact and rerun the Secondary differential at the final VMA. A caller/scheduler test must separately establish when the secondary callback executes and how task/work/resources are retired. Keep runtime and persistence claims open. The experiment does not justify changing the original 224-byte ledger extent or calling the production bytes `matching` after a future promotion.
