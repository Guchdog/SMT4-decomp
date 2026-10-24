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
are logical indices, but no physical mapping or direct constructor store for
title work `+0x9C` was found. H1 remains
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

## H1-B follow-up — title menu caller window (2026-10-24)

Added an explicitly scoped caller test to `tools/tbb_semantic_experiment.py`.
It verifies the pinned ARM call sites, then executes the title menu's getter
sequence from `0x001E9AB0` through the stop at `0x001E9AC8` against the original
image and the two local getter candidates. All four selections (0–3) passed
with the extracted 880-byte `TitleTable.tbb`; payload pointers, selected record
addresses, and help-field bounds matched. `Tbb_GetRowCount` is excluded because
this menu path does not call it. Candidate/original `r12` scratch differed but
is not observed by the continuation; all consumed state matched.

The focused suite passed 7 tests and the end-to-end report is
`build/semantic-equivalence/title-caller-verify/report.json`. This is offline
caller-window evidence only: it does not test the menu's full update loop,
physical input mapping, Audio Settings transition, IPS installation, or
emulator integration. The earlier statement that no caller window had been
run is superseded for this bounded getter path only.

## H1-A follow-up — title initial state and input tables (2026-10-24)

The title's `work+0x9C` is not stored by the constructor, but the allocator
path clears the full requested block before the callback is registered:
`titleMain_func_001eb02c` requests `0xA0` bytes from pool `0x10000`,
`AsdMem_AllocAlign` (`0x002C54F0`) calls `0x002C3B48` with the returned pointer
and requested size, and the zero loop is at `0x002C4B30`. Thus the initial
state is 0; it is not established by the later reset to state 5.

The input chain is also partly mapped: `0x001078D8` builds 31 logical states at
`0x004E3C58`, while `0x001FF830` reads per-ID masks at `0x004E3C48` and checks
the selected source object. Actual masks/physical bindings are runtime BSS data
and are absent from tracked files, so linking them to Azahar controls still
requires a controlled capture. No emulator or save data was touched.

## H1-C pilot — title cursor normalization slice (2026-10-24)

Added a standalone semantic candidate for the inline six-instruction block
`0x001E9DAC..0x001E9DC0` in the title callback. It performs the signed
remainder normalization and the single store to `TitleMainWork+8`; it is not
installed in the 3924-byte production callback. The compiled 32-byte candidate
matched the pinned original ARM slice for provisional cursor values `-1..4`,
including result, memory, access footprint, stack, preserved registers and
flags. A deliberately incorrect `raw % 4` candidate was detected at `-1`.

The focused test suite passed 3 tests; the runner verifies the configured
`code.bin` SHA-256 and exact six-instruction block before comparison. Reproduce
with `python tools/title_cursor_experiment.py --code extracted/exefs/code.bin
--output build/semantic-equivalence/title-cursor/seed-20261024 --seed 20261024`.
This is bounded slice evidence, not a standalone function count, full menu
reconstruction, IPS, or emulator test. The report is ignored build output.

## Semantic throughput follow-up — repeated families (2026-10-24)

To test whether the 60 byte-exact C++ conversions can be accelerated without
loosening that metric, added two isolated batches of non-byte-identical C++
candidates: 19 repeated engine leafs (8 VFP copies, 7 offset copies, 4 word
getters) and 3 AOC/ScriptVM four-word initializers. All 22 matched their
hash-pinned ARM originals across their defined test domains, two deterministic
seeds, and targeted negative controls. That is 2,646 engine-leaf comparisons
and 456 initializer comparisons. The focused semantic suites pass; none of the
candidates were placed in production or the matching ledger.

A strict inventory scan found 371 small, asm-backed leaf candidates up to 512
bytes (306 up to 64 bytes, 216 up to 32 bytes, 70 up to 16 bytes). The 19
repeated engine routines are a confirmed family within this inventory; the
other 352 are only leads, not an estimate of automatically reconstructible
functions. This supports switching from one-function-at-a-time work to
family-sized batches while keeping byte-exact, semantic-candidate, caller-
validated, and milestone counts separate. See
`experiments/semantic_equivalence/README.md` for the current experiment totals
and limitations. I also removed repeated source-file scans from
`tools/find_candidates.py` and moved size/category filtering ahead of source
inspection. The same 306-entry filtered scan dropped from 15.78 s to 1.90 s on
this workstation; the unfiltered scan is 0.49 s. This improves triage time,
not the measured throughput of semantic reconstruction itself. Added
`tools/group_candidate_signatures.py`, which preserves full operands while
grouping by mnemonic sequence. On the ≤64-byte leaf set it found 38 repeated
sequences covering 123 of 306 candidates (221 unique sequences overall). This
is a triage queue only; matching opcodes do not prove equivalent contracts.
Extending the signature inventory to 512-byte leaves yielded 46 repeated
sequences covering 147 of 371 candidates, including higher-risk VFP arithmetic
families; see the experiment README for scope.

## Semantic throughput follow-up — callback and scalar batches (2026-10-24)

