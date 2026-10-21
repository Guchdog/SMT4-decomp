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
// Reconstructed entry points (ledger names)
// ---------------------------------------------------------------------------

/** 0x001FE590, 3,608 B: debug value list renderer/editor. */
s32 ui_func_001fe590(void* scene);

/** 0x002ED5D0, 3,584 B: battle command panel renderer. */
s32 ui_func_002ed5d0(void* scene);

} // namespace smt4::ui
