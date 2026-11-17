# Independent review: `0x00131414` paired-store alias fix

## Recommendation

**Accept the pointer-arithmetic correction for the documented parser-state domain.** The production body now separately forms `u32*` pointers at byte offsets `p+4` and `p+8`; it no longer increments/indexes one `u32*` across two scalar members. At the observed caller, `p` originates from a live `AsdFontParseState*`, whose `data` and `chunk` fields are actual aligned `u32` subobjects at those offsets. The updated report correctly limits this object-model argument and the emulator tests to that caller/layout contract.

## Source, caller and object-model check

All hashes in the fix packet matched, including `leaf_matching.cpp`, parser TU, source checker, tests, function record and producer handoff. The body is:

```cpp
*reinterpret_cast<u32*>(p + 4) = a;
*reinterpret_cast<u32*>(p + 8) = b;
return p + 4;
```

This resolves the previously reported `fields[1]` issue: each typed pointer designates one distinct live `u32` member rather than computing `+1` from the `data` member. The actual parser calls `AsdFont_AttachResource(reinterpret_cast<u8*>(info), ...)` where `info` is `AsdFontParseState*`; the pinned layout assertions are offsets 0/4/8 and size 12. The C linkage, header declaration, parser-side alias declaration and `p+4` return agree. The source-contract checker now requires both independent typed stores and rejects array indexing in the body.

This still depends on `p` naming the start of a live `AsdFontParseState` (or an applicable live object with the same typed field layout), not arbitrary byte storage. The Unicorn harness's byte-backed buffer demonstrates emitted machine behavior, not C++ object lifetime for arbitrary callers. The observed one direct ARM BL site is `0x00121d1c`; no broad indirect/Thumb caller audit or loader runtime is part of this fix review.

## Fresh evidence inspected

The producer's two reports have the hashes recorded in its handoff and both pass:

| Seed | Leaf cases | Candidate | Parser window | Negative control |
|---|---:|---|---|---|
| 7 | 260 | 12 bytes, `060080e9040080e21eff2fe1` | `0x00121d14..0x00121d24` passed | `second_store_xor_1` detected |
| 20261024 | 260 | same source/object shape | passed | detected |

The candidate emits `stmib r0,{r1,r2}; add r0,r0,#4; bx lr`; the original remains `add r0,r0,#4; stm r0,{r1,r2}; bx lr`. The output is still 12 bytes but differs, so retaining the `non_matching` ledger status is correct. Reports compare full `r0-r12`, SP/LR/PC/CPSR, mapped data and stack, write addresses and continuation. The caller window uses representative prepared state, executes the actual parser argument setup/call/success continuation, and does not execute full resource parsing.

I did not compile or rerun tests because this review has compiler budget 0. I checked the frozen report contents and their hashes against the producer handoff.

## Remaining limits and next action

The accepted scope requires a live aligned state object with writable `u32` members at `+4/+8`. MMIO, invalid or unaligned pointers, concurrent observation, exceptions and partial-fault ordering remain untested; the original adjusts `r0` before stores while the compiled body adds four after the `STMIB`, so fault-time register state is explicitly outside the all-writable domain. No emulator/game runtime evidence exists.

Proceed to the integrator-owned batch closure and affected build checks while preserving the original reference and `non_matching` ledger classification. Do not treat this review as full parser, loader, or game equivalence.
