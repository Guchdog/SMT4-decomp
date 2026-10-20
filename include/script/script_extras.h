#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_text.h"

/**
 * Script-adjacent workspaces reconstructed in `src/script/script_extras.cpp`.
 *
 * The eight functions come from seven original translation units named by the
 * inline `ADR` strings:
 *
 *   NpcRoom            c:\SMT4\XRD686\sdds4\program\npc_room\NpcRoom.cpp
 *   UIQuest            c:\SMT4\XRD686\sdds4\program\camp\UIQuest\UIQuest.cpp
 *   qcUtility          c:\SMT4\XRD686\sdds4\program\quest_center\qcUtility.cpp
 *   scrScriptProcess   c:\SMT4\XRD686\sdds4\program\script\scrScriptProcess.cpp
 *   qcMain             c:\SMT4\XRD686\sdds4\program\quest_center\qcMain.cpp
 *   eventCommand       c:\SMT4\XRD686\sdds4\program\event\eventCommand.cpp
 *   EventEffect        c:\SMT4\XRD686\sdds4\program\event\2dEvent\EventEffect.cpp
 *   clearSave          c:\SMT4\XRD686\sdds4\program\clear_save\clearSave.cpp
 *
 * Every field carries the store/load that proves its offset.  Allocation sizes
 * are the immediates passed to AsdMem_Alloc / AsdMem_AllocAlign in the listing.
 */

