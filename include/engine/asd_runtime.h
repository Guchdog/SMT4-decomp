#pragma once
#include <cstddef>
#include "types.h"

/**
 * Large engine runtime routines reconstructed in `src/engine/asd_runtime.cpp`.
 *
 * The four entry points are unrelated neighbours in the ledger and keep their
 * ledger spellings:
 *
 *   engine_func_001aba94  (0x001ABA94, 4,672 B) random "mr01/mr02" maze
 *   engine_func_002e4b10  (0x002E4B10, 4,116 B) UI part instance/trail update
 *   engine_func_0018844c  (0x0018844C, 4,016 B) camp slot command state machine
 *   engine_func_00304164  (0x00304164, 3,684 B) ribbon/trail history builder
 *
 * Every structure below is an observed prefix: only offsets touched by the
 * listing are declared, each with the proving store/load.  Objects owned by
 * other translation units are never given a `sizeof` assertion.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// engine_func_001aba94: random maze ("map/mr01", "map/mr02")
// ---------------------------------------------------------------------------

/** One 8-byte cell of the 15x15 maze grid.
 *
 * The grid base is `engine + 0x3C`; a cell is addressed as
 * `base + (row * 15 + col) * 8` (the `rsb rX,rY,rY,lsl #4` then `lsl #3`
 * sequence at 0x001ABB70/0x001ABDC4).  Because the state byte sits at cell
 * +0x00, the upward neighbour of a cell is the listing's `-0x3C` offset and
 * the left neighbour is `-0x08`; the compiler folded both into the grid-base
 * displacements used below.
 */
struct MazeCell {
    u8  state;          // +0x00: 0 untouched, 1 wall, 2 carved corridor
                        //   (`strb r3,[ip,#0x3c]`, 0x00285634;
                        //    `ldrb r7,[r2,#0x3c]`, 0x001AC188)
    u8  field_01;       // +0x01: cleared by 0x00285638 (`strb r0,[ip,#0x3d]`)
    u8  field_02;       // +0x02: start marker, `strb r2,[r0,#0x3e]`
                        //   (0x001ABC0C) / `ldrb r1,[r0,#0x3e]` (0x001ACA88)
    u8  field_03;       // +0x03: goal marker, `strb r0,[r1,#0x3f]`
                        //   (0x001ABC28) / `ldrb r1,[r0,#0x3f]` (0x001ACA90)
    u8  wall_style;     // +0x04: `strb r1,[r2,#0x40]` from table 0x00447F30
                        //   (0x001AC728)
    u8  wall_kind;      // +0x05: `strb sb,[r2,#0x41]` from table 0x00447F20;
                        //   high nibble is the model type 0..4
                        //   (`cmp r1,r8,lsr #4`, 0x001AC55C)
    u8  field_06;       // +0x06: `ldrb ip,[r1]` with r1=cell+6 (0x001AC6D8)
    u8  direction;      // +0x07: 0 none, 1/2 for predefined layout entries
                        //   (`strb r6,[r3,#0x43]`, 0x001ABC80)
};
static_assert(offsetof(MazeCell, state) == 0x00);
static_assert(offsetof(MazeCell, field_02) == 0x02);
static_assert(offsetof(MazeCell, wall_style) == 0x04);
static_assert(offsetof(MazeCell, wall_kind) == 0x05);
static_assert(offsetof(MazeCell, direction) == 0x07);
static_assert(sizeof(MazeCell) == 0x08);

/** View of the engine context fields used by the maze generator.
 *
 * The object itself is the global engine context returned by 0x002C2B1C;
 * only the offsets this routine touches are declared.  The grid starts at
 * +0x3C and spans 15*15 cells (0x708 bytes), which is why the later fields
 * start at +0x791.
 */
