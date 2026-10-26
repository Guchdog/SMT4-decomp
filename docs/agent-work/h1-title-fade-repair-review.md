# Independent review — repaired `0x00210030` title fade front gate

Task: `h1-title-fade-repair-review`; owner: `h1_menu_map`.

## Review verdict

**Partial; the pointer-reload and return-`r0` repair is supported for the tested
front-gate domain, but the harness does not compare `s0` at return.** Do not call
this a complete replacement or caller-validated implementation. The repaired
candidate resolves the two concrete issues from the prior review: the compiled
object has all three independent `object+8` loads, and the comparator now checks
`r0` on both early-return and positive-continuation paths. One additional
caller-visible state difference remains unmeasured: the original restores the
incoming `s0` before its final test on every path; the candidate's compiled early
return after the second helper does not restore `s0` if that helper's positive
body clobbers it.

## Independent source, object and original inspection

The pinned reference image is SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
The original 68-byte entry at `0x00210030` hashes to
`3f8d4d694b6de74559c6e2fc3ea7bf85e35ddc3e6d5cb13766501d16aa270161`.
The independently decoded ordering is:

1. Save `r4/lr` and `d8`; copy object `r0` to `r4` and fade `s0` to `s16`.
2. Load parent `+8` at `0x00210040`, call `0x002872A4` with object in `r0` and
   fade in hard-float `s0`.
3. Restore `s0=s16`; reload parent `+8` at `0x0021004C`; call `0x0020FFA0`.
4. Reload parent `+8` at `0x00210054`; restore `s0=s16`; restore saved state;
   compare signed child `+0x68` with zero. `<= 0` returns with child in `r0`;
   `> 0` falls through at `0x00210074` with child in `r0` and fade in `s0`.

The object contains both `candidate_00210030` and the wrong-boundary control,
each 96 bytes with no ELF relocations. Independent disassembly of the repaired
candidate confirms the three loads at object-relative instructions:
`ldr r0,[r0,#8]`, then `ldr r0,[r4,#8]` before the second helper, then another
`ldr r0,[r4,#8]` before the final `+0x68` gate. The mutation evidence aligns
with these use points: the first callback changes parent `+8` from
`0x02000400` to `0x02000600`; the second-helper entry receives the already
loaded `0x02000600`, then mutates parent `+8` to `0x02000700`; the final
continuation receives the third load, `0x02000700`.

The candidate's compiled early path preserves the loaded child pointer in `r0`
through its epilogue. Its positive path restores `s0=s16`, restores `d8` and
callee-saved registers, then tail-branches to `0x00210074` with `r0=child`.
The original does the same at the front-gate boundary. The test report records
`r0=0x02000400` for early cases and `r0=0x02000A00` after the exercised positive
continuation's initial zero-guard return. `_difference` compares `r0` directly,
and the unittest requires a `return_r0` result for every directed case. The
wrong `<=0` versus `<0` control is rejected at a zero final gate: it reaches
`0x00210074` and returns a different `r0`.

## Remaining finding: `s0` on the early return

The original executes `vmov.f32 s0,s16` at `0x00210058` before its final gate,
so it restores the input float even when it returns early. The candidate object
does execute `vmov.f32 s0,s16` on the positive tail path, but its final-gate
branch to the early epilogue goes directly to `vpop {d8}; pop {...,pc}` without
restoring `s0`. `s0` is caller-saved under AAPCS, so whether this difference is
contractually important depends on the real caller; the original's explicit
restore and the unresolved title caller make it a question that should be
measured before claiming full caller-state fidelity.

The runner snapshots `s0` in `_execute`, and records helper-entry `s0`, but
`_difference` does not compare returned `s0`; case rows do not serialize it.
Moreover, positive `0x0020FFA0` coverage stops at its `+0x148 == 0` early guard.
Its deeper body at `0x0020FFAC` performs VFP operations and calls an indirect
callback, which can change `s0`; that caller path is not exercised. Thus this
review cannot say the saved test cases produce an observed `s0` mismatch, only
that the candidate has no explicit restoration for a clobbering second-helper
path and the comparison would not catch one.

Recommended next action: either (a) add an assertion for returned `s0` and an
adversarial second-helper positive-body case whose callback changes `s0`, then
restore the original value if that is part of the caller contract; or (b) obtain
caller evidence showing the value is dead on the early return and explicitly
limit the contract to AAPCS caller-saved behavior. This reviewer did not edit
the candidate or run the emulator/compiler.

## Coverage and evidence limits

- The runner executes the pinned original gate/helper bodies, except the one
  explicit callback fixture at `0x01001800`, whose bytes are `bx lr`. The
  parent-pointer mutations at callback/second-helper entry are synthetic seams,
  not observed game bindings.
- It tests 15 directed gate values, signed low/negative/zero/positive/high
  boundaries, a positive first-gate callback, the second gate's positive body
  only to its initial zero-field guard, and the positive final continuation
  only to its initial zero-field guard. The deeper second/final callback graphs
  remain untested.
- It compares data-region memory, event/call records, callback count, `r0`,
  `r4-r11`, SP and `d8-d15`; it does not compare stack bytes or returned `s0`.
- Synthetic ordinary-RAM fixtures provide no runtime-normal object graph,
  physical title caller observation, Azahar result, or whole-game evidence.
- The previous review's stale pointer-reuse concern is fixed in this object;
  its stale claim that `r0` was not compared is also fixed. Remaining deeper
  body, caller, and runtime limits are explicit in the candidate report and
  function record.

## Provenance

- Source SHA-256:
  `7aab6d7fe6b0625e45d295971ab88ef4a76f8340174b82187052a2941a18605a`
- Candidate object SHA-256:
  `046afdbb59f341d92649a3c8405d779d2a40a2cf10be5024eae106c6b663512b`
- Repair run report SHA-256:
  `91ef5b5975745301972b549044543de9b65a3b1f7368350c34bc8a80f52d6b42`
- Final unittest report SHA-256:
  `5c61bf906319fc93d8e2585b156c9576258b92be04cc1eea2d63ae2ad9af7da4`
- Test source SHA-256: `fd256f3eed31b442ec65f50b7cef5501345447e1481210db7727dfdaef710666`
- Runner SHA-256: `932f423f81951bd2fecea65dfc2a865d0c5178904dc7dc7fe6eec2f7f980bd27`
- All declared packet input hashes were independently checked and matched.
- Read-only Capstone inspection of the existing ELF object and pinned original
  completed successfully. No build, test rerun, candidate edit, or emulator
  operation was performed for this review.

## Evidence classification

- Compiled: `passed` in the implementation's frozen report; not rebuilt by this
  reviewer.
- ARM differential: `partial` for review purposes. The implementation reports
  pass for the tested memory/r0/register domain, but the returned-`s0` omission
  and bounded positive-body coverage remain.
- Caller: `partial` (static call-window contract only; no real caller test).
- Runtime: `not_run`.

The task review is complete; independent promotion approval is not given. Resolve
the `s0` return-state contract or record it as an accepted caller-saved limit,
then assign separate bounded coverage for the deeper positive helper bodies.
