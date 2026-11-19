# Independent review: 0x003f32f4 initializer family

The eight separately callable ARM entries occupy consecutive 0x2c-byte blocks, including their literal pools. Inspection of the pinned disassembly confirms that the first pairs of 0x003f3320 and 0x003f3428 are addressed at literal base + 8, unlike the other six. The candidate keeps their global destinations distinct. A coordinator rerun with seed 739 passed all eight entries, 20 cases each, and detected all eight mutants. The worker's handoff and reports describe the other seeds and ABI checks.

Evidence covers isolated initialized RAM, control flow and the runner's preserved-state checks; it does not establish startup registration, real callers, fault or concurrency behavior, integrated placement or runtime. These entries remain experiments within a larger compound ledger span, not an in-place replacement or whole-game claim.
