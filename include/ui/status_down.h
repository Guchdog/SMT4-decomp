#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::ui {

/**
 * Animated UI sprite node used inside StatusDownWork (`0x8C` bytes per slot).
 * Initialized by `UiAnimSprite_Init` (`0x001cc310`) and bound to CTB/BCAT resources
 * via `UiAnimSprite_BindResource` (`0x002c6c5c`).
 */
struct UiAnimSprite {
    u8 raw[0x8C];
};
static_assert(sizeof(UiAnimSprite) == 0x8C);

/**
 * UI list/scroll cursor sub-structure (`0x64` bytes).
 * Operated on by `UiListCursor_Init` (`0x0029fae8`), `UiListCursor_SetPosition` (`0x0029f0f4`),
 * `UiListCursor_SetTextArgs` (`0x0029f248`), and `UiListCursor_SetSelection` (`0x0029edfc`).
 */
struct UiListCursor {
    u8 raw[0x64];
};
static_assert(sizeof(UiListCursor) == 0x64);

/**
 * Bottom-screen Status HUD workspace (`0x2394` bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\status\StatusDown.cpp`
 * Global pointer: `g_StatusDownWork` at `0x0044E190`.
 */
struct StatusDownWork {
    void* calc_task;                    // +0x0000: "TMD CALC" task handle (callback 0x001ca648, prio 2)
    void* draw_task;                    // +0x0004: "TMD DDRAW" task handle (callback 0x001cc914, prio 0xE7)
    u8 sprite_group[0x20];              // +0x0008: Sprite group manager (init via 0x002c3344 & 0x002c32f8)
    UiAnimSprite panel_sprites[7];      // +0x0028..+0x03FC: 7 bottom-screen HUD panel sprites (7 * 0x8C = 0x3D4)
    u8 active_mode;                     // +0x03FC: Active display mode (0, 1, or 2)
    u8 prev_active_mode;                // +0x03FD: Previous active display mode
    u8 pad_03fe[2];                     // +0x03FE..+0x0400
    u32 state;                          // +0x0400: Primary state machine state (0..20)
    u32 prev_state;                     // +0x0404: Previous state machine state
    u32 sub_state;                      // +0x0408: Secondary state / sub-step
    u32 state_timer;                    // +0x040C: Frame timer within current state
    u8 needs_refresh;                   // +0x0410: Dirty flag triggering panel refresh
    u8 flag_411;                        // +0x0411: Toggled via StatusDown_SetFlag411 (0x002efe8c)
    u8 flag_412;                        // +0x0412: Toggled via StatusDown_SetFlag412 (0x0029c6c4)
    u8 flag_413;                        // +0x0413: Sub-mode flag
    u8 unk_0414[0x10];                  // +0x0414..+0x0424
    u32 lr_state_left;                  // +0x0424: Left shoulder prompt animation state
    u32 lr_state_right;                 // +0x0428: Right shoulder prompt animation state
    s16 slot_table[0x29];               // +0x042C..+0x047E: 41-entry slot mapping table (init to -1)
    s16 active_sound_id;                // +0x047E: Active sound effect ID (init to -1)
    s8 loaded_icon_count;               // +0x0480: Number of loaded party icon textures
    s8 status_mode;                     // +0x0481: Current status mode (queried by 0x00293e30)
    u16 party_ids[8];                   // +0x0482..+0x0492: Active party demon/stock IDs
    u8 unk_0492[0x10];                  // +0x0492..+0x04A2: Secondary party slot buffer
    u16 sub_ids_a[8];                   // +0x04A2..+0x04B2: Queued demon/status IDs list A
    u16 sub_ids_b[8];                   // +0x04B2..+0x04C2: Queued demon/status IDs list B
    u8 new_party_flags[16];             // +0x04C2..+0x04D2: Per-slot diff flags when party changes
    u8 pad_04d2[2];                     // +0x04D2..+0x04D4
    UiListCursor list_cursor_main;      // +0x04D4..+0x0538: Main party slot cursor controller
    u8 has_sub_ids_a;                   // +0x0538: Non-zero when sub_ids_a contains entries
    u8 pad_0539[3];                     // +0x0539..+0x053C
    u32 field_53c;                      // +0x053C: Queried by StatusDown_GetField53C (0x002956ac)
    u32 callback_arg1;                  // +0x0540: Argument stored when entering state 11
    s32 selected_result;                // +0x0544: Selected slot result index (init to -1)
    u8 flag_548;                        // +0x0548: Party slot diff mode flag
    u8 unk_0549[0x0B];                  // +0x0549..+0x0554
    u32 prompt_field0;                  // +0x0554: Party prompt parameter 0
    u32 prompt_field1;                  // +0x0558: Party prompt parameter 1
    u32 prompt_field2;                  // +0x055C: Party prompt parameter 2
    u16 prompt_field3;                  // +0x0560: Party prompt parameter 3
    u8 pad_0562[2];                     // +0x0562..+0x0564
    UiListCursor list_cursor_prompt;    // +0x0564..+0x05C8: Prompt cursor controller
    u8 unk_05c8[0x1CD8];                // +0x05C8..+0x22A0: Demon icon/portrait render buffers & sub-panels
    void* text_handle;                  // +0x22A0: AsdText handle (created in Init, freed in Destroy)
    u32 unk_22a4;                       // +0x22A4
    UiListCursor list_cursor_help;      // +0x22A8..+0x230C: Bottom help bar cursor/message controller
    u8 unk_230c[0x78];                  // +0x230C..+0x2384
    u32 field_2384;                     // +0x2384: Queried by StatusDown_GetField2384 (0x0028cd5c)
    s8 field_2388;                      // +0x2388: Queried by StatusDown_GetField2388 (0x002efe2c)
    u8 unk_2389[8];                     // +0x2389..+0x2391
    u8 request_close_flag;              // +0x2391: Set to 1 by StatusDown_RequestClose (0x00317f80)
    u8 visibility_flag;                 // +0x2392: Toggled by StatusDown_SetVisibility (0x0026d8c0)
    u8 pad_2393;                        // +0x2393
};

