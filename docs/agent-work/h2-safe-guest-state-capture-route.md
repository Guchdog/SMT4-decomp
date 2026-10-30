# H2 guest-state capture and deterministic-input route audit

## Result

**No currently approved, supported route satisfies both remaining needs:**
read `g_ConfigBytes` and callback state from the staged Azahar guest, and drive
repeatable H2 input without keyboard/mouse. The H2 image's manual UI behavior is
acceptable partial evidence, but the task packet and prior audits do not
establish a safe live observation/input path. Do not start another emulator,
network listener or debugger session from this audit.

This conclusion is specific to the available pinned 2126.2 interfaces and the
reviewed repository tools. It is not a claim that Azahar cannot be modified to
provide a safe interface.

## Candidate routes

| Route | What saved evidence supports | Why it does not unblock H2 |
| --- | --- | --- |
| Built-in GDB/RSP | Pinned Azahar source binds the listener to `INADDR_ANY`; the CLI accepts a port but exposes no bind-address option. The latest same-value probe stopped before sending RSP because its required listener gate observed a wildcard bind. The checked-in `azahar_hit_flag.py` only connects/attaches, sets/removes breakpoints, continues, reads PC and detaches. | It cannot read `g_ConfigBytes` or full callback state in its current form. A separate RSP reader would need memory-read support, exact staged-path/PID ownership, and a current reviewed loopback-only network boundary before connection. The existing RSP probe did not establish actual `m`/`M`/`P` capability or callback reachability. Deterministic input additionally requires an independently documented guest event seam; the current input-contract audit explicitly says no writable seam is established. |
| Azahar RPC | Pinned source/client support guest-memory read/write requests and screenshots. | The server binds wildcard UDP port 45987; enabling it does not make it loopback-only. The client lacks breakpoint, execution-control, register and input operations. Default async memory access can race with emulation and has unsafe-region warnings. It cannot produce a synchronized snapshot at Calc stores or drive H2. |
| CemuHook UDP touch | Pinned client consumes `touch_1` active/x/y and turns calibrated coordinates into a touch status. An offline local server could theoretically send coordinate responses. | No checked-in server or end-to-end runtime test proves that touch reaches the H2 manager's registered regions. The client ignores PadData button fields. Touch is not a proven source for Calc's logical button-query results and does not expose guest memory. A hypothetical touch stream alone is not H2 input equivalence evidence. |
| Existing H2 offline runners | ARM differential/caller runners can compare original and reconstructed functions with explicit state and modeled service return values. | They operate on harness memory and mocked service boundaries. They can test a controlled logical return contract, not prove physical input delivery, live callback scheduling, or guest state in Azahar. |
| Portable profile/log snapshots | CLI launches, patch application, profile files and logs have been recorded for the final image. | The logs confirm process/profile identity and IPS application. Guest `g_ConfigBytes` is not serialized into the observed Azahar profile files, so hashes cannot substitute for a guest-memory capture. |

## Supported facts and unresolved assumptions

- The pinned Azahar CLI has a `--gdbport` setting but no documented listener
  address override. The pinned source binds GDB to `INADDR_ANY`; the run-007
  safety gate stopped when its staged process listener appeared as `0.0.0.0`.
  A static firewall snapshot or a loopback client destination does not change
  the server's bind address. The separate locality review requires current,
  authoritative effective-policy evidence or administrator-reviewed narrow
  policy before a future RSP connection.
- The saved RPC review identifies the wildcard UDP bind, limited request set and
  asynchronous access caveat. No RPC request was sent in the audit trail.
- The RSP probe's bounded attempt did not connect or read/write a guest
  register; it stopped at listener ownership/locality gating. The existing
  checked-in monitor's code does not implement guest-memory reads, while the
  proposed contract's RSP `m`/`M`/`P` support remains unprobed.
- H2's static input contract says manager state meanings, callback timing,
  logical-input state production and a synchronized guest injection seam are
  unresolved. It prohibits treating a write to an undocumented work/global
  field or directly editing `g_ConfigBytes` as equivalent to a UI event.
- The final manual runtime record establishes only the observations reported by
  the user and the saved process/profile/log identities. It contains no guest
  `g_ConfigBytes` sample or deterministic matched input trace.

## Safe next unblock

Keep runtime work stopped until both boundaries have independently reviewed
plans:

1. **Observation:** either (a) add a reviewed, read-only observer to a local
   Azahar build that exposes explicitly scoped guest memory/callback snapshots
   without a remote listener, or (b) obtain current authoritative evidence
   that a narrowly staged GDB observer can connect only to loopback and cannot
   be reached through any non-loopback interface. If route (b) is chosen, first
   implement and review an RSP memory reader with strict process/path/port
   checks and timeouts; do not enable the current RPC server as a shortcut.
2. **Input:** identify from original instructions and producers a valid,
   synchronized logical-input or touch event path; establish its timing and
   exact fields from the original runtime. Test that route without directly
   changing config bytes or guessing event/work addresses. A CLI-driven UDP
   touch fixture is only a candidate for investigation, not an established
   route.
3. From matched disposable profiles, capture `g_ConfigBytes[0..7]`, work/cursor
   and relevant producer state at defined callback boundaries while executing
   the same no-op, edit-cancel, confirm, re-entry and restart scenarios in
   original and patched profiles. Separately record what the original persists.

Do not make firewall changes, launch Azahar, connect to a listener, change
profiles, send UDP, write guest memory, or use host input under this task. If
the reviewer cannot establish a safe observer or a real input seam from pinned
source/artifacts, stop and ask for the specific external authorization or
reviewed Azahar build needed.

## Scope

This is a read-only route decision, not a game behavior test, RSP/RPC capability
probe, input experiment, firewall review, or H2 acceptance. All runtime,
caller-scheduling and guest-state claims remain bounded as in
`h2-manual-final-image-runtime.md` and `h2-input-seam-contract.md`.
