# Independent second review: APT Utility-4 runtime dependency staging

## Recommendation

**The prior copy-all bypass is closed in the reviewed runner; accept this bounded staging review and proceed only to fresh pre-runtime gates.** The implementation task ID can no longer reach staging or process launch without a verified dependency manifest, and `stage_runtime(..., None)` fails immediately. The adjacent-DLL/plugin fallback is gone. The 59-asset package manifest and offline audit agree on paths, hashes, sizes, and total bytes. The focused unit suite passes 29/29. This does not establish an actual staged Qt runtime or runtime capture.

## Identity and hash verification

Review packet: `build/agent-work/H2-semantic/h2-apt-utility4-runtime-dependency-stage-review/run-002/task.json`, SHA-256 `5ea2a78054b7a40edcf845e34470b1d213b9916cacd7aa2d180e5b1a392b7ead`. All 12 declared packet input hashes matched.

Support packet `build/agent-work/H2-semantic/h2-apt-utility4-runtime-dependency-stage/run-002/task.json` declares nine input pins; all matched. The support handoff and offline report are pinned by the review packet.

Key hashes:

- Runner: `tools/h2_apt_utility4_caller_probe.py` — `5ba2036d3de01886e3a90c2e7c87cca97017e98baee1e44dfb5bef8cf4e3a826`.
- Tests: `tests/test_h2_apt_utility4_caller_probe.py` — `50ed30d171f17e99ff04c078f005b5e517a30a3fa9383b88f70587ab2a61c15e`.
- Support implementation task packet — `1797fa73f91124ba94d095f4989caca7151a9fbb80669825c2eaf9d8ad76262f`.
- Support handoff — `ec8caa84861812ef97773197709b46104ccc897bcf585d3bdf669311d4b6ec71`.
- Support offline report — `bfe85cf9bb8101b25ea5176e74f77a52870b5f606d001ab536ba475ddc708242`.
- Runtime dependency package pin — `bda8e1a43ac9e040e4a8165f1a9eec5a3656ff94d59d85cb50577959815428f9`.

I ran only the assigned test command:

`python -m unittest tests.test_h2_apt_utility4_caller_probe -v` — exit 0, 29 tests passed.

No build, Azahar/GDB, real stage, profile/save staging, or supplied-source-save access occurred.

## Bypass correction

`execute` calls `validate_task_and_inputs`, then immediately raises if `info["runtime_dependencies"] is None`. This happens before output-root creation, port reservation, stage-directory creation, or `subprocess.Popen`. The older implementation task ID can still be parsed for offline/static use, but it cannot proceed to executable staging without the verified dependency object.

`stage_runtime` independently rejects a `None` dependency manifest before touching its destination. It then stages the private executable separately and copies dependencies only via `copy_pinned_runtime_dependencies`. The prior branch that enumerated sibling DLLs, copied the whole `plugins` tree, or added `qt.conf` is absent. No adjacent-DLL/plugin fallback remains in this runner.

The two added refusal tests cover both boundaries: `execute` refuses a non-runtime task with `runtime_dependencies=None`, and `stage_runtime` refuses a missing manifest. The source ordering confirms rejection before staging/launch. The `execute` test could be made slightly stronger by patching `stage_runtime` and `Popen` and asserting neither was called, but the present guard is direct and precedes both operations.

## Pinned dependency audit

The package pin lists 59 unique runtime paths and 112,727,315 bytes. I cross-compared it with all rows in the support offline report: both contain 59 unique paths with identical path sets; every expected/observed SHA-256 and byte count agrees; each row reports unchanged and no error. The total byte sum agrees with the manifest and offline report. This is an audit-record comparison; I did not open or rehash the external `E:\emulador3ds` binaries.

The runner’s manifest validator checks schema/count, safe relative POSIX paths, duplicate paths case-insensitively, absolute existing source root, source resolution beneath that root, file type, SHA-256, and size. The dependency manifest itself is task-pinned. During staging each asset is checked immediately before copying, the destination is resolved under the disposable app directory, staged content hash/size is checked, and the source is rechecked after copying. Post-run finalization rechecks the sources and verifies that the staged non-user runtime file manifest stayed unchanged. Tests cover a two-file fixture with an unlisted sentinel, unsafe/missing/duplicate/hash-size mismatches, pre-copy source mutation, and post-copy source mutation.

## Limits and next action

The offline report says the producer checked all 59 source assets and found them unchanged. This review validates that report against the pinned manifest, not the external source binaries. Unit fixtures exercise the copy mechanism but do not perform an actual 59-file stage or prove Qt startup compatibility. The support handoff correctly marks runtime `not_run` and records no profile/save staging.

No remaining defect was found in the requested bypass or exact-manifest staging scope. A coordinator may prepare a fresh runtime packet with this runner/test hash, repeat and hash the four offline gates, then decide separately whether to authorize the bounded runtime capture. Runtime equivalence and the guest caller remain unproven.
