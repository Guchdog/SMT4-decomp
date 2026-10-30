# Independent review: H4 axis reader at 0x0027FBC8

## Scope and provenance

Reviewed the frozen `h4-axis-reader-review/run-001` packet and verified all 14 declared input SHA-256 values. Reference image: `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Candidate SHA-256 `108b45003ec4908630514b615be7ebe6911fddb83c7448e4a8dacc403dd85aca`; runner SHA-256 `312a2e27211cd3a53784a0b6d8bc918167aef3f71ec8732659d05b9a0f9d9a31`. The two pinned reports are `seed-7/report.json` SHA-256 `ff56fb1b4cf38d902725957d9847d1d10a99129693ddf56ed84b2792536f88ee` and `seed-20261028/report.json` SHA-256 `f0f33937d6fde6774617efd43d51174b623d8eeb33b4510f7a4f4422f68a5cab`. No build, test rerun, or emulator session was performed.

## Original contract and caller evidence

The direct harness executes pinned ARM function `0x0027FBC8` from the reference image and the compiled candidate in separate fresh Unicorn instances with the same generated memory/register setup. The caller record identifies the live mode-0 call at `0x001FA948` inside `0x001FA840`, with helper entry `(r0,r1,r2,r3)=(0x0FFFFCB4,0x0FFFFCB0,0,250.0f)`, LR `0x001FA94C`, and adjacent stack output slots. That is useful observed ABI context, but it is not composed with this candidate in the direct tests.

The candidate's C ABI is consistent with the observed direct helper contract: nullable output pointers in r0/r1, unsigned mode in r2, integer result in r0, and hard-float ARM/VFP handling for its `float` dependency. The runner accepts exactly two `R_ARM_CALL` relocations to `h4_original_deadzone`, checks ARM BL encodings and address alignment/range, and links those calls to the original `0x0019FE4C`. The original implementation and dependency execute from the same pinned code image. The original function also reads calibration before checking invalid mode; the candidate does the same. The source and field-control record agree on selector mapping, mode bounds, source selection, signed input samples, division by the selected signed span, nonzero-threshold deadzone calls, and delayed nullable output writes.

## Directed and randomized coverage

Both reports use the same candidate, object, and linked candidate bytes (object SHA-256 `82c0589a66d61818c9a99776d2e6a208beeedd4c574ace6fbc272253d59cf039`; linked candidate SHA-256 `68bff63e771d574e2ef1bfec4fddecc1fd6c08518424bddc58fcb87e40d34dd6`). Each reports 119 cases, zero differences, and no first counterexample: 19 fixed directed cases plus 100 PRNG cases. The directed set is recoverable from the frozen harness: modes 0/1/2/`0xFFFFFFFF`; selectors 0/1/2/255; mode-1 limit 0; alternate source; all four output-null combinations; thresholds 0.01/0.25/1.0/−0.25; and one zero-span case with nonzero numerators. The 100 random cases use selectors 0..2, modes 0..1, both source flags, thresholds 0/0.1/0.5, and full-range signed 16-bit samples. The two seeds therefore contribute 238 executions, not 238 distinct directed categories.

For each case, the comparator checks integer return, a 16-byte output region initialized to sentinel bytes, recorded deadzone entry threshold/value calls, and reaching the return sentinel. The candidate reports no differences for either seed. The fixed cases do exercise neutral threshold-zero return/write behavior, nonzero-threshold all-zero rejection, signed source extremes, invalid modes, and zero denominator. The reports also pin reference, candidate, runner, and object identities.

## Harness and negative-control audit

The existing negative control does **not** mutate the candidate. It compares original code with invalid mode 2 against candidate code with mode 0. Its `detected=true` shows that this changed input pair produces different outcomes; it does not establish sensitivity to a faulty candidate or prove same-input oracle discrimination. The function record correctly calls this an input perturbation, not a mutated-candidate control.

The test harness has useful checks, but its semantic scope is bounded. It compares only the listed output bytes, helper-entry observations, return value, and sentinel PC. It does not compare all memory writes, preserved ARM/VFP registers, FPSCR state/exception flags, or exact fault behavior. All calibration/source/output memory is mapped and valid; aliasing output pointers, unaligned/invalid pointers, null state/calibration/source, and read/write fault equivalence are not covered. NaN/Inf thresholds, negative zero, threshold boundary equality, zero-span with zero numerators, reversed calibration spans, and broader floating-point exception behavior are also absent. The random generator does not expand threshold values or output-pointer aliasing.

The compiler and relocation setup are coherent for the tested function/dependency pairing: the harness compiles the candidate into a separate object, requires exactly two ARM BL relocations to the named helper, and checks each branch target is aligned and in range. However, the emulator model is ARM11 MPCore in Unicorn with default FPSCR state; reports do not record/compare FPSCR or callee-saved state. Treat the evidence as direct ARM differential evidence for the listed synthetic mapped inputs, not full ABI, fault, or hardware equivalence.

## Promotion decision and next validation

**Do not promote or integrate yet.** Retain the candidate as experimental with partial direct differential support. The smallest high-value offline next step is an actual candidate-mutation sensitivity check: compile a disposable copy with a single semantic defect (for example, change `mode >= 2` to `mode > 2`), compare original and mutated candidate on the same invalid-mode-2 case, and require the harness to report a mismatch. Keep that disposable mutation/output separate from the candidate and existing report directories.

Then add a bounded call-site composition check using the observed `0x001FA948` register/stack state, swapping only the called reader between original and candidate and comparing return, both stack outputs, preserved registers, and selected view bytes after the caller's relevant instructions. A small ARM shim around the actual call-site instructions is feasible and is the smallest useful ABI composition; it would not establish the complete `0x001FA840` non-leaf task, whose other dependencies and live state remain unresolved. Full caller composition should remain separate from this bounded check. No runtime intervention or physical-input evidence is a substitute for that offline candidate composition.

The paired runtime observations support memory-state response to injected helper outputs, but they used a GDB override on the original reader, not this candidate. They establish no physical control mapping, player movement, rendered-camera effect, interaction, or transition. The candidate remains separate from the integrated game image.

## Read-only checks performed

- Verified 14/14 `task.json` declared input hashes.
- Read the candidate, pinned original ARM function/deadzone assembly, harness, function record, and H4 field/camera contract.
- Parsed both raw reports and recomputed their SHA-256 identities; checked 119 cases per seed, report status, first counterexample, linked dependencies, and object/candidate hashes.
- Read the frozen harness's fixed-case generator and comparison/negative-control implementation; no source or runner edits, builds, test reruns, or emulator launches.
