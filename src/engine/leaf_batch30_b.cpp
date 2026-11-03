#include "types.h"

// Batch 30 B: exact ARM bytes; post-return literal words are preserved as data.

// DECOMP_FUNC(0x00201318, 100)
extern "C" u32 func_00289640(void);
extern "C" u32 func_00296f60(u32);
extern "C" void eventCommand_func_0025955c(u32 owner, s32 frames, u32 mode, float alpha);

extern "C" u32 engine_func_00201318(void) {
    if (func_00289640() != 0) {
        u8* r0 = *reinterpret_cast<u8**>(0x0043E088);
        u32 r1 = *reinterpret_cast<u32*>(r0 + 0x10);
        u32 r0_val = *reinterpret_cast<u32*>(r0 + 0x14);
        return (r1 == r0_val) ? 1 : 0;
    }

    u32 owner = (func_00296f60(0) == 0) ? 0xFF : 0xFFFFFFFFu;
    eventCommand_func_0025955c(owner, 10, 1, 1.0f);
    return 0;
}

// DECOMP_FUNC(0x00211824, 124)
extern "C" void* func_00293c98(void);
extern "C" void func_00286928(u32, u32, u32, u32, u32, u32);

extern "C" void ui_func_00211824(void) {
    u8* ctx = reinterpret_cast<u8*>(func_00293c98());
    u32 elem = *reinterpret_cast<u32*>(ctx + 0x2234);
    u32 r6 = func_00296f60(0);
    u32 r2 = func_00289640();

    u8* obj = *reinterpret_cast<u8**>(0x0043E188 + 4);
    if (obj != nullptr) {
        obj[0xA11] = 0x14;
    }

    func_00286928(elem, r6, r2, 6, 0, 0);
}

// DECOMP_FUNC(0x002147e8, 108)
extern "C" void script_vm_func_002a7aa0(void* res);

extern "C" void script_vm_func_002147e8(void) {
    u8* sb = reinterpret_cast<u8*>(0x004BCE8C);
    for (s32 ch = 0; ch < 6; ++ch) {
        u8* ch_base = sb + ch * 256;
        for (s32 slot = 1; slot < 64; ++slot) {
            void** p_res = reinterpret_cast<void**>(ch_base + slot * 4 + 0x284);
            if (*p_res != nullptr) {
                script_vm_func_002a7aa0(*p_res);
                *p_res = nullptr;
            }
        }
        void** master = reinterpret_cast<void**>(sb + ch * 4 + 0x26C);
        if (*master != nullptr) {
            script_vm_func_002a7aa0(*master);
            *master = nullptr;
            *reinterpret_cast<void**>(ch_base + 0x284) = nullptr;
        }
    }
}

// DECOMP_FUNC(0x00218ae4, 112)
extern "C" void camp_func_002bf030(void* object, u32 selector);

extern "C" void camp_func_00218ae4(void* base) {
    u8* b = reinterpret_cast<u8*>(base);
    *reinterpret_cast<u32*>(b + 0x217C) = 0;
    *reinterpret_cast<u32*>(b + 0x2180) = 4;
    *reinterpret_cast<u16*>(b + 0x218E) = 0;

    s16 count = *reinterpret_cast<s16*>(b + 0x218C);
    if (count <= 0) {
        return;
    }

    for (s32 i = 0; i < count; ++i) {
        u8* r5 = b + i * 140;
        camp_func_002bf030(r5 + 0x20, 8);
        camp_func_002bf030(r5 + 0x598, 8);
    }
}

// DECOMP_FUNC(0x002196a4, 116)
extern "C" u32 battle_func_002ae3f0(u32 id);
extern "C" s32 battle_func_0029ac70(u32 id, u32 param);

extern "C" s32 battle_func_002196a4(const u16* a, const u16* b) {
    u16 idA = *a;
    if (idA == 0) {
        return 0;
    }
    u16 idB = *b;
    if (idB == 0) {
        return 0;
    }

    if (battle_func_002ae3f0(idA) == 0) {
        return 0;
    }
    if (battle_func_002ae3f0(idB) == 0) {
        return 0;
    }

    s16 statA = static_cast<s16>(battle_func_0029ac70(idA, 1));
    s16 statB = static_cast<s16>(battle_func_0029ac70(idB, 1));
    return static_cast<s32>(statA) - static_cast<s32>(statB);
}

// DECOMP_FUNC(0x00226d54, 96)
extern "C" float func_00226d54(const u8* ptr) {
    u32 state = *reinterpret_cast<const u32*>(ptr + 0x2C);
    u32 idx = 0;
    if (state == 4) {
        idx = 1;
    } else if (state == 5) {
        idx = 2;
    }

    if (*reinterpret_cast<const u32*>(ptr + 8) == 0) {
        return 0.0f;
    }

    const u8* const* p_c = reinterpret_cast<const u8* const*>(ptr + idx * 4);
    const u8* node1 = p_c[3];
    const u8* node2 = p_c[6];

    float max_val = 0.0f;
    if (node1 != nullptr) {
        max_val = *reinterpret_cast<const float*>(node1 + 0x38);
    }
    if (node2 != nullptr) {
        float val2 = *reinterpret_cast<const float*>(node2 + 0x38);
        if (val2 > max_val) {
            max_val = val2;
        }
    }
    return max_val;
}

// DECOMP_FUNC(0x00227c48, 96)
extern "C" void* ui_func_00282b94(void* inner, s32 idx);

extern "C" void ui_func_00227c48(void** container, u8* dst) {
    for (s32 i = 0; i < 109; ++i) {
        u8* slot = dst + 0x900 + i * 10;
        *reinterpret_cast<u16*>(slot + 0xD4) = 0;
        u8* item = reinterpret_cast<u8*>(ui_func_00282b94(*container, i));
        if (item != nullptr) {
            *reinterpret_cast<u16*>(slot + 0xD4) = *reinterpret_cast<u16*>(item + 0x1B4);
            *reinterpret_cast<u16*>(slot + 0xD6) = *reinterpret_cast<u16*>(item + 0x1B6);
        }
    }
}

// DECOMP_FUNC(0x00228338, 124)
extern "C" s32 battle_func_002934d4(void* context);
extern "C" s32 engine_func_002aa7f4(void* a1, void* a2);

extern "C" s32 ui_func_00228338(u8* ctx) {
    void* ui_ctx = func_00293c98();
    if (battle_func_002934d4(ui_ctx) != 0) {
        return -1;
    }

    u8* base = *reinterpret_cast<u8**>(ctx + 0x1CFC);
    for (s32 i = 0; i < 4; ++i) {
        u8* slot = base + 0x58 + i * 22;
        if (engine_func_002aa7f4(reinterpret_cast<void*>(0x00400958), slot) == 0) {
            return *reinterpret_cast<s16*>(slot + 0x10);
        }
    }
    return 30;
}

// DECOMP_FUNC(0x00229a34, 116)
extern "C" u32 script_vm_func_002b6e44(u32);

extern "C" u32 script_vm_func_00229a34(void) {
    u8** p_mgr = *reinterpret_cast<u8***>(0x00435D78);
    if (p_mgr == nullptr || *p_mgr == nullptr) {
        return 0;
    }

    for (u8* node = *p_mgr; node != nullptr; node = *reinterpret_cast<u8**>(node + 0x2A4)) {
        s16 field_2a2 = *reinterpret_cast<s16*>(node + 0x2A2);
        if (field_2a2 < 0) {
            continue;
        }
        u16 field_2 = *reinterpret_cast<u16*>(node + 2);
        if (field_2 != 1) {
            continue;
        }
        u16 field_6 = *reinterpret_cast<u16*>(node + 6);
        if ((field_6 & 1) != 0) {
            continue;
        }
        if (script_vm_func_002b6e44(field_6) != 0) {
            return 1;
        }
    }
    return 0;
}

// DECOMP_FUNC(0x0022a2b0, 116)
extern "C" void engine_func_002c4b30(void* ptr, u32 size);
extern "C" u32 engine_func_002a71c0(u32 a0, u32 a1, u32 a2, void* a3);
extern "C" void script_vm_func_00234d4c(void* obj, void* buf, u32 arg2, u32 arg3, u32 extra0, u32 extra1, u32 extra2);

extern "C" void script_vm_func_0022a2b0(u32 arg0, u32 arg1, u32 arg2, u32 arg3) {
    u8 buf[0x80];
    engine_func_002c4b30(buf, sizeof(buf));
    if (engine_func_002a71c0(arg0, 0x1F, arg1, buf) != 0) {
        void* obj = *reinterpret_cast<void**>(0x00433130);
        script_vm_func_00234d4c(obj, buf, arg3, arg2, 0, 4, 0);
    }
}

// DECOMP_FUNC(0x00230db0, 100)
extern "C" void* script_vm_func_0022ebbc(void);
extern "C" s32 ui_func_002c615c(void* item, s32 count);
extern "C" s32 camp_func_002b9100(void* obj);
extern "C" s32 camp_func_0028fde4(void* obj);

extern "C" s32 shop_func_00230db0(void* obj, s32 count) {
    void* item = script_vm_func_0022ebbc();
    s32 clamped = ui_func_002c615c(item, count);
    if (clamped < 0) {
        clamped = 0;
    } else if (clamped > 99) {
        clamped = 99;
    }

    s32 cap = camp_func_002b9100(obj);
    s32 current = camp_func_0028fde4(obj);
    s32 diff = cap - current;

    if (clamped < 0) {
        clamped = 0;
    } else if (diff < clamped) {
        clamped = diff;
    }
    return clamped;
}

// DECOMP_FUNC(0x00232974, 104)
extern "C" void func_00232974(const u8* src, u8* dst) {
    for (s32 i = 0; i <= 8; ++i) {
        s8 idx = static_cast<s8>(i);
        s16 val;
        if (idx < 0) {
            val = static_cast<s16>(0x8140);
        } else {
            const u8* p = src + idx * 2;
            u8 b0 = p[0xB0];
            u8 b1 = p[0xB1];
            val = static_cast<s16>((static_cast<u16>(b0) << 8) | b1);
        }
        dst[i * 2 + 0] = static_cast<u8>(static_cast<u16>(val) >> 8);
        dst[i * 2 + 1] = static_cast<u8>(val);
    }
}

