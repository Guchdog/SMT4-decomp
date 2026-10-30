# Independent review: `0x0030A9A4` title entry candidate

## Result

**Recommendation: accept the bounded entry-function differential as useful
experimental evidence; continue with caller composition and integration review.**
The candidate matches the pinned body for the exercised inputs and explicit
dependency stubs. This does not establish save loading, title-state behavior,
or H3 milestone completion.

## Provenance and checks

- Pinned `extracted/exefs/code.bin` SHA-256:
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
  `config/game_info.json` and the differential report.
- Candidate source SHA-256:
  `0f493bfb8d26688e52f6ad49d13eeab56109b66ac4d0097f69a998b052928b5e`.
- Runner SHA-256:
  `4e9a4969659c1b6267a5058fb2ea27ce8eb3e07bafbe7e3dce71a457c22c9e9e`.
- Candidate object SHA-256:
  `db22370011ea12b41cd05781a942467353091c9e6b29b5ae79e84af0be0539d2`;
  its build manifest pins the source hash above and records ARMv6K, ARM state,
  hard-float VFPv2 flags. Extracted function bytes hash to
  `a2713b1ab89ad4e7f77a88a85601ec36e3677b472869f640ede1a216550dd278`, matching
  the report's `candidate_sha256`.
- Existing differential report SHA-256:
  `4acbf5f655bf9bae55ac14ae2ed6f8d34237c96569bf75d0b46be8e2b95684d0`.
- Re-ran `python tools/h3_title_load_entry_experiment.py` against the existing
  object; exit code 0. It reproduced all four cases and the detected wrong-offset
  negative control. No compiler or emulator was used.

## Independent inspection

Disassembly of the pinned 120-byte function and the extracted candidate agrees
on the relevant contract: call `0x00202950(0,0)`, load manager work at
`0x0044DE2C`, clear work `+0x14`, manager bytes `+0/+1`, and work byte `+0x49`,
set `+0x379`, call `0x002BF6D0(0x36,3)`, sign-load halfwords `+8/+0xA`, convert to
single-precision floats at `+0x38/+0x3C`, then clear `+0x49` and store 1/9 at
`+0x34/+0x50`. The original uses a pre-indexed store at `+0x34` followed by
`+0x1C` from the updated base; the candidate's direct `+0x34` and `+0x50` stores
are equivalent. Both preserve `r4-r6` and return through the saved link register.

The harness compares the entire `0x400`-byte work region and the manager's first
8 bytes, records the two dependency call addresses and their first two arguments,
and covers zero, signed min/max, negative, and positive halfword pairs with
poisoned initial work bytes. Since the greatest observed work offset is `+0x379`,
the compared work span includes every write in this function. The mutated `+8`
load reads a deliberately nonzero neighbor at `+6`, so the negative control is
meaningful.

## Limits and next action

The HLEs replace both dependencies; allocator/callback effects and invalid
manager/work/point pointers are outside this differential. The runner records
call order and `r0/r1`, but does not independently assert all callee-saved
registers, stack state, or caller-visible composition. Static inspection shows
matching save/restore shape for `r4-r6`, but caller composition remains untested.
No null/fault behavior, title state 7/8 transition, slot selection, save-file
read, destination scene, or runtime behavior is established. The report itself
does not carry a command/exit record; this review's rerun supplies that check.

Next: run the assigned offline caller-composition/interworking checks when their
runner and contract are available, then review that evidence before any scoped
runtime comparison. Keep `0x00202950` and `0x002BF6D0` as explicit dependencies;
do not describe this function as a reconstructed load operation.

