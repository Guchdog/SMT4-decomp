# H2 runtime harness research: Azahar CLI and GDB route

Status: static research only. Azahar was not launched, no GDB connection was opened, and no active emulator/profile data was inspected or copied. This document specifies a future isolated route; it is not runtime evidence.

## Findings and evidence levels

### CLI and user-data location

The desktop Qt frontend at the pinned [Azahar 2126.2 `citra_qt.cpp`](https://github.com/azahar-emu/azahar/blob/2126.2/src/citra_qt/citra_qt.cpp) parses `--gdbport N` (alias `-g N`), `--windowed` (`-w`), and a final game path. The port parser accepts a base-0 integer. The [same tag's `core.cpp`](https://github.com/azahar-emu/azahar/blob/2126.2/src/core/core.cpp) enables the GDB server and applies this override port. Example command for a future approved run:

```powershell
& 'C:\H2Lab\azahar-2126.2\azahar.exe' --windowed --gdbport 24690 'C:\H2Lab\input\smt4-us-decrypted.cci'
```

Run with working directory `C:\H2Lab\azahar-2126.2`. This is an example command, not executed. The prior H0 record reports Azahar 2126.2 and GDB port 24689; local executable build identity/hash was not verified in this research. Before any runtime run, verify the staged executable version/hash and patch identity; choose a free loopback port distinct from the historical 24689.

The Qt argument parser exposes no user-directory override. In pinned [Azahar 2126.2 `file_util.cpp`](https://github.com/azahar-emu/azahar/blob/2126.2/src/common/file_util.cpp), Windows `SetUserPath` prefers `GetExeDirectory()\\user\\` if that directory already exists; otherwise it falls back to the roaming AppData Azahar directory. Therefore `$env:APPDATA` is not a reliable isolation control. Use a **separate staged installation directory** containing the executable and its required runtime files, and create an empty `user\\` directory beside that staged executable before launch. Validate in a future authorized run that the log reports the local user directory and the resolved path is within the staged tree. Keep original and patched runs in distinct staged trees, each with a separately prepared pristine test profile, or restore an independently prepared pristine profile snapshot between runs. Do not seed either from the active profile. This task did not establish whether an empty profile contains the lawful system files/title setup needed to boot; the runtime owner must provision that input independently and verify paths before starting.

The historical H0 record identifies the title as `00040000000E5C00`, US v0.1.0, code image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, and baseline `g_ConfigBytes=32 50 50 30 00 00 00 00`. These are prior evidence only, not a current environment inspection.

### Existing repository debugger support

`experiments/semantic_equivalence/azahar_hit_flag.py` is the only checked-in Azahar/GDB script found in the declared search. It hardcodes `127.0.0.1:24689`, defaults emulated PID to decimal 11, and implements RSP connect, `qSupported`, no-ack negotiation, extended mode, `vAttach;b`, one-shot 4-byte software breakpoints (`Z0`), continue, PC read (`p0f`), breakpoint removal, and detach (`D`). It does **not** read guest memory, write registers or memory, drive game input, or monitor H2 addresses. Its interrupt/finally path attempts to remove remaining breakpoints and detach. The historical H1 capture file is not present in this checkout; do not rely on it.

`tools/h1_menu_slice_integration_experiment.py` and `tools/title_navigation_family_experiment.py` are offline ARM/Unicorn tools, not Azahar process control. No current repo tool provides the required H2 state snapshots or deterministic input driving.

## Proposed bounded RSP session

This is a protocol plan for a new, separately reviewed script; no script was added here. Bind only to loopback and the selected isolated process. Do not connect to the existing 24689 service. Discover/confirm the emulated PID from the isolated process's own log rather than assuming 11. The old H0 PID is historical evidence only.

1. Check that the selected port (example 24690) is unused. Stage the exact executable/game/patch pair and isolated `user\\` tree. Start the staged executable with the command above. Confirm from its log that the requested game and local user path loaded and that the stub listens on the chosen port. Stop if any resolved path points outside the staged tree.
2. Connect to `127.0.0.1:24690`; negotiate `qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+`. If advertised, send `QStartNoAckMode`. Send `!`, require `OK`, then send `vAttach;<pid-hex>` and require a stop reply beginning with `T`. For historical PID 11, `<pid-hex>` would be `b`; future runs must use the isolated process's observed PID.
3. Arm only a small set of `Z0,<address>,4` breakpoints at a time; require `OK`. Suggested observation sequence: title state 9 caller `0x001EA398`; initializer entry `0x002F4CA0`; main calc `0x001EA928`; secondary callback `0x002CAEF0`; draw callback `0x002CAFD0`; readiness check `0x002FC0EC`; title reset `0x001EA3D8`. Disarm a one-shot breakpoint with `z0,<address>,4` as soon as its observation is complete. For input-store sampling, use only the exact store instruction addresses from the H2 calc contract, after checking the disassembly; the report's grouped interval `0x001EACB4..0x001EACE4` is not a list of every instruction address.
4. At stops, read PC (`p0f`; the existing monitor treats it as little-endian bytes) and capture register context needed to interpret the stop, then use `m<addr>,<length>` for memory. Capture `g_TitleConfigWork` pointer at `0x0044E2D0`; if non-null, snapshot the full `0x158` work area. Capture the eight-byte config block with `m44e0f8,8`; title work pointer at `0x0044E300`; title state at pointer `+0x9C`; and task/work handles at their contract offsets. Save each packet reply alongside stop PC, run identity, profile-seed identity, source/patch hash, event-sequence step and timestamp. Avoid interpreting a stale work pointer after the secondary cleanup callback frees it; take the pointer/area snapshot at callback entry and before cleanup, then record global nulling separately.
5. Use same seed and identical scripted event sequence for original and patched runs. At minimum capture before entering settings, after initializer return/first calc, after each injected event while calc state is active, after each live config write, at state-2 branch, after secondary cleanup, at readiness, and after return to title. Include H2 scenarios: no edit then cancel; edit then cancel; edit then the other state-2 result; and re-entry. These scenarios test live writes and persistence independently. The contract establishes writes to `g_ConfigBytes` during active state 1 and a state-2 write at `+4`; it does not settle commit/rollback or durable-file behavior.

### Deterministic input injection boundary

A script can encode RSP writes (`M<addr>,<length>:<hexbytes>` for memory and `P<reg>=<target-endian-register-hex>` for a register), but support for these packets on the local Azahar stub has not been probed. The current monitor implements neither. More importantly, no safe H2 input address/state is established: `TitleConfig_Calc` consumes event/cursor helper results from unresolved services including `0x0029D8FC`, `0x002C1830`, `0x0029F278`, and `0x0019DFBC`; raw event handles at `work+0x1C..0x22` are initialized by helper calls and their representation/producer is not settled. Do not write arbitrary values into these locations or claim that a config-byte edit is equivalent to UI input.

Before deterministic input can be called reproducible, resolve the event/cursor service contracts and identify a valid pre-calc guest-state seam. Then, in a separately reviewed driver, pause at that seam, write only a documented logical event/HID state through a validated RSP packet, continue for a bounded interval to the next known callback/store breakpoint, snapshot, and clear breakpoints. Validate packet responses and a no-op negative control before using mutation. If Azahar rejects `M`/`P`, stop; do not fall back to OS keyboard/mouse automation in this route. An alternative is a tested emulator-native movie/input script mechanism, but none was found in the declared local repository tooling and it is outside this static audit.

## Teardown and failure limits

For a completed observation, remove every armed breakpoint with matching `z0` packets, send `D` and require a detach response where supported, close the socket, and allow the isolated emulator to resume before a graceful application close. For an exception, attempt cleanup in a `finally` block, record whether each cleanup request succeeded, and do not kill or attach to an unrelated process. Because the existing monitor calls `c` in a blocking loop and has only an interrupt handler, a future snapshot driver needs finite socket timeouts, explicit stop/continue policy, a maximum stop count/deadline, and guaranteed detach attempts. If the process stops at an unexpected PC, the connection drops, PID mismatches, any breakpoint cannot be removed, memory reads are short, or the log shows a non-isolated profile path, stop the run and mark the capture partial/failed.

Azahar issue [#2196](https://github.com/azahar-emu/azahar/issues/2196) reports a GDB-stub hang on some Windows builds after long pauses. It is not proof of a defect in the historical 2126.2 setup, but it supports keeping stops brief, batching only a few reads at a time, and recording the exact local version. No current runtime observation verifies RSP `M`/`P`, watchpoint support (`Z2`/`Z3`), attach behavior on a staged build, or reliable detach after a fault. Prefer breakpoint-and-read sampling; test watchpoints only as an optional capability probe, not a prerequisite.

## Facts, inference, and open limits

**Documented/source facts:** pinned 2126.2 Qt CLI flags above; GDB override enables the stub; Windows local `user\\` selection is conditional on its existence beside the executable; H0's prior build/port/title/hash; repository script's implemented RSP subset; H2 callback/global addresses and config bytes as documented in the init/calc contracts.

**Proposed inference/design:** a copied/staged application tree with a newly created adjacent `user\\` directory isolates user data because the pinned file utility resolves that local path. Future runtime must verify the effective path in logs; isolation is not proven by this research alone. The sample command and packet sequence are unexecuted.

**Unresolved:** current installed executable version/hash; fresh-profile boot prerequisites and lawful fixture availability; isolated target PID; actual RSP `M`/`P` and watchpoint support; event/cursor producer semantics and logical input seam; profile serialization/rollback/persistence; task scheduler ordering/lifecycle. No semantic or original-versus-patched runtime acceptance is established.

## Next action

The integrator should provision two independent staged Azahar trees and authorized pristine profile fixtures, verify their effective user paths and exact executable/patch hashes in a separately assigned runtime task, and build a reviewed bounded RSP reader. In parallel, resolve the event/cursor helper contracts; only then choose and validate a no-OS-input injection seam. Run original and patched scenarios from matching disposable seeds, and keep this research note distinct from execution evidence.
