# Independent Review: Helper `0x00286928` Static Audit (`h2-nested-callback-final-helper-contract`)

**Review Scope:** Independent verification of `docs/agent-work/h2-nested-callback-final-helper-audit.md` against original ARM disassembly in `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) and caller `0x00221168`.

## 1. Disassembly and Caller Argument Verification

Independent disassembly of caller `0x00221168` (`0x002211b4..0x002211f4`) confirms the exact preparation of arguments for helper `0x00286928`:
- `0x002211b4`: `bl 0x0028686c` followed by `mov r7, r0` (stores arg1 in `r7`).
- `0x002211bc`: `mov r0, #0`; `bl 0x00296f60` followed by `mov r6, r0` (stores arg2 in `r6`).
- `0x002211c8`: `nop`; `bl 0x00289640` (stores result in `r0`).
- `0x002211d0`: `mov r1, #0`; `mov r2, r0` (`r2` = arg3); `str r1, [sp, #4]` (`[sp+4]` = 0, arg6).
- `0x002211dc`: `mov r3, r5` (`r3` = arg4 = 6).
- `0x002211e0`: `mov r1, r6` (`r1` = arg2).
- `0x002211e4`: `mov r0, r7` (`r0` = arg1).
- `0x002211e8`: `str r4, [sp]` (`[sp]` = 1, arg5).
- `0x002211ec`: `bl 0x00286928`.
- `0x002211f0`: `add sp, sp, #0xc`.
- `0x002211f4`: `pop {r4, r5, r6, r7, pc}`.

The epilogue of `0x00221168` strictly restores registers and pops PC without modifying `r0`. Therefore, the raw return value of callback `0x00221168` is identical to the raw return value of helper `0x00286928`.

## 2. Helper Body and Control Flow Structure

Disassembly of `0x00286928` (205 instructions, 820 bytes) confirms:
- **Stack frame:** `push {r0..r3, r4..r8, sb, sl, fp, lr}` (13 words = 52 bytes), `vpush {d8}` (8 bytes), `sub sp, #0xc` (12 bytes). Args 5 and 6 are retrieved from `[sp + 0x48]` and `[sp + 0x4c]`.
- **Selector Table:** Base table loaded from literal `0x0043E188`. With `r3 = 6`, the default branch selects pointer `[0x0043E188 + 4]`, and sets literal constant `0x035AB9FF` into `r5 + 0x10`.
- **Return Paths:**
  - Common exit epilogue begins at `0x00286BE8`: `add sp, #0xc`; `vpop {d8}`; `add sp, #0x10`; `pop {r4..fp, pc}`.
  - Return `r0 = 0`: Explicitly loaded at `0x00286BE4` (`mov r0, #0`) right before the epilogue. This path is reached following normal completion of `0x0028E974` and the 6-iteration indexing loop.
  - Return `r0 = 1`: Explicitly loaded at `0x00286C38` (`mov r0, #1`; `b 0x00286BE8`) and `0x00286C48` (`mov r0, #1`; `b 0x00286BE8` after callee `0x0028DF54`).

## 3. Conclusions and Assessment

1. **Audit Accuracy:** The findings in `docs/agent-work/h2-nested-callback-final-helper-audit.md` are 100% verified and accurate against the pinned ARM binary.
2. **Semantic Interpretation:**
   - Return `r0 = 0` is not an error state; it is the ordinary successful termination path of the helper for argument `r3 = 6`.
   - The enclosing handler wrapper `0x001A07CC` (handler 8) inspects the callback return: when the callback returns 0, handler 8 returns `r0 = 2` (pending), causing the script dispatcher to keep the task alive in State 2.
3. **Next Steps for Milestone H2:**
   - The callback and helper behavior is now fully characterized both dynamically (in run-002) and statically.
   - The remaining question for H2 completion is what event or counter triggers transition out of handler 8 into the subsequent script handlers (e.g. completion/fade/save).
