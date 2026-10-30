# H2 production integration: `UiConfig_CopyPair`

## Result

Replaced the naked no-argument wrapper at `0x002ADB40` with a typed C++
function taking `(void* destination, const void* source)` and returning the
destination address in `r0`. The body uses four explicit ARM memory operations
to preserve the original load-load-store-store order and target unaligned
ordinary-memory behavior. It compiles to the exact original 20-byte body, so
the helper remains `matching` in the exact-byte ledger and the already-reviewed
combined H2 image needs no additional code patch.

The `leaf_matching.h` declaration and local declarations in the assembly-caller
translation units now agree with the function ABI. `title_flow.cpp` already
uses the matching two-argument, `u32`-return function pointer for its
initializer tail-call.

This is a typed source reconstruction of a small target-specific primitive;
the actual memory accesses remain inline ARM assembly because standard C++
typed word dereferences would assert alignment that the direct callers do not
all establish. It does not claim MMIO or fault equivalence.

## Contract and caller scope

The pinned original loads two words from `source` before either destination
store, writes those words to `destination` and `destination+4`, then returns
with the original destination bits in `r0`. This ordering preserves equal and
overlapping pointer behavior. There are no calls or global effects.

The direct caller audit found 28 `BL` sites and one initializer tail branch,
including an odd read-only source at `0x004656F1` on two error paths. The helper
requires eight readable source bytes and eight writable destination bytes in
ordinary target memory. Dynamic object extents/lifetimes remain caller-level
assumptions; the static audit is at
[h2-copy-pair-caller-surface-review](h2-copy-pair-caller-surface-review.md).

## Build and differential evidence

The production TU object is
`build/agent-work/H2-semantic/h2-copy-pair-readable-production/compile-tu/leaf_matching.o`.
Its SHA-256 is `b59d0fa7d71b58be50b08ef10a9c0061816c5b37c3f23c5318a39313869bd3e3`.
The extracted function is relocation-free and 20 bytes:
`002091e5043091e5002080e5043080e51eff2fe1`, byte-identical to the pinned
original. The five affected consumer translation units (`leaf_batch19_a`,
`leaf_batch24_c`, `leaf_batch26_c`, `leaf_batch28_c`, and `title_flow`) compile
separately with the updated interface.

Reproducible helper command:

```powershell
python tools/h2_copy_pair_production_experiment.py --output build/agent-work/H2-semantic/h2-copy-pair-readable-production/run-001/checks/production-helper-differential --seed 7 --samples 512
```

It passes 545 original-vs-production cases: all 16 source/destination alignment
pairs modulo four, byte overlap deltas from -7 through +7, the H2
`g_ConfigBytes` address, the actual odd read-only `ERROR` string address, and
512 seeded overlap/alignment cases. The wrong forward-copy control is detected.
The production body equals the original bytes. Report SHA-256:
`81c0570ec34c10c67ef6713961a4674da24ebfc0066d30f5b8b4924e0ee60df6`.

The current offline H2 final image already contains this exact CopyPair body.
Its State-9/10 composition and combined callback/initializer validation are in
[the FillPair integration report](h2-pair-fill-production-integration.md).
Those harnesses retain HLE boundaries and do not prove task scheduling, UI
input, editing, cancel/confirm, persistence, restart, or Azahar runtime
behavior.

## Review and next step

Independent review is pending. The shared interface and consumer builds should
be reviewed together with the source body. Keep H2 open until the authorized
CLI-only runtime scenario validates real input, editing, exit, persistence, and
restart against the original.