Added isolated experiments for 17 table-dispatched callbacks and three
constant-offset getters. The callback candidates passed 1,224 cases across 17
functions with two targeted negative controls detected. Their pointer-table
references establish indirect dispatch but not high-level caller meaning; the
pilot explicitly limits itself to aligned, non-aliasing ordinary RAM. The
scalar getters passed 432 cases across two seeds, including wrap boundaries and
NZCV comparisons, with one wrong-offset control per function and seed. Neither
batch modifies production sources or the configured matching ledger. All
candidate-specific results and reproducible commands are in the semantic
experiment README.

Added a separate five-function null-aware pointer-chain batch. Across two
seeds, all 355 cases per seed passed; ten wrong-offset controls per seed were
detected. The original checks only the intermediate pointer: a null base faults
in both versions, while a null intermediate returns zero without a second
read. Static scan found no direct `BL` references, so no caller window is
claimed. The isolated runner verifies the pinned instruction words, returned
value, memory, access footprint and ABI.

Added four scalar-field predicate candidates at `0x0014E634`, `0x003358E0`,
`0x0034C9E0`, and `0x0034CB7C`. Across two seeds they passed 32,832 function
comparisons, detected all eight wrong-constant/sense controls, and passed 16
caller-window outcomes. The windows confirm that callers consume `r0` and
branch on it, but start at the pinned `BL` with a supplied fixture pointer;
preceding object/global setup remains outside scope. The focused combined
semantic regression now passes 39 tests. Total non-byte-identical semantic
candidates with bounded differential evidence is 68; these remain isolated
from production sources, the match ledger, and byte-exact progress.

Added a parameterized paired-store family at `0x00158784`, `0x0023347C`, and
`0x00292E88`, with destination offsets `+0x84` or `+0x40`; the earlier
`0x00131414` (+4) remains its separately tested baseline. All 26 direct BL
references were pinned. The three candidates passed 408 isolated comparisons
across two seeds, and wrong-offset, swapped-store, and wrong-return controls
were detected. This does not assert MMIO, partial-fault, concurrent mutation,
or high-level caller equivalence. The focused suites now pass 42 tests. The
bounded semantic-candidate total is 71, still separate from production and
byte-exact counts.

Added four state predicates at `0x0028C124`, `0x0028C850`, `0x0028C868`, and
`0x002D01EC`. Across two seeds they passed 576 function/caller comparisons;
24 wrong-offset, wrong-constant, and wrong-sense controls were detected. The
19 direct BL callsites are pinned, with four real caller windows covering both
branches. Those windows start before the BL but use a synthetic state pointer;
they do not reconstruct the global producer or full structure layout. The
focused semantic suites now pass 47 tests. There are 75 bounded semantic
candidates, still isolated from production and byte-exact progress.

Added a three-word copy family at `0x00232B00`, `0x00232B14`, and `0x00232B28`.
Each candidate loads all three source words before any write, preserving exact
and partial overlap, then writes to its pinned destination offset and returns
the original destination. Across two seeds, the candidates passed 24,612
function comparisons and 12 caller windows; wrong-destination and late-load
controls were detected. Caller windows start at the BL and do not validate
preceding argument setup. The focused semantic suite now passes 50 tests. Total
bounded semantic candidates: 78, separate from production and byte-exact counts.

The complete repository regression was rerun after these additions:
`python -m unittest discover -s tests -v` passed all 125 discovered tests in
332.164 seconds; three private extraction/key integration tests were skipped
because `aes_keys.txt` is not installed. The focused semantic experiment suite
accounts for 50 passing tests. `git diff --check` found no whitespace errors.

Added conditional pair-store candidates at `0x00110C2C` and `0x00121150`.
Each guards two contiguous word stores on nonzero `r1` and returns the observed
boolean. They passed 280 isolated comparisons and eight caller-window cases
across two seeds; all eight wrong-offset/order/guard/boolean controls were
detected. Caller windows begin at the BL with arguments injected, and do not
model allocator or preceding object setup.

Added halfword-plus-low-byte getters at `0x002345F0` and `0x002345FC`. Across
two seeds, both passed 280 isolated comparisons plus four caller-window cases;
all eight wrong-offset and missing-mask controls were detected. The candidates
preserve the original halfword read width via volatile access; the tested
caller windows start at BL and check immediate result consumption. Total
bounded semantic candidates: 82. Added `tools/semantic_experiment_support.py`
for pinned reference loading and relocation-free ARM leaf compilation; its
seven synthetic tests pass. Existing runners remain unchanged pending gradual
adoption.

Added two byte predicates at `0x00126430` and `0x0027EC84`, using the new
support helpers. Each seed covers all 256 byte values plus 64 seeded cases per
function; across two seeds that is 1,280 function comparisons and eight caller
window outcomes. All 12 wrong-offset/constant/sense controls were detected. The
17 direct BL references and two bounded consumer windows are pinned, but the
synthetic setup does not reconstruct all caller object producers. Their four
focused tests pass.

Added three two-word zero initializers at `0x0011B850`, `0x0017F5E8`, and
`0x0017F5F8`. Both seeds passed 402 function comparisons total, four direct
caller-window cases, and all six negative controls. The original uses one STM;
the compiled candidates use two ordered STRs, so partial-fault/atomic behavior
is explicitly outside the ordinary-RAM test contract. Two additional targets
are evidenced only through literal callback registrations, not end-to-end
callback execution. Candidate code is 16 bytes (same size as original). The
bounded semantic-candidate total is now 87.

