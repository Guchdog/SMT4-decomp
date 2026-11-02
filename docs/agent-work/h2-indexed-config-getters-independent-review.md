# Independent review: indexed H2 configuration getters

## Recommendation

Approve `0x002F5B2C` and `0x002D65B4` as isolated semantic reconstructions and accept the bounded original-caller composition evidence described here. The new final-VMA run passed all 44 direct cases and two original `0x00286928` caller scenarios. In each caller run, the event trace contains the exact getter argument sequence `(byte,index 0)`, `(halfword,index 0)`, continuing through both getters at indices 1–5; the runner asserts the full ordered pair list and six calls per getter. Four negative controls are detected, the original slots are the only changed bytes, and IPS replay succeeds.

Both exact-byte ledger labels remain `non_matching`. Caller evidence is bounded to the exercised `0x00286928` path and its two explicit zero-return external stubs. It does not establish un-stubbed behavior of those dependencies, the helper's full state machine across other caller states, manager lifecycle, field meaning, or runtime H2 behavior.

## Inputs and fresh independent run

All 20 `input_sha256` entries in the run004 packet were recomputed and matched, including the corrected README, frozen source and runner, pinned base image, and run006 report/image/IPS. The reference code image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The two candidate source hashes are `9461dad078251ffaf77aa85753ce879f1056662b8f690cadcaadaf237d003b99` (`leaf_batch29_b.cpp`) and `cd42f835f48189b1e7700c92bdd2b51ab09dc92b5f59cdc29682c59fdcbd22df` (`leaf_batch32_c.cpp`).

Ran the assigned distinct seeded differential:

```text
python -B tools/h2_indexed_config_getters_experiment.py --out build/agent-work/H2-semantic/h2-indexed-config-getters-review/run004/checks/direct --seed 20261124
exit: 0
```

Fresh report SHA-256: `549ff0d65c4fba8708ff885b03429ca39859879264a1a7b368641224555f0e33`. It records seed 20261124, 44 direct cases and zero mismatches. The `--seed` drives direct fixture generation and mutation fixtures; the two caller compositions use their explicit fixed seeds 20261122 and 20261123. These are two distinct caller fixtures, but they are not randomized from the CLI seed.

## ARM and C++ contract audit

I independently disassembled both pinned ARM entries. Each loads the literal `0x0043DA28`, dereferences its `+4` word at `0x0043DA2C` for the manager pointer, returns zero if null, then compares the input index using an unsigned condition against 6.

- `0x002F5B2C` computes `manager + (index << 2)` and performs `LDRB` at `+0x494`. Its byte result is zero-extended into `r0`. C++ uses an unsigned `uint32_t` index, the same address expression and a volatile `uint8_t` load returned as `uint32_t`.
- `0x002D65B4` computes `manager + (index << 2) + 0x400`, then `LDRH` at `+0x96`, totaling `+0x496`. Its halfword result is zero-extended into `r0`. C++ uses the same address expression and a volatile `uint16_t` load returned as `uint32_t`.

The null and unsigned-bound checks precede indexed access. This prevents large indices from wrapping into memory reads. There are no stores or callees in either getter. The caller declarations use one `uint32_t` input and `uint32_t` result, consistent with the ARM interface. Direct comparisons include raw `r0`, SP, callee-saved registers, full manager/global bytes, write trace, and faults.

The fresh direct run covers null and valid ordinary-memory managers with indices `0..7`, `0x7FFFFFFF`, `0x80000000`, and `0xFFFFFFFF`; all 44 original/staged cases matched. The manager fixture uses distinct sentinels for indices 0–5 and index 6. For non-null valid manager and indices 0–5, the results match the addressed byte/halfword; null or index >=6 returns zero.

## Original-caller compositions

The updated runner executes the original `0x00286928` ARM body twice, once per caller fixture seed, against the original image and the staged image containing both converted getter bodies. It traces actual calls and records getter counts and argument indices. Both compositions report `equal=true`, `valid=true`, six calls to each getter, and `getter_indices=[0,0,1,1,2,2,3,3,4,4,5,5]`. The runner's `valid` predicate checks the full ordered getter address/argument pairs, exactly alternating both getter calls at each index 0 through 5; the report's event counts and argument trace therefore correspond to the asserted caller execution, not just a count inferred from the source loop.

Each composition stubs `0x002C1F28` and `0x0028E974` with a zero return. Those are external dependency substitutions in the measured scenario. No claim is made for their real effects, other `0x00286928` states or external call paths.

## Mutation, slot, classification, and README checks

All four mutation controls are detected:

- Byte getter wrong offset: index 2 changes `0x23` to `0x24`.
- Byte getter wrong upper bound: index 6 changes zero to sentinel `0xE1`.
- Halfword getter wrong offset: index 2 changes `0x6122` to `0x6123`.
- Halfword getter wrong upper bound: index 6 changes zero to sentinel `0xE261`.

The compiled bodies have no relocations and exactly fill their original slots: 44 bytes at `0x002F5B2C` (object SHA-256 `3779ce6e87203addbffc4af1806a55b349ab28b13e37e7a33ca334fbeee9a9d7`) and 52 bytes at `0x002D65B4` (object SHA-256 `5349b4f89ab8376c093ce4c7d90faa8c4af1ea94653557e516fc869ad8e8f271`). Both differ from original bytes, as reported. The staged image SHA-256 is `294db5f615c0c25ed01ceca45f756a08b8b83c805ad5b8d858970db05f74cfdd`; the IPS SHA-256 is `c7a0526b1f83d0933c561699c80ec864b7f21bc8071ae2681a9db4ca6e6326fd`. I independently replayed the IPS and compared the full images: every changed byte is inside the two declared getter slots; there are zero changes outside them.

The two ledger rows are `non_matching`, correctly reflecting the differing bodies. The corrected README percentage is `99.4451%`: `(3,121,204 matching-function bytes + 484 matching-span bytes) / 3,139,108 total bytes = 99.445065...%`, rounded to four decimal places. Ledger totals also reconcile: 10,910 matching functions, 49 non-matching functions, 8 matching spans, and 3,139,108 total bytes.

## Remaining limits

The approved direct domain uses null or a valid mapped ordinary-memory manager. Nonzero invalid/unmapped pointers, aliasing, concurrency and MMIO remain outside the evidence. The caller compositions use fixed fixture seeds and zero-return stubs for two external callees. They demonstrate the actual original caller's six-index loop reaching both converted getters and compare the resulting measured state for those scenarios; they do not validate the complete caller state machine, dependencies without stubs, manager initialization/lifetime, semantics of the byte/halfword fields, or emulator/runtime behavior.
