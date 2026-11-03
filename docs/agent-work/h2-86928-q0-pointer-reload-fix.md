# `0x00286928` selector-6 pointer-load correction

## Result

The original ARM's selector-6 / incoming-`r2==0` route reads `P+4` only when
the full 32-bit arg5 is nonzero. It calls `0x002C4BF0(first_value,0x20)`, then
loads `P+4` again before `0x002B90F0(reloaded_value,0x40)`. The candidate and
production C++ previously read `P+4` unconditionally and reused the first
value. Both now condition the first read and reload after the first helper.
The six-word ABI and the rest of the dispatcher were left as-is.

The pinned ARM was read at the code image file offset `0x00186928` for VMA
`0x00286928`. Its relevant instructions are:

```text
00286af0  cmp   r4, #0
00286af4  beq   #0x286b10
00286af8  ldr   r0, [r5, #4]
00286afc  mov   r1, #0x20
00286b00  bl    #0x2c4bf0
00286b04  ldr   r0, [r5, #4]
00286b08  mov   r1, #0x40
00286b0c  bl    #0x2b90f0
```

Here `r4` is the full stack arg5 and `r5` is the selected object `P`. The
first load and both calls are skipped when arg5 is zero. The second load
observes mutation performed by `0x002C4BF0` before the next call.

## Fresh differential and controls

The final fresh report is
[`offline-report.json`](../../build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix/run001/checks/seed-20261124/offline-report.json),
SHA-256 `6a042f99ff016da16bc1e7418a8bfccac5a8ae0fb23589a431ae8603010a0156`.
It compares pinned original ARM, the compiled standalone candidate, and the
compiled production function. All three agree across 296 existing directed
cases, three dedicated pointer-load cases, and five executions through the
original callback `0x00221168`. Compared outputs include raw return and SP,
callee-saved GPRs and `d8`, helper arguments/order, all writes, final object and
service/global memory, faults, completion, and reads of each fixture object's
`+4` word.

The pointer cases use the original callback-independent selector-6 route with
valid object RAM:

| Full arg5 | Initial `P+4` | `P+4` reads | Relevant call arguments |
|---:|---:|---|---|
| `0` | poison value `0xDEAD0000` | none | neither helper called |
| `1` | `0x00950000` | `0x00950000`, then `0x00958000` | `0x002C4BF0(0x00950000,0x20)`, then `0x002B90F0(0x00958000,0x40)` |
| `0x100` | `0x00950000` | `0x00950000`, then `0x00958000` | same two calls and values as arg5 `1` |

For the latter two, the deterministic `0x002C4BF0` stub changes `P+4` to
`0x00958000`. The ordered trace proves the second call uses the reloaded
pointer. The `0x100` case confirms the gate tests the full word, not merely its
low byte. The callback fixture retains the original callback body and synthetic
upstream getter returns; its six helper ABI words match the established
`(r0,r1,r2,r3; stack) = (0x12003456,0x87654321,0,6; 1,0)` case and includes the
mutating helper stub.

Eight compiled negative controls were detected, including two task-specific
mutants. Their concrete counterexamples from the final report are:

- **Unconditional first read:** with arg5 `0` and `P+4=0xDEAD0000`, original
  reads are `[]`; the mutant records one read at `P+4` (word
  `0xDEAD0000`).
- **Stale second pointer:** with arg5 `1`, the original calls
  `0x002B90F0(0x00958000,0x40)` after the stub mutation; the stale-value mutant
  calls `0x002B90F0(0x00950000,0x40)`.

Candidate and production compile to identical 808-byte bodies, SHA-256
`163403e9038c8b691a61eb19cbc3d7b7836441ef6cf97b3fc61ebb8c0703ce30`, inside
the 820-byte ARM slot with 12 bytes left for ARM NOPs. Their 22 relocation rows
are identical; each is an `R_ARM_CALL` to an even ARM target. The runner resolves
each target from `config/functions.csv` and rejects Thumb-bit targets. The
candidate and production object SHA-256 values are respectively
`4dc49a0b8c5d4f609331a31a10649ddfa7af00ec8cb6b260bc74f1b4cc729e42` and
`f01bf7f4793878c827c0d2b6fe98a98342202dbe4f863de76419c32160d3a87b`.

Final source identities: candidate
`a99dea239c82d4c132f2860581b204cfe48ad449caf927e1ee2aef6cb9b256af`,
production TU
`b6a061c3e058f69179fb38e6da52ddbcf724396ab9a8d190602b96ef0a96b35b`, runner
`eb3c867e7e7ebfe3d7a36eeb9ecccac0bf9d0ea58a8096fcd40b496e69a1f82a`.

## Retries and limits

- `seed-20261121` stopped at the runner's stale hard-coded 812-byte expectation;
  the corrected body is 808 bytes in both outputs and still fits its pinned
  slot.
- `seed-20261122` exposed that Unicorn's memory-read hook `value` parameter was
  zero for these reads. The hook now reads the observed word from emulated
  memory instead of trusting that callback parameter.
- `seed-20261123` passed after fixing the hook. `seed-20261124` is the final
  fresh run after adding concrete mutation-counterexample data to the report.

All non-target helper callees are deterministic stubs, including
`0x002B8D24`; callback getters are synthetic. The fixtures use mapped object
RAM and only the arg5-zero pointer *value* is poisoned—the `P+4` field itself
remains readable as part of the object. No emulator/runtime, full dispatcher
equivalence, arbitrary pointer-fault parity, full original callee behavior, or
whole-game equivalence is established. This fixes and validates the bounded
read ordering only; integration closure remains with the coordinator.