struct MazeEngineState {
    u8  pad_000[0x3A];                  // +0x000..+0x03A
    u8  field_03a;                      // +0x03A: `strb r0,[sl,#0x3a]`
                                        //   (0x001ABC38)
    u8  field_03b;                      // +0x03B: `strb r0,[sl,#0x3b]`
                                        //   (0x001ABC40)
    MazeCell cells[15 * 15];            // +0x03C..+0x744: grid base
    u8  pad_744[0x04D];                 // +0x744..+0x791
    s8  requested_size;                 // +0x791: `ldrsb r0,[r0,sl]` with
                                        //   literal 0x791 (0x001ABB40);
                                        //   -1 means "no override"
    u8  pad_792[0x61E];                 // +0x792..+0xDB0
    u16 field_db0;                      // +0xDB0: `strh r0,[r1,r6]` with
                                        //   r1=0xDB0 (0x001AC414)
    u8  pad_db2[0x01A];                 // +0xDB2..+0xDCC
    s8  start_x;                        // +0xDCC: `strb r0,[sl,#0xdcc]`
                                        //   (0x001ABBD4)
    s8  start_y;                        // +0xDCD: `strb r2,[sl,#0xdcd]`
    u8  goal_x;                         // +0xDCE: `strb r3,[sl,#0xdce]`
    u8  goal_y;                         // +0xDCF: `strb r3,[sl,#0xdcf]`
    s8  width;                          // +0xDD0: `ldrsb r0,[r1,#0xd1]`
                                        //   relative to +0xD00 (0x001ABB4C)
    s8  height;                         // +0xDD1
    s8  cursor_x;                       // +0xDD2: `strb r2,[r0,#0xdd2]`
                                        //   (0x001ABF5C)
    s8  cursor_y;                       // +0xDD3
    s8  carved;                         // +0xDD4: incremented per predefined
                                        //   corridor cell (0x001ABC88)
    u8  field_dd5;                      // +0xDD5: marker-present flag
                                        //   (0x001AC3D8)
    s8  field_dd6;                      // +0xDD6: marker x (0x001AC3E0)
    s8  field_dd7;                      // +0xDD7: marker y (0x001AC3E8)
};
static_assert(offsetof(MazeEngineState, field_03a) == 0x03A);
static_assert(offsetof(MazeEngineState, cells) == 0x03C);
static_assert(offsetof(MazeEngineState, requested_size) == 0x791);
static_assert(offsetof(MazeEngineState, field_db0) == 0xDB0);
static_assert(offsetof(MazeEngineState, start_x) == 0xDCC);
static_assert(offsetof(MazeEngineState, cursor_x) == 0xDD2);
static_assert(offsetof(MazeEngineState, field_dd7) == 0xDD7);

/** One 0x44-byte entry of the layout table at 0x00447F40.
 *
 * Entry 0 and entry 1 share the same 15x15 layout pointer (both point at
 * 0x00448270); every later entry points at its own 0xE1-byte block.
 */
struct MazeLayoutEntry {
    const u8* layout;                   // +0x00: `ldr r4,[r0,r1,lsl #2]`
                                        //   with r1=id*0x11 (0x001ABB18)
    s16 field_04;                       // +0x04: `ldrsh r1,[r5,#4]`; stored
                                        //   at 0x0049F91C+8 and passed to
                                        //   0x0028550C (0x001ABC48)
    u8  width;                          // +0x06: `ldrb r0,[r5,#6]`
                                        //   -> engine+0xDD0 (0x001ABB1C)
    u8  height;                         // +0x07: `ldrb r0,[r5,#7]`
                                        //   -> engine+0xDD1 (0x001ABB24)
    u8  pad_08[0x04];                   // +0x08..+0x0C
    s8  start_x;                        // +0x0C: `ldrsb r0,[r5,#0xc]`
                                        //   (0x001ABBD0)
    s8  start_y;                        // +0x0D: `ldrsb r2,[r5,#0xd]`
    u8  goal_x;                         // +0x0E: `ldrb r3,[r5,#0xe]`
    u8  goal_y;                         // +0x0F: `ldrb r3,[r5,#0xf]`
    s16 field_10;                       // +0x10: `ldrsh r0,[r5,#0x10]`;
                                        //   non-zero gates the +0x3A/+0x3B copy
    u16 field_12;                       // +0x12: `ldrh r0,[r5,#0x12]`
    u8  pad_14[0x30];                   // +0x14..+0x44
};
static_assert(offsetof(MazeLayoutEntry, layout) == 0x00);
static_assert(offsetof(MazeLayoutEntry, field_04) == 0x04);
static_assert(offsetof(MazeLayoutEntry, width) == 0x06);
static_assert(offsetof(MazeLayoutEntry, start_x) == 0x0C);
static_assert(offsetof(MazeLayoutEntry, field_10) == 0x10);
static_assert(offsetof(MazeLayoutEntry, field_12) == 0x12);
static_assert(sizeof(MazeLayoutEntry) == 0x44);

