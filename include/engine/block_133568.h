#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::engine {

/**
 * 0x00133568 (14,908 B) -- PICA200 pipeline state & render command sequencer.
 *
 * This function is the central GPU pipeline synchronizer for Shin Megami
 * Tensei IV. It is reached per draw/pass when dirty flags are set on the
 * render context. It inspects dirty bitmasks on the active GpuPassState
 * and GpuContext, emits PICA200 command packet headers and register payloads
 * into the GPU command buffer (*g_GpuCommandCursor), uploads vertex shader
 * float/bool uniforms, programs fragment lighting / material LUTs, sets up
 * texture samplers 0..3, and emits primitive draw packets.
 */

// GPU context state pointed to by g_LcdGpuState (0x004655C0)
struct GpuContext {
    u32 flags;              // +0x000 (dirty flags checked in caller/callee)
    u32 flags_04;           // +0x004
    u8  pad_008[0x004];     // +0x008
    u8  byte_0c;            // +0x00C
    u8  pad_00d[0x00B];     // +0x00D
    u8  byte_18;            // +0x018
    u8  byte_19;            // +0x019
    u8  pad_01a[0x02A];     // +0x01A
    f32 float_44;           // +0x044
    u8  pad_048[0x004];     // +0x048
    f32 float_4c[2];        // +0x04C
    u8  byte_54;            // +0x054
    u8  pad_055[0x117];     // +0x055
    u32 dword_16c;          // +0x16C
    u8  pad_170[0x010];     // +0x170
    u32 dword_180;          // +0x180
    u8  pad_184[0x06C];     // +0x184
    u32 dword_1f0;          // +0x1F0
    u32 dword_1f4;          // +0x1F4
    u32 dword_1f8;          // +0x1F8
    u32 dword_1fc;          // +0x1FC
    u32 dword_200;          // +0x200
    u32 dword_204;          // +0x204
    u8  pad_208[0x06C];     // +0x208
    u32 dword_274;          // +0x274
    u8  pad_278[0x010];     // +0x278
    u32 dword_288;          // +0x288
    u8  pad_28c[0x34C];     // +0x28C
    u32 dword_5d8;          // +0x5D8
    u8  pad_5dc[0x008];     // +0x5DC
    s32 scissor_x0;         // +0x5E4
    s32 scissor_y0;         // +0x5E8
    s32 scissor_w;          // +0x5EC
    s32 scissor_h;          // +0x5F0
    u8  pad_5f4[0x050];     // +0x5F4
    u32 dword_644;          // +0x644
    u8  scissor_enabled;    // +0x648
    u8  pad_649[0x001];     // +0x649
    u8  byte_64a;           // +0x64A
    u8  byte_64b;           // +0x64B
    u8  byte_64c;           // +0x64C
    u8  byte_64d;           // +0x64D
    u8  pad_64e[0x006];     // +0x64E
    u8  byte_654;           // +0x654
    u8  byte_655;           // +0x655
    u8  byte_656;           // +0x656
    u8  byte_657;           // +0x657
    u8  byte_658;           // +0x658
    u8  pad_659[0x003];     // +0x659
    u8  byte_65c;           // +0x65C
    u8  pad_65d[0x02B];     // +0x65D
    u32 dword_688;          // +0x688
    u32 dword_68c;          // +0x68C
    u8  pad_690[0x008];     // +0x690
    s32 screen_width;       // +0x698
    s32 screen_height;      // +0x69C
    u32 dword_6a0;          // +0x6A0
    u32 dword_6a4[16];      // +0x6A4..+0x6E0 (light distance array)
    u32 dword_6e4;          // +0x6E4
    u8  pad_6e8[0x084];     // +0x6E8
    u8  byte_76c;           // +0x76C
    u8  pad_76d[0x0AF];     // +0x76D
    u8  byte_81c;           // +0x81C
    u8  pad_81d[0x003];     // +0x81D
    u32 dword_820;          // +0x820
    u32 dword_824;          // +0x824
    u32 dword_828[16];      // +0x828..+0x864 (light assignment indices)
};