// DECOMP_FUNC(0x00234304, 100)
extern "C" s32 engine_func_002b45f8(const void* s1, const void* s2, u32 n);

extern "C" u32 script_vm_func_00234304(void** container, const void* key) {
    u8* obj = reinterpret_cast<u8*>(*container);
    u32 count = *reinterpret_cast<u32*>(obj + 0x1C);
    if (count == 0) {
        return 0;
    }

    u8* entries = *reinterpret_cast<u8**>(obj + 0x18);
    for (u32 i = 0; i < count; ++i) {
        const void* entry_key = *reinterpret_cast<const void* const*>(entries + i * 8);
        if (engine_func_002b45f8(entry_key, key, 0x40) == 0) {
            return *reinterpret_cast<u32*>(entries + i * 8 + 4);
        }
    }
    return 0;
}

// DECOMP_FUNC(0x00234608, 100)
extern "C" u32 script_vm_func_00234608(void** container, const void* key) {
    u8* obj = reinterpret_cast<u8*>(*container);
    u32 count = *reinterpret_cast<u32*>(obj + 0x1C);
    if (count == 0) {
        return 0;
    }

    u8* entries = *reinterpret_cast<u8**>(obj + 0x18);
    for (u32 i = 0; i < count; ++i) {
        const void* entry_key = *reinterpret_cast<const void* const*>(entries + i * 8);
        if (engine_func_002b45f8(entry_key, key, 0x40) == 0) {
            return *reinterpret_cast<u32*>(entries + i * 8 + 4);
        }
    }
    return 0;
}

// DECOMP_FUNC(0x00234738, 116)
extern "C" s32 func_0023a390(void* arg1);
extern "C" void engine_func_002bad80(void* dst, s32 code);
extern "C" u32 ui_func_00353578(void* arg1, u32 arg2, u32 arg3);
extern "C" void engine_func_0023a358(void* arg1, u32 w0, u32 w1);

extern "C" void engine_func_00234738(void* dst, void* arg1, u32 arg2, u32 arg3) {
    s32 status = func_0023a390(arg1);
    if (status < 0) {
        engine_func_002bad80(dst, status);
        return;
    }

    u32 res = ui_func_00353578(arg1, arg2, arg3);
    u32 tmp[2];
    engine_func_002bad80(tmp, static_cast<s32>(res));
    engine_func_0023a358(arg1, tmp[0], tmp[1]);
    *reinterpret_cast<u64*>(dst) = *reinterpret_cast<u64*>(tmp);
}

// DECOMP_FUNC(0x00237f34, 104)
extern "C" u32 engine_func_00238990(void* arg0, u16 p0, u16 p1);

extern "C" u32 func_00237f34(void* arg0, u32 span_id) {
    const u32* span = reinterpret_cast<const u32*>(0x004171F8 + span_id * 8);
    u32 start = span[0];
    u32 count = span[1];
    if (count == 0) {
        return 1;
    }

    const u16* elems = reinterpret_cast<const u16*>(0x004149C0);
    for (s32 i = static_cast<s32>(start + count - 1); i >= static_cast<s32>(start); --i) {
        u16 p0 = elems[i * 2 + 0];
        u16 p1 = elems[i * 2 + 1];
        if (engine_func_00238990(arg0, p0, p1) == 0) {
            return 0;
        }
    }
    return 1;
}

// DECOMP_FUNC(0x0023a484, 96)
extern "C" u8* engine_func_00225dac(u32 id);
extern "C" u32 engine_func_003aff38(void* sub);

extern "C" u32 func_0023a484(const u8* obj) {
    u32 field_4 = *reinterpret_cast<const u32*>(obj + 4);
    u8* target = engine_func_00225dac(field_4);
    if (target == nullptr) {
        return 14;
    }

    u8* sub = *reinterpret_cast<u8**>(target + 0x10);
    if (sub == nullptr) {
        return 14;
    }

    s32 count = *reinterpret_cast<s32*>(sub + 0x48);
    for (s32 i = 0; i < count; ++i) {
        if (engine_func_003aff38(sub) == 0) {
            return 20;
        }
    }
    return 0;
}

// DECOMP_FUNC(0x0023a620, 112)
extern "C" void* engine_func_003eab5c(void* sub);

extern "C" u32 func_0023a620(const u8* obj, u32 arg1, u32* out_ptr) {
    if (obj == nullptr) {
        *out_ptr = 0;
        return 1;
    }

    u32 field_4 = *reinterpret_cast<const u32*>(obj + 4);
    u8* target = engine_func_00225dac(field_4);
    u8* sub = *reinterpret_cast<u8**>(target + 0x10);
    if (sub == nullptr || *reinterpret_cast<u32*>(sub + 0x48) == 0) {
        *out_ptr = 0;
        return 14;
    }

    u8* res = reinterpret_cast<u8*>(engine_func_003eab5c(sub));
    if (res == nullptr || res[0x14] != 0) {
        *out_ptr = 0;
        return 14;
    }

    *out_ptr = *reinterpret_cast<u32*>(sub + 0x48);
    return 0;
}

// DECOMP_FUNC(0x0023ec74, 100)
extern "C" void* camp_func_002c0ec4(u32, u32);
extern "C" void* camp_func_002c0e9c(void);
extern "C" u32 camp_func_002c0e4c(void*);
extern "C" void* engine_func_0022add0(void* obj, s32 idx);

extern "C" void* camp_func_0023ec74(s32 idx) {
    void* res1 = camp_func_002c0ec4(2, 2);
    u8* base = reinterpret_cast<u8*>(camp_func_002c0e9c());
    if (idx < 0) {
        return base;
    }

    u32 max_count = camp_func_002c0e4c(res1);
    if (static_cast<u32>(idx) >= max_count) {
        return base;
    }

    void* obj = *reinterpret_cast<void**>(0x00433158);
    void* item = engine_func_0022add0(obj, idx);
    if (item == nullptr) {
        return base + idx * 28;
    }
    return item;
}

// DECOMP_FUNC(0x00240744, 100)
extern "C" u8 battle_func_0024a80c(void*);
extern "C" u8 battle_func_00249fac(u32, const void*);

extern "C" void battle_func_00240744(u8* obj) {
    for (s32 i = 0; i < 11; ++i) {
        u8* slot = obj + 0x25C0 + i * 140;
        const u8* tag = *reinterpret_cast<const u8* const*>(slot + 4);
        if (tag != nullptr && tag[0] == 'V' && tag[1] == 'E' && tag[2] == 'R') {
            u8 code = battle_func_0024a80c(slot + 8);
            slot[0] = code;
            slot[0] = battle_func_00249fac(code, tag);
        }
    }
}

// DECOMP_FUNC(0x00240e1c, 112)
extern "C" void engine_func_002c5ab8(u32, u32);

extern "C" void engine_func_00240e1c(u32 cmd) {
    u32* state = reinterpret_cast<u32*>(0x0044CF60);
    if (state[0] == 0) {
        state[1] = cmd;
        if (cmd == 0x65) {
            engine_func_002c5ab8(0x1C, 6);
        } else if (cmd == 0x66) {
            engine_func_002c5ab8(0x1C, 7);
        } else if (cmd == 0x67) {
            engine_func_002c5ab8(0x1C, 8);
        }
    }
    state[0] += 1;
}

// DECOMP_FUNC(0x0024807c, 116)
extern "C" float func_002b3b34(u32);

extern "C" float ui_func_0024807c(float min_val, float max_val, float duration, float current_time) {
    if (duration == 0.0f) {
        return max_val;
    }
    if (current_time <= 0.0f) {
        return min_val;
    }
    if (current_time >= duration) {
        return max_val;
    }

    float range = max_val - min_val;
    u16 angle = static_cast<u16>(static_cast<u32>((current_time * 16384.0f) / duration));
    float factor = func_002b3b34(angle);
    return min_val + factor * range;
}

// DECOMP_FUNC(0x00248358, 96)
extern "C" void* script_vm_func_00248358(u32 id) {
    void* res1 = camp_func_002c0ec4(0x23, 2);
    u8* base1 = reinterpret_cast<u8*>(camp_func_002c0e9c());
    u32 count1 = camp_func_002c0e4c(res1);
    if (id < count1) {
        return base1 + id * 32;
    }

    u8* mgr = *reinterpret_cast<u8**>(0x00433158);
    u32 count2 = *reinterpret_cast<u32*>(mgr + 0x3F4);
    u8* base2 = *reinterpret_cast<u8**>(mgr + 0x3F8);
    if (id < count1 + count2) {
        return base2 + (id - count1) * 32;
    }
    return nullptr;
}

// DECOMP_FUNC(0x002483b8, 96)
extern "C" void* camp_func_002483b8(u32 id) {
    void* res1 = camp_func_002c0ec4(0x23, 0);
    u8* base1 = reinterpret_cast<u8*>(camp_func_002c0e9c());
    u32 count1 = camp_func_002c0e4c(res1);
    if (id < count1) {
        return base1 + id * 32;
    }

    u8* mgr = *reinterpret_cast<u8**>(0x00433158);
    u32 count2 = *reinterpret_cast<u32*>(mgr + 0x3E4);
    u8* base2 = *reinterpret_cast<u8**>(mgr + 0x3E8);
    if (id < count1 + count2) {
        return base2 + (id - count1) * 32;
    }
    return nullptr;
}

// DECOMP_FUNC(0x0024a964, 112)
extern "C" u32 engine_func_0024a964(void* target_key) {
    s32 max_count = *reinterpret_cast<s32*>(0x00433278);
    if (max_count <= 0) {
        return 0xFF;
    }

    u8* base = reinterpret_cast<u8*>(0x00478000);
    for (s32 i = 0; i < max_count; ++i) {
        u8 idx = static_cast<u8>(i);
        u8* entry = base + idx * 328;
        if (engine_func_002aa7f4(entry + 1, target_key) == 0) {
            return idx;
        }
    }
    return 0xFF;
}

