# Independent review: paired H2 live-observer runtime evidence

## Decision

**Accept the bounded state-snapshot evidence as partial runtime evidence. H2 criterion 6 remains open.** The captures show exact matching guest state at three selected confirmed-change snapshots and after restart. They do not record the input/query trace needed to establish that the original and patched runs received identical actions in the same order and at corresponding times. This review does not change milestone status or establish whole-game equivalence.

## Independent recomputation

The declared comparison script selects original snapshots 4/5/6 against patched snapshots 1/2/3. I independently parsed the four frozen JSONL files, recomputed their SHA-256 values, checked terminal rows and record counts, and compared the selected config bytes and complete 344-byte `TitleConfigWork` payloads. Results:

| Capture | SHA-256 | Snapshots | Terminal |
|---|---|---:|---|
| original live | `696f234673e68732756c09ab2d94dfa6f60c9cc7e66175305edc64723e1252c5` | 7 | `complete`, total_records 7 |
| patched live | `344bdcb74959c5ba4383ee26389d19c99cda7c814d71993e6e0c380002af590f` | 4 | `complete`, total_records 4 |
| original restart | `343450b704020ef2718e98ca26ce3f8b0ce7ea3e4769acd83508d9e5ca8a1ce7` | 1 | `complete`, total_records 1 |
| patched restart | `2a8ea14c9ca1464b6043f2a9dcf1ccd642835dbdc321947b32bf9f0bb5a73d6f` | 1 | `complete`, total_records 1 |

All four contain zero `logical_query_return` events. The three selected live pairs are byte-equal:

| Reported action | Original / patched seq | `g_ConfigBytes` | 344-byte work blob SHA-256 |
|---|---|---|---|
| BGM confirmed | 4 / 1 | `2d50503001000000` | `d3ac205f51288d698c195cf0efd311ff770a22cd55b7891d686d0131b83c651b` |
| SE confirmed | 5 / 2 | `2d46502801000000` | `efdc6cf432f7c6a347850730311f06faf3d366f96179fde865b07b28c2d3b4b2` |
| Voice confirmed | 6 / 3 | `2d46462801000000` | `c89e93b781d174058c91840af9baee8f32ffd9021c9349f251894e0f36afe214` |

Both restart snapshots have `g_ConfigBytes=3250503000000000`, and both full work blobs hash to `593ff4c07e20a72f9e735be7dd3af702622b4ea40703f676a219f20b0463dcc4`. These are exact state comparisons; the selected action labels are based on the operator notes, not machine-recorded event IDs.

## Artifact and stage provenance

I rehashed the current composed artifact chain. Original `extracted/exefs/code.bin` is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; composed image `code.h2-final.bin` is `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`; standalone IPS is `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`; composition manifest is `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`. The manifest describes 533 records and 4,218 changed bytes. These agree with the runtime report and both stage snapshots.

Run-008 stage snapshot SHA-256 is `e3b39dd0cf910b0ffc6b5357af1a6d6a56c57ae9ac6d8f7f0279e47c1744f3b6`; run-009 is `f7682e4b469c3cc53a33e893c9656c5234b5368a77986b3f25af25ebae54cba1`. The saved stage records agree on the original image, final image, composition manifest, IPS, CCI SHA `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`, identical pristine seed hashes, and `profiles_differ_only_by_ips=true`. Original and patched profile snapshots carry hashes `b7349a12e4557a5fb6d4778462f6f9a5e7ca91315a2a0bbe24036fda1ae67101` and `14a9c7afb21cf3dfaebe39757cc83abb459ab2487f0fb6f753f2582b7e1f4587`; their listed difference is the intended IPS. Both stage records say GDB and RPC are disabled. Run-009 was a fresh patched stage after the original stage had been used, which supports profile isolation.

There is a process-to-binary lineage gap: both stage manifests and their command-output summaries identify the staged Azahar executable as SHA-256 `c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`, while the separate private delivery manifest pins `build-clang64/bin/Release/azahar.exe` at `e9eaa321899a796c17e9460cf8b4a7e003e2606712f1fcc8f1fb485d8f5f406d`. The runtime report cites the latter as the final private executable, but exact wrapper/restart invocation lines and a process-path/hash record are absent. The saved evidence therefore does not reconcile which executable image was loaded for each PID. I treat this as unresolved provenance, not proof that the wrong binary ran.

The JSONL terminal records establish that each observer capture ended cleanly and its stated record count matches. The saved report notes wrapper exits 0 and normal restart closure, but exact shell invocation records are not present. A stage manifest is staging metadata, not by itself proof of the process image loaded at runtime.

## Manual observations versus machine evidence

Operator notes report that B cancels a BGM notch and restores prior sound/value, A confirms changes that remain visible on re-entry, all sliders clamp at Min/Max, and restart returns the three settings to initial values. The JSONL files do not encode those key actions, their logical query inputs/results, ordering, or timing. Snapshot counts differ (7 versus 4), and the changed-state pairing is anchored by human-described sequence and selected record indices. The matching restart bytes and confirmed-value snapshots are strong bounded observations, but they cannot substitute for the absent input/query trace. Cancel and endpoint behavior remain human-reported.

## Smallest next action

Capture one paired original/patched run using the same explicit input sequence and an observer that records each logical query input and return value (or a user-recorded CTM plus an event trace), with ordered event IDs/timestamps and the existing state snapshots. Preserve the loaded executable path/hash and exact invocation per process, verify both runs use the pinned CCI and isolated staged profiles, and include complete terminal records. Then compare the action/query traces and state checkpoints. Until that capture exists and is reviewed, criterion 6 remains open.

## Review scope

Read-only review of the prepared task inputs and frozen runtime artifacts. No emulator, UI, debugger, RPC, profile mutation, build, or test was run. The comparison was independently recomputed inline; the original comparison script was not rerun because it writes its comparison output.