static_assert(offsetof(GpuContext, flags) == 0x000);
static_assert(offsetof(GpuContext, flags_04) == 0x004);
static_assert(offsetof(GpuContext, byte_0c) == 0x00C);
static_assert(offsetof(GpuContext, byte_18) == 0x018);
static_assert(offsetof(GpuContext, byte_19) == 0x019);
static_assert(offsetof(GpuContext, float_44) == 0x044);
static_assert(offsetof(GpuContext, float_4c) == 0x04C);
static_assert(offsetof(GpuContext, byte_54) == 0x054);
static_assert(offsetof(GpuContext, dword_16c) == 0x16C);
static_assert(offsetof(GpuContext, dword_180) == 0x180);
static_assert(offsetof(GpuContext, dword_1f0) == 0x1F0);
static_assert(offsetof(GpuContext, dword_1f4) == 0x1F4);
static_assert(offsetof(GpuContext, dword_1f8) == 0x1F8);
static_assert(offsetof(GpuContext, dword_1fc) == 0x1FC);
static_assert(offsetof(GpuContext, dword_200) == 0x200);
static_assert(offsetof(GpuContext, dword_204) == 0x204);
static_assert(offsetof(GpuContext, dword_274) == 0x274);
static_assert(offsetof(GpuContext, dword_288) == 0x288);
static_assert(offsetof(GpuContext, dword_5d8) == 0x5D8);
static_assert(offsetof(GpuContext, scissor_x0) == 0x5E4);
static_assert(offsetof(GpuContext, scissor_y0) == 0x5E8);
static_assert(offsetof(GpuContext, scissor_w) == 0x5EC);
static_assert(offsetof(GpuContext, scissor_h) == 0x5F0);
static_assert(offsetof(GpuContext, dword_644) == 0x644);
static_assert(offsetof(GpuContext, scissor_enabled) == 0x648);
static_assert(offsetof(GpuContext, byte_64a) == 0x64A);
static_assert(offsetof(GpuContext, byte_64b) == 0x64B);
static_assert(offsetof(GpuContext, byte_64c) == 0x64C);
static_assert(offsetof(GpuContext, byte_64d) == 0x64D);
static_assert(offsetof(GpuContext, byte_654) == 0x654);
static_assert(offsetof(GpuContext, byte_655) == 0x655);
static_assert(offsetof(GpuContext, byte_656) == 0x656);
static_assert(offsetof(GpuContext, byte_657) == 0x657);
static_assert(offsetof(GpuContext, byte_658) == 0x658);
static_assert(offsetof(GpuContext, byte_65c) == 0x65C);
static_assert(offsetof(GpuContext, dword_688) == 0x688);
static_assert(offsetof(GpuContext, dword_68c) == 0x68C);
static_assert(offsetof(GpuContext, screen_width) == 0x698);
static_assert(offsetof(GpuContext, screen_height) == 0x69C);
static_assert(offsetof(GpuContext, dword_6a0) == 0x6A0);
static_assert(offsetof(GpuContext, dword_6a4) == 0x6A4);
static_assert(offsetof(GpuContext, dword_6e4) == 0x6E4);
static_assert(offsetof(GpuContext, byte_76c) == 0x76C);
static_assert(offsetof(GpuContext, byte_81c) == 0x81C);
static_assert(offsetof(GpuContext, dword_820) == 0x820);
static_assert(offsetof(GpuContext, dword_824) == 0x824);
static_assert(offsetof(GpuContext, dword_828) == 0x828);