Added tagged-pointer arithmetic getters at `0x003E698C` and `0x003E69C0`.
Across two seeds they passed 448 leaf comparisons and four caller windows;
all 12 wrong-tag-offset, wrong-displacement-offset, and wrong-sum controls
were detected. Both callers exercise only the valid-tag result because their
wrapper dereferences a null result on the invalid path; synthetic objects do
not establish whole-game layout. The bounded semantic-candidate total is 89.

After adding these batches, the full repository test discovery was rerun:
`python -m unittest discover -s tests -v` passed 151 tests in 345.803 seconds;
three private extraction/key integrations were skipped for missing
`aes_keys.txt`. The 76 focused semantic/TBB tests passed as part of that run.

Expanded the isolated semantic experiment with six more candidates: fixed-pair
initializers `0x00399D4C` and `0x003ABCF4`, word-state predicates
`0x0028C290` and `0x002E42E0`, and conditional-slot setters `0x0014E744` and
`0x002B0418`. Across two seeds, they passed respectively 268 function plus
four caller-window cases, 284 function plus eight caller-window cases, and
16,408 function plus 16 caller-window cases; their wrong-offset/constant/
guard/sense negative controls were detected. Caller evidence is bounded to
verified direct call windows and synthetic fixtures, not whole-game setup.
The experimental total is 95; official byte-exact progress remains 60.

Added `tools/scaffold_semantic_family.py` to turn a signature-group report and
pinned `code.bin` into a review manifest, checklist, and comments-only C++
placeholder. It records exact candidate bytes and image hashes, but infers no
ABI or behavior. Its ARM `BL` caller scan is explicitly heuristic, can decode
data as instructions, and excludes Thumb and indirect calls; all hits require
manual verification. Four synthetic scaffold tests pass. Usage and scope are
documented in `experiments/semantic_equivalence/README.md`.

Full regression after the six-candidate batches and scaffold generator:
`python -m unittest discover -s tests -v` ran 164 tests in 394.072 seconds and
passed; three private extraction/key integration tests were skipped because
`aes_keys.txt` is unavailable. `git diff --check` reported no whitespace
errors. These results validate the isolated experiment tooling, not a rebuilt
game or an increase to official byte-exact progress.

Parallel family batch: reconstructed three no-op leaves at `0x0023A350`,
`0x0036A29C`, and `0x00381464` as empty C++ bodies. Each compiled to a 4-byte
return versus the original 8-byte `mov r0, r0; bx lr`. Two seeds passed 408
function comparisons total, checking r0-r12, SP/LR, NZCV, memory/access
footprint, and continuation; four targeted clobber controls were detected.
No callers were confirmed, so no caller windows are claimed. The family test
module passed 3/3. Bounded semantic candidates now total 98; official
byte-exact progress remains 60. The parallel batch protocol is documented in
`experiments/semantic_equivalence/README.md`.

Three more independent family batches passed. Signed-byte getters
`0x003E6368` and `0x003E8878` passed 536 function comparisons across two seeds,
12/12 wrong-offset/width/sign controls, and four fault-parity cases. The
three chained getters `0x00207B78`, `0x002DF440`, and `0x002F300C` passed 438
function comparisons, 12 null-link fault-parity cases, and 30/30 negative
controls. CAMP setters `0x003C8FC8` and `0x003C9314` passed 1,732 function
comparisons and eight caller-window executions across two seeds; their four
direct callers were manually pinned and four negative controls detected.
Evidence remains bounded to the recorded ordinary-RAM cases and synthetic
fixtures. The semantic-candidate total is 105; official byte-exact progress is
still 60.

Three more isolated initializer families passed. Self-pointer initializers
`0x00237F10` and `0x003F7394` passed 272 function comparisons across two
seeds, four page-boundary partial-fault comparisons, and 16 negative controls;
the report pins each ordered store width and value. Script-VM initializers
`0x00353124` and `0x003531AC` passed 268 function comparisons and six negative
controls across two seeds. They use separate STRs in place of the original
STM, so partial-fault behavior is excluded. Flag initializers `0x00383780`
and `0x003A1A6C` passed 536 comparisons and detected all four targeted controls
across two seeds; their C++ stores likewise do not establish STM atomicity on
partial faults. None of these batches claims caller windows because direct
callers were not manually established. The experimental total is now 111;
official byte-exact progress remains 60.

Typed constructors `0x003A80CC` and `0x003A9644` passed 272 function
comparisons across two seeds, checking ordered byte/word writes, return value,
ABI, flags, and access traces; all three targeted negative controls were
detected. Each C++ candidate uses separate stores where the original uses STM,
so partial data-abort equivalence remains outside scope. Two focused tests pass.
Nearby literal pointer slots are pinned, but dispatch/callers are not verified;
no caller windows are claimed. Bounded semantic candidates now total 113.

Callback-state setters `0x003E89D8` and `0x003E8A68` passed 552 function
comparisons across two seeds and all 16 negative controls. The harness checks
full register/flag state, successful write traces, and partial commit behavior
when the second word faults; the fault type/effects match, though the fault PC
differs because the candidate is relocated. No direct ARM BL callers were
found, so no caller windows are claimed. Three focused tests pass. The bounded
semantic-candidate total is 115; official byte-exact progress remains 60.

