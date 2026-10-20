#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::camp {

/**
 * Unite / Bible result-selection entry (0x20 bytes).
 *
 * Filled on the stack by 0x0022E310 (`camp_func_0022e310`) and copied into a
 * `UnitePickList` slot by 0x0022E2EC (`unite_func_0022e2ec`, `vstmia` of eight
 * words at list+count*0x20+4).  The +0x18 word is the 0x0029D100 result; the
 * +0x1C word is the 0x002BD25C lookup result (0x0022E358).
 */
struct UnitePickEntry {
    u16 demon_id;                       // +0x00: row id / 0x0029D100 first argument
    u8 field_02;                        // +0x02: row +0x02
    u8 field_03;                        // +0x03: row +0x04
    u8 field_04;                        // +0x04: row +0x05
    u8 pad_05;                          // +0x05: not written by 0x0022E310
    u16 field_06;                       // +0x06: inherited-skill counter (mode != 0)
    u8 pad_08[4];                       // +0x08..+0x0C
    u8 field_0c;                        // +0x0C: row2 +0x48
    u8 field_0d;                        // +0x0D: row2 +0x48 (second lookup)
    u16 field_0e;                       // +0x0E: row2 +0x0E
    u16 field_10;                       // +0x10: row2 +0x0E (second lookup)
    u16 field_12;                       // +0x12: row2 +0x10
    u16 field_14;                       // +0x14: row2 +0x10 (second lookup)
    u8 pad_16[2];                       // +0x16..+0x18
    u32 field_18;                       // +0x18: camp_func_0029d100 result (0x0022D694)
    u32 field_1c;                       // +0x1C: script_vm_func_002bd25c result (0x0022E358)
};

static_assert(offsetof(UnitePickEntry, demon_id) == 0x00);
static_assert(offsetof(UnitePickEntry, field_06) == 0x06);
static_assert(offsetof(UnitePickEntry, field_0c) == 0x0C);
static_assert(offsetof(UnitePickEntry, field_18) == 0x18);
static_assert(offsetof(UnitePickEntry, field_1c) == 0x1C);
static_assert(sizeof(UnitePickEntry) == 0x20);

/**
 * Result list at work+0x5A8.
 *
 * 0x0022E490 writes the 4-byte header (count at +0x00), clears every one of
 * the 0x500 0x20-byte slots starting at +0x04, and sets +0xA004 = -1 and
 * +0xA006 = 0x500.  0x0022E2EC appends at +0x04+count*0x20; 0x0022E290 sorts
 * the slots (size 0x20) after comparing the cached mode byte at +0xA004.
 */
struct UnitePickList {
    s16 count;                          // +0x0000: `ldrsh r2,[r0]` (0x0022E2EC)
    u8 pad_02[2];                       // +0x0002..+0x0004
    UnitePickEntry entries[0x500];      // +0x0004..+0xA004
    s8 sort_mode;                       // +0xA004: cached comparator index (init -1)
    u8 pad_a005;                        // +0xA005
    s16 capacity;                       // +0xA006: init 0x500, 0x0022E244 denominator
};

static_assert(offsetof(UnitePickList, count) == 0x0000);
static_assert(offsetof(UnitePickList, entries) == 0x0004);
static_assert(offsetof(UnitePickList, sort_mode) == 0xA004);
static_assert(offsetof(UnitePickList, capacity) == 0xA006);
static_assert(sizeof(UnitePickList) == 0xA008);

/**
 * 0x68-byte UI list object stored at work+0x590.
 *
 * Created by AsdMemory_func_002c23f8(0x68) and constructed by 0x002333BC
 * (vtable 0x004221E4, u16 +4 = 0); the caller replaces the vtable with
 * 0x0042207C and stores work+0xC8 at +0x64.  0x002339E8 reads the s16 count
 * at +0x5A and 0x0022D5C8 reads/or's the u16 flags at +4.
 */
struct UniteUiList {
    void** vtable;                      // +0x00: 0x0042207C; [vtable+8] called with work+0x20
    u16 flags;                          // +0x04: `ldrh r1,[r0,#4]!` | 0x1000 (0x0022D784)
    u8 pad_06[0x54];                    // +0x06..+0x5A
    s16 count;                          // +0x5A: entries cleared by 0x002339E8
    u8 pad_5c[0x0C];                    // +0x5C..+0x68
};

