# H2 private Azahar diagnostic CLI fixes: independent review

## Decision

**Request fixes before assigning runtime capture.** The two earlier findings are substantially addressed: observer mode requires a valid CTM and confirms playback started before the guest thread runs; the wrapper verifies both live profile inventories and the selected portable profile paths. Hashes and saved offline evidence are internally consistent. Two narrower issues remain: the preflight trusts the manifest’s assertion that original and patched profiles differ only by IPS instead of comparing the verified inventories, and the observer still emits full H2 memory snapshots for non-H2 queries at the shared query-helper PC.

## Findings

### [P1] Preflight does not prove original and patched profiles differ only by IPS

`h2_ctm_preflight.py:167-170` trusts `profiles_differ_only_by_ips` as a boolean. `_verify_profile_tree` at `:105-139` hashes each live tree against its own manifest inventory, but after both calls the only cross-profile check is that user roots differ (`:187-194`). It never compares the two verified inventories or file contents after removing the expected IPS entry. A manifest can list different non-IPS config/save files for each profile, set the boolean to `true`, and provide matching per-tree hashes; both trees then validate and the wrapper proceeds. This can make original-versus-patched captures start from different state while passing preflight. Compare the actual verified profile inventories and require identical relative paths, sizes, and hashes after excluding the one expected patched IPS, with the original IPS absent.

### [P2] Non-H2 logical queries still produce full H2 snapshots

`h2_observer.cpp` in the feature patch filters query-return pairing with `IsH2LogicalQuery` (`azahar-h2-observer.patch:445-449,742-762`), but `IsAllowlistedPC` still includes `0x002C1830` (`:523-546`). After query pairing, `OnBeforeInstruction` falls through to the generic allowlisted-PC snapshot code whenever `IsAllowlistedPC(pc)` is true (`:764-858`). Thus any other `(r0,r1)` pair reaching that same helper produces a full snapshot of `g_ConfigBytes`, title work/cursor, and touch state, despite being excluded from logical-query return capture. The negative-control test at `tests/test_h2_observer.cpp:251-263` checks only that no `logical_query_return` event appears; it does not assert that no generic `snapshot` or guest reads occur. Gate generic snapshots at this shared PC on the exact H2 query-pair predicate (or remove the PC from the generic allowlist and handle H2 entry/return explicitly), then extend the negative control to assert zero reads and no snapshot event.

## Verified corrections and controls

- The Qt frontend preflights observer startup: `--h2-snapshot` requires a game image and valid movie metadata/title/revision (`azahar-h2-observer.patch:88-116`). The loaded title/process check is before movie startup (`:121-142`); after `StartPlayback`, `ConfirmPlaybackStarted`, current program ID, and exact header-validation result are checked before emulation startup (`:143-157`). `ValidateLoadedTitle` also rejects empty movie paths (`:610-637`). `Movie::StartPlayback` resets stale playback state and records the current validation result (`:337-359`). These close the prior no-movie and stale-playback paths at source level.
- The wrapper validates the pinned delivery manifest/binary identity, then calls staging preflight before building its subprocess command (`h2_azahar_launch.py:14-40,43-55`). Preflight checks CTM program/revision, original/final images, staged CCI, both profile trees, executable identities, IPS contract, working directories, output containment, and profile selection (`h2_ctm_preflight.py:15-28,77-149,152-220`). Negative tests mock `subprocess.run` and assert it is not called on invalid manifests/files (`test_h2_ctm_preflight.py:124-131,145-269`). No actual staged profile was read in this review, consistent with the assignment.
- Profile-root and app-root containment, direct symlink/reparse checks, inventory case-collision detection, and exact live file set/size/hash checks are present. The current pairwise-inventory omission is separate from those per-tree checks.
- Query pairing is bounded to five `(control_id, mode)` pairs, stores pending callers per guest thread with an entry LR/SP, caps outstanding calls at 64, filters return captures by the matching pending return PC, checks return SP, and marks unmatched pending calls incomplete at teardown (`azahar-h2-observer.patch:445-449,548-552,705-729,742-762,861-875`). The test covers correct pairing, wrong-thread return, non-pair return exclusion, and pending teardown (`tests/test_h2_observer.cpp:222-281`). The generic snapshot leak described above remains.

## Provenance and evidence

All declared `input_sha256` entries in the prepared review packet matched independent SHA-256 checks. The corrected feature patch hash is `144197135ac4ce3cb9b943c82a11d40ebf6e38ef17ca4831aa32675c8551cf13`, matching the delivery manifest and fixes report. The delivery manifest hash is `238e84d74dd2147eb3c995d49c1988b0eaa8826736e41300e0dd5f80b6122cb7`. The reported binary exists, is 55,286,784 bytes, and hashes to `bfbbc077b19ef395d316e155401c5633eab82ea21b6c716937641dd0461b4c27`, matching the report and delivery manifest. The pinned Azahar revision is consistently `219d743a1e698101fe1ab8bef43e6563126c3c27`. The task packet owner is `h2_private_azahar_review` and the task is claimed by that owner.

The saved fixes report records two core/Qt builds, seven Python preflight tests, and the C++ observer harness as exit 0. These are saved offline claims, not commands rerun by this reviewer. `compiled` in the fixes handoff is `passed`; ARM differential, caller, and runtime are `not_run`. No emulator launch, live profile access, wrapper invocation, or actual guest capture is evidenced. Raw HID movie determinism still does not prove title-side logical input semantics, and H2 remains open.

## Review execution and limits

Read-only packet/source/artifact inspection and SHA-256 checks only. No builds/tests, wrapper invocation, staged profile inspection, Azahar launch, debugger/RPC/network activity, or input automation. Commands used were PowerShell `Get-Content`, `Select-String`, `Get-FileHash`, and `Get-Item`; all inspection and hash checks completed successfully. This report does not authorize runtime capture. The source-level review cannot prove actual profile behavior, compiler execution, or guest-query timing.

## Next action

Implementation owner should compare the fully verified original and patched inventories after removing the expected IPS and tighten the query-helper branch so non-H2 pairs produce no H2 snapshot reads. Add offline negative controls for both gaps, rerun focused offline validation, and request fresh independent review. After acceptance, the coordinator may assign a separate runtime task; H2 remains open until scoped runtime evidence is reviewed.
