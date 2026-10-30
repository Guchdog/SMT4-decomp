# H2 private Azahar diagnostic CLI follow-up: independent review

## Decision

**Accept the two bounded source fixes for a separately assigned runtime task.** Both outstanding findings are closed in the current source: the wrapper now compares independently verified profile inventories, and non-H2 calls at `0x002C1830` return before generic snapshots or guest reads. This acceptance does not authorize a launch, establish runtime capture behavior, or close H2.

## Finding closure

### Profile-pair isolation — closed

`h2_ctm_preflight.py:148-158` builds an inventory from each enumerated live file after matching its path, size, and SHA-256 to that profile's manifest. The caller invokes `_verify_profile_pair` on those two live inventories (`:225-236`). `_verify_profile_pair` checks the expected patched IPS path/casing/hash and absence from original (`:161-173`), then requires the same non-IPS paths with exact spelling and matching size/hash (`:175-187`). The manifest's `profiles_differ_only_by_ips` flag is still required but no longer serves as evidence by itself.

`test_h2_ctm_preflight.py:173-196` refreshes a self-consistent patched manifest after mutating non-IPS content, path casing, or file set, and expects the pair validator to reject each case; the IPS-only fixture is the positive control. This directly addresses the earlier counterexample. The tests use temporary fixtures and mocked child launch, not actual staged profiles.

### Non-H2 helper calls — closed

`azahar/src/core/h2_observer.cpp:58-62` defines the five H2 `(control_id, mode)` pairs. At query entry (`:355-375`), only those pairs are tracked. The explicit guard at `:377-380` returns for any other call to `0x002C1830` before the general allowlist and snapshot path (`:382-416`), so such a call cannot invoke the process-read callback or emit snapshot/query-return records. The existing allowlist is unchanged; other H2 observation sites retain their generic snapshots.

The revised negative control (`tests/test_h2_observer.cpp:251-270`) counts read-callback invocations and asserts zero reads, no snapshot, and no query-return record for a non-H2 `(99,77)` call. H2 pair/return matching remains covered in `:222-250`; mismatched-thread and pending teardown behavior is covered in `:271-289`. This is source/test review only; I did not execute the harness.

## Prior safeguards rechecked

- The observer requires valid movie-play setup before it is configured (`azahar-h2-observer.patch:88-116`), validates loaded title/process and nonempty movie path before playback (`:121-142`), and confirms playback mode, expected title ID, and exact header-validation result before emulation startup (`:143-157`). The movie patch resets stale state before `StartPlayback` and records header-validation status (`:337-359`). This closes the earlier no-movie/playback-state issue at source level.
- The wrapper checks the staging root and both profile trees, per-tree live file sets/sizes/hashes, staged executable/CCI/IPS identity and output containment (`h2_ctm_preflight.py:77-158,190-260`); it then passes the verified user root to the Qt binary (`h2_azahar_launch.py:30-40`). The Qt launch path applies that user path before constructing profile-backed services (`azahar-h2-observer.patch:162-195`). Invalid preflight raises before the wrapper reaches `subprocess.run` (`h2_azahar_launch.py:30-55`); negative controls mock and assert that launch is not called.
- Output-path containment, reparse-point checks, exact path casing/collision checks, and CTM title/revision validation remain present. The private feature patch remains separated from compatibility patches in the delivery manifest.

## Provenance and evidence

All `input_sha256` entries in this review packet match. The current feature patch hash is `408f1ee5d538f920b827c66a1d505b877e35d4a0a6ecc3045f750ca5451737ee`; delivery-manifest hash is `fc204a0737920c84d112fa2dbac05bb774ab7d8f25013a13ae8bd51ccdc6e1d6`. Each `feature_inputs` hash in the delivery manifest matched its current private source/artifact, and all four patch hashes matched their manifest entries. The reported binary exists, is 55,286,784 bytes, and hashes to `1f98a9cbef07a167226ccf4ea58280d73a05b35b7bd8f89b09fa74e71c15a233`, matching the report and manifest. The source pin is consistently `219d743a1e698101fe1ab8bef43e6563126c3c27`.

The fixes report records eight preflight tests, the C++ observer harness, two incremental build steps plus one Qt link, and delivery packaging as exit 0. These are saved implementation claims and were not rerun. Compiled evidence is `passed` in the implementation handoff; ARM differential and caller evidence are `not_run`; runtime is `not_run`. No actual staged profiles were inspected. No Azahar or wrapper process was launched. The fixes are ready for a separately scoped runtime review, but runtime profile selection, capture timing, and title-side input interpretation remain unproven.

## Review execution and limits

Read-only source/artifact inspection and SHA-256 verification only. No tests/builds, wrapper invocation, profile access, emulator, debugger/RPC/network, or input automation. Commands used were PowerShell `Get-Content`, `Select-String`, `Get-FileHash`, and `Get-Item`. An initial exploratory hash loop incorrectly resolved top-level helper files beneath the Azahar source subdirectory and emitted lookup errors; I corrected its path selection and then verified every manifest feature input successfully. No files were changed by that inspection.

## Next action

Coordinator may accept these source fixes and create a separate guarded runtime assignment. Keep the expected profile/image hashes and input trace fixed across the two runs; record incomplete/complete observer status and compare the scoped original-versus-patched captures. Do not treat this review as runtime authorization or H2 completion.
