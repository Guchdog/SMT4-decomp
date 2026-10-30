# H4 View Subobjects Contract — Static ARM Reconnaissance

**Task ID:** `h4-view-subobjects-contract`  
**Address:** `0x001B481C` (164 bytes, 41 ARM instructions)  
**Assigned Owner:** `worker-1`  
**Reference Binary:** `extracted/exefs/code.bin` (SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`)  
**Date:** 2026-10-30  

---

## 1. Overview and Scope

This document specifies the exact contract, control flow, register conventions, subobject layout, and caller interactions for function `0x001B481C` (`engine_func_001b481c`).

`0x001B481C` operates on the active field camera / view workspace located via the global pointer `g_ViewWork` at `0x00447E88`. It binds the protagonist model asset (`player/pl01_00.bam`) to the view subobject at `work->subobject` (`+0x194`), queries channel mode configuration (`work->field_198`), and invokes three-channel setup routines across channels 0, 1, and 2.

---

## 2. Global Dependencies and Calling Convention

- **Calling Convention:** Standard AAPCS (`void engine_func_001b481c(void)`).
- **Parameters:** None (`void`).
- **Return Value:** None (`void`; `r0` is not used as a functional return).
- **Callee-saved Registers Preserved:** `r4`, `r5`, `r6`, `lr` (pushed at `0x001B481C`, restored at `0x001B4884` and `0x001B48B8`).
- **Global Pointer Targets:**
  - `0x00447E88`: Global pointer to `ViewCameraWork` (heap structure, size `0x1C0`).
- **Callees Invoked:**
  - `0x00294A64`: Subobject player asset initializer (`void sub_00294A64(void* subobj, u32 param)`).
    - Disassembly shows it passes string `"player/pl01_00.bam"` to `0x0029A2D0`, sets flag `subobj[+0x04] = 1`, and stores resource handle into `subobj[+0x08]`.
  - `0x00343E90`: Active channel configurator (`void sub_00343E90(void* subobj, u32 channel_idx, u32 channel_val, u32 size_param)`).
    - Called when `work->field_198 != 0`.
  - `0x002946F4`: Default channel configurator (`void sub_002946F4(void* subobj, u32 channel_idx, u32 size_param)`).
    - Called when `work->field_198 == 0`.

---

## 3. Disassembly and Instruction-Level Trace

```arm
0x001B481C: push {r4, r5, r6, lr}
0x001B4820: mov r1, #0x1c0
0x001B4824: ldr r5, [pc, #0x90]        ; [0x001B48BC] = 0x00447E88 (g_ViewWork)
0x001B4828: ldr r0, [r5]              ; r0 = *g_ViewWork
0x001B482C: ldr r0, [r0, #0x194]       ; r0 = work->subobject
0x001B4830: bl #0x294a64               ; sub_00294A64(work->subobject, 0x1C0)
0x001B4834: ldr r0, [r5]              ; r0 = *g_ViewWork
0x001B4838: mov r4, #0                 ; r4 = i = 0
0x001B483C: ldrb r0, [r0, #0x198]      ; r0 = work->field_198
0x001B4840: cmp r0, #0
0x001B4844: bne #0x1b485c              ; if (work->field_198 != 0) goto Loop 1 entry
0x001B4848: b #0x1b4898                ; else goto Loop 2 entry

; --- Loop 1 (work->field_198 != 0) ---
0x001B484C: cmp r4, #0
0x001B4850: cmpne r4, #1
0x001B4854: cmpne r4, #2
0x001B4858: bne #0x1b4860
0x001B485C: mov r3, #0x1c0             ; r3 = 0x1C0 (constant for i in {0, 1, 2})
0x001B4860: ldr r0, [r5]              ; r0 = *g_ViewWork
0x001B4864: and r1, r4, #0xff         ; r1 = (u8)i
0x001B4868: add r2, r0, r4, lsl #2    ; r2 = (u8*)work + i * 4
0x001B486C: ldr r0, [r0, #0x194]      ; r0 = work->subobject
0x001B4870: ldr r2, [r2, #0x19c]      ; r2 = work->sub_channels[i]
0x001B4874: bl #0x343e90              ; sub_00343E90(work->subobject, i, work->sub_channels[i], 0x1C0)
0x001B4878: add r4, r4, #1            ; i++
0x001B487C: cmp r4, #3
0x001B4880: blt #0x1b484c              ; if (i < 3) loop
0x001B4884: pop {r4, r5, r6, pc}      ; return

; --- Loop 2 (work->field_198 == 0) ---
0x001B4888: cmp r4, #0
0x001B488C: cmpne r4, #1
0x001B4890: cmpne r4, #2
0x001B4894: bne #0x1b489c
0x001B4898: mov r2, #0x1c0             ; r2 = 0x1C0 (constant for i in {0, 1, 2})
0x001B489C: ldr r0, [r5]              ; r0 = *g_ViewWork
0x001B48A0: and r1, r4, #0xff         ; r1 = (u8)i
0x001B48A4: ldr r0, [r0, #0x194]      ; r0 = work->subobject
0x001B48A8: bl #0x2946f4              ; sub_002946F4(work->subobject, i, 0x1C0)
0x001B48AC: add r4, r4, #1            ; i++
0x001B48B0: cmp r4, #3
0x001B48B4: blt #0x1b4888              ; if (i < 3) loop
0x001B48B8: pop {r4, r5, r6, pc}      ; return

; --- Literal Pool ---
0x001B48BC: .word 0x00447E88          ; pointer to g_ViewWork
```

---

## 4. Contract Analysis & Invariants

1. **Object Pointer Dereference:**
   - The function assumes `*[0x00447E88]` is non-null and valid.
   - `work->subobject` at `+0x194` is passed as the `this` / object pointer to all three callees (`0x00294A64`, `0x00343E90`, `0x002946F4`).

2. **Branching on `work->field_198`:**
   - Byte `+0x198` distinguishes two setup paths:
     - Non-zero (`work->field_198 != 0`): Parameterized setup pulling three words from `work->sub_channels` (`+0x19C`, `+0x1A0`, `+0x1A4`).
     - Zero (`work->field_198 == 0`): Default channel configuration via `0x002946F4`.

3. **Loop Bounds & Register Arguments:**
   - Both loops execute exactly 3 times for indices `i = 0, 1, 2`.
   - Condition chain `cmp r4, #0; cmpne r4, #1; cmpne r4, #2; bne ...` evaluates true for all `i in {0, 1, 2}`, guaranteeing that:
     - In Loop 1: `r3 = 0x1C0` (the size of `ViewCameraWork`) is always passed to `0x00343E90`.
     - In Loop 2: `r2 = 0x1C0` is always passed to `0x002946F4`.

---

## 5. FlowScript Caller Integration

Disassembly of caller sites confirms the exact role of `0x001B481C` in the field lifecycle:
1. `0x001B8BA4`:
   - Follows field initialization checks and precedes `0x0021B9F8` and `0x00208C28` (`Map_Field3DManager` initialization sequence).
2. `0x001BF528`:
   - Follows camera reset `0x001B41E0` and counter increment `[r4 + 0x24]++` during field / zone transitions.

Both call sites demonstrate that `0x001B481C` is the canonical subobject / actor asset binder invoked during scene entry.
