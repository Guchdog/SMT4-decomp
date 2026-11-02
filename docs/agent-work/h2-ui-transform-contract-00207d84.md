# H2 UI transform contract: `0x00207D84`

## Recommendation and scope

The 128-byte ARM routine is a feasible bounded C++ candidate if the current transform-context helper (`0x002C5218`) and projection helper (`0x0026330C`) remain original initially. Its behavior is a single precision 3D transform/projection through shared globals, not a pure function of arguments. Validate with stable, valid context memory and serialized calls because it writes a fixed global scratch vector. **No direct TitleConfig/Audio Settings path to `0x00207D84` was established.** `0x0024B874` is a generic UI transform consumer and may be shared by screens; neither shared file participation nor generic UI callers establishes H2 runtime relevance.

## Entry, ABI, and direct behavior

The pinned body occupies `[0x00207D84,0x00207E04)`: ARM instructions through `0x00207DF4`, followed by literals `0x004EA81C`, `0x00472550`, and `0`. Entry r0-r3 are unused. It pushes r4/lr and allocates 0x20 bytes (40 bytes total), then calls `0x002C5218()`.

`0x002C5218` loads the literal `0x0044EA58`, dereferences `[0x0044EA5C]`, then returns the word at that object+0x80. Thus the pointer P used as projection context is:

```text
P = *(*((u32*)0x0044EA5C) + 0x80)
```

There are no null checks in this chain. The helper is integer-only and has no stack frame.

The transform routine uses fixed vector state V=`0x004EA81C`; its vector is V+0x100=`0x004EA91C`. It copies four single-precision words from V+0x100 to fixed scratch `0x00472550`, then copies the first three words from that scratch to its local input vector at entry-SP+0x10. It calls `0x0026330C(out=entry-SP, index=0, context=P, input=entry-SP+0x10)`.

The projection helper preserves r4-r6 and SP, allocates 0x20 bytes, and uses VFP s0-s15. It calls `0x002AD6D8(out=helper-SP+4, matrix=P+0x38, input)` which computes three affine single-precision components from the 12-float matrix and xyz input. The projection helper then reads P+0xA8..0xE4, performs single-precision multiply/add operations and divides by a homogeneous denominator. For index 0 it uses the first float at `0x00409398` (400.0); the next table entry is 320.0. Its literal constants are 1.0, 0.5, and 240.0. In terms of affine output `(x,y,z)`:

```text
w  = P[0xD8]*x + P[0xDC]*y + P[0xE0]*z + P[0xE4]
nx = P[0xA8]*x + P[0xAC]*y + P[0xB0]*z + P[0xB4]
ny = P[0xB8]*x + P[0xBC]*y + P[0xC0]*z + P[0xC4]
out.x = 400.0 * (1.0 - ny/w) * 0.5
out.y = 240.0 * (1.0 - nx/w)
out.z = z
```

The helper writes out.x/out.y as floats and copies the raw bits of z to out+8; the outer wrapper ignores its r0. Afterward, the wrapper writes `0.0f` at its local +0x0C and stores four words `[out.x,out.y,out.z,0.0f]` to V+0x100 in that order. It then loads local +8 into s0 and returns. Machine-visible return state is r0=V+0x100 and s0=out.z (float); no input argument determines either. Both audited caller sites ignore these return registers and read the global vector. The wrapper preserves r4/SP; it uses caller-saved VFP registers, does not save FPSCR, and performs no VFP comparison itself. All transform/projection arithmetic is `.f32`; division and rounding follow the active VFP environment.

## Caller `0x0024B874`: the two calls and visible result

The caller preserves r4-r8/lr and stores r0 in r5, r1 in r4, r2 in r7, and r3 in r6. It first runs unrelated UI helpers at `0x002698F4` and `0x00269768`, writing caller fields +0x14 and +0x18. If byte `[r4+0x9C] != 2`, it takes another `0x00269768` path and returns after writing `s0` to `[r5+0x1C]`; neither `0x00207D84` call is reached.

When `[r4+0x9C] == 2`:

1. Copy four words from `[r5+0..0x0C]` to V+0x100, then call `0x00207D84` at `0x0024B8E0`. Copy the resulting four words to V+0x110, preserving the fourth word at V+0x11C.
2. Copy four words from `[r6+0..0x0C]` to V+0x100, then call `0x00207D84` again at `0x0024B908`.
3. Subtract V+0x110 from V+0x100 as four ordered `vsub.f32` / `vstr` operations, storing deltas back at V+0x100, +0x104, +0x108, +0x10C. If delta x and delta y compare equal to 0.0f, store 0.0f to `[r5+0x1C]`. Otherwise call `0x0024C62C` with s1=delta x and s0=delta y, multiply its s0 result by literal `0x3CC90FDB` (approximately 0.02454369), and store that float to `[r5+0x1C]`.

