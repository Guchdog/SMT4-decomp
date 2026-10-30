# H2 State-2 dispatch runtime — run-001 failure and run-017 capture

> **Status correction:** The original sections below preserve the initial `run-001` launch failure only. They are historical, not the latest status. Later `run-017` reached Audio Settings and captured the original State-2 dispatcher. Its independent review is [here](h2-state2-dispatch-runtime-capture-review.md). H2 remains open.

## Result

The assigned original-only diagnostic was attempted exactly once, after all pinned offline gates passed. Azahar exited before creating its loopback GDB listener, so the runner never connected RSP and collected no guest trace (`trace: {}`). The recorded Windows process status is `3221225781` (`0xC0000135`, `STATUS_DLL_NOT_FOUND`). This is a launch failure, not evidence about State-2 dispatch, readiness, or persistence. No retry was made.

The exact launch command was:

```text
python tools/h2_state2_dispatch_trace.py --run-dir build/agent-work/H2-semantic/h2-state2-dispatch-runtime-capture/001/runtime-original-001 --output build/agent-work/H2-semantic/h2-state2-dispatch-runtime-capture/001/runtime-report.json --port 46781 --startup-timeout 90 --packet-timeout 30 --capture-timeout 180
```

The runner invoked one staged process (host PID 17712) with `azahar.exe -g 46781 <pinned CCI>`. The child exited before listener readiness. The process was no longer present afterward and port 46781 had no listener; no RSP packet was sent. `clean_close_observed` is false, accurately reflecting that no graceful close was observed. The runner removed its disposable staged user profile. Its only staged profile files were the two approved seed files; both seed sources remained unchanged. The staged runtime directory and stdout/stderr logs are retained as run evidence.

## Offline gates and identity

The runner's prelaunch record reports all task input hashes, pinned H2 differential, H2 caller, H3 final-image caller, and ARM interworking checks passed. Original branch targets were `0x1EA348 → 0x30A9A4` and `0x1EA3B4 → 0x2F4CA0`, both with low bit clear. The four existing H2 differential source-identity warnings are recorded verbatim in the runtime JSON; they concern three mapper source entries and one fill source entry and are not silently waived by this failed launch.

Pinned report hashes:

- H2 differential: `cbf1ec48ef8f0ec905eac84e9f6cc137db5732fb9e4ec77692d47eebb6844b98`
- H2 caller: `68c537ef193911f4df52d76657bf093593c9c857a9c982d59ab825aaf89e8c2f`
- H3 final-image caller: `6137060591382cd87b5af20faa2bdb895c462b7b8ddd8e1aae521852d6bf0f6c`

