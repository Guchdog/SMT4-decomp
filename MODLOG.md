# Semantic experiment field notes — 2026-10-24

The seven original leaf functions at `0x00128F34`, `0x002AE464`, `0x00394614`,
`0x0038143C`, `0x00381450`, `0x003D7228`, and `0x0037C46C` have non-byte-identical
typed ARM C++ candidates. Differential execution passed 144,004 function cases
across two seeds. Six deliberate defects were detected, including a byte cursor
alias/order bug and a callee-saved register violation.

The original `.text` page padding `0x003FE624..0x003FF000` is 2,524 zero bytes for
the configured private image. The compiled pilot fits in 144 bytes there. A local
250-byte IPS installs seven entry branches plus that code; independent IPS replay
and two original caller windows passed. Real-loader padding behavior and a full
game boot remain unverified. Core source/ledger and the user's original image are
unchanged. No patch was installed, uploaded or pushed.

See [the experiment report](experiments/semantic_equivalence/README.md) for
contracts, addresses, versions, hashes, commands, exclusions and next gate. Raw
images, object files and machine-readable run artifacts stay in ignored build/.

## Handoff: document, then pause

The user requested a reproducible procedure per function before stopping.
[Workflow](docs/function-reconstruction-workflow.md),
[template](docs/templates/function-reconstruction.md), and a
[completed function record](docs/function-records/0x00394614.md) document the
selection/contract/test/integration/commit gates and current tooling limitations.
This documentation step does not start new reconstructions, installs or runs of
the game. Further function work stays paused until the user resumes it.
