# Static ARM contract: `0x00254CA8` logical query and axis gate

**Scope:** Pinned ARM contract recovery only. No candidate, compile, emulator, or semantic-equivalence claim.

## Identity and ABI

Pinned `extracted/exefs/code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The ARM function span is 840 bytes at `0x00254CA8`; its byte-span SHA-256 is `efecf816aafcb6225ce4646006e54e9c3238b1c76b4ed5e0e371ee3f5cf49bfa`. It is retained as raw ARM in `src/engine/leaf_batch45_b.cpp`, whose SHA-256 is `ae63fc7efcafb9686d5c1b5db0bee5b10aed6ce8dcf3dafd023f051a8da36c52`; the ledger calls the original span `matching`. The contract is based on Capstone disassembly of pinned bytes.

Only the first three ARM argument registers are read: `r0` and `r1` are unsigned logical IDs; `r2` is a mode. `r3` and the two stack argument words at entry SP are not read. The return in `r0` is 0 or 1. The query helpers return zero/one, and both accumulated values are ORed. Unsupported modes leave both accumulated values zero, although a special-ID path can still run after the mode dispatch.

The prologue pushes `r4-r8,lr` (24 bytes), saves `d8` (8 bytes), and reserves 8 local bytes: 40 bytes total. It restores all of those before returning. `r9-r11` are not modified. VFP `s16/s17` alias the saved `d8`; caller-saved GPRs, `d0-d7`, FPSCR/condition flags are not preserved. The target is hard-float ARM/VFP code. It has no pointer/null check for its ID arguments because they are values, but it requires valid stack memory and the fixed global/query data used by its callees.

## Mode dispatch and ordered calls

It retains `id0` in `r8`, `id1` in `r7`, initializes first/second results `r5/r4` and combined result `r6` to zero, then dispatches on exact `r2` equality:

| Mode | Ordered direct calls | Result combination |
|---:|---|---|
| 0 | `0x002BFFBC(id0)`, then `0x002BFFBC(id1)` | `r5 = first`, `r4 = second`, `r6 = r5 OR r4` |
| 1 | `0x002B902C(id0)`, then `0x002B902C(id1)`, then `0x002C17D4(id0)` | The first two calls are unconditional. If the `2C17D4(id0)` result is zero, skip its second query and return the original OR. If it is nonzero, call `2C17D4(id1)`; if that too is nonzero, clear only `r4` (the second `2B902C` result), then OR `r5/r4`. |
| 2 | `0x002C17D4(id0)`, then `0x002C17D4(id1)` | OR the two results |
| Other | No base-mode helper calls | Base result remains zero; common special-ID logic still follows |

All direct calls are ARM `BL`; the `r0` result from each logical helper is consumed immediately. The target uses no indirect call. Mode-specific helper semantics are transitive: `0x002BFFBC` and `0x002B902C` consult logical counters/flags; `0x002C17D4` reads the ID table and tests its mask against a selected global state word. Their bounded records do not establish physical control labels or refresh cadence.

## Special IDs and VFP/calibration path

After mode dispatch, the routine compares each ID against `12,13,14,15`. If `id0` is special, it sets an internal selector to 1 and does not test `id1`; otherwise a special `id1` selects 2. If neither is special, it returns the base OR result. Thus `id0` has precedence when both IDs are special.

For a special ID it loads literal global address `0x00465278` and reads byte `0x00465288` (`base+0x10`). Zero returns the current OR without analog queries. Nonzero causes sequential logical queries `0x002C17D4(14)`, `(15)`, `(12)`, `(13)`, stopping at the first nonzero result. If all are zero, return the current OR. These are logical IDs; no physical mapping is proved.

When one of those queries is nonzero, it calls `0x0027FBC8(r0=sp,r1=sp+4,r2=0)`. It ignores that integer return, then loads two single-precision values from the local stack into `s0/s1` and calls `0x002820A4` using those VFP arguments; the float result is in `s0`. The latter routine is described by its source declaration as an `atan2` helper, but the target establishes only the passed VFP values and returned angle. The target multiplies `s0` by literal `57.29578f`, compares it with zero, and adds literal `360.0f` when negative. It retains the resulting angle in callee-saved `s16`; `s17` holds `360.0f`. If both local sample floats compare equal to zero, it returns the base OR before calibration comparisons.

It then queries IDs `14,15,12,13` again, in that order and short-circuiting at the first nonzero query. The selected query chooses one signed-halfword pair from `0x00465278`:

| Query that succeeds | Signed halfwords read |
|---:|---|
| 14 | `+0`, `+2` |
| 15 | `+4`, `+6` |
| 12 | `+8`, `+0xA` |
| 13 | `+0xC`, `+0xE` |

For ID 14, it computes signed `a-b`, converts it to float, adds 360, compares that with the angle, and has an additional comparison of the angle's float bit pattern against the literal 360 value before the endpoint checks. It then compares `float(a)` and `float(a+b)` with the angle; a branch to the common suppression block occurs when `a > angle` or `a+b <= angle`. For IDs 15 and 12, it tests `float(a-b) > angle` and then `float(a+b) <= angle`; either condition reaches suppression. ID 13 has the same effective conditions with the second comparison encoded as a branch back to the normal return when `a+b > angle`. The arithmetic is performed after `LDRSH` sign extension; the sums/differences are 32-bit integer operations before float conversion.

At suppression, selector 1 clears only first accumulated result `r5`; selector 2 clears only second result `r4`; it then ORs the remaining values and returns. Other angle/calibration branches return the unsuppressed base OR. The target makes no store to the global calibration block or caller object. Its own explicit stores are only `PUSH`/`VPUSH` saves; `0x0027FBC8` receives local stack output pointers. Any effects of deeper services are transitive.

### Axis-reader output validity caveat

`0x0027FBC8` is the calibrated axis reader. Its bounded record documents that invalid mode/source and some neutral/nonzero-threshold cases return zero without writing outputs; zero threshold can instead return one and write zeros. `0x00254CA8` ignores the status and always loads the two stack slots after the call. It does not initialize those slots before passing them. Therefore output validity in no-write cases is an unresolved dependency assumption: a candidate must preserve this behavior or define and test an accepted caller domain; it must not silently substitute zero samples. The helper can also call `0x0019FE4C` internally. `0x002820A4` and the lower services are not reconstructed by this contract.

## Global reads and transitive effects

Direct literal-backed reads in the special path are byte `0x00465288` and signed-halfword pairs within `[0x00465278,0x00465288)`. The logical query services read their table/state/counter globals as specified in their own function records. The axis reader reads calibration and input sample state; its outputs are the two local stack slots. No direct guest-global store is present in the `0x00254CA8` body. It does not receive the caller's cursor object, so it cannot directly update axis index/offset fields.

For the H2 path, the original `0x0029F278` wrapper calls `0x002D5618` before the axis mover, which sets `0x00465288` to one and writes 20 to the second halfword of each calibration pair (`0x0046527A`, `0x0046527E`, `0x00465282`, `0x00465286`). The first halfword of each pair is not initialized by that wrapper call and must be treated as existing global state. This makes the special-axis path eligible for IDs 14/15 in H2, while leaving its thresholds/state dependent on globals and input helpers.

## Caller census and H2 ID domain

A word-aligned ARM B/BL scan of the pinned image finds exactly ten direct calls to `0x00254CA8`, all inside `0x001FF3C4` at `0x001FF3F0`, `0x001FF404`, `0x001FF418`, `0x001FF42C`, `0x001FF440`, `0x001FF454`, `0x001FF468`, `0x001FF47C`, `0x001FF490`, and `0x001FF4A4`. No direct B or BLX target was found. Computed/indirect references are outside this scan. The input ID bytes are supplied from that caller’s axis record; the other direct callers of `0x001FF3C4` are documented in [its contract](h2-001ff3c4-contract.md).

For the initialized H2 `UiListCursor`, axis 0 IDs at `(+4,+8)` are `(6,15)` and at `(+5,+9)` are `(5,14)`. `0x001FF3C4` calls each pair in modes 0, 2, and 1 (in that order across its eager ten-call trace). Pairs `(+6,+10)` and `(+7,+11)` are both `(32,32)` and are called in modes 2 and 1; IDs 32 are rejected by each logical query helper's unsigned `>=31` guard, and are not special IDs. The initialized second axis has IDs `(3,12)` and `(4,13)` but threshold 1, so the H2 wrapper's signed `>1` gate skips calling this helper for that axis. H2's `(6,15)`/`(5,14)` pairs therefore exercise the second-ID special selector; after `0x002D5618`, the global availability byte is one. Which logical query or analog sector is active depends on the internal tables/counters, calibration halfwords, and axis-reader source, not on a proven physical input mapping.

## Fault/domain limits and differential fixtures

The public direct domain is two 32-bit IDs plus a 32-bit mode, but documented callers use modes 0/1/2 and table-valid IDs `0..30`; the H2 path additionally uses `32` sentinels. IDs above 30 return zero through the logical query helpers without counter/table reads; only IDs 12..15 enter the special path. An unmapped stack, query table/state, calibration block, or axis-reader dependency can fault. No null object case applies to the ID arguments. NaNs, infinities, unusual FPSCR state, uninitialized axis output slots, concurrent global changes, MMIO, and malformed calibration are not characterized. Physical controls, input scheduling, and frontend provenance remain unproven.

Recommended later differential fixtures:

- For each mode 0/1/2, test ID boundaries `0,1,11,12,13,14,15,30,31,32,0x7fffffff,0xffffffff`, plus IDs `(6,15)` and `(5,14)` with all four base-helper result combinations.
- Mode 1: vary first/second `2C17D4` results independently to verify its second-query short circuit and suppression of only the second `2B902C` result.
- Special path: IDs special in first only, second only, and both (check first precedence); global byte zero/one; no trigger, each of 14/15/12/13 as first trigger, multiple simultaneous triggers; check exact ordered calls.
- Use fresh global fixtures for each signed-halfword pair, test signed endpoints around each angle and wrap (`a-b+360`), signed sum boundaries, and angles around 0/360. Include exact zero-axis samples and values with high-bit/NaN/Inf float encodings where the reader can produce them.
- Inject `0x27FBC8` status zero with outputs untouched, status zero with outputs written, and status one with both outputs; record that the target ignores status. This exposes the stale-stack contract and must be contained by the documented valid caller domain rather than hidden by a default.
- Compare return `r0`, ordered helper trace/arguments, global read/write set, SP, `r4-r11`, `d8-d15`, and relevant FPSCR behavior; use a wrong mode branch, reversed IDs, omitted extra query, altered comparison, and wrong suppression selector as negative controls. Compose through original `0x001FF3C4` with H2 setup and keep its other dependencies original or separately controlled.

## Provenance and method

All 11 declared run001 input hashes recompute exactly. Pinned target source hash: `ae63fc7efcafb9686d5c1b5db0bee5b10aed6ce8dcf3dafd023f051a8da36c52`. Target machine-code span hash: `efecf816aafcb6225ce4646006e54e9c3238b1c76b4ed5e0e371ee3f5cf49bfa`. Read-only Capstone disassembly of the 840-byte target and callers, source/document cross-check, and aligned ARM branch census exited 0. No build or runtime activity occurred.
