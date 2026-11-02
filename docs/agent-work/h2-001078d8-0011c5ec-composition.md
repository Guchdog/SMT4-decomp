# H2 input refresh and state reader composition

## Scope

This integration stages both production C++ functions at their original H2
addresses: `0x001078D8` (logical input counter refresh) and `0x0011C5EC`
(input-state reader). The refresher's `R_ARM_CALL` resolves to the reader's
even ARM entry. The reader's seven direct calls still use original ARM callees.

## Validation

```powershell
python tools/h2_1078d8_11c5ec_chain.py --out build/agent-work/H2-semantic/h2-input-refresh-reader-integrated-chain/run001/checks/seed-20261116 --seed 20261116
```

The pinned original and two-slot staged image matched through 144 executions
of the original `0x001078D8` entry. Cases vary mode (`0`/`4`), ring count
(`-1`/`0`/`1`), selectors (`0`–`3`), global flag pairs, postprocess gate,
context/output bytes, ring records, table gates/masks and all 32 counter words.
Each comparison includes context, state/output, availability, all counters,
ordered writes, ring-call argument shape, SP, callee-saved registers and faults.
The row-31 sentinel is included in every case. The report records a fixture
digest, case summaries, call relocations, slot hashes and comparison results.

The 304-byte reader body and 160-byte refresher body were staged into their
304-byte and 164-byte slots. The combined IPS replayed exactly and changed only
those two slots. Both production translation units compiled during the focused
runner build.

## Limits

The `0x0012A758` ring helper is a controlled seam that supplies sample records
and signed counts. The other reader callees execute pinned original code.
Fixtures use valid, disjoint synthetic ordinary memory. Physical input source,
freshness, mapping, refresh cadence, scheduler behavior, concurrency, MMIO,
runtime reachability and whole-title behavior remain unverified. This is
component-chain evidence, not an H2 runtime acceptance result.

Independent review reran seed `20261117`, verified a distinct fixture digest,
and passed the same 144-case matrix, two-slot IPS replay/scope, all seven even
ARM callees and the 72 observed ring-call ABI traces. See the
[independent review](h2-001078d8-0011c5ec-composition-review.md).
