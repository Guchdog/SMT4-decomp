# H1 state-5 title-message caller composition plan

## Bounded objective

Compare the original state-5 caller window and the reviewed editable message
candidate from the first selected-row load through the helper return. Start at
`0x001EA12C`; stop at `0x001EA160`, immediately after the original or candidate
helper returns. Keep the TBB getters and caller-side address arithmetic as
pinned ARM in both runs. The only substituted behavior is the callee at the
`0x001EA15C` call boundary.

This closes the caller-to-helper seam for four real localized TitleTable rows.
It does not exercise the earlier state-5 readiness/input work, later callback
logic, full title lifecycle, rendering, or a game runtime.

## Pinned caller and real asset

At `0x001EA12C`, the caller loads selected index from `[r5+8]` into `r4`. It
then calls the original TBB getter at `0x002C0EC4` with `(slot=0x3A,
subtable=0)`, gets payload through `0x002C0E9C`, computes `payload + index*0x56
+ 0x16`, loads color `0x323232FF` from literal `0x001E9EC4`, and calls
`0x0029F10C` at `0x001EA15C`. `r5` is the title-main work pointer; the helper's
manager is a different global and must point to a separate ButtonHelp work
object.

The real `TitleTable.tbb` is 880 bytes, SHA-256
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`. Its
container is `TBCR`; subtable 0 is `TBL1` at file offset `0x20`, with payload
at file offset `0x30` and size 344 (`0x158`). The four help strings begin at
payload-relative offsets `0x16`, `0x6C`, `0xC2`, and `0x118`. Their contents
and byte lengths are:

| Selection | Expected pointer when asset is at `DATA+0x100` | Bytes | Title help string |
| ---: | ---: | ---: | --- |
| 0 | `0x02000146` | 36 | `Start a new game from the beginning.` |
| 1 | `0x0200019C` | 39 | `Load a saved game and continue playing.` |
| 2 | `0x020001F2` | 25 | `Configure audio settings.` |
| 3 | `0x02000248` | 28 | `Download additional content.` |

Each string is ASCII, has an in-row NUL, and is a single line shorter than the
candidate's 64-byte copied-line limit. The final row has 64 payload bytes
remaining after its start, but its NUL is at byte 28, so execution stops
reading well before that remaining payload boundary. The actual asset therefore
fits the candidate's line domain without claiming the helper enforces a line
limit.

The existing [presentation-window harness](../../tools/title_help_presentation_experiment.py)
already places this real container at `DATA+0x100`, installs the slot-`0x3A`
pointer at `0x00493BD0`, and verifies all four ARM-selected message pointers,
colors, and asset strings. Its current window stops at `0x001EA15C`, before the
helper call, and it does not initialize the ButtonHelp manager's work pointer
at `0x0043DA2C`. It cannot by itself establish helper workspace behavior.

The current H1 milestone also records 189/189 original-ARM/candidate helper
cases with these real strings. That evidence sends each of the four row
pointers directly to the helper, so it validates helper behavior for the asset
but does not execute the state-5 TBB lookup and caller arithmetic in that
helper differential. The composition proposed here covers that remaining
caller-to-helper seam.

## Private harness composition

Use a new private harness, reusing the existing asset parser, case construction,
TBB slot setup, and original `Runner` memory layout. Keep its current test and
report semantics unchanged. The original run uses the unmodified pinned image;
the candidate run changes a private image copy at the call instruction only.

The reviewed candidate's prior run-02 report (SHA-256
`90bcc2f28a02858abbd12c93f3b6167ccadf0dec7a0565f511605a07310d4d35`) and
linked ELF (SHA-256
`05059c43b7a1a55312c3c44556bf8386588005cc34e4e79f0f09b5769b6e041f`) record a
fully linked `.text` (SHA-256
`c86e422bad733eeae8dd4e962d237b47c412ef1794fb3be3b732a55bbcafe0bb`) at
`0x01000000`, size 288 bytes, with the forward-copy helper at
`0x01000000` and `h1_title_message_candidate` at `0x01000030`; it reports no
undefined symbols. Preserve the entire linked `.text` blob so the candidate's
internal call to the forward-copy function remains valid. Do not inject the
whole ELF file or let the existing `Runner(replacement=...)` entry trampoline
target `0x01000000`, which is the copy helper, not the message entry.

Instead, put those 288 linked text bytes at the existing private injection
base, and replace only the `BL` at `0x001EA15C` in the candidate-side image with
an ARM `BL` to `0x01000030`. For this pinned address pair the branch word is
`0xEB3857B3` (little-endian bytes `B3 57 38 EB`), within ARM BL range. This
preserves call semantics: the call sets `lr=0x001EA160`, and the candidate's
normal AAPCS return resumes the original caller there. The original-side call
continues to execute the pinned helper. Keep the original TBB getters and all
other caller instructions intact in both runs.

Initialize the same deterministic data, register, and stack fixtures in both
runs:

- Copy the unmodified 880-byte TitleTable asset to `DATA+0x100`; set the
  slot-`0x3A` global pointer at `0x00493BD0` to that container.
- Put a synthetic title-main work block at `DATA+0x800`, set `[work+8]` to each
  selection `0..3`, and set caller `r5` to that title work block. Keep a
  deterministic non-selection pattern in the rest of the block.
- Put a separate `0x564`-byte ButtonHelp work block at `DATA+0x900`; set the
  manager's `+4` pointer at `0x0043DA2C` to that block. This is the pointer the
  pinned helper reads and the candidate resolves. The blocks and TBB container
  are disjoint and fit inside the existing `DATA_SIZE=0x1000` mapping.
- Use an active-state frame precondition: script and preview readiness have
  already succeeded, execution is at the post-reducer state-5 segment, and
  `[r5+8]` is a valid menu index `0..3`. Seed `r8=0x0044E300`, stable
  callee-saved sentinels, an 8-byte-aligned SP, deterministic LR/NZCV, and
  explicit `d8-d15` values with `s17=1.0f` to represent the earlier successful
  state-5 setup. The window overwrites `r4` with the selected index before the
  message call.
- Protect the mapped image pages for the two synthetic global writes (the TBB
  slot and `0x0043DA2C`) before writing them, matching the existing harness's
  TBB-slot setup. Do not modify the source asset or shared memory map.

At the call site, capture `r0`, `r1`, `r4`, `r5`, `r8`, SP, and LR. Assert that
`r0` is the row pointer in the table above, `r1=0x323232FF`, `r4` is the same
selection, and `r5` is the title work pointer. Stop both executions before the
instruction at `0x001EA160`; require the expected return PC, `r0=1`, and
balanced/equal SP. Capture pre-call/helper-entry SP and LR for diagnosis, but
do not claim they are asserted unless the harness explicitly checks them. After
the call, LR is caller-saved and may differ, so report it diagnostically rather
than require equality. Compare `r4-r11`, `d8-d15`, FPSCR, and the complete
caller-owned stack projection. Record `r0-r3`, `r12`, and condition flags as
diagnostic volatile state; do not require equality for caller-saved values
other than the helper's defined `r0` status. The next original instruction is
`LDRB r0,[r5,#0x63]`, followed by `CMP`, so caller flags are reset before its
conditional branch.

Compare the full 0x1000-byte data mapping and the complete ButtonHelp work
block. Also report the title block, unchanged TBB asset bytes, and changed work
offsets separately. Do not require identical read footprints: the pinned copy
helper uses alignment-dependent word paths, while the candidate copy is a
forward byte loop. The public result is the memory and defined register
projection, not identical internal access widths.

## Cases and negative control

Run exactly four paired cases, one per actual selection, with the fixed asset
and deterministic sentinel work bytes. For each case, require the caller's
pre-call pointer/color assertions, the text bytes at the selected TBB address,
helper return status 1, identical final ButtonHelp work and mapped data, and
the bounded register/stack result above. The expected message output is a
single copied line in `ButtonHelpWork+0x4D0`; the second line slot remains
zeroed. Color, `+0x550`, `+0x554`, `+0x55C`, and `+0x4CB` effects come from the
reviewed helper contract.

Add one private wrong-row control: in the candidate run for selection 1, alter
only the candidate entry's incoming `r0` to the valid selection-0 row pointer.
The control must be rejected by the pre-call/entry pointer assertion and by the
different final helper text bytes. This checks that actual row selection is
part of the composition comparison. Keep the control change in the private
candidate image/harness; do not edit the candidate source or shared runner.

## Evidence limits and next action

This design runs original TBB getters and original state-5 caller arithmetic,
but starts at `0x001EA12C` with a synthetic callback frame and valid seeded
selection. It does not prove the full callback's path to this point, title
manager initialization in a live process, other localized assets, malformed
or overlong strings, text rendering, event/input internals, later state-5
branches, production linking/placement, or Azahar/game behavior. The four
actual strings cover only this extracted TitleTable and the candidate's
bounded single-line domain.

Next, assign a separate implementation/validation packet for a private caller
composition harness using these fixture addresses and projections. Freeze the
candidate, asset, and pinned image during that work; return the per-selection
report, one detected wrong-row control, object/text hashes, and a structured
handoff. Do not treat this plan or the earlier pre-call pointer test as helper
caller equivalence.
