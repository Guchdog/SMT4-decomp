# Full H1 preview helper composition differential

> Fixture repair, 2026-10-25: pinned `0x002B1C8C` reads selector sequence words
> at base `+8 + 28*index`. The original `results-v4` fixture writer stored them
> at `+0x14`, so that report's case labelled “successful lookup” did not cover
> successful selection. The fixture writer and assertion are now repaired; see
> the fresh 17-case run below. The historical `results-v4/report.json` is
> retained unchanged for provenance, and the separate [interaction analysis](h1-preview-composition-interactions.md)
> records the reachability limits.

## Repaired full-matrix result

The repaired fixture encodes sequence entries at `+8` and `+0x24` and asserts
that the original selected lookup row: object `+4 == 42`, `+0x70 == 0x0200E104`,
indices `+0x74/+0x76 == 0`, and selector gate `+0x89 == 0`. The new full matrix
again passes all 17 original-pinned versus linked-candidate cases with no
mismatch. The missing setter `+0x50` store control remains detected.

Fresh report:
`build/agent-work/H1-semantic/h1-preview-full-composition-fixture-repair/overnight-20261025-full-composition-fixture-repair/run-01/report.json`
(SHA-256 `751ebf1cf6a4ceab1152b56b43a4f8d71451205208434285c86c9606a2f61078`).
Its report confirms that the corrected successful lookup updates the object as
expected. The earlier `results-v4/report.json` remains at its original path and
hash; it remains valid evidence for its exact bytes/fixtures, but not for
successful selector lookup.

## Result

The earlier private offline Unicorn ARM comparison (`results-v4`, now superseded
for selector sequence coverage) passed all 17 original synthetic cases. The
original side ran pinned `0x002BF9F0` and dispatched its real callees from the
pinned `code.bin`; the candidate side linked the unchanged helper with all five
editable direct-dependency candidates and private ABI wrappers. There are no
external stubs or undefined candidate symbols. The report's first mismatch is
null. A private setter mutation omitting the `+0x50` animation-index store was
detected at data address `0x02000050` (original byte 2, mutant byte 0).

The image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The six
pinned executable spans were identity-checked before running:

| Entry | Size | Pinned body SHA-256 |
|---|---:|---|
| `0x002BF9F0` helper | 664 | `9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e` |
| `0x002BDAC0` row setter | 108 | `e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a` |
| `0x002C615C` divide | 556 | `3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9` |
| `0x002B1FC0` scale track | 444 | `9d9948ecc56a1a6dd32012eacce76ce8cffdf3902632f8efc85245d9dd1f5811` |
| `0x002B1DFC` translation track | 452 | `092706575055bba00e8aab90e9ef2a45c2761fb7d12fa0f0b54dbecd35b7439a` |
| `0x002B1C8C` sequence selector | 368 | `8097eb2315dd6b7f6dd72be434ee38223841c6470bfa3b923b362900572ba092` |

The report records each editable source hash, all seven object compile
commands/exits, linker command/exit, candidate ELF and `.text` hashes, symbol
addresses, and the original body identities. The division wrapper converts
the helper's positive `u16` duration to the candidate's signed `int32_t` ABI;
the helper call domain is nonzero duration. The track wrappers call the
candidate entries and discard pointer returns ignored by the helper.

## Covered flows and comparison

The repaired 17 cases cover a null helper pointer and the two-negative signed early
gates; helper endpoint with disabled sequence; both helper setter paths (next
word `-2` restart and ordinary next); helper interpolation in both directions
through the real divide candidate; current `-1` and next `-3` helper sequence
sentinels; scale-track endpoint and interpolation; translation-track endpoint
and interpolation; selector ordinary row transition, successful lookup-based
sequence selection, and next `-3` completion. The three common-tail helpers are
also called in ordinary helper cases, with their per-object gates set to their
documented early-return conditions where unrelated branches are not under
test. Separate fixtures activate their real track behavior.

Each run starts from the same complete `0x20000`-byte synthetic data map and
stack bytes. The projection compares execution faults and sentinel return,
`r0`, `r4-r11`, SP, `d8-d15`, FPSCR, the full final data-map digest, object
bytes, caller-owned stack bytes, and ordered direct-callee names/argument
registers. The report includes original and candidate digests per case. It
does not compare caller-saved scratch GPRs or flags, below-entry-SP temporary
spill residue, or memory access multiplicity/order.

## Limits and commands

Fixtures use valid, ordinary, non-aliasing synthetic objects, rows, sequences,
descriptors, and lookup records. They do not establish H1 object construction,
allocation, asset selection, runtime callback bindings, actual lifecycle,
concurrency, MMIO, arbitrary invalid-pointer/index behavior, or game/runtime
equivalence. Divide-by-zero is outside the helper interpolation case domain.
This is composition evidence for the exercised synthetic domain, not live H1
integration.

The historical command, retained for provenance, was:

```powershell
python tools/h1_preview_full_composition_experiment.py --output build/agent-work/H1-semantic/h1-preview-full-composition/overnight-20261025-full-composition/results-v4
```

It exited 0 and reported `PASS 17/17; dependency control=detected`, but its
sequence lookup fixture was misplaced as described above. Its report remains at
`build/agent-work/H1-semantic/h1-preview-full-composition/overnight-20261025-full-composition/results-v4/report.json`.

The repaired run used:

```powershell
python tools/h1_preview_full_composition_experiment.py --output build/agent-work/H1-semantic/h1-preview-full-composition-fixture-repair/overnight-20261025-full-composition-fixture-repair/run-01
```

It exited 0 and reported `PASS 17/17; dependency control=detected`. The focused
report assertions used the fresh report path and exited 0:

```powershell
$env:H1_PREVIEW_FULL_COMPOSITION_REPORT='build/agent-work/H1-semantic/h1-preview-full-composition-fixture-repair/overnight-20261025-full-composition-fixture-repair/run-01/report.json'; python -m unittest tests.test_h1_preview_full_composition_experiment -v
```