// DECOMP_FUNC(0x0024b9d0, 116)
extern "C" void func_0024b9d0(const u8* obj, const u8* pos) {
    const u8* sub = *reinterpret_cast<const u8* const*>(obj + 0x20);
    s32 w = *reinterpret_cast<const s32*>(sub + 0xC0);
    s32 h = *reinterpret_cast<const s32*>(sub + 0xC4);
    s32 count = w * h;
    if (count <= 0) {
        return;
    }

    u8* base = *reinterpret_cast<u8**>(const_cast<u8*>(obj) + 0x18);
    s32 f4 = *reinterpret_cast<const s32*>(obj + 4);
    u32 slot_idx = (reinterpret_cast<uintptr_t>(pos) - reinterpret_cast<uintptr_t>(base)) / 40;
    u8* start_slot = base + (slot_idx * count + f4) * 40;

    for (s32 i = 0; i < count; ++i) {
        *reinterpret_cast<s32*>(start_slot + i * 40 + 0x10) = -1;
    }
}

// DECOMP_FUNC(0x00250960, 120)
extern "C" s32 battle_func_00245e2c(u32);

extern "C" void func_00250960(u8* ctx) {
    s16 val = static_cast<s16>(battle_func_00245e2c(1));
    u8* p1 = *reinterpret_cast<u8**>(ctx + 0x1FC0);
    u8* p2 = *reinterpret_cast<u8**>(ctx + 0x1E98);

    for (s32 i = 0; i < 109; ++i) {
        *reinterpret_cast<s16*>(p1 + i * 648 + 0x74) = val;
        float* vec = reinterpret_cast<float*>(p2 + i * 276 + 0x30);
        vec[0] = 0.0f;
        vec[1] = 0.0f;
        vec[2] = 0.0f;
    }
}

// DECOMP_FUNC(0x00253eb0, 116)
extern "C" void* engine_func_002c2b1c(void);

extern "C" void engine_func_00253eb0(const u8* arg0) {
    s16 target = *reinterpret_cast<const s16*>(arg0 + 0x13A);
    u8* base = reinterpret_cast<u8*>(engine_func_002c2b1c());

    for (s32 i = 0; i < 16; ++i) {
        u8* slot = base + i * 20;
        u8 flags = slot[0xF20];
        if ((flags & 1) != 0 && (flags & 4) != 0) {
            s16 val = *reinterpret_cast<s16*>(slot + 0xF26);
            if (val == target) {
                slot[0xF20] = flags | 0x10;
                return;
            }
        }
    }
}

// DECOMP_FUNC(0x00254298, 96)
extern "C" void* camp_func_00254298(u16 target_id) {
    void* res1 = camp_func_002c0ec4(0x24, 1);
    u8* base = reinterpret_cast<u8*>(camp_func_002c0e9c());
    u32 count = camp_func_002c0e4c(res1);
    if (count == 0) {
        return nullptr;
    }

    for (u32 i = 0; i < count; ++i) {
        u8* entry = base + i * 64;
        if (*reinterpret_cast<u16*>(entry) == target_id) {
            return entry;
        }
    }
    return nullptr;
}

// DECOMP_FUNC(0x00254a64, 96)
extern "C" void func_00254a64(u32 val) {
    if ((val & 0x80000000) != 0) {
        u32 cat = (val >> 10) & 0xFF;
        u32 code = val & 0x3FF;
        if (cat == 0x11 && code >= 360) {
            asm volatile("mov r3, #0x180\nadd r3, r3, #5" : : : "r3");
        }
    }
}

// DECOMP_FUNC(0x00256364, 112)
extern "C" u8* script_vm_func_002b6e60(void);
extern "C" void engine_func_002899c4(u32 id, u32 p1, u32 p2);

extern "C" void script_vm_func_00256364(void) {
    u8* ctx = script_vm_func_002b6e60();
    u16 flags = *reinterpret_cast<u16*>(ctx + 0x608);
    if ((flags & 1) == 0) {
        return;
    }

    u16 code = *reinterpret_cast<u16*>(ctx + 0x46);
    if (code == 0x2A3) {
        engine_func_002899c4(0x262, 0, 1);
    } else if (code == 0x2A5) {
        engine_func_002899c4(0x263, 0, 1);
    }

    *reinterpret_cast<u16*>(ctx + 0x46) = 0;
}

// DECOMP_FUNC(0x00256b04, 124)
extern "C" void* battle_func_00226b2c(void* mgr, s16 id, u32 p2, u32 p3);

extern "C" void battle_func_00256b04(s32 arg0, u32 arg1) {
    u8* mgr = *reinterpret_cast<u8**>(0x00434290);
    u8* node = reinterpret_cast<u8*>(battle_func_00226b2c(mgr, static_cast<s16>(arg0), 0, arg1));

    for (u8* curr = *reinterpret_cast<u8**>(mgr + 8); curr != nullptr; curr = *reinterpret_cast<u8**>(curr + 0xC)) {
        if (curr[4] == 0x34) {
            s16 curr_id = *reinterpret_cast<s16*>(curr);
            s16 node_id = *reinterpret_cast<s16*>(node);
            if (curr_id == node_id) {
                s16 node_f2 = *reinterpret_cast<s16*>(node + 2);
                if (node_f2 >= 0) {
                    *reinterpret_cast<s16*>(node + 2) = -1;
                    break;
                }
            }
        }
    }

    node[4] = 0x34;
}

// DECOMP_FUNC(0x00259760, 108)
extern "C" u32 engine_func_002bf41c(void*);

extern "C" void engine_func_00259760(void* new_entry) {
    u8* base = *reinterpret_cast<u8**>(0x0043DED0);

    for (s32 i = 0; i < 10; ++i) {
        void** slot = reinterpret_cast<void**>(base + 0x34 + i * 4);
        if (engine_func_002bf41c(*slot) == 0) {
            *slot = nullptr;
        }
    }

    for (s32 i = 0; i < 10; ++i) {
        void** slot = reinterpret_cast<void**>(base + 0x34 + i * 4);
        if (*slot == nullptr) {
            *slot = new_entry;
            return;
        }
    }
}

// DECOMP_FUNC(0x0025b640, 112)
extern "C" float script_vm_func_00287b4c(float x1, float y1, float z1, float x2, float y2, float z2);
extern "C" float script_vm_func_00287d54(float x1, float y1, float z1, float x2, float y2, float z2);

extern "C" u32 script_vm_func_0025b640(float x1, float y1, float z1, float x2, float y2, float z2, float threshold, float height_limit) {
    s32 mode = *reinterpret_cast<s32*>(0x0049F91C);
    if (mode >= 100) {
        float dist = script_vm_func_00287b4c(x1, y1, z1, x2, y2, z2);
        return (dist < threshold) ? 1 : 0;
    }

    float dy = y1 - y2;
    if (dy < 0.0f) {
        dy = -dy;
    }
    if (dy >= height_limit) {
        return 0;
    }

    float dist = script_vm_func_00287d54(x1, y1, z1, x2, y2, z2);
    return (dist < threshold) ? 1 : 0;
}

// DECOMP_FUNC(0x00262b60, 108)
extern "C" void engine_func_002c3b48(void* dst, u32 len);

extern "C" char* ui_func_00262b60(char* dst, const char* src, u32 max_len) {
    char* d = dst;
    const char* s = src;
    u32 rem = max_len;

    while (rem > 0) {
        char c = *s++;
        *d++ = c;
        rem--;
        if (c == '\0') {
            if (rem > 0) {
                engine_func_002c3b48(d, rem);
            }
            break;
        }
    }
    return dst;
}

// DECOMP_FUNC(0x00266e10, 120)
extern "C" u32 script_vm_func_00266e10(u32 idx) {
    u8 active = *reinterpret_cast<u8*>(0x004E3134);
    if (active == 0 || idx >= 16) {
        return 0;
    }

    u32 entry = *reinterpret_cast<u32*>(0x004E2F68 + idx * 4);
    u32 mask = 1u << idx;
    if (entry == 0) {
        *reinterpret_cast<u32*>(0x004E312C) &= ~mask;
    }

    u32 val = *reinterpret_cast<u32*>(0x004E312C);
    return (val & mask) ? 1 : 0;
}

// DECOMP_FUNC(0x00269f34, 124)
extern "C" void camp_func_002b9008(void);

extern "C" void camp_func_00269f34(void) {
    u8* mgr = *reinterpret_cast<u8**>(0x0043DA90);

    for (s32 i = 0; i < 3; ++i) {
        *reinterpret_cast<s16*>(mgr + 0xE22 + i * 2) = -1;
        *reinterpret_cast<s16*>(mgr + 0xE28 + i * 6) = -1;
        *reinterpret_cast<s16*>(mgr + 0xE2A + i * 6) = -1;
        *reinterpret_cast<s16*>(mgr + 0xE2C + i * 6) = -1;
        camp_func_002b9008();
        camp_func_002b9008();
        camp_func_002b9008();
        camp_func_002b9008();
    }

    mgr[0xE3B] = 0;
}

// DECOMP_FUNC(0x0026ca24, 104)
extern "C" void engine_func_002c4b30(void* dst, u32 len);
extern "C" void engine_func_002c5ff4(void* dst, const void* src, u32 len);

extern "C" void script_vm_func_0026ca24(const char* str) {
    u8* base = *reinterpret_cast<u8**>(0x0043E0F8);
    base[0x10] = 0;
    if (str == nullptr) {
        return;
    }

    engine_func_002c4b30(base + 0x154, 0x31);

    s32 len = 0;
    while (len < 0x31) {
        if (str[len] == '\0') {
            engine_func_002c5ff4(base + 0x154, str, len + 1);
            base[0x10] = 1;
            return;
        }
        len++;
    }
}

// DECOMP_FUNC(0x0026f3f8, 104)
extern "C" void script_vm_func_00296d8c(void* obj, u32 p1, s32 p2, u32 p3, u32 p4, u32 p5, u32 p6);

