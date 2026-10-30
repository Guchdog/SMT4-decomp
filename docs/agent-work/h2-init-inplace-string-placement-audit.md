# H2 initializer in-place string placement audit

## Result

The pinned ExHeader and `code.bin` provide a 68-byte, four-byte-aligned zero-filled file-backed tail inside the ExHeader-sized `.rodata` allocation. Its proposed range is VMA `[0x0042AB78,0x0042ABBC)` and decompressed `code.bin` offsets `[0x0032AB78,0x0032ABBC)`. The pool fits within the `.rodata` page tail `[0x0042AB78,0x0042B000)` / `[0x0032AB78,0x0032B000)`, which is 1,160 zero bytes.

Static scanning found one external direct call to the initializer's entry `0x002F4CA0`, from `0x001EA3B4`. That entry remains the same with an in-place replacement. No direct branch/call targets or aligned absolute pointers enter the body interior that would be replaced. The only old-string references found are four ADR instructions within the original initializer itself. There are no outside ADRs, PC-relative literal loads of pointer words to those strings, or aligned absolute pointer words to the old string addresses.

The layout is therefore statically size-feasible. It is not yet a production patch: the current candidate embeds the four old string addresses, so those constants must be changed to the proposed pool addresses and the candidate rebuilt/rechecked. Also, ExHeader segment/page metadata and `game_info.json` do not expose explicit page protection or prove that the runtime loader copies this file-backed padding byte-for-byte. The pool's read-only access at runtime remains a mapping assumption until verified separately.

## ExHeader and exact image offsets

`tools/extract.py` reads the ExHeader segment triples as little-endian `(vaddr, pages, size)` at offsets `0x10` (text), `0x20` (rodata), and `0x30` (data). Re-reading those fields from the frozen `extracted/exheader.bin` gives:

| Segment | VMA | Pages | Page capacity | Declared size | Page tail | `code.bin` file offset |
|---|---:|---:|---:|---:|---:|---:|
| text | `0x00100000` | 767 (`0x2FF`) | `0x2FF000` | `0x2FE624` | `0x9DC` | `0x00000000` |
| rodata | `0x003FF000` | 44 (`0x2C`) | `0x2C000` | `0x2BB78` | `0x488` | `0x002FF000` |
| data | `0x0042B000` | 76 (`0x4C`) | `0x4C000` | `0x4B644` | `0x9BC` | `0x0032B000` |

The `.rodata` VMA ends at `0x003FF000 + 0x2BB78 = 0x0042AB78`; its 44-page allocation ends at `0x0042B000`. The corresponding decompressed `code.bin` interval is `[0x002FF000,0x0032B000)`, so the tail begins at file offset `0x002FF000 + 0x2BB78 = 0x0032AB78`. I verified bytes `[0x0032AB78,0x0032B000)` are all zero. The full `code.bin` is `0x377000` bytes with SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The ExHeader values identify the rodata segment's allocated pages, and the local metadata calls the segment `rodata`; neither the parsed fields nor `config/game_info.json` contains an explicit read-only permission bit or a loader copy/protection test. The audit proves the pool fits the file-backed page tail and starts zero-filled, not that a running loader exposes the tail with the expected protection.

## Proposed string pool and initializer patch records

The original initializer is `[0x002F4CA0,0x002F4EDC)`, 572 bytes. The reviewed candidate body is 552 bytes and would occupy `[0x002F4CA0,0x002F4EC8)`, leaving the final 20 original bytes unchanged. The original inline strings all overlap those 552 bytes: the final string starts at `0x002F4EC4`, so its first four bytes would be overwritten even though its last 12 bytes remain after the candidate body.

A four-byte-aligned pool of 68 bytes fits at the rodata tail start:

| Candidate pointer constant to update | String | Payload bytes | Pool offset | VMA | `code.bin` file offset | Slot bytes |
|---|---|---:|---:|---:|---:|---:|
| `kCalcTaskName` | `TITLE_CONFIG_MAIN\0` | 18 | `0x00` | `0x0042AB78` | `0x0032AB78` | 20 |
| `kDrawTaskName` | `TITLE_CONFIG D\0` | 15 | `0x14` | `0x0042AB8C` | `0x0032AB8C` | 16 |
| `kConfigScriptName` | `camp/config.bf\0` | 15 | `0x24` | `0x0042AB9C` | `0x0032AB9C` | 16 |
| `kConfigMessageName` | `camp/config.mbm\0` | 16 | `0x34` | `0x0042ABAC` | `0x0032ABAC` | 16 |

The pool ends at VMA `0x0042ABBC` / file offset `0x0032ABBC`, leaving `0x444` (1,092) bytes before the aligned rodata page boundary. The current candidate source defines these four constants as the original addresses `0x002F4E84`, `0x002F4E9C`, `0x002F4EB4`, and `0x002F4EC4`; copying the current body unchanged would keep references to the overwritten old strings. A retargeted source/object must be verified before this layout can be built.

