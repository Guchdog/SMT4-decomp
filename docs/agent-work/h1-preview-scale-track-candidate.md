# H1 preview scale-track candidate handoff

The experimental reconstruction at
`experiments/semantic_equivalence/h1_preview_scale_track_candidate.cpp`
models the self-contained pinned helper `0x002B1FC0`. The function extent is
444 bytes and has returns at `0x002B2024`, `0x002B2114`, `0x002B2120`, and
`0x002B2178`. It is distinct from the neighboring scale/track helpers at
`0x002B1DFC` and `0x002B1C8C`.

The source models the early `+0x87` gate, null track pointer, signed row index
and progress, 12-byte row layout, full-width `12*index` wrap, endpoint mode and
direction, sequence feature/entry sentinels (`-1`, `-2`, `-3`), halfword counter
updates, and the VFP sequence `subtract → unsigned duration conversion → divide
→ add current scale`. There are no external stubs because the target body has
no callees. The preview helper's static caller at `0x002BFC30` passes object
pointer `r4` in `r0`.

The final private ARM11 MPCore run is
`build/agent-work/H1-semantic/h1-preview-scale-track-candidate/overnight-20261025-scale-track/run-04/report.json`.
It records 22/22 original-versus-candidate cases and detects a mutant omitting
the selected-sequence `+0x8A` clear. The cases include null track/gate,
endpoint/interpolation direction branches, duration/progress boundaries and
halfword wrap, zero-duration VFP divide-by-zero status, signed sequence
sentinels/restart, ordinary sequence transition, negative row index with valid
preceding storage, and extreme finite float values. Focused tests assert the
report coverage and key sentinel/FPSCR outcomes.

Evidence remains partial: fixtures use synthetic valid memory and finite
cases; they do not identify a live H1 track object or verify the caller's real
scene. Unchecked pointer/index domains, aliases, concurrent mutation, MMIO,
and runtime behavior remain open. The ledger `matching` label is preserved;
no production source, sibling helper, shared runner, board, or emulator was
modified. Exact hashes and commands/exits are in the structured handoff and
report beside the packet run.
