#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

namespace smt4::camp {

/**
 * Demonica Camp Menu Core Workspace (0x25C4 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\camp\Camp.cpp`
 * Global pointer: `g_CampWork` at `0x0043DA90`.
 */
struct CampWork {
    void* calc_task;                    // +0x0000: "Camp Calc" task handle
    void* draw_task;                    // +0x0004
    u32 state;                          // +0x0008: Camp state
    u32 sub_state;                      // +0x000C
    u8 raw[0x25C4 - 0x010];             // +0x0010..+0x25C4: Sub-menu contexts, Demonica views, and app lists
};

static_assert(offsetof(CampWork, calc_task) == 0x0000);
static_assert(offsetof(CampWork, state) == 0x0008);
static_assert(sizeof(CampWork) == 0x25C4);

extern CampWork* g_CampWork;            // 0x0043DA90

// Camp Core API
void Camp_Init();                                                                   // 0x0028a688
void Camp_Calc(void* arg);                                                          // 0x0028ab8c

/**
 * Party Panel & Demon Display Component.
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\camp\PartyPanel\PartyPanel.cpp`
 */
void PartyPanel_DrawAndCalc(void* arg);                                             // 0x0028ba60

/**
 * Gauntlet App Store & App Management Menu Workspace (0x534 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\camp\GauntletAppMenu\GauntletAppMenu.cpp`
 * Global pointer: `g_GauntletAppMenuWork` at `0x0043DC88`.
 */
struct GauntletAppMenuWork {
    void* calc_task;                    // +0x000: Task handle
    u32 state;                          // +0x004
    u8 raw[0x534 - 0x008];              // +0x008..+0x534: App lists, app points (AP), and unlocked perks
};

static_assert(offsetof(GauntletAppMenuWork, calc_task) == 0x000);
static_assert(sizeof(GauntletAppMenuWork) == 0x534);

extern GauntletAppMenuWork* g_GauntletAppMenuWork; // 0x0043DC88

void GauntletAppMenu_Init();                                                        // 0x002e2454

} // namespace smt4::camp
