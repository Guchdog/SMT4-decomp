# H2 manual original runtime — in progress

The coordinator launched the independently reviewed unpatched portable stage through the Azahar CLI on 2026-10-26. The launched process is PID 11028, executable `E:\SMT4decomp\build\h2-manual-comparison\run-001\original\app\azahar.exe`, with the shared staged `pinned-title.cci` as its sole argument. Preflight checked the pinned executable and CCI hashes, that no original-profile IPS was present, and the explicit disabled GDB/RPC configuration. The isolated user profile was seeded from the independently reviewed package; no installed profile or save was copied or changed.

The running process command line confirms the staged executable and CCI. Its staged log reports `Debugging_UseGdbstub: false`, program ID `00040000000E5C00`, and file accesses under the staged `original/app/user` tree. It has not yet established Audio Settings behavior, input results, persistence, or a comparison to the patched profile. The human is controlling the visible emulator; no keyboard/mouse automation, debugger, RSP or RPC is used.

The user reported that the isolated original game works and looks the same as the supplied Sound screen. This is a visual observation; precise starting slider positions were not reported. The user was then asked to move BGM one notch, use B Back, reopen Sound, and report the observed result. That step is pending.

The user reported that, after making the requested change and using B Back, all sliders returned to their previous positions and sound came back. The response did not state whether a confirmation appeared, so that detail remains unrecorded. The user was next asked to change BGM by one notch, choose A OK, reopen, and report whether the change remained.

The user reported that A OK kept the changed slider position after reopening Audio Settings. The user was asked to close the isolated original window so its process can be restarted and cross-session persistence observed.

After the user closed the first staged process, the coordinator saved its log and a 15-file profile hash inventory and relaunched the same profile as PID 3364 with the same CCI. The user reported that after restarting, BGM returned to its original level rather than remaining at the position saved with A OK. This is a human observation in this disposable profile; the screenshot and exact configuration bytes at each step have not been captured. The user was asked to close the restarted original window before the patched run.

Both isolated original processes have now exited. The restart-session log and profile file hashes were saved separately. Between the two snapshots no NAND or SDMC file hash changed; several Azahar configuration/log/cache files changed. The user reported visual results for B Back, A OK and restart as described above. The exact slider starting value, all three option ranges and guest config bytes remain unmeasured, so this is a partial original baseline.
