#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::engine {

/**
 * 3D Field Exploration Environment & Dynamic Field Actor Workspace.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\map\mapField.cpp`
 * References: `map/sky/sky_%02d.bam`, `test/kemuri.tmx`
 */
struct MapFieldWork {
    f32 camera_pos[3];              // +0x00: Active field camera coordinate
    f32 camera_rot[3];              // +0x0C: Camera pitch / yaw / roll
    f32 player_anchor[3];           // +0x18: Player model world root
    u32 current_area_id;            // +0x24: Active zone index (e.g. Naraku, Tokyo, Mikado)
    u32 skybox_model_id;            // +0x28: Active skybox index (sky_%02d.bam)
    u32 smoke_emitter_count;        // +0x2C: Active particle / smoke emitters (kemuri.tmx)
    u8 raw[0x200 - 0x030];          // +0x030..+0x200: Collision volumes & light probes
};

/**
 * PICA200 GPU Texture Streaming & Mipmap Workspace.
 */
struct TextureStreamerWork {
    void* vram_staging_buffer;      // +0x00: VRAM allocation pointer
    u32 total_textures_loaded;      // +0x04: Active streamed texture count
    u32 stream_flags;               // +0x08: Async decompression state
    u32 mipmap_levels;              // +0x0C: Mipmap generation level
};

/**
 * Processes 3D field environment updates, skybox animations, particle smoke
 * emitters, and collision checking for dungeon exploration.
 *
 * Address: 0x00208ce8, Size: 16,796 bytes
 */
void Map_Field3DManager(MapFieldWork* work, void* scene_ctx);

/**
 * Streams compressed texture assets and mipmaps into 3DS PICA200 GPU VRAM.
 *
 * Address: 0x00386184, Size: 5,948 bytes
 */
void Engine_TextureStreamer(TextureStreamerWork* streamer, void* tex_data, u32 size);

/** Texture descriptor comparator callback used by Engine_TextureStreamer.
 * Address: 0x003878c0, Size: 16 bytes
 */
s32 Engine_TextureStreamer_Compare(const void* lhs, const void* rhs);

} // namespace smt4::engine
