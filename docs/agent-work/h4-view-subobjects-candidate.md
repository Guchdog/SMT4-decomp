# H4 View Subobjects Candidate (0x001B481C) — Semantic Reconstruction & Offline Differential Report

**Task ID:** `h4-view-subobjects-candidate`  
**Address:** `0x001B481C` (`engine_func_001b481c`)  
**Original Binary Size:** 164 bytes (41 instructions)  
**Candidate Size:** 156 bytes (39 instructions)  
**Candidate Source:** [`experiments/semantic_equivalence/h4_view_subobjects_candidate.cpp`](../../experiments/semantic_equivalence/h4_view_subobjects_candidate.cpp)  
**Test Runner:** [`tools/h4_view_subobjects_experiment.py`](../../tools/h4_view_subobjects_experiment.py)  
**Date:** 2026-10-30  
**Overall Status:** `passed`  

---

## 1. Candidate Reconstruction Overview

Function `0x001B481C` configures the view subobject attached to `ViewCameraWork` (`g_ViewWork` at `0x00447E88`). It loads the player model asset `"player/pl01_00.bam"` via `0x00294A64`, checks channel configuration flag `work->field_198`, and executes a 3-iteration setup across channels 0, 1, and 2.

The candidate C++ implementation represents all fields and subobject pointers with strict `static_assert` type-safety:

```cpp
extern "C" void h4_view_subobjects_candidate() {
    auto** view_slot = reinterpret_cast<ViewCameraWork**>(0x00447E88);
    ViewCameraWork* work = *view_slot;

    ui_subobject_load_player_00294a64(work->subobject, sizeof(ViewCameraWork));

    if (work->field_198 != 0) {
        for (u32 i = 0; i < 3; ++i) {
            u32 size_param = 0;
            if (i == 0 || i == 1 || i == 2) {
                size_param = sizeof(ViewCameraWork);
            }
            ui_subobject_set_channel_active_00343e90(
                work->subobject,
                static_cast<u8>(i),
                work->sub_channels[i],
                size_param
            );
        }
    } else {
        for (u32 i = 0; i < 3; ++i) {
            u32 size_param = 0;
            if (i == 0 || i == 1 || i == 2) {
                size_param = sizeof(ViewCameraWork);
            }
            ui_subobject_set_channel_default_002946f4(
                work->subobject,
                static_cast<u8>(i),
                size_param
            );
        }
    }
}
```

---

## 2. Compilation and Binary Footprint

- **Target Architecture:** ARMv6K (3DS Horizon, softfp VFPv2).
- **Toolchain:** Clang 19 with `-O2 -marm -mcpu=arm1176jzf-s -mfpu=vfpv2`.
- **Candidate Size:** 156 bytes (replacement length strictly within original 164-byte budget).
- **Candidate SHA-256:** `6a7fcae5ffa1079800788b5560ba9ec7f7edd8d6a52787f33c71d124e64fe416`.

---

## 3. Offline ARM Differential Verification

An offline differential simulation using Unicorn ARM11MPCore was executed across six deterministic and pseudorandom test fixtures comparing original ARM `0x001B481C` against compiled `h4_view_subobjects_candidate`:

| Fixture ID | Mode / `field_198` | Channel Values | Result | Call Count | Differences |
|---|---|---|---|---|---|
| `field198_zero` | `0` (Default branch) | `[0x1111, 0x2222, 0x3333, 0, 0, 0]` | `pass` | 4 calls | 0 |
| `field198_one` | `1` (Active branch) | `[0xAAAA, 0xBBBB, 0xCCCC, 0, 0, 0]` | `pass` | 4 calls | 0 |
| `field198_0xff` | `0xFF` (Active branch) | `[0x1000, 0x2000, 0x3000, 0, 0, 0]` | `pass` | 4 calls | 0 |
| `field198_rand1` | `0` (Default branch) | Random 32-bit values | `pass` | 4 calls | 0 |
| `field198_rand2` | `42` (Active branch) | Random 32-bit values | `pass` | 4 calls | 0 |
| `field198_rand3` | `128` (Active branch) | Random 32-bit values | `pass` | 4 calls | 0 |

### Invariant Checks Verified:
1. **Callee Sequence & Arguments:**
   - Call 0: `LOAD_PLAYER(work->subobject, 0x1C0)` matched identically.
   - Calls 1..3:
     - Branch 0: `SET_DEFAULT(work->subobject, i, 0x1C0)` for `i = 0, 1, 2`.
     - Branch != 0: `SET_ACTIVE(work->subobject, i, sub_channels[i], 0x1C0)` for `i = 0, 1, 2`.
2. **Registers:** `r4..r11` preserved identically across all fixtures.
3. **Stack Pointer:** `SP` balanced with 0 delta.
4. **Memory:** `ViewCameraWork` memory buffer verified with identical post-execution SHA-256.

---

## 4. Negative Control (Mutation Detection)

A compiled negative control `h4_view_subobjects_mutation` truncating loop iterations from 3 to 2 was tested against the reference original. The harness detected the divergence immediately (`mutation_detected: true`), verifying that the differential test suite possesses high sensitivity.

---

## 5. Artifact Hashes

- Candidate Source: `experiments/semantic_equivalence/h4_view_subobjects_candidate.cpp`
- Test Runner: `tools/h4_view_subobjects_experiment.py`
- Test Output: `build/agent-work/H4-semantic/h4-view-subobjects-candidate/001/output/differential_report.json`
