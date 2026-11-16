# Contract & H2 Relevance Recon: `0x002B8B78` (`script_vm_func_002b8b78` / misnamed `Sound_PlaySE`)

## Recommendation

**Defer** H2 production conversion/validation for `0x002B8B78`. It is **not** a sound-effect playback primitive (`Sound_PlaySE` in `src/camp/camp_cec.cpp`, `src/camp/title_flow.cpp`, `src/ui/status_down.cpp` and `ScriptVm_SetMessageId` in `src/ui/ui_runtime2.cpp:94` are speculative misnomers); it is a 6-slot UI/profile transition switcher on manager root `0x0043DA28` with 5 nested callees, and it is not on the critical `TitleConfig` readiness/audio-settings path (`0` direct `BL`s in `0x00221168`, and only reached by `0x00286928` at `0x00286B80` when `row in {7, 8, 9} && 0x0028DF70(0) == 5`).

## 1. Pinned Identity & Disassembly (`0x002B8B78`, 340 bytes)

All 12 `input_sha256` pins in `task.json` matched (`extracted/exefs/code.bin` `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`). `config/functions.csv:5532` classifies `0x002b8b78` as `non_matching` (`script_vm_func_002b8b78` in `src/engine/leaf_batch32_c.cpp:542-599`).

Disassembly of `0x002B8B78..0x002B8CCC`:
- **Prologue & ABI**: `push {r4, r5, r6, r7, r8, sb, lr}; sub sp, sp, #0xc`. Takes `u32 request` in `r0`, returns `u32` in `r0`, preserves `r4-r11` and `SP`, no VFP instructions.
- **Manager root & early exits**:
  - `sb = 0x0043DA28` (`0x002B8CC4`), `object = *(u32*)(sb + 4)`, `latch = (s32*)(sb + 0x10)`.
  - If `object[0x4C9] == request`, returns `object[0x4C9]` immediately.
  - If `*latch < 0`, scans `slot = 0..5` for `object[0x4B8 + slot] != 0`; on first non-zero, writes `*latch = (s32)request` and returns `slot`.
  - Otherwise sets `*latch = -1` and calls `0x002B85BC(request)`.
- **Profile lookup & 6-slot update**:
  - Calls `r6 = 0x002AEA28(object[0x4C9])` and `r8 = 0x002AEA28(request)`. If `r6 == 0 || r8 == 0`, returns `r8` (`r0`).
  - Stores `object[0x4CA] = object[0x4C9]` and `object[0x4C9] = (u8)request`.
  - Loads 8 bytes from `0x00402548 + 8` (`[5, 6, 4, 3, 2, 1, 0, 0]`) onto `SP[0..7]` and loops `slot = 0..5`: reads `u16 val = ((u16*)r8)[slot]`; if `val != 0`, calls `0x002B8794(slot, priorities[slot], val & 0xFF, 0)`, else calls `0x002B8794(slot, 0x12, 0x51, 0)`.
- **Tail dispatch**:
  - If `*(u8*)(r6 + 0x0C) == 0`: sets `current_object[0x4C5] = 1` (reloading `*(sb + 4)`) and returns `0x0013851C(1)`.
  - Else if `*(u8*)(r8 + 0x0C) != 0`: sets `current_object[0x4C5] = 0` and returns `0x0013851C(0)`.
  - Else: sets `current_object[0x4C5] = 1` and returns `0x002AE874(1)`.

## 2. Direct Callers vs. Speculative H2 Relationship

- **223** direct ARM `BL` sites exist in `extracted/exefs/code.bin`.
- `0x00286B80` (inside `0x00286928`) calls `0x002B8B78(0xDC)` only on `incoming_r2 == 0 && object[8] == 0 && !(query_a && query_b) && row in {7,8,9} && 0x0028DF70(0) == 5`.
- `0x00221168` (`TitleConfig` callback) has **0** direct `BL`s to `0x002B8B78`.
- `Sound_PlaySE` in `camp_cec.cpp`, `title_flow.cpp`, and `status_down.cpp` is a misnomer; `leaf_batch32_c.cpp:542-599` already expresses the 6-slot switcher semantics, and `0x002B8B78`'s 5 callees (`0x002B85BC`, `0x002AEA28`, `0x002B8794`, `0x0013851C`, `0x002AE874`) are outside H2's immediate audio-settings blocker.

## 3. Bounded C++ Scope (If Later Validated)

- Keep `script_vm_func_002b8b78(u32 request)` (`leaf_batch32_c.cpp:542-599`) with its 5 callees stubbed/pinned at their original addresses; test early match, `*latch < 0` active/inactive slots, `*latch >= 0`, null `old`/`new` profile, 6-slot `0x002B8794` loop (`value != 0` vs `0` fallback `(0x12, 0x51)`), and all 3 tail branches (`old[0x0C] == 0`, `new[0x0C] != 0`, else).
- Fault domain: requires valid mapped `0x0043DA28`, `object`, and non-null profile pointers when `0x002AEA28` returns non-zero.
