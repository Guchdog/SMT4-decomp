# `0x00128610` input-sample normalizer: pinned static contract

## Recommendation and evidence scope

The 148-byte ARM helper has a small selector dispatcher around three original
normalization routines. Its branch and argument-routing behavior is recoverable
from the pinned image. The later readable C++ conversion retains all three
callees and compares their exact argument bundles, output writes, return state,
and fault behavior against the original; the implementation report records
that evidence. This contract itself is a static audit only.

The task packet’s 10 declared input hashes all matched. The pinned `code.bin`
SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
The 148-byte target is `[0x00128610,0x001286A4)`, with ARM instructions only
and no literal tail. At packet capture, the source file contained the exact
original bytes as a naked function and the ledger row was `matching`. The
production source and ledger now reflect the reviewed C++ conversion and
`non_matching` classification.

## Entry ABI, selector and branches

At entry, the helper consumes five integer arguments:

| Location | Meaning | Width/interpretation |
| --- | --- | --- |
| `r0` | calibration-block base | pointer; selector is read at `r0+0x0C` |
| `r1` | output-x halfword pointer | pointer |
| `r2` | output-y halfword pointer | pointer |
| `r3` | sample x | full signed 32-bit value |
| `[entry_sp]` | sample y | full 32-bit value |

The prologue saves `{r4,lr}` and reserves eight bytes. It saves output-x in
`r12`, output-y in `r4`, reads the selector with `LDRB` (unsigned), moves sample
x to `r2`, and loads sample y from `[current_sp+0x10]`, which is the fifth
argument at entry SP. The selector comparisons are exact equality checks for
0, 1 and 2. Selector values 3 through 255 take the no-call path.

Each valid branch reads two **signed** calibration halfwords with `LDRSH`,
places their sign-extended 32-bit values in an eight-byte outgoing stack area,
restores the original output pointers into `r0/r1`, then calls the selected
helper. The call bundles are:

| Selector byte | Signed calibration halfwords | Called original routine | Call arguments |
| --- | --- | --- | --- |
| 0 | `[cal+0]`, `[cal+6]` | `0x0013B9FC` | `r0=out_x`, `r1=out_y`, `r2=sample_x`, `r3=sample_y`, `[sp]=cal[0]`, `[sp+4]=cal[6]` |
| 1 | `[cal+2]`, `[cal+8]` | `0x0013B8F8` | `r0=out_x`, `r1=out_y`, `r2=sample_x`, `r3=sample_y`, `[sp]=cal[2]`, `[sp+4]=cal[8]` |
| 2 | `[cal+4]`, `[cal+0xA]` | `0x0013BAE0` | `r0=out_x`, `r1=out_y`, `r2=sample_x`, `r3=sample_y`, `[sp]=cal[4]`, `[sp+4]=cal[0xA]` |

The dispatcher itself writes only its eight-byte outgoing stack pair; sample
and calibration loads do not write caller memory. Each callee owns any output
stores and further effects. The dispatcher does not normalize a return value:
for selectors 0–2 it returns with `r0` as left by the selected callee; for an
invalid selector it returns the original calibration pointer in `r0`. The
caller discards `r0`. It preserves `r4` and restores SP/LR; it does not change
other callee-saved GPRs. It uses no VFP instructions and has no global access.
The 16-byte total frame preserves eight-byte alignment when entered with an
ABI-aligned stack.

There are no null checks. The calibration base must be readable at the selector
byte and the selected pair offsets; output pointers are passed through to the
chosen callee. Invalid selectors only dereference the selector byte and do not
call a normalizer or write output. Malformed pointers, aliasing, MMIO, and
callee-specific fault behavior remain uncharacterized.

## Real caller at `0x0011C5EC`

The pinned 304-byte wrapper calls this helper once at `0x0011C668`; an aligned
ARM `BL` scan of the pinned image found no other direct ARM callsite to
`0x00128610`. The wrapper's argument setup is:

```text
r0 = context + 0x0C                   // calibration base
r1 = output + 0x0C                     // x halfword output slot
r2 = output + 0x0E                     // y halfword output slot
r3 = sign_extend(s16(output + 0x0C))   // sample x
[sp] = sign_extend(s16(output + 0x0E)) // sample y, fifth argument
```

