# Independent review — `0x002BF9F0` preview animation helper

Task: `h1-preview-helper-contract-review`; owner: `h1_title_init`.

## Verdict

**Partial, with the core contract supported.** I independently decoded the
pinned 664-byte function and checked its exits, direct branches, direct calls,
object accesses, ABI behavior, the H1 gate argument, and three non-H1 caller
examples against their pinned ARM windows and assigned source. The behavioral
description is substantially correct. One static-count typo remains in the
contract note: it says there are 23 conditional/unconditional branch
instructions, but the complete pinned decode contains 22. All 22 direct branch
targets are inside the function and match the listed target map; this is a
documentation correction, not a discovered control-flow counterexample.

No candidate was compiled or tested, no emulator/runtime was used, and this
review does not establish dynamic reachability of the 58-function/216-site
caller inventory.

## Function decode, control flow, and ABI

The pinned `extracted/exefs/code.bin` hash is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The body
at `0x002BF9F0`, size 664 bytes, hashes to
`9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e`. Capstone
decoded 166 contiguous four-byte ARM instructions, covering the whole extent.
The source's `ui_func_002bf9f0` mnemonic listing is in
`src/engine/leaf_batch32_c.cpp` and matches the same decoded instruction flow.

The prologue is `push {r4-r8,lr}`; `movs r4,r0` makes the sole object argument
the working pointer. The common epilogue restores `r4-r8` and returns through
saved `lr`; the early epilogue does the same. `r4-r7` are used as object, row
pointer, and constants. `r8` is saved/restored but not otherwise used in the
decoded body. `r0-r3` are scratch/argument/result registers. The function
allocates no local stack frame. Its usable ABI is one object pointer in `r0`, no
stack arguments, and an integer result in `r0`; source declarations of `void`
do not describe the machine result.

There are two return sites:

- Null `r0` branches at `0x002BF9F8` to `0x002BFA10`, sets `r0=1`, and returns.
- For non-null input, it reads signed word `+4`; it reads signed word `+8` only
  if `+4` is negative. If both are negative it falls through to the same
  constant-one return. Otherwise it continues to the common tail.
- Every common-tail path reaches `0x002BFC2C`, passes the object to
  `0x002B1FC0`, `0x002B1DFC`, and `0x002B1C8C` in order, then computes
  `+0x8A = 1` iff bytes `+0x86..+0x89` are all nonzero; otherwise it writes
  zero. It sign-extends `+0x8A` into `r0`, writes byte 1 at `+0x85`, and returns.
  Since this tail itself has just written `+0x8A`, its produced return is 0 or
  1. The early return is 1. The H1 gate uses only the zero/nonzero distinction.

The complete direct branch set (PC → target) is:

| Branch PCs and targets |
| --- |
| `0x2BF9F8→0x2BFA10`, `0x2BFA0C→0x2BFA18`, `0x2BFA28→0x2BFC2C`, `0x2BFA34→0x2BFC2C` |
| `0x2BFA50→0x2BFB88`, `0x2BFA60→0x2BFAA8`, `0x2BFA68→0x2BFA88`, `0x2BFA84→0x2BFAA0` |
| `0x2BFAA4→0x2BFC2C`, `0x2BFAAC→0x2BFACC`, `0x2BFAC8→0x2BFAE4`, `0x2BFAF4→0x2BFB58` |
| `0x2BFB08→0x2BFB58`, `0x2BFB30→0x2BFB58`, `0x2BFB38→0x2BFB60`, `0x2BFB54→0x2BFC2C` |
| `0x2BFB5C→0x2BFC2C`, `0x2BFB84→0x2BFC2C`, `0x2BFB90→0x2BFBDC`, `0x2BFBD8→0x2BFC20` |
| `0x2BFC5C→0x2BFC78`, `0x2BFC74→0x2BFC7C` |

All targets lie within `[0x002BF9F0, 0x002BFC88)`. Thus the contract note's
branch table is complete and its target descriptions are supported, but its
prose count should read 22. The function has nine direct `BL` sites: two calls
to `0x002BDAC0`, four to `0x002C615C`, and one each to `0x002B1FC0`,
`0x002B1DFC`, and `0x002B1C8C`. No `BLX`, `BX`, `LDR pc`, or other indirect
transfer occurs in this body. The `0x002BDAC0` return is ignored; each
`0x002C615C` return is accumulated into an object coordinate; common-tail
returns are ignored.

## Pointer and field effects

`r4` is the object base. The direct accesses I independently verified are:

- `+0x04` signed word; conditionally `+0x08` signed word for the early gate.
- `+0x0C` and `+0x10` word coordinates, read and written by endpoint or
  interpolation paths.
- `+0x4C` word pointer to 12-byte animation rows. The signed halfword at
  `+0x50` selects a row with address calculation `base + 12*index`; there is
  no row-count or signed-index bounds check. The row supplies halfwords at
  `+0,+2,+4,+6,+8` and byte `+0x0A`; duration `+8` is zero-extended while
  progress `object+0x52` is sign-extended before the signed `BGT` comparison.
- `+0x52` is read and reset/incremented as a halfword; `+0x54` is the direction
  byte selecting endpoint/interpolation order.
