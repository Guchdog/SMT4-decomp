# H2 logical-input flag refresh audit

## Status

Static follow-up only. No emulator, debugger/RSP, RPC, profile, keyboard, or
mouse interaction was used. This report refines the producer chain for the
logical-query counters consumed by `TitleConfig_Calc`; it does not establish a
physical input mapping or a safe runtime injection point.

Pinned original image: `extracted/exefs/code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Function boundaries and names are from `config/functions.csv` in checkout HEAD
`1f1179b8cdf22c3e4a5343cb8a528fde64f5aaeb`.

Follow-up: the H2 query IDs and their exact table masks/state-word offsets are
listed in the independently checked [logical table audit](h2-logical-input-table-producer-audit.md).
That mapping still does not assign physical controls or establish full state
buffer population, refresh scheduling, or Azahar delivery.

## Recovered path

1. `TitleConfig_Calc` calls `camp_func_002C1830(id, mode)` for its logical
   queries. For mode 0, that helper dispatches to `ui_func_002B902C(id)`; for
   mode 1, it dispatches to `ui_func_002BFFBC(id)` (see
   [the existing input seam contract](h2-input-seam-contract.md)).
2. Both helpers accept IDs below `0x1F` and read a `u32` at
   `0x004E3C58 + 4*id`. In the path where `*(u32*)(0x004650A0+8) & 1` is zero,
   they return one exactly when that counter equals one; otherwise they return
   zero. When that flag bit is set, `ui_func_002BFFBC` returns zero. The
   flag-set path in `ui_func_002B902C` sets the compared `r0` value to zero;
   its unsigned `BLS` threshold branch returns zero for every 32-bit threshold,
   so the subsequent helper-call block appears unreachable. Do not assign
   physical button labels to these IDs from this check.
3. `func_001078D8` refreshes those 31 counters. It obtains an input-state result
   through `func_0011C5EC`, passing `0x004E3C28` as the state buffer, then
   sets the availability dword at `0x004650A4` to one only when that call
   succeeds. It walks 31 eight-byte mapping records at `0x004099C0` alongside
   the counter array at `0x004E3C58`. For a zero first record word, it loads the
   the same fixed state word at `0x004E3C28` only if availability is set,
   then tests it against the record's second-word mask. A matching bit
   increments the counter and a missing bit resets it to zero. If availability
   is clear for a zero-first-word record, the loop skips this counter's
   mask/reset path and leaves the prior counter unchanged. A nonzero first
   record word resets the corresponding counter. The state pointer stays fixed
   through all 31 rows; only the counter and mapping-row pointers advance.
4. `engine_func_0010B578` directly calls `func_001078D8` at `0x0010B57C`.
   The bounded direct ARM `BL`/`BLX` scan of ledgered functions found this one
   caller of `func_001078D8`. That bounded scan did not report a caller of
   `engine_func_0010B578`, but a later image-wide ARM review found the direct
   call at `0x00101B8C` inside `crt_func_00101308`. Actual runtime cadence and
   scheduler registration remain unresolved.

On a successful input refresh, the `counter == 1` check is consistent with a
one-update pulse for a matching input bit: the refresh increments while
matched, and the query stops returning one after the counter advances beyond
one. A zero-first-word record with unavailable input retains its previous
counter, so a prior value of one can persist across that refresh. This is an
instruction-level inference whose observable pulse behavior depends on
successful refreshes and their scheduling relative to Calc, not a complete
contract for all IDs, records, or the alternate input mode. The title's `(4,0)`
and `(3,0)` queries can additionally fall back to IDs `0xD` and `0xC` when
their primary query result is zero.

## What this resolves and what it does not

The prior audit's statement that no producer for the four touch halfwords
`TitleConfigWork+0x1C..+0x22` was found remains unchanged. This report instead
finds the logical-query counter writer and the raw state buffer/mapping table
used on one query path.

Still unresolved:

- `0x004E3C28`'s producer-side semantics, device/source selection, and
  relationship to Azahar/frontend input.
- The meaning of the 31 mapping-record first words and second-word masks,
  including which records apply to H2's logical IDs `(9,1)`, `(4,0)`, `(3,0)`,
  `(0,1)`, and `(1,1)`.
- The callback registration/scheduling path for `engine_func_0010B578`.
- Whether any guest state can be written between input refresh and Calc
  without a race or an overwrite.

Therefore, an RPC write to `0x004E3C58` or `0x004E3C28` is not a deterministic
H2 event and is not approved by this audit. The RPC path also lacks execution
stops, and its pinned UDP listener is wildcard-bound; see
[the Azahar RPC locality review](h2-azahar-rpc-locality-review.md).

## Reproduction commands

Read-only disassembly commands:

```powershell
python tools/split_asm.py --addr 0x002B902C
python tools/split_asm.py --addr 0x002BFFBC
python tools/split_asm.py --addr 0x001078D8
python tools/split_asm.py --addr 0x0010B578
python tools/split_asm.py --addr 0x0011C5EC
```

The literal-reference scan used Capstone over `config/functions.csv` spans in
ARM mode to find PC-relative `ldr` literals for `0x004E3C58`, `0x004E3C28`,
`0x004099C0`, `0x004650A0`, and `0x004E3C48`; the direct-call scan searched
ledgered ARM spans for immediate `BL`/`BLX` targets `0x001078D8`,
`0x0011C5EC`, `0x0011C5E0`, and `0x0011C71C`. These bounded scans do not cover
Thumb functions, computed calls, runtime registrations, or code outside the
ledgered spans.

## Next useful evidence

Resolve the mapping-table rows and the `engine_func_0010B578` registration path
from static callers and data initializers. For real event injection, require a
reviewed CLI/RSP run that observes the update-to-Calc ordering, confirms the
effective process/profile paths, and uses a documented synchronization seam.
Until then, keep the existing offline logical-service controls as mock
contracts only.
