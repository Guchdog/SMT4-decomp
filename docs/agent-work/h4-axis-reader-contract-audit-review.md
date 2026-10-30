# H4 axis-reader contract audit review

## Disposition

The expanded direct audit is acceptable evidence for its stated synthetic domain, with two invalid-pointer probes retained strictly as observed Unicorn fault/write traces. The same-input mode-2 mutation control is sensitive to the candidate's unsigned upper-mode boundary. I independently reran the frozen audit logic at seed `20261029`; it again passed 146 cases with no valid-domain differences and detected the mutation. This supports continued experimental and caller-composition work, not production or whole-runtime equivalence.

All 17 declared inputs in the outer review packet match. The underlying run-001 audit packet's 15 input hashes and its handoff report hash also match; the candidate and frozen runner snapshots are pinned and unchanged. Key identities:

- Original `code.bin`: SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Candidate source: `108b45003ec4908630514b615be7ebe6911fddb83c7448e4a8dacc403dd85aca`.
- Frozen audit runner snapshot: `312ef698ca68a1a66bb47756fd963e832f2d1617410f9d1a3a8384602a5d9855`.
- Original audit report: `2c110c39d9e04e826a5772a566229ab750b3ab2c6f710c99ed45846df6cf6a0d`.
- Independent seed-20261029 report: `ee67de5be35d402aa01afa60da7faad1a7f31e95c3d1c2e3d323fdf7c757c134`.

The `review-inputs` runner/report snapshots match their declared hashes. The prior run report records the same candidate object/candidate hashes and helper relocation identities as the independent run.

## Runner model and coverage

I inspected the frozen runner's `run`, `audit_cases`, `observable`, and `run_contract_audit` paths. It freshly initializes mapped state, calibration, samples, outputs, registers and VFP enable state per case; executes the original at `0x0027FBC8` and relocated candidate; instruments the original deadzone helper; and compares valid-case return, output bytes, helper calls, selected state/calibration/sample memory, ordered non-stack writes, `r4-r11`, `d8-d15`, and FPSCR. The runner logs memory writes and the count of stack writes. It intentionally excludes compiler-dependent stack byte layout. For the mutation control, it asserts candidate word at offset `+0x30` is `0xE3520001`, changes only that word to `0xE3520002`, and executes original and mutated candidate against the same mode-2 input fixture. In both the original and rerun report, original rejects mode 2 with untouched sentinel outputs while the mutant returns 1 and writes zero outputs; `detected=true`.

The expanded matrix has 146 cases: 144 valid synthetic cases and two invalid-output-pointer fault probes. It covers mode/max limits, selectors `0/1/2/3/255`, flag values, signed halfword extremes, null output combinations, equal/swapped/state/calibration/sample aliases, zero and reversed spans, threshold/deadzone values including signed zero, NaN and infinities, and 100 seeded cases. The mode-2 control is additional to the 146-case matrix.

For valid-domain comparisons, the observable set is meaningful but not a full ABI/memory snapshot: the comparator does not include `SP`, condition flags, or all scratch GPRs; it also excludes `stack_write_count` and compiler-dependent scratch-stack bytes. The report does not claim those dimensions. Callee-saved GPRs `r4-r11`, VFP `d8-d15`, and FPSCR are initialized and compared. The fixed mapped fixture/harness does not characterize real hardware, concurrency, or external caller state.

## Fault probes and limitations

Both invalid-pointer cases produce `UC_ERR_WRITE_UNMAPPED` and identical ordered writes in original and candidate:

- Invalid X: a 4-byte write of `0x3E800000` to `0xFFFFFFF0`, then the unmapped write fault.
- Invalid Y: a 4-byte write of `0x3E800000` to valid X at `0x02011000`, then a 4-byte write of `0xBF000000` to `0xFFFFFFF0`, then the unmapped write fault.

The runner handles fault cases separately: it records fault class and data-write traces, but excludes post-fault PC, return, output snapshots, scratch registers, FPSCR and further memory as supported behavior. This is appropriate for the stated out-of-contract probes; matching these observations must not be described as supported invalid-pointer semantics. Fault hook timing is Unicorn-specific.

The task's prior reports preserve the direct caller-composition evidence separately. No player-control or runtime-game claim follows from these synthetic direct calls. No emulator, private save/profile, or guest-memory access occurred.

## Independent rerun and next action

Command executed from the frozen `review-inputs/h4_axis_reader_experiment.py`, importing that snapshot and rebinding only its repository root/source/image paths in memory, then invoking its own `main()` with `--audit-contract --seed 20261029 --out-dir build/agent-work/H4-semantic/h4-axis-reader-contract-audit-review/001/checks/seed-20261029`. Exit code: 0. This uses the exact frozen runner bytes and an isolated fresh output/object; it does not edit the snapshot, candidate, or shared runner.

Fresh report: `build/agent-work/H4-semantic/h4-axis-reader-contract-audit-review/001/checks/seed-20261029/contract-audit-report.json`, SHA-256 `ee67de5be35d402aa01afa60da7faad1a7f31e95c3d1c2e3d323fdf7c757c134`; status `passed`, case count `146`, difference count `0`, mutation detected. Compiled and ARM-differential evidence is therefore bounded to this frozen synthetic runner. Caller evidence remains partial; runtime is not run. Continue with independent caller-composition review and later integrated/runtime evidence before any promotion.

