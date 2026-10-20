#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * UI Memory Arena Allocator & Texture Cache Manager.
 * Original Atlus source path: `c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp`
 */
struct UiMemoryArena {
    void* base_address;             // +0x00: Beginning of arena heap
    u32 total_capacity;             // +0x04: Size of arena pool
    u32 current_offset;             // +0x08: Current allocation watermark
    u32 allocation_count;           // +0x0C: Active blocks allocated
};

/**
 * Allocates aligned memory blocks from dedicated UI / HUD resource pools.
 *
 * Address: 0x00345194, Size: 7,068 bytes
 */
void* Ui_MemoryArenaAllocate(UiMemoryArena* arena, u32 byte_size, u32 alignment);

} // namespace smt4::ui
