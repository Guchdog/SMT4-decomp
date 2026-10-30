# H2 Azahar binary loopback audit

## Result: unresolved

The target `E:\smt4decomp\build\h2-runtime\h2-azahar-rsp-probe\run-007-59931\app\azahar.exe` has SHA-256 `c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`, matching the staged executable hash in `build/agent-work/H2-semantic/h2-azahar-rsp-probe/run-007/probe-record.json`. This is the executable hash, distinct from the packet's game reference hash. The prior locality investigation identifies source commit `219d743a1e698101fe1ab8bef43e6563126c3c27` and reports `INADDR_ANY` in its [GDB stub](https://github.com/azahar-emu/azahar/blob/219d743a1e698101fe1ab8bef43e6563126c3c27/src/core/gdbstub/gdbstub.cpp). That source finding is indirect evidence and does not identify any binary instruction or demonstrate equivalence of a modified binary.

No GDB address initialization instruction, file offset, or instruction bytes were established. No derivative is currently defensible from this audit. A zero immediate or byte pattern alone would be insufficient: a reviewer needs the data flow from the GDB-specific entry point to the socket address passed to bind, all uses of the changed instruction, correct IPv4 network byte ordering, instruction boundaries, and evidence that any replacement preserves surrounding behavior. Runtime binding and other behavior remain unobserved here.

## Method and limitation

`Get-FileHash` was read-only and matched the probe record. REA 6.4.0 CLI was available; no REA MCP tools were connected. A headless `rea inspect` with the Ghidra provider was started on the exact target with Node 26.11.1, but did not finish during this bounded investigation; it was interrupted, with no usable REA Evidence or offsets. No Ghidra output should be treated as a completed finding. There was no binary mutation, executable launch, socket or network probe, firewall change, or keyboard/mouse interaction.

## Next action

Under a separately scoped analysis task, allow a completed headless analysis of this exact hash with retained output, then trace the source-correlated GDB setup through the bind call and independently review its machine-code data flow and all patch-site uses. Record exact original bytes and file-offset mapping before considering an isolated copy. A copy would require separately authorized verification and cannot inherit the original executable's hash or policy identity. No runtime or semantic equivalence is established by this report.
