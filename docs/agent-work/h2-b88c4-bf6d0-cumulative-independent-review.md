# Independent review: cumulative H2 touch-region image

## Result

The cumulative two-slot image is internally consistent with its pinned run-013 base and staging manifest. I independently verified base, staged image, IPS, and manifest identities; applied the IPS back to the base; checked the exact two slot extents and replacement hashes; and decoded each ARM `BL` target. A fresh staged caller comparison using seed `20261120` passed 58 cases with no mismatch. This supports bounded offline review only; runtime was not run.

## Artifact and interworking audit

The run-013 base image SHA-256 is `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291`. The staged image SHA-256 is `e643173a604c331e6b333086d7df227ec9a684baa92e91b476851b433d1bb369`; its IPS SHA-256 is `1204c568d38245efbb93bb7e12252019a27a8e7156fb574948f71204a1a6e280`. The IPS independently round-trips from base to staged image. Both images are 3,633,152 bytes. Exactly 242 bytes differ and all changed offsets lie inside the two manifest-declared extents.

The `0x002B88C4` slot is 220 bytes, with a 156-byte body and padded replacement matching the manifest hash. Its `BL` at offset 12 targets `0x002BF6D0`, an even ARM address. The `0x002BF6D0` slot is 64 bytes, with a 60-byte body and padded replacement matching the manifest hash. Its `BL`s at offsets 8 and 28 target `0x002B0188` and `0x002C615C`, respectively; both targets are even ARM addresses. I decoded the instruction immediates from the staged bytes and confirmed each destination. The integration manifest records successful compile results for both implementation TUs before staging; this independent follow-up did not recompile them.

## Fresh caller comparison

Command:

```text
python tools/h2_b88c4_bf6d0_staged_validation.py --base build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin --staged build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/staging/code.h2-touch-region-bf6d0.bin --manifest build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/staging/manifest.json --out build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration-review/run001/checks/review-seed-20261120 --seed 20261120
```

Exit code: 0. Fresh report: `build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration-review/run001/checks/review-seed-20261120/report.json`, SHA-256 `b3f4e3b906e8c12a649eceb498cc72b722d467ab4085e4ea7f53b2143195b386`. It records directed counts 0, 1, 37, 199, and 200 for both custom and inline-region forms, plus 48 seeded cases. The actual original caller entry is executed on base and staged images; staged `0x002B88C4` invokes staged `0x002BF6D0`, while original manager resolver `0x002B0188` and divider `0x002C615C` execute. The runner compares return, record contents, count, ordered non-stack writes, both resolver argument pairs, callee-saved registers, restored SP, completion, and faults; no mismatch was recorded.

## Limits

The fixtures provide valid controlled manager, table, node, rectangle, and touch data. Writes in `[STACK-0x100, STACK)` are excluded from equality to tolerate divider spill residue below SP; restored SP and caller-visible outputs are still compared. This does not establish equality of stale stack bytes. Runtime scheduler reachability, manager lifetime, physical input behavior, concurrency, malformed-pointer fault behavior, and whole-title behavior remain untested. Runtime and a full build were not run.

## Recommendation

Accept this as independent bounded offline evidence for the two-slot composition, subject to the stated fixture and stack-residue limits. Keep the integrated byte classification truthful; this report does not claim byte identity or runtime/whole-game equivalence.
