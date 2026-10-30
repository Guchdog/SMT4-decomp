# H2 State-2 nested callback capture

**Status: in progress.** Runs 001–008 did not reach this task's nested
callback. Runs 004 and 006 used a 240-second startup bound. Run-004 spent that
window stopping at 3,967 calls from pre-title message-window callbacks; the
title object remained absent. Run-005 deferred query breakpoints, but its first
`continue` expired at the RSP socket's 30-second packet timeout. The runner now
bounds each `continue` by the remaining phase deadline while restoring the
shorter timeout for individual RSP packets. Run-006 applied the full bound but
stopped only at the pre-menu command and its return. Run-007 observed that
command's downstream resource-init return and control-word increment, then
expired its short startup bound before a title callback. The reviewed run-017
did reach State 2. This extension is locating startup progress; it is not a
replacement for the State-2 trace.

## Run-001: partial failure

Prepared packet:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-001/task.json`

Runtime report:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-001/runtime-report.json`

The runner launched the pinned private loopback Azahar build once and verified
that child PID `20616` owned listener `127.0.0.1:55499`. It recorded the
pre-menu boot-script callback at `0x0026FA94`, then intercepted 512 calls to
`UiInput_Trigger2(0x002BFFBC)` through the mode-1 dispatcher return at
`0x002C18E0`. Because `TitleMainWork` did not yet exist, the old generic path
replaced each helper with a temporary stub returning zero. The query bound then
failed before title initialization or State-2 capture. This is a runner-induced
input suppression, not evidence of a game stall or of the original helper's
return values.

The report records a single launch, supervisor termination, removed disposable
profile, cleared breakpoints, and no source save staging. The pinned disposable
save fixture was staged unchanged. The source CCI, supplied save, fixture, and
profile seed hashes are unchanged; 59 pinned Azahar runtime files were staged
with matching hashes. Run-001 runner SHA-256 was
`a13ffff0871f1a1d55642153934660e7ab4239cf8af559b60e80c5c295a1ebd4`, unchanged
during that run.

## Runner correction and gates

For the exact pre-title case `(TitleMainWork == null, address == 0x002BFFBC,
return PC == 0x002C18E0)`, the runner now lets the original mode-1 helper execute
unchanged. It records the real return value, input mode/counter reads, and the
dispatcher caller return saved by its verified four-register prologue. This
narrow path does not install a code stub or write guest state. Other callers
retain the existing controlled title-navigation behavior.

Run-002 used the pass-through path. All 512 original calls returned zero while
the mode word and corresponding counters were zero. The calls came from
`camp_func_0010edd4` at return PCs `0x0010EDFC`, `0x0010EF08`, and `0x0010EF70`,
and from `camp_func_0010efb4` at `0x0010EFC8`. Static inspection shows these are
callbacks registered by `ui_func_00102848`, which initializes the Info/Com/Guest
windows and the `MESS_D` dialog route. The run stopped because these passive
calls still consumed the shared 512-query cap. It did not demonstrate a game
stall or an input edge.

The runner now records these original helper results in a compact per-ID/caller
summary, excludes them from the title-input cap, and relies on the 90-second
startup timeout plus a separate 4096-call safety bound. The focused runner
tests cover nested method-table resolution, callback return cap accounting,
strict pass-through scoping, and summary aggregation. The offline H2
differential, H2 caller-composition, H3 final-image caller-composition, and
ARM/Thumb interworking gates pass. Four known source-identity warnings remain
explicitly recorded; they are not byte-match claims.

## Run-003: bounded startup timeout

Prepared packet:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-003/task.json`

Runtime report:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-003/runtime-report.json`

All offline gates passed and the private listener belonged to the staged
Azahar child. The original mode-1 helper ran 1,435 times before the 90-second
startup deadline; all recorded returns were zero with mode word and counters
zero. The title object remained absent, so there were no title navigation
queries, Calc entries, handlers, or nested callback events. The preserved log
ends around 91.864 seconds at debugger cleanup. The CCI, supplied save, source
fixture, profile seeds, and staged runtime hashes were recorded unchanged or
matching their pins. This is a startup timeout, not an H2 handler result or
evidence of a guest deadlock.

## Run-004: timeout with repeated pre-title stops

Prepared packet:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-004/task.json`

Runtime report:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-004/runtime-report.json`

All four offline gates passed, runner/task input hashes matched, the private
listener was owned by child PID `11500`, and cleanup removed the disposable
profile and cleared breakpoints. The original query helper returned zero for
3,967 pre-title calls; all captured mode words and counters were zero. The
calls were from the same three `camp_func_0010edd4` call sites and one
`camp_func_0010efb4` call site seen in run-002/003. No `TitleMainWork`, title
input, Calc handler, or nested callback was observed. The 240-second bound
expired; this does not establish a guest deadlock. CCI, supplied save, and
disposable fixture hashes matched before and after; the supplied save was not
staged. The Azahar log is preserved with SHA-256
`9f4da4c3ed93801f9978c203d9eb81d1a1de93ab6f5a8f6547c1699ec7b65792`.

## Run-005: transport timeout before the next guest stop

Prepared packet:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-005/task.json`

Runtime report:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-005/runtime-report.json`

The focused runner tests, pinned H2/H3 reports, and ARM interworking check
passed. The private listener was owned by staged child PID `20340`; the
permitted pre-menu safety guard at `0x0026FA94` returned `r0=128` for the
observed context. No title input or Calc breakpoints fired before RSP timed
out. The error was `TimeoutError: timed out` after the 30-second socket timeout
on a continue request, not the 240-second startup deadline. The supervisor
terminated the child, removed the disposable profile, and cleared all active
breakpoints. CCI, source save, disposable fixture, and seed hashes remained
unchanged. The log hash is
`841c6e7e854bef2e8574dd03718ce4f0bbcd83fcef8c2dd84a275553be2c48d0`
(1,160,580 bytes). This run does not establish whether title initialization
would have occurred later.

## Run-006: startup bound reached before title initialization

Prepared packet:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-006/task.json`

Runtime report:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-006/runtime-report.json`

The focused tests, pinned H2 differential and caller, H3 final-image caller,
and ARM/Thumb interworking checks passed before launch. The private loopback
listener belonged to the staged child. The disposable profile and its staged
save fixture were removed/preserved under the runner's cleanup; the fixture
hash remained `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`,
matching the source fixture. The supplied save was not staged. CCI, supplied
save, fixture, runtime-package pins, and profile seeds remained unchanged.
All active breakpoints were cleared. The preserved Azahar log is
`build/h2-runtime/h2-state2-nested-callback-capture/run-006/azahar-user.log`,
7,988,612 bytes, SHA-256
`5dd2d5f5067d9dc13ca2d36cef01165d44a101e60e519f4fcfc79ff890dc692d`.

