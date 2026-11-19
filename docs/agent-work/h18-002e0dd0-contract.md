# Contract recon: 0x002e0dd0

## Identity and evidence scope

The ledger row is `0x002e0dd0,724,matching,engine,engine_func_002e0dd0,src/engine/leaf_batch45_a.cpp`. The declared span is ARM code, but its first complete control-flow body is only `0x002e0dd0..0x002e0e58` (0x8c bytes including literal at `0x2e0e58`); the next word at `0x2e0e5c` begins a second coherent-looking VFP-heavy routine that runs through `0x2e10a0`. Do not assume the latter is part of this callable contract: no direct branch or aligned pointer references to `0x2e0e5c` were found in the static scans, but that does not prove it is unreachable or dead. It has no separate row in the examined ledger context.

The source wrapper is a naked `.arm` wrapper containing `.hword` encodings. Reference disassembly was generated with `python tools/split_asm.py --addr 0x002e0dd0 --out-dir build/agent-work/batch-h18-001/h18-contract-002e0dd0/run-001/disasm`. It identifies a six-register push/pop and ARM direct calls plus one ARM BLX. The input code image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

## Recovered callable contract (facts)

AAPCS-style entry arguments observed: `r0`, `r1`, `r2`, `r3`, and a fifth 32-bit argument at entry `[sp]`. Prologue saves `r4-r8,lr`, making the fifth argument visible at `[sp,#0x18]`. Callee preserves those saved registers and returns by `pop {...,pc}`. The body reads a global pointer slot at `0x00464fac` (literal base `0x00464fa8`, then offset +4), then reads an object field at `+0x18` for helper calls.

The first helper call `0x00263534` receives object-field pointer in `r0`, entry `r0` in `r1`, entry `r1` in `r2`, and entry `r3` in `r3`. The helper result is masked with `0x80000000`. If bit 31 is set, the function returns integer 5 immediately. Otherwise it calls `0x002b5c2c(entry_r2)`, doubles that helper result into `r3`, then calls `0x00248e58(object_field, 0x6e, entry_r2, doubled_helper_result)`. A second `0x00248e58` call uses `(object_field, 0x65, entry_r3, fifth_entry_argument)`. Finally `0x002390dc(object_field)` is called and integer 0 is returned. Thus observed return domain is exactly `{0,5}`; branch condition is the sign bit of the first helper return. The first branch skips all later helpers.

There are no explicit stores in the `0x2e0dd0` body. Its writes/side effects, if any, are mediated by helpers and the object/global reached through `0x00464fac`; their meanings and aliasing are unresolved. The global slot itself is read-only in this body.

## Caller evidence

Two direct aligned ARM BL references were found by scanning the code image from load base `0x00100000` in four-byte steps and decoding ARM BL/BLX immediates:

- `0x003bbdfc` in `ui_func_003bbdb8` (`src/engine/leaf_batch29_c.cpp`). The caller prepares `r0` from its preceding `ui_func_00357a28` result, `r1` from `*(0x0043de3c-0x84)` (`0x0043ddb8`), `r2=0x0043de3c`, `r3=[caller_arg0+4]`, and fifth stack argument `0x1200`. It ignores `r0` after return and proceeds to `engine_func_0021f480`; this call path supports the side-effect interpretation but does not reveal the helper effect.
- `0x003bc070` in `ui_func_003bbfb0` (`src/engine/leaf_batch37_c.cpp`). It sets up the same argument shape and fifth argument `0x1200`. After return, caller compares `r0` to 5. Equality takes the path that sets `r0=0x11`; inequality executes `movne r0,#0`, branches to `0x003bc02c` (the `add sp,#0x14` instruction), then returns 0. Thus the wrapper's observed 5 maps to `0x11`, while its non-5 result 0 remains 0. The `mov r0,#0x81` at `0x003bc028` is before the branch target and is skipped on this path.

An aligned word scan found no pointer words equal to `0x002e0dd0/0x002e0dd1` or `0x002e0e5c/0x002e0e5d`. This misses unaligned data, relocated/encoded pointers, Thumb/tag transformations other than low-bit variants checked, and indirect dispatch not represented as a literal pointer. The direct-call scan is limited to aligned words interpreted as ARM instructions and does not identify calls through tables or dynamically computed branches.

## Bounded reconstruction proposal and dependencies

A safe first C++ slice is a typed routine with explicit `u32` inputs `(arg0,arg1,arg2,arg3,arg4)` that preserves the observed `{0,5}` return and call order, while modeling the object/global access and helper calls behind named interfaces. Do not assign domain names to arguments, keys `0x6e/0x65`, global object, or helper outputs yet. The `0x00263534` high-bit gate and caller `0x003bbfb0`'s `5 -> 0x11`, `0 -> 0` mapping form the best minimal contract to test. Preserve the second helper's signed/unsigned bit test exactly until its contract is independently recovered.

Dependencies to resolve before claiming full semantic recovery: global slot/object layout at `0x00464fac` and field `+0x18`; behavior/effects/return range of `0x00263534`, `0x002b5c2c`, `0x00248e58`, and `0x002390dc`; and identity/entry status of the code beginning `0x002e0e5c`. No dependency bodies were analyzed for this report.

## Validation needs (not run; this task is static-only)

The later bounded offline ARM differential runner covers the wrapper with object/global fixtures and helper stubs, and composes caller continuations for both `ui_func_003bbdb8` and `ui_func_003bbfb0`. For `ui_func_003bbfb0`, it executes both the non-5 path through `0x003bc02c` (result 0) and the 5 path (result `0x11`). A previous review misread `0x003bc02c` as the preceding `mov r0,#0x81` at `0x003bc028`; the pinned bytes show the branch skips that instruction. Until helper/global contracts are recovered, this validates only wrapper interaction with modeled dependencies, not whole behavior.

## Provenance

Prepared packet hashes must be checked by the coordinator's handoff validator. This report uses only the packet's pinned files plus static disassembly of `code.bin` and the additional direct-caller wrapper `src/engine/leaf_batch37_c.cpp`. No production C++ or ledger was changed.
