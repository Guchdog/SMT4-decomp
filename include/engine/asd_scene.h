#pragma once
#include <cstddef>
#include "types.h"

/**
 * AsdCamera / AsdScene objects, the AsdProcess pool, the AsdSequence loader
 * hook and the Task list.
 *
 * The eleven functions reconstructed in `src/engine/asd_scene.cpp` come from
 * five original translation units:
 *
 *   AsdCamera    c:\SMT4\XRD686\AsdSDK\Source\Gfx\Camera\AsdCamera.cpp
 *   AsdScene     c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdScene.cpp
 *   AsdProcess   c:\SMT4\XRD686\AsdSDK\Source\Sys\Kernel\AsdProcess.cpp
 *   AsdSequence  c:\SMT4\XRD686\AsdSDK\Source\Sys\Kernel\AsdSequence.cpp
 *   Task         c:\SMT4\XRD686\sdds4\program\sys\Task\Task.c
 *
 * Every field carries the instruction and address that proves it.  Structures
 * whose allocation size is visible in the listing (`AsdMem_Alloc(..., size, 1)`)
 * carry a `sizeof` assertion; resource data blocks, whose extent is owned by a
 * different TU, are modelled as observed prefixes with `offsetof` assertions
 * only.
 */

namespace smt4::engine {

struct AsdSceneFogParams;
struct AsdTaskNode;

// ---------------------------------------------------------------------------
// AsdCamera.cpp (0x00105C50, 0x00310124)
// ---------------------------------------------------------------------------

/**
 * One 0x508-byte projection block inside `AsdCamera`.
 *
 * `engine_func_002c2210` (0x002C2210) starts with `mov r1,#0x508` followed by
 * `AsdMem_Zero(r0, 0x508)` (0x002C2218); no field is touched by the two
 * reconstructed camera functions, so the block stays opaque.
 */
struct AsdCameraProjection {
    u8 pad_00[0x508];
};
static_assert(sizeof(AsdCameraProjection) == 0x508);

/**
 * Camera object allocated by `AsdCamera_func_00105c50` (0xA98 bytes, 0x00105C68).
 *
 * The two projections are adjacent: the first starts at +0x88
 * (`add r0,r4,#0x88`, 0x00105CA0) and the second at +0x590
 * (`add r0,r4,#0x590`, 0x00105CEC), which is exactly +0x88 + 0x508.
 * `strd r0,r1,[r4,#0x80]` (0x00105D2C) stores the two interior pointers.
 */
struct AsdCamera {
    u8 pad_00[0x80];
    AsdCameraProjection* projections[2];    // +0x80, +0x84: `strd r0,r1,[r4,#0x80]` (0x00105D2C)
    AsdCameraProjection projection_data[2]; // +0x88 and +0x590 (`add r0,r4,#0x88/#0x590`)
};
static_assert(offsetof(AsdCamera, projections) == 0x80);
static_assert(offsetof(AsdCamera, projection_data) == 0x88);
static_assert(sizeof(AsdCamera) == 0xA98);  // `mov r3,#0xa98` (0x00105C6C)

/**
 * Two-word camera manager at `0x0044EA58`.
 *
 * `str r4,[r6,#4]` (0x00105CA4) records the camera; `str r0,[r6]` (0x00105D54)
 * records the widget returned by `AsdUi_Create`.  The object keeps living past
 * +0x08 in other TUs, so no `sizeof` assertion is made.
 */
struct AsdCameraManager {
    void* proc;             // +0x00: `str r0,[r6]` (0x00105D54)
    AsdCamera* camera;      // +0x04: `str r4,[r6,#4]` (0x00105CA4)
};

/**
 * Default eye/target/up vectors at `0x004D4924`.
 *
 * `AsdCamera_func_00105c50` passes the three addresses 0x004D4924, 0x004D4930
 * and 0x004D493C to `engine_func_002c20a8` as r1/r2/r3 (0x00105CAC-0x00105CBC).
 * Their 0x0C spacing proves three consecutive `f32[3]` vectors.
 */
struct AsdCameraDefaults {
    f32 eye[3];             // +0x00 (0x004D4924)
    f32 target[3];          // +0x0C (0x004D4930)
    f32 up[3];              // +0x18 (0x004D493C)
};
static_assert(sizeof(AsdCameraDefaults) == 0x24);

/**
 * Scene passed to `AsdCamera_func_00310124` (ledger name; the listing calls it
 * with the scene/camera owner whose node tables feed the animation tracks).
 *
 * Only the four table descriptors are read.  The object continues past +0x84
 * in the original (it is not allocated here), so it is an observed prefix.
 */
struct AsdCameraScene {
    u8 pad_00[0x44];
    u32 entry_count;        // +0x44: `ldr r1,[r4,#0x44]` (0x00310174)
    u32 entry_rel;          // +0x48: `ldr r1,[r4,#0x48]` (0x00310160)
    u8 pad_4c[0x30];        // +0x4C..+0x7C
    s32 node_count;         // +0x7C: `ldr fp,[r0,#0x7c]` (0x00310288)
    u32 node_rel;           // +0x80: `ldr r1,[r0,#0x80]!` (0x003102AC)
};
static_assert(offsetof(AsdCameraScene, entry_count) == 0x44);
static_assert(offsetof(AsdCameraScene, entry_rel) == 0x48);
static_assert(offsetof(AsdCameraScene, node_count) == 0x7C);
static_assert(offsetof(AsdCameraScene, node_rel) == 0x80);

/**
 * 0x18-byte binding record returned by `AsdCamera_func_00310124`
 * (`mov r3,#0x18`, 0x00310148).
 */
struct AsdCameraAnim {
    u32 field_00;                  // +0x00: never written by the listing
    void* track;                   // +0x04: `str r4,[r6,#4]` (0x00310340)
    void* object_44E820;           // +0x08: `str r8,[r6,#8]` (0x0031027C)
    void* object_44E858;           // +0x0C: `str r4,[r6,#0xc]` (0x00310278)
    AsdCameraScene* scene;         // +0x10: `str r4,[r6,#0x10]` (0x00310198)
    u32 field_14;                  // +0x14: untouched
};
static_assert(offsetof(AsdCameraAnim, track) == 0x04);
static_assert(offsetof(AsdCameraAnim, object_44E820) == 0x08);
static_assert(offsetof(AsdCameraAnim, object_44E858) == 0x0C);
static_assert(offsetof(AsdCameraAnim, scene) == 0x10);
static_assert(sizeof(AsdCameraAnim) == 0x18);

/** Prefix of the clip reached through `AsdCameraAnimSource::clip`; +0x10 is its duration. */
struct AsdCameraClip {
    u8 pad_00[0x10];
    f32 duration;                  // +0x10: `vldr s16,[r0,#0x10]` (0x003102A0)
};
static_assert(offsetof(AsdCameraClip, duration) == 0x10);

/**
 * Prefix of the animation source: `ldr r0,[sb,#8]` (0x00310294) reads the
 * active clip pointer.
 */
struct AsdCameraAnimSource {
    u8 pad_00[0x08];
    AsdCameraClip* clip;           // +0x08: `ldr r0,[sb,#8]` (0x00310294)
};
static_assert(offsetof(AsdCameraAnimSource, clip) == 0x08);

/**
 * Prefix of the object typed `0x0044E820` that the animation binding requires.
 * `ldr sb,[r8,#0x268]` (0x00310284) reads the animation source pointer.
 */
struct AsdCameraAnimOwner {
    u8 pad_00[0x268];
    AsdCameraAnimSource* source;   // +0x268: `ldr sb,[r8,#0x268]` (0x00310284)
};
static_assert(offsetof(AsdCameraAnimOwner, source) == 0x268);

/**
 * Track descriptor built on the stack for `AsdAnim_SetupTrack`.
 *
 * 0x003102D8-0x00310338: `str r0,[sp,#0x30]`, `vstr s16,[sp,#0x34]`,
 * `str 0x40,[sp,#0x38]`, `strb 1,[sp,#0x3c]`; `ldrd r2,r3,[sp,#0x34]` and
 * `ldrsb r0,[sp,#0x3c]` then feed the 0x002A5CA4 call.
 */
struct AsdCameraTrackDesc {
    void* source;                  // +0x00: resolved node/entry pointer
    f32 time;                      // +0x04: animation clip duration
    u32 field_08;                  // +0x08: constant 0x40
    u8 field_0c;                   // +0x0C: constant 1
    u8 pad_0d[0x03];
};
static_assert(offsetof(AsdCameraTrackDesc, time) == 0x04);
static_assert(offsetof(AsdCameraTrackDesc, field_08) == 0x08);
static_assert(offsetof(AsdCameraTrackDesc, field_0c) == 0x0C);
static_assert(sizeof(AsdCameraTrackDesc) == 0x10);

/**
 * Observed prefix of the 0x74-byte animation track (`mov r1,#0x74`, 0x00310304)
 * built by `AsdAnim_CreateTrack` (0x002A6108).
 *
 * 0x00310360-0x00310384: r4 = track + 0x30, so `[r4,#8]` is +0x38 and
 * `[r4,#0xc]` is +0x3C; r1 = track + 0x44 feeds `vldmia`; the vector call
 * reads +0x4C (function), +0x50 (argument) and writes byte +0x58.
 */
struct AsdCameraTrack {
    u8 pad_00[0x38];
    f32 current;                   // +0x38: `ldr r0,[r4,#8]` (0x00310378) / `vstr s0,[r4,#8]` (0x00310380)
    f32 previous;                  // +0x3C: `str r0,[r4,#0xc]` (0x0031037C)
    u8 pad_40[0x04];               // +0x40..+0x44
    f32 param_a;                   // +0x44: first word of `vldmia r1` (0x0031036C)
    f32 param_b;                   // +0x48: second word of that `vldmia`
    f32 (*evaluate)(void*, f32, f32, f32); // +0x4C: `ldr r1,[r7,#0x4c]` (0x00310370)
    void* evaluate_arg;            // +0x50: `ldr r0,[r7,#0x50]` (0x00310364)
    u8 pad_54[0x04];
    u8 field_58;                   // +0x58: `strb sl,[r7,#0x58]` = 1 (0x00310384)
    u8 pad_59[0x74 - 0x59];
};
static_assert(offsetof(AsdCameraTrack, current) == 0x38);
static_assert(offsetof(AsdCameraTrack, previous) == 0x3C);
static_assert(offsetof(AsdCameraTrack, param_a) == 0x44);
static_assert(offsetof(AsdCameraTrack, param_b) == 0x48);
static_assert(offsetof(AsdCameraTrack, evaluate) == 0x4C);
static_assert(offsetof(AsdCameraTrack, evaluate_arg) == 0x50);
static_assert(offsetof(AsdCameraTrack, field_58) == 0x58);
static_assert(sizeof(AsdCameraTrack) == 0x74);

/**
 * Resource descriptor consumed by `AsdRes_Create` (0x002C3188).
 *
 * Built at sp+0x28 in `AsdCamera_func_00310124`: source word at +0x00
 * (0x00310200), byte 1 at +0x04 (0x003101D4), 8 at +0x08 (0x003101D8),
 * 4 at +0x0C (0x003101D0), 4 at +0x1C (0x003101FC) and byte 1 at +0x24
 * (0x003101F8); the remaining words are zeroed (0x003101E4-0x003101F0).
 */
struct AsdCameraCreateDesc {
    void* source;                  // +0x00
    u8 field_04;                   // +0x04
    u8 pad_05[0x03];
    u32 field_08;                  // +0x08
    u32 field_0c;                  // +0x0C
    u32 field_10;                  // +0x10
    u32 field_14;                  // +0x14
    u32 field_18;                  // +0x18
    u32 field_1c;                  // +0x1C
    u32 field_20;                  // +0x20
    u8 field_24;                   // +0x24
    u8 pad_25[0x03];
};
static_assert(sizeof(AsdCameraCreateDesc) == 0x28);

// ---------------------------------------------------------------------------
// AsdScene.cpp (0x0010BD34, 0x0010E5F0, 0x001186B4, 0x00118C7C, 0x002CB788)
// ---------------------------------------------------------------------------

/**
 * Create descriptor used by every AsdScene resource constructor.
 *
 * The stack image at sp+8 is identical in all five functions: byte 1 at +0x00,
 * byte 1 at +0x01, zero at +0x04, zero at +0x08 and 1 at +0x0C
 * (for example 0x0010BDBC-0x0010BDC8).
 */
struct AsdSceneCreateDesc {
    u8 enabled;                    // +0x00: `strb r7,[sp,#8]` = 1
    u8 visible;                    // +0x01: `strb r7,[sp,#9]` = 1
    u8 pad_02[0x02];
    u32 field_04;                  // +0x04: `str r6,[sp,#0xc]` = 0
    u32 field_08;                  // +0x08: `strd r6,r7,[sp,#0x10]` first word = 0
    u32 field_0c;                  // +0x0C: `strd` second word = 1
};
static_assert(offsetof(AsdSceneCreateDesc, field_04) == 0x04);
static_assert(offsetof(AsdSceneCreateDesc, field_08) == 0x08);
static_assert(offsetof(AsdSceneCreateDesc, field_0c) == 0x0C);
static_assert(sizeof(AsdSceneCreateDesc) == 0x10);

/**
 * 0x0C-byte scene unit allocated by 0x0010E5F0 / 0x001186B4 / 0x00118C7C /
 * 0x002CB788.
 *
 * The index is set to -1 (`mvn r1,#0; str r1,[r0]`, 0x0010E65C), +0x04 receives
 * the created object and +0x08 the object's data pointer (`[r0,#8]`).
 */
struct AsdSceneObject {
    s32 index;                     // +0x00: initialised to -1
    void* object;                  // +0x04: returned by the resource constructor
    void* data;                    // +0x08: `ldr r1,[r0,#8]` (0x0010E688)
};
static_assert(offsetof(AsdSceneObject, object) == 0x04);
static_assert(offsetof(AsdSceneObject, data) == 0x08);
static_assert(sizeof(AsdSceneObject) == 0x0C);

/**
 * Observed prefix of the data block produced by the 0x0011D8E4 node object.
 * `AsdScene_func_0010e5f0` and `AsdScene_func_002cb788` write the RGBA colour
 * at +0xB8..+0xC4 and the `AsdRes_BuildKey` result at +0xC8.
 */
struct AsdSceneNodeData {
    u8 pad_00[0xB8];
    f32 color_r;                   // +0xB8: `vstr s16,[r0]` = 0.2 (0x0010E694)
    f32 color_g;                   // +0xBC: `vstr s16,[r0,#4]` = 0.2 (0x0010E698)
    f32 color_b;                   // +0xC0: `vstmia r0,{s16,s17}` first = 0.2 (0x0010E6A0)
    f32 color_a;                   // +0xC4: second word = 1.0
    u32 key;                       // +0xC8: `str r0,[r1,#0xc8]` (0x0010E6B4)
};
static_assert(offsetof(AsdSceneNodeData, color_r) == 0xB8);
static_assert(offsetof(AsdSceneNodeData, color_g) == 0xBC);
static_assert(offsetof(AsdSceneNodeData, color_b) == 0xC0);
static_assert(offsetof(AsdSceneNodeData, color_a) == 0xC4);
static_assert(offsetof(AsdSceneNodeData, key) == 0xC8);

/**
 * Observed prefix of the data block produced by the 0x0011FF20 effect object.
 * 0x0010E724-0x0010E764 writes +0xB8..+0xE4.
 */
struct AsdSceneEffectData {
    u8 pad_00[0xB8];
    f32 color_r;                   // +0xB8: `vstr s20,[r0]` = 0.1 (0x0010E740)
    f32 color_g;                   // +0xBC: `vstr s18,[r0,#4]` = 0.0
    f32 color_b;                   // +0xC0: `vstr s18,[r0,#8]` = 0.0
    f32 color_a;                   // +0xC4: `vstr s17,[r0,#0xc]` = 1.0
    f32 field_c8;                  // +0xC8: `vstr s19,[r1]` = 0.9 (0x0010E728)
    f32 field_cc;                  // +0xCC: `vstr s19,[r1,#4]` = 0.9
    f32 field_d0;                  // +0xD0: `vstr s17,[r1,#8]` = 1.0
    f32 field_d4;                  // +0xD4: `vstr s17,[r1,#0xc]` = 1.0
    f32 field_d8;                  // +0xD8: `vstmia r0!,{s18}` = 0.0 (0x0010E758)
    f32 field_dc;                  // +0xDC: `vstmia r0,{s17,s18}` first = 1.0
    f32 field_e0;                  // +0xE0: second word = 0.0
    f32 field_e4;                  // +0xE4: `vstr s21,[r0,#0xe4]` = 0.5 (0x0010E764)
};
static_assert(offsetof(AsdSceneEffectData, color_r) == 0xB8);
static_assert(offsetof(AsdSceneEffectData, field_c8) == 0xC8);
static_assert(offsetof(AsdSceneEffectData, field_d8) == 0xD8);
static_assert(offsetof(AsdSceneEffectData, field_e4) == 0xE4);

/**
 * Observed prefix of the data block produced by the 0x0012AAF4 light object
 * (see `AsdScene_func_001186b4`, 0x00118734-0x001187b8).
 */
struct AsdSceneLightData {
    u8 pad_00[0x48];
    f32 field_48;                  // +0x48: `vstmia r0,{s1,s2}` first = 0.0 (0x00118758)
    f32 field_4c;                  // +0x4C: second word = 15.0
    f32 field_50;                  // +0x50: `vstr s0,[r0,#8]` = 5.0 (0x0011874C)
    u8 pad_54[0x64];               // +0x54..+0xB8
    u32 kind;                      // +0xB8: `str r0,[r1,#0xb8]` = 2 (0x00118734)
    f32 color_r;                   // +0xBC: `vstr s2,[r0]` = 0.2 (0x00118768)
    f32 color_g;                   // +0xC0: `vstr s2,[r0,#4]` = 0.2
    f32 color_b;                   // +0xC4: `vstr s2,[r0,#8]` = 0.2
    f32 color_a;                   // +0xC8: `vstr s0,[r0,#0xc]` = 1.0
    f32 field_cc;                  // +0xCC: `vstr s0,[r0]` = 1.0 (0x00118784)
    f32 field_d0;                  // +0xD0: 1.0
    f32 field_d4;                  // +0xD4: 1.0
    f32 field_d8;                  // +0xD8: 1.0
    f32 field_dc;                  // +0xDC: `vstr s1,[r0,#0xdc]` = 0.0 (0x001187C4)
    f32 field_e0;                  // +0xE0: `vstr s1,[r0,#0xe0]` = 0.0
    f32 field_e4;                  // +0xE4: `vstr s0,[r0,#0xe4]` = -1.0
    f32 field_e8;                  // +0xE8: `vstmia r0,{s2,s3,s4}` first = 0.01 (0x0011879C)
    f32 field_ec;                  // +0xEC: second = 0.001
    f32 field_f0;                  // +0xF0: third = 0.0001
    f32 field_f4;                  // +0xF4: `vstr s0,[r0,#0xf4]` = 1.0 (0x001187A8)
    f32 field_f8;                  // +0xF8: `vstr s0,[r0]` = 1.0 (0x001187B4)
    f32 field_fc;                  // +0xFC: `vstr s2,[r0,#4]` = pi/2 (0x001187B8)
};
static_assert(offsetof(AsdSceneLightData, field_48) == 0x48);
static_assert(offsetof(AsdSceneLightData, kind) == 0xB8);
static_assert(offsetof(AsdSceneLightData, field_dc) == 0xDC);
static_assert(offsetof(AsdSceneLightData, field_fc) == 0xFC);

/**
 * Observed prefix of the data block produced by the 0x0012B3B0 light object
 * (see `AsdScene_func_00118c7c`, 0x00118D00-0x00118DDC).
 */
struct AsdSceneEnvData {
    u8 pad_00[0xB8];
    u32 kind;                      // +0xB8: `str r5,[r1,#0xb8]` = 0 (0x00118D00)
    f32 color_r;                   // +0xBC: `vstr s0,[r0]` = 0.2 (0x00118D24)
    f32 color_g;                   // +0xC0: `vstr s0,[r0,#4]` = 0.2
    f32 color_b;                   // +0xC4: `vstr s0,[r0,#8]` = 0.2
    f32 color_a;                   // +0xC8: `vstr s17,[r0,#0xc]` = 1.0
    f32 field_cc;                  // +0xCC: `vstr s17,[r0]` = 1.0 (0x00118D54)
    f32 field_d0;                  // +0xD0: 1.0
    f32 field_d4;                  // +0xD4: 1.0
    f32 field_d8;                  // +0xD8: 1.0
    f32 field_dc;                  // +0xDC: `vstr s16,[r0]` = 0.8 (0x00118D88)
    f32 field_e0;                  // +0xE0: 0.8
    f32 field_e4;                  // +0xE4: `vstmia r0,{s16,s17}` first = 0.8
    f32 field_e8;                  // +0xE8: second = 1.0
    f32 field_ec;                  // +0xEC: `vstr s16,[r0]` = 0.8 (0x00118DB8)
    f32 field_f0;                  // +0xF0: 0.8
    f32 field_f4;                  // +0xF4: `vstmia r0,{s16,s17}` first = 0.8
    f32 field_f8;                  // +0xF8: second = 1.0
    u32 field_fc;                  // +0xFC: `str r1,[r0,#0xfc]` = key (0x00118D48)
    u32 field_100;                 // +0x100: `str r1,[r0,#0x100]` = key (0x00118D7C)
    u32 field_104;                 // +0x104: `str r1,[r0,#0x104]` = key (0x00118DAC)
    u32 field_108;                 // +0x108: `str r1,[r0,#0x108]` = key (0x00118DDC)
    f32 field_10c;                 // +0x10C: `vstr s1,[r0,#0x10c]` = -0.40824828 (0x00118D10)
    f32 field_110;                 // +0x110: `vstmia r1,{s0,s1}` first = -0.81649655
    f32 field_114;                 // +0x114: second = -0.40824828
};
static_assert(offsetof(AsdSceneEnvData, kind) == 0xB8);
static_assert(offsetof(AsdSceneEnvData, field_fc) == 0xFC);
static_assert(offsetof(AsdSceneEnvData, field_10c) == 0x10C);

/**
 * 0x10-byte fog record built by `AsdScene_func_0010bd34`
 * (`AsdMem_AllocAlign(..., 0x10, 1)`, 0x0010BD80).
 *
 * +0x00 is cleared, +0x04 is the object, +0x08 the object's data block and
 * +0x0C the relative fog-parameter block (`ldr r1,[r0,#0xc8]!` + add).
 */
struct AsdSceneFog {
    u32 field_00;                  // +0x00: `str r6,[r0]` = 0 (0x0010BD94)
    void* object;                  // +0x04: `str r0,[r4,#4]` (0x0010BDD0)
    void* data;                    // +0x08: `str r1,[r4,#8]` (0x0010BDD8)
    AsdSceneFogParams* params;     // +0x0C: `str r0,[r4,#0xc]` (0x0010BDFC)
};
static_assert(offsetof(AsdSceneFog, object) == 0x04);
static_assert(offsetof(AsdSceneFog, data) == 0x08);
static_assert(offsetof(AsdSceneFog, params) == 0x0C);
static_assert(sizeof(AsdSceneFog) == 0x10);

/**
 * Observed prefix of the 0x001203D8 fog object's data block.
 * 0x0010BDE0-0x0010BDFC writes +0xB4..+0xC8.
 */
struct AsdSceneFogData {
    u8 pad_00[0xB4];
    f32 field_b4;                  // +0xB4: `vstmia r1!,{s16}` = 0.3 (0x0010BDE0)
    f32 field_b8;                  // +0xB8: `vstmia r1,{s16,s17,s18}` first = 0.3
    f32 field_bc;                  // +0xBC: second = 0.5
    f32 field_c0;                  // +0xC0: third = 1.0
    u8 pad_c4[0x04];
    u32 params_rel;                // +0xC8: `ldr r1,[r0,#0xc8]!` (0x0010BDEC)
};
static_assert(offsetof(AsdSceneFogData, field_b4) == 0xB4);
static_assert(offsetof(AsdSceneFogData, params_rel) == 0xC8);

/**
 * Fog parameters resolved from `AsdSceneFogData::params_rel`.
 * 0x0010BE00-0x0010BE18 writes the four words; the block is owned by the fog
 * object, so only the offsets are asserted.
 */
struct AsdSceneFogParams {
    u32 kind;                      // +0x00: `str r8,[r0]` = 3 (0x0010BE00)
    f32 near_distance;             // +0x04: `vstr s19,[r0,#4]` = 100.0 (0x0010BE10)
    f32 far_distance;              // +0x08: `vstr s20,[r0,#8]` = 5000.0 (0x0010BE18)
    f32 density;                   // +0x0C: `vstr s21,[r0,#0xc]` = 10.0 (0x0010BE08)
};
static_assert(offsetof(AsdSceneFogParams, near_distance) == 0x04);
static_assert(offsetof(AsdSceneFogParams, far_distance) == 0x08);
static_assert(offsetof(AsdSceneFogParams, density) == 0x0C);

/**
 * Scene registry at `0x00464C00`.
 *
 * `ldr r0,[r8]` (0x0010E6B8) yields the slot block written by
 * `AsdScene_func_0010e5f0`; `ldr r0,[sb,#4]` (0x0010BE1C) yields the fog pointer
 * array written by `AsdScene_func_0010bd34`.
 */
struct AsdSceneSlot {
    void* nodes[2];                // +0x00: `str r4,[r0,r5,lsl #2]` (0x0010E6C0)
    void* effects[2];              // +0x08: `str r4,[r0,#8]` after `add r0,r0,r5,lsl #2` (0x0010E770)
    void* lights[2];               // +0x10: `str r0,[r1,#0x10]` (0x0010E780)
    void* environments[2];         // +0x18: `str r0,[r1,#0x18]` (0x0010E798)
};
static_assert(offsetof(AsdSceneSlot, effects) == 0x08);
static_assert(offsetof(AsdSceneSlot, lights) == 0x10);
static_assert(offsetof(AsdSceneSlot, environments) == 0x18);
static_assert(sizeof(AsdSceneSlot) == 0x20);

struct AsdSceneGlobals {
    AsdSceneSlot* slot;            // +0x00: `ldr r0,[r8]` (0x0010E6B8)
    AsdSceneFog** fogs;            // +0x04: `ldr r0,[sb,#4]` (0x0010BE1C)
};
static_assert(offsetof(AsdSceneGlobals, fogs) == 0x04);

// ---------------------------------------------------------------------------
// AsdProcess.cpp (0x00102E80, 0x00118488)
// ---------------------------------------------------------------------------

/**
 * Process node allocated by `AsdProcess_func_00118488` (0xA4 bytes,
 * `mov r3,#0xa4`, 0x001184BC).
 *
 * `name` is copied into +0x00..+0x17 and the signed-byte sum accumulates in
 * +0x18.  The copy loop also stores the byte at index 0x18 into the low byte of
 * the sum (0x001184FC `strb r1,[r4,r0]` runs before the `cmp r0,#0x18` bound
 * check), then +0x17 is forced to zero (0x0011851C).
 */
struct AsdProcessNode {
    char name[0x18];               // +0x00: `strb r1,[r4,r0]` (0x00118504)
    s32 name_hash;                 // +0x18: `str r1,[r4,#0x18]` (0x001184F8)
    u32 flags;                     // +0x1C: `orr r0,r0,#0x190000` / `str` (0x001185D0/0x001185D4)
    u32 bucket;                    // +0x20: `str r7,[r4,#0x20]` (0x00118518)
    u32 id;                        // +0x24: `str r1,[r4,#0x24]` (0x00118590)
    u32 handle;                    // +0x28: `str r1,[r4,#0x28]` (0x0011859C)
    u32 field_2c;                  // +0x2C: not touched here
    u32 field_30;                  // +0x30: not touched here
    u16 field_34;                  // +0x34: `strh r0,[r4,#0x34]` (0x001185A0)
    u16 field_36;                  // +0x36: `strh r2,[r4,#0x36]` (0x001185A4)
    f32 field_38;                  // +0x38: `vstmia r0,{s16,s17,s18}` first (0x001185B0)
    f32 field_3c;                  // +0x3C: second
    f32 field_40;                  // +0x40: third
    u8 pad_44[0x04];
    f32 field_48;                  // +0x48: `vstr s19,[r4,#0x48]` (0x001185A8)
    AsdProcessNode* next;          // +0x4C: `str sb,[r4,#0x4c]` (0x0011862C)
    AsdProcessNode* prev;          // +0x50: `str r2,[r4,#0x50]` (0x00118624)
    u8 pad_54[0x0C];               // +0x54..+0x60 (child links owned by 0x002C4460)
    void* command_list;            // +0x60: `str r0,[r4,#0x60]` (0x001185B8)
    u8 pad_64[0x08];
    u8 field_6c;                   // +0x6C: `strb r8,[r4,#0x6c]` = 1 (0x001185BC)
    u8 pad_6d[0x07];
    u8 field_74;                   // +0x74: `strb r8,[r4,#0x74]` = 1 (0x001185C0)
    u8 pad_75[0x07];
    u8 field_7c;                   // +0x7C: `strb r8,[r4,#0x7c]` = 1 (0x001185C4)
    u8 pad_7d[0x07];
    u8 field_84;                   // +0x84: `strb r8,[r4,#0x84]` = 1 (0x001185C8)
    u8 pad_85[0x13];
    u8 state;                      // +0x98: `strb r8,[r4,#0x98]` = 1 (0x00118520)
    u8 pad_99[0xA4 - 0x99];
};
static_assert(offsetof(AsdProcessNode, name_hash) == 0x18);
static_assert(offsetof(AsdProcessNode, flags) == 0x1C);
static_assert(offsetof(AsdProcessNode, bucket) == 0x20);
static_assert(offsetof(AsdProcessNode, id) == 0x24);
static_assert(offsetof(AsdProcessNode, handle) == 0x28);
static_assert(offsetof(AsdProcessNode, field_34) == 0x34);
static_assert(offsetof(AsdProcessNode, field_48) == 0x48);
static_assert(offsetof(AsdProcessNode, next) == 0x4C);
static_assert(offsetof(AsdProcessNode, prev) == 0x50);
static_assert(offsetof(AsdProcessNode, command_list) == 0x60);
static_assert(offsetof(AsdProcessNode, field_6c) == 0x6C);
static_assert(offsetof(AsdProcessNode, field_74) == 0x74);
static_assert(offsetof(AsdProcessNode, field_7c) == 0x7C);
static_assert(offsetof(AsdProcessNode, field_84) == 0x84);
static_assert(offsetof(AsdProcessNode, state) == 0x98);
static_assert(sizeof(AsdProcessNode) == 0xA4);

/**
 * Process registry at `0x004E3CF4`.
 *
 * `AsdProcess_func_00102e80` stores the 0x200-byte id table at 0x004E3D0C,
 * i.e. +0x18 (0x00102E98), fills it with byte 1 (0x00102E90) and sets
 * `next_id` to 1 (0x00102ECC).
 */
struct AsdProcessPool {
    AsdProcessNode** buckets;      // +0x00: `str r0,[r5],#0x14` (0x00102EC8)
    s32 bucket_count;              // +0x04: `str r4,[r5,#4]` (0x00102EA4)
    u32 field_08;                  // +0x08: untouched by these functions
    u32 process_count;             // +0x0C: `add r0+r0,#1` / `str` (0x00118634-0x00118638)
    u32 field_10;                  // +0x10: untouched
    u32 next_id;                   // +0x14: `str r6,[r5]` = 1 (0x00102ECC)
    u8 id_table[0x200];            // +0x18 (0x004E3D0C): filled with 1 (0x00102E90)
};
static_assert(offsetof(AsdProcessPool, bucket_count) == 0x04);
static_assert(offsetof(AsdProcessPool, process_count) == 0x0C);
static_assert(offsetof(AsdProcessPool, next_id) == 0x14);
static_assert(offsetof(AsdProcessPool, id_table) == 0x18);

// ---------------------------------------------------------------------------
// AsdSequence.cpp (0x002C59B8)
// ---------------------------------------------------------------------------

/** One 0x0C-byte entry of the sequence table. */
struct AsdSequenceEntry {
    u32 selector;                  // +0x00: tested by `cmp r1,#0` (0x002C59D4)
    u32 callback;                  // +0x04: tail-called through `bx r0` (0x002C5A5C)
    u32 field_08;                  // +0x08: third word selected by `4 + 12*index`
};
static_assert(sizeof(AsdSequenceEntry) == 0x0C);

/**
 * Sequence state at `0x004E3F4C`.
 *
 * The table pointer is `ldr r2,[r4]` (0x002C59CC); the current index is +0x08
 * (0x002C5A34), the requested index +0x0C (0x002C59E0) and the staging buffer
 * pair +0x10/+0x14 (`stm r1,{r0,r5}`, 0x002C5A18).
 */
struct AsdSequenceState {
    AsdSequenceEntry* table;       // +0x00: `ldr r2,[r4]` (0x002C59CC)
    u32 field_04;                  // +0x04: untouched here
    s32 current;                   // +0x08: `ldr r0,[r4,#8]` (0x002C5A34)
    u32 requested;                 // +0x0C: `str r0,[r4,#0xc]` (0x002C59E0)
    void* buffer;                  // +0x10: `stm r1,{r0,r5}` first (0x002C5A18)
    u32 buffer_size;               // +0x14: second word
};
static_assert(offsetof(AsdSequenceState, current) == 0x08);
static_assert(offsetof(AsdSequenceState, requested) == 0x0C);
static_assert(offsetof(AsdSequenceState, buffer) == 0x10);
static_assert(offsetof(AsdSequenceState, buffer_size) == 0x14);

// ---------------------------------------------------------------------------
// Task.c (0x002861F8)
// ---------------------------------------------------------------------------

/** One 0x10-byte priority list head in the five-entry array at `0x004C5830`. */
struct AsdTaskList {
    AsdTaskNode* head;             // +0x00: `str r0,[r4]` (0x002862F0)
    AsdTaskNode* tail;             // +0x04: `str r0,[r4,#4]` (0x00286330)
    u32 count;                     // +0x08: incremented at 0x00286384-0x00286390
    u32 field_0c;                  // +0x0C: untouched
};
static_assert(offsetof(AsdTaskList, tail) == 0x04);
static_assert(offsetof(AsdTaskList, count) == 0x08);
static_assert(sizeof(AsdTaskList) == 0x10);

/**
 * Task node allocated by `Task_func_002861f8`.  The allocation is
 * `0x34 + payload_size` (0x00286224/0x00286228) and the payload starts at
 * +0x34 (0x00286394 `add r4,r0,#0x34`).
 *
 * +0x1C is the previous link and +0x20 the next link (both set by the
 * insert-before-head sequence at 0x002862D8 and walked at 0x00286378).
 */
struct AsdTaskNode {
    u16 priority;                  // +0x00: `strh r7,[r0]` (0x00286268)
    u8 field_02;                   // +0x02: `strb r1,[r0,#2]` = 0 (0x00286274)
    u8 type;                       // +0x03: `strb r5,[r0,#3]` (0x00286260)
    u32 field_04;                  // +0x04: `str r1,[r0,#4]` = 0 (0x00286270)
    void* arg0;                    // +0x08: `stm r2,{sb,sl,fp}` first (0x00286278)
    void* arg1;                    // +0x0C: second
    void* arg2;                    // +0x10: third
    f32 arg3;                      // +0x14: `vstr s0,[r0,#0x14]` (0x00286280)
    f32 arg4;                      // +0x18: `vstr s16,[r0,#0x18]` (0x00286284)
    AsdTaskNode* prev;             // +0x1C: `str r1,[r0,#0x1c]` = 0 (0x00286290)
    AsdTaskNode* next;             // +0x20: `str r1,[r0,#0x20]` = 0 (0x00286294)
    u32 field_24;                  // +0x24: zeroed (0x00286298)
    u32 field_28;                  // +0x28: zeroed (0x0028629C)
    u32 field_2c;                  // +0x2C: zeroed (0x002862A0)
    u32 field_30;                  // +0x30: zeroed (0x002862A4)
    u8 payload_start;              // +0x34 (0x00286394); `payload_size` further bytes follow
};
static_assert(offsetof(AsdTaskNode, priority) == 0x00);
static_assert(offsetof(AsdTaskNode, type) == 0x03);
static_assert(offsetof(AsdTaskNode, arg0) == 0x08);
static_assert(offsetof(AsdTaskNode, arg3) == 0x14);
static_assert(offsetof(AsdTaskNode, prev) == 0x1C);
static_assert(offsetof(AsdTaskNode, next) == 0x20);
static_assert(offsetof(AsdTaskNode, field_24) == 0x24);
static_assert(offsetof(AsdTaskNode, field_30) == 0x30);
static_assert(offsetof(AsdTaskNode, payload_start) == 0x34);

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------

extern AsdCameraManager g_AsdCameraManager;      // 0x0044EA58 (observed prefix)
extern AsdCameraDefaults g_AsdCameraDefaults;    // 0x004D4924
extern AsdSceneGlobals g_AsdScene;               // 0x00464C00
extern AsdProcessPool g_AsdProcessPool;          // 0x004E3CF4
extern AsdSequenceState g_AsdSequence;           // 0x004E3F4C
extern AsdTaskList g_AsdTaskLists[];             // 0x004C5830, 5 entries (0x0032FF80), stride 0x10

// ---------------------------------------------------------------------------
// Reconstructed functions
// ---------------------------------------------------------------------------

// AsdCamera.cpp
void* AsdCamera_func_00105c50(void* name);
AsdCameraAnim* AsdCamera_func_00310124(AsdCameraScene* scene);

// AsdScene.cpp
void  AsdScene_func_0010bd34();
void  AsdScene_func_0010e5f0();
void* AsdScene_func_001186b4();
void* AsdScene_func_00118c7c();
void* AsdScene_func_002cb788();

// AsdProcess.cpp
void* AsdProcess_func_00102e80(u32 count);
u32   AsdProcess_func_00118488(const char* name, u32 bucket, u16 field_34,
                               u16 field_36, f32 field_38, f32 field_3c,
                               f32 field_40, f32 field_48, u32 parent);

// AsdSequence.cpp
void  AsdSequence_func_002c59b8(u32 index, const void* data, u32 size);

// Task.c
void* Task_func_002861f8(void* arg0, void* arg1, void* arg2, f32 arg3,
                         f32 arg4, u32 payload_size, u32 type, u16 priority,
                         u32 init_payload);

} // namespace smt4::engine
