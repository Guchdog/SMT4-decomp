# H2 slider boundary and restart probe — partial result

Date: 2026-10-29  
Checkout: semantic worktree on `codex/semantic-equivalence-experiment`  
Status: **partial; H2 remains open**

## Result

The offline gates passed for the pinned integrated images, and the expanded RSP
runner's original-side execution reached A-confirm after exercising BGM, SE, and
Voice minimum/maximum sequences. On that side, the runner selected each row through the original
`UiListCursor_SetSelectedRow` helper and recorded the selected work field,
all three work values, normalized work hash, and all eight `g_ConfigBytes` after
each logical input frame in its live assertions. The process failed before the
runner could write a JSON report, and the patched process was never launched;
there is no paired trace comparison for this boundary batch.

The run reached A-confirm and `TitleConfigWork.state == 2`. Run 003's terminal
exception reported `TitleConfig_IsReady` returning `0` on its 40th bounded poll;
the saved log preserves only 39 complete replies for that run. Run 005's log
preserves 40 complete zero replies. The task remained registered in the observed
state, so the title did not return to state 5 and same-session
re-entry did not occur. A clean close request also failed to exit Azahar within
15 seconds, including a retry that resumed the guest before posting `WM_CLOSE`.
The runner terminated only its staged child process. It did not reach a restart
snapshot, and the patched profile was staged but never launched because each
paired run stopped on the original side. Therefore this probe proves neither
same-session post-confirm re-entry nor restart persistence, and it is not a
paired original-versus-patched result.

## Offline gates and artifact identities

| Check | Result | Evidence |
| --- | --- | --- |
| H2 integrated image differential | 46/46 Draw, 16/16 Calc sequences, 34/34 Secondary, 10/10 initializer, 4/4 ready; 512/512 cases for each mapper; 4,096/4,096 FillPair cases | `build/agent-work/H2-semantic/h2-rsp-slider-boundaries-restart/run-001/checks/h2-differential/report.json`, SHA-256 `cbf1ec48ef8f0ec905eac84e9f6cc137db5732fb9e4ec77692d47eebb6844b98` |
| H2 State-9/10 caller | 3/3; wrong-callback negative control detected | `.../checks/h2-caller/report.json`, SHA-256 `68c537ef193911f4df52d76657bf093593c9c857a9c982d59ab825aaf89e8c2f` |
| H3 title caller | Passed; wrong-next-state control detected | `.../checks/h3-caller-002/report.json`, SHA-256 `6137060591382cd87b5af20faa2bdb895c462b7b8ddd8e1aae521852d6bf0f6c` |
| H2+H3 image | 3,633,152 bytes; IPS round-trip exact | `.../checks/h3-composite/code.h3-h2final.bin`, SHA-256 `81c1c6ae72d88b689cde3e9982439c8f8c4a6e8773887547f4cb85b86cd34a20`; IPS SHA-256 `95846920df9ceb0e6395b6fb7e5358c99b83dd14e5861ffcfa80d8e64208eda5` |
| Private Azahar | Pinned loopback build | SHA-256 `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a` |
| Game CCI | Pinned input | SHA-256 `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2` |
| Expanded RSP runner | Source syntax checked with `ast.parse` | SHA-256 `c9d37b76a8f3edfe56d8dc0a6706ea0c2cf2461d491d814cc9737fb994fad8b3` |

The H2 differential report also lists four source-identity mismatches in the
current checkout for the mapper and FillPair source files. Its case counts
passed against the pinned integrated image, but those mismatches remain a
provenance limitation for this fresh gate and must be reconciled before treating
the current source tree as the exact source of that image.

## Runtime attempts

The initial C: staging attempt failed before launch when the volume ran out of
space; only that attempt's own partial disposable staging directory was
removed. Runtime output is under the separate ignored build directory
`E:\SMT4decomp\build\h0-h3-closure-20261028\` because the semantic checkout's
C: volume was full during that staging attempt. Each process used the
private Azahar executable, loopback RSP, and disposable original/patched
profiles. No keyboard or mouse was used. The patched profile was staged in the
paired output directories, but no patched process started because every runtime
attempt stopped on the original side.

| Run | Outcome |
| --- | --- |
| `h2-rsp-boundaries-restart-run001` | Reached A-confirm, then timed out waiting for `Title_ResetForBoot`; child was terminated by the runner. Log SHA-256 `7cc0aadf406894fe90bf8ea6bbae4340453f9b398884b5ccabfbfa67450384c4`. |
| `h2-rsp-boundaries-restart-run002` | Timed out waiting for `Title_ResetForBoot` after installing the readiness breakpoint. The saved log ends before a readiness return or `r0` read, so no return value is claimed for this run. Log SHA-256 `fe6b6855ae45b9d547bb533da5e7f09a75bec624b6c88f5c74d16463bb5f6382`. |
| `h2-rsp-boundaries-restart-run003` | The runner's terminal exception reported reaching poll frame 40 with `ready_return=0` and state 2. The preserved RSP log contains 39 complete zero-return replies; its last exchange is truncated. Log SHA-256 `5b74f3c40e8285492e189d46bcbac75d58c3a543ecca52c71610ac31a52fd56d`. |
| `h2-rsp-boundaries-restart-run004` | Readiness remained incomplete; `WM_CLOSE` reached one visible window but the child did not exit within 15 seconds. The preserved RSP log contains 39 complete zero-return replies and a truncated final exchange. Log SHA-256 `663fa53428fc8c173804c779ccf5c650266e9048cbb0c34ccfe185f04635252f`. |
| `h2-rsp-boundaries-restart-run005` | The preserved log contains 40 complete readiness replies with `r0=0`. Sending RSP continue before `WM_CLOSE` still did not close the child within 15 seconds. Log SHA-256 `3951e2d66891305e0b7dfa89e11bde8e38c69f4f1b9a343d87d9ea3d34c02696`. |

The independent [review](h2-rsp-slider-boundaries-restart-review.md) confirmed
the report hashes and these limits. It also found that runs 003 and 004 preserve
only 39 complete zero-return replies in their logs, while run 005 preserves 40;
run 002 has no recorded readiness return. The terminal exception from run 003
reported its 40th call, but that final exchange is not fully present in the log.

The only persistent-save input mentioned by the user was never staged or read by
the runner. `E:\emulador3ds\sdds4game1.sav` remains 151,088 bytes with SHA-256
`6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. After
the runs there was no Azahar process and no listener on ports 60944–60953.

## Next work

Resolve the original State-2 progression through its observed script-step and
task-lifecycle dependencies before another persistence attempt. In particular,
do not force the work state, edit `g_ConfigBytes`, or call a guessed persistence
service. Then establish a bounded clean-shutdown path that lets the emulator
process its close event while the guest is not held at an RSP breakpoint. Repeat
the original/patched sequence serially and retain both per-action traces and
restart snapshots. Until then, H2's physical input/scheduling and persistence
criteria remain open; H3 remains at its independently reviewed bounded scope,
and H4 stays paused by the user's instruction.
