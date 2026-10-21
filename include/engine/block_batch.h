#pragma once

#include <cstddef>
#include "types.h"
#include "battle/battle_extras.h"
#include "engine/asd_symbols.h"
#include "engine/runtime_blocks.h"

namespace smt4::battle {

/**
 * 0x002D2E50: Billboard quad target / unit transform descriptor.
 * Offsets proven by disassembly:
 *   +0x0C: 3-float world position (X, Y, Z) (`vldr s1,[r4,#0xc]`)
 *   +0x18: 1-float yaw rotation in degrees (`vldr s0,[r4,#0x18]`)
 *   +0x38: 16-bit target quad identifier (`ldr r0,[r4,#0x38]`, `sxth`)
 */
struct BattleUnitBillboard {
    u8  pad_00[0x0C];
    f32 pos[3];                         // +0x0C: `vldr s1,[r4,#0xc]` (0x002d3098)
    f32 rot_y;                          // +0x18: `vldr s0,[r4,#0x18]` (0x002d2ec4)
    u8  pad_1c[0x1C];                   // +0x1C..+0x38
    s16 id;                             // +0x38: `ldr r0,[r4,#0x38]` (0x002d315c)
    u8  pad_3a[2];                      // +0x3A..+0x3C
};
static_assert(offsetof(BattleUnitBillboard, pos) == 0x0C);
static_assert(offsetof(BattleUnitBillboard, rot_y) == 0x18);
static_assert(offsetof(BattleUnitBillboard, id) == 0x38);

/**
 * 0x0020DC34: Battle effect / layer state pointed to through 0x004475B8.
 * Offsets proven by disassembly:
 *   +0x3C: 8-bit active/visible gate flag (`ldrb r0,[r4,#0x3c]`)
 *   +0x40: 32-bit mode selection (`ldr r0,[r4,#0x40]`)
 *   +0x44: 32-bit timer / frame counter (`ldr r6,[r4,#0x44]`)
 *   +0x48: 3-float base offset (`vldr s1,[r4,#0x48]`)
 */
struct BattleEffectState {
    u8  pad_00[0x3C];
    u8  active;                         // +0x3C: `ldrb r0,[r4,#0x3c]` (0x0020dc4c)
    u8  pad_3d[3];
    s32 mode;                           // +0x40: `ldr r0,[r4,#0x40]` (0x0020dd00)
    s32 timer;                          // +0x44: `ldr r6,[r4,#0x44]` (0x0020dd60)
    f32 offset[3];                      // +0x48: `vldr s1,[r4,#0x48]` (0x0020e23c)
};
static_assert(offsetof(BattleEffectState, active) == 0x3C);
static_assert(offsetof(BattleEffectState, mode) == 0x40);
static_assert(offsetof(BattleEffectState, timer) == 0x44);
static_assert(offsetof(BattleEffectState, offset) == 0x48);

/**
 * 0x001FB520: Screen distortion/transition grid state at 0x00448C58.
 * Offsets proven by disassembly:
 *   +0x04: Grid vertex color buffer (`ldr r0,[r2,#4]`)
 *   +0x14: Color modulation channel (`ldr r5,[r2,#0x14]`)
 *   +0x18: Active gate flag (`ldr r5,[r7,#0x18]`)
 *   +0x1C: State flag / sequence step (`strgt r5,[r7,#0x1c]`)
 *   +0x20: Transition progress 0.0..1.0 (`vldr s16,[r7,#0x20]`)
 *   +0x24: Duration rate (`vldr s1,[r7,#0x24]`)
 *   +0x28: Base color offset (`ldr r3,[r2,#0x28]`)
 *   +0x30: Skip flag (`ldr r1,[r7,#0x30]`)
 *   +0x3C: Render mode selector (`ldr r0,[r7,#0x3c]`)
 */
struct BattleGridState {
    u8   pad_00[4];
    u32* grid_buffer;                   // +0x04: `ldr r0,[r2,#4]` (0x001fb7f0)
    u8   pad_08[0x0C];
    u32  param_14;                      // +0x14: `ldr r5,[r2,#0x14]` (0x001fb7fc)
    u32  active;                        // +0x18: `ldr r5,[r7,#0x18]` (0x001fb530)
    u32  state_1c;                      // +0x1C: `strgt r5,[r7,#0x1c]` (0x001fb570)
    f32  progress;                      // +0x20: `vldr s16,[r7,#0x20]` (0x001fb574)
    f32  duration;                      // +0x24: `vldr s1,[r7,#0x24]` (0x001fb550)
    u32  param_28;                      // +0x28: `ldr r3,[r2,#0x28]` (0x001fb80c)
    u8   pad_2c[4];
    u32  flag_30;                       // +0x30: `ldr r1,[r7,#0x30]` (0x001fb6e4)
    u8   pad_34[8];
    u32  mode_3c;                       // +0x3C: `ldr r0,[r7,#0x3c]` (0x001fb5d8)
};
static_assert(offsetof(BattleGridState, grid_buffer) == 0x04);
static_assert(offsetof(BattleGridState, param_14) == 0x14);
static_assert(offsetof(BattleGridState, active) == 0x18);
static_assert(offsetof(BattleGridState, state_1c) == 0x1C);
static_assert(offsetof(BattleGridState, progress) == 0x20);
static_assert(offsetof(BattleGridState, duration) == 0x24);
static_assert(offsetof(BattleGridState, param_28) == 0x28);
static_assert(offsetof(BattleGridState, flag_30) == 0x30);
static_assert(offsetof(BattleGridState, mode_3c) == 0x3C);

/** Additional nested state pointed to through BattleUnitSprite::+0x354. */
struct BattleDrawUnitExtra {
    u8  pad_00[4];
    f32 field_04[2];                    // +0x04: `vldr s1,[r0]` (0x001aaf44)
    u8  pad_0c[8];
    f32 scale_factor;                   // +0x14: `vldr s1,[r0,#0x14]` (0x001ab310)
};
static_assert(offsetof(BattleDrawUnitExtra, field_04) == 0x04);
static_assert(offsetof(BattleDrawUnitExtra, scale_factor) == 0x14);

/** 0x18-byte quad vertex used in BattleUnitSprite. */
struct BattleVertex {
    f32 pos[3];                         // +0x00: 3D vector (X, Y, Z)
    f32 uv[2];                          // +0x0C: UV coordinate (U, V)
    u32 color;                          // +0x14: RGBA8 packed color
};
static_assert(sizeof(BattleVertex) == 0x18);
static_assert(offsetof(BattleVertex, pos) == 0x00);
static_assert(offsetof(BattleVertex, uv) == 0x0C);
static_assert(offsetof(BattleVertex, color) == 0x14);

/**
 * 0x001AAC60: 2D/3D Battle unit sprite descriptor passed in r0.
 * Offsets proven by disassembly:
 *   +0x04: 3-float Euler rotation angles (`ldm r1,{r1,r2,r3}`)
 *   +0x100: Embedded transform node (+0x6E, +0x70, +0xDA..+0xDD)
 *   +0x120: 3-float world position (`ldm r0,{r0,r1,r2}`)
 *   +0x12C: Texture slot id (`ldr r1,[r4,#0x12c]`)
 *   +0x130: Render flags bitfield (`ldrb r0,[r4,#0x130]`)
 *   +0x160: 3-float pivot offset (`ldr r6,[r4,#0x160]`)
 *   +0x16E: Head transform s16 parameter (`ldrsh r0,[r7,#0x6e]`)
 *   +0x170: Head transform s16 parameter (`ldrsh r1,[r7,#0x70]`)
 *   +0x1D9: Skip rotation flag (`ldrb r0,[r4,#0x1d9]`)
 *   +0x1DA: Head offset s8 parameter (`ldrsb r0,[r7,#0xda]`)
 *   +0x1DB: Head offset s8 parameter (`ldrsb r1,[r7,#0xdb]`)
 *   +0x1DC: Head offset s8 parameter (`ldrsb r0,[r7,#0xdc]`)
 *   +0x1DD: Head offset s8 parameter (`ldrsb r1,[r7,#0xdd]`)
 *   +0x1F4: 3-float scale vector (`vldmia r0,{s0,s1,s2}`)
 *   +0x200: Float Z rotation angle (`vldr s0,[r4,#0x200]`)
 *   +0x204: 3-float base rotation vector (`vldmia r0,{s0,s1,s2}`)
 *   +0x354: Pointer to BattleDrawUnitExtra (`ldr r0,[r4,#0x354]`)
 *   +0x358: 3-float animation offset (`ldm r0,{r0,r1,r2}`)
 *   +0x368: Animation angle/param (`ldr r2,[r4,#0x368]`)
 *   +0x380: Animation mode byte (`ldrb r0,[r4,#0x380]`)
 *   +0x388: 4 quad vertices (each 0x18 bytes)
 *   +0x3E8: Active/visible byte (`ldrb r0,[r0,#0x3e8]`)
 */
struct BattleUnitSprite {
    u8                  pad_00[4];
    s32                 rot_angles[3];          // +0x04..+0x0C
    u8                  pad_10[0x110];
    f32                 pos[3];                 // +0x120: `ldm r0,{r0,r1,r2}` (0x001aaf8c)
    u32                 texture_id;             // +0x12C: `ldr r1,[r4,#0x12c]` (0x001ab538)
    u8                  render_flags;           // +0x130: `ldrb r0,[r4,#0x130]` (0x001aac8c)
    u8                  pad_131[0x2F];
    s32                 pivot_offset[3];        // +0x160: `ldr r6,[r4,#0x160]` (0x001ab150)
    u8                  pad_16c[2];             // +0x16C..+0x16E
    s16                 field_16e;              // +0x16E: `ldrsh r0,[r7,#0x6e]` (0x001ab180)
    s16                 field_170;              // +0x170: `ldrsh r1,[r7,#0x70]` (0x001ab184)
    u8                  pad_172[0x67];
    u8                  skip_rot;               // +0x1D9: `ldrb r0,[r4,#0x1d9]` (0x001ab1a8)
    s8                  field_1da;              // +0x1DA: `ldrsb r0,[r7,#0xda]` (0x001ab280)
    s8                  field_1db;              // +0x1DB: `ldrsb r1,[r7,#0xdb]` (0x001ab294)
    s8                  field_1dc;              // +0x1DC: `ldrsb r0,[r7,#0xdc]` (0x001ab2dc)
    s8                  field_1dd;              // +0x1DD: `ldrsb r1,[r7,#0xdd]` (0x001ab2f4)
    u8                  pad_1de[0x16];
    f32                 scale[3];               // +0x1F4: `vldmia r0,{s0,s1,s2}` (0x001ab34c)
    f32                 rot_z;                  // +0x200: `vldr s0,[r4,#0x200]` (0x001ab1e0)
    f32                 rot_base[3];            // +0x204: `vldmia r0,{s0,s1,s2}` (0x001ab1bc)
    u8                  pad_210[0x144];
    BattleDrawUnitExtra* extra;                 // +0x354: `ldr r0,[r4,#0x354]` (0x001aaf34)
    f32                 anim_offset[3];         // +0x358: `ldm r0,{r0,r1,r2}` (0x001aafc0)
    u8                  pad_364[4];
    s32                 anim_param_368;         // +0x368: `ldr r2,[r4,#0x368]` (0x001ab170)
    u8                  pad_36c[0x14];
    u8                  anim_mode;              // +0x380: `ldrb r0,[r4,#0x380]` (0x001aafb0)
    u8                  pad_381[7];
    BattleVertex        quad_verts[4];          // +0x388..+0x3E7
    u8                  active;                 // +0x3E8: `ldrb r0,[r0,#0x3e8]` (0x001aac70)
};
static_assert(offsetof(BattleUnitSprite, rot_angles) == 0x04);
static_assert(offsetof(BattleUnitSprite, pos) == 0x120);
static_assert(offsetof(BattleUnitSprite, texture_id) == 0x12C);
static_assert(offsetof(BattleUnitSprite, render_flags) == 0x130);
static_assert(offsetof(BattleUnitSprite, pivot_offset) == 0x160);
static_assert(offsetof(BattleUnitSprite, field_16e) == 0x16E);
static_assert(offsetof(BattleUnitSprite, field_170) == 0x170);
static_assert(offsetof(BattleUnitSprite, skip_rot) == 0x1D9);
static_assert(offsetof(BattleUnitSprite, field_1da) == 0x1DA);
static_assert(offsetof(BattleUnitSprite, field_1db) == 0x1DB);
static_assert(offsetof(BattleUnitSprite, field_1dc) == 0x1DC);
static_assert(offsetof(BattleUnitSprite, field_1dd) == 0x1DD);
static_assert(offsetof(BattleUnitSprite, scale) == 0x1F4);
static_assert(offsetof(BattleUnitSprite, rot_z) == 0x200);
static_assert(offsetof(BattleUnitSprite, rot_base) == 0x204);
static_assert(offsetof(BattleUnitSprite, extra) == 0x354);
static_assert(offsetof(BattleUnitSprite, anim_offset) == 0x358);
static_assert(offsetof(BattleUnitSprite, anim_param_368) == 0x368);
static_assert(offsetof(BattleUnitSprite, anim_mode) == 0x380);
static_assert(offsetof(BattleUnitSprite, quad_verts) == 0x388);
static_assert(offsetof(BattleUnitSprite, active) == 0x3E8);

/** Particle track / keyframe emitter interface behind BattleParticleContext::+0x08. */
struct BattleParticleEmitter {
    void* vtable;                       // +0x00
};

/**
 * 0x0034A4E4: Particle emitter evaluation context passed in r0.
 * Offsets proven by disassembly:
 *   +0x04: Command buffer base pointer (`ldr r0,[r0,#4]`, `+0x8c`)
 *   +0x08: Polymorphic emitter source (`ldr r0,[r4,#8]`, vtable calls)
 */
struct BattleParticleContext {
    u8                     pad_00[4];
    u8*                    buffer_base;         // +0x04: `ldr r0,[r0,#4]` (0x0034a4f8)
    BattleParticleEmitter* emitter;             // +0x08: `ldr r0,[r4,#8]` (0x0034a538)
};
static_assert(offsetof(BattleParticleContext, buffer_base) == 0x04);
static_assert(offsetof(BattleParticleContext, emitter) == 0x08);

} // namespace smt4::battle

