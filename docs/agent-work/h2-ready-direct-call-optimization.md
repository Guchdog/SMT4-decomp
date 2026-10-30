# H2 READY direct-call optimization

## Result

Updated only `ui_func_002fc0ec` in `src/engine/leaf_batch26_b.cpp` to call the existing C-linkage helper `battle_func_002bf41c(void*)` directly. The predicate still returns 1 for a null global without calling the helper; otherwise it forwards `work->calc_task`, including a null handle, and returns the inverse of the helper's boolean-like result.

The production symbol is 48 bytes, within the pinned 52-byte span. It has one accepted ARM-state `R_ARM_CALL` relocation at offset 28, naming exactly `battle_func_002bf41c`, with the canonical unresolved branch word `0xEBFFFFFE` and no explicit addend. No other relocations are present.

## Build identity

Command (exit 0):

```powershell
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch26_b.cpp --out-dir build/agent-work/H2-semantic/h2-ready-direct-call-optimization/run-001/checks/production-tu --jobs 1 --force
```

Clang 23.1.3, ARMv6K hard-float.

- Pinned reference image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Source SHA-256: `609aaf963db8129a560293c8d1e65b3c6df8fa016673d28b0143535dadb4e4ee`
- Object `build/agent-work/H2-semantic/h2-ready-direct-call-optimization/run-001/checks/production-tu/engine/leaf_batch26_b.o`, SHA-256 `2c0ca7a51729389cce55cf31476f9a3075b50b3b4ef3cabebba9cffe0382b37d`
- Extracted symbol `ui_func_002fc0ec`: 48 bytes, SHA-256 `d43275ec3a230ed2b038098437f7baa314794b09aadcbd697a35c3f5f8136332`
- Unresolved relocation: offset 28, type 28 (`R_ARM_CALL`), symbol `battle_func_002bf41c`, implicit addend only.

## Final-VMA differential

The task-local script accepts only the exact relocation above and resolves it at production VMA `0x002FC0EC`. The branch site is `P=0x002FC108`, target `S=0x002BF41C`, and the applied instruction is `0xEBFF0CC3`; decoding it targets exactly `0x002BF41C`. It then runs the exact extracted production symbol at that VMA against the pinned original callback, with the helper intercepted by the same explicit registered/unregistered model in both runs.

Command (exit 0):

```powershell
python build/agent-work/H2-semantic/h2-ready-direct-call-optimization/run-001/checks/final-vma-production-differential.py
```

All four directed cases passed: null global, registered task, unregistered task, and null task handle forwarded. The comparator checked return value, return PC, helper trace, SP, `r4-r11`, and `d8-d15`. An always-ready result control was rejected on the registered-task case (`return differs`). Report: `build/agent-work/H2-semantic/h2-ready-direct-call-optimization/run-001/checks/final-vma-production-differential.json`, SHA-256 `eea2f9a6c73d3c9ef8b39fcaebd3dba5f20dae3fb0e0633c596a01b17cdb9835`.

The focused harness suite also passed 7/7 tests with `python -m unittest tests.test_h2_ready_experiment -v`.

## Limits and next action

The helper body is modeled, not executed; task-list internals and scheduling are not covered. This is an isolated final-VMA callback differential, not a merged image patch, title caller composition, or runtime test. No emulator, input, persistence, or restart evidence was produced. The direct-call relocation was resolved in a task-local script only; shared patching/linker integration was not changed. The coordinator should independently review the source, relocation handling and production ledger classification before integration.
