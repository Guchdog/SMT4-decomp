# Independent Review — H4 Map Player Actor Contract (0x001B45C8)

**Task ID:** `h4-map-player-actor-contract-review`  
**Review Target:** `docs/agent-work/h4-map-player-actor-contract.md`  
**Reviewer:** `reviewer-1`  
**Date:** 2026-10-30  
**Status:** Approved  

---

## 1. Executive Summary

The contract report [`h4-map-player-actor-contract.md`](h4-map-player-actor-contract.md) accurately specifies the machine contract, register conventions, and dispatch integration for `0x001B45C8` (`Map_GetPlayerActor`, 20 bytes).

All instructions from `0x001B45C8` to `0x001B45D8` and the literal at `0x001B45DC` were independently disassembled and verified against `extracted/exefs/code.bin`. The contract accurately models:
1. Double-dereference of `g_MapMainWork` (`0x00447E28`) to extract the 32-bit player handle at offset `+0x00`.
2. Setting parameter `r1 = 0`.
3. Tail-call dispatch via `b 0x002C45B8` (`ActorManager_Lookup`).
4. Table binding at index 19 in `0x00446E00`.

---

## 2. Independent Disassembly & Instruction Audit

- `0x001B45C8: ldr r0, [pc, #0xc]`: Correctly targets `0x001B45DC` containing `0x00447E28`.
- `0x001B45CC: mov r1, #0`: Sets second parameter to zero.
- `0x001B45D0: ldr r0, [r0]`: Dereferences `g_MapMainWork`.
- `0x001B45D4: ldr r0, [r0]`: Dereferences the workspace pointer to load word at offset `+0x00` (player actor handle).
- `0x001B45D8: b 0x002C45B8`: Direct branch tail-call to `ActorManager_Lookup(handle, 0)`.
- No stack frame allocation; callee-saved registers `r4..r11` and `lr` are preserved across the routine.

---

## 3. Recommendation

The contract is verified and complete. The task is **approved**. Proceed to C++ candidate implementation and offline differential verification.
