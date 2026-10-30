# Independent review: H1 title-message production-source bridge

## Verdict

**Partial evidence is verified; the H1 caller bridge is not active in compiled source.** The exact `src/camp/title_message.cpp` TU was compiled and linked with a private manager definition, and the run-04 report records 10/10 bounded original-ARM versus candidate comparisons plus 4/4 candidate-only safety controls. The two migrated state-2/state-5 expressions are inside the `#if 0` readable draft of `ui_func_001e989c`. They do not make the running callback call this bridge. The review therefore supports the helper TU's bounded differential, not production integration, caller activation, or runtime behavior.

## Reproducibility and source/build checks

All 15 frozen inputs in the review packet matched their SHA-256 values. The source identity reported by run-04 matches current `src/camp/title_message.cpp` (`e7bd555a79858d546de1ad3fe6cfbbd8199a7ebe98e4d12067898a4395ef50f2`); its header hash is `92b957ee845ff66061b44264da4e64f1d17068a3aaa5c57f9ca036e229e8ac4f`. The exact production TU path is present in the compile command, and the source object hash matches the file on disk: `01517415d64f4e7b1be583ff9f4460dd2556591e4f49be0989f3452c66eb2f35`. Its private linked ELF hash is `9ba1a4df8399ac81a76e0a00c8e5d731c57851face19505f7e76c1852a94f185`; extracted candidate text hash is `fd0849bc72a3cb939003ce291a5a251d254c3b1f6e2d6a0f763162b6afc507ed`. Both source compilation commands and the private link command recorded in report exited 0. The link used `--no-undefined`; the ELF's defined symbols are the H1 entry and typed test manager, and its undefined-symbol list is empty.

`CMakeLists.txt`'s recursive `src/*.cpp` glob includes `src/camp/title_message.cpp` after CMake reconfiguration. This proves source discovery, not that a canonical project build or final game image was linked. The candidate ELF is a focused private test link, not the project static library or a game executable.

The exact source hash for the legacy body is unchanged at `src/engine/leaf_batch33_c.cpp` (`9235d238d06faa5e5fa52f18037302c2adc402d764c42d11147405906b75072c`). The shared copier source is unchanged at `src/engine/leaf_batch37_c.cpp` (`3199e5a1eb3e7b46e2273bb3eb6696b0556ea9d8da9ad6259fa26eb2a785a717`), and `config/functions.csv` remains at `b27580ea4af85889e1167e7af5f898f66e82517c0293fcc3a586fea504a94be8`, retaining the existing ledger labels/ownership. Run-04's integration checks record these same hashes and report all checks true. The new bridge entry is a separate `H1_SetTitleHelpMessage` symbol; it does not alias or replace either ledger-backed helper.

## Callsite activity finding

`src/ui/ui_runtime2.cpp` has exactly two occurrences of `camp::H1_SetTitleHelpMessage`, at the state-2 and state-5 draft sites around lines 3975 and 4177. Both occur after the `#if 0` at line 3909 and before that block's closing `#endif`; the active-source scan in the runner removes `#if 0` blocks and finds zero active bridge calls. The runner independently records `h1_calls_in_disabled_callback_draft=true` and `active_source.count(...) == 0`. The old `Camp_SetSlotMessage` call around line 1265 also remains only in a disabled non-H1 draft. No other active source callsite for the new API was found.

Consequently the existing compiled `ui_func_001e989c` remains the naked ARM callback. The tests that call the helper TU directly do not execute that callback or its TBB getter/caller arithmetic. The work changes only the readable draft expressions; it does not yet migrate live state-2 or state-5 dispatch.

## Differential and control review

Run-04 report SHA-256 is `2768b2b605bdd3503f6783b0e15bd35d33330c68e8ab1ecd8abd9f9bd9147b4b`; companion `integration-checks.json` SHA-256 is `6923b7ac86cce23218c84f10b4fda1951c315a7409aead7115d011df2eba5cd8`. The report records all ten valid-domain cases passing, and I checked the case entries and current artifact hashes without rerunning them:

- Four real strings from the frozen 880-byte `TitleTable.tbb` (`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`) at file offsets `0x46`, `0x9C`, `0xF2`, and `0x148`, lengths 36, 39, 25, and 28. Each has matching original/candidate `r0=1`, full data projection, and ButtonHelp work hash.
- Null reset: original and candidate `r0=0xFF`, matching full data/work projections.
- Empty non-null string; one line of 64 data bytes plus NUL; two lines with a NUL at input scan index 127; high-bit content; and a leading newline. Each has matching defined return, full data and work projections, stack, preserved registers, VFP registers, and FPSCR per the comparator. For the two-line case, the report/test's `input_length=128` counts the NUL byte in the fixture; the helper sees 127 preceding bytes and the NUL at index 127.

The candidate uses `g_ButtonHelpManager.work` via the typed manager/work declarations in `camp/unite.h`; the private test-support object defines that manager at `0x02001000`, pointing to a separate `0x564`-byte work block at `0x02002000`. The original side instead reads the pinned manager cell at `0x0043DA28`. Both map to the same equivalent test work block. The harness has no substitute implementation for the target helper's behavior: the original side executes pinned `0x0029F10C` and its pinned copy dependency, while the candidate side enters the compiled source TU and its private forward-copy loop.

Four separately reported controls detect unsupported candidate inputs: 65-byte first line, 65-byte second line, no NUL in 128 bytes, and null manager work pointer. They return zero, fault neither, and leave the work block unchanged. These are candidate safety guards only; the pinned original does not define matching behavior for invalid manager pointers or overlong/unterminated text. They are not original-versus-candidate equivalence cases or mutation controls.

## Boundaries and next step

The differential establishes bounded direct-entry behavior of the compiled helper against the pinned helper for a valid typed work pointer and at most two lines of at most 64 bytes, terminated within a 128-byte readable span, plus null reset. It does not compile `ui_runtime2.cpp` as a caller in this run, use a project-wide final-link map, execute live H1 state dispatch, prove manager construction/lifecycle, cover other locales or all caller domains, or verify rendering/game runtime. The report itself labels compilation `passed`, ARM differential `partial`, caller `partial`, and runtime `not_run`; that distinction is correct.

**Recommendation:** retain this as reviewed, partial helper evidence, but do not call the H1 source bridge integrated. Before promotion, a separate task must connect the two H1 state callsites through compiled code while preserving the pinned callback's other behavior, then validate that caller path and a canonical final link. Do not enable the entire disabled draft solely to activate two call expressions without validating its remaining body.

I performed a read-only artifact/source review. I did not compile, rerun tests, use an emulator, or modify implementation files.

