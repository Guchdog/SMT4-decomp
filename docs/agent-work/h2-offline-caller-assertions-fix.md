# H2 offline caller reset-argument assertions

## Result

The caller-composition runner now checks consumed arguments for every reset
HLE observed in the State-10 ready/reset path. It also has a negative unit test
that perturbs the first touch-registration node argument and confirms the
validator rejects the mismatch. A separate test verifies that Sound_PlaySE
checks its consumed argument while tolerating different raw caller-saved `r1`
values.

## Sound_PlaySE contract

The pinned `src/camp/title_flow.cpp` declaration is
`void Sound_PlaySE(s32 se_id);` at `0x002B8B78`. Its initializer call site
loads `r0=0x99` immediately before the call. The original callee in
`src/engine/leaf_batch32_c.cpp` begins by preserving `r0` in `r5`; the incoming
`r1` is not used as an argument and is loaded from a PC-relative literal before
subsequent use. The runner therefore asserts `r0=0x99` for init and `r0=0x9f`
for the State-10 reset call, while retaining raw `r1-r3` in diagnostics. The
observed candidate `r1` difference is treated as caller-saved scratch, not a
behavioral mismatch for this one-argument callee.

The reset argument validator also checks, at the pinned State-10 call sites:
touch group/nodes `(0x11, 0x14)`, `(0x11, 0x15)`, `(0x11, 0x18)`,
`(0x11, 0x19)`; cursor mode `2`; environment name `title/title_top.bcenv` and
mode `0`; and model resource token `0xCAFE0088` with visibility `0`.

## Validation and limits

The fresh final report and structured handoff are stored under
`build/agent-work/H2-semantic/h2-offline-caller-assertions-fix/run-001/`.
The runner still uses matched HLEs for these helpers, so argument validation
does not establish their internal effects. It does not execute Calc callbacks
or cover State-1 UI, editing, persistence, Azahar/RSP, or whole-game behavior.
No emulator/runtime/input control was used.
