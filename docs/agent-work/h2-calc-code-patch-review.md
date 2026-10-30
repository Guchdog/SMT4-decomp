# Independent review: H2 Calc code-cave patch

Status: bounded patch-construction review passed. No production promotion or H2 runtime equivalence is approved by this review.

## Findings

I found no implementation defect that blocks accepting this artifact as an experimental Calc-only patched image and final-address differential.

- **Image and placement:** The builder pins the configured image size and SHA-256, then verifies the reviewed `.text` base, file offset, size, aligned end, and exact 2,524-byte cave. It rejects occupied page padding, an entry outside `.text`, candidate overflow, and entry/cave overlap. The candidate body length is pinned at 2,096 bytes. The original extracted image still matches `config/game_info.json`.
- **Branch:** `arm_branch(0x001EA928, 0x003FE624)` produces the recorded little-endian ARM `B` instruction `3d4f08ea`. The builder decodes its signed 26-bit displacement and confirms the destination exactly matches the cave address.
- **Relocations:** The extractor returns four relocations. The rebasing routine accepts only relocation type 2 with an empty symbol and implicit addend, rejects duplicate/out-of-body offsets and out-of-body local targets, and rebases the four in-body values from the cave VMA. The manifest’s offsets/addends/targets agree with the tested outputs. These are appropriate for the reviewed candidate object; a future source/compiler/layout change must be re-reviewed instead of inheriting this conclusion.
- **Image/IPS integrity:** Only the original entry word and candidate cave body are written. The IPS records are in bounds and non-overlapping; applying the serialized IPS reproduces the constructed patched image. I independently checked the emitted IPS and patched-image SHA-256 values against the manifest, and checked manifest/report image identity fields. The implementation uses the repository’s own IPS applier, so an unrelated IPS parser or actual Azahar patch-loader check remains useful before distribution or runtime claims.
- **Differential:** The runner maps the patched full image at the original text VMA, so the callback begins at the real entry and branches into the body at its final cave VMA. It compares return/PC, work bytes, config bytes, call trace, faults, stop-at-return, and callee-saved registers/SP/D8-D15 through the shared Calc comparator. The two stored runs each pass 64 directed/seeded cases and report the same artifact hashes. The cave-plus-four wrong-branch control is detected because it fails to reach the return sentinel.
- **Focused verification:** `python -m unittest tests.test_h2_calc_code_patch -v` passed all five tests. Those tests cover local relocation rebasing, unsupported/out-of-range relocations, image hash and occupied-cave rejection, byte preservation, IPS reproduction, and truncated/out-of-range IPS rejection.

## Evidence limits and follow-up

The code-cave artifact and differential are sound within their stated model. Both callbacks share deterministic external service mocks; this does not validate the real helper implementations or title caller composition. The negative control exercises branch redirection only and does not independently corrupt each relocation. No real Azahar execution, H2 input sequence, edit/cancel/confirm path, persistence, re-entry, or restart was tested. The Calc semantic review’s signed overflow concern for an unbounded special-handle value remains; retain its fixture-domain limit or define the valid range/use explicit wrap semantics before broadening the contract.

Before production promotion, separately resolve the Azahar CLI startup/listener blocker and logical input seam, run the milestone caller/runtime scenarios with a field-by-field comparator, and obtain evidence for configuration persistence and restart behavior. Keep the production ledger classification non-matching for byte-different code and do not interpret this review as whole-milestone completion.
