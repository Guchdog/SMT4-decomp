#include "types.h"

static __attribute__((always_inline)) inline float inline_vsqrt_f32(float value) {
    float result;
    asm volatile("vsqrt.f32 %0, %1" : "=t"(result) : "t"(value));
    return result;
}

static __attribute__((always_inline)) inline float return_vector_r0(u32 r0_val, float s0_val) {
    register u32 r0 asm("r0") = r0_val;
    asm volatile("" : "+r"(r0));
    return s0_val;
}

// Batch 30 C: redirected to 0x00200000-0x002fffff; exact ARM bytes and bounded literal tails.

// DECOMP_FUNC(0x00207d84, 128)
extern "C" u32 ui_func_002c5218();
extern "C" void ui_func_0026330c(float* output, u32 index, u32 context,
                                  const float* input);

extern "C" __attribute__((minsize)) float ui_func_00207d84() {
    constexpr u32 kVectorAddress = 0x004EA91Cu;
    constexpr u32 kScratchAddress = 0x00472550u;
    auto* const vector = reinterpret_cast<volatile u32*>(kVectorAddress);
    auto* const scratch = reinterpret_cast<volatile u32*>(kScratchAddress);
    const u32 context = ui_func_002c5218();

    for (u32 word = 0; word < 4; ++word) {
        scratch[word] = vector[word];
    }

    alignas(8) u32 frame[8];
    auto* const input_words = reinterpret_cast<volatile u32*>(frame + 4);
    input_words[0] = scratch[0];
    input_words[1] = scratch[1];
    input_words[2] = scratch[2];

    ui_func_0026330c(reinterpret_cast<float*>(frame), 0, context,
                     reinterpret_cast<const float*>(frame + 4));
    frame[3] = 0;
    vector[0] = frame[0];
    vector[1] = frame[1];
    vector[2] = frame[2];
    vector[3] = frame[3];

    return return_vector_r0(kVectorAddress, *reinterpret_cast<float*>(&frame[2]));
}

// DECOMP_FUNC(0x0020e9ac, 152)
extern "C" u32 func_002b2530(void*);
extern "C" void func_002a7b7c(void*);
extern "C" void func_00263e60(void*);
extern "C" void func_002b2520(void*);
extern "C" void engine_func_002c4360(void*);

extern "C" u32 engine_func_0020e9ac(void) {
    u8** slot = reinterpret_cast<u8**>(0x0044CFD0 + 4);
    u8* r4 = *slot;
    if (r4 == nullptr) {
        return 0;
    }

    if (func_002b2530(*reinterpret_cast<void**>(r4)) != 0) {
        return 1;
    }

    if (r4[4] == 0) {
        return 1;
    }

    r4 = *slot;
    if (r4 == nullptr) {
        return 0;
    }

    r4[4] = 1;
    void* child = *reinterpret_cast<void**>(r4 + 8);
    if (child != nullptr) {
        func_002a7b7c(child);
        child = *reinterpret_cast<void**>(r4 + 8);
        if (child != nullptr) {
            func_00263e60(reinterpret_cast<u8*>(child) + 0x110);
            func_002b2520(child);
        }
        *reinterpret_cast<void**>(r4 + 8) = nullptr;
    }

    engine_func_002c4360(*slot);
    *slot = nullptr;
    return 0;
}

// DECOMP_FUNC(0x0020eac4, 148)
extern "C" u32 func_00296f60(u32);
extern "C" u32 func_00289640(void);
extern "C" u32 func_002b8ce4(u32);
extern "C" u32 func_002c1f28(void);
extern "C" void func_002a0678(u32, u32);

extern "C" u32 engine_func_0020eac4(void) {
    u32 r4 = func_00296f60(1);
    if (func_00289640() != 0) {
        if (func_002b8ce4(0) == 0) {
            return 0;
        }
        if (func_002b8ce4(0) == 0) {
            return 0;
        }
        return 1;
    }

    if (func_002c1f28() != 0) {
        return 1;
    }

    u32 v = func_00296f60(0);
    if (v != 0 && v != 1) {
        return 1;
    }

    func_002a0678(0, r4);
    func_002a0678(1, r4);
    return 0;
}

// DECOMP_FUNC(0x002100f8, 144)
extern "C" void ui_func_00263254(void* v_curr, void* v_next, float x0, float y0, float x1, float y1, float f4, float f5);

extern "C" void ui_func_002100f8(float x, float y, float w, float h, float f4, float f5, void* v0, void* v1, void* v2, void* v3) {
    float x2 = x + w;
    float y2 = y + h;

    void* const verts[5] = {v0, v1, v2, v3, v0};
    const float coords[5][2] = {
        {x, y},
        {x, y2},
        {x2, y2},
        {x2, y},
        {x, y}
    };

    for (int i = 0; i < 4; ++i) {
        ui_func_00263254(
            verts[i],
            verts[i + 1],
            coords[i][0],
            coords[i][1],
            coords[i + 1][0],
            coords[i + 1][1],
            f4,
            f5
        );
    }
}

// DECOMP_FUNC(0x002118a0, 148)
extern "C" void func_0028df3c(u32);
extern "C" u32 func_00286880(void);
extern "C" u32 func_0028686c(void);
extern "C" void func_00286928(u32, u32, u32, u32, u32, u32);

extern "C" void engine_func_002118a0(void) {
    func_0028df3c(0);
    if (func_00289640() == 0) {
        u8* obj = *reinterpret_cast<u8**>(0x0043E188 + 8);
        if (obj != nullptr) {
            obj[0x30] = 1;
            obj[0x31] = 1;
        }
    }

    u32 mode = func_00286880();
    if (mode == 0x14) {
        mode = 5;
    }

    u32 a0 = func_0028686c();
    u32 a1 = func_00296f60(0);
    u32 a2 = func_00289640();
    func_00286928(a0, a1, a2, mode, 1, 0);
}

// DECOMP_FUNC(0x00211c50, 148)
extern "C" void* func_0031bdbc(void);
extern "C" u32 func_002bf41c(void);
extern "C" u8* func_002c0ac8(void*);
extern "C" void func_002c45b8(void*, u32);

extern "C" u32 battle_func_00211c50(void) {
    void* obj = func_0031bdbc();
    if (func_002bf41c() == 0) {
        return 1;
    }

    u8* r4 = func_002c0ac8(obj);
    if (*reinterpret_cast<u32*>(r4 + 0x0C) == 1) {
        func_002c45b8(obj, 0);
        return 1;
    }

    if (r4[0x64] == 0) {
        r4[0x30] = 1;
        *reinterpret_cast<float*>(r4 + 0x28) = -0.25f;
        return 1;
    }

    if (func_00289640() == 0) {
        r4[0x30] = 1;
        *reinterpret_cast<float*>(r4 + 0x28) = -0.1f;
        return 0;
    }

    return 0;
}

// DECOMP_FUNC(0x00211f8c, 152)
extern "C" s32 func_0026ace0(void);

extern "C" s32 camp_func_00211f8c(void) {
    u8* mgr = *reinterpret_cast<u8**>(0x0043E2A8 + 4);
    const u16* arr = reinterpret_cast<const u16*>(mgr + 0x108);
    s32 total = func_0026ace0();
    s32 count = 0;
    for (s32 i = 0; i < total; ++i) {
        if (arr[i] != 0) {
            count++;
        }
    }
    return count;
}

// DECOMP_FUNC(0x00215bd8, 148)
extern "C" u8 func_00299224(void);
extern "C" void func_002509d8(void);
extern "C" void func_002900b0(u32, u32);
extern "C" void func_002bdac0(void*, u32, u32);
extern "C" void* func_002b6700(u16 id);

extern "C" void script_vm_func_00215bd8(u32 id) {
    u8* mgr = *reinterpret_cast<u8**>(0x0043DD50);
    mgr[0x5F2] = 1;
    mgr[0x5C4] = func_00299224();
    *reinterpret_cast<u16*>(mgr + 0x97E) = static_cast<u16>(id);

    func_002509d8();
    func_002900b0(id, 1);
    func_002bdac0(mgr + 0x34, 0, 0);

    u8* cur = *reinterpret_cast<u8**>(0x0043DD50);
    *reinterpret_cast<u32*>(cur + 8) = *reinterpret_cast<u32*>(cur + 4);
    *reinterpret_cast<u32*>(cur + 4) = 1;
    *reinterpret_cast<u32*>(cur + 0x10) = 0;
    *reinterpret_cast<u32*>(mgr + 0x0C) = 0x1D;

    u8* demon_rec = reinterpret_cast<u8*>(func_002b6700(static_cast<u16>(id)));
    if ((demon_rec[7] & 0x40) != 0) {
        *reinterpret_cast<u32*>(mgr + 0x5C8) = 2;
    } else {
        *reinterpret_cast<u32*>(mgr + 0x5C8) = 1;
    }
}

// DECOMP_FUNC(0x00219624, 128)
extern "C" u32 func_0029ed08(u16 key);
extern "C" const u8* func_002b9364(u16 key);

extern "C" __attribute__((minsize)) s32 camp_func_00219624(const u16* a, const u16* b) {
    const u32 flag_a = func_0029ed08(*a);
    const u32 flag_b = func_0029ed08(*b);
    if (flag_b > flag_a) {
        return -1;
    }
    if (flag_a > flag_b) {
        return 1;
    }

    const u8* const rec_a = func_002b9364(*a);
    const u8* const rec_b = func_002b9364(*b);

    const s32 diff2 = static_cast<s32>(rec_a[2]) - static_cast<s32>(rec_b[2]);
    if (diff2 != 0) {
        return diff2;
    }

    const s32 diff3 = static_cast<s32>(rec_b[3]) - static_cast<s32>(rec_a[3]);
    if (diff3 != 0) {
        return diff3;
    }

    return static_cast<s32>(*reinterpret_cast<const u16*>(rec_a)) -
           static_cast<s32>(*reinterpret_cast<const u16*>(rec_b));
}

extern "C" uint32_t ui_func_0028df3c(uint32_t);
extern "C" uint32_t engine_func_00286928(uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);
extern "C" u32 engine_func_00296f60(u32);
extern "C" u32 engine_func_00289640();

// DECOMP_FUNC(0x00221168, 148)
extern "C" uint32_t engine_func_00221168() {
    auto fn_get_state = reinterpret_cast<uint32_t (*)(uint32_t)>(engine_func_00289640);
    auto fn_get_context = reinterpret_cast<uint32_t (*)(uint32_t)>(func_0028686c);
    auto slots = reinterpret_cast<uint32_t*>(0x0043e188);
    uint32_t state = fn_get_state(ui_func_0028df3c(0));
    if (state == 0) {
        auto object = reinterpret_cast<uint8_t*>(slots[2]);
        if (object != nullptr) object[0x30] = 1;
        object[0x31] = 1;
    }
    auto object = reinterpret_cast<uint8_t*>(slots[1]);
    if (object != nullptr) object[0xa11] = 0x14;
    uint32_t context = fn_get_context(reinterpret_cast<uint32_t>(object));
    uint32_t value = engine_func_00296f60(0);
    uint32_t current = fn_get_state(value);
    return engine_func_00286928(context, value, current, 6, 1, 0);
}

// DECOMP_FUNC(0x00221fb4, 128)
extern "C" u32 engine_func_00259510(u32);
extern "C" u32 battle_func_002bf41c(u32);
extern "C" u32 _3dEventEffect_func_0030a28c(u32, u32, u32, u32);

extern "C" __attribute__((minsize)) u32 engine_func_00221fb4() {
    auto* const global_handle = reinterpret_cast<volatile u32*>(0x0043DF58u);
    const u32 arg0 = engine_func_00259510(0);
    const u32 arg1 = engine_func_00296f60(1);
    const u32 arg2 = engine_func_00296f60(2);
    const u32 arg3 = engine_func_00296f60(3);

    if (engine_func_00289640() != 0) {
        if (battle_func_002bf41c(*global_handle) == 0) {
            return 1;
        }
        return 0;
    }

    *global_handle = _3dEventEffect_func_0030a28c(arg0, arg1, arg2, arg3);
    return 0;
}

// DECOMP_FUNC(0x002220a8, 140)
extern "C" u32 func_002ebe10(void*, void*, float, float);
extern "C" void func_002c4460(void*, u32);

extern "C" u32 ui_func_002220a8(void) {
    u32 idx = func_00296f60(0);
    s32 val = static_cast<s32>(func_00296f60(1));
    float fval = static_cast<float>(val);

    const float* table = reinterpret_cast<const float*>(0x00403788);
    float s0 = table[idx];

    u8* ctx = *reinterpret_cast<u8**>(0x0043DFC0);
    u32 res = func_002ebe10(ctx + 0x738, ctx + 0x73C, s0, fval);

    if (func_002bf41c() != 0) {
        ctx = *reinterpret_cast<u8**>(0x0043DFC0);
        void* sub = *reinterpret_cast<void**>(ctx);
        func_002c4460(sub, res);
    }
    return 1;
}

