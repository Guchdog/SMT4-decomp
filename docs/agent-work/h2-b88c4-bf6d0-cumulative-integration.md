# H2 touch-region and indexed-resolver integration

## Result

Integrated typed `0x002B88C4` and typed `0x002BF6D0` together into the reviewed run-013 H2 image at their original addresses. The output remains 3,633,152 bytes. The two-slot IPS changes 242 bytes, all within the declared 220-byte and 64-byte slots, and round-trips to the staged image. Calls resolve to even ARM entries: `0x002B88C4 -> 0x002BF6D0`; the resolver calls `0x002B0188` and `0x002C615C`.

The original `0x002B88C4` entry was run on the run-013 base and two-slot image for 58 cases: counts 0, 1, 37, 199 and 200 with both record forms, plus 48 seeded cases. All cases matched for return, region records, count, ordered non-stack writes, resolver arguments, callee-saved registers, restored SP, stop/fault state. Both implementation TUs compiled into private output during staging.

## Reproduction and artifacts

```powershell
python tools/h2_b88c4_bf6d0_staged_image.py --output build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/staging
python tools/h2_b88c4_bf6d0_staged_validation.py --base build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin --staged build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/staging/code.h2-touch-region-bf6d0.bin --manifest build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/staging/manifest.json --out build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/checks/caller-seed-20261119 --seed 20261119
```

Base SHA-256: `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291`. Staged image SHA-256: `e643173a604c331e6b333086d7df227ec9a684baa92e91b476851b433d1bb369`. IPS SHA-256: `1204c568d38245efbb93bb7e12252019a27a8e7156fb574948f71204a1a6e280`. Validation report SHA-256: `5bcfb15a4c4b05ad0901f995824884c44ed9a26fafd2316ca36616e7e4a0f524`.

## Limits

The manager/table/node/rectangle/touch work are controlled valid fixtures. The original manager resolver and divider execute, but this is offline component-chain evidence; runtime scheduler reachability, manager lifetime, physical input behavior, concurrency, malformed-pointer faults and whole-title behavior were not tested. The divider can leave temporary spill bytes below SP; comparison excludes writes within `STACK-0x100..STACK` while comparing restored SP and caller-visible effects. Runtime was not run.
