# H1 navigation reducer: continuation and adapter contract

## Static result

There is a statically feasible path from the compiled reducer back into the
original state-5 body, but it requires an assembly tail shim (or a fully
reconstructed C++ continuation). An ordinary C++ adapter cannot return while
intentionally leaving the callee-saved `r4`, `r8`, and `d8`/`s17` in the
values needed by an interior original continuation. The candidate's current
status return is a shim control value, not the original UI callback return.
This is a feasibility analysis only; no adapter or integrated differential
has been built.

The pinned `code.bin` SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
`config/game_info.json`.

## Original frame and exact paths

`ui_func_001e989c` enters at `0x001E989C`. Its prologue pushes `r4-r8,lr`,
saves `d8`, and allocates `0x20` stack bytes (`0x001E989C..0x001E98A8`). It
loads the title work pointer into `r5` at `0x001E98AC` and copies it to `r4`
at `0x001E98B0`. State 5 reaches the inline window at `0x001E9D08` with this
callback frame still active.

The two gate failures are *not callback returns*. Script failure at
`0x001E9D18` and preview failure at `0x001E9D28` both branch to
`0x001EA62C`. That is the shared later state-5 continuation: its first two
instructions load the global slot `0x0044E300` into `r6` and the current work
pointer into `r4`, and it proceeds through transition/fade work before the
callback's common epilogue. The epilogue at `0x001EA7D8..0x001EA7E4` adds back
`0x20` stack bytes, sets return `r0=0`, restores `d8`, then restores
`r4-r8` and returns. The original gate failure skips the timer, cursor, input,
and event work but continues at `0x001EA62C`.

At `0x001E9D08`, before either gate succeeds, `r8` and `d8`/`s17` still hold
their callback-entry values. The inline window does not alter them on a failed
gate. This matches the compiled candidate's ordinary ABI return, which
preserves callee-saved `r8` and `d8`. At the shared branch target, the original
code does not use `r8` or `s17`; it re-establishes `r6/r4` from the global
slot. Static scan of this callback finds the relevant `r8/s17` uses only in
the successful state-5 path described below.

After both gates pass, the original performs:

| Address | Original action / state |
| --- | --- |
| `0x001E9D2C` | `r8 = 0x0044E300`, the address of the global pointer slot (literal at `0x001E9EBC`) |
| `0x001E9D30` | `s17 = 1.0f` (`0x3F800000`, literal at `0x001E9F30`; `s17` is the upper 32 bits of `d8`) |
| `0x001E9D38` | `r4 = [r8]`, the current work pointer, read after both gates |
| `0x001E9D3C..0x001E9D44` | increment work timer `+0x64` by 1.0 using `s17` |
| `0x001E9D48..0x001E9DDC` | trigger pairs, signed normalization, cursor/cache and event reducer |
| `0x001E9DE0` | success continuation, before blend/clamp and touch polling |

At `0x001E9E30`, the blend path moves live `s17` into `s1` when the current
blend value is greater than 1.0, then stores it to work `+0x68`. At
`0x001E9E4C`, touch processing reloads the singleton work pointer with
`ldr r6,[r8]`. Thus success continuation requires exactly `r8=0x0044E300`,
`r4` equal to the work pointer sampled by the original at `0x001E9D38`, and
`s17=1.0f`. These values are live and can affect post-reducer behavior.

The original `r0` at `0x001E9DE0` holds the final cursor after the cache store,
but the first continuation instruction (`ldr r0,[r4,#0x64]`) overwrites it.
On the gate-failure path, the first instructions at `0x001EA62C` overwrite
`r6`, `r4`, and then `r0`. The candidate's return value 0/1 is therefore
usable as a local dispatch status if the shim branches immediately; it is not
an original callback return value. The complete original callback returns 0
from its common epilogue.

## Adapter options and exact constraints

The candidate is an AAPCS C++ function with a 248-byte relocation-free symbol.
It returns 0 when either readiness check fails and 1 when the reducer finishes.
Its own prologue/epilogue restores stack and callee-saved registers. The current
code contains a 16-byte PC-relative literal pool and internal relative branch;
its private candidate report validates those regions. This alone does not
place/link the symbol in a patched game image.

A bounded naked ARM call-site shim could replace the inline window
`0x001E9D08..0x001E9DE0` by calling the candidate and dispatching on `r0`:

1. Call candidate from the existing callback frame. Keep `sp` balanced; it
   must equal the original frame's `sp` when tail-branching. The candidate
   saves/restores its callee-saved registers and returns status in `r0`.
