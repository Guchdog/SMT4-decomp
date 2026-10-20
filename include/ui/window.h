#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

namespace smt4::ui {

/**
 * 0x20-byte sprite-layout descriptor zeroed by 0x002C3344
 * (`UiSpriteGroup_Init`) and filled by 0x002C32F8
 * (`UiSpriteGroup_BindTable`).  It is embedded by the ComWin/InfoWin/GuestWin/
 * PlaceWin/RunWin/SearchWin workspaces below.
 */
struct UiSpriteGroup {
    u8 raw[0x20];
};
static_assert(sizeof(UiSpriteGroup) == 0x20);

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

/**
 * Information & Alert Dialog Window workspace (0x1BC bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\font\InfoWin\InfoWin.cpp`
 * Global pointer: `g_InfoWinWork` at `0x0043E128`.
 */
struct InfoWinWork {
    void* calc_task;                    // +0x00: "InfoWin Calc" task handle (0x0011b1bc)
    void* draw_up_left;                 // +0x04: "InfoWin DrawUpLeft" task handle (0x0011ae10, prio 0x81)
    void* draw_up_right;                // +0x08: "InfoWin DrawUpRight" task handle (0x0011ae10, prio 0xDF)
    u32 state;                          // +0x0C: Active state
    u32 timer;                          // +0x10: Frame display timer (default 30)
    u32 flags;                          // +0x14
    u32 unk_18;                         // +0x18
    u32 unk_1c;                         // +0x1C
    u32 unk_20;                         // +0x20
    UiSpriteGroup sprite_group;         // +0x24: Sprite table group (0x20 bytes)
    UiAnimSprite panel_sprites[2];      // +0x44, +0xD0: Anim sprites (2 * 0x8C bytes)
    u8 unk_15c[0x1B8 - 0x15C];          // +0x15C..+0x1B8
    void* text_handle;                  // +0x1B8: Text renderer handle
};

static_assert(offsetof(InfoWinWork, calc_task) == 0x00);
static_assert(offsetof(InfoWinWork, draw_up_left) == 0x04);
static_assert(offsetof(InfoWinWork, draw_up_right) == 0x08);
static_assert(offsetof(InfoWinWork, sprite_group) == 0x24);
static_assert(offsetof(InfoWinWork, panel_sprites) == 0x44);
static_assert(offsetof(InfoWinWork, text_handle) == 0x1B8);
static_assert(sizeof(InfoWinWork) == 0x1BC);

extern InfoWinWork* g_InfoWinWork;      // 0x0043E128

// InfoWin API functions
bool InfoWin_IsActive();                                                            // 0x0010af38
void InfoWin_SetState(u32 state);                                                   // 0x0010af48
void InfoWin_Init();                                                                // 0x0010af84
void InfoWin_ShowMessage(const char* msg);                                          // 0x0010b1b4
void InfoWin_UpdateTimer();                                                         // 0x0010b260
void InfoWin_Dismiss();                                                             // 0x0010b320
void InfoWin_DrawUp(void* arg);                                                     // 0x0011ae10
void InfoWin_Calc(void* arg);                                                       // 0x0011b128

/**
 * Guest Demonica Partner Prompt Window workspace (0xBC bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\font\GuestWin\GuestWin.cpp`
 * Global pointer: `g_GuestWinWork` at `0x0043E110`.
 */
struct GuestWinWork {
    void* calc_task;                    // +0x00: "GuestWin Calc" task handle (0x0011b128)
    void* draw_up_left;                 // +0x04: "GuestWin DrawUpLeft" task handle (0x0011a9b4, prio 0x81)
    void* draw_up_right;                // +0x08: "GuestWin DrawUpRight" task handle (0x0011a9b4, prio 0xDF)
    u32 state;                          // +0x0C: Active state
    UiSpriteGroup sprite_group;         // +0x10: Sprite table group (0x20 bytes)
    UiAnimSprite panel_sprite;          // +0x30: Anim sprite (0x8C bytes)
};

static_assert(offsetof(GuestWinWork, calc_task) == 0x00);
static_assert(offsetof(GuestWinWork, draw_up_left) == 0x04);
static_assert(offsetof(GuestWinWork, draw_up_right) == 0x08);
static_assert(offsetof(GuestWinWork, sprite_group) == 0x10);
static_assert(offsetof(GuestWinWork, panel_sprite) == 0x30);
static_assert(sizeof(GuestWinWork) == 0xBC);

extern GuestWinWork* g_GuestWinWork;    // 0x0043E110

// GuestWin API functions
bool GuestWin_IsActive();                                                           // 0x0010b340
void GuestWin_Init();                                                               // 0x0010b350
void GuestWin_HandlePrompt();                                                       // 0x0010b510
void GuestWin_DrawUp(void* arg);                                                    // 0x0011a9b4

/**
 * Location / Area Banner Dialog Window workspace (0x140 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\font\PlaceWin\PlaceWin.cpp`
 * Global pointer: `g_PlaceWinWork` at `0x0043E140`.
 */
struct PlaceWinWork {
    void* calc_task;                    // +0x00: "PlaceWin Calc" task handle
    void* draw_up_left;                 // +0x04: "PlaceWin DrawUpLeft" task handle (prio 0x81)
    u32 state;                          // +0x08: State (0: inactive, 1: showing, 2: hold, 3: dismiss)
    void* draw_up_right;                // +0x0C: "PlaceWin DrawUpRight" task handle (prio 0xDF)
    u32 flags;                          // +0x10: Display flags
    UiSpriteGroup sprite_group;         // +0x14: Sprite table group (0x20 bytes)
    UiAnimSprite panel_sprite;          // +0x34: Anim sprite (0x8C bytes)
    char message[128];                  // +0xC0: Area name string buffer (0x80 bytes)
};

static_assert(offsetof(PlaceWinWork, calc_task) == 0x00);
static_assert(offsetof(PlaceWinWork, draw_up_left) == 0x04);
static_assert(offsetof(PlaceWinWork, state) == 0x08);
static_assert(offsetof(PlaceWinWork, sprite_group) == 0x14);
static_assert(offsetof(PlaceWinWork, panel_sprite) == 0x34);
static_assert(offsetof(PlaceWinWork, message) == 0xC0);
static_assert(sizeof(PlaceWinWork) == 0x140);

extern PlaceWinWork* g_PlaceWinWork;    // 0x0043E140

// PlaceWin API functions
void PlaceWin_SetPos(f32 x, f32 y, f32 z, f32 w);                                   // 0x0026385c
void PlaceWin_SetScale(s32 idx, s32 layer, f32 sx, f32 sy, f32 sz, f32 sw);         // 0x0026389c
void PlaceWin_Dismiss();                                                             // 0x002638dc
void PlaceWin_SetVisible(u8 visible);                                               // 0x002638fc
bool PlaceWin_CheckState();                                                         // 0x00263910
bool PlaceWin_IsActive();                                                           // 0x0026394c
void PlaceWin_ShowMessage(const char* msg);                                         // 0x00263978
void PlaceWin_Init();                                                               // 0x002639f4
void PlaceWin_Calc(void* arg);                                                      // 0x00263bb4

/**
 * Running / Escape Prompt Window workspace (0xE4 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\font\SearchWin\RunWin.cpp`
 * Global pointer: `g_RunWinWork` at `0x0043E158`.
 */
struct RunWinWork {
    void* calc_task;                    // +0x00: "RunWin Calc" task handle
    void* draw_down;                    // +0x04: "RunWin DrawDown" task handle (prio 0xE9)
    u32 state;                          // +0x08: State (0: inactive, 1: enter, 2: run, 3: exit)
    u32 timer;                          // +0x0C: Timer
    u32 unk_10;                         // +0x10
    u8 visible;                         // +0x14: Display visibility
    u8 pad_15[3];                       // +0x15
    UiSpriteGroup sprite_group;         // +0x18: Sprite table group (0x20 bytes)
    UiAnimSprite panel_sprite;          // +0x38: Anim sprite (0x8C bytes)
    u8 unk_c4[0xE4 - 0xC4];             // +0xC4..+0xE4
};

static_assert(offsetof(RunWinWork, calc_task) == 0x00);
static_assert(offsetof(RunWinWork, draw_down) == 0x04);
static_assert(offsetof(RunWinWork, state) == 0x08);
static_assert(offsetof(RunWinWork, visible) == 0x14);
static_assert(offsetof(RunWinWork, sprite_group) == 0x18);
static_assert(offsetof(RunWinWork, panel_sprite) == 0x38);
static_assert(sizeof(RunWinWork) == 0xE4);

extern RunWinWork* g_RunWinWork;        // 0x0043E158

// RunWin API functions
void RunWin_Init();                                                                 // 0x002027dc
void RunWin_DrawDownAndCalc(void* arg);                                             // 0x0018f178

/**
 * Demonica Radar & Relic Search Window workspace (0xE4 bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\font\SearchWin\SearchWin.cpp`
 * Global pointer: `g_SearchWinWork` at `0x0043E170`.
 */
struct SearchWinWork {
    void* calc_task;                    // +0x00: "SearchWin Calc" task handle
    void* draw_up_left;                 // +0x04: "SearchWin DrawUpLeft" task handle (prio 0x81)
    u32 state;                          // +0x08: State (0: inactive, 1: scanning, 2: lock, 3: dismiss)
    void* draw_up_right;                // +0x0C: "SearchWin DrawUpRight" task handle (prio 0xDF)
    u32 timer;                          // +0x10: Display frame timer
    u8 visible;                         // +0x14: Display visibility
    u8 pad_15[3];                       // +0x15
    UiSpriteGroup sprite_group;         // +0x18: Sprite table group (0x20 bytes)
    UiAnimSprite panel_sprite;          // +0x38: Anim sprite (0x8C bytes)
    u8 unk_c4[0xE4 - 0xC4];             // +0xC4..+0xE4
};

static_assert(offsetof(SearchWinWork, calc_task) == 0x00);
static_assert(offsetof(SearchWinWork, draw_up_left) == 0x04);
static_assert(offsetof(SearchWinWork, state) == 0x08);
static_assert(offsetof(SearchWinWork, draw_up_right) == 0x0C);
static_assert(offsetof(SearchWinWork, visible) == 0x14);
static_assert(offsetof(SearchWinWork, sprite_group) == 0x18);
static_assert(offsetof(SearchWinWork, panel_sprite) == 0x38);
static_assert(sizeof(SearchWinWork) == 0xE4);

extern SearchWinWork* g_SearchWinWork;  // 0x0043E170

// SearchWin API functions
bool SearchWin_IsActive();                                                          // 0x002cecd8
void SearchWin_Dismiss();                                                           // 0x002ced0c
void SearchWin_Init();                                                              // 0x002ced28
void SearchWin_DrawUpAndCalc(void* arg);                                            // 0x001accd4

} // namespace smt4::ui
