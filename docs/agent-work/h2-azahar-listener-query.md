# H2 Azahar listener-owner query refinement

## Change

The run-006 failure was a four-second timeout starting PowerShell and querying
`Get-NetTCPConnection`. The probe now invokes Windows' native `netstat.exe`
with `-ano -p tcp` and a three-second subprocess deadline. Its parser requires
the TCP header, validates every TCP row's shape, state, numeric endpoints and
PID, and fails closed on malformed output. It selects listeners on the chosen
port, requires loopback-only local addresses, and rejects multiple owning PIDs.
No matching listener returns `None`; a query timeout, failed command, malformed
output, non-loopback bind, or ambiguous owner raises `ProbeError`.

The runtime gates are unchanged: the staged process must be the sole owner of
the chosen loopback port before the in-run staged-user and game-path check; RSP
is reached only after both checks pass. The listener query has no permission to
connect to a process or send input.

## Offline evidence

The focused suite covers IPv4 and IPv6 parser rows, malformed/missing-header
output, ambiguous PIDs, wildcard listener rejection, timeout failure, a free
loopback port, and a live loopback listener owned by the current test process.
`python -m unittest tests.test_h2_azahar_rsp_probe -v` passes all 15 tests.
`python -m py_compile tools/h2_azahar_rsp_probe.py tests/test_h2_azahar_rsp_probe.py`
also passes. This task performed no Azahar launch, profile/game write, RSP
exchange, or keyboard/mouse operation. Run-006 remains historical partial
runtime evidence and must not be retried without a fresh assignment.

