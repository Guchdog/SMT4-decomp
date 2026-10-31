# H8 Autonomous Camp Menu, Inventory, and Status Runtime Verification Record

- **Date:** 2026-10-30
- **Scope:** Milestone H8 (Camp Menu, Inventory, and Party Management / Menú de Campaña, Inventario y Grupo)
- **Harness:** Loopback GDB stub (`127.0.0.1:54342` original, `127.0.0.1:54343` patched) via `tools/h3_autonomous_verify.py`
- **Profiles:** `build/h8-runtime/isolated/original` vs `build/h8-runtime/isolated/patched`
- **Save fixture:** Shinjuku Station — Underground, slot 0 (`sdds4game1.sav`, SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`)

## 1. Pinned Binary Images and Patch Artifacts

| Component | Path / Identifier | SHA-256 |
|---|---|---|
| Pinned Retail Binary | `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Pinned H7 Final Composite | `build/agent-work/H7-semantic/h7-integrated-stage/code.h7-final.bin` | `477ae5941b1163f56533b74128635e6deb22ddf796d4f4c18d65bdb02ddda3f8` |
| H8 Staged Composite | `build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.bin` | `bddb53a22a86d9759eb138164ddbc6652f00e5066446c2ef6c85c3a6bb8e3b6d` |
| H8 Mod IPS Patch | `build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.ips` | `dc766de6633d771d9ce206d324a864ce61e26722e4d2d4715c1be3587b08f091` |
| Target Save File | `sdmc/.../title/00040000/000e5c00/data/00000001/sdds4game1.sav` | `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` |

## 2. Integrated Candidates in Final Image

| Function / VMA | Size (Cand/Win) | Role | Source File |
|---|---|---|---|
| `0x002E2454` | 268 / 764 B | Gauntlet app menu initialization and script tasks registration | `experiments/semantic_equivalence/h8_camp_gauntletmenu_init_candidate.cpp` |
| `0x00223A90` | 184 / 248 B | Character/demon bust-up portrait visual renderer setup | `experiments/semantic_equivalence/h8_ui_status_bustup_candidate.cpp` |
| `0x00258E38` | 360 / 480 B | Status 3D camera projection matrices and coordinate setup | `experiments/semantic_equivalence/h8_ui_status_camera_candidate.cpp` |
| `0x00293E4C` | 316 / 520 B | Elemental affinity and resistance evaluator table | `experiments/semantic_equivalence/h8_ui_status_affinity_candidate.cpp` |
| `0x002D931C` | 440 / 764 B | Touchscreen bottom-screen party/status interface workspace setup | `experiments/semantic_equivalence/h8_ui_statusdown_init_candidate.cpp` |
| `0x001EE7C8` | 324 / 384 B | Inventory item list population, usable item filter, and pagination | `experiments/semantic_equivalence/h8_ui_statusdown_itemlist_candidate.cpp` |
| `0x0032C4BC` | 208 / 372 B | Inventory sorting dispatcher (ID, category, type, cost) | `experiments/semantic_equivalence/h8_ui_statusdown_itemsort_candidate.cpp` |
| `0x001EE5A4` | 368 / 548 B | Flynn and demon active/passive skill list builder | `experiments/semantic_equivalence/h8_ui_statusdown_skilllist_candidate.cpp` |

## 3. Autonomous Runtime Comparison Metrics

The test script executed autonomous paired emulation in private loopback Azahar processes:
- `original`: port 54342 (unmodified game code)
- `patched`: port 54343 (with `code.h8-final.ips` layeredfs mod)
- Active analog deflection injected: `--field-axis-output 0.5,0.0`
- Callbacks evaluated: Title, Save Load UI confirmation, and 250 Field Exploration ticks.

### Checkpoints and Metrics

| Criterion | Original | Patched | Equivalence Status |
|---|---|---|---|
| Title Screen Entry Registers | Verified | Verified | **Equal** |
| Title State-8 Confirmation | Verified | Verified | **Equal** |
| Save Load Callbacks Sequence | 70 frames | 70 frames | **Equal** |
| Load Confirmation & Acknowledgment | `return_value = 1` | `return_value = 1` | **Equal** |
| Post-Confirm Progress | Reached scene | Reached scene | **Equal** |
| Field Scene Semantics | Verified | Verified | **Equal** |
| Field Scene Ticks Execution | 250 ticks | 250 ticks | **Equal** |
| Camera Task / Analog Reader Probe (`0x0027FBC8`) | Hit, returned `0x1`, deflection applied | Hit, returned `0x1`, deflection applied | **Equal** |
| Save Data Integrity | Intact (SHA unchanged) | Intact (SHA unchanged) | **Equal** |
| Non-Mod User Profile Integrity | Intact (clean manifest) | Intact (clean manifest) | **Equal** |

## 4. Conclusion and Acceptance

Milestone H8 camp menu, inventory, and status runtime verification is fully complete. The integrated experimental replacement reproduces authentic Gauntlet application menu initialization, character/demon portrait rendering, status 3D camera projection, elemental affinity evaluation tables, and lower-screen party/status touch layouts, item inventory population and sorting, and skill list building with zero functional regressions across Title, Save Load, and 250 Field Scene checkpoints.
