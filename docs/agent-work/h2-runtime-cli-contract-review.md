# Coordinator review: Azahar H2 CLI/GDB route

## Review result

**Recommendation:** accept this as the runtime harness design for H2. It respects the requested CLI/GDB-only interaction and records the unproven capabilities instead of assuming them.

I reviewed the handoff and protocol plan. It uses Azahar's windowed CLI and GDB port, requires a separately staged executable tree with an adjacent `user` directory, uses loopback RSP, verifies the isolated PID and paths from logs, limits breakpoints and snapshots, and defines detach/cleanup conditions. It prohibits fallback to keyboard/mouse automation. The sequence includes original and patched scenarios, config/work snapshots, re-entry, and persistence observations.

The plan correctly treats RSP memory/register writes as unvalidated and refuses to inject arbitrary event-handle values. That is the key blocker for deterministic edit/cancel/confirm coverage: the logical event seam and Azahar's `M`/`P` support must be proven before those scenarios can be driven. Breakpoint-and-read capture can still establish entry, callback order, field state, and reset behavior without injection.

The ownership/provenance checker passed. This is static tool/source research only: no launch, GDB connection, profile-path verification, input injection, caller capture, or original-versus-patched runtime comparison was performed. The report's pinned-source URLs support the version-specific CLI and profile-path claims; local executable identity and boot prerequisites remain to be checked in the future runtime task.

## Runtime gate

Before launching, verify the local executable/version/hash, staged game and patch hashes, free port, and effective isolated user path from the process log. Use matching disposable profile seeds for original and patched runs. Add a reviewed RSP driver only after packet support and a documented logical input seam are validated; if these remain unavailable, report only the behavior actually observed through CLI/GDB and leave edit/persistence acceptance open.
