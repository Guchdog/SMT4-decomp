# Independent static contract review: `0x002B8D24`

## Scope and provenance

Read-only review of `docs/agent-work/h2-2b8d24-contract.md` against pinned `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`), the production assembly wrapper, and recorded callers. No compilation, execution, or emulator use. The original function begins at `0x002B8D24` and occupies 360 bytes.

## Review result

The selector interpretation and all 19 jump-table destinations match the pinned words at `0x002B8D38..0x002B8D80`. The unsigned comparison routes every `r1 >= 19`, including `0x80000000` and `0xffffffff`, to the common return with `r0=obj`. The switch map is correct:

- 0, 13, 14, 15 return `obj` without body writes or calls.
- 1 and 10 tail-branch to `0x002AF854(obj+0xC4,2,0)`.
- 2–5 and 16–18 call `0x002AF854` on `obj+0xC4` and `obj+0x1DC`, then tail-branch to `0x001384F0(obj+0x150,0)`.
- 6 loads the word at `obj+0xE4` through VFP, compares its raw bits with `0x3F800000`, returns those original bits when unequal, and otherwise tail-branches to `0x002AF854(obj+0xC4,2,0)`.
- 7–9 call `0x002AF854(obj+0xC4,2,0)`, then tail-branch to `0x002AF854(obj+0x40C,2,0)`.
- 11 calls `0x002BF030(obj+0xC4,7)` and `0x002BF030(obj+0x268,7)`, then tail-branches to `0x001384F0(obj+0x380,0)`.
- 12 checks flags at `obj+0x37..0x3B`; for each set flag it calls `0x002AF854(obj+0x498+140*i,5,0)`, then stores a 32-bit zero at `obj+0x28` and returns zero.

The prologue preserves `r4-r6` and LR; all paths restore the stack and callee-saved registers. VFP use in case 6 is caller-clobbered `s0`. `0x001384F0` is an ARM helper that stores `r1` at `[r0+0x85]` then returns through LR; with the two zero arguments this clears `obj+0x1D5` or `obj+0x405` and preserves the supplied `r0`. These facts agree with the contract.

## Limits and follow-up

No contract error blocks implementation. The existing 0x002AF854 and 0x002BF030 records support bounded dependencies, not arbitrary pointers, aliasing, faults, or every deeper service path. In particular, selector 11 can reach original service `0x00138934` and its deeper `0x002BDAC0` call, which is outside the current fully supported domain. A full replacement therefore needs explicit valid fixtures for both selector-11 calls and must not claim the deeper service as reconstructed.

The recorded H2 caller `0x00286928` supplies a byte-derived selector but does not exhaust the helper's public unsigned selector ABI. An earlier caller attribution placed `0x0029D00C/0x0029D030` in `script_vm_func_0029af60`; the implementation review corrected both sites to `camp_func_0029cee4` and found no direct BL from `0x0029af60` to this helper. The contract correctly warns that other callers must be mapped. No direct runtime H2 state is inferred from these static caller facts.

For a full candidate, compare all selectors, unsigned out-of-range inputs, raw case-6 values, call counts/arguments, return values, memory effects, stack and callee-saved state. Exercise all 32 selector-12 flag masks and include negative controls for the selector table, second helper target, case-6 bit comparison, selector-11 tail byte and selector-12 stride/loop/store. The contract's proposed plan covers these requirements. Verify ARM/Thumb state at retained call boundaries before image integration.

Conclusion: the static contract is accurate for the pinned image and suitable for implementation. Independent candidate review, executable differential evidence, size/placement feasibility, and runtime integration remain outstanding.
