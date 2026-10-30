# Independent audit: H0–H3 plan and completion claims

## Summary finding

H0 and H1 are supported as explicitly bounded smoke/menu-slice milestones. H3 is supported for the known-save route in the final H2+H3 test image; its post-open read failure remains partial. H2 has a canonical 12-checkpoint original-versus-patched run on the stated final image, but the raw checkpoint values do not substantiate the report's SE and Voice checkpoint labels: those checkpoints change the BGM config/work field while SE and Voice remain at 8. Manual observations partially cover SE/Voice, but have no exact guest-byte or synchronized-input record and were run on a different H2 image hash. I therefore do not consider the broader three-slider H2 acceptance fully supported by the current evidence.

The blocked/claimed auxiliary tooling tasks do not, by their status alone, invalidate the bounded H2 result. The `h2-final-live-cli-capture` task is directly relevant to the still-unproven exact-input/guest-state requirement, though: it remains blocked. The substantive H2 checkpoint mismatch is independent of those task states and needs reconciliation or corrected evidence before claiming all three controls were machine-verified.

## Frozen input and artifact hashes

All 22 hashes declared in this task's `task.json` match the current checkout. The pinned H0 batch-4 reports, patch/image files, H2 final composition and autonomous report, and H3 final-composition review are present and match these identities:

| Artifact | Size | SHA-256 | Audit result |
| --- | ---: | --- | --- |
| H0 batch-4 `seed-7/code.ips` | 456 B | `9b5f7c8f261743a2805d356153232f445c02f00c2f7938e7550505bc4b6317f9` | Matches report |
| H0 batch-4 `seed-7/code.experimental.bin` | 3,633,152 B | `ce9d9e77acae832049fb56bfe7952db8dd69a83a99b5f409cdd3a093bbd49120` | Matches report |
| H0 batch-4 `seed-20261024/code.ips` | 456 B | `9b5f7c8f261743a2805d356153232f445c02f00c2f7938e7550505bc4b6317f9` | Same IPS as seed 7 |
| H0 batch-4 `seed-20261024/code.experimental.bin` | 3,633,152 B | `ce9d9e77acae832049fb56bfe7952db8dd69a83a99b5f409cdd3a093bbd49120` | Same image as seed 7 |
| H2 final `code.h2-final.bin` | 3,633,152 B | `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446` | Matches H2 GDB report |
| H2 final `code.h2-final.ips` | 6,891 B | `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb` | Matches H2 GDB report |
| H2 `autonomous-gdb-verification.json` | 50,473 B | `e370da857f1738409decc468bee81859eb84cfc9278bacf3d0c9d0b460d045b8` | Present; `passed=true` |
| H3 `composition.json` | 670 B | `b7bce10550608004ae45bad2cd06803af201900a69caa2a4b59bb7256d7f1006` | Matches H3 evidence manifest |
| H3 combined `code.h3-h2final.bin` | 3,633,152 B | `81c1c6ae72d88b689cde3e9982439c8f8c4a6e8773887547f4cb85b86cd34a20` | Matches composition and GDB report |
| H3 combined `code.h3-h2final.ips` | 7,030 B | `95846920df9ceb0e6395b6fb7e5358c99b83dd14e5861ffcfa80d8e64208eda5` | Matches composition and GDB report |
| H3 paired known-save report | 264,355 B | `d653259f803e9cb5814b12da849bda44595fb17f00b47b0462db704eed7c36e5` | Present |
| H3 paired post-open read-error report | 30,827 B | `adb543faa6b31f6b59b803828902576f6418c1833a3bc711feca0c94ca03b326` | Present |
| H3 independent composition review | — | `b7cc029f1b284d1c5bf0b8aca9b4fbc15c10da017673f41690aca9f27b62c6f1` | Present |

The two H0 seed directories contain the reports, IPS, and `code.experimental.bin`; there is no `code.bin` under those directories, so the reports' image hash refers to `code.experimental.bin`, not a file literally named `code.bin`. The H0 screenshots and preserved prior IPS backup named in the milestone record are present.

The H2 manual final-image staging manifest is also present. It identifies a different final-image hash, `cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4`, and staged IPS hash `bb9fc65956b2261468825a3732a2019cdd69226a6402309716bbeadfb26ac808`. These are not the canonical H2 image/IPS (`acd8…` / `67e4…`) used by the accepted autonomous report. Treat that manual observation as supplementary evidence for its staged revision, not as a runtime check of the canonical H2 image.

