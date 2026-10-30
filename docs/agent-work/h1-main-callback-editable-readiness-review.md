# Independent Review: H1 Main Callback Editable Readiness Assessment — `0x001E989C`

**Task ID:** `h1-main-callback-editable-readiness-review`  
**Milestone:** H1 (Main menu integration)  
**Role:** Validation / Independent Review  
**Reviewer:** `flash-reviewer-1`  
**Worktree Root:** `C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp`  
**Reference SHA-256 (`code.bin`):** `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`  
**Target Assessment Document:** [`docs/agent-work/h1-main-callback-editable-readiness.md`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/docs/agent-work/h1-main-callback-editable-readiness.md) (SHA-256: `046ffdd4c44a9bb082a096756c39994079bb95532780a87d190a66eb3e0d2e47`)

---

## 1. Executive Verdict and Assessment

### Verdict: CONCUR WITH REPAIR-FIRST RECOMMENDATION; WHOLE-CALLBACK ACTIVATION BLOCKED

I have independently audited the claims in [`docs/agent-work/h1-main-callback-editable-readiness.md`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/docs/agent-work/h1-main-callback-editable-readiness.md) against the pinned reference binary `extracted/exefs/code.bin`, the source tree (`src/ui/ui_runtime2.cpp`, `src/camp/unite.cpp`, `src/camp/title_message.cpp`, `src/engine/leaf_batch*.cpp`), and `config/functions.csv`.

The assessment by `recon-worker-1` is **technically sound, accurate, and supported by concrete binary and source evidence**. My independent audit verifies:

