# Independent review — `0x001078D8` logical input counter refresh

## Recommendation

Approve the production conversion only for the bounded synthetic-memory contract exercised here. Two independent fresh runs matched original execution across all direct and caller fixtures, and I found no counterexample. This does not establish physical input identity, buffer freshness, input scheduling/cadence, concurrent or MMIO behavior, or runtime behavior.

## Frozen-input and final-state review

I recomputed all 18 SHA-256 entries in the run002 packet; every pin matched. The pinned reference image is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; production TU is `89eae0a570bc408bad9704dc56c2c7f865bf37599f04dba79d1f27a4bdd06302`; runner is `c4ed34de257e55f91f48b64ed5cfa6c21c65a7445c043c40e567c63bbcaf512c`. The prior staged-image, slot-IPS, report, and compiled-object pins match too. I inspected the final function record, conversion note, the H2 table-producer audit, and the earlier independent static review. The final notes correctly keep physical meaning and scheduling open, and the production classification is `non_matching`.

I independently read the pinned ARM listing at `0x001078D8`. Its `0x001078E8` call passes the input handle from `0x004650A0` in `r0` and fixed output buffer `0x004E3C28` in `r1` to `0x0011C5EC`. It normalizes the return to 0/1 and writes availability at `0x004650A4`. The loop count is 31, the table begins at `0x004099C0`, and counters begin at `0x004E3C58`. The state word pointer held in `r6` is loaded from `counter_base - 0x30 == 0x004E3C28` and is never advanced; each row's mask pointer and counter/table pointers advance by 8/4 bytes respectively.

## Fresh differential and final-VMA results

I ran the required runner twice, each into a separate output directory:

- `python tools/h2_1078d8_experiment.py --out build/agent-work/H2-semantic/h2-titleconfig-001078d8-independent-review/run002/checks/seed-20261104 --seed 20261104` — exit 0; report SHA-256 `42b435e662f16c276b5d764667661ea36dd7d50849e821723ff94b429d199656`.
- `python tools/h2_1078d8_experiment.py --out build/agent-work/H2-semantic/h2-titleconfig-001078d8-independent-review/run002/checks/seed-20261105 --seed 20261105` — exit 0; report SHA-256 `3564aa1e006f967444e634a3fa6f6abb9cf085c68bc296f088480edbb3a54204`.

Both runs compile the production TU, resolve and link the helper call, construct the 164-byte exact-slot image, replay the IPS, compare original and staged execution at the final VMA, and exercise the original caller slice. Both reports say `all_passed: true`: 140 direct cases, four caller cases, zero mismatches, exact IPS replay, and no changes outside the 164-byte slot. The C++ body is 160 bytes and has one `R_ARM_CALL` relocation at body offset 20 to even ARM entry `0x0011C5EC`; the final linked call is at `0x001078EC`. A 31-to-30 loop-bound mutation is detected in both runs.

The direct matrix covers availability returns `0`, `1`, `2`, and `0xFFFFFFFF` against state words `0`, `1`, `0x80000000`, and `0xFFFFFFFF`; it exercises all 31 rows with gate resets, mask matches/misses, unavailable retention, wraparound from `0xFFFFFFFF`, and an untouched row-31 sentinel. For every row, the per-row fixtures check: successful matching increments modulo 2^32, successful missing-bit clears to zero, unavailable input with zero gate retains the old counter, and a nonzero gate resets the counter even when unavailable. Output comparisons include ordered writes to the availability/counter globals, resulting counters, fixed state word, reader arguments, return/stack state, and callee-saved registers.

The four caller compositions enter original `engine_func_0010B578` and compare original versus staged `0x001078D8`, with only the unrelated later service `0x00108B10` stubbed. The helper seam returns 0, 1, or `0xFFFFFFFF` and supplies four state words. All four compositions match and call the stubbed follow-up once. This is a bounded wrapper call slice, not proof of the actual caller's task/schedule or physical input source.

## Contract reading

For each row, a nonzero first table word forces that counter to zero. A zero first word checks signed-positive availability; since the helper result was normalized, only 1 is positive. With availability false, the counter is untouched. With availability true, the same fixed state word is ANDed with the row's second-word mask: no bits clears the counter; a match increments the unsigned counter with wraparound. The function is `void`. It leaves the pointer to state at `0x004E3C28` fixed for all 31 rows.

No discrepancy was found between this behavior, the C++ source, the pinned ARM listing, or either fresh staged-image comparison.

## Limits and next step

The helper result and state word are controlled synthetic fixtures. The evidence does not prove that `0x0011C5EC` populates all 31 logical bits, identify physical controls, establish source-buffer freshness, update cadence or scheduler registration, or cover races/MMIO and natural guest execution. Caller composition stubs the later service and does not establish runtime effects.

Retain the bounded semantic claim and truthful `non_matching` status. Broader acceptance needs independent evidence for actual buffer provenance and safe refresh scheduling, then a scoped autonomous runtime comparison. No emulator or full build was run for this review.

