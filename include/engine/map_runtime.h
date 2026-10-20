#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_scene.h"

/**
 * Map runtime workspaces and entry points reconstructed in
 * `src/engine/map_runtime.cpp`.
 *
 * The nine functions come from seven original translation units named by the
 * inline `ADR` strings in the listing:
 *
 *   lmapMain         c:\SMT4\XRD686\sdds4\program\map\lmapMain.cpp
 *   mapIf            c:\SMT4\XRD686\sdds4\program\map\mapIf.cpp
 *   mapEnemy         c:\SMT4\XRD686\sdds4\program\map\mapEnemy.cpp
 *   mapDepart        c:\SMT4\XRD686\sdds4\program\map\mapDepart.cpp
 *   mapEpl           c:\SMT4\XRD686\sdds4\program\map\mapEpl.cpp
 *   mapMain          c:\SMT4\XRD686\sdds4\program\map\mapMain.cpp
 *   naviMain         c:\SMT4\XRD686\sdds4\program\mapnavi\naviMain.cpp
 *   3dEventOpening   c:\SMT4\XRD686\sdds4\program\event\3dEvent\3dEventOpening.cpp
 *   NkmGrowEvent     c:\SMT4\XRD686\sdds4\program\gamedata\nkm\NkmGrowEvent.cpp
 *
 * Every field carries the store/load that proves its offset.  Workspaces whose
 * allocation size is an immediate in the listing assert `sizeof`; objects owned
 * by another TU are modelled as observed prefixes with `offsetof` only.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// lmapMain.cpp (0x001D2B14, 760 B)
// ---------------------------------------------------------------------------

/**
 * Large-map ("LMAP") host object allocated by `lmapMain_func_001d2b14`.
 * Allocation: 0x4F04 bytes (`ldr r3,[pc,#0x270] @ =0x4f04`, 0x001D2B30).
 */
struct LmapMainWork {
    void* calc_task;                    // +0x000: `str r0,[r4]` "LMAP C" (0x001D2D40)
    void* draw_task;                    // +0x004: `str r0,[r4,#4]` "LMAP U" (0x001D2D68)
    u8  field_008;                      // +0x008: `strb r6,[r4,#8]` (0x001D2D1C)
    u8  field_009;                      // +0x009: `strb r6,[r4,#9]` (0x001D2B64)
    u8  field_00a;                      // +0x00A: `strb r6,[r4,#0xa]` (0x001D2B68)
    u8  field_00b;                      // +0x00B: `strb r6,[r4,#0xb]` (0x001D2B6C)
    u32 field_00c;                      // +0x00C: `str r6,[r4,#0xc]` (0x001D2B70)
    u32 field_010;                      // +0x010: `str r6,[r4,#0x10]` (0x001D2B74)
    u8  pad_014[0x2C];                  // +0x014..+0x040
    u32 field_040;                      // +0x040: `str r2,[r4,#0x40]` = 0x65 (0x001D2BAC)
    u8  pad_044[0x04];                  // +0x044..+0x048
    u32 field_048;                      // +0x048: `str r7,[r4,#0x48]` = 1 (0x001D2BB8)
    u16 field_04c;                      // +0x04C: `strh r6,[r4,#0x4c]` (0x001D2BB0)
    u16 field_04e;                      // +0x04E: `strh r6,[r4,#0x4e]` (0x001D2BB4)
    u8  pad_050[0x74];                  // +0x050..+0x0C4
    f32 field_0c4;                      // +0x0C4: `vstr s0,[r4,#0xc4]` = 1.0f (0x001D2BA4)
    f32 field_0c8;                      // +0x0C8: `vstr s0,[r4,#0xc8]` = 1.0f (0x001D2BA0)
    u32 field_0cc;                      // +0x0CC: `stm r2,{r1,r6}`, r2=r0+0xcc (0x001D2B90)
    u32 field_0d0;                      // +0x0D0: second word of that store
    u32 field_0d4;                      // +0x0D4: `str r6,[r0,#0xd4]` (0x001D2B94)
    u8  pad_0d8[0x04];                  // +0x0D8..+0x0DC
    f32 field_0dc;                      // +0x0DC: `vstr s0,[r4,#0xdc]` = 0.0f (0x001D2C1C)
    u8  field_0e0;                      // +0x0E0: `strb r6,[r4,#0xe0]` (0x001D2C24)
    u8  field_0e1;                      // +0x0E1: `strb r6,[r4,#0xe1]` (0x001D2CF4)
    u8  pad_0e2[0x02];                  // +0x0E2..+0x0E4
    u32 field_0e4;                      // +0x0E4: `str r2,[r4,#0xe4]` = 0x38 (0x001D2CF8)
    f32 field_0e8;                      // +0x0E8: `vstr s0,[r4,#0xe8]` = 40.0f (0x001D2CFC)
    u8  block_0ec[0x8A4];               // +0x0EC..+0x990: handed to 0x00396534
                                        //   (`add r0,r4,#0xec`, 0x001D2C08)
    u8  field_990;                      // +0x990: `strb r6,[r4,#0x990]` (0x001D2CE0)
    u8  pad_991[0x03];                  // +0x991..+0x994
    u32 field_994;                      // +0x994: `str r6,[r4,#0x994]` (0x001D2C0C)
    u8  pad_998[0x08];                  // +0x998..+0x9A0
    u8  field_9a0;                      // +0x9A0: `strb r6,[r4,#0x9a0]` (0x001D2CE4)
    u8  pad_9a1[0x03];                  // +0x9A1..+0x9A4
    u32 field_9a4;                      // +0x9A4: `str r6,[r4,#0x9a4]` (0x001D2C54)
    u32 field_9a8;                      // +0x9A8: `str r6,[r4,#0x9a8]` (0x001D2C58)
    u32 field_9ac;                      // +0x9AC: `str r6,[r4,#0x9ac]` (0x001D2C5C)
    u32 field_9b0;                      // +0x9B0: `str r6,[r4,#0x9b0]` (0x001D2C60)
    u32 field_9b4;                      // +0x9B4: `str r6,[r4,#0x9b4]` (0x001D2C64)
    u32 field_9b8;                      // +0x9B8: `str r6,[r4,#0x9b8]` (0x001D2C68)
    u8  pad_9bc[0x28];                  // +0x9BC..+0x9E4
    u32 field_9e4;                      // +0x9E4: `str r6,[r4,#0x9e4]` (0x001D2C6C)
    u32 field_9e8;                      // +0x9E8: `str r6,[r4,#0x9e8]` (0x001D2C70)
    u32 field_9ec;                      // +0x9EC: `str r6,[r4,#0x9ec]` (0x001D2C74)
    u32 field_9f0;                      // +0x9F0: `str r6,[r4,#0x9f0]` (0x001D2C78)
    u8  pad_9f4[0x0C];                  // +0x9F4..+0xA00
    f32 field_a00;                      // +0xA00: `vstr s0,[r2,#0x200]`, r2=r4+0x800 (0x001D2C28)
    f32 field_a04;                      // +0xA04: `vstr s0,[r2,#0x204]` (0x001D2C2C)
    f32 field_a08;                      // +0xA08: `vstr s0,[r2,#0x208]` (0x001D2C30)
    u32 field_a0c;                      // +0xA0C: `str r6,[r4,#0xa0c]` (0x001D2C7C)
    u32 field_a10[0x20];                // +0xA10..+0xA90: zeroed by the paired
                                        //   store loop at 0x001D2C94..0x001D2CB4
    u8  field_a90;                      // +0xA90: `strb r6,[r4,#0xa90]` (0x001D2C90)
    u8  pad_a91[0x03];                  // +0xA91..+0xA94
    u32 field_a94;                      // +0xA94: `str r6,[r4,#0xa94]` (0x001D2C80)
    u32 field_a98;                      // +0xA98: `str r6,[r4,#0xa98]` (0x001D2C84)
    u32 field_a9c;                      // +0xA9C: `str r6,[r4,#0xa9c]` (0x001D2C88)
    u8  pad_aa0[0x91];                  // +0xAA0..+0xB31
    u8  actor_flags[0x437B];            // +0xB31..+0x4EAC: 0x80 records swept with
                                        //   a 0x88 stride (0x001D2CC0..0x001D2CD8)
    u32 field_4eac;                     // +0x4EAC: `str r6,[r0,r4]`, r0=0x4eac (0x001D2C48)
    f32 field_4eb0;                     // +0x4EB0: `vstmia r1,{s1,s2,s3}` (0x001D2C4C)
    f32 field_4eb4;                     // +0x4EB4: second word of that store
    f32 field_4eb8;                     // +0x4EB8: third word of that store
    u8  pad_4ebc[0x44];                 // +0x4EBC..+0x4F00
    u32 field_4f00;                     // +0x4F00: `str r6,[r0,r4]`, r0=0x4f00 (0x001D2CE8)
};
static_assert(offsetof(LmapMainWork, calc_task) == 0x000);
static_assert(offsetof(LmapMainWork, draw_task) == 0x004);
static_assert(offsetof(LmapMainWork, field_00c) == 0x00C);
static_assert(offsetof(LmapMainWork, field_040) == 0x040);
static_assert(offsetof(LmapMainWork, field_048) == 0x048);
static_assert(offsetof(LmapMainWork, field_04c) == 0x04C);
static_assert(offsetof(LmapMainWork, field_0c4) == 0x0C4);
static_assert(offsetof(LmapMainWork, field_0cc) == 0x0CC);
static_assert(offsetof(LmapMainWork, field_0d4) == 0x0D4);
static_assert(offsetof(LmapMainWork, field_0dc) == 0x0DC);
static_assert(offsetof(LmapMainWork, field_0e4) == 0x0E4);
static_assert(offsetof(LmapMainWork, block_0ec) == 0x0EC);
static_assert(offsetof(LmapMainWork, field_994) == 0x994);
static_assert(offsetof(LmapMainWork, field_a00) == 0xA00);
static_assert(offsetof(LmapMainWork, field_a10) == 0xA10);
static_assert(offsetof(LmapMainWork, field_a90) == 0xA90);
static_assert(offsetof(LmapMainWork, field_4eac) == 0x4EAC);
static_assert(offsetof(LmapMainWork, actor_flags) == 0xB31);
static_assert(offsetof(LmapMainWork, field_4f00) == 0x4F00);
static_assert(sizeof(LmapMainWork) == 0x4F04);

