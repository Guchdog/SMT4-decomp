# H2 logical query JSONL fix

## Change

Fixed `logical_query_return` serialization in the private H2 observer. The
`entry_seq` field no longer receives an extra quote before `thread_id`, and the
`lr` string now closes before `result`. Each return row is valid JSONL again.

Extended the focused C++ observer test to parse every nonempty line emitted by
the five-query scenario with the bundled nlohmann JSON parser. It checks all five
entry and return rows for event type, sequence, PC, guest thread ID, control ID,
mode, SP, LR, return address, entry sequence, and result, and parses/checks the
terminal `complete` row. The scenario has 11 JSONL records total.

## Validation and pins

- Observer harness compiled and passed with the parser-backed assertions.
- Private `azahar.exe` rebuilt under `build-clang64` with `--parallel 2`; the
  subsequent build check reported no work to do. No Azahar process was launched.
- `python -m unittest test_h2_live_preflight -v`: 19 tests passed.
- Regenerated the feature patch and delivery manifest. An independent package
  verifier checked all 30 binary, feature, shim, and patch hash entries.
- New executable SHA-256: `1bec8c3fef5b794e0abfe4bbbc1870202c562bb35ef3e49648b1d09060f8e6f1`.
- Delivery manifest SHA-256: `f3d7cce444ffb3406491ee6767c9daa2ad99a44d6a3b7a0de1a7add4b2b0be91`.
- Feature patch SHA-256: `7b0cc890c94e07217574e2c17dd631670734e6a60758f3d6d64e210e8226d3b1`.

## Limits

The JSONL format and focused observer behavior are validated offline. No live
Azahar capture was run, so this is not runtime input or profile-equivalence
evidence. The previously reported CTM fixture failures were outside this fix's
focused validation and the CTM path was not modified.
