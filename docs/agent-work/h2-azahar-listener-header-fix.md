# H2 listener-header validation fix

## Change

`parse_netstat_listener_rows()` now requires the complete expected header
columns and rejects duplicate headers. A bare `Proto`, missing `PID`, or
incorrect address-column label raises `ProbeError`; a complete header with no
TCP rows remains the distinct valid empty-table case. This closes the review
finding without changing the listener owner, loopback, PID, staged-path, or RSP
gates.

The focused test run initially surfaced that this Windows installation emits
Spanish netstat headings (`Dirección local`, `Dirección remota`, `Estado`) in
OEM code page 850. The query now decodes using `GetOEMCP()` and validates either
the full English or normalized Spanish header. It does not guess based on a
partial heading. Actual live free-port and listener ownership tests pass with
the host's localized output.

## Validation

- `python -m unittest tests.test_h2_azahar_rsp_probe -v`: exit 0; all 17 tests
  passed, including bare/truncated/duplicate header rejection, valid empty
  table, complete localized header, IPv4/IPv6 synthetic rows, a live loopback
  PID check, and a free loopback port.
- `python -m py_compile tools/h2_azahar_rsp_probe.py tests/test_h2_azahar_rsp_probe.py`:
  exit 0.
- Run-001 frozen inputs and both writable code baselines matched before edits;
  frozen input hashes still match after the change.
- Offline only: no Azahar launch, RSP, profile/game write, or keyboard/mouse
  action occurred.

The independent review's header-only false-empty finding is corrected. This
does not establish ownership for Azahar or runtime RSP behavior; a future
runtime attempt still requires a fresh packet and the existing process/path
gates.

