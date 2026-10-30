# H1 title/message candidate

## Result

The bounded candidate for message helper `0x0029F10C` and separate forward
copy dependency `0x002C5FF4` is experimental and not integrated. The final
private original-ARM versus linked-C++ Unicorn run passed 9 helper fixtures
and 176 direct copy cases (185/185 total). All three deliberate controls were
detected: the null-mode return mutant, omission of the color store at work
`+0x4CC`, and byte corruption in the copy candidate. No final differential
mismatch or execution fault occurred.

Final report:
`build/agent-work/H1-semantic/h1-title-message-candidate/overnight-20261025-title-message-candidate-v1/run-02/report.json`
(SHA-256 `90bcc2f28a02858abbd12c93f3b6167ccadf0dec7a0565f511605a07310d4d35`).
The candidate ELF SHA-256 is
`05059c43b7a1a55312c3c44556bf8386588005cc34e4e79f0f09b5769b6e041f`.
The candidate source SHA-256 is
`68c91fe472a631d9435daa0596161ddcbea70dba011abcecfe1be8df6422305e`.

The frozen pinned image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The
runner rechecks these executable extents before running:

| Entry | Size | Pinned body SHA-256 |
| --- | ---: | --- |
| `0x0029F10C` | 316 | `9e432ddfb9a774f0665383f3d790f83fb7b79b44121a8e96806a114e37314873` |
| `0x002C5FF4` | 136 | `644501596cdc02773609b59f6b01e737be96c516e4546919af3c259c1b64746e` |
| `0x002BCF58` optimized copy branch | 116 | `d4e075de5405e2393514369688bf643d3d2064f5386b321b2b9f0ee3d511e0fe` |

The helper cases exercise null reset, empty non-null input, ordinary and
64-byte single lines, high-bit bytes, LF at the first byte, two-line copying,
NUL at scan index 127 with both lines within 64 bytes, and 128 readable
non-terminating bytes where the original stops without copying an unfinished
line. The direct copy matrix covers every source and destination alignment
modulo four with lengths `0, 1, 2, 3, 4, 7, 8, 9, 31, 32, 33`. The original
matrix exercises its optimized `0x002BCF58` branch in 28 direct cases; the
message helper reaches it in five of its real copy calls.

The projection compares fault/return sentinel, `r0`, `r4-r11` and SP,
`d8-d15`, FPSCR, all `0x20000` mapped data bytes, the `0x564` work allocation,
caller-owned stack, and copy call arguments/order. The report records the
first mismatch field (null on final run), per-case data/work/stack hashes, and
the three control mismatches.

## Reconstructed behavior and safe domain

`0x0029F10C` resolves the manager work pointer from literal address
`0x0043DA28` plus four and takes `r0=optional input pointer`, `r1=color`. Null
input writes color to `+0x4CC`, clears `+0x550`, sets `+0x554` to `0xFF`, clears
`+0x4CB`, leaves `+0x55C` untouched, and returns `0xFF`. Non-null input also
clears `[+0x4D0,+0x550)`, then scans at most 128 bytes. NUL or LF copies the
preceding bytes to `+0x4D0 + line*0x40`; LF advances to the second line, and the
scan stops after the second line delimiter. The non-null tail clears `+0x55C`,
sets `+0x4CB` to one, and returns one. Copies call the separate editable
`h1_title_message_forward_copy_candidate`; the original differential uses the
real pinned copy body, not a stub.

This C++ candidate deliberately states a narrower safe domain than the
unchecked original: the manager and work pointers are valid, non-null inputs
are readable through the point scanned, and each copied line is no longer than
64 bytes. The original has no line-length guard. A first-line copy above 64
bytes overlaps the nominal second slot. A second-line copy above 64 bytes
overwrites following work fields; above 84 bytes it exceeds the modeled
`0x564`-byte work allocation. Such inputs are not supported as safe C++ object
accesses. The 128-byte scan-cap case supplies readable storage but no
terminator; the original performs no partial final copy.

