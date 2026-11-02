# Independent static review: 0x002B8B78

## Recommendation

**Ready for bounded reconstruction planning.** I found no material discrepancy in the pinned ARM contractâ€™s 340-byte body, its direct call order, the two H2 static routes, or the stated runtime limits. Preserve the full 32-bit request and original dependencies until each dependency and manager/profile memory domain is independently supported.

## Packet and target verification

All 15 declared `input_sha256` entries in the review packet matched, including the pinned image (`1f98884fâ€¦cfaa558`), contract, five source TUs, function ledger, and prior `0x00286928` packet files. The ledger identifies `0x002B8B78` as a 340-byte ARM function in `src/engine/leaf_batch32_c.cpp`.

Independent Capstone ARM decoding confirmed the full body from `0x002B8B78` through the epilogue at `0x002B8CC0`, with two trailing literal words. The entry saves `r4-r8`, `sb`/r9, and `lr`, then allocates 12 bytes (40 bytes total). `r0` is preserved as a full-width request in `r5`; incoming `r1-r3` are overwritten before use. No VFP instructions occur in this function itself. The manager literal resolves to `0x0043DA28`; `[manager+4]` supplies object pointer P.

The documented ordered paths match the disassembly:

1. Compare zero-extended byte `P+0x4C9` against the full request. Equality returns that byte. Otherwise, if signed `[manager+0x10]` is negative, scan `P+0x4B8..+0x4BD` in ascending order; first nonzero stores the full request at manager+0x10 and returns its index. If no match (or the initial signed value is nonnegative), store `0xFFFFFFFF` and continue.
2. Call `0x002B85BC(request)`, read the original P byte again, call `0x002AEA28(current)` and then `0x002AEA28(request)`. Both lookups occur; either null result exits after the second lookup, returning its raw r0 while retaining prior effects.
3. Copy the old byte to P+0x4CA and low byte of request to P+0x4C9. Load the two literal words at `0x00402550` onto the local stack. Six loop iterations pass `(i, priority, low_byte_or_0x51, 0)` to `0x002B8794`; any nonzero 16-bit profile field takes the configured priority and its low byte, including values such as `0x0100`.
4. The old/new profile byte+0x0C branches select `0x0013851C(1)`, `0x0013851C(0)`, or `0x002AE874(1)` and write object+0x4C5 as stated. The final serviceâ€™s raw return is preserved. No normalized boolean return is imposed.

The review also confirms there is no null guard before the initial P+0x4C9 read, and the later final object is reloaded from manager+4. Those details support the reportâ€™s pointer/fault and mutation caveats. The callee-saved and stack claims are accurate if callees obey the ABI; the target has no direct VFP state to save.

## Static H2 routes

- At `0x002F4DF0`, the pinned TitleConfig initializer executes `mov r0,#0x99; bl 0x002B8B78`. This is a direct static call with request `0x99`; it does not establish that the initializer ran in an observed session.
- Callback `0x00221168` calls `0x00289640` at `0x002211CC`, moves that result to r2, sets r3=6, and passes r0/r1 from its earlier object lookups plus entry stack words `[sp]=1`, `[sp+4]=0` to `0x00286928` at `0x002211EC`. The callback epilogue leaves r0 unchanged. At the helperâ€™s `0x00286B80` BL, r0 is explicitly set to `0xDC`.
- Within `0x00286928`, for r3=6 the selected object is the manager+4 pointer. If the forwarded r2 is zero, the `r5+8` nonzero bypass is not taken only when that byte is zero. The `0x002C1F28` / conditional `0x002B89A0` guard can still early-exit. Continuing reaches a six-iteration setup loop, then checks object byte+9 for 7, 8, or 9; only those values call `0x0028DF70(0)`, and return value 5 is required to proceed to the `r0=0xDC; BL 0x002B8B78` site. Static branch conditions therefore support the contractâ€™s conditional path. They do not prove this branch or callback is naturally reached at runtime.

An aligned ARM scan found the asserted direct BLs at `0x002F4DF0` and `0x00286B80`, alongside the broader non-H2 caller set in the contract. Such a scan does not exclude Thumb, indirect, or dynamic calls.

## Limits and next step

This is static evidence only. No compiler, candidate execution, differential, caller execution, debugger, or emulator was used. Manager/object/profile validity and aliasing, resource counts and table contents, dependency side effects, concurrent mutation, fault behavior beyond observed instruction order, callback/runtime reachability, actual sound behavior, and persistence remain unproven. A later implementation should first use explicit valid manager/object/profile fixtures and controlled dependency traces, then test both the direct initializer call and the conditional callback composition separately. Do not describe this as runtime sound equivalence.
