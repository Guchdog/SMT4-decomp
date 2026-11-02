# Independent review: selector-2 VFP normalizer `0x0013BAE0`

## Recommendation

**Ready for bounded promotion review.** I independently decoded the original ARM/VFP body and compared its branches and operation grouping with the typed candidate. Fresh seed `20261109` matched all 352 direct and 18 original caller-composition cases; all three controls were detected. No output, return, core callee-saved register, stack, memory-write, or fault counterexample appeared in the tested domain.

The supported scope is valid disjoint ordinary-RAM fixtures emphasizing the parent-reachable signed-halfword samples/calibrations. `0x0013BAE0` has no external call dependencies in the candidate. The candidate is byte-different, so retain `non_matching`. FPSCR values are recorded but deliberately excluded from equality; this review makes no FPSCR flag parity claim.

## Pinned original and candidate audit

Pinned `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; all 12 run002 input pins matched. Capstone decoded 115 ARM/VFP words across `[0x0013BAE0,0x0013BCAC)`, 460 bytes. The final 16 bytes are the original literal pool at `0x0013BC9C..0x0013BCAB`: `0.0`, `-36.0`, `+36.0`, and `1600.0` (IEEE-754 words `0x00000000`, `0xC2100000`, `0x42100000`, `0x44C80000`).

The original accepts output-X/Y pointers in r0/r1, signed samples in r2/r3, and signed calibration A/B on the stack. It pushes r4-r6 and reads only B at entry-SP+4; A is unused. It computes `R=low32(x*x+y*y)`, converts signed R to float, and takes the zero-output path when R converts to exactly zero. Otherwise signed compares of wrapped `x*x` and `y*y` choose the dominant axis and ±36 boundary ratio. The original uses VFP multiply/divide for each coordinate and `VMUL`/`VMLA` to assemble boundary squared. `VCMPE` plus `VMOVHS` caps that value at 1600; a second compare and `BHS` sends R at/above the boundary to scaling, while lower R stores zero to X then Y.

For the scaling path the original computes square roots of the boundary and R, converts signed B and low-word `(B-40)` to float, then compares R to signed low-word `B*B`. `BLT` chooses interpolation; the other path uses direct scaling. Both paths use VFP multiply/divide, `VCVT.S32.F32` toward zero, and ordered halfword stores X then Y. All exits leave r0 as output-X. The candidate source explicitly keeps u32 wrap intermediates before signed conversion, uses the same direction-dependent ±36 construction, preserves the boundary-square cap and interpolation/direct formulas, converts outputs toward zero, stores low halfwords X then Y, and returns output-X. It intentionally ignores calibration A.

I also disassembled the compiled candidate: its 368-byte body has no ELF relocations and includes inline constants `+36`, `-36`, `1600`; it fits the 460-byte slot. The original selector-2 `BL` at `0x00128658` targets even ARM entry `0x0013BAE0`.

## VFP predicate and FPSCR limits

The normal signed-halfword path exercised here produces finite VFP operands on the tested comparisons. At the instruction level, however, original VFP unordered conditions are not interchangeable with C++ ordered `<` for every possible exceptional value. In particular, the original final `VCMPE`/`BLT` treats unordered as LT (`N != V`), while the candidate's C++ `<` selects the non-interpolation path for NaN on the compiled ARM target. The runner's parent-reachable halfword fixtures did not produce an unordered value, and it does not claim arbitrary direct s32 or exceptional-float equivalence.

The original uses both `VCMP` and `VCMPE`; candidate C++ conditionals can change FPSCR exception-flag behavior even when observable outputs agree. The runner records FPSCR but excludes it from `compare_view`. Therefore this evidence supports outputs, ordered writes, raw r0, r4-r11, SP and faults for tested cases only; it does **not** support FPSCR parity or exceptional flag semantics.

## Fresh offline evidence

Runner command (exit 0):

```text
python tools/h2_input_normalizer_branch2_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-branch2-review-0013bae0/run002/checks/review-seed-20261109 --seed 20261109
```

- Direct differential: 352/352 matched. This is 280 systematic pairs from 10 calibration pairs × 28 signed-halfword samples, plus 72 deterministic random signed-halfword fixtures. The set covers signs/quadrants, axes, zero, ±36 boundary neighbors, calibration pairs including reversed/equal/extreme values, and `(-32768,-32768)` wrapped-radius behavior.
- Caller compositions: 18/18 matched over two seeds, including selector-2 samples, zero/negative reader count, other selector values, and original reader/dispatcher code with a controlled ring-reader seam.
- All controls detected: `boundary_extent`, `boundary_clamp`, and `truncation_vs_rounding`.
- Body: 368/460 bytes; no relocations; even ARM callsite; exact-slot IPS replay and one-slot-only patch audit passed.
- Both affected TUs, `leaf_batch44_c.cpp` and `leaf_batch29_a.cpp`, compiled sequentially into private outputs using one compiler slot (exit 0).
- Runtime/emulator was not run.

Report: `build/agent-work/H2-semantic/h2-input-normalizer-branch2-review-0013bae0/run002/checks/review-seed-20261109/report.json` (SHA-256 `7fd5d6a0073b7692cee0eb1f850df3ada97bf66a256dfa219ebb2f9567818d8a`). Source SHA-256 `7ff6a3d3dd82364f0b9756f261ba72459a59c9b8432880e39807a899a356fb9d`; candidate body SHA-256 `0d1d0ef552cb3b255aaea65c6cb07b940f5e36b08a3863c7eed72e797fe3621b`. Staged image SHA-256 `89daed38fa55e01cf8c7f8e1d03f2d46726fe90867c929c712de8883fe0a6010`; IPS SHA-256 `457751df03b84b54050d30aab7aefd6b0327d8d44b49ebd8dd7a4aba2c8a347e`. Object hashes: `leaf_batch44_c.o` `f46154067a8aca79e270014fc7a26b5e16d5e41f49e5573c34fce34eed8fd7eb`; `leaf_batch29_a.o` `a99542f991ab01fdeb4381d7a399d77610dee760d931e5a99adbf3dbf3fac70c`.

## Limits and next action

No evidence covers malformed or aliased pointers, MMIO, concurrent mutation, arbitrary s32 inputs, exceptional VFP/FPSCR behavior, live input provenance/cadence, or whole-title behavior. Caller compositions use the controlled `0x0012A758` ring-reader seam. The original input producer and parent services remain dependencies.

Coordinator can consider this candidate for integration within the stated finite parent-reachable domain. Preserve the FPSCR exclusion, original caller-seam limits, and `non_matching` byte classification.
