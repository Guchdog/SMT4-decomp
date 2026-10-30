# Runtime compatibility guard

Run-003 launched executable SHA-256 1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682 and exited with 0xC000001D before the GDB listener. It produced no caller evidence. The retained executable SHA-256 8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a matches the previously successful GDB report. The runner now checks the retained executable, prior report and packet pins, while validating the current source build separately. The focused offline suite passed 34 tests. Independent review is required before launch. The precise reason for the run-003 exit remains unknown; the hash difference is not proof of its cause.

Independent review found cleanup required observed_binary_sha256. The guard now records that field and the focused test checks it. Re-review remains required.

Run-004 failed before GDB with the same status using the previously successful executable. The runner now preserves only the staged Azahar log, bounded to 8 MiB and hash-checked, before removing its owned stage. The focused suite passed 37 tests. Independent review remains required; no new emulator run occurred for this change.

Independent review found the revalidation hash was unbounded. Source and preserved log are now reread with the same 8 MiB plus one limit and compared to the initial bytes; the focused test forbids the unbounded hash helper. 37 tests passed. Re-review required.

Run-005 log recorded CreateDirectory error 206 at the long staged NAND path followed by an assertion. The runner now obtains Windows short aliases for staged executable and CCI, checks same-file identity, and refuses a projected disposable-save path of 260 characters or more. Cleanup retains the canonical owned stage path. The focused suite passed 39 tests; independent review and fresh offline gates are required before launch.

Run-006 reached a child-owned loopback listener and logged the intended title ID, but the old verifier expected a long profile path and logged CCI filename. The runner now checks that the short profile and CCI aliases identify the staged objects, requires the short profile path and intended title ID in the bounded staged log, and records that CCI filename logging was not used. The launch argv and staged hash are separate evidence. The focused suite passed 40 tests; independent review and fresh offline gates remain required.

Independent review requested a pinned shared command helper and explicit argv verification. The runner now rejects any command except the verified executable, -g, selected port and verified staged CCI, and the packet pins the shared helper. Wrong executable, flag, port, CCI and extra argument controls pass; the focused suite passed 41 tests. Re-review and fresh offline gates are required.
