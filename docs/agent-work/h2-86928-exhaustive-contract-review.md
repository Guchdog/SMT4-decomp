# Independent contract review: `0x00286928`

## Recommendation

The exhaustive static contract is detailed enough to guide an implementation, but **do not treat it as implementation-ready until the three contract corrections below are applied**. They affect selector-derived writes, a branch's call/return behavior, and the documented invalid-pointer fault location. I found no issue with the AAPCS/VFP frame description or the listed 22 direct BL sites. The contract is appropriately cautious about the run-002 trace; an older nested-callback review is not.

## Identity and independent checks

All 13 hashes declared in the prepared packet match. The pinned original image is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. I parsed the 410 `.hword` values under `engine_func_00286928` in `src/engine/leaf_batch45_a.cpp`; all 820 bytes equal the pinned image slice, whose SHA-256 is `13599a73fefa7f8ed72d8251e769b2302486c973169be524785830699b7f7c6c`. The ledger remains `matching` for that byte-identical body.

I disassembled the pinned ARM span at `0x00286928` and independently checked the reported selector and state paths. I also decoded each of the 22 listed call-site addresses: every one is an ARM `BL` to `0x00286928`, and its containing ledger range/name matches the inventory. This confirms those 22 direct sites only; it says nothing about indirect dispatch or Thumb references, consistent with the report's limitation.

## Contract corrections required

1. **Raw selector 15's `+0x5E` value is zero, not one.** At `0x00286978..0x0028697C`, raw 15 branches to `0x00286A38`, which sets normalized selector `r6=11`, sets `r2=1`, and explicitly sets `r1=0`. The common store at `0x002869B4` writes `r1` to `P+0x5E`; the later flag check at `0x00286A4C` also tests `r1`, so raw 15 does not set `P+0x5F`. Correct the raw-15 row of the selector table in `h2-86928-exhaustive-contract.md` from mode 1 to mode 0. The `r2=1` in the normalization stub is dead after setup; it does not change the stored mode.

2. **The `r2!=0`, `P+8==0`, `P+0x2E==0`, normalized selector 11/19 route has a missing global-state gate.** At `0x00286BF8..0x00286C14`, after confirming selector 11 or 19, code checks the default pointer kept in `r0`: if non-null it reads byte `[r0+8]`; a nonzero byte branches to the ordinary `r0=0` exit at `0x00286BE4`. Only when the default pointer is null or that byte is zero does execution call `0x0028DF54`, `0x0028DF3C(0xFFFFFFFF)`, and `0x0028DF0C(0)`, then return 1. The exhaustive branch map currently says this triple-call/return-1 route is unconditional for selectors 11/19. Add the guard and the no-call return-0 alternative. This gate is observable state and required for implementation.

3. **A null selected pointer faults in the common prewrite, before the described `+0x2E` path.** The unconditional `strb r2,[r5,#0x2D]` at `0x0028699C` occurs before the incoming-`r2` branch and before any check of `r5`; `r2` was zeroed at entry. Thus, for an invalid/null selected `P`, execution faults at this common write (assuming address zero is unmapped), not later by dereferencing `P+0x2E` after the `r5` check. Update the incoming-`r2!=0` paragraph and fault-domain text so they do not imply the common prewrites succeeded for null `P`.

## Other reviewed details

