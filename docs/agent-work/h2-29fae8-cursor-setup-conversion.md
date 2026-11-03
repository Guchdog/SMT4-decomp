# H2 cursor setup `0x0029FAE8` conversion

The naked ARM mirror in `src/engine/leaf_batch40_a.cpp` is replaced by readable typed C++. Its six arguments are cursor, signed total, visible rows, and columns in `r0-r3`, followed by signed `wrap_row` and `repeat` at entry `[sp]` and `[sp+4]`. The implementation retains the pinned divider and axis/ID helper boundaries. It reproduces signed `total<=0`, the visible clamp, row ceiling from the divider's quotient/remainder return, conditional axis-1 sizing, repeat-controlled ID helpers, header stores, and raw `r0` return values (`1` when disabled, `cursor+0x28` when initialized). The last axis-1 start store from the original interior tail leaf `0x002FC20C` is expressed directly as a volatile word write.

## Offline evidence

Run with a fresh ignored build output:

```powershell
python tools/h2_29fae8_cursor_setup_experiment.py --out build/agent-work/H2-semantic/h2-titleconfig-0029fae8-convert/run001/checks/<run-name> --seed 20261102 --random-cases 48
```

The runner compiles only `leaf_batch40_a.cpp`, resolves each ELF ARM `BL` relocation to the uniquely named ledger target, verifies even word-aligned original ARM entries and branch range, stages a one-slot IPS, checks its roundtrip and unchanged outside bytes, then compares the pinned original and staged candidate in Unicorn. It records full cursor output, ordered writes, exact helper argument traces, raw return, faults, callee-saved registers and SP. Its H2 case checks the exact helper sequence and both final ten-word records. Its negative control retargets the axis ID helper and requires a detected state difference.

Coordinator run `coordinator-run005` passed 60/60 cases (12 fixed, 48 seeded), including both `wrap_row` routes and both `repeat` settings. Report SHA-256: `f22249336cba0ae05f401f5e7e883748c7a74388bcabf355e0ab8e5f4930cd8f`. The compiled 392-byte body SHA-256 is `61f40c89bfc4ba6f6f0e35150c54de65fa5114bc287b097e5869d787a57ae9b0`; object SHA-256 is `b67d10cb10ba11c76e4a9028e5f376a775bb399280e8f0d1858b8ec832e3794e`. The single-slot IPS SHA-256 is `9ebc9c4de860c32f72aee9ef9dc85e7e6c9a15b4990e603fa99d83a414382497`; staged image SHA-256 is `2d0676d5ef27714288507e3ae91e60ccecfca26920c5e3948a4896f2d1b9258f`.

Independent run003 used seed `20261119` and 48 random cases. It also passed 60/60 and detected the wrong-target mutation. Its report SHA-256 is `9afce600666e95de46ba0acd5cf86ccda9235ea1365c5ed19f6929f5d535042f`; see [independent review](h2-29fae8-independent-review.md). That review caught and corrected an earlier runner defect that had discarded `wrap_row`; the reported coordinator and independent runs were both performed after correction.

## Scope

This validates wrapper behavior using the pinned divider, axis initializer, and ID writers. H2 caller inputs are `(cursor=work+0xE8,total=3,visible=3,columns=1,wrap_row=0,repeat=1)`. The asserted final axis starts are both 1; `0x00296F18`'s intermediate start=2 is later overwritten. Full TitleConfig lifecycle, scheduler/input timing, audio behavior, runtime reachability, and other callers remain open. No emulator was launched.
