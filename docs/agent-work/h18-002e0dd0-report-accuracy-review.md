# Independent report-accuracy review: `0x002e0dd0`

## Result

The serialized stop for `ui_func_003bbdb8_ignored_result` is now accurate. Fresh report `checks/seed-20261120/report.json` records `stop: 0x3bbe18`; disassembly of the pinned bytes shows this is the next real helper BL (`bl 0x0021f480`) after the wrapper call at `0x003bbdfc`. The caller runner executes from that real BL site and stops when it reaches `0x003bbe18`, before executing the helper instruction. The two `ui_func_003bbfb0` cases correctly stop at the synthetic caller LR `0x1001000` after completing their epilogues.

Both branch outcomes pass against the original and candidate: wrapper result 0 returns 0; wrapper result 5 returns `0x11`. The `0x81` statement in the body of the older candidate-review document is explicitly labeled historical and refuted in its opening correction note, which links the corrected caller review. That correction cites the pinned `bne 0x003bc02c` and confirms it skips `mov r0,#0x81` at `0x003bc028`. The separate report-accuracy note records the stop-field correction and its prior mislabel. These notes preserve the old review text as historical evidence without leaving its conclusion ambiguous.

## Fresh checks

- `python -m unittest tests.test_h18_002e0dd0_experiment -v` — exit 0, one focused test passed. The assertions include the ignored caller's `0x3bbe18` stop, both branch stop addresses and returns, and negative-control detection.
- `python tools/h18_002e0dd0_experiment.py --image extracted/exefs/code.bin --output build/agent-work/batch-h18-001/h18-002e0dd0-report-accuracy-review/run-001/checks/seed-20261120 --seed 20261120 --samples 8` — exit 0; 33 direct cases passed, three caller compositions passed, and all 3/3 negative controls were detected.
- Pinned original disassembly at `0x003bbde0..0x003bbe30` confirms `0x003bbe18` is the next caller call site after the ignored-result continuation; the wrapper BL is at `0x003bbdfc`.

The fresh report records caller stops/results: ignored-result continuation `0x3bbe18` / `0x0043ddf2`; non-5 branch `0x1001000` / 0; 5 branch `0x1001000` / `0x11`. Direct result count is 33 for this eight-random-sample run, because the runner also includes 25 directed gate/string cases.

## Limits

This remains offline Unicorn evidence with synthetic global/object fixtures and modeled wrapper helpers. The caller starts at the audited BL site, not its full setup path; the ignored caller stops at the next helper BL rather than executing that helper. No emulator/runtime or whole-game equivalence claim follows. The corrected `0x81` conclusion is supported by the pinned original bytes; the old erroneous text remains only under its explicit historical-correction note.