// DECOMP_FUNC(0x00224730, 152)
extern "C" void* func_002a51dc(void);
extern "C" void func_002a3d50(void*, void*);
extern "C" void func_002a399c(void*, float);
extern "C" u32 func_0021a36c(void*);
extern "C" void func_00281e20(void*);
extern "C" u32 func_002f302c(void*);

extern "C" s32 engine_func_00224730(void* input) {
    u8* r4 = func_002c0ac8(input);
    u32 state = *reinterpret_cast<u32*>(r4 + 4);

    if (state == 0) {
        if (*reinterpret_cast<void**>(r4 + 8) == nullptr) {
            return 0;
        }
        *reinterpret_cast<u32*>(r4 + 4) = 1;
        void* sub = func_002a51dc();
        *reinterpret_cast<void**>(r4 + 0x0C) = sub;
        func_002a3d50(sub, r4 + 0x1C);
        func_002a399c(sub, 0.5f);
        *reinterpret_cast<u32*>(r4 + 0x18) = func_0021a36c(sub);
        r4[0x10] = 1;
        return 0;
    }

    if (state == 1) {
        void* sub = *reinterpret_cast<void**>(r4 + 0x0C);
        func_00281e20(sub);
        if (func_002f302c(sub) != 0) {
            return -1;
        }
        return 0;
    }

    return 0;
}

// DECOMP_FUNC(0x002277fc, 144)
extern "C" void* func_00293c98(void);
extern "C" u32 func_002934d4(void);

extern "C" s32 ui_func_002277fc(void* entity) {
    u8* r3 = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(entity) + 0x1CFC);
    if (r3 == nullptr) {
        return -1;
    }

    func_00293c98();
    if (func_002934d4() != 0) {
        return -1;
    }

    s32 max_val = 0;
    const s16 offsets[4] = {0x68, 0x7E, 0x94, 0xAA};
    for (int i = 0; i < 4; ++i) {
        s16 val = *reinterpret_cast<const s16*>(r3 + offsets[i]);
        if (val > 0 && val > max_val) {
            max_val = val;
        }
    }

    if (max_val <= 0) {
        return *reinterpret_cast<const s16*>(r3 + 0x190);
    }
    return max_val;
}

// DECOMP_FUNC(0x00227f50, 144)
extern "C" u32 engine_func_002c3290(u32 context);
extern "C" u32 engine_func_002b45f8(const void* entry, u32 context, u32 aux);

extern "C" s32 engine_func_00227f50(void* entity) {
    u8* base = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(entity) + 0x1CFC);
    if (base == nullptr) {
        return -1;
    }

    func_00293c98();
    if (func_002934d4() != 0) {
        return -1;
    }

    u32 context = *reinterpret_cast<const u32*>(0x00435D00 + 0x0C);
    for (u32 i = 0; i < 4; ++i) {
        u8* entry = base + 0x58 + i * 22;
        u32 aux = engine_func_002c3290(context);
        if (engine_func_002b45f8(entry, context, aux) == 0) {
            return *reinterpret_cast<const s16*>(entry + 0x10);
        }
    }
    return -1;
}

// DECOMP_FUNC(0x00227fe0, 128)
extern "C" u32 engine_func_002c3290(u32 context);
extern "C" u32 engine_func_002b45f8(const void* entry, u32 context, u32 aux);

extern "C" __attribute__((minsize)) s32 engine_func_00227fe0(const u8* object) {
    auto* const base = *reinterpret_cast<const u8* const*>(object + 0x1cfcu);
    if (base == nullptr) {
        return -1;
    }

    const u32 context = *reinterpret_cast<const u32*>(0x00435D00u + 0x0Cu);

    for (u32 i = 0; i < 4; ++i) {
        const u8* const entry = base + 0x58u + i * 22u;
        const u32 aux = engine_func_002c3290(context);
        if (engine_func_002b45f8(entry, context, aux) == 0) {
            return *reinterpret_cast<const u16*>(entry + 0x12u);
        }
    }

    return -1;
}

// DECOMP_FUNC(0x002282a0, 152)
extern "C" void* func_00293c98(void);
extern "C" u32 func_002934d4(void);

extern "C" s32 ui_func_002282a0(void* entity, u32 flag) {
    u8* comp = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(entity) + 0x1CFC);
    if (comp == nullptr) {
        return -1;
    }

    s16 val = *reinterpret_cast<s16*>(comp + 0x190);
    if (val < 0) {
        return -1;
    }

    func_00293c98();
    if (func_002934d4() != 0) {
        u8* sub = reinterpret_cast<u8*>(func_00293c98());
        if ((*reinterpret_cast<u32*>(sub + 0x44AC) & 2) != 0) {
            return 0;
        }
    }

    if (flag != 0) {
        func_00293c98();
        if (func_002934d4() != 0) {
            return -1;
        }
    }

    comp = *reinterpret_cast<u8**>(reinterpret_cast<u8*>(entity) + 0x1CFC);
    return *reinterpret_cast<s16*>(comp + 0x190);
}

// DECOMP_FUNC(0x0022922c, 128)
extern "C" __attribute__((minsize)) void func_0022922c(const uintptr_t* obj) {
    const auto base_addr = *reinterpret_cast<const uintptr_t*>(*obj + 0x1fc0u);
    auto* const array = reinterpret_cast<uint8_t*>(base_addr);
    for (uint32_t i = 0; i < 109; ++i) {
        auto* const word = reinterpret_cast<uint32_t*>(array + i * 648u);
        *word &= ~0x400u;
    }
}

// DECOMP_FUNC(0x00229aa8, 132)
extern "C" void* ui_func_00282b94(void* inner, s32 idx);

extern "C" u32 ui_func_00229aa8(void* const* obj, const void* table, s32 default_idx) {
    void* const inner = *obj;
    void* const node = ui_func_00282b94(inner, default_idx);

    s32 idx = default_idx;
    if (node != nullptr) {
        idx = static_cast<s32>(*reinterpret_cast<const s16*>(static_cast<const u8*>(node) + 0x6E));
    }

    const auto* const tbl = static_cast<const u8*>(table);
    const u16 flag = *reinterpret_cast<const u16*>(tbl + 0x9D4 + idx * 10);
    if (flag == 0) {
        const auto* const entity_table = *reinterpret_cast<const u8* const*>(static_cast<const u8*>(inner) + 0x1FC0);
        const auto* const elem = entity_table + idx * 648;
        const u32 elem_flags = *reinterpret_cast<const u32*>(elem);

        if ((elem_flags & 1u) != 0 && (elem_flags & 0x400000u) == 0) {
            const s32 timer = *reinterpret_cast<const s32*>(elem + 0xC8);
            if (timer <= 0) {
                return 1;
            }
        }
    }
    return 0;
}

// DECOMP_FUNC(0x00229b2c, 140)
extern "C" u8* script_vm_func_0027eb98(void);

extern "C" void script_vm_func_00229b2c(void* manager) {
    u8* mgr = *reinterpret_cast<u8**>(manager);
    u8* base = *reinterpret_cast<u8**>(mgr + 0x1FC0);

    s32 count = 0;
    s32 min_val = 100000;
    s32 stack[109];

    for (s32 i = 0; i < 109; ++i) {
        u8* entry = base + i * 648;
        if ((*reinterpret_cast<u32*>(entry) & 0x400) != 0) {
            s16 key = *reinterpret_cast<s16*>(entry + 0x1B4);
            if (key <= min_val) {
                min_val = key;
                stack[count++] = *reinterpret_cast<s16*>(entry + 0x6E);
            }
        }
    }

    u8* obj = script_vm_func_0027eb98();
    s32 id = stack[count - 1];
    obj[0x38 + id] = 1;
}

// DECOMP_FUNC(0x00229bd0, 152)
extern "C" u8* func_00226b2c(void*, s16, u32, u32);

extern "C" void battle_func_00229bd0(s32 arg0, u32 arg1, u32 arg2, u32 arg3, u32 arg4) {
    u8* mgr = *reinterpret_cast<u8**>(0x00434290);
    u8* r0 = func_00226b2c(mgr, static_cast<s16>(arg0), 0, arg1);

    if (arg4 != 0) {
        u8* node = *reinterpret_cast<u8**>(mgr + 8);
        while (node != nullptr) {
            u8* next = *reinterpret_cast<u8**>(node + 0x0C);
            if (node[4] == 0x0E && *reinterpret_cast<u32*>(node + 0x28) == 0 && *reinterpret_cast<u32*>(node + 0x4C) == arg3) {
                if (*reinterpret_cast<s16*>(r0 + 2) >= 0) {
                    *reinterpret_cast<s16*>(r0 + 2) = -1;
                    break;
                }
            }
            node = next;
        }
    }

    *reinterpret_cast<u32*>(r0 + 0x28) = arg2;
    r0[4] = 0x0E;
    *reinterpret_cast<u32*>(r0 + 0x4C) = arg3;
}

// DECOMP_FUNC(0x0022b9d0, 132)
extern "C" void engine_func_0022b9d0(const void* src, float* out) {
    const float* src_coords = reinterpret_cast<const float*>(static_cast<const u8*>(src) + 0x50);
    const float limit_x = static_cast<float>(static_cast<s32>(src_coords[0] - 400.0f));
    const float limit_y = static_cast<float>(static_cast<s32>(src_coords[1] - 240.0f));

    float x = out[0];
    if (x <= 0.0f) {
        x = 0.0f;
    }
    if (x > limit_x) {
        x = limit_x;
    }
    out[0] = x;

    float y = out[1];
    if (y <= 0.0f) {
        y = 0.0f;
    }
    if (y > limit_y) {
        y = limit_y;
    }
    out[1] = y;
}

// DECOMP_FUNC(0x0022df7c, 140)
extern "C" const u8* camp_func_002b9364(u32 id);

extern "C" void unite_func_0022df7c(void* container, u32 demon_id) {
    const u8* demon_info = camp_func_002b9364(demon_id);
    if (demon_info == nullptr) {
        return;
    }

    u16 race = *reinterpret_cast<const u16*>(demon_info + 0x90);
    if (race >= 0x160) {
        return;
    }

    s16* slots = reinterpret_cast<s16*>(container);
    u8* flags = reinterpret_cast<u8*>(container) + 0x20;

    for (s32 i = 0; i < 0x10; ++i) {
        if (slots[i] == static_cast<s16>(demon_id)) {
            flags[i] = 1;
            return;
        }
    }

    for (s32 i = 0; i < 0x10; ++i) {
        if (slots[i] == -1) {
            slots[i] = static_cast<s16>(demon_id);
            flags[i] = 1;
            return;
        }
    }
}

// DECOMP_FUNC(0x002306ec, 144)
extern "C" __attribute__((noinline)) u32 camp_func_002bdb2c(
    u8* sprite, u32 type, u32 index,
    const u8* group, u32 panel, float scale);
extern "C" void func_002bdac0(void*, u32, u32);

extern "C" u32 engine_func_002306ec(u32 input) {
    u8* r4 = *reinterpret_cast<u8**>(0x0043E188 + 8);

    if (input != 0) {
        r4[0x82] = 1;
        camp_func_002bdb2c(r4 + 0x7E0, 0x0E, 0, r4 + 0xA4, 11, 1.0f);
        func_002bdac0(r4 + 0x7E0, 8, 0);
    } else {
        r4[0x82] = 2;
        camp_func_002bdb2c(r4 + 0x7E0, 0x0E, 0, r4 + 0xA4, 11, 1.0f);
        func_002bdac0(r4 + 0x7E0, 9, 0);
    }

    return 1;
}

// DECOMP_FUNC(0x0023d230, 132)
extern "C" __attribute__((minsize)) void func_0023d230(void* out, u32 packed) {
    auto* const out_words = reinterpret_cast<u32*>(out);
    auto* const out_floats = reinterpret_cast<float*>(out_words + 2);

    const u8 tag = *reinterpret_cast<const u8*>(0x00490E46u);
    out_words[0] = static_cast<u32>(tag) | 0x80000000u;
    out_words[1] = 0x804F02C0u;

    constexpr float kInv255 = 1.0f / 255.0f;
    out_floats[0] = static_cast<float>(packed & 0xFFu) * kInv255;
    out_floats[1] = static_cast<float>((packed >> 8) & 0xFFu) * kInv255;
    out_floats[2] = static_cast<float>((packed >> 16) & 0xFFu) * kInv255;
    out_floats[3] = static_cast<float>((packed >> 24) & 0xFFu) * kInv255;
}

