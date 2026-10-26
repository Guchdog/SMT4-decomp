# H1 title/message contract: `0x0029F10C` and copy helper `0x002C5FF4`

## Scope and evidence

This is a read-only static contract against the pinned ARM image. The image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

- `0x0029F10C` has a 316-byte recorded extent `[0x0029F10C,0x0029F248)`, extent hash `9e432ddfb9a774f0665383f3d790f83fb7b79b44121a8e96806a114e37314873`. Executable instructions end with `POP {...,pc}` at `0x0029F240`; the final word at `0x0029F244` is a literal pool entry (`0x0043DA28`), not code.
- `0x002C5FF4` has a 136-byte extent `[0x002C5FF4,0x002C607C)`, hash `644501596cdc02773609b59f6b01e737be96c516e4546919af3c259c1b64746e`; the last instruction is `BX LR` at `0x002C6078`.
- The H1 main-menu callback is `ui_func_001e989c` `[0x001E989C,0x001EA7F0)`. The H1 title initializer is `titleConfig_func_002f4ca0` `[0x002F4CA0,0x002F4EDC)`.

The instruction and literal addresses below were decoded directly from `extracted/exefs/code.bin`; names in source aliases are corroborating labels, not the basis for the behavior claims.

## H1 caller inputs

At callback entry, `0x001E98A0` loads a literal pointing to the title-work global cell `0x0044E300`; `0x001E98AC` loads the work pointer from that cell and `0x001E98B0` copies it into `r4`. The selected menu index is read from `[work+8]`.

The main-menu message path calls `0x0029F10C` twice in this callback (the callback dispatch table at `0x001E98C4` identifies state 2 at `0x001E9A3C` and state 5 at `0x001E9D08`):

1. At `0x001E9ADC` in state 2, after `ButtonHelp_Init` at `0x001E9A9C`, it loads TBB global subtable `(slot=0x3A, subtable=0)` with `0x002C0EC4`, gets its payload with `0x002C0E9C`, computes `payload + selected_index*0x56 + 0x16`, and calls the target. The selection is loaded from `[work+8]` at `0x001E9AAC`.
2. At `0x001EA15C` in state 5, it reloads the selected index from `[work+8]`, gets the same slot/subtable payload, computes the same row/field pointer, and calls the target.

At both sites `r1` is loaded from the same literal word at `0x001E9EC4`, value `0x323232FF`. The H1 milestone documents four selection indices (`0..3`) and the slot-`0x3A` message payload as 0x56-byte rows with the string field at `+0x16`. Therefore the H1 message input is a selected TBB-row string pointer, not a fixed C string literal. The exact localized bytes cannot be named from the pinned code image alone; the TBB asset contents were not part of this review packet.

The title configuration path is a distinct H1 call mode. In `titleConfig_func_002f4ca0`, `LDR r1,[pc,#0xd8]` at `0x002F4DF4` resolves to literal `0x002F4ED4 = 0x323232FF`; `MOV r0,#0` at `0x002F4DF8` precedes `BL 0x0029F10C` at `0x002F4DFC`. This supplies a null text pointer with the same color. It is the color/reset path, not an actual title string. The caller overwrites `r0` immediately afterward and does not consume the helper's return.

A separate tail branch in `StatusDown_SetDisplayMode` at `0x00293064` also supplies `r0=0` and the same color literal. It is a non-title caller of the null mode. The wider image has many unrelated calls to this shared helper; this contract covers the H1 callback's two message calls, the title initializer's null call, and that directly observed null-mode example, not every subsystem's caller domain.

## `0x0029F10C`: arguments, effects, and returns

The pinned entry begins with `LDR r2,[pc,#0x130]` at `0x0029F10C`. ARM PC-relative resolution gives literal address `0x0029F244`, whose word is `0x0043DA28`. It then loads `r7=[0x0043DA28+4]`: the manager's work pointer. This routine does not check the manager or work pointer for null before writing. The H1 callback calls `ButtonHelp_Init` earlier in its path, but allocation/lifecycle correctness remains a caller precondition rather than a check in this body.

The effective input convention is `r0 = optional byte-string pointer`, `r1 = color word`. It saves/restores `r4-r8` and SP (`PUSH {r4-r8,lr}` / `POP {r4-r8,pc}`). It has two observable paths:

### Null `r0`: color/reset mode

`MOVS r5,r0` at `0x0029F114` sets the zero condition. Both modes first store `r1` at `work+0x4CC`, clear word `work+0x550`, and set byte `work+0x554` to `0xFF`. On null input, `STRBEQ` at `0x0029F130` clears `work+0x4CB`, and `BEQ 0x0029F240` skips all text-buffer clearing/copying. It does not touch `work+0x55C`. It returns `r0=0xFF` (the `MOV r0,#0xFF` used for `+0x554` remains live).

