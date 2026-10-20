#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

namespace smt4::ui {

/**
 * Save / Load UI Workspace (0x388 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\saveLoadUI\saveLoadUI.cpp`
 * Global manager: `g_SaveLoadUIManager` at `0x0044DE28`.
 */
struct SaveLoadUIWork {
    void* calc_task;                    // +0x000: "BOOT Calc" task handle
    u8 pad_04[4];                       // +0x04
    u32 state;                          // +0x08: Menu state (0: slot select, 1: confirm, 2: save, 3: load)
    u32 sub_state;                      // +0x0C
    u32 selected_slot;                  // +0x010: Selected slot index (0..N)
    u8 raw[0x388 - 0x014];              // +0x014..+0x388: Sprite tables, touch buttons, and file headers
};

static_assert(offsetof(SaveLoadUIWork, calc_task) == 0x00);
static_assert(offsetof(SaveLoadUIWork, state) == 0x08);
static_assert(offsetof(SaveLoadUIWork, selected_slot) == 0x10);
static_assert(sizeof(SaveLoadUIWork) == 0x388);

struct SaveLoadUIManager {
    u8 flags;                           // +0x00
    u8 pad_01[3];                       // +0x01..+0x04
    SaveLoadUIWork* work;               // +0x04
};

extern SaveLoadUIManager g_SaveLoadUIManager; // 0x0044DE28

// saveLoadUI API
void saveLoadUI_Init();                                                             // 0x00191eac
void saveLoadUI_DrawMain(void* arg);                                                // 0x001c897c
void saveLoadUI_Calc(void* arg);                                                    // 0x00202950

/**
 * Save / Load Thread Process Workspace (0x18 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\gamedata\SaveLoadProcess.cpp`
 */
struct SaveLoadProcess {
    void* thread_handle;                // +0x00
    u32 operation;                      // +0x04: 0: None, 1: Save, 2: Load
    u32 status;                         // +0x08: 0: Busy, 1: Done, -1: Error
    u32 slot_index;                     // +0x0C: Target file slot
    u32 file_size;                      // +0x10: Target payload size
    u32 bytes_transferred;              // +0x14: Progress counter
};

static_assert(sizeof(SaveLoadProcess) == 0x18);

// SaveLoadProcess API
void SaveLoadProcess_Init(void* arg);                                               // 0x0026b874
void SaveLoadProcess_Step(void* arg);                                               // 0x002ef9ac
void SaveLoadProcess_Write(void* arg);                                              // 0x002efb50
void SaveLoadProcess_Read(void* arg);                                               // 0x00322d70
void SaveLoadProcess_Close(void* arg);                                              // 0x00322f0c

} // namespace smt4::ui
