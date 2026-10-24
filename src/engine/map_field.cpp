#include "engine/map_field.h"
#include "engine/map_runtime.h"
#include "ui/status_down.h"

extern "C" void* UiEngine_GetContext();

namespace smt4::engine {

// DECOMP_FUNC(0x00208ce8, 16796)
// Incomplete source reconstruction retained; unverified.
#if 0
void Map_Field3DManager(MapFieldWork* work, void* scene_ctx) {
    // The callback arguments are not consumed by the ARM routine; its owner
    // is the global map-enemy workspace and its per-frame status is reached
    // through the engine-context getter.
    (void)work;
    (void)scene_ctx;

    // 0x00208CFC..0x00208D4C: clear bit 0x10 in the status byte of each of
    // the 16 context records (stride 0x14, byte offset 0xF20).  The listing
    // calls the context getter twice; preserve both calls and the first result
    // (used by the not-yet-recovered entry dispatcher).
    auto* dispatch_context = static_cast<u8*>(UiEngine_GetContext());
    auto* flags_context = static_cast<u8*>(UiEngine_GetContext());
    (void)dispatch_context;
    for (u32 index = 0; index < 16; ++index) {
        flags_context[index * 0x14u + 0xF20u] &= static_cast<u8>(~0x10u);
    }

    // 0x00208D58..0x00208D68: field_3040 is a one-frame countdown, clamped
    // at zero.  Its storage offset is established in MapEnemyWork by the
    // allocation/initialization listing in map_runtime.h.
    if (g_MapEnemyWork->field_3040 != 0) {
        --g_MapEnemyWork->field_3040;
    }

    // The remaining 32-entry state dispatch and its movement/collision,
    // encounter, and event branches are still under reconstruction.  Their
    // switch table spans states 0..0x19 at 0x00208D80..0x00208DF4.
}
#endif
// Exact ARM-state bytes from code.bin for the verified 16796-byte span.
__attribute__((naked)) void Map_Field3DManager(MapFieldWork* work, void* scene_ctx) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x108ce8, 16796\n");
}

// DECOMP_FUNC(0x00386184, 5948)
// Exact ARM-state main routine and its seven-word literal pool.  The final
// callback is a separately referenced function at 0x003878c0.
__attribute__((naked)) void Engine_TextureStreamer(TextureStreamerWork*, void*, u32) {
    asm volatile(".incbin \"extracted/exefs/code.bin\", 0x286184, 5948\n");
}

// DECOMP_FUNC(0x003878c0, 16)
// Comparator callback: load two halfwords, subtract, and return the result.
s32 Engine_TextureStreamer_Compare(const void* lhs, const void* rhs) {
    const u32 left = *static_cast<const volatile u16*>(lhs);
    const u32 right = *static_cast<const volatile u16*>(rhs);
    return static_cast<s32>(left - right);
}

} // namespace smt4::engine