extern "C" void script_vm_func_0026f3f8(u32 arg0, u32 arg1) {
    u8* mgr = *reinterpret_cast<u8**>(0x0043DA2C);
    mgr[0x55C] = 1;
    mgr[0x4CB] = 1;

    if (arg0 != 0) {
        void* obj = *reinterpret_cast<void**>(mgr + 0x558);
        script_vm_func_00296d8c(obj, 3, -1, 0, 3, arg0, arg1);
    } else {
        mgr[0x4CB] = 0;
        mgr[0x55C] = 0;
        *reinterpret_cast<u32*>(mgr + 0x558) = 0;
    }
}

// DECOMP_FUNC(0x0026fc24, 124)
extern "C" u32 engine_func_002c583c(u32);
extern "C" void script_vm_func_002105f4(u32, u32);

extern "C" u32 script_vm_func_0026fc24(void) {
    if (engine_func_002c583c(1) != 0) {
        return 0;
    }

    u32 changed = 0;
    u8* slots = reinterpret_cast<u8*>(0x004C53C4);

    for (s32 i = 0; i < 2; ++i) {
        u8* slot = slots + i * 32;
        u32 flags = *reinterpret_cast<u32*>(slot + 0x1C);
        if ((flags & 2) != 0 && (flags & 0x30) != 0) {
            u32 arg0 = *reinterpret_cast<u32*>(slot);
            script_vm_func_002105f4(arg0, 0);

            *reinterpret_cast<u32*>(slot + 4) = 0;
            *reinterpret_cast<u32*>(slot + 8) = 0;
            *reinterpret_cast<u32*>(slot + 0xC) = 0;
            *reinterpret_cast<u32*>(slot + 0x10) = 0;
            *reinterpret_cast<u32*>(slot + 0x14) = 0;
            *reinterpret_cast<u32*>(slot + 0x18) = 0;
            *reinterpret_cast<u32*>(slot + 0x1C) = 0;
            changed = 1;
        }
    }

    return changed;
}

// DECOMP_FUNC(0x0027054c, 124)
extern "C" void engine_func_002c4360(void*);

extern "C" void script_vm_func_0027054c(void) {
    u8* base = reinterpret_cast<u8*>(0x00446FE8);

    for (s32 i = 0; i < 4; ++i) {
        void** slot = reinterpret_cast<void**>(base + 0x18 + i * 4);
        if (*slot != nullptr) {
            engine_func_002c4360(*slot);
            *slot = nullptr;
        }
    }

    *reinterpret_cast<void**>(base + 4) = nullptr;
    *reinterpret_cast<void**>(base + 8) = nullptr;
    *reinterpret_cast<void**>(base + 0xC) = nullptr;
    *reinterpret_cast<void**>(base + 0x10) = nullptr;
    *reinterpret_cast<void**>(base + 0x14) = nullptr;
    *base = 0;
}

// DECOMP_FUNC(0x00275c2c, 116)
extern "C" void ui_func_002c0a6c(void*);

extern "C" void script_vm_func_00275c2c(void) {
    u8* mgr = *reinterpret_cast<u8**>(0x0043E278);
    mgr[0xE8C] = 0;

    void** p0 = reinterpret_cast<void**>(mgr + 0xFDC);
    if (*p0 != nullptr) {
        ui_func_002c0a6c(*p0);
        *p0 = nullptr;
    }

    void** p1 = reinterpret_cast<void**>(mgr + 0xFE8);
    if (*p1 != nullptr) {
        ui_func_002c0a6c(*p1);
        *p1 = nullptr;
    }

    void** p2 = reinterpret_cast<void**>(mgr + 0xFE4);
    if (*p2 != nullptr) {
        ui_func_002c0a6c(*p2);
        *p2 = nullptr;
    }
}

// DECOMP_FUNC(0x002764d4, 124)
extern "C" void* Tbb_GetGlobalSubTable(u32 slot_id, u32 table_index);
extern "C" void* Tbb_GetPayloadData(void* table);
extern "C" u32 Tbb_GetRowCount(void* table);

extern "C" void* script_vm_func_002764d4(u32 index) {
    void* table = Tbb_GetGlobalSubTable(0x23, 5);
    u8* payload = reinterpret_cast<u8*>(Tbb_GetPayloadData(table));
    u32 row_count = Tbb_GetRowCount(table);

    if (index < row_count) {
        return payload + index * 44;
    }

    u8* mgr = *reinterpret_cast<u8**>(0x00433158);
    u32 extra_count = *reinterpret_cast<u32*>(mgr + 0x40C);
    u8* extra_payload = *reinterpret_cast<u8**>(mgr + 0x410);

    if (index < row_count + extra_count) {
        return extra_payload + (index - row_count) * 44;
    }

    return nullptr;
}

// DECOMP_FUNC(0x0027d9b8, 104)
extern "C" void* script_vm_func_0027d9b8(u32 index) {
    void* table = Tbb_GetGlobalSubTable(0x23, 1);
    u8* payload = reinterpret_cast<u8*>(Tbb_GetPayloadData(table));
    u32 row_count = Tbb_GetRowCount(table);

    if (index < row_count) {
        return payload + index * 12;
    }

    u8* mgr = *reinterpret_cast<u8**>(0x00433158);
    u32 extra_count = *reinterpret_cast<u32*>(mgr + 0x3EC);
    u8* extra_payload = *reinterpret_cast<u8**>(mgr + 0x3F0);

    if (index < row_count + extra_count) {
        return extra_payload + (index - row_count) * 12;
    }

    return nullptr;
}

// DECOMP_FUNC(0x002879c0, 124)
extern "C" u32 ui_func_002a63f8(u32 cat, u32 sub);

extern "C" u32 ui_func_002879c0(void) {
    u32 mode = *reinterpret_cast<u32*>(0x0044CF64);

    if (mode == 0x65) {
        if (ui_func_002a63f8(0x1C, 6) == 0) {
            return 0;
        }
    } else if (mode == 0x66) {
        if (ui_func_002a63f8(0x1C, 7) == 0) {
            return 0;
        }
    } else if (mode == 0x67) {
        if (ui_func_002a63f8(0x1C, 8) == 0) {
            return 0;
        }
    }

    return 1;
}

// DECOMP_FUNC(0x00287ce0, 116)
extern "C" float ui_func_002820a4(float dx, float dz);
extern "C" float script_vm_func_00287d74(float heading, float angle);

extern "C" float script_vm_func_00287ce0(float x1, float y1, float z1, float heading, float x2, float y2, float z2) {
    float rad = ui_func_002820a4(x2 - x1, z2 - z1);
    float deg = rad * 57.3248405456543f;
    if (deg < 0.0f) {
        deg += 360.0f;
    }
    if (deg > 360.0f) {
        deg -= 360.0f;
    }
    float delta = script_vm_func_00287d74(heading, deg);
    if (delta < 0.0f) {
        delta = -delta;
    }
    return delta;
}

// DECOMP_FUNC(0x00288990, 104)
extern "C" void script_vm_func_002a7aa0(void*);
extern "C" void engine_func_002c4360(void*);

extern "C" void ui_func_00288990(void* ptr) {
    u8* obj = reinterpret_cast<u8*>(ptr);

    for (s32 i = 0; i < 3; ++i) {
        u8* slot = obj + i * 80;
        void** p18 = reinterpret_cast<void**>(slot + 0x18);
        if (*p18 != nullptr) {
            script_vm_func_002a7aa0(*p18);
            *p18 = nullptr;
        }

        void** p1c = reinterpret_cast<void**>(slot + 0x1C);
        if (*p1c != nullptr) {
            engine_func_002c4360(*p1c);
            *p1c = nullptr;
        }
    }

    void** p8 = reinterpret_cast<void**>(obj + 8);
    if (*p8 != nullptr) {
        script_vm_func_002a7aa0(*p8);
        *p8 = nullptr;
    }
}

// DECOMP_FUNC(0x00289fdc, 112)
extern "C" void engine_func_002a4828(void* mgr, void* buf, u32 arg2, void* res_plus8, u32 p5, u32 p6, u32 p7);

extern "C" void script_vm_func_00289fdc(u32 arg0, u32 arg1, u32 arg2) {
    u8 buffer[128];
    for (s32 i = 0; i < 128; ++i) {
        buffer[i] = 0;
    }

    u8* res = reinterpret_cast<u8*>(static_cast<uintptr_t>(engine_func_002a71c0(arg0, 8, arg1, buffer)));
    if (res != nullptr) {
        void* mgr = *reinterpret_cast<void**>(0x00433130);
        engine_func_002a4828(mgr, buffer, arg2, res + 8, 1, 128, 0);
    }
}

// DECOMP_FUNC(0x0028a04c, 112)
extern "C" void script_vm_func_0028a04c(u32 arg0, u32 arg1, u32 arg2) {
    u8 buffer[128];
    for (s32 i = 0; i < 128; ++i) {
        buffer[i] = 0;
    }

    u8* res = reinterpret_cast<u8*>(static_cast<uintptr_t>(engine_func_002a71c0(arg0, 7, arg1, buffer)));
    if (res != nullptr) {
        void* mgr = *reinterpret_cast<void**>(0x00433130);
        engine_func_002a4828(mgr, buffer, arg2, res + 8, 1, 128, 0);
    }
}

// DECOMP_FUNC(0x0028c194, 112)
extern "C" void script_vm_func_002aeb2c(u32 id, u32 sub = 0);
extern "C" void engine_func_002a6410(void*, u32, s32);

extern "C" void script_vm_func_0028c194(void) {
    u8* r4 = *reinterpret_cast<u8**>(0x00434210);
    if (r4 == nullptr) {
        return;
    }

    s32 id = *reinterpret_cast<s32*>(r4 + 0x2F8);
    if (id >= 0) {
        script_vm_func_002aeb2c(0x18);
        u8* r0 = *reinterpret_cast<u8**>(0x00434210);
        if (r0 != nullptr) {
            r0[0x2F4] = 0;
        }
        void* mgr2 = *reinterpret_cast<void**>(0x00433158);
        engine_func_002a6410(mgr2, 0x18, *reinterpret_cast<s32*>(r4 + 0x2F8));
        *reinterpret_cast<s32*>(r4 + 0x2F8) = -1;
    }

    *reinterpret_cast<s32*>(r4 + 0x2E8) = 3;
    *reinterpret_cast<s32*>(r4 + 0x2EC) = 0;
}