/** One 12-byte path/dead-end point (0x004BCE8C + 0x100 + index*12).
 *
 * `s32` components are proven by the Manhattan distance loop at
 * 0x001AC1E8..0x001AC240 and by the sort at 0x001AC270..0x001AC2AC.
 */
struct MazePoint {
    s32 x;                              // +0x00: `str r2,[r3,#0x100]`
    s32 y;                              // +0x04: `str r0,[r3,#0x104]`
    s32 distance;                       // +0x08: `str r0,[ip]` (0x001AC23C)
};
static_assert(sizeof(MazePoint) == 12);

/** One 8-byte model placement marker (0x004BCE8C + 0x1C0 + index*8). */
struct MazeMarker {
    u8  kind;                           // +0x00: `strb r8,[r0,#0x1c0]!`
                                        //   with r8=0x18 (0x001ACB44)
    u8  pad_01;                         // +0x01: `strb sl,[r0,#1]` = 0
    s16 x;                              // +0x02: `strh r1,[r0,#2]`
    s16 pad_04;                         // +0x04: `strh sl,[r0,#4]` = 0
    s16 y;                              // +0x06: `strh r2,[r0,#6]`
};
static_assert(offsetof(MazeMarker, kind) == 0x00);
static_assert(offsetof(MazeMarker, x) == 0x02);
static_assert(offsetof(MazeMarker, y) == 0x06);
static_assert(sizeof(MazeMarker) == 8);

/** Maze workspace at 0x004BCE8C (.data/BSS). */
struct MazeGenWork {
    u8  cell_list[0x100];               // +0x000: u16 (x,y) frontier cells;
                                        //   count at +0x244
    MazePoint points[0x10];             // +0x100..+0x1C0: dead-end list,
                                        //   count at +0x24C
    MazeMarker markers[0x10];           // +0x1C0..+0x240
    s32 marker_count;                   // +0x240: `str r0,[sb,#0x240]`
    s32 cell_count;                     // +0x244: `str r1,[fp,#0x244]`
    u8  direction[4];                   // +0x248: `strb r1,[fp,#0x248]`
    s32 path_count;                     // +0x24C: `str r0,[fp,#0x24c]`
    u8  ready;                          // +0x250: `strb r0,[sb,#0x250]`
    u8  pad_251[0x03];                  // +0x251..+0x254
    s32 type_count[5];                  // +0x254..+0x268: maximum cell count
                                        //   per wall type over eight angles
    s32 depth;                          // +0x268: `str r1,[sb,#0x268]`
    u32 model[5];                       // +0x26C..+0x280: model handles
    u8  pad_280[0x04];                  // +0x280..+0x284
    void* instances[5][0x40];           // +0x284: type stride 0x100
                                        //   (`add r6,sb,r7,lsl #8`, 0x001AC8A8)
};
static_assert(offsetof(MazeGenWork, points) == 0x100);
static_assert(offsetof(MazeGenWork, markers) == 0x1C0);
static_assert(offsetof(MazeGenWork, marker_count) == 0x240);
static_assert(offsetof(MazeGenWork, cell_count) == 0x244);
static_assert(offsetof(MazeGenWork, direction) == 0x248);
static_assert(offsetof(MazeGenWork, path_count) == 0x24C);
static_assert(offsetof(MazeGenWork, ready) == 0x250);
static_assert(offsetof(MazeGenWork, type_count) == 0x254);
static_assert(offsetof(MazeGenWork, depth) == 0x268);
static_assert(offsetof(MazeGenWork, model) == 0x26C);
static_assert(offsetof(MazeGenWork, instances) == 0x284);

