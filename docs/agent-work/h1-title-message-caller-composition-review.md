# Independent review: H1 state-5 title-message caller composition

## Verdict

The evidence supports the bounded state-5 caller-to-message-helper comparison
for the four rows in the frozen `TitleTable.tbb`: 4/4 paired runs satisfy the
reported functional projection, and the wrong-row mutation is detected. This
is partial offline ARM differential evidence for the window
`0x001EA12C..0x001EA160`, not full callback, lifecycle, or runtime equivalence.
I independently checked the frozen input hashes, pinned caller instructions,
asset layout, source/harness assertions, report, build command record, and
producer handoff. I did not compile, rerun tests, or use an emulator.

## Pinned routing and row selection

`config/game_info.json` places the text image at virtual address `0x00100000`.
Independent ARM disassembly of the frozen `code.bin` at the claimed window
confirms:

| Address | Pinned instruction / effect |
| --- | --- |
| `0x001EA12C` | `ldr r4, [r5, #8]` selects the index |
| `0x001EA130`–`0x001EA138` | `r1=0`; `r0=0x3A`; call pinned `0x002C0EC4` |
| `0x001EA144` | call pinned `0x002C0E9C` to obtain payload |
| `0x001EA148`–`0x001EA158` | multiply index by `0x2B`, double it, add to payload, load color literal, add `0x16` |
| `0x001EA15C` | pinned `BL 0x0029F10C`, word `ead302eb` |
| `0x001EA160` | next instruction, `ldrb r0, [r5, #0x63]` |

The candidate-side image changes only that 4-byte call word to `b35738eb`,
which branches from `0x001EA15C` to linked candidate message entry
`0x01000030`. The original image still routes to pinned `0x0029F10C`. The
candidate is linked as a 288-byte text blob at `0x01000000`: its copy dependency
is at `0x01000000`, and the entry is at `0x01000030`. The recorded compile and
link commands both exited 0, with `--no-undefined`; object and ELF hashes in
the report match the files on disk. The candidate's internal copy call thus
targets linked candidate code, while the original helper executes its pinned
copy routine. The TBB getters and caller arithmetic remain pinned in both
images.

