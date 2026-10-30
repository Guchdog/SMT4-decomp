# H4 Navi query and coordinate-helper contracts review

## Disposition

Both static recon reports are acceptable for their bounded ARM claims. The query wrapper/shared-reader contract and the two host-pair helper contracts agree with the pinned instructions and the inspected Navi callsites. No material correction is required. Keep the direct-call scans bounded, preserve the pointer/fault/concurrency limits, and do not infer physical-input, coordinate-unit, player, or movement semantics.

All 22 declared inputs in this combined review packet match. I also recomputed every input hash in the two underlying recon task packets (15 query-task inputs and 16 coordinate-helper-task inputs); each matches. The reported recon handoffs pin the expected report hashes:

- Query recon report: `ba0553aa0009ef88c785c29d595a48df7d3a2137809e41686f98646422d87f02`; handoff: `8e775cdee3a4e37168d0c2706be03ef1131d222c5552560ddf3c4ae3b36abdce`.
- Coordinate-helper recon report: `52848a6eae8f0f62282e9a75188c1d509c940d093b54e539c93f3aba58b97f3d`; handoff: `d0bec1e09b9a22883468e175cb078af030cce7f8375fec54fb0ccbb9d70d58a1`.
- Pinned `code.bin`: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

## Query reader: `0x002C01B0` and `0x002C01B8`

Independent ARM disassembly confirms that `0x002C01B0` is an 8-byte wrapper (`mov r2,#0; mov r0,r0`) that falls through to the 212-byte shared reader at `0x002C01B8`. The shared reader loads the absolute state address `0x004E3CD4`, pushes/restores `r4-r6`, reads the initial state byte at `+0x10` and halfword at `+0`, and returns `r0=1` or `r0=0`.

Modes and success conditions in the recon are correct: mode 0 requires byte `+0x10 == 1`; mode 1 also requires `+0x11 == 0`; mode 2 requires `+0x12 == 1` after the `+0x10` check; mode 3 requires `+0x10 == 0` and `+0x11 == 1`; other values fail. For nonzero modes the implementation reads `+0x11` before mode-specific comparisons. On success it stores the zero-extended halfword at state `+0` as a 32-bit word through nonnull `r0`, then reads state `+2` and stores that zero-extended halfword as a 32-bit word through nonnull `r1`. It returns success even if either/both outputs are null. Failure performs neither output store. Since the second halfword read follows the first output store, output/state aliases and equal or overlapping output pointers can affect the final values; this ordering and 32-bit write width are material contract details. No pointer/alignment/fault checks or coherent snapshot guarantee are present.

The inspected Navi mode-0 caller at `0x0039C980` prepares `r0=sp+4`, `r1=sp`, calls the wrapper, then branches on the returned status at `0x0039C984`; on success it reads the separately configured global gate. The `0x0039B5CC` mode-0 caller similarly uses stack-local outputs and tests the return before its success route. The wrapper at `0x003C303C` sets mode 3 and branches to shared `0x002C01B8`; `0x003C3034` sets mode 1. These are distinct mode contracts. The listed direct-call scan is an aligned ARM immediate-call scan over its stated text interval; it does not prove there are no indirect, Thumb, or out-of-range references.

The reader uses the absolute state block at `0x004E3CD4`, not the separate `0x004E3C28/0x004E3C48` axis-reader buffer snapshots. The two halfwords and mode bytes are raw data only; no physical input or gameplay meaning is established.

## Global pair helpers: `0x00231F58` and `0x00231B38`

The code bytes and literals support the recon:

- `0x00231F58` loads literal `0x0044CDF0`, dereferences that slot once, adds `0x38`, and returns the resulting address in `r0`. It does not read the pair, use its incoming `r0`, or write memory. A null slot still produces address `0x38`; dereference/fault behavior belongs to later callers/environment.
- `0x00231B38` loads literal `0x0044CDF0`, loads two source words via `ldm r1,{r1,r2}`, dereferences the global host slot, and stores those words in order to host `+0x38` and `+0x3C`. The host pointer remains in `r0` as a residual return value; it is not a success flag. The source words are loaded before the host dereference, the stores are separate/non-atomic, and no pointer/range/alignment validation or synchronization appears in the body.

At `0x0039C944`'s delta path, the getter call at `0x0039CA44` returns the host pair address. The caller loads the pair words into locals, combines them with the two deltas scaled by the separate accessor result saved in `s16`, and passes the local pair by `r1=sp` to setter at `0x0039CA88`. On the separate query-coordinate branch, the caller combines query outputs with object fields and passes a stack pair (`r1=sp+8`) to setter at `0x0039CAEC`; this branch does not use the getter. The pair words, object-relative fields, and divisor source at host `+0x34` remain distinct dataflow values. The selected additional getter caller at `0x0039B6BC` copies two returned words into object-relative `+0x34/+0x38`, as reported. Other direct references remain xref inventory unless their full caller dataflow is separately traced.

The “coordinate” label in the recon is properly limited to observed float arithmetic and pair handling; the helper bodies themselves establish only a global-host pair address/copy contract. Host-slot lifetime, retargeting between getter and setter, pointer faults, alias consequences, alignment, concurrent observation, and atomicity requirements remain unresolved.

## Runtime claim boundary

The run-006 and run-007 reports are `observed`, but neither report asserts that the query ran. Their probe lists do not include `0x0039C980` or `0x0039C984`; run-006 records callback/helper entry through `0x0039C9E8`, while run-007 additionally records `0x0039CA90` and no-hits at the greater-than continuation/accessor/divide probes. The query recon correctly treats the bit-set route as static possibility and says that the reports do not supply a query return/output observation. No query runtime result should be inferred.

The static caller path and runtime route do not prove query state production, player ownership, coordinates, physical controls, movement, interaction, camera movement, or zone transition. A passive stop at `0x0039C980/0x0039C984` with validated stack pointers and state bytes would establish an invocation only; broader semantics require separately supported evidence. No emulator, build, private save/profile, or guest-memory operation was performed for this review.
