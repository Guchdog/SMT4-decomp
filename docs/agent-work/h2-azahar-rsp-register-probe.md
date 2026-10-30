# H2 Azahar same-value r0 probe


## Latest assigned attempt: run-007

Run-007 launched the staged Azahar 2126.2 CLI with a fresh profile, approved seed files, pinned CCI and unique port `59931`. The owner query resolved the listener to the staged PID but reported `0.0.0.0`; the safety gate rejected this wildcard bind before RSP. The runner terminated only its child (PID `24696`). No RSP packet, guest register action, memory write or keyboard/mouse input occurred. The isolated title log confirms title ID `00040000000E5C00` and staged user/game paths. EXE, CCI, runtime file manifest and seed hashes remained unchanged. Windows application-error query still cannot load `Microsoft.PowerShell.Diagnostics`. See the [run-007 report](../../build/agent-work/H2-semantic/h2-azahar-rsp-probe/run-007/evidence/probe-report.md) and [record](../../build/agent-work/H2-semantic/h2-azahar-rsp-probe/run-007/probe-record.json).

The pinned Azahar 2126.2 GDB source binds to `INADDR_ANY`, consistent with the observed wildcard. The next step is a separate source/safety investigation for a supported way to restrict access to the ephemeral listener; no RSP retry is authorized by run-007.


## Latest assigned attempt: run-006

Run-006 supersedes the run-001 status below for the latest CLI attempt. Eleven
offline tests passed and all frozen packet inputs matched. One fresh attempt
launched staged Azahar PID `26460` with `-g 59566` and the staged CCI. The
PowerShell `Get-NetTCPConnection` owner query timed out after four seconds, so
the runner stopped before RSP and terminated only its own child. No RSP
connection or guest register operation occurred. The installed PID `14948`
was not contacted; a post-run process check found only that installed process.

The staged log records Azahar `2126.2 | HEAD-219d743`, title ID
`00040000000E5C00`, and absolute accesses under the disposable E: `app/user`
tree. It logs `Pausing process 11 at start`; this is evidence that the title
loaded, not evidence of a particular GDB state. The logged
`UseGdbstub:false`/`24689` settings are pre-override configuration and do not
establish the effective runtime stub state. These staged paths were confirmed
by post-run log inspection, but the runner's ownership query failed before its
subsequent in-run path gate. The source and
staged EXE/CCI hashes matched after the run, both approved seed files remained
unchanged, and the runtime file manifest was unchanged. Stdout/stderr and Qt
plugin diagnostics were empty. Windows application-error capture could not
load `Microsoft.PowerShell.Diagnostics`, so no event conclusion is available.
The specific blocked gate is listener ownership verification, not a confirmed
absence of the listener. See the
[`run-006 report`](../../build/agent-work/H2-semantic/h2-azahar-rsp-probe/run-006/evidence/probe-report.md)
and [structured handoff](../../build/agent-work/H2-semantic/h2-azahar-rsp-probe/run-006/handoff.json).
The offline follow-up replaces that slow PowerShell query with bounded native
`netstat.exe` parsing; it does not relaunch Azahar or repeat RSP. See the
[listener-query report](h2-azahar-listener-query.md).

## Run-001 result (historical)

The offline RSP tests pass. The disposable runtime attempt reached the mandatory
listener-ownership check but could not verify an owner for port `57822`; the
probe stopped there, terminated only its own Azahar process, and made no RSP
connection. No register write, title callback stop, or runtime capability claim
was obtained. The task remains blocked at this environment-specific process
verification gate.

The run record is
[`probe-record.json`](../../build/agent-work/H2-semantic/h2-azahar-rsp-probe/run-001/probe-record.json).
It records the launched process PID, exact CLI, stage paths and hashes. The
staged executable matched the pinned SHA-256
`c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`; the copied
CCI hash matched its source (`9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`).
The new `app/user` profile was empty before launch. The launched host process
was PID `1376`, and its recorded exit code was `1`. A post-run process check
found no process with that PID and no listener on port `57822`. The active
Azahar PID `14948` and its profile were not contacted or changed.

## Probe implementation

[`h2_azahar_rsp_probe.py`](../../tools/h2_azahar_rsp_probe.py) requires the
pinned executable hash, stages only the executable, top-level DLL dependencies,
Qt plugins, a new empty adjacent `user` directory, and a copy of the supplied
CCI. It rejects an existing stage path and the historical GDB port `24689`.
Before the RSP exchange it requires a free selected loopback port, verifies
that the selected listener belongs to the `Popen` child, and looks for both the
staged profile and game paths in logs under that staged profile. The protocol
sequence is bounded by socket/startup deadlines, discovers the emulated PID
from `qfProcessInfo`, sets only the documented title-main callback breakpoint
at `0x001E989C`, reads the stopped PC and `r0`, writes the same target-endian
value with `P0=...`, reads `r0` back, removes the breakpoint, and detaches. It
does not write guest memory or send host input. Any failed gate returns a
failure record; process cleanup targets only the child created by this run.

The offline suite covers RSP framing/checksum validation, ARM little-endian
register encoding, a local-stub same-value `p0`/`P0` round trip, and rejection of
an unexpected acknowledgement. Command:

```text
python -m unittest tests.test_h2_azahar_rsp_probe -v
```

Result: 4 tests passed. `py_compile` also completed successfully. The runtime
command and exit code are recorded in the structured handoff. The failed
listener-owner check is the unblock point: an assigned runtime owner needs a
working, independently verifiable Windows listener-owner query for the staged
process. The probe was not launched again after that failed gate, and no
keyboard/mouse fallback was used.

## Limits

The local test stub validates only the client protocol implementation. It does
not establish Azahar's actual `P` packet support, callback reachability, or
same-value register behavior. The empty disposable profile may also be
insufficient to boot the title; that question was not reached. Existing
original/patched user trees and the active emulator remain outside this task's
evidence.
