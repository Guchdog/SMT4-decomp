# H2 private Azahar movie input ordering review

## Scope

Independently review the private pinned Azahar H2 movie playback change in
`build/agent-work/H2-semantic/h2-private-azahar-source/azahar/src/core/movie.h`,
`movie.cpp`, and `citra_qt/citra_qt.cpp`. The change indexes the CTM input
records by controller/touch/sensor type and uses per-type cursors only for H2
observer playback. Its purpose is to prevent HID callback ordering differences
from shifting the single serialized CTM cursor and feeding the wrong event type.

The original record is
`E:/SMT4decomp/build/agent-work/H2-semantic/h2-private-azahar-diagnostic-cli-runtime/run-004/titleconfig-trace-original.ctm`.
It has the pinned SMT4 program ID and Azahar revision. Stock Azahar replay of
that file logged event-type order mismatches. The private binary was rebuilt
after the source change; its current SHA-256 is recorded in
`h2-private-azahar-source/h2-delivery-manifest.json`.

## Review constraints

- Read the listed source and task evidence only; do not edit the implementation,
  build, run tests, launch Azahar, or interact with emulator input.
- Check whether the per-type index preserves each input payload and cursor,
  whether replay termination is correct for unequal event counts, how exhausted
  types behave, whether activation is restricted to H2 observer playback, and
  whether save-state behavior is left safe or clearly bounded.
- Check the build/package manifest reflects the current source and binary.
- Return `accept`, `request_fixes`, or `blocked`, with concrete findings and a
  recommendation about whether the coordinator may perform an isolated runtime
  replay of the already-recorded CTM.

