# H2 logical mode-1 query integration

## Result

`ui_func_002bffbc` (`0x002BFFBC`) is now typed production C++ in
`src/engine/leaf_batch32_c.cpp`. It rejects unsigned IDs `>=31`, returns zero
when bit 0 of `*(u32*)0x004650A8` is set, and otherwise returns one only when
`*(u32*)(0x004E3C58 + 4*id) == 1`. It performs no guest writes. The H2 Calc
caller uses IDs 9, 0 and 1 through this mode-1 path.

The pinned original is 60 bytes. The compiled production function is 68 bytes
with no relocations; its ledger classification is therefore `non_matching`.
The final direct differential ran 506 calls: a complete 31-ID by four-flag by
four-counter matrix, plus ten invalid-ID cases. The ID 31 case seeds its
adjacent counter slot to one and detects a mutant that accepts that ID. The
runner compared returns, faults, PC, SP and r4-r11, found no guest writes, and
detected wrong-flag, wrong-counter-index and off-by-one-bound mutants.

Eight production/caller translation units compiled with the new typed return
and argument declaration. Results and object hashes are in the compile report.
Focused test result: 5/5 passed.

## Reproduction

```powershell
python -m unittest tests.test_h2_logical_mode1_query_experiment -v
python -m tools.h2_logical_mode1_query_experiment --output build/agent-work/H2-semantic/h2-logical-mode1-boundary-fix/run-002/checks/differential-20261026
```

The compile helper used the repository's ARMv6K target with `-O2`, hard-float
ABI, freestanding mode and one compiler process. The compile report captures
exact arguments and output hashes.

## Evidence limits and next step

This closes only the isolated query contract. It does not identify physical
controls or prove the freshness and scheduling of the counter producer. It does
not establish input delivery, caller sequence behavior, an IPS image containing
this changed function, or the H2 runtime scenario. Independent review is
required before promotion. Azahar, GDB/RSP, RPC, profiles and guest state were
not accessed.