// ---------------------------------------------------------------------------
// engine_func_002e4b10: UI part instance update
// ---------------------------------------------------------------------------

/** One 0x28-byte animated instance. */
struct UiPartInstance {
    f32 vector[4];                      // +0x00: `ldm r5,{r0,r1,r2,r3}` /
                                        //   `stm r5,{r1,r2,r3}`
    s32 life;                           // +0x10: `ldr r8,[r5,#0x10]`
    f32 field_14;                       // +0x14: `str r0,[r5,#0x14]`
                                        //   (0x0024B898)
    f32 scale_x;                        // +0x18: `vstr s0,[r5,#0x18]`
                                        //   (0x0024B8AC)
    f32 scale_y;                        // +0x1C: `vstr s0,[r5,#0x1c]`
    u8  pad_20[0x08];                   // +0x20..+0x28
};
static_assert(offsetof(UiPartInstance, life) == 0x10);
static_assert(offsetof(UiPartInstance, field_14) == 0x14);
static_assert(offsetof(UiPartInstance, scale_x) == 0x18);
static_assert(sizeof(UiPartInstance) == 0x28);

/** One 0x4C-byte part descriptor (control points, scale and rotation). */
struct UiPartDescriptor {
    f32 anchor[6];                      // +0x00..+0x18: `vldr s7,[r4]` ..
                                        //   `vldr s14,[r4,#0x14]`
    u8  pad_18[0x0C];                   // +0x18..+0x24
    f32 offset[3];                      // +0x24..+0x30: `vldr s1,[r4,#0x24]`
                                        //   .. `[r4,#0x2c]`
    f32 speed_a;                        // +0x30: `vldr s3,[r4,#0x30]`
    f32 speed_b;                        // +0x34: `vldr s1,[r4,#0x34]`
    f32 scale;                          // +0x38: `vldr s1,[r4,#0x38]`
    f32 progress;                       // +0x3C: `vstrle s16,[r4,#0x3c]`
    f32 angle;                          // +0x40: `vmul s0,[r4,#0x40]`
    f32 angle_offset;                   // +0x44: `vldr s1,[r4,#0x44]`
    f32 angle_scale;                    // +0x48: `vldr s1,[r4,#0x48]`
};
static_assert(offsetof(UiPartDescriptor, anchor) == 0x00);
static_assert(offsetof(UiPartDescriptor, offset) == 0x24);
static_assert(offsetof(UiPartDescriptor, speed_a) == 0x30);
static_assert(offsetof(UiPartDescriptor, progress) == 0x3C);
static_assert(offsetof(UiPartDescriptor, angle_offset) == 0x44);
static_assert(sizeof(UiPartDescriptor) == 0x4C);

/** Shared source descriptor read through the owner's +0x20 slot.
 *
 * The four words at +0x10..+0x1C are the quaternion copied to 0x004EA91C
 * before the 0x002A2F1C scene-matrix build (0x002E4B44/0x002E4B6C).
 */
