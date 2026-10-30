# Independent review: `TitleConfig_IsReady` direct-call production body

## Decision

The refreshed production source and object are suitable inputs for a narrowly scoped shared-patcher extension. The 48-byte body fits the original 52-byte slot, and its only relocation is the expected ARM-state `R_ARM_CALL` to the original task-registration helper. The task-local resolver checks the expected unresolved instruction, target alignment/range, applies the relocation at the original function VMA, decodes the branch back to the exact target, and differentially runs that resolved body at `0x002FC0EC`.

Treat this as a bounded callback result, not as a merged H2 replacement. The helper remains mocked; no state-10 caller composition or runtime evidence exists. The harness checks SP restoration and every callee-saved GPR/VFP register, but does not compare caller-owned stack bytes. The current four cases and always-ready negative control support the predicate contract, though the stack-memory dimension should be stated accurately and added before broader caller evidence.

## Source and object identity

Every declared run-002 input hash matched. Verified identities:

- Source `src/engine/leaf_batch26_b.cpp`: SHA-256 `609aaf963db8129a560293c8d1e65b3c6df8fa016673d28b0143535dadb4e4ee`.
- Production object `.../run-001/checks/production-tu/engine/leaf_batch26_b.o`: SHA-256 `2c0ca7a51729389cce55cf31476f9a3075b50b3b4ef3cabebba9cffe0382b37d`.
- Extracted `ui_func_002fc0ec`: 48 bytes, body SHA-256 `d43275ec3a230ed2b038098437f7baa314794b09aadcbd697a35c3f5f8136332`.
- Resolved body SHA-256: `f61aba9c1b7a9763c66bd4f00900b59e7a51928925370a7cc587eca0fb943a44`.
- Production differential JSON SHA-256: `eea2f9a6c73d3c9ef8b39fcaebd3dba5f20dae3fb0e0633c596a01b17cdb9835`.
- Pinned reference image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The exact function is 48 of the original 52 bytes. The remaining four-byte tail at `0x002FC11C` is the old global-address literal `0x0044E2D0`, referenced by the original wrapper at offset zero. The new production source uses the global address in its own 48-byte body. The eventual in-place patch should write exactly the 48-byte replacement and leave the trailing four bytes unchanged unless a separately audited patch record intentionally owns them. The ledger/function record now correctly marks the changed source `non_matching`.

## Relocation review at the original VMA

The extracted symbol contains exactly one relocation:

- Offset: `28` (`0x1C`)
- Type: `R_ARM_CALL` (type 28)
- Symbol: `battle_func_002bf41c`
- Explicit addend: none
- Unresolved instruction word: `0xEBFFFFFE`

At final VMA `0x002FC0EC`, the branch site is `P=0x002FC108` and target `S=0x002BF41C`. ARM PC-relative branch calculation gives `S-(P+8) = -249,076 = -0x3CCF4`, aligned and within ARM `B/BL` range. The encoded instruction `0xEBFF0CC3` decodes from `P+8` to exactly `0x002BF41C`. The task-local resolver validates the opcode/addend form, relocation count/type/offset/symbol, range, alignment, and decoded target. I independently repeated the extraction and arithmetic; no other relocation is present.

For shared patcher support, whitelist this exact expected relocation shape (and fail closed for any changed offset, symbol, opcode, addend, or additional relocation). Since the function stays at its original VMA, no entry branch or cave allocation is needed. Apply the 48-byte body at the original file offset and preserve the four-byte tail. The one-off resolver's success does not mean the shared patcher already supports it.

## Differential and ABI evidence

The task-local final-VMA runner uses the exact extracted production symbol after resolving the call and executes it at `0x002FC0EC` against the pinned original. It intercepted `battle_func_002bf41c` identically in both executions as a configurable task-registration predicate. The four passed cases were: null global, registered task, unregistered task, and null task handle forwarded. The always-ready control was detected on the registered-task case because it returned 1 instead of 0. There was no first counterexample.

The comparator checks fault/return-to-sentinel, return `r0`, return PC, helper address/argument trace, SP, `r4-r11`, and `d8-d15`. The report records all four cases and each preserved-register result. It does not snapshot or compare caller-owned stack bytes; “stack check” here means SP restoration only. The source body is simple and the final-VMA differential checks the full callee-saved register set, but do not claim stack-memory preservation from this report.

The source matches the recovered contract: if the global work pointer is null it returns ready (`r0=1`) without a helper call; otherwise it forwards `work->calc_task` (including null) to the helper and returns the inverse of the helper's zero/nonzero registration result. The helper's task-list implementation is not executed in these comparisons. The state-10 caller's wait/reset behavior is static source evidence only.

## Remaining limits and next action

This result supports adding exact `R_ARM_CALL` handling for the 48-byte in-place body to the shared patcher, provided the patcher enforces the relocation checks above and preserves the old tail. Before treating the function as integrated, apply one reproducible patch to the pinned image, independently apply its serialized IPS, and verify the resulting image hash and bytes outside the authorized 48-byte record. Add caller-stack byte snapshots to the differential or accurately keep the current SP-only claim. Then compose State 10 with the production ready-gate and task helper behavior under explicit HLE boundaries.

No build, source/patcher/ledger change, emulator, RSP, profile, or input control was performed for this review. The helper's list internals, scheduler lifecycle, actual title caller composition, runtime UI, persistence, and restart behavior remain untested.