/**
 * Scene/view object reached through the global pointer slot 0x00447E88.
 *
 * `lmapMain_func_001d2b14` writes nine camera floats and two ranges at
 * +0x1C..+0x50 plus the pair at +0x15C (0x001D2BC0..0x001D2C04); 0x001B4664 and
 * 0x00192320/0x001923D0/0x001A8B64 reset the same object elsewhere, so the
 * extent beyond these fields belongs to those TUs and is not asserted.
 */
struct MapSceneView {
    u8  pad_000[0x1C];                  // +0x000..+0x01C
    f32 field_01c;                      // +0x01C: `vstmia r1,{s0,s1,s2}`, r1=r0+0x1c
    f32 field_020;                      // +0x020: 0.01f (0x3c23d70a)
    f32 field_024;                      // +0x024: -4780.0f (0xc5956000)
    f32 field_028;                      // +0x028: `vstr s3,[r0,#0x28]` (0x001D2BE4)
    f32 field_02c;                      // +0x02C: `vstmia r1,{s1,s2,s3}`, r1=r0+0x2c
    f32 field_030;                      // +0x030: second word of that store
    f32 field_034;                      // +0x034: third word of that store
    f32 field_038;                      // +0x038: `vstmia r1,{s1,s2}`, r1=r0+0x38
    f32 field_03c;                      // +0x03C: second word of that store
    u8  pad_040[0x0C];                  // +0x040..+0x04C
    f32 field_04c;                      // +0x04C: `vstr s0,[r0,#0x4c]` = 180.0f (0x001D2BF4)
    f32 field_050;                      // +0x050: `vstr s0,[r0,#0x50]` = 180.0f (0x001D2BF8)
    u8  pad_054[0x108];                 // +0x054..+0x15C
    f32 field_15c;                      // +0x15C: `vstmia r0,{s4,s5}`, r0=r0+0x15c (0x001D2C04)
    f32 field_160;                      // +0x160: second word of that store
};
static_assert(offsetof(MapSceneView, field_01c) == 0x01C);
static_assert(offsetof(MapSceneView, field_028) == 0x028);
static_assert(offsetof(MapSceneView, field_038) == 0x038);
static_assert(offsetof(MapSceneView, field_04c) == 0x04C);
static_assert(offsetof(MapSceneView, field_15c) == 0x15C);

// ---------------------------------------------------------------------------
// mapIf.cpp (0x0018ABA8, 696 B)
// ---------------------------------------------------------------------------

/**
 * One 0x30-byte projection quad written by `mapIf_func_0018aba8`
 * (0x0018AD1C..0x0018ADC0).  Four consecutive 3-float corners.
 */
struct MapIfProjectionQuad {
    f32 corner[4][3];                   // +0x00..+0x30
};
static_assert(sizeof(MapIfProjectionQuad) == 0x30);

/**
 * Global projection table at 0x004B5D30 (BSS).
 *
 * Three quads are written at +0x000, +0x630 and +0xC60: the `add r1,r0,#0x630`
 * / `add r2,r1,#0x630` chain at 0x0018AD34..0x0018AD3C proves the 0x630 stride.
 * No other offset of this object is touched, so the tail is not declared.
 */
struct MapIfProjectionTables {
    MapIfProjectionQuad area;           // +0x000: camera quad (0x0018AD38..0x0018AD60)
    u8  pad_030[0x600];                 // +0x030..+0x630
    MapIfProjectionQuad field;          // +0x630: field quad (0x0018AD64..0x0018AD94)
    u8  pad_660[0x600];                 // +0x660..+0xC60
    MapIfProjectionQuad opening;        // +0xC60: opening quad (0x0018AD98..0x0018ADC0)
};
static_assert(offsetof(MapIfProjectionTables, area) == 0x000);
static_assert(offsetof(MapIfProjectionTables, field) == 0x630);
static_assert(offsetof(MapIfProjectionTables, opening) == 0xC60);
static_assert(sizeof(MapIfProjectionTables) == 0xC90);

