# H4 Map Player Actor Candidate (0x001B45C8) — Semantic Reconstruction & Offline Differential Report

**Task ID:** `h4-map-player-actor-candidate`  
**Address:** `0x001B45C8` (`Map_GetPlayerActor`)  
**Original Binary Size:** 24 bytes (5 instructions + 1 literal word)  
**Candidate Size:** 24 bytes (5 instructions + 1 literal word)  
**Candidate Source:** [`experiments/semantic_equivalence/h4_map_player_actor_candidate.cpp`](../../experiments/semantic_equivalence/h4_map_player_actor_candidate.cpp)  
**Test Runner:** [`tools/h4_map_player_actor_experiment.py`](../../tools/h4_map_player_actor_experiment.py)  
**Date:** 2026-10-30  
**Overall Status:** `passed`  

---

## 1. Candidate Reconstruction Overview

Function `0x001B45C8` resolves the protagonist player actor pointer. It double-dereferences global `g_MapMainWork` (`0x00447E28`), extracts the 32-bit handle at offset `+0x00`, and tail-calls `ActorManager_Lookup(handle, 0)` at `0x002C45B8`.

The candidate C++ implementation:
```cpp
#include <cstddef>

using u32 = unsigned int;

struct MapMainWork {
    u32 player_actor_handle; // +0x00
};

static_assert(offsetof(MapMainWork, player_actor_handle) == 0x00, "offset 0x00");

extern "C" void* ActorManager_Lookup_002c45b8(u32 handle, u32 mode);

extern "C" void* h4_map_player_actor_candidate() {
    auto** map_slot = reinterpret_cast<MapMainWork**>(0x00447E28);
    MapMainWork* work = *map_slot;
    return ActorManager_Lookup_002c45b8(work->player_actor_handle, 0);
}
```

---

## 2. Compilation and Binary Footprint

- **Target Architecture:** ARMv6K (3DS Horizon, softfp VFPv2).
- **Toolchain:** Clang 19 with `-O2 -marm -mcpu=arm1176jzf-s -mfpu=vfpv2`.
- **Candidate Size:** 24 bytes (strictly equal to original 24 bytes).
- **Candidate SHA-256:** `7c38d5db520054ca39fb1e184d0f21f6587f15dd7c4b5c685fb011ffa8f7dc43`.

---

## 3. Offline ARM Differential Verification

An offline differential simulation using Unicorn ARM11MPCore was executed across six deterministic and pseudorandom handle fixtures comparing original ARM `0x001B45C8` against compiled `h4_map_player_actor_candidate`:

| Fixture ID | Handle Value | Status | Return `r0` Delta | Register Mismatches |
|---|---|---|---|---|
| `handle_zero` | `0x00000000` | `pass` | 0 | None (`r4..r11`) |
| `handle_sample1` | `0x00100001` | `pass` | 0 | None (`r4..r11`) |
| `handle_sample2` | `0x00200045` | `pass` | 0 | None (`r4..r11`) |
| `handle_max` | `0xFFFFFFFF` | `pass` | 0 | None (`r4..r11`) |
| `handle_rand1` | Pseudorandom | `pass` | 0 | None (`r4..r11`) |
| `handle_rand2` | Pseudorandom | `pass` | 0 | None (`r4..r11`) |

### Invariant Checks Verified:
1. **Handle and Mode Arguments:**
   - Callee `ActorManager_Lookup` receives identical `r0` (player actor handle) and `r1 = 0` (lookup mode).
2. **Registers & Stack:**
   - Registers `r4..r11` preserved identically.
   - Stack pointer `SP` balanced with delta 0.
3. **Return Value:**
   - Return pointer in `r0` matched across all cases.

---

## 4. Negative Control (Mutation Detection)

A compiled negative control `h4_map_player_actor_mutation` passing mode `1` instead of `0` to `ActorManager_Lookup` was evaluated against the reference original. The harness detected the divergence in call arguments immediately (`mutation_detected: true`).

---

## 5. Artifact Hashes

- Candidate Source: `experiments/semantic_equivalence/h4_map_player_actor_candidate.cpp`
- Test Runner: `tools/h4_map_player_actor_experiment.py`
- Test Output: `build/agent-work/H4-semantic/h4-map-player-actor-candidate/001/output/differential_report.json`
