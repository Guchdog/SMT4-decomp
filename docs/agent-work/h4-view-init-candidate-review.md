# Independent Review: H4 View Initialization Candidate

**Task ID:** `h4-view-init-candidate-review`  
**Reviewer:** `h4_impl_reviewer`  
**Target:** `experiments/semantic_equivalence/h4_view_init_candidate.cpp` and `tools/h4_view_init_experiment.py`  
**Date:** 2026-10-30  

---

## 1. Scope and Objective

This review independently evaluates the C++ candidate implementation for `0x001B4664` (`h4_view_init_candidate.cpp`), its struct-level memory layout, and the 9-fixture offline ARM differential suite.

---

## 2. Integrity and Provenance Verification

- **Candidate Source (`experiments/semantic_equivalence/h4_view_init_candidate.cpp`):**  
  SHA-256: `3bae23d47aff7e712082817481efd6ef850be7d10c54318396b742424d15da2b`
- **Harness Runner (`tools/h4_view_init_experiment.py`):**  
  SHA-256: `76098bc27be6d7fa658eae52fdca0b490680f256986d20da7d9f99608334b4f4`
- **Differential Report (`build/agent-work/H4-semantic/h4-view-init-candidate/001/output/report.json`):**  
  SHA-256: `f33b9366be25eca116ceddae4c73b02f11f72723e2f369d01dc25872798c8e0a`
- **Candidate Size:** 396 bytes, comfortably within the original 440-byte allocation budget.

---

## 3. Code Quality and Type Safety

- The candidate defines `ViewCameraWork` with explicit compile-time offset assertions (`static_assert(offsetof(...))`) covering every mapped field.
- Eliminates raw pointer arithmetic in favor of structured field assignments.
- Preserves exact AAPCS calling convention and branch linking for external dependencies (`0x002C23F8` and `0x00294A98`).
- Handles the null allocation branch (`sub == nullptr`) safely, reproducing the retail conditional branch (`0x001B4730: beq #0x1b4740`).

---

## 4. Differential Verification

- All 9 fixtures (zero fill, pattern fills `0xA5`, `0x5A`, `0xFF`, multiple random noise buffers, and null allocation paths) produced 0 memory differences across all `0x1C0` bytes of `ViewCameraWork` and `0x50` bytes of the repeat gate.
- Preserved registers `r4-r11` and `sp` were byte-identical across original and candidate executions.
- The mutation control (`sentinel_id` changed from `-1` to `0`) was positively detected.

---

## 5. Recommendation

**ACCEPT.** The C++ implementation faithfully reproduces the semantic memory effects of `0x001B4664`.