// DECOMP_FUNC(0x0024095c, 128)
extern "C" __attribute__((minsize)) void func_0024095c(u8* obj, u32 param_1) {
    *reinterpret_cast<u32*>(obj + 0x72C) = param_1;
    *reinterpret_cast<u32*>(obj + 0x728) = 0;

    u32 flags = *reinterpret_cast<u32*>(obj + 0x634) | 0x80000u;
    *reinterpret_cast<u32*>(obj + 0x634) = flags;

    const float* const p1 = reinterpret_cast<const float*>(obj + 0x0C);
    const float* const p2 = reinterpret_cast<const float*>(obj + 0x18);

    const float dx = p1[0] - p2[0];
    const float dy = p1[1] - p2[1];
    const float dz = p1[2] - p2[2];
    const float dist = inline_vsqrt_f32(dx * dx + dy * dy + dz * dz);

    if (dist <= 0.01f) {
        flags &= ~0x80000u;
        *reinterpret_cast<u32*>(obj + 0x634) = flags;
    }
}

// DECOMP_FUNC(0x00247d64, 128)
extern "C" u8* ui_func_002c0ac8(u32 id);

extern "C" __attribute__((minsize)) void engine_func_00247d64(u32 id, s32 duration, s32 reverse_flag) {
    u8* const target = ui_func_002c0ac8(id);
    float* const val_ptr = reinterpret_cast<float*>(target + 0x24);
    float* const step_ptr = reinterpret_cast<float*>(target + 0x28);

    if (reverse_flag != 0) {
        if (duration == 0) {
            *val_ptr = 0.0f;
            *step_ptr = 0.0f;
        } else {
            *val_ptr = 1.0f;
            *step_ptr = -1.0f / static_cast<float>(duration);
        }
    } else {
        if (duration == 0) {
            *val_ptr = 1.0f;
            *step_ptr = 0.0f;
        } else {
            *val_ptr = 0.0f;
            *step_ptr = 1.0f / static_cast<float>(duration);
        }
    }
}

// DECOMP_FUNC(0x0024baf4, 140)
extern "C" void* func_00293c98(void);
extern "C" u32 ui_func_0024bb80(void);
extern "C" u32 func_0028686c(void);
extern "C" u32 func_00296f60(u32);
extern "C" u32 func_00289640(void);
extern "C" void func_00286928(u32, u32, u32, u32, u32, u32);

extern "C" void ui_func_0024baf4(void) {
    u8* ctx = reinterpret_cast<u8*>(func_00293c98());
    u32 r4 = *reinterpret_cast<u32*>(ctx + 0x2234);
    u32 r5 = ui_func_0024bb80();

    if (r4 == 0) {
        r4 = func_0028686c();
    }
    u8* obj = *reinterpret_cast<u8**>(0x0043E188 + 0x0C);
    *reinterpret_cast<u32*>(obj + 0x24) = r5;

    u32 res_r5 = func_00296f60(0);
    u32 r2 = func_00289640();

    func_00286928(r4, res_r5, r2, 0x0C, 0, 0);
}

// DECOMP_FUNC(0x0024c3f8, 148)
extern "C" u8* func_002b0188(void* arg0);

extern "C" void engine_func_0024c3f8(void* arg0, s32 index, s32* out1, s32* out2) {
    u8* obj = func_002b0188(arg0);
    u8* r3 = *reinterpret_cast<u8**>(obj + 4);
    u8* table = *reinterpret_cast<u8**>(r3);

    s32 rem = index % 1000;
    u8* entry = table + rem * 20;

    s32 val1 = *reinterpret_cast<u16*>(entry + 4) & 0x7FFF;
    s32 val2 = *reinterpret_cast<u16*>(entry + 6) & 0x7FFF;

    u8* sub = *reinterpret_cast<u8**>(entry + 0x0C);
    if (sub != nullptr) {
        u16 type = *reinterpret_cast<u16*>(sub + 4);
        if (type == 1 || (sub[0x0C] & 1) != 0) {
            val1 = *reinterpret_cast<s16*>(sub);
            val2 = *reinterpret_cast<s16*>(sub + 2);
        }
    }

    if (out1 != nullptr) {
        *out1 = val1;
    }
    if (out2 != nullptr) {
        *out2 = val2;
    }
}

// DECOMP_FUNC(0x0024de78, 136)
extern "C" void engine_func_002c4360(void* ptr);
extern "C" void engine_func_002c4b30(volatile u8* destination, u32 size);

extern "C" void engine_func_0024de78(void) {
    s32* count_ptr = reinterpret_cast<s32*>(0x00433278);
    s32 count = *count_ptr;
    if (count > 0) {
        u8* base = reinterpret_cast<u8*>(0x00478000);
        for (s32 i = 0; i < count; ++i) {
            u8* entry = base + i * 328;
            void* p13c = *reinterpret_cast<void**>(entry + 0x13C);
            if (p13c != nullptr) {
                engine_func_002c4360(p13c);
                *reinterpret_cast<void**>(entry + 0x13C) = nullptr;
                *reinterpret_cast<u32*>(entry + 0x28) = 0;
            }
            void* p24 = *reinterpret_cast<void**>(entry + 0x24);
            if (p24 != nullptr) {
                engine_func_002c4360(p24);
                *reinterpret_cast<void**>(entry + 0x24) = nullptr;
                *reinterpret_cast<u32*>(entry + 0x20) = 0;
            }
        }
    }
    engine_func_002c4b30(reinterpret_cast<volatile u8*>(0x00478000), 0x5200);
    *count_ptr = 0;
}

// DECOMP_FUNC(0x0024fd10, 148)
extern "C" void* engine_func_002c34a4(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5);
extern "C" void engine_func_002c3b48(void* ptr, u32 size);

extern "C" void* engine_func_0024fd10(const u8* input) {
    u32 r2 = *reinterpret_cast<const u32*>(input + 0x20);
    u32 r1 = *reinterpret_cast<const u32*>(input + 0x24);
    u32 val;
    if (r2 != 0) {
        val = r2 * r1;
    } else {
        val = *reinterpret_cast<const u32*>(input + 0xB8) * r1;
    }

    if (val > 100) {
        val = 100;
    }

    u8* node = reinterpret_cast<u8*>(engine_func_002c34a4(0x10000, 0x100, 0, 0x38, 0x10, 1));
    engine_func_002c3b48(node, 0x38);

    *reinterpret_cast<u32*>(node + 0x00) = val;
    *reinterpret_cast<u32*>(node + 0x04) = 0xFFFFFFFFu;
    *reinterpret_cast<float*>(node + 0x08) = 1.0f;
    *reinterpret_cast<u16*>(node + 0x34) = 1;

    return node;
}

// DECOMP_FUNC(0x002502e8, 128)
extern "C" void engine_func_00256c3c(float* dst_matrix);
extern "C" void func_003f6ea8();
extern "C" void ui_func_002a2f1c();

extern "C" __attribute__((minsize)) void engine_func_002502e8(float* dst, const float* src_quat) {
    engine_func_00256c3c(dst);

    auto* const context_base = reinterpret_cast<uint8_t*>(0x004EA81Cu);
    float* const quat_scratch = reinterpret_cast<float*>(context_base + 0x100u);
    __builtin_memcpy(quat_scratch, src_quat, 4 * sizeof(float));

    func_003f6ea8();
    ui_func_002a2f1c();

    for (int i = 0; i < 3; ++i) {
        const float* const src_row = reinterpret_cast<const float*>(context_base + 0x140u + i * 16);
        float* const dst_row = dst + i * 4;
        dst_row[0] = src_row[0];
        dst_row[1] = src_row[1];
        dst_row[2] = src_row[2];
    }

    dst[12] = 0.0f;
    dst[13] = 0.0f;
    dst[14] = 0.0f;
}

// DECOMP_FUNC(0x00252630, 140)
extern "C" void func_002aeb2c(u32);
extern "C" void func_002a6410(void*, u32, s32);
extern "C" void func_002c45b8(void*, u32);

extern "C" void script_vm_func_00252630(void) {
    u8** global_slot = reinterpret_cast<u8**>(0x00434210);
    u8* r5 = *global_slot;
    if (r5 == nullptr) {
        return;
    }

    s32 voice_id = *reinterpret_cast<s32*>(r5 + 0x2F8);
    if (voice_id >= 0) {
        func_002aeb2c(0x18);
        u8* cur = *global_slot;
        if (cur != nullptr) {
            cur[0x2F4] = 0;
        }
        void* sound_mgr = *reinterpret_cast<void**>(0x00433158);
        func_002a6410(sound_mgr, 0x18, *reinterpret_cast<s32*>(r5 + 0x2F8));
        *reinterpret_cast<s32*>(r5 + 0x2F8) = -1;
        *reinterpret_cast<u32*>(r5 + 0x2E8) = 3;
        *reinterpret_cast<u32*>(r5 + 0x2EC) = 0;
    }

    void* sub_obj = *reinterpret_cast<void**>(r5 + 0x2E4);
    func_002c45b8(sub_obj, 0);
    engine_func_002c4360(r5);
    *global_slot = nullptr;
}

// DECOMP_FUNC(0x00256524, 140)
extern "C" void func_00256524(s32 r0, s32 r1) {
    u8* base = *reinterpret_cast<u8**>(0x00447A78);
    u8* ctx = base + 0xCCC0;
    if (r1 == 0) {
        *ctx = 0;
        return;
    }
    *ctx = 1;

    s16 val0 = (r0 == 0) ? -1 : static_cast<s16>(r0);
    *reinterpret_cast<s16*>(ctx + 2) = val0;

    s16 val1 = static_cast<s16>(r1 * 10);
    *reinterpret_cast<s16*>(ctx + 6) = val1;

    *reinterpret_cast<float*>(ctx + 0x0C) = 0.0f;
    *reinterpret_cast<float*>(ctx + 0x10) = 0.0f;
    *reinterpret_cast<float*>(ctx + 0x14) = 0.0f;

    s16 scaled = static_cast<s16>((val1 * 4) / 10);
    *reinterpret_cast<s16*>(ctx + 4) = scaled;
    *reinterpret_cast<s16*>(ctx + 8) = scaled;
}

// DECOMP_FUNC(0x00262664, 140)
extern "C" s16 func_00262664(void* entity) {
    s16 res = *reinterpret_cast<s16*>(reinterpret_cast<u8*>(entity) + 0x1C);
    u8* r2 = *reinterpret_cast<u8**>(0x00435D90);
    if (r2 == nullptr || *reinterpret_cast<u32*>(r2 + 0x64) == 0x15) {
        return res;
    }

    u8* base = *reinterpret_cast<u8**>(r2 + 0x1FC0);
    for (s32 i = 0; i < 0x6D; ++i) {
        u8* entry = base + i * 648;
        u32 flags = *reinterpret_cast<u32*>(entry);
        if ((flags & 1) != 0 && (flags & 0x40) == 0 && (flags & 2) != 0) {
            if (*reinterpret_cast<void**>(entry + 0x278) == entity) {
                res = *reinterpret_cast<s16*>(entry + 0x1B6);
                break;
            }
        }
    }
    return res;
}

// DECOMP_FUNC(0x00262edc, 144)
extern "C" s32 camp_func_0026ace0(void* ptr);

extern "C" u32 camp_func_00262edc(u16 target_id) {
    u8* base = *reinterpret_cast<u8**>(0x0043E2A8u + 4);
    u8* obj = base + 0x90;
    s32 count = camp_func_0026ace0(obj);
    if (count <= 0) {
        return 0;
    }
    const u16* items = reinterpret_cast<const u16*>(obj + 0x78);
    for (s32 i = 0; i < count; ++i) {
        if (items[i] == target_id) {
            return 1;
        }
    }
    return 0;
}

// DECOMP_FUNC(0x002642d0, 152)
extern "C" u8** script_vm_func_002b780c(u8** first, u8** last, u8** result, const void* val_ptr);

extern "C" void script_vm_func_002642d0(void** table_ptr, s32 index) {
    u8** table = reinterpret_cast<u8**>(*table_ptr);
    u8* item = table[index];

    u8* container = *reinterpret_cast<u8**>(item + 0x0C);
    if (container != nullptr) {
        u8** end = *reinterpret_cast<u8***>(container + 0x1C);
        u8** begin = *reinterpret_cast<u8***>(container + 0x18);
        u8** it = begin;
        while (it != end) {
            if (*it == item) {
                break;
            }
            ++it;
        }

        u8** new_end = it;
        if (it != end) {
            new_end = script_vm_func_002b780c(it + 1, end, it, &item);
        }

        u8** old_end = *reinterpret_cast<u8***>(container + 0x1C);
        *reinterpret_cast<u8***>(container + 0x1C) = new_end;
        if (old_end != new_end) {
            *reinterpret_cast<void**>(item + 0x0C) = nullptr;
        }
    }

    s32* global_counter = reinterpret_cast<s32*>(0x004DAD80);
    *global_counter -= 1;
}

