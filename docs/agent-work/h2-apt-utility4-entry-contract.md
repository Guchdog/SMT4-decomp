# H2: APT utility-4 entry contract

Read-only reconstruction for independent review. No candidate, offline differential, caller test or runtime test was executed by this task. Original: build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/reference/code.bin, base 0x00100000, SHA-256 1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558. All 13 packet-pinned input hashes matched during inspection.

## Entry and ABI

The distinct ARM entry 0x002C0EFC is 44 bytes. It sets r1=0, saves LR, reserves 12 more stack bytes, sets r0=4 and r2=r3=0, stores zero at [sp] and [sp+4], BLs 0x002B5A1C, restores SP and returns through saved LR. Thus the wrapper sees six 32-bit argument words (4, 0, 0, 0, 0, 0), with the fifth and sixth on the stack. Incoming arguments are ignored. Return r0 equals the wrapper's returned 32-bit word, including failure values. At the call, SP is entry SP minus 16 and remains 8-byte aligned if its caller provided that alignment. LR is preserved; the entry itself does not modify r4-r11. It writes two zero words and saved LR in its stack frame; deeper stack and service-visible writes depend on the wrapper. Scratch stack residue is not itself proof of semantic observable equality. ARM/Thumb interworking and unusual caller contexts require separate ABI tests.

0x002C0EE0 is a different externally called entry: it calls 0x002BB7A0 with 0, then 0x002BB774 with 1, restores LR and falls through via NOP into 0x002C0EFC. Replacing only the latter must preserve both entry points and fallthrough.

## Original dependency and effects

0x002B5A1C is 204 bytes and preserves r4-r11/LR. It captures the six ABI words, initializes two local words to zero, calls 0x002BB6B8, and applies fallback pointer/size logic. For this all-zero argument pattern it calls 0x0013B2A4 with r0=4, r1=&local-zero-input, r2=1, r3=&local-zero-output, stack arguments (1, &local-result). Afterward it retains raw r0, invokes 0x002C14F4 if its high bit is set, sets the local result to zero because output pointer/size were absent, skips the optional caller-result store because argument six is null, calls 0x002BB648 and returns the retained word. These calls may have global, service, and error-path effects; their precise full contracts remain dependencies. Fallback buffers are stack-local; no general no-write guarantee follows.

0x0013B2A4 builds the IPC request and executes SVC 0x32. With this call it sends operation word 4 and input/output sizes 1, with the local pointers. It restores two saved thread-local descriptor words after the SVC. If SVC returns a word with its high bit set, it returns that word; otherwise it stores the IPC response word at offset 8 through the result pointer and returns the response word at offset 4. Service behavior and global handles are not established by this static inspection. The wrapper has no indirect call instruction in its body; its direct callees are 0x002BB6B8, 0x0013B2A4, 0x002C14F4 (conditional) and 0x002BB648. Their transitive behavior remains unproven.

A candidate can express this entry as a call to a correctly declared original six-word wrapper with those constants and return its raw word; do not infer a void return or replace the wrapper with a no-op. Pointer typing, symbol linkage, calling convention, actual callable entry and interworking must be established against the integration environment. This representation only addresses this entry, not the full wrapper or service.

## Callers and prior observations

Direct ARM BL instructions to the entry: 0x002C0F6C, 0x002C1260 and 0x002C1304; return addresses are 0x002C0F70, 0x002C1264 and 0x002C1308. Direct ARM B instructions to it: 0x00106F00, 0x0010700C, 0x002A8164 and 0x002C5638; these preserve existing LR. The preceding entry 0x002C0EE0 has direct BLs at 0x00102184 and 0x001051DC.

Prior docs/agent-work/h2-apt-utility4-distinct-entry-probe-runtime.md reports two distinct stepped hits with LR 0x00103E84 and 0x002C1264. Static code has BL at 0x00103E80 to 0x002C5624, then B at 0x002C5638 to this entry. The second LR is compatible with BL 0x002C1260, but LR alone is not a complete dynamic trace. This task did not repeat those probes. An aligned ARM B/BL scan cannot exclude Thumb, BLX, indirect calls, or false positives in code/data.

The existing ledger labels the entry and related functions matching; their source representations in leaf_batch19_b.cpp, leaf_batch45_c.cpp and leaf_batch37_b.cpp are naked byte/word assembly stubs. That is not a claim that readable C++ exists or that the whole runtime is semantically equivalent.

## Validation proposal

1. Compile a candidate against the correct ARM ABI and test call/return interworking, callee-saved registers, SP alignment and restored SP. Freeze input and candidate hashes.
2. Differentially compare original entry and compiled candidate with a controlled wrapper at 0x002B5A1C. Vary incoming registers, stack sentinels and flags; verify six argument words, entry SP alignment, returned arbitrary words including 0, 1, 0x7fffffff, 0x80000000 and 0xffffffff, caller-visible memory and preserved registers. Distinguish ABI-permitted scratch stack residue from live memory.
3. Test original wrapper and any replacement separately with controlled 0x0013B2A4, 0x002BB6B8, 0x002C14F4 and 0x002BB648. Cover success, high-bit failure, buffer contents, local fallback sizes and pointers, callback order, return propagation and acquisition/release, plus result-pointer and nonzero buffer branches if the wrapper is replaced. Actual service/SVC and global effects require additional evidence.
4. Compose each direct BL and B caller, 0x002C0EE0 fallthrough and 0x00103E80 -> 0x002C5624 tail path with relevant controlled dependencies; compare return flow, stack, live state and ordered effects. Caller scan completeness and other indirect or Thumb paths remain open.
5. Negative controls must fail when command 4 changes, one zero argument changes, raw return is discarded, high-bit error callback is skipped, or acquisition/release order differs. Verify they exercise the measured assertion.
6. Only after ARM/Thumb, offline differential and caller-composition gates pass, an integrator may design a pinned original-versus-patched runtime scenario using the private loopback emulator procedure. No prior observation here certifies that comparison.

No blanket equivalence, complete service contract, title-settings coverage or production promotion is implied by this report.