static_assert(offsetof(UniteUiList, vtable) == 0x00);
static_assert(offsetof(UniteUiList, flags) == 0x04);
static_assert(offsetof(UniteUiList, count) == 0x5A);
static_assert(sizeof(UniteUiList) == 0x68);

/**
 * Ten-line result text block at work+0x55C (0x34 bytes).
 *
 * 0x00233804 stores the three words at +4/+8/+0xC, -1 at +0x14, clears
 * +0x11/+0x12/+0x16 and appends up to twelve u16 table ids at +0x18.  The
 * byte at +0x10 is the per-screen "rows enabled" flag that all three setup
 * paths write through work+0x56C (`strb ...,[r5,#0x56c]`).
 */
struct UniteResultRows {
    u8 pad_00[4];                       // +0x00..+0x04
    u32 field_04;                       // +0x04: 0x1D
    u32 field_08;                       // +0x08: 0x40E
    u32 limit;                          // +0x0C: requested row count
    u8 enabled;                         // +0x10: work+0x56C, set to 1 by all callers
    u8 field_11;                        // +0x11: cleared
    u8 field_12;                        // +0x12: cleared
    u8 pad_13;                          // +0x13
    u16 field_14;                       // +0x14: -1
    u16 field_16;                       // +0x16: cleared
    u16 entries[12];                    // +0x18..+0x30
    s16 count;                          // +0x30: entries appended by 0x00233804
    u8 pad_32[2];                       // +0x32..+0x34
};

static_assert(offsetof(UniteResultRows, field_04) == 0x04);
static_assert(offsetof(UniteResultRows, limit) == 0x0C);
static_assert(offsetof(UniteResultRows, enabled) == 0x10);
static_assert(offsetof(UniteResultRows, field_14) == 0x14);
static_assert(offsetof(UniteResultRows, entries) == 0x18);
static_assert(offsetof(UniteResultRows, count) == 0x30);
static_assert(sizeof(UniteResultRows) == 0x34);

/**
 * Shared Unite / Bible Devil / Bible LegionSkill workspace (0xA5B4 bytes).
 *
 * The task/draw handles and the vtable at +0 are written by
 * bibleDevil_func_003a7ad8 and bibleLegionSkill_func_003ab770; the result
 * selection list lives at +0x5A8 and is driven by unite_func_0022d5c8.
 */
struct UniteExtrasWork {
    void** vtable;                      // +0x0000: [vtable+0x20] invoked at 0x003A7B28
    void* calc_task;                    // +0x0004: "BIBLE ... CALC" task
    void* draw_up_task;                 // +0x0008: tag 0x6F draw task
    void* draw_down_task;               // +0x000C: tag 0xE6 draw task
    u8 pad_010[4];                      // +0x0010..+0x0014
    s32 field_014;                      // +0x0014: 0 for Devil, 1 for LegionSkill
    s32 field_018;                      // +0x0018: 0
    u8 pad_01c[4];                      // +0x001C..+0x0020
    u8 result_mode;                     // +0x0020: read by 0x002338C4
    u8 pad_021[3];                      // +0x0021..+0x0024
    s32 result_field_024;               // +0x0024: 0x0A (`strd r6,r7,[r4,#4]`)
    s32 result_count;                   // +0x0028: list count
    u8 result_field_02c;                // +0x002C: cleared by 0x002338C4
    u8 result_field_02d;                // +0x002D: set to 1 by the setup paths
    u8 pad_02e[0x66];                   // +0x002E..+0x0094
    s8 completion;                      // +0x0094: percentage / 0x003AD8C0 result
    u8 pad_095;                         // +0x0095
    u16 selected_ids[0x10];             // +0x0096..+0x00B6: 16 result ids (init -1)
    u8 selected_flags[0x10];            // +0x00B6..+0x00C6: per-id present flags
    u8 pad_0c6[2];                      // +0x00C6..+0x00C8
    u8 skill_panel[0x494];              // +0x00C8..+0x055C: rect at +0xC8, 0x480 sprite group at +0xDC
    UniteResultRows result_rows;        // +0x055C..+0x0590
    UniteUiList* ui_list;               // +0x0590: 0x68-byte object
    u8 pad_594[0x10];                   // +0x0594..+0x05A4
    u8 list_mode;                       // +0x05A4: 1 = gamedata roster path (0x0022D5FC)
    u8 sort_mode;                       // +0x05A5: 0x0029D100 second argument
    u8 pad_5a6[2];                      // +0x05A6..+0x05A8
    UnitePickList list;                 // +0x05A8..+0x0A5B0
    u8 field_a5b0;                      // +0x0A5B0: 0
    u8 pad_a5b1;                        // +0x0A5B1
    s16 field_a5b2;                     // +0x0A5B2: -1 in bibleDevil_func_003a7ad8
};

