# Independent review: H18 signed-byte stage (`0x00121d70`)

## Review result

The offline placement/patch construction is internally consistent and the checked evidence supports a staged-image review. I found no collision or branch/interworking defect. This does **not** establish that a real loader/title runtime maps and executes the cave; the handoff correctly leaves that boundary unverified.

## Independently verified facts

- The pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching the packet and both stage reports.
- Segment metadata places text at VMA `0x00100000`, logical size `0x002fe624`, aligned size `0x002ff000`, and rodata at `0x003ff000` / file offset `0x002ff000`. The candidate cave address `0x003fe624` is the first byte after logical text, aligned to 4, and lies in the final page-rounded text interval before rodata. The pinned image has exactly 2,524 zero bytes over `[file offset 0x2fe624, 0x2ff000)`. The 28-byte body fits wholly in that interval (2,496 bytes remain afterward), and an independent catalog overlap scan found no span covering it.
- Entry patch occupies the full original 12-byte span at VMA `0x00121d70` / file offset `0x00021d70`. Its first word is `0xea0b722b` (`B`, unconditional, no link), which independently decodes to target `0x003fe624`; the remaining two words are ARM NOPs. Both entry and cave are word-aligned with bit 0 clear. The 28-byte body decodes as ARM and ends in `bx lr`; the branch preserves the original caller LR, and the return uses the original ARM-state LR.
- Independent ARM branch scan reproduced the sole direct caller, `BL` at `0x00110f44 -> 0x00121d70`. The scan found no branch into the entry interior. The actual caller starts at `0x00110f3c`: literal load, global-pointer load, BL, `cmp r0,#0`, then `beq 0x00111008`; the nonzero path proceeds at `0x00110f50`. This matches the staged runner's two stop continuations.
- I independently parsed `code.staged.ips`: two ordinary records, `(offset 0x21d70, length 12)` and `(offset 0x2fe624, length 28)`, followed by EOF and no trailing bytes. Applying both records to the pinned image reproduced `code.staged.bin` byte-for-byte; its SHA-256 is `a0a00341aff58b407490cedd281d220a3a83ed7161a02372bbd30f99664b53d5`. The IPS SHA-256 is `73169f032f95ba8637f64b473c489ca900790dd3dd7c1645e384a5d8e984f97d`. Both seed reports carry the same staged-image and IPS hashes.
- The supplied seed reports are hash-pinned by the review packet and show 512/512 patched-image direct-entry comparisons plus 512/512 caller-window comparisons each, reaching both caller continuations. The runner executes the patched image through the entry veneer and body, rather than comparing a separately injected body only.

## Cave / loader interpretation

The cave is located in the final page-rounded text page: logical text ends at `0x003fe624`, while rodata begins at the next aligned page `0x003ff000`. This is good static placement evidence and is consistent with the configured executable text mapping. The review did not inspect a live loader or boot a title, so actual runtime page permissions, image patch ingestion, and execution at the cave remain unverified. The staging artifact is suitable for an offline staged-image result, not proof of runtime integration.

## Limits retained

The direct/xref and pointer searches are aligned static scans; indirect, computed, relocated, Thumb, unaligned, or runtime-generated references can be missed. Caller composition seeds `0x00433158` with synthetic readable RAM and does not establish the runtime pointee's type/lifetime/extent or execute its producer. No candidate recompilation, emulator, loader, title boot, or whole-game test was performed during this independent review. The source implementation and ledger were not changed.

## Recommendation

Accept the static placement, ARM veneer, IPS roundtrip, and supplied patched-image/caller evidence for the bounded offline staging claim, with loader/runtime mapping explicitly left open. Require a separate loader/runtime-stage validation before making an integration or game-execution claim.
