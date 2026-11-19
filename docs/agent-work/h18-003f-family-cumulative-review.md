# H18 cumulative family independent review — run-001

## Verdict

The bounded cumulative staging claim is supported by an independent byte/IPS audit and a fresh offline functional run. I found no composition or preservation defect in the reviewed artifact. This supports only private cumulative staging and the exercised synthetic cases; it does not establish startup caller/order, production promotion, or runtime/game equivalence.

## Independent checks

The task packet's declared source/input hashes all matched at review time, including the pinned original (`1f98884f…aa558`), integrated H18 base image (`efdb59e3…03d12`), base IPS (`464d6dd0…af450`), staging utility, fit utility, and tests. The independent byte audit used a separately implemented IPS parser/replayer rather than importing the staging module's replay logic.

- Replayed the 2,335-record H18 base IPS over the pinned original: exact match to the 3,633,152-byte H18 base.
- Independently checked all 11 full slot intervals are disjoint, word-aligned, fit their extents, and were byte-identical to original in H18 base; no base IPS record intersects any target slot.
- Overlay IPS has 11 records; replay over H18 base yields the final image. Combined IPS has 2,346 records; replay over original yields the same final image. Both match SHA-256 `ba4149f1ba302e8acb22782d89435d8fe6e38d0ebebc0ca63b3a50dc72b56545e`.
- The 480 bytes occupied by candidate bodies are the only bytes permitted to change. 361 byte values differ from H18 base and all differences are within those body intervals.
- H2 cave `[0x003fe624,0x003ff000)` and preserved oversized `0x003f3454` interval `[0x003f3454,0x003f34a0)` remain byte-identical.

Fresh runner seed `20261118`, 20 samples per entry: 20/20 differential cases passed for `0x003f3274`, each of the eight `0x003f32f4` family entries, and both `0x003f34a0`/`0x003f34cc` tail entries (220 cases). All 15 negative controls were detected (5 + 8 + 2). The preserved original `0x003f3454` path also passed 20 base-versus-cumulative execution cases with the Thumb transition observed. The focused staging unit suite passed all four tests. Compile helpers report relocation-free bodies; the 11 placed bodies are ARM-word aligned. The separate 80-byte `0x003f3454` candidate is not placed; this keeps it from overflowing its 76-byte available interval.

## Evidence boundary

The function comparisons are offline Unicorn executions using synthetic fixtures; the preserved `0x003f3454` helper path is modeled by its existing harness. No actual startup caller or initializer order is established, and no emulator/runtime run was performed. The staged binary and IPS are private artifacts; this review is not production promotion or whole-game equivalence.

## Commands and outputs

- `python tools/h18_003f_family_cumulative_staging.py --help` — exit 0; confirmed `--output-dir`, `--seed`, and `--samples` CLI.
- `python -m unittest tests.test_h18_003f_family_cumulative_staging -v` — exit 0; 4 tests passed.
- `python tools/h18_003f_family_cumulative_staging.py --output-dir build/agent-work/batch-h18-001/h18-003f-family-cumulative-review/run-001/checks/seed-20261118 --seed 20261118 --samples 20` — exit 0; final image hash above; 361 changed bytes.
- `python -` with the separate byte audit (auditor source embedded in the task execution) — exit 0; results saved at `build/agent-work/batch-h18-001/h18-003f-family-cumulative-review/run-001/reports/independent-byte-audit.json`.

Fresh runner report: `checks/seed-20261118/report.json`. Next step: coordinator may review the audit and, separately, establish the real caller/order before considering integration or runtime evidence.