The only guest stops were entry to `0x0026FA94` and its return at
`0x001C05A0`; the original callee returned `r0=128`. The context prefix read at
entry was `4c002000000000000b00000000000000...`. Do not label its `+0x08`
word as a FlowScript opcode index: `FlowScriptExecContext` documents `+0x08`
as `code_base`, while the observed native dispatcher increments a word at
`r4+0x08` after this command. The runtime pointer's type/field naming is
therefore unresolved here. No title initializer, title input, Calc handler, or
nested callback was observed. This is a bounded startup timeout, not a guest
deadlock result.

Static inspection resolves the next native calls after `0x001C05A0`:
`0x001C05A8` calls `script_vm_func_002c5810` (a tail branch to
`func_0010fa74`), then `0x001C05B4` calls
`engine_func_001a863c`, which starts a set of map/script resource loads and
returns at `0x001C05B8`. The dispatcher then increments `[r4,#8]` and loops.
Run-017 reached title initialization at about 3.19 seconds; run-006's log has
no guest stop after 2.875 seconds. The difference is actionable: observe these
native return points under a short bound to determine whether the execution
stalls in a specific callee or takes another path. This is a new localized
diagnostic, not another uninstrumented startup retry.

## Run-007: localized native script progress

Prepared packet:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-007/task.json`

Runtime report:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-007/runtime-report.json`

The focused eight-test runner suite, pinned H2 differential/caller and H3
final-image caller reports, and ARM/Thumb interworking gate passed before this
original-only launch. The loopback listener was owned by the staged child PID
`2132`; the runner source SHA-256 was
`cb768a3aee1aad7d4357ffa412fec1bd4f6abaaeb9b3bffd34566c10b93f6547` before
and after. The task packet SHA-256 was
`313704c0e3a9e819e01d369ff279e100178b9638c81b2b397ec4f344b2768517`. CLI
arguments used 30 seconds for startup and per-packet waits, and 180 seconds
for a State-2 capture if startup succeeded.

Read-only stops recorded the dispatcher's common return epilogue at
`0x001C03D0` initially with the `r4+0x08` word equal to 1, the guarded
pre-menu call at `0x0026FA94` with the same word
equal to 11, then returns at `0x001C05AC` and `0x001C05B8`. The latter is the
return from `engine_func_001a863c`. At `0x001C05C4`, the word at `r4+0x08` was
12 after the dispatcher increment. This supports calling it a progressing
control word in this observed dispatcher path, but does not reconcile it with
`FlowScriptExecContext::code_base` documented at `+0x08`; keep the runtime field
name unresolved until the type/caller audit is complete. No `TitleMainWork`,
title query, Calc handler, or nested callback was observed before the
30-second startup deadline. Static disassembly identifies `0x001C03D0` as
`mov r0,#0; pop {r4,pc}`, the dispatcher's common return path, not a loop
entry. Run-007 removed its one-shot breakpoint after the first return at word
1, so it did not observe the later return after index 12. No further
breakpoint fired after the word reached 12; the report does not locate the
subsequent execution point.

The trace does not prove a deadlock or establish why run-017 reached title
initialization at about 3.19 seconds. It narrows the next static question to
the command reached after index 12 and its caller. The report records
all offline gates passed, four existing source-identity warnings preserved,
CCI/save/fixture/profile seed hashes unchanged, disposable profile removed,
and all breakpoints cleared. The staged fixture SHA matched its expected
`6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; the
supplied save was not staged.

## Run-008: observer rearm failure

Prepared packet:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-008/task.json`

Runtime report:
`build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-008/runtime-report.json`

The same offline gates passed. The trace captured the same guard and resource
returns as run-007, then reported eight stops at `0x001C03D0` within about
0.13 seconds, each with the same caller `0x00103164` and context word 1. This
was a tracer bug: after clearing the software breakpoint, it reinstalled it
while the CPU was still stopped at the return instruction. Continuing
therefore retriggered the same breakpoint before the guest executed the
epilogue. Those eight events are not eight guest loop iterations and do not
indicate a game stall. The guest-path conclusion remains the run-007 bounded
startup observation. The run-008 report records CCI/save/fixture unchanged,
profile cleanup, and no active breakpoints. Its runtime log SHA-256 is
`cdf72e3be531f5a5d22fde5fa5465ef0a2b23d6aea9a12600c87b71c3ded4ce5`
(966,459 bytes).

The corrected observer uses the statically verified caller return at
`0x00103164` (the `BLX r1` at `0x00103160` in
`engine_func_00102f18`). It removes that breakpoint, places a temporary one
at `0x00103168`, and resumes through the original `mov r5,r0`. Only after that
instruction executes does it re-arm `0x00103164`. A focused test verifies the
return-site breakpoint is absent during this step.

## Run-009: command return not observed

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-009/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-009/runtime-report.json`

Packet SHA-256 is `e871af579b2cf088008ab9536a2002e208ee3865d9f8908dc2db48d9b533ee0e`; report SHA-256 is `2e0a16abb22e2c9bf9fa1b9f6ed96b49a538791d206a6711515e1d2abe587112`. The run used the pinned runner SHA-256 `99615a923c6e3ca16577044ecb5546a74eaecbbefd14cbc104758f4f3afc0a43` before and after, with a 30-second startup bound. All prelaunch offline gates passed; the loopback listener owner matched the disposable child. The report retained the four H2 source-identity warnings. The CCI, supplied save, disposable fixture, profile seeds and runner were unchanged, the staged profile was removed, and no breakpoints remained.

The trace recorded 72 coalesced/individual navigation events. The pre-menu call at `0x0026FA94` was allowed once for the observed context; it returned `r0=128`. The same context `0x14657380` reached `0x001C05AC` and `0x001C05B8` with the raw word at `+0x08` equal to 11, then `0x001C05C4` with that word equal to 12 at 4.885 seconds. `TitleMainWork`, title input, Calc, and nested callback events were absent. The observer then expired its startup wall-clock bound waiting for another watched stop. Static evidence says `0x001C05C4` branches to the common epilogue `0x001C03D0`, but this run did not observe that branch or the return. It does not establish a guest stall, deadlock, or progression through unobserved code. The independent review agrees that the missing evidence is the post-increment return path. Runner SHA-256 was `99615a923c6e3ca16577044ecb5546a74eaecbbefd14cbc104758f4f3afc0a43` before and after this run.

## Run-010: return target and bounded guest snapshot

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-010/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-010/runtime-report.json`