The older path `E:\SMT4decomp\build\h3-runtime-comparison\run-002\runtime-missing-before-confirm-044\report.json` is absent. It is superseded by the present `h3-final-composite/evidence-run-001` reports and the mirrored private-runtime evidence at `E:\SMT4decomp\build\agent-work\H3-semantic\h3-final-h2base-revalidation-20261028\`. The current H3 report/review chain is present; no current H3 conclusion here depends on the absent legacy path.

## Numbered plan audit

| Plan section | Status | Evidence and limit |
| --- | --- | --- |
| 1. Inventory and scope | **Partial** | The inventory distinguishes runtime, production C++, experiments, and limits, but explicitly leaves per-address reconciliation to the ledger and report links pending. It does not yet provide a complete accepted/partial/pending crosswalk. Counts below are a bounded reconstruction from the records, not a percentage. |
| 2. H0 reproducible base | **Proven for its stated smoke scope; partial for the broader menu** | Both batch-4 seeds report the same pinned reference, IPS, patched image, 14 leaf experiments, 11 caller windows, and detected negative controls. The H0 Azahar record separately confirms patch application, title → Audio Settings → title, and two observed entry hits. The reports explicitly exclude a full game boot/equivalence claim; hits prove reachability only. |
| 3. H1 main menu | **Proven for the closed slices; partial against the entire plan wording** | The two state-5 C++ slices, three TBB helpers, caller checks, and bounded Azahar navigation/Audio Settings/return route are recorded. New Game, Load Game, and AOC destinations were intentionally not run; most of the callback remains original ARM. The milestone's bounded closure is supported, not a full menu reconstruction. |
| 4. H2 audio settings | **Partial; the 12 paired comparisons pass, but three-slider checkpoint labels conflict with raw values** | The canonical report matches the final H2 image and passes 12/12 equality comparisons. However, see the direct discrepancy below: the raw `se_set_to_4` and `voice_set_to_4` checkpoints leave `se_2c=8` and `voice_30=8` while changing `bgm_28` and the first config byte. Manual UI observations report SE/Voice edits and endpoint behavior, but do not supply exact bytes or input traces. |
| 5. H3 load from title | **Proven for the bounded known-save route; partial for read-error handling** | The final paired known-save run reaches acknowledgement and the field manager in both profiles and records 250 semantically concordant field callbacks. Prior paired runs cover empty-slot/cancel. The separate after-open truncation trace records open `r0=1`, read size `0x24E30`, `AsdSave_Read r0=0` (intact `r0=1`), validator `r0=1`, and clear-flag `r0=6`; it captures no final status marker, acknowledgement, field-manager entry, or visible error. Reader/parser/validation/I/O remain original. |
| 6. Per-function validation and promotion | **Partial** | There are reviewed bounded C++ replacements and candidates, but not every function in the H0–H3 paths is reconstructed. Stubs, original dependencies, unintegrated candidates, and the unresolved H3 error response remain. “Passed” reports establish only their recorded domains. |
| 7. Joint regression and closeout | **Partial** | H2+H3 image composition is reproducible and H2's 12 checkpoints were repeated on it; the H3 known-save scenario and final independent composition review are present. The evidence is not one fresh end-to-end H0→H3 run: H0 uses batch-4, H1 uses its own composed/runtime package, and the H2+H3 closure uses a later image. H2's checkpoint discrepancy also prevents using the repeated report to close the three-slider gap. |

## H2 checkpoint discrepancy and board tasks

The canonical `build/h2-runtime/autonomous-verify-run001/autonomous-gdb-verification.json` and the repeated H2 regression in the H3 composite both have 12 entries with `passed=true`. The equality predicate is original-versus-patched state equality; it is not an assertion that a named logical control was changed to an expected value. Comparing the milestone's expected bytes with the raw canonical report exposes these mismatches:

| H2 label | Milestone's stated result | Canonical raw report |
| --- | --- | --- |
| `bgm_min_clamp` | `g_ConfigBytes=0050503000000000` (minimum 0) | `bgm_min_clamp_step_6`: `1450503000000000`, `bgm_28=2` |
| `se_set_to_4` | `2d46503000000000` | `2850503000000000`, `bgm_28=6`, `se_2c=8`, `voice_30=8` |
| `voice_set_to_4` | `2d46463000000000` | `2350503000000000`, `bgm_28=5`, `se_2c=8`, `voice_30=8` |
| `voice_max_clamp` | Voice reaches maximum 10 and returns to 4 | `voice_max_clamp_step_7`: `5a50503000000000`, `bgm_28=10`, `se_2c=8`, `voice_30=8` |

The raw report therefore supports matched state at those sampled points, but not the milestone's claim that those points set/clamp SE and Voice. The H3-composite report repeats the same state pattern; it is not an independent correction. The manual runtime log reports visible SE and Voice changes and endpoint stops, but lacks `g_ConfigBytes`, exact values, identical timing/input records, and SE/Voice cross-restart checks. That is useful partial evidence, not a repair of the raw checkpoint mismatch.

Current non-accepted H2 board tasks:

- **Blocked and auxiliary/superseded for the canonical GDB closure:** `h2-azahar-rsp-probe`, `h2-azahar-binary-loopback-audit`, `h2-manual-patched-runtime`, `h2-private-azahar-live-wrapper-review`, and `h2-final-image-stage-tool-update-review`. Later accepted private-loopback GDB, corrected-image manual staging/runtime/review, and autonomous verification supersede the earlier probes/packages.
- **Blocked and directly relevant to richer input evidence:** `h2-final-live-cli-capture` would record the same human-controlled original/patched action sequence with live guest-state snapshots. Its absence leaves the strict exact-input/bytes clause partial; it does not erase the current bounded 12-checkpoint result.
- **Claimed auxiliary observer engineering:** `h2-observer-failure-isolation` and `h2-synchronized-query-capture-design` improve optional live observer capture. The accepted GDB report does not depend on them, so their claimed state is not itself an H2 acceptance failure.

Conclusion on status: **blocked/claimed tooling rows alone do not invalidate the bounded H2 closeout; the raw checkpoint mismatch does prevent treating the 12/12 pass as proof of all three controls.** Preserve the H2 closure only as a narrower state-checkpoint/manual-observation result, or reconcile the labels and obtain corrected SE/Voice guest-state evidence before asserting the full documented three-slider acceptance.

## Milestone statuses and unique replacement-unit count

| Milestone | Justified status | Accepted scope versus remaining work |
| --- | --- | --- |
| H0 | **Closed, bounded test base** | Reproducible patch/application and title/audio/title smoke route are supported. No area logic is accepted from the two hits alone. |
| H1 | **Closed for state-5 navigation/confirmation slices and TBB dependencies** | Five integrated code units: three TBB helpers plus two disjoint slices inside `ui_func_001e989c`. The full callback and New Game/Load/AOC destination behavior remain outside this closure. Alpha and track candidates are not promoted units. |
| H2 | **Closure claim requires qualification/reconciliation** | The canonical image/runtime identity and 12 paired comparisons are proven, but not all expected SE/Voice outcomes are shown in raw checkpoints. Manual evidence is partial and for a prior image hash. Do not describe the wider three-slider acceptance as fully machine-verified yet. |
| H3 | **Closed for known-save happy path; error response partial** | One H3 C++ candidate (`SaveLoad_BeginFromTitle`, `0x0030A9A4`) was compiled into the final experimental composition and has differential/caller/runtime evidence. Downstream reader, parser, validator, and I/O remain original. |

Count rule: count distinct behavior units once, separate different slices from full functions, and exclude mere hits or candidate definitions from integrated replacements.

| Category | Unique units | Reconciliation |
| --- | ---: | --- |
| H0 runtime-observed batch-4 entries | 2 addresses | `0x0037C46C` and `0x002ADB40`; neither is an H0 reconstruction acceptance. `0x002ADB40` is the same function address later represented by H2 `UiConfig_CopyPair`, so it is not added as another function. |
| H0 batch-4 differential candidates | 14 addresses | Same 14 in both seeds, same image and IPS; 14/14 reports are not 28 functions or 14 accepted production replacements. Only two got H0 runtime hits. |
| H1 integrated production code units | 5 | Three TBB functions + two state-5 replacement slices. The two slices are one containing callback function address. All are non-identical replacements under the documented ledger classification. |
| H2 integrated production code units | 10 | Five titleConfig functions, three mappers, FillPair, and CopyPair. Nine are non-matching replacements; CopyPair is byte-identical (`matching`) and is the same `0x002ADB40` unit seen in H0. |
| H3 final-image experimental candidate | 1 | `SaveLoad_BeginFromTitle` at `0x0030A9A4`; experimental compiled overlay in the final H2+H3 test image, not promoted as production C++ in the ledger. The original preserved source row remains `matching`; that label is not a claim about the candidate overlay. |
| Other named C++ candidates not in final IPS | At least 5 | H2: `0x0029D8FC`, `0x0019DFBC`, `0x002BFFBC`, `0x002B902C`; H1 alpha `0x0029BDB4`. Excluded from integrated counts. H1 track binding/candidate evidence is also not counted as a promoted replacement. |

Thus the bounded H1+H2 production count is **15 replacement units** (14 non-matching plus one matching unit), not 15 fully reconstructed game functions: two H1 units are regions of one callback. H3 contributes **one additional experimental image replacement**, making 16 code units across the selected final test image, of which 15 are H1/H2 production units and one is an H3 candidate overlay. H0's 14-function experiment and its two observed hits are separate historical evidence and are not summed into these totals. The generated inventory's 180 experimental definitions are not an accepted-unit count.

## Procedure, limitations, and handoff

- Recomputed every declared task input hash: all matched. Recomputed H0 report image/IPS files, H2 canonical image/IPS and report, and H3 composition/image/IPS and selected report hashes listed above.
- Read the H0–H3 plan, inventory, functional status, reconstruction plan, milestone records, H3 independent review, H2 board and bounded reports. Read-only PowerShell/Python JSON/hash inspections exited 0.
- No build, test, emulator, source/ledger/board edit, or user input was used.
- Limitation: this audit follows current records and their scoped artifacts; it does not reproduce runtime evidence or prove unobserved input behavior. Several auxiliary package files remain outside the current checkout/private E: evidence root; the identified legacy H3 report path is superseded.

Next action: reconcile the H2 labels/expected states against the actual 12-point runner trace and correct or rerun the SE/Voice checkpoints on the canonical H2 image. Keep H2's closure text explicitly scoped until that reconciliation is complete; continue to label H3's read-error response partial.
