# Independent review: H1 title-message real-asset inputs

## Verdict

**The four real-asset input comparisons are supported as bounded offline evidence; caller and runtime validation remain absent.** All 12 frozen task input hashes matched. I independently recomputed the `TitleTable.tbb` hash and decoded its header/first table, the four row field offsets, NUL-terminated bytes and lengths. I also checked the relevant pinned caller arithmetic, run-02's original/candidate copy routing, all declared comparison fields, build/source/report hashes, and the three inherited mutation controls. No mismatch was found. I did not compile, rerun tests, or use an emulator/runtime.

## Asset and row-pointer derivation

The frozen asset is 880 bytes with SHA-256 `edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`. Its TBCR header declares header size `0x20` and two tables. The first offset is zero, so table 0's TBL1 header starts at file `0x20`; its payload size is 344 (`0x158`) and its payload begins after the 16-byte TBL1 header at file `0x30`. The next table starts at `0x190`, after table 0's payload. The generic TBL1 row-stride field is zero; the H1 row layout instead follows the pinned caller's arithmetic.

At the state-2 caller, pinned instructions around `0x001E9AAC-0x001E9ADC` load the selected row index, request slot `0x3A`/subtable 0, obtain the table payload, multiply the index by `0x2B` then two, add `0x16`, load color literal `0x323232FF`, and call `0x0029F10C`. State 5 repeats the same calculation around `0x001EA12C-0x001EA15C`. Thus the payload-relative byte-string field is `0x56*index + 0x16`.

Applying that formula to table 0 gives the independently decoded records below. The string length excludes the terminating NUL. Each NUL is inside its row's 86-byte extent, each message is a single line, and every line length is below the candidate's 64-byte safe slot limit.

| Row | Row start in payload/file | Payload-relative string offset | File offset / NUL offset | Bytes as text | Length | Mapped source pointer |
| ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 0 | `0x00` / `0x30` | `0x16` | `0x46` / `0x6A` | `Start a new game from the beginning.` | 36 | `0x02010046` |
| 1 | `0x56` / `0x86` | `0x6C` | `0x9C` / `0xC3` | `Load a saved game and continue playing.` | 39 | `0x0201009C` |
| 2 | `0xAC` / `0xDC` | `0xC2` | `0xF2` / `0x10B` | `Configure audio settings.` | 25 | `0x020100F2` |
| 3 | `0x102` / `0x132` | `0x118` | `0x148` / `0x164` | `Download additional content.` | 28 | `0x02010148` |

The run maps the frozen asset bytes at data-map base `0x02000000 + 0x10000` and passes the computed file-offset pointer directly. For each message, the original pinned helper's copy call uses that same source pointer and exact non-NUL byte length; the candidate routes through its linked copy candidate with matching arguments. The work destination is `0x020014D0`, disjoint from the mapped asset range. This validates direct helper behavior on these bytes; it does not call the TBB slot lookup in a runtime object.

## Run-02 report and controls

The fresh report hash is `b5d1d1d2495bd0dfe5d29176eaeeb289f42948c7eeb6e4217118d663edaccc8a`. It records 13 message cases (nine synthetic plus these four asset-backed rows) and 176 direct-copy cases, with no first mismatch. Each of the four asset rows passes with no fault, equal return `r0`, preserved registers/SP, `d8-d15`, FPSCR, complete 0x20000-byte memory hash, 0x564-byte work hash, caller-stack hash, and normalized copy call name/arguments. The full projection and case results are recorded by the report; optimized pinned-copy entry counts are path-coverage diagnostics for the original and are not a requirement that the C++ byte loop reproduce that internal branch.

The unchanged candidate source hash is `68c91fe472a631d9435daa0596161ddcbea70dba011abcecfe1be8df6422305e`. The object hash is `4fbcc5b3d18d6762fb2eea0ffcddcd1f42c6922ba0fab72b5f8639e0aefb4852`, and the linked ELF hash is `05059c43b7a1a55312c3c44556bf8386588005cc34e4e79f0f09b5769b6e041f`. The command log hash is `9591982223743fe145f8d40137320ba81c49596eeff49bbe969d1de07431df79`. The candidate and report still identify the same three pinned bodies, including optimized-copy extent `0x002BCF58`; the candidate has no undefined symbols.

All three deliberate controls remain detected: wrong null-mode return (`r0` differs), omitted color store (first data mismatch at `0x020014CC`, `0xFF` versus `0xA7`), and corrupted forward-copy bytes (first mismatch at `0x020014D0`, `0x54` versus `0xAB`). The producer handoff records the private one-slot run exiting 0, six focused tests exiting 0, and its provenance check exiting 0. I audited the command records and test assertions but did not rerun them.

## Evidence boundaries

The asset-backed cases improve evidence over the earlier all-synthetic message batch: four actual strings from this one frozen asset now fit and pass through original ARM and the editable candidate. The nine synthetic edge cases and 176 synthetic copy matrix cases remain separate evidence. The asset rows are supplied as direct pointers; the H1 caller's global TBB lookup, resource binding, runtime object construction and selected row index are not executed. This also says nothing about other locale assets or rows with longer/multiline content.

The candidate still requires valid manager/work pointers, readable input through the bytes it scans, at most 64 bytes in each copied line, and valid non-overlapping forward-copy spans. The original routine does not enforce the candidate's line cap. No title initialization order, rendered text, production integration, Azahar/game runtime, or gameplay scenario was tested. Keep the result as partial offline asset-backed differential evidence, not caller or runtime equivalence.

## Next step

If runtime validation is needed, separately exercise the actual H1 caller and TBB lookup with this frozen asset, then verify initialization and rendered output. Keep the candidate experimental until that caller/runtime evidence is reviewed.
