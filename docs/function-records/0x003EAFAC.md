# `func_003eafac` (0x003EAFAC)

## Summary
- **Address:** `0x003EAFAC`
- **Size:** 20 bytes
- **Domain:** Utility / Intrusive Singly Linked List Insertion
- **Status:** Semantically verified (`non_matching` in ledger)
- **Source File:** `src/engine/leaf_batch31_a.cpp`
- **Differential Suite:** `tools/batch31_a_part1_experiment.py`

## Role and Behavior
- **Role:** Checks pointer `p1`. If non-null, delegates to intrusive list push routine `func_002a3428(p0 + 1, p1)`. If null, returns immediately.
- **Calling Interface:**
  - `func_002a3428`: list push routine inserting node `p1` at head pointer `p0[1]`.

## Differential Verification
- Validated via Unicorn CPU emulation against original ARM instructions.
- Test matrix:
  - `p1 == nullptr` -> returns without calling `func_002a3428`.
  - `p1 != nullptr` -> calls `func_002a3428(p0 + 1, p1)`.
- 100% equivalence verified across all test cases.
