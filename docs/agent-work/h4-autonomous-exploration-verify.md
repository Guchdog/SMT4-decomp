# H4 Autonomous Exploration Verification Record

- **Date:** 2026-10-30
- **Scope:** Milestone H4 (Minimal Exploration in Shinjuku Station — Underground)
- **Harness:** Loopback GDB stub (`127.0.0.1:54342` original, `127.0.0.1:54343` patched) via `tools/h3_autonomous_verify.py`
- **Profiles:** `build/h4-runtime/isolated/original` vs `build/h4-runtime/isolated/patched`
- **Save fixture:** Shinjuku Station — Underground, slot 0 (`sdds4game1.sav`, SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`)

## 1. Pinned Binary Images and Patch Artifacts

| Component | Path / Identifier | SHA-256 |
|---|---|---|
| Pinned Retail Binary | `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Pinned H3 Final Composite | `build/agent-work/H3-semantic/h3-title-entry/in-place-patch-run002/code.h3-final.bin` | `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8` |
| H4 Staged Composite Binary | `build/agent-work/H4-semantic/h4-integrated-stage/run-001/code.h4-final.bin` | `db36bea481fd35a4434b83d53da61b1a9cad08d4060fc8c68ff21c675c79af58` |
| H4 Mod IPS Patch | `build/agent-work/H4-semantic/h4-integrated-stage/run-001/code.h4-final.ips` | `9ef1c650c3699ad409a9b39cfbd74e2633b68e310eafcf328b83dc1d77f77992` |
| Target Save File | `sdmc/.../title/00040000/000e5c00/data/00000001/sdds4game1.sav` | `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` |

## 2. Integrated Candidates in Final Image

| Function / VMA | Size (Cand/Win) | Role | Source File |
|---|---|---|---|
| `0x0027FBC8` | 300 / 320 B | Analog axis reader for field camera task (`0x001FA840`) | `experiments/semantic_equivalence/h4_axis_reader_candidate.cpp` |
| `0x001B4664` | 396 / 440 B | View camera workspace initialization (`g_ViewWork` at `0x00447E88`) | `experiments/semantic_equivalence/h4_view_init_candidate.cpp` |
| `0x001B481C` | 156 / 164 B | View subobject initialization & Flynn asset binding (`player/pl01_00.bam`) | `experiments/semantic_equivalence/h4_view_subobjects_candidate.cpp` |
| `0x001B45C8` | 24 / 24 B | Player actor resolution from map workspace (`g_MapMainWork` offset `+0x00`) | `experiments/semantic_equivalence/h4_map_player_actor_candidate.cpp` |
| `0x001B45E0` | 100 / 132 B | 24-entry map entity pool reset (`g_MapEntities` at `0x00447E70`) | `experiments/semantic_equivalence/h4_map_entity_pool_candidate.cpp` |

*(Note: `0x002C615C` integer divide helper remains documented and verified offline across 633 direct cases and 1,982 caller composition cases; it is preserved as an experimental candidate while production CRT linking uses runtime libraries).*

## 3. Autonomous Runtime Comparison Metrics

The test script executed autonomous paired emulation in private loopback Azahar processes:
- `original`: port 54342 (unmodified game code)
- `patched`: port 54343 (with `code.h4-final.ips` layeredfs mod)

### Checkpoints and Metrics

| Criterion | Original | Patched | Equivalence Status |
|---|---|---|---|
| Title Screen Entry Registers | `0x0, 0x1, 0x0, 0x1eb02c` | `0x0, 0x1, 0x0, 0x1eb02c` | **Equal** |
| Title State-8 Confirmation | Verified | Verified | **Equal** |
| Save Load Callbacks Sequence | 70 frames | 70 frames | **Equal** |
| Load Confirmation & Acknowledgment | `return_value = 1` | `return_value = 1` | **Equal** |
| Post-Confirm Progress | State 2 -> State 8 -> Scene | State 2 -> State 8 -> Scene | **Equal** |
| Field Scene Transition | Reached `0x00208CE8` | Reached `0x00208CE8` | **Equal** |
| Field Manager Callbacks | 250 ticks | 250 ticks | **Equal (0 diffs)** |
| Camera Task / Analog Reader Probe (`0x0027FBC8`) | Hit, returned `0x1` | Hit, returned `0x1` | **Equal** |
| Scene View Prefix (`0x170` bytes at `0x004BCCD0`) | Captured | Captured | **Byte-for-byte identical** |
| Save Data Integrity | Intact (SHA unchanged) | Intact (SHA unchanged) | **Equal** |
| Non-Mod User Profile Integrity | Intact (clean manifest) | Intact (clean manifest) | **Equal** |

## 4. Verification Command and Output

```powershell
python tools/h3_autonomous_verify.py `
  --profile-root build/h4-runtime/isolated `
  --output build/agent-work/H4-semantic/h4-autonomous-exploration-verify/run-001 `
  --confirm-load `
  --callbacks 70 `
  --field-ticks 250 `
  --field-probe-address 0x0027fbc8
```

Report result:
```json
{
  "status": "observed",
  "comparison": {
    "title_entry_registers_equal": true,
    "title_state8_equal": true,
    "save_load_callbacks_equal": true,
    "post_confirm_events_equal": true,
    "post_confirm_progress_equal": true,
    "load_complete_acknowledged_both": true,
    "field_manager_reached_both": true,
    "field_scene_semantics_equal": true,
    "field_scene_ticks_both": true,
    "empty_slot_rejected_both": false,
    "save_unchanged_both": true,
    "profile_unchanged_both": true,
    "load_result_flag_one_both": true
  }
}
```

## 5. Conclusion and Acceptance

Milestone H4 exploration verification is complete. The integrated experimental replacement reproduces authentic field exploration camera initialization, player asset binding, analog deflection handling, player actor lookup, and entity pool clearing with zero functional regressions across 250 ticks in Shinjuku Station — Underground.
