# 0x00121d70 production integration

Replaced the inline assembly in `func_00121d70` with readable C++ that accesses the object representation through `const unsigned char*` at offset `0x330`, then explicitly converts the byte to the matching signed `s32` value. C linkage and the existing `s32(const u8*)` declaration are unchanged. The exact ledger span is `non_matching` because the emitted 28-byte production body differs from the original 12 bytes.

## Evidence

- Focused tests: `python -m unittest tests.test_h18_signed_byte_production -v` — exit 0, 2 tests.
- Seed 7: `python tools/h18_signed_byte_production.py --output build/agent-work/batch-h18-001/h18-integrate-00121d70/run-001/seed-7 --seed 7 --samples 256 --caller-samples 256` — exit 0; 512 direct inputs and 512 caller inputs passed; all byte values and both continuations covered.
- Seed 20261024: same runner and sample counts in `.../seed-20261024` — exit 0.
- Both reports pin original `code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, compile `src/engine/leaf_matching.cpp`, extract `func_00121d70` and compare against original ARM execution. Direct evidence compares result, callee-saved GPRs, SP/LR/PC, D8-D15, memory, access footprint and completion; caller composition also checks the consumed final flags and continuation.
- Caller composition begins at `0x00110f3c`, executes the real PC-relative literal load yielding global address `0x00433158`, loads the seeded pointer at `0x00110f40`, calls at `0x00110f44`, and exercises zero (`0x00111008`) and nonzero (`0x00110f50`) continuations. The pointer's runtime producer is not executed.
- Two negative controls per seed are detected: unsigned byte return at `0x80`, and a load from `+0x331`.
- `git diff --check` over the owned production, ledger, record, runner and test files — exit 0.

## Limits and next action

The caller fixture seeds the shared global pointer with a synthetic aligned RAM object. It proves the real load/call/branch composition for this fixture, not the runtime pointee's type, lifetime, extent, or initialization producer. The source requires readable object representation through `p+0x330`. MMIO, null/invalid pointers, inaccessible ranges, concurrency, exceptions/fault order, loader runtime and game runtime remain untested. No emulator was used. Next: independent review of the frozen source and both reports; retain `non_matching` unless exact bytes are separately restored.
