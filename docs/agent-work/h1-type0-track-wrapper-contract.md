# Static contract: wrapper `0x00155540` versus callback `0x0015555C`

## Scope and provenance

This is a static contract note for the pinned US `code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
The declared source cross-checks are `src/engine/leaf_batch29_a.cpp`
(`06be0823b62c7e3a589964b665dda95ed599ce00336c7a63f113aaf63e126a8d`),
`leaf_batch39_c.cpp`
(`e02cc5f49f278ce54a5820127b19bfe1a09b8431ad3d8402691b0c637160ab24`),
`leaf_batch36_a.cpp`
(`d58631151f305aaa5b10f9b3fb21532215730c3f67330fb72225b1e97a8b16d3`),
`leaf_batch10_c.cpp`
(`8c042d859ea2412f06f31ed21b13576c699a3d8ead744a790f5da09f4898afc9`),
and `leaf_batch27_c.cpp`
(`2dc24e3169bc553b6d7a5f9cdd23ed6c7ecc13735dcf5d867a3300b6852e4ae`).
`config/functions.csv` labels `0x00155540` as a 68-byte `matching` function
with `unknown` semantics. Those ledger labels are bookkeeping, not recovered
behavior.

## Entry and return boundaries

Pinned ARM at `0x00155540` begins with `push {r4,lr}`. Its wrapper body is seven
instructions and returns at `0x00155558` with `pop {r4,pc}`:

| Address | Instruction | Contract effect |
| --- | --- | --- |
| `0x00155540` | `push {r4,lr}` | Saves one callee-saved GP register and caller return address (8 bytes). |
| `0x00155544` | `mov r4,r0` | Retains the sole incoming argument, a context/base pointer. |
| `0x00155548` | `bl 0x002A2414` | Calls the first helper with incoming context in `r0`. |
| `0x0015554C` | `add r1,r4,#0x80` | Sets helper-2 input `r1=context+0x80`; leaves helper-1 return in `r0`. |
| `0x00155550` | `bl 0x002A23FC` | Calls the second helper with that `r0` and computed `r1`. |
| `0x00155554` | `mov r0,r4` | Discards helper-2's `r0` return and restores original context as wrapper result. |
| `0x00155558` | `pop {r4,pc}` | Restores saved `r4`/LR and returns with the incoming `sp`. |

The next instruction at `0x0015555C` is a distinct callable VFP callback entry,
not wrapper fallthrough: it begins `vmov.f32 s3,s0`, operates on hard-float
arguments, and returns at `0x00155580` with `bx lr`. The next independent
prologue begins at `0x00155584`. Although the naked source symbol and ledger
span encode all 68 bytes from `0x00155540` through `0x00155583`, control flow
returns before the callback bytes. Separately, callback setup stores literal
`0x0015555C`, not `0x00155540`, in the callback slot. The wrapper's source
partition must not merge these two entry contracts semantically.

The wrapper's supported signature is one pointer-like GP input in `r0`, with
that same pointer returned in `r0`. No other incoming argument is consumed;
the wrapper contains no VFP operations. It saves `r4`/LR for 8 bytes, calls a
callee that also saves/restores `r4`, tail-calls the second helper chain without
an additional stack frame, then restores `sp`, `r4`, and PC. Its own direct
memory effects are limited to the stack save/restore; the helpers have the
effects below.

## Exact helper argument/result flow

### First call: `0x002A2414`

The wrapper enters this helper with `r0=context`. The helper immediately
replaces `r0` with literal address `0x00473530`, dereferences that global word,
and tests bit zero. Thus it does not use the wrapper's context argument.
Depending on the bit, it either skips initialization or calls unresolved
`0x002C00D4` with `r0=0x00473530`; a zero helper result also skips the
initialization path. When the latter helper returns nonzero, the pinned body
initializes words at static address `0x004EAD74`: offset `+0` becomes zero,
`+4` becomes `0x004EAD78`, and `+8` becomes `0x004EAD78`.

All observed branches converge on `0x002A2464`, which loads literal
`0x004EAD74` into `r0`, then pops `{r4,pc}` at `0x002A2468`. Hence the supported
return contract is `r0=0x004EAD74` on the paths encoded here, with conditional
global reads, an unresolved `0x002C00D4` call, and the listed static writes.
This is an instruction-derived contract, not a semantic name for the object.
The helper saves/restores `r4` and LR in an 8-byte frame.

### Second call: `0x002A23FC` tail adapter to `0x002B777C`

Immediately after the first helper returns, the wrapper's `add r1,r4,#0x80`
does not alter `r0`. Therefore the first helper's `0x004EAD74` result flows
unchanged into the second helper's `r0`; this is proved by the adjacent
instructions, not inferred from a C++ prototype. At `0x002A23FC`, the helper
executes `add r1,r1,#4`, then an unconditional branch to `0x002B777C` (not a
link). The target therefore enters with `r0=0x004EAD74` and
`r1=context+0x84`.

Pinned target instructions at `0x002B777C` then:

1. Save `r0` in `r2`.
2. Load two words from `[r1]` and `[r1+4]` into `r0` and `r3` (the wrapper
   context slots `+0x84` and `+0x88`). Call these loaded values `A` and `B`.
3. Store `B` at `[A+4]` and `A` at `[B]`.
4. Decrement the word at `[r2]`, i.e. `[0x004EAD74]`, and store it back.
5. Clear the two wrapper-context slots at `+0x84` and `+0x88`.
6. Return through the LR established by the wrapper's `BL 0x002A23FC`.

No null checks are present in this target; valid pointers/layout are an
unverified precondition. The target leaves the loaded `A` in `r0` when it
returns, but the wrapper immediately overwrites it with `r4=context` at
`0x00155554`. The second helper/target uses no stack frame and does not alter
callee-saved registers in the inspected body. Its contract includes the exact
pointer writes above, but no stronger data-structure name is established.

As a cross-check of this helper pair, the pinned/source body around
`0x0037FBB8` also calls `0x002A2414`, computes `r1=r5+0x44`, then calls
`0x002A23FC`; the tail target consequently uses `r5+0x48` there. This is a
separate caller pattern, not evidence that `0x0037FBB8` calls
`0x00155540`.

## Callback registration and H1 relationship

The track setup body at `0x002A5CEC..0x002A5D08` reads a byte from the resolved
source at `+0x10` and writes a callback pointer at the destination `+0x4C`:
type 0/default is `0x0015555C`; type 1 is `0x00151404`. The constructor at
`0x002A6194` also initializes the callback slot to `0x0015555C`. In the H1
transition path, callback-bearing objects are called indirectly (including
`BLX` at `0x002872E4` and `0x00210010`) from their `+0x4C` slots.

These references concern the interior callback entry `0x0015555C`, not the
wrapper entry `0x00155540`. No live source `+0x10` byte, actual H1 slot value,
or runtime callback selection was observed here. The serialized CANM member
type must not be substituted for the separate runtime source byte. The
assigned source set also establishes no specific direct caller of the wrapper;
its own helper flow is recovered from its body, while its external caller and
purpose remain open.

## Evidence limits and next step

Evidence is static pinned-image disassembly plus source/listing cross-check.
No compilation, candidate, emulator, or runtime test was performed. The helper
`0x002C00D4` behavior is unresolved; whether the static memory is a pool,
counter, or another structure is not named; input pointer validity is assumed
by the code; and wrapper caller/ownership are not established. The next useful
step is a separate caller/object-layout trace for `0x00155540` and the
`0x004EAD74` object, keeping the registered callback at `0x0015555C` distinct.
