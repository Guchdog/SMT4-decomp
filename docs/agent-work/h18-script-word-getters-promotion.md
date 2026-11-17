# H18 script low-byte getter promotion handoff

## Changes

Promoted `script_vm_func_002345f0` and `script_vm_func_002345fc` in `src/engine/leaf_matching.cpp` to alias-safe byte reads (`return p[0x48]` and `return p[0x4a]`) under their existing `const u8* -> u32` interfaces. Removed inline assembly. Their original image leaves are still 12-byte references; rebuilt symbols are 8 bytes and differ, so both ledger rows are now `non_matching` while retaining original address and size. Function records describe the semantic contract and limits.

Before editing, a pinned-image scan found 16 aligned ARM BL sites into each exact entry, no branch into either leaf interior, and no aligned pointer-word references to either function window. The four direct caller functions are `0x0038c43c`, `0x0038cdf4`, `0x0038d7b0`, and `0x0038de60`.

## Production-source evidence

`tools/h18_script_word_getters_production.py` compiles the affected production translation unit, extracts the two exact production symbols, and runs pinned-original Unicorn differential checks. Seeds 7 and 20261024 each pass 80 cases per getter (16 directed halfword boundaries and 64 seeded inputs), with return/full-register/NZCV/continuation/data/write comparisons and wrong-offset/omitted-mask controls. Both compiled functions are 8 bytes: `ldrb r0,[r0,#offset]; bx lr`.

One paired caller window per each of the four caller functions passes for each seed. Each window includes both getter calls and the instructions consuming the returned values. The read sets are recorded and differ: original LDRH reads two bytes; the C++ byte read touches one. The comparator intentionally ignores only that read-width distinction under the side-effect-free ordinary-RAM contract, while retaining state and write checks.

This does not claim equivalence for MMIO, read-width-sensitive memory, unaligned or invalid pointers, page-boundary faults, races, every direct callsite, complete caller behavior, or game runtime. The source and ledger are frozen for independent review; no production build integration beyond compiling `leaf_matching.cpp`, no full project build, and no emulator run were performed.

Reports:
- `build/agent-work/batch-h18-001/h18-integrate-002345f0-fields/run-001/checks/seed-7/report.json` (SHA256 `0d6abeff2abdea09bad5aeb1df2dcb37aa2cf46c65d82160f56d7a0b996a26a5`)
- `build/agent-work/batch-h18-001/h18-integrate-002345f0-fields/run-001/checks/seed-20261024/report.json` (SHA256 `f3b351a16beabf22a0fc8bffb80aae2823e6a0063083998578ffd5c891ff8525`)

Pinned image SHA256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
