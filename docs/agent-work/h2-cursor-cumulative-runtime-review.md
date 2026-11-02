# Independent review — H2 cumulative cursor runtime

## Recommendation

Accept this as bounded autonomous runtime evidence for the defined paired H2 TitleConfig scenario. It is not evidence that the H2 lifecycle is complete: readiness and same-session reentry did not complete on either side, and the report explicitly says full controlled lifecycle is false. Keep the milestone open. No blocker was found in the provenance/replay or integrity checks below.

## Frozen-input and artifact audit

I read the assigned `task.json`, `brief.md`, `AGENTS.md`, and `docs/agent-workflow.md`. Recomputed every SHA-256 in the packet’s `input_sha256` map; all 23 declared entries match, including the original image, cumulative image, IPS, both runtime report copies, both autonomous GDB report copies, runner hashes, profile files, config, workflow note, and reports. Run001 and run002 runtime reports and GDB reports are byte-identical by hash.

The image/IPS pins are:

- Original `extracted/exefs/code.bin`: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Cumulative image: `aca919c95b0bc58af0a50b9f9f7f7d22084c2eb1dba5767889258920b08c582f`
- Original-based IPS: `c4c4667fa564b846830b01a6b2226b480f1e99a5e3785b7c4ca89c95eeec643c`
- Runtime report: `5a02e2a16f5a25b15f8d2bbcd55281b817ef983383aca22d6662410f66b17734`
- Autonomous GDB report: `d0aa7b2419a93c9c793ab86032e306e7fdb746d5f39676dba80f94365d4f69bc`

I independently replayed the IPS records against the pinned original: 822 records, 6,397 differing bytes, and the resulting bytes exactly equal the pinned cumulative image (SHA above). The paired report also records `ips_roundtrip: true`.

## Runtime and integrity result

The paired report records 51/51 scripted actions and 19/19 state checkpoints matched. Readiness remained incomplete in both original and patched profiles. Same-session reentry also remained incomplete on both; restart-state/persistence outcomes matched. Both runs shut down cleanly. These are comparable outcomes, not successful completion of the lifecycle.

The driver calls the original `UiListCursor_SetSelectedRow` and replaces the logical query with deterministic one-frame responses. The report expressly does not establish physical controller mapping or natural input scheduling. Its declared limitation also remains material: it does not observe every `0x0027FBC8` output write and cannot establish that the no-write axis sample domain is unreachable. This is one scripted scenario, not whole-game equivalence.

The report says the profile seed, runtime support assets, and private Azahar were unchanged. Independently confirmed the profile seed before/after file maps are equal, recomputed the two packet-pinned config hashes, and hashed all 58 currently present runtime-support assets against the recorded post-run manifest: no missing or changed files. The private `azahar.exe` exists and matches the report SHA-256 `1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682`. At review time, no `azahar` process was present and no listener was present on ports 60340 or 60341; I did not relaunch the emulator.

The aggregate static audit remains marked not passed due to two inherited ARM-to-Thumb findings in `ui-statusdown-itemsort` at `0x0032C5D0` and `0x0032C600`; the runtime report states these were unchanged and not introduced by this image. This review does not reclassify those findings.

## Commands and exits

- Read-only Python SHA-256 audit of all packet `input_sha256` entries: exit 0; all entries matched.
- Read-only Python IPS replay from `extracted/exefs/code.bin` to the pinned cumulative image: exit 0; 822 records and exact byte match.
- Read-only Python verification of profile maps, runtime asset manifest, and private Azahar SHA-256: exit 0; all matched.
- PowerShell `Get-Process -Name azahar`: no process found.
- PowerShell `Get-NetTCPConnection -State Listen -LocalPort 60340,60341`: no listeners found.

No compilation, runner, build, or emulator was run for this review.

## Evidence level and next step

Runtime evidence is **partial** for H2 acceptance, although the bounded paired scenario itself passed. Compiled, ARM differential, and caller evidence were not independently rerun in this assignment. Preserve the no-write axis uncertainty and incomplete readiness/reentry status in the integration record. Next, obtain evidence that exercises the no-write path or bounds its reachability, and a controlled scenario that can complete readiness and reentry on both original and cumulative images; then review the inherited interworking findings separately before claiming broader acceptance.