/**
 * Map-interface host object allocated by `mapIf_func_0018aba8`.
 * Allocation: 0xCCE8 bytes (`ldr r3,[pc,#0x22c] @ =0xcce8`, 0x0018ABD4).
 */
struct MapIfWork {
    void* calc_task;                    // +0x000: `str r1,[r4]` "MAPIF C" (0x0018ACA0)
    void* up_task;                      // +0x004: `str r0,[r4,#4]` "MAPIF U" (0x0018ACC8)
    void* draw_task;                    // +0x008: `str r0,[r4,#8]` "MIF3DL" (0x0018AD18)
    u8  pad_00c[0x08];                  // +0x00C..+0x014
    u8  field_014;                      // +0x014: `strb r7,[r0,#0x14]` (0x0018ABF8)
    u8  field_015;                      // +0x015: `strb r6,[r4,#0x15]` (0x0018ADC4)
    u8  field_016;                      // +0x016: `strb r7,[r0,#0x16]` (0x0018ABFC)
    u8  pad_017[0x01];                  // +0x017..+0x018
    u8  field_018;                      // +0x018: `strb r7,[r0,#0x18]` (0x0018AC00)
    u8  pad_019[0x03];                  // +0x019..+0x01C
    u32 field_01c;                      // +0x01C: `str r7,[r0,#0x1c]` (0x0018AC04)
    u8  field_020;                      // +0x020: `strb r7,[r0,#0x20]` (0x0018AC08)
    u8  pad_021[0x0F];                  // +0x021..+0x030
    u32 field_030;                      // +0x030: `str r7,[r0,#0x30]` (0x0018AC0C)
    u32 field_034;                      // +0x034: `str r7,[r0,#0x34]` (0x0018AC10)
    u32 field_038;                      // +0x038: `str r7,[r0,#0x38]` (0x0018AC14)
    u8  pad_03c[0xC84];                 // +0x03C..+0xCC0
    u8  field_cc0;                      // +0xCC0: `strb r7,[r3]`, r3=r0+0xcc0 (0x0018AC30)
    u8  pad_cc1[0xBF0F];                // +0xCC1..+0xCBD0
    u8  field_cbd0;                     // +0xCBD0: `strb r7,[r2]`, r2=r0+0xcbd0 (0x0018AC20)
    u8  pad_cbd1[0xE7];                 // +0xCBD1..+0xCCB8
    u16 field_ccb8;                     // +0xCCB8: `strh r7,[r1,#0xb8]`, r1=r0+0xcc00 (0x0018AC28)
    u16 field_ccba;                     // +0xCCBA: `strh r7,[r1,#0xba]` (0x0018AC2C)
    u8  pad_ccbc[0x10];                 // +0xCCBC..+0xCCCC
    f32 field_cccc;                     // +0xCCCC: `vstr s16,[r1,#0xcc]` (0x0018AC3C)
    f32 field_ccd0;                     // +0xCCD0: `vstr s16,[r1,#0xd0]` (0x0018AC40)
    f32 field_ccd4;                     // +0xCCD4: `vstr s16,[r1,#0xd4]` (0x0018AC4C)
    u8  field_ccd8;                     // +0xCCD8: `strb r7,[ip]`, ip=r0+0xccd8 (0x0018AC58)
    u8  pad_ccd9[0x07];                 // +0xCCD9..+0xCCE0
    u8  field_cce0;                     // +0xCCE0: `strb r7,[r8]`, r8=r0+0xcce0 (0x0018AC60)
    u8  pad_cce1[0x03];                 // +0xCCE1..+0xCCE4
    u32 field_cce4;                     // +0xCCE4: `str r7,[sb]`, sb=r0+0xcce4 (0x0018AC70)
};
static_assert(offsetof(MapIfWork, calc_task) == 0x000);
static_assert(offsetof(MapIfWork, up_task) == 0x004);
static_assert(offsetof(MapIfWork, draw_task) == 0x008);
static_assert(offsetof(MapIfWork, field_014) == 0x014);
static_assert(offsetof(MapIfWork, field_015) == 0x015);
static_assert(offsetof(MapIfWork, field_030) == 0x030);
static_assert(offsetof(MapIfWork, field_cc0) == 0xCC0);
static_assert(offsetof(MapIfWork, field_cbd0) == 0xCBD0);
static_assert(offsetof(MapIfWork, field_ccb8) == 0xCCB8);
static_assert(offsetof(MapIfWork, field_cccc) == 0xCCCC);
static_assert(offsetof(MapIfWork, field_ccd8) == 0xCCD8);
static_assert(offsetof(MapIfWork, field_cce0) == 0xCCE0);
static_assert(offsetof(MapIfWork, field_cce4) == 0xCCE4);
static_assert(sizeof(MapIfWork) == 0xCCE8);

// ---------------------------------------------------------------------------
// mapEnemy.cpp (0x001A8924, 552 B)
// ---------------------------------------------------------------------------

/**
 * One of the 0x20 roaming enemy records.  The record base is `work + 0x34`
 * (`strb r7,[r4,#0x34]!`, 0x001A89E4) and the stride is 0x180
 * (`add r0,r5,r5,lsl #1` then `lsl #7` = r5*0x180, 0x001A89DC/0x001A89E0).
 */