// DECOMP_FUNC(0x0028ebd8, 108)
extern "C" void* script_vm_func_002b931c(void* mgr, u32 id);

extern "C" void* camp_func_0028ebd8(u32 id, u32 flag) {
    void* mgr = *reinterpret_cast<void**>(0x00433158);
    u8* custom = reinterpret_cast<u8*>(script_vm_func_002b931c(mgr, id));
    if (custom != nullptr) {
        return custom + 2;
    }

    void* table = Tbb_GetGlobalSubTable(1, 0);
    u8* payload = reinterpret_cast<u8*>(Tbb_GetPayloadData(table));
    u32 row_count = Tbb_GetRowCount(table);

    if (row_count <= id) {
        return payload;
    }

    u8* entry = payload + id * 40;
    if (flag != 0) {
        entry += 0x10;
    }
    return entry;
}

// DECOMP_FUNC(0x0029117c, 112)
extern "C" void script_vm_func_0029117c(u32 val) {
    if (engine_func_002c583c(1) != 0) {
        return;
    }

    u32 mode = *reinterpret_cast<u32*>(0x0044E09C);
    u8* slot = nullptr;
    if (mode == 0) {
        slot = reinterpret_cast<u8*>(0x004C53C4);
    } else if (mode == 1) {
        slot = reinterpret_cast<u8*>(0x004C53E4);
    } else {
        return;
    }

    u32 flags = *reinterpret_cast<u32*>(slot + 0x1C);
    if ((flags & 2) == 0 || (flags & 0x3C) != 0) {
        return;
    }

    if ((flags & 0x40) != 0) {
        flags |= 0x200;
    } else {
        flags |= 0x10;
    }

    *reinterpret_cast<u32*>(slot + 8) = val;
    *reinterpret_cast<u32*>(slot + 0x1C) = flags;
}

// DECOMP_FUNC(0x00291c3c, 112)
extern "C" void script_vm_func_00291c3c(void) {
    u32 count = *reinterpret_cast<u32*>(0x0044CF60);
    count--;
    *reinterpret_cast<u32*>(0x0044CF60) = count;

    if (count == 0) {
        u32 mode = *reinterpret_cast<u32*>(0x0044CF64);
        if (mode == 0x65) {
            script_vm_func_002aeb2c(0x1C, 6);
        } else if (mode == 0x66) {
            script_vm_func_002aeb2c(0x1C, 7);
        } else if (mode == 0x67) {
            script_vm_func_002aeb2c(0x1C, 8);
        }
        *reinterpret_cast<u32*>(0x0044CF64) = 0;
    }
}

// DECOMP_FUNC(0x0029350c, 112)
extern "C" void camp_func_002bdac0(void*, u32, u32);
extern "C" void script_vm_func_00293a30(void*, u32);

extern "C" void script_vm_func_0029350c(void) {
    u8* r4 = *reinterpret_cast<u8**>(0x0043DCF0);
    u32 val = *reinterpret_cast<u32*>(r4 + 0x2C) ^ 1;
    *reinterpret_cast<u32*>(r4 + 0x2C) = val;

    camp_func_002bdac0(r4 + 0x180, 4, 0);

    for (s32 i = 0; i < 4; ++i) {
        void* elem = *reinterpret_cast<void**>(r4 + 0x6C8 + i * 4);
        script_vm_func_00293a30(elem, val);
    }

    for (s32 i = 0; i < 24; ++i) {
        void* elem = *reinterpret_cast<void**>(r4 + 0x6D8 + i * 4);
        script_vm_func_00293a30(elem, val);
    }
}

// DECOMP_FUNC(0x0029357c, 112)
extern "C" void script_vm_func_0029357c(void) {
    u8* r4 = *reinterpret_cast<u8**>(0x0043DCF0);
    u32 val = *reinterpret_cast<u32*>(r4 + 0x2C) ^ 1;
    *reinterpret_cast<u32*>(r4 + 0x2C) = val;

    camp_func_002bdac0(r4 + 0x180, 5, 0);

    for (s32 i = 0; i < 4; ++i) {
        void* elem = *reinterpret_cast<void**>(r4 + 0x6C8 + i * 4);
        script_vm_func_00293a30(elem, val);
    }

    for (s32 i = 0; i < 24; ++i) {
        void* elem = *reinterpret_cast<void**>(r4 + 0x6D8 + i * 4);
        script_vm_func_00293a30(elem, val);
    }
}

// DECOMP_FUNC(0x00293c2c, 108)
extern "C" u8* camp_func_0026f25c(u32 idx);

extern "C" u32 camp_func_00293c2c(u8* obj) {
    u32 flags = *reinterpret_cast<u32*>(obj + 0x44A8);
    if ((flags & 0x40) != 0) {
        return 1;
    }

    u32 type = *reinterpret_cast<u32*>(obj + 0x2F34);
    if (type - 1 <= 3) {
        return 1;
    }

    s32 alive_count = 0;
    for (u32 i = 0; i < 12; ++i) {
        u8* slot = camp_func_0026f25c(i);
        u16 hp = *reinterpret_cast<u16*>(slot + 0x48);
        if (hp != 0) {
            alive_count++;
        }
    }

    return (alive_count >= 1) ? 1 : 0;
}

// DECOMP_FUNC(0x002940ac, 112)
extern "C" void engine_func_0025c0f0(void* node, u32 p1, float x, float y, float z);

extern "C" void ui_func_002940ac(void* ptr, float x, float y, float z) {
    u8* obj = reinterpret_cast<u8*>(ptr);
    u8* head = *reinterpret_cast<u8**>(obj + 8);
    void* head_node = *reinterpret_cast<void**>(head + 8);
    engine_func_0025c0f0(head_node, 0, x, y, z);

    for (s32 i = 0; i < 3; ++i) {
        u8* slot = obj + i * 80;
        u8* sub = *reinterpret_cast<u8**>(slot + 0x18);
        if (sub != nullptr) {
            void* sub_node = *reinterpret_cast<void**>(sub + 8);
            engine_func_0025c0f0(sub_node, 0, x, y, z);
        }
    }
}

// DECOMP_FUNC(0x00296154, 120)
extern "C" u8* camp_func_002bf6d0(u32 arg1, u32 arg2);

extern "C" void script_vm_func_00296154(void* dst_ptr, u32 arg1, u32 arg2) {
    u8* dst = reinterpret_cast<u8*>(dst_ptr);
    u8* node = camp_func_002bf6d0(arg1, arg2);

    u8* p = *reinterpret_cast<u8**>(node + 0xC);
    if (p != nullptr) {
        s16 x0 = *reinterpret_cast<u16*>(node + 8);
        s16 y0 = *reinterpret_cast<u16*>(node + 0xA);
        s16 dx = *reinterpret_cast<s16*>(p);
        s16 dy = *reinterpret_cast<s16*>(p + 2);
        *reinterpret_cast<u16*>(dst + 0x18) = static_cast<u16>(x0 + (dx / 2));
        *reinterpret_cast<u16*>(dst + 0x1A) = static_cast<u16>(y0 + (dy / 2));
    } else {
        u16 w = *reinterpret_cast<u16*>(node + 4) & 0x7FFF;
        u16 h = *reinterpret_cast<u16*>(node + 6) & 0x7FFF;
        u16 x0 = *reinterpret_cast<u16*>(node + 8);
        u16 y0 = *reinterpret_cast<u16*>(node + 0xA);
        *reinterpret_cast<u16*>(dst + 0x18) = static_cast<u16>(x0 + (w >> 1));
        *reinterpret_cast<u16*>(dst + 0x1A) = static_cast<u16>(y0 + (h >> 1));
    }
}

// DECOMP_FUNC(0x00298a74, 112)
extern "C" u8* script_vm_func_002b66ec(void);
extern "C" s32 battle_func_0029ac70(u32, u32);
extern "C" u8* camp_func_002a89e4(s32);
extern "C" s32 battle_func_0029abc0(u32);

extern "C" u32 camp_func_00298a74(s32 arg0, u32 arg1) {
    battle_func_002ae3f0(arg1);

    if (arg0 < 0) {
        u8* ptr = script_vm_func_002b66ec();
        s32 limit = battle_func_0029ac70(arg1, 1);
        s16 current = *reinterpret_cast<s16*>(ptr + 0x2C);
        return (limit <= current) ? 1 : 0;
    } else {
        u8* ptr = camp_func_002a89e4(arg0);
        s32 limit = battle_func_0029abc0(arg1);
        s16 current = *reinterpret_cast<s16*>(ptr + 0x2C);
        return (current >= limit) ? 1 : 0;
    }
}

// DECOMP_FUNC(0x00299874, 100)
extern "C" u32 script_vm_func_00247344(void);
extern "C" u8* engine_func_002b47cc(u32 id);

extern "C" u32 engine_func_00299874(u32 id) {
    u32 state = script_vm_func_00247344();
    u8* obj = engine_func_002b47cc(id);
    if (obj == nullptr) {
        return 0;
    }

    u8 flags = obj[0x60];
    if ((flags & 1) != 0 && state == 4) {
        return 1;
    }
    if ((flags & 4) != 0 && state == 5) {
        return 1;
    }
    if ((flags & 2) != 0 && state == 1) {
        return 1;
    }

    return 0;
}

// DECOMP_FUNC(0x0029c084, 120)
extern "C" void camp_func_0029c084(const void* src) {
    const u32 ip = *reinterpret_cast<const u32*>(0x0043E2ACu);
    for (u32 i = 0; i < 8; ++i) {
        const s16 id = *reinterpret_cast<const s16*>(static_cast<const char*>(src) + 0x34 + i * 2);
        if (id > 0 && id <= 500) {
            const u32 byte_idx = static_cast<u32>(id) >> 3;
            const u32 bit_idx = static_cast<u32>(id) & 7u;
            *reinterpret_cast<u8*>(ip + 0x24BC4u + byte_idx) |= static_cast<u8>(1u << bit_idx);
        }
    }
}

extern "C" void* engine_func_002c54f0(u32 a, u32 b, u32 c, u32 size, u32 e);
extern "C" void* AsdModel_func_001fe470();

