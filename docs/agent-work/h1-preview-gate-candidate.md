# H1 Camp preview readiness candidate

This task reconstructs `Camp_IsPreviewReady` at `0x0025A2BC` as an isolated
no-argument C++ function. It reads the `FrameTexScene*` from `0x0043E278`,
checks bytes at scene offsets `+0xF2B`, `+0x1C`, and signed byte `+0xD6D`, and
conditionally calls `0x002BF9F0` with the object pointer `scene+0xD74`. The
helper's recovered C++ ABI is `s32 (*)(void*)`; the gate returns 1 when its
result is nonzero and 0 when zero.

The helper body reads and mutates an animation object, calls other functions,
and returns a sign-extended byte at object `+0x8A` on its main return path;
early paths may return constant 1. The differential harness stubs only this
external helper entry. It supplies positive, zero, and negative results, so it
checks the gate's branch and argument contract without claiming the helper's
animation effects.

The final report is
`build/agent-work/H1-semantic/h1-preview-readiness-candidate/sleep-20261025-preview-gate/checks/final/report.json`.
It records 52/52 original-versus-candidate cases and 3/3 detected negative
controls. Coverage includes every boolean branch combination, 0/1/0x7F/0x80/0xFF
field boundaries, and signed helper-result boundaries.

Evidence levels: compiled `passed`, ARM differential `passed`, caller `partial`,
runtime `not_run`. The actual H1 state-5 callback calls this no-argument gate
after the script-ready gate and branches on `r0`; the callback itself is not
executed here. The scene constructor allocates and clears the enclosing
`0xFEC` object, but the exact lifecycle of its nested `+0xD74` object and
runtime call timing remain unresolved. No emulator, physical input, or
whole-game behavior is claimed.
