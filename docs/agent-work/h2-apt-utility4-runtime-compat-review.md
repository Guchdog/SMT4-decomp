# Independent review: H2 exact launch command and frozen helper

**Task:** h2-apt-utility4-runtime-compat-review, run-007  
**Reviewer:** h3_read_return_review  
**Recommendation:** The helper is pinned, and the runner rejects command changes before process creation. The prior argv-linkage gap is closed for a fresh bounded runtime attempt after the prescribed offline gates.

## Input identity and executable selection

All 19 run-007 `input_sha256` entries were recomputed and matched, including the newly declared `tools/h2_azahar_rsp_probe.py` helper (SHA-256 `9d70a15ddd62ff6eedeccc9de54b88da7f2ec1bcda11de236c23ff64931a132b`).

The package compatibility pin hash is `3a2a9c195b4637ad686a32307782645fa8730eabd6f185e2358463987d479070`. Retained executable `build/h2-runtime/autonomous-verify-run001/original/app/azahar.exe` is SHA-256 `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`; the historical successful report is `e370da857f1738409decc468bee81859eb84cfc9278bac9d0c9d0b460d045b8`, has `passed: true`, and records that same executable hash. This is the binary associated with the earlier GDB run. The current rebuilt executable (`1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682`) is separately validated against its delivery manifest (`2d84d83fee84b4d1588d310084e0dc919cbd4c92fa41d4432497e696e2b0f286`).

## Exact argv validation

The command helper is now a declared and hash-pinned input. Its implementation builds exactly `[str(executable), "-g", str(port), str(game)]`. After `runtime_launch_paths` obtains same-file-verified executable and CCI aliases, `execute` calls `validate_launch_command(command, launch_executable, args.port, launch_game)` before recording the command or calling `subprocess.Popen`. Validation requires list equality against those four exact arguments, so a changed executable, option, port, CCI, or any extra/omitted argument raises before process creation. `Popen` receives the validated list and uses the alias executable's parent as cwd.

The focused test validates the correct four-element argv and rejects a mutation at each index plus an added argument. The end-to-end test supplies the expected helper shape, and the separate exact-command test covers the validator. Because the helper implementation is also frozen by the packet, the previous unpinned command-construction dependency is resolved.

## Alias, profile and title evidence

`GetShortPathNameW` remains Windows-only, uses a bounded 32,768-character buffer, and fails closed on an error/oversized result. It requires `os.path.samefile` for the original and returned path. `runtime_launch_paths` obtains aliases for the executable and CCI, projects the disposable save path from the alias executable directory, and rejects a path length `>= 260`. The execute path uses the returned aliases; cleanup still removes only the original owned stage.

`staged_alias_log_evidence` rechecks that alias-profile directory identifies the staged profile and the launch CCI alias identifies the staged CCI. It reads only the fixed staged-user log, capped at 8 MiB + 1, rejects oversized/out-of-tree/symlink paths, checks the alias profile path and expected `Program ID` title ID, and marks `cci_filename_log_check: not_used`. Thus the log establishes profile-path/title-ID observations; CCI identity comes from the same-file-verified path in the validated argv. The expected title ID `00040000000E5C00` matches `config/game_info.json`. Tests include wrong title, wrong profile path, mismatched CCI identity, command mutations, and path-length rejection.

The execute loop requires both profile and title checks before connecting to RSP and remains within the bounded log-wait window. Cleanup still preserves the staged diagnostic log only after child stop, records cleanup errors, and removes only its owned direct-child stage; it does not copy the staged save through the log path.

## Validation and limits

Command: `python -m unittest tests.test_h2_apt_utility4_caller_probe -v` — exit 0, **41 tests passed**. No build or runtime was performed. No source save or real profile was opened, copied, or hashed. This review validates the pinned helper, exact command gate, static path/log checks, and offline tests only. It supplies no new RSP/caller/runtime evidence and does not establish H2 equivalence.
