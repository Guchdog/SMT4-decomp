#pragma once
#include <cstddef>
#include "types.h"
#include "engine/asd_scene.h"
#include "engine/asd_texture.h"

/**
 * Render-system, event-texture, staff-roll, bustup and filter entry points.
 *
 * The twelve ledger rows reconstructed in `src/engine/asd_render_ui.cpp` come
 * from nine original translation units:
 *
 *   AsdGxRenderSystem.cpp   AsdGxRenderSystem_func_002d595c / _002bc570
 *   StaffRollMain.cpp       StaffRollMain_func_002cabcc
 *   2dEventTex.cpp          2dEventTex_func_002ee6a0
 *   3dEventTex.cpp          3dEventTex_func_0030a0b8
 *   WhisperEffect.cpp       WhisperEffect_func_002f6734
 *   BustupCutAnim.cpp       BustupCutAnim_func_002fc260
 *   BustupTex.cpp           BustupTex_func_0030ac20
 *   AsdMdlManager.cpp       AsdMdlManager_func_002b2928
 *   Npc2d.cpp               Npc2d_func_00327634
 *   Filter4Poly.cpp         Filter4Poly_func_0034b920
 *   effBehavior.cpp         effBehavior_func_00269404
 *
 * Only the fields touched by these bodies are named.  Every offset below cites
 * the instruction that proves it; unproven ranges stay `pad_NN`.
 */

