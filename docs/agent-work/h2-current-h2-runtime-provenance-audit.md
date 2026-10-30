# H2 runtime provenance and acceptance audit

**Task:** `h2-current-h2-runtime-provenance-audit`  
**Scope:** read-only audit of the frozen final-image artifacts and run-005 captures. No build, tests, emulator, debugger, save/profile access, or source/board/ledger edits were performed.

## Finding

The final H2 image contains the target helper machine-code bodies byte-for-byte as found in the pinned production objects. The composition manifest still reports four whole-TU source hash mismatches, but a subsequent coordinator-owned check resolves the selected-body lineage: `build/agent-work/H2-semantic/h2-current-h2-production-source-body-check/run-001/function-body-comparison.json` (SHA-256 `7471b758d6167b2a1b10543b3f7c4ef2e2ec091749c4ae18c5a59d3ed4d4186e`) records fresh compilations from the current three TUs and confirms all four extracted symbols equal the previous production objects and final-image bytes, with zero symbol relocations. Its handoff records the three single-job `build_check.py` commands and body-comparison command as exit 0. I inspected that report after the coordinator supplied it; I did not build or rerun those commands in this audit.

The current C++ definitions differ from `HEAD`'s former assembly stubs because they are intentional reconstructions, not because the selected compiled bodies drifted after integration. In the fresh check, the full `leaf_batch32_c.o` hash differs from its previous object while both mapper symbols remain identical; `leaf_batch32_b.o` and `leaf_matching.o` whole-object hashes also match their previous objects. The four manifest source identity mismatches remain whole-TU hash metadata mismatches and cannot, on their own, locate source changes. With the independent fresh-body comparison, there is no selected-body drift between the current source's compiled output, the pinned production symbols, and the final image. The manifest's source identity fields remain stale/unreconciled at TU granularity.

Run-005 provides useful paired guest-state snapshots and manual behavior reports, but it does not close H2. Criterion 6 remains open: there are no logical input/query return events, original and patched snapshot counts differ, action labels come from the user's notes, and the process-to-Azahar-binary identity is unresolved.

## Final image and object lineage

Recomputed packet inputs: **35/35 SHA-256 pins matched**. Final `code.h2-final.bin` is 3,633,152 bytes, SHA-256 `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`. Its standalone IPS is `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`; composition manifest is `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`. The manifest identifies 533 IPS records and 4,218 changed bytes.

The image composition includes five title callbacks (Calc `0x001EA928`, Draw `0x002CAFD0`, Secondary `0x002CAEF0`, initializer `0x002F4CA0`, ready gate `0x002FC0EC`), three configuration mappers (`0x0021F39C`, `0x002CAB70`, `0x002E0AF4`), and `UiConfig_FillPair` (`0x0027EDF8`). The `UiConfig_CopyPair` body at `0x002ADB40` is recorded as preserved, not overlaid by this final composition. The callback cave placements and hashes are in the composition manifest.

I parsed the ELF32 symbol tables from the pinned objects and compared each target symbol's extracted bytes to the final image at `VMA - 0x00100000`. All four comparisons are exact:

| Function | Object (whole-file SHA-256) | Symbol size / SHA-256 | Final image comparison |
|---|---|---|---|
| `camp_func_0021f39c` | `leaf_batch32_b.o`: `2aea8bc429a521f894546bd550b44b53d8940493d10d880b06dc188c588d772d` | 48 B / `616fdaa08187217f5859996444b65cdce852f6b045f047e0497df4602eaa0451` | exact at file offset `0x11F39C` |
| `camp_func_002cab70` | `leaf_batch32_c.o`: `5d0f079cfc288754d3035e0aa2484b88b5e04dcac6e95073efa9280d5931c58d` | 48 B / `fbb5b34c4b5b94322cb10ba9da7257fa4010d82c3aa6f754e54d6b32a14c2438` | exact at file offset `0x1CAB70` |
| `camp_func_002e0af4` | same `leaf_batch32_c.o` | 48 B / `8b99e056165e42868b91ef1d6498d392261d3fd37197b6ac42331d75ea2e5aaa` | exact at file offset `0x1E0AF4` |
| `camp_func_0027edf8` | `leaf_matching.production.o`: `b59d0fa7d71b58be50b08ef10a9c0061816c5b37c3f23c5318a39313869bd3e3` | 24 B / `43f1278d7a4e61088c5b91786351f36a1d949a0d00294e3e617d7813c9bb648c` | exact at file offset `0x17EDF8` |

