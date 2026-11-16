# `0x002B8B78` (`script_vm_func_002b8b78` / misnamed `Sound_PlaySE`) — independent contract review

**Verdict: APPROVE the 340-byte ARM contract in `docs/agent-work/h2-sound-playse-contract-002b8b78.md` WITH CORRECTION to H2 caller reachability: `0x002F4CA0` (`titleConfig_func_002f4ca0`) also directly calls `0x002B8B78(0x99)` at `0x002F4DF0`.**

## 1. Frozen pins & independent 340-byte ARM verification

- Read-only static review (`compiler_slots: 0`); no source, ledger, README, milestone, or board edits, and no builds or emulator runs.
- Recomputed all `15/15` `input_sha256` entries in `build/agent-work/H2-semantic/h2-sound-playse-contract-review-002b8b78/run-001/task.json`: `15/15` matched (`reference_sha256` = `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Independently disassembled `0x002B8B78..0x002B8CCB` (340 bytes) from `extracted/exefs/code.bin` (literals at `0x002B8CC4`: `0x0043DA28`, `0x00402548`; table at `0x00402550`: `[5, 6, 4, 3, 2, 1, 0, 0]`):
  - **ABI:** `u32 request` in `r0`, returns `u32` in `r0`, saves `{r4..r8, sb, lr}`, `sub sp, sp, #0xc`, preserves `r4..r11` and `SP`, no VFP.
  - **Early exits:** `object = *(u32*)(0x0043DA2C)`, `latch = (s32*)(0x0043DA38)`. If `object[0x4C9] == request`, returns `object[0x4C9]`. If `*latch < 0`, loops `slot = 0..5` checking `object[0x4B8 + slot] != 0`; on first nonzero, stores `*latch = (s32)request` and returns `slot`.
  - **6-slot update & tail dispatch:** Sets `*latch = -1`, calls `0x002B85BC(request)`, looks up `r6 = 0x002AEA28(object[0x4C9])` and `r8 = 0x002AEA28(request)` (returns `r8` if either is `0`), stores `object[0x4CA] = object[0x4C9]` and `object[0x4C9] = (u8)request`, loops `slot = 0..5` calling `0x002B8794(slot, val != 0 ? priorities[slot] : 0x12, val != 0 ? (val & 0xFF) : 0x51, 0)`, then sets `current_object[0x4C5]` and tail-calls `0x0013851C(1)` (`r6[0x0C] == 0`), `0x0013851C(0)` (`r8[0x0C] != 0`), or `0x002AE874(1)` (`else`).
  - Confirms `Sound_PlaySE` / `ScriptVm_SetMessageId` are misnomers; `0x002B8B78` is a 6-slot UI/profile transition switcher.

## 2. Independent verification of both asserted H2 call paths

1. **`0x002F4CA0` (`titleConfig_func_002f4ca0`, `src/camp/title_flow.cpp`) -> `0x002F4DF0: bl 0x002B8B78` (omitted from `h2-sound-playse-contract-002b8b78.md`):**
   - Disassembly at `0x002F4DD8..0x002F4DF0` shows two `0x00297704` calls followed directly by `mov r0, #0x99; bl #0x2b8b78` (`request = 0x99`) on the function's main init path.
2. **`0x00286928` (`engine_func_00286928`, `src/engine/leaf_batch45_a.cpp`) -> `0x00286B80: bl 0x002B8B78`:**
   - Conditional path: `incoming_r2 == 0 && object[8] == 0 && !(query_a != 0 && query_b != 0) && row in {7, 8, 9} && 0x0028DF70(0) == 5` (`request = 0xDC`).
- **Static vs runtime:** Both are statically verified `BL` sites; neither establishes live runtime frequency or `TitleConfig` audio-settings reachability on its own (`0x00221168` has 0 direct `BL`s to `0x002B8B78`).

## 3. Dependency & memory-domain unknowns

- Five direct callees (`0x002B85BC`, `0x002AEA28`, `0x002B8794`, `0x0013851C`, `0x002AE874`) have separate contracts/state; `0x002B8B78` requires valid mapped ordinary RAM at `0x0043DA28`, `object` (`+0x4B8..+0x4CA`), and non-null `u16[6]`/`+0x0C` profile structs when `0x002AEA28` returns non-null.
