# H2 callback 0x00221168: bounded conversion contract

Reference: `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; ARM body at 0x00221168, 148-byte ledger span includes literal at 0x002211f8. Read-only inspection with Capstone 5.0.7; no candidate, compiler, Unicorn execution or emulator run in this task. Source identity from dispatch packet: `src/engine/leaf_batch30_c.cpp` SHA-256 `9e73163a03874f5fc514311f23790616abb4789dabfc57c3388bcdd633f176d9`.

## ABI and observable operations

The callback does not consume its incoming r0. It saves r4-r7 and lr and reserves 12 bytes, leaving call-time stack aligned if entry SP is AAPCS-aligned. It returns raw r0 from the final helper. No float argument type is inferred from the zero raw sixth argument.

1. Calls 0x0028df3c with r0=0; its pinned code stores word zero at 0x0043e0bc and leaves r0 unchanged. Calls 0x00289640 with that r0. The latter loads the literal 0x0044de98 at 0x00289650, then reads `[0x0044de98+0x20]` and `[loaded_pointer+0xd0]`.
2. If the first getter result is zero, load pointer `[0x0043e188+8]`; conditionally write 1 to pointer+0x30 when non-null, then unconditionally write 1 to pointer+0x31. A null pointer therefore faults on that path; it is not a safe null case.
3. Regardless of that getter result, load pointer `[0x0043e188+4]` and, if non-null, write byte 0x14 at pointer+0xa11. This happens before calling 0x0028686c and leaves that pointer in r0. The getter ignores r0; its literal at 0x0028687c is 0x0044de98 and it reads `[0x0044de98+0x20]` then `[loaded_pointer+0xc0]`.
4. Call 0x00296f60 with r0=0. Save its returned word. Call 0x00289640 again with r0 still equal to that word; the pinned getter ignores its input. The prior audit incorrectly reports this argument as zero and identifies 0x0043da28 as the getter literal. The previous audit also places the +0xa11 write under the first getter's zero branch; the BNE targets 0x0022119c, before that write, so the write belongs to both paths.
5. Call 0x00286928 with r0=the 0x0028686c result, r1=the 0x00296f60 result, r2=the second 0x00289640 result, r3=6, and stack words 1 and 0. Propagate its raw r0. The original helper has many effects and unknown layouts; leaving it original is an explicit dependency, not proof of its reconstructed semantics.

## Directed offline validation

Use compiled ARM candidate against pinned original with mapped target memory and call hooks that preserve ABI. Compare ordered calls and raw arguments, SP alignment, return, callee-saved registers, all touched memory and faults. Exercise first getter zero/nonzero, +4 pointer null/non-null, +8 valid/null on the zero branch, unrelated initial bytes and sentinels, helper results 0, 1 and other nonzero words. The null +8 zero-branch case should fault on both sides at the unconditional store, with earlier effects compared. Treat safe valid pointer sizes and normal RAM as a bounded domain; do not infer behavior for arbitrary addresses or concurrent mutation.

Negative controls: incorrectly make +0xa11 conditional on getter zero; suppress +0x31 on null; normalize helper return to boolean; swap two getter results; reverse stack words; skip or reorder an effect/call. The call trace must model the actual getter implementations if checking their raw inputs, rather than arbitrarily replacing them with ABI-violating stubs.

Caller composition: use actual handler 0x001a07cc with the callback selected through its nested table. A callback raw result of zero makes handler return 2 without the nonzero path updates. For nonzero, handler subtracts the row word at +4 from task+0x1c, increments task+0x18 only if it still equals the value saved before callback, and returns 1. Cover both unchanged and callback-mutated +0x18, table lookup, memory and ARM/Thumb pointer state. Stub-only composition is partial; run a separate case with original helper where feasible.

## Limits and review

The later run-002 callback trace observes target 0x00221168 and raw zero, but does not directly record the six helper arguments or determine which 0x00286928 branch produced zero. Earlier run-017 did not capture that nested target. No inferred semantic names for object fields or complete helper behavior are supported. Before promotion, independently review disassembly and the compiled candidate, run contract-specific differential and caller tests with negative controls, check interworking, and perform the prescribed original-versus-patched H2 scenario. Preserve the original helper until separately reconstructed and validated.