// DECOMP_FUNC(0x002649c0, 136)
extern "C" void script_vm_func_002649c0() {
    u8* target = reinterpret_cast<u8*>(0x0049F91C);
    const u8* r1 = *reinterpret_cast<const u8**>(0x00447060);
    const u8* r2 = *reinterpret_cast<const u8**>(0x00447E88);

    target[0x2F8] = 1;
    *reinterpret_cast<u32*>(target + 0x2FC) = *reinterpret_cast<const u32*>(r1 + 0x40);
    *reinterpret_cast<u32*>(target + 0x300) = *reinterpret_cast<const u32*>(r1 + 0x48);
    *reinterpret_cast<u32*>(target + 0x304) = *reinterpret_cast<const u32*>(target + 0x08);

    *reinterpret_cast<float*>(target + 0x308) = *reinterpret_cast<const float*>(r2 + 0x1C);
    *reinterpret_cast<float*>(target + 0x30C) = *reinterpret_cast<const float*>(r2 + 0x20);
    *reinterpret_cast<float*>(target + 0x310) = *reinterpret_cast<const float*>(r2 + 0x24);
    *reinterpret_cast<u32*>(target + 0x314) = *reinterpret_cast<const u32*>(r2 + 0x4C);

    *reinterpret_cast<u32*>(target + 0x31C) = *reinterpret_cast<const u32*>(r1 + 0x40);
    *reinterpret_cast<u32*>(target + 0x320) = *reinterpret_cast<const u32*>(r1 + 0x48);

    *reinterpret_cast<u32*>(target + 0x324) = *reinterpret_cast<const u32*>(r2 + 0x1C);
    *reinterpret_cast<u32*>(target + 0x328) = *reinterpret_cast<const u32*>(r2 + 0x20);
    *reinterpret_cast<u32*>(target + 0x32C) = *reinterpret_cast<const u32*>(r2 + 0x24);
    *reinterpret_cast<u32*>(target + 0x330) = *reinterpret_cast<const u32*>(r2 + 0x4C);
}

// DECOMP_FUNC(0x00269e54, 140)
extern "C" s16 func_00269e54(void* entity) {
    s16 res = *reinterpret_cast<s16*>(reinterpret_cast<u8*>(entity) + 0x0E);
    u8* r2 = *reinterpret_cast<u8**>(0x00435D90);
    if (r2 == nullptr || *reinterpret_cast<u32*>(r2 + 0x64) == 0x15) {
        return res;
    }

    u8* base = *reinterpret_cast<u8**>(r2 + 0x1FC0);
    for (s32 i = 0; i < 0x6D; ++i) {
        u8* entry = base + i * 648;
        u32 flags = *reinterpret_cast<u32*>(entry);
        if ((flags & 1) != 0 && (flags & 0x40) == 0 && (flags & 8) != 0) {
            if (*reinterpret_cast<void**>(entry + 0x27C) == entity) {
                res = *reinterpret_cast<s16*>(entry + 0x1B6);
                break;
            }
        }
    }
    return res;
}

// DECOMP_FUNC(0x0026b734, 152)
extern "C" u32 engine_func_002c586c(void* out);
extern "C" s32 script_vm_func_0025461c(const void* dt);
extern "C" s32 script_vm_func_002545c4(const void* dt);
extern "C" s32 script_vm_func_0025456c(const void* dt);
extern "C" s32 script_vm_func_002a8730(s32 day, s32 month, s32 year);
extern "C" s32 ui_func_003e0eac(const void* dt);
extern "C" s32 ui_func_003e0f14(const void* dt);
extern "C" s32 ui_func_003e0f80(const void* dt);

extern "C" void ui_func_0026b734(void) {
    u64 raw_dt;
    engine_func_002c586c(&raw_dt);

    u64 dt = raw_dt;
    s32 year = script_vm_func_0025461c(&dt);
    s32 month = script_vm_func_002545c4(&dt);
    s32 day = script_vm_func_0025456c(&dt);
    s32 days = script_vm_func_002a8730(day, month, year);

    s32 hours = days * 24 + ui_func_003e0eac(&dt);
    s32 minutes = hours * 60 + ui_func_003e0f14(&dt);
    s32 seconds = minutes * 60 + ui_func_003e0f80(&dt);

    u8* ptr = *reinterpret_cast<u8**>(0x0043E2A8 + 0x0C);
    *reinterpret_cast<s32*>(ptr + 4) = seconds;
}

// DECOMP_FUNC(0x0026ea7c, 152)
extern "C" void engine_func_0026ea7c(
    u32 mode, float* out,
    float x0, float y0, float z0,
    float x1, float y1, float z1,
    float x2, float y2, float z2,
    float x3, float y3, float z3) {
    float avg_y = (y0 + y1 + y2 + y3) * 0.25f;
    float avg_z = (z0 + z1 + z2 + z3) * 0.25f;

    if (mode == 0) {
        out[0] = 0.0f;
        out[1] = avg_y;
        out[2] = avg_z;
    } else {
        float avg_x = (x0 + x1 + x2 + x3) * 0.25f;
        if (mode == 1) {
            out[0] = avg_x;
            out[1] = 0.0f;
            out[2] = avg_z;
        } else if (mode == 2) {
            out[0] = avg_x;
            out[1] = avg_y;
            out[2] = 0.0f;
        }
    }
}

// DECOMP_FUNC(0x0026f370, 136)
extern "C" float func_002c55e4(u32 curr_step, u32 total_steps);

extern "C" u32 func_0026f370(float* out_val, u32 curr_step, u32 total_steps, float start_val, float target_val) {
    const float curr = func_002c55e4(curr_step, total_steps);
    const float diff = target_val - start_val;
    const bool reached = (curr_step == total_steps);

    *out_val = curr;
    if (diff > 0.0f) {
        if (curr >= target_val) {
            *out_val = target_val;
            return 1;
        }
    } else {
        if (curr <= target_val) {
            *out_val = target_val;
            return 1;
        }
    }

    if (reached) {
        *out_val = target_val;
        return 1;
    }
    return 0;
}

// DECOMP_FUNC(0x002701c4, 140)
extern "C" void* ui_func_0026b844(void);
extern "C" void func_002bcf58(void* dst, void* src, u32 size);
extern "C" void* ui_func_0026b830(void);
extern "C" void func_002adb40(void* dst, void* src);
extern "C" u8* ui_func_002c0b94(void);
extern "C" void ui_func_002e0b50(void);
extern "C" void func_002c5a6c(void);
extern "C" void ui_func_0026e594(void* obj);
extern "C" void engine_func_002c4360(void* ptr);

extern "C" void script_vm_func_002701c4(void) {
    u8* r4 = reinterpret_cast<u8*>(0x0044DE28);
    void* p10 = *reinterpret_cast<void**>(r4 + 0x10);
    if (p10 == nullptr) {
        return;
    }

    void* r0 = ui_func_0026b844();
    func_002bcf58(r0, p10, 0x80);

    r0 = ui_func_0026b830();
    func_002adb40(r0, *reinterpret_cast<void**>(r4 + 0x14));

    r0 = ui_func_002c0b94();
    func_002bcf58(r0, *reinterpret_cast<void**>(r4 + 0x18), 0x24D28);

    ui_func_002e0b50();
    func_002c5a6c();

    void* obj = *reinterpret_cast<void**>(0x00433158);
    ui_func_0026e594(obj);

    engine_func_002c4360(*reinterpret_cast<void**>(r4 + 0x10));
    engine_func_002c4360(*reinterpret_cast<void**>(r4 + 0x14));
    engine_func_002c4360(*reinterpret_cast<void**>(r4 + 0x18));

    *reinterpret_cast<void**>(r4 + 0x10) = nullptr;
    *reinterpret_cast<void**>(r4 + 0x14) = nullptr;
    *reinterpret_cast<void**>(r4 + 0x18) = nullptr;
}

// DECOMP_FUNC(0x002706e4, 140)
extern "C" void script_vm_func_002711e0(void* ptr);

extern "C" void script_vm_func_002706e4() {
    u8* target = reinterpret_cast<u8*>(0x0049F91C);
    const u8* r4 = *reinterpret_cast<const u8**>(0x00447E28);

    script_vm_func_002711e0(target + 0x94);

    target[0x2F8] = 1;
    *reinterpret_cast<u32*>(target + 0x2FC) = *reinterpret_cast<const u32*>(r4 + 0x2C);
    *reinterpret_cast<u32*>(target + 0x300) = *reinterpret_cast<const u32*>(r4 + 0x30);
    *reinterpret_cast<u32*>(target + 0x304) = *reinterpret_cast<const u32*>(target + 0x08);

    *reinterpret_cast<float*>(target + 0x308) = *reinterpret_cast<const float*>(target + 0x94);
    *reinterpret_cast<u32*>(target + 0x30C) = *reinterpret_cast<const u32*>(target + 0x98);
    *reinterpret_cast<u32*>(target + 0x310) = *reinterpret_cast<const u32*>(target + 0x9C);

    const float s1 = *reinterpret_cast<const float*>(target + 0xA0);
    *reinterpret_cast<float*>(target + 0x314) = s1;
    *reinterpret_cast<float*>(target + 0x318) = s1;

    *reinterpret_cast<u32*>(target + 0x31C) = *reinterpret_cast<const u32*>(r4 + 0x2C);
    *reinterpret_cast<u32*>(target + 0x320) = *reinterpret_cast<const u32*>(r4 + 0x30);

    *reinterpret_cast<float*>(target + 0x324) = *reinterpret_cast<const float*>(target + 0x94);
    *reinterpret_cast<u32*>(target + 0x328) = *reinterpret_cast<const u32*>(target + 0x98);
    *reinterpret_cast<u32*>(target + 0x32C) = *reinterpret_cast<const u32*>(target + 0x9C);

    const u32 w90 = *reinterpret_cast<const u32*>(target + 0x90);
    *reinterpret_cast<u32*>(target + 0x330) = w90;
    *reinterpret_cast<u32*>(target + 0x334) = w90;
}

// DECOMP_FUNC(0x00275984, 148)
extern "C" u32 script_vm_func_002920e4(u32 id, float x, float y, float z);

extern "C" void script_vm_func_00275984(void) {
    u8* mgr = *reinterpret_cast<u8**>(0x00448C20);
    if (mgr[9] == 0 || mgr[8] == 0) {
        return;
    }

    s32 count = *reinterpret_cast<s32*>(mgr + 4);
    mgr[8] = 0;
    if (count <= 0) {
        return;
    }

    for (s32 i = 0; i < count; ++i) {
        mgr = *reinterpret_cast<u8**>(0x00448C20);
        u8* entry = mgr + i * 32;
        if (entry[0x0C] != 0 && *reinterpret_cast<u16*>(entry + 0x1C) == 0 && *reinterpret_cast<u32*>(entry + 0x14) == 0) {
            u32 id = *reinterpret_cast<u32*>(entry + 0x10);
            const float* pos = reinterpret_cast<const float*>(entry + 0x20);
            u32 icon = script_vm_func_002920e4(id, pos[0], pos[1], pos[2]);
            *reinterpret_cast<u32*>(entry + 0x14) = icon;
        }
    }
}

// DECOMP_FUNC(0x002762e8, 132)
extern "C" void* engine_func_002c2b1c();
extern "C" void script_vm_func_002899c4(s32 val, s32 p1, s32 p2);

extern "C" void script_vm_func_002762e8(s32 target_id) {
    auto* const ctx = static_cast<u8*>(engine_func_002c2b1c());
    const s32 count = *reinterpret_cast<const s8*>(ctx + 0xDE3);
    if (count <= 0) {
        return;
    }

    for (s32 i = 0; i < *reinterpret_cast<const s8*>(ctx + 0xDE3); ++i) {
        auto* const active_ptr = ctx + 0xDE4 + i;
        if (*active_ptr == 0) {
            continue;
        }

        const s16 id = *reinterpret_cast<const s16*>(ctx + 0xE04 + i * 2);
        if (id != target_id) {
            continue;
        }

        *active_ptr = 0;
        const s16 val = *reinterpret_cast<const s16*>(ctx + 0xDF4 + i * 2);
        if (val != 0) {
            script_vm_func_002899c4(val, 1, 1);
        }
    }
}

// DECOMP_FUNC(0x00276c24, 136)
extern "C" s32 script_vm_func_0024c538();
extern "C" const u8* script_vm_func_0027d9b8(u32 index);

extern "C" s32 script_vm_func_00276c24(s32 p0, s32 p1, s32 p2) {
    u32* query = reinterpret_cast<u32*>(0x0049FD14);
    query[0] = static_cast<u32>(p0);
    query[1] = static_cast<u32>(p1);
    query[2] = static_cast<u32>(p2);

    if (p2 == -1) {
        query[3] = 0xFFFFFFFFu;
        return -1;
    }

    const s32 count = script_vm_func_0024c538();
    if (count > 0) {
        for (s32 i = 0; i < count; ++i) {
            const u8* entry = script_vm_func_0027d9b8(static_cast<u32>(i));
            if (static_cast<s8>(entry[0]) == static_cast<s8>(p0) &&
                static_cast<s8>(entry[1]) == static_cast<s8>(p1) &&
                entry[2] == static_cast<u8>(p2)) {
                if (entry[3] != 0xFF) {
                    query[3] = entry[3];
                    return static_cast<s32>(entry[3]);
                }
                break;
            }
        }
    }

    query[3] = 0xFFFFFFFFu;
    return -1;
}

