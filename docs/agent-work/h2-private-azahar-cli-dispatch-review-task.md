# H2 private Azahar CLI dispatch: independent review

## Goal

Independently review the fix for the real runtime blocker where movie and H2
long options were misrouted to the compression CLI before Qt startup.

## Required review

- Verify the failed runtime report's exact observed error and the current
  dispatch implementation in `citra_meta/main.cpp` / `citra_cli/citra_cli.cpp`.
- Confirm `CitraCLI::CheckForOptions`, as used before `LaunchQtFrontend`,
  recognizes only genuine declared compression short options. Long flags
  `--movie-play`, `--movie-record`, `--h2-snapshot`, `--h2-run-root`, and
  `--h2-user-dir` must pass through to Qt; they must not trip getopt by
  containing `c`, `x`, or `o` characters.
- Verify compression short/attached forms remain routed correctly and that
  `ParseCommand` cannot fall through without a defined return value.
- Inspect the focused test and verify it invokes the exact implementation used
  by the top-level pre-router, checks no compression parser call for H2/movie
  long flags, and has meaningful positive controls for `-c`, `-x`, `-o`.
- Verify current feature patch, delivery manifest, binary and report hashes;
  compatibility patches remain separate; no wrapper/emulator runtime evidence
  is claimed.
- Recommend `accept`, `request_fixes`, or `blocked`. Acceptance authorizes only
  a separate coordinator-owned runtime retry; it does not itself launch Azahar
  or prove runtime behavior.

## Restrictions

Read-only review. Do not run builds/tests, invoke the wrapper, access staged
profiles, launch/connect to Azahar, use debugger/RPC/network/firewall, write
guest memory, access user save trees, or automate host input. Write only the
assigned report and structured handoff.