struct MapEnemyEntry {
    u8  field_00;                       // +0x000: `strb r7,[r4]` after writeback
    u8  pad_01[0x03];                   // +0x001..+0x004
    u32 index;                          // +0x004: `str r5,[r4,#4]` (0x001A89EC)
    f32 field_08;                       // +0x008: `vstr s16,[r4,#8]` (0x001A89F0)
    f32 field_0c;                       // +0x00C: `vstr s16,[r4,#0xc]` (0x001A89F4)
    f32 field_10;                       // +0x010: `vstr s16,[r4,#0x10]` (0x001A89F8)
    f32 field_14;                       // +0x014: `stm r0,{r1,r2}` verbatim copy
                                        //   of +0x08 (0x001A8A04)
    f32 field_18;                       // +0x018: verbatim copy of +0x0C
    f32 field_1c;                       // +0x01C: `vstr s16,[r4,#0x1c]` (0x001A8A0C)
    f32 field_20;                       // +0x020: `vstr s16,[r4,#0x20]` (0x001A8A10)
    f32 field_24;                       // +0x024: `vstr s16,[r4,#0x24]` (0x001A8A14)
    f32 field_28;                       // +0x028: `vstr s16,[r4,#0x28]` (0x001A8A18)
    f32 field_2c;                       // +0x02C: `vstr s16,[r4,#0x2c]` (0x001A8A1C)
    u32 field_30;                       // +0x030: `stm r0,{r7,r8,sb}` = 0 (0x001A8A20)
    s32 field_34;                       // +0x034: second word of that store = -1
    u32 field_38;                       // +0x038: third word of that store = 1
    f32 field_3c;                       // +0x03C: `vstr s17,[r4,#0x3c]` = 99999.0f
                                        //   (0x001A8A28)
    u8  pad_40[0x10];                   // +0x040..+0x050
    u8  field_50;                       // +0x050: `strb r7,[r4,#0x50]` (0x001A8A2C)
    u8  pad_51[0x03];                   // +0x051..+0x054
    u32 field_54;                       // +0x054: `str r7,[r4,#0x54]` (0x001A8A30)
    u32 field_58;                       // +0x058: `str r7,[r4,#0x58]` (0x001A8A34)
    u32 field_5c;                       // +0x05C: `str r7,[r4,#0x5c]` (0x001A8A38)
    u32 field_60;                       // +0x060: `str r7,[r4,#0x60]` (0x001A8A3C)
    u32 field_64;                       // +0x064: `str r7,[r4,#0x64]` (0x001A8A40)
    u32 field_68;                       // +0x068: `str r7,[r4,#0x68]` (0x001A8A44)
    u32 field_6c;                       // +0x06C: `str r7,[r4,#0x6c]` (0x001A8A48)
    u32 field_70;                       // +0x070: `str r7,[r4,#0x70]` (0x001A8A4C)
    u32 field_74;                       // +0x074: `stm r0,{r7,sb}` = 0 (0x001A8A50)
    u32 field_78;                       // +0x078: second word of that store = 1
    u8  field_7c;                       // +0x07C: `strb r7,[r4,#0x7c]` (0x001A8A58)
    u8  field_7d;                       // +0x07D: `strb r7,[r4,#0x7d]` (0x001A8A5C)
    u8  field_7e;                       // +0x07E: `strb r7,[r4,#0x7e]` (0x001A8A60)
    u8  pad_7f[0x05];                   // +0x07F..+0x084
    u32 field_84;                       // +0x084: `str r7,[r4,#0x84]` (0x001A8A64)
    u32 field_88;                       // +0x088: `str r7,[r4,#0x88]` (0x001A8A68)
    u32 field_8c;                       // +0x08C: `stm r2,{r1,r7}` = rand+0x1e
                                        //   (0x001A8A78..0x001A8A7C)
    u32 field_90;                       // +0x090: second word of that store
    u8  pad_94[0xA4];                   // +0x094..+0x138
    u16 field_138;                      // +0x138: `strh r7,[r0,#0x38]`, r0=r4+0x100
    u16 field_13a;                      // +0x13A: `strh r7,[r0,#0x3a]` (0x001A8A94)
    u8  field_13c;                      // +0x13C: `strb r7,[r4,#0x13c]` (0x001A8A88)
    u8  field_13d;                      // +0x13D: `strb r7,[r4,#0x13d]` (0x001A8A8C)
    u8  field_13e;                      // +0x13E: `strb r7,[r4,#0x13e]` (0x001A8A98)
    u8  pad_13f[0x01];                  // +0x13F..+0x140
    u32 field_140;                      // +0x140: `str r7,[r4,#0x140]` (0x001A8A9C)
    u8  field_144;                      // +0x144: `strb r7,[r4,#0x144]` (0x001A8AA0)
    u8  pad_145[0x03];                  // +0x145..+0x148
    f32 field_148;                      // +0x148: `vstr s16,[r4,#0x148]` (0x001A8AA4)
    u8  pad_14c[0x20];                  // +0x14C..+0x16C
    u32 field_16c;                      // +0x16C: `str r7,[r4,#0x16c]` (0x001A8A84)
    u32 field_170;                      // +0x170: `str sl,[r4,#0x170]` = 999 (0x001A8AAC)
    u32 field_174;                      // +0x174: `str r7,[r4,#0x174]` (0x001A8AA8)
    u32 field_178;                      // +0x178: `str r7,[r4,#0x178]` (0x001A8AB0)
    u8  field_17c;                      // +0x17C: `strb r7,[r4,#0x17c]` (0x001A8AB8)
    u8  field_17d;                      // +0x17D: `strb r7,[r4,#0x17d]` (0x001A8ABC)
    u8  pad_17e[0x02];                  // +0x17E..+0x180
};
static_assert(offsetof(MapEnemyEntry, index) == 0x004);
static_assert(offsetof(MapEnemyEntry, field_08) == 0x008);
static_assert(offsetof(MapEnemyEntry, field_14) == 0x014);
static_assert(offsetof(MapEnemyEntry, field_30) == 0x030);
static_assert(offsetof(MapEnemyEntry, field_34) == 0x034);
static_assert(offsetof(MapEnemyEntry, field_3c) == 0x03C);
static_assert(offsetof(MapEnemyEntry, field_74) == 0x074);
static_assert(offsetof(MapEnemyEntry, field_8c) == 0x08C);
static_assert(offsetof(MapEnemyEntry, field_138) == 0x138);
static_assert(offsetof(MapEnemyEntry, field_140) == 0x140);
static_assert(offsetof(MapEnemyEntry, field_148) == 0x148);
static_assert(offsetof(MapEnemyEntry, field_16c) == 0x16C);
static_assert(offsetof(MapEnemyEntry, field_170) == 0x170);
static_assert(offsetof(MapEnemyEntry, field_17c) == 0x17C);
static_assert(sizeof(MapEnemyEntry) == 0x180);

/**
 * One 8-byte spawn slot at work+0x304C (`add r1,r6,r0,lsl #3`, 0x001A8ACC).
 */
struct MapEnemySpawn {
    u32 field_00;                       // +0x00: `str r7,[r1]` (0x001A8ADC)
    u8  field_04;                       // +0x04: `strb r7,[r1,#4]` (0x001A8AE0)
    u8  field_05;                       // +0x05: `strb r7,[r1,#5]` (0x001A8AE8)
    u8  pad_06[0x02];                   // +0x06..+0x08
};
static_assert(sizeof(MapEnemySpawn) == 0x08);

/**
 * Enemy manager allocated by `mapEnemy_func_001a8924`.
 * Allocation: 0x30F4 bytes (`ldr r3,[pc,#0x1dc] @ =0x30f4`, 0x001A8948).
 */
