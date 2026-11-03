# `0x00207D84` generic UI transform conversion

## Result

Implemented a readable typed C++ wrapper in `src/engine/leaf_batch30_c.cpp`.
The affected translation unit emits a 156-byte ARMv6K function. The original
slot is 128 bytes, so in-place replacement does not fit. The bounded experiment
uses a branch at the original entry and stages the body at `0x003FEE54`, the
remaining 428-byte zero tail after the documented Calc body at `0x003FE624`.
This is a concrete, reproducible synthetic placement candidate; integration
must retain the Calc body and revalidate the combined image. The existing
ledger still says `matching`, which is not truthful for this 156-byte body.
Ledger correction is coordinator-owned and required before any promotion.

The C++ calls the original `0x002C5218` and `0x0026330C`, copies the four global
vector words to the fixed scratch in order, passes the first three words as
projection input, writes x/y/z/zero back in order, and produces `r0=0x004EA91C`
and `s0=projected z`. A small empty GNU register constraint preserves the
independent `r0` result alongside the C++ float return in `s0`; the body is not
an opaque assembly substitute.

## Fresh offline evidence

Command:

```text
python -B tools/ui_transform_00207d84_experiment.py --out build/agent-work/H2-semantic/h2-ui-transform-convert-00207d84/run001/checks/direct --seed 20261102
```

Exit code: 0. The report is
`build/agent-work/H2-semantic/h2-ui-transform-convert-00207d84/run001/checks/direct/report.json`.
All seven direct fixtures matched, including basis vectors, negative values,
nontrivial perspective terms, a finite near-denominator case, and seeded
values. Four initial FPSCR rounding modes (RN, RP, RM, RZ) matched, including
the final FPSCR bits. The comparisons include the four returned vector words,
the four scratch words, `r0`, `s0`, `r4-r11`, SP, `s16-s31`, caller-owned stack,
and ordered stores to both global ranges. The direct result returned
`r0=0x004EA91C`; `s0` matched the projected third component.

Two executions of original `0x0024B874` took the real callsites
`0x0024B8E0` and `0x0024B908` under the `[r4+0x9C] == 2` path. Both original
and staged images matched their result bytes and ordered global write traces.
Unrelated UI helper calls at `0x002698F4` and `0x00269768` were stubbed; the
final `0x0024C62C` service was stubbed to return fixed `s0=0.125`. The wrapper's
projection callees remain original. Three observation-level negative controls
detect swapped x/y result words, a missing zero fourth word, and a changed
scratch word. These controls validate comparison sensitivity; they do not
replace semantic code mutations.

The four individually compiled TUs (`leaf_batch30_c.cpp`, `leaf_batch21_b.cpp`,
`leaf_batch40_b.cpp`, `leaf_batch41_a.cpp`) all exited 0. No full build or
emulator was run.

## Placement and relocation audit

The pinned residual range `0x003FEE54..0x003FEFFF` has 428 zero bytes. The
runner's aligned pointer-word scan, linear ARM branch and PC-relative-memory
scan, and Thumb literal-load scan found no reference into that range. This is
not a proof against computed/indirect references or loader-specific use. The
staged body resolves exactly two `R_ARM_CALL`s, at final VMAs `0x003FEE68` and
`0x003FEEB0`, to even ARM entries `0x002C5218` and `0x0026330C`. The entry
trampoline at `0x00207D84` is an aligned ARM B to `0x003FEE54`; return through
the candidate's original LR remains intact. IPS replay passed, with changes
limited to the 4-byte entry branch and 156-byte cave body.

The independent review found that this standalone pinned-image cave is already
allocated in the current cumulative H2 image: `[0x003FEE54,0x003FEED0)` is Draw
helper code, `0x003FEED0..0x003FEED4` is format data/alignment, and
`[0x003FEED4,0x003FEFF8)` is Secondary. This body would overwrite the Draw
helper/data and the first 28 bytes of Secondary; only 8 bytes remain. The
candidate is a reviewed non-matching reconstruction, but it is not integrated
into the cumulative image. A new non-overlapping complete-image layout or an
in-slot implementation is required before integration.

## Scope limits and next step

The caller is a generic UI consumer. Neither it nor these synthetic fixtures
establish direct TitleConfig/Audio Settings reachability, natural H2 scheduling,
or whole-screen behavior. Invalid pointer chains fault as the original does;
this run uses valid mapped pointers. Zero and nonfinite homogeneous denominators
are not asserted beyond the bounded finite near-boundary sample. Runtime was
not run. No direct TitleConfig/Audio Settings route is established. The ledger
now records the non-identical C++ body as `non_matching`; cumulative-image
integration remains blocked by the verified cave collision. Retain the
external-service and reachability limits above.