Thus the two calls transform two input 4-word vectors in place using the same global context, keep the first result as a baseline, and expose a scalar derived from the projected delta. The caller’s two uses do not consume the wrapper’s r0/s0 returns. The zero test checks only the first two delta components; z/w do not decide that branch. The semantics/units of the final `0x0024C62C` result are outside this wrapper and should remain an original dependency until separately audited.

An aligned ARM scan found exactly these two direct BL sites to `0x00207D84`, both inside `0x0024B874`. The call is statically reachable only through its `[r4+0x9C]==2` caller branch. The caller has many aligned callers across UI-engine functions; that static census does not establish that a titleConfig/audio-settings screen invokes it in runtime.

## Valid domain and differential plan

Start with a mapped, aligned, writable V+0x100 vector; ordinary non-overlapping V and `0x00472550` scratch; a valid pointer chain through `0x0044EA5C`; and a valid P region through at least P+0xE4. Serialize calls because the scratch is global. For numerical tests, begin with finite ordinary floats and nonzero homogeneous denominator. Explicitly characterize zero/near-zero denominator, infinities, NaNs, signed zero, active rounding mode, and FPSCR exception flags before claiming those cases. Do not infer pointer validity, camera identity, or caller scheduling from literals alone.

Direct tests should compare all four words at V+0x100, the complete scratch vector, r0 and s0 returns, callee-saved registers/SP, and relevant FPSCR state against the pinned original. Cover index 0, matrix basis vectors, affine translation, nontrivial perspective terms, negative coordinates, and denominator boundaries. The caller-composition tests should cover both values of `[r4+0x9C]`, exact zero/nonzero delta x/y, distinct r5/r6 vectors, all four delta stores, calls to `0x0024C62C`, and final `[r5+0x1C]`. Include mutations for swapped x/y coefficients, omitted perspective division, index 1 instead of 0, missing w=0 store, and an incorrect caller zero gate. Keep `0x002C5218`, `0x0026330C`, `0x002AD6D8`, and `0x0024C62C` original for the first bounded compositions.

This report is static only: no compile, ARM execution, differential, caller execution, or emulator run. It establishes no physical audio/input mapping, UI scheduling, natural H2 reachability, or whole-screen behavior.

## Run002 refresh: current source, caller, and H2 scope

All 13 hashes declared by `h2-ui-transform-contract-00207d84/run002` matched.
The pinned original image remains SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
128-byte target extent hashes to
`b239f86b9599bbe933bb8181a0fd34fd9e5efad8ea6c3b45a6ad0df2372af3ce`. The
current target source is `src/engine/leaf_batch30_c.cpp` (SHA-256
`5d14bc774791213e7198633abcf259704d7606619a8b5e2b5990f3d06dbb829e`), and
the current 284-byte caller source is `src/engine/leaf_batch41_a.cpp` (SHA-256
`7e81b244bad7117a7d69b693f5335a036a74087deb8d1b7ecc04a6eb6d3ee441`). The
current `config/functions.csv` and H2 milestone hashes are respectively
`33e8ad813dc73b3198e54cab74b3eb22f4b0bfd18db62300939584e94ab96476` and
`653ca10c15d612426a6f01822b85ee3a9d522dee2872674bfdd86e674e032d1a`.
The current ledger still records `0x00207D84` as a 128-byte `matching` UI
function and `0x0024B874` as a 284-byte `matching` UI caller; this task made no
candidate and proposes no ledger change.

Fresh ARM decoding still finds the same two calls inside `0x0024B874`, at
`0x0024B8E0` and `0x0024B908`, both guarded by caller byte `[r4+0x9C] == 2`.
An aligned ARM `BL` encoding scan of the pinned text finds exactly those two
direct callsites and no aligned exact pointer word to `0x00207D84`. The current
source contains generic UI part spawn/live-tail uses of `ui_func_0024b874` in
`asd_runtime.cpp` (current SHA-256
`726f3e3192b8b72a3213809f4c67f67ce7db438afacd6feec5a38ee4f907c451`); these
identify a generic transform consumer, not a TitleConfig caller. This source
was a supplemental read, not a run002 packet pin. The active H2 milestone continues to identify its
TitleConfig initializer, calculation, drawing, secondary callback, and ready
gate, with no direct call chain to this transform established by the current
source or assigned milestone evidence. This bounded static search cannot rule
out indirect/computed calls, Thumb callers, or a runtime registration path;
it therefore supports the explicit conclusion that direct H2 relevance is
unestablished, not a proof that no such path can exist.

This remains static-only evidence. The 128-byte function and its caller were
rechecked against the unchanged pinned image; no compilation, differential,
emulator, or production-source edits were made.
