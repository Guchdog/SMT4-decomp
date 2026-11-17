# H18 word getter candidates

Implemented four isolated typed getter candidates for `0x003f5a68`, `0x003f5e34`, `0x003f635c`, and `0x003f6800`. Each original is a pinned 12-byte ARM leaf: `ldr r0,[r0,#4]; mov r0,r0; bx lr`. The candidate uses `const std::uint32_t* words` and returns `words[1]`, letting the compiler omit the inert MOV.

## Validation

Test-first red: before the experiment module/candidate existed, `python -m unittest tests.test_h18_word_getters_experiment -v` failed with `ModuleNotFoundError: No module named 'tools.h18_word_getters_experiment'` (expected missing-feature red). After implementation, the focused unittest passed. Two final CLI runs also passed:

- Seed 7: 544 function cases (136 per address: eight directed values plus 128 random cases), all three invalid controls detected, r1 caller-saved scope control accepted.
- Seed 20261024: same coverage and result.

The runner verifies pinned image/ledger identity and original instruction sequences, returns, PC continuation, NZCV, RAM and stack contents, exact `p+4..p+7` read footprint, no writes, and AAPCS callee-saved state. Direct aligned ARM BL/BLX scans found no callers; source search found only prototypes/definitions. Indirect/Thumb/computed references remain possible. Reports include per-address results, source/object hashes and toolchain version.

An early `__builtin_memcpy` implementation compiled into byte loads and ORR instructions, changing caller-saved r1-r3; the first seed-7 experiment therefore failed an overly strict all-GPR check. The first case showed original→candidate deltas `r1: 0xb04342be→0`, `r2: 0xcfcdfe06→0`, `r3: 0x70aabd2e→0`. Per ABI workflow, caller-saved registers are not a preservation requirement absent evidence a caller consumes them. The final typed aligned word access compiles to `040090e51eff2fe1`. The comparator now checks only AAPCS-preserved r4-r11/SP/d8-d15 as ABI state, while NZCV is retained as an extra diagnostic per task acceptance. A separate r1-clobber control confirms the comparator permits caller-saved variation.

Candidate output is 8 bytes versus 12 original bytes; no byte match is claimed. No production source or ledger was changed. Limits: aligned ordinary RAM only; null/misaligned/MMIO/unmapped inputs, actual callers, caller composition, returned-field meaning, concurrency and runtime behavior remain unverified. See the four function records for per-address details.