// Active material / pass state pointed to through 0x004652AC+8
struct GpuPassState {
    u8  pad_000[0x02C];     // +0x000
    u32 dword_2c;           // +0x02C
    u8  pad_030[0x180];     // +0x030
    u32 count_1b0;          // +0x1B0
    u32 mask_1b4[3];        // +0x1B4..+0x1BC
    u32 dword_1c0;          // +0x1C0
    u8  pad_1c4[0x180];     // +0x1C4
    u32 count_344;          // +0x344
    u32 mask_348[3];        // +0x348..+0x350
    u8  pad_354[0x0C0];     // +0x354
    void* dword_414;        // +0x414 (uniform descriptor)
    u32 dword_418;          // +0x418
    u32 dword_41c;          // +0x41C
    u8  pad_420[0x004];     // +0x420
    u8  byte_424;           // +0x424
    u8  byte_425;           // +0x425
    u8  pad_426[0x017];     // +0x426
    u8  byte_43d;           // +0x43D
    u8  byte_43e;           // +0x43E
    u8  pad_43f[0x101];     // +0x43F
    u32 dword_540;          // +0x540
    u32 dword_544;          // +0x544
    u8  pad_548[0x048];     // +0x548
    u32 dword_590;          // +0x590
    u32 dword_594;          // +0x594
    u8  pad_598[0x08C];     // +0x598
    u32 dword_624;          // +0x624
    u8  pad_628[0x008];     // +0x628
    u32 dword_630;          // +0x630
    u8  pad_634[0x18C];     // +0x634
    u32 dword_7c0;          // +0x7C0
    u8  pad_7c4[0x014];     // +0x7C4
    u32 dirty_masks[8];     // +0x7D8..+0x7F4
    u8  pad_7f8[0x078];     // +0x7F8
    u32 dword_870;          // +0x870
    u32 dword_874;          // +0x874
    u8  pad_878[0x07C];     // +0x878
    u32 dword_8f4;          // +0x8F4
    u8  pad_8f8[0x040];     // +0x8F8
    u32 dword_938;          // +0x938
    u32 dword_93c;          // +0x93C
    u32 lighting_words[39]; // +0x940..+0x9DB (0x27 words)
    u32 dword_9dc;          // +0x9DC
    u32 dword_9e0;          // +0x9E0
    u32 dword_9e4;          // +0x9E4
    u32 dword_9e8;          // +0x9E8
    u8  pad_9ec[0x020];     // +0x9EC
    u32 dword_a0c;          // +0xA0C
    u8  pad_a10[0x3E8];     // +0xA10
    u32 dword_df8;          // +0xDF8
    u32 tex_slots[4];       // +0xDFC..+0xE08
    u32 dword_e0c;          // +0xE0C
    u8  pad_e10[0x028];     // +0xE10
    u32 draw_mode_e38;      // +0xE38
    u8  pad_e3c[0x010];     // +0xE3C
    f32 float_e4c;          // +0xE4C
    u8  pad_e50[0x014];     // +0xE50
    u32 dword_e64;          // +0xE64
    u8  pad_e68[0x00C];     // +0xE68
    u8  byte_e74;           // +0xE74
    u8  pad_e75[0x003];     // +0xE75
    u32 tex_cube_slots[4];  // +0xE78..+0xE84
};

