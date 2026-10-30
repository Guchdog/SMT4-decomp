# Independent Review: H1 Main Menu State-5 Slice Production Integration — `0x001E989C`

**Task ID:** `h1-menu-slice-integration-review`  
**Milestone:** H1 (Main menu integration)  
**Role:** Validation / Independent Review  
**Reviewer:** `flash-reviewer-3`  
**Worktree Root:** `C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp`  
**Reference Binary (`code.bin`):** `extracted/exefs/code.bin` (SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`)  
**Target Integration Report:** [`docs/agent-work/h1-menu-slice-integration.md`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/docs/agent-work/h1-menu-slice-integration.md) (SHA-256: `96e3a1eff7a302e45b90b2922d2db83daf7f06d5b020cbf5f9f97f433c232733`)  
**Producer Handoff:** [`build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/handoff.json`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/handoff.json) (SHA-256: `12732c986708b8cf544e9fb879a77636c76a83aee9d886e4e62edc58c6b07e98`)  

---

## 1. Recommendation & Executive Verdict

### Verdict: APPROVE PRODUCTION INTEGRATION AT DOCUMENTED SEMANTIC EVIDENCE LEVEL

I have independently inspected and audited the production integration of `H1_TitleMain_UpdateNavigationSlice` and its 54-word continuation shim inside `ui_func_001e989c` (`0x001E989C`) against the pinned reference binary `extracted/exefs/code.bin`, the source and header trees, `config/functions.csv`, the 258-case differential and composition report, and the 11-step Azahar live runtime report.

The integration is **technically rigorous, semantically equivalent within the bounded scope, and preserves strict structural integrity**:

1. **Exact Binary Span and Byte-Identity Outside the Slice:**
   - The compiled function `ui_func_001e989c` at [`src/ui/ui_runtime2.cpp:2981-3965`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/ui/ui_runtime2.cpp#L2981-L3965) maintains the exact 3,924-byte layout (981 32-bit ARM instructions).
   - The prefix window (`0x001E989C..0x001E9D04`, words 0..282, 1,132 bytes) matches `extracted/exefs/code.bin` byte-for-byte (283/283 words, 0 mismatches).
   - The suffix window (`0x001E9DE0..0x001EA7EC`, words 337..980, 2,576 bytes) matches `extracted/exefs/code.bin` byte-for-byte (644/644 words, 0 mismatches).
   - Only the defined 54-word State-5 window (`0x001E9D08..0x001E9DDC`, 216 bytes) is replaced by the 15-word continuation shim and 39 NOPs/literals.
   - `config/functions.csv` row `0x001e989c` is truthfully classified as `non_matching`.

2. **Shim Continuation Contract & Non-Destructive Gate Exit:**
   - On readiness failure (`r0 == 0`), the shim restores `sp` (`add sp, sp, #8`) and branches to the shared tail exit at `0x001EA62C` (`beq #0x1ea62c`, `.word 0x0a000241`) without touching `r4`, `r8`, or `s17`.
   - On readiness success (`r0 != 0`), the shim sets `r4` to the captured `TitleMainWork*`, restores `r8 = 0x0044E300` from the literal pool at `0x001E9D40`, sets `s17 = 1.0f` (`0x3F800000`), and branches to `0x001E9DE0` (`b #0x1e9de0`, `.word 0xea000029`), precisely satisfying the State-5 continuation invariant.

3. **Differential & Composition Matrix Verification:**
   - Differential report `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/differential-matrix/report.json` passes 258/258 cases from function entry `0x001E989C` (2 false readiness cases + 256 Cartesian cursor×cached×mask combinations).
   - The post-capture global pointer mutation case confirms that `*captured_work_out` preserves the active work pointer across external slot mutation.
   - The wrong-signed-modulo negative control confirms validator sensitivity by detecting mutant failure at `cursor = 0, mask = 0x01` (`0xFFFFFFFF` vs `3`).
   - The 4-selection transition/fade/help-lookup composition (`0x001E9FD4..0x001EA15C`) passes 4/4 selections using the observed runtime callback `0x00151404` (duration `1200.0f`), reviewed alpha helper `0x0029BDB4`, and promoted TBB accessors (`0x002AC2F4`, `0x002C0E9C`) with real `TitleTable.tbb`.

4. **Azahar Live Runtime Audit:**
   - Runtime report `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/azahar-runtime/runtime-report.json` confirms live code cave execution of `H1_TitleMain_UpdateNavigationSlice` at `0x003FE720` (`r0 = 0x0FFFFEA0`).
   - All 11 original-vs-patched steps match identically, verifying initial readiness at `0x001E9DE0`, help lookups at `0x001EA15C`, cursor stepping (`1->2->3`), bidirectional wraparound (`3->0` and `0->3`), Audio Settings entry (`0x002F4CA0` -> `0x001EA928`), and safe return reset (`0x001EA3D8` -> `0x001E9DE0`).
   - Zero save profile or configuration side-effects occurred (`saves_unchanged: true`, `g_ConfigBytes = 3250503000000000`).

5. **Honest Boundaries & Documented Fallthrough Constraint:**
   - Both `docs/agent-work/h1-menu-slice-integration.md` and `docs/milestones/H1-main-menu-flow.md` honestly document that direct callees (`0x00289924`, `0x0025A2BC`, `0x002B902C`, `0x002B91C4`), other callback states (`0-4`, `6-12`), and touch polling remain original ARM.
   - The architectural constraint that `Tbb_GetDefaultTable18Payload` (`0x002C0E84`) falls through into `Tbb_GetPayloadData` (`0x002C0E9C`) with `r4, lr` on the stack is clearly identified as a prerequisite before live IPS patching of `0x002C0E9C`.

---

## 2. In-Depth Layout and Binary Preservation Audit

### 2.1 Span Geometry and Byte Preservation

The function `ui_func_001e989c` (`0x001E989C`) is defined in `src/ui/ui_runtime2.cpp:2981-3965` as naked assembly containing exactly 981 32-bit instructions (3,924 bytes).

An automated byte-by-byte comparison against `extracted/exefs/code.bin` (offset `0x000E989C..0x000EA7F0`) confirms:

| Segment | Virtual Address Range | Offset in Callback | Instruction Count | Byte Length | Match vs `code.bin` |
| --- | --- | --- | --- | --- | --- |
| **Prefix** | `0x001E989C .. 0x001E9D04` | `0x000 .. 0x468` | 283 words | 1,132 bytes | **100% (283/283 words identical)** |
| **State-5 Slice** | `0x001E9D08 .. 0x001E9DDC` | `0x46C .. 0x540` | 54 words | 216 bytes | Replaced with C++ call shim + NOPs |
| **Suffix** | `0x001E9DE0 .. 0x001EA7EC` | `0x544 .. 0xF50` | 644 words | 2,576 bytes | **100% (644/644 words identical)** |
| **Total** | `0x001E989C .. 0x001EA7F0` | `0x000 .. 0xF54` | 981 words | 3,924 bytes | Exact size preserved |

### 2.2 54-Word Continuation Shim Disassembly & ABI Analysis

The 54 words (`0x001E9D08..0x001E9DDC`) inside `ui_func_001e989c` disassemble and execute as follows:

```arm
0x001e9d08:  sub     sp, sp, #8             ; Allocate 8-byte aligned stack slot for work pointer
0x001e9d0c:  mov     r0, sp                 ; Pass &captured_work in r0
0x001e9d10:  bl      H1_TitleMain_UpdateNavigationSlice  ; Call C++ slice (relocated at link time)
0x001e9d14:  cmp     r0, #0                 ; Test readiness return (1 = ready, 0 = not ready)
0x001e9d18:  ldr     r0, [sp]               ; Load captured TitleMainWork* into r0
0x001e9d1c:  add     sp, sp, #8             ; Restore stack pointer
0x001e9d20:  beq     0x001ea62c             ; (.word 0x0a000241) Branch to gate exit if not ready
0x001e9d24:  mov     r4, r0                 ; Continuation: r4 = captured TitleMainWork*
0x001e9d28:  ldr     r8, [pc, #16]          ; Load r8 = 0x0044E300 (&camp::g_TitleMainWork) from 0x001E9D40
0x001e9d2c:  mov     r12, #0x3f800000       ; IEEE-754 1.0f
0x001e9d30:  vmov    s17, r12               ; Restore s17 = 1.0f
0x001e9d34:  b       0x001e9de0             ; (.word 0xea000029) Branch to State-5 continuation
0x001e9d38:  nop                            ; (.word 0xe320f000)
0x001e9d3c:  nop                            ; (.word 0xe320f000)
0x001e9d40:  .word   0x0044e300             ; Literal pool: &camp::g_TitleMainWork
0x001e9d44..0x001e9ddc: nop (39 words)      ; (.word 0xe320f000) NOP padding to 0x001E9DE0
```

#### Detailed Branch Offset and Register Verification:
1. **Gate Exit Branch (`0x001E9D20`):**
   - Word encoding: `0x0A000241`.
   - Condition: `EQ` (when `r0 == 0`).
   - Offset: `0x0241` words = `+0x904` bytes relative to `PC + 8` (`0x001E9D28`).
   - Target: `0x001E9D28 + 0x904 = 0x001EA62C`.
   - Register preservation on branch: `sp` has been adjusted by `-8` and restored by `+8`. The callee `H1_TitleMain_UpdateNavigationSlice` follows AAPCS (preserving `r4-r11`, `d8-d15`). Neither `mov r4, r0`, `ldr r8`, nor `vmov s17` have executed. Therefore, `r4`, `r8`, and `s17` remain 100% unaltered upon branching to `0x001EA62C`, matching the exact pre-continuation register state of the original binary.
2. **Continuation Branch (`0x001E9D34`):**
   - Word encoding: `0xEA000029`.
   - Offset: `0x0029` words = `+0xA4` bytes relative to `PC + 8` (`0x001E9D3C`).
   - Target: `0x001E9D3C + 0xA4 = 0x001E9DE0`.
   - Invariants satisfied: `r4` points to `work`, `r8` holds `0x0044E300`, `s17` holds `1.0f` (`0x3F800000`), and `sp` is restored. At `0x001E9DE0`, the suffix immediately executes `ldr r0, [r4, #0x64]`, consuming `r4` as expected.

### 2.3 Functions Ledger Truthfulness

In `config/functions.csv`:
```csv
0x001e989c,3924,non_matching,ui,ui_func_001e989c,src/ui/ui_runtime2.cpp
```
The entry correctly marks `ui_func_001e989c` as `non_matching` with size `3924`. This fulfills project rules requiring truthful ledger accounting rather than claiming byte-identity for semantic replacements.

---

## 3. Audit of Differential Matrix & Composition Evidence

Report: [`build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/differential-matrix/report.json`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/differential-matrix/report.json) (SHA-256: `ff430feade8c0eb215b2a0e2f605a22371d21430141357a1285065684feb2c50`).

### 3.1 Full-Callback State-5 Differential Matrix (258 Cases)

The matrix executes from the actual callback entry `0x001E989C` with `state_9C = 5`, passing through the 13-entry jump table at `0x001E98C4` into the State-5 slice:

1. **Readiness False Gate Cases (2/2 Passed):**
   - `script_not_ready` (`Script_IsReadyToAdvance` returns 0): stops at `0x001EA62C`, zero helper/event calls, `TitleMainWork` unmodified, `r4`/`r8`/`s17` preserved.
   - `preview_not_ready` (`Camp_IsPreviewReady` returns 0): stops at `0x001EA62C`, short-circuits after gate 1, zero trigger/event calls, `r4`/`r8`/`s17` preserved.
2. **Full Cartesian Matrix (256/256 Passed):**
   - Dimensions: 4 initial cursors (`0..3`) × 4 cached cursors (`0..3`) × 16 trigger masks (combinations of logical IDs `{5, 0xE}` for decrement and `{6, 0xF}` for increment).
   - Execution stops at `0x001E9E50` (interior checkpoint after blend ramp and `ldr r6, [r8]` at `0x001E9E4C`).
   - Results: 100% equivalence in stop PC (`0x001E9E50`), helper invocation sequence, event `0x0100016C` dispatch (only when normalized cursor != cached), `TitleMainWork` memory diffs (`+0x08`, `+0x0C`, `+0x64`, `+0x68`), and registers (`r4`, `r8`, `s17`, `r6`, `r7`, `r9-r11`, `d8-d15`, `SP`, `FPSCR`).

### 3.2 Adversarial Global-Pointer Mutation Case

Case: `captured-work-survives-global-slot-mutation`.
- Test mechanism: on the very first trigger query inside `H1_TitleMain_UpdateNavigationSlice`, the test hook mutates `*0x0044E300` from `0x02000100` to `0x02000300`.
- Expected behavior: the slice captures `*captured_work_out = work` (`0x02000100`) at gate entry. Reducer writes must apply to `0x02000100`. At `0x001E9E4C`, `ldr r6, [r8]` reads `*0x0044E300`, loading `r6 = 0x02000300`.
- Result: **Passed**. Both original ARM and production C++ integration produce identical register state (`r4 = 0x02000100`, `r6 = 0x02000300`, `r8 = 0x0044E300`) and identical memory modifications on `0x02000100`.

### 3.3 Negative Control Validation

Mutant: `wrong_raw_signed_remainder_for_minus_one`.
- A mutant `ui_runtime2_wrong_modulo.cpp` replaces `NormalizeSignedRemainderByFour` with `static_cast<u32>(static_cast<s32>(provisional) % 4)`.
- In C++, `(-1) % 4` evaluates to `-1` (`0xFFFFFFFF`), whereas the ARM logic `provisional + 4` normalized by 4 wraps `-1` to `3`.
- Result: **Detected (`detected: true`, `passed: false`)**. The differential comparison immediately flagged mismatch on `cursor = 0, mask = 0x01` (`0xFFFFFFFF` vs `3`, failing memory and event observations). This confirms that the test harness actively rejects non-equivalent arithmetic.

### 3.4 State-5 Transition / Fade / Help-Lookup Composition (4 Selections)

Window: `0x001E9FD4..0x001EA15C`.
The composition integrates:
- Observed track callback: `0x00151404` (from `h1-track-runtime`, duration `1200.0f` = `0x44960000`, `callback_arg = 0x00000000`).
- Reviewed alpha helper: `0x0029BDB4` (from `h1-alpha-caller-review`).
- Promoted production TBB accessors: `Tbb_GetSubTable` (`0x002AC2F4`) and `Tbb_GetPayloadData` (`0x002C0E9C`) from `src/ui/tbb_loader.cpp`.
- Asset: real `build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb` (880 bytes).

Results across all 4 selections (`0..3`):
- Selection 0: `"Start a new game from the beginning."` (`r0 = 0x02001046`, `r1 = 0x323232FF`, `work+0x98 = 0.75`, `work+0x94 = 1`, `data_sha256 = 0a49d1e2...`) — **PASS**.
- Selection 1: `"Load a saved game and continue playing."` (`r0 = 0x0200109C`, `r1 = 0x323232FF`, `work+0x98 = 0.75`, `work+0x94 = 1`, `data_sha256 = af6a6fd1...`) — **PASS**.
- Selection 2: `"Configure audio settings."` (`r0 = 0x020010F2`, `r1 = 0x323232FF`, `work+0x98 = 0.75`, `work+0x94 = 1`, `data_sha256 = 1be34d4c...`) — **PASS**.
- Selection 3: `"Download additional content."` (`r0 = 0x02001148`, `r1 = 0x323232FF`, `work+0x98 = 0.75`, `work+0x94 = 1`, `data_sha256 = 22249a97...`) — **PASS**.

---

## 4. Audit of Azahar Live Runtime Report

Report: [`build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/azahar-runtime/runtime-report.json`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/azahar-runtime/runtime-report.json) (SHA-256: `665dc7d4f35370063e26ee6a6e7e3f1f68ef7df50b6d8046e7687147ac2196e7`).

### 4.1 Live Code Cave Placement and Hit Confirmation
- **Target Emulator:** `E:\emulador3ds\azahar.exe`
- **Game Title:** Shin Megami Tensei IV (US v0.1.0, Title ID `00040000000E5C00`)
- **Cave Address:** `0x003FE720` in executable text padding.
- **Verification:** Breakpoint on `0x003FE720` hit live with `r0 = 0x0FFFFEA0` (`&captured_work` on stack), verifying that the patched binary entered compiled `H1_TitleMain_UpdateNavigationSlice` directly from the `ui_func_001e989c` continuation shim in real emulator execution.

### 4.2 11/11 Original-vs-Patched Runtime Steps Matched

| Step | State | Location | Matched Features |
|:---:|:---:|:---:|---|
| **1. initial_ready_at_001e9de0** | State 5 | `0x001E9DE0` | `selection_08 = 1` (Load Game), `cached_0c = 1`, `state_9c = 5`, `r4 = r5 = 0x15C00080`, `r8 = 0x0044E300`. |
| **2. help_lookup_sel1** | State 5 | `0x001EA15C` | `r0 = 0x086C9D1C` (`"Load a saved game and continue playing."`), `r1 = 0x323232FF`. |
| **3. move_down_1_to_2_at_001e9de0** | State 5 | `0x001E9DE0` | Cursor moved 1 -> 2, `selection_08 = 2`, `cached_0c = 2`, help text updated to `"Configure audio settings."`. |
| **4. move_down_2_to_3_at_001e9de0** | State 5 | `0x001E9DE0` | Cursor moved 2 -> 3, `selection_08 = 3`, `cached_0c = 3`, help text updated to `"Download additional content."`. |
| **5. wrap_down_3_to_0_at_001e9de0** | State 5 | `0x001E9DE0` | **Forward wraparound 3 -> 0**, `selection_08 = 0`, `cached_0c = 0`, help text updated to `"Start a new game from the beginning."`. |
| **6. wrap_up_0_to_3_at_001e9de0** | State 5 | `0x001E9DE0` | **Backward wraparound 0 -> 3**, `selection_08 = 3`, `cached_0c = 3`, help text updated to `"Download additional content."`. |
| **7. move_up_3_to_2_at_001e9de0** | State 5 | `0x001E9DE0` | Cursor moved 3 -> 2, `selection_08 = 2`, `cached_0c = 2`, help text updated to `"Configure audio settings."`. |
| **8. enter_titleConfig_002f4ca0** | State 9 | `0x002F4CA0` | Confirming selection 2 triggers State 9 dispatch to `titleConfig_func_002f4ca0` with `selection_08 = 2`. |
| **9. titleConfig_calc_reached** | Config | `0x001EA928` | Reached `TitleConfig_Calc` task with allocated `g_TitleConfigWork = 0x086E4700`. |
| **10. return_from_audio_settings_reset_001ea3d8** | State 10 | `0x001EA3D8` | Cancelling Audio Settings enters `Title_ResetForBoot` with `state_9c = 10`. |
| **11. returned_to_state5_ready_001e9de0** | State 5 | `0x001E9DE0` | Reset returns to State 5 ready with `selection_08 = 2`, `cached_0c = 2`, `timer_64 = 1.0`, `blend_68 = 0.0`, `fade_6c = 1.0`. |

### 4.3 Profile and Save Integrity
- `saves_before: []`, `saves_after: []` (`saves_unchanged: true`).
- `g_ConfigBytes` (`0x0044E0F8`): `3250503000000000` before and after (`config_bytes_unchanged: true`).
- This confirms that no persistent user options or save slots were altered during H1 navigation and config menu verification.

---

## 5. Architectural Constraints and Remaining Boundaries

1. **`0x002C0E84 -> 0x002C0E9C` Fallthrough Constraint:**
   - In original ARM, `Tbb_GetDefaultTable18Payload` (`0x002C0E84`) pushes `{r4, lr}` and falls through directly into `Tbb_GetPayloadData` (`0x002C0E9C`), relying on `0x002C0E9C` returning without modifying the stack so `0x002C0E90` can execute `pop {r4, pc}`.
   - Compiled C++ `Tbb_GetPayloadData` emits standard function prologue/epilogue (`push {fp, lr}` ... `pop {fp, pc}`).
   - While direct calls to `0x002C0E9C` (such as `0x001EA14C` in H1 help presentation) function properly, hooking `0x002C0E9C` globally via live IPS breaks the fallthrough caller `0x002C0E84` (used by `Camp_SetSlotMessage` at `0x0029F10C`).
   - Both documents correctly identify that `0x002C0E84` must be reconstructed as an ordinary C++ call before live IPS patching of `0x002C0E9C`.

2. **Original ARM Callees Still Called by Slice:**
   - `Script_IsReadyToAdvance` (`0x00289924`)
   - `Camp_IsPreviewReady` (`0x0025A2BC`) and its callee `0x002BF9F0`
   - `UiInput_Trigger` (`0x002B902C`)
   - `Script_RequestEvent` (`0x002B91C4`)

3. **Untested Destructive Paths:**
   - New Game confirmation (State 6 / 12 -> `Script_StartNewGame` `0x0026FA94`), Load Game slot selection (States 7–8 -> `SaveLoad_BeginFromTitle` `0x0030A9A4`), and Add-On Content (States 11–12) remain intentionally excluded from Azahar live testing to safeguard user save state.

---

## 6. Artifact Provenance & SHA-256 Table

All inspected input, source, binary, report, and script files match their pinned identities:

| File Path | SHA-256 Hash | Provenance / Role |
| --- | --- | --- |
| `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` | Reference binary |
| `build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb` | `edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41` | Real asset |
| `src/ui/ui_runtime2.cpp` | `7d0c4aa573a54e6862fafdb582aef750e27f476b90a09ebb6c9745fb458c1b3a` | Production source with slice |
| `include/camp/title_flow.h` | `e099fa067c054bb59d00b30c8bd5eb88502a00869f0d92c38734e37978e61c1a` | Production header with slice decl |
| `config/functions.csv` | `2729777ae50e16341186e341e715ba46f6d12da41dd419d46e16442c7854a757` | Function ledger (`non_matching`) |
| `config/game_info.json` | `5b9f1fa5114e9a460c9e2d7ca045d882c17ff8f93d70e358b1834141a0d4dbdd` | Game metadata |
| `config/reconstruction.json` | `26cfcb7f84d1a879e99fc95548754b9ceb0ce0b9a814680d2f2888bbe78b888c` | Project configuration |
| `docs/agent-workflow.md` | `0cacc1c803e3206651e6ad67493510a9437b6a2303a76cb7910ce6515f85cc56` | Workflow specification |
| `docs/milestones/H1-main-menu-flow.md` | `4c53c00ff055c0a59039114ec1fc2934fa0fe83aa595cfc171adb8c568a79235` | Milestone documentation |
| `docs/agent-work/h1-menu-slice-integration.md` | `96e3a1eff7a302e45b90b2922d2db83daf7f06d5b020cbf5f9f97f433c232733` | Producer integration report |
| `tools/h1_menu_slice_integration_experiment.py` | `2afdc55375bce278de118c3bf3f3f249e10ae5349c2d86117c0d445f1296d3c9` | Differential runner |
| `tests/test_h1_menu_slice_integration_experiment.py` | `fe3f8c303c600b636a7b6603330ff43a4e77de5239b2940d18762a08f0c8f016` | Unit test |
| `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/handoff.json` | `12732c986708b8cf544e9fb879a77636c76a83aee9d886e4e62edc58c6b07e98` | Producer handoff |
| `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/differential-matrix/report.json` | `ff430feade8c0eb215b2a0e2f605a22371d21430141357a1285065684feb2c50` | 258-case differential report |
| `build/agent-work/H1-semantic/h1-menu-slice-integration/run-01/checks/azahar-runtime/runtime-report.json` | `665dc7d4f35370063e26ee6a6e7e3f1f68ef7df50b6d8046e7687147ac2196e7` | 11-step Azahar runtime report |
| `build/agent-work/H1-semantic/h1-menu-slice-integration-review/run-01/task.json` | `2c75bc6cdd30abc8c3f8b8c63026912e4e80f4ce44620a9534cce48508a31a2f` | Assigned task packet |
| `build/agent-work/H1-semantic/h1-menu-slice-integration-review/run-01/brief.md` | `69d0b5c786c11786768d967c580142cc0fa9b944cc93c4dd39f80dca371568e4` | Assigned task brief |

---

## 7. Conclusion & Next Action

The H1 State-5 menu slice integration (`h1-menu-slice-integration`) satisfies all acceptance criteria, maintains strict binary layout preservation outside the slice window, truthfully records the non-matching ledger state, demonstrates comprehensive differential equivalence across 258 matrix cases and controls, and confirms live cave execution and 11-step runtime parity in Azahar.

**Recommendation:** Accept `h1-menu-slice-integration`, mark task complete on the coordinator board, and proceed with closing the active H1 batch.
