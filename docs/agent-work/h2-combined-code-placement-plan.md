# H2 combined code placement and split-helper plan

## Decision

There is **no production-ready combined placement proven yet**: no production
Draw/initializer split object or multi-symbol patch builder exists. The byte
budgets do show two conditional layouts worth testing. The least disruptive
near-term layout keeps the already-tested Calc body in the cave and outlines
Draw's repeated renderer-cache code into the remaining 428 bytes. A broader
layout can put Calc, Draw, and optionally Secondary main symbols in their
original spans and use the whole 2,524-byte cave for their split helpers plus
the initializer body. Both require fresh production compilation to prove the
actual outlined symbol sizes and relocations.

Do not treat either layout below as already feasible in machine code, and do
not claim that raw padding outside `.text` is executable. The current Calc-only
patch remains the only production-source final-address image.

## Exact original ranges and measured bodies

All original ranges are half-open intervals from the ledger and pinned image.
The candidate sizes are from the accepted experimental ARM objects, except
Calc, which is the production-TU extracted symbol.

| Function | Original VMA span / bytes | Candidate bytes | Candidate over original | Current evidence |
|---|---|---:|---:|---|
| `TitleConfig_Calc` | `[0x001EA928,0x001EB02C)` / 1,796 | 2,096 | 300 | Production TU, four local `R_ARM_ABS32` table references; final-address callback and persistent sequence evidence. |
| `TitleConfig_Draw` | `[0x002CAFD0,0x002CB75C)` / 1,932 | 2,252 | 320 | Experimental candidate only, no relocations in its extracted symbol; 46 isolated cases at synthetic VMA. |
| `TitleConfig_Secondary` | `[0x002CAEF0,0x002CAFD0)` / 224 | 284 | 60 | Experimental candidate object, no relocations; callback lifecycle remains unresolved. |
| `titleConfig_func_002f4ca0` initializer | `[0x002F4CA0,0x002F4EDC)` / 572 | 552 | fits by 20 bytes arithmetically | Experimental candidate only, no relocations; its body overlaps original inline strings if copied in place. |

The measured callback-body total is 5,184 bytes. The four original spans total
4,524 bytes, for 660 bytes of net overage before helper-call instructions,
literal data, or alignment. These totals do not imply that an arbitrary suffix
can be moved: C++ control flow, stack/VFP live values, local tables, and
relocations must be handled explicitly.

The pinned `.text` starts at VMA `0x00100000`, has size `0x002FE624`, and ends
at `0x003FE624`. Its aligned size is `0x002FF000`, so its page tail ends at
`0x003FF000`. The one audited executable cave is therefore
`[0x003FE624,0x003FF000)`, 2,524 bytes (`0x9DC`). The current production Calc
blob is 2,096 bytes (`0x830`), occupying
`[0x003FE624,0x003FEE54)`. The exact remaining interval is
`[0x003FEE54,0x003FF000)`, 428 bytes (`0x1AC`). The approved Calc image hash is
`c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`; its
production object is
`94197ad141393099a25e679b73457f127c54c7155fa4d8c2ff25270f8ca620fd`.

The previous Draw placement note says the cave ends at `0x00400000`; the
segment metadata and patch manifest instead end it at `0x003FF000`. The prior
initializer note places the Calc end at `0x003FEE64`; adding the manifest's
2,096 bytes to `0x003FE624` gives `0x003FEE54`. Use the manifest/segment
arithmetic above for any subsequent patch map.

No all-zero run of 64 bytes or more occurs inside the actual `.text` bytes
outside the page-tail cave. `.rodata` ends at `0x0042AB78` before its aligned
end `0x0042B000`; `.data` ends at `0x00476644` before aligned end `0x00477000`.
Those page tails are not verified executable code space. In particular, the
nominal 2,492-byte `.data` tail cannot be called a cave without a permission,
ownership, and loader audit.

## Split-helper layout hypotheses

### A. Keep the production Calc cave body and test one Draw helper in 428 bytes

This is the smallest next placement experiment:

| Piece | Proposed VMA | Hard byte limit |
|---|---|---:|
| Existing production Calc | `0x003FE624` | 2,096, fixed by reviewed object |
| Draw main symbol | `0x002CAFD0` | 1,932, the original Draw span |
| Outlined Draw helper and relocated `%s` data | start at `0x003FEE54` | at most 428 combined, including alignment |
| Original initializer and Secondary | original bodies | unchanged |