The frozen asset is 880 bytes with SHA-256
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`. Its
TBCR header has size `0x20`; table 0's TBL1 header starts at file `0x20`, and
its payload starts at `0x30` with size `0x158`. The caller's field formula is
`payload + selection*0x56 + 0x16`. With the harness mapping the container at
`DATA+0x100` (`DATA=0x02000000`), the row pointers/text are:

| Selection | Caller pointer | Text | Byte length |
| ---: | ---: | --- | ---: |
| 0 | `0x02000146` | `Start a new game from the beginning.` | 36 |
| 1 | `0x0200019C` | `Load a saved game and continue playing.` | 39 |
| 2 | `0x020001F2` | `Configure audio settings.` | 25 |
| 3 | `0x02000248` | `Download additional content.` | 28 |

Every message has an in-row NUL and is one line within the candidate's 64-byte
line domain. The report checks the expected pointer at the caller and helper
entry, color `0x323232FF`, selection index and title work pointer for both
sides. It records the helper return status as `r0=1` and stop PC `0x001EA160`.

The title-main block is at `DATA+0x800`; the separate `0x564`-byte ButtonHelp
work block is at `DATA+0x900`, selected through the initialized manager global
at `0x0043DA2C`. The TBB slot pointer is installed at `0x00493BD0`. These
fixtures are disjoint. Reported copy calls have identical normalized `(r0,r1,r2)`
arguments/order on both sides for all rows, with destination `0x02000DD0`,
source equal to the selected row pointer, and exact non-NUL lengths above.

## Projection, setup, and sensitivity control

The report and code compare all 0x1000 bytes of the mapped data region, the
separate title block and ButtonHelp work block, the caller-owned stack
projection, `r4-r11`, `d8-d15`, FPSCR, and the helper's defined return status.
They verify the final SP is the seeded `0x08001000`; entry LR is checked as the
resume address. The help-work bytes are also checked against expected color,
status, cleared fields, copied text, and terminator effects. The original and
candidate preserve the asset bytes. Access footprints are captured but not
required to match, which is appropriate because the pinned copy routine has
alignment-dependent word paths and the candidate uses a forward byte copy.

The report captures pre-call SP/LR and helper-entry SP, but the comparator does
not assert their expected values or equality. Its pre-call checks cover pointer,
color, index, title pointer, and seeded `r8`; helper entry checks pointer and LR.
The balanced final SP is asserted. The coordinator has now corrected the plan
language: it explicitly identifies pre-call/helper-entry SP and LR as captured
diagnostics unless asserted, requires balanced final SP, and treats post-call
LR as caller-saved diagnostic state. That wording matches the actual harness.
Post-call LR does differ (`original=0x0029F1F8`, `candidate=0x010000E8`), while
both helper-entry LR values are `0x001EA160`; the difference remains correctly
outside the defined projection.

Pre-call and return `r0-r3`, `r12`, and NZCV are emitted as diagnostics rather
than required equal, except `r0=1` is explicitly required as the helper's
defined status. At `0x001EA160`, `LDRB` and then `CMP` overwrite condition flags
before the conditional branch, so flags at the stop are not a defined caller
result for this boundary. A minor projection wording issue remains: the report
lists “pre-call ... SP/LR” and the plan implies checks more strongly than the
comparator implements; those fields are captured but not asserted.

The negative control applies only to the selection-1 candidate run. The hook
first records the real caller's pre-call pointer (`0x0200019C`), then changes
candidate incoming `r0` to row 0 (`0x02000146`). The helper entry records the
wrong pointer; the text changes from `Load...` to `Start...`; the first full-data
mismatch is at `0x02000DD0` (`0x4C` vs `0x53`). The control is detected through
both the expected-entry-pointer rejection and changed final help output. It
does not mutate the original or production image.

Report SHA-256:
`9d1985154dad78679dc20b74fb716cc26531f6a7ea9608665d75643ff8197188`.
Candidate source SHA-256:
`68c91fe472a631d9435daa0596161ddcbea70dba011abcecfe1be8df6422305e`.
Candidate object SHA-256:
`4fbcc5b3d18d6762fb2eea0ffcddcd1f42c6922ba0fab72b5f8639e0aefb4852`.
Candidate ELF SHA-256:
`05059c43b7a1a55312c3c44556bf8386588005cc34e4e79f0f09b5769b6e041f`.
All declared packet input hashes match the current files.

## Evidence boundary and recommendation

This composition starts at `0x001EA12C` with a synthetic active-state frame,
valid preselected index, preinitialized globals/work blocks, seeded callee-saved
registers and VFP state, and stops at the helper return. It does not establish
that live H1 reaches this frame, manager initialization/binding order, full
callback behavior, later state-5 branches, other locale assets or malformed
strings, production placement, rendering, or Azahar/game runtime behavior. It
also does not compare post-call global slot/manager storage outside the mapped
DATA projection, though these globals are setup inputs and no such writes are
claimed. Keep the result labeled partial real-asset caller-window differential;
it is useful evidence for this four-row seam, not a runtime or whole-callback
claim.

## Plan correction re-review (v2)

The fresh v2 packet freezes the corrected plan at SHA-256
`3f8dcfd4eb03082d190dbd8690772c78f05f6c23bedbbf4144816fd56c7ec55b`. Its new
wording matches the actual capture/assertion split: entry snapshots are
diagnostic unless explicitly asserted; final SP balance is asserted; and
post-call LR is diagnostic. I independently reconfirmed the unchanged candidate
source (`68c91fe...6422305e`), runner (`208a3dc4...c36c38f1`), and run-05 report
(`9d198515...8197188`) hashes. The report still has 4/4 passing cases, equal
final SP `0x08001000`, equal entry LR `0x001EA160`, and the expected differing
post-call LR values listed above. The plan edit changes no executable input or
assertion and does not invalidate the existing run-05 report under this task's
bounded acceptance. No rerun or code change is indicated.

Recommendation: accept the bounded composition comparison as partial
real-asset caller-window evidence. It does not imply stricter entry-frame
assertions, a full callback/lifecycle result, production integration, or
runtime equivalence. If entry SP/LR equality is required by a future contract,
add and validate those assertions in a separately assigned task.
