# H1 state-5 navigation caller candidate: independent review

## Review result

**Partial; bounded reducer evidence is supported, raw continuation substitution
is not.** I independently inspected the pinned inline window, the candidate
source and object, the helper entry bodies, and the frozen runner report. The
candidate's helper order, valid-domain cursor updates, event-before-cache
ordering, timer/work changes, and pool layout agree with the bounded original
window under the runner's explicit helper hooks. The report is correctly
classified as compiled `passed`, ARM differential `partial`, caller `partial`,
runtime `not_run`.

The raw `R8` and `S17` differences are not only byte/register identity
differences. Both values are consumed after the comparison boundary at
`0x001E9DE0`, so a direct replacement that returns to the original continuation
would alter the later path unless an adapter supplies equivalent values or the
continuation is reconstructed. This does not invalidate the measured reducer
results because the runner stops before that continuation and does not claim
blend/touch behavior.

## Frozen input identity and bounded harness

Pinned `extracted/exefs/code.bin` SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
`config/game_info.json`. The reviewed candidate source hash is
`d1e0a1d0fb5276c44b6e2d7e0d8cf1bdd2e1f687979b1ace97a492071b9459ba`; object
hash is `58ad1ac87d89ff1fc95f6557622e88b3c6e1a1a5c734a1330848462487baa6bb`;
candidate symbol hash is
`fbf21e614edc27f79c146724d2ef4bad65dd43b403a83d3b9627ec5501def31a`.

The frozen report starts original execution at `0x001E9D08`, stopping at
`0x001EA62C` for either failed readiness gate or `0x001E9DE0` after both gates
pass. Candidate execution returns to a private sentinel. Only four helper entry
PCs are hooked: `0x00289924`, `0x0025A2BC`, `0x002B902C`, and `0x002B91C4`.
Thus tests provide explicit return/input responses and replace the event queue
boundary; this is not a physical-input or event-system test.

## Helper contracts and original instruction order

The pinned image decodes as follows:

1. At `0x001E9D0C`, call `0x00289924`; its body loads its own global at entry
   (`ldr r0,[pc,#0x50]` at `0x00289924`) and returns 0/1 in `r0`. The caller
   branches to `0x001EA62C` on zero. No input argument is consumed.
2. Only on script-ready does `0x001E9D1C` call `0x0025A2BC`. That body also
   loads its own global at entry, reads its readiness fields and returns 0/1
   in `r0`; the caller takes the same early exit on zero. No input argument
   is consumed.
3. After both gates pass, `0x001E9D2C` loads the global-work slot address into
   `r8`, `0x001E9D30` loads `1.0f` into `s17`, and `0x001E9D38` obtains the
   work pointer into `r4`. It increments binary32 timer at work `+0x64` before
   querying input.
4. `UiInput_Trigger` at `0x002B902C` takes logical ID in `r0`, and its body
   returns a boolean-style integer. Previous IDs are 5 then `0xE` only if 5
   is false; a true result decrements work `+8`. Next IDs are 6 then `0xF`
   only if 6 is false; a true result increments `+8`. The next pair runs even
   after the previous pair, so opposite directions can cancel in one update.
5. At `0x001E9DAC..0x001E9DC0`, the original performs word arithmetic for
   signed-remainder-by-four normalization. The report's `previous-primary-wrap`
   case initializes cursor 0, takes the decrement path to provisional `-1`,
   then compares the candidate and original result 3. The separate wrong raw
   signed-modulo function returns `0xFFFFFFFF` for `-1`, so the negative
   control is rejected for the intended distinction. Values outside the
   tested 0..3 input domain (apart from the reached provisional -1) remain
   unvalidated.
6. The normalized cursor is stored at work `+8` before comparison to cache
   `+0xC`. If equal, the event call is skipped. If different, the original
   loads event ID `0x0100016C` from its literal at `0x001E9DD0`, calls
   `0x002B91C4`, then reloads and stores the cursor into `+0xC`. The event
   helper takes the ID in `r0`; inspected body reads and writes its queue using
   that ID and has no caller stack arguments. Runner hooks record event ID and
   cursor/cache at call time; the candidate preserves event-before-cache order.

