# Caller branch audit: `0x002e0dd0` / `ui_func_003bbfb0`

## Finding

The prepared task acceptance and the earlier independent review said that the non-5 path returns `0x81`. The pinned original `extracted/exefs/code.bin` refutes this. Capstone disassembly at `0x003bc070..0x003bc088` is:

```text
0x003bc070  bl      0x002e0dd0
0x003bc074  cmp     r0, #5
0x003bc078  movne   r0, #0
0x003bc07c  bne     0x003bc02c
0x003bc080  add     sp, sp, #0x14
0x003bc084  mov     r0, #0x11
0x003bc088  pop     {r4, r5, r6, r7, pc}
```

The branch destination is `0x003bc02c`, which is the stack adjustment before the epilogue. The `mov r0,#0x81` instruction is at `0x003bc028`, four bytes before the destination, and is skipped. Therefore, wrapper result 5 returns `0x11`; wrapper result 0 takes `movne r0,#0` and returns 0. The original function record's old “else zero” statement was correct. The prior review and the new task's requested change were based on a four-byte branch-target misread.

The runner now composes the original and candidate from the real BL site through the complete caller return for both configured gate outcomes. It retains the ignored-result caller window and checks the wrapper helper trace, all wrapper-level negative controls, returned `r0`, preserved callee-saved registers, SP, and final PC. `r1-r3` are caller-saved and are intentionally not compared across the wrapper call.

## Evidence scope

This proves only these two continuations under the runner's synthetic helper/object fixtures. It does not recover helper effects or run either caller's setup preceding the BL. No candidate C++ or production source was changed.
