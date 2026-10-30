# Independent production review: H2 config mappers

## Decision

Accept the three mapper replacements as a bounded offline production integration for their observed zero-extended byte input domain. The compiled symbols fit their original 92-byte spans, the final-address differential evidence is reproducible, and the combined image plus State-9/10 composition pass their declared offline cases. The ledger correctly labels all three production bodies non_matching.

This does not establish complete titleConfig behavior or close H2. The caller composition's evidence is partial: important services remain matched HLEs, and it does not schedule Calc, Draw, or Secondary. Real UI/input delivery, persistence, and Azahar behavior remain untested.

## Identity and in-place patch audit

The packet's 23 frozen input hashes all matched at review start. The pinned reference image identity is SHA-256 1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558. The mapper manifest identifies each production source, object, symbol, symbol hash, table, and 92-byte original slot. The two mapper-bearing object hashes are 2aea8bc429a521f894546bd550b44b53d8940493d10d880b06dc188c588d772d (TU B) and 5d0f079cfc288754d3035e0aa2484b88b5e04dcac6e95073efa9280d5931c58d (TU C); their recorded source hashes are dd9dac02bd19c27dd0fdfc9897229757bfc71f68a3e7fb4532ac781c873f325c and 9baf88cee24f0b53c2d330171c194d5795132907b77db0396cc29842fe3743de.

| Function | Production symbol size/hash | Slot | Table |
|---|---|---:|---|
| 0x0021F39C | 48 bytes; 616fdaa08187217f5859996444b65cdce852f6b045f047e0497df4602eaa0451 | 92 bytes | 0x004077F6 |
| 0x002CAB70 | 48 bytes; fbb5b34c4b5b94322cb10ba9da7257fa4010d82c3aa6f754e54d6b32a14c2438 | 92 bytes | 0x004077EB |
| 0x002E0AF4 | 48 bytes; 8b99e056165e42868b91ef1d6498d392261d3fd37197b6ac42331d75ea2e5aaa | 92 bytes | 0x00407801 |

Each symbol consists of 44 executable bytes followed by its in-body absolute table-address literal. The patcher pads each to the existing slot with ARM NOPs. It requires the literal value/location and return boundary, checks the original span and rejects relocations. The manifest records 209 changed bytes over the three slots. Nothing in this patch writes beyond those original spans.

Two independent patcher outputs (run-008 and run-012) were present and independently rehashed. They match byte-for-byte in all five principal artifacts: final image 97b6c2ab9ea7f15904bbee3ad42115599bd3529220dbfba818a77bbbcfbe321c, IPS 72b9c68d2aca701c899978adeb793698032097a2599d70ab9c90a0361336e214, manifest e3f3502e9326cbf82e37ad995d8fb8889dc7a58a71f6ad88676182f7748cf2d5, seed-7 report 7d2518fa46cceb30944882ae302c32751d8d6e11e77a898e26a645c24e829cf6, and seed-20261024 report 55cbdf3d48a91f5ebb6ef136cf95570fe8332002e73f22f4ac19f5c698f7462f. The IPS record hashes and the image hash agree with the manifest's patch chain from reviewed run-013 base image 7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291.

The incoming-reference audit reports 10,967 ledger spans scanned on both the original and run-013 base. It found no direct ARM B/BL/BLX entry or aligned absolute pointer into an overwritten mapper interior. The claimed scope is appropriately limited: computed/encoded-relative targets, unaligned pointer interpretations, and non-ledger instruction/data interpretation are not proven absent by this scan.

## Contract, ABI, and differential evidence

The original mapper tables are eleven ordered bytes each. The behavior is to return the first index whose threshold is greater than or equal to the input, falling back to zero when no threshold qualifies. The thresholds are:

- 0x002CAB70: 0,10,20,25,30,35,40,45,50,70,90.
- 0x0021F39C and 0x002E0AF4: 0,10,20,30,40,50,60,70,80,100,120.

The initializer loads its three persisted configuration bytes with LDRB, and Calc supplies byte-valued config fields. Thus the supported caller domain is 0..255. For each seed, the final-address reports show 512 comparisons per mapper: all 256 byte values plus 256 seeded cases. Every comparison passes with no counterexample. Both original and patched paths read all eleven table bytes and write no data or stack memory. The off-by-one negative control changes mapper A's threshold 10 to 11 and is detected at input 11 (original result 2, mutant result 1). The reports also identify the same pinned image and compiled production identities.

The mapper scan loops retain the original table reads rather than replacing them with unrelated constants. The 32-bit input/result ABI is consistent with the callers' LDRB inputs and r0 result stores. There are no relocations in the mapper symbols. Their 48-byte symbols are intentionally not claimed byte-identical to the 92-byte originals; the exact ledger labels are non_matching.

## Final-address and caller composition

The final-image report identifies the original image and combined mapper-extended image above and passes all declared callback suites: Calc 16/16 sequences and 54/54 ticks; Draw 46/46; Secondary 34/34; initializer 10/10; ready gate 4/4. Its overall caller evidence is correctly marked partial, and runtime is not_run. The initializer suite executes mapper code from the original and patched images, while other declared initializer services remain HLEs.

The State-9/10 caller composition uses the exact combined image and production initializer/ready gate. It passes all three cases (baseline pending-ready, distinct config pending-ready, and the State-9 flag gate) and detects a wrong-primary-Calc-callback negative control. Its argument checks constrain Sound_PlaySE on consumed r0 only and assert call-site-specific consumed arguments for reset HLEs; raw scratch registers remain diagnostic. This is more precise than treating every volatile register as a semantic argument.

Its limits are explicit and material: allocation, process factory, task-active lookup, sprite/resource/cursor setup, Sound_PlaySE internals, transition, touch registration, cursor mode, environment loading and model visibility are matched HLEs. It compares callback registration and TitleConfigWork linkage but schedules none of Calc, Draw, or Secondary. It covers State 9, State-10 pending-ready and the flag gate only—not State-1 input/cursor behavior, rendering, editing, persistence, profile behavior, or emulator runtime. This is useful caller-composition evidence, not a test of actual settings-menu lifecycle.

## Remaining limitations and next action

No production-code correction is identified by this review. Keep the three mapper ledger rows non_matching, retain their semantic records, and accept this bounded offline integration evidence. H2 remains open until the CLI-driven Azahar scenario requested by the milestone is exercised with appropriate original-versus-patched observations. Do not extrapolate the current HLE composition or mapper byte-domain proof to UI appearance, physical input meaning, confirm/cancel behavior, persistence, restart, or whole-game equivalence.

I did not compile, run tests, launch Azahar, use RSP, or control input. This review read the frozen packet and its linked production manifests/reports and independently rehashed their principal artifacts and the two reproducibility outputs.