// DECOMP_FUNC(0x002a135c, 116)
extern "C" void* AsdMdlManager_func_002a135c() {
    u32* node = static_cast<u32*>(engine_func_002c54f0(0x100, 0x100, 0, 0x1C, 1));
    for (u32 i = 0; i < 7; ++i) {
        node[i] = 0;
    }
    void* sub_ptr = AsdModel_func_001fe470();
    node[2] = reinterpret_cast<uintptr_t>(sub_ptr);
    node[0] |= 0x00200000u;
    return node;
}

extern "C" void engine_func_002a8898(void* arbiter, void* addr, s32 op, s32 count, s64 timeout);

// DECOMP_FUNC(0x002a4588, 120)
extern "C" s32 func_002a4588(void* synch_obj, s32 delta) {
    const s16 max_cap = *reinterpret_cast<const s16*>(static_cast<const char*>(synch_obj) + 6);
    s32* const target = static_cast<s32*>(synch_obj);
    s32 old_val;
    s32 new_val;
    do {
        old_val = __atomic_load_n(target, __ATOMIC_RELAXED);
        if (static_cast<s32>(max_cap) - delta < old_val) {
            new_val = static_cast<s32>(max_cap);
        } else {
            new_val = old_val + delta;
        }
    } while (!__atomic_compare_exchange_n(target, &old_val, new_val, false, __ATOMIC_RELAXED, __ATOMIC_RELAXED));

    if (old_val <= 0 || *reinterpret_cast<const s16*>(static_cast<const char*>(synch_obj) + 4) > 0) {
        void* arbiter = *reinterpret_cast<void**>(0x00471B58u);
        engine_func_002a8898(arbiter, synch_obj, 0, delta, 0LL);
    }
    return old_val;
}

// DECOMP_FUNC(0x002a7fd8, 100)
extern "C" s32 func_002a7fd8(float a, float b) {
    const float eps = 1.1920929e-7f;
    float diff = a - b;
    if (diff < 0.0f) {
        diff = -diff;
    }
    float abs_a = a < 0.0f ? -a : a;
    if (abs_a * eps >= diff) {
        return 1;
    }
    float abs_b = b < 0.0f ? -b : b;
    if (abs_b * eps >= diff) {
        return 1;
    }
    return 0;
}

extern "C" s32 func_002bb5b4();

// DECOMP_FUNC(0x002a8674, 112)
extern "C" void func_002a8674(u32 id, u32 mode, float val) {
    if (!func_002bb5b4()) {
        return;
    }

    const u16 offset_val = *reinterpret_cast<const u16*>(0x0000131Eu + id);
    const u32 entry = id + (static_cast<u32>(offset_val) << 2) + 0x1000u;
    u8* const target = *reinterpret_cast<u8**>(entry + 0x00A0u);

    *reinterpret_cast<float*>(target + 8u + mode * 4u) = val;
    if (mode == 0) {
        *reinterpret_cast<u32*>(target) |= 0x01000000u;
    } else if (mode == 1) {
        *reinterpret_cast<u32*>(target) |= 0x02000000u;
    }
}

// DECOMP_FUNC(0x002a8cfc, 108)
extern "C" void func_0014e804(void* obj);
extern "C" void func_002bfff8(void* matrix, void* src);
extern "C" void script_vm_func_002b71f8(void* obj);
extern "C" u32 engine_func_002b9438(void* src, void* obj);

extern "C" u32 func_002a8cfc(void* dest) {
    u8 temp_obj[0x40];
    float matrix_buf[16];
    u8 local_fallback[0x44];

    void* target = dest ? dest : local_fallback;

    func_0014e804(temp_obj);
    void* global_obj = *reinterpret_cast<void**>(0x0044EA00u);
    func_002bfff8(matrix_buf, global_obj);

    float* dst_f = static_cast<float*>(target);
    for (u32 i = 0; i < 16; ++i) {
        dst_f[i] = matrix_buf[i];
    }

    script_vm_func_002b71f8(temp_obj);
    return engine_func_002b9438(global_obj, temp_obj);
}

extern "C" void func_0014e760(u32 a, u32 b, u32 c, u32 d);
extern "C" void ui_func_001456d0(u32 mode);

// DECOMP_FUNC(0x002aa48c, 120)
extern "C" void func_002aa48c(u32 id, void* node, u8 mode) {
    const u8 flag = *reinterpret_cast<const u8*>(0x000011E8u + id);
    u8* const base = reinterpret_cast<u8*>(id + 0x1000u);
    void** const slot = reinterpret_cast<void**>(base + 0x1E4u);

    if (flag != 0 || *slot != node) {
        *slot = node;
        if (node != nullptr) {
            const u8* const np = static_cast<const u8*>(node);
            const u32 a0 = *reinterpret_cast<const u32*>(np + 0x14);
            const u32 a1 = *reinterpret_cast<const u32*>(np + 0x18);
            const u32 a2 = *reinterpret_cast<const u32*>(np + 0x34);
            const u32 a3 = *reinterpret_cast<const u32*>(np + 0x30);
            func_0014e760(a0, a1, a2, a3);
            base[0x1E9] = 3;
        }
    }

    base[0x1E8] = 0;
    const u8 cur_mode = base[0x1E9];
    if (cur_mode != mode) {
        ui_func_001456d0(mode);
        base[0x1E9] = mode;
    }
}

extern "C" s32 script_vm_func_002a8730(s32 year, s32 month, s32 day);

// DECOMP_FUNC(0x002ad714, 112)
extern "C" void func_002ad714(s64* out_ms, s32 year, s32 month, s32 day, s32 hour, s32 minute, s32 second, s32 millisecond) {
    const s32 days = script_vm_func_002a8730(year, month, day);
    const s64 total_ms = static_cast<s64>(days) * 86400000LL
                       + static_cast<s64>(hour) * 3600000LL
                       + static_cast<s64>(minute) * 60000LL
                       + static_cast<s64>(second) * 1000LL
                       + static_cast<s64>(millisecond);
    *out_ms = total_ms;
}

extern "C" void engine_func_0014e648(void* list, void* node, s32 index);

// DECOMP_FUNC(0x002b2814, 120)
extern "C" void* AsdList_func_002b2814(void* list, void* item, u32 extra) {
    u32* const node = static_cast<u32*>(engine_func_002c54f0(0x100, 0x100, 0, 0x1C, 1));
    node[0] = 0;
    node[1] = 0;
    node[2] = reinterpret_cast<uintptr_t>(item);
    node[3] = 0;
    node[4] = extra;
    node[5] = 0;
    node[6] = 0;
    engine_func_0014e648(list, node, -1);
    return node;
}

extern "C" void func_002bd620(void* elem);
extern "C" void* engine_func_002bb270();
extern "C" void func_0015c6bc(void* mgr, void* obj);

// DECOMP_FUNC(0x002b4ddc, 104)
extern "C" void func_002b4ddc(void* obj) {
    u8* const base = static_cast<u8*>(obj);
    if (base[0x14] == 0) {
        return;
    }

    s32 i = 0;
    while (*reinterpret_cast<const s32*>(base + 8) > i) {
        void** const slot = reinterpret_cast<void**>(base + i * 4);
        if (*slot != nullptr) {
            func_002bd620(*slot);
            *slot = nullptr;
        }
        ++i;
    }

    *reinterpret_cast<s32*>(base + 8) = 0;
    void* mgr = engine_func_002bb270();
    func_0015c6bc(mgr, obj);
    base[0x14] = 0;
}

extern "C" u32 ui_func_002b2530(void* handle);
extern "C" void script_vm_func_002b01a0(void* sub);
extern "C" void engine_func_002c4360(void* obj);

// DECOMP_FUNC(0x002b8adc, 104)
extern "C" u32 ui_func_002b8adc() {
    void** const holder = reinterpret_cast<void**>(0x00447060u);
    u8* const inst = static_cast<u8*>(*holder);
    if (inst == nullptr) {
        return 0;
    }

    if (ui_func_002b2530(*reinterpret_cast<void**>(inst)) != 0) {
        return 1;
    }

    if (inst[8] == 0) {
        return 1;
    }

    if (*holder != nullptr) {
        script_vm_func_002b01a0(static_cast<u8*>(*holder) + 0xEC);
        engine_func_002c4360(*holder);
        *holder = nullptr;
    }
    return 0;
}

static inline u32 h2_mode0_query_remainder(u32 dividend, u32 divisor) {
    u32 remainder;
    asm volatile(
        "mov r0, %1\n"
        "mov r1, %2\n"
        "ldr r12, 1f\n"
        "blx r12\n"
        "b 2f\n"
        ".balign 4\n"
        "1: .word 0x002c6c10\n"
        "2:\n"
        "mov %0, r1\n"
        : "=r"(remainder)
        : "r"(dividend), "r"(divisor)
        : "r0", "r1", "r2", "r3", "r12", "lr", "cc", "memory");
    return remainder;
}

// DECOMP_FUNC(0x002b902c, 104)
extern "C" s32 ui_func_002b902c(u32 id) {
    if (id >= 0x1fu) {
        return 0;
    }

    const u32 input_flags = *reinterpret_cast<const u32*>(0x004650A8u);
    u32 counter = 0;
    if ((input_flags & 1u) == 0) {
        counter = *reinterpret_cast<const u32*>(0x004E3C58u + id * 4u);
        if (counter == 1u) {
            return 1;
        }
    }

    const u32 threshold = *reinterpret_cast<const u32*>(0x004650ACu);
    if (counter <= threshold) {
        return 0;
    }

    const u32 selector = *reinterpret_cast<const u32*>(0x004650B0u);
    return h2_mode0_query_remainder(counter - threshold, selector) == 0 ? 1 : 0;
}

extern "C" void ui_func_002ae2c4(const float* rgba);

// DECOMP_FUNC(0x002be4dc, 108)
extern "C" void func_002be4dc(u32 hex_color) {
    const float inv_255 = 1.0f / 255.0f;
    const float r = static_cast<float>((hex_color >> 24) & 0xFFu) * inv_255;
    const float g = static_cast<float>((hex_color >> 16) & 0xFFu) * inv_255;
    const float b = static_cast<float>((hex_color >> 8) & 0xFFu) * inv_255;
    const float rgba[4] = { r, g, b, 1.0f };
    ui_func_002ae2c4(rgba);
}

