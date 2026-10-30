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

// Deliberately mutated negative control (only clears 12 entities instead of 24)
extern "C" void h4_map_entity_pool_mutation() {
    auto** pool_slot = reinterpret_cast<MapEntity**>(0x00447E70);
    MapEntity* entities = *pool_slot;

    #pragma clang loop unroll(disable)
    for (u32 i = 0; i < 12; ++i) {
        if (entities[i].resource != nullptr) {
            Resource_Release_002a7aa0(entities[i].resource);
            entities[i].resource = nullptr;
        }
    }

    #pragma clang loop unroll(disable)
    for (u32 i = 0; i < 12; ++i) {
        entities[i].state_14 = 0;
    }
}
