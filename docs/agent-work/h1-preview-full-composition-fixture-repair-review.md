# Independent review: repaired full-composition selector fixture

## Verdict

**The repaired run supports the 17 declared synthetic comparisons, including a real selector lookup; overall evidence remains partial.** All 18 frozen task inputs matched their packet hashes. I independently disassembled the pinned selector calculation, recomputed all six pinned body hashes, checked the repaired fixture writer and success assertions, audited all 17 report cases and the setter mutation, and recomputed the report and candidate ELF hashes. I did not compile, rerun tests, or use an emulator/runtime.

## Selector lookup is now exercised

At pinned `0x002B1C8C`, instructions `0x002B1D34-0x002B1D40` compute `sequence_base + 8 + 28*index` and load the word there. The function increments the index, then `0x002B1D58-0x002B1D60` loads the next record's word at its `+8`. For initial index zero, the relevant words are at sequence-base `+8` and `+0x24`.

The repaired shared writer now allocates the records from offset `8` and writes each word at `8 + 0x1C*i`. Its lookup fixture supplies words `[0, 1]` and lookup entries `[-1, 42]`. Pinned execution sees zero at index zero, advances, reads `1` at `+0x24`, walks the lookup records and selects the entry containing `42`. The final original snapshot has object `+4 == 42`, `+0x70 == 0x0200E104`, indices `+0x74/+0x76 == 0`, and selector enable `+0x89 == 0`. The focused test asserts all five effects. These assertions establish branch effects beyond a mere original/candidate equality result.

The prior `results-v4` matrix also reported 17/17 exact fixture comparisons, but its writer put the word at `+0x14`; therefore its case labelled successful selector lookup did not establish lookup success. That interpretation is superseded. The prior report remains a comparison of the fixtures it actually encoded and is not retroactively a bad byte/data comparison. The corrected run-01 report is the applicable evidence for the lookup path. Neither matrix establishes that scale, translation, and selector all take active update paths simultaneously with the helper's distinct branch work; this full-composition matrix uses individual synthetic branch fixtures.

## Identities, link and differential report

Pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. I independently rehashed each reported pinned function span from `code.bin`; all six matched:

| Entry | Size | SHA-256 |
| --- | ---: | --- |
| `0x002BF9F0` helper | 664 | `9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e` |
| `0x002BDAC0` setter | 108 | `e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a` |
| `0x002C615C` divide | 556 | `3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9` |
| `0x002B1FC0` scale | 444 | `9d9948ecc56a1a6dd32012eacce76ce8cffdf3902632f8efc85245d9dd1f5811` |
| `0x002B1DFC` translation | 452 | `092706575055bba00e8aab90e9ef2a45c2761fb7d12fa0f0b54dbecd35b7439a` |
| `0x002B1C8C` selector | 368 | `8097eb2315dd6b7f6dd72be434ee38223841c6470bfa3b923b362900572ba092` |

The six candidate source hashes match the task packet. Run-01 records all object builds and the link exiting zero, an empty undefined-symbol list, and the six candidate sources routed through its local ABI adapter. This supports “no external stubs” for the composition: the original side dispatches into pinned bodies, while the candidate image contains the editable dependency bodies. The composed ELF hash independently recomputes to `cadabe6a51fbc6ccda698afde01beb595417b636af2bc65f086e2c7121b5678c`.

The report contains 17/17 passing cases with `first_mismatch == null`. I checked every case's recorded projection fields: data digests, caller-stack digests, `r0`, preserved registers/SP, `d8-d15`, FPSCR, and ordered direct-callee calls and arguments agree. The defined projection covers the entire 0x20000-byte synthetic data map and caller-owned stack, but excludes caller-saved scratch GPRs/flags, memory access multiplicity/order, and below-entry-SP spill residue. The setter negative control is detected at `0x02000050` (original byte `2`, mutant `0`).

The corrected report SHA-256 is `751ebf1cf6a4ceab1152b56b43a4f8d71451205208434285c86c9606a2f61078`; the linked ELF SHA-256 is `cadabe6a51fbc6ccda698afde01beb595417b636af2bc65f086e2c7121b5678c`; and the focused test source SHA-256 is `f107c63c1af131c2e7c4213102ffa666f9f390eccaeab92de237a81891adb838`. The producer handoff records the fresh run exit 0, focused tests exit 0 (two tests), and its provenance check exit 0. I audited those recorded outcomes and test assertions but did not rerun them.

## Limits

Fixtures are synthetic valid non-aliasing ordinary-memory objects, rows, sequences, descriptors and lookup records. The helper divide cases exercise positive nonzero duration only. This does not establish real H1 allocation/object construction, asset binding, callback registration in the live caller, lifecycle or rendering. It also leaves arbitrary invalid pointers/indices, aliases, concurrency, MMIO, caller-saved scratch/flags, access order and below-SP residue unvalidated. No production build, Azahar, gameplay or runtime equivalence was exercised. Keep this as partial offline semantic evidence, not promotion or whole-game equivalence.

## Recommendation

Retain corrected run-01 as the selector-lookup evidence and label results-v4 as superseded for that branch only. A later coherent integration step should validate real caller setup/lifecycle and the defined game-runtime scenario; use the separate corrected combined-path evidence for simultaneous reachable dependencies rather than inferring that coverage from this 17-case matrix.
