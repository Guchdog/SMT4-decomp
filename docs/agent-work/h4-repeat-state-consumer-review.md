# H4 repeat-state consumer: independent static review

## Result

The bounded scan and ARM inspection support the report’s central separation: 31 dword counters occupy `[0x004E3C58,0x004E3CD4)`, while the distinct 0x20-byte state block starts exactly at `0x004E3CD4` and extends through `+0x1F`. In the stated aligned-word scan over `[0x00100000,0x003FE624)`, I independently found only the three reported in-range absolute words, all `0x004E3CD4`, at `0x00108BFC`, `0x0010A744`, and `0x002C0288`. This is bounded absolute-reference evidence; it does not cover computed/indirect pointers, Thumb code, data outside the interval, or dynamic execution.

The initialization and active update are distinguishable. `0x0010A70C` clears dwords `+0..+0x14`, sets `+0x18=15`, `+0x1C=4`, and returns 1; `0x0010DB78` calls it after two preceding calls. The active writer `0x00108B10` snapshots dwords `+0/+4` into `+8/+0xC`, copies current byte `+0x10` to `+0x11`, performs the described repeat/counter state updates, calls `0x0011C380` with destination `0x004E3CD4`, then conditionally restores halfwords from `+8/+0xA` when its freshly reread byte `+4` is zero. Byte `+4` aliases the least-significant byte of dword `+4`; byte fields `+0x10..+0x13` likewise overlap dword storage. `0x001078D8` is the separate 31-row counter updater: it advances the counter/table pointers but keeps its state-word pointer at `0x004E3C28`. The reset path is not evidence that it is the active producer.

## Reader ABI and call behavior

Pinned `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; all 16 declared packet input hashes matched. `0x002C01B8` is ARM code. It reads unsigned halfwords at state `+0/+2`, current byte `+0x10`, prior byte `+0x11`, and reads `+0x12` only for mode 2. Its mode predicates match the recon report:

| `r2` | Success predicate |
|---|---|
| 0 | current `+0x10 == 1` |
| 1 | current `+0x10 == 1` and prior `+0x11 == 0` |
| 2 | current `+0x10 == 1` and `+0x12 == 1` |
| 3 | current `+0x10 == 0` and prior `+0x11 == 1` |
| other | failure |

On success it independently null-checks `r0` and `r1` and stores the corresponding zero-extended halfword with a 32-bit `str`; nulling one output does not suppress the other or change the success result. Failure/unsupported mode reaches the return without output stores, so both caller buffers remain untouched. The function returns 0/1 in `r0` and preserves `r4-r6`. It does not validate the meaning or provenance of the returned values.

`0x002C0144` loads its fifth argument (reader mode) from the caller stack, passes two local stack slots as output pointers, and only applies its bounds predicate after a successful read. The comparisons express inclusive bounds for ordinary non-overflowing arguments; the sum bounds are computed in 32-bit registers and comparisons are signed, so this is not an unqualified mathematical rectangle for arbitrary extreme inputs. Its return is a boolean. This qualification does not alter the reported ABI-level description.

Independent ARM direct-call enumeration reproduced the reported sites: nine BLs into `0x002C01B8`, nineteen into `0x002C0144`, one to the initializer `0x0010A70C`, and one to active updater `0x00108B10` inside the declared text range. At the noted `0x0010797C` callers, the visible call setup supports modes 1, 0, 3 and 0 respectively; at `0x00107E5C`, `r0=r1=0`, mode 3 and the returned predicate controls a local state-byte write without either output store. The raw instructions at `0x001C185C` and `0x00317760` show mode 0 with stack output slots; the `0x00317464` site uses mode 1 with work-area outputs; `0x00317684` uses mode 3 with stack slots. These usages support caller/output-slot descriptions only, not a physical input mapping or gameplay identity.

The two short ARM wrappers at `0x003C3034` and `0x003C303C` set `r2=1` and `r2=3` before tail-branching to the reader. The inspected functions `0x0039B58C` and `0x0039D758` contain direct calls into those wrappers (`0x0039B69C`, `0x0039D7FC`) and `0x0039B58C` also calls the mode-3 wrapper at `0x0039B5EC`. This makes them a justified next bounded static observation. Their actual scene ownership and dynamic reach remain unresolved; no validated player-work, position/orientation, movement, H4 interaction or transition path is established by these call chains.

## Scope and next step

The report’s conclusions and limitations are appropriately bounded. The direct sites include UI/window-associated routines and the counter/state local code, but source names, `matching` ledger status and static calls do not demonstrate field execution or semantics. The scan is not exhaustive for indirect/computed/Thumb references or references beyond its stated interval, and no runtime or player-state correlation was made. Continue with the proposed static context/consumer inspection around `0x0039B58C` and `0x0039D758`, following only directly evidenced state/object writes; any gameplay attribution still needs a separately authorized, validated runtime binding. No build, tests, emulator, save access, or guest writes were performed in this review.

## Read-only checks

- Verified declared packet input SHA-256 values: 16 checked, zero mismatches.
- `python tools/split_asm.py --addr 0x002C01B8`, `--addr 0x002C0144`, `--addr 0x00108B10`, `--addr 0x0010A70C`, `--addr 0x0039B58C`, `--addr 0x0039D758`, `--addr 0x003C3034`, `--addr 0x0010DB6C`: all completed with exit 0 (the split-asm function printer does not emit output for every interior address).
- Recomputed the declared aligned absolute-word and ARM direct-BL scans from pinned `code.bin`; output matches the reference list and caller sites stated above.
- Decoded narrow caller windows with Capstone at the listed mode/output sites and updater loop; exit 0.
- No source, runner, board, build, test, emulator, save, or guest-memory changes.
