# Independent review: selector-1 normalizer `0x0013B8F8`

## Recommendation

**Accept the bounded candidate for coordinator promotion review.** The pinned ARM body, corrected signed-negation distinction, direct differential, original reader/caller composition, negative controls, slot/IPS checks, and both affected TU compiles passed independent review. No counterexample was found.

## Static audit and edge distinction

- Recomputed every one of the 13 frozen `task.json` input hashes; all matched. The pinned original image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; candidate source SHA-256 is `f3bb626aa41607471bc5e22a04d9e8232b44a158662c311f0356b93d3eed2793`.
- Independently disassembled the full pinned 260-byte ARM body at `0x0013B8F8`. It performs signed tests on X and Y, uses `RSB #0` for negative coordinates, then signed `CMP`/conditional `ADD`; for nonnegative inputs it uses signed calibration/sample comparisons and conditional `SUB`. It computes low-word `R=U²+V²` and `F²`, with signed `F² > R` branching to the direct store path. Equality takes the scaled path. Direct stores are X then Y; scaled quotient stores are also X then Y. The return is `SXTH(F)` in r0. The scaled path retains a zero magnitude when signed `R<<14 <= 0` and still invokes the divider; there is no zero-divisor guard.
- The corrected edge is real: caller sample `-32768` arrives as `0xFFFF8000`; wrapped `0 - bits` is `0x00008000`, positive 32768, and the signed comparison can pass against signed-halfword A. Direct `INT32_MIN` arrives as `0x80000000`; wrapped negation remains `0x80000000`, signed-negative, so it cannot compare greater than any signed-halfword A. The C++ explicitly performs unsigned subtraction then reinterprets the result as signed, preserving this distinction for the pinned ARM target.
- Fresh direct trace summaries include `x=-32768` (case 155, 6 divider calls) and `x=INT32_MIN` (case 157, 0 divider calls); both original/candidate traces matched. Caller case index 4 supplies `[32767, -32768]` through original dispatcher `0x00128610` and reader `0x0011C5EC`, with full output/context/counter/write/return/stack observations equal.

## Fresh validation

All build and report outputs are under `build/agent-work/H2-semantic/h2-input-normalizer-branch1-review-0013b8f8/run001/checks/`.

- `python tools/h2_input_normalizer_branch1_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-branch1-review-0013b8f8/run001/checks/reviewer-seed-20261102 --seed 20261102` — exit 0. Seed differs from the implementer's recorded `20261110` run. Results: 176/176 direct cases matched, 16/16 original reader/caller compositions matched, 27 zero-denominator observations matched, and all three negative controls were detected (`int32_min_wrapped_negation`, equal-radius direct-branch boundary, and direct-store order).
- Final-VMA candidate body is 252 bytes in the 260-byte slot; bytes differ from the original. Three `R_ARM_CALL` relocations target original divider `0x002C615C`, each even ARM entry (`bit0=0`). Pinned selector-1 caller at `0x00128698` branches to even ARM address `0x0013B8F8`. Exact-slot IPS replay passed and staged bytes differ only within this function slot.
- Compiled `src/engine/leaf_batch28_a.cpp` and `src/engine/leaf_batch29_a.cpp` sequentially to distinct reviewer-private object paths; both exited 0. Object hashes: `256aed41ef9d118aa66dd831b44c5d170606de296b83c1cc671d3d16334bb06d` and `a99542f991ab01fdeb4381d7a399d77610dee760d931e5a99adbf3dbf3fac70c`.

Fresh runner report SHA-256: `d31a5e9fa3cfc7a9ba35e6d30fa92b72837c28da3ab6e37f95cd499628bccf61`.

## Limits and next action

Evidence is limited to valid, disjoint synthetic ordinary RAM. Caller composition uses a controlled `0x0012A758` ring-reader seam; the original signed divider `0x002C615C` remains in the call chain. Aliasing, malformed pointers, MMIO, concurrent mutation, physical input provenance, runtime reachability, and whole-title H2 equivalence are not established. Low-word overflow behavior is matched for tested cases, not exhaustively proven over all inputs.

Coordinator may accept this independent bounded review and consider promotion under the `non_matching` ledger policy. Preserve the divider dependency and these domain limits in the integrated record, then perform the coordinator-owned batch closure and separately defined runtime scenario.