Conditional pointer getters `0x00240EA4` and `0x0029E3BC` passed 1,316
function comparisons, eight manually pinned caller-window comparisons, and
four unmapped-slot fault cases across two seeds. All three wrong-offset,
wrong-width, and wrong-sense controls were detected. Their candidates are 24 B
versus 20 B originals, preserving the byte flag read and conditionally loading
the word pointer. The focused suite passed 3/3. Bounded semantic candidates
now total 117; official byte-exact progress remains 60.

The signed-delta pair `0x001220C4` and `0x001220D8` was compiled from C++ in
isolation and matched the pinned 20-byte function bodies byte-for-byte. Each
passed 164 cases per seed, including signed boundaries, NZCV, ABI, 8-byte read
footprint and cross-boundary faults; all three negative controls were detected.
Because it has not been integrated into production sources or the ledger, it
does not change the official exact count and is not part of the non-identical
semantic-candidate total.

The remaining triple conditional-store candidate `0x0034F978` passed 144
function comparisons and four caller-window comparisons across two seeds; all
ten negative-control executions were detected. Its one direct caller is pinned
and branches on the returned boolean. The C++ candidate emits three STRs in
place of one conditional STM, so precise fault/atomicity equivalence is not
claimed even though a boundary probe observed the same first two committed
words before a third-word fault. The focused module passed 3/3. The semantic
candidate total is now 118; official byte-exact progress remains 60.

Two VFP families passed isolated binary32 experiments. Lane-add helpers
`0x0023E4E4` and `0x002A3788` passed 744 comparisons across two seeds, including
IEEE edge inputs and alias layouts; four wrong-lane/operation controls were
detected. Block-scale helpers `0x0015F6D4` and `0x00256ED8` passed 1,432
comparisons, including all rounding modes, FZ/DN configurations, IEEE edge
values, aliases, and two wrong-factor/lane controls. Both runs check output
memory, FPSCR, GPR/SP/FPEXC, callee-saved VFP registers, and access footprints;
caller-saved `s0-s15` differences are reported but permitted by the ABI. Neither
batch claims caller-window equivalence. The candidates are larger than their
assembly originals; this is semantic reconstruction only. Bounded semantic
candidates now total 122; official byte-exact progress remains 60.

VFP matrix-scale helpers `0x0023D368` and `0x0023E55C` passed 1,432 binary32
comparisons across two seeds, including special values, alias layouts and
FPSCR modes; wrong factor/lane controls were detected. Results preserve output,
FPSCR and ABI-required state; caller-saved VFP registers are diagnostic only.
The candidates compile to 148 bytes versus 52-byte originals.

Packed-word helpers `0x003F8808`, `0x003F88E4`, and `0x003F89CC` passed 8,778
register-level comparisons across two seeds and all 12 negative controls. The
observed contract reads a word from `[sp]`, returns incoming `r1` in `r0`, and
assembles a word in `r1` with fixed unsigned shifts. C++ shift UB is avoided.
No direct ARM BL callers or source-level ABI were established; pointer-like
rodata slots remain unresolved. These 32-byte candidates are semantic, not
byte-identical to the 44-byte original leaves. Bounded semantic candidates now
total 127; official byte-exact progress remains 60.

Added two isolated conditional record-writer candidates at `0x0035B254` and
`0x0035BF8C`. Across two seeds they passed 544 function comparisons, ten
original-NZCV checks, eight aligned partial-fault probes, and the wrong-width
negative control. Candidate flags differ on some inputs and are excluded as
ABI-volatile; callers were not manually verified. Added indexed halfword
writers at `0x0035BBC4` and `0x0035C00C`, which passed 300 function comparisons,
eight fault probes, six controls per seed, and four caller-window cases across
two seeds. The verified direct caller is `0x0035B56C` for `0x0035BBC4`; no
ARM `BL` was found for `0x0035C00C` (Thumb and indirect calls remain outside
the scan). The indexed candidate depends on the observed compiler lowering of
an aligned `uint64_t` view to `LDRD`. The bounded semantic total is now 131;
official byte-exact progress remains 60.

Also measured a bitstream value model for `0x0016E468`, `0x00174A68`, and
`0x0017B068`: 6,144 comparisons across two seeds, all 256 shift residues, and
four high-bit patterns. This is intentionally excluded from the C++ candidate
count because the routines use a private register protocol and clobber
callee-saved `r9/r10`; only a subset of caller setup/liveness is established.

Added singleton scalar status getter `0x0035D270`: two seeds passed 528
comparisons and detected the wrong-result control. The 20-byte candidate pins
the image and exact instructions; caller-window and NZCV equivalence are not
claimed. Added four VFP sparse-scale candidates at `0x002E5B24`, `0x002F29A4`,
`0x0030C8BC`, and `0x003134F8`. Across two seeds they passed 3,104
binary32/FPSCR/alias comparisons, four late source-fault probes per seed, and
two wrong-factor controls per seed. Inline VFP assembly preserves operand order
for signaling-NaN behavior; caller-saved `s1/s2` differences are diagnostic,
while memory/access sets, FPSCR, and callee-saved state matched. No callers
were verified. Bounded semantic candidates now total 136; official
byte-exact progress remains 60.