The candidate uses matching C++ function-pointer signatures: no-argument
readiness predicates returning `s32`, `s32(u32)` trigger query, and
`void(u32)` event request. These signatures match the values consumed by the
original entry bodies and call sites. The event helper's internal queue state
is outside the isolated comparison.

## Ordering, normalization, and tested domain

The original body and candidate both delay the global work lookup/timer update
until both readiness checks pass; the readiness false paths skip the remaining
helpers and all candidate work changes. The candidate then increments timer,
processes previous aliases with short-circuit priority, processes next aliases
in sequence, normalizes, writes cursor, compares cache, requests event if
changed, and writes cache after the event call. This matches the decoded
`0x001E9D2C..0x001E9DDC` order.

The frozen report records three readiness cases, ten directed cases, and 256
cases for cursor 0..3 × cache 0..3 × 16 trigger masks. All cases pass its
behavior predicate; all 256 valid-domain cases pass the same predicate. That
predicate checks no faults, expected stop/return-sentinel membership, helper
order, event ID/call-time cursor and cache, work-block equality, untouched
bytes, stack pointer and FPSCR. It deliberately reports `passed_full_state`
separately. The two direction pairs, alias winners, net-zero combinations,
changed/unchanged cache, timer and `0xA0` work-block effects are therefore
covered in the synthetic bounded domain. No result establishes held-input
filtering, logical-to-physical key mapping, genuine readiness return timing, or
queue-side effects.

## Literal pool and compiled object inspection

The candidate symbol is 248 bytes; its code region is 232 bytes followed by a
16-byte literal pool at `0x010000E8`. Four contiguous word references land at
`0x010000E8`, `0x010000EC`, `0x010000F0`, and `0x010000F4`; the words represent
the two readiness helper addresses, float `1.0`, and trigger helper address.
The event helper address is formed as `trigger_address + 0x198`, matching
`0x002B91C4`. The unconditional branch at `0x010000E4` targets
`0x0100009C`, which skips the literal bytes while returning into the
normalization path. The object has no relocations for this symbol. This agrees
with the runner's pool validator; it does not establish production link or
integration behavior.

## R8/S17 continuation deltas

At the original continuation `0x001E9DE0`, original `r8` is `0x0044E300` and
original `s17` is `1.0f` (`0x3F800000`). With the report's input seed, the
candidate preserves callee-saved `r8=0x88888888`; its preserved `d8` is
`0x1122334400000008`, so its `s17` half remains `0x11223344` instead of 1.0.
The candidate meets normal C++ callee-preservation behavior, but the original
is an inline window that intentionally leaves these values changed.
The report's first such state counterexample is `both-ready-no-input`: the
reducer's memory/helper behavior matches while `passed_full_state` is false.

These values are live beyond the boundary: original `0x001E9E30` copies `s17`
into `s1` on the `timer > 1.0` branch, and `0x001E9E4C` reloads the work
pointer through `[r8]` before touch polling. Therefore they block both raw
interior-PC substitution and any claim that the current helper can resume the
original continuation with equivalent blend/touch behavior. They do not refute
the report's measured reducer outputs because that harness stops at
`0x001E9DE0` and its behavioral predicate excludes callee-saved/VFP register
deltas. An integration adapter or inlined reconstruction must reproduce the
live continuation values; a return status from the candidate is not an
equivalent original callback return value.

Other scope limits: the original event request is stubbed at its entry; the
candidate never runs blend, touch, help text, fade, or dispatch; no emulator
or runtime test is present; the exhaustive cursor/cache set is 0..3, not all
possible corrupt work states. The candidate is suitable only as a bounded
reducer proposal pending a caller-context solution for the live continuation
state and an integrated comparison.
