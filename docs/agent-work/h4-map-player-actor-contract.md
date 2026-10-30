# H4 Map Player Actor Contract — Static ARM Reconnaissance

**Task ID:** `h4-map-player-actor-contract`  
**Address:** `0x001B45C8` (20 bytes, 5 instructions + 1 literal word)  
**Assigned Owner:** `worker-1`  
**Reference Binary:** `extracted/exefs/code.bin` (SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`)  
**Date:** 2026-10-30  

---

## 1. Overview and Scope

This document specifies the contract, register usage, memory accesses, and caller dispatch for `0x001B45C8` (`Map_GetPlayerActor`).

`0x001B45C8` retrieves the active player actor handle from the global map manager workspace `g_MapMainWork` at `0x00447E28` and performs a tail-call lookup via the actor manager helper `0x002C45B8` (`ActorManager_Lookup`) with mode `0`.

---

## 2. Global Dependencies and Calling Convention

- **Calling Convention:** Standard AAPCS (`void* Map_GetPlayerActor(void)`).
- **Parameters:** None (`void`).
- **Return Value:** Pointer to the resolved player actor structure in `r0` (or `nullptr` if lookup fails or handle is 0).
- **Registers Used:** `r0`, `r1` (scratch). Callee-saved registers `r4..r11` and `lr` are untouched.
- **Global Pointer Targets:**
  - `0x00447E28`: Global pointer `g_MapMainWork` pointing to the heap-allocated map workspace (allocated in `0x001B4410`).
- **Callees Invoked:**
  - `0x002C45B8`: `ActorManager_Lookup(u32 handle, u32 mode)` (tail-called via branch `b #0x2C45B8`).

---

## 3. Disassembly and Instruction-Level Trace

```arm
0x001B45C8: ldr r0, [pc, #0xc]        ; [0x001B45DC] = 0x00447E28 (g_MapMainWork)
0x001B45CC: mov r1, #0                ; r1 = 0 (mode parameter)
0x001B45D0: ldr r0, [r0]              ; r0 = *g_MapMainWork
0x001B45D4: ldr r0, [r0]              ; r0 = (*g_MapMainWork)->player_actor_handle (offset +0x00)
0x001B45D8: b #0x2c45b8               ; tail-call ActorManager_Lookup(player_handle, 0)
0x001B45DC: .word 0x00447E28          ; literal pointer to g_MapMainWork
```

---

## 4. Contract Analysis & Invariants

1. **Handle Extraction:**
   - Offset `+0x00` in the map workspace pointed to by `*g_MapMainWork` holds the 32-bit handle for the protagonist actor.
2. **Actor Table Lookup (`0x002C45B8`):**
   - If `handle == 0`, `0x002C45B8` immediately returns `0` (`cmp r0, #0; bxeq lr`).
   - If `handle != 0`, `0x002C45B8` decomposes the handle into table index (`handle >> 20`) and generational tag (`handle & 0xFFFFF`), traverses the hash bucket chain, and returns the resolved actor pointer in `r0`.
3. **FlowScript Dispatch Table:**
   - Registered at index 19 (offset `+0x4C`) in table `0x00446E00`, bound via `0x0010E560`.
   - Used by field scripts and cutscenes to query Flynn's actor object for coordinates, direction, and interaction status.
