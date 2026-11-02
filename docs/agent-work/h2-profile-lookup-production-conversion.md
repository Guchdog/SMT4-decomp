# `0x002AEA28` profile selector production conversion

**Result:** independently reviewed typed C++ replacement for a bounded TBB
profile selector used by `0x002B8B78`.

## Contract and implementation

The pinned function calls `Tbb_GetGlobalSubTable(14, 0)`, then
`Tbb_GetPayloadData(table)`, then `Tbb_GetRowCount(table)`. The index compare is
unsigned over all 32 bits. A hit returns `payload + index * 16` using ARM
32-bit address arithmetic; a miss returns zero. The typed body retains all
three dependencies in that order. A compact inline ARM conditional sequence
keeps the body inside its original 56-byte slot and writes the result directly
to `r0`.

## Validation

| Check | Result |
| --- | --- |
| Final-VMA direct differential | 16/16 cases; zero mismatches |
| Original TitleConfig init slice | Request `0x99`; matched with both selector calls executed |
| Original conditional callback slice | Request `0xDC`; matched with both selector calls executed |
| Mutation controls | 3/3 detected: wrong TBB slot, stride 8, and wrong equality boundary |
| Body and placement | 56/56 bytes; three ARM calls to even entries; single-slot IPS replay passed |
| Affected TU builds | `leaf_batch24_b.cpp`, `leaf_batch32_c.cpp`, `tbb_loader.cpp`: 3/3 passed |

The wrapper compositions keep original `0x002B8B78` and stub its other service
dependencies. TBB selector/payload/count services return controlled values.
The tests cover indices 0, count-1, count, count+1, sign/high-bit boundaries,
maximum values, null helper results, and a zero payload. They do not validate
transitive TBB semantics or game resource population.

The final body differs from the pinned ARM implementation, so the ledger is
`non_matching`. Independent review approved the bounded selector contract and
the tested slices. No runtime/emulator test was run; TBB lifecycle and audio
behavior remain outside this evidence.

Review: [independent review](h2-profile-lookup-independent-review-002aea28.md).
