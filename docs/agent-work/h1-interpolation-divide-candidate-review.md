# Independent review: `0x002C615C` interpolation divide candidate

## Review result

**Partial, favorable independent review; keep experimental and do not promote yet.** The pinned static contract, candidate source, linked object identity, and existing private Unicorn report are mutually consistent for the reported quotient/remainder and ABI projection. The report is finite isolated differential evidence, not a rerun in this review, formal proof, H1 caller execution, or game-runtime evidence. This review used no compiler and did not launch Azahar.

## Provenance checked

The review packet's declared input hashes were checked against the checkout before review; all 21 matched. The pinned image is `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The reviewed body is `[0x002C615C, 0x002C6388)` (556 bytes), SHA-256 `3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9`.

The candidate source SHA-256 is `078dc53d627479fb787ef3c45c093f8cebd3936c8bf4b562362f1b23d9cf0a30`. The linked `candidate.elf` is 66,564 bytes, SHA-256 `5c3894ca7d4cf2d818eee263aa027a01013339ce53fa450f1362b9d847e0e35e`. The existing report SHA-256 is `4dceee717a809b436827b2e369668827fc8b8d9abd9e5e5fee5b2a00c5077449`.

## Pinned behavior and result ABI

The pinned entry begins with `ORRS r3,r0,r1` and `BMI 0x002C629C`: if either operand has its high bit set, it takes a sign-aware path; if both are nonnegative, its quotient is ordinary unsigned division. The sign path works on operand magnitudes and restores quotient sign from operand signs. The remainder sign follows the numerator. The outputs are quotient in `r0` and remainder in `r1`.

For denominator zero, the body branches to `0x002C6378`, pushes `{r0,lr}`, sets `r0=0`, calls `0x0014E604`; that helper branches to `0x001524EC` (`BX LR`), then the divide helper pops `{r1,pc}`. This returns `r0=0` and original numerator bits in `r1`. Static inspection also confirms the pinned function returns through `BX LR` at `0x002C6384`; it preserves `r4-r11` and SP, while `r2`, `r3`, `ip`, and flags are scratch.

The candidate's `uint64_t` divmod result correctly lays out low word quotient in `r0`, high word remainder in `r1` under 32-bit ARM AAPCS. Its quotient-only wrapper exposes only `r0`. The source uses unsigned magnitude arithmetic and explicit sign correction, avoiding signed-overflow dependence for two's-complement edge patterns. The reported H1 fixtures do not include divisor zero; the nine zero-divisor directed observations separately check the original numerator bits in `r1` and zero in `r0`.

## Differential and control audit

The existing report records `passed: true`, 368 cases, no first mismatch, and `partial_selected_integer_domain`. The total breaks down as 35 H1 caller-domain cases, 77 directed cases, and 256 seeded cases (seed `20261025`). It records nine zero-divisor observations. All 368 result/data projections pass; `r0` and `r1` match in every case, faults are absent, and caller data memory matches. The negative control `quotient-plus-one` is detected: at 4096/2, original `r0=0x800`, mutant `r0=0x801`.

The directed set covers signed high-bit/boundary inputs, exact and zero quotients, `INT_MIN/-1`, and zero divisors. The seeded samples add breadth, not exhaustive proof. The report also separately records stack deltas rather than folding them into its pass claim.

## H1 caller and source declarations

Static instructions in the `0x002BF9F0` preview helper show four calls at `0x002BFBA4`, `0x002BFBC8`, `0x002BFBEC`, and `0x002BFC10` (the second address is `0x002BFBC8`). Each forms a numerator from signed-halfword coordinates, signed subtraction, then `LSL #12`; it loads row duration as an unsigned halfword and adds returned `r0` to the object's fixed-point x or y field. The two coordinate difference operands are each signed 16-bit, so the difference is `[-65535,65535]`; after multiplying by 4096 it remains representable as signed 32-bit. The exercised intended domain is positive duration `1..65535`.

`src/camp/unite_extras.cpp` and `src/script/script_vm_extras.cpp` declare this address as `u32(u32,u32)` and describe it as unsigned division. Those aliases fit their currently modeled contexts but overstate the binary contract for arbitrary 32-bit inputs: the pinned high-bit route is sign-aware. This review did not validate those non-H1 callers' runtime input domains.

## Stack scratch discrepancy and comparison boundary

The report does **not** establish byte-identical post-return stack memory. It reports that 359 nonzero candidate calls leave bytes at offsets `SP-32..SP-1`, while the pinned original has no nonzero-path residue. For all nine zero-divisor observations the original leaves its push/pop words at `SP-8..SP-1`, while the candidate leaves none. `SP` and callee-saved registers restore; the report separately compares data memory and returns. Under AAPCS, memory below the restored current SP is not caller-owned live stack state, so excluding those scratch bytes from the supported result contract is reasonable for these callers. It would be incorrect to claim full memory-image or machine-state equivalence; the existing report accurately exposes `stack_residue_matches_case_count: 0` and the residue counts. Code that deliberately inspects below-SP scratch, unusual unwinding/debug behavior, asynchronous observers, or non-AAPCS embedding is outside this evidence.

## Evidence limits and recommendation

- **Static:** pinned function/sign/zero paths and H1 callsite argument/result flow reviewed.
- **Synthetic/offline:** an existing private Unicorn ARM differential is reported for 368 cases, plus a mutation control. I inspected its report and artifact hashes; I did not rerun it.
- **Caller:** static-only; H1 duration positivity is the assigned exercised domain, but the full runtime state invariant is not established.
- **Runtime:** not run; no H1 scene lifecycle, production binding, integration, concurrency/interrupt behavior, or whole-game equivalence is demonstrated.

Keep the candidate experimental until coordinator review decides whether to assign integration and an H1 caller/runtime scenario. Do not alter exact ledger labels based on this finite non-byte-identical candidate.