The verified private Azahar executable SHA-256 was `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`; the staged copy has the same hash. The original CCI was hash-read before and after as `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`. The supplied save `E:\emulador3ds\sdds4game1.sav` was hash-read before and after as `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; it was not staged or loaded. Both inputs are recorded unchanged.

## Launch dependency diagnosis

The staged app directory contained only `azahar.exe` after the runner removed its disposable `user` directory. The pinned executable's source `build-clang64/bin/Release` directory likewise contained `azahar.exe`, `user`, and a diagnostic IPS file, but no sibling DLLs, `plugins` directory, or `qt.conf`. The runner's staging routine copies sibling DLLs, `plugins`, and `qt.conf` when present, but there were none to copy. The existing H2 probe uses the same sibling-runtime convention and additionally copies pinned package assets when present; the recorded stage has no deployment bundle alongside this executable.

`0xC0000135` establishes that Windows could not resolve a required DLL, but this record does not identify which DLL. Do not infer a specific missing library from the status alone. The safe unblock is to locate a deployment bundle tied to this exact pinned build, record and verify its provenance/hashes, then stage its required DLLs and plugin/config assets alongside the executable using the existing H2 staging convention. The coordinator reports that the existing H2 packaging path obtains its runtime DLL set from the Azahar distribution under `E:\emulador3ds` (including Qt, ICU, and OpenAL libraries). That is the concrete candidate source to inspect and pin against the exact executable, not permission to copy an unverified subset. Verify the needed dependency closure and hashes from that distribution, then stage it using the existing helper convention. If that pinned inventory cannot be established, produce a separate preparation task first. Do not copy arbitrary DLLs from the host. This packet authorizes no second launch.

## Scope of run-001

No title state was entered or changed, and no dispatcher, handler, Calc branch, Secondary path, or readiness result was observed in `run-001`. Its packet did not authorize a retry. A later fresh run used a separately pinned runtime package and reached the guest; see the run-017 section below. Do not generalize the run-001 no-trace result to the later attempts.

## Artifacts

- Runner: `tools/h2_state2_dispatch_trace.py` (SHA-256 `284c21bb0318a9df2adbe1c1052a71a3789cb3c4f221031a3f0d785be0b51e78`)
- Offline-gate record: `build/agent-work/H2-semantic/h2-state2-dispatch-runtime-capture/001/offline-gates.json` (SHA-256 `2aecc5c444efda0335e6c907de29f56d38092caf892d18d116c884da5214b3e7`)
- Runtime record: `build/agent-work/H2-semantic/h2-state2-dispatch-runtime-capture/001/runtime-report.json` (SHA-256 `261398eeb37cadc4a28d04ee4d32f74d763a9c63982dff2b8d1e692021d5f485`)

## Latest reviewed capture — run-017

`run-017` launched the pinned private executable once with a disposable original profile and the 59-file runtime package. Offline H2 differential, H2 caller, H3 final-image caller, and ARM interworking gates passed. Four source-identity warnings in the H2 differential remain recorded; they were not waived. The loopback listener was observed at `127.0.0.1:46797`, owned by the same PID as the staged child. All staged runtime-asset hashes matched their pin. The child was terminated by the supervisor after the bounded capture; clean shutdown was not observed.

The original title callback path reached `TitleConfig_Init` (`0x002F4CA0`) through State 5 with selection 2 and a controlled logical A-confirm query. The work moved from Calc State 1 to State 2. For one task (`0x08C0AA80`, method table `0x086E5AD0`), the trace recorded:

| Instruction index | Handler | Target | Return | Task counters at entry |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 7 | `0x001A08A8` | 1 | `+0xCC/+0xD0 = 0/0` |
| 11 | 29 | `0x001C1D2C` | 1 | `0/0` |
| 12 | 8, ten calls | `0x001A07CC` | 2 each | `0/0` through `9/9` |

Each of ten Calc dispatch returns had `r0=1` with State 2 unchanged. Each readiness cycle recorded task-activity return 1 and outer ready result 0. No Calc follow-up or Secondary entry/exit was observed. The run timed out after 12 handler returns and ten readiness cycles. This demonstrates a still-active task and a repeated pending top-level callback in that sample; it does not establish a deadlock.

The wrapper at `0x001A07CC` invokes a nested function through `BLX r0`. `run-017` did not record that nested callback ID, target, or raw return. That is the next bounded observation: resolve the method's nested ID and function pointer, then record the call at `0x001A07FC` and return at `0x001A0800` without modifying guest state.

The runtime report records the game CCI unchanged (`9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`) and the supplied save unchanged (`6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`), not staged or loaded. Only a hash-pinned disposable copy was staged. The run packet pins the runtime-package document and other listed inputs, but **does not pin the runner source hash or invocation arguments**; this limits exact reproducibility. The independent review recommends a fresh packet for the nested-callback probe and requires its output to bind the runner hash.

Evidence: task packet SHA-256 `5c8bc300f0a75eb0ccc8355acd811189172eed6a0e36e7b84f56bbc1c3e69d4a`; runtime report/console JSON SHA-256 `9976f6f643dfb9ef08e084cd2d6a92bfebbb7e1826dde761a122810e6aade4a4`; package pin SHA-256 `bda8e1a43ac9e040e4a8165f1a9eec5a3656ff94d59d85cb50577959815428f9`; independent review SHA-256 `1c0592f4f732bcf0b9879ab9374174c16d36dda32dd3bdba79d80f5bbd249d53`.

H2 remains open. This is original-only evidence with scripted logical queries; it does not establish physical-input parity, the nested callback's contract, a patched-side comparison, completion, clean restart, persistence, or whole-game equivalence.

