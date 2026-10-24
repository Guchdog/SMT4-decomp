# Semantic experiment field notes — 2026-10-24

Ten leaf functions at `0x00128F34`, `0x002AE464`, `0x00394614`, `0x0038143C`,
`0x00381450`, `0x003D7228`, `0x0037C46C`, `0x00121D70`, `0x0014EC5C`, and
`0x00131414` now have non-byte-identical typed ARM C++ candidates. Across the
two batches, differential execution passed 227,124 function cases and 4,674
original-caller-window cases. Nine deliberate defects were detected for their
intended reason, including signedness, null handling, alias order, memory
effects, and ABI preservation.

The original `.text` page padding `0x003FE624..0x003FF000` is 2,524 zero bytes
for the configured private image. The current 184 compiled bytes fit there. The
332-byte batch-2 IPS and 3,633,152-byte derived image have identical hashes for
both seeds; the earlier pilot separately verified IPS replay. Four original
caller windows passed, including useful checks for two batch-2 functions.
The real Azahar loader applied the IPS and the game reached its title menu.
Execution of individual replacement functions and behavior beyond the menu
remain unverified. Core source/ledger and the user's original image are
unchanged; the IPS is installed only in the local Azahar profile. Nothing was
uploaded or pushed.

See [the experiment report](experiments/semantic_equivalence/README.md) and the
[per-function procedure](docs/function-reconstruction-workflow.md) for
contracts, addresses, versions, hashes, commands, exclusions, and next gates.
Raw images, object files, and machine-readable run artifacts stay in ignored
`build/`.

## Handoff: batch 2 complete; game integration is the next gate

The user resumed work after the documented pause. Batch 2 added three typed
proposals and per-function records. The final harness runs each passed 4,096
random samples per function plus boundaries under two seeds. Four caller windows
passed. The 11 focused tests and final full repository regression passed:
64 tests in 279.534 seconds, with three private-key integration tests skipped.

The user's Azahar build loaded the supplied decrypted CCI before patching. Its
decompressed `code.bin` is 3,633,152 bytes and SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching
the exact revision used for the IPS. Azahar's [loader](https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/ncch_container.cpp)
searches `load/mods/<Title ID>/exefs/code.ips`; for this game the title path is
`load/mods/00040000000E5C00/exefs/code.ips`. The 332-byte patch is installed at
`%APPDATA%/Azahar/load/mods/00040000000E5C00/exefs/code.ips`. Luma uses
`/luma/titles/00040000000E5C00/code.ips`. In the first patched launch, Azahar's
log reported `code.ips patching code.bin`, and the user provided a screenshot
showing the SMT IV title menu. This confirms patch loading and a boot to menu;
it does not prove any replacement function executed. Next, trace replacement
entry execution and run behavior-focused in-game checks. A local ready-to-copy Azahar mod folder is in ignored
`build/azahar-mod/00040000000E5C00/`; its `code.ips` hash matches both test runs.
Only the external patch was added; the CCI was not modified. Do not claim a
full-game pass from the ARM harness.

For runtime entry confirmation, `experiments/semantic_equivalence/azahar_hit_flag.py`
connects to the Azahar GDB stub, attaches to the game process, and sets
one-shot execution breakpoints for the ten batch-2 replacement entries in the
installed patch during that recorded run. A later update added a `--batch 4`
mode; the live capture below still documents batch 2 only. A hit prints a
`FLAG` line and auto-continues. Azahar temporarily replaces the emulated code
instruction with a trap and restores it when the breakpoint is removed; no game
state marker or IPS modification is made. In the live session it confirmed
`state_flags` (`0x0037C46C`) and `relative_pointer` (`0x00128F34`). The user then
stopped monitoring; Azahar logged the disconnect, restarted its listener, and
remained responsive. See the experiment report for setup and limits: these hits
confirm entry execution, not whole-game behavioral equivalence.

## Batch 3 — semantic UI candidates

Added three isolated typed proposals and function records: bit-4 predicate
`0x0023E4D4`, void widget-flag OR `0x002C4BF0`, and unsigned UI identifier pack
`0x00357A28`. All three passed 4,104 ARM differential cases per seed under
`20261024` and `7`, and each directed negative control was rejected for its
expected return or memory difference. Six direct caller windows passed 1,058
cases per seed. The batch-3 full configured harness passed 53,872 function
comparisons and 2,616 caller-window comparisons per seed; the same generated
patch and image hashes were reproduced across seeds.

Caller-window observables are now specified per contract. The void setter
windows do not compare unconsumed `r0` or NZCV; the predicate compares the
return consumed by the caller's `cmp` and resulting branch; identifier-pack
windows compare `r0` because a following call consumes it. For windows that
begin inside a caller body, callee-saved/SP states are compared between original
and patched runs at the stop point; isolated function runs still check them
against the initial state. A focused runner test covers the caller-saved `r0` /
NZCV false-rejection case. No exact wrappers, ledger rows, or game files changed.
No full game integration was performed for this batch.

## Batch 4 — overlap-safe two-word copy

Added a typed semantic candidate for `0x002ADB40`: copy two aligned `u32`
elements after loading both source values, preserving same-array aliasing and
overlap behavior. Each of seeds `20261024` and `7` passed 4,101 differential
cases for the candidate, including exact alias, destination-after-source and
destination-before-source overlaps, and 261 cases in the real caller window
`0x00238E18` / BL `0x00238E28`. Sequential-copy and wrong-word-order controls
were both rejected for memory differences. Full configured reports are in
`build/semantic-equivalence/batch-004-copy/`. At the time of this entry the
patch had not been installed; the later H0 smoke test below records its Azahar
run. A ready-to-copy local mod folder is at
`build/azahar-mod-batch4/00040000000E5C00/exefs/code.ips`; its SHA-256 matches
the batch-4 report.

