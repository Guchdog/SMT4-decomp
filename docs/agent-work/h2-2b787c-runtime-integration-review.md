# Runtime integration review: `0x002B787C`

## Decision

The evidence supports committing and pushing this **bounded, non-matching C++ conversion**, provided the commit description preserves the probe’s scope. It supports execution of the original and staged helper bodies in Azahar under a controlled fixture and the existing paired H2 scenario. It does **not** show natural reachability from H2: the normal callback uses selector 6, while the helper’s known `0x00286928` route requires normalized selector 11 or 19. Do not describe this as natural caller coverage, user-visible line-count behavior, or H2 acceptance.

Before publishing the documentation, label the initial status in `docs/agent-work/h2-2b787c-contract.md` as a historical contract snapshot or correct its stale claim that the ledger is `matching`. The current ledger, README, function record, and implementation record correctly classify the changed body as `non_matching`.

## Runtime artifacts and comparison

All 32 packet-declared input hashes match the run001 values, including the original image and runtime wrapper/report inputs. The staged production patch is pinned as follows:

- Original image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- One-slot staged image: `a915d0baee331366636fd9e25d55bfafa3554351f15d242fce3f52f9675d1dec`; 176-byte body in the original 176-byte slot, with two even ARM call targets.
- Final cumulative H2 image: `58493b9441dea722371d8a698356023c063c2994511fac472bbc724b291d8b29`.
- Final cumulative IPS: `4ec0281be1c29af99da2f5e1442be65f04ac7ee94e3903c7a5856dac89684391`; manifest records 560 records and a successful round trip.
- Final paired runtime report: `build/h2-2b787c-integration/runtime-probe-001/autonomous-gdb-verification.json`, SHA-256 `d57694f1200057a377d97bb9a66eb8d36aea0ed81dde20caa20bf2b5c444494e`.

The report contains 19 paired H2 checkpoint comparisons, all passing. At the paused `TitleConfig_Calc` checkpoint, the wrapper supplied a temporary stack handle and a table containing `F801, F802`, set guest PC to the real even ARM entry `0x002B787C`, and returned to the saved Calc checkpoint. Original and patched runs each hit once with the same `r0` handle and stack arguments, returned raw `r0=1`, consumed that result in a probe-owned handle word, and reported the original SP restored. The wrapper’s `finally` path restores the old handle bytes, table bytes, all 16 registers, and the temporary breakpoint. This is a controlled direct invocation: the probe-owned word is not a real caller’s result slot.

The cumulative runtime manifest explicitly says `natural_h2_path_reachability` is not claimed. That distinction is supported by the static caller contract and the report: selector 6 does not naturally enter the helper. Offline caller evidence remains two controlled `0x00286928` compositions (selectors 11 and 19), not runtime execution of that natural route. The other two static callers were not runtime-tested.

## Profile and scope safeguards

The runtime report pins the same original `code.bin`, cumulative image/IPS, CCI, Azahar executable and wrapper hashes. It records identical before/after hashes for all 12 pristine profile-seed files and all 58 runtime-support assets, and reports the private Azahar binary unchanged. Original and patched runs used separate staged app directories and loopback GDB ports. These safeguards support the paired comparison’s provenance and show that the profile seed and support assets were not modified.

The report does not establish physical input mapping, input scheduling, readiness, same-session re-entry, full lifecycle completion, persistence matching beyond its explicitly bounded outcome, natural helper reachability, or whole-game equivalence. `h2_full_acceptance_supported` remains false. The helper’s arbitrary malformed/sentinelless table behavior and the two other runtime callers also remain outside this evidence.

## Documentation and ledger audit

- `config/functions.csv` classifies `0x002b787c` as `non_matching`, correctly. Current totals recalculate to 10,933 `matching` functions, 26 `non_matching` functions, 8 `matching_span` entries, 3,127,548 matching-function bytes plus 484 matching-span bytes, and 11,076 non-matching bytes. README’s 3,128,032 exact-match bytes and 11,076 non-matching bytes are consistent.
- README, `PROGRESS.md`, `docs/function-records/0x002b787c.md`, `docs/functional-status.md`, H2 milestone status, and MODLOG accurately describe the direct controlled probe and preserve the `non_matching` label. H2 remains partially validated/open.
- `docs/agent-work/h2-2b787c-contract.md` is a historical pre-implementation contract report, but its opening structured handoff still says `matching` and carries the prior source hash without an explicit “historical snapshot” label. Clarify that record before publishing so readers do not mistake it for current ledger state.
- The implementation report records `python tools/progress.py --write` exiting 1 on the unrelated `script_vm_func_001ea928` parser failure in `leaf_batch46_b.cpp`. I did not rerun it. `PROGRESS.md` currently has the correct `0x002b787c` row; the unrelated parser issue is not evidence against this helper.

## Evidence status and next action

- Compiled production body: **reported passed**, 176 bytes; staged manifest pins the object and production source. This reviewer did not build.
- ARM differential: **reported passed**, 515/515 direct cases, two bounded caller compositions, six controls; final-address staged validation also reports 515/515 and both compositions. This reviewer did not rerun either runner.
- Caller: **partial**. Two offline compositions through one caller; no natural runtime call and two other direct callers remain untested.
- Runtime: **passed for the scoped paired scenario and direct fixture only**; 19/19 checkpoints, one direct invocation per side, equal `r0=1`, SP restored and probe consumption matched.

