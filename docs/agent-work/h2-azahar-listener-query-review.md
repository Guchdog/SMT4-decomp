# Independent review: H2 Azahar listener-owner query

## Recommendation

The owner check and RSP gate ordering are sound for the reviewed scope, but the
parser needs one small fail-closed correction before the next runtime attempt:
validate the complete `netstat` header instead of accepting a bare `Proto` token
as a valid empty snapshot. This gap cannot pass the owner gate or cause an RSP
connection; it can misreport malformed/truncated output as “no listener” and
continue polling until startup timeout.

## Finding

**P2 — incomplete header accepted as empty results.** In
[`tools/h2_azahar_rsp_probe.py`](../../tools/h2_azahar_rsp_probe.py),
`parse_netstat_listener_rows()` sets `saw_header = True` whenever the first
header token is `Proto`, without checking the column labels. Consequently
`parse_netstat_listener_rows("Proto\n")` returns `[]`. If the command exited
zero with that truncated output, `listener_owner()` would return `None` rather
than reject malformed output. This remains fail-closed for the RSP gate, but
does not meet the stated malformed-output contract. Validate the expected
header columns and add a regression for header-only/truncated output.

## Reviewed behavior

- The command is a direct argument-vector call to `netstat.exe -ano -p tcp`,
  `shell=False` by `subprocess.run` default, with a three-second timeout. A
  timeout, OS error, nonzero exit, or parse error raises `ProbeError`.
- TCP listener rows parse both IPv4 and bracketed IPv6 local endpoints. Port
  matching is exact; listener PID must be a positive ASCII decimal integer.
  Multiple addresses owned by the same PID remain one owner; multiple PIDs for
  the selected port fail. Non-loopback binds, including wildcard, fail.
- The live test binds a loopback socket and verifies the query reports the
  current Python PID. A free-port test returns `None`; synthetic parser tests
  cover IPv4/IPv6, malformed rows, ambiguity, wildcard rejection and timeout.
  These checks passed in the independent focused run: 15 tests, exit 0.
- The runtime sequence checks `process.poll()`, waits for the selected listener,
  requires a fresh owner query to equal `process.pid`, then verifies staged
  user/game paths, and only then calls `connect_and_probe()`. A listener owned
  by another process cannot reach RSP through this sequence. The code does not
  connect to installed PID 14948; it only queries the local TCP table.

## Evidence boundary

Run-006's post-run log inspection confirmed title `00040000000E5C00` and paths
under the disposable stage. The runtime owner query itself timed out before the
runner's in-run path check, so no effective GDB state or RSP behavior was
established. The logged `UseGdbstub:false` and port `24689` are pre-override
configuration and are not evidence of the runtime setting. This review ran no
Azahar process, did not modify profile/game data, and performed no RSP or host
input operation.

After complete-header validation is corrected and independently checked, a
freshly assigned runtime task may use this owner query while preserving the
staged PID and staged-path gates. Runtime evidence remains partial until the
bounded same-value probe actually completes.

