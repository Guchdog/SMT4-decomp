# Independent review: selector-0 normalizer `0x0013B9FC`

## Recommendation

**Ready for bounded promotion review.** Four fresh original-versus-candidate runs and independent pinned ARM inspection found no behavioral counterexample within the tested domain. The candidate preserves the examined wrapped arithmetic, signed branch choices, original signed-divider dependency, output store order/width, and low-halfword return. Coordinator corrections to the contract span/epilogue and zero-divisor counts are now confirmed by the run004 packet and pinned decode.

This is bounded evidence on valid, disjoint ordinary RAM. The original `0x002C615C` signed divider remains a dependency. No claim is made for malformed pointers, aliasing/MMIO, all possible s32 combinations, physical input validity, runtime cadence, or title-wide behavior.

## Independent pinned-image audit

The pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; all 11 input hashes declared in the run packet still match. I decoded the original target and selector-0 call path from that image.

The original body spans `[0x0013B9FC,0x0013BAE0)`, exactly 228 bytes, including its epilogue at `0x0013BAD4` (`ADD SP`), `0x0013BAD8` (`MOV r0,r1`), and `0x0013BADC` (`POP ... pc`). The following function begins at `0x0013BAE0`. Earlier packet revisions had an incorrect half-open end; the current contract correctly states `[0x0013B9FC,0x0013BAE0)`.

The original entry saves r0-r12/lr, loads signed A/B stack arguments, computes low-32-bit squares and compares them with signed conditions. When `R2 <= A2`, it stores zero to output-y then output-x and returns zero. Otherwise, `Q=low32(R2<<14)` selects either the magnitude-zero path or an integer estimate loop that calls the original divider. The outer-square comparison selects saturation or radial scaling. The two quotient calls store halfwords to x then y, and the final `SXTH`/return path returns the signed low 16 bits of the delta. Selector-0 setup at `0x00128610` uses adjacent output halfword pointers, full-width samples, and signed calibration values on its outgoing stack; the actual reader supplies sign-extended halfword samples and post-clamp A/B values.

## Fresh offline validation

Runner command (exit 0):

```text
python tools/h2_input_normalizer_branch0_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-branch0-review-0013b9fc/run002/checks/review-seed-20261107 --seed 20261107
```

- Direct original-versus-candidate differential: 107/107 matched, including directed deadzone/radial/saturation boundaries, A/B boundary and reversed pairs, negative samples, `361/362/363` around the signed `Q` boundary, large signed samples through `INT_MAX`/`INT_MIN`, and deterministic random cases. Raw r0, r4-r11, SP, fault status, output/context bytes, ordered writes, and divider entry traces matched.
- Original reader/caller compositions: 16/16 matched over two seeds. They compose through original `0x001078D8`, `0x0011C5EC`, and `0x00128610`, with only `0x0013B9FC` staged, a controlled `0x0012A758` ring-reader seam, and original `0x002C615C` divider.
- Zero-divisor observations: 14 direct fixtures contain zero-denominator calls, with two final x/y quotient calls per fixture (28 call entries total). Original and candidate traces/results matched. The conversion note/function record's “14 ... calls” wording should be clarified to distinguish 14 fixtures from 28 call entries for this seed/run.
- Negative controls all triggered: `inner_uses_outer`, `deadzone_store_order`, and `divide_denominator_off_by_one`. No candidate counterexample occurred.
- Compiled candidate body: 208 bytes within the 228-byte original span. Three final-VMA `R_ARM_CALL` relocations resolve to even ARM entry `0x002C615C`; the pinned dispatcher `BL` at `0x00128678` resolves to even ARM entry `0x0013B9FC`. Exact-slot IPS replay and one-slot-only patch audit passed. Candidate bytes differ from original.
- The runner compiled `leaf_batch30_a.cpp`. I separately compiled both affected TUs, `leaf_batch30_a.cpp` and `leaf_batch29_a.cpp`, into private objects with one compiler slot; both exited 0.
- Runtime/emulator check: not run.

Fresh report: `build/agent-work/H2-semantic/h2-input-normalizer-branch0-review-0013b9fc/run002/checks/review-seed-20261107/report.json` (SHA-256 `0c34825700fd774530defbcaeff462ecbc56f2ae6c72f639e8ed29b6eaacaeb2`). Candidate body SHA-256 is `d6ca9c2a69d86fc80a614a4d81db7695f701f1c1400c12df1de8af641a52d84e`. Staged image SHA-256 is `d2c152788d935a8fdd36696a33d7e3e863dbac600f435c3582e60c610b01ea71`; IPS SHA-256 is `de0b5bcd26df9029126810ddf1c8df66621aff4cd7914eb33edfeda1b063a2eb`. Private object hashes: `leaf_batch30_a.o` `e39b538b01ba53ed49cc5cdd231862d4d25d64a2e255092483b0bd7776a2bf33`; `leaf_batch29_a.o` `a99542f991ab01fdeb4381d7a399d77610dee760d931e5a99adbf3dbf3fac70c`.

