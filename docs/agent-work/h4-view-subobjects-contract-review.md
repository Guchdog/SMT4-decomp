# Independent Review — H4 View Subobjects Contract (0x001B481C)

**Task ID:** `h4-view-subobjects-contract-review`  
**Review Target:** `docs/agent-work/h4-view-subobjects-contract.md`  
**Reviewer:** `reviewer-1`  
**Date:** 2026-10-30  
**Status:** Approved  

---

## 1. Executive Summary

The reconnaissance report [`h4-view-subobjects-contract.md`](h4-view-subobjects-contract.md) accurately specifies the machine contract, register conventions, subobject bindings, branching logic, and caller integration points for function `0x001B481C` (`engine_func_001b481c`, 164 bytes).

All 41 ARM instructions from `0x001B481C` to `0x001B48B8` and the trailing literal pool at `0x001B48BC` were independently disassembled and audited against `extracted/exefs/code.bin`. The contract accurately identifies the object layout from `ViewCameraWork` (`0x00447E88`), the player model asset binding to `"player/pl01_00.bam"` via `0x00294A64`, and the 3-channel loops calling `0x00343E90` and `0x002946F4`.

---

## 2. Independent Disassembly & Register Audit

1. **Prologue & Initialization (`0x001B481C..0x001B4830`):**
   - `push {r4, r5, r6, lr}` preserves non-volatile registers.
   - `mov r1, #0x1c0` sets argument `0x1C0` (matching `sizeof(ViewCameraWork)`).
   - `ldr r5, =0x00447E88` loads the base pointer to `ViewCameraWork*`.
   - `ldr r0, [r5]` retrieves `work`.
   - `ldr r0, [r0, #0x194]` retrieves `work->subobject`.
   - `bl 0x00294A64`: Independent inspection confirms this callee takes `(subobject, 0x1C0)`, passes literal string `"player/pl01_00.bam"` to `0x0029A2D0`, sets flag word `+0x04 = 1`, and saves the asset handle into `+0x08`.

2. **Branching Logic (`0x001B4834..0x001B4848`):**
   - Re-reads `r0 = *g_ViewWork`.
   - Initializes iteration counter `r4 = 0`.
   - Reads `ldrb r0, [r0, #0x198]`.
   - Compares with 0:
     - If non-zero (`bne 0x001B485C`), branches directly into the Loop 1 entry.
     - If zero, branches (`b 0x001B4898`) into the Loop 2 entry.

3. **Loop 1 (`work->field_198 != 0`):**
   - Condition block `0x001B484C..0x001B4858`:
     `cmp r4, #0; cmpne r4, #1; cmpne r4, #2; bne 0x001B4860`.
     Since `r4` is strictly in `{0, 1, 2}`, the condition is always met, guaranteeing `mov r3, #0x1c0` is executed for every iteration.
   - Arguments to `bl 0x00343E90`:
     - `r0`: `work->subobject` (from `[r0, #0x194]`).
     - `r1`: `r4 & 0xFF` (channel index `0, 1, 2`).
     - `r2`: `work->sub_channels[i]` (from `[r0, +0x19C + i*4]`).
     - `r3`: `0x1C0`.
   - Counter increments by 1; loops while `r4 < 3`.
   - Epilogue restores `{r4, r5, r6, pc}`.

4. **Loop 2 (`work->field_198 == 0`):**
   - Condition block `0x001B4888..0x001B4894`:
     Similarly guarantees `mov r2, #0x1c0` for all iterations `0, 1, 2`.
   - Arguments to `bl 0x002946F4`:
     - `r0`: `work->subobject`.
     - `r1`: `r4 & 0xFF` (channel index `0, 1, 2`).
     - `r2`: `0x1C0`.
   - Counter increments by 1; loops while `r4 < 3`.
   - Epilogue restores `{r4, r5, r6, pc}`.

---

## 3. Caller Context Verification

- Call site 1 (`0x001B8BA4`): Invoked immediately prior to `0x0021B9F8` and `0x00208C28` during scene creation.
- Call site 2 (`0x001BF528`): Invoked following camera state reset `0x001B41E0` and scene counter increment `[r4 + 0x24]++`.
- Both call sites confirm that `0x001B481C` is called without parameters and its return value is discarded.

---

## 4. Recommendation

The contract is verified and complete. The task is **approved**. Proceed to C++ implementation (`h4-view-subobjects-candidate`) and offline differential verification.
