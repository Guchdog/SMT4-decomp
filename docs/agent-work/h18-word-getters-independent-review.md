# Independent review: H18 word getters

## Decision

No counterexample was found for the declared domain: aligned pointers to readable ordinary RAM containing a live 32-bit word at `p + 4`. The four candidates are plausible isolated semantic equivalents in that domain. Do not promote yet: object layout, caller use, and production source-interface compatibility remain unestablished.

## Original and candidate

The pinned image (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) confirms four 12-byte leaves at `0x003f5a68`, `0x003f5e34`, `0x003f635c`, and `0x003f6800`. Each decodes as `ldr r0,[r0,#4]; mov r0,r0; bx lr` (bytes `040090e50000a0e11eff2fe1`). The candidate is a typed `words[1]` load and return; reviewed report disassembly is 8 bytes, `ldr r0,[r0,#4]; bx lr`. This is semantic evidence, not byte identity.

Two final Unicorn reports, seeds 7 and 20261024, each cover 544 comparisons (136 per address), including directed and random inputs. All four originals/candidates passed; three invalid controls were detected and the caller-saved scope control was accepted. Report hashes: seed 7 `87ae5a3147ccbf4ac2d1475c51a890b7ae8c6bb31de756799d31fc705f3f3912`; seed 20261024 `3b83638936bc1d129e042e527766c420fc7f7356fedcbe8e1ea1d4464f143be7`. Candidate source hash `9a25d735701b7041303e422eb8cc720c58442b21ee7508459752013f5a4fbd62`; object hash `3ead60ce2fc70478b14a271754a7b8f7b24d7cfe0fa5ea3b324c8fd79a03ba8a`.

## Contract and coverage gaps

The production declaration/definition uses `u32 getter(u8* p)`, while the experiment declares `uint32_t getter(const uint32_t* words)`. Both pass one pointer and return one word under the tested ARM ABI, but the C++ types are not interchangeable as-is. The candidate additionally assumes a suitably aligned `uint32_t` object at offset 4; records acknowledge caller layouts and returned-word meanings are unknown. The experiment only establishes behavior for aligned readable ordinary RAM; null, misaligned, MMIO, unmapped, concurrent and invalid pointers are excluded.

The producer description says `r1-r12` are preserved, but the comparator intentionally checks ABI-preserved registers and allows caller-saved `r1-r3` to vary. Its accepted scope control confirms that distinction. The final candidate disassembly only writes `r0` and PC, so it appears to preserve caller-saved registers too, but the final comparator does not dynamically assert that stronger property. Clarify the claim or add a separate check if it matters to a real caller.

No direct immediate ARM BL/BLX callers were found. This does not exclude Thumb, indirect/computed, relocated, or runtime-dispatched references. A read-only scan found pointer-like words in the image at: `0x004206e8 -> 0x003f5a68`, `0x00420764 -> 0x003f5e34`, `0x0042070c -> 0x003f635c`, and `0x00420740 -> 0x003f6800`. These may be tables, but ownership and use are unknown; nearby entries also point elsewhere. A scan of the surrounding rodata window found no direct PC-relative ARM LDR/ADR references. No caller-composition or runtime test was performed.

Current production functions and ledger rows were not changed. Original rows remain classified `matching`; that label cannot be transferred to the shorter 8-byte experimental code. No byte-matching claim is made. The former 720-byte compound span is not validated by these four isolated leaf tests; no evidence supports substituting these functions into or restructuring that span.

## Recommendation

Keep these as isolated candidates. Before production promotion, recover the actual object/caller contract (including the pointer-like table use), align the candidate declaration with the production interface, and validate caller composition. No production build or emulator run was performed in this review.