// DECOMP_FUNC(0x00277dcc, 128)
extern "C" u32 script_vm_func_002857e4();
extern "C" s32 script_vm_func_00255050(u32 code);

extern "C" __attribute__((minsize)) void script_vm_func_00277dcc(u16 code, u16 param) {
    if (code == 0x24) {
        return;
    }

    if (script_vm_func_002857e4() == 1) {
        if (script_vm_func_00255050(0x29) == 1) {
            return;
        }
    }

    if (code != 0x18 && code < 0x64) {
        if (script_vm_func_00255050(code) == 1) {
            return;
        }
    }

    auto* const global_ptr = *reinterpret_cast<u8**>(0x00447A78u);
    auto* const target = reinterpret_cast<u32*>(global_ptr + 0xCCB8u);
    target[0] = 1;
    target[1] = (static_cast<u32>(param) << 16) | code;
}

// DECOMP_FUNC(0x00289044, 140)
extern "C" u8* script_vm_func_002b66ec(s32);
extern "C" u8* camp_func_002a8a08();
extern "C" u8* camp_func_002a89e4(s32);

extern "C" u32 camp_func_00289044(s16 threshold, s16 filter_id) {
    if (filter_id < 0) {
        u8* p = script_vm_func_002b66ec(0);
        const s16 val = *reinterpret_cast<const s16*>(p + 0x1C);
        return (val < threshold) ? 1 : 0;
    }

    u8* base = camp_func_002a8a08();
    for (s32 slot = 0; slot < 24; ++slot) {
        const s8 active = *reinterpret_cast<const s8*>(base + slot + 0x90F0);
        if (active >= 0) {
            u8* entity = camp_func_002a89e4(active);
            if (entity != nullptr) {
                const u16 id = *reinterpret_cast<const u16*>(entity + 0x46);
                const s16 val = *reinterpret_cast<const s16*>(entity + 0x0E);
                if (id == static_cast<u16>(filter_id) && val < threshold) {
                    return 1;
                }
            }
        }
    }
    return 0;
}

// DECOMP_FUNC(0x0028de84, 136)
extern "C" u8* camp_func_002b66ec(s32);
extern "C" u8* battle_func_002a89e4(s32);
extern "C" s32 engine_func_002b0788(s16);

extern "C" s32 script_vm_func_0028de84(u8* obj) {
    if (obj[0x23] != 0) {
        return -1;
    }

    const s32 id = *reinterpret_cast<const s32*>(obj + 0x34);
    u16 mask;
    if (id < 0) {
        mask = *reinterpret_cast<const u16*>(camp_func_002b66ec(id) + 0x72);
    } else {
        mask = *reinterpret_cast<const u16*>(battle_func_002a89e4(id) + 0x44);
    }

    const u32 target_idx = *reinterpret_cast<const u32*>(obj + 0x1C);
    u32 match_count = 0;
    for (s16 bit = 1; bit < 11; ++bit) {
        if ((mask & (1u << bit)) != 0) {
            if (target_idx == match_count) {
                return engine_func_002b0788(bit);
            }
            ++match_count;
        }
    }

    return -1;
}

// DECOMP_FUNC(0x002918c4, 140)
extern "C" s32 ui_func_00297004(u32 p0, u32 p1);

extern "C" float ui_func_002918c4(u32 mode, u32 p1, u32 p2) {
    if (mode == 0) {
        s32 val = ui_func_00297004(0, p1);
        return static_cast<float>(val) / static_cast<float>(p2);
    }
    if (mode == 1) {
        s32 val = ui_func_00297004(0, p1);
        return -(static_cast<float>(val) / static_cast<float>(p2));
    }
    if (mode == 2) {
        s8 check = static_cast<s8>(ui_func_00297004(0, 1));
        s32 val = ui_func_00297004(0, p1);
        float res = static_cast<float>(val) / static_cast<float>(p2);
        return (check == 0) ? -res : res;
    }
    return 0.0f;
}

// DECOMP_FUNC(0x00295300, 140)
extern "C" u32 ui_func_00295300(u8* obj) {
    auto* const chunk = *reinterpret_cast<u8* const*>(obj + 0x28);
    if (chunk == nullptr) {
        return 0;
    }
    if (obj[0x3C] != 0) {
        return 1;
    }

    obj[0x3C] = 1;
    *reinterpret_cast<u8**>(obj + 0x10) = chunk;

    if (*reinterpret_cast<const u32*>(chunk) != 0x57444B4Eu) {
        *reinterpret_cast<u8**>(obj + 0x10) = nullptr;
        return 1;
    }

    auto* cursor = chunk + 0x28;
    *reinterpret_cast<u8**>(obj + 0x14) = cursor;

    const u32 count4 = *reinterpret_cast<const u16*>(chunk + 4);
    cursor += count4 * 32u;
    *reinterpret_cast<u8**>(obj + 0x18) = cursor;

    const u32 count8 = *reinterpret_cast<const u32*>(chunk + 8);
    cursor += count8 * 40u;
    *reinterpret_cast<u8**>(obj + 0x1C) = cursor;

    const u32 count6 = *reinterpret_cast<const u16*>(chunk + 6);
    cursor += count6 * 4u;
    *reinterpret_cast<u8**>(obj + 0x20) = cursor;

    const u32 countC = *reinterpret_cast<const u16*>(chunk + 0xC);
    cursor += countC * 24u;
    *reinterpret_cast<u8**>(obj + 0x24) = cursor;

    return 1;
}

// DECOMP_FUNC(0x00295f04, 140)
extern "C" const void* Tbb_GetGlobalSubTable(u32 table_id, u32 sub_id);
extern "C" const void* Tbb_GetPayloadData(const void* subtable);
extern "C" const u8* camp_func_002b9364(u32);

extern "C" u32 script_vm_func_00295f04(void* obj, s32 level) {
    if (level >= 99) {
        return 0;
    }

    const void* sub1 = Tbb_GetGlobalSubTable(9, 1);
    auto* const tbl1 = static_cast<const u32*>(Tbb_GetPayloadData(sub1));
    const u32 base_cost = tbl1[level - 1];

    auto* const info = camp_func_002b9364(reinterpret_cast<uintptr_t>(obj));
    const s32 diff = (level - static_cast<s32>(info[3])) + 1;

    u32 rate;
    if (diff <= 0) {
        rate = 100;
    } else {
        s32 clamped_diff = diff;
        if (clamped_diff > 10) {
            clamped_diff = 10;
        }
        const void* sub2 = Tbb_GetGlobalSubTable(9, 2);
        auto* const tbl2 = static_cast<const u16*>(Tbb_GetPayloadData(sub2));
        rate = tbl2[clamped_diff - 1];
    }

    return (base_cost * rate) / 100u;
}

// DECOMP_FUNC(0x002960d4, 128)
extern "C" const void* Tbb_GetPayloadData(const void* subtable);

extern "C" u32 camp_func_002960d4(u16 key, u32 index, s32 stat_val) {
    const void* const sub1 = Tbb_GetGlobalSubTable(9, 1);
    const auto* const table1 = reinterpret_cast<const u32*>(Tbb_GetPayloadData(sub1));
    const u32 base_val = table1[index - 1];

    const u8* const rec = camp_func_002b9364(key);
    s32 diff = stat_val - static_cast<s32>(rec[3]) + 1;

    u32 scale;
    if (diff <= 0) {
        scale = 100;
    } else {
        if (diff > 10) {
            diff = 10;
        }
        const void* const sub2 = Tbb_GetGlobalSubTable(9, 2);
        const auto* const table2 = reinterpret_cast<const u16*>(Tbb_GetPayloadData(sub2));
        scale = table2[diff - 1];
    }

    return (base_val * scale) / 100;
}

// DECOMP_FUNC(0x0029933c, 152)
extern "C" u8* ui_func_002c0b94();
extern "C" void script_vm_func_002b90e0(void* sprite, u32 arg);
extern "C" void camp_func_002bf030(void* sprite, u32 arg);
extern "C" u32 camp_func_002bdb2c(
    u8* sprite, u32 type, u32 index,
    const u8* group, u32 panel, float scale);

extern "C" u32 camp_func_0029933c() {
    u8* base = *reinterpret_cast<u8**>(0x0043E188u + 8);
    u8* p = ui_func_002c0b94();
    u32 val = *reinterpret_cast<const u32*>(p + 0x1F454);
    if (val == 0) {
        return 1;
    }

    *reinterpret_cast<u32*>(base + 0x9C) = val;
    base[0xA0] = 1;
    base[0xA1] = 1;

    u8* sprite = base + 0x86C;
    camp_func_002bdb2c(sprite, 0x0E, 0xFFFFFFFFu, base + 0xA4, 0x0B, 1.0f);
    script_vm_func_002b90e0(sprite, 0x16);
    camp_func_002bf030(sprite, 6);
    return 1;
}

// DECOMP_FUNC(0x0029957c, 144)
extern "C" void engine_func_002946f4(u32 handle, u32 mode, u32 count);

extern "C" void engine_func_0029957c(u32 mode) {
    u8* const* global_slot = reinterpret_cast<u8* const*>(0x0044E140u + 4);
    u8* const base = *global_slot;
    if (base != nullptr) {
        if (mode == 0) {
            u32 handle = *reinterpret_cast<const u32*>(base + 0x1E80);
            engine_func_002946f4(handle, 0, 7);
        } else if (mode == 1) {
            u32 handle = *reinterpret_cast<const u32*>(base + 0x1E80);
            engine_func_002946f4(handle, 1, 7);
        } else if (mode == 2) {
            u32 handle = *reinterpret_cast<const u32*>(base + 0x1E80);
            engine_func_002946f4(handle, 2, 7);
        }

        *reinterpret_cast<u32*>(base + 0x10) = 0;
        *reinterpret_cast<u32*>(base + 0x12DC) = 6;
    }
}

// DECOMP_FUNC(0x0029bddc, 140)
extern "C" void* sub_002A135C(void* ctx);
extern "C" void* sub_002B0434(void* ctx, u32 arg);
extern "C" void sub_002B0418(u32 arg);
extern "C" void sub_001181B0(void* ptr);
extern "C" void sub_00138330(void* ptr, u32* out_val);
extern "C" void* sub_002B2B78(void* ptr, u32 val);
extern "C" void sub_002A9498(void* field_8, u32 val);
extern "C" void sub_002B2928(void* node);
extern "C" void sub_002B2814(void* mgr, void* node, u32 flag);

extern "C" void* engine_func_0029bddc(void* ctx, u32 val) {
    struct SubNode {
        u32 pad0;
        void* field_4;
        u32 field_8;
    };
    struct Node {
        u32 pad0;
        void* field_4;
        SubNode* field_8;
    };

    Node* node = reinterpret_cast<Node*>(sub_002A135C(ctx));
    node->field_8->field_8 = val;

    void* res4 = sub_002B0434(ctx, 0);
    node->field_4 = res4;
    sub_002B0418(1);
    sub_001181B0(res4);

    u32 sp_val = 0;
    sub_00138330(res4, &sp_val);
    void* res2 = sub_002B2B78(res4, sp_val);
    node->field_8->field_4 = res2;

    sub_002A9498(node->field_8, val);
    sub_002B2928(node);
    sub_002B2814(reinterpret_cast<void*>(0x004DAD60), node, 0);

    return node;
}

// DECOMP_FUNC(0x002a140c, 148)
extern "C" u32 engine_func_002a1578();

extern "C" u32 engine_func_002a140c() {
    const u32 val = engine_func_002a1578();
    if ((val & 0x3FC00u) != 0x13800u) {
        return 0;
    }

    if (val == 0xC9413910u) {
        return 1;
    }

    if (val < 0xC9413910u) {
        const u32 diff = val - 0xC9413910u;
        const u32 r1 = diff + 0x00A00007u;
        if (r1 == 0) {
            return 1;
        }
        const u32 r1_next = r1 + 0xFFE00084u - 0x00800088u;
        if (r1_next == 0) {
            return 1;
        }
    } else {
        const u32 r1 = val + 0x36BEC6EEu - 0x00200008u;
        if (r1 == 0) {
            return 1;
        }
    }

    const u32 low10 = val & 0x3FFu;
    if (low10 >= 0x60u && low10 < 0x80u) {
        return 1;
    }

    return 0;
}

// DECOMP_FUNC(0x002a515c, 128)
extern "C" u32 engine_func_002ae16c(const void* sub);
extern "C" u32 engine_func_002ae074(const void* field8, u32 entry, void* target);