Packet SHA-256 is `9f65e87f5aa54409814040030b33fe1fadf3691eec13a6ff5e9875069ad728e0`; report SHA-256 is `e749de3287c2419bc12ea028bfb4a4257a8c8cc51b408e1b24be048186271188`. The pinned runner SHA-256 `481988f2a4eb7c235c282a5de809561874e052797429111fe5e1d2e8ef343b73` matched before and after. All five offline gates passed; the report retained four H2 source-identity warnings, verified the loopback listener belonged to the launched child, and recorded the CCI/save/fixture and profile-seed hashes unchanged. The staged profile was removed and all breakpoints were cleared.

At `0x001C03D0` (6.051 seconds), the one-shot epilogue trace captured raw context word `+0x08=12` and saved PC `0x00103164` at `[SP+4]`, before the original `mov r0,#0; pop {r4,pc}` executed. The caller-return breakpoint did not fire: the generic breakpoint at `0x00103164` had already reached its 128-stop cap on 67 unrelated contexts by 4.527 seconds and was disarmed. This proves the stack return target, not that the pop or caller return ran.

At the 10-second bound, a read-only ETX interrupt obtained a stop at `0x002A88A8`, LR `0x001465A8`, SP `0x0FFFFEB0`. Pinned disassembly places the PC at `pop {r4,r5}` immediately after `svc #0x22` in matching helper `engine_func_002a8898`; the LR resumes at `ldrex` in `engine_func_001464f8`. The exact SVC behavior and whether this path caused any wait remain unresolved. The interrupt does not prove deadlock or explain the missing title initialization. The independent run-010 review agrees with these bounds.

## Next diagnostic: run-011 targeted return

Remove `0x00103164` from the startup breakpoint set so unrelated callbacks do not consume its stop budget. Arm it only when the one-shot `0x001C03D0` snapshot reports saved PC `0x00103164`; capture that return, execute the original instruction at `0x00103168` once, and do not re-arm. Keep the `0x001C03D0` breakpoint one-shot after the exact `0x001C05C4/+0x08=12` event.

Use a 10-second startup bound, 30-second packet timeout, and at most 120 seconds for State-2 capture if title initialization is reached. Keep the 20 nested-return and 40 readiness-check caps. On timeout, retain the ETX register/PC/stack snapshot, without claiming it identifies a deadlock. Before launch, run the focused suite, pinned H2 differential/caller, H3 final-image caller, and ARM/Thumb interworking gates; pin the runner and tests. Preserve the four source-identity warnings and verify the loopback owner, input/save/fixture/profile hashes, disposable-profile cleanup, and cleared breakpoints. If TitleMainWork remains absent, use the captured caller and interrupt PCs for static analysis before any further launch.

## Run-011: targeted caller return

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-011/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-011/runtime-report.json`

Packet SHA-256 is `ba5139cc14e4f8d8809c7b43c34beaba16d1affbefe6bd6dac92ba90706039f2`; report SHA-256 is `93b91105cc66d11deb0d83b69239d9b93b0c307a2cfe252d6bf029b09074aa94`. Runner SHA-256 `ef971fdbc51a720a299cbcb630996db8d732a6b7184c6c183fe700188a5c6dd4` matched before and after. The prelaunch task-input, H2 differential, H2 caller, H3 final-image caller, and ARM interworking gates passed; four source-identity warnings remained explicit. The loopback listener belonged to the staged child. The CCI, supplied save, disposable fixture and profile seeds were unchanged; the disposable profile was removed and no breakpoints remained.

With the generic return breakpoint removed from startup, the one-shot epilogue at `0x001C03D0` again recorded saved PC `0x00103164` for raw context word `+0x08=12`. The targeted caller stop arrived at `0x00103164` at 1.709 seconds, and the runner executed the original `mov r5,r0` through `0x00103168` once. This closes the previously missing native command return observation, but did not reach `TitleMainWork`, Audio Settings, State 2, or a nested callback within the 10-second startup bound.

The timeout interrupt again stopped at `0x002A88A8`, LR `0x001465A8`, in the pinned `svc #0x22` wrapper return path. Static inspection shows the caller resumes with an atomic load at `0x001465A8`; the guest's saved `r4` at the wrapper stop is `0x00431C40`, the address read by that atomic load after the wrapper restores its saved registers. The runner did not capture the value stored there, so it cannot say which branch follows. The timeout still does not prove a deadlock or assign semantics to SVC `0x22`.

## Run-012 plan: bounded state read

Keep the same 10-second route and targeted return observer. When the ETX snapshot is exactly `PC=0x002A88A8` and `LR=0x001465A8`, decode saved `r4` from `[SP]` and read the 32-bit word at that address while the guest is stopped. Record the raw unsigned and signed values without naming the object or inferring the SVC contract. Do not resume guest execution or add another wait. If TitleMainWork remains absent, analyze the recorded state and the startup caller path before any further launch.

No guest data writes are added. All input/save/profile protections, offline gates, source-identity warnings, loopback-owner checks, and cleanup requirements remain unchanged. H2 stays open until the actual Audio Settings scenario, completion/readiness path, clean shutdown, and restart comparison are supported.

## Run-012: caller reconfirmed; timeout in a separate system-call path

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-012/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-012/runtime-report.json`

Packet SHA-256 is `e31ed37cc69cf150116932991ecb81cff3c3382818cbcd5b084ac35eda946bdf`; report SHA-256 is `fcf115748efc8d7a0b3d3f32ec9a8cadb857fa8ed52a0a94085e57614c172c2e`. The runner SHA-256 `70de2643850dde030f1de4b0d5254adb0e33f3bd8e7cf506131214a0d085b7e5` matched before and after. The pinned task-input, H2 differential, H2 caller, H3 final-image caller and ARM/Thumb interworking gates passed. The four H2 source-identity warnings were retained. The loopback listener owner matched the staged child; CCI, supplied save, disposable fixture and profile seed hashes were unchanged. The disposable profile was removed and all breakpoints were cleared.

At 1.194 seconds, the one-shot dispatcher epilogue again recorded raw context word `+0x08=12` and saved PC `0x00103164`. At 1.210 seconds the targeted caller breakpoint fired with `r0=0`; the runner stepped the original instruction through `0x00103168`. This independently reconfirms the command return and one caller instruction, but still did not reach `TitleMainWork`, Audio Settings, State 2 or a nested callback.

The 10-second ETX snapshot stopped at `PC=0x00147C34`, `LR=0x00105890`, `SP=0x0FFFFEF0`; the conditional `[SP]`/saved-`r4` read for `PC=0x002A88A8, LR=0x001465A8` therefore did not run. Pinned code places `0x00147C34` immediately after `svc #0x32` in matching wrapper `func_00147c0c`. Static caller inspection ties this stop to the regular frame path: `runtime_blocks.cpp` calls `engine_func_00105848` as part of the CRT frame, its call at `0x0010588C` reaches the four-byte branch at `0x002C25F0`, and `func_0014782c` tail-calls `func_00147c0c`; the observed LR is the return at `0x00105890`. This explains which call path was interrupted. It does not establish the service contract, a guest stall, or why the separate title-initialization route did not reach `TitleMainWork`.

