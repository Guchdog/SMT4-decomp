# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation

Decompilation and reverse-engineering project for **Shin Megami Tensei IV** (Nintendo 3DS, US v0.1.0, Title ID `00040000000E5C00`, internal codename `sdds4`), aimed at recovering modifiable C++20 source code. The current build targets 3DS ARMv6K objects and a static library; linking a runnable game and PC / Android ports are future work.

> **Legal Notice:** This repository contains **no copyrighted ROM data, binaries, encryption keys, or extracted assets**. You must supply your own legally dumped `.cia` copy of *Shin Megami Tensei IV* (`CTR-P-AMXE`) and `aes_keys.txt` locally to extract `code.bin` and `RomFS`.

---

## Primary goal: editable C++ semantics

Find and reconstruct readable C++ with supported behavior. Byte-for-byte identity is not an acceptance requirement. Prioritize coherent milestone behavior, differential/caller evidence, and integration; do not optimize the project around matching opcodes.

Follow the [functional status](docs/functional-status.md), [milestone plan](docs/reconstruction-milestones.md), and [per-function workflow](docs/function-reconstruction-workflow.md). The [generated candidate inventory](docs/semantic-inventory.md) measures experimental definitions and static evidence links, not equivalence or integration. Milestone status lives in the functional and reconstruction plans. H2 (title audio settings) remains open: earlier paired runtime evidence stopped before readiness and re-entry, and the per-function conversions below do not close that milestone.

Use the [agent workflow](docs/agent-workflow.md) for bounded parallel contracts, implementation and independent review; the coordinator owns shared files, integration and the CPU budget.

Find new semantic work or review existing C++ for validation/integration:

```powershell
python tools/find_candidates.py --limit 20
python tools/find_candidates.py --include-existing-candidates --limit 20
```

## Full C++ reconstruction and native port progress

The [full reconstruction and native port plan](docs/native-port-plan.md) tracks every inventoried function and raw span through classification, readable C++ or a documented portable replacement, and contract-specific validation. Native gameplay scenarios are tracked separately from per-function coverage.

| Progress dimension | Current baseline |
| --- | --- |
| Original inventory | 10,959 functions and 8 raw spans; boundaries require audit |
| Readable byte-identical C++ | 60 functions reported by the historical exact ledger; this is not a complete semantic count |
| Experimental candidate inventory | 188 address-named definitions and 21 prefix/control/helper definitions in the [generated snapshot](docs/semantic-inventory.md); static presence is not validation or integration |
| Classified, integrated and contract-validated across the full inventory | Baseline audit pending; these dimensions must be counted separately |
| Native game scenarios without original ARM code | Not established; H20 tests isolated host HAL components |

The historical 100% exact-byte baseline is retained as a recoverable reference, not a claim about the current semantic ledger. H19's composite ARM image retains original code; H20's host tests do not establish a native game build. The next step is the reproducible P0 inventory audit described in the plan.

## Recent H2 C++ semantic progress

The following H2 functions have typed C++ definitions, with ledger classifications and per-function evidence recorded below. Several are bounded helpers that retain original ARM services. The paired runtime comparison establishes parity only for its defined scripted scenario on the recorded cumulative image; it does not establish whole-game or full H2 equivalence.

