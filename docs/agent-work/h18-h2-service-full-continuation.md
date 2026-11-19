# H18 service full continuation through return

## Result

The previous positive composition stopped at `0x00138980`, immediately after `0x002bdac0`. This extension executes the original service body from `0x00138934` through its final `POP {r4,r5,pc}` at `0x00138ac0` and returns to a synthetic LR. The service body remains the pinned original in every case. The runner substitutes production C++ for `0x002bf030`, `0x002bdac0`, each separately, and both together.

The initial positive record word is `1`, so the service calls `0x002bdac0` with `(object,1,0)`. The fixture also controls the subsequent record fields and service-owned tables:

| Scenario | record `+8` | record `+0x0c` | record `+0x14` | Later branches reached |
|---|---:|---:|---:|---|
| `all_positive` | 1 | 1 | 1 | `0x1389a4`, `0x1389fc`, `0x138a48` |
| `first_later_only` | -1 | 1 | -1 | `0x1389a4` |
| `second_later_only` | -1 | -1 | 1 | `0x1389fc` |
| `third_later_only` | 1 | -1 | -1 | `0x138a48` |
| `all_later_skipped` | -1 | -1 | -1 | none |

In `all_positive`, the original returns `r0=7`, restores `sp` and callee-saved registers, and visits each later branch once. Each single-branch fixture visits only its intended branch; the all-skipped fixture visits none. Every snapshot matches for original, either production replacement alone, and both replacements, including return registers, full object bytes, row and external tables. The `0x002bdac0` selector-pair mutation is detected.

## Reproducibility

Run `python tools/h18_h2_service_full_continuation.py --output <fresh-directory>`. It compiles the two pinned production translation units into that private output, then executes all variants using Unicorn. `tests/test_h18_h2_service_full_continuation.py` reruns the focused experiment. The report records image/source/object hashes, field values, branch traces, return state, and control result.

## Limits

The runner reaches the real end of the service body, but begins at `0x002bf030` with deliberately constructed ordinary-RAM objects and tables. It does not infer a natural title-config caller, record population, allocation/lifetime, valid table extent, or runtime scheduling. External array values and the sentinel table are synthetic, aligned, and readable. It establishes the bounded original-versus-production composition under those fixtures, not whole-H2 behavior.
