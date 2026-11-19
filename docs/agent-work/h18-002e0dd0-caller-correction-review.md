# Independent caller correction review: `0x002e0dd0`

Task: `h18-002e0dd0-caller-correction-review`; owner `luna_probe_review`.

## Branch bytes and return mapping

The pinned input `extracted/exefs/code.bin` has SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Capstone disassembly of the actual bytes at `0x003bc074..0x003bc088` is:

```text
0x003bc074: cmp     r0, #5
0x003bc078: movne   r0, #0
0x003bc07c: bne     #0x3bc02c
0x003bc080: add     sp, sp, #0x14
0x003bc084: mov     r0, #0x11
0x003bc088: pop     {r4, r5, r6, r7, pc}
```

The raw words confirm `0x003bc028` is `mov r0,#0x81` (`0xe3a00081`), while the actual branch target `0x003bc02c` is `add sp,sp,#0x14` (`0xe28dd014`). Therefore the non-5 path first writes `r0=0` at `0x003bc078`, branches over the `0x81` assignment, and preserves zero through the stack adjustment and pop. The 5 path does not take BNE and returns `0x11`. The earlier candidate-review statement that the branch target itself returns `0x81` was wrong; the corrected caller-fix note/function record's 0 mapping matches the bytes.

A full raw-byte slice and decoded disassembly are saved in `reports/branch-disassembly.txt` under this run.

## Fresh offline execution

Executed the current runner against the hash-pinned original and current candidate:

- `python tools/h18_002e0dd0_experiment.py --image extracted/exefs/code.bin --output build/agent-work/batch-h18-001/h18-002e0dd0-caller-correction-review/run-001/checks/fresh-seed-20261118 --seed 20261118 --samples 8` — exit 0.
- `python -m unittest tests.test_h18_002e0dd0_experiment -v` — exit 0, 1 test passed.

Fresh report `checks/fresh-seed-20261118/report.json` reports 33/33 direct cases passed, all three caller compositions passed, and all three negative controls detected. Both `ui_func_003bbfb0` continuations are composed from the actual BL at `0x003bc070`: gate result 0 returns 0 in both original and candidate; gate result `0x80000000` returns `0x11` in both. The ignored-result caller at `0x003bbdfc` also reaches its continuation in both executions; it overwrites `r0`, as expected for an ignored wrapper result. The harness compares caller-visible preserved registers, SP, PC, fixture memory, and helper trace. This is offline Unicorn instruction execution against modeled helper hooks, not an emulator runtime.

All three mutant controls were caught: nonzero-vs-bit31 gate, wrong first value key, and wrong forwarded fifth argument. Candidate object has no unresolved relocations per the runner's compile gate. Candidate code size is 160 bytes, larger than the 140-byte first-body span; it remains experimental and is not suitable for in-place replacement at that address without separate placement/layout work.

## Reporting issue and limits

The runner's caller result currently reports `stop: 0x1001000` for every case. This is correct for the two `ui_func_003bbfb0` cases, which stop at synthetic LR, but mislabeled for the ignored-result case: that execution actually uses stop `0x003bbe18`. The comparison does reach and compare the actual stop PC because `execute(..., stops=(stop,))` receives `0x003bbe18`; the incorrect field comes from a later name check comparing `name` to `ui_func_003bbdb8` while the actual name is `ui_func_003bbdb8_ignored_result`. This is a report-label defect, not a counterexample to the branch/return mapping. Correct it before relying on the stop field in future reports.

The harness injects the candidate at the wrapper entry, uses a configurable gate and synthetic count/value/cleanup helper hooks, and supplies synthetic globals/objects. It does not validate the real helpers' side effects, each caller's pre-call setup, application state, production placement, or whole-game behavior. No emulator/runtime comparison was performed.

## Recommendation

Accept the correction `non-5 -> 0`, `5 -> 0x11` for this caller continuation based on the exact pinned bytes and fresh offline differential caller execution. Keep the function candidate experimental until helper contracts and production placement are separately established. Correct the mislabeled ignored-caller `stop` field in a later runner-maintenance task.
