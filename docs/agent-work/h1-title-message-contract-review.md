# Independent review: H1 title/message helper contract

## Review result

**Partial; correct the string-capacity contract before treating it as a safe
C++ object model.** Direct decoding of the pinned image supports the main
behavioral facts for `0x0029F10C`, its dependency `0x002C5FF4`, and the scoped
H1 caller arithmetic. The existing contract correctly identifies the null
reset mode, message mode, two line destinations, scan limit, copy dependency,
return values, and missing null checks. Its unsafe-domain note needs a sharper
boundary: a second-line copy longer than 64 bytes already leaves its nominal
`0x40` slot and overwrites adjacent fields; length 85 is the first size that
exceeds the modeled `0x564` allocation. A first line longer than 64 bytes also
overlaps the logical second slot.

This is an independent static review, with no compilation, differential test,
emulator, or runtime. The frozen packet inputs matched. The pinned image SHA-256
is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

## `0x0029F10C` direct decode

The 316-byte function extent is `[0x0029F10C,0x0029F248)`, hash
`9e432ddfb9a774f0665383f3d790f83fb7b79b44121a8e96806a114e37314873`. Its
executable return is `POP {r4,r5,r6,r7,r8,pc}` at `0x0029F240`; the following
word at `0x0029F244` is literal `0x0043DA28`. Entry loads that manager-cell
address and then the work pointer at manager `+4`. The function does not check
either pointer for null. It saves/restores `r4-r8` and returns with balanced
SP.

The effective arguments are `r0 = optional input byte string` and
`r1 = color word`. Both modes store `r1` at work `+0x4CC`, clear the word at
`+0x550`, and set byte `+0x554` to `0xFF`.

- **Null `r0`:** clears byte `+0x4CB`, skips the buffer clear and copy loop,
  leaves `+0x55C` untouched, and returns `r0=0xFF`.
- **Non-null `r0`:** clears 128 bytes `[+0x4D0,+0x550)`, then uses `LDRSB` to
  scan input indices `0..127`. NUL ends/copies the current line; LF (`0x0A`)
  copies the current line without the delimiter, advances the line start, and
  moves to line slot 1. Other byte values, including high-bit bytes, are
  treated as content. The two copy call sites are `0x0029F1F4` (NUL) and
  `0x0029F218` (LF); destination is `work+0x4D0+line_index*0x40`, source is
  `input+line_start`, and length is `index-line_start`.

The loop can process no more than two lines and reads no index above 127. If
the scan reaches index 127 without NUL or LF, it exits without copying that
unfinished line. A second LF ends the scan after the second line copy. On the
non-null common tail it clears byte `+0x55C`, sets byte `+0x4CB` to 1, and
returns `r0=1`. The scoped H1 callers overwrite `r0` immediately afterward;
they do not consume this helper status.

### Buffer and workspace limits

The first slot begins at `+0x4D0`, the second at `+0x510`, and each nominal
slot is `0x40` bytes. The clear spans both slots but does not establish that
either copy is capped to its slot:

- First-line length 65 or greater writes beyond its nominal first slot into
  the second slot. The first-line copy can be as long as 127 bytes while still
  remaining inside the 128-byte cleared span. If a second line is then copied,
  it can overwrite bytes already placed in the overlapping portion of the
  first line.
- Second-line length 65 is the first size to overwrite beyond its nominal
  slot: byte index 64 lands at `work+0x550`, whose word was cleared before the
  scan. At length 69, the copy reaches `+0x554`, previously set to `0xFF`.
  Longer copies can also overwrite subsequent fields before the common tail
  resets `+0x55C`.
- The modeled work extent is `0x564` bytes, leaving 84 bytes from second-slot
  start `+0x510` through the last in-bounds byte `+0x563`. Thus a second-line
  length of 85 or more writes outside that modeled object. This allocation
  size is a project model, not a bound enforced by the helper.

Consequently, `char line1[64]`/`char line2[64]` are safe logical-slot models
only when each copied line is at most 64 bytes. The pinned routine itself has
no such guard; any C++ candidate must state and validate its accepted string
domain, and must not silently treat longer inputs as safe. Independently of
the allocation model, this body requires writable memory through byte
`+0x55C` on its non-null path (minimum extent `0x55D`) and through byte
`+0x554` on its null path (minimum extent `0x555`).

The project model corroborates a `0x564`-byte `ButtonHelpWork` allocation and
zeroing (`include/camp/unite.h`, SHA-256
`68fa7bf3d9b278dc0ef09b93edc32c6ab2d5d251341f040354bcab06c20d1b73`;
`src/camp/unite.cpp`, SHA-256
`ed36340f835f41a08aaed4360671a2b80b5a4240db021106bc288149c370bed4`). These
were supplemental current-workspace reads, not among the packet's frozen read
paths; use the pinned body for its direct access requirements and keep the
model claim qualified.

