# ARM behavioral equivalence pilot — 2026-10-24

The previous experiment log reported 169 non-byte-identical C++ function
candidates with isolated differential evidence: the original fourteen-function pilot, three TBB
getters, twenty-two repeated-family candidates, seventeen table callbacks, and
three scalar offset, five null-chain, four scalar predicate, three paired-store,
four state predicate, three three-word-copy, two conditional pair-store, two
halfword getters, two byte predicates, three two-word zero initializers, two
tagged-pointer arithmetic getters, two fixed-pair initializers, two word-state
predicates, two conditional-slot setters, three no-op leaves, two additional
signed-byte getters, three chained pointer getters, two CAMP setters, two
self-pointer initializers, two script-VM initializers, two flag initializers,
two typed constructors, two callback-state setters, two conditional pointer
getters, one three-word conditional setter, two VFP lane-add helpers, two
VFP block-scale helpers, three packed-word helpers, two VFP matrix-scale
helpers, two conditional record writers, two indexed halfword writers, one
scalar status getter, twelve VFP sparse-scale helpers, two boolean record
writers, two indexed halfword dispatch writers, two VFP matrix-transpose
initializers, three integer singleton leaves, one five-lane VFP sparse-scale
singleton, three field round-trip/predicate leaves, two fixed-byte record
initializers, one signed-halfword range clamp, three mask/record helpers,
three progress/sparse-record initializers, one UI VFP transpose helper, and one
conditional mask-copy helper, and one indexed word-vector writer.
This experimental total is not the production or byte-exact metric; the official
byte-exact C++ count remains 60 and the matching ledger is unchanged. A
separate two-function signed-delta experiment compiled byte-identically to its
pinned originals, but remains isolated and is not included in that project
count. The accumulated experiment log reports 169 semantic candidates and 229
functions with either byte-exact or isolated semantic evidence; only the 60
byte-exact functions count toward official progress. The new static auditor
finds 164 unique candidate C++ definitions (153 linked to differential-check
assertions and 89 to Markdown reports); these are associations, not proof that
tests ran. Its raw count does not yet reconcile the reported 169, so both 169
and 229 remain provisional aggregates pending scope review.
The pilot's four batches passed
**450,814 differential function cases** and **15,660 original-caller-window
cases**; the TBB getters also passed their synthetic, real-asset, and title
caller checks. The 22 repeated-family functions add **3,102 comparisons across
two seeds**; the 17 callbacks add **1,224**; the three scalar getters add
**432 across two seeds**; the five null-chain getters add **710 across two
seeds**; the four predicates add **32,832 function comparisons and 16
caller-window comparisons across two seeds**; the three paired stores add
**408 comparisons across two seeds**; and the four state predicates add
**576 function/caller comparisons across two seeds**; the three-word copy adds
**24,612 function comparisons and 12 caller-window comparisons across two
seeds**; the conditional pair stores add **280 function comparisons and eight
caller-window comparisons across two seeds**; and the halfword getters add
**280 function comparisons and four caller-window comparisons across two
seeds**; the two byte predicates add **1,280 function comparisons and eight
caller-window comparisons across two seeds**; the zero initializers add **402
function comparisons and four direct-caller-window comparisons across two
seeds**; the tagged-pointer getters add **448 function comparisons and four
caller-window comparisons across two seeds**; the fixed-pair initializers add
**268 function comparisons and four caller-window comparisons across two
seeds**; the word-state predicates add **284 function comparisons and eight
caller-window comparisons across two seeds**; the conditional-slot setters add
**16,408 function comparisons and 16 caller-window comparisons across two
seeds**; the three no-op leaves add **408 function comparisons across two
seeds**, with four targeted negative controls; the signed-byte getters add
**536 function comparisons**, the chained pointer getters **438**, and the CAMP
setters **1,732 function comparisons plus eight caller-window executions**,
each across two seeds; the self-pointer initializers add **272 comparisons**,
the script-VM initializers **268 comparisons**, the flag initializers
**536 comparisons**, and the typed constructors **272 comparisons**, each
across two seeds; the callback-state setters add **552 function comparisons**
and 16 negative-control detections; conditional pointer getters add **1,316
function comparisons, eight caller-window comparisons, and four unmapped-slot
fault cases** across two seeds; the three-word conditional setter adds **144
function comparisons and four caller-window comparisons**, with ten negative
controls detected across two seeds. These are bounded execution results, not a
proof that a complete rebuilt game behaves identically. VFP lane-add helpers
add **744 comparisons**, and VFP block-scale helpers add **1,432 comparisons**
across two seeds. VFP matrix-scale helpers add another **1,432 comparisons**;
the packed-word helpers add **8,778**. Conditional record writers add **544
function comparisons** and eight aligned partial-fault probes across two seeds;
indexed halfword writers add **300 function comparisons**, eight fault probes,
and four manually verified caller-window cases across two seeds. The scalar
status getter adds **528 comparisons** and one wrong-result control across two
seeds. The initial four VFP sparse-scale helpers add **3,104 comparisons** and
four late-fault probes per seed; eight sibling helpers add **6,208 comparisons**
and 16 late-fault probes across two seeds. Two wrong-factor controls per seed
were detected in each batch.
All VFP batches compare output/FPSCR and ABI-preserved state; caller-saved
`s0–s15` differences are recorded but permitted. The cursor pilot is an inline
block and is not counted as a standalone function.
The boolean record writers add **212 function comparisons**, 12 partial-fault
probes, and four detected controls across two seeds. Indexed halfword dispatch
adds **216 comparisons**, 12 fault probes, and eight controls; exceptional
fault state differs in scratch `r4/r5`, while normal-return ABI state matches.
The VFP matrix-transpose initializers add **256 comparisons** and four controls;
the candidate's 52-byte stack spills below entry SP and restores SP on return.

## Faster repeated-family triage

`tools/group_candidate_signatures.py` groups inventory candidates with matching
instruction-mnemonic sequences. To produce a review-only scaffold for one
group, first generate the signature report, then select its zero-based group
index:

```powershell
python tools/group_candidate_signatures.py --functions config/functions.csv --code extracted/exefs/code.bin --output build/semantic-equivalence/signature-groups.json
python tools/scaffold_semantic_family.py --groups build/semantic-equivalence/signature-groups.json --code extracted/exefs/code.bin --group-index 0 --output build/semantic-equivalence/scaffolds/group-000
```

The output directory is new-only (the tool refuses to overwrite it) and
contains `family_manifest.json` with the image hash, exact candidate bytes,
instruction listing, and per-function byte hash; `review.md` with the evidence
and a behavior/caller checklist; and `candidate_skeleton.cpp`, which is
comments-only and deliberately does not compile. Use repeated `--address`
options to narrow a group. This saves repeated inventory and transcription
work; it does not establish that members have the same behavior or eliminate
the manual contract analysis and differential tests needed for each function.

The generated caller list is only a heuristic scan for ARM direct `BL`
instructions. Linear decoding can mistake literals/data for code, and the scan
does not include Thumb calls or indirect calls. Inspect each candidate in its
containing function and verify callsites before treating any listed address as
a caller; a missing result does not establish that the function has no callers.
The scaffold intentionally infers neither C++ ABI nor semantics from matching
mnemonics.

For a broader first-pass filter, `tools/triage_operand_signatures.py` groups
integer-only leaves by normalized operand shape as well as instruction
mnemonics. It keeps register classes, addressing forms, conditions, flag
updates, and writeback visible while abstracting general-purpose register
identities and literal values. The current <=64-byte run decodes 197 of 306
asm-backed candidates and finds 76 candidates in 24 repeated shapes. This is
only a shortlist: every proposed group still needs individual ABI, caller,
memory, flag, and behavior review. With the optional known-candidate directory,
the current scan marks every candidate in repeated shapes as already covered;
the tool keeps covered and uncovered lists without hiding any functions.
Generate a local report with:

```powershell
python tools/triage_operand_signatures.py --max-size 64 --known-candidate-dir experiments/semantic_equivalence --output build/semantic-equivalence/operand-signature-triage.json
```

Cross-checking the <=64-byte mnemonic groups found 38 repeated sequences across
123 candidate slots; every one of those addresses already has a candidate C++
symbol. This makes that particular queue a duplicate-code queue, not 123 new
functions to start. The next speed gain must come from selecting uncovered
semantic families outside this repeated-leaf set, or from improving parallel
validation/evidence rather than re-scaffolding the same symbols.

