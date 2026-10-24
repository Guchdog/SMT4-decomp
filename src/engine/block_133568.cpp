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
// .data state tables recovered from binary (0x004652BC)
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

// ---------------------------------------------------------------------------
// .data runtime state (0x004652AC)
// ---------------------------------------------------------------------------

alignas(16) GpuPipelineState g_GpuPipelineState = {
    {0, 0},
    nullptr,
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

#if 0
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

    // 0x001336a4..0x001336b4: Fetch active pass pointer via double indirection
    if (g_GpuPipelineState.active_pass == nullptr || *g_GpuPipelineState.active_pass == nullptr) {
        return;
    }
    GpuPassState* pass = *g_GpuPipelineState.active_pass;

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
        const auto* desc = reinterpret_cast<const UniformDescriptor*>(pass->dword_414);
        if (pass->byte_424 != 0) {
            EmitCmd(0u, 0x000F029Bu);
            if (desc != nullptr) {
                func_002aaa1c(0x29C, desc->count_04, desc->data_00);
            }
            EmitCmd(1u, 0x000F028Fu);
            EmitCmd(0u, 0x000F02A5u);
            if (desc != nullptr) {
                func_002aaa1c(0x2A6, desc->count_0c, desc->data_08);
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
                func_002aaa1c(0x2D6, desc->count_0c, desc->data_08);
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

    // 0x00133b20..0x00134a1c: Stage 6 - Fragment Lighting and Materials
    if ((dirty_flags & 0x0200u) && (gpu->flags & 0x00008042u)) {
        GpuPassState** pass_slot = g_GpuPipelineState.active_pass;
        if (pass_slot != nullptr) {
            pass_slot[1] = pass;
        }
        gpu->byte_81c = 1;
        u32 active_count = 0;
        u32 inactive_count = 0;
        u32 inactive_list[16] = {};

        struct LightNode {
            u32 light_idx;
            LightNode* next;
        };
        LightNode node_storage[16];
        LightNode* head = nullptr;
        u32 max_dist = 0;

        // Sort active light sources by distance in ascending order
        for (s32 i = 15; i >= 0; --i) {
            u32 slot_valid = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x358 + i * 12);
            if (slot_valid != 0xFFFFFFFFu) {
                u8 light_type = *reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(gpu) + 0x46D + i * 24);
                if (light_type == 0) {
                    inactive_list[inactive_count++] = static_cast<u32>(i);
                } else {
                    u32 light_val = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x468 + i * 24);
                    if (light_val == 0) {
                        gpu->byte_81c = 0;
                    } else {
                        u32 d = gpu->dword_6a4[i];
                        if (d > max_dist) {
                            max_dist = d;
                        }
                    }
                    LightNode* node = &node_storage[active_count++];
                    node->light_idx = static_cast<u32>(i);
                    node->next = nullptr;
                    if (head == nullptr || gpu->dword_6a4[i] <= gpu->dword_6a4[head->light_idx]) {
                        node->next = head;
                        head = node;
                    } else {
                        LightNode* curr = head;
                        while (curr->next != nullptr && gpu->dword_6a4[i] > gpu->dword_6a4[curr->next->light_idx]) {
                            curr = curr->next;
                        }
                        node->next = curr->next;
                        curr->next = node;
                    }
                }
            }
        }

        if (gpu->byte_76c != 0 || (active_count + inactive_count > 12)) {
            gpu->byte_81c = 0;
        }

        if (active_count > 0 && head != nullptr) {
            u32 base_dist = gpu->dword_6a4[head->light_idx] & ~0x0Fu;
            gpu->dword_6e4 = base_dist;
            if (gpu->byte_81c != 0) {
                if (gpu->byte_19 == 0) {
                    u32 r1 = base_dist;
                    u32 r2 = gpu->dword_6a0;
                    if (r2 < r1) r1 = r2;
                    if (r2 > max_dist) max_dist = r2;
                    if (max_dist - r1 >= 0x10000000u) {
                        gpu->byte_81c = 0;
                    }
                }
            }
        }

        bool config_changed = (pass->dword_8f4 != active_count ||
                               pass->dword_938 != inactive_count ||
                               (gpu->flags_04 & 0x200u));
        if (!config_changed) {
            LightNode* curr = head;
            for (u32 idx = 0; idx < active_count && curr != nullptr; ++idx, curr = curr->next) {
                u32 lidx = curr->light_idx;
                if (lidx != *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x7F0 + idx * 8)) {
                    config_changed = true;
                    break;
                }
            }
        }

        if (config_changed) {
            pass->dword_8f4 = active_count;
            pass->dword_938 = inactive_count;

            LightNode* curr = head;
            for (u32 idx = 0; idx < active_count && curr != nullptr; ++idx, curr = curr->next) {
                u32 lidx = curr->light_idx;
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(pass) + 0x7F0 + idx * 8) = lidx;
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(pass) + 0x874 + idx * 4) = gpu->dword_6a4[lidx];
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(pass) + 0x8B4 + idx * 4) =
                    *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x464 + lidx * 24);
                if (idx + 1 < active_count) {
                    *reinterpret_cast<void**>(reinterpret_cast<u8*>(pass) + 0x7F4 + idx * 8) =
                        reinterpret_cast<u8*>(pass) + 0x7F0 + (idx + 1) * 8;
                } else {
                    *reinterpret_cast<void**>(reinterpret_cast<u8*>(pass) + 0x7F4 + idx * 8) = nullptr;
                }
            }

            for (u32 idx = 0; idx < inactive_count; ++idx) {
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(pass) + 0x8F8 + idx * 4) = inactive_list[idx];
            }

            pass->dword_870 = reinterpret_cast<uintptr_t>(reinterpret_cast<u8*>(pass) + 0x7F0);

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

            u32 out_idx = 0;
            curr = head;
            while (curr != nullptr) {
                gpu->dword_828[out_idx++] = curr->light_idx;
                curr = curr->next;
            }
            for (u32 idx = 0; idx < inactive_count; ++idx) {
                gpu->dword_828[out_idx++] = inactive_list[idx];
            }
        }

        if (gpu->byte_81c != 0 && (gpu->flags & 0x000080C2u)) {
            for (u32 r2 = gpu->dword_820; r2 < gpu->dword_824; ++r2) {
                u32 ip = gpu->dword_828[r2];
                EmitCmd(r2, 0x000F0232u);
                EmitCmd(*reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x398 + ip * 12), 0x000F0233u);
                EmitCmd(*reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x39C + ip * 12), 0x000F0234u);
                EmitCmd(*reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x3A0 + ip * 12), 0x000F0235u);
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

    // 0x00134c6c..0x00134fd0: Stage 10 - Alpha/Stencil/Depth uniforms & Bit span scanner
    if (dirty_flags & 0x0010u) {
        // Scanner 1: mask_348
        if (pass->dword_1c0 != 0 &&
            (pass->mask_348[0] || pass->mask_348[1] || pass->mask_348[2])) {
            const u8* base_data = reinterpret_cast<const u8*>(pass->dword_1c0);
            u32 span_start = 0;
            u32 span_len = 0;
            const void* span_ptr = nullptr;

            for (u32 bit = 0; bit < pass->count_344; ++bit) {
                u32 word_idx = bit >> 5;
                u32 bit_idx = bit & 0x1Fu;
                if (pass->mask_348[word_idx] & (1u << bit_idx)) {
                    u32 reg = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x1C4 + bit * 4);
                    if (span_len > 0 && reg == span_start + span_len) {
                        ++span_len;
                    } else {
                        if (span_len > 0) {
                            EmitCmd(0x80000000u | span_start, 0x000F0290u);
                            func_002aaa1c(0x291, span_len * 4, span_ptr);
                        }
                        span_start = reg;
                        span_len = 1;
                        span_ptr = base_data + bit * 16;
                    }
                }
            }
            if (span_len > 0) {
                EmitCmd(0x80000000u | span_start, 0x000F0290u);
                func_002aaa1c(0x291, span_len * 4, span_ptr);
            }
        }

        // Scanner 2: mask_1b4
        if (pass->dword_2c != 0 &&
            (pass->mask_1b4[0] || pass->mask_1b4[1] || pass->mask_1b4[2])) {
            const u8* base_data = reinterpret_cast<const u8*>(pass->dword_2c);
            u32 span_start = 0;
            u32 span_len = 0;
            const void* span_ptr = nullptr;

            for (u32 bit = 0; bit < pass->count_1b0; ++bit) {
                u32 word_idx = bit >> 5;
                u32 bit_idx = bit & 0x1Fu;
                if (pass->mask_1b4[word_idx] & (1u << bit_idx)) {
                    u32 reg = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x030 + bit * 4);
                    if (span_len > 0 && reg == span_start + span_len) {
                        ++span_len;
                    } else {
                        if (span_len > 0) {
                            EmitCmd(0x80000000u | span_start, 0x000F02C0u);
                            func_002aaa1c(0x2C1, span_len * 4, span_ptr);
                        }
                        span_start = reg;
                        span_len = 1;
                        span_ptr = base_data + bit * 16;
                    }
                }
            }
            if (span_len > 0) {
                EmitCmd(0x80000000u | span_start, 0x000F02C0u);
                func_002aaa1c(0x2C1, span_len * 4, span_ptr);
            }
        }

        pass->mask_1b4[0] = 0;
        pass->mask_1b4[1] = 0;
        pass->mask_1b4[2] = 0;
        pass->mask_348[0] = 0;
        pass->mask_348[1] = 0;
        pass->mask_348[2] = 0;
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
        bool lut_updated = false;
        for (u32 unit = 0; unit < 6; ++unit) {
            if ((pass->dword_a0c >> unit) & 1u) {
                u32 bit_idx = kGpuConst_0040b4e0[unit];
                if (!((pass->dword_7c0 >> bit_idx) & 1u)) {
                    u32 tex_idx = *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(pass) + 0x9F4 + unit * 4);
                    if (tex_idx != 0xFFFFFFFFu) {
                        u32 tex_obj = func_002aa908(tex_idx);
                        if (tex_obj != 0) {
                            u32 chan = kGpuConst_0040b4f8[unit];
                            EmitCmd(chan << 8, 0x000F01C5u);

                            if (g_TextureAllocCallback != nullptr) {
                                void* buf = g_TextureAllocCallback(0x10000u, 0x100u, 0u, 0x400u);
                                (void)buf;
                            }

                            func_002aaa1c(0x1C8, 0x100, reinterpret_cast<const void*>(pass->dword_df8));
                            lut_updated = true;
                        }
                    }
                }
            }
        }

        if ((pass->dword_624 & 7u) && (gpu->flags & 0x00004010u)) {
            u32 tex_idx = pass->dword_e64;
            u32 tex_obj = func_002aa908(tex_idx);
            if (tex_obj != 0) {
                EmitCmd(0u, 0x000F00E6u);
            }
        }

        if (((pass->dword_624 & 7u) == 0) && (gpu->flags & 0x02004000u)) {
            u32 packed_luts[16] = {};
            for (u32 r8 = 0; r8 < 3; ++r8) {
                u32 tex_idx = pass->tex_cube_slots[r8];
                u32 tex_obj = func_002aa908(tex_idx);
                if (tex_obj != 0) {
                    if (g_TextureAllocCallback != nullptr) {
                        void* buf = g_TextureAllocCallback(0x10000u, 0x100u, 0u, 0x40u);
                        (void)buf;
                    }
                    for (u32 r0 = 0; r0 < 8; ++r0) {
                        packed_luts[r0] |= (r8 << (r8 * 8));
                    }
                }
            }

            if (!lut_updated) {
                func_002aabb0(0x0C0, 0x2D);
            }
            EmitCmd(0u, 0x000F0123u);
            func_002aaa1c(0x124, 0x10, packed_luts);
            EmitCmd(0x100u, 0x000F0110u);

            for (u32 r0 = 0; r0 < 3; ++r0) {
                u32 tex_idx = pass->tex_cube_slots[r0];
                *reinterpret_cast<u32*>(reinterpret_cast<u8*>(gpu) + 0x184 + r0 * 4) =
                    *reinterpret_cast<const u32*>(reinterpret_cast<const u8*>(gpu) + 0x74 + tex_idx * 4);
            }
        } else if (!lut_updated) {
            func_002aabb0(0x0C0, 0x2D);
        }
    }

    // 0x00136c4c..0x00136fa4: Stage 17 - Primitive Geometry and Draw packet generation
    if (dirty_flags & 0x0800u) {
        if ((gpu->flags & 0x100u) || (pass->draw_mode_e38 != gpu->dword_644)) {
            u32 packed_r0 = static_cast<u32>(gpu->byte_654) |
                            (static_cast<u32>(gpu->byte_655) << 1) |
                            (static_cast<u32>(gpu->byte_656) << 2) |
                            (static_cast<u32>(gpu->byte_657) << 3);

            gpu->dword_644 = pass->draw_mode_e38;

            // Emit index buffer configuration (registers 0x111, 0x110)
            EmitCmd(1u, 0x000F0111u);
            EmitCmd(1u, 0x000F0110u);

            u32 mode_delta = pass->draw_mode_e38 - 0x6000u - 0x30u;
            if (mode_delta == 0) {
                // 0x00136dac: Mode 0x6030
                u32 flags = 0;
                if (packed_r0 != 0) {
                    if (gpu->dword_688 == 1 || gpu->byte_64c != 0 ||
                        packed_r0 != 0x0Fu || gpu->byte_64d != 0) {
                        flags = 1;
                    }
                    flags |= 2;
                    if (gpu->byte_64b != 0) {
                        flags |= 4;
                        if (gpu->byte_658 != 0) {
                            flags |= 8;
                        }
                    }
                    if (gpu->byte_64a != 0) {
                        flags |= 0x10;
                        if (gpu->byte_65c != 0) {
                            flags |= 0x20;
                        }
                    }
                }

                EmitCmd((flags & 1u) ? 0xFu : 0u, 0x000F0112u);
                EmitCmd((flags & 2u) ? 0xFu : 0u, 0x000F0113u);

                u32 val3 = 0;
                if ((flags & 4u) && (flags & 0x0Au)) {
                    val3 |= 2u;
                }
                if ((flags & 0x10u) && (flags & 0x22u)) {
                    val3 |= 1u;
                }
                EmitCmd(val3, 0x000F0114u);

                u32 val4 = 0;
                if (flags & 8u) {
                    val4 |= 2u;
                }
                val4 |= (flags & 0x20u) >> 5;
                EmitCmd(val4, 0x000F0115u);
            } else if (mode_delta == 0x18u) {
                // 0x00136f00: Mode 0x6048
                EmitCmd(0xFu, 0x000F0113u);
                EmitCmd(0xFu, 0x000F0112u);
                EmitCmd(0u, 0x000F0114u);
                EmitCmd(0u, 0x000F0115u);
            } else if (mode_delta == 0x21u) {
                // 0x00136d20: Mode 0x6051
                EmitCmd(0xFu, 0x000F0113u);
                EmitCmd(0xFu, 0x000F0112u);
                EmitCmd(3u, 0x000F0114u);
                EmitCmd(0u, 0x000F0115u);
            }
        }
    }
}
#endif

