# Independent review: 0x002b89a0 manager predicate

## Scope and identities

Reviewed source `src/engine/leaf_batch26_b.cpp` SHA-256 `353fe67f82d0ee07832dd0fe5bfb151e11103f344086ec68d2fda80dee1b8222`, candidate `af44d869ad09a5bfc099434b47e5140f35a943be51c361578e93bde6e9c3b66d`, runner `b85e9bcd08ac648439a3d072d465a77e547a8fce22313b26c64c67c36ab419a2`, production and experimental objects and recorded output. Reference code.bin SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. No compilation, offline runner or emulator was executed during this review.

## Contract and production object

The original reads the pointer at 0x0044dc20. A null pointer returns 1 without dereferencing it; otherwise the original reads the word at manager+0x352c and returns 1 only for value 0x14, else 0. The body has no explicit writes. Source expresses these cases with fixed 32-bit pointers and a uint32_t load. Supported domain is a readable normal global pointer and, for non-null manager, an object permitting the aligned word read; no invalid-address fault, concurrent mutation, or MMIO equivalence is established.

Experimental and production symbol bodies are identical 52-byte ARM code, with no symbol relocations; both differ from the original. Candidate object SHA-256 `08901fada8fe04d4c849869a3c9dc691d77cce99dd618168372c8004d4bd7f77`, production object `6c8e340b727286717ca679606320adf020b508e9e2dcd4448e9f1216a82cb541`; the ledger's `non_matching` classification is appropriate. Candidate computes the final boolean with SUB/CLZ/LSR, and may leave caller-clobbered CPSR/r1 different from the original comparison sequence. AAPCS treats these as clobbered, but raw assembly callers must be assessed rather than assumed.

The original helper 0x00286928 uses direct ARM BLs to this address at 0x002869f8 and 0x00286a90, each followed by `cmp r0,#0`. A conservative scan of all aligned words in the pinned image found 13 possible ARM BL locations targeting 0x002b89a0: 0x001152a4, 0x001808b8, 0x00185ed4, 0x00186090, 0x001dbbb0, 0x001dfda8, 0x001e4ae8, 0x00213d74, 0x0028583c, 0x002869f8, 0x00286a90, 0x0033eba0 and 0x00382810. All decode to BL followed immediately by `cmp r0,#0`, so they do not directly consume callee flags. This is a byte scan, not proof of instruction boundaries or a complete Thumb/indirect call inventory. `src/battle/battle_extras.cpp` declares and calls a different C++ symbol `Camp_IsMenuActive` annotated with this address; its linkage to `camp_func_002b89a0` is not established by this review.

## Evidence and limits

Recorded `build/h2-b89a0/offline-closure.txt` SHA-256 `3bdf12fe2676b5f4b53fbf3b16946fd70f3d6d162073c5d8b36ac5720db559be` reports 139/139 direct comparisons, no direct guest writes, 32/32 original-helper continuations, and three detected mutants. The direct fixture covers the null manager and valid aligned non-null pointers with modes 0, 0x13, 0x14, 0x15, 0xffffffff and 128 seeded choices from those values; it compares r0, SP, r4-r11, selected memory and observed write events. It does not cover arbitrary mode values beyond that set, null-pointer faults in later callers, CPSR, unaligned or inaccessible memory, aliases, timing or all caller-saved registers. Null mutant may be detected by an emulator fault, which the runner treats as a difference.

The caller fixture uses original 0x00286928 with selector 6, nonzero third argument and state 1. It initializes 0x002c1f28 to return nonzero, sets the manager null so this predicate returns 1, and chooses object byte +9 = 19 so original 0x002b8d24 exits before its jump table. It compares returns, SP, callee-saved registers, selected memory and ordered observed guest writes. This is a bounded continuation with a nonzero upstream predicate and a true result here; it does not cover the non-null manager path in that caller, 0x002b8d24 jump-table effects, all helper states or runtime H2. The caller hook does not explicitly assert the call was hit; the entry/branch setup is consistent with the pinned static control flow. Output is recorded evidence, not independently repeated here.

## Assessment

No static counterexample was found within the documented ordinary-memory domain. Cumulative image packaging, address binding/interworking, offline composition with other replacements and original-versus-patched runtime are separate integration work. Preserve exact ledger status and do not infer complete H2, other callers or whole-game equivalence from this review.

## Callee-entry assertion, packet 004

The current runner SHA-256 is `7601740c7601fa52608aa094a289554c07f89275ff2322bfc24aec76f61a3f43`. The caller-composition hook now counts entries at 0x002b89a0 and raises unless exactly one occurs in each original, candidate and production execution. This supersedes the earlier observation that callee entry was not explicitly asserted. The revised preserved output SHA-256 `f50a88f93aff95c4f0dfe4bf0144fa8800259e8aba74c8c8d6ab08b7234d1c0b` reports 139 direct cases, 32 caller seeds with that assertion and three detected controls. The reviewer did not rerun the script; output provenance remains recorded rather than independently reproduced. Other fixture and runtime limits are unchanged.
