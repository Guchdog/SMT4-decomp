# H6 Autonomous Save and Reload Verification Record

- **Date:** 2026-10-30
- **Scope:** Milestone H6 (Save and Reload / Guardado y recarga)
- **Harness:** Loopback GDB stub (`127.0.0.1:54342` original, `127.0.0.1:54343` patched) via `tools/h3_autonomous_verify.py`
- **Profiles:** `build/h6-runtime/isolated/original` vs `build/h6-runtime/isolated/patched`
- **Save fixture:** Shinjuku Station — Underground, slot 0 (`sdds4game1.sav`, SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`)

## 1. Pinned Binary Images and Patch Artifacts

| Component | Path / Identifier | SHA-256 |
|---|---|---|
| Pinned Retail Binary | `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Pinned H5 Final Composite | `build/agent-work/H5-semantic/h5-integrated-stage/code.h5-final.bin` | `48b73ed0246547dfe6397d6300b61fcbd885688ee70ef28f9b713db1d741ec5d` |
| H6 Staged Composite | `build/agent-work/H6-semantic/h6-integrated-stage/code.h6-final.bin` | `1677aac91a81740ab03dde2010e0df0dea4ce3b9b7265a7339bdf2ef22333587` |
| H6 Mod IPS Patch | `build/agent-work/H6-semantic/h6-integrated-stage/code.h6-final.ips` | `7965539180716f160d5af86ca06e73e17036611c8639926babfd84a9600406f5` |
| Target Save File | `sdmc/.../title/00040000/000e5c00/data/00000001/sdds4game1.sav` | `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` |

## 2. Integrated Candidates in Final Image

| Function / VMA | Size (Cand/Win) | Role | Source File |
|---|---|---|---|
| `0x0021041C` | 172 / 204 B | ASD save file stream reading, validation, and payload copy | `experiments/semantic_equivalence/h6_asd_save_common_read_candidate.cpp` |
| `0x002104E8` | 180 / 200 B | ASD save file serialization and stream writing | `experiments/semantic_equivalence/h6_asd_save_common_write_candidate.cpp` |
| `0x0026B874` | 228 / 304 B | SaveLoad process load task spawn and work initialization | `experiments/semantic_equivalence/h6_saveload_process_init_candidate.cpp` |
| `0x002EF9AC` | 344 / 420 B | SaveLoad FSM step transition machine (states 0..5) | `experiments/semantic_equivalence/h6_saveload_process_step_candidate.cpp` |
| `0x002EFB50` | 360 / 456 B | SaveLoad process state serialization and slot write | `experiments/semantic_equivalence/h6_saveload_process_write_candidate.cpp` |
| `0x00322D70` | 284 / 412 B | SaveLoad process block read and slot verification | `experiments/semantic_equivalence/h6_saveload_process_read_candidate.cpp` |
| `0x00322F0C` | 200 / 304 B | SaveLoad save task launcher and parameters setup | `experiments/semantic_equivalence/h6_saveload_process_close_candidate.cpp` |
| `0x00191EAC` | 140 / 208 B | SaveLoad UI manager workspace setup and task registration | `experiments/semantic_equivalence/h6_saveload_ui_init_candidate.cpp` |

## 3. Autonomous Runtime Comparison Metrics

The test script executed autonomous paired emulation in private loopback Azahar processes:
- `original`: port 54342 (unmodified game code)
- `patched`: port 54343 (with `code.h6-final.ips` layeredfs mod)
- Active analog deflection injected: `--field-axis-output 0.5,0.0`
- Callbacks evaluated: 70 Save Load UI callbacks with controlled slot load confirmation.

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

Milestone H6 save and reload verification is fully complete. The integrated experimental replacement reproduces authentic ASD save file streaming, save/load process task lifecycle, state machine transitions, block reading/writing, and UI workspace registration with zero functional regressions across Title, Save Load, and 250 Field Scene checkpoints.