- `+0x84` gates the optional sequence path; `+0x78` is its word pointer and
  `+0x7C` its signed halfword index. The code computes entries with stride
  `0x1C`, tests first words against `-1`, `-3`, and `-2`, increments or resets
  the index, and reads signed byte `entry+4` on the animation-update path.
  The sequence index and storage bounds are not checked.
- `+0x86` is an existing-completion byte and is set to 1 on terminal/disabled
  sequence cases. `+0x87..+0x89` participate in the common-tail completion
  conjunction. `+0x8A` is assigned 0/1 and signed-byte-loaded as the result.
  `+0x85` is written to 1 on common-tail paths only; the early constant-one
  return does not write it.

The direct callees can add further memory effects and runtime dependencies.
The function body proves neither their internals nor the lifetime, lengths, or
valid index ranges of the row/sequence data and downstream objects.

## H1 and non-H1 callsite checks

At the pinned `0x0025A2BC` H1 gate, the global literal at `0x0025A314` is
`0x0043E278`; the gate loads the `FrameTexScene*` from that slot. After its
three short-circuit fields, the call argument is formed exactly as
`scene + 0xC00 + 0x174 = scene + 0xD74` at `0x0025A2F0..0x0025A2F4`, then
`BL 0x002BF9F0` at `0x0025A2F8`. At `0x0025A2FC`, zero branches to the gate's
zero return; nonzero continues to its one return. This independently verifies
the helper argument and zero/nonzero use.

Two representative non-H1 source/ARM pairs agree:

- `GuestWin_Calc` at `0x0011B128` forms `r0=r4+0x30` and calls the helper at
  `0x0011B174` and `0x0011B198`. The first result is compared with zero and
  used to choose a window-state update; the second is compared and gates a
  store. `src/ui/window.cpp` contains those exact inline ARM instructions.
- `StatusDown_CalcTaskCallback` at `0x001CA648` calls at `0x001CA80C` with
  `r0=r4+0x28`. The next instruction reconstructs that same object pointer and
  reads signed byte `+0x8A` at `0x001CA818`; source `src/ui/status_down.cpp`
  uses `UiAnimSprite_StepAnimation(&work->panel_sprites[0])`, then reads
  `raw+0x8A`. This is consistent with the helper's mutating result field.

The script state-control caller at `0x001C3ED4` loads event work through its
global slot, then calls at `0x001C3F10`, `0x001C3F18`, `0x001C3F20`, and
`0x001C3F30` with event-work offsets `+0x68`, `+0xF4`, `+0x20C`, and `+0x4C8`.
These are distinct owner pointers; the source comment in
`src/script/script_exec.cpp` accurately describes them as event-work-derived.
They do not establish the identity or initialization of H1 `scene+0xD74`.

The contract note's 58-caller/216-site sweep is correctly labeled an apparent
static inventory from linear ARM decoding, with possible instruction/data
false positives. It is not dynamic call reachability evidence and should stay
described that way.

## Lifecycle and remaining limits

The H1 gate performs no null check on the loaded scene before its field reads.
Its helper argument is an interior pointer into the currently padding-typed
`FrameTexScene` model, not a source-level named animation member. If the
enclosing `0xFEC` scene allocation is live, the helper's direct accesses through
object `+0x8A` reach at most `scene+0xDFF` (exclusive), within that allocation.
That extent calculation does not establish that the nested object is
constructed or that its optional row/sequence pointers are valid.

The preceding static contract note cites scene allocation/zero-initialization
and initial gate-field stores, while correctly leaving the `+0xD74` nested
object's construction/population and dynamic call timing unresolved. This
review's assigned inputs did not include the constructor source, so I did not
independently re-prove that allocator path. The helper body contains no
allocation or nested-pointer validation. It may call `0x002BDAC0`,
`0x002C615C`, and three `0x002B1xxx` helpers; their callbacks and side effects
remain unknown here. No runtime object graph, physical H1 call, or Azahar
behavior is established.

## Frozen inputs and review method

All 14 packet-declared input hashes matched. The pinned image and helper-body
hashes are listed above. Relevant source hashes from the packet are
`src/engine/leaf_batch32_c.cpp`:
`fb918815656c0980b6ff8176074301aee2960b96eb3c0d9278d3f89a5489a175`,
`src/ui/window.cpp`:
`693ca4bcca19b47c4dbc521a63c4e9852bcdc33332f8d2b839c317930602f647`,
`src/ui/status_down.cpp`:
`4a34235f4e2eca511e8156420359dfd52ad739cdb5915e3e45f4c6bb2bc8c183`, and
`src/script/script_exec.cpp`:
`4d493188cf93cc98712fc43e66b1149b689bf377e616fb6648b3956a6e3df584`.
The review used static Capstone decoding of the pinned bytes, direct source
inspection of assigned caller files, and packet hash verification only. No
compile, differential, emulator, candidate edit, or runtime test was performed.

- Compiled: `not_run`.
- ARM differential: `not_run`.
- Caller: `partial` (static named callsite checks only).
- Runtime: `not_run`.

Recommended next action: correct the prose branch count to 22 and retain this
helper as a mutating animation-step dependency with unresolved nested-object
lifecycle. Do not treat the caller census or gate's interior pointer arithmetic
as proof of runtime construction or reachability.
