# TitleConfig asynchronous table-load wrapper — `0x00297704`

## Result

Replaced the 32-byte naked wrapper in `src/engine/leaf_batch18_b.cpp` with a typed C++ function. It ignores the caller's fourth register word, forwards the name/output/flags, supplies a null owner, raw scale bits zero and size four, and returns the original loader's `r0`. The outgoing call uses base AAPCS to preserve the loader's legacy two-word stack payload. The production body is 24/32 bytes with one ARM call relocation to even entry `0x002AE6C8`; bytes differ, so the ledger is `non_matching`.

## Evidence

The pinned Unicorn runner intercepted the real loader entry for 34 direct wrapper cases and two calls from the exact `TitleConfig` slice `0x002F4DC8..0x002F4DEC`. For each it compared name, output pointer, flags, `r3=0`, stack payload `(0,4)`, aligned helper SP, controlled raw return, preserved GPR/VFP callee-saved state, final SP and output bytes. A mutation from size 4 to size 8 was detected. The slot-only IPS roundtrip and scope are checked by the runner.

The independent fresh-seed run passed 66 direct cases and the exact two-call TitleConfig composition. It confirmed the 24-byte body fits the 32-byte slot, the call targets even ARM entry `0x002AE6C8`, IPS replay stays within the slot, the `non_matching` label is accurate, and the size-4-to-8 control is detected. The full ARMv6K build compiled all 204 translation units successfully.

The `0x002AE6C8` boundary is a controlled return hook. The test validates this wrapper's ABI forwarding and return, not the asynchronous loader's service effects or completion.

## Limits and remaining checks

No emulator was run. Path resolution, queue insertion/completion, output slot contents after loading, failure paths and asset lifetime remain outside this wrapper conversion. This is bounded wrapper evidence, not H2 lifecycle closure.
