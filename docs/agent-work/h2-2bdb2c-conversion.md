# TitleConfig sprite setup conversion — `0x002BDB2C`

## Result

Replaced the 152-byte naked ARM body with typed C++ in the production translation unit. The candidate compiles to 148 bytes and has one `R_ARM_CALL` relocation to the original ARM entry `0x002C4B30` (`AsdMem_Zero`). The runner resolves the branch at the original VMA, pads only the remainder of the function slot with ARM NOPs, creates a one-slot IPS, replays it, and verifies no bytes outside the 152-byte slot changed.

## Differential evidence

The coordinator run `build/agent-work/H2-semantic/h2-titleconfig-sprite-setup-convert-002bdb2c/run001/coordinator-run003/report.json` passed 36 direct cases (four directed and 32 seeded), comparing full node and group bytes, raw `r0`, helper arguments, GPR callee-saved registers, SP, and `d8-d15`. It also executed the actual TitleConfig caller slice `0x002F4D6C..0x002F4D8C` and checked the resulting H2 fields. A mutant that redirects the zero call to `0x002C3344`, which only clears 0x20 bytes, produced a detected mismatch. Independent review repeated the matrix with 48 random cases (52 total), passed the caller slice, and detected the negative control; see [review](h2-002bdb2c-independent-review.md).

The ARM BL target is even and four-byte aligned, and the relocation is in range. The candidate uses `__restrict` for the sprite and group pointers based on the actual TitleConfig topology and the supported non-overlapping domain. Its flag stores are coalesced into halfword stores; the tests compare final memory semantics rather than access width/order. The runner checks `r4-r10`, `d8-d15`, and final SP, but does not explicitly sentinel-check `r11`, condition flags, or SP at the helper-call boundary; the reviewer verified the candidate `r11` save/restore in its prologue/epilogue. The independent review confirmed the ordinary RAM scope and explicitly excludes MMIO and concurrent observers.

## Limits and remaining checks

This is an offline controlled-memory result. The resource table and rendering behavior remain external. Malformed pointers, aliasing, natural runtime reachability, and full H2 lifecycle are not covered. The independent fresh-seed review passed, and the full ARMv6K build passed 204/204 translation units. No emulator was run.
