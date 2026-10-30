# H2 `TitleConfig_Calc` production-source integration

## Outcome under independent review

The readable Calc implementation now replaces only `script_vm_func_001ea928` in
`src/engine/leaf_batch46_b.cpp`. The registered callback receives one context
pointer, ignores it, and resolves the work state through the fixed global as the
pinned body does. The semantic callback declaration is `s32` because state 4
returns `-1`; the factory registration remains an address embedded in the
original constructor. Original absolute-address service helpers remain in use.

The production ARMv6K object builds successfully. The extracted symbol is
2,096 bytes, has four local `R_ARM_ABS32` references, and its section-relative
local addends normalize to offsets within the function. The final patch builder
rejects other relocation types/symbols, out-of-body references, occupied cave
bytes, and image/hash/layout drift. Applying the IPS independently reproduces
the patched image.

## Reproduction and identities

- Production source SHA-256: `c76ab50c12589404ca81e35373c8b136c50c91eb63c5af805bf05cc44c6081c7`.
- Clang: `23.1.3`, `armv6k-none-eabihf`, `-mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -ffreestanding -fno-exceptions -fno-rtti -nostdinc -nostdinc++`.
- Focused TU build: `python tools/build_check.py --repo-root . --tu src/engine/leaf_batch46_b.cpp --out-dir build/agent-work/H2-semantic/h2-calc-production-integration/final-obj --jobs 1 --force` — exit 0. The final object SHA-256 is `94197ad141393099a25e679b73457f127c54c7155fa4d8c2ff25270f8ca620fd`.
- The `h2_calc_code_patch.py` build command extracts the exact production symbol `script_vm_func_001ea928`; it reports symbol offset `0x184c4`, size `2096`, and the same four normalized local references. The production source/object/image identities and exact compile command are in each run's `manifest.json` and `report.json`.
- Final patched image SHA-256: `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`.
- Final IPS SHA-256: `0b671f4f40c172984e730d0387899ce47abe8f2ee5e90043a2e481aa591cf781`.
- Original `code.bin` SHA-256 remains `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; it was not modified.

## Differential and caller results

- Production final-address differential seed 7: 68/68 cases passed; report SHA-256 `6ca0d9b0c33a5ce1a08a560920b1888420476bc74c3330ebb00ff616d4857a14` at `build/agent-work/H2-semantic/h2-calc-production-integration/run-001/checks/final-seed-7-20261026/report.json`.
- Production final-address differential seed 20261024: 68/68 passed; report SHA-256 `5c4cc3eff11684d8d167e6dc9b1c7cf45a6811cd5feab21d86a56ba46eebf6d0` at `build/agent-work/H2-semantic/h2-calc-production-integration/run-001/checks/final-seed-20261024-20261026/report.json`.
- Persistent production-symbol run, seeds 7 and 20261024: 16/16 sequences and 54/54 ticks passed; report SHA-256 `b9cb49c8f93bb0c2a72f7c449aa9c3ff47c3efe975f59913cb46ba5d5d946d81` at `build/agent-work/H2-semantic/h2-calc-production-integration/run-001/checks/final-sequences-20261026/report.json`. The wrong `(4,0)` to `(3,0)` logical mapping control was detected as a work difference.
- State-9/10 initializer caller composition with the exact production-derived Calc-patched image loaded: 3/3 cases passed, and the wrong registered Calc callback address was detected; report SHA-256 `144119150c1c6fbfbb57add4a67a017265088599e58d68b7d67143937718e8b8` at `build/agent-work/H2-semantic/h2-calc-production-integration/run-001/checks/final-caller-20261026/report.json`. Calc is registered but not scheduled in this caller runner.
- Focused suite `python -m unittest tests.test_h2_calc_experiment tests.test_h2_calc_code_patch tests.test_h2_calc_sequence_experiment tests.test_h2_offline_caller_composition -v`: 22 tests passed. `py_compile` passed for all three modified runners.
- `python tools/asm_diff.py --addr 0x001ea928`: exit 1 as expected for a byte mismatch. It reports original 1,796 bytes vs compiled 2,096 bytes, 10.91% byte match and 7.39% mnemonic match. Captured output is `build/agent-work/H2-semantic/h2-calc-production-integration/run-001/checks/asm-diff/output.txt` (SHA-256 `D09E0AF3616DE02ACD246C763A0B697D8150ED5D454A2760187D56FF550702DB`); `exit-code.txt` records 1.

## Evidence limits and review gate

This evidence composes the original and production Calc at a final guest VMA under
the same documented helper/HLE outcomes. It does not establish physical input
mapping, renderer/audio/task/script helper internals, a scheduled Calc callback
inside the title scheduler, visible screen behavior, changed-option cancel vs
confirm semantics, file persistence, re-entry, clean restart, Azahar runtime, or
whole-title equivalence. The input-handle contract and the special bounded-helper
range remain unresolved. No emulator, RSP, keyboard, or mouse was used.

The implementation and reports are frozen for independent review. The reference
ledger remains unchanged until that review recommends promotion.

## Independent old-body entry audit

The separate static audit at `docs/agent-work/h2-calc-interior-entry-audit.md`
found no outside ARM B/BL/BLX-immediate target into the overwritten old Calc
body after its first word, and no outside aligned absolute code pointer into
that interior. It scanned the full 10,967-row ARM ledger and all aligned words
in the pinned image. The five aligned hits are Calc's own state dispatch table.
The audit reports odd-offset byte overlaps separately and confirms one
two-byte-aligned overlap is an instruction-boundary artifact. Its conclusion is
limited to static encodings and aligned pointers in the pinned image.
