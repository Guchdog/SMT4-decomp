# ARM behavioral equivalence pilot — 2026-10-24

Seven previously rejected C++ reconstructions passed **144,004 differential
function cases** and **1,558 original-caller-window cases** across two seeds.
None produces the original bytes. Six deliberately incorrect controls were
detected for their intended errors in both runs. These are bounded execution
results, not a proof that a complete rebuilt game behaves identically.

The experiment is isolated on `codex/semantic-equivalence-experiment`, based on
`681ac82`. It leaves `src/`, `include/`, the matching ledger, original private
image, and the primary checkout's pending README/progress edits unchanged.
Experimental candidates do not increase the exact reconstruction count.

For subsequent functions, use the [per-function procedure](../../docs/function-reconstruction-workflow.md),
its [record template](../../docs/templates/function-reconstruction.md), and the
[completed byte-getter example](../../docs/function-records/0x00394614.md).
The current runner is specialized for this pilot; that procedure identifies
the code and scenarios that must be extended before testing a new function.

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

The sample represents 140 original bytes, approximately 0.00446% of the text
segment. It was deliberately selected for known compiler differences; its
success rate must not be extrapolated to the whole game.

| Seed | Random cases per function | Function comparisons, including boundaries | Caller comparisons | Full pilot elapsed |
|---|---:|---:|---:|---:|
| `20261024` | 16,384 | 115,010 | 779 | 44.86 s |
| `7` | 4,096 | 28,994 | 779 | 12.41 s |

Each run includes compilation (about 0.27 s), negative controls, patch generation,
and execution. Timings are local observations under concurrent regression-test
load, not a controlled performance benchmark. They exclude manual reconstruction,
harness development, and the full repository suite. This demonstrates that seven
functions blocked by byte equality can be retained as tested experimental C++;
it does not establish an end-to-end project speedup factor or faster game code.

## What actually executes

`candidates.cpp` is compiled by the existing ARMv6K Clang pipeline with the
repository's `-O2`, ARM11 MPCore, VFPv2 and hard-float options. The local compiler
was Clang 23.1.3; the CPU backend was Unicorn 2.1.4, model ARM11 MPCore.

The original is read from the user's decompressed `code.bin`, checked against
the configured size and SHA-256 before execution. Both versions execute as
ARM instructions, not as Python rewrites of their algorithms. The reference hash
is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The tool checks the following after every run:

- Return register `r0` for all seven functions, including pointer preservation
  for functions whose complete original return type remains uncertain.
- Callee-saved `r4-r11`, `SP`, and `d8-d15` against their initial values.
- All test RAM, live caller stack bytes, and observable read/write byte sets.
- Expected return/continuation and bounded execution without a CPU/memory fault.

Caller-saved temporary registers and leaf-function condition flags may differ.
The caller-window tests additionally compare condition flags and the actual
continuation after the caller's conditional branch. Internal stack scratch and
the order of ordinary RAM accesses are not required to match.

Inputs include integer boundaries, seeded random values and surrounding memory,
all 256 byte-equality inputs, and four valid byte-reader aliases where the input
cursor points into its own pointer representation. Halfword/pointer/record
alignment is respected. Relative offsets stay within the bounded fixture's
accessible payload; the fixture does not assert an actual game record size.

Negative controls intentionally introduce `>=` instead of `>`, the wrong byte
constant, the wrong cursor stride, incorrect alias-sensitive load/store ordering,
the wrong flag bit, and a clobbered callee-saved register. A fault or timeout is
always failure, even if both versions fail the same way. Controls must fail for
the expected reason, not merely trigger any error.

## Patched-image integration

The local image has 2,524 zero bytes between the logical text end `0x003FE624`
and its existing page boundary `0x003FF000`. The tool places the 144 compiled
bytes in that padding and replaces the seven original entries with ARM branches.
It rejects relocations, PC-relative replacements, calls, floating-point code,
nonzero padding, invalid bounds, and insufficient padding. No segment offsets,
file length, original data, or matching source definitions are moved.

All positive function comparisons execute this **same patched-image layout**.
Two original call windows also execute their unchanged BL and subsequent
comparison/branch instructions:

- `0x001B0370`: caller passes `r5` to `0x002AE464`; both continuations
  `0x001B0384` and `0x001B0394` were exercised.
- `0x001B4DBC`: caller passes a stack byte to `0x00394614`; both continuations
  `0x001B4DD0` and `0x001B4DF4` were exercised.

Successful runs emit ignored, local-only artifacts:

- `build/semantic-equivalence/report.json`: versions, hashes, seed, counts,
  timings, patch manifest, counterexamples for controls, and limitations.
- `build/semantic-equivalence/code.experimental.bin`: derived 3,633,152-byte image.
- `build/semantic-equivalence/code.ips`: 250-byte patch containing generated
  branches and generated C++ machine code. Independent IPS replay reproduced
  the tested image exactly. Both seeds generated identical patch/image hashes.

Patched image SHA-256:
`f33a1153b8f41415bc32d24afb463364e5724377b1c8b38ec1ad9602a6ad7c4f`.
IPS SHA-256:
`433d3f0fadcb49f7d6b23286c546e4510e4fd20cba6568024ba7d02ad6234955`.

**A complete game was not booted.** The harness maps the existing text pages
including padding; preservation/execution of those bytes by a real 3DS loader
still needs to be tested. No Azahar/Citra executable was found on PATH or through
the inspected Windows uninstall entries; a portable installation elsewhere was
not ruled out. The repository still has no full executable linking/package target.

Luma3DS documents external decompressed code and IPS loading under
`/luma/titles/<TitleID>/` in its
[official optional-features documentation](https://github.com/LumaTeam/Luma3DS/wiki/Optional-features).
This provides a next integration route, not evidence that this patch has already
booted. No emulator configuration, console, installation or saves were modified.

## Reproduce

From the experiment worktree, with your own verified extracted image:

```powershell
python -m pip install -r requirements-experiment.txt
python -m unittest tests.test_semantic_experiment -v
python tools/semantic_experiment.py --code E:/SMT4decomp/extracted/exefs/code.bin --samples 16384
python tools/semantic_experiment.py --code E:/SMT4decomp/extracted/exefs/code.bin --samples 4096 --seed 7 --output build/semantic-equivalence-seed7
```

Use your actual private input path. No binary, asset, key or dump is needed in
version control. The generated image must stay local. Synthetic harness tests do
not require game data; the CLI requires the exact configured US revision.

## Limits and next gate

Final regression checks: `python -m unittest discover -s tests -v` ran 63 tests
in 324.326 s, with no failures and three extraction/key integration tests skipped
because the private root-level keys were not copied into the worktree. The game
byte audits, all-translation-unit ARM build, fresh CMake build and the ten new
oracle tests ran. `python tools/verify_decomp.py` independently retained all
10,959 matching functions and eight exact raw spans, with zero matching or
compilation failures. `git diff --check` passed.

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