The Draw candidate has one obvious source-level factoring opportunity:
`cached_render_update` is currently `always_inline` and appears at six call
sites. Outlining this renderer/cache helper may remove repeated code from the
2,252-byte Draw body and put a single helper in the tail cave. To fit, the
production Draw main must compile to at most 1,932 bytes, and the helper,
literal data, veneers, and alignment together must fit in 428 bytes. The
current object does not measure those split sizes, so this is plausible but
unproven. Do not assume a source `noinline` annotation guarantees either
bound; compile and inspect the production symbol/helper symbols in a fresh
later task.

The Draw body reads the original `%s\0` at `0x002CB410`, offset `0x440` within
its original span. Replacing all 1,932 bytes in place would overwrite that
literal. Either preserve it as a deliberate non-code island with verified
control flow around it, or move/copy the three bytes to a reserved cave-data
slot and retarget the format pointer through a supported relocation. Count
that data and any pointer relocation against the same 428-byte limit. The
original initializer and its strings stay untouched in this layout.

The helper-call branch from Draw to the cave is well within ARM `BL` range,
but the production object may emit `R_ARM_CALL` or another relocation that the
Calc-only patcher does not accept. The branch encoding, addend semantics, ARM
state, and target range still need checks. The Draw helper uses integer
arguments; any other split that passes VFP coordinates must preserve the
hard-float AAPCS contract.

### B. Put Calc/Draw main symbols in their original spans and use the full cave

If the goal is specifically to keep both main symbols inside their original
spans, move the Calc main out of its current cave placement too. The cave then
starts fully free at `0x003FE624`, rather than having only the current 428-byte
tail. A capacity-feasible target map is:

| Piece | Proposed location | Necessary bound / treatment |
|---|---|---|
| Calc main | `0x001EA928` | At most 1,796 bytes. Outlined helper portion must cover the 300-byte measured excess plus call/ABI overhead. Keep its local jump tables within the main or explicitly relocate them. |
| Draw main | `0x002CAFD0` | At most 1,932 bytes. Outline repeated cache work; preserve or retarget `%s` at `0x002CB410`. |
| Secondary main (optional) | `0x002CAEF0` | At most 224 bytes. Its measured candidate is 60 bytes over; keep original Secondary until its lifecycle contract is ready if not promoting it. |
| Initializer body (optional) | `0x003FE624` | 552 bytes, reached by a branch at `0x002F4CA0`; leave the original string pool intact. |
| Calc/Draw/Secondary outlined helpers and data | after the initializer, or before it with explicit symbol map | Lower-bound candidate-derived budget: `300+320+60+552+3 = 1,235` bytes when including all four candidates and a copied Draw format literal. Reserve up to the 2,524-byte cave, then fail if measured helpers/calls/alignment exceed it. |

This uses no unverified memory, and the lower-bound arithmetic leaves 1,289
bytes for call/prologue overhead, alignment, and additional outlined code.
However, 300/320/60 are only candidate body-size differences, not measured
helper symbol sizes. The initializer's 552-byte candidate must be placed wholly
in the cave (or have a separately proven code/data island layout); branching
from its original entry to the cave leaves its absolute string references
valid. This is a feasible **budget target**, not a proven executable layout.

For Calc-in-place, the four production local absolute references must be
resolved to the new main VMA/table offsets, not rebased blindly to the old
cave. The helper split must keep any live work/config values explicit across
the call and preserve AAPCS callee-saved state. The caller-visible Calc entry
remains `0x001EA928`. The existing static audit found no outside B/BL/BLX or
aligned absolute code pointer into Calc's old body interior; Draw, Secondary,
and initializer need their own interior-entry/literal audits before any
in-place overwrite.

### C. Put full callbacks in the one cave

This is infeasible with measured bodies. Calc plus Draw alone require 4,348
bytes, 1,824 above the cave. Including the 552-byte initializer and 284-byte
Secondary raises this to 5,184 bytes, 2,660 above the cave. The current 428-byte
tail cannot hold a complete Draw or initializer body. Do not append a second
patch to the Calc cave: the current builder is pinned to the original image,
one entry, and one zero-filled cave; it would overlap the Calc blob or reject
already-written bytes.

