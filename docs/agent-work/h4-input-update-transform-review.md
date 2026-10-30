# Independent review: H4 input update transform

## Recommendation

The new direct-caller path and most of the `0x00108B10` update trace are supported by the pinned ARM listing. Correct two details before relying on the interpretation:

1. In `0x001078D8`, the mapping loop tests each of 31 row masks against the same state word at `0x004E3C28`. The code initializes `r6 = r0 - 0x30 = 0x004E3C28`, then never increments `r6`; it advances the counter pointer `r0` by four and the mapping-row pointers by eight. The producer report's phrase `0x004E3C28 + 4*i` is not supported. This is one fixed 32-bit state value tested against each map mask, not 31 sequential state words.
2. In `0x00108B10`, byte offset `+4` is the first (least-significant, little-endian) byte of the dword at `+4`, not its third byte. It aliases that dword and must be described accordingly.

The fixed state word does not overlap the 31-counter array. The counter range is `[0x004E3C58,0x004E3CD4)`; the separate 8-byte sample/state record starts at `0x004E3CD4`, exactly at the exclusive end. No inspected function writes player position/orientation or establishes movement.

## Pinned identity, caller and ARM bounds

- The reference image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching `config/game_info.json` and the packet. All packet `input_sha256` values matched when checked.
- The `.text` VMA interval is `[0x00100000,0x003FE624)`. The newly found caller and the reviewed callees fall within it. `config/functions.csv` identifies `0x00101308` as `crt_func_00101308` (4,144 bytes), and the target as `0x0010B578` (604 bytes, ledger label `engine_func_0010b578`). Both are ledgered matching code wrappers; labels do not imply scheduler or input semantics.
- At `0x00101B80..0x00101B98`, the listing decodes `svc #0x28`, `ldr r5,[pc,#-0x3f4]`, `strd r0,r1,[r5,#0x20]`, `bl 0x0010B578`, two NOPs, then `bl 0x00103744`. Thus the `0x00101B8C` hit is an actual contextual ARM BL, not merely an aligned data word.
- Direct BLs are confirmed at `0x0010B57C→0x001078D8`, `0x0010B580→0x00108B10`, `0x00108BD0→0x0011C380`, and `0x0011C3C0→0x0012A900`. The byte displacements from `PC=site+8` are respectively `+0x99E4`, `-0x3CAC`, `-0x2A78`, `+0x137A8`, and `+0xE538`. Each site and target is 4-byte aligned, in the pinned `.text` interval, and within ARM B/BL's signed range `[-33,554,432,+33,554,428]`; all are ARM BL instructions with even target addresses. The scan is bounded to aligned ARM BL encodings: embedded data can produce false candidates, and Thumb, BLX/indirect/computed calls, code outside this image, and runtime reachability are not exhaustively covered. The report states these limits appropriately.
- `0x0010B584` is `pop {r4,lr}`, not a return; execution continues at `0x0010B588` within the larger ledger extent. The target report explicitly preserves this distinction. The call order does not prove that the containing CRT routine is a per-frame scheduler.

## Counter loop correction

At `0x001078FC`, the loop counter destination pointer is loaded from the literal `0x004E3C58`; at `0x00107914`, `r6` is set to that pointer minus `0x30`, i.e. `0x004E3C28`. Each row reads its first word at the mapping table (`r1`, 8-byte stride), reads its mask at `r2=r1+4`, and uses `ldrgt ip,[r6]` after the availability check. There is no `add r6,#4` at the loop bottom; only the counter pointer and mapping pointers advance. Therefore the same `word[0x004E3C28]` is tested for every eligible row. A nonzero first mapping word is forced to zero and resets the corresponding counter. For a zero first mapping word, unavailable input skips the mask/reset block and preserves that row's prior counter; available input bit-tests the fixed state word, incrementing on a match and resetting on a miss. The increment is ordinary 32-bit arithmetic and wraps modulo 2^32.

`0x004E3C58 + 31*4 == 0x004E3CD4`, exclusive. Consequently `0x004E3CD4` is adjacent to, not part of, the counter array. This also means the initializer's 0x7C-byte zeroing from `0x004E3C58` ends just before this record.

## `0x004E3CD4` byte/word aliases and update path