extern "C" void engine_func_002c3aa8(void* mutex);
extern "C" void engine_func_002c3a24(void* mutex);
extern "C" u32 camp_func_0011cd48(void* config);

// DECOMP_FUNC(0x002c1570, 104)
extern "C" u32 nn_sdk_func_002c1570() {
    void* const mutex = reinterpret_cast<void*>(0x004E9BA8u);
    engine_func_002c3aa8(mutex);

    s32* const counter = reinterpret_cast<s32*>(0x00471B90u);
    u32 result;
    if (*counter > 0) {
        *counter += 1;
        result = 0x082067F9u;
    } else {
        result = camp_func_0011cd48(reinterpret_cast<void*>(0x0040B6E4u));
    }

    engine_func_002c3a24(mutex);
    return result;
}

extern "C" s32 script_vm_func_002c0ba8(u32 flag_id);

// DECOMP_FUNC(0x002c8630, 104)
extern "C" s32 script_vm_func_002c8630(u32 id) {
    engine_func_002c2b1c();

    asm("" : "+r"(id));
    if ((id - 0x19u) <= 5u || id == 0x66u) {
        if (script_vm_func_002c0ba8(0x144u) == 0) {
            return 0;
        }
    }

    asm("" : "+r"(id));
    if ((id - 0x1Fu) <= 4u || id == 0x67u) {
        if (script_vm_func_002c0ba8(0x15Au) == 0) {
            return 0;
        }
    }

    return 1;
}

extern "C" void* Tbb_GetGlobalSubTable(u32 table_id, u32 subtable_id);
extern "C" void* Tbb_GetPayloadData(void* table);
extern "C" u32 Tbb_GetRowCount(void* table);

// DECOMP_FUNC(0x002c9b3c, 104)
extern "C" void* script_vm_func_002c9b3c(u32 id) {
    void* table = Tbb_GetGlobalSubTable(0x23u, 3u);
    void* static_base = Tbb_GetPayloadData(table);
    const u32 static_count = Tbb_GetRowCount(table);

    if (id < static_count) {
        return static_cast<char*>(static_base) + id * 20u;
    }

    const u8* const dyn_mgr = *reinterpret_cast<const u8* const*>(0x00433158u);
    const u32 dyn_count = *reinterpret_cast<const u32*>(dyn_mgr + 0x3FCu);
    void* const dyn_base = *reinterpret_cast<void* const*>(dyn_mgr + 0x400u);

    if (id < static_count + dyn_count) {
        const u32 dyn_idx = id - static_count;
        return static_cast<char*>(dyn_base) + dyn_idx * 20u;
    }

    return nullptr;
}

// DECOMP_FUNC(0x002cd754, 116)
extern "C" __attribute__((naked)) void ui_func_002cd754() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebff194e\n.inst 0xe2800a02\n.inst 0xe5900234\n.inst 0xe8bd4010\n.inst 0xe1a00000\n.inst 0xe92d4030\n.inst 0xe1a04000\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xebff25f7\n.inst 0xe1a05000\n.inst 0xebfeefad\n.inst 0xe59f1034\n.inst 0xe1a02000\n.inst 0xe1a00004\n.inst 0xe5911004\n.inst 0xe3510000\n.inst 0x13a03014\n.inst 0x15c13a11\n.inst 0xe3a01000\n.inst 0xe58d1000\n.inst 0xe58d1004\n.inst 0xe3a0300b\n.inst 0xe1a01005\n.inst 0xebfee45a\n.inst 0xe28dd00c\n.inst 0xe8bd8030\n.word 0x0043e188\n");
}

// DECOMP_FUNC(0x002cd880, 104)
extern "C" __attribute__((naked)) void engine_func_002cd880() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfeef6d\n.inst 0xe3500000\n.inst 0x0a000007\n.inst 0xe59f0048\n.inst 0xe5900000\n.inst 0xe5901010\n.inst 0xe5900014\n.inst 0xe1510000\n.inst 0x03a00001\n.inst 0x13a00000\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xebff25a9\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xebff25a6\n.inst 0xe1a01000\n.inst 0xed9f0a05\n.inst 0xe3a02001\n.inst 0xe1a00004\n.inst 0xebfe2f20\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x0043e088\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002cde1c, 96)
extern "C" __attribute__((naked)) void camp_func_002cde1c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe3a01000\n.inst 0xe3a00025\n.inst 0xebffcc24\n.inst 0xe1a06000\n.inst 0xebffcc18\n.inst 0xe1a04000\n.inst 0xe1a00006\n.inst 0xebffcc01\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0x9a000008\n.inst 0xe1d420d0\n.inst 0xe1520005\n.inst 0x1a000001\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.inst 0xe2800001\n.inst 0xe1510000\n.inst 0xe2844020\n.inst 0x8afffff6\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002d14d8, 120)
extern "C" __attribute__((naked)) void engine_func_002d14d8() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a08000\n.inst 0xe590009c\n.inst 0xebfe602c\n.inst 0xe598009c\n.inst 0xe5907008\n.inst 0xe3570000\n.inst 0x15901010\n.inst 0x13510000\n.inst 0x0a000012\n.inst 0xe1d810bc\n.inst 0xe5904018\n.inst 0xe59860a0\n.inst 0xe3510003\n.inst 0x1a00000d\n.inst 0xe3570000\n.inst 0xe3a05000\n.inst 0xda00000a\n.inst 0xe5940010\n.inst 0xe3500000\n.inst 0x1a000002\n.inst 0xe1a01006\n.inst 0xe1a00008\n.inst 0xeb00c3d6\n.inst 0xe2855001\n.inst 0xe1550007\n.inst 0xe2844028\n.inst 0xe286601c\n.inst 0xbafffff4\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002db9d0, 112)
extern "C" __attribute__((naked)) void engine_func_002db9d0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfeed60\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfeed5d\n.inst 0xe2504000\n.inst 0xaa000003\n.inst 0xe2641000\n.inst 0xe1a00005\n.inst 0xebfdd571\n.inst 0xea000002\n.inst 0xe1a01000\n.inst 0xe1a00005\n.inst 0xebfee8ab\n.inst 0xe320f000\n.inst 0xebffc84e\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe59f0014\n.inst 0xebff75e6\n.inst 0xe1a00004\n.inst 0xe320f000\n.inst 0xebfcd76c\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x01000174\n");
}

// DECOMP_FUNC(0x002dbad4, 120)
extern "C" __attribute__((naked)) void battle_func_002dbad4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfeed1f\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfee069\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000007\n.inst 0xe3110040\n.inst 0x01d00cbe\n.inst 0x01500005\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfec90a\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffea\n.inst 0xe3a00000\n.inst 0xebfec903\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002dca98, 96)
extern "C" __attribute__((naked)) void func_002dca98() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04001\n.inst 0xe1d010b2\n.inst 0xe3510000\n.inst 0xe1d410b2\n.inst 0x0a000009\n.inst 0xe3510000\n.inst 0x03e00000\n.inst 0x0a000005\n.inst 0xe1d000b0\n.inst 0xebfeae2e\n.inst 0xe1a05000\n.inst 0xe1d400b0\n.inst 0xebfeae2b\n.inst 0xe0400005\n.inst 0xe8bd8070\n.inst 0xe3510000\n.inst 0x03a00000\n.inst 0x13a00001\n.inst 0xe8bd8070\n.inst 0xe5d00000\n.inst 0xe5d11000\n.inst 0xe0400001\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002e0c54, 108)
extern "C" __attribute__((naked)) void ui_func_002e0c54() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xebff7fcd\n.inst 0xe3500000\n.inst 0x0a000013\n.inst 0xe59f104c\n.inst 0xe59f204c\n.inst 0xe5d15000\n.inst 0xe182c342\n.inst 0xe1e0300c\n.inst 0xe7c25000\n.inst 0xe5d15001\n.inst 0xe08cc000\n.inst 0xe0404003\n.inst 0xe5cc5000\n.inst 0xe5d1c002\n.inst 0xe04368c2\n.inst 0xe0402006\n.inst 0xe5c4c000\n.inst 0xe5d11003\n.inst 0xe2800909\n.inst 0xe2800d2e\n.inst 0xe3a03001\n.inst 0xe5c21000\n.inst 0xe5c03000\n.inst 0xe8bd8070\n.word 0x0044e0f8\n.word 0x00024b7c\n");
}