struct UiPartSource {
    u8  pad_00[0x10];                   // +0x00..+0x10
    f32 orientation[4];                 // +0x10..+0x20
    u32 field_20;                       // +0x20: `ldr r2,[r6,#0x20]`
    f32 field_24;                       // +0x24: `vldr s1,[r6,#0x24]`
    f32 field_28;                       // +0x28: `vldr s0,[r6,#0x28]`
    u8  pad_2c[0x40];                   // +0x2C..+0x6C
    f32 field_6c;                       // +0x6C: `vldr s1,[r6,#0x6c]`
    u8  pad_70[0x28];                   // +0x70..+0x98
    f32 field_98;                       // +0x98: `vldr s1,[r6,#0x98]`
    u8  field_9c;                       // +0x9C: `ldrb r0,[r6,#0x9c]`
    u8  pad_9d[0x1B];                   // +0x9D..+0xB8
    s32 field_b8;                       // +0xB8: `ldr r1,[r6,#0xb8]`, zero
                                        //   returns immediately
    u8  pad_bc[0x01];                   // +0xBC
    u8  field_bd;                       // +0xBD: `ldrb r0,[r6,#0xbd]`
    u8  pad_be[0x0A];                   // +0xBE..+0xC8
    s16 field_c8;                       // +0xC8: `ldrsh r1,[r6,#0xc8]`
    u8  pad_ca[0x02];                   // +0xCA..+0xCC
    f32 field_cc;                       // +0xCC: `vldr s2,[r6,#0xcc]`
    f32 field_d0;                       // +0xD0: `vldr s1,[r6,#0xd0]`
    s16 field_d4;                       // +0xD4: `ldrsh r1,[r6,#0xd4]`
    u8  pad_d6[0x02];                   // +0xD6..+0xD8
    f32 field_d8;                       // +0xD8: `vldr s6,[r6,#0xd8]`
    f32 field_dc;                       // +0xDC: `vldr s1,[r6,#0xdc]`
    s16 field_e0;                       // +0xE0: `ldrsh r0,[r6,#0xe0]`
    u8  pad_e2[0x02];                   // +0xE2..+0xE4
    f32 field_e4;                       // +0xE4: `vldr s3,[r6,#0xe4]`
    f32 field_e8;                       // +0xE8: `vldr s1,[r6,#0xe8]`
    f32 field_ec;                       // +0xEC: `vldr s28,[r6,#0xec]`
    f32 field_f0;                       // +0xF0: `vldr s2,[r6,#0xf0]`
    f32 field_f4;                       // +0xF4: `vldr s1,[r6,#0xf4]`
    f32 field_f8;                       // +0xF8: `vldr s27,[r6,#0xf8]`
    f32 bezier[3];                      // +0xFC..+0x108: control triple
    f32 field_108;                      // +0x108: `vldr s2,[r6,#0x108]`
    f32 field_10c;                      // +0x10C
    f32 field_110;                      // +0x110: `vldr s4,[r6,#0x110]`
    f32 field_114;                      // +0x114
    f32 field_118;                      // +0x118
    f32 field_11c;                      // +0x11C: `vldr s1,[r6,#0x11c]`
    f32 field_120;                      // +0x120: `vldr s0,[r6,#0x120]`
};
static_assert(offsetof(UiPartSource, orientation) == 0x10);
static_assert(offsetof(UiPartSource, field_b8) == 0xB8);
static_assert(offsetof(UiPartSource, field_c8) == 0xC8);
static_assert(offsetof(UiPartSource, field_d4) == 0xD4);
static_assert(offsetof(UiPartSource, field_e0) == 0xE0);
static_assert(offsetof(UiPartSource, bezier) == 0xFC);
static_assert(offsetof(UiPartSource, field_120) == 0x120);

/** Owner of the 0x28-byte instances and 0x4C-byte part descriptors. */
struct UiPartUpdateOwner {
    u8  pad_00[0x04];                   // +0x00..+0x04
    s32 count;                          // +0x04: `ldr sl,[r0,#4]`
    u8  pad_08[0x08];                   // +0x08..+0x10
    s32 limit;                          // +0x10: `ldr r0,[sb,#0x10]`
    f32 time;                           // +0x14: `vstr s2,[sb,#0x14]`
    UiPartInstance* instances;          // +0x18: `ldr r5,[r0,#0x18]`
    UiPartDescriptor* parts;            // +0x1C: `ldm r4,{r4,r6}`
    UiPartSource* source;               // +0x20: second word of that load
};
static_assert(offsetof(UiPartUpdateOwner, count) == 0x04);
static_assert(offsetof(UiPartUpdateOwner, limit) == 0x10);
static_assert(offsetof(UiPartUpdateOwner, instances) == 0x18);
static_assert(offsetof(UiPartUpdateOwner, parts) == 0x1C);
static_assert(offsetof(UiPartUpdateOwner, source) == 0x20);

// ---------------------------------------------------------------------------
// engine_func_0018844c: camp slot command state machine
// ---------------------------------------------------------------------------

/** One 0x64-byte camp slot record.
 *
 * The seven command bases are work+0x2A4, +0x308, +0x36C, +0x3D0, +0x434,
 * +0x498 and +0x4FC, i.e. a 0x64 stride (`add r0,r6,r6,lsl #3` then
 * `add r0,r0,r6,lsl #4` = index*0x19, 0x00188D54..0x00188D58).
 */