static_assert(offsetof(GpuPassState, dword_2c) == 0x02C);
static_assert(offsetof(GpuPassState, count_1b0) == 0x1B0);
static_assert(offsetof(GpuPassState, mask_1b4) == 0x1B4);
static_assert(offsetof(GpuPassState, dword_1c0) == 0x1C0);
static_assert(offsetof(GpuPassState, count_344) == 0x344);
static_assert(offsetof(GpuPassState, mask_348) == 0x348);
static_assert(offsetof(GpuPassState, dword_414) == 0x414);
static_assert(offsetof(GpuPassState, dword_418) == 0x418);
static_assert(offsetof(GpuPassState, dword_41c) == 0x41C);
static_assert(offsetof(GpuPassState, byte_424) == 0x424);
static_assert(offsetof(GpuPassState, byte_425) == 0x425);
static_assert(offsetof(GpuPassState, byte_43d) == 0x43D);
static_assert(offsetof(GpuPassState, byte_43e) == 0x43E);
static_assert(offsetof(GpuPassState, dword_540) == 0x540);
static_assert(offsetof(GpuPassState, dword_544) == 0x544);
static_assert(offsetof(GpuPassState, dword_590) == 0x590);
static_assert(offsetof(GpuPassState, dword_594) == 0x594);
static_assert(offsetof(GpuPassState, dword_624) == 0x624);
static_assert(offsetof(GpuPassState, dword_630) == 0x630);
static_assert(offsetof(GpuPassState, dword_7c0) == 0x7C0);
static_assert(offsetof(GpuPassState, dirty_masks) == 0x7D8);
static_assert(offsetof(GpuPassState, dword_870) == 0x870);
static_assert(offsetof(GpuPassState, dword_874) == 0x874);
static_assert(offsetof(GpuPassState, dword_8f4) == 0x8F4);
static_assert(offsetof(GpuPassState, dword_938) == 0x938);
static_assert(offsetof(GpuPassState, dword_93c) == 0x93C);
static_assert(offsetof(GpuPassState, lighting_words) == 0x940);
static_assert(offsetof(GpuPassState, dword_9dc) == 0x9DC);
static_assert(offsetof(GpuPassState, dword_9e0) == 0x9E0);
static_assert(offsetof(GpuPassState, dword_9e4) == 0x9E4);
static_assert(offsetof(GpuPassState, dword_9e8) == 0x9E8);
static_assert(offsetof(GpuPassState, dword_a0c) == 0xA0C);
static_assert(offsetof(GpuPassState, dword_df8) == 0xDF8);
static_assert(offsetof(GpuPassState, tex_slots) == 0xDFC);
static_assert(offsetof(GpuPassState, dword_e0c) == 0xE0C);
static_assert(offsetof(GpuPassState, draw_mode_e38) == 0xE38);
static_assert(offsetof(GpuPassState, float_e4c) == 0xE4C);
static_assert(offsetof(GpuPassState, dword_e64) == 0xE64);
static_assert(offsetof(GpuPassState, byte_e74) == 0xE74);
static_assert(offsetof(GpuPassState, tex_cube_slots) == 0xE78);

// Uniform buffer descriptor consumed by Stage 3 (0x001337c0)
struct UniformDescriptor {
    const void* data_00;        // +0x00
    u32         count_04;       // +0x04
    const void* data_08;        // +0x08
    u32         count_0c;       // +0x0C (accessed via pre-indexed ldr r2,[r0,#8]! writeback)
    const void* matrix_base_10; // +0x10
};
static_assert(offsetof(UniformDescriptor, data_00) == 0x00);
static_assert(offsetof(UniformDescriptor, count_04) == 0x04);
static_assert(offsetof(UniformDescriptor, data_08) == 0x08);
static_assert(offsetof(UniformDescriptor, count_0c) == 0x0C);
static_assert(offsetof(UniformDescriptor, matrix_base_10) == 0x10);

// Pipeline state at 0x004652AC
struct GpuPipelineState {
    u32 words[2];               // +0x00..+0x04
    GpuPassState** active_pass; // +0x08 (double indirection: ldr r1, [r0, #8]; ldr r4, [r1])
    u32 prev_flag_424;          // +0x0C (initialized to 0xFFFFFFFFu)
};
static_assert(sizeof(GpuPipelineState) == 0x10);
static_assert(offsetof(GpuPipelineState, words) == 0x00);
static_assert(offsetof(GpuPipelineState, active_pass) == 0x08);
static_assert(offsetof(GpuPipelineState, prev_flag_424) == 0x0C);

// 0x00133568: PICA200 pipeline state & render command sequencer
void func_00133568(GpuContext* gpu, u32 dirty_flags);

} // namespace smt4::engine