// Readable PICA200 pipeline reconstruction above; exact ARM body retained while codegen is recovered.
// DECOMP_FUNC(0x00133568, 14908)
__attribute__((naked)) void func_00133568(GpuContext* gpu, u32 dirty_flags) {
    asm volatile(
        ".word 0xe92d4ff3, 0xed2d8b08, 0xe24ddb02, 0xe24dd034\n"
        ".word 0xe59d0858, 0xe3100a01, 0xe3a00000, 0xe58d0818\n"
        ".word 0xe59f0f54, 0xe5905000, 0x0a000043, 0xe59d0854\n"
        ".word 0xe5900000, 0xe3100c02, 0x0a00003f, 0xe5d50648\n"
        ".word 0xe3500000, 0x0a000073, 0xe2850b01, 0xe2800f79\n"
        ".word 0xe2851b01, 0xe8900011, 0xe2811f7b, 0xe5953698\n"
        ".word 0xe8910006, 0xe240c001, 0xe1530000, 0xe2446001\n"
        ".word 0xe081100c, 0xe0822006, 0xd2430001, 0xda000001\n"
        ".word 0xe3500000, 0xb3a00000, 0xe595c69c, 0xe15c0004\n"
        ".word 0xd24c4001, 0xda000001, 0xe3540000, 0xb3a04000\n"
        ".word 0xe1530001, 0xb2431001, 0xba000001, 0xe3510000\n"
        ".word 0xb3a01000, 0xe15c0002, 0xb24c2001, 0xba000001\n"
        ".word 0xe3520000, 0xb3a02000, 0xe3a03003, 0xe59fceac\n"
        ".word 0xe59f7eac, 0xe59c8000, 0xe5976000, 0xe1580006\n"
        ".word 0x2a000003, 0xe59f9e9c, 0xe288a008, 0xe8880208\n"
        ".word 0xe58ca000, 0xe59c3000, 0xe5976000, 0xe1530006\n"
        ".word 0x2a000004, 0xe59f8e80, 0xe1800804, 0xe2834008\n"
        ".word 0xe8830101, 0xe58c4000, 0xe5970000, 0xe59c3000\n"
        ".word 0xe1530000, 0x2a000004, 0xe59f4e60, 0xe1812802\n"
        ".word 0xe2831008, 0xe8830014, 0xe58c1000, 0xe59f0e50\n"
        ".word 0xe5901008, 0xe5914000, 0xe3540000, 0x0a000db7\n"
        ".word 0xe59d1858, 0xe3110004, 0x0a00003e, 0xe5d40424\n"
        ".word 0xe59f9e2c, 0xe2906000, 0x13a06001, 0xe599000c\n"
        ".word 0xe1560000, 0x1a000002, 0xe5950004, 0xe3100004\n"
        ".word 0x0a000034, 0xe59f0e0c, 0xe3a0100a, 0xeb05dd2d\n"
        ".word 0xe3a0101e, 0xe3a00c02, 0xeb05dd2a, 0xe59f7ddc\n"
        ".word 0xe59f8ddc, 0xe5971000, 0xe5980000, 0xe1510000\n"
        ".word 0x2a000007, 0xe59f2de0, 0xe3560000, 0x13a03002\n"
        ".word 0x03a03000, 0xe5812004, 0xe281c008, 0xe5813000\n"
        ".word 0xe587c000, 0xe3a0101e, 0xe3a00c02, 0xeb05dd19\n"
        ".word 0xe589600c, 0xe59f2db4, 0xe5980000, 0xe5971000\n"
        ".word 0xe3560000, 0x0a000010, 0xe1510000, 0x2a000015\n"
        ".word 0xe3a03001, 0xe5812004, 0xe281c008, 0xe5813000\n"
        ".word 0xe587c000, 0xea00000f, 0xe2851b01, 0xe2811fa6\n"
        ".word 0xe3a04000, 0xe8910006, 0xe1a00004, 0xe1a03004\n"
        ".word 0xe2411001, 0xe2422001, 0xeaffffa3, 0xe1510000\n"
        ".word 0x2a000004, 0xe3a03000, 0xe5812004, 0xe281c008\n"
        ".word 0xe5813000, 0xe587c000, 0xe59d0858, 0xe3100001\n"
        ".word 0x0a000079, 0xe59d0854, 0xe5900000, 0xe3100601\n"
        ".word 0x0a000075, 0xe5d40424, 0xe59f2d24, 0xe3500000\n"
        ".word 0xe242700c, 0x0a000028, 0xe59f6cf0, 0xe59f8cf0\n"
        ".word 0xe5961000, 0xe5980000, 0xe1500001, 0x9a000004\n"
        ".word 0xe3a03000, 0xe5812004, 0xe281c008, 0xe5813000\n"
        ".word 0xe586c000, 0xe5940414, 0xe5901004, 0xe5902000\n"
        ".word 0xe3a00fa7, 0xeb05dc7a, 0xe5981000, 0xe5960000\n"
        ".word 0xe1500001, 0x2a000003, 0xe3a02001, 0xe8800084\n"
        ".word 0xe2803008, 0xe5863000, 0xe5980000, 0xe5961000\n"
        ".word 0xe1510000, 0x2a000004, 0xe59f3ca8, 0xe3a02000\n"
        ".word 0xe281c008, 0xe1c120f0, 0xe586c000, 0xe5940414\n"
        ".word 0xe5b02008, 0xe5901004, 0xe59f0c8c, 0xeb05dc64\n"
        ".word 0xe320f000, 0xe320f000, 0xea00001d, 0xe5940414\n"
        ".word 0xe5900004, 0xe3500c02, 0x9a000019, 0xe59f6c3c\n"
        ".word 0xe59f8c3c, 0xe5961000, 0xe5980000, 0xe1510000\n"
        ".word 0x2a000004, 0xe3a03c02, 0xe5812004, 0xe281c008\n"
        ".word 0xe5813000, 0xe586c000, 0xe5940414, 0xe5901000\n"
        ".word 0xe5900004, 0xe2812b02, 0xe2401c02, 0xe3a00fa7\n"
        ".word 0xeb05dc4b, 0xe5980000, 0xe5961000, 0xe1510000\n"
        ".word 0x2a000003, 0xe3a02001, 0xe8810084, 0xe2813008\n"
        ".word 0xe5863000, 0xe59f7bd4, 0xe59f6bd4, 0xe5971000\n"
        ".word 0xe5960000, 0xe1510000, 0x2a000005, 0xe59f2bec\n"
        ".word 0xe3a0c000, 0xe2813008, 0xe5812004, 0xe581c000\n"
        ".word 0xe5873000, 0xe5940414, 0xe5901004, 0xe5902000\n"
        ".word 0xe3a00fb3, 0xe3510c02, 0x83a01c02, 0xeb05dc30\n"
        ".word 0xe5960000, 0xe5971000, 0xe1510000, 0x2a000004\n"
        ".word 0xe59f3bac, 0xe3a02001, 0xe281c008, 0xe1c120f0\n"
        ".word 0xe587c000, 0xe5961000, 0xe5970000, 0xe1500001\n"
        ".word 0x2a000004, 0xe59f3b8c, 0xe3a02000, 0xe280c008\n"
        ".word 0xe1c020f0, 0xe587c000, 0xe5940414, 0xe5b02008\n"
        ".word 0xe5901004, 0xe59f0b70, 0xeb05dc19, 0xe59d0858\n"
        ".word 0xe3100004, 0x0a000022, 0xe5d40424, 0xe3500000\n"
        ".word 0x0a00000f, 0xe59d0854, 0xe5900000, 0xe3100502\n"
        ".word 0x0a00000b, 0xe59f1b18, 0xe3a00001, 0xe5911008\n"
        ".word 0xe0843100, 0xe59334e4, 0xe0812100, 0xe2822a01\n"
        ".word 0xe2800001, 0xe1e03003, 0xe3500008, 0xe582300c\n"
        ".word 0x9afffff6, 0xe59d0854, 0xe5900000, 0xe3100401\n"
        ".word 0x0a00000b, 0xe59f1ad8, 0xe3a00009, 0xe5912008\n"
        ".word 0xe0843100, 0xe59334e4, 0xe0821100, 0xe2811a01\n"
        ".word 0xe2800001, 0xe1e03003, 0xe3500010, 0xe581300c\n"
        ".word 0x9afffff6, 0xe59d0858, 0xe3100008, 0x0a000031\n"
        ".word 0xe59d0854, 0xe5900000, 0xe3100606, 0x0a00002d\n"
        ".word 0xe5d41424, 0xe3510000, 0x13100501, 0x0a000012\n"
        ".word 0xe594041c, 0xe5941414, 0xe3a06000, 0xe0802080\n"
        ".word 0xe5911010, 0xe0620280, 0xe0817180, 0xe5970034\n"
        ".word 0xe3500000, 0x9a000008, 0xe5970030, 0xe3a01004\n"
        ".word 0xe0802206, 0xe3a00e29, 0xeb05dba0, 0xe5970034\n"
        ".word 0xe2866001, 0xe1500006, 0x8afffff6, 0xe59d0854\n"
        ".word 0xe5900000, 0xe3100602, 0x0a000012, 0xe5940418\n"
        ".word 0xe5941414, 0xe3a06000, 0xe0802080, 0xe5911010\n"
        ".word 0xe0620280, 0xe0817180, 0xe5970034, 0xe3500000\n"
        ".word 0x9a000008, 0xe5970030, 0xe3a01004, 0xe0802206\n"
        ".word 0xe3a00d0b, 0xeb05db89, 0xe5970034, 0xe2866001\n"
        ".word 0xe1500006, 0x8afffff6, 0xe59d0858, 0xe3100c02\n"
        ".word 0x0a0003b8, 0xe59d0854, 0xe59f19f0, 0xe5900000\n"
        ".word 0xe1100001, 0x0a000375, 0xe59f09b4, 0xe3a03001\n"
        ".word 0xe28da028, 0xe5902008, 0xe1a0000a, 0xe5921004\n"
        ".word 0xe1510004, 0x03a0c001, 0x13a0c000, 0xe3a01000\n"
        ".word 0xe58dc020, 0xe5824004, 0xe5c5381c, 0xe1a06001\n"
        ".word 0xe1a07001, 0xe1a08001, 0xe3a0c00f, 0xe58d102c\n"
        ".word 0xe08c108c, 0xe0842101, 0xe5922358, 0xe3720001\n"
        ".word 0x0a000033, 0xe0851181, 0xe5d1246d, 0xe3520000\n"
        ".word 0x0a000023, 0xe5911468, 0xe3510000, 0x03a01000\n"
        ".word 0x05c5181c, 0x0a000003, 0xe085110c, 0xe59116a4\n"
        ".word 0xe1510008, 0x81a08001, 0xe08a9186, 0xe3560000\n"
        ".word 0xe589c000, 0x0a000021, 0xe5901000, 0xe085210c\n"
        ".word 0xe59236a4, 0xe0851101, 0xe59116a4, 0xe1530001\n"
        ".word 0xd5890004, 0xd1a00009, 0xda000018, 0xe5901004\n"
        ".word 0xe1a02000, 0xe3510000, 0x0a000011, 0xe591b000\n"
        ".word 0xe085b10b, 0xe59bb6a4, 0xe153000b, 0xca000008\n"
        ".word 0xe5829004, 0xe3510000, 0xe5891004, 0x1a00000b\n"
        ".word 0xea000007, 0xe28d10b0, 0xe781c107, 0xe2877001\n"
        ".word 0xea000007, 0xe1a02001, 0xe5911004, 0xe3510000\n"
        ".word 0x1affffed, 0xe3a01000, 0xe5829004, 0xe5891004\n"
        ".word 0xe2866001, 0xe25cc001, 0x5affffc4, 0xe5d5176c\n"
        ".word 0xe3510000, 0x1a000002, 0xe0861007, 0xe351000c\n"
        ".word 0xda000001, 0xe3a01000, 0xe5c5181c, 0xe3560000\n"
        ".word 0x0a000012, 0xe5901000, 0xe0851101, 0xe59116a4\n"
        ".word 0xe3c1100f, 0xe58516e4, 0xe5d5281c, 0xe3520000\n"
        ".word 0x0a00000c, 0xe5d52019, 0xe3520000, 0x1a000004\n"
        ".word 0xe59526a0, 0xe1520001, 0x31a01002, 0xe1520008\n"
        ".word 0x81a08002, 0xe0481001, 0xe3510201, 0x3a000001\n"
        ".word 0xe3a01000, 0xe5c5181c, 0xe59418f4, 0xe1510006\n"
        ".word 0xe3a01001, 0xe58d1018, 0x05941938, 0x01510007\n"
        ".word 0x1a0000e7, 0xe5951004, 0xe3110c02, 0x1a0000e4\n"
        ".word 0xe5942870, 0xe3560000, 0xe1a09000, 0xe3a01000\n"
        ".word 0xda00003b, 0xe5993000, 0xe592c000, 0xe153000c\n"
        ".word 0x1a000011, 0xe5908000, 0xe084c101, 0xe085a103\n"
        ".word 0xe594b874, 0xe0858108, 0xe59aa6a4, 0xe59ce874\n"
        ".word 0xe59886a4, 0xe04eb00b, 0xe04a8008, 0xe158000b\n"
        ".word 0x1a000005, 0xe0833083, 0xe59c88b4, 0xe0853183\n"
        ".word 0xe593c464, 0xe15c0008, 0x0a000002, 0xe3a01000\n"
        ".word 0xe58d1018, 0xea000022, 0xe593c460, 0xe24ccb05\n"
        ".word 0xe25cc001, 0x03a0c001, 0x0a000005, 0xe35c0001\n"
        ".word 0x03a0c002, 0x0a000002, 0xe35c0005, 0x13a0c000\n"
        ".word 0x03a0c003, 0xe593845c, 0xe3e03003, 0xe3510008\n"
        ".word 0xe0833108, 0xe183300c, 0xe203c0ff, 0xaa000004\n"
        ".word 0xe5943944, 0xe1a08101, 0xe1a03833, 0xe203300f\n"
        ".word 0xea000004, 0xe5943948, 0xe1a08101, 0xe2488020\n"
        ".word 0xe1a03833, 0xe203300f, 0xe15c0003, 0x1affffde\n"
        ".word 0xe5999004, 0xe5922004, 0xe2811001, 0xe1510006\n"
        ".word 0xbaffffc3, 0xe3570000, 0xe3a01000, 0xc28d30b0\n"
        ".word 0xda000007, 0xe0842101, 0xe793c101, 0xe59228f8\n"
        ".word 0xe15c0002, 0x1a00009a, 0xe2811001, 0xe1510007\n"
        ".word 0xbafffff7, 0xe59d1018, 0xe3510000, 0x15d5181c\n"
        ".word 0x13510000, 0x0a000092, 0xe5d52019, 0xe59d1020\n"
        ".word 0xe3520000, 0x159536e4, 0x1a000003, 0xe59526a0\n"
        ".word 0xe59536e4, 0xe1520003, 0xb3c2300f, 0xe59526e4\n"
        ".word 0xe1520003, 0x05d42425, 0x03520000, 0x1a000006\n"
        ".word 0xe590c000, 0xe594294c, 0xe085c10c, 0xe59cc6a4\n"
        ".word 0xe04cc003, 0xe15c0002, 0x0a000018, 0xe5902000\n"
        ".word 0xe594193c, 0xe3a00001, 0xe0852102, 0xe3510001\n"
        ".word 0xe59226a4, 0xe0422003, 0xda00000a, 0xe0801080\n"
        ".word 0xe594c94c, 0xe0841101, 0xe2800001, 0xe591894c\n"
        ".word 0xe048c00c, 0xe08cc002, 0xe581c94c, 0xe594193c\n"
        ".word 0xe1510000, 0xcafffff4, 0xe584294c, 0xe59506e4\n"
        ".word 0xe3a01000, 0xe1500003, 0x03a00000, 0x05c40425\n"
        ".word 0xe1a0c1a3, 0xe58536e4, 0xe3510000, 0xe584c940\n"
        ".word 0x0a00000b, 0xe59f05b8, 0xe59f25b0, 0xe5901000\n"
        ".word 0xe5920000, 0xe1500001, 0x2a000274, 0xe59f35e0\n"
        ".word 0xe2806008, 0xe5803004, 0xe580c000, 0xe5826000\n"
        ".word 0xea00026e, 0xe59d0020, 0xe3500000, 0x0a000008\n"
        ".word 0xe594093c, 0xe2842d25, 0xe0800080, 0xe2801001\n"
        ".word 0xe3a00c02, 0xeb05da6d, 0xe320f000, 0xe320f000\n"
        ".word 0xea000262, 0xe2842d25, 0xe3a01027, 0xe3a00c02\n"
        ".word 0xeb05da66, 0xe59f1544, 0xe59f3544, 0xe5912000\n"
        ".word 0xe5930000, 0xe1520000, 0x2a000004, 0xe59489dc\n"
        ".word 0xe59fc570, 0xe2829008, 0xe8821100, 0xe5819000\n"
        ".word 0xe5912000, 0xe5930000, 0xe1520000, 0x2a000004\n"
        ".word 0xe59489e0, 0xe59fc550, 0xe2829008, 0xe8821100\n"
        ".word 0xe5819000, 0xe5d40424, 0xe3500000, 0x0a000012\n"
        ".word 0xe5912000, 0xe5930000, 0xe1520000, 0x2a000004\n"
        ".word 0xe59489e4, 0xe59fc524, 0xe2829008, 0xe8821100\n"
        ".word 0xe5819000, 0xe5932000, 0xe5910000, 0xe1500002\n"
        ".word 0x2a000005, 0xe59f3508, 0xe594c9e8, 0xe2808008\n"
        ".word 0xe5803004, 0xe580c000, 0xe5818000, 0xe5941870\n"
        ".word 0xe0862007, 0xe5852824, 0xe3560000, 0xe3a00000\n"
        ".word 0xe5856820, 0xda000006, 0xe5913000, 0xe0852100\n"
        ".word 0xe2800001, 0xe5823828, 0xe5911004, 0xe1560000\n"
        ".word 0xcafffff8, 0xe3570000, 0xe3a01000, 0xc28d30b0\n"
        ".word 0xda000222, 0xe7932101, 0xe085c100, 0xe2811001\n"
        ".word 0xe1570001, 0xe2800001, 0xe58c2828, 0xcafffff8\n"
        ".word 0xea00021a, 0xe3560000, 0xe1a02000, 0xe3a01000\n"
        ".word 0xc3a0a000, 0xc246c001, 0xda000016, 0xe5929000\n"
        ".word 0xe0843181, 0xe0848101, 0xe58397f0, 0xe5929000\n"
        ".word 0xe151000c, 0xe0859109, 0xe59996a4, 0xe5889874\n"
        ".word 0xe5929000, 0xe0899089, 0xe0859189, 0xe5999464\n"
        ".word 0xe58898b4, 0x0583a7f4, 0x0a000003, 0xe2838b01\n"
        ".word 0xe2888ffe, 0xe58387f4, 0xe5922004, 0xe2811001\n"
        ".word 0xe1510006, 0xbaffffe8, 0xe3570000, 0xe3a01000\n"
        ".word 0xc28d30b0, 0xda000005, 0xe793c101, 0xe0842101\n"
        ".word 0xe2811001, 0xe1570001, 0xe582c8f8, 0xcafffff9\n"
        ".word 0xe2841e7f, 0xe5841870, 0xe58468f4, 0xe5847938\n"
        ".word 0xe59515d8, 0xe3510000, 0xe5d51019, 0x0a000054\n"
        ".word 0xe3510000, 0x0a000056, 0xe59526e4, 0xe3a01000\n"
        ".word 0xe1a021c2, 0xe5842940, 0xe5c41425, 0xe5d5181c\n"
        ".word 0xe3510000, 0x0a000165, 0xe3a0c000, 0xe2851b01\n"
        ".word 0xe2811058, 0xe58dc0f0, 0xe58d1104, 0xe2851e6a\n"
        ".word 0xe58d10ac, 0xe2841b02, 0xe2811f4f, 0xe58dc010\n"
        ".word 0xe58d1100, 0xe2841b02, 0xe1a0200c, 0xe3a03001\n"
        ".word 0xe2811f53, 0xe584c93c, 0xe084c103, 0xe3a08000\n"
        ".word 0xe2833001, 0xe3530027, 0xe58c8940, 0xbafffff9\n"
        ".word 0xe3a03001, 0xe3560000, 0xe3a0c000, 0xe58d301c\n"
        ".word 0xda00012d, 0xe2843b02, 0xe2833f52, 0xe58d310c\n"
        ".word 0xe2843b02, 0xe2833f51, 0xe58d3110, 0xe59d30ac\n"
        ".word 0xe8900900, 0xe3a09000, 0xe593a044, 0xe58db108\n"
        ".word 0xe59db0ac, 0xe088e088, 0xe1a03009, 0xe08b8108\n"
        ".word 0xe085e18e, 0xe598b004, 0xe28e8b01, 0xe59ee460\n"
        ".word 0xe04ba00a, 0xe2888058, 0xe35e0b05, 0x03a03001\n"
        ".word 0xe58da024, 0x0a00000b, 0xe24eab05, 0xe25aa001\n"
        ".word 0x03a09001, 0x01a03009, 0x0a000006, 0xe35a0001\n"
        ".word 0x03a09002, 0x01a03009, 0x0a000002, 0xe35a0005\n"
        ".word 0x03a09003, 0x03a03004, 0xe598b004, 0xe3e0a003\n"
        ".word 0xe35c0008, 0xe08aa10b, 0xe189900a, 0xaa000014\n"
        ".word 0xe594a944, 0xe1a0b10c, 0xe18aab19, 0xe59d9110\n"
        ".word 0xea000014, 0xe3510000, 0x03a01000, 0x05c5181c\n"
        ".word 0x1affffa8, 0xe59516a0, 0xe59526e4, 0xe1510002\n"
        ".word 0xb3c1200f, 0xb3a01001, 0xa3a01000, 0xb58526e4\n"
        ".word 0xe5c41425, 0xe59516e4, 0xe1a011c1, 0xe5841940\n"
        ".word 0xeaffffa1, 0xe1a0b10c, 0xe594a948, 0xe24bb020\n"
        ".word 0xe18aab19, 0xe59d910c, 0xe589a000, 0xe598900c\n"
        ".word 0xe3590000, 0x0a000016, 0xe59d901c, 0xe598b004\n"
        ".word 0xe59da010, 0xe1530009, 0x91a0e009, 0xe00b039b\n"
        ".word 0x81a0e003, 0xe08aa003, 0xe2439001, 0xe24aa001\n"
        ".word 0xe1ca9009, 0xe089300b, 0xe3520000, 0xe58d3010\n"
        ".word 0xe58de01c, 0x0a000018, 0xe3520008, 0x2a000021\n"
        ".word 0xe5910004, 0xe1a03102, 0xe180031c, 0xe5810004\n"
        ".word 0xea000021, 0xe59d0024, 0xe5988004, 0xe5810000\n"
        ".word 0xe5910004, 0xe180900c, 0xe0000398, 0xe5819004\n"
        ".word 0xe5918008, 0xe3a03201, 0xe1830800, 0xe1800008\n"
        ".word 0xe5810008, 0xe594093c, 0xe281100c, 0xe2803001\n"
        ".word 0xe59d0100, 0xe5803000, 0xea0000b7, 0xe59d3024\n"
        ".word 0xe5813000, 0xe5909000, 0xe59d30ac, 0xe598000c\n"
        ".word 0xe0833109, 0xe58d00f0, 0xe5933004, 0xe0800003\n"
        ".word 0xe58d00fc, 0xeaffffdd, 0xe1a03102, 0xe5910008\n"
        ".word 0xe2433020, 0xe180031c, 0xe5810008, 0xe28c0001\n"
        ".word 0xe1500006, 0xe2822001, 0x0a00004a, 0xe59d0108\n"
        ".word 0xe59d30ac, 0xe59da024, 0xe5900000, 0xe5939044\n"
        ".word 0xe0833100, 0xe5933004, 0xe0439009, 0xe159000a\n"
        ".word 0x9a000040, 0xe080a080, 0xe59d0104, 0xe598800c\n"
        ".word 0xe080018a, 0xe590000c, 0xe1580000, 0x1a000039\n"
        ".word 0xe59d00fc, 0xe1530000, 0xaa000036, 0xe352000c\n"
        ".word 0x13a00000, 0x158d00f8, 0x0a000032, 0xe59d0024\n"
        ".word 0xe262800c, 0xe0493000, 0xe043000b, 0xe1a00120\n"
        ".word 0xe2103003, 0x13a03001, 0xe0833120, 0xe1530008\n"
        ".word 0x8a00006e, 0xe3500000, 0x0a000060, 0xe59d3010\n"
        ".word 0xe3100003, 0xe2833003, 0xe3c33003, 0xe0833100\n"
        ".word 0xe58d3010, 0x0a00002e, 0xe3520008, 0x2a000023\n"
        ".word 0xe5919004, 0xe2008003, 0xe1a03102, 0xe288800b\n"
        ".word 0xe1893318, 0xe5813004, 0xea000023, 0x004655c0\n"
        ".word 0x004652a0, 0x004652a4, 0x000f0065, 0x000f0066\n"
        ".word 0x000f0067, 0x004652ac, 0x00000251, 0x00010229\n"
        ".word 0x00010244, 0x000f029b, 0x000f02a5, 0x000002a6\n"
        ".word 0x000f02cb, 0x000f02bf, 0x000f02d5, 0x000002d6\n"
        ".word 0x00008042, 0x000f0200, 0x000f02bb, 0x000f02bc\n"
        ".word 0x000f028b, 0x000f028c, 0xe3a00001, 0xe58d00f8\n"
        ".word 0xe5913000, 0xe59d00f0, 0xe0839000, 0xeaffffc6\n"
        ".word 0xe1a03102, 0xe5919008, 0xe2008003, 0xe2433020\n"
        ".word 0xe288800b, 0xe1893318, 0xe5813008, 0xe2822001\n"
        ".word 0xe3c00003, 0xe3700106, 0x83a0300f, 0x9a00000f\n"
        ".word 0xe3520008, 0x2a000004, 0xe5919004, 0xe1a08102\n"
        ".word 0xe1898813, 0xe5818004, 0xea000004, 0xe1a08102\n"
        ".word 0xe5919008, 0xe2488020, 0xe1898813, 0xe5818008\n"
        ".word 0xe2500004, 0xe2822001, 0x1afffff0, 0xea000017\n"
        ".word 0xe3e03002, 0xe0430000, 0xe5918004, 0xe1a03fc0\n"
        ".word 0xe080ef23, 0xe1a0014e, 0xe2600000, 0xe3500000\n"
        ".word 0xda00000e, 0xe5919008, 0xe3a03000, 0xe3a0b00f\n"
        ".word 0xe082a003, 0xe35a0008, 0xe1a0a10a, 0x224aa020\n"
        ".word 0xe2833001, 0xe1a0aa1b, 0x3188800a, 0x2189900a\n"
        ".word 0xe2500001, 0x1afffff5, 0xe042214e, 0xe1c180f4\n"
        ".word 0xe59d00f8, 0xe3500000, 0x0a00001b, 0xe59d001c\n"
        ".word 0xe59d3010, 0xe0833000, 0xe2400001, 0xe2433001\n"
        ".word 0xe1c30000, 0xe59d30f0, 0xe1500003, 0x0a000002\n"
        ".word 0xe3a00000, 0xe5c5081c, 0xea000030, 0xe59d00f0\n"
        ".word 0xe5913008, 0xe1a08800, 0xe3a00001, 0xe58d001c\n"
        ".word 0xe3a00000, 0xe58d0010, 0xe1880e02, 0xe1800003\n"
        ".word 0xe5a10008, 0xe594093c, 0xe3a02000, 0xe2811004\n"
        ".word 0xe2803001, 0xe59d0100, 0xe5803000, 0xe59d0108\n"
        ".word 0xe28cc001, 0xe15c0006, 0xbafffed7, 0xe5d5081c\n"
        ".word 0xe3500000, 0x0a000019, 0xe3570000, 0xc2841b02\n"
        ".word 0xe3a00000, 0xc3a02801, 0xc2811f52, 0xda000006\n"
        ".word 0xe0803006, 0xe594c948, 0xe2800001, 0xe18c3312\n"
        ".word 0xe1570000, 0xe5813000, 0xcafffff8, 0xe3560000\n"
        ".word 0x0a000005, 0xe5941948, 0xe0862007, 0xe3a0320f\n"
        ".word 0xe0832e02, 0xe1811002, 0xe5841948, 0xe5d50019\n"
        ".word 0xe3500000, 0x0594093c, 0x0350000c, 0x0affffcb\n"
        ".word 0xe0860007, 0xe5856820, 0xe59f8c14, 0xe59f9c14\n"
        ".word 0xe5850824, 0xe5941870, 0xe3a03000, 0xe2842e9e\n"
        ".word 0xe58439dc, 0xe284cb02, 0xe8820308, 0xe3560000\n"
        ".word 0xe1a00003, 0xe28ccf77, 0xca000002, 0xea00001c\n"
        ".word 0xe3500008, 0xaa000009, 0xe5918000, 0xe59439dc\n"
        ".word 0xe1a09100, 0xe0888088, 0xe0848108, 0xe5988358\n"
        ".word 0xe208800f, 0xe1833918, 0xe58c3000, 0xea000009\n"
        ".word 0xe5918000, 0xe1a09100, 0xe59439e0, 0xe2499020\n"
        ".word 0xe0888088, 0xe0848108, 0xe5988358, 0xe208800f\n"
        ".word 0xe1833918, 0xe5823000, 0xe5918000, 0xe0853100\n"
        ".word 0xe2800001, 0xe5838828, 0xe5911004, 0xe1500006\n"
        ".word 0xbaffffe2, 0xe3570000, 0xe3a01000, 0xc28d30b0\n"
        ".word 0xda00001b, 0xe7936101, 0xe3500008, 0xaa000008\n"
        ".word 0xe0866086, 0xe59489dc, 0xe0846106, 0xe1a09100\n"
        ".word 0xe5966358, 0xe206600f, 0xe1886916, 0xe58c6000\n"
        ".word 0xea000008, 0xe0866086, 0xe1a08100, 0xe0846106\n"
        ".word 0xe59499e0, 0xe5966358, 0xe2488020, 0xe206600f\n"
        ".word 0xe1896816, 0xe5826000, 0xe7936101, 0xe0858100\n"
        ".word 0xe2811001, 0xe1510007, 0xe2800001, 0xe5886828\n"
        ".word 0xbaffffe3, 0xe2842d25, 0xe3a01027, 0xe3a00c02\n"
        ".word 0xeb05d832, 0xe51f338c, 0xe51f138c, 0xe5930000\n"
        ".word 0xe5912000, 0xe1500002, 0x2a000005, 0xe51f635c\n"
        ".word 0xe594c9dc, 0xe2807008, 0xe5806004, 0xe580c000\n"
        ".word 0xe5837000, 0xe5932000, 0xe5910000, 0xe1520000\n"
        ".word 0x2a000004, 0xe59469e0, 0xe51fc384, 0xe2827008\n"
        ".word 0xe8821040, 0xe5837000, 0xe5d40424, 0xe3500000\n"
        ".word 0x0a000012, 0xe5932000, 0xe5910000, 0xe1520000\n"
        ".word 0x2a000004, 0xe59469e4, 0xe51fc3b0, 0xe2827008\n"
        ".word 0xe8821040, 0xe5837000, 0xe5911000, 0xe5930000\n"
        ".word 0xe1500001, 0x2a000005, 0xe51f23cc, 0xe594c9e8\n"
        ".word 0xe2806008, 0xe5802004, 0xe580c000, 0xe5836000\n"
        ".word 0xe5d5081c, 0xe3500000, 0x0a00003a, 0xe59d0854\n"
        ".word 0xe59f1a24, 0xe5900000, 0xe1100001, 0x0a000035\n"
        ".word 0xe5950824, 0xe5952820, 0xe1500002, 0x9a000031\n"
        ".word 0xe59f8a08, 0xe51f046c, 0xe1887341, 0xe088b741\n"
        ".word 0xe087e741, 0xe51f1478, 0xe085c102, 0xe5903000\n"
        ".word 0xe59cc828, 0xe5916000, 0xe1530006, 0x2a000002\n"
        ".word 0xe8830104, 0xe2839008, 0xe5809000, 0xe5903000\n"
        ".word 0xe5916000, 0xe1530006, 0x2a000006, 0xe08c908c\n"
        ".word 0xe283a008, 0xe0859109, 0xe5999398, 0xe5837004\n"
        ".word 0xe5839000, 0xe580a000, 0xe5903000, 0xe5916000\n"
        ".word 0xe1530006, 0x2a000005, 0xe08c908c, 0xe283a008\n"
        ".word 0xe0859109, 0xe599939c, 0xe8830a00, 0xe580a000\n"
        ".word 0xe5916000, 0xe5903000, 0xe1530006, 0x2a000005\n"
        ".word 0xe08c608c, 0xe2839008, 0xe0856106, 0xe59663a0\n"
        ".word 0xe8834040, 0xe5809000, 0xe5953824, 0xe2822001\n"
        ".word 0xe1530002, 0x8affffd3, 0xe5950004, 0xe3500000\n"
        ".word 0x0a000093, 0xe59d1858, 0xe2011010, 0xe1100001\n"
        ".word 0x0a000047, 0xe59f0928, 0xe3e03000, 0xe58431bc\n"
        ".word 0xe58431b8, 0xe58431b4, 0xe5902000, 0xe3a01000\n"
        ".word 0xe35200bd, 0x0a000019, 0xe2402070, 0xe284cb01\n"
        ".word 0xe5926008, 0xe3a07001, 0xe28cc026, 0xe7902101\n"
        ".word 0xe7d2800c, 0xe3580000, 0x0a00000c, 0xe0848102\n"
        ".word 0xe0862102, 0xe59884e4, 0xe2829a01, 0xe1e02008\n"
        ".word 0xe589200c, 0xe7902101, 0xe202901f, 0xe1a082c2\n"
        ".word 0xe0842108, 0xe59287d8, 0xe1888917, 0xe58287d8\n"
        ".word 0xe2811001, 0xe7902101, 0xe35200bd, 0x1affffea\n"
        ".word 0xe5d40424, 0xe3500000, 0x0a000021, 0xe59f2894\n"
        ".word 0xe5843350, 0xe584334c, 0xe5843348, 0xe5920000\n"
        ".word 0xe3a01000, 0xe35000bd, 0x0a000019, 0xe2420088\n"
        ".word 0xe2843b01, 0xe590c008, 0xe3a06001, 0xe2833026\n"
        ".word 0xe7920101, 0xe7d07003, 0xe3570000, 0x0a00000c\n"
        ".word 0xe0847100, 0xe08c0100, 0xe59774e4, 0xe2800a01\n"
        ".word 0xe1e07007, 0xe580700c, 0xe7920101, 0xe200801f\n"
        ".word 0xe1a072c0, 0xe0840107, 0xe59077d8, 0xe1877816\n"
        ".word 0xe58077d8, 0xe2811001, 0xe7920101, 0xe35000bd\n"
        ".word 0x1affffea, 0xe59d0858, 0xe5951004, 0xe2000020\n"
        ".word 0xe1100001, 0x0a00001e, 0xe59f17fc, 0xe3a00000\n"
        ".word 0xe5912000, 0xe35200bd, 0x0a000019, 0xe24120a0\n"
        ".word 0xe284cb01, 0xe5926008, 0xe3a03001, 0xe28cc026\n"
        ".word 0xe7912100, 0xe7d2700c, 0xe3570000, 0x0a00000c\n"
        ".word 0xe0847102, 0xe0862102, 0xe59774e4, 0xe2822a01\n"
        ".word 0xe1e07007, 0xe582700c, 0xe7912100, 0xe202801f\n"
        ".word 0xe1a072c2, 0xe0842107, 0xe59277d8, 0xe1877813\n"
        ".word 0xe58277d8, 0xe2800001, 0xe7912100, 0xe35200bd\n"
        ".word 0x1affffea, 0xe59d0858, 0xe5951004, 0xe2000002\n"
        ".word 0xe1100001, 0x0a00001e, 0xe59f1770, 0xe3a00000\n"
        ".word 0xe5912000, 0xe35200bd, 0x0a000019, 0xe2412010\n"
        ".word 0xe284cb01, 0xe5923008, 0xe3a06001, 0xe28cc026\n"
        ".word 0xe7912100, 0xe7d2700c, 0xe3570000, 0x0a00000c\n"
        ".word 0xe0847102, 0xe0838102, 0xe59724e4, 0xe59f7730\n"
        ".word 0xe1e02002, 0xe7872008, 0xe7912100, 0xe202801f\n"
        ".word 0xe1a072c2, 0xe0842107, 0xe59277d8, 0xe1877816\n"
        ".word 0xe58277d8, 0xe2800001, 0xe7912100, 0xe35200bd\n"
        ".word 0x1affffea, 0xe59d0858, 0xe3100010, 0x0a0000d5\n"
        ".word 0xe59401b4, 0xe3500000, 0x059401b8, 0x03500000\n"
        ".word 0x1a000009, 0xe59401bc, 0xe3500000, 0x05940348\n"
        ".word 0x03500000, 0x1a000004, 0xe594034c, 0xe3500000\n"
        ".word 0x05940350, 0x03500000, 0x0a0000c6, 0xe59491c0\n"
        ".word 0xe3590000, 0x0a00005c, 0xe5940348, 0xe3500000\n"
        ".word 0x0594134c, 0x03510000, 0x05941350, 0x03510000\n"
        ".word 0x0a000055, 0xe3a02000, 0xe3100001, 0xe3a07001\n"
        ".word 0xe1a0c002, 0xe1a0a002, 0xe1a06002, 0x1a00000d\n"
        ".word 0xe1a012a6, 0xe206001f, 0xe0841101, 0xe5911348\n"
        ".word 0xe1b00031, 0x03c6001f, 0x02806020, 0x12866001\n"
        ".word 0xe206301f, 0xe1a002a6, 0xe0840100, 0xe5901348\n"
        ".word 0xe1110317, 0x0afffff1, 0xe5940344, 0xe1500006\n"
        ".word 0x9a00003d, 0xe0840106, 0xe3520000, 0xe59081c4\n"
        ".word 0x0a000013, 0xe048000c, 0xe150000a, 0x028aa001\n"
        ".word 0x0a000012, 0xe51f0878, 0xe51f3880, 0xe5901000\n"
        ".word 0xe5930000, 0xe1500001, 0x2a000006, 0xe1a0e003\n"
        ".word 0xe59f35f0, 0xe38cc102, 0xe280b008, 0xe5803004\n"
        ".word 0xe580c000, 0xe58eb000, 0xe59f05dc, 0xe1a0110a\n"
        ".word 0xeb05d71f, 0xe1a0c008, 0xe3a0a001, 0xe0892206\n"
        ".word 0xe5940344, 0xe2866001, 0xe206801f, 0xe1a012a6\n"
        ".word 0xe0841101, 0xe5911348, 0xe1110817, 0x1a000007\n"
        ".word 0xea000004, 0xe1b01831, 0x03c6101f, 0x02816020\n"
        ".word 0x12866001, 0xeafffff3, 0xe1500006, 0x8afffff8\n"
        ".word 0xe1500006, 0x8affffd2, 0xe3520000, 0x0a00000e\n"
        ".word 0xe51f3918, 0xe51f0918, 0xe5931000, 0xe5900000\n"
        ".word 0xe1510000, 0x2a000005, 0xe59f6558, 0xe38cc102\n"
        ".word 0xe2817008, 0xe5816004, 0xe581c000, 0xe5837000\n"
        ".word 0xe59f0544, 0xe1a0110a, 0xeb05d6f9, 0xe594902c\n"
        ".word 0xe3590000, 0x0a00005c, 0xe59401b4, 0xe3500000\n"
        ".word 0x059411b8, 0x03510000, 0x059411bc, 0x03510000\n"
        ".word 0x0a000055, 0xe3a02000, 0xe3100001, 0xe3a08001\n"
        ".word 0xe1a0b002, 0xe1a0c002, 0xe1a06002, 0x1a00000d\n"
        ".word 0xe1a002a6, 0xe206101f, 0xe0840100, 0xe59001b4\n"
        ".word 0xe1b00130, 0x03c6001f, 0x02806020, 0x12866001\n"
        ".word 0xe206301f, 0xe1a002a6, 0xe0840100, 0xe59011b4\n"
        ".word 0xe1110318, 0x0afffff1, 0xe59401b0, 0xe1500006\n"
        ".word 0x9a00003d, 0xe0840106, 0xe3520000, 0xe5907030\n"
        ".word 0x0a000013, 0xe047000b, 0xe150000c, 0x028cc001\n"
        ".word 0x0a000012, 0xe51f09f8, 0xe51f3a00, 0xe5901000\n"
        ".word 0xe5930000, 0xe1500001, 0x2a000006, 0xe1a0e003\n"
        ".word 0xe59f3478, 0xe38ba102, 0xe280b008, 0xe5803004\n"
        ".word 0xe580a000, 0xe58eb000, 0xe59f0464, 0xe1a0110c\n"
        ".word 0xeb05d6bf, 0xe1a0b007, 0xe3a0c001, 0xe0892206\n"
        ".word 0xe59411b0, 0xe2866001, 0xe206301f, 0xe1a002a6\n"
        ".word 0xe0840100, 0xe590a1b4, 0xe11a0318, 0x1a000007\n"
        ".word 0xea000004, 0xe1b0033a, 0x03c6001f, 0x02806020\n"
        ".word 0x12866001, 0xeafffff3, 0xe1510006, 0x8afffff8\n"
        ".word 0xe1510006, 0x8affffd2, 0xe3520000, 0x0a00000e\n"
        ".word 0xe51f1a98, 0xe51f0a98, 0xe5913000, 0xe5900000\n"
        ".word 0xe1530000, 0x2a000005, 0xe59f63e0, 0xe38b8102\n"
        ".word 0xe2837008, 0xe5836004, 0xe5838000, 0xe5817000\n"
        ".word 0xe59f03cc, 0xe1a0110c, 0xeb05d699, 0xe3a00000\n"
        ".word 0xe58401b4, 0xe58401b8, 0xe58401bc, 0xe5840348\n"
        ".word 0xe584034c, 0xe5840350, 0xe59d0858, 0xeddf8ae9\n"
        ".word 0xe3100b01, 0x0a000071, 0xe59d0854, 0xe5900000\n"
        ".word 0xe3100004, 0x0a00006d, 0xe2840b03, 0xedd00a93\n"
        ".word 0xeef40a68, 0xeef1fa10, 0x0285004c, 0x0c900a02\n"
        ".word 0xe5d50054, 0x0e700a60, 0x1eb00a68, 0x1ef10a60\n"
        ".word 0xe3500000, 0x1d951a11, 0x1eb41a68, 0x1ef1fa10\n"
        ".word 0x0a000004, 0xe595068c, 0xe3500000, 0x1ddf1ad2\n"
        ".word 0x0ddf1ad2, 0xee010a21, 0xee100a90, 0xe3d01102\n"
        ".word 0x0a000002, 0xe1a01080, 0xe1a01c21, 0xe2411040\n"
        ".word 0xe1a02480, 0xeeb40a68, 0xe3510000, 0xe1a02822\n"
        ".word 0xe1a00fa0, 0xa1821801, 0xa1812b80, 0xb1a02b80\n"
        ".word 0xeef1fa10, 0x03a00000, 0x0a00000c, 0xee100a10\n"
        ".word 0xe3d01102, 0x0a000002, 0xe1a01080, 0xe1a01c21\n"
        ".word 0xe2411040, 0xe1a03480, 0xe3510000, 0xe1a03823\n"
        ".word 0xe1a00fa0, 0xa1831801, 0xa1810b80, 0xb1a00b80\n"
        ".word 0xe5d4343d, 0xe383300f, 0xe5c4343d, 0xe5d5100c\n"
        ".word 0xe3510000, 0x0a00000d, 0xe5842540, 0xe59437d8\n"
        ".word 0xe51f1be4, 0xe3833502, 0xe58437d8, 0xe5952000\n"
        ".word 0xe3822702, 0xe5852000, 0xe5942540, 0xe5913008\n"
        ".word 0xe1e01002, 0xe59f2288, 0xe7821003, 0xea000009\n"
        ".word 0xe5941540, 0xe1510002, 0x0a000006, 0xe5842540\n"
        ".word 0xe59427d8, 0xe3822502, 0xe58427d8, 0xe5951000\n"
        ".word 0xe3811702, 0xe5851000, 0xe5d4243e, 0xe382200f\n"
        ".word 0xe5c4243e, 0xe5d5100c, 0xe3510000, 0x0a00000d\n"
        ".word 0xe5840544, 0xe59427d8, 0xe3822401, 0xe58427d8\n"
        ".word 0xe5950000, 0xe3800702, 0xe5850000, 0xe51f0c70\n"
        ".word 0xe5941544, 0xe5900008, 0xe1e01001, 0xe2800a01\n"
        ".word 0xe580106c, 0xea000009, 0xe5941544, 0xe1510000\n"
        ".word 0x0a000006, 0xe5840544, 0xe59417d8, 0xe3811401\n"
        ".word 0xe58417d8, 0xe5950000, 0xe3800702, 0xe5850000\n"
        ".word 0xe59d0858, 0xe3100020, 0x0a000024, 0xe5941624\n"
        ".word 0xe3a00007, 0xe1d00001, 0x1a000014, 0xe5d40e74\n"
        ".word 0xe3500000, 0xe51f0cd8, 0x0a000007, 0xe5942630\n"
        ".word 0xe5901008, 0xe2840e7e, 0xe2811a01, 0xe5812158\n"
        ".word 0xe59417e0, 0xe3c11702, 0xea000007, 0xe5900008\n"
        ".word 0xe5941630, 0xe2800a01, 0xe1e01001, 0xe5801158\n"
        ".word 0xe59417e0, 0xe2840e7e, 0xe3811702, 0xe5801000\n"
        ".word 0xe5940590, 0xe3100001, 0x13a00000, 0x0a000007\n"
        ".word 0xe0601180, 0xe0841201, 0xe5d11a20, 0xe3510000\n"
        ".word 0x1a000002, 0xe2800001, 0xe3500008, 0xbafffff7\n"
        ".word 0xe59d0858, 0xe59fe13c, 0xe3100010, 0x0a000086\n"
        ".word 0xe59f0100, 0xe3a01000, 0xe5902000, 0xe35200bd\n"
        ".word 0x0a000034, 0xe2402088, 0xe51f6d90, 0xe5922008\n"
        ".word 0xe2849b01, 0xe3a03001, 0xe2899026, 0xe58d200c\n"
        ".word 0xe790c101, 0xe20c701f, 0xe1a022cc, 0xe0842102\n"
        ".word 0xe59227d8, 0xe1120713, 0x0a000022, 0xe59d200c\n"
        ".word 0xe084710c, 0xe2877b01, 0xe082210c, 0xe7dcc009\n"
        ".word 0xe2828a01, 0xe28770e4, 0xe35c0000, 0xe288800c\n"
        ".word 0x0a000011, 0xe597a000, 0xe5982000, 0xe15a0002\n"
        ".word 0x0a00000d, 0xe51f2df8, 0xe592b000, 0xe5962000\n"
        ".word 0xe15b0002, 0x9a000006, 0xe482a004, 0xe790a101\n"
        ".word 0xe282b004, 0xe79ea10a, 0xe18ac80c, 0xe582c000\n"
        ".word 0xe586b000, 0xe5972000, 0xe5882000, 0xe7902101\n"
        ".word 0xe202701f, 0xe1a0c2c2, 0xe084210c, 0xe592c7d8\n"
        ".word 0xe1ccc713, 0xe582c7d8, 0xe2811001, 0xe7902101\n"
        ".word 0xe35200bd, 0x1affffd1, 0xe59f0014, 0xe3a01000\n"
        ".word 0xea000011, 0x76543210, 0xfedcba98, 0x000080c2\n"
        ".word 0x000f0232, 0x0046531c, 0x00465334, 0x0046534c\n"
        ".word 0x004652bc, 0x0000100c, 0x000f0290, 0x00000291\n"
        ".word 0x000f02c0, 0x000002c1, 0x00000000, 0x33800001\n"
        ".word 0x37800080, 0x00001068, 0x004e4f54, 0xe5902000\n"
        ".word 0xe35200bd, 0x0a000034, 0xe2402070, 0xe51f6ec4\n"
        ".word 0xe5922008, 0xe2849b01, 0xe3a03001, 0xe2899026\n"
        ".word 0xe58d200c, 0xe790c101, 0xe20c701f, 0xe1a022cc\n"
        ".word 0xe0842102, 0xe59227d8, 0xe1120713, 0x0a000022\n"
        ".word 0xe59d200c, 0xe084710c, 0xe2877b01, 0xe082210c\n"
        ".word 0xe7dcc009, 0xe2828a01, 0xe28770e4, 0xe35c0000\n"
        ".word 0xe288800c, 0x0a000011, 0xe597a000, 0xe5982000\n"
        ".word 0xe15a0002, 0x0a00000d, 0xe51f2f2c, 0xe592b000\n"
        ".word 0xe5962000, 0xe15b0002, 0x9a000006, 0xe482a004\n"
        ".word 0xe790a101, 0xe282b004, 0xe79ea10a, 0xe18ac80c\n"
        ".word 0xe582c000, 0xe586b000, 0xe5972000, 0xe5882000\n"
        ".word 0xe7902101, 0xe202701f, 0xe1a0c2c2, 0xe084210c\n"
        ".word 0xe592c7d8, 0xe1ccc713, 0xe582c7d8, 0xe2811001\n"
        ".word 0xe7902101, 0xe35200bd, 0x1affffd1, 0xe59d0858\n"
        ".word 0xe3100002, 0x0a000039, 0xe51f0120, 0xe3a01000\n"
        ".word 0xe5902000, 0xe35200bd, 0x0a000034, 0xe2402010\n"
        ".word 0xe51f6fb8, 0xe5922008, 0xe2849b01, 0xe3a03001\n"
        ".word 0xe2899026, 0xe58d200c, 0xe790c101, 0xe20c701f\n"
        ".word 0xe1a022cc, 0xe0842102, 0xe59227d8, 0xe1120713\n"
        ".word 0x0a000022, 0xe59d200c, 0xe084710c, 0xe2877b01\n"
        ".word 0xe082210c, 0xe7dcc009, 0xe2828a01, 0xe28770e4\n"
        ".word 0xe35c0000, 0xe288800c, 0x0a000011, 0xe597a000\n"
        ".word 0xe5982000, 0xe15a0002, 0x0a00000d, 0xe59f2430\n"
        ".word 0xe592b000, 0xe5962000, 0xe15b0002, 0x9a000006\n"
        ".word 0xe482a004, 0xe790a101, 0xe282b004, 0xe79ea10a\n"
        ".word 0xe18ac80c, 0xe582c000, 0xe586b000, 0xe5972000\n"
        ".word 0xe5882000, 0xe7902101, 0xe1a0c2c2, 0xe202201f\n"
        ".word 0xe084c10c, 0xe59c77d8, 0xe1c72213, 0xe58c27d8\n"
        ".word 0xe2811001, 0xe7902101, 0xe35200bd, 0x1affffd1\n"
        ".word 0xe59d0858, 0xe3100020, 0x0a000039, 0xe51f0218\n"
        ".word 0xe3a01000, 0xe5902000, 0xe35200bd, 0x0a000034\n"
        ".word 0xe24020a0, 0xe59f63ac, 0xe5922008, 0xe2849b01\n"
        ".word 0xe3a03001, 0xe2899026, 0xe58d200c, 0xe790c101\n"
        ".word 0xe20c701f, 0xe1a022cc, 0xe0842102, 0xe59227d8\n"
        ".word 0xe1120713, 0x0a000022, 0xe59d200c, 0xe084710c\n"
        ".word 0xe2877b01, 0xe082210c, 0xe7dcc009, 0xe2828a01\n"
        ".word 0xe28770e4, 0xe35c0000, 0xe288800c, 0x0a000011\n"
        ".word 0xe597a000, 0xe5982000, 0xe15a0002, 0x0a00000d\n"
        ".word 0xe59f233c, 0xe592b000, 0xe5962000, 0xe15b0002\n"
        ".word 0x9a000006, 0xe482a004, 0xe790a101, 0xe282b004\n"
        ".word 0xe79ea10a, 0xe18ac80c, 0xe582c000, 0xe586b000\n"
        ".word 0xe5972000, 0xe5882000, 0xe7902101, 0xe202c01f\n"
        ".word 0xe1a072c2, 0xe0842107, 0xe59277d8, 0xe1c7cc13\n"
        ".word 0xe582c7d8, 0xe2811001, 0xe7902101, 0xe35200bd\n"
        ".word 0x1affffd1, 0xe59d0858, 0xe3100040, 0x0a000578\n"
        ".word 0xe5940590, 0xeddfaab4, 0xed9faab4, 0xe3100001\n"
        ".word 0x0a0001c9, 0xe59d0854, 0xe59f12c4, 0xe5900000\n"
        ".word 0xe1100001, 0x0a0001c4, 0xe59f92bc, 0xe59fa2bc\n"
        ".word 0xe59f82bc, 0xed9fbaab, 0xe3a07000, 0xe5940a0c\n"
        ".word 0xe1a00730, 0xe3100001, 0x0a00008f, 0xe59f02a4\n"
        ".word 0xe7901107, 0xe59407c0, 0xe1a00130, 0xe3100001\n"
        ".word 0x1a000089, 0xe0840107, 0xe59009f4, 0xe3700001\n"
        ".word 0x0a000088, 0xe0851100, 0xe591b074, 0xe35b0000\n"
        ".word 0x0a000084, 0xeb05d485, 0xe1b06000, 0xe320f000\n"
        ".word 0x0a000080, 0xe0850107, 0xe58d0000, 0xe590010c\n"
        ".word 0xe150000b, 0xe59d0000, 0xe5900190, 0x1a00001a\n"
        ".word 0xe3500000, 0x0a000074, 0xe59f1218, 0xe59f0210\n"
        ".word 0xe5912000, 0xe5900000, 0xe1520000, 0x2a000007\n"
        ".word 0xe59f0224, 0xe790c107, 0xe59d0000, 0xe5903214\n"
        ".word 0xe183340c, 0xe8820208, 0xe282c008, 0xe581c000\n"
        ".word 0xe59d0000, 0xe5962804, 0xe5b01190, 0xe5903084\n"
        ".word 0xe3a00f72, 0xe0822103, 0xeb05d4a9, 0xe59d1000\n"
        ".word 0xe3a00000, 0xe5810190, 0xea00005b, 0xe3500000\n"
        ".word 0x0a000002, 0xe59d1000, 0xe3a00000, 0xe5810190\n"
        ".word 0xe59d0000, 0xe580b10c, 0xe2860b02, 0xe280001c\n"
        ".word 0xe58d001c, 0xe596081c, 0xe3100001, 0x0a00003b\n"
        ".word 0xe5960804, 0xe3500000, 0x1a00000a, 0xe59f019c\n"
        ".word 0xe590c000, 0xe35c0000, 0x03a00000, 0x0a000004\n"
        ".word 0xe3a03b01, 0xe3a02000, 0xe3a01c01, 0xe3a00801\n"
        ".word 0xe12fff3c, 0xe5860804, 0xe3a01000, 0xe1a0c00a\n"
        ".word 0xe3a030ff, 0xe0862101, 0xed920a01, 0xee100a10\n"
        ".word 0xeeb40ae8, 0xeef1fa10, 0x9a000002, 0xe1a00080\n"
        ".word 0xe1530c20, 0x1a000052, 0xe3a00000, 0xe596b804\n"
        ".word 0xe2822b01, 0xe78b0101, 0xed920a01, 0xee102a10\n"
        ".word 0xeeb40a68, 0xeef1fa10, 0x11a02082, 0x11530c22\n"
        ".word 0x03a02000, 0x0a00000b, 0xee209a0a, 0xeeb49ae8\n"
        ".word 0xeef1fa10, 0x3eb19a49, 0x33a02b02, 0x23a02000\n"
        ".word 0xee19ba10, 0xe35b0445, 0xaeb09a4b, 0xeebc0ac9\n"
        ".word 0xee10ba10, 0xe182200b, 0xe1802602, 0xe5960804\n"
        ".word 0xe7802101, 0xe2811001, 0xe3510c01, 0xbaffffd8\n"
        ".word 0xe596081c, 0xe3c01001, 0xe59d001c, 0xe5801000\n"
        ".word 0xe59f2090, 0xe59f0088, 0xe5921000, 0xe5900000\n"
        ".word 0xe1510000, 0x2a000006, 0xe59f009c, 0xe7903107\n"
        ".word 0xe5819004, 0xe1a0c403, 0xe2813008, 0xe581c000\n"
        ".word 0xe5823000, 0xe5962804, 0xe3a01c01, 0xe3a00f72\n"
        ".word 0xeb05d44b, 0xe3a00001, 0xe58d0818, 0xe2877001\n"
        ".word 0xe3570006, 0xbaffff68, 0xe3a07000, 0xe0670187\n"
        ".word 0xe0848200, 0xe5d80a20, 0xe3500000, 0x0a00011f\n"
        ".word 0xe5940a0c, 0xe1b00c80, 0x5a000093, 0xe59407c0\n"
        ".word 0xe2871008, 0xe1a00130, 0xe3100001, 0x1a00008e\n"
        ".word 0xea000012, 0x004652a4, 0x004652a0, 0x45800000\n"
        ".word 0x45000000, 0x00004008, 0x44ffe000, 0x000f01c5\n"
        ".word 0x00000fff, 0x45800000, 0x0040b4e0, 0x0040b4f8\n"
        ".word 0x0044e330, 0xee200a2a, 0xee100a10, 0xe1580000\n"
        ".word 0xcebc0ac0, 0xd1a0000c, 0xce100a10, 0xeaffffa6\n"
        ".word 0xe5980a80, 0xe0851100, 0xe591a074, 0xeb05d3db\n"
        ".word 0xe0859107, 0xe1a06000, 0xe5990124, 0xe150000a\n"
        ".word 0xe59901a8, 0x1a000018, 0xe3500000, 0x0a00006e\n"
        ".word 0xe51f1080, 0xe51f0088, 0xe5912000, 0xe5900000\n"
        ".word 0xe1520000, 0x2a000007, 0xe599322c, 0xe1a0c407\n"
        ".word 0xe51fa08c, 0xe28cbb02, 0xe183300b, 0xe8820408\n"
        ".word 0xe282c008, 0xe581c000, 0xe599222c, 0xe5960804\n"
        ".word 0xe59911a8, 0xe0802102, 0xe3a00f72, 0xeb05d404\n"
        ".word 0xe3a00000, 0xe58901a8, 0xea000057, 0xe3500000\n"
        ".word 0x13a00000, 0x158901a8, 0xe589a124, 0xe596081c\n"
        ".word 0xe286ab02, 0xe28aa01c, 0xe3100001, 0x0a00003b\n"
        ".word 0xe5960804, 0xe3500000, 0x1a00000a, 0xe51f00e4\n"
        ".word 0xe590c000, 0xe35c0000, 0x03a00000, 0x0a000004\n"
        ".word 0xe3a03b01, 0xe3a02000, 0xe3a01c01, 0xe3a00801\n"
        ".word 0xe12fff3c, 0xe5860804, 0xe51f9120, 0xe51fc120\n"
        ".word 0xe3a01000, 0xe3a030ff, 0xe0862101, 0xed920a01\n"
        ".word 0xee100a10, 0xeeb40ae8, 0xeef1fa10, 0x9a000002\n"
        ".word 0xe1a00080, 0xe1530c20, 0x1a000039, 0xe3a00000\n"
        ".word 0xe596b804, 0xe2822b01, 0xe78b0101, 0xed920a01\n"
        ".word 0xee102a10, 0xeeb40a68, 0xeef1fa10, 0x11a02082\n"
        ".word 0x11530c22, 0x03a02000, 0x0a00000b, 0xee208a0a\n"
        ".word 0xeeb48ae8, 0xeef1fa10, 0x3eb18a48, 0x33a02b02\n"
        ".word 0x23a02000, 0xee18ba10, 0xe35b0445, 0xaeb08a4b\n"
        ".word 0xeebc0ac8, 0xee10ba10, 0xe182200b, 0xe1802602\n"
        ".word 0xe5960804, 0xe7802101, 0xe2811001, 0xe3510c01\n"
        ".word 0xbaffffd8, 0xe596081c, 0xe3c00001, 0xe58a0000\n"
        ".word 0xe51f21f0, 0xe51f01f8, 0xe5921000, 0xe5900000\n"
        ".word 0xe1510000, 0x2a000006, 0xe1a03407, 0xe283cb02\n"
        ".word 0xe51f31fc, 0xe2819008, 0xe5813004, 0xe581c000\n"
        ".word 0xe5829000, 0xe5962804, 0xe3a01c01, 0xe3a00f72\n"
        ".word 0xeb05d3ab, 0xe3a00001, 0xe58d0818, 0xe59407c0\n"
        ".word 0xe2871018, 0xe1a00130, 0xe3100001, 0x0a000007\n"
        ".word 0xea000082, 0xee200a2a, 0xee100a10, 0xe15c0000\n"
        ".word 0xcebc0ac0, 0xd1a00009, 0xce100a10, 0xeaffffbf\n"
        ".word 0xe5980a8c, 0xe0851100, 0xe5919074, 0xeb05d353\n"
        ".word 0xe0858107, 0xe1a06000, 0xe5980144, 0xe1500009\n"
        ".word 0xe59801c8, 0x1a000019, 0xe3500000, 0x0a00006f\n"
        ".word 0xe51f02a4, 0xe51f22a4, 0xe5901000, 0xe5920000\n"
        ".word 0xe1500001, 0x2a000008, 0xe598c24c, 0xe51f32a8\n"
        ".word 0xe1a09407, 0xe289aa01, 0xe18cc00a, 0xe5803004\n"
        ".word 0xe2809008, 0xe580c000, 0xe5829000, 0xe598224c\n"
        ".word 0xe5960804, 0xe59811c8, 0xe0802102, 0xe3a00f72\n"
        ".word 0xeb05d37b, 0xe3a00000, 0xe58801c8, 0xea000057\n"
        ".word 0xe3500000, 0x13a00000, 0x158801c8, 0xe5889144\n"
        ".word 0xe596081c, 0xe2869b02, 0xe289901c, 0xe3100001\n"
        ".word 0x0a00003b, 0xe5960804, 0xe3500000, 0x1a00000a\n"
        ".word 0xe51f0308, 0xe590c000, 0xe35c0000, 0x03a00000\n"
        ".word 0x0a000004, 0xe3a03b01, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xe12fff3c, 0xe5860804, 0xe51f8344\n"
        ".word 0xe51fc344, 0xe3a01000, 0xe3a030ff, 0xe0862101\n"
        ".word 0xed920a01, 0xee100a10, 0xeeb40ae8, 0xeef1fa10\n"
        ".word 0x9a000002, 0xe1a00080, 0xe1530c20, 0x1a000049\n"
        ".word 0xe3a00000, 0xe596a804, 0xe2822b01, 0xe78a0101\n"
        ".word 0xed920a01, 0xee102a10, 0xeeb40a68, 0xeef1fa10\n"
        ".word 0x11a02082, 0x11530c22, 0x03a02000, 0x0a00000b\n"
        ".word 0xee609a0a, 0xeef49ae8, 0xeef1fa10, 0x3ef19a69\n"
        ".word 0x33a02b02, 0x23a02000, 0xee19aa90, 0xe35a0445\n"
        ".word 0xaef09a4b, 0xeebc0ae9, 0xee10aa10, 0xe182200a\n"
        ".word 0xe1800602, 0xe5962804, 0xe7820101, 0xe2811001\n"
        ".word 0xe3510c01, 0xbaffffd8, 0xe596081c, 0xe3c00001\n"
        ".word 0xe5890000, 0xe51f0418, 0xe51f2418, 0xe5901000\n"
        ".word 0xe5920000, 0xe1500001, 0x2a000006, 0xe1a03407\n"
        ".word 0xe283ca01, 0xe51f3420, 0xe2808008, 0xe5803004\n"
        ".word 0xe580c000, 0xe5828000, 0xe5962804, 0xe3a01c01\n"
        ".word 0xe3a00f72, 0xeb05d322, 0xe3a00001, 0xe58d0818\n"
        ".word 0xe2877001, 0xe3570008, 0xbafffed7, 0xe5940e0c\n"
        ".word 0xed9f9aca, 0xe3500000, 0x0a000259, 0xe59d0854\n"
        ".word 0xe59f131c, 0xe5900000, 0xe1100001, 0x0a000254\n"
        ".word 0xe59f1310, 0xe28d2e82, 0xe51f847c, 0xe3a07000\n"
        ".word 0xe1c100d8, 0xe28dae82, 0xed9fbabf, 0xeddf9abf\n"
        ".word 0xe8820003, 0xea00000b, 0xee200a2a, 0xee100a10\n"
        ".word 0xe15c0000, 0xcebc0ac0, 0xd1a00008, 0xce100a10\n"
        ".word 0xeaffffaf, 0xe3570001, 0x1a000002, 0xe5940594\n"
        ".word 0xe3100901, 0x0a00008a, 0xe0840107, 0xe5900df0\n"
        ".word 0xe0851100, 0xe591b074, 0xeb05d2b4, 0xe0859107\n"
        ".word 0xe1a06000, 0xe5990164, 0xe150000b, 0xe59901e8\n"
        ".word 0x1a000018, 0xe3500000, 0x0a00007a, 0xe51f0520\n"
        ".word 0xe51f1520, 0xe5902000, 0xe5910000, 0xe1500002\n"
        ".word 0x2a000007, 0xe79ab107, 0xe599c26c, 0xe59f3270\n"
        ".word 0xe18cc40b, 0xe5803004, 0xe280b008, 0xe580c000\n"
        ".word 0xe581b000, 0xe599026c, 0xe5962810, 0xe59911e8\n"
        ".word 0xe0822100, 0xe3a000b0, 0xeb05d2dd, 0xe3a00000\n"
        ".word 0xe58901e8, 0xea000063, 0xe3500000, 0x13a00000\n"
        ".word 0x158901e8, 0xe589b164, 0xe596081c, 0xe2869b02\n"
        ".word 0xe289901c, 0xe3100008, 0x0a000047, 0xe5960810\n"
        ".word 0xe3500000, 0x1a00000a, 0xe51f0580, 0xe590c000\n"
        ".word 0xe35c0000, 0x03a00000, 0x0a000004, 0xe3a03c02\n"
        ".word 0xe3a02000, 0xe3a01c01, 0xe3a00801, 0xe12fff3c\n"
        ".word 0xe5860810, 0xe51fc5bc, 0xe3a01000, 0xe3a030ff\n"
        ".word 0xe0862101, 0xed920a01, 0xee100a10, 0xeeb40ae8\n"
        ".word 0xeef1fa10, 0x9a000002, 0xe1a00080, 0xe1530c20\n"
        ".word 0x1a00001a, 0xe3a00000, 0xe596b810, 0xe78b0101\n"
        ".word 0xed920a81, 0xee102a10, 0xeeb40a68, 0xeef1fa10\n"
        ".word 0x11a02082, 0x11530c22, 0x03a02000, 0x0a000019\n"
        ".word 0xee300a29, 0xee208a0a, 0xeef48ac8, 0xeef1fa10\n"
        ".word 0xceb08a68, 0xca000010, 0xee182a10, 0xe1520008\n"
        ".word 0xbe182a10, 0xaeb08a4b, 0xb3520445, 0xba00000a\n"
        ".word 0xee380a4a, 0xeebc0ac0, 0xee102a10, 0xea000009\n"
        ".word 0xee200a2a, 0xee100a10, 0xe1580000, 0xcebc0ac0\n"
        ".word 0xd1a0000c, 0xce100a10, 0xeaffffde, 0xee380a0a\n"
        ".word 0xeebc0ac0, 0xee102a10, 0xe1802602, 0xe5960810\n"
        ".word 0xe7802101, 0xe2811001, 0xe3510080, 0xbaffffcb\n"
        ".word 0xe596081c, 0xe3c00008, 0xe5890000, 0xe51f06c0\n"
        ".word 0xe51f26c0, 0xe5901000, 0xe5920000, 0xe1500001\n"
        ".word 0x2a000006, 0xe79ac107, 0xe59f30d4, 0xe1a0940c\n"
        ".word 0xe5803004, 0xe280c008, 0xe5809000, 0xe582c000\n"
        ".word 0xe5962810, 0xe3a01080, 0xe3a000b0, 0xeb05d278\n"
        ".word 0xe3a00001, 0xe58d0818, 0xe2877001, 0xe3570002\n"
        ".word 0xbaffff6f, 0xe5940594, 0xe3100902, 0x0a000088\n"
        ".word 0xe5940df8, 0xe0851100, 0xe5917074, 0xeb05d227\n"
        ".word 0xe1a06000, 0xe595016c, 0xe1500007, 0xe59501f0\n"
        ".word 0x1a00001c, 0xe3500000, 0x0a00007d, 0xe51f0750\n"
        ".word 0xe51f2750, 0xe5901000, 0xe5920000, 0xe1500001\n"
        ".word 0x2a000005, 0xe59f3048, 0xe595c274, 0xe2807008\n"
        ".word 0xe5803004, 0xe580c000, 0xe5827000, 0xe5952274\n"
        ".word 0xe5960814, 0xe59511f0, 0xe0802102, 0xe3a000b0\n"
        ".word 0xeb05d253, 0xe3a00000, 0xe58501f0, 0xea000068\n"
        ".word 0x437f0000, 0x00004020, 0x00409bf0, 0x457ff000\n"
        ".word 0x3f800000, 0x000f00af, 0xe3500000, 0x13a00000\n"
        ".word 0x158501f0, 0xe585716c, 0xe596081c, 0xe2867b02\n"
        ".word 0xe287701c, 0xe3100010, 0x0a000047, 0xe5960814\n"
        ".word 0xe3500000, 0x1a00000a, 0xe51f07c0, 0xe590c000\n"
        ".word 0xe35c0000, 0x03a00000, 0x0a000004, 0xe3a03c02\n"
        ".word 0xe3a02000, 0xe3a01c01, 0xe3a00801, 0xe12fff3c\n"
        ".word 0xe5860814, 0xe51fc7fc, 0xe3a01000, 0xe3a020ff\n"
        ".word 0xe0863101, 0xed930a01, 0xee100a10, 0xeeb40ae8\n"
        ".word 0xeef1fa10, 0x9a000002, 0xe1a00080, 0xe1520c20\n"
        ".word 0x1a00001a, 0xe3a00000, 0xe5969814, 0xe7890101\n"
        ".word 0xed930a81, 0xee103a10, 0xeeb40a68, 0xeef1fa10\n"
        ".word 0x11a03083, 0x11520c23, 0x03a03000, 0x0a000019\n"
        ".word 0xee300a29, 0xee200a0a, 0xeef48ac0, 0xeef1fa10\n"
        ".word 0xceb00a68, 0xca000010, 0xee103a10, 0xe1530008\n"
        ".word 0xbe103a10, 0xaeb00a4b, 0xb3530445, 0xba00000a\n"
        ".word 0xee300a4a, 0xeebc0ac0, 0xee103a10, 0xea000009\n"
        ".word 0xee200a2a, 0xee100a10, 0xe1580000, 0xcebc0ac0\n"
        ".word 0xd1a0000c, 0xce100a10, 0xeaffffde, 0xee300a0a\n"
        ".word 0xeebc0ac0, 0xee103a10, 0xe1803603, 0xe5960814\n"
        ".word 0xe7803101, 0xe2811001, 0xe3510080, 0xbaffffcb\n"
        ".word 0xe596081c, 0xe3c00010, 0xe5870000, 0xe51f0900\n"
        ".word 0xe51f3900, 0xe5901000, 0xe5930000, 0xe1500001\n"
        ".word 0x2a000005, 0xe51f2168, 0xe3a0c000, 0xe2807008\n"
        ".word 0xe5802004, 0xe580c000, 0xe5837000, 0xe5962814\n"
        ".word 0xe3a01080, 0xe3a000b0, 0xeb05d1e9, 0xe3a00001\n"
        ".word 0xe58d0818, 0xe3a00000, 0xe0841100, 0xe0852100\n"
        ".word 0xe5911dfc, 0xe5922170, 0xe0851101, 0xe5911074\n"
        ".word 0xe1510002, 0x1a000002, 0xe2800001, 0xe3500004\n"
        ".word 0xbafffff4, 0xe3500004, 0xe28d9008, 0x0a000016\n"
        ".word 0xe59f8330, 0xe3a07000, 0xeddfbac8, 0xed9fbac8\n"
        ".word 0xe3a0b0ff, 0xe1a09007, 0xe0840107, 0xe5900dfc\n"
        ".word 0xeb05d18a, 0xe1a06000, 0xe0850107, 0xe286ab02\n"
        ".word 0xe59011f4, 0xe28aa01c, 0xe3510000, 0x158091f4\n"
        ".word 0xe596081c, 0xe3100020, 0x0a0000c9, 0xe5960818\n"
        ".word 0xe3500000, 0x0a00007a, 0xea000084, 0xe59501f4\n"
        ".word 0xe3500000, 0x059501f8, 0x03500000, 0x1a000004\n"
        ".word 0xe59501fc, 0xe3500000, 0x05950200, 0x03500000\n"
        ".word 0x0a0000f7, 0xe3a08000, 0xe3a07c02, 0xe1a00008\n"
        ".word 0xe1a0c008, 0xe0851100, 0xe59121f4, 0xe3520000\n"
        ".word 0x0a000007, 0xe5913278, 0xe581c1f4, 0xe1530007\n"
        ".word 0x31a07003, 0xe0822003, 0xe2423001, 0xe1530008\n"
        ".word 0x81a08003, 0xe2800001, 0xe3500004, 0xbafffff0\n"
        ".word 0xe3a0a000, 0xe3a0b0ff, 0xe084010a, 0xe5900dfc\n"
        ".word 0xeb05d15a, 0xe1570008, 0x91a0118a, 0xe1a06007\n"
        ".word 0x91a0211b, 0x8a000008, 0xe590c818, 0xe7993106\n"
        ".word 0xe7dcc006, 0xe1c33002, 0xe183311c, 0xe7893106\n"
        ".word 0xe2866001, 0xe1560008, 0x9afffff6, 0xe28aa001\n"
        ".word 0xe35a0004, 0xbaffffeb, 0xe3570c01, 0x2a00002f\n"
        ".word 0xe3580c01, 0x3a000020, 0xe51f6ab8, 0xe51faac0\n"
        ".word 0xe5960000, 0xe59a1000, 0xe1500001, 0x2a000005\n"
        ".word 0xe51f2324, 0xe387cb01, 0xe2803008, 0xe5802004\n"
        ".word 0xe580c000, 0xe5863000, 0xe2671c01, 0xe0892107\n"
        ".word 0xe3a000b0, 0xeb05d17a, 0xe59a1000, 0xe5960000\n"
        ".word 0xe1500001, 0x2a000005, 0xe51f235c, 0xe3a03c05\n"
        ".word 0xe280c008, 0xe5802004, 0xe5803000, 0xe586c000\n"
        ".word 0xe2892b01, 0xe24810ff, 0xe3a000b0, 0xeb05d16c\n"
        ".word 0xe320f000, 0xe320f000, 0xea0000a9, 0xe51f1b3c\n"
        ".word 0xe51f0b44, 0xe5912000, 0xe5900000, 0xe1520000\n"
        ".word 0x2a000013, 0xe51f33a8, 0xe3876b01, 0xe282c008\n"
        ".word 0xe5823004, 0xe5826000, 0xe581c000, 0xea00000c\n"
        ".word 0xe51f2b70, 0xe51f0b78, 0xe5921000, 0xe5900000\n"
        ".word 0xe1500001, 0x9a000006, 0xe2473c01, 0xe383cc05\n"
        ".word 0xe51f33e4, 0xe2816008, 0xe5813004, 0xe581c000\n"
        ".word 0xe5826000, 0xe0480007, 0xe2801001, 0xe0892107\n"
        ".word 0xe3a000b0, 0xeb05d14a, 0xe320f000, 0xe320f000\n"
        ".word 0xea000087, 0xe51f0b9c, 0xe590c000, 0xe35c0000\n"
        ".word 0x03a00000, 0x0a000004, 0xe3a03c02, 0xe3a02000\n"
        ".word 0xe3a01c01, 0xe3a00801, 0xe12fff3c, 0xe5860818\n"
        ".word 0xeef00a49, 0xe3a01000, 0xeeb01a6b, 0xe0860101\n"
        ".word 0xe5962818, 0xed900a01, 0xee100a10, 0xe35005fe\n"
        ".word 0xceb00a69, 0xee001a20, 0xeebc0ac1, 0xee100a10\n"
        ".word 0xe7c20001, 0xe2811001, 0xe3510c01, 0xbafffff1\n"
        ".word 0xe1510008, 0xbeb08a68, 0xb59f007c, 0xaa000027\n"
        ".word 0xe0862101, 0xed920a01, 0xee102a10, 0xeeb40a48\n"
        ".word 0xeef1fa10, 0x11a02082, 0x115b0c22, 0x05962818\n"
        ".word 0x07c29001, 0x0a00001a, 0xee300a29, 0xee200a0b\n"
        ".word 0xeeb48ac0, 0xeef1fa10, 0xceb00a48, 0xca00000f\n"
        ".word 0xee102a10, 0xe1520000, 0xbe102a10, 0xaeb00a60\n"
        ".word 0xb3520443, 0xba000009, 0xe5963818, 0xee300a4b\n"
        ".word 0xeebc0ac0, 0xee102a10, 0xe7c32001, 0xea000008\n"
        ".word 0x3f000000, 0x43000000, 0x000001ff, 0x43800000\n"
        ".word 0xee300a0b, 0xe5963818, 0xeebc0ac0, 0xee102a10\n"
        ".word 0xe7c32001, 0xe2811001, 0xe1510008, 0xbaffffd7\n"
        ".word 0xe5960818, 0xe7c09001, 0xe596081c, 0xe3c00020\n"
        ".word 0xe58a0000, 0xe1a03187, 0xe3a00000, 0xe1a0231b\n"
        ".word 0xe28d1008, 0xe596a818, 0xe791c100, 0xe7daa000\n"
        ".word 0xe1ccc002, 0xe18cc31a, 0xe781c100, 0xe2800001\n"
        ".word 0xe3500c02, 0xbafffff6, 0xe2877001, 0xe3570004\n"
        ".word 0xbaffff18, 0xe3570004, 0x1a000029, 0xe51f6d3c\n"
        ".word 0xe51f8d44, 0xe5960000, 0xe5981000, 0xe1500001\n"
        ".word 0x2a000005, 0xe51f25a8, 0xe3a03b01, 0xe280c008\n"
        ".word 0xe5802004, 0xe5803000, 0xe586c000, 0xe28d7008\n"
        ".word 0xe1a02007, 0xe3a01c01, 0xe3a000b0, 0xeb05d0d8\n"
        ".word 0xe5980000, 0xe5961000, 0xe1510000, 0x2a000004\n"
        ".word 0xe51f35e4, 0xe3a02c05, 0xe281c008, 0xe1c120f0\n"
        ".word 0xe586c000, 0xe2872b01, 0xe3a01c01, 0xe3a000b0\n"
        ".word 0xeb05d0cb, 0xe3a00001, 0xe58d0818, 0xe3a00000\n"
        ".word 0xe0841100, 0xe0852100, 0xe5911dfc, 0xe2800001\n"
        ".word 0xe3500004, 0xe0851101, 0xe5911074, 0xe5821170\n"
        ".word 0xbafffff6, 0xe5940624, 0xe3100007, 0x0a000086\n"
        ".word 0xe59d0854, 0xe59f1440, 0xe5900000, 0xe1100001\n"
        ".word 0x0a000081, 0xe5940e64, 0xe0851100, 0xe5917074\n"
        ".word 0xeb05d06e, 0xe1a06000, 0xe5950180, 0xe59f841c\n"
        ".word 0xe1500007, 0xe5950204, 0x1a000014, 0xe3500000\n"
        ".word 0x0a000075, 0xe51f2e34, 0xe51f0e3c, 0xe5921000\n"
        ".word 0xe5900000, 0xe1510000, 0x2a000003, 0xe5953288\n"
        ".word 0xe281c008, 0xe8810108, 0xe582c000, 0xe5950288\n"
        ".word 0xe5962808, 0xe5951204, 0xe0822100, 0xe3a000e8\n"
        ".word 0xeb05d09b, 0xe3a00000, 0xe5850204, 0xea000062\n"
        ".word 0xe3500000, 0x13a00000, 0x15850204, 0xe5857180\n"
        ".word 0xe596081c, 0xe2867b02, 0xe287701c, 0xe3100002\n"
        ".word 0x0a000049, 0xe5960808, 0xe3500000, 0x1a00000a\n"
        ".word 0xe51f0e88, 0xe590c000, 0xe35c0000, 0x03a00000\n"
        ".word 0x0a000004, 0xe3a03c02, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xe12fff3c, 0xe5860808, 0xe51f9ec0\n"
        ".word 0xe59fc364, 0xe3a01000, 0xed9f1ad5, 0xeddf1ad5\n"
        ".word 0xe3a020ff, 0xe1a03001, 0xe0860101, 0xed900a81\n"
        ".word 0xee10aa10, 0xeeb40a68, 0xeef1fa10, 0x11a0a08a\n"
        ".word 0x11520c2a, 0x0596a808, 0x078a3101, 0x0a000016\n"
        ".word 0xee300a01, 0xee600a0a, 0xeef48ae0, 0xeef1fa10\n"
        ".word 0xcef00a68, 0xca00000b, 0xee10aa90, 0xe35a0446\n"
        ".word 0xbe10aa90, 0xaef00a61, 0xb15a0009, 0xba000005\n"
        ".word 0xe596b808, 0xee300aea, 0xeebc0ac0, 0xee10aa10\n"
        ".word 0xe78ba101, 0xea000004, 0xee300aaa, 0xe596b808\n"
        ".word 0xeebc0ac0, 0xee10aa10, 0xe78ba101, 0xed900a01\n"
        ".word 0xee100a10, 0xeeb40ae8, 0xeef1fa10, 0x9a000002\n"
        ".word 0xe1a00080, 0xe1520c20, 0x1a000020, 0xe3a00000\n"
        ".word 0xe1a0a000, 0xe5960808, 0xe790b101, 0xe18ba68a\n"
        ".word 0xe780a101, 0xe2811001, 0xe3510080, 0xbaffffcd\n"
        ".word 0xe596081c, 0xe3c00002, 0xe5870000, 0xe51f0fd0\n"
        ".word 0xe51f2fd0, 0xe5901000, 0xe5920000, 0xe1500001\n"
        ".word 0x2a000003, 0xe3a03000, 0xe8800108, 0xe280c008\n"
        ".word 0xe582c000, 0xe5962808, 0xe3a01080, 0xe3a000e8\n"
        ".word 0xeb05d037, 0xe3a00001, 0xe58d0818, 0xe5941624\n"
        ".word 0xe3a00007, 0xe1d00001, 0x1a0000bd, 0xea000006\n"
        ".word 0xee200a0a, 0xee100a10, 0xe3500445, 0xbebc0ac0\n"
        ".word 0xa1a0000c, 0xbe100a10, 0xeaffffd8, 0xe59d0854\n"
        ".word 0xe59f1208, 0xe5900000, 0xe1100001, 0x13a00000\n"
        ".word 0x0a0000af, 0xe0842100, 0xe0851100, 0xe5922e78\n"
        ".word 0xe5913184, 0xe0852102, 0xe5921074, 0xe1510003\n"
        ".word 0x1a000002, 0xe2800001, 0xe3500003, 0xbafffff4\n"
        ".word 0xe3500003, 0x0a0000a2, 0xe3a08000, 0xeeb08a68\n"
        ".word 0xe58d8010, 0xe58d8014, 0xe58d8018, 0xe58d801c\n"
        ".word 0xe58d8020, 0xe58d8024, 0xeddf9a69, 0xe58d8028\n"
        ".word 0xe58d802c, 0xe58d8030, 0xe58d8034, 0xe58d8038\n"
        ".word 0xe3a09020, 0xe58d803c, 0xe58d8040, 0xe58d8044\n"
        ".word 0xe58d8048, 0xe58d804c, 0xe0840108, 0xe5900e78\n"
        ".word 0xeb05cfba, 0xe1a06000, 0xe280ab02, 0xe590081c\n"
        ".word 0xe28aa01c, 0xe3100004, 0x0a000035, 0xe596080c\n"
        ".word 0xe2867b02, 0xe287700c, 0xe3500000, 0x1a00000a\n"
        ".word 0xe59f0140, 0xe590c000, 0xe35c0000, 0x03a00000\n"
        ".word 0x0a000004, 0xe3a03040, 0xe3a02000, 0xe3a01c01\n"
        ".word 0xe3a00801, 0xe12fff3c, 0xe586080c, 0xe51fe488\n"
        ".word 0xe3a00000, 0xe3a020ff, 0xe0861100, 0xed910a01\n"
        ".word 0xee200a09, 0xee103a10, 0xeeb40ac8, 0xeef1fa10\n"
        ".word 0x9a000002, 0xe1a03083, 0xe1520c23, 0x1a00003a\n"
        ".word 0xe3a03000, 0xe596c80c, 0xe78c3100, 0xed910a09\n"
        ".word 0xe597b000, 0xe089c100, 0xee200a29, 0xeeb00ac0\n"
        ".word 0xeebc0ac0, 0xee103a10, 0xe203307f, 0xe78b300c\n"
        ".word 0xed910a09, 0xeeb40ac8, 0xeef1fa10, 0x2a000002\n"
        ".word 0xe596180c, 0xe3833080, 0xe781300c, 0xe2800001\n"
        ".word 0xe3500008, 0xbaffffdf, 0xe596081c, 0xe3c00004\n"
        ".word 0xe58a0000, 0xe2863b02, 0xe3a00000, 0xe28d1010\n"
        ".word 0xe1a02188, 0xe283300c, 0xe596c80c, 0xe0897100\n"
        ".word 0xe791a100, 0xe79c7007, 0xe081c100, 0xe18a7217\n"
        ".word 0xe7817100, 0xe5937000, 0xe59ca020, 0xe7977100\n"
        ".word 0xe2800001, 0xe3500008, 0xe18a7217, 0xe58c7020\n"
        ".word 0xbafffff0, 0xe2888001, 0xe3580003, 0xbaffffa9\n"
        ".word 0xe3580003, 0x1a000036, 0xea00000d, 0x00004010\n"
        ".word 0x000f00e6, 0x40000000, 0x45fff800, 0x000007ff\n"
        ".word 0x02004000, 0x42fe0000, 0x0044e330, 0xee103a10\n"
        ".word 0xe15e0003, 0xcebc0ac0, 0xd3a030ff, 0xce103a10\n"
        ".word 0xeaffffbf, 0xe59d0818, 0xe3500000, 0x1a000002\n"
        ".word 0xe3a0102d, 0xe3a000c0, 0xeb05cffa, 0xe59f63c0\n"
        ".word 0xe59f73c0, 0xe5961000, 0xe5970000, 0xe1510000\n"
        ".word 0x2a000004, 0xe59f33b0, 0xe3a02000, 0xe281c008\n"
        ".word 0xe1c120f0, 0xe586c000, 0xe28d2010, 0xe3a01010\n"
        ".word 0xe3a00f49, 0xeb05cf86, 0xe5970000, 0xe5961000\n"
        ".word 0xe1510000, 0x2a000004, 0xe3a02000, 0xe3a0cc01\n"
        ".word 0xe8811004, 0xe2813008, 0xe5863000, 0xe3a00000\n"
        ".word 0xe0841100, 0xe0852100, 0xe5911e78, 0xe2800001\n"
        ".word 0xe3500003, 0xe0851101, 0xe5911074, 0xe5821184\n"
        ".word 0xbafffff6, 0xe59d0858, 0xe3100b02, 0x0a00004f\n"
        ".word 0xe59d0854, 0xe5900000, 0xe3100c01, 0x1a000003\n"
        ".word 0xe5940e38, 0xe5951644, 0xe1500001, 0x0a000047\n"
        ".word 0xe5d50656, 0xe5941e38, 0xe5d52654, 0xe5d54655\n"
        ".word 0xe5d53657, 0xe59fc2f8, 0xe59f62f8, 0xe5851644\n"
        ".word 0xe1a00100, 0xe59c1000, 0xe5967000, 0xe1822084\n"
        ".word 0xe1800183, 0xe1510007, 0xe1800002, 0x2a000004\n"
        ".word 0xe59f42d8, 0xe3a03001, 0xe2817008, 0xe8810018\n"
        ".word 0xe58c7000, 0xe59c2000, 0xe5961000, 0xe1520001\n"
        ".word 0x2a000004, 0xe59f42b8, 0xe3a03001, 0xe2827008\n"
        ".word 0xe8820018, 0xe58c7000, 0xe59f32a8, 0xe5951644\n"
        ".word 0xe2832002, 0xe2411a06, 0xe2511030, 0xe1837943\n"
        ".word 0xe18249c2, 0x0a000026, 0xe3510018, 0x0a000079\n"
        ".word 0xe3510021, 0x1a00001d, 0xe59c1000, 0xe5960000\n"
        ".word 0xe1510000, 0x2a000003, 0xe3a0500f, 0xe88100a0\n"
        ".word 0xe2818008, 0xe58c8000, 0xe59c0000, 0xe5961000\n"
        ".word 0xe1500001, 0x2a000004, 0xe3a0500f, 0xe5803004\n"
        ".word 0xe2807008, 0xe5805000, 0xe58c7000, 0xe59c1000\n"
        ".word 0xe5960000, 0xe1510000, 0x2a000004, 0xe3a03003\n"
        ".word 0xe5812004, 0xe2815008, 0xe5813000, 0xe58c5000\n"
        ".word 0xe5961000, 0xe59c0000, 0xe1500001, 0x3a000077\n"
        ".word 0xe28ddb02, 0xe28dd034, 0xecbd8b08, 0xe28dd008\n"
        ".word 0xe8bd8ff0, 0xe3500000, 0x03a01000, 0x0a00000b\n"
        ".word 0xe5951688, 0xe3510001, 0x0a000006, 0xe5d5164c\n"
        ".word 0xe3510000, 0x1a000003, 0xe350000f, 0x05d5064d\n"
        ".word 0x03500000, 0x0a000000, 0xe3a00001, 0xe3a01002\n"
        ".word 0xe5d5864b, 0xe1800001, 0xe3580000, 0x13a01004\n"
        ".word 0x03a01000, 0xe1800001, 0x15d51658, 0xe5d5864a\n"
        ".word 0x13510000, 0x03a01000, 0x13a01008, 0xe3580000\n"
        ".word 0xe1800001, 0x13a01010, 0x03a01000, 0xe1800001\n"
        ".word 0x1595165c, 0xe59c5000, 0x13510000, 0x03a01000\n"
        ".word 0x13a01020, 0xe1800001, 0xe5961000, 0xe1550001\n"
        ".word 0x2a000006, 0xe3100001, 0x13a0800f, 0x03a08000\n"
        ".word 0xe5853004, 0xe2859008, 0xe5858000, 0xe58c9000\n"
        ".word 0xe59c3000, 0xe5961000, 0xe1530001, 0x2a000005\n"
        ".word 0xe3100002, 0x13a0500f, 0x03a05000, 0xe88300a0\n"
        ".word 0xe2838008, 0xe58c8000, 0xe59c3000, 0xe5961000\n"
        ".word 0xe1530001, 0x2a00000c, 0xe3100004, 0x1310000a\n"
        ".word 0x03a05000, 0x13a05002, 0xe3100010, 0x13100022\n"
        ".word 0x03a07000, 0x13a07001, 0xe1855007, 0xe5832004\n"
        ".word 0xe2837008, 0xe5835000, 0xe58c7000, 0xe5962000\n"
        ".word 0xe59c1000, 0xe1510002, 0x2affffac, 0xe2102008\n"
        ".word 0xe2003020, 0x13a02002, 0xe18222a3, 0xe2813008\n"
        ".word 0xe8810014, 0xea000020, 0xe59c0000, 0xe5961000\n"
        ".word 0xe1500001, 0x2a000003, 0xe3a0500f, 0xe88000a0\n"
        ".word 0xe2808008, 0xe58c8000, 0xe59c1000, 0xe5960000\n"
        ".word 0xe1510000, 0x2a000004, 0xe3a0500f, 0xe5813004\n"
        ".word 0xe2817008, 0xe5815000, 0xe58c7000, 0xe59c1000\n"
        ".word 0xe5960000, 0xe1510000, 0x2a000004, 0xe3a03000\n"
        ".word 0xe5812004, 0xe2815008, 0xe5813000, 0xe58c5000\n"
        ".word 0xe5961000, 0xe59c0000, 0xe1500001, 0x2affff87\n"
        ".word 0xe3a02000, 0xe8800014, 0xe2803008, 0xe58c3000\n"
        ".word 0xeaffff82, 0x004652a0, 0x004652a4, 0x000f0123\n"
        ".word 0x000f0111, 0x000f0110, 0x000f0112\n");
}

} // namespace smt4::engine