Assuming a rebuilt body still measures 552 bytes and carries the new string addresses in its own body/literal pool, the minimum patch has two non-overlapping records: (1) the 552-byte body at VMA `0x002F4CA0`, `code.bin` offset `0x001F4CA0`; (2) the 68-byte string pool at VMA `0x0042AB78`, file offset `0x0032AB78`. No entry branch record is needed because the original initializer entry stays at `0x002F4CA0`. The 20-byte tail `[0x002F4EC8,0x002F4EDC)` remains original. These are proposed record bounds only; the modified object and final IPS do not exist in this audit.

## External entries and old string references

I parsed 10,967 four-byte-aligned ledger extents and scanned their ARM-state words for B/BL and BLX-immediate targets into the original initializer range. The only target was the expected outside BL at `0x001EA3B4 -> 0x002F4CA0`, from ledger function `ui_func_001e989c` at `0x001E989C`. It targets the unchanged entry. There were no branch/call targets anywhere else in the original initializer span; in particular, none enters the overwritten interior `[0x002F4CA4,0x002F4EC8)`. The full-image four-byte-aligned absolute pointer scan, masking bit 0 for Thumb-tagged values, found no pointers into the initializer body. There were no aligned pointer words to the four original string addresses either.

The four strings' original addresses and only decoded ADR references are:

| Old address | Exact string | Internal reference | ARM calculation |
|---|---|---|---|
| `0x002F4E84` | `TITLE_CONFIG_MAIN\0` | `0x002F4CFC: add r0, pc, #0x180` | `(0x002F4CFC + 8) + 0x180 = 0x002F4E84` |
| `0x002F4E9C` | `TITLE_CONFIG D\0` | `0x002F4D28: add r0, pc, #0x16C` | `(0x002F4D28 + 8) + 0x16C = 0x002F4E9C` |
| `0x002F4EB4` | `camp/config.bf\0` | `0x002F4DD0: add r0, pc, #0xDC` | `(0x002F4DD0 + 8) + 0xDC = 0x002F4EB4` |
| `0x002F4EC4` | `camp/config.mbm\0` | `0x002F4DE4: add r0, pc, #0xD8` | `(0x002F4DE4 + 8) + 0xD8 = 0x002F4EC4` |

All four ADRs lie within the replaced function. A fifth internal ADR at `0x002F4CAC` targets `0x002F4E44`, not any string; it points into the post-tail-call literal/data area and is not an external entry. The scan found no PC-relative LDR/VLDR literal-pool word whose contents equal an old string address, and no aligned absolute pointer to those addresses. The old strings are inline data, not branch targets. The one outside BL to the function entry is the legitimate caller and remains valid for an in-place body.

The scan is bounded to ledgered ARM branch encodings, PC-relative ADR/LDR/VLDR patterns, and aligned absolute words in the pinned image. It does not find addresses assembled from multiple immediates, relative/encoded pointer tables, dynamic callback values, non-ledgered code, or references generated at runtime. The string ADR scan walks the pinned text under the ARM-state assumption; decoded instruction hits were checked against the owning initializer and exact target formula.

## Required final-address checks and limits

Before a production patch, update all four candidate address constants, compile the initializer production TU (the experiment body is not the production symbol), check the emitted size/relocations, and construct a patch with exactly the body and pool ranges above. Confirm the loader-visible pool bytes and access mode rather than inferring protection only from segment labels.

At minimum, compare the original and rebuilt initializer at final VMA `0x002F4CA0` with the pool at `0x0042AB78`, using identical initialized snapshots and declared HLE boundaries. Compare the four task/resource string arguments, helper order, global/work/config memory, return/PC/SP, and callee-saved registers. Include baseline and distinct config bytes, poisoned work, incoming `r0` variation, and the wrong group-count control. Then run the real State-9/10 caller composition against that same final-address patched image, checking Calc/Draw task tuples, work pointer/handle linkage, readiness/reset ordering, the flag gate, and a wrong-callback control. These remain offline caller tests and do not prove that the scheduler executes Calc or Draw.

No compile, source/ledger/patcher edit, image patch, emulator, RSP, profile, keyboard, or mouse operation was performed. This static audit neither proves loader permissions nor UI, scheduler, persistence, or H2 runtime behavior.

## Provenance

- Pinned ExHeader SHA-256: `c90b444552d54dd1d63ff4a725d8919aeee5a72d3f812538fb6bbfcd1fadc8af`.
- Pinned `code.bin` SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Current candidate source SHA-256: `9b2b181a2f79683cf456b07b26484fa7d5390672b8662b71b469553280c665c5`; it still uses the old string addresses and is not a retargeted placement artifact.
- Frozen input hashes matched before and after the scan; see the run-001 packet and handoff for the complete declared set.
