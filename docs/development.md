# Development and validation

The current build target is Nintendo 3DS ARMv6K. The repository compiles reconstructed translation units into objects and a static library; it does not yet link or package a runnable game. Native PC and Android ports are future work. The reconstructed layouts currently depend on 32-bit pointers and the original ABI.

## Setup

Use Python 3.10 or newer (the local validation environment uses Python 3.14), Clang with the ARM backend, CMake 3.20 or newer, and Ninja. Install the Python dependencies into a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Put the compiler and build tools on PATH. The Python build helper also searches standard Clang locations and accepts `CLANG_PATH` pointing to `clang++`. CMake must be able to find Ninja, or receive its absolute path through `-DCMAKE_MAKE_PROGRAM=...`.

Keep the compiler version consistent when comparing generated code. Exact matches are dependent on compiler version and flags; updating Clang requires rerunning the matching checks.

## Private game inputs

Supply a local CIA for the US revision identified in `config/game_info.json` and the corresponding `aes_keys.txt`. These inputs and extracted assets are ignored by Git.

```powershell
python tools/extract.py --cia "path/to/game.cia"
```

With no `--cia`, extraction only selects an input when the current directory contains exactly one CIA. Extraction validates the decompressed code against the configured SHA-256 before accepting it. Existing extracted code can also be checked explicitly:

```powershell
python tools/extract.py --check
```

## Compile and find semantic work

The Python build helper uses the canonical ARMv6K freestanding configuration:

```powershell
python tools/build_check.py
python tools/find_candidates.py --limit 30
```

The Python helper compiles independent translation units in parallel by default,
using the logical CPUs available to the process (8 on the current machine).
Use `--jobs N` / `-j N` to choose the worker count, or `--jobs 1` for a serial
build. It prints elapsed time, the number of workers, and rebuilt/up-to-date
counts. For example:

```powershell
python tools/build_check.py --force --jobs 8
```

`--force` rebuilds every translation unit; omit it for everyday incremental
builds. Cached objects are checked against source/header contents, compiler
identity, and flags. `--tu src/engine/leaf_matching.cpp` uses the same object path
and cache as the full build, avoiding a second compilation during the next audit.
A single translation unit still uses one compiler process; parallelism helps
when several files need work. Audit/emulation stages have their own CPU usage.
Audit commands also check object freshness.

The CMake build uses the same target and optimization settings:

```powershell
cmake -S . -B build/cmake-armv6k -G Ninja -DSMT4_ARMV6K=ON -DCMAKE_CXX_COMPILER=clang++
cmake --build build/cmake-armv6k --parallel 8
```

This produces a static library, which does not check that all external symbols can be resolved into an executable. The tests separately compare the CMake object code for functions marked `matching` when the original code is available.

## Tests

Run all available tests, including private integration tests when their inputs exist:

```powershell
python -m unittest discover -s tests -v
```

Run the same suite with private integration tests explicitly disabled:

```powershell
$env:SMT4_SKIP_PRIVATE_TESTS = "1"
python -m unittest discover -s tests -v
Remove-Item Env:SMT4_SKIP_PRIVATE_TESTS
```

Tests requiring missing local game files skip with a reason. Synthetic extraction and verifier regression tests remain available without those inputs. Compiler tests require Clang; CMake tests additionally require CMake and Ninja.

For tooling changes, run focused regressions and `git diff --check`. Compiler, flags, ABI, or build changes additionally require a forced ARM build, affected consumers, and CMake checks. Run the exact audit when exact-reference claims or their verifier change; byte equality is not a semantic acceptance gate.

## Find semantic reconstruction candidates

Semantic discovery is the default. It searches the original function ledger
regardless of byte-match status, ranks H1 dependencies from
`config/reconstruction.json`, includes functions with calls, and omits already
written experimental C++ from the new-work queue:

```powershell
python tools/find_candidates.py --limit 30 --output build/semantic-equivalence/semantic-queue.json
python tools/find_candidates.py --include-existing-candidates --limit 30
```

The second command includes candidates that need validation or integration;
presence does not imply a pass. The default size ceiling is 8192 original bytes;
use `--max-size 0` to remove it, or category/status filters to narrow the scope.
The explicit `--mode leaf --status matching --asm-backed-only` path preserves the
old small-leaf triage when it helps a particular task. It is not the main goal.

Follow the [per-function workflow](function-reconstruction-workflow.md): recover a
contract, write clear C++, run differential and caller checks, then integrate a
coherent batch. Different machine code and function sizes are accepted when
behavior is supported. Do not add volatile or distort types merely for byte
identity. Keep exact labels truthful and semantic evidence separate.

## Progress definitions

An isolated [behavioral equivalence pilot](../experiments/semantic_equivalence/README.md)
compares compiled C++ candidates with their original ARM code. The
[generated inventory](semantic-inventory.md) separates candidate definitions from
static test/report links; [functional status](functional-status.md) tracks the
integration goal without treating candidate presence as completion.
Run it with the optional `requirements-experiment.txt` dependencies and
`python tools/semantic_experiment.py --code <private-code.bin>`. It emits local
reports and an experimental patch under ignored `build/`; these results do not
change matching status or establish a complete game boot.

Only `matching` verifies exact machine code against the original binary. Relocations are accepted only when their type and symbol are supported and the encoded instruction can be checked against an unambiguous ledger target; currently that is limited to canonical ARM-state `R_ARM_CALL` relocations. Every other unresolved relocation remains ineligible for an exact match. The compiled-coverage tier uses a size threshold (at least 15% of the original function size, with a small minimum) to distinguish larger reconstructions from drafts. It does not establish equivalent behavior. Explored coverage includes stubs and should not be treated as runnable or completed game code.

Use `python tools/progress.py --write` to regenerate the progress report and README from the reporting tool. Update that generator when changing generated documentation.

## Safe analysis and automated matching

`python tools/analyze_code.py` writes heuristic proposals and a boundary-difference
report to `build/analysis/`. The Python API is read-only by default. Even when
writing a proposal, it refuses to overwrite curated configuration files. A changed
function size does not inherit an existing matching claim. Review discoveries
against disassembly before accepting them into `config/functions.csv`.

`python tools/asm_diff.py --addr <address>` returns exit code 0 only for an exact
match, and 1 for a mismatch, compilation failure, or missing symbol. A semantic
candidate can intentionally differ in bytes: validate it with its differential
runner and caller tests, keeping its status separate from exact matching.

`python tools/progress.py --write` regenerates the README with links to the
functional roadmap and generated inventory; detailed functional state lives in
`docs/functional-status.md` and the milestone records.

## Multi-agent batch coordination

Use [the agent workflow](agent-workflow.md) and the coordinator-owned H1 board.
`python tools/agent_workflow.py check` validates dependencies, ownership and
resource allocation; `ready` lists schedulable tasks and `prepare` generates a
fresh source-hashed brief. The tool does not spawn agents or certify equivalence.
Workers must use separate output directories/files and inspect test side effects.
The default object cache, full regression, shared runner edits and runtime profile
are integrator-owned resources. Never run several default eight-job build processes
against the same output directory. See the workflow for handoff/provenance checks.
