# Semantic experiment field notes — 2026-10-24

Ten leaf functions at `0x00128F34`, `0x002AE464`, `0x00394614`, `0x0038143C`,
`0x00381450`, `0x003D7228`, `0x0037C46C`, `0x00121D70`, `0x0014EC5C`, and
`0x00131414` now have non-byte-identical typed ARM C++ candidates. Across the
two batches, differential execution passed 227,124 function cases and 4,674
original-caller-window cases. Nine deliberate defects were detected for their
intended reason, including signedness, null handling, alias order, memory
effects, and ABI preservation.

The original `.text` page padding `0x003FE624..0x003FF000` is 2,524 zero bytes
for the configured private image. The current 184 compiled bytes fit there. The
332-byte batch-2 IPS and 3,633,152-byte derived image have identical hashes for
both seeds; the earlier pilot separately verified IPS replay. Four original
caller windows passed, including useful checks for two batch-2 functions.
Real-loader padding behavior and a full game boot remain
unverified. Core source/ledger and the user's original image are unchanged. No
patch was installed, uploaded, or pushed.

See [the experiment report](experiments/semantic_equivalence/README.md) and the
[per-function procedure](docs/function-reconstruction-workflow.md) for
contracts, addresses, versions, hashes, commands, exclusions, and next gates.
Raw images, object files, and machine-readable run artifacts stay in ignored
`build/`.

## Handoff: batch 2 complete; game integration is the next gate

The user resumed work after the documented pause. Batch 2 added three typed
proposals and per-function records. The final harness runs each passed 4,096
random samples per function plus boundaries under two seeds. Four caller windows
passed. The 11 focused tests and final full repository regression passed:
64 tests in 279.534 seconds, with three private-key integration tests skipped.

The user's Azahar build loaded the supplied decrypted CCI before patching. Its
decompressed `code.bin` is 3,633,152 bytes and SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
the exact revision used for the IPS. Azahar's [loader](https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/ncch_container.cpp)
searches `load/mods/<Title ID>/exefs/code.ips`; for this game the title path is
`load/mods/00040000000E5C00/exefs/code.ips`. The 332-byte patch is installed at
`%APPDATA%/Azahar/load/mods/00040000000E5C00/exefs/code.ips`. Luma uses
`/luma/titles/00040000000E5C00/code.ips`. In the first patched launch, Azahar's
log reported `code.ips patching code.bin`, and the user provided a screenshot
showing the SMT IV title menu. This confirms patch loading and a boot to menu;
it does not prove any replacement function executed. Next, trace replacement
entry execution and run behavior-focused in-game checks. A local ready-to-copy Azahar mod folder is in ignored
`build/azahar-mod/00040000000E5C00/`; its `code.ips` hash matches both test runs.
Only the external patch was added; the CCI was not modified. Do not claim a
full-game pass from the ARM harness.