| Address | Reconstructed behavior | Recorded evidence |
| --- | --- | --- |
| `0x00221168` | `titleConfig` nested callback slice | 20 paired callback returns and 19 checkpoints; readiness and re-entry remain incomplete. [Function record](docs/function-records/0x00221168.md) |
| `0x0028DF54` | H2 state-field writes and raw return | 64 direct cases, 64 compositions through original `0x00286928`, one negative control; RAM/ordering limits documented. [Function record](docs/function-records/0x0028df54.md) |
| `0x002C1F28` | Signed global predicate and byte return | 153 direct cases, 32 zero-result caller compositions, three negative controls; six named callsites audited. [Function record](docs/function-records/0x002c1f28.md) |
| `0x002B89A0` | Null or manager-mode predicate | 139 direct cases, 32 nonzero caller continuations, three negative controls; caller entry is asserted. [Function record](docs/function-records/0x002b89a0.md) |
| `0x002AF854` | Indexed field selection with ordered alias-safe accesses | 503 direct cases, 32 disjoint and 32 cross-alias compositions through original `0x002B8D24`, five controls; selector-12 cross-call aliasing is covered by two five-call chains for one documented topology. [Function record](docs/function-records/0x002af854.md) |
| `0x002CAB70`, `0x0021F39C`, `0x002E0AF4` | `titleConfig` config-byte-to-index mappers | Two 512-case runs per mapper, each covering all 256 byte values, plus production-image checks and initializer caller compositions. [Mapper records](docs/function-records/0x002cab70.md), [0x0021F39C](docs/function-records/0x0021f39c.md), [0x002E0AF4](docs/function-records/0x002e0af4.md) |
| `0x002BF030` | Sentinel-counted table selector, retaining original service `0x00138934` | 128 direct cases, 24 compositions through original `0x002B8D24`, six negative controls; full service branches and cumulative H2 runtime remain open. [Function record](docs/function-records/0x002bf030.md) |
| `0x002B8D24` | Typed selector dispatcher, retaining original helpers `0x002AF854`, `0x002BF030` and `0x001384F0` | 116 direct cases, two selector-11 caller compositions, two five-call selector-12 cross-alias chains and seven controls; 356/360 bytes. Paired cumulative-image H2 runtime matched 19/19 checkpoints across 51 scripted actions; a hit at this helper is unverified, and readiness/re-entry still prevent H2 closure. [Function record](docs/function-records/0x002b8d24.md) |
| `0x00286928` | Typed titleConfig state dispatcher, retaining its original callees | 296 direct cases, four compositions through original callback `0x00221168`, six negative controls; 812/820 bytes and 22 ARM call relocations. Cumulative paired runtime captured 129/129 helper hits with arguments/returns matched and 19/19 checkpoints across 51 actions; readiness/re-entry are incomplete, so H2 remains open. [Function record](docs/function-records/0x00286928.md) |
| `0x002B0188` | Group manager-table resolver with preserved `node_index` tail-call ABI | 261 direct cases, signed quotient boundaries, null entries and two detected mutations. The final-address body matches the 24-byte original; full build 204/204. [Function record](docs/function-records/0x002b0188.md) |
| `0x002B787C` | `AsdText_GetLineCount`, retaining original text-code helpers | 515 direct cases, selector 11/19 caller compositions, six controls; 176/176 bytes and two ARM call relocations. Final-address staged differential passed. Paired Azahar scenario matched 19/19 H2 checkpoints; a GDB-controlled direct invocation returned/consumed `1` in both profiles. The normal H2 selector-6 route does not reach this helper, and the probe does not establish natural runtime caller reachability. [Function record](docs/function-records/0x002b787c.md) |
| `0x002AE6B0` | `AsdText_IsControlCode`, unsigned predicate for `[0xF801, 0xF88F]` | Exhaustive 65,536 halfword values, 18 directed and 512 seeded 32-bit cases, two boundary mutation controls, and selector 11/19 partial compositions through original callers (other services stubbed; imported harness hashes not pinned); 24/24 bytes with no relocations, but bytes differ. Runtime not run for this helper. [Function record](docs/function-records/0x002ae6b0.md) |
| `0x002AE664` | ASD control-code mapping helper used by `AsdText_GetLineCount` | 65,798 direct values, three table layouts, two detected mutations; 515 line-count cases plus selector 11/19 compositions through original callers. Candidate 56/76 bytes, zero relocations; bytes differ. Stack spill and runtime limits are documented. [Function record](docs/function-records/0x002ae664.md) |
| `0x002BF41C` | Task-registration lookup for `TitleConfig_IsReady` | All 4,096 bucket indices, empty/boundary handles, 5 chain probes, 64 seeded chains, two mutations; five compositions through the original ready gate. 68/68 bytes, no relocations, but bytes differ. Runtime/scheduler lifecycle not run. [Function record](docs/function-records/0x002bf41c.md) |
| `0x002B88C4` | Touch-region registration used by titleConfig and UI callers | Staged into H2 run-013 with a slot-only IPS overlay; 58/58 original-versus-staged caller-chain cases and two mutations detected. Body 156/220 bytes; independent review accepted offline integration. Runtime and scheduler lifecycle remain unverified. [Function record](docs/function-records/0x002b88c4.md) |
| `0x002A63F8` | `AsdRes_IsLoaded`, testing bit 2 of the resolved resource record | 8 direct fixtures plus the original null-result fault, three compositions through the actual `TitleConfig_Calc` call slice, and two negative controls. Staged as a 24-byte one-slot IPS overlay; independent review confirmed the staged null fault at offset 8 and the `non_matching` ledger label. Runtime is not run. [Function record](docs/function-records/0x002a63f8.md) |
| `0x002B96F0` | Typed 24-byte group-table resolver and subindex tail call | 103 direct fixtures, paired `TitleConfig_Calc` caller compositions, group-stride mutation detected, and second-index mutation rejected for exceeding the slot. Final-VMA relocation produces the original bytes, so ledger stays `matching`; runtime is not run. [Function record](docs/function-records/0x002b96f0.md) |
| `0x002C1830` | Logical query dispatcher used by TitleConfig_Calc | 114 direct cases, three controls and 43 scenarios cover all six original Calc call PCs and seven ID/mode combinations; 264/504-byte body and six ARM calls. Slot-only IPS, independent review accepted and full ARMv6K build passed 204/204; runtime not run. [Function record](docs/function-records/0x002c1830.md) |
| `0x0029EDFC` | Cursor range update called by TitleConfig_Calc | 14 direct cases, three controls and four actual touch-path compositions cover handled indices 0–2 and selected-row skip. 44/80-byte body with one ARM tail relocation; slot-only IPS, independent review and build passed 204/204. Runtime not run. [Function record](docs/function-records/0x0029edfc.md) |
| `0x00297674` | Full-width global state word getter used in TitleConfig_Calc state 2 | Seven direct values, null fault, three controls and 28 original-caller cases; 20-byte body differs in two bytes. Slot-only IPS, independent review and full ARMv6K build passed 204/204. Runtime not run. [Function record](docs/function-records/0x00297674.md) |
| `0x002BDAC0` | Table-selected position setup used by TitleConfig_Calc | 72 direct cases, three null-table cases, an alias/order case, three negative controls, and both actual TitleConfig_Calc call slices; 80/108-byte body and slot-only cumulative IPS. Independent review accepted and full ARMv6K build passed 204/204; runtime not run. [Function record](docs/function-records/0x002bdac0.md) |
| `0x0029F260`, `0x0029F248` | Guarded ASD slot getters for fields `+0x24` and `+0x20` | 76 direct cases per getter, four actual `TitleConfig_Calc` caller-slice cases, two mutation controls, and a cumulative three-slot H2 IPS overlay. Each body is 20/24 bytes and differs from the original; independent review confirmed relocation targets, ledger status and slot scope. Runtime is not run. [0x0029F260](docs/function-records/0x0029f260.md), [0x0029F248](docs/function-records/0x0029f248.md) |