To audit the candidate-symbol inventory and its static test/report links, run:

```powershell
python tools/audit_semantic_candidates.py --output build/semantic-equivalence/semantic-candidate-audit.json
```

The JSON distinguishes C++ source presence, runner/test associations, structural
differential assertions, and Markdown references. It deliberately does not
execute tests or infer approval; reconcile the remaining scope difference
before changing the accumulated count.

For parallel throughput, assign separate signature families (or disjoint
address sets) to separate workers. Each worker owns a uniquely named candidate
translation unit, experiment runner, test module, and report directory; do not
have workers edit the shared ledger, production sources, or shared progress
documents. A batch is ready to integrate only after its pinned-reference checks,
ARM compilation, at least two seeded differential runs, and targeted negative
controls pass. Add caller windows only for manually verified sites. The parent
integrates the reports, checks for address/file overlap, updates shared docs,
and runs the full regression. This parallelizes independent investigation and
test authoring, not evidence review or the final integration gate.

The experiment is isolated on `codex/semantic-equivalence-experiment`, based on
`422c7af`. It leaves `src/`, `include/`, the matching ledger, original private
image, and the primary checkout's pending README/progress edits unchanged.
Experimental candidates do not increase the exact reconstruction count.

For subsequent functions, use the [per-function procedure](../../docs/function-reconstruction-workflow.md),
its [record template](../../docs/templates/function-reconstruction.md), and the
[completed byte-getter example](../../docs/function-records/0x00394614.md).
Batch 2 records: [signed byte](../../docs/function-records/0x00121d70.md),
[nullable pointer](../../docs/function-records/0x0014ec5c.md), and
[paired store](../../docs/function-records/0x00131414.md).
The current runner is specialized for this pilot; that procedure identifies
the code and scenarios that must be extended before testing a new function.
Batch 2 added signed-byte field read `0x00121D70`, nullable pointer field read
`0x0014EC5C`, and paired word store `0x00131414`. Each passed 4,352 or 4,107
cases under each of two seeds, with its corresponding negative control. Caller
windows were added for the signed-byte getter and paired store. Final reports
are under `build/semantic-equivalence/batch-002-callers/`.

Batch 3 adds UI flag predicate `0x0023E4D4`, void widget-flag OR `0x002C4BF0`,
and UI identifier packer `0x00357A28`. Each passed 4,104 cases per seed plus its
directed negative control. Six newly recorded caller windows passed 1,058 cases
per seed. The predicate window compares the result consumed by `cmp` and the
resulting branch; the void setter windows intentionally ignore unconsumed `r0`
and NZCV while checking RAM, access footprint, continuation, and ABI state; the
identifier packer windows compare `r0` because the next call consumes it. Full
runner output is under `build/semantic-equivalence/batch-003-ui/`.

Batch 4 adds the two-word copy `0x002ADB40`. Its C++ candidate reads both source
words before either store, preserving the original result for exact aliasing and
one-word overlap in either direction. It passed 4,101 cases per seed, two
directed negative controls, and a real caller window with 261 cases per seed.
Reports are under `build/semantic-equivalence/batch-004-copy/`.

The runner's caller-window comparison now distinguishes the caller's own
callee-saved-register usage from an isolated ABI check: isolated functions must
preserve state against initialization, while windows compare original and
patched states at the same continuation. A focused synthetic test covers false
rejections from unconsumed caller-saved `r0`/NZCV.

## Results

| Original entry | Reconstructed operation | Original / compiled bytes | Byte-identical | Differential result |
|---|---|---:|---|---|
| `0x00128F34` | Header-relative pointer | 16 / 16 | No | Pass |
| `0x002AE464` | Unsigned value greater than 400 | 16 / 20 | No | Pass |
| `0x00394614` | Byte equals `0x68` | 20 / 20 | No | Pass |
| `0x0038143C` | Read halfword and advance cursor | 20 / 20 | No | Pass |
| `0x00381450` | Read byte and advance cursor | 20 / 20 | No | Pass |
| `0x003D7228` | Copy three record words | 16 / 16 | No | Pass |
| `0x0037C46C` | Two byte fields plus a flag bit | 32 / 32 | No | Pass |
| `0x00121D70` | Sign-extended byte at `object + 0x330` | 12 / 12 | No | Pass |
| `0x0014EC5C` | Null-aware pointer load at `object + 0x1C` | 12 / 16 | No | Pass |
| `0x00131414` | Store two words at `object + 4`; return `object + 4` | 12 / 12 | No | Pass |
| `0x0023E4D4` | Predicate: bit `0x4` at `object + 0x10` | 16 / 16 | No | Pass |
| `0x002C4BF0` | OR widget flags at `object + 0x34` (void) | 16 / 16 | No | Pass |
| `0x00357A28` | Mask and shift UI identifier | 20 / 16 | No | Pass |
| `0x002ADB40` | Copy two words, both loads before stores | 20 / 20 | No | Pass |

Together the fourteen candidates represent 248 original bytes, approximately
0.00791% of the text segment. They were selected for known compiler differences;
their success rate must not be extrapolated to the whole game.

| Seed | Random cases per function | Function comparisons, including boundaries | Caller comparisons | Full pilot elapsed |
|---|---:|---:|---:|---:|
| `20261024` | 16,384 | 115,010 | 779 | 44.86 s |
| `7` | 4,096 | 28,994 | 779 | 12.41 s |
| `20261024` (batch 2) | 4,096 | 41,560 | 1,558 | 18.11 s |
| `7` (batch 2) | 4,096 | 41,560 | 1,558 | 19.35 s |
| `20261024` (batch 3) | 4,096 | 53,872 | 2,616 | 22.43 s |
| `7` (batch 3) | 4,096 | 53,872 | 2,616 | 23.82 s |
| `20261024` (batch 4) | 4,096 | 57,973 | 2,877 | 25.25 s |
| `7` (batch 4) | 4,096 | 57,973 | 2,877 | 25.01 s |

Each run includes compilation (about 0.27 s), negative controls, patch generation,
and execution. Timings are local observations under concurrent regression-test
load, not a controlled performance benchmark. They exclude manual reconstruction,
harness development, and the full repository suite. Batch 2 increased the
candidate count from seven to ten; batch 3 from ten to thirteen; batch 4 from
thirteen to fourteen.
This shows that functions rejected by byte
equality can be retained as tested experimental C++; it does not establish an
end-to-end project speedup factor or faster game code.

## What actually executes

`candidates.cpp` is compiled by the existing ARMv6K Clang pipeline with the
repository's `-O2`, ARM11 MPCore, VFPv2 and hard-float options. The local compiler
was Clang 23.1.3; the CPU backend was Unicorn 2.1.4, model ARM11 MPCore.

The original is read from the user's decompressed `code.bin`, checked against
the configured size and SHA-256 before execution. Both versions execute as
ARM instructions, not as Python rewrites of their algorithms. The reference hash
is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The tool checks the following after every run:

- Return register `r0` for value-returning functions, including pointer
  preservation where a complete original return type remains uncertain. The
  new `void` widget setter ignores unconsumed `r0` in isolated tests.
- Callee-saved `r4-r11`, `SP`, and `d8-d15` against their initial values.
- All test RAM, live caller stack bytes, and observable read/write byte sets.
- Expected return/continuation and bounded execution without a CPU/memory fault.

Caller-saved temporaries and leaf condition flags may differ. Caller windows
compare NZCV only when the caller consumes it, and compare `r0` only when the
return is consumed. Each window compares callee-saved/SP state between original
and patched executions at the stop point; isolated calls validate those
registers against their initial state. Internal stack scratch and the order of
ordinary RAM accesses are not required to match.

Inputs include integer boundaries, seeded random values and surrounding memory,
all 256 byte-equality and signed-byte inputs, null and non-null pointer cases,
paired-store boundary values, and four valid byte-reader aliases where the input
cursor points into its own pointer representation. Halfword/pointer/record
alignment is respected. Relative offsets stay within the bounded fixture's
accessible payload; the fixture does not assert an actual game record size.

Negative controls intentionally introduce `>=` instead of `>`, the wrong byte
constant, the wrong cursor stride, incorrect alias-sensitive load/store ordering,
the wrong flag bit, and a clobbered callee-saved register. Batch 2 adds incorrect
signed-byte extension, wrong nullable-pointer return, and wrong paired-store
data. A fault or timeout is always failure, even if both versions fail the same
way. Controls must fail for the expected reason, not merely trigger any error.

