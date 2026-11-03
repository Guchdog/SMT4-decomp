# `0x002A8A8C` — decrement a bounded global halfword

## Scope and pinned image

This static contract covers all 36 bytes at `0x002A8A8C`, pinned from
`extracted/exefs/code.bin` with SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The
first 32 bytes are eight ARM instructions; the last word is a PC-relative
literal, not a ninth instruction. Packet input pins matched 11/11.

## Exact behavior and memory chain

The literal at `0x002A8AAC` is `0x0043DCB0`. The first instruction's ARM PC
value is `0x002A8A94`, so its `LDR [PC,#0x18]` loads that literal. Define
`G = 0x0043DCB0` and `P = *(u32*)(G+4)`. The function then sets
`r0 = P + 0x600` and loads a **signed** halfword `n = (s16)*(u16*)(r0+0x4C)`,
whose absolute address is `P + 0x64C`.

If `n > 0`, it stores the halfword `n-1` back at `P+0x64C`. If `n <= 0`, it
does not write memory. There is no saturation path beyond this positive-only
decrement, no global/object null check, no call, and no other memory write.
`r0` remains `P+0x600` and is the raw return value on every non-faulting path;
the function returns neither the counter value nor a success flag. The C++
interface should therefore express the raw pointer-sized `u32` result even
though the current H2 caller discards it.

Signed boundary behavior from the ARM `LDRSH/CMP/SUBGT/STRHGT` sequence:

| Stored halfword | Signed `n` | Write at `P+0x64C` |
|---:|---:|---|
| `0x8000` | -32768 | none; preserve `0x8000` |
| `0xFFFF` | -1 | none; preserve `0xFFFF` |
| `0x0000` | 0 | none; preserve zero |
| `0x0001` | 1 | write `0x0000` |
| `0x0002` | 2 | write `0x0001` |
| `0x7FFF` | 32767 | write `0x7FFE` |

The function does not alter bytes adjacent to the halfword. A future direct
differential should also vary the incoming raw `r0`, verifying that it is
ignored and replaced by `P+0x600`.

## ABI and faults

The routine has no prologue, stack access, or calls. It overwrites `r0` with
the returned `P+0x600`; `r1` contains the sign-extended halfword, or `n-1` on
the positive path. `r2`–`r12`, SP, and callee-saved registers are untouched;
condition flags are changed by the compare. There are no caller stack
arguments.

There are no pointer checks. An unmapped literal/code page faults during
instruction/data fetch; an unmapped `G+4` faults on the pointer load; an
unmapped `P+0x64C` faults on the signed-halfword read. Those cases have no
prior memory writes. If the counter read succeeds but the positive-path store
is unwritable, the store faults after the compare/decrement but still with no
earlier memory write. A null `P` is not returned as null: it attempts to read
address `0x64C`, which may fault or may be mapped. These are observed
instruction-level consequences, not tested runtime behavior.

## H2 caller sites and call multiplicity

The direct H2 caller is the six-slot status handling inside original
`0x002B85BC`. There are nine encoded call instructions to this service: two
conditional `BLEQ`s (`0x002B8634`, `0x002B8758`) and seven unconditional `BL`s
(`0x002B8644`, `0x002B8650`, `0x002B8658`, `0x002B86C4`, `0x002B8768`,
`0x002B8774`, `0x002B877C`). These are branch sites across mutually exclusive
paths and loops, not nine calls on every selector invocation.

For each slot in either of the two six-slot paths that use the status loop
(old profile active, or both profile flags zero), `0x002BF030` runs first and
the status byte is then examined:

- Status zero: zero service calls.
- Ordinary nonzero status other than 7, 8, or 9: one call.
- Status 8: three calls. The first call receives `r0=8`; it returns `P+0x600`,
  which becomes the raw `r0` input to the next two calls.
- Status 7 or 9: a conditional first call receives `r0=7` or `r0=9`, then
  caller code reloads the status byte. If the reloaded value is not 8, one
  final call follows with that reloaded value (two total calls when unchanged).
  If it is 8, three more calls follow: the first with `r0=8`, the next two with
  the returned pointer (four total including the conditional call).

The status-reload behavior matters: if the byte observed after the first 7/9
call is 8, control selects the three-call block. The callee writes only its
global halfword under the recovered contract; the code does not establish that
this location aliases the slot status, so any such mutation path remains an
assumption. Each call decrements the global halfword only while its current
signed value remains positive, so the call count can exceed the number of
actual stores.

In the new-profile route (old flag zero, new flag nonzero), each of the six
slots with nonzero status takes one call at `0x002B86C4` after the caller clears
that status byte; zero status skips the call. Here raw `r0` is the status
record base `object + 4*i` (the status value is held in `r1`), not the status
byte. This path has at most six service calls. The two later profile-record
calls at `0x002B86FC`/`0x002B8718` do not call this service.

The selector's outer H2 caller ignores the raw return. Exact natural execution,
profile selection, and whether the shared counter is positive are not
established by this static call graph.

## Bounded implementation and validation plan

A typed implementation can use a fixed global root address, volatile 32-bit
load at `G+4`, and volatile signed 16-bit load/store at `P+0x64C`; it should
return `P+0x600` as `u32`. Preserve positive-only signed behavior rather than
clamping an unsigned counter. Direct differential cases should test incoming
`r0` sentinels; signed values `-32768`, `-1`, `0`, `1`, `2`, and `32767`; exact
halfword-only writes; returned pointer; unchanged SP/callee-saved registers;
and read/write faults with zero pre-fault writes.

Caller composition should use explicit status/service hooks to cover zero,
ordinary nonzero, 7, 9, and 8 after `0x002BF030`; test 7/9 unchanged and mutated
to 8; verify exact per-slot calls, raw r0 values for successive repeated
calls, and both six-slot status-loop routes. Separately exercise the new-profile
clear-status path and verify one call for each nonzero status and none for
zero. Include negative controls for unsigned halfword comparison, decrement
at zero/negative values, a byte store instead of a halfword, wrong global
pointer offset, and returning the decremented count instead of `P+0x600`.

Only static disassembly and caller mapping were performed for this report. No
candidate, direct differential, compile, emulator, or runtime lifecycle was
tested; caller/service semantics outside the listed pinned code remain
unverified.