struct CampSlotRecord {
    u8  pad_00[0x60];                   // +0x00..+0x60
    s8  field_60;                       // +0x60: `ldrsb r0,[r0,#0x60]`
                                        //   (0x001888B8)
    s8  field_61;                       // +0x61: `ldrsb r0,[r0,#0x61]`
                                        //   (0x001888A4)
    u8  pad_62[0x02];                   // +0x62..+0x64
};
static_assert(offsetof(CampSlotRecord, field_60) == 0x60);
static_assert(offsetof(CampSlotRecord, field_61) == 0x61);
static_assert(sizeof(CampSlotRecord) == 0x64);

/** View of the global camp command workspace at 0x0043DA90. */
struct CampSlotCommandWork {
    u8  pad_000[0x1C];                  // +0x000..+0x01C
    s32 state;                          // +0x01C: `ldr r0,[r4,#0x1c]`
                                        //   (0x00188568)
    s32 field_020;                      // +0x020: `str r0,[r4,#0x20]`
                                        //   (0x00189380)
    s32 field_024;                      // +0x024: `str r2,[r0,#0x24]`
                                        //   (0x00189308)
    u8  pad_028[0x09];                  // +0x028..+0x031
    u8  field_031;                      // +0x031: `strb r0,[r4,#0x31]`
                                        //   (0x001892F0)
    u8  field_032;                      // +0x032: `strb r0,[r4,#0x32]`
                                        //   (0x0018874C)
    u8  field_033;                      // +0x033: `strb sl,[r4,#0x33]`
                                        //   (0x00188834)
    u8  list_034;                       // +0x034: `add r0,r4,#0x34`
                                        //   (0x00188D1C)
    u8  pad_035[0x63];                  // +0x035..+0x098
    s8  field_098;                      // +0x098: `ldrsb r2,[r4,#0x98]`
                                        //   (0x00188DB4)
    // The seven 0x64-byte slot records at +0x2A4..+0x560, the embedded list
    // header at +0x34 and the model slot at +0x25C0 are reached through the
    // explicit offsets in the routine; no contiguous array is asserted here.
};
static_assert(offsetof(CampSlotCommandWork, state) == 0x1C);
static_assert(offsetof(CampSlotCommandWork, field_020) == 0x20);
static_assert(offsetof(CampSlotCommandWork, field_024) == 0x24);
static_assert(offsetof(CampSlotCommandWork, field_031) == 0x31);
static_assert(offsetof(CampSlotCommandWork, field_032) == 0x32);
static_assert(offsetof(CampSlotCommandWork, field_033) == 0x33);
static_assert(offsetof(CampSlotCommandWork, list_034) == 0x34);
static_assert(offsetof(CampSlotCommandWork, field_098) == 0x98);

// ---------------------------------------------------------------------------
// engine_func_00304164: ribbon/trail history builder
// ---------------------------------------------------------------------------

/** 0x00: entry-array holder, 0x04: fractional time, 0x08: time step. */
struct TrailBuffer {
    void* entries;                      // +0x00: `ldr r1,[r4]`
    f32 time;                           // +0x04: `vldmia r0,{s0,s1}` with
                                        //   r0=buffer+4 (0x00304270)
    f32 step;                           // +0x08: added into +0x04
};
static_assert(offsetof(TrailBuffer, entries) == 0x00);
static_assert(offsetof(TrailBuffer, time) == 0x04);
static_assert(offsetof(TrailBuffer, step) == 0x08);

/** Source object reached through TrailEntry+0x00. */
struct TrailFrame {
    u8  pad_00[0x02];                   // +0x00..+0x02
    u16 count;                          // +0x02: `ldrh r2,[r0,#2]`
                                        //   (0x003042C0)
    u8  pad_04[0x04];                   // +0x04..+0x08
    void* track;                        // +0x08: `ldr r3,[r0,#8]`
                                        //   (0x003042C4)
};
static_assert(offsetof(TrailFrame, count) == 0x02);
static_assert(offsetof(TrailFrame, track) == 0x08);

