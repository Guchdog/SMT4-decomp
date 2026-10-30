# H2 Calc, Draw, and Secondary final-address placement — run-012

## Result

The reviewed 292-byte production `TitleConfig_Secondary` body is placed at `0x003FEED4` in the remaining `.text` page-tail cave. Its original entry at `0x002CAEF0` branches directly to that body. The Calc body remains at `0x003FE624`; the Draw helper and `%s\0` remain at `0x003FEE54` and `0x003FEED0`. The complete payload ends at `0x003FEFF8`, leaving 8 bytes in the 2,524-byte cave.

The coordinator-owned builder emits one merged image and IPS from the pinned original, applies the known Calc local `R_ARM_ABS32` relocations and Draw helper-call/string relocations, and verifies that Secondary has zero ELF relocations. IPS roundtrip and changed-byte authorization checks pass. This is offline evidence for the three callback bodies and the title caller's registration/gate composition. It does not establish scheduler execution, visible UI, persistence, or runtime behavior.

## Image and patch map

- Original `code.bin`: 3,633,152 bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Patched image: `build/agent-work/H2-semantic/h2-secondary-final-placement/run-012/combined-build/code.combined.bin`, SHA-256 `84c6eb66a6f9a2a23d46e08df4eb04d723fef852c0b8bd3405945f9dbdd5ae32`.
- Serialized IPS: `build/agent-work/H2-semantic/h2-secondary-final-placement/run-012/combined-build/code.combined.ips`, SHA-256 `f5369e77ddfe48f93d46ffbb8670819cc432039589c51aac6e6c67af9d9b8376`.
- Manifest: `build/agent-work/H2-semantic/h2-secondary-final-placement/run-012/combined-build/manifest.json`, SHA-256 `28de5a9c2530792dc7307c657d814af86bf6affa6e1404972a78e62a12a536fc`.
- The final cave map is Calc `[0x003FE624,0x003FEE54)`, Draw helper `[0x003FEE54,0x003FEED0)`, `%s\0` `[0x003FEED0,0x003FEED3)`, alignment padding through `0x003FEED4`, and Secondary `[0x003FEED4,0x003FEFF8)`. The rounded payload ends at `0x003FEFF8`; the page boundary is `0x003FF000`.
- IPS records are Calc entry branch at file offset `0x000EA928` (4 bytes), Draw main at `0x001CAFD0` (1,464 bytes), Secondary entry branch at `0x001CAEF0` (4 bytes), and the full audited cave `[0x002FE624,0x002FF000)` (2,524 bytes). Reapplying the serialized IPS reproduced the image exactly; all changed bytes fall within those four authorized records.
- Production Secondary TU SHA-256 `3ca4676613634ae91fe980e5e6e3c79fa74aff355e0facc50149749ba10b9c37`; production object SHA-256 `e04b6dcb9ae560efa2e39202b04763263b03f1f61455efe5b54756ffda81d53e`; extracted symbol `engine_func_002caef0` is 292 bytes with no relocations.

## Final-address differential

Command:

```powershell
python tools/h2_combined_offline_validation.py --original extracted/exefs/code.bin --patched build/agent-work/H2-semantic/h2-secondary-final-placement/run-012/combined-build/code.combined.bin --manifest build/agent-work/H2-semantic/h2-secondary-final-placement/run-012/combined-build/manifest.json --output build/agent-work/H2-semantic/h2-secondary-final-placement/run-012/final-validation --seeds 7 20261024
```

Exit code 0. Report SHA-256 `2d7a40f720cd5ca994423c2b7e4fe712a8f85517231f8cc1edcede77036fc968`.

- Draw: 46/46 directed cases pass; wrong-helper-target-plus-four control is detected.
- Calc: 16/16 persistent sequences and 54/54 ticks pass across seeds 7 and 20261024; wrong logical-map control is detected.
- Secondary: 34/34 cases pass across the same seeds. Cases cover both counters and individual boundaries, nullable slots, task registration predicate, manager halfword 9–12, and distinct simultaneous loop counts.
- The production Secondary path is exercised at its final cave VMA. A compiled wrong-count mutant placed at that same VMA, reached through the patched entry branch, is detected on `both-loops-distinct`.
- The Secondary helper at `0x002B9008` is modeled for its direct manager-halfword effect. Script cleanup, releases, task registration internals, and task-state/scheduler effects remain explicit trace-only helper models.

## Caller composition

Command:

```powershell
python tools/h2_offline_caller_composition.py --patched-image build/agent-work/H2-semantic/h2-secondary-final-placement/run-012/combined-build/code.combined.bin --output build/agent-work/H2-semantic/h2-secondary-final-placement/run-012/caller-composition
```

Exit code 0. Report SHA-256 `74f83e4caf3c0af5a44509dd080c618936065a05cef32f05eed0291f9d86309f`.

All 3 State-9/10 caller cases pass, and the wrong-primary-Calc-callback-address control is detected. The runner compiles and injects the separate initializer experiment candidate at synthetic VMA `0x01004000`; it does not execute the newly readable production initializer or its proposed `.rodata` pool. It compares task registration tuples and work/handle linkage, but does not schedule or execute Calc, Draw, or Secondary callbacks.

## Limits and next work

- Secondary's 8-byte cave margin permits no additional code/data payload. Any later code placement must use another verified range or revise this map.
- `config/functions.csv` records Calc, Draw, and Secondary as `non_matching`; the classification truthfully describes their changed source/image bytes. It is not a claim of whole-function or title equivalence.
- The initializer is independently reviewed as an exact 572-byte production symbol and now has a separate 68-byte `.rodata` string-pool placement proposal. It is not included in this merged image. Its production-object differential and exact-image caller composition remain required.
- The ready-gate source currently compiles to 56 bytes against a 52-byte original span. It is not included in this image while a size-reduction attempt is underway.
- No Azahar CLI/GDB runtime, visible screen comparison, input/edit/cancel/confirm scenario, save/persistence test, or restart test was run. The task scheduler never invoked the registered Secondary callback in these offline runs.

Next, integrate and differentially test the production initializer with the string-pool record, resolve the ready-gate span, then run one coordinator-owned wider offline closure before resuming the authorized Azahar CLI attempt.
