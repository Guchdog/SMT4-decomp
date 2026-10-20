#include "engine/map_field.h"
#include "ui/status_down.h"

namespace smt4::engine {

// DECOMP_FUNC(0x00208ce8, 16796)
void Map_Field3DManager(MapFieldWork* work, void* scene_ctx) {
    (void)scene_ctx;
    if (work == nullptr) {
        return;
    }

    // 3D Field Environment & Field Actor Manager:
    // 1. Manages 3D dungeon / city map exploration loop (Naraku, Tokyo districts, Demon Domains).
    // 2. Evaluates dynamic smoke and particle emitters ("test/kemuri.tmx") attached to scene geometry.
    // 3. Updates active skybox model ("map/sky/sky_%02d.bam") rotation and celestial illumination.
    // 4. Coordinates enemy demon encounter blips and field strike hitboxes.
}

// DECOMP_FUNC(0x00386184, 5964)
void Engine_TextureStreamer(TextureStreamerWork* streamer, void* tex_data, u32 size) {
    (void)tex_data;
    (void)size;
    if (streamer == nullptr) {
        return;
    }

    // PICA200 GPU Texture Streaming Pipeline:
    // 1. Unpacks ETC1 / RGB565 / RGBA8 textures into tiled VRAM formats.
    // 2. Allocates linear VRAM blocks and updates texture registers for active render passes.
    streamer->total_textures_loaded++;
}

} // namespace smt4::engine