2. If status is zero, tail-branch to `0x001EA62C`, **not** to the callback
   epilogue. Do not initialize `r8/s17` on this path: the original skipped
   their writes, and the tail body reloads `r6/r4` itself. It must preserve
   the callback-entry `r8/d8` values through the candidate call.
3. If status is one, set `r8=0x0044E300`, set `r4` to the same work pointer
   captured by the reducer after readiness gates, set `s17=1.0f`, then
   tail-branch to `0x001E9DE0`. `r0-r3` and condition flags are not needed at
   this continuation: the first instructions reload `r0-r2` and the later
   compare sets flags before conditional VFP operations. `r5` must retain its
   original callback value; the C++ callee preserves it.
4. Preserve the original callback frame and do not `bx lr` from the shim. The
   continuation eventually reaches the existing epilogue, which restores the
   callback-entry `r8/d8` and returns 0.

An ordinary C++ function that calls the candidate and then returns cannot
leave `r4/r8/d8` changed: its ABI requires restoring those registers for its
own caller. C++ control flow also cannot directly resume at the middle of this
ARM callback. A normal C++ wrapper can be used only if the remaining blend,
touch, and later callback work are reconstructed as C++; to rejoin the current
ARM body, the handoff/branches and register writes must live in a naked ARM
shim or equivalent patch trampoline. A direct branch from the candidate's
normal return is insufficient because status 0 and 1 have different targets.

One remaining pointer detail needs an explicit contract. The original samples
the title work pointer at `0x001E9D38` and holds it in `r4` across trigger and
event calls. The current candidate likewise samples the global after the
gates and holds its local pointer while reducing, but it does not return that
pointer to the shim. Reloading `*[0x0044E300]` after the candidate is equivalent
only if no intervening trigger/event helper can replace the global pointer.
No write to this title slot is visible in the inspected helper entry bodies,
but transitive/reentrant mutation has not been ruled out. For a strict contract,
either make pointer stability an asserted invariant and test it, or extend the
candidate boundary to publish the captured pointer through an explicit
out-parameter before relying on `r4` at resume.

The branch targets are within ARM branch range of the original callback, but
the reviewed object is only a test artifact at its injection address. A code
cave/placement, patched call reachability, literal-pool non-overlap, stack
alignment and final executable mapping have not been established. No byte
patch, object link, or full callback substitution is approved by this static
note.

## Smallest next caller-context differential

Use a private original-image copy and a shim/candidate image; leave the
production candidate and shared runner unchanged during the test. Start at
`0x001E9D08` with the already-active callback frame represented explicitly
(`r4/r5=work`, chosen entry `r8/d8`, aligned `sp`, `lr`, `FPSCR`, and a bounded
`0xA0` work block). Hook only the four documented external entries
`0x00289924`, `0x0025A2BC`, `0x002B902C`, and `0x002B91C4`, recording helper
order and event-time cursor/cache.

Minimum directed cases:

- script false: preview/input skipped; adapter goes to `0x001EA62C` with the
  entry `r8/d8` intact and no timer/cursor/cache writes;
- script true, preview false: input skipped; same tail target/register
  preservation, with preview called once;
- both ready, unchanged cursor/cache and no event: shim reaches `0x001E9DE0`
  with `r4/r8/s17` exact, balanced `sp`, and original cursor/timer/cache work;
- both ready with a cursor change/event and `work+0x68` seeded above 1.0:
  event sees updated cursor and old cache; cache is stored afterward; continue
  through `0x001E9E48` and the `ldr r6,[r8]` at `0x001E9E4C`, stopping at
  `0x001E9E50`. Compare `work+0x68`, `r6`, stack, FPSCR, VFP state and all
  helper/event observations against original.

The existing 256-case reducer differential covers cursor/cache 0..3 and all
trigger masks, so a first adapter check need not repeat all of those through the
blend/touch tail. Once the shim's path mapping and continuation registers pass,
reuse that reducer matrix with the actual adapter to catch call-context
differences. Add one adversarial global-pointer mutation at an input/event hook
if the adapter reloads the slot after return; otherwise return the captured
pointer explicitly and verify `r4` uses that same pointer.

This bounded stop compares caller context through the first touch pointer
reload, not physical input, touch dispatch, real event queue effects, renderer,
later fade/transition branches, or a complete title runtime. Full callback
execution would require valid model/resource handles and task/fade state not
provided by this packet.
