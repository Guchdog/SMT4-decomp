# H1-A title input-binding audit (static)

Scope: identify what the title's logical navigation trigger IDs reveal about
3DS input, trace the relevant helpers and data, and define a safe Azahar probe.
The binary chain is statically audited and a navigation-only probe was then
performed in Azahar. No menu option was confirmed, no save/option was changed,
no source was changed, and no function/test counts are affected.

## Source identity and direct observations

- The analyzed image is `extracted/exefs/code.bin`, SHA-256
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
  `config/game_info.json`.
- `0x004099C0` is a 31-row, 8-byte-per-row mask table in the image's read-only
  data. Its file offset is `0x003099C0` (RODATA base `0x003FF000`, file base
  `0x002FF000`). The relevant rows, read as two little-endian 32-bit words,
  are:

  | Logical ID | First word | Second word |
  | --- | ---: | ---: |
  | `5` | `0x00000000` | `0x00000040` |
  | `6` | `0x00000000` | `0x00000080` |
  | `0xE` | `0x00000000` | `0x40000000` |
  | `0xF` | `0x00000000` | `0x80000000` |

- In the title callback, calls to `UiInput_Trigger` at `0x001E9D4C`,
  `0x001E9D60`, `0x001E9D7C`, and `0x001E9D90` pass IDs `5`, `0xE`, `6`, and
  `0xF`, respectively. IDs `5`/`0xE` feed the previous/decrement path; IDs
  `6`/`0xF` feed the next/increment path. Each pair is short-circuited, so the
  alias is queried only when the primary ID returns false.
- `UiInput_Trigger` begins at `0x002B902C`. It rejects IDs `>= 0x1F`. It reads
  the selector bit at `0x004650A8`; with bit 0 clear it indexes the derived
  logical-state array at `0x004E3C58` and tests for value `1`. With bit 0 set,
  it takes the alternate threshold/mask path using fields at `0x004650AC` and
  `0x004650B0` (the image contains `15` and `4` there).
- `UiInput_Trigger2` begins at `0x002BFFBC`. It also rejects IDs `>= 0x1F`,
  indexes the same `0x004099C0` mask rows, and checks the second row word against
  a selected runtime value reached through `0x004E3C28` or `0x004E3C48` (chosen
  by the selector at `0x004650A8`).
- `0x001078D8` walks the 31 mask rows at `0x004099C0` and writes derived states
  beginning at BSS address `0x004E3C58`. Before that loop it calls
  `0x0011C5EC` with `r0 = [0x004650A0]` and `r1 = 0x004E3C28`; this call's
  complete semantic role is not established here. `0x004E3C28`, `0x004E3C48`,
  and `0x004E3C58` are BSS/runtime addresses, not initialized mask constants
  available as static physical bindings.

## Interpretation and limits

**Direct binary evidence:** the exact row masks above, their use by the two
helpers, their helper addresses, and the title caller's logical IDs and branch
directions.

**Conventional 3DS HID interpretation (inference):** masks `0x40` and `0x80`
align with D-pad Up and Down; masks `0x40000000` and `0x80000000` align with
Circle Pad Up and Down. This explains why each logical direction has a primary
and an alias. The mask values are directly observed; the human-readable
control names rely on the conventional 3DS HID bit assignment, not a runtime
capture from this game's Azahar configuration.

## Azahar navigation-only observation

Azahar 2126.2 was started with the user's decrypted CCI. The title screen began
with “Load Game” highlighted (index 1). In the current keyboard profile at
`%APPDATA%/Azahar/config/qt-config.ini`, the arrow keys are bound to Circle Pad
and T/G are bound to D-pad. The UI responded as follows, with one tap per step:

| Input | Selection before → after | Visible help line |
| --- | --- | --- |
| Arrow Up | Load Game (1) → New Game (0) | “Start a new game from the beginning.” |
| Arrow Down | New Game (0) → Load Game (1) | “Load a saved game and continue playing.” |
| Arrow Down | Load Game (1) → Audio Settings (2) | “Configure audio settings.” |
| T (configured D-pad Up) | Audio Settings (2) → Load Game (1) | “Load a saved game and continue playing.” |
| G (configured D-pad Down) | Load Game (1) → Audio Settings (2) | “Configure audio settings.” |

No option was confirmed; execution stayed at the title menu and Azahar was
closed after the probe. This confirms the tested keyboard bindings and visible
selection/help update for this CCI/profile. It does **not** prove physical
controller mappings, isolate which logical alias returned true inside the
short-circuit pair, or characterize held-input/repeat timing.

**Still unknown:** whether a physical host controller emits these bits as
expected; whether analog deadzone, key repeat, held-input filtering, or
simultaneous inputs change behavior; and whether alternate selector state
changes which source the helpers consult. Resolving the exact logical alias
requires a debugger trace at `0x002B902C` under isolated inputs.

## Probe procedure (already performed for keyboard profile)

1. Start at the title screen and record the highlighted row. The documented
   normal initial selection is index 1, “Load Game.” If needed, restore that
   selection using navigation only; never confirm it.
2. From index 1, press D-pad Up once and record the highlight/help line;
   expected result is index 0, “New Game.” Do not confirm.
3. Press D-pad Down once to restore index 1, then press it once more; expected
   result is index 2, “Audio Settings.” Record each step separately.
4. Restore index 1 using navigation only. Repeat the same isolated sequence
   with Circle Pad Up and Circle Pad Down, recording each press separately and
   holding no other input.

This tests the safe navigation effect and distinguishes the configured
keyboard control families without entering a route. Never confirm New Game,
Load Game, or Add-On Content, and do not modify options or saves. A UI-only
observation proves the aggregate direction response, not which short-circuited
logical ID returned true; resolving that distinction requires an emulator
debugger trace of calls/returns at `0x002B902C` under isolated inputs.
