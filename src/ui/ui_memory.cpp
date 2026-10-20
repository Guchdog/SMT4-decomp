#include "ui/ui_memory.h"
#include "ui/status_down.h"

namespace smt4::ui {

// DECOMP_FUNC(0x00345194, 7068)
void* Ui_MemoryArenaAllocate(UiMemoryArena* arena, u32 byte_size, u32 alignment) {
    if (arena == nullptr || arena->base_address == nullptr || byte_size == 0) {
        return nullptr;
    }

    // Aligns allocation offset to specified boundary
    u32 align_mask = (alignment > 0) ? (alignment - 1) : 3;
    u32 aligned_offset = (arena->current_offset + align_mask) & ~align_mask;

    if (aligned_offset + byte_size > arena->total_capacity) {
        return nullptr; // Arena out of memory
    }

    u8* ptr = reinterpret_cast<u8*>(arena->base_address) + aligned_offset;
    arena->current_offset = aligned_offset + byte_size;
    arena->allocation_count++;
    return ptr;
}

} // namespace smt4::ui
