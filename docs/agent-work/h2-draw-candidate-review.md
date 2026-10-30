# Independent review: H2 TitleConfig_Draw candidate

## Disposition

Accept the recorded 44-case result as bounded isolated differential evidence for its controlled fixtures. Do not promote the candidate or extend its supported cursor domain yet. The candidate has a signedness mismatch at the TBB table guard: original ARM uses an unsigned `bhs` branch after `cmp r7,#3`, while C++ uses signed `absolute_index < 3`. Negative absolute indices therefore take different paths. Either preserve the unsigned condition in C++ or establish from initialized caller state that negative indices are unreachable and explicitly constrain/test that domain.

## Source and contract review

I compared the candidate with the pinned contract and the recorded experiment. The original body is `0x002CAFD0..0x002CB75C` (1932 bytes), reference image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The candidate loads the work object through `0x0044E2D0`, ignores its callback argument, returns zero, and follows the documented row loop. It does not claim visible label, touch-action, or resource semantics that are not established by this body.

For the exercised nonnegative row indices, candidate helper ordering and arguments are consistent with the contract: common panel setup; cursor scroll/selection/count; row layout and renderer update; selected/inactive panel paths; table/format/font path under the index guard; row marker/touch handling; option lookup and common value panel; decrement/increment/special touch branches; then next row. The two panel wrapper forms carry four register arguments and the two stack arguments used at the original call sites. The font call passes color/string and the floating-point coordinates/scales in the documented order.

The renderer-cache update reads the render root through `0x0044EA00`, uses base `+0x1000+0x2AC`, loads the slot index, obtains the old slot at record `+8+4*index`, stores the `0x002C5FA4` result, conditionally calls the function pointer at `+0x1C` when the dirty byte `+0x18` is set or the value changed, passes the new value to that callback, then clears the dirty byte. This is consistent with the recorded original behavior and is included in compared cache bytes and ordered traces.

The candidate's ARM differential harness checks return/fault/PC state, helper and callback traces with arguments, work/config/cache bytes, callee-saved `r4-r11`, SP, and `d8-d15`. This covers the relevant ABI contract (original saves `r4-r11`, `lr`, and `d8`, restores on its normal exit, and returns `r0=0`) within the harness. The harness does not establish behavior of unresolved helper internals.

## Differential evidence inspected

The final report SHA-256 is `f34c83ae70b3528d1436900c0c0ac1a3ad43696ab37b6faee92f85f8e3b04b70`; it names reference SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, candidate source SHA-256 `651120294060d4bdf964f03918df89d19cc7a37bfa67c09e9eae263c77ce4b3c`, and runner SHA-256 `0a76b3bbf035fc1c3e70ef122086401a511740bbeb6bd1fbbfcd7b1a7091dea1`. The report records successful compilation, 44/44 directed cases, and a detected negative control compiled with the wrong TBB stride. The matrix covers zero and negative controlled row counts, active/inactive selected paths across row indices 0–2, touch results 1/2/6 for each row/decrement/increment/special region, and dirty/matching render cache paths. Four focused Python unit tests passed in the worker run; I also reran `python -m unittest tests.test_h2_draw_experiment -v` and observed four passing tests.

The matrix sets scroll to zero, so it does not exercise the signedness discrepancy. It also does not model real cursor/TBB/layout/format/font/panel/render/touch helper behavior: these are deterministic mocks. Thus it supports only isolated behavior under those explicit fixtures; no real caller, initialized runtime, Azahar, persistence, scheduler/calc interaction, user input, visible meaning, or whole-game equivalence is established.

## Required next action

Before broadening or promoting, change the guard to an unsigned comparison equivalent to the original (`static_cast<u32>(absolute_index) < 3u`) and rerun the focused differential matrix with an explicit negative absolute-index case and an index-3 boundary case. If preserving a narrower domain instead, provide initialized-caller evidence that excludes negative indices. After that, plan the bounded original-versus-patched draw-task comparison using initialized caller/resource state, with calc frozen and the same ordered helper/cache observations.
