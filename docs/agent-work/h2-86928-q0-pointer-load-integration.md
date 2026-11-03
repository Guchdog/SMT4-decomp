# H2 `0x00286928` q=0 pointer-load integration closure

## Final-address staged image

The production TU was rebuilt into the original 820-byte slot:

```powershell
python tools/h2_86928_staged_image_patch.py --output build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix-integration/run002/staged-image
```

The current body is **808/820 bytes** with 12 bytes of ARM NOP fill. All 22
`R_ARM_CALL` relocations resolve to even ARM ledger entries. The staged IPS
round-trips to the generated image and changes only this function slot.
Staged image SHA-256:
`9113bf293ca3930818ada6a0342ff6189a6598bea6274bd92da312c979ca9c6c`;
IPS SHA-256:
`2708906f658e8a3283aeefb431d8e5af9171a98b305dc2b05b9690abef0b975a`.

## Offline validation and build

```powershell
python tools/h2_86928_staged_validation.py --staged-dir build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix-integration/run002/staged-image --out-dir build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix-integration/run002/staged-validation
python tools/build_check.py --repo-root . --out-dir build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix-integration/run002/full-build -j 8
```

The staged image passed 296 direct cases, four original-callback compositions,
and three `P+4` timing cases against the pinned original. Report SHA-256:
`2a916e7ca7d3b39685339987cc7e62deed423ca099cafefa6cffd7117f0582f1`. The full
ARMv6K build passed **204/204 translation units**, zero reused objects, eight
workers, 11.01 seconds.

The fresh direct/callback evidence and independent review are linked from the
[function record](../function-records/0x00286928.md) and
[the focused correction report](h2-86928-q0-pointer-reload-fix.md). In
particular, arg5 zero skips the `P+4` read; arg5 `1` and `0x100` exercise the
initial read, `0x002C4BF0` mutation, reload, and updated second helper argument.

## Limits and current milestone state

The caller tests use deterministic stubs for the other callees and synthetic
callback getter results. The runtime report with 129 dispatcher hits and 19
checkpoints used the prior 812-byte implementation; it does not validate this
808-byte revision. No current-revision emulator run was performed. Invalid
pointer faults, MMIO/concurrency, full callee behavior, readiness, same-session
re-entry, physical input mapping, audio output, and whole-H2 equivalence remain
unverified. The ledger stays `non_matching`; H2 remains open.
