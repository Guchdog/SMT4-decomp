# ARM behavioral equivalence pilot — 2026-10-24

Fourteen non-byte-identical typed C++ reconstructions passed **450,814 differential
function cases** and **15,660 original-caller-window cases** across four batches.
Fourteen deliberately incorrect controls were detected for their intended errors.
These are bounded execution results, not a proof that a complete rebuilt game
behaves identically.

The experiment is isolated on `codex/semantic-equivalence-experiment`, based on
`681ac82`. It leaves `src/`, `include/`, the matching ledger, original private
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

## Limits and next gate

The full repository regression `python -m unittest discover -s tests -v` ran 83
tests in 323.905 s, with no failures and three extraction/key integration tests
skipped because `aes_keys.txt` is not installed at the worktree root. The game
byte audits, all-translation-unit ARM build, fresh CMake build and TBB semantic
tests ran. The 30 focused semantic/TBB tests also passed, and `git diff --check`
was clean.

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