struct MapEnemyWork {
    void* task;                         // +0x000: `str r0,[r6]` "MENEMY" (0x001A8998)
    u32 field_004;                      // +0x004: `str r7,[r6,#4]` (0x001A899C)
    u32 field_008;                      // +0x008: `str r7,[r6,#8]` (0x001A89A0)
    u32 field_00c;                      // +0x00C: `str r7,[r6,#0xc]` (0x001A89A8)
    u32 field_010;                      // +0x010: `str r7,[r6,#0x10]` (0x001A89AC)
    u8  pad_014[0x20];                  // +0x014..+0x034
    MapEnemyEntry entries[0x20];        // +0x034..+0x3034
    u32 field_3034;                     // +0x3034: `str r7,[r1,#0x34]`, r1=r6+0x3000
    u32 field_3038;                     // +0x3038: `str r7,[r1,#0x38]` (0x001A89B4)
    u32 field_303c;                     // +0x303C: `str r7,[r1,#0x3c]` (0x001A89B8)
    u32 field_3040;                     // +0x3040: `str r7,[r1,#0x40]` (0x001A89BC)
    u8  pad_3044[0x04];                 // +0x3044..+0x3048
    u8  field_3048;                     // +0x3048: `strb r7,[r1,#0x48]` (0x001A89CC)
    u8  field_3049;                     // +0x3049: `strb r7,[r1,#0x49]` (0x001A89D8)
    u8  pad_304a[0x02];                 // +0x304A..+0x304C
    MapEnemySpawn spawns[0x15];         // +0x304C..+0x30F4
};
static_assert(offsetof(MapEnemyWork, task) == 0x000);
static_assert(offsetof(MapEnemyWork, entries) == 0x034);
static_assert(offsetof(MapEnemyWork, field_3034) == 0x3034);
static_assert(offsetof(MapEnemyWork, field_3048) == 0x3048);
static_assert(offsetof(MapEnemyWork, spawns) == 0x304C);
static_assert(sizeof(MapEnemyWork) == 0x30F4);

// ---------------------------------------------------------------------------
// mapDepart.cpp (0x0027EE6C, 552 B)
// ---------------------------------------------------------------------------

/**
 * Request record consumed by `mapDepart_func_0027ee6c`.  Only the words the
 * listing loads are modelled (`ldr r0,[r5]`, `[r5,#4]`, `[r5,#8]` and the four
 * words copied at 0x0027EF64..0x0027EF80).
 */
struct MapDepartRequest {
    u32 mode;                           // +0x00: `ldr r0,[r5]` (0x0027EEC0)
    u32 field_04;                       // +0x04: `ldr r0,[r5,#4]` (0x0027EEF4)
    u32 field_08;                       // +0x08: `ldr r0,[r5,#8]` (0x0027EF24)
    u8  pad_0c[0x04];                   // +0x0C..+0x10
    u32 field_10;                       // +0x10: `ldr r0,[r5,#0x10]` (0x0027EF64)
    u32 field_14;                       // +0x14: `ldr r0,[r5,#0x14]` (0x0027EF6C)
    u32 field_18;                       // +0x18: `ldr r0,[r5,#0x18]` (0x0027EF74)
    u32 field_1c;                       // +0x1C: `ldr r0,[r5,#0x1c]` (0x0027EF7C)
};
static_assert(offsetof(MapDepartRequest, mode) == 0x00);
static_assert(offsetof(MapDepartRequest, field_04) == 0x04);
static_assert(offsetof(MapDepartRequest, field_10) == 0x10);
static_assert(offsetof(MapDepartRequest, field_1c) == 0x1C);

/**
 * Departure/search host object allocated by `mapDepart_func_0027ee6c`.
 * Allocation: 0x80 bytes (`mov r3,#0x80`, 0x0027EE8C).
 */
struct MapDepartWork {
    void* calc_task;                    // +0x000: `str r0,[r4]` "DEPART C" (0x0027EFC4)
    u8  pad_004[0x04];                  // +0x004..+0x008
    u8  field_008;                      // +0x008: `strb r7,[r4,#8]` (0x0027EF9C)
    u8  pad_009[0x03];                  // +0x009..+0x00C
    u32 field_00c;                      // +0x00C: `str r7,[r4,#0xc]` /
                                        //   `str sb,[r4,#0xc]` (0x0027EEF0..0x0027EF4C)
    u32 field_010;                      // +0x010: `str r0,[r4,#0x10]` (0x0027EEF8)
    u32 field_014;                      // +0x014: `str r0,[r4,#0x14]` (0x0027EF28)
    u8  pad_018[0x30];                  // +0x018..+0x048
    u32 field_048;                      // +0x048: `str r0,[r4,#0x48]` (0x0027EF68)
    u32 field_04c;                      // +0x04C: `str r0,[r4,#0x4c]` (0x0027EF70)
    u32 field_050;                      // +0x050: `str r0,[r4,#0x50]` (0x0027EF78)
    u32 field_054;                      // +0x054: `str r0,[r4,#0x54]` (0x0027EF80)
    u8  pad_058[0x28];                  // +0x058..+0x080
};
static_assert(offsetof(MapDepartWork, calc_task) == 0x000);
static_assert(offsetof(MapDepartWork, field_008) == 0x008);
static_assert(offsetof(MapDepartWork, field_00c) == 0x00C);
static_assert(offsetof(MapDepartWork, field_014) == 0x014);
static_assert(offsetof(MapDepartWork, field_048) == 0x048);
static_assert(offsetof(MapDepartWork, field_054) == 0x054);
static_assert(sizeof(MapDepartWork) == 0x80);

// ---------------------------------------------------------------------------
// 3dEventOpening.cpp (0x002F62D0, 552 B)
// ---------------------------------------------------------------------------

/**
 * Opening-event host allocated by `3dEventOpening_func_002f62d0`.
 * Allocation: 0x574 bytes (`ldr r5,[pc,#0x1b4] @ =0x574`, 0x002F62F4).
 */
struct EventOpeningWork {
    void* calc_task;                    // +0x000: `str r0,[r4]` (0x002F6400)
    AsdCameraProjection projection;     // +0x004..+0x50C: `add r0,r4,#4`
                                        //   (0x002F6328, 0x002F63B4, 0x002F63C8)
    f32 eye[3];                         // +0x50C: r4+0x40C (`add sl,r4,#0x400`+
                                        //   #0x10c, 0x002F6330/0x002F6338)
    f32 target[3];                      // +0x518: r4+0x418 (0x002F633C)
    f32 up[3];                          // +0x524: r4+0x424 (`add sb,r4,#0x400`+
                                        //   #0x124, 0x002F6374)
    f32 perspective[4];                 // +0x530: r4+0x430, loaded by
                                        //   `vldmia r5,{s0,s1,s2,s3}` (0x002F63C4)
    u8  pad_540[0x10];                  // +0x540..+0x550
    f32 field_550;                      // +0x550: `vstr s0,[r5,#0x150]` = 5.0f
                                        //   (0x002F63A0)
    void* model;                        // +0x554: `str r0,[r4,#0x554]!` (0x002F6454)
    u32 field_558;                      // +0x558: `str r5,[r4,#0x558]` (0x002F6430)
    void* cam_loop;                     // +0x55C: `str r0,[r4,#0x55c]` (0x002F6438)
    void* cam_start;                    // +0x560: `str r0,[r4,#0x560]` (0x002F6444)
    u32 field_564;                      // +0x564: `stm r2,{r0,r5}` = 1 (0x002F641C)
    u32 field_568;                      // +0x568: second word of that store = 0
    u8  pad_56c[0x04];                  // +0x56C..+0x570
    u32 field_570;                      // +0x570: `str r8,[r4,#0x1c]`, r4=r4+0x554
                                        //   (0x002F6458)
};
static_assert(offsetof(EventOpeningWork, calc_task) == 0x000);
static_assert(offsetof(EventOpeningWork, projection) == 0x004);
static_assert(offsetof(EventOpeningWork, eye) == 0x50C);
static_assert(offsetof(EventOpeningWork, target) == 0x518);
static_assert(offsetof(EventOpeningWork, up) == 0x524);
static_assert(offsetof(EventOpeningWork, perspective) == 0x530);
static_assert(offsetof(EventOpeningWork, field_550) == 0x550);
static_assert(offsetof(EventOpeningWork, model) == 0x554);
static_assert(offsetof(EventOpeningWork, field_558) == 0x558);
static_assert(offsetof(EventOpeningWork, cam_loop) == 0x55C);
static_assert(offsetof(EventOpeningWork, cam_start) == 0x560);
static_assert(offsetof(EventOpeningWork, field_564) == 0x564);
static_assert(offsetof(EventOpeningWork, field_570) == 0x570);
static_assert(sizeof(EventOpeningWork) == 0x574);

