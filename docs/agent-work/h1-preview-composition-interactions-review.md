# Independent review: corrected H1 preview composition interactions

## Verdict

**The bounded composition evidence is supported; the result remains partial.** I checked the fresh v2 packet inputs without finding a hash mismatch, decoded the pinned helper and selector instructions, independently recomputed the six original function-span hashes from the pinned `code.bin`, and inspected run-03's candidate link, case projections, fixtures, mutation control, and producer handoff. No discrepancy was found in the reported three fixture comparisons. I did not compile, rerun tests, or use a game runtime.

The corrected third fixture supports successful selector lookup only for this specific synthetic layout. The older 17-case report does not support its claimed successful selector lookup; it still records exact comparisons for the fixtures actually supplied and other covered paths.

## Pinned reachability and maximal dependency sets

Pinned helper `0x002BF9F0` returns before dependencies if its object pointer is null. For a non-null object, it reads signed words at `+4` and, only if that first word is negative, `+8`; both negative words take the early return. Otherwise control reaches helper work. At `0x002BFA48-0x002BFA50`, the row duration is loaded unsigned from the row and compared against signed object progress. The `bgt` edge enters interpolation and calls divide (`0x002C615C`); the endpoint arm bypasses divide and can call setter (`0x002BDAC0`) only when its row/sequence conditions allow it. These branches prove divide and setter are mutually exclusive in a single helper invocation.

Every continuing helper path reaches the shared tail in this order: scale `0x002B1FC0` (`0x002BFC30`), translation `0x002B1DFC` (`0x002BFC3C`), selector `0x002B1C8C` (`0x002BFC48`). The callees independently test their object enable bytes `+0x87/+0x88/+0x89` and their tables at `+0x58/+0x64/+0x70`, respectively. Thus the maximal reachable dependency combinations are:

1. divide, scale, translation, selector;
2. setter, scale, translation, selector.

There is no valid combined path containing both divide and setter in one call. Run-03's first and third cases exercise the first set; its second exercises the second. The case tables also set scale and translation to endpoint/interpolation branches as named. The recorded direct-callee sequences match those paths and preserve the common-tail order.

## Selector fixture correction

The pinned selector loads the signed selector index from object `+0x82`, computes `sequence_base + 8 + 28*index` (`0x002B1D30-0x002B1D40`), and reads the word there. After incrementing the index, it computes the next record address and loads the word at that record's `+8` (`0x002B1D4C-0x002B1D64`). For indexes zero and one, those locations are sequence-base `+8` and `+0x24`.

The inherited shared fixture writer instead starts each encoded entry at `+0x0C`, then adds the per-entry `0x1C` stride and `+8`, putting words at `+0x14`, `+0x30`, etc. The interaction runner locally overwrites the first two words at `+8` and `+0x24`; it does not change the shared runner or any candidate. In the third fixture, the corrected values are `0` and `1`. The pinned code consumes index zero's non-sentinel value, advances to index one, reads `1`, searches the descriptor's lookup entries, and reaches the selected table path. Run-03's final object snapshot has `+4 == 42` and a nonzero `+0x70` selected-table pointer; original and candidate snapshots match. This is consistent with the corrected selector branch and with the test assertions.

The previous 17-case report used the shared writer's `+0x14` layout. Its case labelled successful selector lookup therefore does **not** prove that path. Withdraw that selector-lookup claim and do not count it as selector lookup coverage. The report's 17/17 equality remains valid for the exact supplied fixtures and its separately exercised paths; it does not become invalid as a comparison, but its branch label was wrong. The 17-case suite also isolated dependency bodies and did not prove simultaneous active common-tail updates. The corrected three-case run repairs fixture data only for its own third case; the shared writer remains unfixed and its selector-lookup cases still need separately assigned repair/revalidation.

## Identity, build, comparison and mutation audit

Pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. I independently sliced and hashed all six report spans from `extracted/exefs/code.bin`; each matched the run-03 identity:

| Entry | Size | Pinned span SHA-256 |
| --- | ---: | --- |
| `0x002BF9F0` helper | 664 | `9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e` |
| `0x002BDAC0` setter | 108 | `e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a` |
| `0x002C615C` divide | 556 | `3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9` |
| `0x002B1FC0` scale | 444 | `9d9948ecc56a1a6dd32012eacce76ce8cffdf3902632f8efc85245d9dd1f5811` |
| `0x002B1DFC` translation | 452 | `092706575055bba00e8aab90e9ef2a45c2761fb7d12fa0f0b54dbecd35b7439a` |
| `0x002B1C8C` selector | 368 | `8097eb2315dd6b7f6dd72be434ee38223841c6470bfa3b923b362900572ba092` |

The report's six candidate source identities match the packet hashes. Its private ARMv6K link includes all six candidate sources plus the local composition adapter; every recorded object compile and the link exit with code 0, the ELF has no undefined symbols, and the ELF SHA-256 recomputes to `cadabe6a51fbc6ccda698afde01beb595417b636af2bc65f086e2c7121b5678c`. The adapter provides entry-name/ABI wrappers, not replacement bodies for the tested dependencies. The producer reports a fresh run-03 command exit 0 and four focused test cases passing (test command exit 0); I inspected those records and test assertions but did not rerun them.

All three original-vs-candidate cases report `passed`, no fault, no first mismatch, equal full mapped-data SHA-256 values, equal caller-stack hashes, equal `r0`, and equal preserved `r4-r11`, SP, `d8-d15`, and FPSCR. The mapped-data projection is the complete `0x20000`-byte fixture memory. Recorded ordered calls and arguments agree, including two divide calls where expected and the corrected selector path. The targeted mutation that omits setter's `+0x50` store is detected at `0x02000050` (`2` versus `0`), so the mutation control is effective for that setter effect.

The compared projection intentionally excludes caller-saved scratch state: recorded `r1` differs between original and candidate (original `0x02007000` / `0x2a`, candidate `1`). This does not invalidate the declared ABI projection, but it means the result is not full register-state identity. The runner also does not compare memory access multiplicity/order or below-SP spill residue.

## Limits and next work

The evidence is synthetic ARM/Unicorn composition evidence for three non-aliasing fixture combinations. It is not a test of live H1 object construction, asset/table binding, frame lifecycle, rendering, caller-visible integration, concurrency, MMIO, or game runtime. Helper division cases use positive nonzero row duration `8`; divide-by-zero, broader signed-duration domains, invalid pointers/indices, and aliases remain uncovered. No Azahar or gameplay/runtime scenario was run.

Keep the result as partial supporting evidence. Separately repair the shared full-composition selector fixture writer and rerun its relevant cases before treating those cases as lookup coverage. Then validate caller-owned object setup/lifecycle and an integrated runtime scenario before promotion.
