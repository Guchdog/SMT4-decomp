# H2 conversion: `0x0027FBC8` axis reader

## Result

The original 320-byte assembly body is now a typed C++ implementation in `src/engine/leaf_batch41_a.cpp`. Its production object body is exactly the 300-byte body from the independent experimental candidate; five ARM NOP instructions fill the remaining slot. Both retained `R_ARM_CALL` instructions target the even ARM entry `0x0019FE4C`.

The function ledger now labels the differing body `non_matching`. This is a semantic reconstruction claim with bounded offline evidence, not a byte-match claim. The downstream `0x00254CA8` uninitialized-output read remains unresolved when this helper returns zero without writes; no H2 or consumer-domain completion is inferred.

## Reproduction

Original image identity: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

Commands and results:

```powershell
python tools/h4_axis_reader_experiment.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-0027fbc8-reader-cpp/run002/checks/direct --audit-contract --seed 20261103
python tools/h4_axis_camera_composition.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-0027fbc8-reader-cpp/run002/checks/camera-caller
python tools/build_check.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-0027fbc8-reader-cpp/run005/checks/affected-tu --jobs 1 --tu src/engine/leaf_batch41_a.cpp
python tools/h2_27fbc8_production_validation.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-0027fbc8-reader-cpp/run005/checks/staged --seed 20261107
```

All commands exited 0. The direct candidate audit compared 146 cases: zero differences and a detected same-input mode-bound mutation. The two invalid output-pointer probes produced the same unmapped-write fault class and matching ordered writes; these remain fault observations, outside the supported pointer domain. The caller composition executed the actual `0x001FA948` camera call slice through `0x001FAA84`: 6/6 cases matched and its mutation was detected. It uses a synthetic view/stack fixture, not the full camera task.

The final-VMA validator recompiled both candidate and production objects, confirmed their function bodies match byte for byte (300 bytes), resolved both helper calls to `0x0019FE4C`, checked the original caller BL targets the even ARM entry, padded and patched the 320-byte slot, and replayed the slot-only IPS exactly. It then compared original and staged function executions at `0x0027FBC8` over 146 cases: zero differences; the two invalid-pointer cases had matching fault classes and writes. All changes remained within the target slot.

| Evidence | Value |
| --- | --- |
| Direct differential report SHA-256 | `cb8a79f46fc387ba6d8e51a91f316c18fd98cf485b2e0bf64f4bc35f1baf439f` |
| Camera caller report SHA-256 | `982d1c5a9179e134f6f981c84c2a830c7c54a8bff5264ae89586fc6b66b3a8dd` |
| Final-VMA report SHA-256 | `6704e6f905e1fa2d6e7735329ab34d4d8043a74bf225ada6c3ea0840a18cd7b8` |
| Production object SHA-256 | `14c698618f315cde451a1b29347c6cf0972d80226b56454748d44be84f11d579` |
| Production/staged body SHA-256 | `5a8160055c296e73c46e94fe8a5aaf439e38c8e91a66e5855c9f8c04922dda6a` |
| Staged image SHA-256 | `64175ee8940de6faa132185ba2684af241fe9fa6bfe9c6857287b764c999515c` |
| Slot IPS SHA-256 | `486c8191f83ba2212a66874689c66e43b4b0191fa118cbc6d7006b75c4ade1e8` |

The detailed files and reports are under `build/agent-work/H2-semantic/h2-titleconfig-0027fbc8-reader-cpp/`. Static interworking evidence covers the even ARM entry, original caller BL, two final-VMA ARM BL calls, and their even helper target. The complete stack scratch bytes, SP, condition flags and all caller-saved GPRs are not part of the direct runner's equality contract. Runtime comparison was not run.

Independent review recomputed all 17 frozen input hashes and reran fresh 146-case direct and final-VMA checks with seeds `20261102` and `20261106`. Both runs passed with no differences or counterexamples. The reviewer approved the `non_matching` classification and bounded behavior; the downstream no-write read remains unresolved. See [independent review](h2-0027fbc8-independent-review.md).