// ---------------------------------------------------------------------------
// mapEpl.cpp (0x001FA408, 468 B; constructor 0x00192298)
// ---------------------------------------------------------------------------

/**
 * One 0x18-byte EPL placement.  The table base is work+8 and the stride is 0x18
 * (`add r0,r1,r1,lsl #1` then `lsl #3`, 0x001FA470..0x001FA478).
 */
struct MapEplEntry {
    f32 pos[3];                         // +0x00: `vstmia r1,{s0,s1,s2}` (0x001FA568)
    f32 rot;                            // +0x0C: `vstr s16,[r1,#0xc]` (0x001FA564)
    void* resource;                     // +0x10: `str r0,[r5,#0x10]` (0x001FA5A0)
    void* parts;                        // +0x14: `str r0,[r5,#0x14]` (0x001FA5AC)
};
static_assert(offsetof(MapEplEntry, pos) == 0x00);
static_assert(offsetof(MapEplEntry, rot) == 0x0C);
static_assert(offsetof(MapEplEntry, resource) == 0x10);
static_assert(offsetof(MapEplEntry, parts) == 0x14);
static_assert(sizeof(MapEplEntry) == 0x18);

/**
 * EPL placement manager allocated by `mapEpl_func_00192298` / lazily by
 * `mapEpl_func_001fa408`.  Allocation: 0x188 bytes
 * (`mov r3,#0x188`, 0x001922B4 / 0x001FA448).
 */
struct MapEplWork {
    u32 field_00;                       // +0x000: `str r2,[r0]` (0x001922D8)
    u32 field_04;                       // +0x004: `str r2,[r0,#4]` (0x001922DC)
    MapEplEntry entries[0x10];          // +0x008..+0x188
};
static_assert(offsetof(MapEplWork, field_00) == 0x000);
static_assert(offsetof(MapEplWork, field_04) == 0x004);
static_assert(offsetof(MapEplWork, entries) == 0x008);
static_assert(sizeof(MapEplWork) == 0x188);

/**
 * One 0x18-byte row of global TBB table 0x2D / sub-table 3, looked up by
 * `engine_func_002c9ba4` (0x002C9BD4 `add r0,r4,r4,lsl #1`, `lsl #3`).
 */
struct MapEplRow {
    s8  group;                          // +0x00: `ldrsb r0,[r0]` (0x001FA4C0)
    s8  index;                          // +0x01: `ldrsb r0,[r7,#1]` (0x001FA4D4)
    s16 x;                              // +0x02: `ldrsh r2,[r7,#2]` (0x001FA524)
    s16 y;                              // +0x04: `ldrsh r0,[r7,#4]` (0x001FA528)
    s16 z;                              // +0x06: `ldrsh r1,[r7,#6]` (0x001FA52C)
    char name[0x10];                    // +0x08: passed as "%s" (0x001FA4E0)
};
static_assert(offsetof(MapEplRow, group) == 0x00);
static_assert(offsetof(MapEplRow, index) == 0x01);
static_assert(offsetof(MapEplRow, x) == 0x02);
static_assert(offsetof(MapEplRow, z) == 0x06);
static_assert(offsetof(MapEplRow, name) == 0x08);
static_assert(sizeof(MapEplRow) == 0x18);

// ---------------------------------------------------------------------------
// mapMain.cpp (0x001B4410, 440 B)
// ---------------------------------------------------------------------------

/**
 * Map script host allocated by `mapMain_func_001b4410`.
 * Allocation: 0xC8 bytes (`mov r3,#0xc8`, 0x001B442C).  The slot itself
 * (0x00447E28) is the "global script manager pointer" documented in
 * `include/script/script_exec.h`.
 */
