# Independent review — wrapper `0x00155540` and helpers

## Verdict

**Partial; the central instruction-level contract is supported.** I independently
decoded the wrapper span, first helper, tail adapter, target, type-selection
window, and constructor slot initialization from the pinned image. The wrapper's
return boundary, `r0`/`r1` flow, conditional helper writes, adapter adjustment,
and interior callback pointer are consistent with the contract note.

The result remains static. The assigned sources do not identify a direct caller
of `0x00155540`; the setup code's callback value does not prove that a live H1
object selects or invokes it. The unresolved `0x002C00D4` behavior and input
pointer validity remain material. I found no instruction-level counterexample
to the wrapper/helper effects claimed in the reviewed note.

## Pinned wrapper and callback boundaries

The reviewed image is `extracted/exefs/code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` (3,633,152
bytes). I decoded the file at text VMA `0x00100000` using ARM-mode Capstone.
The 68-byte function-table extent at `0x00155540` decodes as seven wrapper
instructions ending with `pop {r4,pc}` at `0x00155558`, followed immediately by
a separate callback body at `0x0015555C` (`vmov.f32 s3,s0` through `bx lr` at
`0x00155580`). The wrapper cannot fall through into that callback. The source
listing places both byte ranges in one 68-byte naked-symbol span, so semantic
entry points must still be kept distinct.

The wrapper dataflow independently decodes as:

| PC | Instruction | Review result |
|---|---|---|
| `0x00155540` | `push {r4,lr}` | 8-byte save. |
| `0x00155544` | `mov r4,r0` | Retains incoming context. |
| `0x00155548` | `bl 0x002A2414` | First helper receives context in `r0`. |
| `0x0015554C` | `add r1,r4,#0x80` | Sets `r1=context+0x80`; does not change helper result in `r0`. |
| `0x00155550` | `bl 0x002A23FC` | Second helper receives first helper's `r0` and computed `r1`. |
| `0x00155554` | `mov r0,r4` | Discards second helper/target `r0`; returns original context. |
| `0x00155558` | `pop {r4,pc}` | Restores saved `r4` and caller PC/SP. |

The wrapper has no direct object-memory stores. It has one pointer-like GP
argument and returns that pointer in `r0`. Its `r4` save also keeps context
across both calls. The direct wrapper caller and the runtime purpose of this
wrapper are not established by this decode.

## First helper `0x002A2414`

The 104-byte extent at `0x002A2414` has an 8-byte `{r4,lr}` frame and returns
through `pop {r4,pc}` at `0x002A2468`. I independently read the literal words at
`0x002A246C` and `0x002A2470` as `0x00473530` and `0x004EAD74` respectively.
The helper overwrites incoming `r0` with `0x00473530`, dereferences the global
word there, and tests bit zero:

- If bit zero is set, it skips `0x002C00D4` and all initialization stores.
- If bit zero is clear, it calls unresolved `0x002C00D4` at `0x002A242C` with
  `r0=0x00473530`. A zero return skips initialization; a nonzero return enters
  the stores below.
- The conditional initialization sets the word at base `0x004EAD74` to zero
  and stores `0x004EAD78` to base offsets `+4` and `+8`.
- All paths converge on `ldr r0,[pc,#4]` at `0x002A2464`, yielding
  `r0=0x004EAD74`, then return at `0x002A2468`.

Thus the static return pointer is branch-invariant; the global writes are not.
The code does not reveal the object's semantic name, initial runtime global
value, what `0x002C00D4` does, or whether its pointer/return contract is safe for
all callers. The `r4` save is restored; the helper allocates no other frame.

## Adapter `0x002A23FC` and target `0x002B777C`

The 8-byte adapter is exactly `add r1,r1,#4` at `0x002A23FC`, followed by an
unconditional `b 0x002B777C` at `0x002A2400`. It does not link or replace LR.
Combined with the wrapper, the target therefore sees
`r0=0x004EAD74` and `r1=context+0x84`; its `bx lr` returns to the wrapper's
post-call instruction at `0x00155554`.

The target body at `0x002B777C` independently confirms the effects claimed in
the note:

1. `r2=r0` preserves the helper-result/base pointer.
2. `ldm r1,{r0,r3}` loads `A=[context+0x84]` and `B=[context+0x88]`.
3. It writes `B` to `[A+4]`, then `A` to `[B]`.
4. It decrements the word `[0x004EAD74]` modulo 32 bits and stores it back.
5. It zeros the words at context offsets `+0x84` and `+0x88`.
6. `bx lr` returns with `r0=A`; the wrapper then replaces that with context.

There is no target stack frame, null guard, or write to a callee-saved register
in the decoded body. Pointer validity, aliasing safety, and the meaning of the
linked records are not determined here.

## Callback registration and claim limits

The pinned type-dispatch window at `0x002A5CEC` reads a byte from
`[source+0x10]`. Its literal words are `0x0015555C` at `0x002A5FB4` and
`0x00151404` at `0x002A5FB8`. At `0x002A5CF4` type 0 loads the former; at
`0x002A5CFC..0x002A5D00` type 1 loads the latter; `0x002A5D08` stores the
selected value to `[destination+0x4C]`. Other byte values branch past that
store. The constructor body beginning `0x002A6108` loads literal
`0x0015555C` from `0x002A61E4` and stores it at `[object+0x4C]` at
`0x002A6194`. Therefore the type-0 callback and constructor default point to the
interior entry `0x0015555C`, not the preceding wrapper entry `0x00155540`.
“Default” refers to constructor initialization: the setup window itself writes
only on the recognized type-0/type-1 branches and otherwise preserves the
existing slot.

The H1 map's `BLX` sites establish that some callback-bearing objects are called
indirectly, but do not by themselves tie those loaded targets to this setup path
or this exact function pointer. The loader trace and track contract correctly
distinguish serialized CANM type from the runtime `[source+0x10]` byte and state
that no live source byte or callback-slot value was observed. The reviewed
wrapper note likewise limits itself: it does not name a direct wrapper caller,
claim that H1 selects type 0, or claim runtime execution. Preserve those limits.

## Provenance, scope, and next step

All 20 packet-declared input hashes matched. The review covers the pinned image
and these assigned listing/source files: `leaf_batch29_a.cpp` (wrapper),
`leaf_batch39_c.cpp` (first helper), `leaf_batch36_a.cpp` (tail adapter),
`leaf_batch10_c.cpp` (tail target), plus the contract, callback-map, loader
trace, and callback-candidate notes. The pinned image bytes are decisive; the
independent decode also agrees with the available instruction listings.

No compilation, test, emulator, or runtime operation was performed. This review
does not prove external caller reachability, H1 runtime callback choice, source
byte materialization, pointer validity, or the unresolved helper's behavior.
Next: keep the wrapper and callback as separate contracts; if the wrapper's
caller is pursued, identify the live caller/object ownership separately and
retain the runtime-selection observation requirement.