Three additional isolated families passed. Boolean record writers
`0x001AA094` and `0x001AA0EC` passed 212 comparisons, 12 partial-fault probes,
and four detected negative controls across two seeds; callers were not
verified. Indexed halfword dispatch writers `0x001DC648` and `0x001DC6A8`
passed 216 comparisons, 12 fault probes, and eight negative controls. Faulting
access, data prefix, and SP match, but scratch `r4/r5` differs at interruption;
normal-return ABI state matches. VFP matrix-transpose initializers
`0x0023AFF0` and `0x002A1B4C` passed 256 lane/alias comparisons and four
negative controls across two seeds; the 168-byte candidates restore SP after
52-byte private stack spills below entry SP. No caller windows are claimed.
The bounded semantic total is now 142; official byte-exact progress remains 60.

Extended the VFP sparse-scale batch to eight additional functions
`0x002DD08C`, `0x002E5BA4`, `0x0030C93C`, `0x0030C9B0`, `0x0031341C`,
`0x00313578`, `0x002F293C`, and `0x00313490`. The six nine-lane and two
eight-lane candidates passed 6,208 comparisons, 16 late-fault probes, and four
negative controls across two seeds; lane maps are pinned individually. A
separate six-function packing-kernel scan found an implicit `r11` base and
callee-saved `r4-r9` clobbers, so those routines were excluded from normal C++
reconstruction pending private-caller evidence. Bounded semantic candidates
now total 150; official byte-exact progress remains 60.

Final full regression after these experiments (`python -m unittest discover -s tests -v`)
ran 237 tests in 388.089 seconds, all passing; three private extraction and key
tests were skipped because `aes_keys.txt` is unavailable. The 26 recent family
tests are included. Official byte-exact progress remains 60.

Added three isolated integer singleton leaves (`0x00130FE8`, `0x0015C408`,
`0x002A17D4`) and one five-lane VFP singleton (`0x002F28F8`). The integer
batch passed 3,112 differential comparisons across two seeds, with three
targeted negative controls and matched unmapped-read/partial-write faults; the
VFP leaf passed 776 comparisons, a late-fault probe, and wrong-lane/omitted-
lane controls. These are bounded semantic candidates, not byte-identical
reconstructions; callers were not established. The bounded semantic total is
now 154; official byte-exact progress remains 60.

Added `tools/triage_operand_signatures.py` as a review-only filter that groups
small integer leaves by normalized operand/addressing shape. On the <=64-byte
corpus it decoded 197 of 306 candidates into 24 repeated shapes covering 76
functions; this narrows review but does not infer semantics or ABI. A wider
513–2048-byte sweep found three repeated private-`r11` families and a 1008-byte
range with unresolved internal function boundaries; all were excluded. The
new singleton and triage tests passed individually. The prior full-suite result
predated these additions; the full-worktree rerun is recorded below.

Reran the complete repository suite after this batch: 245 tests passed in
400.932 seconds with no failures; three extraction/key tests were skipped
because `aes_keys.txt` is unavailable. Official byte-exact progress remains 60.

Added a recursive `--known-candidate-dir` option to the operand-shape triage
report. It annotates covered/uncovered addresses without filtering them; in the
current <=64-byte scan, all candidates in repeated shapes are already covered,
so subsequent discovery should focus on singleton shapes or broader sizes.
Added three more isolated leaves: `0x00146CE0` (halfword round-trip),
`0x00146D10` (signed-byte round-trip), and `0x002523C0` (equals-one
predicate). Across two seeds they passed 3,608 comparisons, three negative
controls, and three unmapped-read probes. Their focused tests passed. Bounded
semantic candidates now total 157; official byte-exact progress remains 60.

Continued the fresh leaf scan and added two fixed-byte record initializers
(`0x002B63BC`, `0x002B6410`) plus a signed-halfword range clamp (`0x001285C4`).
The pair passed 300 comparisons, 12 partial-fault probes, and four controls;
the clamp passed 144 boundary/random comparisons and four controls, across two
seeds. Four focused tests passed. The operand-shape triage and these latest
candidate tests were added after the earlier 245-test full regression; the
full-worktree rerun is recorded below. Bounded semantic candidates now total
160; adding the 60 byte-exact functions gives 220 distinct functions with
either exact or isolated semantic evidence. Official byte-exact progress
remains 60.

Full regression after all current batches: `python -m unittest discover -s
tests -v` ran 256 tests in 556.194 seconds, all passing; three extraction/key
tests were skipped because `aes_keys.txt` is unavailable. This run includes
the ARM/CMake builds and the new singleton and triage tests. Official
byte-exact progress remains 60.

Two final isolated batches added six candidates: `0x0023E634`, `0x00286700`,
and `0x002B540C` (mask/record helpers), plus `0x00296F18`, `0x003E8B44`, and
`0x00140854` (progress/sparse-record helpers). The first batch passed 384
comparisons and six controls per seed; the second passed 386 comparisons
across two seeds, with alias and late-fault probes and all targeted controls
detected. All eight focused tests passed. Bounded semantic candidates now
total 166; adding the 60 byte-exact functions gives 226 with exact or isolated
semantic evidence. The earlier 256-test regression predates these six
candidates; the current full-worktree result is recorded below. Official
byte-exact progress remains 60.

