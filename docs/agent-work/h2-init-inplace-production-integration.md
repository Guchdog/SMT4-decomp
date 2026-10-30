# H2 initializer in-place production source — run-001

## Result

The production definition of `titleConfig_func_002f4ca0` in `src/camp/title_flow.cpp` is now a readable C++ implementation in the original 572-byte slot at `0x002F4CA0`. It uses the four audited string addresses in the read-only `.rodata` tail:

| Pointer | String |
| --- | --- |
| `0x0042AB78` | `TITLE_CONFIG_MAIN` |
| `0x0042AB8C` | `TITLE_CONFIG D` |
| `0x0042AB9C` | `camp/config.bf` |
| `0x0042ABAC` | `camp/config.mbm` |

The source SHA-256 is `11b5360c77aecb4ab0e510774fd42a1cb479e8343aff4bb1a30d4cadeccc1b5e`. Existing allocator, task, sprite/cursor, async table, sound, UI reset, mapper, fill, and pair-copy functions remain original helper dependencies. There is no new null check, task scheduling, or async-readiness assumption.

The frozen header declares the entry `void`. To keep that declaration and preserve the original tail-call's observable `r0`, the source explicitly moves the pair-copy helper's result back into `r0`; three ARM NOPs keep the extracted body at the original slot length. The compiler output contains no ELF relocations for this symbol.

## Build evidence

Successful exact command:

```text
python tools/build_check.py --repo-root . --tu src/camp/title_flow.cpp --out-dir build/agent-work/H2-semantic/h2-init-inplace-production-integration/run-001/checks/production-tu --jobs 1 --force
```

Exit code: `0`. Compiler: Clang 23.1.3, ARMv6K hard-float, `-O2`, one compiler job. Fresh object: `build/agent-work/H2-semantic/h2-init-inplace-production-integration/run-001/checks/production-tu/camp/title_flow.o`, SHA-256 `432664ba70073ff98c2fed19559d4f663f0e4dd9732c519e1bf66eda4dcfe82d`.

Extracted symbol `_ZN4smt44camp25titleConfig_func_002f4ca0EPv`:

- Size: 572 bytes, exactly the original `[0x002F4CA0,0x002F4EDC)` slot.
- Relocations: none.
- Symbol-body SHA-256: `5d77e804a00fbb2d670e0c42e15ba2a61bb6362387fde008eaf8f79562aa8c4b`.

An initial compile attempt with a `u32` definition was rejected because the frozen header declares the function `void`. The definition was corrected to preserve the header ABI and explicit `r0` behavior; the successful build above is from the corrected source.

## Focused validation and limits

`python -m unittest tests.test_h2_init_orchestration_experiment -v` exited `0` (3 tests). Those tests exercise the existing experiment runner's case construction, trace projection, and mutation detector. They do not compile or execute this production symbol.

The existing `tools/h2_init_orchestration_experiment.py` accepts the pinned image and compiles the separate experiment candidate; it does not accept a production object or relocated string-pool map. Its prior two-seed ARM differential and wrong-count control therefore remain candidate-only and are not reused as production differential evidence. A compatible production-object original-vs-compiled runner was unavailable within this task's write lease. No production differential, caller-composed test, patch application, or runtime/emulator test was run.

The source edit is not byte-identical to the pinned original. `config/functions.csv` was outside the assigned write paths and was left unchanged; its current `matching` label is stale for this source and requires coordinator correction before any promotion or global reporting. This handoff does not establish `.rodata` page permissions at runtime, final image/patch placement, helper behavior beyond the frozen contracts, scheduling, async completion, UI input, persistence, or whole-game equivalence.

## Frozen-input check

Before editing, all hashes in run-001 `task.json` matched, including the writable baseline hash for `src/camp/title_flow.cpp`. After implementation, every declared `input_sha256` read input still matches its packet hash. The only changed task write path among the tracked source/docs is the production source; the function record and this report are the other owned writes. No board, shared runner, header, ledger, patcher, canonical build output, or emulator state was changed by this task.

## Next action

Coordinator should update the ledger classification to a supported non-matching label, then provide an object-aware differential harness or bounded production-image patch route. A reviewer should verify call order, the `r0` preservation shim, the exact string VMA mapping, and the in-place slot/relocation result before caller composition or promotion.
