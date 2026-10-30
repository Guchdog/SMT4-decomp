# H1 title-message source bridge

## Scope and implementation

Added the source-private `smt4::camp::H1_SetTitleHelpMessage(const char*, u32)`
API in `src/camp/title_message.{h,cpp}`. The implementation accesses the typed
`ButtonHelpManager.work` and `ButtonHelpWork` fields, keeps the established
null/reset writes and return values (`0xFF` for reset, `1` for a valid message),
and uses a private forward byte-copy loop. The helper validates a readable
128-byte input span before changing work state; it accepts at most two lines,
each no longer than 64 bytes. Unsupported text and a null work pointer return
zero without changing work memory. The shared copy routine and its ledger entry
remain untouched.

Only the state-2 and state-5 title-message C++ expressions were changed to call
the new bridge. Static inspection found that these expressions are in the
existing `#if 0` readable draft of `ui_func_001e989c`; the currently compiled
callback remains a naked ARM body. Thus the source call names are migrated, but
this task does not claim the production callback dispatches through the bridge.
The new bridge TU is included by the existing recursive `src/*.cpp` CMake glob.
No full CMake configure/build or final executable/map was run.

## Differential evidence

The exact `src/camp/title_message.cpp` TU was compiled and linked for ARMv6K
hard-float VFPv2 with a private, typed test definition of
`g_ButtonHelpManager`. The original side executes pinned `0x0029F10C` and its
pinned `0x002C5FF4` copy body in offline Unicorn. The candidate side enters the
compiled production TU. Its test manager symbol is isolated at `0x02001000`;
both sides point at a distinct `0x564`-byte help-work block at `0x02002000`.

The fresh `run-04` matrix compares return `r0`, resume PC/SP, callee-saved
`r4-r11`, `d8-d15`, FPSCR, caller-owned stack, the full `0x20000`-byte data
mapping, typed manager bytes, pinned manager cell, mapped asset, and the full
ButtonHelp work block. It passes 10/10 cases: four actual TitleTable rows, null
reset, empty non-null text, a 64-byte single-line boundary, a two-line string
with NUL at scan index 127, high-bit content, and a leading newline. Original
copy-call arguments are captured for valid non-null cases. The frozen asset SHA
is `edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`.

The asset rows verified in this run are:

| Selection | File offset | Length | Text |
| ---: | ---: | ---: | --- |
| 0 | `0x46` | 36 | `Start a new game from the beginning.` |
| 1 | `0x9C` | 39 | `Load a saved game and continue playing.` |
| 2 | `0xF2` | 25 | `Configure audio settings.` |
| 3 | `0x148` | 28 | `Download additional content.` |

Separate candidate-only controls pass for a 65-byte first line, a 65-byte
second line, no NUL in 128 bytes, and a null manager work pointer. Each returns
zero, avoids a fault, and leaves ButtonHelp work unchanged. These are safety
guard observations only; the pinned helper does not define equivalent behavior
for invalid pointers or overlong input.

Integration checks confirm the CMake glob includes the new source, exactly one
API declaration and definition exist, the two H1 draft expressions use the new
name, and neither the new TU's linked symbols nor the ledger-backed helper/copy
source or `config/functions.csv` contain a replacement/label change. Exact
source, object, ELF, input, report, and test hashes are recorded in the handoff.

## Limits

This evidence covers the compiled helper TU, not a canonical production link.
The test manager definition is a minimal stub; object allocation and lifecycle
remain caller preconditions. State-2/state-5 callsite use is static source
evidence only because the readable callback implementation is disabled. No
live callback path, renderer, other locale, invalid pointer, overlong-input
equivalence, full build, emulator, or game runtime was exercised. The helper's
safe non-null domain is bounded to valid readable input and work pointers, at
most two lines of at most 64 bytes, and non-overlapping forward-copy spans.