The manifest's source hash expectations differ from the current packet-pinned files: `leaf_batch32_b.cpp` expected `dd9dac02…`, observed `882993ac…`; `leaf_batch32_c.cpp` expected `9baf88ce…`, observed `56893b2c…`; `leaf_matching.cpp` expected `b5e511d0…`, observed `90238ffc…`. `git diff` against `HEAD` shows that the current source contains the intended C++ mapper and FillPair reconstructions where `HEAD` had naked assembly (definitions at `leaf_batch32_b.cpp:1774`, `leaf_batch32_c.cpp:3537` and `6128`, and `leaf_matching.cpp:2577`); the TUs also contain other edits. The composition manifest's expected object hashes match the frozen production objects.

The independent fresh-source check described above removes the remaining ambiguity at function-body level: it compiled the current source files and found all four target symbols byte-identical to the pinned production symbol bodies and final image. The fresh `leaf_batch32_c.o` whole-file hash (`681e67ee…`) differs from the pinned object's (`5d0f079c…`) while both target mapper symbols match; the fresh `leaf_batch32_b.o` and `leaf_matching.o` hashes also match their pinned objects. Thus the current source reproduces the integrated bodies; the manifest's whole-TU source identity warnings remain but do not indicate target-body drift. The manifest expected-source snapshots were not available, so the precise historical source edits behind those whole-file mismatches cannot be reconstructed from this task's inputs.

## Azahar executable identity in run-005

The run-008 and run-009 staging snapshots record the intended staged command arrays under `E:\SMT4decomp\build\h2-manual-comparison\run-008\{original,patched}\app\azahar.exe` and run-009 respectively, with the pinned CCI SHA-256 `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`. Both snapshots mark themselves `staging_only_runtime_not_run=true`; they say their source executable was `E:\emulador3ds\azahar.exe`, SHA-256 `c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`, and list that same digest for the staged profile executables.

By contrast, run-005 `runtime-report.md` identifies the private build executable by SHA-256 `e9eaa321899a796c17e9460cf8b4a7e003e2606712f1fcc8f1fb485d8f5f406d`. The independent run-005 review notes that the private delivery manifest uses this `e9eaa…` digest, while staging metadata uses `c248…`. The runtime comparison JSON stores neither executable path nor executable hash; manual notes give PIDs, while exact wrapper/restart invocation records and process image path/hash are absent. The staged command metadata and report therefore disagree, and the saved evidence cannot determine which image each process actually loaded. This is an unresolved provenance gap, not proof that the wrong executable ran.

## Run-005 capture facts

The four JSONL files have matching hashes and complete terminal records: original live 7 snapshots, patched live 4, and one snapshot in each restart capture. All four have **zero** `logical_query_return` events. The three selected confirmed-value pairs have equal `g_ConfigBytes` and equal full 344-byte `TitleConfigWork` payloads:

- BGM: `2d50503001000000`, work SHA-256 `d3ac205f51288d698c195cf0efd311ff770a22cd55b7891d686d0131b83c651b`.
- SE: `2d46502801000000`, work SHA-256 `efdc6cf432f7c6a347850730311f06faf3d366f96179fde865b07b28c2d3b4b2`.
- Voice: `2d46462801000000`, work SHA-256 `c89e93b781d174058c91840af9baee8f32ffd9021c9349f251894e0f36afe214`.
- Both restart snapshots: `3250503000000000`, work SHA-256 `593ff4c07e20a72f9e735be7dd3af702622b4ea40703f676a219f20b0463dcc4`.

