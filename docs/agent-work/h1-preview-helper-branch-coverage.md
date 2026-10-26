# Preview helper branch-coverage extension

Task: `h1-preview-helper-branch-coverage`; owner: `h1_title_fade`.

## Result

The isolated original-versus-candidate matrix now contains 21 cases (13 prior
fixtures plus 8 added branch cases). All 21 pass. The existing compiled
negative control still detects omission of the disabled-sequence `+0x86`
completion store through the endpoint case's `r0` and memory differences. No
first mismatch occurred in the extended run.

Added cases cover:

- `+0x04 == 0` with negative `+0x08`, which continues, and signed extremes:
  minimum/minimum returns early; minimum/maximum continues; maximum/minimum
  continues without consulting the second gate.
- Both direction-1 endpoint paths: row mode zero and nonzero.
- Direction-1 interpolation with reversed signed coordinate deltas.
- The next sequence entry `-3` completion sentinel.

The original candidate body is unchanged. The compiled linked candidate ELF
hash is the same as the previous run.

## Validation and identities

Pinned `code.bin` SHA-256:
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Pinned helper-body SHA-256:
`9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e`.
Unchanged candidate source SHA-256:
`64c3964b0abae2c0ff6e51d1e9ef5961c8e8d0769e177c528a878d4b094b3282`.
Linked candidate ELF SHA-256:
`8c5dbdc24e7b86652f3c6604f3c830758c83aa1ddfbfc73f365eaa708decf33b`.
Extended runner SHA-256:
`adf2647b43b72469f516936f0c875ccc470e89c12df51b82f5fed5454b44f4b3`.
Focused test SHA-256:
`04f5d8a2c712dbaa8addca5d4fc104ce3c7bbbcb947fce34d738ffd7825fbdf6`.
Report SHA-256:
`31f961f48cc54d4e615d9d48347fe672bda71313d9d503082650a768fdae6b81`.
The report and linked object are under
`build/agent-work/H1-semantic/h1-preview-helper-branch-coverage/overnight-20261025-preview-helper-coverage/run-01/`.

Commands and exits:

- `python tools/h1_preview_helper_experiment.py --output build/agent-work/H1-semantic/h1-preview-helper-branch-coverage/overnight-20261025-preview-helper-coverage/run-01` — exit 0, 21/21.
- `python -m unittest tests.test_h1_preview_helper_experiment -v` — exit 0, 2 tests.

The first mismatch is none: every original/candidate projection matched in
the 21 reported fixtures. The negative control produced the expected mismatch
(`r0 differs`, `synthetic memory differs`) when the `+0x86` store was removed.

## Evidence limits

The original helper and linked candidate are compared under the same five
explicit stub boundaries: animation `0x002BDAC0`, interpolation `0x002C615C`,
and common-tail calls `0x002B1FC0`, `0x002B1DFC`, and `0x002B1C8C`. The
interpolation stub returns signed delta/duration (or zero for zero duration);
the other stubs return zero without original side effects. The fixture
comparison covers `r0`, callee-saved registers, SP, FPSCR, direct stub-call
arguments/order, and the full synthetic data mapping. It does not validate the
real callee bodies or transitive effects.

The rows and sequence entries are synthetic and valid for the selected
indices. The helper's unchecked invalid-index behavior, nested pointer
lifecycle, H1 `scene+0xD74` initialization, real caller binding, and runtime
behavior remain unknown. This is expanded bounded synthetic evidence only;
there was no emulator, caller integration, production change, or full build.

Next action: review the expanded local branch matrix, then recover the actual
callee and H1 object-lifecycle contracts before a caller-level experiment.