Independent review confirmed the packet/report/runner and `code.bin` pins, the caller return and single-instruction step, the exact timeout PC/LR, and that the conditional state read was skipped. The supplied save remains at SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e`; the original CCI remains at `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`.

Before another runtime launch, use this pinned caller chain and the already reviewed run-017 State-2 capture to choose a probe at an H2-relevant transition. Do not repeat a generic timeout snapshot: it is likely to interrupt a periodic frame/service path and does not resolve the pending ID-8 callback. H2 remains open.

## Run-013: longer startup bound and conditional wait-state read

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-013/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-013/runtime-report.json`

Packet SHA-256 is `3a9cf34e5dcc0f354485468ba5508f2f57a702796c34344fd926a410b923b4cc`; report SHA-256 is `d40678827a3541cc4377fc97d555dc9235c880951a2e92badefa9ad9a166cbc7`. Runner SHA-256 `70de2643850dde030f1de4b0d5254adb0e33f3bd8e7cf506131214a0d085b7e5` matched before and after. All 29 task input hashes and all five offline gates passed; the four source-identity warnings remained explicit. The run used a 90-second startup bound, 30-second packet wait and 120-second State-2 bound. The loopback listener was owned by the staged child. The CCI, supplied save, disposable fixture and profile seeds were unchanged; the disposable profile was removed and all breakpoints were cleared.

The run again recorded the dispatcher epilogue at `0x001C03D0` with raw context word `+0x08=12`, then the targeted caller return at `0x00103164` and original step to `0x00103168`. It still did not reach `TitleMainWork`, Audio Settings or State 2 within the 90-second startup bound.

This run did reach the exact conditional snapshot site `PC=0x002A88A8`, `LR=0x001465A8`. The wrapper's saved `r4` was `0x00431C40`; the single bounded read at that address returned raw `0xFFFFFFFE`, signed `-2`. The pinned caller at `0x001465A8` executes `ldrex r2,[r4]`, `cmp r2,#0`, then `ble 0x001465CC`. If the value remains negative when that later load executes, the branch goes through `clrex` and back to `0x00146588`, before setup of another call to the SVC wrapper. The snapshot did not resume the guest, so it does not prove that branch executed or that a retry occurred; it assigns no meaning to the word, object or SVC and proves no deadlock.

Independent review verified the 29 packet hashes, report and runner identity, gates, loopback ownership and cleanup, the caller return, the exact conditional read and the ARM branch destination. H2 remains open. Do not repeat the same 90-second route or add another generic timeout read; next analyze the pinned callers/state around the observed retry path and the already reviewed run-017 callback route, then choose a probe that can distinguish H2 script progress from a separate pending system call.

This probe does not close H2 or establish physical input parity, patched runtime equivalence, clean restart, persistence, or whole-game equivalence.


## Run-014: observed one retry, then an Audio Sync wait path

Prepared packet: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-014/task.json

Runtime report: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-014/runtime-report.json

Packet SHA-256: a48908ec8b675bf114e4da88d17d9d7ca6b7967ea556ef4b2ac62fbfd74a57cd; report SHA-256: c2c41a856678da7ec9e817ab6e55dde90fec97c336df16fbd8cb8c3ff2453477. Runner SHA-256 before and after: 16941a89582a44ebfe22f9514cee2afc3728f6fa89fdfad204d761625ffa73f8. The recorded invocation used 30 seconds for startup, 30 seconds per RSP packet, and 120 seconds for State 2.

All five prelaunch gates passed: packet input hashes, H2 differential, H2 caller composition, H3 final-image caller composition, and ARM interworking. The four existing source-identity warnings remained present. The loopback listener was 127.0.0.1:55295, owned by the launched child PID 24248. The original CCI, supplied save, disposable fixture, and profile seeds remained unchanged. The profile was removed and no breakpoints remained after cleanup.

The new read-only observer stopped at 0x001465CC at 0.750 seconds. r4=0x00431C40, r2=0xFFFFFFFE (-2), and the bounded word read at [r4] was also 0xFFFFFFFE. After clearing that one-shot breakpoint, execution reached 0x001465A4 at 0.780 seconds with the word still -2. This is direct evidence that the negative branch destination was reached and execution returned to the next call site once in this sample. It does not identify the SVC contract or prove a persistent deadlock.

Startup still did not reach TitleMainWork or Audio Settings. At the 30-second deadline the interrupt stopped at PC=0x002A88A8, LR=0x002C36DC, SP=0x0FFFFEC0. The captured stack has the saved r4 value 0x00431CA4 and saved continuation 0x001131C4. Static disassembly maps 0x002C3628 to the AsdSync_Wait declaration in src/engine/asd_file.cpp; its code receives the sync pointer in r0, stores it in r4, and calls the SVC wrapper at 0x002C36D8, whose continuation is 0x002C36DC. The caller path at 0x0013AD64 sets r0 = r4 + 0x64 and tail-branches to 0x002C3628; in this run the base pointer 0x00431C40 plus 0x64 matches the saved sync pointer 0x00431CA4. The stack continuation 0x001131C4 lies after the call at 0x001131C0 in battle_func_00113150; that function's observed r7 was 0x402. These names and raw values identify the static path only; their higher-level runtime purpose and the word at 0x00431CA4 remain unresolved. The guest was interrupted inside the SVC wrapper before a stop at 0x002C36DC, so no SVC return or loop-back was observed.

This narrows the next probe to a one-shot stop at 0x002C36DC after the wrapper returns: record r0, r4, and the raw word at [r4], clear the breakpoint, and let the original instructions continue. That would read the pending synchronization state without changing it and distinguish the wait value from the earlier -2 at 0x00431C40. Do not repeat a blind startup timeout. H2 remains open.


## Run-015: separate sync return observed; retry caller persists

Prepared packet: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-015/task.json

Runtime report: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-015/runtime-report.json

Packet SHA-256: effe00820e65bbe2ec98f2f54a61fd972f5e4f89d3d47015910c06e6cc8d0edb; report SHA-256: c57b357a99a19a299f294f66292cc202890f11200f2d4b5a76aa9cc300b44bd5. Runner SHA-256 before and after: 3dac6f1a5357f18c19a2cda3395b1c784e5e35f90e42c7cd2ca462e03e26c6ab. The invocation used 30 seconds for startup, 30 seconds per RSP packet, and 120 seconds for State 2.

