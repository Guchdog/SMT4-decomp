# H2 input-manager touch-state producer audit

Independent review confirmed the producer and record-layout findings and
identified four additional state-byte write sites. A final review confirmed
the complete write inventory and found one accumulator-offset typo, corrected
below; see [the producer review](h2-input-manager-touch-state-producer-review.md)
and [the final review](h2-input-manager-touch-state-final-review.md).

## Finding

The pinned image does contain the producer for the fields read by
`UiTouch_GetRegionTouchState` (`0x0029D8FC`). `IfTouch_Init` (`0x0010299C`)
allocates a `0x680`-byte manager, registers a task named `TOUCH CALC` with an
update callback at internal entry `0x00107CCC`, and initializes
`manager+0x64E` to signed `-1`. The callback body writes the active index to
`manager+0x64E` on successful hit-test branches and writes the event byte at
`manager+0x08` with values selected by its update paths. Therefore the earlier
statement that the active-panel/raw-byte producers were not found is superseded.

This resolves the static producer question, but not the complete touch contract.
The callback's raw state byte remains opaque; the exact coordinate/region
meaning of the helper arguments and relationship between its active index and
the three handles registered by H2 are not established here. The callback
schedule is registered by `IfTouch_Init`, but its actual runtime cadence and
ordering relative to `TitleConfig_Calc` have not been observed. No physical
input mapping or Azahar delivery is claimed.

## Pinned evidence

Image: `extracted/exefs/code.bin`, SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Function spans/names: `config/functions.csv` at checkout HEAD
`1f1179b8cdf22c3e4a5343cb8a528fde64f5aaeb`.

`IfTouch_Init` disassembly shows:

- Allocator call at `0x001029E4` with size `0x680`; its result is published to
  `g_IfTouchGlobal+4` (`0x0043DCB4`).
- Task factory call at `0x00102A20`, named `TOUCH CALC`, with callback
  `0x00107CCC` passed on the stack and `0x0010A28C` as the other callback
  pointer (`0x001029F8..0x00102A20`). This directly associates the internal
  entry with the manager's scheduled update task.
- The allocator result is passed through the helper at `0x001029F4` with size
  `0x680`. This report does not rely on that helper's clearing semantics to
  establish the active-index initialization below.
- At `0x00102A38`, `strh -1,[manager+0x64E]` initializes the signed active
  index; `0x00102A3C` writes 10 to `manager+0x64A`; `0x00102A40` writes zero to
  `manager+0x64C`.

At internal callback entry `0x00107CCC`, the image loads the same manager from
`g_IfTouchGlobal+4`, reads the state byte at `+0x08`, and dispatches the update
state. Relevant writes include:

- `0x00107D88`: stores a nonzero path value in `manager+0x08`, then
  `0x00107D8C` stores loop index `r5` to `manager+0x64E` when the called
  `camp_func_002C0144` hit-test returns nonzero.
- `0x00107EE4` and `0x00107EE8`: on another hit-test path, conditionally store
  the path state byte and loop index to those same fields.
- `0x00107E4C`: stores `r8` when the computed-distance result at `0x00107E44`
  is greater than 8.
- `0x00107E68`: stores 6 only when `camp_func_002C01B8(0,3)` returns nonzero.
  `0x00107E94` clears the byte when the helper at `0x00107E8C` returns zero;
  `0x00107F04` unconditionally clears it on its dispatch path.
- `0x00107F5C`: conditionally clears the byte when the signed difference
  tested at `0x00107F58` is below its negative boundary.
- `0x00107FE8` and `0x0010800C`: conditionally clear the byte when the
  movement accumulator at `manager+0x674` crosses zero in either direction.
- The update reads the region-count-like halfword at `+0x64A` and a second
  halfword at `+0x64C`; it calls `camp_func_002C0144` while scanning indexed
  records. The names and physical meanings of these values are not inferred.

The getter at `0x0029D8FC` loads `manager+0x64E`, compares it as signed `s16`
with its argument, and returns the byte at `manager+0x08` only on equality. In
combination with `IfTouch_Init`, this proves that `-1` is the initialized
no-active-index value and can match the four H2 fields initialized to `-1`.
It does not prove that those H2 fields are intended handles or that any state
byte denotes a specific user action.

## Corrected registration layout

The earlier `h2-input-handle-producer-audit.md` described registration records
as residing at `manager+0x600+8*index`. Re-reading the pinned instructions
shows that this address was wrong. In `camp_func_002B88C4` (`0x002B88C4`),
`manager+0x600+0x4A` is read as the current registration index/count, but the
record stores use `manager + 8*index + {0xA,0xC,0xE,0x10}`. Initialization
starts this index at 10, so successful H2 registrations return indices 10,
11, and 12 and store records at those indexed locations. The helper increments
the count at `manager+0x64A`; it does not write `TitleConfigWork`.

H2's three returned registration values are stored at `TitleConfigWork+0x14`,
`+0x16`, and `+0x18`. The four values Calc reads at `+0x1C,+0x1E,+0x20,+0x22`
remain initialized to `-1` in the observed code. The manager producer finding
does not turn those values into registration handles or justify changing them.

## Evidence boundary and next observation

All conclusions above are static instruction/caller facts. The task registration
proves intended callback linkage, not actual runtime scheduling. A future
read-only CLI observer can now inspect a known producer boundary: after
`IfTouch_Init`, record `manager+0x08`, `+0x64A`, `+0x64C`, and `+0x64E`; at
`0x00107D88/0x00107D8C`, `0x00107EE4/0x00107EE8`, the additional state-byte
sites `0x00107E4C`, `0x00107E68`, `0x00107E94`, `0x00107F04`,
`0x00107F5C`, `0x00107FE8`, and `0x0010800C`, and each
`UiTouch_GetRegionTouchState` call, capture the same fields, loop index, and
hit-test result. Also record the three H2 registration returns and their record
addresses. This should establish event cadence and whether the H2 polled
sentinels are meaningful in the actual title flow. Do not inject state into
these fields based on this static report.

No build, tests, emulator, debugger/RSP/RPC, profile or game-state write,
network probe, firewall change, keyboard, or mouse was used.

## Reproduction commands

```powershell
python tools/split_asm.py --addr 0x0010299C
python tools/split_asm.py --addr 0x0010797C
python tools/split_asm.py --addr 0x0029D8FC
python tools/split_asm.py --addr 0x002B88C4
```

The callback entry `0x00107CCC` is inside the ledger span beginning at
`0x0010797C`; its registration as a task callback is visible directly in
`IfTouch_Init`. Direct disassembly establishes the manager field writes and
registration-record arithmetic described above. It is not a whole-program
alias proof; computed writes and runtime callbacks outside the observed task
remain outside scope.