## Scope and next action

The direct tests use valid disjoint ordinary-RAM fixtures. Caller compositions use a controlled ring reader and original signed divider; this does not establish live input provenance or freshness. Aliasing, malformed pointers, MMIO, concurrent mutation, exhaustive s32 behavior, and runtime/title behavior remain unsupported. Wrapped u32-to-s32 reinterpretation and arithmetic shift behavior are verified for this pinned ARM target/compiler, not claimed as host-independent C++ semantics.

Coordinator action: consider bounded integration/promotion based on the reviewed evidence, retaining `non_matching` byte classification and original dependency `0x002C615C`.


## Run003 confirmation

The coordinator's updated packet inputs all matched before the rerun. The corrected contract now gives the exact original span `[0x0013B9FC,0x0013BAE0)` and labels BAD4/BAD8/BADC as the epilogue sequence; the conversion note/function record distinguish 14 zero-divisor fixtures from 28 final quotient-call entries in the prior run. A fresh pinned decode confirms those range/count corrections, with one remaining editorial detail: the updated contract currently says the BAD4 instruction is `ADD SP,SP,#0x38`; the instruction word decodes as `ADD SP,SP,#0x10`. BAD8 is `MOV r0,r1`, and BADC is `POP {r4-r12,pc}`. The coordinator has been notified and will correct the immediate after this handoff; I did not edit frozen inputs.

Fresh run003 command (exit 0):

```text
python tools/h2_input_normalizer_branch0_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-branch0-review-0013b9fc/run003/checks/review-seed-20261108 --seed 20261108
```

This distinct seed again matched all 107 direct cases and 16 caller compositions. All three controls were detected. Twelve direct fixtures reached zero-denominator calls, totaling 24 final x/y quotient-call entries; original and candidate traces/results matched. The body remains 208/228 bytes, all three divider relocations and the selector-0 caller target are even ARM, IPS replay passed, and only the 228-byte slot changed. Both affected TUs compiled sequentially into fresh run003 outputs (exit 0).

Run003 report: `build/agent-work/H2-semantic/h2-input-normalizer-branch0-review-0013b9fc/run003/checks/review-seed-20261108/report.json` (SHA-256 `70d8633488cf89da39a55dc11bf5774e7050a12411901e588241faed8fbd8ca3`). Runtime was not run; caller composition continues to use the controlled ring-reader seam and original divider.


## Run004 confirmation

All 11 refreshed packet input hashes matched before the run. Current documentation correctly records `[0x0013B9FC,0x0013BAE0)`, the epilogue instructions `ADD SP,SP,#0x10` at BAD4, `MOV r0,r1` at BAD8, and `POP` at BADC, plus 14 zero-divisor fixtures / 28 quotient-call entries for the earlier seed. Fresh Capstone decoding of pinned `code.bin` confirms each instruction and range.

Fresh run004 command (exit 0):

```text
python tools/h2_input_normalizer_branch0_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-branch0-review-0013b9fc/run004/checks/review-seed-20261109 --seed 20261109
```

The distinct seed again matched 107/107 direct cases and 16/16 reader/caller compositions. Fourteen fixtures contained zero-denominator calls, totaling 28 final x/y quotient-call entries; original and candidate traces/results matched. All three negative controls triggered. Candidate size is 208/228 bytes; the three divider relocations and dispatcher call target are even ARM; exact-slot IPS replay and the one-slot-only audit passed. Both `leaf_batch30_a.cpp` and `leaf_batch29_a.cpp` compiled sequentially into private run004 outputs with one compiler slot (exit 0). Runtime was not run.

Run004 report: `build/agent-work/H2-semantic/h2-input-normalizer-branch0-review-0013b9fc/run004/checks/review-seed-20261109/report.json` (SHA-256 `47c7f0254a5691ed56ac354c36d693fad05755a719968e2d6ff9a88426d10084`). Staged image SHA-256 `d2c152788d935a8fdd36696a33d7e3e863dbac600f435c3582e60c610b01ea71`; slot-only IPS SHA-256 `de0b5bcd26df9029126810ddf1c8df66621aff4cd7914eb33edfeda1b063a2eb`. Objects: `leaf_batch30_a.o` SHA-256 `e39b538b01ba53ed49cc5cdd231862d4d25d64a2e255092483b0bd7776a2bf33`; `leaf_batch29_a.o` SHA-256 `a99542f991ab01fdeb4381d7a399d77610dee760d931e5a99adbf3dbf3fac70c`.
