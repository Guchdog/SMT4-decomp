# H4 Navi helper contracts review

## Result

All 21 declared hashes in run-001/task.json match. I reviewed the two static recon reports against pinned ARM disassembly of `0x00220888` (0x370-byte ARM function) and `0x0039C944` (0x240-byte ARM function), then compared the relevant residuals and snapshots with the pinned run-004 original/patched JSON. The control-flow maps and unresolved-dependency cautions are useful for dependency recon. Each report needs one material return/address correction before its contract is reused verbatim.

Pinned image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Recon report hashes: `h4-navi-helper-00220888-recon.md` `7cc00020ecb95ab99a81c3cedbb00572ec001a6c66b19a21431dd7c1a53d45eb`; `h4-navi-helper-39c944-recon.md` `30400c8c73cb2635928d7839ddaf8797dd600b1ca51466385efdf301a36fbc41`.

## `0x00220888`

The function boundary, ARM mode, direct callees, six-step loops, field widths and store ranges are supported. At entry it replaces incoming `r0` with the `0x0043DA28` literal address, saves `r4-r10,lr`, loads `r4 = *0x0043DA2C`, and calls `0x002B9094`; this helper reads the byte at `+8` from `*0x0043DCB4`. If `[r4+0x4C7]` is nonzero, the function immediately returns that helper's residual `r0` (the returned kind byte). If the gate is zero, kind 1/2, kind 6, or the other-kind path runs its six iterations. The direct secondary helper `0x002B90A8` reads a signed halfword at `+0x64E` from `*0x0043DCB4`.

**Correction — loop-path return:** the recon calls the active-path return a path-specific residual, as though it were unconstrained by the loop tail. Every active path rejoins at its common iteration tail, sets `r0=r4+r5`, increments `r5`, and exits only after `r5` reaches 6. Therefore all three completed non-gated six-iteration paths return `r4+5` (the last loop's object-plus-index address). The gated path remains different: it returns the residual kind byte from `0x002B9094`. There is no fixed return across all calls, but the active-path result is deterministic and should be documented.

The run-004 trace records `r4=0x086FE980` for the input object and `r0=0x086FE985` at `0x00399DB8` in both profiles. That is exactly `r4+5`, independently consistent with completion of a non-gated loop. The raw trace does not stop inside the helper, and its `+0x4C7` byte/kind are not among the captured fields, so it does not distinguish kind 1/2/6/other or identify any specific output branch. The callback then reloads its own `+0x0C` at `0x00399DB8`; thus the helper residual is overwritten for callback control flow. Do not call the value a generic input pointer or physical/logical input value.

The per-path branch descriptions are broadly accurate. The six target slots are `+0x4B8..+0x4BD` and `+0x4BE..+0x4C3`, with the special writes that can hit `+0x4B7+i` and overlap the preceding slot, and the `+0x4BD+i` family in the kind-6 path. Special branches may skip some normal-index assignments or flow back to general handling; retain the exact repeated helper calls and overlapping byte stores. No type, initialization/lifetime, extent, or upstream-state contract for either global-derived object is established. Those dependencies remain a valid blocker to implementation and a suitable next dependency-recon target.

## `0x0039C944`

The ARM boundary and 576-byte extent are supported; the disassembly reaches normal code through `0x0039CB60`, with trailing literal/code-looking words not attributed to reachable body. ABI/frame, input `r4`, derived `r5=object+0x5A8D`, `r6=object+0x162`, VFP save, initial `+0x10 & 0x20000` split, calls, coordinate/repeat fields, conditional object stores and path-dependent `r0` are supported. The signed `+0x54` comparison to 99, reset-on-coordinate-change behavior, bit clearing of `0x30000`, and the branch on global byte `[0x0049F91C+0x18]` are also correctly represented. The four direct callees and unvalidated pointer/object effects are appropriately left unresolved.

**Correction — float address:** in the common update path, the multiplier is read through literal `0x0044CDC8` (`LDR r0` at `0x0039CA18`, then `VLDR s1,[r0]`), not from `0x0049F91C`. `0x0049F91C` is separately loaded and its byte at `+0x18` is used as a gate in this helper. The recon currently conflates those globals in its sentence about the multiplier. The coordinate calculations separately use the float returned in `s0` by `0x0039FA68` as the divisor; neither divide site guards zero, infinity, NaN or other numeric edge cases. The report correctly identifies this divisor contract as unresolved and implementation-blocking.

The accepted run-004 callback trace reaches `0x00399DAC` with `r0=0` in both original and patched samples, after the callback's conditional `BLNE 0x0039C944`; this is the helper return in that one invocation. It is not a general zero-return contract. The same captured callback later reaches `0x00399DCC` after `0x0039AF30` with `r0=0`, then returns to `0x001A95E8` with `r0=0`. No helper-entry breakpoint or internal branch/result capture was used for `0x0039C944`; its direct object changes, divisor, and transitive state effects are not dynamically established.

The unresolved contracts for `0x002C01B0`, `0x0039FA68`, `0x00231F58`, and `0x00231B38`, along with validity/lifetime of object+`0x162` and possible zero divisor, are stated precisely enough to block implementation and direct next dependency recon. Correct the global multiplier address before relying on this recon's numeric/dataflow description.

## Recommendation

Both reports are acceptable as bounded dependency-recon maps after the explicit corrections above; neither is an implementation-ready contract. For `0x00220888`, update the normal-loop return to `r4+5`, retain the kind-byte gated return and the run-004 sample caveat. For `0x0039C944`, change the multiplier source to `0x0044CDC8` and keep `0x0049F91C+0x18` only as the gate. Then continue static dependency recon for the global-derived object and the four direct callees, especially initialization/pointer validity and the `0x0039FA68` divisor range. No build, test, emulator, save access or guest writes were used.


## Run-002 correction check

All 21 declared input hashes in `build/agent-work/H4-semantic/h4-navi-helper-contracts-review/002/task.json` matched at review time. The refreshed `0x00220888` recon now explicitly distinguishes the gated `[r4+0x4C7]` return (the kind byte left by `0x002B9094`) from every completed non-gated loop return (`r4+5`). It retains the run-004 observation `r0=0x086FE985` at `0x00399DB8` as a sample consistent with object+5, while correctly stating that the capture does not expose the helper's internal branch or establish a general return path. Its refreshed handoff summary agrees.

The refreshed `0x0039C944` recon identifies `0x0044CDC8` as the common-path multiplier source and preserves `[0x0049F91C+0x18]` as a separate gate byte. Its refreshed handoff summary agrees. The run-004 `r0=0` at `0x00399DAC` remains a single sampled helper return, not a general return contract. The prior report's run-001 hashes and correction wording above are historical; run-002 pins the refreshed recon files at `65e6c4560fd318347c58ec556d467900b1e77565e55c2c6979baf58cf9e2b639` (`0x00220888`) and `dad01cf64a095cfdb3c799f57a9c7ae6f60825e67256deace47c25aab380396b` (`0x0039C944`). No broader runtime or implementation claim follows from this document-only refresh.
