# Independent review: H2 slider boundary and restart probe

## Finding

**Accept the report as a correctly bounded partial result; keep H2 open.** The offline artifacts and their hashes are consistent, the RSP runner selects the three rows and limits readiness polling, and the runtime attempts never produced a paired patched execution or a restart snapshot. The report does not claim persistence or physical-input equivalence.

Two runtime details need to remain qualified in any downstream summary. The saved logs for runs 003 and 004 contain 39 complete zero `r0` replies at the readiness return, with the log cut off during the final recorded RSP exchange; run 005 contains 40 complete zero replies. Run 002's claim that one additional `TitleConfig_IsReady` call returned zero is not independently visible in its saved log: that file ends after the readiness breakpoint is installed, without a continue, return-register read, or `r0` response. The live runner may have observed those outcomes, but it did not write a JSON run report before failing, so these details are not fully recoverable from the preserved logs.

## Offline evidence and artifact checks

I recomputed the report hashes in the copied run-003 packet. They match the report and the original run-001 artifact identities:

| Evidence | SHA-256 | Review |
|---|---|---|
| H2 image differential report | `cbf1ec48ef8f0ec905eac84e9f6cc137db5732fb9e4ec77692d47eebb6844b98` | Hash matches; the report has no single aggregate `passed` field. Component counts are all passed: Draw 46/46, Calc 16/16, Secondary 34/34, initializer 10/10, ready gate 4/4; each mapper 512/512; FillPair 4,096/4,096. It records `runtime: not_run`. |
| H2 State-9/10 caller | `68c537ef193911f4df52d76657bf093593c9c857a9c982d59ab825aaf89e8c2f` | Hash matches; `passed=true`, 3/3 cases and wrong-callback negative control detected. |
| H3 title caller | `6137060591382cd87b5af20faa2bdb895c462b7b8ddd8e1aae521852d6bf0f6c` | Hash matches; `passed=true`, wrong-next-state negative control detected. |
| H2+H3 final image | `81c1c6ae72d88b689cde3e9982439c8f8c4a6e8773887547f4cb85b86cd34a20` | Hash matches; 3,633,152 bytes. |
| H3 composition IPS | `95846920df9ceb0e6395b6fb7e5358c99b83dd14e5861ffcfa80d8e64208eda5` | Hash matches; independently applied to the pinned H2 final image and reproduced the H2+H3 image byte-for-byte. |
| Expanded RSP runner | `c9d37b76a8f3edfe56d8dc0a6706ea0c2cf2461d491d814cc9737fb994fad8b3` | Hash matches the report; source inspection confirms the bounded 40-call readiness poll and original row helper call. |

The H2 differential report records four current-source identity mismatches, all independently consistent with the actual source-file hashes:

| Entry | Expected source hash | Current/observed source hash |
|---|---|---|
| Mapper `0x0021F39C`, `leaf_batch32_b.cpp` | `dd9dac02bd19c27dd0fdfc9897229757bfc71f68a3e7fb4532ac781c873f325c` | `882993acbf47d181b3881cec61d26731ebc3a72737eee804f6b7a897cbde710e` |
| Mapper `0x002CAB70`, `leaf_batch32_c.cpp` | `9baf88cee24f0b53c2d330171c194d5795132907b77db0396cc29842fe3743de` | `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa` |
| Mapper `0x002E0AF4`, `leaf_batch32_c.cpp` | `9baf88cee24f0b53c2d330171c194d5795132907b77db0396cc29842fe3743de` | `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa` |
| FillPair `camp_func_0027edf8`, `leaf_matching.cpp` | `b5e511d0bae599ac38a13b6df68918444c00aece51ebcb760e0817897c18adf8` | `90238ffc67607cdb8578d1ce65aa6370389deb527423d3b0b278e43f6f621da2` |

Thus the case counts support the pinned integrated image and declared test domains, while the source identity warnings correctly prevent claiming the current whole source files are the exact producers of that image. The report’s narrowed count summary matches the JSON; it no longer states a 54/54 Calc tick result that this aggregate JSON does not expose.

## Runtime log identity and observed outcomes

All five runtime logs copied under `build/agent-work/H2-semantic/h2-rsp-slider-boundaries-restart/003/runtime-logs/` match the reported SHA-256 and sizes:

