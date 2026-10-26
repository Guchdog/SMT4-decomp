# Static contract: `0x002BF9F0` preview animation helper

## Scope and provenance

This is a read-only static reconstruction of the full ARM function
`0x002BF9F0..0x002BFC87` (664 bytes). The pinned image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
helper-body SHA-256 is
`9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e`. Capstone
decoded 166 contiguous ARM instructions (664/4), with no undecoded tail.
The code is represented in `src/engine/leaf_batch32_c.cpp` as the matching
`ui_func_002bf9f0` instruction sequence.

The H1 gate at `0x0025A2BC` calls it at `0x0025A2F8` with
`r0 = *(u8**)0x0043E278 + 0xD74`. The gate passes no other formal argument and
uses the helper result only as `r0 == 0` versus nonzero. The H1 state-5 callback
calls that no-argument gate at `0x001E9D1C`, after its script-ready check, then
branches to `0x001EA62C` if the gate returns zero.

## ABI and return contract

The usable helper ABI is `s32 UiAnimSpriteStep(void* object)` / ARM AAPCS32:
one pointer argument in `r0`, no stack arguments, return in `r0`, and
callee-saved `r4-r8` restored. The function prologue at `0x002BF9F0` saves
`r4-r8,lr`; `movs r4,r0` makes the input pointer the working object. The source
currently has conflicting `void` aliases (`UiAnimSprite_UpdateCalc` in
`src/ui/status.cpp`, `UiAnimSprite_StepAnimation` in `src/ui/status_down.cpp`
and `include/ui/status_down.h`). The binary proves a non-void integer return:
its normal tail loads a signed byte into `r0` at `0x002BFC7C`. Do not use the
different `UiAnimSprite_UpdateCalc` at `0x002B9220` (declared `bool` with two
arguments) as the prototype for this address.

The return paths are:

- At `0x002BF9F8`, null `r0` branches to `0x002BFA10`, returns constant 1 at
  `0x002BFA10..0x002BFA14`, and does not execute the common tail.
- For non-null `r0`, the word at `object+4` is compared as signed. Only if it is
  negative is the word at `object+8` loaded and compared as signed. If both are
  negative, execution falls through to the same constant-1 return at
  `0x002BFA10`; otherwise `BGE` at `0x002BFA0C` continues at `0x002BFA18`.
- Every continuing path converges at `0x002BFC2C`. After three direct update
  calls, the helper sets byte `+0x8A` to 1 only when bytes `+0x86`, `+0x87`,
  `+0x88`, and `+0x89` are all nonzero; otherwise it sets `+0x8A` to 0. It
  sign-extends that byte into `r0` at `0x002BFC7C`, writes byte 1 to `+0x85`
  at `0x002BFC80`, and returns at `0x002BFC84`.

So the observed return values are exactly 1 on the early path and 0 or 1 on
the common path. The H1 gate reduces these to zero/nonzero. The animation
helper itself has substantial side effects; it is not a pure readiness query.

## Control-flow map

The 22 conditional/unconditional non-call branch instructions below are all in the
decoded 664-byte function. Direct calls are listed separately in the next
section. In the map, `common` is `0x002BFC2C`, and `return-1` is the constant-1
return at `0x002BFA10`.

