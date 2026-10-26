# Independent review: full H1 preview composition

> Correction, 2026-10-25: after this review, a combined-path fixture exposed
> an inherited selector-sequence layout error in the 17-case producer runner.
> Its sequence words were placed at `+0x14`, but pinned `0x002B1C8C` loads at
> sequence-base `+8 + 28*index`. I withdraw this review's claim that the old
> 17-case matrix exercised successful selector lookup. The recorded 17/17
> comparison and identity checks remain accurate for the exact fixtures; the
> selector path is covered by a separate three-case run using the correct
> `+8/+0x24` layout, pending its independent review. The 17-case run also
> isolated dependencies and did not prove simultaneous active paths. See the
> [producer correction and interaction fixtures](h1-preview-composition-interactions.md).

## Verdict

**Bounded composition evidence is supported; overall evidence remains partial.**
All 20 packet input hashes matched. I independently recomputed all six pinned
body hashes and the final candidate object/ELF/text hashes. The original side
reaches each pinned body, and the linked candidate routes through compiled C++
adapters to all five editable dependency candidates. The link has no undefined
symbols or external stubs. The final report records 17/17 cases passing,
`first_mismatch=null`, and detection of the missing-`+0x50` setter-store
mutation. No mismatch or provenance discrepancy was found in the exercised
domain.

The matrix isolates dependencies: while the helper update paths run, the scale,
translation, and selector dependencies are gated; the individual dependency
cases gate the other helpers. Consequently, the run does not demonstrate
simultaneous cross-field behavior among multiple actively updating dependencies
in one constructed H1 object. This is useful composed differential evidence,
not live H1 integration or runtime equivalence.

## Pinned and candidate identities

Pinned image SHA-256:
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
All six executable spans below were independently rehashed from that image and
matched the runner/report identities:

| Entry | Size | Pinned body SHA-256 |
|---|---:|---|
| `0x002BF9F0` preview helper | 664 | `9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e` |
| `0x002BDAC0` row setter | 108 | `e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a` |
| `0x002C615C` divide helper | 556 | `3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9` |
| `0x002B1FC0` scale track | 444 | `9d9948ecc56a1a6dd32012eacce76ce8cffdf3902632f8efc85245d9dd1f5811` |
| `0x002B1DFC` translation track | 452 | `092706575055bba00e8aab90e9ef2a45c2761fb7d12fa0f0b54dbecd35b7439a` |
| `0x002B1C8C` sequence selector | 368 | `8097eb2315dd6b7f6dd72be434ee38223841c6470bfa3b923b362900572ba092` |

The six candidate source hashes match the frozen packet: helper
`64c3964b0abae2c0ff6e51d1e9ef5961c8e8d0769e177c528a878d4b094b3282`, setter
`653f143c22f46a30ac2f5fe183f5d305927fca5f4959ef69d9a2f38f477377fc`, divide
`078dc53d627479fb787ef3c45c093f8cebd3936c8bf4b562362f1b23d9cf0a30`, scale
`5226b8680178fac814a515a4bb9440aadbec37edcd156b3ec1278dd381fc30e7`,
translation `add9c202a734341338068d7ec0c72a3555df2779bb75582eda3d345a6d294e50`,
and selector `cc7d7ab98919b4cabf741b09d95fb61f199246ddb79ac4e4f4a26f686e9fe007`.

The seven compiled object hashes in final report `results-v4/report.json` were
also recomputed and matched: helper `4383bac62698846b1c5e0fbce7266b9685c945a7599e55411348b653fcae281c`,
setter `e9d9dfa136387bdfb2cb723bc4f18073dea4f799ae8d60184799e7caa34ddd57`,
divide `d1a2c6462ecd2d25d32c70f62f76fe4d9f3409fe537d381a56e5f3444f0b85f8`,
scale `ed37a44940831afd463a6be6b790744c2d365bbaf5399e2e398e2cb94b43f76a`,
translation `dc5400cde57da1e217ff3cefae4b02da6c94364872292b50123cf42a262a911b`,
selector `e6e77d04eb49be38bb77e8c4f24ca12c40112a96bc9b21e811ae17cd37fdc53a`,
and adapter `ae8bcdf2668bd426ac680cc3b8c99506502eee80015e2f1f1fd9916db3ce0136`.
Adapter source SHA-256 is
`247e586f47da635419032111130ef577175a62ff9722e6f90537e55386d2e3d6`. The
linked candidate ELF SHA-256 is
`cadabe6a51fbc6ccda698afde01beb595417b636af2bc65f086e2c7121b5678c`, linked
text SHA-256 `ea02cfc47cb99e03967d54fbe6bb01bc5459aa20df2ddeb1ba0a026899d85fae`,
and the final report SHA-256 is
`be20ae62754ead7190364844d625cc3e2e133dc83bc82473dc607f5f92b7112d`.

## Execution paths and ABI routing

The pinned helper disassembly confirms two setter calls (`0x002BFB48` and
`0x002BFB78`), four divide calls (`0x002BFBA4`, `0x002BFBC8`, `0x002BFBEC`,
`0x002BFC10`), then the scale, translation, and selector calls at
`0x002BFC30`, `0x002BFC3C`, and `0x002BFC48`. The original ARM hook records each
callee entry and leaves PC/LR unchanged so the pinned body executes.