| Attempt | Bytes | SHA-256 | RSP evidence from the preserved log |
|---|---:|---|---|
| run001 | 516,996 | `7cc0aadf406894fe90bf8ea6bbae4340453f9b398884b5ccabfbfa67450384c4` | Contains a final TitleConfig work dump with state 2 and BGM/SE/Voice work values 7/7/7, plus config bytes `2d46462800000000`. It records the pre-confirm readiness/reset path, but no completed post-confirm readiness return. Its tail is cut during a log line. |
| run002 | 516,997 | `fe6b6855ae45b9d547bb533da5e7f09a75bec624b6c88f5c74d16463bb5f6382` | Contains the same state-2/value dump and readiness breakpoint installation, then ends mid-line. It contains no `p00` return-register query, so the reported additional readiness result of zero is not independently verified by this log. |
| run003 | 652,165 | `5b74f3c40e8285492e189d46bcbac75d58c3a543ecca52c71610ac31a52fd56d` | 41 readiness-entry stops (one earlier readiness entry plus the 40-poll sequence), 39 complete `p00` responses of zero, and 39 complete reads of work state 2. The file ends mid-GDB log line during the final poll. |
| run004 | 652,165 | `663fa53428fc8c173804c779ccf5c650266e9048cbb0c34ccfe185f04635252f` | Same persisted poll evidence as run003: 41 readiness-entry stops, 39 complete zero return reads, and 39 state-2 reads. The log ends during a final memory exchange; the recorded contents do not serialize the `WM_CLOSE` API return or `wait()` result. |
| run005 | 654,505 | `3951e2d66891305e0b7dfa89e11bde8e38c69f4f1b9a343d87d9ea3d34c02696` | 41 readiness-entry stops, 40 complete zero return reads and 40 state-2 reads. The log shows RSP continue at 43.116 s and a connection reset at 58.129 s, consistent with the reported 15-second close timeout followed by runner termination. |

The runner source supports the intended test mechanics: it calls `UiListCursor_SetSelectedRow`, installs the deterministic logical-query response for a frame, checks work fields, polls the original readiness function at most 40 times, and performs the patched run only after the original scenario returns. Because the first side raises on the no-ready/close path, the final paired comparison and JSON report are never written; the handoff’s nonzero run exits are consistent with that control flow. This means the report’s live assertions are plausible, but action-level runtime evidence is not retained as a standalone trace. The four/forty-call statements should be described as live-run observations with the persistence limits above, rather than as fully reproducible from the copied logs.

The report and handoff say the initial C: staging failure preceded the E: runtime attempts; the C: staging attempt has no separate artifact in this review packet, so that disk-space event remains reported context rather than independently verifiable runtime evidence. The E: logs do show launched Azahar/RSP activity for runs 001–005.

## Save, process, and port checks

The current `E:\emulador3ds\sdds4game1.sav` is 151,088 bytes and hashes to `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`, matching the report’s recorded expected identity. The runner uses a staged CCI and disposable profile seed and has no reference to this user save path. That supports the claim that the save was not staged by the runner; it does not provide an on-run before/after snapshot.

At review time, no `azahar` process was present and `netstat` showed no TCP listener matching ports 60944–60953. This confirms no current leftover process/listener; the run005 RSP disconnect and the inspected `proc.terminate()`/kill fallback support the reported cleanup path. The saved runtime files do not establish that the attempted `WM_CLOSE` was processed as a clean Azahar shutdown; the report accurately says it did not exit cleanly within the timeout.

## Recommendation and limits

The conclusion that H2 remains open is correct. This run provides original-side scripted logical-condition observations, bounded offline checks, and no evidence of physical controller mapping, scheduler timing, paired patched-runtime equivalence, same-session post-confirm re-entry, or settings persistence after process restart. Keep the current source/image mismatch and the incomplete RSP-log tail visible in the provenance record. The next action proposed in the report—inspect the original State-2 script/task lifecycle and establish a bounded clean shutdown before retrying persistence—is consistent with the available evidence. No guest state/config force-write or guessed persistence call should be inferred from this review.

## Review method

Read-only review of the updated report, task packet, handoff, offline reports, final image/IPS, current RSP runner/source, copied Azahar logs, current save hash, process list, and port table. I recomputed the stated artifact hashes, checked H3 IPS application in memory, parsed the persisted RSP request/response records and counts, and inspected the runner’s readiness/close flow. No build, test, emulator, debugger, profile, save, runner, board, or milestone change was made. The C: staging attempt and missing run JSON remain the evidence gaps described above.