| PC | Instruction / target | Behavior |
|---|---|---|
| `0x002BF9F8` | `beq 0x002BFA10` | Null object returns 1. |
| `0x002BFA0C` | `bge 0x002BFA18` | Continue unless both signed words `+4` and `+8` are negative. |
| `0x002BFA28` | `bne 0x002BFC2C` | Existing byte `+0x86` skips animation selection/update. |
| `0x002BFA34` | `beq 0x002BFC2C` | Null table pointer at `+0x4C` skips table processing. |
| `0x002BFA50` | `bgt 0x002BFB88` | Signed comparison of unsigned row duration `row+8` against signed progress `+0x52`; greater takes interpolation path. |
| `0x002BFA60` | `beq 0x002BFAA8` | Row byte `+0x0A` selects one of two coordinate-selection blocks. |
| `0x002BFA68` | `beq 0x002BFA88` | Direction byte `object+0x54` selects row coordinates `+0/+2` versus `+4/+6`. |
| `0x002BFA84` | `b 0x002BFAA0` | Join endpoint path and reset progress. |
| `0x002BFAA4` | `b 0x002BFC2C` | Endpoint path joins common update tail. |
| `0x002BFAAC` | `beq 0x002BFACC` | Direction selects opposite endpoint ordering. |
| `0x002BFAC8` | `b 0x002BFAE4` | Join before frame-sequence lookup. |
| `0x002BFAF4` | `beq 0x002BFB58` | Disabled/null sequence path sets `+0x86=1`. |
| `0x002BFB08` | `beq 0x002BFB58` | Current sequence word `-1` sets `+0x86=1`. |
| `0x002BFB30` | `beq 0x002BFB58` | Next word `-1` or `-3` sets `+0x86=1`. |
| `0x002BFB38` | `beq 0x002BFB60` | Next word `-2` resets sequence index and changes animation. |
| `0x002BFB54` | `b 0x002BFC2C` | Animation-change path joins common tail. |
| `0x002BFB5C` | `b 0x002BFC2C` | Sequence-complete path joins common tail. |
| `0x002BFB84` | `b 0x002BFC2C` | Reset/change-animation path joins common tail. |
| `0x002BFB90` | `beq 0x002BFBDC` | Direction selects sign/order for x/y interpolation. |
| `0x002BFBD8` | `b 0x002BFC20` | Join after interpolation. |
| `0x002BFC5C` | `beq 0x002BFC78` | If either `+0x86` or `+0x87` is zero, clear `+0x8A`. |
| `0x002BFC74` | `bne 0x002BFC7C` | If `+0x88` and `+0x89` are both nonzero, keep/set `+0x8A=1`; otherwise clear it. |

There is no `BLX`, indirect `BX`, `LDR pc`, or other indirect callback dispatch
inside this 664-byte function. The only PC-writing instruction is the final
`pop {...,pc}` return. The direct callees below can themselves have callbacks;
those transitive effects are not bounded by this function decode.

## Object reads, writes, and callees

`r4` remains the object pointer throughout the function. Direct object fields
accessed by this body are:

| Offset | Width / access | Use |
|---|---|---|
| `+0x04`, `+0x08` | signed word reads | Early validity/status test; `+0x08` is read only when `+0x04 < 0`. |
| `+0x0C`, `+0x10` | word reads/writes | Fixed-point x/y values; interpolation adds results here, or endpoint values are stored directly. |
| `+0x4C` | word pointer read | Base of 12-byte animation rows; null skips row update. |
| `+0x50`, `+0x52` | signed halfword reads | Row index and animation progress. `+0x52` is reset or incremented as a halfword. |
| `+0x54` | byte read | Direction/endpoint selection. |
| `+0x78` | word pointer read | Optional animation-entry array, read only when `+0x84 != 0`. |
| `+0x7C` | signed halfword read/write | Animation-entry index; incremented with `SXTH` or reset to zero. |
| `+0x84`, `+0x86` | byte reads | Feature/sequence and already-complete guards. `+0x86` is set to 1 on terminal/error cases. |
| `+0x85` | byte write | Set to 1 on every common-tail path; not written by the constant-1 early return. |
| `+0x87..+0x89` | byte reads | Completion conjunction. |
| `+0x8A` | byte write, then signed byte read | Set to 0/1, then sign-extended into the function result. |

When `+0x4C` is non-null and `+0x86` is zero, the helper computes
`row = *(void**)(object+0x4C) + 12 * (s16)(object+0x50)`. It reads row
halfwords at `+0,+2,+4,+6,+8`, byte `+0x0A`; there is no row-index bounds
check. Row values at `+0,+2,+4,+6` are treated as signed coordinates and
shifted by 12 for endpoint stores/interpolation. Row `+8` is read as an
unsigned duration/progress threshold.

If `+0x84` is nonzero and `+0x78` non-null, the helper computes
`entry = pointer + 0x1C * (s16)(object+0x7C)` and tests the first word against
`-1`, `-3`, and `-2`. It increments the signed halfword index before examining
the next 0x1C-byte entry. For non-sentinel entries it also reads a signed byte
at entry `+4`. The indexed sequence and row pointers are dereferenced without
a length check; storage, valid index domains, and sentinel-table lifecycle are
not recoverable from this function alone.