static_assert(offsetof(UniteExtrasWork, vtable) == 0x0000);
static_assert(offsetof(UniteExtrasWork, calc_task) == 0x0004);
static_assert(offsetof(UniteExtrasWork, field_014) == 0x0014);
static_assert(offsetof(UniteExtrasWork, field_018) == 0x0018);
static_assert(offsetof(UniteExtrasWork, result_mode) == 0x0020);
static_assert(offsetof(UniteExtrasWork, result_field_024) == 0x0024);
static_assert(offsetof(UniteExtrasWork, result_count) == 0x0028);
static_assert(offsetof(UniteExtrasWork, result_field_02c) == 0x002C);
static_assert(offsetof(UniteExtrasWork, result_field_02d) == 0x002D);
static_assert(offsetof(UniteExtrasWork, completion) == 0x0094);
static_assert(offsetof(UniteExtrasWork, selected_ids) == 0x0096);
static_assert(offsetof(UniteExtrasWork, selected_flags) == 0x00B6);
static_assert(offsetof(UniteExtrasWork, skill_panel) == 0x00C8);
static_assert(offsetof(UniteExtrasWork, result_rows) == 0x055C);
static_assert(offsetof(UniteExtrasWork, ui_list) == 0x0590);
static_assert(offsetof(UniteExtrasWork, list_mode) == 0x05A4);
static_assert(offsetof(UniteExtrasWork, sort_mode) == 0x05A5);
static_assert(offsetof(UniteExtrasWork, list) == 0x05A8);
static_assert(offsetof(UniteExtrasWork, field_a5b0) == 0x0A5B0);
static_assert(offsetof(UniteExtrasWork, field_a5b2) == 0x0A5B2);
static_assert(sizeof(UniteExtrasWork) == 0xA5B4);

/**
 * 0x94-byte demon table row returned by camp_func_002b9364.
 * Only the fields read by these five functions are named.
 */
struct UniteBibleRow {
    u16 id;                             // +0x00
    u8 race;                            // +0x02: UniteCtrl bucket (0..0x37)
    u8 field_03;                        // +0x03: secondary sort value
    u8 field_04;                        // +0x04
    u8 field_05;                        // +0x05
    u16 flags;                          // +0x06: bit 0 = available
    u8 raw[0x94 - 0x08];                // +0x08..+0x94
};

static_assert(offsetof(UniteBibleRow, id) == 0x00);
static_assert(offsetof(UniteBibleRow, race) == 0x02);
static_assert(offsetof(UniteBibleRow, flags) == 0x06);
static_assert(sizeof(UniteBibleRow) == 0x94);

/**
 * 0x604-byte gamedata record addressed through the 0x0043E2A8 manager
 * (base = *(0x0043E2A8 + 4) + 0x8C; record n = base + 0x90 + n*0x604).
 */
struct UniteGamedataRecord {
    u8 raw_00[0x46];                    // +0x0000..+0x0046
    u16 demon_id;                       // +0x0046: camp_func_002b9364 key
    u8 raw_48[0x604 - 0x48];            // +0x0048..+0x0604
};

static_assert(offsetof(UniteGamedataRecord, demon_id) == 0x46);
static_assert(sizeof(UniteGamedataRecord) == 0x604);

/**
 * One {id, value} entry in a UniteCtrl_func_003c9ebc race bucket (4 bytes).
 * 0x00219600 orders by value (+2) and then id (+0).
 */
struct UniteCtrlEntry {
    u16 demon_id;                       // +0x00
    u16 field_02;                       // +0x02: UniteBibleRow::field_03
};

static_assert(sizeof(UniteCtrlEntry) == 4);

/**
 * Output of UniteCtrl_func_003c9ebc.
 *
 * The function clears 0x38 bytes of per-race counts, allocates 0x38 bucket
 * arrays of 4-byte entries, fills {id, row+3} and sorts every non-empty
 * bucket, then initialises the tail fields below.
 */