- The selector normalization for 11, 12, 13, 14, and 19 matches the ARM; raw 15 is the sole mode-table error I found. The selector-6 literal choice and default pointer selection also match.
- Incoming `r2` is copied to `ip` and used as a zero/nonzero predicate. The contract correctly distinguishes the `r2==0` and `r2!=0` route families and preserves the state-4/5, query, state-0, and update-loop ordering, subject to correction 2.
- The 13-register integer push, `vpush {d8}`, 12-byte local allocation, stack args at current `sp+0x48/+0x4c`, raw-word transfer through `s16`, 8-byte call alignment from an aligned entry SP, common epilogue, and preservation of `r4-r11`/`d8` match the disassembly. No float semantic type is established for arg6.
- Direct helper order and the path-local writes in the report match the decoded body. The nested callees remain original dependencies; their behavior is not inferred to be pure.
- All 22 table entries verified as direct ARM `BL`s to the target. The direct-site scan is not a runtime reachability result or an exhaustive indirect/Thumb dispatch audit.
- The exhaustive contract accurately bounds run-002: callback return `r0=0` implies helper return `r0=0` because the wrapper's final call is the helper and its epilogue preserves `r0`, but run-002 did not capture helper entry args, internal PC, or branch cause. Keep this as a raw return observation.
- `h2-nested-callback-final-helper-review.md` overstates this point when it calls the helper “fully characterized” dynamically and assigns high-level “successful termination” meaning to return zero. Those claims should be removed or qualified to match the exhaustive contract and dynamic audit. The run does not identify the internal branch or the semantic meaning of zero.
- The separate earlier static review describes 205 instructions over 820 bytes; the pinned span contains 202 ARM instructions in the 808-byte code prefix plus a 12-byte literal pool. Keep code and literal-pool accounting distinct if that count is repeated.

## Scope and next action

Read-only static review only: no candidate implementation, build, differential runner, emulator, debugger, or board edit. Fix the three branch/selector/fault details in the exhaustive contract and qualify the older runtime interpretation. Then the contract is suitable to guide implementation with unresolved callees retained at original addresses. Its stated limitation remains: complete candidate size/relocations/interworking and semantic support still need separate validation; the 22-site scan does not establish caller behavior at all sites.

## Run-002 follow-up: corrections and claim narrowing verified

The new run-002 packet pins all 13 inputs; every recorded SHA-256 matches the current file. I re-read the corrected exhaustive contract against the previously decoded pinned ARM:

- The selector table now correctly says raw `r3=15` normalizes to `S=11` while storing mode 0 at `P+0x5E` and leaving the `+0x5F` flag clear. This matches the branch at `0x00286A38` (`r6=11`, `r2=1`, `r1=0`) and the later stores/tests of `r1`.
- The `I2!=0`, `P+8==0`, `P+0x2E==0`, `S in {11,19}` route now includes the default pointer retained in `r0`: non-null with `[r0+8] != 0` exits with raw 0 before the three callees; null or zero state reaches the `0x0028DF54`, `0x0028DF3C`, `0x0028DF0C` sequence and returns raw 1. This matches `0x00286BF8..0x00286C38`.
- Both incoming-r2 sections now state that null/invalid selected `P` faults at the unconditional `P+0x2D` common store at `0x0028699C`, before the branch and later state reads. That corrects the previous fault-location description.

The revised `h2-nested-callback-final-helper-review.md` now correctly says the raw callback return is preserved from the final helper call, does not assign success/error meaning, and does not claim the helper's internal branch was dynamically characterized. Its explanation of the wrapper's `r0=2` return is consistent with the static conditional at `0x001A0800..0x001A0808` and the run's outer handler return.

One minor wording improvement remains in that older review: its return-zero bullet says “This path is reached following normal completion of `0x0028E974` and the 6-iteration indexing loop.” The shared `0x00286BE4` return-zero epilogue is also reached by early query/state exits and by the alternate `I2!=0`, `P+0x2E!=0` path that skips the loop. Consider changing it to “One ordinary update route reaches this shared return after ...” to avoid implying every zero-return path executes the loop. This does not block implementation; the exhaustive contract's own path map distinguishes those routes.

**Updated recommendation:** the three material contract corrections are present and match the pinned ARM. The exhaustive contract is suitable to guide implementation, with unresolved helpers retained as original dependencies and the already stated size/differential/caller validation gates still outstanding. This is a static contract approval only, not evidence that a candidate exists, fits 820 bytes, or behaves equivalently.

Read-only follow-up: packet-hash verification and inspection of the corrected docs plus pinned branch disassembly; no builds, tests, emulator, code, or board changes.