| Call PC | Target | Arguments and result use |
|---|---|---|
| `0x002BFB48`, `0x002BFB78` | `0x002BDAC0` (`camp_func_002bdac0`, also declared `UiAnimSprite_SetAnim`) | `r0=object`, `r1=s16 animation word`, `r2=s8 entry byte`; return ignored. |
| `0x002BFBA4`, `0x002BFBC8`, `0x002BFBEC`, `0x002BFC10` | `0x002C615C` (`ui_func_002c615c`) | `r0=(s16 coordinate difference)<<12`, `r1=row+8 duration`; returned `r0` is added to object `+0x0C` or `+0x10`. |
| `0x002BFC30` | `0x002B1FC0` (`ui_func_002b1fc0`) | `r0=object`; result ignored. |
| `0x002BFC3C` | `0x002B1DFC` (`ui_func_002b1dfc`) | `r0=object`; result ignored. |
| `0x002BFC48` | `0x002B1C8C` (`ui_func_002b1c8c`) | `r0=object`; result ignored. |

The external callees can add memory effects and runtime dependencies. For
example, row/sequence animation changes invoke `0x002BDAC0`; the four
interpolation calls invoke `0x002C615C`; then the normal tail always invokes
the three `0x002B1xxx` helpers. This note does not claim their internal effects.

## Other direct callers and what they establish

A linear ARM decode over the function extents in `config/functions.csv` found
58 caller functions containing 216 apparent direct `BL 0x002BF9F0` sites.
Grouped by source directory, that sweep found engine 41 functions/106 sites,
camp 5/36, script 2/17, UI 8/52, and battle 2/5. It is an address/caller
inventory, not a proof that all sites are dynamically reachable; literal/data
words in function extents can be mistaken for instructions by a linear sweep.
The examples below were individually checked in their instruction windows:

- H1 gate: `0x0025A2F8` passes `g_FrameTex + 0xC00 + 0x174`, i.e.
  `scene+0xD74`; it compares result to zero at `0x0025A2FC` and returns 0 on
  zero.
- `GuestWin_Calc` (`0x0011B128`): sites `0x0011B174` and `0x0011B198` pass
  `r4+0x30`; both compare the helper result with zero, then conditionally store
  window state at `r4+8`.
- `StatusDown_CalcTaskCallback` (`0x001CA648`): site `0x001CA80C` passes
  `r4+0x28`; at `0x001CA818` it separately reads `s8` at object `+0x8A` and
  tests it. The task source models its known panel entries as raw `0x8C`-byte
  `UiAnimSprite` blocks. This supports the helper's animation-node use
  elsewhere, but does not identify the H1 scene's `+0xD74` field by itself.
- `Status_CalcTaskCallback` (`0x0018F560`) has sites `0x0018F584`, `0x0018F58C`,
  `0x0018F5A4`, `0x0018F5AC`, `0x0018F65C`, and `0x0018F688`; the available C++
  draft advances status sprites and reads `+0x8A` after selected updates.
- `FlowScript_EventVmExecute` (`0x001955BC`) has 13 sites, starting
  `0x001955E4/0x001955EC`, with event-work-derived pointers. In the checked
  pair the next call overwrites `r0`; it is not an H1 scene pointer.
- `FlowScript_EvalStateControl` (`0x001C3ED4`) calls at
  `0x001C3F10/0x001C3F18/0x001C3F20/0x001C3F30` on offsets from its event work.
  These pointers and event lifecycle are distinct from H1's singleton-derived
  pointer; this caller is not a source for naming the H1 nested field.
- Other decoded caller families include `Result_Calc` (`0x0018BFEC`),
  `Camp_MainProc` (`0x0017FE9C`), `InfoWin_DrawUp` (`0x0011AE10`),
  `InfoWin_Calc` (`0x0011B1BC`), `StatusDown_CalcTaskCallback`, save/load,
  status-skills, camp, battle, shop, and additional script-VM functions. They
  pass pointers to distinct interior offsets or computed entries; the common
  helper body alone does not make those owner structures interchangeable.

