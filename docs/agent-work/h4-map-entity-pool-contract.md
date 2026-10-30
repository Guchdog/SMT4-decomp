# H4 Map Entity Pool Contract — Static ARM Reconnaissance

**Task ID:** `h4-map-entity-pool-contract`  
**Address:** `0x001B45E0` (132 bytes, 32 ARM instructions + 1 literal word)  
**Assigned Owner:** `worker-1`  
**Reference Binary:** `extracted/exefs/code.bin` (SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`)  
**Date:** 2026-10-30  

---

## 1. Overview and Scope

This document specifies the contract, memory layout, loop iteration, and resource destruction for function `0x001B45E0` (`Map_ClearEntityPool`, currently registered as `script_vm_func_001b45e0` in `src/engine/leaf_batch26_a.cpp`).

`0x001B45E0` clears and resets the 24-entry field entity/event pool located via `g_MapEntities` at `0x00447E70`. For each entity, it releases allocated resources at offset `+0x3C` through helper `0x002A7AA0` (`Resource_Release`), zeroes the resource pointer, and clears state byte `+0x14`.

---

## 2. Global Dependencies and Calling Convention

- **Calling Convention:** Standard AAPCS (`void Map_ClearEntityPool(void)`).
- **Parameters:** None (`void`).
- **Return Value:** None (`void`).
- **Callee-saved Registers Preserved:** `r4`, `r5`, `r6`, `r7`, `r8`, `lr`.
- **Global Pointer Targets:**
  - `0x00447E70`: Global pointer `g_MapEntities` to the 24-entry entity array.
- **Callees Invoked:**
  - `0x002A7AA0`: `void Resource_Release(void* resource)` (called if `entity->resource != nullptr`).

---

## 3. Disassembly and Instruction-Level Trace

```arm
0x001B45E0: push {r4, r5, r6, r7, r8, lr}
0x001B45E4: mov r4, #0                 ; r4 = i = 0
0x001B45E8: mov r7, r4                 ; r7 = 0
0x001B45EC: ldr r6, [pc, #0x6c]        ; [0x001B4660] = 0x00447E70 (g_MapEntities)

; --- Loop 1: Resource Release Loop (24 iterations) ---
0x001B45F0: add r5, r4, r4, lsl #3     ; r5 = i * 9
0x001B45F4: ldr r0, [r6]               ; r0 = *g_MapEntities
0x001B45F8: add r0, r0, r5, lsl #3     ; r0 = entity = *g_MapEntities + i * 72
0x001B45FC: ldr r0, [r0, #0x3c]        ; r0 = entity->resource
0x001B4600: cmp r0, #0
0x001B4604: beq #0x1b4618              ; if (!entity->resource) skip release
0x001B4608: bl #0x2a7aa0               ; Resource_Release(entity->resource)
0x001B460C: ldr r0, [r6]
0x001B4610: add r0, r0, r5, lsl #3
0x001B4614: str r7, [r0, #0x3c]        ; entity->resource = nullptr
0x001B4618: add r4, r4, #1             ; i++
0x001B461C: cmp r4, #0x18              ; i < 24
0x001B4620: blt #0x1b45f0

; --- Loop 2: Unrolled State Reset Loop (12 steps of 2 entries) ---
0x001B4624: ldr r2, [r6]               ; r2 = *g_MapEntities
0x001B4628: mov r1, #0                 ; r1 = j = 0
0x001B462C: mov r0, r1                 ; r0 = count = 0
0x001B4630: add r3, r1, r1, lsl #3     ; r3 = j * 9
0x001B4634: add r1, r1, #1             ; j++
0x001B4638: add r3, r2, r3, lsl #3     ; r3 = &entity[j-1]
0x001B463C: add ip, r1, r1, lsl #3     ; ip = j * 9
0x001B4640: add r0, r0, #2             ; count += 2
0x001B4644: add ip, r2, ip, lsl #3     ; ip = &entity[j]
0x001B4648: strb r7, [r3, #0x14]       ; entity[j-1].state_14 = 0
0x001B464C: cmp r0, #0x18              ; count < 24
0x001B4650: add r1, r1, #1             ; j++
0x001B4654: strb r7, [ip, #0x14]       ; entity[j].state_14 = 0
0x001B4658: blt #0x1b4630

0x001B465C: pop {r4, r5, r6, r7, r8, pc} ; return
0x001B4660: .word 0x00447E70           ; literal pointer to g_MapEntities
```

---

## 4. Contract Analysis & Invariants

1. **Entity Stride and Count:**
   - Calculation `(i * 9) << 3 = i * 72` establishes that each entity is exactly 72 bytes (`0x48`).
   - Constant `0x18` defines the capacity of the active map entity pool as 24 entries.
2. **Entity Layout (`MapEntity`):**
   - Size: 72 bytes (`0x48`).
   - `+0x14`: Byte state / active flag.
   - `+0x3C`: Pointer to attached resource (cleared on map exit or scene reset).
3. **Callee Invocation:**
   - `0x002A7AA0` is only invoked when `entity->resource != nullptr`.
   - After return, `entity->resource` is unconditionally set to 0.
