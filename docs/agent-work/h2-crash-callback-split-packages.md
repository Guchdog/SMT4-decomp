# H2 callback crash diagnostic split

The callback-only image differs from the original by 3,413 bytes: 1,800 in Calc entry/body and 1,613 in Draw/Secondary. The stage manifest lists every reviewed VMA interval and each IPS and image hash. The two subsets apply in either order to produce callback-only SHA-256 `84c6eb66a6f9a2a23d46e08df4eb04d723fef852c0b8bd3405945f9dbdd5ae32`. The diagnostic uses the original initializer and dependencies in both profiles.

Launch separately, closing each before starting the next:

```powershell
& 'E:\SMT4decomp\build\h2-manual-comparison\run-001\diagnostics\run-002\calc\app\azahar.exe' 'E:\SMT4decomp\build\h2-manual-comparison\run-001\pinned-title.cci'
& 'E:\SMT4decomp\build\h2-manual-comparison\run-001\diagnostics\run-002\draw-secondary\app\azahar.exe' 'E:\SMT4decomp\build\h2-manual-comparison\run-001\pinned-title.cci'
```

Both profiles start with identical approved seeds, no game save, and disabled GDB/RPC. Verify the selected portable user path and patch loading in the log, prepare equivalent game states, then record whether opening Audio Settings crashes and preserve the relevant logs. Profiles change with use. Each mixed image may exhibit interactions absent in the full patch; outcomes narrow the investigation but do not prove the cause. Neither patch load nor runtime behavior was observed during preparation.