extern "C" u32 engine_func_002a515c(void* target, u32 slot_index) {
    auto* const ctx = *reinterpret_cast<u8* const*>(0x0043DFC0u);
    if (!ctx) {
        return 0;
    }

    auto* const sub = *reinterpret_cast<u8* const*>(ctx + 0x5E4);
    if (!sub || !engine_func_002ae16c(sub)) {
        return 1;
    }

    const auto* const sub_field8 = *reinterpret_cast<const void* const*>(sub + 8);
    const auto* const table = reinterpret_cast<const u32*>(0x0043E048u);
    const u32 ret = engine_func_002ae074(sub_field8, table[slot_index], target);

    if (slot_index == 0) {
        auto* const target_y = reinterpret_cast<float*>(static_cast<u8*>(target) + 8);
        const float offset = *reinterpret_cast<const float*>(ctx + 0x640);
        *target_y += offset;
    }

    return ret;
}

// DECOMP_FUNC(0x002a9414, 132)
extern "C" void battle_func_002ade34(void* buf, u32 size, u32 mode);

extern "C" void func_002a9414(const u32* a, const u32* b, const u32* c) {
    u32 buf[12];
    auto* const src1 = reinterpret_cast<const u32*>(0x00409780u + 0x130u);
    auto* const src2 = reinterpret_cast<const u32*>(0x00409780u + 0x150u);

    for (int i = 0; i < 8; ++i) {
        buf[i] = src1[i];
    }
    for (int i = 0; i < 4; ++i) {
        buf[8 + i] = src2[i];
    }

    buf[0] = a[2];
    buf[2] = a[1];
    buf[3] = a[0];

    buf[4] = b[2];
    buf[6] = b[1];
    buf[7] = b[0];

    buf[10] = c[1];
    buf[11] = c[0];

    battle_func_002ade34(buf, 0x30, 1);
}

// DECOMP_FUNC(0x002b0614, 140)
extern "C" u32 engine_func_002b0614(const char* str) {
    s32 len = static_cast<s32>(engine_func_002c3290(reinterpret_cast<uintptr_t>(str)));
    if (len > 8) {
        len = 8;
    }
    if (len <= 0) {
        return 0;
    }

    s32 i = 0;
    if ((len & 1) != 0) {
        if (str[0] == ':') {
            return 1;
        }
        i = 1;
    }

    while (i < len) {
        if (str[i] == ':' || str[i + 1] == ':') {
            return 1;
        }
        i += 2;
    }

    return 0;
}

// DECOMP_FUNC(0x002b32e0, 144)
extern "C" u32 func_002b32e0(u32 val) {
    auto* const tbl = reinterpret_cast<const u32*>(0x00465120u);
    const u32 r0_start = tbl[7];  // +0x1C
    const u32 r1_start = tbl[8];  // +0x20
    const u32 r2_start = tbl[9];  // +0x24
    const u32 r3_start = tbl[10]; // +0x28

    if (val >= r0_start && val <= r0_start + tbl[11]) { // +0x2C
        return 0;
    }
    if (val >= r1_start && val <= r1_start + tbl[12]) { // +0x30
        return 1;
    }
    if (val >= r2_start && val <= r2_start + tbl[13]) { // +0x34
        return 2;
    }
    if (val >= r3_start && val <= r3_start + tbl[14]) { // +0x38
        return 3;
    }
    return 0;
}

// DECOMP_FUNC(0x002b7584, 152)
extern "C" void func_002b7584(float* out, const float* in) {
    const float in_28 = in[10];
    const float in_2c = in[11];
    out[4] = in_2c / in_28;
    out[5] = in_2c / (in_28 - 1.0f);

    const float scale_x = in_2c / (in[0] * in_28);
    out[0] = (in[2] - 1.0f) * scale_x;
    out[1] = (in[2] + 1.0f) * scale_x;

    const float scale_y = in_2c / (in[5] * in_28);
    out[3] = (in[6] + 1.0f) * scale_y;
    out[2] = (in[6] - 1.0f) * scale_y;
}

// DECOMP_FUNC(0x002b8070, 148)
extern "C" void ui_func_002b8524(void);
extern "C" void ui_func_002b8104(
    u32 a0, u32 a1, u32 a2, u32 a3,
    float s0, float s1, float s2, float s3, float s4, float s5, float s6, float s7, float s8);

extern "C" void ui_func_002b8070(
    float s0, float s1, float s2, float s3, float s4, float s5, float s6, float s7, float s8) {
    ui_func_002b8524();
    ui_func_002b8104(0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu, 0xFFFFFFFFu, s0, s1, s2, s3, s4, s5, s6, s7, s8);
}

// DECOMP_FUNC(0x002b89fc, 132)
extern "C" u32 ui_func_002b2530(void* handle);
extern "C" void script_vm_func_002a72fc(void* sub);
extern "C" void engine_func_002b2520(void* sub);
extern "C" void engine_func_002c4360(void* main);

extern "C" u32 battle_func_002b89fc() {
    auto** const p_main = reinterpret_cast<u8**>(0x0044DB8Cu);
    auto* main = *p_main;
    if (!main) {
        return 0;
    }

    void* const handle = *reinterpret_cast<void**>(main);
    if (ui_func_002b2530(handle) != 0) {
        return 1;
    }

    if (main[0x18] == 0) {
        return 1;
    }

    main = *p_main;
    if (!main) {
        return 0;
    }

    main[0x18] = 1;

    void* sub = *reinterpret_cast<void**>(main + 0x1C);
    if (sub != nullptr) {
        script_vm_func_002a72fc(sub);
        sub = *reinterpret_cast<void**>(main + 0x1C);
        engine_func_002b2520(sub);
        *reinterpret_cast<void**>(main + 0x1C) = nullptr;
    }

    engine_func_002c4360(*p_main);
    *p_main = nullptr;

    return 0;
}

// DECOMP_FUNC(0x002baacc, 144)
extern "C" void camp_func_002c3344(void* obj);
extern "C" u32 camp_func_002c32f8(
    u8* group, u32 table, u32 count, u32 reg_word,
    u32 stack_0, u32 stack_1, u32 stack_2,
    u32 stack_3, u32 stack_4, u32 stack_5, u32 stack_6);

extern "C" void engine_func_002baacc(u8* obj) {
    u32* words = reinterpret_cast<u32*>(obj);
    words[0] = 0;
    words[1] = 0;
    words[2] = 0;
    words[3] = 0;
    words[4] = 0;
    obj[0x414] = 1;
    obj[0x415] = 1;
    *reinterpret_cast<u32*>(obj + 0x418) = 0;
    *reinterpret_cast<u32*>(obj + 0x41c) = 0;

    camp_func_002c3344(obj + 0x420);

    const u32 base = 0x003FF3F4u;
    const u32 s1 = base - 0x54u;
    const u32 s3_reg = s1 - 0x48u;
    const u32 r1_arg = s3_reg - 0x78u;
    camp_func_002c32f8(
        obj + 0x420,
        r1_arg,
        0x78,
        s3_reg,
        0x48,
        s1,
        0x54,
        0,
        0,
        base,
        0x310
    );
}

// DECOMP_FUNC(0x002bc170, 144)
extern "C" void engine_func_002bc170(float* mtx, float left, float right, float bottom, float top, float near_val, float far_val) {
    const float dx = right - left;
    const float dy = top - bottom;
    const float dz = far_val - near_val;

    const float inv_dx = 1.0f / dx;
    const float inv_dy = 1.0f / dy;
    const float inv_dz = 1.0f / dz;

    mtx[0] = inv_dx * 2.0f;
    mtx[1] = 0.0f;
    mtx[2] = 0.0f;
    mtx[3] = -(right + left) * inv_dx;

    mtx[4] = 0.0f;
    mtx[5] = inv_dy * 2.0f;
    mtx[6] = 0.0f;
    mtx[7] = -(top + bottom) * inv_dy;

    mtx[8] = 0.0f;
    mtx[9] = 0.0f;
    mtx[10] = inv_dz;
    mtx[11] = near_val * inv_dz;

    mtx[12] = 0.0f;
    mtx[13] = 0.0f;
    mtx[14] = 0.0f;
    mtx[15] = 1.0f;
}

// DECOMP_FUNC(0x002bdb2c, 152)
extern "C" void engine_func_002c4b30(volatile u8* destination, u32 size);

extern "C" __attribute__((noinline, minsize)) u32 camp_func_002bdb2c(
    u8* __restrict sprite, u32 type, u32 index,
    const u8* __restrict group,
    u32 panel, f32 scale) {
    engine_func_002c4b30(sprite, 0x8C);

    *reinterpret_cast<u32*>(sprite + 0x00) = type;
    *reinterpret_cast<u32*>(sprite + 0x04) = index;
    *reinterpret_cast<u32*>(sprite + 0x08) = 0xFFFFFFFFu;
    *reinterpret_cast<f32*>(sprite + 0x20) = scale;
    *reinterpret_cast<u16*>(sprite + 0x38) = static_cast<u16>(panel);
    *reinterpret_cast<f32*>(sprite + 0x24) = 1.0f;
    *reinterpret_cast<f32*>(sprite + 0x28) = 1.0f;
    *reinterpret_cast<f32*>(sprite + 0x2C) = 1.0f;

    *reinterpret_cast<u32*>(sprite + 0x48) = reinterpret_cast<u32>(group);
    const u32* const group_words = reinterpret_cast<const u32*>(group);
    *reinterpret_cast<u32*>(sprite + 0x4C) = group_words[3];
    *reinterpret_cast<u32*>(sprite + 0x58) = group_words[4];
    *reinterpret_cast<u32*>(sprite + 0x64) = group_words[5];
    *reinterpret_cast<u32*>(sprite + 0x70) = group_words[6];
    *reinterpret_cast<u32*>(sprite + 0x78) = group_words[7];

    sprite[0x86] = 1;
    sprite[0x87] = 1;
    sprite[0x88] = 1;
    sprite[0x89] = 1;
    sprite[0x8A] = 1;
    return reinterpret_cast<u32>(sprite + 0x8C);
}

// DECOMP_FUNC(0x002bf0a8, 152)
extern "C" void ui_func_002bf0a8(
    u8* sprite, u32 type, u32 index, u32 field_8,
    f32 scale, const u8* group, u32 panel) {
    engine_func_002c4b30(sprite, 0x8C);

    *reinterpret_cast<u32*>(sprite + 0x00) = type;
    *reinterpret_cast<u32*>(sprite + 0x04) = index;
    *reinterpret_cast<u32*>(sprite + 0x08) = field_8;
    *reinterpret_cast<f32*>(sprite + 0x20) = scale;
    *reinterpret_cast<u16*>(sprite + 0x38) = static_cast<u16>(panel);
    *reinterpret_cast<f32*>(sprite + 0x24) = 1.0f;
    *reinterpret_cast<f32*>(sprite + 0x28) = 1.0f;
    *reinterpret_cast<f32*>(sprite + 0x2C) = 1.0f;

    *reinterpret_cast<u32*>(sprite + 0x48) = reinterpret_cast<u32>(group);
    const u32* const group_words = reinterpret_cast<const u32*>(group);
    *reinterpret_cast<u32*>(sprite + 0x4C) = group_words[3];
    *reinterpret_cast<u32*>(sprite + 0x58) = group_words[4];
    *reinterpret_cast<u32*>(sprite + 0x64) = group_words[5];
    *reinterpret_cast<u32*>(sprite + 0x70) = group_words[6];
    *reinterpret_cast<u32*>(sprite + 0x78) = group_words[7];

    sprite[0x86] = 1;
    sprite[0x87] = 1;
    sprite[0x88] = 1;
    sprite[0x89] = 1;
    sprite[0x8A] = 1;
}

// DECOMP_FUNC(0x002c25f4, 144)
extern "C" void engine_func_002c25f4() {
    auto* const r4 = *reinterpret_cast<u8* const*>(0x004C6290u + 0x9C);
    if (r4 == nullptr) {
        return;
    }
    const u32 f4 = *reinterpret_cast<const u32*>(r4 + 4);
    auto* const f18 = *reinterpret_cast<volatile u8* const*>(r4 + 0x18);
    if (f4 == 0 && f18 == nullptr) {
        return;
    }

    const u32 f20 = *reinterpret_cast<const u32*>(r4 + 0x20);
    engine_func_002c4b30(f18, f20 * 28u);

    *reinterpret_cast<u32*>(r4 + 0x0C) = 0;
    *reinterpret_cast<u32*>(r4 + 0x10) = 0;
    *reinterpret_cast<u32*>(r4 + 0x20) = 0;
    *reinterpret_cast<u32*>(r4 + 0x28) = 0;
    *reinterpret_cast<u32*>(r4 + 0x14) = 0;
    *reinterpret_cast<u32*>(r4 + 0x24) = 0;
    *reinterpret_cast<u32*>(r4 + 0x34) = 0;
    *reinterpret_cast<u32*>(r4 + 0x30) = 0;

    *reinterpret_cast<u32*>(0x004652A0u) = f4;
    const u32 f8 = *reinterpret_cast<const u32*>(r4 + 8);
    *reinterpret_cast<u32*>(0x004652A4u) = f4 + f8;
}

