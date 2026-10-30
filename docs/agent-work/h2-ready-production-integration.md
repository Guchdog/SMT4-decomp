# H2 READY production integration

## Result

Replaced only `ui_func_002fc0ec` in `src/engine/leaf_batch26_b.cpp` with a readable C++ predicate preserving the no-argument return-in-`r0` contract: return ready for a null global work pointer; otherwise pass `work->calc_task` (including null) to original helper `0x002BF41C` and return the inverse of its registered result.

The production source now expresses the correct predicate, but its compiled production symbol is **56 bytes**, four bytes larger than the pinned `[0x002FC0EC,0x002FC120)` 52-byte span. It has no relocations. The body was not truncated or relocated; no image patch or safe production placement is claimed. This is a placement blocker for the in-place production replacement.

## Build and symbol identity

Command (exit 0):

```powershell
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch26_b.cpp --out-dir build/agent-work/H2-semantic/h2-ready-production-integration/run-001/checks/production-tu --jobs 1 --force
```

Clang 23.1.3, ARMv6K hard-float. Object:
`build/agent-work/H2-semantic/h2-ready-production-integration/run-001/checks/production-tu/engine/leaf_batch26_b.o`

- Production TU SHA-256: `27365ab1cb211824d933186ca6231dd3c5682fcd6f7ac5d2c9ba186d0e82ecc8`
- Object SHA-256: `76a169e7a9cfa0442b75fc15e9c25303973e7ae4b5a9726bdf534c4f6c48a392`
- Exact extracted symbol `ui_func_002fc0ec`: 56 bytes, SHA-256 `1f36fd8cadd763ebd4d2e1a64cdf3d9334a6bd5baaebb58e5f20e59a7b73730c`
- Relocations: none
- Pinned reference image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`

## Focused production-symbol differential

Ran `python build/agent-work/H2-semantic/h2-ready-production-integration/run-001/checks/production-symbol-differential.py` (exit 0). It extracted the exact production symbol and compared it to the pinned original at the runner's synthetic injection address. All four directed cases passed: null global, registered task, unregistered task, and null task forwarded. Original and production symbol matched return value, return PC, helper trace, SP, `r4-r11`, and `d8-d15`. A deliberate `mov r0,#1; bx lr` always-ready result control was rejected on the registered-task case (`return differs`).

Report: `build/agent-work/H2-semantic/h2-ready-production-integration/run-001/checks/production-symbol-differential.json`, SHA-256 `abf746aff42817fa1cb3103d9d80573c17f6e72ec2e98a8ac58ee550cc7aac9b`.

Focused harness tests: `python -m unittest tests.test_h2_ready_experiment -v` (exit 0, 7 tests).

## Limits and next action

The helper at `0x002BF41C` is intercepted with an explicit identical registration model; helper internals and task-list lifecycle are not executed in this differential. The production body runs at the synthetic injection address, not its final VMA. There is no caller-composition or runtime evidence. The exact 52-byte span does not fit the 56-byte symbol, so coordinator review must decide whether to optimize the readable implementation under the same frozen inputs, assign an approved alternate placement, or restore the original production wrapper and retain the readable version as an experimental candidate. Do not truncate the body. No ledger edit was made; because source now differs from the pinned assembly, the coordinator must reconcile the `matching` classification before any promotion.
