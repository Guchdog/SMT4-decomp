# H4 calibration integer divide helper: `0x002C615C`

## Source identity and disposition

Static ARM inspection of pinned `extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The ledger span is 556 bytes, SHA-256 `3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9`; all 12 task input hashes matched. This is a hand-coded 32-bit signed quotient/remainder routine with an unsigned magnitude divider. The result registers are `r0=quotient` and `r1=remainder` on the normal path. No mathematical C++ substitute is justified without differential tests, especially for zero divisors and the signed overflow case. An independent review identified the zero-path stack writes and the selector-1 transformed/scaled numerator details; see the review report.

## Entry, sign handling, and outputs

Inputs are signed 32-bit dividend in `r0` and signed 32-bit divisor in `r1`. The initial `ORRS r3,r0,r1` branches to sign normalization when either sign bit is set. The sign path forms absolute magnitudes modulo 2^32, retains two sign bits in `ip`, runs the unsigned quotient/remainder core, then restores signs. From the `EOR` of divisor sign with sign-extended dividend and the final `ASR`/conditional `RSB`s:

- quotient sign is negative iff dividend and divisor signs differ;
- remainder sign follows the dividend;
- for nonzero divisor and non-overflowing quotient, the resulting behavior is signed division truncated toward zero, with `remainder = dividend - quotient * divisor` and `abs(remainder) < abs(divisor)`.

The nonnegative path uses an unsigned fast case when `dividend >> 1 < divisor`: it returns quotient 1 and remainder `dividend-divisor` if dividend >= divisor, otherwise quotient 0 and the dividend as remainder. Larger nonnegative inputs use an unrolled shift/subtract divider. The signed path likewise divides magnitudes using the unrolled core. The divider is 32-bit; no 64-bit quotient or widened intermediate appears.

Representative branch results derived from the instructions are `17/5 -> (3,2)`, `-17/5 -> (-3,-2)`, `17/-5 -> (-3,2)`, and `-17/-5 -> (3,-2)`. These examples describe the routine's ordinary nonzero-divisor path, not a separately executed test.

For `INT_MIN`, magnitude normalization wraps to the same bit pattern `0x80000000`. In particular, `INT_MIN / -1` follows the ordinary magnitude algorithm and returns quotient bits `0x80000000` with remainder zero; there is no explicit overflow check or trap in this routine. The result is the wrapped 32-bit bit pattern, not a claim that C/C++ signed division may use this case without explicit handling. Other intermediate caller arithmetic can also wrap before arguments reach the helper.

## Divisor zero and `0x0014E604`

The unsigned path detects zero after its shift setup at `0x002C61AC`; the signed path reaches the corresponding zero test and sign-adjust step at `0x002C62F0..0x002C6374`. Both enter `0x002C6378`, which saves `{r0,lr}`, sets `r0=0`, calls `0x0014E604`, then executes `pop {r1,pc}`. In the pinned image `0x0014E604` is an unconditional branch to `0x001524EC`, whose instruction is `BX LR`; it does not change `r0`. Thus the static current-image path returns quotient `r0=0` and restores the dividend value into `r1` (the signed path reapplies dividend sign before saving it). This is a concrete observation about the pinned instructions, not a general divide-by-zero exception contract. No fault, trap, process failure, or mathematical error result should be inferred. Any replacement must preserve or explicitly scope this unusual path and validate it independently.

## ABI and width

The routine modifies `r0-r3`, `r12/ip`, and condition flags. `r0/r1` carry quotient/remainder outputs. No instruction touches `r4-r11`; normal returns use `BX LR`. The zero-divisor path temporarily pushes two words and restores stack depth with `POP {r1,pc}`, preserving the original return address while using the saved dividend as remainder. There is no VFP operation. Normal paths make no explicit data-memory writes; the zero-divisor route executes `PUSH {r0,lr}`, writing two words at `[SP-8,SP)` before `POP {r1,pc}` restores SP and returns the dividend in r1. This is instruction-level evidence only: no independent ABI harness checked all flags, stack/fault states, caller assumptions, or platform interworking behavior.

## Direct calls and H4 calibration context

An aligned ARM linear scan with skip-data over `[0x00100000,0x003FE624)` reports 143 candidate `BL` sites to `0x002C615C`. An independent unfiltered aligned ARM-word scan found 144 candidate BL words; the difference is method-dependent, and either scan can decode embedded data. Linear scans do not discover Thumb, indirect, computed, or external calls; treat both counts as xref aids, not exhaustive caller graphs. The `BL` at `0x002C6380` inside this helper is the zero-divisor dependency call to `0x0014E604`.

The H4 selector-0/1 caller sites are directly confirmed in their pinned ARM function bodies:

- Selector 0, function `0x0013B9FC`: `0x0013BA78` divides the shifted squared magnitude by a positive power-of-two estimate in the iterative quotient/average loop; `0x0013BAB4` and `0x0013BAC4` divide low-32-bit `x*P` and `y*P` products by `r4`, then store the low halfword of the quotient to output X/Y. If prior wrapped arithmetic or the `r6 <= 0` path leaves `r4=0`, there is no local divisor guard before these calls.
- Selector 1, function `0x0013B8F8`: `0x0013B9B4` divides its shifted squared magnitude by the iterative estimate; `0x0013B9D4` and `0x0013B9E4` divide low-32-bit products of transformed intermediates `r6`/`r5` by the computed `r8`; the factor is `low32((B-A)<<7)`. They then store low halfwords. The `r7 <= 0` route sets `r8=0` and proceeds to these calls without a zero check.

The nearby calibration dispatcher `0x00128610` selects functions `0x0013B9FC` and `0x0013B8F8` for selector values 0 and 1, respectively. Their `MUL`/`LSL` operations are 32-bit; signed operand ranges, overflow, zero-denominator reachability under real calibration data, and valid calibration domains are not established here. Selector 2's VFP path and other unrelated direct callers are outside this helper-to-H4 mapping. This static trace does not show that any helper call naturally executed in-game or that these transforms represent physical input or player movement.

## Next evidence

Before implementing a C++ replacement, test the pinned original against compiled code for positive/negative sign combinations, zero divisor (including `0/0`), `INT_MIN`, `INT_MAX`, `INT_MIN/-1`, divisors ±1, exact/remainder cases, and all quotient/remainder output/ABI effects. Exercise the selector-0/1 caller with low-32-bit product overflow and zero/negative Q/F cases; preserve the distinction between helper contract and real calibration-domain evidence. No C++ was written; no build, emulator/GDB, save/profile access, guest write, or board edit was performed.
