# H2 logical input table and producer audit

## Result and scope

Static audit of the pinned ARM image only. The logical query IDs and their table
entries are recoverable, and the counter refresh path is visible. The underlying
state source is an internal input object/snapshot path, but its physical mapping
and frontend provenance are not established. A direct refresh call exists inside
`engine_func_0010B578`, and a later H4 image-wide ARM review found a direct call
to that wrapper at `0x00101B8C` inside `crt_func_00101308`. Runtime scheduling
and cadence remain unproven.

Pinned `extracted/exefs/code.bin` SHA-256:
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Function boundaries come from `config/functions.csv` at task base commit
`1f1179b8cdf22c3e4a5343cb8a528fde64f5aaeb`.

## Query IDs and pinned table rows

`func_001078D8` walks 31 eight-byte records beginning at `0x004099C0`. For ID
`i`, the record is `{u32 gate = *(0x004099C0 + 8*i), u32 mask = *(... + 4)}`;
the refresh loop tests each row mask against the same raw state word at
`0x004E3C28` (its state pointer does not advance), and the counter is at
`0x004E3C58 + 4*i`. The requested pinned records are:

| Query ID | Table row | First word / gate | Mask | State word tested | Calc mode path |
|---:|---:|---:|---:|---:|---|
| `9` | `0x00409A08` | `0` | `0x00000400` | `0x004E3C28` | `(9,1)` → `ui_func_002BFFBC(9)` |
| `4` | `0x004099E0` | `0` | `0x00000020` | `0x004E3C28` | `(4,0)` → `ui_func_002B902C(4)`; if false, mode-0 fallback ID `0xD` |
| `3` | `0x004099D8` | `0` | `0x00000010` | `0x004E3C28` | `(3,0)` → `ui_func_002B902C(3)`; if false, mode-0 fallback ID `0xC` |
| `0` | `0x004099C0` | `0` | `0x00000001` | `0x004E3C28` | `(0,1)` → `ui_func_002BFFBC(0)` |
| `1` | `0x004099C8` | `0` | `0x00000002` | `0x004E3C28` | `(1,1)` → `ui_func_002BFFBC(1)` |
| `0xD` | `0x00409A28` | `0` | `0x20000000` | `0x004E3C28` | fallback from `(4,0)`, through `ui_func_002B902C(0xD)` |
| `0xC` | `0x00409A20` | `0` | `0x10000000` | `0x004E3C28` | fallback from `(3,0)`, through `ui_func_002B902C(0xC)` |

The two query helpers reject unsigned IDs `>=0x1F`. On their ordinary
flag-clear path, they read the corresponding counter and return one only when it
equals exactly one. Their mode paths differ: mode 1 uses
`ui_func_002BFFBC`; mode 0 uses `ui_func_002B902C`. A set bit at
`*(u32*)(0x004650A0+8)` makes the former return zero; for the latter the
emitted unsigned `BLS` branch also returns zero for every 32-bit threshold. The
fallback IDs are logical helper calls; this table does not establish physical
button names.

All seven selected records have a zero first word. In the refresh loop, that
allows the mask test when the input-state availability flag at `0x004650A4` is
set. A matching state bit increments the ID's counter; a valid state word with
no matching bit resets it to zero. If state retrieval fails, zero-gated rows
leave their prior counter unchanged. A nonzero table first word takes the reset
path. Consequently, `counter == 1` can act as a one-successful-refresh pulse,
but a retained value can survive a failed refresh; actual query timing depends
on scheduling that was not recovered.

## Producer/source path

At `0x001078D8`, `func_001078D8` loads the input root pointer from
`0x004650A0`, passes it with output buffer `0x004E3C28` to
`func_0011C5EC` (`0x0011C5EC`), and writes success/failure to
`0x004650A4`. It then applies the 31 table records described above. These
instructions establish a shared state buffer, mapping table, and query-counter
array; they do not give the entries physical control meanings.

`func_0011C5EC` checks the byte at `0x0047388B` through
`func_00138F34`; value `4` exits with failure. Otherwise it clamps fields in
the root's `+0x0C` subobject via `func_001285C4`, obtains an object pointer from
`*(u32*)(root+4)`, and calls `func_0012A758` with that object, the supplied
buffer, and a requested count of one. A nonpositive result returns failure. A
positive result then updates the first output record: it clears bit `0x2000`
from its first word, derives change masks into `+4` and `+8`, and can clear the
record fields after calls to `0x002BB978` and `0x002BC9C8`. This supports an
internal object/snapshot as the immediate source. The meanings of the mode byte,
object fields, copied record, remaining words consumed by the 31-row loop, and
their device/frontend provenance are unresolved. In particular, the visible
single-record copy is not evidence that all 31 state words receive fresh values
on every successful call.

## Caller and scheduling search

The direct ARM call chain found in ledgered spans is:

| Call site | Caller | Target | Static conclusion |
|---:|---|---|---|
| `0x001078E8` | `func_001078D8` | `func_0011C5EC` | refresh obtains state through this helper |
| `0x00101B8C` | `crt_func_00101308` | `engine_func_0010B578` | later image-wide ARM review found this direct wrapper caller |
| `0x0010B57C` | `engine_func_0010B578` | `func_001078D8` | wrapper directly invokes the counter refresh |
| `0x0010B580` | `engine_func_0010B578` | `func_00108B10` | wrapper continues with another input-related update |

A later image-wide ARM review found the direct caller `0x00101B8C` to
`engine_func_0010B578` inside `crt_func_00101308`; the older bounded scan missed
this site. The refresh is statically linked to a wrapper, but that call alone
does not establish the wrapper's task/callback registration or execution
cadence. Thumb spans, computed or relative references, runtime registration,
data outside the pinned code image, and unledgered code are not exhausted by
these scans. The separate touch-manager callback audit does not establish
linkage to this logical-state refresh.

## Limits and next evidence

No physical controls are named; no Azahar input delivery, runtime ordering, or
safe guest-write seam is established. Do not treat writes to `0x004E3C28`,
`0x004E3C58`, or the table as a validated event-injection method. The static
scan establishes neither refresh frequency nor race-free ordering relative to
`TitleConfig_Calc`.

Useful read-only reproduction commands:

```powershell
python tools/split_asm.py --addr 0x001078D8
python tools/split_asm.py --addr 0x0011C5EC
python tools/split_asm.py --addr 0x0010B578
python tools/split_asm.py --addr 0x00108B10
python tools/split_asm.py --addr 0x001285C4
python tools/split_asm.py --addr 0x00128C2C
python tools/split_asm.py --addr 0x0012A758
python tools/split_asm.py --addr 0x00138F34
```

No build, tests, emulator, debugger/RSP/RPC, network, keyboard/mouse, or profile
or game-state mutation was performed.
