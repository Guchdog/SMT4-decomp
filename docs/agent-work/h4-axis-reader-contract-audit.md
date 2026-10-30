# H4 axis reader contract audit — run 001

## Disposition

The experimental C++ candidate for `0x0027FBC8` matched the pinned original in all 144 valid synthetic direct-call cases in the expanded matrix. Two additional invalid-output-pointer probes faulted on the same unmapped write in both implementations and issued the same write sequence; post-fault scratch-register values are excluded from the semantic comparison because these pointers are outside the valid caller domain. A same-input mode-2 mutation control detected the intentionally widened upper-mode bound. This supports continued experimental/caller-composition work; it does not establish full ABI, hardware, production-integration, player-movement, or runtime equivalence.

## Frozen inputs and provenance

The prepared task packet is `build/agent-work/H4-semantic/h4-axis-reader-contract-audit/001/task.json`. Its declared input hashes were checked before the successful rerun; all 15 matched. The pinned original `extracted/exefs/code.bin` has SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The unchanged candidate source `experiments/semantic_equivalence/h4_axis_reader_candidate.cpp` has SHA-256 `108b45003ec4908630514b615be7ebe6911fddb83c7448e4a8dacc403dd85aca`. Prior seed-7, seed-20261028, and camera-002 reports retained their packet hashes. Their existing output directories were left untouched.

The successful expanded run compiled a fresh candidate object to the new ignored output directory. The candidate source hash remained unchanged. The report records code, source, tool, object, linked-candidate, mutant, and helper-relocation identities. No emulator was launched and no save/profile files were read or changed.

## Coverage and results

Command:

```text
python tools/h4_axis_reader_experiment.py --audit-contract --seed 42 --out-dir build/agent-work/H4-semantic/h4-axis-reader-contract-audit/001/checks/contract-042-r3
```

Exit code: `0`. AST parsing also passed. The fresh report is `build/agent-work/H4-semantic/h4-axis-reader-contract-audit/001/checks/contract-042-r3/contract-audit-report.json`, SHA-256 `2c110c39d9e04e826a5772a566229ab750b3ab2c6f710c99ed45846df6cf6a0d`.

The 146 cases cover mode/max boundaries; calibration selectors; flags; signed halfword extremes; zero, positive, negative-zero, NaN, and infinite thresholds; deadzone boundaries; null outputs; equal, swapped, and state/calibration/sample aliases; zero and reversed spans; and 100 seeded cases. For valid mapped cases the harness compares return/output values, helper calls, selected memory snapshots, ordered non-stack writes, preserved `r4-r11`, preserved `d8-d15`, and FPSCR. It counts stack writes but deliberately does not compare compiler-dependent scratch-stack layouts.

Result: 144 valid cases had no difference. The two invalid-pointer probes produced the same `UC_ERR_WRITE_UNMAPPED` class and same write sequence in original and candidate: invalid X writes `0x3e800000` to `0xfffffff0`; invalid Y first writes `0x3e800000` to valid X, then `0xbf000000` to `0xfffffff0`. They remain fault probes, not evidence of supported invalid-pointer behavior. The initial strict comparator also saw different post-fault PC/temporary-register values; the runner now reports these separately instead of misclassifying them as valid-domain semantic counterexamples.

The same-input negative control used mode `2`, max `2`, and the identical three-sample fixture in original and mutant. It changed candidate instruction `CMP r2,#1` at candidate offset `0x30` (`0xE3520001`) to `CMP r2,#2` (`0xE3520002`). The original rejected mode 2 without output writes; the mutant accepted it and wrote two zero outputs. The harness detected the difference. This validates sensitivity to the unsigned upper-mode boundary without modifying the candidate source.

## Limits and next action

The direct-call fixtures use synthetic mapped globals and execute the original deadzone helper at `0x0019FE4C`. The existing camera caller-composition evidence is separate; this audit did not rerun it. The candidate remains experimental and unintegrated. Pointer-fault equivalence is only the observed Unicorn fault/write trace. No claim is made about all registers, full memory, real hardware, concurrency, player-control meaning, or whole-game behavior.

Next: independent review this audit and handoff. Keep production promotion gated on the reviewed caller contract, reproducible integrated replacement/build, and defined original-versus-patched runtime scenario.
