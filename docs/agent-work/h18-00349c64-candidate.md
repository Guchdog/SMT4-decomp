# H18 candidate: `0x00349c64`

## Bounded result

The isolated 8-byte ARM entry is `mov r0,#1; bx lr`. The typed experimental C++ candidate in `experiments/semantic_equivalence/h18_00349c64_candidate.cpp` returns `std::uint32_t{1}`. It compiles to the same 8 bytes, `0100a0e31eff2fe1`. This conclusion applies only to the entry, not the enclosing catalogued 720-byte span.

## Caller evidence

No aligned immediate ARM `BL`/`BLX` references target this entry. Six aligned pointer values at `0x0047299c..0x004729b0` contain `0x00349c64`; they likely form callback data, but the consumer is unresolved. Direct-call and pointer scans do not find all indirect, computed, unaligned, or relocated references. No return-value consumer or runtime callback has been verified.

## Validation

`tools/h18_00349c64_experiment.py` verifies the pinned image, exact entry bytes and catalog span, compiles the candidate in a private per-run object path, and compares original/candidate execution with seeded ARM11 register, flags, RAM, stack, return, and control-flow observations. Negative controls change `r0`, NZCV, and memory independently.

- Seed `20261024`: 128/128 candidate cases passed; all three controls were detected.
- Seed `7`: 128/128 candidate cases passed; all three controls were detected.
- Compiled entry: `0100a0e31eff2fe1`; report object hash is recorded in each JSON output.
- Caller-composition/runtime: not run. No production source or ledger changed.

Detailed reports: `build/agent-work/batch-h18-001/h18-candidate-00349c64/run-001/checks/seed-20261024/report.json` and `.../checks/seed-7/report.json`.

## Scope limits and next action

The value `1` in `r0` is observed; its higher-level type/meaning and whether a callback caller consumes it are unknown. The adjacent interior entry `0x00349c70` and remaining 712 bytes of the catalog span are outside this reconstruction. Request independent review of the evidence, then identify the pointer-table owner/consumer before making caller claims or integration decisions.