Final full regression after all current batches: `python -m unittest discover
-s tests -v` ran 262 tests in 638.813 seconds, all passing; three extraction/key
tests were skipped because `aes_keys.txt` is unavailable. This run includes
the ARM/CMake builds, all current semantic experiments, and triage tests.
Official byte-exact progress remains 60.

Added UI transpose helper `0x002B7AA8`, a non-arithmetic VFP move/transpose
leaf. It passed 128 comparisons across two seeds, including aligned overlap,
and detected a wrong-lane-order control; two focused tests passed. Bounded
semantic candidates now total 167; adding the 60 byte-exact functions gives
227 with exact or isolated semantic evidence. The 262-test full regression
predates this helper; rerun after the remaining candidate audit. Official
byte-exact progress remains 60.

Added conditional mask-copy helper `0x003E8BA0` (72-byte C++ candidate versus
88-byte original). Two seeds passed 278 comparisons, detected one negative
control per seed, and matched pre-write and later-lane partial-write faults.
The adjacent progress writer `0x003E8B44` has a layout that appears
compatible, but no caller relationship is demonstrated. Three focused tests
passed. Bounded semantic candidates now total 168; adding 60 byte-exact
functions gives 228 with exact or isolated semantic evidence. The latest
262-test full regression predates the UI transpose and mask-copy helpers;
rerun after this audit. Official byte-exact progress remains 60.

Resumed validation after the candidate audit. The full command
`python -m unittest discover -s tests -v` ran 267 tests in 673.090 seconds with
no failures; three extraction/key integration tests were skipped because
`aes_keys.txt` is unavailable. This includes the UI transpose and conditional
mask-copy helpers, all ARM translation-unit and CMake build checks, and the
signature-triage tests. The count audit found no canonical machine-readable
manifest to independently reconcile the reported 168 semantic candidates, so
the aggregate of 228 (168 semantic plus 60 byte-exact) is documented as a
reported experiment-log total, not an independently generated count. A fresh
read-only inventory found no uncovered simple integer leaf groups; remaining
candidates require caller/contract analysis or resolving ambiguous boundaries.
The README's stale 167 count and pre-helper regression note were corrected.
Official byte-exact progress remains 60. No production sources, matching
ledger, commit, or push were changed.

Added isolated indexed word-vector writer `0x00151FF4` after pinning its
96-byte boundary and direct ARM caller at `0x0014D4B4`. The caller prepares
`r0/r1` and overwrites `r0` after the call. The helper reloads its count before
each lane write, so output/count aliasing affects subsequent addresses. Two
seeded differential runs passed 280 cases total, detected negative controls,
matched a partial-write fault, and passed the caller-window comparison; all
three focused tests passed. The reported semantic total is now 169 and the
aggregate is 229 (60 byte-exact plus 169 isolated semantic candidates); no
canonical manifest exists yet to independently reconcile the accumulated
total. The 267-test full suite above predates this helper; its focused tests
were rerun successfully after addition.

Also investigated callback target `0x001A0768`: table entry 11 in the
dispatcher table at `0x0044DED0` resolves to it and reaches it through `BLX`.
Normal and alias cases plus real dispatcher windows matched, but exception
state on a memory fault differs because the original saves `r4` and adjusts
`sp` before the faulting accesses. Cursor/state bounds are also unknown, so
the draft was removed and excluded from the candidate total. `0x0015A3A4`
remains excluded for lack of a static caller and a sufficiently bounded
pointer/alias contract. Official byte-exact progress remains 60.

Returned to the active H1 milestone and implemented the menu-navigation reducer
as one isolated family, not as a new standalone function count. The pinned ARM
windows execute with explicit `UiInput_Trigger` results; the event boundary at
`0x002B91C4` is an observation stub only. The family harness covered the two
readiness gates, trigger-pair short-circuiting, both directions, simultaneous
opposing inputs, wraparound, cached selection and event-visible state with 11
directed cases plus 256 exhaustive combinations over valid cursor/cache values
and trigger masks. The three focused tests passed. Physical input bindings,
touch, visible help-text changes, event-helper internals, the rest of the
callback and whole-game behavior remain unverified. Findings and next H1 family
steps are recorded in `docs/milestones/H1-main-menu-flow.md` and
`experiments/semantic_equivalence/title_navigation_family_audit.md`. This does
not add a function to the 169 semantic-candidate total or change the 60
byte-exact count.

Continued H1 by functional family. Added an isolated touch reducer for the
two ARM scans at `0x001E9E4C..0x001E9EB8`; it matched 2,592 combinations of
stable per-region states and initial confirmation flag. The first scan takes
the lowest-index state 1/2, while the later scan lets the highest-index state
6 overwrite selection and set the confirmation byte. Added a help-selection
caller-window check at `0x001EA12C..0x001EA15C` using the real 880-byte
`TitleTable.tbb`; all four selected pointers matched their help strings and
color argument `0x323232FF`, stopping before the renderer. Together with the
previous navigation reducer, the three focused test modules passed 9/9 tests.
These family reducers/caller windows do not increase the semantic-function
count. They do not establish physical controls, live touch coordinates, visible
rendering, or complete callback behavior. The H1 ficha and milestone table now
record these boundaries and set composition of the three windows as the next
family task. No production sources or ledger were modified.

