# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation

Decompilation and reverse-engineering project for **Shin Megami Tensei IV** (Nintendo 3DS, US v0.1.0, Title ID `00040000000E5C00`, internal codename `sdds4`), aimed at recovering modifiable C++20 source code. The current build targets 3DS ARMv6K objects and a static library; linking a runnable game and PC / Android ports are future work.

> **Legal Notice:** This repository contains **no copyrighted ROM data, binaries, encryption keys, or extracted assets**. You must supply your own legally dumped `.cia` copy of *Shin Megami Tensei IV* (`CTR-P-AMXE`) and `aes_keys.txt` locally to extract `code.bin` and `RomFS`.

---

## Live Decompilation Progress

- **Matching (Byte-for-Byte):** `3,139,108 / 3,139,108 bytes` (**100.0000%**) across `10,959` functions and `8` explicitly labeled raw spans (each exact-checked against 3DS ARMv6K code.bin)
- **Compiled Coverage (≥15% size):** `0 / 3,139,108 bytes` (**0.0000%**) across `0` functions (ARMv6K compilation and size threshold only; logic unverified)
- **Draft Logic (<15% size):** `0 / 3,139,108 bytes` (**0.0000%**) across `0` functions (early-stage draft reconstructions)
- **Scaffolded Architecture (Stubs & Interfaces):** `0 / 3,139,108 bytes` (**0.0000%**) across `0` functions (headers, structs, function skeletons)
- **Total Codebase Explored:** `3,139,108 / 3,139,108 bytes` (**100.0000%**) across `10,959` functions and `8` exact raw spans (all explored bytes mapped into `src/`)
- See [`PROGRESS.md`](PROGRESS.md) for the full subsystem breakdown (`ui`, `camp`, `battle`, `script_vm`, `shop`, `unite`, `engine`, `nn_sdk`, `crt`) and explored function ledger. Coverage totals use original function sizes and do not measure behavioral equivalence.

---

## Quick Start

For the functional reconstruction roadmap, see the [milestone plan](docs/reconstruction-milestones.md) (Spanish): areas, testable scenarios, acceptance criteria, and subagent responsibilities. Implement each batch using the [per-function workflow](docs/function-reconstruction-workflow.md). Exact byte coverage above is separate from reconstructed C++ behavior and milestone completion.

**Current functional milestone:** H0's batch-4 title → Audio Settings → title smoke test is recorded; H1 maps the main-menu flow. Isolated ARM family experiments cover title navigation, touch reduction, help-string selection, the widget-transition mutator, and both positive fade-gate bodies through the real TBB help lookup. At both gates, separate original-code scenarios exercise candidates `0x0015555C` (type 0) and `0x00151404` (type 1); the title's actual runtime callback pointers remain unknown. A read-only BAM inventory confirms 50 animation tracks in `title_top1` and 43 in `title_top2`, but does not map serialized tracks to live callbacks. Parallel signature-family audits added reports for eight existing candidates across three initializer/writer families. A static audit finds 164 candidate C++ symbols against the previously reported 169; both this reconciliation and the semantic aggregate are provisional, and static links do not prove tests ran. The full local suite passes 301 tests (3 private CIA/key skips). Official matching progress is unchanged. A navigation-only Azahar check confirmed the current keyboard profile's Circle Pad (arrows) and D-pad (T/G) bindings on the original CCI; no menu option was confirmed. These are partial experiments, not a reconstructed/integrated menu callback, patched-game verification, or visible-renderer validation. See the [H1 flow and acceptance record](docs/milestones/H1-main-menu-flow.md) and [experiment evidence](experiments/semantic_equivalence/README.md).

Install Python dependencies with `python -m pip install -r requirements.txt`. Clang is required for ARM compilation; CMake and Ninja are required for the CMake build. See [development setup](docs/development.md) for compiler configuration, build commands, and tests. Run `python -m unittest discover -s tests -v` for tests; tests requiring private game files skip when those files are absent.

### 1. Extract `code.bin` and UI/HUD Assets from Your Local CIA
Place your `.cia` and `aes_keys.txt` in the repository root (both are automatically ignored by `.gitignore`) and run:
```powershell
python tools/extract.py
```
This auto-selects a CIA only when exactly one is present; otherwise pass `--cia path/to/game.cia`. It decrypts the CIA, decompresses the BLZ-compressed `ExeFS/.code` into `extracted/exefs/code.bin` (`0x377000` bytes), verifies its size and SHA-256 against the configured revision by default, indexes all 20,126 RomFS files in `extracted/romfs_index.json`, and extracts UI/HUD folders.

### 2. Analyze Functions & Subsystem Xrefs
```powershell
python tools/analyze_code.py
```
Scans all `3,139,108` bytes of `.text` (`0x00100000`–`0x003FE624`), resolves literal pools and inline `ADR` strings (including original Atlus `c:\SMT4\XRD686\...` source file paths), and populates [`config/functions.csv`](config/functions.csv) and [`config/symbols.csv`](config/symbols.csv).

### 3. Disassemble Any Function or HUD Subsystem
```powershell
# Disassemble a specific function by address or original Atlus source name:
python tools/split_asm.py --addr 0x002ac2f4
python tools/split_asm.py --name StatusDown --limit 3
python tools/split_asm.py --category ui --limit 10
```

### 4. Inspect `.tbb` (`TBCR`/`TBL1`) UI Tables and `.bf` (`FLW0`) FlowScripts
```powershell
python tools/inspect_assets.py extracted/romfs/saveLoadUI/SaveLoadUITable.tbb extracted/romfs/saveLoadUI/saveloadUI.bf
```

### 5. Verify Progress & Update `PROGRESS.md`
```powershell
python tools/progress.py --write
```

---

## Project Structure

- [`config/game_info.json`](config/game_info.json) — Memory map and binary metadata for `CTR-P-AMXE`.
- [`config/functions.csv`](config/functions.csv) — Master ledger of 10,959 callable functions and 8 explicitly labeled non-function spans covering 100% of `.text` (`3,139,108` bytes).
- [`config/symbols.csv`](config/symbols.csv) — String and data symbols recovered from `.rodata`, `.data`, and `.text` literal pools.
- [`include/`](include/) & [`src/`](src/) — Decompiled C++20 source code and engine/UI headers.
- [`docs/architecture.md`](docs/architecture.md) — Documentation of the `XRD686` / `AsdSDK` engine, dual-screen LCD pipelines, and `TBCR`/`TBL1` UI table formats.
- [`tools/`](tools/) — Extraction, static analysis, annotated disassembly, asset inspection, and progress verification scripts.
