# H4 axis calibration helper contracts — independent ARM review

## Disposition

The bounded reconstruction is broadly supported by the pinned ARM instructions and is suitable for static dependency mapping. Before using it as a precise numeric contract, clarify two edge details: selector 1's negation at `x=-32768`, and the architectural unordered behavior of the selector-2 VFP condition codes. These do not establish a different normal result for the parent-supplied halfword inputs, but they matter to the stated edge domain and any general helper contract. The unresolved `0x002C615C` divide semantics, arithmetic overflow, source-object writer, caller cadence, physical device identity, and movement meaning remain real blockers for implementation or behavioral claims.

## Identity and independent inspection

All 16 declared run-001 input hashes matched. The pinned image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. I independently disassembled the ledger spans in ARM mode and recalculated the call arguments and branches. Function-slice SHA-256 values:

| Span | Bytes | SHA-256 |
|---|---:|---|
| `0x0011C5EC` parent | 304 | `2a35630875d322688ae72bc8c19e0c0c46e0f304ae3e1d8e271228662832e55f` |
| `0x00128610` dispatch | 148 | `48ce373a70cffc3e46ab7700a97d84978a5a025b46209bc78edd15a87f1575fe` |
| `0x0013B9FC` selector 0 | 228 | `ad98481b1c072879fe11c7d2191ab9a0066cc7b18741340dd6f35630290e4531` |
| `0x0013B8F8` selector 1 | 260 | `770a2b4eecf554152fa2f3ad450d2c1a202d138f9a61f874e6477701defc160f` |
| `0x0013BAE0` selector 2 | 460 | `c7d6e316e724a50a1c5b8b9214c8cd949a6f0c694ad2f166ba8a0970ba4e6929` |
| `0x0013BCAC` post-process | 212 | `a8965324f22dadfac09f2c4b3558fb88748ab0e5fe8cddaaa5ab7d872679f636` |

## Caller ABI, A/B values, and selector behavior

At parent callsite `0x0011C668`, `r0=root+0x0C` is the calibration pointer, `r1=record+0x0C` is output-X, `r2=record+0x0E` is output-Y, and `r3` is the signed halfword value loaded from record `+0x0C` (X). The parent placed the sign-extended halfword from record `+0x0E` (Y) at `[sp]` as the fifth argument. Dispatcher `0x00128610` saves the output pointers, reads selector byte `[calibration+0x0C]`, restores X into `r2`, and loads the caller's stack word into `r3` as Y. It selects signed halfword A/B values and lays them at child `[sp]`/`[sp+4]`:

| Selector | A | B | Child |
|---:|---|---|---|
| 0 | `[calibration+0]` | `[calibration+6]` | `0x0013B9FC` |
| 1 | `[calibration+2]` | `[calibration+8]` | `0x0013B8F8` |
| 2 | `[calibration+4]` | `[calibration+0xA]` | `0x0013BAE0` |

All these loads are `LDRSH`; under this parent path X, Y, A, and B are sign-extended 16-bit values. Selector 2 reads only child stack `[sp+4]` after its three-register push, which is B; A is passed but unused. Selector values other than `0/1/2` take the dispatcher's epilogue without calling a child or writing either output. Its residual `r0` is the calibration pointer, not a boolean. For valid selectors, child `r0` is output-X and `r1` output-Y. Parent ignores the child return, and its own success/failure result is separate.

## Integer selectors: recalculated operations and boundaries

**Selector 0.** The child loads A/B from the two child stack words, computes `R = low32(x*x + y*y)` and `A2=low32(A*A)`, then uses signed `CMP`/`BGT`. `R <= A2` writes halfword zero to output-Y first and output-X second, and leaves residual `r0=0`. Otherwise `N=low32(R<<14)`; signed `N<=0` chooses `Q=0`, while positive N enters the divide/average loop using `0x002C615C`. The loop computes a candidate from `N / estimate`, adds the old estimate in low 32 bits, arithmetic-shifts right one, and repeats while the candidate is signed-less-than the old estimate. If `low32(B*B) <= R` under signed comparison, `D=low32(B-A)` and `P=low32(D<<7)`. Otherwise `P=low32(Q-(A<<7))` and `D=low32((Q ASR 7)-A)`. It then calls `0x002C615C` for X and stores its low halfword, calls it for Y and stores its low halfword, and returns sign-extended low-16 bits of D. The scaling-path store order is X then Y; the zero-path order is Y then X. Signed overflow in R, shifts, products, and the `R<<14` positivity guard is real. With signed-halfword X/Y, R reaches `0x80000000` for `x=y=-32768`; it is not a mathematical nonnegative sum after that wrap. Q-zero and divide-helper behavior remain unresolved.

