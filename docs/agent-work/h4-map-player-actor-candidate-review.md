# Independent Review — H4 Map Player Actor Candidate (0x001B45C8)

**Task ID:** `h4-map-player-actor-candidate-review`  
**Review Target:** `docs/agent-work/h4-map-player-actor-candidate.md`  
**Candidate Source:** `experiments/semantic_equivalence/h4_map_player_actor_candidate.cpp`  
**Reviewer:** `reviewer-1`  
**Date:** 2026-10-30  
**Status:** Approved  

---

## 1. Executive Summary

The semantic C++ candidate implementation for `0x001B45C8` (`h4_map_player_actor_candidate.cpp`) has been independently audited and verified. The candidate reconstructs the player actor handle extraction from `*g_MapMainWork` (`0x00447E28`) and tail-call lookup via `ActorManager_Lookup(handle, 0)` at `0x002C45B8`.

Independent execution of the differential test harness [`tools/h4_map_player_actor_experiment.py`](../../tools/h4_map_player_actor_experiment.py) confirmed:
- Zero register differences across `r4..r11`.
- Zero stack pointer delta.
- Identical return values in `r0` and identical argument tuples passed to `ActorManager_Lookup`.
- Successful negative control detection via compiled mutation routine `h4_map_player_actor_mutation`.
- Replacement binary footprint of 24 bytes, strictly matching original function extent.

---

## 2. Independent Code Audit

1. **Object Layout and Type Safety:**
   - `MapMainWork` layout declares `player_actor_handle` at offset `+0x00`, verified via `static_assert(offsetof(MapMainWork, player_actor_handle) == 0x00)`.
   - Access strictly models `*g_MapMainWork` pointer semantics.
2. **Tail-Call Optimization:**
   - Compiler generates `b #target` tail-call rather than allocating an unnecessary stack frame, matching original binary AAPCS behavior.
3. **Absence of Undefined Behavior:**
   - Handles are unsigned 32-bit values without sign truncation.

---

## 3. Independent Verification Run

Re-execution of `tools/h4_map_player_actor_experiment.py` reproduced the reported results deterministically:
```json
{
  "status": "passed",
  "fixtures_tested": 6,
  "mutation_detected": true,
  "candidate_bytes": 24,
  "original_bytes": 24,
  "candidate_sha256": "7c38d5db520054ca39fb1e184d0f21f6587f15dd7c4b5c685fb011ffa8f7dc43"
}
```

---

## 4. Recommendation

The candidate is **approved** and recommended for inclusion in the integrated H4 candidate collection.
