# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation

Decompilation and reverse-engineering project for **Shin Megami Tensei IV** (Nintendo 3DS, US v0.1.0, Title ID `00040000000E5C00`, internal codename `sdds4`), aimed at recovering modifiable C++20 source code. The current build targets 3DS ARMv6K objects and a static library; linking a runnable game and PC / Android ports are future work.

> **Legal Notice:** This repository contains **no copyrighted ROM data, binaries, encryption keys, or extracted assets**. You must supply your own legally dumped `.cia` copy of *Shin Megami Tensei IV* (`CTR-P-AMXE`) and `aes_keys.txt` locally to extract `code.bin` and `RomFS`.

---

## Primary goal: editable C++ semantics

Find and reconstruct readable C++ with supported behavior. Byte-for-byte identity is not an acceptance requirement. Prioritize coherent milestone behavior, differential/caller evidence, and integration; do not optimize the project around matching opcodes.

Follow the [functional status](docs/functional-status.md), [milestone plan](docs/reconstruction-milestones.md), and [per-function workflow](docs/function-reconstruction-workflow.md). The [generated candidate inventory](docs/semantic-inventory.md) measures experimental definitions and static evidence links, not equivalence or integration. Milestones H0, H1, H2, H3, and H4 are completed and closed.

Use the [agent workflow](docs/agent-workflow.md) for bounded parallel contracts, implementation and independent review; the coordinator owns shared files, integration and the CPU budget.

Find new semantic work or review existing C++ for validation/integration:

```powershell
python tools/find_candidates.py --limit 20
python tools/find_candidates.py --include-existing-candidates --limit 20
```

## Reference byte coverage

- **Matching (Byte-for-Byte):** `3,139,108 / 3,139,108 bytes` (**100.0000%**) across `10,959` functions and `8` explicitly labeled raw spans (each exact-checked against 3DS ARMv6K code.bin)
- **Readable C++ reconstructions:** `60` functions have been converted from assembly wrappers to typed C++ while retaining byte-for-byte ARMv6K output. Recent batches cover engine state/accessors, UI and camp record updates, shop/texture comparators, Script VM helpers, queue/list operations, record initialization, float state updates, a zeroing helper, and a state getter. These semantic milestones are tracked separately from the size-based coverage categories below.
- **Compiled Coverage (≥15% size):** `0 / 3,139,108 bytes` (**0.0000%**) across `0` functions (ARMv6K compilation and size threshold only; logic unverified)
- **Draft Logic (<15% size):** `0 / 3,139,108 bytes` (**0.0000%**) across `0` functions (early-stage draft reconstructions)
- **Scaffolded Architecture (Stubs & Interfaces):** `0 / 3,139,108 bytes` (**0.0000%**) across `0` functions (headers, structs, function skeletons)
- **Total Codebase Explored:** `3,139,108 / 3,139,108 bytes` (**100.0000%**) across `10,959` functions and `8` exact raw spans (all explored bytes mapped into `src/`)
- See [`PROGRESS.md`](PROGRESS.md) for the full subsystem breakdown (`ui`, `camp`, `battle`, `script_vm`, `shop`, `unite`, `engine`, `nn_sdk`, `crt`) and explored function ledger. Coverage totals use original function sizes and do not measure behavioral equivalence.

---

## Quick Start

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
Scans all `3,139,108` bytes of `.text` (`0x00100000`–`0x003FE624`), resolves literal pools and inline `ADR` strings (including original Atlus `c:\SMT4\XRD686\...` source file paths), and writes review proposals to `build/analysis/functions.csv`, `symbols.csv`, and `ledger_diff.json`. The curated files in `config/` are never overwritten; review boundary changes before manually accepting individual discoveries.

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
