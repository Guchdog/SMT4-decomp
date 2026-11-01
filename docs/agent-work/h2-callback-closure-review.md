# Independent closure review: H2 callback 0x00221168

## Scope and identities

Static review of frozen run-002 source, ledger, runner, function record and progress note; read-only inspection of production object and preserved generated image/runtime reports. No build, differential execution or emulator operation was performed by this reviewer. Source SHA-256 `5d14bc774791213e7198633abcf259704d7606619a8b5e2b5990f3d06dbb829e`; runner SHA-256 `5e52c77108ddbb00477d4187a7369ad09939a7f38a977d4ee8797acd48102b83`. The latest source change moves a marker comment; the function body is unchanged from the reviewed preview.

## Production source and build

The ledger entry retains address 0x00221168, original span 148 and production symbol/file, with status `non_matching`, appropriate for the changed body. The marker now directly precedes that definition. The function record describes target-specific aliases and limits. The actual production object `build/h2-callback-00221168/production-build/engine/leaf_batch30_c.o` SHA-256 `4094ba4c24d5109f34277b5cc3b581a82b89882a33c212dfff60d9d5469e6d19` matches its build manifest, which identifies the current source hash. Its extracted 140-byte symbol exactly equals the current experimental object body before relocation, and six R_ARM_CALL relocation offsets/names match the intended legacy targets. The production object comparison is not a production link or a claim of type-compatible cross-TU C++ interfaces; the aliases bind assembly-defined void symbols under a target-specific, non-LTO ABI assumption.

There are 204 object manifests in `full-build`. Its leaf_batch30_c manifest records the previous source hash `54ba63613d8acefdb41fa624c2e4bf70068305862e70456a6c14619ea5161028`; that build preceded the marker-only change. The separately rebuilt production TU records the current source and same machine-code body. The existence of manifests alone does not independently establish the full build command's exit code.

## Offline and runtime evidence limits

The current runner defines branch, write, stack-word and boolean-return mutants; each replacement must be unique and detected at least once. It compares call events, selected register state, selected memory and guest non-stack writes, with controlled fixtures and 64 seeds/cases in each of three modes. Selector 0x00296f60 and, in the real-helper fixture, dependency 0x002c1f28 remain stubbed. The progress note reports results including counts, but I found no preserved offline stdout/report that independently substantiates those counts in this review; inspecting the runner cannot itself prove execution.

The integrated image SHA-256 is `061058c4c7e3ddc548c0166b41d837ab1ee88293c5500853faf79e6737b4e757`; it matches the manifest and the runtime report's `final_image_sha256`. The full runtime JSON SHA-256 is `5dbaa3cbc46006796769c808f6eaa2d7fb0ef1accddd4263fc4661e86591394c`; the nested comparison JSON SHA-256 is `2b045053238638eec32a71591ff04f34f3eb83f5be5a52fdf445098c88090b1e`. Comparison reports 20 original and 20 patched events, normalized lists equal, callback 0x00221168 returning zero. The runtime JSON contains 19 checkpoint records and reports full H2 acceptance, physical input mapping and complete lifecycle as false; neither side reached readiness or same-session reentry. These results support the explicitly controlled paired scenario only. The expanded runner was changed after the runtime trace; the progress note correctly states that the regenerated image hash was unchanged.

Normal valid RAM with non-null slot +8 on the zero-state path remains a required bounded C++ domain; null fault equivalence, general aliasing, concurrent mutation and arbitrary indirect/interior entries are unresolved. The aligned-pointer/ARM-branch scans do not exclude Thumb branches or computed references. No full helper reconstruction or whole-game equivalence follows. Runtime image and IPS consistency, final call targets and their scope are separately recorded in the package review.

## Assessment

No new static counterexample to the scoped production wrapper was found. Its non-matching ledger classification and limited behavior record are consistent with the inspected artifacts. To strengthen reproducibility, preserve per-run stdout/exit codes, compiler and transitive runner identities, and hashes for offline cases and negative-control counts; keep the old full-build source identity distinct from the subsequent TU rebuild. Do not characterize the paired scenario as completed H2 lifecycle or physical-input equivalence.
