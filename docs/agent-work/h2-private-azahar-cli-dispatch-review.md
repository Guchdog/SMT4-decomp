# H2 private Azahar CLI dispatch: independent review

## Decision

**Accept the bounded CLI dispatch fix for a separately assigned runtime retry.** The actual `main.cpp` pre-router calls the reviewed manual scanner; the scanner ignores long options and routes declared short compression options. The focused harness links the exact `citra_cli.cpp` implementation used by that call, verifies H2/movie flags do not trigger compression parsing, and checks compression positive controls and the no-compression return path. No runtime claim follows from this review.

## Source and test review

- `azahar/src/citra_meta/main.cpp:63-65` calls `CheckForOptions(cli_capture_optstring, argc, argv)` and enters `ParseCommand` only when it returns true. Otherwise it proceeds through normal room/Qt routing (`:67-81`).
- `azahar/src/citra_cli/citra_cli.cpp:16-47` is the actual manual pre-dispatch implementation. It skips non-short and single-dash-empty args; double-dash long args are ignored, and `--` ends the scan. For single-dash arguments it checks characters against the supplied declared option string and recognizes only `c`, `x`, and `o`; options taking a value support attached and separate forms. `ParseCommand` repeats the narrower compression-option check and returns `1` without invoking `ParseCompressionCommand` when no compression short option is present (`:49-54`). `citra_cli.h:7-11` keeps both option strings as `c:x:o:` and exposes those functions.
- `tests/test_citra_cli_dispatch.cpp:34-64` uses the real `CheckForOptions` and `ParseCommand` linked from `citra_cli.cpp`, with only the compression-parser function stubbed for call counting. It checks `--movie-play`, `--movie-record`, H2 flags, similarly prefixed long options, and `--c` are not compression options; it checks `-c`, `-x`, `-o` and attached `-cVALUE`/`-xVALUE`; it confirms compression parser dispatch for valid cases and return `1` without parser calls for movie/long-only cases. An explicit zero-extra-argument `ParseCommand(argc=1)` case is not present, but the no-compression return path is exercised with long-only argv.
- The H2 long options remain available to the Qt parser after the pre-router returns false; the feature patch adds the scanner change as a source diff. The report and test exercise the dispatch logic, not the `main()` function as a whole or the real Qt frontend.

## Provenance and evidence

All `input_sha256` entries in the prepared review packet matched. Every `feature_inputs` hash in the delivery manifest matched the current private source/artifact. The feature patch hash is `5cd60eb058efc02a6d5035031dd6fa18bc4132ef5dec4249ef77d82a306585b5`, matching the delivery manifest and fixes report. The built Azahar binary is 55,287,296 bytes with SHA-256 `c1a3d847e48c0839059c3809b8e147cc027f20c2b342d875c13ee20d66a9c308`, matching the delivery manifest and report. The saved report pins Azahar to `219d743a1e698101fe1ab8bef43e6563126c3c27`.

The fixes report records that the standalone dispatch harness compiled and passed, the Qt binary rebuilt in three steps, and packaging completed, all with exit 0. Those are saved implementation claims and were not rerun by this reviewer. Compiled evidence is recorded as passed; ARM differential, caller, and runtime evidence are `not_run`. No wrapper process, Azahar launch, or profile access was performed. H2 remains open pending scoped runtime capture/comparison.

## Review execution and limits

Read-only packet/source/report inspection and SHA-256 checks only. No build/test, wrapper invocation, emulator, profiles, debugger/RPC/network, or input automation. Commands used were PowerShell `Get-Content`, `Select-String`, `Get-FileHash`, and `Get-Item`; all completed successfully. The private application was not launched, so this review cannot establish that the full Windows Qt startup path receives the H2 options or selects the staged profile at runtime.

## Next action

Coordinator may accept this dispatch fix and assign a separate guarded runtime retry. Verify the runtime command reaches the Qt frontend with `--movie-play` and H2 flags, keep the verified input/profile/image identities fixed, and treat output completeness and actual guest capture as separate evidence. Do not treat this review as H2 completion.
