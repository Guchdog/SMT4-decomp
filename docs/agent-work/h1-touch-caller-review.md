# Independent coordinator review — H1 touch caller candidate

Task: `h1-touch-caller-candidate`; bounded scan `0x001E9E4C..0x001E9EB8`.

## Result

**Pass for the bounded touch scan; integration remains partial.** I independently
decoded the pinned window and adjacent selection continuation, checked the
candidate's fixed-address helper type and reviewed the final runner/report. No
concrete mismatch was found in the tested scan behavior. This does not establish
physical touch behavior or make the helper a drop-in interior-PC replacement.

## Identity and behavior checked

- Pinned image SHA-256:
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Original 108-byte touch window SHA-256:
  `6bc78786fdb2b48d6f1be6db03aaf1e0ae781ced4ff40a512691c33f03bb311d`.
- Candidate source SHA-256:
  `a813c2b419ad04f1ad30fe22f3a0ce275e863bb74a7afec8226587edaf43d73e`.
- Candidate object SHA-256:
  `bd084591399def02af4c7b8851fb57bd0111020c63e758325ddb381655438c74`.
- Final report SHA-256:
  `df1a9ac4df8d553eb6759fa314b63edbdf3981743e5b53e6407cc1b6738c38fc`.

The pinned instruction slice confirms signed-halfword handle loads at work
`+0x74,+0x76,+0x78,+0x7A`, helper `0x0029D8FC`, first-scan state-1 selection,
second probe for each non-1 response and second-scan state-6 updates. I also
decoded the branch target `0x001EA014`: it stores the chosen index and resumes
at `0x001E9E8C`, the full state-6 scan. That confirms the candidate's control
flow of recording a first-scan selection and then always running the second
scan.

The runner scripts results only at the external helper entry, including values
that vary between repeated calls. Its seven directed cases and two negative
controls are implementer evidence; I inspected the recorded report and runner
logic but did not rerun compilation or emulation. The checker validated the
implementer handoff before this review.

## Limits and next action

The candidate passes a `void* work` argument and returns the final cursor,
whereas the original is an inline section that loads the work pointer through
`r8`, uses `r4/r6/r7` as scratch and continues in the surrounding callback.
The report correctly limits equivalence to work bytes, helper order and
arguments, continuation membership and selected ABI obligations. It does not
prove the next callback instructions receive equivalent live scratch state.
The helper implementation, coordinates/hitboxes, actual Azahar input, later
callback behavior and whole-game equivalence remain untested.

Keep this as a reviewed, bounded editable candidate. For integration, combine
it with the caller-context work that restores or reconstructs the state live at
the following callback instructions, then compare a wider original-versus-C++
window. Runtime touch acceptance remains pending.

## Evidence dimensions

- Compiled: passed by implementer; source/object hashes checked here.
- ARM differential: passed by implementer for seven directed synthetic helper
  sequences and two negative controls; not rerun by reviewer.
- Caller: partial, isolated inline window only.
- Runtime: not run.