static_assert(offsetof(StatusDownWork, panel_sprites) == 0x0028);
static_assert(offsetof(StatusDownWork, active_mode) == 0x03FC);
static_assert(offsetof(StatusDownWork, state) == 0x0400);
static_assert(offsetof(StatusDownWork, lr_state_left) == 0x0424);
static_assert(offsetof(StatusDownWork, slot_table) == 0x042C);
static_assert(offsetof(StatusDownWork, active_sound_id) == 0x047E);
static_assert(offsetof(StatusDownWork, status_mode) == 0x0481);
static_assert(offsetof(StatusDownWork, party_ids) == 0x0482);
static_assert(offsetof(StatusDownWork, sub_ids_a) == 0x04A2);
static_assert(offsetof(StatusDownWork, sub_ids_b) == 0x04B2);
static_assert(offsetof(StatusDownWork, new_party_flags) == 0x04C2);
static_assert(offsetof(StatusDownWork, list_cursor_main) == 0x04D4);
static_assert(offsetof(StatusDownWork, has_sub_ids_a) == 0x0538);
static_assert(offsetof(StatusDownWork, field_53c) == 0x053C);
static_assert(offsetof(StatusDownWork, selected_result) == 0x0544);
static_assert(offsetof(StatusDownWork, prompt_field0) == 0x0554);
static_assert(offsetof(StatusDownWork, list_cursor_prompt) == 0x0564);
static_assert(offsetof(StatusDownWork, text_handle) == 0x22A0);
static_assert(offsetof(StatusDownWork, list_cursor_help) == 0x22A8);
static_assert(offsetof(StatusDownWork, field_2384) == 0x2384);
static_assert(offsetof(StatusDownWork, field_2388) == 0x2388);
static_assert(offsetof(StatusDownWork, request_close_flag) == 0x2391);
static_assert(offsetof(StatusDownWork, visibility_flag) == 0x2392);
static_assert(sizeof(StatusDownWork) == 0x2394);

