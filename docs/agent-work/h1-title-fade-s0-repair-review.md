# Independent review — `0x00210030` s0 restoration repair

Task: `h1-title-fade-s0-repair-review`; owner: `h1_title_init`.

## Verdict

**Pass for the bounded repair under review; overall candidate remains partial.**
The pinned original restores the incoming fade to `s0` before the second helper
and restores it again after the third `object+8` reload, before the final gate.
The frozen candidate's compiled object follows those same register/dataflow
points: it reloads `s0` from saved `s16` before the second call, then reloads
`object+8`, restores `s0`, and only then reads `child+0x68`. The prior review's
specific early-return `s0` omission is fixed in the inspected object. The
candidate has no first counterexample in the supplied differential report.

This does not establish caller use of `s0` or `r0`, deeper positive helper
behavior, runtime behavior, or whole-function equivalence beyond the exercised
synthetic fixtures and original-code dependencies.

## Independent instruction and object review

The pinned image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
68-byte original body at `0x00210030` hashes to
`3f8d4d694b6de74559c6e2fc3ea7bf85e35ddc3e6d5cb13766501d16aa270161`.
Read-only Capstone disassembly confirmed this order:

1. Save `r4/lr` and `d8`; copy `r0` to `r4`; copy input `s0` to `s16`.
2. Load parent `+8` at `0x00210040`, call `0x002872A4`, restore `s0=s16` at
   `0x00210048`, reload parent `+8` at `0x0021004C`, then call `0x0020FFA0`.
3. Reload parent `+8` at `0x00210054`; restore `s0=s16` at `0x00210058`;
   restore `d8` and `r4/lr`; test signed `child+0x68`. `<= 0` returns with the
   child in `r0`; `> 0` falls through at `0x00210074` with the child in `r0`
   and the input fade in `s0`.

I independently disassembled the frozen candidate object
(`258db8e94623f5c41e68704836ddf9901da626ac43ac6150011b0d8b6b2df01a`); both
candidate symbols are present and the candidate symbol has no ELF relocations.
The relevant compiled ordering is `vmov s0,s16` before the second `blx`, then
`ldr r0,[r4,#8]`, `vmov s0,s16`, and `ldr r1,[r0,#0x68]`. Thus the candidate
passes the input float in `s0` at second-helper entry, and restores it on the
final-gate early path as well as before the positive tail branch. Its compare
uses `cmp r1,#1; blt`, which implements the same signed `<= 0` boundary as the
original `cmp r1,#0; bxle lr`; the separate wrong-boundary control uses
`cmp r1,#0; bmi` and is not equivalent at zero.

The new restore is after the third pointer reload, exactly as in the original.
The compiler also emits another restore on the positive tail path before
restoring saved registers and branching to `0x00210074`; this preserves the
same positive-continuation entry state. The candidate still deliberately calls
the pinned original `0x002872A4`, `0x0020FFA0`, and `0x00210074` bodies.

## Differential, hook and negative-control review

The runner's comparator now checks both returned `r0` and returned `s0`, as
well as memory, callback count, ordered calls/events, parent mutations, SP,
`r4-r11`, and `d8-d15`. The test hook writes `s0=0x41200000` at entry to
`0x0020FFA0`, after recording its pre-write value. In each S0-specific case
the hook sees `0x3f400000` and overwrites it with `0x41200000`. The final gate
is zero in the early-return case and one in the positive-continuation case.
The reported original and candidate return `s0=0x3f400000` in both cases;
reported `r0` values also agree: `0x02000400` on early return and
`0x02000A00` after the exercised positive continuation's initial zero guard.
The positive-continuation flag is false/true for those respective cases.

The hook is an external-entry seam: the S0 cases do not exercise the deeper
positive table/callback path inside `0x0020FFA0`. They establish restoration
across a call that clobbers `s0` at entry, with the helper's zero-gate body
thereafter; they do not prove which VFP registers the real deeper body changes.
The 15 directed cases cover signed gate boundaries and selected positive
paths. The first positive helper path uses an explicit synthetic `bx lr`
callback. The second positive body reaches only its first zero-field guard,
and the final positive continuation reaches only its first zero-field guard.

The negative control changes the last gate from signed `<= 0` to `< 0`. At
zero, the original returns early with `r0=0x02000400`, while the wrong version
reaches `0x00210074` and returns `r0=0x02000A00`; the report records
`calls differs`. This is a useful boundary control, not proof of deeper body
behavior.

## Provenance and evidence scope

All 14 frozen input hashes declared by this review packet matched at review
time. Relevant hashes:

- Candidate source: `e5c05eecd57c7b965ae4f2406d4770b32eb68d50a69c643eaa315104eaf717d6`
- Runner: `b3c5db172cb27b546dfb132ee0aee7295133e1c2234509151e9451169fce70f5`
- Focused test source: `cf9c0bed96aa6a7be739a5f62d89efa349a83efdae3f830eaa4e2abea62b75a8`
- Candidate object: `258db8e94623f5c41e68704836ddf9901da626ac43ac6150011b0d8b6b2df01a`
- Differential report: `3cc1ab7ae04b182fa972dc505ab26eb4c4bb53562914a9995dae471050a4fdd8`
- Unittest report: `703fae8530fd772d00f5e5579a4e9db4bf4b35b9b3a0fad68c67b660424c7c36`
- Implementation handoff: `ce7ad2fea0723ebd2c506cdeb7c29c7cc30b6fce415058284f5e26ef011fdc2d`

The producer reports compiled and ARM differential as passed; the reports
record 15 directed cases, two `s0`-clobber cases, a parent-pointer mutation
case, and the wrong-zero-boundary negative control. This reviewer did not
compile or execute the runner; I independently inspected the pinned ARM bytes,
existing candidate object, runner assertions/hooks, tests, and report hashes.
No candidate or test was changed and no emulator/runtime was used.

- Compiled: `passed` in the producer's frozen evidence; not rebuilt here.
- ARM differential: `passed` for the reported synthetic cases and compared
  state; no independent execution in this review.
- Caller: `partial`; actual caller consumption of `r0`/`s0` is unresolved.
- Runtime: `not_run`.

Recommended next action: keep this as a bounded experimental candidate and
retain the original helper/continuation dependencies. Assign actual caller
state-use and deeper positive helper-path coverage before claiming a broader
contract or promoting an integrated replacement.
