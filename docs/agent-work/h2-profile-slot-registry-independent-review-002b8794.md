# Independent review: `camp_func_002b8794` (`0x002B8794`)

## Recommendation

Approve the typed reconstruction for the reviewed, bounded profile-slot contract and its documented `non_matching` classification. No counterexample appeared in the fresh differential: 12 direct cases and both original caller slices matched, all three mutation controls were detected, and the slot IPS replayed with no out-of-slot changes. The candidate occupies 272 of 304 bytes and has no relocations; its bytes differ from the original, so the non-matching ledger label is correct.

The evidence does not establish live manager lifecycle/concurrency, natural callback reachability, audio output, or runtime behavior. Direct synthetic fixtures cover nonzero registry modes; the two actual H2 caller slices invoke the helper six times each with `mode=0`.

## Frozen inputs and fresh run

Recomputed all 18 SHA-256 pins in the run001 packet; all matched. In particular, the pinned image is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, the candidate source is `7e81b244bad7117a7d69b693f5335a036a74087deb8d1b7ecc04a6eb6d3ee441`, and the experiment source is `75109f6d2f1fa948b84e81f277e336841de6d715fed2894066f13e78df98cb31`.

Ran the assigned fresh validation:

```text
python -B tools/h2_profile_slot_registry_experiment.py --out build/agent-work/H2-semantic/h2-profile-slot-registry-review-002b8794/run001/checks/fresh
exit: 0
```

Fresh `report.json` SHA-256 is `41e3341447bbd0dc11d69a8ab3441fbdb759b38ce5b4dcc2ce09793d32d60336`. It records 12/12 direct cases equal, 2/2 caller slices equal, no mismatches, three detected controls, IPS replay true, and no changed bytes outside the slot. The compiled body is 272 bytes in the 304-byte slot, with no relocations and `exact_matching=false`.

## ARM contract and implementation audit

I independently disassembled the pinned entry at `0x002B8794`. It first performs the unsigned `slot >= 6` check and returns; it then loads the manager pointer through `0x0043DA2C` and returns on null. For nonzero mode, it loads the first registry word at `0x0043DA50 + slot*4`, tests the signed-negative condition, and, when negative, scans six reservation bytes beginning at `manager+0x4B8`. Any occupied reservation claims the pair by writing priority and value to the first and second six-word registries (`0x0043DA50` and `0x0043DA68`) and returns early. Otherwise, matching registry priority/value clears both words to `0xFFFFFFFF` and falls through to the manager update.

The normal manager path writes a byte at `manager+0x494+slot*4` and a halfword at `manager+0x496+slot*4`. Priority 8 writes row `+0x3C = 4`, then `+0x34 = 0x12`, then `+0x38 = 0xFFFFFFFF`. Priority 7 and 9 through 17 write `+0x3C = 1`, then `+0x34 = 0x12`, then `+0x38 = 0xFFFFFFFF`. All other priorities write `+0x34 = 0x12`, `+0x38 = 3`, then `+0x3C = 0xFFFFFFFF`. The C++ uses volatile accesses and matching branch classes, widths, offsets, early returns, and store ordering. The C++ signature is void, so the direct comparison appropriately focuses on state, writes, fault, SP, callee-saved registers, and dependency events rather than assigning meaning to incidental `r0`.

The 12 direct fixtures cover slots 0–5, boundary slot 6, `UINT32_MAX` slot, null manager, default/special priority classes including 7/8/9/17/18, low-byte/halfword truncation, and registry claim, release, and no-claim paths. The report compares manager memory, manager/TBB globals, ordered writes, SP, callee-saved state, faults, and helper events. The three controls detect a changed slot boundary, wrong priority-8 class, and inverted registry-mode condition.

## Caller, placement, and build evidence

Both caller slices execute original code: the `0x99` TitleConfig initializer from `0x002F4DEC` and the `0xDC` nested callback from `0x00286B7C`. Each has six observed calls to `0x002B8794`, for slots 0 through 5, with aligned SP and `mode=0`. Full original-versus-staged slice results match. The scenarios also execute original wrapper/selector code; other external services are modeled by explicit hooks in the runner, so these are bounded slices rather than whole-path or runtime proof.

The pinned interworking report confirms the helper entry and the original wrapper branch target at `0x002B8C54` are even ARM addresses. The fresh compiler emitted no relocations. The staged image retains the original bytes outside this one 304-byte slot, the IPS replays to the staged image, and `changed_outside_slot=false`. Fresh artifact SHA-256 values: staged image `5c70b5fceae46ab5d1020ee5146b7e2944f9a8433e7a2313503c0e699cdbd478`; IPS `51c48c4f390f0882bae75823f775d543b5826ac0eef7000ca3291604aa0d1cdb`; object `264362a05d1f50d907784b043780938a4f3417699210edd76ce5ca3d29774787`.

The pinned affected-TU report records successful ARMv6K builds for `leaf_batch41_a.cpp` and `leaf_batch32_c.cpp` (2/2). This is focused translation-unit evidence, not a full build.

## Ledger and README

The ledger row for `0x002B8794` is `non_matching`, consistent with the different final body. Independent status counts are: 10,907 matching functions / 3,120,504 bytes; 52 non-matching functions / 18,120 bytes; 8 matching spans / 484 bytes. The 10,959 function rows plus 8 spans total 3,139,108 bytes. README exact-match bytes are 3,120,988 including spans, or 99.4228%; the non-matching total is 18,120 bytes. These totals reconcile with the ledger.

## Limits

The manager and profile/TBB records are synthetic mapped-memory fixtures. Registry nonzero-mode behavior is direct-fixture evidence; the actual H2 caller compositions use mode zero. The harness hooks other external service calls. This review does not prove real manager lifetime, concurrency/atomicity, natural callback reachability, profile population in a running title, audible output, or emulator/runtime behavior. The acceptance is limited to the tested ARMv6K implementation against the pinned ARM contract and those caller slices.
