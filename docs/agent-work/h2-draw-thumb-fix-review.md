# Independent review: H2 Draw Thumb-state correction

## Recommendation

**Proceed with rebuilding the combined H2 image.** I found no blocker to integrating this narrowly scoped pointer correction into that build. Treat the rebuild as the next validation boundary: verify code-cave placement/size, relocation handling, IPS integrity, and all derived image/profile hashes before any runtime comparison. This review does not approve runtime equivalence.

## Independent findings

- The pinned `extracted/exefs/code.bin` hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching the task packet. With text base `0x00100000`, the original instruction at `0x002CB358` is bytes `27 cd ff fa` (`0xFAFFCD27`), an ARM BLX-immediate. Decoding its signed displacement and H bit gives target address `0x002BE7FC`; BLX immediate switches to Thumb state. The target bytes `0f b4 1c b5 08 4b 06 aa` match the Thumb prologue noted in the prior audit.
- The production source now passes `0x002BE7FD` to `draw_call`, which is the correct Thumb-tagged pointer for that entry. The recorded production object is byte-identical to the hash in its manifest (`250598c55e1b175f1e9316425cc83810331340e92286346b8d5f87b9dd89adb4`), and the manifest binds it to the current source hash (`5ca7486aaa1244ae5e95b9e5073a7f1c49d1568cd6ad01139bc14bd86c0c0726`). In `ui_func_002cafd0`, the emitted call sequence loads literal `0x002BE77C` into `r10`, adds `0x81` into `r3`, then executes `blx r3`: target `0x002BE7FD`, so register BLX selects Thumb. This confirms the production call mode in the saved object.
- The candidate report's source hash matches the current candidate source (`7f51f1071d2e715e25009b61db0170850b4e89fb2f8efc8f29208608cc3751b0`); its object hash matches the saved candidate object (`b81e681ed76e104ad07cb26397758dd6495f21b43eddb0cf9f564f8ebb679fff`); and its pinned-reference hash matches `code.bin`. The report records 46/46 directed cases, no counterexample, and successful detection of both the wrong-stride and wrong-formatter-state controls.
- The updated harness checks CPSR.T at every named mocked service entry. The indirect cache callback is checked separately against its fixture's ARM-state expectation. The formatter trace includes the observed T bit. The intentionally even formatter pointer compiles and is rejected at the formatter hook with `CPSR.T=0, expected 1`; the correct original/candidate path records formatter mode 1. This is a meaningful mode-specific negative control, not just a trace mismatch.

## Evidence limits

The differential is an isolated callback experiment with mocked cursor, TBB, layout, format/font, panel/sprite, render-value, and touch helpers. It proves the callback under those controlled fixtures and catches this instruction-state defect. It does not prove real helper side effects, all possible callback targets, caller-created state, user input, the full `titleConfig` path, combined-image placement/size, or runtime behavior. Caller and runtime evidence remain `not_run`. The combined build must still confirm the cave's available space and patch chain before claiming the fix is present in the intended final image.

## Commands and checks

Reviewer performed read-only inspection only:

- Read the assigned packet, workflow, review inputs, source, harness, tests, manifests, and saved report: exit 0.
- `C:\msys64\clang64\bin\llvm-objdump.exe -dr --disassemble-symbols=ui_func_002cafd0 build/agent-work/H2-semantic/h2-draw-thumb-fix/run-002/production/leaf_batch43_a.o`: exit 0.
- Read-only Python decode of original bytes at `0x002CB358` and target bytes at `0x002BE7FC`: exit 0; decoded target was `0x002BE7FC`.
- No test, compiler, canonical build, emulator, profile, or debugger was run by this reviewer.

## Identity

- Production source SHA-256: `5ca7486aaa1244ae5e95b9e5073a7f1c49d1568cd6ad01139bc14bd86c0c0726`
- Candidate source SHA-256: `7f51f1071d2e715e25009b61db0170850b4e89fb2f8efc8f29208608cc3751b0`
- Runner SHA-256: `e56a5eda81d272c0d2c332561601f6d852426904145316cb724c57a7cc30bc33`
- Candidate report SHA-256: `cea9a1022b30ad2fe574e5668e63758ab8ae4a32d5e32ddb6e0bdcb1f836b3bb`
- Candidate object SHA-256: `b81e681ed76e104ad07cb26397758dd6495f21b43eddb0cf9f564f8ebb679fff`
- Production object SHA-256: `250598c55e1b175f1e9316425cc83810331340e92286346b8d5f87b9dd89adb4`
- Production object manifest SHA-256: `e902f1595c89b6a3a86ce72effbdaac49a462a9b54e64bc6b041855825d49576`
- Pinned original SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`

## Next action

Coordinator may integrate this pointer fix into a freshly rebuilt combined H2 image. Independently check output placement, size, relocations, IPS integrity, and final hashes; then decide whether to prepare the controlled runtime comparison. Preserve the distinction between this bounded semantic evidence and full runtime equivalence.
