#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_symbols.h"

namespace smt4::ui {

/**
 * Animated UI sprite node used inside StatusDownWork (`0x8C` bytes per slot).
 */
struct UiAnimSprite {
    u8 raw[0x8C];
};
static_assert(sizeof(UiAnimSprite) == 0x8C);

/**
 * 2D UI list/grid cursor controller (`0x64` bytes).
 * Contains two 1D axis controllers (Row axis at `+0x00`, Column axis at `+0x28`),
 * total item count at `+0x50`, and disabled flag at `+0x62`.
 */
struct UiListCursor {
    u8 raw[0x64];
};
static_assert(sizeof(UiListCursor) == 0x64);

/**
 * 4-byte entry in the StatusDown skill/item sub-tables.
 */
struct StatusDownListEntry {
    u16 id;
    u16 value;
};
static_assert(sizeof(StatusDownListEntry) == 4);

/**
 * Party prompt configuration passed to `StatusDown_SetPartyPrompt` (`0x00215990`).
 */
struct StatusDownPartyPrompt {
    u32 field0;
    u32 field1;
    u32 field2;
    u16 field3;
};

/**
 * Bottom-screen Status HUD workspace (`0x2394` bytes).
 * Original Atlus source path: `c:\SMT4\XRD686\sdds4\program\status\StatusDown.cpp`
 * Global pointer: `g_StatusDownWork` at `0x0044E190`.
 */
struct StatusDownWork {
    void* calc_task;                        // +0x0000: "TMD CALC" task handle (callback 0x001ca648, prio 2)
    void* draw_task;                        // +0x0004: "TMD DDRAW" task handle (callback 0x001cc914, prio 0xE7)
    u8 sprite_group[0x20];                  // +0x0008: Sprite group manager (init via 0x002c3344 & 0x002c32f8)
    UiAnimSprite panel_sprites[7];          // +0x0028..+0x03FC: 7 bottom-screen HUD panel sprites (7 * 0x8C = 0x3D4)
    u8 active_mode;                         // +0x03FC: Active display mode (0..5)
    u8 prev_active_mode;                    // +0x03FD: Previous active display mode
    u8 pad_03fe[2];                         // +0x03FE..+0x0400
    u32 state;                              // +0x0400: Primary state machine state (0..26)
    u32 prev_state;                         // +0x0404: Previous state machine state
    u32 sub_state;                          // +0x0408: Secondary state / sub-step
    u32 state_timer;                        // +0x040C: Frame timer within current state
    u8 needs_refresh;                       // +0x0410: Dirty flag triggering panel refresh
    u8 flag_411;                            // +0x0411: Toggled via StatusDown_SetFlag411 (0x002efe8c)
    u8 flag_412;                            // +0x0412: Toggled via StatusDown_SetFlag412 (0x0029c6c4)
    u8 flag_413;                            // +0x0413: Category select mode flag (set in 0x00311494)
    s32 touch_hold_state;                   // +0x0414: Touch hold state
    u32 touch_drag_state[3];                // +0x0418..+0x0424: Touch drag state words
    u32 lr_state_left;                      // +0x0424: Left shoulder prompt highlight state
    u32 lr_state_right;                     // +0x0428: Right shoulder prompt highlight state
    s16 slot_touch_handles[36];             // +0x042C..+0x0474: Per-slot touch region handles (init to -1)
    s16 btn_touch_handle;                   // +0x0474: Action button touch region handle
    s16 scroll_up_touch_handle;             // +0x0476: Scroll-up arrow touch region handle
    s16 scroll_down_touch_handle;           // +0x0478: Scroll-down arrow touch region handle
    s16 l_btn_touch_handle;                 // +0x047A: L-shoulder touch region handle (0x50F)
    s16 r_btn_touch_handle;                 // +0x047C: R-shoulder touch region handle (0x50E)
    s16 active_sound_id;                    // +0x047E: Active help message / sound ID (init to -1)
    s8 registered_touch_count;              // +0x0480: Number of currently registered touch regions
    s8 status_mode;                         // +0x0481: Current status mode (queried by 0x00293e30)
    u16 party_ids[8];                       // +0x0482..+0x0492: Active party demon/stock IDs
    u8 unk_0492[0x10];                      // +0x0492..+0x04A2: Secondary party slot buffer
    u16 sub_ids_a[8];                       // +0x04A2..+0x04B2: Queued demon/status IDs list A
    u16 sub_ids_b[8];                       // +0x04B2..+0x04C2: Queued demon/status IDs list B
    u8 new_party_flags[16];                 // +0x04C2..+0x04D2: Per-slot diff flags when party changes
    u8 pad_04d2[2];                         // +0x04D2..+0x04D4
    UiListCursor list_cursor_main;          // +0x04D4..+0x0538: Main party slot cursor controller
    u8 has_sub_ids_a;                       // +0x0538: Non-zero when sub_ids_a contains entries
    u8 pad_0539[3];                         // +0x0539..+0x053C
    u32 field_53c;                          // +0x053C: Queried by StatusDown_GetField53C (0x002956ac)
    u32 callback_arg1;                      // +0x0540: Argument stored when entering state 11
    s32 selected_result;                    // +0x0544: Selected slot result index (init to -1)
    u8 flag_548;                            // +0x0548: Party slot diff mode flag
    u8 pad_0549[3];                         // +0x0549..+0x054C
    s32 highlighted_slot_index;             // +0x054C: Highlighted slot index (checked in 0x0029a520)
    u32 unk_0550;                           // +0x0550
    u32 prompt_field0;                      // +0x0554: Party prompt parameter 0
    u32 prompt_field1;                      // +0x0558: Party prompt parameter 1
    u32 prompt_field2;                      // +0x055C: Party prompt parameter 2
    u16 prompt_field3;                      // +0x0560: Party prompt parameter 3
    u8 pad_0562[2];                         // +0x0562..+0x0564
    UiListCursor list_cursor_prompt;        // +0x0564..+0x05C8: Prompt cursor controller
    StatusDownListEntry skill_entries[512]; // +0x05C8..+0x0DC8: Filtered skill list (0x800 bytes)
    s16 skill_count;                        // +0x0DC8: Number of populated entries in skill_entries
    s16 skill_total;                        // +0x0DCA: Total skills scanned in bitfield
    UiListCursor skill_cursor;              // +0x0DCC..+0x0E30: Skill list cursor controller
    StatusDownListEntry item_entries[1280]; // +0x0E30..+0x2230: Filtered inventory item list (0x1400 bytes)
    s16 item_count;                         // +0x2230: Number of populated entries in item_entries
    s16 item_nonzero_count;                 // +0x2232: Number of non-zero quantity items
    s16 item_saved_col;                     // +0x2234: Saved column index for item grid cursor
    s16 item_saved_row;                     // +0x2236: Saved row index for item grid cursor
    u8 unk_2238[4];                         // +0x2238..+0x223C
    UiListCursor item_cursor;               // +0x223C..+0x22A0: Item grid cursor controller (9x4 grid)
    void* text_handle;                      // +0x22A0: AsdText handle (created in Init, freed in Destroy)
    u32 unk_22a4;                           // +0x22A4
    UiListCursor list_cursor_help;          // +0x22A8..+0x230C: Bottom help bar cursor/message controller
    UiListCursor category_cursor;           // +0x230C..+0x2370: Category selection cursor controller
    u16 category_ids[8];                    // +0x2370..+0x2380: Available category IDs (0x79F..0x802)
    u16 category_arg0;                      // +0x2380: Category selection argument 0
    u16 unk_2382;                           // +0x2382
    u32 field_2384;                         // +0x2384: Queried by StatusDown_GetField2384 (0x0028cd5c)
    s8 field_2388;                          // +0x2388: Queried by StatusDown_GetField2388 (0x002efe2c)
    u8 unk_2389[8];                         // +0x2389..+0x2391
    u8 request_close_flag;                  // +0x2391: Set to 1 by StatusDown_RequestClose (0x00317f80)
    u8 visibility_flag;                     // +0x2392: Toggled by StatusDown_SetVisibility (0x0026d8c0)
    u8 pad_2393;                            // +0x2393
};

static_assert(offsetof(StatusDownWork, panel_sprites) == 0x0028);
static_assert(offsetof(StatusDownWork, active_mode) == 0x03FC);
static_assert(offsetof(StatusDownWork, state) == 0x0400);
static_assert(offsetof(StatusDownWork, touch_hold_state) == 0x0414);
static_assert(offsetof(StatusDownWork, lr_state_left) == 0x0424);
static_assert(offsetof(StatusDownWork, slot_touch_handles) == 0x042C);
static_assert(offsetof(StatusDownWork, btn_touch_handle) == 0x0474);
static_assert(offsetof(StatusDownWork, scroll_up_touch_handle) == 0x0476);
static_assert(offsetof(StatusDownWork, scroll_down_touch_handle) == 0x0478);
static_assert(offsetof(StatusDownWork, l_btn_touch_handle) == 0x047A);
static_assert(offsetof(StatusDownWork, r_btn_touch_handle) == 0x047C);
static_assert(offsetof(StatusDownWork, active_sound_id) == 0x047E);
static_assert(offsetof(StatusDownWork, registered_touch_count) == 0x0480);
static_assert(offsetof(StatusDownWork, status_mode) == 0x0481);
static_assert(offsetof(StatusDownWork, party_ids) == 0x0482);
static_assert(offsetof(StatusDownWork, sub_ids_a) == 0x04A2);
static_assert(offsetof(StatusDownWork, sub_ids_b) == 0x04B2);
static_assert(offsetof(StatusDownWork, new_party_flags) == 0x04C2);
static_assert(offsetof(StatusDownWork, list_cursor_main) == 0x04D4);
static_assert(offsetof(StatusDownWork, has_sub_ids_a) == 0x0538);
static_assert(offsetof(StatusDownWork, field_53c) == 0x053C);
static_assert(offsetof(StatusDownWork, selected_result) == 0x0544);
static_assert(offsetof(StatusDownWork, highlighted_slot_index) == 0x054C);
static_assert(offsetof(StatusDownWork, prompt_field0) == 0x0554);
static_assert(offsetof(StatusDownWork, list_cursor_prompt) == 0x0564);
static_assert(offsetof(StatusDownWork, skill_entries) == 0x05C8);
static_assert(offsetof(StatusDownWork, skill_count) == 0x0DC8);
static_assert(offsetof(StatusDownWork, skill_total) == 0x0DCA);
static_assert(offsetof(StatusDownWork, skill_cursor) == 0x0DCC);
static_assert(offsetof(StatusDownWork, item_entries) == 0x0E30);
static_assert(offsetof(StatusDownWork, item_count) == 0x2230);
static_assert(offsetof(StatusDownWork, item_nonzero_count) == 0x2232);
static_assert(offsetof(StatusDownWork, item_saved_col) == 0x2234);
static_assert(offsetof(StatusDownWork, item_saved_row) == 0x2236);
static_assert(offsetof(StatusDownWork, item_cursor) == 0x223C);
static_assert(offsetof(StatusDownWork, text_handle) == 0x22A0);
static_assert(offsetof(StatusDownWork, list_cursor_help) == 0x22A8);
static_assert(offsetof(StatusDownWork, category_cursor) == 0x230C);
static_assert(offsetof(StatusDownWork, category_ids) == 0x2370);
static_assert(offsetof(StatusDownWork, category_arg0) == 0x2380);
static_assert(offsetof(StatusDownWork, field_2384) == 0x2384);
static_assert(offsetof(StatusDownWork, field_2388) == 0x2388);
static_assert(offsetof(StatusDownWork, request_close_flag) == 0x2391);
static_assert(offsetof(StatusDownWork, visibility_flag) == 0x2392);
static_assert(sizeof(StatusDownWork) == 0x2394);

extern StatusDownWork* g_StatusDownWork; // 0x0044E190

// Lifecycle & mode control
void StatusDown_Init();                                                             // 0x002d931c
void StatusDown_Destroy();                                                          // 0x002f6550
void StatusDown_OpenDefaultView();                                                  // 0x001ddab4
void StatusDown_Close();                                                            // 0x0029bfec
void StatusDown_SetDisplayMode(s32 mode);                                           // 0x00292f44
void StatusDown_SetVisibility(u8 visible);                                          // 0x0026d8c0
void StatusDown_RequestClose();                                                     // 0x00317f80

// Party slots, sub-ID queues, skill/item lists & touch region setup
void StatusDown_SetPartyPrompt(const StatusDownPartyPrompt* prompt);                // 0x00215990
void StatusDown_SetActiveSoundId(s16 sound_id);                                     // 0x00215a44
void StatusDown_SetPartySlots(const u16* ids, s32 count);                           // 0x00215a68
void StatusDown_UpdatePartySlotsAndDiff(const u16* ids, s32 count);                 // 0x002e2f44
void StatusDown_SetSubIdsA(const u16* ids, s32 count);                              // 0x0026abe0
void StatusDown_PopFirstSubIdA();                                                   // 0x0026b01c
void StatusDown_SetSubIdsB(const u16* ids, s32 count);                              // 0x002efe48
void StatusDown_PopulateSkillList(const u8* skill_bitfield);                        // 0x001ee5a4
void StatusDown_PopulateItemList(const u8* item_counts);                            // 0x001ee7c8
void StatusDown_SortItemList();                                                     // 0x0032c4bc
void StatusDown_OpenCategorySelect(u16 arg0, u8 flag_413);                          // 0x00311494
void StatusDown_SetupTouchRegions();                                                // 0x0026b0d0

// Skill & Item Sort Comparators
s32  StatusDown_SkillSortByIdAsc(const void* a, const void* b);                     // 0x00206be8
s32  StatusDown_SkillSortByIdDesc(const void* a, const void* b);                    // 0x002e4534
s32  StatusDown_SkillSortByCostAsc(const void* a, const void* b);                   // 0x001f60dc
s32  StatusDown_SkillSortByCostDesc(const void* a, const void* b);                  // 0x002dc96c
s32  StatusDown_SkillSortByNameAsc(const void* a, const void* b);                   // 0x001f6174
s32  StatusDown_ItemSortByIdAsc(const void* a, const void* b);                      // 0x00206cbc
s32  StatusDown_ItemSortByIdDesc(const void* a, const void* b);                     // 0x002e4608
s32  StatusDown_ItemSortByTypeAsc(const void* a, const void* b);                    // 0x00206c38
s32  StatusDown_ItemSortByTypeDesc(const void* a, const void* b);                   // 0x002e4584

// UI drawing & help bar
void StatusDown_CalcTaskCallback(void* arg);                                        // 0x001ca648
void StatusDown_DrawTaskCallback(void* arg);                                        // 0x001cc914
void StatusDown_DrawPartyAndSubViews(s32 x_offset, s32 y_offset);                   // 0x00187014
void StatusDown_DrawLRPrompts(s32 x_offset, s32 y_offset);                          // 0x0029adf0
void StatusDown_DrawPartySlotRow(s32 x_offset, s32 y_offset, s32 demon_id,
                                 u32 node_id, f32 scale, s32 is_stock_row,
                                 s32 is_empty_mode, s32 highlight_mode);            // 0x0029a520
void StatusDown_DrawSkillList(s32 x_offset, s32 y_offset);                          // 0x0032be34
void StatusDown_UpdateHelpMessage(s32 msg_index);                                   // 0x002cf4e0

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