// ---------------------------------------------------------------------------
// External / C-linkage declarations
// ---------------------------------------------------------------------------

extern "C" {

// 0x002D2E50 (3,108 B): 4-face oriented billboard quad generator & render submitter
void battle_func_002d2e50(const smt4::battle::BattleUnitBillboard* billboard);

// 0x00267420 (2,888 B): General 4-face bounding box / billboard column submitter
void battle_func_00267420(s32 id, f32 x, f32 y, f32 z, f32 rot_y, f32 width, f32 height, f32 depth);

// 0x0034A4E4 (2,816 B): Three-pass particle emitter command buffer evaluator
void battle_func_0034a4e4(smt4::battle::BattleParticleContext* context, u32 arg1);

// 0x001FB520 (2,788 B): Screen transition / distortion grid renderer
void battle_func_001fb520();

// 0x001AAC60 (2,448 B): Battle unit 3D sprite perspective projection & drawing
void battle_func_001aac60(smt4::battle::BattleUnitSprite* unit);

// 0x0020DC34 (2,416 B): Concentric billboard layer renderer with sine fade
void battle_func_0020dc34();

// ---------------------------------------------------------------------------
// Call targets proven across the six functions
// ---------------------------------------------------------------------------

// 0x00262CB8: Submits 3D billboard quad corners and normal to global quad buffer
void engine_func_00262cb8(s32 id, ...);

// 0x002AD6D8: 4x3 affine transform vector (out = M * in + translation)
void battle_func_002ad6d8(f32* out_vec, const f32* matrix, const f32* in_vec);

// 0x002C8A28: Pre-render state prepare
void func_002c8a28();

// 0x0028277C: Sine calculation (sinf)
f32 script_vm_func_0028277c(f32 x);

// 0x002BA520: Draw quad with 4 vertices and vertex colors
void func_002ba520(u32 c0, u32 c1, u32 c2, u32 c3);

// 0x001FB448: Grid pre-update
void func_001fb448();

// 0x002AA418: Set fullscreen/viewport background quad
void func_002aa418(f32 a0, f32 a1, f32 a2, f32 a3, u32 c0, u32 c1, u32 c2, u32 c3);

// 0x002C0B1C: Draw grid tile
void ui_func_002c0b1c(u32 c0, u32 c1, s32 x, u32 c2, u32 c3);

// 0x002C1D3C: Set active texture
void ui_func_002c1d3c(void* gpu, u32 tex_id);

// 0x002A7F04: Get FilterXPoly identity/projection matrix
f32* battle_func_002a7f04();

// 0x002C0000: 4x4 matrix copy (16 floats)
void battle_func_002c0000(f32* dst, const f32* src);

// 0x002C00B4: 4x3 matrix copy (12 floats)
void battle_func_002c00b4(f32* dst, const f32* src);

// 0x002C00D4: Query engine state
u32 engine_func_002c00d4();

// 0x002A84EC
u32 func_002a84ec(void* dst, void* src);

// 0x002863F4
void script_vm_func_002863f4(void* dst, void* src);

// 0x00286604
void func_00286604(void* dst, void* src);

// 0x00286700: Build translation matrix from 3D vector
void func_00286700(f32* matrix, const f32* vec);

// 0x0028640C: Rotate matrix by Euler angles
void func_0028640c(f32* matrix, s32 angle_x, s32 angle_y, s32 angle_z);

// 0x002A89CC
void func_002a89cc(void* a0, void* a1);

// 0x002A8A58: 3x3 matrix * 3-vector
void engine_func_002a8a58(f32* out_vec, const f32* matrix, const f32* in_vec);

// 0x002B22FC: Build axis rotation matrix
void func_002b22fc(f32* matrix, f32 angle_x, f32 angle_y, f32 angle_z);

// 0x002B71F8: 4x4 matrix multiply (dest = left * right)
void script_vm_func_002b71f8(f32* dest, const f32* left, const f32* right);

// 0x00195424: Draw unit shadow / billboard attachment
void ui_func_00195424(void* unit, u32 mode);

// 0x002BC9D8: Command buffer memory allocate
void* engine_func_002bc9d8(u32 size);

// 0x0034DE5C: Sequencer init pass 1
void* engine_func_0034de5c(void* buf);

// 0x0034DDA4: Sequencer init pass 2
void* func_0034dda4(void* buf);

// 0x0034DE00: Sequencer intermediate pass
void* func_0034de00(void* buf);

// 0x0034DF38: Sequencer final pass
void* func_0034df38(void* buf);

// 0x0023D3D0: Keyframe index binary search
s32 func_0023d3d0(void* data, s32 time);

// 0x0023D39C
void func_0023d39c(void* out_mat, void* src, void* dir);

// 0x0023D368
void func_0023d368(void* mat, f32 scale);

// 0x002A5078
void battle_func_002a5078(void* dst, void* src);

// 0x0023D348
void func_0023d348(void* obj, u32 val);

// 0x0023D2B4
void* func_0023d2b4(void* buf, void* obj);

// 0x0023D230
void* func_0023d230(void* buf, u32 val);

// 0x0023D1D4
void* func_0023d1d4(void* buf);

// 0x00349F34: Emit particle packet pass 1
void* ui_func_00349f34(void* obj, void* buf, u32 arg2, void* mat);

// 0x00349FE0: Emit particle packet pass 2
void* ui_func_00349fe0(void* obj, void* buf, u32 arg2, void* mat);

// 0x0034A08C: Emit particle packet pass 3
void* ui_func_0034a08c(void* obj, void* buf, u32 arg2, void* mat);

// 0x003570A0
void* func_003570a0(void* buf);

// 0x002AF630
void func_002af630(u32 size);

// 0x00364F78
void func_00364f78(void* ctx, u32 arg1, u32 arg2);

} // extern "C"
