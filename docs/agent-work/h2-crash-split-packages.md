# H2 crash diagnostic split packages

The two standalone patches partition the 4,218 bytes differing between pinned original and reviewed full H2 image. Initializer/dependencies owns 805 changed bytes; callbacks/cave owns 3,413. The stage manifest records each exact VMA range, image hash, and IPS hash. Every difference is owned once; applying the subsets in either order reproduces final SHA-256 `5e9aa08b449985f012e24400c45b4b037e4a0d5d069723b6cfa7ccf83300d8fa`. Range identities come from the reviewed run-013 placement manifest and mapper/fill production integrations. This is byte partition evidence, not proof either mixed image is behaviorally valid.

Launch one at a time, with the same shared game file:

```powershell
& 'E:\SMT4decomp\build\h2-manual-comparison\run-001\diagnostics\run-001\init-deps\app\azahar.exe' 'E:\SMT4decomp\build\h2-manual-comparison\run-001\pinned-title.cci'
& 'E:\SMT4decomp\build\h2-manual-comparison\run-001\diagnostics\run-001\callbacks\app\azahar.exe' 'E:\SMT4decomp\build\h2-manual-comparison\run-001\pinned-title.cci'
```

Before each launch inspect `app/user/config/qt-config.ini` for disabled GDB/RPC and verify in the log that its local profile and intended IPS were loaded. Each profile begins with identical approved system seeds and no game save; use equivalent game state and actions. Record whether Audio Settings opens or closes, the exact path to the log, and any other symptoms. Profiles diverge after use. The subsets retain original code for the other group and may interact with it differently than the full image; an observed crash or successful entry narrows investigation but does not independently identify the cause or prove full-image equivalence. No emulator was launched during preparation.
