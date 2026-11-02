# Independent integration review: `0x002B8D24`

## Verdict

**The production conversion is ready to commit/push as a bounded semantic reconstruction.** I found no implementation, ledger, slot-layout, or patch-generation defect. Keep the H2 runtime evidence narrowly described: it establishes paired scripted behavior for the exact cumulative patched image, but does not establish that execution reached `0x002B8D24`. Before citing runtime as function-specific validation, add that explicit hit-status caveat to the runtime/function record.

## Provenance and staged artifact checks

All 24 entries in the prepared packet's `input_sha256` map recomputed exactly, including the pinned original `code.bin` (`1f98884f…cfaa558`), production TU (`988c31ce…9c33b9`), candidate, ledger, patcher, differential outputs, manifests, and reports. No packet input drift was found.

The ledger row is `0x002b8d24,360,non_matching,...`, which is truthful for a changed body. The production function in `src/engine/leaf_batch46_a.cpp` retains the reviewed selector branches, unsigned selector behavior, raw selector-6 word comparison/return, helper order and return values, selector-12 ascending five-entry loop and `+0x28` clear. It calls the expected even ARM targets `0x002af854`, `0x002bf030`, and `0x001384f0`; this replacement does not claim to reconstruct those helpers' deeper behavior.

I independently read the existing staged object (no rebuild): `battle_func_002b8d24` is 356 bytes, has no relocations, and its body SHA-256 is `f4d9d0d013bc79aff63bf1a0872c964aa984e67d90531955bbe379ae6253e14c`. It fits the 360-byte slot. The patcher replaces the final four bytes with one ARM NOP; the two final words of the body remain the fixed reset/process helper literals, while the setter target is synthesized from immediates. Patcher checks decode the ARM prefix, reject branch/PC-relative-load references to the final NOP word, validate all three helper targets and indirect-call registers, round-trip the IPS, and assert the tail bytes. This matches the staged result.

Recomputed standalone image and IPS SHA-256 values match the manifest: `36f3f5c0…358c45a` and `35aac4d1…77c125`. Replayed the IPS against the pinned original and got the exact standalone image. The preserved staged offline output hash matches the packet; it reports 116 direct cases, two original `0x00286928` selector-11 caller compositions, two selector-12 alias chains, and seven detected negative controls. The staged and cumulative image validation records both report 116 direct cases and two caller compositions. I inspected these preserved results and provenance; I did not rerun the suites.

The cumulative runtime image hash matches its manifest and runtime JSON (`f87b3149…4f94e940`); bytes outside the 360-byte slot are identical to the declared base composition. Its manifest records IPS replay success and the same final slot replacement. The paired runtime report's exact image and IPS hashes match the integration note.

## Runtime claim limits

The raw report supports 51 paired scripted actions and 19/19 matching checkpoints, including `g_ConfigBytes` and normalized `TitleConfigWork`. It also records `h2_full_acceptance_supported: false`, `controlled_lifecycle_completed: false`, readiness incomplete on both sides, same-session re-entry incomplete on both sides, and physical input mapping/scheduling unproven. Restart persistence outcomes match, but the lifecycle does not complete. The runner also uses a deterministic one-frame logical-query stub, so this is not evidence for physical input behavior.

The GDB verifier installs probes for TitleConfig and input helpers, but has no execution breakpoint/counter at `0x002B8D24`; **whether the helper was reached in either runtime run is unverified**. Recommended wording: “Paired scripted H2 behavior matched for 51 actions and 19 checkpoints on the exact cumulative image containing the `0x002B8D24` replacement. This run did not instrument or prove a hit at `0x002B8D24`; readiness and same-session re-entry did not complete on either side, and full H2 acceptance is unsupported.”

The base composition is pinned to `acd8b2f3…6a51446`, but its own manifest records mapper-source and FillPair-source identity mismatches against the objects used to produce those overlays. The function record and runtime note already disclose this caveat. The runtime result therefore applies to the supplied image bytes, not to a claim that every current working-tree source produced them. The semantic domain remains the documented valid, aligned, non-overflowing ordinary-RAM cases; arbitrary aliasing/faults/MMIO/concurrency, all manager patterns and the nested positive-record service path remain outside the demonstrated domain.

## Review actions and next step

Read-only work only. I did not rebuild, rerun offline suites, launch an emulator, or modify implementation, runner, ledger, or README. The only authored repository report is this assigned review file. Coordinator should add the explicit “helper hit unverified” sentence wherever runtime evidence is summarized before push, then accept this review. No further technical gate is required for pushing this bounded conversion; H2 remains open.
