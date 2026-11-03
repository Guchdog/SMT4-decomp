# Independent review: 0x0027FBC8 production axis reader

## Finding

**Accept the bounded direct-function evidence and `non_matching` ledger classification; no counterexample found in exercised cases.** This does not establish the downstream `0x00254CA8` consumer when the reader leaves outputs unwritten, natural H2 input, or runtime integration. The source and declared reports were frozen during review.

The original code loads the global state/calibration pointer and selector before the unsigned mode rejection. Source retains selector 0/1/other mapping, unsigned `mode>=2` and state maximum checks, signed-halfword endpoint subtraction, source selection by flags bit 0, original hard-float deadzone helper calls X then Y, zero-threshold success, nonzero-threshold double-zero no-write return, null outputs, and X-before-Y stores. `0x00254CA8` may ignore a no-write return and consume its prior stack contents; this review does not establish those contents or safe replacement of that consumer.

## Independent evidence

- All 17 packet hashes matched at start and end. Fresh candidate audit using `python tools/h4_axis_reader_experiment.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-0027fbc8-independent-review/run003/direct --audit-contract --seed 20270113` exited 0: 146 cases, no differences, mode-bound mutation detected. The two out-of-domain invalid-output probes showed the same unmapped-write class and recorded write sequences. The audit's own pass condition requires fault class equality, not general fault-state equivalence.
- A separate 240-case deterministic randomized set (seed 20270114) varies full flag words, selector and mode boundaries, calibration endpoints, samples, thresholds and output targets including equal/reversed/null pointers and aliases into state, calibration and sample spans. It uses the existing runner's original-vs-candidate execution and observation functions, not a separately implemented ARM oracle. It reported zero differences and zero faults. Script and output are under this review's run003; arbitrary aliasing or unaligned/MMIO behavior is not established.
- A fresh private production TU compilation exited 0. Extracted production function body is 300 bytes and **byte-identical** to the fresh experimental object body, SHA-256 `5a8160055c296e73c46e94fe8a5aaf439e38c8e91a66e5855c9f8c04922dda6a`; each object has two ARM CALL relocations at offsets 0xB8/0xC4 to the same original 0x0019FE4C (symbols differ only by asm alias). Production object SHA-256 `264362a05d1f50d907784b043780938a4f3417699210edd76ce5ca3d29774787` matches run007.
- Independently parsed and replayed the pinned run007 IPS against the pinned original: one record, offset 0x17FBC8 length 320; exact staged-image equality and unchanged bytes outside slot. Resolving fresh production object calls at final VMA reproduces the staged 300-byte body and five ARM NOPs. Decoding ARM BL confirms 0x0027FC80 and 0x0027FC8C target even 0x0019FE4C and original camera call at 0x001FA948 targets even 0x0027FBC8. This is static interworking evidence, not execution on hardware.
- Frozen prior camera report records six matching synthetic original-callsite windows and a detected control, but explicitly excludes full camera task and full ABI/write-set/FPSCR/fault claims. Run007 direct/final-VMA reports each record 146 cases, no differences and matching fault observations. These reports do not demonstrate `0x00254CA8` composition or H2 lifecycle.

## Limits and next action

Direct cases operate on synthetic mapped RAM. The runner compares selected memory windows, output pointers, non-stack write order, saved r4-r11/d8-d15 and FPSCR, but does not compare SP, CPSR, all scratch registers or the complete stack; a successful return sentinel is not a direct SP assertion. The 146-case matrix exercises selected no-write and alias cases, not arbitrary overlap, concurrency, device memory or all floating-point modes. The same-input mutant checks the mode upper bound only; it is not an independent control for every no-write or alias path. Invalid-pointer probes are observations, not supported caller inputs.

Before claiming the H2 consumer path, characterize original `0x00254CA8` stack values and output validity on every `0x0027FBC8` no-write route, then validate the combined original-vs-patched caller with appropriate fixtures and runtime scenario. No emulator or runtime was used in this review.

## Provenance

Pinned reference SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; production source `7e81b244bad7117a7d69b693f5335a036a74087deb8d1b7ecc04a6eb6d3ee441`; experimental source `108b45003ec4908630514b615be7ebe6911fddb83c7448e4a8dacc403dd85aca`; direct runner `e4e80b7567446400e0b29c4703a4637c9c163170e349dd920f4a0e58cc3d1279`. Run003 direct report SHA-256 `07c36315efd440d8fa449f641547f5cb9a18d59b21d6494f8440a1d1e6a3dd62`. All checks were offline and exit 0.
