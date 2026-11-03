# Independent review: 0x0028DF70 row halfword query

## Finding

**Accept the bounded direct and caller evidence.** No counterexample was found. Original ARM first compares the full unsigned r0 with 6; indices >=6 return 0 before loading the manager pointer. For 0..5, it loads pointer from 0x0043DA2C, calculates manager+0x496+4*index and executes `LDRH`, returning the zero-extended halfword. The typed source preserves the guard and pointer ordering and uses one inline ARM `LDRH` with a memory clobber. No data write or callee is present. Valid aligned ordinary memory is required for in-range indices; invalid manager pointers, concurrent mutation, MMIO and arbitrary faults remain outside the supported domain.

## Independent replay

`python tools/h2_8df70_experiment.py --out build/agent-work/H2-semantic/h2-final-helper-row-query-0028df70-review/run001/fresh --seed 20270121` exited 0: 94/94 direct and 9/9 compositions of original 0x00286928; bound and halfword-offset mutants were detected. The direct matrix crosses six valid indices with eight halfword values and includes 6,7, high-bit values, UINT32_MAX and 40 random values. Invalid indices use an unmapped manager pointer; all returned zero with no observed pointer read. The runner asserts exact in-range pointer-word read then 2-byte halfword read and correct zero-extended return. Separately reran the 94 indices and nine caller fixtures to assert no faults, original-vs-staged parity, SP/r4-r11 and caller d8 preservation. The direct write hook only observes the manager/global region; the no-direct-write conclusion also relies on the inspected original and C++ body, not an all-address hook.

The nine caller fixtures exercise original 0x00286928 selector 6, r2=0 and row bytes 7/8/9 crossed with getter outputs 5,4,0xFFFF. Every case enters the actual getter once with index 0. Return 5 drives the byte stores at object+0xA26/+0xA12 and reaches 0x002B8CCC/0x002B8B78; other values skip them. Other helper callees are controlled stubs. These cases do not establish full 0x00286928 behavior, scheduler state, natural H2 reachability, audio effect or runtime.

Fresh production body is 40 bytes with no relocations, SHA-256 `2252e566878c7b7b99fb29c0486cc68f0e4ae6520f1a00619f3a0c8225541439`; its compiled form differs from the pinned original. Independent IPS parsing confirms one 40-byte slot record and exact staged-image replay; original `BL` at 0x00286B60 resolves to even ARM 0x0028DF70. That supports final-VMA static placement and entry mode, not installed runtime.

## Ledger, README and provenance

Frozen ledger contains 10,881 matching functions / 3,116,740 bytes plus eight matching spans / 484 bytes = 3,117,224 matching; 78 non-matching / 21,884 bytes; 3,139,108 total. `3,117,224 / 3,139,108 * 100 = 99.30285928359265%`, correctly rounded to README 99.3029%. Getter is truthfully `non_matching`. All 13 packet input hashes matched before replay.

Reference SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; source `d58af51b015546dff6a5a4918413ace7ec3dd70455c19295e7873111159a7f50`; runner `943299e24a76d2ac19a8c4b105610b635390438795c5b13931c90bf6c57cd13f`; fresh report `3bf900418cf06ab87b3acfc219ca49dfa55888a189067d07c098426526fd42ec`. No full build, emulator or runtime executed.