1. **Compiled binary reality vs `#if 0` C++ draft:**
   - The compiled function `ui_func_001e989c` at [`src/ui/ui_runtime2.cpp:2924-3908`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/ui/ui_runtime2.cpp#L2924-L3908) consists of **100% naked inline ARM assembly words** (981 instructions, 3,924 bytes), matching `extracted/exefs/code.bin` slice `0x000E989C..0x000EA7F0` byte-for-byte (SHA-256: `818ac879c6d4f028f4686969ed1743322683b0656c5b018737b29596b7d779b4`).
   - The readable C++ draft at [`src/ui/ui_runtime2.cpp:3909-4424`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/ui/ui_runtime2.cpp#L3909-L4424) is entirely enclosed in `#if 0 ... #endif` (516 lines). **Zero C++ logic from this callback compiles into the binary.** The two static helper functions in the anonymous namespace (`Title_ResetForBoot` at line 2889 and `Title_SequenceRequest` at line 2911) are only referenced inside `#if 0` and are completely dead uncalled code.
2. **Helper symbol binding seam (refined from 9/49 to 1/8/49):**
   - The file declares 58 `extern "C"` helper functions in [`src/ui/ui_runtime2.cpp:86-144`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/ui/ui_runtime2.cpp#L86-L144).
   - Only **1** of the 58 declared functions has an actual compiled definition with that symbol name: `ButtonHelp_Init` (at `0x0028D974`, defined in [`src/camp/unite.cpp:151`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/camp/unite.cpp#L151)).
   - **8** functions (`Sound_RequestBgm`, `Effect_SetDrawParams`, `Effect_SetScale`, `AsdCamera_BindProjection`, `UiInput_Trigger`, `UiInput_Trigger2`, `AsdTask_DestroyPair`, `Save_GetGameOverStateIndex`) appear in other translation units, but **strictly as duplicate forward declarations or call sites without definitions**. In their defining leaf batches, they are named with ledger names (e.g. `camp_func_002a0640`, `ui_func_002c1ffc`, `ui_func_002b902c`, etc.).
   - **49** functions have zero occurrences outside `ui_runtime2.cpp`.
   - **Linker consequence:** Activating `#if 1` immediately produces **57 unresolved external reference errors** (not 49).
3. **Behavioral and semantic discrepancies:**
   - **State 3 condition cascade (`0x001E9B90..0x001E9BBC`):** Decoded ARM demonstrates an OR-cascade over three conditions: `0x002AE16C(work->resource_8c) != 0` OR `0x002AE16C(work->resource_90) != 0` OR `work->resource_88 != 0`. The callee `0x002AE16C` tests whether payload pointer `handle->field_8->field_4 != 0`, returning 1 when valid/ready and 0 when not. The draft name `Res_IsLoadBusy` is an inverse misnomer for an "is loaded / valid" query.
   - **State 5 touch loop (`0x001E9E4C..0x001E9EB8`):** ARM Loop 1 (`0x001E9E4C..0x001E9E88`) calls `0x0029D8FC` **twice per handle index** if the first result is not 1 (once for state 1, then again for state 2). If matched, it sets `work->field_08 = i` and immediately branches to Loop 2. The C++ draft calls `UiTouch_GetRegionTouchState` only once per index and caches the return value. Furthermore, `UiTouch_GetRegionTouchState` is also undefined at link time.
4. **State-5 bounded activation boundary and continuation ABI:**
   - The keyboard/controller selection reducer (`0x001E9D48..0x001E9DE0`) remains the smallest coherent C++ candidate slice.
   - Expanding to the outer readiness window (`0x001E9D08..0x001E9DE0`) requires bindings for `0x00289924` (`script_vm_func_00289924`) and `0x0025A2BC` (`ui_func_0025a2bc`).
   - The continuation contract requires:
     - `r4`: must point to `work` (`g_TitleMainWork`) at `0x001E9DE0`.
     - `r8`: must hold literal `0x0044E300` (`&g_TitleMainWork`), dereferenced at `0x001E9E4C` (`ldr r6, [r8]`).
     - `s17`: must preserve float `1.0F` (`0x3F800000`), loaded at `0x001E9D30` and consumed at `0x001E9E30` (`vsubgt.f32 s1, s0, s17`).
     - Callee-saved register set `r4-r8` and `d8` (`s16-s17`) must be preserved.

---

## 2. Independent Extent and Binary Identity Audit

### 2.1 Virtual Address Span and Extents
- **Symbol:** `ui_func_001e989c` (`config/functions.csv` line 2494)
- **Virtual Address Range:** `[0x001E989C, 0x001EA7F0)`
- **Byte Length:** `3,924` bytes (`981` 32-bit ARM words)
- **Offset in `extracted/exefs/code.bin`:** `0x000E989C..0x000EA7F0`
- **Binary Slice SHA-256 (`code.bin`):** `818ac879c6d4f028f4686969ed1743322683b0656c5b018737b29596b7d779b4`

### 2.2 Source Verification in `src/ui/ui_runtime2.cpp`
- **Compiled Function Lines:** [`src/ui/ui_runtime2.cpp:2924-3908`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/ui/ui_runtime2.cpp#L2924-L3908)
  - Signature: `__attribute__((naked)) void ui_func_001e989c(void*)`
  - Body: `asm volatile(...)` containing exactly 981 `.word 0x...` directives.
  - Extracted binary packing of these 981 `.word` values yields **100% byte identity** with the `code.bin` slice:
    - `cpp_words_sha256 = 818ac879c6d4f028f4686969ed1743322683b0656c5b018737b29596b7d779b4`
- **Disabled Readable C++ Draft:** [`src/ui/ui_runtime2.cpp:3909-4424`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/ui/ui_runtime2.cpp#L3909-L4424)
  - Starts with line 3909: `#if 0`
  - Ends with line 4424: `#endif`
  - Total draft size: 516 lines.

### 2.3 Jump Table Geometry Audit
The dispatch table located at `0x001E98BC..0x001E98F8` was disassembled and confirmed:
- `0x001E98B4: ldr r0, [r5, #0x9C]` (loads `work->state_9C`)
- `0x001E98B8: cmp r0, #0xD` (checks `state < 13`)
- `0x001E98BC: ldrlo pc, [pc, r0, lsl #2]` (branches via 13-entry word table at `0x001E98C4`)
- `0x001E98C0: b 0x001EA62C` (if `state >= 13`, branches to shared tail)

Table targets independently verified:
| State | Table Address | Jump Target in `code.bin` | Description in Report | Independent Status |
|:---:|:---:|:---:|---|:---:|
| **0** | `0x001E98C4` | `0x001E98F8` | Layout slot 0x3A cache, fade reset | MATCH |
| **1** | `0x001E98C8` | `0x001E9A10` | Animation update at `+0x14` | MATCH |
| **2** | `0x001E98CC` | `0x001E9A3C` | Title resource bootstrap (.bccam, .bam, .bcenv) | MATCH |
| **3** | `0x001E98D0` | `0x001E9B90` | Handle load polling cascade | MATCH |
| **4** | `0x001E98D4` | `0x001E9BC0` | Camera projection & billboard scale | MATCH |
| **5** | `0x001E98D8` | `0x001E9D08` | Main menu navigation & option dispatch | MATCH |
| **6** | `0x001E98DC` | `0x001EA48C` | Immediate transition to state 12 | MATCH |
| **7** | `0x001E98E0` | `0x001EA32C` | Save/load start, transition 0 | MATCH |
| **8** | `0x001E98E4` | `0x001EA358` | Save/load busy poll | MATCH |
| **9** | `0x001E98E8` | `0x001EA398` | Title config start | MATCH |
| **10** | `0x001E98EC` | `0x001EA3C4` | Title config wait | MATCH |
| **11** | `0x001E98F0` | `0x001EA478` | Script ready wait | MATCH |
| **12** | `0x001E98F4` | `0x001EA494` | Teardown & mode execution | MATCH |

---

## 3. Independent Symbol Binding Audit

### 3.1 Analysis of the 58 Declared `extern "C"` Helpers
Lines 86–144 in [`src/ui/ui_runtime2.cpp`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/ui/ui_runtime2.cpp#L86-L144) forward-declare 58 helper functions. A repository-wide code and symbol scan produced the following exact distribution:

1. **Functions with a compiled definition matching the declared name: Exactly 1**
   - `ButtonHelp_Init` (`0x0028D974`): defined in [`src/camp/unite.cpp:151`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/camp/unite.cpp#L151) as `__attribute__((naked)) void ButtonHelp_Init()` and listed in `config/functions.csv` under this exact name.
2. **Functions with forward declarations or call sites elsewhere, but NO definitions: Exactly 8**
   - `Sound_RequestBgm` (`0x002A0640`): declared in `include/engine/asd_symbols.h`; compiled as `camp_func_002a0640` in `leaf_batch34_b.cpp`.
   - `Effect_SetDrawParams` (`0x002C1FFC`): declared in `src/battle/battle_extras.cpp`; compiled as `ui_func_002c1ffc` in `leaf_batch37_c.cpp`.
   - `Effect_SetScale` (`0x002C1774`): declared in `src/battle/battle_extras.cpp` and `src/ui/ui_scene_extras.cpp`; compiled as `ui_func_002c1774` in `leaf_matching.cpp`.
   - `AsdCamera_BindProjection` (`0x00298FEC`): declared in `src/engine/asd_render_ui.cpp`, `src/engine/map_runtime.cpp`, and `src/script/script_vm_extras.cpp`; compiled as `ui_func_00298fec` in `leaf_batch21_b.cpp`.
   - `UiInput_Trigger` (`0x002B902C`): declared in `src/ui/ui_blocks.cpp` and `src/ui/ui_scene_extras.cpp`; compiled as `ui_func_002b902c` in `leaf_batch30_b.cpp`.
   - `UiInput_Trigger2` (`0x002BFFBC`): declared in `src/engine/asd_frame.cpp`, `src/engine/asd_model.cpp`, `src/ui/ui_blocks.cpp`, and `src/ui/ui_scene_extras.cpp`; compiled as `ui_func_002bffbc` in `leaf_batch32_c.cpp`.
   - `AsdTask_DestroyPair` (`0x002C45B8`): declared in `src/ui/status_down.cpp`; compiled as `battle_func_002c45b8` in `leaf_batch36_c.cpp`.
   - `Save_GetGameOverStateIndex` (`0x002C0B94`): declared in `src/battle/battle_extras.cpp`; compiled as `ui_func_002c0b94` in `leaf_batch21_b.cpp`.
3. **Functions with ZERO references anywhere else in the repository: Exactly 49**
   - Includes: `Title_LoadLayout`, `Title_ResetFadeState`, `Script_TestFlag`, `UiSound_PlayCue`, `TitleAnim_Update`, `CommonBg_Begin`, `ScriptVm_SetMessageId`, `Title_PreparePreview`, `Res_LoadBccam`, `Res_LoadBam`, `Res_LoadBcenv`, `Title_RegisterDefaultResources`, `Res_IsLoadBusy`, `UiModel_SetVisible`, `UiStyle_GetCurrent`, `UiText_GetMetrics`, `UiModel_SetFlag`, `UiModel_ApplyAlpha`, `Script_IsReadyToAdvance`, `Camp_IsPreviewReady`, `Script_RequestEvent`, `UiModel_SetFade`, `UiModel_IsVisible`, `UiModel_IsReady`, `UiModel_ResetFade`, `UiModel_SetFadeParam`, `UiModel_GetFade`, `UiMenu_CheckCursorSound`, `Camp_AdvanceCursorBlink`, `Script_PrepareCursor`, `Script_ApplyCursorMode`, `Script_SetCursorSound`, `Script_ResetCursorSound`, `Script_PrepareTransition`, `SaveLoad_BeginFromTitle`, `SaveLoad_IsBusy`, `Title_GetManagerFlag`, `TitleConfig_IsReady`, `ScriptVm_ResetTitle`, `UiScene_SetupField`, `UiScene_DrawLoading`, `Script_PrepareTitleBoot`, `UiScene_SetFade`, `Script_StartTitleFade`, `Script_ClearTitleInput`, `Script_StartNewGame`, `Camp_DrawTitleBundle`, `Res_ReleaseHandle`, `Runtime_GetTitleObject`.

### 3.2 Finding
The assessment's conclusion that enabling `#if 1` is blocked by unresolved symbols is **completely verified and slightly understated**: 57 out of 58 symbols lack definitions, making whole-callback C++ linking impossible without substantial interface bindings.

---

## 4. Independent Disassembly & Behavioral Discrepancy Audits

### 4.1 State 3 Condition Cascade (`0x001E9B90..0x001E9BBC`)

```
0x001E9B90: ldr   r0, [r5, #0x8C]       ; r0 = work->resource_8c
0x001E9B94: bl    0x002AE16C            ; call 0x002AE16C(resource_8c)
0x001E9B98: cmp   r0, #0                ; test result
0x001E9B9C: nop
0x001E9BA0: bne   0x001E9A30            ; if != 0, advance state! (work->state_9C++)
0x001E9BA4: ldr   r0, [r5, #0x90]       ; r0 = work->resource_90
0x001E9BA8: bl    0x002AE16C            ; call 0x002AE16C(resource_90)
0x001E9BAC: cmp   r0, #0                ; test result
0x001E9BB0: ldreq r0, [r5, #0x88]       ; if == 0, load work->resource_88
0x001E9BB4: cmpeq r0, #0                ; if == 0, test work->resource_88
0x001E9BB8: bne   0x001E9A30            ; if resource_90 ready OR resource_88 != 0, advance state!
0x001E9BBC: b     0x001EA62C            ; else exit to shared tail (stay in state 3)
```

**Disassembly of Helper `0x002AE16C`:**
```
0x002AE16C: cmp   r0, #0
0x002AE170: ldrne r0, [r0, #8]          ; r0 = handle->field_8
0x002AE174: cmpne r0, #0
0x002AE178: beq   0x002AE188            ; if handle == NULL or handle->field_8 == NULL -> return 0
0x002AE17C: ldr   r0, [r0, #4]          ; r0 = handle->field_8->field_4
0x002AE180: cmp   r0, #0
0x002AE184: movne r0, #1                ; return 1 if subobject != NULL, else 0
0x002AE188: bx    lr
```

**Audit Verdict:**
- `0x002AE16C` returns `1` when the underlying resource subobject is loaded/valid.
- The C++ draft at lines 4002–4014 names this function `Res_IsLoadBusy`, which semantically contradicts its return value (`1` = ready, not busy).
- The cascade advances if ANY of the three handles has valid data. The C++ draft flow matches this cascade, but the semantic naming is inverted and misleading.

### 4.2 State 5 Touch Polling Loop (`0x001E9E4C..0x001E9EB8`)

**Disassembly of Loop 1 (State 1 and 2 detection):**
```
0x001E9E4C: ldr   r6, [r8]              ; r6 = *g_TitleMainWork
0x001E9E50: mov   r4, #0                ; i = 0
0x001E9E54: add   r7, r6, r4, lsl #1    ; r7 = &work->field_74[i]
0x001E9E58: ldrh  r0, [r7, #0x74]       ; r0 = touch_handle
0x001E9E5C: bl    0x0029D8FC            ; call 0x0029D8FC(handle)
0x001E9E60: cmp   r0, #1                ; check if state == 1
0x001E9E68: beq   0x001EA014            ; if 1, branch to set cursor and enter Loop 2
0x001E9E6C: ldrh  r0, [r7, #0x74]       ; r0 = touch_handle (RELOAD!)
0x001E9E70: bl    0x0029D8FC            ; call 0x0029D8FC(handle) (SECOND CALL!)
0x001E9E74: cmp   r0, #2                ; check if state == 2
0x001E9E7C: beq   0x001EA014            ; if 2, branch to set cursor and enter Loop 2
0x001E9E80: add   r4, r4, #1            ; i++
0x001E9E84: cmp   r4, #4
0x001E9E88: blt   0x001E9E54            ; loop while i < 4
```

**Disassembly of Loop 2 (State 6 confirmation detection):**
```
0x001E9E8C: mov   r4, #0                ; i = 0
0x001E9E90: mov   r7, #1                ; r7 = 1
0x001E9E94: add   r0, r6, r4, lsl #1
0x001E9E98: ldrh  r0, [r0, #0x74]
0x001E9E9C: bl    0x0029D8FC            ; call 0x0029D8FC(handle)
0x001E9EA0: cmp   r0, #6                ; check if state == 6
0x001E9EA4: streq r4, [r6, #8]          ; if 6, work->field_08 = i
0x001E9EA8: add   r4, r4, #1            ; i++
0x001E9EAC: strbeq r7, [r6, #0x63]      ; if 6, work->flag_63 = 1
0x001E9EB0: cmp   r4, #4
0x001E9EB4: blt   0x001E9E94            ; loop while i < 4
```

**C++ Draft Implementation ([`src/ui/ui_runtime2.cpp:4109-4121`](file:///C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/src/ui/ui_runtime2.cpp#L4109-L4121)):**
```cpp
const u16* touch = TitleTouchHandles(work);
for (s32 i = 0; i < 4; ++i) {
    const s32 state = UiTouch_GetRegionTouchState(static_cast<s16>(touch[i]));
    if (state == 1 || state == 2) {
        work->field_08 = static_cast<u32>(i);
        break;
    }
}
for (s32 i = 0; i < 4; ++i) {
    if (UiTouch_GetRegionTouchState(static_cast<s16>(touch[i])) == 6) {
        work->field_08 = static_cast<u32>(i);
        work->flag_63 = 1;
    }
}
```

**Audit Verdict:**
- The discrepancy identified by `recon-worker-1` is **confirmed**: ARM queries `0x0029D8FC` up to twice per iteration in Loop 1 (if the first query returns non-1, it invokes the helper a second time to test for 2).
- The C++ draft calls `UiTouch_GetRegionTouchState` once per iteration and checks `state == 1 || state == 2`. If `0x0029D8FC` interacts with an input queue or advances internal touch state, this creates an observable behavior difference.
- In Loop 2, ARM executes all 4 queries unconditionally and writes `field_08` and `flag_63` on every match, meaning the **highest index matching state 6 wins**. The C++ draft accurately mirrors this last-match-wins behavior.

---

## 5. State-5 Activation Boundary and Continuation ABI Verification

### 5.1 Reducer Window (`0x001E9D48..0x001E9DE0`)
The core keyboard/controller reducer performs:
- Input trigger checks for IDs 5, 0xE, 6, 0xF via `0x002B902C` (`ui_func_002b902c`).
- Signed modulo wrap `(cursor + 4) % 4` ensuring `[-1..3] -> [0..3]`.
- Cache check with `work->field_0C`: emits event `0x0100016C` via `0x002B91C4` (`script_vm_func_002b91c4`) on mismatch, then updates `work->field_0C`.

### 5.2 Continuation Register and VFP Constraints
I independently examined the surrounding instructions from `0x001E9D08` through `0x001E9E54`:

1. **`r4` Requirement:**
   - At `0x001E9D38`, `ldr r4, [r8]` samples `g_TitleMainWork`.
   - At `0x001E9DE0`, the very first instruction after the reducer is `ldr r0, [r4, #0x64]`.
   - Subsequent instructions throughout `0x001E9DE0..0x001E9E48` repeatedly load and store through `r4`.
   - **Constraint:** `r4` must hold the active `TitleMainWork*` pointer upon resuming ARM execution at `0x001E9DE0`.
2. **`r8` Requirement:**
   - At `0x001E9D2C`, `ldr r8, =0x0044E300` (`&g_TitleMainWork`).
   - Inside the reducer (`0x001E9D48..0x001E9DE0`), `r8` is not used.
   - At `0x001E9E4C` (start of touch loop), the instruction is `ldr r6, [r8]`.
   - **Constraint:** `r8` must remain `0x0044E300` when execution reaches `0x001E9E4C`. If clobbered across the reducer or shim, `[r8]` dereference will fault.
3. **`s17` (VFP single-precision) Requirement:**
   - At `0x001E9D30`, `0xEDDF8A7E` decodes as `vldr s17, [pc, #0x1F8]`, loading literal `1.0F` (`0x3F800000` at `0x001E9F30`).
   - At `0x001E9D40`, `s17` is used: `vadd.f32 s0, s0, s17` (`field_64 += 1.0F`).
   - Inside the blend ramp at `0x001E9E30`, `0xCEF00A68` decodes as `vsubgt.f32 s1, s0, s17`, **directly reusing `s17` as `1.0F`**.
   - **Constraint:** `s17` must remain `1.0F` (`0x3F800000`) at `0x001E9DE0`. Since `s17` is the upper 32 bits of `d8` (callee-saved under AAPCS-VFP), any routine that touches `d8` or single registers `s16..s31` must preserve `s17`.
4. **Readiness Window (`0x001E9D08..0x001E9DE0`):**
   - If the candidate encompasses readiness gating, failure of `0x00289924` or `0x0025A2BC` branches to `0x001EA62C`.
   - At `0x001EA62C`, the shared tail expects caller-preserved entry registers (`r4-r8`, `d8`).

---

## 6. Recommendations and Next Actions

1. **Maintain `#if 0` on full callback:** Do not attempt whole-callback C++ activation.
2. **Target bounded State-5 slice:**
   - Establish canonical symbol bindings:
     - `UiInput_Trigger` -> `ui_func_002b902c`
     - `Script_RequestEvent` -> `script_vm_func_002b91c4`
     - `Script_IsReadyToAdvance` -> `script_vm_func_00289924`
     - `Camp_IsPreviewReady` -> `ui_func_0025a2bc`
   - Implement the bounded selection reducer in a separate, isolated TU (e.g. `src/ui/title_navigation.cpp`).
   - Use the proven continuation adapter pattern to satisfy the `r4`, `r8`, and `s17` register constraints before branching back to `0x001E9DE0`.

---

## 7. Provable Provenance and Input Hashes

All 16 read-only input dependencies were verified and remain strictly frozen:

| File Path | SHA-256 Hash | Status |
|---|---|:---:|
| `AGENTS.md` | `9a95c120bfd0d16d894713259f6df8bd743d415cdd1f2edbf4f6595ea9b194c9` | MATCH |
| `config/functions.csv` | `b27580ea4af85889e1167e7af5f898f66e82517c0293fcc3a586fea504a94be8` | MATCH |
| `config/game_info.json` | `5b9f1fa5114e9a460c9e2d7ca045d882c17ff8f93d70e358b1834141a0d4dbdd` | MATCH |
| `config/reconstruction.json` | `26cfcb7f84d1a879e99fc95548754b9ceb0ce0b9a814680d2f2888bbe78b888c` | MATCH |
| `docs/agent-work/h1-main-callback-editable-readiness.md` | `046ffdd4c44a9bb082a096756c39994079bb95532780a87d190a66eb3e0d2e47` | MATCH |
| `docs/agent-work/h1-menu-callback-map.md` | `4cc506086c6177d8f025b1dc8d004264ea3de68da14d9fa5ab90539055132783` | MATCH |
| `docs/agent-work/h1-title-message-source-bridge.md` | `bdd5bdf0e070bf1cfdb753a0ac8d20c47723cee35c3a4f256295c7dfb68ec507` | MATCH |
| `docs/agent-work/h1-title-message-symbol-abi-audit.md` | `aa854d82cd9d39c6040e1709c9a5c6ba4e0c4c058e33560396d050dce8d35fe6` | MATCH |
| `docs/agent-workflow.md` | `0cacc1c803e3206651e6ad67493510a9437b6a2303a76cb7910ce6515f85cc56` | MATCH |
| `docs/milestones/H1-main-menu-flow.md` | `ea5d8049c167792bf16f6bb1ed9ace95daaf316cd0e3b738186a6194b71bc063` | MATCH |
| `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` | MATCH |
| `src/camp/title_message.cpp` | `e7bd555a79858d546de1ad3fe6cfbbd8199a7ebe98e4d12067898a4395ef50f2` | MATCH |
| `src/camp/title_message.h` | `92b957ee845ff66061b44264da4e64f1d17068a3aaa5c57f9ca036e229e8ac4f` | MATCH |
| `src/engine/leaf_batch33_c.cpp` | `9235d238d06faa5e5fa52f18037302c2adc402d764c42d11147405906b75072c` | MATCH |
| `src/ui/ui_runtime2.cpp` | `ae46fd507efe1f3284e83dcb4ba5490b35cdaa5067b82676d01ac1401cb673a7` | MATCH |
| `tools/agent_workflow.py` | `b710b0ad59793e10292f818143f49d8155c00320dd14caba54e2a8db69af87bf` | MATCH |
