# `0x00286928` semantic implementation and integration evidence

## Structured handoff

- **Task:** `h2-helper-00286928-convert` / integrator
- **Reference:** `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- **Function:** `0x00286928`, original span 820 bytes
- **Production ledger:** `non_matching` (compiled body differs from original)
- **Source:** `src/engine/leaf_batch45_a.cpp`, SHA-256 `962c018c8c02971ed5bf77cca52685dcda4d7cc2634868e8e7640009ddb17dff`
- **Offline evidence:** `build/agent-work/H2-semantic/h2-helper-00286928-convert/run001/offline-report.json`, SHA-256 `02ce909c877cbdbeacf01efde7d7be4745c9e69526c5c18d23e182fa5f6e7385`
- **Production staging:** `build/h2-86928-integration/staged-image/manifest.json`
- **Production differential:** `build/h2-86928-integration/staged-validation/production-offline-validation.json`, SHA-256 `222d4c3feaebda3d3ff06c74ad5a5fcd56200b27c68489b7c8a3cc2210af51323`

## Implementation

The C++ body implements all raw selector families and both incoming-`r2` routes. Five details were corrected after original-versus-candidate counterexamples and independently checked against pinned ARM: selector 11 writes mode 1; selector 19 uses the special pointer while retaining selector 19; selectors 13 and 15 write 1 to the common `+0x2D` byte; the `r2==0`, nonzero-state route calls `0x002B8D24` then writes state 3 and returns without the six-element update loop; and both `0x0028DF54` calls pass the word loaded from `P+0x18`. The full contract is in [the exhaustive contract](h2-86928-exhaustive-contract.md); [the independent review](h2-86928-post-diff-review.md) confirms those corrections.

The raw interface is six 32-bit words. Arg6 remains an opaque word; no float meaning is assigned. The candidate and production object each compile to 812 bytes, with 22 named `R_ARM_CALL` relocations and no local-section relocations. The staged patch resolves the calls to ledger-listed, even ARM targets, then writes two ARM NOPs in the remaining eight bytes.

## Offline checks

`python tools/h2_86928_experiment.py` passes:

- 296 direct cases spanning selectors `0..20`, high unsigned selectors, both `r2` routes, and state values `0,1,3,4,5,6`;
- four executions through the original callback code at `0x00221168`, with the helper's six ABI words captured and compared;
- six compiled mutation controls for selector mode, selector prewrite, selector-19 pointer, the `r2==0` state call, the `0x0028DF54` argument, and loop bound.

All direct callees are intercepted with deterministic contract-scoped stubs. The callback's upstream getters are also stubbed. This confirms the dispatcher against its pinned caller composition within the synthetic fixtures, while preserving unresolved callees as original production dependencies; it does not validate those callees' full behavior.

`python tools/h2_86928_staged_image_patch.py` builds the production TU, relocates its body at the original VMA, verifies the 820-byte slot and IPS round-trip, and checks that no bytes outside the slot change. The staged image hash is `32c7469f5cb8a6c8654d94f7fdc25e8c17733061081e92f585c819d109f05159`, and the IPS hash is `ace8db842a40af07e563c58b54d2fa71a057ad4d84c0190403107e58cef30862`.

`python tools/h2_86928_staged_validation.py` then compares the production staged image to the pinned original across 296 direct cases and four original-callback compositions; it passes. A wider `python tools/build_check.py --out-dir build/h2-86928-integration/full-build -j 4` compiled all 204 translation units. The two consumers with raw inline-assembly calls now declare the same six-word ABI, and both compiled in this build.

Independent validation is recorded in [the caller/control review](h2-86928-caller-control-review.md). It checks the callback composition, controls, slot size, and relocations and retains the same stub/fixture limits.

## Limits and next step

The dedicated autonomous loopback Azahar run is recorded in `build/h2-86928-integration/runtime-probe-002/autonomous-gdb-verification.json` (SHA-256 `7ea75a944d1f72c62ae76bbdc3f86c2d4c2a5d1f5fe0ded85b6c02110b3d3c76`). A breakpoint at even ARM entry `0x00286928` captured 129 original and 129 patched hits; all six ABI words and raw `r0` returns matched. The cumulative image and IPS hashes are `1616aa24873a72beafdc9ae12cf688f9d7575b11a3f9b3f366c77fddd1f4e703` and `cc63c2fe655bdc38c3c017531cc429de6eb9c9a287f6f9c5ad31126a8e5a2252`. The paired run matched 19/19 checkpoints across 51 scripted actions.

The cumulative manifest records source-identity caveats for its prior H2 base; runtime parity is tied to the exact recorded image/IPS bytes and is not a fresh source-rebuild claim.

This run does not meet full H2 acceptance: readiness and same-session re-entry did not complete; physical input mapping and scheduling remain unproven. The runner uses a one-frame logical query stub. Offline scenarios still use deterministic getter/callee fixtures, omit arbitrary invalid pointers, MMIO aliases and concurrent mutation, do not cover every caller domain, and stop before handler `0x001A07CC` continues above callback `0x00221168`. Keep H2 open and treat the runtime result as evidence for this paired scripted scenario only.