## Initializer literal pool

The initializer's original function bytes contain these absolute strings:

| Address | Function-relative offset | Bytes including NUL |
|---|---:|---|
| `0x002F4E84` | `0x1E4` | `TITLE_CONFIG_MAIN\0` (18) |
| `0x002F4E9C` | `0x1FC` | `TITLE_CONFIG D\0` (15) |
| `0x002F4EB4` | `0x214` | `camp/config.bf\0` (15) |
| `0x002F4EC4` | `0x224` | `camp/config.mbm\0` (16) |

All four start within the 572-byte original initializer span. The 552-byte
candidate extends through relative offset `0x228`; if copied byte-for-byte at
the original entry it overwrites the first three strings and the first four
bytes of the last one. The candidate itself embeds those four original
addresses. The safe initial approach is to put the complete 552-byte candidate
in a validated executable cave, patch only the original entry branch, and
leave every other original byte—including the strings—untouched. If an
in-place initializer main is later required, either keep a verified literal
island at those addresses and branch around it, or relocate all strings to a
known readable area and retarget every use; record exact bytes and references
and test the initializer's task/resource-name arguments. Do not rely on the
candidate's current hard-coded pointers after overwriting their targets.

## Patch-builder and verification requirements

The next builder needs an explicit multi-symbol placement manifest, not a
second invocation of `h2_calc_code_patch.py`. It must:

1. Extract exact production symbols and helper symbols from their real TUs and
   retain source/object/reference hashes. The isolated candidate sizes are
   inputs for budgeting only.
2. Support a mixed placement map: in-place main body within its exact original
   span, separate cave helper/body/data blobs, and optional entry branches for
   functions wholly moved to cave. Check every VMA/file interval, alignment,
   overlap, code/data boundary, original cave byte, and ARM branch/BL reach.
3. Resolve only explicitly supported relocations, including the four Calc
   local `R_ARM_ABS32` table references, production cross-symbol helper calls,
   literal/data references, and each addend relative to the correct function
   or section. Reject undefined/external symbols, unsupported relocation
   types, out-of-placement targets, unexpected ARM/Thumb-state changes, and
   capacity overflow.
4. Keep callback entry ABIs and helper calling conventions exact: ignored
   incoming context values, observed return registers, callee-saved
   `r4-r11`/SP/`d8-d15`, stack-passed arguments, VFP hard-float arguments, and
   helper live-value preservation. Do not split mid-block or truncate at the
   old function length.
5. Verify no caller or jump table enters an overwritten body interior; preserve
   Draw/initializer literal pools or retarget and verify all references. Apply
   one serialized IPS independently to the pinned original; compare that image
   byte-for-byte with the exact image used by final-address differential runs,
   and prove bytes outside authorized records remain unchanged.
6. Emit separate per-symbol source/object/body hashes and one combined IPS and
   image hash. Keep ledger statuses truthful (`non_matching` for promoted
   differing bytes), preserve original address/span metadata, and keep semantic
   records separate from exact-byte claims.

## Next bounded experiment and limits

For the cheapest placement probe, keep the current production Calc patch fixed,
outline only Draw's repeated `cached_render_update`, move/retarget `%s`, and
measure a production `leaf_batch43_a.cpp` object. Accept that layout only if
the extracted Draw main is at most 1,932 bytes and helper+string+alignment
fits the exact tail `[0x003FEE54,0x003FF000)`. This experiment requires an
assigned source/patch-builder owner and invalidates no existing Calc evidence
unless shared code or the Calc image changes.

If that bounded probe misses the 428-byte tail, test the larger map: move Calc
main into its original 1,796-byte span with measured helper calls, free the
whole cave, then place the initializer body and all outlined helpers within
2,524 bytes. Keep Secondary original in that batch unless its lifecycle
evidence is explicitly promoted. In both experiments run production-symbol
final-address Draw cases and the Calc persistent sequence against the *same*
merged image; add initialized caller/task composition before promotion.

Current semantic evidence remains under mocked/HLE helper boundaries. There is
no combined image, source-level split build, Draw production-TU extraction,
initializer final-cave patch, Secondary production replacement, real scheduler
execution, visible UI, persistence, or Azahar runtime evidence in this plan.
No compiler, source/ledger edit, emulator, RSP, or host input was used here.
