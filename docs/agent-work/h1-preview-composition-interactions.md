# H1 preview composition interactions

## Result and scope

The pinned `0x002BF9F0` helper reaches the common tail on every continuing
path. The tail calls scale (`0x002B1FC0`), translation (`0x002B1DFC`), and
selector (`0x002B1C8C`) in that order. Their `+0x87`, `+0x88`, and `+0x89`
enable bytes and their `+0x58`, `+0x64`, and `+0x70` table pointers are
independent, so all three bodies can run during one helper call.

The helper's own interpolation and row-setter paths cannot both run in one
call. The helper compares the unsigned row duration with the signed progress
at the interpolation/endpoint split: duration greater than progress reaches
the divide dependency (`0x002C615C`) and bypasses the endpoint setter. The
other side can reach setter `0x002BDAC0` only when row mode is zero and the
sequence is enabled, non-null, and has an ordinary/restart entry. Before this
split, a null helper table or both signed words at object `+4/+8` negative
returns before dependencies. Thus the two maximal reachable dependency sets
are:

1. divide + scale + translation + selector;
2. setter + scale + translation + selector.

Three fresh synthetic fixtures exercised these sets and distinct track paths:

| Fixture | Helper path | Scale / translation | Selector |
| --- | --- | --- | --- |
| `helper interpolation + scale endpoint + translation endpoint + selector row advance` | two divide calls | both endpoint stores | ordinary row advance |
| `helper setter + scale interpolation + translation interpolation + selector row advance` | setter call | both interpolation paths | ordinary row advance |
| `helper + scale + translation interpolation with selector sequence selection` | two divide calls | both interpolation paths | successful sequence lookup and selected row update |

Each original pinned path and the linked C++ candidate composition agreed on
the full-composition runner's defined projection: return/fault sentinel, `r0`,
`r4-r11`, `SP`, `d8-d15`, `FPSCR`, the mapped data snapshot/digest, caller-owned
stack, and ordered direct-callee names/arguments. The final report contains
three passing cases and no original/candidate mismatch. Its targeted negative
control omits the setter's object `+0x50` animation-index store; the setter
fixture detects the changed word at `0x02000050` (`2` versus `0`).

## Selector fixture correction

While constructing the third interaction fixture, the inherited full-composition
fixture writer was found to place selector sequence words at sequence-base
`+0x14`. Pinned instructions at `0x002B1D34-0x002B1D40` compute
`sequence + 8 + 28 * index` and load the word there. This interaction runner
keeps the shared fixture and runner unchanged, and writes the two test words at
the pinned `+8` and `+0x24` positions. The corrected fixture reaches the
successful lookup; its assertions check object `+4 == 42` and a nonzero selected
table pointer at `+0x70`. This is a test-data correction only; no candidate was
changed.

The common-tail reachability follows directly from the pinned helper: after its
conditional main-row work it reaches the three calls in order, with each callee
checking a separate gate and table pointer. The original-body identity checks
passed for all six pinned spans. Source and image SHA-256 identities are listed
in the final private report.

## Evidence and limits

Final fresh output:
`build/agent-work/H1-semantic/h1-preview-composition-interactions/overnight-20261025-preview-interactions/run-03/report.json`.
The report records candidate compilation and three synthetic ARM/Unicorn
differentials as passing, with the targeted setter mutation detected. The
focused test module passes all four tests. No emulator, Azahar, production
build, or live H1 caller/runtime was run. The fixtures do not establish live
object construction, table binding, lifecycle, rendering, aliasing, invalid
indices/pointers, concurrency, MMIO, or behavior beyond the explicitly encoded
track and helper paths. The divide path uses positive nonzero duration only;
the helper's divide and setter arms are covered separately because they are
mutually exclusive.

The shared full-composition runner's selector fixture layout remains outside
this task's write lease; its sequence cases should be audited or corrected in
a separately assigned shared-runner task before treating those cases as
successful sequence-lookup coverage.
