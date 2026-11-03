# 0x00128C2C: mode predicate and interior SVC entry

## Recommendation

A bounded C++ conversion of the **first 24 bytes only** (0x00128C2C..0x00128C43) is conceptually possible if integrated patch/link tooling proves it preserves all bytes from 0x00128C44 onward, resolves the helper call and keeps both interior entry targets operational. The 84-byte ledger span contains another real callable stream; replacing or padding the whole span as a single C++ function would break callers. Do not promote until a partial-span integration and independent caller tests exist. Renaming/splitting ledger symbols or reclassifying matching is integrator-owned.

## Pinned 84-byte span

| Address | ARM instruction / role |
| --- | --- |
| 0x00128C2C | `push {r4,lr}` |
| 0x00128C30 | `bl 0x00138F34` |
| 0x00128C34 | `cmp r0,#4` |
| 0x00128C38 | `moveq r0,#1` |
| 0x00128C3C | `movne r0,#0` |
| 0x00128C40 | `pop {r4,pc}` |
| 0x00128C44 | `mov r0,r0` (NOP entry; falls through) |
| 0x00128C48 | `push {r4,lr}` (second entry) |
| 0x00128C4C | `mrc p15,#0,r4,c13,c0,#3` |
| 0x00128C50 | `ldr r1,[pc,#0x20]` -> word at 0x00128C78 |
| 0x00128C54 | `str r1,[r4,#0x80]!` |
| 0x00128C58 | `str r0,[r4,#4]` |
| 0x00128C5C | `ldr r0,[pc,#0x18]` -> word at 0x00128C7C |
| 0x00128C60 | `ldr r0,[r0]` |
| 0x00128C64 | `svc #0x32` |
| 0x00128C68 | `and r1,r0,#0x80000000` |
| 0x00128C6C | `cmp r1,#0` |
| 0x00128C70 | `ldrge r0,[r4,#4]` |
| 0x00128C74 | `pop {r4,pc}` |
| 0x00128C78 / 0x00128C7C | literal words `0x00060040` / `0x00472AD8` |

The `0x00128C50` instruction is **inside** the second stream, after its push and TLS read; it is not its established normal entry. Treat 0x00128C44 and 0x00128C48 as actual branch targets. Literal words are data and must stay at the original PC-relative locations unless the interior stream is deliberately relocated and all branches/literals audited.

## Wrapper contract and H2 caller

The wrapper ignores incoming argument registers as its own logic, saves r4/lr on stack (8 bytes), calls ARM 0x00138F34, compares the full r0 with 4, and returns r0=1 on equality else 0. Original 0x00138F34 loads byte from literal base 0x00473888+3 = 0x0047388B, zero-extends and returns it, with no write; current source `src/engine/leaf_batch21_a.cpp` provides a typed getter. A wrapper conversion may call this existing symbol as a separately validated dependency. It preserves SP/r4-r11 under helper ABI; r0-r3/r12 and CPSR are caller-saved. Wrapper and original helper have no VFP or non-stack writes, though flags/scratch are not a blanket bitwise-preservation guarantee. Mapped stack, code/literal and the byte address are required; there is no pointer argument validation or fallback if unmapped.

Original H2 state reader 0x0011C5EC BL at 0x0011C60C calls **0x00128C2C**, not the interior entry; on nonzero return it exits 0 before its later calibration/reader work. The converted reader record must be assessed using its own actual build and tests; the static callsite establishes the pinned original path only. No physical mode meaning, callback cadence or live H2 behavior follows.

## Interior entry and SVC behavior

Both 0x00128C44 and 0x00128C48 reach the same stream, taking original r0 as a 32-bit request. After stack save, MRC reads the current thread's ARM TLS base into r4. It loads literal command word 0x00060040 and stores it to TLS+0x80 with writeback; then stores the full incoming r0 to TLS+0x84. It loads the literal address 0x00472AD8, reads a 32-bit handle from that address into r0 and executes `SVC #0x32` (the 3DS send-sync-request service number); the command meaning, handle lifetime and remote side effects are not established here. After SVC, r1 becomes `r0 & 0x80000000`; a signed `cmp r1,#0` followed by `ldrge` reads TLS+0x84 into r0 iff the returned r0's high bit is clear. If set, r0 remains the SVC result. Restore r4 and SP and return through saved LR; r1/CPSR change and the kernel/service may mutate TLS response data or other external state. The code does not validate TLS base, handle, mapped command buffer or service response. Do not reduce this to a pure function or infer meaning from the numeric command alone.

The pinned image has direct ARM B at 0x0010FC3C to 0x00128C44 after restoring that caller's frame and setting r0=6; and ARM B at 0x0035B0B8 to 0x00128C48 when incoming unsigned r0<4, with r0=1<<input. No immediate ARM branch to 0x00128C50 was found. These are tail branches, not BL calls; both preserve the caller's LR into the interior entry. A word-aligned whole-image scan found exactly one BL to the wrapper (0x0011C60C), those two B to interior and no aligned absolute pointer to any word in the span. Scanning encoded words can include data false positives and cannot exclude Thumb, computed, indirect or dynamic entry.

## Validation plan and limitations

For the predicate candidate, use the original 0x00138F34 or a separately controlled/verified helper, exercise all 256 possible global byte values (especially 3,4,5,0x80,0xFF), compare r0, stack/SP, r4-r11 and relevant flags/scratch only as required by ABI; confirm no non-stack writes and preserve original null/fault behavior of unreadable byte/stack under explicit mappings. Negative controls must detect incorrect comparison constant, boolean polarity, truncation or extra global access. Compose original 0x0011C5EC with mode 4 and non-4 fixtures, keeping remaining callees controlled or original and tracing early exit/call order. Inspect injected image byte-for-byte to ensure the entire 0x00128C44..0x00128C7F interior and literal pool remain intact; resolve the wrapper BL and verify ARM interworking and no incoming branch to changed middle instructions. Separately static-check original tail callers; testing live SVC/kernel effects requires an exclusive later runtime task, not a stub-only equivalence claim. No compilation, ARM execution, runtime or emulator was performed here.

## Provenance

Pinned image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; wrapper source `src/engine/leaf_batch29_a.cpp` `be020c68977448bbb8f25e7707dbfef2f7970703c848b7154f019cab885bb5a6`; getter source `src/engine/leaf_batch21_a.cpp` `6e0ca93d7dd7bc0739aa84c95b38cb9b13d7f4526eaf33b83142467319f2c564`; reader source `src/engine/leaf_batch30_a.cpp` `4796f75f521f88d31c4277469d1b1239c9f6f0f8a982991984fb82ee22c8d282`. All run002 frozen input hashes match, including `config/functions.csv` SHA-256 `0abdb535550e1f84d3d6d993bd1587a88401648326f45e765404a9dc792c1405`. The original run001 ledger hash became stale and is not used for this handoff. Read-only `python -` Capstone disassembly, aligned branch/pointer scan, source reads and SHA-256 checks exited 0.
