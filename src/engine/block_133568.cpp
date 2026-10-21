#include "engine/block_133568.h"

#include <cmath>
#include <cstdint>
#include <cstring>

#include "engine/runtime_blocks.h"

namespace smt4::engine {

// ---------------------------------------------------------------------------
// External call targets
// ---------------------------------------------------------------------------

extern "C" {
    // 0x002AA908: retrieves texture/sampler object from global table by index.
    u32 func_002aa908(u32 index);

    // 0x002AA938: writes sequential PICA200 register packet to command buffer.
    void func_002aa938(u32 reg, u32 count, const void* data = nullptr);

    // 0x002AAA1C: writes chunked register array (e.g. uniform arrays) to command buffer.
    void func_002aaa1c(u32 reg, u32 count, const void* data);

    // 0x002AABB0: writes single register command packet header to command buffer.
    void func_002aabb0(u32 reg, u32 count);
}

namespace {

// ---------------------------------------------------------------------------
// .rodata constant tables recovered from binary
// ---------------------------------------------------------------------------

constexpr u32 kGpuConst_00409bf0[8] = {
    0x00000002u, 0x00000003u, 0x00000002u, 0x00000003u,
    0x00000000u, 0x00000001u, 0x00008B56u, 0x0042915Eu
};

constexpr u32 kGpuConst_0040b4e0[6] = {
    0x10u, 0x11u, 0x13u, 0x14u, 0x15u, 0x16u
};

constexpr u32 kGpuConst_0040b4f8[6] = {
    0x00u, 0x01u, 0x03u, 0x04u, 0x05u, 0x06u
};

// ---------------------------------------------------------------------------
// .data state tables recovered from binary (sentinel 0xBD)
// ---------------------------------------------------------------------------

const u32 kGpuStateTable_004652bc[] = {
    0x00u, 0x06u, 0x07u, 0x08u, 0x0Eu, 0x0Fu, 0x10u, 0x11u,
    0x12u, 0x13u, 0x14u, 0x15u, 0x16u, 0x19u, 0x1Au, 0x1Bu,
    0x1Cu, 0x1Du, 0x1Eu, 0x1Fu, 0x20u, 0x26u, 0x28u, 0xBDu
};

const u32 kGpuStateTable_0046531c[] = {
    0x09u, 0x0Au, 0x0Bu, 0x0Cu, 0x0Du, 0xBDu
};

const u32 kGpuStateTable_00465334[] = {
    0x01u, 0x02u, 0x03u, 0x04u, 0x05u, 0xBDu
};

const u32 kGpuStateTable_0046534c[] = {
    0x17u, 0x18u, 0x21u, 0x22u, 0x23u, 0x24u, 0x25u, 0x27u,
    0x29u, 0x2Au, 0x2Bu, 0x2Cu, 0x2Du, 0x2Eu, 0x2Fu, 0x30u,
    0x31u, 0x32u, 0x33u, 0x34u, 0x35u, 0x36u, 0x37u, 0x38u,
    0x39u, 0x3Au, 0x3Bu, 0x3Cu, 0x3Du, 0x3Eu, 0x3Fu, 0x40u,
    0x41u, 0x42u, 0x43u, 0x44u, 0x45u, 0x46u, 0x47u, 0x48u,
    0x49u, 0x4Au, 0x4Bu, 0x4Cu, 0x4Du, 0x4Eu, 0x4Fu, 0x54u,
    0x50u, 0x51u, 0x52u, 0x53u, 0x55u, 0x56u, 0x57u, 0x58u,
    0x59u, 0x5Au, 0x5Bu, 0x5Cu, 0x5Du, 0x5Eu, 0x5Fu, 0x60u,
    0x61u, 0x62u, 0x63u, 0x64u, 0x65u, 0x66u, 0x67u, 0x68u,
    0x69u, 0x6Au, 0x6Bu, 0x6Cu, 0x6Du, 0x6Eu, 0x6Fu, 0x70u,
    0x71u, 0x72u, 0x73u, 0x74u, 0x75u, 0x76u, 0x77u, 0x78u,
    0x79u, 0x7Au, 0x7Bu, 0x7Cu, 0x7Du, 0x7Eu, 0x7Fu, 0x80u,
    0x81u, 0x82u, 0x83u, 0x84u, 0x85u, 0x86u, 0x87u, 0x88u,
    0x89u, 0x8Au, 0x8Bu, 0x8Cu, 0x8Du, 0x8Eu, 0x8Fu, 0x90u,
    0x91u, 0x92u, 0x93u, 0x94u, 0x95u, 0x96u, 0x97u, 0x98u,
    0x99u, 0x9Au, 0x9Bu, 0x9Cu, 0x9Du, 0x9Eu, 0x9Fu, 0xA0u,
    0xA1u, 0xA2u, 0xA3u, 0xA4u, 0xA5u, 0xA6u, 0xA7u, 0xA8u,
    0xA9u, 0xAAu, 0xABu, 0xACu, 0xADu, 0xAEu, 0xAFu, 0xB0u,
    0xB1u, 0xB2u, 0xB3u, 0xB4u, 0xB5u, 0xB6u, 0xB7u, 0xB8u,
    0xB9u, 0xBAu, 0xBBu, 0xBCu, 0xBDu
};

// Pipeline state struct at 0x004652AC
struct GpuPipelineState {
    u32 words[2];               // +0x00..+0x04
    GpuPassState* active_pass;  // +0x08
    u32 prev_flag_424;          // +0x0C
    u32 sentinel;               // +0x10 (0xFFFFFFFF)
};

alignas(16) GpuPipelineState g_GpuPipelineState = {
    {0, 0},
    nullptr,
    0,
    0xFFFFFFFFu
};

using TextureAllocFn = void* (*)(u32 size, u32 align, u32 flags, u32 extra);
TextureAllocFn g_TextureAllocCallback = nullptr; // 0x0044E330

// Register map in BSS (0x004E4F54)
u32 g_GpuPicaRegisterMap[256] = {};

inline void EmitCmd(u32 param, u32 header) {
    if (g_GpuCommandCursor < g_GpuCommandEnd) {
        *g_GpuCommandCursor++ = param;
        *g_GpuCommandCursor++ = header;
    }
}

// Float depth encoding helper for Stage 11 (0x00135040..0x00135074)
inline u32 EncodeDepthFloat(f32 val) {
    u32 u = 0;
    std::memcpy(&u, &val, sizeof(u));
    if ((u & 0x7FFFFFFFu) == 0) {
        return 0;
    }
    s32 exp = static_cast<s32>((u >> 23) & 0xFFu) - 0x40;
    u32 mant = (u & 0x007FFFFFu) >> 8;
    u32 sign = u >> 31;
    if (exp >= 0) {
        return (sign << 23) | (static_cast<u32>(exp) << 16) | mant;
    }
    return sign << 23;
}

} // namespace

// ---------------------------------------------------------------------------
// 0x00133568: PICA200 pipeline state & render command sequencer
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00133568, 14908)
void func_00133568(GpuContext* gpu, u32 dirty_flags)
{
    // 0x00133578..0x001336a4: Stage 1 - Scissor and Viewport setup
    if ((dirty_flags & 0x1000u) && (gpu->flags & 0x200u)) {
        s32 x0, y0, x1, y1;
        u32 mode;
        if (gpu->scissor_enabled != 0) {
            x0 = gpu->scissor_x0;
            y0 = gpu->scissor_y0;
            x1 = gpu->scissor_w + x0 - 1;
            y1 = gpu->scissor_h + y0 - 1;

            if (gpu->screen_width <= x0) {
                x0 = gpu->screen_width - 1;
            }
            if (x0 < 0) {
                x0 = 0;
            }

            if (gpu->screen_height <= y0) {
                y0 = gpu->screen_height - 1;
            }
            if (y0 < 0) {
                y0 = 0;
            }

            if (gpu->screen_width <= x1) {
                x1 = gpu->screen_width - 1;
            }
            if (x1 < 0) {
                x1 = 0;
            }

            if (gpu->screen_height <= y1) {
                y1 = gpu->screen_height - 1;
            }
            if (y1 < 0) {
                y1 = 0;
            }
            mode = 3;
        } else {
            x0 = 0;
            y0 = 0;
            x1 = gpu->screen_width - 1;
            y1 = gpu->screen_height - 1;
            mode = 0;
        }

        // Emit scissor mode (reg 0x065), lower-left (0x066), upper-right (0x067)
        EmitCmd(mode, 0x000F0065u);
        EmitCmd(static_cast<u32>(x0) | (static_cast<u32>(y0) << 16), 0x000F0066u);
        EmitCmd(static_cast<u32>(x1) | (static_cast<u32>(y1) << 16), 0x000F0067u);
    }

    // 0x001336a4..0x001336b4: Fetch active pass pointer
    GpuPassState* pass = g_GpuPipelineState.active_pass;
    if (pass == nullptr) {
        return;
    }

    // 0x001336b8..0x001337c0: Stage 2 - Texture combiner / TEV stage configuration
    if (dirty_flags & 0x0004u) {
        u32 flag_424 = (pass->byte_424 != 0) ? 1u : 0u;
        if (flag_424 != g_GpuPipelineState.prev_flag_424 || (gpu->flags_04 & 4u)) {
            func_002aabb0(0x251, 10);
            func_002aabb0(0x200, 30);
            EmitCmd((flag_424 != 0) ? 2u : 0u, 0x00010229u);
            func_002aabb0(0x200, 30);
            g_GpuPipelineState.prev_flag_424 = flag_424;
            EmitCmd((flag_424 != 0) ? 1u : 0u, 0x00010244u);
        }
    }

    // 0x001337c0..0x001339b4: Stage 3 - Vertex shader float uniforms
    if ((dirty_flags & 0x0001u) && (gpu->flags & 0x100000u)) {
        struct UniformDescriptor {
            const void* data_00;
            u32 count_04;
            const void* data_08;
            const void* matrix_base_10;
        };
        auto* desc = reinterpret_cast<const UniformDescriptor*>(pass->dword_414);
        if (pass->byte_424 != 0) {
            EmitCmd(0u, 0x000F029Bu);
            if (desc != nullptr) {
                func_002aaa1c(0x29C, desc->count_04, desc->data_00);
            }
            EmitCmd(1u, 0x000F028Fu);
            EmitCmd(0u, 0x000F02A5u);
            if (desc != nullptr) {
                func_002aaa1c(0x2A6, desc->count_04, desc->data_08);
            }
        } else {
            if (desc != nullptr && desc->count_04 > 0x200u) {
                EmitCmd(0x200u, 0x000F029Bu);
                const u8* data_p = reinterpret_cast<const u8*>(desc->data_00) + 0x800;
                func_002aaa1c(0x29C, desc->count_04 - 0x200u, data_p);
                EmitCmd(1u, 0x000F028Fu);
            }
            EmitCmd(0u, 0x000F02CBu);
            if (desc != nullptr) {
                u32 c = desc->count_04 > 0x200u ? 0x200u : desc->count_04;
                func_002aaa1c(0x2CC, c, desc->data_00);
            }
            EmitCmd(1u, 0x000F02BFu);
            EmitCmd(0u, 0x000F02D5u);
            if (desc != nullptr) {
                func_002aaa1c(0x2D6, desc->count_04, desc->data_08);
            }
        }
    }

    // 0x001339b4..0x00133a4c: Stage 4 - VS uniform inverted bitmasks
    if (dirty_flags & 0x0004u) {
        if (pass->byte_424 != 0 && (gpu->flags & 0x800000u)) {
            for (u32 idx = 1; idx <= 8; ++idx) {
                u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + idx * 4);
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + idx * 4) = ~val;
            }
        }
        if (gpu->flags & 0x1000000u) {
            for (u32 idx = 9; idx <= 16; ++idx) {
                u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + idx * 4);
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + idx * 4) = ~val;
            }
        }
    }

    // 0x00133a4c..0x00133b20: Stage 5 - VS Matrix registers (0x290 / 0x2C0)
    if ((dirty_flags & 0x0008u) && (gpu->flags & 0x600000u)) {
        struct MatrixBlock {
            u8 pad_00[0x30];
            const void* matrix_data; // +0x30
            u32 matrix_count;        // +0x34
        };
        const u8* desc_base = reinterpret_cast<const u8*>(pass->dword_414);
        if (desc_base != nullptr) {
            const u8* matrix_base = *reinterpret_cast<const u8* const*>(desc_base + 0x10);
            if (pass->byte_424 != 0 && (gpu->flags & 0x400000u)) {
                u32 idx = pass->dword_41c;
                const auto* mb = reinterpret_cast<const MatrixBlock*>(matrix_base + idx * 232u);
                if (mb->matrix_count > 0) {
                    for (u32 i = 0; i < mb->matrix_count; ++i) {
                        func_002aa938(0x290, 4, reinterpret_cast<const u8*>(mb->matrix_data) + i * 16);
                    }
                }
            }
            if (gpu->flags & 0x200000u) {
                u32 idx = pass->dword_418;
                const auto* mb = reinterpret_cast<const MatrixBlock*>(matrix_base + idx * 232u);
                if (mb->matrix_count > 0) {
                    for (u32 i = 0; i < mb->matrix_count; ++i) {
                        func_002aa938(0x2C0, 4, reinterpret_cast<const u8*>(mb->matrix_data) + i * 16);
                    }
                }
            }
        }
    }

    // 0x00133b20..0x00134a1c: Stage 6 - Lighting and Materials
    if ((dirty_flags & 0x0200u) && (gpu->flags & 0x00008042u)) {
        gpu->byte_81c = 1;
        u32 active_count = 0;
        u32 inactive_count = 0;
        u32 inactive_list[16] = {};

        // Sort light sources
        for (s32 i = 15; i >= 0; --i) {
            u32 slot_valid = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x358 + i * 12);
            if (slot_valid != 0xFFFFFFFFu) {
                u8 light_type = *reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(gpu) + 0x46D + i * 24);
                if (light_type != 0) {
                    ++active_count;
                } else {
                    inactive_list[inactive_count++] = static_cast<u32>(i);
                }
            }
        }

        if (gpu->byte_76c != 0 || (active_count + inactive_count <= 12)) {
            // Check light configuration changes
            if (pass->dword_8f4 != active_count || pass->dword_938 != inactive_count || (gpu->flags_04 & 0x200u)) {
                pass->dword_8f4 = active_count;
                pass->dword_938 = inactive_count;

                // Update lighting registers
                func_002aa938(0x200, 0x27, pass->lighting_words);
                EmitCmd(pass->dword_9dc, 0x000F02BBu);
                EmitCmd(pass->dword_9e0, 0x000F02BCu);
                if (pass->byte_424 != 0) {
                    EmitCmd(pass->dword_9e4, 0x000F028Bu);
                    EmitCmd(pass->dword_9e8, 0x000F028Cu);
                }
                gpu->dword_820 = active_count;
                gpu->dword_824 = active_count + inactive_count;
            }
        }
    }

    // 0x00134a1c..0x00134c6c: Stages 7, 8, 9 - Uniform bool and register state tables
    if ((dirty_flags & 0x0010u) && (gpu->flags_04 & 0x0010u)) {
        pass->mask_1b4[0] = 0xFFFFFFFFu;
        pass->mask_1b4[1] = 0xFFFFFFFFu;
        pass->mask_1b4[2] = 0xFFFFFFFFu;
        for (u32 idx = 0; kGpuStateTable_0046531c[idx] != 0xBDu; ++idx) {
            u32 reg = kGpuStateTable_0046531c[idx];
            u8 flag = *reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(pass) + 0x426 + reg);
            if (flag != 0) {
                u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + reg * 4);
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + reg * 4) = ~val;
                pass->dirty_masks[reg >> 5] |= (1u << (reg & 0x1Fu));
            }
        }
        if (pass->byte_424 != 0) {
            pass->mask_348[0] = 0xFFFFFFFFu;
            pass->mask_348[1] = 0xFFFFFFFFu;
            pass->mask_348[2] = 0xFFFFFFFFu;
            for (u32 idx = 0; kGpuStateTable_00465334[idx] != 0xBDu; ++idx) {
                u32 reg = kGpuStateTable_00465334[idx];
                u8 flag = *reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(pass) + 0x426 + reg);
                if (flag != 0) {
                    u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + reg * 4);
                    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + reg * 4) = ~val;
                    pass->dirty_masks[reg >> 5] |= (1u << (reg & 0x1Fu));
                }
            }
        }
    }

    if ((dirty_flags & 0x0020u) && (gpu->flags_04 & 0x0020u)) {
        for (u32 idx = 0; kGpuStateTable_0046534c[idx] != 0xBDu; ++idx) {
            u32 reg = kGpuStateTable_0046534c[idx];
            u8 flag = *reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(pass) + 0x426 + reg);
            if (flag != 0) {
                u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + reg * 4);
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + reg * 4) = ~val;
                pass->dirty_masks[reg >> 5] |= (1u << (reg & 0x1Fu));
            }
        }
    }

    if ((dirty_flags & 0x0002u) && (gpu->flags_04 & 0x0002u)) {
        for (u32 idx = 0; kGpuStateTable_004652bc[idx] != 0xBDu; ++idx) {
            u32 reg = kGpuStateTable_004652bc[idx];
            u8 flag = *reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(pass) + 0x426 + reg);
            if (flag != 0) {
                u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + reg * 4);
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + reg * 4) = ~val;
                pass->dirty_masks[reg >> 5] |= (1u << (reg & 0x1Fu));
            }
        }
    }

    // 0x00134c6c..0x00134fd0: Stage 10 - Alpha/Stencil/Depth uniforms
    if (dirty_flags & 0x0010u) {
        if (pass->mask_1b4[0] || pass->mask_1b4[1] || pass->mask_1b4[2] ||
            pass->mask_348[0] || pass->mask_348[1] || pass->mask_348[2]) {
            if (pass->dword_1c0 != 0 && (pass->mask_348[0] || pass->mask_348[1] || pass->mask_348[2])) {
                EmitCmd(0x80000000u, 0x000F0290u);
                func_002aaa1c(0x291, pass->count_344 * 4, reinterpret_cast<const void*>(pass->dword_1c0));
            }
            if (pass->dword_2c != 0 && (pass->mask_1b4[0] || pass->mask_1b4[1] || pass->mask_1b4[2])) {
                EmitCmd(0x80000000u, 0x000F02C0u);
                func_002aaa1c(0x2C1, pass->count_1b0 * 4, reinterpret_cast<const void*>(pass->dword_2c));
            }
            pass->mask_1b4[0] = 0;
            pass->mask_1b4[1] = 0;
            pass->mask_1b4[2] = 0;
            pass->mask_348[0] = 0;
            pass->mask_348[1] = 0;
            pass->mask_348[2] = 0;
        }
    }

    // 0x00134fd0..0x001351a8: Stage 11 - Fog, Gas and Depth scale
    if ((dirty_flags & 0x0400u) && (gpu->flags & 4u)) {
        f32 near_f = pass->float_e4c;
        f32 far_f = 0.0f;
        if (near_f == 0.0f) {
            far_f = gpu->float_4c[0];
            near_f = gpu->float_4c[0] - gpu->float_4c[1];
        } else {
            near_f = -near_f;
        }

        if (gpu->byte_54 != 0 && gpu->float_44 != 0.0f) {
            f32 scale = (gpu->dword_68c != 0) ? 0.000015258789f : 0.00390631f;
            far_f += gpu->float_44 * scale;
        }

        u32 enc_near = EncodeDepthFloat(near_f);
        u32 enc_far = EncodeDepthFloat(far_f);

        pass->byte_43d |= 0x0Fu;
        pass->byte_43e |= 0x0Fu;

        if (gpu->byte_0c != 0) {
            pass->dword_540 = enc_near;
            pass->dirty_masks[0] |= 0x00800000u;
            gpu->flags |= 0x00080000u;
            *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x1068) = ~enc_near;
        } else if (pass->dword_540 != enc_near) {
            pass->dword_540 = enc_near;
            pass->dirty_masks[0] |= 0x00800000u;
            gpu->flags |= 0x00080000u;
        }

        if (gpu->byte_0c != 0) {
            pass->dword_544 = enc_far;
            pass->dirty_masks[0] |= 0x01000000u;
            gpu->flags |= 0x00080000u;
            *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x106C) = ~enc_far;
        } else if (pass->dword_544 != enc_far) {
            pass->dword_544 = enc_far;
            pass->dirty_masks[0] |= 0x01000000u;
            gpu->flags |= 0x00080000u;
        }
    }

    // 0x001351a8..0x00135248: Stage 12 - Cull mode / Primitive restart
    if (dirty_flags & 0x0020u) {
        if ((pass->dword_624 & 7u) == 7u && pass->byte_e74 == 0) {
            // Emits cull mode override
            EmitCmd(0u, 0x00010040u);
        }
    }

    // 0x00135248..0x00135474: Stage 13 - Uniform sync loop for table 0x00465334
    if (dirty_flags & 0x0010u) {
        for (u32 idx = 0; kGpuStateTable_00465334[idx] != 0xBDu; ++idx) {
            u32 reg = kGpuStateTable_00465334[idx];
            if (pass->dirty_masks[reg >> 5] & (1u << (reg & 0x1Fu))) {
                u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + reg * 4);
                u32 cached = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x100C + reg * 4);
                if (val != cached) {
                    EmitCmd(val, g_GpuPicaRegisterMap[reg]);
                    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + reg * 4) = val;
                }
                pass->dirty_masks[reg >> 5] &= ~(1u << (reg & 0x1Fu));
            }
        }
    }

    // 0x00135474..0x00135568: Stage 14 - Uniform sync loop for table 0x004652bc
    if (dirty_flags & 0x0002u) {
        for (u32 idx = 0; kGpuStateTable_004652bc[idx] != 0xBDu; ++idx) {
            u32 reg = kGpuStateTable_004652bc[idx];
            if (pass->dirty_masks[reg >> 5] & (1u << (reg & 0x1Fu))) {
                u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + reg * 4);
                u32 cached = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x100C + reg * 4);
                if (val != cached) {
                    EmitCmd(val, g_GpuPicaRegisterMap[reg]);
                    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + reg * 4) = val;
                }
                pass->dirty_masks[reg >> 5] &= ~(1u << (reg & 0x1Fu));
            }
        }
    }

    // 0x00135568..0x0013565c: Stage 15 - Uniform sync loop for table 0x0046534c
    if (dirty_flags & 0x0020u) {
        for (u32 idx = 0; kGpuStateTable_0046534c[idx] != 0xBDu; ++idx) {
            u32 reg = kGpuStateTable_0046534c[idx];
            if (pass->dirty_masks[reg >> 5] & (1u << (reg & 0x1Fu))) {
                u32 val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x4E4 + reg * 4);
                u32 cached = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x100C + reg * 4);
                if (val != cached) {
                    EmitCmd(val, g_GpuPicaRegisterMap[reg]);
                    *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x100C + reg * 4) = val;
                }
                pass->dirty_masks[reg >> 5] &= ~(1u << (reg & 0x1Fu));
            }
        }
    }

    // 0x0013565c..0x00136c4c: Stage 16 - Texture Units 0..3 & Samplers
    if ((dirty_flags & 0x0040u) && (pass->dword_590 & 1u) && (gpu->flags & 0x00004008u)) {
        for (u32 unit = 0; unit < 4; ++unit) {
            if ((pass->dword_a0c >> unit) & 1u) {
                u32 bit_idx = kGpuConst_0040b4e0[unit];
                if (!((pass->dword_7c0 >> bit_idx) & 1u)) {
                    u32 tex_idx = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x9F4 + unit * 4);
                    if (tex_idx != 0xFFFFFFFFu) {
                        u32 tex_obj = func_002aa908(tex_idx);
                        if (tex_obj != 0) {
                            u32 chan = kGpuConst_0040b4f8[unit];
                            EmitCmd(chan << 8, 0x000F01C5u);

                            // Dynamic allocation callback if buffer not yet allocated
                            if (g_TextureAllocCallback != nullptr) {
                                void* buf = g_TextureAllocCallback(0x10000u, 0x100u, 0u, 0x400u);
                                (void)buf;
                            }

                            // Upload sampler and coordinate transform registers
                            func_002aaa1c(0x0B0, 0x80, reinterpret_cast<const void*>(pass->dword_df8));
                        }
                    }
                }
            }
        }
        func_002aabb0(0x0C0, 0x2D);
    }

    // 0x00136c4c..0x00136fa4: Stage 17 - Primitive Geometry and Draw packet generation
    if (dirty_flags & 0x0800u) {
        if ((gpu->flags & 0x100u) || (pass->draw_mode_e38 != gpu->dword_644)) {
            gpu->dword_644 = pass->draw_mode_e38;

            // Emit index buffer configuration (registers 0x111, 0x110, 0x112)
            EmitCmd(1u, 0x000F0111u);
            EmitCmd(1u, 0x000F0110u);

            u32 mode_delta = pass->draw_mode_e38 - 0x6000u - 0x30u;
            if (mode_delta == 0) {
                // 0x00136dac: Mode 0x6030
                u32 p = 0;
                if (gpu->dword_688 == 1 || gpu->byte_64c != 0) {
                    p = 1;
                }
                p |= 2u;
                if (gpu->byte_64b != 0) {
                    p |= 4u;
                }
                if (gpu->byte_64a != 0 && gpu->byte_658 != 0) {
                    p |= 8u;
                }
                if (gpu->byte_64a != 0) {
                    p |= 0x10u;
                }
                if (gpu->byte_65c != 0) {
                    p |= 0x20u;
                }
                EmitCmd((p & 1u) ? 0xFu : 0u, 0x000F0112u);
                EmitCmd((p & 2u) ? 0xFu : 0u, 0x000F0112u);
                EmitCmd((p & 4u) ? 2u : 0u, 0x000F0112u);
                EmitCmd((p & 8u) ? 2u : 0u, 0x000F0123u);
            } else if (mode_delta == 0x18u) {
                // 0x00136f00: Mode 0x6048
                EmitCmd(0xFu, 0x000F0112u);
                EmitCmd(0xFu, 0x000F0112u);
                EmitCmd(0u, 0x000F0112u);
                EmitCmd(0u, 0x000F0123u);
            } else if (mode_delta == 0x21u) {
                // 0x00136d20: Mode 0x6051
                EmitCmd(0xFu, 0x000F0112u);
                EmitCmd(0xFu, 0x000F0112u);
                EmitCmd(3u, 0x000F0112u);
                EmitCmd(0u, 0x000F0123u);
            }
        }
    }
}

} // namespace smt4::engine
