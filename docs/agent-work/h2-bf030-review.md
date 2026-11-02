# Independent review: 0x002bf030 sentinel table selector

## Scope and evidence identity

Read-only review of production `src/engine/leaf_batch41_b.cpp` SHA-256 `7a3b1952bc0a40b66da9e392bd7a954ed48500e1bede7fab4bbbf37698345575`, experimental candidate SHA-256 `17dc44497bdf60f5e67a591fd015b5a6dc40c493eda3d9b6f0cce9c7b6014734`, runner SHA-256 `35aef20db75b331611a89d5a9ad83f90cc661fd012ce53d1d8809e4362118b4f`, record and pre-existing object files. Reference is pinned code.bin SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. No independent compilation, runner execution or emulator use.

## Blocking test gap: non-marker entries

Every table entry in both `run_direct` and `run_real_caller` fixtures is initialized with first word `0xffffffff`. The candidate correctly increments its marker count only when that word equals `0xffffffff`, but the fixtures cannot distinguish it from an incorrect implementation that increments on every entry. Existing marker mutant changes equality from `0xffffffff` to `0xfffffffe`; that exercises a never-increment implementation, not unconditional increment.

Concrete counterexample: count=2, selector=1, entry headers `[0x00000000, 0xffffffff]`. Correct original checks marker count before reading the current entry, observes zero after first non-marker, and selects no entry; unconditional increment incorrectly selects entry 1. Add mixed-marker, no-marker, first/last and consecutive-marker patterns with valid full records and both selector 0 and nonzero; add an explicitly applied and detected unconditional-increment mutant. Re-run and freeze the resulting runner and output before accepting the scan evidence. This is a gap in validation, not a demonstrated defect in the inspected C++.

## Implementation and object

The C++ loads object+0x48, the unsigned halfword manager+8, computes `((n*0x9249+0x9249) modulo 2^32)>>20`, tests marker count before reading each 28-byte entry and tail-delegates `(object,selected)` to even ARM address 0x00138934. Its raw service result is returned. The source gives the intended fixed-width arithmetic and does not claim null checks. Scope remains valid ordinary RAM, aligned fields, valid manager and table records, non-wrapping pointer arithmetic, and valid service data. Aliasing, concurrent mutation and fault equivalence are not established.

Inspected candidate and production object symbols contain the same 96 bytes, no function relocations, and differ from the original 120-byte span. Candidate object SHA-256 `5e82e9d5396df6b0d3baab04a188fdc6fa0ba3aea2c430fc87241959acf4e0cf`; production object SHA-256 `22440fb73c30f21f2f08ceca67d47579a078a40136366e33a03e1a4bab7032a4`. The compiled tail is `BX` to literal even 0x00138934, consistent with ARM target mode at this boundary. Ledger `non_matching` is appropriate. Target-specific fixed function-pointer calls and legacy cross-TU declarations require stated ABI/non-LTO assumptions and final-image interworking verification. No link/package identity is proven by this static object comparison.

## Caller and evidence limits

The runner source defines 120 direct cases, deterministic count boundaries including n=65535, selector cases and retained original service with null, negative-word or zero return paths. It defines five controls for scan comparison, count, stride, marker and raw return. Each caller fixture enters original 0x002b8d24 index 11, asserts two entries at 0x002bf030 with selector 7, retains original 0x00138934 and caller tail, and compares raw r0, SP, r4-r11, selected memory and ordered non-stack guest writes. Caller table consists of eight marker entries, with selected record signed fields -1. The service branch calling 0x002bdac0 is not covered; broader service cases, invalid/fault inputs and integrated H2 runtime remain unsupported.

The function record reports the cases and a full build, but no independent runner execution occurred in this review and no preserved offline stdout was located under `build/h2-bf030`. Object and source identities alone do not prove those commands' execution or counts. Record fresh command/exit, runner, compiler, object and output hashes after closing the blocker; retain the actual original service in the runtime comparison.

## Revised runner review, packet 002

Runner SHA-256 `3074c3942cb9c99dca2874d05e7de86c4e57eec4fbaae9373e800b37ed56b17f` now adds eight directed `leading_nonmarker` and `none` table cases and a uniquely applied `increment_unconditionally` mutant whose detection is mandatory. For `leading_nonmarker`, header 0 is an ordinary non-marker and subsequent headers are markers; selector 1 tests the previously missed distinction between current correct scan and unconditional counting. The no-marker selector-1 case tests exhaustion. These changes address the run-001 test-design blocker. Existing caller fixture still uses all-marker records and selector 7; no claim for full service branches or H2 runtime follows.

The function record reports 128 direct cases, 24 caller cases and six controls, but this reviewer did not rerun them and did not locate `build/h2-bf030/offline-closure.txt` when inspecting packet 002. Preserve fresh stdout/exit status and toolchain/object/runner identities for reproducibility. All other target-memory, ABI, service and runtime limitations in this review remain. A later script or fixture change requires a fresh evidence review.
