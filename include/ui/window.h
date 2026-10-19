#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

namespace smt4::ui {

/**
 * Common Message Dialog Window workspace (0x188 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\font\ComWin\ComWin.cpp`
 * Global pointer: `g_ComWinWork` at `0x0043E0F8`.
 */
struct ComWinWork {
    void* calc_task;                    // +0x00: "ComWin Calc" task handle (0x0011b094)
    void* draw_up_left;                 // +0x04: "ComWin DrawUpLeft" task handle (0x0011a354, prio 0x81)
    void* draw_up_right;                // +0x08: "ComWin DrawUpRight" task handle (0x0011a354, prio 0xDF)
    u32 state;                          // +0x0C: Active state
    u32 sub_state;                      // +0x10: Sub state / display mode
    u32 timer;                          // +0x14: Frame timer
    u32 flag_18;                        // +0x18
    UiSpriteGroup sprite_group;         // +0x1C: Sprite table group (0x20 bytes)
    UiAnimSprite panel_sprites[2];      // +0x3C, +0xC8: Anim sprites (2 * 0x8C bytes)
    u8 unk_154[0x188 - 0x154];          // +0x154..+0x188
};

static_assert(offsetof(ComWinWork, calc_task) == 0x00);
static_assert(offsetof(ComWinWork, draw_up_left) == 0x04);
static_assert(offsetof(ComWinWork, draw_up_right) == 0x08);
static_assert(offsetof(ComWinWork, sprite_group) == 0x1C);
static_assert(offsetof(ComWinWork, panel_sprites) == 0x3C);
static_assert(sizeof(ComWinWork) == 0x188);

extern ComWinWork* g_ComWinWork;        // 0x0043E0F8

// ComWin API functions
void ComWin_SetParam1C(u32 val);                                                    // 0x0010a6fc
bool ComWin_SetState();                                                             // 0x0010a70c
void ComWin_Init();                                                                 // 0x0010a748
void ComWin_GetState(u32* out_state);                                               // 0x0010a940
void ComWin_ProcessDialog();                                                        // 0x0010a954
void ComWin_CheckFlag();                                                            // 0x0010ae9c
void ComWin_GetResult();                                                            // 0x0010aec8
void ComWin_Reset();                                                                // 0x0010aed4
void ComWin_DrawUp(void* arg);                                                      // 0x0011a354

} // namespace smt4::ui
