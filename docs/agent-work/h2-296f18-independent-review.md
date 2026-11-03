# Independent static review: H2 cursor-axis setup `0x00296F18`

## Recommendation

I found no behavioral counterexample in the readable candidate for aligned,
valid writable memory. The pre-existing compiled shape object is 68 bytes,
fits the 72-byte original slot, has no relocations, preserves the raw r0 block
pointer, and decodes to the same field values, access widths, and ordered stores
as the pinned ARM body. This supports the bounded initializer contract.

I do not recommend promotion from the current evidence package yet. The runner
does not assert that the H2 setup took the two expected axis calls, does not
record their argument tuples, and does not assert the expected final axis0 and
axis1 records. Its H2 acceptance condition only requires at least one identical
callsite from a four-entry allowlist. The H2-specific result is therefore
weaker than the report wording implies. Persist the direct run report and close
these H2 assertions before promotion. The ledger still says `matching` even
though the compiled candidate body is 68 bytes and is non-identical; coordinator
integration must classify it truthfully if promoted.

## Contract and candidate comparison

The pinned original occupies `[0x00296F18,0x00296F60)` (72 bytes). It accepts
`r0=block`, signed `r1=start`, raw `r2=metadata`; r3 is unused. It stores, in
order: metadata at `+0x1C`; zeros at `+0,+4,+8,+0x0C,+0x20`; start at `+0x10`;
constant 2 at `+0x14`; zero at `+0x24`; raw start at `+0x18`; signed clamp
`start<=0 ? 0 : start` at `+0x18`; and constant 6 at `+0`. All stores are
32-bit ARM `STR`s. It ends with `BX LR` and never changes r0, so raw r0 remains
the input block pointer. There are no calls, globals, stack accesses, or fault
guards.

The candidate in `src/engine/leaf_batch11_b.cpp` expresses the same fields and
write order with `volatile u32` accesses. The persisted shape artifact
`build/agent-work/H2-semantic/h2-cursor-axis-setup-00296f18-convert/run001/shape/candidate.o`
contains `ui_func_00296f18`, 68 bytes and no relocations. Its final clamp
instruction is `BIC r1,r1,r1,ASR #31`: for a signed value it yields zero for
negative inputs and leaves nonnegative inputs unchanged, including zero. The
compiled body leaves r0 intact and returns through `BX LR`; the runner pads the
four remaining slot bytes with one ARM NOP after the return. This review did
not compile or run the candidate.

The exact H2 `UiListCursor_Setup` entry at `0x0029FAE8` receives cursor,
`total=3`, `visible=3`, `cols=1`, and stack values `0,1`. Static ARM flow shows
the expected calls to this helper at `0x0029FBC4` for axis0 with
`(r0=cursor,r1=3,r2=3)`, and `0x0029FC44` for axis1 with
`(r0=cursor+0x28,r1=1,r2=1)`. The sibling slot helper later sets the axis query
bytes. The H2 record contract describes the resulting axis0 fields/IDs as flags
6, width 3, start 2, threshold/count 3, IDs `(6,5,32,32,15,14,32,32)`; axis1
has width/threshold/count 1 and IDs `(3,4,32,32,12,13,32,32)`. The two `r1`
start arguments to this candidate are 3 and 1; the constant start-related
record word at `+0x14` is separately initialized to 2.

## Runner review and evidence limits

`tools/h2_296f18_cursor_axis_experiment.py` provides a useful direct differential
design: a pinned-image check, final in-slot replacement, IPS replay and
outside-slot check; 61 start/metadata fixtures including signed extremes,
high-bit metadata, seeded raw r3, and the H2 `(3,3)` case; full block bytes,
ordered writes, r0, callee-saved GPRs/SP and fault comparison; a mapped-boundary
fault control; three source-mutation controls; and an actual original
`0x0029FAE8` setup composition. It also compiles the affected caller TU.

The concrete H2 composition assertion is too permissive. It currently passes
when the observed trace is merely nonempty, equal between base/staged, and
contains only addresses from `(0x0029FB6C,0x0029FBC4,0x0029FC28,0x0029FC44)`.
It would accept one call, the wrong recognized site, or an unexpected pair of
recognized sites. The hook records only `LR-4`, not r0-r2. It does not compare
the post-setup axis record to expected H2 values. Make it require exactly
`(0x0029FBC4,0x0029FC44)`, record and assert the two argument tuples above, and
assert the documented axis0/axis1 fields and ID bytes after setup. This ensures
the real caller fixture has the intended H2 meaning rather than merely matching
the original on an arbitrary initialized block.

The direct runner compares the raw return even though the C++ declaration is
`void`; that is appropriate here because the original preserves r0 and the
persisted compiled body also does. Its mapped-boundary control compares the
Unicorn fault string but not the PC at which the fault occurred; include the
fault PC in that control if fault-point equivalence is claimed. The direct
fixture uses aligned mapped RAM only; unaligned pointers, aliases, concurrent
observers of intermediate stores, and MMIO remain out of scope. The mutation
controls catch clamp, metadata-offset, and flags errors, but do not independently
exercise the transient raw-start store or field-store ordering.

The integration artifacts under `build/h2-1ff3c4-integrated/run003` show four
bounded TitleConfig_Calc comparisons with a manually initialized cursor state.
That harness does not call `0x0029FAE8` to produce that state. Conversely, the
direct `0x0029FAE8` runner does not exercise the complete TitleConfig caller.
Keep these as separate evidence claims; neither establishes runtime screen
reachability or full TitleConfig lifecycle behavior. At review time, the
conversion task output directory contains only the compiled shape metadata and
no persisted direct runner report, so I cannot independently inspect its
reported differential rows.

## Required next validation

Before promotion, rerun the frozen runner into a fresh output and retain the
report, staged image, IPS, and object hashes. Verify the direct corpus and
mutation/fault controls pass; check the exact 68-byte ARM body, 72-byte IPS
extent and no-relocation/even-entry facts. Strengthen the H2 trace and final
record assertions listed above, then compare original and staged
`0x0029FAE8` composition. Separately run a TitleConfig caller composition that
actually obtains the cursor state through setup before `TitleConfig_Calc`; do
not infer that from manual `initialize_cursor` fixture fields. Keep runtime,
input scheduling, and physical controls outside the claim. If the candidate is
promoted, change the `0x00296F18` ledger status from `matching` to the truthful
non-matching classification through the coordinator-owned promotion workflow.

## Static provenance

- Pinned image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Original 72-byte slice SHA-256: `230a091b54d0d9702438bd061a5a53c917b20f8b92dd77e3f87db475480bfe43`
- Candidate source SHA-256: `42b047f03986f8f2362ccc9d64a5d8913db2f9276be8c7c5efaf0c982b6077a0`
- Candidate runner SHA-256: `18a635fb3811cc4dff358ff32efdf840f828d8b953043a415706e3b86b316b4f`
- Persisted shape object hash from its metadata: `c446d43463ce9b70b49d2819f16d233061ac8789f42b4440ea630e1a52a8cb08`
- Candidate ledger row at review: `0x00296f18,72,matching,...` (coordinator-owned).

This review was read-only. It did not compile, invoke the experiment runner,
edit source/runner/ledger/board, or start the emulator.
