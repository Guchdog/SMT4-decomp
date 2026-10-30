# H4 View Initialization Candidate — 0x001B4664

**Task ID:** `h4-view-init-candidate`  
**Address:** `0x001B4664` (440 bytes)  
**Candidate Source:** `experiments/semantic_equivalence/h4_view_init_candidate.cpp` (SHA-256: `3bae23d47aff7e712082817481efd6ef850be7d10c54318396b742424d15da2b`)  
**Runner:** `tools/h4_view_init_experiment.py` (SHA-256: `76098bc27be6d7fa658eae52fdca0b490680f256986d20da7d9f99608334b4f4`)  
**Date:** 2026-10-30  

---

## 1. Result

Offline ARM differential validation **PASSED**: The compiled C++ candidate for `0x001B4664` was compared directly against the retail ARM assembly across 9 diverse fixtures (zero fill, pattern fills `0xA5`, `0x5A`, `0xFF`, multiple pseudo-random noise memory initializations, and null-allocator failure branches).

- **Total Fixtures:** 9
- **Memory Differences:** 0 (100% byte equivalence across all `0x1C0` bytes of `ViewCameraWork` and `0x50` bytes of the global repeat gate `0x0049F91C`)
- **Register Equivalence:** Preserved registers `r4-r11` and `sp` matched across all runs.
- **Mutation Control:** Same-input compiled mutation (`sentinel_id` changed from `-1` to `0`) was positively detected by the harness.

---

## 2. Technical Evidence and Reproducibility

- **Reference Image:** `extracted/exefs/code.bin` (SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- **Command:** `python tools/h4_view_init_experiment.py --out-dir build/agent-work/H4-semantic/h4-view-init-candidate/001/output` (exit code: 0).
- **Report Path:** `build/agent-work/H4-semantic/h4-view-init-candidate/001/output/report.json` (SHA-256: `f33b9366be25eca116ceddae4c73b02f11f72723e2f369d01dc25872798c8e0a`).
- **Candidate Size:** 396 bytes (original: 440 bytes; fits without relocation overflow).
- **Relocations:** Standard AAPCS BL relocations for `AsdMem_Alloc_002c23f8` (0x002C23F8) and `ui_subobject_constructor_00294a98` (0x00294A98).

---

## 3. Scope and Limitations

This offline test establishes memory-level initialization equivalence for `0x001B4664` and the repeat gate. Upstream caller FlowScript integration and subsequent frame update routines (`0x002E8F9C`) remain separate tasks.
