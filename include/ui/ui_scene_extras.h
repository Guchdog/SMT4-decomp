#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"

namespace smt4::ui {

/**
 * Views required by the four large unnamed UI routines added by the 21%
 * milestone.  Every offset below is backed by the ARM listing quoted next to
 * the field; nothing is inferred from unrelated TUs.  The ledger names are
 * kept unchanged.
 *
 *   0x001E83FC  talk-target / model selection overlay
 *   0x00243E8C  effect-menu (effMenu.cpp) option-row renderer
 *   0x002F150C  battle command ring ("Attack" / "Shoot" / "Analyze")
 *   0x003D7630  battle-result panel state machine
 */

// ---------------------------------------------------------------------------
// 0x001E83FC: talk-target / model selection overlay
// ---------------------------------------------------------------------------

/** Fallback game-window state at 0x0049F91C.  The routine gates on +0x380
 *  (`ldr r1,[r0,#0x380]`, 0x001E840C), +0x22/+0x24 (`ldrb`, 0x001E8420 /
 *  0x001E842C) and the busy byte at +0x18 (`ldrb r0,[r5,#0x18]`,
 *  0x001E8F44).  The only other readers are the overlay pop in the 0x003D7630
 *  TU, which uses the same +0x380 word. */
struct UiWindowState {
    u8  pad_00[0x18];
    u8  busy_18;                    // +0x18: `ldrb r0,[r5,#0x18]` (0x001E8F44)
    u8  pad_19[0x22 - 0x19];
    u8  field_22;                   // +0x22: `ldrb r1,[r0,#0x22]` (0x001E8420)
    u8  pad_23[0x01];
    u8  field_24;                   // +0x24: `ldrb r0,[r0,#0x24]` (0x001E842C)
    u8  pad_25[0x380 - 0x25];
    s32 enabled_380;                // +0x380: `ldr r1,[r0,#0x380]` (0x001E840C)
};
static_assert(offsetof(UiWindowState, busy_18) == 0x18);
static_assert(offsetof(UiWindowState, field_22) == 0x22);
static_assert(offsetof(UiWindowState, field_24) == 0x24);
static_assert(offsetof(UiWindowState, enabled_380) == 0x380);

/** Overlay flags at 0x0049FB1C.  `+0x2A` enables the secondary target list
 *  (`ldrb r0,[fp,#0x2a]`, 0x001E852C) and `+0x29` gates the alternate rows
 *  (`ldrb r0,[fp,#0x29]`, 0x001E8534). */
struct TalkOverlayFlags {
    u8  pad_00[0x29];
    u8  field_29;                   // +0x29
    u8  field_2a;                   // +0x2A
};

/** Camera/render context behind 0x004474F4.  `*ctx` is the mode compared
 *  against 3 (`ldr r0,[r0]; cmp r0,#3`, 0x001E843C); +0x4C is the camera
 *  position consumed by the distance helper 0x00287D54
 *  (`vldmia r0,{s0,s1,s2}`, 0x001E85E0). */
struct TalkCamera {
    s32 mode_00;                    // +0x00: `ldr r0,[r0]` (0x001E8440)
    u8  pad_04[0x4c - 0x04];
    f32 pos_4c[3];                  // +0x4C: `vldmia r0,{s0,s1,s2}` (0x001E85E0)
};
static_assert(offsetof(TalkCamera, mode_00) == 0x00);
static_assert(offsetof(TalkCamera, pos_4c) == 0x4C);

/** One of 128 0x194-byte target records in `TalkWork`.  The loop advances by
 *  `0x65*4 = 0x194` (`mov r0,#0x65; mul r0,r5,r0; add r4,r6,r0,lsl #2`,
 *  0x001E84C0..0x001E84C8) and pre-indexes the first field with
 *  `ldrb r0,[r4,#0x1d0]!` (0x001E84CC), so all offsets are record-relative. */
struct TalkTargetEntry {
    u8  active_000;                 // +0x00: pre-indexed `ldrb` (0x001E84CC)
    u8  pad_001[0x0B];
    s16 kind_00c;                   // +0x0C: `ldrshne r0,[r4,#0xc]` (0x001E84D4)
    u8  pad_00e[0x06];
    s32 type_014;                   // +0x14: `ldr r0,[r4,#0x14]` (0x001E85E8)
    u8  pad_018[0x10];
    s16 frame_028;                  // +0x28: `ldrsh r0,[r4,#0x28]` (0x001E8764)
    u8  pad_02a[0x18];
    u8  flag_042;                   // +0x42: `ldrbne r1,[r4,#0x42]` (0x001E84DC)
    u8  pad_043[0x3D];
    u32 handle_080;                 // +0x80: `ldr r0,[r4,#0x80]` (0x001E88F4)
    u32 handle_084;                 // +0x84: `ldr r0,[r4,#0x84]` (0x001E8844)
    u32 handle_088;                 // +0x88: `ldr r0,[r4,#0x88]` (0x001E8888)
    u8  pad_08c[0x04];
    f32 matrix_090[12];             // +0x90: `vldmia sl,{s0..s11}` (0x001E87F0)
    f32 matrix_0c0[12];             // +0xC0: `add sl,r4,#0xc0` (0x001E8938)
    f32 matrix_0f0[12];             // +0xF0: `add ip,r4,#0xf0` (0x001E8858)
    f32 matrix_120[12];             // +0x120: `add ip,r4,#0x120` (0x001E889C)
    f32 matrix_150[12];             // +0x150: `add ip,r4,#0x150` (0x001E8B94)
    u32 handle_180;                 // +0x180: `ldr r0,[r4,#0x180]` (0x001E8A08)
    u32 handle_184;                 // +0x184: `ldr r1,[r4,#0x184]` (0x001E88CC)
    u32 handle_188;                 // +0x188: `ldr r1,[r4,#0x188]` (0x001E8A34)
    s32 flag_18c;                   // +0x18C: `ldr r1,[r4,#0x18c]` (0x001E89D0)
    u8  pad_190[0x04];
};
static_assert(offsetof(TalkTargetEntry, active_000) == 0x000);
static_assert(offsetof(TalkTargetEntry, kind_00c) == 0x00C);
static_assert(offsetof(TalkTargetEntry, type_014) == 0x014);
static_assert(offsetof(TalkTargetEntry, frame_028) == 0x028);
static_assert(offsetof(TalkTargetEntry, flag_042) == 0x042);
static_assert(offsetof(TalkTargetEntry, handle_080) == 0x080);
static_assert(offsetof(TalkTargetEntry, handle_084) == 0x084);
static_assert(offsetof(TalkTargetEntry, handle_088) == 0x088);
static_assert(offsetof(TalkTargetEntry, matrix_090) == 0x090);
static_assert(offsetof(TalkTargetEntry, matrix_0c0) == 0x0C0);
static_assert(offsetof(TalkTargetEntry, matrix_0f0) == 0x0F0);
static_assert(offsetof(TalkTargetEntry, matrix_120) == 0x120);
static_assert(offsetof(TalkTargetEntry, matrix_150) == 0x150);
static_assert(offsetof(TalkTargetEntry, handle_180) == 0x180);
static_assert(offsetof(TalkTargetEntry, handle_184) == 0x184);
static_assert(offsetof(TalkTargetEntry, handle_188) == 0x188);
static_assert(offsetof(TalkTargetEntry, flag_18c) == 0x18C);
static_assert(sizeof(TalkTargetEntry) == 0x194);

/** 56-byte animation row behind 0x00447E58.  The selected index at
 *  `TalkWork::selected_1cc` is scaled by 7*8 = 56 (`rsb r0,r2,r2,lsl #3` /
 *  `add r0,r1,r0,lsl #3`, 0x001E8F6C..0x001E8F74); +0x1C/+0x20 are the two
 *  position words loaded by `ldm r1,{r1,r2}` and +0x24 the trailing word. */
struct TalkAnimRow {
    u8  pad_00[0x1C];
    f32 field_1c;                   // +0x1C
    f32 field_20;                   // +0x20
    u32 field_24;                   // +0x24: `ldr r0,[r0,#0x24]`
    u8  pad_28[0x10];               // stride is 0x38 (`lsl #3` after 7*index)
};
static_assert(offsetof(TalkAnimRow, field_1c) == 0x1C);
static_assert(offsetof(TalkAnimRow, field_20) == 0x20);
static_assert(offsetof(TalkAnimRow, field_24) == 0x24);
static_assert(sizeof(TalkAnimRow) == 0x38);

/** Renderer pointed to by `TalkWork+0x04`.  The overlay reads the model
 *  handles at +0x18/+0x20/+0x4C/+0x60/+0x68/+0x74/+0x88
 *  (`ldr r0,[r0,#4]; ldr r1,[r0,#0x60]`, 0x001E8750..0x001E8754). */
struct TalkRenderer {
    u8  pad_00[0x18];
    u32 handle_18;                  // +0x18
    u32 handle_20;                  // +0x20
    u8  pad_24[0x4c - 0x24];
    u32 handle_4c;                  // +0x4C
    u8  pad_50[0x60 - 0x50];
    u32 handle_60;                  // +0x60
    u32 handle_68;                  // +0x68
    u8  pad_6c[0x74 - 0x6C];
    u32 handle_74;                  // +0x74
    u8  pad_78[0x88 - 0x78];
    u32 handle_88;                  // +0x88
};

/** Root of the target table at 0x00447A78.  The record array begins right
 *  after the 0x1D0-byte header (record 0 is reached with `+0x1D0`). */
struct TalkWork {
    u8  pad_000[0x04];
    TalkRenderer* renderer_04;      // +0x04: `ldr r0,[r0,#4]` (0x001E8750)
    u8  pad_08[0x16 - 0x08];
    u8  field_16;                   // +0x16: `ldrb r0,[r6,#0x16]` (0x001E8F34)
    u8  pad_17[0x20 - 0x17];
    u8  field_20;                   // +0x20: `ldrb r0,[r6,#0x20]` (0x001E9048)
    u8  pad_21[0x24 - 0x21];
    f32 field_24;                   // +0x24: `vldmia r6,{s20,s21}` (0x001E9090)
    f32 field_28;                   // +0x28
    f32 field_2c;                   // +0x2C: `vldr s19,[r6,#0x2c]` (0x001E9084)
    u8  pad_30[0x3c - 0x30];
    u8  field_3c[0x4c - 0x3c];      // +0x3C..+0x4B: 0x0025A434 object head
    s32 mode_4c;                    // +0x4C: `str r0,[r6,#0x4c]` (0x001E8F54)
    u8  pad_50[0x98 - 0x50];
    f32 field_98[2];                // +0x98: `stm r3,{r1,r2}` (0x001E8F90)
    u32 field_a0[3];                // +0xA0: `stm r3,{r0,r1,r2}` (0x001E8F94)
    u32 field_ac;                   // +0xAC: `str r0,[r6,#0xac]` (0x001E8FA0)
    f32 field_b0;                   // +0xB0: `vldr s1,[r4,#0x74]` (0x001E909C)
    u8  pad_b4[0x180 - 0xB4];
    s32 field_180;                  // +0x180: `ldr r0,[r4,#0x180]` (0x001E8FC4)
    u8  pad_184[0x1bc - 0x184];
    f32 field_1bc;                  // +0x1BC: `vstr s16,[r4,#0x180]` @0x001E8FB4
    u8  pad_1c0[0x1cc - 0x1C0];
    s32 selected_1cc;               // +0x1CC: `ldr r2,[r6,#0x1cc]` (0x001E8F5C)
    TalkTargetEntry entries[0x80];  // +0x1D0, stride 0x194
};
static_assert(offsetof(TalkWork, renderer_04) == 0x04);
static_assert(offsetof(TalkWork, field_16) == 0x16);
static_assert(offsetof(TalkWork, field_20) == 0x20);
static_assert(offsetof(TalkWork, field_24) == 0x24);
static_assert(offsetof(TalkWork, field_2c) == 0x2C);
static_assert(offsetof(TalkWork, mode_4c) == 0x4C);
static_assert(offsetof(TalkWork, field_b0) == 0xB0);
static_assert(offsetof(TalkWork, field_98) == 0x98);
static_assert(offsetof(TalkWork, field_a0) == 0xA0);
static_assert(offsetof(TalkWork, field_ac) == 0xAC);
static_assert(offsetof(TalkWork, field_180) == 0x180);
static_assert(offsetof(TalkWork, field_1bc) == 0x1BC);
static_assert(offsetof(TalkWork, selected_1cc) == 0x1CC);
static_assert(offsetof(TalkWork, entries) == 0x1D0);

/** 16-byte entries of the sine/cos palette at 0x00407FC0.  The overlay indexes
 *  it with `add r2,r3,r2,lsl #4` after masking the byte index
 *  (0x001E913C..0x001E9170) and reads the first two floats. */
struct UiColorEntry {
    f32 r;                          // +0x00: `vldr s6,[r2]` (0x001E9174)
    f32 g;                          // +0x04: `vldr s2,[r2,#4]` (0x001E9198)
    f32 b;                          // +0x08: `vldr s8,[r2,#8]` (0x001E9188)
    f32 a;                          // +0x0C: `vldr s10,[r2,#0xc]` (0x001E919C)
};
static_assert(sizeof(UiColorEntry) == 0x10);

// ---------------------------------------------------------------------------
// 0x00243E8C: effect-menu option-row renderer (effMenu.cpp)
// ---------------------------------------------------------------------------

/** 0x24-byte row item passed in r0.  The callers build it inline
 *  (`add r1,r0,#0x24`, 0x0031E9A4) and pass a 16-byte slot buffer in r1. */
struct EffMenuItemState {
    u8  state;                      // +0x00: `ldrb r0,[r4]` (0x00243ED8)
    u8  pad_01[0x03];
    f32 field_04;                   // +0x04: `vldr s2,[r4,#4]` (0x00243EC8)
    u32 field_08;                   // +0x08: `ldr r1,[r4,#8]` (0x00243F00)
    f32 field_0c;                   // +0x0C: `vldr s0,[r4,#0xc]` (0x00243EDC)
    f32 field_10;                   // +0x10: `vldr s4,[r4,#0x10]` (0x00243F50)
    f32 field_14;                   // +0x14: `vldr s1,[r4,#0x14]` (0x00243EE0)
    f32 field_18;                   // +0x18: `vldmia r3,{s5,s6}` (0x00243F54)
    f32 field_1c;                   // +0x1C
    u32 field_20;                   // +0x20: `ldr r1,[r4,#0x20]` (0x00243F78)
};
static_assert(offsetof(EffMenuItemState, state) == 0x00);
static_assert(offsetof(EffMenuItemState, field_04) == 0x04);
static_assert(offsetof(EffMenuItemState, field_08) == 0x08);
static_assert(offsetof(EffMenuItemState, field_0c) == 0x0C);
static_assert(offsetof(EffMenuItemState, field_10) == 0x10);
static_assert(offsetof(EffMenuItemState, field_14) == 0x14);
static_assert(offsetof(EffMenuItemState, field_18) == 0x18);
static_assert(offsetof(EffMenuItemState, field_1c) == 0x1C);
static_assert(offsetof(EffMenuItemState, field_20) == 0x20);
static_assert(sizeof(EffMenuItemState) == 0x24);

/** 16-byte slot block passed in r1 (`vstmia r1` copy at 0x0024473C and the
 *  final `vstmia r4,{s0..s7}` at 0x0024474C both operate on it). */
struct EffMenuSlot {
    u32 word[4];                    // +0x00..+0x0C
};
static_assert(sizeof(EffMenuSlot) == 0x10);

/** Effect-menu UI object at 0x0044FCA8 / 0x0044F970 (`0x0024DFA4` reset).
 *  `+0x0C` is the current row (`ldr r0,[r3,#0xc]`, 0x002446AC), `+0x10` is
 *  the input flag word (`tst r0,#0x20`, 0x00244580), `+0x14` the row table
 *  (`ldr r3,[r3,#0x14]`, 0x002446B0) and `+0x1C` the user pointer. */
struct AsdUiObject {
    u8  pad_00[0x0C];
    s32 field_0c;                   // +0x0C
    u32 flags_10;                   // +0x10
    u32* table_14;                  // +0x14
    u8  pad_18[0x04];
    u32* user_1c;                   // +0x1C
    u8  pad_20[0x14];
    AsdUiObject* child_34;          // +0x34
};
static_assert(offsetof(AsdUiObject, field_0c) == 0x0C);
static_assert(offsetof(AsdUiObject, flags_10) == 0x10);
static_assert(offsetof(AsdUiObject, table_14) == 0x14);
static_assert(offsetof(AsdUiObject, user_1c) == 0x1C);
static_assert(offsetof(AsdUiObject, child_34) == 0x34);

/** Shared effect-menu work at 0x0044EA80.  `+0x4C` is the input mode
 *  (`ldr r0,[r7,#0x4c]`, 0x00244008), `+0x50` the selected column
 *  (0x00243F18), `+0x54` the sub-column (0x00244334), `+0x58` the page
 *  (0x0024402C), `+0x5C` the packed colour (0x00243F38), `+0x84` the current
 *  value (0x00243F48) and `+0x88..+0x90` the three scaled integers
 *  (0x00244804..0x00244824). */
struct EffMenuWork {
    u8  pad_000[0x09];
    u8  field_09;                   // +0x09: `ldrb r0,[r7,#9]` (0x00243F98)
    u8  pad_0a[0x4c - 0x0A];
    s32 mode_4c;                    // +0x4C: `ldr r0,[r7,#0x4c]` (0x00244008)
    s32 column_50;                  // +0x50: `ldr r3,[r7,#0x50]` (0x00243F18)
    s32 field_54;                   // +0x54: `ldr r0,[r7,#0x54]` (0x00244334)
    s32 page_58;                    // +0x58: `ldr r0,[r7,#0x58]` (0x0024402C)
    u32 color_5c;                   // +0x5C: `str r2,[r7,#0x5c]` (0x00243F38)
    u8  pad_60[0x84 - 0x60];
    f32 value_84;                   // +0x84: `vldr s0,[r7,#0x84]` (0x002440E0)
    s32 field_88;                   // +0x88: `vstr s0,[r4,#0x88]` (0x00244804)
    s32 field_8c;                   // +0x8C
    s32 field_90;                   // +0x90
    u8  pad_94[0xef0 - 0x94];
    AsdUiObject fallback_ef0;       // +0xEF0: `addeq r0,r4,#0xef0` (0x0024484C)
};

/** Effect-menu scene buffer at 0x004D8F40.  The state copied back into the
 *  item lives at +0x350 (eight floats), the trailing word at +0x370 and the
 *  slot block at +0x374.  +0x380 is written from the caller's slot+0x0C. */
struct EffMenuScene {
    u8  pad_000[0x350];
    f32 state_350[8];               // +0x350: `vldmia r1,{s0..s7}` (0x00244748)
    u32 field_370;                  // +0x370: `ldr r0,[r0,#0x370]` (0x00244750)
    u32 slot_374[4];                // +0x374: `ldm r2,{r2,r3,fp,ip}` (0x0024473C)
};
static_assert(offsetof(EffMenuScene, state_350) == 0x350);
static_assert(offsetof(EffMenuScene, field_370) == 0x370);
static_assert(offsetof(EffMenuScene, slot_374) == 0x374);
static_assert(sizeof(EffMenuScene) == 0x384);

/** Animation constants at 0x004D92B4.  `+0x08`/`+0x0C` are the two end
 *  positions used by the slide animation (`vldr s0,[r8,#8]`,
 *  0x0024433C) and `&+0x08` is the sentinel compared against the sprite
 *  table (`ldr r2,=0x004d92bc; cmp r0,r2`, 0x002446A8..0x002446C0). */
struct EffMenuAnimConfig {
    u8  pad_00[0x08];
    f32 field_08;                   // +0x08
    f32 field_0c;                   // +0x0C
};
static_assert(offsetof(EffMenuAnimConfig, field_08) == 0x08);
static_assert(offsetof(EffMenuAnimConfig, field_0c) == 0x0C);

/** Scroll/value state at 0x004D9290.  `+0x00` is the active column
 *  (`ldrb r1,[r0]`, 0x002446EC), `+0x10` the animation phase and `+0x18` the
 *  displayed ratio (0x00244700..0x00244728). */
struct EffMenuScroll {
    u8  column;                     // +0x00
    u8  pad_01[0x0F];
    f32 field_10;                   // +0x10
    f32 field_14;                   // +0x14
    f32 field_18;                   // +0x18
};
static_assert(offsetof(EffMenuScroll, column) == 0x00);
static_assert(offsetof(EffMenuScroll, field_10) == 0x10);
static_assert(offsetof(EffMenuScroll, field_18) == 0x18);

// ---------------------------------------------------------------------------
// 0x002F150C: battle command ring
// ---------------------------------------------------------------------------

/** One 0x2C-byte command-row record at work+0x5700.  The loop index is
 *  scaled by 0x2C (`add r1,r0,r0,lsl #1` / `add r0,r1,r0,lsl #3`,
 *  0x002F1784..0x002F1788); +0x60 is the linked skill/unit id
 *  (`ldrh r0,[sl,#0x60]`, 0x002F17A0), +0x78 the visible byte
 *  (`ldrb r0,[sl,#0x78]`, 0x002F1794) and +0x88 the selected byte
 *  (`ldrb r0,[sl,#0x88]`, 0x002F1868). */
struct BattleCommandEntry {
    u8  pad_00[0x60];
    u16 id_60;                      // +0x60
    u8  pad_62[0x16];
    u8  visible_78;                 // +0x78
    u8  pad_79[0x0F];
    u8  selected_88;                // +0x88
    u8  pad_89[0x03];
};
static_assert(offsetof(BattleCommandEntry, id_60) == 0x60);
static_assert(offsetof(BattleCommandEntry, visible_78) == 0x78);
static_assert(offsetof(BattleCommandEntry, selected_88) == 0x88);
static_assert(sizeof(BattleCommandEntry) == 0x8C);

/** Battle command work view.  The two anchor sprites at +0x11A0 and +0x12B8
 *  are queried through 0x002BEF7C/0x002BEF70 (0x002F1548..0x002F1558); the
 *  cursor lives at +0x340C (0x002F1C74); the five party ids at +0x34F8
 *  (`ldrh r0,[r0,#0xf8]`, 0x002F19F8); the row ids at +0x3480
 *  (`ldrsh r4,[r0,r4]`, 0x002F22E8); the row count at +0x5758
 *  (`ldr r0,[r0]`, 0x002F1760) and the records at +0x5700. */
struct BattleCommandWork {
    u8  pad_0000[0x11A0];
    UiAnimSprite sprite_11a0;       // +0x11A0
    u8  pad_122c[0x124c - 0x122C];
    f32 alpha_124c;                 // +0x124C: `vldr s0,[r0,#0x20]` (0x002F1878)
    u8  pad_1250[0x12B8 - 0x1250];
    UiAnimSprite sprite_12b8;       // +0x12B8
    u8  pad_1344[0x340C - 0x1344];
    UiListCursor* cursor_340c;      // +0x340C: `ldr r0,[r5]` (0x002F1C74)
    u8  pad_3410[0x3480 - 0x3410];
    s16 row_ids_3480[0x3C];         // +0x3480: `ldrsh r4,[r0,r4]` (0x002F22E8)
    u16 party_ids_34f8[5];          // +0x34F8: `ldrh r0,[r0,#0xf8]` (0x002F19F8)
    u8  pad_3502[0x5700 - 0x3502];
    // The listing scales the record slot by 0x2C (`add r5,sb,r0,lsl #2`,
    // 0x002F178C) while the fields it reads sit at +0x60/+0x78/+0x88 of that
    // slot; the view therefore exposes raw bytes and the cpp computes the
    // slot pointer explicitly rather than pretending the records are 0x2C.
    u8  entries_5700[0x58];         // +0x5700..+0x5757
    s32 count_5758;                 // +0x5758: `ldr r0,[r0]` (0x002F1760)
    u8  pad_575c[0x575f - 0x575C];
    u8  variant_575f;               // +0x575F: `ldrb r0,[fp,#0x5f]` (0x002F17B4)
};
static_assert(offsetof(BattleCommandWork, sprite_11a0) == 0x11A0);
static_assert(offsetof(BattleCommandWork, alpha_124c) == 0x124C);
static_assert(offsetof(BattleCommandWork, sprite_12b8) == 0x12B8);
static_assert(offsetof(BattleCommandWork, cursor_340c) == 0x340C);
static_assert(offsetof(BattleCommandWork, row_ids_3480) == 0x3480);
static_assert(offsetof(BattleCommandWork, party_ids_34f8) == 0x34F8);
static_assert(offsetof(BattleCommandWork, entries_5700) == 0x5700);
static_assert(offsetof(BattleCommandWork, count_5758) == 0x5758);
static_assert(offsetof(BattleCommandWork, variant_575f) == 0x575F);

// ---------------------------------------------------------------------------
// 0x003D7630: battle-result panel state machine
// ---------------------------------------------------------------------------

/** Animation constants at 0x004342C8.  `+0x04`/`+0x08` scale the shake
 *  (0x003D78C8..0x003D78E0), `+0x0C/+0x10` are the interpolation source and
 *  duration (0x003D7DA4), `+0x14` the slide distance (0x003D7DAC) and
 *  `+0x18..+0x24` are the four phase durations (0x003D7E2C..0x003D7F34). */
struct ResultAnimConfig {
    u32 field_00;                   // +0x00
    f32 field_04;                   // +0x04
    f32 field_08;                   // +0x08
    s32 field_0c;                   // +0x0C
    s32 field_10;                   // +0x10
    f32 field_14;                   // +0x14
    s32 field_18;                   // +0x18
    s32 field_1c;                   // +0x1C
    s32 field_20;                   // +0x20
    s32 field_24;                   // +0x24
};
static_assert(offsetof(ResultAnimConfig, field_04) == 0x04);
static_assert(offsetof(ResultAnimConfig, field_0c) == 0x0C);
static_assert(offsetof(ResultAnimConfig, field_14) == 0x14);
static_assert(offsetof(ResultAnimConfig, field_24) == 0x24);

/** Result-panel work at the pointer stored in 0x004342C8 (+0x00 is the
 *  pointer consumed by 0x001E4928).  The state byte at +0x28 selects the
 *  prologue path (`ldr r0,[r0,#0x28]`, 0x003D7640); +0x634 is the animation
 *  bit field (every `tst r0,#...` from 0x003D7664 onward); +0x638..+0x720
 *  are the per-phase timers and +0x728..+0x840 the second group. */
struct ResultWork {
    f32 pos_00[3];                  // +0x00..+0x08: `vstmia r4,{s2,s3}` (0x003D7958)
    f32 pos_0c[3];                  // +0x0C..+0x14: `vldmia r0,{s0..s5}` (0x003D790C)
    f32 pos_18[3];                  // +0x18..+0x20: `ldm r1,{r1,r2}` / `ldr r3,[r4,#0x20]` (0x003D7964)
    u8  pad_24[0x04];
    s32 state_28;                   // +0x28: `ldr r0,[r0,#0x28]` (0x003D7640)
    u8  pad_2c[0x30 - 0x2C];
    u8  block_30[0x14];             // +0x30..+0x44: 0x002580A8 / 0x0023ABC0
    u8  block_44[0x14];             // +0x44..+0x58: 0x002580A8 / 0x0023ABC0
    u8  effect_58[0x528];           // +0x58: passed to 0x003D5D1C (0x003D8594)
    f32 scale_580[3];               // +0x580: `vldr s2,[r0]` (0x003D80F4)
    u8  pad_58c[0x634 - 0x58C];
    u32 flags_634;                  // +0x634: first `ldr r0,[r4,#0x634]` (0x003D7664)
    s32 limit_638;                  // +0x638: `ldr r1,[r4,#0x638]` (0x003D7698)
    u8  pad_63c[0x64c - 0x63C];
    s32 mode_64c;                   // +0x64C: `ldr r0,[r4,#0x64c]` (0x003D76C8)
    s32 limit_650;                  // +0x650
    s32 timer_654;                  // +0x654
    u8  pad_658[0x664 - 0x658];
    s32 field_664;                  // +0x664
    s32 field_668;                  // +0x668
    s32 field_66c;                  // +0x66C
    u8  pad_670[0x674 - 0x670];
    s32 field_674;                  // +0x674
    s32 field_678;                  // +0x678
    s32 field_67c;                  // +0x67C
    s32 limit_680;                  // +0x680
    s32 timer_684;                  // +0x684
    u8  pad_688[0x694 - 0x688];
    s32 field_694;                  // +0x694
    u8  pad_698[0x6a0 - 0x698];
    s32 timer_6a0;                  // +0x6A0
    u8  pad_6a4[0x6ac - 0x6A4];
    s32 limit_6ac;                  // +0x6AC
    s32 timer_6b0;                  // +0x6B0
    s32 field_6b4;                  // +0x6B4
    u8  pad_6b8[0x6d8 - 0x6B8];
    s32 limit_6d8;                  // +0x6D8
    s32 timer_6dc;                  // +0x6DC
    s32 field_6e0;                  // +0x6E0
    u8  pad_6e4[0x6f0 - 0x6E4];
    s32 field_6f0;                  // +0x6F0
    s32 field_6f8;                  // +0x6F8
    u8  pad_6fc[0x714 - 0x6FC];
    s32 limit_714;                  // +0x714
    s32 timer_718;                  // +0x718
    u8  pad_71c[0x728 - 0x71C];
    s32 field_728;                  // +0x728
    s32 field_72c;                  // +0x72C
    u8  pad_730[0x7a4 - 0x730];
    s32 field_7a4;                  // +0x7A4
    u8  pad_7a8[0x7bc - 0x7A8];
    s32 field_7bc;                  // +0x7BC
    u8  pad_7c0[0x7e0 - 0x7C0];
    s32 field_7e0;                  // +0x7E0
    u8  pad_7e4[0x810 - 0x7E4];
    s32 field_810;                  // +0x810
    u8  pad_814[0x840 - 0x814];
    s32 field_840;                  // +0x840
};
static_assert(offsetof(ResultWork, pos_0c) == 0x0C);
static_assert(offsetof(ResultWork, state_28) == 0x28);
static_assert(offsetof(ResultWork, block_30) == 0x30);
static_assert(offsetof(ResultWork, block_44) == 0x44);
static_assert(offsetof(ResultWork, effect_58) == 0x58);
static_assert(offsetof(ResultWork, scale_580) == 0x580);
static_assert(offsetof(ResultWork, flags_634) == 0x634);
static_assert(offsetof(ResultWork, limit_638) == 0x638);
static_assert(offsetof(ResultWork, mode_64c) == 0x64C);
static_assert(offsetof(ResultWork, field_664) == 0x664);

// ---------------------------------------------------------------------------
// Globals reproduced from .data/.bss
// ---------------------------------------------------------------------------

// 0x00447A78 (engine::g_MapIfWork), 0x004474F4 (script_vm::g_ScriptCameraWork),
// 0x0049F91C (engine::g_MapRuntimeState), 0x0044EA80 (engine::g_EffectEditor)
// and 0x004B5D30 (engine::g_MapIfProjectionTables) already have canonical
// owners; ui_scene_extras.cpp views them through the aliases documented there.

extern TalkOverlayFlags g_TalkOverlayFlags;    // 0x0049FB1C (BSS)
extern EffMenuScene g_EffMenuScene;            // 0x004D8F40 (BSS)
extern EffMenuScroll g_EffMenuScroll;          // 0x004D9290 (BSS)
extern EffMenuAnimConfig g_EffMenuAnimConfig;  // 0x004D92B4 (BSS)
// 0x0044FCA8 (.data image): flags_10 = 0x14 and table_14 = 0x0044F9A8.
extern AsdUiObject g_EffMenuObjectA;
// 0x0044F970 (.data image): table_14 = 0x00463EF0 (flags_10 is zero).
extern AsdUiObject g_EffMenuObjectB;
// 0x004342C8 (.data): { 0, 0.15f, 0.1f, 5, 0, 0, -1, 5, -1, 5 }.
extern ResultAnimConfig g_ResultAnim;
extern f32 g_ResultOrigin[3];                  // 0x00493530 (.data)
// 0x00447E58 (.data pointer) -> 0x004BB7B0 (56-byte rows).
extern TalkAnimRow* g_TalkAnimRows;
// 0x00407FC0..0x00408FBF: the non-zero 4096-byte .rodata palette transcribed
// from code.bin (256 rows of four floats; row 0 is {0, 1, ...}).
extern UiColorEntry g_UiColorTable[256];

// ---------------------------------------------------------------------------
// Ledger entry points
// ---------------------------------------------------------------------------

/** Talk-target / model selection overlay.  Ledger name retained:
 *  ui_func_001e83fc (0x001E83FC, 4,380 B). */
void ui_func_001e83fc();

/** Battle-result panel animation state machine.  Ledger name retained:
 *  ui_func_003d7630 (0x003D7630, 4,308 B). */
s32 ui_func_003d7630(ResultWork* work, s32 frame);

/** Effect-menu option-row renderer (effMenu.cpp).  Ledger name retained:
 *  ui_func_00243e8c (0x00243E8C, 4,216 B). */
s32 ui_func_00243e8c(EffMenuItemState* item, EffMenuSlot* slot, s32 count);

/** Battle command ring.  Ledger name retained: ui_func_002f150c
 *  (0x002F150C, 4,204 B). */
void ui_func_002f150c(BattleCommandWork* work);

/** Tail routine inside the 0x003D7630 ledger span
 *  (0x003D86C0..0x003D8700): arms the 0x800 shake bit and seeds the three
 *  vectors.  Exposed for callers/tests even though this build never reaches
 *  it. */
void Result_BeginShake(ResultWork* work, s32 a, s32 b, f32 value);

/** Second routine inside the 0x001E83FC ledger span
 *  (0x001E9414..0x001E9518): gates on `[g_MapMainWork]+0x24`, runs the two
 *  mode updates and returns 0.  Exposed for callers/tests. */
s32 TalkOverlay_PollMode();

} // namespace smt4::ui
