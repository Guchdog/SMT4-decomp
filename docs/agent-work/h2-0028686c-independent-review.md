# Independent review: 0x0028686C callback getter

## Findings

**Accept the bounded getter review.** The ledger correctly labels the differing 20-byte body `non_matching`. The matching fraction 3,117,452 / 3,139,108 equals **99.31012249%**, correctly rounded to **99.3101%** in the run002 README. The prior run001 README showed 99.3102% and has been corrected.

Pinned original loads literal 0x0044DE98, reads a pointer at 0x0044DEB8 and then returns the entire word at pointer+0xC0 in r0; input r0 is ignored, there are no data writes or calls, and no null guard. The C++ source uses two volatile word loads in that order. Valid aligned mapped ordinary RAM is required; invalid pointers, faults, MMIO, concurrent writes and lifetime remain outside tested scope. The code has ARM `BX LR` and no relocation; r4-r11 and SP are ABI-preserved, while CPSR/VFP and all scratch state are not comprehensively tested.

## Independent replay

`python tools/h2_8686c_experiment.py --out build/agent-work/H2-semantic/h2-callback-getter-0028686c-review/run001/fresh --seed 20270117` exited 0: 38/38 direct, 50/50 compositions of original 0x00221168, and wrong-offset +0xC4 mutant detected in both. Additional calls using the same frozen runner independently asserted for every fixture: no fault, SP restored, r4-r11 preserved, direct raw return, exactly two observed data reads 0x0044DEB8 and table+0xC0, no direct writes, and the callback helper order `[0x0028DF3C,0x00289640,0x0028686C,0x00296F60,0x00289640,0x00286928]`. The test includes varied ignored r0, return boundaries, state mutation between the two original getter calls and exact final helper arguments.

The original callback, 0x0028DF3C and both 0x00289640 calls execute as ARM; 0x00296F60 and 0x00286928 are controlled seams. These tests establish the bounded composition only, not those helper implementations, full callback behavior or H2 runtime. Fixtures use a fixed valid table address and synthetic RAM.

The private production body is 20 bytes with no relocations, SHA-256 `c3451e66a26af449900965de03764d0db9dce9740eab6f86e39906329c415605`; object SHA-256 `cd775f679b15c2474d28e9a05b4ec0615e79054a80e71b9c6b513fefcaa26e77`. Independent IPS parsing/replay confirms a single 20-byte slot record at file offset 0x18686C, exact image reproduction and changed bytes only 0x00286870 and 0x0028687C. Original callback BL at 0x002211B4 resolves to even ARM 0x0028686C; the staged body returns via `BX LR`. This is offline evidence, not proof of installed-game behavior.

## Ledger, provenance and limits

Frozen ledger: 10,884 matching functions totaling 3,116,968 bytes plus eight matching spans totaling 484 = 3,117,452; 75 non-matching functions total 21,656; overall 3,139,108 bytes. README's counts and corrected percentage agree. No README or ledger edit was made in this review.

All 13 run002 packet hashes matched. The run001 fresh replay is reused without recompilation: its source and reference identity, report, object, staged image and IPS hashes were rechecked unchanged. Reference SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; production source `c1c773f43dad73a2e44158667ad6750c4e2cdf50b8df41534415a8845281e533`; runner `fa9f58224ff6da4c5785b8faf7f375b175b41187f05fdbae7255f7f947f7fdb4`; fresh report `9fa9652f5ed2851ec6d5665ce9c4b270d8dac079a70c33a9d16315179f989a18`. No emulator or runtime was run. Separately validate the full helper chain and integrated runtime before broader H2 claims.
