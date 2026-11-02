# H2 cumulative cursor runtime — run001

## Result

The reviewed cumulative image was compared with the pinned original in the autonomous TitleConfig scenario using the private loopback-bound Azahar build, disposable original/patched profiles, and GDB ports `127.0.0.1:60340` / `:60341`. The original-based IPS was generated from the pinned original and replayed byte-for-byte to the cumulative image before launch.

| Evidence | Result |
|---|---:|
| Original code SHA-256 | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Cumulative image SHA-256 | `aca919c95b0bc58af0a50b9f9f7f7d22084c2eb1dba5767889258920b08c582f` |
| Original-based IPS SHA-256 | `c4c4667fa564b846830b01a6b2226b480f1e99a5e3785b7c4ca89c95eeec643c` |
| Original-based IPS records / changed bytes | 822 / 6,397 |
| Scripted actions | 51/51 matched |
| State checkpoints | 19/19 matched |
| Readiness | did not complete on either side; outcomes matched |
| Same-session reentry | did not complete on either side |
| Clean shutdowns | original and patched both exited cleanly |
| Profile seed / runtime assets / private emulator | unchanged |

The final paired runner report says `passed: true` for the defined scripted scenario, with matching action traces, checkpoints, lifecycle outcomes and restart observations. `full_controlled_lifecycle_completed` is false: the readiness gate did not complete in either profile, so the report does not establish successful title return, same-session reentry, or persistence after a confirmed setting change. It is bounded runtime evidence, not full H2 acceptance.

The first attempt used the long repository output path and exited before GDB readiness with Windows status `0xC000001D`; it produced no guest evidence. The paired run then completed from the short staging root `C:\h2rt-cumulative-run001`. The initial wrapper had a post-run path-reporting exception after the autonomous runner had completed. The wrapper was corrected to accept an external short root and summarize an existing run without relaunch; the saved report and image/IPS artifacts are in the task output directory.

## Reproduction

```powershell
python tools/h2_cursor_cumulative_runtime.py --output-dir C:/h2rt-cumulative-run002
```

The short output path avoids overly long staged portable-profile paths. To summarize a completed run without launching Azahar again:

```powershell
python tools/h2_cursor_cumulative_runtime.py --summarize-existing C:/h2rt-cumulative-run001 --report-dir build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-runtime/run001
```

The autonomous report, original-based IPS, and cumulative binary are retained under the task's ignored `build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-runtime/run001/` output. The detailed GDB report SHA-256 is `d0aa7b2419a93c9c793ab86032e306e7fdb746d5f39676dba80f94365d4f69bc`.

## Limits

The scripted GDB driver replaces the logical query with deterministic one-frame stubs. It does not capture every nested axis-reader output write and cannot prove that live H2 avoids the `0x0027FBC8` no-write domain. It also does not prove physical input mapping or natural scheduling. The readiness/reentry stall remains identical to the original and patched runs; the H2 milestone remains open. This is not whole-game equivalence.
