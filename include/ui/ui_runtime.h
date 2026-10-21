#pragma once
#include <cstddef>
#include "types.h"
#include "ui/status_down.h"
#include "engine/asd_render_ui.h"

namespace smt4::ui {

/**
 * Shared runtime UI helpers recovered from three large unnamed routines in the
 * `ui` ledger bucket.  The functions keep their address-based ledger names;
 * the header documents the role recovered from the literals and callees.
 */

// ---------------------------------------------------------------------------
// 0x00267FB0: type-dispatched part/model renderer
// ---------------------------------------------------------------------------

/**
 * One 0x28-byte draw entry consumed by 0x00267FB0.  The listing walks the
 * array with `add r4,r4,#0x28` (0x0026849C, 0x00268498, 0x00268DC0 and
 * 0x002691A4) and skips entries whose +0x10 word is negative
 * (`ldr r1,[r4,#0x10]` / `cmp r1,#0` / `blt`, 0x00268190..0x00268198).
 */
struct UiPartEntry {
    f32 vector[4];                  // +0x00: `vldmia r4,{s0,s1,s2,s3}` (0x002681E4)
    s32 index;                      // +0x10: `ldr r1,[r4,#0x10]` (0x00268190)
    u32 color;                      // +0x14: `ldr r2,[r4,#0x14]` (0x002682A4)
    f32 scale;                      // +0x18: `vldr s0,[r4,#0x18]` (0x00268438)
    f32 rotation;                   // +0x1C: `vldr s0,[r4,#0x1c]` (0x002682E8)
    f32 scale_x;                    // +0x20: `vldr s3,[r4,#0x20]` (0x00268460)
    f32 scale_y;                    // +0x24: `vldr s2,[r4,#0x24]` (0x00268470)
};
static_assert(offsetof(UiPartEntry, index) == 0x10);
static_assert(offsetof(UiPartEntry, color) == 0x14);
static_assert(offsetof(UiPartEntry, scale) == 0x18);
static_assert(offsetof(UiPartEntry, rotation) == 0x1C);
static_assert(offsetof(UiPartEntry, scale_x) == 0x20);
static_assert(offsetof(UiPartEntry, scale_y) == 0x24);
static_assert(sizeof(UiPartEntry) == 0x28);

/**
 * Part-set passed through `ctx+0x4C` (0x00267FC4).  Only the words actually
 * dereferenced by 0x00267FB0 are named.
 */
struct UiPartSet {
    u8  pad_00[0x08];
    s32 count;                      // +0x08: `ldr r5,[r8,#8]` (0x00268020)
    u32 flags;                      // +0x0C: `ldr r0,[r8,#0xc]` (0x002680D4)
    u32 field_10;                   // +0x10: `ldrne r0,[r8,#0x10]` (0x00268028)
    u8  pad_14[0x04];
    UiPartEntry* entries;           // +0x18: `ldr r4,[r8,#0x18]` (0x00268038)
    u8  pad_1c[0x04];
    u32 handle;                     // +0x20: `ldr r0,[r8,#0x20]` (0x00268084)
};
static_assert(offsetof(UiPartSet, count) == 0x08);
static_assert(offsetof(UiPartSet, flags) == 0x0C);
static_assert(offsetof(UiPartSet, field_10) == 0x10);
static_assert(offsetof(UiPartSet, entries) == 0x18);
static_assert(offsetof(UiPartSet, handle) == 0x20);

/**
 * Draw-task context passed in r0.  `+0x0C` is the jump-table selector
 * (`ldrh r0,[sb,#0xc]` / `cmp r0,#0xa` / `ldrlo pc,[pc,r0,lsl #2]`,
 * 0x00268034..0x00268040).
 */
struct UiPartRenderContext {
    void* field_00;                 // +0x00
    u32 color;                      // +0x04: `ldr r0,[r0,#4]` (0x00267FC8)
    u32 field_08;                   // +0x08
    u16 kind;                       // +0x0C: jump-table index (0x00268034)
    u16 pad_0e;                     // +0x0E
    u8  pad_10[0x14];               // +0x10..+0x24
    f32 alpha;                      // +0x24: `vldr s0,[r4,#0x24]` (0x0021ACD0)
    void* field_28;                 // +0x28
    u32 enabled;                    // +0x2C: `ldr r0,[r4,#0x2c]` (0x0021ACC4)
    void* field_30;                 // +0x30
    u32* handles_34;                // +0x34: `ldr r6,[sb,#0x34]` (0x00268EEC)
    u32 field_38;                   // +0x38
    u32* handles_3c;                // +0x3C: `ldr r6,[sb,#0x3c]` (0x00269050)
    u32 field_40;                   // +0x40
    void* field_44;                 // +0x44: `ldr r0,[sb,#0x44]` (0x00268628)
    u32 field_48;                   // +0x48
    UiPartSet* parts;               // +0x4C: `ldr r8,[r0,#0x4c]` (0x00267FC4)
    void* sprite;                   // +0x50: `ldr r0,[sb,#0x50]` (0x002685F8)
    f32 scale_x;                    // +0x54: `vldmia r0,{s0,s1}` (0x00268078)
    f32 scale_y;                    // +0x58
};
static_assert(offsetof(UiPartRenderContext, color) == 0x04);
static_assert(offsetof(UiPartRenderContext, kind) == 0x0C);
static_assert(offsetof(UiPartRenderContext, alpha) == 0x24);
static_assert(offsetof(UiPartRenderContext, enabled) == 0x2C);
static_assert(offsetof(UiPartRenderContext, handles_34) == 0x34);
static_assert(offsetof(UiPartRenderContext, handles_3c) == 0x3C);
static_assert(offsetof(UiPartRenderContext, field_44) == 0x44);
static_assert(offsetof(UiPartRenderContext, parts) == 0x4C);
static_assert(offsetof(UiPartRenderContext, sprite) == 0x50);
static_assert(offsetof(UiPartRenderContext, scale_x) == 0x54);
static_assert(offsetof(UiPartRenderContext, scale_y) == 0x58);

/** 4-word scratch block at 0x004EA81C.  The renderer keeps the input tint
 *  at +0x100 (`vstmia r0,{s16,s17,s18,s19}`, 0x0026801C), a 4-float colour at
 *  +0x110, an accumulation quad at +0x120 and a 16-float matrix at +0x140;
 *  the alternating stores/loads at 0x002681B0..0x002681D8 and
 *  0x002687A8..0x002687E0 save/restore the same slots per entry.  The block
 *  overlaps 0x004EA91C by construction: that address is exactly base+0x100,
 *  not a separate global.
 *
 *  0x002F9F54 additionally uses the +0x120 scratch quad (0x002FA130) and
 *  saves the first four-float axis at +0x180 (`vstmia r0,{r1,r2,r3,ip}` over
 *  0x00472530, 0x002FA090; restored at 0x002FA20C and 0x002FA500).  The block
 *  is therefore 0x190 bytes; the +0x130..+0x13F gap remains explicit.
 */
struct UiPartRenderState {
    u8  pad_000[0x100];
    f32 vector[4];                  // +0x100 (also 0x004EA91C tint quad)
    f32 color[4];                   // +0x110
    f32 scratch[4];                 // +0x120 (0x002FA130 / 0x002FA5E0)
    u8  pad_130[0x10];              // +0x130..+0x13F
    f32 matrix[16];                 // +0x140..+0x17F
    f32 saved[4];                   // +0x180 (0x002FA094 / 0x002FA20C)
};
static_assert(offsetof(UiPartRenderState, vector) == 0x100);
static_assert(offsetof(UiPartRenderState, color) == 0x110);
static_assert(offsetof(UiPartRenderState, scratch) == 0x120);
static_assert(offsetof(UiPartRenderState, matrix) == 0x140);
static_assert(offsetof(UiPartRenderState, saved) == 0x180);
static_assert(sizeof(UiPartRenderState) == 0x190);

extern UiPartRenderState g_UiPartRenderState;   // 0x004EA81C (BSS)

// ---------------------------------------------------------------------------
// 0x001F0454: camp fusion inheritance screen
// ---------------------------------------------------------------------------

/**
 * View of the 0x0043DD68 camp-menu workspace used by the fusion inheritance
 * screen.  The workspace is much larger than the 0x600-byte
 * `CampMainContext` prefix; the offsets below are the ones this routine
 * touches.  `+0x3FC` is the horizontal slide counter (used by the three
 * `field_3fc / 4 % 3` computations at 0x001F062C..0x001F0658), `+0x24`,
 * `+0xB0`, `+0x2E0` and `+0x36C` are UiAnimSprite-sized blocks
 * (0x001F066C, 0x001F0BE8, 0x001F0FF8), and the party list lives at
 * `+0x9000`.
 */
struct CampFusionView {
    u8  pad_000[0x24];
    UiAnimSprite sprite_024;        // +0x024..+0x0B0
    UiAnimSprite sprite_0b0;        // +0x0B0..+0x13C
    u8  pad_13c[0x2E0 - 0x13C];
    UiAnimSprite sprite_2e0;        // +0x2E0..+0x36C
    UiAnimSprite sprite_36c;        // +0x36C..+0x3F8
    u8  pad_3f8[0x04];
    s32 field_3fc;                  // +0x3FC: `ldr r0,[r4,#0x3fc]` (0x001F062C)
    u8  pad_400[0x72];
    s16 field_472;                  // +0x472: `ldrsh r2,[r0,#0x72]` (0x001F1A38)
    s16 field_474;                  // +0x474: `ldrsh r1,[r0,#0x74]` (0x001F1A3C)
    s16 field_476;                  // +0x476: `ldrsh r0,[r0,#0x76]` (0x001F1A54)
    u8  pad_478[0x1390 - 0x478];
    u8  records_1390[0x5210 - 0x1390];  // 0x1390: indexed by `work+0x6CE2` (0x001F0724)
    u16 field_5210;                 // +0x5210: `ldrh r0,[r0,r4]` (0x001F06DC)
    u8  pad_5212[0x6CE2 - 0x5212];
    u16 field_6ce2;                 // +0x6CE2: `ldrh r0,[r0,r4]` (0x001F0724)
    u8  pad_6ce4[0x9000 - 0x6CE4];
    u8  pad_9000[0x10];
    u16 rows_9010[8];               // +0x9010: `ldrh r0,[r0,#0x10]` (0x001F08E4)
    u16 rows_9020[8];               // +0x9020: `ldrh r0,[r0,#0x20]` (0x001F0BC0)
    u8  pad_9030[0x91A0 - 0x9030];
    u8  list_91a0[0x64];            // +0x91A0: passed to 0x0029D8E4 (0x001F08C8)
    UiListCursor cursor_9204;       // +0x9204: 0x0029F0F4 / 0x0029F248 / 0x0029F260
    u8  pad_9268[0x04];
    s32 count_926c;                 // +0x926C: `ldr r0,[r0,#0x26c]` (0x001F0A58)
    u8  pad_9270[0x9431 - 0x9270];
    s8  field_9431;                 // +0x9431: `ldrsb r2,[r1,r4]` (0x001AE0A8)
    u8  pad_9432[0x06];             // +0x9432..+0x9438
    // Four 8-byte "possible fusion" descriptors.  0x001F1FC8 indexes them
    // with `add r1,sl,r7,lsl #3` (sl = work) and `ldr r3,[r0,r1]` where
    // r0 = 0x943C (0x001F2204..0x001F220C); the first byte at +0x9450 is
    // the table-valid guard (`ldrb r0,[r0,sl]`, 0x001F2188).
    u32 candidate_pairs_9438[8];    // +0x9438..+0x9458 (4 x {low,high})
};
static_assert(offsetof(CampFusionView, sprite_024) == 0x024);
static_assert(offsetof(CampFusionView, sprite_0b0) == 0x0B0);
static_assert(offsetof(CampFusionView, sprite_2e0) == 0x2E0);
static_assert(offsetof(CampFusionView, sprite_36c) == 0x36C);
static_assert(offsetof(CampFusionView, field_3fc) == 0x3FC);
static_assert(offsetof(CampFusionView, field_472) == 0x472);
static_assert(offsetof(CampFusionView, field_474) == 0x474);
static_assert(offsetof(CampFusionView, field_476) == 0x476);
static_assert(offsetof(CampFusionView, records_1390) == 0x1390);
static_assert(offsetof(CampFusionView, field_5210) == 0x5210);
static_assert(offsetof(CampFusionView, field_6ce2) == 0x6CE2);
static_assert(offsetof(CampFusionView, rows_9010) == 0x9010);
static_assert(offsetof(CampFusionView, rows_9020) == 0x9020);
static_assert(offsetof(CampFusionView, list_91a0) == 0x91A0);
static_assert(offsetof(CampFusionView, cursor_9204) == 0x9204);
static_assert(offsetof(CampFusionView, count_926c) == 0x926C);
static_assert(offsetof(CampFusionView, field_9431) == 0x9431);
static_assert(offsetof(CampFusionView, candidate_pairs_9438) == 0x9438);

// ---------------------------------------------------------------------------
// 0x00197D2C: quest list / quest detail screen
// ---------------------------------------------------------------------------

/**
 * View of the UIQuest singleton (0x0043DD50).  `script/script_extras.h`
 * already declares the allocation and its first 0x5B8 bytes; this view names
 * the runtime fields past that point that the draw routine touches:
 * `+0x5C4` selects the alternate cursor pair (+0x5FC/+0x6C4 versus
 * +0x660/+0x78A, 0x00197D7C..0x00197D94), `+0x5C8` is the selected row,
 * `+0x5D0` the row count, and +0x5D4/+0x5D8/+0x5DC are the three sprite
 * handles passed to 0x002B792C.
 */
struct QuestUiView {
    u8  pad_000[0x34];
    UiAnimSprite sprite_034;        // +0x034: first quest panel (0x00197D54)
    u8  pad_0c0[0x1D8 - 0x0C0];
    UiAnimSprite sprite_1d8;        // +0x1D8: `add r0,r4,#0x1d8` (0x001984CC)
    u8  object_264[0x8C];           // +0x264: passed to 0x002B9708 (0x00198728)
    u8  pad_2f0[0x494 - 0x2F0];
    UiAnimSprite sprite_494;        // +0x494: alternate anchor (0x00197E0C)
    u8  pad_520[0x5C4 - 0x520];
    u8  field_5c4;                  // +0x5C4: `ldrb r0,[r4,#0x5c4]` (0x00197D74)
    u8  pad_5c5[0x03];
    s32 field_5c8;                  // +0x5C8: `ldr r0,[r4,#0x5c8]` (0x0019879C)
    u8  pad_5cc[0x04];
    s32 field_5d0;                  // +0x5D0: `ldr r0,[r4,#0x5d0]` (0x00198784)
    u32 handle_5d4;                 // +0x5D4: `ldr r0,[r4,#0x5d4]` (0x0019890C)
    u32 handle_5d8;                 // +0x5D8: `ldr r0,[r4,#0x5d8]` (0x00198470)
    u32 handle_5dc;                 // +0x5DC: `ldr r0,[r4,#0x5dc]` (0x00198D14)
    u8  pad_5e0[0x10];
    s8  field_5f0;                  // +0x5F0: `ldrb r0,[r5,#0x5f0]` (0x001ADA64)
    u8  pad_5f1[0x01];
    u8  field_5f2;                  // +0x5F2: `ldrb r1,[r1,#0xf2]` (0x00197DB8)
    u8  pad_5f3[0x09];
    UiListCursor cursor_5fc;        // +0x5FC: alternate cursor (0x00197D84)
    UiListCursor cursor_660;        // +0x660: default cursor (0x00197D8C)
    u8  rows_6c4[0x78A - 0x6C4];    // +0x6C4: alternate row-id array (0x00197D88)
    u8  pad_78a[0x97E - 0x78A];
    u16 field_97e;                  // +0x97E: `ldrh r0,[r0,r4]` (0x00197DD0)
    u8  pad_980[0x9FC - 0x980];
};
static_assert(offsetof(QuestUiView, sprite_034) == 0x034);
static_assert(offsetof(QuestUiView, sprite_1d8) == 0x1D8);
static_assert(offsetof(QuestUiView, object_264) == 0x264);
static_assert(offsetof(QuestUiView, sprite_494) == 0x494);
static_assert(offsetof(QuestUiView, field_5c4) == 0x5C4);
static_assert(offsetof(QuestUiView, field_5c8) == 0x5C8);
static_assert(offsetof(QuestUiView, field_5d0) == 0x5D0);
static_assert(offsetof(QuestUiView, handle_5d4) == 0x5D4);
static_assert(offsetof(QuestUiView, handle_5d8) == 0x5D8);
static_assert(offsetof(QuestUiView, handle_5dc) == 0x5DC);
static_assert(offsetof(QuestUiView, field_5f0) == 0x5F0);
static_assert(offsetof(QuestUiView, field_5f2) == 0x5F2);
static_assert(offsetof(QuestUiView, cursor_5fc) == 0x5FC);
static_assert(offsetof(QuestUiView, cursor_660) == 0x660);
static_assert(offsetof(QuestUiView, rows_6c4) == 0x6C4);
static_assert(offsetof(QuestUiView, field_97e) == 0x97E);
static_assert(sizeof(QuestUiView) == 0x9FC);

// ---------------------------------------------------------------------------
// Ledger entry points
// ---------------------------------------------------------------------------

/** Camp fusion inheritance screen (skills inherited from both parents).
 *  Ledger name retained: ui_func_001f0454 (0x001F0454, 5,764 B). */
void ui_func_001f0454(s32 x, s32 y, s32 mode, s32 flag, s32 has_target,
                      s32 slide_dir);

/** Type-dispatched part/model renderer used by two draw callbacks.
 *  Ledger name retained: ui_func_00267fb0 (0x00267FB0, 4,672 B). */
void ui_func_00267fb0(UiPartRenderContext* ctx, f32 scale);

/** Quest list / detail screen draw.
 *  Ledger name retained: ui_func_00197d2c (0x00197D2C, 4,432 B). */
void ui_func_00197d2c();

} // namespace smt4::ui
