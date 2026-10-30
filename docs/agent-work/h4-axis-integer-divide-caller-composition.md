# H4 integer-divider caller composition

## Result

Offline composition **passed for the bounded synthetic fixture set**: the original selector-0 caller (`0x0013B9FC`) and selector-1 caller (`0x0013B8F8`) produced identical compared observations against the pinned image and an image where only the `0x002C615C` helper body was replaced with the reviewed experimental C++ candidate.

The run covered 1,982 cases (991 per caller), combining deadzone/radial boundaries, signed-halfword extrema, seven A/B calibration orderings, aliased/swapped/null outputs, and deterministic random cases (seed `20261028`, 128 per caller). It found zero compared differences and zero unmatched faults. Sixteen null-output probes faulted identically in the two images at the same faulting PC. The same-input divisor-zero mutation control reached the zero-divisor helper branch in both callers and changed the observed output in both.

## Evidence and reproducibility

- Runner: `tools/h4_axis_integer_divide_caller_composition.py`, SHA-256 `BDA16622E7EFDA91DC1B11FC15B2FCBBF38D5F8B16143EA7D6E37B5A3B106FD5`.
- Candidate source: `experiments/semantic_equivalence/h4_integer_divide_candidate.cpp`, SHA-256 `970E00F3C6BF8E350F935158B5B8BAB46919F257418F5EFB0174D2B19E8DA96B`.
- Pinned reference: `extracted/exefs/code.bin`, SHA-256 `1F98884FE997AF22E032A14C51A46C872B05B0E079A0F29E307B0E059CFaa558`.
- Command: `python tools/h4_axis_integer_divide_caller_composition.py --out-dir build/agent-work/H4-semantic/h4-axis-integer-divide-caller-composition/003/output` (exit 0).
- Raw report: `build/agent-work/H4-semantic/h4-axis-integer-divide-caller-composition/003/output/report.json`, SHA-256 `936EE8B8B415E77A6EBFEE662D09D2DB0D23322DDBC8FB5EFD38211639B9694A`.
- Candidate object SHA-256 `29C52ADAA8ABC61A7906C3B79E471F0005A45C7742BD21F4957F40856F552A64`; extracted 128-byte body has no relocations.
- Replacement bytes SHA-256 `9DB496A20169FFB679D56702131F5CE5A8FAEC1FF3C56718CE179EADC8BD8930`; replacement covers only `[0x002C615C, 0x002C6388)` (556 bytes), with ARM NOP padding after the candidate body.
- Composed image SHA-256 `5A6F75D7761DF1870A00F2D2FF727576821852CBC4E7161BC14F16BDCC871755`.

The comparator checks return registers, return-to-sentinel, SP, `r4-r11`, the captured output region, fault text and PC, and ordered non-stack writes. It records but excludes stack-write identity and flags. The null-pointer probes are deliberately invalid arguments; matching faults document that both implementations reject them similarly, not that null pointers are supported.

## Limits and next step

This is synthetic caller-composition evidence, not real calibration-domain coverage or full machine-state/runtime equivalence. The original and candidate helper retain different stack-write behavior; flags and stack-boundary faults are not compared. The per-caller aggregation records 15,230 versus 21,138 stack writes for selector 0 and 11,426 versus 16,082 for selector 1 (original versus candidate). Real calibration values, player movement, physical input, rendered camera behavior, interaction, and zone transition remain unproven. Keep the helper experimental; obtain independent review before acceptance or promotion.