struct UniteCtrlRoster {
    u8 counts[0x38];                    // +0x000: per-race entry counts
    UniteCtrlEntry* buckets[0x38];      // +0x038: per-race sorted arrays
    u8 field_118;                       // +0x118: cleared
    u8 pad_119;                         // +0x119
    u16 field_11a;                      // +0x11A: cleared
    u8 field_11c;                       // +0x11C: cleared
    u8 pad_11d;                         // +0x11D
    u16 field_11e;                      // +0x11E: cleared
    u8 field_120;                       // +0x120: cleared
    u8 field_121;                       // +0x121: cleared
    u8 field_122[4];                    // +0x122: cleared as a word
    u8 field_126[4];                    // +0x126: cleared as a word
    u8 field_12a[4];                    // +0x12A: cleared as a word
    u8 field_12e[4];                    // +0x12E: cleared as a word
    u8 field_132;                       // +0x132: cleared
    u16 field_134;                      // +0x134: bits 10..15 cleared (`bic #0xFC00`)
    u8 field_136;                       // +0x136: cleared
    u16 field_138;                      // +0x138: -1
    u16 field_13a;                      // +0x13A: -1
    u8 pad_13c[7];                      // +0x13C..+0x143
    u8 field_143;                       // +0x143: cleared
    u8 pad_144[0x38];                   // +0x144..+0x17C
    u8 field_17c;                       // +0x17C: cleared
};

static_assert(offsetof(UniteCtrlRoster, counts) == 0x000);
static_assert(offsetof(UniteCtrlRoster, buckets) == 0x038);
static_assert(offsetof(UniteCtrlRoster, field_118) == 0x118);
static_assert(offsetof(UniteCtrlRoster, field_11a) == 0x11A);
static_assert(offsetof(UniteCtrlRoster, field_11c) == 0x11C);
static_assert(offsetof(UniteCtrlRoster, field_11e) == 0x11E);
static_assert(offsetof(UniteCtrlRoster, field_122) == 0x122);
static_assert(offsetof(UniteCtrlRoster, field_12e) == 0x12E);
static_assert(offsetof(UniteCtrlRoster, field_134) == 0x134);
static_assert(offsetof(UniteCtrlRoster, field_138) == 0x138);
static_assert(offsetof(UniteCtrlRoster, field_143) == 0x143);
static_assert(offsetof(UniteCtrlRoster, field_17c) == 0x17C);

/**
 * bibleLegionDraw.cpp workspace (0x474 bytes).
 *
 * Allocated on the first call (`ldr r0,[r8,#4]` null check at 0x003AD328);
 * the four 0x8C-byte sprite nodes are initialised by the 0x003AD460 loop.
 */
struct BibleLegionDrawWork {
    void* calc_task;                    // +0x000: "LegionDrawUp CALC" (0x003AD414)
    s32 field_004;                      // +0x004: cleared
    s16 field_008;                      // +0x008: -1
    u8 pad_00a[2];                      // +0x00A..+0x00C
    s32 field_00c;                      // +0x00C: cleared
    s16 field_010;                      // +0x010: -1
    u8 pad_012[2];                      // +0x012..+0x014
    s32 field_014;                      // +0x014: cleared
    s16 field_018;                      // +0x018: -1
    u8 pad_01a[2];                      // +0x01A..+0x01C
    u8 field_01c;                       // +0x01C: cleared
    u8 field_01d;                       // +0x01D: cleared
    u8 field_01e;                       // +0x01E: cleared
    u8 field_01f;                       // +0x01F: cleared
    u8 text_block[0x20];                // +0x020..+0x040: cleared, 0x002C32F8 init
    u8 sprite_0[0x8C];                  // +0x040..+0x0CC: 0x002BDB2C node
    u8 sprite_1[0x8C];                  // +0x0CC..+0x158
    u8 sprite_2[0x8C];                  // +0x158..+0x1E4
    u8 sprite_3[0x8C];                  // +0x1E4..+0x270
    u16 field_270;                      // +0x270: cleared
    u16 field_272;                      // +0x272: cleared
    f32 field_274;                      // +0x274: 0.0
    f32 field_278;                      // +0x278: 0.0
    f32 field_27c;                      // +0x27C: 1.0
    f32 field_280;                      // +0x280: -3.0 (0xC0400000)
    u16 field_284;                      // +0x284: cleared
    u16 field_286;                      // +0x286: cleared
    u16 field_288;                      // +0x288: Random_Range(0xC8) + 0x64
    u16 field_28a;                      // +0x28A: Random_Range(0xC8) + 0x64
    u8 field_28c;                       // +0x28C: cleared
    u8 field_28d;                       // +0x28D: cleared
    u8 pad_28e[2];                      // +0x28E..+0x290
    u8 block_290[0x1E0];                // +0x290..+0x470: AsdMem_Zero(...,0x1E0)
    u8 field_470;                       // +0x470: cleared
    u8 pad_471[3];                      // +0x471..+0x474
};

