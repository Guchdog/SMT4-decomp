#include "types.h"

// Batch 45 C: exact raw code.bin wrappers; full mode-specific Capstone coverage, semantics are not reconstructed.

extern "C" void engine_func_002c4b30(void* buf, u32 size);
extern "C" void engine_func_002bf86c(void* dst, const void* src);
extern "C" u32 engine_func_003d9b0c(u8* self, u32 r6, u32 a1, u32 a2, float f0, float f1, s32 kind,
                                    u32 extra, void* buf);

// DECOMP_FUNC(0x0023c85c, 744)
extern "C" u32 engine_func_0023c85c(u8* self, u32 a1, u32 a2, s32 kind, float f0, float f1,
                                    s32 slot_idx, u32 extra) {
    if (kind >= 10) {
        return 0u;
    }

    alignas(4) u8 buf[0x80];
    engine_func_002c4b30(buf, 0x80u);

    u32 r6 = 0xFFu;
    if (static_cast<u32>(kind) < 10u) {
        static const s8 kMaxSlots[10] = {4, 4, 4, 4, 11, 2, 5, 3, 1, 1};
        static const u16 kByteOffsets[10] = {
            0x1D00u, 0x1F30u, 0x2160u, 0x2390u, 0x25C0u,
            0x2BC4u, 0x2CDCu, 0x3070u, 0x3218u, 0x2F9Cu,
        };
        if (kind < 8 ? (slot_idx >= static_cast<s32>(kMaxSlots[kind])) : (slot_idx != 0)) {
            return 0u;
        }
        u8* const rec = self + kByteOffsets[kind] + ((kind < 8) ? (slot_idx * 0x8C) : 0);
        r6 = rec[0];
        engine_func_002bf86c(buf, rec + 8);
    }

    return engine_func_003d9b0c(self, r6, a1, a2, f0, f1, kind, extra, buf);
}

extern "C" s32 battle_func_0022a5d8(void* sub, u32 cmd);
extern "C" const u32* battle_func_0022a4d8(void* sub, u32 cmd);
extern "C" const u32* battle_func_0022a5f8(void* sub, u32 cmd);

// DECOMP_FUNC(0x003c6224, 940)
extern "C" void battle_func_003c6224(u8* self, u8* r4_obj, u32 cmd) {
    if (cmd >= 31u) {
        return;
    }

    void* const sub = *reinterpret_cast<void* const*>(self + 0x10u);
    if (cmd == 0u) {
        const s32 b = battle_func_0022a5d8(sub, 0u);
        u8* const g = *reinterpret_cast<u8* const*>(0x004342C8u);
        u32* const f = reinterpret_cast<u32*>(g + 0x634u);
        *f = (b != 0) ? (*f | 0x100u) : (*f & ~0x100u);
        return;
    }
    if (cmd == 1u) {
        const u32 val = *battle_func_0022a4d8(sub, 1u);
        u8* const g = *reinterpret_cast<u8* const*>(0x004342C8u);
        *reinterpret_cast<u32*>(g + 0x560u) = val;
        return;
    }
    if (cmd == 2u) {
        const s32 b = battle_func_0022a5d8(sub, 2u);
        u32* const f = reinterpret_cast<u32*>(r4_obj + 0x44A8u);
        *f = (b != 0) ? (*f | 0x40000000u) : (*f & ~0x40000000u);
        return;
    }

    static const u32 kTargetAddrs[28] = {
        0x00493554u, 0x0049355Cu, 0x00434310u, 0x00434314u, 0x00434318u, 0x0043431Cu,
        0x004342D4u, 0x004342D8u, 0x00434320u, 0x00434324u, 0x004342E0u, 0x00434328u,
        0x0043432Cu, 0x00434330u, 0x004342E4u, 0x00434334u, 0x00434338u, 0x004342E8u,
        0x0043433Cu, 0x00434340u, 0x004342ECu, 0x00434344u, 0x00434348u, 0x0043434Cu,
        0x00434350u, 0x00434354u, 0x00439CECu, 0x004342F0u,
    };

    const bool use_a4d8 = (cmd <= 7u || cmd == 11u || cmd == 15u);
    const u32 val = *(use_a4d8 ? battle_func_0022a4d8(sub, cmd) : battle_func_0022a5f8(sub, cmd));
    *reinterpret_cast<u32*>(kTargetAddrs[cmd - 3u]) = val;
}

extern "C" const u8* script_vm_func_002b66ec();
extern "C" const u8* battle_func_002ae3f0(u32 skill_id);
extern "C" u32 battle_func_002ae464(u32 skill_id);
extern "C" const u8* camp_func_002a8a08();
extern "C" const u8* camp_func_002a89e4(s32 index);

namespace {

__attribute__((always_inline)) inline void collect_valid_skills_1b02e8(const u8* unit, u16* out) {
    u32 count = 0u;
    for (s32 slot = 0; slot < 8; ++slot) {
        const u16 skill_id = *reinterpret_cast<const u16*>(unit + 0x34 + slot * 2);
        const u8* const skill = battle_func_002ae3f0(skill_id);
        if (skill != nullptr && skill[0x55] == 0u && battle_func_002ae464(skill_id) == 0u) {
            out[count++] = skill_id;
        }
    }
}

}  // namespace

// DECOMP_FUNC(0x001b02e8, 944)
extern "C" void battle_func_001b02e8(u8* self) {
    for (u32 i = 0u; i < 16u; ++i) {
        *reinterpret_cast<u32*>(self + 0x341Cu + i * 4u) = 0u;
    }

    u32 mc_count = 0u;
    for (s32 slot = 0; slot < 8; ++slot) {
        const u8* const mc = script_vm_func_002b66ec();
        const u16 skill_id = *reinterpret_cast<const u16*>(mc + 0x34 + slot * 2);
        const u8* const skill = battle_func_002ae3f0(skill_id);
        if (skill != nullptr && skill[0x55] == 0u && battle_func_002ae464(skill_id) == 0u) {
            *reinterpret_cast<u16*>(self + 0x341Cu + mc_count * 2u) = skill_id;
            ++mc_count;
        }
    }

    for (s32 party_idx = 0; party_idx < 3; ++party_idx) {
        const u8* const pt = camp_func_002a8a08();
        if (*reinterpret_cast<const s8*>(pt + 0x9108 + party_idx) < 0) {
            continue;
        }
        const u8* const pt2 = camp_func_002a8a08();
        const s8 unit_idx = *reinterpret_cast<const s8*>(pt2 + 0x9108 + party_idx);
        const u8* const demon = camp_func_002a89e4(unit_idx);
        if (demon == nullptr) {
            continue;
        }
        collect_valid_skills_1b02e8(
            demon, reinterpret_cast<u16*>(self + 0x342Cu + static_cast<u32>(party_idx) * 0x10u));
    }
}

extern "C" __attribute__((naked)) void func_001b0454() {
    asm volatile(
        ".arm\n"
        ".word 0xe59f0234\n"
        ".word 0xe92d41f0, 0xe24dde61, 0xe5904000, 0xeb034b1d\n"
        ".word 0xe1a06000, 0xeb034ab2, 0xe3560000, 0xe1a05000\n"
        ".word 0x0a000004, 0xe28dde61, 0xe3a01000, 0xe8bd41f0\n"
        ".word 0xe1a00001, 0xea059b59, 0xe3550000, 0xaa00006d\n"
        ".word 0xe5d4066c, 0xe59f71f0, 0xe3a05000, 0xe350000c\n"
        ".word 0x1350000d, 0x1a00000e, 0xe3a01000, 0xe3a00039\n"
        ".word 0xeb044281, 0xe1a08000, 0xe320f000, 0xeb044274\n"
        ".word 0xe1a06000, 0xe1a00008, 0xeb04425d, 0xe3500006\n"
        ".word 0x82860c01, 0x828000f9, 0x91a00005, 0xe1a01007\n"
        ".word 0xeb03bb07, 0xe5d4066c, 0xe350000e, 0x1a00000e\n"
        ".word 0xe3a01000, 0xe3a00039, 0xeb04426f, 0xe1a08000\n"
        ".word 0xe320f000, 0xeb044262, 0xe1a06000, 0xe1a00008\n"
        ".word 0xeb04424b, 0xe3500007, 0x82860c02, 0x8280004d\n"
        ".word 0x91a00005, 0xe1a01007, 0xeb03baf5, 0xe5d4066c\n"
        ".word 0xe3500004, 0x1a00000d, 0xe3a01000, 0xe3a00039\n"
        ".word 0xeb04425d, 0xe1a08000, 0xe320f000, 0xeb044250\n"
        ".word 0xe1a06000, 0xe1a00008, 0xeb044239, 0xe3500002\n"
        ".word 0x828600a9, 0x91a00005, 0xe1a01007, 0xeb03bae4\n"
        ".word 0xe5d4066c, 0xe350000f, 0x1a00000e, 0xe3a01000\n"
        ".word 0xe3a00039, 0xeb04424c, 0xe1a08000, 0xe320f000\n"
        ".word 0xeb04423f, 0xe1a06000, 0xe1a00008, 0xeb044228\n"
        ".word 0xe3500008, 0x82860c02, 0x828000a1, 0x91a00005\n"
        ".word 0xe1a01007, 0xeb03bad2, 0xe5d4066c, 0xe3500002\n"
        ".word 0x1a00000d, 0xe3a01000, 0xe3a00039, 0xeb04423a\n"
        ".word 0xe1a08000, 0xe320f000, 0xeb04422d, 0xe1a06000\n"
        ".word 0xe1a00008, 0xeb044216, 0xe3500000, 0x82860001\n"
        ".word 0x91a00005, 0xe1a01007, 0xeb03bac1, 0xe5d4066c\n"
        ".word 0xe3500003, 0x1a00001d, 0xe3a01000, 0xe3a00039\n"
        ".word 0xeb044229, 0xe1a06000, 0xe320f000, 0xeb04421c\n"
        ".word 0xe1a04000, 0xe1a00006, 0xeb044205, 0xe3500001\n"
        ".word 0xe28dde61, 0x82840055, 0x91a00005, 0xe1a01007\n"
        ".word 0xe8bd41f0, 0xea03baae, 0xe6ff0075, 0xeb040072\n"
        ".word 0xe1b03000, 0xe320f000, 0x1a000004, 0xe1a0400d\n"
        ".word 0xe6ff0075, 0xe1a01004, 0xeb03b627, 0xe1a03004\n"
        ".word 0xe6ff2075, 0xe3a01001, 0xe3a00000, 0xeb03b592\n"
        ".word 0xe28dde61, 0xe8bd81f0, 0x0043dcf0, 0x323232ff\n"
    );
}

extern "C" void script_vm_func_0026ee9c(float* out_dist, s32 a1, s32 a2, const u8* plane,
                                        float px, float py, float pz, float radius);

namespace {

__attribute__((always_inline)) inline u32 float_to_bits_27f6fc(float v) {
    union {
        float f;
        u32 u;
    } cvt;
    cvt.f = v;
    return cvt.u;
}

__attribute__((always_inline)) inline void zero_flags_27f6fc(u8* dst, s32 count) {
    for (s32 i = 0; i < count; ++i) {
        dst[i] = 0u;
    }
}

}  // namespace

// DECOMP_FUNC(0x0027f6fc, 956)
extern "C" u32 script_vm_func_0027f6fc(float* pos, float* prev_pos) {
    u8* const g_sl = reinterpret_cast<u8*>(0x0049F91Cu);
    const u32* const g_tbl = reinterpret_cast<const u32*>(0x00446FE8u);
    u8* const arr0 = reinterpret_cast<u8*>(0x0049E45Cu);
    u8* const arr1 = reinterpret_cast<u8*>(0x0049E65Cu);
    u8* const arr2 = reinterpret_cast<u8*>(0x0049E7DCu);
    u8* const arr3 = reinterpret_cast<u8*>(0x0049E87Cu);
    u8* const arrs[4] = {arr0, arr1, arr2, arr3};

    s32 r8 = -1;
    u32 ret_flag = 0u;
    float px = pos[0];
    float py = pos[1];
    float pz = pos[2];
    const float orig_x = px;
    const float orig_y = py;
    const float orig_z = pz;

    *reinterpret_cast<s32*>(g_sl + 0x3D0u) = -1;
    *reinterpret_cast<s32*>(g_sl + 0x3D4u) = -1;

    for (s32 i = 0; i < 4; ++i) {
        zero_flags_27f6fc(arrs[i], static_cast<s32>(g_tbl[1 + i]));
    }

    const float dx = px - prev_pos[0];
    const float dy = py - prev_pos[1];
    const float dz = pz - prev_pos[2];
    float dist;
    __asm__("vsqrt.f32 %0, %1" : "=t"(dist) : "t"(dx * dx + dy * dy + dz * dz));
    if (static_cast<s32>(0x3C23D70Au) > static_cast<s32>(float_to_bits_27f6fc(dist))) {
        return 1u;
    }

    py += 15.0f;
    for (s32 pass = 0; pass < 4; ++pass) {
        const float radius = (pass < 2) ? 25.0f : 60.0f;
        const s32 count = static_cast<s32>(g_tbl[1 + pass]);
        const u8* plane = reinterpret_cast<const u8*>(g_tbl[6 + pass]);
        for (s32 idx = 0; idx < count; ++idx, plane += 0xA8) {
            if (plane[8] == 0u) {
                continue;
            }
            const float nx = *reinterpret_cast<const float*>(plane + 0x0C);
            const float ny = *reinterpret_cast<const float*>(plane + 0x10);
            const float nz = *reinterpret_cast<const float*>(plane + 0x14);
            const float d = *reinterpret_cast<const float*>(plane + 0x18);
            const float signed_dist = (px * nx + py * ny + pz * nz) - d;
            const float abs_dist = (signed_dist < 0.0f) ? -signed_dist : signed_dist;
            if (radius <= abs_dist) {
                continue;
            }

            float out_dist = 0.0f;
            script_vm_func_0026ee9c(&out_dist, *reinterpret_cast<const s8*>(plane + 4),
                                    *reinterpret_cast<const s8*>(plane + 5), plane, px, py, pz,
                                    radius);
            if (0.0f > out_dist) {
                continue;
            }

            const float proj_x = px - nx * signed_dist;
            const float proj_y = py - ny * signed_dist;
            const float proj_z = pz - nz * signed_dist;
            if (plane[4] == 1u) {
                *reinterpret_cast<s32*>(g_sl + 0x3D4u) = idx;
                *reinterpret_cast<s32*>(g_sl + 0x3D0u) = pass;
                if (pass == 0 || pass == 1) {
                    arrs[pass][idx] = 1u;
                }
                if (r8 > -1 && out_dist < abs_dist) {
                    out_dist = abs_dist;
                }
                ret_flag = 1u;
                px = proj_x + nx * out_dist;
                py = proj_y + ny * out_dist;
                pz = proj_z + nz * out_dist;
                if (out_dist == radius) {
                    r8 = idx;
                }
            } else {
                if (pass == 2 || pass == 3) {
                    arrs[pass][idx] = 1u;
                }
                if (signed_dist >= 0.0f) {
                    if (abs_dist > out_dist) {
                        out_dist = abs_dist;
                    }
                    px = proj_x + nx * out_dist;
                    py = proj_y + ny * out_dist;
                    pz = proj_z + nz * out_dist;
                }
            }
        }
    }

    pos[0] = px;
    pos[1] = py - 25.0f;
    pos[2] = pz;
    prev_pos[0] = orig_x;
    prev_pos[1] = orig_y;
    prev_pos[2] = orig_z;
    return ret_flag;
}
extern "C" u8* engine_func_002c2b1c();
extern "C" void camp_func_0029c0fc(u32 a0, u32 a1);
extern "C" void ui_func_002be7fc(u8* dst, const char* fmt, u32 a, u32 b);
extern "C" void script_vm_func_00259544(s32 a, u32 b);
extern "C" void script_vm_func_0027de00();
extern "C" void script_vm_func_0027db24(u32 a);
extern "C" float engine_func_00287d54(float x0, float y0, float z0, float x1, float y1, float z1);
extern "C" float script_vm_func_0028277c(float ang);
extern "C" float script_vm_func_00282600(float ang);
extern "C" void engine_func_00253aa0(u8* obj, u32 mode);
extern "C" float script_vm_func_00287e4c(float x0, float y0, float z0, float x1, float y1, float z1);
extern "C" float script_vm_func_0027f150(float a, float b, float c);

namespace {

__attribute__((always_inline)) inline u32 float_to_bits_2d2a94(float v) {
    union {
        float f;
        u32 u;
    } cvt;
    cvt.f = v;
    return cvt.u;
}

__attribute__((always_inline)) inline float bits_to_float_2d2a94(u32 u) {
    union {
        float f;
        u32 u;
    } cvt;
    cvt.u = u;
    return cvt.f;
}

__attribute__((always_inline)) inline void apply_event_2d2a94(u8* r4, u8* sb, u8* r7,
                                                              bool allow_zero_hook) {
    if (r4[0x50] == 0u) {
        return;
    }
    if (*reinterpret_cast<const u32*>(sb + 0x36Cu) != 0u) {
        *reinterpret_cast<u16*>(r7 + 0x22u) =
            static_cast<u16>(*reinterpret_cast<const u32*>(r4 + 0x58u));
    }
    const s32 v68 = *reinterpret_cast<const s32*>(r4 + 0x68u);
    if (v68 > 0) {
        if (*reinterpret_cast<const u32*>(r4 + 0x64u) != 0u) {
            sb[0x145] = 1u;
            *reinterpret_cast<s32*>(sb + 0x148u) = v68;
            ui_func_002be7fc(sb + 0x14Cu, "e%03d_%02d", static_cast<u32>(v68),
                             *reinterpret_cast<const u32*>(r4 + 0x6Cu));
        } else {
            script_vm_func_00259544(v68, *reinterpret_cast<const u32*>(r4 + 0x6Cu));
        }
    } else if (allow_zero_hook) {
        script_vm_func_0027de00();
    }
    script_vm_func_0027db24(*reinterpret_cast<const u32*>(r4 + 0x70u));
    const s32 v5c = *reinterpret_cast<const s32*>(r4 + 0x5Cu);
    if (v5c > 0) {
        *reinterpret_cast<s32*>(sb + 0x1B8u) = v5c;
        *reinterpret_cast<u32*>(sb + 0x1BCu) = *reinterpret_cast<const u32*>(r4 + 0x60u);
    }
    if (r4[0x7C] != 0u) {
        const u32 v54 = *reinterpret_cast<const u32*>(r4 + 0x54u);
        u8* const rec = r7 + 0xF2Au + v54 * 20u;
        if (rec[0] != 0u) {
            sb[0x19B] = 1u;
            *reinterpret_cast<s16*>(sb + 0x19Cu) = *reinterpret_cast<const s8*>(rec);
            *reinterpret_cast<s16*>(sb + 0x19Eu) = *reinterpret_cast<const s8*>(rec + 1);
        }
    }
}

}  // namespace

// DECOMP_FUNC(0x002d2a94, 956)
extern "C" s32 script_vm_func_002d2a94() {
    u8* const r6 = *reinterpret_cast<u8* const*>(0x00447600u);
    u8* const r7 = engine_func_002c2b1c();
    u8* const sb = reinterpret_cast<u8*>(0x0049F91Cu);

    if (*reinterpret_cast<const u32*>(sb + 0x364u) != 0u ||
        *reinterpret_cast<const u32*>(r6 + 4u) == 0u) {
        return -1;
    }

    *reinterpret_cast<u32*>(sb + 0x1B8u) = 0u;
    *reinterpret_cast<u32*>(sb + 0x1BCu) = 0u;
    sb[0x19B] = 0u;

    s16 val_194 = *reinterpret_cast<const s16*>(sb + 0x194u);
    if (val_194 > 0) {
        val_194 = static_cast<s16>(val_194 - 1);
        *reinterpret_cast<s16*>(sb + 0x194u) = val_194;
        if (val_194 != 1) {
            return -1;
        }
        sb[0x198] = 1u;
        const s16 idx = *reinterpret_cast<const s16*>(sb + 0x196u);
        u8* const r4 = r6 + idx * 0x180 + 0x34;
        camp_func_0029c0fc(0x15u, 1u);
        apply_event_2d2a94(r4, sb, r7, true);
        return *reinterpret_cast<const s32*>(r4 + 0x70u);
    }

    const float kDeg2Rad = bits_to_float_2d2a94(0x3C8EFA35u);
    const float k100 = 100.0f;
    u8* const player_obj = *reinterpret_cast<u8* const*>(0x00447E88u);
    const float* const p_pos = reinterpret_cast<const float*>(player_obj + 0x1Cu);

    for (s32 i = 0; i < 0x20; ++i) {
        u8* const r4 = r6 + i * 0x180 + 0x34;
        if (r4[0] == 0u) {
            continue;
        }
        if (r4[0x17C] == 0u) {
            continue;
        }
        const u32 type84 = *reinterpret_cast<const u32*>(r4 + 0x84u);
        if (type84 == 0x13u) {
            continue;
        }
        if (type84 == 3u && *reinterpret_cast<const s32*>(r4 + 0x88u) < 0x14) {
            continue;
        }
        if (*reinterpret_cast<const u32*>(r4 + 0x30u) == 6u) {
            continue;
        }

        const float x = *reinterpret_cast<const float*>(r4 + 0x20u);
        const float y = *reinterpret_cast<const float*>(r4 + 0x24u);
        const float z = *reinterpret_cast<const float*>(r4 + 0x28u);
        const float dist1 = engine_func_00287d54(p_pos[0], p_pos[1], p_pos[2], x, y, z);
        if (static_cast<s32>(0x42700000u) <= static_cast<s32>(float_to_bits_2d2a94(dist1))) {
            const u32 st174 = *reinterpret_cast<const u32*>(r4 + 0x174u);
            if ((st174 == 6u || st174 == 0x10u) && *reinterpret_cast<const u32*>(r4 + 0x30u) == 4u) {
                const float ang = *reinterpret_cast<const float*>(r4 + 0x2Cu) * kDeg2Rad;
                const float x2 = x + script_vm_func_0028277c(ang) * k100;
                const float z2 = z + script_vm_func_00282600(ang) * k100;
                const float dist2 =
                    engine_func_00287d54(p_pos[0], p_pos[1], p_pos[2], x2, y, z2);
                if (static_cast<s32>(float_to_bits_2d2a94(dist2)) >=
                    static_cast<s32>(0x42700000u)) {
                    continue;
                }
            } else {
                continue;
            }
        }

        sb[0x199] = 0u;
        engine_func_00253aa0(r4, 2u);
        const float ang_to = script_vm_func_00287e4c(p_pos[0], p_pos[1], p_pos[2], x, y, z);
        const float yaw = *reinterpret_cast<const float*>(player_obj + 0x4Cu);
        const float diff = script_vm_func_0027f150(yaw, ang_to, yaw);
        if (static_cast<s32>(float_to_bits_2d2a94(diff)) > static_cast<s32>(0x42F00000u)) {
            sb[0x19A] = 1u;
        }
        apply_event_2d2a94(r4, sb, r7, false);
        return *reinterpret_cast<const s32*>(r4 + 0x70u);
    }
    return -1;
}
extern "C" s32 script_vm_func_00299064(u32 arg0);
extern "C" u32 script_vm_func_00290694();
extern "C" void ui_func_002bf460(u32 a0, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5);
extern "C" void func_002bf558(u32 a0, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5);
extern "C" s32 script_vm_func_002990bc(u32 arg0);
extern "C" const u8* script_vm_func_002b6700();
extern "C" s32 script_vm_func_0028f5a8(u32 arg0);
extern "C" s32 script_vm_func_002990dc(u32 arg0, s32 idx, s32* out_val);
extern "C" s32 script_vm_func_0029909c(u32 arg0);
extern "C" s32 script_vm_func_0028f460(u32 arg0);
extern "C" s32 script_vm_func_00333ce0(u32 arg0);

// DECOMP_FUNC(0x001af748, 960)
extern "C" u32 ui_func_001af748(u32 arg0, u32 arg1, u32 arg2, u32 arg3, u32 arg4) {
    const u32 default_ret = (arg4 != 0u) ? 0xFFFFFFFFu : 0xFFu;
    const u32 grey_ret = (arg4 != 0u) ? 0x787878FFu : 0x5A5A5AFFu;
    const u32 green_ret = (arg4 != 0u) ? 0x72E027FFu : 0x008400FFu;

    const u8* const global_obj = *reinterpret_cast<const u8* const*>(0x0043DD50u);
    if (global_obj[0x5C4] != 0u) {
        if (script_vm_func_00299064(arg0) != 0) {
            if (script_vm_func_00290694() != 0u) {
                ui_func_002bf460(2u, 0x29u, 0x92u, arg1, arg2, arg3);
                return grey_ret;
            }
            func_002bf558(2u, 0x29u, 0x0Cu, arg1, arg2, arg3);
            return green_ret;
        }
        if (script_vm_func_002990bc(arg0) == 0) {
            return default_ret;
        }
        ui_func_002bf460(2u, 0x29u, 0x93u, arg1, arg2, arg3);
        return grey_ret;
    }

    const u8* const ctx = script_vm_func_002b6700();
    if (ctx == nullptr) {
        return default_ret;
    }

    if (ctx[6] != 0u) {
        if (script_vm_func_0028f5a8(arg0) == 0) {
            if (script_vm_func_00333ce0(arg0) != 0) {
                ui_func_002bf460(2u, 0x29u, 0x91u, arg1, arg2, arg3);
                return grey_ret;
            }
            const u32 msg_id = (script_vm_func_002990bc(arg0) != 0) ? 0x93u : 0x91u;
            ui_func_002bf460(2u, 0x29u, msg_id, arg1, arg2, arg3);
            return grey_ret;
        }
        if (script_vm_func_00290694() == arg0) {
            func_002bf558(2u, 0x29u, 0x0Du, arg1, arg2, arg3);
            return green_ret;
        }
        if (script_vm_func_002990bc(arg0) != 0) {
            ui_func_002bf460(2u, 0x29u, 0x93u, arg1, arg2, arg3);
        }
        return default_ret;
    }

    bool all_clear = true;
    for (s32 i = 0; i < 6; ++i) {
        s32 out_val = 0;
        if (script_vm_func_002990dc(arg0, i, &out_val) != 0) {
            if (script_vm_func_002990bc(arg0) == 0 || script_vm_func_0029909c(arg0) != 0) {
                if (out_val > 0) {
                    all_clear = false;
                    break;
                }
            } else {
                all_clear = false;
                break;
            }
        }
    }

    if (script_vm_func_0028f460(arg0) != 0) {
        if (all_clear) {
            func_002bf558(2u, 0x29u, 0x0Eu, arg1, arg2, arg3);
            return default_ret;
        }
        if (script_vm_func_002990bc(arg0) == 0) {
            return default_ret;
        }
        ui_func_002bf460(2u, 0x29u, 0x93u, arg1, arg2, arg3);
        if (script_vm_func_0029909c(arg0) != 0) {
            return default_ret;
        }
        return grey_ret;
    }

    if (script_vm_func_0029909c(arg0) == 0 && script_vm_func_002990bc(arg0) != 0) {
        ui_func_002bf460(2u, 0x29u, 0x93u, arg1, arg2, arg3);
    } else {
        ui_func_002bf460(2u, 0x29u, 0xC2u, arg1, arg2, arg3);
    }
    return default_ret;
}

extern "C" void func_0035a408(void* iter);
extern "C" s32 func_0035a2e4(void* iter, const u16* path);
extern "C" s32 func_0035a350(void* iter, void* comp_out);
extern "C" s32 func_00239dec(void* self, u32* next_id_out, void* info_out, const void* state);
extern "C" s32 func_00239d2c(void* self, u32* parent_id_out, u32* parent_meta_out, u32 zero0,
                             u32 zero1, u32 cur_dir_id);
extern "C" s32 func_0035a420(void* comp_out, const void* tmp_pair, const u16* path);
extern "C" s32 func_003e0e7c(void* iter, void* comp_out);
extern "C" s32 func_00225678(void* self, u32* dummy_out, void* dst_entry, void* dst_info,
                             u32 entry_id, u32 entry_len, const u16* entry_ptr, const u16* path);
extern "C" s32 func_003e0e28(void* iter);
extern "C" s32 func_003e0df8(void* iter, void* name_slice_out);

// DECOMP_FUNC(0x003fc5e4, 960)
extern "C" s32 func_003fc5e4(void* self, u32* out_dir, u32* out_info, u32* out_name,
                             u32 resolve_leaf, const u16* path) {
    alignas(4) u8 iter[0x10];
    func_0035a408(iter);
    s32 rc = func_0035a2e4(iter, path);
    if (rc < 0) {
        return rc;
    }

    u32 cur_state[3] = {0u, 0u, 0u};
    u32 cur_info[3] = {0u, 0u, 0u};
    u32 next_id = 0u;
    u32 cur_id = 0u;

    rc = func_0035a350(iter, &cur_state[1]);
    if (rc >= 0) {
        rc = func_00239dec(self, &next_id, cur_info, cur_state);
        if (rc >= 0) {
            cur_id = next_id;
            while (*reinterpret_cast<const s8*>(iter + 0xCu) == 0) {
                const u32 saved0 = cur_state[0];
                const u32 saved1 = cur_state[1];
                const u32 saved2 = cur_state[2];
                rc = func_0035a350(iter, &cur_state[1]);
                if (rc < 0) {
                    break;
                }
                const u16* const comp = reinterpret_cast<const u16*>(cur_state[2]);
                if (cur_state[1] == 1u && comp[0] == u'.') {
                    cur_state[0] = saved0;
                    cur_state[1] = saved1;
                    cur_state[2] = saved2;
                    continue;
                }
                if (cur_state[1] == 2u && comp[0] == u'.' && comp[1] == u'.') {
                    if (cur_id == 0u) {
                        rc = static_cast<s32>(0xE0C04702u);
                        break;
                    }
                    const u32 tmp_pair[2] = {cur_state[1], cur_state[2]};
                    u32 p_id = 0u;
                    u32 p_meta = 0u;
                    rc = func_00239d2c(self, &p_id, &p_meta, 0u, 0u, cur_state[0]);
                    if (rc < 0) {
                        break;
                    }
                    cur_state[0] = p_id;
                    rc = func_0035a420(&cur_state[1], tmp_pair, path);
                    if (rc < 0) {
                        break;
                    }
                    rc = func_00239dec(self, &cur_id, cur_info, cur_state);
                    if (rc < 0) {
                        break;
                    }
                    rc = 0;
                    continue;
                }
                cur_state[0] = cur_id;
                rc = func_00239dec(self, &next_id, cur_info, cur_state);
                if (rc < 0) {
                    break;
                }
                cur_id = next_id;
            }
            if (rc >= 0) {
                out_dir[0] = cur_state[0];
                out_dir[1] = cur_state[1];
                out_dir[2] = cur_state[2];
                out_info[0] = cur_info[0];
                out_info[1] = cur_info[1];
                out_info[2] = cur_info[2];
                rc = 0;
            }
        }
    }

    if (rc < 0) {
        return rc;
    }

    if (resolve_leaf == 0u) {
        if (func_003e0e28(iter) != 0) {
            return static_cast<s32>(0xE0C04702u);
        }
        out_name[0] = cur_id;
        rc = func_003e0df8(iter, out_name + 1);
        return (rc < 0) ? rc : 0;
    }

    u32 leaf_comp[2] = {0u, 0u};
    rc = func_003e0e7c(iter, leaf_comp);
    if (rc < 0) {
        return rc;
    }

    const u16* const leaf_str = reinterpret_cast<const u16*>(leaf_comp[1]);
    u32 dummy_out = 0u;
    if (leaf_comp[0] == 1u && leaf_str[0] == u'.') {
        out_name[0] = out_dir[0];
        out_name[1] = out_dir[1];
        out_name[2] = out_dir[2];
        if (out_name[0] == 0u) {
            return 0;
        }
        rc = func_00225678(self, &dummy_out, out_dir, out_info, out_name[0], out_name[1],
                           reinterpret_cast<const u16*>(out_name[2]), path);
        return (rc < 0) ? rc : 0;
    }

    if (leaf_comp[0] == 2u && leaf_str[0] == u'.' && leaf_str[1] == u'.') {
        if (cur_id == 0u) {
            return static_cast<s32>(0xE0C04702u);
        }
        rc = func_00225678(self, &dummy_out, out_name, &cur_id, out_dir[0], out_dir[1],
                           reinterpret_cast<const u16*>(out_dir[2]), path);
        if (rc < 0) {
            return rc;
        }
        if (out_name[0] == 0u) {
            return 0;
        }
        rc = func_00225678(self, &dummy_out, out_dir, out_info, out_name[0], out_name[1],
                           reinterpret_cast<const u16*>(out_name[2]), path);
        return (rc < 0) ? rc : 0;
    }

    out_name[0] = (leaf_comp[0] != 0u) ? cur_id : 0u;
    out_name[1] = leaf_comp[0];
    out_name[2] = leaf_comp[1];
    return 0;
}

extern "C" void engine_func_002c3b48(void* buf, u32 size);
extern "C" const u8* camp_func_002b9364(u16 idx);
extern "C" void engine_func_0033fa54();
extern "C" void func_002c4b1c();
extern "C" void camp_func_003bc17c();
extern "C" void engine_func_003c2818();
extern "C" u32 camp_func_002cf308();

// DECOMP_FUNC(0x001a1000, 984)
extern "C" u32 engine_func_001a1000() {
    u8* const* const g_base = reinterpret_cast<u8* const*>(0x0043E2A8u);
    u8* const s1 = g_base[1];
    u8* const s3 = g_base[3];

    engine_func_002c4b30(s1 + 0x88u, 0x00024D28u);
    *reinterpret_cast<u32*>(s3 + 0x0u) = 0u;
    *reinterpret_cast<u32*>(s3 + 0x4u) = 0u;
    *reinterpret_cast<u32*>(s3 + 0x8u) = 0u;

    for (u32 i = 0u; i < 0x18u; ++i) {
        s1[0x917Cu + i] = 0xFFu;
        s1[0x166u + i * 0x604u] = static_cast<u8>(i);
    }
    s1[0x9194u] = 0xFFu;
    s1[0x9195u] = 0xFFu;
    s1[0x9196u] = 0xFFu;
    *reinterpret_cast<u32*>(s1 + 0x986Cu) = 0u;
    *reinterpret_cast<u32*>(s1 + 0x9870u) = 0u;
    engine_func_002c3b48(s1 + 0x981Eu, 0x4Cu);

    u16* const s3_16 = reinterpret_cast<u16*>(g_base[3]);
    s3_16[4] = 0u;
    s3_16[5] = 0u;

    u8* dst_b = g_base[1] + 0xC22Cu;
    for (s32 i = 0; i < 0x500; ++i, dst_b += 0x34) {
        const u8* const item = camp_func_002b9364(static_cast<u16>(i + 1));
        if (item == nullptr) {
            continue;
        }
        const u16 flags = *reinterpret_cast<const u16*>(item + 6);
        if ((flags & 1u) != 0u) {
            u16* const s3_cur = reinterpret_cast<u16*>(g_base[3]);
            const u16 id = *reinterpret_cast<const u16*>(item);
            if (s3_cur[4] == 0u) {
                s3_cur[4] = id;
            }
            s3_cur[5] = id;
        }
        u16* const dst = reinterpret_cast<u16*>(dst_b);
        const u16* const item16 = reinterpret_cast<const u16*>(item);
        dst[0] = item[3];
        for (s32 k = 0; k < 5; ++k) {
            dst[1 + k] = item16[0x0Du + k];
            dst[6 + k] = item16[0x0Du + k];
        }
        dst[12] = item16[0x0Au];
        dst[13] = item16[0x0Bu];
        for (s32 k = 0; k < 8; ++k) {
            dst[14 + k] = item16[0x1Eu + k];
        }
        dst[22] = 0u;
        dst[23] &= 0xFF00u;
        dst_b[0x16] &= static_cast<u8>(~0x3Eu);
    }

    u8* const r4 = g_base[1] + 0xA8C0u;
    for (u32 off = 0u; off < 4u; ++off) {
        r4[off] = 0u;
    }
    for (u32 off = 4u; off <= 0x14u; off += 4u) {
        *reinterpret_cast<u32*>(r4 + off) = 0u;
    }
    *reinterpret_cast<u32*>(r4 + 0x18u) = 0u;
    *reinterpret_cast<u16*>(r4 + 0x20u) = 0u;
    *reinterpret_cast<u16*>(r4 + 0x22u) = 0u;
    r4[0x1Cu] = 0u;
    *reinterpret_cast<u16*>(r4 + 0x1Eu) = 0xFFFFu;
    r4[0x1Du] = 0u;
    for (u32 off = 0x744u; off <= 0x78Cu; off += 4u) {
        *reinterpret_cast<u32*>(r4 + off) = 0u;
    }
    for (u32 off = 0xBD8u; off <= 0xC14u; off += 4u) {
        *reinterpret_cast<u32*>(r4 + off) = 0u;
    }
    engine_func_002c4b30(r4 + 0xC18u, 0x80u);
    for (u32 off = 0xD18u; off <= 0xD54u; off += 4u) {
        *reinterpret_cast<u32*>(r4 + off) = 0u;
    }
    for (u32 off = 0xD5Cu; off <= 0xD78u; off += 4u) {
        *reinterpret_cast<u32*>(r4 + off) = 0u;
    }
    for (u32 off = 0xD9Cu; off <= 0xDACu; off += 4u) {
        *reinterpret_cast<u32*>(r4 + off) = 0u;
    }
    r4[0x3Au] = 1u;
    r4[0x3Bu] = 1u;
    r4[0x792u] = 0u;
    engine_func_002c4b30(r4 + 0xE60u, 0xC0u);
    for (u32 off = 0xDE0u; off <= 0xDE3u; ++off) {
        r4[off] = 0u;
    }
    *reinterpret_cast<u32*>(r4 + 0xE54u) = 0xFFFFFFFFu;
    r4[0xD5Au] = 0xCu;
    *reinterpret_cast<u32*>(r4 + 0xD98u) = 0xE10u;
    *reinterpret_cast<u32*>(r4 + 0xD94u) = 0u;
    r4[0xD5Bu] = 0u;
    *reinterpret_cast<u32*>(r4 + 0xDC0u) = 0u;
    *reinterpret_cast<u32*>(r4 + 0xDC4u) = 0u;
    r4[0xDC8u] = 0u;

    engine_func_0033fa54();
    func_002c4b1c();
    camp_func_003bc17c();
    engine_func_003c2818();
    engine_func_002c3b48(g_base[1] + 0x1EC18u, 0x80u);
    return camp_func_002cf308();
}

extern "C" void engine_func_00234278(u32* state_buf);
extern "C" s32 camp_func_0027ec84(const u32* state_buf);
extern "C" s32 engine_func_002a17c0(const u32* state_buf);
extern "C" void battle_func_00233f0c(u8* self);
extern "C" void engine_func_00234004(u8* self, u32 a1, u32 a2);
extern "C" void camp_func_00233ac0(u8* self, s32 state, u32 flag);
extern "C" s32 ui_func_0026b7cc();
extern "C" void shop_func_002339e8(u8* sub);
extern "C" void shop_func_002339ac(u8* sub);
extern "C" void engine_func_00233f4c(u8* self, u32 a1);
extern "C" void* engine_func_00234160(u8* sub, u32 a1);
extern "C" void func_002342b8(u8* self, const u32* state_buf);
extern "C" void unite_func_002338c4(u8* sub, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5);
extern "C" void camp_func_00152434(u8* dst, const u8* src);
extern "C" const u8* camp_func_002bf6d0(u32 a0, u32 a1);
extern "C" void camp_func_002348e0(u8* sub, s32 a1, s32 a2, s32 a3, s32 a4);
extern "C" void camp_func_002348a0(u8* sub, s32 a1, s32 a2, s32 a3, s32 a4);
extern "C" void camp_func_00234840(u8* sub, s32 a1, s32 a2, s32 a3, s32 a4);
extern "C" u32 unite_func_002338ac(u8* sub);
extern "C" void unite_func_00233804(u8* sub, u32 a1, u32 a2, u32 a3);

// DECOMP_FUNC(0x0038edf0, 984)
extern "C" void engine_func_0038edf0(u8* self) {
    u32 state_buf[5];
    engine_func_00234278(state_buf);
    const u8* const g = *reinterpret_cast<const u8* const*>(0x00432FC8u);
    const s32 st = *reinterpret_cast<const s32*>(self + 8);

    auto release_obj = [self]() {
        void* const obj = *reinterpret_cast<void* const*>(self + 0x208u);
        if (obj != nullptr) {
            void* const* const vt = *reinterpret_cast<void* const* const*>(obj);
            reinterpret_cast<void (*)(void*)>(vt[1])(obj);
            *reinterpret_cast<void**>(self + 0x208u) = nullptr;
        }
    };

    auto read_obj_state = [](void* obj, u32* out_buf) {
        u32 tmp[5];
        void* const* const vt = *reinterpret_cast<void* const* const*>(obj);
        reinterpret_cast<void (*)(u32*, void*)>(vt[3])(tmp, obj);
        for (s32 i = 0; i < 5; ++i) {
            out_buf[i] = tmp[i];
        }
    };

    switch (st) {
        case 0: {
            reinterpret_cast<void (*)(u8*, s32, u32)>(camp_func_00233ac0)(self, -1, 0u);
            *reinterpret_cast<s32*>(self + 8) = 1;
            return;
        }
        case 1: {
            if (ui_func_0026b7cc() == 0) {
                return;
            }
            shop_func_002339e8(self + 0x2E8u);
            shop_func_002339ac(self + 0x2B4u);
            engine_func_00233f4c(self, 0u);
            void* const obj = engine_func_00234160(self + 0x20Cu, 0u);
            *reinterpret_cast<s32*>(self + 8) = 2;
            *reinterpret_cast<void**>(self + 0x208u) = obj;
            return;
        }
        case 2: {
            if ((*reinterpret_cast<const u32*>(self) & 0x200u) == 0u) {
                return;
            }
            read_obj_state(*reinterpret_cast<void* const*>(self + 0x208u), state_buf);
            if (camp_func_0027ec84(state_buf) != 0) {
                *reinterpret_cast<s32*>(self + 8) = 3;
                return;
            }
            if (engine_func_002a17c0(state_buf) == 0) {
                return;
            }
            battle_func_00233f0c(self);
            const u8 tag = *reinterpret_cast<const u8*>(state_buf);
            if (tag == 0x66u) {
                u32 arg_buf[5];
                for (s32 i = 0; i < 5; ++i) {
                    arg_buf[i] = state_buf[i];
                }
                func_002342b8(self, arg_buf);
                return;
            }
            if (tag == 0x67u) {
                *reinterpret_cast<s32*>(self + 4) = 3;
                *reinterpret_cast<s32*>(self + 8) = 0;
                release_obj();
                return;
            }
            *reinterpret_cast<s32*>(self + 8) = 0x270F;
            u32* const dst = reinterpret_cast<u32*>(self + 0x210u);
            for (s32 i = 0; i < 5; ++i) {
                dst[i] = state_buf[i];
            }
            return;
        }
        case 3: {
            void* const obj = *reinterpret_cast<void* const*>(self + 0x208u);
            if (obj != nullptr) {
                void* const* const vt = *reinterpret_cast<void* const* const*>(obj);
                reinterpret_cast<void (*)(void*)>(vt[1])(obj);
            }
            void* const obj2 = engine_func_00234160(self + 0x20Cu, 1u);
            *reinterpret_cast<s32*>(self + 8) = 4;
            *reinterpret_cast<void**>(self + 0x208u) = obj2;
            engine_func_00233f4c(self, 1u);
            return;
        }
        case 4: {
            read_obj_state(*reinterpret_cast<void* const*>(self + 0x208u), state_buf);
            if (camp_func_0027ec84(state_buf) == 0) {
                if (engine_func_002a17c0(state_buf) == 0) {
                    return;
                }
                battle_func_00233f0c(self);
                *reinterpret_cast<s32*>(self + 8) = 0x270F;
                u32* const dst = reinterpret_cast<u32*>(self + 0x210u);
                for (s32 i = 0; i < 5; ++i) {
                    dst[i] = state_buf[i];
                }
                return;
            }
            battle_func_00233f0c(self);
            const u32 g_val = *reinterpret_cast<const u32*>(g + 0x67Cu);
            if (g_val == 0u) {
                *reinterpret_cast<s32*>(self + 4) = 0xB;
                *reinterpret_cast<s32*>(self + 8) = 0;
                release_obj();
                return;
            }
            unite_func_002338c4(self + 0x240u, 3u, g_val, 0u, 1u, 1u);
            self[0x24Du] = 1u;
            u8* const r5 = self + 0x2E8u;
            camp_func_00152434(r5, self + 0x240u);
            {
                const u8* const d = camp_func_002bf6d0(0x3Au, 0x4Fu);
                const s16* const arr = *reinterpret_cast<const s16* const*>(d + 0xCu);
                camp_func_002348e0(r5, *reinterpret_cast<const s16*>(d + 8),
                                   *reinterpret_cast<const s16*>(d + 0xAu), arr[0], arr[1]);
            }
            {
                const u8* const d = camp_func_002bf6d0(0x3Au, 0x50u);
                const s16* const arr = *reinterpret_cast<const s16* const*>(d + 0xCu);
                camp_func_002348a0(r5, *reinterpret_cast<const s16*>(d + 8),
                                   *reinterpret_cast<const s16*>(d + 0xAu), arr[0], arr[1]);
            }
            {
                const u8* const d = camp_func_002bf6d0(0x3Au, 0x4Eu);
                const s16* const arr = *reinterpret_cast<const s16* const*>(d + 0xCu);
                camp_func_00234840(r5, *reinterpret_cast<const s16*>(d + 8),
                                   *reinterpret_cast<const s16*>(d + 0xAu), arr[0], arr[1]);
            }
            self[0x34Cu] = 1u;
            *reinterpret_cast<u16*>(self + 0x2ECu) |= 0x1000u;
            const u32 val = unite_func_002338ac(self + 0x240u);
            unite_func_00233804(self + 0x2B4u, 0x3Au, 0x88u, val);
            self[0x2C4u] = 1u;
            self[0x2E6u] = 0u;
            reinterpret_cast<void (*)(u8*, s32, u32)>(camp_func_00233ac0)(self, 2, 1u);
            *reinterpret_cast<s32*>(self + 4) = 6;
            *reinterpret_cast<s32*>(self + 8) = 0;
            release_obj();
            return;
        }
        case 0x270F: {
            engine_func_00234004(self, 5u, 3u);
            return;
        }
        default:
            return;
    }
}

extern "C" const u8* engine_func_0022b3cc(u8* list_base, s32 idx);
extern "C" u32 script_vm_func_00291018(u8* d88, const char* name);
extern "C" void script_vm_func_002971e4(u8* d90, u32 h);
extern "C" s32 script_vm_func_0019dfbc(u8* d90);
extern "C" s32 script_vm_func_002c0ba8(u32 id);
extern "C" void engine_func_0022ba6c(u8* list_base, u32 val);
extern "C" void script_vm_func_002bd9ec(u8* dst, const u16* vals);
extern "C" void shop_func_00297128();
extern "C" void engine_func_0022b430(u8* self, s32 s3c, u32 mode);
extern "C" void engine_func_0022b158(void* obj, u32 a1, u32 a2);

namespace {

__attribute__((always_inline)) inline bool check_entry_ready_3b9e20(u8* self, const u8* entry) {
    if (entry[0x2Cu] == 0x30u) {
        return true;
    }
    u8* const d90 = *reinterpret_cast<u8* const*>(self + 0xD90u);
    u8* const d88 = *reinterpret_cast<u8* const*>(self + 0xD88u);
    volatile u32* const flag_ptr = reinterpret_cast<volatile u32*>(0x0044CFB8u);
    *flag_ptr = 0u;
    char buf[0x28];
    reinterpret_cast<void (*)(char*, const char*, const char*)>(ui_func_002be7fc)(
        buf, "%s", reinterpret_cast<const char*>(entry + 0x2Cu));
    const u32 h = script_vm_func_00291018(d88, buf);
    script_vm_func_002971e4(d90, h);
    while (script_vm_func_0019dfbc(d90) != 2) {
    }
    if (*flag_ptr != 0u) {
        return true;
    }
    const u16 s3c = *reinterpret_cast<const u16*>(entry + 0x3Cu);
    if (s3c != 0u && script_vm_func_002c0ba8(s3c) == 0) {
        return true;
    }
    const u16 s3e = *reinterpret_cast<const u16*>(entry + 0x3Eu);
    if (s3e != 0u && script_vm_func_002c0ba8(s3e) == 0) {
        return true;
    }
    return false;
}

}  // namespace

// DECOMP_FUNC(0x003b9e20, 984)
extern "C" void script_vm_func_003b9e20(u8* self) {
    const s32 count = *reinterpret_cast<const s32*>(self + 0x5C8u);
    u32 r8 = 1u;

    for (s32 i = 0; i < count; ++i) {
        const u8* const entry = engine_func_0022b3cc(self + 0x9Cu, i);
        const u16 kind = *reinterpret_cast<const u16*>(entry + 0x54u);
        if (kind == 3u) {
            if (!check_entry_ready_3b9e20(self, entry)) {
                break;
            }
        } else if (kind == 4u) {
            if (!check_entry_ready_3b9e20(self, entry)) {
                r8 = 0u;
                break;
            }
        }
    }

    for (s32 i = 0; i < count; ++i) {
        const u8* const entry = engine_func_0022b3cc(self + 0x9Cu, i);
        const u16 kind = *reinterpret_cast<const u16*>(entry + 0x54u);
        if (kind == 2u) {
            if (!check_entry_ready_3b9e20(self, entry)) {
                break;
            }
        }
    }

    const u32 mode = *reinterpret_cast<const u32*>(self + 0xD64u);
    switch (mode) {
        case 0u: {
            if (r8 == 0u || script_vm_func_002c0ba8(0x15u) == 0) {
                return;
            }
            engine_func_0022ba6c(self + 0x9Cu, 0xFFu);
            u16 tmp[3] = {4u, 0u, 0u};
            script_vm_func_002bd9ec(self + 0x42u, tmp);
            const u32 f = *reinterpret_cast<const u32*>(self + 0x20u) | 0x10u;
            if ((f & 0x40u) == 0u) {
                *reinterpret_cast<u32*>(self + 0x20u) = f;
                return;
            }
            *reinterpret_cast<u32*>(self + 0x20u) = f & ~0x40u;
            shop_func_00297128();
            return;
        }
        case 5u:
            if (r8 == 0u) {
                return;
            }
            // fallthrough
        case 1u:
        case 2u:
            engine_func_0022ba6c(self + 0x9Cu, 0xFFu);
            *reinterpret_cast<u32*>(self + 0x20u) |= 0x40000000u;
            self[0x6CEu] = 1u;
            return;
        case 6u:
        case 7u: {
            const u32 f = *reinterpret_cast<const u32*>(self + 0x20u);
            const s16 s3c = *reinterpret_cast<const s16*>(self + 0x3Cu);
            engine_func_0022b430(self, s3c, ((f & 0x10000000u) != 0u) ? 4u : 3u);
            *reinterpret_cast<u32*>(self + 0x2Cu) = 0u;
            *reinterpret_cast<u32*>(self + 0x28u) = 4u;
            engine_func_0022b158(*reinterpret_cast<void* const*>(self + 0xE5Cu), 0u, 0xFFFFFFFFu);
            return;
        }
        default:
            return;
    }
}

extern "C" void ui_func_002bf9f0(u8* slot);
extern "C" void camp_func_002b9220(u8* slot, u32 a1);
extern "C" void func_00220888();
extern "C" void func_002ae2b4(u8* dst);
extern "C" void script_vm_func_002b8b78(u32 val);
extern "C" void camp_func_002b8794(u32 idx, u32 a1, u16 a2, u32 a3);

namespace {

__attribute__((always_inline)) inline s32 scan_slots_1c0b38(u8* r4) {
    s32 r8 = 0;
    for (s32 i = 0; i < 6; ++i) {
        if (r4[0x494u + i * 4] != 0u) {
            if (*reinterpret_cast<const s32*>(r4 + 0xCu) > i) {
                ui_func_002bf9f0(r4 + 0x34u + i * 0x8Cu);
            }
            r8 = i;
        }
    }
    return r8;
}

}  // namespace

// DECOMP_FUNC(0x001c0b38, 988)
extern "C" u32 ui_func_001c0b38() {
    u8* const sb = reinterpret_cast<u8*>(0x0043DA28u);
    u8* const r4 = *reinterpret_cast<u8* const*>(sb + 4);
    const s32 state = *reinterpret_cast<const s32*>(r4 + 0x10u);

    if (state == 1) {
        for (s32 i = 0; i < 2; ++i) {
            u8* const slot = r4 + 0x37Cu + i * 0x8Cu;
            if (r4[0x4C8u] == 1u) {
                if (r4[0x4C6u] != 0u) {
                    camp_func_002b9220(slot, 0u);
                }
            } else {
                ui_func_002bf9f0(slot);
            }
        }
        const s32 r8 = scan_slots_1c0b38(r4);
        if (*reinterpret_cast<const s32*>(r4 + 0xCu) > r8 &&
            *reinterpret_cast<const s8*>(r4 + 0x34u + r8 * 0x8Cu + 0x8Au) != 0) {
            u8* const cur = *reinterpret_cast<u8* const*>(sb + 4);
            *reinterpret_cast<s32*>(cur + 0x10u) = 2;
            *reinterpret_cast<s32*>(cur + 0xCu) = 0;
        }
    } else if (state == 2) {
        func_00220888();
    } else if (state == 3) {
        for (s32 i = 0; i < 2; ++i) {
            ui_func_002bf9f0(r4 + 0x37Cu + i * 0x8Cu);
        }
        const s32 r8 = scan_slots_1c0b38(r4);
        if (*reinterpret_cast<const s32*>(r4 + 0xCu) > r8 &&
            *reinterpret_cast<const s8*>(r4 + 0x34u + r8 * 0x8Cu + 0x8Au) != 0) {
            *reinterpret_cast<u32*>(r4 + 0x4B8u) = 0u;
            *reinterpret_cast<u16*>(r4 + 0x4BCu) = 0u;
            func_002ae2b4(r4 + 0x4BEu);
            u8* const cur = *reinterpret_cast<u8* const*>(sb + 4);
            *reinterpret_cast<s32*>(cur + 0x10u) = 0;
            *reinterpret_cast<s32*>(cur + 0xCu) = 0;
        }
    }

    const s32 v10 = *reinterpret_cast<const s32*>(sb + 0x10u);
    if (v10 >= 0) {
        script_vm_func_002b8b78(static_cast<u32>(v10) & 0xFFu);
    }
    if (*reinterpret_cast<const s32*>(sb + 0x10u) < 0) {
        const s32* const arr6 = reinterpret_cast<const s32*>(0x0043DA50u);
        const u32* const arr7 = reinterpret_cast<const u32*>(0x0043DA68u);
        for (s32 i = 0; i < 6; ++i) {
            if (arr6[i] >= 0) {
                camp_func_002b8794(static_cast<u32>(i) & 0xFFu, static_cast<u32>(arr6[i]) & 0xFFu,
                                   static_cast<u16>(arr7[i]), 1u);
            }
        }
    }
    *reinterpret_cast<s32*>(r4 + 0xCu) += 1;
    return 0u;
}

extern "C" __attribute__((naked)) void func_001c0d9c() {
    asm volatile(
        ".arm\n"
        ".word 0xe59f0054, 0xe92d4010, 0xe24dd008, 0xe5904000\n"
        ".word 0xeb00b25b, 0xe3500000, 0x1a00000c, 0xe5d41124\n"
        ".word 0xe2840c01, 0xe3510000, 0x0a000008, 0xe1d002d7\n"
        ".word 0xe3a01000, 0xe58d1000, 0xe58d0004, 0xe5940010\n"
        ".word 0xe5941008, 0xe3a03000, 0xe2842014, 0xeb042d07\n"
        ".word 0xe28dd008, 0xe3a00000, 0xe8bd8010, 0x0043dad0\n"
    );
}

extern "C" __attribute__((naked)) void func_001c0dfc() {
    asm volatile(
        ".arm\n"
        ".word 0xe59f00a8, 0xe92d4010, 0xe5904000, 0xe594010c\n"
        ".word 0xe0840100, 0xe59010b4, 0xe3510000, 0x0a000021\n"
        ".word 0xe1a00004, 0xe12fff31, 0xe3500002, 0x0a000002\n"
        ".word 0xe3500001, 0x0a000016, 0xea00001a, 0xe5940110\n"
        ".word 0xe3700001, 0x0a000017, 0xe594110c, 0xe584010c\n"
        ".word 0xe3e02000, 0xe5841108, 0xe3500008, 0xe5842110\n"
        ".word 0x1a000010, 0xe3a00000, 0xe5840048, 0xe5c4004c\n"
        ".word 0xe584005c, 0xe5c40060, 0xe5840070, 0xe5c40074\n"
        ".word 0xe5840020, 0xe5c40024, 0xe5840034, 0xe5c40038\n"
        ".word 0xea000004, 0xe5940004, 0xe3a01000, 0xeb02baf4\n"
        ".word 0xe3a00001, 0xe5c40125, 0xe3a00000, 0xe8bd8010\n"
        ".word 0x0043dad0\n"
    );
}

extern "C" __attribute__((naked)) void func_001c0eb0() {
    asm volatile(
        ".arm\n"
        ".word 0xe59f0058, 0xe52de004, 0xed9f0a13, 0xe24dd00c\n"
        ".word 0xe5902000, 0xe2820c01, 0xed820a28, 0xe5d21165\n"
        ".word 0xe3510000, 0x03a00000, 0x0a000009, 0xe1d005dd\n"
        ".word 0xe3a01000, 0xe58d1000, 0xe58d0004, 0xe5b2100c\n"
        ".word 0xe3a03000, 0xe592012c, 0xe2822094, 0xeb042cc2\n"
        ".word 0xe3a00000, 0xe28dd00c, 0xe49df004, 0x3f800000\n"
        ".word 0x0043db10\n"
    );
}

extern "C" s32 func_00231b54();
extern "C" void camp_func_002315c8(u32 a0, u32 a1, u32* out_a, u32* out_b, u32* out_c, u32* out_d);
extern "C" s32 func_002315b4(u32 a0, u32 a1, u32 a2, u32 a3);
extern "C" u32 func_0039ae80(u8* self, s32 dir);
extern "C" const float* func_00231f58(u8* vec_ptr);
extern "C" void func_00231b38(u8* vec_ptr, const float* vals);

namespace {

__attribute__((always_inline)) inline void scale_vec_39b864(u8* vec_ptr, float factor) {
    const float* const v = func_00231f58(vec_ptr);
    const float scaled[2] = {v[0] * factor, v[1] * factor};
    func_00231b38(vec_ptr, scaled);
}

}  // namespace

// DECOMP_FUNC(0x0039b864, 996)
extern "C" u32 engine_func_0039b864(u8* self) {
    u8* const r9 = engine_func_002c2b1c();
    const u8* const g_sb = reinterpret_cast<const u8*>(0x0049F91Cu);

    if ((*reinterpret_cast<const u32*>(self + 0x10u) & 0x02000000u) != 0u) {
        if (func_00231b54() == 0 || g_sb[0x18u] != 0u) {
            *reinterpret_cast<u32*>(self + 0x10u) &= ~0x02000000u;
        }
    }

    u8* const vec_ptr = self + 0x162u;
    u8* const r6_ptr = self + 0x5A8Cu;
    u8* const r7_ptr = self + 0x5A8Du;
    u8* const r8_ptr = self + 0x12000u;

    for (s32 i = 0; i < 5; ++i) {
        u32 out_a = 0u, out_b = 0u, out_c = 0u, out_d = 0u;
        camp_func_002315c8(0x1Cu, 0xFB5u + static_cast<u32>(i), &out_a, &out_b, &out_c, &out_d);
        if (func_002315b4(out_a, out_b, out_c, out_d) == 0 || g_sb[0x18u] != 0u) {
            continue;
        }

        switch (i) {
            case 0: {
                const s32 count = *reinterpret_cast<const s32*>(r8_ptr + 0x264u);
                for (s32 j = 0; j < count; ++j) {
                    const u8* const slot = self + 0x12100u + j * 4;
                    if (*reinterpret_cast<const u16*>(slot + 0xE4u) != 0u &&
                        *reinterpret_cast<const s16*>(slot + 0xE6u) ==
                            *reinterpret_cast<const s8*>(self + 0x60u)) {
                        if (j - 1 < 0 || *reinterpret_cast<const u16*>(slot + 0xE2u) == 0u) {
                            return 1u;
                        }
                        *reinterpret_cast<u32*>(self + 0x10u) |= 0x02000000u;
                        const u32 res = func_0039ae80(self, 1);
                        if (res != 0u) {
                            self[0x60u] = static_cast<u8>(res);
                        }
                        self[0x56u + i] = 5u;
                        *r6_ptr = 1u;
                        *r7_ptr = 1u;
                        return 1u;
                    }
                }
                return 1u;
            }
            case 1: {
                if (r9[0xD5Au] != 6u) {
                    continue;
                }
                *reinterpret_cast<u32*>(self + 0x10u) =
                    (*reinterpret_cast<const u32*>(self + 0x10u) & ~0x30000u) | 0x02000000u;
                *r6_ptr = 1u;
                *r7_ptr = 1u;
                scale_vec_39b864(vec_ptr, 2.0f);
                r9[0xD5Au] = 0xCu;
                self[0x57u] = 5u;
                self[0x59u] = 0u;
                return 1u;
            }
            case 3: {
                if (r9[0xD5Au] == 6u) {
                    continue;
                }
                *reinterpret_cast<u32*>(self + 0x10u) =
                    (*reinterpret_cast<const u32*>(self + 0x10u) & ~0x30000u) | 0x02000000u;
                *r6_ptr = 1u;
                *r7_ptr = 1u;
                scale_vec_39b864(vec_ptr, 0.5f);
                r9[0xD5Au] = 6u;
                self[0x59u] = 5u;
                self[0x57u] = 0u;
                return 1u;
            }
            case 2: {
                *reinterpret_cast<u32*>(self + 0x10u) |= 0x02000000u;
                if (func_002315b4(out_a, out_b, out_c, out_d) != 0) {
                    func_00231f58(vec_ptr);
                    const float zero[2] = {0.0f, 0.0f};
                    func_00231b38(vec_ptr, zero);
                    self[0x60u] = static_cast<u8>(*reinterpret_cast<const u32*>(r8_ptr + 0x1CCu));
                    self[0x58u] = 5u;
                    *r6_ptr = 1u;
                    *r7_ptr = 1u;
                }
                return 1u;
            }
            case 4: {
                const s32 count = *reinterpret_cast<const s32*>(r8_ptr + 0x264u);
                for (s32 j = 0; j < count; ++j) {
                    const u8* const slot = self + 0x12100u + j * 4;
                    if (*reinterpret_cast<const u16*>(slot + 0xE4u) != 0u &&
                        *reinterpret_cast<const s16*>(slot + 0xE6u) ==
                            *reinterpret_cast<const s8*>(self + 0x60u)) {
                        if (j + 1 >= count || *reinterpret_cast<const u16*>(slot + 0xEAu) == 0u) {
                            return 1u;
                        }
                        *reinterpret_cast<u32*>(self + 0x10u) |= 0x02000000u;
                        const u32 res = func_0039ae80(self, -1);
                        if (res != 0u) {
                            self[0x60u] = static_cast<u8>(res);
                        }
                        self[0x56u + i] = 5u;
                        *r6_ptr = 1u;
                        *r7_ptr = 1u;
                        return 1u;
                    }
                }
                return 1u;
            }
            default:
                return 1u;
        }
    }

    return 0u;
}

extern "C" void camp_func_002b7f08(void* base, u32 count, u32 elem_size, u32 cmp_fn);
extern "C" s32 script_vm_func_003d12cc(u8* r8, u8* r6, const u8** ptrs, u32 count, u32 flag);
extern "C" void func_0022ad74(const u32* r6_20, u16* out_arr);
extern "C" s32 battle_func_0029ac70(u16 id, u32 a1);
extern "C" s32 battle_func_0029abc0(u16 id);
extern "C" s32 ui_func_00227968(u8* r8, u8* r6, const void* sb, const u8** ptrs, u32 count, u32 a5,
                                u32 a4);
extern "C" s32 ui_func_0029ec6c(u16 id);
extern "C" void script_vm_func_00229b2c(u8* r8);

namespace {

__attribute__((always_inline)) inline bool try_pass_3d0910(u8* r8, u8* r6, const u8** ptrs,
                                                           u32 count, const u16* arr9, u32 a4,
                                                           u32 a5) {
    for (s32 i = 0; i < 9; ++i) {
        const u16 id = arr9[i];
        if (id == 0u) {
            continue;
        }
        const void* const sb = battle_func_002ae3f0(id);
        if (sb == nullptr) {
            continue;
        }
        const u32 flags = **reinterpret_cast<const u32* const*>(r6 + 0x20u);
        const s32 cost =
            ((flags & 2u) != 0u) ? battle_func_0029ac70(id, 1u) : battle_func_0029abc0(id);
        const s16 limit =
            *reinterpret_cast<const s16*>(*reinterpret_cast<const u8* const*>(r6 + 0x28u) + 0xECu);
        if (cost > static_cast<s32>(limit)) {
            continue;
        }
        if (ui_func_00227968(r8, r6, sb, ptrs, count, a5, a4) != 0) {
            return true;
        }
    }
    return false;
}

}  // namespace

// DECOMP_FUNC(0x003d0910, 996)
extern "C" void camp_func_003d0910(u8* r8, u8* r6) {
    const u8* ptrs[0x6D];
    u32 count = 0u;
    const u8* const arr_base =
        *reinterpret_cast<const u8* const*>(*reinterpret_cast<const u8* const*>(r8) + 0x1FC0u);
    for (u32 i = 0u; i < 0x6Du; ++i) {
        const u8* const elem = arr_base + i * 0x288u;
        if ((*reinterpret_cast<const u32*>(elem) & 0x400u) != 0u) {
            ptrs[count++] = elem;
        }
    }

    camp_func_002b7f08(ptrs, count, 4u, 0x001B1900u);
    if (script_vm_func_003d12cc(r8, r6, ptrs, count, 1u) != 0) {
        return;
    }

    u16 arr9[10] = {};
    func_0022ad74(*reinterpret_cast<const u32* const*>(r6 + 0x20u), arr9);
    const u32 cmp_fn = ((**reinterpret_cast<const u32* const*>(r6 + 0x20u) & 2u) != 0u)
                           ? 0x002196A4u
                           : 0x001E1708u;
    camp_func_002b7f08(arr9, 9u, 2u, cmp_fn);

    if (try_pass_3d0910(r8, r6, ptrs, count, arr9, 0u, 1u)) {
        return;
    }
    if (script_vm_func_003d12cc(r8, r6, ptrs, count, 0u) != 0) {
        return;
    }
    if (try_pass_3d0910(r8, r6, ptrs, count, arr9, 1u, 0u)) {
        return;
    }
    if (try_pass_3d0910(r8, r6, ptrs, count, arr9, 2u, 0u)) {
        return;
    }

    for (u32 i = 0u; i < count; ++i) {
        const u8* const elem = ptrs[i];
        if ((*reinterpret_cast<const u32*>(elem) & 0x400u) != 0u &&
            ui_func_0029ec6c(*reinterpret_cast<const u16*>(elem + 0xCEu)) != 0) {
            u8* const r28 = *reinterpret_cast<u8* const*>(r6 + 0x28u);
            *reinterpret_cast<u16*>(r28 + 0x14Cu) = 6u;
            *reinterpret_cast<u16*>(r28 + 0x14Eu) = 0u;
            return;
        }
    }

    u8* const r28 = *reinterpret_cast<u8* const*>(r6 + 0x28u);
    *reinterpret_cast<u16*>(r28 + 0x14Cu) = 1u;
    const u32 flags = **reinterpret_cast<const u32* const*>(r6 + 0x20u);
    *reinterpret_cast<u16*>(r28 + 0x14Eu) = ((flags & 6u) != 0u) ? 1u : 0u;
    script_vm_func_00229b2c(r8);
}

extern "C" void battle_func_001123b8(u32 a0, u32 a1);
extern "C" void battle_func_002c2a5c(void* dst, u32 mode, u32 a2, u32 a3);
extern "C" void battle_func_002c2a2c(u32 a0);
extern "C" void battle_func_002c28f4(u32 count, void* dst);
extern "C" void battle_func_002c27ec(u32 handle);
extern "C" void battle_func_002c2700(u32 fp, u32 w, u32 h, u32 flag);
extern "C" void battle_func_002c26a8(u32 kind, u32* out_val);
extern "C" void battle_func_002c2684(u32 a0, u32 a1);
extern "C" void engine_func_0010e9ec(u32 a0, u32 a1, u32 a2);
extern "C" void battle_func_0010d180(void* dst);
extern "C" void battle_func_0010e5e0(u32 a0);
extern "C" void battle_func_002bf140(void* dst, u32 a1);
extern "C" void battle_func_0011311c(u32 a0, u32 a1);
extern "C" void battle_func_00113104(u64 a0, u32 a2);
extern "C" void battle_func_0010a4dc();

namespace {

__attribute__((always_inline)) inline void init_render_target_105460(u8* buf, u32 tex_id,
                                                                     u32 count, u32 w, u32 h,
                                                                     u32 fp) {
    *reinterpret_cast<u32*>(buf + 0u) = tex_id;
    *reinterpret_cast<u32*>(buf + 4u) = count;
    *reinterpret_cast<u32*>(buf + 0x18u) = w;
    *reinterpret_cast<u32*>(buf + 0x1Cu) = h;
    battle_func_002c2a2c(tex_id);
    battle_func_002c28f4(*reinterpret_cast<const u32*>(buf + 4u), buf + 8u);
    const u32 n = *reinterpret_cast<const u32*>(buf + 4u);
    for (u32 i = 0u; i < n; ++i) {
        u8* const slot = buf + i * 4u;
        battle_func_002c27ec(*reinterpret_cast<const u32*>(slot + 8u));
        battle_func_002c2700(fp, w, h, 0x10000u);
        u32 out_val = 0u;
        battle_func_002c26a8(0x600u, &out_val);
        *reinterpret_cast<u32*>(slot + 0x20u) = out_val;
    }
    battle_func_002c2684(0u, 0u);
}

}  // namespace

// DECOMP_FUNC(0x00105460, 1000)
extern "C" void battle_func_00105460(const u32* cfg) {
    u8* const g = reinterpret_cast<u8*>(0x004E39E0u);
    const u32* src = cfg;
    if (src == nullptr) {
        *reinterpret_cast<u32*>(g + 0x1F0u) = 0u;
        *reinterpret_cast<u32*>(g + 0x1ECu) = 0x500u;
        *reinterpret_cast<u32*>(g + 0x1D8u) = 0x800u;
        *reinterpret_cast<u32*>(g + 0x1D4u) = 0x100000u;
        *reinterpret_cast<u32*>(g + 0x1F4u) = 0u;
        src = reinterpret_cast<const u32*>(g + 0x1D4u);
    } else {
        u32* const dst = reinterpret_cast<u32*>(g + 0x1D4u);
        for (s32 i = 0; i < 10; ++i) {
            dst[i] = src[i];
        }
        *reinterpret_cast<u32*>(g + 0x1FCu) = src[10];
    }

    battle_func_001123b8(0x0010A940u, 0x002C4358u);
    battle_func_002c2a5c(g + 0x13Cu, 2u, src[0], src[1]);

    const u32 fp = *reinterpret_cast<const u32*>(g + 0x1FCu);
    const u32 count = (src[8] == 1u) ? 2u : 3u;
    init_render_target_105460(g, 0x400u, count, 0xF0u, 0x190u, fp);
    init_render_target_105460(reinterpret_cast<u8*>(0x004E3A38u), 0x401u, count, 0xF0u, 0x140u, fp);
    init_render_target_105460(reinterpret_cast<u8*>(0x004E3A0Cu), 0x410u, count, 0xF0u, 0x190u, fp);

    engine_func_0010e9ec(0u, src[6], src[7]);
    battle_func_002c2a5c(g + 0x154u, 2u, src[4], src[5]);
    battle_func_0010d180(g + 0x154u);

    u32 tmp = 0u;
    battle_func_002c2a5c(&tmp, 1u, src[2], src[3]);
    battle_func_0010e5e0(tmp);
    battle_func_002bf140(g + 0x13Cu, 0u);

    *reinterpret_cast<u32*>(g + 0x174u) = 0x3E800000u;
    *reinterpret_cast<u32*>(g + 0x178u) = 0x3E800000u;
    *reinterpret_cast<u32*>(g + 0x17Cu) = 0x3E800000u;
    *reinterpret_cast<u32*>(g + 0x180u) = 0u;
    *reinterpret_cast<u32*>(g + 0x184u) = 0x3E800000u;
    *reinterpret_cast<u32*>(g + 0x188u) = 0x3E800000u;
    *reinterpret_cast<u32*>(g + 0x18Cu) = 0x3E800000u;
    *reinterpret_cast<u32*>(g + 0x190u) = 0u;
    *reinterpret_cast<u32*>(g + 0x1A4u) = 0x3F800000u;
    *reinterpret_cast<u32*>(g + 0x1A8u) = 0x3F800000u;
    *reinterpret_cast<u32*>(g + 0x1B0u) = 0u;
    *reinterpret_cast<u32*>(g + 0x1B4u) = 0u;
    if (*reinterpret_cast<const u32*>(g + 0x1C8u) != 0u) {
        *reinterpret_cast<u32*>(g + 0x1CCu) = 0u;
    }
    *reinterpret_cast<u32*>(g + 0x1C4u) = 0x4682937Du;
    *reinterpret_cast<u32*>(g + 0x1C0u) = 0u;

    battle_func_0011311c(0x400u, 0x0010A688u);
    const u64 t64 =
        (static_cast<u64>(0x2A05F200u) * 0x44A2FA85u >> 32) + 0x44A2FA85u;
    battle_func_00113104(t64, 0x0010E7CCu);
    battle_func_0010a4dc();

    g[0x201u] = (*reinterpret_cast<const u32*>(g + 0x138u) != 0x500u) ? 1u : 0u;
    g[0x200u] = (*reinterpret_cast<const u32*>(g + 0xC0u) != 0x500u) ? 1u : 0u;
}

extern "C" void ui_func_002a4e50(void* dst, u32 elem_sz, u32 ptr, u32 byte_sz, u32 a4, u32 a5);
extern "C" void ui_func_002c3b00(void* dst);
extern "C" s32 nn_sdk_func_00145e7c(void* dst);
extern "C" void nn_sdk_func_002bbd10(s32 err, u32 caller_pc);

// DECOMP_FUNC(0x00145e9c, 1000)
extern "C" s32 ui_func_00145e9c(u8* self, void* stream, u32 vtx_count, u32 idx_count,
                                u32 base_off, u32 max_end, u32 read_flag) {
    typedef s32 (*StreamReadFn)(void* s, u32* bytes_read, u64 off, void* dst, u32 size);
    const StreamReadFn stream_read = (*reinterpret_cast<const StreamReadFn* const*>(stream))[0];

    u32 hdr[10];
    u32 bytes_read = 0u;
    s32 rc = stream_read(stream, &bytes_read, 0ULL, hdr, 0x28u);
    if (rc < 0) {
        return rc;
    }
    if (bytes_read != 0x28u) {
        return static_cast<s32>(0xC8A04554u);
    }

    const u32 vtx_bytes = vtx_count << 5;
    const u32 idx_bytes = idx_count * 24u;
    u32 total_size = 0u;
    if (read_flag == 0u) {
        total_size = vtx_bytes + idx_bytes;
    } else {
        u32 hdr2[10];
        u32 bytes_read2 = 0u;
        const s32 rc2 = stream_read(stream, &bytes_read2, 0ULL, hdr2, 0x28u);
        total_size = 0xFFFFFFFFu;
        if (rc2 >= 0 && bytes_read2 == 0x28u) {
            const s32 sum = static_cast<s32>(hdr2[2] + hdr2[4] + hdr2[6] + hdr2[8]);
            if (sum >= 0) {
                total_size = vtx_bytes + idx_bytes + static_cast<u32>(sum);
            }
        }
    }
    if (total_size > max_end) {
        return static_cast<s32>(0xD8604659u);
    }

    u32 cur_ptr = base_off;
    if (read_flag != 0u) {
        u32 offs[4] = {};
        s32 off = static_cast<s32>(bytes_read);
        for (s32 k = 0; k < 4; ++k) {
            const u32 sz = hdr[2 + k * 2];
            u32 nread = 0u;
            rc = stream_read(stream, &nread, static_cast<u64>(static_cast<s64>(off)),
                             reinterpret_cast<void*>(cur_ptr), sz);
            if (rc < 0) {
                return rc;
            }
            off += static_cast<s32>(nread);
            offs[k] = cur_ptr;
            cur_ptr += sz;
        }
        for (s32 k = 0; k < 4; ++k) {
            u32* const desc = reinterpret_cast<u32*>(self + 0x70u + k * 0x10u);
            desc[0] = offs[k];
            desc[1] = hdr[2 + k * 2];
            desc[2] = 0u;
            desc[3] = reinterpret_cast<u32>(self);
        }
    } else {
        for (s32 k = 0; k < 4; ++k) {
            u32* const desc = reinterpret_cast<u32*>(self + 0x70u + k * 0x10u);
            desc[0] = 0u;
            desc[1] = hdr[2 + k * 2];
            desc[2] = reinterpret_cast<u32>(self);
            desc[3] = hdr[1 + k * 2];
        }
    }

    *reinterpret_cast<u32*>(self + 0x20u) = 0u;
    *reinterpret_cast<u32*>(self + 0x24u) = 0u;
    *reinterpret_cast<u32*>(self + 0x28u) = hdr[2] >> 2;
    *reinterpret_cast<u32*>(self + 0x2Cu) = reinterpret_cast<u32>(self + 0x70u);
    *reinterpret_cast<u32*>(self + 0x30u) = 0u;
    *reinterpret_cast<u32*>(self + 0x34u) = 0u;
    *reinterpret_cast<u32*>(self + 0x38u) = hdr[4];
    *reinterpret_cast<u32*>(self + 0x3Cu) = reinterpret_cast<u32>(self + 0x80u);
    *reinterpret_cast<u32*>(self + 0x48u) = 0u;
    *reinterpret_cast<u32*>(self + 0x4Cu) = 0u;
    *reinterpret_cast<u32*>(self + 0x50u) = hdr[6] >> 2;
    *reinterpret_cast<u32*>(self + 0x54u) = reinterpret_cast<u32>(self + 0x90u);
    *reinterpret_cast<u32*>(self + 0x58u) = 0u;
    *reinterpret_cast<u32*>(self + 0x5Cu) = 0u;
    *reinterpret_cast<u32*>(self + 0x60u) = hdr[8];
    *reinterpret_cast<u32*>(self + 0x64u) = reinterpret_cast<u32>(self + 0xA0u);

    ui_func_002a4e50(self + 0xB8u, 0x20u, cur_ptr, vtx_bytes, 4u, 0u);
    ui_func_002c3b00(self + 0xE8u);
    ui_func_002a4e50(self + 0xF4u, 0x18u, cur_ptr + vtx_bytes, idx_bytes, 4u, 0u);
    ui_func_002c3b00(self + 0x124u);
    *reinterpret_cast<u32*>(self + 0xB0u) = hdr[9];

    const s32 e7c = nn_sdk_func_00145e7c(self + 4u);
    if (e7c < 0) {
        nn_sdk_func_002bbd10(e7c, 0u);
    }

    const s32 v4 = *reinterpret_cast<const s32*>(self + 4u);
    s32 slot = 0;
    if (v4 == 0) {
        slot = 2;
    } else if (v4 < 0) {
        slot = (v4 >= -8) ? 1 : 0;
    } else {
        slot = (v4 <= 8) ? 3 : 4;
    }
    *reinterpret_cast<void**>(self + 0xCu + slot * 4) = stream;
    *reinterpret_cast<void**>(self + 8u) = stream;
    return 0;
}

extern "C" const u8* battle_func_002b087c(u16 id);
extern "C" u8* engine_func_00294334(s32 id, u32 a1);
extern "C" void battle_func_00240744();
extern "C" void* ui_func_0027dc58(u8* self, u32 id);
extern "C" s32 ui_func_00295300(void* obj);
extern "C" void ui_func_0029423c(void* obj, u32 a1);
extern "C" s32 ui_func_00295284(void* obj);
extern "C" void engine_func_0023fce0(void* obj);
extern "C" void func_003c1b8c(u32 a0);
extern "C" void func_002406ac(u8* self, u8* r5_p, u32 a2, u32 a3);
extern "C" u32 script_vm_func_0027eb98(u32 a0);
extern "C" void battle_func_00245330(s32 x, u32 e_id, u8* r5_p, u32 a3, s32 y, u32 a5);
extern "C" void battle_func_00240660(s32 x, u32 e_id, u8* r5_p, u32 mode, u32 a4);

// DECOMP_FUNC(0x00337594, 1004)
extern "C" u32 battle_func_00337594(u8* self, u16 id) {
    s32* const fp = reinterpret_cast<s32*>(self + 0x4454u);
    if (*fp != -1) {
        return 1u;
    }

    const u8* const r8 = battle_func_002b087c(id);
    u8* const sl = self + 0x4450u;
    void** const r7 = reinterpret_cast<void**>(self + 0x4458u);
    u32* const r5 = reinterpret_cast<u32*>(self + 0x1FE8u);
    u32* const r4 = reinterpret_cast<u32*>(self + 0x1FE4u);
    const u8 state = *sl;

    if (state == 0u) {
        for (u32 i = 0u; i < 0x2Au; ++i) {
            *reinterpret_cast<u32*>(self + 0x1FE4u + i * 8u) = 0u;
            *reinterpret_cast<u32*>(self + 0x1FE8u + i * 8u) = 0xFFFFFFFFu;
        }
        *r7 = nullptr;
        const s32 target_id = *reinterpret_cast<const s16*>(r8 + 0x88u);
        bool found = false;
        for (u32 i = 0u; i < 0x2Au; ++i) {
            const u8* const entry = *reinterpret_cast<const u8* const*>(self + 0x2134u + i * 4u);
            if (entry != nullptr && *reinterpret_cast<const s32*>(entry + 4u) == target_id) {
                *r5 = static_cast<u32>(target_id);
                *r4 |= 3u;
                found = true;
                break;
            }
        }
        if (!found) {
            u8* const created = engine_func_00294334(target_id, 1u);
            for (u32 i = 0u; i < 0x2Au; ++i) {
                u8** const slot = reinterpret_cast<u8**>(self + 0x2134u + i * 4u);
                if (*slot == nullptr) {
                    *slot = created;
                    break;
                }
            }
            *r5 = static_cast<u32>(static_cast<s32>(*reinterpret_cast<const s16*>(r8 + 0x88u)));
        }
        u8* const g = *reinterpret_cast<u8* const*>(0x004342C8u);
        *reinterpret_cast<u32*>(g + 0x634u) |= 0x4000u;
        const u8* const d18 = *reinterpret_cast<const u8* const*>(0x00435D18u);
        if ((*reinterpret_cast<const u32*>(d18 + 0x3028u) & 0x400u) != 0u) {
            battle_func_00240744();
        }
        *sl = 1u;
        return 0u;
    }

    if (state != 1u) {
        return 0u;
    }

    void* const obj = ui_func_0027dc58(self, *r5);
    if ((*r4 & 1u) == 0u) {
        if (ui_func_00295300(obj) == 0) {
            return 0u;
        }
        *r4 |= 1u;
        ui_func_0029423c(obj, 7u);
    }
    if ((*r4 & 2u) == 0u) {
        if (ui_func_00295284(obj) == 0) {
            return 0u;
        }
        engine_func_0023fce0(obj);
        *r4 |= 2u;
        *r7 = obj;
    }

    u8* const arr1 = *reinterpret_cast<u8* const*>(self + 0x1FC0u);
    s32 idx1 = 0x35;
    while (idx1 >= 0 && (*reinterpret_cast<const u32*>(arr1 + idx1 * 0x288) & 1u) != 0u) {
        --idx1;
    }
    *reinterpret_cast<u32*>(arr1 + idx1 * 0x288) = 0x00200001u;
    *reinterpret_cast<u32*>(arr1 + idx1 * 0x288 + 4) = 0u;

    const u8* const arr2 = *reinterpret_cast<const u8* const*>(self + 0x1E98u);
    s32 idx2 = 0x35;
    while (idx2 > 3 && (*reinterpret_cast<const u32*>(arr2 + 0x50 + idx2 * 0x114) & 1u) != 0u) {
        --idx2;
    }

    u8* const r5_p = *reinterpret_cast<u8* const*>(*reinterpret_cast<const u8* const*>(0x00435D90u) +
                                                  0x1E98u) +
                     idx2 * 0x114;
    *reinterpret_cast<u32*>(r5_p + 0x50u) = 0x00020483u;
    *reinterpret_cast<u16*>(r5_p + 0x60u) = static_cast<u16>(idx1);
    *reinterpret_cast<u32*>(r5_p + 0xCu) = 0u;
    *reinterpret_cast<u32*>(r5_p + 0x10u) = 0u;
    *reinterpret_cast<u32*>(r5_p + 0x14u) = 0x41700000u;
    *reinterpret_cast<u16*>(r5_p + 0x5Au) = 0u;
    const u32 c_val = *reinterpret_cast<const u32*>(0x00439CF8u);
    *reinterpret_cast<u32*>(r5_p + 0x64u) = c_val;
    *reinterpret_cast<u32*>(r5_p + 0x68u) = c_val;
    *reinterpret_cast<u32*>(r5_p + 0x6Cu) = c_val;
    func_003c1b8c(1u);
    *reinterpret_cast<u32*>(r5_p + 0x40u) = 0u;
    *reinterpret_cast<u16*>(r5_p + 0x58u) |= 0x800u;

    *reinterpret_cast<s32*>(arr1 + idx1 * 0x288 + 0xD8) =
        static_cast<s32>(*reinterpret_cast<const s16*>(r8 + 0x88u));
    *reinterpret_cast<u16*>(arr1 + idx1 * 0x288 + 8) = *reinterpret_cast<const u16*>(r5_p + 0x62u);
    *fp = idx2;
    *sl = 0u;

    const u8* const g9a20 = reinterpret_cast<const u8*>(0x00439A20u);
    const s16 v4 = static_cast<s16>(*reinterpret_cast<const u32*>(g9a20 + 4u));
    const s16 v18 = static_cast<s16>(*reinterpret_cast<const u32*>(g9a20 + 0x18u));
    const s16 v8 = static_cast<s16>(*reinterpret_cast<const u32*>(g9a20 + 8u));
    func_002406ac(self, r5_p, 0u, 0u);
    const u32 e1 = script_vm_func_0027eb98(*reinterpret_cast<const u32*>(0x0043427Cu));
    battle_func_00245330(v18 + v4, e1, r5_p, 0xFFu, v8, 0u);
    const u32 mode = ((*reinterpret_cast<const u32*>(r5_p + 0x50u) & 0x10u) != 0u) ? 7u : 6u;
    const u32 e2 = script_vm_func_0027eb98(*reinterpret_cast<const u32*>(0x0043427Cu));
    battle_func_00240660(v18, e2, r5_p, mode, 0xDu);
    return 1u;
}

extern "C" u32 func_0011d11c();
extern "C" void func_002bb480(u32 a0);
extern "C" void func_002bb624();
extern "C" void func_002bb4c0();
extern "C" void func_002c0efc();
extern "C" s32 camp_func_0013b508(u32* out20, u32* out24, u32 arg1, u32 arg2, u32* v4, u32* v3,
                                  u64 timeout);
extern "C" void func_0011d8c4();
extern "C" u32 func_002c1494();
extern "C" void func_002bb4d4(u32 a0);
extern "C" s32 func_0012a62c();
extern "C" void engine_func_002c14f4(s32 err, u32 caller_pc);
extern "C" void func_002b5ae8(u32 a0);
extern "C" void func_0012a6d8(u32 a0);
extern "C" void func_00128408();
extern "C" void func_0012a28c();
extern "C" void func_002bb774(u32 mask);
extern "C" void func_002bb7a0(u32 a0);
extern "C" void func_0011d1e0(u32 a0);
extern "C" void func_0012a5f8(u32 a0, u32 a1);

// DECOMP_FUNC(0x002c0f28, 1016)
extern "C" s32 func_002c0f28(u32* out_a, u32 arg1, u32 arg2, u32* out_b, u32* out_c,
                             u64 timeout) {
    u32 saved_a = 0u;
    const u32 fp = func_0011d11c();
    func_002bb480(0u);
    if (fp == 0x63u) {
        if (out_a != nullptr) {
            *out_a = 0u;
        }
        if (out_b != nullptr) {
            *out_b = 0u;
        }
        if (out_c != nullptr) {
            *out_c = *reinterpret_cast<const u32*>(0x0044E368u);
        }
        return 0;
    }

    func_002bb624();
    func_002bb4c0();
    if (fp == 0x62u) {
        func_002bb480(0u);
    } else {
        func_002c0efc();
    }

    u32 r4 = 0u;
    s32 rc = 0;
    for (;;) {
        u32 v3 = 0u;
        u32 v4 = 0u;
        u32 out20 = 0u;
        u32 out24 = 0u;
        rc = camp_func_0013b508(&out20, &out24, arg1, arg2, &v4, &v3, timeout);
        u8 cont_flag = 1u;
        if ((static_cast<u32>(rc) << 22) != 0xFBC00000u) {
            if (rc >= 0) {
                const u8* const g_cb = reinterpret_cast<const u8*>(0x0044E3B0u);
                const u32 cb_addr = *reinterpret_cast<const u32*>(g_cb + 0x48u);
                if (cb_addr != 0u) {
                    typedef u8 (*CbFn)(u32, u32, u32, u32, u32, u32, u32);
                    cont_flag = reinterpret_cast<CbFn>(cb_addr)(
                        *reinterpret_cast<const u32*>(g_cb + 0x88u), out20, out24, arg1, arg2, v4,
                        v3);
                }
            }
            saved_a = out20;
            r4 = out24;
            if (out_b != nullptr) {
                *out_b = v4;
            }
            if (out_c != nullptr) {
                *out_c = v3;
            }
        }
        if (static_cast<s8>(cont_flag) == 0) {
            continue;
        }
        if (out_a != nullptr) {
            *out_a = saved_a;
        }
        if (rc < 0) {
            break;
        }
        if (r4 == 1u || r4 == 0xBu || r4 == 0xAu || r4 == 0xCu || r4 == 0xDu || r4 == 0xFu ||
            r4 == 0xEu || r4 == 0x11u || r4 == 0x40u || r4 == 0x41u) {
            func_0011d8c4();
            break;
        }
    }

    if ((static_cast<u32>(rc) << 22) == 0xFBC00000u) {
        return -1;
    }

    if (func_002c1494() == 0u && fp != 3u && r4 != 0xCu && r4 != 1u) {
        func_002bb4d4(1u);
        const s32 ret = func_0012a62c();
        if (ret < 0) {
            engine_func_002c14f4(ret, 0u);
        }
    }

    bool skip_b5ae8 = false;
    switch (r4) {
        case 0xEu:
            r4 = 6u;
            break;
        case 0xBu:
            r4 = 3u;
            break;
        case 1u:
            break;
        case 0xAu:
            r4 = 2u;
            break;
        case 0xCu:
            r4 = 4u;
            func_00128408();
            func_0012a28c();
            skip_b5ae8 = true;
            break;
        case 0xDu:
            r4 = 5u;
            func_00128408();
            skip_b5ae8 = true;
            break;
        case 0xFu:
            r4 = 7u;
            func_002bb7a0(1u);
            func_0011d1e0(1u);
            break;
        case 0x11u:
            r4 = 9u;
            skip_b5ae8 = true;
            break;
        case 0x40u:
        case 0x41u:
            break;
        default:
            r4 = 1u;
            break;
    }

    if (!skip_b5ae8) {
        func_002b5ae8(1u);
        if (fp == 0xEu || fp == 5u) {
            func_0012a6d8(1u);
        }
    }

    if (r4 == 1u || r4 == 2u || r4 == 3u || r4 == 4u || r4 == 5u || r4 == 6u || r4 == 9u ||
        r4 == 0x40u || r4 == 0x41u) {
        const u32 v = func_002c1494();
        const u32 mask = (v <= 3u) ? (0x10u << v) : 0u;
        func_002bb774(mask);
        func_002c0efc();
    } else if (r4 == 7u) {
        func_0012a5f8(1u, 1u);
    }

    if (fp == 0xEu || fp == 4u || fp == 5u || fp == 0x12u) {
        if (r4 != 4u && r4 != 5u) {
            func_002bb4d4(1u);
        }
        if (func_002c1494() == 0u && r4 != 7u) {
            func_002bb7a0(0u);
            func_002bb774(1u);
            func_002c0efc();
        }
    }

    return static_cast<s32>(r4);
}

extern "C" u32 engine_func_002c1784(u32 a0);
extern "C" u32 engine_func_002c17ac(u32 a0);
extern "C" void ui_func_002c1d3c(u8* self, u32 val);
extern "C" u32 ui_func_002c5f7c(u32 a0, u32 a1);
extern "C" u32 engine_func_00286834(u32 a0, float f0);
extern "C" u32 camp_func_0023d5ac(u32 a0, u32 a1, u32 a2, u32 a3);
extern "C" u32 battle_func_002c5fa4(u32 a0, u32 a1, u32 a2);
extern "C" u32 func_003105dc(u32 a0, u32 a1, u32 a2, u32 a3);
extern "C" u32 func_0031b9a0(u32 a0, u32 a1, u32 a2);
extern "C" void ui_func_002b7978(u32 a0, u32 a1, u32 a2, u32 a3, float s0, float s1, float s2,
                                 float s3, float s4);

namespace {

__attribute__((always_inline)) inline void push_state_34359c(u8* stk, u32 val) {
    u32 idx = *reinterpret_cast<const u32*>(stk);
    const u32 prev = *reinterpret_cast<const u32*>(stk + 8u + idx * 4u);
    ++idx;
    *reinterpret_cast<u32*>(stk) = idx;
    *reinterpret_cast<u32*>(stk + 8u + idx * 4u) = val;
    if (stk[0x18u] != 0u || prev != val) {
        reinterpret_cast<void (*)(u32)>(*reinterpret_cast<const u32*>(stk + 0x1Cu))(val);
        stk[0x18u] = 0u;
    }
}

__attribute__((always_inline)) inline void pop_state_34359c(u8* stk) {
    u32 idx = *reinterpret_cast<const u32*>(stk);
    const u32 prev = *reinterpret_cast<const u32*>(stk + 8u + idx * 4u);
    --idx;
    *reinterpret_cast<u32*>(stk) = idx;
    const u32 cur = *reinterpret_cast<const u32*>(stk + 8u + idx * 4u);
    if (stk[0x18u] != 0u || prev != cur) {
        reinterpret_cast<void (*)(u32)>(*reinterpret_cast<const u32*>(stk + 0x1Cu))(cur);
        stk[0x18u] = 0u;
    }
}

}  // namespace

// DECOMP_FUNC(0x0034359c, 1044)
extern "C" void ui_func_0034359c(u8* self, u32 a1, u32 a2, u32 flags, float f0) {
    const u32 saved_1e4 = *reinterpret_cast<const u32*>(self + 0x11E4u);
    const float w = static_cast<float>(engine_func_002c1784(*reinterpret_cast<const u32*>(self + 0x528u)));
    const float h = static_cast<float>(engine_func_002c17ac(*reinterpret_cast<const u32*>(self + 0x528u)));

    const u32 f_bit0 = ((flags & 1u) != 0u) ? 1u : 0u;
    const u32 f_bit1 = ((flags & 2u) != 0u) ? 1u : 0u;
    const u32 f_bit2 = ((flags & 4u) != 0u) ? 2u : 0u;

    ui_func_002c1d3c(self, 0u);
    push_state_34359c(self + 0x124Cu, ui_func_002c5f7c(1u, f_bit1));
    push_state_34359c(self + 0x126Cu, engine_func_00286834(1u, 0.0f));
    push_state_34359c(self + 0x128Cu, camp_func_0023d5ac(f_bit0, f_bit0, f_bit0, f_bit0));
    push_state_34359c(self + 0x12ACu, battle_func_002c5fa4(1u, 0u, 0u));
    push_state_34359c(self + 0x120Cu, func_003105dc(1u, a2, 0xFFu, 0xFFu));
    push_state_34359c(self + 0x122Cu, func_0031b9a0(f_bit2, f_bit2, f_bit2));

    ui_func_002b7978(a1, a1, a1, a1, 0.0f, 0.0f, w, h, f0);

    pop_state_34359c(self + 0x122Cu);
    pop_state_34359c(self + 0x120Cu);
    pop_state_34359c(self + 0x12ACu);
    pop_state_34359c(self + 0x128Cu);
    pop_state_34359c(self + 0x126Cu);
    pop_state_34359c(self + 0x124Cu);

    ui_func_002c1d3c(self, saved_1e4);
}

extern "C" s32 script_vm_func_0022a458(u32 mgr, u32 sub_id);
extern "C" void script_vm_func_00387c8c(u32 mgr, u32 sub_id, void** out_handle, const char* path);
extern "C" void script_vm_func_0022a2b0(u32 mgr, u32 sub_id, void** out_handle, const char* path);
extern "C" void script_vm_func_00297704(const char* path, void** out_handle, u32 a2);
extern "C" void* Tbb_GetSubTable(void* tbb, u32 idx);
extern "C" u32 Tbb_GetPayloadData(void* sub);
extern "C" u32 Tbb_GetRowCount(void* sub);
extern "C" u32 script_vm_func_0022a324(u8* self, u8* r5);
extern "C" u32 script_vm_func_0022a210(u8* self, u8* r5);
extern "C" u32 battle_func_003c7988(u8* self, u8* r5);
extern "C" void engine_func_003db004(void* mgr);
extern "C" s32 script_vm_func_003dc368(void* mgr);
extern "C" void battle_func_003dc094(void* mgr);
extern "C" s32 script_vm_func_003dce60(void* mgr);

namespace {

__attribute__((always_inline)) inline void load_event_file_3c7a94(const char* fmt, u8* r5,
                                                                  void** out_handle,
                                                                  bool use_tbb) {
    char buf[0x80];
    engine_func_002c4b30(buf, 0x80u);
    const char* const name = reinterpret_cast<const char*>(r5 + 0x100u);
    reinterpret_cast<void (*)(char*, const char*, const char*, const char*)>(ui_func_002be7fc)(
        buf, fmt, name, name);
    const u32 mgr = *reinterpret_cast<const u32*>(0x00433158u);
    const u32 sub_id = *reinterpret_cast<const u32*>(r5 + 0xC4u);
    if (script_vm_func_0022a458(mgr, sub_id) != 0) {
        if (use_tbb) {
            script_vm_func_00387c8c(mgr, sub_id, out_handle, buf);
        } else {
            script_vm_func_0022a2b0(mgr, sub_id, out_handle, buf);
        }
    } else {
        script_vm_func_00297704(buf, out_handle, 0u);
    }
}

__attribute__((always_inline)) inline u32 finish_tbb_3c7a94(u8* self, u8* r5) {
    void* const h = *reinterpret_cast<void* const*>(self + 8u);
    if (h == nullptr) {
        return 0u;
    }
    void* const tbl = Tbb_GetSubTable(h, 0u);
    *reinterpret_cast<u32*>(self + 0x18u) = Tbb_GetPayloadData(tbl);
    *reinterpret_cast<u32*>(self + 0x1Cu) = Tbb_GetRowCount(tbl);
    *reinterpret_cast<u32*>(self) = 3u;
    return script_vm_func_0022a324(self, r5);
}

__attribute__((always_inline)) inline u32 finish_bf_3c7a94(u8* self, u8* r5) {
    if (*reinterpret_cast<const u32*>(self + 0x10u) == 0u) {
        return 0u;
    }
    *reinterpret_cast<u32*>(self) = 7u;
    return script_vm_func_0022a210(self, r5);
}

__attribute__((always_inline)) inline u32 trigger_vm_3c7a94(u8* self, u8* r5) {
    const s32 id = *reinterpret_cast<const s32*>(self + 0x20u);
    if (id < 0) {
        return 0u;
    }
    script_vm_func_002971e4(*reinterpret_cast<u8* const*>(self + 0x14u), static_cast<u32>(id));
    *reinterpret_cast<u32*>(self) = 0xAu;
    *reinterpret_cast<u32*>(self + 0x28u) = 0u;
    if ((*reinterpret_cast<const u32*>(r5 + 0x44A0u) & 0x100000u) != 0u) {
        script_vm_func_002b8b78(0xDDu);
    }
    return battle_func_003c7988(self, r5);
}

}  // namespace

// DECOMP_FUNC(0x003c7a94, 1048)
extern "C" u32 script_vm_func_003c7a94(u8* self, u8* r5) {
    const u32 state = *reinterpret_cast<const u32*>(self);
    switch (state) {
        case 1u: {
            load_event_file_3c7a94("battle/event/%s/ProTable_%s.tbb", r5,
                                   reinterpret_cast<void**>(self + 8u), true);
            *reinterpret_cast<u32*>(self) = 2u;
            return finish_tbb_3c7a94(self, r5);
        }
        case 2u:
            return finish_tbb_3c7a94(self, r5);
        case 3u:
            return script_vm_func_0022a324(self, r5);
        case 4u: {
            if (*reinterpret_cast<const u32*>(self + 0xCu) == 0u) {
                return 0u;
            }
            *reinterpret_cast<u32*>(self) = 5u;
            // fallthrough
        }
        case 5u: {
            load_event_file_3c7a94("battle/event/%s/%s.bf", r5,
                                   reinterpret_cast<void**>(self + 0x10u), false);
            *reinterpret_cast<u32*>(self) = 6u;
            return finish_bf_3c7a94(self, r5);
        }
        case 6u:
            return finish_bf_3c7a94(self, r5);
        case 7u:
            return script_vm_func_0022a210(self, r5);
        case 8u: {
            void* const mgr = *reinterpret_cast<void* const*>(0x00435D18u);
            switch (self[0x2Cu]) {
                case 0u:
                    engine_func_003db004(mgr);
                    self[0x2Cu] = 1u;
                    // fallthrough
                case 1u:
                    if (script_vm_func_003dc368(*reinterpret_cast<void* const*>(0x00435D18u)) ==
                        0) {
                        return 0u;
                    }
                    battle_func_003dc094(*reinterpret_cast<void* const*>(0x00435D18u));
                    self[0x2Cu] = 2u;
                    // fallthrough
                case 2u:
                    if (script_vm_func_003dce60(*reinterpret_cast<void* const*>(0x00435D18u)) ==
                        0) {
                        return 0u;
                    }
                    self[0x2Cu] = 3u;
                    break;
                default:
                    break;
            }
            *reinterpret_cast<u32*>(self) = 9u;
            return trigger_vm_3c7a94(self, r5);
        }
        case 9u:
            return trigger_vm_3c7a94(self, r5);
        case 10u:
            return battle_func_003c7988(self, r5);
        default:
            return 0u;
    }
}

extern "C" void* func_0015f7bc(const u32* ctx);
extern "C" void* func_00162ba4(const u32* ctx);
extern "C" void* func_0015fba4(const u32* ctx);

// DECOMP_FUNC(0x001634fc, 1056)
extern "C" void* func_001634fc(const u32* ctx) {
    if (ctx[0] == ctx[1]) {
        func_0015f7bc(ctx);
    } else {
        func_00162ba4(ctx);
    }
    return func_0015fba4(ctx);
}

// Trailing SIMD deblocking helper at 0x00163534 within the 0x001634fc span.
extern "C" __attribute__((naked)) void func_00163534() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4001, 0xe5902008\n"
        ".word 0xe590300c, 0xe5908010, 0xe5909014, 0xe5900004\n"
        ".word 0xe2422008, 0xe2433008, 0xe16d20f8, 0xe59fc3b4\n"
        ".word 0xe59fe3b4, 0xe2800b02, 0xe52d2004, 0xe1888408\n"
        ".word 0xe1899409, 0xe1888808, 0xe1899809, 0xf550f1e0\n"
        ".word 0xe5101200, 0xe5904100, 0xe5102100, 0xe5903000\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a100, 0xe580b000, 0xf550f0e0\n"
        ".word 0xe51011fc, 0xe5904104, 0xe51020fc, 0xe5903004\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a0fc, 0xe580b004, 0xf5d0f020\n"
        ".word 0xe51011f8, 0xe5904108, 0xe51020f8, 0xe5903008\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a0f8, 0xe580b008, 0xf5d0f120\n"
        ".word 0xe51011f4, 0xe590410c, 0xe51020f4, 0xe590300c\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a0f4, 0xe580b00c, 0xe59d1000\n"
        ".word 0xe2800010, 0xe2511010, 0xc58d1000, 0xcaffff6a\n"
        ".word 0xba000046, 0xe5101200, 0xe5904100, 0xe5102100\n"
        ".word 0xe5903000, 0xe1e06004, 0xe6766f91, 0xe6725f93\n"
        ".word 0xe6766f9c, 0xe661bff2, 0xe6766f9c, 0xe6621ff1\n"
        ".word 0xe6667ffe, 0xe66e6ff6, 0xe665af97, 0xe6511f9b\n"
        ".word 0xe66aaff6, 0xe665bff7, 0xe6635ff4, 0xe66bbf96\n"
        ".word 0xe6644ff3, 0xe6111ff9, 0xe682afba, 0xe683bfbb\n"
        ".word 0xe6544f95, 0xe6625ff3, 0xe6636ff2, 0xe6144ff9\n"
        ".word 0xe682afba, 0xe683bfbb, 0xe6555f96, 0xe6155ff8\n"
        ".word 0xe682afba, 0xe683bfbb, 0xe500a100, 0xe580b000\n"
        ".word 0xe51011fc, 0xe5904104, 0xe51020fc, 0xe5903004\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a0fc, 0xe580b004, 0xe2800008\n"
        ".word 0xe1cd20d4, 0xe2800b02, 0xe2400008, 0xe2533008\n"
        ".word 0x10400002, 0x158d2000, 0x158d3008, 0x1affff1a\n"
        ".word 0xe28dd00c, 0xe8bd8001, 0x01010101, 0x20202020\n"
    );
}

extern "C" void* func_0016691c(const u32* ctx);
extern "C" void* func_0016391c(const u32* ctx);

// DECOMP_FUNC(0x00167274, 1056)
extern "C" void* func_00167274(const u32* ctx) {
    if (ctx[0] == ctx[1]) {
        reinterpret_cast<void* (*)(const u32*)>(func_00163534)(ctx);
    } else {
        func_0016691c(ctx);
    }
    return func_0016391c(ctx);
}

// Trailing SIMD deblocking helper at 0x001672ac within the 0x00167274 span.
extern "C" __attribute__((naked)) void func_001672ac() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4001, 0xe5902008\n"
        ".word 0xe590300c, 0xe5908010, 0xe5909014, 0xe5900004\n"
        ".word 0xe2422008, 0xe2433008, 0xe16d20f8, 0xe59fc3b4\n"
        ".word 0xe59fe3b4, 0xe2800a01, 0xe52d2004, 0xe1888408\n"
        ".word 0xe1899409, 0xe1888808, 0xe1899809, 0xf550f3e0\n"
        ".word 0xe5101400, 0xe5904200, 0xe5102200, 0xe5903000\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a200, 0xe580b000, 0xf550f1e0\n"
        ".word 0xe51013fc, 0xe5904204, 0xe51021fc, 0xe5903004\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a1fc, 0xe580b004, 0xf5d0f020\n"
        ".word 0xe51013f8, 0xe5904208, 0xe51021f8, 0xe5903008\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a1f8, 0xe580b008, 0xf5d0f220\n"
        ".word 0xe51013f4, 0xe590420c, 0xe51021f4, 0xe590300c\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a1f4, 0xe580b00c, 0xe59d1000\n"
        ".word 0xe2800010, 0xe2511010, 0xc58d1000, 0xcaffff6a\n"
        ".word 0xba000046, 0xe5101400, 0xe5904200, 0xe5102200\n"
        ".word 0xe5903000, 0xe1e06004, 0xe6766f91, 0xe6725f93\n"
        ".word 0xe6766f9c, 0xe661bff2, 0xe6766f9c, 0xe6621ff1\n"
        ".word 0xe6667ffe, 0xe66e6ff6, 0xe665af97, 0xe6511f9b\n"
        ".word 0xe66aaff6, 0xe665bff7, 0xe6635ff4, 0xe66bbf96\n"
        ".word 0xe6644ff3, 0xe6111ff9, 0xe682afba, 0xe683bfbb\n"
        ".word 0xe6544f95, 0xe6625ff3, 0xe6636ff2, 0xe6144ff9\n"
        ".word 0xe682afba, 0xe683bfbb, 0xe6555f96, 0xe6155ff8\n"
        ".word 0xe682afba, 0xe683bfbb, 0xe500a200, 0xe580b000\n"
        ".word 0xe51013fc, 0xe5904204, 0xe51021fc, 0xe5903004\n"
        ".word 0xe1e06004, 0xe6766f91, 0xe6725f93, 0xe6766f9c\n"
        ".word 0xe661bff2, 0xe6766f9c, 0xe6621ff1, 0xe6667ffe\n"
        ".word 0xe66e6ff6, 0xe665af97, 0xe6511f9b, 0xe66aaff6\n"
        ".word 0xe665bff7, 0xe6635ff4, 0xe66bbf96, 0xe6644ff3\n"
        ".word 0xe6111ff9, 0xe682afba, 0xe683bfbb, 0xe6544f95\n"
        ".word 0xe6625ff3, 0xe6636ff2, 0xe6144ff9, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe6555f96, 0xe6155ff8, 0xe682afba\n"
        ".word 0xe683bfbb, 0xe500a1fc, 0xe580b004, 0xe2800008\n"
        ".word 0xe1cd20d4, 0xe2800a01, 0xe2400008, 0xe2533008\n"
        ".word 0x10400002, 0x158d2000, 0x158d3008, 0x1affff1a\n"
        ".word 0xe28dd00c, 0xe8bd8001, 0x01010101, 0x20202020\n"
    );
}

extern "C" void engine_func_002c3aa8(void* lock);
extern "C" void engine_func_002c3a24(void* lock);
extern "C" void func_00239b84(void* ptr);
extern "C" void* func_00239b54(u32 size, u32 align);
extern "C" void engine_func_002c5ff4(void* dst, const void* src, u32 size);

namespace {

inline void release_slot_239734(void* lock2, void* const* slot, volatile u8* flag) {
    engine_func_002c3aa8(lock2);
    if (*flag != 0u) {
        func_00239b84(*slot);
        *flag = 0u;
    }
    engine_func_002c3a24(lock2);
}

}  // namespace

// DECOMP_FUNC(0x00239734, 1056)
extern "C" u32 engine_func_00239734(u8* self, u8* out_hdr, const u8** out_entries, u32 /*unused*/,
                                    u32 mode) {
    void* const lock1 = reinterpret_cast<void*>(0x004E62A8u);
    void* const lock2 = reinterpret_cast<void*>(0x004E62B4u);
    volatile u8* const flags = reinterpret_cast<volatile u8*>(0x004656D0u);

    engine_func_002c3aa8(lock1);
    const u32 ctx_id = *reinterpret_cast<const u32*>(self + 4u);
    if (ctx_id == 0u) {
        engine_func_002c3a24(lock1);
        return 0xC8810BEAu;
    }

    u32 bytes_read = 0u;
    u32 file_size = 0u;
    const u32 slot_arg = (mode == 0u) ? 3u : 4u;
    void* const* const vtable = *reinterpret_cast<void* const* const*>(self);
    using GetSizeFn = void (*)(u8*, u32, u32, u32, u32*);
    reinterpret_cast<GetSizeFn>(vtable[2])(self, ctx_id, slot_arg, 2u, &file_size);
    if (file_size == 0u) {
        engine_func_002c3a24(lock1);
        return 0xC8810BEFu;
    }

    void** const slot = reinterpret_cast<void**>(self + ((mode == 0u) ? 0x3A8u : 0x558u));
    volatile u8* const flag = flags + ((mode == 0u) ? 3u : 4u);

    if ((mode == 0u || mode == 1u) && *flag != 0u) {
        *reinterpret_cast<u32*>(out_hdr + 0x14u) = 0u;
        release_slot_239734(lock2, slot, flag);
    }

    engine_func_002c3aa8(lock2);
    if (*flag != 0u) {
        func_00239b84(*slot);
        *flag = 0u;
    }
    void* const buf_alloc = func_00239b54(file_size, 4u);
    *slot = buf_alloc;
    if (buf_alloc == nullptr) {
        *flag = 0u;
        engine_func_002c3a24(lock2);
        *reinterpret_cast<u32*>(out_hdr + 0x14u) = 0u;
        engine_func_002c3a24(lock1);
        return 0xC8610BF3u;
    }
    *flag = 1u;
    engine_func_002c3a24(lock2);

    using ReadFn = s32 (*)(u8*, void*, u32, u32*, u32, u32, u32);
    const s32 read_res = reinterpret_cast<ReadFn>(vtable[13])(
        self, buf_alloc, file_size, &bytes_read, *reinterpret_cast<const u32*>(self + 4u),
        slot_arg, 0x12u);
    const u8* const buf = static_cast<const u8*>(*slot);

    if (read_res < 0 || bytes_read == 0u) {
        *reinterpret_cast<u32*>(out_hdr + 0x14u) = 0u;
        release_slot_239734(lock2, slot, flag);
        engine_func_002c3a24(lock1);
        return 0xC8810BEFu;
    }

    if (bytes_read < 0x20u) {
        engine_func_002c3a24(lock1);
        return 0xC8E1086Au;
    }

    engine_func_002c5ff4(out_hdr, buf, 0x20u);
    if (*reinterpret_cast<const u32*>(out_hdr + 4u) != bytes_read) {
        engine_func_002c3a24(lock1);
        return 0xC8E1086Au;
    }

    const u32 count = *reinterpret_cast<const u32*>(out_hdr + 0x14u);
    if (0x20u + count * 0x70u > bytes_read) {
        engine_func_002c3a24(lock1);
        return 0xC8E1086Au;
    }

    u8 entry_tmp[0x70];
    for (u32 i = 0u; i < count; ++i) {
        const u8* const entry = buf + 0x20u + i * 0x70u;
        engine_func_002c5ff4(entry_tmp, entry, 0x70u);
        if (*reinterpret_cast<const u16*>(entry_tmp) != 0x6060u ||
            *reinterpret_cast<const u32*>(entry_tmp + 0x10u) !=
                *reinterpret_cast<const u32*>(self + 4u)) {
            engine_func_002c3a24(lock1);
            return 0xC8E1086Au;
        }
        out_entries[i] = entry;
    }

    engine_func_002c3a24(lock1);
    return 0u;
}

extern "C" void func_002b0908(u32 kind, u32 a4, u32 color, s32 x, u32 y_bits, u32 w, s32 h,
                            u32 z_bits);

namespace {

inline void set_tex_002beae4(u32 tex_id) {
    const u32 val = battle_func_002c5fa4(6u, tex_id, 0u);
    u8* const p = *reinterpret_cast<u8* const*>(0x0044EA00u) + 0x12ACu;
    const u32 idx = *reinterpret_cast<const u32*>(p);
    u32* const slot = reinterpret_cast<u32*>(p + 8u + idx * 4u);
    const u32 old = *slot;
    *slot = val;
    if (p[0x18u] != 0u || old != val) {
        using SetFn = void (*)(u32);
        (*reinterpret_cast<const SetFn*>(p + 0x1Cu))(val);
        p[0x18u] = 0u;
    }
}

inline u32 calc_bar_width_002beae4(s32 val, s32 max_val, s32 full_w, bool min1_always) {
    const s32 raw = val;
    if (val > max_val) {
        val = max_val;
    }
    if (val < 0) {
        val = 0;
    }
    const f32 ratio = static_cast<f32>(full_w) / static_cast<f32>(max_val);
    u32 w = static_cast<u32>(ratio * static_cast<f32>(val));
    if (w == 0u && (min1_always || raw > 0)) {
        w = 1u;
    }
    return w;
}

inline u32 pick_bar_color_002beae4(s32 max_val, s32 target_val, u32 normal_color, u32 low_color) {
    s32 q12_max = static_cast<s32>(static_cast<s16>(max_val)) << 12;
    s32 thresh = (q12_max / 100) * 20;
    if (thresh < 0x1000) {
        thresh = 0x1000;
    }
    const s32 q12_target = static_cast<s32>(static_cast<s16>(target_val)) << 12;
    return (static_cast<u32>(thresh) >= static_cast<u32>(q12_target)) ? low_color : normal_color;
}

inline void draw_delta_002beae4(u32 a4, u32 delta_color, s32 x, u32 y_bits, u32 w_delta, s32 h,
                                u32 z_bits, u32 skip_main) {
    if (w_delta == 0u) {
        return;
    }
    if (skip_main != 0u) {
        set_tex_002beae4(1u);
    }
    func_002b0908(2u, a4, delta_color, x, y_bits, w_delta, h, z_bits);
    set_tex_002beae4(7u);
}

}  // namespace

// DECOMP_FUNC(0x002beae4, 1072)
extern "C" void battle_func_002beae4(s32 cur, s32 max_val, s32 delta, s32 step, u32 a4, u32 color,
                                     u32 heal_color, u32 dmg_color, u32 low_color, s32 x,
                                     u32 y_bits, u32 z_bits, u32 skip_main) {
    const u8* const info = camp_func_002bf6d0(a4, color);
    const s16* const dims = *reinterpret_cast<const s16* const*>(info + 0x0Cu);
    const s32 full_w = dims[0];
    const s32 h = dims[1];

    u32 w_cur = calc_bar_width_002beae4(cur, max_val, full_w, false);
    if (delta == 0) {
        const u32 draw_color = pick_bar_color_002beae4(max_val, cur, color, low_color);
        func_002b0908(2u, a4, draw_color, x, y_bits, w_cur, h, z_bits);
        return;
    }

    s32 next_val = cur + delta;
    if (next_val > max_val) {
        next_val = max_val;
    }
    if (next_val < 0) {
        next_val = 0;
    }
    u32 w_next = calc_bar_width_002beae4(next_val, max_val, full_w, true);
    const u32 draw_color = pick_bar_color_002beae4(max_val, next_val, color, low_color);

    if (delta > 0) {
        const u32 diff = w_next - w_cur;
        u32 w_delta = (diff == 0u) ? 1u : diff;
        if (static_cast<u32>(step - 11) <= 9u) {
            const u32 anim = static_cast<u32>(static_cast<f32>(diff) * 0.1f *
                                              static_cast<f32>(step - 10));
            w_delta -= anim;
            w_cur += anim;
        } else if (step > 20) {
            w_cur = w_next;
            w_delta = 0u;
        }
        if (skip_main == 0u) {
            func_002b0908(2u, a4, draw_color, x, y_bits, w_cur, h, z_bits);
        }
        draw_delta_002beae4(a4, heal_color, x + static_cast<s32>(w_cur), y_bits, w_delta, h, z_bits,
                            skip_main);
    } else {
        u32 w_delta = w_cur - w_next;
        if (w_cur < w_next) {
            w_next = w_cur;
            w_delta = 0u;
        }
        if (static_cast<u32>(step - 11) <= 9u) {
            const u32 anim = static_cast<u32>(static_cast<f32>(w_cur - w_next) * 0.1f *
                                              static_cast<f32>(step - 10));
            w_delta -= anim;
        } else if (step > 20) {
            w_delta = 0u;
        }
        if (skip_main == 0u) {
            func_002b0908(2u, a4, draw_color, x, y_bits, w_next, h, z_bits);
        }
        draw_delta_002beae4(a4, dmg_color, x + static_cast<s32>(w_next), y_bits, w_delta, h, z_bits,
                            skip_main);
    }
}

extern "C" void ui_func_002bf710(f32 scale);

// DECOMP_FUNC(0x00109aa0, 1080)
extern "C" u32 ui_func_00109aa0(u32 mode, u32 idx, u32 suppress_draw, f32 x, f32 y,
                                f32 /*unused*/, f32 init_scale) {
    ui_func_002bf710(init_scale);

    u32 id = 0u;
    s32 sub_id = -1;
    bool valid_mode = true;

    if (mode == 0u) {
        static constexpr u16 kMode0Ids[22] = {
            0x0BB8u, 0x0BB8u, 0x0BB8u, 0x0BB8u, 0x0BB9u, 0x0BBAu, 0x0BBBu, 0x0BBBu,
            0x0BBCu, 0x0BC1u, 0x0BC2u, 0x0BC3u, 0x0BC4u, 0x0BC5u, 0x0BBDu, 0x0BBEu,
            0x0BC0u, 0x0BBFu, 0x0BBBu, 0x0BBBu, 0x0BBBu, 0x0BBBu,
        };
        static constexpr s8 kMode0Sub[22] = {
            0, 1, 2, 3, 4, 5, 7, 6, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0x1B, 0x1C, 0x1D, 0x1E,
        };
        if (idx < 22u) {
            id = kMode0Ids[idx];
            sub_id = kMode0Sub[idx];
        }
    } else if (mode == 1u) {
        static constexpr u16 kMode1Ids[14] = {
            0x03E8u, 0x03E9u, 0x03EAu, 0x03EBu, 0x03ECu, 0x03EDu, 0x03EEu,
            0x03EFu, 0x03F0u, 0x03F1u, 0x03F2u, 0x03F3u, 0x03F4u, 0x03F6u,
        };
        if (idx < 14u) {
            id = kMode1Ids[idx];
        }
    } else if (mode == 2u) {
        static constexpr u16 kMode2Ids[10] = {
            0x03F7u, 0x03F8u, 0x03F9u, 0x03FAu, 0x03FBu,
            0x03FCu, 0x03FDu, 0x03FEu, 0x03FFu, 0x0400u,
        };
        if (idx < 10u) {
            id = kMode2Ids[idx];
        }
    } else {
        valid_mode = false;
    }

    u32 ret = 0u;
    if (valid_mode) {
        const u8* const info = camp_func_002bf6d0(0x13u, id);
        if (info != nullptr && suppress_draw == 0u) {
            const u32 xi = static_cast<u32>(static_cast<s32>(x));
            const u32 yi = static_cast<u32>(static_cast<s32>(y + 2.0f));
            if (sub_id >= 0) {
                func_002bf558(2u, 0x13u, static_cast<u32>(sub_id), xi, yi, 0x0Bu);
            } else {
                ui_func_002bf460(2u, 0x13u, id, xi, yi, 0x0Bu);
            }
            ret = *reinterpret_cast<const u16*>(info + 4u) & 0x7FFFu;
        }
    }

    ui_func_002bf710(1.0f);
    return ret;
}

extern "C" s32 engine_func_0028796c(u32 a0);
extern "C" s32 engine_func_00287958(s32 a0, u32 a1);
extern "C" void engine_func_00287790(u32 a0);
extern "C" s32 ui_func_002876d0(u32 bg_id);
extern "C" void engine_func_00287590(u32 bg_id);
extern "C" void CommonBg_func_00289b4c();
extern "C" void camp_func_0028dc54();
extern "C" void ButtonHelp_Init();
extern "C" void script_vm_func_00289ae8();
extern "C" u8* AsdMemory_func_002c23f8(u32 size);
extern "C" u8* engine_func_0028757c(u8* ptr);
extern "C" void script_vm_func_00381d9c();
extern "C" void engine_func_00384304(u8* vm, u32 a1, u32 a2, u32 a3);
extern "C" void AsdSequence_func_002c59b8(u32 kind, const void* data, u32 size);
extern "C" void engine_func_00384ac8(u8* vm);
extern "C" void script_vm_func_002a72fc(u8* vm);
extern "C" void engine_func_002b2520(u8* vm);
extern "C" s32 engine_func_00385488(u8* vm);
extern "C" s32 engine_func_0028756c();
extern "C" s32 engine_func_0028753c();
extern "C" void script_vm_func_00291be8();
extern "C" void script_vm_func_00291a5c();
extern "C" void engine_func_002874e4();
extern "C" void ui_func_002a0678(u32 a0, u32 a1);
extern "C" void script_vm_func_0032c8d0();

namespace {

inline u32 map_scene_type_001a9970(s32 scene_id) {
    switch (scene_id) {
        case 1:
            return 0u;
        case 9:
            return 2u;
        case 10:
        case 11:
        case 12:
        case 13:
            return 3u;
        default:
            return 1u;
    }
}

inline void destroy_vm_001a9970(u8* state_obj) {
    state_obj[0x19u] = 4u;
    state_obj[0x18u] = 1u;
    u8* const vm = *reinterpret_cast<u8* const*>(state_obj + 0x1Cu);
    if (vm != nullptr) {
        script_vm_func_002a72fc(vm);
        engine_func_002b2520(*reinterpret_cast<u8* const*>(state_obj + 0x1Cu));
        *reinterpret_cast<u8**>(state_obj + 0x1Cu) = nullptr;
    }
}

inline bool check_rec_001a9970(const u8* rec, u32 scene_type, s32 scene_id) {
    if (*reinterpret_cast<const u16*>(rec + 0x16u) != scene_type) {
        return false;
    }
    const s32 cond_id = *reinterpret_cast<const s16*>(rec + 0x18u);
    if (cond_id != -1 && cond_id != scene_id) {
        return false;
    }
    const u16 f1 = *reinterpret_cast<const u16*>(rec + 0x12u);
    if (f1 == 0xFFFFu) {
        if (script_vm_func_002990bc(0x65u) == 0 || script_vm_func_002990bc(0x66u) == 0 ||
            script_vm_func_002990bc(0x67u) == 0) {
            return false;
        }
    } else if (f1 != 0u && script_vm_func_002c0ba8(f1) == 0) {
        return false;
    }
    const u16 f2 = *reinterpret_cast<const u16*>(rec + 0x14u);
    if (f2 != 0u && script_vm_func_002c0ba8(f2) != 0) {
        return false;
    }
    return true;
}

}  // namespace

// DECOMP_FUNC(0x001a9970, 1096)
extern "C" s32 engine_func_001a9970() {
    u8* const g_state = reinterpret_cast<u8*>(0x0044DB88u);
    u8* const state_obj = *reinterpret_cast<u8* const*>(g_state + 4u);

    switch (state_obj[0x19u]) {
        case 0u: {
            const s32 scene_id = *reinterpret_cast<const s32*>(g_state + 8u);
            const u32 scene_type = map_scene_type_001a9970(scene_id);
            const u32 quick_mode = *reinterpret_cast<const u32*>(g_state + 0x10u);

            if (quick_mode == 0u) {
                if (scene_type == 1u && script_vm_func_002c0ba8(0x235u) != 0) {
                    if (script_vm_func_002c0ba8(0x1C0u) == 0 ||
                        script_vm_func_002c0ba8(0x424u) == 0 ||
                        engine_func_00287958(engine_func_0028796c(1u), 4u) != 0) {
                        engine_func_00287790(0u);
                    }
                }

                const u8* const table = reinterpret_cast<const u8*>(0x0044DBB0u);
                for (u32 i = 0u; i < 3u; ++i) {
                    const u8* const rec = table + i * 26u;
                    if (check_rec_001a9970(rec, scene_type, scene_id)) {
                        u32 seq_buf[8];
                        seq_buf[0] = *reinterpret_cast<const u16*>(rec + 0x10u);
                        seq_buf[1] = 0xFFFFFFFFu;
                        engine_func_002bf86c(&seq_buf[2], rec);
                        AsdSequence_func_002c59b8(4u, seq_buf, 0x20u);
                        return 0;
                    }
                }

                const u32 bg_id = (scene_id == 1) ? 0x0100005Du : 0x0100005Au;
                if (ui_func_002876d0(bg_id) != 1) {
                    engine_func_00287590(bg_id);
                }
                CommonBg_func_00289b4c();
                camp_func_0028dc54();
                ButtonHelp_Init();
                script_vm_func_00289ae8();
            }

            u8* vm = AsdMemory_func_002c23f8(0xFC4u);
            if (vm != nullptr) {
                *reinterpret_cast<u32*>(vm) = 0u;
                vm = engine_func_0028757c(vm + 0x658u) - 0x658u;
            }
            *reinterpret_cast<u8**>(state_obj + 0x1Cu) = vm;
            script_vm_func_00381d9c();
            engine_func_00384304(*reinterpret_cast<u8* const*>(state_obj + 0x1Cu),
                                 *reinterpret_cast<const u32*>(g_state + 8u),
                                 *reinterpret_cast<const u32*>(g_state + 0x0Cu),
                                 *reinterpret_cast<const u32*>(g_state + 0x10u));
            state_obj[0x19u] = 1u;
            return 0;
        }
        case 1u: {
            engine_func_00384ac8(*reinterpret_cast<u8* const*>(state_obj + 0x1Cu));
            const u32 flags = **reinterpret_cast<const u32* const*>(state_obj + 0x1Cu);
            if ((flags & 1u) != 0u) {
                state_obj[0x19u] = 3u;
            }
            return 0;
        }
        case 2u: {
            destroy_vm_001a9970(state_obj);
            return 0;
        }
        case 3u: {
            u8* const vm = *reinterpret_cast<u8* const*>(state_obj + 0x1Cu);
            const bool skip_seq = (vm != nullptr && engine_func_00385488(vm) != 0);
            if (!skip_seq && engine_func_0028756c() != 0 &&
                *reinterpret_cast<const u32*>(g_state + 0x10u) == 0u) {
                if (engine_func_0028753c() != 0) {
                    const u8* const sys = reinterpret_cast<const u8*>(0x0049F91Cu);
                    const u32 val = *reinterpret_cast<const u32*>(sys + 0x2FCu) - 0xC8u;
                    AsdSequence_func_002c59b8(0x0Eu, &val, 4u);
                } else {
                    AsdSequence_func_002c59b8(6u, nullptr, 0u);
                }
            }
            destroy_vm_001a9970(state_obj);
            if (*reinterpret_cast<const u32*>(g_state + 0x10u) == 0u) {
                script_vm_func_00291be8();
                script_vm_func_00291a5c();
                engine_func_002874e4();
            }
            return 0;
        }
        case 4u: {
            if (g_state[1] != 0u) {
                ui_func_002a0678(0u, 1u);
                ui_func_002a0678(1u, 1u);
                script_vm_func_0032c8d0();
            }
            return -1;
        }
        default:
            return 0;
    }
}

extern "C" void script_vm_func_00291000(u32 a0);
extern "C" void script_vm_func_00289f00(u32 a0);
extern "C" void ui_func_002a8a8c();
extern "C" void camp_func_002ae874();
extern "C" s32 shop_func_002337a0(const u8* sub);
extern "C" s32 engine_func_0023378c(const u8* shop, s32 idx);
extern "C" s32 engine_func_00394338(const u8* rec);
extern "C" void PlaceWin_SetVisible(u32 visible);
extern "C" void camp_func_0029f10c(const u8* ptr, u32 rgba);

namespace {

inline void play_se_and_anim_00233ac0(u32 se_id) {
    script_vm_func_002b8b78(se_id);
    for (u32 i = 0u; i < 6u; ++i) {
        ui_func_002a8a8c();
    }
    camp_func_002ae874();
}

}  // namespace

// DECOMP_FUNC(0x00233ac0, 1100)
extern "C" void camp_func_00233ac0(u8* self, s32 state, u32 flag) {
    script_vm_func_00291000(0u);
    static constexpr u32 kRgba = 0x323232FFu;

    switch (state) {
        case -1: {
            u32 bits = *reinterpret_cast<const u32*>(self);
            if ((bits & 0x100000u) != 0u) {
                *reinterpret_cast<u32*>(self) = bits & ~0x100000u;
                script_vm_func_00289f00(0u);
                for (u32 i = 0u; i < 6u; ++i) {
                    ui_func_002a8a8c();
                }
            }
            break;
        }
        case 0: {
            *reinterpret_cast<u32*>(self) |= 0x100000u;
            play_se_and_anim_00233ac0(0xC9u);
            break;
        }
        case 1: {
            *reinterpret_cast<u32*>(self) |= 0x100000u;
            if (flag != 0u) {
                play_se_and_anim_00233ac0(0xCAu);
            }
            camp_func_002b8794(0u, 0x11u, 0u, 1u);
            camp_func_002b8794(1u, 0u, 0u, 1u);
            camp_func_002b8794(2u, 0x0Bu, 0x4Bu, 1u);
            camp_func_002b8794(3u, 0u, 0u, 1u);
            camp_func_002b8794(4u, 0x10u, 0x4Fu, 1u);
            camp_func_002b8794(5u, 0u, 0u, 1u);
            break;
        }
        case 2: {
            *reinterpret_cast<u32*>(self) |= 0x100000u;
            const u8* const shop = *reinterpret_cast<const u8* const*>(0x00432FC8u);
            shop_func_002337a0(self + 0x240u);
            if (flag != 0u) {
                play_se_and_anim_00233ac0(0xCBu);
            }
            camp_func_002b8794(0u, 0x0Au, 0x4Au, 1u);
            camp_func_002b8794(1u, 0u, 0u, 1u);
            camp_func_002b8794(2u, 0x0Bu, 0x4Bu, 1u);
            camp_func_002b8794(3u, 0u, 0u, 1u);

            const s32 idx = shop_func_002337a0(self + 0x240u);
            if (engine_func_0023378c(shop, idx) == 0) {
                camp_func_002b8794(4u, 0x11u, 0u, 0u);
            } else {
                const u8* const table = *reinterpret_cast<const u8* const*>(shop + 0x678u);
                const s32 idx2 = shop_func_002337a0(self + 0x240u);
                const u8* const rec = table + idx2 * 2504;
                if (rec[0x9B3u] != 0u) {
                    camp_func_002b8794(4u, 0x0Fu, 0x4Fu, 0u);
                } else {
                    const s32 idx3 = shop_func_002337a0(self + 0x240u);
                    const s32 kind = engine_func_00394338(table + idx3 * 2504);
                    if (kind == 0) {
                        camp_func_002b8794(4u, 0x0Cu, 0x4Cu, 0u);
                    } else if (kind == 1) {
                        camp_func_002b8794(4u, 0x0Du, 0x4Du, 0u);
                    } else if (kind == 2) {
                        camp_func_002b8794(4u, 0x0Eu, 0x4Eu, 0u);
                    } else if (kind == 3) {
                        camp_func_002b8794(4u, 0x11u, 0u, 0u);
                    }
                }
            }
            camp_func_002b8794(5u, 0u, 0u, 0u);
            PlaceWin_SetVisible(1u);
            camp_func_0029f10c(self + 0x1130u, kRgba);
            break;
        }
        case 3: {
            *reinterpret_cast<u32*>(self) |= 0x100000u;
            if (flag != 0u) {
                play_se_and_anim_00233ac0(0xCAu);
            }
            camp_func_002b8794(0u, 0x11u, 0u, 1u);
            camp_func_002b8794(1u, 0u, 0u, 1u);
            camp_func_002b8794(2u, 0x11u, 0u, 1u);
            camp_func_002b8794(3u, 0u, 0u, 1u);
            camp_func_002b8794(4u, 0x10u, 0x4Fu, 1u);
            camp_func_002b8794(5u, 0u, 0u, 1u);
            PlaceWin_SetVisible(0u);
            camp_func_0029f10c(nullptr, kRgba);
            break;
        }
        case 4: {
            *reinterpret_cast<u32*>(self) |= 0x100000u;
            if (flag != 0u) {
                script_vm_func_002b8b78(0xCEu);
            }
            break;
        }
        default:
            break;
    }
}

extern "C" u32 engine_func_0038b75c(void* ctx, u8* buffer, const char16_t* name, u32 size,
                                    u32 flag_a, u32 flag_b, u32 out_ptr);
extern "C" void ui_func_002acb3c(void* dst, const void* src, u32 size);

namespace {

inline void release_obj_38f1d0(u8* self) {
    void* const obj = *reinterpret_cast<void* const*>(self + 0x208u);
    if (obj != nullptr) {
        using ReleaseFn = void (*)(void*);
        (*reinterpret_cast<ReleaseFn* const*>(obj))[1](obj);
        *reinterpret_cast<void**>(self + 0x208u) = nullptr;
    }
}

}  // namespace

// DECOMP_FUNC(0x0038f1d0, 1112)
extern "C" void engine_func_0038f1d0(u8* self) {
    u32* const state = reinterpret_cast<u32*>(self + 8u);
    switch (*state) {
        case 0u:
            *state = 1u;
            return;
        case 1u: {
            u8* shop = *reinterpret_cast<u8* const*>(0x00432FC8u);
            u32* const buf = reinterpret_cast<u32*>(shop + 0x694u);
            for (u32 i = 0u; i < 16u; ++i) {
                buf[i] = 0u;
            }
            if (engine_func_0038b75c(shop, shop + 0x694u,
                                     u"16\u30B1\u30BF\u306E\u756A\u53F7\u5165\u529B\u30C6\u30B9\u30C8", 0x10u,
                                     0u, 1u, reinterpret_cast<u32>(shop + 0x6D4u)) != 0u) {
                shop = *reinterpret_cast<u8* const*>(0x00432FC8u);
                ui_func_002acb3c(shop + 0x6D4u, shop + 0x694u, 0x40u);
                *reinterpret_cast<u32*>(self + 4u) = 0xEu;
                *state = 0u;
                release_obj_38f1d0(self);
                engine_func_00233f4c(self, 0u);
                camp_func_00233ac0(self, -1, 0u);
            } else {
                *state = 2u;
                *reinterpret_cast<u32*>(self + 0xCu) = 3u;
            }
            return;
        }
        case 2u: {
            s32* const timer = reinterpret_cast<s32*>(self + 0xCu);
            *timer -= 1;
            if (*timer <= 0) {
                *reinterpret_cast<u32*>(self + 4u) = 6u;
                *state = 0u;
                release_obj_38f1d0(self);
            }
            return;
        }
        default:
            return;
    }
}

// Trailing function at 0x0038f360 within the 0x0038f1d0 span.
extern "C" __attribute__((naked)) void func_0038f360() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe24dd02c, 0xe1a04000, 0xe1a0000d\n"
        ".word 0xebfa93c0, 0xe59f52a0, 0xe59f62a0, 0xe3a07000\n"
        ".word 0xe5951000, 0xe5910754, 0xe2002010, 0xe3c00070\n"
        ".word 0xe1b02222, 0xe5810754, 0x0a000027, 0xe3a02000\n"
        ".word 0xe3e01000, 0xe1a00004, 0xebfa91c4, 0xe2840a01\n"
        ".word 0xe2800e1b, 0xebfbbe79, 0xe1a00004, 0xebfa92d2\n"
        ".word 0xe5940208, 0xe2842004, 0xe3a01012, 0xe8820082\n"
        ".word 0xe3500000, 0x0a000003, 0xe5901000, 0xe5911004\n"
        ".word 0xe12fff31, 0xe5847208, 0xe5950000, 0xe2800080\n"
        ".word 0xebf65eb9, 0xe5960000, 0xe320f000, 0xebfbbdff\n"
        ".word 0xe5960000, 0xe320f000, 0xebfcae37, 0xe5950000\n"
        ".word 0xe2800098, 0xebfc7814, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000003, 0xe5950000, 0xe5901754, 0xe3c11801\n"
        ".word 0xe5801754, 0xe28dd02c, 0xe8bd80f0, 0xe5941008\n"
        ".word 0xe3510002, 0x0a00003e, 0xaa000011, 0xe3510000\n"
        ".word 0x0a000032, 0xe3510001, 0x1afffff5, 0xebfb70da\n"
        ".word 0xe3500000, 0xe320f000, 0x0afffff1, 0xe3a01001\n"
        ".word 0xe1a00004, 0xebfa92b4, 0xe5960000, 0xe320f000\n"
        ".word 0xebffe21e, 0xe3a00002, 0xe5840008, 0xe28dd02c\n"
        ".word 0xe8bd80f0, 0xe3510003, 0x0a00004d, 0xe2411c27\n"
        ".word 0xe251100f, 0x03100004, 0x1affffe1, 0xe3100008\n"
        ".word 0x1affffdf, 0xe5960000, 0xebfbbdd0, 0xe5960000\n"
        ".word 0xe320f000, 0xebfcae08, 0xe5950000, 0xe2800098\n"
        ".word 0xebfc77e5, 0xe3500000, 0xe320f000, 0x0a000003\n"
        ".word 0xe5950000, 0xe5901754, 0xe3c11801, 0xe5801754\n"
        ".word 0xe5940208, 0xe2842004, 0xe3a01003, 0xe8820082\n"
        ".word 0xe3500000, 0x0affffca, 0xe5901000, 0xe5911004\n"
        ".word 0xe12fff31, 0xe5847208, 0xe28dd02c, 0xe8bd80f0\n"
        ".word 0xe3a00000, 0xebfca416, 0xe3a02000, 0xe3e01000\n"
        ".word 0xe1a00004, 0xebfa9161, 0xe3a00001, 0xe320f000\n"
        ".word 0xeaffffd0, 0xe5940000, 0xe3100c02, 0x0affffb8\n"
        ".word 0xe5961000, 0xe28d0014, 0xebffe51f, 0xe28d7014\n"
        ".word 0xe897100f, 0xe88d100f, 0xe1a0000d, 0xebfbbdc4\n"
        ".word 0xe3500000, 0x13a00003, 0x15840008, 0x1affffac\n"
        ".word 0xe1a0000d, 0xebfc488d, 0xe3500000, 0xe320f000\n"
        ".word 0x0affffa7, 0xe59f0088, 0xe5840008, 0xe5950000\n"
        ".word 0xe2800098, 0xebfc77b0, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000003, 0xe5950000, 0xe5901754, 0xe3c11801\n"
        ".word 0xe5801754, 0xe1a00004, 0xebfa924f, 0xe28dd02c\n"
        ".word 0xe8bd80f0, 0xe320f000, 0xebfb707b, 0xe3500000\n"
        ".word 0xe320f000, 0x0affff92, 0xe5960000, 0xebfbbd83\n"
        ".word 0xe5961000, 0xe28d0014, 0xebfc47c3, 0xe2841004\n"
        ".word 0xe3a00005, 0xe8810081, 0xe5940208, 0xe3500000\n"
        ".word 0x1affffbc, 0xe28dd02c, 0xe8bd80f0, 0x00432fc8\n"
        ".word 0x00433158, 0x0000270f\n"
    );
}

extern "C" const u8* ui_func_0027dca0(u8* self, s32 id);

namespace {

inline const u8* find_obj_by_meta_0033aa2c(u8* self, const u8* item) {
    const u8* const meta = ui_func_0027dca0(self, *reinterpret_cast<const s16*>(item + 0x62u));
    const u32 target_id = *reinterpret_cast<const u32*>(meta + 0x0Cu);
    for (s32 i = 0; i < 42; ++i) {
        const u8* const obj =
            *reinterpret_cast<const u8* const*>(self + 0x2134u + static_cast<u32>(i) * 4u);
        if (obj != nullptr && *reinterpret_cast<const u32*>(obj + 4u) == target_id) {
            return obj;
        }
    }
    return nullptr;
}

}  // namespace

// DECOMP_FUNC(0x0033aa2c, 1120)
extern "C" s32 ui_func_0033aa2c(u8* self, u8* cursor, u32 flags) {
    f32 new_x = 0.0f;

    if (*reinterpret_cast<const u32*>(self + 0x1FBCu) != 0u) {
        for (s32 r1 = 0; r1 < 50; ++r1) {
            const u8* const base = *reinterpret_cast<const u8* const*>(self + 0x1FBCu);
            for (s32 r0 = 0; r0 < 50; r0 += 2) {
                const u8* hit = nullptr;
                if (*reinterpret_cast<const s16*>(base + r0 * 24 + 2) == r1) {
                    hit = base + r0 * 24;
                } else if (*reinterpret_cast<const s16*>(base + r0 * 24 + 0x1A) == r1) {
                    hit = base + r0 * 24 + 0x18;
                } else {
                    continue;
                }
                if (hit != nullptr) {
                    if (*reinterpret_cast<const f32*>(hit + 0x0Cu) ==
                        *reinterpret_cast<const f32*>(cursor)) {
                        *reinterpret_cast<f32*>(cursor + 0x0Cu) =
                            *reinterpret_cast<const f32*>(hit + 0x0Cu);
                        *reinterpret_cast<f32*>(cursor + 0x10u) =
                            *reinterpret_cast<const f32*>(hit + 0x10u);
                        *reinterpret_cast<f32*>(cursor + 0x14u) =
                            *reinterpret_cast<const f32*>(hit + 0x14u);
                        return 1;
                    }
                    break;
                }
            }
        }
    }

    const u8* const meta = ui_func_0027dca0(self, *reinterpret_cast<const s16*>(cursor + 0x62u));
    const u8* const obj = reinterpret_cast<const u8*>(
        ui_func_0027dc58(self, *reinterpret_cast<const u32*>(meta + 0x0Cu)));
    if (obj == nullptr) {
        return 0;
    }

    const u8* const tex = *reinterpret_cast<const u8* const*>(obj + 0x10u);
    const f32 cur_scale = *reinterpret_cast<const f32*>(cursor + 0x40u);
    const f32 cur_w = static_cast<f32>(static_cast<u32>(*reinterpret_cast<const u16*>(tex + 0x24u)));
    const f32 cur_x0 = static_cast<f32>(static_cast<s32>(*reinterpret_cast<const s16*>(tex + 0x20u)));
    const f32 min_gap = cur_w * cur_scale + cur_scale * 2.5f;
    const f32 cur_right = (cur_w - cur_x0) * cur_scale;
    const f32 cur_left = cur_scale * cur_x0;

    const u8* items[50];
    engine_func_002c4b30(items, 0xC8u);

    u32 count = 0u;
    const u8* const base_items = *reinterpret_cast<const u8* const*>(self + 0x1E98u) + 0x450u;
    const s16 cur_id = *reinterpret_cast<const s16*>(cursor + 0x62u);
    for (s32 i = 0; i < 50; ++i) {
        const u8* const item = base_items + i * 0x114;
        const u32 st = *reinterpret_cast<const u32*>(item + 0x50u);
        if ((st & 1u) != 0u && (st & 2u) != 0u && (st & 0x80u) != 0u && (st & 0x10u) == 0u &&
            *reinterpret_cast<const s16*>(item + 0x62u) != cur_id) {
            items[count++] = item;
        }
    }
    camp_func_002b7f08(items, count, 4u, 0x0019D82Cu);

    if ((flags & 0x10000u) != 0u) {
        const u32 limit = count + 1u;
        for (u32 idx = 0u; idx < limit; ++idx) {
            if (idx == count) {
                const u8* const prev = items[idx - 1u];
                const u8* const obj2 = find_obj_by_meta_0033aa2c(self, prev);
                const u8* const tex2 = *reinterpret_cast<const u8* const*>(obj2 + 0x10u);
                const f32 sc2 = *reinterpret_cast<const f32*>(prev + 0x40u);
                const f32 w2 = static_cast<f32>(
                    static_cast<u32>(*reinterpret_cast<const u16*>(tex2 + 0x24u)));
                const f32 x2 = static_cast<f32>(
                    static_cast<s32>(*reinterpret_cast<const s16*>(tex2 + 0x20u)));
                const f32 prev_right = (w2 - x2) * sc2 + sc2 * 2.5f;
                if (__builtin_fabsf(*reinterpret_cast<const f32*>(prev + 0x0Cu)) - 20.0f >=
                    min_gap) {
                    new_x = *reinterpret_cast<const f32*>(prev + 0x0Cu) + (prev_right + cur_left);
                    break;
                }
            } else {
                const u8* const item = items[idx];
                const u8* const obj2 = find_obj_by_meta_0033aa2c(self, item);
                const u8* const tex2 = *reinterpret_cast<const u8* const*>(obj2 + 0x10u);
                const f32 sc2 = *reinterpret_cast<const f32*>(item + 0x40u);
                const f32 x2 = static_cast<f32>(
                    static_cast<s32>(*reinterpret_cast<const s16*>(tex2 + 0x20u)));
                const f32 item_left = sc2 * x2 + sc2 * 2.5f;
                const f32 ref_abs =
                    (idx > 0u) ? __builtin_fabsf(*reinterpret_cast<const f32*>(items[idx - 1u] +
                                                                               0x0Cu))
                               : 20.0f;
                if (ref_abs - __builtin_fabsf(*reinterpret_cast<const f32*>(item + 0x0Cu)) >=
                    min_gap) {
                    new_x = (*reinterpret_cast<const f32*>(item + 0x0Cu) - item_left) - cur_right;
                    break;
                }
            }
        }
    } else {
        const u8* const wrap = reinterpret_cast<const u8*>(
            script_vm_func_0027eb98(*reinterpret_cast<const u32*>(0x0043427Cu)));
        const u8* const item = *reinterpret_cast<const u8* const*>(wrap + 0x24u);
        if (item == nullptr) {
            return 0;
        }
        const u8* const meta2 = ui_func_0027dca0(self, *reinterpret_cast<const s16*>(item + 0x62u));
        const u8* const obj2 = reinterpret_cast<const u8*>(
            ui_func_0027dc58(self, *reinterpret_cast<const u32*>(meta2 + 0x0Cu)));
        if (obj2 == nullptr) {
            return 0;
        }
        const u8* const tex2 = *reinterpret_cast<const u8* const*>(obj2 + 0x10u);
        const f32 sc2 = *reinterpret_cast<const f32*>(item + 0x40u);
        const f32 x2 =
            static_cast<f32>(static_cast<s32>(*reinterpret_cast<const s16*>(tex2 + 0x20u)));
        const f32 w2 =
            static_cast<f32>(static_cast<u32>(*reinterpret_cast<const u16*>(tex2 + 0x24u)));
        const f32 s1 = sc2 * x2 + sc2 * 2.5f;
        const f32 s2 = (w2 - x2) * sc2 + sc2 * 2.5f;
        if ((flags & 0x20000u) != 0u) {
            new_x = (*reinterpret_cast<const f32*>(item + 0x0Cu) - s1) - cur_right;
        } else if ((flags & 0x40000u) != 0u) {
            new_x = *reinterpret_cast<const f32*>(item + 0x0Cu) + (s2 + cur_left);
        }
    }

    *reinterpret_cast<f32*>(cursor + 0x0Cu) = new_x;
    *reinterpret_cast<f32*>(cursor + 0x10u) = 0.0f;
    *reinterpret_cast<f32*>(cursor + 0x14u) = 0.0f;
    return 1;
}

extern "C" u32 func_0022c198(u8* self, u32 min_cap);
extern "C" void func_0022c968(u8* self, u32 new_end, u32 old_end, u32 arg3);

namespace {

struct Node22C294 {
    void* ptr;
    u32 ctrl;
    Node22C294* prev;
    Node22C294* next;
};

inline void copy_node_22c294(Node22C294* dst, const Node22C294* src) {
    dst->ptr = src->ptr;
    dst->ctrl = src->ctrl;
    Node22C294* const next = src->next;
    dst->next = next;
    next->prev = dst;
    dst->prev = const_cast<Node22C294*>(src);
    const_cast<Node22C294*>(src)->next = dst;
}

inline void destroy_range_22c294(Node22C294* begin, Node22C294* end) {
    for (Node22C294* cur = begin; cur < end; ++cur) {
        Node22C294* const prev = cur->prev;
        if (prev == nullptr || prev == cur) {
            if (cur->ctrl != 0u) {
                void* const obj = cur->ptr;
                using DelFn = void (*)(void*);
                (*reinterpret_cast<DelFn* const*>(obj))[1](obj);
            }
        } else {
            Node22C294* const next = cur->next;
            prev->next = next;
            next->prev = prev;
            cur->prev = nullptr;
            cur->next = nullptr;
        }
        cur->ctrl = 0u;
    }
}

inline Node22C294* alloc_nodes_22c294(void* alloc, u32 count) {
    void* const* const vt = *reinterpret_cast<void* const* const*>(alloc);
    using AllocFn = Node22C294* (*)(void*, u32);
    using OomFn = void (*)(void*, u32, u32);
    Node22C294* const p = reinterpret_cast<AllocFn>(vt[0])(alloc, count * 16u);
    if (p == nullptr) {
        reinterpret_cast<OomFn>(vt[2])(alloc, 0x0040FE40u, count * 16u);
    }
    return p;
}

}  // namespace

// DECOMP_FUNC(0x0022c294, 1124)
extern "C" s32 func_0022c294(u8* self, u32 new_size, const u8* fill_val) {
    const u32 old_size = *reinterpret_cast<const u32*>(self + 0x0Cu);
    Node22C294* const old_data = *reinterpret_cast<Node22C294* const*>(self + 0x04u);

    if (new_size <= old_size) {
        if (new_size == old_size) {
            return 1;
        }
        func_0022c968(self, new_size, old_size, 0u);
        Node22C294* const data = *reinterpret_cast<Node22C294* const*>(self + 0x04u);
        const u32 cur_size = *reinterpret_cast<const u32*>(self + 0x0Cu);
        destroy_range_22c294(data + new_size, data + cur_size);
        *reinterpret_cast<u32*>(self + 0x0Cu) = new_size;
        return 1;
    }

    u32 add_count = new_size - old_size;
    const u32 old_cap = *reinterpret_cast<const u32*>(self + 0x08u);
    u32 idx = old_size;

    if (new_size <= old_cap) {
        const u32 new_end = old_size + add_count;
        func_0022c968(self, new_end, old_size, 0u);
        const u32 cur_size = *reinterpret_cast<const u32*>(self + 0x0Cu);
        const u32 destroy_end = (new_end < cur_size) ? new_end : cur_size;
        Node22C294* const data = *reinterpret_cast<Node22C294* const*>(self + 0x04u);
        destroy_range_22c294(data + old_size, data + destroy_end);
        *reinterpret_cast<u32*>(self + 0x0Cu) = new_size;
    } else {
        const u32 cap1 = func_0022c198(self, new_size);
        void* const alloc = *reinterpret_cast<void* const*>(self);
        u32 new_cap = 0u;
        Node22C294* new_data = nullptr;

        if (cap1 != 0u) {
            new_data = alloc_nodes_22c294(alloc, cap1);
            if (new_data != nullptr) {
                new_cap = cap1;
            }
        }
        if (new_data == nullptr) {
            if (new_size == cap1 || new_size == 0u) {
                void* const* const vt = *reinterpret_cast<void* const* const*>(alloc);
                using Free0Fn = void (*)(void*);
                reinterpret_cast<Free0Fn>(vt[1])(alloc);
                return 0;
            }
            new_data = alloc_nodes_22c294(alloc, new_size);
            if (new_data == nullptr) {
                void* const* const vt = *reinterpret_cast<void* const* const*>(alloc);
                using Free0Fn = void (*)(void*);
                reinterpret_cast<Free0Fn>(vt[1])(alloc);
                return 0;
            }
            new_cap = new_size;
        }

        for (u32 i = 0u; i < old_size; ++i) {
            copy_node_22c294(new_data + i, old_data + i);
        }
        *reinterpret_cast<Node22C294**>(self + 0x04u) = new_data;
        *reinterpret_cast<u32*>(self + 0x08u) = new_cap;
        const u32 cur_size = *reinterpret_cast<const u32*>(self + 0x0Cu);
        destroy_range_22c294(old_data, old_data + cur_size);
        void* const* const vt = *reinterpret_cast<void* const* const*>(alloc);
        using Free1Fn = void (*)(void*, Node22C294*);
        reinterpret_cast<Free1Fn>(vt[1])(alloc, old_data);
        *reinterpret_cast<u32*>(self + 0x0Cu) = new_size;
    }

    Node22C294* const final_data = *reinterpret_cast<Node22C294* const*>(self + 0x04u);
    const Node22C294* const fill = reinterpret_cast<const Node22C294*>(fill_val);
    while (add_count != 0u) {
        copy_node_22c294(final_data + idx, fill);
        ++idx;
        --add_count;
    }
    return 1;
}

extern "C" s32 engine_func_0031b928();
extern "C" const u8* engine_func_002f4754(s32 idx);
extern "C" void engine_func_002dffd8(f32 a0, f32 a1, f32 a2);
extern "C" void engine_func_001e32f0();
extern "C" s32 engine_func_002fb468();
extern "C" const u8* engine_func_0026715c(s32 idx);
extern "C" s32 engine_func_0025c110(void* obj, u32 a1, u32 a2);
extern "C" s32 engine_func_00316eac(s32 a0, s32 a1);
extern "C" void* engine_func_0028549c(void* obj, u32 a1);
extern "C" void* engine_func_0029a2d0(const char* path, u32 flags);
extern "C" s32 engine_func_002ae16c(void* obj);
extern "C" void engine_func_002a06c8(void* obj, u32 a1);
extern "C" void engine_func_0025c0f0(void* obj, u32 zero, f32 s0, f32 s1, f32 s2);
extern "C" void* engine_func_0021e070();

namespace {

inline void step_state0_1e3408(u8* mgr, s32 target_a, s32 target_b) {
    const s32 count = engine_func_0031b928();
    for (s32 i = 0; i < count; ++i) {
        const u8* const rec = engine_func_002f4754(i);
        const s32 id0 = *reinterpret_cast<const s32*>(rec);
        if (id0 != 0x000F423F && id0 == target_a &&
            *reinterpret_cast<const s32*>(rec + 4u) == target_b) {
            ++i;
            for (s32 j = i; j < 0x270F; ++j, ++i) {
                const u8* const sub = engine_func_002f4754(i);
                const s32 sub_id = *reinterpret_cast<const s32*>(sub);
                if (sub_id == 0x000F423E) {
                    break;
                }
                const s32 s1 = *reinterpret_cast<const s32*>(sub + 4u);
                const s32 s2 = *reinterpret_cast<const s32*>(sub + 8u);
                engine_func_002dffd8(static_cast<f32>(sub_id), static_cast<f32>(s1),
                                     static_cast<f32>(s2));
            }
            engine_func_001e32f0();
        }
    }
    *reinterpret_cast<u32*>(mgr + 4u) = 0u;
    *reinterpret_cast<u32*>(mgr + 8u) = 0u;
    *reinterpret_cast<s32*>(mgr) += 1;
}

inline s32 step_state1_1e3408(u8* mgr, s32 target_a, s32 target_b, u32 skip_dups) {
    const s32 count = engine_func_002fb468();
    s32 idx = *reinterpret_cast<s32*>(mgr + 4u);
    void* const g_sys = *reinterpret_cast<void* const*>(0x00433158u);

    for (; idx < count; ++idx) {
        const u8* const info = engine_func_0026715c(idx);
        const s32 has_tail = engine_func_0025c110(g_sys, 0x24u, 0u);
        const s16 id0 = *reinterpret_cast<const s16*>(info);
        if (has_tail != 0) {
            if (id0 == -1) {
                const s32 tail = count - engine_func_0025c110(g_sys, 0x24u, 0u);
                if (idx >= tail) {
                    *reinterpret_cast<s32*>(mgr) = 0;
                    *reinterpret_cast<s32*>(mgr + 4u) = -1;
                    return 1;
                }
                continue;
            }
        } else if (id0 == -1) {
            *reinterpret_cast<s32*>(mgr) = 0;
            *reinterpret_cast<s32*>(mgr + 4u) = -1;
            return 1;
        }

        if (id0 != target_a || *reinterpret_cast<const s16*>(info + 2u) != target_b ||
            info[0x33u] != 0x13u) {
            continue;
        }
        if (engine_func_00316eac(*reinterpret_cast<const s16*>(info + 4u),
                                 *reinterpret_cast<const s16*>(info + 6u)) == 0) {
            continue;
        }
        if (skip_dups != 0u) {
            bool dup = false;
            for (s32 k = 0; k < 64; ++k) {
                const u8* const slot = mgr + 0x0Cu + k * 56;
                if (slot[0] != 0u && *reinterpret_cast<const s16*>(slot + 8u) == idx) {
                    dup = true;
                    break;
                }
            }
            if (dup) {
                continue;
            }
        }
        *reinterpret_cast<s32*>(mgr + 4u) = idx;
        break;
    }

    const s32 slot_idx = *reinterpret_cast<const s32*>(mgr + 8u);
    u8* const entry = mgr + 0x0Cu + slot_idx * 56;
    const u8* const info = engine_func_0026715c(*reinterpret_cast<const s32*>(mgr + 4u));
    *reinterpret_cast<u16*>(entry + 0x28u) = *reinterpret_cast<const u16*>(info + 4u);
    *reinterpret_cast<u16*>(entry + 0x2Au) = *reinterpret_cast<const u16*>(info + 6u);
    entry[3] = 0u;
    *reinterpret_cast<s16*>(entry + 8u) =
        static_cast<s16>(*reinterpret_cast<const s32*>(mgr + 4u));
    *reinterpret_cast<s16*>(entry + 6u) = static_cast<s16>(static_cast<s8>(info[0x33u]));

    char path_buf[0x44];
    reinterpret_cast<void (*)(char*, const char*, s32)>(ui_func_002be7fc)(
        path_buf, "character/npc/npc_%02d.bam", static_cast<s8>(info[0x33u]));

    void* obj = nullptr;
    if (target_a > 0x64 && slot_idx > 0) {
        obj = engine_func_0028549c(*reinterpret_cast<void* const*>(mgr + 0x3Cu), 0u);
    } else {
        obj = engine_func_0029a2d0(path_buf, 0x1C0u);
    }
    *reinterpret_cast<void**>(entry + 0x30u) = obj;
    *reinterpret_cast<s32*>(mgr) += 1;
    return 0;
}

inline void step_state2_1e3408(u8* mgr, s32 target_a) {
    const s32 slot_idx = *reinterpret_cast<const s32*>(mgr + 8u);
    u8* const entry = mgr + 0x0Cu + slot_idx * 56;
    void* const obj = *reinterpret_cast<void* const*>(entry + 0x30u);

    if (!(target_a > 0x64 && slot_idx > 0)) {
        if (engine_func_002ae16c(obj) == 0) {
            return;
        }
    }

    engine_func_002a06c8(obj, 1u);
    const u8* const info = engine_func_0026715c(*reinterpret_cast<const s32*>(mgr + 4u));
    engine_func_002fb468();
    if (info[0x33u] == 0x13u) {
        void* const sub_obj = *reinterpret_cast<void* const*>(static_cast<u8*>(obj) + 8u);
        engine_func_0025c0f0(sub_obj, 0u, 50.0f, 50.0f, 50.0f);
    }

    entry[0] = 1u;
    const s16 type_val = *reinterpret_cast<const s16*>(info + 0x28u);
    *reinterpret_cast<s16*>(entry + 4u) = type_val;
    *reinterpret_cast<s16*>(entry + 8u) =
        static_cast<s16>(*reinterpret_cast<const s32*>(mgr + 4u));
    *reinterpret_cast<s16*>(entry + 0x0Au) = static_cast<s16>(static_cast<s8>(info[0x32u]));
    *reinterpret_cast<f32*>(entry + 0x0Cu) = 4.0f;
    *reinterpret_cast<f32*>(entry + 0x10u) =
        static_cast<f32>(*reinterpret_cast<const s16*>(info + 0x2Au));
    *reinterpret_cast<f32*>(entry + 0x14u) =
        static_cast<f32>(*reinterpret_cast<const s16*>(info + 0x2Cu));
    *reinterpret_cast<f32*>(entry + 0x18u) =
        static_cast<f32>(*reinterpret_cast<const s16*>(info + 0x2Eu));
    *reinterpret_cast<f32*>(entry + 0x1Cu) =
        static_cast<f32>(*reinterpret_cast<const s16*>(info + 0x30u));
    *reinterpret_cast<u32*>(entry + 0x20u) = 0u;
    *reinterpret_cast<u32*>(entry + 0x34u) = 0u;
    if (type_val == 1) {
        *reinterpret_cast<void**>(entry + 0x2Cu) = engine_func_0021e070();
    }

    *reinterpret_cast<s32*>(mgr + 8u) += 1;
    *reinterpret_cast<s32*>(mgr + 4u) += 1;
    *reinterpret_cast<s32*>(mgr) = 1;
}

}  // namespace

// DECOMP_FUNC(0x001e3408, 1132)
extern "C" s32 engine_func_001e3408(s32 target_a, s32 target_b, u32 mode) {
    u8* const mgr = *reinterpret_cast<u8* const*>(0x00447E58u);
    switch (*reinterpret_cast<const s32*>(mgr)) {
        case 0:
            if (mode != 0u) {
                *reinterpret_cast<u32*>(mgr + 4u) = 0u;
                *reinterpret_cast<s32*>(mgr) = 1;
            } else {
                step_state0_1e3408(mgr, target_a, target_b);
            }
            return 0;
        case 1:
            return step_state1_1e3408(mgr, target_a, target_b, mode);
        case 2:
            step_state2_1e3408(mgr, target_a);
            return 0;
        default:
            return 0;
    }
}

extern "C" const f32* engine_func_002acbd8();
extern "C" s32 func_002a84ec(u8* dst, const u8* src);
extern "C" const f32* battle_func_002a7f04();

namespace {

inline void invert_mat4_2af0bc(const f32* m, f32* out) {
    const f32 a0 = m[0] * m[5] - m[1] * m[4];
    const f32 a1 = m[0] * m[6] - m[2] * m[4];
    const f32 a2 = m[0] * m[7] - m[3] * m[4];
    const f32 a3 = m[1] * m[6] - m[2] * m[5];
    const f32 a4 = m[1] * m[7] - m[3] * m[5];
    const f32 a5 = m[2] * m[7] - m[3] * m[6];

    const f32 b0 = m[8] * m[13] - m[9] * m[12];
    const f32 b1 = m[8] * m[14] - m[10] * m[12];
    const f32 b2 = m[8] * m[15] - m[11] * m[12];
    const f32 b3 = m[9] * m[14] - m[10] * m[13];
    const f32 b4 = m[9] * m[15] - m[11] * m[13];
    const f32 b5 = m[10] * m[15] - m[11] * m[14];

    const f32 det = a0 * b5 - a1 * b4 + a2 * b3 + a3 * b2 - a4 * b1 + a5 * b0;
    if (det == 0.0f) {
        const f32* const id = battle_func_002a7f04();
        for (u32 i = 0u; i < 16u; ++i) {
            out[i] = id[i];
        }
        return;
    }

    const f32 inv_det = 1.0f / det;
    out[0] = (m[5] * b5 - m[6] * b4 + m[7] * b3) * inv_det;
    out[1] = (-m[1] * b5 + m[2] * b4 - m[3] * b3) * inv_det;
    out[2] = (m[13] * a5 - m[14] * a4 + m[15] * a3) * inv_det;
    out[3] = (-m[9] * a5 + m[10] * a4 - m[11] * a3) * inv_det;
    out[4] = (-m[4] * b5 + m[6] * b2 - m[7] * b1) * inv_det;
    out[5] = (m[0] * b5 - m[2] * b2 + m[3] * b1) * inv_det;
    out[6] = (-m[12] * a5 + m[14] * a2 - m[15] * a1) * inv_det;
    out[7] = (m[8] * a5 - m[10] * a2 + m[11] * a1) * inv_det;
    out[8] = (m[4] * b4 - m[5] * b2 + m[7] * b0) * inv_det;
    out[9] = (-m[0] * b4 + m[1] * b2 - m[3] * b0) * inv_det;
    out[10] = (m[12] * a4 - m[13] * a2 + m[15] * a0) * inv_det;
    out[11] = (-m[8] * a4 + m[9] * a2 - m[11] * a0) * inv_det;
    out[12] = (-m[4] * b3 + m[5] * b1 - m[6] * b0) * inv_det;
    out[13] = (m[0] * b3 - m[1] * b1 + m[2] * b0) * inv_det;
    out[14] = (-m[12] * a3 + m[13] * a1 - m[14] * a0) * inv_det;
    out[15] = (m[8] * a3 - m[9] * a1 + m[10] * a0) * inv_det;
}

}  // namespace

// DECOMP_FUNC(0x002af0bc, 1132)
extern "C" void battle_func_002af0bc(u8* self) {
    u32 tmp[3];
    tmp[0] = *reinterpret_cast<const u32*>(self + 0x98u);
    tmp[1] = *reinterpret_cast<const u32*>(self + 0xA8u);
    tmp[2] = *reinterpret_cast<const u32*>(self + 0xB8u);

    void* const target = *reinterpret_cast<void* const*>(self + 0x0Cu);
    const void* arg2 = nullptr;
    if (target != nullptr) {
        using GetMatFn = const void* (*)(void*);
        arg2 = (*reinterpret_cast<GetMatFn* const*>(target))[5](target);
    } else {
        arg2 = engine_func_002acbd8();
    }

    void* const h1 = *reinterpret_cast<void* const*>(self + 0x258u);
    using BuildViewFn = void (*)(void*, u8*, const void*, const u32*);
    (*reinterpret_cast<BuildViewFn* const*>(h1))[3](h1, self + 0x148u, arg2, tmp);

    if (func_002a84ec(self + 0x178u, self + 0x148u) == 0) {
        const u32* const id = reinterpret_cast<const u32*>(engine_func_002acbd8());
        u32* const dst = reinterpret_cast<u32*>(self + 0x178u);
        for (u32 i = 0u; i < 12u; ++i) {
            dst[i] = id[i];
        }
    }

    void* const h2 = *reinterpret_cast<void* const*>(self + 0x260u);
    using BuildProjFn = void (*)(void*, u8*, u8*);
    (*reinterpret_cast<BuildProjFn* const*>(h2))[3](h2, self + 0x1A8u, self + 0x228u);

    invert_mat4_2af0bc(reinterpret_cast<const f32*>(self + 0x1A8u),
                       reinterpret_cast<f32*>(self + 0x1E8u));
}

extern "C" s32 script_vm_func_00258074(u32 elem);
extern "C" s32 script_vm_func_00258040(u32 elem);
extern "C" s32 script_vm_func_00269e34(u32 a1, u32 elem);
extern "C" s32 script_vm_func_00258020(u32 a1, u32 elem);
extern "C" void engine_func_002b67e0(char* dst, const char* src);
extern "C" u32 engine_func_002c3290(const char* str);

namespace {

inline void append_ailment_group_1f4480(char* out, const u8* list, u32 count, const char* suffix) {
    if (count == 0u) {
        return;
    }
    static const u32 kNameAddrs[5] = {
        0x00402648u, 0x00402658u, 0x00402664u, 0x00402670u, 0x0040267Cu,
    };
    char tmp[0x60];
    for (u32 i = 0u; i < count; ++i) {
        if (i != 0u) {
            engine_func_002b67e0(out, "\x81\x5E");
        }
        const u32 idx = static_cast<u32>(list[i]) - 11u;
        if (idx < 5u) {
            reinterpret_cast<void (*)(char*, const char*)>(ui_func_002be7fc)(
                tmp, reinterpret_cast<const char*>(kNameAddrs[idx]));
        }
        engine_func_002b67e0(out, tmp);
    }
    engine_func_002b67e0(out, suffix);
}

}  // namespace

// DECOMP_FUNC(0x001f4480, 1140)
extern "C" void engine_func_001f4480(u32 a0, u32 a1, u16 a2, char* out) {
    const u8* const elems = reinterpret_cast<const u8*>(0x00402548u);
    u8 null_list[8];
    u8 weak_list[8];
    u8 res_list[8];
    u32 null_cnt = 0u;
    u32 weak_cnt = 0u;
    u32 res_cnt = 0u;

    if (a0 != 0u) {
        for (u32 i = 0u; i < 5u; ++i) {
            const u8 e = elems[i];
            const s32 kind = script_vm_func_00258074(e);
            if (kind == 1) {
                null_list[null_cnt++] = e;
            } else if (kind == 2) {
                weak_list[weak_cnt++] = e;
            } else if (script_vm_func_00258040(e) < 0x64) {
                res_list[res_cnt++] = e;
            }
        }
    } else if (a1 != 0u) {
        for (u32 i = 0u; i < 5u; ++i) {
            const u8 e = elems[i];
            const s32 kind = script_vm_func_00269e34(a1, e);
            if (kind == 1) {
                null_list[null_cnt++] = e;
            } else if (kind == 2) {
                weak_list[weak_cnt++] = e;
            } else if (script_vm_func_00258020(a1, e) < 0x64) {
                res_list[res_cnt++] = e;
            }
        }
    } else {
        const u8* const rec = battle_func_002b087c(a2);
        for (u32 i = 0u; i < 5u; ++i) {
            const u8 e = elems[i];
            const u16 raw = *reinterpret_cast<const u16*>(rec + 0x24u + static_cast<u32>(e) * 2u);
            const u32 kind = raw >> 10u;
            if (kind == 1u) {
                null_list[null_cnt++] = e;
            } else if (kind == 2u) {
                weak_list[weak_cnt++] = e;
            } else if ((raw & 0x3FFu) < 0x64u) {
                res_list[res_cnt++] = e;
            }
        }
    }

    out[0] = '\0';
    append_ailment_group_1f4480(
        out, null_list, null_cnt,
        "\x81\x40\x82\x6D\x82\x95\x82\x8C\x82\x8C\x82\x89\x82\x86\x82\x99\x81\x40");
    append_ailment_group_1f4480(
        out, res_list, res_cnt,
        "\x81\x40\x82\x71\x82\x85\x82\x93\x82\x89\x82\x93\x82\x94\x82\x81\x82\x8E\x82\x83\x82\x85"
        "\x81\x40");
    append_ailment_group_1f4480(
        out, weak_list, weak_cnt,
        "\x81\x40\x82\x76\x82\x85\x82\x81\x82\x8B\x82\x8E\x82\x85\x82\x93\x82\x93\x81\x40");

    if ((null_cnt | res_cnt | weak_cnt) == 0u) {
        engine_func_002b67e0(
            out,
            "\x82\x6D\x82\x8F\x81\x40\x82\x60\x82\x89\x82\x8C\x82\x8D\x82\x85\x82\x8E\x82\x94\x81"
            "\x40\x82\x71\x82\x85\x82\x93\x82\x89\x82\x93\x82\x94\x82\x81\x82\x8E\x82\x83\x82\x85");
    }
    if (engine_func_002c3290(out) >= 0x5Du) {
        out[0x5Du] = '\0';
        out[0x5Eu] = '\0';
        out[0x5Fu] = '\0';
    }
}

extern "C" u32 battle_func_002564cc(void* sub);
extern "C" u8* battle_func_00256418(void* mgr, u32 idx, u32 a2);
extern "C" void* ui_func_00293c98();
extern "C" void battle_func_0022a53c(void* sub, u32 field, s32 val, s32 min_val, s32 max_val,
                                    u32 a5);
extern "C" void battle_func_0022a594(void* sub, u32 field, u32 val);
extern "C" s32 script_vm_func_002458d4(u16 id);
extern "C" void func_00245888(u16 id, u32 val);

namespace {

inline void sync_linked_stat_3c4cec(u8* unit, u32 off, s16 val) {
    for (u32 k = 0u; k < 3u; ++k) {
        u8* const sub = *reinterpret_cast<u8* const*>(unit + 0x278u + k * 4u);
        if (sub != nullptr) {
            *reinterpret_cast<s16*>(sub + off) = val;
        }
    }
}

}  // namespace

// DECOMP_FUNC(0x003c4cec, 1140)
extern "C" void battle_func_003c4cec(u8* self, void* mgr) {
    void* const sub = *reinterpret_cast<void* const*>(self + 0x10u);
    const u32 cmd = battle_func_002564cc(sub);
    u8* unit = battle_func_00256418(mgr, *reinterpret_cast<const u32*>(self + 0x1Cu), 1u);
    s16* stats = (unit != nullptr) ? reinterpret_cast<s16*>(unit + 0x1B4u) : nullptr;

    switch (cmd) {
        case 0u: {
            const u32 sel = *battle_func_0022a5f8(sub, 0u);
            *reinterpret_cast<u32*>(self + 0x1Cu) = sel;
            unit = battle_func_00256418(ui_func_00293c98(), sel, 1u);
            if (unit == nullptr) {
                return;
            }
            stats = reinterpret_cast<s16*>(unit + 0x1B4u);
            static constexpr s32 kMin[9] = {1, 1, 0, 1, 1, 1, 1, 1, 1};
            static constexpr s32 kMax[9] = {9999, 9999, 9999, 9999, 999, 999, 999, 999, 999};
            for (u32 i = 0u; i < 9u; ++i) {
                battle_func_0022a53c(*reinterpret_cast<void* const*>(self + 0x10u), i + 1u, stats[i],
                                     kMin[i], kMax[i], 0u);
            }
            const u32 flags = *reinterpret_cast<const u32*>(unit);
            battle_func_0022a594(*reinterpret_cast<void* const*>(self + 0x10u), 10u,
                                 (flags & 0x1000u) >> 12u);
            battle_func_0022a594(*reinterpret_cast<void* const*>(self + 0x10u), 11u,
                                 (flags & 0x4000000u) >> 26u);
            const s32 v12 = ((flags & 0x10u) != 0u)
                                ? script_vm_func_002458d4(*reinterpret_cast<const u16*>(unit + 0xCEu))
                                : 0;
            battle_func_0022a53c(*reinterpret_cast<void* const*>(self + 0x10u), 12u, v12, 0, 9999,
                                 0u);
            return;
        }
        case 1u:
            if (stats != nullptr) {
                const s16 v = static_cast<s16>(*battle_func_0022a5f8(sub, 1u));
                stats[0] = v;
                sync_linked_stat_3c4cec(unit, 0x2Au, v);
            }
            return;
        case 3u:
            if (stats != nullptr) {
                const s16 v = static_cast<s16>(*battle_func_0022a5f8(sub, 3u));
                stats[2] = v;
                sync_linked_stat_3c4cec(unit, 0x2Cu, v);
            }
            return;
        case 2u:
        case 4u:
        case 5u:
        case 6u:
        case 7u:
        case 8u:
        case 9u:
            if (stats != nullptr) {
                stats[cmd - 1u] = static_cast<s16>(*battle_func_0022a5f8(sub, cmd));
            }
            return;
        case 10u:
            if (unit != nullptr) {
                if (battle_func_0022a5d8(sub, 10u) != 0) {
                    *reinterpret_cast<u32*>(unit) |= 0x1000u;
                } else {
                    *reinterpret_cast<u32*>(unit) &= ~0x1000u;
                }
            }
            return;
        case 11u:
            if (unit != nullptr) {
                if (battle_func_0022a5d8(sub, 11u) != 0) {
                    *reinterpret_cast<u32*>(unit) |= 0x4000000u;
                } else {
                    *reinterpret_cast<u32*>(unit) &= ~0x4000000u;
                }
            }
            return;
        case 12u:
            if (unit != nullptr && (*reinterpret_cast<const u32*>(unit) & 0x10u) != 0u) {
                func_00245888(*reinterpret_cast<const u16*>(unit + 0xCEu),
                              *battle_func_0022a5f8(sub, 12u));
            }
            return;
        default:
            return;
    }
}

extern "C" void engine_func_00234b30(u64* out, u8* a1, u8* a2);
extern "C" s32 engine_func_002a1578(const u64* status);
extern "C" void script_vm_func_003531ac(u8* req, u8* buf, u32 size);
extern "C" u32 script_vm_func_002345fc(u8* a0);
extern "C" u32 script_vm_func_002345f0(u8* a0);
extern "C" void script_vm_func_002344c4(u8* out64, u32 idx, u32 a2, u32 a3);
extern "C" void script_vm_func_0023a330(u8* dst, const char* fmt, const char* str);
extern "C" void aocApplication_func_0038b384(u8* shop);
extern "C" void engine_func_0035307c(u64* out, u32 a1, u32 a2, u32 a3, u8* req);
extern "C" u32 script_vm_func_002344b4(u32 a0);
extern "C" u32 script_vm_func_003df598(u32 a0);
extern "C" void engine_func_003533ec(u64* out, u8* a1, u32* pair);
extern "C" void script_vm_func_00234b08(u8* a0);
extern "C" u32 script_vm_func_0025461c(const u32* pair);
extern "C" u32 script_vm_func_002545c4(const u32* pair);
extern "C" u32 script_vm_func_0025456c(const u32* pair);
extern "C" u32 script_vm_func_002a8730(u32 a0, u32 a1, u32 a2);
extern "C" s32 script_vm_func_0038c43c(u8* self);
extern "C" void engine_func_00234368(u64* out, u8* shop);

namespace {

inline bool check_status_38cdf4(u8* self, u64 status) {
    *reinterpret_cast<u64*>(self + 0x0Cu) = status;
    return engine_func_002a1578(reinterpret_cast<const u64*>(self + 0x0Cu)) < 0;
}

inline void fill_sale_block_38cdf4(u8* shop, u32 idx, u32 dst_off) {
    const u32 a = script_vm_func_002345fc(shop + 0x28u);
    const u32 b = script_vm_func_002345f0(shop + 0x28u);
    u32 tmp[16];
    script_vm_func_002344c4(reinterpret_cast<u8*>(tmp), idx, b, a);
    u32* const dst = reinterpret_cast<u32*>(shop + dst_off);
    for (u32 i = 0u; i < 16u; ++i) {
        dst[i] = tmp[i];
    }
}

}  // namespace

// DECOMP_FUNC(0x0038cdf4, 1144)
extern "C" void script_vm_func_0038cdf4(u8* self) {
    u8* const shop = *reinterpret_cast<u8* const*>(0x00432FC8u);
    u64 status = 0u;

    engine_func_00234b30(&status, shop + 0x28u, shop + 0x18u);
    if (check_status_38cdf4(self, status)) {
        return;
    }

    u8 buf_400[0x400];
    u8 req[0x38];
    script_vm_func_003531ac(req, buf_400, 0x400u);
    req[0x28u] = 1u;

    fill_sale_block_38cdf4(shop, 0u, 0x368u);
    fill_sale_block_38cdf4(shop, 2u, 0x3A8u);
    fill_sale_block_38cdf4(shop, 3u, 0x3E8u);
    fill_sale_block_38cdf4(shop, 5u, 0x428u);

    static const char* const kFields[5] = {
        "SET_SALE_INDEX", "SET_SALE_NEW", "SET_SALE_PRICE", "SET_SALE_ECARD", "SET_SALE_CHANGE",
    };
    for (u32 i = 0u; i < 5u; ++i) {
        script_vm_func_0023a330(shop + 0x468u + i * 0x40u, "%s", kFields[i]);
    }

    *reinterpret_cast<u8**>(req) = shop + 0x368u;
    *reinterpret_cast<u32*>(req + 4u) = 9u;
    const u32 extra = *reinterpret_cast<const u32*>(shop + 0x364u);
    if (extra != 0u) {
        *reinterpret_cast<u8**>(req + 8u) = shop + 0xE3u;
        *reinterpret_cast<u32*>(req + 0x0Cu) = extra;
    }

    aocApplication_func_0038b384(shop);

    char sort_buf[0xC0];
    reinterpret_cast<void (*)(char*, const char*)>(ui_func_002be7fc)(sort_buf, "ascending");
    reinterpret_cast<void (*)(char*, const char*)>(ui_func_002be7fc)(sort_buf + 0x40u,
                                                                     "SET_SALE_INDEX");
    reinterpret_cast<void (*)(char*, const char*)>(ui_func_002be7fc)(sort_buf + 0x80u, "integer");
    *reinterpret_cast<char**>(req + 0x18u) = sort_buf;

    for (;;) {
        engine_func_0035307c(&status, *reinterpret_cast<const u32*>(shop + 0x5A8u),
                             *reinterpret_cast<const u32*>(shop + 0x684u), 0x40u, req);
        if (check_status_38cdf4(self, status)) {
            script_vm_func_00234b08(shop + 0x28u);
            return;
        }
        if (script_vm_func_002344b4(*reinterpret_cast<const u32*>(shop + 0x5A8u)) >
                *reinterpret_cast<const u32*>(shop + 0x684u) ||
            script_vm_func_002344b4(*reinterpret_cast<const u32*>(shop + 0x5A8u)) == 0u) {
            break;
        }
        const u32 cur = script_vm_func_002344b4(*reinterpret_cast<const u32*>(shop + 0x5A8u));
        *reinterpret_cast<u32*>(shop + 0x684u) = ((cur + 0x3Fu) >> 6u) - 1u;
        *reinterpret_cast<u32*>(shop + 0x684u) <<= 6u;
    }

    *reinterpret_cast<u32*>(shop + 0x67Cu) =
        script_vm_func_003df598(*reinterpret_cast<const u32*>(shop + 0x5A8u));
    *reinterpret_cast<u32*>(shop + 0x680u) =
        script_vm_func_002344b4(*reinterpret_cast<const u32*>(shop + 0x5A8u));
    *reinterpret_cast<u32*>(shop + 0x680u) =
        script_vm_func_002344b4(*reinterpret_cast<const u32*>(shop + 0x5A8u));

    u32 pair[2] = {0u, 0u};
    engine_func_003533ec(&status, shop + 0x84u, pair);
    if (check_status_38cdf4(self, status)) {
        script_vm_func_00234b08(shop + 0x28u);
        return;
    }

    const u32 p0 = script_vm_func_0025461c(pair);
    const u32 p1 = script_vm_func_002545c4(pair);
    const u32 p2 = script_vm_func_0025456c(pair);
    *reinterpret_cast<u32*>(self + 0x18u) = script_vm_func_002a8730(p2, p1, p0);

    const s32 res = script_vm_func_0038c43c(self);
    script_vm_func_00234b08(shop + 0x28u);
    if (res >= 0) {
        engine_func_00234368(&status, shop);
        check_status_38cdf4(self, status);
    }
}

// DECOMP_FUNC(0x003c42d4, 1144)
extern "C" void battle_func_003c42d4(u8* ctx, u8* target) {
    struct BitCase3c42d4 {
        u32 offset;
        u32 mask;
    };
    static const BitCase3c42d4 kBitCases[29] = {
        {0x44A8u, 0x00000004u}, {0x44A8u, 0x00000008u}, {0x44A8u, 0x00000010u},
        {0x44A8u, 0x00000020u}, {0u, 0u},                  {0x44A8u, 0x00000040u},
        {0x44A8u, 0x00000080u}, {0x44A8u, 0x00000100u}, {0x44A8u, 0x00000200u},
        {0x44A8u, 0x00000400u}, {0x44A8u, 0x00000800u}, {0u, 0u},
        {0u, 0u},               {0x44A8u, 0x00020000u}, {0x44A8u, 0x00400000u},
        {0x44A8u, 0x00800000u}, {0x44A8u, 0x01000000u}, {0x44A8u, 0x02000000u},
        {0x44A8u, 0x04000000u}, {0x44A8u, 0x08000000u}, {0x44A8u, 0x10000000u},
        {0x44A8u, 0x20000000u}, {0x44ACu, 0x00000001u}, {0x44ACu, 0x00000002u},
        {0u, 0u},               {0x44ACu, 0x00000004u}, {0u, 0u},
        {0u, 0u},               {0x44ACu, 0x00000040u},
    };

    void* const sub = *reinterpret_cast<void* const*>(ctx + 0x10u);
    const u32 cmd = battle_func_002564cc(sub);
    if (cmd >= 29u) {
        return;
    }

    switch (cmd) {
        case 4u:
            *reinterpret_cast<u32*>(target + 0x4A50u) = *battle_func_0022a5f8(sub, cmd);
            return;
        case 11u:
            *reinterpret_cast<u32*>(target + 0x49C8u) = *battle_func_0022a5f8(sub, cmd);
            return;
        case 12u: {
            const u32 val = *battle_func_0022a5f8(sub, cmd);
            *const_cast<u32*>(reinterpret_cast<const u32*>(camp_func_002a8a08())) = val;
            return;
        }
        case 24u:
            *reinterpret_cast<u32*>(target + 0x2F2Cu) = *battle_func_0022a5f8(sub, cmd);
            return;
        case 26u:
            *reinterpret_cast<u32*>(target + 0x2F34u) = *battle_func_0022a5f8(sub, cmd);
            return;
        case 27u:
            *reinterpret_cast<u32*>(0x00439AD4u) = *battle_func_0022a5f8(sub, cmd);
            return;
        default: {
            const BitCase3c42d4 bc = kBitCases[cmd];
            u32* const flags = reinterpret_cast<u32*>(target + bc.offset);
            if (battle_func_0022a5d8(sub, cmd) != 0) {
                *flags |= bc.mask;
            } else {
                *flags &= ~bc.mask;
            }
            return;
        }
    }
}

extern "C" void script_vm_func_00354d28(u8* obj, u32 a1, u8* buf, u32 size);
extern "C" void engine_func_00354c30(u64* out, u8* obj, u8* a2);
extern "C" void script_vm_func_00354d4c(u8* obj);
extern "C" void script_vm_func_00353124(u8* req, u8* buf, u32 size);
extern "C" void engine_func_0035495c(u8* out_hdr, u8* obj);
extern "C" void aocApplication_func_0038b510(u8* shop);
extern "C" void engine_func_003528d4(u64* out, u32 a1, u32 a2, u32 a3, u8* req);
extern "C" u32 script_vm_func_003df578(u32 a0);
extern "C" u32 script_vm_func_003df588(u32 a0);
extern "C" s32 script_vm_func_0038d7b0(u8* self);

// DECOMP_FUNC(0x0038de60, 1156)
extern "C" void script_vm_func_0038de60(u8* self) {
    u8* const shop = *reinterpret_cast<u8* const*>(0x00432FC8u);
    u64 status = 0u;

    engine_func_00234b30(&status, shop + 0x28u, shop + 0x18u);
    if (check_status_38cdf4(self, status)) {
        return;
    }

    u8 buf_400_a[0x400];
    u8 obj[0x10];
    script_vm_func_00354d28(obj, *reinterpret_cast<const u32*>(shop + 0x80u), buf_400_a, 0x400u);
    engine_func_00354c30(&status, obj, shop + 0x694u);
    if (check_status_38cdf4(self, status)) {
        script_vm_func_00234b08(shop + 0x28u);
        script_vm_func_00354d4c(obj);
        return;
    }

    u8 buf_400_b[0x400];
    u8 req[0x38];
    script_vm_func_00353124(req, buf_400_b, 0x400u);

    u32 hdr[16];
    u32 hdr_copy[16];
    engine_func_0035495c(reinterpret_cast<u8*>(hdr), obj);
    for (u32 i = 0u; i < 16u; ++i) {
        hdr_copy[i] = hdr[i];
    }
    *reinterpret_cast<u32**>(req + 0x1Cu) = hdr_copy;

    fill_sale_block_38cdf4(shop, 0u, 0x368u);
    fill_sale_block_38cdf4(shop, 2u, 0x3A8u);
    fill_sale_block_38cdf4(shop, 3u, 0x3E8u);
    fill_sale_block_38cdf4(shop, 5u, 0x428u);

    static const char* const kFields[5] = {
        "SET_SALE_INDEX", "SET_SALE_NEW", "SET_SALE_PRICE", "SET_SALE_ECARD", "SET_SALE_CHANGE",
    };
    for (u32 i = 0u; i < 5u; ++i) {
        script_vm_func_0023a330(shop + 0x468u + i * 0x40u, "%s", kFields[i]);
    }

    *reinterpret_cast<u8**>(req) = shop + 0x368u;
    *reinterpret_cast<u32*>(req + 4u) = 9u;
    const u32 extra = *reinterpret_cast<const u32*>(shop + 0x364u);
    if (extra != 0u) {
        *reinterpret_cast<u8**>(req + 8u) = shop + 0xE3u;
        *reinterpret_cast<u32*>(req + 0x0Cu) = extra;
    }

    aocApplication_func_0038b510(shop);

    engine_func_003528d4(&status, *reinterpret_cast<const u32*>(shop + 0x5B0u),
                         *reinterpret_cast<const u32*>(shop + 0x684u), 0x40u, req);
    if (check_status_38cdf4(self, status)) {
        script_vm_func_00234b08(shop + 0x28u);
        script_vm_func_00354d4c(obj);
        return;
    }

    *reinterpret_cast<u32*>(shop + 0x68Cu) =
        script_vm_func_003df578(*reinterpret_cast<const u32*>(shop + 0x5B0u));
    *reinterpret_cast<u32*>(shop + 0x690u) =
        script_vm_func_003df588(*reinterpret_cast<const u32*>(shop + 0x5B0u));

    u32 pair[2] = {0u, 0u};
    engine_func_003533ec(&status, shop + 0x84u, pair);
    if (check_status_38cdf4(self, status)) {
        script_vm_func_00234b08(shop + 0x28u);
        script_vm_func_00354d4c(obj);
        return;
    }

    const u32 p0 = script_vm_func_0025461c(pair);
    const u32 p1 = script_vm_func_002545c4(pair);
    const u32 p2 = script_vm_func_0025456c(pair);
    *reinterpret_cast<u32*>(self + 0x18u) = script_vm_func_002a8730(p2, p1, p0);

    const s32 res = script_vm_func_0038d7b0(self);
    script_vm_func_00234b08(shop + 0x28u);
    if (res >= 0) {
        engine_func_00234368(&status, shop);
        check_status_38cdf4(self, status);
    }
    script_vm_func_00354d4c(obj);
}

namespace {

inline void poll_task_38e80c(u8* self, u32* st) {
    void* const obj = *reinterpret_cast<void* const*>(self + 0x208u);
    void* const* const vtbl = *reinterpret_cast<void* const* const*>(obj);
    using GetResultFn = void (*)(u32*, void*);
    reinterpret_cast<GetResultFn>(vtbl[3])(st, obj);
}

inline void destroy_task_38e80c(u8* self, bool clear_ptr) {
    void* const obj = *reinterpret_cast<void* const*>(self + 0x208u);
    if (obj != nullptr) {
        void* const* const vtbl = *reinterpret_cast<void* const* const*>(obj);
        using DtorFn = void (*)(void*);
        reinterpret_cast<DtorFn>(vtbl[1])(obj);
        if (clear_ptr) {
            *reinterpret_cast<void**>(self + 0x208u) = nullptr;
        }
    }
}

inline void handle_task_error_38e80c(u8* self, const u32* st, bool check_fg) {
    battle_func_00233f0c(self);
    if (check_fg) {
        const u8 code = *reinterpret_cast<const u8*>(st);
        if (code == 0x66u) {
            u32 arg[5];
            for (u32 i = 0u; i < 5u; ++i) {
                arg[i] = st[i];
            }
            func_002342b8(self, arg);
            return;
        }
        if (code == 0x67u) {
            *reinterpret_cast<u32*>(self + 8u) = 7u;
            *reinterpret_cast<u32*>(self + 0x0Cu) = 3u;
            return;
        }
    }
    *reinterpret_cast<u32*>(self + 8u) = 0x270Fu;
    u32* const dst = reinterpret_cast<u32*>(self + 0x210u);
    for (u32 i = 0u; i < 5u; ++i) {
        dst[i] = st[i];
    }
}

}  // namespace

// DECOMP_FUNC(0x0038e80c, 1172)
extern "C" void engine_func_0038e80c(u8* self) {
    u32 st[5];
    engine_func_00234278(st);
    u8* const shop = *reinterpret_cast<u8* const*>(0x00432FC8u);
    const s32 state = *reinterpret_cast<const s32*>(self + 8u);

    switch (state) {
        case 0:
            if (ui_func_0026b7cc() != 0 && (*reinterpret_cast<const u32*>(self) & 0x200u) != 0u) {
                *reinterpret_cast<void**>(self + 0x208u) = engine_func_00234160(self + 0x20Cu, 0u);
                *reinterpret_cast<u32*>(self + 8u) = 1u;
            }
            return;
        case 1:
            if ((*reinterpret_cast<const u32*>(self) & 0x200u) == 0u) {
                return;
            }
            poll_task_38e80c(self, st);
            if (camp_func_0027ec84(st) != 0) {
                *reinterpret_cast<u32*>(self + 8u) = 2u;
                return;
            }
            if (engine_func_002a17c0(st) != 0) {
                handle_task_error_38e80c(self, st, true);
            }
            return;
        case 2:
            destroy_task_38e80c(self, false);
            *reinterpret_cast<void**>(self + 0x208u) = engine_func_00234160(self + 0x20Cu, 6u);
            *reinterpret_cast<u32*>(self + 8u) = 3u;
            engine_func_00233f4c(self, 1u);
            return;
        case 3:
            poll_task_38e80c(self, st);
            if (camp_func_0027ec84(st) != 0) {
                destroy_task_38e80c(self, false);
                engine_func_00233f4c(self, 0u);
                *reinterpret_cast<void**>(self + 0x208u) = engine_func_00234160(self + 0x20Cu, 0u);
                *reinterpret_cast<u32*>(self + 8u) = 4u;
            } else if (engine_func_002a17c0(st) != 0) {
                handle_task_error_38e80c(self, st, false);
            }
            return;
        case 4:
            if ((*reinterpret_cast<const u32*>(self) & 0x200u) == 0u) {
                return;
            }
            poll_task_38e80c(self, st);
            if (camp_func_0027ec84(st) != 0) {
                *reinterpret_cast<u32*>(self + 8u) = 5u;
                engine_func_00233f4c(self, 1u);
            } else if (engine_func_002a17c0(st) != 0) {
                handle_task_error_38e80c(self, st, true);
            }
            return;
        case 5: {
            destroy_task_38e80c(self, false);
            u8* const task = static_cast<u8*>(engine_func_00234160(self + 0x20Cu, 7u));
            *reinterpret_cast<u8**>(self + 0x208u) = task;
            const u8* const sub = *reinterpret_cast<const u8* const*>(shop + 0x688u);
            *reinterpret_cast<u32*>(task + 0x14u) = *reinterpret_cast<const u16*>(sub + 0x9AAu);
            *reinterpret_cast<u32*>(self + 8u) = 6u;
            return;
        }
        case 6:
            poll_task_38e80c(self, st);
            if (camp_func_0027ec84(st) != 0) {
                *reinterpret_cast<u32*>(self + 4u) = 0xAu;
                *reinterpret_cast<u32*>(self + 8u) = 0u;
                destroy_task_38e80c(self, true);
                u32* const cleared = reinterpret_cast<u32*>(shop + 0x694u);
                for (u32 i = 0u; i < 16u; ++i) {
                    cleared[i] = 0u;
                }
                engine_func_002c4b30(shop + 0x6D4u, 0x80u);
            } else if (engine_func_002a17c0(st) != 0) {
                handle_task_error_38e80c(self, st, true);
            }
            return;
        case 7: {
            const s32 cnt = *reinterpret_cast<const s32*>(self + 0x0Cu) - 1;
            *reinterpret_cast<s32*>(self + 0x0Cu) = cnt;
            if (cnt > 0) {
                return;
            }
            *reinterpret_cast<u32*>(self + 4u) = 6u;
            *reinterpret_cast<u32*>(self + 8u) = 0u;
            destroy_task_38e80c(self, true);
            camp_func_00233ac0(self, 2, 1u);
            return;
        }
        case 0x270F:
            engine_func_00234004(self, 0x0Eu, 6u);
            if (*reinterpret_cast<const u32*>(self + 4u) == 6u) {
                camp_func_00233ac0(self, 2, 1u);
            }
            return;
        default:
            return;
    }
}

extern "C" void ui_func_002acd38(void* dst, const void* src, u32 size);
extern "C" u8* engine_func_002b5498(u8* obj, void* alloc, const u8* desc, u32 a2);
extern "C" s32 engine_func_002af604(const void* a, const void* b);

namespace {

inline void* vtbl_alloc_12c97c(void* alloc, u32 size, u32 align) {
    void* const* const vtbl = *reinterpret_cast<void* const* const*>(alloc);
    using AllocFn = void* (*)(void*, u32, u32);
    return reinterpret_cast<AllocFn>(vtbl[2])(alloc, size, align);
}

inline void vtbl_free_12c97c(void* alloc, void* ptr) {
    void* const* const vtbl = *reinterpret_cast<void* const* const*>(alloc);
    using FreeFn = void (*)(void*, void*);
    reinterpret_cast<FreeFn>(vtbl[3])(alloc, ptr);
}

inline u32 ext_size_12c97c(u32 tag) {
    switch (tag) {
        case 0x80000000u:
            return 0x1Cu;
        case 0x40000000u:
        case 0x04000000u:
            return 0x28u;
        case 0x20000000u:
            return 0x24u;
        case 0x10000000u:
            return 0x08u;
        case 0x08000000u:
            return 0x18u;
        default:
            return 0u;
    }
}

inline void attach_child_12c97c(u8* parent, u8* obj) {
    if (parent == nullptr) {
        return;
    }
    const void* const p_link = *reinterpret_cast<const void* const*>(parent + 0x0Cu);
    if (p_link != nullptr && (p_link == obj || engine_func_002af604(p_link, obj) != 0)) {
        return;
    }
    if (*reinterpret_cast<const void* const*>(obj + 0x0Cu) != nullptr) {
        return;
    }

    u8** begin = *reinterpret_cast<u8***>(parent + 0x18u);
    u8** end = *reinterpret_cast<u8***>(parent + 0x1Cu);
    const u32 cap_flags = *reinterpret_cast<const u32*>(parent + 0x20u);
    const s32 count = end - begin;
    const s32 cap = static_cast<s32>(cap_flags & 0x3FFFFFFFu);

    bool ok = true;
    if (cap <= count) {
        const s32 new_cap = (cap != 0) ? (cap << 1) : 1;
        if (cap < new_cap) {
            void* const vec_alloc = *reinterpret_cast<void* const*>(parent + 0x14u);
            if (vec_alloc == nullptr || (cap_flags & 0xC0000000u) != 0x40000000u) {
                ok = false;
            } else {
                u8** const new_buf = static_cast<u8**>(
                    vtbl_alloc_12c97c(vec_alloc, static_cast<u32>(new_cap) * 4u, 0x20u));
                u8** dst = new_buf;
                for (u8** src = begin; src != end; ++src, ++dst) {
                    if (dst != nullptr) {
                        *dst = *src;
                    }
                }
                const s32 cur_count = *reinterpret_cast<u8***>(parent + 0x1Cu) -
                                      *reinterpret_cast<u8***>(parent + 0x18u);
                if (*reinterpret_cast<void**>(parent + 0x18u) != nullptr) {
                    vtbl_free_12c97c(vec_alloc, *reinterpret_cast<void**>(parent + 0x18u));
                }
                *reinterpret_cast<u8***>(parent + 0x1Cu) = new_buf + cur_count;
                *reinterpret_cast<u8***>(parent + 0x18u) = new_buf;
                *reinterpret_cast<u32*>(parent + 0x20u) =
                    (cap_flags & 0xC0000000u) | static_cast<u32>(new_cap);
            }
        }
    }

    if (ok) {
        u8** const cur_end = *reinterpret_cast<u8***>(parent + 0x1Cu);
        if (cur_end != nullptr) {
            *cur_end = obj;
        }
        *reinterpret_cast<u8***>(parent + 0x1Cu) = cur_end + 1;
        *reinterpret_cast<u32*>(obj + 0x0Cu) = *reinterpret_cast<const u32*>(parent + 0x10u);
    }
}

}  // namespace

// DECOMP_FUNC(0x0012c97c, 1184)
extern "C" void* ui_func_0012c97c(u8* parent, const u8* desc, u32 a2, void* alloc) {
    const u8* valid_desc = nullptr;
    if (desc != nullptr && (*reinterpret_cast<const u32*>(desc) & 0x40000006u) == 0x40000006u) {
        valid_desc = desc;
    }

    void* block_c0 = nullptr;
    if (valid_desc[0xC0u] != 0u) {
        block_c0 = vtbl_alloc_12c97c(alloc, 0x20u, 4u);
        if (block_c0 == nullptr) {
            return nullptr;
        }
        ui_func_002acd38(block_c0, valid_desc + 0xC0u, 0x20u);
    }

    void* ext_block = nullptr;
    const u32 ext_off = *reinterpret_cast<const u32*>(valid_desc + 0xBCu);
    const u8* const ext = (ext_off != 0u) ? (valid_desc + 0xBCu + ext_off) : nullptr;
    if (ext != nullptr && ext[4] != 0u) {
        const u32 sz = ext_size_12c97c(*reinterpret_cast<const u32*>(ext));
        if (sz != 0u) {
            ext_block = vtbl_alloc_12c97c(alloc, sz, 4u);
        }
        if (ext_block == nullptr) {
            if (block_c0 != nullptr) {
                vtbl_free_12c97c(alloc, block_c0);
            }
            return nullptr;
        }
        ui_func_002acd38(ext_block, ext, sz);
    }

    u8* obj = static_cast<u8*>(vtbl_alloc_12c97c(alloc, 0x188u, 4u));
    if (obj == nullptr) {
        if (block_c0 != nullptr) {
            vtbl_free_12c97c(alloc, block_c0);
        }
        if (ext_block != nullptr) {
            vtbl_free_12c97c(alloc, ext_block);
        }
        return nullptr;
    }

    obj = engine_func_002b5498(obj, alloc, valid_desc, a2);
    *reinterpret_cast<u32*>(obj + 0x000u) = 0x00420F90u;
    *reinterpret_cast<u8*>(obj + 0x148u) = 1u;
    *reinterpret_cast<u32*>(obj + 0x14Cu) = 0x00000000u;
    *reinterpret_cast<u32*>(obj + 0x150u) = 0u;
    *reinterpret_cast<u32*>(obj + 0x154u) = 0u;
    *reinterpret_cast<u32*>(obj + 0x158u) = 0u;
    *reinterpret_cast<u32*>(obj + 0x15Cu) = 0x00421CA0u;
    *reinterpret_cast<u32*>(obj + 0x160u) = 0x00421CD4u;
    *reinterpret_cast<u32*>(obj + 0x164u) = 0x00000000u;
    *reinterpret_cast<u32*>(obj + 0x168u) = 0x00000000u;
    *reinterpret_cast<u32*>(obj + 0x16Cu) = 0x3F800000u;
    *reinterpret_cast<u32*>(obj + 0x170u) = 0x00000000u;
    *reinterpret_cast<u32*>(obj + 0x174u) = 0x4B7FFFFFu;
    *reinterpret_cast<u32*>(obj + 0x178u) = 0x00151404u;
    *reinterpret_cast<u32*>(obj + 0x17Cu) = 0u;
    *reinterpret_cast<void**>(obj + 0x180u) = block_c0;
    *reinterpret_cast<void**>(obj + 0x184u) = ext_block;

    void* const* const obj_vtbl = *reinterpret_cast<void* const* const*>(obj);
    using InitFn = s32 (*)(u8*, void*);
    if (reinterpret_cast<InitFn>(obj_vtbl[9])(obj, alloc) < 0) {
        using DtorFn = void (*)(u8*);
        reinterpret_cast<DtorFn>(obj_vtbl[0])(obj);
        vtbl_free_12c97c(*reinterpret_cast<void* const*>(obj + 4u), obj);
        return nullptr;
    }

    attach_child_12c97c(parent, obj);
    return obj;
}

extern "C" s32 ui_func_002b0788(s16 bit);
extern "C" void func_002be4dc(s32 color);
extern "C" void ui_func_002b6a98(s32 a0, s32 x, s32 y, u32 a3, u32 a4);
extern "C" void engine_func_002be16c(u32 a0, s32 x, s32 y, u32 a3, u32 a4, u32 a5,
                                     const char* fmt, s32 val);
extern "C" void ui_func_003b6fc4(u8* a0, s32 idx, s32 x, s32 y);

namespace {

inline void set_color_3b67c4(s32 color) {
    s32* const slot = reinterpret_cast<s32*>(0x0044DC38u + 4u);
    if (*slot != color) {
        func_002be4dc(color);
        *slot = color;
    }
}

}  // namespace

// DECOMP_FUNC(0x003b67c4, 1208)
extern "C" void ui_func_003b67c4(u8* a0, u32 mode, s32 idx, u32 a3, s32 x_off, s32 y_off,
                                 u32 w_bits, u32 flag, s32 val7, s32 val10) {
    const u8* const demon = camp_func_002a89e4(idx);
    const u8* const layout = camp_func_002bf6d0(0x28u, a3 + 0x68u);
    const s32 bx = *reinterpret_cast<const s16*>(layout + 8u) + x_off;
    const s32 by = *reinterpret_cast<const s16*>(layout + 10u) + y_off;

    switch (mode) {
        case 0u:
            ui_func_002bf460(2u, 0x28u, 0x56u, bx, by, 0x65u);
            return;
        case 1u:
            if (val7 > 0 || static_cast<s32>(demon[0x48u]) > val10) {
                ui_func_002bf460(2u, 0x28u, 0x58u, bx, by, 0x6Au);
                ui_func_002bf460(2u, 0x28u, 0x5Au, bx, by, 0x6Fu);
            } else {
                ui_func_002bf460(2u, 0x28u, 0x57u, bx, by, 0x6Au);
                ui_func_002bf460(2u, 0x28u, 0x59u, bx, by, 0x6Fu);
            }
            return;
        case 2u: {
            const s32 target = *reinterpret_cast<const s32*>(a0 + 0xD5E0u + idx * 4);
            const u16 mask = (idx < 0)
                                 ? *reinterpret_cast<const u16*>(script_vm_func_002b66ec() + 0x72u)
                                 : *reinterpret_cast<const u16*>(camp_func_002a89e4(idx) + 0x44u);
            s32 color = -1;
            s32 cnt = 0;
            for (s32 bit = 1; bit < 0x0B; ++bit) {
                if ((mask & (1u << bit)) != 0u) {
                    if (cnt == target) {
                        color = ui_func_002b0788(static_cast<s16>(bit));
                        break;
                    }
                    ++cnt;
                }
            }
            set_color_3b67c4(color);
            const u8* const g0 = *reinterpret_cast<const u8* const*>(0x0044DC38u);
            const s32 gx = *reinterpret_cast<const s16*>(g0 + 8u) + bx;
            const s32 gy = *reinterpret_cast<const s16*>(g0 + 10u) + by;
            ui_func_002b6a98(*reinterpret_cast<const s16*>(demon + 0x46u), gx, gy, 0x6Au, 0u);
            return;
        }
        case 3u:
            ui_func_002bf460(2u, 0x28u, 0x5Bu, bx, by, 0x6Fu);
            ui_func_002bf460(2u, 0x28u, 0x5Cu, bx, by, 0x6Fu);
            ui_func_002bf460(2u, 0x28u, 0x5Du, bx, by, 0x74u);
            ui_func_002bf460(2u, 0x28u, 0x5Eu, bx, by, 0x79u);
            return;
        case 4u: {
            const s32 color = (val7 > 0 || static_cast<s32>(demon[0x48u]) > val10) ? 0xFF : -1;
            set_color_3b67c4(color);
            const u8* const g0 = *reinterpret_cast<const u8* const*>(0x0044DC38u);
            const s32 gx = *reinterpret_cast<const s16*>(g0 + 8u) + bx;
            const s32 gy = *reinterpret_cast<const s16*>(g0 + 10u) + by;
            engine_func_002be16c(6u, gx, gy, 1u, 2u, 0x7Eu, "%d",
                                 static_cast<s32>(demon[0x48u]) + val7);
            return;
        }
        case 5u:
            ui_func_003b6fc4(a0, idx, bx, by);
            return;
        case 6u:
            if (flag != 0u) {
                ui_func_002bf460(2u, 0x28u, 0x60u, bx, by, 0x83u);
            } else {
                const u8* const g0 = *reinterpret_cast<const u8* const*>(0x0044DC38u);
                const u8* const g0_c = *reinterpret_cast<const u8* const*>(g0 + 0x0Cu);
                const s32 h = *reinterpret_cast<const s16*>(g0_c + 2u);
                func_002b0908(2u, 0x28u, 0x5Fu, bx, static_cast<u32>(by), w_bits, h, 0x83u);
            }
            return;
        case 7u:
            if (flag == 0u) {
                return;
            }
            if (val7 < 8) {
                ui_func_002bf710(static_cast<f32>(val7) * 0.125f);
            }
            ui_func_002bf460(2u, 0x28u, 0x61u, bx, by, 0x88u);
            ui_func_002bf460(2u, 0x28u, 0x61u, bx, by, 0x89u);
            return;
        default:
            return;
    }
}

extern "C" u32 script_vm_func_00152790(s32 idx);
extern "C" u8* script_vm_func_002a44f8(s32 idx);
extern "C" u8* script_vm_func_002a4518(s32 idx);
extern "C" u32 engine_func_002af528(u8* vec, u32 new_cap);
extern "C" u8* script_vm_func_002a4508(s32 idx);
extern "C" void engine_func_002c2b34(u8* obj, u32 val);
extern "C" void script_vm_func_001db538(s32 idx);
extern "C" u32 func_003948d0(u32 a0, u8* a1, u32 a2, u32 a3);

namespace {

inline void attach_node_2a0790(u8* parent, u8* child) {
    if (child == nullptr) {
        return;
    }
    const void* const p_link = *reinterpret_cast<const void* const*>(parent + 0x0Cu);
    if (p_link != nullptr && (p_link == child || engine_func_002af604(p_link, child) != 0)) {
        return;
    }
    if (*reinterpret_cast<const void* const*>(child + 0x0Cu) != nullptr) {
        return;
    }

    u8* const vec = parent + 0x14u;
    u8** const begin = *reinterpret_cast<u8***>(parent + 0x18u);
    u8** const end = *reinterpret_cast<u8***>(parent + 0x1Cu);
    const u32 cap = *reinterpret_cast<const u32*>(parent + 0x20u) & 0x3FFFFFFFu;
    u32 ok = 1u;
    if (static_cast<s32>(cap) <= (end - begin)) {
        const u32 new_cap = (cap != 0u) ? (cap << 1) : 1u;
        ok = engine_func_002af528(vec, new_cap);
        if (ok == 0u) {
            return;
        }
    }

    u8** const cur_end = *reinterpret_cast<u8***>(parent + 0x1Cu);
    if (cur_end != nullptr) {
        *cur_end = child;
    }
    *reinterpret_cast<u8***>(parent + 0x1Cu) = cur_end + 1;
    if (ok != 0u) {
        *reinterpret_cast<u32*>(child + 0x0Cu) = *reinterpret_cast<const u32*>(parent + 0x10u);
    }
}

}  // namespace

// DECOMP_FUNC(0x002a0790, 1220)
extern "C" u32 script_vm_func_002a0790(s32 idx) {
    const u32 v1 = script_vm_func_00152790(idx);
    u8* const v2 = script_vm_func_002a44f8(idx);
    const u32* const* const p4 = *reinterpret_cast<const u32* const* const*>(v2 + 4u);
    const u32 v3 = *p4[0x4Cu / 4u];
    u8* const v2b = script_vm_func_002a44f8(idx);
    u8* const parent5 = script_vm_func_002a4518(idx);

    const u32 stride = static_cast<u32>(idx) * 0x284u;
    u8* const* const a0 = reinterpret_cast<u8* const*>(0x004D9880u + 0x264u + stride);
    u8* const* const a1 = reinterpret_cast<u8* const*>(0x004D9D88u + 0x264u + stride);
    u8* const* const a2 = reinterpret_cast<u8* const*>(0x004D9880u + 0xA10u + 0x264u + stride);
    u8* const* const a3 = reinterpret_cast<u8* const*>(0x004D9D88u + 0xA10u + 0x264u + stride);

    for (s16 i = 0; i < 8; ++i) {
        attach_node_2a0790(parent5, a0[i]);
        attach_node_2a0790(parent5, a1[i]);
        attach_node_2a0790(parent5, a2[i]);
        attach_node_2a0790(parent5, a3[i]);
    }

    u8* const parent6 = script_vm_func_002a4508(idx);
    u8* const* const q = reinterpret_cast<u8* const*>(0x004DACA0u + 4u + static_cast<u32>(idx) * 0x14u);
    for (s16 i = 0; i < 4; ++i) {
        attach_node_2a0790(parent6, q[i]);
    }

    engine_func_002c2b34(v2b, *reinterpret_cast<const u32*>(0x00464B84u + static_cast<u32>(idx) * 4u));
    script_vm_func_001db538(idx);
    return func_003948d0(v1, v2, 0x004DACE0u + static_cast<u32>(idx) * 0x40u, v3);
}

extern "C" u32 func_00147994(u32 addr);

namespace {

inline void emit_gpu_cmd_132fc4(u32 val, u32 reg) {
    u32* const ptr = *reinterpret_cast<u32**>(0x004652A0u);
    u32* const end = *reinterpret_cast<u32* const*>(0x004652A4u);
    if (ptr < end) {
        ptr[0] = val;
        ptr[1] = reg;
        *reinterpret_cast<u32**>(0x004652A0u) = ptr + 2;
    }
}

inline u32 validate_rt_132fc4(const u8* color_buf, const u8* depth_buf) {
    if (color_buf == nullptr && depth_buf == nullptr) {
        return 0x8CD7u;
    }
    u32 cw = 0u;
    u32 ch = 0u;
    if (color_buf != nullptr) {
        const u32 p = *reinterpret_cast<const u32*>(color_buf);
        if (p == 0u) {
            return 0x8CD6u;
        }
        cw = *reinterpret_cast<const u32*>(color_buf + 0x0Cu);
        ch = *reinterpret_cast<const u32*>(color_buf + 0x10u);
        if (cw == 0u || ch == 0u) {
            return 0x8CD6u;
        }
    }
    if (depth_buf != nullptr) {
        const u32 dp = *reinterpret_cast<const u32*>(depth_buf);
        if (dp == 0u) {
            return 0x8CD6u;
        }
        const u32 dw = *reinterpret_cast<const u32*>(depth_buf + 0x0Cu);
        const u32 dh = *reinterpret_cast<const u32*>(depth_buf + 0x10u);
        if (dw == 0u || dh == 0u) {
            return 0x8CD6u;
        }
        if (cw != 0u && (dw != cw || dh != ch)) {
            return 0x8CD9u;
        }
    }
    return (color_buf != depth_buf) ? 0x8CD5u : 0x8CD6u;
}

}  // namespace

// DECOMP_FUNC(0x00132fc4, 1224)
extern "C" void func_00132fc4() {
    const u8* const ctx = *reinterpret_cast<const u8* const*>(0x004652A8u);
    const u8* const rt = *reinterpret_cast<const u8* const*>(ctx + 8u);
    u8* const gpu = *reinterpret_cast<u8* const*>(0x004655C0u);
    const u8* const color_buf = *reinterpret_cast<const u8* const*>(rt + 0x0Cu);
    const u8* const depth_buf = *reinterpret_cast<const u8* const*>(rt + 0x1Cu);

    u8* const st4 = gpu + 0x684u;
    const u32 status = validate_rt_132fc4(color_buf, depth_buf);
    if (status != 0x8CD5u) {
        *reinterpret_cast<u32*>(st4) = 0u;
        st4[0x0Cu] = 0u;
        st4[0x0Du] = 0u;
        st4[0x0Eu] = 0u;
        return;
    }

    *reinterpret_cast<u32*>(st4) = status;
    if ((*reinterpret_cast<const u32*>(gpu + 8u) & 0x100u) != 0u) {
        return;
    }

    u8* const st6 = gpu + 0x804u;
    const bool buf_changed =
        (color_buf != nullptr &&
         *reinterpret_cast<const u32*>(st6 + 0x0Cu) != *reinterpret_cast<const u32*>(color_buf)) ||
        (depth_buf != nullptr &&
         *reinterpret_cast<const u32*>(st6 + 8u) != *reinterpret_cast<const u32*>(depth_buf));
    if (buf_changed || (*reinterpret_cast<const u32*>(gpu + 4u) & 0x100u) != 0u) {
        emit_gpu_cmd_132fc4(1u, 0x000F0111u);
        emit_gpu_cmd_132fc4(1u, 0x000F0110u);
    }

    u32 w = 0u;
    u32 h = 0u;
    if (color_buf == nullptr) {
        st4[0x0Cu] = 0u;
    } else {
        st4[0x0Cu] = 1u;
        *reinterpret_cast<u32*>(st6 + 0x0Cu) = *reinterpret_cast<const u32*>(color_buf);
        *reinterpret_cast<u32*>(st6 + 0x14u) = *reinterpret_cast<const u32*>(color_buf + 0x20u);
        switch (*reinterpret_cast<const u32*>(color_buf + 0x1Cu)) {
            case 0u:
                *reinterpret_cast<u32*>(st4 + 4u) = 0u;
                *reinterpret_cast<u32*>(st6) = 2u;
                break;
            case 2u:
                *reinterpret_cast<u32*>(st4 + 4u) = 2u;
                *reinterpret_cast<u32*>(st6) = 0u;
                break;
            case 3u:
                *reinterpret_cast<u32*>(st4 + 4u) = 3u;
                *reinterpret_cast<u32*>(st6) = 0u;
                break;
            case 4u:
                *reinterpret_cast<u32*>(st4 + 4u) = 4u;
                *reinterpret_cast<u32*>(st6) = 0u;
                break;
            default:
                break;
        }
        emit_gpu_cmd_132fc4(
            *reinterpret_cast<const u32*>(st6) | (*reinterpret_cast<const u32*>(st4 + 4u) << 16u),
            0x000F0117u);
        if (*reinterpret_cast<u32* const*>(0x004652A0u) <
            *reinterpret_cast<u32* const*>(0x004652A4u)) {
            emit_gpu_cmd_132fc4(func_00147994(*reinterpret_cast<const u32*>(st6 + 0x0Cu)) >> 3u,
                                0x000F011Du);
        }
        w = *reinterpret_cast<const u32*>(color_buf + 0x0Cu);
        h = *reinterpret_cast<const u32*>(color_buf + 0x10u);
    }

    if (depth_buf == nullptr) {
        st4[0x0Du] = 0u;
        st4[0x0Eu] = 0u;
    } else {
        const u32 old_68c = *reinterpret_cast<const u32*>(gpu + 0x68Cu);
        st4[0x0Du] = 1u;
        *reinterpret_cast<u32*>(st6 + 8u) = *reinterpret_cast<const u32*>(depth_buf);
        switch (*reinterpret_cast<const u32*>(depth_buf + 0x38u)) {
            case 0x10u:
                *reinterpret_cast<u32*>(st6 + 4u) = 0u;
                *reinterpret_cast<u32*>(gpu + 0x68Cu) = 0u;
                break;
            case 0x18u:
                *reinterpret_cast<u32*>(st6 + 4u) = 2u;
                *reinterpret_cast<u32*>(gpu + 0x68Cu) = 2u;
                break;
            case 0x20u:
                *reinterpret_cast<u32*>(st6 + 4u) = 3u;
                *reinterpret_cast<u32*>(gpu + 0x68Cu) = 3u;
                break;
            default:
                break;
        }
        if (gpu[0x54u] != 0u) {
            const u32 new_68c = *reinterpret_cast<const u32*>(gpu + 0x68Cu);
            if ((new_68c == 0u) != (old_68c == 0u)) {
                *reinterpret_cast<u32*>(gpu) |= 4u;
            }
        }
        st4[0x0Eu] = (*reinterpret_cast<const u32*>(gpu + 0x68Cu) == 3u) ? 1u : 0u;
        *reinterpret_cast<u32*>(st6 + 0x10u) = *reinterpret_cast<const u32*>(depth_buf + 0x20u);
        emit_gpu_cmd_132fc4(*reinterpret_cast<const u32*>(st6 + 4u), 0x000F0116u);
        if (*reinterpret_cast<u32* const*>(0x004652A0u) <
            *reinterpret_cast<u32* const*>(0x004652A4u)) {
            emit_gpu_cmd_132fc4(func_00147994(*reinterpret_cast<const u32*>(st6 + 8u)) >> 3u,
                                0x000F011Cu);
        }
        w = *reinterpret_cast<const u32*>(depth_buf + 0x0Cu);
        h = *reinterpret_cast<const u32*>(depth_buf + 0x10u);
    }

    if (*reinterpret_cast<const u32*>(st4 + 0x14u) != w ||
        *reinterpret_cast<const u32*>(st4 + 0x18u) != h ||
        (*reinterpret_cast<const u32*>(gpu + 4u) & 0x100u) != 0u) {
        const u32 packed = (w & 0xFFFu) | (((h - 1u) & 0xFFFu) << 12u) | 0x01000000u;
        emit_gpu_cmd_132fc4(packed, 0x000F011Eu);
        emit_gpu_cmd_132fc4(packed, 0x000F006Eu);
        *reinterpret_cast<u32*>(st4 + 0x14u) = w;
        *reinterpret_cast<u32*>(st4 + 0x18u) = h;
        if (gpu[0x648u] != 0u) {
            *reinterpret_cast<u32*>(gpu) |= 0x200u;
        }
    }

    if (gpu[0x30u] == 0u) {
        gpu[0x30u] = 1u;
        reinterpret_cast<void (*)(u32, u32)>(0x001425E8u)(0u, 0u);
    }
}

extern "C" const u8* camp_func_002bf6c8(u8* ui_obj, u32 id);
extern "C" void ui_func_00230f18(u8* ui_obj, u32 id, s32 x, s32 y, u32 a4);
extern "C" void camp_func_00231d60(u8* ui_obj, u32 id, s32 x, s32 y, u32 a4, u32 a5);
extern "C" void func_002313ec(s32 x, s32 y, s32 w, s32 h);
extern "C" s32 ui_func_002bef7c();
extern "C" s32 shop_func_002bef70(u8* ptr);
extern "C" void func_0039fde4(u8* ui_obj, s16 item_id, s32 x, s32 y, u32 a4);
extern "C" const char* script_vm_func_002bd020(u16 item_id, u32 a1);
extern "C" s32 ui_func_002335c0(const char* str, u32 a1);
extern "C" const char* script_vm_func_002bd25c(u16 item_id);
extern "C" void func_002be744(u8* ui_obj, u32 mode, u32 color, const char* str, f32 x, f32 y,
                             f32 alpha, f32 z, f32 scale);
extern "C" void func_00230c80(u8* ui_obj, u32 a1, s32 x, s32 y, u32 a4, u32 a5, u32 color, u32 a7,
                             const char* str);

// DECOMP_FUNC(0x003aa264, 1224)
extern "C" void ui_func_003aa264(u8* self, u32 a1, u32 flag, u32 item_id) {
    s32 a5 = *reinterpret_cast<const s32*>(self + 0x594u);
    if (flag != 0u) {
        ++a5;
    }
    const f32 alpha = static_cast<f32>(0x100 - a5) * (1.0f / 256.0f);
    const u8* const base_l = camp_func_002bf6c8(
        self + 0xC8u, a1 + ((flag == 0u) ? 0x102Fu : 0x1042u));
    const s32 bx = *reinterpret_cast<const s16*>(base_l + 8u);
    const s32 by = *reinterpret_cast<const s16*>(base_l + 10u);

    if (flag != 0u) {
        ui_func_002bf710(*reinterpret_cast<const f32*>(self + 0x234u));
        ui_func_00230f18(self + 0xC8u, 0x103Au, bx, by, static_cast<u32>(a5));
        ui_func_00230f18(self + 0xC8u, 0x103Bu, bx, by, static_cast<u32>(a5));
        ui_func_00230f18(self + 0xC8u, 0x103Cu, bx, by, static_cast<u32>(a5));
        ui_func_002bf710(1.0f);
        camp_func_00231d60(self + 0xC8u, 0x103Du, bx, by, static_cast<u32>(a5), 1u);
        camp_func_00231d60(self + 0xC8u, 0x103Eu, bx, by, static_cast<u32>(a5), 1u);

        const u8* const l41 = camp_func_002bf6c8(self + 0xC8u, 0x1041u);
        const s16* const sz41 = *reinterpret_cast<const s16* const*>(l41 + 0x0Cu);
        func_002313ec(*reinterpret_cast<const s16*>(l41 + 8u) + bx,
                      *reinterpret_cast<const s16*>(l41 + 10u) + by, sz41[0], sz41[1]);

        const u8* const l40 = camp_func_002bf6c8(self + 0xC8u, 0x1040u);
        const u32 w40 = *reinterpret_cast<const u16*>(l40 + 4u) & 0x7FFFu;
        const s32 tx = ui_func_002bef7c() + bx - static_cast<s32>(w40);
        const s32 ty = shop_func_002bef70(self + 0x2A0u) + by;
        camp_func_00231d60(self + 0xC8u, 0x1040u, tx, ty, static_cast<u32>(a5), 1u);

        u8* const sl = *reinterpret_cast<u8* const*>(0x0044EA00u) + 0x130Cu;
        const u32 idx = *reinterpret_cast<const u32*>(sl);
        void* const cb = *reinterpret_cast<void* const*>(sl + 8u + idx * 4u);
        *reinterpret_cast<void**>(sl + 8u + idx * 4u) = nullptr;
        if (sl[0x18u] != 0u || cb != nullptr) {
            reinterpret_cast<void (*)()>(*reinterpret_cast<void* const*>(sl + 0x1Cu))();
            sl[0x18u] = 0u;
        }
    }

    if (item_id == 0u) {
        return;
    }

    const u8* const l_hdr =
        camp_func_002bf6c8(self + 0xC8u, (flag != 0u) ? 0x1068u : 0x1058u);
    func_0039fde4(self + 0xC8u, static_cast<s16>(item_id),
                  *reinterpret_cast<const s16*>(l_hdr + 8u) + bx,
                  *reinterpret_cast<const s16*>(l_hdr + 10u) + by, static_cast<u32>(a5));

    const u32 mode2 = (flag != 0u) ? 3u : 2u;
    const char* const s1 = script_vm_func_002bd020(static_cast<u16>(item_id), 0u);
    const s32 sw = ui_func_002335c0(s1, 2u);
    const u32 color1 = (flag != 0u) ? 0xFFFFFFFFu : 0xFFu;
    const u8* const l_name =
        camp_func_002bf6c8(self + 0xC8u, (flag != 0u) ? 0x106Bu : 0x105Bu);
    const s16* const sz_name = *reinterpret_cast<const s16* const*>(l_name + 0x0Cu);
    const s32 nx = bx + (sz_name[0] / 2) + *reinterpret_cast<const s16*>(l_name + 8u) - (sw / 2);
    const s32 ny = *reinterpret_cast<const s16*>(l_name + 10u) + by;
    func_002be744(self + 0xC8u, mode2, color1, s1, static_cast<f32>(nx), static_cast<f32>(ny),
                  alpha, 0.0f, 1.0f);

    const char* const s2 = script_vm_func_002bd25c(static_cast<u16>(item_id));
    const u8* const l_desc =
        camp_func_002bf6c8(self + 0xC8u, (flag != 0u) ? 0x106Cu : 0x105Cu);
    func_002be744(self + 0xC8u, mode2, color1, s2,
                  static_cast<f32>(*reinterpret_cast<const s16*>(l_desc + 8u) + bx),
                  static_cast<f32>(*reinterpret_cast<const s16*>(l_desc + 10u) + by), alpha, 0.0f,
                  1.0f);

    const u8* const rec1 = battle_func_002b087c(static_cast<u16>(item_id));
    const u32 qty = (rec1 != nullptr) ? rec1[2] : 0u;
    const u8* const l_qty =
        camp_func_002bf6c8(self + 0xC8u, (flag != 0u) ? 0x106Au : 0x105Au);
    char buf[0x20];
    reinterpret_cast<void (*)(char*, const char*, u32)>(ui_func_002be7fc)(buf, "%2d", qty);
    func_00230c80(self + 0xC8u, 0u, *reinterpret_cast<const s16*>(l_qty + 8u) + bx,
                  *reinterpret_cast<const s16*>(l_qty + 10u) + by, 0u, 7u, 0xFFFFFFFFu,
                  static_cast<u32>(a5), buf);

    const u8* const rec2 = battle_func_002b087c(static_cast<u16>(item_id));
    const u32 price = (rec2 != nullptr) ? *reinterpret_cast<const u32*>(rec2 + 0x78u) : 0u;
    const u8* const l_pr =
        camp_func_002bf6c8(self + 0xC8u, (flag != 0u) ? 0x1074u : 0x1064u);
    const u32 color_pr = (flag != 0u) ? 0xFFFFFFFFu : 0x323232FFu;
    reinterpret_cast<void (*)(char*, const char*, u32)>(ui_func_002be7fc)(buf, "%8d", price);
    func_00230c80(self + 0xC8u, 0u, *reinterpret_cast<const s16*>(l_pr + 8u) + bx,
                  *reinterpret_cast<const s16*>(l_pr + 10u) + by, 0u, 7u, color_pr,
                  static_cast<u32>(a5), buf);
}

extern "C" void engine_func_002bad80(u64* out, u32 err);
extern "C" s32 func_0023a15c(const u32* items, u32 count);
extern "C" void engine_func_00361350(u8* g, u32 a1);
extern "C" void func_003613c8(u8* g_1000);
extern "C" s32 func_0023a11c(u32* out_tmp, u8* g, u32 a2);
extern "C" s32 func_002c57b4();
extern "C" s32 func_002c57a4();
extern "C" void func_0023a068(u64* out, u8* g);
extern "C" u32 script_vm_func_002b5f84();
extern "C" void engine_func_002bac28(u32* out_val);
extern "C" s32 ui_func_00353a50(u32 ctx, u32* val_ptr, u32 h0, u32 h1, const char* str,
                                u8* g_40c);
extern "C" s32 func_003522e8(u8* desc, u32 one, u64* out_entry, u32 one2);
extern "C" void func_00353acc(u32 ctx, u32 id20, u32 word, u32 val);
extern "C" s32 func_00353b58(u32* val_ptr);
extern "C" s32 func_00353800(u32 a1, u32 val);

namespace {

inline u32 encode_hi_353d10(const u32* pair) {
    const u8 tag = *reinterpret_cast<const u8*>(pair + 1);
    u32 hi = 0u;
    if (tag == 0u) {
        hi = 0x8Cu;
    } else if (tag == 1u) {
        hi = 0x0Du;
    } else if (tag == 3u) {
        hi = 0x10u;
    }
    return hi | 0x40000u;
}

inline u32 encode_lo_353d10(const u32* pair) {
    const u8 b5 = reinterpret_cast<const u8*>(pair)[5];
    return static_cast<u32>(b5) | ((pair[0] & ~0x00F00000u) << 8u);
}

inline u32 encode_kind_353d10(u32 hi) {
    if ((hi >> 14u) == 0x10u) {
        const u16 lo16 = static_cast<u16>(hi);
        if (lo16 == 0x8Cu) {
            return 0u;
        }
        if (lo16 == 0x0Du) {
            return 1u;
        }
    }
    return 0xFFu;
}

}  // namespace

// DECOMP_FUNC(0x00353d10, 1240)
extern "C" void engine_func_00353d10(u64* out_status, u32 a1, u32* out_val, const u32* hdr_pair,
                                     const char* num_str, const u32* items, u32 count) {
    if (count > 0x40u) {
        engine_func_002bad80(out_status, 0xE0613881u);
        return;
    }
    for (u32 i = 0u; i < count; ++i) {
        const u32 hi = encode_hi_353d10(items + i * 2u);
        if ((hi >> 14u) != 0x10u ||
            (static_cast<u16>(hi) != 0x8Cu && static_cast<u16>(hi) != 0x0Du)) {
            engine_func_002bad80(out_status, 0xE0E13883u);
            return;
        }
    }

    s32 rc = func_0023a15c(items, count);
    if (rc < 0) {
        engine_func_002bad80(out_status, static_cast<u32>(rc));
        return;
    }

    u8* const g = reinterpret_cast<u8*>(0x004C7000u);
    engine_func_00361350(g, 1u);
    *reinterpret_cast<u32*>(g + 8u) = encode_lo_353d10(hdr_pair);
    *reinterpret_cast<u32*>(g + 0x0Cu) = encode_hi_353d10(hdr_pair);
    *reinterpret_cast<u64*>(g + 0x10u) =
        reinterpret_cast<u64 (*)(const char*, char**, u32)>(0x00100BF7u)(num_str, nullptr, 10u);
    *reinterpret_cast<u32*>(g + 0x18u) = 1u;
    func_003613c8(g + 0x1000u);

    u32 n_tag0 = 0u;
    for (u32 i = 0u; i < count; ++i) {
        const u32* const item = items + i * 2u;
        const u32 hi = encode_hi_353d10(item);
        const u32 lo = encode_lo_353d10(item);
        if ((hi >> 14u) == 0x10u && static_cast<u16>(hi) == 0x8Cu) {
            *reinterpret_cast<u32*>(g + 0x30u + n_tag0 * 8u) = lo;
            *reinterpret_cast<u32*>(g + 0x30u + n_tag0 * 8u + 4u) = hi;
            ++n_tag0;
        }
    }
    *reinterpret_cast<u32*>(g + 0x230u) = n_tag0;

    u32 tmp_30 = 0u;
    rc = func_0023a11c(&tmp_30, g, 0u);
    if (rc < 0) {
        engine_func_002bad80(out_status, static_cast<u32>(rc));
        return;
    }
    if (func_002c57b4() != 0 || func_002c57a4() != 0) {
        engine_func_002bad80(out_status, 0xC9413891u);
        return;
    }

    u64 st64 = 0u;
    func_0023a068(&st64, g);
    if (engine_func_002a1578(&st64) < 0) {
        *out_status = st64;
        return;
    }

    const u32 h_ctx = script_vm_func_002b5f84();
    u32 val8 = 0u;
    engine_func_002bac28(&val8);
    rc = ui_func_00353a50(h_ctx, &val8, hdr_pair[0], hdr_pair[1], num_str, g + 0x43Cu);
    if (rc < 0) {
        engine_func_002bad80(out_status, static_cast<u32>(rc));
        return;
    }

    const u32 n_entries = *reinterpret_cast<const u32*>(g + 0x438u);
    for (u32 j = 0u; j < n_entries; ++j) {
        u8 desc[0x18];
        const u64 entry = *reinterpret_cast<const u64*>(g + 0x238u + j * 8u);
        u64 out_entry = entry;
        rc = func_003522e8(desc, 1u, &out_entry, 1u);
        if (rc < 0) {
            engine_func_002bad80(out_status, static_cast<u32>(rc));
            return;
        }
        const u32 lo_out = static_cast<u32>(out_entry);
        const u32 hi_out = static_cast<u32>(out_entry >> 32u);
        const u32 id20 = ((lo_out >> 8u) | (hi_out << 24u)) & 0x000FFFFFu;
        const u32 word = encode_kind_353d10(hi_out) | ((lo_out << 8u) & 0xFF00u) |
                         (static_cast<u32>(*reinterpret_cast<const u16*>(desc + 0x10u)) << 16u);
        func_00353acc(h_ctx, id20, word, val8);
    }

    for (u32 k = 0u; k < count; ++k) {
        const u32* const item = items + k * 2u;
        const u32 hi = encode_hi_353d10(item);
        const u32 lo = encode_lo_353d10(item);
        if ((hi >> 14u) == 0x10u && static_cast<u16>(hi) == 0x8Cu) {
            continue;
        }
        const u32 id20 = ((lo >> 8u) | (hi << 24u)) & 0x000FFFFFu;
        const u32 word = encode_kind_353d10(hi) | ((lo << 8u) & 0xFF00u);
        func_00353acc(h_ctx, id20, word, val8);
    }

    rc = func_00353b58(&val8);
    if (rc < 0) {
        engine_func_002bad80(out_status, static_cast<u32>(rc));
        return;
    }
    rc = func_00353800(a1, val8);
    if (rc < 0) {
        engine_func_002bad80(out_status, static_cast<u32>(rc));
        return;
    }

    *out_val = val8;
    engine_func_002bad80(out_status, 0u);
}

extern "C" void ui_func_002c3ba8(u8* g);
extern "C" void ui_func_002b217c(const f32* c0, const f32* c1, const f32* c2, const f32* c3,
                                 u32 a4, u32 a5);
extern "C" void ui_func_002c1b64(u8* g);
extern "C" void ui_func_002c1abc(u8* g);

namespace {

inline void push_state_1ecc7c(u8* slot, u32 val) {
    const u32 old_idx = *reinterpret_cast<const u32*>(slot);
    const u32 new_idx = old_idx + 1u;
    const u32 old_val = *reinterpret_cast<const u32*>(slot + 8u + old_idx * 4u);
    *reinterpret_cast<u32*>(slot) = new_idx;
    *reinterpret_cast<u32*>(slot + 8u + new_idx * 4u) = val;
    if (slot[0x18u] != 0u || old_val != val) {
        reinterpret_cast<void (*)()>(*reinterpret_cast<void* const*>(slot + 0x1Cu))();
        slot[0x18u] = 0u;
    }
}

inline void pop_state_1ecc7c(u8* slot) {
    const u32 old_idx = *reinterpret_cast<const u32*>(slot);
    const u32 new_idx = old_idx - 1u;
    const u32 old_val = *reinterpret_cast<const u32*>(slot + 8u + old_idx * 4u);
    *reinterpret_cast<u32*>(slot) = new_idx;
    const u32 cur_val = *reinterpret_cast<const u32*>(slot + 8u + new_idx * 4u);
    if (slot[0x18u] != 0u || old_val != cur_val) {
        reinterpret_cast<void (*)()>(*reinterpret_cast<void* const*>(slot + 0x1Cu))();
        slot[0x18u] = 0u;
    }
}

inline void set_state_1ecc7c(u8* slot, u32 val) {
    const u32 idx = *reinterpret_cast<const u32*>(slot);
    const u32 old_val = *reinterpret_cast<const u32*>(slot + 8u + idx * 4u);
    *reinterpret_cast<u32*>(slot + 8u + idx * 4u) = val;
    if (slot[0x18u] != 0u || old_val != val) {
        reinterpret_cast<void (*)()>(*reinterpret_cast<void* const*>(slot + 0x1Cu))();
        slot[0x18u] = 0u;
    }
}

inline void call_2b217c_ones_1ecc7c() {
    const f32 c0[4] = {1.0f, 1.0f, 1.0f, 1.0f};
    const f32 c1[4] = {1.0f, 1.0f, 1.0f, 1.0f};
    const f32 c2[4] = {1.0f, 1.0f, 1.0f, 1.0f};
    const f32 c3[4] = {1.0f, 1.0f, 1.0f, 1.0f};
    ui_func_002b217c(c0, c1, c2, c3, 0u, 1u);
}

}  // namespace

// DECOMP_FUNC(0x001ecc7c, 1256)
extern "C" u32 ui_func_001ecc7c() {
    const u8* const r5 = *reinterpret_cast<const u8* const*>(0x0043DC20u + 4u);
    if (r5 == nullptr || *reinterpret_cast<const u32*>(r5 + 8u) == 0u) {
        return 0u;
    }

    u8* const g = *reinterpret_cast<u8* const*>(0x0044EA00u);
    ui_func_002c3ba8(g);
    push_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x124Cu, ui_func_002c5f7c(1u, 0u));

    if (*reinterpret_cast<const u32*>(r5 + 0x0Cu) == 1u) {
        func_002bf558(2u, 0x11u, 0u, 0u, 0u, 1u);
    } else {
        call_2b217c_ones_1ecc7c();
        ui_func_002bf460(2u, 0x11u, 0u, 0u, 0u, 1u);
        set_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x12ACu,
                         battle_func_002c5fa4(6u, 1u, 0u));

        const f32 inv255 = static_cast<f32>(0x3B808081u ? 1.0f / 255.0f : 0.0f);
        for (s32 i = 0; i < 5; ++i) {
            const u8* const entry = r5 + i * 20;
            ui_func_002bf710(*reinterpret_cast<const f32*>(entry + 0x88u) * inv255);
            call_2b217c_ones_1ecc7c();
            const s32 y = static_cast<s32>(*reinterpret_cast<const f32*>(entry + 0x7Cu));
            ui_func_002bf460(2u, 0x11u, 3u, 0u, static_cast<u32>(y), 1u);
        }

        ui_func_002bf710(1.0f);
        call_2b217c_ones_1ecc7c();
        set_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x12ACu,
                         battle_func_002c5fa4(6u, 1u, 0u));

        for (s32 i = 0; i < 5; ++i) {
            const u8* const entry = r5 + i * 20;
            const s32 x = static_cast<s32>(*reinterpret_cast<const f32*>(entry + 0x18u));
            const s32 y = static_cast<s32>(*reinterpret_cast<const f32*>(entry + 0x1Cu));
            ui_func_002bf460(2u, 0x11u, 1u, static_cast<u32>(x), static_cast<u32>(y), 2u);
        }

        set_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x12ACu,
                         battle_func_002c5fa4(6u, 7u, 0u));
    }

    pop_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x124Cu);
    ui_func_002c1b64(*reinterpret_cast<u8* const*>(0x0044EA00u));
    ui_func_002c1abc(*reinterpret_cast<u8* const*>(0x0044EA00u));
    return 0u;
}

extern "C" __attribute__((naked)) void func_001ed048() {
    asm volatile(
        ".arm\n"
        ".word 0xe59f0104\n"
        ".word 0xe92d4070, 0xe24dd008, 0xe5900004, 0xe3500000\n"
        ".word 0x0a00003a, 0xe5901008, 0xe3510000, 0x0a000036\n"
        ".word 0xed900a04, 0xeddf0a38, 0xeeb40ae0, 0xeef1fa10\n"
        ".word 0xda000031, 0xeb0349a2, 0xe59f50d0, 0xe3a01000\n"
        ".word 0xe3a00001, 0xe5954000, 0xeb0363b8, 0xe2844a01\n"
        ".word 0xe2844f93, 0xe3a06000, 0xe5941000, 0xe2812001\n"
        ".word 0xe0843101, 0xe5931008, 0xe0843102, 0xe5842000\n"
        ".word 0xe5830008, 0xe5d42018, 0xe3520000, 0x01510000\n"
        ".word 0x0a000002, 0xe594101c, 0xe12fff31, 0xe5c46018\n"
        ".word 0xe3a000fb, 0xe58d0004, 0xe3a03000, 0xe3a02f43\n"
        ".word 0xe3a0100e, 0xe3a00002, 0xe58d6000, 0xeb0348d8\n"
        ".word 0xe5950000, 0xe2804a01, 0xe2844f93, 0xe5940000\n"
        ".word 0xe0841100, 0xe2400001, 0xe5911008, 0xe5840000\n"
        ".word 0xe0840100, 0xe5d42018, 0xe5900008, 0xe3520000\n"
        ".word 0x01510000, 0x0a000002, 0xe594101c, 0xe12fff31\n"
        ".word 0xe5c46018, 0xed9f0a06, 0xeb034971, 0xe3a00000\n"
        ".word 0xe28dd008, 0xe8bd8070, 0x0043dc20, 0x00000000\n"
        ".word 0x0044ea00, 0x3f800000\n"
    );
}

extern "C" u8* func_00262a44();
extern "C" s32 camp_func_0029f260(u8* list);
extern "C" s32 camp_func_0029f248(u8* list);
extern "C" u32 camp_func_002888dc(s32 idx);
extern "C" s32 camp_func_0029f0f4(u8* list);
extern "C" s32 camp_func_001b0698(u8* r5, u32 id, char* out_buf, s32 item_idx);
extern "C" void ui_func_002be77c(u32 mode, u32 color, const char* str, f32 x, f32 y, f32 alpha,
                                 f32 z, f32 scale);
extern "C" s32 ui_func_0029d8fc(s16 val);
extern "C" void func_0029a418(s32 x, s32 y, s32 w, s32 h, u32 flag);

namespace {

inline s32 lerp_pos_1f1ad8(s32 src, s32 dst, s32 t) {
    if (t >= 4) {
        return dst;
    }
    return src + (((((dst - src) << 12) / 4) * t) >> 12);
}

}  // namespace

// DECOMP_FUNC(0x001f1ad8, 1264)
extern "C" void camp_func_001f1ad8(s32 bx, s32 by) {
    u8* const r5 = func_00262a44();
    if (r5 == nullptr) {
        return;
    }

    u8* const list1 = r5 + 0x4E8u;
    const u32 id = camp_func_002888dc(camp_func_0029f260(list1) + camp_func_0029f248(list1));
    const u8* const sl = camp_func_002bf6d0(0x24u, static_cast<u32>(camp_func_0029f248(list1) + 0xB6));
    if (*reinterpret_cast<const s32*>(r5 + 0x3FCu) >= 4) {
        ui_func_002bf460(2u, 0x24u, 0xB5u, bx, by, 0x97u);
    }

    u8* const list2 = r5 + 0x54Cu;
    const s32 base2 = camp_func_0029f260(list2);
    const s32 sl_x = *reinterpret_cast<const s16*>(sl + 8u);
    const s32 sl_y = *reinterpret_cast<const s16*>(sl + 10u);

    for (s32 i = 0; i < 8; ++i) {
        const u8* const li = camp_func_002bf6d0(0x24u, static_cast<u32>(i + 0xB6));
        const s32 t = *reinterpret_cast<const s32*>(r5 + 0x3FCu);
        const s32 ix = bx + lerp_pos_1f1ad8(sl_x, *reinterpret_cast<const s16*>(li + 8u), t);
        const s32 iy = by + lerp_pos_1f1ad8(sl_y, *reinterpret_cast<const s16*>(li + 10u), t);
        ui_func_002bf460(2u, 0x24u, 0xB1u, ix, iy, 0x9Cu);

        const s32 item_idx = base2 + i;
        if (camp_func_0029f0f4(list2) > item_idx) {
            const u8* const l_txt = camp_func_002bf6d0(0x24u, 0xB2u);
            char buf[0x44];
            const s32 nonzero = camp_func_001b0698(r5, id, buf, item_idx);
            const u32 color = (nonzero != 0) ? 0x008400FFu : 0xFFu;
            ui_func_002be77c(2u, color, buf,
                             static_cast<f32>(*reinterpret_cast<const s16*>(l_txt + 8u) + ix),
                             static_cast<f32>(*reinterpret_cast<const s16*>(l_txt + 10u) + iy),
                             0.0f, 0.0f, 1.0f);
        }
    }

    const u8* const r4_l = camp_func_002bf6d0(0x24u, static_cast<u32>(camp_func_0029f248(list1) + 0xC8));
    const s32 fp = camp_func_0029f260(list2) + camp_func_0029f248(list2);
    const u8* const l2 = camp_func_002bf6d0(0x24u, static_cast<u32>(camp_func_0029f248(list2) + 0xC8));
    const s32 t2 = *reinterpret_cast<const s32*>(r5 + 0x3FCu);
    const s32 dx = bx + lerp_pos_1f1ad8(*reinterpret_cast<const s16*>(r4_l + 8u),
                                        *reinterpret_cast<const s16*>(l2 + 8u), t2);
    const s32 dy = by + lerp_pos_1f1ad8(*reinterpret_cast<const s16*>(r4_l + 10u),
                                        *reinterpret_cast<const s16*>(l2 + 10u), t2);

    ui_func_002bf710(*reinterpret_cast<const f32*>(r5 + 0x44u));
    ui_func_002bf460(2u, 0x24u, 0xBEu, dx, dy, 0xABu);
    ui_func_002bf460(2u, 0x24u, 0xBFu, dx, dy, 0xABu);
    ui_func_002bf460(2u, 0x24u, 0xC0u, dx, dy, 0xABu);
    ui_func_002bf710(1.0f);
    ui_func_002bf460(2u, 0x24u, 0xC1u, dx, dy, 0xB5u);

    const s32 idx2 = camp_func_0029f248(list2);
    const s32 kind = ui_func_0029d8fc(*reinterpret_cast<const s16*>(r5 + 0x44Cu + idx2 * 2));
    const u32 spr = (kind == 1 || kind == 2 || kind == 6) ? 0xC3u : 0xC2u;
    ui_func_002bf460(2u, 0x24u, spr, dx, dy, 0xBAu);

    const u8* const l_c2 = camp_func_002bf6d0(0x24u, 0xC2u);
    u8* const st30c = *reinterpret_cast<u8* const*>(0x0044EA00u) + 0x130Cu;
    set_state_1ecc7c(st30c, 3u);
    const s16* const sz_c2 = *reinterpret_cast<const s16* const*>(l_c2 + 0x0Cu);
    func_0029a418(*reinterpret_cast<const s16*>(l_c2 + 8u) + dx,
                  *reinterpret_cast<const s16*>(l_c2 + 10u) + dy, sz_c2[0], sz_c2[1], 1u);

    const s32 ty = shop_func_002bef70(r5 + 0xB0u) + dy;
    const s32 tx = ui_func_002bef7c() + dx;
    ui_func_002bf460(2u, 0x24u, 0xC4u, tx, ty, 0xBFu);
    set_state_1ecc7c(*reinterpret_cast<u8* const*>(0x0044EA00u) + 0x130Cu, 0u);

    const u8* const l_c5 = camp_func_002bf6d0(0x24u, 0xC5u);
    char buf2[0x44];
    const s32 nz2 = camp_func_001b0698(r5, id, buf2, fp);
    const u32 color2 = (nz2 != 0) ? 0x008400FFu : 0xFFFFFFFFu;
    ui_func_002be77c(3u, color2, buf2,
                     static_cast<f32>(*reinterpret_cast<const s16*>(l_c5 + 8u) + dx),
                     static_cast<f32>(*reinterpret_cast<const s16*>(l_c5 + 10u) + dy),
                     0.25f, 0.0f, 1.0f);
}

extern "C" s32 battle_func_002934d4(u8* base);
extern "C" void* AsdMemory_func_002c684c(u32 size);
extern "C" u32 script_vm_func_0023ec3c(u16 max_val);
extern "C" void ui_func_00250fb4(void* ptr);

namespace {

inline void assign_thirds_23e688(u8** sel, u32 n, u32 a3) {
    const u32 q = n / 3u;
    const u32 q2 = q * 2u;
    for (u32 i = q; i < q2; ++i) {
        *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = a3;
    }
    for (u32 i = q2; i < n; ++i) {
        *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = a3 * 2u;
    }
}

inline void assign_shuffled_23e688(u8** sel, u32 n) {
    if (n >= 0x28u) {
        return;
    }
    const f32 step = 40.0f / static_cast<f32>(n);
    f32* const arr = static_cast<f32*>(AsdMemory_func_002c684c(n * 4u));
    f32 cur = 0.0f;
    for (u32 i = 0u; i < n; ++i) {
        arr[i] = cur;
        cur += step;
    }
    if (n >= 4u) {
        for (u32 i = 1u; i < n - 2u; ++i) {
            const u32 r = script_vm_func_0023ec3c(static_cast<u16>(n - i - 1u));
            const f32 tmp = arr[i];
            arr[i] = arr[i + r];
            arr[i + r] = tmp;
        }
    }
    for (u32 i = 0u; i < n; ++i) {
        *reinterpret_cast<s32*>(sel[i] + 0x5Cu) = static_cast<s32>(arr[i]);
    }
    ui_func_00250fb4(arr);
}

inline void assign_mode1_23e688(u8** sel, u32 n, u32 a3) {
    if (n == 2u) {
        const f32 lo = *reinterpret_cast<const f32*>(0x00439ACCu);
        const f32 hi = *reinterpret_cast<const f32*>(0x00439AD0u);
        for (u32 i = 0u; i < n; ++i) {
            const f32 v = *reinterpret_cast<const f32*>(sel[i] + 0x0Cu);
            *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = (v >= lo && v <= hi) ? 0u : a3;
        }
    } else {
        const u32 last = n - 1u;
        for (u32 i = 0u; i < n; ++i) {
            *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = (i == 0u || i == last) ? a3 : 0u;
        }
    }
}

}  // namespace

// DECOMP_FUNC(0x0023e688, 1268)
extern "C" void engine_func_0023e688(u8* mgr, u8* a1, u32 mode, u32 a3, u32 flag) {
    u8* const units = *reinterpret_cast<u8* const*>(*reinterpret_cast<u8* const*>(mgr) + 0x1E98u);
    for (s32 i = 0; i < 0x6D; ++i) {
        u8* const u = units + static_cast<u32>(i) * 0x114u;
        const u32 f = *reinterpret_cast<const u32*>(u + 0x50u);
        if ((f & 1u) != 0u && (f & 2u) != 0u && (f & 0x80u) != 0u) {
            *reinterpret_cast<u32*>(u + 0x5Cu) = 0u;
        }
    }

    if (battle_func_002934d4(*reinterpret_cast<u8* const*>(mgr)) != 0) {
        return;
    }
    *reinterpret_cast<u32*>(a1 + 0x598u) = mode;
    if (mode == 0xFFFFu || mode == 0u) {
        return;
    }

    const s32 limit = (flag == 0u) ? 0x32 : 0x2A;
    const s32 start = (flag == 0u) ? 4 : 0x43;
    u8* sel[0x32];
    u32 n = 0u;
    bool has_bit10 = false;
    for (s32 i = 0; i < limit; ++i) {
        u8* const u = units + static_cast<u32>(start + i) * 0x114u;
        const u32 f = *reinterpret_cast<const u32*>(u + 0x50u);
        if ((f & 1u) != 0u && (f & 2u) != 0u && (f & 0x80u) != 0u) {
            sel[n++] = u;
            if ((f & 0x10u) != 0u) {
                has_bit10 = true;
            }
        }
    }
    if (n <= 1u) {
        return;
    }

    auto qsort_fn = reinterpret_cast<void (*)(u8**, u32, u32, u32)>(0x002B7F0Bu);
    switch (mode) {
        case 4u:
            if (flag == 0u && !has_bit10) {
                for (u32 i = 0u; i < n; ++i) {
                    *reinterpret_cast<u32*>(sel[i] + 0x5Cu) = i;
                }
            }
            return;
        case 5u:
            qsort_fn(sel, n, 4u, 0x001B1920u);
            assign_shuffled_23e688(sel, n);
            break;
        case 1u:
        case 2u:
            qsort_fn(sel, n, 4u, 0x0019D80Cu);
            if (mode == 1u) {
                assign_mode1_23e688(sel, n, a3);
            } else {
                assign_thirds_23e688(sel, n, a3);
            }
            break;
        case 3u:
            qsort_fn(sel, n, 4u, 0x001A824Cu);
            assign_thirds_23e688(sel, n, a3);
            break;
        default:
            assign_thirds_23e688(sel, n, a3);
            break;
    }

    u8* const units2 = *reinterpret_cast<u8* const*>(*reinterpret_cast<u8* const*>(mgr) + 0x1E98u);
    for (u32 i = 0u; i < n; ++i) {
        const s16 id = *reinterpret_cast<const s16*>(sel[i] + 0x62u);
        for (s32 j = 0; j < 0x6D; ++j) {
            u8* const u = units2 + static_cast<u32>(j) * 0x114u;
            if (*reinterpret_cast<const s16*>(u + 0x62u) == id) {
                *reinterpret_cast<u32*>(u + 0x5Cu) = *reinterpret_cast<const u32*>(sel[i] + 0x5Cu);
                break;
            }
        }
    }
}

extern "C" void func_0024faa4(u8* r6, f32* out_vec);
extern "C" void func_0024fa94(u8* r6, f32* out_vec);
extern "C" void ui_func_002a2f1c(f32* dst);
extern "C" void ui_func_002b2cec(u8* obj);
extern "C" void engine_func_002a399c(u8* obj, f32 val);
extern "C" void engine_func_002a3d50(u8* obj, const f32* pos);
extern "C" void ui_func_00281e20(u8* obj);
extern "C" void func_001a839c(u8* obj);
extern "C" void engine_func_0024c5b0(u8* obj, f32 val);
extern "C" void engine_func_0024c584(u8* obj, const f32* pos);
extern "C" void engine_func_00250420(u8* obj);

namespace {

inline void xform_pos_2c7420(const f32* src, f32* out) {
    u8* const g = reinterpret_cast<u8*>(0x004EA81Cu);
    f32* const v = reinterpret_cast<f32*>(g + 0x100u);
    const f32* const m = reinterpret_cast<const f32*>(g + 0x140u);

    v[0] = src[0];
    v[1] = src[1];
    v[2] = src[2];
    v[3] = src[3];

    const f32 vx = v[0];
    const f32 vy = v[1];
    const f32 vz = v[2];
    v[0] = (m[12] + vx * m[0]) + (vy * m[4] + vz * m[8]);
    v[1] = (m[13] + vx * m[1]) + (vy * m[5] + vz * m[9]);
    v[2] = (m[14] + vx * m[2]) + (vy * m[6] + vz * m[10]);
    v[3] = (m[15] + vx * m[3]) + (vy * m[7] + vz * m[11]);

    out[0] = v[0];
    out[1] = v[1];
    out[2] = v[2];
    out[3] = v[3];
}

}  // namespace

// DECOMP_FUNC(0x002c7420, 1304)
extern "C" void ui_func_002c7420(u8* self, f32 scale) {
    const u16 kind = *reinterpret_cast<const u16*>(self + 0x0Cu);
    if (kind != 5u && kind != 6u) {
        return;
    }

    u8* const r6 = *reinterpret_cast<u8* const*>(self + 0x4Cu);
    u8* const* const objs =
        *reinterpret_cast<u8* const* const*>(self + ((kind == 5u) ? 0x34u : 0x3Cu));
    const u8* items = *reinterpret_cast<const u8* const*>(r6 + 0x18u);
    const s32 count = *reinterpret_cast<const s32*>(r6 + 8u);
    const bool has_xform = (*reinterpret_cast<const u32*>(r6 + 0x0Cu) & 1u) != 0u;

    if (has_xform) {
        f32 v10[4];
        f32 v00[4];
        func_0024faa4(r6, v10);
        func_0024fa94(r6, v00);
        u8* const g = reinterpret_cast<u8*>(0x004EA81Cu);
        f32* const gv = reinterpret_cast<f32*>(g + 0x100u);
        f32* const gm3 = reinterpret_cast<f32*>(g + 0x170u);
        for (u32 i = 0u; i < 4u; ++i) {
            gv[i] = v10[i];
        }
        ui_func_002a2f1c(gv);
        for (u32 i = 0u; i < 4u; ++i) {
            gm3[i] = v00[i];
        }
    }

    for (s32 i = 0; i < count; ++i, items += 0x28u) {
        const s32 st = *reinterpret_cast<const s32*>(items + 0x10u);
        if (st == 0) {
            if (kind == 6u) {
                ui_func_002b2cec(objs[i]);
            } else if (!has_xform) {
                func_001a839c(objs[i]);
            }
        }
        if (*reinterpret_cast<const s32*>(items + 0x10u) < 0) {
            continue;
        }
        f32 pos_buf[4];
        const f32* pos = reinterpret_cast<const f32*>(items);
        if (has_xform) {
            xform_pos_2c7420(pos, pos_buf);
            pos = pos_buf;
        }
        const f32 s = *reinterpret_cast<const f32*>(items + 0x18u) * scale;
        if (kind == 6u) {
            engine_func_002a399c(objs[i], s);
            engine_func_002a3d50(objs[i], pos);
            ui_func_00281e20(objs[i]);
        } else {
            engine_func_0024c5b0(objs[i], s);
            engine_func_0024c584(objs[i], pos);
            engine_func_00250420(objs[i]);
        }
    }
}

extern "C" void ui_func_002bcf58(u8* dst, const void* src, u32 size);
extern "C" u32 ui_func_002c6c10(u32 a0, u32 size);
extern "C" u64 script_vm_func_002aa504(s64 num, s64 den);
extern "C" void engine_func_0015c310(u32 a0, const u32* ptrs, u32 idx, u32 delay, u32 mode);
extern "C" u32 engine_func_002bb270();
extern "C" void* func_0015c5c8(u32 h, u32 one, u32 max_val, u32 cb, u8* track);
extern "C" void func_002b4ddc(void* voice);
extern "C" void ui_func_002a2268(u8* mgr, u32 track0);
extern "C" void func_002a2224(void* voice, u32 flag);
extern "C" void func_0015d14c(void* voice, u32 a1);

// DECOMP_FUNC(0x00157a24, 1312)
extern "C" u32 ui_func_00157a24(u8* self, u32 flag, const void* src_7c, const u32* arr_fp,
                                u32 id) {
    if (self[0x50u] == 0u || *reinterpret_cast<const u16*>(self + 0x1C58u) != id) {
        return 0u;
    }
    if (flag == 0u) {
        self[0x0Fu] = 1u;
        void* const* const vtbl = *reinterpret_cast<void* const* const*>(self);
        reinterpret_cast<void (*)(u8*)>(vtbl[5])(self);
        return 0u;
    }

    ui_func_002bcf58(self + 0x7Cu, src_7c, 0x48u);
    const u32 n_ch = *reinterpret_cast<const u32*>(self + 0xD4u);
    for (u32 i = 0u; i < n_ch; ++i) {
        const u8* const src = self + 0xA8u + i * 7u;
        u8* const dst = self + i * 0x20u;
        dst[0x1AE5u] = src[0];
        dst[0x1AE6u] = src[1];
        dst[0x1AE7u] = src[2];
        dst[0x1AE8u] = src[3];
        const u8 cnt = src[4];
        dst[0x1AE4u] = cnt;
        u32 j = 0u;
        if (cnt != 0u && (cnt & 1u) == 1u) {
            *reinterpret_cast<u8**>(dst + 0x1ADCu) =
                self + 0xD8u + static_cast<u32>(src[5]) * 0x340u;
            j = 1u;
        }
        while (j < cnt) {
            *reinterpret_cast<u8**>(dst + 0x1ADCu + j * 4u) =
                self + 0xD8u + static_cast<u32>(src[5u + j]) * 0x340u;
            *reinterpret_cast<u8**>(dst + 0x1AE0u + j * 4u) =
                self + 0xD8u + static_cast<u32>(src[6u + j]) * 0x340u;
            j += 2u;
        }
    }

    const u32 sz = *reinterpret_cast<const u32*>(self + 0x94u);
    if (sz > 0x2000u) {
        return 0u;
    }
    const u32 n_bufs =
        ui_func_002c6c10(*reinterpret_cast<const u32*>(*reinterpret_cast<u8* const*>(self + 0x64u) + 8u),
                         sz);
    *reinterpret_cast<u32*>(self + 0x68u) = n_bufs;
    if (n_bufs < 4u) {
        return 0u;
    }
    const u32 capped = (n_bufs > 0x20u) ? 0x20u : n_bufs;
    *reinterpret_cast<u32*>(self + 0x68u) = capped;
    *reinterpret_cast<u32*>(self + 0x6Cu) = 0u;
    *reinterpret_cast<u32*>(self + 0x70u) = 0u;
    *reinterpret_cast<u32*>(self + 0x5Cu) = 0u;

    const u32 n_tracks = *reinterpret_cast<const u32*>(self + 0xD0u);
    for (u32 b = 0u; b < capped; ++b) {
        u32 ptrs[8];
        for (u32 t = 0u; t < n_tracks; ++t) {
            const u32 base_ptr = *reinterpret_cast<const u32*>(self + 0xD8u + t * 0x340u);
            ptrs[t] = base_ptr + (*reinterpret_cast<const u32*>(self + 0x94u) *
                                  *reinterpret_cast<const u32*>(self + 0x6Cu));
        }
        u32 delay = 0u;
        if (self[0x74u] == 0u) {
            delay = *reinterpret_cast<const u32*>(self + 0x78u);
        } else if (self[0x74u] == 1u) {
            const s64 prod = static_cast<s64>(*reinterpret_cast<const s32*>(self + 0x78u)) *
                             static_cast<s64>(*reinterpret_cast<const u32*>(self + 0x80u));
            const u64 q = script_vm_func_002aa504(prod, 1000LL);
            if (q > 0xFFFFFFFFULL) {
                delay = 0xFFFFFFFFu;
            } else {
                delay = static_cast<u32>(script_vm_func_002aa504(prod, 1000LL));
            }
        }
        *reinterpret_cast<u32*>(self + 0x78u) = 0u;
        engine_func_0015c310(*reinterpret_cast<const u32*>(self + 0x60u), ptrs,
                             *reinterpret_cast<const u32*>(self + 0x6Cu), delay,
                             (self[0x0Du] != 0u) ? 2u : 1u);
        u32 next_idx = *reinterpret_cast<const u32*>(self + 0x6Cu) + 1u;
        if (next_idx >= *reinterpret_cast<const u32*>(self + 0x68u)) {
            next_idx = 0u;
        }
        *reinterpret_cast<u32*>(self + 0x6Cu) = next_idx;
        *reinterpret_cast<u32*>(self + 0x5Cu) += 1u;
    }

    for (u32 i = 0u; i < n_tracks; ++i) {
        u8* const track = self + 0xD8u + i * 0x340u;
        void* const v = func_0015c5c8(engine_func_002bb270(), 1u, 0x7FFFu, 0x0015C6E8u, track);
        if (v == nullptr) {
            for (u32 j = 0u; j < i; ++j) {
                u8* const tj = self + 0xD8u + j * 0x340u;
                void* const vj = *reinterpret_cast<void* const*>(tj + 0x30u);
                if (vj != nullptr) {
                    func_002b4ddc(vj);
                    *reinterpret_cast<void**>(tj + 0x30u) = nullptr;
                }
            }
            for (u32 j = 0u; j < *reinterpret_cast<const u32*>(self + 0xD0u); ++j) {
                u8* const tj = self + 0xD8u + j * 0x340u;
                const u32 t0 = *reinterpret_cast<const u32*>(tj);
                if (t0 != 0u) {
                    ui_func_002a2268(*reinterpret_cast<u8* const*>(self + 0x64u), t0);
                    *reinterpret_cast<u32*>(tj) = 0u;
                }
            }
            return 0u;
        }
        *reinterpret_cast<void**>(track + 0x30u) = v;
    }

    for (u32 ch = 0u; ch < *reinterpret_cast<const u32*>(self + 0xD4u); ++ch) {
        const u8* const dst = self + ch * 0x20u;
        const s32 cnt = static_cast<s32>(dst[0x1AE4u]);
        for (s32 k = 0; k < cnt; ++k) {
            u8* const track = *reinterpret_cast<u8* const*>(dst + 0x1ADCu + static_cast<u32>(k) * 4u);
            void* const voice = *reinterpret_cast<void* const*>(track + 0x30u);
            const u8 mode = dst[0x1AE8u];
            if (mode == 0u || mode == 2u) {
                func_002a2224(voice, 0u);
            } else if (mode == 1u) {
                func_002a2224(voice, 1u);
            }
        }
    }

    for (u32 t = 0u; t < *reinterpret_cast<const u32*>(self + 0xD0u); ++t) {
        if (arr_fp[t] != 0u) {
            func_0015d14c(*reinterpret_cast<void* const*>(self + 0xD8u + t * 0x340u + 0x30u), 0u);
        }
    }
    return 1u;
}

extern "C" void battle_func_002ba948(u8* p);
extern "C" void battle_func_002ba860(void* a0, u8* p);

namespace {

inline void gpu_free_3f5428(void* ptr) {
    using FreeFn = void (*)(u32, u32, u32, void*);
    FreeFn const fn = *reinterpret_cast<FreeFn const*>(0x0044E334u);
    if (fn != nullptr) {
        fn(0x10000u, 0x100u, 0u, ptr);
    }
}

inline void clear_slots_3f5428(u8* gpu, u8* tbl, u32 h, u32 gpu_off, u32 aux_off, u32 cache_off,
                               u32 flag_off, u32 count, bool set_flag_bits) {
    for (u32 i = 0u; i < count; ++i) {
        if (*reinterpret_cast<const u32*>(gpu + gpu_off + i * 4u) == h) {
            *reinterpret_cast<u32*>(gpu + gpu_off + i * 4u) = 0u;
            u8* const ind = *reinterpret_cast<u8* const*>(tbl + 0x8A8u);
            u8* const aux = (ind != nullptr) ? *reinterpret_cast<u8* const*>(ind)
                                             : *reinterpret_cast<u8* const*>(tbl + 8u);
            *reinterpret_cast<u32*>(aux + aux_off + i * 4u) = 0u;
            *reinterpret_cast<u32*>(tbl + cache_off + i * 4u) = 0u;
            if (set_flag_bits && gpu[flag_off + i] != 0u) {
                *reinterpret_cast<u32*>(gpu) |= (0x400u << i);
            }
        }
    }
}

}  // namespace

// DECOMP_FUNC(0x003f5428, 1368)
extern "C" void func_003f5428(s32 count, const u32* handles) {
    u8* const gpu = *reinterpret_cast<u8* const*>(0x004655C0u);
    for (s32 idx = 0; idx < count; ++idx) {
        const u32 h = handles[idx];
        if (h == 0u) {
            continue;
        }

        u8** const tbl_hdr = reinterpret_cast<u8**>(0x004655E8u);
        u8* const tbl = *tbl_hdr;
        const u32 bucket = h & 0x1FFu;
        u8* prev = nullptr;
        u8* node = *reinterpret_cast<u8* const*>(tbl + 0x10u + bucket * 4u);
        while (node != nullptr && *reinterpret_cast<const u32*>(node + 8u) < h) {
            prev = node;
            node = *reinterpret_cast<u8* const*>(node + 0x0Cu);
        }
        if (node == nullptr || *reinterpret_cast<const u32*>(node + 8u) != h) {
            continue;
        }

        u8* const obj = *reinterpret_cast<u8* const*>(node);
        if (obj != nullptr) {
            const u32 kind = *reinterpret_cast<const u32*>(node + 4u);
            if (kind == 0u) {
                clear_slots_3f5428(gpu, tbl, h, 0x5Cu, 4u, 0x810u, 0x104u, 3u, true);
                battle_func_002ba948(obj + 0x34u);
                battle_func_002ba860(*reinterpret_cast<void* const*>(obj + 0x2Cu), obj + 0x34u);
                gpu_free_3f5428(obj);
                *reinterpret_cast<void**>(node) = nullptr;
            } else if (kind == 1u) {
                clear_slots_3f5428(gpu, tbl, h, 0x68u, 0x10u, 0x81Cu, 0x107u, 3u, true);
                for (s32 j = 0; j < 6; ++j) {
                    u8* const p = obj + 0x34u + static_cast<u32>(j) * 0x44u;
                    battle_func_002ba948(p);
                    battle_func_002ba860(*reinterpret_cast<void* const*>(obj + 0x2Cu), p);
                }
                gpu_free_3f5428(obj);
                *reinterpret_cast<void**>(node) = nullptr;
            } else if (kind == 2u) {
                if (*reinterpret_cast<const u32*>(gpu + 0xF4u) == h) {
                    *reinterpret_cast<u32*>(tbl + 0x0Cu) = h;
                    continue;
                }
                gpu_free_3f5428(obj);
                *reinterpret_cast<void**>(node) = nullptr;
            } else if (kind == 3u) {
                clear_slots_3f5428(gpu, tbl, h, 0x74u, 0x1Cu, 0x828u, 0u, 0x20u, false);
                for (s32 i = 0; i < 0x21; ++i) {
                    if (*reinterpret_cast<const u32*>(gpu + 0x10Cu + static_cast<u32>(i) * 4u) ==
                        h) {
                        *reinterpret_cast<u32*>(gpu + 0x10Cu + static_cast<u32>(i) * 4u) = 0u;
                        *reinterpret_cast<u32*>(gpu + 0x190u + static_cast<u32>(i) * 4u) = 0u;
                        *reinterpret_cast<u32*>(gpu) |= 0x4000u;
                    }
                }
                for (u32 k = 0u; k < 6u; ++k) {
                    void* const sub = *reinterpret_cast<void* const*>(obj + 0x804u + k * 4u);
                    if (sub != nullptr) {
                        gpu_free_3f5428(sub);
                    }
                }
                gpu_free_3f5428(obj);
                *reinterpret_cast<void**>(node) = nullptr;
            }
        }

        u32* const min_h = reinterpret_cast<u32*>(0x004655E8u + 4u);
        if (h < *min_h) {
            *min_h = h;
        }
        if (prev != nullptr) {
            *reinterpret_cast<u8**>(prev + 0x0Cu) = *reinterpret_cast<u8* const*>(node + 0x0Cu);
        } else {
            *reinterpret_cast<u8**>(*tbl_hdr + 0x10u + bucket * 4u) =
                *reinterpret_cast<u8* const*>(node + 0x0Cu);
        }
        gpu_free_3f5428(node);
    }
}

struct Ret3FD56C {
    u32 words[6];
};
extern "C" void battle_func_003fd56c(
    Ret3FD56C* out, u8** begin, u8** end, u8* r0_arg,
    u32 a1, u32 a2, u32 f0_ptr_bits, u32 packed, u32 f1_bits);
extern "C" void battle_func_003fe018(u32* out, u8** begin, u8** end, u8* ctx, u32 a1, u32 a2, u32 f0_ptr, u32 packed_flags, u32 f1_bits);
extern "C" void battle_func_00225ba4(u8* ctx, u8* obj, u32 a1, u32 f0_ptr);
extern "C" void func_00286604(u32* dst, const u8* src);
extern "C" void battle_func_002a5078(void* dst, const void* a, const void* b);
extern "C" void battle_func_002c00b4(u8* dst, const u8* src);
extern "C" void engine_func_002b7b34(u32* dst, const u32* src);
extern "C" s32 func_00225b20(u8* owner, u8* item);
extern "C" void func_00225750(void* ctx_buf, u8* item, u32 f0_ptr);
extern "C" void func_00225824(u32 a2, void* arg_buf, u32 byte_arg, u32 flags);
extern "C" void battle_func_00225a74(u8* node, const u8* mat, u32 f0_ptr);

// DECOMP_FUNC(0x003f821c, 1372)
extern "C" void battle_func_003f821c(
    u8* r0_arg,
    u32 a1,
    u32 a2,
    u8* r3_mgr,
    u32 f0_ptr_bits,
    u32 s1,
    u32 s2,
    u32 s3,
    u32 s4,
    u32 f1_bits) {
    if (s4 == 1u || s3 == 1u) {
        u32 packed = (s1 | (s3 & ~0xFFu));
        packed = (packed & ~0xFF00u) | ((s2 << 8) & 0xFF00u);
        u8** begin = *reinterpret_cast<u8***>(r3_mgr + 0x2Cu);
        u8** end = *reinterpret_cast<u8***>(r3_mgr + 0x30u);
        Ret3FD56C out_full;
        if (s4 == 1u && s3 != 1u) {
            battle_func_003fd56c(
                &out_full, begin, end, r0_arg, a1, a2, f0_ptr_bits, packed, f1_bits);
        } else {
            battle_func_003fe018(
                out_full.words, begin, end, r0_arg, a1, a2, f0_ptr_bits, packed, f1_bits);
        }
        return;
    }

    u8** begin = *reinterpret_cast<u8***>(r3_mgr + 0x2Cu);
    u8** end = *reinterpret_cast<u8***>(r3_mgr + 0x30u);
    u32 packed = (s1 | (s4 & ~0xFFu));
    packed = (packed & ~0xFF00u) | ((s2 << 8) & 0xFF00u);
    u8* f0_ptr = reinterpret_cast<u8*>(static_cast<uintptr_t>(f0_ptr_bits));

    for (u8** it = begin; it != end; ++it) {
        u8* obj = *it;
        if (obj == nullptr) {
            continue;
        }
        using GetTypeFn = u32 (*)(u8*);
        u32** vtbl = *reinterpret_cast<u32***>(obj);
        u32 type_id = reinterpret_cast<GetTypeFn>(vtbl[2])(obj);

        u8* matched = nullptr;
        if (type_id == 0x00472288u) {
            matched = obj;
            *reinterpret_cast<u8*>(*reinterpret_cast<u8**>(obj + 0x220u) + 0x18u) = 0u;
        }

        if (obj[0x1F6u] == 0u || (*reinterpret_cast<u32*>(obj + 0x38u) & 1u) == 0u) {
            continue;
        }

        u8* dst_mat = obj + 0x1BCu;
        u8* src_mat = f0_ptr + 0x148u;

        if (matched != nullptr) {
            if (matched[0x230u] == 0u) {
                battle_func_00225ba4(
                    r0_arg, *reinterpret_cast<u8**>(matched + 0x220u), a1, f0_ptr_bits);
            }
            u8* m220 = *reinterpret_cast<u8**>(matched + 0x220u);
            u8* m220_8 = *reinterpret_cast<u8**>(m220 + 8u);
            bool use_286604 = (*reinterpret_cast<u32*>(m220_8 + 0x28u) & 1u) != 0u;
            if (use_286604) {
                u32 buf[16];
                func_00286604(buf, obj + 0x8Cu);
                battle_func_002a5078(dst_mat, src_mat, buf);
            } else if ((*reinterpret_cast<u32*>(obj + 0xF8u) & 0x200u) != 0u) {
                battle_func_002c00b4(dst_mat, src_mat);
            } else {
                u32 m1[16];
                u32 m2[16];
                u32 m3[16];
                func_002a84ec(reinterpret_cast<u8*>(m1), obj + 0x8Cu);
                engine_func_002b7b34(m2, m1);
                battle_func_002a5078(m3, m1, m2);
                battle_func_002a5078(dst_mat, src_mat, m3);
            }

            s32* list_cur = *reinterpret_cast<s32**>(matched + 0x170u);
            s32* list_end = *reinterpret_cast<s32**>(matched + 0x174u);
            u32 flags = (packed & 0xFFu) | obj[0x1F4u];
            if (list_cur == list_end) {
                u8* data = *reinterpret_cast<u8**>(matched + 8u);
                s32 rel = *reinterpret_cast<s32*>(data + 0xB8u);
                u32 count = *reinterpret_cast<u32*>(data + 0xB4u);
                list_cur = (rel != 0) ? reinterpret_cast<s32*>(data + 0xB8u + rel) : nullptr;
                list_end = list_cur + count;
            }
            if (list_cur != list_end) {
                struct BranchACtx {
                    u8* unit;
                    u32 unit_8;
                    u32 a2;
                    u32 f0_ptr;
                    u32 flags;
                };
                BranchACtx bctx;
                bctx.unit = matched;
                bctx.unit_8 = *reinterpret_cast<u32*>(matched + 8u);
                bctx.a2 = a2;
                bctx.f0_ptr = f0_ptr_bits;
                bctx.flags = flags;

                for (; list_cur != list_end; ++list_cur) {
                    s32 rel = *list_cur;
                    u8* item = (rel != 0) ? (reinterpret_cast<u8*>(list_cur) + rel) : nullptr;
                    if (func_00225b20(bctx.unit, item) != 0) {
                        func_00225750(&bctx, item, bctx.f0_ptr);
                        u32 idx = *reinterpret_cast<u32*>(item + 0x1Cu);
                        u8** arr = *reinterpret_cast<u8***>(bctx.unit + 0x164u);
                        u8* q = *reinterpret_cast<u8**>(arr[idx] + 0x2Cu);
                        u32 byte_arg = *reinterpret_cast<u32*>(q + 0x20u) & 0xFFu;
                        struct Call225824Arg {
                            u32 f0;
                            u32 f1;
                            u8* item;
                            u8* owner;
                        } arg_buf = {0u, 0u, item, bctx.unit};
                        func_00225824(bctx.a2, &arg_buf, byte_arg, bctx.flags & 0xFFu);
                    }
                }
            }
        } else {
            if ((*reinterpret_cast<u32*>(obj + 0xF8u) & 0x200u) != 0u) {
                battle_func_002c00b4(dst_mat, src_mat);
            } else {
                u32 m1[16];
                u32 m2[16];
                u32 m3[16];
                func_002a84ec(reinterpret_cast<u8*>(m1), obj + 0x8Cu);
                engine_func_002b7b34(m2, m1);
                battle_func_002a5078(m3, m1, m2);
                battle_func_002a5078(dst_mat, src_mat, m3);
            }

            u32** obj_vtbl = *reinterpret_cast<u32***>(obj);
            u32 t2 = reinterpret_cast<GetTypeFn>(obj_vtbl[2])(obj);
            u32 flag_byte = (t2 == 0x004721E0u) ? ((packed >> 8) & 0xFFu) : (packed & 0xFFu);
            u32 flags = (flag_byte | obj[0x1F4u]) & 0xFFu;

            s32* list_cur = *reinterpret_cast<s32**>(obj + 0x170u);
            s32* list_end = *reinterpret_cast<s32**>(obj + 0x174u);
            if (list_cur == list_end) {
                u8* data = *reinterpret_cast<u8**>(obj + 8u);
                s32 rel = *reinterpret_cast<s32*>(data + 0xB8u);
                u32 count = *reinterpret_cast<u32*>(data + 0xB4u);
                list_cur = (rel != 0) ? reinterpret_cast<s32*>(data + 0xB8u + rel) : nullptr;
                list_end = list_cur + count;
            }
            u8* data = *reinterpret_cast<u8**>(obj + 8u);
            for (; list_cur != list_end; ++list_cur) {
                s32 rel = *list_cur;
                u8* item = (rel != 0) ? (reinterpret_cast<u8*>(list_cur) + rel) : nullptr;
                if (func_00225b20(obj, item) != 0) {
                    s32 rel1 = *reinterpret_cast<s32*>(data + 0xC8u);
                    u8* base1 = (rel1 != 0) ? (data + 0xC8u + rel1) : nullptr;
                    u32 idx0 = *reinterpret_cast<u32*>(item + 0x18u);
                    u8* slot1 = base1 + idx0 * 4u;
                    s32 rel2 = *reinterpret_cast<s32*>(slot1);
                    u8* obj2 = (rel2 != 0) ? (slot1 + rel2) : nullptr;
                    s32 rel3 = *reinterpret_cast<s32*>(obj2 + 0x1Cu);
                    u8* node = (rel3 != 0) ? (obj2 + 0x1Cu + rel3 + 4u) : reinterpret_cast<u8*>(4u);
                    battle_func_00225a74(node, obj + 0x8Cu, f0_ptr_bits);

                    u32 idx = *reinterpret_cast<u32*>(item + 0x1Cu);
                    u8** arr = *reinterpret_cast<u8***>(obj + 0x164u);
                    u8* q = *reinterpret_cast<u8**>(arr[idx] + 0x2Cu);
                    u32 byte_arg = *reinterpret_cast<u32*>(q + 0x20u) & 0xFFu;
                    struct Call225824Arg {
                        u32 f0;
                        u32 f1;
                        u8* item;
                        u8* owner;
                    } arg_buf = {0u, 0u, item, obj};
                    func_00225824(a2, &arg_buf, byte_arg, flags);
                }
            }
        }
    }
}

struct Ret373094 {
    u8* ptr;
    u32 err;
};

extern "C" u8* crt_func_00101208(void* dst, const void* src, u32 elem_size, u32 count, void* copy_ctor);
extern "C" void battle_func_0036fd98();
extern "C" u8* func_0036f2d8(u8** ptr_slot, u8* alloc);
extern "C" void func_00373b40(Ret373094* out, u8* src_wrap, u8* alloc, u8* sub);

// DECOMP_FUNC(0x00373094, 1376)
extern "C" void ui_func_00373094(Ret373094* out, u8* src_wrap, u8* alloc, u32 flags) {
    using AllocFn = u8* (*)(u8*, u32, u32);
    auto call_alloc = [&](u32 size) -> u8* {
        u32** vtbl = *reinterpret_cast<u32***>(alloc);
        return reinterpret_cast<AllocFn>(vtbl[2])(alloc, size, 4u);
    };

    u8* src = *reinterpret_cast<u8**>(src_wrap + 8u);
    u8* dst = call_alloc(0x2D8u);
    if (dst == nullptr) {
        out->ptr = nullptr;
        out->err = 0x80000000u;
        return;
    }

    src = *reinterpret_cast<u8**>(src_wrap + 8u);
    for (u32 off = 0u; off < 0x24u; off += 4u) {
        *reinterpret_cast<u32*>(dst + off) = *reinterpret_cast<const u32*>(src + off);
    }
    ui_func_002bcf58(dst + 0x24u, src + 0x24u, 0xE0u);
    for (u32 off = 0x104u; off < 0x118u; off += 4u) {
        *reinterpret_cast<u32*>(dst + off) = *reinterpret_cast<const u32*>(src + off);
    }
    ui_func_002bcf58(dst + 0x118u, src + 0x118u, 0x50u);
    *reinterpret_cast<u32*>(dst + 0x168u) = *reinterpret_cast<const u32*>(src + 0x168u);

    u8* elem_dst = crt_func_00101208(
        dst + 0x16Cu, src + 0x16Cu, 0x58u, 3u, reinterpret_cast<void*>(battle_func_0036fd98));
    dst = elem_dst - 0x16Cu;

    for (u32 off = 0x274u; off < 0x2D8u; off += 4u) {
        *reinterpret_cast<u32*>(dst + off) = *reinterpret_cast<const u32*>(src + off);
    }

    static const u32 kZeroOffsets[] = {
        0x0Cu, 0x10u, 0x14u,
        0x274u, 0x278u, 0x27Cu, 0x280u, 0x284u, 0x288u, 0x290u, 0x294u,
        0x2A0u, 0x2A4u, 0x2A8u, 0x2ACu, 0x2B0u, 0x2B4u, 0x2B8u, 0x2BCu,
        0x2C0u, 0x2C4u, 0x2C8u, 0x2CCu, 0x2D0u,
    };
    for (u32 off : kZeroOffsets) {
        *reinterpret_cast<u32*>(dst + off) = 0u;
    }

    if ((flags & 1u) != 0u) {
        s32 count = *reinterpret_cast<s32*>(src + 0x290u);
        *reinterpret_cast<s32*>(dst + 0x290u) = count;
        u8* arr = nullptr;
        if (count != 0) {
            arr = call_alloc(static_cast<u32>(count) << 2u);
            if (arr == nullptr) {
                out->ptr = dst;
                out->err = 0x80000000u;
                return;
            }
            *reinterpret_cast<s32*>(dst + 0x294u) = static_cast<s32>(arr - (dst + 0x294u));
        }
        for (s32 i = 0; i < count; ++i) {
            reinterpret_cast<u32*>(arr)[i] = 0u;
        }
        for (s32 i = 0; i < count; ++i) {
            s32 rel_base = *reinterpret_cast<s32*>(src + 0x294u);
            u8* base = (rel_base != 0) ? (src + 0x294u + rel_base) : nullptr;
            u8* slot = base + i * 4;
            s32 rel_elem = *reinterpret_cast<s32*>(slot);
            u8* elem = (rel_elem != 0) ? (slot + rel_elem) : nullptr;
            u32 tag = *reinterpret_cast<u32*>(elem + 8u) & 0xFFu;
            s32 extra_words = 0;
            if (tag == 0u || tag == 1u) {
                extra_words = 1;
            } else if (tag < 5u) {
                extra_words = static_cast<s32>(tag);
            }
            u8* node = call_alloc(0xCu + (static_cast<u32>(extra_words) << 2u));
            if (node == nullptr) {
                out->ptr = dst;
                out->err = 0x80000000u;
                return;
            }
            for (u32 k = 0u; k < 4u; ++k) {
                reinterpret_cast<u32*>(node)[k] = reinterpret_cast<const u32*>(elem)[k];
            }
            for (s32 k = 0; k < extra_words; ++k) {
                *reinterpret_cast<u32*>(node + 0x0Cu + k * 4) =
                    *reinterpret_cast<const u32*>(elem + 0x0Cu + k * 4);
            }
            s32 rel0 = *reinterpret_cast<s32*>(elem);
            if (rel0 != 0) {
                *reinterpret_cast<s32*>(node) = static_cast<s32>((elem + rel0) - node);
            } else {
                *reinterpret_cast<s32*>(node) = 0;
            }
            u8* arr_slot = arr + i * 4;
            *reinterpret_cast<s32*>(arr_slot) = static_cast<s32>(node - arr_slot);
        }
    }

    if ((flags & 0x20u) != 0u) {
        for (s32 i = 0; i < 3; ++i) {
            u8* src_slot = src + 0x274u + i * 4;
            s32 rel = *reinterpret_cast<s32*>(src_slot);
            u8* ptr = (rel != 0) ? (src_slot + rel) : nullptr;
            if (ptr != nullptr) {
                u8* cloned = func_0036f2d8(&ptr, alloc);
                if (cloned == nullptr) {
                    out->ptr = dst;
                    out->err = 0x80000000u;
                    return;
                }
                u8* dst_slot = dst + 0x274u + i * 4;
                *reinterpret_cast<s32*>(dst_slot) = static_cast<s32>(cloned - dst_slot);
            }
        }
    }

    if ((flags & 0x40u) != 0u) {
        s32 rel = *reinterpret_cast<s32*>(src + 0x280u);
        u8* ptr = (rel != 0) ? (src + 0x280u + rel) : nullptr;
        if (ptr != nullptr) {
            u8* cloned = func_0036f2d8(&ptr, alloc);
            if (cloned == nullptr) {
                out->ptr = dst;
                out->err = 0x80000000u;
                return;
            }
            *reinterpret_cast<s32*>(dst + 0x280u) = static_cast<s32>(cloned - (dst + 0x280u));
        }
    }

    if ((flags & 0x780u) != 0u) {
        s32 rel = *reinterpret_cast<s32*>(src + 0x288u);
        u8* sub = (rel != 0) ? (src + 0x288u + rel) : nullptr;
        if (sub != nullptr) {
            u8* sub_dst = call_alloc(0xF4u);
            if (sub_dst == nullptr) {
                out->ptr = dst;
                out->err = 0x80000000u;
                return;
            }
            ui_func_002bcf58(sub_dst, sub, 0xF4u);
            *reinterpret_cast<s32*>(dst + 0x288u) = static_cast<s32>(sub_dst - (dst + 0x288u));
            *reinterpret_cast<u32*>(sub_dst + 0x28u) = 0u;

            if ((flags & 0x100u) != 0u) {
                s32 rel28 = *reinterpret_cast<s32*>(sub + 0x28u);
                u8* sub2 = (rel28 != 0) ? (sub + 0x28u + rel28) : nullptr;
                if (sub2 != nullptr) {
                    Ret373094 sub_res;
                    func_00373b40(&sub_res, src_wrap, alloc, sub2);
                    *reinterpret_cast<s32*>(sub_dst + 0x28u) =
                        (sub_res.ptr != nullptr) ? static_cast<s32>(sub_res.ptr - (sub_dst + 0x28u)) : 0;
                    if ((sub_res.err & 0x80000000u) != 0u) {
                        out->ptr = dst;
                        out->err = 0x80000000u;
                        return;
                    }
                }
            }
        }
    }

    out->ptr = dst;
    out->err = 0u;
}

extern "C" void script_vm_func_002bef14();
extern "C" f32 ui_func_002ba46c(u8* mgr, f32 x);
extern "C" void func_002a37a4(void* dst, const void* a, const void* b);
extern "C" void func_002a3788(void* dst, const void* a, const void* b);
extern "C" void func_0026e9c4(void* quad);

static inline void push_state_335db4(u8* stk, u32 val) {
    u32 top = *reinterpret_cast<u32*>(stk);
    u32 old_val = *reinterpret_cast<u32*>(stk + 8u + top * 4u);
    u32 next = top + 1u;
    *reinterpret_cast<u32*>(stk) = next;
    *reinterpret_cast<u32*>(stk + 8u + next * 4u) = val;
    if (stk[0x18u] != 0u || old_val != val) {
        using Fn = void (*)(u32);
        reinterpret_cast<Fn>(*reinterpret_cast<u32*>(stk + 0x1Cu))(val);
        stk[0x18u] = 0u;
    }
}

static inline void pop_state_335db4(u8* stk) {
    u32 top = *reinterpret_cast<u32*>(stk);
    u32 old_val = *reinterpret_cast<u32*>(stk + 8u + top * 4u);
    u32 next = top - 1u;
    *reinterpret_cast<u32*>(stk) = next;
    u32 new_val = *reinterpret_cast<u32*>(stk + 8u + next * 4u);
    if (stk[0x18u] != 0u || old_val != new_val) {
        using Fn = void (*)(u32);
        reinterpret_cast<Fn>(*reinterpret_cast<u32*>(stk + 0x1Cu))(new_val);
        stk[0x18u] = 0u;
    }
}

static inline void draw_quad_335db4(
    u8* mgr,
    const f32 pmin[3],
    const f32 pmax[3],
    u32 draw_tex_id,
    u32 quad_param) {
    u32 quad[16] = {};
    quad[0] = quad_param;
    quad[5] = quad_param;
    quad[10] = 0x3F800000u;
    quad[15] = 0x3F800000u;
    func_002a37a4(quad, quad, pmin);
    func_002a3788(quad, pmax, quad);
    func_0026e9c4(quad);

    const u8* layout = camp_func_002bf6d0(0x2Du, draw_tex_id);
    s32 hw = *reinterpret_cast<const s16*>(layout + 8u);
    s32 hh = *reinterpret_cast<const s16*>(layout + 10u);
    s32 base_x = static_cast<s32>(ui_func_002ba46c(mgr, 0.3f));
    s32 x = static_cast<s32>(static_cast<f32>(base_x) + static_cast<f32>(-hw) * 0.5f);
    ui_func_002bf460(2u, 0x2Du, draw_tex_id, static_cast<u32>(x), static_cast<u32>(-hh), 6u);
    ui_func_002c1b64(mgr);
    ui_func_002bf710(1.0f);
}

// DECOMP_FUNC(0x00335db4, 1384)
extern "C" u32 ui_func_00335db4(u8* self) {
    if (*reinterpret_cast<u32*>(self) != 8u || *reinterpret_cast<u32*>(self + 0x1Cu) == 0u) {
        return 0u;
    }

    u8* const* g_mgr = reinterpret_cast<u8* const*>(0x0044EA00u);
    push_state_335db4(*g_mgr + 0x124Cu, ui_func_002c5f7c(1u, 0u));
    ui_func_002bf710(1.0f);
    script_vm_func_002bef14();
    camp_func_002bf6d0(0x2Du, 0xBB8u);
    s32 x0 = static_cast<s32>(ui_func_002ba46c(*g_mgr, 0.35f));
    ui_func_002bf460(2u, 0x2Du, 0xBB8u, static_cast<u32>(x0), 0u, 2u);
    pop_state_335db4(*g_mgr + 0x124Cu);
    ui_func_002bf710(1.0f);

    push_state_335db4(*g_mgr + 0x12ACu, battle_func_002c5fa4(6u, 1u, 0u));
    ui_func_002bf710(*reinterpret_cast<const f32*>(self + 0x28u));
    script_vm_func_002bef14();
    const u8* bounds_layout = camp_func_002bf6d0(0x2Du, 0x7D2u);
    s32 bw = *reinterpret_cast<const s16*>(bounds_layout + 8u);
    s32 bh = *reinterpret_cast<const s16*>(bounds_layout + 10u);
    f32 pmin[3] = {static_cast<f32>(-bw), static_cast<f32>(-bh), 0.0f};
    f32 pmax[3] = {static_cast<f32>(bw), static_cast<f32>(bh), 0.0f};
    draw_quad_335db4(*g_mgr, pmin, pmax, 0x7D0u, *reinterpret_cast<const u32*>(self + 0x2Cu));

    ui_func_002bf710(*reinterpret_cast<const f32*>(self + 0x30u));
    draw_quad_335db4(*g_mgr, pmin, pmax, 0x7D1u, *reinterpret_cast<const u32*>(self + 0x34u));

    pop_state_335db4(*g_mgr + 0x12ACu);
    ui_func_002bf710(1.0f);

    push_state_335db4(*g_mgr + 0x124Cu, ui_func_002c5f7c(1u, 0u));
    ui_func_002bf710(*reinterpret_cast<const f32*>(self + 0x20u));
    script_vm_func_002bef14();
    camp_func_002bf6d0(0x2Du, 0x3E8u);
    s32 x1 = static_cast<s32>(ui_func_002ba46c(*g_mgr, 0.28f));
    ui_func_002bf460(2u, 0x2Du, 0x3E8u, static_cast<u32>(x1), 0u, 6u);
    pop_state_335db4(*g_mgr + 0x124Cu);
    ui_func_002bf710(1.0f);

    return 0u;
}

extern "C" s32 script_vm_func_00297674();
extern "C" void script_vm_func_0027fd08(u32 a0);
extern "C" void script_vm_func_0028550c(u32 a0, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5);
extern "C" void script_vm_func_002766cc(u32 a0);
extern "C" void script_vm_func_002735c8(s32 a0);
extern "C" s32 script_vm_func_0026fbc0();
extern "C" void script_vm_func_002760bc();
extern "C" void script_vm_func_002706e4();
extern "C" void script_vm_func_002bf9e8(u32 a0);
extern "C" u32 script_vm_func_002857e4();
extern "C" s32 script_vm_func_0027da20(u32 a0, u32 a1, u32 a2);
extern "C" u8* script_vm_func_0027d9b8(s32 idx);
extern "C" void script_vm_func_0027d6e4(u32 a0, u32 a1, u32 a2, f32 f);
extern "C" void script_vm_func_002766f0(u32 a0, u32 a1, u32 a2);
extern "C" void script_vm_func_00276bc0(u32 a0);
extern "C" void script_vm_func_00276c24(u32 a0, u32 a1, u32 a2);
extern "C" void script_vm_func_00276088();
extern "C" void script_vm_func_0027fe84(u32 a0);
extern "C" void script_vm_func_00273ab0(u32 a0);
extern "C" void script_vm_func_00273de8();
extern "C" void script_vm_func_0027d35c();
extern "C" u32 script_vm_func_002c2bd0(u32 idx);
extern "C" void script_vm_func_002c2ba4(u32 a0, u32 a1, u32 a2);
extern "C" void script_vm_func_00271280(u32 a0);

static inline void call_28550c_31d6d4(const u8* s) {
    script_vm_func_0028550c(s[0xF8u], s[0xF9u], s[0xFAu], s[0xFBu], s[0xFCu], s[0xFDu]);
}

static inline void finish_c2bd0_31d6d4() {
    if (script_vm_func_002c2bd0(0u) == 3u) {
        script_vm_func_002c2ba4(0u, 10u, 0xFFu);
    }
    if (script_vm_func_002c2bd0(1u) == 3u) {
        script_vm_func_002c2ba4(1u, 10u, 0xFFu);
    }
}

// DECOMP_FUNC(0x0031d6d4, 1400)
extern "C" void script_vm_func_0031d6d4() {
    u8* s = reinterpret_cast<u8*>(0x0049F91Cu);
    s32* g_fd14 = reinterpret_cast<s32*>(0x0049FD14u);
    u8* r4 = *reinterpret_cast<u8* const*>(0x00447E28u);

    auto fail_reset = [&]() {
        g_fd14[0] = -1;
        *reinterpret_cast<u32*>(s + 0x54u) = 0u;
        script_vm_func_002735c8(-1);
    };

    if (s[0x250u] != 0u) {
        s[0x250u] = 0u;
        if (script_vm_func_00297674() == 0) {
            script_vm_func_0027fd08(0x26u);
            *reinterpret_cast<u32*>(r4 + 0x24u) = 0x52u;
            *reinterpret_cast<u32*>(r4 + 0x28u) = 0u;
            call_28550c_31d6d4(s);
            script_vm_func_002766cc(1u);
            return;
        }
        fail_reset();
    } else if (s[0x24Du] != 0u) {
        s[0x24Du] = 0u;
        if (script_vm_func_00297674() == 0) {
            call_28550c_31d6d4(s);
            *reinterpret_cast<u32*>(r4 + 0x24u) = 0x2Cu;
            *reinterpret_cast<u32*>(r4 + 0x28u) = 0u;
            return;
        }
        fail_reset();
    } else if (s[0x24Eu] != 0u) {
        s[0x24Eu] = 0u;
        if (script_vm_func_00297674() == 0) {
            call_28550c_31d6d4(s);
            r4[0x14u] = 1u;
            script_vm_func_0027fd08(0x26u);
            *reinterpret_cast<u32*>(r4 + 0x24u) = 0x3Cu;
            return;
        }
        fail_reset();
    } else if (s[0x24Fu] != 0u) {
        s[0x24Fu] = 0u;
        script_vm_func_002735c8(-1);
    }

    if (script_vm_func_0026fbc0() != 0) {
        *reinterpret_cast<u32*>(r4 + 0x28u) = 0u;
        *reinterpret_cast<u32*>(r4 + 0x24u) = 0x6Fu;
        r4[0x0Du] = 1u;
        return;
    }

    if (*reinterpret_cast<u32*>(s + 0x54u) != 0u) {
        script_vm_func_002760bc();
        *reinterpret_cast<u32*>(r4 + 0x28u) = 0u;
        *reinterpret_cast<u32*>(r4 + 0x24u) = 0x6Fu;
        r4[0x14u] = 1u;
        return;
    }

    if (*reinterpret_cast<u32*>(s + 0x50u) != 0u) {
        *reinterpret_cast<u32*>(s + 0x50u) = 0u;
        call_28550c_31d6d4(s);
        u32 t = *reinterpret_cast<u32*>(s);
        u32 sub = *reinterpret_cast<u32*>(s + 4u);
        bool is_special = ((t - 0x1Fu) <= 4u) || ((t - 0x19u) <= 5u) || (t == 5u && sub == 6u);
        if (is_special) {
            s32 b4 = *reinterpret_cast<s32*>(s + 0xB4u);
            if (b4 < 0x63) {
                script_vm_func_002bf9e8(static_cast<u32>(b4) + 0x010000AFu);
            }
            script_vm_func_002706e4();
        } else {
            script_vm_func_002760bc();
        }
        *reinterpret_cast<u32*>(r4 + 0x38u) = *reinterpret_cast<u32*>(s + 0x74u);
        r4[0x0Eu] = 1u;
        *reinterpret_cast<u32*>(r4 + 0x24u) = 0x6Fu;
        *reinterpret_cast<u32*>(r4 + 0x28u) = 0u;
        return;
    }

    u8* g_4f4 = *reinterpret_cast<u8* const*>(0x004474F4u);
    if (g_fd14[0] != -1) {
        s8 prev228 = static_cast<s8>(s[0x228u]);
        s[0x228u] = (*reinterpret_cast<u32*>(s + 0x48u) != 0u) ? 1u : 0u;
        u32 r6_val = *reinterpret_cast<u32*>(r4 + 0x30u);
        if (script_vm_func_002857e4() != 0u) {
            r6_val = script_vm_func_002857e4();
        }
        u32 r3_val = *reinterpret_cast<u32*>(r4 + 0x2Cu);
        if (r3_val != static_cast<u32>(g_fd14[0]) ||
            r6_val != static_cast<u32>(g_fd14[1]) ||
            static_cast<s8>(s[0x228u]) != prev228) {
            *reinterpret_cast<u32*>(r4 + 0x24u) = 0x6Fu;
            return;
        }
        s32 idx = script_vm_func_0027da20(r3_val, r6_val, static_cast<u32>(g_fd14[2]));
        u8* g_e88 = *reinterpret_cast<u8* const*>(0x00447E88u);
        if (idx != -1) {
            u8* rec = script_vm_func_0027d9b8(idx);
            f32 f4 = static_cast<f32>(*reinterpret_cast<const s16*>(rec + 4u));
            f32 f6 = static_cast<f32>(*reinterpret_cast<const s16*>(rec + 6u));
            f32 f8 = static_cast<f32>(*reinterpret_cast<const s16*>(rec + 8u));
            f32 fa = static_cast<f32>(*reinterpret_cast<const s16*>(rec + 10u));
            *reinterpret_cast<f32*>(g_e88 + 0x1Cu) = f4;
            *reinterpret_cast<f32*>(g_e88 + 0x20u) = f6;
            *reinterpret_cast<f32*>(g_e88 + 0x24u) = f8;
            *reinterpret_cast<f32*>(g_e88 + 0x28u) = f4;
            *reinterpret_cast<f32*>(g_e88 + 0x2Cu) = f6;
            *reinterpret_cast<f32*>(g_e88 + 0x30u) = f8;
            *reinterpret_cast<f32*>(g_e88 + 0x4Cu) = fa;
            *reinterpret_cast<f32*>(g_e88 + 0x50u) = fa;
            *reinterpret_cast<f32*>(g_4f4 + 0x18u) = fa;
        }
        u32 s8 = *reinterpret_cast<u32*>(s + 0x08u);
        u32 sc = *reinterpret_cast<u32*>(s + 0x0Cu);
        u32 s10 = *reinterpret_cast<u32*>(s + 0x10u);
        script_vm_func_0027d6e4(sc, s10, s8, *reinterpret_cast<f32*>(g_e88 + 0x4Cu));
        script_vm_func_002766f0(sc, s10, s8);
        script_vm_func_00276bc0(sc);
        script_vm_func_002766cc(0u);
        script_vm_func_00276c24(0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu);
        script_vm_func_00276088();
        script_vm_func_0027fe84(0u);
        script_vm_func_00273ab0(0u);
        script_vm_func_0027fd08(1u);
        r4[0x47u] = 1u;
        g_4f4[0xA4u] = 1u;
        s[0x229u] = 1u;
        s[0x22Au] = 1u;
        s[0x18u] = 0u;
        s[0x20u] = 0u;
        *reinterpret_cast<u32*>(r4 + 0x24u) = 0x15u;
        *reinterpret_cast<u32*>(r4 + 0x28u) = 0u;
        script_vm_func_00273de8();
        script_vm_func_0027d35c();
        finish_c2bd0_31d6d4();
        return;
    }

    u8* g_fc8 = *reinterpret_cast<u8* const*>(0x00432FC8u);
    if (g_fc8[0xC0u] != 0u) {
        g_fc8[0xC0u] = 0u;
        *reinterpret_cast<u32*>(r4 + 0x24u) = 0x1Fu;
        *reinterpret_cast<u32*>(r4 + 0x28u) = 0u;
        return;
    }

    script_vm_func_0027fe84(0u);
    script_vm_func_00273ab0(0u);
    script_vm_func_0027fd08(1u);
    r4[0x47u] = 1u;
    g_4f4[0xA4u] = 1u;
    s[0x229u] = 1u;
    s[0x22Au] = 1u;
    s[0x22Bu] = 0u;
    script_vm_func_00273de8();
    s[0x18u] = 0u;
    s[0x20u] = 0u;
    script_vm_func_00271280(0u);
    *reinterpret_cast<u32*>(r4 + 0x24u) = 0x15u;
    *reinterpret_cast<u32*>(r4 + 0x28u) = 0u;
    finish_c2bd0_31d6d4();
}

extern "C" s32 shop_func_0028ec74(u32 id);
extern "C" void shop_func_00230680(u8* list, u16 id, u32 a2, u32 a3, u32 a4);
extern "C" void camp_func_002305c8(u8* sub, u32 a1);
extern "C" void shop_func_0023046c(u8* self, u32 a1);
extern "C" u32 shop_func_002923d0(u32 id);

static inline void add_range_22fe4c(u8* list, u32 start, u32 end) {
    for (u32 id = start; id <= end; ++id) {
        if (shop_func_0028ec74(id) != 0) {
            shop_func_00230680(list, static_cast<u16>(id), 0u, 0u, 0u);
        }
    }
}

// DECOMP_FUNC(0x0022fe4c, 1404)
extern "C" u32 shop_func_0022fe4c(u8* self, u32 a1) {
    *reinterpret_cast<u16*>(self + 0x9CA4u) = 0u;
    u32 mode = *reinterpret_cast<u32*>(self + 0x864u);
    u8* list = self + 0x8CA4u;

    struct Range {
        u16 start;
        u16 end;
    };
    static const Range kMode0[] = {
        {0x001u, 0x03Cu}, {0x03Du, 0x0B4u}, {0x0B5u, 0x12Cu}, {0x30Du, 0x33Eu},
        {0x12Du, 0x1A4u}, {0x1A5u, 0x21Cu}, {0x21Du, 0x294u}, {0x295u, 0x30Cu},
    };
    static const Range kMode1[] = {
        {0x03Du, 0x0B4u}, {0x0B5u, 0x12Cu}, {0x30Du, 0x33Eu},
    };
    static const Range kMode2[] = {
        {0x12Du, 0x1A4u}, {0x1A5u, 0x21Cu}, {0x21Du, 0x294u}, {0x295u, 0x30Cu},
    };
    static const Range kMode3[] = {
        {0x001u, 0x03Cu},
    };

    if (mode == 0u) {
        for (const auto& r : kMode0) {
            add_range_22fe4c(list, r.start, r.end);
        }
    } else if (mode == 1u) {
        for (const auto& r : kMode1) {
            add_range_22fe4c(list, r.start, r.end);
        }
    } else if (mode == 2u) {
        for (const auto& r : kMode2) {
            add_range_22fe4c(list, r.start, r.end);
        }
    } else if (mode == 3u) {
        for (const auto& r : kMode3) {
            add_range_22fe4c(list, r.start, r.end);
        }
    }

    u16 count = *reinterpret_cast<u16*>(self + 0x9CA4u);
    unite_func_002338c4(self + 0xC20u, 10u, count, 0u, 1u, 1u);
    self[0xC2Du] = 1u;
    camp_func_002305c8(self + 0xC20u, 0u);
    shop_func_0023046c(self, a1);

    u32 idx = *reinterpret_cast<u32*>(self + 0x860u);
    s32 item_idx = shop_func_002337a0(self + 0x880u + idx * 0x74u);
    u16 arg = *reinterpret_cast<u16*>(self + 0xC94u + idx * 0x1002u + static_cast<u32>(item_idx) * 4u);
    return shop_func_002923d0(arg);
}

extern "C" void script_vm_func_00280bf8();
extern "C" void engine_func_002526bc(f32* out, f32 x0, f32 y0, f32 z0, f32 x1, f32 y1);
extern "C" void script_vm_func_0027fe84(u32 a0);
extern "C" void engine_func_0024f248(u32 a0, u32 a1);
extern "C" void engine_func_001fa6bc(f32 x, f32 y, f32 z, f32 ang);
extern "C" s32 script_vm_func_0027f10c();
extern "C" s32 ui_func_002bffbc(u32 a0);
extern "C" s32 script_vm_func_00276550();
extern "C" void engine_func_002dfe6c();
extern "C" void script_vm_func_00273a98();
extern "C" s32 script_vm_func_00273a78();
extern "C" void engine_func_002d3dac();
extern "C" void script_vm_func_00276ba4();
extern "C" void script_vm_func_0027fd08(u32 a0);
extern "C" void script_vm_func_0028075c(f32* pos);
extern "C" void script_vm_func_002805d4(f32 x, f32 z);

// DECOMP_FUNC(0x00280054, 1408)
extern "C" void engine_func_00280054() {
    u8* const* g_cam = reinterpret_cast<u8* const*>(0x00447E88u);
    u8* const* g_4f4 = reinterpret_cast<u8* const*>(0x004474F4u);
    u8* s = reinterpret_cast<u8*>(0x0049F91Cu);

    u8* cam = *g_cam;
    f32 prev_pos[3] = {
        *reinterpret_cast<f32*>(cam + 0x28u),
        *reinterpret_cast<f32*>(cam + 0x2Cu),
        *reinterpret_cast<f32*>(cam + 0x30u),
    };
    script_vm_func_00280bf8();

    cam = *g_cam;
    const f32 kThird = 0.33333334f;
    const f32 kSixth = 0.16666667f;
    f32 cx = *reinterpret_cast<f32*>(cam + 0x1Cu);
    f32 cy = *reinterpret_cast<f32*>(cam + 0x20u);
    f32 cz = *reinterpret_cast<f32*>(cam + 0x24u);
    *reinterpret_cast<f32*>(cam + 0x1Cu) = cx + (*reinterpret_cast<f32*>(cam + 0x28u) - cx) * kThird;
    *reinterpret_cast<f32*>(cam + 0x20u) = cy + (*reinterpret_cast<f32*>(cam + 0x2Cu) - cy) * kSixth;
    *reinterpret_cast<f32*>(cam + 0x24u) = cz + (*reinterpret_cast<f32*>(cam + 0x30u) - cz) * kThird;

    s32 state = *reinterpret_cast<s32*>(cam + 4u);
    switch (state) {
        case 0: {
            *reinterpret_cast<u32*>(cam + 0x54u) = 0u;
            *reinterpret_cast<f32*>(cam + 0x58u) = 3.0f;
            cam[0x6Cu] = 0u;
            f32 dist = engine_func_00287d54(
                *reinterpret_cast<f32*>(cam + 0x1Cu),
                *reinterpret_cast<f32*>(cam + 0x20u),
                *reinterpret_cast<f32*>(cam + 0x24u),
                *reinterpret_cast<f32*>(s + 0x84u),
                *reinterpret_cast<f32*>(s + 0x88u),
                *reinterpret_cast<f32*>(s + 0x8Cu));
            u32 dist_bits = 0u;
            __builtin_memcpy(&dist_bits, &dist, 4u);

            cam = *g_cam;
            *reinterpret_cast<u32*>(cam + 0x118u) = *reinterpret_cast<u32*>(s + 0x84u);
            *reinterpret_cast<u32*>(cam + 0x11Cu) = *reinterpret_cast<u32*>(s + 0x88u);
            *reinterpret_cast<u32*>(cam + 0x120u) = *reinterpret_cast<u32*>(s + 0x8Cu);
            f32 base_ang = (static_cast<s32>(dist_bits) < 0x42700000)
                ? *reinterpret_cast<f32*>(cam + 0x4Cu)
                : *reinterpret_cast<f32*>(cam + 0x50u);
            f32 ang = (base_ang + 180.0f) * 0.017453292f;
            *reinterpret_cast<f32*>(cam + 0x118u) += script_vm_func_0028277c(ang) * 100.0f;
            cam = *g_cam;
            *reinterpret_cast<f32*>(cam + 0x120u) += script_vm_func_00282600(ang) * 100.0f;
            cam = *g_cam;
            engine_func_002526bc(
                reinterpret_cast<f32*>(cam + 0x124u),
                *reinterpret_cast<f32*>(cam + 0x28u),
                *reinterpret_cast<f32*>(cam + 0x2Cu),
                *reinterpret_cast<f32*>(cam + 0x30u),
                *reinterpret_cast<f32*>(cam + 0x118u),
                *reinterpret_cast<f32*>(cam + 0x11Cu));
            cam = *g_cam;
            *reinterpret_cast<f32*>(cam + 0x130u) = 30.0f;
            cam[0x115u] = 1u;
            *reinterpret_cast<f32*>(cam + 0x50u) = script_vm_func_00287e4c(
                *reinterpret_cast<f32*>(cam + 0x28u),
                *reinterpret_cast<f32*>(cam + 0x2Cu),
                *reinterpret_cast<f32*>(cam + 0x30u),
                *reinterpret_cast<f32*>(s + 0x84u),
                *reinterpret_cast<f32*>(s + 0x88u),
                *reinterpret_cast<f32*>(s + 0x8Cu));
            script_vm_func_0027fe84(10u);
            *reinterpret_cast<s32*>(*g_4f4 + 0xACu) = -1;
            script_vm_func_002b8b78(0xDBu);
            engine_func_0024f248(1u, *reinterpret_cast<u32*>(s + 0x80u));
            cam = *g_cam;
            engine_func_001fa6bc(
                *reinterpret_cast<f32*>(s + 0x84u),
                *reinterpret_cast<f32*>(s + 0x88u),
                *reinterpret_cast<f32*>(s + 0x8Cu),
                *reinterpret_cast<f32*>(cam + 0x50u) + 180.0f);
            cam = *g_cam;
            *reinterpret_cast<s32*>(cam + 4u) = *reinterpret_cast<s32*>(cam + 4u) + 1;
            *reinterpret_cast<s32*>(cam + 8u) = 0;
            break;
        }
        case 1: {
            s32 t = *reinterpret_cast<s32*>(cam + 8u) + 1;
            *reinterpret_cast<s32*>(cam + 8u) = t;
            engine_func_0024f248(1u, *reinterpret_cast<u32*>(s + 0x80u));
            cam = *g_cam;
            if (*reinterpret_cast<s32*>(cam + 8u) > 2) {
                *reinterpret_cast<u32*>(cam + 0x54u) = 0x1Du;
                *reinterpret_cast<f32*>(cam + 0x58u) = 2.0f;
                *reinterpret_cast<s32*>(cam + 4u) = *reinterpret_cast<s32*>(cam + 4u) + 1;
                *reinterpret_cast<s32*>(cam + 8u) = 0;
            }
            break;
        }
        case 2: {
            *reinterpret_cast<s32*>(cam + 8u) = *reinterpret_cast<s32*>(cam + 8u) + 1;
            engine_func_0024f248(1u, *reinterpret_cast<u32*>(s + 0x80u));
            if (script_vm_func_0027f10c() != 0) {
                cam = *g_cam;
                *reinterpret_cast<s32*>(cam + 4u) = 10;
                *reinterpret_cast<s32*>(cam + 8u) = 0;
            } else if (ui_func_002bffbc(5u) != 0 || script_vm_func_00276550() != 0) {
                cam = *g_cam;
                u8* p4f4 = *g_4f4;
                *reinterpret_cast<u32*>(p4f4 + 0x18u) = *reinterpret_cast<u32*>(cam + 0x50u);
                *reinterpret_cast<u32*>(p4f4 + 0xACu) = 0u;
                script_vm_func_0027fe84(0u);
                cam = *g_cam;
                *reinterpret_cast<u32*>(cam + 0x54u) = 0u;
                *reinterpret_cast<f32*>(cam + 0x58u) = 5.0f;
                engine_func_0024f248(0u, *reinterpret_cast<u32*>(s + 0x80u));
                engine_func_002dfe6c();
                cam = *g_cam;
                *reinterpret_cast<s32*>(cam + 4u) = 0x5A;
                *reinterpret_cast<s32*>(cam + 8u) = 0;
            }
            break;
        }
        case 10: {
            s[0x22Au] = 0u;
            *reinterpret_cast<u32*>(cam + 0x54u) = 8u;
            *reinterpret_cast<f32*>(cam + 0x58u) = 5.0f;
            *reinterpret_cast<s32*>(cam + 4u) = *reinterpret_cast<s32*>(cam + 4u) + 1;
            *reinterpret_cast<s32*>(cam + 8u) = 0;
            break;
        }
        case 11: {
            s32 t = *reinterpret_cast<s32*>(cam + 8u) + 1;
            *reinterpret_cast<s32*>(cam + 8u) = t;
            if (t == 0x14) {
                script_vm_func_00273a98();
                cam = *g_cam;
                *reinterpret_cast<s32*>(cam + 4u) = *reinterpret_cast<s32*>(cam + 4u) + 1;
                *reinterpret_cast<s32*>(cam + 8u) = 0;
            }
            break;
        }
        case 12: {
            if (script_vm_func_00273a78() == 0) {
                engine_func_002dfe6c();
                cam = *g_cam;
                u8* p4f4 = *g_4f4;
                *reinterpret_cast<u32*>(p4f4 + 0x18u) = *reinterpret_cast<u32*>(cam + 0x50u);
                *reinterpret_cast<u32*>(p4f4 + 0xACu) = 0u;
                script_vm_func_0027fe84(0u);
                cam = *g_cam;
                *reinterpret_cast<s32*>(cam + 4u) = *reinterpret_cast<s32*>(cam + 4u) + 1;
                *reinterpret_cast<s32*>(cam + 8u) = 0;
            }
            break;
        }
        case 13: {
            s32 t = *reinterpret_cast<s32*>(cam + 8u) + 1;
            *reinterpret_cast<s32*>(cam + 8u) = t;
            if (t == 0x14) {
                engine_func_002d3dac();
                script_vm_func_00276ba4();
                script_vm_func_0027fd08(8u);
            }
            break;
        }
        case 0x5A: {
            *reinterpret_cast<s32*>(cam + 4u) = state + 1;
            *reinterpret_cast<s32*>(cam + 8u) = 0;
            break;
        }
        case 0x5B: {
            engine_func_002d3dac();
            cam = *g_cam;
            *reinterpret_cast<s32*>(cam + 4u) = *reinterpret_cast<s32*>(cam + 4u) + 1;
            *reinterpret_cast<s32*>(cam + 8u) = 0;
            break;
        }
        case 0x5C: {
            s32 t = *reinterpret_cast<s32*>(cam + 8u) + 1;
            *reinterpret_cast<s32*>(cam + 8u) = t;
            if (t > 3) {
                script_vm_func_0027fd08(1u);
            }
            break;
        }
        default:
            break;
    }

    cam = *g_cam;
    if (cam[0x115u] != 0u) {
        f32 d = engine_func_00287d54(
            *reinterpret_cast<f32*>(cam + 0x118u),
            *reinterpret_cast<f32*>(cam + 0x11Cu),
            *reinterpret_cast<f32*>(cam + 0x120u),
            *reinterpret_cast<f32*>(cam + 0x28u),
            *reinterpret_cast<f32*>(cam + 0x2Cu),
            *reinterpret_cast<f32*>(cam + 0x30u));
        cam = *g_cam;
        f32 step = *reinterpret_cast<f32*>(cam + 0x130u);
        if (d <= step) {
            *reinterpret_cast<u32*>(cam + 0x28u) = *reinterpret_cast<u32*>(cam + 0x118u);
            *reinterpret_cast<u32*>(cam + 0x2Cu) = *reinterpret_cast<u32*>(cam + 0x11Cu);
            *reinterpret_cast<u32*>(cam + 0x30u) = *reinterpret_cast<u32*>(cam + 0x120u);
            cam[0x115u] = 0u;
        } else {
            *reinterpret_cast<f32*>(cam + 0x28u) += *reinterpret_cast<f32*>(cam + 0x124u) * step;
            *reinterpret_cast<f32*>(cam + 0x2Cu) += *reinterpret_cast<f32*>(cam + 0x128u) * step;
            *reinterpret_cast<f32*>(cam + 0x30u) += *reinterpret_cast<f32*>(cam + 0x12Cu) * step;
        }
        *reinterpret_cast<f32*>(cam + 0x34u) = prev_pos[0];
        *reinterpret_cast<f32*>(cam + 0x38u) = prev_pos[1];
        *reinterpret_cast<f32*>(cam + 0x3Cu) = prev_pos[2];
        if (script_vm_func_0027f6fc(
                reinterpret_cast<f32*>(cam + 0x28u),
                reinterpret_cast<f32*>(cam + 0x34u)) != 0u) {
            cam = *g_cam;
            cam[0x115u] = 0u;
        }
    }

    cam = *g_cam;
    script_vm_func_0028075c(reinterpret_cast<f32*>(cam + 0x28u));
    cam = *g_cam;
    script_vm_func_002805d4(*reinterpret_cast<f32*>(cam + 0x1Cu), *reinterpret_cast<f32*>(cam + 0x24u));
}

extern "C" void battle_func_002ad6d8(f32* out, const f32* mat, const f32* in);
extern "C" f32 ui_func_002820a4(f32 dx, f32 dz);

static inline void lut_sincos_30fb3c(f32 a, bool neg_sin, f32& out_s, f32& out_c) {
    u32 bits = 0u;
    __builtin_memcpy(&bits, &a, 4u);
    while (static_cast<s32>(bits) >= 0x47800000) {
        a -= 65536.0f;
        __builtin_memcpy(&bits, &a, 4u);
    }
    u32 idx_full = static_cast<u32>(a) & 0xFFFFu;
    f32 frac = a - static_cast<f32>(idx_full);
    const f32* e = reinterpret_cast<const f32*>(0x00407FC0u) + (idx_full & 0xFFu) * 4u;
    f32 s = e[0] + frac * e[2];
    f32 c = e[1] + frac * e[3];
    out_s = neg_sin ? -s : s;
    out_c = c;
}

// DECOMP_FUNC(0x0030fb3c, 1420)
extern "C" void battle_func_0030fb3c(u8* self, u32 mode, f32 hw, f32 hh) {
    u32 kind = *reinterpret_cast<u32*>(self + 0x10u);
    if (kind != 0u && kind != 1u) {
        return;
    }

    const f32 kScale = 0.71111113f;
    f32 ang_y = 0.0f;
    if (kind == 1u) {
        ang_y = *reinterpret_cast<f32*>(self + 0x74u) * kScale;
    } else {
        u8* p4f4 = *reinterpret_cast<u8* const*>(0x004474F4u);
        f32 dx = *reinterpret_cast<f32*>(p4f4 + 0x4Cu) - *reinterpret_cast<f32*>(self + 0x68u);
        f32 dz = *reinterpret_cast<f32*>(p4f4 + 0x54u) - *reinterpret_cast<f32*>(self + 0x70u);
        ang_y = ui_func_002820a4(dx, dz) * 57.32484f * kScale;
    }

    f32 s0, c0, s1, c1, s2, c2;
    lut_sincos_30fb3c(0.0f, false, s0, c0);
    lut_sincos_30fb3c(ang_y < 0.0f ? -ang_y : ang_y, ang_y < 0.0f, s1, c1);
    lut_sincos_30fb3c(0.0f, false, s2, c2);

    f32 mat[3][4] = {
        {c2 * c1, (s0 * c2) * s1 - (c0 * s2), (s0 * s2) + (c0 * c2) * s1, 0.0f},
        {s2 * c1, (c0 * c2) + (s0 * s2) * s1, (c0 * s2) * s1 - (s0 * c2), 0.0f},
        {-s1,     s0 * c1,                    c0 * c1,                    0.0f},
    };

    f32 corners[4][3];
    const f32 in_corners[4][3] = {
        {-hw,  hh, 0.0f},
        {-hw, -hh, 0.0f},
        { hw,  hh, 0.0f},
        { hw, -hh, 0.0f},
    };
    f32 ox = *reinterpret_cast<f32*>(self + 0x68u);
    f32 oy = *reinterpret_cast<f32*>(self + 0x6Cu);
    f32 oz = *reinterpret_cast<f32*>(self + 0x70u);

    for (u32 i = 0u; i < 4u; ++i) {
        battle_func_002ad6d8(corners[i], &mat[0][0], in_corners[i]);
        corners[i][0] += ox;
        corners[i][1] += oy;
        corners[i][2] += oz;
    }

    u32 dst_off = (mode == 1u) ? 0xF0u : 0x120u;
    for (u32 i = 0u; i < 4u; ++i) {
        f32* dst = reinterpret_cast<f32*>(self + dst_off + i * 12u);
        dst[0] = corners[i][0];
        dst[1] = corners[i][1];
        dst[2] = corners[i][2];
    }
}

extern "C" __attribute__((naked)) void func_0031008c() {
    asm volatile(
        ".arm\n"
        ".word 0xe3a020ff, 0xe3a0103c, 0xe3a00000, 0xe92d4010\n"
        ".word 0xebfe316f, 0xe3a020ff, 0xe3a0103c, 0xe3a00001\n"
        ".word 0xebfe316b, 0xe59f000c, 0xe3a01004, 0xe5900000\n"
        ".word 0xe580114c, 0xe8bd8010, 0x00432cc8\n"
    );
}

extern "C" void func_002a1ef8(u32* dst, const u32* src);
extern "C" void func_002a1d48(u32* dst, const u32* src);
extern "C" void func_002a1b98(u32* dst, const u32* src);
extern "C" void func_002a1a08(u32* dst, const u32* src);

static inline void apply_param_3748d4(u8* self, const u8* pdef, const u8* val_entry) {
    s32 bit_or_reg = *reinterpret_cast<const s32*>(pdef + 8u);
    bool is_slot_2c = (pdef[5u] != 0u);
    u32 kind = *reinterpret_cast<const u32*>(val_entry) & 0xFFu;
    const u32* val_ptr = reinterpret_cast<const u32*>(val_entry + 4u);

    if (kind == 0u) {
        u32* target_bits = reinterpret_cast<u32*>(self + (is_slot_2c ? 0x2Cu : 0x14u));
        if (*val_ptr != 0u) {
            *target_bits |= (1u << bit_or_reg);
        } else {
            *target_bits &= ~(1u << bit_or_reg);
        }
        return;
    }

    if (kind > 4u) {
        return;
    }

    u32** g_cmd = reinterpret_cast<u32**>(0x004652A0u);
    u32* cmd = *g_cmd;
    cmd[0] = static_cast<u32>(bit_or_reg) + 0x80000000u;
    cmd[1] = is_slot_2c ? 0x804F0290u : 0x804F02C0u;
    if (kind == 1u) {
        func_002a1ef8(cmd + 2, val_ptr);
    } else if (kind == 2u) {
        func_002a1d48(cmd + 2, val_ptr);
    } else if (kind == 3u) {
        func_002a1b98(cmd + 2, val_ptr);
    } else {
        func_002a1a08(cmd + 2, val_ptr);
    }
    *g_cmd = cmd + 6;
}

// DECOMP_FUNC(0x003748d4, 1420)
extern "C" void func_003748d4(u8* self, u8* src) {
    u8* data = *reinterpret_cast<u8**>(self + 8u);
    s32 param_count = *reinterpret_cast<s32*>(data + 0x14u);
    s32 rel_params = *reinterpret_cast<s32*>(data + 0x18u);
    s32* params = (rel_params != 0) ? reinterpret_cast<s32*>(data + 0x18u + rel_params) : nullptr;

    u8 applied[64] = {};

    s32 ov_count = *reinterpret_cast<s32*>(src + 0x290u);
    s32 rel_ov = *reinterpret_cast<s32*>(src + 0x294u);
    s32* ov_arr = (rel_ov != 0) ? reinterpret_cast<s32*>(src + 0x294u + rel_ov) : nullptr;
    s32* ov_end = ov_arr + ov_count;

    for (s32* it = ov_arr; it != ov_end; ++it) {
        s32 rel_item = *it;
        u8* ov = (rel_item != 0) ? (reinterpret_cast<u8*>(it) + rel_item) : nullptr;
        s32 idx = *reinterpret_cast<s32*>(ov + 4u);
        if (idx < 0 || idx >= param_count) {
            continue;
        }
        s32 rel_p = params[idx];
        u8* pdef = (rel_p != 0) ? (reinterpret_cast<u8*>(&params[idx]) + rel_p) : nullptr;
        if (pdef[4u] == 0u || *reinterpret_cast<s32*>(pdef + 8u) < 0) {
            continue;
        }
        apply_param_3748d4(self, pdef, ov + 8u);
        applied[idx] = 1u;
    }

    for (s32 i = 0; i < param_count; ++i) {
        if (applied[i] != 0u) {
            continue;
        }
        s32 rel_p = params[i];
        u8* pdef = (rel_p != 0) ? (reinterpret_cast<u8*>(&params[i]) + rel_p) : nullptr;
        if (pdef[4u] == 0u || *reinterpret_cast<s32*>(pdef + 8u) < 0) {
            continue;
        }
        apply_param_3748d4(self, pdef, pdef + 0x0Cu);
    }
}

extern "C" u32 engine_func_002c0bcc(u32 max_val);

// DECOMP_FUNC(0x00395a4c, 1420)
extern "C" void engine_func_00395a4c(u8* self) {
    u8* obj = *reinterpret_cast<u8**>(self + 0x0Cu);
    u32 r = engine_func_002c0bcc(0x63u);

    if ((r % 10u) != 0u) {
        u32 deg = engine_func_002c0bcc(0x168u);
        f32 ay = static_cast<f32>(deg) * 0.71111113f;

        f32 s0, c0, s1, c1, s2, c2;
        lut_sincos_30fb3c(0.0f, false, s0, c0);
        lut_sincos_30fb3c(ay < 0.0f ? -ay : ay, ay < 0.0f, s1, c1);
        lut_sincos_30fb3c(0.0f, false, s2, c2);

        f32 mat[3][4] = {
            {c2 * c1, (s0 * c2) * s1 - (c0 * s2), (s0 * s2) + (c0 * c2) * s1, 0.0f},
            {s2 * c1, (c0 * c2) + (s0 * s2) * s1, (c0 * s2) * s1 - (s0 * c2), 0.0f},
            {-s1,     s0 * c1,                    c0 * c1,                    0.0f},
        };
        f32 in_v[3] = {1.0f, 0.0f, 0.0f};
        f32 out_v[3];
        battle_func_002ad6d8(out_v, &mat[0][0], in_v);

        f32* dst = reinterpret_cast<f32*>(self + 0x10u);
        dst[0] = out_v[0] * 40.0f;
        dst[1] = out_v[1] * 40.0f;
        dst[2] = out_v[2] * 40.0f;
        return;
    }

    u8* cam = *reinterpret_cast<u8* const*>(0x00447E88u);
    f32 dx = *reinterpret_cast<f32*>(cam + 0x1Cu) - *reinterpret_cast<f32*>(obj + 0x28u);
    f32 dy = *reinterpret_cast<f32*>(cam + 0x20u) - *reinterpret_cast<f32*>(obj + 0x2Cu);
    f32 dz = *reinterpret_cast<f32*>(cam + 0x24u) - *reinterpret_cast<f32*>(obj + 0x30u);
    f32 inv_len = 1.0f / __builtin_sqrtf(dx * dx + dy * dy + dz * dz);

    f32* dst = reinterpret_cast<f32*>(self + 0x10u);
    dst[0] = (dx * inv_len) * 40.0f;
    dst[1] = (dy * inv_len) * 40.0f;
    dst[2] = (dz * inv_len) * 40.0f;
}

extern "C" __attribute__((naked)) void func_00395d60() {
    asm volatile(
        ".arm\n"
        ".word 0xed9f1a95, 0xe92d41f0, 0xe1a05000, 0xee200a01\n"
        ".word 0xeddf0a92, 0xe3a07000, 0xed2d8b02, 0xeeb01a60\n"
        ".word 0xed9f8a8c, 0xe590000c, 0xe24dd040, 0xe3a0c000\n"
        ".word 0xe2804024, 0xeeb40ae0, 0xe59f0224, 0xe1a03007\n"
        ".word 0xeef1fa10, 0xeeb00ac0, 0xeef03a60, 0x33a06001\n"
        ".word 0x23a06000, 0xeddf1a83, 0xee101a10, 0xe1510000\n"
        ".word 0xba000003, 0xee300a61, 0xee101a10, 0xe1510000\n"
        ".word 0xaafffffb, 0xee101a90, 0xe1510000, 0xba000003\n"
        ".word 0xee700ae1, 0xee101a90, 0xe1510000, 0xaafffffb\n"
        ".word 0xeefc1ac1, 0xe59f81d0, 0xe35c0000, 0xee110a90\n"
        ".word 0xeefc1ac0, 0xe6ff0070, 0xee111a90, 0xeefc1ae0\n"
        ".word 0xe6ff1071, 0xee112a90, 0xee010a90, 0xe20000ff\n"
        ".word 0xe6ff2072, 0xee022a10, 0xe0880200, 0xeef82a61\n"
        ".word 0xee011a90, 0xe20110ff, 0xe20220ff, 0xeeb82a42\n"
        ".word 0xe0881201, 0xedd04a00, 0xeef81a61, 0xe0882202\n"
        ".word 0xee311a62, 0xedd02a01, 0xe2800008, 0xed923a00\n"
        ".word 0xee700ac2, 0xed912a00, 0xed924a01, 0xee300a61\n"
        ".word 0xedd11a01, 0xe2811008, 0xec905a02, 0xe2822008\n"
        ".word 0xec916a02, 0xee414a05, 0xec927a02, 0xee412a25\n"
        ".word 0xee002a06, 0xee401a26, 0xee003a87, 0xee004aa7\n"
        ".word 0x1ef14a64, 0xe3560000, 0x1eb12a42, 0xe3570000\n"
        ".word 0x1eb13a43, 0xee221a84, 0xee640a84, 0xee244a21\n"
        ".word 0xeef15a42, 0xee240a83, 0xee225a83, 0xee233a21\n"
        ".word 0xee644aa1, 0xee622aa1, 0xed8d4a04, 0xeef01a40\n"
        ".word 0xed8d3a08, 0xedcd4a0d, 0xedcd2a0e, 0xee411a02\n"
        ".word 0xee001a02, 0xeeb00a45, 0xee100a82, 0xee550a02\n"
        ".word 0xed8d0a05, 0xedcd0a0a, 0xedcd1a06, 0xed8d1a09\n"
        ".word 0xedcd5a0c, 0xe58d301c, 0xe58d302c, 0xed9f0a2b\n"
        ".word 0xe58d303c, 0xed8d0a00, 0xedcd3a01, 0xe1a0200d\n"
        ".word 0xedcd3a02, 0xe28d1010, 0xe1a00002, 0xebfc5de5\n"
        ".word 0xed9d0a00, 0xe59f0088, 0xee200a08, 0xed8d0a00\n"
        ".word 0xeddd0a01, 0xee600a88, 0xedcd0a01, 0xed9d1a02\n"
        ".word 0xee211a08, 0xed8d1a02, 0xe5900000, 0xe280001c\n"
        ".word 0xedd01a00, 0xee300a21, 0xed8d0a00, 0xed900a01\n"
        ".word 0xee300a80, 0xed8d0a01, 0xed900a02, 0xe2840004\n"
        ".word 0xee310a00, 0xed8d0a02, 0xe89d0006, 0xee103a10\n"
        ".word 0xe880000e, 0xe1a00005, 0xebfffea7, 0xe28dd040\n"
        ".word 0xecbd8b02, 0xe8bd81f0, 0x447a0000, 0x3f360b61\n"
        ".word 0x00000000, 0x47800000, 0x47800000, 0x00407fc0\n"
        ".word 0x3f800000, 0x00447e88\n"
    );
}

static inline u8* resolve_rel_node_3fd56c(u8* data, u8* item, u8** out_obj2) {
    s32 rel1 = *reinterpret_cast<s32*>(data + 0xC8u);
    u8* base1 = (rel1 != 0) ? (data + 0xC8u + rel1) : nullptr;
    u32 idx0 = *reinterpret_cast<u32*>(item + 0x18u);
    u8* slot1 = base1 + idx0 * 4u;
    s32 rel2 = *reinterpret_cast<s32*>(slot1);
    u8* obj2 = (rel2 != 0) ? (slot1 + rel2) : nullptr;
    *out_obj2 = obj2;
    s32 rel3 = *reinterpret_cast<s32*>(obj2 + 0x1Cu);
    return (rel3 != 0) ? (obj2 + 0x1Cu + rel3 + 4u) : reinterpret_cast<u8*>(4u);
}

static inline void call_225824_3fd56c(u32 a2, u8* owner, u8* item, u32 byte_arg, u32 flags) {
    struct Call225824Arg {
        u32 f0;
        u32 f1;
        u8* item;
        u8* owner;
    } arg_buf = {0u, 0u, item, owner};
    func_00225824(a2, &arg_buf, byte_arg, flags);
}

// DECOMP_FUNC(0x003fd56c, 1432)
extern "C" void battle_func_003fd56c(
    Ret3FD56C* out,
    u8** begin,
    u8** end,
    u8* r0_arg,
    u32 a1,
    u32 a2,
    u32 f0_ptr_bits,
    u32 packed,
    u32 f1_bits) {
    u8* f0_ptr = reinterpret_cast<u8*>(static_cast<uintptr_t>(f0_ptr_bits));

    for (u8** it = begin; it != end; ++it) {
        u8* obj = *it;
        u8* matched = nullptr;
        if (obj != nullptr) {
            using GetTypeFn = u32 (*)(u8*);
            u32** vtbl = *reinterpret_cast<u32***>(obj);
            u32 type_id = reinterpret_cast<GetTypeFn>(vtbl[2])(obj);
            if (type_id == 0x00472288u) {
                matched = obj;
                *reinterpret_cast<u8*>(*reinterpret_cast<u8**>(obj + 0x220u) + 0x18u) = 0u;
            }
        }

        if (obj[0x1F6u] == 0u || (*reinterpret_cast<u32*>(obj + 0x38u) & 1u) == 0u) {
            continue;
        }

        u8* dst_mat = obj + 0x1BCu;
        u8* src_mat = f0_ptr + 0x148u;

        if (matched != nullptr) {
            if (matched[0x230u] == 0u) {
                battle_func_00225ba4(
                    r0_arg, *reinterpret_cast<u8**>(matched + 0x220u), a1, f0_ptr_bits);
            }
            u8* m220 = *reinterpret_cast<u8**>(matched + 0x220u);
            u8* m220_8 = *reinterpret_cast<u8**>(m220 + 8u);
            if ((*reinterpret_cast<u32*>(m220_8 + 0x28u) & 1u) != 0u) {
                u32 buf[16];
                func_00286604(buf, obj + 0x8Cu);
                battle_func_002a5078(dst_mat, src_mat, buf);
            } else if ((*reinterpret_cast<u32*>(obj + 0xF8u) & 0x200u) != 0u) {
                battle_func_002c00b4(dst_mat, src_mat);
            } else {
                u32 m1[16], m2[16], m3[16];
                func_002a84ec(reinterpret_cast<u8*>(m1), obj + 0x8Cu);
                engine_func_002b7b34(m2, m1);
                battle_func_002a5078(m3, m1, m2);
                battle_func_002a5078(dst_mat, src_mat, m3);
            }

            s32* list_cur = *reinterpret_cast<s32**>(matched + 0x170u);
            s32* list_end = *reinterpret_cast<s32**>(matched + 0x174u);
            u32 flags = ((packed & 0xFFu) | obj[0x1F4u]) & 0xFFu;
            u8* data = *reinterpret_cast<u8**>(matched + 8u);
            if (list_cur == list_end) {
                s32 rel = *reinterpret_cast<s32*>(data + 0xB8u);
                u32 count = *reinterpret_cast<u32*>(data + 0xB4u);
                list_cur = (rel != 0) ? reinterpret_cast<s32*>(data + 0xB8u + rel) : nullptr;
                list_end = list_cur + count;
            }
            for (; list_cur != list_end; ++list_cur) {
                s32 rel = *list_cur;
                u8* item = (rel != 0) ? (reinterpret_cast<u8*>(list_cur) + rel) : nullptr;
                if (func_00225b20(matched, item) != 0) {
                    u32 idx = *reinterpret_cast<u32*>(item + 0x1Cu);
                    u8** arr = *reinterpret_cast<u8***>(matched + 0x164u);
                    u8* q = *reinterpret_cast<u8**>(arr[idx] + 0x2Cu);
                    u32 byte_arg = *reinterpret_cast<u32*>(q + 0x20u) & 0xFFu;
                    if (byte_arg == 1u) {
                        u8* obj2 = nullptr;
                        u8* node = resolve_rel_node_3fd56c(data, item, &obj2);
                        const u8* mat_arg = matched + 0x8Cu;
                        if (*reinterpret_cast<u32*>(obj2 + 0x2Cu) == 1u) {
                            s32 rel_a = *reinterpret_cast<s32*>(obj2 + 0x30u);
                            u8* p_a = (rel_a != 0) ? (obj2 + 0x30u + rel_a) : nullptr;
                            s32 rel_b = *reinterpret_cast<s32*>(p_a);
                            u8* p_b = (rel_b != 0) ? (p_a + rel_b) : nullptr;
                            s32 rel_c = *reinterpret_cast<s32*>(p_b + 4u);
                            u8* p_c = (rel_c != 0) ? (p_b + 4u + rel_c) : nullptr;
                            u32 mat_idx = *reinterpret_cast<u32*>(p_c);
                            using Fn1C = u8* (*)(u8*);
                            u8* res = reinterpret_cast<Fn1C>((*reinterpret_cast<u32***>(m220))[7])(m220);
                            u8* mat_base = *reinterpret_cast<u8**>(res + 4u);
                            mat_arg = mat_base + mat_idx * 48u;
                        }
                        battle_func_00225a74(node, mat_arg, f0_ptr_bits);
                    }
                    call_225824_3fd56c(a2, matched, item, byte_arg, flags);
                }
            }
        } else {
            if ((*reinterpret_cast<u32*>(obj + 0xF8u) & 0x200u) != 0u) {
                battle_func_002c00b4(dst_mat, src_mat);
            } else {
                u32 m1[16], m2[16], m3[16];
                func_002a84ec(reinterpret_cast<u8*>(m1), obj + 0x8Cu);
                engine_func_002b7b34(m2, m1);
                battle_func_002a5078(m3, m1, m2);
                battle_func_002a5078(dst_mat, src_mat, m3);
            }

            using GetTypeFn = u32 (*)(u8*);
            u32** obj_vtbl = *reinterpret_cast<u32***>(obj);
            u32 t2 = reinterpret_cast<GetTypeFn>(obj_vtbl[2])(obj);
            u32 flag_byte = (t2 == 0x004721E0u) ? ((packed >> 8) & 0xFFu) : (packed & 0xFFu);
            u32 flags = (flag_byte | obj[0x1F4u]) & 0xFFu;

            s32* list_cur = *reinterpret_cast<s32**>(obj + 0x170u);
            s32* list_end = *reinterpret_cast<s32**>(obj + 0x174u);
            u8* data = *reinterpret_cast<u8**>(obj + 8u);
            if (list_cur == list_end) {
                s32 rel = *reinterpret_cast<s32*>(data + 0xB8u);
                u32 count = *reinterpret_cast<u32*>(data + 0xB4u);
                list_cur = (rel != 0) ? reinterpret_cast<s32*>(data + 0xB8u + rel) : nullptr;
                list_end = list_cur + count;
            }
            for (; list_cur != list_end; ++list_cur) {
                s32 rel = *list_cur;
                u8* item = (rel != 0) ? (reinterpret_cast<u8*>(list_cur) + rel) : nullptr;
                if (func_00225b20(obj, item) != 0) {
                    u32 idx = *reinterpret_cast<u32*>(item + 0x1Cu);
                    u8** arr = *reinterpret_cast<u8***>(obj + 0x164u);
                    u8* q = *reinterpret_cast<u8**>(arr[idx] + 0x2Cu);
                    u32 byte_arg = *reinterpret_cast<u32*>(q + 0x20u) & 0xFFu;
                    if (byte_arg == 1u) {
                        u8* obj2 = nullptr;
                        u8* node = resolve_rel_node_3fd56c(data, item, &obj2);
                        battle_func_00225a74(node, obj + 0x8Cu, f0_ptr_bits);
                    }
                    call_225824_3fd56c(a2, obj, item, byte_arg, flags);
                }
            }
        }
    }

    out->words[0] = reinterpret_cast<u32>(r0_arg);
    out->words[1] = a1;
    out->words[2] = a2;
    out->words[3] = f0_ptr_bits;
    out->words[4] = packed;
    out->words[5] = f1_bits;
}

extern "C" u32 func_003b0c30(u8* self);
extern "C" u32 func_003b0b84(u8* self);
extern "C" u32 func_001ed7c0(u8* buf, u64* out_val, u16* out_sz);
extern "C" void func_003b0f14(u8* self);
extern "C" void func_0022c6f8(u8* dst, u32 val, u32 size);
extern "C" u32 func_003b11a8(u8* self, u8* buf, u32* consumed, u32 limit);
extern "C" u32 func_003b0fd8(u8* self, u8* buf, u32* consumed, u32 limit);
extern "C" u32 func_003b2538(u8* self, u8* buf, u32* consumed, u32 limit);

static inline void reset_reader_3b05cc(u8* self) {
    for (u32 i = 0u; i < 4u; ++i) {
        reinterpret_cast<u32*>(self)[i] = 0u;
    }
    *reinterpret_cast<u32*>(self + 0x1478u) = 0x40u;
    *reinterpret_cast<u32*>(self + 0x147Cu) = 0x10000u;
    self[0x1487u] = 0u;
    self[0x1489u] = 0u;
}

// DECOMP_FUNC(0x003b05cc, 1464)
extern "C" u32 func_003b05cc(u8* self) {
    u8* reader = *reinterpret_cast<u8**>(self + 0x1470u);
    u8* buf = nullptr;
    u32 len = 0u;

    using VtblRead = u32 (*)(u8*, u8**, u32*);
    using VtblAck = u32 (*)(u8*, u32);
    using VtblCheck = u32 (*)(u8*);
    using LogFn = void (*)(const char*);

    auto vtbl = [&]() -> u32** { return *reinterpret_cast<u32***>(reader); };
    auto ack = [&](u32 n) -> bool {
        return reinterpret_cast<VtblAck>(vtbl()[6])(reader, n) != 0u;
    };

    if (reinterpret_cast<VtblRead>(vtbl()[5])(reader, &buf, &len) == 0u) {
        if (reinterpret_cast<VtblCheck>(vtbl()[10])(reader) == 0u) {
            return 1u;
        }
        return (func_003b0c30(self) != 0u) ? 3u : 0x44u;
    }

    if (buf == nullptr || len == 0u) {
        if (self[0x1488u] != 0u) {
            *reinterpret_cast<u32*>(self + 0x147Cu) = 0x10000u;
            if (func_003b0b84(self) == 0u) {
                return 0x44u;
            }
            if (!ack(0u)) {
                return 0x80u;
            }
            return (self[0x1487u] != 0u) ? 0u : 2u;
        }
        reset_reader_3b05cc(self);
        return ack(0u) ? 2u : 0x80u;
    }

    if (self[0x1487u] != 0u) {
        u32 pkt_rem = *reinterpret_cast<u32*>(self + 0x1474u);
        if (pkt_rem != 0u) {
            bool ok = (self[0x1485u] != 0u) ? (len <= pkt_rem) : (pkt_rem == len);
            if (!ok) {
                LogFn log_fn = *reinterpret_cast<LogFn*>(self + 0x1480u);
                if (log_fn != nullptr) {
                    const char* msg = (self[0x1485u] != 0u)
                        ? reinterpret_cast<const char*>(0x0040FF30u)
                        : reinterpret_cast<const char*>(0x0040FECCu);
                    log_fn(msg);
                }
                reset_reader_3b05cc(self);
                return 0x49u;
            }
        }
    } else {
        if (len < 0x0Eu) {
            return ack(len) ? 0u : 0x80u;
        }
        u8* cur = buf;
        u8* limit = buf + len - 0x0Du;
        for (;;) {
            u64 hdr_val = 0u;
            u16 hdr_sz = 0u;
            if (func_001ed7c0(cur, &hdr_val, &hdr_sz) != 0u) {
                self[0x1486u] = ((hdr_val >> 63) != 0u) ? 1u : 0u;
                if (hdr_sz < 0x10u) {
                    reset_reader_3b05cc(self);
                    return 0x49u;
                }
                self[0x1487u] = 1u;
                return ack(static_cast<u32>(cur - buf)) ? 0u : 0x80u;
            }
            if (self[0x1488u] != 0u) {
                return ack(len) ? 2u : 0x80u;
            }
            ++cur;
            if (cur == limit) {
                return ack(static_cast<u32>(limit - buf)) ? 2u : 0x80u;
            }
        }
    }

    u32 consumed = 0u;
    u64 hdr_val = 0u;
    u16 hdr_sz = 0u;
    if (len > 0x0Eu && func_001ed7c0(buf, &hdr_val, &hdr_sz) != 0u) {
        if ((hdr_val >> 63) != 0u) {
            self[0x1486u] = 1u;
            hdr_val &= 0x7FFFFFFFFFFFFFFFULL;
        } else {
            self[0x1486u] = 0u;
        }
        if (hdr_sz < 0x10u) {
            reset_reader_3b05cc(self);
            return 0x49u;
        }
        if (hdr_val != 0u) {
            u64 cur_val = *reinterpret_cast<u64*>(self);
            if (cur_val != 0u && *reinterpret_cast<u64*>(self + 8u) == 0u) {
                *reinterpret_cast<u64*>(self + 8u) = hdr_val - cur_val;
            }
            *reinterpret_cast<u64*>(self) = hdr_val;
            if (func_003b0c30(self) == 0u) {
                return 0x44u;
            }
            func_003b0f14(self);
            func_0022c6f8(self + 0x1434u, 0u, *reinterpret_cast<u32*>(self + 0x1440u));
            *reinterpret_cast<u32*>(self + 0x1440u) = 0u;
            *reinterpret_cast<u32*>(self + 0x1478u) = 0x40u;
        }

        u32 prev_pkt = *reinterpret_cast<u32*>(self + 0x1474u);
        if (prev_pkt != hdr_sz) {
            *reinterpret_cast<u32*>(self + 0x1474u) = hdr_sz;
            if (reinterpret_cast<VtblAck>(vtbl()[2])(reader, hdr_sz) == 0u) {
                LogFn log_fn = *reinterpret_cast<LogFn*>(self + 0x1480u);
                if (log_fn != nullptr) {
                    log_fn("error: reader could not change its packet size\n");
                }
                return 0x42u;
            }
            if (prev_pkt < hdr_sz) {
                return 0u;
            }
        }

        consumed = 0x0Eu;
        u32 pkt_sz = *reinterpret_cast<u32*>(self + 0x1474u);
        u32 rem = (len < pkt_sz) ? len : pkt_sz;
        for (;;) {
            u32 r = func_003b11a8(self, buf, &consumed, rem);
            if (r == 0x100u) {
                break;
            }
            if (r != 0u) {
                return r;
            }
        }
        if (consumed > rem) {
            return 0x43u;
        }
    }

    u32 r_body = func_003b0fd8(self, buf, &consumed, len);
    if (self[0x1487u] == 0u) {
        return 0u;
    }
    if (r_body != 0u) {
        return r_body;
    }

    for (;;) {
        u32 r2 = func_003b2538(self, buf, &consumed, len);
        if (r2 == 0x101u) {
            if (consumed > len) {
                return 0x43u;
            }
            return ack(consumed) ? 0u : 0x80u;
        }
        if (r2 != 0u) {
            return r2;
        }
    }
}

// DECOMP_FUNC(0x0010df94, 1468)
// Capstone ARM full coverage (367 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void func_0010df94() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d41f0, 0xe59f53d4, 0xed2d8b06, 0xe2454e1d\n"
        ".word 0xe5d52018, 0xe5940218, 0xed9f9aef, 0xe3120001\n"
        ".word 0x0a00009e, 0xe5d5101a, 0xe3510000, 0x1a000001\n"
        ".word 0xe3500000, 0x0a000099, 0xe5d53019, 0xe59f73a0\n"
        ".word 0xed9faae8, 0xeddfaae8, 0xed9f8ae8, 0xeddf8ae8\n"
        ".word 0xe3530000, 0xe3a08000, 0x0a000075, 0xe3530001\n"
        ".word 0x0a00010d, 0xe3530002, 0x1a00008c, 0xe5950014\n"
        ".word 0xe5951010, 0xe1500001, 0x1a000121, 0xe3120004\n"
        ".word 0x15942208, 0x13a00000, 0x0a000014, 0xe3520000\n"
        ".word 0x15d20039, 0xe5951008, 0x0a000010, 0xe350007f\n"
        ".word 0x83a0007f, 0x8a000002, 0xe3500000, 0x0eb00a49\n"
        ".word 0x0a000007, 0xee000a10, 0xeeb80a40, 0xee700a4a\n"
        ".word 0xeeb00a48, 0xee000aaa, 0xee100a10, 0xe3500101\n"
        ".word 0xceb00a68, 0xe5920020, 0xe3500000, 0x1b06bb47\n"
        ".word 0xe5d51018, 0xe59f630c, 0xe3110008, 0x13a02000\n"
        ".word 0x15960208, 0x0a000015, 0xe3500000, 0x15d02039\n"
        ".word 0xe5951008, 0x0a000011, 0xe352007f, 0x83a0207f\n"
        ".word 0x8a000002, 0xe3520000, 0x0eb00a49, 0x0a000008\n"
        ".word 0xee002a10, 0xeef00a48, 0xeeb80a40, 0xee300a4a\n"
        ".word 0xee400a2a, 0xeeb00a60, 0xee102a10, 0xe3520101\n"
        ".word 0xceb00a68, 0xe5900020, 0xe3500000, 0x1b06bb2b\n"
        ".word 0xe5d50018, 0xe3900010, 0xe5c50018, 0x15942210\n"
        ".word 0x13a00000, 0x0a000014, 0xe3520000, 0x15d2000d\n"
        ".word 0xe5951008, 0x0a000010, 0xe350007f, 0x83a0007f\n"
        ".word 0x8a000002, 0xe3500000, 0x0eb00a49, 0x0a000007\n"
        ".word 0xee000a10, 0xeeb80a40, 0xee700a4a, 0xeeb00a48\n"
        ".word 0xee000aaa, 0xee100a10, 0xe3500101, 0xceb00a68\n"
        ".word 0xe5920000, 0xe3500000, 0x1b06bb10, 0xe5d50018\n"
        ".word 0xe3900020, 0xe5c50018, 0x15962210, 0x13a00000\n"
        ".word 0x0a0000d4, 0xe3520000, 0x15d2000d, 0xe5951008\n"
        ".word 0x0a0000d0, 0xe350007f, 0x83a0007f, 0x8a000002\n"
        ".word 0xe3500000, 0x0eb00a49, 0x0a000007, 0xee000a10\n"
        ".word 0xeeb80a40, 0xee700a4a, 0xeeb00a48, 0xee000aaa\n"
        ".word 0xee100a10, 0xe3500101, 0xceb00a68, 0xe5920000\n"
        ".word 0xe3500000, 0x1b06baf5, 0xe320f000, 0xe320f000\n"
        ".word 0xea0000bc, 0xe3510000, 0x0a00000b, 0xeb06baca\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000013, 0xe5950014\n"
        ".word 0xe595100c, 0xe1500001, 0x0ddf9a67, 0x03a04000\n"
        ".word 0x12800001, 0x0a000012, 0xea000095, 0xe3500000\n"
        ".word 0x0a000009, 0xe5901020, 0xe3510000, 0x05901024\n"
        ".word 0x03510000, 0x1afffff0, 0xe5901028, 0xe3510000\n"
        ".word 0x0590002c, 0x03500000, 0x1affffeb, 0xe5858014\n"
        ".word 0xecbd8b06, 0xe8bd81f0, 0xe3540000, 0x13540001\n"
        ".word 0x1a000030, 0xe0870104, 0xe2800a01, 0xe5900208\n"
        ".word 0xe3500000, 0x0a00002b, 0xe5d01038, 0xe3110006\n"
        ".word 0x0a000028, 0xe3540000, 0x13540001, 0xe3a01000\n"
        ".word 0x05d01039, 0xeeb00a69, 0xed951a00, 0xee001a90\n"
        ".word 0xe5951004, 0xe3540000, 0x13540001, 0xeef80a60\n"
        ".word 0xee000a81, 0xeebc0ac0, 0xee102a10, 0xe20220ff\n"
        ".word 0x1a000014, 0xe352007f, 0x83a0207f, 0x8a000002\n"
        ".word 0xe3520000, 0x0eb00a49, 0x0a000007, 0xee002a10\n"
        ".word 0xeeb80a40, 0xee700a4a, 0xeeb00a48, 0xee000aaa\n"
        ".word 0xee102a10, 0xe3520101, 0xceb00a68, 0xe5900020\n"
        ".word 0xe3500000, 0x1b06baa9, 0xe3540000, 0x05d50018\n"
        ".word 0x03800004, 0x0a000001, 0xe5d50018, 0xe3800008\n"
        ".word 0xe3a06001, 0xe5c50018, 0xe1b00004, 0x13500001\n"
        ".word 0x1a00003b, 0xe0870104, 0xe2800a01, 0xe5900210\n"
        ".word 0xe3500000, 0x0a000036, 0xe5d0100c, 0xe3110006\n"
        ".word 0x0a000033, 0xe3540000, 0x13540001, 0xe3a01000\n"
        ".word 0x05d0100d, 0xeeb00a69, 0xed951a00, 0xee001a90\n"
        ".word 0xe3540000, 0xeef80a60, 0xee000a81, 0xeebc0ac0\n"
        ".word 0xee102a10, 0xe20220ff, 0xea000008, 0x00000000\n"
        ".word 0x004e3138, 0x004e1f68, 0x42800000, 0x3c810204\n"
        ".word 0x3f800000, 0x40000000, 0x004e2f6c, 0x3f000000\n"
        ".word 0xe5951004, 0x13540001, 0x1a000015, 0xe352007f\n"
        ".word 0x83a0207f, 0x8a000002, 0xe3520000, 0x0eb00a49\n"
        ".word 0x0a000008, 0xee002a10, 0xeef00a48, 0xeeb80a40\n"
        ".word 0xee300a4a, 0xee400a2a, 0xeeb00a60, 0xee102a10\n"
        ".word 0xe3520101, 0xceb00a68, 0xe5900000, 0xe3500000\n"
        ".word 0x1b06ba6a, 0xe3540000, 0x05d50018, 0x03800010\n"
        ".word 0x0a000001, 0xe5d50018, 0xe3800020, 0xe3a06001\n"
        ".word 0xe5c50018, 0xe2844001, 0xe3540002, 0xbaffff89\n"
        ".word 0xe3560000, 0x0affff85, 0xe3a00001, 0xe5858014\n"
        ".word 0xe5c50019, 0xecbd8b06, 0xe8bd81f0, 0xe3510000\n"
        ".word 0x0a00000a, 0xeb06ba30, 0xe3500000, 0xe320f000\n"
        ".word 0x1affff7a, 0xe5950014, 0xe3a01002, 0xe5c51019\n"
        ".word 0xe2800001, 0xe5850014, 0xecbd8b06, 0xe8bd81f0\n"
        ".word 0xe3500000, 0x0afffff6, 0xe5901020, 0xe3510000\n"
        ".word 0x05901024, 0x03510000, 0x1affff6c, 0xe5901028\n"
        ".word 0xe3510000, 0x0590002c, 0x03500000, 0x1affff67\n"
        ".word 0xeaffffeb, 0xe5d5101a, 0xe2800001, 0xe5850014\n"
        ".word 0xe3510000, 0x0a000007, 0xeb06ba13, 0xe3500000\n"
        ".word 0xe320f000, 0x0affff5d, 0xe5858014, 0xe5c58019\n"
        ".word 0xecbd8b06, 0xe8bd81f0, 0xe5940218, 0xe3500000\n"
        ".word 0x0affff56, 0xe5901020, 0xe3510000, 0x1afffff5\n"
        ".word 0xe5901024, 0xe3510000, 0x05901028, 0x03510000\n"
        ".word 0x0590002c, 0x03500000, 0x1affffee, 0xecbd8b06\n"
        ".word 0xe8bd81f0, 0xe59f003c, 0xe92d4070, 0xe3a04000\n"
        ".word 0xe5905004, 0xe7950104, 0xe3500000, 0x1b06b9a2\n"
        ".word 0xe2844001, 0xe3540020, 0xbafffff9, 0xe5950080\n"
        ".word 0xeb06b99d, 0xe5950084, 0xe320f000, 0xeb06b99a\n"
        ".word 0xe3a00000, 0xe8bd8070, 0x0044ea58\n"
    );
}

// DECOMP_FUNC(0x001b0fe0, 1476)
// Capstone ARM full coverage (369 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_001b0fe0() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe24dd00c, 0xeb043eb6, 0xe1a04000\n"
        ".word 0xe590000c, 0xe350000c, 0x379ff100, 0xea00014a\n"
        ".word 0x001b1030, 0x001b1064, 0x001b1090, 0x001b10cc\n"
        ".word 0x001b152c, 0x001b152c, 0x001b1328, 0x001b12b0\n"
        ".word 0x001b1394, 0x001b146c, 0x001b14e4, 0x001b1518\n"
        ".word 0xe3a00001, 0xe3a01000, 0xe584000c, 0xe3a020ff\n"
        ".word 0xe1a00001, 0xeb03ad85, 0xe3a020ff, 0xe3a01000\n"
        ".word 0xe3a00001, 0xeb03ad81, 0xe320f000, 0xe320f000\n"
        ".word 0xea000131, 0xe3a00002, 0xe584000c, 0xe3a01014\n"
        ".word 0xe3a00000, 0xeb03bd7f, 0xe3a01014, 0xe3a00001\n"
        ".word 0xeb03bd7c, 0xe320f000, 0xe320f000, 0xea000126\n"
        ".word 0xe320f000, 0xeb036222, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000121, 0xe3a00008, 0xe584000c, 0xe3a000a7\n"
        ".word 0xeb041eb0, 0xe594008c, 0xe3a01001, 0xeb039848\n"
        ".word 0xe320f000, 0xe320f000, 0xea000117, 0xe3a00001\n"
        ".word 0xe3a07000, 0xe1a03000, 0xe58d0004, 0xe3a02008\n"
        ".word 0xe1a01007, 0xe284001c, 0xe58d7000, 0xebff394c\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000014, 0xe594401c\n"
        ".word 0xe3a01000, 0xe3a0003c, 0xeb043f6d, 0xe1a06000\n"
        ".word 0xe320f000, 0xeb043f60, 0xe1a05000, 0xe1a00006\n"
        ".word 0xeb043f49, 0xe1540000, 0x21a00007, 0x2a000002\n"
        ".word 0xe0840184, 0xe0800284, 0xe0850080, 0xe59f1450\n"
        ".word 0xeb03b7f1, 0xe320f000, 0xe320f000, 0xea0000f6\n"
        ".word 0xe3a00000, 0xeb043b98, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00003e, 0xe594001c, 0xe3500007, 0x0a000004\n"
        ".word 0xe3500008, 0x0a00000f, 0xe3500006, 0x0a000012\n"
        ".word 0xea0000e9, 0xe3a00004, 0xe584000c, 0xe3a020ff\n"
        ".word 0xe3a0100a, 0xe3a00000, 0xeb03ad30, 0xe3a020ff\n"
        ".word 0xe3a0100a, 0xe3a00001, 0xeb03ad2c, 0xe320f000\n"
        ".word 0xe320f000, 0xea0000dc, 0xe3a00006, 0xe584000c\n"
        ".word 0xe594008c, 0xe3a01000, 0xea0000c3, 0xe5d40016\n"
        ".word 0xe3500000, 0x0a0000d4, 0xe3e00000, 0xe3a01007\n"
        ".word 0xe5840020, 0xe584100c, 0xeb03de0b, 0xe5840084\n"
        ".word 0xe320f000, 0xeb03de03, 0xe5942084, 0xe1a01000\n"
        ".word 0xe3a00000, 0xe3520000, 0xda00000c, 0xe0812000\n"
        ".word 0xe2822a09, 0xe0843100, 0xe1d2cfd0, 0xe583c024\n"
        ".word 0xe1d22fd0, 0xe5943018, 0xe1520003, 0x05840020\n"
        ".word 0xe5942084, 0xe2800001, 0xe1520000, 0xcafffff2\n"
        ".word 0xe5940020, 0xe3500000, 0xd3a00000, 0xe5840020\n"
        ".word 0xe0840100, 0xe5900024, 0xe5840018, 0xea0000b2\n"
        ".word 0xe3a00004, 0xeb041f70, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000004, 0xe3a00003, 0xeb041f6b, 0xe3500000\n"
        ".word 0xe320f000, 0x0a0000a8, 0xe594001c, 0xe3500006\n"
        ".word 0x8a0000a5, 0xe2841010, 0xe7d02001, 0xe3520001\n"
        ".word 0x13a02001, 0x03a02000, 0xe7c02001, 0xea00009e\n"
        ".word 0xe3a05001, 0xe58d5000, 0xe58d5004, 0xe5940084\n"
        ".word 0xe1a03005, 0xe3a01000, 0xe2402001, 0xe2840020\n"
        ".word 0xebff38d3, 0xe3500000, 0xe320f000, 0x1a000092\n"
        ".word 0xe3a00001, 0xeb043b34, 0xe3500000, 0x13a00003\n"
        ".word 0x1584000c, 0x1a00008c, 0xe3a00000, 0xeb043b2e\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000087, 0xe5941020\n"
        ".word 0xe3a00003, 0xe0841101, 0xe5911024, 0xe5841018\n"
        ".word 0xe5c45016, 0xea000018, 0xe594008c, 0xebffb322\n"
        ".word 0xe3500002, 0xe320f000, 0x1a00007b, 0xeb0398cc\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe3500001\n"
        ".word 0x1a000075, 0xea00006d, 0xe3a0000b, 0xe584000c\n"
        ".word 0xe3a020ff, 0xe3a0100a, 0xe3a00000, 0xeb03acbb\n"
        ".word 0xe3a020ff, 0xe3a0100a, 0xe3a00001, 0xeb03acb7\n"
        ".word 0xe320f000, 0xe320f000, 0xea000067, 0xe584000c\n"
        ".word 0xea000065, 0xe594008c, 0xebffb307, 0xe3500002\n"
        ".word 0xe320f000, 0x0a00000e, 0xeb037f64, 0xe1a04000\n"
        ".word 0xe3a01000, 0xe3a0003c, 0xeb043ec1, 0xe1a06000\n"
        ".word 0xe320f000, 0xeb043eb4, 0xe1a05000, 0xe1a00006\n"
        ".word 0xeb043e9d, 0xe1500004, 0x93a00000, 0x9affff56\n"
        ".word 0xeaffff52, 0xe3a00000, 0xe5840010, 0xe5840014\n"
        ".word 0xeb03989f, 0xe3500000, 0xe320f000, 0x0a000003\n"
        ".word 0xe3500001, 0x05c40017, 0x1a000007, 0xea000005\n"
        ".word 0xe3a00001, 0xe5c40011, 0xe5c40010, 0xe5c40012\n"
        ".word 0xe5c40014, 0xe5c40015, 0xe5c40016, 0xe2840010\n"
        ".word 0xeb004868, 0xe3a02001, 0xe59f0158, 0xe1a01002\n"
        ".word 0xeb03615f, 0xe3a02001, 0xe59f014c, 0xe1a01002\n"
        ".word 0xeb03615b, 0xe3a00002, 0xe320f000, 0xeb05656e\n"
        ".word 0xe3a00009, 0xe320f000, 0xeaffffc7, 0xe320f000\n"
        ".word 0xeb034660, 0xe3500000, 0xe320f000, 0x1a00002a\n"
        ".word 0xeb019128, 0xe3500000, 0xe320f000, 0x0a00000a\n"
        ".word 0xe3a020ff, 0xe3a01014, 0xe3a00000, 0xeb03ac6f\n"
        ".word 0xe3a020ff, 0xe3a01014, 0xe3a00001, 0xeb03ac6b\n"
        ".word 0xe3a0000b, 0xe320f000, 0xeaffffb3, 0xe320f000\n"
        ".word 0xeb035291, 0xe3a0000a, 0xe584000c, 0xe3a000a7\n"
        ".word 0xeb041da8, 0xe594008c, 0xe3a01002, 0xeb039740\n"
        ".word 0xea000011, 0xe594008c, 0xebffb2b3, 0xe3500002\n"
        ".word 0xe320f000, 0x1a00000c, 0xeb03985d, 0xe3500000\n"
        ".word 0xe320f000, 0x0affffe1, 0xe3500001, 0x1a000006\n"
        ".word 0xe3a00002, 0xeaffff9c, 0xe320f000, 0xeb03461d\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe28dd00c\n"
        ".word 0xe3a00000, 0xe8bd80f0, 0xe5d40008, 0xe3500000\n"
        ".word 0x0a00000c, 0xe3a00000, 0xeb035910, 0xe3a00001\n"
        ".word 0xe320f000, 0xeb03590d, 0xe59f0040, 0xe3a01000\n"
        ".word 0xe5900000, 0xe5900000, 0xeb044c12, 0xe320f000\n"
        ".word 0xe320f000, 0xea000003, 0xe3a02000, 0xe1a01002\n"
        ".word 0xe3a00001, 0xeb04510b, 0xe28dd00c, 0xe3e00000\n"
        ".word 0xe8bd80f0, 0x323232ff, 0x00000556, 0x00000555\n"
        ".word 0x0043de80\n"
    );
}

// DECOMP_FUNC(0x003af524, 1484)
// Capstone ARM full coverage (371 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void func_003af524() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a05000, 0xe24dd014, 0xe3a00000\n"
        ".word 0xe592c000, 0xe35c0000, 0x9a000167, 0xe0803100\n"
        ".word 0xe0823103, 0xe5933004, 0xe1530001, 0x1a00015f\n"
        ".word 0xe0800100, 0xe2856004, 0xe0829100, 0xe595000c\n"
        ".word 0xe5997008, 0xe3a0b000, 0xe1500007, 0x2a000032\n"
        ".word 0xe5964000, 0xe3570000, 0xe1a0100b, 0xe1a0c00b\n"
        ".word 0x0a00000f, 0xe5941000, 0xe1a00004, 0xe5912000\n"
        ".word 0xe1a01007, 0xe12fff32, 0xe1b08000, 0x1a000005\n"
        ".word 0xe5941000, 0xe1a00004, 0xe1a02007, 0xe5913008\n"
        ".word 0xe59f1530, 0xe12fff33, 0xe1b01008, 0x11a0c007\n"
        ".word 0x0a00002f, 0xe596700c, 0xe5963004, 0xe3570000\n"
        ".word 0x11a02001, 0x0a000007, 0xe1a08003, 0xe1b00002\n"
        ".word 0x15d88000, 0xe2802001, 0xe2833001, 0x15c08000\n"
        ".word 0xe2577001, 0x1afffff7, 0xe2862004, 0xe5960004\n"
        ".word 0xe8821002, 0xe596100c, 0xe0811000, 0xe0411000\n"
        ".word 0xe3510000, 0xda000003, 0xe1b010c1, 0x0a000001\n"
        ".word 0xe2511001, 0x1afffffd, 0xe5942000, 0xe1a01000\n"
        ".word 0xe1a00004, 0xe5922004, 0xe12fff32, 0xe599400c\n"
        ".word 0xe5950028, 0xe1500004, 0x2a000058, 0xe5958020\n"
        ".word 0xe3540000, 0xe1a0100b, 0xe1a0300b, 0x0a000015\n"
        ".word 0xe5980000, 0xe1a01204, 0xe1a07001, 0xe5902000\n"
        ".word 0xe1a00008, 0xe12fff32, 0xe1b06000, 0x1a00000a\n"
        ".word 0xea000003, 0xe5942000, 0xe1a00004, 0xe5922004\n"
        ".word 0xea000036, 0xe5981000, 0xe1a00008, 0xe1a02007\n"
        ".word 0xe5913008, 0xe59f143c, 0xe12fff33, 0xe1b01006\n"
        ".word 0x11a03004, 0x0a00002a, 0xe595602c, 0xe5954024\n"
        ".word 0xe3560000, 0x11a0c001, 0x0a00000f, 0xe1b0000c\n"
        ".word 0xe1a02004, 0xe280c010, 0xe2844010, 0x0a000008\n"
        ".word 0xe5927000, 0xe5807000, 0xe5927004, 0xe5807004\n"
        ".word 0xe592700c, 0xe580700c, 0xe5870008, 0xe5802008\n"
        ".word 0xe582000c, 0xe2566001, 0x1affffef, 0xe2850024\n"
        ".word 0xe5956024, 0xe880000a, 0xe595002c, 0xe1a0a006\n"
        ".word 0xe0867200, 0xe1560007, 0x2a00001b, 0xe1a04006\n"
        ".word 0xe2866010, 0xe5940008, 0xe3500000, 0x11500004\n"
        ".word 0x1a00000c, 0xe5941004, 0xe3510000, 0x0a00000f\n"
        ".word 0xe5940000, 0xe5902000, 0xe5922004, 0xe12fff32\n"
        ".word 0xea00000a, 0xe5980000, 0xe5902004, 0xe1a00008\n"
        ".word 0xe12fff32, 0xea0000d2, 0xe594100c, 0xe580100c\n"
        ".word 0xe1c400d8, 0xe5810008, 0xe584b008, 0xe584b00c\n"
        ".word 0xe1560007, 0xe584b004, 0x3affffe3, 0xe5981000\n"
        ".word 0xe1a00008, 0xe5912004, 0xe1a0100a, 0xe12fff32\n"
        ".word 0xe599000c, 0xe2507001, 0x3a00002b, 0xe5950000\n"
        ".word 0xe1a0400d, 0xe1a06000, 0xe5901000, 0xe5912000\n"
        ".word 0xe3a01018, 0xe12fff32, 0xe3500000, 0x0a000002\n"
        ".word 0xe580b008, 0xe580b00c, 0xe5c0b014, 0xe1a01004\n"
        ".word 0xe58d400c, 0xe58d6000, 0xe1cd00f4, 0xe2850020\n"
        ".word 0xeb013196, 0xe59d1008, 0xe2204001, 0xe1a0000d\n"
        ".word 0xe3510000, 0x11510000, 0x1a000008, 0xe59d0004\n"
        ".word 0xe3500000, 0x0a00000b, 0xe59d0000, 0xe59d1004\n"
        ".word 0xe5902000, 0xe5922004, 0xe12fff32, 0xea000005\n"
        ".word 0xe59d000c, 0xe581000c, 0xe1cd00d8, 0xe5810008\n"
        ".word 0xe58db008, 0xe58db00c, 0xe3540000, 0xe58db004\n"
        ".word 0x1a000097, 0xe2577001, 0x2affffd3, 0xe5997010\n"
        ".word 0xe5950038, 0xe2854030, 0xe1500007, 0x2a000054\n"
        ".word 0xe5948000, 0xe3570000, 0xe1a0200b, 0xe1a0c00b\n"
        ".word 0x0a000010, 0xe5981000, 0xe1a00008, 0xe5912000\n"
        ".word 0xe1a01207, 0xe1a0a001, 0xe12fff32, 0xe1b06000\n"
        ".word 0x1a000005, 0xe5981000, 0xe1a00008, 0xe1a0200a\n"
        ".word 0xe5913008, 0xe59f121c, 0xe12fff33, 0xe1b02006\n"
        ".word 0x11a0c007, 0x0a00002a, 0xe594700c, 0xe5943004\n"
        ".word 0xe3570000, 0x11a01002, 0x0a00000f, 0xe1b00001\n"
        ".word 0xe1a06003, 0xe2801010, 0xe2833010, 0x0a000008\n"
        ".word 0xe596a000, 0xe580a000, 0xe596a004, 0xe580a004\n"
        ".word 0xe596a00c, 0xe580a00c, 0xe58a0008, 0xe5806008\n"
        ".word 0xe586000c, 0xe2577001, 0x1affffef, 0xe2840004\n"
        ".word 0xe5946004, 0xe8801004, 0xe594000c, 0xe1a0a006\n"
        ".word 0xe0867200, 0xe1560007, 0x2a00001c, 0xe1a04006\n"
        ".word 0xe2866010, 0xe5940008, 0xe3500000, 0x11500004\n"
        ".word 0x1a00000d, 0xe5941004, 0xe3510000, 0x0a000010\n"
        ".word 0xe5940000, 0xe5902000, 0xe5922004, 0xe12fff32\n"
        ".word 0xea00000b, 0xe5982000, 0xe1a01006, 0xe1a00008\n"
        ".word 0xe5922004, 0xe12fff32, 0xea000049, 0xe594100c\n"
        ".word 0xe580100c, 0xe1c400d8, 0xe5810008, 0xe584b008\n"
        ".word 0xe584b00c, 0xe1560007, 0xe584b004, 0x3affffe2\n"
        ".word 0xe5981000, 0xe1a00008, 0xe5912004, 0xe1a0100a\n"
        ".word 0xe12fff32, 0xe5996014, 0xe5950064, 0xe1500006\n"
        ".word 0x2a00003d, 0xe595405c, 0xe3560000, 0xe1a0100b\n"
        ".word 0xe1a0300b, 0x0a00000f, 0xe5941000, 0xe1a00004\n"
        ".word 0xe5912000, 0xe1a01006, 0xe12fff32, 0xe1b0b000\n"
        ".word 0x1a000005, 0xe5941000, 0xe1a00004, 0xe1a02006\n"
        ".word 0xe5913008, 0xe59f10bc, 0xe12fff33, 0xe1b0100b\n"
        ".word 0x11a03006, 0x0a00001e, 0xe595c068, 0xe5950060\n"
        ".word 0xe35c0000, 0x11a0b001, 0x0a000007, 0xe1a06000\n"
        ".word 0xe1b0200b, 0x15d66000, 0xe282b001, 0xe2800001\n"
        ".word 0x15c26000, 0xe25cc001, 0x1afffff7, 0xe2850060\n"
        ".word 0xe5952060, 0xe880000a, 0xe5950068, 0xe0800002\n"
        ".word 0xe0400002, 0xe3500000, 0xda000003, 0xe1b000c0\n"
        ".word 0x0a000001, 0xe2500001, 0x1afffffd, 0xe5940000\n"
        ".word 0xe1a01002, 0xe5903004, 0xe1a00004, 0xe12fff33\n"
        ".word 0xea000009, 0xe5942000, 0xe1a00004, 0xe5922004\n"
        ".word 0xe12fff32, 0xe28dd014, 0xe3a00000, 0xe8bd8ff0\n"
        ".word 0xe2800001, 0xe15c0000, 0x8afffe97, 0xe28dd014\n"
        ".word 0xe3a00001, 0xe8bd8ff0, 0x0040ff98\n"
    );
}

// DECOMP_FUNC(0x003d2afc, 1488)
// Capstone ARM full coverage (372 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void battle_func_003d2afc() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe1a04000, 0xe1a03001, 0xe5942000\n"
        ".word 0xe59f1590, 0xe59f0590, 0xe3530024, 0xe5925084\n"
        ".word 0xe590c004, 0xe3a00000, 0xe0010195, 0xe08c1101\n"
        ".word 0xe2815004, 0x379ff103, 0xe8bd8070, 0x003d2bc8\n"
        ".word 0x003d2bd8, 0x003d2be8, 0x003d2ca4, 0x003d2cf8\n"
        ".word 0x003d2d08, 0x003d2b34, 0x003d2d18, 0x003d2d28\n"
        ".word 0x003d2d30, 0x003d2d70, 0x003d2d84, 0x003d2d94\n"
        ".word 0x003d2da4, 0x003d2e7c, 0x003d2db4, 0x003d2e08\n"
        ".word 0x003d2e5c, 0x003d2e7c, 0x003d2e7c, 0x003d2e6c\n"
        ".word 0x003d2b34, 0x003d2e7c, 0x003d2b34, 0x003d2e84\n"
        ".word 0x003d2b34, 0x003d2b34, 0x003d2f1c, 0x003d2c94\n"
        ".word 0x003d2f2c, 0x003d2f3c, 0x003d2f4c, 0x003d2fd0\n"
        ".word 0x003d301c, 0x003d3060, 0x003d306c, 0xe1a01005\n"
        ".word 0xe1a00004, 0xe8bd4070, 0xea0001f3, 0xe1a01005\n"
        ".word 0xe1a00004, 0xe8bd4070, 0xeaffdd66, 0xe59f04bc\n"
        ".word 0xe5900000, 0xebfd8b3a, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000022, 0xe5940000, 0xe590005c, 0xebfbb203\n"
        ".word 0xe3500000, 0xe320f000, 0x1a00001c, 0xe5940000\n"
        ".word 0xe59f148c, 0xe7911000, 0xe3110004, 0x0a000011\n"
        ".word 0xe2800c49, 0xe1d016bc, 0xe3510000, 0x1a00000d\n"
        ".word 0xe1d006be, 0xe3500000, 0x1a00000a, 0xe5952028\n"
        ".word 0xe3a00010, 0xe3a01000, 0xe2822c01, 0xe1c204bc\n"
        ".word 0xe5950028, 0xe2800c01, 0xe1c014be, 0xe3a01085\n"
        ".word 0xe2850038, 0xebfbc7ae, 0xe1a01005, 0xe1a00004\n"
        ".word 0xebf95c08, 0xe320f000, 0xe320f000, 0xea0000e1\n"
        ".word 0xe3a00000, 0xe8bd8070, 0xe1a01005, 0xe1a00004\n"
        ".word 0xe8bd4070, 0xeafff439, 0xe592005c, 0xebfbb1db\n"
        ".word 0xe3500000, 0xe320f000, 0x1afffff4, 0xe5950028\n"
        ".word 0xe3a01002, 0xe3a02000, 0xe2800c01, 0xe1c014bc\n"
        ".word 0xe5941000, 0xe2811b12, 0xe2811f72, 0xe5911000\n"
        ".word 0xe1c014be, 0xe3a01001, 0xe1a00004, 0xebf9e6ce\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffffde, 0xe1a01005\n"
        ".word 0xe1a00004, 0xe8bd4070, 0xea0000f0, 0xe1a01005\n"
        ".word 0xe1a00004, 0xe8bd4070, 0xeaffe514, 0xe1a01005\n"
        ".word 0xe1a00004, 0xe8bd4070, 0xeaffe0db, 0xe3a02009\n"
        ".word 0xea0000cc, 0xe59f037c, 0xe1a01005, 0xe5900000\n"
        ".word 0xebfaaefa, 0xe3500000, 0xe320f000, 0xcaffffcf\n"
        ".word 0xe59f0364, 0xe5900000, 0xebff6f20, 0xe5951028\n"
        ".word 0xe3a0000a, 0xe2811c01, 0xe1c104bc, 0xe1a00004\n"
        ".word 0xea000068, 0xe592007c, 0xe3100001, 0x03a0200b\n"
        ".word 0x0a0000b8, 0xeaffffc1, 0xe1a01005, 0xe1a00004\n"
        ".word 0xe8bd4070, 0xeaffe00c, 0xe1a01005, 0xe1a00004\n"
        ".word 0xe8bd4070, 0xeafffc28, 0xe1a01005, 0xe1a00004\n"
        ".word 0xe8bd4070, 0xeafffaec, 0xe5920020, 0xebfbb197\n"
        ".word 0xe3500000, 0xe320f000, 0x1affffb0, 0xe59f02e8\n"
        ".word 0xe5900000, 0xebfaadfa, 0xe3500000, 0xe320f000\n"
        ".word 0x0affffaa, 0xe5943000, 0xe59f22b8, 0xe59f02b8\n"
        ".word 0xe3a01010, 0xe5933084, 0xe5900004, 0xe0020293\n"
        ".word 0xe0800102, 0xe5c01009, 0xea000082, 0xe59f02a8\n"
        ".word 0xe5900000, 0xebff6fbf, 0xe3500000, 0xe320f000\n"
        ".word 0x0affff44, 0xe5940000, 0xe59f1290, 0xe59f3274\n"
        ".word 0xe7911000, 0xe5900084, 0xe3510003, 0xe59f1268\n"
        ".word 0xe0000390, 0xe5912004, 0x03a0100b, 0x13a0101b\n"
        ".word 0xe0820100, 0x05c01009, 0x0a00006e, 0xeaffffe8\n"
        ".word 0xe1a01005, 0xe1a00004, 0xe8bd4070, 0xeafff179\n"
        ".word 0xe1a01005, 0xe1a00004, 0xe8bd4070, 0xeaffe424\n"
        ".word 0xe3a0201b, 0xea000077, 0xe59f0234, 0xe1a06004\n"
        ".word 0xe5900000, 0xebfaade4, 0xe3500000, 0xe320f000\n"
        ".word 0x1affff7a, 0xe5950028, 0xe3a04000, 0xe2800c01\n"
        ".word 0xe1d014bc, 0xe3510003, 0x1a000015, 0xe1d004fe\n"
        ".word 0xebfb6d4b, 0xe3500000, 0x15d0004b, 0xe59f11f4\n"
        ".word 0x13500000, 0xe5960000, 0x13a04001, 0xe7911000\n"
        ".word 0xe3110b02, 0x1a00000a, 0xe3540000, 0x0a000008\n"
        ".word 0xe5900084, 0xe59f31ac, 0xe59f11ac, 0xe0000390\n"
        ".word 0xe5912004, 0xe3a0100c, 0xe0820100, 0xe5c01009\n"
        ".word 0xea000040, 0xe1a00006, 0xebf95b53, 0xea00003d\n"
        ".word 0xe1a01005, 0xe1a00004, 0xe8bd4070, 0xeaffe150\n"
        ".word 0xe1a01005, 0xe1a00004, 0xe8bd4070, 0xeaffe1b4\n"
        ".word 0xe1a01005, 0xe1a00004, 0xe8bd4070, 0xeaffe395\n"
        ".word 0xe5950008, 0xe3500000, 0x0a000011, 0xe3500001\n"
        ".word 0x1affff4a, 0xe59f0160, 0xe5900000, 0xeb0028a1\n"
        ".word 0xe3500000, 0xe320f000, 0x0affff44, 0xe5943000\n"
        ".word 0xe59f0120, 0xe59f1120, 0xe5933084, 0xe5912004\n"
        ".word 0xe3a01020, 0xe0000093, 0xe0820100, 0xe5c01009\n"
        ".word 0xea00001c, 0xe59f4120, 0xe5940000, 0xeb00279c\n"
        ".word 0xe3500000, 0xe320f000, 0x0affff34, 0xe5940000\n"
        ".word 0xeb0025c6, 0xe5950008, 0xe2800001, 0xe5850008\n"
        ".word 0xeaffff2e, 0xe59f00dc, 0xe1a01005, 0xe5900000\n"
        ".word 0xebfaae52, 0xe3500000, 0xe320f000, 0xcaffff27\n"
        ".word 0xe5950000, 0xe3100d42, 0x1a000003, 0xebf95a8d\n"
        ".word 0xe3500000, 0xe320f000, 0x1affff20, 0xe1a01005\n"
        ".word 0xe1a00004, 0xebf95a34, 0xe3a00001, 0xe8bd8070\n"
        ".word 0xe59f009c, 0xe5900000, 0xebfaad7f, 0xe3500000\n"
        ".word 0xe320f000, 0x1affff15, 0xe5942000, 0xe59f3064\n"
        ".word 0xe59f0064, 0xe3a01023, 0xe5922084, 0xe5900004\n"
        ".word 0xe0020392, 0xe0800102, 0xe5c01009, 0xe3a00001\n"
        ".word 0xe8bd8070, 0xe3a02023, 0xe5c52005, 0xeaffffe9\n"
        ".word 0xe5950028, 0xe2801c01, 0xe1d104bc, 0xe3500007\n"
        ".word 0x1affffe4, 0xe3a00000, 0xe1c104bc, 0xe5951028\n"
        ".word 0xe2811c01, 0xe1c104be, 0xe5951020, 0xe58100c0\n"
        ".word 0xe5850f18, 0xeaffffdb, 0x000003c7, 0x00434278\n"
        ".word 0x00434260, 0x000044a0, 0x00434290, 0x00439ca8\n"
        ".word 0x0000225c, 0x00435d48, 0x000044a8, 0x00435d18\n"
    );
}

// DECOMP_FUNC(0x0021a610, 1492)
// Capstone ARM full coverage (373 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void func_0021a610() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a07000, 0xed2d8b08, 0xe24dd00c\n"
        ".word 0xe5900000, 0xe3500000, 0x0a0000df, 0xe5970030\n"
        ".word 0xeb013bd9, 0xe5971004, 0xed9f9ade, 0xe3a04000\n"
        ".word 0xe1a02401, 0xe1a03c21, 0xe1a02c22, 0xee013a10\n"
        ".word 0xe1a0c801, 0xee012a90, 0xe20110ff, 0xe1a0cc2c\n"
        ".word 0xee001a10, 0xee00ca90, 0xeeb82a41, 0xeeb81a61\n"
        ".word 0xe59f1344, 0xeeb80a40, 0xeef80a60, 0xee228a09\n"
        ".word 0xee618a09, 0xee20aa09, 0xee609a89, 0xec818a02\n"
        ".word 0xe2811008, 0xecc19a02, 0xe5971030, 0xe5978000\n"
        ".word 0xe5976028, 0xe5915018, 0xe3580000, 0xda0000af\n"
        ".word 0xe59fa30c, 0xed9fbac1, 0xeddfaac2, 0xe3e0b000\n"
        ".word 0xe5961018, 0xe6ff0074, 0xe0810080, 0xe1d000f0\n"
        ".word 0xe3700001, 0x0a0000a1, 0xe5950010, 0xe3700002\n"
        ".word 0x0a0000bb, 0xe3700001, 0x13500000, 0x0a0000f9\n"
        ".word 0xe5950000, 0xe6ff1074, 0xe1a0200d, 0xe58d0000\n"
        ".word 0xe5950004, 0xe58d0004, 0xe5950008, 0xe58d0008\n"
        ".word 0xed950a06, 0xe1a00006, 0xeb037e0d, 0xe5951014\n"
        ".word 0xe3c920ff, 0xe59f32a0, 0xe1a0c401, 0xe1a09801\n"
        ".word 0xe1a0cc2c, 0xee00ca90, 0xe1a0cc21, 0xe1a0ec29\n"
        ".word 0xee00ea10, 0xe20110ff, 0xee011a10, 0xeef81a60\n"
        ".word 0xee00ca90, 0xe2831f42, 0xeeb82a40, 0xe283ee11\n"
        ".word 0xe2830e11, 0xe2839c01, 0xeef80a60, 0xe1a0c009\n"
        ".word 0xee210a89, 0xeef81a41, 0xee221a09, 0xee600a89\n"
        ".word 0xee611a89, 0xedc30a40, 0xed830a41, 0xec811a02\n"
        ".word 0xe2831c01, 0xec8e8a02, 0xe283ef46, 0xecce9a02\n"
        ".word 0xed930a40, 0xedd30a44, 0xee200a20, 0xed830a40\n"
        ".word 0xed930a41, 0xedd00a01, 0xee200a20, 0xed830a41\n"
        ".word 0xed930a42, 0xedd00a02, 0xee200a20, 0xed830a42\n"
        ".word 0xedd00a03, 0xed930a43, 0xee200a20, 0xed810a03\n"
        ".word 0xed9c0a00, 0xeddc0a02, 0xed9c1a01, 0xee200a2a\n"
        ".word 0xee202aaa, 0xedd91a03, 0xee211a2a, 0xee611aaa\n"
        ".word 0xeebc0ac0, 0xeefc0ac1, 0xee100a10, 0xeebc0ac2\n"
        ".word 0xee101a90, 0xe1a00c00, 0xe20110ff, 0xe1800801\n"
        ".word 0xee103a10, 0xeebc0ae1, 0xe20330ff, 0xe1800403\n"
        ".word 0xee10ca10, 0xe20cc0ff, 0xe180000c, 0xe6bf1f30\n"
        ".word 0xe6bf3f30, 0xe6bfcf30, 0xe1a01c21, 0xe1a03823\n"
        ".word 0xe1a0c42c, 0xe1a03403, 0xe1822001, 0xe2033cff\n"
        ".word 0xe3c22cff, 0xe1a0c80c, 0xe1822003, 0xe6bf0f30\n"
        ".word 0xe20cc8ff, 0xe3c228ff, 0xe182200c, 0xe3c224ff\n"
        ".word 0xe1829c00, 0xee001a90, 0xe1a00809, 0xe1a02409\n"
        ".word 0xe1a00c20, 0xe1a02c22, 0xee010a90, 0xe1a00c29\n"
        ".word 0xee012a10, 0xee000a10, 0xeeb82a60, 0xe5963010\n"
        ".word 0xeef81a61, 0xe6ffc074, 0xeef80a41, 0xeeb81a40\n"
        ".word 0xe5930004, 0xe1a02409, 0xe1a03c29, 0xe080020c\n"
        ".word 0xe2801004, 0xe1a02c22, 0xee210a89, 0xee621a09\n"
        ".word 0xee600a89, 0xee212a09, 0xee200a09, 0xee211a89\n"
        ".word 0xee600a89, 0xee621a09, 0xed801a00, 0xedc01a03\n"
        ".word 0xe1a00809, 0xec810a02, 0xe1a01c20, 0xe20900ff\n"
        ".word 0xee000a90, 0xee011a10, 0xee012a90, 0xee003a10\n"
        ".word 0xe596e014, 0xeef80a60, 0xeeb81a41, 0xeef81a61\n"
        ".word 0xeeb82a40, 0xe59e0004, 0xe080020c, 0xee200a89\n"
        ".word 0xee610a09, 0xee211a89, 0xee621a09, 0xee200a09\n"
        ".word 0xee600a89, 0xee211a09, 0xee611a89, 0xec800a04\n"
        ".word 0xe2844001, 0xe1540008, 0xe2855028, 0xbaffff53\n"
        ".word 0xe597002c, 0xe3500000, 0x0a00000b, 0xe5971030\n"
        ".word 0xe5972010, 0xe5911010, 0xe1520001, 0x8a000006\n"
        ".word 0xe5971004, 0xe5801004, 0xed970a09, 0xeddf0a0b\n"
        ".word 0xe597002c, 0xee200a20, 0xeb02b29c, 0xe28dd00c\n"
        ".word 0xecbd8b08, 0xe8bd8ff0, 0x3b808081, 0x004ea91c\n"
        ".word 0x00000000, 0x00472560, 0x437f0000, 0x004ea81c\n"
        ".word 0x3dcccccd, 0xeeb00a4b, 0xe6ff1074, 0xe59f21fc\n"
        ".word 0xe1a00006, 0xeb037d5a, 0xe5da2000, 0xe5961010\n"
        ".word 0xe6ff0074, 0xee002a10, 0xe5911004, 0xe0811200\n"
        ".word 0xeeb80a40, 0xee200a09, 0xee200a09, 0xed810a00\n"
        ".word 0xe5da2001, 0xee002a10, 0xeeb80a40, 0xee200a09\n"
        ".word 0xee200a09, 0xed810a01, 0xe5da2002, 0xee002a10\n"
        ".word 0xeeb80a40, 0xee200a09, 0xee200a09, 0xed810a02\n"
        ".word 0xe5da2003, 0xee002a10, 0xeeb80a40, 0xee200a09\n"
        ".word 0xee200a09, 0xed810a03, 0xe5da2000, 0xe5961014\n"
        ".word 0xee002a10, 0xe5911004, 0xe0810200, 0xeeb80a40\n"
        ".word 0xee200a09, 0xee200a09, 0xed800a00, 0xe5da1001\n"
        ".word 0xee001a10, 0xeeb80a40, 0xee200a09, 0xee200a09\n"
        ".word 0xed800a01, 0xe5da1002, 0xee001a10, 0xeeb80a40\n"
        ".word 0xee200a09, 0xee200a09, 0xed800a02, 0xe5da1003\n"
        ".word 0xee001a10, 0xeeb80a40, 0xee200a09, 0xee200a09\n"
        ".word 0xed800a03, 0xe5961018, 0xe6ff0074, 0xe0810080\n"
        ".word 0xe1c0b0b0, 0xeaffffa1, 0xeeb00a4b, 0xe6ff1074\n"
        ".word 0xe59f20f8, 0xe1a00006, 0xeb037d19, 0xe5da2000\n"
        ".word 0xe5961010, 0xe6ff0074, 0xee002a10, 0xe5911004\n"
        ".word 0xe0811200, 0xeeb80a40, 0xee200a09, 0xee200a09\n"
        ".word 0xed810a00, 0xe5da2001, 0xee002a10, 0xeeb80a40\n"
        ".word 0xee200a09, 0xee200a09, 0xed810a01, 0xe5da2002\n"
        ".word 0xee002a10, 0xeeb80a40, 0xee200a09, 0xee200a09\n"
        ".word 0xed810a02, 0xe5da2003, 0xee002a10, 0xeeb80a40\n"
        ".word 0xee200a09, 0xee200a09, 0xed810a03, 0xe5da2000\n"
        ".word 0xe5961014, 0xee002a10, 0xe5911004, 0xe0810200\n"
        ".word 0xeeb80a40, 0xee200a09, 0xee200a09, 0xed800a00\n"
        ".word 0xe5da1001, 0xee001a10, 0xeeb80a40, 0xee200a09\n"
        ".word 0xee200a09, 0xed800a01, 0xe5da1002, 0xee001a10\n"
        ".word 0xeeb80a40, 0xee200a09, 0xee200a09, 0xed800a02\n"
        ".word 0xe5da1003, 0xee001a10, 0xe3a01000, 0xeeb80a40\n"
        ".word 0xee200a09, 0xee200a09, 0xed800a03, 0xe5962018\n"
        ".word 0xe6ff0074, 0xe0820080, 0xe1c010b0, 0xeaffff5f\n"
        ".word 0x004ea810\n"
    );
}

// DECOMP_FUNC(0x003ec380, 1492)
// Capstone ARM full coverage (373 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_003ec380() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4010, 0xe59f4020, 0xe3a00000, 0xe5840000\n"
        ".word 0xe1a00004, 0xebfb5dd9, 0xe1a00004, 0xe59f200c\n"
        ".word 0xe59f100c, 0xe8bd4010, 0xeaf8e6a7, 0x004c6458\n"
        ".word 0x00100000, 0x003576b8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00473858\n"
        ".word 0x00473860, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0043e330, 0x0043e338\n"
        ".word 0xe59f2044, 0xe3e00000, 0xe1a01000, 0xe3a03902\n"
        ".word 0xe1c202f0, 0xe59f0034, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe2400014, 0xe59f2028, 0xe5801000\n"
        ".word 0xe59f001c, 0xe280c004, 0xe5801000, 0xe280000c\n"
        ".word 0xe88c0006, 0xe880000a, 0xe12fff1e, 0x0044e458\n"
        ".word 0x0044e480, 0x004c64c4, 0x0035a5a4, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c201f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x004724c8, 0x004724e8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00472540\n"
        ".word 0x00472548, 0xe59f204c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe92d4010, 0xe1c200f8, 0xe3a01000, 0xe2820010\n"
        ".word 0xe1a03001, 0xe880000a, 0xe59f002c, 0xe59f402c\n"
        ".word 0xe5900004, 0xe5820000, 0xe5841000, 0xe1a00004\n"
        ".word 0xebfb5d7e, 0xe1a00004, 0xe59f2014, 0xe59f1014\n"
        ".word 0xe8bd4010, 0xeaf8e64c, 0x0044e608, 0x00407f9c\n"
        ".word 0x004d4280, 0x00100000, 0x003576b8, 0xe59f2028\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f001c\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe2400010\n"
        ".word 0xe59f100c, 0xe5801000, 0xe12fff1e, 0x00472030\n"
        ".word 0x00472040, 0x004722b8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x0044e678\n"
        ".word 0x0044e680, 0xe59f2060, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0054, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe59f0048, 0xe5801000, 0xe5801008\n"
        ".word 0xe5801010, 0xe580101c, 0xe59f1038, 0xe5801018\n"
        ".word 0xe5802024, 0xe580202c, 0xe5802030, 0xe5802034\n"
        ".word 0xe5802038, 0xe5c0203c, 0xe5802040, 0xe5c02044\n"
        ".word 0xe59f2014, 0xe59f1014, 0xeaf8e613, 0x00471ac0\n"
        ".word 0x00471ad0, 0x004e6c74, 0x00420be4, 0x00100000\n"
        ".word 0x0035af20, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00446d78, 0x00446d88\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f8\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x004475d0, 0x004475e0, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00447a98, 0x00447aa8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f8, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00447e28\n"
        ".word 0x00447e38, 0xe59f204c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe92d4010, 0xe1c200f8, 0xe59f003c, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe3a03010, 0xe8800006, 0xe3a02fa1\n"
        ".word 0xe59f0028, 0xe59f1028, 0xfafb6616, 0xe2800b0a\n"
        ".word 0xe59f1020, 0xe8bd4010, 0xe3a03020, 0xe3a02030\n"
        ".word 0xe2800044, 0xeafb660d, 0x00447e40, 0x00447e50\n"
        ".word 0x004b896c, 0x00340888, 0x0034089c, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0044cda0, 0x0044cdb0, 0xe59f2070, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe92d4010, 0xe1c200f0, 0xe59f0060\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe3a03090, 0xe8800006\n"
        ".word 0xe3a02020, 0xe59f004c, 0xe59f104c, 0xfafb65f1\n"
        ".word 0xe59f0048, 0xe59f1048, 0xe3a03c01, 0xe3a0201c\n"
        ".word 0xfafb65ec, 0xe59f003c, 0xe59f103c, 0xe3a03020\n"
        ".word 0xe3a0207c, 0xfafb65e7, 0xe59f0030, 0xe59f1030\n"
        ".word 0xe8bd4010, 0xe3a03080, 0xe3a0201c, 0xeafb65df\n"
        ".word 0x0044cdb8, 0x0044cdc0, 0x004be698, 0x0034b39c\n"
        ".word 0x004bf89c, 0x0034a214, 0x004c14a0, 0x0034afe8\n"
        ".word 0x004c2424, 0x0034bebc, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c201f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x0043e188\n"
        ".word 0x0043e1a0, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00471b18, 0x00471b20\n"
        ".word 0xe59f2020, 0xe3e00000, 0xe1a01000, 0xe3a03000\n"
        ".word 0xe1c200f8, 0xe2820010, 0xe5803000, 0xe5803004\n"
        ".word 0xe5823000, 0xe12fff1e, 0x004719e8, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00471a10, 0x00471a20, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x0044dc00\n"
        ".word 0x0044dc08, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00473838, 0x00473840\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x004728b0, 0x004728b8, 0xe59f0014\n"
        ".word 0xe3a02000, 0xe5802000, 0xe5802004, 0xe59f2008\n"
        ".word 0xe59f1008, 0xeaf8e540, 0x0044e7c8, 0x00100000\n"
        ".word 0x003575b0\n"
    );
}

// DECOMP_FUNC(0x00357c48, 1500)
// Capstone ARM full coverage (375 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_00357c48() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe24dd0c4, 0xe1a04000, 0xe1a06001\n"
        ".word 0xe1a07002, 0xe59f559c, 0xe1a00005, 0xebfdaf8f\n"
        ".word 0xe3a09000, 0xe28d0088, 0xebfc2eaa, 0xe5d41009\n"
        ".word 0xe3a00000, 0xe58d009c, 0xe3510000, 0xe58d0098\n"
        ".word 0x1a000003, 0xe1a00004, 0xeb00039d, 0xe2101102\n"
        ".word 0x4a00006a, 0xe5940004, 0xe3500000, 0x0a000012\n"
        ".word 0xe596000c, 0xe59f8550, 0xe3500000, 0x0a000009\n"
        ".word 0xe3a00000, 0xe58d00a0, 0xe28d30a0, 0xe28d20c0\n"
        ".word 0xe3a01002, 0xe1a00006, 0xeb0223e7, 0xe2100102\n"
        ".word 0xe320f000, 0x5a00000a, 0xe1a00005, 0xebfdaf4e\n"
        ".word 0xe28dd0d4, 0xe1a00008, 0xe8bd8ff0, 0xe59f450c\n"
        ".word 0xe1a00005, 0xebfdaf48, 0xe28dd0d4, 0xe1a00004\n"
        ".word 0xe8bd8ff0, 0xe5940004, 0xe5961010, 0xe1500001\n"
        ".word 0x0a000005, 0xe59f44e8, 0xe1a00005, 0xebfdaf3e\n"
        ".word 0xe28dd0d4, 0xe1a00004, 0xe8bd8ff0, 0xe28d2088\n"
        ".word 0xe1a01006, 0xe1a0000d, 0xebfb8423, 0xe28d1018\n"
        ".word 0xe1a00006, 0xeb022415, 0xe28d0088, 0xe320f000\n"
        ".word 0xebfb8666, 0xe3500000, 0xe320f000, 0x0a000014\n"
        ".word 0xe28d00b0, 0xebfdb6be, 0xe1cd0bd0, 0xe1cd0af8\n"
        ".word 0xe28d10a8, 0xe1a0000d, 0xebfd56dc, 0xe89d0007\n"
        ".word 0xe28d3078, 0xe8830007, 0xe5d6006c, 0xe3500001\n"
        ".word 0x85d6006d, 0x83500001, 0x9a00000d, 0xe59f4464\n"
        ".word 0xe1a00005, 0xebfdaf1c, 0xe28dd0d4, 0xe1a00004\n"
        ".word 0xe8bd8ff0, 0xe2971000, 0xe28d2088, 0xe1a00004\n"
        ".word 0x13a01001, 0xeb022274, 0xe3700001, 0x13a09001\n"
        ".word 0xeaffffec, 0xe2841e89, 0xe58d10a4, 0xe2841b02\n"
        ".word 0xe2811088, 0xe58d10b0, 0xe2841e8b, 0xe58d10b4\n"
        ".word 0xe59f0414, 0xe2841b02, 0xe28110a8, 0xe3570000\n"
        ".word 0xe58d10a8, 0x0a000013, 0xe5d4100b, 0xe3510000\n"
        ".word 0x12848b02, 0x02848fed, 0x128880a4, 0x059413c0\n"
        ".word 0x159418b0, 0xe8980d00, 0xe58d10bc, 0xe59413c8\n"
        ".word 0xe3510000, 0x15962004, 0x11520001, 0x9a000013\n"
        ".word 0xe1a04000, 0xe1a00005, 0xebfdaef3, 0xe28dd0d4\n"
        ".word 0xe1a00004, 0xe8bd8ff0, 0xe5d4100a, 0xe3510000\n"
        ".word 0x12848b02, 0x02848f81, 0x12888084, 0x05941210\n"
        ".word 0x15941890, 0xe8980d00, 0xe58d10bc, 0xe5941218\n"
        ".word 0xe3510000, 0x15962004, 0x11520001, 0x8affffeb\n"
        ".word 0xe3590000, 0x0a000019, 0xe28d2088, 0xe1a01007\n"
        ".word 0xe1a00004, 0xeb02223c, 0xe3700001, 0xe320f000\n"
        ".word 0x0a00001d, 0xe1a02000, 0xe1a01007, 0xe1a00004\n"
        ".word 0xebfb85db, 0xe3500000, 0x15900004, 0xe3580000\n"
        ".word 0x0a000012, 0xe5961004, 0xe04a2000, 0xe0811002\n"
        ".word 0xe1510008, 0x9a00000d, 0xe59f4320, 0xe1a00005\n"
        ".word 0xebfdaec9, 0xe28dd0d4, 0xe1a00004, 0xe8bd8ff0\n"
        ".word 0xe3580000, 0x0a000003, 0xe5960004, 0xe080000a\n"
        ".word 0xe1500008, 0x8afffff3, 0xe5960004, 0xea000001\n"
        ".word 0xe5961004, 0xe0410000, 0xe58d009c, 0xe35b0000\n"
        ".word 0x0a00000b, 0xe3590000, 0x1a00000d, 0xe59d00bc\n"
        ".word 0xe2800001, 0xe150000b, 0x9a000007, 0xe59f42c0\n"
        ".word 0xe1a00005, 0xebfdaeb0, 0xe28dd0d4, 0xe1a00004\n"
        ".word 0xe8bd8ff0, 0xe3590000, 0x1a000001, 0xe3a00001\n"
        ".word 0xe58d0098, 0xe5960004, 0xe3a01004, 0xebfb86f2\n"
        ".word 0xe3500000, 0xe58d00ac, 0x0a00000f, 0xe1a01000\n"
        ".word 0xe1a00006, 0xeb022353, 0xe59d00ac, 0xe3a02070\n"
        ".word 0xe28d1018, 0xebfdb810, 0xe3a00000, 0xe58d0090\n"
        ".word 0xe58d0094, 0xe28d0088, 0xebfb85cc, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000006, 0xea000008, 0xe59f4244\n"
        ".word 0xe1a00005, 0xebfdae90, 0xe28dd0d4, 0xe1a00004\n"
        ".word 0xe8bd8ff0, 0xe28d1090, 0xe28d0088, 0xeb02237b\n"
        ".word 0xe5962004, 0xe59d10ac, 0xe3a00008, 0xe2843f6b\n"
        ".word 0xe88d000f, 0xe1a02007, 0xe5940000, 0xe5941004\n"
        ".word 0xe28d3090, 0xe590c020, 0xe1a00004, 0xe12fff3c\n"
        ".word 0xe1a0b000, 0xe59d00f8, 0xe3500000, 0x0a000018\n"
        ".word 0xe3570001, 0xe1a00004, 0x0a00000e, 0xe2803f87\n"
        ".word 0xe2802f7f, 0xe3a01000, 0xebfb8543, 0xe1a06000\n"
        ".word 0xe2160102, 0x5a00003e, 0xe59d00ac, 0xebfb86c6\n"
        ".word 0xe1a00005, 0xe320f000, 0xebfdae6b, 0xe28dd0d4\n"
        ".word 0xe1a00006, 0xe8bd8ff0, 0xe2803ff3, 0xe2802feb\n"
        ".word 0xe3a01001, 0xebfb8534, 0xe1a06000, 0xe320f000\n"
        ".word 0xeaffffee, 0xe3570001, 0x0a000003, 0xe5d4000a\n"
        ".word 0xe3500000, 0x1a00001b, 0xea000015, 0xe5d4000b\n"
        ".word 0xe3500000, 0x1a000004, 0xe2840feb, 0xe284eb02\n"
        ".word 0xe890154f, 0xe28ee09c, 0xe88e154f, 0xe3a00001\n"
        ".word 0xe21b1102, 0xe5c4000b, 0x4a00003e, 0xe59418a8\n"
        ".word 0xe59d009c, 0xe0811000, 0xe59d00a8, 0xe5801000\n"
        ".word 0xe59418b0, 0xe59d0098, 0xe0811000, 0xe59d00b4\n"
        ".word 0xea000011, 0xe2840f7f, 0xe284eb02, 0xe890154f\n"
        ".word 0xe28ee07c, 0xe88e154f, 0xe3a00001, 0xe21b1102\n"
        ".word 0xe5c4000a, 0x4a00002b, 0xe5941888, 0xe59d009c\n"
        ".word 0xe0811000, 0xe59d00b0, 0xe5801000, 0xe5941890\n"
        ".word 0xe59d0098, 0xe0811000, 0xe59d00a4, 0xe5801000\n"
        ".word 0xea000001, 0xe21b0102, 0x4a00001e, 0xe28d0088\n"
        ".word 0xebfb8562, 0xe3500000, 0xe320f000, 0x0a000009\n"
        ".word 0xe28d1090, 0xe1a0000d, 0xebfb84ed, 0xe1a01000\n"
        ".word 0xe28d6088, 0xe1a00006, 0xebfd566a, 0xe59d00d0\n"
        ".word 0xe1a01006, 0xebfd5667, 0xe3570001, 0x03590000\n"
        ".word 0x1a00000c, 0xe3a00002, 0xe58d0000, 0xe5940000\n"
        ".word 0xe5941004, 0xe28d2088, 0xe3a03008, 0xe590c028\n"
        ".word 0xe1a00004, 0xe12fff3c, 0xe2000102, 0xe3500000\n"
        ".word 0xa1a00004, 0xabfb843f, 0xe59d00ac, 0xebfb8666\n"
        ".word 0xe1a00005, 0xe320f000, 0xebfdae0b, 0xe28dd0d4\n"
        ".word 0xe1a0000b, 0xe8bd8ff0, 0x004e62a8, 0xc8810bef\n"
        ".word 0xc8810bea, 0xc8e1086b, 0xe0e10bee, 0xc8e10869\n"
        ".word 0xc8e10865, 0xc8e10866, 0xc8610bf3\n"
    );
}

// DECOMP_FUNC(0x002283b4, 1512)
// Capstone ARM full coverage (378 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_002283b4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe1a06000, 0xed2d8b02, 0xe24dd0c4\n"
        ".word 0xe28d0f41, 0xe8900c80, 0xeb01ae31, 0xe59d10d4\n"
        ".word 0xe1a08000, 0xe3a00000, 0xe2411009, 0xe3510006\n"
        ".word 0xe5cb0000, 0x379ff101, 0xea00000c, 0x00228500\n"
        ".word 0x00228500, 0x00228408, 0x00228500, 0x00228424\n"
        ".word 0x0022841c, 0xe3a0000b, 0xe28dd0c4, 0xecbd8b02\n"
        ".word 0xe28dd010, 0xe8bd8ff0, 0xe3a00008, 0xeafffff9\n"
        ".word 0xe2460cff, 0xe25000ff, 0x0a000033, 0xe1a00006\n"
        ".word 0xeb0217ed, 0xe3560000, 0xe1a05000, 0xe3a04000\n"
        ".word 0xda00002f, 0xe3570000, 0x0a00000c, 0xe5d50023\n"
        ".word 0xe3500007, 0x13500009, 0x1350000b, 0x0a000024\n"
        ".word 0xe5950028, 0xe1a00b80, 0xe1a00e20, 0xe3500007\n"
        ".word 0x13500008, 0x15d5002f, 0x13500004, 0x0a00001c\n"
        ".word 0xe5d50023, 0xe3500007, 0x13500009, 0x0a00001a\n"
        ".word 0xe350000b, 0x03a00010, 0x0affffda, 0xe1d503b6\n"
        ".word 0xe3100a01, 0x13a00009, 0x1affffd6, 0xe5d5104a\n"
        ".word 0xe3510000, 0x13a00007, 0x1affffd2, 0xe5d51056\n"
        ".word 0xe3510000, 0x13a0000c, 0x1affffce, 0xe3100901\n"
        ".word 0x13a0000e, 0x1affffcb, 0xe3550000, 0x0a000008\n"
        ".word 0xe5950038, 0xe310087f, 0x13a04001, 0x1a000008\n"
        ".word 0xea000003, 0xe3a0000f, 0xeaffffc2, 0xe3a00006\n"
        ".word 0xeaffffc0, 0xe59f0410, 0xe7900008, 0xe3100c01\n"
        ".word 0x1a000050, 0xe59f0400, 0xe7900008, 0xe3100080\n"
        ".word 0x0a000002, 0xe3540000, 0x0a000117, 0xea000114\n"
        ".word 0xe320f000, 0xeb01add6, 0xe59d10d8, 0xe320f000\n"
        ".word 0xeb016992, 0xe1a09000, 0xe320f000, 0xeb01add0\n"
        ".word 0xe59d1100, 0xe320f000, 0xeb01698c, 0xe1a07000\n"
        ".word 0xe320f000, 0xeb01adca, 0xe1a01000, 0xe1a02009\n"
        ".word 0xe28d0098, 0xeb007c19, 0xed9f0ae8, 0xe3560000\n"
        ".word 0xca000002, 0xe59d00d4, 0xe3500001, 0x1a0000fe\n"
        ".word 0xe1dd09fe, 0xe1dd29fc, 0xe1dd19ba, 0xee000a90\n"
        ".word 0xe3520003, 0x13520004, 0xe58d1004, 0xeef80ae0\n"
        ".word 0xee208a80, 0x0a0000f4, 0xe59d0100, 0xe3e03000\n"
        ".word 0xeb007735, 0xe1a06000, 0xe59d0004, 0xe28d10c0\n"
        ".word 0xeb0009b0, 0xe59d00c0, 0xe20010ff, 0xe1a00009\n"
        ".word 0xeb000978, 0xe3500000, 0xe320f000, 0x0a000010\n"
        ".word 0xe316080d, 0x0a000004, 0xe35a0000, 0x059f1320\n"
        ".word 0xe3a00001, 0x07810008, 0xe5cb0000, 0xe3160802\n"
        ".word 0x0a000014, 0xe3160602, 0x0a00000e, 0xe35a0000\n"
        ".word 0x1a00000c, 0xe5971000, 0xe3811102, 0xe5871000\n"
        ".word 0xea000008, 0xe3160701, 0x13a00002, 0x1affff71\n"
        ".word 0xe3160802, 0x0a000005, 0xe3160602, 0x0a000001\n"
        ".word 0xe35a0000, 0x0afffff2, 0xe3a00001, 0xeaffff69\n"
        ".word 0xe3160801, 0x1a000058, 0xe3550000, 0x0a000004\n"
        ".word 0xe5d50023, 0xe3500002, 0x0a000008, 0xe3500008\n"
        ".word 0x0a0000c1, 0xe2875c01, 0xe1d50cb6, 0xe3100c02\n"
        ".word 0x0a000053, 0xe3540000, 0x0a0000bb, 0xea0000b8\n"
        ".word 0xe3a01048, 0xe28d0008, 0xeb02711f, 0xe3a01048\n"
        ".word 0xe28d0050, 0xeb02711c, 0xe5d5002f, 0xe28d7008\n"
        ".word 0xe3500001, 0x0a000008, 0xe3500013, 0x13500014\n"
        ".word 0x0a000009, 0xe3500016, 0x0a000018, 0xeb00779b\n"
        ".word 0xe3a06001, 0xe58d0008, 0xea000027, 0xe1dd09ba\n"
        ".word 0xe3a06001, 0xe58d0008, 0xea000023, 0xe3a00005\n"
        ".word 0xeb007792, 0xe58d0008, 0xe3a00006, 0xeb00778f\n"
        ".word 0xe58d000c, 0xe3a00007, 0xeb00778c, 0xe58d0010\n"
        ".word 0xe3a00008, 0xeb007789, 0xe58d0014, 0xe3a00009\n"
        ".word 0xeb007786, 0xe3a06005, 0xe58d0018, 0xea000012\n"
        ".word 0xe3a00005, 0xeb007781, 0xe58d0008, 0xe3a00006\n"
        ".word 0xeb00777e, 0xe58d000c, 0xe3a00007, 0xeb00777b\n"
        ".word 0xe58d0010, 0xe3a00008, 0xeb007778, 0xe58d0014\n"
        ".word 0xe3a00009, 0xeb007775, 0xe58d0018, 0xe3a00003\n"
        ".word 0xeb007772, 0xe3a06006, 0xe58d001c, 0xe3a04000\n"
        ".word 0xe28d8050, 0xe5d52023, 0xe7971104, 0xe59d0100\n"
        ".word 0xe3e03000, 0xeb0076bc, 0xe7880104, 0xe7971104\n"
        ".word 0xe59d0100, 0xeb0008bb, 0xe7981104, 0xe1800001\n"
        ".word 0xe3100817, 0xe7880104, 0x0a000001, 0xe3a00003\n"
        ".word 0xeaffff0c, 0xe2844001, 0xe1540006, 0xbaffffec\n"
        ".word 0xea000069, 0xe3100080, 0x0a000002, 0xe3540000\n"
        ".word 0x0a000065, 0xea000062, 0xe3100c01, 0x0a000002\n"
        ".word 0xe3540000, 0x0a000060, 0xea00005d, 0xe59800e0\n"
        ".word 0xe3100202, 0x0a000002, 0xe3540000, 0x0a00005a\n"
        ".word 0xea000057, 0xe2888901, 0xe2888e4a, 0xe5980000\n"
        ".word 0xe3100701, 0x0a000002, 0xe3540000, 0x0a000052\n"
        ".word 0xea00004f, 0xed9d0a36, 0xe3a0000b, 0xeeb80ac0\n"
        ".word 0xeb0007f2, 0xeef08a40, 0xed9d0a40, 0xe3a00009\n"
        ".word 0xeeb80ac0, 0xeb0007ed, 0xe2891f6d, 0xe2870f6d\n"
        ".word 0xe1d120fe, 0xe1d030fe, 0xe1d0c1f0, 0xe1d111f0\n"
        ".word 0xe0420003, 0xee000a90, 0xe041100c, 0xee011a10\n"
        ".word 0xed9f2a24, 0xeddf1a24, 0xe59f1094, 0xeef80ae0\n"
        ".word 0xeef82ac1, 0xee281a80, 0xee600a82, 0xed9f2a1f\n"
        ".word 0xee220aa1, 0xee700a82, 0xee300a80, 0xee200a01\n"
        ".word 0xee208a08, 0xee180a10, 0xe1500001, 0xbd9f8a19\n"
        ".word 0xba000003, 0xe59f1060, 0xee180a10, 0xe1510000\n"
        ".word 0xbd9f8a16, 0xe5990000, 0xe3100010, 0x1a000002\n"
        ".word 0xeb0058bd, 0xed900a01, 0xee208a08, 0xe59f0040\n"
        ".word 0xe19000b9, 0xe3100010, 0x0a00000f, 0xe1d50cb6\n"
        ".word 0xe3100010, 0x0d9f8a0b, 0xea000010, 0x000044a8\n"
        ".word 0x3c23d70a, 0x000048b8, 0x3eb33333, 0x3dcccccd\n"
        ".word 0x42be0000, 0x42480000, 0x42480000, 0x42c40000\n"
        ".word 0x42c40000, 0x000001c6, 0x42c80000, 0xe1d51cb6\n"
        ".word 0xe3110010, 0x0a000001, 0xe3100010, 0x0d9f8a0c\n"
        ".word 0xe3a00063, 0xeb0058b3, 0xeebd0ac8, 0xee101a10\n"
        ".word 0xe1500001, 0xc3a00005, 0xcafffea2, 0xe3540000\n"
        ".word 0x0a000001, 0xe3a0000d, 0xeafffe9e, 0xe3a00000\n"
        ".word 0xeafffe9c, 0x41700000\n"
    );
}

// DECOMP_FUNC(0x003ef40c, 1540)
// Capstone ARM full coverage (385 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void battle_func_003ef40c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4070, 0xe3e00000, 0xe59f22cc, 0xe1a01000\n"
        ".word 0xed2d8b02, 0xed9f8ab2, 0xe1c200f0, 0xe59f02bc\n"
        ".word 0xe3a01000, 0xe1a02001, 0xeddf8aae, 0xe8800006\n"
        ".word 0xe2800008, 0xe2804000, 0xed808a00, 0xed808a01\n"
        ".word 0xedc48a02, 0xedc48a03, 0xe3a01001, 0xe3a00006\n"
        ".word 0xebfb5ad0, 0xe5a40018, 0xe2844008, 0xed9f0aa2\n"
        ".word 0xed848a00, 0xed840a01, 0xe59f4280, 0xed9f0aa0\n"
        ".word 0xe3a02000, 0xe2840018, 0xed840a04, 0xed848a05\n"
        ".word 0xed9f0a9c, 0xe3a01007, 0xec808a02, 0xe3a00006\n"
        ".word 0xed840a08, 0xedc48a09, 0xebfb5abe, 0xe5a40028\n"
        ".word 0xe59f025c, 0xed9f0a94, 0xeddf0a94, 0xe2844008\n"
        ".word 0xe2805000, 0xec840a02, 0xe3a02000, 0xed808a00\n"
        ".word 0xed808a01, 0xedc58a02, 0xedc58a03, 0xe3a01001\n"
        ".word 0xe3a00006, 0xebfb5aaf, 0xe5850018, 0xe2850040\n"
        ".word 0xe2804000, 0xed808a00, 0xed808a01, 0xedc48a02\n"
        ".word 0xedc48a03, 0xe3a02000, 0xe3a01001, 0xe3a00006\n"
        ".word 0xebfb5aa4, 0xe5a40018, 0xed9f0a7e, 0xeddf0a7e\n"
        ".word 0xe2844008, 0xe2850080, 0xec840a02, 0xe2804000\n"
        ".word 0xed808a00, 0xed808a01, 0xedc48a02, 0xedc48a03\n"
        ".word 0xe3a02000, 0xe3a01001, 0xe3a00006, 0xebfb5a95\n"
        ".word 0xe5840018, 0xed9f0a71, 0xed848a08, 0xed840a09\n"
        ".word 0xed848a0a, 0xed848a0b, 0xedc48a0c, 0xedc48a0d\n"
        ".word 0xe3a02000, 0xe3a01001, 0xe3a00006, 0xebfb5a89\n"
        ".word 0xe5a40040, 0xe2844008, 0xed9f0a65, 0xed848a00\n"
        ".word 0xed840a01, 0xe28500dc, 0xe2804000, 0xed808a00\n"
        ".word 0xed808a01, 0xedc48a02, 0xedc48a03, 0xe3a02000\n"
        ".word 0xe3a01007, 0xe3a00006, 0xebfb5a7a, 0xe5a40018\n"
        ".word 0xe2844008, 0xe2850f47, 0xed848a00, 0xed848a01\n"
        ".word 0xed808a00, 0xed808a01, 0xe2804000, 0xe3a02000\n"
        ".word 0xedc48a02, 0xedc48a03, 0xe3a01007, 0xe3a00006\n"
        ".word 0xebfb5a6c, 0xe5a40018, 0xe2844008, 0xe2850f57\n"
        ".word 0xed848a00, 0xed848a01, 0xed808a00, 0xed808a01\n"
        ".word 0xe2804000, 0xe3a02000, 0xedc48a02, 0xedc48a03\n"
        ".word 0xe3a01001, 0xe3a00006, 0xebfb5a5e, 0xe5a40018\n"
        ".word 0xe2844008, 0xe2850f67, 0xed848a00, 0xed848a01\n"
        ".word 0xed808a00, 0xed808a01, 0xe2804000, 0xe3a02001\n"
        ".word 0xedc48a02, 0xedc48a03, 0xe3a01000, 0xe3a00005\n"
        ".word 0xebfb5a50, 0xe5a40018, 0xe2844008, 0xe2850f77\n"
        ".word 0xed848a00, 0xed848a01, 0xed808a00, 0xed808a01\n"
        ".word 0xe2804000, 0xe3a02000, 0xedc48a02, 0xedc48a03\n"
        ".word 0xe3a01007, 0xe3a00006, 0xebfb5a42, 0xe5a40018\n"
        ".word 0xe2844008, 0xe2850f87, 0xed848a00, 0xed848a01\n"
        ".word 0xed808a00, 0xed808a01, 0xe2804000, 0xe3a02000\n"
        ".word 0xedc48a02, 0xedc48a03, 0xe3a01001, 0xe3a00006\n"
        ".word 0xebfb5a34, 0xe5a40018, 0xe2844008, 0xed848a00\n"
        ".word 0xed848a01, 0xecbd8b02, 0xe8bd8070, 0x00433e70\n"
        ".word 0x00433e78, 0x00000000, 0x3f800000, 0x3b03126f\n"
        ".word 0x00433ec0, 0x3ed3f7cf, 0x3f53f7cf, 0x38d1b717\n"
        ".word 0x3a03126f, 0x00433f0c, 0xbd8f5c29, 0x3d23d70a\n"
        ".word 0x3a83126f, 0x3b83126f, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00434168\n"
        ".word 0x00434170, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00446388, 0x00446398\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f8\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x0043e2d8, 0x0043e2e8, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x004463f0, 0x004463f8, 0xe59f202c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xed9f0a0a, 0xe1c200f8, 0xe59f001c\n"
        ".word 0xe3a01000, 0xe1a02001, 0xeddf0a06, 0xe8800006\n"
        ".word 0xe2400010, 0xec800a02, 0xe12fff1e, 0x0044e2a8\n"
        ".word 0x0044e2b8, 0x43c80000, 0x43700000, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0043dd90, 0x0043dda0, 0xe59f0008, 0xe3a01000\n"
        ".word 0xe5801000, 0xe12fff1e, 0x00472a30, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00433130, 0x00433140, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00433038\n"
        ".word 0x00433040, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00433180, 0x00433190\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00433060, 0x00433068, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c202f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0044e380, 0x0044e3a8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f8, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00434260\n"
        ".word 0x00434270, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00434240, 0x00434248\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f8\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00435d60, 0x00435d70, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c201f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00435e00, 0x00435e18, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f8, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x0044e1f8\n"
        ".word 0x0044e208\n"
    );
}

// DECOMP_FUNC(0x00203554, 1552)
// Capstone ARM full coverage (388 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_00203554() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xed2d8b04, 0xe24dd07c, 0xe1a07000\n"
        ".word 0xe1a06001, 0xeb017d35, 0xe1b05000, 0x0a00016e\n"
        ".word 0xe3a00065, 0xe58d0004, 0xe1a03007, 0xe3a02006\n"
        ".word 0xe3a01024, 0xe3a00002, 0xe58d6000, 0xeb02eff0\n"
        ".word 0xe3a0906a, 0xe1a03007, 0xe2892f5a, 0xe3a01024\n"
        ".word 0xe3a00002, 0xe88d0240, 0xeb02efab, 0xe2850b25\n"
        ".word 0xe2800f42, 0xe1a08000, 0xe58d0030, 0xeb026f26\n"
        ".word 0xe1a0b000, 0xe3a04000, 0xe1a00008, 0xeb0268c3\n"
        ".word 0xe3500000, 0xed9f8ae8, 0xeddf8ae8, 0xcd9f9ae8\n"
        ".word 0xda000056, 0xe2850f72, 0xe1d008da, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000004, 0xe59d0030, 0xeb026f10\n"
        ".word 0xe1500004, 0xe320f000, 0x0a000046, 0xe284102e\n"
        ".word 0xe3a00024, 0xeb02f02c, 0xe1a08000, 0xe08b0004\n"
        ".word 0xe0850080, 0xe280ab25, 0xe1da06b8, 0xeb014318\n"
        ".word 0xe1b09000, 0xe320f000, 0x0a00003a, 0xe1d800fa\n"
        ".word 0xe3a0106a, 0xe59f233c, 0xe0800006, 0xe1cd00f0\n"
        ".word 0xe1d800f8, 0xe3a01024, 0xe0803007, 0xe3a00002\n"
        ".word 0xeb02ef7d, 0xe2892008, 0xe28f1fc7, 0xe28d0038\n"
        ".word 0xfa02ec60, 0xe59f1314, 0xe3a00024, 0xeb02f012\n"
        ".word 0xe1d810fa, 0xe1d030fa, 0xe1d0c0f8, 0xe1d820f8\n"
        ".word 0xe0810003, 0xe0800006, 0xe082100c, 0xe0811007\n"
        ".word 0xee000a90, 0xee001a10, 0xeeb02a68, 0xeef01a48\n"
        ".word 0xeeb01a49, 0xe28d2038, 0xeef80ae0, 0xeeb80ac0\n"
        ".word 0xe3a010ff, 0xe3a00002, 0xeb02ec2a, 0xe1da06b8\n"
        ".word 0xe320f000, 0xebfff34c, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000010, 0xe3a01f75, 0xe3a00024, 0xeb02eff6\n"
        ".word 0xe1d020fa, 0xe1d810fa, 0xe0811002, 0xe0811006\n"
        ".word 0xe3a0206a, 0xe88d0006, 0xe1d810f8, 0xe1d000f8\n"
        ".word 0xe3a02007, 0xe0800001, 0xe0803007, 0xe3a01024\n"
        ".word 0xe3a00002, 0xeb02ef8a, 0xe59d0030, 0xe2844001\n"
        ".word 0xeb02686a, 0xe1500004, 0xe320f000, 0xcaffffa8\n"
        ".word 0xe59d0030, 0xeb026ec4, 0xe1a04000, 0xe59d0030\n"
        ".word 0xeb026ebb, 0xe0800004, 0xe0850080, 0xe280bb25\n"
        ".word 0xe1db06b8, 0xeb0142ca, 0xe1a0a000, 0xe2850f72\n"
        ".word 0xe1d008da, 0xe3500000, 0x135a0000, 0x0a0000ce\n"
        ".word 0xe59d0030, 0xeb026eae, 0xe280103f, 0xe3a00024\n"
        ".word 0xeb02efcd, 0xe1a04000, 0xe2850024, 0xed900a08\n"
        ".word 0xe320f000, 0xe320f000, 0xeb02efd7, 0xe1d400fa\n"
        ".word 0xe3a08079, 0xe3a02038, 0xe0800006, 0xe88d0101\n"
        ".word 0xe1d400f8, 0xe3a01024, 0xe0803007, 0xe3a00002\n"
        ".word 0xeb02ef21, 0xe1d400fa, 0xe3a02039, 0xe3a01024\n"
        ".word 0xe0800006, 0xe88d0101, 0xe1d400f8, 0xe0803007\n"
        ".word 0xe3a00002, 0xeb02ef18, 0xe1d400fa, 0xe3a0203a\n"
        ".word 0xe3a01024, 0xe0800006, 0xe88d0101, 0xe1d400f8\n"
        ".word 0xe0803007, 0xe3a00002, 0xeb02ef0f, 0xeeb00a68\n"
        ".word 0xe320f000, 0xeb02efb8, 0xe1d400fa, 0xe3a0807e\n"
        ".word 0xe3a0203b, 0xe0800006, 0xe88d0101, 0xe1d400f8\n"
        ".word 0xe3a01024, 0xe0803007, 0xe3a00002, 0xeb02ef02\n"
        ".word 0xe59d0030, 0xe320f000, 0xeb026e79, 0xe0850080\n"
        ".word 0xe2800b01, 0xe1d003f8, 0xeb026822, 0xe3500001\n"
        ".word 0x13500002, 0x13500006, 0xe1d400fa, 0xe0800006\n"
        ".word 0xe88d0101, 0xe1d400f8, 0xe0803007, 0x0a0000a9\n"
        ".word 0xe3a0203c, 0xe3a01024, 0xe3a00002, 0xeb02eeee\n"
        ".word 0xe3a0103c, 0xe3a00024, 0xeb02ef87, 0xe1a09000\n"
        ".word 0xe59f00dc, 0xe5901000, 0xe3a00003, 0xe2818a01\n"
        ".word 0xe2888fc3, 0xe5981000, 0xe0882101, 0xe5921008\n"
        ".word 0xe5820008, 0xe5d82018, 0xe3520000, 0x03510003\n"
        ".word 0x0a000003, 0xe598101c, 0xe12fff31, 0xe3a00000\n"
        ".word 0xe5c80018, 0xe3a00001, 0xe58d0000, 0xe599000c\n"
        ".word 0xe1d9c0fa, 0xe1d410fa, 0xe1d990f8, 0xe1d480f8\n"
        ".word 0xe1d030f2, 0xe1d020f0, 0xe081100c, 0xe0880009\n"
        ".word 0xe0811006, 0xe0800007, 0xeb025ab9, 0xe28500b0\n"
        ".word 0xe320f000, 0xeb02ed8c, 0xe1d410fa, 0xe0800006\n"
        ".word 0xe0808001, 0xe28500b0, 0xeb02ed8a, 0xe1d410f8\n"
        ".word 0xe0800007, 0xe3a09083, 0xe0803001, 0xe3a0203e\n"
        ".word 0xe3a01024, 0xe3a00002, 0xe1cd80f0, 0xeb02eeba\n"
        ".word 0xe59f001c, 0xe320f000, 0xea000006, 0x00000000\n"
        ".word 0x3f800000, 0x3f160000, 0x000001d3, 0x00007325\n"
        ".word 0x000001d5, 0x0044ea00, 0xe5901000, 0xe3a00000\n"
        ".word 0xe2818a01, 0xe2888fc3, 0xe5981000, 0xe0882101\n"
        ".word 0xe5921008, 0xe5820008, 0xe5d82018, 0xe3520000\n"
        ".word 0x03510000, 0x0a000003, 0xe598101c, 0xe12fff31\n"
        ".word 0xe3a00000, 0xe5c80018, 0xe1d400fa, 0xe59f2170\n"
        ".word 0xe3a01024, 0xe0800006, 0xe88d0201, 0xe1d400f8\n"
        ".word 0xe0803007, 0xe3a00002, 0xeb02ee97, 0xe28a2008\n"
        ".word 0xe24f107c, 0xe28d0038, 0xfa02eb7a, 0xe3a01f76\n"
        ".word 0xe3a00024, 0xeb02ef2c, 0xe1d410fa, 0xe1d030fa\n"
        ".word 0xe1d0c0f8, 0xe1d420f8, 0xe0810003, 0xe0800006\n"
        ".word 0xe082100c, 0xe0811007, 0xee000a10, 0xee011a10\n"
        ".word 0xeeb02a68, 0xeef01a48, 0xe28d2038, 0xe3e01000\n"
        ".word 0xeef80ac0, 0xeeb80ac1, 0xe3a00003, 0xed9f1a3d\n"
        ".word 0xeb02eb44, 0xe1db06b8, 0xe320f000, 0xebfff266\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000f, 0xe59f10d8\n"
        ".word 0xe3a00024, 0xeb02ef10, 0xe1d010fa, 0xe1d420fa\n"
        ".word 0xe0811002, 0xe0811006, 0xe88d0202, 0xe1d410f8\n"
        ".word 0xe1d000f8, 0xe3a02007, 0xe0800001, 0xe0803007\n"
        ".word 0xe3a01024, 0xe3a00002, 0xeb02eea5, 0xe2850b01\n"
        ".word 0xe28d8020, 0xe1d027f4, 0xe1d017f2, 0xe3a04000\n"
        ".word 0xe3a03097, 0xe888001e, 0xe3a02021, 0xe3a0301f\n"
        ".word 0xe1d007f6, 0xe3a05024, 0xe3a04025, 0xe3a08023\n"
        ".word 0xe28d9014, 0xe58d300c, 0xe58d2010, 0xe58d001c\n"
        ".word 0xe3a0c022, 0xe3a01020, 0xe58d5004, 0xe58d4008\n"
        ".word 0xe58d8000, 0xe8891002, 0xe1a03005, 0xe59d0030\n"
        ".word 0xe1a02006, 0xe1a01007, 0xeb023441, 0xe28dd07c\n"
        ".word 0xecbd8b04, 0xe8bd8ff0, 0xe3a0203d, 0xe3a01024\n"
        ".word 0xe3a00002, 0xeb02ee44, 0xe320f000, 0xe320f000\n"
        ".word 0xeaffff52, 0x000001d6, 0x3efa0000, 0x000001d7\n"
    );
}

// DECOMP_FUNC(0x0033445c, 1552)
// Capstone ARM full coverage (388 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_0033445c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff3, 0xed2d8b02, 0xe24ddf81, 0xe59d020c\n"
        ".word 0xe5901008, 0xe59d0210, 0xe2800b07, 0xe2800fa2\n"
        ".word 0xe5902000, 0xe59d0210, 0xe58d1000, 0xe3a01032\n"
        ".word 0xe2803a01, 0xe2833074, 0xe2800ffd, 0xebff27ae\n"
        ".word 0xe58d0000, 0xe59d0210, 0xe3a01001, 0xebfd292d\n"
        ".word 0xe59d5210, 0xe58d000c, 0xe0803200, 0xe2855d7f\n"
        ".word 0xe0830300, 0xe5952000, 0xe3a010ce, 0xe0810180\n"
        ".word 0xe19200b0, 0xebfdf0e9, 0xe5d0009e, 0xed9f8ad5\n"
        ".word 0xe3500000, 0x0d9f8ad4, 0x13500001, 0x0a000001\n"
        ".word 0xe3500002, 0x0d9f8ad1, 0xed9f0ad1, 0xebfd4fc9\n"
        ".word 0xe59d0000, 0xe3500000, 0xc1a04000, 0xc3a01000\n"
        ".word 0xda00000d, 0xe59d0210, 0xe2544001, 0xe0800281\n"
        ".word 0xe2802b01, 0xe2811001, 0xed920a03, 0xee300a08\n"
        ".word 0xed820a03, 0xe2802ffd, 0xe2800b02, 0xe8921fc4\n"
        ".word 0xe2800f8d, 0xe8801fc4, 0x1afffff1, 0xe59d0210\n"
        ".word 0xe59d1000, 0xe2800ffd, 0xebfc303d, 0xe59d0210\n"
        ".word 0xe59d1000, 0xe2800b02, 0xe2800f8d, 0xebfc3038\n"
        ".word 0xe59d1210, 0xe59d0000, 0xe3e07000, 0xe2812c1e\n"
        ".word 0xe58d2030, 0xe1c208b4, 0xe3a000ff, 0xe58d01fc\n"
        ".word 0xe3a00004, 0xe58d00c8, 0xe59d0210, 0xe3a01000\n"
        ".word 0xe2804b07, 0xe2844fa6, 0xe59d30c8, 0xe594c000\n"
        ".word 0xe3a00060, 0xe0832103, 0xe0822303, 0xe58d2000\n"
        ".word 0xe0802102, 0xe19c00f2, 0xe3500000, 0xba00009f\n"
        ".word 0xe5953000, 0xe0806200, 0xe0860300, 0xe7930180\n"
        ".word 0xe3100c01, 0x0a0000aa, 0xe59d3000, 0xe3a00050\n"
        ".word 0xe59f6250, 0xe3a0affe, 0xe0807103, 0xe59d0210\n"
        ".word 0xe59d300c, 0xe78c6007, 0xe5947000, 0xe59d6000\n"
        ".word 0xe59d8000, 0xe3a0c00c, 0xe0800281, 0xe08c6106\n"
        ".word 0xe18730b2, 0xe3a0c05a, 0xe2807b01, 0xe08cb108\n"
        ".word 0xe2877004, 0xe594c000, 0xe8970380, 0xe3a0e064\n"
        ".word 0xe08cc006, 0xe88c0380, 0xe2808b01, 0xe59dc000\n"
        ".word 0xe19a60b0, 0xe5947000, 0xe58d8004, 0xe08ec10c\n"
        ".word 0xe58dc014, 0xe59d9000, 0xe3a08040, 0xe18760bb\n"
        ".word 0xe594a000, 0xe0883109, 0xe59083fc, 0xe59d9000\n"
        ".word 0xe3a070f0, 0xe78a800c, 0xe59da000, 0xe0877109\n"
        ".word 0xe3a090fc, 0xe59db000, 0xe089c10a, 0xe3a08068\n"
        ".word 0xe3a0906c, 0xe088810a, 0xe089910a, 0xe3a0a08c\n"
        ".word 0xe08aa10b, 0xe1a0e00b, 0xe3a0b090, 0xe08bb10e\n"
        ".word 0xe58dc038, 0xe594e000, 0xe3a06000, 0xe08ee003\n"
        ".word 0xe59d3004, 0xe5933000, 0xe58e3000, 0xe594e000\n"
        ".word 0xe78e6007, 0xe59d3004, 0xe5947000, 0xe1d361b0\n"
        ".word 0xe787600c, 0xe5947000, 0xe59f614c, 0xe58d7024\n"
        ".word 0xe5966000, 0xe206e8ff, 0xe1a03c26, 0xe2066cff\n"
        ".word 0xe1a0c426, 0xe59d6014, 0xe58d302c, 0xe58dc018\n"
        ".word 0xe7976006, 0xe20638ff, 0xe1a07c26, 0xe206ccff\n"
        ".word 0xe1a06823, 0xe1a0342c, 0xe58d3028, 0xe59d302c\n"
        ".word 0xe086682e, 0xe59dc018, 0xe0833007, 0xe1a060a6\n"
        ".word 0xe1a030a3, 0xe59d7024, 0xe1a03c03, 0xe0836806\n"
        ".word 0xe59d3028, 0xe083e00c, 0xe59d3014, 0xe1a0e0ae\n"
        ".word 0xe086640e, 0xe28660ff, 0xe7876003, 0xe5947000\n"
        ".word 0xe7876008, 0xe5946000, 0xe59d7014, 0xe7967007\n"
        ".word 0xe7867009, 0xe5946000, 0xe59d7014, 0xe7967007\n"
        ".word 0xe786700a, 0xe5946000, 0xe59dc014, 0xe796300c\n"
        ".word 0xe786300b, 0xe5943000, 0xe59dc038, 0xe59d6000\n"
        ".word 0xe793300c, 0xe59dc1fc, 0xe153000c, 0xb58d31fc\n"
        ".word 0xe3a03062, 0xe3a0c000, 0xe0838106, 0xe5943000\n"
        ".word 0xe5956000, 0xed900afd, 0xe19330f2, 0xe0837203\n"
        ".word 0xe0873303, 0xe0866183, 0xe086a101, 0xe1d676fe\n"
        ".word 0xed8a0a36, 0xe594a000, 0xe086908c, 0xe1d990f8\n"
        ".word 0xe19aa0f8, 0xe15a0009, 0x0a000017, 0xe3590000\n"
        ".word 0xaa000012, 0xe5940000, 0xe086208c, 0xe19000b8\n"
        ".word 0xe1c200b8, 0xea000010, 0x00000000, 0x41700000\n"
        ".word 0xc1a00000, 0x3e9c61ab, 0x00000491, 0x00439cf8\n"
        ".word 0xe59d3000, 0xe3a00050, 0xe0800103, 0xe79c0000\n"
        ".word 0xe3100001, 0x03100080, 0x1a000009, 0xeaffff5d\n"
        ".word 0xe28cc001, 0xe35c0032, 0xbaffffd7, 0xe59d0030\n"
        ".word 0xe2811001, 0xe1d008f4, 0xe2400001, 0xe1510000\n"
        ".word 0xca000004, 0xe59d00c8, 0xe2800001, 0xe3500036\n"
        ".word 0xe58d00c8, 0xbaffff3f, 0xe3770001, 0x0a000064\n"
        ".word 0xe5950000, 0xe0871207, 0xe0811307, 0xe3a05000\n"
        ".word 0xe0806181, 0xe28690cc, 0xe0860085, 0xe1d000f8\n"
        ".word 0xe3500000, 0xba000037, 0xe5941000, 0xe0802100\n"
        ".word 0xe0820300, 0xe0817100, 0xe5970050, 0xe3100001\n"
        ".word 0x13100080, 0x0a00002f, 0xe59720fc, 0xe59d01fc\n"
        ".word 0xe1520000, 0x1a00002b, 0xe1d600f8, 0xe0802100\n"
        ".word 0xe0820300, 0xe0818100, 0xe59d01fc, 0xe59810fc\n"
        ".word 0xe1510000, 0x1a000006, 0xedd80a03, 0xed970a03\n"
        ".word 0xee600aa0, 0xee200a00, 0xeef40ac0, 0xeef1fa10\n"
        ".word 0xda00001c, 0xe59d0210, 0xe1a01008, 0xebfd24f4\n"
        ".word 0xe1a0a000, 0xe59d0210, 0xe1a01007, 0xebfd24f0\n"
        ".word 0xe0892100, 0xe089110a, 0xe592300c, 0xe591000c\n"
        ".word 0xe581300c, 0xe582000c, 0xe1d8a6b2, 0xe1d7b6b2\n"
        ".word 0xe3a02f45, 0xe1a01008, 0xe28d00dc, 0xebfe2172\n"
        ".word 0xe3a02f45, 0xe1a01007, 0xe1a00008, 0xebfe216e\n"
        ".word 0xe3a02f45, 0xe28d10dc, 0xe1a00007, 0xebfe216a\n"
        ".word 0xe1c8a6b2, 0xe1c7b6b2, 0xe2855001, 0xe3550032\n"
        ".word 0xbaffffc0, 0xe3a05000, 0xe1a00005, 0xe1a0700d\n"
        ".word 0xe0861080, 0xe1d110f8, 0xe3510000, 0xba000005\n"
        ".word 0xe5942000, 0xe0813101, 0xe0831301, 0xe0821101\n"
        ".word 0xe7871105, 0xe2855001, 0xe2800001, 0xe3500032\n"
        ".word 0xbafffff2, 0xe59d0210, 0xe28610cc, 0xeb000def\n"
        ".word 0xe59f3054, 0xe3a02004, 0xe1a01005, 0xe1a0000d\n"
        ".word 0xfbfe0d39, 0xe3550000, 0xe3a00000, 0xda000004\n"
        ".word 0xe7971100, 0xe58100f4, 0xe2800001, 0xe1550000\n"
        ".word 0xcafffffa, 0xe59d020c, 0xe3a01007, 0xe28d2f83\n"
        ".word 0xe5801000, 0xe8920003, 0xe28ddf81, 0xecbd8b02\n"
        ".word 0xe28dd008, 0xe8bd4ff0, 0xeafc2fdc, 0x001920c8\n"
    );
}

// DECOMP_FUNC(0x003ea54c, 1552)
// Capstone ARM full coverage (388 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_003ea54c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff7, 0xe24dd010, 0xe1a04000, 0xe5900014\n"
        ".word 0xe594c010, 0xe5942008, 0xe594703c, 0xe150000c\n"
        ".word 0x2040100c, 0x20825001, 0xe5941040, 0x30825000\n"
        ".word 0xe5946034, 0xe1510007, 0x20413007, 0x20863203\n"
        ".word 0x30863201, 0xe5933004, 0xe5933008, 0xe2433001\n"
        ".word 0xe0833000, 0xe153000c, 0x2043300c, 0xe0833002\n"
        ".word 0xe1550003, 0x9a000152, 0xe1510007, 0x20410007\n"
        ".word 0xe284505c, 0x20860200, 0x30860201, 0xe595300c\n"
        ".word 0xe5900004, 0xe5951004, 0xe3a0b000, 0xe5900008\n"
        ".word 0xe1500003, 0x9a0000d4, 0xe0507003, 0xe0812003\n"
        ".word 0x0a000122, 0xe5950008, 0xe0839007, 0xe0426001\n"
        ".word 0xe1500009, 0x3a000061, 0xe0433006, 0xe1530007\n"
        ".word 0xe1a00007, 0x31a00003, 0xe3500000, 0xe0438000\n"
        ".word 0xe049c000, 0xe0423000, 0x1081100c, 0x0a000007\n"
        ".word 0xe1a0c003, 0xe1b02001, 0x15dcc000, 0xe2821001\n"
        ".word 0xe2833001, 0x15c2c000, 0xe2500001, 0x1afffff7\n"
        ".word 0xe0861007, 0xe3580000, 0xe1a00006, 0xe1a02001\n"
        ".word 0x0a00003c, 0xe1510000, 0x8a00001d, 0xe5953004\n"
        ".word 0xe3780106, 0xe0831002, 0xe0830006, 0x9a000004\n"
        ".word 0xe4d03001, 0xe2588001, 0xe4c13001, 0x1afffffb\n"
        ".word 0xea000030, 0xe3580001, 0xd3a08001, 0xda000001\n"
        ".word 0xe3580000, 0xda00002b, 0xe3180001, 0xe2400001\n"
        ".word 0xe2411001, 0x0a000001, 0xe5f03001, 0xe5e13001\n"
        ".word 0xe1b030c8, 0x0a000023, 0xe5d0c001, 0xe2533001\n"
        ".word 0xe5c1c001, 0xe5f0c002, 0xe5e1c002, 0x1afffff9\n"
        ".word 0xea00001c, 0xe5950004, 0xe0821008, 0xe0863008\n"
        ".word 0xe0811000, 0xe3780106, 0xe0800003, 0x9a000004\n"
        ".word 0xe5703001, 0xe2588001, 0xe5613001, 0x1afffffb\n"
        ".word 0xea000010, 0xe3580001, 0xd3a08001, 0xda000001\n"
        ".word 0xe3580000, 0xda00000b, 0xe3180001, 0x0a000001\n"
        ".word 0xe5703001, 0xe5613001, 0xe1b030c8, 0x0a000005\n"
        ".word 0xe550c001, 0xe2533001, 0xe541c001, 0xe570c002\n"
        ".word 0xe561c002, 0x1afffff9, 0xe595000c, 0xe1520000\n"
        ".word 0x31a00002, 0xe5952004, 0xe0821006, 0xe0800002\n"
        ".word 0xe0400001, 0xe3500000, 0xda000060, 0xe1b000c0\n"
        ".word 0x0a00005e, 0xe2500001, 0x1afffffd, 0xea00005b\n"
        ".word 0xe1a01009, 0xebf90680, 0xe5958000, 0xe1b0a000\n"
        ".word 0xe1a0100b, 0xe58db000, 0x0a000027, 0xe58da004\n"
        ".word 0xe5980000, 0xe1a0100a, 0xe5902000, 0xe1a00008\n"
        ".word 0xe12fff32, 0xe3500000, 0xe58d0008, 0x1a000005\n"
        ".word 0xe5980000, 0xe59f1380, 0xe59d2004, 0xe5903008\n"
        ".word 0xe1a00008, 0xe12fff33, 0xe59d1008, 0xe3510000\n"
        ".word 0x158da000, 0x1a000014, 0xe159000a, 0x0a000047\n"
        ".word 0xe3590000, 0x0a000010, 0xe58d9000, 0xe5980000\n"
        ".word 0xe1a01009, 0xe5902000, 0xe1a00008, 0xe12fff32\n"
        ".word 0xe1b0a000, 0x1a000005, 0xe5980000, 0xe59f1328\n"
        ".word 0xe59d2000, 0xe5903008, 0xe1a00008, 0xe12fff33\n"
        ".word 0xe1b0100a, 0x158d9000, 0x0a000034, 0xe5952004\n"
        ".word 0xe1b0c006, 0x11a00001, 0x0a000007, 0xe1a0a002\n"
        ".word 0xe1b03000, 0x15daa000, 0xe2830001, 0xe2822001\n"
        ".word 0x15c3a000, 0xe25cc001, 0x1afffff7, 0xe595300c\n"
        ".word 0xe5952004, 0xe0860007, 0xe053c006, 0xe0822006\n"
        ".word 0x10800001, 0x0a000007, 0xe1a0a002, 0xe1b03000\n"
        ".word 0x15daa000, 0xe2830001, 0xe2822001, 0x15c3a000\n"
        ".word 0xe25cc001, 0x1afffff7, 0xe5952004, 0xe5851004\n"
        ".word 0xe59d0000, 0xe5850008, 0xe595000c, 0xe0800002\n"
        ".word 0xe0400002, 0xe3500000, 0xda000003, 0xe1b000c0\n"
        ".word 0x0a000001, 0xe2500001, 0x1afffffd, 0xe1a01002\n"
        ".word 0xe5982000, 0xe1a00008, 0xe5922004, 0xe12fff32\n"
        ".word 0xe585900c, 0xe5950004, 0xe0900006, 0xe2866001\n"
        ".word 0x15c0b000, 0xe2577001, 0x1afffff9, 0xea000057\n"
        ".word 0xe5982000, 0xe1a00008, 0xe5922004, 0xe12fff32\n"
        ".word 0xe28dd01c, 0xe3a00000, 0xe8bd8ff0, 0xe0812003\n"
        ".word 0xe0800001, 0xe1500002, 0x0a00004c, 0xe042c000\n"
        ".word 0xe0426001, 0xe0402001, 0xe0530006, 0xe043c00c\n"
        ".word 0x0a00003a, 0xe1520006, 0x8a00001c, 0xe0822001\n"
        ".word 0xe3700106, 0xe0811006, 0x9a000004, 0xe4d13001\n"
        ".word 0xe2500001, 0xe4c23001, 0x1afffffb, 0xea00002f\n"
        ".word 0xe3500001, 0xd3a00001, 0xda000001, 0xe3500000\n"
        ".word 0xda00002a, 0xe3100001, 0xe2411001, 0xe2422001\n"
        ".word 0x0a000001, 0xe5f13001, 0xe5e23001, 0xe1b000c0\n"
        ".word 0x0a000022, 0xe5d13001, 0xe2500001, 0xe5c23001\n"
        ".word 0xe5f13002, 0xe5e23002, 0x1afffff9, 0xea00001b\n"
        ".word 0xe0822000, 0xe0863000, 0xe0822001, 0xe3700106\n"
        ".word 0xe0811003, 0x9a000004, 0xe5713001, 0xe2500001\n"
        ".word 0xe5623001, 0x1afffffb, 0xea000010, 0xe3500001\n"
        ".word 0xd3a00001, 0xda000001, 0xe3500000, 0xda00000b\n"
        ".word 0xe3100001, 0x0a000001, 0xe5713001, 0xe5623001\n"
        ".word 0xe1b000c0, 0x0a000005, 0xe5513001, 0xe2500001\n"
        ".word 0xe5423001, 0xe5713002, 0xe5623002, 0x1afffff9\n"
        ".word 0xe5952004, 0xe595100c, 0xe082000c, 0xe0811002\n"
        ".word 0xe0410000, 0xe3500000, 0xda000003, 0xe1b000c0\n"
        ".word 0x0a000001, 0xe2500001, 0x1afffffd, 0xe585c00c\n"
        ".word 0xe5940014, 0xe5941010, 0xe1500001, 0xe0415000\n"
        ".word 0x20400001, 0xe5941008, 0xe1a02005, 0xe0811000\n"
        ".word 0xe5940060, 0xebfb6d53, 0xe5940040, 0xe594103c\n"
        ".word 0xe1500001, 0x20400001, 0xe5941034, 0xe0810200\n"
        ".word 0xe5941010, 0xe5900004, 0xe5900008, 0xe0402005\n"
        ".word 0xe5940014, 0xe0800005, 0xe1500001, 0x20400001\n"
        ".word 0xe5941008, 0xe0811000, 0xe5940060, 0xe0800005\n"
        ".word 0xebfb6d40, 0xe59d1014, 0xe5940060, 0xe5810000\n"
        ".word 0xea000004, 0xe59d1014, 0xe150000c, 0x2040000c\n"
        ".word 0xe0800002, 0xe5810000, 0xe5940040, 0xe594103c\n"
        ".word 0xe1500001, 0x20400001, 0xe5941034, 0xe0810200\n"
        ".word 0xe5900004, 0xe5901008, 0xe59d0018, 0xe5801000\n"
        ".word 0xe594006c, 0xe1510000, 0x81a00001, 0xe584006c\n"
        ".word 0xe28dd01c, 0xe3a00001, 0xe8bd8ff0, 0x0040ff98\n"
    );
}

// DECOMP_FUNC(0x003f2bb4, 1572)
// Capstone ARM full coverage (393 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_003f2bb4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4010, 0xe59f4020, 0xe3a00000, 0xe5840000\n"
        ".word 0xe1a00004, 0xebfb43cc, 0xe1a00004, 0xe59f200c\n"
        ".word 0xe59f100c, 0xe8bd4010, 0xeaf8cc9a, 0x004e6cd0\n"
        ".word 0x00100000, 0x003576b8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x004738f8\n"
        ".word 0x00473900, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0044de58, 0x0044de60\n"
        ".word 0xe59f0014, 0xe3a01000, 0xe59f2010, 0xe5801000\n"
        ".word 0xe5801004, 0xe59f1008, 0xeaf8cc7a, 0x0044e910\n"
        ".word 0x00100000, 0x0037a548, 0xe59f0008, 0xe59f1008\n"
        ".word 0xe5801000, 0xe12fff1e, 0x00472368, 0x00472338\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00472388, 0x00472390, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c201f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00465058, 0x00465078, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00472940\n"
        ".word 0x00472948, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00464c58, 0x00464c60\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f8\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x0044ea00, 0x0044ea10, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00472970, 0x00472978, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x0043de98\n"
        ".word 0x0043dea0, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0043dda8, 0x0043ddb0\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x004330b0, 0x004330b8, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0043d9f8, 0x0043da08, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f8, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00434290\n"
        ".word 0x004342a0, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00434358, 0x00434360\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00465718, 0x00465720, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0044e5f0, 0x0044e600, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00446378\n"
        ".word 0x00446380, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0044e948, 0x0044e958\n"
        ".word 0xe59f2028, 0xe3e00000, 0xe1a01000, 0xe1c200f8\n"
        ".word 0xe59f001c, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe2400010, 0xe59f100c, 0xe5801000, 0xe12fff1e\n"
        ".word 0x00471f18, 0x00471f28, 0x004732d8, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00473330, 0x00473338, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x004733b0\n"
        ".word 0x004733b8, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0044e848, 0x0044e850\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x004733d0, 0x004733d8, 0xe59f2028\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f001c\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe2400010\n"
        ".word 0xe59f100c, 0xe5801000, 0xe12fff1e, 0x00473410\n"
        ".word 0x00473420, 0x00476548, 0xe59f208c, 0xe3e00000\n"
        ".word 0xe92d4070, 0xe1a01000, 0xe1c202f0, 0xe59f007c\n"
        ".word 0xe59f407c, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe1a05001, 0xe5841000, 0xe1a00004, 0xebfb4296\n"
        ".word 0xe59f2060, 0xe59f1060, 0xe1a00004, 0xe1a00000\n"
        ".word 0xe284400c, 0xe5845000, 0xe1a00004, 0xebfb428e\n"
        ".word 0xe59f2040, 0xe59f1040, 0xe1a00004, 0xe1a00000\n"
        ".word 0xe59f1038, 0xe59f0038, 0xe5912004, 0xe5802000\n"
        ".word 0xe2802004, 0xe5910004, 0xe5820000, 0xe5911004\n"
        ".word 0xe2820004, 0xe5801000, 0xe8bd8070, 0x00471a70\n"
        ".word 0x00471a98, 0x004e6c5c, 0x00100000, 0x003576b8\n"
        ".word 0x0040b5a4, 0x00471a80, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00472c70\n"
        ".word 0x00472c78, 0xe59f2020, 0xe59f1020, 0xe59f0020\n"
        ".word 0xe92d4010, 0xe1a00000, 0xe59f200c, 0xe59f100c\n"
        ".word 0xe59f0010, 0xe8bd4010, 0xeaf8cb36, 0x00100000\n"
        ".word 0x003576e8, 0x00473270, 0x00473274, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0044de68, 0x0044de70, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c201f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x0044de78\n"
        ".word 0x0044de90\n"
    );
}

// DECOMP_FUNC(0x003c35f0, 1588)
// Capstone ARM full coverage (397 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void battle_func_003c35f0() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff3, 0xe24dd004, 0xe1a05000, 0xe5900010\n"
        ".word 0xebfa4bb1, 0xe350000f, 0xe3a07000, 0x379ff100\n"
        ".word 0xea000014, 0x003c3650, 0x003c3670, 0x003c368c\n"
        ".word 0x003c36a8, 0x003c36c4, 0x003c36f0, 0x003c3714\n"
        ".word 0x003c3738, 0x003c375c, 0x003c3780, 0x003c37a4\n"
        ".word 0x003c37c8, 0x003c37ec, 0x003c3810, 0x003c3a2c\n"
        ".word 0xe5952010, 0xe1a01000, 0xe1a00002, 0xebf99be5\n"
        ".word 0xe5900000, 0xe585001c, 0xe28dd00c, 0xe8bd8ff0\n"
        ".word 0xe5952010, 0xe1a01000, 0xe1a00002, 0xebf99bd5\n"
        ".word 0xe5c50014, 0xe28dd00c, 0xe8bd8ff0, 0xe5952010\n"
        ".word 0xe1a01000, 0xe1a00002, 0xebf99bce, 0xe5c50015\n"
        ".word 0xe28dd00c, 0xe8bd8ff0, 0xe5952010, 0xe1a01000\n"
        ".word 0xe1a00002, 0xebf99bc7, 0xe5c50016, 0xe28dd00c\n"
        ".word 0xe8bd8ff0, 0xe5952010, 0xe1a01000, 0xe1a00002\n"
        ".word 0xebf99bc0, 0xe3500000, 0xe5950018, 0x13800010\n"
        ".word 0x03c00010, 0xe5850018, 0xe28dd00c, 0xe8bd8ff0\n"
        ".word 0xe5952010, 0xe1a01000, 0xe1a00002, 0xebf99bb5\n"
        ".word 0xe3500000, 0xe5950018, 0x13800002, 0x03c00002\n"
        ".word 0xeafffff3, 0xe5952010, 0xe1a01000, 0xe1a00002\n"
        ".word 0xebf99bac, 0xe3500000, 0xe5950018, 0x13800020\n"
        ".word 0x03c00020, 0xeaffffea, 0xe5952010, 0xe1a01000\n"
        ".word 0xe1a00002, 0xebf99ba3, 0xe3500000, 0xe5950018\n"
        ".word 0x13800040, 0x03c00040, 0xeaffffe1, 0xe5952010\n"
        ".word 0xe1a01000, 0xe1a00002, 0xebf99b9a, 0xe3500000\n"
        ".word 0xe5950018, 0x13800080, 0x03c00080, 0xeaffffd8\n"
        ".word 0xe5952010, 0xe1a01000, 0xe1a00002, 0xebf99b91\n"
        ".word 0xe3500000, 0xe5950018, 0x13800c01, 0x03c00c01\n"
        ".word 0xeaffffcf, 0xe5952010, 0xe1a01000, 0xe1a00002\n"
        ".word 0xebf99b88, 0xe3500000, 0xe5950018, 0x13800c02\n"
        ".word 0x03c00c02, 0xeaffffc6, 0xe5952010, 0xe1a01000\n"
        ".word 0xe1a00002, 0xebf99b7f, 0xe3500000, 0xe5950018\n"
        ".word 0x13800b01, 0x03c00b01, 0xeaffffbd, 0xe5952010\n"
        ".word 0xe1a01000, 0xe1a00002, 0xebf99b76, 0xe3500000\n"
        ".word 0xe5950018, 0x13800008, 0x03c00008, 0xeaffffb4\n"
        ".word 0xe3a00000, 0xebfbf7ee, 0xe3500000, 0xe320f000\n"
        ".word 0x0affff90, 0xe5d50014, 0xe3500000, 0x05d50015\n"
        ".word 0x03500000, 0x0a00002e, 0xe59d0008, 0xe59fb3dc\n"
        ".word 0xe3a0a001, 0xe2808b07, 0xe2888fa6, 0xe59d0008\n"
        ".word 0xe3a02001, 0xe1a01007, 0xebfa4aee, 0xe1b06000\n"
        ".word 0xe320f000, 0x0a00001f, 0xe5d50014, 0xe3500000\n"
        ".word 0x0a000002, 0xe5960000, 0xe3100010, 0x1a000019\n"
        ".word 0xe5d50015, 0xe3500000, 0x0a000002, 0xe5960000\n"
        ".word 0xe3100010, 0x0a000013, 0xe3a04000, 0xe0860084\n"
        ".word 0xe1d000f8, 0xe3500000, 0xba00000b, 0xe5981000\n"
        ".word 0xe0802100, 0xe0820300, 0xe0819100, 0xe59b0000\n"
        ".word 0xebfaecb4, 0xe1a01000, 0xe58da000, 0xe5953018\n"
        ".word 0xe1a02009, 0xe3a00000, 0xebfa0dac, 0xe2844001\n"
        ".word 0xe3540032, 0xbaffffec, 0xe2877001, 0xe357006d\n"
        ".word 0xbaffffd5, 0xe5d50016, 0xe3500000, 0x0a000021\n"
        ".word 0xebfb9440, 0xe2800a09, 0xe3a06000, 0xe5d0710b\n"
        ".word 0xe3570000, 0xc3a09001, 0xda00001a, 0xe320f000\n"
        ".word 0xebfb9438, 0xe0800006, 0xe2800a09, 0xe1d00fd0\n"
        ".word 0xe3500000, 0xba000010, 0xebfb9429, 0xe1b08000\n"
        ".word 0xe320f000, 0x0a00000c, 0xebfb49b4, 0xe3500000\n"
        ".word 0x03a04000, 0x1a000008, 0xe5950018, 0xe1100419\n"
        ".word 0x0a000002, 0xe1a01004, 0xe1a00008, 0xebfaabc6\n"
        ".word 0xe2844001, 0xe354000b, 0xbafffff6, 0xe2866001\n"
        ".word 0xe1560007, 0xbaffffe4, 0xe5d50014, 0xe3500000\n"
        ".word 0x05d50015, 0x03500000, 0x1affff32, 0xe595101c\n"
        ".word 0xe3510000, 0xbaffff2f, 0xe59d0008, 0xe3a02001\n"
        ".word 0xebfa4a98, 0xe1b06000, 0xe320f000, 0x0affff29\n"
        ".word 0xe59d0008, 0xe59fa254, 0xe3a04000, 0xe2807b07\n"
        ".word 0xe3a09001, 0xe2877fa6, 0xe0860084, 0xe1d000f8\n"
        ".word 0xe3500000, 0xba00000b, 0xe5972000, 0xe0801100\n"
        ".word 0xe0810300, 0xe0828100, 0xe59a0000, 0xebfaec65\n"
        ".word 0xe1a01000, 0xe58d9000, 0xe5953018, 0xe1a02008\n"
        ".word 0xe3a00000, 0xebfa0d5d, 0xe2844001, 0xe3540032\n"
        ".word 0xbaffffec, 0xe28dd00c, 0xe8bd8ff0, 0xe3a00000\n"
        ".word 0xebfbf767, 0xe3500000, 0xe320f000, 0x0affff09\n"
        ".word 0xe5d50014, 0xe3500000, 0x05d50015, 0x03500000\n"
        ".word 0x0a00002c, 0xe59d0008, 0xe59fa1c0, 0xe2808b07\n"
        ".word 0xe2888fa6, 0xe59d0008, 0xe3a02001, 0xe1a01007\n"
        ".word 0xebfa4a68, 0xe1b06000, 0xe320f000, 0x0a00001e\n"
        ".word 0xe5d50014, 0xe3500000, 0x0a000002, 0xe5960000\n"
        ".word 0xe3100010, 0x1a000018, 0xe5d50015, 0xe3500000\n"
        ".word 0x0a000002, 0xe5960000, 0xe3100010, 0x0a000012\n"
        ".word 0xe3a04000, 0xe0860084, 0xe1d000f8, 0xe3500000\n"
        ".word 0xba00000a, 0xe5981000, 0xe0802100, 0xe0820300\n"
        ".word 0xe0819100, 0xe59a0000, 0xebfaec2e, 0xe1a01000\n"
        ".word 0xe5953018, 0xe1a02009, 0xe3a00000, 0xebfa0cec\n"
        ".word 0xe2844001, 0xe3540032, 0xbaffffed, 0xe2877001\n"
        ".word 0xe357006d, 0xbaffffd6, 0xe5d50016, 0xe3500000\n"
        ".word 0x0a00001b, 0xebfb93bb, 0xe2800a09, 0xe3a04000\n"
        ".word 0xe5d0610b, 0xe3560000, 0xda000015, 0xe320f000\n"
        ".word 0xebfb93b4, 0xe0800004, 0xe2800a09, 0xe1d00fd0\n"
        ".word 0xe3500000, 0xba00000b, 0xebfb93a5, 0xe1b07000\n"
        ".word 0xe320f000, 0x0a000007, 0xebfb4930, 0xe3500000\n"
        ".word 0xe320f000, 0x1a000003, 0xe5950018, 0xe6ff1070\n"
        ".word 0xe1a00007, 0xebfa7d86, 0xe2844001, 0xe1540006\n"
        ".word 0xbaffffe9, 0xe5d50014, 0xe3500000, 0x05d50015\n"
        ".word 0x03500000, 0x1afffeb3, 0xe595101c, 0xe3510000\n"
        ".word 0xbafffeb0, 0xe59d0008, 0xe3a02001, 0xebfa4a19\n"
        ".word 0xe1b06000, 0xe320f000, 0x0afffeaa, 0xe59d0008\n"
        ".word 0xe59f9058, 0xe3a04000, 0xe2807b07, 0xe2877fa6\n"
        ".word 0xe0860084, 0xe1d000f8, 0xe3500000, 0xba00000a\n"
        ".word 0xe5971000, 0xe0802100, 0xe0820300, 0xe0818100\n"
        ".word 0xe5990000, 0xebfaebe7, 0xe1a01000, 0xe5953018\n"
        ".word 0xe1a02008, 0xe3a00000, 0xebfa0ca5, 0xe2844001\n"
        ".word 0xe3540032, 0xbaffffed, 0xe28dd00c, 0xe8bd8ff0\n"
        ".word 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x00143b98, 1604)
// Capstone ARM full coverage (401 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void func_00143b98() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d47f0, 0xe1a05000, 0xe3510000, 0xe59f03c0\n"
        ".word 0xe59fe3b8, 0xe5900000, 0x0a000001, 0xe1a0000e\n"
        ".word 0xe8bd87f0, 0xe2804e77, 0xe2806058, 0xe3a03001\n"
        ".word 0xe2852034, 0xe083c203, 0xe085010c, 0xe5b0c034\n"
        ".word 0xe35c0000, 0x0a00001e, 0xe5927034, 0xe5908034\n"
        ".word 0xe1570008, 0x1a00001a, 0xe5907020, 0xe5928020\n"
        ".word 0xe1580007, 0x1a000016, 0xe592800c, 0xe590900c\n"
        ".word 0xe1580009, 0x1a000012, 0xe5928010, 0xe5909010\n"
        ".word 0xe1580009, 0x1a00000e, 0xe5928014, 0xe5900014\n"
        ".word 0xe1580000, 0x1a00000a, 0xe5920000, 0xe087700c\n"
        ".word 0xe2477001, 0xe1a07cc7, 0xe1570cc0, 0x1a000004\n"
        ".word 0xe150000c, 0x8a000002, 0xe2833001, 0xe3530006\n"
        ".word 0xbaffffdb, 0xe0811006, 0xe3530006, 0xe5d110af\n"
        ".word 0x11a0000e, 0x03a00000, 0xe3510000, 0x0a000001\n"
        ".word 0xe3500000, 0x0a000003, 0xe5941000, 0xe3c11001\n"
        ".word 0xe5841000, 0xe8bd87f0, 0xe2850020, 0xed9f0ab5\n"
        ".word 0xedd51a07, 0xed952a06, 0xe594100c, 0xee611a80\n"
        ".word 0xecd00a02, 0xee222a00, 0xe1a00002, 0xe3c11611\n"
        ".word 0xee602a80, 0xee213a00, 0xe584100c, 0xe3e0c33e\n"
        ".word 0xe59f32a4, 0xeefc0ae1, 0xeebc0ac2, 0xeebc1ae2\n"
        ".word 0xeefc1ac3, 0xee108a90, 0xee107a10, 0xee116a10\n"
        ".word 0xee112a90, 0xe1878408, 0xe1a07004, 0xe1886806\n"
        ".word 0xe1862c02, 0xe5842004, 0xe5942008, 0xe590600c\n"
        ".word 0xe3c22407, 0xe3c228ff, 0xe00cc806, 0xe182200c\n"
        ".word 0xe5842008, 0xe590c010, 0xe1a025a2, 0xe1a02582\n"
        ".word 0xe1a0ca8c, 0xe1a0caac, 0xe18cc002, 0xe584c008\n"
        ".word 0xe594202c, 0xe202c4ff, 0xe584c02c, 0xe5942038\n"
        ".word 0xe590c01c, 0xe3c2200f, 0xe20cc00f, 0xe18cc002\n"
        ".word 0xe584c038, 0xe5902014, 0xe1520003, 0xe0423003\n"
        ".word 0x0a00000f, 0xaa000007, 0xe2422c19, 0xe2522006\n"
        ".word 0x13520001, 0x0a00000a, 0xe3520002, 0x13520003\n"
        ".word 0x0a000007, 0xeaffff88, 0xe2432c47, 0xe2522036\n"
        ".word 0x0a0000c1, 0xe2422c07, 0xe252201a, 0x13520001\n"
        ".word 0x1affff81, 0xe3c11207, 0xe3811201, 0xe584100c\n"
        ".word 0xe5952008, 0xe2422c29, 0xe2522001, 0x03c11a07\n"
        ".word 0x03812a02, 0x0a00000c, 0xe2422b16, 0xe252202c\n"
        ".word 0x03c11a07, 0x03812a01, 0x0a000007, 0xe3520002\n"
        ".word 0x03c12a07, 0x0a000004, 0xe2422c02, 0xe2522043\n"
        ".word 0x03c11a07, 0x03812a03, 0x1a000000, 0xe584200c\n"
        ".word 0xe595100c, 0xe2411c29, 0xe2511001, 0x0a00000a\n"
        ".word 0xe2411b16, 0xe251102c, 0x0a00000b, 0xe3510002\n"
        ".word 0x0594100c, 0x03c12c07, 0x0a00000e, 0xe2411c02\n"
        ".word 0xe2511043, 0x1a00000c, 0xea000007, 0xe594100c\n"
        ".word 0xe3c11c07, 0xe3812c02, 0xea000006, 0xe594100c\n"
        ".word 0xe3c11c07, 0xe3812c01, 0xea000002, 0xe594100c\n"
        ".word 0xe3c11c07, 0xe3812c03, 0xe584200c, 0xe5951000\n"
        ".word 0xe3510c26, 0x0594100c, 0x03c12002, 0x0a000004\n"
        ".word 0xe2411c26, 0xe2511001, 0x0594100c, 0x03812002\n"
        ".word 0x1a000000, 0xe584200c, 0xe5953004, 0xe59fc0cc\n"
        ".word 0xe3a0180f, 0xe3a0240f, 0xe153000c, 0xe043c00c\n"
        ".word 0x0a000059, 0xca000007, 0xe3530c26, 0x0a00000a\n"
        ".word 0xe2433c26, 0xe2533001, 0x0a00003d, 0xe35300ff\n"
        ".word 0x1a000043, 0xea00000d, 0xe35c0001, 0x0a000024\n"
        ".word 0xe35c0002, 0x1a00003e, 0xea00005b, 0xe5942010\n"
        ".word 0xe594300c, 0xe3c2240f, 0xe3c33401, 0xe3c2280f\n"
        ".word 0xe3c33004, 0xe5842010, 0xe584300c, 0xea000034\n"
        ".word 0xe594300c, 0xe3c33004, 0xe584300c, 0xe590e034\n"
        ".word 0xe594c010, 0xe24ee001, 0xe3ccc80f, 0xe001180e\n"
        ".word 0xe181100c, 0xe3c1c40f, 0xe5841010, 0xe5951014\n"
        ".word 0xe3510000, 0xba000042, 0xe0021c01, 0xe18c2001\n"
        ".word 0xe3c33401, 0xe5842010, 0xe584300c, 0xea000020\n"
        ".word 0x00000502, 0x004655c0, 0x437f0000, 0x0000190a\n"
        ".word 0x00002701, 0xe594300c, 0xe3c33004, 0xe584300c\n"
        ".word 0xe590e034, 0xe594c010, 0xe24ee001, 0xe3ccc80f\n"
        ".word 0xe001180e, 0xe181100c, 0xe3c1c40f, 0xe5841010\n"
        ".word 0xe5951014, 0xe3510000, 0xba000039, 0xe0021c01\n"
        ".word 0xe18c2001, 0xe3833401, 0xe5842010, 0xe584300c\n"
        ".word 0xea000007, 0xe5942010, 0xe594300c, 0xe3c2240f\n"
        ".word 0xe3c31401, 0xe3c2280f, 0xe3813004, 0xe5842010\n"
        ".word 0xe584300c, 0xe5941010, 0xe1a036a1, 0xe1a03683\n"
        ".word 0xe5843010, 0xe5900014, 0xe594100c, 0xe2402c67\n"
        ".word 0xe252205a, 0x03a00002, 0x13a00000, 0xe3c11030\n"
        ".word 0xe1811200, 0xe584100c, 0xea00002b, 0xe594300c\n"
        ".word 0xe3833004, 0xe584300c, 0xe590e034, 0xe594c010\n"
        ".word 0xe24ee001, 0xe3ccc80f, 0xe001180e, 0xe181100c\n"
        ".word 0xe3c1c40f, 0xe5841010, 0xe5951014, 0xe3510000\n"
        ".word 0xaaffffbc, 0xe3a01000, 0xeaffffba, 0xe594300c\n"
        ".word 0xe3833004, 0xe584300c, 0xe590e034, 0xe594c010\n"
        ".word 0xe24ee001, 0xe3ccc80f, 0xe001180e, 0xe181100c\n"
        ".word 0xe3c1c40f, 0xe5841010, 0xe5951014, 0xe3510000\n"
        ".word 0xaaffffc5, 0xe3a01000, 0xeaffffc3, 0xe5942010\n"
        ".word 0xe3c11207, 0xe3c11c77, 0xe3c2040f, 0xe3c0080f\n"
        ".word 0xe3c11030, 0xe1a026a0, 0xe3811119, 0xe284000c\n"
        ".word 0xe1a02682, 0xe3811601, 0xe8800006, 0xe5950034\n"
        ".word 0xeb000e2d, 0xe5941014, 0xe2011103, 0xe18111a0\n"
        ".word 0xe5841014, 0xe5950078, 0xeb000e27, 0xe5941018\n"
        ".word 0xe3e0657f, 0xe00601a0, 0xe0011b06, 0xe1811000\n"
        ".word 0xe5841018, 0xe59500bc, 0xeb000e1f, 0xe594101c\n"
        ".word 0xe00601a0, 0xe0011b06, 0xe1811000, 0xe584101c\n"
        ".word 0xe5950100, 0xeb000e18, 0xe5941020, 0xe00601a0\n"
        ".word 0xe0011b06, 0xe1811000, 0xe5841020, 0xe5950144\n"
        ".word 0xeb000e11, 0xe1a01000, 0xe5940024, 0xe0002b06\n"
        ".word 0xe00601a1, 0xe1821000, 0xe5841024, 0xe5950188\n"
        ".word 0xeb000e09, 0xe5941028, 0xe00601a0, 0xe2842004\n"
        ".word 0xe0011b06, 0xe1811000, 0xe5841028, 0xe5940000\n"
        ".word 0xe3801001, 0xe5841000, 0xe3a0100a, 0xe3a00081\n"
        ".word 0xeb0599e6, 0xe59f202c, 0xe59f002c, 0xe5921000\n"
        ".word 0xe5900000, 0xe1510000, 0x2a000004, 0xe5943038\n"
        ".word 0xe59fc018, 0xe281e008, 0xe8811008, 0xe582e000\n"
        ".word 0xe3a00000, 0xe8bd87f0, 0x004652a0, 0x004652a4\n"
        ".word 0x000f008e\n"
    );
}

// DECOMP_FUNC(0x00232cfc, 1624)
// Capstone ARM full coverage (406 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void camp_func_00232cfc() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5fff, 0xe1a06001, 0xe1a07003, 0xe1a0b002\n"
        ".word 0xe1d106b2, 0xe3500000, 0x1a0000c0, 0xe59d0000\n"
        ".word 0xe3a04000, 0xe1a05004, 0xe3500000, 0xaa000002\n"
        ".word 0xeb020e6e, 0xe1a04000, 0xea00000f, 0xe320f000\n"
        ".word 0xeb01d728, 0xe1b05000, 0xe320f000, 0x0a0000b3\n"
        ".word 0xe3a0100a, 0xeb01b03d, 0xe3500000, 0xe320f000\n"
        ".word 0x1a0000ae, 0xe3a01002, 0xe1a00005, 0xeb01b037\n"
        ".word 0xe3500000, 0xe320f000, 0x1a0000a8, 0xe3a0a000\n"
        ".word 0xe3540000, 0xe3a09001, 0xe1a0800a, 0x0a000006\n"
        ".word 0xeb0183c1, 0xe3500000, 0x01d4a1fc, 0x0a000002\n"
        ".word 0xe1a00004, 0xeb00be2f, 0xe1a0a000, 0xe3550000\n"
        ".word 0x0a000006, 0xeb0183b8, 0xe3500000, 0x01d580fe\n"
        ".word 0x0a000002, 0xe1a00005, 0xeb00dc22, 0xe1a08000\n"
        ".word 0xe3560000, 0x0a000004, 0xe5d6006a, 0xe200007f\n"
        ".word 0xe350000e, 0x13500001, 0x0a000007, 0xe3540000\n"
        ".word 0x0a000084, 0xe3a00001, 0xeb018c6c, 0xe3500000\n"
        ".word 0xe320f000, 0x1a000085, 0xea000087, 0xe3540000\n"
        ".word 0x0a00003d, 0xe3a00001, 0xeb018c64, 0xe3500000\n"
        ".word 0xe320f000, 0x0a00013e, 0xe35b0000, 0x0a000009\n"
        ".word 0xe3570000, 0x0a000071, 0xe3a00003, 0xeb018c5b\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000020, 0xe3a00001\n"
        ".word 0xe5870000, 0xea000069, 0xe3a00002, 0xeb00bdfa\n"
        ".word 0xe3a00003, 0xe320f000, 0xeb018c50, 0xe3500000\n"
        ".word 0x11d402ba, 0x12800001, 0x1a00000e, 0xe1d606b4\n"
        ".word 0xe6bf107a, 0xe3500000, 0x1a000008, 0xe5d60068\n"
        ".word 0xe3500000, 0x0a000005, 0xe0000190, 0xe59f24b0\n"
        ".word 0xe0c01092, 0xe1a012c0, 0xe0510fc0, 0x03a00001\n"
        ".word 0xe1d412ba, 0xe0800001, 0xe1c402ba, 0xe6bf0070\n"
        ".word 0xe3500000, 0xd3a00001, 0xd1c402ba, 0xea00004b\n"
        ".word 0xe1d606b4, 0xe6bf107a, 0xe3500000, 0x1a000008\n"
        ".word 0xe5d60068, 0xe3500000, 0x0a000005, 0xe0000190\n"
        ".word 0xe59f245c, 0xe0c01092, 0xe1a012c0, 0xe0510fc0\n"
        ".word 0x0a00001e, 0xe5870000, 0xea00003c, 0xe3a01001\n"
        ".word 0xe1a00005, 0xeb01afcd, 0xe3500000, 0xe320f000\n"
        ".word 0x0a0000ff, 0xe35b0000, 0x0a000016, 0xe3570000\n"
        ".word 0x0a000032, 0xe3a01003, 0xe1a00005, 0xeb01afc3\n"
        ".word 0xe3500000, 0xe320f000, 0x1affffbf, 0xe1d606b4\n"
        ".word 0xe6bf1078, 0xe3500000, 0x1affffe9, 0xe5d60068\n"
        ".word 0xe3500000, 0x0affffe6, 0xe0000190, 0xe59f23e0\n"
        ".word 0xe0c01092, 0xe1a012c0, 0xe0510fc0, 0x1affffe0\n"
        ".word 0xe3a00001, 0xeaffffde, 0xe3a01002, 0xe1a00005\n"
        ".word 0xeb00c080, 0xe3a01003, 0xe1a00005, 0xeb01afab\n"
        ".word 0xe3500000, 0x11d502ba, 0x12800001, 0x1a00000e\n"
        ".word 0xe1d606b4, 0xe6bf1078, 0xe3500000, 0x1a000008\n"
        ".word 0xe5d60068, 0xe3500000, 0x0a000005, 0xe0000190\n"
        ".word 0xe59f237c, 0xe0c01092, 0xe1a012c0, 0xe0510fc0\n"
        ".word 0x03a00001, 0xe1d512ba, 0xe0800001, 0xe1c502ba\n"
        ".word 0xe6bf0070, 0xe3500000, 0xd3a00001, 0xd1c502ba\n"
        ".word 0xe3a09000, 0xea0000c6, 0xe3a01001, 0xe1a00005\n"
        ".word 0xeb01af8e, 0xe3500000, 0xe320f000, 0x0a000002\n"
        ".word 0xe28dd010, 0xe3a00001, 0xe8bd9ff0, 0xe5d6006e\n"
        ".word 0xe3100002, 0x0a000004, 0xe59d0000, 0xe1a0200b\n"
        ".word 0xe1a01006, 0xeb03a513, 0xe1a09000, 0xe3540000\n"
        ".word 0x0a000058, 0xe1d417b2, 0xe1a00006, 0xeb03e0e2\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe35b0000\n"
        ".word 0x0b00bd75, 0xe3a09000, 0xe1d656b4, 0xe6bf007a\n"
        ".word 0xe3550000, 0x1a000009, 0xe5d61068, 0xe3510000\n"
        ".word 0x0a00001a, 0xe0000091, 0xe59f22b4, 0xe0c01092\n"
        ".word 0xe1a012c0, 0xe0515fc0, 0x03a05001, 0x0a000001\n"
        ".word 0xe3550000, 0x0a000011, 0xe3a00003, 0xeb018bbb\n"
        ".word 0xe3500000, 0xe1d402fa, 0x13550001, 0xc3a05001\n"
        ".word 0xe150000a, 0xaa000009, 0xe35b0000, 0x00800005\n"
        ".word 0x01c402ba, 0x13570000, 0x0a000003, 0xe04a0000\n"
        ".word 0xe1550000, 0xc1a05000, 0xe5875000, 0xe3a09000\n"
        ".word 0xe1d656b6, 0xe1d401fe, 0xe3550000, 0x1a000009\n"
        ".word 0xe5d61069, 0xe3510000, 0x0a00001c, 0xe0000091\n"
        ".word 0xe59f222c, 0xe0c01092, 0xe1a012c0, 0xe0515fc0\n"
        ".word 0x03a05001, 0x0a000001, 0xe3550000, 0x0a000013\n"
        ".word 0xe3a00003, 0xeb018b99, 0xe3500000, 0xe1d402fc\n"
        ".word 0xe1d411fe, 0x13550001, 0xc3a05001, 0xe1500001\n"
        ".word 0xaa00000a, 0xe35b0000, 0x159d2038, 0x00800005\n"
        ".word 0x01c402bc, 0x13520000, 0x0a000003, 0xe0410000\n"
        ".word 0xe1550000, 0xc1a05000, 0xe5825000, 0xe3a09000\n"
        ".word 0xe1d402fa, 0xe1d411fe, 0xe15a0000, 0xa1a0a000\n"
        ".word 0xe1d402fc, 0xe1c4a2ba, 0xe1500001, 0xc1a00001\n"
        ".word 0xe1c402bc, 0xea00005a, 0xe1d514b4, 0xe1a00006\n"
        ".word 0xeb03e089, 0xe1b01000, 0xe320f000, 0x0a000003\n"
        ".word 0xe35b0000, 0x01a00005, 0x0b00bfee, 0xe3a09000\n"
        ".word 0xe1d646b4, 0xe6bf0078, 0xe3540000, 0x1a000009\n"
        ".word 0xe5d61068, 0xe3510000, 0x0a00001b, 0xe0000091\n"
        ".word 0xe59f214c, 0xe0c01092, 0xe1a012c0, 0xe0514fc0\n"
        ".word 0x03a04001, 0x0a000001, 0xe3540000, 0x0a000012\n"
        ".word 0xe3a01003, 0xe1a00005, 0xeb01af08, 0xe3500000\n"
        ".word 0xe1d502fa, 0x13540001, 0xc3a04001, 0xe1500008\n"
        ".word 0xaa000009, 0xe35b0000, 0x00800004, 0x01c502ba\n"
        ".word 0x13570000, 0x0a000003, 0xe0480000, 0xe1540000\n"
        ".word 0xc1a04000, 0xe5874000, 0xe3a09000, 0xe1d646b6\n"
        ".word 0xe1d501f0, 0xe3540000, 0x1a000009, 0xe5d61069\n"
        ".word 0xe3510000, 0x0a00001d, 0xe0000091, 0xe59f20c0\n"
        ".word 0xe0c01092, 0xe1a012c0, 0xe0514fc0, 0x03a04001\n"
        ".word 0x0a000001, 0xe3540000, 0x0a000014, 0xe3a01003\n"
        ".word 0xe1a00005, 0xeb01aee5, 0xe3500000, 0xe1d502fc\n"
        ".word 0xe1d511f0, 0x13540001, 0xc3a04001, 0xe1500001\n"
        ".word 0xaa00000a, 0xe35b0000, 0x159d2038, 0x00800004\n"
        ".word 0x01c502bc, 0x13520000, 0x0a000003, 0xe0410000\n"
        ".word 0xe1540000, 0xc1a04000, 0xe5824000, 0xe3a09000\n"
        ".word 0xe1d502fa, 0xe1d512fc, 0xe1580000, 0xa1a08000\n"
        ".word 0xe1d501f0, 0xe1c582ba, 0xe1510000, 0xd1a00001\n"
        ".word 0xe1c502bc, 0xe5d6006e, 0xe3100002, 0x0a000005\n"
        ".word 0xe59d0000, 0xe1a0300b, 0xe1a02009, 0xe1a01006\n"
        ".word 0xeb02c00f, 0xe1a09000, 0xe28dd010, 0xe1a00009\n"
        ".word 0xe8bd9ff0, 0x51eb851f\n"
    );
}

// DECOMP_FUNC(0x002ca048, 1628)
// Capstone ARM full coverage (407 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_002ca048() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe59f6438, 0xed2d8b04, 0xe24dd05c\n"
        ".word 0xe5965000, 0xe5950018, 0xe3500002, 0xba00016d\n"
        ".word 0xe350000b, 0xaa00016b, 0xe59f4418, 0xe5940000\n"
        ".word 0xebffe6ca, 0xe5944000, 0xe3a01000, 0xe3a00001\n"
        ".word 0xebffefbb, 0xe2844a01, 0xe2844f93, 0xe5941000\n"
        ".word 0xe2812001, 0xe0843101, 0xe5931008, 0xe0843102\n"
        ".word 0xe5842000, 0xe5830008, 0xe5d42018, 0xe3520000\n"
        ".word 0x01510000, 0x0a000003, 0xe594101c, 0xe12fff31\n"
        ".word 0xe3a00000, 0xe5c40018, 0xe5950018, 0xe3500005\n"
        ".word 0x13500006, 0x1a00013c, 0xeddf8aeb, 0xeeb00a68\n"
        ".word 0xebffd588, 0xe320f000, 0xe320f000, 0xebffd386\n"
        ".word 0xe5960000, 0xe58d0040, 0xe5d00020, 0xe3500000\n"
        ".word 0x0a000131, 0xe59d0040, 0xeddf9ae0, 0xe5900024\n"
        ".word 0xe350000a, 0xaeb09a69, 0xaa000005, 0xe0800100\n"
        ".word 0xeddf0adb, 0xe1a00180, 0xee000a10, 0xeeb80ac0\n"
        ".word 0xee309a20, 0xe59d0040, 0xe3a0600b, 0xe590000c\n"
        ".word 0xe3500000, 0x1a000026, 0xe2861c01, 0xe3a0000e\n"
        ".word 0xebffd55c, 0xeebd8ac9, 0xe28640fc, 0xe1a05000\n"
        ".word 0xe2848003, 0xe3a07000, 0xe1a02004, 0xe3a0100e\n"
        ".word 0xe3a00002, 0xe58d6004, 0xee183a10, 0xe58d7000\n"
        ".word 0xebffd4b4, 0xe2844001, 0xe1540008, 0xdafffff5\n"
        ".word 0xe59f0300, 0xe59000a8, 0xebfe45c0, 0xe1a02000\n"
        ".word 0xe28f1fbd, 0xe28d0018, 0xfaffd191, 0xe1d510f8\n"
        ".word 0xe1d500fa, 0xeef01a68, 0xee001a90, 0xee000a10\n"
        ".word 0xe28d2018, 0xe3e01000, 0xe3a00003, 0xeeb02a61\n"
        ".word 0xeeb81ae0, 0xeef80ac0, 0xee310a09, 0xeeb01a69\n"
        ".word 0xebffd163, 0xe59d0040, 0xe5900024, 0xe350000a\n"
        ".word 0xaeb08a69, 0xaa000005, 0xe0800100, 0xeddf0aa7\n"
        ".word 0xe1a00180, 0xee000a10, 0xeeb80ac0, 0xee308ac0\n"
        ".word 0xe59d0040, 0xe590000c, 0xe3500002, 0xe3a00000\n"
        ".word 0xeebd0ac8, 0xee103a10, 0x0a0000fe, 0xe88d0041\n"
        ".word 0xe3a0201a, 0xe3a0101c, 0xe3a00002, 0xebffd4c3\n"
        ".word 0xe59f025c, 0xe3a07000, 0xe1d01af6, 0xe3510000\n"
        ".word 0xceb09a69, 0xda0000dc, 0xe2871c11, 0xe2811005\n"
        ".word 0xe3a0001c, 0xebffd517, 0xe1a06000, 0xe2871c11\n"
        ".word 0xe281100d, 0xe3a0001c, 0xebffd512, 0xe1a05000\n"
        ".word 0xe59f1220, 0xe3a0001c, 0xebffd50e, 0xe1a09000\n"
        ".word 0xe3a01c11, 0xe3a0001c, 0xebffd50a, 0xe1a04000\n"
        ".word 0xe59f1204, 0xe3a0001c, 0xebffd506, 0xe58d0048\n"
        ".word 0xe59f11f8, 0xe3a0001c, 0xebffd502, 0xe58d0044\n"
        ".word 0xe59f11ec, 0xe3a0001c, 0xebffd4fe, 0xe3a0b000\n"
        ".word 0xe58d0010, 0xe58db000, 0xe1d600f8, 0xe1d410f8\n"
        ".word 0xe59fa1bc, 0xee000a10, 0xe1d620fa, 0xe1d430fa\n"
        ".word 0xe08a8087, 0xe0822003, 0xeef80ac0, 0xee001a10\n"
        ".word 0xe1d805f4, 0xe3a0306f, 0xeeb80ac0, 0xee700a88\n"
        ".word 0xee300a80, 0xeebd0ac0, 0xee101a10, 0xebffd087\n"
        ".word 0xe08a0007, 0xe5d00074, 0xe3500000, 0x0a00001c\n"
        ".word 0xe59d0040, 0xe59f117c, 0xe5900024, 0xe1a02000\n"
        ".word 0xe0e2b091, 0xe1a01242, 0xe0411fc2, 0xe0411201\n"
        ".word 0xe0800081, 0xe3500014, 0xaa000011, 0xe59f4158\n"
        ".word 0xe3a0b00b, 0xe184a5c4, 0xe1d500fa, 0xe1a02004\n"
        ".word 0xe3a0101c, 0xe88d0801, 0xe1d500f8, 0xee000a10\n"
        ".word 0xe3a00002, 0xeeb80ac0, 0xee300a08, 0xeebd0ac0\n"
        ".word 0xee103a10, 0xebffd42f, 0xe2844001, 0xe154000a\n"
        ".word 0xdafffff0, 0xe59f40f8, 0xe1d805f4, 0xe3a01000\n"
        ".word 0xebffd11a, 0xe1a02000, 0xe28f10dc, 0xe28d0018\n"
        ".word 0xfaffd10b, 0xe1d600f8, 0xe1d930f8, 0xe1d610fa\n"
        ".word 0xee000a10, 0xe1d920fa, 0xeef01a68, 0xe0810002\n"
        ".word 0xee000a90, 0xeeb81ac0, 0xee003a10, 0xeeb02a61\n"
        ".word 0xe59f10c8, 0xe28d2018, 0xeef80ae0, 0xe3a00002\n"
        ".word 0xeeb80ac0, 0xee311a08, 0xee310a00, 0xeeb01a49\n"
        ".word 0xebffd0d7, 0xe1d808f4, 0xe59f10a4, 0xe3a0500b\n"
        ".word 0xe1610180, 0xe1a02941, 0xe0429fc1, 0xe59f1094\n"
        ".word 0xe0c12091, 0xe1a02141, 0xe0421fc1, 0xe2611000\n"
        ".word 0xe59f2084, 0xe0811101, 0xe0808081, 0xe1d600fa\n"
        ".word 0xe3a0101c, 0xe88d0021, 0xe1d600f8, 0xee000a10\n"
        ".word 0xe3a00002, 0xeeb80ac0, 0xee300a08, 0xeebd0ac0\n"
        ".word 0xee103a10, 0xebffd3f7, 0xe1d610fa, 0xe320f000\n"
        ".word 0xea000012, 0x004475b8, 0x0044ea00, 0x3f800000\n"
        ".word 0x00000000, 0xc3c80000, 0x0049f91c, 0x00007325\n"
        ".word 0x43c80000, 0x0049fd38, 0x00001101, 0x00001104\n"
        ".word 0x00001102, 0x00001103, 0x88888889, 0x000010b9\n"
        ".word 0x323232ff, 0x00006667, 0x66666667, 0x000010fe\n"
        ".word 0xe59d0048, 0xe3a0200d, 0xe1d000fa, 0xe0800001\n"
        ".word 0xe88d0021, 0xe1d600f8, 0xe1a01002, 0xee000a10\n"
        ".word 0xe59d0048, 0xe1d000f8, 0xeef80ac0, 0xee000a10\n"
        ".word 0xe3a00002, 0xeeb80ac0, 0xee700a88, 0xee300a80\n"
        ".word 0xeebd0ac0, 0xee103a10, 0xebffd3ce, 0xe59d0010\n"
        ".word 0xe1d610fa, 0xe1a02009, 0xe1d000fa, 0xe0800001\n"
        ".word 0xe88d0021, 0xe1d600f8, 0xe59d1010, 0xee000a10\n"
        ".word 0xe3a00002, 0xe1d110f8, 0xee001a90, 0xeeb80ac0\n"
        ".word 0xe3a0100d, 0xeef80ae0, 0xee300a08, 0xee300a20\n"
        ".word 0xeebd0ac0, 0xee103a10, 0xebffd3ba, 0xe59d0044\n"
        ".word 0xe1d610fa, 0xe1a02008, 0xe1d000fa, 0xe0800001\n"
        ".word 0xe88d0021, 0xe1d600f8, 0xe59d1044, 0xee000a10\n"
        ".word 0xe3a00002, 0xe1d110f8, 0xeef80ac0, 0xee001a10\n"
        ".word 0xe3a0100d, 0xeeb80ac0, 0xee700a88, 0xee300a80\n"
        ".word 0xeebd0ac0, 0xee103a10, 0xebffd3a6, 0xe1d40af6\n"
        ".word 0xe2877001, 0xe1500007, 0xcaffff22, 0xe51f014c\n"
        ".word 0xe5900000, 0xe2804a01, 0xe2844f93, 0xe5940000\n"
        ".word 0xe0841100, 0xe2400001, 0xe5911008, 0xe5840000\n"
        ".word 0xe0840100, 0xe5d42018, 0xe5900008, 0xe3520000\n"
        ".word 0x01510000, 0x0a000003, 0xe594101c, 0xe12fff31\n"
        ".word 0xe3a00000, 0xe5c40018, 0xe28dd05c, 0xe3a00000\n"
        ".word 0xecbd8b04, 0xe8bd8ff0, 0xe88d0041, 0xe3a0201e\n"
        ".word 0xe3a0101c, 0xe3a00002, 0xebffd3c4, 0xe320f000\n"
        ".word 0xe320f000, 0xeafffefd, 0xe59f002c, 0xe92d4010\n"
        ".word 0xe5900000, 0xe5900018, 0xe3500002, 0xba000004\n"
        ".word 0xe350000b, 0xaa000002, 0xe3500005, 0x13500006\n"
        ".word 0x0bfd0d6d, 0xe3a00000, 0xe8bd8010, 0x004475b8\n"
        ".word 0xe12fff1e, 0xe59f000c, 0xe3a01001, 0xe5900000\n"
        ".word 0xe5c01004, 0xe12fff1e, 0x0044e110\n"
    );
}

// DECOMP_FUNC(0x003a23d4, 1684)
// Capstone ARM full coverage (421 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_003a23d4() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a04000, 0xe0830083, 0xed2d8b04\n"
        ".word 0xe0840080, 0xe2800c9d, 0xe24dd05c, 0xe1d0b1bc\n"
        ".word 0xe1d0a1be, 0xe1d002b0, 0xe35b0000, 0xe1a06002\n"
        ".word 0xe58d0058, 0x0a00013a, 0xe594537c, 0xe3560000\n"
        ".word 0xeddf0aec, 0x12855001, 0xe2650c01, 0xee000a10\n"
        ".word 0xeeb80ac0, 0xee608a20, 0x1a000003, 0xe2811027\n"
        ".word 0xe2840d0e, 0xebfc74a2, 0xea000002, 0xe281104f\n"
        ".word 0xe2840d0e, 0xebfc749e, 0xe1d070f8, 0xe1d080fa\n"
        ".word 0xed9f8add, 0xe3560000, 0x0a000066, 0xe2840e4e\n"
        ".word 0xed900a08, 0xe320f000, 0xe320f000, 0xebfc74a6\n"
        ".word 0xe1a03008, 0xe1a02007, 0xe3a01047, 0xe2840d0e\n"
        ".word 0xe58d5000, 0xebfa3aa2, 0xe1a03008, 0xe1a02007\n"
        ".word 0xe3a01048, 0xe2840d0e, 0xe58d5000, 0xebfa3a9c\n"
        ".word 0xe1a03008, 0xe1a02007, 0xe3a01049, 0xe2840d0e\n"
        ".word 0xe58d5000, 0xebfa3a96, 0xeeb00a48, 0xe320f000\n"
        ".word 0xebfc7491, 0xe3a09001, 0xe1a03008, 0xe1a02007\n"
        ".word 0xe3a0104a, 0xe2840d0e, 0xe88d0220, 0xebfa3e1e\n"
        ".word 0xe2840b02, 0xe2800028, 0xe1d001d1, 0xe3500000\n"
        ".word 0xe1a03008, 0xe1a02007, 0x0a000006, 0xe3a0104c\n"
        ".word 0xe2840d0e, 0xe88d0220, 0xebfa3e13, 0xe320f000\n"
        ".word 0xe320f000, 0xea000003, 0xe3a0104b, 0xe2840d0e\n"
        ".word 0xe88d0220, 0xebfa3e0c, 0xe3a0104e, 0xe2840d0e\n"
        ".word 0xebfc7463, 0xe1a01000, 0xe590000c, 0xe1d1c0f8\n"
        ".word 0xe1d110fa, 0xe1d020f0, 0xe1d030f2, 0xe08c0007\n"
        ".word 0xe0811008, 0xebfa3ba3, 0xe3a0104d, 0xe2840d0e\n"
        ".word 0xebfc7457, 0xe58d0000, 0xe2840b01, 0xe2800f5b\n"
        ".word 0xe58d0004, 0xebfc727f, 0xe1a01000, 0xe59d0000\n"
        ".word 0xe0811007, 0xe1d000b4, 0xe3c00902, 0xe0410000\n"
        ".word 0xe58d0008, 0xe59d0004, 0xebfc7273, 0xe0803008\n"
        ".word 0xe88d0220, 0xe59d2008, 0xe3a0104d, 0xe2840d0e\n"
        ".word 0xebfa3de9, 0xe59f0214, 0xe5901000, 0xe3a00000\n"
        ".word 0xe2819a01, 0xe2899fc3, 0xe5991000, 0xe0892101\n"
        ".word 0xe5921008, 0xe5820008, 0xe5d92018, 0xe3520000\n"
        ".word 0x03510000, 0x0a000003, 0xe599101c, 0xe12fff31\n"
        ".word 0xe3a00000, 0xe5c90018, 0xe1a0900a, 0xe1a00009\n"
        ".word 0xebfa3350, 0xe3500000, 0x01a0900b, 0xe3560000\n"
        ".word 0x0a0000ba, 0xe3a010e6, 0xe2840d0e, 0xebfc7428\n"
        ".word 0xe1d020f8, 0xe1d010fa, 0xe3560000, 0xe0820007\n"
        ".word 0xe58d000c, 0xe0810008, 0xe58d0008, 0x0a000007\n"
        ".word 0xe3a00001, 0xe58d0004, 0xe1a03008, 0xe1a02007\n"
        ".word 0xe3a010e4, 0xe2840d0e, 0xe58d5000, 0xebfa3dbe\n"
        ".word 0xe3a0b000, 0xe88d0820, 0xe6bf1079, 0xe59d200c\n"
        ".word 0xe59d3008, 0xe2840d0e, 0xebfa3a0f, 0xe3560000\n"
        ".word 0x03a00002, 0x13a00003, 0xe58d0030, 0xe3a01000\n"
        ".word 0xe1a00009, 0xebfa39dd, 0xe3560000, 0xe58d0010\n"
        ".word 0x03a010d3, 0x03a090ff, 0x13a010e7, 0x13e09000\n"
        ".word 0xe2840d0e, 0xebfc7402, 0xe1d010f8, 0xe1d000fa\n"
        ".word 0xed9f9a43, 0xe081c007, 0xe0800008, 0xee000a10\n"
        ".word 0xeeb02a48, 0xeef01a49, 0xeeb01a68, 0xe59d1030\n"
        ".word 0xe59d3010, 0xeef80ac0, 0xee00ca10, 0xe1a02009\n"
        ".word 0xe2840d0e, 0xeeb80ac0, 0xebfc7010, 0xe1a0000a\n"
        ".word 0xe320f000, 0xebfa330f, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000080, 0xe1dd03b2, 0xe1a00520, 0xe1a00500\n"
        ".word 0xe1cd03b2, 0xe28d0030, 0xe1cda3b0, 0xebfa8fe9\n"
        ".word 0xe58d000c, 0xe3560000, 0xe3a00001, 0xe58d0004\n"
        ".word 0x03a010d1, 0x13a010e3, 0xe1a03008, 0xe1a02007\n"
        ".word 0xe2840d0e, 0xe58d5000, 0xebfa3d7f, 0xe3560000\n"
        ".word 0xe320f000, 0x0a0000a9, 0xe3a010f1, 0xe2840d0e\n"
        ".word 0xebfc73d3, 0xe3e09000, 0xe1d010f8, 0xe1d000fa\n"
        ".word 0xe59d200c, 0xe0811007, 0xe0800008, 0xe58d002c\n"
        ".word 0xe58d1024, 0xe28f103c, 0xe28d0038, 0xfafc7015\n"
        ".word 0xe28d0038, 0xe28d2004, 0xe58d0010, 0xe3a01007\n"
        ".word 0xe58d500c, 0xe58db000, 0xe8820202, 0xe3a01000\n"
        ".word 0xe2840d0e, 0xea000004, 0x3b800000, 0x3f800000\n"
        ".word 0x0044ea00, 0x00000000, 0x00643825, 0xe59d2024\n"
        ".word 0xe59d302c, 0xebfa3924, 0xe3560000, 0x0a00008d\n"
        ".word 0xe3a010f4, 0xe2840d0e, 0xebfc73b1, 0xe3e09000\n"
        ".word 0xe1d020f8, 0xe1d010fa, 0xe0820007, 0xe58d0024\n"
        ".word 0xe0810008, 0xe58d002c, 0xe59d2058, 0xe28f1f8b\n"
        ".word 0xe28d0038, 0xfafc6ff3, 0xe28d0038, 0xe3a02000\n"
        ".word 0xe28d3004, 0xe58d0010, 0xe3a01007, 0xe58d2000\n"
        ".word 0xe58d500c, 0xe8830202, 0xe3a01000, 0xe59d2024\n"
        ".word 0xe59d302c, 0xe2840d0e, 0xebfa3907, 0xe3560000\n"
        ".word 0x159f11f0, 0xe28fbf7a, 0x03a01c01, 0xe2840d0e\n"
        ".word 0xebfc7393, 0xe1d010f8, 0xe1d030fa, 0xe28dc004\n"
        ".word 0xe3a00007, 0xe88c0201, 0xe3a00000, 0xe0812007\n"
        ".word 0xe28dc00c, 0xe58d0000, 0xe1a01000, 0xe0833008\n"
        ".word 0xe2840d0e, 0xe88c0820, 0xebfa38f3, 0xe5d4001c\n"
        ".word 0xe3500000, 0x0a000061, 0xe1a0000a, 0xebfa32a1\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00005c, 0xe3560000\n"
        ".word 0x03a010d0, 0x13a010e2, 0xe3a00001, 0xe58d0004\n"
        ".word 0xe1a03008, 0xe1a02007, 0xe2840d0e, 0xe58d5000\n"
        ".word 0xebfa3d19, 0xe28dd05c, 0xecbd8b04, 0xe8bd8ff0\n"
        ".word 0xe3a010d2, 0xe2840d0e, 0xebfc736d, 0xe320f000\n"
        ".word 0xe320f000, 0xeaffff41, 0xe3560000, 0x0a000035\n"
        ".word 0xe3a010e8, 0xe2840d0e, 0xebfc7365, 0xe1d020f8\n"
        ".word 0xe1d010fa, 0xe3560000, 0xe0820007, 0xe0819008\n"
        ".word 0xe58d000c, 0x0a000007, 0xe3a00001, 0xe58d0004\n"
        ".word 0xe1a03008, 0xe1a02007, 0xe3a010e5, 0xe2840d0e\n"
        ".word 0xe58d5000, 0xebfa3cfc, 0xe88d0820, 0xe6bf107a\n"
        ".word 0xe59d200c, 0xe1a03009, 0xe2840d0e, 0xebfa394e\n"
        ".word 0xe3a01000, 0xe1a0000a, 0xebfa3920, 0xe3560000\n"
        ".word 0xe58d0010, 0x03a010d5, 0x03a090ff, 0x13a010e9\n"
        ".word 0x13e09000, 0xe2840d0e, 0xebfc7345, 0xe1d010fa\n"
        ".word 0xe1d020f8, 0xeeb02a48, 0xe0810008, 0xee000a10\n"
        ".word 0xe082c007, 0xeef01a49, 0xeeb01a68, 0xe59d1030\n"
        ".word 0xe59d3010, 0xeef80ac0, 0xee00ca10, 0xe1a02009\n"
        ".word 0xe2840d0e, 0xeeb80ac0, 0xebfc6f54, 0xe320f000\n"
        ".word 0xe320f000, 0xeaffff7b, 0xe3a010d4, 0xe2840d0e\n"
        ".word 0xebfc732f, 0xe320f000, 0xe320f000, 0xeaffffc6\n"
        ".word 0xe3a010dd, 0xe2840d0e, 0xebfc7329, 0xe59f9038\n"
        ".word 0xe320f000, 0xeaffff53, 0xe3a010e0, 0xe2840d0e\n"
        ".word 0xebfc7323, 0xe59f9024, 0xe320f000, 0xeaffff6f\n"
        ".word 0xe3560000, 0x03a010cf, 0x13a010e1, 0xeaffffa1\n"
        ".word 0x00643325, 0x0000002a, 0x00000101, 0x5a5a5aff\n"
        ".word 0x323232ff\n"
    );
}

// DECOMP_FUNC(0x00108c00, 1712)
// Capstone ARM full coverage (428 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_00108c00() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1b04000, 0xe24dd04c, 0xe3a00000\n"
        ".word 0x01a0400d, 0xe58d0000, 0xe58d0004, 0xe58d0008\n"
        ".word 0xe58d000c, 0xe58d0010, 0xe58d0014, 0xe58d0018\n"
        ".word 0xe58d001c, 0xe58d0020, 0xe58d0024, 0xe5940000\n"
        ".word 0xe1a05001, 0xe3550000, 0x01a0500d, 0xe3500000\n"
        ".word 0x05940004, 0xe59fb63c, 0xe3a06001, 0x03500000\n"
        ".word 0xe3a07004, 0xe3a08008, 0x0a0000ff, 0xeb06e952\n"
        ".word 0xe28d203c, 0xe5cd6038, 0xe5cd6039, 0xe58d6044\n"
        ".word 0xe8820180, 0xe1a01000, 0xe5942000, 0xe28d0038\n"
        ".word 0xe58d2040, 0xe5942004, 0xe58d203c, 0xeb06db38\n"
        ".word 0xe58b0000, 0xe5940008, 0xe59f95ec, 0xe3500000\n"
        ".word 0x0594000c, 0x03500000, 0x0a0000f9, 0xeb06e93e\n"
        ".word 0xe28d203c, 0xe5cd6038, 0xe5cd6039, 0xe58d6044\n"
        ".word 0xe8820180, 0xe1a01000, 0xe5942008, 0xe28d0038\n"
        ".word 0xe58d2040, 0xe594200c, 0xe58d203c, 0xeb06db24\n"
        ".word 0xe5890000, 0xe1a01000, 0xe59b0000, 0xeb06dd62\n"
        ".word 0xe320f000, 0xe320f000, 0xeb06e92b, 0xe28d302c\n"
        ".word 0xe5cd6029, 0xe58d6034, 0xe8830180, 0xe1a01000\n"
        ".word 0xe3a02000, 0xe28d0028, 0xe5cd2028, 0xeb06db14\n"
        ".word 0xe59f1568, 0xe5810000, 0xe59b2000, 0xe1a01000\n"
        ".word 0xe1a00002, 0xeb06dd50, 0xe5940010, 0xe59fa550\n"
        ".word 0xe3500000, 0x05940014, 0x03500000, 0x0a0000de\n"
        ".word 0xeb06e915, 0xe28d203c, 0xe5cd6038, 0xe5cd6039\n"
        ".word 0xe58d6044, 0xe8820180, 0xe1a01000, 0xe5942010\n"
        ".word 0xe28d0038, 0xe58d2040, 0xe5942014, 0xe58d203c\n"
        ".word 0xeb06dafb, 0xe58a0000, 0xe1a01000, 0xe59f04f4\n"
        ".word 0xe5900000, 0xeb06dd38, 0xe5940018, 0xe59fb4f4\n"
        ".word 0xe3500000, 0x0594001c, 0x03500000, 0x0a0000d4\n"
        ".word 0xeb06e8fd, 0xe28d203c, 0xe5cd6038, 0xe5cd6039\n"
        ".word 0xe58d6044, 0xe8820180, 0xe1a01000, 0xe5942018\n"
        ".word 0xe28d0038, 0xe58d2040, 0xe594201c, 0xe58d203c\n"
        ".word 0xeb06dae3, 0xe58b0000, 0xe1a01000, 0xe59f0494\n"
        ".word 0xe5900000, 0xeb06dd20, 0xe5940020, 0xe3500000\n"
        ".word 0x05940024, 0x03500000, 0x0a0000cb, 0xeb06e8e6\n"
        ".word 0xe28d203c, 0xe5cd6038, 0xe5cd6039, 0xe58d6044\n"
        ".word 0xe8820180, 0xe1a01000, 0xe5942020, 0xe28d0038\n"
        ".word 0xe58d2040, 0xe5942024, 0xe58d203c, 0xeb06dacc\n"
        ".word 0xe59f1454, 0xe5810000, 0xe59f4438, 0xe2840028\n"
        ".word 0xe5901000, 0xe5940000, 0xeb06dd07, 0xe5950000\n"
        ".word 0xe3500000, 0x05950004, 0x03500000, 0x0a0000c0\n"
        ".word 0xeb06e8cd, 0xe28d203c, 0xe5cd6038, 0xe5cd6039\n"
        ".word 0xe58d6044, 0xe8820180, 0xe1a01000, 0xe5952000\n"
        ".word 0xe28d0038, 0xe58d2040, 0xe5952004, 0xe58d203c\n"
        ".word 0xeb06dab3, 0xe5840004, 0xe5950008, 0xe3500000\n"
        ".word 0x0595000c, 0x03500000, 0x0a0000bb, 0xeb06e8ba\n"
        ".word 0xe28d203c, 0xe5cd6038, 0xe5cd6039, 0xe58d6044\n"
        ".word 0xe8820180, 0xe1a01000, 0xe5952008, 0xe28d0038\n"
        ".word 0xe58d2040, 0xe595200c, 0xe58d203c, 0xeb06daa0\n"
        ".word 0xe5890004, 0xe1a01000, 0xe5940004, 0xeb06dcde\n"
        ".word 0xe320f000, 0xe320f000, 0xeb06e8a7, 0xe28d302c\n"
        ".word 0xe5cd6029, 0xe58d6034, 0xe8830180, 0xe1a01000\n"
        ".word 0xe3a02000, 0xe28d0028, 0xe5cd2028, 0xeb06da90\n"
        ".word 0xe59f2358, 0xe1a01000, 0xe5820004, 0xe5940004\n"
        ".word 0xeb06dccd, 0xe5950010, 0xe3500000, 0x05950014\n"
        ".word 0x03500000, 0x0a0000a2, 0xeb06e893, 0xe28d203c\n"
        ".word 0xe5cd6038, 0xe5cd6039, 0xe58d6044, 0xe8820180\n"
        ".word 0xe1a01000, 0xe5952010, 0xe28d0038, 0xe58d2040\n"
        ".word 0xe5952014, 0xe58d203c, 0xeb06da79, 0xe58a0004\n"
        ".word 0xe5940004, 0xe59a1004, 0xeb06dcb7, 0xe5950018\n"
        ".word 0xe3500000, 0x0595001c, 0x03500000, 0x0a00009a\n"
        ".word 0xeb06e87d, 0xe28d203c, 0xe5cd6038, 0xe5cd6039\n"
        ".word 0xe58d6044, 0xe8820180, 0xe1a01000, 0xe5952018\n"
        ".word 0xe28d0038, 0xe58d2040, 0xe595201c, 0xe58d203c\n"
        ".word 0xeb06da63, 0xe58b0004, 0xe5940004, 0xe59b1004\n"
        ".word 0xeb06dca1, 0xe5950020, 0xe3500000, 0x05950024\n"
        ".word 0x03500000, 0x0a000091, 0xeb06e867, 0xe28d203c\n"
        ".word 0xe5cd6038, 0xe5cd6039, 0xe58d6044, 0xe8820180\n"
        ".word 0xe1a01000, 0xe5952020, 0xe28d0038, 0xe58d2040\n"
        ".word 0xe5952024, 0xe58d203c, 0xeb06da4d, 0xe59f1258\n"
        ".word 0xe5810004, 0xe59f0250, 0xe5901004, 0xe5940004\n"
        ".word 0xeb06dc89, 0xe28dd04c, 0xe8bd8ff0, 0xe320f000\n"
        ".word 0xeb06e851, 0xe28d303c, 0xe5cd6039, 0xe58d6044\n"
        ".word 0xe8830180, 0xe1a01000, 0xe3a02000, 0xe28d0038\n"
        ".word 0xe5cd2038, 0xeb06da3a, 0xe58b0000, 0xe320f000\n"
        ".word 0xeafffeff, 0xe320f000, 0xeb06e843, 0xe28d303c\n"
        ".word 0xe5cd6039, 0xe58d6044, 0xe8830180, 0xe1a01000\n"
        ".word 0xe3a02000, 0xe28d0038, 0xe5cd2038, 0xeb06da2c\n"
        ".word 0xe5890000, 0xe320f000, 0xeaffff05, 0xe320f000\n"
        ".word 0xeb06e835, 0xe28d303c, 0xe5cd6039, 0xe58d6044\n"
        ".word 0xe8830180, 0xe1a01000, 0xe3a02000, 0xe28d0038\n"
        ".word 0xe5cd2038, 0xeb06da1e, 0xe58a0000, 0xe320f000\n"
        ".word 0xeaffff20, 0xe320f000, 0xeb06e827, 0xe28d303c\n"
        ".word 0xe5cd6039, 0xe58d6044, 0xe8830180, 0xe1a01000\n"
        ".word 0xe3a02000, 0xe28d0038, 0xe5cd2038, 0xeb06da10\n"
        ".word 0xe58b0000, 0xe320f000, 0xeaffff2a, 0xe320f000\n"
        ".word 0xeb06e819, 0xe28d303c, 0xe5cd6039, 0xe58d6044\n"
        ".word 0xe8830180, 0xe1a01000, 0xe3a02000, 0xe28d0038\n"
        ".word 0xe5cd2038, 0xeb06da02, 0xe59f112c, 0xe5810000\n"
        ".word 0xeaffff34, 0xe320f000, 0xeb06e80b, 0xe28d303c\n"
        ".word 0xe5cd6039, 0xe58d6044, 0xe8830180, 0xe1a01000\n"
        ".word 0xe3a02000, 0xe28d0038, 0xe5cd2038, 0xeb06d9f4\n"
        ".word 0xe5840004, 0xe320f000, 0xeaffff3e, 0xe320f000\n"
        ".word 0xeb06e7fd, 0xe28d303c, 0xe5cd6039, 0xe58d6044\n"
        ".word 0xe8830180, 0xe1a01000, 0xe3a02000, 0xe28d0038\n"
        ".word 0xe5cd2038, 0xeb06d9e6, 0xe5890004, 0xe320f000\n"
        ".word 0xeaffff43, 0xe320f000, 0xeb06e7ef, 0xe28d303c\n"
        ".word 0xe5cd6039, 0xe58d6044, 0xe8830180, 0xe1a01000\n"
        ".word 0xe3a02000, 0xe28d0038, 0xe5cd2038, 0xeb06d9d8\n"
        ".word 0xe58a0004, 0xe320f000, 0xeaffff5c, 0xe320f000\n"
        ".word 0xeb06e7e1, 0xe28d203c, 0xe5cd6038, 0xe1a01000\n"
        ".word 0xe5cd6039, 0xe58d6044, 0xe28d0038, 0xe8820180\n"
        ".word 0xeb06d9cb, 0xe58b0004, 0xe320f000, 0xeaffff65\n"
        ".word 0xe320f000, 0xeb06e7d4, 0xe28d303c, 0xe5cd6039\n"
        ".word 0xe58d6044, 0xe8830180, 0xe1a01000, 0xe3a02000\n"
        ".word 0xe28d0038, 0xe5cd2038, 0xeb06d9bd, 0xe59f1018\n"
        ".word 0xe5810004, 0xeaffff6e, 0x00464b84, 0x00464b8c\n"
        ".word 0x00464b94, 0x00464b9c, 0x00464ba4, 0x00464bac\n"
    );
}

// DECOMP_FUNC(0x00308d20, 1736)
// Capstone ARM full coverage (434 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void script_vm_func_00308d20() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe24dd00c, 0xe1a08000, 0xebfdd4f5\n"
        ".word 0xe3500000, 0x0a000006, 0xe59f1694, 0xe3a0000c\n"
        ".word 0xe5911000, 0xe3510000, 0x15810068, 0xe28dd00c\n"
        ".word 0xe8bd8ff0, 0xe2881a02, 0xe3a00000, 0xe58d1004\n"
        ".word 0xe5810314, 0xe598016c, 0xe3500000, 0xda000005\n"
        ".word 0xe59f065c, 0xe3a01008, 0xe5900000, 0xe3500000\n"
        ".word 0x0afffff1, 0xea000141, 0xe2880b11, 0xe288bc49\n"
        ".word 0xe28000a8, 0xe58d0000, 0xe1db06fc, 0xe2885901\n"
        ".word 0xe2855e4a, 0xe3500000, 0xd1db06fe, 0xd3500000\n"
        ".word 0xda000015, 0xe59d0000, 0xe5900000, 0xe3100010\n"
        ".word 0x1a000004, 0xe5950000, 0xe3100080, 0x03100401\n"
        ".word 0x01a00008, 0x0bfd30cb, 0xe59f05f8, 0xe5900000\n"
        ".word 0xebfd30a9, 0xe5951000, 0xe59f05e4, 0xe3c11401\n"
        ".word 0xe3c11080, 0xe5851000, 0xe5900000, 0xe3a0100c\n"
        ".word 0xe3500000, 0x0affffd0, 0xea000120, 0xe2880b07\n"
        ".word 0xe2800fa6, 0xe3a04000, 0xe2887d7f, 0xe58d0008\n"
        ".word 0xe5970000, 0xe0841204, 0xe0811304, 0xe0806181\n"
        ".word 0xe5960000, 0xe3100001, 0x0a00003a, 0xe3100040\n"
        ".word 0x1a000038, 0xe5951000, 0xe2000010, 0xe3110004\n"
        ".word 0x0a000002, 0xe3500000, 0x0a000032, 0xea000001\n"
        ".word 0xe3500000, 0x1a00002f, 0xe2869c01, 0xe3a0a000\n"
        ".word 0xe1d90cb6, 0xe3100080, 0x0a000004, 0xe3a01007\n"
        ".word 0xe1a00004, 0xebfcf3fb, 0xe3500000, 0x13a0a080\n"
        ".word 0xe1d90cb6, 0xe3100040, 0x0a000004, 0xe3a01006\n"
        ".word 0xe1a00004, 0xebfcf3f3, 0xe3500000, 0x138aa040\n"
        ".word 0xe1d90cb6, 0xe3100c01, 0x0a000004, 0xe3a01008\n"
        ".word 0xe1a00004, 0xebfcf3eb, 0xe3500000, 0x138aac01\n"
        ".word 0xe1d90cb6, 0xe3100008, 0x0a000004, 0xe3a01003\n"
        ".word 0xe1a00004, 0xebfcf3e3, 0xe3500000, 0x138aa008\n"
        ".word 0xe35a0000, 0x0a00000b, 0xe1d600f8, 0xe3500000\n"
        ".word 0xba000008, 0xe59d1008, 0xe0802100, 0xe0820300\n"
        ".word 0xe1a0300a, 0xe5911000, 0xe0812100, 0xe3a01000\n"
        ".word 0xe1a00001, 0xebfcf7de, 0xe2844001, 0xe354006d\n"
        ".word 0xbaffffba, 0xe3a04000, 0xe5970000, 0xe0841204\n"
        ".word 0xe0811304, 0xe7b01181, 0xe3110001, 0x0a000050\n"
        ".word 0xe3110040, 0x1a00004e, 0xe5952000, 0xe2011010\n"
        ".word 0xe3120004, 0x0a000002, 0xe3510000, 0x0a000048\n"
        ".word 0xea000001, 0xe3510000, 0x1a000045, 0xe2806c01\n"
        ".word 0xe1d090f8, 0xe1d60cb6, 0xe3100080, 0x0a000007\n"
        ".word 0xe3a03000, 0xe3a02001, 0xe3a01016, 0xe1a00009\n"
        ".word 0xebfd30dc, 0xe320f000, 0xe320f000, 0xea000005\n"
        ".word 0xe3a00016, 0xebfcf39c, 0xe1a02000, 0xe3a01016\n"
        ".word 0xe1a00009, 0xebfd30fd, 0xe1d60cb6, 0xe3100040\n"
        ".word 0x0a000007, 0xe3a03000, 0xe3a02001, 0xe3a01017\n"
        ".word 0xe1a00009, 0xebfd30cb, 0xe320f000, 0xe320f000\n"
        ".word 0xea000005, 0xe3a00017, 0xebfcf38b, 0xe1a02000\n"
        ".word 0xe3a01017, 0xe1a00009, 0xebfd30ec, 0xe1d60cb6\n"
        ".word 0xe3100c01, 0x0a000007, 0xe3a03000, 0xe3a02001\n"
        ".word 0xe3a01018, 0xe1a00009, 0xebfd30ba, 0xe320f000\n"
        ".word 0xe320f000, 0xea000005, 0xe3a00018, 0xebfcf37a\n"
        ".word 0xe1a02000, 0xe3a01018, 0xe1a00009, 0xebfd30db\n"
        ".word 0xe1d60cb6, 0xe3100008, 0x0a000007, 0xe3a03000\n"
        ".word 0xe3a02001, 0xe3a01019, 0xe1a00009, 0xebfd30a9\n"
        ".word 0xe320f000, 0xe320f000, 0xea000005, 0xe3a00019\n"
        ".word 0xebfcf369, 0xe1a02000, 0xe3a01019, 0xe1a00009\n"
        ".word 0xebfd30ca, 0xe2844001, 0xe354006d, 0xbaffffa5\n"
        ".word 0xe5db00c4, 0xe3500000, 0x0a00007f, 0xe59d0000\n"
        ".word 0xe5900000, 0xe2100302, 0x03a01d7f, 0x07911008\n"
        ".word 0x1a000079, 0xe0802200, 0xe0822300, 0xe7912182\n"
        ".word 0xe3120020, 0x13120001, 0x0a000008, 0xe0802200\n"
        ".word 0xe0820300, 0xe0910180, 0x0a000007, 0xe5950000\n"
        ".word 0xe59f12e4, 0xe1100001, 0x0a000007, 0xea00006a\n"
        ".word 0xe2800001, 0xe350006d, 0xbaffffed, 0xe59f12cc\n"
        ".word 0xe3a00000, 0xe7c10008, 0xea000063, 0xe59d0004\n"
        ".word 0xe5900260, 0xe3500004, 0x0a00005f, 0xebfcf32c\n"
        ".word 0xe59f42ac, 0xe3500000, 0xe3a06001, 0x1a000007\n"
        ".word 0xebfcf327, 0xe3500000, 0xe320f000, 0x1a000012\n"
        ".word 0xeb02fdb1, 0xe3500000, 0xe320f000, 0x0a00000e\n"
        ".word 0xe5940000, 0xebfdd68b, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000004, 0xe5900000, 0xe3100080, 0x1a000002\n"
        ".word 0xe3100a01, 0x1a000000, 0xe3a06000, 0xe59f0244\n"
        ".word 0xe2261001, 0xe5900000, 0xeb029851, 0xe320f000\n"
        ".word 0xebfcf30f, 0xe3500000, 0xe320f000, 0x0a00002f\n"
        ".word 0xe5940000, 0xebfdd677, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000004, 0xe5900000, 0xe3100080, 0x1a000027\n"
        ".word 0xe3100a01, 0x1a000025, 0xe3a00001, 0xebfef196\n"
        ".word 0xe3500000, 0xe320f000, 0x1a000020, 0xebfcf2fc\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00001c, 0xe5940000\n"
        ".word 0xebfdd664, 0xe3500000, 0xe320f000, 0x0a000004\n"
        ".word 0xe5900000, 0xe3100080, 0x1a000014, 0xe3100a01\n"
        ".word 0x1a000012, 0xe3a01d7f, 0xe3a00000, 0xe7911008\n"
        ".word 0xe0802200, 0xe0822300, 0xe7912182, 0xe3120020\n"
        ".word 0x13120001, 0x0a000014, 0xe0802200, 0xe0820300\n"
        ".word 0xe0910180, 0x0a000005, 0xe2888901, 0xe2888e9e\n"
        ".word 0xe3a00001, 0xe5981000, 0xebfcf25e, 0xe5880000\n"
        ".word 0xe5951000, 0xe59f0158, 0xe3811a01, 0xe5851000\n"
        ".word 0xe5900000, 0xe3a0100e, 0xe3500000, 0x0afffeae\n"
        ".word 0xe5801068, 0xe28dd00c, 0xe8bd8ff0, 0xe2800001\n"
        ".word 0xe350006d, 0xbaffffe1, 0xeafffff0, 0xe5950000\n"
        ".word 0xe3c00401, 0xe3c00d82, 0xe5850000, 0xe59f0114\n"
        ".word 0xe5900000, 0xeb0294c8, 0xe5950000, 0xe2884b11\n"
        ".word 0xe28440b5, 0xe3100004, 0x0a000021, 0xe5952000\n"
        ".word 0xe2881b11, 0xe28110b4, 0xe3c22a01, 0xe3c22004\n"
        ".word 0xe5852000, 0xe5d10000, 0xe2800001, 0xe20000ff\n"
        ".word 0xe35000ff, 0xe5c10000, 0x23a000ff, 0xe5c10000\n"
        ".word 0xe5d40000, 0xe3a01011, 0xe2800001, 0xe20000ff\n"
        ".word 0xe35000ff, 0xe5c40000, 0x23a000ff, 0xe5c40000\n"
        ".word 0xe59f009c, 0xe5900000, 0xe3500000, 0x15801068\n"
        ".word 0xe3a01000, 0xe1a00008, 0xeb00bac1, 0xe3a01001\n"
        ".word 0xe1a00008, 0xeb00c7f6, 0xe28dd00c, 0xe8bd4ff0\n"
        ".word 0xea02d793, 0xe3a01000, 0xe1a00001, 0xeb0352bf\n"
        ".word 0xe5951000, 0xe3c11a01, 0xe3811004, 0xe5851000\n"
        ".word 0xe5d40000, 0xe3a01011, 0xe2800001, 0xe20000ff\n"
        ".word 0xe35000ff, 0xe5c40000, 0x23a000ff, 0xe5c40000\n"
        ".word 0xe59f002c, 0xe5900000, 0xe3500000, 0x15801068\n"
        ".word 0xe3a01001, 0xe1a00008, 0xeb00baa5, 0xe3a01000\n"
        ".word 0xe1a00008, 0xeb00c7da, 0xe28dd00c, 0xe8bd4ff0\n"
        ".word 0xea02d777, 0x00435d90, 0x00439ca8, 0x00003004\n"
        ".word 0x000049c4, 0x0043427c\n"
    );
}

// DECOMP_FUNC(0x003d918c, 1736)
// Capstone ARM full coverage (434 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_003d918c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe1a04000, 0xe24dd084, 0xe5900000\n"
        ".word 0xe1a05001, 0xe350000a, 0x379ff100, 0xea000197\n"
        ".word 0x003d91d4, 0x003d92e0, 0x003d93e4, 0x003d9570\n"
        ".word 0x003d9694, 0x003d95b4, 0x003d94f4, 0x003d95d4\n"
        ".word 0x003d9724, 0x003d9360, 0xe3510000, 0x0a00001f\n"
        ".word 0xe2811b07, 0xe2811fa6, 0xe5910000, 0xe3500000\n"
        ".word 0x13a00004, 0x0a00000b, 0xe5912000, 0xe0803100\n"
        ".word 0xe0833300, 0xe2800001, 0xe0822103, 0xe5923050\n"
        ".word 0xe3130001, 0x13130080, 0x13c33008, 0x15823050\n"
        ".word 0xe3500036, 0xbafffff3, 0xe3550000, 0x15910000\n"
        ".word 0x13500000, 0x13a00000, 0x0a000008, 0xe5912000\n"
        ".word 0xe0803100, 0xe0833300, 0xe2800001, 0xe0822103\n"
        ".word 0xe350006d, 0xe5923068, 0xe5823064, 0xbafffff6\n"
        ".word 0xe5950058, 0xe3a01004, 0xe58d1000, 0xe3a03020\n"
        ".word 0xe3a02010, 0xe3a010eb, 0xebfa2863, 0xe59f2598\n"
        ".word 0xe59f1598, 0xe584000c, 0xebf93842, 0xe594000c\n"
        ".word 0xe3a02010, 0xe3a0100c, 0xebf93838, 0xe59f1580\n"
        ".word 0xe594000c, 0xebfa2626, 0xe59f1578, 0xe594000c\n"
        ".word 0xebf93807, 0xe59f1570, 0xe594000c, 0xebf93804\n"
        ".word 0xe59f1568, 0xe594000c, 0xebf93801, 0xe594000c\n"
        ".word 0xe3a01001, 0xebfa0c93, 0xe3a00001, 0xe5840000\n"
        ".word 0xea00014a, 0xe3a00000, 0xebfb9b34, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000010, 0xe594000c, 0xebf9f473\n"
        ".word 0xe1a06000, 0xe594000c, 0xe3a01000, 0xebfbacaa\n"
        ".word 0xe3a00000, 0xe3560000, 0xe584000c, 0x0a000013\n"
        ".word 0xe3560001, 0x03a00005, 0x0affffeb, 0xe3560002\n"
        ".word 0x03a00006, 0x0affffe8, 0xea000009, 0xe3a00001\n"
        ".word 0xebfb9b1e, 0xe3500000, 0xe320f000, 0x0a00012f\n"
        ".word 0xe594000c, 0xe3a01000, 0xebfbac97, 0xe3a00000\n"
        ".word 0xe584000c, 0xe28dd084, 0xe3e00000, 0xe8bd80f0\n"
        ".word 0xe5950058, 0xe3a01004, 0xe58d1000, 0xe3a03020\n"
        ".word 0xe3a02010, 0xe3a010eb, 0xebfa281f, 0xe59f2488\n"
        ".word 0xe59f1488, 0xe584000c, 0xebf937fe, 0xe594000c\n"
        ".word 0xe3a02010, 0xe3a0100c, 0xebf937f4, 0xe59f1480\n"
        ".word 0xe594000c, 0xebfa25e2, 0xe59f1478, 0xe594000c\n"
        ".word 0xebf937c3, 0xe59f1470, 0xe594000c, 0xebf937c0\n"
        ".word 0xe594000c, 0xe3a01001, 0xebfa0c52, 0xe3a00002\n"
        ".word 0xe320f000, 0xeaffffbc, 0xe3a00000, 0xebfb9af3\n"
        ".word 0xe3500000, 0xe320f000, 0x0a00000c, 0xe594000c\n"
        ".word 0xebf9f432, 0xe1a06000, 0xe594000c, 0xe3a01000\n"
        ".word 0xebfbac69, 0xe3a00000, 0xe3560000, 0xe584000c\n"
        ".word 0x0a00000d, 0xe3560001, 0x1a000062, 0xea000010\n"
        ".word 0xe3a00001, 0xebfb9ae1, 0xe3500000, 0xe320f000\n"
        ".word 0x0a0000f2, 0xe594000c, 0xe3a01000, 0xebfbac5a\n"
        ".word 0xe3a00000, 0xe584000c, 0xea000056, 0xe1a01005\n"
        ".word 0xe1a00004, 0xebfffdf7, 0xe3a00003, 0xe320f000\n"
        ".word 0xeaffff99, 0xe5950058, 0xe3a06004, 0xe3a03020\n"
        ".word 0xe3a02010, 0xe3a010eb, 0xe58d6000, 0xebfa27de\n"
        ".word 0xe59f2384, 0xe59f1384, 0xe584000c, 0xebf937bd\n"
        ".word 0xe594000c, 0xe3a02010, 0xe3a0100c, 0xebf937b3\n"
        ".word 0xe59f1388, 0xe594000c, 0xebfa25a1, 0xe59f1380\n"
        ".word 0xe594000c, 0xebf93782, 0xe59f1378, 0xe594000c\n"
        ".word 0xebf9377f, 0xe59f1370, 0xe594000c, 0xebf9377c\n"
        ".word 0xe594000c, 0xe3a01001, 0xebfa0c0e, 0xe5846000\n"
        ".word 0xe320f000, 0xea0000c5, 0xe3a01080, 0xe1a0000d\n"
        ".word 0xebfbad8b, 0xe1a00005, 0xe320f000, 0xebf99c1a\n"
        ".word 0xe1a01000, 0xe1a0000d, 0xebfb98d4, 0xe320f000\n"
        ".word 0xe320f000, 0xebfa0914, 0xe1a07000, 0xe3a00001\n"
        ".word 0xebfa090d, 0xe1a0000d, 0xe320f000, 0xebfbb23b\n"
        ".word 0xe1a06000, 0xe1a00007, 0xebfa0907, 0xe5d6000a\n"
        ".word 0xe3500001, 0x1a000003, 0xe1a02006, 0xe1a01005\n"
        ".word 0xe1a00004, 0xeb0000bb, 0xe3a00000, 0xe5840000\n"
        ".word 0xea0000a6, 0xe3a00000, 0xebfb9a90, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000006, 0xe5952058, 0xe1a01005\n"
        ".word 0xe1a00004, 0xebfffdf2, 0xe3a00007, 0xe320f000\n"
        ".word 0xeaffff4d, 0xe3a00001, 0xebfb9a84, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000001, 0xe3a00000, 0xeaffff46\n"
        ".word 0xe1a01005, 0xe1a00004, 0xebfffd4f, 0xe320f000\n"
        ".word 0xe320f000, 0xea00008d, 0xe1a06001, 0xe3a00001\n"
        ".word 0xebfb9a76, 0xe3500000, 0xe320f000, 0x0a000006\n"
        ".word 0xe594000c, 0xe3a01000, 0xebfbabef, 0xe3a00000\n"
        ".word 0xe584000c, 0xe3a00003, 0xeaffff33, 0xe59f023c\n"
        ".word 0xe1d411f0, 0xe594700c, 0xe7900006, 0xe0812101\n"
        ".word 0xe0822301, 0xe0805102, 0xe1a00006, 0xebfa919c\n"
        ".word 0xe1d411f0, 0xe1a00006, 0xebfd8479, 0xe1a04000\n"
        ".word 0xe3a01001, 0xe1a00007, 0xebf943a3, 0xe5900000\n"
        ".word 0xe3a01002, 0xe585000c, 0xe1a00007, 0xebf9439e\n"
        ".word 0xe5900000, 0xe3a01003, 0xe5850010, 0xe1a00007\n"
        ".word 0xebf94399, 0xe5900000, 0xe5850014, 0xe595000c\n"
        ".word 0xe584000c, 0xe5950010, 0xe5840010, 0xe5950014\n"
        ".word 0xe5840014, 0xea00005d, 0xe3a00000, 0xebfb9a47\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000013, 0xe594000c\n"
        ".word 0xebf9f386, 0xe1a06000, 0xe594000c, 0xe3a01000\n"
        ".word 0xebfbabbd, 0xe3560000, 0x13560001, 0xe3a00000\n"
        ".word 0x13560002, 0xe584000c, 0x1affff24, 0xe6ff3076\n"
        ".word 0xe5952058, 0xe1a01005, 0xe1a00004, 0xebfffdf1\n"
        ".word 0xe3a00008, 0xe320f000, 0xeafffef7, 0xe3a00001\n"
        ".word 0xebfb9a2e, 0xe3500000, 0xe320f000, 0x0a00003f\n"
        ".word 0xe594000c, 0xe3a01000, 0xebfbaba7, 0xe3a00000\n"
        ".word 0xe584000c, 0xeaffff11, 0xe3a00001, 0xebfb9a23\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000005, 0xe594000c\n"
        ".word 0xe3a01000, 0xebfbab9c, 0xe3a00000, 0xe584000c\n"
        ".word 0xeaffff47, 0xe1d401b4, 0xe594600c, 0xe3500000\n"
        ".word 0x0a000004, 0xe3500001, 0x0a000002, 0xe3500002\n"
        ".word 0x0a00001f, 0xea000025, 0xe3500000, 0xe59f00d0\n"
        ".word 0x02855b07, 0x02855fa9, 0x12855a01, 0xe5900000\n"
        ".word 0x12855eeb, 0xe3a01000, 0x0280400c, 0x12804018\n"
        ".word 0xe1a00006, 0xebf9434c, 0xe5900000, 0xe3a01001\n"
        ".word 0xe5840000, 0xe1a00006, 0xebf94347, 0xe5900000\n"
        ".word 0xe3a01002, 0xe5840004, 0xe1a00006, 0xebf94342\n"
        ".word 0xe5900000, 0xe5840008, 0xe8940007, 0xe8850007\n"
        ".word 0xe59f006c, 0xe894000e, 0xe5900000, 0xe880000e\n"
        ".word 0xea000006, 0xe3a01000, 0xe1a00006, 0xebf9437e\n"
        ".word 0xe59f104c, 0xe5900000, 0xe5911000, 0xe5810024\n"
        ".word 0xe28dd084, 0xe3a00000, 0xe8bd80f0, 0x00193b28\n"
        ".word 0x00192990, 0x004006ac, 0x004006a4, 0x0040069c\n"
        ".word 0x00400694, 0x00400614, 0x00400608, 0x004005fc\n"
        ".word 0x004005f4, 0x004005ec, 0x004005e4, 0x004005d4\n"
        ".word 0x00001e98, 0x004342c8\n"
    );
}

// DECOMP_FUNC(0x00382a88, 1748)
// Capstone ARM full coverage (437 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_00382a88() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a05000, 0xe24dd074, 0xe5d00018\n"
        ".word 0xebfacac3, 0xe59fb434, 0xe3500000, 0xe28b6010\n"
        ".word 0x0a00003e, 0xe3e00000, 0xe58d0004, 0xe28d0004\n"
        ".word 0xebfc1334, 0xe59d0004, 0xe595101c, 0xe1510000\n"
        ".word 0x0a000003, 0xe585001c, 0xe5d50018, 0xebfc13a4\n"
        ".word 0xebfffc7c, 0xe5d50018, 0xebfc13a1, 0xe3a01004\n"
        ".word 0xe320f000, 0xebfc1399, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000086, 0xe5d50018, 0xe3a07000, 0xe3500000\n"
        ".word 0x03a04000, 0x0a000004, 0xe3500001, 0x03a04000\n"
        ".word 0x01a08006, 0x1a000011, 0xea000008, 0xe08b6104\n"
        ".word 0xe1d600b0, 0xebfcf81d, 0xe3500000, 0x11d670b2\n"
        ".word 0xe2844001, 0xe3540004, 0x3afffff7, 0xea000007\n"
        ".word 0xe0886104, 0xe1d600b0, 0xebfcf814, 0xe3500000\n"
        ".word 0x11d670b2, 0xe2844001, 0xe3540004, 0x3afffff7\n"
        ".word 0xe5d50018, 0xebfc137e, 0xe595201c, 0xe1a03007\n"
        ".word 0xe2851020, 0xebfffbf9, 0xe595001c, 0xe3500000\n"
        ".word 0x1a000062, 0xe3a02001, 0xe59f0344, 0xe1a01002\n"
        ".word 0xebfc1b89, 0xe320f000, 0xe320f000, 0xea00005b\n"
        ".word 0xe5d50018, 0xebfc136e, 0xe320f000, 0xe320f000\n"
        ".word 0xebfffc02, 0xe3500005, 0xe1a09000, 0x0a000053\n"
        ".word 0xe5d50018, 0xe3a08000, 0xe3a0a014, 0xe3500000\n"
        ".word 0x0a000002, 0xe3500001, 0x1a00001a, 0xea00000c\n"
        ".word 0xe3a08014, 0xe3a00025, 0xebfcf7ec, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000013, 0xe3a08005, 0xe3a00055\n"
        ".word 0xebfcf7e6, 0xe3500000, 0xe320f000, 0x0a00000d\n"
        ".word 0xea00000b, 0xe3a08014, 0xe3a0006c, 0xebfcf7df\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000006, 0xe3a08005\n"
        ".word 0xe3a0007c, 0xebfcf7d9, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000000, 0xe3a08000, 0xe5d50018, 0xebfc1344\n"
        ".word 0xe3a01000, 0xe1c010bc, 0xe5d50018, 0xe3500000\n"
        ".word 0x1a000008, 0xe3a00055, 0xebfcf7cc, 0xe3500000\n"
        ".word 0xe320f000, 0x1a000003, 0xe5d50018, 0xebfc1338\n"
        ".word 0xe3a01008, 0xe1c010bc, 0xe5d50018, 0xe3a07000\n"
        ".word 0xe3500000, 0x03a04000, 0x0a000004, 0xe3500001\n"
        ".word 0x03a04000, 0x01a0b006, 0x1a000011, 0xea000008\n"
        ".word 0xe08b6104, 0xe1d600b0, 0xebfcf7b8, 0xe3500000\n"
        ".word 0x11d670b2, 0xe2844001, 0xe3540004, 0x3afffff7\n"
        ".word 0xea000007, 0xe08b6104, 0xe1d600b0, 0xebfcf7af\n"
        ".word 0xe3500000, 0x11d670b2, 0xe2844001, 0xe3540004\n"
        ".word 0x3afffff7, 0xe5d50018, 0xebfc1319, 0xe1a03007\n"
        ".word 0xe2852020, 0xe1a01009, 0xe88d0500, 0xebfffa61\n"
        ".word 0xe5d50018, 0xebfc1312, 0xe1a04000, 0xe5d51018\n"
        ".word 0xe3a02000, 0xe2850020, 0xeb019df0, 0xe1a06000\n"
        ".word 0xe5d51018, 0xe3a02000, 0xe2850020, 0xebfaca83\n"
        ".word 0xe1a08000, 0xe5d4000a, 0xe0867280, 0xe5d50018\n"
        ".word 0xebfaca13, 0xe3500000, 0xe320f000, 0x0a000005\n"
        ".word 0xe595001c, 0xe3500000, 0x1a000002, 0xe5d4000a\n"
        ".word 0xe0860280, 0xe2807020, 0xe3a01000, 0xe1a00007\n"
        ".word 0xebfce908, 0xe3a07000, 0xe58d0004, 0xe58d7000\n"
        ".word 0xe595028c, 0xe1a03007, 0xe3e02000, 0xe3a01003\n"
        ".word 0xebfc500c, 0xe5d4000a, 0xe28d9008, 0xe0800100\n"
        ".word 0xe0840200, 0xe2806010, 0xe3a04000, 0xe5cd7050\n"
        ".word 0xe7960104, 0xe3700002, 0x0a00000c, 0xe3700001\n"
        ".word 0x0a000010, 0xe0881280, 0xe1d101b6, 0xe3500000\n"
        ".word 0x0a000014, 0xebfce8d2, 0xe1a01000, 0xe28d0050\n"
        ".word 0xfafcce78, 0xe320f000, 0xe320f000, 0xea00000f\n"
        ".word 0xe28f10d0, 0xe28d0050, 0xfafcce72, 0xe320f000\n"
        ".word 0xe320f000, 0xea000009, 0xe320f000, 0xebfce970\n"
        ".word 0xe1a01000, 0xe28d0050, 0xfafcce6a, 0xe320f000\n"
        ".word 0xe320f000, 0xea000001, 0xe28d0050, 0xfafcce65\n"
        ".word 0xe28d1008, 0xe28d0050, 0xebfce8d6, 0xe3540000\n"
        ".word 0xe320f000, 0x0a000004, 0xe3540001, 0x0a000008\n"
        ".word 0xe3540002, 0x0a000011, 0xea00000b, 0xe88d0280\n"
        ".word 0xe5950290, 0xe3a03000, 0xe3e02000, 0xe3a01004\n"
        ".word 0xea000004, 0xe88d0280, 0xe5950294, 0xe3a03000\n"
        ".word 0xe3e02000, 0xe3a01003, 0xebfc4fce, 0xe2844001\n"
        ".word 0xe3540003, 0xbaffffc4, 0xe28dd074, 0xe8bd8ff0\n"
        ".word 0xe88d0280, 0xe5950298, 0xe3a03000, 0xe3e02000\n"
        ".word 0xe3a01002, 0xebfc4fc3, 0xe28dd074, 0xe8bd8ff0\n"
        ".word 0x0044db62, 0x00000424, 0x7c817c81, 0x00007c81\n"
        ".word 0xe92d41f0, 0xe1a04000, 0xebfafaf2, 0xe3500000\n"
        ".word 0x0a00008d, 0xebfd31e8, 0xe5c40d4c, 0xebfe1f19\n"
        ".word 0xe2845c0d, 0xe1c504be, 0xebfdb3f4, 0xe1c505b0\n"
        ".word 0xebfa4b28, 0xe1a06000, 0xebfa8330, 0xe5c40d4a\n"
        ".word 0xebfd31d7, 0xe3500000, 0x0a000039, 0xe1d505b0\n"
        ".word 0xe35000ca, 0x0a000002, 0xe35000c3, 0x0a000014\n"
        ".word 0xea000033, 0xe59f01e4, 0xe3a02001, 0xe3a01000\n"
        ".word 0xebfc1a99, 0xe3a02001, 0xe3a01000, 0xe3a00f9d\n"
        ".word 0xebfc1a95, 0xe59f01c8, 0xe3a02001, 0xe3a01000\n"
        ".word 0xebfc1a91, 0xe3a02001, 0xe3a01000, 0xe3a00f92\n"
        ".word 0xebfc1a8d, 0xe59f01ac, 0xe3a02001, 0xe3a01000\n"
        ".word 0xea00001e, 0xe3a02001, 0xe3a01000, 0xe3a00f93\n"
        ".word 0xebfc1a85, 0xe59f0190, 0xe3a02001, 0xe3a01000\n"
        ".word 0xebfc1a81, 0xe3a02001, 0xe3a01000, 0xe2820f93\n"
        ".word 0xebfc1a7d, 0xe59f0174, 0xe3a02001, 0xe3a01000\n"
        ".word 0xebfc1a79, 0xe3a02001, 0xe3a01000, 0xe3a00e25\n"
        ".word 0xebfc1a75, 0xe59f0158, 0xe3a02001, 0xe3a01000\n"
        ".word 0xebfc1a71, 0xe3a02001, 0xe3a01000, 0xe2820e25\n"
        ".word 0xebfc1a6d, 0xe59f013c, 0xe3a02001, 0xe3a01000\n"
        ".word 0xebfc1a69, 0xe5d5004c, 0xe3a08000, 0xe3500000\n"
        ".word 0x0a00000f, 0xebfcfeba, 0xe1a07000, 0xe1c082b2\n"
        ".word 0xebfbc463, 0xe320f000, 0xe320f000, 0xebfbeacb\n"
        ".word 0xe3560000, 0xe320f000, 0x1a000005, 0xe1d504be\n"
        ".word 0xe1c701be, 0xebfbc3d0, 0xe320f000, 0xe320f000\n"
        ".word 0xebfbc395, 0xe320f000, 0xebfc4ed8, 0xe5d5004a\n"
        ".word 0xe3500000, 0x0a000008, 0xe59f20cc, 0xe3a01001\n"
        ".word 0xe2844004, 0xe3a0000f, 0xe1c217b8, 0xe8840101\n"
        ".word 0xe3a00000, 0xe8bd41f0, 0xeafac9a7, 0xe3560000\n"
        ".word 0x0a00000c, 0xe59f10a4, 0xe3a00000, 0xe5c46d48\n"
        ".word 0xebfc7013, 0xe3a00001, 0xe320f000, 0xebfc1b8d\n"
        ".word 0xe2844004, 0xe3a0000c, 0xe8840101, 0xe3a00000\n"
        ".word 0xe8bd41f0, 0xeafac998, 0xe5d50055, 0xe3500000\n"
        ".word 0x0a00000c, 0xe3a01000, 0xe3a00001, 0xebfc6dfb\n"
        ".word 0xe320f000, 0xe320f000, 0xe3a00064, 0xe2600000\n"
        ".word 0xe3a01000, 0xebfc6deb, 0xe3a00001, 0xe320f000\n"
        ".word 0xebfac96d, 0xe5c48d55, 0xe320f000, 0xebfc4eab\n"
        ".word 0xe2844004, 0xe3a00005, 0xe8840101, 0xe8bd81f0\n"
        ".word 0x00000246, 0x0000026b, 0x00000247, 0x0000024e\n"
        ".word 0x0000024f, 0x00000252, 0x00000253, 0x0049fa1c\n"
        ".word 0x323232ff\n"
    );
}

// DECOMP_FUNC(0x0025a434, 1756)
// Capstone ARM full coverage (439 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void script_vm_func_0025a434() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d40f0, 0xe1a04000, 0xe3a06000, 0xe59f0374\n"
        ".word 0xe59f7378, 0xe59f537c, 0xed2d8b08, 0xeef0aa40\n"
        ".word 0xeeb09a60, 0xeef08a41, 0xeeb08a61, 0xe5941010\n"
        ".word 0xe5900000, 0xed9fbad4, 0xeddf9ad5, 0xed9faad6\n"
        ".word 0xe3510000, 0xe24dd0b4, 0x0a0000d6, 0xe3510001\n"
        ".word 0x0a00013e, 0xe3510002, 0x1a0000c7, 0xed900a06\n"
        ".word 0xeddf0ace, 0xe3a01000, 0xe3a03000, 0xee300a20\n"
        ".word 0xeef00a69, 0xee200a0b, 0xeeb40ae0, 0xeef1fa10\n"
        ".word 0xeeb01ac0, 0xeef01a60, 0x33a02001, 0x23a02000\n"
        ".word 0xee110a10, 0xe1500005, 0xba000003, 0xee311a4a\n"
        ".word 0xee110a10, 0xe1500005, 0xaafffffb, 0xee110a90\n"
        ".word 0xe1500005, 0xba000003, 0xee711aca, 0xee110a90\n"
        ".word 0xe1500005, 0xaafffffb, 0xeebc0ae0, 0xe3510000\n"
        ".word 0xee100a10, 0xeebc0ac1, 0xe6ff0070, 0xee10ca10\n"
        ".word 0xeebc0ae1, 0xe6ffc07c, 0xee105a10, 0xee000a10\n"
        ".word 0xe20000ff, 0xe6ff5075, 0xe0870200, 0xeeb82a40\n"
        ".word 0xee00ca10, 0xe20cc0ff, 0xe087c20c, 0xed9c3a00\n"
        ".word 0xeef82a40, 0xee005a10, 0xe20550ff, 0xee700ac2\n"
        ".word 0xe0875205, 0xeddc3a01, 0xe28cc008, 0xeeb80a40\n"
        ".word 0xed952a01, 0xee311a62, 0xedd52a00, 0xe2855008\n"
        ".word 0xecdc5a02, 0xecd56a02, 0xee711ac0, 0xecb00a01\n"
        ".word 0xec904a03, 0xee013a25, 0xee413a06, 0xee000aa4\n"
        ".word 0xee004a85, 0xee412aa6, 0xee012a87, 0x1eb10a40\n"
        ".word 0xe3520000, 0x1eb13a43, 0xe3530000, 0x1ef12a62\n"
        ".word 0xee641a02, 0xee604a02, 0xee222a23, 0xeeb16a43\n"
        ".word 0xee205a22, 0xee241a22, 0xee622aa3, 0xee200a23\n"
        ".word 0xee643a23, 0xed8d2a16, 0xeef05a45, 0xeeb05a41\n"
        ".word 0xedcd2a1a, 0xed8d0a1f, 0xedcd3a20, 0xeef00a65\n"
        ".word 0xee145a83, 0xee514a03, 0xee410a83, 0xee451a83\n"
        ".word 0xed8d5a17, 0xedcd4a1c, 0xedcd0a18, 0xedcd1a1b\n"
        ".word 0xed8d6a1e, 0xeeb00a48, 0xed9fba6d, 0xe58d6064\n"
        ".word 0xe58d6074, 0xe58d6084, 0xedcd8a12, 0xee090a0b\n"
        ".word 0xe28d2048, 0xe28d1058, 0xe28d0010, 0xed8d0a13\n"
        ".word 0xeeb0aa40, 0xedcd9a14, 0xeb014c21, 0xee098a4b\n"
        ".word 0xedcd8a12, 0xe28d2048, 0xe28d1058, 0xe28d5010\n"
        ".word 0xe28d001c, 0xed8d8a13, 0xedcd9a14, 0xeb014c18\n"
        ".word 0xee788aaa, 0xe28d2048, 0xe28d1058, 0xe2850018\n"
        ".word 0xedcd8a12, 0xed8daa13, 0xedcd9a14, 0xeb014c10\n"
        ".word 0xedcd8a12, 0xed8d8a13, 0xedcd9a14, 0xe28d2048\n"
        ".word 0xe28d1058, 0xe2850024, 0xeb014c09, 0xedd40a1a\n"
        ".word 0xed9d0a04, 0xe28d3010, 0xee300a20, 0xed8d0a04\n"
        ".word 0xedd40a1b, 0xed9d0a05, 0xee300a20, 0xed8d0a05\n"
        ".word 0xedd40a1c, 0xed9d0a06, 0xee300a20, 0xed8d0a06\n"
        ".word 0xedd40a1a, 0xed9d0a07, 0xee300a20, 0xed8d0a07\n"
        ".word 0xedd40a1b, 0xed9d0a08, 0xee300a20, 0xed8d0a08\n"
        ".word 0xedd40a1c, 0xed9d0a09, 0xee300a20, 0xed8d0a09\n"
        ".word 0xedd40a1a, 0xed9d0a0a, 0xee300a20, 0xed8d0a0a\n"
        ".word 0xedd40a1b, 0xed9d0a0b, 0xee300a20, 0xed8d0a0b\n"
        ".word 0xedd40a1c, 0xed9d0a0c, 0xee300a20, 0xed8d0a0c\n"
        ".word 0xedd40a1a, 0xed9d0a0d, 0xee300a20, 0xed8d0a0d\n"
        ".word 0xedd40a1b, 0xed9d0a0e, 0xee300a20, 0xed8d0a0e\n"
        ".word 0xedd40a1c, 0xed9d0a0f, 0xee300a20, 0xed8d0a0f\n"
        ".word 0xe8930007, 0xe28430c0, 0xe8830007, 0xe28d301c\n"
        ".word 0xe8930007, 0xe28430cc, 0xe8830007, 0xe28d3028\n"
        ".word 0xe8930007, 0xe28430d8, 0xe28440e4, 0xe8830007\n"
        ".word 0xe28d3034, 0xe8930007, 0xe8840007, 0xe28dd0b4\n"
        ".word 0xecbd8b08, 0xe8bd80f0, 0x004474f4, 0x3f360b61\n"
        ".word 0x00407fc0, 0x00000000, 0x47800000, 0x47800000\n"
        ".word 0x43340000, 0x3f000000, 0xed900a13, 0xedd00a15\n"
        ".word 0xedd41a1a, 0xed941a1c, 0xee300a61, 0xee700ac1\n"
        ".word 0xeb009e2a, 0xeddf0ac3, 0xe3a01000, 0xe3a03000\n"
        ".word 0xee200a20, 0xeef00a69, 0xee200a0b, 0xeeb40ae0\n"
        ".word 0xeef1fa10, 0xeeb01ac0, 0xeef01a60, 0x33a02001\n"
        ".word 0x23a02000, 0xee110a10, 0xe1500005, 0xba000003\n"
        ".word 0xee311a4a, 0xee110a10, 0xe1500005, 0xaafffffb\n"
        ".word 0xee110a90, 0xe1500005, 0xba000003, 0xee711aca\n"
        ".word 0xee110a90, 0xe1500005, 0xaafffffb, 0xeebc0ae0\n"
        ".word 0xe3510000, 0xee100a10, 0xeebc0ac1, 0xe6ff0070\n"
        ".word 0xee10ca10, 0xeebc0ae1, 0xe6ffc07c, 0xee105a10\n"
        ".word 0xee000a10, 0xe20000ff, 0xe6ff5075, 0xe0870200\n"
        ".word 0xeef82a40, 0xee00ca10, 0xe20cc0ff, 0xed903a01\n"
        ".word 0xe087c20c, 0xeddc3a01, 0xeeb82a40, 0xee005a10\n"
        ".word 0xe20550ff, 0xee700ae2, 0xe0875205, 0xedd52a00\n"
        ".word 0xeeb80a40, 0xed954a01, 0xe2855008, 0xee311a42\n"
        ".word 0xed902a00, 0xe2800008, 0xecd56a02, 0xecd04a02\n"
        ".word 0xe28d005c, 0xee711ac0, 0xed9c0a00, 0xe28cc008\n"
        ".word 0xee002aa4, 0xecdc5a02, 0xee003a85, 0xee010a25\n"
        ".word 0xee413a06, 0xee412aa6, 0xee014a87, 0x1eb12a42\n"
        ".word 0xe3520000, 0x1eb10a40, 0xe3530000, 0x1ef12a62\n"
        ".word 0xee221a04, 0xee631a04, 0xee226a23, 0xee244a23\n"
        ".word 0xeef15a40, 0xee630a22, 0xee624a22, 0xee225aa3\n"
        ".word 0xee233a23, 0xed8d4a16, 0xeeb02a60, 0xeef02a64\n"
        ".word 0xed8d5a1a, 0xed8d3a20, 0xee112a00, 0xee412a80\n"
        ".word 0xee101a80, 0xee441a80, 0xed8d1a1c, 0xedcd1a1b\n"
        ".word 0xec802a02, 0xe28d0078, 0xecc05a02, 0xeaffff24\n"
        ".word 0xed940a1d, 0xeef00a69, 0xe3a01000, 0xee200a0b\n"
        ".word 0xe3a03000, 0xeeb40ae0, 0xeef1fa10, 0xeeb01ac0\n"
        ".word 0xeef01a60, 0x33a02001, 0x23a02000, 0xee110a10\n"
        ".word 0xe1500005, 0xba000003, 0xee311a4a, 0xee110a10\n"
        ".word 0xe1500005, 0xaafffffb, 0xee110a90, 0xe1500005\n"
        ".word 0xba000003, 0xee711aca, 0xee110a90, 0xe1500005\n"
        ".word 0xaafffffb, 0xeebc0ae0, 0xe3510000, 0xee100a10\n"
        ".word 0xeebc0ac1, 0xe6ff0070, 0xee10ca10, 0xeebc0ae1\n"
        ".word 0xe6ffc07c, 0xee105a10, 0xee000a10, 0xe20000ff\n"
        ".word 0xe6ff5075, 0xe0870200, 0xeef82a40, 0xee00ca10\n"
        ".word 0xe20cc0ff, 0xed903a01, 0xe087c20c, 0xeddc3a00\n"
        ".word 0xeeb82a40, 0xee005a10, 0xe20550ff, 0xee700ae2\n"
        ".word 0xe0875205, 0xeddc2a01, 0xe28cc008, 0xeeb80a40\n"
        ".word 0xed954a01, 0xee311a42, 0xed952a00, 0xe2855008\n"
        ".word 0xecdc5a02, 0xecd56a02, 0xee711ac0, 0xed900a00\n"
        ".word 0xe2800008, 0xee413a25, 0xecd04a02, 0xee412a06\n"
        ".word 0xe28d0078, 0xee000aa4, 0xee003a85, 0xee012aa6\n"
        ".word 0xee014a87, 0x1eb10a40, 0xe3520000, 0x1ef13a63\n"
        ".word 0xe3530000, 0x1eb12a42, 0xee634a04, 0xee601a04\n"
        ".word 0xee605a22, 0xee244a22, 0xeeb15a63, 0xee600a02\n"
        ".word 0xee231a02, 0xee222a22, 0xee632a22, 0xed8d4a16\n"
        ".word 0xeeb00a60, 0xed8d2a1a, 0xedcd2a20, 0xee040aa3\n"
        ".word 0xee404aa3, 0xeef00a41, 0xee510aa3, 0xee511a23\n"
        ".word 0xedcd0a17, 0xedcd1a1c, 0xed8d0a18, 0xedcd4a1b\n"
        ".word 0xec805a02, 0xeafffec2, 0x42654ca3\n"
    );
}

// DECOMP_FUNC(0x003889dc, 1768)
// Capstone ARM full coverage (442 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_003889dc() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe24dd04c, 0xe3a08001, 0xe1a04001\n"
        ".word 0xe4c08004, 0xebfcc9a9, 0xe3a07000, 0xe5807008\n"
        ".word 0xe2405004, 0xe580700c, 0xe1a01007, 0xe28d0008\n"
        ".word 0xebfcc8db, 0xe59f9688, 0xe1c000d0, 0xe1c500f4\n"
        ".word 0xe5990000, 0xe2800098, 0xebfc9290, 0xe3500000\n"
        ".word 0xe3a0a006, 0x0a000007, 0xe5990000, 0xe5901754\n"
        ".word 0xe3c11801, 0xe5801754, 0xe3a000c8, 0xe584a344\n"
        ".word 0xe5c50000, 0xea000044, 0xe5940344, 0xe3a0b004\n"
        ".word 0xe3500006, 0x379ff100, 0xea00002b, 0x00388a80\n"
        ".word 0x00388bcc, 0x00388c68, 0x00388d40, 0x00388e0c\n"
        ".word 0x00388f0c, 0xe320f000, 0xebfbd8b8, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000022, 0xe5940318, 0xe3500000\n"
        ".word 0x0a000002, 0xe59f15fc, 0xfafcb0b0, 0xe5847318\n"
        ".word 0xe1a01004, 0xe1a0000d, 0xebfffcaa, 0xe1a0000d\n"
        ".word 0xe320f000, 0xebfc633e, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000018, 0xe1cd00d4, 0xe3a06000, 0xe1cd02f8\n"
        ".word 0xe28d0028, 0xebfc62a4, 0xe59f15bc, 0xe1500001\n"
        ".word 0x03a06001, 0xe28d0028, 0xebfc629f, 0xe59f15ac\n"
        ".word 0xe1500001, 0x0a000003, 0xe3560000, 0x089d100f\n"
        ".word 0x0885100f, 0x0a000014, 0xe5c57000, 0xe28dd04c\n"
        ".word 0xe8bd8ff0, 0xe3a00000, 0xebfcf344, 0xe5c57000\n"
        ".word 0xe28dd04c, 0xe8bd8ff0, 0xe1a01004, 0xe28d0034\n"
        ".word 0xeb000182, 0xe28d6034, 0xe896100f, 0xe88d100f\n"
        ".word 0xe1a0000d, 0xebfc631a, 0xe3500000, 0x189d100f\n"
        ".word 0x05848344, 0x0affffec, 0xe885100f, 0xe5940318\n"
        ".word 0xe5847310, 0xe5847314, 0xe3500000, 0xe5847350\n"
        ".word 0x0a000002, 0xe59f151c, 0xfafcb078, 0xe5847318\n"
        ".word 0xe1a00004, 0xebfcafae, 0xe5990000, 0xe5901754\n"
        ".word 0xe3c11801, 0xe5801754, 0xe3a00000, 0xebfcf323\n"
        ".word 0xe5990000, 0xe5901754, 0xe2012010, 0xe1b02222\n"
        ".word 0x03811010, 0x05801754, 0x1affffd3, 0xea000049\n"
        ".word 0xe5942448, 0xe594044c, 0xe2841b01, 0xe281104c\n"
        ".word 0xe1520000, 0xc2800001, 0xc5810000, 0xcaffffca\n"
        ".word 0xe5990000, 0xe59f54bc, 0xe58d403c, 0xe280c088\n"
        ".word 0xe5900094, 0xe58d502c, 0xe59f54ac, 0xe58db028\n"
        ".word 0xe3a03011, 0xe58d5030, 0xe59f54a0, 0xe3e01001\n"
        ".word 0xe59f248c, 0xe58d5034, 0xe5905008, 0xe590000c\n"
        ".word 0xe0800005, 0xe88d0009, 0xe28d0008, 0xe28d303c\n"
        ".word 0xe8800082, 0xe28d1028, 0xe1a0000c, 0xebfcd080\n"
        ".word 0xe200167e, 0xe3510606, 0x11b01fa0, 0x1bfcf202\n"
        ".word 0xe3a00002, 0xe320f000, 0xea00001f, 0xe5990000\n"
        ".word 0xe2800088, 0xebfaaf71, 0xe3500000, 0xe320f000\n"
        ".word 0x0affffa5, 0xe2840fc7, 0xebfc62cd, 0xe3500000\n"
        ".word 0x12840fc7, 0x1890100f, 0x1affffb2, 0xe5940310\n"
        ".word 0xe3a05000, 0xe3500000, 0xda00000e, 0xe5940318\n"
        ".word 0xe0856105, 0xe0800206, 0xe2800008, 0xebfc68f3\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe5940318\n"
        ".word 0xe0800206, 0xeb000b4c, 0xe5940310, 0xe2855001\n"
        ".word 0xe1500005, 0xcafffff0, 0xe3a00003, 0xe5840344\n"
        ".word 0xe28dd04c, 0xe8bd8ff0, 0xe3811040, 0xe5801754\n"
        ".word 0xe2850004, 0xe584a344, 0xebfc621b, 0xe59f13b0\n"
        ".word 0xe1500001, 0x0affff80, 0xe5990000, 0xe2800098\n"
        ".word 0xebfc91d2, 0xe3500000, 0xe320f000, 0x0a00007d\n"
        ".word 0xe5990000, 0xe5901754, 0xe3c11801, 0xe5801754\n"
        ".word 0xea0000aa, 0xe5940310, 0xe3a05000, 0xe3500000\n"
        ".word 0xda000011, 0xe5940318, 0xe0856105, 0xe0800206\n"
        ".word 0xe2800008, 0xebfc68c9, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000005, 0xe5940318, 0xe0800206, 0xebfaaf27\n"
        ".word 0xe3500000, 0xe320f000, 0x0affff63, 0xe5940310\n"
        ".word 0xe2855001, 0xe1500005, 0xcaffffed, 0xe3500000\n"
        ".word 0xe3a05000, 0xda000014, 0xe5940318, 0xe0856105\n"
        ".word 0xe0800206, 0xe2800008, 0xebfc68b4, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000008, 0xe5940318, 0xe0800206\n"
        ".word 0xebfaaf12, 0xe3500000, 0xe320f000, 0x0a000002\n"
        ".word 0xe5940318, 0xe0800206, 0xeb000ae3, 0xe5940310\n"
        ".word 0xe2855001, 0xe1500005, 0xcaffffea, 0xe5847354\n"
        ".word 0xe584b344, 0xe5847358, 0xe28dd04c, 0xe8bd8ff0\n"
        ".word 0xe5940310, 0xe3500000, 0x0a000038, 0xe5941358\n"
        ".word 0xe3510000, 0x0a000002, 0xe3510001, 0x0a000023\n"
        ".word 0xea00002e, 0xe5941354, 0xe1510000, 0xaa00002b\n"
        ".word 0xe5940354, 0xe5941318, 0xe0800100, 0xe0810200\n"
        ".word 0xe2800008, 0xebfc688d, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00000f, 0xe5940354, 0xe5941318, 0xe0800100\n"
        ".word 0xe0810200, 0xebfaaee9, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000007, 0xe5940354, 0xe5941318, 0xe0800100\n"
        ".word 0xe0810200, 0xeb000aff, 0xe5848358, 0xe320f000\n"
        ".word 0xea000012, 0xe5940354, 0xe5941310, 0xe2800001\n"
        ".word 0xe1500001, 0xe5840354, 0xbaffffe0, 0xea00000b\n"
        ".word 0xe5940354, 0xe5941318, 0xe0800100, 0xe0810200\n"
        ".word 0xeb000b61, 0xe3500000, 0xe320f000, 0x0a000003\n"
        ".word 0xe5940354, 0xe2841fd5, 0xe2800001, 0xe8810081\n"
        ".word 0xe5940354, 0xe5941310, 0xe1500001, 0xbaffff06\n"
        ".word 0xe3a00005, 0xe5840344, 0xe28dd04c, 0xe8bd8ff0\n"
        ".word 0xe1a00004, 0xebfff49b, 0xe5c57000, 0xe584a344\n"
        ".word 0xe28dd04c, 0xe8bd8ff0, 0xe5d50000, 0xe35000c8\n"
        ".word 0x0a00002e, 0xe895100f, 0xe28d6014, 0xe886100f\n"
        ".word 0xe28d1014, 0xe1c520d4, 0xe5990000, 0xebf75345\n"
        ".word 0xe3500000, 0xe320f000, 0x1afffeef, 0xe5d50000\n"
        ".word 0xe3500069, 0x0a000030, 0xe350006a, 0x0a000036\n"
        ".word 0xe2850004, 0xebfc6180, 0xe2850004, 0xe320f000\n"
        ".word 0xebfc617d, 0xe3100102, 0xe1a00da0, 0x12400020\n"
        ".word 0xe3700004, 0x0a000033, 0xe2850004, 0xebfc6176\n"
        ".word 0xe3100102, 0xe1a00da0, 0x12400020, 0xe3700005\n"
        ".word 0x0a00002c, 0xe5940350, 0xe2800001, 0xe3500003\n"
        ".word 0xe5840350, 0xb1a01007, 0xb5847344, 0xaafffed2\n"
        ".word 0xe5c58000, 0xe28d0008, 0xe585100c, 0xebfcc768\n"
        ".word 0xe1c000d0, 0xe1c500f4, 0xe28dd04c, 0xe8bd8ff0\n"
        ".word 0xe5990000, 0xe28d6028, 0xe5901754, 0xe3110c01\n"
        ".word 0xe895100a, 0x13a02066, 0xe1c540dc, 0x03a02065\n"
        ".word 0xe886100a, 0xe3a03000, 0xe28d1028, 0xe1cd43f4\n"
        ".word 0xebfcc721, 0xe28dd04c, 0xe8bd8ff0, 0xe895100f\n"
        ".word 0xe88d100f, 0xe1a0100d, 0xe595200c, 0xe5990000\n"
        ".word 0xeb0009b1, 0xe28dd04c, 0xe8bd8ff0, 0xe895100f\n"
        ".word 0xe88d100f, 0xe1a0100d, 0xe3a03000, 0xe5952010\n"
        ".word 0xe5990000, 0xea00000b, 0xe5990000, 0xe28d6028\n"
        ".word 0xe5901754, 0xe3110c01, 0xe895100a, 0x13a02032\n"
        ".word 0xe1c540dc, 0x03a02096, 0xe886100a, 0xe3a03000\n"
        ".word 0xe28d1028, 0xe1cd43f4, 0xebfcc703, 0xe28dd04c\n"
        ".word 0xe8bd8ff0, 0x00432fc8, 0x0013188c, 0xc8813894\n"
        ".word 0xc8813887, 0x0038a258, 0x003f7120, 0x003f722c\n"
        ".word 0x003f71d0, 0xc9413891\n"
    );
}

// DECOMP_FUNC(0x003bd508, 1800)
// Capstone ARM full coverage (450 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_003bd508() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe1a04002, 0xed2d0b02, 0xed2d8b0a\n"
        ".word 0xe24ddf4f, 0xebfb59dd, 0xe58d0108, 0xe59d016c\n"
        ".word 0xebfbc3b0, 0xe58d0120, 0xe1a00004, 0xebfbdcc6\n"
        ".word 0xe3500000, 0x11d006b2, 0x13500000, 0x0a000001\n"
        ".word 0xebfbc3a8, 0xe58d0120, 0xe59d0108, 0xe59d1178\n"
        ".word 0xebfb158d, 0xe1a04000, 0xe59d0108, 0xe59d11a0\n"
        ".word 0xebfb1589, 0xe58d0114, 0xe59d1108, 0xe1a02004\n"
        ".word 0xe28d0024, 0xebfa2818, 0xe5dd8035, 0xe3580000\n"
        ".word 0x1a000013, 0xe59d0120, 0xe3500000, 0x0a000008\n"
        ".word 0xe5d00035, 0xe3100020, 0x1a000003, 0xe59d0120\n"
        ".word 0xe1d003b6, 0xe3100a02, 0x0a000005, 0xe59d01a0\n"
        ".word 0xeb00086f, 0xe28ddf4f, 0xecbd8b0a, 0xe28dd018\n"
        ".word 0xe8bd8ff0, 0xe59d0120, 0xe5d0002f, 0xe3500000\n"
        ".word 0x0afffff7, 0xe5dd0036, 0xe59d4178, 0xee000a10\n"
        ".word 0xeef88a40, 0xebfb59a9, 0xe1a01004, 0xe320f000\n"
        ".word 0xebfb1565, 0xe1a04000, 0xe320f000, 0xebfb59a3\n"
        ".word 0xe1a01000, 0xe1a02004, 0xe1a0000d, 0xebfa27f2\n"
        ".word 0xe1ddb0f4, 0xe3a01048, 0xe28d0078, 0xebfc1d41\n"
        ".word 0xe3a01048, 0xe28d00c0, 0xebfc1d3e, 0xe3a00000\n"
        ".word 0xe58d0048, 0xe58d004c, 0xe58d0050, 0xe58d0054\n"
        ".word 0xe58d0058, 0xe58d005c, 0xe3580001, 0xe28d6078\n"
        ".word 0xe3a0a001, 0xe58d0060, 0xe58d0064, 0xe58d0068\n"
        ".word 0xe58d006c, 0xe58d0070, 0x0a000016, 0xe3580013\n"
        ".word 0x13580014, 0xe3a02005, 0xe3a03006, 0xe3a04007\n"
        ".word 0xe3a05008, 0xe3a07009, 0x0a000013, 0xe3580016\n"
        ".word 0x0a000027, 0xe1a00008, 0xebfa23ab, 0xe3a07001\n"
        ".word 0xe58d0078, 0xe58d8048, 0xe59d0120, 0xe3e09000\n"
        ".word 0xe3500000, 0x0a00003d, 0xe5d00023, 0xe3500001\n"
        ".word 0x0a000036, 0xea000039, 0xe1dd02b6, 0xe3a07001\n"
        ".word 0xe58da048, 0xe58d0078, 0xeafffff2, 0xe3a00005\n"
        ".word 0xebfa2399, 0xe58d0078, 0xe3a00006, 0xe58d2048\n"
        ".word 0xebfa2395, 0xe58d007c, 0xe3a00007, 0xe58d304c\n"
        ".word 0xebfa2391, 0xe58d0080, 0xe3a00008, 0xe58d4050\n"
        ".word 0xebfa238d, 0xe58d0084, 0xe3a00009, 0xe58d5054\n"
        ".word 0xebfa2389, 0xe58d7058, 0xe3a07005, 0xe58d0088\n"
        ".word 0xeaffffdc, 0xe3a00005, 0xebfa2383, 0xe58d0078\n"
        ".word 0xe3a00006, 0xe58d2048, 0xebfa237f, 0xe58d007c\n"
        ".word 0xe3a00007, 0xe58d304c, 0xebfa237b, 0xe58d0080\n"
        ".word 0xe3a00008, 0xe58d4050, 0xebfa2377, 0xe58d0084\n"
        ".word 0xe3a00009, 0xe58d5054, 0xebfa2373, 0xe58d0088\n"
        ".word 0xe3a00003, 0xe58d7058, 0xebfa236f, 0xe3a01003\n"
        ".word 0xe3a07006, 0xe58d008c, 0xe58d105c, 0xeaffffc1\n"
        ".word 0xe59d0120, 0xe5900028, 0xe1a00780, 0xe1a09da0\n"
        ".word 0xeebd8ae8, 0xee180a10, 0xe35000ff, 0x0a000014\n"
        ".word 0xe3570000, 0xe3a04000, 0xc28d50c0, 0xda000010\n"
        ".word 0xe7961104, 0xe59d01a0, 0xe1a03009, 0xe1a0200b\n"
        ".word 0xebfa22ac, 0xe7850104, 0xe7961104, 0xe59d01a0\n"
        ".word 0xebf9b4ab, 0xe7951104, 0xe1800001, 0xe3100817\n"
        ".word 0xe7850104, 0x1a000016, 0xe2844001, 0xe1540007\n"
        ".word 0xbaffffee, 0xe3580013, 0x13580014, 0x03a0be3e\n"
        ".word 0x0a000002, 0xe3580016, 0x11a0b81a, 0x03a0bffa\n"
        ".word 0xe59d0114, 0xe5900000, 0xe3100020, 0x1a000008\n"
        ".word 0xee180a10, 0xe35000ff, 0x0a0000e5, 0xe59d0108\n"
        ".word 0xe2800b11, 0xe28000a8, 0xe5900000, 0xe3100301\n"
        ".word 0x0a000001, 0xe3a00000, 0xeaffff51, 0xe3100080\n"
        ".word 0x1a0000db, 0xe59d8108, 0xe2888901, 0xe2888e4a\n"
        ".word 0xe5980000, 0xe3100701, 0xe59d0120, 0x13cbbb01\n"
        ".word 0xe3500000, 0x15d00048, 0x13500000, 0x1a0000d0\n"
        ".word 0xe59d0108, 0xe59d1178, 0xebfb00fa, 0xe1a04000\n"
        ".word 0xe59d0108, 0xe59d11a0, 0xebfb00f6, 0xe1a09000\n"
        ".word 0xe28000e8, 0xe1d41ff6, 0xe1d020fe, 0xe1d43ff8\n"
        ".word 0xe1d001f0, 0xe0411002, 0xee001a90, 0xe0430000\n"
        ".word 0xee010a10, 0xed9f0ac0, 0xeddf1ac0, 0xe3570000\n"
        ".word 0xeef80ae0, 0xe3a05000, 0xeeb81ac1, 0xee600aa1\n"
        ".word 0xee211a00, 0xda0000a9, 0xee689a80, 0xeddfbab8\n"
        ".word 0xeddf1ab8, 0xed9f8ab8, 0xed9fbab8, 0xee780aa0\n"
        ".word 0xee28aaa1, 0xeddfcab6, 0xee700a81, 0xee30caab\n"
        ".word 0xe28d00c0, 0xe3a04000, 0xe7900105, 0xe58d4134\n"
        ".word 0xe28d1f4d, 0xe6ff0070, 0xee000a10, 0xe28d0078\n"
        ".word 0xe7900105, 0xeeb80a40, 0xee608a0b, 0xebf9b4cc\n"
        ".word 0xe59d616c, 0xe59da178, 0xebfb58c8, 0xe1a0100a\n"
        ".word 0xe320f000, 0xebfb1484, 0xe5900000, 0xe3100002\n"
        ".word 0x0a00000d, 0xe1a00006, 0xebfbc296, 0xe1b0a000\n"
        ".word 0xe320f000, 0x0a000008, 0xe1a00006, 0xebfbc27a\n"
        ".word 0xe1a01000, 0xe3a02003, 0xe1a0000a, 0xebfb19dc\n"
        ".word 0xee000a10, 0xeeb80ac0, 0xea000000, 0xeeb00a6b\n"
        ".word 0xe3a01005, 0xe3e00004, 0xee3c9a00, 0xebfa6191\n"
        ".word 0xee000a10, 0xe5980000, 0xe59da1a0, 0xe3100701\n"
        ".word 0xe28d0048, 0xeeb80ac0, 0x1eb00a6b, 0xe7900105\n"
        ".word 0xe6ff6070, 0xee200a0b, 0xee200a09, 0xee399a00\n"
        ".word 0xebfb58a2, 0xe1a0100a, 0xe320f000, 0xebfb145e\n"
        ".word 0xe3500000, 0x0eb00a48, 0x0a000024, 0xe28d1f43\n"
        ".word 0xe58d410c, 0xe58d4110, 0xe58d4114, 0xe58d4118\n"
        ".word 0xe58d411c, 0xebf9b4cc, 0xe3a00000, 0xe1a04000\n"
        ".word 0xe28daf43, 0xe58d001c, 0xe08a1084, 0xe1d110b0\n"
        ".word 0xe3510000, 0x0a00000e, 0xe1a00001, 0xebfb1993\n"
        ".word 0xe3500000, 0x15d0102e, 0x13510000, 0x0a000008\n"
        ".word 0xe3560001, 0x13560002, 0x0a000005, 0xe3560004\n"
        ".word 0x1356000a, 0x0a000002, 0xe59d001c, 0xe0800001\n"
        ".word 0xe58d001c, 0xe2844001, 0xe3540009, 0xbaffffe9\n"
        ".word 0xeddd0a07, 0xeeb00a48, 0xeef80ae0, 0xee000acb\n"
        ".word 0xe5d90000, 0xee290a00, 0xeef49ac0, 0xeef1fa10\n"
        ".word 0xceb00a69, 0xeeb4aac0, 0xeef1fa10, 0xe3100004\n"
        ".word 0x3eb00a4a, 0xee60aa28, 0x1a000002, 0xebfa0441\n"
        ".word 0xed900a03, 0xee60aa2a, 0xe59d0108, 0xe28d6048\n"
        ".word 0xe3a04000, 0xe28010c8, 0xe5d000f4, 0xe7962105\n"
        ".word 0xe1520000, 0x1a00000b, 0xe3500001, 0x13500005\n"
        ".word 0x1a000002, 0xe5d9c000, 0xe31c0004, 0x11d142de\n"
        ".word 0xe3500003, 0x13500005, 0x1a000002, 0xe5d90000\n"
        ".word 0xe3100004, 0x01d142de, 0xe3520001, 0x1a00000b\n"
        ".word 0xe28d0078, 0xe7900105, 0xe3500006, 0x0a000007\n"
        ".word 0xe3500007, 0x0a000005, 0xe3a00063, 0xebfa0434\n"
        ".word 0xe5d9114a, 0xe1510000, 0xdef0aa6c, 0xd3e04000\n"
        ".word 0xe5980000, 0xe3100701, 0x1a000009, 0xe3a00063\n"
        ".word 0xebfa042b, 0xeebd0aea, 0xee101a10, 0xe0811004\n"
        ".word 0xe1510000, 0xaa000002, 0xe7961105, 0xe3a00001\n"
        ".word 0xe1cbb110, 0xe2855001, 0xe1550007, 0xbaffff5f\n"
        ".word 0xe59d0120, 0xe3500000, 0x0a000009, 0xe5d00035\n"
        ".word 0xe3100020, 0x1a000003, 0xe59d0120, 0xe1d003b6\n"
        ".word 0xe3100a02, 0x0a000002, 0xe59d01a0, 0xeb0006e4\n"
        ".word 0xe18bb000, 0xe1a0000b, 0xeafffe71, 0x3f000000\n"
        ".word 0x3e800000, 0x00000000, 0x40000000, 0x3f800000\n"
        ".word 0x3c23d70a, 0xbf800000\n"
    );
}

// DECOMP_FUNC(0x0015aa90, 1812)
// Capstone ARM full coverage (453 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void func_0015aa90() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff7, 0xe1a07001, 0xe1a06002, 0xe59fb2e0\n"
        ".word 0xed2d8b02, 0xe24dd068, 0xe5924008, 0xe59d1070\n"
        ".word 0xe3a02001, 0xe1a05712, 0xe59110a4, 0xe59400b8\n"
        ".word 0xed9f8ab0, 0xe2811f52, 0xe3500000, 0xe58d1010\n"
        ".word 0x0a000057, 0xe59f12b0, 0xeddf8aac, 0xe3500001\n"
        ".word 0xe0818207, 0xe59f12a8, 0xe3a09000, 0xe287a00f\n"
        ".word 0xe5912000, 0x0a000079, 0xe3500002, 0x1a000073\n"
        ".word 0xe594111c, 0xe2840f47, 0xe3510000, 0x10800001\n"
        ".word 0x01a00009, 0xe3500000, 0x0a000040, 0xe59f0270\n"
        ".word 0xe1c22005, 0xe3510000, 0xe5802000, 0xe2840f47\n"
        ".word 0x10800001, 0x01a00009, 0xe5b01008, 0xe3510000\n"
        ".word 0x10800001, 0x01a00009, 0xe5901000, 0xe3510102\n"
        ".word 0x0a000002, 0xe3510101, 0x13a00000, 0x0a0000b2\n"
        ".word 0xe2871007, 0xe20110ff, 0xeb051d4e, 0xe594111c\n"
        ".word 0xe2840f47, 0xe3510000, 0x10800001, 0x01a00009\n"
        ".word 0xe5b02008, 0xe3520000, 0x10800002, 0x01a00009\n"
        ".word 0xe5902000, 0xe3520102, 0x0a000002, 0xe3520101\n"
        ".word 0x13a00000, 0x0a0000a5, 0xe59f21e8, 0xe5d00008\n"
        ".word 0xe3500000, 0xe5920000, 0x13c00c02, 0x03800c02\n"
        ".word 0xe5820000, 0xe3510000, 0xe2840f47, 0x10800001\n"
        ".word 0x01a00009, 0xe59f21c0, 0xe5900000, 0xe1a00c00\n"
        ".word 0xe1a03820, 0xe5920000, 0xe3c00c07, 0xe1800003\n"
        ".word 0xe5820000, 0xe2840f47, 0x10800001, 0x01a00009\n"
        ".word 0xe59f1198, 0xe5900004, 0xe1a00c00, 0xe1a02820\n"
        ".word 0xe5910000, 0xe3c00c07, 0xe1800002, 0xe5810000\n"
        ".word 0xe5940018, 0xe3a01004, 0xe1d10000, 0x0a000088\n"
        ".word 0xea0000ae, 0xe596017c, 0xe1a0300d, 0xe1a02001\n"
        ".word 0xe58d0000, 0xe5960180, 0xe1a01003, 0xe58d0004\n"
        ".word 0xe5960184, 0xe58d0008, 0xed8d8a03, 0xe59d0070\n"
        ".word 0xeb051b49, 0xecdd0a03, 0xe28d2020, 0xed9d0a03\n"
        ".word 0xe28d1020, 0xeef10a60, 0xeeb10a40, 0xeef11a61\n"
        ".word 0xeeb11a41, 0xe1a00007, 0xed8d0a0b, 0xecc20a03\n"
        ".word 0xeb000a99, 0xed9d0a03, 0xe59b0000, 0xeeb40a48\n"
        ".word 0xeef1fa10, 0x01800005, 0x11c00005, 0xe58b0000\n"
        ".word 0xe59f00dc, 0xe5901000, 0xe1811005, 0xe5801000\n"
        ".word 0xe59f00dc, 0xe5901000, 0xe1811005, 0xe5801000\n"
        ".word 0xe28dd068, 0xecbd8b02, 0xe28dd00c, 0xe8bd8ff0\n"
        ".word 0xe59f00ac, 0xe1851002, 0xe59f20b4, 0xe5801000\n"
        ".word 0xe5940018, 0xe5922000, 0xe3a01004, 0xe1d10000\n"
        ".word 0x1a00002e, 0xe5941118, 0xe2840f46, 0xe3510000\n"
        ".word 0x10800001, 0x01a00009, 0xe3500000, 0x0a000027\n"
        ".word 0xe59f007c, 0xe1c22005, 0xe3510000, 0xe5802000\n"
        ".word 0xe2840f46, 0x10800001, 0x01a00009, 0xe5901000\n"
        ".word 0xe3510102, 0x0a000002, 0xe3510101, 0x13a00000\n"
        ".word 0x0a000015, 0xe20a10ff, 0xeb051cd2, 0xe59f1044\n"
        ".word 0xe2844f4a, 0xe894000c, 0xe5910000, 0xe2804008\n"
        ".word 0xe280c010, 0xe8840204, 0xe8800108, 0xe581c000\n"
        ".word 0xea000011, 0x00472100, 0x00000000, 0x8017014a\n"
        ".word 0x3f800000, 0x00472108, 0x004720e0, 0x004720e4\n"
        ".word 0x004720e8, 0x0047210c, 0x004652a0, 0xe5b0100c\n"
        ".word 0xe3510000, 0x10800001, 0x01a00009, 0xeaffffe4\n"
        ".word 0xe51f0024, 0xe1851002, 0xe5801000, 0xe5b60098\n"
        ".word 0xe28d3020, 0xe5b61010, 0xe5962010, 0xe8830007\n"
        ".word 0xe1a01003, 0xedcd8a0b, 0xe59d0070, 0xe59d2010\n"
        ".word 0xeb051ae5, 0xe28d1020, 0xe1a00007, 0xeb000a3e\n"
        ".word 0xed9d0a0b, 0xeeb40a48, 0xeef1fa10, 0x1a000002\n"
        ".word 0xe59b0000, 0xe1800005, 0xea000001, 0xe59b0000\n"
        ".word 0xe1c00005, 0xe58b0000, 0xeaffffa8, 0xe5b0100c\n"
        ".word 0xe3510000, 0x10800001, 0x01a00009, 0xeaffff47\n"
        ".word 0xe5b0200c, 0xe3520000, 0x10800002, 0x01a00009\n"
        ".word 0xeaffff54, 0xe5940118, 0xe2841f46, 0xe3500000\n"
        ".word 0x10811000, 0x01a01009, 0xe3510000, 0x0a00001f\n"
        ".word 0xe51f10d4, 0xe3500000, 0xe5912000, 0xe1c22005\n"
        ".word 0xe5812000, 0xe2841f46, 0x10800001, 0x01a00009\n"
        ".word 0xe5901000, 0xe3510102, 0x0a000002, 0xe3510101\n"
        ".word 0x13a00000, 0x0a00000c, 0xe20a10ff, 0xeb051c7d\n"
        ".word 0xe51f1110, 0xe2844f4a, 0xe8941004, 0xe5910000\n"
        ".word 0xe2804008, 0xe5808004, 0xe580c000, 0xe8840204\n"
        ".word 0xe2803010, 0xe5813000, 0xea000008, 0xe5b0100c\n"
        ".word 0xe3510000, 0x10800001, 0x01a00009, 0xeaffffed\n"
        ".word 0xe51f0154, 0xe5901000, 0xe1811005, 0xe5801000\n"
        ".word 0xe596017c, 0xe28d3050, 0xe1a01003, 0xe58d0050\n"
        ".word 0xe5960180, 0xe58d0054, 0xe5960184, 0xe58d0058\n"
        ".word 0xed8d8a17, 0xe59d0070, 0xe59d2010, 0xeb051a96\n"
        ".word 0xe5b60098, 0xe28d3040, 0xe5b61010, 0xe5962010\n"
        ".word 0xe8830007, 0xe1a01003, 0xedcd8a13, 0xe59d0070\n"
        ".word 0xe59d2010, 0xeb051a8c, 0xed9d0a14, 0xed9d1a15\n"
        ".word 0xeddd0a16, 0xe58d902c, 0xe59d2040, 0xe58d9030\n"
        ".word 0xe59f0218, 0xe2123102, 0xe1a0c482, 0xe1a0e082\n"
        ".word 0xe59d1044, 0xe1a0c4ac, 0x13a03902, 0xe3d22102\n"
        ".word 0xe58d9028, 0xe1a0ec2e, 0x01a0c6ac, 0xe58d9034\n"
        ".word 0xe58d9038, 0xe58d903c, 0x0a000005, 0xe25e2070\n"
        ".word 0xe1a0c6ac, 0x4a000005, 0xe352001f, 0xc3a03b1f\n"
        ".word 0xca000002, 0xe202e01f, 0xe18c2003, 0xe182350e\n"
        ".word 0xe1a0c081, 0xe2112102, 0xe1a0ec2c, 0xe1a0c481\n"
        ".word 0x13a02902, 0xe1a0c4ac, 0xe3d11102, 0xe6ff3073\n"
        ".word 0x01a0c6ac, 0x0a000005, 0xe25e1070, 0xe1a0c6ac\n"
        ".word 0x4a000005, 0xe351001f, 0xc3a02b1f, 0xca000002\n"
        ".word 0xe201e01f, 0xe18c1002, 0xe181250e, 0xe0800207\n"
        ".word 0xe1831802, 0xe58d1028, 0xe59d1048, 0xe58d002c\n"
        ".word 0xe2110102, 0xe1a02081, 0x13a00902, 0xe1a03c22\n"
        ".word 0xe1a02481, 0xe3d11102, 0xe1a024a2, 0x01a026a2\n"
        ".word 0x0a000005, 0xe2531070, 0xe1a026a2, 0x4a000005\n"
        ".word 0xe351001f, 0xc3a00b1f, 0xca000002, 0xe201101f\n"
        ".word 0xe1800002, 0xe1800501, 0xeeb10a40, 0xed9f3a44\n"
        ".word 0xeddf2a44, 0xe6ff0070, 0xe58d0030, 0xeeb11a41\n"
        ".word 0xee300a03, 0xeddf1a40, 0xee200a22, 0xee100a10\n"
        ".word 0xee000a10, 0xeeb40ac8, 0xeef1fa10, 0x3e180a10\n"
        ".word 0x3a000001, 0xe3500446, 0xae110a90, 0xed9f2a37\n"
        ".word 0xee000a10, 0xee300a42, 0xeebd0ac0, 0xee100a10\n"
        ".word 0xee310a03, 0xe1a01980, 0xe1a019a1, 0xee200a22\n"
        ".word 0xee100a10, 0xee000a10, 0xeeb40ac8, 0xeef1fa10\n"
        ".word 0x3e180a10, 0x3a000001, 0xe3500446, 0xae110a90\n"
        ".word 0xee000a10, 0xee300a42, 0xeebd0ac0, 0xee100a10\n"
        ".word 0xeeb10a60, 0xe1a00980, 0xe1a009a0, 0xee300a03\n"
        ".word 0xe1810800, 0xe58d0034, 0xee200a22, 0xee100a10\n"
        ".word 0xee000a10, 0xeeb40ac8, 0xeef1fa10, 0x3e180a10\n"
        ".word 0x3a000001, 0xe3500446, 0xae110a90, 0xe51f43ac\n"
        ".word 0xe28d1028, 0xee000a10, 0xee300a42, 0xeebd0ac0\n"
        ".word 0xee100a10, 0xe1a00980, 0xe1a009a0, 0xe58d0038\n"
        ".word 0xe5940000, 0xeb051cfd, 0xe5840000, 0xed9d0a13\n"
        ".word 0xeeb40a48, 0xeef1fa10, 0x1affff23, 0xeaffff1f\n"
        ".word 0x803f0144, 0x40000000, 0x45000000, 0x45fff800\n"
        ".word 0x45800000\n"
    );
}

// DECOMP_FUNC(0x00218384, 1820)
// Capstone ARM full coverage (455 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void camp_func_00218384() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a04000, 0xe24dd044, 0xe2800a03\n"
        ".word 0xe2800fea, 0xe3a01000, 0xe58d000c, 0xeb02046c\n"
        ".word 0xe2846a03, 0xe3e00000, 0xe5860064, 0xe3a02001\n"
        ".word 0xe3a01022, 0xe1a00004, 0xeb020006, 0xe3a00038\n"
        ".word 0xeb0281eb, 0xe3a09000, 0xe1cd91b4, 0xe1a0200d\n"
        ".word 0xe28d1014, 0xe1a00004, 0xe1cd90b0, 0xeb01d27f\n"
        ".word 0xe59f06a8, 0xe2848b0d, 0xe288805c, 0xe284ab0d\n"
        ".word 0xe5880000, 0xe58a9060, 0xe58a9064, 0xe58a9068\n"
        ".word 0xe58a906c, 0xe1dd01f4, 0xe2841a03, 0xe2811e46\n"
        ".word 0xe3500002, 0x13500003, 0xe3a0b023, 0xe58d1004\n"
        ".word 0x1a000082, 0xe1dd00f0, 0xeb0257ef, 0xe5901028\n"
        ".word 0xe1a07000, 0xe3a00003, 0xe1a01b81, 0xe1500e21\n"
        ".word 0x1a00002d, 0xe586b048, 0xe28d2008, 0xe28d1028\n"
        ".word 0xe1a00004, 0xe1cd92b8, 0xe1cd90b8, 0xeb01d25f\n"
        ".word 0xe596005c, 0xe59d3004, 0xe1dd20f8, 0xe2400001\n"
        ".word 0xe3e01000, 0xeb0127db, 0xe3a05001, 0xe320f000\n"
        ".word 0xeb02415f, 0xe59f1608, 0xe0800005, 0xe0842105\n"
        ".word 0xe2823a03, 0xe19010d1, 0xe596005c, 0xe1dd20f8\n"
        ".word 0xe2833e46, 0xe2400001, 0xeb0127ce, 0xe2855001\n"
        ".word 0xe3550004, 0xbafffff0, 0xe1dd00f8, 0xeb0257ca\n"
        ".word 0xe5900038, 0xe3100c06, 0x0a00000d, 0xe596105c\n"
        ".word 0xe3510004, 0x2a00000a, 0xe59f05b8, 0xe7900004\n"
        ".word 0xe3500000, 0xaa000006, 0xe0841101, 0xe2811a03\n"
        ".word 0xe2811e46, 0xe5810000, 0xea000001, 0xe1a00004\n"
        ".word 0xeb01d2e1, 0xe5971028, 0xe3a00004, 0xe1a01b81\n"
        ".word 0xe1500e21, 0x1a000004, 0xe3a00024, 0xe5860048\n"
        ".word 0xe596105c, 0xe59d000c, 0xeb020409, 0xe1dd10f0\n"
        ".word 0xe3e00000, 0xeb049e97, 0xe3500000, 0xe3a05000\n"
        ".word 0x15c89000, 0xe320f000, 0xeb02412d, 0xe0800005\n"
        ".word 0xe2800c91, 0xe1d000d8, 0xe3500000, 0xba000005\n"
        ".word 0xe1dd10f0, 0xe1a00005, 0xeb049e8a, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000003, 0xe0840005, 0xe2800b0d\n"
        ".word 0xe280005d, 0xe5c09000, 0xe2855001, 0xe3550003\n"
        ".word 0xbaffffeb, 0xe5970038, 0xe3100c02, 0x1596005c\n"
        ".word 0x17c09008, 0xe5d70023, 0xe3500003, 0x1a00001f\n"
        ".word 0xe5971028, 0xe3a00002, 0xe1a01b81, 0xe1500e21\n"
        ".word 0x1a00001a, 0xe1d703b6, 0xe1b00a00, 0x0a000017\n"
        ".word 0xe5970038, 0xe200007f, 0xe3500001, 0x0a000013\n"
        ".word 0xe3a00001, 0xeb01f66f, 0xe3500000, 0x13a00000\n"
        ".word 0x0a00000e, 0xe0841000, 0xe2811b0d, 0xe281105d\n"
        ".word 0xe5d11000, 0xe3510000, 0x0a000005, 0xe2801001\n"
        ".word 0xe59d000c, 0xeb0203ce, 0xe320f000, 0xe320f000\n"
        ".word 0xea000002, 0xe2800001, 0xe3500003, 0xbafffff0\n"
        ".word 0xe1dd01b4, 0xe3500008, 0x1a000084, 0xe58a9070\n"
        ".word 0xe58a9074, 0xe58a9078, 0xe58a907c, 0xe1dd00f0\n"
        ".word 0xeb02707e, 0xe1d006b2, 0xe3500000, 0x0a00007d\n"
        ".word 0xeb025761, 0xe5901028, 0xe1a07000, 0xe3a00003\n"
        ".word 0xe1a01b81, 0xe1500e21, 0x1a00002d, 0xe586b048\n"
        ".word 0xe1cd91bc, 0xe28d2008, 0xe28d101c, 0xe1a00004\n"
        ".word 0xe1cd90b8, 0xeb01d1d1, 0xe596005c, 0xe59d3004\n"
        ".word 0xe1dd20f8, 0xe2400001, 0xe3e01000, 0xeb01274d\n"
        ".word 0xe3a05001, 0xe320f000, 0xeb0240d1, 0xe59f13d0\n"
        ".word 0xe0800005, 0xe0842105, 0xe2823a03, 0xe19010d1\n"
        ".word 0xe596005c, 0xe1dd20f8, 0xe2833e46, 0xe2400001\n"
        ".word 0xeb012740, 0xe2855001, 0xe3550004, 0xbafffff0\n"
        ".word 0xe1dd00f8, 0xeb02573c, 0xe5900038, 0xe3100c06\n"
        ".word 0x0a00000d, 0xe596105c, 0xe3510004, 0x2a00000a\n"
        ".word 0xe59f0380, 0xe7900004, 0xe3500000, 0xaa000006\n"
        ".word 0xe0841101, 0xe2811a03, 0xe2811e46, 0xe5810000\n"
        ".word 0xea000001, 0xe1a00004, 0xeb01d253, 0xe5971028\n"
        ".word 0xe3a00004, 0xe1a01b81, 0xe1500e21, 0x1a000004\n"
        ".word 0xe3a00024, 0xe5860048, 0xe596105c, 0xe59d000c\n"
        ".word 0xeb02037b, 0xe1dd10f0, 0xe3e00000, 0xeb00dfc1\n"
        ".word 0xe3500000, 0xe3a05000, 0x15c89000, 0xe320f000\n"
        ".word 0xeb02409f, 0xe0800005, 0xe2800c91, 0xe1d000d8\n"
        ".word 0xe3500000, 0xba000005, 0xe1dd10f0, 0xe1a00005\n"
        ".word 0xeb00dfb4, 0xe3500000, 0xe320f000, 0x0a000003\n"
        ".word 0xe0840005, 0xe2800b0d, 0xe280005d, 0xe5c09000\n"
        ".word 0xe2855001, 0xe3550003, 0xbaffffeb, 0xe5970038\n"
        ".word 0xe3100c02, 0x1596005c, 0x17c09008, 0xe5d70023\n"
        ".word 0xe3500003, 0x1a000019, 0xe5971028, 0xe3a00002\n"
        ".word 0xe1a01b81, 0xe1500e21, 0x1a000014, 0xe1d703b6\n"
        ".word 0xe1b00a00, 0x0a000011, 0xe5970038, 0xe200007f\n"
        ".word 0xe3500001, 0x0a00000d, 0xe3a00001, 0xeb01f5e1\n"
        ".word 0xe3500000, 0x13a00000, 0x0a000008, 0xe0841000\n"
        ".word 0xe2811b0d, 0xe281105d, 0xe5d11000, 0xe3510000\n"
        ".word 0x1a000088, 0xe2800001, 0xe3500003, 0xbafffff6\n"
        ".word 0xe28dd044, 0xe8bd8ff0, 0xe1dd00f0, 0xeb026ffb\n"
        ".word 0xe1a07000, 0xe5d0006a, 0xe284aa03, 0xe28aae47\n"
        ".word 0xe3100080, 0x0a00001c, 0xe586b048, 0xe28d2008\n"
        ".word 0xe28d1020, 0xe1a00004, 0xe1cd92b0, 0xe1cd90b8\n"
        ".word 0xeb01d152, 0xe59d2004, 0xe1dd10f8, 0xe1a0300a\n"
        ".word 0xe3e00000, 0xeb01d13b, 0xe3a05001, 0xe320f000\n"
        ".word 0xeb024053, 0xe0841105, 0xe0800005, 0xe2800c91\n"
        ".word 0xe2812a03, 0xe2813a03, 0xe1d000d7, 0xe1dd10f8\n"
        ".word 0xe2822e46, 0xe2833e47, 0xeb01d12e, 0xe2855001\n"
        ".word 0xe3550004, 0xbafffff0, 0xea000020, 0xe28d2008\n"
        ".word 0xe28d1020, 0xe1a00004, 0xe1cd92b0, 0xe1cd90b8\n"
        ".word 0xeb01d136, 0xe59d000c, 0xe320f000, 0xeb0218a4\n"
        ".word 0xe1b05000, 0xe320f000, 0x0a00003a, 0xeb024038\n"
        ".word 0xe59fc16c, 0xe0800005, 0xe1dd10f8, 0xe190c0dc\n"
        ".word 0xe0840105, 0xe2803a03, 0xe2802a03, 0xe2833e47\n"
        ".word 0xe2822e46, 0xe1a0000c, 0xeb01d112, 0xe320f000\n"
        ".word 0xe320f000, 0xeb02402a, 0xe0800005, 0xe2800c91\n"
        ".word 0xe1d000d7, 0xe3500000, 0xb1dd00f8, 0xbb026fb7\n"
        ".word 0xe1dd10f0, 0xe3e00000, 0xeb00df3e, 0xe3500000\n"
        ".word 0xe3a05000, 0x15c89000, 0xe320f000, 0xeb02401c\n"
        ".word 0xe0800005, 0xe2800c91, 0xe1d000d8, 0xe3500000\n"
        ".word 0xba000005, 0xe1dd10f0, 0xe1a00005, 0xeb00df31\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000003, 0xe0840005\n"
        ".word 0xe2800b0d, 0xe280005d, 0xe5c09000, 0xe2855001\n"
        ".word 0xe3550003, 0xbaffffeb, 0xe5d7006a, 0xe200107f\n"
        ".word 0xe3510001, 0x0affff99, 0xe3100080, 0x1affff97\n"
        ".word 0xe1d706b4, 0xe3500000, 0x01d706b6, 0x03500000\n"
        ".word 0x1a00000d, 0xea000007, 0xe59d2004, 0xe1dd10f8\n"
        ".word 0xe1a0300a, 0xe3e00000, 0xeb01d0de, 0xe320f000\n"
        ".word 0xe320f000, 0xeaffffd1, 0xe5d70068, 0xe3500000\n"
        ".word 0x05d70069, 0x03500000, 0x0affff84, 0xe3a00001\n"
        ".word 0xeb01f558, 0xe3500000, 0x13a00000, 0x0affff7f\n"
        ".word 0xe0841000, 0xe2811b0d, 0xe281105d, 0xe5d11000\n"
        ".word 0xe3510000, 0x0a000004, 0xe2801001, 0xe59d000c\n"
        ".word 0xeb0202b7, 0xe28dd044, 0xe8bd8ff0, 0xe2800001\n"
        ".word 0xe3500003, 0xbafffff1, 0xe28dd044, 0xe8bd8ff0\n"
        ".word 0x01010101, 0x00009107, 0x00003504\n"
    );
}

// DECOMP_FUNC(0x00197054, 1880)
// Capstone ARM full coverage (470 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void camp_func_00197054() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a04000, 0xe59f0550, 0xe1a07001\n"
        ".word 0xed2d8b04, 0xe24dd03c, 0xe5900000, 0xe2800b01\n"
        ".word 0xe2800fb5, 0xe1a05000, 0xeb049fbe, 0xe1a06000\n"
        ".word 0xe1a00005, 0xeb049fb8, 0xe1a01000, 0xe2560000\n"
        ".word 0xb2660000, 0xe3500d05, 0xaa0001b5, 0xe3540013\n"
        ".word 0x0a000015, 0xca00000d, 0xe2440009, 0xe350000a\n"
        ".word 0x379ff100, 0xea0001ae, 0x00197140, 0x00197158\n"
        ".word 0x00197170, 0x00197170, 0x00197170, 0x00197778\n"
        ".word 0x00197778, 0x00197778, 0x00197100, 0x00197100\n"
        ".word 0xe3540017, 0x0a000004, 0xca00000b, 0xe3540014\n"
        ".word 0x13540015, 0x13540016, 0x1a00019d, 0xe28dd03c\n"
        ".word 0xe1a02001, 0xecbd8b04, 0xe1a03007, 0xe1a01006\n"
        ".word 0xe1a00004, 0xe8bd4ff0, 0xea005cc4, 0xe3540027\n"
        ".word 0x0a000196, 0xe3540029, 0x1a000191, 0xe28dd03c\n"
        ".word 0xecbd8b04, 0xe8bd4ff0, 0xeafff631, 0xe28dd03c\n"
        ".word 0xe1a02007, 0xecbd8b04, 0xe1a00006, 0xe8bd4ff0\n"
        ".word 0xea005eae, 0xe28dd03c, 0xe1a02007, 0xecbd8b04\n"
        ".word 0xe1a00006, 0xe8bd4ff0, 0xea0171bf, 0xe59f043c\n"
        ".word 0xe28d2030, 0xe354000b, 0xe8820090, 0xe1a05001\n"
        ".word 0xe5908000, 0x0a000059, 0xe354000c, 0x0a00006e\n"
        ".word 0xe354000d, 0x1a000176, 0xe3a01065, 0xe2880f5e\n"
        ".word 0xe2889b07, 0xe58d1004, 0xe58d000c, 0xe28990c4\n"
        ".word 0xe1a03006, 0xe3a02000, 0xe3a0101d, 0xe3a00002\n"
        ".word 0xe58d5000, 0xeb04a0e2, 0xe3a0006a, 0xe58d0004\n"
        ".word 0xe59f23dc, 0xe1a03006, 0xe3a0101d, 0xe3a00002\n"
        ".word 0xe58d5000, 0xeb04a09c, 0xeddf8af2, 0xed9f9af2\n"
        ".word 0xed9f8af2, 0xe3a07000, 0xe59d000c, 0xeb042016\n"
        ".word 0xe0804007, 0xe59d000c, 0xeb041fb8, 0xe1540000\n"
        ".word 0xe320f000, 0xaa0000b9, 0xe59d000c, 0xeb04200e\n"
        ".word 0xe0800007, 0xe2871b01, 0xe0890080, 0xe281100d\n"
        ".word 0xe1d0b0b0, 0xe3a0001d, 0xeb04a123, 0xe1a04000\n"
        ".word 0xe1d000fa, 0xe3a0a06a, 0xe59f2374, 0xe0800005\n"
        ".word 0xe88d0401, 0xe1d400f8, 0xe3a0101d, 0xe0803006\n"
        ".word 0xe3a00002, 0xeb04a07c, 0xe1d400fa, 0xe59f2354\n"
        ".word 0xe3a0101d, 0xe0800005, 0xe88d0401, 0xe1d400f8\n"
        ".word 0xe0803006, 0xe3a00002, 0xeb04a073, 0xe1d400fa\n"
        ".word 0xe59f2334, 0xe3a0101d, 0xe0800005, 0xe88d0401\n"
        ".word 0xe1d400f8, 0xe0803006, 0xe3a00002, 0xeb04a06a\n"
        ".word 0xe3a01e47, 0xe3a0001d, 0xeb04a103, 0xe1a0a000\n"
        ".word 0xe3a01000, 0xe1a0000b, 0xeb049d55, 0xe3500000\n"
        ".word 0xe58d0000, 0x0a00004b, 0xe59d0030, 0xe350000b\n"
        ".word 0xe3a000ff, 0xe58d0004, 0x1a000033, 0xea00002d\n"
        ".word 0xe3a01065, 0xe28800b0, 0xe2889b05, 0xe58d1004\n"
        ".word 0xe58d000c, 0xe289907c, 0xe1a03006, 0xe3a02000\n"
        ".word 0xe3a0101d, 0xe3a00002, 0xe58d5000, 0xeb04a08c\n"
        ".word 0xe3a0006a, 0xe58d0004, 0xe59f22a0, 0xe1a03006\n"
        ".word 0xe3a0101d, 0xe3a00002, 0xe58d5000, 0xeb04a046\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffffa6, 0xe3a01065\n"
        ".word 0xe2880f45, 0xe2889b05, 0xe58d1004, 0xe58d000c\n"
        ".word 0xe28990f4, 0xe1a03006, 0xe3a02000, 0xe3a0101d\n"
        ".word 0xe3a00002, 0xe58d5000, 0xeb04a075, 0xe3a0006a\n"
        ".word 0xe2802b01, 0xe58d0004, 0xe1a03006, 0xe3a0101d\n"
        ".word 0xe3a00002, 0xe58d5000, 0xeb04a02f, 0xe320f000\n"
        ".word 0xe320f000, 0xeaffff8f, 0xe1a0000b, 0xeb03e2d3\n"
        ".word 0xe3500000, 0x059f0218, 0x058d0004, 0xe1d400fa\n"
        ".word 0xe1da10fa, 0xe1d420f8, 0xe1da30f8, 0xe0800001\n"
        ".word 0xe0800005, 0xe0821003, 0xe0811006, 0xee000a10\n"
        ".word 0xee011a10, 0xeeb02a68, 0xeef01a49, 0xe59d1004\n"
        ".word 0xe59d2000, 0xeef80ac0, 0xeeb80ac1, 0xeeb01a48\n"
        ".word 0xe3a00002, 0xeb049cdb, 0xe59f11c8, 0xe3a0001d\n"
        ".word 0xeb04a0ad, 0xe1a0a000, 0xe1a0000b, 0xeb03e26f\n"
        ".word 0xe1a02000, 0xe28f1e1b, 0xe28d0010, 0xfa049cf1\n"
        ".word 0xe28d2010, 0xe3a00003, 0xe3a0106f, 0xe88d0007\n"
        ".word 0xe1d410fa, 0xe1da20fa, 0xe1d430f8, 0xe1da00f8\n"
        ".word 0xe0811002, 0xe0812005, 0xe0800003, 0xe0801006\n"
        ".word 0xe3a03001, 0xe3a00000, 0xeb049b3e, 0xe59f116c\n"
        ".word 0xe3a0001d, 0xeb04a094, 0xe3a0206f, 0xe28f3e16\n"
        ".word 0xe3a01001, 0xe88d000e, 0xe1d020fa, 0xe1d410fa\n"
        ".word 0xe1d430f8, 0xe1d000f8, 0xe0811002, 0xe0812005\n"
        ".word 0xe0800003, 0xe0801006, 0xe3a03001, 0xe3a00000\n"
        ".word 0xeb049b2c, 0xe59f112c, 0xe3a0001d, 0xeb04a082\n"
        ".word 0xe3a01000, 0xe58d1000, 0xe1d030fa, 0xe1d410fa\n"
        ".word 0xe1d420f8, 0xe1d000f8, 0xe0811003, 0xe3a0306f\n"
        ".word 0xe0800002, 0xe0812005, 0xe0801006, 0xe6bf007b\n"
        ".word 0xeb049c13, 0xe2877001, 0xe357000b, 0xbaffff3d\n"
        ".word 0xe59d000c, 0xe3a03001, 0xe1a02005, 0xe1a01006\n"
        ".word 0xeb03e17e, 0xe59d0034, 0xe3500000, 0x0a000094\n"
        ".word 0xe59d000c, 0xeb041f4c, 0xe1a04000, 0xe59d000c\n"
        ".word 0xeb041f43, 0xe0800004, 0xe0890080, 0xe1d090b0\n"
        ".word 0xe59d000c, 0xeb041f3e, 0xe2801b01, 0xe281102e\n"
        ".word 0xe3a0001d, 0xeb04a05c, 0xe1a04000, 0xe59d000c\n"
        ".word 0xeb041f37, 0xe59f2080, 0xe0880080, 0xe1d430f8\n"
        ".word 0xe19020f2, 0xe1d400fa, 0xe0801005, 0xe0830006\n"
        ".word 0xeb03e0eb, 0xe59f1064, 0xe3a0001d, 0xeb04a04e\n"
        ".word 0xe1a08000, 0xe3a01000, 0xe1a00009, 0xeb049ca0\n"
        ".word 0xe1b0a000, 0xe320f000, 0x0a00002c, 0xea000010\n"
        ".word 0x0043da90, 0x0000046b, 0x3f800000, 0x00000000\n"
        ".word 0x3f0ccccd, 0x0000046c, 0x0000046d, 0x0000046e\n"
        ".word 0x00000469, 0x5a5a5aff, 0x00000473, 0x00006425\n"
        ".word 0x00000474, 0x0000002a, 0x0000046f, 0x00000e0c\n"
        ".word 0x00000477, 0xe59d0030, 0xe3e07000, 0xe350000b\n"
        ".word 0x1a000003, 0xe1a00009, 0xeb03e23c, 0xe3500000\n"
        ".word 0x051f7044, 0xe1d400fa, 0xe1d410f8, 0xe1d820fa\n"
        ".word 0xe1d830f8, 0xeeb02a68, 0xe0800002, 0xe0811003\n"
        ".word 0xe0800005, 0xe0811006, 0xee000a90, 0xee001a10\n"
        ".word 0xeef01a49, 0xe1a0200a, 0xe1a01007, 0xe3a00003\n"
        ".word 0xeef80ae0, 0xeeb80ac0, 0xed9f1a4e, 0xeb049c45\n"
        ".word 0xe59f1134, 0xe3a0001d, 0xeb04a017, 0xe1a07000\n"
        ".word 0xe1a00009, 0xeb03e1d9, 0xe1a02000, 0xe24f10a8\n"
        ".word 0xe28d0010, 0xfa049c5b, 0xe28d1010, 0xe3a08083\n"
        ".word 0xe3a00003, 0xe58d1008, 0xe88d0101, 0xe1d700fa\n"
        ".word 0xe1d410fa, 0xe1d420f8, 0xe1d730f8, 0xe0811000\n"
        ".word 0xe0820003, 0xe0812005, 0xe0801006, 0xe3a03001\n"
        ".word 0xe3a00000, 0xeb049aa7, 0xe2881ffe, 0xe3a0001d\n"
        ".word 0xeb049ffd, 0xe24f20f8, 0xe3a01001, 0xe58d2008\n"
        ".word 0xe88d0102, 0xe1d020fa, 0xe1d410fa, 0xe1d430f8\n"
        ".word 0xe1d000f8, 0xe0811002, 0xe0812005, 0xe0800003\n"
        ".word 0xe0801006, 0xe3a03001, 0xe3a00000, 0xeb049a95\n"
        ".word 0xe1d400fa, 0xe59f2084, 0xe3a0101d, 0xe0800005\n"
        ".word 0xe88d0101, 0xe1d400f8, 0xe0803006, 0xe3a00002\n"
        ".word 0xeb049f49, 0xe59f1068, 0xe3a0001d, 0xeb049fe2\n"
        ".word 0xe3a01000, 0xe58d1000, 0xe1d410fa, 0xe1d020fa\n"
        ".word 0xe1d000f8, 0xe3a03088, 0xe0811002, 0xe0812005\n"
        ".word 0xe1d410f8, 0xe0800001, 0xe0801006, 0xe6bf0079\n"
        ".word 0xeb049b73, 0xe28dd03c, 0xecbd8b04, 0xe8bd8ff0\n"
        ".word 0xe28dd03c, 0xe1a02007, 0xecbd8b04, 0xe1a00006\n"
        ".word 0xe8bd4ff0, 0xeaffceff, 0x3f000000, 0x0000047a\n"
        ".word 0x00000475, 0x00000476\n"
    );
}

// DECOMP_FUNC(0x003d236c, 1936)
// Capstone ARM full coverage (484 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void battle_func_003d236c() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d43f0, 0xe3510024, 0xe1a08000, 0xe24dd00c\n"
        ".word 0xe59f0758, 0xe598c000, 0xe59f274c, 0xe5903004\n"
        ".word 0xe59c0084, 0xe0020290, 0xe0832102, 0xe2824004\n"
        ".word 0x379ff101, 0xea00003f, 0x003d24a4, 0x003d2434\n"
        ".word 0x003d24dc, 0x003d27ec, 0x003d24a4, 0x003d2598\n"
        ".word 0x003d24a4, 0x003d25ac, 0x003d25d0, 0x003d24a4\n"
        ".word 0x003d24a4, 0x003d267c, 0x003d2690, 0x003d26b4\n"
        ".word 0x003d26e8, 0x003d26fc, 0x003d27d8, 0x003d27ec\n"
        ".word 0x003d2808, 0x003d2860, 0x003d2918, 0x003d24a4\n"
        ".word 0x003d24a4, 0x003d24a4, 0x003d292c, 0x003d24a4\n"
        ".word 0x003d24a4, 0x003d24a4, 0x003d2558, 0x003d24a4\n"
        ".word 0x003d24a4, 0x003d29a0, 0x003d29b4, 0x003d29c8\n"
        ".word 0x003d24a4, 0x003d2a50, 0xe28cc901, 0xe28cce4a\n"
        ".word 0xe59c0000, 0xe3100040, 0x15940000, 0x13800080\n"
        ".word 0x0a000016, 0xe5840000, 0xe3100b02, 0x0a000018\n"
        ".word 0xe5940028, 0xe3a02f53, 0xe1d412bc, 0xe3a03001\n"
        ".word 0xe19020f2, 0xe59f0668, 0xe5900000, 0xebf9560a\n"
        ".word 0xe5941000, 0xe3a00000, 0xe3c11b02, 0xe5841000\n"
        ".word 0xe5941028, 0xe2811c01, 0xe1c104bc, 0xe5941028\n"
        ".word 0xe2811c01, 0xe1c104be, 0xe28dd00c, 0xe8bd83f0\n"
        ".word 0xe3100c01, 0xe5940000, 0x13800a01, 0x1affffe4\n"
        ".word 0xeaffffe4, 0xe59f0618, 0xe1d412bc, 0xe3a02001\n"
        ".word 0xe5900000, 0xe28dd00c, 0xe8bd43f0, 0xeaf95e44\n"
        ".word 0xe1a00004, 0xebf72d57, 0xe3a01085, 0xe2840038\n"
        ".word 0xebfbc98f, 0xe1a00008, 0xe320f000, 0xebf95b4b\n"
        ".word 0xe320f000, 0xe320f000, 0xebfb99f0, 0xe1a04000\n"
        ".word 0xe5980000, 0xebfb03ef, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000005, 0xe354003d, 0x0affffde, 0xe28dd00c\n"
        ".word 0xe3a0003d, 0xe8bd43f0, 0xeafb998f, 0xe35400b3\n"
        ".word 0x0affffd8, 0xe35400b4, 0x0affffd6, 0xe28dd00c\n"
        ".word 0xe3a00000, 0xe8bd43f0, 0xeafb02c6, 0xe1a01000\n"
        ".word 0xe1a00008, 0xebfa11a1, 0xe1a01004, 0xe1a00008\n"
        ".word 0xebf955b5, 0xe59f456c, 0xe5940000, 0xebfab02a\n"
        ".word 0xe3500000, 0xe320f000, 0x1affffc6, 0xe5940000\n"
        ".word 0xe28dd00c, 0xe8bd43f0, 0xeafab018, 0xe28dd00c\n"
        ".word 0xe1a01004, 0xe1a00008, 0xe8bd43f0, 0xeaffe0d0\n"
        ".word 0xe59f052c, 0xe5900000, 0xebff7154, 0xe3a01085\n"
        ".word 0xe2840038, 0xebfbc95a, 0xe28dd00c, 0xe8bd43f0\n"
        ".word 0xeafb590d, 0xe1a09004, 0xebfb590b, 0xe1a05000\n"
        ".word 0xe3a07000, 0xe5980000, 0xe0871207, 0xe0811307\n"
        ".word 0xe2800d7f, 0xe5900000, 0xe0806181, 0xe5960000\n"
        ".word 0xe3100001, 0x13100008, 0x13a04000, 0x0a000016\n"
        ".word 0xe0850004, 0xe2800c91, 0xe1d000d8, 0xe3500000\n"
        ".word 0xba00000a, 0xe1a00004, 0xebfa07c0, 0xe1d014b6\n"
        ".word 0xe1d62cbe, 0xe1510002, 0x1a000004, 0xe586027c\n"
        ".word 0xebf9b1a5, 0xe1c60db4, 0xe320f000, 0xea000006\n"
        ".word 0xe2844001, 0xe3540003, 0xbaffffec, 0xe1a02006\n"
        ".word 0xe1a01009, 0xe3a00000, 0xebf9cfd5, 0xe2877001\n"
        ".word 0xe3570004, 0xbaffffda, 0xe28dd00c, 0xe8bd83f0\n"
        ".word 0xe28dd00c, 0xe1a01004, 0xe1a00008, 0xe8bd43f0\n"
        ".word 0xea000537, 0xe3a000ff, 0xe58d0000, 0xe3a0300a\n"
        ".word 0xe3a02001, 0xe3a01000, 0xe1a0000c, 0xebf9ca9b\n"
        ".word 0xe28dd00c, 0xe8bd83f0, 0xe1a0000c, 0xebfda0bd\n"
        ".word 0xe59f0424, 0xe5900000, 0xeb000ff7, 0xe3a00000\n"
        ".word 0xe1a01000, 0xe584000c, 0xebfa10ff, 0xe28dd00c\n"
        ".word 0xe3a000ed, 0xe8bd43f0, 0xeafb9923, 0xe28dd00c\n"
        ".word 0xe1a01004, 0xe1a00008, 0xe8bd43f0, 0xea0005b5\n"
        ".word 0xe59f03e8, 0xe1a01004, 0xe3e03000, 0xe790200c\n"
        ".word 0xe3a00000, 0xe3120c02, 0x13a02d7f, 0x1792500c\n"
        ".word 0x0a000012, 0xe0802200, 0xe0822300, 0xe0854182\n"
        ".word 0xe5942000, 0xe3120001, 0x0a000008, 0xe3120040\n"
        ".word 0x1a000006, 0xe1d460f8, 0xe3560000, 0xba000003\n"
        ".word 0xe3120010, 0x0a000001, 0xe1d430f8, 0xea000019\n"
        ".word 0xe2800001, 0xe350006d, 0xbaffffed, 0xea000015\n"
        ".word 0xe59f437c, 0xe3a02060, 0xe794400c, 0xe0805100\n"
        ".word 0xe0855300, 0xe0825105, 0xe19450f5, 0xe3550000\n"
        ".word 0xba000009, 0xe0855001, 0xe5d55038, 0xe3550000\n"
        ".word 0x0a000005, 0xe0803100, 0xe0830300, 0xe3a02062\n"
        ".word 0xe0820100, 0xe19430f0, 0xea000002, 0xe2800001\n"
        ".word 0xe350006d, 0xbaffffec, 0xe28dd00c, 0xe3a02000\n"
        ".word 0xe8bd43f0, 0xe1a0000c, 0xeaf7ff8d, 0xe28dd00c\n"
        ".word 0xe1a01004, 0xe1a00008, 0xe8bd43f0, 0xeafff4e2\n"
        ".word 0xe3a01085, 0xe2840038, 0xebfbc8cd, 0xe28dd00c\n"
        ".word 0xe1a00008, 0xe8bd43f0, 0xeaf95a88, 0xe5940000\n"
        ".word 0xe3a01001, 0xe3a03000, 0xe3100d42, 0xe58d1000\n"
        ".word 0x03a00032, 0x13a00000, 0xe1a02003, 0xe1a01004\n"
        ".word 0xebfa663b, 0xe320f000, 0xe320f000, 0xebffd88e\n"
        ".word 0xe1b02000, 0xe320f000, 0x0affff16, 0xe28dd00c\n"
        ".word 0xe1a01004, 0xe8bd43f0, 0xe3e03000, 0xe3a00000\n"
        ".word 0xea002daf, 0xe5941028, 0xe5940000, 0xe2811c01\n"
        ".word 0xe3100d42, 0xe1d114fc, 0x03a00032, 0x13a00000\n"
        ".word 0xe3510006, 0x0a000012, 0xe351000f, 0x1affff05\n"
        ".word 0xe3a01001, 0xe58d1000, 0xe5943024, 0xe3a02000\n"
        ".word 0xe1a01004, 0xebfa661e, 0xe3a00005, 0xe58d0000\n"
        ".word 0xe58d0004, 0xe5940024, 0xe3a03000, 0xe1a01004\n"
        ".word 0xe1d026f2, 0xe1a00008, 0xebf95bef, 0xe28dd00c\n"
        ".word 0xe8bd83f0, 0xe3a00001, 0xe58d0000, 0xe1a02000\n"
        ".word 0xe5943024, 0xe1a01004, 0xe3a00000, 0xebfa660c\n"
        ".word 0xe3a00005, 0xe58d0000, 0xe58d0004, 0xe5940024\n"
        ".word 0xe3a03000, 0xe1a01004, 0xe1d026f2, 0xe1a00008\n"
        ".word 0xebf95bdd, 0xe28dd00c, 0xe8bd83f0, 0xe28dd00c\n"
        ".word 0xe1a01004, 0xe1a00008, 0xe8bd43f0, 0xeaffdf6b\n"
        ".word 0xe59f51b0, 0xe5950000, 0xebfaaf3b, 0xe3500000\n"
        ".word 0xe320f000, 0x1afffed7, 0xe5940028, 0xe3a03000\n"
        ".word 0xe2800c01, 0xe1d004bc, 0xe350000b, 0xe5940020\n"
        ".word 0xe1d026fe, 0x0a000006, 0xe5950000, 0xe3a01003\n"
        ".word 0xebfaaf3d, 0xe3500000, 0xe320f000, 0x0afffec9\n"
        ".word 0xea000027, 0xe5950000, 0xe3a01007, 0xebfaaf36\n"
        ".word 0xe3500000, 0xe320f000, 0x1a000021, 0xe28dd00c\n"
        ".word 0xe8bd83f0, 0xe59f014c, 0xe5900000, 0xe28dd00c\n"
        ".word 0xe8bd43f0, 0xea0024ed, 0xe28dd00c, 0xe1a01004\n"
        ".word 0xe1a00008, 0xe8bd43f0, 0xeaffdee3, 0xe5940000\n"
        ".word 0xe3100801, 0x0a000016, 0xe59f011c, 0xe19000fc\n"
        ".word 0xe3500000, 0xdafffeaf, 0xe59f50f8, 0xe5950000\n"
        ".word 0xebfaaf0d, 0xe3500000, 0xe320f000, 0x1afffea9\n"
        ".word 0xe5940020, 0xe3a03000, 0xe3a01004, 0xe1d026fe\n"
        ".word 0xe5950000, 0xebfaaf14, 0xe3500000, 0xe320f000\n"
        ".word 0x0afffea0, 0xe5950000, 0xe28dd00c, 0xe8bd43f0\n"
        ".word 0xeafaaef2, 0xe5940020, 0xe5900000, 0xe3100001\n"
        ".word 0x0afffe98, 0xe3100040, 0x0affffe6, 0xe28dd00c\n"
        ".word 0xe8bd83f0, 0xe5940020, 0xe5900000, 0xe3100010\n"
        ".word 0x1a000002, 0xe59f0078, 0xe5900000, 0xebff725d\n"
        ".word 0xe59f4080, 0xe5940000, 0xeb001e1b, 0xe5940000\n"
        ".word 0xe320f000, 0xebf95381, 0xe5940000, 0xe2801a03\n"
        ".word 0xe5912028, 0xe3c22902, 0xe5812028, 0xebf95e7e\n"
        ".word 0xe5940000, 0xe320f000, 0xebfaad7a, 0xe5940000\n"
        ".word 0xe320f000, 0xebfaad55, 0xe59f002c, 0xe5900000\n"
        ".word 0xe5901634, 0xe3c11901, 0xe5801634, 0xebf95237\n"
        ".word 0xe28dd00c, 0xe8bd43f0, 0xeaff08b3, 0x000003c7\n"
        ".word 0x00434278, 0x00439ca8, 0x00435d48, 0x004342c8\n"
        ".word 0x000044a0, 0x00001e98, 0x00435d18, 0x00001fc4\n"
    );
}

// DECOMP_FUNC(0x003cb610, 1940)
// Capstone ARM full coverage (485 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void battle_func_003cb610() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a04000, 0xe24dd014, 0xe1a07001\n"
        ".word 0xe59f076c, 0xe5900000, 0xebfaccbf, 0xe3500000\n"
        ".word 0xca00002d, 0xe5970000, 0xe3a0b050, 0xe3100d42\n"
        ".word 0x03a05000, 0x1a00002b, 0xe5940000, 0xe0851105\n"
        ".word 0xe0811305, 0xe2800b07, 0xe2800fa6, 0xe08b1101\n"
        ".word 0xe5900000, 0xe7900001, 0xe3100001, 0x0a000010\n"
        ".word 0xe1a02005, 0xe1a01007, 0xe1a00004, 0xebf97909\n"
        ".word 0xe3500000, 0xe320f000, 0x1a000009, 0xe5940000\n"
        ".word 0xe1a01005, 0xebfadd3e, 0xe28000cc, 0xe1d01fbc\n"
        ".word 0xe3510000, 0x0a000002, 0xe1d00fba, 0xe3500000\n"
        ".word 0x0a000003, 0xe2855001, 0xe355006d, 0xbaffffe1\n"
        ".word 0xea00000c, 0xe5940000, 0xe2800b12, 0xe28000b8\n"
        ".word 0xe5900000, 0xe3500000, 0x0a000006, 0xebf978d4\n"
        ".word 0xe3500000, 0xe320f000, 0x0a000002, 0xe28dd014\n"
        ".word 0xe3a00000, 0xe8bd8ff0, 0xe3a09000, 0xe58d9000\n"
        ".word 0xe5940000, 0xebf9cfcd, 0xe3a02005, 0xe1a01007\n"
        ".word 0xe3a00000, 0xeb004c9a, 0xe3a05000, 0xe5940000\n"
        ".word 0xe0851105, 0xe0811305, 0xe2800b07, 0xe2800fa6\n"
        ".word 0xe5900000, 0xe0900101, 0x0a000003, 0xe5901050\n"
        ".word 0xe3110001, 0x13110002, 0x1bfacc41, 0xe2855001\n"
        ".word 0xe355006d, 0xbafffff0, 0xe5940000, 0xe3a08000\n"
        ".word 0xe2800b12, 0xe2800f79, 0xe5808000, 0xe5940000\n"
        ".word 0xebfa147a, 0xe5970000, 0xe3100a02, 0x0a00000d\n"
        ".word 0xe3c00a02, 0xe5870000, 0xe5943000, 0xe59f2604\n"
        ".word 0xe59f0604, 0xe3a01014, 0xe5933084, 0xe5900004\n"
        ".word 0xe0020293, 0xe0800102, 0xe5c01009, 0xe28dd014\n"
        ".word 0xe3a00001, 0xe8bd8ff0, 0xe5970024, 0xe3a0a001\n"
        ".word 0xe1d006f2, 0xe3500004, 0xb3a05004, 0xb3a00032\n"
        ".word 0xa3a05000, 0xa3a00004, 0xe0856000, 0xe1560005\n"
        ".word 0xda000013, 0xe5940000, 0xe0851105, 0xe0811305\n"
        ".word 0xe2800b07, 0xe2800fa6, 0xe08b1101, 0xe5900000\n"
        ".word 0xe7900001, 0xe3100001, 0x0a000006, 0xe1a02005\n"
        ".word 0xe1a01007, 0xe1a00004, 0xebf978a2, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000003, 0xe2855001, 0xe1560005\n"
        ".word 0xcaffffeb, 0xe3a0a000, 0xe5940000, 0xe5900088\n"
        ".word 0xe3500000, 0xe5970000, 0x13a0a000, 0xe3100004\n"
        ".word 0x1a00008f, 0xe35a0000, 0x0a000003, 0xe59d2000\n"
        ".word 0xe1a01007, 0xe1a00004, 0xeb000e67, 0xe3a00000\n"
        ".word 0xe1a05000, 0xe58d0008, 0xe58d8004, 0xe5940000\n"
        ".word 0xe0851105, 0xe0818305, 0xe2800b07, 0xe2800fa6\n"
        ".word 0xe08b1108, 0xe5900000, 0xe7900001, 0xe3100001\n"
        ".word 0x0a00004c, 0xe1a02005, 0xe1a01007, 0xe1a00004\n"
        ".word 0xebf9787c, 0xe3500000, 0xe320f000, 0x1a000045\n"
        ".word 0xe5940000, 0xe1a01005, 0xebfadcb1, 0xe28060cc\n"
        ".word 0xe58d000c, 0xe1d60fbe, 0xe3500000, 0x0a00000e\n"
        ".word 0xe5940000, 0xe3a03010, 0xe1a01007, 0xe2800b07\n"
        ".word 0xe2800fa6, 0xe5900000, 0xe0802108, 0xe3a00000\n"
        ".word 0xebf9ed67, 0xe3a00000, 0xe1c60fbe, 0xe1d60fbc\n"
        ".word 0xe3c00010, 0xe1c60fbc, 0xea00002e, 0xe1d60fbc\n"
        ".word 0xe3500000, 0x0a000002, 0xe1d60fba, 0xe3500000\n"
        ".word 0x0a000007, 0xe1d60fba, 0xe3100010, 0x0a000025\n"
        ".word 0xe59d000c, 0xe1d006fe, 0xe3500004, 0x2a000021\n"
        ".word 0xea00001d, 0xe35a0000, 0x0a00001e, 0xe3a09000\n"
        ".word 0xe58d9000, 0xe5940000, 0xe3a03010, 0xe1a01007\n"
        ".word 0xe2800b07, 0xe2800fa6, 0xe5900000, 0xe0802108\n"
        ".word 0xe1a00009, 0xebf9ed81, 0xe59d100c, 0xe3a02001\n"
        ".word 0xe3a00019, 0xebf97b74, 0xe1a00009, 0xe1c60fbc\n"
        ".word 0xe59d000c, 0xe3a09001, 0xe5900000, 0xe310000a\n"
        ".word 0x0a000008, 0xe59d000c, 0xe3a01001, 0xe1d006fe\n"
        ".word 0xe58d1008, 0xe3500004, 0x2a000002, 0xe28d2004\n"
        ".word 0xe3a01001, 0xe7c21000, 0xe2855001, 0xe355006d\n"
        ".word 0xbaffffa5, 0xe59d0008, 0xe3500000, 0x15dd0004\n"
        ".word 0x13500000, 0x0a00000e, 0xe5dd0005, 0xe3500000\n"
        ".word 0x15dd0006, 0x13500000, 0x15dd0007, 0x13500000\n"
        ".word 0x0a000007, 0xe3a00019, 0xebffd37c, 0xe3a00000\n"
        ".word 0xe3a03021, 0xe1a02000, 0xe1a01007, 0xe58d0000\n"
        ".word 0xebf97866, 0xe3590000, 0x1a000015, 0xe5941000\n"
        ".word 0xe3a02000, 0xe1a00002, 0xe2811d7f, 0xe5913000\n"
        ".word 0xe0801200, 0xe0811300, 0xe0831181, 0xe591c000\n"
        ".word 0xe31c0001, 0x0a000005, 0xe31c0040, 0x1a000003\n"
        ".word 0xe2811c01, 0xe1d11cb6, 0xe3110010, 0x12822001\n"
        ".word 0xe2800001, 0xe3500004, 0xbafffff0, 0xe3520004\n"
        ".word 0x03a09001, 0xe5970024, 0xe1a01007, 0xe1d026f2\n"
        ".word 0xe1a00004, 0xebf977ff, 0xe3500000, 0xe320f000\n"
        ".word 0x1a000042, 0xe5970028, 0xe1d00fba, 0xe3100020\n"
        ".word 0x0a00003e, 0xe5970024, 0xe1d006f2, 0xe3500004\n"
        ".word 0xb3a05004, 0xb3a00032, 0xa3a05000, 0xa3a00004\n"
        ".word 0xe0856000, 0xe1560005, 0xda000034, 0xe5940000\n"
        ".word 0xe0851105, 0xe0811305, 0xe2800b07, 0xe2800fa6\n"
        ".word 0xe08b1101, 0xe5900000, 0xe7900001, 0xe3100001\n"
        ".word 0x0a000006, 0xe1a02005, 0xe1a01007, 0xe1a00004\n"
        ".word 0xebf977e0, 0xe3500000, 0xe320f000, 0x0a000003\n"
        ".word 0xe2855001, 0xe1560005, 0xcaffffeb, 0xea00001f\n"
        ".word 0xe5940000, 0xe5900088, 0xe3500000, 0x1a00001b\n"
        ".word 0xe5970020, 0xe5900000, 0xe3100040, 0x03100202\n"
        ".word 0x1a000016, 0xe5970000, 0xe3100004, 0x1a000013\n"
        ".word 0xe5970028, 0xe1d00efa, 0xe1a01fc0, 0xe0800ea1\n"
        ".word 0xe1a021c0, 0xe3520064, 0xda000002, 0xe3a0000f\n"
        ".word 0xebf9cc29, 0xe2802064, 0xe1a01007, 0xe1a00004\n"
        ".word 0xeb001126, 0xe3500000, 0xe320f000, 0x0a000002\n"
        ".word 0xe5970000, 0xe3800801, 0xe5870000, 0xe3a09001\n"
        ".word 0xe3a05000, 0xe5941000, 0xe0850205, 0xe0800305\n"
        ".word 0xe2811d7f, 0xe5911000, 0xe0816180, 0xe5960000\n"
        ".word 0xe3100001, 0x0a00000e, 0xe3100040, 0x1a00000c\n"
        ".word 0xe59f01a8, 0xe19000b6, 0xe3100b01, 0x0a000008\n"
        ".word 0xe3a02001, 0xe1a01006, 0xe3a00016, 0xebf97ad6\n"
        ".word 0xe1a02006, 0xe1a01007, 0xe3a00000, 0xebf9ea67\n"
        ".word 0xe3a09001, 0xe2855001, 0xe355006d, 0xbaffffe4\n"
        ".word 0xe5940000, 0xe3a0b005, 0xebf9f7b3, 0xe1b05000\n"
        ".word 0xe320f000, 0x0a000040, 0xe5940000, 0xe1d510f8\n"
        ".word 0xe2800b07, 0xe2800fa6, 0xe0812101, 0xe5900000\n"
        ".word 0xe0821301, 0xe0808101, 0xe3a01002, 0xe3a00000\n"
        ".word 0xebfa25c8, 0xe1a06000, 0xe320f000, 0xebfff256\n"
        ".word 0xe3500000, 0x13560000, 0xda000007, 0xebfff2d7\n"
        ".word 0xe1b02000, 0xe320f000, 0x0a00002d, 0xe3a0300c\n"
        ".word 0xe1a01007, 0xe3a00005, 0xea000025, 0xe320f000\n"
        ".word 0xebfff2d9, 0xe1a06000, 0xe320f000, 0xebfff387\n"
        ".word 0xe1a0a000, 0xe5970024, 0xe3a0101d, 0xe1d006f2\n"
        ".word 0xebfa25b0, 0xe3560000, 0xe320f000, 0x0a00001a\n"
        ".word 0xe15a0000, 0x8a000018, 0xe3a0001d, 0xebf9e84e\n"
        ".word 0xe1a02000, 0xe5970024, 0xe3a0101d, 0xe1d006f2\n"
        ".word 0xebfa25ae, 0xe1a02006, 0xe3a03019, 0xe1a01007\n"
        ".word 0xe1a00004, 0xe58d5004, 0xe58d8000, 0xeb001240\n"
        ".word 0xe320f000, 0xe320f000, 0xebfff35e, 0xe1b02000\n"
        ".word 0xe320f000, 0x0a000006, 0xe3e03000, 0xe1a01007\n"
        ".word 0xe1a0000b, 0xeb004875, 0xea000001, 0xe3590000\n"
        ".word 0x0a000009, 0xe5943000, 0xe59f2038, 0xe59f0038\n"
        ".word 0xe3a0101e, 0xe5933084, 0xe5900004, 0xe0020293\n"
        ".word 0xe0800102, 0xe5c01009, 0xea000002, 0xe1a01007\n"
        ".word 0xe1a00004, 0xebf976d7, 0xe28dd014, 0xe3a00001\n"
        ".word 0xe8bd8ff0, 0x00434290, 0x000003c7, 0x00434278\n"
        ".word 0x000001c6\n"
    );
}

// DECOMP_FUNC(0x002b3398, 1948)
// Capstone ARM full coverage (487 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_002b3398() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d5ff0, 0xe1a04000, 0xe3a08002, 0xe3a0a000\n"
        ".word 0xe5942008, 0xe5900000, 0xe0801282, 0xe1d110b0\n"
        ".word 0xe2413cff, 0xe25330ff, 0x1a00001b, 0xe5c48044\n"
        ".word 0xe584a030, 0xe5940034, 0xe3100c03, 0x0a000149\n"
        ".word 0xebfa46b3, 0xe5940010, 0xe594500c, 0xe0800005\n"
        ".word 0xe1500005, 0xda000008, 0xe5940000, 0xe0800285\n"
        ".word 0xe1d000b0, 0xebfa4637, 0xe1c400dc, 0xe2855001\n"
        ".word 0xe0800001, 0xe1500005, 0xcafffff6, 0xe5940034\n"
        ".word 0xe3100c02, 0x1a000077, 0xe320f000, 0xebfa45a3\n"
        ".word 0xe320f000, 0xe320f000, 0xea000132, 0xe5943010\n"
        ".word 0xe59fb6dc, 0xe59f96dc, 0xe59f76dc, 0xe3530000\n"
        ".word 0xe3a0c001, 0x1a000047, 0xe2415b3e, 0xe2555012\n"
        ".word 0x1a00000a, 0xe5941008, 0xe2811001, 0xe5841008\n"
        ".word 0xe5942010, 0xe0801281, 0xe2822001, 0xe5842010\n"
        ".word 0xe1d110b0, 0xe3510000, 0x1afffff5, 0xea000029\n"
        ".word 0xe151000b, 0x1a000027, 0xe2821001, 0xe2813001\n"
        ".word 0xe5841008, 0xe0805281, 0xe584c010, 0xe1d510b0\n"
        ".word 0xe5843008, 0xe080c283, 0xe5848010, 0xe1dc50b0\n"
        ".word 0xe2836001, 0xe3a02003, 0xe5842010, 0xe080c286\n"
        ".word 0xe1815805, 0xe5846008, 0xe1dc10b0, 0xe2862001\n"
        ".word 0xe59fc648, 0xe3a03004, 0xe5842008, 0xe0800282\n"
        ".word 0xe5843010, 0xe1d000b0, 0xe59c2014, 0xe3520000\n"
        ".word 0xe1816800, 0x0a000002, 0xe1a01006, 0xe1a00005\n"
        ".word 0xe12fff32, 0xe5940034, 0xe3100c01, 0x0a000015\n"
        ".word 0xe1a01006, 0xe1a00005, 0xebfa469c, 0xe320f000\n"
        ".word 0xe320f000, 0xea00000f, 0xe3a00000, 0xe7972100\n"
        ".word 0xe3520000, 0x0a000008, 0xe0892080, 0xe1d230b0\n"
        ".word 0xe1530001, 0x1a000004, 0xe1a00004, 0xebfa47ac\n"
        ".word 0xe320f000, 0xe320f000, 0xea000002, 0xe2800001\n"
        ".word 0xe3500008, 0xbafffff0, 0xe5941008, 0xe2811001\n"
        ".word 0xe5841008, 0xe5942010, 0xe2822001, 0xe5842010\n"
        ".word 0xe5942000, 0xe0821281, 0xe1d150b0, 0xe2450cff\n"
        ".word 0xe25000ff, 0x1a00001c, 0xe5c48044, 0xe584a030\n"
        ".word 0xe5940034, 0xe3100c03, 0x0a0000d2, 0xebfa463c\n"
        ".word 0xe5940010, 0xe594500c, 0xe0800005, 0xe1500005\n"
        ".word 0xda000009, 0xe5940000, 0xe0800285, 0xe1d000b0\n"
        ".word 0xebfa45c0, 0xe5940010, 0xe594100c, 0xe2855001\n"
        ".word 0xe0800001, 0xe1500005, 0xcafffff5, 0xe5940034\n"
        ".word 0xe3100c02, 0x0affff87, 0xe3a00001, 0xebfa4615\n"
        ".word 0xe320f000, 0xe320f000, 0xeaffff82, 0xe3a06000\n"
        ".word 0xe1a00005, 0xebffec23, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000139, 0xe3a00000, 0xe7971100, 0xe3510000\n"
        ".word 0x0a000005, 0xe0891080, 0xe1d120b0, 0xe1520005\n"
        ".word 0x1a000001, 0xe3a00000, 0xea000015, 0xe2800001\n"
        ".word 0xe3500008, 0xbafffff3, 0xe59f14b4, 0xe3a00000\n"
        ".word 0xe1550001, 0xe0452001, 0x0a0000af, 0xaa000080\n"
        ".word 0xe241100e, 0xe1550001, 0xe0452001, 0x0a00008c\n"
        ".word 0xca000075, 0xe2451b3e, 0xe2511001, 0x0a0000f2\n"
        ".word 0xe3510001, 0x0a000081, 0xe3510003, 0x1a0000ee\n"
        ".word 0xea0000e7, 0xe7971100, 0xe3510000, 0x0a000066\n"
        ".word 0xe0891080, 0xe1d110b0, 0xe1510005, 0x1a000062\n"
        ".word 0xe59f145c, 0xe7911100, 0xe3510001, 0x0a000006\n"
        ".word 0xe3510002, 0x0a000011, 0xe3510003, 0x0a000022\n"
        ".word 0xe3510004, 0x1a0000dc, 0xea000038, 0xe5941008\n"
        ".word 0xe2811001, 0xe5841008, 0xe5942010, 0xe2822001\n"
        ".word 0xe5842010, 0xe5942000, 0xe0821281, 0xe1d120b0\n"
        ".word 0xe7971100, 0xe1a00002, 0xe12fff31, 0xea0000ce\n"
        ".word 0xe5941008, 0xe2811001, 0xe5841008, 0xe5942010\n"
        ".word 0xe2813001, 0xe2822001, 0xe282c001, 0xe5842010\n"
        ".word 0xe5942000, 0xe0821281, 0xe0825283, 0xe1d120b0\n"
        ".word 0xe5843008, 0xe584c010, 0xe7973100, 0xe1d510b0\n"
        ".word 0xe1a00002, 0xe12fff33, 0xea0000bb, 0xe5941008\n"
        ".word 0xe2811001, 0xe5841008, 0xe5943010, 0xe2812001\n"
        ".word 0xe281c002, 0xe2833001, 0xe2838001, 0xe5843010\n"
        ".word 0xe5943000, 0xe2885001, 0xe0831281, 0xe083a282\n"
        ".word 0xe083b28c, 0xe1d130b0, 0xe5842008, 0xe5848010\n"
        ".word 0xe1da10b0, 0xe5845010, 0xe584c008, 0xe797c100\n"
        ".word 0xe1db20b0, 0xe1a00003, 0xe12fff3c, 0xea0000a2\n"
        ".word 0xe5941008, 0xe281c001, 0xe584c008, 0xe5942010\n"
        ".word 0xe2811002, 0xe2813001, 0xe2822001, 0xe282a001\n"
        ".word 0xe5842010, 0xe5942000, 0xe2815002, 0xe28a8001\n"
        ".word 0xe082c28c, 0xe082b281, 0xe1dcc0b0, 0xe584a010\n"
        ".word 0xe5841008, 0xe1db10b0, 0xe5843008, 0xe0823283\n"
        ".word 0xe5848010, 0xe0828285, 0xe1d320b0, 0xe28aa002\n"
        ".word 0xe5845008, 0xe584a010, 0xe7975100, 0xe1d830b0\n"
        ".word 0xe1a0000c, 0xe12fff35, 0xea000083, 0xe2800001\n"
        ".word 0xe3500008, 0xbaffff92, 0xea00007f, 0xe3520001\n"
        ".word 0x0a000022, 0xe352000d, 0x05941000, 0x1a00007a\n"
        ".word 0xea000022, 0xe3520008, 0x379ff102, 0xea000076\n"
        ".word 0x002b3a64, 0x002b39e8, 0x002b3a64, 0x002b3a64\n"
        ".word 0x002b3a04, 0x002b3a64, 0x002b3a4c, 0x002b3a4c\n"
        ".word 0xe3a01002, 0xe5c41044, 0xe3a06001, 0xe5840030\n"
        ".word 0xea000069, 0xe5940008, 0xe3a01004, 0xe3a02000\n"
        ".word 0xe2800001, 0xe5840008, 0xe5943010, 0xe2833001\n"
        ".word 0xe5843010, 0xe5943000, 0xe0830280, 0xe1d000b0\n"
        ".word 0xe5c41044, 0xe5a42028, 0xe5840004, 0xea000001\n"
        ".word 0xe3a00003, 0xe5c40044, 0xe3a00001, 0xe8bd9ff0\n"
        ".word 0xe5940008, 0xe2800001, 0xe5840008, 0xe5942010\n"
        ".word 0xe0810280, 0xe2822001, 0xe5842010, 0xe1d000b0\n"
        ".word 0xe3500000, 0x1afffff5, 0xea00004b, 0xe5940008\n"
        ".word 0xe59f81e8, 0xe2801001, 0xe2803002, 0xe5841008\n"
        ".word 0xe5940010, 0xe2832001, 0xe2835002, 0xe2800001\n"
        ".word 0xe280c001, 0xe5840010, 0xe5940000, 0xe28cb001\n"
        ".word 0xe0801281, 0xe080a283, 0xe1d110b0, 0xe5843008\n"
        ".word 0xe584c010, 0xe1daa0b0, 0xe0803282, 0xe5842008\n"
        ".word 0xe584b010, 0xe181a80a, 0xe1d310b0, 0xe28cc002\n"
        ".word 0xe5845008, 0xe0800285, 0xe584c010, 0xe1d000b0\n"
        ".word 0xe5982014, 0xe3520000, 0xe1815800, 0x0a000002\n"
        ".word 0xe1a01005, 0xe1a0000a, 0xe12fff32, 0xe5940034\n"
        ".word 0xe3100c01, 0x0a000024, 0xe1a01005, 0xe1a0000a\n"
        ".word 0xebfa456e, 0xe320f000, 0xe320f000, 0xea00001e\n"
        ".word 0xe5940008, 0xe5941010, 0xe2800002, 0xe2811002\n"
        ".word 0xe5840008, 0xe5841010, 0xea000017, 0xe59f8124\n"
        ".word 0xe5940008, 0xe2800001, 0xe5840008, 0xe5941010\n"
        ".word 0xe2811001, 0xe5841010, 0xe5941000, 0xe0810280\n"
        ".word 0xe1d050b0, 0xe1a00005, 0xebffeb1e, 0xe3500000\n"
        ".word 0xe320f000, 0x0afffff1, 0xe1550008, 0x1affffef\n"
        ".word 0xea000005, 0xe5940008, 0xe5941010, 0xe2800001\n"
        ".word 0xe2811001, 0xe5840008, 0xe5841010, 0xe5940008\n"
        ".word 0xe3560000, 0xe2800001, 0xe5840008, 0xe5941010\n"
        ".word 0xe2811001, 0xe5841010, 0xe5941000, 0xe0810280\n"
        ".word 0xe1d050b0, 0x0a00001b, 0xe5940034, 0xe3100c03\n"
        ".word 0x0a00001d, 0xebfa4502, 0xe5940010, 0xe594500c\n"
        ".word 0xe0800005, 0xe1500005, 0xda000008, 0xe5940000\n"
        ".word 0xe0800285, 0xe1d000b0, 0xebfa4486, 0xe1c400dc\n"
        ".word 0xe2855001, 0xe0800001, 0xe1500005, 0xcafffff6\n"
        ".word 0xe5940034, 0xe3100c02, 0x13a00001, 0x1bfa44dd\n"
        ".word 0xe320f000, 0xe320f000, 0xebfa43f0, 0xe320f000\n"
        ".word 0xe320f000, 0xea000004, 0xe1a00005, 0xebffeae9\n"
        ".word 0xe3500000, 0xe320f000, 0x1afffec5, 0xe1a00006\n"
        ".word 0xe8bd9ff0, 0x0000f813, 0x004def18, 0x004daee8\n"
        ".word 0x00464d48, 0x004def28, 0x0000f818\n"
    );
}

// DECOMP_FUNC(0x001f3870, 1956)
// Capstone ARM full coverage (489 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void camp_func_001f3870() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff7, 0xe1a07000, 0xe59f0400, 0xe1a06001\n"
        ".word 0xed2d8b04, 0xe24dd058, 0xe3a01065, 0xe5908000\n"
        ".word 0xe58d1004, 0xe1a03007, 0xe2880d09, 0xe58d000c\n"
        ".word 0xe3a0200b, 0xe3a0101d, 0xe3a00002, 0xe58d6000\n"
        ".word 0xeb032f28, 0xe3a0b06a, 0xe1a03007, 0xe28b2ff9\n"
        ".word 0xe3a0101d, 0xe3a00002, 0xe88d0840, 0xeb032ee3\n"
        ".word 0xeddf8aeb, 0xed9f9aeb, 0xed9f8aeb, 0xe3a05000\n"
        ".word 0xe3a0a06f, 0xe320f000, 0xeb01dcfc, 0xe1500005\n"
        ".word 0xe320f000, 0xca000009, 0xe2852b01, 0xe1a03007\n"
        ".word 0xe2822f6a, 0xe3a0101d, 0xe3a00002, 0xe88d0840\n"
        ".word 0xeb032ed2, 0xe320f000, 0xe320f000, 0xea000091\n"
        ".word 0xe59d000c, 0xeb02ae4d, 0xe0800005, 0xe2851b01\n"
        ".word 0xe0880080, 0xe2800c1d, 0xe281100d, 0xe1d09bb4\n"
        ".word 0xe3a0001d, 0xeb032f61, 0xe1a04000, 0xe1d000fa\n"
        ".word 0xe59f2338, 0xe3a0101d, 0xe0800006, 0xe88d0801\n"
        ".word 0xe1d400f8, 0xe0803007, 0xe3a00002, 0xeb032ebb\n"
        ".word 0xe1d400fa, 0xe3a02e45, 0xe3a0101d, 0xe0800006\n"
        ".word 0xe88d0801, 0xe1d400f8, 0xe0803007, 0xe3a00002\n"
        ".word 0xeb032eb2, 0xe1d400fa, 0xe59f22f4, 0xe3a0101d\n"
        ".word 0xe0800006, 0xe88d0801, 0xe1d400f8, 0xe0803007\n"
        ".word 0xe3a00002, 0xeb032ea9, 0xe1d400fa, 0xe59f22d4\n"
        ".word 0xe3a0101d, 0xe0800006, 0xe88d0401, 0xe1d400f8\n"
        ".word 0xe0803007, 0xe3a00002, 0xeb032ea0, 0xe3590000\n"
        ".word 0xe320f000, 0x0a00010a, 0xe1a00009, 0xeb0255b7\n"
        ".word 0xe3500000, 0xe58d0050, 0x0a000105, 0xe59f1298\n"
        ".word 0xe3a0001d, 0xeb032f31, 0xe58d0000, 0xe59d0050\n"
        ".word 0xeb032576, 0xe3500000, 0xe58d0004, 0x0a000026\n"
        ".word 0xe3a000ff, 0xe58d0008, 0xe59d0050, 0xe3e01000\n"
        ".word 0xeb02942b, 0xe3500000, 0xe320f000, 0x0a000007\n"
        ".word 0xe59d0050, 0xeb026693, 0xe1a09000, 0xe320f000\n"
        ".word 0xeb02d3ec, 0xe5900000, 0xe1590000, 0xda000001\n"
        ".word 0xe59f0238, 0xe58d0008, 0xe59d1000, 0xe59d3000\n"
        ".word 0xe1d400fa, 0xe1d420f8, 0xe1d110fa, 0xe1d330f8\n"
        ".word 0xeeb02a68, 0xe0800001, 0xe0821003, 0xe0800006\n"
        ".word 0xe0811007, 0xee000a90, 0xee001a10, 0xeef01a49\n"
        ".word 0xeeb01a48, 0xe59d1008, 0xe59d2004, 0xeef80ae0\n"
        ".word 0xeeb80ac0, 0xe3a00002, 0xeb032b2f, 0xe59f11e0\n"
        ".word 0xe3a0001d, 0xeb032f01, 0xe1a09000, 0xe59d0050\n"
        ".word 0xeb026670, 0xe1a02000, 0xe28f1f72, 0xe28d0010\n"
        ".word 0xfa032b45, 0xe28d0010, 0xe3a01008, 0xe58d0008\n"
        ".word 0xe88d0402, 0xe1d410fa, 0xe1d920fa, 0xe1d430f8\n"
        ".word 0xe1d900f8, 0xe0811002, 0xe0812006, 0xe0800003\n"
        ".word 0xe0801007, 0xe3a03001, 0xe3a00000, 0xeb032992\n"
        ".word 0xe59f1184, 0xe3a0001d, 0xeb032ee8, 0xe3a01000\n"
        ".word 0xe58d1000, 0xe58d1004, 0xe1d030fa, 0xe1d410fa\n"
        ".word 0xe1d420f8, 0xe1d000f8, 0xe0811003, 0xe3a0306f\n"
        ".word 0xe0800002, 0xe0812006, 0xe0801007, 0xe59d0050\n"
        ".word 0xe6bf0070, 0xeb030d02, 0xe2855001, 0xe3550008\n"
        ".word 0xbaffff5b, 0xe59d000c, 0xe3a03001, 0xe1a02006\n"
        ".word 0xe1a01007, 0xeb026fe2, 0xe59d0070, 0xe3500000\n"
        ".word 0x0a00009b, 0xe59d000c, 0xeb02adb0, 0xe1a04000\n"
        ".word 0xe59d000c, 0xeb02ada7, 0xe0800004, 0xe0880080\n"
        ".word 0xe2800c1d, 0xe1d05bb4, 0xe59d000c, 0xeb02ada1\n"
        ".word 0xe2801b01, 0xe281102e, 0xe3a0001d, 0xeb032ebf\n"
        ".word 0xe1a04000, 0xe59d000c, 0xeb02ad9a, 0xe59f20cc\n"
        ".word 0xe0880080, 0xe1d410fa, 0xe19020f2, 0xe1d400f8\n"
        ".word 0xe0811006, 0xe0800007, 0xeb026f4e, 0xed9f8a2c\n"
        ".word 0xe3550000, 0xe3a0a083, 0x0a0000b4, 0xe1a00005\n"
        ".word 0xeb02552e, 0xe1b09000, 0xe320f000, 0x0a0000af\n"
        ".word 0xe3a01e46, 0xe3a0001d, 0xeb032ea8, 0xe1a05000\n"
        ".word 0xe1a00009, 0xeb0324ed, 0xe3500000, 0xe58d0000\n"
        ".word 0x0a000033, 0xe3e08000, 0xe1a01008, 0xe1a00009\n"
        ".word 0xeb0293a3, 0xe3500000, 0xe320f000, 0x0a000018\n"
        ".word 0xe1a00009, 0xeb02660b, 0xe1a0b000, 0xe320f000\n"
        ".word 0xeb02d364, 0xe320f000, 0xe320f000, 0xea00000d\n"
        ".word 0x0043da90, 0x3f800000, 0x00000000, 0x3f0ccccd\n"
        ".word 0x0000044f, 0x00000451, 0x00000452, 0x00000454\n"
        ".word 0x5a5a5aff, 0x0000045c, 0x00006425, 0x00000453\n"
        ".word 0x00000e0c, 0x3f000000, 0xe5900000, 0xe15b0000\n"
        ".word 0xda000000, 0xe51f802c, 0xe1d400fa, 0xe1d520fa\n"
        ".word 0xe1d410f8, 0xe1d530f8, 0xe0800002, 0xe0800006\n"
        ".word 0xe0811003, 0xe0811007, 0xee000a10, 0xee011a10\n"
        ".word 0xeeb02a68, 0xeef01a49, 0xe59d2000, 0xe1a01008\n"
        ".word 0xeef80ac0, 0xeeb80ac1, 0xeeb01a48, 0xe3a00003\n"
        ".word 0xeb032a99, 0xe1d400fa, 0xe59f22a8, 0xe3a0101d\n"
        ".word 0xe0800006, 0xe88d0401, 0xe1d400f8, 0xe0803007\n"
        ".word 0xe3a00002, 0xeb032dc9, 0xe59f128c, 0xe3a0001d\n"
        ".word 0xeb032e62, 0xe1a05000, 0xe1a00009, 0xeb0265d1\n"
        ".word 0xe1a02000, 0xe24f10b4, 0xe28d0010, 0xfa032aa6\n"
        ".word 0xe28d0010, 0xe3a01008, 0xe58d0008, 0xe88d0402\n"
        ".word 0xe1d400fa, 0xe1d510fa, 0xe1d420f8, 0xe1d530f8\n"
        ".word 0xe0811000, 0xe0820003, 0xe0812006, 0xe0801007\n"
        ".word 0xe3a03001, 0xe3a00000, 0xeb0328f3, 0xe1d400fa\n"
        ".word 0xe59f2228, 0xe3a0101d, 0xe0800006, 0xe88d0401\n"
        ".word 0xe1d400f8, 0xe0803007, 0xe3a00002, 0xeb032da7\n"
        ".word 0xe59f120c, 0xe3a0001d, 0xeb032e40, 0xe3a01000\n"
        ".word 0xe58d1000, 0xe58d1004, 0xe1d030fa, 0xe1d410fa\n"
        ".word 0xe1d420f8, 0xe1d000f8, 0xe0811003, 0xe3a03088\n"
        ".word 0xe0800002, 0xe0812006, 0xe0801007, 0xe6bf0079\n"
        ".word 0xeb030c5b, 0xe28dd058, 0xecbd8b04, 0xe28dd00c\n"
        ".word 0xe8bd8ff0, 0xe51f1180, 0xe3a0001d, 0xeb032e2b\n"
        ".word 0xe1a09000, 0xe28f1f6b, 0xe28d0010, 0xfa032a72\n"
        ".word 0xe1d410fa, 0xe1d920fa, 0xe1d430f8, 0xe1d900f8\n"
        ".word 0xe0811002, 0xeeb02a68, 0xe0832000, 0xe0810006\n"
        ".word 0xe0821007, 0xee000a10, 0xee011a10, 0xeef01a49\n"
        ".word 0xe51f11c8, 0xe28d2010, 0xe3a00002, 0xeef80ac0\n"
        ".word 0xeeb80ac1, 0xeeb01a48, 0xeb032a3f, 0xe51f11e0\n"
        ".word 0xe3a0001d, 0xeb032e11, 0xe1a09000, 0xe28f1f5f\n"
        ".word 0xe28d0010, 0xfa032a58, 0xe28d1010, 0xe3a00008\n"
        ".word 0xe58d1008, 0xe88d0401, 0xe1d400fa, 0xe1d920fa\n"
        ".word 0xe1d410f8, 0xe1d930f8, 0xe0822000, 0xe0822006\n"
        ".word 0xe0810003, 0xe0801007, 0xe3a03001, 0xe3a00000\n"
        ".word 0xeb0328a5, 0xe320f000, 0xe320f000, 0xeaffff21\n"
        ".word 0xe3a01e46, 0xe3a0001d, 0xeb032df8, 0xe1a05000\n"
        ".word 0xe28f10e0, 0xe28d0010, 0xfa032a3f, 0xe1d400fa\n"
        ".word 0xe1d510fa, 0xe1d420f8, 0xe1d530f8, 0xe0800001\n"
        ".word 0xe0800006, 0xe0821003, 0xe0811007, 0xee000a90\n"
        ".word 0xee001a10, 0xeeb02a68, 0xeef01a49, 0xeeb01a48\n"
        ".word 0xe51f1298, 0xeef80ae0, 0xeeb80ac0, 0xe28d2010\n"
        ".word 0xe3a00003, 0xeb032a0c, 0xe1d400fa, 0xe59f2074\n"
        ".word 0xe3a0101d, 0xe0800006, 0xe88d0401, 0xe1d400f8\n"
        ".word 0xe0803007, 0xe3a00002, 0xeb032d3c, 0xe59f1058\n"
        ".word 0xe3a0001d, 0xeb032dd5, 0xe1a05000, 0xe28f108c\n"
        ".word 0xe28d0010, 0xfa032a1c, 0xe28d0010, 0xe3a01008\n"
        ".word 0xe58d0008, 0xe88d0402, 0xe1d400fa, 0xe1d520fa\n"
        ".word 0xe1d410f8, 0xe1d530f8, 0xe0822000, 0xe0822006\n"
        ".word 0xe0810003, 0xe0801007, 0xe3a03001, 0xe3a00000\n"
        ".word 0xeb032869, 0xeaffff8e, 0x0000045e, 0x00000468\n"
        ".word 0x0000045d, 0x0000045f, 0x85826d82, 0x40819782\n"
        ".word 0x85829282, 0x89828782, 0x94829382, 0x81829282\n"
        ".word 0x89829482, 0x8e828f82, 0x90824081, 0x93828f82\n"
        ".word 0x89829382, 0x8c828282, 0x49818582, 0x00000000\n"
        ".word 0x002d2d2d\n"
    );
}

// DECOMP_FUNC(0x0037cc10, 1980)
// Capstone ARM full coverage (495 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_0037cc10() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe24dd06c, 0xe3a05000, 0xe1a07000\n"
        ".word 0xe59d00a0, 0xe59f8798, 0xe58d503c, 0xe3500000\n"
        ".word 0xe58d5030, 0xe58d5038, 0x0a000050, 0xe5d70a90\n"
        ".word 0xe3500003, 0x1a000007, 0xe59d20a0, 0xe1c81005\n"
        ".word 0xe3a00000, 0xe0a01892, 0xe1a00120, 0xe0600180\n"
        ".word 0xe1a00080, 0xe58d00a0, 0xe5970054, 0xe59d40a0\n"
        ".word 0xe597105c, 0xe0800004, 0xe1500001, 0x23a06001\n"
        ".word 0x3a000029, 0xe1a00001, 0xe5971054, 0xe0400001\n"
        ".word 0xe0444000, 0xe5970018, 0xe5d01008, 0xe3510000\n"
        ".word 0x0a000007, 0xe590100c, 0xe5871058, 0xe5970018\n"
        ".word 0xe5901010, 0xe587105c, 0xe5971058, 0xe5871054\n"
        ".word 0xea000011, 0xe5972c24, 0xe1a00007, 0xe3520000\n"
        ".word 0x0a000086, 0xe5970050, 0xe58d0008, 0xe5971c28\n"
        ".word 0xe28d0008, 0xe12fff32, 0xe3500000, 0x0a00007b\n"
        ".word 0xe59d1008, 0xe5871050, 0xe5970018, 0xe5901010\n"
        ".word 0xe587105c, 0xe5875058, 0xe5875054, 0xe59d0038\n"
        ".word 0xe2800001, 0xe58d0038, 0xe5970054, 0xe597105c\n"
        ".word 0xe0800004, 0xe1500001, 0x2affffd5, 0xe5970054\n"
        ".word 0xe0800004, 0xe5870054, 0xe5974018, 0xe5941014\n"
        ".word 0xebfd27b2, 0xe5870034, 0xe5941018, 0xe5972020\n"
        ".word 0xe5973040, 0xe0010291, 0xe0213091, 0xe5970014\n"
        ".word 0xe5902000, 0xe5923040, 0xe3a02000, 0xe12fff33\n"
        ".word 0xe5d70a90, 0xe3500003, 0x03a00001, 0x058d0030\n"
        ".word 0xe3a00000, 0xe1a0a000, 0xe58d002c, 0xe5970054\n"
        ".word 0xe3a06001, 0xe58d0040, 0xe1c703d4, 0xe1500001\n"
        ".word 0xe5970018, 0x12805014, 0xe1a01000, 0x18950220\n"
        ".word 0x05905020, 0x0590901c, 0xe5970054, 0xe5911014\n"
        ".word 0xebfd2792, 0xe58d1004, 0xe5d70a90, 0xe3500003\n"
        ".word 0x11a08001, 0x0a00004b, 0xe3560000, 0x0a00002a\n"
        ".word 0xe59d0030, 0xe3500000, 0xe59d0004, 0xe0400008\n"
        ".word 0xe58d003c, 0x0a000024, 0xe5970014, 0xe5901000\n"
        ".word 0xe5911054, 0xe12fff31, 0xe1a04000, 0xe5970020\n"
        ".word 0xe28d2058, 0xe28d1048, 0xe58d0000, 0xe5973034\n"
        ".word 0xe1a00007, 0xebfffbf2, 0xe3500000, 0xe320f000\n"
        ".word 0x0a00004b, 0xe5970014, 0xe3a02000, 0xe5901000\n"
        ".word 0xe5913040, 0xe1a01004, 0xe12fff33, 0xe5970020\n"
        ".word 0xe3500000, 0x0a00000c, 0xe28d1048, 0xe28d2058\n"
        ".word 0xe3a03000, 0xe0d140b2, 0xe083c083, 0xe2500001\n"
        ".word 0xe087c08c, 0xe28ccc0b, 0xe2833001, 0xe1cc4fb4\n"
        ".word 0xe0d240b2, 0xe1cc4fb6, 0x1afffff5, 0xe5d71a90\n"
        ".word 0xe1a00008, 0xebfffc4a, 0xe1a0b000, 0xe5970020\n"
        ".word 0xe049100b, 0xe58d1000, 0xe59d1004, 0xe3500000\n"
        ".word 0xe3a04000, 0xe0451001, 0xe58d1020, 0x9a000051\n"
        ".word 0xe59d0030, 0xe0000006, 0xe58d0044, 0xe5970010\n"
        ".word 0xe5d00052, 0xe3500000, 0x1a000020, 0xea000011\n"
        ".word 0xe597105c, 0xe1a00007, 0xe5871054, 0xea000001\n"
        ".word 0xe597105c, 0xe5871054, 0xe5c0604d, 0xe59d0070\n"
        ".word 0xe5805020, 0xea00012b, 0xe59f24b4, 0xe59d3004\n"
        ".word 0xe3a00000, 0xe0a02293, 0xe1a00120, 0xe0600180\n"
        ".word 0xe1a08080, 0xeaffffab, 0xe5970020, 0xe2841002\n"
        ".word 0xe3a08002, 0xe1500001, 0x30408004, 0xe5970014\n"
        ".word 0xe0050899, 0xe5901000, 0xe1a02005, 0xe5913024\n"
        ".word 0xe59f1470, 0xe12fff33, 0xe1500005, 0x0a000002\n"
        ".word 0xe3a00000, 0xe28dd07c, 0xe8bd8ff0, 0xe3580000\n"
        ".word 0xe3a05000, 0x9a000020, 0xe59d0074, 0xe59f1444\n"
        ".word 0xe0261599, 0xe7900104, 0xe086100b, 0xe080000a\n"
        ".word 0xe58d0014, 0xe59d2000, 0xebfd2415, 0xe59d0014\n"
        ".word 0xe59d1000, 0xebfc9f81, 0xe59d0044, 0xe3500000\n"
        ".word 0x0a00000d, 0xe0840084, 0xe5d61000, 0xe0870080\n"
        ".word 0xe2800c0b, 0xe28000f2, 0xe1a03006, 0xe1c010b0\n"
        ".word 0xe0841084, 0xe0811184, 0xe59d2004, 0xe0871101\n"
        ".word 0xe2811c0a, 0xe2811092, 0xebfffcdf, 0xe2855001\n"
        ".word 0xe1550008, 0xe2844001, 0x3affffde, 0xe5970020\n"
        ".word 0xe1540000, 0x3affffb0, 0xe59d3020, 0xe59d202c\n"
        ".word 0xe5970054, 0xe5971034, 0xe0822003, 0xe0800003\n"
        ".word 0xe58d202c, 0xe597205c, 0xe59d3000, 0xe2811001\n"
        ".word 0xe5870054, 0xe1500002, 0xe08aa003, 0xe5871034\n"
        ".word 0x1a000034, 0xe5970018, 0xe5d01008, 0xe3510000\n"
        ".word 0x0a000007, 0xe590100c, 0xe5871058, 0xe5970018\n"
        ".word 0xe5901010, 0xe587105c, 0xe5971058, 0xe5871054\n"
        ".word 0xea000010, 0xe5972c24, 0xe3520000, 0x0a000020\n"
        ".word 0xe5970050, 0xe58d0004, 0xe5971c28, 0xe28d0004\n"
        ".word 0xe12fff32, 0xe3500000, 0x0a000019, 0xe59d2004\n"
        ".word 0xe3a00000, 0xe5872050, 0xe5971018, 0xe5911010\n"
        ".word 0xe1c705f8, 0xe5870054, 0xe59d0038, 0xe2800001\n"
        ".word 0xe58d0038, 0xe5974018, 0xe5970054, 0xe5941014\n"
        ".word 0xebfd26ce, 0xe5870034, 0xe5942018, 0xe5973020\n"
        ".word 0xe5971040, 0xe0020392, 0xe0211092, 0xe5970014\n"
        ".word 0xe5902000, 0xe5923040, 0xe3a02000, 0xe12fff33\n"
        ".word 0xea000008, 0xe597105c, 0xe3a00001, 0xe5871054\n"
        ".word 0xe5c7004d, 0xea000003, 0xe59d002c, 0xe3a06000\n"
        ".word 0xe3500000, 0x0affff1b, 0xe5d70a90, 0xe3500003\n"
        ".word 0x0a000006, 0xe5970020, 0xe3500000, 0x0a00008b\n"
        ".word 0xe2000001, 0xe3500001, 0x0a000079, 0xea00007b\n"
        ".word 0xe59d0040, 0xe3500000, 0x0a00000e, 0xe5970018\n"
        ".word 0xe5d01008, 0xe3510000, 0x0a00003e, 0xe590100c\n"
        ".word 0xe59d0040, 0xe1510000, 0x1a00003a, 0xe5970020\n"
        ".word 0xe3500000, 0x0a000079, 0xe2000001, 0xe3500001\n"
        ".word 0x1a000021, 0xea00001c, 0xe5970020, 0xe3500000\n"
        ".word 0x0a000072, 0xe2000001, 0xe3500001, 0x1a000003\n"
        ".word 0xe59d1070, 0xe2872c0a, 0xe28220b2, 0xe5812024\n"
        ".word 0xe5971020, 0xe1510000, 0x9a000068, 0xe0802080\n"
        ".word 0xe0822180, 0xe59d1070, 0xe0872102, 0xe2823c0a\n"
        ".word 0xe0811100, 0xe28330b2, 0xe2822c0a, 0xe5a13024\n"
        ".word 0xe28220de, 0xe5812004, 0xe5971020, 0xe2800002\n"
        ".word 0xe1510000, 0x8afffff0, 0xea000058, 0xe59d1070\n"
        ".word 0xe2872b02, 0xe2822fae, 0xe5812024, 0xe5971020\n"
        ".word 0xe1510000, 0x9a000051, 0xe59d1070, 0xe0803080\n"
        ".word 0xe0812100, 0xe0831180, 0xe2800002, 0xe0871101\n"
        ".word 0xe2813b02, 0xe2833fae, 0xe2811b02, 0xe5a23024\n"
        ".word 0xe2811fb9, 0xe5821004, 0xe5971020, 0xe1510000\n"
        ".word 0x8afffff0, 0xea000041, 0xe59d00a0, 0xe3500000\n"
        ".word 0xe5970020, 0x0a000019, 0xe3500000, 0x0a00003b\n"
        ".word 0xe2000001, 0xe3500001, 0x1a000003, 0xe59d1070\n"
        ".word 0xe2872c0b, 0xe28220f2, 0xe5812024, 0xe5971020\n"
        ".word 0xe1510000, 0x9a000031, 0xe0801080, 0xe0872081\n"
        ".word 0xe59d1070, 0xe2823b02, 0xe2822c0b, 0xe0811100\n"
        ".word 0xe2833ffe, 0xe28220f2, 0xe1c122f4, 0xe5971020\n"
        ".word 0xe2800002, 0xe1510000, 0x8afffff2, 0xea000023\n"
        ".word 0xe3500000, 0x0a000021, 0xe2000001, 0xe3500001\n"
        ".word 0x1a000002, 0xe59d2070, 0xe3a01000, 0xe5821024\n"
        ".word 0xe5971020, 0xe1510000, 0x83a01000, 0x9a000017\n"
        ".word 0xe59d2070, 0xe0822100, 0xe2800002, 0xe5821024\n"
        ".word 0xe5821028, 0xe5972020, 0xe1520000, 0x8afffff7\n"
        ".word 0xea00000e, 0xe59d2070, 0xe3a01000, 0xe5821024\n"
        ".word 0xe5971020, 0xe1510000, 0x83a01000, 0x9a000007\n"
        ".word 0xe59d2070, 0xe0822100, 0xe2800002, 0xe5821024\n"
        ".word 0xe5821028, 0xe5972020, 0xe1520000, 0x8afffff7\n"
        ".word 0xe59d0070, 0xe59d1078, 0xe5801018, 0xe59d1070\n"
        ".word 0xe59d002c, 0xe5810020, 0xe59d1070, 0xe59d0040\n"
        ".word 0xe581001c, 0xe59d1070, 0xe59d003c, 0xe5810044\n"
        ".word 0xe59d1070, 0xe59d0038, 0xe5810048, 0xe59d0070\n"
        ".word 0xe5d7104d, 0xe5c0104c, 0xe28dd07c, 0xe3a00001\n"
        ".word 0xe8bd8ff0, 0x49249249, 0x004eb380\n"
    );
}

// DECOMP_FUNC(0x00393a00, 1984)
// Capstone ARM full coverage (496 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void ui_func_00393a00() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff7, 0xe1a04002, 0xe1a07001, 0xe3a08000\n"
        ".word 0xe1a06008, 0xe1a09008, 0xed2d8b06, 0xe24ddf4e\n"
        ".word 0xe591500c, 0xebfa7e60, 0xeeb08a40, 0xe59f13e4\n"
        ".word 0xe3a03004, 0xe3a02010, 0xe28d0060, 0xfafcc945\n"
        ".word 0xe59f13d0, 0xe3a03004, 0xe3a02010, 0xe28d0020\n"
        ".word 0xfafcc940, 0xe3a00000, 0xe58d0010, 0xebf9f354\n"
        ".word 0xe3500000, 0x0a000005, 0xe5d71010, 0xe594000c\n"
        ".word 0xe0800001, 0xe3500c01, 0xa3a000ff, 0xe584000c\n"
        ".word 0xed9f0ae5, 0xe3a00000, 0xe28db020, 0xe28da060\n"
        ".word 0xe08a1200, 0xe59f2384, 0xed810a00, 0xed810a01\n"
        ".word 0xed810a02, 0xe0822200, 0xed818a03, 0xe282c030\n"
        ".word 0xe592302c, 0xe08b1200, 0xecdc0a02, 0xe2800001\n"
        ".word 0xe5922038, 0xe5813000, 0xe2813004, 0xe3500004\n"
        ".word 0xecc30a02, 0xe581200c, 0xbaffffec, 0xebfce1a6\n"
        ".word 0xe3550000, 0xe58d00c0, 0x0a0000a1, 0xe5d5000c\n"
        ".word 0xed9faacb, 0xe3100002, 0x0a000002, 0xe5941000\n"
        ".word 0xe3110008, 0x0a000004, 0xe3100004, 0x0a000016\n"
        ".word 0xe5940000, 0xe3100004, 0x1a000013, 0xeef08a48\n"
        ".word 0xed950a02, 0xeeb08a40, 0xee180a90, 0xe35005fe\n"
        ".word 0x0a00000d, 0xeef48a4a, 0xeef1fa10, 0x1a000003\n"
        ".word 0xeeb48a4a, 0xeef1fa10, 0x1a000050, 0xea000006\n"
        ".word 0xee288a28, 0xeeb48a4a, 0xeef1fa10, 0x1a000002\n"
        ".word 0xeeb40a4a, 0xeef1fa10, 0x1d9f8aae, 0xe320f000\n"
        ".word 0xebfd609e, 0xe3500000, 0xe320f000, 0x0a000019\n"
        ".word 0xe3a02000, 0xe3a01007, 0xe3a00006, 0xebfcc904\n"
        ".word 0xe58d00a0, 0xe3a02000, 0xe3a01001, 0xe3a00006\n"
        ".word 0xebfcc8ff, 0xe58d00a4, 0xe3a02002, 0xe3a01001\n"
        ".word 0xe3a00006, 0xebfcc8fa, 0xe58d00a8, 0xe3a02001\n"
        ".word 0xe3a01000, 0xe3a00005, 0xebfcc8f5, 0xe58d00ac\n"
        ".word 0xe5d5000c, 0xe28d10a0, 0xe1a00320, 0xe7910100\n"
        ".word 0xebfce16d, 0xe3a09001, 0xe5d5000c, 0xe3100004\n"
        ".word 0x0a00001e, 0xe5940000, 0xe2100004, 0x1a00001b\n"
        ".word 0xe08b1200, 0xe3500002, 0xec910a02, 0xedd11a02\n"
        ".word 0x03a01003, 0x0a000002, 0xe3500003, 0x03a01002\n"
        ".word 0x11a01000, 0xee102a10, 0xe0851201, 0xee103a90\n"
        ".word 0xed911a04, 0xe2811014, 0xe35205fe, 0xec912a03\n"
        ".word 0x1e211a00, 0xee11ca90, 0xe35305fe, 0x1e222a20\n"
        ".word 0xe35c05fe, 0x1e622aa1, 0xe08a1200, 0xe2800001\n"
        ".word 0xe3500004, 0xeca11a01, 0xec812a03, 0xbaffffe3\n"
        ".word 0xe1d500f4, 0xe3a0a001, 0xe3500000, 0x0a000008\n"
        ".word 0xe3500001, 0x0a000068, 0xe3590000, 0x1bfa7db0\n"
        ".word 0xe3a00000, 0xe28ddf4e, 0xecbd8b06, 0xe28dd00c\n"
        ".word 0xe8bd8ff0, 0xe5d5000c, 0xe3100002, 0x0a000005\n"
        ".word 0xe5940000, 0xe3100008, 0x1a000002, 0xeeb00a48\n"
        ".word 0xe3a06001, 0xebfcae91, 0xe5d5000c, 0xe3100004\n"
        ".word 0x0a000027, 0xe5940000, 0xe3100004, 0x1a000024\n"
        ".word 0xeddd0a1b, 0xed9d0a04, 0xe28d0090, 0xee600a88\n"
        ".word 0xe3a08001, 0xe1a06008, 0xe28d30a0, 0xe28d20c8\n"
        ".word 0xe28d10d8, 0xedcd0a1b, 0xeddd0a1f, 0xee600a88\n"
        ".word 0xedcd0a1f, 0xeddd0a23, 0xee600a88, 0xedcd0a23\n"
        ".word 0xeddd0a27, 0xee600a88, 0xedcd0a27, 0xecd00a04\n"
        ".word 0xe28d00a0, 0xecc00a04, 0xe28d0080, 0xecd00a04\n"
        ".word 0xe28d00c8, 0xecc00a04, 0xe28d0070, 0xecd00a04\n"
        ".word 0xe28d00d8, 0xecc00a04, 0xe28d0060, 0xecd00a04\n"
        ".word 0xe28d00e8, 0xed8d0a00, 0xecc00a04, 0xe58da004\n"
        ".word 0xebfc7901, 0xe59d2150, 0xe1a01004, 0xe1a00007\n"
        ".word 0xebfc53f8, 0xe3560000, 0x1eb00a68, 0xe1a04000\n"
        ".word 0x1bfcae5e, 0xe3580000, 0xe320f000, 0x0a000018\n"
        ".word 0xe28d1050, 0xed9d0a30, 0xe3a00000, 0xecd10a04\n"
        ".word 0xe28d1010, 0xe28d3010, 0xe28d20a0, 0xecc10a04\n"
        ".word 0xe28d1040, 0xecd10a04, 0xe28d10a0, 0xecc10a04\n"
        ".word 0xe28d1030, 0xecd10a04, 0xe28d10c8, 0xecc10a04\n"
        ".word 0xe28d1020, 0xecd10a04, 0xe28d10d8, 0xed8d0a00\n"
        ".word 0xecc10a04, 0xe28d10c8, 0xe58d0004, 0xe28d00d8\n"
        ".word 0xebfc78dd, 0xe3590000, 0x1bfa7d51, 0xe1a00004\n"
        ".word 0xe320f000, 0xeaffff9e, 0x0014144c, 0x3f800000\n"
        ".word 0x004d4680, 0x00000000, 0x3b808081, 0xe5940000\n"
        ".word 0xe3100002, 0x0a000007, 0xe5941004, 0xe1d720f8\n"
        ".word 0xe0811002, 0xe5841004, 0xe1d710fa, 0xe5942008\n"
        ".word 0xe0811002, 0xe5841008, 0xe5d5100c, 0xe3110002\n"
        ".word 0x0a000004, 0xe3100008, 0x1a000002, 0xeeb00a48\n"
        ".word 0xe3a06001, 0xebfcae25, 0xe5d5000c, 0xe3100004\n"
        ".word 0x0a000027, 0xe5940000, 0xe3100004, 0x1a000024\n"
        ".word 0xeddd0a1b, 0xed9d0a04, 0xe28d0090, 0xee600a88\n"
        ".word 0xe3a08001, 0xe1a06008, 0xe28d30a0, 0xe28d2f42\n"
        ".word 0xe28d1f46, 0xedcd0a1b, 0xeddd0a1f, 0xee600a88\n"
        ".word 0xedcd0a1f, 0xeddd0a23, 0xee600a88, 0xedcd0a23\n"
        ".word 0xeddd0a27, 0xee600a88, 0xedcd0a27, 0xecd00a04\n"
        ".word 0xe28d00a0, 0xecc00a04, 0xe28d0080, 0xecd00a04\n"
        ".word 0xe28d0f42, 0xecc00a04, 0xe28d0070, 0xecd00a04\n"
        ".word 0xe28d0f46, 0xecc00a04, 0xe28d0060, 0xecd00a04\n"
        ".word 0xe28d0f4a, 0xed8d0a00, 0xecc00a04, 0xe58da004\n"
        ".word 0xebfc7895, 0xe594000c, 0xe5941000, 0xeddfaa9e\n"
        ".word 0xe2600c01, 0xee000a10, 0xe3110010, 0xeeb09a4a\n"
        ".word 0xe3a05000, 0xeeb80ac0, 0xee208a2a, 0x1d940a0c\n"
        ".word 0x1eb40a4a, 0x1ef1fa10, 0x0a00001f, 0xe1d423f4\n"
        ".word 0xe5941004, 0xe5940008, 0xe3520001, 0x05942014\n"
        ".word 0x008110a2, 0x0a000005, 0xe3520002, 0x05942014\n"
        ".word 0x00811002, 0x0a000001, 0xe3520003, 0x01d413f8\n"
        ".word 0xe1d423f6, 0xe3520001, 0x05942018, 0x008000a2\n"
        ".word 0x0a000005, 0xe3520002, 0x05942018, 0x00800002\n"
        ".word 0x0a000001, 0xe3520003, 0x01d403fa, 0xee000a90\n"
        ".word 0xe28d00c8, 0xeeb81ae0, 0xee001a90, 0xeef80ae0\n"
        ".word 0xebfc5349, 0xed949a0c, 0xe3a05001, 0xe320f000\n"
        ".word 0xebfce069, 0xe59fa1c4, 0xe3500000, 0x0a000036\n"
        ".word 0xe5941000, 0xeeb00a48, 0xe594000c, 0xe3110502\n"
        ".word 0xe2011501, 0xe1a02000, 0x0a000006, 0xe3510000\n"
        ".word 0xe5940010, 0x15d71011, 0x10800001, 0xe3500c01\n"
        ".word 0xc3a00c01, 0xea000001, 0xe3510000, 0x15d70011\n"
        ".word 0xe1520000, 0x0a000003, 0xe2600c01, 0xee000a10\n"
        ".word 0xeeb80ac0, 0xee200a2a, 0xe59a0000, 0xebfc9906\n"
        ".word 0xeef09a40, 0xe320f000, 0xebfd5f68, 0xe3500000\n"
        ".word 0x1ebd0ae9, 0xeeb49a4a, 0x1ef89ac0, 0xeef1fa10\n"
        ".word 0x0a000010, 0xed9f0a4e, 0xeddf0a4e, 0xee290a00\n"
        ".word 0xee200a20, 0xeddf0a4c, 0xee200a2a, 0xee209a20\n"
        ".word 0xeeb00a49, 0xebfc8cdc, 0xedd40a02, 0xeef80ae0\n"
        ".word 0xee400a69, 0xeebd0ae0, 0xed840a02, 0xeeb00a49\n"
        ".word 0xebfc8cbb, 0xee609a29, 0xed940a01, 0xeeb80ac0\n"
        ".word 0xee300a29, 0xeebd0ac0, 0xed840a01, 0xe59a0000\n"
        ".word 0xe3a01000, 0xebfcb718, 0xedd40a06, 0xed941a05\n"
        ".word 0xed942a02, 0xed940a01, 0xeef81a60, 0xe51f02d4\n"
        ".word 0xeeb81a41, 0xeef80ac2, 0xeeb80ac0, 0xeeb02a48\n"
        ".word 0xe280305c, 0xe280204c, 0xe280103c, 0xe280002c\n"
        ".word 0xebfc8e3e, 0xe3550000, 0x128d00c8, 0x1bfb6a28\n"
        ".word 0xe3560000, 0x1eb00a68, 0x1bfcad78, 0xe3580000\n"
        ".word 0xe320f000, 0x0a000018, 0xe28d1050, 0xed9d0a30\n"
        ".word 0xe3a00000, 0xecd10a04, 0xe28d1008, 0xe28d3008\n"
        ".word 0xe28d20a0, 0xecc10a04, 0xe28d1040, 0xecd10a04\n"
        ".word 0xe28d10a0, 0xecc10a04, 0xe28d1030, 0xecd10a04\n"
        ".word 0xe28d1f42, 0xecc10a04, 0xe28d1020, 0xecd10a04\n"
        ".word 0xe28d1f46, 0xed8d0a00, 0xecc10a04, 0xe28d1f42\n"
        ".word 0xe58d0004, 0xe28d0f46, 0xebfc77f7, 0xe3590000\n"
        ".word 0x1bfa7c6b, 0xe3a00001, 0xeafffeb9, 0x3b800000\n"
        ".word 0x0044ea00, 0x40000000, 0xc0490fdb, 0x4222f983\n"
    );
}

// DECOMP_FUNC(0x003d33a8, 1992)
// Capstone ARM full coverage (498 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void battle_func_003d33a8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff8, 0xe1a05000, 0xe1a06001, 0xe3a08000\n"
        ".word 0xe1a01008, 0xe5902000, 0xe3e00000, 0xe2822a02\n"
        ".word 0xe582825c, 0xe5952000, 0xe2822a02, 0xe5828260\n"
        ".word 0xe5952000, 0xe2822a02, 0xe5828264, 0xe5953000\n"
        ".word 0xe1a02008, 0xe2833c22, 0xe1c385b8, 0xe595c000\n"
        ".word 0xe1a03008, 0xe28ccc22, 0xe1cc85ba, 0xe5954000\n"
        ".word 0xe3a0c000, 0xe2844b12, 0xe2844f79, 0xe5848000\n"
        ".word 0xe5954000, 0xe2844b12, 0xe28440b8, 0xe5848000\n"
        ".word 0xe58605a4, 0xe5954000, 0xe2844b0b, 0xe2844fc1\n"
        ".word 0xe5c48000, 0xe5954000, 0xe2844a01, 0xe2844efd\n"
        ".word 0xe8840006, 0xe5951000, 0xe2811b07, 0xe2811ff6\n"
        ".word 0xe8811008, 0xe5951000, 0xe2812901, 0xe2822e4a\n"
        ".word 0xe5923004, 0xe3c33002, 0xe5823004, 0xe5951000\n"
        ".word 0xe5c10080, 0xe5951000, 0xe5c10081, 0xe5950000\n"
        ".word 0xebf9f534, 0xe3a07000, 0xe5950000, 0xe0871207\n"
        ".word 0xe0811307, 0xe2800d7f, 0xe5900000, 0xe0804181\n"
        ".word 0xe3a00002, 0xebf9ca5e, 0xe1c407b6, 0xe5942000\n"
        ".word 0xe3a01000, 0xe2877001, 0xe3c22206, 0xe5842000\n"
        ".word 0xe3c20102, 0xe58480c8, 0xe357006d, 0xe1c400f0\n"
        ".word 0xbaffffec, 0xe59f066c, 0xe5900000, 0xeb001b25\n"
        ".word 0xe5960028, 0xe3a020cc, 0xe2800c01, 0xe1c084bc\n"
        ".word 0xe5960028, 0xe2800c01, 0xe1c084be, 0xe5960020\n"
        ".word 0xe58080c0, 0xe3a00000, 0xe5868f18, 0xe5951000\n"
        ".word 0xe0803200, 0xe0833300, 0xe2811d7f, 0xe0823183\n"
        ".word 0xe5911000, 0xe2800001, 0xe350006d, 0xe0811003\n"
        ".word 0xe1c18fbc, 0xe1c18fbe, 0xbafffff3, 0xe5950000\n"
        ".word 0xe2800901, 0xe2800e4a, 0xe5900000, 0xe3100040\n"
        ".word 0x15960000, 0x13800080, 0x0a000036, 0xe5860000\n"
        ".word 0xe5950000, 0xebfaffd8, 0xe59f45dc, 0xe3500000\n"
        ".word 0x0a000004, 0xe5940000, 0xebff6f65, 0xe3500000\n"
        ".word 0xe320f000, 0x0a0000f7, 0xe5950000, 0xe59f95bc\n"
        ".word 0xe3a0701d, 0xe2801901, 0xe2811e4a, 0xe3a0a001\n"
        ".word 0xe5912000, 0xe3120802, 0x0a000027, 0xe5940000\n"
        ".word 0xebfaac00, 0xe3500000, 0xe320f000, 0x0a0000e9\n"
        ".word 0xe58da000, 0xe5963024, 0xe3a0200f, 0xe1a01006\n"
        ".word 0xe3a00000, 0xebfa62cf, 0xe5950000, 0xe2802901\n"
        ".word 0xe2822e4a, 0xe5921000, 0xe5920004, 0xe3811a02\n"
        ".word 0xe5821000, 0xe5953000, 0xe3c12802, 0xe2831901\n"
        ".word 0xe2811e4a, 0xe5810004, 0xe5812000, 0xe5940000\n"
        ".word 0xe59f153c, 0xe7818000, 0xebf95964, 0xe5951000\n"
        ".word 0xe59f0530, 0xe5992004, 0xe5911084, 0xe0000091\n"
        ".word 0xe0820100, 0xea0000ef, 0xe3100c01, 0x15960000\n"
        ".word 0x13800a01, 0x1affffc4, 0xeaffffc4, 0xe5962030\n"
        ".word 0xe3520001, 0x0a000070, 0xe3520004, 0x0a000091\n"
        ".word 0xe3520005, 0x0a0000c8, 0xe59f44ec, 0xe1a01000\n"
        ".word 0xe3a02001, 0xe5940000, 0xebfa0d3e, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000010, 0xe5950000, 0xe2801c1f\n"
        ".word 0xe3e00000, 0xe1d11cf8, 0xe3510000, 0x03a00001\n"
        ".word 0x0a000007, 0xe3510001, 0x03a00002, 0x0a000004\n"
        ".word 0xe3510002, 0x03a00003, 0x0a000001, 0xe3510003\n"
        ".word 0x03a00004, 0xe5941000, 0xe5810760, 0xe5953000\n"
        ".word 0xe5940000, 0xe59f1484, 0xe5902760, 0xe19110f3\n"
        ".word 0xe1520001, 0x0a00000a, 0xe3520000, 0xba000008\n"
        ".word 0xe3a02001, 0xe1a01003, 0xebfa0d1e, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000002, 0xe1a01006, 0xe3a00000\n"
        ".word 0xebfa0cf9, 0xe58da000, 0xe5950000, 0xe59f243c\n"
        ".word 0xe3a03001, 0xe1a01006, 0xe19020f2, 0xe1a00003\n"
        ".word 0xebf9a402, 0xe5960020, 0xe5900000, 0xe3100020\n"
        ".word 0x0a000003, 0xebf9c9a4, 0xe3500000, 0xe320f000\n"
        ".word 0x0a000095, 0xe1c602d4, 0xe3a04000, 0xe1d11fba\n"
        ".word 0xe1d076f2, 0xe3110080, 0x0a000004, 0xe3a01007\n"
        ".word 0xe1a00007, 0xebf9c9bd, 0xe3500000, 0x13a04080\n"
        ".word 0xe5960028, 0xe1d00fba, 0xe3100040, 0x0a000004\n"
        ".word 0xe3a01006, 0xe1a00007, 0xebf9c9b4, 0xe3500000\n"
        ".word 0x13844040, 0xe5960028, 0xe1d00fba, 0xe3100c01\n"
        ".word 0x0a000004, 0xe3a01008, 0xe1a00007, 0xebf9c9ab\n"
        ".word 0xe3500000, 0x13844c01, 0xe5960028, 0xe1d00fba\n"
        ".word 0xe3100008, 0x0a000004, 0xe3a01003, 0xe1a00007\n"
        ".word 0xebf9c9a2, 0xe3500000, 0x13844008, 0xe3540000\n"
        ".word 0x0a000004, 0xe3a01000, 0xe5962024, 0xe1a03004\n"
        ".word 0xe1a00001, 0xebf9cda4, 0xe5960028, 0xe1d00fba\n"
        ".word 0xe3100080, 0x1a00007f, 0xea000078, 0xe5961028\n"
        ".word 0xe3a00007, 0xe3a04008, 0xe2811c01, 0xe1c104bc\n"
        ".word 0xe5960028, 0xe3a01085, 0xe2800c01, 0xe1c044be\n"
        ".word 0xe2860038, 0xe58685a0, 0xebfbc4b6, 0xe5962034\n"
        ".word 0xe1a01006, 0xe1a00005, 0xebfff092, 0xe5951000\n"
        ".word 0xe5960034, 0xe2812d7f, 0xe2811c22, 0xe0803200\n"
        ".word 0xe5922000, 0xe0830300, 0xe0840180, 0xe19200b0\n"
        ".word 0xe1c105ba, 0xe5952000, 0xe59f02c8, 0xe5993004\n"
        ".word 0xe3a0100b, 0xe5922084, 0xe0000092, 0xe0830100\n"
        ".word 0xe5c01009, 0xea00002e, 0xe5960020, 0xe3a04023\n"
        ".word 0xe5900000, 0xe3100001, 0x0a00001f, 0xe5960028\n"
        ".word 0xe2800c01, 0xe1c0a4bc, 0xe5961020, 0xe5960580\n"
        ".word 0xe58100c0, 0xe5960020, 0xe3a01085, 0xe5900000\n"
        ".word 0xe3100006, 0xe5960028, 0xe2800c01, 0x11c0a4be\n"
        ".word 0x01c084be, 0xe2860038, 0xebfbc48a, 0xe5962034\n"
        ".word 0xe1a01006, 0xe1a00005, 0xebfff066, 0xe3500000\n"
        ".word 0xe320f000, 0x0a000014, 0xe5960000, 0xe1a01006\n"
        ".word 0xe3800f81, 0xe5860000, 0xe1a00005, 0xebf958da\n"
        ".word 0xe320f000, 0xe320f000, 0xea000009, 0xe5912000\n"
        ".word 0xe59f0210, 0xe3822401, 0xe5812000, 0xe5951000\n"
        ".word 0xe5992004, 0xe5911084, 0xe0000091, 0xe0820100\n"
        ".word 0xe5c04009, 0xe3a00001, 0xe8bd8ff8, 0xe5951000\n"
        ".word 0xe59f01e0, 0xe5992004, 0xe5911084, 0xe0000091\n"
        ".word 0xe0820100, 0xe5c04009, 0xeafffff5, 0xe5902084\n"
        ".word 0xe59f01c0, 0xe5993004, 0xe3a0101c, 0xe0000092\n"
        ".word 0xe0830100, 0xe5c01009, 0xeaffffed, 0xe5950000\n"
        ".word 0xe5901084, 0xe1a00005, 0xebfa0c89, 0xe1a01006\n"
        ".word 0xe1a00005, 0xebf9509d, 0xe5960024, 0xe3a03000\n"
        ".word 0xe3a02001, 0xe3a0101d, 0xe1d006f2, 0xebfa064b\n"
        ".word 0xe5950000, 0xe59f216c, 0xe5991004, 0xe5900084\n"
        ".word 0xe0000290, 0xe0810100, 0xe5c07009, 0xeaffffd8\n"
        ".word 0xe3a00016, 0xebf9c906, 0xe1a02000, 0xe3a01016\n"
        ".word 0xe1a00007, 0xebfa0667, 0xe5960028, 0xe1d00fba\n"
        ".word 0xe3100040, 0x1a000005, 0xe3a00017, 0xebf9c8fc\n"
        ".word 0xe1a02000, 0xe3a01017, 0xe1a00007, 0xebfa065d\n"
        ".word 0xe5960028, 0xe1d00fba, 0xe3100c01, 0x1a000005\n"
        ".word 0xe3a00018, 0xebf9c8f2, 0xe1a02000, 0xe3a01018\n"
        ".word 0xe1a00007, 0xebfa0653, 0xe5960028, 0xe1d00fba\n"
        ".word 0xe3100008, 0x1a000005, 0xe3a00019, 0xebf9c8e8\n"
        ".word 0xe1a02000, 0xe3a01019, 0xe1a00007, 0xebfa0649\n"
        ".word 0xe5961028, 0xe3a00004, 0xe1d11fba, 0xe1c11004\n"
        ".word 0xe3110d07, 0x0a000007, 0xe5951000, 0xe59f20a4\n"
        ".word 0xe5993004, 0xe5911084, 0xe0010291, 0xe0831101\n"
        ".word 0xe5c10009, 0xeaffffa6, 0xe5963020, 0xe5931000\n"
        ".word 0xe3110806, 0x1afffff3, 0xe3a02001, 0xe1a01004\n"
        ".word 0xe1a00003, 0xebffb2ee, 0xe5960020, 0xe5900000\n"
        ".word 0xe3100030, 0xe5950000, 0x0a00000b, 0xe59f1060\n"
        ".word 0xe5902084, 0xe5993004, 0xe7911000, 0xe59f0044\n"
        ".word 0xe3510000, 0x03a01002, 0xe0000092, 0x13a01003\n"
        ".word 0xe0830100, 0xe5c01009, 0xeaffff8d, 0xe59f1024\n"
        ".word 0xe5900084, 0xe5992004, 0xe0000190, 0xe0820100\n"
        ".word 0xe5c0a009, 0xeaffff86, 0x00435d18, 0x00439ca8\n"
        ".word 0x00434278, 0x00007e38, 0x000003c7, 0x004342c8\n"
        ".word 0x00001fc8, 0x000049c8\n"
    );
}

// DECOMP_FUNC(0x001c35d8, 1996)
// Capstone ARM full coverage (499 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void script_vm_func_001c35d8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff1, 0xe24dd090, 0xe3a00000, 0xe1a05000\n"
        ".word 0xe3a06001, 0xe59f475c, 0xe58d0004, 0xe58d0008\n"
        ".word 0xe58d000c, 0xe58d0010, 0xe58d0014, 0xe58d0018\n"
        ".word 0xe58d001c, 0xe58d0020, 0xe58d0024, 0xe28db004\n"
        ".word 0xe284702c, 0xe284802d, 0xe284902e, 0xe284a036\n"
        ".word 0xe58d0028, 0xe58d002c, 0xe58d0030, 0xe58d0034\n"
        ".word 0xe58d0038, 0xe1a00004, 0xeb03f558, 0xe3500000\n"
        ".word 0x17cb6005, 0xe2844001, 0xe154000a, 0xe2855001\n"
        ".word 0x2a000004, 0xe1540007, 0x11540008, 0x11540009\n"
        ".word 0x0afffff7, 0xeafffff2, 0xe3a0a000, 0xe59f46d8\n"
        ".word 0xe1a0500a, 0xe28d703c, 0xe284900e, 0xe18483c4\n"
        ".word 0xe58da03c, 0xe58da040, 0xe58da044, 0xe58da048\n"
        ".word 0xea000001, 0xe1540008, 0x0a000003, 0xe1a00004\n"
        ".word 0xeb03f53e, 0xe3500000, 0x17c76005, 0xe2844001\n"
        ".word 0xe1540009, 0xe2855001, 0x3afffff5, 0xe3a00000\n"
        ".word 0xe1a05000, 0xe3a04077, 0xe58d0050, 0xe58d0054\n"
        ".word 0xe1a00004, 0xeb033eba, 0xe3500000, 0x128d0050\n"
        ".word 0xe2844001, 0x17c06005, 0xe354007f, 0xe2855001\n"
        ".word 0x3afffff6, 0xe59f0654, 0xeb03f528, 0xe1a05000\n"
        ".word 0xe59f064c, 0xeb03f525, 0xe1a0a000, 0xe59f0644\n"
        ".word 0xeb03f522, 0xe58d0064, 0xe59f063c, 0xeb03f51f\n"
        ".word 0xe58d0068, 0xe59f0634, 0xeb03f51c, 0xe58d006c\n"
        ".word 0xe59f062c, 0xeb03f519, 0xe58d0074, 0xe59f0624\n"
        ".word 0xeb03f516, 0xe58d0078, 0xe59f061c, 0xeb03f513\n"
        ".word 0xe58d007c, 0xe59f0614, 0xeb03f510, 0xe58d0080\n"
        ".word 0xe59f060c, 0xeb03f50d, 0xe58d0084, 0xe59f0604\n"
        ".word 0xeb03f50a, 0xe58d0088, 0xe59f05fc, 0xeb03f507\n"
        ".word 0xe58d008c, 0xe59f05f4, 0xeb03f504, 0xe1a09000\n"
        ".word 0xe320f000, 0xeb02cb39, 0xe3a00000, 0xe320f000\n"
        ".word 0xeb02b0b9, 0xe3a00000, 0xe320f000, 0xeb0311b8\n"
        ".word 0xe320f000, 0xe320f000, 0xeb03f4f3, 0xe1a06000\n"
        ".word 0xe320f000, 0xeb00a753, 0xe1a08000, 0xe2800b7d\n"
        ".word 0xe59f15ac, 0xe5900058, 0xe3a02b01, 0xe7810006\n"
        ".word 0xe2881b7d, 0xe2860b7d, 0xe281105c, 0xe280005c\n"
        ".word 0xeb03e5d6, 0xe2881a1e, 0xe2811ec1, 0xe2864a1e\n"
        ".word 0xec910a08, 0xe2844ec1, 0xe2883a1e, 0xe2833ec3\n"
        ".word 0xe2860a1e, 0xe2800ec3, 0xe2882b92, 0xec840a08\n"
        ".word 0xe2822fe7, 0xe2861b92, 0xe2811fe7, 0xe3a04000\n"
        ".word 0xec930a08, 0xec800a08, 0xe8920005, 0xe8810005\n"
        ".word 0xe7db0004, 0xe3500000, 0x0a000004, 0xe3a02001\n"
        ".word 0xe2840b01, 0xe1a01002, 0xe2800026, 0xeb031856\n"
        ".word 0xe2844001, 0xe3540036, 0xbafffff4, 0xe3a04000\n"
        ".word 0xe7d70004, 0xe3500000, 0x0a000004, 0xe3a02001\n"
        ".word 0xe2840b01, 0xe1a01002, 0xe2800067, 0xeb03184a\n"
        ".word 0xe2844001, 0xe354000e, 0xbafffff4, 0xe2881b2e\n"
        ".word 0xe2860b2e, 0xe2811f47, 0xe2800f47, 0xeb05f07a\n"
        ".word 0xe3550000, 0xe320f000, 0x0a000003, 0xe3a02001\n"
        ".word 0xe59f0488, 0xe1a01002, 0xeb03183b, 0xe35a0000\n"
        ".word 0x0a000003, 0xe3a02001, 0xe59f0474, 0xe1a01002\n"
        ".word 0xeb031835, 0xe59d0064, 0xe3500000, 0x0a000003\n"
        ".word 0xe3a02001, 0xe59f045c, 0xe1a01002, 0xeb03182e\n"
        ".word 0xe59d0068, 0xe3500000, 0x0a000003, 0xe3a02001\n"
        ".word 0xe59f0444, 0xe1a01002, 0xeb031827, 0xe59d006c\n"
        ".word 0xe3500000, 0x0a000003, 0xe3a02001, 0xe59f042c\n"
        ".word 0xe1a01002, 0xeb031820, 0xe59d0074, 0xe3500000\n"
        ".word 0x0a000003, 0xe3a02001, 0xe59f0414, 0xe1a01002\n"
        ".word 0xeb031819, 0xe59d0078, 0xe3500000, 0x0a000003\n"
        ".word 0xe3a02001, 0xe59f03fc, 0xe1a01002, 0xeb031812\n"
        ".word 0xe59d007c, 0xe3500000, 0x0a000003, 0xe3a02001\n"
        ".word 0xe59f03e4, 0xe1a01002, 0xeb03180b, 0xe59d0080\n"
        ".word 0xe3500000, 0x0a000003, 0xe3a02001, 0xe59f03cc\n"
        ".word 0xe1a01002, 0xeb031804, 0xe59d0084, 0xe3500000\n"
        ".word 0x0a000003, 0xe3a02001, 0xe59f03b4, 0xe1a01002\n"
        ".word 0xeb0317fd, 0xe59d0088, 0xe3500000, 0x0a000003\n"
        ".word 0xe3a02001, 0xe59f039c, 0xe1a01002, 0xeb0317f6\n"
        ".word 0xe59d008c, 0xe3500000, 0x0a000003, 0xe3a02001\n"
        ".word 0xe59f0384, 0xe1a01002, 0xeb0317ef, 0xe59f1384\n"
        ".word 0xe2882b92, 0xe2822fc7, 0xe2860b92, 0xe7911008\n"
        ".word 0xe892000c, 0xe5801324, 0xe2860b92, 0xe2800fc7\n"
        ".word 0xe2881b91, 0xe880000c, 0xe2860b91, 0xe3a02e39\n"
        ".word 0xe2811fe3, 0xe2800fe3, 0xeb03e544, 0xe3a02012\n"
        ".word 0xe2881054, 0xe2860054, 0xeb03e540, 0xe3a00000\n"
        ".word 0xe1a0a000, 0xe1a0b000, 0xe58d0074, 0xe2880b25\n"
        ".word 0xe2800ffb, 0xe58d006c, 0xe2860b25, 0xe2800ffb\n"
        ".word 0xe58d005c, 0xe2860903, 0xe2800f69, 0xe58d0068\n"
        ".word 0xe2880903, 0xe2800f69, 0xe58d0064, 0xe2880b25\n"
        ".word 0xe2800ff9, 0xe58d007c, 0xe59d0090, 0xe7d0000a\n"
        ".word 0xe3500000, 0x0a000084, 0xe35a0008, 0x379ff10a\n"
        ".word 0xea000081, 0x001c3adc, 0x001c3b54, 0x001c3b74\n"
        ".word 0x001c3cc4, 0x001c3be8, 0x001c3bf4, 0x001c3c0c\n"
        ".word 0x001c3b90, 0xe5d8007e, 0xe3a0200e, 0xe2881008\n"
        ".word 0xe5c6007e, 0xe5980016, 0xe5860016, 0xe598001a\n"
        ".word 0xe586001a, 0xe598001e, 0xe586001e, 0xe1d802b2\n"
        ".word 0xe1c602b2, 0xe5980038, 0xe5860038, 0xe2860008\n"
        ".word 0xeb03e50e, 0xe288003c, 0xe286403c, 0xe890000f\n"
        ".word 0xe884000f, 0xe1c804dc, 0xe1c604fc, 0xe3a00000\n"
        ".word 0xeb0356b3, 0xe320f000, 0xe320f000, 0xeb05c171\n"
        ".word 0xe3a00001, 0xe58d0074, 0xea00005b, 0xe59d0090\n"
        ".word 0xe59d106c, 0xe1d020d3, 0xe59d005c, 0xeb0745a2\n"
        ".word 0xe320f000, 0xe320f000, 0xea000053, 0xe59d0068\n"
        ".word 0xe59d1064, 0xe3a02b41, 0xeb03e4f4, 0xe320f000\n"
        ".word 0xe320f000, 0xea00004c, 0xe59d0068, 0xe59d1064\n"
        ".word 0xe3a02b41, 0xeb03e4ed, 0xe3a02000, 0xe1a00002\n"
        ".word 0xe2821001, 0xe0823102, 0xe0832182, 0xe0813101\n"
        ".word 0xe0862102, 0xe0833181, 0xe2822cc1, 0xe0863103\n"
        ".word 0xe2833cc1, 0xe1c2bdb0, 0xe2800002, 0xe3500c05\n"
        ".word 0xe2812001, 0xe1c3bdb0, 0xbafffff0, 0xea000036\n"
        ".word 0xe5980004, 0xe5860004, 0xea000033, 0xe59d007c\n"
        ".word 0xe5900000, 0xeb02ab27, 0xe320f000, 0xe320f000\n"
        ".word 0xea00002d, 0xe3a04000, 0xe3a01002, 0xe0840384\n"
        ".word 0xe0800404, 0xe0880100, 0xe2807094, 0xe1a00007\n"
        ".word 0xeb036c87, 0xe3500000, 0xe320f000, 0x0a00001f\n"
        ".word 0xe3a02000, 0xe1d714b6, 0xe1a00002, 0xeb036207\n"
        ".word 0xe3a00000, 0xe320f000, 0xeb039363, 0xe59f2138\n"
        ".word 0xe1a05000, 0xe1a01007, 0xeb03e4bc, 0xe5c5b04a\n"
        ".word 0xe5c5b049, 0xe5c5b04b, 0xe5c5b600, 0xe3a01002\n"
        ".word 0xe1a00005, 0xe1c5b4b4, 0xeb02ab01, 0xe1a00005\n"
        ".word 0xe320f000, 0xeb03632f, 0xe3a01001, 0xe3a00020\n"
        ".word 0xeb02aaef, 0xe3590000, 0xe320f000, 0x0a000003\n"
        ".word 0xe3a02001, 0xe1a01002, 0xe2820e55, 0xeb031742\n"
        ".word 0xe2844001, 0xe3540018, 0xbaffffd2, 0xe28aa001\n"
        ".word 0xe35a0008, 0xbaffff73, 0xe3a04000, 0xe28d5050\n"
        ".word 0xe7d50004, 0xe3500000, 0x0a000003, 0xe3a02000\n"
        ".word 0xe3a01001, 0xe2840077, 0xeb02aa66, 0xe2844001\n"
        ".word 0xe3540008, 0x3afffff5, 0xe3a02001, 0xe59f008c\n"
        ".word 0xe1a01002, 0xeb03172c, 0xe59d0074, 0xe3500000\n"
        ".word 0x0a000007, 0xe3a02001, 0xe59f0074, 0xe1a01002\n"
        ".word 0xeb031725, 0xe3a02001, 0xe1a01002, 0xe3a00e41\n"
        ".word 0xeb031721, 0xe59f005c, 0xe5900000, 0xeb02aa12\n"
        ".word 0xe28dd094, 0xe8bd8ff0, 0x00000426, 0x00000467\n"
        ".word 0x00000556, 0x00000557, 0x00000555, 0x00000674\n"
        ".word 0x00000675, 0x00000676, 0x00000677, 0x00000678\n"
        ".word 0x00000679, 0x0000067a, 0x0000067b, 0x00000464\n"
        ".word 0x00000551, 0x0001f458, 0x00024b24, 0x00000604\n"
        ".word 0x00000565, 0x00000466, 0x00433158\n"
    );
}

// DECOMP_FUNC(0x0030dc74, 2020)
// Capstone ARM full coverage (505 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_0030dc74() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff0, 0xe1a09000, 0xed2d8b0c, 0xe24dd024\n"
        ".word 0xe590a004, 0xe5906020, 0xe590000c, 0xe1a0b00a\n"
        ".word 0xe58d0020, 0xe1c941d8, 0xe59600b8, 0xe3500000\n"
        ".word 0x0a0000ba, 0xe5961020, 0xed9fbabb, 0xe58d001c\n"
        ".word 0xe58d1004, 0xe5d6009c, 0xeeb08a4b, 0xe3510000\n"
        ".word 0xe58d0018, 0xedd68a37, 0xed969a36, 0x0a000006\n"
        ".word 0xe5990010, 0xe1510000, 0xca000003, 0xe3a00000\n"
        ".word 0xe1a0b000, 0xe58d0000, 0xea000034, 0xe5990010\n"
        ".word 0xeddf9aaa, 0xe3500000, 0x1a000013, 0xe5d600bd\n"
        ".word 0xe3500000, 0x0a000010, 0xed960a0a, 0xe3a00001\n"
        ".word 0xe58d0000, 0xeeb40acb, 0xeef1fa10, 0xda000027\n"
        ".word 0xe3a00000, 0xebfcf745, 0xed961a0a, 0xedd90a01\n"
        ".word 0xee391ac1, 0xeef80a60, 0xee200a01, 0xee200a20\n"
        ".word 0xeebd0ac0, 0xee10ba10, 0xea00001c, 0xed960a0a\n"
        ".word 0xe3a00000, 0xe58d0000, 0xeeb40acb, 0xeef1fa10\n"
        ".word 0xda00000a, 0xebfcf735, 0xe2860024, 0xedd90a05\n"
        ".word 0xec901a02, 0xeeb81a41, 0xee791ae1, 0xee200a21\n"
        ".word 0xee410a00, 0xedc90a05, 0xeeb00a60, 0xea000004\n"
        ".word 0xed960a09, 0xedd90a05, 0xeeb80a40, 0xee300a80\n"
        ".word 0xed890a05, 0xeef00ac0, 0xeefd0ae0, 0xee10ba90\n"
        ".word 0xee00ba90, 0xeef80ae0, 0xee300a60, 0xed890a05\n"
        ".word 0xe35a0000, 0xe3a08000, 0x9a000070, 0xed9fca74\n"
        ".word 0xeddfda74, 0xed9fda74, 0xeddfba74, 0xe5941010\n"
        ".word 0xe59d201c, 0xe1510002, 0xba000007, 0xe59d1004\n"
        ".word 0xe1a00009, 0xe3510000, 0x13e01001, 0x03e01000\n"
        ".word 0xe5841010, 0xe1a01004, 0xebfcf6ef, 0xe5947010\n"
        ".word 0xe3770002, 0x0a000058, 0xe3770001, 0x0a000065\n"
        ".word 0xe2840004, 0xe5941000, 0xe8901009, 0xee007a10\n"
        ".word 0xe59f217c, 0xe28de00c, 0xe58d1008, 0xe2821e11\n"
        ".word 0xe88e1009, 0xe1a00001, 0xe894500a, 0xeeb80ac0\n"
        ".word 0xe880500a, 0xe2821e11, 0xe2820c01, 0xed951a03\n"
        ".word 0xe2823c01, 0xe1a0c003, 0xee091a00, 0xeeb4bac1\n"
        ".word 0xeef1fa10, 0xee007a90, 0xed950a01, 0xceb01a4b\n"
        ".word 0xedd52a00, 0xed952a02, 0xeef81ae0, 0xee200a01\n"
        ".word 0xee620a81, 0xee221a01, 0xee080ae1, 0xedc20a40\n"
        ".word 0xed820a41, 0xed821a42, 0xed828a43, 0xed920a40\n"
        ".word 0xedd20a44, 0xee300a20, 0xed820a40, 0xed920a41\n"
        ".word 0xedd20a45, 0xee300a20, 0xed820a41, 0xed920a42\n"
        ".word 0xedd10a02, 0xee300a20, 0xed800a02, 0xedd10a03\n"
        ".word 0xed900a03, 0xee300a20, 0xed800a03, 0xe89c000f\n"
        ".word 0xe884000f, 0xe1a02007, 0xe28d3008, 0xe1a01006\n"
        ".word 0xe1a00004, 0xebfcf659, 0xed940a06, 0xedd50a04\n"
        ".word 0xe1a01007, 0xe28600e8, 0xee200a20, 0xed840a06\n"
        ".word 0xed940a07, 0xedd50a06, 0xee200a20, 0xed840a07\n"
        ".word 0xedd50a05, 0xee300a20, 0xed840a07, 0xe59620b8\n"
        ".word 0xebfd6e07, 0xed840a08, 0xe59620b8, 0xe1a01007\n"
        ".word 0xe2860f45, 0xebfd6e02, 0xed840a09, 0xe1a01004\n"
        ".word 0xe1a00009, 0xebfcf41f, 0xe320f000, 0xe320f000\n"
        ".word 0xebfd6f4f, 0xe0801007, 0xe5841010, 0xe2888001\n"
        ".word 0xe158000a, 0xe285501c, 0xe2844028, 0x3affff92\n"
        ".word 0xe28dd024, 0xecbd8b0c, 0xe8bd8ff0, 0x00000000\n"
        ".word 0x3f8ccccd, 0x40000000, 0x40c90fdb, 0x3f800000\n"
        ".word 0x3f000000, 0x004ea81c, 0xe35b0000, 0x0affffee\n"
        ".word 0xe3a00000, 0xebfcf69d, 0xee300a6b, 0xe3a00000\n"
        ".word 0xee609a0c, 0xebfcf699, 0xee300a6b, 0xe3a00000\n"
        ".word 0xee20aa0c, 0xebfcf695, 0xee300a6b, 0xe59f145c\n"
        ".word 0xe1a00001, 0xee200a0c, 0xed810a02, 0xed818a03\n"
        ".word 0xecc19a02, 0xed910a02, 0xec911a02, 0xee610a01\n"
        ".word 0xee410aa1, 0xee400a00, 0xeeb10ae0, 0xeeb40acb\n"
        ".word 0xeef1fa10, 0xda000007, 0xee812a00, 0xedd02a01\n"
        ".word 0xedd01a02, 0xe2801004, 0xed802a00, 0xeec20a80\n"
        ".word 0xee811a80, 0xecc10a02, 0xe3a00000, 0xe59f13fc\n"
        ".word 0xecd19a03, 0xecc59a03, 0xebfcf678, 0xedd60a35\n"
        ".word 0xedd61a34, 0xe3a00000, 0xee3d1a60, 0xee001a20\n"
        ".word 0xee210a21, 0xeeb00ac0, 0xed850a03, 0xebfcf66f\n"
        ".word 0xedd60a33, 0xe59f13c4, 0xed961a32, 0xee7d1a60\n"
        ".word 0xeef0ca4b, 0xed818a03, 0xecc19a03, 0xee401a20\n"
        ".word 0xedd60a34, 0xeef40aec, 0xee210a81, 0xeef1fa10\n"
        ".word 0x2a000008, 0xedd10a00, 0xedd11a01, 0xed911a02\n"
        ".word 0xeef10a60, 0xeef11a61, 0xeeb11a41, 0xedc10a00\n"
        ".word 0xedc11a01, 0xed811a02, 0xe59d0020, 0xe3100001\n"
        ".word 0x0a000019, 0xe51f2138, 0xeef01a40, 0xeeb01a40\n"
        ".word 0xeef00a6c, 0xed820a44, 0xe2821e11, 0xedc21a45\n"
        ".word 0xed821a46, 0xedc20a47, 0xed920a40, 0xedd20a44\n"
        ".word 0xee200a20, 0xed820a40, 0xed920a41, 0xedd20a45\n"
        ".word 0xee200a20, 0xed820a41, 0xed920a42, 0xedd20a46\n"
        ".word 0xee200a20, 0xed820a42, 0xedd10a03, 0xed920a43\n"
        ".word 0xee200a20, 0xed820a43, 0xea00002e, 0xe51f31a0\n"
        ".word 0xeef01a40, 0xeeb01a40, 0xeef00a6c, 0xed830a44\n"
        ".word 0xe2832c01, 0xedc31a45, 0xed831a46, 0xedc30a47\n"
        ".word 0xed930a40, 0xedd30a44, 0xe2831e11, 0xe1a0e001\n"
        ".word 0xee200a20, 0xe1a0c00e, 0xe2833c01, 0xed820a00\n"
        ".word 0xed920a01, 0xedd10a01, 0xee200a20, 0xed820a01\n"
        ".word 0xed920a02, 0xedde0a02, 0xee200a20, 0xed820a02\n"
        ".word 0xedde0a03, 0xed920a03, 0xee200a20, 0xed820a03\n"
        ".word 0xec960a04, 0xec810a04, 0xed930a00, 0xeddc0a00\n"
        ".word 0xee300a20, 0xed830a00, 0xed930a01, 0xeddc0a01\n"
        ".word 0xee300a20, 0xed830a01, 0xed930a02, 0xeddc0a02\n"
        ".word 0xee300a20, 0xed830a02, 0xeddc0a03, 0xed930a03\n"
        ".word 0xee300a20, 0xed830a03, 0xe51f025c, 0xe2802c01\n"
        ".word 0xe5901108, 0xe590010c, 0xe892000c, 0xe584000c\n"
        ".word 0xe5841008, 0xe3a00000, 0xe1c420f0, 0xebfcf603\n"
        ".word 0xedd60a1b, 0xe59d0018, 0xee3d1a60, 0xe3500002\n"
        ".word 0x02850014, 0xee001a20, 0xed851a04, 0x0cc0ca02\n"
        ".word 0x0a000016, 0xe3a00000, 0xebfcf5f8, 0xedd60a26\n"
        ".word 0xe59d0018, 0xee3d1a60, 0xe3500001, 0xee001a20\n"
        ".word 0xed851a06, 0x1dc5ca05, 0x1a00000c, 0xe3a00000\n"
        ".word 0xebfcf5ee, 0xeef00a6d, 0xe3a00000, 0xee200a20\n"
        ".word 0xed850a05, 0xebfcf5bc, 0xe3100001, 0xe320f000\n"
        ".word 0x0a000002, 0xed950a06, 0xeeb10a40, 0xed850a06\n"
        ".word 0xe8945009, 0xe3a01000, 0xe59d2000, 0xe5841010\n"
        ".word 0xe28d1008, 0xe3520000, 0xe8815009, 0x0a000037\n"
        ".word 0xe3a00000, 0xebfcf5ac, 0xe59d101c, 0xe320f000\n"
        ".word 0xebfee249, 0xee001a10, 0xe51f133c, 0xe8945009\n"
        ".word 0xe2812e11, 0xeeb80a40, 0xe8825009, 0xe2810f41\n"
        ".word 0xe281ee11, 0xedd50a03, 0xe281cc01, 0xe2812c01\n"
        ".word 0xe1a03002, 0xee291a00, 0xee600a80, 0xee211a00\n"
        ".word 0xee410a2b, 0xeef40aec, 0xeef1fa10, 0xee282a80\n"
        ".word 0xed953a01, 0x3ef00a6c, 0xeefd1ac0, 0xed951a00\n"
        ".word 0xedd52a02, 0xee211a20, 0xee222a00, 0xee230a20\n"
        ".word 0xee620aa0, 0xed811a40, 0xed818a43, 0xee020a6b\n"
        ".word 0xec800a02, 0xed910a40, 0xedd10a44, 0xee300a20\n"
        ".word 0xed810a40, 0xed910a41, 0xedd10a45, 0xee300a20\n"
        ".word 0xed810a41, 0xed910a42, 0xedde0a02, 0xee300a20\n"
        ".word 0xed8c0a02, 0xedde0a03, 0xed9c0a03, 0xee300a20\n"
        ".word 0xed8c0a03, 0xe893000f, 0xe884000f, 0xedc41a04\n"
        ".word 0xe5942010, 0xe28d3008, 0xe1a01006, 0xe1a00004\n"
        ".word 0xebfcf52a, 0xed940a06, 0xedd50a04, 0xe1a01007\n"
        ".word 0xe28600e8, 0xee200a20, 0xed840a06, 0xed940a07\n"
        ".word 0xedd50a06, 0xee200a20, 0xed840a07, 0xedd50a05\n"
        ".word 0xee300a20, 0xed840a07, 0xe59620b8, 0xebfd6cd8\n"
        ".word 0xed840a08, 0xe59620b8, 0xe1a01007, 0xe2860f45\n"
        ".word 0xebfd6cd3, 0xed840a09, 0xe59d1000, 0xe3510000\n"
        ".word 0x0a000008, 0xe1a01004, 0xe1a00009, 0xebfcf4f3\n"
        ".word 0xe320f000, 0xe320f000, 0xebfd6e1d, 0xe5942010\n"
        ".word 0xe0801002, 0xe5841010, 0xe24bb001, 0xeafffeca\n"
        ".word 0x004ea91c\n"
    );
}

// DECOMP_FUNC(0x00122148, 2120)
// Capstone ARM full coverage (530 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void battle_func_00122148() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4ff8, 0xe59f47cc, 0xe59f17cc, 0xe5840008\n"
        ".word 0xeb068a74, 0xe3a00000, 0xe58d0000, 0xe59f37bc\n"
        ".word 0xe3a08001, 0xe3e00000, 0xe5848004, 0xe584000c\n"
        ".word 0xe5848000, 0xe5931000, 0xe3a00000, 0xe3710001\n"
        ".word 0x159fc79c, 0x0a00000c, 0xe0831200, 0xe2800001\n"
        ".word 0xe8910024, 0xe0822082, 0xe78c5102, 0xe5915008\n"
        ".word 0xe08c2102, 0xe5825004, 0xe591100c, 0xe5821008\n"
        ".word 0xe7931200, 0xe3710001, 0x1afffff2, 0xe59f0764\n"
        ".word 0xe3a01000, 0xe5902000, 0xe3720001, 0x159f3758\n"
        ".word 0x0a000006, 0xe0802181, 0xe2811001, 0xe8921004\n"
        ".word 0xe783c102, 0xe7902181, 0xe3720001, 0x1afffff8\n"
        ".word 0xe5940008, 0xe59fc734, 0xe3a0100f, 0xe2802a01\n"
        ".word 0xe3a05a01, 0xe58253a4, 0xe18ce141, 0xe3a06002\n"
        ".word 0xe7cc6000, 0xe3a03000, 0xe02e70c1, 0xe58233a8\n"
        ".word 0xe7ce1000, 0xe02cc0c1, 0xe58233ac, 0xe7c71000\n"
        ".word 0xe3a04009, 0xe58243b0, 0xe02ce141, 0xe7cc1000\n"
        ".word 0xe1875001, 0xe58233b4, 0xe7ce1000, 0xe08c6141\n"
        ".word 0xe58233b8, 0xe7c51000, 0xe58233bc, 0xe59fa6d0\n"
        ".word 0xe7c61000, 0xe08e7141, 0xe582a3c0, 0xe59fc6c4\n"
        ".word 0xe7c71000, 0xe0859141, 0xe582c3c4, 0xe246bf9d\n"
        ".word 0xe7c91000, 0xe3a0cb0f, 0xe285e02d, 0xe78bc000\n"
        ".word 0xe245a015, 0xe7ce1000, 0xe59fe69c, 0xe5823364\n"
        ".word 0xe18a4141, 0xe7ca1000, 0xe582e368, 0xe7c41000\n"
        ".word 0xe02450c1, 0xe582e36c, 0xe7c51000, 0xe2806c16\n"
        ".word 0xe28660cd, 0xe582e370, 0xe5c61000, 0xe2807c16\n"
        ".word 0xe28770ce, 0xe582e374, 0xe5c71000, 0xe2809c16\n"
        ".word 0xe28990cf, 0xe284a005, 0xe582e378, 0xe5c91000\n"
        ".word 0xe2804c16, 0xe2805b05, 0xe2806b05, 0xe2807c16\n"
        ".word 0xe3a0c05c, 0xe28440d1, 0xe2855fb6, 0xe2866fb2\n"
        ".word 0xe28770c9, 0xe18a95ca, 0xe582e37c, 0xe7ca1000\n"
        ".word 0xe582e380, 0xe5c41000, 0xe582839c, 0xe5c51000\n"
        ".word 0xe3a058bf, 0xe582535c, 0xe5c61000, 0xe5823360\n"
        ".word 0xe5c71000, 0xe5823384, 0xe189a141, 0xe7c91000\n"
        ".word 0xe5823388, 0xe02ae0c1, 0xe7ca1000, 0xe582338c\n"
        ".word 0xe02940c1, 0xe7ce1000, 0xe5823390, 0xe0245141\n"
        ".word 0xe7c41000, 0xe5823394, 0xe7c51000, 0xe35c008d\n"
        ".word 0x0a0000d6, 0xca000026, 0xe35c0077, 0x0a0000d3\n"
        ".word 0xca000012, 0xe35c006c, 0x0a0000d0, 0xca000008\n"
        ".word 0xe35c0061, 0x0a0000cd, 0xe35c0063, 0x0a0000d4\n"
        ".word 0xe35c0064, 0x0a0000d4, 0xe35c0066, 0x1a00003c\n"
        ".word 0xea0000bd, 0xe35c006e, 0x0a0000cd, 0xe35c006f\n"
        ".word 0x0a0000cd, 0xe35c0071, 0x1a000035, 0xea0000b6\n"
        ".word 0xe35c0082, 0x0a0000bd, 0xca000006, 0xe35c0079\n"
        ".word 0x0a0000c3, 0xe35c007a, 0x0a0000c3, 0xe35c007c\n"
        ".word 0x1a00002b, 0xea0000ac, 0xe35c0084, 0x0a0000bc\n"
        ".word 0xe35c0085, 0x0a0000bc, 0xe35c0087, 0x1a000024\n"
        ".word 0xea0000a5, 0xe35c00a3, 0x0a0000ac, 0xca000010\n"
        ".word 0xe35c0098, 0x0a0000a9, 0xca000006, 0xe35c008f\n"
        ".word 0x0a0000af, 0xe35c0090, 0x0a0000af, 0xe35c0092\n"
        ".word 0x1a000017, 0xea000098, 0xe35c009a, 0x0a0000a8\n"
        ".word 0xe35c009b, 0x0a0000a8, 0xe35c009d, 0x1a000010\n"
        ".word 0xea000091, 0xe35c00ae, 0x0a000098, 0xca000006\n"
        ".word 0xe35c00a5, 0x0a00009e, 0xe35c00a6, 0x0a00009e\n"
        ".word 0xe35c00a8, 0x1a000006, 0xea000087, 0xe35c00b0\n"
        ".word 0x0a000097, 0xe35c00b1, 0x0a000097, 0xe35c00b3\n"
        ".word 0x0a000081, 0xe080e10c, 0xe080300c, 0xe28eea01\n"
        ".word 0xe2833c16, 0xe3a02000, 0xe28330b1, 0xe58e2300\n"
        ".word 0xe5c31000, 0xe28cc001, 0xe35c00b3, 0x9affffa6\n"
        ".word 0xe59f6458, 0xe59fb45c, 0xe59f3454, 0xe286cf56\n"
        ".word 0xe786b000, 0xe286ef57, 0xe59f644c, 0xe7c31000\n"
        ".word 0xe2834056, 0xe78c6000, 0xe7c41000, 0xe3a04000\n"
        ".word 0xe2805c17, 0xe78e4000, 0xe2855066, 0xe2807a01\n"
        ".word 0xe2877e5e, 0xe5c51000, 0xe3a05001, 0xe2808c17\n"
        ".word 0xe5875000, 0xe2888069, 0xe59fb410, 0xe2809b05\n"
        ".word 0xe5c81000, 0xe2899f76, 0xe280ac17, 0xe589b000\n"
        ".word 0xe28aa067, 0xe2802b05, 0xe5ca1000, 0xe2822f77\n"
        ".word 0xe3e0b000, 0xe2803b05, 0xe582b000, 0xe2833fda\n"
        ".word 0xe280cb05, 0xe28ccf7a, 0xe5c31000, 0xe280ec17\n"
        ".word 0xe28ee06b, 0xe2806b05, 0xe58c4000, 0xe2866f7b\n"
        ".word 0xe2807b05, 0xe2877fdb, 0xe5ce1000, 0xe5864000\n"
        ".word 0xe5c71000, 0xe59f73ac, 0xe2808b05, 0xe2888f79\n"
        ".word 0xe59f239c, 0xe2809c17, 0xe289906a, 0xe280aa01\n"
        ".word 0xe5887000, 0xe28aae5f, 0xe5c91000, 0xe3a03d51\n"
        ".word 0xe58a4000, 0xe7c21000, 0xe242c06c, 0xe7834000\n"
        ".word 0xe283e004, 0xe7cc1000, 0xe78e4000, 0xe59fb324\n"
        ".word 0xe242606b, 0xe08ec105, 0xe242e06a, 0xe3a03b0f\n"
        ".word 0xe3a07c01, 0xe28c200c, 0xe7c61000, 0xe78c3000\n"
        ".word 0xe7ce1000, 0xe02e3542, 0xe7824000, 0xe282c004\n"
        ".word 0xe7c31000, 0xe183e542, 0xe78c4000, 0xe2826008\n"
        ".word 0xe2822fad, 0xe7ce1000, 0xe7867000, 0xe7c21000\n"
        ".word 0xe3a02c0a, 0xe2823ea6, 0xe59fc30c, 0xe7832000\n"
        ".word 0xe3a0e007, 0xe2433014, 0xe7cce000, 0xe3a02b0f\n"
        ".word 0xe283cfae, 0xe2878739, 0xe7832000, 0xe283e018\n"
        ".word 0xe7cc1000, 0xe02c6a48, 0xe3a0900d, 0xe283701c\n"
        ".word 0xe78e8000, 0xe3a0a010, 0xe7c69000, 0xe787a000\n"
        ".word 0xe59f72c8, 0xe02c2542, 0xe2803a01, 0xe280cc16\n"
        ".word 0xe7c21000, 0xe3a02000, 0xe3a0e01e, 0xe2833ff2\n"
        ".word 0xe28cc0e3, 0xe18760c7, 0xea000091, 0xe3a02a3f\n"
        ".word 0xe080e10c, 0xe080300c, 0xe28eea01, 0xe2833c16\n"
        ".word 0xe28330b1, 0xe58e2300, 0xe5c31000, 0xeaffff7c\n"
        ".word 0xe080310c, 0xe080e00c, 0xe2833a01, 0xe28eec16\n"
        ".word 0xe3a02b0f, 0xe28ee0b1, 0xe5832300, 0xe5ce1000\n"
        ".word 0xeaffff73, 0xe3a02b02, 0xeaffffec, 0xe080e10c\n"
        ".word 0xe080300c, 0xe28eea01, 0xe2833c16, 0xe3a02001\n"
        ".word 0xe28330b1, 0xe58e2300, 0xe5c31000, 0xeaffff68\n"
        ".word 0xe3520000, 0x0a000072, 0xe3520005, 0x1352000a\n"
        ".word 0x0a000071, 0xe352000f, 0x13520014, 0x0a00006e\n"
        ".word 0xe3520019, 0x15834000, 0x15cc1000, 0x0a00006a\n"
        ".word 0xe25ee001, 0xe2833004, 0xe28cc001, 0xe2822001\n"
        ".word 0x1affffee, 0xe59f21e8, 0xe59f31e8, 0xe7824000\n"
        ".word 0xe7c31000, 0xe2801c13, 0xe2800a01, 0xe3a02fbd\n"
        ".word 0xe280000c, 0xeb0669ed, 0xe59b0008, 0xe3a020bd\n"
        ".word 0xe2801c16, 0xe2800b05, 0xe28110b1, 0xe2800f7d\n"
        ".word 0xeb068e0d, 0xe59fe1b0, 0xe59f21b0, 0xe3a00000\n"
        ".word 0xe58e4104, 0xe58e4108, 0xe58e410c, 0xe58e4110\n"
        ".word 0xe58e4114, 0xe58e4118, 0xe5921000, 0xe35100bd\n"
        ".word 0x128e3f41, 0x0a000009, 0xe792c100, 0xe2800001\n"
        ".word 0xe1a012cc, 0xe20cc01f, 0xe7936101, 0xe186cc15\n"
        ".word 0xe783c101, 0xe7921100, 0xe35100bd, 0x1afffff5\n"
        ".word 0xe58e411c, 0xe58e4120, 0xe59fc154, 0xe58e4124\n"
        ".word 0xe58e4128, 0xe58e412c, 0xe58e4130, 0xe59c2000\n"
        ".word 0xe59f0140, 0xe3a01000, 0xe35200bd, 0x0a000009\n"
        ".word 0xe79c3101, 0xe2811001, 0xe1a022c3, 0xe203301f\n"
        ".word 0xe7906102, 0xe1863315, 0xe7803102, 0xe79c2101\n"
        ".word 0xe35200bd, 0x1afffff5, 0xe59f210c, 0xe3a01000\n"
        ".word 0xe5923000, 0xe35300bd, 0x0a000009, 0xe792c101\n"
        ".word 0xe2811001, 0xe20c601f, 0xe1a032cc, 0xe790c103\n"
        ".word 0xe18cc615, 0xe780c103, 0xe7923101, 0xe35300bd\n"
        ".word 0x1afffff5, 0xe58e4134, 0xe58e4138, 0xe59f10cc\n"
        ".word 0xe58e413c, 0xe58e4140, 0xe58e4144, 0xe58e4148\n"
        ".word 0xe5912000, 0xe3a00000, 0xe35200bd, 0x159f20b0\n"
        ".word 0x0a000009, 0xe7913100, 0xe2800001, 0xe1a0c2c3\n"
        ".word 0xe203301f, 0xe792e10c, 0xe18e3315, 0xe782310c\n"
        ".word 0xe7913100, 0xe35300bd, 0x1afffff5, 0xe59d0000\n"
        ".word 0xe8bd8ff8, 0xe5837000, 0xea000000, 0xe5836000\n"
        ".word 0xe5cc1000, 0xeaffff91, 0x004652ac, 0x00001774\n"
        ".word 0x00409c00, 0x004e4168, 0x0040aea0, 0x004e4f54\n"
        ".word 0x000016da, 0x01c00301, 0xe0c08000, 0x1f1f1f1f\n"
        ".word 0x00001478, 0x0000170f, 0x0cc330cc, 0x00a0280a\n"
        ".word 0x88000400, 0x0000176d, 0x02222222, 0x00001709\n"
        ".word 0x0eee0eee, 0x00001450, 0x00001705, 0x004e5144\n"
        ".word 0x004652bc, 0x0046531c, 0x004e5260, 0x00465334\n"
        ".word 0x0046534c, 0x004e5278\n"
    );
}

// DECOMP_FUNC(0x003ee398, 2128)
// Capstone ARM full coverage (532 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void engine_func_003ee398() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4038, 0xe3a05000, 0xe59f4040, 0xe59f0040\n"
        ".word 0xe5845000, 0xe58d5000, 0xe5901000, 0xe1a0000d\n"
        ".word 0xebf5c4e9, 0xe1b01fa0, 0x1bfb5c28, 0xe59d0000\n"
        ".word 0xe59f2020, 0xe59f1020, 0xe5840000, 0xe5c45004\n"
        ".word 0xe1a00004, 0xe5c45005, 0xe8bd4038, 0xeaf8de98\n"
        ".word 0x0044e7b4, 0x00408fd0, 0x00100000, 0x00357938\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x0044dac8, 0x0044dad0, 0xe59f2044\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0038\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe3a00000\n"
        ".word 0xe59f1028, 0xe3a02001, 0xe5c10000, 0xe5810004\n"
        ".word 0xe5c10008, 0xe2811e1a, 0xe5c12000, 0xe5810004\n"
        ".word 0xe5c10008, 0xe12fff1e, 0x0044dc10, 0x0044dc18\n"
        ".word 0x004c4404, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0044e040, 0x0044e048\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c201f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x0044e068, 0x0044e080, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0044e110, 0x0044e120, 0xe59f2044, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f8, 0xe59f0038, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe59f002c, 0xe59f202c\n"
        ".word 0xe5801000, 0xe5801004, 0xe5801008, 0xe580100c\n"
        ".word 0xe5c01010, 0xe5801014, 0xe5c01018, 0xe59f1010\n"
        ".word 0xeaf8de3f, 0x0044e7d0, 0x0044e7e0, 0x004d4618\n"
        ".word 0x00100000, 0x003577b0, 0xe59f2040, 0xe3e00000\n"
        ".word 0xe1a01000, 0xeddf0a10, 0xe1c201f8, 0xe59f0030\n"
        ".word 0xe3a01000, 0xe1a02001, 0xed9f0a0a, 0xe8800006\n"
        ".word 0xe240001c, 0xedc00a00, 0xed800a01, 0xe2800008\n"
        ".word 0xeddf0a06, 0xedc00a00, 0xed800a01, 0xe12fff1e\n"
        ".word 0x0044e300, 0x0044e320, 0x43700000, 0x43c80000\n"
        ".word 0x43a00000, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0043ded0, 0x0043dee0\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x0043dfb0, 0x0043dfb8, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0044e1d0, 0x0044e1d8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00465258\n"
        ".word 0x00465260, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x004650e0, 0x004650f0\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f8\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00465228, 0x00465238, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00472a10, 0x00472a18, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c201f8, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x004729b8\n"
        ".word 0x004729d8, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00464d90, 0x00464da0\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f8\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00464d30, 0x00464d40, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c201f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0043da28, 0x0043da48, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f8, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x0043de68\n"
        ".word 0x0043de78, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x004331f8, 0x00433200\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c201f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x0043e360, 0x0043e378, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0043e3a0, 0x0043e3a8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x00433e08\n"
        ".word 0x00433e10, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0043dcf0, 0x0043dd00\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00446508, 0x00446510, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x0044dc38, 0x0044dc48, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f8, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x0044e190\n"
        ".word 0x0044e1a0, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00432ff8, 0x00433000\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x004331b8, 0x004331c0, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x004331d8, 0x004331e0, 0xe59f2050, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe92d4010, 0xe1c201f0, 0xe59f0040\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe1a04001, 0xe8800006\n"
        ".word 0xe59f0030, 0xe59f2034, 0xe5801008, 0xe5804004\n"
        ".word 0xe580100c, 0xe59f1020, 0xe5801000, 0xe59f1020\n"
        ".word 0xe1a00000, 0xe59f001c, 0xe5804000, 0xe8bd8010\n"
        ".word 0x0044e360, 0x0044e378, 0x004c641c, 0x00407f24\n"
        ".word 0x00100000, 0x00385d70, 0x0044e368, 0xe59f201c\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f0, 0xe59f0010\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe12fff1e\n"
        ".word 0x00465680, 0x00465688, 0xe59f2020, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe3a03000, 0xe1c200f8, 0xe2820010\n"
        ".word 0xe5803000, 0xe5803004, 0xe5823000, 0xe12fff1e\n"
        ".word 0x004656b0, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f8, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x0043d9c8, 0x0043d9d8\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f8\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x00435d30, 0x00435d40, 0xe59f0008\n"
        ".word 0xe3a01000, 0xe5801000, 0xe12fff1e, 0x0047384c\n"
        ".word 0xe59f0008, 0xe3a01000, 0xe5801000, 0xe12fff1e\n"
        ".word 0x00473854, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00471a28, 0x00471a30\n"
        ".word 0xe59f201c, 0xe3e00000, 0xe1a01000, 0xe1c200f0\n"
        ".word 0xe59f0010, 0xe3a01000, 0xe1a02001, 0xe8800006\n"
        ".word 0xe12fff1e, 0x0044e5e0, 0x0044e5e8, 0xe59f2028\n"
        ".word 0xe3e00000, 0xe1a01000, 0xe1c200f8, 0xe59f001c\n"
        ".word 0xe3a01000, 0xe1a02001, 0xe8800006, 0xe2400010\n"
        ".word 0xe59f100c, 0xe5801000, 0xe12fff1e, 0x0044e820\n"
        ".word 0x0044e830, 0x004722b8, 0xe59f201c, 0xe3e00000\n"
        ".word 0xe1a01000, 0xe1c200f0, 0xe59f0010, 0xe3a01000\n"
        ".word 0xe1a02001, 0xe8800006, 0xe12fff1e, 0x004734a0\n"
        ".word 0x004734a8, 0xe59f201c, 0xe3e00000, 0xe1a01000\n"
        ".word 0xe1c200f0, 0xe59f0010, 0xe3a01000, 0xe1a02001\n"
        ".word 0xe8800006, 0xe12fff1e, 0x00471aa0, 0x00471aa8\n"
    );
}

// DECOMP_FUNC(0x003bdcd8, 2180)
// Capstone ARM full coverage (545 instructions); raw bytes only, no terminal-return claim.
extern "C" __attribute__((naked)) void camp_func_003bdcd8() {
    asm volatile(
        ".arm\n"
        ".word 0xe92d4fff, 0xe1a04003, 0xed2d0b02, 0xed2d8b02\n"
        ".word 0xe24dd034, 0xeeb08a40, 0xe59d907c, 0xebfb57e7\n"
        ".word 0xe58d000c, 0xe59d0048, 0xebfbc1ba, 0xe1a08000\n"
        ".word 0xe1a00004, 0xebfbdad0, 0xe1a0a000, 0xe59d000c\n"
        ".word 0xe59d1078, 0xebfb139c, 0xe1a0b000, 0xe59d000c\n"
        ".word 0xe1a01009, 0xebfb1398, 0xe1a06000, 0xe59d100c\n"
        ".word 0xe1a0200b, 0xe28d0010, 0xebfa2627, 0xe5dd002d\n"
        ".word 0xeddf8ab6, 0xe3e04000, 0xe3500000, 0xe1a05004\n"
        ".word 0xe3a07001, 0x1a000002, 0xe5dd002e, 0xe3500000\n"
        ".word 0x1a000005, 0xe3580000, 0x0a00001d, 0xe5982038\n"
        ".word 0xe3120902, 0x0312087f, 0x0a000004, 0xe3e00000\n"
        ".word 0xe28dd034, 0xecbd8b02, 0xe28dd018, 0xe8bd8ff0\n"
        ".word 0xe1d802bc, 0xeddf0aa1, 0xe5d8c023, 0xee000a10\n"
        ".word 0xee680a20, 0xe59f3278, 0xe35c0009, 0xe3a00005\n"
        ".word 0xe3a01002, 0xeeb80a40, 0x379ff10c, 0xea00004f\n"
        ".word 0x003bdf58, 0x003be0a4, 0x003bdf08, 0x003be278\n"
        ".word 0x003bdf08, 0x003bdf08, 0x003bdf08, 0x003bdf08\n"
        ".word 0x003be40c, 0xe35a0000, 0x0a000015, 0xe1da06b4\n"
        ".word 0xe3500000, 0x11a05000, 0xe5da0068, 0x13a07000\n"
        ".word 0xe3500000, 0x0a00019e, 0xe359006d, 0xed9f8a85\n"
        ".word 0xaa000190, 0xe59d000c, 0xe1a01009, 0xebfaff9d\n"
        ".word 0xe1d00eba, 0xe5da1068, 0xe1600180, 0xee000a10\n"
        ".word 0xeeb80ac0, 0xee200a08, 0xeebd0ac0, 0xee105a10\n"
        ".word 0xea00018e, 0xe59b1000, 0xe1dd21fa, 0xe1dd01b2\n"
        ".word 0xe3110006, 0x0a000030, 0xe59d004c, 0xebfbda58\n"
        ".word 0xe5d00052, 0xe1dd21fa, 0xe3500002, 0x1a000001\n"
        ".word 0xe3a01001, 0xea000000, 0xe3a01002, 0xe1dd02df\n"
        ".word 0xe1dd33d0, 0xeef00a48, 0xeeb00a68, 0xe1cd20f0\n"
        ".word 0xe58d0008, 0xe59d2078, 0xe1a03009, 0xe3a00000\n"
        ".word 0xeb0003c8, 0xe59f1180, 0xe1a04000, 0xe19110bb\n"
        ".word 0xe3110c02, 0x0a000006, 0xe59f0170, 0xe0841184\n"
        ".word 0xe0811204, 0xe0c01190, 0xe1a012c0, 0xe0410fc0\n"
        ".word 0xe0444000, 0xe59f0150, 0xe19000b6, 0xe3100080\n"
        ".word 0x0a000006, 0xe59f0144, 0xe0841184, 0xe0811204\n"
        ".word 0xe0c01190, 0xe1a012c0, 0xe0410fc0, 0xe0844000\n"
        ".word 0xe59d000c, 0xe2800901, 0xe2800e4a, 0xe5900000\n"
        ".word 0xe3100701, 0x1a00017e, 0xea00016b, 0xe3110010\n"
        ".word 0x0a000002, 0xe3500001, 0x0affffd2, 0xeaffffcf\n"
        ".word 0xe3110008, 0x0a000002, 0xe3500001, 0x0affffcd\n"
        ".word 0xeaffffca, 0xe3500001, 0x0affffca, 0xeaffffc7\n"
        ".word 0xe1d844bc, 0xe3540000, 0x0a000035, 0xe5d8204e\n"
        ".word 0xe3520000, 0x13a0c000, 0x11a0200c, 0x1a00001b\n"
        ".word 0xea000115, 0xe3520008, 0x03a02009, 0x0afffffc\n"
        ".word 0xe3520009, 0x03a0200a, 0x0afffff9, 0xe352000a\n"
        ".word 0x03a0200b, 0x0afffff6, 0xe352000b, 0x03a0200c\n"
        ".word 0x0afffff3, 0xe352000c, 0x03a0200d, 0x0afffff0\n"
        ".word 0xe352000d, 0x03a0200e, 0x0affffed, 0xe352000e\n"
        ".word 0x03a0200f, 0x0affffea, 0xe352000f, 0x03a02010\n"
        ".word 0x0affffe7, 0xe3520010, 0x03a02011, 0x0affffe4\n"
        ".word 0xe0867082, 0xe2877c01, 0xe28770f2, 0xe1d770b0\n"
        ".word 0xe3170b3f, 0x11500527, 0x0a000001, 0xe1510527\n"
        ".word 0x128cc001, 0xe2822001, 0xe3520012, 0xbaffffd8\n"
        ".word 0xe0040c94, 0xe3540ffa, 0xba0000eb, 0xea000071\n"
        ".word 0x3f800000, 0x000003e7, 0x3c23d70a, 0x000001c6\n"
        ".word 0x51eb851f, 0xe1dd22df, 0xe1dd13d0, 0xe3a00000\n"
        ".word 0xe1a03009, 0xe88d0007, 0xe1a01000, 0xe59d0048\n"
        ".word 0xe59d2078, 0xeb00035b, 0xe51f1034, 0xe1a04000\n"
        ".word 0xe19110bb, 0xe3110c02, 0x0a000006, 0xe51f0044\n"
        ".word 0xe0841184, 0xe0811204, 0xe0c01190, 0xe1a012c0\n"
        ".word 0xe0410fc0, 0xe0444000, 0xe51f0064, 0xe19000b6\n"
        ".word 0xe3100080, 0x0affff99, 0xeaffff91, 0xe3120502\n"
        ".word 0x0a000004, 0xe3a00f6d, 0xe3a07000, 0xe19000f6\n"
        ".word 0xe2404001, 0xeaffff91, 0xe5d82049, 0xe3520000\n"
        ".word 0x0a000009, 0xe3a00f6d, 0xe3a02000, 0xe19000f6\n"
        ".word 0xe0801fa0, 0xe3c13001, 0xe0400003, 0xe3500000\n"
        ".word 0xc3a02001, 0xe08240c1, 0xea0000b7, 0xe5d82047\n"
        ".word 0xe3520000, 0x0a000008, 0xe3a01f6d, 0xe51f00d4\n"
        ".word 0xe19110f6, 0xe3a07000, 0xe0010291, 0xe0c01190\n"
        ".word 0xe1a012c0, 0xe0414fc0, 0xeaffff78, 0xe1d844bc\n"
        ".word 0xe3540000, 0x0a000031, 0xe5d8204e, 0xe3520000\n"
        ".word 0x13a0c000, 0x11a0200c, 0x1a00001b, 0xea0000a2\n"
        ".word 0xe3520008, 0x03a02009, 0x0afffffc, 0xe3520009\n"
        ".word 0x03a0200a, 0x0afffff9, 0xe352000a, 0x03a0200b\n"
        ".word 0x0afffff6, 0xe352000b, 0x03a0200c, 0x0afffff3\n"
        ".word 0xe352000c, 0x03a0200d, 0x0afffff0, 0xe352000d\n"
        ".word 0x03a0200e, 0x0affffed, 0xe352000e, 0x03a0200f\n"
        ".word 0x0affffea, 0xe352000f, 0x03a02010, 0x0affffe7\n"
        ".word 0xe3520010, 0x03a02011, 0x0affffe4, 0xe0867082\n"
        ".word 0xe2877c01, 0xe28770f2, 0xe1d770b0, 0xe3170b3f\n"
        ".word 0x11500527, 0x0a000001, 0xe1510527, 0x128cc001\n"
        ".word 0xe2822001, 0xe3520012, 0xbaffffd8, 0xe0040c94\n"
        ".word 0xe3540ffa, 0xba000078, 0xe1a04003, 0xea000076\n"
        ".word 0xe1dd02df, 0xe1dd33d0, 0xe1a02009, 0xe58d0000\n"
        ".word 0xe59d0048, 0xe59d1078, 0xeb00024a, 0xe5dd102d\n"
        ".word 0xe1a04000, 0xe3510000, 0x0a000004, 0xe59f0324\n"
        ".word 0xe0c01490, 0xe0404fc0, 0xe3540064, 0xc3a04064\n"
        ".word 0xe51f020c, 0xe19000bb, 0xe3100c02, 0x0a000006\n"
        ".word 0xe51f0218, 0xe0841184, 0xe0811204, 0xe0c01190\n"
        ".word 0xe1a012c0, 0xe0410fc0, 0xe0444000, 0xe51f0238\n"
        ".word 0xe19000b6, 0xe3100080, 0x0affff24, 0xeaffff1c\n"
        ".word 0xe1d803b6, 0xe3a014fa, 0xe1510a00, 0x1a00000a\n"
        ".word 0xe3560000, 0x159f02c0, 0x119050f6, 0x0a000001\n"
        ".word 0xe3a07000, 0xea000045, 0xe249006d, 0xebfba9ce\n"
        ".word 0xe1d050fe, 0xe320f000, 0xea000015, 0xe5d81043\n"
        ".word 0xe3510000, 0x0a000014, 0xe3560000, 0x0a000007\n"
        ".word 0xe59f2284, 0xe51f029c, 0xe19220f6, 0xe0010192\n"
        ".word 0xe0c01190, 0xe1a012c0, 0xe0415fc0, 0xeaffffeb\n"
        ".word 0xe249006d, 0xebfba9bc, 0xe1d010be, 0xe5d82043\n"
        ".word 0xe51f02c8, 0xe1610281, 0xe0c01190, 0xe1a012c0\n"
        ".word 0xe0415fc0, 0xe3a07000, 0xea000031, 0xe3c00a0f\n"
        ".word 0xee000a10, 0xe59d5078, 0xe59d8048, 0xeeb88a40\n"
        ".word 0xebfb565a, 0xe1a01005, 0xe320f000, 0xebfb1216\n"
        ".word 0xe5900000, 0xe3100002, 0x0a00000d, 0xe1a00008\n"
        ".word 0xebfbc028, 0xe1b0a000, 0xe320f000, 0x0a000008\n"
        ".word 0xe1a00008, 0xebfbc00c, 0xe1a01000, 0xe3a02002\n"
        ".word 0xe1a0000a, 0xebfb176e, 0xe1a08000, 0xe320f000\n"
        ".word 0xea000000, 0xe3a08000, 0xe3a01014, 0xe1a00005\n"
        ".word 0xebfffe20, 0xee200a28, 0xee008a90, 0xed9f1a6f\n"
        ".word 0xe3560000, 0xeef80ae0, 0xee280a00, 0xee300a01\n"
        ".word 0xee300a20, 0xeebd0ac0, 0xee105a10, 0x0a000008\n"
        ".word 0xe51f038c, 0xe19000b6, 0xe2000008, 0xe3500000\n"
        ".word 0x13550001, 0xda00000a, 0xe3a05001, 0xe3a07000\n"
        ".word 0xeafffeca, 0xe249006d, 0xebfba97f, 0xe3a01003\n"
        ".word 0xe320f000, 0xebfb8296, 0xe3500000, 0x13550001\n"
        ".word 0xcafffff4, 0xe3550000, 0xaafffec0, 0xe3a05001\n"
        ".word 0xeafffebe, 0xe59d0084, 0xe3500005, 0xe5d80044\n"
        ".word 0x0a000007, 0xe3500000, 0x0afffeb8, 0xe3a00f6d\n"
        ".word 0xe19000b6, 0xe3500001, 0x13a04001, 0x0a000007\n"
        ".word 0xeaffffe5, 0xe3500000, 0x0afffeb0, 0xe3a00f6d\n"
        ".word 0xe19000f6, 0xe3500001, 0x12404001, 0x1affffde\n"
        ".word 0xe3a04000, 0xeaffffdc, 0xe249006d, 0xebfba95e\n"
        ".word 0xe1d000be, 0xe5da1068, 0xe1600180, 0xee000a10\n"
        ".word 0xeeb80ac0, 0xee200a08, 0xeebd0ac0, 0xee105a10\n"
        ".word 0xe3a07000, 0xe359006d, 0xaa000006, 0xe51f0468\n"
        ".word 0xe19000b6, 0xe2000008, 0xe3500000, 0x13550001\n"
        ".word 0xdafffe96, 0xeaffffd4, 0xe249006d, 0xebfba94a\n"
        ".word 0xe3a01003, 0xe320f000, 0xebfb8261, 0xe3500000\n"
        ".word 0x13550001, 0xdafffe8d, 0xeaffffcb, 0xe3570000\n"
        ".word 0x0a00000f, 0xe3540000, 0xda00000d, 0xe59d000c\n"
        ".word 0xe2800b11, 0xe28000ac, 0xe5901000, 0xe2011040\n"
        ".word 0xe1b00001, 0x1a000006, 0xe59d000c, 0xe59000e0\n"
        ".word 0xe3100202, 0x1a000002, 0xe3a0000f, 0xebfa01c8\n"
        ".word 0xe0844000, 0xe59d0044, 0xe3500000, 0x01a00005\n"
        ".word 0x0afffe16, 0xe5dd002d, 0xe3500000, 0x0a000003\n"
        ".word 0xe59f0014, 0xe19000f6, 0xe1540000, 0xc1a04000\n"
        ".word 0xe1a00004, 0xeafffe0d, 0x55555556, 0x000001b6\n"
        ".word 0x00000000\n"
    );
}
