# Current static contract for H2 final helper `0x00286928`

## Scope and provenance

This is a bounded static audit of selector 6 in the current C++ candidate and
the pinned ARM image. It does not validate a conversion or establish full H2
equivalence. The run002 packet pins match: `src/engine/leaf_batch45_a.cpp`
SHA-256 is `c9e989ae493ffd64ea873cf7bd070524121efc9c3c8e7d54787164890015586d`;
`extracted/exefs/code.bin` is 3,633,152 bytes with SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The
820-byte ARM body at VMA `[0x00286928,0x00286C5C)` has SHA-256
`13599a73fefa7f8ed72d8251e769b2302486c973169be524785830699b7f7c6c`.
Because this image's text starts at file offset `VMA - 0x00100000`, the body
was decoded from file offset `0x00186928`, not the VMA as a file offset. ARM
Capstone decodes 205 instructions in the span; the three final words are a
literal pool, not additional control flow.

The packet's `task.blocker` says the source snapshot is stale. That statement
does not match its pins: all eight declared `input_sha256` values, including
the current source, were recomputed and matched. This report treats that blocker
text as stale; it does not change the packet or any shared task state.

## ABI and selector-6 entry

The original uses AAPCS ARM entry with six words: `r0`–`r3`, then arg5 at
`[sp]` and arg6 at `[sp+4]`. The callback `0x00221168` supplies
`r0=result(0x0028686C)`, `r1=result(0x00296F60)`,
`r2=result(second 0x00289640)`, `r3=6`, stack words `1,0`. The first three
values are raw helper results; this audit does not assign them application
types. The original saves/restores `r4`–`r11` and VFP `d8`, restores SP, and
returns an integer word in raw `r0`. It temporarily loads stack arg6 through
`s16` and passes its bits onward; no float meaning is established. The current
C++ candidate has the corresponding six `uint32_t` parameters and uses the
stack arguments at the same call sites. This is a static ABI comparison, not a
compiled ABI check.

For selector 6 the original selects the default object pointer
`P = *(uint32_t *)(0x0043E188+4)`. Before validating that pointer it writes
byte zero to `P+0x2D` and `P+0x5E`. A null/invalid `P` therefore faults; it is
not a benign null case. The selector-6 path does not use the special objects
or selector flags for 11–15/19. It also skips the selector-19-only
`0x002B8584` call and the selector-11/19 `0x002B787C` call.

## Selector-6 paths and effects

Here `state` means byte `P+8`, `row` means byte `P+9`, and `q` means incoming
`r2`. These are structural labels, not recovered field types.

### `q != 0`

After the two common byte stores:

| `state` | Original behavior for selector 6 | Raw return |
|---|---|---:|
| 4 | Return immediately through `0x00286C38`. | 1 |
| 5 | Load word `P+0x18`, call `0x0028DF54(word)`, return through `0x00286C40`. | 1 |
| 0 | If `P+0x2E==0`, return 1. Otherwise clear `P+0x2E`, call `0x0028E974(P,r0,r1,6; stack 0x1A,1,0)`, conditionally call `0x0028DF98(P,row)` when byte `P+0x35` is zero, then return 0. | 0 or 1 |
| other | Call `0x002C1F28`; zero returns 0. Otherwise call `0x002B89A0`; zero returns 0. If the current state is neither 3 nor 0, call `0x002B8D24(P,row)`, write byte 3 to `P+8` and zero to `P+0x35`; return 0. | 0 |

For the `state==0` special case, selector 6 matches neither selector 11 nor
19, so the `P+0x2E==0` branch returns 1 without those special calls. The
`state==other` route's two gate calls short-circuit in order; the second gate
is not called when `0x002C1F28` returns zero.

### `q == 0`

The helper writes the low byte of arg5 to `P+0x36` and the word
`0x035AB9FF` to `P+0x10`. If `state!=0`, it sets `P+0x2E=1`, calls
`0x002B8D24(P,row)`, writes byte 3 to `P+8` and zero to `P+0x35`, and returns
0.

