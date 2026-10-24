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

## Compile and audit

The Python build helper uses the canonical ARMv6K freestanding configuration:

```powershell
python tools/build_check.py --force
python tools/verify_decomp.py
python tools/progress.py
```

`--force` rebuilds every translation unit. Incremental compilation must invalidate cached objects when dependencies, flags, or compiler identity change. Audit commands also check object freshness.

The CMake build uses the same target and optimization settings:

```powershell
cmake -S . -B build/cmake-armv6k -G Ninja -DSMT4_ARMV6K=ON -DCMAKE_CXX_COMPILER=clang++
cmake --build build/cmake-armv6k
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

Before considering a tooling change complete, run the relevant tests, force the ARM build, run the audit, build through CMake, and run `git diff --check`.

## Find semantic reconstruction candidates

Follow the [per-function reconstruction and validation procedure](function-reconstruction-workflow.md)
for exact and experimental behavioral work. It defines contracts, attempt records,
negative controls, batch checks and separate ARM/caller/full-game acceptance gates.

The ledger can be 100% byte-matching while functions are still represented by
inline assembly or `.incbin` wrappers. To find small, call-free wrappers that
are good candidates for replacement with readable C++, run:

```powershell
python tools/find_candidates.py --status matching --asm-backed-only --max-size 64 --limit 80
```

The default remains `--status todo` for compatibility. Inspect a candidate
before editing it, then verify the exact function after rebuilding its
translation unit:

```powershell
python tools/split_asm.py --addr 0x00121d70
python tools/build_check.py --tu src/engine/leaf_matching.cpp
python tools/asm_diff.py --addr 0x00121d70
```

Semantic cleanup must not reduce the byte-exact baseline. Keep the exact
`DECOMP_FUNC` address, size, and ledger symbol, and prefer small coherent
batches that can be reverted independently.

## Progress definitions

An isolated [behavioral equivalence pilot](../experiments/semantic_equivalence/README.md)
compares seven non-byte-identical C++ candidates with their original ARM code.
Run it with the optional `requirements-experiment.txt` dependencies and
`python tools/semantic_experiment.py --code <private-code.bin>`. It emits local
reports and an experimental patch under ignored `build/`; these results do not
change matching status or establish a complete game boot.

Only `matching` verifies exact machine code against the original binary. Relocations are accepted only when their type and symbol are supported and the encoded instruction can be checked against an unambiguous ledger target; currently that is limited to canonical ARM-state `R_ARM_CALL` relocations. Every other unresolved relocation remains ineligible for an exact match. The compiled-coverage tier uses a size threshold (at least 15% of the original function size, with a small minimum) to distinguish larger reconstructions from drafts. It does not establish equivalent behavior. Explored coverage includes stubs and should not be treated as runnable or completed game code.

Use `python tools/progress.py --write` to regenerate the progress report and README from the reporting tool. Update that generator when changing generated documentation.
