# Independent Review — H4 Map Entity Pool Contract (0x001B45E0)

**Task ID:** `h4-map-entity-pool-contract-review`  
**Review Target:** `docs/agent-work/h4-map-entity-pool-contract.md`  
**Reviewer:** `reviewer-1`  
**Date:** 2026-10-30  
**Status:** Approved  

---

## 1. Executive Summary

The contract report [`h4-map-entity-pool-contract.md`](h4-map-entity-pool-contract.md) accurately specifies the machine contract, array dimensions, resource disposal, and register usage for `0x001B45E0` (`Map_ClearEntityPool`, 132 bytes).

All 33 instructions from `0x001B45E0` to `0x001B465C` and the trailing literal word at `0x001B4660` were independently audited against `extracted/exefs/code.bin`. The contract accurately models:
1. Array base pointer `g_MapEntities` at `0x00447E70`.
2. Entity stride of 72 bytes (`0x48`) calculated via `(i * 9) << 3`.
3. Array capacity of 24 entries (`0x18`).
4. Resource disposal loop: testing `entity[i].resource` at `+0x3C`, calling `Resource_Release` (`0x002A7AA0`) when non-null, and zeroing the field.
5. State clearing loop: unrolled 2-step iteration zeroing byte `+0x14` across all 24 entities.

---

## 2. Independent Disassembly & Instruction Audit

- **Prologue & Epilogue:** Saves `{r4..r8, lr}` at `0x001B45E0` and restores `{r4..r8, pc}` at `0x001B465C`.
- **Loop 1 (`0x001B45F0..0x001B4620`):**
  - Increments `r4` from 0 to 23 (`cmp r4, #0x18; blt`).
  - Calls `0x002A7AA0` with `r0 = entity->resource` only when non-null.
  - Zeroes `entity->resource` using saved constant `r7 = 0`.
- **Loop 2 (`0x001B4624..0x001B4658`):**
  - Iterates 12 pairs (`add r0, r0, #2; cmp r0, #0x18; blt`).
  - Clears byte `+0x14` for `entity[2*k]` and `entity[2*k+1]`.

---

## 3. Recommendation

The contract is verified and complete. The task is **approved**. Proceed to C++ candidate implementation and offline differential verification.
