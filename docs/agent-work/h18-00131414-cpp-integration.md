# 0x00131414 paired-store production integration

## Result

`ui_func_00131414` is now a readable C++ leaf with the original three-argument ABI: it writes `a` and `b` as 32-bit words at `p+4` and `p+8`, and returns the byte pointer `p+4`. The public header and parser-side `AsdFont_AttachResource` declaration now agree on the `u8*` return and argument pointer. The parser caller continues to ignore the return and returns success after the helper call.

The recovered parser object is `AsdFontParseState` with `u32` fields at offsets `0`, `4`, and `8`; compile-time assertions pin those offsets and the `0x0c` size. No additional record type was introduced for the helper.

The exact original bytes are `040080e2060080e81eff2fe1`. The production object emits `060080e9040080e21eff2fe1`, which is a different 12-byte sequence. The ledger therefore classifies the address as `non_matching`. The ARM/Unicorn reports establish semantic agreement only in the tested domain below.

## Checks

- Focused test: `python -m unittest tests.test_h18_paired_store_integration -v` — exit 0, 2 tests.
- Differential seed 7: `python tools/h18_paired_store_integration.py --output build/agent-work/batch-h18-001/h18-integrate-00131414-paired-store/run-001/seed-7 --seed 7 --samples 256` — exit 0; 260 leaf cases pass, caller window passes, negative control detected. Report SHA-256: `13d66a3f17ddaf4ec3ed674820c14905d3aab6d10fb8a62a5af746567bea5252`.
- Differential seed 20261024: same command with `--seed 20261024` and output directory `.../seed-20261024` — exit 0; same scope passes. Report SHA-256: `0405d9701d48d0d4e6eba0db7d451d4c8733602c34f94e2d95a61ac1afa06a20`.
- Both seeds pin original `code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, extract the function from production `leaf_matching.cpp`, and compare full `r0-r12`, SP/LR/PC/CPSR, full mapped data/stack snapshots, write addresses, and continuation.
- Caller composition starts at `0x00121d14`, executes the original argument setup and BL at `0x00121d1c`, then stops at `0x00121d24` after the success result is set at `0x00121d20`. It passes for both seeds.
- The `second_store_xor_1` negative control is detected.
- Affected production TUs compile with private outputs and one compiler process: `leaf_matching.cpp` exit 0 (object SHA-256 `0328cbfc63a242ab09ca19ce3016a0629486174c3d6a643867161869fc1195f8`) and `leaf_batch34_c.cpp` exit 0 (object SHA-256 `e7aa37b4809dbf8c7881324d134a482b70f7b5391b44712ea6d9844a4df5ee71`).
- `git diff --check -- src/engine/leaf_matching.cpp include/engine/leaf_matching.h src/engine/leaf_batch34_c.cpp config/functions.csv` — exit 0.

## Scope limits and next action

The tested pointers are non-null, four-byte-aligned, and refer to at least 12 writable bytes in ordinary RAM. The tests do not cover MMIO, unaligned or invalid pointers, concurrent observation, exceptions, or partial-fault ordering. Caller composition uses representative prepared state around the real call site; it does not run the parser's earlier validation/chunk traversal or a resource loader. No emulator, loader, booted-game, or whole-game equivalence claim is made. Next: independent review of the frozen production diff and this bounded evidence; then the coordinator may perform batch closure.
