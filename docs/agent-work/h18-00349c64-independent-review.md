# Independent review: `0x00349c64`

## Verdict

The bounded candidate is supported for the isolated 8-byte entry. The pinned original is `mov r0,#1; bx lr` (`0100a0e31eff2fe1`), and the typed C++ candidate compiles to those same bytes. I found no counterexample in the submitted evidence. Keep this as an experiment-only result: the six-pointer table consumer and callback return-value use are unresolved, so this review does not support caller-level promotion or runtime claims.

## Entry and compound-span boundary

The ledger row at `0x00349c64` is 720 bytes, but the first 8 bytes form a complete return-constant entry. Immediately afterward, `0x00349c6c` is `mov r0,r0`; `0x00349c70` begins an apparent separate stack-framed body (`push {r4-r8,sb,sl,fp,lr}; sub sp,sp,#0x74`), though its entry boundary is not established by this review. The 720-byte catalog span ends at `0x00349f34`, where the next catalog row `ui_func_00349f34` begins. The production wrapper still contains the compound raw-byte span. The candidate and reports explicitly limit their claim to `0x00349c64..0x00349c6b`; neither validates the `.6c` entry, the `.70` body, nor all 720 bytes.

Thus the exact-byte match is properly scoped: candidate bytes equal the first 8 original bytes, not the complete 720-byte ledger row. The higher-level meaning of the returned one is unknown (boolean, enum, or status value).

## Differential runner and reports

Reviewed `tools/h18_00349c64_experiment.py`, its test, and both submitted reports. The runner pins the image SHA-256, checks the exact entry bytes and ledger span, compiles a relocation-free ARM leaf, and executes original and replacement in separate Unicorn runners. It checks expected r0=1, r1-r12, SP, LR, NZCV, return PC, data memory, live stack, and read/write footprint. The shared runner also checks callee-saved registers/SP and d8-d15 against entry state. This covers the observable state relevant to these two instructions; the harness models ARM11 and ordinary mapped RAM/stack only.

The three negative controls target distinct failures: a wrong return value, changed NZCV, and a data-memory write. Both submitted seeds pass all 128 cases, and every control is detected:

| Seed | Report SHA-256 | Result | Candidate bytes | Object SHA-256 |
|---|---|---|---|---|
| 7 | `941f1a1bb487fea6b17d1cbeaa65c941954b79f4e3999189aa71664f66dd547d` | 128/128; controls detected | `0100a0e31eff2fe1` | `fda4812491e81819cbeb5c130bb8efa60820feb3e0f9f8eaac2bcd00175a7948` |
| 20261024 | `fe14f910b1beb620f1cd87bb09c28f200ef3ef08008dfbcf769e6adb55c42a56` | 128/128; controls detected | `0100a0e31eff2fe1` | `fda4812491e81819cbeb5c130bb8efa60820feb3e0f9f8eaac2bcd00175a7948` |

The focused test also checks the entry bytes, six pointer locations, compound-span metadata, randomized inputs, and all three controls. These remain bounded tests rather than proof over every machine context. The contract checker compares NZCV, not the entire CPSR control state; neither instruction writes CPSR control bits. The runner does not model MMIO, concurrency, callers, or a game session.

## Pointer-table and caller limits

The report's aligned pointer scan found six consecutive `0x00349c64` values at `0x0047299c..0x004729b0`. Independent inspection shows the surrounding data words are `0x00349bb8`, `0x00349b24`, `0x00349a90`, then those six copies, then `0xffffffff`. This is consistent with a callback or method table, but it does not identify the owner, element semantics, or dispatch site. The runner found no immediate direct BL/BLX caller and no recognized PC-relative load/ADR resolving to that table. Its exact pointer scan is limited to aligned little-endian values; the instruction scan examines aligned words in ARM text and may interpret data as instructions. Register-indirect calls, computed references, unaligned/relocated references, Thumb callers, and runtime dispatch remain unresolved.

**Integration blocker:** resolve the table owner/consumer and establish whether the callback result is used before making caller-level or runtime claims. The current candidate can be reviewed as an isolated entry implementation, but not as a proven callback replacement in that table.

## Reviewed identities and checks

- Pinned image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Candidate source SHA-256: `c6845f2d580c1377864a3c02a9071d4a29750c0d0629259e795416f3eaa03cfe`.
- Runner SHA-256: `42b893507c6f771047bfabb1d479903d44dd5612b4750ec3aca5bd16ece18508`.
- Test SHA-256: `77f82961a252bd42d026769485c51e8a7f0cc61a31bc94d6d96ab8079d634041`.
- Source function-record and candidate-note hashes are frozen by the run-002 packet; production source and `config/functions.csv` were not changed by this review.
- No compilation, new differential run, caller composition, or emulator session was performed. The two recorded run-001 reports were hash-checked and their JSON outcomes inspected.

## Recommendation

Accept the narrow 8-byte candidate as an independently reviewed experimental reconstruction. Keep caller evidence partial and production promotion pending until the six-pointer table is mapped and a representative callback invocation and return-value consumer are confirmed. Do not claim equivalence of the 720-byte span or runtime behavior.