All five offline gates passed; the four source-identity warnings remained visible. The loopback listener at 127.0.0.1:58620 belonged to child PID 12912. The CCI, supplied save, disposable fixture, and profile seeds remained unchanged; the staged profile was removed and all breakpoints were cleared.

The one-shot return observer at 0x002C36DC fired at 0.308 seconds with r0=0, r4=0x00465024, and the bounded word read at [r4] equal to 0. This was a raw snapshot at the post-wrapper call site; the pointer differs from the 0x00431CA4 sync pointer inferred from Run-014, so do not merge the events or assign a shared object identity.

Run-015 later captured the atomic retry branch at 0x001465CC with r2=-2 and [0x00431C40]=-2, then the call site 0x001465A4. At the 30-second deadline it was again stopped at PC=0x002A88A8/LR=0x001465A8, with saved r4=0x00431C40 and the word still -2. No TitleMainWork, title query, or State-2 handler event was recorded. The separate AsdSync_Wait event does not identify the timed-out call; no deadlock or SVC semantics are established.

The next bounded variant should retain the 0x002C36DC one-shot but allow at most a second stop at 0x001465CC: after the first branch stop, observe 0x001465A4 once, then re-arm only 0x001465CC for one additional raw value read. Clear it at the second hit and continue. This distinguishes a repeated negative branch from the separate sync-return observation without leaving a recurrent breakpoint armed. Keep H2 open.



## Run-016: one observed wait/recheck cycle; startup still stops before TitleMain

Prepared packet: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-016/task.json

Runtime report: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-016/runtime-report.json

Packet SHA-256: bc8d2d50d48e396b05856ba18c4e44c5312cb271772dbaf62bf97f7d685b8921; report SHA-256: 4645c74ce7ad5821a49e7e3504509ca5cc433e9de7dc873c404957e999ed2092. Runner SHA-256 before and after: 1059abd06c4b47696338b173d11c96cfd31c2a7e59e0f48fc0e4aabdafce124e. Invocation: python -B tools/h2_state2_dispatch_trace.py --task-json build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-016/task.json --startup-timeout 30 --packet-timeout 30 --capture-timeout 120.

The task input hashes, H2 differential, H2 caller composition, H3 final-image caller composition, and ARM interworking gates all passed. The four existing H2 source-identity warnings remained explicit. The loopback listener was 127.0.0.1:48618, owned by child PID 10736. Run status is partial_failed because the 30-second startup bound expired before TitleMain; the run did not reach Audio Settings or State 2. The supervisor terminated the disposable child, removed its profile, found no active breakpoints, and confirmed the source CCI, supplied save, disposable fixture, and profile seeds unchanged. The supplied-save SHA-256 remained 6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9.

The one-shot 0x002C36DC observer again saw a return with r4=0x00465024 and raw [r4]=0; keep this event separate from the 0x00431CA4 pointer inferred in Run-014. The bounded retry observer captured branch hit 1 at 0x001465CC, with r4=0x00431C40, r2=-2, and [r4]=-2. At 0x001465A4, the pre-call register snapshot was r0=1, r1=0x00431C40, r2=1, r3=0, with the word still -2. The one permitted re-arm then captured branch hit 2 at 0x001465CC with the same raw address/value. This directly shows the call returned to the caller and the same negative branch was taken again in this sample; the capture does not count later iterations.

Static inspection narrows the mechanism. At 0x00146588..0x001465A4, the caller loads the handle, passes the address in r1, arbitration type 1 in r2, comparison value 0 in r3, and writes a zero 64-bit timeout to its caller stack before calling wrapper 0x002A8898. The wrapper executes svc #0x22 at 0x002A88A4. The package's unmodified Azahar source checkout is at commit 219d743a1e698101fe1ab8bef43e6563126c3c27; inspected source hashes are svc.cpp d55eeaefa017906c2cc189c42986c8aaf5aae92a7a04e6bd3bda68255dfe85b8, address_arbiter.h 44b5974ffc30fa15d586e21367d5ec2ffd98148b682dc7c40b3c33265e698b39, and address_arbiter.cpp 5882bd6b6cc686c56a862860b14c06bbcfbdbc6dbdb85ce03757232f0fd3ac8d. In that emulator source, SVC 0x22 maps to ArbitrateAddress, enum value 1 is WaitIfLessThan, and the implementation queues the current thread when the signed word at the address is less than the comparison value. With the observed -2 < 0 and zero timeout, this is an address-arbiter wait; after a wake the caller rechecks the word and may wait again. This describes the pinned emulator implementation, not a hardware-level contract or the game-level meaning of the object.

The interrupted stack also ties this wait to 0x002C3AA8 returning to 0x0013AD70: that helper compares the current thread ID against a field at object +4, calls the atomic lock helper on the object base when needed, then records the owner and increments a field at +8. The next probe will read only the three raw words at the saved object base, and only at the already pinned timeout PC/LR, so the owner/depth fields can be checked against this static layout without naming the object. No source or guest bytes were changed by Run-016.

H2 remains open. The next startup attempt must use a fresh packet pinning the Azahar source files and bounded raw-header reader, and must pass all offline gates before launch. Do not repeat an uninstrumented startup timeout; compare this route against the earlier reviewed Run-017 State-2 route and keep the observed thread/object values raw until correlated.



## Run-017: raw lock-object header captured at the bounded timeout

Prepared packet: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-017/task.json

Runtime report: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-017/runtime-report.json

Packet SHA-256: 78e0f86b0e2522ac0b87d7af41fb9fb62976f751050d4a1cd7fc74344e1b4743; report SHA-256: 287a0e64244c666d6ecf7ef9a4993b069105b48520b7d3d7f912c29995fc8a64. Runner SHA-256 before and after: 1eb113cab1aad1e6d966e70c8ddcbf93e8787cc7454423ae2997040f30fd7f07. Invocation used startup 30 seconds, packet 30 seconds, and State-2 capture 120 seconds.

All 34 packet input hashes and all five offline gates passed; the four H2 source-identity warnings remain explicit. The loopback listener at 127.0.0.1:45076 belonged to child PID 2780. The run timed out before TitleMain and is recorded partial_failed. The supervisor terminated only its child, removed the staged profile, and reported no active breakpoints. CCI, supplied save, disposable fixture, and profile seeds remained unchanged; the supplied save hash is still 6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9.