**Selector 1.** A/B are signed halfwords, and `F=low32(B-A)`. For each coordinate, the negative branch computes `RSB #0` in 32 bits, signed-compares the result to A, and conditionally adds A to the original negative coordinate; the nonnegative branch signed-compares A to the coordinate and conditionally subtracts A. Thus for ordinary negatives the report's `(-value > A) ? value+A : 0` shorthand is accurate, but it is **not** mathematical negation at `x=-32768`: `RSB` wraps to `0x80000000`, which is signed-negative and cannot compare greater than any signed-halfword A, so that component becomes zero. Under the parent ABI this input is reachable. Let the resulting components be U,V and `R=low32(U*U+V*V)`. `low32(F*F)>R` is a signed comparison; that branch writes U then V directly. Otherwise `low32(R<<14)` signed-nonpositive selects Q=0, else the same divide/average loop computes Q. It calls the unresolved divider on `low32(U*(F<<7))/Q` and then `low32(V*(F<<7))/Q`, sign-extends each quotient's low halfword, and stores X then Y. Return is sign-extended low-16 bits of F. `F` itself cannot overflow for signed-halfword A/B (range -65535..65535), but `F*F`, R, and the shifted numerator can wrap and alter signed branches; no zero-Q guard is present.

## Selector 2: VFP comparisons and stores

The child takes signed 32-bit X/Y from `r2/r3` and B from its second stack argument; the dispatch path narrows these source values to sign-extended halfwords. A is not read. It computes `R=low32(x*x+y*y)`, converts that signed integer to float with `VCVT.F32.S32`, and `VCMP.F32`s it to zero. Exact zero stores X=0 then Y=0 and returns with `r0` still the output-X pointer. For the parent halfword domain, only `x=y=-32768` makes the squared sum wrap to `0x80000000`; that is a finite negative float, not zero. As a result it does not take the zero branch and later comparisons can choose the zero-output branch.

For nonzero R, direction selection compares low-word `y*y` and `x*x` as signed integers. It builds a ±36 boundary coordinate by a ratio of the lesser-magnitude coordinate to the dominant coordinate. With parent-supplied signed halfwords, the selected denominator is nonzero unless X=Y=0, which already took the zero path; both squares remain nonnegative signed values. The boundary squared length is compared with 1600. `VCMPE.F32` followed by `VMOVHS.F32` clamps it to 1600 on the ordered greater-or-equal case. ARM `HS` tests C=1, so an unordered comparison would also select the clamp. The next `VCMPE` compares input squared length to the clamped boundary; `BHS` proceeds on greater-or-equal **or unordered**, otherwise outputs zero X then Y. For the normal signed-halfword path these operands are finite; unordered is an instruction-level case, not observed runtime behavior. It could matter for unconstrained direct calls or exceptional state and should not be collapsed into ordinary `>=` semantics.

It then computes square roots, converts B and low-word `(B-40)` to float, and compares input R against low-word `B*B` converted with signed `VCVT.F32.S32`. `VCMPE` plus `BLT` selects interpolation when less; ARM `LT` is `N != V`, so unordered would also select interpolation. Direct and interpolation formulas use the VFP instruction grouping in the report. Both use `VCVT.S32.F32` before halfword stores; this is the toward-zero form (not `VCVTR`). Store order is X then Y, and in both branches the X halfword store occurs before conversion/store of Y. The 0x3F/0xC2/0x42/0x44 literals decode to 0, -36, +36, and 1600. A/B and integer conversions are bounded by signed halfwords on this caller path, but low-word R and the float formulas still have edge behavior; no FPSCR/fault differential evidence comes from static inspection.

For ordinary parent-supplied signed-halfword X/Y and B, the VFP compare operands before the `HS`/`LT` branches are produced from integer-to-float conversions and finite ratios with a branch-protected nonzero denominator; the ordinary path is therefore ordered. The condition-code interpretation above is still important for any broader input domain. On the ordered interpolation path, the guards imply `R >= boundary` and `R < B²`; hence `|B| > sqrt(boundary)` and the factor `B-sqrt(boundary)` cannot be zero. This removes a zero denominator for that ordinary path, though it does not settle pathological/unordered inputs, quotient range, VCVT exceptional results, or FPSCR effects. The exact exceptional conversion result/flags remain unverified.

## Parent post-process `0x0013BCAC`

The input `r0` is the record pointer. For word `+4`, it reads current bits 0x4/0x8 and prior word `+0`; it sets bit 0x8 iff `(current4 && current8) || (current4 && !prior8) || (current8 && !prior4)`, otherwise clears bit 0x8, and stores `+4`. It repeats the analogous predicate using current word `+8` and prior word `+0`, then stores `+8`. Next, if prior/current word `+0` bit 0x4 is set, it clears bit 0x4 and sets bit 0x8 in `+0`, storing `+0`. Finally it clears bit 0x4 in `+4` then `+8`, storing in that order. Other bits are preserved by the masks. The routine saves/restores r4 and returns with `r0` equal to the final word loaded from `+8` after bit 0x4 is cleared; the parent discards it. Stores are sequential, not a transactional update; aliasing/fault cases can expose partial effects. This verifies the bit transform only, not a physical device or control mapping.

## Recommendation and evidence limits

Accept the report's static maps for the bounded parent path, with the two edge qualifications above recorded alongside any later candidate contract. Preserve the observed low-word arithmetic and branch/store ordering. Keep unresolved the exact `0x002C615C` division semantics, pathological arithmetic and FPSCR effects, source-object writer, caller cadence, hardware identity, and any movement interpretation. This review is static only; it does not prove producer execution, runtime behavior, or semantic equivalence. No source/candidate changes, build, emulator, GDB, save/profile access, or guest-memory operation was performed.
