# Independent review: H1 preview-readiness gate

## Outcome

**Pass for the bounded isolated candidate.** The candidate's fixed global read,
short-circuit order, byte widths/sign extension, helper pointer and result
polarity agree with the pinned `0x0025A2BC` instruction sequence. The report
supports the producer's 52/52 synthetic ARM differential and three detected
negative controls. This accepts an experimental function candidate only; it
does not establish helper-body, caller, runtime or whole-H1 equivalence.

## Independent checks

- Decoded the pinned 92-byte function at `0x0025A2BC` (22 ARM instructions).
  The primary byte at `scene+0xF2B` gates the secondary byte at `+0x1C`; either
  unset flag returns 1. The signed-byte load at `+0xD6D` returns 0 when
  nonzero. Otherwise the function calls `0x002BF9F0(scene+0xD74)` and returns
  1 exactly when `r0` is nonzero.
- The C++ uses the same branch order and offsets. Its helper type
  `s32 (*)(void*)` matches the pointer in `r0` and integer result consumed by
  the original. The function has no formal arguments and reads the fixed
  singleton slot `0x0043E278`.
- The focused report is pinned to reference SHA-256
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, says
  52/52 cases passed, and records three detected controls: wrong helper offset,
  reversed primary branch, and reversed helper-result polarity. The wrong
  offset control is caught by the observed helper argument even when the final
  boolean result happens to match.
- Verified the source, runner, unit-test and report hashes listed below against
  the current files. The provenance checker passed. These are producer-run
  compile/differential/test results; this review did not rebuild or rerun them.

## Evidence and limits

`compiled` and `arm_differential` are reported as `passed`; `caller` is
`partial`; `runtime` is `not_run`. The runner stops at helper entry and supplies
controlled signed return values. Thus it checks the gate's call ABI boundary,
not animation mutations, callbacks or lifecycle inside `0x002BF9F0`. Static
inspection of the H1 call site confirms a no-argument call and `r0` branch,
but the candidate was not substituted into the full callback. The nested
`scene+0xD74` object's live lifecycle and actual Azahar timing are unresolved.

Keep the candidate experimental. Before using it as an integrated replacement,
run the caller-context adapter experiment with the actual readiness call and
preserve the original runtime/helper boundary; retain the current limits on
the helper body and live scene graph.

## Frozen hashes

| Artifact | SHA-256 |
| --- | --- |
| Candidate source | `061591aaecbb30933fde1e31fe3f9a3c78ca4431aab53e7fb9d7558df83a3824` |
| Runner | `35214ab7dc1e8c7bdcbb07ceaddbb43ba66d0730f0049d281f3eca1f797eeb45` |
| Unit test | `c5e03ae58fb0342dc0b11574313c169045104fb349c1b5c1df50655ad5a304fc` |
| Differential report | `70a3c227f4a96381e0352002eac49b9df549e783bf8c264027a9392bd8f9c515` |
| Candidate object | `dd3741b683fc6841677b269643a103ad2e46df06d17eca4d1e26be8a2d4e4fb4` |

## Handoff

- Task: `h1-preview-readiness-candidate-review` (coordinator independent review)
- Outcome: pass for bounded candidate; no promotion claim
- Provenance: packet input hashes and `agent_workflow.py check-handoff` passed
- Next action: preserve as experimental source and consume only through a
  caller-context experiment; runtime/helper-body limitations remain open.
