# H1 TBB proposal review — 2026-10-25

## Recommendation

**Ready for integration review of the two H1 dependencies**, with the limits
below. The isolated TBB proposals for `Tbb_GetSubTable` (`0x002AC2F4`) and
`Tbb_GetPayloadData` (`0x002C0E9C`) passed fresh differential runs for both
recorded seeds. The hash-pinned title caller window also passed for all four
selection values using the extracted `TitleTable.tbb`. This supports promoting
these bounded accessor behaviors to an integration/patch experiment; it does
not establish game behavior or whole-H1 completion.

## Contract and coverage review

- `Tbb_GetSubTable` takes container/index in `r0/r1`; it rejects null, a
  non-TBCR magic, an index `>= table_count`, a zero computed address, and a
  child whose magic is not TBL1. On a valid table it follows
  `container + header_size + table_offsets[index]`. It has no file length and
  cannot establish that the offset array, addition, or child are in bounds.
- `Tbb_GetPayloadData` takes the TBL1 pointer in `r0`; it returns null for null
  or bad magic, otherwise `table + 0x10`. It does not inspect payload size,
  stride, or available memory.
- Both candidates have no external relocations in the fresh build. Differential
  runs compare return/continuation, ABI state, memory and access footprint under
  the runner's local-blob validator. The title window additionally compares
  caller-observable state and stops at `0x001E9AC8`.
- The negative control omitting the TBL1 payload check is caught at
  `wrong-magic`; the control omitting the subtable child-magic check is caught
  at `wrong-child-magic`, in both seeds.
- Per seed: 70 payload getter fixtures (including 64 random samples), 71
  subtable fixtures (including 64 random samples), and the real asset's two
  subtable indices plus the `index == table_count` boundary and both real
  payload pointers passed. The title caller window passed selections 0, 1, 2,
  and 3. It reaches the same table-0 payload (`0x02000130`) and computes the
  expected selected-record/help-field addresses for each selection.
- The caller evidence covers `Tbb_GetGlobalSubTable` in original code plus the
  original/candidate subtable and payload getters through the title caller stop.
  It does not read the selected record/help string in this window; the selected
  field addresses are reported by the harness. It does not validate text
  rendering or a live title flow.

## Separate RowCount evidence

`Tbb_GetRowCount` is outside this H1 menu caller route and is **not** part of
the recommendation above. The TBB runner also ran its 72 synthetic cases and
negative control per seed; its oracle tail-branches to the pinned original
helper at `0x002C6C10`. The `TitleTable.tbb` row-count cases both return zero
because its two subtables have zero stride. These results remain separately
scoped getter evidence and do not support H1 caller promotion. The runner's
top-level `passed` field is composite and includes RowCount; this review
independently checked the payload/subtable arrays and caller results.

## Reproduction and hashes

Test side-effect inspection: `tests/test_tbb_semantic_experiment.py` loads the
pinned `code.bin` and uses in-memory fixtures; it does not invoke the canonical
build cache. The focused unit command exited 0 (7 tests).

```text
python -m unittest tests.test_tbb_semantic_experiment -v
exit: 0

python tools/tbb_semantic_experiment.py --code extracted/exefs/code.bin --seed 7 --samples 64 --output build/agent-work/H1-semantic/h1-tbb-review/sleep-20261025/checks/seed-7 --real-tbb build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb --title-caller-tbb build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb
exit: 0

python tools/tbb_semantic_experiment.py --code extracted/exefs/code.bin --seed 20261024 --samples 64 --output build/agent-work/H1-semantic/h1-tbb-review/sleep-20261025/checks/seed-20261024 --real-tbb build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb --title-caller-tbb build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb
exit: 0
```

The two compiler runs used separate output directories and one compiler job.
The runner itself rejects a `code.bin` whose configured size/hash differs from
the pinned revision.

| Input/artifact | SHA-256 |
| --- | --- |
| `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| `experiments/semantic_equivalence/tbb_candidates.cpp` | `ebf47d6c416d6c2a1cf56829bff51540fed56fda77b3b1cb84de9ea14e1ff5b8` |
| `TitleTable.tbb` (880 bytes) | `edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41` |
| seed 7 `report.json` | `f83fd54c6119142e506be04c3f6ec67ac7e06abdb5b33a87002b2f868e3fd87c` |
| seed 20261024 `report.json` | `12f7aff883b5d21c3ab45c20b9745530e319394f22f86ce791780a39acb6bc54` |

Reports:

- [`seed 7`](../../build/agent-work/H1-semantic/h1-tbb-review/sleep-20261025/checks/seed-7/report.json)
- [`seed 20261024`](../../build/agent-work/H1-semantic/h1-tbb-review/sleep-20261025/checks/seed-20261024/report.json)

## Conditions before production promotion

1. Integrate only the two getter behaviors in a reviewed patch/build, preserving
   the original source and exact-ledger labels; these C++ outputs are not byte
   matches. Keep RowCount out of this slice unless it receives its own review.
2. Preserve the contracts' real limits: malformed/out-of-range offsets and
   payload bounds are not checked by the original or candidate. A production
   caller must provide a valid readable TBCR/TBL1 allocation.
3. Review the candidate's trailing-offset-array access for standard C++ object
   bounds/lifetime assumptions before adopting it as maintained source; if
   needed, express the offset load as a byte-addressed read while retaining the
   same target behavior.
4. Re-run the title caller comparison against the integrated patch and verify
   that applying the patch reproduces the executed image. Then run the explicitly
   scoped original-versus-patched H1 runtime scenario. No IPS, emulator, or game
   comparison was performed here.

## Structured handoff

The machine-readable handoff is at
[`handoff.json`](../../build/agent-work/H1-semantic/h1-tbb-review/sleep-20261025/handoff.json).