namespace smt4::engine {

// ---------------------------------------------------------------------------
// AsdGxRenderSystem.cpp (0x002D595C, 0x002BC570)
// ---------------------------------------------------------------------------

/**
 * One 0x18-byte GPU buffer descriptor.
 *
 * `AsdGxRenderSystem_func_002d595c` builds two of them in a single 0x30-byte
 * allocation: the first at +0x00 (0x002D5B40..0x002D5BFC) and the second at
 * +0x18 (0x002D5D00..0x002D5DB4).  `AsdGxRenderSystem_func_002bc570` fills the
 * same layout for two caller-supplied records.
 *
 * +0x00 is the pixel format word, +0x04 the 2/3/4 code produced by the format
 * classifier, +0x08 the host buffer, +0x0C its GPU address, +0x10 the byte
 * stride and +0x14 the secondary code (only 2 for code 0x8058).
 */
struct AsdGxBufferDesc {
    u32 format;                     // +0x00: `str r8,[r4]` (0x002d5b58)
    u32 code;                       // +0x04: `str r1,[r4,#4]` (0x002d5b40)
    void* data;                     // +0x08: `str r0,[r4,#8]` (0x002d5bf0)
    u32 gpu_address;                // +0x0C: `str r0,[r4,#0xc]` (0x002d5bf8)
    u32 stride;                     // +0x10: `str r3,[r4,#0x10]` (0x002d5b48)
    u32 aux;                        // +0x14: `str fp,[r4,#0x14]` (0x002d5bfc)
};
static_assert(offsetof(AsdGxBufferDesc, format) == 0x00);
static_assert(offsetof(AsdGxBufferDesc, code) == 0x04);
static_assert(offsetof(AsdGxBufferDesc, data) == 0x08);
static_assert(offsetof(AsdGxBufferDesc, gpu_address) == 0x0C);
static_assert(offsetof(AsdGxBufferDesc, stride) == 0x10);
static_assert(offsetof(AsdGxBufferDesc, aux) == 0x14);
static_assert(sizeof(AsdGxBufferDesc) == 0x18);

/**
 * Object returned by `AsdGxRenderSystem_func_002d595c` (0x14 bytes at
 * 0x002D599C).  +0x00 points at the 0x30-byte descriptor array, +0x04 at its
 * second element (`add r1,r4,#0x18`, 0x002D5DB8), +0x08 is the first buffer and
 * +0x0C the texture created through 0x002BD940.  +0x10 is never written.
 */
struct AsdGxRenderSystem {
    AsdGxBufferDesc* descriptors;   // +0x00: `str r4,[r5]` (0x002d5dc4)
    AsdGxBufferDesc* active;        // +0x04: `str r1,[r5,#4]` (0x002d5dc0)
    void* data;                     // +0x08: `str r0,[r5,#8]` (0x002d5c04)
    AsdTexture* texture;            // +0x0C: `str r0,[r5,#0xc]` (0x002d59d4)
    u8 pad_10[0x04];
};
static_assert(offsetof(AsdGxRenderSystem, descriptors) == 0x00);
static_assert(offsetof(AsdGxRenderSystem, active) == 0x04);
static_assert(offsetof(AsdGxRenderSystem, data) == 0x08);
static_assert(offsetof(AsdGxRenderSystem, texture) == 0x0C);
static_assert(sizeof(AsdGxRenderSystem) == 0x14);   // `mov r3,#0x14` (0x002d598c)

/**
 * Input record pair consumed by `AsdGxRenderSystem_func_002bc570`.
 *
 * The loop index is scaled by 0x18 (`add r0,r7,r7,lsl #1` then `lsl #3`,
 * 0x002BC590..0x002BC598).  +0x00 is the format word, +0x04/+0x08 the two
 * dimensions multiplied together for the stride, +0x0C the allocation kind,
 * +0x10 is unused by the body and +0x14 is copied to the destination's +0x38.
 */
struct AsdGxLayerDesc {
    u32 format;                     // +0x00: `ldr ip,[r4]` (0x002bc5a0)
    u32 width;                      // +0x04: `ldm r1,{r1,r2}` (0x002bc5a4)
    u32 height;                     // +0x08: same `ldm`
    u32 memory_kind;                // +0x0C: `ldr r1,[r4,#0xc]` (0x002bc650)
    u32 field_10;                   // +0x10: unused by 0x002BC570
    u32 field_14;                   // +0x14: `ldr r0,[r4,#0x14]` (0x002bc720)
};
static_assert(offsetof(AsdGxLayerDesc, format) == 0x00);
static_assert(offsetof(AsdGxLayerDesc, width) == 0x04);
static_assert(offsetof(AsdGxLayerDesc, height) == 0x08);
static_assert(offsetof(AsdGxLayerDesc, memory_kind) == 0x0C);
static_assert(offsetof(AsdGxLayerDesc, field_10) == 0x10);
static_assert(offsetof(AsdGxLayerDesc, field_14) == 0x14);
static_assert(sizeof(AsdGxLayerDesc) == 0x18);

/**
 * Destination of `AsdGxRenderSystem_func_002bc570`: two 0x18-byte layer
 * descriptors followed by the three tail words copied from record 1
 * (0x002BC708..0x002BC724).
 */
struct AsdGxLayerSet {
    AsdGxBufferDesc layers[2];      // +0x00 and +0x18
    u32 field_30;                   // +0x30: `str r0,[r6,#0x30]`
    u32 field_34;                   // +0x34: `str r0,[r6,#0x34]`
    u32 field_38;                   // +0x38: `str r0,[r6,#0x38]`
};
static_assert(offsetof(AsdGxLayerSet, layers) == 0x00);
static_assert(offsetof(AsdGxLayerSet, field_30) == 0x30);
static_assert(offsetof(AsdGxLayerSet, field_34) == 0x34);
static_assert(offsetof(AsdGxLayerSet, field_38) == 0x38);
static_assert(sizeof(AsdGxLayerSet) == 0x3C);

// ---------------------------------------------------------------------------
// StaffRollMain.cpp (0x002CABCC)
// ---------------------------------------------------------------------------

/**
 * Staff-roll singleton (0x764 bytes at 0x002CAC00).
 *
 * The three 12-entry float tables have stride 8: +0x08/+0x0C (0x002CAC7C),
 * +0x68/+0x6C (0x002CAD00) and +0xC8/+0xCC (0x002CAC84).  The callback words
 * at +0x12C..+0x144 are code addresses from the listing's literal pool.
 */
struct StaffRollMain {
    void* task;                     // +0x00: `str r0,[r5]` (0x002cadac)
    u8 field_04;                    // +0x04: `strb sb,[r5,#4]` (0x002cad88)
    u8 field_05;                    // +0x05: `strb r7,[r5,#5]` (0x002cac18)
    u8 pad_06[0x02];
    f32 rows_a[12][2];              // +0x08: `vstr s0,[r0,#8]` (0x002cac98)
    f32 rows_b[12][2];              // +0x68: `vstr s5,[r0,#0x68]` (0x002cad00)
    f32 rows_c[12][2];              // +0xC8: `vstr s0,[r0,#0xc8]` (0x002cac84)
    u8 field_128;                   // +0x128: `strb r7,[r0,#0x128]` (0x002cac1c)
    u8 pad_129[0x03];
    u32 callbacks[7];               // +0x12C..+0x147: 0x002CAD48..0x002CAD7C
    f32 field_148;                  // +0x148: `vstr s0,[r5,#0x148]` (0x002cad28)
    u32 field_14c;                  // +0x14C: `str r7,[r0,#0x14c]` (0x002cad44)
    f32 field_150;                  // +0x150: `vstr s1,[r5,#0x150]` (0x002cad2c)
    u8 pad_154[0x604];
    u32 field_758;                  // +0x758: `str r7,[r5,#0x758]` (0x002cad30)
    u8 field_75c;                   // +0x75C: `strb r7,[r5,#0x75c]` (0x002cad34)
    u8 pad_75d[0x03];
    u32 field_760;                  // +0x760: `str r1,[r5,#0x760]` (0x002cad38)
};
static_assert(offsetof(StaffRollMain, task) == 0x00);
static_assert(offsetof(StaffRollMain, field_04) == 0x04);
static_assert(offsetof(StaffRollMain, rows_a) == 0x08);
static_assert(offsetof(StaffRollMain, rows_b) == 0x68);
static_assert(offsetof(StaffRollMain, rows_c) == 0xC8);
static_assert(offsetof(StaffRollMain, field_128) == 0x128);
static_assert(offsetof(StaffRollMain, callbacks) == 0x12C);
static_assert(offsetof(StaffRollMain, field_148) == 0x148);
static_assert(offsetof(StaffRollMain, field_14c) == 0x14C);
static_assert(offsetof(StaffRollMain, field_150) == 0x150);
static_assert(offsetof(StaffRollMain, field_758) == 0x758);
static_assert(offsetof(StaffRollMain, field_75c) == 0x75C);
static_assert(offsetof(StaffRollMain, field_760) == 0x760);
static_assert(sizeof(StaffRollMain) == 0x764);  // `mov r3,#0x764` (0x002cac00)

// ---------------------------------------------------------------------------
// 2dEventTex.cpp (0x002EE6A0)
// ---------------------------------------------------------------------------

/**
 * 2D event-texture list (0x68 bytes at 0x002EE6DC).
 *
 * The ten pointer slots hold registered tasks, `count` is the leading non-null
 * run (`ldr r0,[r5,#0x2c]`, 0x002EE870) and +0x5C is the initialised flag.
 */
struct EventTexList2d {
    void* task;                     // +0x00: `str r0,[r4]` (0x002ee720)
    void* entries[10];              // +0x04..+0x2B: `str r7,[r0,#4]` (0x002ee81c)
    u32 count;                      // +0x2C: `str r0,[r5,#0x2c]` (0x002ee88c)
    u8 pad_30[0x2C];                // +0x30..+0x5C
    u8 field_5c;                    // +0x5C: `strb r5,[r4,#0x5c]` (0x002ee700)
    u8 pad_5d[0x0B];                // +0x5D..+0x68
};
static_assert(offsetof(EventTexList2d, task) == 0x00);
static_assert(offsetof(EventTexList2d, entries) == 0x04);
static_assert(offsetof(EventTexList2d, count) == 0x2C);
static_assert(offsetof(EventTexList2d, field_5c) == 0x5C);
static_assert(sizeof(EventTexList2d) == 0x68);   // `mov r3,#0x68` (0x002ee6cc)

// ---------------------------------------------------------------------------
// 3dEventTex.cpp (0x0030A0B8)
// ---------------------------------------------------------------------------

/**
 * 3D event-texture object (0x48 bytes at 0x0030A0F0).
 *
 * +0x04 is the load state (1 when the scene is busy, 2 after the sprite is
 * created), +0x2C/+0x30 are the two incoming floats, +0x38 the negated row
 * halfword and +0x3C the mode selected by the float thresholds.
 */
struct EventTex3d {
    u32 id;                         // +0x00: `str r5,[r4]` (0x0030a164)
    u32 state;                      // +0x04: `strne r7,[r4,#4]` (0x0030a140)
    f32 field_08;                   // +0x08: `vstr s0,[r4,#8]` (0x0030a10c)
    f32 field_0c;                   // +0x0C: `vstr s18,[r4,#0xc]` (0x0030a110)
    f32 field_10;                   // +0x10: `vstr s1,[r4,#0x10]` (0x0030a118)
    u8 field_14;                    // +0x14: `strb r6,[r4,#0x14]` (0x0030a11c)
    u8 field_15;                    // +0x15: `strb r6,[r4,#0x15]` (0x0030a1d8)
    u8 field_16;                    // +0x16: `strb r7,[r4,#0x16]` (0x0030a1d4)
    u8 field_17;                    // +0x17: `strb r6,[r4,#0x17]` (0x0030a124)
    u8 pad_18[0x14];                // +0x18..+0x2C
    f32 value;                      // +0x2C: `vstmia r2,{s16,s17}` (0x0030a1cc)
    f32 value2;                     // +0x30: same `vstmia`
    void* sprite;                   // +0x34: `str r0,[r4,#0x34]` (0x0030a158)
    s32 field_38;                   // +0x38: `str r0,[r4,#0x38]` (0x0030a134)
    u32 mode;                       // +0x3C: `str r0,[r4,#0x3c]` (0x0030a1b8)
    u8 pad_40[0x08];                // +0x40..+0x48
};
static_assert(offsetof(EventTex3d, id) == 0x00);
static_assert(offsetof(EventTex3d, state) == 0x04);
static_assert(offsetof(EventTex3d, field_08) == 0x08);
static_assert(offsetof(EventTex3d, field_10) == 0x10);
static_assert(offsetof(EventTex3d, field_14) == 0x14);
static_assert(offsetof(EventTex3d, value) == 0x2C);
static_assert(offsetof(EventTex3d, value2) == 0x30);
static_assert(offsetof(EventTex3d, sprite) == 0x34);
static_assert(offsetof(EventTex3d, field_38) == 0x38);
static_assert(offsetof(EventTex3d, mode) == 0x3C);
static_assert(sizeof(EventTex3d) == 0x48);       // `mov r3,#0x48` (0x0030a0e0)

// ---------------------------------------------------------------------------
// WhisperEffect.cpp (0x002F6734)
// ---------------------------------------------------------------------------

/**
 * Whisper-effect singleton (0x1B8 bytes at 0x002F6764).
 *
 * +0xC4..+0x1A4 receive byte offsets into the engine block at 0x0044DC68
 * (0x002F6800..0x002F687C).  The five "entry" counts sit at +0xD8+0x34*i and
 * their random values at +0xDC+0x34*i (0x002F68AC..0x002F68D4); entry 3's
 * count therefore coincides with the +0x174 pointer word, which is what the
 * listing reads.
 */
struct WhisperEffectWork {
    void* task;                     // +0x00: `str r0,[r1]` (0x002f6924)
    u8 pad_04[0x08];
    u32 event_id;                   // +0x0C: `str r3,[r2,#0xc]` (0x002f68f8)
    f32 field_10;                   // +0x10: `vstr s0,[r4,#0x10]` (0x002f67b0)
    u8 pad_14[0x0C];
    f32 field_20;                   // +0x20: `vstr s0,[r1,#0x20]` (0x002f68a0)
    f32 field_24;                   // +0x24: `vstr s1,[r4,#0x24]` (0x002f67c0)
    u32 field_28;                   // +0x28: `str r2,[r4,#0x28]` (0x002f67b4)
    u8 pad_2c[0x14];
    f32 field_40;                   // +0x40: same base+0x20 store, i=1
    f32 field_44;                   // +0x44: `vstr s2,[r4,#0x44]` (0x002f67cc)
    u32 field_48;                   // +0x48: `str r3,[r4,#0x48]` (0x002f67c4)
    u8 pad_4c[0x24];
    u32 field_70;                   // +0x70: `str sb,[r4,#0x70]` (0x002f67d0)
    u8 pad_74[0x1C];
    u32 field_90;                   // +0x90: `str sb,[r4,#0x90]` (0x002f67dc)
    u8 pad_94[0x0C];
    f32 field_a0;                   // +0xA0: `vstr s3,[r4,#0xa0]` (0x002f67e8)
    u8 pad_a4[0x0C];
    u32 field_b0;                   // +0xB0: `str ip,[r4,#0xb0]` (0x002f67e0)
    u8 pad_b4[0x10];
    u8* ptr_c4;                     // +0xC4: `str r0,[r4,#0xc4]` (0x002f680c)
    u8* ptr_c8;                     // +0xC8: `str r0,[r4,#0xc8]` (0x002f6814)
    u8 pad_cc[0x08];
    u8* ptr_d4;                     // +0xD4: `str r0,[r4,#0xd4]` (0x002f6824)
    u32 field_d8;                   // +0xD8: entry 0 count
    u32 field_dc;                   // +0xDC: entry 0 value (`str r0,[r6,#0xdc]`)
    u8 pad_e0[0x18];
    u8* ptr_f8;                     // +0xF8: `str r0,[r4,#0xf8]` (0x002f682c)
    u8* ptr_fc;                     // +0xFC: `str r0,[r4,#0xfc]` (0x002f6834)
    u8 pad_100[0x08];
    u8* ptr_108;                    // +0x108: `str r0,[r4,#0x108]` (0x002f683c)
    u32 field_10c;                  // +0x10C: entry 1 count
    u32 field_110;                  // +0x110: entry 1 value
    u8 pad_114[0x18];
    u8* ptr_12c;                    // +0x12C: `str r0,[r4,#0x12c]` (0x002f6844)
    u8* ptr_130;                    // +0x130: `str r0,[r4,#0x130]` (0x002f684c)
    u8 pad_134[0x08];
    u8* ptr_13c;                    // +0x13C: `str r0,[r4,#0x13c]` (0x002f6854)
    u32 field_140;                  // +0x140: entry 2 count
    u32 field_144;                  // +0x144: entry 2 value
    u8 pad_148[0x18];
    u8* ptr_160;                    // +0x160: `str r0,[r4,#0x160]` (0x002f685c)
    u8* ptr_164;                    // +0x164: `str r0,[r4,#0x164]` (0x002f6864)
    u8 pad_168[0x08];
    u8* ptr_170;                    // +0x170: `stm r2,{r0,r1}` (0x002f6864)
    u32 field_174;                  // +0x174: second word of that `stm`
    u32 field_178;                  // +0x178: entry 3 value
    u8 pad_17c[0x18];
    u8* ptr_194;                    // +0x194: `str r0,[r4,#0x194]` (0x002f686c)
    u8* ptr_198;                    // +0x198: `str r0,[r4,#0x198]` (0x002f6874)
    u8 pad_19c[0x08];
    u8* ptr_1a4;                    // +0x1A4: `str r0,[r4,#0x1a4]` (0x002f687c)
    u32 field_1a8;                  // +0x1A8: entry 4 count
    u32 field_1ac;                  // +0x1AC: entry 4 value
    u8 pad_1b0[0x08];
};
static_assert(offsetof(WhisperEffectWork, task) == 0x00);
static_assert(offsetof(WhisperEffectWork, event_id) == 0x0C);
static_assert(offsetof(WhisperEffectWork, field_10) == 0x10);
static_assert(offsetof(WhisperEffectWork, field_20) == 0x20);
static_assert(offsetof(WhisperEffectWork, field_40) == 0x40);
static_assert(offsetof(WhisperEffectWork, field_70) == 0x70);
static_assert(offsetof(WhisperEffectWork, field_90) == 0x90);
static_assert(offsetof(WhisperEffectWork, field_a0) == 0xA0);
static_assert(offsetof(WhisperEffectWork, field_b0) == 0xB0);
static_assert(offsetof(WhisperEffectWork, ptr_c4) == 0xC4);
static_assert(offsetof(WhisperEffectWork, ptr_c8) == 0xC8);
static_assert(offsetof(WhisperEffectWork, ptr_d4) == 0xD4);
static_assert(offsetof(WhisperEffectWork, field_d8) == 0xD8);
static_assert(offsetof(WhisperEffectWork, field_10c) == 0x10C);
static_assert(offsetof(WhisperEffectWork, field_140) == 0x140);
static_assert(offsetof(WhisperEffectWork, field_174) == 0x174);
static_assert(offsetof(WhisperEffectWork, ptr_1a4) == 0x1A4);
static_assert(offsetof(WhisperEffectWork, field_1a8) == 0x1A8);
static_assert(offsetof(WhisperEffectWork, field_1ac) == 0x1AC);
static_assert(sizeof(WhisperEffectWork) == 0x1B8); // `mov r3,#0x1b8` (0x002f6758)

// ---------------------------------------------------------------------------
// BustupCutAnim.cpp (0x002FC260)
// ---------------------------------------------------------------------------

/**
 * Bustup cut animation work (0x744 bytes at 0x002FC2A8).
 *
 * The 0x508-byte projection starts at +0x04, so the 30 model handles at +0x658
 * and the 28 camera handles at +0x6C8 follow the eye/target/up/perspective
 * block at +0x50C/+0x518/+0x524/+0x530.
 */
struct BustupCutAnimWork {
    void* task;                     // +0x00: `str r1,[r5]` (0x002fc3bc)
    AsdCameraProjection projection; // +0x04: `add r0,r5,#4` (0x002fc2bc)
    f32 eye[3];                     // +0x50C: `vstr s2,[r7]` (0x002fc2d4)
    f32 target[3];                  // +0x518: `vstr s2,[r0]` (0x002fc2e8)
    f32 up[3];                      // +0x524: `vstr s2,[r0]` (0x002fc328)
    f32 perspective[4];             // +0x530: `vstmia r2,{s0,s1}` (0x002fc320)
    u32 field_540;                  // +0x540: `vstr s2,[r1,#0x140]` (0x002fc30c)
    u8 pad_544[0xA4];               // +0x544..+0x5E8
    void* model;                    // +0x5E8: `str r0,[r5,#0x5e8]` (0x002fc444)
    u32 field_5ec;                  // +0x5EC: `str sl,[r5,#0x5ec]` (0x002fc3ec)
    u8 field_5f0;                   // +0x5F0: `strb sl,[r5,#0x5f0]` (0x002fc38c)
    u8 field_5f1;                   // +0x5F1: `strb sl,[r5,#0x5f1]` (0x002fc448)
    u8 field_5f2;                   // +0x5F2: `strb sb,[r5,#0x5f2]` (0x002fc394)
    u8 pad_5f3[0x65];               // +0x5F3..+0x658
    void* models[0x1C];             // +0x658: `str r0,[r6,#0x658]` (0x002fc438)
    void* cameras[0x1C];            // +0x6C8: `str r0,[r6,#0x6c8]` (0x002fc414)
    u8 pad_738[0x0C];               // +0x738..+0x744
};
static_assert(offsetof(BustupCutAnimWork, task) == 0x00);
static_assert(offsetof(BustupCutAnimWork, projection) == 0x04);
static_assert(offsetof(BustupCutAnimWork, eye) == 0x50C);
static_assert(offsetof(BustupCutAnimWork, target) == 0x518);
static_assert(offsetof(BustupCutAnimWork, up) == 0x524);
static_assert(offsetof(BustupCutAnimWork, perspective) == 0x530);
static_assert(offsetof(BustupCutAnimWork, field_540) == 0x540);
static_assert(offsetof(BustupCutAnimWork, model) == 0x5E8);
static_assert(offsetof(BustupCutAnimWork, field_5ec) == 0x5EC);
static_assert(offsetof(BustupCutAnimWork, models) == 0x658);
static_assert(offsetof(BustupCutAnimWork, cameras) == 0x6C8);
static_assert(sizeof(BustupCutAnimWork) == 0x744); // `mov r3,#0x744` (0x002fc2a8)

// ---------------------------------------------------------------------------
// BustupTex.cpp (0x0030AC20)
// ---------------------------------------------------------------------------

/**
 * Bustup texture loader (0x90 bytes at 0x0030AC80).
 *
 * +0x10/+0x14 are only filled when the mode argument is zero (0x0030ACD8);
 * +0x14 == -1 then skips the row load (0x0030ACF4).  +0x7C is the "scene busy"
 * flag and +0x84 is initialised to -1 (0x0030AC94).
 */
struct BustupTexWork {
    u32 request_id;                 // +0x00: `str r5,[r4]` (0x0030ac90)
    void* row;                      // +0x04: `str r0,[r4,#4]` (0x0030acac)
    u32 field_08;                   // +0x08: never written
    void* row_data;                 // +0x0C: `str r0,[r4,#0xc]` (0x0030ad44)
    u32 key;                        // +0x10: `stm r2,{r0,r8}` (0x0030acd8)
    u32 sub;                        // +0x14: same `stm` with r8 = -1
    s32 field_18;                   // +0x18: `str r8,[r4,#0x18]` (0x0030ac9c)
    f32 field_1c;                   // +0x1C: `vstr s0,[r4,#0x1c]` (0x0030ace4)
    f32 field_20;                   // +0x20: `vstr s0,[r4,#0x20]` (0x0030ace8)
    u8 pad_24[0x04];
    f32 field_28;                   // +0x28: `vstmia r2,{s0,s1}` (0x0030ad64)
    f32 field_2c;                   // +0x2C: same `vstmia`
    u8 field_30;                    // +0x30: `strb r5,[r4,#0x30]` (0x0030ad6c)
    u8 field_31;                    // +0x31: `strb r7,[r4,#0x31]` (0x0030ad70)
    u8 pad_32[0x4A];                // +0x32..+0x7C
    u8 field_7c;                    // +0x7C: `strbne r7,[r4,#0x7c]` (0x0030acc4)
    u8 pad_7d[0x07];                // +0x7D..+0x84
    s32 field_84;                   // +0x84: `str r8,[r4,#0x84]` (0x0030ac94)
    u8 pad_88[0x08];                // +0x88..+0x90
};
static_assert(offsetof(BustupTexWork, request_id) == 0x00);
static_assert(offsetof(BustupTexWork, row) == 0x04);
static_assert(offsetof(BustupTexWork, row_data) == 0x0C);
static_assert(offsetof(BustupTexWork, key) == 0x10);
static_assert(offsetof(BustupTexWork, sub) == 0x14);
static_assert(offsetof(BustupTexWork, field_18) == 0x18);
static_assert(offsetof(BustupTexWork, field_1c) == 0x1C);
static_assert(offsetof(BustupTexWork, field_20) == 0x20);
static_assert(offsetof(BustupTexWork, field_30) == 0x30);
static_assert(offsetof(BustupTexWork, field_31) == 0x31);
static_assert(offsetof(BustupTexWork, field_7c) == 0x7C);
static_assert(offsetof(BustupTexWork, field_84) == 0x84);
static_assert(sizeof(BustupTexWork) == 0x90);    // `mov r3,#0x90` (0x0030ac6c)

// ---------------------------------------------------------------------------
// AsdMdlManager.cpp (0x002B2928)
// ---------------------------------------------------------------------------

/**
 * Model-manager record allocated at manager+0x18 (0x1C bytes per model,
 * 0x002B2974..0x002B2990).  +0x14/+0x18 receive the two maxima.
 */
struct AsdMdlEntry {
    void* buffer;                   // +0x00: `stm r8,{r0,r6}` (0x002b2a1c)
    u32 count;                      // +0x04: same `stm`
    u8 pad_08[0x0C];                // +0x08..+0x14
    f32 max_x;                      // +0x14: `vstmia r8,{s16,s17}` (0x002b2b10)
    f32 max_y;                      // +0x18: same `vstmia`
};
static_assert(offsetof(AsdMdlEntry, buffer) == 0x00);
static_assert(offsetof(AsdMdlEntry, count) == 0x04);
static_assert(offsetof(AsdMdlEntry, max_x) == 0x14);
static_assert(offsetof(AsdMdlEntry, max_y) == 0x18);
static_assert(sizeof(AsdMdlEntry) == 0x1C);

/**
 * Model manager prefix.  Only +0x08 (scene owner) and +0x18 (entry array) are
 * touched by 0x002B2928.
 */
struct AsdMdlManagerWork {
    u8 pad_00[0x08];
    void* field_08;                 // +0x08: `ldr r0,[r7,#8]` (0x002b2938)
    u8 pad_0c[0x0C];
    AsdMdlEntry* entries;           // +0x18: `str r0,[r7,#0x18]` (0x002b29a4)
};

/**
 * Animation node behind the three relative-offset chains walked by
 * 0x002B2928.  The 8 floats at +0x10 and the word at +0x30 form the 3x3
 * matrix passed to 0x002A8A58; +0x34 is the three-float vector and +0x04 the
 * translation added afterwards.
 */
struct AsdMdlTransform {
    u8 pad_00[0x04];
    f32 position[3];                // +0x04: `vldmia r1,{s18,s19,s20}` (0x002b2a60)
    f32 matrix[9];                  // +0x10..+0x33: `vldmia r1,{s0..s7}` + `[r0,#0x30]`
    f32 vector[3];                  // +0x34: `ldm r1,{r1,r2}` (0x002b2a7c)
};
static_assert(offsetof(AsdMdlTransform, position) == 0x04);
static_assert(offsetof(AsdMdlTransform, matrix) == 0x10);
static_assert(offsetof(AsdMdlTransform, vector) == 0x34);
static_assert(sizeof(AsdMdlTransform) == 0x40);

// ---------------------------------------------------------------------------
// Npc2d.cpp (0x00327634)
// ---------------------------------------------------------------------------

/** NPC row returned by 0x00245B44; +0x22 is read by 0x0030A12C and +0x24 by
 *  0x003276CC. */
struct Npc2dRow {
    u8 pad_00[0x22];
    u16 field_22;                   // +0x22: `ldrh r0,[r0,#0x22]` (0x0030a12c)
    u16 field_24;                   // +0x24: `ldrh r0,[r0,#0x24]` (0x003276cc)
};
static_assert(offsetof(Npc2dRow, field_22) == 0x22);
static_assert(offsetof(Npc2dRow, field_24) == 0x24);

/** Layout node returned by 0x002BF6D0; the two signed halves at +0x08/+0x0A
 *  and the pointer at +0x0C are the only fields 0x00327634 touches. */
struct Npc2dLayoutNode {
    u8 pad_00[0x08];
    s16 x;                          // +0x08: `ldrsh r2,[r0,#8]` (0x003276e8)
    s16 y;                          // +0x0A: `ldrsh r2,[r0,#0xa]` (0x00327700)
    void* extra;                    // +0x0C: `ldr r1,[r0,#0xc]` (0x00327798)
};
static_assert(offsetof(Npc2dLayoutNode, x) == 0x08);
static_assert(offsetof(Npc2dLayoutNode, y) == 0x0A);
static_assert(offsetof(Npc2dLayoutNode, extra) == 0x0C);

/** Row returned by 0x002B9364 in WhisperEffect.cpp; +0x32 feeds the request id
 *  built at 0x002F68E0..0x002F68F8. */
struct TalkEntryRow {
    u8 pad_00[0x32];
    u8 field_32;                    // +0x32: `ldrb r3,[r0,#0x32]` (0x002f68e0)
};
static_assert(offsetof(TalkEntryRow, field_32) == 0x32);

/**
 * NPC sprite created by `Npc2d_func_00327634` (0x98 bytes at 0x00327664).
 *
 * The size and the shared +0x00/+0x04/+0x3C/+0x40/+0x44/+0x54 offsets match
 * `Npc2dSprite` in engine/asd_frame.h; this constructor additionally writes the
 * node slots at +0x74..+0x90 and the state bytes at +0x64..+0x71, which that
 * header leaves as padding.
 */
struct Npc2dEvent {
    u32 id;                         // +0x00: `str r5,[r4]` (0x003276a4)
    u32 field_04;                   // +0x04: `str r1,[r4,#4]` with 0x41
    u8 pad_08[0x04];
    u32 field_0c;                   // +0x0C: `strne r7,[r4,#0xc]` (0x0032775c)
    u32 field_10;                   // +0x10: `str r1,[r4,#0x10]` (0x00327738)
    s32 field_14;                   // +0x14: `vstr s0,[r4,#0x14]` (0x00327750)
    f32 field_18;                   // +0x18: `vstr s0,[r4,#0x18]` (0x00327774)
    s32 field_1c;                   // +0x1C: `vstr s16,[r4,#0x1c]` (0x00327740)
    f32 field_20;                   // +0x20: `vstr s0,[r4,#0x20]` (0x00327680)
    f32 field_24;                   // +0x24: `vstr s0,[r4,#0x24]` (0x00327684)
    f32 field_28;                   // +0x28: `vstr s16,[r4,#0x28]` (0x0032773c)
    u8 pad_2c[0x0C];                // +0x2C..+0x38
    u32 field_38;                   // +0x38: `str r0,[r4,#0x38]` with 5
    u32 field_3c;                   // +0x3C: `str r2,[r4,#0x3c]` with 0x26
    u32 field_40;                   // +0x40: `str r0,[r4,#0x40]` (0x003276d8)
    s32 field_44;                   // +0x44: `str r3,[r4,#0x44]` with -1
    u8 pad_48[0x0C];                // +0x48..+0x54
    void* row;                      // +0x54: `str r0,[r4,#0x54]` (0x003276c8)
    u8 pad_58[0x0C];                // +0x58..+0x64
    u8 field_64;                    // +0x64: `strb r7,[r4,#0x64]` (0x003276ac)
    u8 pad_65[0x03];
    u32 field_68;                   // +0x68: `str r6,[r4,#0x68]` (0x003276b0)
    u32 field_6c;                   // +0x6C: `str r6,[r4,#0x6c]` (0x003276b4)
    u8 field_70;                    // +0x70: `strb r6,[r4,#0x70]` (0x003276b8)
    u8 field_71;                    // +0x71: `strb r6,[r4,#0x71]` (0x003276c0)
    u8 pad_72[0x02];                // +0x72..+0x74
    f32 slots[3][2];                // +0x74: `vstr s0,[r1,#0x74]` (0x003276fc)
    f32 field_8c;                   // +0x8C: `vstr s0,[r4,#0x8c]` (0x003277b0)
    f32 field_90;                   // +0x90: `vstr s0,[r4,#0x90]` (0x003277c4)
    u8 pad_94[0x04];                // +0x94..+0x98
};
static_assert(offsetof(Npc2dEvent, id) == 0x00);
static_assert(offsetof(Npc2dEvent, field_0c) == 0x0C);
static_assert(offsetof(Npc2dEvent, field_10) == 0x10);
static_assert(offsetof(Npc2dEvent, field_14) == 0x14);
static_assert(offsetof(Npc2dEvent, field_20) == 0x20);
static_assert(offsetof(Npc2dEvent, field_38) == 0x38);
static_assert(offsetof(Npc2dEvent, field_3c) == 0x3C);
static_assert(offsetof(Npc2dEvent, field_40) == 0x40);
static_assert(offsetof(Npc2dEvent, field_44) == 0x44);
static_assert(offsetof(Npc2dEvent, row) == 0x54);
static_assert(offsetof(Npc2dEvent, field_64) == 0x64);
static_assert(offsetof(Npc2dEvent, field_68) == 0x68);
static_assert(offsetof(Npc2dEvent, field_70) == 0x70);
static_assert(offsetof(Npc2dEvent, slots) == 0x74);
static_assert(offsetof(Npc2dEvent, field_8c) == 0x8C);
static_assert(offsetof(Npc2dEvent, field_90) == 0x90);
static_assert(sizeof(Npc2dEvent) == 0x98);       // `mov r3,#0x98` (0x00327658)

// ---------------------------------------------------------------------------
// Filter4Poly.cpp (0x0034B920)
// ---------------------------------------------------------------------------

/**
 * Filter source record.  +0x1C is the block count used for both allocations and
 * the loop bound; +0x34..+0x3C are the three words handed to the auxiliary
 * object's virtual slot 5 (0x0034BA98..0x0034BAA8).
 */
struct Filter4PolySource {
    u8 pad_00[0x1C];
    u32 count;                      // +0x1C: `ldr r2,[r7,#0x1c]` (0x0034b9c8)
    u8 pad_20[0x0C];
    u32 field_2c;                   // +0x2C: `ldr r0,[r0,#0x2c]` (0x0034ba18)
    u8 pad_30[0x04];
    u32 field_34;                   // +0x34: `ldm r7,{r1,r2,r3}` (0x0034ba9c)
    u32 field_38;
    u32 field_3c;
};
static_assert(offsetof(Filter4PolySource, count) == 0x1C);
static_assert(offsetof(Filter4PolySource, field_2c) == 0x2C);
static_assert(offsetof(Filter4PolySource, field_34) == 0x34);
static_assert(sizeof(Filter4PolySource) == 0x40);

/**
 * Auxiliary filter object allocated as 0x0C bytes (flag set, vtable 0x004204D0)
 * or 0x20 bytes (flag clear, vtable 0x00420358) at 0x0034B938/0x0034B95C.
 * Only the first three words are initialised, so no `sizeof` is asserted.
 */
struct Filter4PolyAux {
    void** vtable;                  // +0x00: `stm r0,{r1,r6}` (0x0034b954)
    u32 field_04;                   // +0x04: same `stm`
    f32 field_08;                   // +0x08: `vstr s0,[r0,#8]` (0x0034b950)
};

/**
 * Filter work object (0x20 bytes at 0x0034B9EC).
 *
 * +0x04 is the 0x50-byte vertex block, +0x18 the `count*0x50` block array and
 * +0x14 the auxiliary object whose virtual slots 4/5 are called at
 * 0x0034BA4C and 0x0034BAA8.
 */
struct Filter4Poly {
    void** vtable;                  // +0x00: `str r1,[r0]` with 0x00420598
    void* vertices;                 // +0x04: `str r0,[r5,#4]` (0x0034ba00)
    u32 field_08;                   // +0x08: `str r6,[r0,#8]` (0x0034b9a8)
    u32 field_0c;                   // +0x0C: `str r6,[r0,#0xc]` (0x0034b9ac)
    f32 field_10;                   // +0x10: `vstr s0,[r0,#0x10]` (0x0034b9b0)
    void* aux;                      // +0x14: `str r8,[r0,#0x14]` (0x0034b9c0)
    void* blocks;                   // +0x18: `str r0,[r5,#0x18]` (0x0034ba34)
    Filter4PolySource* source;      // +0x1C: `str r7,[r5,#0x1c]` (0x0034b9c4)
};
static_assert(offsetof(Filter4Poly, vtable) == 0x00);
static_assert(offsetof(Filter4Poly, vertices) == 0x04);
static_assert(offsetof(Filter4Poly, field_08) == 0x08);
static_assert(offsetof(Filter4Poly, field_0c) == 0x0C);
static_assert(offsetof(Filter4Poly, field_10) == 0x10);
static_assert(offsetof(Filter4Poly, aux) == 0x14);
static_assert(offsetof(Filter4Poly, blocks) == 0x18);
static_assert(offsetof(Filter4Poly, source) == 0x1C);
static_assert(sizeof(Filter4Poly) == 0x20);      // `mov r0,#0x20` (0x0034b95c)

// ---------------------------------------------------------------------------
// effBehavior.cpp (0x00269404)
// ---------------------------------------------------------------------------

/**
 * Per-behaviour size table at 0x00473590, five words per id.  The body reads
 * words 2 and 3 (`add r0,r0,#8` then `ldm r0,{r2,r7}`, 0x0026942C..0x00269434)
 * and the source record contributes +0xC0/+0xC4 as a multiplier pair.
 */
struct EffBehaviorEntry {
    u32 field_00;
    u32 field_04;
    u32 field_08;                   // +0x08: `ldm r0,{r2,r7}` first word
    u32 field_0c;                   // +0x0C: second word
    u32 field_10;
};
static_assert(offsetof(EffBehaviorEntry, field_08) == 0x08);
static_assert(offsetof(EffBehaviorEntry, field_0c) == 0x0C);
static_assert(sizeof(EffBehaviorEntry) == 0x14);

/**
 * Behavior header built by `effBehavior_func_00269404` (0x30 bytes before the
 * variable data).  +0x18 is the element region, +0x20 the record region and
 * +0x1C/+0x24 the two copies inside it (0x00269480..0x002694A0).
 */
struct EffBehavior {
    u16 id;                         // +0x00: `strh r5,[r4]` (0x002694ac)
    u8 pad_02[0x02];
    u32 count;                      // +0x04: `stm r0,{r6,r8,fp}` (0x002694b0)
    u32 total;                      // +0x08: same `stm`
    u32 flags;                      // +0x0C: `orr r0,r0,#1` (0x00269524)
    u32 field_10;                   // +0x10: `str fp,[r4,#0x10]` (0x002694bc)
    f32 field_14;                   // +0x14: `vstr s0,[r4,#0x14]` (0x002694c0)
    void* data;                     // +0x18: `str r1,[r0,#0x18]` (0x00269488)
    void* record_c;                 // +0x1C: `stm r0,{r1,r3}` (0x002694a0)
    void* records;                  // +0x20: second word of that `stm`
    void* record_b;                 // +0x24: `str r1,[r0,#0x24]` (0x00269494)
    void* self;                     // +0x28: `str r4,[r4,#0x28]` (0x002694cc)
    u8 pad_2c[0x04];
};
static_assert(offsetof(EffBehavior, id) == 0x00);
static_assert(offsetof(EffBehavior, count) == 0x04);
static_assert(offsetof(EffBehavior, total) == 0x08);
static_assert(offsetof(EffBehavior, flags) == 0x0C);
static_assert(offsetof(EffBehavior, field_10) == 0x10);
static_assert(offsetof(EffBehavior, field_14) == 0x14);
static_assert(offsetof(EffBehavior, data) == 0x18);
static_assert(offsetof(EffBehavior, record_c) == 0x1C);
static_assert(offsetof(EffBehavior, records) == 0x20);
static_assert(offsetof(EffBehavior, record_b) == 0x24);
static_assert(offsetof(EffBehavior, self) == 0x28);
static_assert(sizeof(EffBehavior) == 0x30);

// ---------------------------------------------------------------------------
// Ledger entry points (address / size match config/functions.csv)
// ---------------------------------------------------------------------------

AsdGxRenderSystem* AsdGxRenderSystem_func_002d595c(
    u32 width, u32 height, u32 memory_kind, u32 format, u32 param,
    u32 memory_kind2, u32 memory_kind3);                       // 0x002d595c, 1144 B
void AsdGxRenderSystem_func_002bc570(AsdGxLayerSet* target,
                                     const AsdGxLayerDesc* layers,
                                     u32 allocate);            // 0x002bc570, 468 B
void StaffRollMain_func_002cabcc(u32 reset_flag);              // 0x002cabcc, 800 B
void* EventTex2d_func_002ee6a0();                              // 0x002ee6a0, 784 B
void* EventTex3d_func_0030a0b8(u32 id, f32 value,
                               f32 value2);                    // 0x0030a0b8, 468 B
u32 AsdMdlManager_func_002b2928(AsdMdlManagerWork* manager);   // 0x002b2928, 592 B
void Npc2d_func_00327634(u32 id);                              // 0x00327634, 488 B
Filter4Poly* Filter4Poly_func_0034b920(Filter4PolySource* source,
                                       u32 flags, u32 allocate); // 0x0034b920, 432 B
EffBehavior* effBehavior_func_00269404(u32 id, u32 count,
                                       void* data);            // 0x00269404, 400 B

} // namespace smt4::engine

namespace smt4::ui {

/**
 * 0x0044DC68 is a static engine block addressed by fixed byte offsets.  Only
 * its address is observable from 0x002F6734, so the contents stay external.
 */
extern u8 g_WhisperEffectBlock[0x1B8];

void  WhisperEffect_func_002f6734(u32 id);                     // 0x002f6734, 776 B
void* BustupCutAnim_func_002fc260();                           // 0x002fc260, 800 B
void  BustupTex_func_0030ac20(u32 id, u32 mode);               // 0x0030ac20, 412 B

} // namespace smt4::ui
