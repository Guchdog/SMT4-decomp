# H3 title state-7 caller-composition review

## Review result

**Ready for integration review, with bounded offline caller evidence.** I independently inspected the caller-composition runner, its test, the submitted report, and the read-only candidate. The runner verifies the pinned caller's ARM `BL` at `0x001EA348` resolves to `0x0030A9A4`, then patches only that instruction to an aligned injected target containing the freshly compiled candidate. It runs original and patched caller paths under Unicorn with deterministic stubs for the declared dependencies.

Fresh rerun passed. The original and candidate both reached `0x001EA62C` without a Unicorn fault, transitioned work state `+0x9C` from 7 to 8, and had matching full manager/work bytes, `r0`, and the dependency call sequence plus the first two arguments for each dependency. The nonzero `+0x7C` guard case skipped dependency calls and preserved state 7 in both runs. Changing the caller's next-state immediate from 8 to 7 was detected. The pinned call target low bit was clear, and the generated candidate had zero relocations.

## Independent rerun

Command:

```powershell
python tools/h3_title_caller_composition.py --output C:\Users\altair\.codex\visualizations\2026\10\28\01a180a7-c0c9-7d30-ae82-d0e876a8ccb6\h3-caller-rerun
```

Exit code: `0` (`H3 title caller composition PASS`). Fresh report: `C:\Users\altair\.codex\visualizations\2026\10\28\01a180a7-c0c9-7d30-ae82-d0e876a8ccb6\h3-caller-rerun\report.json`, SHA-256 `5531f2680023b432f0b3189883194df57aff67ff2717fde6e5c6a34e9e0fd62b`.

The rerun compiled the unchanged candidate with ARMv6K hard-float flags, produced a 136-byte function with no relocations, and recorded candidate object SHA-256 `db22370011ea12b41cd05781a942467353091c9e6b29b5ae79e84af0be0539d2` and function SHA-256 `a2713b1ab89ad4e7f77a88a85601ec36e3677b472869f640ede1a216550dd278`.

Input hashes still match the prepared packet: runner `c4ea30e6b14396142235731baf2c81919512ddc2c939e53e2c10734dbeb59aa7`; test `a4460f3df6af81ed4f62679e40856aa259a41ab4ac62adbf77a5478b8b74dee9`; candidate `0f493bfb8d26688e52f6ad49d13eeab56109b66ac4d0097f69a998b052928b5e`; composition report source `d0302d292266e84b68b99fdfE79de78cbeec292b628be48bd3720b5b19502511`.

## Review notes and limits

- The rerun demonstrates offline caller composition for the pinned state-7 success gate and one nonzero skip-gate value. It does not validate state-8 polling, downstream load/save behavior, or a runtime game scenario.
- The stubs make dependency returns deterministic; their behavior is not validated here. Caller assertions compare dependency argument registers between original and candidate, but do not independently assert a specific expected argument tuple. The pinned original instruction stream remains the comparison baseline.
- The negative control specifically validates the post-call next-state assertion; it is not a general mutation campaign.
- `r2/r3` are retained in traces but excluded from call-argument equivalence as caller-saved. Runtime evidence remains `not_run`.

Recommendation: retain as caller-composition evidence for this bounded state-7 path, then have the integrator review the candidate contract/dependencies and run the integrated milestone checks. Do not treat this report as whole-game equivalence.