extern StatusDownWork* g_StatusDownWork; // 0x0044E190

// Lifecycle & mode control
void StatusDown_Init(u8 visibility);                                                // 0x002d931c
void StatusDown_Destroy();                                                          // 0x002f6550
void StatusDown_OpenDefaultView();                                                  // 0x001ddab4
void StatusDown_Close();                                                            // 0x0029bfec
void StatusDown_SetDisplayMode(s32 mode);                                           // 0x00292f44
void StatusDown_SetVisibility(u8 visible);                                          // 0x0026d8c0
void StatusDown_RequestClose();                                                     // 0x00317f80

// Party slots, sub-ID queues & diffing
void StatusDown_SetPartyPrompt(u32 a0, u32 a1, u32 a2, u16 a3);                     // 0x00215990
void StatusDown_SetActiveSoundId(s16 sound_id);                                     // 0x00215a44
void StatusDown_SetPartySlots(const u16* ids, s32 count);                           // 0x00215a68
void StatusDown_UpdatePartySlotsAndDiff(const u16* ids, s32 count, u8 flag);        // 0x002e2f44
void StatusDown_SetSubIdsA(const u16* ids, s32 count);                              // 0x0026abe0
u16  StatusDown_PopFirstSubIdA();                                                   // 0x0026b01c
void StatusDown_SetSubIdsB(const u16* ids, s32 count);                              // 0x002efe48

// UI drawing & help bar
void StatusDown_DrawLRPrompts(StatusDownWork* work, s32 mode);                      // 0x0029adf0
void StatusDown_UpdateHelpMessage(StatusDownWork* work, s32 msg_index);             // 0x002cf4e0

// State transitions
void StatusDown_EnterState3();                                                      // 0x002f66e8
void StatusDown_EnterState3_Alt();                                                  // 0x002d9618
void StatusDown_EnterState4();                                                      // 0x002efea4
void StatusDown_EnterState6();                                                      // 0x0030ab34
void StatusDown_EnterState6_Simple();                                               // 0x0030aa98
void StatusDown_EnterState14(s32 selected_result);                                  // 0x0030ab00
void StatusDown_SelectLastPartySlotAndEnterState11(s32 result_val, u32 arg1);       // 0x002f6620

// State & field queries
bool StatusDown_CanOpenSubScreen();                                                 // 0x00288718
bool StatusDown_IsInactiveOrState0();                                               // 0x0028cd78
bool StatusDown_IsNotTransitioning();                                               // 0x00293d2c
bool StatusDown_IsNotState1();                                                      // 0x0029c70c
bool StatusDown_IsNotState2();                                                      // 0x0029c72c
bool StatusDown_IsNotState4();                                                      // 0x002efe0c
bool StatusDown_IsState7();                                                         // 0x002f6524
bool StatusDown_IsState10();                                                        // 0x0030aae0
bool StatusDown_IsState15();                                                        // 0x0030aac0
bool StatusDown_IsState20();                                                        // 0x00223b88
bool StatusDown_IsCursorAtLastPartySlot();                                          // 0x002f65d4
u8   StatusDown_GetActiveMode();                                                    // 0x00293d50
s8   StatusDown_GetStatusMode();                                                    // 0x00293e30
u32  StatusDown_GetField53C();                                                      // 0x002956ac
u32  StatusDown_GetField2384();                                                     // 0x0028cd5c
s8   StatusDown_GetField2388();                                                     // 0x002efe2c
s32  StatusDown_GetPartyMaxIndex();                                                 // 0x002efde0
s32  StatusDown_GetSelectedPartyIndex();                                            // 0x0032303c
void StatusDown_SetFlag411(u8 val);                                                 // 0x002efe8c
void StatusDown_SetFlag412(u8 val);                                                 // 0x0029c6c4

} // namespace smt4::ui
