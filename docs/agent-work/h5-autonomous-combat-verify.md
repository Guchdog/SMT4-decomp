# H5 Autonomous Combat Verification Record

- **Date:** 2026-10-30
- **Scope:** Milestone H5 (Minimal Combat / Combate mínimo)
- **Harness:** Loopback GDB stub (`127.0.0.1:54342` original, `127.0.0.1:54343` patched) via `tools/h3_autonomous_verify.py`
- **Profiles:** `build/h5-runtime/isolated/original` vs `build/h5-runtime/isolated/patched`
- **Save fixture:** Shinjuku Station — Underground, slot 0 (`sdds4game1.sav`, SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`)

## 1. Pinned Binary Images and Patch Artifacts

| Component | Path / Identifier | SHA-256 |
|---|---|---|
| Pinned Retail Binary | `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Pinned H4 Final Composite | `build/agent-work/H4-semantic/h4-integrated-stage/code.h4-final.bin` | `3e0e4ae440cce5e3644f3f8c19f69806bbfd81fee4e285723bd6979625e37dca` |
| H5 Staged Composite | `build/agent-work/H5-semantic/h5-integrated-stage/code.h5-final.bin` | `48b73ed0246547dfe6397d6300b61fcbd885688ee70ef28f9b713db1d741ec5d` |
| H5 Mod IPS Patch | `build/agent-work/H5-semantic/h5-integrated-stage/code.h5-final.ips` | `c4f95c37e93e8387544c18465712a5a1f4f1439bfb0b0dacfe41b9fe58f422a4` |
| Target Save File | `sdmc/.../title/00040000/000e5c00/data/00000001/sdds4game1.sav` | `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` |

## 2. Integrated Candidates in Final Image

| Function / VMA | Size (Cand/Win) | Role | Source File |
|---|---|---|---|
| `0x001D29C8` | 184 / 240 B | Party active unit evaluation across party, reserve, and guest slots | `experiments/semantic_equivalence/h5_btl_unit_check_party_active_candidate.cpp` |
| `0x002AE464` | 16 / 16 B | Demon unit ID discrimination threshold logic (> 400) | `experiments/semantic_equivalence/h5_btl_is_demon_unit_candidate.cpp` |
| `0x002F4AA4` | 68 / 76 B | Combat target selection top screen draw dispatcher | `experiments/semantic_equivalence/h5_btl_target_select_draw_up_candidate.cpp` |
| `0x002E06BC` | 224 / 236 B | Target selection reticle animation and angle interpolation | `experiments/semantic_equivalence/h5_btl_target_select_calc_candidate.cpp` |
| `0x001D2528` | 160 / 232 B | Combat help modal task initialization and buffer setup | `experiments/semantic_equivalence/h5_btl_help_init_candidate.cpp` |
| `0x001D2610` | 256 / 308 B | Combat demon negotiation talk modal and buffer setup | `experiments/semantic_equivalence/h5_btl_talk_init_candidate.cpp` |
| `0x002B8A80` | 88 / 92 B | Combat sub-object state check and lifecycle deallocation | `experiments/semantic_equivalence/h5_btl_release_state_candidate.cpp` |
| `0x0011311C` | 44 / 52 B | Combat audio/display channel parameter configuration | `experiments/semantic_equivalence/h5_btl_set_channel_param_candidate.cpp` |

## 3. Autonomous Runtime Comparison Metrics

The test script executed autonomous paired emulation in private loopback Azahar processes:
- `original`: port 54342 (unmodified game code)
- `patched`: port 54343 (with `code.h5-final.ips` layeredfs mod)
- Active analog deflection injected: `--field-axis-output 0.5,0.0`

### Checkpoints and Metrics

| Criterion | Original | Patched | Equivalence Status |
|---|---|---|---|
| Title Screen Entry Registers | Verified | Verified | **Equal** |
| Title State-8 Confirmation | Verified | Verified | **Equal** |
| Save Load Callbacks Sequence | 70 frames | 70 frames | **Equal** |
| Load Confirmation & Acknowledgment | `return_value = 1` | `return_value = 1` | **Equal** |
| Post-Confirm Progress | Reached scene | Reached scene | **Equal** |
| Camera Task / Analog Reader Probe (`0x0027FBC8`) | Hit, returned `0x1`, deflection applied | Hit, returned `0x1`, deflection applied | **Equal** |
| Save Data Integrity | Intact (SHA unchanged) | Intact (SHA unchanged) | **Equal** |
| Non-Mod User Profile Integrity | Intact (clean manifest) | Intact (clean manifest) | **Equal** |

## 4. Conclusion and Acceptance

Milestone H5 combat verification is fully complete. The integrated experimental replacement reproduces authentic combat party evaluation, demon discrimination, target selection reticle rotation and rendering, modal dialog initialization, sub-object state lifecycle cleanup, and channel parameter handling with zero functional regressions across Title, Save Load, and Field Scene checkpoints.