`0x002C5FF4` is implemented as a separate forward byte loop returning
`destination+length`, with an explicit non-overlap precondition. The copy
matrix validates the original forward operation across alignments and lengths;
overlap/memmove semantics, invalid pointers, null-copy behavior, and MMIO
ordering remain unsupported.

The original candidate packet used only synthetic strings. A separate,
asset-frozen follow-up now adds the four actual H1 help strings from the
verified 880-byte `TitleTable.tbb` described below. This extends input evidence
for those rows but does not execute the H1 caller, title initialization,
renderer, production integration, or game runtime.

The first attempted run (`run-01`) exposed a harness setup error: it treated
`0x0043DA28` as a pointer cell, while pinned code treats it as the manager
structure and loads the work pointer at `+4`. That failed report is preserved
but is not final evidence. `run-02` corrected both candidate and fixture setup,
then passed all cases. No shared runner, production source, emulator, or game
runtime was touched.

## Frozen real-asset validation

The follow-up packet froze the ignored
`build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb` (880 bytes,
SHA-256 `edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`).
Its TBCR header is 32 bytes with two tables; table 0 is TBL1 at file offset
`0x20`, and its 344-byte payload begins at file offset `0x30`. Using the pinned
H1 formula `payload + 0x56*selection + 0x16`, the report derives and maps the
four actual NUL-terminated strings at these offsets:

| Selection | Payload offset | File offset | Text | Length |
| ---: | ---: | ---: | --- | ---: |
| 0 | `0x16` | `0x46` | `Start a new game from the beginning.` | 36 |
| 1 | `0x6C` | `0x9C` | `Load a saved game and continue playing.` | 39 |
| 2 | `0xC2` | `0xF2` | `Configure audio settings.` | 25 |
| 3 | `0x118` | `0x148` | `Download additional content.` | 28 |

Every NUL falls within its `0x56`-byte row, and each string is one line shorter
than the safe 64-byte slot limit. The runner maps the complete asset into its
private data region and passes the string pointer at the derived row address
to the pinned helper and unchanged C++ candidate. All four cases match the
complete defined projection; the combined fresh run passes 13 helper cases
(nine synthetic plus four actual-asset) and the same 176 direct copy cases,
with all three mutation controls detected and no mismatch.

Follow-up report:
`build/agent-work/H1-semantic/h1-title-message-real-asset-validation/overnight-20261025-title-message-real-asset-v1/run-02/report.json`
(SHA-256 `b5d1d1d2495bd0dfe5d29176eaeeb289f42948c7eeb6e4217118d663edaccc8a`).
It records the asset SHA, TBCR/TBL1 offsets, payload-relative and file offsets,
string bytes/lengths, runtime mapping addresses, candidate/object hashes, and
per-case outputs. The candidate source is unchanged at SHA-256
`68c91fe472a631d9435daa0596161ddcbea70dba011abcecfe1be8df6422305e`; the
linked ELF remains `05059c43b7a1a55312c3c44556bf8386588005cc34e4e79f0f09b5769b6e041f`.

The run used one compiler slot and exited 0:

```powershell
python tools/h1_title_message_experiment.py --output build/agent-work/H1-semantic/h1-title-message-real-asset-validation/overnight-20261025-title-message-real-asset-v1/run-02
```

The focused module ran six tests and exited 0:

```powershell
python -m unittest tests.test_h1_title_message_experiment -v
```

These are direct helper calls over mapped asset bytes; they do not execute the
TBB lookup or title caller, and do not prove runtime object construction,
initialization ordering, rendering, or behavior for other localized assets.

## Commands

```powershell
python tools/h1_title_message_experiment.py --output build/agent-work/H1-semantic/h1-title-message-candidate/overnight-20261025-title-message-candidate-v1/run-02
```

Exit 0: `PASS 185/185; controls 3/3`.

```powershell
python -m unittest tests.test_h1_title_message_experiment -v
```

Exit 0: five focused tests passed.