The one-shot trace again recorded branch 1 at 0x001465CC with r2=-2 and [0x00431C40]=-2, the call site 0x001465A4 with r0=1, r1=0x00431C40, r2=1, r3=0, and branch 2 with the same negative value. At the bounded interrupt the runner stopped at PC=0x002A88A8, LR=0x001465A8, with saved r4 base 0x00431C40. The three read-only dwords were offset 0 = 0xFFFFFFFE, offset 4 = 0x1FF82800, and offset 8 = 1. These are recorded as raw fields.

Static code at 0x002C3AA8 reads the current thread token, compares it with the word at object offset +4, calls the atomic lock helper on the object base when they differ, then stores the owner token and increments the word at +8. The observed stack returns through 0x002C3AC8 to 0x0013AD70 while the caller is inside that lock path. This supports the bounded interpretation that this caller took the non-owner lock path while another raw token (0x1FF82800) and count 1 were present. Run-017 did not capture the current token at the compare instruction, so the next one-shot will stop at 0x002C3AB4, immediately after the MRC instruction and before the owner load/compare, and record r0 plus the same three raw object words. No object type or game-level meaning is assigned.

This run still did not reach TitleMain, Audio Settings, or State 2. H2 remains open; the nested callback, completion, patched comparison, clean shutdown, and restart persistence remain unresolved.



## Run-018: first lock-compare was a different object; a separate CRT service timed out

Prepared packet: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-018/task.json

Runtime report: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-018/runtime-report.json

Packet SHA-256: dd01e734d8f01117ded109aa2c08b15682f6abe56b6823210bb770dc3698dc88; report SHA-256: 483239e4ac7c5b37dc12e1a79f26bdaca5951f4c0f4fb7df7f48095d45c19ceb. Runner SHA-256 before and after: 89f8f4b9b997ca46a169b53f84db58e1261ec31e83e094080f0d4bc306872e9f. Invocation used startup 30 seconds, packet 30 seconds, and State-2 capture 120 seconds.

The 34 packet inputs and all five offline gates passed, with the four source-identity warnings retained. The loopback listener at 127.0.0.1:47710 belonged to child PID 6404. The supervisor terminated the disposable child, removed the staged profile, cleared all breakpoints, and verified CCI, supplied save, disposable fixture, and profile seeds unchanged. The run timed out as partial_failed before TitleMain; its final stop was PC=0x00147C34, LR=0x00105890, the previously localized CRT SVC 0x32 path.

The one-shot at 0x002C3AB4 captured current token 0x1FF82000, object base 0x004E6EFC, and raw words 1, 0, 0. This was not the object base 0x00431C40 seen in Run-017. The observation is retained as a separate object and does not explain the timeout or establish its type. The current runner stopped after this first compare, so it did not observe the relevant 0x0013AD6C caller in this run.

The next probe will pin the target object dynamically: one-shot at 0x0013AD6C records the raw r0 passed to 0x002C3AA8, then arms one-shot 0x002C3AB4. It reads the three raw dwords only if r4 matches that caller base, then clears the breakpoint and resumes the original instruction. This avoids attributing an unrelated first lock object to the pending caller. H2 remains open.



## Run-019: object token matched; its raw header changed before timeout

Prepared packet: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-019/task.json

Runtime report: build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-019/runtime-report.json

Packet SHA-256: e1639b868a1daaf494418eac210940879b6c6f998dd0902d84823571d8a2921b; report SHA-256: 84d541766e4c06a5932cfc77844c796105726394fcf778d66a218daa8bf4d517. Runner SHA-256 before and after: 3b9f7e574509ac36214055be1ffe8566bca506a51938354dbb6c97e37bc9b694. Invocation used startup 30 seconds, packet 30 seconds, and State-2 capture 120 seconds.

All 34 packet hashes and five offline gates passed; the four source-identity warnings remain explicit. The loopback listener at 127.0.0.1:49958 belonged to child PID 16908. The supervisor terminated the disposable child, removed the staged profile, cleared breakpoints, and verified CCI, supplied save, disposable fixture, and profile seeds unchanged. The run timed out before TitleMain and is partial_failed.

The caller-specific one-shot at 0x0013AD6C captured object base 0x00431C40 and LR 0x001131C4. Its subsequent post-MRC compare at 0x002C3AB4 matched that base: current thread token was 0x1FF82800 and the three raw words were offset 0 = 1, offset 4 = 0, offset 8 = 0. At the timeout the guest was at PC=0x002A88A8, LR=0x001465A8, with saved r4 base 0x00431C40. The three raw words then were offset 0 = 0xFFFFFFFE, offset 4 = 0x1FF82800, offset 8 = 1. This directly shows the same raw token at +4 while the other words changed between the two observations. It does not identify which thread caused the changes or when the initial lock call returned.

H2 remains open. The next one-shot will be armed at 0x0013AD70 only after this caller's 0x0013AD6C hit; it will read the three raw object words and the byte at +0x76, then clear itself and resume. This tests whether that specific lock call reaches its return site before the bounded startup timeout, without changing guest state.


## Run-020: the caller-specific lock call reached its return site

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-020/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-020/runtime-report.json`

Packet SHA-256: `f60c0b81e61275b8000a7e003b523eb25b637a7faf76f438a2b3896c0c878b39`; report SHA-256: `dbec5c366918af85732a7348559c1a02d2fdbbc5a65ae97d730d211bf1f42402`. Runner SHA-256 before and after: `19c5021bd63e39656e13f8e435ab54f483c0b75b5f239464d25a595ce929be76`. Invocation used startup 30 seconds, packet 30 seconds, and State-2 capture 120 seconds.

All packet input hashes and five offline gates passed, including H2 differential, H2 caller composition, H3 final-image caller composition, and ARM interworking. The new interworking check verified the ARM `BL` at `0x0013AD6C` targets `0x002C3AA8` with bit 0 clear, and the return-site instruction at `0x0013AD70` is the pinned ARM word `0xE5D40076`. Four existing source-identity warnings remained visible. The loopback listener was `127.0.0.1:52878`, owned by child PID 21696.

The caller-specific stop at `0x0013AD6C` captured object base `0x00431C40` and LR `0x001131C4`. At `0x002C3AB4`, the current token was `0x1FF82800` and the raw words at the matching base were `1/0/0`. The one-shot at `0x0013AD70` then fired at 0.787 seconds, proving that this particular call returned from `0x002C3AA8`: the matching object's raw words were `0xFFFFFFFF`, `0x1FF82000`, and `1`, and byte `+0x76` was `0x02`. These snapshots show a change across the helper call, but do not identify why the token differs or assign a game-level type to the object.

The bounded retry observer then saw two branch-target hits at `0x001465CC`, both with raw `r2=-2` and `[r4]=0xFFFFFFFE`, with the permitted call-site observation between them. The run still did not reach TitleMain or State 2. After the 30-second startup bound, the stop was `PC=0x00153930`, `LR=0x002A4D9C`; static code identifies `0x00153918` as a 40-byte wrapper that issues `SVC #0x32`, and the pinned Azahar source labels that SVC `SendSyncRequest`. This timeout stop is after that SVC instruction and does not establish that the IPC call is causing the missing title transition.

