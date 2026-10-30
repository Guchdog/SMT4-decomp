# H4 axis-reader caller-composition evidence review

## Scope and frozen provenance

Reviewed the frozen `h4-camera-candidate-composition-review/run-001` packet. All 16 declared input SHA-256 values matched. Reference code image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Candidate source SHA-256: `108b45003ec4908630514b615be7ebe6911fddb83c7448e4a8dacc403dd85aca`. Direct differential runner SHA-256: `312a2e27211cd3a53784a0b6d8bc918167aef3f71ec8732659d05b9a0f9d9a31`.

Caller report hashes: `caller-1fa948.json` `de560c54abf1704e1def81fa98bd1cc4dd4e0c077753cde35a7a24762f794d91`; `caller-1fe650.json` `490b7fd3ccf69519eade386e7c286f9423747aac3ce40addc0e8746229114fcd`. Candidate mutation report hash: `candidate-mutation.json` `e93876c62ae5183dfe7ecb28581015867ab92c59df5a4b5d7020d488ec15a12f`. The additional 119-case reports for seeds 42 and 73 have hashes `c8843b1f25768595aadb624c10593c12edb60d7997cdcab57d2ce07271c091a5` and `4a15f4e25816701adaa70ebda407a807a60866bddaf032f351d16c59e0b1f6c6`; both report zero differences and no first counterexample. No build or emulator was run during this review.

## Call-site and retarget audit

The pinned original instruction at `0x001FA948` is ARM word `0xEB02149E`. Decoding its PC-relative BL displacement (`PC = address+8`) gives target `0x0027FBC8`, consistent with the function record and runtime-observed call. Its captured call contract is `r0=SP+4`, `r1=SP`, `r2=0`, `r3=250.0f`, with view slot `0x00447E88`. These are adjacent output slots: `r0` is X and `r1` is Y, so the JSON's `stack_y_then_x` encodes Y first, then X. The report says the original helper `0x0019FE4C` is retained and execution stops at `0x001FAA84` after the stated window through `0x001FAA80`.

The report does not serialize the candidate mapping address, original/patched BL word, displacement, or patch-site bytes. The direct runner maps its candidate at `0x01000000`; **if** that same mapping was used for the caller report, the valid replacement word is `0xEB3815AC` (word displacement 3,675,564; aligned; within ARM BL's signed 24-bit word range), and the candidate can return through LR `0x001FA94C`. That establishes that the proposed retarget is representable, but it does not prove that this exact word was installed in the caller report's private copy. The artifact is therefore consistent with a bounded call-site replacement but lacks enough patch metadata for complete independent verification of the actual replacement.

## Case results

`caller-1fa948.json` reports six equal original/candidate cases. Each has equal helper return, stack outputs, `r6`, deadzone-call count, stop boundary `0x001FAA84`, and all 0x170 bytes of captured view prefix:

| Scenario | Reader outputs (Y then X bytes) | `r6` | Deadzone calls |
|---|---|---:|---:|
| Neutral | `00000000 00000000` | 1 | 0 |
| X positive above threshold | `00000000 9a99193f` (+0.6 X) | 0 | 0 |
| X negative above threshold | `00000000 9a9919bf` (−0.6 X) | 0 | 0 |
| Exact +0.5 X boundary | `00000000 0000003f` | 0 | 0 |
| Exact −0.5 X boundary | `00000000 000000bf` | 0 | 0 |
| Deadzone returns zero | sentinel `a5a5a5a5a5a5a5a5` (no output writes) | 1 | 2 |

`caller-1fe650.json` separately reports eight equal cases at a different UI-labelled caller window, including neutral, both X/Y signs, exact ±0.5, and deadzone-return-zero. It compares helper return, caller output bytes, two work floats, deadzone-call count, and stop at `0x001FE6B0`. This is useful second-caller evidence, but it is not the observed H4 field-camera call-site.

The report's uniform `0x11` view-prefix initialization with a `0x5A` marker indicates a synthetic memory fixture rather than the live view object sampled in the runtime camera probes. Thus byte equality is evidence for this initialized window and these cases; it does not prove behavior from the live camera object's full runtime state.

## Mutation control

The mutation report uses mode 1 and changes the candidate's unsigned upper-bound immediate from 1 to 0 at offset `0x30`. Original result: `ret=1`, output X `0.25`, Y `−0.5`, sentinel tail intact. Mutant result: `ret=0`, all output bytes remain sentinel; both reach the return sentinel. `detected=true` demonstrates same-mode mismatch detection and directly addresses the earlier input-only negative control. The report does not include the full config object or mutant object hash/bytes, so the exact mutated artifact cannot be reconstructed from this JSON alone; its core counterexample is nevertheless explicit and semantically consistent with the candidate's `max < mode` boundary.

## Evidence boundary and recommendation

This is a **bounded call-site instruction-window composition**, not execution of all of `0x001FA840`. The report supplies entry arguments and synthetic stack/view state, replaces the single helper call in a private copy, and executes the actual ARM call/post-call window to its stop. It does not establish the pre-call setup path, the complete task's unresolved dependencies/state, preserved general/VFP registers, FPSCR flags, complete memory write-set/fault equivalence, or physical input and rendered-camera behavior. The `0x001FE650` report is a separate bounded caller, not full composition either.

The two new direct runs add 238 synthetic cases across seeds 42/73, and the same-mode mutant control is detected. Together with the six-case field-camera window, this improves support for retaining the candidate as an experimental semantic reconstruction. **Do not promote it to production yet:** obtain reproducible caller-patch provenance (candidate address and patched BL word/hash), then add missing ABI/write-set/FPSCR limits or explicitly keep them out of the contract. Runtime observations that override original helper outputs remain independent of candidate validation. No evidence here establishes physical controls, player movement, visual camera effect, interaction, transition, or H4 completion.

## Read-only checks

- Verified 16/16 declared packet input hashes.
- Decoded original BL word at `0x001FA948` from pinned `code.bin`; computed target and candidate retarget displacement/bounds for the direct harness candidate mapping.
- Parsed all six field-camera cases, all eight secondary-caller cases, the mutation record, and both 119-case reports; compared reported results/equality fields and SHA-256 identities.
- Read candidate source, direct runner, caller sweep, and function record; no build, test rerun, candidate/harness edit, or emulator launch.