Added a narrow transition-readiness→help path experiment. It executes original
ARM from `0x001E9FD4` through both readiness helpers, takes a documented
synthetic branch (`child+0x34=0`, `child+0x58=0`, `work+0x94=1`), runs original
TBB getters against the real `TitleTable.tbb`, and stops before
`Camp_SetSlotMessage`. All four help pointers/color arguments match; the single
focused test passes. This skips the widget mutation block and makes no claim
that the synthetic state is runtime-normal. The next H1 family target is the
`work+0x94=0` mutator path with valid child objects, preserved VFP, and explicit
handling of indirect callbacks. Five H1-focused modules now pass 13 tests; with
the separate indexed-word-vector candidate module, 16 focused tests pass. The
267-test full-suite result predates all these new modules. No function count,
production source, or ledger changed.

Extended H1 with a continuous navigation→VFP-animation→touch harness. The ARM
reference executes all three contiguous windows in one machine with shared
work and FP state; explicit call-counted hooks cover input, event observation,
and touch responses. Three stable response profiles passed against the hybrid
reducers; a fourth ARM-only path records twelve variable touch responses.
Three focused tests passed on rerun. A composition audit found that the
subsequent `0x001E9F4C..0x001EA128` widget transition has additional object,
helper, and VFP state contracts, so it remains the next bounded investigation;
no callback composition or renderer claim is made. H1 docs and the experiment
README now record this bridge and the next blocker. No function count changed.

Continued H1 through the previously uncovered synthetic mutator branch. One
machine executes 111 original ARM PCs from `0x001E9FD4` through
`0x001EA070..0x001EA128`, then through the real TBB getters to the boundary
before `Camp_SetSlotMessage`. The focused test passes; it records 38 reads and
six expected writes to resource flags, nested transition bytes, `work+0x98`,
and `work+0x94`. Both fade helpers take their original early returns, so no
indirect callbacks are called or stubbed; the path does not prove positive-gate
or runtime-normal behavior and does not validate visible rendering in Azahar.
H1 docs now set the next investigation to obtaining a runtime-normal snapshot
and resolving positive-gate callback targets, followed by physical-input
mapping. No production source, ledger, or official function count changed.

Continued H1 through the first synthetic positive fade gate. The original
`0x002872B0` body ran continuously in the title mutator and invoked its
`BLX r1` once; the harness recorded `r0`, `s0`, `s2`, and LR at the callback
boundary and used a one-instruction `bx lr` stub with zero memory effects. The
original helper then stored its FP result and set nested byte `+0x58`; execution
continued through the real TBB help lookup and stopped before
`Camp_SetSlotMessage`. One focused test passes with 50 reads and 11 writes,
including the original stack saves. The remaining `0x0020FFAC` positive body
needs an indexed `child+0x2C` record/table graph and its own indirect callback;
that destination and ABI are still unobserved. The full trace and synthetic
limits are in `title_transition_positive_gate_report.md`. No function count,
ledger, production source, or Azahar/rendering claim changed.

Continued the transition family through the second positive gate. The original
`0x0020FFAC` body resolved a synthetic indexed descriptor/table/record, invoked
its `BLX` once with registers and FP inputs traced, and continued through the
real TBB help caller to the pre-renderer boundary. Its isolated callback was
again only `bx lr`; the test and report record 65 reads and 16 writes (including
four original stack saves). The trace does not identify the game's actual
callback implementation or establish runtime-normal state. No count, ledger,
production source, or Azahar/rendering claim changed.

Ran a navigation-only Azahar check on the user's decrypted CCI. The current
keyboard profile maps arrows to Circle Pad and T/G to D-pad; isolated taps
moved Load Game→New Game→Load Game→Audio Settings and back between Load Game
and Audio Settings, with the help line updating at each selection. No option
was confirmed and no save or game option was changed. This confirms only the
configured keyboard bindings, not a physical controller, logical short-circuit
alias, or held/repeat behavior. The exact observation and limits are in
`title_input_binding_audit.md`; capture screenshots remain in the ignored build
directory. The emulator was closed after the check. No official count changed.

Completed a static audit of the title's logical input bindings. The raw masks
for IDs 5/6 and E/F at `0x004099C0` align with D-pad and Circle Pad up/down
under the conventional 3DS HID bit assignment; that label is an inference from
the bit values; the separate Azahar probe confirms the configured keyboard
effect, not a gamepad's physical HID reports. The remaining runtime/repeat
limits are documented in `title_input_binding_audit.md`. Tightened the
transition-mutator harness to reject out-of-graph reads and assert each of its
six writes by PC, width, and value. The combined focused suite now passes 19
tests: three for the separate indexed-word-vector experiment and 16 across H1.
The latest 267-test repository-wide run predates these modules; no official
count changed.

Continued H1 by executing the alternate first-gate callback candidate
`0x00151404`, statically associated with resource type 1, plus its reached
original callees from the pinned `code.bin`. The isolated trace reaches the real
TBB/help boundary with 62 reads and 20 writes; it skips an unrelated indirect
call and an exceptional indirect site. Its one focused test passes. Together,
the type-0 and type-1 candidates have now each been exercised separately, but
the live title's resource type/pointer and the second gate's callback remain
unknown. No official function count, ledger, production source, or Azahar
verification claim changed.

