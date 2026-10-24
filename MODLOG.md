# Semantic experiment field notes — 2026-10-24

Ten leaf functions at `0x00128F34`, `0x002AE464`, `0x00394614`, `0x0038143C`,
`0x00381450`, `0x003D7228`, `0x0037C46C`, `0x00121D70`, `0x0014EC5C`, and
`0x00131414` now have non-byte-identical typed ARM C++ candidates. Across the
two batches, differential execution passed 227,124 function cases and 3,116
original-caller-window cases. Nine deliberate defects were detected for their
intended reason, including signedness, null handling, alias order, memory
effects, and ABI preservation.

The original `.text` page padding `0x003FE624..0x003FF000` is 2,524 zero bytes
for the configured private image. The current 184 compiled bytes fit there. The
332-byte batch-2 IPS and 3,633,152-byte derived image have identical hashes for
both seeds; the earlier pilot separately verified IPS replay. Two original
caller windows passed. Batch-2 additions have function-level tests but no
caller-window tests. Real-loader padding behavior and a full game boot remain
unverified. Core source/ledger and the user's original image are unchanged. No
patch was installed, uploaded, or pushed.

See [the experiment report](experiments/semantic_equivalence/README.md) and the
[per-function procedure](docs/function-reconstruction-workflow.md) for
contracts, addresses, versions, hashes, commands, exclusions, and next gates.
Raw images, object files, and machine-readable run artifacts stay in ignored
`build/`.

## Handoff: batch 2 complete; game integration is the next gate

The user resumed work after the documented pause. Batch 2 added three typed
proposals and per-function records; its 11 focused harness tests, two
4,096-sample runs, and the full 64-test repository regression passed (three
private-key integration tests were skipped).

No 3DS emulator or console is available in the inspected environment. Azahar's
documented IPS path is
`load/mods/00040000000E5C00/exefs/code.ips`; Luma uses
`/luma/titles/00040000000E5C00/code.ips`. The next integration work needs a
supported emulator or console, the exact US base game, isolated original and
patched profiles, loader-log confirmation, and a way to trace replacement
entry execution. Do not claim a full-game pass from the ARM harness.
