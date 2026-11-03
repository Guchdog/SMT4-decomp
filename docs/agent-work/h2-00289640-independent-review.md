# Independent review: 0x00289640 state getter

## Finding

**Accept the bounded ordinary-RAM getter evidence; no counterexample found.** Original ARM loads literal base 0x0044DE98, reads the pointer at 0x0044DEB8, then reads the full word at pointer+0xD0 and returns it in r0. The input argument is ignored; there are no data writes or helper calls. The typed production source folds the literal to the same pointer slot and uses volatile 32-bit reads. There is no null check; valid aligned mapped slot and object word are required. Invalid pointers, faults, MMIO, concurrency and lifetime are not established by these tests.

## Independent replay

`python -B tools/h2_89640_experiment.py --out build/agent-work/H2-semantic/h2-callback-getter-00289640-review/run002/fresh-seed --seed 20270116` exited 0: 40/40 direct and 5/5 original 0x00221168 callback compositions matched; the +0xD4 wrong-offset mutation was detected. Independently inspected all 40 direct records: no faults or writes, exactly two observed data reads at 0x0044DEB8 and state+0xD0, raw r0 equals requested test word, and r4-r11/SP/LR equal initialized values. Cases include eight boundaries and 32 fresh random values with varied ignored r0 and state addresses. The original instruction literal fetch is code data and is outside the recorded two runtime state reads.

All five caller fixtures reached the real getter twice and the final-helper stub once, with exact six arguments `(0xACCE5501,0xBEEF0020,state_word,6,1,0)` and stub return 0x13572468. The original 0x00221168 body and 0x0028DF3C run; 0x0028686C, 0x00296F60 and 0x00286928 are controlled stubs. This verifies the getter's bounded composition, not the full callback dependency chain or natural H2 behavior. The runner compares selected registers, reads, writes and memory but not CPSR, VFP, every memory location or runtime.

The private production object has a 20-byte body, no relocations, SHA-256 `a6217a31e982312c187059bd38b4777406f8a0b34585f079400a892adea21988`. Staged image differs from pinned original at 0x00289644 and 0x00289650, so the current ledger `non_matching` is truthful; original callback BL sites 0x00221178 and 0x002211CC target the even ARM entry, and compiled body returns via ARM `BX LR`. This is offline evidence, not a runtime or integration scenario.

## Ledger and README check

At review time `config/functions.csv` SHA-256 `0597092cddef0e6f2f5d357bb89cffa19a9e48a636997470b905fe4edf76c9fd` contains 10,885 matching functions totaling 3,116,988 bytes, eight matching spans totaling 484 bytes, and 74 non-matching functions totaling 21,636 bytes. Therefore README's matching 3,117,472 and explored 3,139,108 are arithmetically consistent. README SHA-256 `7ca3afac8c1630f14eebec2ba7014c446543b3fa78170dc2ca00ba2a757a85ed` says H2 remains open and describes the prior 40+5 tests consistently. The separator between `0x00128C2C` and `0x0012A758` is present. Ledger and README are frozen in run002 at the stated hashes.

## Provenance and next action

All 14 run002 packet input hashes matched before replay. Pinned original SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; production source `ba79b34feea23f9409bdfd6c3eccb25143de3ed75ed77d2aa2d8c12711517d97`; runner `4ca48670bce181fcebed31a49713aa0775db07daa119eaabba1818b4ec97b341`; fresh report `3efaefbf4469e1461343f00b549ed332a03a29cd8b2837eb32c933597026d032`. No emulator or runtime scenario was run. Independent review supports only this getter's tested contract; keep H2 open and separately test original dependency chain and integrated runtime.
