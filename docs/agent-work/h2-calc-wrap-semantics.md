# H2 `TitleConfig_Calc` special-handle wrap semantics

## Implementation

The original ARM path computes the signed helper-result difference, multiplies
by five, then doubles the product in 32-bit registers before calling
`0x002C615C`. The candidate now casts each signed helper return to `u32` before
subtraction, then uses `u32` multiplications. C++ therefore defines every
operation modulo `2^32` and sends the same 32-bit words in `r0` and `r2`; the
sign-extended `s16` limit remains passed in `r1` as before.

The scenario model can supply exact signed return values for the script-value
and script-index helper stubs and a safe `bounded_value` return in `0..10`.
Four directed cases cover subtraction wrap in both directions and scale
overflow from positive and negative extreme values:

| Case | Script value | Current value | Helper args `(r0,r1,r2)` | Safe mapped result |
|---|---:|---:|---|---:|
| max minus min | `0x7fffffff` | `0x80000000` | `0xfffffff6, 10, 0xfffffffb` | 3 |
| min minus max | `0x80000000` | `0x7fffffff` | `10, 10, 5` | 7 |
| positive scale extreme | `0x7fffffff` | `0` | `0xfffffff6, 10, 0x7ffffffb` | 10 |
| negative scale extreme | `0x80000000` | `0` | `0, 10, 0x80000000` | 0 |

The original and candidate ARM callback traces compare the exact `bounded_value`
arguments and selected work state. The mapped results stay inside the initialized
option storage range so these cases test arithmetic without introducing an
unmapped-memory fault.

## Validation

Fresh outputs are under
`build/agent-work/H2-semantic/h2-calc-wrap-semantics/run-001/checks/`.

- Focused tests: `python -m unittest tests.test_h2_calc_experiment tests.test_h2_calc_code_patch -v` — 9 passed.
- Python syntax: `python -m py_compile tools/h2_calc_experiment.py tests/test_h2_calc_experiment.py tools/h2_calc_code_patch.py tests/test_h2_calc_code_patch.py` — exit 0.
- Callback differential, seed 7, 32 seeded cases plus 36 directed cases — 68/68 passed; config-byte corruption control detected.
- Callback differential, seed 20261024, 32 seeded cases plus 36 directed cases — 68/68 passed; config-byte corruption control detected.
- Final-address patched-image differential for each seed — 68/68 passed; wrong-branch control detected in both runs.

The candidate source SHA-256 is `16f2af7c953a089ffe277d2f299ea89ab90d028f57d6708ffdc8cf6115844ed2`; object SHA-256 remains `cd4c0eb1cbf21ac849f994370c0403fb2a6919b0263afd834db5928e768c60b`. The compiled ARM body remains 2,096 bytes, so final cave placement and patch hashes are reproducible and unchanged: patched image `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`, IPS `0b671f4f40c172984e730d0387899ce47abe8f2ee5e90043a2e481aa591cf781`.

## Limits

This evidence establishes modulo arithmetic at the modeled helper boundary for
the tested `s32` extremes. The real script helper ranges, `bounded_value`
semantics, callers, UI behavior, persistence, and runtime remain unverified.
The callback and patched-image runs use the same deterministic external service
stubs and are not production promotion or whole-title equivalence. No Azahar,
RSP, or host input was used.

