# `0x0013B9FC` selector-0 input normalizer: static contract

## Scope and recommendation

This 228-byte ARM routine implements the selector-0, two-axis calibration path
selected by `0x00128610`. Static evidence supports an integer radial deadzone
and saturation transform with signed division through original helper
`0x002C615C`. The routine also has wrapped 32-bit intermediates, signed branch
tests, an integer square-root loop, and low-halfword output stores. A future
typed C++ conversion should retain `0x002C615C` initially and validate the
normal arithmetic domain against the pinned image. This report makes no claim
that arbitrary signed 32-bit inputs or malformed/overlapping memory are safe.

All ten packet input pins matched. Pinned `code.bin` SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The
function occupies `[0x0013B9FC,0x0013BAE0)` exactly (228 bytes, 57 ARM words)
with no literal pool. Its source is currently an exact-byte naked ARM body.

## ABI and saved state

The entry arguments are:

| Entry location | Value |
| --- | --- |
| `r0` | output-x halfword pointer |
| `r1` | output-y halfword pointer |
| `r2` | signed 32-bit x sample |
| `r3` | signed 32-bit y sample |
| `[entry_sp]` | signed 32-bit calibration A |
| `[entry_sp+4]` | signed 32-bit calibration B |

The prologue pushes `{r0-r12,lr}` (56 bytes), then addresses the two stack
calibrations at saved-entry-SP (`current_sp+0x38`). It does not allocate a
separate local frame. Before each return, it skips the saved input words for
`r0-r3` and pops `{r4-r12,pc}`. Thus SP and `r4-r12` are restored; `r0-r3` and
condition flags are caller-saved/changed. No VFP state is used.

At its one direct caller, `0x00128610`, these inputs have precise origins:

```text
r0 = output + 0x0C                 // output_x
r1 = output + 0x0E                 // output_y
r2 = signed sample_x snapshot
r3 = signed sample_y snapshot
[entry_sp]   = sign_extend(calibration[0])
[entry_sp+4] = sign_extend(calibration[6])
```

`0x00128610` is called by `0x0011C5EC` at `0x0011C668`. The reader loads
`output+0x0E` with `LDRSH`, writes that sign-extended value to its outgoing
stack argument, loads `output+0x0C` with `LDRSH` into r3, and passes pointers to
the two adjacent halfword output slots. Its calibration base is `context+0x0C`;
before selector-0 dispatch, `0x001285C4` has clamped calibration[0] to at
least 40 and calibration[6] to at most 145. The clamp does not establish
`B>=A` or a maximum for A. Samples therefore normally originate as signed
halfwords, but this routine’s own ABI accepts full 32-bit sample arguments.

## Arithmetic and control flow

Let `x=r2`, `y=r3`, `A=[entry_sp]`, and `B=[entry_sp+4]`. `MUL`/`MLA`, `LSL`,
and `ADD`/`SUB` here retain low 32-bit results. `CMP` uses signed conditions.
The behavior below describes the pinned instruction sequence, including its
32-bit wrap behavior; it is not a widened mathematical implementation.

1. Compute `R2 = low32(x*x + y*y)` using two `MUL`s and one `MLA`, and
   `A2 = low32(A*A)`. If signed `R2 <= A2`, write zero to output-y first and
   output-x second with two `STRH`s; return `r0=0`. No divide call is made.
2. Otherwise form `Q = low32(R2 << 14)`. If signed `Q <= 0`, set the scaled
   magnitude estimate `M=0`. If `Q>0`, initialize a power-of-two estimate and
   iteratively replace it by `floor((Q/current + current)/2)` through signed
   divide calls until the next estimate is not smaller. On ordinary positive
   `Q`, this is an integer Newton iteration toward `floor(sqrt(Q))`; loop and
   quotient behavior are delegated to original `0x002C615C`.
3. Compute `B2=low32(B*B)` and compare signed `B2` with signed `R2`:
   - If `B2 <= R2`, set `D=low32(B-A)` and `P=low32(D << 7)` (saturation branch).
   - Otherwise, set `P=low32(M - low32(A << 7))` and
     `D=ASR(M,7)-A` (unsaturated radial branch).
4. Call original `0x002C615C` with numerator `low32(x*P)`, divisor `M`, and
   store the low 16 result bits to output-x. Call it again with numerator
   `low32(y*P)`, divisor `M`, and store the low 16 result bits to output-y.
   These two stores occur x then y. The calls return quotient in r0; the
   routine does not use their remainders.
5. Sign-extend the low 16 bits of `D` into r0 and return. The r0 return is
   therefore zero for the deadzone path and `s16(D)` for the arithmetic path.

For normal positive non-overflowing radii with `0 <= A <= B`, this corresponds
to a radial deadzone and clamp: below/equal A both outputs are zero; between A
and B, the sample vector is scaled by approximately `(radius-A)/radius`; at or
above B it is scaled by `(B-A)/radius`. The implementation uses a fixed-point
integer estimate and integer quotient, so this expression is only a readable
description of the intended ordinary domain, not a replacement formula for
all bit patterns.

### Branch and dependency map

