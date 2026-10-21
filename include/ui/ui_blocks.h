#pragma once
#include <cstddef>
#include "types.h"

/**
 * UI runtime blocks A: the debug value list at 0x001FE590 and the battle
 * command panel at 0x002ED5D0.
 *
 * All structures are opaque views.  Only offsets with a proving access in the
 * corresponding ARM listing are named; the comments carry the instruction.
 */

namespace smt4::ui {

// ---------------------------------------------------------------------------
// 0x001FE590: debug value list
// ---------------------------------------------------------------------------

struct DebugValueEntry;

/**
 * One linked-list node (`r5` in the 0x001FEA6C loop).
 * +0x00 id, +0x08 entry, +0x18 next (`ldr r5,[r5,#0x18]`, 0x001FEE10).
 */
struct DebugListNode {
    u32 id;                             // +0x00: `ldr r0,[r5]` (0x001FEA78)
    u8  pad_004[4];
    DebugValueEntry* entry;             // +0x08: `ldr r7,[r5,#8]` (0x001FEAA4)
    u8  pad_00c[0x0C];
    DebugListNode* next;                // +0x18: `ldr r5,[r5,#0x18]`
                                        //   (0x001FEE10)
};
static_assert(offsetof(DebugListNode, id) == 0x00);
static_assert(offsetof(DebugListNode, entry) == 0x08);
static_assert(offsetof(DebugListNode, next) == 0x18);

/**
 * One value entry.  The label is at +0x06, the alternate/formatted text buffer
 * at +0x106 (both 0x100 bytes), then the integer, float, minimum and maximum
 * slots used by the scroll paths.
 */
struct DebugValueEntry {
    u8  pad_000[4];
    u8  type;                           // +0x04: `ldrb r0,[r7,#4]` (0x001FEAC0)
    u8  hex;                            // +0x05: `ldrb r0,[r7,#5]` (0x001FEBC8)
    char label[0x100];                  // +0x006: `add r2,r7,#6`
                                        //   (0x001FEAB0)
    char text[0x100];                   // +0x106: `add r2,r7,#0x100;
                                        //   add r2,r2,#6` (0x001FEAE4)
    s32 int_value;                      // +0x208: `ldr r0,[r7,#0x208]`
                                        //   (0x001FEB90)
    f32 float_value;                    // +0x20C: `vldr s0,[r7,#0x20c]`
                                        //   (0x001FEC40)
    s32 min_value;                      // +0x210: `ldr r1,[r5,#0x210]`
                                        //   (0x001FF15C)
    s32 max_value;                      // +0x214: `ldr r1,[r5,#0x214]`
                                        //   (0x001FEFC0)
    u32 user;                           // +0x218: `ldr r2,[r0,#0x218]`
                                        //   (0x001FF2D8)
    void (*callback)(const void*);      // +0x21C: `ldr r1,[r0,#0x21c]`
                                        //   (0x001FF2A8)
};
static_assert(offsetof(DebugValueEntry, type) == 0x004);
static_assert(offsetof(DebugValueEntry, hex) == 0x005);
static_assert(offsetof(DebugValueEntry, label) == 0x006);
static_assert(offsetof(DebugValueEntry, text) == 0x106);
static_assert(offsetof(DebugValueEntry, int_value) == 0x208);
static_assert(offsetof(DebugValueEntry, float_value) == 0x20C);
static_assert(offsetof(DebugValueEntry, min_value) == 0x210);
static_assert(offsetof(DebugValueEntry, max_value) == 0x214);
static_assert(offsetof(DebugValueEntry, user) == 0x218);
static_assert(offsetof(DebugValueEntry, callback) == 0x21C);
static_assert(sizeof(DebugValueEntry) == 0x220);

/**
 * List cursor object at HUD+0x0C, updated by camp_func_001FF3C4.
 * Only the two words copied back by 0x001FEE54/0x001FEE60 are named.
 */
struct DebugListState {
    u8  pad_000[0x20];
    s32 field_20;                       // +0x20: `ldr r0,[r0,#0x20]`
                                        //   reached as HUD+0x2C
                                        //   (0x001FEE60)
    s32 field_24;                       // +0x24: `ldr r0,[r0,#0x24]`
                                        //   reached as HUD+0x30
                                        //   (0x001FEE54)
};
static_assert(offsetof(DebugListState, field_20) == 0x20);
static_assert(offsetof(DebugListState, field_24) == 0x24);

/**
 * Debug HUD work returned by 0x002C0AC8 for the scene handle.
 * `x/y/width/height` are the panel rectangle; `char_width` and `line_height`
 * size the formatted columns and rows.
 */
struct DebugHudWork {
    DebugListNode* list;                // +0x00: `ldr r5,[r4]` (0x001FEA6C)
    u8  pad_004[8];
    DebugListState list_state;          // +0x0C: `add r0,r4,#0xc`
                                        //   (0x001FEE3C)
    s32 state;                          // +0x34: `ldr r0,[r0,#0x34]`
                                        //   (0x001FE5A8)
    u32 flags;                          // +0x38: `ldr r0,[r4,#0x38]`
                                        //   (0x001FE634)
    u8  palette;                        // +0x3C: `ldrb r0,[r4,#0x3c]`
                                        //   (0x001FE6EC)
    u8  enabled;                        // +0x3D: `ldrb r0,[r4,#0x3d]`
                                        //   (0x001FE5DC)
    u8  pad_03e[2];
    s32 countdown;                      // +0x40: `ldr r0,[r4,#0x40]`
                                        //   (0x001FEE28)
    u8  pad_044[4];
    f32 x;                              // +0x48: `vldr s0,[r4,#0x48]`
                                        //   (0x001FE668)
    f32 y;                              // +0x4C: `vldr s1,[r4,#0x4c]`
                                        //   (0x001FE6B0)
    f32 width;                          // +0x50: `vldr s0,[r4,#0x50]`
                                        //   (0x001FE764)
    f32 height;                         // +0x54: `vldr s0,[r4,#0x54]`
                                        //   (0x001FE88C)
    s32 char_width;                     // +0x58: `ldr r1,[r4,#0x58]`
                                        //   (0x001FEB00)
    s32 line_height;                    // +0x5C: `ldr r0,[r4,#0x5c]`
                                        //   (0x001FEA4C)
    s32 scroll;                         // +0x60: `ldr r0,[r4,#0x60]`
                                        //   (0x001FEE60)
    s32 first_id;                       // +0x64: `ldr r1,[r4,#0x64]`
                                        //   (0x001FEA7C)
    s32 visible_count;                  // +0x68: `ldr r2,[r4,#0x68]`
                                        //   (0x001FEA8C)
    s32 active;                         // +0x6C: `ldr r0,[r4,#0x6c]`
                                        //   (0x001FE628)
    u8  pad_070[4];
    void (*frame_cb)(s32 arg);          // +0x74: `ldr r1,[r4,#0x74]`
                                        //   (0x001FF370)
    s32 frame_arg;                      // +0x78: `ldr r0,[r4,#0x78]`
                                        //   (0x001FF380)
    void (*draw_text_cb)(f32* x, f32* y, const char* text);
                                        // +0x7C: `blx r3` with r0=&x,
                                        //   r1=&y, r2=text (0x001FEABC)
    s32 (*measure_text_cb)(const char* text);
                                        // +0x80: `blx r1` with r0=buffer,
                                        //   result used as width (0x001FEB00)
    u8  pad_084[8];
    char text[0x100];                   // +0x8C: `add r1,r4,#0x8c`
                                        //   (0x001FE924)
};
static_assert(offsetof(DebugHudWork, list) == 0x00);
static_assert(offsetof(DebugHudWork, list_state) == 0x0C);
static_assert(offsetof(DebugHudWork, state) == 0x34);
static_assert(offsetof(DebugHudWork, flags) == 0x38);
static_assert(offsetof(DebugHudWork, palette) == 0x3C);
static_assert(offsetof(DebugHudWork, enabled) == 0x3D);
static_assert(offsetof(DebugHudWork, countdown) == 0x40);
static_assert(offsetof(DebugHudWork, x) == 0x48);
static_assert(offsetof(DebugHudWork, y) == 0x4C);
static_assert(offsetof(DebugHudWork, width) == 0x50);
static_assert(offsetof(DebugHudWork, height) == 0x54);
static_assert(offsetof(DebugHudWork, char_width) == 0x58);
static_assert(offsetof(DebugHudWork, line_height) == 0x5C);
static_assert(offsetof(DebugHudWork, scroll) == 0x60);
static_assert(offsetof(DebugHudWork, first_id) == 0x64);
static_assert(offsetof(DebugHudWork, visible_count) == 0x68);
static_assert(offsetof(DebugHudWork, active) == 0x6C);
static_assert(offsetof(DebugHudWork, frame_cb) == 0x74);
static_assert(offsetof(DebugHudWork, frame_arg) == 0x78);
static_assert(offsetof(DebugHudWork, draw_text_cb) == 0x7C);
static_assert(offsetof(DebugHudWork, measure_text_cb) == 0x80);
static_assert(offsetof(DebugHudWork, text) == 0x8C);

/** 0x00409B60: one 4-colour palette row (`ldr r0,[r5,r0,lsl #4]`). */
struct DebugPalette {
    u32 color[4];                       // +0x00/+0x04/+0x08/+0x0C:
                                        //   `ldr r0,[r0,#0xc]` etc.
                                        //   (0x001FE778, 0x001FE800,
                                        //   0x001FE994)
};
static_assert(sizeof(DebugPalette) == 0x10);

/** 0x00409B60 holds five 16-byte rows; the next data starts at 0x00409BB0. */
extern const DebugPalette g_DebugPalette[5];

// ---------------------------------------------------------------------------
// 0x002ED5D0: battle command panel
// ---------------------------------------------------------------------------

/** One 16-byte 2D layout node returned by 0x002BF6D0. */
struct UiLayoutRect {
    s16 w;                              // +0x00
    s16 h;                              // +0x02
};

/** Layout node view: x/y at +0x08/+0x0A, payload at +0x0C. */
struct UiLayoutNode {
    u8  pad_000[8];
    s16 x;                              // +0x08
    s16 y;                              // +0x0A: `ldrsh r1,[r0,#0xa]`
                                        //   (0x002ED7A4)
    const UiLayoutRect* rect;           // +0x0C: `ldr r0,[r0,#0xc]`
                                        //   (0x002ED8F4)
};
static_assert(offsetof(UiLayoutNode, y) == 0x0A);
static_assert(offsetof(UiLayoutNode, rect) == 0x0C);

/**
 * Battle command / action panel work passed in r0 and re-fetched through
 * 0x002C0AC8 when the listing needs the scene handle.
 */
struct BattleCommandWork {
    u8  pad_000[4];
    s32 state;                          // +0x04: `ldr r0,[r5,#4]`
                                        //   (0x002ED644)
    s32 substate;                       // +0x08: `ldr r0,[r5,#8]`
                                        //   (0x002ED754)
    void* text_a;                       // +0x0C: `ldr r0,[r5,#0xc]`
                                        //   (0x002ED784)
    void* text_b;                       // +0x10: `ldr r0,[r5,#0x10]`
                                        //   (0x002EDDD4)
    u8  pad_014[4];
    s32 value_a;                        // +0x18: `vldr s0,[r5,#0x18]`
                                        //   (0x002ED82C)
    s32 value_b;                        // +0x1C: `vldr s0,[r5,#0x1c]`
                                        //   (0x002ED848)
    s32 gauge;                          // +0x20: `ldr r3,[r5,#0x20]`
                                        //   (0x002ED660)
};
static_assert(offsetof(BattleCommandWork, state) == 0x04);
static_assert(offsetof(BattleCommandWork, substate) == 0x08);
static_assert(offsetof(BattleCommandWork, text_a) == 0x0C);
static_assert(offsetof(BattleCommandWork, text_b) == 0x10);
static_assert(offsetof(BattleCommandWork, value_a) == 0x18);
static_assert(offsetof(BattleCommandWork, value_b) == 0x1C);
static_assert(offsetof(BattleCommandWork, gauge) == 0x20);

/** 0x0043DC2C: eight icon ids selected by (value_a + index) mod 8. */
extern const u8 g_BattleCommandIcons[8];

// ---------------------------------------------------------------------------
// 0x0036C0A8 / 0x00368CF8: action-panel command emitters
// ---------------------------------------------------------------------------

/**
 * One action panel.  Both emitters walk the same layout; 0x00368CF8 reaches
 * eleven of them through `UiActionSlotTable`, while 0x0036C0A8 receives a
 * single one through `UiActionSlot`.  Only offsets with a proving access in
 * either listing are named.
 */
struct UiActionPanel {
    u8  pad_000[8];
    void* scene;                        // +0x08: `ldr r7,[r0,#8]`
                                        //   (0x0036C140)
    u8  pad_00c[7];
    u8  field_13;                       // +0x13: `ldrb r0,[r0,#0x13]`
                                        //   (0x0036C1B0)
    u32 field_14;                       // +0x14: `ldr r2,[r7,#0x14]`
                                        //   (0x0036C1FC)
    u32 field_18;                       // +0x18: `ldr r1,[r5,#0x18]`
                                        //   (0x0036C1C8)
    u8  pad_01c[8];
    u32 field_24;                       // +0x24: `ldr r0,[r0,#0x24]`
                                        //   (0x0036C0EC)
    u8  pad_028[0x18];
    u8  field_40;                       // +0x40: `add r6,r0,#0x40`
                                        //   (0x0036C0B4)
    u32 field_44;                       // +0x44: `ldr r3,[r6,#4]`
                                        //   (0x0036C2A0)
    u8  pad_048[0x1C];
    u32 field_64;                       // +0x64: `ldr ip,[r6,#0x24]`
                                        //   (0x0036C78C)
    u8  pad_068[0x38];
    u32 field_a0;                       // +0xA0: `ldr r1,[r6,#0x60]`
                                        //   (0x0036C2F8)
    u8  pad_0a4[0x3C];
    u32 field_e0;                       // +0xE0: `ldr r3,[r6,#0xa0]`
                                        //   (0x0036C264)
    u32 field_e4;                       // +0xE4: `ldr r0,[r6,#0xa4]`
                                        //   (0x0036C1E8)
    u8  field_e8;                       // +0xE8: `ldrb r0,[r0,#0xe8]`
                                        //   (0x0036C0B8)
    u8  field_e9;                       // +0xE9: `ldrb r0,[r6,#0xa9]`
                                        //   (0x0036C0C4)
    u8  field_ea;                       // +0xEA: `ldrb r1,[r6,#0xaa]`
                                        //   (0x0036C0BC)
    u8  field_eb;                       // +0xEB: `ldrb r0,[r6,#0xab]`
                                        //   (0x0036C0D8)
    u8  pad_ec[0x14];
    u32 field_100;                      // +0x100: `ldr r2,[r0,#0x100]`
                                        //   (0x0036C13C)
    u32 field_104;                      // +0x104: `ldr r2,[r0,#0x104]`
                                        //   (0x0036C14C)
    u32 field_108;                      // +0x108: `ldr r2,[r0,#0x108]`
                                        //   (0x0036C154)
    u32 field_10c;                      // +0x10C: `ldr r2,[r0,#0x10c]`
                                        //   (0x0036C15C)
    u32 field_110;                      // +0x110: `ldr r2,[r0,#0x110]`
                                        //   (0x0036C164)
    u32 field_114;                      // +0x114: `ldr r2,[r0,#0x114]`
                                        //   (0x0036C16C)
    u32 field_118;                      // +0x118: `ldr r2,[r0,#0x118]`
                                        //   (0x0036C174)
    u32 field_11c;                      // +0x11C: `ldr r2,[r0,#0x11c]`
                                        //   (0x0036C17C)
    u32 field_120;                      // +0x120: `ldr r2,[r0,#0x120]`
                                        //   (0x0036C184)
    u32 field_124;                      // +0x124: `ldr r2,[r0,#0x124]`
                                        //   (0x0036C18C)
    u32 field_128;                      // +0x128: `ldr r0,[r0,#0x128]`
                                        //   (0x0036C194)
    u32 field_12c;                      // +0x12C: `add r3,r0,#0x14`
                                        //   with r0 = panel+0x118
                                        //   (0x0036CAB4)
    u32 field_130;                      // +0x130: `ldr r2,[sl,#0x18]`
                                        //   (0x0036CBE0 with sl=panel+0x118)
    u8  pad_134[0xC];
    u32 field_140;                      // +0x140: `ldr r0,[sl,#0x28]`
                                        //   (0x0036CC40)
    u8  pad_144[0x14];
    u32 field_158;                      // +0x158: `add fp,r0,#0x40`
                                        //   with r0 = panel+0x118
                                        //   (0x0036CAB0)
    u8  pad_15c[0x118];
    u32 field_274;                      // +0x274: `mov r0,#0x274`
                                        //   (0x0036C4E0)
    u32 field_278;                      // +0x278
    u32 field_27c;                      // +0x27C
    u8  pad_280[8];
    u32 rel_288;                        // +0x288: `ldr r0,[r5,#0x288]`
                                        //   (0x0036C594)
    u8  pad_28c[0x14];
    u32 field_2a0;                      // +0x2A0: `ldr r0,[r4,#0x2a0]`
                                        //   (0x0036C230)
    u32 field_2a4;                      // +0x2A4: `ldr r4,[r1,#0x2a4]`
                                        //   (0x0036C134)
    u32 field_2a8;                      // +0x2A8: `ldr r4,[r5,#0x2a8]`
                                        //   (0x0036C484)
    u32 field_2ac;                      // +0x2AC
    u32 field_2b0;                      // +0x2B0: `ldr r0,[r5,#0x2b0]`
                                        //   (0x0036C4B0)
    u32 field_2b4;                      // +0x2B4: `ldr r8,[r5,#0x2b4]`
                                        //   (0x0036C86C)
    u32 field_2b8;                      // +0x2B8: `ldr r4,[r5,#0x2b8]`
                                        //   (0x0036C31C)
    u32 field_2bc;                      // +0x2BC: `ldr r0,[r5,#0x2bc]`
                                        //   (0x0036C580)
    u32 field_2c0;                      // +0x2C0: `ldr r0,[r5,#0x2c0]`
                                        //   (0x0036C588)
    u32 field_2c4;                      // +0x2C4
    u32 field_2c8;                      // +0x2C8: `ldr r8,[r5,#0x2c8]`
                                        //   (0x0036C8B0)
    u32 field_2cc;                      // +0x2CC: `ldr r0,[r5,#0x2cc]`
                                        //   (0x0036CA58)
    u32 field_2d0;                      // +0x2D0: `ldr r4,[r5,#0x2d0]`
                                        //   (0x0036CA8C)
};
static_assert(offsetof(UiActionPanel, scene) == 0x008);
static_assert(offsetof(UiActionPanel, field_13) == 0x013);
static_assert(offsetof(UiActionPanel, field_14) == 0x014);
static_assert(offsetof(UiActionPanel, field_18) == 0x018);
static_assert(offsetof(UiActionPanel, field_24) == 0x024);
static_assert(offsetof(UiActionPanel, field_40) == 0x040);
static_assert(offsetof(UiActionPanel, field_44) == 0x044);
static_assert(offsetof(UiActionPanel, field_64) == 0x064);
static_assert(offsetof(UiActionPanel, field_a0) == 0x0A0);
static_assert(offsetof(UiActionPanel, field_e0) == 0x0E0);
static_assert(offsetof(UiActionPanel, field_e4) == 0x0E4);
static_assert(offsetof(UiActionPanel, field_e8) == 0x0E8);
static_assert(offsetof(UiActionPanel, field_e9) == 0x0E9);
static_assert(offsetof(UiActionPanel, field_ea) == 0x0EA);
static_assert(offsetof(UiActionPanel, field_eb) == 0x0EB);
static_assert(offsetof(UiActionPanel, field_100) == 0x100);
static_assert(offsetof(UiActionPanel, field_104) == 0x104);
static_assert(offsetof(UiActionPanel, field_108) == 0x108);
static_assert(offsetof(UiActionPanel, field_10c) == 0x10C);
static_assert(offsetof(UiActionPanel, field_110) == 0x110);
static_assert(offsetof(UiActionPanel, field_114) == 0x114);
static_assert(offsetof(UiActionPanel, field_118) == 0x118);
static_assert(offsetof(UiActionPanel, field_11c) == 0x11C);
static_assert(offsetof(UiActionPanel, field_120) == 0x120);
static_assert(offsetof(UiActionPanel, field_124) == 0x124);
static_assert(offsetof(UiActionPanel, field_128) == 0x128);
static_assert(offsetof(UiActionPanel, field_12c) == 0x12C);
static_assert(offsetof(UiActionPanel, field_130) == 0x130);
static_assert(offsetof(UiActionPanel, field_140) == 0x140);
static_assert(offsetof(UiActionPanel, field_158) == 0x158);
static_assert(offsetof(UiActionPanel, field_274) == 0x274);
static_assert(offsetof(UiActionPanel, rel_288) == 0x288);
static_assert(offsetof(UiActionPanel, field_2a0) == 0x2A0);
static_assert(offsetof(UiActionPanel, field_2a4) == 0x2A4);
static_assert(offsetof(UiActionPanel, field_2a8) == 0x2A8);
static_assert(offsetof(UiActionPanel, field_2b0) == 0x2B0);
static_assert(offsetof(UiActionPanel, field_2b4) == 0x2B4);
static_assert(offsetof(UiActionPanel, field_2b8) == 0x2B8);
static_assert(offsetof(UiActionPanel, field_2bc) == 0x2BC);
static_assert(offsetof(UiActionPanel, field_2c0) == 0x2C0);
static_assert(offsetof(UiActionPanel, field_2c8) == 0x2C8);
static_assert(offsetof(UiActionPanel, field_2cc) == 0x2CC);
static_assert(offsetof(UiActionPanel, field_2d0) == 0x2D0);

/**
 * Scene object reached through UiActionPanel::scene.
 * +0x00 word tested with 4, +0x14 word carrying the 0x8000/0x1000 bits and
 * +0x68 the signed count.
 */
struct UiActionScene {
    u32 field_00;                       // +0x00: `ldr ip,[ip]`
                                        //   (0x0036C290)
    u8  pad_004[4];
    void* list;                         // +0x08: `ldr ip,[r7,#8]`
                                        //   (0x0036C250)
    u8  pad_00c[8];
    u32 field_14;                       // +0x14: `ldr r2,[r7,#0x14]`
                                        //   (0x0036C1FC)
    u8  pad_018[0x50];
    s32 field_68;                       // +0x68: `ldr r3,[ip,#0x68]`
                                        //   (0x0036C258)
    u8  pad_06c[0xB4];
    u32 field_120;                      // +0x120: `ldr ip,[ip,#0x120]`
                                        //   (0x00368EAC uses [ip] after
                                        //   `ldr ip,[r6,#8]`)
};
static_assert(offsetof(UiActionScene, field_00) == 0x00);
static_assert(offsetof(UiActionScene, field_14) == 0x14);
static_assert(offsetof(UiActionScene, field_68) == 0x68);

/** The 0x288-relative list record, reached from UiActionPanel::rel_288. */
struct UiActionList {
    u32 flags;                          // +0x00: `ldr ip,[ip]`
                                        //   (0x0036C290)
    u32 field_04;                       // +0x04: `ldr r1,[sb,#4]`
                                        //   (0x0036C5FC)
    u32 field_08;                       // +0x08: `ldr r2,[sb,#8]`
    u32 field_0c;                       // +0x0C: `ldr r3,[sb,#0xc]`
    u32 field_10;                       // +0x10: `ldr ip,[sb,#0x10]`
    u8  field_14;                       // +0x14: `ldrb ip,[sb,#0x14]`
    u8  pad_015[3];
    u32 field_18;                       // +0x18: `ldr ip,[ip,#0x18]`
                                        //   (0x0036C2A0 uses scene+8)
    u8  pad_01c[0x4C];
    s32 field_68;                       // +0x68: `ldr r3,[ip,#0x68]`
                                        //   (0x0036C258)
    u8  pad_06c[0x4C];
    u32 field_b8;                       // +0xB8: `ldr ip,[ip,#0xb8]`
                                        //   (0x0036C79C)
    u8  pad_0bc[0x2C];
    u32 field_e8;                       // +0xE8: `ldr r0,[r0,#0xe8]`
                                        //   (shape placeholder)
};
static_assert(offsetof(UiActionList, flags) == 0x00);
static_assert(offsetof(UiActionList, field_04) == 0x04);
static_assert(offsetof(UiActionList, field_68) == 0x68);
static_assert(offsetof(UiActionList, field_b8) == 0xB8);

/** The second argument of 0x0036C0A8: `ldr r1,[r2,#8]` (0x0036C0F4). */
struct UiActionSlot {
    u8  pad_000[8];
    UiActionPanel* panel;               // +0x08
};
static_assert(offsetof(UiActionSlot, panel) == 0x08);

/**
 * The second argument of 0x00368CF8.  Each slot is a distinct panel component
 * selected by the corresponding 0x0036C0A8 path.
 */
struct UiActionSlotTable {
    u8  pad_000[0x28];
    UiActionPanel* actor;               // +0x28: `ldr r1,[r8,#0x28]`
                                        //   (0x00368D34)
    UiActionPanel* field_2c;            // +0x2C: `ldr r1,[r8,#0x2c]`
                                        //   (0x00368DD8)
    UiActionPanel* field_30;            // +0x30: `ldr r1,[r8,#0x30]`
                                        //   (0x003694C4)
    UiActionPanel* field_34;            // +0x34: `ldr r0,[r8,#0x34]`
                                        //   (0x00368F34)
    UiActionPanel* field_38;            // +0x38: `ldr r2,[r8,#0x38]`
                                        //   (0x003690A4)
    UiActionPanel* field_3c;            // +0x3C: `ldr sl,[r8,#0x3c]`
                                        //   (0x0036910C)
    UiActionPanel* field_40;            // +0x40: `ldr r1,[r8,#0x40]`
                                        //   (0x003691D4)
    UiActionPanel* field_44;            // +0x44: `ldr r0,[r8,#0x44]`
                                        //   (0x003691D0)
    UiActionPanel* field_48;            // +0x48: `ldr r1,[r8,#0x48]`
                                        //   (0x00369510)
    UiActionPanel* field_4c;            // +0x4C: `ldr r2,[r8,#0x4c]`
                                        //   (0x0036967C)
    UiActionPanel* field_50;            // +0x50: `ldr r0,[r8,#0x50]`
                                        //   (0x003696C4)
};
static_assert(offsetof(UiActionSlotTable, actor) == 0x28);
static_assert(offsetof(UiActionSlotTable, field_2c) == 0x2C);
static_assert(offsetof(UiActionSlotTable, field_30) == 0x30);
static_assert(offsetof(UiActionSlotTable, field_34) == 0x34);
static_assert(offsetof(UiActionSlotTable, field_38) == 0x38);
static_assert(offsetof(UiActionSlotTable, field_3c) == 0x3C);
static_assert(offsetof(UiActionSlotTable, field_40) == 0x40);
static_assert(offsetof(UiActionSlotTable, field_44) == 0x44);
static_assert(offsetof(UiActionSlotTable, field_48) == 0x48);
static_assert(offsetof(UiActionSlotTable, field_4c) == 0x4C);
static_assert(offsetof(UiActionSlotTable, field_50) == 0x50);

/**
 * 0x00472088: per-panel animation/dirty flags.  Byte members are read with
 * `ldrb`/`ldrsb`; +0x08 is read as a word (`ldr r1,[sb]`, 0x0036CB38).
 */
struct UiPanelFlags {
    u8  field_00;                       // +0x00: `ldrb r0,[r2]`
                                        //   (0x0036CC4C)
    u8  field_01;                       // +0x01: `ldrb r2,[r7]`
                                        //   (0x0036CAC4)
    u8  field_02;                       // +0x02: `ldrsbeq r1,[r8]`
                                        //   (0x0036CC0C)
    u8  field_03;                       // +0x03: `ldrsbeq r2,[ip]`
                                        //   (0x0036CAD8)
    u8  field_04;                       // +0x04: `ldrb r6,[r5]`
                                        //   (0x0036CBB0)
    u8  field_05;                       // +0x05: `ldrsbeq r0,[r1]`
                                        //   (0x0036CB0C)
    u8  field_06;                       // +0x06: `ldrb r0,[sl]`
                                        //   (0x0036C3D4)
    u8  field_07;                       // +0x07: `ldrb r2,[r2]`
                                        //   (0x0036CB3C)
    u32 field_08;                       // +0x08: `ldr r1,[sb]`
                                        //   (0x0036CB38)
};
static_assert(offsetof(UiPanelFlags, field_00) == 0x00);
static_assert(offsetof(UiPanelFlags, field_01) == 0x01);
static_assert(offsetof(UiPanelFlags, field_02) == 0x02);
static_assert(offsetof(UiPanelFlags, field_03) == 0x03);
static_assert(offsetof(UiPanelFlags, field_04) == 0x04);
static_assert(offsetof(UiPanelFlags, field_05) == 0x05);
static_assert(offsetof(UiPanelFlags, field_06) == 0x06);
static_assert(offsetof(UiPanelFlags, field_07) == 0x07);
static_assert(offsetof(UiPanelFlags, field_08) == 0x08);
static_assert(sizeof(UiPanelFlags) == 0x0C);

/** 0x004720B8: 0x28-byte state block copied into the command stream. */
struct UiPanelShader {
    u8  pad_000[0x10];
    u32 field_10;                       // +0x10: `strne r3,[r0,#0x10]`
                                        //   (0x0036CD58)
    u8  pad_014[4];
    u32 field_18;                       // +0x18: `str r3,[r0,#0x18]`
                                        //   (0x0036CDD4)
    u32 field_1c;                       // +0x1C: `str r1,[r0,#0x1c]`
                                        //   (0x0036CCD8)
    u32 field_20;                       // +0x20: `str r1,[r0,#0x20]`
                                        //   (0x0036CCE0)
    u8  pad_024[4];                     // +0x24..+0x28
};
static_assert(offsetof(UiPanelShader, field_10) == 0x10);
static_assert(offsetof(UiPanelShader, field_18) == 0x18);
static_assert(offsetof(UiPanelShader, field_1c) == 0x1C);
static_assert(offsetof(UiPanelShader, field_20) == 0x20);
static_assert(sizeof(UiPanelShader) == 0x28);

/** 0x004EFDDC: five-word command template patched by the shader path. */
struct UiPanelCommand {
    u32 word_00;                        // +0x00: `str r0,[r2],#8`
                                        //   (0x0036C3C0)
    u32 word_04;                        // +0x04: `str sb,[r0,#4]!`
                                        //   (0x0036C394)
    u32 word_08;                        // +0x08: `str fp,[r0,#8]`
                                        //   (0x0036C398)
    u32 word_0c;                        // +0x0C: `str r3,[r2]`
                                        //   (0x0036C3C8)
    u32 color;                          // +0x10: `str r0,[r1,#0x10]`
                                        //   (0x0036C45C)
};
static_assert(offsetof(UiPanelCommand, color) == 0x10);
static_assert(sizeof(UiPanelCommand) == 0x14);

// ---------------------------------------------------------------------------
// Reconstructed entry points (ledger names)
// ---------------------------------------------------------------------------

/** 0x001FE590, 3,608 B: debug value list renderer/editor. */
s32 ui_func_001fe590(void* scene);

/** 0x002ED5D0, 3,584 B: battle command panel renderer. */
s32 ui_func_002ed5d0(void* scene);

/**
 * 0x0036C0A8, 3,480 B: emits the action-panel command stream for the single
 * panel reached through `slot->panel`.  `frame` (r1) supplies the +0x40 byte
 * block and the +0x100 snapshot.  No return value is defined by the epilogue
 * at 0x0036CE00.
 */
void ui_func_0036c0a8(void* unused, UiActionPanel* frame, UiActionSlot* slot);

/**
 * 0x00368CF8, 3,452 B: the multi-panel variant.  Each component is fetched
 * from `slots`; `frame` still supplies the +0x40 byte block and the +0x100
 * snapshot.  No return value is defined by the epilogue at 0x00369A3C.
 */
void ui_func_00368cf8(void* unused, UiActionPanel* frame,
                      UiActionSlotTable* slots);

} // namespace smt4::ui
