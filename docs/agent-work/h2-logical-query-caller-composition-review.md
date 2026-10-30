# H2 logical-query Calc caller composition: independent review

## Result

The pinned ARM call structure and the composition report agree on the claimed
query reachability. The composition is useful offline evidence that the typed
query bodies can be substituted on the exercised, directly seeded scenarios
without changing the measured caller outputs. The 43/43 `passed` result should
remain qualified, however: the runner compares runs to one another but does not
require the pinned baseline to finish without a fault or satisfy its saved ABI
state. As written, equal failure states could be counted as a match. This is a
runner/report gate to fix before treating `passed` as successful caller
execution; I did not rerun it.

## Pinned call-path review

The configured image is the pinned code image with SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` and text
base `0x00100000`. Static disassembly confirms the relevant `TitleConfig_Calc`
sites call the real dispatcher at `0x002C1830`:

- `0x001EAAB4..0x001EAABC`: mode 1, ID 9.
- `0x001EABD4..0x001EABDC`: mode 0, ID 4.
- `0x001EAC18..0x001EAC20`: mode 0, ID 3.
- `0x001EAC4C..0x001EAC50`: mode 0, ID 3 on the increment path.
- `0x001EAE5C..0x001EAE64`: mode 1, ID 0.
- `0x001EAF0C..0x001EAF14`: mode 1, ID 1.

The pinned wrapper at `0x002C1830` dispatches mode 0 through `0x002B902C`
and mode 1 through `0x002BFFBC`. Its fallback blocks are also real pinned
instructions: the `r6==4` path sends mode-0 ID `0xD` at `0x002C1960..0x002C1988`,
and the `r6==3` path sends mode-0 ID `0xC` at `0x002C19E8..0x002C1988`. Thus the
report's helper-entry pairs `(0,4)`, `(0,3)`, `(0,13)`, `(0,12)`, `(1,9)`,
`(1,0)`, and `(1,1)` match the pinned dispatcher and Calc callsites.

Selected report rows support the scenario mapping:

- `mode0-fallback-D` logs wrapper arguments `[(4,0),(4,0)]` and query entries
  `[(0,4),(0,13),(0,4),(0,13)]`.
- `mode0-fallback-C` logs `[(4,0),(3,0),(3,0)]` and entries including
  `(0,4),(0,13),(0,3),(0,12)`.
- `mode1-H2-ID9`, `mode1-ID0-positive`, and `mode1-ID1-positive` reach the
  corresponding mode-1 entries; the latter two also show the expected earlier
  Calc queries and, for ID 1, the ID-0 query.
- All seven required unique `(mode,id)` pairs are present in the observed set.

The report covers three candidate-vs-original comparisons per scenario:
candidate Calc with original queries, original Calc with typed queries, and
candidate Calc with typed queries. Each of the 43 rows records no difference
for these comparisons. It is more precise to describe this as one baseline plus
three candidate variants, rather than “four candidate combinations.”

## Observable keys and comparator caveat

`compare_runs` checks equality of `fault`, `stopped`, return `r0`, final PC,
the `preserved` tuple, work bytes, config bytes, deterministic service trace,
wrapper arguments, and helper-entry trace. The preserved tuple includes
`r4-r11`, SP, and `d8-d15`. Work and config are final-state bytes; the runner
does not compare the recorded general read/write address sets.

Two important success checks are absent from the caller-composition comparator:

1. It compares `fault` and `stopped` between baseline and variants, but does
   not require `fault is None` and `stopped is True`.
2. It compares preserved state between runs, but does not require it to equal
   `expected_preserved`, which `CalcMachine.run()` supplies. The separate
   `tools.h2_calc_experiment.compare()` enforces clean return and this ABI
   expectation, but the composition runner does not call that comparator.

Consequently `status: passed` establishes relative equality under these keys,
not by itself successful execution or ABI conformance. The report has no
per-row fault/stopped/expected-ABI values with which this read-only review could
independently resolve that caveat. A follow-up should add those absolute gates
to `compare_runs` (or record and validate them per run), then refresh the report.

## Candidate identity, controls, and provenance

The packet's 16 declared input hashes all match. The pinned code hash matches
the report reference. The report's external SHA-256 is
`8f2c088a3ece23930d648dbff68386662941493e31bb67b3a71e43d49a43522b`, matching
the packet. Candidate helper source hashes match the packet. I independently
extracted the named symbols from the recorded candidate and production object
files: mode 0 is 136 bytes, body SHA-256
`6d375730a5326520f907ac12c3928dafdcfb2d85dc1fefcc86f727ef1c662538`, and mode
1 is 68 bytes, body SHA-256
`0dfb38ba0a2c8384b0557230def99f875ad18866bc21a6eb5851b1ebf9f7fd8f`. Each
candidate body equals its production body and has no symbol relocations. The
mode-0 candidate retains the original `0x002C6C10` dependency.

The wrong-counter mode-0 helper is injected in the fallback-D case and the
report records `detected: true`. The runner determines this by a difference in
its caller comparison keys; the report does not preserve the specific differing
key. This is a useful sensitivity control, though recording the differing key
would make the evidence more diagnostic.

The JSON's embedded `report_sha256` is
`d3048a0f58f93846cddfbf2fb67109705f8a3619f0c4b335a7d44d10479935bf`, not the
final file hash. The runner hashes the first serialization, adds the digest,
then serializes again, so that field cannot be the final file's digest. The
packet and composition note correctly use the final external file hash above.

## Evidence limits and recommendation

The test is offline. It patches branches to synthetic helper locations and
seeds counter words directly from each scenario's requested logical outcomes.
It does not test the producer, counter freshness/scheduling, selector-zero
behavior, physical control meanings, event delivery, persistence, or a safe
input injection seam. Other Calc service boundaries use deterministic HLE; the
mode-0 helper still depends on the original `0x002C6C10`. No IPS/code image
integration or Azahar runtime result is claimed; runtime is `not_run`.

Recommendation: retain the static reachability, source provenance, body
identity, and relative-differential evidence as bounded offline evidence. Do
not treat the current 43/43 status as a complete successful caller gate until
the runner enforces clean returns and expected ABI state. Runtime and producer
questions remain open independently of that runner correction.
