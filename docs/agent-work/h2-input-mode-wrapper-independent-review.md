# Independent review: partial-span mode predicate `0x00128C2C`

## Finding

The conversion is supported for the first 24 bytes only. The wrapper calls the unsigned getter at `0x00138F34`, compares the full result with 4, and returns exactly 1 for mode 4 and 0 otherwise. The helper call relocation resolves to even ARM address `0x00138F34`. Direct comparison checks return, SP and `r4-r11` over every byte value.

The 84-byte ledger span is mixed code/data. Its first 24 bytes are the predicate; `0x00128C44` is a one-instruction NOP entry, `0x00128C48..0x00128C7F` is a separate 56-byte SVC entry body, and `0x00128C78`/`0x00128C7C` hold literals `0x00060040`/`0x00472AD8`. The compiled interior body equals the original bytes. IPS staging preserves the entire suffix `[0x00128C44,0x00128C80)` byte-for-byte while patching only the 24-byte predicate and separate 16-byte getter slot.

The incoming original branches remain intact: `0x0011C60C` BLs to the wrapper; `0x00128C30` BLs to the getter; `0x0010FC3C` branches to interior entry `0x00128C44`; and `0x0035B0B8` branches to `0x00128C48`. All targets are even ARM entries. Since the wrapper bytes differ, the full 84-byte row is now correctly `non_matching`; it had incorrectly remained `matching` in the earlier packet state. The corrected README total, 21,192 bytes across 72 non-matching functions, matches an independent sum of the ledger rows.

## Fresh run002 validation

All 19 frozen inputs matched. The normal runner staged and compiled its inputs but hit a Windows allocation error (`Failed to allocate memory: 1455`) during its repeated Unicorn executions in the earlier run. For run002, I used the unchanged runner's `main()` and helpers with explicit garbage collection between Unicorn instances. This completed the full fresh build/stage, all 256 direct modes, 14 fixed original-reader compositions, wrong-predicate mutation, and 64 additional seeded reader cases (seed `20261229`) with zero differences.

The 14 directed reader cases include modes `0, 3, 4, 5, 0x7f, 0x80, 0xff` with ring counts 0 and 1. Mode 4 suppresses ring reading; all other values continue. The wrapper call at `0x0011C60C` returns zero for non-4 modes, so the original reader takes its early exit only for mode 4. The wrong-comparison-constant mutation was detected.

The 58-byte IPS replays exactly. It has records for the 24-byte wrapper window and the 16-byte getter slot; only 15 byte positions differ from the original, all within those windows. The 56-byte interior body and the preceding NOP/literals are unchanged.

Fresh run artifacts:

- Full report SHA-256: `2496f9fae4ee2c9bf61d6e3e5812b56b04f6312ab3b40a4c4e55b3dce69065d8`
- Seeded reader report SHA-256: `b347552d4c0a75207ec24dbc75dbf0ab4a0facc550328cd5313b6ac300495325`
- Wrapper source SHA-256: `151cd20f2df17c417920dca630cc64a0d345c2aaaabc5e830af9c60a652051f3`
- Wrapper object SHA-256: `48ca198df64bc2812bd9d8d56d1d46b28ff6a76b727314de5161c9a8ac323a52`
- Getter source SHA-256: `6e0ca93d7dd7bc0739aa84c95b38cb9b13d7f4526eaf33b83142467319f2c564`
- IPS SHA-256: `81f2f38f8084526e04860d11e5b6de90e3a65cf3367c3fd44a5efdcc3700f96d`

## Limits

This establishes the wrapper predicate, helper ABI, original-reader composition, and byte preservation of the mixed-span interior. The SVC `#0x32` stream is preserved but not executed; kernel/service effects, handle lifetime, physical mode-byte meaning/provenance, scheduling, and full H2 runtime behavior remain unproven. The fixtures use a mapped mode byte and synthetic reader state with a controlled ring-reader seam. No canonical full build or emulator run was performed.

## Reproduction

```powershell
python build/agent-work/H2-semantic/h2-input-mode-wrapper-00128c2c-review/run002/checks/review_gc.py --out build/agent-work/H2-semantic/h2-input-mode-wrapper-00128c2c-review/run002/checks/fresh-gc-runner
python tools/agent_workflow.py check-handoff --packet build/agent-work/H2-semantic/h2-input-mode-wrapper-00128c2c-review/run002/task.json --handoff build/agent-work/H2-semantic/h2-input-mode-wrapper-00128c2c-review/run002/handoff.json
```
