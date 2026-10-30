# H2 private Azahar CLI dispatch fix

## Goal

Fix the pinned Azahar executable's top-level argument dispatch so movie and H2
observer options reach the Qt frontend instead of being mistaken for
compression short options. Preserve existing compression CLI behavior.

## Required changes

- Inspect `citra_meta/main.cpp` and `citra_cli/citra_cli.cpp`. Replace any
  `getopt`-based detection that scans long-option characters with exact
  compression-option recognition. Do not change compression option semantics.
- Add focused offline tests proving `--movie-record`, `--movie-play`,
  `--h2-snapshot`, `--h2-run-root`, and `--h2-user-dir` do not route to the
  compression CLI. Include positive controls for valid `-c`, `-x`, and `-o`
  compression options and negative controls for similarly prefixed strings.
- Confirm the wrapper's existing command line can pass through the dispatcher
  into Qt parsing. Preserve all previously reviewed movie validation,
  profile-integrity, and bounded observer behavior.
- Rebuild the private pinned `citra_meta`/Qt executable with at most two jobs,
  regenerate the feature patch/delivery manifest and report hashes, and return
  a structured handoff.

## Restrictions

No wrapper invocation, Azahar launch, actual staged-profile access, emulator
connection, debugger/RPC/network/firewall, guest write, save-tree access, or
host input automation. Runtime remains `not_run` until a fresh independent
review and separate coordinator runtime assignment. Edit only the private
Azahar build tree and the implementation report.