static_assert(offsetof(BibleLegionDrawWork, calc_task) == 0x000);
static_assert(offsetof(BibleLegionDrawWork, text_block) == 0x020);
static_assert(offsetof(BibleLegionDrawWork, sprite_0) == 0x040);
static_assert(offsetof(BibleLegionDrawWork, sprite_1) == 0x0CC);
static_assert(offsetof(BibleLegionDrawWork, sprite_2) == 0x158);
static_assert(offsetof(BibleLegionDrawWork, sprite_3) == 0x1E4);
static_assert(offsetof(BibleLegionDrawWork, field_270) == 0x270);
static_assert(offsetof(BibleLegionDrawWork, field_280) == 0x280);
static_assert(offsetof(BibleLegionDrawWork, field_288) == 0x288);
static_assert(offsetof(BibleLegionDrawWork, block_290) == 0x290);
static_assert(offsetof(BibleLegionDrawWork, field_470) == 0x470);
static_assert(sizeof(BibleLegionDrawWork) == 0x474);

/**
 * LegionDraw manager at 0x0043D9E0 (.data, all zero).
 * +0 is incremented by bibleLegionDraw_func_003ad300; +1 by
 * engine_func_003acd48 (texture-table bring-up reached from bibleLegionSkill).
 */
struct BibleLegionDrawManager {
    s8 draw_ref_count;                  // +0x00
    s8 tex_ref_count;                   // +0x01: `ldrsb r0,[r5,#1]` (0x003ACD50)
    u8 pad_02[2];                       // +0x02..+0x04
    BibleLegionDrawWork* work;          // +0x04
};

static_assert(offsetof(BibleLegionDrawManager, work) == 0x04);
static_assert(sizeof(BibleLegionDrawManager) == 0x08);

/**
 * bibleDevil.cpp manager at 0x0043D9C8 (.data, all zero).
 * 0x003AAF30 frees the 4-byte handle at +0 when the calc task is torn down;
 * bibleDevil_func_003a7ad8 stores -1 in the word at +4.
 */
struct BibleDevilManager {
    void** work_handle;                 // +0x00: allocated 4 bytes; [0] = UniteExtrasWork*
    s32 field_04;                       // +0x04: -1
};

static_assert(offsetof(BibleDevilManager, field_04) == 0x04);
static_assert(sizeof(BibleDevilManager) == 0x08);

/**
 * bibleLegionSkill.cpp manager at 0x0043D9F8 (.data, all zero).
 * 0x003AD05C frees the 4-byte handle at +0.
 */
struct BibleLegionSkillManager {
    void** work_handle;                 // +0x00: allocated 4 bytes; [0] = UniteExtrasWork*
};

extern BibleDevilManager g_BibleDevilManager;               // 0x0043D9C8
extern BibleLegionDrawManager g_BibleLegionDrawManager;      // 0x0043D9E0
extern BibleLegionSkillManager g_BibleLegionSkillManager;    // 0x0043D9F8

// unite_func_0022d5c8.cpp / bibleDevil.cpp / bibleLegionSkill.cpp entries
void unite_func_0022d5c8(UniteExtrasWork* work);            // 0x0022D5C8
void bibleDevil_func_003a7ad8(UniteExtrasWork* work);       // 0x003A7AD8
void bibleLegionSkill_func_003ab770(UniteExtrasWork* work); // 0x003AB770

// bibleLegionDraw.cpp entry (the listing leaves r0 dead at 0x003AB90C)
void bibleLegionDraw_func_003ad300();                       // 0x003AD300

// UniteCtrl.cpp race-bucket builder
void UniteCtrl_func_003c9ebc(UniteCtrlRoster* roster);      // 0x003C9EBC

} // namespace smt4::camp