The run is `partial_failed`, not a milestone pass. The supervisor terminated only its child, removed the staged profile, and reported no active breakpoints. The original CCI, supplied save, disposable fixture, and profile seeds were unchanged; the supplied-save SHA-256 remains `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. H2 remains open. The next bounded capture targets `0x002C3ACC`, after the second MRC and immediately before the owner-field store, conditional on the same caller base. It records the raw token and three raw words, then clears the one-shot and resumes the original instruction. A shorter 10-second startup bound is sufficient for this early caller-specific observation.


## Run-021: pre-store token differs from the later returned header

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-021/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-021/runtime-report.json`

Packet SHA-256: `7daeb9761c4203ddd016105eb5d2e046554670b68c3339bc5437559fe9e8a93e`; report SHA-256: `e223ddaff6996118708b0e2a2201201ccbfbb2804048e8c8986b47b55178be0e`. Runner SHA-256 before and after: `3fbc96edc31ed6478510f4310752e35582d9d7a6947cab0fb6947922c188e6ea`. The invocation used startup 10 seconds, packet 30 seconds, and State-2 capture 120 seconds.

All packet input hashes and the five offline gates passed, including the ARM instruction check for `0x002C3ACC` (`0xE5840004`, `STR r0,[r4,#4]`). The four source-identity warnings remained visible. The loopback listener was `127.0.0.1:58799`, owned by child PID 13320. The supervisor terminated that child, removed the staged profile, cleared all breakpoints, and verified the CCI, supplied save, disposable fixture, and profile seeds unchanged. The supplied-save SHA-256 remained `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`.

The caller-specific capture again matched object base `0x00431C40`. At the compare site `0x002C3AB4`, the current raw token and words were `0x1FF82800` and `1/0/0`. Immediately before the store at `0x002C3ACC`, the raw value in `r0` was `0x1FF82800`; the three words were `0xFFFFFFFF/0/0`. By the caller's return at `0x0013AD70`, the header instead read `0xFFFFFFFF/0x1FF82000/1`, and byte `+0x76` was `0x02`. This pins the value presented to the store but not why the later snapshot has a different owner word; no concurrency or thread-identity explanation is asserted.

Startup remained `partial_failed` and timed out after 10 seconds at `PC=0x002A88A8`, `LR=0x001465A8`, before TitleMain or State 2. The timeout header was the earlier raw triplet `0xFFFFFFFE/0x1FF82800/1`. H2 remains open. The next one-shot will stop at `0x002C3AD0`, immediately after the owner store and before the depth load, to read the same three words while `r4` still matches the caller base. This distinguishes the post-store value from any later change before the outer call returns.


## Run-022: post-store value matched `r0`; later return snapshot differed

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-022/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-022/runtime-report.json`

Packet SHA-256: `3ae755beb6d189f6a54a64acdf6196c44d04769ddba91d7587de29e2e91b57c7`; report SHA-256: `66dae84d0c63b98da16338a53cfb1254c39271a017de54497fe1f9b855b120c5`. Runner SHA-256 before and after: `60af6b6892eae928670fa5461a711c02703baaadfaf59d812cf1476c509ade2b`. The invocation used startup 10 seconds, packet 30 seconds, and State-2 capture 120 seconds.

All packet input hashes and five offline gates passed, including the checks for the ARM instructions at `0x002C3ACC` (`0xE5840004`) and `0x002C3AD0` (`0xE5940008`). The four source-identity warnings remained visible. The loopback listener was `127.0.0.1:54815`, owned by child PID 20692. The supervisor terminated that child, removed the staged profile, and reported no active breakpoints. The CCI, supplied save, disposable fixture, and profile seeds remained unchanged; the supplied-save SHA-256 remained `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`.

At `0x002C3ACC`, the observed raw `r0` was `0x1FF82800` and the matching object's words were `0xFFFFFFFF/0/0`. At `0x002C3AD0`, immediately after the original store, `r0` remained `0x1FF82800` and the memory words were `0xFFFFFFFF/0x1FF82800/0`. At the outer return `0x0013AD70`, the same base read `0xFFFFFFFF/0x1FF82000/1` and byte `+0x76=0x02`. Thus the post-store read matches the value in `r0`; the later owner-word difference appears sometime after this stop and before the outer-return snapshot. The trace does not identify an actor or scheduler cause.

Startup again timed out before TitleMain or State 2, at `PC=0x002A88A8`, `LR=0x001465A8`, after the 10-second bound. The run is partial evidence, not a milestone pass. H2 remains open. The next attempt will stop collecting these low-level startup observations by default and reuse the already reviewed State-5 → A-confirm route, retaining the task/instruction and nested `BLX` observations needed for the actual acceptance criterion. The low-level lock observers remain available only as an explicit diagnostic option.


## Run-023: lock probes disabled, but command-progress stops remained

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-023/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-023/runtime-report.json`

Packet SHA-256: `fc866006d62841753693bc0c564f28c56c18f4bbece0ac4a56e3f5831373345a`; report SHA-256: `1174f6d25add86c4e46383b0bbb53afbe216be49b3f25dda78986135fc5a32bc`. Runner SHA-256 before and after: `62cecf0a9a37aed3e451b9f7ea2ef6bdec8ed8d0588c46229b8a77077c904809`. Invocation used startup 90 seconds, packet 30 seconds, and State-2 capture 120 seconds; the startup lock-path option was disabled.

All offline gates passed and the four source-identity warnings remained. Listener `127.0.0.1:51191` was owned by child PID 22144. The run logged the safety-guard call and native-command progress through the caller return, but did not observe TitleMain or any title query. It timed out at `PC=0x002A88A8`, `LR=0x001465A8`, and is partial evidence. The staged profile was removed, no breakpoints remained, and the original CCI, supplied save, disposable fixture, and profile seeds remained unchanged.

Comparison with the reviewed State-2 run-017 shows the same CCI, disposable-save hash, profile seeds, and staged config hashes; run-017 reached TitleMain and State 5, while Run-023 did not. The cause of that route difference is not established. The Run-023 log shows 90 seconds elapsed. The next reproduction disables the remaining native-command progress/return breakpoints as well as lock observers.