// DECOMP_FUNC(0x002c3734, 128)
extern "C" void battle_func_00119670(
    void* r0,
    void* r1,
    u32 r2,
    u32 r3,
    float s0,
    float s1,
    float s2,
    float s3,
    float s4,
    u32 stack_param
);

extern "C" void engine_func_002c3734(u32 mode, u32 param) {
    u8* const base = reinterpret_cast<u8*>(0x004E39E0u);
    u8* sub_r0;
    u32 r3_idx = 0;

    if (mode == 0) {
        sub_r0 = base + 0x88;
    } else if (mode == 1) {
        sub_r0 = base + 0xC4;
    } else if (mode == 2) {
        if (*reinterpret_cast<const u32*>(base + 0x84) == 1) {
            return;
        }
        r3_idx = 1;
        sub_r0 = base + 0x100;
    } else {
        return;
    }

    const float* const vec = reinterpret_cast<const float*>(base + (r3_idx * 16) + 0x174);
    const float s3 = *reinterpret_cast<const float*>(base + (r3_idx * 16) + 0x180);
    const u32 r2_val = *reinterpret_cast<const u32*>(base + (r3_idx * 4) + 0x1B0);
    const float s4 = *reinterpret_cast<const float*>(base + (r3_idx * 4) + 0x1A4);

    battle_func_00119670(
        sub_r0,
        sub_r0 + 0x18,
        r2_val,
        7,
        vec[0],
        vec[1],
        vec[2],
        s3,
        s4,
        param
    );
}

// DECOMP_FUNC(0x002c854c, 136)
extern "C" u32 battle_func_002c854c(const void* obj) {
    void* const inner = *reinterpret_cast<void* const*>(static_cast<const u8*>(obj) + 8);
    if (battle_func_002bf41c(reinterpret_cast<uintptr_t>(inner)) == 0) {
        return 1;
    }

    auto* const p_5d30 = *reinterpret_cast<u8* const*>(0x00435D30u);
    if (p_5d30 == nullptr) {
        return 1;
    }
    auto* const p_4290 = *reinterpret_cast<u8* const*>(0x00434290u);
    if (p_4290 == nullptr) {
        return 1;
    }
    auto* const p_5d18 = *reinterpret_cast<u8* const*>(0x00435D18u);
    if (p_5d18 == nullptr) {
        return 1;
    }
    auto* const p_42c8 = *reinterpret_cast<u8* const*>(0x004342C8u);
    if (p_42c8 == nullptr) {
        return 1;
    }

    const u32 flag_state = *reinterpret_cast<const u32*>(p_42c8 + 0x634);
    if ((flag_state & 0x80000u) != 0) {
        return 0;
    }

    const u32 ui_flag = *reinterpret_cast<const u32*>(p_5d30 + 0xC);
    if ((ui_flag & 4u) == 0) {
        return 0;
    }

    return 1;
}

// DECOMP_FUNC(0x002c8750, 128)
extern "C" __attribute__((minsize)) void script_vm_func_002c8750() {
    auto* const base = *reinterpret_cast<u8* const*>(0x00447600u);
    for (u32 i = 0; i < 32; ++i) {
        auto* const elem = base + i * 384u + 0x34u;
        if (*elem == 0) {
            continue;
        }

        const u32 val = *reinterpret_cast<const u32*>(elem + 0x174u);
        if (val == 0 || val >= 11) {
            continue;
        }

        if (*reinterpret_cast<const u8*>(elem + 0x7Du) != 0) {
            continue;
        }

        const u32 state = *reinterpret_cast<const u32*>(elem + 0x84u);
        if (state == 0 || state == 4 || state == 5) {
            *reinterpret_cast<u32*>(elem + 0x84u) = 1;
            *reinterpret_cast<u32*>(elem + 0x88u) = 0;
        }
    }
}

// DECOMP_FUNC(0x002c8a78, 148)
extern "C" void func_00152af8(void*);

extern "C" void script_vm_func_002c8a78() {
    auto* const base = *reinterpret_cast<u8* const*>(0x00447E10u);

    for (s32 i = 8; i >= 0; --i) {
        auto* const slot = base + (i * 44) + 0x1114;
        if (slot[0] != 0) {
            void* const item = *reinterpret_cast<void* const*>(slot + 0x20);
            if (item != nullptr) {
                func_00152af8(item);
                slot[0x24] = 0;
            }
        }
    }

    for (s32 i = 2; i >= 0; --i) {
        auto* const slot = base + (i * 44) + 0x12A0;
        if (slot[0] != 0) {
            void* const item = *reinterpret_cast<void* const*>(slot + 0x20);
            if (item != nullptr) {
                func_00152af8(item);
                slot[0x24] = 0;
            }
        }
    }
}

// DECOMP_FUNC(0x002cf6d4, 128)
extern "C" void script_vm_func_002509d8();
extern "C" s32 camp_func_0029f260(void* slot);
extern "C" s32 camp_func_0029f248(void* slot);
extern "C" void script_vm_func_002900b0(u16 id, u32 mode);
extern "C" void camp_func_002bdac0(void* entity, u32 p1, u32 p2);

extern "C" void script_vm_func_002cf6d4() {
    auto* const ctx = *reinterpret_cast<u8* const*>(0x0043DD50u);
    ctx[0x5C4] = 1;
    script_vm_func_002509d8();

    auto* const slot = ctx + 0x5FC;
    const s32 q1 = camp_func_0029f260(slot);
    const s32 q2 = camp_func_0029f248(slot);
    const u32 sum = static_cast<u32>(q1 + q2);

    const u16 id = *reinterpret_cast<const u16*>(ctx + 0x6C4 + sum * 2);
    script_vm_func_002900b0(id, 1);
    camp_func_002bdac0(ctx + 0x34, 0, 0);

    auto* const ctx2 = *reinterpret_cast<u8* const*>(0x0043DD50u);
    *reinterpret_cast<u32*>(ctx2 + 8) = *reinterpret_cast<const u32*>(ctx2 + 4);
    *reinterpret_cast<u32*>(ctx2 + 4) = 1;
    *reinterpret_cast<u32*>(ctx2 + 0x10) = 0;
}

// DECOMP_FUNC(0x002cfc60, 128)
extern "C" u32 engine_func_00259510(u32);
extern "C" void engine_func_002bf86c(void* buf, u32 id);
extern "C" void engine_func_003db484(void* context, const void* buf);

extern "C" __attribute__((minsize)) u32 engine_func_002cfc60() {
    u32 stack_buf[16];
    #pragma unroll
    for (int i = 0; i < 16; ++i) {
        stack_buf[i] = 0;
    }
    const u32 id = engine_func_00259510(0);
    engine_func_002bf86c(stack_buf, id);

    void* const ctx = *reinterpret_cast<void* const*>(0x00435D18u);
    engine_func_003db484(ctx, stack_buf);
    return 1;
}

// DECOMP_FUNC(0x002d0400, 152)
extern "C" u32 camp_func_0029909c(u16 id);
extern "C" void* func_002b6700(u16 id);

extern "C" s32 script_vm_func_002d0400(const u16* a, const u16* b) {
    const u32 fa = camp_func_0029909c(*a);
    const u32 fb = camp_func_0029909c(*b);

    s32 diff = 0;
    if ((fa & ~fb) != 0) {
        diff = 1;
    }
    if ((fb & ~fa) != 0) {
        diff = -1;
    }
    if (diff != 0) {
        return diff;
    }

    auto* const ra = static_cast<const u8*>(func_002b6700(*a));
    auto* const rb = static_cast<const u8*>(func_002b6700(*b));
    if (ra == nullptr || rb == nullptr) {
        return 0;
    }

    const s32 pa = *reinterpret_cast<const u16*>(ra + 4);
    const s32 pb = *reinterpret_cast<const u16*>(rb + 4);
    return pb - pa;
}

extern "C" s32 script_vm_func_002d0474(const u8* a, const u8* b) {
    const s32 d0 = static_cast<s32>(a[0]) - static_cast<s32>(b[0]);
    if (d0 != 0) {
        return d0;
    }
    return static_cast<s32>(a[1]) - static_cast<s32>(b[1]);
}

// DECOMP_FUNC(0x002d54c4, 128)
extern "C" u32 func_002b2530(void* ptr);

extern "C" u32 func_002d54c4(void) {
    u8* r4 = *reinterpret_cast<u8**>(0x00432CC8);
    if (r4 == nullptr) {
        return 0;
    }
    void* p = *reinterpret_cast<void**>(r4);
    if (func_002b2530(p) != 0) {
        return 1;
    }
    if (r4[5] == 0) {
        return 1;
    }
    return 0;
}

// DECOMP_FUNC(0x002d5780, 136)
extern "C" void script_vm_func_0029bdb4(void*, float);
extern "C" void script_vm_func_0028c8d0(void*, float);

extern "C" void script_vm_func_002d5780(void* obj, float volume_scale) {
    auto* const inner = *reinterpret_cast<u8* const*>(static_cast<u8*>(obj) + 8);
    script_vm_func_0029bdb4(inner, volume_scale);
    script_vm_func_0028c8d0(inner, volume_scale);

    const s32 count = *reinterpret_cast<const s32*>(inner + 0x68);
    if (count <= 0) {
        return;
    }
    *reinterpret_cast<float*>(inner + 0x80) = volume_scale;
    const float scale_factor = *reinterpret_cast<const float*>(inner + 0x74);
    const float final_vol = scale_factor * volume_scale;

    auto* const p2c = *reinterpret_cast<u8* const*>(inner + 0x2C);
    if (*reinterpret_cast<const u32*>(p2c + 0x150) == 0) {
        return;
    }
    auto* const p28 = *reinterpret_cast<u8* const*>(p2c + 0x28);
    const u32 idx = *reinterpret_cast<const u32*>(p2c + 0x154);
    const u32 stride = *reinterpret_cast<const u32*>(p28 + 0x28);
    auto* const array = *reinterpret_cast<u8* const* const*>(p28 + 0x1C);
    auto* const target = array[idx * stride];
    if (target != nullptr) {
        *reinterpret_cast<float*>(target + 0x40) = final_vol;
    }
}

// DECOMP_FUNC(0x002d782c, 144)
extern "C" void func_002d782c(u32 set_or_clear, u32 id, u32 flags) {
    u8* table_ptr = *reinterpret_cast<u8**>(0x004E3CF4);
    u32 bucket = id >> 20;
    u32 tag = id & 0x000FFFFFu;

    u8* node = *reinterpret_cast<u8**>(table_ptr + bucket * 8);
    while (node != nullptr) {
        if (*reinterpret_cast<u32*>(node + 0x24) == tag) {
            break;
        }
        node = *reinterpret_cast<u8**>(node + 0x4C);
    }

    if (node == nullptr) {
        return;
    }

    u32 mask = flags & ~0xF000000Fu;
    u32 curr_flags = *reinterpret_cast<u32*>(node + 0x1C);
    if (set_or_clear != 0) {
        curr_flags |= mask;
    } else {
        curr_flags &= ~mask;
    }
    *reinterpret_cast<u32*>(node + 0x1C) = curr_flags;

    u8* child = *reinterpret_cast<u8**>(node + 0x58);
    while (child != nullptr) {
        u32 child_id = *reinterpret_cast<u32*>(child + 0x28);
        func_002d782c(set_or_clear, child_id, flags);
        child = *reinterpret_cast<u8**>(child + 0x5C);
    }
}

// DECOMP_FUNC(0x002dba40, 148)
extern "C" u32 engine_func_00296f60(u32);
extern "C" void* ui_func_00293c98();
extern "C" void battle_func_0028df54(u32);
extern "C" s32 ui_func_002c615c(s32 num, s32 den);

extern "C" u32 ui_func_002dba40() {
    const s32 threshold = static_cast<s32>(engine_func_00296f60(0));

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const s32 curr = *reinterpret_cast<const u16*>(elem + 0x1B4);
                const s32 max_val = *reinterpret_cast<const s16*>(elem + 0x1B6);
                const s32 pct = ui_func_002c615c(curr * 100, max_val);
                if (pct <= threshold) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002e11bc, 148)
extern "C" void script_vm_func_00254c6c(void*);
extern "C" void script_vm_func_002e1180(void*, u32);

extern "C" void script_vm_func_002e11bc(void* obj, u32 flag) {
    auto* const inner = *reinterpret_cast<u8* const*>(static_cast<u8*>(obj) + 8);
    script_vm_func_00254c6c(inner);
    script_vm_func_002e1180(inner, flag);

    const s32 count = *reinterpret_cast<const s32*>(inner + 0x68);
    if (count <= 0) {
        return;
    }
    auto* const p2c = *reinterpret_cast<u8* const*>(inner + 0x2C);
    if (*reinterpret_cast<const u32*>(p2c + 0x150) == 0) {
        return;
    }
    auto* const p28 = *reinterpret_cast<u8* const*>(p2c + 0x28);
    const u32 idx = *reinterpret_cast<const u32*>(p2c + 0x154);
    const u32 stride = *reinterpret_cast<const u32*>(p28 + 0x28);
    auto* const array = *reinterpret_cast<u8* const* const*>(p28 + 0x1C);
    auto* const target = array[idx * stride];
    if (target == nullptr) {
        return;
    }

    const u32 callback = (flag == 0) ? 0x0015555Cu : 0x00151404u;
    target[0x58] = 1;
    *reinterpret_cast<u32*>(target + 0x4C) = callback;
}

