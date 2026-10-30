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

// Deliberately mutated negative control (passes wrong mode parameter 1)
extern "C" void* h4_map_player_actor_mutation() {
    auto** map_slot = reinterpret_cast<MapMainWork**>(0x00447E28);
    MapMainWork* work = *map_slot;
    return ActorManager_Lookup_002c45b8(work->player_actor_handle, 1);
}
