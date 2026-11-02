# Independent review: range helper `0x002892C0` — run001

## Recommendation

The C++ body is supported for the exercised object domain, but it is not safe to copy into the original 124-byte slot: the compiled body is 132 bytes and would overwrite the first 8 bytes of the following ledgered function `Filter4Poly_func_0028933c`. A production trampoline is physically feasible in the remaining verified H2 `.text` tail after the current Calc body. I recommend a separate integrator-owned merged-patch builder and final-VMA differential before production promotion.

A conservative candidate placement is `0x003FEE64`. The pinned zero-filled tail runs from `0x003FE624` through `0x003FEFFF`. Current Calc occupies 2,096 bytes beginning at `0x003FE624`; the plan conservatively reserves through `0x003FEE64`, leaving 412 bytes from that aligned boundary. The 132-byte helper body fits there and ends at `0x003FEEE8`, leaving 280 bytes. I verified those 132 source and Calc-patched bytes are zero and unallocated in the current Calc patch records. The branch from `0x002892C0` to `0x003FEE64` is aligned, remains within ARM `B` range, and preserves LR. The candidate has no relocations and returns through `BX LR`.

This is a viable placement design, not an already produced or validated production IPS. Keep production promotion deferred until a merged patch redirects the original entry to that body and the original caller path passes at the final address.

## Provenance and independent rerun

All 15 declared run001 input hashes recompute exactly. Pinned identities include:

- Original image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Candidate source: `e37ee409d29da112e09a5a0cb01c42eb012957ee47165913fbbcb64aa67b15e8`
- Original frozen report: `c6eacb1c3db31dfcf60e386b3cc2d7c92c6ea1fcfd2b033817f82a4a6c1842c8`
- Reported candidate object/body: `df7bd85463fff8ff15b14dea31a7b09fad6fd9113921bc4c08de3f432e48626c` / `753b0f533019e197ea4c51d3ab1ececa579e57fbfe08defcee1f164114fe31df`

I reran `tools.h2_2892c0_experiment` with its output redirected in memory to the distinct directory `build/agent-work/H2-semantic/h2-titleconfig-002892c0-review/run001/checks/reviewer-rerun/`. This used one candidate-TU compile and did not overwrite the implementer output. The independent report has the same source, runner, object, and body hashes and passes 1,220 direct comparisons, 360 wrapper comparisons, and the negative control (`wrong-branch-target`/strict-bound mutation as defined by the harness: changing the strict count/index comparison is detected). Rerun report SHA-256: `c6eacb1c3db31dfcf60e386b3cc2d7c92c6ea1fcfd2b033817f82a4a6c1842c8`.

## Contract and differential coverage

The helper returns 1 and applies ARM 32-bit wraparound to its unsigned arithmetic while interpreting comparisons as signed 32-bit values. It handles count zero with ordered writes `+0x24 = 0`, then `+0x20 = 0`. Otherwise, index is clamped to zero when signed-nonpositive and to `count-1` only when signed `count < index` (so equality with count is retained). It computes wrapped `delta = index - start`. For signed-negative delta it writes `+0x20 = index` then `+0x24 = 0`; otherwise it writes `+0x24 = delta`, clamps visible to count with signed comparison, calculates wrapped limit, and on signed `delta > limit` writes `+0x24 = limit` then `+0x20 = index-limit`.

The candidate mirrors those branches with explicit unsigned arithmetic, `signed_less` comparisons, and volatile stores. The `uint32_t` to `int32_t` conversion for values above `INT32_MAX` is implementation-defined in the C++ standard; the ARMv6K Clang target behavior is exercised by the compiled differential, but portability to a different implementation is not established.

The direct matrix covers 196 directed boundary combinations (seven values each for count and index crossed with four visible/start pairs) plus 1,024 deterministic random vectors using seed 2892. The wrapper matrix exercises the original `0x0029EDFC` with disabled byte values 0, 1, and `0x80` over 120 fixtures each. Comparisons include return, the full 256-byte object, ordered non-stack writes, helper entry arguments, completion, SP and `r4-r11`. Disabled caller paths verify that the original wrapper returns without entering the helper. A mutation changing the strict count/index comparison is detected.

No concrete semantic counterexample emerged in these tests. The contract is bounded to readable aligned object memory. Invalid/misaligned pointers, malformed objects, concurrent access, MMIO, CPSR/scratch-register identity, VFP state, and all possible caller domains are not established.

## Caller and production placement

The caller run keeps original `0x0029EDFC`. It branches from the original helper entry to a test-only trampoline at `0x01001000`, where the compiled body runs and returns through the caller’s original LR. This establishes wrapper-to-candidate behavior under the fixtures; it does not establish a production cave or final-address installation.

In-place placement is ruled out by span arithmetic: `[0x002892C0, 0x0028933C)` is the original 124-byte slot, while 132 bytes would end at `0x00289344`, overlapping 8 bytes of `Filter4Poly_func_0028933c`. I also scanned the pinned image’s aligned ARM B/BL/BLX-immediate encodings and aligned absolute words; none target the helper’s interior `[0x002892C4,0x0028933C)`. This bounded static check supports redirecting its entry but does not rule out runtime-computed or external references.

For a trampoline, the verified code cave is the aligned `.text` page tail `[0x003FE624,0x003FF000)`, capacity 2,524 bytes. The existing production Calc patch record writes only 2,096 bytes at `0x003FE624`; at conservative address `0x003FEE64`, its remaining 412-byte tail can host this 132-byte body. The pinned original tail is zero-filled, the proposed 132 bytes remain zero in the Calc-patched image, and no current Calc patch record allocates them. The existing H1 test cave at `0x003FE720` lies inside the Calc body and is not treated as free. A new builder must add the `0x002892C0` entry branch plus a disjoint record at `0x003FEE64`, preserve the Calc blob and its four rebased ABS32 references, reject overlap, and prove IPS application recreates the tested image. Then rerun the wrapper path using the final cave address.

## Limits and next action

The frozen report records runtime `not_run`. The test trampoline deliberately avoids clobbering adjacent original code, but it is not a production placement. The residual cave appears sufficient, so lack of space is not the blocker; the missing evidence is the merged patch builder/manifest and final-address wrapper differential. The original helper’s arithmetic and state updates are supported for tested fixtures, while production installation and runtime behavior remain open.