The same callee is named `UiAnimSprite_UpdateCalc` (void) in
`src/ui/status.cpp`, `UiAnimSprite_StepAnimation` (void) in
`src/ui/status_down.cpp` / `include/ui/status_down.h`, and is distinct from
the two-argument boolean `UiAnimSprite_UpdateCalc` at `0x002B9220`. The pinned
ARM proves the single-pointer ABI and a returned value regardless of those
source aliases. The caller-usable conservative signature is therefore
`s32 (*)(void*)`.

## H1 `scene+0xD74` lifecycle and bounded preconditions

`g_FrameTex` is initialized to null in `src/engine/asd_frame.cpp`; the
`FrameTex_func_00104378` path allocates `0xFEC` bytes, stores the pointer in
the global slot, zeroes all `0xFEC` bytes, and explicitly writes zero to scene
bytes `+0x1C` and `+0xF2B`. Those writes explain the H1 gate's short-circuit
success before later setup. The existing `FrameTexScene` model leaves
`+0x54..+0xE8B` as padding; `scene+0xD74` is inside that padding and is not a
named field in the model. The gate's arithmetic proves only that it passes
this interior address. The helper accesses it through at least byte `+0x8A`,
so the directly addressed extent must reach `scene+0xDFF`, within the enclosing
`0xFEC` allocation.

The helper's minimum path-dependent memory requirements are:

- A non-null base that is readable through object `+0x86` and, on a main
  return, writable through `+0x8A` and `+0x85` (minimum contiguous extent
  `0x8B` bytes). The H1 call site has no guard for null `g_FrameTex`.
- If signed `+0x04 < 0`, readable signed word `+0x08`.
- If `+0x86==0` and `+0x4C!=0`, a valid 12-byte row at the unchecked signed
  halfword index `+0x50`; fields `+0x52`, `+0x54`, `+0x0C`, and `+0x10` must
  be readable/writable as the selected path requires.
- If `+0x84!=0` and `+0x78!=0`, a valid sequence at unchecked signed index
  `+0x7C`, plus a readable entry byte at `entry+4` on non-sentinel paths.
- Callees at `0x002BDAC0`, `0x002C615C`, `0x002B1FC0`, `0x002B1DFC`, and
  `0x002B1C8C` must accept the supplied pointers/values and their own indirect
  structures/callbacks must be valid.

What remains unknown: which FrameTex setup/subwidget operation initializes the
`+0xD74` object, whether its nested row/sequence pointers are populated before
the H1 gate can reach this helper, the valid signed index ranges and sentinel
tables, actual callback targets/timing, and runtime behavior. The helper
contract is thus a single-pointer mutating animation step with branch-produced
0/1 result, not a standalone pure readiness predicate. This static note does
not validate its runtime side effects or promote the H1 gate candidate.

## Source identities

| Input | SHA-256 |
|---|---|
| `build/azahar-validation/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| `src/engine/leaf_batch32_c.cpp` | `fb918815656c0980b6ff8176074301aee2960b96eb3c0d9278d3f89a5489a175` |
| `src/ui/status.cpp` | `af7bfd529cfdc6064d57bab0179be61dbc976527c4bdb11d379f669be13678ca` |
| `src/ui/status_down.cpp` | `4a34235f4e2eca511e8156420359dfd52ad739cdb5915e3e45f4c6bb2bc8c183` |
| `include/ui/status_down.h` | `3d39e468d2867579a691ab40f3f7e5b057d909b1c73c7f9e74444b5fd3601c03` |
| `src/ui/window.cpp` | `693ca4bcca19b47c4dbc521a63c4e9852bcdc33332f8d2b839c317930602f647` |
| `src/script/script_exec.cpp` | `4d493188cf93cc98712fc43e66b1149b689bf377e616fb6648b3956a6e3df584` |
| `src/engine/asd_frame.cpp` | `2eb47952a660bde3fb2203d506243610eafd23f6e217a58d522c63d4c22973a8` |
| `include/engine/asd_frame.h` | `062ebe523688acf615f72979a4edb455b7b14c9df56e8f2788a9119003b3efd3` |
| `config/functions.csv` | `b27580ea4af85889e1167e7af5f898f66e82517c0293fcc3a586fea504a94be8` |
