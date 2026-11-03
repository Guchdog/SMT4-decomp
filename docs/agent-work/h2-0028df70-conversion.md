# H2 final-helper row query conversion: `0x0028DF70`

## Result

Replaced only `camp_func_0028df70` in `src/engine/leaf_batch26_b.cpp`. The typed guard is unsigned `index >= 6u`; it returns zero before reading the manager pointer for out-of-range inputs. In-range inputs load the manager pointer at `0x0043DA2C` and use the selected row's halfword at `manager+0x496+4*index`, returned zero-extended as `uint32_t`. A single inline `LDRH` constraint lets the compiled helper fit its original 40-byte ARM slot. There are no relocations.

## Validation

```text
python tools/h2_8df70_experiment.py --out build/agent-work/H2-semantic/h2-final-helper-row-query-0028df70-convert/run001/checks/seed-20261106-final --seed 20261106
```

Exit 0: 94 direct cases and nine compositions through the original `0x00286928` passed with zero differences. Direct cases cross every valid index 0–5 with eight varied halfword boundaries; they also test 6, 7, high-bit values, `UINT32_MAX`, and seeded indices. Out-of-range inputs use an unmapped manager pointer, confirming no global pointer read. The original final helper was run for rows 7, 8, and 9 with getter return values 5, 4, and `0xFFFF`; the production getter remained real and the controlled remaining callees produced matching call/write/continuation traces. The return-5 path performed the `+0xA26` and `+0xA12` byte writes and called `0x002B8CCC`/`0x002B8B78`; non-5 paths skipped them. The getter BL at `0x00286B60` targets even ARM `0x0028DF70`.

The bound and offset negative controls were detected. Report SHA-256: `2d9b29de478fda970079d7d93dab363fba0cf4dc702bfe3f332343678aea9685`. The body is 40/40 bytes; IPS replay is exact and changes are confined to the slot.

## Limits and ledger follow-up

Unrelated `0x00286928` callees remain controlled stubs in this row-path harness, so evidence is partial caller composition, not full helper equivalence. No other rows, callers, or emulator behavior are claimed. The coordinator corrected the ledger to `non_matching`, since bytes differ. Independent review run001 accepted the bounded evidence; the full ARMv6K build passed 204/204 translation units (see `h2-0028df70-integration.md`).