The sample values are loaded with `LDRSH` from the output slots before the
normalizer call. Thus the actual caller passes sign-extended signed-halfword
values, even though the helper itself accepts full 32-bit sample arguments.
The two output pointers are adjacent halfwords and are distinct in this call.
The calibration pointer is `context+0x0C`; its selector is therefore
`context+0x18`.

This call happens only after the wrapper's input-mode check succeeds, its
calibration clamp routine has run, and its one-record ring read reports a
positive signed count. The ring read writes the output record and a count at
wrapper local SP+8. Before that read, the wrapper initializes timestamp and
index outputs to all-one sentinels. On positive count, it reads output y and x
as signed halfwords, then calls the normalizer as shown above. Relevant
calibration fields may already have been clamped: `context+0x0C` and `+0x0E`
to minimums 40 and 36, and `context+0x12`, `+0x14`, `+0x16` to maximum 145;
`context+0x10` is not clamped by that routine. Consequently selector 0/1/2
must be tested against the post-clamp state as well as raw direct-helper
fixtures.

After the call, the wrapper continues to update its state words at `context+8`
and output offsets 0, 4, and 8; it can also clear output fields under two global
flag checks and call `0x0013BCAC` when the byte at `0x00471AD8` is zero. Those
later effects are outside the normalizer itself but must be included in a
separate complete-wrapper composition. The higher-level static caller census
identifies `0x001078E8` as the direct caller of this wrapper, using a context
pointer loaded from `0x004650A0` and output address `0x004E3C28`; this does not
establish runtime cadence or live input provenance.

## Bounded conversion and differential plan

Keep the three routines `0x0013B9FC`, `0x0013B8F8`, and `0x0013BAE0` original
for the first conversion. A typed C++ dispatcher can express the unsigned
selector and signed halfword pairs directly, but its ABI wrapper must retain the
5th sample argument at entry SP and create the two outgoing stack parameters
for each six-argument callee. Do not silently narrow the sample arguments or
swap output x/y pointers.

For a later focused original-versus-candidate runner:

- Exercise selector bytes `0,1,2,3,127,128,255`, with disjoint aligned valid
  calibration/output regions first.
- For each valid selector, place distinct signed halfwords around
  `-32768,-1,0,1,32767` in each selected pair and check the exact pair/branch.
- Pass sample values at signed 16-bit boundaries through the real caller and
  additionally test full 32-bit signed values in direct calls, since the helper
  ABI itself does not truncate them.
- Record branch target, full `r0-r3` and both stack arguments at the callee
  boundary; compare output halfwords, callee-saved registers, SP, return `r0`,
  fault class, and relevant memory. The invalid-selector path should not reach a
  normalizer and should leave output unchanged.
- Add controls for signed-to-unsigned selector decoding, swapped selector
  pairs/callees, `LDRH` in place of `LDRSH`, reversed output pointers, dropped
  sample-y stack argument, and unconditional callee dispatch.
- Compose the original `0x0011C5EC` wrapper for all three post-clamp selector
  routes and a nonpositive count early return, with the same ring fixtures in
  both images. Keep the separate ring-reader contract and postprocess dependency
  limits explicit.
- Resolve final-VMA ARM `R_ARM_CALL` relocations only to even ARM entries; check
  function-pointer bit 0, branch encodings, body size versus the 148-byte slot,
  and replay a narrowly scoped IPS against the pinned image. If an out-of-slot
  placement is required, validate it as a separate integration decision.

No arithmetic semantics of the three callees, physical controller meaning,
source-ring liveness, concurrent mutation behavior, output/calibration aliasing,
or invalid-pointer faults are claimed by this static audit.

## Provenance

Packet pins all match, including the source/image/ledger hashes. `code.bin`
SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`;
`src/engine/leaf_batch29_a.cpp` is
`eda60a6e0a3830bf187021ec0f3d0cbf69d5b3fb0ea32ed14a1650c68282ad46`,
`src/engine/leaf_batch30_a.cpp` is
`14e36c11b3f45da42ae14f870469d7cee9c665f7c78af24c35309a7686980d59`, and
`config/functions.csv` is
`c69267e99013560a92ab08c33ad4e7f4b9b6e61bbd913fbc28e9e73105f372ae`.
The static Capstone ARM decode covered all 37 words of `0x00128610` and the
full 304-byte `0x0011C5EC` wrapper. The direct call scan found one aligned ARM
`BL` to the helper, at `0x0011C668`.
