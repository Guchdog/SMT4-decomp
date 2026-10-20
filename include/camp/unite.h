#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

namespace smt4::camp {

/**
 * Bottom-Screen Dynamic Button Help HUD Manager Workspace (0x564 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\camp\ButtonHelp\ButtonHelp.cpp`
 * Global manager: `g_ButtonHelpManager` at `0x0043DA28`.
 */
struct ButtonHelpWork {
    u8 raw[0x564];
};

static_assert(sizeof(ButtonHelpWork) == 0x564);

struct ButtonHelpManager {
    s8 ref_count;                       // +0x00
    u8 pad_01[3];                       // +0x01..+0x04
    ButtonHelpWork* work;               // +0x04
};

extern ButtonHelpManager g_ButtonHelpManager; // 0x0043DA28

void ButtonHelp_Init();                                                             // 0x0028d974

/**
 * Demon / Skill / Item Sort Menu Modal Manager Workspace (0x878 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\camp\SortMenu\SortMenu.cpp`
 * Global manager: `g_SortMenuManager` at `0x0043DD20`.
 */
struct SortMenuWork {
    u8 raw[0x878];
};

static_assert(sizeof(SortMenuWork) == 0x878);

struct SortMenuManager {
    s8 ref_count;                       // +0x00
    u8 pad_01[3];                       // +0x01..+0x04
    SortMenuWork* work;                 // +0x04
};

extern SortMenuManager g_SortMenuManager; // 0x0043DD20

void SortMenu_Init(s32 mode);                                                       // 0x0029e63c

/**
 * Mido Demon Fusion (Cathedral of Shadows) Engine Workspace (0x1BC8 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\camp\Unite\Unite.cpp`
 */
struct UniteWork {
    void* calc_task;                    // +0x000: Task handle
    u32 state;                          // +0x004
    u8 raw[0x1BC8 - 0x008];             // +0x008..+0x1BC8
};

static_assert(sizeof(UniteWork) == 0x1BC8);

// Unite API
void Unite_Init(void* r0, void* r1, s32 r2, void* r3);                             // 0x0029b3cc
void Unite_Setup(void* arg);                                                        // 0x001f2f58
void UniteEffect_Init(void* arg);                                                   // 0x002e315c
void Unite_DrawAndCalc(void* arg);                                                  // 0x001de238

} // namespace smt4::camp
