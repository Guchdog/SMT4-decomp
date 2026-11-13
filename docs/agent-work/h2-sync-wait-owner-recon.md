# H2 sync-wait / lock owner recon (2026-11-12)

## Scope

Read-only static follow-up to
[`h2-real-entry-readiness-diagnosis.md`](h2-real-entry-readiness-diagnosis.md).
The goal was to identify the guest synchronization object that keeps the
title-config thread from completing after the first ComWin wait. No source,
ledger, board, runner, profile, or emulator state was changed.

## Stop sites

| Observation | Address | Meaning |
|---|---|---|
| Free-run 5 s stop | `0x001465A8` | ARM exclusive-load spinlock body (`ldrex r2,[r4]`) |
| Free-run 30 s stop | `0x00153930` | `func_00153918` tail, after TLS access and `SVC #0x32` |
| Startup failure stop | `0x002A88A8` | `engine_func_002a8898` tail (`pop {r4,r5}; bx lr`) after a sync wrapper |

The lock spin at `0x001465A8` belongs to `engine_func_001464f8`
(`[0x001464F8,0x001465D8)`, `src/engine/leaf_batch42_c.cpp`). The adjacent
`0x001465CC` path clears the exclusive monitor and branches to `0x00146588`
when the lock word is `<= 0`; that is the contention/wait path.

## Lock object 0x00431C40

The only literal reference to `0x00431C40` in `extracted/exefs/code.bin` is at
`0x00129A20`, in `battle_func_0012991c` (`[0x0012991C,0x00129A24)`,
`src/engine/leaf_batch43_c.cpp`). The initializer loads the object pointer at
`0x001299A0` and writes:

- `[+0x00] = 0`
- `[+0x04] = 0`
- `[+0x08] = 0xFFFFFFFF`
- `[+0x2C..0x44] = 0`
- `[+0x48] = 0`
- `[+0x4C] = 0`
- `[+0x50] = 0`
- `[+0x58], [+0x5C], [+0x64], [+0x68], [+0x6C] = 0`
- `[+0x70] = 1`

The runtime free-run sample reads `[+0x00] = 0xFFFFFFFE`,
`[+0x04] = 0x1FF82000`, `[+0x08] = 1`, and byte `[+0x76] = 2`. The current
thread token observed in the earlier captures was `0x1FF82800`. The owner word
therefore belongs to a different guest thread or context.

## Interpretation

The title-config thread is not blocked on a missing title-config state machine
step; it is parked in the same guest spinlock/sync family already documented for
the startup captures. The first ComWin wait (`nested 33`, selector 6) completes
at `r2=39`; the next script step (`nested 5`, selector 11) waits for the default
window object to reset from state 4 to 0, and the guest thread ends up spinning
on `0x00431C40` or waiting in `SVC #0x32`/`SVC #0x22` paths. The lock owner token
does not match the current thread, so another guest thread owns the resource and
is not releasing it in this automated profile.

This is consistent with an emulator guest-thread/service lifecycle problem, not
with a missing C++ reconstruction or an input-entry shortcut. The existing GDB
stub reports the stopped guest as thread 1; it did not expose the owner thread
for direct inspection in this run.

## Next observations

1. Identify the lock acquisition/release sites that use the object initialized
   by `battle_func_0012991c` (the function stores a pointer at `[r4+0x1c]`, so
   other users may reach the object through that pointer rather than the literal
   address).
2. Inspect the guest thread that owns token `0x1FF82000` and the service it is
   blocked on (audio, file I/O, task scheduler) using a guest-thread-aware
   debugger path or targeted instrumentation, not a generic startup timeout.
3. Correlate the stop with the default-object state-4 reset writer
   (`default_object+8`) and the selector-11 wait at script index 14.
4. Only after the owner/release path is understood should the paired
   original-versus-patched runtime scenario be retried.

## Limits

- Static disassembly and preserved runtime reports only; no new emulator run.
- The lock is identified by its literal initializer; other accesses may use
  pointer aliases and are not enumerated here.
- The owner token interpretation as a guest thread id is an inference from the
  raw values, not a captured thread table.
- No claim of whole-game or H2 equivalence.
