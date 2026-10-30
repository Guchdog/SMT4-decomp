# Independent Review — H4 View Subobjects Candidate (0x001B481C)

**Task ID:** `h4-view-subobjects-candidate-review`  
**Review Target:** `docs/agent-work/h4-view-subobjects-candidate.md`  
**Candidate Source:** `experiments/semantic_equivalence/h4_view_subobjects_candidate.cpp`  
**Reviewer:** `reviewer-1`  
**Date:** 2026-10-30  
**Status:** Approved  

---

## 1. Executive Summary

The semantic C++ candidate implementation for `0x001B481C` (`h4_view_subobjects_candidate.cpp`) has been independently audited and verified. The candidate reconstructs the view subobject player asset binding (`player/pl01_00.bam` via `0x00294A64`), channel configuration branching via `work->field_198`, and 3-channel setup iterations.

Independent execution of the differential test harness [`tools/h4_view_subobjects_experiment.py`](../../tools/h4_view_subobjects_experiment.py) confirmed:
- Zero register differences across `r4..r11`.
- Zero stack pointer delta.
- Identical invocation sequences and argument tuples for all four function calls per execution.
- Successful negative control detection via the compiled mutation routine.
- Replacement code size of 156 bytes, within the original 164-byte function boundary.

---

## 2. Independent Code Audit

1. **Object Layout and Type Safety:**
   - `ViewCameraWork` layout conforms to the reviewed contract (`docs/agent-work/h4-view-subobjects-contract.md`), verified via `static_assert(sizeof(ViewCameraWork) == 0x1C0)`.
   - Accesses to `subobject` (`+0x194`), `field_198` (`+0x198`), and `sub_channels` (`+0x19C..0x1B0`) utilize strictly typed struct member access without arbitrary pointer casts.

2. **Branching & Tail Recursion / Optimization:**
   - Clang unrolls the 3-iteration loop cleanly, producing specialized instructions for each channel index `0, 1, 2` and tail-calling the final channel invocation (`b #target`), matching AAPCS requirements.

3. **Absence of Undefined Behavior:**
   - Channel index conversions `static_cast<u8>(i)` prevent sign extension.
   - Pointers passed to callees (`work->subobject`) are non-null heap references guaranteed by the view initialization lifecycle.

---

## 3. Independent Verification Run

Re-execution of `tools/h4_view_subobjects_experiment.py` reproduced the reported results deterministically:
```json
{
  "status": "passed",
  "fixtures_tested": 6,
  "mutation_detected": true,
  "candidate_bytes": 156,
  "original_bytes": 164,
  "candidate_sha256": "6a7fcae5ffa1079800788b5560ba9ec7f7edd8d6a52787f33c71d124e64fe416"
}
```

---

## 4. Recommendation

The candidate is **approved** and recommended for inclusion in the integrated H4 candidate collection.