/** Track object whose +0x30 slot is the five-vec3 output array. */
struct TrailTrack {
    u8  pad_00[0x30];                   // +0x00..+0x30
    f32* points;                        // +0x30: `ldr r8,[r3,#0x30]`
                                        //   (0x003042CC)
};
static_assert(offsetof(TrailTrack, points) == 0x30);

/** One 0x30-byte trail entry. */
struct TrailEntry {
    TrailFrame* frame;                  // +0x00: `ldr r0,[r0]` (0x003042BC)
    f32 vector[3];                      // +0x04..+0x10: `vstr s0,[r0,#4]`
                                        //   (0x003048CC)
    u8  pad_10[0x04];                   // +0x10..+0x14
    s32 life;                           // +0x14: `ldr r0,[r0,#0x14]`
                                        //   (0x00304288)
    u32 color;                          // +0x18: `ldr r0,[r0,#0x18]`
                                        //   (0x00304298)
    f32 angle_a;                        // +0x1C: `vldr s0,[r0,#0x1c]`
                                        //   (0x003043E0)
    f32 angle_b;                        // +0x20: `vldr s0,[r0,#0x20]`
                                        //   (0x003043EC)
    f32 offset_a;                       // +0x24: `vldr s3,[r0,#0x24]`
                                        //   (0x003043A0)
    f32 offset_b;                       // +0x28: `vldr s6,[r0,#0x28]`
    f32 offset_c;                       // +0x2C: `vldr s7,[r2,#0x2c]`
                                        //   (0x003047F8)
};
static_assert(offsetof(TrailEntry, frame) == 0x00);
static_assert(offsetof(TrailEntry, vector) == 0x04);
static_assert(offsetof(TrailEntry, life) == 0x14);
static_assert(offsetof(TrailEntry, color) == 0x18);
static_assert(offsetof(TrailEntry, angle_a) == 0x1C);
static_assert(offsetof(TrailEntry, offset_c) == 0x2C);
static_assert(sizeof(TrailEntry) == 0x30);

/** One 0x3C-byte history sample written by engine_func_00304164. */
struct TrailSample {
    f32 position[3];                    // +0x00..+0x0C
    f32 w;                              // +0x0C: `vstr s3,[r1,#0xc]`
    s32 index;                          // +0x10: `str ip,[r0,#0x10]!`
                                        //   with ip=-1 (0x00304B5C)
    u8  pad_14[0x28];                   // +0x14..+0x3C
};
static_assert(offsetof(TrailSample, position) == 0x00);
static_assert(offsetof(TrailSample, index) == 0x10);
static_assert(sizeof(TrailSample) == 0x3C);

/** Owner of the trail builder (argument object). */
struct TrailOwner {
    u8  pad_00[0x28];                   // +0x00..+0x28
    s32 limit;                          // +0x28: `ldr r2,[r0,#0x28]`
                                        //   (0x00304174)
    u8  pad_2c[0x04];                   // +0x2C..+0x30
    TrailBuffer* buffer;                // +0x30: `ldr r4,[r0,#0x30]`
                                        //   (0x0030417C)
    struct TrailConfig* config;         // +0x34: `ldr r1,[r0,#0x34]`
                                        //   (0x00304170)
};
static_assert(offsetof(TrailOwner, limit) == 0x28);
static_assert(offsetof(TrailOwner, buffer) == 0x30);
static_assert(offsetof(TrailOwner, config) == 0x34);