Reran the focused H1 callback/menu family together with the indexed-word-vector
control: **21 tests passed** in 9.502 seconds (18 H1 tests plus three control
tests). A read-only range check of the user's decrypted CCI confirmed the two
title BAM resources and their hashes, with the RomFS offset method cross-checked
against the known `TitleTable.tbb` hash. Both BAM files start with `ATBC`; the
file header's byte `+0x10` is not enough to infer the model track's callback
type, so the candidate selection remains open pending record parsing or a live
snapshot. No official function count or production source changed.

Closed another H1 uncertainty with an isolated comparison of the two registered
callback candidates at the second fade gate (`0x00210010`). Fresh machines ran
each original candidate from the synthetic indexed record: type 0 returned
`s0=0.6` without callback writes; type 1 returned `s0=0.25` through its reached
original callees, with writes limited to the modeled stack. Both reached the
real TBB/help boundary with no out-of-model reads; the first gate remains an
explicit prerequisite stub. Three new tests plus the existing second-gate test
pass. The complete focused group now passes **24 tests** (21 H1, three
indexed-word-vector control). The report records these as candidate scenarios,
not evidence of the live runtime callback pointer or visible rendering. No
official function count, production source, or Azahar claim changed.

Added a read-only `tools/title_bam_inventory.py` for reproducible inspection of
the title's two BAM ranges directly from the user's decrypted CCI. It validates
NCSD/NCCH bounds and the local `TitleTable.tbb` hash anchor, then reports only
CGFX animation names, categories, frame counts, and track counts; it does not
extract or write game assets. The real CCI reports 3 animations / 50 tracks for
`title_top1` and 3 / 43 for `title_top2`. All five inspector tests pass, and the
title-focused regression passes **29 tests** plus **3** indexed-word-vector
control tests. This still does not map serialized animation members to runtime
callback records. No official function count, ledger, production source, or
Azahar claim changed.

Ran three signature-family audits in parallel against existing semantic
candidates: group 18 (three zero-word initializers), group 19 (three four-word
record writers), and group 21 (two fixed two-word initializers). Their two-seed
ARM-vs-C++ suites passed 402, 6,216, and 16,396 function comparisons. Address-
specific reports distinguish verified direct caller windows from static-only
caller evidence and untested callback/table dispatch. These families were
already present in the experiment inventory, so the semantic-candidate total
does not increase; production sources and matching ledger remain unchanged.
The focused title group passes 29 tests plus three indexed-word-vector control
tests, and the initializer group passes 12 tests.

Added `tools/audit_semantic_candidates.py` with three unit tests. It scans 58
candidate translation units and finds 164 unique C++ candidate definitions,
statically linking all 164 to test modules, 153 to test assertions shaped like
differential checks, and 89 to Markdown reports. These are static links, not
execution/proof status. The README aggregate is 169 semantic candidates (and
explicitly excludes the two signed-delta exact-code candidates); the difference
is unresolved, so the aggregate remains provisional and was not silently
rewritten. Reproduce the JSON audit with
`python tools/audit_semantic_candidates.py --output build/semantic-equivalence/semantic-candidate-audit.json`.

Two parallel read-only H1 traces followed the BAM/CANM evidence into the loader.
The BAM inventory confirms the serialized animation categories/member counts,
but `AsdAnim_SetupTrack` reads `source+0x10` from an already-resolved runtime
object; CANM's member type at `+0x08` has no proven mapping to that source byte.
Six direct callers pass resolved model/scene objects, and no source-type
assignment was found. The live callback selection remains open. Details are in
`experiments/semantic_equivalence/title_bam_track_source_type_mapping_audit.md`
and `title_canm_source_type_trace.md`; neither trace modified the CCI or exported
game assets.

Re-ran the full repository suite after the family audits and new tooling:
`python -m unittest discover -s tests -v` passed **301 tests in 396.535 s**;
three private CIA/key integration tests were skipped because `aes_keys.txt` is
not installed. This run includes the ARM all-translation-unit and CMake build
checks, title BAM inventory, family test additions, and semantic-candidate
auditor. No production source, official matching count, or ledger changed.

Resumed family-based validation with three parallel isolated tasks. Added a
tagged relative-payload getter family for `0x003E6974` and `0x003E69A8`; the
agent and independent rerun passed four focused tests and 2,064 differential
comparisons per seed under two seeds, with four negative controls. Added a
bounded EffPolygonThunder point-count-prefix experiment: three pre-geometry
prefixes passed 646 cases each and detected three negative controls. This does
not validate the full constructors. Three TexConv clones passed projected
output/memory checks (78 total comparisons and four control detections across
two seeds), but original ARM clobbers `r7`/`r9` while C++ preserves them, and no
caller window resolves the convention; full equivalence remains false. The
current audit reports 173 candidate-prefixed symbols (169 address-named
definitions plus four prefix/control helpers), all statically linked to tests,
with 155 differential-shaped checks. The matching old aggregate of 169 is a
numeric coincidence, not reconciliation. Full regression is pending. No
production, ROM, or matching-ledger changes; no commit or push.
