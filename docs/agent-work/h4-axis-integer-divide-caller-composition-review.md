# Independent Review: H4 Integer-Divider Caller Composition

**Task ID:** `h4-axis-integer-divide-caller-composition-review`  
**Reviewer:** `h4_composition_reviewer`  
**Target:** `tools/h4_axis_integer_divide_caller_composition.py` and `docs/agent-work/h4-axis-integer-divide-caller-composition.md`  
**Date:** 2026-10-30  

---

## 1. Scope and Objective

This review independently evaluates the caller composition evidence of the experimental C++ integer division helper (`0x002C615C`, `h4_integer_divide_candidate.cpp`) composed under the two original calibration caller functions:
- `0x0013B9FC` (selector 0: radial fixed-point scaling)
- `0x0013B8F8` (selector 1: threshold deadzone scaling)

The objective is to verify that replacing the original 556-byte helper with the compiled 128-byte candidate preserves observable caller behavior across all synthetic fixtures without unintended side effects.

---

## 2. Integrity and Provenance Verification

All input files and generated artifacts were independently recomputed:

- **Reference Image (`extracted/exefs/code.bin`):**  
  SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` (matches pinned ledger).
- **Candidate Source (`experiments/semantic_equivalence/h4_integer_divide_candidate.cpp`):**  
  SHA-256: `970e00f3c6bf8e350f935158b5b8bab46919f257418f5efb0174d2b19e8da96b`.
- **Harness Runner (`tools/h4_axis_integer_divide_caller_composition.py`):**  
  SHA-256: `bda16622e7efda91dc1b11fc15b2fcbbf38d5f8b16143ea7d6e37b5a3b106fd5`.
- **Composition Report (`build/agent-work/H4-semantic/h4-axis-integer-divide-caller-composition/003/output/report.json`):**  
  SHA-256: `936ee8b8b415e77a6ebfee662d09d2db0d23322ddbc8fb5efd38211639b9694a`.
- **Candidate Object Body:**  
  128 bytes, 0 relocations, verified replacement range `[0x002C615C, 0x002C6388)` padded with ARM NOPs (`0xE1A00000`).

---

## 3. Findings and Technical Analysis

1. **Equivalence Across Tested Fixtures:**  
   The suite executed 1,982 cases (991 per caller):
   - 847 systematic grid cases covering positive, negative, zero, deadzone thresholds (±36, ±40), and signed 16-bit extrema (-32768, 32767).
   - 16 memory alias and null pointer cases ('same', 'swapped', 'x-null', 'y-null').
   - 128 deterministic pseudo-random cases per caller (seed `20261028`).
   All 1,982 cases yielded zero compared differences in `r0`, `r1`, `sp`, `r4-r11`, `output` buffer snapshot, and non-stack memory writes.

2. **Fault and Exception Handling:**  
   The 16 invalid null-output pointer test cases produced identical faults in both original and candidate images (`Invalid memory read/write`) at the exact same faulting instruction PC. Zero unmatched faults occurred.

3. **Sensitivity and Negative Control:**  
   The same-input mutation control (flipping bit 0 in the zero-divisor quotient return) reliably exercised the zero-divisor code path (`div_calls` with divisor 0) and was detected in both selector 0 and selector 1 caller outputs.

4. **Documented Exclusions and Differences:**  
   - Stack writes differ in quantity (15,230 vs 21,138 for selector 0; 11,426 vs 16,082 for selector 1) due to standard prologue/epilogue and spill differences between the retail assembly and modern clang compilation. These are correctly tracked, segregated, and excluded from equivalence criteria.
   - CPU condition flags are not preserved across calls, which adheres to AAPCS requirements where caller-saved condition codes need not match.

---

## 4. Limitations

- **Synthetic Domain:** The fixtures use synthetic signed halfword inputs. Actual in-game calibration structures and coordinate distributions from hardware sensors remain to be verified at runtime.
- **Scope Restriction:** This composition validates the integer divider helper under its callers; it does not constitute full reconstruction of the callers themselves or the upstream input producer / camera pipeline.

---

## 5. Recommendation

**ACCEPT.** The composition harness and evidence satisfy all acceptance criteria of `h4-axis-integer-divide-caller-composition`. The experimental candidate `0x002C615C` is verified under caller functions `0x0013B9FC` and `0x0013B8F8` offline.