On the linked side, the helper candidate calls these wrapper symbols:

| Wrapper | Compiled target | ABI note |
|---|---|---|
| `camp_func_002bdac0` (`0x01000F54`) | `h1_animation_row_setter_candidate` (`0x010004AC`) | forwards object, signed row index, signed mode/frame in `r0-r2` |
| `ui_func_002c615c` (`0x01000F58`) | `candidate_002c615c` (`0x01000614`) | passes numerator and casts the helper's `u16` duration to `s32` |
| `ui_func_002b1fc0` (`0x01000F5C`) | `h1_preview_scale_track_candidate` (`0x01000620`) | forwards object; discards the ignored pointer return |
| `ui_func_002b1dfc` (`0x01000F60`) | `h1_preview_translation_track_candidate` (`0x0100090C`) | forwards object |
| `ui_func_002b1c8c` (`0x01000F64`) | `h1_preview_sequence_track_candidate` (`0x01000C68`) | forwards object; discards the ignored pointer return |

The divide wrapper's signed conversion preserves the helper's exercised positive,
nonzero unsigned-halfword duration domain. Zero-duration division is explicitly
outside this composition fixture domain. The report shows every object compile
and final link exited 0, and `llvm-nm -u` found no undefined symbols. The
candidate wrapper hook records the wrapper entry and lets its compiled body
continue; disassembly confirms each wrapper branches/calls into its editable
candidate rather than a return-zero/no-op stub.

## Seventeen-case coverage and mutation control

The final matrix covers: null helper pointer; both signed helper gates negative;
common tail calls with all track objects gated; endpoint/sequence-disabled;
restart and ordinary helper setter transitions; both interpolation directions
through the divide candidate; helper current `-1` and next `-3` sentinels; scale
endpoint and interpolation; translation endpoint and interpolation; selector
ordinary row transition; selector lookup success after a sentinel; and selector
next `-3` completion. All report cases pass. The original call-name set contains
all five direct dependency bodies: setter, divide, scale, translation, selector.

The setter control links a private mutant omitting the `+0x50` row-index store
while keeping the other five candidates intact. On the ordinary-next setter
case, the first memory mismatch is at `0x02000050`: original byte `2`, mutant
byte `0`; exactly one data byte differs. The control is therefore sensitive to
the setter side effect the test intends to protect.

The comparison projects fault and return-sentinel state, `r0`, preservation and
equality of `r4-r11` and SP, preservation/equality of `d8-d15`, FPSCR, SHA-256 of
the full `0x20000`-byte data map, final object bytes, caller-owned stack bytes,
and ordered direct-call names and argument registers. This is appropriately
broader than output-only comparison for these fixtures. It excludes
caller-saved scratch GPRs and flags, below-entry-SP spill residue, and memory
access order/multiplicity. Direct call PCs are normalized to dependency names;
the runner separately pins the original entry map and candidate wrapper symbols.

Remaining local coverage gaps include selector current/next `-1` and selector
next `-2` behavior in this composition run, more selector lookup misses/count
edges, active scale/translation/selector updates in combination with a helper
setter transition, and cross-effects between simultaneously active tracks.
Separate dependency experiments exist, but they do not establish these
combined paths.

## Evidence boundary and next action

Fixtures are finite, valid, non-aliasing ordinary-memory synthetic objects,
tables, sequences, descriptors, and lookups. They do not establish real H1
construction/allocation, asset bindings, callback selection/timing, lifecycle,
concurrency, MMIO, invalid pointer/index behavior, or game/runtime equivalence.
The divide wrapper is only validated for the positive nonzero `u16` duration
domain reached by these helper cases. No actual H1 caller scenario was executed.
The report and candidate records correctly keep ARM differential and caller
evidence partial and runtime `not_run`; no ledger promotion is justified by this
review alone.

Next action: retain the full-composition result as partial synthetic evidence;
review or add bounded cross-field active-track cases and recover live object
lifecycle before considering an integrated H1 runtime claim.

## Read-only review commands

- An initial typo `python tools.split_asm.py ...` exited 2; the corrected
  `tools/split_asm.py` commands below completed successfully. An exploratory
  artifact-hash script also used an incorrect path for the mutated source and
  exited 1; the subsequent recursive artifact hash audit completed and matched
  the recorded ELF/source identities.
- Python SHA-256 audit of all 20 packet inputs: exit 0, no mismatches.
- Python recomputation of all six pinned body identities and all seven object
  identities, candidate ELF/text and adapter: exit 0; values matched the report.
- `python tools/split_asm.py --addr 0x002BF9F0` filtered to direct calls and
  returns: exit 0.
- `python tools/split_asm.py --addr 0x002C615C` filtered to returns: exit 0.
- `llvm-objdump.exe -d .../results-v4/candidate-build/composed_candidate.elf`
  filtered to all wrapper/candidate symbols and calls: exit 0.
- Read-only report and results-v4 link-command JSON audit: exit 0.
- `python tools/agent_workflow.py check-handoff --packet <review-task.json>
  --handoff <review-handoff.json>`: exit 0 after handoff creation.

No compilation, test execution, emulator, or game-runtime control was performed.
