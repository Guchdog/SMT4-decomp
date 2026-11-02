# H2 indexed configuration getters: production conversion

## Scope

Converted the two original direct callees that `0x00286928` invokes in its six-entry loop:

- `0x002F5B2C` reads an unsigned byte from manager `+ index*4 + 0x494`.
- `0x002D65B4` reads an unsigned halfword from manager `+ index*4 + 0x496`.

Both load the manager pointer from `0x0043DA2C`, return zero for a null pointer or unsigned index `>= 6`, and otherwise perform one volatile field load. Neither writes memory or calls another function. Nonzero invalid pointers remain outside the supported domain. The source preserves the raw word input and zero-extended return contract; field meanings are not inferred.

## Production changes

Replaced inline ARM assembly with typed C++ at each original entry. `func_002f5b2c` remains in `src/engine/leaf_batch29_b.cpp`; `func_002d65b4` remains in `src/engine/leaf_batch32_c.cpp`. Their signatures agree with the typed declarations already used by `0x00286928`.

Both compiled bodies have no relocations and occupy their original slots exactly: 44/44 bytes and 52/52 bytes. Both bodies differ from the pinned ARM bytes, so the ledger classifications are `non_matching`.

## Offline evidence

Runner: `tools/h2_indexed_config_getters_experiment.py`.

The final-VMA comparison used 44 direct cases: each function, null and valid manager pointers, and indices `0..7`, `0x7FFFFFFF`, `0x80000000`, and `0xFFFFFFFF`. It compared raw `r0`, SP, callee-saved registers, complete manager/global bytes, write traces and faults. All cases matched. It also executed the original `0x00286928` body in two caller compositions; each made six calls to each getter for indices 0 through 5, with original guard/main service callees stubbed to their recorded zero path. Both original-versus-staged caller runs matched complete observed state and write traces. Four mutation controls detected a wrong field offset and a wrong upper bound for each function. The two-slot IPS replay passed; bytes outside those two declared slots were unchanged.

Run output: `build/agent-work/H2-semantic/h2-indexed-config-getters/run006/checks/direct/report.json`.

## Limits

The loop's six indices are established statically in the original `0x00286928` body. This evidence validates the isolated getter calls and their index range, but does not execute or validate that larger helper's full state machine. Manager lifecycle, the meanings of the fields, wider pointer validity, and runtime H2 behavior remain open. See the independent [review report](h2-indexed-config-getters-independent-review.md) when complete.