If `state==0`, it calls `0x002C1F28`. Only a nonzero result permits the next
call, `0x002B89A0`; if that result is also nonzero, the helper returns 1 before
`0x0028E974`. Otherwise it calls
`0x0028E974(P,r0,r1,6; stack 0x1A,1,arg6)`. For selector 6, there is no
selector-11/19 `0x002B787C` call. If `P+0x35==0`, it calls
`0x0028DF98(P,row)`. If arg5 is nonzero, it then calls
`0x002C4BF0(*(P+4),0x20)` followed by `0x002B90F0(*(P+4),0x40)`.

It next clears byte `P+0xA12` and runs six ordered iterations for `i=0..5`:
`0x002F5B2C(i)` supplies a low byte stored at `P+0xA13+i`, then
`0x002D65B4(i)` supplies a low halfword stored at `P+0xA1A+2*i`. If `row` is
7, 8, or 9, it calls `0x0028DF70(0)`; only return value 5 triggers byte
`P+0xA26=1`, `0x002B8CCC()`, a low-byte store of that result to `P+0xA12`,
and `0x002B8B78(0xDC)`. This route returns 0.

All paths that do not explicitly return 1 converge on raw return 0 at
`0x00286BE4`. The epilogue at `0x00286BE8` restores the local stack, `d8`,
the saved stack area, and callee-saved GPRs. The source candidate expresses
these selector-6 branches in readable C++, but its presence is not differential,
compiled-ABI, or runtime evidence.

## Callees and evidence boundary

Selector 6 may reach `0x002C1F28`, `0x002B89A0`, `0x002B8D24`, `0x0028E974`,
`0x0028DF98`, `0x002C4BF0`, `0x002B90F0`, `0x002F5B2C`, `0x002D65B4`,
`0x0028DF70`, `0x002B8CCC`, and `0x002B8B78`. The caller and candidate keep
these calls in the original at their corresponding branches. This audit does
not re-establish each callee's contract. In particular, it cannot infer the
state/value conditions from the callback's observed zero return.

The earlier bounded callback run recorded nested target `0x00221168`, callback
raw return zero, and outer handler return 2. Static caller code makes
`0x00286928` the callback's final call and propagates its raw `r0`, so the
observation implies that this helper returned zero on that observed callback.
That trace did **not** stop at `0x00286928`, capture its six arguments, object
pointer/fields, branch PC, or internal callee trace. It therefore does not say
which selector-6 row above produced zero. No branch is marked dynamically
observed here; the runtime callback binding and physical-input mapping also
remain unproven.

## Recommended next slice

Expand validation of the existing readable `0x00286928` candidate as a
selector-6 slice; do not infer that a static contract alone authorizes replacing
the whole dispatcher. Start with direct ARM-versus-C++ differential fixtures
for both `q` values and each distinct `state` route above, using a valid,
aligned object and explicit mapped globals. Assert the ordered helper trace,
all specified writes, raw return, and preserved callee-saved GPR/VFP state.
Cover both outcomes of each `0x002C1F28`/`0x002B89A0` gate, `P+0x2E` and
`P+0x35` conditions, arg5 zero/nonzero, rows 7/8/9 and a non-trigger row, plus
the 2DF70 return-5/non-5 split. Keep the original callees for unresolved
behavior and state clearly where stubs constrain the domain. A null `P` can
serve as a fault characterization only; do not treat it as a successful
equivalence case.

Then extend the original `0x00221168` composition fixture: record all six
arguments and the object/global state at entry to `0x00286928`, and compare the
callback's raw result and mutations with the original call chain. This is
needed because the prior runtime trace established only that one callback
returned zero, not the conditions that selected its path. Keep emulator/runtime
verification separate until the prescribed controlled H2 scenario and input
mapping are available. The small gate at `0x002C1F28` is itself a possible
focused follow-up if its existing candidate is separately differentially
validated, but validating it alone will not cover the branches or ordered
side-effects in the 820-byte dispatcher.

## Limits

- Static image/source audit only. No compilation, direct differential,
  caller-composition rerun, emulator, debugger, or game runtime was used for
  this task.
- The observed callback zero has no captured helper arguments or internal
  branch attribution.
- Valid pointer/object layout, helper effects outside the described calls,
  runtime callback binding, physical-input mapping, and complete H2 lifecycle
  remain unresolved.
- This is not a claim of whole-function semantic equivalence or authorization
  to patch the complete dispatcher.
