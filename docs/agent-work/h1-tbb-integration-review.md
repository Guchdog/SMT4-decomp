# H1 TBB production-source integration review — 2026-10-25

## Recommendation

**Approve bounded source promotion for `Tbb_GetSubTable` (`0x002AC2F4`) and
`Tbb_GetPayloadData` (`0x002C0E9C`) at the documented semantic evidence level.**
The production C++ expresses the recovered 32-bit contracts, avoids the former
trailing-array indexing issue, and both pinned integration-mode reports name
the production symbols and report matching ARM differential, real asset, and
title getter-caller outcomes for seeds 7 and 20261024. The ledger correctly
classifies both functions as `non_matching`; neither the reports nor this review
support an IPS, live game, or whole-H1 equivalence claim.

## Source and ABI inspection

`TbcrHeader` models the first three 32-bit words, while `ReadU32LEAt` reads the
offset table byte by byte from `container + 0x0C + index*4`. This avoids C++
indexing beyond a one-element trailing array and explicitly assembles little
endian values. `Tbb_GetSubTable` uses `r0/r1`, rejects null, bad TBCR magic, and
unsigned `index >= table_count`, then resolves the child in the target's 32-bit
address domain and checks child magic. `Tbb_GetPayloadData` uses `r0`, rejects
null/bad TBL1 magic, and returns `table + 0x10` in 32-bit address arithmetic.
These signatures and scalar/pointer returns fit the pinned ARM32 ABI.

The source intentionally has no allocation-length parameter. It therefore
cannot validate that the header, trailing offsets, computed child, magic read,
or payload are within the allocation; malformed/unreadable pointers may fault.
There is no length-aware protection for addition wraparound either. The reports
exercise readable fixtures and the 880-byte real `TitleTable.tbb`; they do not
claim malformed-offset or arbitrary-memory safety. These are consistent with
the original wrapper's input limits, not newly supported behavior.

The function records and ledger agree on the classification: the subtable C++
is 156 bytes versus 92 original bytes; payload C++ is 40 bytes but is still not
byte-identical. `config/functions.csv` says `non_matching` for both. This is a
truthful semantic source promotion; the old exact bytes remain available as
reference.

## Integration-report audit

Both reports use the same pinned `code.bin` SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, the same
production TU SHA-256
`90d17cb7206c47d5fa5ddfae533a2d946f58815c14b92673f0cde3f838219819`, and the
same extracted integration object SHA-256
`e95866fb2b03fdb83c367ddc260cad0cc1599f26432f633e7db610509032649c`. Their
symbol map is exactly `Tbb_GetPayloadData` and `Tbb_GetSubTable`; the runner's
integration path resolves each from the compiled production TU, rejects
missing/ambiguous symbols and relocations, and substitutes those bodies in the
differential windows. The reported object was built with Clang 23.1.3.

For each seed, the production payload symbol passed 70 cases (six directed,
64 random); the production subtable symbol passed 71 (seven directed, 64
random). The real asset passed both valid subtable indices, the count boundary,
and both payload pointers. Negative controls were detected at `wrong-magic`
and `wrong-child-magic`. The hash-checked original title getter caller reached
`0x001E9AC8` and passed selections 0–3, with the expected table-0 payload
pointer.

The caller window is narrowly scoped to the getter chain. It leaves
`Tbb_GetGlobalSubTable` original and checks the candidate subtable/payload
accessors; it computes selected record/help-field addresses but does not
consume or render the strings. The reports also contain 72 RowCount cases and
a RowCount negative control; RowCount is outside this promotion. The reports'
top-level `passed` bit includes RowCount, so the recommendation here rests on
the payload, subtable, and caller-specific arrays and controls inspected
separately.

| Seed | Payload/subtable/caller | Report SHA-256 |
| --- | --- | --- |
| 7 | 70/70 payload; 71/71 subtable; selections 0–3 pass | `86091087e9533dced582336506892f28bf4e0435f60847346edff86fbbab83c2` |
| 20261024 | 70/70 payload; 71/71 subtable; selections 0–3 pass | `aa2b39b2e92df488594835f1ed42d68835e7a1a220efd39d2e253023c38d6811` |

The runner and symbol-resolution test hashes match the prepared packet:
`tools/tbb_semantic_experiment.py`
`da2a68c6d09ac968fc9dfb89c3a646d7ea5055042543caca685d48d751e12585`,
`tests/test_tbb_semantic_experiment.py`
`3ba3818965de6c58bc8844d66ef33d1b5234b810e348bf0c23c62bb3be523921`.
Production header SHA-256:
`1eabd1831dca8f8949e53f24ef34be569b8eee2ec768e39949f32fc45f061c5f`.

Read-only provenance command (exit 0):

```text
python -c "import hashlib,json,pathlib; root=pathlib.Path('.'); rels=['build/agent-work/H1-semantic/h1-tbb-promotion/sleep-20261025-tbb/checks/integrated-seed-7b/report.json','build/agent-work/H1-semantic/h1-tbb-promotion/sleep-20261025-tbb/checks/integrated-seed-20261024/report.json']; rs=[json.loads((root/p).read_text()) for p in rels]; assert [r['seed'] for r in rs]==[7,20261024]; assert all(r['integration_source']=='src\\ui\\tbb_loader.cpp' or r['integration_source']=='src/ui/tbb_loader.cpp' for r in rs); assert all(r['integration_source_sha256']==hashlib.sha256((root/'src/ui/tbb_loader.cpp').read_bytes()).hexdigest() for r in rs); assert all(r['candidate_symbols']=={'payload':'Tbb_GetPayloadData','subtable':'Tbb_GetSubTable'} for r in rs); assert all(all(x['passed'] for x in r['cases']) and all(x['passed'] for x in r['subtable_cases']) and r['negative_control']['detected'] and r['subtable_negative_control']['detected'] and all(x['passed'] for x in r['title_caller_window']['selections']) and len(r['title_caller_window']['selections'])==4 for r in rs); assert all(r['reference_sha256']=='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558' and r['real_tbb_sha256']=='edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41' for r in rs); print('two pinned integration reports verified: source, production symbols, case arrays, controls, caller selections, reference and asset')"
exit: 0
```

Machine-readable review evidence:
[`review-evidence.json`](../../build/agent-work/H1-semantic/h1-tbb-integration-review/sleep-20261025-tbb/review-evidence.json).

## Remaining boundary

This review did not rebuild, patch, or execute an emulator. The reports prove
finite differential cases against the pinned original and a synthetic caller
window with the real TBB asset. Before claiming the H1 runtime scenario, the
integrator still needs a reproducible patched-image build, verification that the
patch matches the image exercised, and an original-versus-patched scoped title
runtime comparison. No blocker remains for the bounded two-source promotion.

Structured handoff:
[`handoff.json`](../../build/agent-work/H1-semantic/h1-tbb-integration-review/sleep-20261025-tbb/handoff.json).