struct MapMainWork {
    void* calc_task;                    // +0x000: `str r1,[r4]` "MAP C" (0x001B4538)
    void* draw_task;                    // +0x004: `str r0,[r4,#4]` "MAP U" (0x001B4560)
    u8  pad_008[0x04];                  // +0x008..+0x00C
    u8  field_00c;                      // +0x00C: `strb r6,[r4,#0xc]` (0x001B4514)
    u8  field_00d;                      // +0x00D: `strb r6,[r4,#0xd]` (0x001B4460)
    u8  field_00e;                      // +0x00E: `strb r6,[r4,#0xe]` (0x001B4464)
    u8  field_00f;                      // +0x00F: `strb r6,[r4,#0xf]` (0x001B4468)
    u8  field_010;                      // +0x010: `strb r6,[r4,#0x10]` (0x001B446C)
    u8  field_011;                      // +0x011: `strb r6,[r4,#0x11]` (0x001B4470)
    u8  field_012;                      // +0x012: `strb r6,[r4,#0x12]` (0x001B4474)
    u8  field_013;                      // +0x013: `strb r6,[r4,#0x13]` (0x001B4478)
    u8  field_014;                      // +0x014: `strb r6,[r4,#0x14]` (0x001B447C)
    u8  pad_015[0x03];                  // +0x015..+0x018
    u32 field_018;                      // +0x018: `str r6,[r4,#0x18]` (0x001B4480)
    u8  field_01c;                      // +0x01C: `strb r6,[r4,#0x1c]` (0x001B4484)
    u8  field_01d;                      // +0x01D: `strb r6,[r4,#0x1d]` (0x001B4488)
    u8  field_01e;                      // +0x01E: `strb r6,[r4,#0x1e]` (0x001B448C)
    u8  field_01f;                      // +0x01F: `strb r6,[r4,#0x1f]` (0x001B4490)
    u8  field_020;                      // +0x020: `strb r6,[r4,#0x20]` (0x001B4494)
    u8  pad_021[0x03];                  // +0x021..+0x024
    u32 field_024;                      // +0x024: `str r6,[r4,#0x24]` (0x001B44A0)
    u32 field_028;                      // +0x028: `strd r6,r7,[r4,#0x28]` = 0 (0x001B44A4)
    u32 field_02c;                      // +0x02C: second word of that store = 1
    u32 field_030;                      // +0x030: `str r7,[r4,#0x30]` = 1 (0x001B44AC)
    u32 field_034;                      // +0x034: `str r6,[r4,#0x34]` = 0 (0x001B44A8)
    u8  pad_038[0x04];                  // +0x038..+0x03C
    u8  field_03c;                      // +0x03C: `strb r6,[r4,#0x3c]` (0x001B44B0)
    u8  field_03d;                      // +0x03D: `strb r6,[r4,#0x3d]` (0x001B4498)
    u8  pad_03e[0x02];                  // +0x03E..+0x040
    u32 field_040;                      // +0x040: `str r6,[r4,#0x40]` (0x001B449C)
    u8  pad_044[0x02];                  // +0x044..+0x046
    u8  field_046;                      // +0x046: `strb r6,[r4,#0x46]` (0x001B44BC)
    u8  field_047;                      // +0x047: `strb r7,[r4,#0x47]` = 1 (0x001B44B4)
    u8  field_048;                      // +0x048: `strb r6,[r4,#0x48]` (0x001B44B8)
    u8  pad_049[0x5F];                  // +0x049..+0x0A8
    u32 field_0a8;                      // +0x0A8: `stm r1,{r0,r6}` = 0x1c2 (0x001B44E8)
    u32 field_0ac;                      // +0x0AC: second word of that store = 0
    u8  pad_0b0[0x04];                  // +0x0B0..+0x0B4
    u32 field_0b4;                      // +0x0B4: `str r6,[r4,#0xb4]` (0x001B44F4)
    u8  field_0b8;                      // +0x0B8: `strb r6,[r4,#0xb8]` (0x001B44F8)
    u8  field_0b9;                      // +0x0B9: `strb r6,[r4,#0xb9]` (0x001B44FC)
    u8  pad_0ba[0x0A];                  // +0x0BA..+0x0C4
    u32 field_0c4;                      // +0x0C4: `str r6,[r4,#0xc4]` (0x001B450C)
};
static_assert(offsetof(MapMainWork, calc_task) == 0x000);
static_assert(offsetof(MapMainWork, draw_task) == 0x004);
static_assert(offsetof(MapMainWork, field_00c) == 0x00C);
static_assert(offsetof(MapMainWork, field_018) == 0x018);
static_assert(offsetof(MapMainWork, field_024) == 0x024);
static_assert(offsetof(MapMainWork, field_028) == 0x028);
static_assert(offsetof(MapMainWork, field_030) == 0x030);
static_assert(offsetof(MapMainWork, field_03c) == 0x03C);
static_assert(offsetof(MapMainWork, field_046) == 0x046);
static_assert(offsetof(MapMainWork, field_048) == 0x048);
static_assert(offsetof(MapMainWork, field_0a8) == 0x0A8);
static_assert(offsetof(MapMainWork, field_0b4) == 0x0B4);
static_assert(offsetof(MapMainWork, field_0b8) == 0x0B8);
static_assert(offsetof(MapMainWork, field_0c4) == 0x0C4);
static_assert(sizeof(MapMainWork) == 0xC8);

// ---------------------------------------------------------------------------
// naviMain.cpp (0x00291CAC, 412 B)
// ---------------------------------------------------------------------------

/**
 * 0x10-byte fade controller at NaviMainWork+0x12334.
 *
 * `engine_func_003c2c58` (0x003C2C58) writes +0x00, +0x04, +0x08..+0x0B and
 * +0x0C; the fade-start entry at 0x003C2C20 (inside ui_func_003c2b10) writes
 * +0x08/+0x0A/+0x0B and the state word at +0x04.
 */
struct NaviFade {
    u8  field_00;                       // +0x00: `strb r2,[r0]` (0x003C2C74)
    u8  pad_01[0x03];                   // +0x01..+0x04
    u32 state;                          // +0x04: `str r2,[r0,#4]` (0x003C2C60)
    u8  field_08;                       // +0x08: `strb r2,[r0,#8]` (0x003C2C64)
    u8  field_09;                       // +0x09: `strb r2,[r0,#9]` (0x003C2C68)
    u8  field_0a;                       // +0x0A: `strb r2,[r0,#0xa]` (0x003C2C6C)
    u8  field_0b;                       // +0x0B: `strb r2,[r0,#0xb]` (0x003C2C70)
    u8  field_0c;                       // +0x0C: `strb r1,[r0,#0xc]` (0x003C2C5C)
    u8  pad_0d[0x03];                   // +0x0D..+0x10
};
static_assert(offsetof(NaviFade, state) == 0x04);
static_assert(offsetof(NaviFade, field_0a) == 0x0A);
static_assert(offsetof(NaviFade, field_0c) == 0x0C);
static_assert(sizeof(NaviFade) == 0x10);

/**
 * Map-navigation host allocated by `naviMain_func_00291cac`.
 * Allocation: 0x12344 bytes (`ldr r3,[pc,#0x144] @ =0x12344`, 0x00291CCC).
 */
struct NaviMainWork {
    void* proc_task;                    // +0x000: `str r0,[r4]` "NAVI PROC" (0x00291D78)
    void* down_task;                    // +0x004: `str r0,[r4,#4]` "NAVI DOWN" (0x00291DA4)
    u8  field_008;                      // +0x008: `strb r6,[r0,#8]` (0x00291D24)
    u8  field_009;                      // +0x009: `strb r6,[r0,#9]` (0x00291CF8)
    u8  field_00a;                      // +0x00A: `strb r6,[r0,#0xa]` (0x00291CF4)
    u8  pad_00b[0x01];                  // +0x00B..+0x00C
    u32 field_00c;                      // +0x00C: `str r6,[r0,#0xc]` (0x00291CFC)
    u32 field_010;                      // +0x010: `str r6,[r0,#0x10]` (0x00291D00)
    u32 field_014;                      // +0x014: `str r6,[r0,#0x14]` (0x00291D04)
    f32 field_018;                      // +0x018: `vstr s0,[r0,#0x18]` = 0.0f (0x00291D08)
    u8  pad_01c[0x0C];                  // +0x01C..+0x028
    u32 field_028;                      // +0x028: `str r8,[r0,#0x28]` = 1 (0x00291D10)
    u32 field_02c;                      // +0x02C: `str r6,[r0,#0x2c]` = 0 (0x00291D0C)
    u8  pad_030[0x04];                  // +0x030..+0x034
    f32 field_034;                      // +0x034: `vstr s1,[r0,#0x34]` = 1.0f (0x00291D14)
    f32 field_038;                      // +0x038: `vstr s0,[r0,#0x38]` = 0.0f (0x00291D18)
    f32 field_03c;                      // +0x03C: `vstr s0,[r0,#0x3c]` = 0.0f (0x00291D1C)
    u8  object_040[0x122F0];            // +0x040..+0x12330: `add r0,r4,#0x40`
                                        //   handed to 0x00399594 (0x00291D28)
    void* fade_task;                    // +0x12330: `str r0,[r1,r4]`, r1=0x12330
                                        //   (0x00291DD0)
    NaviFade fade;                      // +0x12334..+0x12344: `add r0,r4,#0x12000`
                                        //   then `add r0,r0,#0x334` (0x00291DD4)
};
static_assert(offsetof(NaviMainWork, proc_task) == 0x000);
static_assert(offsetof(NaviMainWork, down_task) == 0x004);
static_assert(offsetof(NaviMainWork, field_008) == 0x008);
static_assert(offsetof(NaviMainWork, field_018) == 0x018);
static_assert(offsetof(NaviMainWork, field_028) == 0x028);
static_assert(offsetof(NaviMainWork, field_034) == 0x034);
static_assert(offsetof(NaviMainWork, object_040) == 0x040);
static_assert(offsetof(NaviMainWork, fade_task) == 0x12330);
static_assert(offsetof(NaviMainWork, fade) == 0x12334);
static_assert(sizeof(NaviMainWork) == 0x12344);