| Address | Condition/effect |
| --- | --- |
| `0x0013BA24` | signed compare `R2` vs `A2`; `R2 <= A2` takes the zero-output path at `0x0013BA2C` |
| `0x0013BA44` | signed compare `Q` vs zero; nonpositive Q selects `M=0` and skips sqrt iteration |
| `0x0013BA4C` | `Q <= 0` branch to magnitude selection at `0x0013BA90` |
| `0x0013BA5C` | initial estimate loop; power-of-two growth stops when shifted Q is no longer greater than the estimate |
| `0x0013BA88` | Newton loop repeats while the next estimate is smaller than the current estimate |
| `0x0013BA78` | `BL 0x002C615C` for `Q/current` in the Newton step; may execute repeatedly |
| `0x0013BA98` | signed compare `B2` vs `R2`, selecting radial scaling or saturation |
| `0x0013BAB4`, `0x0013BAC4` | two `BL 0x002C615C` calls for x/y output quotients |
| `0x0013BAD4` | Epilogue starts with `ADD SP,SP,#0x10` |
| `0x0013BAD8` | Move the saved signed delta to `r0` |
| `0x0013BADC` | Pop saved registers and return |

The three direct `BL`s all target ARM entry `0x002C615C` (even address). That
original helper is the signed 32-bit integer quotient/remainder routine: it
returns quotient in r0 and remainder in r1; this routine consumes only r0. The
divide helper has its own divide-by-zero path through `0x0014E604`; that path
returns quotient zero in r0 rather than trapping in the pinned original. Thus
when overflow or calibration inputs lead to `M=0`, the two output calls still
have an original, observable zero-divisor behavior. The remainder is ignored.

## Memory effects, return and alias limits

Direct stores are halfword stores only. The deadzone branch writes y then x;
the nonzero branch writes x then y. Output values are the low 16 quotient bits.
The arithmetic branch returns sign-extended low 16 bits of D, not either output
component. The saved register block is stack memory; nested divide calls can
also transiently push in their zero-divisor path. This helper has no global
access and no direct data writes outside its output halfwords and stack.

The actual wrapper passes distinct adjacent output pointers at `output+0x0C`
and `output+0x0E`. If an arbitrary direct caller aliases both pointers, the
store order is observable and the second store wins: output-x in the deadzone
path, output-y in the arithmetic path. Partial overlaps, output/calibration
aliasing, unreadable pointers, and faults are not characterized. The target
loads both calibration values from its incoming stack before output writes;
that does not justify claims for arbitrary aliases or concurrent mutation.

The arithmetic has important unvalidated corners. Squared inputs and products
wrap modulo 2^32; signed comparisons can then take unexpected branches. `Q`
also wraps on the 14-bit shift and can select `M=0`. `B<A`, negative direct
coefficients, and low-16 delta wrap are not rejected. The real caller's clamp
limits A only from below and B only from above, so it does not prove these
conditions absent. Do not claim all s16 pairs or all s32 direct arguments are
ordinary radial behavior without differential or runtime calibration evidence.

## Differential and conversion plan

For an eventual typed C++ implementation:

- Keep original `0x002C615C` first. Confirm its final argument ABI and return
  register use; compile only the affected TU, inspect all three final-VMA ARM
  call relocations, and verify each target remains even/ARM.
- Record output-x/output-y pointers, x/y inputs, A/B stack arguments, return
  r0, output halfwords, ordered memory writes, SP, r4-r12, and fault status.
  Compare the pinned original directly with the candidate at final VMA.
- Exercise selectors only through `0x00128610` for selector-0 path selection;
  for direct target tests include signed samples around `-32768,-1,0,1,32767`,
  calibration values around and across A/B (`A=40`, `B=145`, `A=B`, `B<A`),
  exact deadzone/saturation radii, just-below/above thresholds, and values that
  make `R2`, `Q`, products, or D cross signed/unsigned wrap boundaries.
- Include divisor-zero/reachable-overflow cases and compare original
  `0x002C615C` return/fault effects. Do not assume host C++ signed division
  matches the ARM helper for `INT_MIN/-1` or zero divisor.
- Add controls that swap A/B, use `LDRH` instead of sign extension, reverse
  output pointers, omit the deadzone, use Euclidean floating arithmetic, or
  store full words instead of low halfwords.
- Compose the original `0x00128610` selector-0 call with its exact samples,
  output slots, and post-clamp calibration pair. Separately compose through
  original `0x0011C5EC` with a pinned one-record source fixture so its clamp,
  ring-read success gate, and later output/state transformations are tested
  without attributing those behaviors to this callee.
- Verify body fit versus the 228-byte original extent, or propose and audit an
  explicit code-cave/entry-branch placement; replay only the target patch and
  check final-VMA call targets/interworking before any larger integration.

No compilation, execution, differential, full build, or emulator was run for
this static task. Physical input meaning, live calibration validity, ring
freshness, runtime cadence, and full wrapper behavior remain unresolved.

## Provenance

All ten run001 packet hashes matched. Pinned image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`;
target source `src/engine/leaf_batch30_a.cpp` SHA-256 is
`26f886237980a318d70649e0c9ccac3b2712df952014a1b9a302f0303c96705b`, and
`config/functions.csv` is
`84a4ece33babf6dc4f317dc913baed66a9179c63b3b4b2b4b9d963815ca2f2c8`.
Static Capstone ARM decoding covered all 57 target words, plus the dispatcher
call sequence and actual reader call setup. `0x0013B9FC` has exactly three
aligned ARM `BL` instructions, all to `0x002C615C`.
The divisor behavior cited above was cross-checked against the separate
`docs/function-records/0x002c615c.md` record (SHA-256
`e675bb53399e5570d82e574cd7b4a3fc5983209a39faa2b7fd1c2bf749f10621`); that
record is auxiliary context, not an input pinned by this task packet.
