# `0x002B8B78` production conversion evidence

**Result:** bounded typed C++ reconstruction passed independent review.
The ledger label is `non_matching`; the function is not claimed to be an audio
playback wrapper. Its manager/profile state and six-slot transition behavior
are described in [the function contract](h2-sound-playse-contract-002b8b78.md)
and [function record](../function-records/0x002b8b78.md).

## Implementation

- Replaced the inline ARM body in `src/engine/leaf_batch32_c.cpp` with the full
  typed flow and raw `u32` return.
- Updated cross-translation-unit declarations to the typed signature in
  `leaf_batch19_b.cpp`, `leaf_batch20_c.cpp`, `leaf_batch21_c.cpp`,
  `leaf_batch22_c.cpp`, `leaf_batch29_c.cpp`, `leaf_batch32_b.cpp`,
  `leaf_batch45_a.cpp`, and `asd_runtime.cpp`.
- Retained the original direct dependencies. The compiled body is 332 bytes;
  its six branch instructions resolve to five unique ARM targets, all with bit
  0 clear, and the local priority-data
  relocation is bound to pinned original table `0x00402550`, whose first six
  bytes match `05 06 04 03 02 01`.
- One 340-byte slot is staged. IPS replay passed and no byte outside that slot
  changed.

## Validation

Commands and exit codes:

| Command | Exit | Result |
| --- | ---: | --- |
| `python tools/h2_sound_playse_experiment.py --out build/agent-work/H2-semantic/h2-sound-playse-convert-002b8b78/run002/checks/direct` | 0 | 23/23 direct cases, 2/2 real caller slices, 4/4 mutation controls, IPS replay, slot scope |
| Focused `compile_tu_armv6k` loop for the nine affected translation units | 0 | 9/9 ARMv6K object builds passed |
| Static Capstone ARM/interworking inspection of five unique branch targets and both caller BLs | 0 | All targets are even ARM entries; both caller BLs target `0x002B8B78` |
| `python tools/agent_workflow.py check` | 0 | Ownership/provenance checks passed |

The direct matrix covers same-profile return, signed negative/nonnegative
latch, first/middle/last/no scan hit, full-width requests including `0x100` and
`0xFFFFFFFF`, null lookup outcomes, old/new profile gates, zero/nonzero and
`0x0100` halfwords, six ordered slot calls, final-object reload, and all three
final service paths. Detected controls cover byte-truncated equality, signed
latch polarity, request-store truncation, and the default slot arguments.

The two caller tests execute the original `MOV r0,#0x99; BL` sequence at
`0x002F4DEC` and the original `MOV r0,#0xDC; BL` sequence at `0x00286B7C`,
then stop at the instruction immediately after the call. They establish these
call-slice compositions under fixed valid memory fixtures; the nested callback
path is static/conditional evidence, not runtime reachability.

## Limits and review

The five dependencies are controlled stubs, so their transitive memory and
audio effects remain outside this result. Invalid/null object pointers, profile
table bounds/lifecycle, arbitrary aliasing, concurrency, physical sound and
runtime execution are not established. No emulator was launched. The independent
review accepted the bounded reconstruction and found no behavior counterexample;
it requested a branch-count clarification that has been applied above and in
README and the H2 milestone record.

Raw focused output is in
`build/agent-work/H2-semantic/h2-sound-playse-convert-002b8b78/run002/checks/direct/`.

The independent fresh review approved the bounded wrapper. It corrected the
branch count here and in README: six branch instructions resolve to five unique
ARM targets. See
[`h2-sound-playse-independent-review-002b8b78.md`](h2-sound-playse-independent-review-002b8b78.md)
and its structured handoff under `build/agent-work/H2-semantic/`.
