# H2 Calc interior-entry audit

## Run-002 refresh

This refresh revalidated the audit against the current frozen packet after the coordinator updated Calc's ledger classification and integration report. The Calc row is now `non_matching`; its start, size, code image, and body address range are unchanged. The complete run-002 `input_sha256` set matched, and the direct-reference and aligned-pointer scans below were rerun against those inputs. This changes the recorded identity/classification only; the static scan outcome is unchanged.

## Result

For the pinned `code.bin` and its complete ledgered ARM text spans, I found no
outside ARM direct branch/call target and no outside aligned absolute code
pointer into `[0x001EA92C, 0x001EB02C)`. The only four-byte-aligned image words
that resolve to the interior are the five dispatch-table entries inside Calc's
own ledgered body. They are excluded as intra-function control flow, as
requested. Under this static audit, an entry branch at `0x001EA928` has no
evidenced supported old-body caller after the overwritten entry word.

This conclusion is bounded to direct ARM branch encodings and aligned absolute
pointer words in the pinned static image. It does not rule out a runtime-
computed or encoded-relative indirect target, code generated into memory, or a
caller outside this image.

## Identities and scan coverage

- All `input_sha256` entries in
  `build/agent-work/H2-semantic/h2-calc-interior-entry-audit/run-002/task.json`
  matched before and after the scan. The refreshed packet records the updated ledger and
  production integration report identities; run-001 remains preserved.
- Pinned image: `extracted/exefs/code.bin`, 3,633,152 bytes, SHA-256
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Its
  configured text mapping is file offset `0`, VMA `0x00100000`, size
  `0x002FE624`.
- `config/functions.csv` is SHA-256
  `d293c3b0a8a53eaf3cf3750ece6ce0d7886fac3eda8293462cd4aa07ba2f38a1` and has
  10,967 ledger rows. All rows are within the text interval; each start and
  size is four-byte aligned. The rows are contiguous, with no gap or overlap,
  covering the full text interval `[0x00100000,0x003FE624)`. Calc's row is
  `0x001EA928, 1796, non_matching, script_vm, script_vm_func_001ea928`; its own
  range `[0x001EA928,0x001EB02C)` was excluded as a source of external edges.
- The full ledger scan decoded 784,328 ARM words outside the Calc row. It
  examined 121,131 direct B/BL encodings and 1,479 BLX-immediate encodings.
  None target the interior interval. The direct-reference scan starts only at
  four-byte-aligned ledger addresses and decodes the ARM immediate target from
  `PC+8`, sign-extending the 24-bit displacement; BLX immediate includes its H
  bit and is checked with the Thumb-state bit removed.
- The aligned pointer scan examined every four-byte-aligned word in the entire
  `code.bin` (text, rodata, data and file padding), not only `.text`. It masks
  bit 0 to account for a Thumb function pointer before checking the target
  interval.

## Pointer hits and false positives

The aligned four-byte scan returns exactly these five values:

| File offset | VMA | Stored target | Classification |
| --- | --- | --- | --- |
| `0x000EA950` | `0x001EA950` | `0x001EA964` | Calc's own state dispatch table |
| `0x000EA954` | `0x001EA954` | `0x001EAA60` | Calc's own state dispatch table |
| `0x000EA958` | `0x001EA958` | `0x001EAF98` | Calc's own state dispatch table |
| `0x000EA95C` | `0x001EA95C` | `0x001EAFEC` | Calc's own state dispatch table |
| `0x000EA960` | `0x001EA960` | `0x001EB004` | Calc's own state dispatch table |

All five words lie inside the excluded Calc function, at the dispatch table
following its initial instructions. There are no other four-byte-aligned
absolute pointer candidates, including in rodata/data and no odd-bit Thumb
pointer candidates.

An additional two-byte-aligned scan finds one non-word-aligned candidate at
file offset `0x002CF02E` (VMA `0x003CF02E`), whose overlapping little-endian
window is `0x001EAAFF`. Masking bit 0 produces `0x001EAAFE`. This is not a
pointer: the
source offset is `2 mod 4`, and the four bytes are the second halfword of the
ARM `bge 0x003CEFE4` at `0x003CF02C` followed by the first halfword of the ARM
`b 0x003CF0B0` at `0x003CF030`. ARM disassembly at those aligned instruction
addresses confirms it is an instruction-overlap artifact.

A raw byte-by-byte scan yields 16 more odd-offset overlapping words into the
numeric interval, at file offsets
`0x0008FCB3`, `0x0008FCB7`, `0x000AC67D`, `0x0014BD89`, `0x001811F1`,
`0x001AFC99`, `0x00278937`, `0x00293D89`, `0x002CCE79`, `0x003757D9`,
`0x003757E1`, `0x003757E9`, `0x003757F1`, `0x003757F9`, `0x00375801`, and
`0x00375811`. Every one starts at an odd file offset, so none is a naturally
aligned 32-bit ARM function pointer. The seven offsets in the `0x003757D9`
through `0x00375811` group are in the data region; the others overlap text
instruction bytes. They were not counted as pointer references. In total, the
raw byte-pattern scan finds 22 windows: five aligned internal table entries,
one two-byte-aligned instruction overlap, and sixteen odd-offset matches.

## Assessment and limits

The static image audit found no outside direct branch/call or aligned absolute
pointer that would continue execution in the old Calc body after an entry-only
redirect. The only aligned interior pointers are the function's own jump-table
targets. This addresses the interior-entry risk for references represented by
the pinned image's ARM branches or absolute pointer words.

The audit cannot identify a pointer assembled arithmetically at runtime, a
relative-offset table that is not represented as an absolute pointer, external
code outside `code.bin`, or memory-generated code. Its mode classification
comes from the full four-byte-aligned `config/functions.csv` text ledger; it is
not a whole-program dynamic call-graph proof. No compile, source/ledger edit,
emulator, RSP, keyboard, or mouse operation was performed.
