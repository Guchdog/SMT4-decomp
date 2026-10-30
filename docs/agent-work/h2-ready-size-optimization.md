# H2 READY size optimization

## Result

No safe source-only reduction from the previously reviewed 56-byte readable implementation to the pinned 52-byte span was found. I tried spelling the boolean inversion as `return !registered;`; Clang emitted the exact same 56-byte symbol. I restored the prior ternary source, leaving the full production function intact and untruncated. Its source hash is unchanged from the start of this task.

No raw PC-relative branch, unsupported relocation, alternate placement, or truncation was introduced. The production wrapper still does not fit its 52-byte in-place extent. This task is blocked on reducing code size under the same contract or a coordinator decision about restoring/retaining the experimental candidate outside production.

## Final production build

Command (exit 0):

```powershell
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch26_b.cpp --out-dir build/agent-work/H2-semantic/h2-ready-size-optimization/run-001/checks/production-tu --jobs 1 --force
```

Clang 23.1.3, ARMv6K hard-float.

- Source SHA-256: `27365ab1cb211824d933186ca6231dd3c5682fcd6f7ac5d2c9ba186d0e82ecc8`
- Object: `build/agent-work/H2-semantic/h2-ready-size-optimization/run-001/checks/production-tu/engine/leaf_batch26_b.o`
- Object SHA-256: `76a169e7a9cfa0442b75fc15e9c25303973e7ae4b5a9726bdf534c4f6c48a392`
- Exact symbol `ui_func_002fc0ec`: 56 bytes, SHA-256 `1f36fd8cadd763ebd4d2e1a64cdf3d9334a6bd5baaebb58e5f20e59a7b73730c`
- Relocations: none
- Pinned image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`

The emitted symbol remains four bytes larger than `[0x002FC0EC, 0x002FC120)`. There is no in-place fit or placement claim.

## Focused validation

The exact extracted production symbol passed the four directed cases (null global, registered task, unregistered task, and null task forwarded) at the runner's synthetic injection address. Return value, return PC, helper trace, SP, `r4-r11`, and `d8-d15` matched. The always-ready result control was detected on the registered-task case. The task-local report is `build/agent-work/H2-semantic/h2-ready-size-optimization/run-001/checks/production-symbol-differential.json`.

Command (exit 0):

```powershell
python build/agent-work/H2-semantic/h2-ready-size-optimization/run-001/checks/production-symbol-differential.py
```

The focused harness suite passed 7/7:

```powershell
python -m unittest tests.test_h2_ready_experiment -v
```

The helper `0x002BF41C` remains modeled with an explicit registered/unregistered result; the differential does not execute task-list internals. The symbol is not run at a final production VMA, and no caller composition, scheduler lifecycle, emulator/runtime, persistence, or restart behavior is established.

## Next action

Keep the function untruncated. Coordinator/reviewer should decide whether to authorize another semantically justified source reduction with fresh evidence, restore the previous production wrapper and retain the reconstruction experimentally, or explicitly broaden the production placement task. Reconcile ledger classification before any production promotion.
