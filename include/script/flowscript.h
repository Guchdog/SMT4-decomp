#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::script {

/**
 * Character & Demon Name Entry Modal Workspace (0x960 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\name\nameMain.cpp`
 * Global manager: `g_NameMainManager` at `0x0044D180`.
 */
struct NameMainWork {
    void* proc_task;                    // +0x00: Task handle ("NameMainProc", tag 2)
    u8 pad_04[0x0C];                    // +0x04..+0x10
    u8 text_input_buf[0x100];           // +0x10..+0x110
    u8 raw[0x960 - 0x110];              // +0x110..+0x960
};

static_assert(sizeof(NameMainWork) == 0x960);

struct NameMainManager {
    void* unk_00;                       // +0x00
    NameMainWork* work;                 // +0x04
};

extern NameMainManager g_NameMainManager; // 0x0044D180

void nameMain_Init(void* arg0, s32 arg1);                                           // 0x001d374c

/**
 * Barracks ("One's Room") Subsystem Workspace (0x14 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\ones_room\onesRoom.cpp`
 * Global manager: `g_OnesRoomManager` at `0x0044D1C8`.
 */
struct OnesRoomWork {
    void* calc_task;                    // +0x00: Task handle ("onesRoom C", tag 2)
    void* bf_data;                      // +0x04: Loaded onesRoom.bf
    void* script_proc;                  // +0x08: Script process handle
    void* mbm_data;                     // +0x0C: Loaded onesRoom.mbm
    u8 flag_10;                         // +0x10
    u8 flag_11;                         // +0x11
    u8 pad_12[2];                       // +0x12..+0x14
};

static_assert(sizeof(OnesRoomWork) == 0x14);

struct OnesRoomManager {
    OnesRoomWork* work;                 // +0x00
};

extern OnesRoomManager g_OnesRoomManager; // 0x0044D1C8

void onesRoom_Init(void* arg0, s32 arg1);                                           // 0x001d38fc

// Core FlowScript Virtual Machine Opcode Dispatcher
s32 FlowScript_ExecuteOpcode(void* script_ctx);                                     // 0x001d3d40

} // namespace smt4::script