## Patched-image integration

The local image has 2,524 zero bytes between the logical text end `0x003FE624`
and its existing page boundary `0x003FF000`. The batch-4 tool places the 248
compiled bytes in that padding and replaces the fourteen original entries with
ARM branches.
It rejects relocations, PC-relative replacements, calls, floating-point code,
nonzero padding, invalid bounds, and insufficient padding. No segment offsets,
file length, original data, or matching source definitions are moved.

All positive function comparisons execute this **same patched-image layout**.
Four original caller windows execute their unchanged BL and following
instructions:

- `0x001B0370`: caller passes `r5` to `0x002AE464`; both continuations
  `0x001B0384` and `0x001B0394` were exercised.
- `0x001B4DBC`: caller passes a stack byte to `0x00394614`; both continuations
  `0x001B4DD0` and `0x001B4DF4` were exercised.
- `0x00110F44`: caller passes a test record to `0x00121D70`; both outcomes at
  `0x00110F50` and `0x00111008` were exercised. The preceding global producer
  is outside this window.
- `0x00121D1C`: caller invokes `0x00131414` and continues at `0x00121D24`.
  The caller overwrites `r0`, so this checks writes and continuation, not return use.

Batch 2's signed-byte getter also exercised both real caller branches at
`0x00110F44`. The paired-store window at `0x00121D1C` compared the writes and
the caller continuation; the caller overwrites `r0`, so it does not test the
callee's return use. The nullable-pointer caller windows discard its return and
are not counted as useful caller validation.

Successful runs emit ignored, local-only artifacts:

- `build/semantic-equivalence/batch-002-callers/seed-20261024/report.json` and
  `build/semantic-equivalence/batch-002-callers/seed-7/report.json`: versions, hashes,
  seed, counts,
  timings, patch manifest, counterexamples for controls, and limitations.
- `build/semantic-equivalence/batch-002-callers/seed-20261024/code.experimental.bin`:
  derived 3,633,152-byte image.
- `build/semantic-equivalence/batch-002-callers/seed-20261024/code.ips`: 332-byte
  patch containing generated branches and C++ machine code. Both seeds
  generated identical patch/image hashes; the earlier pilot independently
  replayed its IPS to verify exact image reconstruction.

Batch 2 patched image SHA-256:
`3b4595c91b1ad41457cab8dc6f4196fadb7ae47c045a828b46adf80120295116`.
Batch 2 IPS SHA-256:
`5d0cb36fa319678872d7c96ce9a9f878a6df393dbe5b6c3847702c2df749a89a`.

**Patched boot confirmed; per-function execution is not yet confirmed.** The
decrypted CCI supplied for Azahar was inspected without modification: its decompressed `code.bin` is
3,633,152 bytes and has the expected SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The IPS
was installed in this Azahar profile. On launch, the log reported
`File .../load/mods/00040000000E5C00/exefs/code.ips patching code.bin`, and the
user provided a screenshot of the SMT IV title menu. This confirms the loader
applied the patch and the game reached its menu, but does not prove any specific
replacement function was called. No visual difference is expected from
semantics-preserving replacements. Per-function runtime evidence and behavior
checks remain outstanding.

### One-shot execution flags (Azahar GDB)

To confirm that a replacement actually runs in Azahar, use the prepared
[`azahar_hit_flag.py`](azahar_hit_flag.py) monitor. It connects to Azahar's GDB
Remote Serial Protocol, attaches to the game process, and installs one-shot
execution breakpoints selected from the patch report manifest. `--batch 2`
monitors the historical ten-cave patch (the default, preserving the previously
used mode). `--batch 4` monitors the current fourteen-cave patch, including
batch 3's three UI functions and batch 4's two-word copy at cave `0x003FE70C`.
The breakpoint-to-function tables are checked against the ignored `report.json`
manifests by focused tests. The monitor does not install or inspect the IPS, so
select the batch that exactly matches the patch currently loaded by Azahar.

To try batch 4, first verify the generated patch against its report (the
recorded batch-4 IPS SHA-256 is
`9b5f7c8f261743a2805d356153232f445c02f00c2f7938e7550505bc4b6317f9`):

```powershell
Get-FileHash build/semantic-equivalence/batch-004-copy/seed-20261024/code.ips -Algorithm SHA256
```

Then, only if you want to run the new patch, manually place that exact `code.ips`
at `load/mods/00040000000E5C00/exefs/code.ips`, launch the matching US game in
Azahar, and run `python experiments/semantic_equivalence/azahar_hit_flag.py --batch 4`.
This monitor does not modify the emulator profile. The historical
installed patch can be monitored with the default `--batch 2`; its IPS SHA-256
is `5d0cb36fa319678872d7c96ce9a9f878a6df393dbe5b6c3847702c2df749a89a`.

When a monitored function is reached, the debugger
prints `FLAG: replacement ... executed ...`, removes that breakpoint, and
continues automatically. No game-state marker is written and the IPS is
unchanged. Azahar implements software execution breakpoints by temporarily
replacing the instruction in emulated code memory with a trap and restoring the
original bytes when the breakpoint is removed or the debugger detaches. A hit
confirms only that execution reached that entry. It does not establish semantic
equivalence, correctness for all game states, that the whole menu was
reconstructed, or that any other entry ran.

In Azahar, enable **Emulación > Configurar > Debug > Enable GDB Stub** and keep
the configured port at `24689`. With the matching patched title running, run
the monitor from the repository root:

```powershell
python experiments/semantic_equivalence/azahar_hit_flag.py
```

For the current batch-4 image, explicitly select it so the monitor arms all
fourteen caves:

```powershell
python experiments/semantic_equivalence/azahar_hit_flag.py --batch 4
```

The previously recorded live run used batch 2, attached to process `11`, and captured two flags:
`state_flags` (`0x003FE694`, replacement for `0x0037C46C`) and
`relative_pointer` (`0x003FE624`, replacement for `0x00128F34`). The user then
stopped monitoring. Azahar logged the client disconnect, restarted its GDB
listener, and remained responsive. If Azahar is restarted and its process ID
changes, pass the current emulated process ID with `--pid <id>` (the log's
`Caller PID` identifies it). Press Ctrl+C in the monitor terminal to disconnect;
Azahar clears its breakpoints and restores the original code instructions. A
breakpoint that never hits is inconclusive: that code path may simply not have
occurred during the observed menu/gameplay.

Azahar's [loader](https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/ncch_container.cpp)
searches `load/mods/<Title ID>/exefs/code.ips`. For this US title, use
`load/mods/00040000000E5C00/exefs/code.ips` and the exact base revision whose
`code.bin` hash is recorded above; IPS does not check the source image. The
ready-to-copy title folder is `build/azahar-mod/00040000000E5C00/`; the batch-4
folder is `build/azahar-mod-batch4/00040000000E5C00/`. The current profile copy
is under `%APPDATA%/Azahar/load/mods/00040000000E5C00/exefs/`.
Only the external patch file was added; the CCI was not modified. The
repository still has no full executable linking/package target.