/** Configuration consumed by the trail builder. */
struct TrailConfig {
    u8  pad_00[0x34];                   // +0x00..+0x34
    s32 active_count;                   // +0x34: `ldr r0,[r1,#0x34]`
                                        //   (0x00304180)
    s32 entry_count;                    // +0x38: `ldr r0,[r0,#0x38]`
                                        //   (0x003041B4)
    s32 frame_span;                     // +0x3C: `vcvt.f32.u32 s0,s1`
    s32 field_40;                       // +0x40: `ldr r1,[sp,#0x7c]`
                                        //   (0x00304F74)
    u8  pad_44[0x08];                   // +0x44..+0x4C
    s32 angle_count;                    // +0x4C: `vcvt.f32.u32 s1,s2`
    f32 radius;                         // +0x50: `vldr s0,[r0,#0x50]`
    u8  pad_54[0x28];                   // +0x54..+0x7C
    f32 field_7c;                       // +0x7C: `vldr s1,[r0,#0x7c]`
    f32 field_80;                       // +0x80: `vldr s0,[r0,#0x80]`
    f32 segment_length;                 // +0x84: `vldr s3,[r0,#0x84]`
    u8  field_88;                       // +0x88: `ldrb r0,[r0,#0x88]`
    u8  pad_89[0x13];                   // +0x89..+0x9C
    f32 fade_speed;                     // +0x9C: `vldr s1,[r0,#0x9c]`
    f32 field_a0;                       // +0xA0: `vldr s3,[r0,#0xa0]`
    f32 field_a4;                       // +0xA4: `vldr s1,[r0,#0xa4]`
    f32 time_step;                      // +0xA8: `vldr s0,[r0,#0xa8]`
};
static_assert(offsetof(TrailConfig, active_count) == 0x34);
static_assert(offsetof(TrailConfig, entry_count) == 0x38);
static_assert(offsetof(TrailConfig, frame_span) == 0x3C);
static_assert(offsetof(TrailConfig, angle_count) == 0x4C);
static_assert(offsetof(TrailConfig, radius) == 0x50);
static_assert(offsetof(TrailConfig, field_7c) == 0x7C);
static_assert(offsetof(TrailConfig, segment_length) == 0x84);
static_assert(offsetof(TrailConfig, time_step) == 0xA8);

// ---------------------------------------------------------------------------
// Globals (addresses are the storage locations used by the listing)
// ---------------------------------------------------------------------------

// 0x00447EC0: 24 four-byte direction permutations consumed by Random_Range(0x17).
extern const u8 g_MazeDirectionOrders[24][4];
// 0x00447F20 / 0x00447F30: 16-byte wall tables indexed by the four-neighbour
// mask (bit0 left, bit1 right, bit2 up, bit3 down).
extern const u8 g_MazeWallKinds[16];        // cell+0x05 (high nibble = type)
extern const u8 g_MazeWallStyles[16];       // cell+0x04
// 0x00447F40: twelve map layouts; entry 0 and 1 share one 15x15 block.
extern const MazeLayoutEntry g_MazeLayoutTable[12];
extern const u8 g_MazeLayout00[15 * 15];
extern const u8 g_MazeLayout02[15 * 15];
extern const u8 g_MazeLayout03[15 * 15];
extern const u8 g_MazeLayout04[15 * 15];
extern const u8 g_MazeLayout05[15 * 15];
extern const u8 g_MazeLayout06[15 * 15];
extern const u8 g_MazeLayout07[15 * 15];
extern const u8 g_MazeLayout08[15 * 15];
extern const u8 g_MazeLayout09[15 * 15];
extern const u8 g_MazeLayout10[15 * 15];
extern const u8 g_MazeLayout11[15 * 15];

// 0x004BCE8C: maze frontier/path/model workspace.
extern MazeGenWork g_MazeGenWork;

// 0x00472530 / 0x00472550: two four-float scratch blocks used by the trail
// builders.  0x00472530 starts {0,1,0,1}, 0x00472550 starts {0,0,0,1}.
extern f32 g_TrailScratchA[4];
extern f32 g_TrailScratchB[4];

// ---------------------------------------------------------------------------
// Reconstructed entry points
// ---------------------------------------------------------------------------

// 0x001ABA94 (4,672 B): generate (or load) the "mr01/mr02" maze, place its
// models and markers, and publish the ready flag.
void engine_func_001aba94();

// 0x002E4B10 (4,116 B): advance every UI part instance/descriptor pair.
void engine_func_002e4b10(UiPartUpdateOwner* owner);

// 0x0018844C (4,016 B): run the camp slot command state machine for one of
// commands 0x11..0x17.
void engine_func_0018844c(u32 command);

// 0x00304164 (3,684 B): rebuild the ribbon/trail history for one owner.
void engine_func_00304164(TrailOwner* owner);

} // namespace smt4::engine
