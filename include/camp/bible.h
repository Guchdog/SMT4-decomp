#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::camp {

/**
 * Cathedral of Shadows Demon Compendium (Devil Book) Workspace (0x20 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\bible\bibleMain.cpp`
 * Global manager: `g_BibleMainManager` at `0x0043DA10`.
 */
struct BibleMainWork {
    void* proc_task;                    // +0x00: Task handle ("BibleMainProc", tag 2)
    void* draw_up_task;                 // +0x04: Task handle ("BibleDrawUp", tag 0x6F)
    void* draw_down_task;               // +0x08: Task handle ("BibleDrawDown", tag 0xE6)
    u8 flag_0c;                         // +0x0C
    u8 flag_0d;                         // +0x0D
    u8 pad_0e[2];                       // +0x0E..+0x10
    s32 state;                          // +0x10
    u8 flag_14;                         // +0x14
    u8 raw[0x20 - 0x15];                // +0x15..+0x20
};

static_assert(sizeof(BibleMainWork) == 0x20);

struct BibleMainManager {
    BibleMainWork* work;                // +0x00
};

extern BibleMainManager g_BibleMainManager; // 0x0043DA10

void bibleMain_Init();                                                              // 0x00269cc8

/**
 * Demon Compendium Analysis & Stat Viewer Workspace.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\bible\bibleAnalyze.cpp`
 */
struct BibleAnalyzeWork {
    void* vtable;                       // +0x00
    u8 pad_04[0x90];                    // +0x04..+0x94
    u8 state_flag;                      // +0x94
    u8 pad_95[0x5A4 - 0x95];            // +0x95..+0x5A4
    u8 view_mode;                       // +0x5A4
    u8 raw[0x600 - 0x5A5];              // +0x5A5..+0x600
};

static_assert(sizeof(BibleAnalyzeWork) == 0x600);

void bibleAnalyze_Init(BibleAnalyzeWork* work);                                     // 0x003a9200

} // namespace smt4::camp