The coordinator can commit/push this bounded conversion once the stale historical contract header is made explicit. Keep the change classified `non_matching` and retain the reachability and H2 limits above in any release note. No compiler, test, runner, build, or emulator was run for this review.

## Read-only review actions

- Recomputed SHA-256 for all 32 run001 packet inputs; all matched.
- Parsed the staged image, offline validation, cumulative manifest, and final runtime JSON; checked the stated image/report hashes, 19 checkpoint results, helper hit/return fields, and profile/support before/after flags.
- Read the runtime wrapper’s fixture, breakpoint, consumption, and `finally` restoration code; read the current ledger, README, PROGRESS row, function record, implementation/contract notes, H2 status, and MODLOG.
- No runtime command, test, compiler, build, emulator, or write to implementation/ledger/status files was performed.

## Follow-up addendum — run002 (2026-11-02)

All 32 input hashes in the fresh run002 packet match. The corrected opening in `docs/agent-work/h2-2b787c-contract.md` explicitly dates the `matching` label and old source hash to the original-code audit snapshot before conversion, then points to the current `non_matching` implementation record. This removes the ambiguity identified above; no further contract-note correction is needed for this review.

I rechecked the cumulative image and IPS bytes against their manifest: image `58493b9441dea722371d8a698356023c063c2994511fac472bbc724b291d8b29`, IPS `4ec0281be1c29af99da2f5e1442be65f04ac7ee94e3903c7a5856dac89684391`. The final runtime report remains SHA-256 `d57694f1200057a377d97bb9a66eb8d36aea0ed81dde20caa20bf2b5c444494e`. Its 19 checkpoint records all pass; the direct probe records one original and one patched hit with raw `r0=1`, matching probe-owned consumption, and restored SP. The wrapper saves and restores all 16 registers and the previous handle/table bytes in `finally`. The fixture is still a GDB-directed call with `F801, F802`, not evidence of natural caller reachability.

The current ledger still classifies `0x002b787c` as `non_matching`. Its 10,933 matching functions, 26 non-matching functions, 8 matching spans, 3,127,548 matching-function bytes, 484 matching-span bytes, and 11,076 non-matching bytes agree with README. README, PROGRESS row, function record, functional status, and H2 milestone retain the bounded-probe caveat and keep H2 open. The implementation report still records the unrelated `progress.py --write` parser failure on `script_vm_func_001ea928`; I did not rerun it.

**Updated recommendation:** the earlier documentation condition has been resolved. The bounded commit/push recommendation stands: publish this C++ reconstruction under its truthful `non_matching` classification with the direct-probe and natural-reachability limits preserved. This does not promote the whole H2 milestone or claim natural runtime use of the helper.

Run002 review actions were limited to packet/input and report hashing, JSON/ledger inspection, and static source/documentation reading. No compiler, runner, build, test, or emulator was invoked.

## Follow-up addendum — run003 PROGRESS reconciliation (2026-11-02)

All 32 run003 packet input hashes match. The updated `PROGRESS.md` aggregate rows reconcile with `config/functions.csv`: 10,933 `matching` functions plus 8 `matching_span` records account for 3,127,548 + 484 = 3,128,032 bytes; 26 `non_matching` functions account for 11,076 bytes; the total is 10,959 functions plus 8 spans and 3,139,108 bytes. The exact matched byte total is 3,128,032 (99.6472%); the compiled-coverage label remains explicitly size-threshold-only and does not claim semantic verification.

Each subsystem row also matches a ledger aggregation. Matching and non-matching counts/bytes by category are: engine 2,555/768,816 and 5/1,396; ui 1,645/676,100 and 9/6,268; script_vm 1,199/444,372 and 2/1,916; camp 910/325,244 and 7/1,044; battle 575/236,480 and 3/452. Unknown (3,818/610,392), shop (111/39,976), crt (26/9,484), nn_sdk (64/8,852), unite (30/7,832), and raw_span (8/484) are all matching classifications. These categories sum to the aggregate totals above.

The retained integration full-build directory has 204 `.o`, 204 `.o.json`, and 204 `.o.d` artifacts. All 204 object hashes match the corresponding metadata hashes. I read the existing ELF objects and resolved each of the ledger’s 26 `non_matching` function symbols by name/address; all 26 compiled bodies satisfy the progress rule (`compiled_size >= min(16, original_size)` and `compiled_size / original_size >= 0.15`). Their original ledger spans total 11,076 bytes, split by category exactly as PROGRESS reports: engine 5/1,396 B, ui 9/6,268 B, script_vm 2/1,916 B, camp 7/1,044 B, battle 3/452 B. This is a read-only check of the retained outputs; it does not establish semantic behavior or replace the reported successful 204-TU build.

**Updated reconciliation result:** no mismatch found in the revised PROGRESS aggregate, subsystem rows, ledger counts/bytes, or retained full-build size evidence. The previous bounded commit/push recommendation remains unchanged. This addendum ran no compiler, build, runner, test, or emulator.