The recent helper batch compiled all 204 translation units. Runtime and integration limits remain explicit in the per-function reviews and the [H2 milestone record](docs/milestones/H2-audio-settings.md).

---

## Reference byte coverage

- **Current ledger exact matches:** `3,126,860 / 3,139,108 bytes` (**99.6099%**) across `10,922` matching functions and `8` matching raw spans, according to the current `config/functions.csv` classifications.
- **Current non-matching reconstructions:** `12,248 bytes` across `37` functions; semantic evidence is recorded per function. `0x002B0188` and `0x002B96F0` have typed C++, but their relocated final bodies are byte-identical and remain `matching`. `0x00297674`, `0x0029EDFC`, `0x0029F248`, `0x0029F260`, `0x002A63F8`, `0x002B787C`, `0x002AE6B0`, `0x002AE664`, `0x002BF41C`, `0x002B88C4`, `0x002BDAC0` and `0x002C1830` have typed C++ with bounded offline evidence; caller and runtime scope is documented per function.
- **Readable byte-identical C++ reconstructions:** `60` functions from the historical exact-conversion count. Non-identical semantic reconstructions, including `0x002B787C`, are counted separately in the ledger.
- **Total Codebase Explored:** `3,139,108 / 3,139,108 bytes` (**100.0000%**) across `10,959` functions and `8` raw spans; this measures mapped inventory, not byte matching or behavioral equivalence.
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