## `0x002C5FF4` copy dependency

The 136-byte extent is `[0x002C5FF4,0x002C607C)`, hash
`644501596cdc02773609b59f6b01e737be96c516e4546919af3c259c1b64746e`; `BX LR`
at `0x002C6078` is its final instruction. Its ABI is `r0=destination`,
`r1=source`, `r2=length`. Short lengths use byte tails. Longer lengths align
the destination with byte copies, then select based on source alignment. If
the adjusted source is aligned, it branches to `0x002BCF58` (not a call).
That 116-byte optimized body, `[0x002BCF58,0x002BCFCC)`, has hash
`d4e075de5405e2393514369688bf643d3d2064f5386b321b2b9f0ee3d511e0fe` and
copies forward in word/chunk and tail operations. It saves/restores the extra
callee-saved registers it uses, including LR, so the branch returns through
the original caller's LR. The parent helper also has a forward unaligned-source
path and byte/word tails; it advances `r0` and `r1` as it copies.

No overlap detection or direction selection exists, so this is not supported
as `memmove`; overlapping ranges, especially `destination > source`, can
overwrite unread source bytes. Null-pointer behavior is not guarded. The
message helper ignores the copy helper's advanced `r0` and assigns its own
status after the scan.

## H1 caller arguments and source alias review

At state 2 call site `0x001E9ADC`, the callback has selected index from
`[work+8]` in `r6`. It passes slot `0x3A`, subtable 0 to `0x002C0EC4`, gets
payload via `0x002C0E9C`, computes `payload + index*0x56 + 0x16`, loads color
`0x323232FF` from literal `0x001E9EC4`, then calls `0x0029F10C`.

At state 5 call site `0x001EA15C`, it reloads index from `[work+8]`, performs
the same slot/subtable lookup and `index*0x56 + 0x16` pointer arithmetic, and
uses the same shared literal at `0x001E9EC4` with value `0x323232FF`. These
instructions establish the caller-side row stride and string-field offset;
they do not establish the localized bytes stored in the selected TBB row.

The title initializer at `0x002F4DFC` passes null `r0` and color
`0x323232FF` from literal `0x002F4ED4`, so it uses reset mode. The `StatusDown`
tail caller at `0x00293064` also passes null `r0`; its literal is at
`0x00293070` and also contains `0x323232FF`. The caller alias
`Camp_SetFadeColor(u32,u32)` in `src/camp/title_flow.cpp` does not describe
the pinned helper's first argument or its return/workspace effects. The alias
in the matching ARM listing is a naked `void` stub; neither source alias is a
recovered semantic contract.

The packet has no localized TBB asset bytes. The static caller proves the
pointer formula and color argument only. It cannot prove actual localized
message contents, real line lengths, runtime initialization order, or rendered
text.

## Evidence and next action

- Pinned helper/copy extents and body hashes: independently recomputed.
- H1 message and null-mode caller arguments/literals: independently decoded.
- Compilation, candidate differential, runtime rendering: not run.
- Recommendation: amend the contract to distinguish nominal 64-byte slot
  capacities from the helper's unbounded copy lengths, especially the second
  line's 65-byte adjacent-field overwrite and 85-byte allocation overrun. Then
  use an explicit bounded C++ input contract and test actual TBB rows once the
  asset is made available.

## Out-of-scope navigation-matrix activity disclosure

Before the coordinator redirected me to this review, I ran an extra matrix
experiment in the already-existing navigation-matrix task directory. That
report is intentionally not cited as evidence here and does not belong to this
review. I briefly added two projections to the navigation runner
(`register_projection` and `bounded_memory`) and adjusted its test, then
restored both code/test files to the earlier hashes. Current hashes are:

- `tools/h1_navigation_adapter_matrix_experiment.py`:
  `13e8b219f7767c3aea34ec46c090190d08aa79b937a46d37f62ef222119c4789`
- `tests/test_h1_navigation_adapter_matrix_experiment.py`:
  `dee635b6576430f20aede95ad0971d135f6a1d075ba28899875cb6379aceba7e`
- `docs/agent-work/h1-navigation-adapter-matrix.md`:
  `5d54d870e0ca2d87a973ee5da1a78611c05b0b1ce239f23cd9740e23a0489057`

The unreferenced private `results-v3` files remain under the navigation packet.
Their SHA-256 values are disclosed in this review's structured handoff so the
coordinator can validate or clean that separate task's artifacts.
