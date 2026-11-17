# H18 nullable getter conversion — 0x0014ec5c

**Owner:** `h18_nullable_impl`
**Result:** Ready for independent review. Production conversion and bounded offline checks completed.

## Change

`engine_func_0014ec5c` retains its C-linkage `void*(void*)` ABI. The replacement returns null for a null input; otherwise it copies the four bytes at `p + 0x1c` into a `u32` with `__builtin_memcpy_inline` and converts that 32-bit target address to `void*`. The width assertion makes the ARM32 assumption explicit and the byte-copy avoids inventing an object type or strict-aliasing access.

The original range is 12 bytes (`000050e31c0090151eff2fe1`); the compiled replacement symbol is 44 bytes. `config/functions.csv` keeps the original 12-byte span and changes its truthful status to `non_matching`.

## Caller evidence

The two direct BL sites are `0x002a62a0` in `engine_func_002a6228` and `0x002aebe0` in `engine_func_002aeb78`. Both callers guard null before invoking the leaf. The first then replaces `r0` with `[r4]`; the second replaces the result source with `r2 = r5`. Their actual leaf return is therefore unused in the observed windows. Caller tests start at the guard and check both null and non-null continuations; they do not execute earlier helper calls or recover object provenance/lifetime.

## Checks and evidence

- `python -m unittest tests.test_h18_nullable_getter_production` — exit 0, 2 tests.
- `python tools/h18_nullable_getter_production.py --output build/agent-work/batch-h18-001/h18-0014ec5c-convert/run-001/seed-7 --seed 7 --samples 256 --caller-randomized 64` — exit 0.
- Same runner with output `.../seed-20261024`, seed `20261024`, samples 256 and caller-randomized 64 — exit 0.
- Each seed checks 261 direct cases (null, zero field, representative nonzero fields and randomized cases), 66 windows per caller, and detects both negative controls. The runner compiles the actual production translation unit and confirms no relocations in the tested symbol.
- For ordinary RAM reads, the runner compares covered bytes rather than access width, since the original word load and alias-safe C++ copy may lower to different read widths. It continues comparing register/flag state, returned value, memory contents, writes, faults and continuation.

## Limits

Only aligned, readable ordinary RAM and 32-bit target pointers are covered. The field's true C++ type and object's lifetime are unknown. The two caller windows do not show the preceding object-producing helpers. Invalid/unreadable pointers, MMIO, concurrent mutation, partial-fault ordering, loader/runtime behavior, and whole-game behavior are not validated. No emulator or full build was run.

**Next:** independent review of production source, the two seeded reports, caller windows, byte-span classification, and the ordinary-RAM read-coverage comparison.