namespace smt4::script {

// ---------------------------------------------------------------------------
// NpcRoom.cpp (0x0026DF40)
// ---------------------------------------------------------------------------

/**
 * One 0x6C-byte row of global TBB sub-table 0x35, table 0.  The only field the
 * listing reads is the room id at +0x00 (`ldrh r2,[r5]`, 0x0026E084).
 */
struct NpcRoomRow {
    u16 room_id;                        // +0x00
    u8  pad_02[0x6A];
};
static_assert(offsetof(NpcRoomRow, room_id) == 0x00);
static_assert(sizeof(NpcRoomRow) == 0x6C);

/**
 * One 0xD4-byte row of global TBB sub-table 0x35, table 1.  Rows are selected
 * by the room id at +0x00 and filtered by the four event-bit ids at
 * +0x0E/+0x10/+0x12/+0x14 (0x0026E100..0x0026E150).  The sprite fields are
 * read in the attachment loop at 0x0026E490..0x0026E4E8 and the payload index
 * by 0x0026E51C..0x0026E528.
 */
struct NpcRoomEntry {
    u16 room_id;                        // +0x00: `ldrh r0,[r5]` (0x0026E0F4)
    u16 sprite_id;                      // +0x02: `ldrh r0,[r0,#2]` (0x0026E4A0)
    u16 variant;                        // +0x04: `ldrh r1,[r0,#4]` (0x0026E490)
    s16 offset_x;                       // +0x06: `ldrsh r1,[r0,#6]` (0x0026E49C)
    s16 offset_y;                       // +0x08: `ldrsh r2,[r0,#8]` (0x0026E494)
    u16 group_type;                     // +0x0A: `ldrh r3,[r0,#0xa]` (0x0026E1F4)
    u8  pad_0c;
    u8  pose;                           // +0x0D: `ldrb r1,[r0,#0xd]` (0x0026E4DC)
    u16 flag_a;                         // +0x0E: `ldrh r0,[r5,#0xe]` (0x0026E100)
    u16 flag_b;                         // +0x10: `ldrh r0,[r5,#0x10]` (0x0026E11C)
    u16 flag_c;                         // +0x12: `ldrh r0,[r5,#0x12]` (0x0026E138)
    u16 flag_d;                         // +0x14: `ldrh r0,[r5,#0x14]` (0x0026E154)
    u8  pad_16[0x0C];                   // +0x16..+0x22
    u16 payload_index;                  // +0x22: `ldrh r0,[r0,#0x22]` (0x0026E520)
    u8  pad_24[0xB0];                   // +0x24..+0xD4
};
static_assert(offsetof(NpcRoomEntry, sprite_id) == 0x02);
static_assert(offsetof(NpcRoomEntry, variant) == 0x04);
static_assert(offsetof(NpcRoomEntry, offset_x) == 0x06);
static_assert(offsetof(NpcRoomEntry, offset_y) == 0x08);
static_assert(offsetof(NpcRoomEntry, group_type) == 0x0A);
static_assert(offsetof(NpcRoomEntry, pose) == 0x0D);
static_assert(offsetof(NpcRoomEntry, flag_a) == 0x0E);
static_assert(offsetof(NpcRoomEntry, flag_d) == 0x14);
static_assert(offsetof(NpcRoomEntry, payload_index) == 0x22);
static_assert(sizeof(NpcRoomEntry) == 0xD4);

/**
 * One 0x10-byte visible-slot record.  Each record holds the entry indices of
 * one `group_type` run; the fill loops use `strh` at +0x64 + n*2 and the
 * records are cleared to 0xFFFF by AsdMem_FillBytes(..., 0x10, 0xFF)
 * (0x0026E1A4..0x0026E1C0).
 */
struct NpcRoomVisible {
    u16 entries[8];                     // +0x00..+0x10
};
static_assert(sizeof(NpcRoomVisible) == 0x10);

/**
 * NpcRoom singleton (`g_NpcRoomWork`, 0x0044D198).  Allocated as exactly
 * 0x108 bytes: `mov r3,#0x108` (0x0026DF74) and `mov r1,#0x108`
 * (0x0026DF8C), then zeroed by AsdMem_Zero.
 */
struct NpcRoomWork {
    void* calc_task;                    // +0x000: `str r0,[r4]` (0x0026DFBC)
    void* sprites[8];                   // +0x004..+0x024: `str r0,[r6,#4]` (0x0026E4C8)
    const NpcRoomEntry* current;        // +0x024: `str r5,[r7,#0x24]` (0x0026E090)
    const NpcRoomEntry* entries[8];     // +0x028..+0x048: `str r5,[r0,#0x28]` (0x0026E178)
    u32 msg_mbm;                        // +0x048: `str r0,[r4,#0x48]` (0x0026E440)
    u32 script_bf;                      // +0x04C: `str r0,[r4,#0x4c]` (0x0026E44C)
    void* script_process_a;             // +0x050: `str r0,[r4,#0x50]` (0x0026E45C)
    void* script_process_b;             // +0x054: `str r0,[r4,#0x54]` (0x0026E474)
    u8  pad_058[0x0C];                  // +0x058..+0x064
    NpcRoomVisible visible[8];          // +0x064..+0x0E4
    u32 visible_count;                  // +0x0E4: `str r0,[r4,#0xe4]` (0x0026E230)
    u8  pad_0e8[0x0C];                  // +0x0E8..+0x0F4
    u32 entry_count;                    // +0x0F4: `str r0,[r7,#0xf4]` (0x0026E188)
    u8  pad_0f8[0x08];                  // +0x0F8..+0x100
    u16 room_id;                        // +0x100: `strh r6,[sl]` (0x0026E04C)
    u16 payload_row;                    // +0x102: `strh r1,[sl,#2]` (0x0026E530)
    u8  pad_104[0x04];                  // +0x104..+0x108
};
static_assert(offsetof(NpcRoomWork, sprites) == 0x004);
static_assert(offsetof(NpcRoomWork, current) == 0x024);
static_assert(offsetof(NpcRoomWork, entries) == 0x028);
static_assert(offsetof(NpcRoomWork, msg_mbm) == 0x048);
static_assert(offsetof(NpcRoomWork, script_process_b) == 0x054);
static_assert(offsetof(NpcRoomWork, visible) == 0x064);
static_assert(offsetof(NpcRoomWork, visible_count) == 0x0E4);
static_assert(offsetof(NpcRoomWork, entry_count) == 0x0F4);
static_assert(offsetof(NpcRoomWork, room_id) == 0x100);
static_assert(offsetof(NpcRoomWork, payload_row) == 0x102);
static_assert(sizeof(NpcRoomWork) == 0x108);

extern NpcRoomWork* g_NpcRoomWork;      // 0x0044D198

// ---------------------------------------------------------------------------
// UIQuest.cpp (0x0026A02C)
// ---------------------------------------------------------------------------

/**
 * UIQuest singleton (`g_UIQuestWork`, 0x0043DD50).  Allocated as exactly
 * 0x9FC bytes: `ldr r5,=0x9fc` (0x0026A034) is passed as the size
 * (`mov r3,r5`, 0x0026A064) and the zero size (`mov r1,r5`, 0x0026A07C).
 */
struct UIQuestWork {
    void* calc_task;                    // +0x000: `str r0,[r4]` (0x0026A0AC)
    void* draw_up_left;                 // +0x004: `str r0,[r4,#4]` (0x0026A5A0 result)
    void* draw_up_right;                // +0x008
    u32 field_00c;                      // +0x00C
    u32 field_010;                      // +0x010: `str r6,[r0,#8]` after STMIB (0x0026A5A0)
    smt4::ui::AsdLayoutRect layout;     // +0x014: 0x002C3344 / 0x002C32F8
    u8  sprites[10 * 0x8C];             // +0x034..+0x5AC: 10 UiAnimSprite objects
    u32 msg_mbm;                        // +0x5AC: "event/quest/QuestSys.mbm" (0x0026A134)
    u32 script_bf;                      // +0x5B0: "event/quest/QuestScr.bf" (0x0026A140)
    void* script_process;               // +0x5B4: `str r0,[r4,#0x5b4]` (0x0026A150)
    u8  pad_5b8[0x3CA];                 // +0x5B8..+0x982
    u16 field_982;                      // +0x982: `strh r6,[r1,#0x82]` (0x0026A154)
    u16 field_984;                      // +0x984: `strh r6,[r1,#0x84]` (0x0026A15C)
    u8  pad_986[0x76];                  // +0x986..+0x9FC
};
static_assert(offsetof(UIQuestWork, calc_task) == 0x000);
static_assert(offsetof(UIQuestWork, field_010) == 0x010);
static_assert(offsetof(UIQuestWork, layout) == 0x014);
static_assert(offsetof(UIQuestWork, sprites) == 0x034);
static_assert(offsetof(UIQuestWork, msg_mbm) == 0x5AC);
static_assert(offsetof(UIQuestWork, script_process) == 0x5B4);
static_assert(offsetof(UIQuestWork, field_982) == 0x982);
static_assert(sizeof(UIQuestWork) == 0x9FC);

extern UIQuestWork* g_UIQuestWork;      // 0x0043DD50

// ---------------------------------------------------------------------------
// qcUtility.cpp (0x003816E4)
// ---------------------------------------------------------------------------

/** 20-bit/flag-filtered quest row (0x20-byte stride in TBB slot 0x26). */
struct QcQuestRow {
    u8  pad_00[0x16];                   // +0x00..+0x16
    u16 value;                          // +0x16: `ldrh ip,[sb,#0x16]` (0x003817EC)
    u16 flag_id;                        // +0x18: `ldrh r0,[sb,#0x18]` (0x003817C4)
    u8  quantity;                       // +0x1A: `ldrb r0,[sl,#0x1a]` (0x003817B8)
    u8  pad_1b[0x05];                   // +0x1B..+0x20
};
static_assert(offsetof(QcQuestRow, value) == 0x16);
static_assert(offsetof(QcQuestRow, flag_id) == 0x18);
static_assert(offsetof(QcQuestRow, quantity) == 0x1A);
static_assert(sizeof(QcQuestRow) == 0x20);

/** 8-byte filtered-list record (`strh r6,[r0]`, `str ip,[r0,#4]`). */
struct QcListEntry {
    u16 index;                          // +0x00
    u16 value;                          // +0x02: `ldrh r2,[r2,#2]` (0x00381838)
    u32 quantity;                       // +0x04: `str ip,[r0,#4]` (0x00381804)
};
static_assert(offsetof(QcListEntry, value) == 0x02);
static_assert(offsetof(QcListEntry, quantity) == 0x04);
static_assert(sizeof(QcListEntry) == 0x08);

/**
 * qcUtility state header (parameter 0).  `category` and `target_index` are
 * read directly from it (`ldrb r1,[r0]`, 0x00381738; `ldrh r1,[r0,#0xc]`,
 * 0x0038181C).  Each budget block owns 20 selection slots at
 * `state + block*0x50 + 0x10` (`add r1,r0,r0,lsl #2` /
 * `add r1,r0,r1,lsl #4`, filled with -2 by 0x00381718..0x00381730).
 */
struct QcUtilityState {
    u8  category;                       // +0x00: `ldrb r1,[r0]` (0x00381738)
    u8  pad_01[0x0B];                   // +0x01..+0x0C
    u16 target_index;                   // +0x0C: `ldrh r1,[r0,#0xc]` (0x0038181C)
    u8  pad_0e[0x02];                   // +0x0E..+0x10
};
static_assert(offsetof(QcUtilityState, category) == 0x00);
static_assert(offsetof(QcUtilityState, target_index) == 0x0C);
static_assert(sizeof(QcUtilityState) == 0x10);

// ---------------------------------------------------------------------------
// scrScriptProcess.cpp (0x002972F8)
// ---------------------------------------------------------------------------

/** 0x10-byte command descriptor at script+0x20 (`add r3,r6,r2,lsl #4`). */
struct ScrScriptDescriptor {
    u32 type;                           // +0x00: `ldr fp,[r3]` (0x00297358)
    u32 field_04;
    u32 field_08;
    u32 offset;                         // +0x0C: `ldr r7,[r3,#0xc]` (0x0029737C)
};
static_assert(sizeof(ScrScriptDescriptor) == 0x10);

/**
 * One script-process node (`AsdMem_AllocAlign(..., 0x10C, 0)`).
 * The name is copied byte-by-byte at 0x00297424..0x00297434; +0x18 receives
 * the word at `descriptor_payload + 0x18` (0x00297438).
 */
struct ScrScriptProcess {
    char name[0x18];                    // +0x000: copy loop (0x00297424)
    s32 field_018;                      // +0x018: `stm r2,{r0,fp}` (0x00297444)
    u32 field_01c;                      // +0x01C
    u32 field_020;                      // +0x020..+0x038: word clears
    u32 field_024;
    u32 field_028;
    u32 field_02c;
    u32 field_030;
    u32 field_034;
    u32 field_038;
    u8  block_03c[0x70];                // +0x03C..+0x0AC: AsdMem_Zero(...,0x70)
    void* script;                       // +0x0AC: `stm r0,{r5,...}` (0x00297474)
    void* commands;                     // +0x0B0: script + 0x20
    u32 offset_name;                    // +0x0B4
    u32 offset_sl;                      // +0x0B8
    u32 offset_r8;                      // +0x0BC: `str r8,[r4,#0xbc]` (0x00297470)
    void* msg;                          // +0x0C0: `str r0,[r4,#0xc0]` (0x00297480)
    u32 offset_ip;                      // +0x0C4: `stm r2,{r0,sb,fp}` (0x00297488)
    u32 field_0c8;
    u32 field_0cc;
    u32 field_0d0;                      // +0x0D0
    u32 field_0d4;
    u32 field_0d8;
    u32 field_0dc;
    u32 field_0e0;
    u32 field_0e4;
    s32* values;                        // +0x0E8: `str r0,[r4,#0xe8]` (0x002974EC)
    f32* floats;                        // +0x0EC: `str r0,[r4,#0xec]` (0x00297580)
    ScrScriptProcess* prev;             // +0x0F0: `str r1,[r4,#0xf0]` (0x002975F4)
    ScrScriptProcess* next;             // +0x0F4: `str fp,[r4,#0xf4]` (0x002975FC)
    u8  pad_0f8[0x10];                  // +0x0F8..+0x108
    u32 state;                          // +0x108: caller writes 2 (0x0026E460 / 0x0026E478)
};
static_assert(offsetof(ScrScriptProcess, field_018) == 0x018);
static_assert(offsetof(ScrScriptProcess, block_03c) == 0x03C);
static_assert(offsetof(ScrScriptProcess, script) == 0x0AC);
static_assert(offsetof(ScrScriptProcess, commands) == 0x0B0);
static_assert(offsetof(ScrScriptProcess, offset_r8) == 0x0BC);
static_assert(offsetof(ScrScriptProcess, msg) == 0x0C0);
static_assert(offsetof(ScrScriptProcess, offset_ip) == 0x0C4);
static_assert(offsetof(ScrScriptProcess, values) == 0x0E8);
static_assert(offsetof(ScrScriptProcess, floats) == 0x0EC);
static_assert(offsetof(ScrScriptProcess, prev) == 0x0F0);
static_assert(offsetof(ScrScriptProcess, next) == 0x0F4);
static_assert(offsetof(ScrScriptProcess, state) == 0x108);
static_assert(sizeof(ScrScriptProcess) == 0x10C);

/** Script-process list head, 0x0044DE78 (`ldr r1,[r0,#8]`, 0x002975E8). */
struct ScrScriptProcessList {
    u32 count;                          // +0x00: incremented at 0x00297604
    ScrScriptProcess* head;             // +0x04
    ScrScriptProcess* tail;             // +0x08
};
static_assert(offsetof(ScrScriptProcessList, head) == 0x04);
static_assert(offsetof(ScrScriptProcessList, tail) == 0x08);
static_assert(sizeof(ScrScriptProcessList) == 0x0C);

extern ScrScriptProcessList g_ScrScriptProcessList; // 0x0044DE78

// ---------------------------------------------------------------------------
// qcMain.cpp (0x001A969C)
// ---------------------------------------------------------------------------

/**
 * qcMain shared state (`g_QcMainState`, 0x0044DB88).  The .data image is
 * {0, 0, 1, 0, 0}; +0x08 holds the initial tab index 1
 * (`ldr r0,[r7,#8]`, 0x001A9744).
 */
struct QcMainState {
    u32 field_00;                       // +0x00 (never read here)
    void* work;                         // +0x04: `str r0,[r7,#4]` (0x001A96EC)
    s32 field_08;                       // +0x08: .data = 1
    s32 field_0c;                       // +0x0C
    s32 field_10;                       // +0x10
};
static_assert(offsetof(QcMainState, work) == 0x04);
static_assert(offsetof(QcMainState, field_08) == 0x08);
static_assert(offsetof(QcMainState, field_10) == 0x10);
static_assert(sizeof(QcMainState) == 0x14);

extern QcMainState g_QcMainState;       // 0x0044DB88

/**
 * qcMain singleton (`g_QcMainWork`, allocated as 0x20 bytes by
 * `mov r3,#0x20`, 0x001A96C8).  Only +0x00, +0x04, +0x0C, +0x18, +0x19 and
 * +0x1C are written by this function.
 */
struct QcMainWork {
    void* calc_task;                    // +0x00: `str r0,[r4]` (0x001A97D4)
    void* draw_up;                      // +0x04
    u8  pad_08[0x04];                   // +0x08..+0x0C
    void* draw_down;                    // +0x0C: `str r0,[r4,#0xc]` (0x001A9880)
    u8  pad_10[0x08];                   // +0x10..+0x18
    u8  flag_18;                        // +0x18: `strb r8,[r0,#0x18]` (0x001A96F0)
    u8  flag_19;                        // +0x19: `strb r8,[r0,#0x19]` (0x001A96F8)
    u8  pad_1a[0x02];                   // +0x1A..+0x1C
    u32 field_1c;                       // +0x1C: `str r8,[r0,#0x1c]` (0x001A96F4)
};
static_assert(offsetof(QcMainWork, calc_task) == 0x00);
static_assert(offsetof(QcMainWork, draw_up) == 0x04);
static_assert(offsetof(QcMainWork, draw_down) == 0x0C);
static_assert(offsetof(QcMainWork, flag_18) == 0x18);
static_assert(offsetof(QcMainWork, field_1c) == 0x1C);
static_assert(sizeof(QcMainWork) == 0x20);

// ---------------------------------------------------------------------------
// eventCommand.cpp (0x0025955C)
// ---------------------------------------------------------------------------

/**
 * EventMessUnderFade singleton (`g_EventCommandWork`, 0x0043E088).
 * Allocated as 0x18 bytes (`mov r3,#0x18`, 0x002595A8).
 */
struct EventCommandWork {
    void* calc_task;                    // +0x00: `str r0,[r4]` (0x002595F4)
    u32 owner;                          // +0x04: `str r6,[r0,#4]` (0x00259660)
    f32 value;                          // +0x08: `vstr s16,[r0,#8]` (0x002596AC)
    f32 step;                           // +0x0C: `vstr s1,[r0,#0xc]` (0x00259680)
    u32 field_10;                       // +0x10: `str r8,[r0,#0x10]` (0x00259654)
    u32 frames;                         // +0x14: `str r5,[r0,#0x14]` (0x00259650)
};
static_assert(offsetof(EventCommandWork, owner) == 0x04);
static_assert(offsetof(EventCommandWork, value) == 0x08);
static_assert(offsetof(EventCommandWork, step) == 0x0C);
static_assert(offsetof(EventCommandWork, field_10) == 0x10);
static_assert(offsetof(EventCommandWork, frames) == 0x14);
static_assert(sizeof(EventCommandWork) == 0x18);

extern EventCommandWork* g_EventCommandWork; // 0x0043E088

// ---------------------------------------------------------------------------
// EventEffect.cpp (0x0030A4FC)
// ---------------------------------------------------------------------------

/**
 * BlinkFade singleton (`g_EventEffectWork`, 0x0043DEE8).
 * Allocated as 0x1C bytes (`mov r3,#0x1c`, 0x0030A528).
 */
struct EventEffectWork {
    void* calc_task;                    // +0x00: `str r0,[r4]` (0x0030A584)
    void* draw_up_left;                 // +0x04
    void* draw_up_right;                // +0x08
    u32 field_0c;                       // +0x0C: `str r0,[r4,#0xc]` = 0x28 (0x0030A5F4)
    u32 field_10;                       // +0x10: `str r5,[r4,#0x10]` = 0 (0x0030A5D8)
    f32 field_14;                       // +0x14: `vstr s0` 1.0f (0x0030A5F0)
    u8  flag_18;                        // +0x18: `strb r5,[r4,#0x18]` = 0 (0x0030A5E8)
    u8  pad_19[0x03];                   // +0x19..+0x1C
};
static_assert(offsetof(EventEffectWork, field_0c) == 0x0C);
static_assert(offsetof(EventEffectWork, field_10) == 0x10);
static_assert(offsetof(EventEffectWork, field_14) == 0x14);
static_assert(offsetof(EventEffectWork, flag_18) == 0x18);
static_assert(sizeof(EventEffectWork) == 0x1C);

extern EventEffectWork* g_EventEffectWork; // 0x0043DEE8

/**
 * One 0xC-byte BlinkFade texture-table row at 0x0043DF00.  The .data image is
 * {key 0x2D, row 4} and {key 0x2D, row 6}; the two load flags start clear
 * (`strb r8,[r6,#8]`, 0x0030A64C; `strb r8,[r0,#9]`, 0x0030A620).
 */
struct BlinkFadeTexture {
    u32 key;                            // +0x00: `ldr r0,[r7,r4,lsl #2]` (0x0030A5FC)
    u32 row;                            // +0x04: `ldr r1,[r6,#4]` (0x0030A62C)
    u8  res_loaded;                     // +0x08
    u8  table_loaded;                   // +0x09
    u8  pad_0a[0x02];
};
static_assert(offsetof(BlinkFadeTexture, row) == 0x04);
static_assert(offsetof(BlinkFadeTexture, res_loaded) == 0x08);
static_assert(offsetof(BlinkFadeTexture, table_loaded) == 0x09);
static_assert(sizeof(BlinkFadeTexture) == 0x0C);

extern BlinkFadeTexture g_BlinkFadeTextures[2]; // 0x0043DF00

// ---------------------------------------------------------------------------
// clearSave.cpp (0x001E1118)
// ---------------------------------------------------------------------------

/**
 * clearSave singleton (`g_ClearSaveWork`, 0x0043DE80).  Allocated as exactly
 * 0x94 bytes: `mov r3,#0x94` (0x001E1138) and `mov r1,#0x94` (0x001E1150).
 */
struct ClearSaveWork {
    void* calc_task;                    // +0x00: `str r0,[r1]` (0x001E1214)
    u8  pad_04[0x04];
    u8  flag_08;                        // +0x08: `strbeq r6,[r0,#8]` (0x001E1164)
    u8  pad_09[0x7F];                   // +0x09..+0x88
    u32 script_bf;                      // +0x88: "clear_save/clearSave.bf" (0x001E1188)
    void* script_process;               // +0x8C: `str r0,[r4,#0x8c]` (0x001E11A8)
    u32 msg_mbm;                        // +0x90: "clear_save/clearSave.mbm" (0x001E1198)
};
static_assert(offsetof(ClearSaveWork, flag_08) == 0x08);
static_assert(offsetof(ClearSaveWork, script_bf) == 0x88);
static_assert(offsetof(ClearSaveWork, script_process) == 0x8C);
static_assert(offsetof(ClearSaveWork, msg_mbm) == 0x90);
static_assert(sizeof(ClearSaveWork) == 0x94);

extern ClearSaveWork* g_ClearSaveWork;  // 0x0043DE80

// ---------------------------------------------------------------------------
// Entry points (address / size match config/functions.csv)
// ---------------------------------------------------------------------------

void NpcRoom_func_0026df40(u32 room_id);                    // 0x0026DF40, 1620 B
void UIQuest_func_0026a02c();                               // 0x0026A02C, 1412 B
u32  qcUtility_func_003816e4(void* state, u32 block, void* context,
                             s32 selected, u32 ext_offset,
                             s32 min_index, s32 max_index); // 0x003816E4, 1012 B
ScrScriptProcess* scrScriptProcess_func_002972f8(void* script,
                                                 void* msg); // 0x002972F8, 892 B
void qcMain_func_001a969c(const u32* args, u32 mode);       // 0x001A969C, 644 B
void eventCommand_func_0025955c(u32 owner, s32 frames, u32 mode,
                                f32 alpha);                 // 0x0025955C, 516 B
void EventEffect_func_0030a4fc();                           // 0x0030A4FC, 504 B
void clearSave_func_001e1118(u32 arg);                      // 0x001E1118, 488 B

} // namespace smt4::script
