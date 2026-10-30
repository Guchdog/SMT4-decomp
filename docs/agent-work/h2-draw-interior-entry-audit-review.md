# Independent review: Draw interior-entry and literal audit

## Review result

The report's central direct-reference finding is supported, with one important boundary distinction. Scanning all ledgered ARM words and the whole aligned image confirms no external direct branch/call or aligned absolute pointer enters the actual retained suffix `[0x002CB588,0x002CB75C)`. The incoming suffix targets found are from Draw itself. The two old main-to-suffix edges, `0x002CB0AC -> 0x002CB74C` and `0x002CB580 -> 0x002CB6D4`, have source instructions inside the proposed 1,464-byte main write `[0x002CAFD0,0x002CB588)` and therefore are replaced. The remaining suffix edge at `0x002CB598 -> 0x002CB648` is wholly within the retained suffix.

The suffix back-edge at `0x002CB748` is `bgt 0x002CB0B0`; its target is in the replacement body. I found no direct branch source outside Draw into the suffix and no aligned absolute pointer into the suffix. Under these bounded static scans, the retained old suffix does not have an evidenced outside entry.

The replacement's actual return also matters. Inspection of the split production object identifies a return at `0x002CB55C` (`pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}`), followed by symbol-tail literal/pool bytes through `0x002CB588`; the relocation at offset 1,460 is at `0x002CB584`. It is not a `BX LR` instruction, but it does return through `pc` before the retained suffix begins. Thus an exact 1,464-byte write at `0x002CAFD0` does not fall through into old suffix bytes, provided the placement builder preserves this code/data layout and resolves relocations without changing control flow. The returned body is 20 bytes shorter than the interior audit interval's end at `0x002CB59C`, so the manifest must explicitly record the actual write and the retained `[0x002CB588,0x002CB59C)` bytes.

## Reproduced original edges and suffix reachability

Using the pinned `code.bin` at text VMA `0x00100000`, I decoded the two requested original words independently:

| Source | Original instruction | Target | Classification |
|---|---|---|---|
| `0x002CB0AC` | `ble` | `0x002CB74C` | Old main-to-suffix edge; source is overwritten by the new main. |
| `0x002CB748` | `bgt` | `0x002CB0B0` | Retained suffix back-edge into the overwritten body. |

A complete ledgered-text B/BL/BLX-immediate scan for targets in the actual retained suffix found nine source-to-target edges. Two originate in the old main (`0x002CB0AC -> 0x002CB74C` and `0x002CB580 -> 0x002CB6D4`); both source words fall in `[0x002CAFD0,0x002CB588)` and disappear with the replacement. The other seven originate and end within the retained Draw suffix, including `0x002CB598 -> 0x002CB648`; none comes from another ledger function. The full-image four-byte aligned absolute-pointer scan found zero targets in the suffix (bit 0 masked for Thumb-tagged pointers).

The audit report's requested interval `[0x002CAFD4,0x002CB59C)` is 1,480 bytes and is not the actual production write interval. Starting the 1,464-byte body at the original entry produces `[0x002CAFD0,0x002CB588)`. This leaves 468 bytes of the 1,932-byte original function range. Treat `[0x002CB588,0x002CB75C)` as retained suffix; its first 20 bytes are also inside the report's requested interior range. A patch manifest that uses only the audited interior bounds would misstate the number of bytes replaced.

## Old format literal reference

The original `%s\0` bytes are at `0x002CB410` (function-relative offset `0x440`). I independently decoded the only PC-relative ADR-form reference to that address: `add r1, pc, #0xb8` at `0x002CB350`; ARM PC is `0x002CB358`, giving `0x002CB410`. Both the instruction and literal are within the actual new-main write interval. I found no PC-relative LDR/VLDR literal-pool reference targeting the old string, no additional ADR to it, and no aligned absolute-pointer word to `0x002CB410` across the pinned image. The original literal contains `25 73 00` (`%s\0`); `0x002CB414`, immediately after it, is code targeted by another branch and must not be mistaken for string data.

The split-object evidence records the new local `.rodata` string reference as `R_ARM_ABS32` at symbol offset 1,460 with `.rodata` section addend 0; under the proposed tail layout its string address is `0x003FEED0`. A placement-aware builder must retarget that relocation and verify the final formatter argument points at the moved string. The old internal ADR is overwritten with the old body, so no separate old-literal reader remains in the retained suffix under the audited encodings.

## Assessment, provenance, and limits

The audit report's no-external-entry conclusion holds for direct ARM branches and aligned absolute pointers in the pinned image. Combined with the production object's return before `0x002CB588`, this supports retaining the old suffix as unreachable under those static mechanisms after an exact replacement at `0x002CAFD0`. It is not a proof against computed/encoded addresses, indirect task callbacks, unaligned or relative tables, external code, Thumb paths outside the declared excluded CRT span, or generated code. The builder should additionally verify all final-address internal branches remain within the replacement/helper map, the return remains before retained bytes, and changed bytes match the declared patch records.

Frozen review inputs matched before and after review. Pinned `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; `config/functions.csv` SHA-256 is `d293c3b0a8a53eaf3cf3750ece6ce0d7886fac3eda8293462cd4aa07ba2f38a1`. Draw's ledger row remains `0x002cafd0,1932,matching,ui,ui_func_002cafd0,src/engine/leaf_batch43_a.cpp`; this audit does not update it. No compilation, image patch, ledger/source edit, emulator, RSP, profile, keyboard, or mouse operation was performed. This is a static placement review, not semantic or runtime approval.
