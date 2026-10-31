# H7 Autonomous Script VM and Event Runtime Verification Record

- **Date:** 2026-10-30
- **Scope:** Milestone H7 (Script VM and Event Execution / Máquina virtual de scripts y eventos)
- **Harness:** Loopback GDB stub (`127.0.0.1:54342` original, `127.0.0.1:54343` patched) via `tools/h3_autonomous_verify.py`
- **Profiles:** `build/h7-runtime/isolated/original` vs `build/h7-runtime/isolated/patched`
- **Save fixture:** Shinjuku Station — Underground, slot 0 (`sdds4game1.sav`, SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`)

## 1. Pinned Binary Images and Patch Artifacts

| Component | Path / Identifier | SHA-256 |
|---|---|---|
| Pinned Retail Binary | `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Pinned H6 Final Composite | `build/agent-work/H6-semantic/h6-integrated-stage/code.h6-final.bin` | `1677aac91a81740ab03dde2010e0df0dea4ce3b9b7265a7339bdf2ef22333587` |
| H7 Staged Composite | `build/agent-work/H7-semantic/h7-integrated-stage/code.h7-final.bin` | `477ae5941b1163f56533b74128635e6deb22ddf796d4f4c18d65bdb02ddda3f8` |
| H7 Mod IPS Patch | `build/agent-work/H7-semantic/h7-integrated-stage/code.h7-final.ips` | `08eee6b3b42e166baf0e99afea7083a780a63f564bc2204706c8e09ad83206de` |
| Target Save File | `sdmc/.../title/00040000/000e5c00/data/00000001/sdds4game1.sav` | `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` |

## 2. Integrated Candidates in Final Image

| Function / VMA | Size (Cand/Win) | Role | Source File |
|---|---|---|---|
| `0x0010A748` | 384 / 504 B | Common dialogue window initialization and task registration | `experiments/semantic_equivalence/h7_ui_comwin_init_candidate.cpp` |
| `0x0010AEE4` | 84 / 84 B | Dialogue window reset and active sprite clearing | `experiments/semantic_equivalence/h7_ui_comwin_reset_candidate.cpp` |
| `0x0010AF84` | 388 / 560 B | Notification and info window workspace setup and sprite anim | `experiments/semantic_equivalence/h7_ui_infowin_init_candidate.cpp` |
| `0x0010B350` | 340 / 448 B | Guest dialogue window workspace setup and panel registration | `experiments/semantic_equivalence/h7_ui_guestwin_init_candidate.cpp` |
| `0x001D374C` | 324 / 408 B | FlowScript naming prompt event setup and script environment init | `experiments/semantic_equivalence/h7_script_namemain_init_candidate.cpp` |
| `0x001D38FC` | 288 / 392 B | Barracks event script loader (`ones_room/onesRoom.bf`, `onesRoom.mbm`) | `experiments/semantic_equivalence/h7_script_onesroom_init_candidate.cpp` |
| `0x0025955C` | 340 / 516 B | Event command message under-fade step and draw task runner | `experiments/semantic_equivalence/h7_script_eventcmd_fade_candidate.cpp` |
| `0x0030A4FC` | 248 / 504 B | Event visual effect screen blink and color transition setup | `experiments/semantic_equivalence/h7_script_eventeffect_init_candidate.cpp` |

## 3. Autonomous Runtime Comparison Metrics

The test script executed autonomous paired emulation in private loopback Azahar processes:
- `original`: port 54342 (unmodified game code)
- `patched`: port 54343 (with `code.h7-final.ips` layeredfs mod)
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

Milestone H7 script VM and event runtime verification is fully complete. The integrated experimental replacement reproduces authentic dialogue window workspace setup, window reset, info window animations, guest window layout, FlowScript naming initialization, barracks event loading, message under-fade transitions, and event visual blink/flash effects with zero functional regressions across Title, Save Load, and 250 Field Scene checkpoints.
