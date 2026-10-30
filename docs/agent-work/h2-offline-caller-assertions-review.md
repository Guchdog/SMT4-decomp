# Independent review: H2 caller argument assertions

## Review result

The added assertions address the earlier argument-coverage gap. The pinned
`0x002B8B78` body and the declared one-argument prototypes support treating
entry `r0` as the consumed sound/message ID while retaining incoming `r1-r3` as
diagnostics. The State-10 reset checks cover the arguments consumed by each
observed helper call site, and the focused negative test rejects a changed
touch-node argument. The frozen final report records three passing original vs
candidate cases and detects the wrong-callback control. This remains a bounded
offline caller result because the helper internals are still HLEs and Calc is
not scheduled or executed.

## Evidence checked

- All frozen input hashes in
  `build/agent-work/H2-semantic/h2-offline-caller-assertions-review/run-001/task.json`
  matched at review time.
- The implementation handoff identifies runner SHA-256
  `fdd87617dacb8d02288ae927b2268a8d4225c20c3e07a05a4b20b865b0619924`, test
  SHA-256 `c4dbb88fb87d6f8359c1d66ff1fbe277ecc1f29c52005664d2d96dded5e2cd11`,
  and final report SHA-256
  `7034452e1749da6bd3e4c18eccb32ea4ce4dcadb4db7afc25b4b470ffd960ad7`. Each
  matches the corresponding frozen packet input.
- The final report has `passed=true`, `case_count=3`, and `cases_passed=3`.
  Baseline and distinct-config cases each reach `[10, 10, 5]` on both sides;
  the `flag_7c` gate stays at State 9. Its wrong-primary-Calc-callback control
  mutates `0x001EA928` to `0x001EA92C` and is detected by the expected tuple and
  original-vs-mutant tuple checks.

## Sound_PlaySE `r0` allowance

`src/camp/title_flow.cpp` declares `void Sound_PlaySE(s32 se_id)` at
`0x002B8B78`; the initializer call loads `r0=0x99`. `src/ui/ui_runtime2.cpp`
also declares a one-argument `ScriptVm_SetMessageId(u32 id)` at this address for
the reset caller, which passes `0x9f`. The label differs between those source
contexts, but both signatures pass one word in `r0`.

The pinned body in `src/engine/leaf_batch32_c.cpp` begins with `mov r5, r0`,
preserving the sole incoming argument. The later `r1` value is loaded using a
PC-relative `ldr` before the body consumes it; there is no use of entry `r1` as
an argument. The runner asserts the observed `r0` sequence `[0x99, 0x9f]` and
keeps `r1-r3` in raw records. Its focused unit test changes the init record's
`r1` and still accepts the argument check, then changes `r0` and expects
`validate_reset_arguments` to reject it. This matches the pinned body contract;
it does not prove the callee's full sound/message side effects.

## State-10 reset assertions and negative test

The asserted expectations match the pinned `Title_ResetForBoot` call sites in
`src/ui/ui_runtime2.cpp`:

- `0x001EA3F0`: one-argument ID `0x9f`.
- `0x001EA3FC`, `0x001EA40C`, `0x001EA41C`, `0x001EA42C`: touch groups/nodes
  `(0x11,0x14)`, `(0x11,0x15)`, `(0x11,0x18)`, `(0x11,0x19)`; the helper
  declaration is `UiTouch_RegisterRegion(u32 group, u32 node)`.
- `0x001EA440`: cursor mode `2`.
- `0x001EA454`: decoded name `title/title_top.bcenv` and mode `0`.
- `0x001EA464`: resource handle `0xCAFE0088` and visible mode `0`.

The validator checks the exact call-site set, callee address at each site, and
the consumed register/string arguments. The unit test first accepts the
expected trace, then changes the second argument at `0x001EA3FC` from node
`0x14` to `0x15` and confirms the validator returns a consumed-argument
mismatch. Report traces show matching expected values at every listed site on
both original and candidate sides for both transition cases.

## Limits and recommendation

Sound, touch registration, cursor mode, environment load, and model visibility
remain matched HLE boundaries. The checks validate observed arguments and
registration/state effects, not those helpers' internal behavior. The runner
does not schedule or execute either registered Calc callback; it does not
establish Calc editing, State-1 input/UI, persistence or save behavior, profile
behavior, Azahar/RSP execution, or whole-game equivalence. The config cases
exercise initializer mapping/copy composition and do not validate mapper
candidates.

The updated caller evidence is suitable for the scoped State-9/10 initializer
composition claim under the declared HLE model. Keep the result experimental
and caller-scoped; it is not evidence for production integration or broader
Calc/persistence/UI behavior. This review was read-only and did not rerun tests,
compile, or interact with an emulator, RSP, or input device.
