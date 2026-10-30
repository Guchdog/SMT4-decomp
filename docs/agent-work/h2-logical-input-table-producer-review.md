# Coordinator review: H2 logical input table and producer audit

## Recommendation

**Accept within the stated static scope.** Independent inspection confirms the
H2 query IDs' table rows, masks, state-word addresses, mode paths, and Calc
fallback IDs. The refresh and immediate state-source path match the pinned
instructions. The bounded negative caller search is reproducible for the
specified direct ARM calls and aligned absolute words; it does not rule out
runtime registration or computed scheduling.

## Verified table and query paths

Pinned image: `extracted/exefs/code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

I read the 31-row table at `0x004099C0` directly and verified these rows:

| ID | Gate | Mask | Tested state word |
|---:|---:|---:|---:|
| 9 | `0` | `0x400` | `0x004E3C4C` |
| 4 | `0` | `0x20` | `0x004E3C38` |
| 3 | `0` | `0x10` | `0x004E3C34` |
| 0 | `0` | `0x1` | `0x004E3C28` |
| 1 | `0` | `0x2` | `0x004E3C2C` |
| `0xD` | `0` | `0x20000000` | `0x004E3C5C` |
| `0xC` | `0` | `0x10000000` | `0x004E3C58` |

`func_001078D8` loads the state buffer at `0x004E3C28`, the counter array at
`0x004E3C58`, and the records at `0x004099C0`. Its failure path leaves a
counter unchanged for a zero-gate row when availability is false. Successful
state retrieval tests the row mask and increments on a match or clears on a
miss. `camp_func_002C1830` dispatches mode 0 to `0x002B902C`, mode 1 to
`0x002BFFBC`, and mode 2 to `0x002C17D4`; the Calc calls and fallback IDs in
the report match the disassembly. These masks are internal state bits; no
physical controller names follow from them.

The immediate producer path at `0x0011C5EC` checks an internal mode/object,
requests a single record into the supplied buffer through `0x0012A758`, and
updates its first record. This does not establish the provenance of all 31
indexed state words, hardware mapping, or a safe memory-write seam.

## Bounded scheduler-search result

I independently reran a Capstone ARM scan over the ledgered spans in
`config/functions.csv`, using file offset `VMA - 0x00100000`, and searched
aligned words in the pinned `code.bin`. Results:

- `0x0010B57C` is the only scanned direct caller of `func_001078D8`.
- This scan missed direct caller `0x00101B8C -> engine_func_0010B578`, later found by the H4 image-wide ARM review inside `crt_func_00101308`; its original negative result is superseded.
- No aligned absolute word equal to `0x001078D8`, `0x0010B578`, or
  `0x0011C5EC` was found.

The later H4 review supersedes the negative direct-caller result for
`engine_func_0010B578`. The original scan still records its bounded inputs, but
does not establish absence of direct callers or runtime scheduling. Thumb
functions, computed or relative references, runtime task registrations,
unledgered spans, and data outside the pinned image remain uncovered.

## Evidence and remaining limits

Commands independently used:

```powershell
python tools/split_asm.py --addr 0x001078D8
python tools/split_asm.py --addr 0x002C1830
```

I also read `code.bin` at `0x004099C0 + 8*ID` and reran the direct-call/aligned
word scan over `config/functions.csv` spans. No build, test, emulator,
debugger/RSP/RPC, network, OS input, profile/game mutation, or firewall action
was performed.

Physical control meanings, state refresh cadence/order, complete state-buffer
population, Azahar delivery, and deterministic guest input remain unresolved.
Keep the table as a logical bit contract and do not seed the guest state buffer
or counter array based on this report.
