# H4 Map Entity Pool Candidate (0x001B45E0) — Semantic Reconstruction & Offline Differential Report

**Task ID:** `h4-map-entity-pool-candidate`  
**Address:** `0x001B45E0` (`Map_ClearEntityPool`)  
**Original Binary Size:** 132 bytes (32 instructions + 1 literal word)  
**Candidate Size:** 100 bytes (24 instructions + 1 literal word)  
**Candidate Source:** [`experiments/semantic_equivalence/h4_map_entity_pool_candidate.cpp`](../../experiments/semantic_equivalence/h4_map_entity_pool_candidate.cpp)  
**Test Runner:** [`tools/h4_map_entity_pool_experiment.py`](../../tools/h4_map_entity_pool_experiment.py)  
**Date:** 2026-10-30  
**Overall Status:** `passed`  

---

## 1. Candidate Reconstruction Overview

Function `0x001B45E0` resets the 24-entry field entity/event pool located via `g_MapEntities` at `0x00447E70`. For each entity (stride 72 bytes), it checks resource pointer `+0x3C`, releases non-null resources via `Resource_Release` (`0x002A7AA0`), zeroes the resource pointer, and resets state byte `+0x14`.

The candidate C++ implementation:
```cpp
#include <cstddef>

using u8 = unsigned char;
using u32 = unsigned int;

struct MapEntity {
    u8 pad_00[0x14];        // +0x00..+0x13
    u8 state_14;            // +0x14
    u8 pad_15[0x3C - 0x15]; // +0x15..+0x3B
    void* resource;         // +0x3C
    u8 pad_40[0x48 - 0x40]; // +0x40..+0x47
};

static_assert(sizeof(MapEntity) == 72, "stride 72");
static_assert(offsetof(MapEntity, state_14) == 0x14, "offset 0x14");
static_assert(offsetof(MapEntity, resource) == 0x3C, "offset 0x3C");

extern "C" void Resource_Release_002a7aa0(void* res);

extern "C" void h4_map_entity_pool_candidate() {
    auto** pool_slot = reinterpret_cast<MapEntity**>(0x00447E70);
    MapEntity* entities = *pool_slot;

    for (u32 i = 0; i < 24; ++i) {
        if (entities[i].resource != nullptr) {
            Resource_Release_002a7aa0(entities[i].resource);
            entities[i].resource = nullptr;
        }
    }

    #pragma clang loop unroll(disable)
    for (u32 i = 0; i < 24; ++i) {
        entities[i].state_14 = 0;
    }
}
```

---

## 2. Compilation and Binary Footprint

- **Target Architecture:** ARMv6K (3DS Horizon, softfp VFPv2).
- **Toolchain:** Clang 19 with `-O2 -marm -mcpu=arm1176jzf-s -mfpu=vfpv2`.
- **Candidate Size:** 100 bytes (strictly within original 132-byte limit).
- **Candidate SHA-256:** `d6a2dbf72ca9e6361ecdc497a702462155d4c89585dc7079f0e8a4a9acb6278a`.

---

## 3. Offline ARM Differential Verification

An offline differential simulation using Unicorn ARM11MPCore was executed across five deterministic and pseudorandom test fixtures comparing original ARM `0x001B45E0` against compiled `h4_map_entity_pool_candidate`:

| Fixture ID | Description | Result | Released Count | Differences |
|---|---|---|---|---|
| `all_resources_active` | All 24 entities have active resources | `pass` | 24 | 0 |
| `alternating_resources` | Even entities have active resources, odd null | `pass` | 12 | 0 |
| `no_resources` | All 24 entities have null resource pointers | `pass` | 0 | 0 |
| `random_sparse` | Randomized null/non-null resources and states | `pass` | 12 | 0 |
| `only_last_entry` | Only entity index 23 has active resource | `pass` | 1 | 0 |

### Invariant Checks Verified:
1. **Conditional Resource Release:**
   - Callee `Resource_Release` is invoked only for non-null resource pointers with exact resource address in `r0`.
   - Post-execution memory confirms `entity->resource == nullptr` across all 24 entities.
2. **State Reset:**
   - Byte `state_14` reset to 0 across all 24 entities.
3. **Preserved Registers & Stack:**
   - Registers `r4..r11` preserved identically.
   - Stack pointer `SP` balanced with delta 0.
4. **Memory Hash:**
   - Entire 1,728-byte entity pool buffer verified with matching SHA-256 between original and candidate.

---

## 4. Negative Control (Mutation Detection)

A compiled negative control `h4_map_entity_pool_mutation` clearing only 12 entries was evaluated against the reference original. The harness detected the divergence immediately in both release counts and post-execution memory SHA-256 (`mutation_detected: true`).

---

## 5. Artifact Hashes

- Candidate Source: `experiments/semantic_equivalence/h4_map_entity_pool_candidate.cpp`
- Test Runner: `tools/h4_map_entity_pool_experiment.py`
- Test Output: `build/agent-work/H4-semantic/h4-map-entity-pool-candidate/001/output/differential_report.json`