// DECOMP_FUNC(0x002e3304, 124)
extern "C" __attribute__((naked)) void camp_func_002e3304() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a06000\n.inst 0xeb010390\n.inst 0xe2505000\n.inst 0xe3a04000\n.inst 0x9a000013\n.inst 0xe6ff0074\n.inst 0xebfd951a\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000f\n.inst 0xe1d000b0\n.inst 0xe1500006\n.inst 0x1a00000c\n.inst 0xebfef71a\n.inst 0xe1a01fc4\n.inst 0xe3a03001\n.inst 0xe0841ea1\n.inst 0xe08021c1\n.inst 0xe3c11007\n.inst 0xe0441001\n.inst 0xe5f20035\n.inst 0xe1a01113\n.inst 0xe1100001\n.inst 0x01800001\n.inst 0x05c20000\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe1540005\n.inst 0x3affffe7\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002e3bb0, 120)
extern "C" __attribute__((naked)) void battle_func_002e3bb0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfec035\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000006\n.inst 0xe3110040\n.inst 0x1a000004\n.inst 0xe1d00cbe\n.inst 0xebff55dc\n.inst 0xe5d00005\n.inst 0xe3500004\n.inst 0x0a000006\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffeb\n.inst 0xe3a00000\n.inst 0xebfea8d0\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xebfea8cc\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002ed404, 120)
extern "C" __attribute__((naked)) void camp_func_002ed404() {
    asm volatile(".arm\n.inst 0xe59f2068\n.inst 0xe92d4038\n.inst 0xe3a01001\n.inst 0xe5924008\n.inst 0xe5c4107e\n.inst 0xe5c4107c\n.inst 0xe5840068\n.inst 0xebfe8a6f\n.inst 0xe584006c\n.inst 0xe5840078\n.inst 0xe3a0100b\n.inst 0xe2840b01\n.inst 0xe28430a4\n.inst 0xe2800fd5\n.inst 0xe58d1000\n.inst 0xed9f0a0c\n.inst 0xe3e02000\n.inst 0xe3a0100e\n.inst 0xe1a04000\n.inst 0xebff41b5\n.inst 0xe3a0100a\n.inst 0xe1a00004\n.inst 0xebff2f1f\n.inst 0xe3a01006\n.inst 0xe1a00004\n.inst 0xebff46f0\n.inst 0xe3a00001\n.inst 0xe8bd8038\n.word 0x0043e188\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002f067c, 112)
extern "C" __attribute__((naked)) void engine_func_002f067c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9a35\n.inst 0xe3500000\n.inst 0xe3a04000\n.inst 0x03a04007\n.inst 0x0a000004\n.inst 0xe3500001\n.inst 0x03a0400a\n.inst 0x0a000001\n.inst 0xe3500002\n.inst 0x03a0400b\n.inst 0xe3a00001\n.inst 0xebfe9a2a\n.inst 0xe1a05000\n.inst 0xe59f0028\n.inst 0xe5900000\n.inst 0xebfe3934\n.inst 0xe5900020\n.inst 0xe0800084\n.inst 0xe1d007f2\n.inst 0xe1500005\n.inst 0x03a00001\n.inst 0x13a00000\n.inst 0xebfe761c\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0043427c\n");
}

// DECOMP_FUNC(0x002f3b78, 104)
extern "C" __attribute__((naked)) void script_vm_func_002f3b78() {
    asm volatile(".arm\n.inst 0xe59f005c\n.inst 0xe3a01000\n.inst 0xe3a0c006\n.inst 0xe5903000\n.inst 0xe3a00065\n.inst 0xe0000091\n.inst 0xe0830100\n.inst 0xe5f021d0\n.inst 0xe3520000\n.inst 0x0a00000a\n.inst 0xe5902014\n.inst 0xe352001d\n.inst 0x13520026\n.inst 0x0a000003\n.inst 0xe352001e\n.inst 0x1352001f\n.inst 0x13520025\n.inst 0x1a000002\n.inst 0xe5902004\n.inst 0xe3520008\n.inst 0x0580c004\n.inst 0xe2811001\n.inst 0xe3510080\n.inst 0xbaffffeb\n.inst 0xe12fff1e\n.word 0x00447a78\n");
}

// DECOMP_FUNC(0x002f4a2c, 120)
extern "C" __attribute__((naked)) void engine_func_002f4a2c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfe5302\n.inst 0xe3500000\n.inst 0x0a000006\n.inst 0xebff3539\n.inst 0xe3500000\n.inst 0xe3a00000\n.inst 0x0a00000e\n.inst 0xebfe4bcf\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebff3531\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x1a00000b\n.inst 0xe3a00000\n.inst 0xebfe893a\n.inst 0xe1a01000\n.inst 0xe3a00000\n.inst 0xebfeaefd\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebff1094\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0affffed\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f5dc0, 96)
extern "C" __attribute__((naked)) void engine_func_002f5dc0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe59f6050\n.inst 0xe5965000\n.inst 0xe5950138\n.inst 0xeb00973a\n.inst 0xe3a04000\n.inst 0xe0850104\n.inst 0xe590012c\n.inst 0xeb00501d\n.inst 0xe2844001\n.inst 0xe3540003\n.inst 0xbafffff9\n.inst 0xe5950160\n.inst 0xebff3959\n.inst 0xe5950000\n.inst 0xe3a01000\n.inst 0xebff39ec\n.inst 0xe1a00005\n.inst 0xe320f000\n.inst 0xebff3953\n.inst 0xe3a00000\n.inst 0xe5860000\n.inst 0xe8bd8070\n.word 0x0043db10\n");
}

// DECOMP_FUNC(0x002f6d84, 120)
extern "C" __attribute__((naked)) void battle_func_002f6d84() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe73c0\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000006\n.inst 0xe3110040\n.inst 0x1a000004\n.inst 0xe1d00cbe\n.inst 0xebff0967\n.inst 0xe5d00005\n.inst 0xe3500005\n.inst 0x0a000006\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffeb\n.inst 0xe3a00000\n.inst 0xebfe5c5b\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xebfe5c57\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f6dfc, 116)
extern "C" __attribute__((naked)) void battle_func_002f6dfc() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe73a2\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000009\n.inst 0xe3110040\n.inst 0x1a000007\n.inst 0xebfd40cd\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe5c41\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe8\n.inst 0xe3a00000\n.inst 0xebfe5c3a\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f701c, 96)
extern "C" __attribute__((naked)) void ui_func_002f701c() {
    asm volatile(".arm\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfe7fcd\n.inst 0xe1a04000\n.inst 0xebfe7319\n.inst 0xebfd4ab5\n.inst 0xe3500000\n.inst 0x0a00000b\n.inst 0xe28000cc\n.inst 0xe1d02eb8\n.inst 0xe1d01efa\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebff3c41\n.inst 0xe1500004\n.inst 0xca000003\n.inst 0xe3a00001\n.inst 0xebfe5bbb\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xebfe5bb7\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f7108, 96)
extern "C" __attribute__((naked)) void battle_func_002f7108() {
    asm volatile(".arm\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfe7f92\n.inst 0xe1a04000\n.inst 0xe59f0044\n.inst 0xe5900000\n.inst 0xebfe1e9c\n.inst 0xe5901028\n.inst 0xe0810084\n.inst 0xe2800c01\n.inst 0xe1d002b6\n.inst 0xe3100b3f\n.inst 0x13a01002\n.inst 0x11510520\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfe5b81\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe3a00000\n.inst 0xebfe5b7d\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x0043427c\n");
}

// DECOMP_FUNC(0x002fb54c, 124)
extern "C" __attribute__((naked)) void engine_func_002fb54c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfe383a\n.inst 0xe3500000\n.inst 0x0a000006\n.inst 0xebff1a71\n.inst 0xe3500000\n.inst 0xe3a00000\n.inst 0x0a00000f\n.inst 0xebfe3107\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebff1a69\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x1a00000c\n.inst 0xe3a00000\n.inst 0xebfe6e72\n.inst 0xe1a01000\n.inst 0xe3e02000\n.inst 0xe3a00000\n.inst 0xebfe842e\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe320f000\n.inst 0xebfef5cb\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0affffec\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002fc9d4, 112)
extern "C" __attribute__((naked)) void camp_func_002fc9d4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a06001\n.inst 0xe59f405c\n.inst 0xe2845063\n.inst 0xe1a00004\n.inst 0xebfe48a2\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000c\n.inst 0xe1a00004\n.inst 0xebfe4cf8\n.inst 0xe1a01000\n.inst 0xe1a00004\n.inst 0xebfd516d\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebfe9164\n.inst 0xe08001a4\n.inst 0xe2041007\n.inst 0xe5d02044\n.inst 0xe1821116\n.inst 0xe5c01044\n.inst 0xe2844001\n.inst 0xe1540005\n.inst 0x9affffea\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x0000079f\n");
}

// DECOMP_FUNC(0x002febb4, 112)
extern "C" __attribute__((naked)) void engine_func_002febb4() {
    asm volatile(".arm\n.inst 0xe92d4038\n.inst 0xe3a00000\n.inst 0xe1cd00b0\n.inst 0xe1dd00b2\n.inst 0xe1a00520\n.inst 0xe1a00500\n.inst 0xe1cd00b2\n.inst 0xe3a00000\n.inst 0xebfe60e1\n.inst 0xe1a04000\n.inst 0xebfebe9b\n.inst 0xe3500009\n.inst 0x1a000005\n.inst 0xe59f1030\n.inst 0xe3a03000\n.inst 0xe1a00004\n.inst 0xe1a02001\n.inst 0xeb029df4\n.inst 0xe1a04000\n.inst 0xe1a0000d\n.inst 0xe1cd40b0\n.inst 0xebfd1eb3\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebfe3cce\n.inst 0xe3a00001\n.inst 0xe8bd8038\n.word 0x0000ffff\n");
}

// DECOMP_FUNC(0x002fec44, 124)
extern "C" __attribute__((naked)) void script_vm_func_002fec44() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe59f6064\n.inst 0xe3a00001\n.inst 0xe5964000\n.inst 0xe5c405f2\n.inst 0xe1a00005\n.inst 0xebfe696f\n.inst 0xe59f1050\n.inst 0xe5c405c4\n.inst 0xe18150b4\n.inst 0xebfd4758\n.inst 0xe3a01001\n.inst 0xe1a00005\n.inst 0xebfe450b\n.inst 0xe3a02000\n.inst 0xe1a01002\n.inst 0xe2840034\n.inst 0xebfefb8b\n.inst 0xe5960000\n.inst 0xe3a01001\n.inst 0xe5902004\n.inst 0xe5802008\n.inst 0xe5a01004\n.inst 0xe3a02000\n.inst 0xe580200c\n.inst 0xe3a0001c\n.inst 0xe584000c\n.inst 0xe8bd8070\n.word 0x0043dd50\n.word 0x0000097e\n");
}

// DECOMP_FUNC(0x002fff20, 112)
extern "C" __attribute__((naked)) void battle_func_002fff20() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xebfe4f5b\n.inst 0xe1a04000\n.inst 0xeb00db61\n.inst 0xebfedbca\n.inst 0xe2800c06\n.inst 0xe1d050b6\n.inst 0xebfedbc7\n.inst 0xe2800c06\n.inst 0xe1a01005\n.inst 0xe1d000f4\n.inst 0xebfedb90\n.inst 0xe1d005ba\n.inst 0xe3a01000\n.inst 0xe2800001\n.inst 0xe6bf0070\n.inst 0xebfe5180\n.inst 0xe2841901\n.inst 0xe2811e4a\n.inst 0xe59f0018\n.inst 0xe5912000\n.inst 0xe3822402\n.inst 0xe5812000\n.inst 0xe5900000\n.inst 0xeb02ba2e\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.word 0x00439ca8\n");
}
