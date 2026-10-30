# Independent correction review: `0x002C615C`

## Disposition

Accept the run-002 report corrections for the two flagged items. Direct ARM inspection confirms the zero-divisor path's eight-byte stack save/restore and the selector-1 products formed from transformed components `r6/r5` and the scaled factor `r4=low32((B-A)<<7)`. The updated wording remains bounded: it does not prescribe a language-level divide-by-zero policy, claim C++ signed-overflow behavior, assert ABI/fault equivalence, or treat either BL scan count as an exhaustive caller total.

## Identity and recalculation

All 12 declared run-001 inputs matched. Pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Recomputed ledger slice `0x002C615C..0x002C6387` is 556 bytes with SHA-256 `3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9`, matching the frozen recon.

At `0x002C6378`, `PUSH {r0,lr}` is `STMDB sp!,{r0,lr}`: SP decreases by eight and two 32-bit words are written at the new stack top. `MOVS r0,#0` sets the quotient, `BL 0x0014E604` branches to `0x001524EC` (`BX lr`) without changing `r0`, and `POP {r1,pc}` reads back the saved dividend and return address and restores SP by eight. The signed zero-divisor route at `0x002C6370..74` reapplies the dividend sign before joining this sequence; the unsigned zero route branches directly. This verifies an instruction-level write on the pinned path, not a portable exception convention or stack-fault guarantee.

For selector 1, the pinned `0x0013B8F8` body computes transformed X/Y components into `r6` and `r5`, respectively. At `0x0013B9C8`, `LSL r4,fp,#7` forms the wrapped 32-bit `(B-A)<<7` factor. `MUL r0,r6,r4` at `0x0013B9D0` is the first low-word numerator before `BL 0x002C615C` at `0x0013B9D4`; `MUL r0,r5,r4` at `0x0013B9DC` is the second before the call at `0x0013B9E4`. Both use `r1=r8` as divisor. The corrected report accurately replaces the earlier shorthand that could be read as original X/Y times F.

## Scope and overclaim check

The corrected report says the zero path's observed quotient/remainder bit results are a pinned-image instruction derivation and explicitly disclaims general fault, trap, or mathematical-error semantics. It distinguishes the `INT_MIN/-1` bit pattern from defined C/C++ signed division and leaves signed-overflow language behavior unresolved. It labels the register/stack summary as static instruction evidence and disclaims an independent ABI/fault harness. Finally, it presents 143 linear-scan and 144 aligned-word results as candidate BL counts, explains the method difference/data risk, and excludes Thumb/indirect/computed/out-of-range references. Those are appropriate limits, not exhaustive-call-graph claims.

No further correction is needed for the assigned two items. The divider's detailed zero/overflow behavior still needs an assigned offline differential/ABI exercise before implementation claims; this review itself is static. No source change, build, emulator/GDB, save/profile access, or guest-memory write was made.