## Run-024: minimal startup breakpoints still did not reach TitleMain

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-024/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-024/runtime-report.json`

Packet SHA-256: `e145499e7e62753029b77b22d3fc19b7b70808df7d537a823a3b84d058ee79e7`; report SHA-256: `28fd5df0e0925297fb4803d501429fcbe5cddb7c8121e2d3caa6d42d65907ff7`. Runner SHA-256 before and after: `09fb6095933953d6f61afd39ea809ef32b0e52ac6f227097aeefe79a97b42bbc`. Invocation used startup 90 seconds, packet 30 seconds, and State-2 capture 120 seconds; both startup observer options were disabled.

All offline gates passed and all four source-identity warnings remained visible. Listener `127.0.0.1:40539` was owned by child PID 12544. Only the safety-guard event was observed; there was no `title-main-init`, logical title query, handler, or nested callback. At the 90-second bound the stop was `PC=0x002A88A8`, `LR=0x002C36DC`. The run is `partial_failed`; the staged profile was removed, breakpoints were cleared, and original inputs, save, fixture, and profile seeds were unchanged.

Run-017's preserved Azahar log reaches 189 seconds during its State-2 capture, whereas Run-024 ended at 91.7 seconds. This does not prove that extra startup time will solve the route, but it justifies one bounded reproduction with startup extended to 180 seconds. Do not infer that the sync wrapper is the cause of the missing title transition. H2 remains open.


## Run-025: longer startup bound, different final PC, still no title transition

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-025/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-025/runtime-report.json`

Packet SHA-256: `c8fdd6b23454cd2a5239f419bdd7c01b96c216203ef7e3772474bda93419493b`; report SHA-256: `93428022a850c5236094eafd919689605cf58cb226fb66bac0d8683379eb7da9`. Runner SHA-256 before and after: `09fb6095933953d6f61afd39ea809ef32b0e52ac6f227097aeefe79a97b42bbc`. Invocation used startup 180 seconds, packet 30 seconds, and State-2 capture 120 seconds; both startup observer groups were disabled.

All packet hashes and five offline gates passed; the four source-identity warnings remained. The loopback listener `127.0.0.1:53401` was owned by child PID 14216. The trace recorded only the pre-menu safety-guard event; no TitleMain initialization, title query, State-2 handler, or nested callback was observed. At the 180-second deadline the PC/LR snapshot was `0x002B8258/0x002AA480`, different from Run-024's sync-wrapper stop. This records a different sampled PC at the bound; it does not by itself prove title-flow progress.


## Run-026: 300-second minimal startup attempt stopped at the known atomic wrapper

Prepared packet: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-026/task.json`

Runtime report: `build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-026/runtime-report.json`

Packet SHA-256: `e2ed83069c9b29f7d91b71e943b597bc17a803435078f152fecb75a0ee6e8693`; report SHA-256: `90a1e3c9002225049d14f4e88f50cff50bbab40fbf46a8ca470e2415893b7c70`. Runner SHA-256 before and after: `09fb6095933953d6f61afd39ea809ef32b0e52ac6f227097aeefe79a97b42bbc`. The invocation used startup 300 seconds, packet timeout 30 seconds, and State-2 capture timeout 120 seconds; both optional startup observer groups were disabled.

All five offline gates passed and the four H2 source-identity warnings remained visible. The private listener `127.0.0.1:58154` belonged to disposable child PID 20344. The trace recorded only the pre-menu safety-guard event; it saw no TitleMain initialization, title query, State-2 handler, or nested callback. At the startup deadline the stop was `PC=0x002A88A8`, `LR=0x001465A8`, `SP=0x0FFFFEB0`. The bounded timeout read recovered saved `r4=0x00431C40`; the three raw words there were `0xFFFFFFFE`, `0x1FF82800`, and `1`. Pinned code identifies `0x002A88A8` as the wrapper instruction after `SVC #0x22` and `0x001465A8` as the continuation at the atomic-load path. This snapshot does not show whether the guest resumed, retried, or remained blocked, and it does not establish that this path caused the missing title transition.

The supervisor terminated only the disposable child, removed the staged profile, cleared all breakpoints, and verified the CCI, supplied save, disposable fixture, profile seeds, and runner remained unchanged. The supplied-save SHA-256 remained `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; no Azahar process remained. Run-026 is `partial_failed`; H2 remains open. No further generic startup-bound extension is planned.

### Bounded runtime/static composition from preserved State-2 Run-017

The preserved report records ten calls to top-level handler ID 8 at `0x001A07CC`, each returning `2`. Pinned wrapper code executes an indirect `BLX r0` at `0x001A07FC`, then compares the callback result: zero takes the `moveq r0,#2` return path, while nonzero follows the path that returns `1`. Thus the ten outer returns support the inference that an indirect callback returned zero on those calls, conditional on the pinned wrapper path; the raw inner `r0`, dynamic callback pointer, and nested ID were not captured. This evidence does not bind those returns to `0x00221168`.

### Static resolution of the SoundConfig instruction-12 row

The pinned CCI at `E:/emulador3ds/00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci` has SHA-256 `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`. Its RomFS index maps `/camp/config.bf` to section-relative offset `136607472`, size `512`. Reading the indexed asset from the pinned CCI at raw offset `0x84976F0` yields SHA-256 `eea827346c226038e8e36e1a763df919c33f6a9f7bdce0da259a50b4573ee80e`; its header is `FLW0`, internal file size `0x110`, with five sections. The `SoundConfig_Change` procedure starts at instruction index 10. Its instruction index 12 contains word `0x00210008`: top-level handler ID `8`, adjacent nested ID `0x21`.

In the pinned original `extracted/exefs/code.bin` (SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`), nested table base `0x00406038` plus `0x21 * 8` resolves to row `0x00406140` at file offset `0x306140`. The row bytes are `68 11 22 00 01 00 00 00`; its first word is callback pointer `0x00221168`, and the second word is `1`. Run-017's runtime task had method table `0x086E5AD0`, instruction index 12, and top-level ID 8, so the static SoundConfig row aligns with that runtime dispatch. The runtime capture did not read the adjacent halfword, the nested table entry, or the `BLX` target, so this remains asset/runtime correlation rather than direct dynamic resolution.

An independent static contract audit of `0x00221168` is recorded in [h2-callback-contract-00221168.md](h2-callback-contract-00221168.md). It finds direct global/pointer effects and a large unresolved final helper; it does not produce a typed candidate or runtime claim. Run-026 did not reach TitleMain or the wrapper. Do not repeat generic startup-bound extensions. Any fresh RSP attempt must first resolve the route-specific divergence between the earlier successful Run-017 and the later pre-title atomic-wait timeouts; if State 2 is reached, capture the actual ID-8 `BLX` target and return before attributing the callback behavior to `0x00221168`.
