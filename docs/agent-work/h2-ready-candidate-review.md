# Independent review: `TitleConfig_IsReady` candidate

## Review result

**Disposition:** accept the bounded experimental predicate reconstruction and isolated ARM differential. This review does not approve production promotion, title caller composition, or H2 runtime equivalence.

## Contract and source checks

- The pinned 52-byte body at `0x002FC0EC` loads `g_TitleConfigWork` from `0x0044E2D0`. A null work pointer reaches `r0 = 1`. Otherwise it loads the first word at `work+0`, calls `0x002BF41C`, and returns `0` when that lookup is nonzero or `1` when it is zero.
- `TitleConfigWork::calc_task` is at offset zero and the declared structure size is `0x158`; these agree with the initializer contract and candidate's narrow workspace view.
- The checked-in helper body for `0x002BF41C` is a task-record lookup: it returns one when a matching task handle is found and zero after exhausting the list. A null task handle is still forwarded. Whether null could match a malformed task record is an input-state question; the candidate correctly delegates that condition to the helper.
- The title caller enters state 10 after dispatching the title-config initializer. It remains there while `TitleConfig_IsReady()` returns zero and calls `Title_ResetForBoot` after a nonzero result. The candidate's boolean result therefore agrees with this caller's gate.

## Candidate and differential

`experiments/semantic_equivalence/h2_ready_candidate.cpp` expresses that predicate directly and keeps `0x002BF41C` as an explicit original helper dependency. The runner rejects object relocations, maps the pinned configured image, intercepts the helper identically for original and candidate, and compares return value, return PC, helper trace, and each execution's SP/r4 preservation.

The stored ARM differential covers null global, registered task, unregistered task, and null task-handle forwarding: 4/4 pass. The intentionally always-ready control is detected on the registered-task case. I independently ran `python -m unittest tests.test_h2_ready_experiment -v`; all five focused tests passed.

## Follow-up and evidence limits

- The synthetic `WORK` address is `0x00410000`, which lies inside the mapped `code.bin` range (`0x00100000..0x00477000`). The fixture overwrites that image location with a synthetic task handle. The tested callback reads only the supplied work pointer and the helper boundary, so this does not reveal a predicate mismatch in the current matrix, but a separate writable fixture mapping would avoid accidental image-data collisions before expanding into helper or caller composition.
- The helper is mocked, not executed as part of both callback runs. Its body was separately inspected, but the differential does not test task-list mutation, concurrency, or malformed list state.
- The ABI checks explicitly cover SP and r4. The function body only saves r4 and LR, and the candidate has no floating-point operation; adding checks for the full callee-saved register set would strengthen future integration tests.
- The state-10 caller evidence is static. No title caller sequence, scheduler lifecycle, Azahar run, user input, configuration persistence, or restart behavior was exercised.
- Production source and the ledger remain unchanged. Any eventual production byte-different implementation must use a truthful non-matching ledger classification and must be reviewed with the integrated caller/runtime evidence required by H2.

No blocking defect was found in the bounded candidate. Before integrating it into a wider test, move the synthetic work fixture outside the mapped image and compose it with the actual state-10 caller and task-helper behavior.