Luma3DS documents external decompressed code and IPS loading under
`/luma/titles/<TitleID>/` in its
[official optional-features documentation](https://github.com/LumaTeam/Luma3DS/wiki/Optional-features).
This provides a next integration route, not evidence that this patch has already
booted. No console, installation, game image or save data was modified.

## TBB getter semantic experiments

The isolated runner `tools/tbb_semantic_experiment.py` compiles proposals for
`Tbb_GetPayloadData`, `Tbb_GetSubTable`, and `Tbb_GetRowCount` without changing
the configured batch candidates or emitting an IPS. The first two original
wrappers use local branches and PC-relative literal pools, so only the strict
`validate_local_blob` validator is used for the replacement blobs.

`Tbb_GetRowCount` tail-branches to the shared unsigned division routine at
`0x002C6C10`. The oracle executes that exact target in the configured,
hash-verified original `code.bin`; the runner does not whitelist arbitrary
external branches. Its separate C++ candidate uses a 32-bit restoring division
with no external relocations. This validates the getter against the original
helper, not a reconstruction of that shared helper itself.

With `--samples 64`, seeds `20261024` and `7` passed 70 payload, 71 subtable,
and 72 row-count synthetic cases each. All three targeted negative controls
were detected. The 880-byte `/title/TitleTable.tbb` was extracted under ignored
`build/semantic-equivalence/real-assets/` and passed seven direct getter cases
per seed: two payload pointers, two valid subtable indices, the out-of-range
index equal to count, and row-count on each real TBL1 header. Its SHA-256 is
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`.
The total is 426 synthetic plus 14 real-asset comparisons. The real asset's
row strides are both zero; nonzero division is covered by synthetic cases.

Reproduce both seeds from the repository root after extracting your own
verified code image and title asset:

```powershell
python tools/tbb_semantic_experiment.py --code extracted/exefs/code.bin --output build/semantic-equivalence/tbb-real-title/seed-20261024 --seed 20261024 --samples 64 --real-tbb build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb
python tools/tbb_semantic_experiment.py --code extracted/exefs/code.bin --output build/semantic-equivalence/tbb-real-title/seed-7 --seed 7 --samples 64 --real-tbb build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb
```

These are isolated direct-call comparisons only. They do not prove every
possible pointer layout, caller integration, title-menu behavior, IPS loading,
or gameplay equivalence.

## Additional repeated-function families

Two newer batches tested repeated shapes that are suitable for one candidate
template plus per-entrypoint address/hash checks:

- The engine-leaf batch covers **19 functions**: eight 16-byte VFP copies,
  seven copies to `dst + 0x10`, and four raw `u32` getters at `p + 4`. Each copy
  passed 69 cases and each getter 72 cases under seeds `20261024` and `7`, for
  2,646 function comparisons total. Three negative controls per seed detected
  forward-copy overlap errors and a wrong getter offset. The original VFP
  instructions execute with ARM11 CP10/11 and FPEXC enabled; aligned ordinary
  RAM is the tested domain. The runner initializes `d0-d7` deterministically,
  but does not claim equality for caller-saved VFP state.
- The AOC/ScriptVM initializer batch covers **three 4-word descriptor
  initializers**. Each passed 76 cases under both seeds (456 comparisons);
  three intentionally incorrect initializers were detected per seed. The
  candidate stores `{source, 0, buffer, size}` and returns the object pointer.
  Original caller instructions were inspected, but full caller-window tests
  have not yet been added for these three functions.

These 22 functions, together with the earlier fourteen and three TBB getters,
bring the isolated candidate-function count to 39 before the newer callback and
scalar batches below. This is not a count of production replacements and does
not change the 60 byte-exact C++ reconstructions in the primary branch. All
newer candidates live only in this experiment tree and do not modify `src/`,
`include/`, the configured matching ledger, an IPS, or the emulator profile.

### Table callback batch

Seventeen 44-byte entries from `0x0035B6FC` through `0x0035BB98` share one
callback protocol and vary their constants/store width. Each candidate writes
two fields in the record reached through `*r1`, increments the word at `r0+16`,
and returns zero. The hash-pinned table at `0x00473080..0x0047324F` contains
their function pointers in 8-byte slots, interleaved with neighboring
callbacks. This establishes table-based dispatch, but not the high-level
business meaning or real caller state.

All 17 passed 72 differential cases each (1,224 total) with seed `20261024`;
two targeted negative controls were detected. The candidate functions compile
to 44 bytes, but none is byte-identical. The test domain uses valid aligned,
non-aliasing pointers into ordinary RAM. It excludes volatile/MMIO, concurrency,
partial faults and aliasing because the original performs two separate loads
through `r1`. No caller window is claimed. Reproduce with:

```powershell
python tools/table_callback_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/table-callbacks
```

### Scalar offset batch

Three leaves at `0x00343550`, `0x00343584`, and `0x00343590` add `0x5B4`,
`0xC04`, and `0x6FC` to `r0`, respectively. The C++ candidates use `uint32_t`
addition to retain ARM's modulo-2^32 behavior. They passed 72 cases each under
seeds `20261024` and `7` (432 total); every NZCV value was compared, and one
wrong-offset control per entry was detected. None is byte-identical; caller
windows are not yet included. Reproduce each seed with:

```powershell
python tools/scalar_offset_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/scalar-offsets/seed-20261024
python tools/scalar_offset_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/scalar-offsets/seed-7
```

### Null-aware pointer-chain batch

Five getters at `0x00141468`, `0x002344B4`, and `0x003DF578/588/598` read a
word from `base + first_offset`; when that intermediate pointer is nonzero, they
read and return a second word at its function-specific offset. A zero second
value is returned unchanged. Only the intermediate pointer is checked: a null
base faults in both the reference and candidate.

All five passed 71 cases each under seeds `20261024` and `7` (710 comparisons);
ten wrong-offset controls per seed were detected. Tests compare return values,
ABI state, read/write footprints, and memory; the footprint confirms the second
load is skipped for a null intermediate. No caller window was added because
direct `BL` references were not found. The domain is aligned ordinary RAM, not
MMIO, concurrent mutation, or unaligned pointers. Reproduce with:

```powershell
python tools/null_chain_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/null-chain/seed-20261024
python tools/null_chain_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/null-chain/seed-7
```

### Scalar predicate batch

Four field-equality predicates at `0x0014E634`, `0x003358E0`, `0x0034C9E0`,
and `0x0034CB7C` compare a loaded word with 5, 4, 4, and 1 (the last returns
true when it is not 1). All four passed 4,104 cases each with seeds `20261024`
and `7`, for 32,832 differential function comparisons. Four wrong-constant or
wrong-sense controls were detected per seed. Their four pinned caller windows
consume `r0` and branch on its boolean value; both outcomes passed per caller
and seed (16 caller-window comparisons). The windows begin at each `BL` and
supply `r0` directly, so they do not validate preceding global/object setup.
The candidates use aligned ordinary RAM and are not byte-identical. Reproduce
with:

```powershell
python tools/scalar_predicate_experiment.py --code extracted/exefs/code.bin --samples 4096 --seed 20261024 --output build/semantic-equivalence/scalar-predicates/seed-20261024
python tools/scalar_predicate_experiment.py --code extracted/exefs/code.bin --samples 4096 --seed 7 --output build/semantic-equivalence/scalar-predicates/seed-7
```

### Paired-store batch

Three functions at `0x00158784`, `0x0023347C`, and `0x00292E88` store `r1` and
`r2` in ascending order at destination offsets `+0x84` and `+0x88`, or `+0x40`
and `+0x44`, then return the adjusted destination. Their code shares the
operation but the static callers span different engine, shop, UI and ScriptVM
contexts. All 26 direct callsites were inventoried and pinned; this establishes
references, not high-level caller behavior. Each candidate passed 68 cases per
seed (408 total), and wrong-offset, swapped-store, and wrong-return controls
were detected. The domain requires aligned, in-bounds ordinary RAM and excludes
MMIO, concurrency and partial-fault behavior. Reproduce with:

```powershell
python tools/paired_store_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/paired-stores/seed-20261024
python tools/paired_store_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/paired-stores/seed-7
```

### State predicate batch

Four predicates at `0x0028C124`, `0x0028C850`, `0x0028C868`, and `0x002D01EC`
load a word at argument-relative `+0x2180` (first, second and fourth) or
`+0x3048` (third), then return whether it differs from 6, 5, 14 or 4. The
exact enclosing structure names/types are unknown. All four passed 280
function comparisons and eight caller-window outcomes per seed (576 combined
positive comparisons); all 12 wrong-offset, wrong-constant and wrong-sense
controls per seed were detected (24 total). The 19 direct BL references were
pinned. Caller windows begin before the BL and exercise both branches with a
synthetic state pointer; they do not recover the global producer or complete
structure layout. Inputs are aligned ordinary RAM; null and MMIO semantics are
not claimed. Reproduce with:

```powershell
python tools/state_predicate_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/state-predicates/seed-20261024
python tools/state_predicate_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/state-predicates/seed-7
```

### Three-word copy batch

Three routines at `0x00232B00`, `0x00232B14`, and `0x00232B28` copy three words
from `r1` to `r0 + 0x4C`, `r0 + 0x40`, or `r0 + 0x28`, respectively, and return
the original `r0`. All three source loads precede every store, and the store
order is not assumed to imply the load order. The candidates preserve this
load-before-store behavior and passed 4,102 cases each under seeds `20261024`
and `7` (24,612 total). Six caller windows per seed passed; they start at the
pinned BL, so preceding argument setup is not tested. Wrong-destination and
late-load controls were detected, including forward/backward/exact overlap
cases. The domain is aligned, in-bounds ordinary RAM, not MMIO or partial-fault
behavior. Reproduce with:

```powershell
python tools/three_word_copy_experiment.py --code extracted/exefs/code.bin --samples 4096 --seed 20261024 --output build/semantic-equivalence/three-word-copy/seed-20261024
python tools/three_word_copy_experiment.py --code extracted/exefs/code.bin --samples 4096 --seed 7 --output build/semantic-equivalence/three-word-copy/seed-7
```

### Conditional pair-store batch

Two helpers at `0x00110C2C` and `0x00121150` check whether `r1` is nonzero;
when nonzero, they store `r1` and `r2` at context offsets `+0x1C/+0x20` or
`+0x30/+0x34` and return 1, otherwise they make no writes and return 0. Each
candidate passed 70 function cases per seed; together both candidates and
seeds produced 280 comparisons. Four caller-window cases per seed (eight total) passed with
arguments supplied at the pinned BL. Eight targeted controls across both seeds
were detected (wrong offset, swapped values, missing null guard, wrong
boolean). The windows do not model allocation or preceding object/global
setup. Inputs are aligned in-bounds ordinary RAM, not MMIO or partial faults.
Reproduce with:

```powershell
python tools/conditional_pair_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/conditional-pair/seed-20261024
python tools/conditional_pair_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/conditional-pair/seed-7
```

### Halfword-plus-low-byte getters

Two getters at `0x002345F0` and `0x002345FC` read a halfword at `r0+0x48` or
`r0+0x4A`, mask it to the low byte, and return that value. The volatile C++
load preserves the original 16-bit access width; omitting it let the compiler
narrow the access. Both candidates passed 70 cases each under seeds `20261024`
and `7` (280 isolated comparisons), plus two original caller windows per seed
(four total). The 32 direct BL references and both tested call sites are pinned;
the windows start at BL with `r0` supplied and compare the immediate result
consumption. Offset+1 and missing-mask controls were all detected (8 total).
The domain is aligned in-bounds ordinary RAM. Reproduce with:

```powershell
python tools/halfword_lowbyte_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/halfword-lowbyte/seed-20261024
python tools/halfword_lowbyte_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/halfword-lowbyte/seed-7
```

### Byte predicate pair

Two byte predicates at `0x00126430` and `0x0027EC84` return whether the byte at
`r0+0x44` equals 2 or the byte at `r0` equals 0. Both functions passed all 256
possible byte values plus 64 seeded register/memory cases per function and
seed (1,280 function comparisons total across two seeds). Their 17 direct callers and two
consumer windows are pinned; eight branch-window outcomes passed, covering
both predicate values at the selected callsites. Six wrong-offset/constant/
sense controls per seed were detected. The setup is a bounded fixture, not the
full caller or object producer. Reproduce with:

```powershell
python tools/byte_predicate_pair_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/byte-predicate-pair/seed-20261024
python tools/byte_predicate_pair_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/byte-predicate-pair/seed-7
```

### Two-word zero initializers

Three routines at `0x0011B850`, `0x0017F5E8`, and `0x0017F5F8` write zero to
`[r0]` and `[r0+4]`, then return the unchanged base. The original uses one
`stm`, while the compiled candidate emits two ordered `str` operations; both
words and the return match in the tested ordinary-RAM domain, but atomicity and
partial-fault behavior are not claimed. Candidate size is 16 bytes, equal to
the original. The direct-call function has two pinned callers, both
with caller windows; the other two are callback pointers passed through nearby
registration sites, so their downstream callback behavior is not claimed.
Across two seeds, the three candidates passed 402 function comparisons and
four direct caller-window cases; all six targeted controls were detected.
Inputs are aligned, in-bounds ordinary RAM. Reproduce with:

```powershell
python tools/zero_pair_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/zero-pairs-seed20261024
python tools/zero_pair_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/zero-pairs-seed7
```

### Tagged-pointer arithmetic getters

Two routines at `0x003E698C` and `0x003E69C0` inspect a halfword tag at `r0+8`
or `r0+0x10`. When it equals `0x101`, they load a displacement at `r0+0xC` or
`r0+0x14` and return `r0+displacement` modulo 2^32; otherwise they return zero
without reading the displacement. Across two seeds, both passed 224 cases each
(448 total), four bounded caller windows passed, and 12 wrong-tag-offset,
wrong-displacement-offset, or wrong-sum controls were detected. The two caller
wrappers are tested only for the valid-tag path because they dereference the
result on that path; invalid-tag behavior is established only at the leaf.
The caller setup uses synthetic outer/inner objects and is not whole-game
evidence. Reproduce with:

```powershell
python tools/tagged_pointer_arithmetic_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/tagged-pointer-arithmetic/seed-20261024
python tools/tagged_pointer_arithmetic_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/tagged-pointer-arithmetic/seed-7
```

The strict leaf scanner also found **371** small asm-backed, call-free,
return-terminated entries at or below 512 bytes in the current ledger: 306 at or
below 64 bytes, 216 at or below 32 bytes, and 70 at or below 16 bytes. Nineteen
of these are the repeated copy/getter family above. The remaining 352 are only
shortlist entries, not automatically reconstructible functions; they need
pattern classification and contract/caller review. In particular, counts by
size must not be interpreted as a speedup estimate.

The candidate scanner itself was also optimized: for the `--max-size 64
--status matching --asm-backed-only` scan, indexing source blocks once reduced
observed wall time from 15.78 s to 1.90 s on this workstation, with the same
306 results. The unfiltered scan took 0.49 s. This is an 8.3x reduction in
filtered discovery time, not an 8.3x speedup in reconstruction work.

The new `tools/group_candidate_signatures.py` report groups scanner results by
mnemonic sequence while retaining the full disassembly and operands for every
entry. On the current `--max-size 64` set it found 221 signatures among 306
candidates: 38 signatures repeat, covering 123 candidates. This is a review
queue, not proof of shared semantics; registers, immediates, memory widths,
flags, and dispatch callers can change the contract. Reproduce it with:

```powershell
python tools/group_candidate_signatures.py --code extracted/exefs/code.bin --max-size 64 --status matching --output build/semantic-equivalence/signature-groups-64.json
```

For new families, `tools/semantic_experiment_support.py` now provides two small
helpers: `load_pinned_reference` validates code-image size/SHA before loading
the function ledger, and `compile_candidate_symbols` compiles an ARMv6K TU,
rejecting relocations, missing symbols, and non-leaf code. Seven synthetic
tests cover these failure paths. Existing family runners remain self-contained
for now; instruction/caller pins, fixtures, comparison policy, and negative
controls stay visible in each family rather than being hidden in a framework.

Extending the scan to 512 bytes produced 270 signatures among 371 candidates;
46 repeat, covering 147 functions. Some of the newly included repeated groups
contain long VFP arithmetic sequences. They are inventory leads only and need
their own floating-point and caller-state contracts before any code generation.

### Conditional record writers

The two writers at `0x0035B254` and `0x0035BF8C` write a byte, reload the
pointer slot, perform a condition-specific byte/halfword write, then increment
the record counter. Both seeds passed 272 function comparisons (544 total),
ten original-NZCV checks, and four aligned partial-fault probes per seed; the
wrong-width negative control was detected. C++ candidate flags differ on some
inputs, so they are ABI-volatile and excluded from equivalence. No caller was
manually verified. The observed behavior is bounded to ordinary mapped RAM;
MMIO and concurrent mutation are not covered. Reproduce with:

```powershell
python tools/conditional_record_writer_experiment.py --code extracted/exefs/code.bin --samples 128 --seed 20261024 --output build/semantic-equivalence/conditional-record-writers-seed20261024
python tools/conditional_record_writer_experiment.py --code extracted/exefs/code.bin --samples 128 --seed 7 --output build/semantic-equivalence/conditional-record-writers-seed7
```

### Indexed halfword writers

`0x0035BBC4` and `0x0035C00C` clear a byte, load a halfword through an indexed
base, store it through a reloaded target pointer, and increment a record
counter. Each seed compares 75 cases per function, including alias layouts;
both reports pass, and all six negative controls per seed were detected. Four
fault probes per seed preserve the observed write prefix. A manually pinned
direct caller at `0x0035B56C` was exercised for `0x0035BBC4`; no ARM `BL` was
found for `0x0035C00C` (this scan does not cover Thumb or indirect calls). The
candidate's `uint64_t` view lowers to the required `LDRD` with the current
compiler/alignment; this is not a portable C++ guarantee. Reproduce with:

```powershell
python tools/indexed_halfword_writer_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 20261024 --output build/semantic-equivalence/indexed-halfword-writer-seed20261024
python tools/indexed_halfword_writer_experiment.py --code extracted/exefs/code.bin --samples 64 --seed 7 --output build/semantic-equivalence/indexed-halfword-writer-seed7
```

### Scalar status getter

`0x0035D270` loads the word at `r0+0x18` and returns 3 when it is zero, or 1
otherwise. The 20-byte C++ candidate passed 264 cases under each of two seeds
(528 total), including every byte value in the tested word's low byte and
random full-word values; the wrong-result control was detected. The image and
exact entry bytes are hash-pinned and instruction drift fails closed. No caller
window or NZCV contract is claimed, and the tested domain is aligned ordinary
RAM. Reproduce with:

```powershell
python tools/scalar_0035d270_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/scalar-0035d270/seed-20261024
python tools/scalar_0035d270_experiment.py --code extracted/exefs/code.bin --seed 20261025 --output build/semantic-equivalence/scalar-0035d270/seed-20261025
```

### VFP sparse-scale helpers

Four 128-byte routines at `0x002E5B24`, `0x002F29A4`, `0x0030C8BC`, and
`0x003134F8` apply a factor to nine disjoint single-precision matrix lanes.
Across two seeds, each passed 388 cases (3,104 total), including IEEE/FPSCR
configurations, alias layouts, and four late source-fault probes per seed; two
wrong-factor controls per seed were detected. The candidate uses inline VFP
instructions to preserve operand order and signaling-NaN behavior that the
compiler reordered for ordinary C++ multiplication. Memory, access sets,
FPSCR, and callee-saved state match in the tested domain; caller-saved `s1/s2`
differences are reported as ABI-permitted diagnostics. Candidates are 132
bytes versus 128-byte originals. No callers or whole-game behavior are claimed.
Reproduce with:

```powershell
python tools/vfp_sparse_scale_experiment.py --code extracted/exefs/code.bin --samples 256 --seed 20261024 --output build/semantic-equivalence/vfp-sparse-scale-seed20261024
python tools/vfp_sparse_scale_experiment.py --code extracted/exefs/code.bin --samples 256 --seed 7 --output build/semantic-equivalence/vfp-sparse-scale-seed7
```

### VFP sparse-scale sibling helpers

Eight more functions at `0x002DD08C`, `0x002E5BA4`, `0x0030C93C`,
`0x0030C9B0`, `0x0031341C`, `0x00313578`, `0x002F293C`, and `0x00313490`
share the sparse single-precision scaling pattern. The first six operate on
nine lanes and the last two on eight; each has a pinned per-function lane map.
Across seeds 7 and 20261024, the eight candidates passed 3,104 cases per run
(6,208 total), including IEEE/FPSCR modes, aliases, and one late-fault case per
function per seed; 16 partial-fault probes and four wrong-factor controls were
recorded. Memory/access sets, FPSCR, and callee-saved state match; no callers
or whole-game behavior are claimed. Reproduce with:

```powershell
python tools/vfp_sparse_scale_extension_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/vfp-sparse-scale-extension-final-seed20261024
python tools/vfp_sparse_scale_extension_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/vfp-sparse-scale-extension-final-seed7
```

### Boolean record writers

`0x001AA094` and `0x001AA0EC` update a cursor, use it to read a table word,
write distinct boolean bytes (1 and 0) into an indexed record, store the word,
and advance the index. Across two seeds each function passed 53 cases (212
total); six partial-fault probes per seed matched their faulting access and
observable prefix, and both wrong-boolean/missing-cursor controls were detected
per seed. No callers were verified. This is bounded to ordinary mapped RAM,
not a high-level record-type claim. Reproduce with:

```powershell
python tools/boolean_record_writer_experiment.py --code extracted/exefs/code.bin --samples 128 --seed 20261024 --output build/semantic-equivalence/group41-record-writers-seed20261024
python tools/boolean_record_writer_experiment.py --code extracted/exefs/code.bin --samples 128 --seed 7 --output build/semantic-equivalence/group41-record-writers-seed7
```

### Indexed halfword dispatch writers

`0x001DC648` and `0x001DC6A8` use a flag byte to select a halfword destination
and value from a dispatch table. Each passed 54 cases per function for seeds
`20261024` and `23063` (216 total), including alias cases. Across both reports,
all 12 partial-fault probes matched the invalid access, memory prefix and SP;
eight wrong-table/value controls were detected. At the interruption point
callee-saved scratch `r4/r5` differs, which is explicitly not claimed equivalent;
on normal returns the ABI-preserved state matches. No caller window is claimed.
Reproduce with:

```powershell
python tools/indexed_halfword_dispatch_experiment.py --code extracted/exefs/code.bin --samples 48 --seed 20261024 --output build/semantic-equivalence/indexed-halfword-dispatch/seed-20261024
python tools/indexed_halfword_dispatch_experiment.py --code extracted/exefs/code.bin --samples 48 --seed 23063 --output build/semantic-equivalence/indexed-halfword-dispatch/seed-23063
```

### VFP matrix-transpose initializers

`0x0023AFF0` and `0x002A1B4C` load 16 single-precision values and place them
into transposed matrix slots. Across seeds 7 and 20261024 they passed 128
comparisons per run (256 total), including lane-distinct patterns and
source/destination overlap; both negative controls per seed were detected.
The candidate uses 168 bytes versus 76-byte originals and spills 52 bytes
below entry SP before restoring SP; bytes above entry SP, output, access set,
and callee-saved state match. No callers or whole-game behavior are claimed.
Reproduce with:

```powershell
python tools/vfp_matrix_transpose_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/group-042-vfp-transpose/seed-20261024
python tools/vfp_matrix_transpose_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/group-042-vfp-transpose/seed-7
```

### Integer singleton leaves

Three 16-byte leaves at `0x00130FE8`, `0x0015C408`, and `0x002A17D4`
implement, respectively, a scaled increment, two adjacent word stores, and a
bit-16 predicate. Their C++ candidates are also 16 bytes but are not
byte-identical. Across seeds 20261024 and 20261025, they passed 3,112
comparisons total; wrong-arithmetic, wrong-offset, and wrong-bit controls were
detected. Unmapped-read and second-store fault probes matched the observed
fault state and partial writes. No callers, NZCV equivalence, write timing, or
MMIO behavior are claimed. Reproduce with:

```powershell
python tools/singleton_integer_leaves_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/singleton-integer-leaves/seed-20261024
python tools/singleton_integer_leaves_experiment.py --code extracted/exefs/code.bin --seed 20261025 --output build/semantic-equivalence/singleton-integer-leaves/seed-20261025
```

### Field round-trip and predicate leaves

Three 16-byte ARM leaves at `0x00146CE0`, `0x00146D10`, and `0x002523C0`
read then write back a halfword, read then write back a signed byte, and test
whether a word equals one. The compiled candidates are 16, 16, and 20 bytes,
respectively, and are not byte-identical. Across seeds 20261024 and 20261025,
they passed 3,608 comparisons, detected three targeted controls, and matched
three unmapped-read probes. A bounded ARM BL sweep found no direct callers; no
caller-window or flag equivalence is claimed. Reproduce with:

```powershell
python tools/field_roundtrip_predicate_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/field-roundtrip-predicate/seed-20261024
python tools/field_roundtrip_predicate_experiment.py --code extracted/exefs/code.bin --seed 20261025 --output build/semantic-equivalence/field-roundtrip-predicate/seed-20261025
```

### Fixed-byte record initializers and signed-halfword clamp

`0x002B63BC` and `0x002B6410` write distinct fixed 18-byte records; their
C++ candidates are 84 and 92 bytes. Across seeds 7 and 20261024, they passed
300 comparisons total, 12 partial-fault probes, and two controls per seed.
`0x001285C4` clamps signed halfwords at offsets 0 and 2 upward to 40 and 36,
and offsets 6, 8, and 10 downward to 145. Its 84-byte candidate for the
76-byte original passed 144 directed/random comparisons and four controls
across the same two seeds. These candidates are non-byte-identical and have no
verified caller windows. Reproduce with:

```powershell
python tools/fixed_byte_record_init_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/fixed-byte-record-seed20261024
python tools/fixed_byte_record_init_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/fixed-byte-record-seed7
python tools/signed_halfword_range_clamp_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/signed-halfword-clamp-seed20261024
python tools/signed_halfword_range_clamp_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/signed-halfword-clamp-seed7
```

### Mask and record helpers

`0x0023E634` clears five bits in a halfword; `0x00286700` initializes a record
using constants and three source words; and `0x002B540C` writes 11 sentinel
values selected by a bit mask. Their candidates are 76, 88, and 136 bytes
versus originals of 84, 76, and 140 bytes. Across two seeds they passed 384
comparisons and detected six targeted controls per seed. They are isolated,
non-byte-identical candidates with no caller windows claimed. Reproduce with:

```powershell
python tools/selected_flag_clear_and_struct_init_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/selected-flags-struct-mask-seed20261024
python tools/selected_flag_clear_and_struct_init_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/selected-flags-struct-mask-seed7
```

### Progress and sparse-record initializers

`0x00296F18` initializes/clamps signed fields and `0x003E8B44` writes progress
state according to a mask; together they passed 256 comparisons across two
seeds, including four alias cases and four detected controls per seed, plus
late-fault probes. `0x00140854` initializes sparse record bytes; it passed 130
comparisons, including a final-byte fault probe and two detected controls per
seed. Across all three functions that is 386 comparisons. Candidate sizes are
68, 88, and 88 bytes versus originals of 72, 92, and 88 bytes. The equal-size
initializer was checked to be byte-different. No callers or whole-game
behavior are claimed. Reproduce with:

```powershell
python tools/record_init_and_progress_writer_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/record-init-progress-seed20261024
python tools/record_init_and_progress_writer_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/record-init-progress-seed7
python tools/sparse_record_initializer_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/sparse-record-seed20261024
python tools/sparse_record_initializer_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/sparse-record-seed7
```

### UI VFP transpose helper

`0x002B7AA8` transposes a 4x4 matrix using VFP moves, with no floating-point
arithmetic. The C++ candidate is non-byte-identical. Across seeds 7 and
20261024 it passed 128 comparisons, including aligned overlap, and detected a
wrong-lane-order control. This is bounded to aligned ordinary RAM; no caller
window or whole-game behavior is claimed. Reproduce with:

```powershell
python tools/vfp_ui_transpose_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/vfp-ui-transpose/seed-20261024
python tools/vfp_ui_transpose_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/vfp-ui-transpose/seed-7
```

### Conditional mask-copy helper

`0x003E8BA0` conditionally copies four words from a source record according to
a mask. Its 72-byte C++ candidate is non-byte-identical to the 88-byte
original. Across seeds 20261024 and 20261025, it passed 278 comparisons,
detected a wrong-copy control, and matched both a pre-write fault and a
later-lane partial-write fault. It reproduces the observed `r0` return even
though no verified caller establishes whether that value is consumed. An
adjacent writer at `0x003E8B44` appears layout-compatible, but no dynamic or
call-site relationship is established. No caller window is claimed.
Reproduce with:

```powershell
python tools/conditional_mask_copy_003e8ba0_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/conditional-mask-copy-003e8ba0/seed-20261024
python tools/conditional_mask_copy_003e8ba0_experiment.py --code extracted/exefs/code.bin --seed 20261025 --output build/semantic-equivalence/conditional-mask-copy-003e8ba0/seed-20261025
```

### Indexed word-vector writer

`0x00151FF4` has a pinned 96-byte ARM body and a direct caller at
`0x0014D4B4`. The caller prepares `r0/r1`, then overwrites `r0` after the call,
so the candidate's return is not consumed there. The candidate reloads its
count before each lane store; aliasing the count with output can therefore
change later addresses. Two seeded differential runs passed 280 cases total,
detected negative controls, matched a partial-write fault, and passed the
bounded caller-window comparison. Three focused tests passed. The candidate
remains isolated and non-byte-identical; this does not establish all indirect
callers or the entire runtime contract.

```powershell
python -m unittest tests.test_indexed_word_vector_00151ff4_experiment -v
python tools/indexed_word_vector_00151ff4_experiment.py --code extracted/exefs/code.bin --seed 20261024
python tools/indexed_word_vector_00151ff4_experiment.py --code extracted/exefs/code.bin --seed 20261025
```

### Five-lane sparse-scale singleton

The 68-byte leaf at `0x002F28F8` multiplies five ordered single-precision
lanes through pointers stored at object offset `0x20`. Its C++ candidate is 72
bytes. Across seeds 7 and 20261024 it passed 776 comparisons, including a late
source-fault probe and wrong-lane/omitted-lane controls. Output, memory access
set, FPSCR, and callee-saved state matched within the tested RAM domain. No
caller window or whole-game behavior is claimed. Reproduce with:

```powershell
python tools/vfp_sparse_scale_002f28f8_experiment.py --code extracted/exefs/code.bin --seed 20261024 --output build/semantic-equivalence/vfp-sparse-scale-002f28f8/seed-20261024
python tools/vfp_sparse_scale_002f28f8_experiment.py --code extracted/exefs/code.bin --seed 7 --output build/semantic-equivalence/vfp-sparse-scale-002f28f8/seed-7
```

### Excluded bitstream experiment

The value model for `0x0016E468`, `0x00174A68`, and `0x0017B068` passed 6,144
isolated value comparisons over two seeds, all 256 shift residues, and four
high-bit patterns. However, these routines use a private register protocol:
they update `r1/r2/r3` and clobber `r9/r10`, contrary to a normal AAPCS C++
function contract. Only the first refill setup in three callers was established;
general caller liveness and the full value domain remain unknown. This is a
bounded bitstream model, not a drop-in C++ replacement, and is excluded from
the 168-candidate total.

### Excluded private-frame-pointer packing kernels

The six routines `0x001700CC`, `0x001766CC`, `0x0017CCCC`, `0x0016FFC4`,
`0x001765C4`, and `0x0017CBC4` average and repack byte channels into words at
four offsets separated by `0x400`. They use `r11` as an implicit data/frame
base and clobber callee-saved `r4–r9`; no direct ARM BL caller or full source
of that private calling convention was established. They are excluded from
the normal C++/AAPCS candidate count pending caller and `r11` contract evidence.

A wider 513–2048-byte sweep found three more repeated packing families whose
members use `r11` as a hidden cursor and clobber callee-saved registers. A
1008-byte ledger range at `0x002A263C` contains multiple return instructions
and likely concatenated entries; its function boundary is unresolved. None
was accepted as a semantic C++ candidate.

## Reproduce

From the experiment worktree, with your own verified extracted image:

```powershell
python -m pip install -r requirements-experiment.txt
python -m unittest tests.test_semantic_experiment -v
python tools/semantic_experiment.py --code E:/SMT4decomp/extracted/exefs/code.bin --samples 4096 --seed 20261024 --output build/semantic-equivalence/batch-002-callers/seed-20261024
python tools/semantic_experiment.py --code E:/SMT4decomp/extracted/exefs/code.bin --samples 4096 --seed 7 --output build/semantic-equivalence/batch-002-callers/seed-7
```

Use your actual private input path. No binary, asset, key or dump is needed in
version control. The generated image must stay local. Synthetic harness tests do
not require game data; the CLI requires the exact configured US revision.

## H1 title-menu family probes

These bounded H1 experiments are recorded separately from the accumulated
semantic-function count above because they model caller windows/families, not
new standalone functions:

- The navigation reducer executes pinned ARM windows with logical trigger
  results controlled and an observation-only stub for event `0x0100016C`;
  11 directed cases and 256 valid cursor/cache/trigger combinations pass.
- The touch reducer executes the two ARM touch scans with stable per-region
  helper results; 2,592 combinations match, including ordering between the
  selection and confirmation scans.
- The help-selection window uses the real 880-byte `TitleTable.tbb`; for all
  four cursor indices it selects the expected help-string pointer and color
  argument, stopping before `Camp_SetSlotMessage` renders anything.
- A continuity harness executes navigation, the original VFP animation window,
  and touch in one ARM machine with shared work/FP state. Three stable profiles
  match the hybrid reducers; a fourth ARM-only case records variable responses
  across all twelve touch-helper calls. The next blocker is the widget
  transition at `0x001E9F4C..0x001EA128`.
- A synthetic readiness-to-help path then executes both original readiness
  helpers and the original TBB getters with the real asset, for all four menu
  indices. It stops before `Camp_SetSlotMessage` and skips the widget mutation
  path; it proves neither runtime-normal fields nor rendered text.
- A continuous synthetic transition path executes the original widget mutator
  at `0x001EA070..0x001EA128`, both readiness and early-return fade helpers,
  then the original TBB getters with the real asset. For selection 0 it records
  111 ARM PCs, 38 reads and six writes before stopping at the same pre-renderer
  boundary. The conditional alpha calls and indirect fade callbacks are not
  reached; the synthetic flags/fields do not establish a runtime-normal path.
- A positive-gate probe enters the original `0x002872B0` fade body, records one
  indirect call's register/FP arguments, returns through an explicit one-
  instruction `bx lr` stub, then reaches the same TBB/help boundary. It records
  50 reads and 11 writes (including two stack saves); the stub is not the real
  game's callback. A second probe builds the indexed descriptor/record graph
  for `0x0020FFAC`, records its `BLX` ABI and original data writes, then reaches
  the same boundary through another explicit `bx lr` stub. Both traces are
  synthetic; neither identifies the game's real callback implementations.
- Separate first-gate variants execute the original callback candidates
  `0x0015555C` (type 0) and `0x00151404` (type 1) instead of a stub. Both
  reach the real TBB/help boundary; the type-1 path also executes its reached
  original callees. Constructor evidence links the candidates to different
  resource types, but the title asset's runtime type byte/pointer remain
  unknown, as does the second gate's actual callback. See the [callback target
  audit](title_real_callback_target_audit.md) and both callback reports.
- A separate second-gate experiment invokes both original candidates at
  `0x00210010` from a synthetic indexed track record. Type 0 returns `s0=0.6`
  without callback writes; type 1 returns `s0=0.25` and reaches original
  callees `0x0014D608`/`0x0015258C`, writing only to its modeled stack. Both
  reach the real TBB/help boundary with zero out-of-model reads. The first
  positive fade callback remains an explicit prerequisite stub; neither
  scenario proves which target the live track selects. See the [candidate
  comparison report](title_second_gate_callback_candidates_report.md).
- The local decrypted CCI's RomFS ranges for `title_top1.bam` and
  `title_top2.bam` were read without modifying the ROM; their SHA-256 values
  and the cross-check against `TitleTable.tbb` are recorded in the callback
  target audit. The files begin with `ATBC`, followed by `MDLSIGN` at `+0x80`
  and `CGFX` at `+0x100`; the file-header byte at `+0x10` is not the
  source-object type used to register a track callback. The new read-only BAM
  inventory decodes selected CGFX/CANM metadata, but not the serialization-to-
  runtime-loader graph. Static trace confirms that `AsdAnim_SetupTrack` reads
  `source+0x10` from an already-resolved runtime object; CANM stores a member
  type at `member+0x08`, with no proven mapping between them. Six direct setup
  callers pass resolved model/scene references, and no assignment to the source
  type byte was found. See the [asset-to-track audit](title_bam_track_source_type_mapping_audit.md)
  and [loader trace](title_canm_source_type_trace.md).
- Static title input masks at `0x004099C0` associate IDs 5/6 and E/F with
  bitmasks conventionally assigned to D-pad and Circle Pad up/down. The raw
  values and call chain are observed, but the button labels are an HID
  interpretation; Azahar input translation/repeat still needs a safe UI probe.
  See the [input-binding audit](title_input_binding_audit.md).
- A navigation-only Azahar 2126.2 check on the decrypted CCI confirmed the
  current keyboard profile's arrow-key Circle Pad and T/G D-pad mappings:
  isolated taps moved the title highlight between indices 0, 1 and 2 and
  updated the help line. No option was confirmed; physical-controller and
  held/repeat behavior remain untested.

Focused modules: `tests.test_title_navigation_family_experiment`,
`tests.test_title_touch_family_experiment`, and
`tests.test_title_help_presentation_experiment`, and
`tests.test_title_callback_continuity_experiment`, and
`tests.test_title_transition_ready_path_experiment`, and
`tests.test_title_transition_mutator_experiment`, and
`tests.test_title_transition_positive_gate_experiment`, and
`tests.test_title_transition_second_positive_gate_experiment`, and
`tests.test_title_transition_original_callback_experiment`, and
`tests.test_title_transition_callback_00151404_experiment`, and
`tests.test_title_second_gate_candidate_experiment`, and
`tests.test_title_bam_inventory` (29 title-focused tests total;
32 tests including the separate indexed-word-vector module). The BAM inventory
CLI was also run against the local decrypted CCI and reports three animations/
50 tracks for `title_top1` and three animations/43 tracks for `title_top2`.
These checks do
not establish physical button bindings, real touch coordinates,
visible rendering, complete callback behavior, or production integration. See the
[H1 milestone](../../docs/milestones/H1-main-menu-flow.md), the
[navigation audit](title_navigation_family_audit.md), and the
[help-selection audit](title_help_presentation_audit.md).

### Fresh signature-family audit (2026-10-24)

Parallel workers revisited three already-counted groups from the instruction
signature queue: three two-word zero initializers (group 18), three four-word
record writers (group 19), and two fixed two-word initializers (group 21).
Their address-specific reports preserve differences in evidence quality:
[group 18](group_18_zero_pair_report.md),
[group 19](group19_four_word_record_report.md), and
[group 21](fixed_pair_initializer_report.md). The two-seed runs passed 402,
6,216, and 16,396 function comparisons respectively; validated direct caller
windows and negative controls are reported per family. Group 18's callback
targets have registration evidence but no executed callback windows; group
19's caller sequences are static only; group 21 has two tested direct caller
windows, while its table-dispatched entry is untested. All remain isolated
semantic evidence: no production source or matching ledger changed, and these
audits do not increase the existing 169-candidate experiment total.

The latest focused commands passed 29 title tests plus three indexed-word-
vector control tests, 12 initializer-family tests, and three static-auditor
tests (47 total across the focused commands). These additions are now covered
by the full-repository regression below.

## Limits and next gate

The latest full repository regression ran **301 tests in 396.535 s** with no
failures; three extraction/key integration tests were skipped because
`aes_keys.txt` is not installed at the worktree root. The run includes all
translation-unit ARM and CMake build checks, the new BAM inventory, family
reports' tests, and the static candidate auditor. The cumulative semantic-
candidate total remains provisional: the source-symbol audit finds 164 versus
the previous aggregate of 169, and static test/report links do not establish
that each candidate is semantically approved.

The family queue resumed with three parallel scopes. Two tagged relative-payload
getters (`0x003E6974`, `0x003E69A8`) passed 2,064 differential comparisons per
seed under two seeds, four negative controls, and bounded null-fault parity; see
[`tagged_payload_getter_report.md`](tagged_payload_getter_report.md). Three
`EffPolygonThunder` functions passed an isolated point-count-prefix comparison
(646 cases per function, three negative controls), but this is not
full-constructor equivalence; see
[`eff_polygon_thunder_prefix_report.md`](eff_polygon_thunder_prefix_report.md).
Three TexConv clones passed projected output/memory comparisons (78 total and
four negative-control detections across two seeds), but the candidates differ
from the originals in `r7`/`r9` state and caller conventions are unresolved;
the report therefore marks full equivalence **false**:
[`texconv_sliding_average_experiment_report.md`](texconv_sliding_average_experiment_report.md).

The current static audit finds 173 candidate-prefixed symbols: 169
address-named function candidates plus four EffPolygonThunder prefix/control
helpers. All 173 link to test modules; 155 tests match the auditor's heuristic
for differential assertions. Static association is not approval. The old
aggregate also said 169, but this numeric coincidence does not reconcile its
scope or establish that all candidates are equivalent. Full-suite regression
is pending for these additions.

The two executions share one emulator backend, so hardware fidelity is not
independently established. There are no captured gameplay traces, floating-point
checks, concurrent observers, hardware registers, OS calls, timing guarantees or
formal proof. Pointer and alignment contracts restrict the tested input domain.
The replacement functions retain 32-bit target assumptions and are not a PC port.

Before broad adoption, boot the local patched image on a supported emulator or
console, verify padding loading and function execution, then compare reproducible
menu/battle/save scenarios against the original. Keep experimentally validated
functions separate from byte-matching claims until that integration gate passes.

The execution API follows the
[Unicorn tutorial](https://www.unicorn-engine.org/docs/tutorial.html).