These are exact state comparisons at selected snapshots. The labels and action correspondence rely on `manual-action-notes.md`: the user reports opening/re-entering Audio Settings, canceling with B, confirming with A, testing Min/Max, and observing reset after restart. That file is human-only behavior evidence. It is not a machine input trace. The original/patched counts differ, and no ordered query inputs/results or action-to-snapshot timing is captured.

## Six H2 criteria against run-005

| # | Acceptance criterion | Evidence and remaining gap |
|---|---|---|
| 1 | Open Audio Settings; execute initializer/callbacks; relate the three visible options to config bytes; return to title state 5. | Partial/manual. Notes report the screen opened and stayed stable; machine snapshots contain config/work state. Run-005 does not record the complete entry/callback/return sequence or prove the visible-option mapping. Earlier H0/H1 evidence covers a bounded entry/cancel route, not this complete paired scenario. |
| 2 | Move every option in both directions and test observed endpoints. | Partial/manual. Confirmed BGM/SE/Voice states are machine-recorded and paired exactly. Min/Max clamping is only in the operator notes; there is no captured per-direction input sequence or endpoint state trace. |
| 3 | Cancel without changes and after a change; compare config, selection and transition; repeat entry/exit. | Partial/manual. The notes report B cancellation and restored BGM value/sound. The JSONL has no cancel input/query event or event-linked selection/transition evidence, so it cannot independently attribute a snapshot to that branch. |
| 4 | Confirm a change; compare config and stored data; re-enter; restart to test persistence. | Partial. Confirmed-value config/work bytes and post-restart reset bytes are machine-recorded and equal. A-retention/re-entry and visible reset are user-reported; persisted storage bytes and a machine-linked re-entry/action trace are absent. |
| 5 | Differential tests for reconstructed functions and caller composition, including boundaries/negative controls and domain limits. | Substantial bounded offline evidence in the cited integration/gap reports (callbacks, mapper cases, FillPair/CopyPair, State-9/10 composition), but not a whole runtime proof. Original/HLE service dependencies and unverified input/scheduler behavior remain explicit. This audit did not rerun tests. |
| 6 | Same input journey in original and patched Azahar, capturing inputs, config bytes and persistence result. | **Open.** There are zero logical query events, no machine-recorded common action sequence, unequal snapshot counts, manual action labels, and unresolved process-to-binary provenance. Run-005 is partial state-snapshot evidence only. |

## Smallest next evidence

Capture one paired original/patched run with a single explicit input source (for example a recorded CTM or an equivalent event stream) and an observer that assigns ordered IDs/timestamps to each action or logical query input and return value, alongside the existing config/work snapshots. Record each process's actual executable path and SHA-256, exact argv/working directory, CCI hash, isolated profile identity, exit/terminal record, and a post-restart state checkpoint. To close criterion 4's storage clause, include a before/after hash or byte comparison of the relevant setting storage within the disposable profiles. Then independently compare the paired event traces and state checkpoints. Do not treat the present manual notes or a successful boot as satisfying criterion 6.

## Commands and limitations

Read-only commands used: PowerShell packet/file inspection; `git diff --unified=3 -- src/engine/leaf_batch32_b.cpp src/engine/leaf_batch32_c.cpp src/engine/leaf_matching.cpp`; `rg` on the assigned reports; and `python -B build/agent-work/H2-semantic/h2-current-h2-runtime-provenance-audit/run-001/checks/audit_readonly.py` (exit 0), which recomputed the 35 packet hashes, parsed ELF32 symbols, compared object bytes with the final image, and counted JSONL events. `python tools/agent_workflow.py --help` also exited 0. The coordinator-supplied `function-body-comparison.json` was read-only inspected and its SHA-256 verified; that separate handoff records three one-job `build_check.py` runs and the comparison command as exit 0. This audit itself ran no tests, build, emulator, or debugger. The audit parser only reads declared artifacts and the coordinator-supplied body report, and writes its summary under this task output root.