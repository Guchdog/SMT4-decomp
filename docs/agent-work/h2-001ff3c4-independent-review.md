# Independent review: `0x001FF3C4` axis mover

## Recommendation

**Bounded approval for the typed C++ mover and its offline direct/caller evidence.** I recomputed the packet’s frozen-input hashes and independently ran the differential/caller harness into fresh `run007` using seed `20261111` and 121 seeded cases. It passed 171/171 direct cases, all four caller compositions, and the wrong-query-target control. I found no counterexample in the tested domain. The review specifically checked the corrected `C2/C1` branch and `B0/B2` wrapped-subtraction condition, plus placement of the outlined helpers.

## Frozen inputs and rerun provenance

Every `input_sha256` entry in the packet matched before execution. The runner’s source/object/report inputs remained pinned; because the frozen runner’s module constant points at `build/h2-1ff3c4-experiment/candidate.o`, I redirected only that in-memory constant to `build/h2-1ff3c4-direct/run007/candidate.o` before invoking the same `main()`/runner path. This avoided writing the packet-pinned object. The original pinned object still hashes to `29346e7b…531ae`; the run-local compiled object has the same SHA-256. The report pins source `c2416b15…79cc7`, image `1f98884f…aa558`, 880-byte candidate sequence `44c6adab…04717`, seed `20261111`, and sample count `121`.

Fresh runner report SHA-256: `d9c8933a1e841989d149253d1ec8d92b1abf791343076a14da44413350e44083`. It records 171 direct cases passed, no failures, four passing caller compositions, and `wrong_query_target_control_detected: true`.

## Corrected ARM conditions and C++ match

The pinned disassembly confirms the reverse primary branch at `0x001FF608` uses `SUBS r6,r2,#1; BMI`, and the reverse fallback at `0x001FF7EC` uses `SUBS r6,r2,#1; BPL`. The decision therefore depends on the wrapped subtraction result’s N bit. For example, offset `0x80000000` decrements to `0x7fffffff` (N clear); it must take the same decrement route as the original ARM. C++ computes unsigned `offset - 1u` and branches on `(decremented & 0x80000000u) == 0`, preserving this wrap condition. The direct suite includes `primary-reverse-subs-overflow` and `fallback-reverse-overflow`; both passed.

At `0x001FF660..0x001FF6B8`, the C2 branch loads original width, clamps a separate local width only for reset values, and advances/computes the upper comparison using the original width. It has no `count <= 1` gate when both C2 and C1 are nonzero. The C++ checks `c2`, returns only if `c1` is false, then uses original `width` for `offset + width` and `next + width`; `limited = min_signed(count,width)` is used only to store reset index/offset. The directed tests `C-count-zero-width-greater`, `C-count-one-original-width-advance`, and `C-width-greater-count` pass. I found no discrepancy between the frozen corrected contract, pinned ARM conditions, and implementation.

## Outlined helper placement and branch reach

The run-local object yields a 580-byte main body, 152-byte `axis_forward` and 148-byte `axis_reverse`, with no relocations in either outlined helper. The experiment concatenates them at offsets `0x000`, `0x244`, and `0x2DC`, respectively, for an exact 880-byte sequence. It fits within the original 1104-byte function slot. I reconstructed the sequence from the run-local object and checked all decoded direct branch/call targets: the ten relocated external `BL`s target only `0x00254CA8`; all remaining direct branches target addresses within `[0x001FF3C4, 0x00200444)`, the full 880-byte sequence. Thus the calls to the adjacent outlined helpers remain internal after integration. The runner also enforces exactly ten `R_ARM_CALL` query relocations and zero relocations in the outlined helpers.

## Differential and caller scope

The 171 direct cases include 50 named directed cases and 121 seeded cases. They cover primary/fallback priority, C count 0/1 and width-greater-than-count conditions, B offset subtraction/wrap, boundary grids for A/B/C/D and A2/B2, flags, and simultaneous-query precedence. The harness substitutes an identical deterministic ten-result query sequence for both original and candidate in direct tests; those cases establish the axis mover’s response to controlled results, not the original query service’s input/calibration semantics.

All four compositions passed: stable cursor, active cursor without input, logical bits, and initialized H2 cursor. Caller runs preserve the original query/input/calibration chain while executing the candidate mover; unrelated outer `TitleConfig_Calc` services are modeled. This is bounded caller evidence, not proof of all Calc states or natural H2 scheduling. The deliberately altered first query target was detected.

## Limits and next action

Valid aligned ordinary RAM is assumed. Physical input mapping/timing, runtime sound, complete query-service/calibration behavior in isolation, malformed pointers, MMIO/concurrent mutation, exact fault/read-order identity, and whole-game equivalence are unproven. No full build or emulator was run in this review.

**Next action:** accept the corrected mover as a bounded `non_matching` semantic replacement, retain original query dependencies, and have the integrator close the composed H2 batch before any runtime comparison.