// DECOMP_FUNC(0x002e3af8, 132)
extern "C" u32 engine_func_00296f60(u32);
extern "C" void* ui_func_00293c98();
extern "C" void battle_func_0028df54(u32);

extern "C" u32 battle_func_002e3af8() {
    const u32 shift = engine_func_00296f60(0);
    const u32 bitmask = 1u << shift;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 mask = *reinterpret_cast<const u16*>(elem + 0x1C6);
                if ((mask & bitmask) != 0) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002eb59c, 152)
extern "C" void script_vm_func_002711e0(void*);

extern "C" void script_vm_func_002eb59c() {
    auto* const g_sys = reinterpret_cast<u8*>(0x0049F91Cu);
    auto* const r4 = *reinterpret_cast<u8* const*>(0x00447E28u);

    if (g_sys[0x284] != 0) {
        g_sys[0x284] = 0;
        return;
    }

    script_vm_func_002711e0(g_sys + 0x94);
    g_sys[0x2F8] = 1;
    *reinterpret_cast<u32*>(g_sys + 0x2FC) = *reinterpret_cast<const u32*>(r4 + 0x2C);
    *reinterpret_cast<u32*>(g_sys + 0x300) = *reinterpret_cast<const u32*>(r4 + 0x30);
    *reinterpret_cast<u32*>(g_sys + 0x304) = *reinterpret_cast<const u32*>(g_sys + 0x8);

    const float f1 = *reinterpret_cast<const float*>(g_sys + 0x94);
    const float f2 = *reinterpret_cast<const float*>(g_sys + 0x98);
    const float f3 = *reinterpret_cast<const float*>(g_sys + 0x9C);
    *reinterpret_cast<float*>(g_sys + 0x308) = f1;
    *reinterpret_cast<float*>(g_sys + 0x30C) = f2;
    *reinterpret_cast<float*>(g_sys + 0x310) = f3;

    const float s0 = *reinterpret_cast<const float*>(g_sys + 0x90);
    *reinterpret_cast<float*>(g_sys + 0x314) = s0;
    *reinterpret_cast<float*>(g_sys + 0x318) = s0;

    const float r4_2c = *reinterpret_cast<const float*>(r4 + 0x2C);
    const float r4_30 = *reinterpret_cast<const float*>(r4 + 0x30);
    *reinterpret_cast<float*>(g_sys + 0x31C) = r4_2c;
    *reinterpret_cast<float*>(g_sys + 0x320) = r4_30;

    *reinterpret_cast<float*>(g_sys + 0x330) = s0;
    *reinterpret_cast<float*>(g_sys + 0x334) = s0;

    *reinterpret_cast<float*>(g_sys + 0x324) = f1;
    *reinterpret_cast<float*>(g_sys + 0x328) = f2;
    *reinterpret_cast<float*>(g_sys + 0x32C) = f3;
}

// DECOMP_FUNC(0x002ed47c, 144)
extern "C" u32 engine_func_00286880();
extern "C" u32 engine_func_0028686c();
extern "C" u32 engine_func_00286928(u32, u32, u32, u32, u32, u32);
extern "C" void battle_func_002b8574(u32);

extern "C" u32 engine_func_002ed47c() {
    auto* const ptr_block = *reinterpret_cast<u8* const*>(0x0043E188u + 4);
    u32 r5 = engine_func_00286880();
    if (r5 == 0x14) {
        r5 = 5;
    }
    const u32 r7 = engine_func_0028686c();
    const u32 r6 = engine_func_00296f60(0);
    const u32 r2 = engine_func_00289640();
    r5 = engine_func_00286928(r7, r6, r2, r5, 0, 0);

    if (engine_func_00289640() == 0) {
        battle_func_002b8574(*reinterpret_cast<const u32*>(ptr_block + 4));
        *reinterpret_cast<u8*>(ptr_block + 0xA10) = 0;
        *reinterpret_cast<u32*>(ptr_block + 0xC) |= 0x20u;
    }

    return r5;
}

// DECOMP_FUNC(0x002f02b8, 132)
extern "C" u32 engine_func_00296f60(u32);
extern "C" void* ui_func_00293c98();
extern "C" void battle_func_0028df54(u32);

extern "C" u32 battle_func_002f02b8() {
    const u32 shift = engine_func_00296f60(0);
    const u32 bitmask = 1u << shift;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 mask = *reinterpret_cast<const u16*>(elem + 0x1C6);
                if ((mask & bitmask) != 0) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002f033c, 148)
extern "C" s32 ui_func_002c615c(s32 num, s32 den);

extern "C" u32 ui_func_002f033c() {
    const s32 threshold = static_cast<s32>(engine_func_00296f60(0));

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const s32 curr = *reinterpret_cast<const u16*>(elem + 0x1B4);
                const s32 max_val = *reinterpret_cast<const s16*>(elem + 0x1B6);
                const s32 pct = ui_func_002c615c(curr * 100, max_val);
                if (pct >= threshold) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002f0520, 140)
extern "C" u32 ui_func_002f0520() {
    const s32 threshold = static_cast<s32>(engine_func_00296f60(0));
    s32 sum = 0;
    s32 count = 0;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                count += 1;
                sum += *reinterpret_cast<const u16*>(elem + 0x1CC);
            }
        }
    }

    const s32 avg = ui_func_002c615c(sum, count);
    battle_func_0028df54(threshold <= avg ? 1 : 0);
    return 1;
}

// DECOMP_FUNC(0x002f05ac, 136)
extern "C" u32 battle_func_002f05ac() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val >> 10) == 2) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002f10dc, 132)
extern "C" u32 engine_func_00289640();
extern "C" void script_vm_func_003c8148(void* mgr, void* ctx);
extern "C" void script_vm_func_003c7eac(void* mgr);
extern "C" void engine_func_0027e9d0(void* mgr);

extern "C" u32 engine_func_002f10dc() {
    auto* const ctx = static_cast<u8*>(ui_func_00293c98());
    const u32 p0 = engine_func_00296f60(0);
    const u32 p1 = engine_func_00296f60(1);

    if (engine_func_00289640() != 0) {
        auto* const mgr = *reinterpret_cast<u8* const*>(0x004398D4u);
        const u32 val = *reinterpret_cast<const u32*>(mgr + 0x80);
        return val == 4 ? 1 : 0;
    }

    auto* const mgr = *reinterpret_cast<u8* const*>(0x004398D4u);
    script_vm_func_003c8148(mgr, ctx);

    *reinterpret_cast<u32*>(ctx + 0x13C) = p0;
    *reinterpret_cast<u32*>(ctx + 0x140) = p1;

    auto* const mgr2 = *reinterpret_cast<u8* const*>(0x004398D4u);
    script_vm_func_003c7eac(mgr2);

    auto* const mgr3 = *reinterpret_cast<u8* const*>(0x004398D4u);
    engine_func_0027e9d0(mgr3);

    return 0;
}

// DECOMP_FUNC(0x002f2878, 128)
extern "C" u32 camp_func_0029ed08(u16 id);

extern "C" __attribute__((minsize)) s32 camp_func_002f2878(const u16* a, const u16* b) {
    const u32 flags_a = camp_func_0029ed08(*a);
    const u32 flags_b = camp_func_0029ed08(*b);

    if ((flags_b & ~flags_a) != 0) {
        return 1;
    }
    if ((flags_a & ~flags_b) != 0) {
        return -1;
    }

    const u8* const rec_a = camp_func_002b9364(*a);
    const u8* const rec_b = camp_func_002b9364(*b);

    const s32 diff2 = static_cast<s32>(rec_b[2]) - static_cast<s32>(rec_a[2]);
    if (diff2 != 0) {
        return diff2;
    }

    const s32 diff3 = static_cast<s32>(rec_a[3]) - static_cast<s32>(rec_b[3]);
    if (diff3 != 0) {
        return diff3;
    }

    return static_cast<s32>(*reinterpret_cast<const u16*>(rec_b)) -
           static_cast<s32>(*reinterpret_cast<const u16*>(rec_a));
}

// DECOMP_FUNC(0x002f6cf0, 148)
extern "C" u32 ui_func_002f6cf0() {
    const s32 threshold = static_cast<s32>(engine_func_00296f60(0));
    s32 sum_max = 0;
    s32 sum_curr = 0;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                sum_max += *reinterpret_cast<const s16*>(elem + 0x1B6);
                sum_curr += *reinterpret_cast<const s16*>(elem + 0x1B4);
            }
        }
    }

    const s32 pct = ui_func_002c615c(sum_curr * 100, sum_max);
    battle_func_0028df54(pct <= threshold ? 1 : 0);
    return 1;
}

// DECOMP_FUNC(0x002f6f08, 136)
extern "C" u32 battle_func_002f6f08() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val >> 10) == 1) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002f6f90, 140)
extern "C" u32 battle_func_002f6f90() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val & 0xFC00u) != 0 && (val >> 10) == 2) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002fb4c0, 140)
extern "C" u32 engine_func_00289640();
extern "C" void battle_func_0028df3c(s32);
extern "C" void battle_func_0028df0c(u32);
extern "C" void script_vm_func_0027605c();
extern "C" void script_vm_func_00270298(u32);
extern "C" void battle_func_002b91c4(u32);

extern "C" u32 script_vm_func_002fb4c0() {
    if (engine_func_00289640() == 0) {
        battle_func_0028df3c(1);
        script_vm_func_0027605c();
        script_vm_func_00270298(3);
        return 0;
    }
    if (engine_func_00289640() == 1) {
        battle_func_002b91c4(0x01000184);
        script_vm_func_00270298(1);
        return 0;
    }
    if (static_cast<s32>(engine_func_00289640()) < 3) {
        return 0;
    }
    battle_func_0028df3c(-1);
    battle_func_0028df0c(0);
    return 1;
}

// DECOMP_FUNC(0x002fe924, 132)
extern "C" void ui_func_0025a318();
extern "C" void script_vm_func_00275a18();
extern "C" void script_vm_func_00275e38();
extern "C" void script_vm_func_00289ae8();
extern "C" void script_vm_func_002b8b78(u32 mode);

extern "C" u32 script_vm_func_002fe924() {
    const u32 val = engine_func_00296f60(0);
    auto* const flag_ptr = reinterpret_cast<u8*>(0x0049F91Cu + 0x251u);
    const u8 flag = *flag_ptr;

    if (val != 0) {
        if (flag == 0) {
            *flag_ptr = 1;
            script_vm_func_00275e38();
            script_vm_func_00289ae8();
            script_vm_func_002b8b78(0x90);
        }
    } else {
        if (flag != 0) {
            *flag_ptr = 0;
            ui_func_0025a318();
            script_vm_func_00275a18();
        }
    }

    return 1;
}

// DECOMP_FUNC(0x002fed1c, 136)
extern "C" u32 battle_func_002fed1c() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val >> 10) == 3) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002ff050, 148)
extern "C" u32 engine_func_002ff050() {
    const u32 p0 = engine_func_00296f60(0);
    const u32 p1 = engine_func_00296f60(1);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val0 = *reinterpret_cast<const u16*>(elem + 0xCE);
                if (val0 == p0) {
                    const u16 val1 = *reinterpret_cast<const u16*>(elem + 0x1CC);
                    if (val1 >= p1) {
                        battle_func_0028df54(1);
                        return 1;
                    }
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002ff180, 136)
extern "C" u32 battle_func_002ff180() {
    const u32 index = engine_func_00296f60(0);

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 val = *reinterpret_cast<const u16*>(elem + 0x1F2 + index * 2);
                if ((val >> 10) == 4) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}

// DECOMP_FUNC(0x002ff208, 132)
extern "C" u32 battle_func_002ff208() {
    const u32 shift = engine_func_00296f60(0);
    const u32 bitmask = 1u << shift;

    for (u32 i = 0; i < 109; ++i) {
        auto* const ctx = static_cast<u8*>(ui_func_00293c98());
        auto* const table = *reinterpret_cast<u8* const*>(ctx + 0x1FC0);
        auto* const elem = table + i * 648;
        const u32 flags = *reinterpret_cast<const u32*>(elem);

        if ((flags & 0x10u) != 0 && (flags & 1u) != 0) {
            if ((flags & 0x40u) == 0) {
                const u16 mask = *reinterpret_cast<const u16*>(elem + 0x1C6);
                if ((mask & bitmask) == 0) {
                    battle_func_0028df54(1);
                    return 1;
                }
            }
        }
    }

    battle_func_0028df54(0);
    return 1;
}