### Non-null `r0`: message-copy mode

This path zeroes 0x80 bytes at `work+0x4D0..work+0x54F` using 32-bit stores, then scans the input using signed-byte loads (`LDRSB`) from index zero. Byte `0x0A` is a line separator; byte zero terminates the current line. Other bytes—including high-bit bytes read as negative signed values—are ordinary content.

For a line ending at input index `i`, it calls `0x002C5FF4` with:

- `r0 = work + 0x4D0 + line_index*0x40` (destination),
- `r1 = input + line_start` (source),
- `r2 = i - line_start` (byte count; delimiter and NUL are excluded).

The first line uses `work+0x4D0`; the second uses `work+0x510`. There are exactly two call PCs: `0x0029F1F4` on NUL and `0x0029F218` on newline. After newline it increments line index and sets the next start after the delimiter. It scans at most two lines and reads indices `0..127`: loop continuation at `0x0029F224..0x0029F230` stops once the incremented index reaches `0x80`, or after the second newline. If it reaches that scan limit without seeing NUL/newline, it exits without copying the unfinished final line. The output bytes are not NUL-terminated by the copy call; the earlier zero-fill provides trailing zeros only when writes stay within their expected buffer areas.

There is no per-line length check. Each logical line slot is 0x40 bytes, but a first line can be copied with length up to 127 bytes, crossing into the second slot. A second line starts at `+0x510`; only `0x54` bytes remain before the end of the modeled 0x564-byte `ButtonHelpWork`, so a second-line copy longer than 84 bytes can write past that workspace. Such overlong inputs are not a safe C++ object contract. The actual H1 TBB line lengths are unknown here, so they must not be assumed safe without reading/validating those asset records.

On every non-null path that reaches the common tail, it clears `work+0x55C`, sets `work+0x4CB` to 1, and returns `r0=1`. The H1 callback's next instructions overwrite `r0`, so this status is not consumed there. The inspected source aliases declare the helper `void` or name it “fade color”; the pinned code instead accepts a text pointer, returns 0xFF/1, and copies message bytes into workspace buffers.

The manager/work layout agrees with the existing project model: manager global at `0x0043DA28`, work pointer at manager `+4`, and a `ButtonHelpWork` extent of `0x564`. Independently from that model, this function requires writable work memory through at least byte `+0x55C` (minimum extent `0x55D`) even on its non-null tail. Its null mode still requires writable offsets through `+0x554`.

## `0x002C5FF4`: byte-copy helper contract

The relevant ABI is `r0=destination`, `r1=source`, `r2=byte length`. The body makes no external call and no null/overlap checks. For lengths up to three it uses the byte-tail path. For longer copies it advances the destination bytewise to word alignment, then selects a path based on source alignment. It performs word transfers and byte/word tails, so the semantic operation for the H1 use is a forward byte copy of the requested length. It is not a `memmove`: overlapping source and destination ranges are not supported by this evidence.

At `0x002C602C`, if the post-prefix source is word-aligned, it branches (not calls) to `0x002BCF58`, the separate optimized copier. That helper saves/restores its own callee-saved registers, copies 32-byte chunks and tails, and returns through the original LR to the `0x0029F10C` caller. The unaligned-source path stays in `0x002C5FF4`. The helper advances `r0/r1` during copying; the message routine ignores that result and replaces `r0` with its own 0xFF/1 status.

The two direct calls from `0x0029F10C` are the complete copy-helper dependency for this H1 contract. `0x002C5FF4` also has many unrelated image-wide memory-copy callers; they are outside the H1 title message scope and were not individually traced here.

## Defensible editable-C++ scope and validation

Start with a readable experimental C++ reconstruction for the two-argument message helper, preserving the null/reset and non-null/copy paths, the exact H1 TBB pointer formula, byte delimiter behavior, return values, and callee-saved ABI. Model workspace as explicit byte offsets until a full safe structure is supported. Implement the copy dependency as a separate forward-copy candidate with a stated non-overlap precondition; do not copy the optimized ARM instruction pattern into the C++ source.

The first differential should include the actual H1 table entries once the TBB asset is available, plus synthetic strings for null, empty, one-line, two-line, newline at boundary, NUL at indices 126/127, no terminator before index 128, and signed high-bit bytes. Use guard bytes around workspace and report the overlong second-line writes as unsupported/faulting cases rather than allowing C++ object overflow to masquerade as safe behavior. Test the copy helper across all source/destination alignment pairs and lengths around 0, 1–4, 7–9, 31–33; include an overlap negative control. Then compare the H1 caller's selected index and resulting workspace bytes in an offline ARM differential. No runtime initialization order, actual asset string bytes, rendering, or H1 gameplay behavior is established by this static contract.


