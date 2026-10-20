#pragma once
#include <cstddef>
#include "types.h"
#include "script/flowscript.h"

namespace smt4::script {

/**
 * FlowScript Runtime Memory Manager & Heap Coordinator.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\event\eventCommand.cpp`
 */
struct FlowScriptRuntimeMem {
    void* heap_base;                    // +0x00: Base pointer of script execution heap
    u32 heap_size;                      // +0x04: Total allocated heap capacity
    u32 allocated_bytes;                // +0x08: High-water mark of currently used heap
    void* active_call_frame;            // +0x0C: Active script call stack frame
    u32 frame_depth;                    // +0x10: Recursion/call depth counter
    u8 raw[0x200 - 0x014];              // +0x014..+0x200: Event trigger chains, hook callback pointers, and string pool
};

/**
 * FlowScript Global & Local Bitflag Storage Bank.
 * Manages quest completion states, demon unlock flags, alignment points, and story events.
 */
struct FlowScriptFlagBank {
    u32 global_flags[256];              // +0x000..+0x400: 8,192 global story & sidequest flags
    u32 local_flags[64];                // +0x400..+0x500: 2,048 map/event-local flags
    s32 alignment_value;                // +0x500: Flynn Law / Neutral / Chaos alignment score
    u8 raw[0x600 - 0x504];              // +0x504..+0x600: Cached quest status counters
};

/**
 * Allocates and initializes the FlowScript execution memory arena,
 * setting up stack frame limits, global event buffers, and message hooks.
 *
 * Address: 0x00277f9c, Size: 12,192 bytes
 */
void FlowScript_InitRuntimeMemory(FlowScriptRuntimeMem* mem, void* parent_env);

/**
 * Evaluates, sets, and clears quest and scenario bitflags within the FlowScript flag bank.
 *
 * Address: 0x001e5d84, Size: 9,740 bytes
 */
s32 FlowScript_ProcessFlagBank(FlowScriptFlagBank* bank, u32 flag_id, s32 op_mode);

} // namespace smt4::script
