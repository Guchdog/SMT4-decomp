# Independent review: H2 `0x002BF6D0`

## Result

The candidate remains supported for the exercised offline domain. I repeated the independent experiment against the refreshed run002 packet with seed `20261116`; there are no direct or original-caller mismatches. `config/functions.csv` currently classifies `0x002BF6D0` as `non_matching`, which correctly records that the semantic replacement bytes differ from the reference. This is bounded offline evidence, not runtime or whole-game equivalence.

## Contract and ABI audit

The original helper occupies `[0x002BF6D0, 0x002BF710)` (64 bytes). It preserves `node_index` in `r4`, calls the manager resolver at even ARM address `0x002B0188` with both incoming arguments unchanged (`group` in `r0`, `node_index` in `r1`), and uses the resolver result as a two-load pointer chain: `[manager+4]`, then `[*]` to obtain `node_base`.

The original code multiplies signed `node_index` by `0x10624DD3`, then applies the signed reciprocal-multiply correction and arithmetic shift for division by 1000. This produces truncation toward zero, including for negative inputs. It computes `remainder = node_index - 1000 * quotient`, then returns the 32-bit wrapped address `node_base + 20 * remainder` in `r0`. The candidate forwards both resolver arguments and calls the original even ARM divider at `0x002C615C`; the divider returns signed quotient in low `r0` and signed remainder in high `r1` as a 64-bit result. Candidate C++ uses the quotient and recomputes the same signed remainder before forming the result address.

The original `0x002B88C4` caller composition executes the original resolver path, including `0x002B0188` and its downstream helper. Only `0x002BF6D0` is staged as the candidate. It observes both arguments at helper and resolver boundaries and consumes the returned node. Direct cases use a deterministic resolver-return seam, so they provide broad helper-input coverage but do not independently establish resolver behavior.

## Refreshed run002 evidence

Command:

```text
python tools/h2_bf6d0_experiment.py --out build/agent-work/H2-semantic/h2-bf6d0-independent-review-conversion/run002/checks/review-seed-20261116 --seed 20261116
```

Exit code: 0. Report: `build/agent-work/H2-semantic/h2-bf6d0-independent-review-conversion/run002/checks/review-seed-20261116/report.json` (SHA-256 `051e1b46a4187ee25bafee0dbd3b76438fcfa2129e0923f78cf8c824761a3863`). It records 2,269 direct cases and 42 original-caller cases, with no mismatches. All three negative controls were detected: wrong block divisor, resolver-index forwarding, and node stride.

The compiled body is 60 bytes in the 64-byte slot. Its two `R_ARM_CALL` relocations target even ARM entries `0x002B0188` at offset 8 and `0x002C615C` at offset 28. Exact-slot IPS replay passed and only the original slot changed. Both affected translation units compiled with one compiler slot and return code 0: `leaf_batch27_b.cpp` and consumer `leaf_batch32_c.cpp`; compiler invocations and private object paths are in the report.

## Explicit limits

The candidate divider leaves temporary spill/push bytes below restored `SP`. Equality deliberately excludes this stack residue because it lies below the callee's live frame and is not caller-visible ABI state after return. The comparison still checks restored `SP`, callee-saved registers, raw `r0`, resolver arguments, faults/stops, and non-stack writes. No parity claim is made for stale bytes below `SP`.

Inputs exercise valid aligned synthetic ordinary RAM. Direct cases use a deterministic resolver-return seam; caller cases use the actual original resolver and original caller. Runtime lifecycle, arbitrary aliasing, invalid-pointer/fault domains, and production runtime behavior were not tested. No emulator or full build was run.

## Recommendation

Proceed to bounded integration review with these limits and preserve the `non_matching` classification. Retain original resolver/divider dependencies and check final-image placement/interworking during integration. These offline results do not establish whole-game equivalence.
