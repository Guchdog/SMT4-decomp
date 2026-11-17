# Independent review: 0x00121d70 signed-byte getter

## Recommendation

**Hold promotion to a fixed-address replacement pending a placement/patching decision.** The source-level operation and bounded differential evidence are credible for ordinary readable RAM, and the ledger correctly says `non_matching`. The compiled candidate is 28 bytes while the original slot is 12 bytes. The reported runner injects candidate code elsewhere and branches to it; it does not establish that this larger body can be installed without overwriting the following function at `0x00121d7c` or changing the patch layout. If production integration uses separately linked/replaced code with a verified trampoline or relocation scheme, that scheme still needs evidence before promotion.

## Source and contract

The original 12 bytes `030c80e2d003d0e11eff2fe1` decode to `add r0,r0,#0x300; ldrsb r0,[r0,#0x30]; bx lr`: return the signed 8-bit value at `p+0x330`, with no stores. Production keeps C linkage and `s32(const u8*)`, reads through `const unsigned char*` (valid aliasing access to object representation), and explicitly maps bytes `0..127` to nonnegative values and `128..255` to `-128..-1`. This is semantically consistent on the tested ordinary RAM domain and avoids alignment requirements. The `p+0x330` storage extent/lifetime must be valid; actual runtime pointee provenance remains unknown.

The reported object is 28 bytes (`331ea0e3ff20e0e3d11090e1000051e37100efe6020080411eff2fe1`), not byte-identical. Ledger row remains 12 bytes and `non_matching`, which is truthful. Its length makes the inline slot question material: next original symbol starts at `0x00121d7c`.

## Differential evidence and caller

I inspected both frozen reports and their recorded hashes. Seeds 7 and 20261024 each report 512 direct cases (all byte values plus 256 random values), 512 caller cases, and two detected controls (unsigned return at `0x80`, wrong offset `+0x331`). The comparison observes `r0`, callee-saved `r4-r11`, SP/LR/PC, D8-D15, memory, access footprint, completion, and mode; isolated caller-saved registers and unconsumed flags are appropriately excluded. In caller mode it includes CPSR after the caller's real compare/branch. Both report branches to `0x00110f50` and `0x00111008`.

The fixture begins at `0x00110f3c`, executes the literal load and `ldr r0,[r5]`, seeds global word `0x00433158` with a synthetic aligned RAM object, calls at `0x00110f44`, and tests both continuations. The static aligned ARM scan finds this direct BL; it finds no aligned pointer words. The fixture does not execute the producer of that global or establish the real target object's type, lifetime, or extent. Its caller evidence therefore supports this call path only under the seeded fixture.

## Limits and next contract question

No emulator/loader/game runtime check was performed; invalid or null pointers, unreadable spans, MMIO, concurrency, fault ordering, and non-static/indirect/Thumb/runtime-generated references are not covered. The report/test assertions were inspected but not rerun in this review.

**Question for integration:** is this address patched in place within its 12-byte extent, or does the production build/linker provide a verified larger replacement/trampoline path? Until answered with placement evidence, retain the source semantic finding and non-matching label, but do not promote the 28-byte body as a safe fixed-address replacement.