The Azahar hit monitor now supports `--batch 2` (default, historical ten caves)
and `--batch 4` (fourteen caves from the batch-4 report, including the new UI
and copy candidates). Focused tests compare each table with its report's patch
manifest. The monitor itself only observes entry reachability; it does not
install/check the IPS or prove function behavior, semantic equivalence, or full
menu reconstruction. The README records the manual hash-check and launch steps
for a user who chooses to install the batch-4 patch. No Azahar profile was
modified during this work.

## H0 — Batch 4 runtime smoke test (2026-10-24)

Backed up the previously installed batch-2 IPS (SHA-256
5d0cb36fa319678872d7c96ce9a9f878a6df393dbe5b6c3847702c2df749a89a) and
installed the batch-4 IPS (9b5f7c8f261743a2805d356153232f445c02f00c2f7938e7550505bc4b6317f9).
Azahar 2126.2 logged that it patched code.bin, reached the title, entered
Audio Settings, and returned to the title. With --batch 4 armed on emulated
process 11, the monitor captured state_flags (0x0037C46C → 0x003FE694)
and the new two_word_copy (0x002ADB40 → 0x003FE70C). No Audio Settings
value was changed and the title's save-data directory remained empty. The other
twelve entries were not observed in this short route; that is inconclusive for
other game paths. Azahar remained open after the debugger disconnected.

This closes H0's patch-identity/load/short-route criteria. It does not establish
full menu equivalence. See docs/milestones/H0-reproducible-test-base.md.

## H1 — Main menu flow map (2026-10-24)

Documented the 13-state title callback, four menu entries, trigger handling,
dispatch routes, and current static/runtime evidence in
`docs/milestones/H1-main-menu-flow.md`. The map identifies safe next work:
resolve the title's initial state and physical input IDs, then test the TBB
getters against synthetic tables before wiring them into the menu. A follow-up
trace located `UiInput_Trigger`/`Trigger2` at `0x002B902C`/`0x002BFFBC`; IDs
are logical indices, but no physical mapping or explicit initializer for title
work `+0x9C` was found. H1 remains
open; New Game, save selection, option changes, and Add-On Content are excluded
from the user-profile smoke test until isolated test data and their routes are
understood. A focused audit found that `tools/inspect_assets.py` had assumed
sequential tables and an incorrect TBL1 size/stride layout; it now follows the
TBCR offset array and payload-size/row-stride contract. Two synthetic parser
tests pass; those validate the Python reader only. The original all-candidate
ARM pilot cannot validate these getters because it rejects PC-relative literals
and external control transfers. Added a separate fail-closed blob validator for local branch
targets and in-blob LDR literal pools, plus an explicit validator parameter on
the runner so the existing pilot behavior is unchanged. Synthetic tests reject
external branches/calls, unsupported PC-relative forms, out-of-blob literals,
truncated code, and missing returns; a Unicorn test confirms a literal remains
readable after the blob is copied to the injection region. A dedicated TBB mode now tests payload and
subtable getters; row count was initially deferred because its original
tail-branches to a shared divide helper. A later H1-B follow-up covers that
dependency. The milestone plan links the H1 record and lists the remaining
integration steps.

## H1-B — TBB payload and subtable getters (2026-10-24)

Added an isolated proposal and runner at `experiments/semantic_equivalence/tbb_candidates.cpp`
and `tools/tbb_semantic_experiment.py`; this path emits no IPS and does not
modify the existing batch candidates. `Tbb_GetPayloadData` (`0x002C0E9C`)
matched the original ARM entry for 70 synthetic cases per seed;
`Tbb_GetSubTable` (`0x002AC2F4`) matched for 71 cases per seed. Both used
seeds `20261024` and `7` (282 synthetic comparisons total), and each magic-check
mutation was rejected on its targeted wrong-magic fixture. I extracted the
880-byte `TitleTable.tbb` into ignored build output (SHA-256
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`) and ran
five direct getter cases per seed against the original ARM entries; all ten
passed. Reports and hashes are in `build/semantic-equivalence/tbb-all/` and
`build/semantic-equivalence/tbb-real-title/`; function records are
`docs/function-records/0x002c0e9c.md` and `docs/function-records/0x002ac2f4.md`.
This remains isolated direct-call evidence: no caller window, IPS, or emulator
test was run.

## H1-B follow-up — TBB row-count and real asset (2026-10-24)

The static trace pinned `Tbb_GetRowCount`'s tail-branch to the shared unsigned
division helper at `0x002C6C10`. Its oracle now permits only that exact branch
inside the hash-pinned original `code.bin`; no arbitrary external control flow
was enabled. The 132-byte local candidate implements restoring unsigned
division with no relocations. It matched 72 synthetic cases for each of two
seeds, including zero divisor, truncation and large values; the wrong-result
control was caught in both runs.

Extracted `/title/TitleTable.tbb` to ignored build output and directly tested
both payloads, both subtable indices plus the count boundary, and row-count on
both real subtable headers for each seed: 14 real-asset comparisons, all pass.
Together the three getters have 426 synthetic plus 14 real comparisons. The
asset's two row strides are zero, so nonzero-stride behavior is covered by the
synthetic cases only. See `docs/function-records/0x002c0e4c.md` and the H1
milestone record for exact evidence. No caller-window, IPS or emulator test was
run.