// ---------------------------------------------------------------------------
// NkmGrowEvent.cpp (0x0033BB94, 564 B)
// ---------------------------------------------------------------------------

/**
 * One 4-byte row of global TBB table 6 / sub-table 1, selected by
 * `camp_func_0029ec14` (element size 4, 0x0029EC58).  The growth event reads
 * only byte +3: bit 0x80 marks a candidate and bits 0x1F hold its rank.
 */
struct NkmGrowState {
    u8  field_00;                       // +0x00: never read here
    u8  field_01;                       // +0x01
    u8  field_02;                       // +0x02
    u8  field_03;                       // +0x03: `ldrb r0,[r0,#3]` (0x0033BBF4)
};
static_assert(offsetof(NkmGrowState, field_03) == 0x03);
static_assert(sizeof(NkmGrowState) == 0x04);

/**
 * One 0x94-byte row of global TBB table 0 / sub-table 0, selected by
 * `Battle_GetTalkEntry` (`mov r3,#0x94`, 0x002B938C).
 *
 * The eight party member ids sit at +0x3C..+0x4C (`ldrh r0,[r0,#0x3c]` with
 * `add r0,r6,r4,lsl #1`) and the eight associated level words at +0x4E..+0x6E
 * (`ldrh r0,[r6,#0x4e]`, then +4 per entry, 0x0033BC38..0x0033BC78).
 */
struct NkmGrowEntry {
    u8  pad_00[0x3C];                   // +0x00..+0x3C
    u16 members[8];                     // +0x3C..+0x4C
    u8  pad_4c[0x02];                   // +0x4C..+0x4E
    struct {
        u16 value;                      // +0x00: `ldrh r0,[r6,#0x4e]` (0x0033BC38)
        u16 pad;                        // +0x02: skipped by the +4 stride
    } levels[8];                        // +0x4E..+0x6E
    u8  pad_6e[0x26];                   // +0x6E..+0x94
};
static_assert(offsetof(NkmGrowEntry, members) == 0x3C);
static_assert(offsetof(NkmGrowEntry, levels) == 0x4E);
static_assert(sizeof(NkmGrowEntry) == 0x94);

/**
 * Growth-event actor.  Only the eight owned ids and the species id are read by
 * the listing; the object is owned by the caller, so the rest is a prefix.
 */
struct NkmGrowEventWork {
    u8  pad_00[0x34];                   // +0x00..+0x34
    u16 owned[8];                       // +0x34..+0x44: `ldrh r1,[r1,#0x34]`
                                        //   (0x0033BD28) / `strh r4,[r0,#0x34]`
    u16 pad_44;                         // +0x44
    u16 species;                        // +0x46: `ldrh r0,[r7,#0x46]` (0x0033BBCC)
};
static_assert(offsetof(NkmGrowEventWork, owned) == 0x34);
static_assert(offsetof(NkmGrowEventWork, species) == 0x46);

// ---------------------------------------------------------------------------
// Reconstructed entry points
// ---------------------------------------------------------------------------

// 0x001D2B14 (760 B): create the large-map host and its "LMAP C"/"LMAP U"
// tasks.
void  lmapMain_func_001d2b14();

// 0x0018ABA8 (696 B): create the map interface tasks and the three projection
// quads, then enter script_vm_func_00297c9c.
void  mapIf_func_0018aba8(void* parent, u32 flag);

// 0x001A8924 (552 B): create the "MENEMY" enemy manager and clear its 0x20
// records and 0x15 spawn slots.
void  mapEnemy_func_001a8924(void* parent);

// 0x0027EE6C (552 B): departure/search host for the three map transitions.
void  mapDepart_func_0027ee6c(const MapDepartRequest* request);

// 0x002F62D0 (552 B): lazily create the opening-event camera, env, cam tracks
// and loop model; returns the calc-task handle.
void* EventOpening3d_func_002f62d0();

// 0x001FA408 (468 B): load and place the `effect_editor/%s.EPL` entries that
// match (group, index).
void  mapEpl_func_001fa408(u32 group, u32 index);

// 0x001B4410 (440 B): create the "MAP C"/"MAP U" script host and reset the
// map sub-managers.
void  mapMain_func_001b4410();

// 0x00291CAC (412 B): create the "NAVI PROC"/"NAVI DOWN"/"NAVI FADE DRAW"
// tasks and start the navigation fade.
void  naviMain_func_00291cac(u32 arg0, u32 arg1);

// 0x0033BB94 (564 B): pick one reinforced party id for the growth event.
u16   NkmGrowEvent_func_0033bb94(NkmGrowEventWork* work);

// ---------------------------------------------------------------------------
// Globals (addresses are the storage locations used by the listing)
// ---------------------------------------------------------------------------

extern LmapMainWork* g_LmapMainWork;                // 0x00447060 (BSS)
extern MapSceneView* g_MapSceneView;                // 0x00447E88 (BSS slot)
extern MapIfWork* g_MapIfWork;                      // 0x00447A78 (BSS)
extern MapEnemyWork* g_MapEnemyWork;                // 0x00447600 (BSS)
extern MapDepartWork* g_MapDepartWork;              // 0x004475B8 (BSS)
extern MapEplWork* g_MapEplWork;                    // 0x00447A10 (BSS)
extern MapMainWork* g_MapMainWork;                  // 0x00447E28 (BSS)
extern EventOpeningWork* g_EventOpeningWork;        // 0x0043DF98 (.data)
extern NaviMainWork* g_NaviMainWork;                // 0x0044CDF0 (BSS)

extern MapIfProjectionTables g_MapIfProjectionTables;   // 0x004B5D30 (BSS)

/**
 * Shared map/script runtime block at 0x0049F91C.
 *
 * mapDepart compares the dword at +0x00 with 100 (`ldr r0,[r8]`,
 * 0x0027EF04), while mapMain and lmapMain clear byte +0x22B
 * (`strb r6,[r0,#0x22b]`, 0x001B4500 / 0x001D2D14).  Only those two accesses
 * are proven, so the array is sized to the highest byte touched.
 */
extern u8 g_MapRuntimeState[0x22C];                 // 0x0049F91C (BSS)

} // namespace smt4::engine