`0x00108B10` obtains `r4=0x004E3CD4`. `ldm r4,{r0,r2}` reads dwords at `+0/+4`, and `stm r4+8,{r0,r2}` copies them to `+8/+0xC`. The later `ldrb [r4,#4]` reads the first byte of the dword at `+4`; that value controls the state branches. It is not a standalone allocation or the third byte of that dword. `ldrb +0x10` and `strb +0x11` also address bytes within/adjacent to the dword at `+0x10`; writes to bytes `+0x12/+0x13` alias its upper two byte lanes. Treating these as independent objects would lose the actual overlapping updates.

The described state transitions match the instructions: if byte `+4` is not 1, dword `+0x14` and bytes `+0x12/+0x13` are cleared; byte `+0x10` is cleared only when byte `+4` equals 0. If byte `+4` equals 1, byte `+0x10` becomes 1, byte `+0x12` clears, and dword `+0x14` increments. When byte `+0x13` is nonzero, signed `strle`/`strble` apply to comparison of dword `+0x1C` against the incremented counter. When byte `+0x13` is zero, counter `==1` sets `+0x12`; signed `blt` skips the threshold action only when counter `<` dword `+0x18`; otherwise `+0x13` and `+0x12` set and the counter clears. Preserve these signed conditions for high-bit values.

At `0x00108BD0`, the function passes `r0=sp`, `r1=0x004E3CD4` to `0x0011C380`. That function dereferences the root and its `+4` pointer, calls `0x0012A900` with output `r1`, request `r2=1`, a count pointer in `r3`, and two stack pointers. The subordinate loop copies source halfwords `+0x20/+0x22` and byte `+0x24` to output `+0/+2/+4` with 8-byte destination stride, and retries if the source snapshot changes. It can conditionally clear those same outputs after helper checks. `0x0011C380` returns 1 when the copied count is positive and 0 otherwise; `0x00108B10` ignores that return, rereads byte `+4`, conditionally copies halfwords `+8/+0xA` back to `+0/+2` if the fresh byte is zero, then returns 1 unconditionally.

This proves local state and sampled-record updates at `0x004E3CD4`. It does not identify the ring object's producer/API, physical control, active input, update cadence, or a player-state consumer.

## Scope and next action

The static path does not reach a verified player-work pointer or position/orientation update. The separate H4 runtime trace is neutral input only and does not extend this path to `0x00108B10`, active input, or per-frame cadence. Do not call the repeat-like bytes player movement, physical button state, or a proven input event. The identified caller plus update routine is useful for future trace planning, but actual scheduler identity/reach, source object, consumer, active-input behavior, cadence and movement remain open.

Next: correct the fixed-word counter description and the byte-lane wording in the source report, then an assigned autonomous observation should passively capture `0x00101B8C`, both update call/return sequences, the 32-bit word at `0x004E3C28`, all counters and the aliased fields at `0x004E3CD4` before/after. First establish repeated timing; then correlate an independently verified frontend input event and trace downstream consumers. This review itself used only read-only static disassembly and report/ledger cross-checks—no source, runner, build, test, emulator, save access, or guest-memory write.

## Run-003 follow-up

Rechecked the updated H4 reports against the same pinned image after the coordinator refreshed the packet. `h4-input-update-transform.md` now states that the state pointer remains fixed at `0x004E3C28` while counters advance at `0x004E3C58+4*i`; the producer report makes the same correction. Both now place the 31-counter interval at `[0x004E3C58,0x004E3CD4)` and treat the `0x004E3CD4` record as separate. The byte-lane note now correctly identifies `+4` as lane 0 of the dword at `+4`. These statements match the instructions: `r6` is set once to `r0-0x30`, no loop instruction advances it, and the byte load is `ldrb [r4,#4]` after the dword copies. The `0x00101B8C→0x0010B578` branch, ARM-state/range checks, signed conditional branches, `0x0011C380→0x0012A900` copy route, and absence of a verified player-work update remain as previously reviewed. No further correction is required for this bounded static report.

Run-003 packet input hashes matched. This follow-up performed only local hash and ARM-disassembly inspection; no code, build, tests, emulator, save, or guest-memory changes were made. The packet's source/reference hash remains `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
