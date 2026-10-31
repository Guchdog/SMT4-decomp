# H10 Autonomous Burroughs, Quests, and Apps Runtime Verification Record

- **Date:** 2026-10-30
- **Scope:** Milestone H10 (Burroughs, Quests, and Apps / Burroughs, Misiones y Apps)
- **Harness:** Loopback GDB stub (`127.0.0.1:54342` original, `127.0.0.1:54343` patched) via `tools/h3_autonomous_verify.py`
- **Profiles:** `build/h10-runtime/isolated/original` vs `build/h10-runtime/isolated/patched`
- **Save fixture:** Shinjuku Station — Underground, slot 0 (`sdds4game1.sav`, SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`)

## 1. Pinned Binary Images and Patch Artifacts

| Component | Path / Identifier | SHA-256 |
|---|---|---|
| Pinned Retail Binary | `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Pinned H9 Final Composite | `build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.bin` | `0043ccce8b7bf4a53bbe5312414b27d8c0184345cf674a7e11c1759d0af667ac` |
| H10 Staged Composite | `build/agent-work/H10-semantic/h10-integrated-stage/code.h10-final.bin` | `8233530ba0df84acc66bf6196153403d257e8bbfa1aca1537fafcabc51bdc4e3` |
| H10 Mod IPS Patch | `build/agent-work/H10-semantic/h10-integrated-stage/code.h10-final.ips` | `db659411fb8e4c9c17f7246a8ae3b488cb42191d1648a18fdcdeaca9ad2c0122` |
| Target Save File | `sdmc/.../title/00040000/000e5c00/data/00000001/sdds4game1.sav` | `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` |

## 2. Integrated Candidates in Final Image

| Function / VMA | Size (Cand/Win) | Role | Source File |
|---|---|---|---|
| `0x002A0FAC` | 24 / 24 B | Burroughs and Quest save data pointer resolution | `experiments/semantic_equivalence/h10_camp_burroughs_getsavedata_candidate.cpp` |
| `0x002A0EA8` | 160 / 168 B | Burroughs application selection dispatcher | `experiments/semantic_equivalence/h10_camp_burroughs_appdispatch_candidate.cpp` |
| `0x0026A004` | 36 / 40 B | Quest list selection reset and category flag set | `experiments/semantic_equivalence/h10_camp_quest_resetselection_candidate.cpp` |
| `0x0026A86C` | 128 / 152 B | Quest objective target condition evaluation | `experiments/semantic_equivalence/h10_camp_quest_evaltarget_candidate.cpp` |
| `0x0026A9FC` | 156 / 196 B | Quest availability checking for main and challenge quests | `experiments/semantic_equivalence/h10_camp_quest_getavailability_candidate.cpp` |
| `0x0026AAC0` | 240 / 256 B | Quest static definition unpack into dynamic UI buffers | `experiments/semantic_equivalence/h10_camp_quest_unpackentry_candidate.cpp` |
| `0x003253D8` | 56 / 56 B | Burroughs Demonica App Store purchase flag registration | `experiments/semantic_equivalence/h10_camp_appstore_setflag_candidate.cpp` |
| `0x00325444` | 52 / 52 B | Burroughs Demonica App Store parameter query & formatter | `experiments/semantic_equivalence/h10_camp_appstore_getappparam_candidate.cpp` |

## 3. Autonomous Runtime Comparison Metrics

The test executed paired emulation in private loopback Azahar processes:
- `original`: port 54342 (unmodified game code)
- `patched`: port 54343 (with `code.h10-final.ips` layeredfs mod)
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

Milestone H10 Burroughs, Quests, and Apps runtime verification is fully complete. The integrated experimental replacement reproduces authentic Burroughs save data resolution, application dispatching, quest selection reset, objective condition evaluation, quest eligibility checking, definition unpacking, and Demonica App Store purchase flag registration with zero functional regressions across Title, Save Load, and 250 Field Scene checkpoints.
