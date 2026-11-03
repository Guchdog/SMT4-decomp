# Contract reconstruction: unsigned divmod service `0x002C6C10`

## Conclusion

The pinned 48-byte entry is an unsigned 32-bit quotient/remainder routine, not a signed divider and not a zero-divisor trap. Its observable result is quotient in `r0`, remainder in `r1`. The current matching ledger row (`config/functions.csv`) accurately describes the original bytes. A readable C++ replacement can express the return pair, but a full-domain replacement that fits 48 bytes is not established by this static audit: ARMv6K has no hardware integer divide, so ordinary `/` and `%` need an unsigned helper or generated software division. The only nearby known divider, signed `0x002C615C`, is equivalent only on a bounded signed-safe domain for nonzero divisors. The required bounds are not established for both callers. A bounded conversion remains plausible, but needs an explicit domain contract and a compiler/size check before implementation is treated as feasible.

## Pinned code and control flow

Reference image: `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The 48-byte entry `[0x002C6C10,0x002C6C40)` has SHA-256 `bd920f09d9e327b25ea077882c91b9294d2542cac02f5d4e55f4de88e8010fb0`.

All 12 ARM instructions at the entry:

```text
002C6C10  MOVS r2,#0
002C6C14  RSBS r3,r1,r0,LSR #2
002C6C18  BLO  0x002C6264
002C6C1C  RSBS r3,r1,r0,LSR #5
002C6C20  BLO  0x002C6240
002C6C24  RSBS r3,r1,r0,LSR #8
002C6C28  BLO  0x002C621C
002C6C2C  RSBS r3,r1,r0,LSR #12
002C6C30  BLO  0x002C61E8
002C6C34  RSBS r3,r1,r0,LSR #16
002C6C38  BLO  0x002C61B8
002C6C3C  B    0x002C6190
```

`r0` is the unsigned dividend, `r1` the unsigned divisor. `MOVS` clears the quotient accumulator in `r2`. Each `RSBS` computes `(dividend >> k) - divisor` and sets unsigned carry; `BLO` takes the smaller-quotient entry when the shifted dividend is below the divisor. The final unconditional branch chooses the wider path. These six destinations are interior entries in the larger original division body beginning at `0x002C615C`, not independent helper functions. They are exactly `0x002C6264`, `0x002C6240`, `0x002C621C`, `0x002C61E8`, `0x002C61B8`, and `0x002C6190`.

The shared restoring-division tail accumulates quotient bits in `r2`, reduces the dividend remainder in `r0`, then finishes at `0x002C6270..0x002C627C`: subtract divisor into `r1`, select the unreduced value when the subtraction borrowed, form the final quotient in `r0`, and `BX LR`. For nonzero divisor this is ordinary unsigned `q = n / d`, `r = n % d`.

For `d == 0`, all initial unsigned comparisons select the wide path. The shared loop treats each divisor subtraction as successful and returns `r0 = 0xFFFFFFFF`, `r1 = original n`; there is no call to an error hook and no fault path in the service. This corrects the “divide-by-zero error path” description currently in the mode-0 query record: that description does not match the pinned `0x002C6C10` entry. It must not be inferred from the distinct signed helper at `0x002C615C`.

## ABI and effects

- Inputs: unsigned 32-bit `n` in `r0`, `d` in `r1`.
- Results: unsigned quotient in `r0`; unsigned remainder in `r1`. Both are observable even though the two inspected callers consume different halves.
- Scratch/clobbers: `r2` and `r3`; `r0`/`r1` are overwritten as outputs. Condition flags are changed and are not preserved. `r12` is untouched by this entry/tail.
- Preserved state: `r4-r11`, `sp`, and `lr`; no push/pop, memory access, or nested call occurs. Return is through `BX LR` at `0x002C627C`.
- A typed C++ ABI shape can express both output words as `u64`, packed as `(u64(remainder) << 32) | quotient`; ARM AAPCS returns the low word in `r0` and high word in `r1`. A quotient-only `u32` declaration loses the remainder required by one real caller.

## Actual H2 caller projections

### Mode-0 logical query `0x002B902C`

The path calls the service only after an unsigned logical ID `<31`, the mode flag/counter path has been selected, counter is not the early-pulse value 1, and `counter > threshold`. It passes `n = counter - threshold` in `r0` (therefore nonzero and no unsigned underflow) and the global selector in `r1`. It consumes only the returned remainder: after the call it tests `r1` and returns true iff that remainder is zero. The query does not consume the quotient.

H2 initialization is documented with selector 2, but the global selector is a runtime `u32`; no global invariant or maximum for the counter or selector is established here. If the selector is zero, the pinned service returns remainder `n`, so this caller returns false (for this path `n > 0`); it does not enter an error handler. The service's quotient would be `UINT32_MAX`, but this caller ignores it.

### TBB row count `0x002C0E4C`

This caller returns zero for a null table, wrong `TBL1` magic, or zero stride. Otherwise it passes `n = payload_size` (`table+4`) in `r0` and the nonzero row stride (`table+8`) in `r1`, tail-branches to `0x002C6C10`, and returns its raw `r0` quotient. It ignores the remainder. The denominator is proven nonzero on this path; the two table fields are `u32`, with no signed-range constraint established by the caller. The format's practical bounds may be smaller, but that needs a separate format/resource contract.

Thus the callers share the unsigned service but require different result projections and domains: mode-0 needs the remainder and has a positive numerator but no demonstrated signed-range bound; TBB needs the quotient and guards zero stride but likewise has no demonstrated signed-range bound. Neither caller justifies replacing the full unsigned service with signed division for all input words.

## Bounded C++ feasibility and next implementation question

A full unsigned, zero-divisor-compatible typed body could be expressed conceptually as an explicit `d == 0` pair plus a call to a known unsigned divmod primitive for `d != 0`. If that primitive returns quotient/remainder using the same pair ABI and has a fixed nonrecursive address in the final image, the wrapper plausibly fits 48 bytes. This audit found no pinned address/availability guarantee for such an alternative primitive. Letting the compiler lower `/` and `%` may introduce a runtime helper relocation (possibly this very service); without a compile/link/placement check, the size and recursion risks remain open.

Calling original signed divider `0x002C615C` is a bounded option only when `n` and nonzero `d` are both in `[0, INT32_MAX]`. In that domain it yields the same quotient/remainder pair. Its zero-divisor quotient differs from this service, although the mode-0 caller's remainder-only projection would still match for its positive `n`; TBB excludes zero divisor. Those caller projections do not prove the required signed-safe bounds, and a full service replacement would also need to preserve `d==0`'s `r0=UINT32_MAX` result. A `u64` wrapper with a zero special case and a direct signed-divider call is a plausible small candidate for a formally restricted domain, but fitting it is unverified because this task forbids compilation.

Implementation should first choose one explicit scope: (1) full unsigned semantics and a fixed known nonrecursive unsigned divmod dependency, or (2) a caller-bounded signed-safe domain with evidence for operand bounds and an explicit zero-divisor projection. Preserve/review the six shared interior entries before changing the 48-byte slot. Until that dependency and domain are fixed, keep the original implementation.

## Evidence limits

This is a pinned-binary and static caller audit only. I did not run compilation, differential tests, caller execution, emulator, or a full build. In particular, I did not verify code size or link resolution for any proposed C++ shape; physical counter ranges and TBB payload/stride limits remain open.
