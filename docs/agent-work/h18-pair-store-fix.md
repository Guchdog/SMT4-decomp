# H18 paired-store alias correction

The production body for `0x00131414` no longer computes `fields[1]` by incrementing a `u32*` that points at the `AsdFontParseState::data` scalar. It independently forms the two typed addresses at byte offsets `p+4` and `p+8`, stores `a` and `b`, and returns `p+4`. The ledger remains `non_matching` because the production bytes differ from the original.

The source-contract checker now requires both exact independent typed-address stores, rejects array indexing in the body, and still checks the pointer return and parser declaration/layout contract. This updates the validation contract without suppressing ARM, register, flags, memory, write-footprint, continuation, or negative-control comparisons.

`tests.test_h18_paired_store_integration` passes (2 tests). Fresh production-source differential runs for seeds `7` and `20261024` each pass 260 leaf cases, a real parser call-site window from `0x00121d14` through `0x00121d24`, and detection of the `second_store_xor_1` negative control. Both compile the exact production TU and extract `ui_func_00131414`; the compiled symbol remains 12 bytes `060080e9040080e21eff2fe1`.

The C++ object-model contract depends on `p` pointing to a live `AsdFontParseState` or layout-compatible live object with aligned `u32` subobjects at `+4` and `+8`. The Unicorn tests use mapped byte storage and verify machine behavior only; they do not establish object lifetime for arbitrary buffers or prove callers beyond the observed parser call. MMIO, invalid/unaligned pointers, concurrent observation, and partial-fault ordering remain outside evidence. No emulator or game runtime was used.

Reports are under `build/agent-work/batch-h18-001/h18-fix-pair-store-alias/run-002/seed-7/` and `.../seed-20261024/`. The independent review can now recheck the frozen source, checker, and reports.
