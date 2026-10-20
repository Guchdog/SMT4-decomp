#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Development Debug Profiler HUD & Performance Monitor.
 * Formats and overlays:
 * - CPU / GPU frame time (ms)
 * - VRAM allocation heaps
 * - Active task counts and PICA200 draw calls
 * String patterns: `%-7s:%-d`, `%-7s:%-X`, `%-7s:%-4.1f`, `%-7s:`
 */
struct DebugStatsWork {
    f32 cpu_frame_time_ms;          // +0x00: CPU frame time
    f32 gpu_frame_time_ms;          // +0x04: PICA200 GPU frame time
    u32 allocated_vram_bytes;       // +0x08: VRAM usage in bytes
    u32 allocated_heap_bytes;       // +0x0C: Main RAM heap usage
    u32 active_draw_calls;          // +0x10: Geometry draw call count
    u32 display_flags;              // +0x14: Profiler overlay toggle flags
};

/**
 * Formats and renders performance statistics, memory bars, and frame timers.
 *
 * Address: 0x001b1a90, Size: 8,352 bytes
 */
void Ui_DebugStatsRender(DebugStatsWork* work, void* display_ctx);

} // namespace smt4::ui
