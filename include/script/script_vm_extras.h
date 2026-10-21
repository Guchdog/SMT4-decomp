#pragma once
#include <cstddef>
#include "types.h"

/**
 * Script-VM extras: four large routines that sit on top of the FlowScript
 * bytecode engine but drive the world-map / event camera and the map-marker
 * render list.
 *
 * Every field below is an observed access in the ARM listing of this file;
 * the comment cites the pointer expression (`ldr`/`str`/`vldr`/`vstr`) that
 * proves the offset.  Objects owned by other translation units are modelled
 * as opaque prefixes and deliberately have no `sizeof` assertion.
 */

namespace smt4::script {

// ---------------------------------------------------------------------------
// 0x0049F130: script camera work object (`g_ScriptCameraWork`)
//
// The pointer lives in .data at 0x004474F4 (`ldr r1,[r8,#4]`, r8 =
// 0x004474F0 at 0x00276CBC/0x00276D60 inside 0x00276CAC).
// ---------------------------------------------------------------------------

/**
 * The per-camera-preset "cut" block at work+0x220.  The target is read at
 * +0x30 (`add r0,r4,#0x30`, 0x00277150) and the eye at +0x3C
 * (`add r0,r4,#0x3c`, 0x0027714C).
 */
struct ScriptCameraCut {
    u8  pad_00[0x30];
    f32 target[3];                      // +0x30: `add r0,r4,#0x30` (0x00277150)
    f32 eye[3];                         // +0x3C: `add r0,r4,#0x3c` (0x0027714C)
    u8  pad_48[0x2C];                   // +0x48..+0x74
};
static_assert(offsetof(ScriptCameraCut, target) == 0x30);
static_assert(offsetof(ScriptCameraCut, eye) == 0x3C);

struct ScriptCameraWork {
    s32 mode;                           // +0x000: `ldr r1,[r0]` (0x00276F30)
    u8  pad_004[0x14];
    f32 angle;                          // +0x018: `vldr s0,[r0,#0x18]` (0x002772A4)
    u8  pad_01c;
    u8  preset_bias;                    // +0x01D: `ldrb r0,[r0,#0x1d]` (0x00277274)
    u8  pad_01e[0x16];
    f32 eye[3];                         // +0x034: `vstr s0,[r0,#0x34]` (0x00277508)
    f32 target[3];                      // +0x040: `vstr s0,[r0,#0x40]` (0x0027750C)
    f32 blend_eye[3];                   // +0x04C: `vstr s1,[r0,#0x4c]` (0x00277C84)
    f32 blend_target[3];                // +0x058: `vstr s1,[r0,#0x58]` (0x00277C78)
    f32 alt_eye_a[3];                   // +0x064: `vldmia r0,{s0..s5}` (0x00277048)
    f32 alt_target_a[3];                // +0x070
    f32 alt_fov_a;                      // +0x07C: `vldr s0,[r0,#0x7c]` (0x00277030)
    f32 alt_eye_b[3];                   // +0x080: `vldmia r0,{s0..s5}` (0x002770E4)
    f32 alt_target_b[3];                // +0x08C
    f32 far_clip;                       // +0x098: `vldr s1,[r0,#0x98]` (0x00276FB4)
    f32 blend_distance;                 // +0x09C: `vldr s0,[r0,#0x9c]` (0x00277770)
    f32 blend_speed;                    // +0x0A0: `vldr s0,[r0,#0xa0]` (0x00277784)
    u8  hold_flag;                      // +0x0A4: `ldrb r1,[r0,#0xa4]` (0x00277750)
    u8  pad_0a5[3];
    s32 hold_timer;                     // +0x0A8: `ldr r1,[r0,#0xa8]` (0x00277768)
    s32 cut_animation;                  // +0x0AC: `ldr r1,[r0,#0xac]` (0x002778B4)
    u8  pad_0b0[0x14];
    u32 saved_camera_id;                // +0x0C4: `ldr r4,[r1,#0xc4]` (0x002771E0)
    f32 preset_offset_y[16];            // +0x0C8: `vldr s1,[r0,#0xc8]` (0x002772FC)
    f32 preset_eye_y[16];               // +0x108: `vldr s1,[r1,#0x108]` (0x0027730C)
    f32 preset_side[16];                // +0x148: `vldr s2,[r1,#0x148]` (0x00277334)
    f32 preset_distance[16];            // +0x188: `vldr s2,[r2,#0x188]` (0x002772C0)
    f32 preset_fov[16];                 // +0x1C8: `vldr s0,[r0,#0x1c8]` (0x00277D34)
    s32 camera_id;                      // +0x208: `ldr r2,[r1,#0x208]` (0x002771DC)
    u8  pad_20c[8];
    f32 desired_height;                 // +0x214: `vldr s0,[r0,#0x214]` (0x002773F4)
    f32 current_height;                 // +0x218: `vldr s2,[r0,#0x218]` (0x002773EC)
    u8  snap_from_model;                // +0x21C: `ldrb r2,[r0,#0x21c]` (0x00276F54)
    u8  pad_21d[3];
    ScriptCameraCut cut;                // +0x220: `add r4,r0,#0x220` (0x00276F78)
    f32 shake_offset[3];                // +0x294: `vstr s0,[r0,#0x294]` (0x00276E34)
    u32 shake_active;                   // +0x2A0: `ldr r2,[r1,#0x2a0]` (0x00276D70)
    u8  pad_2a4[4];
    s16 shake_timer;                    // +0x2A8: `ldrh r2,[r0,#0xa8]` with
                                        // r0 = work+0x200 (0x00276D7C)
    u16 shake_angle_x;                  // +0x2AA: `ldrh r1,[r0,#0xaa]` (0x00276DB0)
    u16 shake_angle_y;                  // +0x2AC: `ldrh r1,[r0,#0xac]` (0x00276DC0)
    u16 shake_angle_z;                  // +0x2AE: `ldrh r0,[r0,#0xae]` (0x00276DC4)
    u8  snap_positions;                 // +0x2B0: `ldrb r2,[r1,#0x2b0]` (0x00276CCC)
    u8  pad_2b1[3];
    void* model;                        // +0x2B4: `ldr r1,[r1,#0x2b4]` (0x00276CD8)
    u8  track_target;                   // +0x2B8: `ldrb r1,[r0,#0x2b8]` (0x00277554)
    u8  pad_2b9[3];
};
static_assert(offsetof(ScriptCameraWork, mode) == 0x000);
static_assert(offsetof(ScriptCameraWork, angle) == 0x018);
static_assert(offsetof(ScriptCameraWork, preset_bias) == 0x01D);
static_assert(offsetof(ScriptCameraWork, eye) == 0x034);
static_assert(offsetof(ScriptCameraWork, target) == 0x040);
static_assert(offsetof(ScriptCameraWork, blend_eye) == 0x04C);
static_assert(offsetof(ScriptCameraWork, blend_target) == 0x058);
static_assert(offsetof(ScriptCameraWork, alt_eye_a) == 0x064);
static_assert(offsetof(ScriptCameraWork, alt_target_a) == 0x070);
static_assert(offsetof(ScriptCameraWork, alt_fov_a) == 0x07C);
static_assert(offsetof(ScriptCameraWork, alt_eye_b) == 0x080);
static_assert(offsetof(ScriptCameraWork, alt_target_b) == 0x08C);
static_assert(offsetof(ScriptCameraWork, far_clip) == 0x098);
static_assert(offsetof(ScriptCameraWork, blend_distance) == 0x09C);
static_assert(offsetof(ScriptCameraWork, blend_speed) == 0x0A0);
static_assert(offsetof(ScriptCameraWork, hold_flag) == 0x0A4);
static_assert(offsetof(ScriptCameraWork, hold_timer) == 0x0A8);
static_assert(offsetof(ScriptCameraWork, cut_animation) == 0x0AC);
static_assert(offsetof(ScriptCameraWork, saved_camera_id) == 0x0C4);
static_assert(offsetof(ScriptCameraWork, preset_fov) == 0x1C8);
static_assert(offsetof(ScriptCameraWork, camera_id) == 0x208);
static_assert(offsetof(ScriptCameraWork, desired_height) == 0x214);
static_assert(offsetof(ScriptCameraWork, current_height) == 0x218);
static_assert(offsetof(ScriptCameraWork, snap_from_model) == 0x21C);
static_assert(offsetof(ScriptCameraWork, cut) == 0x220);
static_assert(offsetof(ScriptCameraWork, shake_offset) == 0x294);
static_assert(offsetof(ScriptCameraWork, shake_active) == 0x2A0);
static_assert(offsetof(ScriptCameraWork, shake_timer) == 0x2A8);
static_assert(offsetof(ScriptCameraWork, shake_angle_x) == 0x2AA);
static_assert(offsetof(ScriptCameraWork, shake_angle_y) == 0x2AC);
static_assert(offsetof(ScriptCameraWork, shake_angle_z) == 0x2AE);
static_assert(offsetof(ScriptCameraWork, snap_positions) == 0x2B0);
static_assert(offsetof(ScriptCameraWork, model) == 0x2B4);
static_assert(offsetof(ScriptCameraWork, track_target) == 0x2B8);

extern ScriptCameraWork* g_ScriptCameraWork;      // 0x004474F4 -> 0x0049F130

// ---------------------------------------------------------------------------
// 0x004BCCD0: event/scene camera (view over smt4::engine::g_MapSceneView)
//
// The canonical pointer lives in .data at 0x00447E88 and is declared as
// `g_MapSceneView` in engine/map_runtime.h.  Its observed initial value is
// 0x004BCCD0.  Its position (+0x1C..+0x24) is returned by 0x002327EC
// (`add r0,r0,#0x1c`), which both routines use.
// ---------------------------------------------------------------------------

struct ScriptCamera {
    u8  pad_000[4];
    s32 state;                          // +0x004: `ldr r1,[r0,#4]` (0x002C8C80)
    s32 frame;                          // +0x008: `ldr r1,[r0,#8]` (0x002C8D88)
    u8  pad_00c[0x10];
    f32 position[3];                    // +0x01C: `vldr s17,[r0,#0x1c]` (0x0025BED0)
    f32 route_position[3];              // +0x028: `vldr s18,[r0,#0x28]` (0x002C8D00)
    f32 saved_position[3];              // +0x034: `vstr s18,[r2,#0x34]`
                                        //   (0x002C8F48) / `[r0,#0x34]`
                                        //   (0x002C9130)
    f32 previous_position[3];           // +0x040: `stm r3,{r1,r2}` (0x002C9128)
    f32 yaw;                            // +0x04C: `vldr s0,[r0,#0x4c]` (0x002C9184)
    f32 route_angle;                    // +0x050: `vldr s0,[r0,#0x50]` (0x002C8EEC)
    s32 field_054;                      // +0x054: `str r1,[r0,#0x54]` (0x002C8D6C)
    f32 field_058;                      // +0x058: `vstr s0,[r0,#0x58]` (0x002C8D74)
    u8  field_05c;                      // +0x05C: `strb r7,[r0,#0x5c]` (0x002C8D78)
    u8  pad_05d[0x0B];
    f32 field_068;                      // +0x068: `vstr s22,[r1,#0x68]` (0x002C8FB4)
    u8  field_06c;                      // +0x06C: `strb r6,[r0,#0x6c]` (0x002C8D30)
    u8  pad_06d[0xEF];
    f32 field_15c;                      // +0x15C: `vldr s0,[r0,#0x15c]` (0x002C96AC)
    f32 field_160;                      // +0x160: `vldr s1,[r0,#0x160]` (0x002C8FFC)
    u8  pad_164[4];
    s32 field_168;                      // +0x168: `str r6,[r1,#0x168]` (0x002C955C)
    s32 field_16c;                      // +0x16C: `str r2,[r1,#0x16c]` (0x002C9554)
    u8  pad_170[0x18];
    u32 field_188;                      // +0x188: `strgt r7,[r0,#0x188]` (0x002C99CC)
    u32 field_18c;                      // +0x18C: `str r2,[r4,#0x18c]` (0x002C96FC)
    u32 field_190;                      // +0x190: `stm r1,{r0,r2}` (0x002C9700)
};
static_assert(offsetof(ScriptCamera, state) == 0x004);
static_assert(offsetof(ScriptCamera, frame) == 0x008);
static_assert(offsetof(ScriptCamera, position) == 0x01C);
static_assert(offsetof(ScriptCamera, route_position) == 0x028);
static_assert(offsetof(ScriptCamera, saved_position) == 0x034);
static_assert(offsetof(ScriptCamera, previous_position) == 0x040);
static_assert(offsetof(ScriptCamera, yaw) == 0x04C);
static_assert(offsetof(ScriptCamera, route_angle) == 0x050);
static_assert(offsetof(ScriptCamera, field_054) == 0x054);
static_assert(offsetof(ScriptCamera, field_058) == 0x058);
static_assert(offsetof(ScriptCamera, field_05c) == 0x05C);
static_assert(offsetof(ScriptCamera, field_068) == 0x068);
static_assert(offsetof(ScriptCamera, field_06c) == 0x06C);
static_assert(offsetof(ScriptCamera, field_15c) == 0x15C);
static_assert(offsetof(ScriptCamera, field_160) == 0x160);
static_assert(offsetof(ScriptCamera, field_168) == 0x168);
static_assert(offsetof(ScriptCamera, field_16c) == 0x16C);
static_assert(offsetof(ScriptCamera, field_188) == 0x188);
static_assert(offsetof(ScriptCamera, field_18c) == 0x18C);
static_assert(offsetof(ScriptCamera, field_190) == 0x190);

// ---------------------------------------------------------------------------
// 0x0049F91C: FlowScript event state (view over smt4::engine::g_MapRuntimeState)
//
// Only the bytes/words touched by these four routines are declared.  The
// canonical storage is `g_MapRuntimeState` (0x3E4 bytes) in
// engine/map_runtime.h; the +0x3E0 debug-force dword is its last field and
// the +0x3CC access below stays inside that block.
// ---------------------------------------------------------------------------

struct ScriptEventState {
    u8  pad_000[0x21];
    u8  field_021;                      // +0x021: `ldrb r1,[sb,#0x21]` (0x002C8F60)
    u8  pad_022[3];
    u8  field_025;                      // +0x025: `ldrb r0,[r4,#0x25]` (0x00399FDC)
    u8  pad_026[8];
    s8  field_02e;                      // +0x02E: `ldrsb r1,[r1,#0x2e]` (0x0025BF18)
    u8  field_02f;                      // +0x02F: `strb r0,[r8,#0x2f]` (0x002805F4)
    u8  field_030;                      // +0x030: `strb r2,[r8,#0x30]` (0x002807A8)
    u8  field_031;                      // +0x031: `strb r0,[r8,#0x31]` (0x002805F8)
    u8  field_032;                      // +0x032: `strb r2,[r8,#0x32]` (0x002807B0)
    u8  field_033;                      // +0x033: `strb sl,[sb,#0x33]` (0x002C9048)
    u8  pad_034[0x148];                 // +0x034..+0x17B
    u8  field_17c;                      // +0x17C: `strb r7,[r4,#0x17c]` (0x002C9560)
    u8  pad_17d[3];
    f32 arrival_x;                      // +0x180: `stm r5,{r2,r3,ip}` (0x002C956C)
    f32 arrival_y;                      // +0x184
    f32 arrival_z;                      // +0x188
    f32 arrival_yaw;                    // +0x18C: `str r2,[r4,#0x18c]` (0x002C9574)
    u8  pad_190[0x10];                  // +0x190..+0x19F
    u8  field_1a0;                      // +0x1A0: `strbgt r7,[r4,#0x1a0]` (0x002C9634)
    u8  pad_1a1[3];
    s32 field_1a4;                      // +0x1A4: `strgt r6,[r4,#0x1a4]` (0x002C9638)
    u8  pad_1a8[0x70];                  // +0x1A8..+0x217
    s32 field_218;                      // +0x218: `ldr r0,[sb,#0x218]` (0x002C8D34)
    u8  pad_21c[0x154];
    s32 field_370;                      // +0x370: `ldr r1,[r1,#0x370]` (0x00277550)
    u8  pad_374[0x58];
    u8  field_3cc;                      // +0x3CC: `ldrb r1,[r1,#0x3cc]` (0x00277540)
    u8  pad_3cd[3];
    s32 field_3d0;                      // +0x3D0: `str r0,[sl,#0x3d0]` (0x0027F73C)
    s32 field_3d4;                      // +0x3D4: `str r0,[sl,#0x3d4]` (0x0027F74C)
    u8  pad_3d8[8];
    s32 field_3e0;                      // +0x3E0: `ldr r0,[r0,#0x3e0]` (0x0039A2B8)
};
static_assert(offsetof(ScriptEventState, field_021) == 0x021);
static_assert(offsetof(ScriptEventState, field_025) == 0x025);
static_assert(offsetof(ScriptEventState, field_02e) == 0x02E);
static_assert(offsetof(ScriptEventState, field_033) == 0x033);
static_assert(offsetof(ScriptEventState, field_17c) == 0x17C);
static_assert(offsetof(ScriptEventState, arrival_x) == 0x180);
static_assert(offsetof(ScriptEventState, arrival_y) == 0x184);
static_assert(offsetof(ScriptEventState, arrival_z) == 0x188);
static_assert(offsetof(ScriptEventState, arrival_yaw) == 0x18C);
static_assert(offsetof(ScriptEventState, field_1a0) == 0x1A0);
static_assert(offsetof(ScriptEventState, field_1a4) == 0x1A4);
static_assert(offsetof(ScriptEventState, field_218) == 0x218);
static_assert(offsetof(ScriptEventState, field_370) == 0x370);
static_assert(offsetof(ScriptEventState, field_3cc) == 0x3CC);
static_assert(offsetof(ScriptEventState, field_3d0) == 0x3D0);
static_assert(offsetof(ScriptEventState, field_3d4) == 0x3D4);
static_assert(offsetof(ScriptEventState, field_3e0) == 0x3E0);

// ---------------------------------------------------------------------------
// 0x0044CDF0 world-map/navi context is owned by src/engine/map_runtime.cpp as
// `smt4::engine::g_NaviMainWork`; no duplicate declaration here.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// World-map work buffer shared by 0x00399F28 / 0x0039D8B8
//
// The buffer starts with the UI fields; the marker/command banks below are
// addressed with `r8 + constant` in 0x0039D8B8:
//   +0x0E88 marker bank A (stride 0x4C): `add r1,r1,#0xc00; add r1,r1,#0x288`
//   +0x5A88 marker A count:            `str sl,[r0,r8]` with r0=0x5A88
//   +0x5A90 marker bank B (stride 0x4C): `add r1,r1,#0x5000; add r1,r1,#0xa90`
//   +0x61B0 marker B count:            `str r0,[r1,#0x1b0]` with r1=work+0x6000
//   +0x61B4 command bank (stride 0x30): `add r0,r8,r0,lsl #4` with 3*index
//   +0x121B4 command count:            `str r4,[r0,r8]` with r0=0x121B4
// ---------------------------------------------------------------------------

/** One 0x4C-byte map marker record (banks A/B). */
struct MapMarker {
    u32 object;                         // +0x00: `str r2,[r1]` (0x0039DA84)
    u8  kind;                           // +0x04: `strb r2,[r1,#4]` (0x0039DAA4)
    u8  palette;                        // +0x05: `strb r2,[r1,#5]` (0x0039DABC)
    u16 field_006;                      // +0x06: `strh r2,[r1,#6]` (0x0039DAC4)
    u16 field_008;                      // +0x08: `strh sb,[r1,#8]` (0x0039DAD8)
    u16 field_00A;                      // +0x0A: `strh fp,[r1,#0xa]` (0x0039DAFC)
    f32 x;                              // +0x0C: `vstr s2,[r1,#0xc]` (0x0039DADC)
    f32 y;                              // +0x10: `vstr s4,[r1,#0x10]` (0x0039DAE0)
    f32 z;                              // +0x14: `vstr s0,[r1,#0x14]` (0x0039DAEC)
    f32 field_018;                      // +0x18: `vstr s0,[r1,#0x18]` (0x0039DAF8)
    f32 field_01C;                      // +0x1C: `vstr s3,[r1,#0x1c]` (0x0039DB00)
    f32 field_020;                      // +0x20: `vstr s1,[r1,#0x20]` (0x0039DB04)
    f32 field_024;                      // +0x24: `vstr s0,[r1,#0x24]` (0x0039DB10)
    f32 field_028;                      // +0x28: `vstr s0,[r1,#0x28]` (0x0039DB1C)
    u16 sprite;                         // +0x2C: `strh r2,[r1,#0x2c]` (0x0039DAB4)
    u16 field_02E;                      // +0x2E: `strh r1,[r5,#0x2e]` (0x0039DE4C)
    u16 field_030;                      // +0x30: `strh r3,[r1,#0x30]` (0x0039DACC)
    u16 field_032;                      // +0x32: `strh r3,[r1,#0x32]` (0x0039DAD4)
    u16 visible;                        // +0x34: `strh r3,[r1,#0x34]` (0x0039DB20)
    u16 field_036;                      // +0x36: `strh r0,[r4,#0x36]` (0x0039EF2C)
    f32 field_038;                      // +0x38: `vldr s0,[r4,#0x38]` (0x0039EB90)
    f32 field_03C;                      // +0x3C: `vldr s0,[r4,#0x3c]` (0x0039EB68)
    u32 field_040;                      // +0x40: `ldrd r0,r1,[r4,#0x40]` (0x0039EB70)
    u32 field_044;                      // +0x44
    s32 field_048;                      // +0x48: `str ip,[r1,#0x48]` (0x0039DB24)
};
static_assert(offsetof(MapMarker, object) == 0x00);
static_assert(offsetof(MapMarker, kind) == 0x04);
static_assert(offsetof(MapMarker, palette) == 0x05);
static_assert(offsetof(MapMarker, field_006) == 0x06);
static_assert(offsetof(MapMarker, field_008) == 0x08);
static_assert(offsetof(MapMarker, field_00A) == 0x0A);
static_assert(offsetof(MapMarker, x) == 0x0C);
static_assert(offsetof(MapMarker, z) == 0x14);
static_assert(offsetof(MapMarker, sprite) == 0x2C);
static_assert(offsetof(MapMarker, field_02E) == 0x2E);
static_assert(offsetof(MapMarker, visible) == 0x34);
static_assert(offsetof(MapMarker, field_036) == 0x36);
static_assert(offsetof(MapMarker, field_048) == 0x48);
static_assert(sizeof(MapMarker) == 0x4C);

/** One 0x30-byte world-map command record (0x0039D8B8 marker builder). */
struct MapCommand {
    u8  kind;                           // +0x00: `strb fp,[r0]` (0x0039E6DC)
    u8  field_001;                      // +0x01: `strb sl,[r0,#1]` (0x0039E4B0)
    u8  field_002;                      // +0x02: `strb fp,[r0,#2]` (0x0039E4C0)
    u8  field_003;                      // +0x03: `strb fp,[r0,#3]` (0x0039E4D4)
    u8  field_004;                      // +0x04: `strb r1,[r0,#4]` (0x0039E700)
    u8  field_005;                      // +0x05: `strb r1,[r0,#5]` (0x0039E708)
    u16 field_006;                      // +0x06: `strh sb,[r0,#6]` (0x0039E4C8)
    s32 field_008;                      // +0x08: `str sb,[r0,#8]` (0x0039E70C)
    f32 field_00C;                      // +0x0C: `vstr s0,[r0,#0xc]` (0x0039E71C)
    f32 field_010;                      // +0x10: `vstr s0,[r0,#0x10]` (0x0039E72C)
    f32 field_014;                      // +0x14: `vstr s0,[r0,#0x14]` (0x0039E73C)
    f32 field_018;                      // +0x18: `vstr s0,[r0,#0x18]` (0x0039E74C)
    u8  pad_01c[0x10];
    f32 field_02C;                      // +0x2C: `vstr s16,[r0,#0x2c]` (0x0039E750)
};
static_assert(offsetof(MapCommand, field_008) == 0x08);
static_assert(offsetof(MapCommand, field_00C) == 0x0C);
static_assert(offsetof(MapCommand, field_02C) == 0x2C);
static_assert(sizeof(MapCommand) == 0x30);

struct WorldMapWork {
    u8  pad_000[0x10];
    u32 flags;                          // +0x010: `ldr r0,[r4,#0x10]` (0x00399F98)
    u8  pad_014[0x14E];
    u16 ui_handle;                      // +0x162: `add r0,r0,#0x162` (0x00399F3C)
    f32 origin_x;                       // +0x164: `add r0,r0,#0x164` (0x00399F7C)
    f32 origin_y;                       // +0x168: `str r0,[r1,#4]` (0x00231D58)
    u8  pad_16c[0xA1C];
    s32 sprite_table[64][2];            // +0xB88: `ldr r3,[r1,#0xb88]` (0x0039DCA8)
    u8  pad_d88[0x100];
    MapMarker markers_a[256];           // +0x0E88
    u32 marker_count;                   // +0x5A88: `str sl,[r0,r8]` (0x0039E26C)
    u32 pad_5a8c;
    MapMarker markers_b[24];            // +0x5A90
    u32 line_count;                     // +0x61B0: `str r0,[r1,#0x1b0]` (0x0039E274)
    MapCommand commands[1024];          // +0x61B4
    u32 command_count;                  // +0x121B4: `str r4,[r0,r8]` (0x0039E770)
};
static_assert(offsetof(WorldMapWork, flags) == 0x010);
static_assert(offsetof(WorldMapWork, ui_handle) == 0x162);
static_assert(offsetof(WorldMapWork, origin_x) == 0x164);
static_assert(offsetof(WorldMapWork, origin_y) == 0x168);
static_assert(offsetof(WorldMapWork, sprite_table) == 0x0B88);
static_assert(offsetof(WorldMapWork, markers_a) == 0x0E88);
static_assert(offsetof(WorldMapWork, marker_count) == 0x5A88);
static_assert(offsetof(WorldMapWork, markers_b) == 0x5A90);
static_assert(offsetof(WorldMapWork, line_count) == 0x61B0);
static_assert(offsetof(WorldMapWork, commands) == 0x61B4);
static_assert(offsetof(WorldMapWork, command_count) == 0x121B4);
static_assert(sizeof(WorldMapWork) == 0x121B8);

/**
 * 0x0039D8B8 walks TBB sub-table 0x23 rows (`camp_func_002483B8`, 0x20-byte
 * stride) and TBB sub-table 0x2B rows (`camp_func_0039FE50`, 0x0C-byte stride).
 * Only the bytes the builder reads are named.
 */
struct CampMapSpawnRow {
    u32 field_000;                      // +0x00: `ldr r0,[r7]` (0x0039DE2C)
    u8  pad_004[4];
    s8  map_id;                         // +0x08: `ldrsb r1,[r0,#8]` (0x0039DACC)
    s8  sprite_index;                   // +0x09: `ldrsb r1,[r7,#9]` (0x0039DC90)
    s8  type;                           // +0x0A: `ldrsb r1,[r7,#0xa]` (0x0039DBE0)
    u8  link_id;                        // +0x0B: `ldrb r1,[r7,#0xb]` (0x0039DC5C)
    u8  pad_00c[4];
    s16 x;                              // +0x10: `ldrsh r1,[r6,#0x10]` (0x0039E3E8)
    u8  pad_012[4];
    s16 offset_x;                       // +0x16: `ldrsh r5,[r7,#0x16]` (0x0039DC8C)
    u8  pad_018[2];
    s16 offset_y;                       // +0x1A: `ldrsh ip,[r7,#0x1a]` (0x0039DC94)
    u8  pad_01c[4];
};
static_assert(offsetof(CampMapSpawnRow, map_id) == 0x08);
static_assert(offsetof(CampMapSpawnRow, sprite_index) == 0x09);
static_assert(offsetof(CampMapSpawnRow, type) == 0x0A);
static_assert(offsetof(CampMapSpawnRow, link_id) == 0x0B);
static_assert(offsetof(CampMapSpawnRow, x) == 0x10);
static_assert(offsetof(CampMapSpawnRow, offset_x) == 0x16);
static_assert(offsetof(CampMapSpawnRow, offset_y) == 0x1A);
static_assert(sizeof(CampMapSpawnRow) == 0x20);

struct CampMapCommandRow {
    s16 map_id;                         // +0x00: `ldrsh r0,[r0]` (0x0039E5D4)
    u8  field_002;                      // +0x02: `ldrb r2,[r6,#2]` (0x0039E600)
    u8  field_003;                      // +0x03: `ldrb r1,[r6,#3]` (0x0039E6F4)
    u8  field_004;                      // +0x04: `ldrb r1,[r6,#4]` (0x0039E6FC)
    u8  field_005;                      // +0x05: `ldrb r1,[r6,#5]` (0x0039E704)
    s16 field_006;                      // +0x06: `ldrsh r1,[r6,#6]` (0x0039E710)
    s16 field_008;                      // +0x08: `ldrsh r1,[r6,#8]` (0x0039E720)
    u8  field_00A;                      // +0x0A: `ldrb r1,[r6,#0xa]` (0x0039E730)
    u8  field_00B;                      // +0x0B: `ldrb r1,[r6,#0xb]` (0x0039E740)
};
static_assert(offsetof(CampMapCommandRow, field_002) == 0x02);
static_assert(offsetof(CampMapCommandRow, field_006) == 0x06);
static_assert(offsetof(CampMapCommandRow, field_00A) == 0x0A);
static_assert(sizeof(CampMapCommandRow) == 0x0C);

/** One row returned by 0x00231628 in the 0x0039D8B8 layer sweep. */
struct CampMapLayerRow {
    u8  field_000;                      // +0x00: `ldrsb r1,[r0]` (0x0039D904)
    u8  field_001;                      // +0x01: `ldrb r0,[r6,#1]` (0x0039DC58)
    u8  field_002;                      // +0x02: `ldrb r2,[r6,#2]` (0x0039DAB8)
    s8  field_003;                      // +0x03: `ldrsb r1,[r6,#3]` (0x0039DC68)
    u16 field_004;                      // +0x04: `ldrh r0,[r6,#4]` (0x0039D990)
    u16 field_006;                      // +0x06: `ldrh r0,[r6,#6]` (0x0039D9AC)
    u16 type;                           // +0x08: `ldrh r0,[r6,#8]` (0x0039D944)
    u16 field_00A;                      // +0x0A: `ldrh sb,[r6,#0xa]` (0x0039D9C8)
    u16 field_00C;                      // +0x0C: `ldrh fp,[r6,#0xc]` (0x0039D9CC)
    s16 field_00E;                      // +0x0E: `ldrsh r2,[r6,#0xe]` (0x0039D9F0)
    s16 field_010;                      // +0x10: `ldrsh r3,[r6,#0x10]` (0x0039D9F4)
    s8  field_012;                      // +0x12: `ldrsb r1,[r6,#0x12]` (0x0039DA00)
    s8  field_013;                      // +0x13: `ldrsb r1,[r6,#0x13]` (0x0039DA18)
};
static_assert(offsetof(CampMapLayerRow, field_004) == 0x04);
static_assert(offsetof(CampMapLayerRow, type) == 0x08);
static_assert(offsetof(CampMapLayerRow, field_00A) == 0x0A);
static_assert(offsetof(CampMapLayerRow, field_00E) == 0x0E);
static_assert(offsetof(CampMapLayerRow, field_010) == 0x10);
static_assert(offsetof(CampMapLayerRow, field_012) == 0x12);
static_assert(offsetof(CampMapLayerRow, field_013) == 0x13);

// ---------------------------------------------------------------------------
// 0x0049FA1C: world-map event/transition state touched by 0x002C8C90
// ---------------------------------------------------------------------------

struct MapEventState {
    u8  pad_000[0x7C];
    u8  field_07c;                      // +0x07C: `ldrb r2,[r0,#0x7c]` (0x002C9580)
    u8  pad_07d[0x13];
    s16 field_090;                      // +0x090: `ldrh r2,[r0,#0x90]` (0x002C95A4)
    s16 field_092;                      // +0x092: `strh r6,[r0,#0x92]` (0x002C95B4)
    s16 field_094;                      // +0x094: `ldrsh r2,[r0,#0x94]` (0x002C962C)
    u8  pad_096[0x0A];
    u8  field_0a0;                      // +0x0A0: `ldrb r2,[r0,#0xa0]` (0x002C9620)
};
static_assert(offsetof(MapEventState, field_07c) == 0x07C);
static_assert(offsetof(MapEventState, field_090) == 0x090);
static_assert(offsetof(MapEventState, field_092) == 0x092);
static_assert(offsetof(MapEventState, field_094) == 0x094);
static_assert(offsetof(MapEventState, field_0a0) == 0x0A0);

// 0x0049FA1C is the object itself (g_MapRuntimeState + 0x100), not a pointer.
// It is exposed as an object reference so call sites use `g_MapEventState.x`,
// mirroring the g_UiPartRenderState overlay style.
extern MapEventState& g_MapEventState;            // 0x0049FA1C

/**
 * 0x0044CDC8 (.data): world-map transition/palette block.  The only field the
 * reconstructed routines touch is the phase word at +0x10, written to 0x0B on
 * entry (0x00399F90) and to 0xF1 on exit (0x0039AE68).  The initial words in
 * code.bin are 0x3F000000, 0x00000004, 0xF49800FF, 0xDC0F14FF, 0x0000000B.
 */
struct WorldMapUiState {
    f32 field_000;                      // +0x00 = 0.5f in code.bin
    s32 field_004;                      // +0x04 = 4
    u32 field_008;                      // +0x08 = 0xF49800FF
    u32 field_00c;                      // +0x0C = 0xDC0F14FF
    s32 phase;                          // +0x10: `str r0,[r1,#0x10]` (0x00399F90)
};
static_assert(offsetof(WorldMapUiState, field_000) == 0x00);
static_assert(offsetof(WorldMapUiState, field_008) == 0x08);
static_assert(offsetof(WorldMapUiState, phase) == 0x10);

extern WorldMapUiState g_WorldMapUiState;         // 0x0044CDC8

/** One 0x14-byte row returned by 0x002473D8 (TBB sub-table 0x2B, table 0). */
struct CampMapLandmarkRow {
    s16 map_id;                         // +0x00: `ldrsh r1,[r0]` (0x0039E2D0)
    u8  field_002;                      // +0x02: `ldrb r0,[r5,#4]` uses row+4 below
    u8  field_003;
    u8  field_004;                      // +0x04: `ldrb r2,[r5,#4]` (0x0039E330)
    u8  field_005;
    s8  field_006;                      // +0x06: `ldrsb r1,[r5,#6]` (0x0039E2E8)
    s8  field_007;                      // +0x07: `ldrsb r0,[r5,#7]` (0x0039E304)
    s8  field_008;                      // +0x08: `ldrsb r0,[r5,#8]` (0x0039E2E4)
    s8  field_009;                      // +0x09: `ldrsb r1,[r5,#9]` (0x0039E2F8)
    u8  field_00A;                      // +0x0A: `ldrb r1,[r6,#0xa]` (0x0039E730)
    u8  field_00B;                      // +0x0B: `ldrb r1,[r6,#0xb]` (0x0039E740)
    u8  pad_00c[8];                     // +0x0C..+0x14 (0x14 stride at
                                        // 0x002473D8: 5*index*4)
};
static_assert(offsetof(CampMapLandmarkRow, map_id) == 0x00);
static_assert(offsetof(CampMapLandmarkRow, field_004) == 0x04);
static_assert(offsetof(CampMapLandmarkRow, field_006) == 0x06);
static_assert(offsetof(CampMapLandmarkRow, field_009) == 0x09);
static_assert(offsetof(CampMapLandmarkRow, field_00A) == 0x0A);
static_assert(offsetof(CampMapLandmarkRow, field_00B) == 0x0B);
static_assert(sizeof(CampMapLandmarkRow) == 0x14);

/** One 8-byte sprite-atlas entry at 0x004C3228 (`add fp,fp,kind,lsl #3`). */
struct MapSpriteAtlasEntry {
    u16 base;                           // +0x00: `ldrh fp,[fp]` (0x0039E4F0)
    u16 stride;                         // +0x02: `ldrh lr,[fp,#2]` (0x0039E4EC)
    u16 field_004;                      // +0x04 (unread by these routines)
    u16 field_006;                      // +0x06
};
static_assert(sizeof(MapSpriteAtlasEntry) == 8);

extern const MapSpriteAtlasEntry g_MapSpriteAtlas[];  // 0x004C3228

// ---------------------------------------------------------------------------
// Reproduced .data tables
// ---------------------------------------------------------------------------

/** One 8-byte entry of the four 20-frame route banks (0x004045AC..). */
struct MapRouteFrame {
    s16 distance;                       // +0x00: `sxth r0,r5` (0x002C8ED8)
    s16 has_segment;                    // +0x02: `asrs r0,r5,#0x10` (0x002C8EB4)
    s16 segment_x;                      // +0x04: `sxth r1,r4` (0x002C8EBC)
    s16 segment_y;                      // +0x06: `asr r0,r4,#0x10` (0x002C8EC0)
};
static_assert(sizeof(MapRouteFrame) == 8);

extern const MapRouteFrame g_MapRouteBanks[4][20]; // 0x004045AC, 0x004064C, ...
extern const f32 g_MapRouteDamping[3];             // 0x0040449C = {0.6f,0.6f,0.6f}

// ---------------------------------------------------------------------------
// Reconstructed entry points (ledger names, smt4::script)
// ---------------------------------------------------------------------------

/** 0x00276CAC, 4,384 B: script/event camera cut evaluator. */
void script_vm_func_00276cac();

/** 0x002C8C90, 3,656 B: world-map route camera state machine. */
void script_vm_func_002c8c90();

/** 0x00399F28, 3,928 B: bottom-screen map cell grid renderer. */
void script_vm_func_00399f28(WorldMapWork* work);

/** 0x0039D8B8, 3,792 B: map marker/command list builder. */
void script_vm_func_0039d8b8(WorldMapWork* work, s32 map_id);

} // namespace smt4::script
