# H9 Autonomous Cathedral of Shadows: Fusion & Compendium Runtime Verification Record

- **Date:** 2026-10-30
- **Scope:** Milestone H9 (Cathedral of Shadows: Fusion & Compendium / Catedral de las Sombras: Fusión y Compendio)
- **Harness:** Loopback GDB stub (`127.0.0.1:54342` original, `127.0.0.1:54343` patched) via `tools/h3_autonomous_verify.py`
- **Profiles:** `build/h9-runtime/isolated/original` vs `build/h9-runtime/isolated/patched`
- **Save fixture:** Shinjuku Station — Underground, slot 0 (`sdds4game1.sav`, SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`)

## 1. Pinned Binary Images and Patch Artifacts

| Component | Path / Identifier | SHA-256 |
|---|---|---|
| Pinned Retail Binary | `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Pinned H8 Final Composite | `build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.bin` | `bddb53a22a86d9759eb138164ddbc6652f00e5066446c2ef6c85c3a6bb8e3b6d` |
| H9 Staged Composite | `build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.bin` | `0043ccce8b7bf4a53bbe5312414b27d8c0184345cf674a7e11c1759d0af667ac` |
| H9 Mod IPS Patch | `build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.ips` | `975fcde2a8cbdd4b332126974af00ce2d7588517ed30bc2130c160f8968fdd20` |
| Target Save File | `sdmc/.../title/00040000/000e5c00/data/00000001/sdds4game1.sav` | `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` |

## 2. Integrated Candidates in Final Image

| Function / VMA | Size (Cand/Win) | Role | Source File |
|---|---|---|---|
| `0x002E315C` | 244 / 344 B | 3D fusion summoning circle and lighting particle effect setup | `experiments/semantic_equivalence/h9_camp_uniteeffect_init_candidate.cpp` |
| `0x00269CC8` | 228 / 352 B | Demon Compendium Devil Book manager initialization | `experiments/semantic_equivalence/h9_camp_biblemain_init_candidate.cpp` |
| `0x003AB770` | 404 / 592 B | Legion Skill setup, task registration, and UI list initialization | `experiments/semantic_equivalence/h9_camp_biblelegionskill_init_candidate.cpp` |
| `0x003AD300` | 484 / 596 B | Legion stereoscopic upper/lower draw manager, sprites & nodes | `experiments/semantic_equivalence/h9_camp_biblelegiondraw_init_candidate.cpp` |
| `0x0029E63C` | 364 / 644 B | Fusion & compendium sorting modal and comparator dispatcher | `experiments/semantic_equivalence/h9_camp_sortmenu_init_candidate.cpp` |
| `0x003C9EBC` | 504 / 664 B | Demon fusion candidate roster counter, race bucket allocator, and qsort | `experiments/semantic_equivalence/h9_camp_unitectrl_roster_candidate.cpp` |
| `0x003A7AD8` | 504 / 668 B | Compendium demon inspector, 3D model task registration, UI list | `experiments/semantic_equivalence/h9_camp_bibledevil_init_candidate.cpp` |
| `0x0028D974` | 604 / 736 B | Dynamic button prompt HUD and input helper | `experiments/semantic_equivalence/h9_camp_buttonhelp_init_candidate.cpp` |

## 3. Autonomous Runtime Comparison Metrics

The test script executed autonomous paired emulation in private loopback Azahar processes:
- `original`: port 54342 (unmodified game code)
- `patched`: port 54343 (with `code.h9-final.ips` layeredfs mod)
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

Milestone H9 Cathedral of Shadows: Fusion and Compendium runtime verification is fully complete. The integrated experimental replacement reproduces authentic 3D fusion summoning particle effects, Demon Compendium Devil Book initialization, Legion skill configuration and stereoscopic draw managers, fusion candidate roster generation and race-bucket sorting, compendium demon inspection, and dynamic button prompt HUDs with zero functional regressions across Title, Save Load, and 250 Field Scene checkpoints.
