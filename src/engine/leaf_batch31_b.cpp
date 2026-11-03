#include "types.h"

// Batch 31 B: raw ARM/Thumb encodings with explicit bounded return/data tails.

// DECOMP_FUNC(0x003e4eb0, 12)
extern "C" void* func_003e4eb0(void) {
    return reinterpret_cast<void*>(0x0044E870);
}
// DECOMP_FUNC(0x003e5194, 12)
extern "C" void* func_003e5194(void) {
    return reinterpret_cast<void*>(0x00472140);
}

// DECOMP_FUNC(0x003e51a8, 12)
extern "C" void* func_003e51a8(void) {
    return reinterpret_cast<void*>(0x00472238);
}

// DECOMP_FUNC(0x003e5224, 12)
extern "C" void* func_003e5224(void) {
    return reinterpret_cast<void*>(0x004722A0);
}

// DECOMP_FUNC(0x003e6024, 12)
extern "C" void* func_003e6024(void) {
    return reinterpret_cast<void*>(0x00472030);
}

// DECOMP_FUNC(0x003e6030, 12)
extern "C" void* func_003e6030(void) {
    return reinterpret_cast<void*>(0x004732D8);
}

// DECOMP_FUNC(0x003e603c, 12)
extern "C" void* func_003e603c(void) {
    return reinterpret_cast<void*>(0x00472180);
}

// DECOMP_FUNC(0x003e6048, 12)
extern "C" void* func_003e6048(void) {
    return reinterpret_cast<void*>(0x0044E820);
}

// DECOMP_FUNC(0x003e611c, 12)
extern "C" void* func_003e611c(void) {
    return reinterpret_cast<void*>(0x00472158);
}

// DECOMP_FUNC(0x003e6128, 12)
extern "C" void* func_003e6128(void) {
    return reinterpret_cast<void*>(0x004765B0);
}

// DECOMP_FUNC(0x003e6134, 12)
extern "C" void* func_003e6134(void) {
    return reinterpret_cast<void*>(0x0044E858);
}

// DECOMP_FUNC(0x003bcfc8, 16)
extern "C" float func_003bcfc8(float val) {
    return val * 1.25f;
}

// DECOMP_FUNC(0x003409d4, 24)
extern "C" void func_003409d4(void* obj) {
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 4) = 0;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 8) = 0.0f;
}

// DECOMP_FUNC(0x00348ac0, 24)
extern "C" void func_00348ac0(void* obj) {
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 4) = 0;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 8) = 1.0f;
}

// DECOMP_FUNC(0x0035a220, 24)
extern "C" const char* script_vm_func_0035a220(u32 region_id) {
    if (region_id < 7) {
        const char* const* table = reinterpret_cast<const char* const*>(0x00465768);
        return table[region_id];
    }
    return nullptr;
}

// DECOMP_FUNC(0x0035a270, 24)
extern "C" const char* script_vm_func_0035a270(u32 lang_id) {
    if (lang_id < 12) {
        const char* const* table = reinterpret_cast<const char* const*>(0x00465728);
        return table[lang_id];
    }
    return nullptr;
}

// DECOMP_FUNC(0x00380420, 24)
extern "C" void func_00380420(void* obj) {
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x10) = 0;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x14) = 0.0f;
}

// DECOMP_FUNC(0x003f59f0, 24)
extern "C" void func_003f59f0(void) {
    u32* target = reinterpret_cast<u32*>(0x0044E918);
    target[0] = 0;
    target[1] = 0;
}

// DECOMP_FUNC(0x003f5dc8, 24)
extern "C" void func_003f5dc8(void) {
    u32* target = reinterpret_cast<u32*>(0x0044E930);
    target[0] = 0;
    target[1] = 0;
}

// DECOMP_FUNC(0x003f61d8, 24)
extern "C" void func_003f61d8(void) {
    u32* target = reinterpret_cast<u32*>(0x0044E948);
    target[0] = 0;
    target[1] = 0;
}

// DECOMP_FUNC(0x003f6b2c, 24)
extern "C" void func_003f6b2c(void) {
    u32* target = reinterpret_cast<u32*>(0x0044E990);
    target[0] = 0;
    target[1] = 0;
}

// DECOMP_FUNC(0x00379b14, 28)
extern "C" void func_00379b14(void* obj, float val) {
    if (val < 0.0f) {
        val = 0.0f;
    }
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0xB0) = val;
}

// DECOMP_FUNC(0x003f62d0, 32)
extern "C" void func_003f62d0(void) {
    u32* target = reinterpret_cast<u32*>(0x0044E960);
    target[0] = 0;
    target[1] = 0;
}

// DECOMP_FUNC(0x0033c908, 36)
extern "C" void camp_func_0033c908(void* obj) {
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x390) = 0;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x394) = 0.0f;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x398) = 0.0f;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x39C) = 0.0f;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x3A0) = 0.0f;
}

// DECOMP_FUNC(0x003954a4, 36)
extern "C" void func_003954a4(void* obj) {
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x70) &= ~1u;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x74) = 0.0f;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x78) = 0.0f;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x7C) = 0.0f;
}

// DECOMP_FUNC(0x003d6610, 36)
extern "C" void engine_func_003d6610(void* obj) {
    float* p = reinterpret_cast<float*>(static_cast<char*>(obj) + 0xC);
    for (int i = 0; i < 6; ++i) {
        p[i] = 0.0f;
    }
}

// DECOMP_FUNC(0x00302770, 40)
extern "C" void func_00302770(void* dst, const void* src) {
    const u32* s = reinterpret_cast<const u32*>(src);
    u32* d = reinterpret_cast<u32*>(static_cast<char*>(dst) + 0x20);
    d[0] = s[0];
    d[1] = s[1];
    d[2] = s[2];
    *reinterpret_cast<float*>(static_cast<char*>(dst) + 0x2C) = 1.0f;
}

// DECOMP_FUNC(0x003f65e8, 40)
extern "C" void func_003f65e8(void) {
    u32* target1 = reinterpret_cast<u32*>(0x0044E978);
    target1[0] = 0;
    target1[1] = 0;
    *reinterpret_cast<u32*>(0x004D4674 + 8) = 0xFFFFFFFF;
}

// DECOMP_FUNC(0x00376fb4, 44)
extern "C" void func_00376fb4(void* obj) {
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x18) = 0;
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x1C) = 0;
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x20) = 0;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x24) = 0.5f;
    *reinterpret_cast<u8*>(static_cast<char*>(obj) + 0x28) = 1;
    *reinterpret_cast<u8*>(static_cast<char*>(obj) + 0x29) = 0;
}

// DECOMP_FUNC(0x0037f7e0, 44)
extern "C" void* func_0037f7e0(void* obj, s32 index) {
    if (index < 16) {
        return static_cast<char*>(obj) + 0xCC + (index * 2);
    }
    if (index < 32) {
        return reinterpret_cast<char*>(0x004EA494) + ((index - 16) * 2);
    }
    return nullptr;
}

// DECOMP_FUNC(0x003f5a3c, 44)
extern "C" void* nn_sdk_func_003f5a3c(u32 a0, u32 a1) {
    u32* target = reinterpret_cast<u32*>(0x0044E918);
    target[0] = a0;
    target[1] = a1;
    return target;
}

// DECOMP_FUNC(0x003f5e08, 44)
extern "C" void* nn_sdk_func_003f5e08(u32 a0, u32 a1) {
    u32* target = reinterpret_cast<u32*>(0x0044E930);
    target[0] = a0;
    target[1] = a1;
    return target;
}

// DECOMP_FUNC(0x003f6c40, 44)
extern "C" void* nn_sdk_func_003f6c40(u32 a0, u32 a1) {
    u32* target = reinterpret_cast<u32*>(0x0044E990);
    target[0] = a0;
    target[1] = a1;
    return target;
}

// DECOMP_FUNC(0x003e0df8, 48)
extern "C" s32 func_003e0df8(const void* range, void* out) {
    const char* start = *reinterpret_cast<const char* const*>(range);
    const char* end = *reinterpret_cast<const char* const*>(static_cast<const char*>(range) + 4);
    s32 count = static_cast<s32>(end - start) >> 1;
    if (static_cast<u32>(count) <= 0x100) {
        reinterpret_cast<u32*>(out)[0] = static_cast<u32>(count);
        reinterpret_cast<const void**>(out)[1] = start;
        return 0;
    }
    return static_cast<s32>(0xE0E046C7);
}

// DECOMP_FUNC(0x003e0e7c, 48)
extern "C" s32 func_003e0e7c(const void* range, void* out) {
    const char* start = *reinterpret_cast<const char* const*>(range);
    const char* end = *reinterpret_cast<const char* const*>(static_cast<const char*>(range) + 4);
    s32 count = static_cast<s32>(end - start) >> 1;
    if (static_cast<u32>(count) <= 0x100) {
        reinterpret_cast<u32*>(out)[0] = static_cast<u32>(count);
        reinterpret_cast<const void**>(out)[1] = start;
        return 0;
    }
    return static_cast<s32>(0xE0E046C8);
}

// DECOMP_FUNC(0x003e70c8, 48)
extern "C" bool func_003e70c8(void* unused, const void* header) {
    const u32* h = reinterpret_cast<const u32*>(header);
    if (h[0] != 0x4D545343) {
        return false;
    }
    u32 ver_offset = h[2] - 0x02000000u;
    return ver_offset <= 0x10000u;
}

extern "C" void engine_func_002c3aa8(void* mutex);
extern "C" void engine_func_002c3a24(void* mutex);

// DECOMP_FUNC(0x003f6708, 48)
extern "C" u32 engine_func_003f6708(const void* src, u32* out) {
    void* mutex = reinterpret_cast<void*>(0x004D4674);
    engine_func_002c3aa8(mutex);
    *out = *reinterpret_cast<const u32*>(static_cast<const char*>(src) + 0x38);
    engine_func_002c3a24(mutex);
    return 1;
}

// DECOMP_FUNC(0x00338658, 52)
extern "C" void func_00338658(void* obj) {
    float* p = reinterpret_cast<float*>(static_cast<char*>(obj) + 0x1EA4);
    for (int i = 0; i < 6; ++i) {
        p[i] = 0.0f;
    }
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x1EBC) = 0;
}

// DECOMP_FUNC(0x003e69dc, 52)
extern "C" void* func_003e69dc(void* archive, u32 index) {
    u32 count = *reinterpret_cast<u32*>(archive);
    if (index < count) {
        const char* entry = static_cast<const char*>(archive) + (index * 8);
        u16 tag = *reinterpret_cast<const u16*>(entry + 4);
        if (tag == 0x4101) {
            u32 offset = *reinterpret_cast<const u32*>(entry + 8);
            return static_cast<char*>(archive) + offset;
        }
    }
    return nullptr;
}

// DECOMP_FUNC(0x003e6a10, 52)
extern "C" void* func_003e6a10(void* archive, u32 index) {
    u32 count = *reinterpret_cast<u32*>(archive);
    if (index < count) {
        const char* entry = static_cast<const char*>(archive) + (index * 8);
        u16 tag = *reinterpret_cast<const u16*>(entry + 4);
        if (tag == 0x4102) {
            u32 offset = *reinterpret_cast<const u32*>(entry + 8);
            return static_cast<char*>(archive) + offset;
        }
    }
    return nullptr;
}

extern "C" u32 func_002a6d94(void* obj, u32* out, u32 tag);

// DECOMP_FUNC(0x003e6af4, 52)
extern "C" u32 func_003e6af4(void* obj) {
    u32 val = 0;
    if (func_002a6d94(static_cast<char*>(obj) + 4, &val, 0) != 0) {
        if (((val >> 8) & 0xFF) == 1) {
            return 1;
        }
    }
    return 0;
}

extern "C" const u8* func_003f89f8(void* obj);

// DECOMP_FUNC(0x003f9044, 52)
extern "C" float func_003f9044(void* obj) {
    const u8* data = func_003f89f8(obj);
    u32 int_val = static_cast<u32>(data[1]) | (static_cast<u32>(data[2] & 0xF) << 8);
    float scale = *reinterpret_cast<float*>(static_cast<char*>(obj) + 8);
    float base = *reinterpret_cast<float*>(static_cast<char*>(obj) + 12);
    return base + (static_cast<float>(int_val) * scale);
}

// DECOMP_FUNC(0x003e646c, 56)
extern "C" void* func_003e646c(void* obj) {
    u32 offset = 0;
    if (func_002a6d94(obj, &offset, 9) == 0) {
        return reinterpret_cast<void*>(0x004765DD);
    }
    char* target = static_cast<char*>(obj) + offset;
    u32 inner_offset = *reinterpret_cast<u32*>(target + 4);
    return target + inner_offset;
}

extern "C" const void* Tbb_GetGlobalSubTable(u32 slot_id, u32 table_index);
extern "C" const void* Tbb_GetPayloadData(const void* table);
extern "C" u32 Tbb_GetRowCount(const void* table);

// DECOMP_FUNC(0x003ea4f8, 56)
extern "C" const void* camp_func_003ea4f8(u32 unused, u32 sub_index, u32 entry_index) {
    const void* table = Tbb_GetGlobalSubTable(0x26, sub_index * 2);
    const void* payload = Tbb_GetPayloadData(table);
    u32 row_count = Tbb_GetRowCount(table);
    if (entry_index < row_count) {
        return static_cast<const char*>(payload) + (entry_index * 32);
    }
    return nullptr;
}

// DECOMP_FUNC(0x003d71c4, 60)
extern "C" void func_003d71c4(void* obj) {
    float* v1 = reinterpret_cast<float*>(static_cast<char*>(obj) + 0x738);
    v1[0] = 0.0f;
    v1[1] = 0.0f;
    v1[2] = 0.0f;
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x634) &= ~0x00800000u;
    float* v2 = reinterpret_cast<float*>(static_cast<char*>(obj) + 0x764);
    v2[0] = 0.0f;
    v2[1] = 0.0f;
    v2[2] = 0.0f;
}

// DECOMP_FUNC(0x003d8acc, 60)
extern "C" void battle_func_003d8acc(void* obj) {
    float* v = reinterpret_cast<float*>(static_cast<char*>(obj) + 0x688);
    v[0] = 0.0f;
    v[1] = 0.0f;
    v[2] = 0.0f;
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x694) = 0;
    *reinterpret_cast<u32*>(static_cast<char*>(obj) + 0x634) |= 0x20u;
}

// DECOMP_FUNC(0x003e84f0, 60)
extern "C" void* func_003e84f0(void* obj) {
    u32 offset = 0;
    if (func_002a6d94(static_cast<char*>(obj) + 4, &offset, 9) == 0) {
        return reinterpret_cast<void*>(0x004765D8);
    }
    char* target = static_cast<char*>(obj) + offset;
    u32 inner_offset = *reinterpret_cast<u32*>(target + 4);
    return target + inner_offset;
}

extern "C" void* engine_func_00296f60(u32);
extern "C" void* ui_func_00293c98(void);
extern "C" char* ui_func_00282b94(void*, void*);
extern "C" void battle_func_0028df54(s32);

// DECOMP_FUNC(0x00300150, 64)
extern "C" u32 ui_func_00300150(void) {
    void* p = engine_func_00296f60(0);
    void* u = ui_func_00293c98();
    char* target = ui_func_00282b94(u, p);
    s32 id = 0;
    if (target != nullptr) {
        id = *reinterpret_cast<const s16*>(target + 0x1B6);
    }
    battle_func_0028df54(id);
    return 1;
}

// DECOMP_FUNC(0x0031b960, 64)
extern "C" bool camp_func_0031b960(void) {
    void* ptr = *reinterpret_cast<void**>(0x0044CDF0);
    return ptr != nullptr;
}

extern "C" void camp_func_0031b978(void) {
    char* obj = *reinterpret_cast<char**>(0x00432CC8);
    s32 count = *reinterpret_cast<s32*>(obj + 0x760) - 1;
    *reinterpret_cast<s32*>(obj + 0x760) = count;
    if (count < 0) {
        *reinterpret_cast<u32*>(obj + 0x14C) = 3;
    }
}

extern "C" u32 battle_func_002bf41c(void*);
extern "C" void battle_func_002c45b8(void*, u32);

// DECOMP_FUNC(0x0031bfcc, 64)
extern "C" void script_vm_func_0031bfcc(void) {
    void** ptr = *reinterpret_cast<void***>(0x0043E088);
    if (ptr != nullptr) {
        void* obj = *ptr;
        if (battle_func_002bf41c(obj) != 0) {
            void** ptr2 = *reinterpret_cast<void***>(0x0043E088);
            battle_func_002c45b8(*ptr2, 0);
        }
    }
}

// DECOMP_FUNC(0x00324b68, 64)
extern "C" void func_00324b68(void) {
    char* base = reinterpret_cast<char*>(0x004D8B40);
    *reinterpret_cast<u8*>(base + 0x88) = 8;
    *reinterpret_cast<u8*>(base + 0x89) = 0;
    *reinterpret_cast<u8*>(base + 0x8A) = 0;
    float* v = reinterpret_cast<float*>(base + 0x740);
    v[0] = 0.0f;
    v[1] = 0.0f;
    v[2] = 0.0f;
    v[3] = 1.0f;
}

// DECOMP_FUNC(0x00327b18, 64)
extern "C" u32 func_00327b18(void) {
    char* base = reinterpret_cast<char*>(0x004D8B40);
    float* v = reinterpret_cast<float*>(0x004D9270);
    v[0] = 0.0f;
    v[1] = 0.0f;
    v[2] = 0.0f;
    v[3] = 0.0f;
    *reinterpret_cast<u8*>(base + 0x88) = 8;
    *reinterpret_cast<u8*>(base + 0x89) = 0;
    *reinterpret_cast<u8*>(base + 0x8A) = 0;
    return 0;
}

// DECOMP_FUNC(0x00340918, 64)
extern "C" void func_00340918(void* obj, s32 a, s32 b, s32 c) {
    s32 ab = a + b;
    s32 total = ab + c;
    *reinterpret_cast<s32*>(static_cast<char*>(obj) + 0x0C) = a;
    *reinterpret_cast<s32*>(static_cast<char*>(obj) + 0x10) = ab;
    *reinterpret_cast<s32*>(static_cast<char*>(obj) + 0x14) = total;
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x18) = 1.0f / static_cast<float>(a);
    *reinterpret_cast<float*>(static_cast<char*>(obj) + 0x1C) = 1.0f / static_cast<float>(c);
}

// DECOMP_FUNC(0x00360354, 64)
extern "C" void func_00360354(void* obj, u32 id) {
    *reinterpret_cast<u32*>(obj) = id;
    float* matrix = reinterpret_cast<float*>(static_cast<char*>(obj) + 0x34);
    for (int i = 0; i < 12; ++i) {
        matrix[i] = 0.0f;
    }
}

static inline s32 sys_svcCloseHandle(u32 handle) {
    register u32 r0 asm("r0") = handle;
    asm volatile("svc 0x23" : "+r"(r0) : : "r1", "r2", "r3", "memory");
    return static_cast<s32>(r0);
}

extern "C" void engine_func_002bce48(u32);
extern "C" s32 func_00360bcc(u32* handle_out);

// DECOMP_FUNC(0x00360780, 64)
extern "C" void engine_func_00360780(u32* handle_storage) {
    u32 new_handle = 0;
    s32 res = func_00360bcc(&new_handle);
    if (res < 0) {
        engine_func_002bce48(static_cast<u32>(res));
    }
    u32 old_handle = *handle_storage;
    if (old_handle != 0) {
        sys_svcCloseHandle(old_handle);
        *handle_storage = 0;
    }
    *handle_storage = new_handle;
}

typedef float (*TimerStepCallback)(void* ctx, float a, float b, float c);

// DECOMP_FUNC(0x00368820, 64)
extern "C" void func_00368820(void* obj, float dt) {
    char* p = static_cast<char*>(obj);
    float old_val = *reinterpret_cast<float*>(p + 0x38);
    float s0 = *reinterpret_cast<float*>(p + 0x44);
    float s1 = *reinterpret_cast<float*>(p + 0x48);
    float s2 = old_val + dt;
    TimerStepCallback fn = *reinterpret_cast<TimerStepCallback*>(p + 0x4C);
    void* ctx = *reinterpret_cast<void**>(p + 0x50);
    float new_val = fn(ctx, s0, s1, s2);
    *reinterpret_cast<float*>(p + 0x3C) = old_val;
    *reinterpret_cast<float*>(p + 0x38) = new_val;
    *reinterpret_cast<u8*>(p + 0x58) = 1;
}

// DECOMP_FUNC(0x0036a25c, 64)
extern "C" void* func_0036a25c(void* obj) {
    char* p = static_cast<char*>(obj);
    u8 flag = *reinterpret_cast<u8*>(p + 8);
    *reinterpret_cast<uintptr_t*>(p) = 0x00421104;
    if (flag != 0) {
        void* inner = *reinterpret_cast<void**>(p + 0x0C);
        if (inner != nullptr) {
            void* sub_obj = *reinterpret_cast<void**>(p + 4);
            typedef void (*VirtualMethod)(void*);
            VirtualMethod* vtable = *reinterpret_cast<VirtualMethod**>(sub_obj);
            vtable[3](sub_obj);
        }
    }
    return obj;
}

// DECOMP_FUNC(0x0036ac80, 64)
extern "C" void* func_0036ac80(void* obj) {
    char* p = static_cast<char*>(obj);
    u8 flag = *reinterpret_cast<u8*>(p + 8);
    *reinterpret_cast<uintptr_t*>(p) = 0x0042114C;
    if (flag != 0) {
        void* inner = *reinterpret_cast<void**>(p + 0x0C);
        if (inner != nullptr) {
            void* sub_obj = *reinterpret_cast<void**>(p + 4);
            typedef void (*VirtualMethod)(void*);
            VirtualMethod* vtable = *reinterpret_cast<VirtualMethod**>(sub_obj);
            vtable[3](sub_obj);
        }
    }
    return obj;
}

// DECOMP_FUNC(0x0036aed4, 64)
extern "C" void* func_0036aed4(void* obj) {
    char* p = static_cast<char*>(obj);
    u8 flag = *reinterpret_cast<u8*>(p + 9);
    *reinterpret_cast<uintptr_t*>(p) = 0x00421194;
    if (flag != 0) {
        void* inner = *reinterpret_cast<void**>(p + 0x1C);
        if (inner != nullptr) {
            void* sub_obj = *reinterpret_cast<void**>(p + 4);
            typedef void (*VirtualMethod)(void*);
            VirtualMethod* vtable = *reinterpret_cast<VirtualMethod**>(sub_obj);
            vtable[3](sub_obj);
        }
    }
    return obj;
}

// DECOMP_FUNC(0x0036b570, 64)
extern "C" void* func_0036b570(void* obj) {
    char* p = static_cast<char*>(obj);
    u8 flag = *reinterpret_cast<u8*>(p + 8);
    *reinterpret_cast<uintptr_t*>(p) = 0x004211F4;
    if (flag != 0) {
        void* inner = *reinterpret_cast<void**>(p + 0x0C);
        if (inner != nullptr) {
            void* sub_obj = *reinterpret_cast<void**>(p + 4);
            typedef void (*VirtualMethod)(void*);
            VirtualMethod* vtable = *reinterpret_cast<VirtualMethod**>(sub_obj);
            vtable[3](sub_obj);
        }
    }
    return obj;
}

extern "C" void func_0037da70(void*, u32);
extern "C" void func_002358dc(void*);

// DECOMP_FUNC(0x0036d03c, 64)
extern "C" void* func_0036d03c(void* obj) {
    char* p = static_cast<char*>(obj);
    u8 flag = *reinterpret_cast<u8*>(p + 9);
    *reinterpret_cast<uintptr_t*>(p) = 0x00421244;
    if (flag != 0) {
        void* inner = *reinterpret_cast<void**>(p + 0x1C);
        if (inner != nullptr) {
            void* sub_obj = *reinterpret_cast<void**>(p + 4);
            typedef void (*VirtualMethod)(void*);
            VirtualMethod* vtable = *reinterpret_cast<VirtualMethod**>(sub_obj);
            vtable[3](sub_obj);
        }
    }
    return obj;
}

// DECOMP_FUNC(0x0036e2b8, 64)
extern "C" void* func_0036e2b8(void* obj) {
    char* p = static_cast<char*>(obj);
    u8 flag = *reinterpret_cast<u8*>(p + 9);
    *reinterpret_cast<uintptr_t*>(p) = 0x00421304;
    if (flag != 0) {
        void* inner = *reinterpret_cast<void**>(p + 0x1C);
        if (inner != nullptr) {
            void* sub_obj = *reinterpret_cast<void**>(p + 4);
            typedef void (*VirtualMethod)(void*);
            VirtualMethod* vtable = *reinterpret_cast<VirtualMethod**>(sub_obj);
            vtable[3](sub_obj);
        }
    }
    return obj;
}

// DECOMP_FUNC(0x0036f338, 64)
extern "C" void func_0036f338(void* holder) {
    void* target = *reinterpret_cast<void**>(holder);
    char* p = static_cast<char*>(target);
    u32 cond = *reinterpret_cast<u32*>(p + 4);
    if (cond == 0) {
        return;
    }
    u32 magic = *reinterpret_cast<u32*>(p);
    typedef void (*HandlerFn)(void*);
    HandlerFn* table = reinterpret_cast<HandlerFn*>(0x0044E8F0);
    if (magic == 0x80000000) {
        table[0](target);
    } else if (magic == 0x40000000) {
        table[1](target);
    }
}

// DECOMP_FUNC(0x0037f880, 64)
extern "C" void func_0037f880(void* obj, u32 val) {
    char* p = static_cast<char*>(obj);
    *reinterpret_cast<u8*>(p + 0x0E) = static_cast<u8>(val);
    void** children = reinterpret_cast<void**>(p + 0x8C);
    for (int i = 0; i < 16; ++i) {
        void* child = children[i];
        if (child != nullptr) {
            func_0037da70(child, val);
        }
    }
}

// DECOMP_FUNC(0x00380c70, 64)
extern "C" u32 func_00380c70(void* obj) {
    char* p = static_cast<char*>(obj);
    func_002358dc(p);
    u32 flags = *reinterpret_cast<u32*>(p + 0x0C);
    if ((flags & 1) != 0) {
        return *reinterpret_cast<u32*>(p + 0x10);
    }
    u32 idx = (flags & 0x38) >> 3;
    typedef u32 (*DispatchFn)(void*);
    DispatchFn* table = reinterpret_cast<DispatchFn*>(0x00471C20);
    return table[idx](p + 0x10);
}

// DECOMP_FUNC(0x003aaef0, 64)
extern "C" void camp_func_003aaef0(void) {
    char* target = *reinterpret_cast<char**>(0x0043D9E4);
    *reinterpret_cast<u8*>(target + 0x1D) = 4;
}

extern "C" u32 camp_func_003aaf08(void) {
    void** p = *reinterpret_cast<void***>(0x0043D9C8);
    void* sub_obj = *p;
    typedef void (*VirtualMethod)(void*);
    VirtualMethod* vtable = *reinterpret_cast<VirtualMethod**>(sub_obj);
    vtable[3](sub_obj);
    return 0;
}

extern "C" void* ui_func_00357a28(u32);
extern "C" u32 engine_func_0022af30(void*, void*);
extern "C" u32 func_002d5508(void*);

// DECOMP_FUNC(0x003bbed4, 64)
extern "C" u32 ui_func_003bbed4(void) {
    void* p = ui_func_00357a28(0x0E5C);
    void* ctx = *reinterpret_cast<void**>(0x0043DDB8);
    if (engine_func_0022af30(p, ctx) == 0) {
        return 0;
    }
    void* p2 = ui_func_00357a28(0x0E5C);
    return func_002d5508(p2);
}

// DECOMP_FUNC(0x003e68bc, 64)
extern "C" void* func_003e68bc(void* archive) {
    char* p = static_cast<char*>(archive);
    const u16 tag = 0x4002;
    char* entry = nullptr;
    if (*reinterpret_cast<u16*>(p + 0x14) == tag) {
        entry = p + 0x14;
    } else if (*reinterpret_cast<u16*>(p + 0x20) == tag) {
        entry = p + 0x20;
    } else if (*reinterpret_cast<u16*>(p + 0x2C) == tag) {
        entry = p + 0x2C;
    }
    return *reinterpret_cast<void**>(entry + 4);
}

// DECOMP_FUNC(0x003e6934, 64)
extern "C" void* func_003e6934(void* archive) {
    char* p = static_cast<char*>(archive);
    const u16 tag = 0x4001;
    char* entry = nullptr;
    if (*reinterpret_cast<u16*>(p + 0x14) == tag) {
        entry = p + 0x14;
    } else if (*reinterpret_cast<u16*>(p + 0x20) == tag) {
        entry = p + 0x20;
    } else if (*reinterpret_cast<u16*>(p + 0x2C) == tag) {
        entry = p + 0x2C;
    }
    return *reinterpret_cast<void**>(entry + 4);
}

// DECOMP_FUNC(0x003f6228, 64)
extern "C" void func_003f6228(void* obj) {
    typedef void (*CallbackFn)(void*);
    CallbackFn* cb_ptr = reinterpret_cast<CallbackFn*>(0x0044E948 + 4);
    CallbackFn cb = *cb_ptr;
    if (cb == nullptr || obj == nullptr) {
        return;
    }
    void* sub_obj = *reinterpret_cast<void**>(static_cast<char*>(obj) + 4);
    if (sub_obj != nullptr) {
        cb(sub_obj);
    }
    cb = *cb_ptr;
    cb(obj);
}

// DECOMP_FUNC(0x003f6368, 64)
extern "C" __attribute__((naked)) void func_003f6368() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe59f5030\n"
        ".inst 0xe5951004\n"
        ".inst 0xe3510000\n"
        ".inst 0x13500000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900010\n"
        ".inst 0xe3500000\n"
        ".inst 0x112fff31\n"
        ".inst 0xe5951004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe12fff11\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044e960 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00341c04, 68)
extern "C" __attribute__((naked)) void engine_func_00341c04() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd080\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a02001\n"
        ".inst 0xe28f1024\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xfafdf2f6\n"
        ".inst 0xe3a01007\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfd686b\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe5840028\n"
        ".inst 0xebfd7aa3\n"
        ".inst 0xe28dd080\n"
        ".inst 0xe8bd8010\n"
        ".word 0x622e7325 @ bounded tail data\n"
        ".word 0x00006d61 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00351e24, 68)
extern "C" __attribute__((naked)) void engine_func_00351e24() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe1a04001\n"
        ".inst 0xebfdd061\n"
        ".inst 0xeb0020d9\n"
        ".inst 0xe1a05000\n"
        ".inst 0xebf7d21e\n"
        ".inst 0xe3550000\n"
        ".inst 0x059f0018\n"
        ".inst 0x0a000003\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe1a00006\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xea000026\n"
        ".inst 0xe8bd8070\n"
        ".word 0xe0409fff @ bounded tail data\n"
        ".word 0xc9209f84 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00362374, 68)
extern "C" __attribute__((naked)) void func_00362374() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2804010\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5900014\n"
        ".inst 0xe5840008\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x15941004\n"
        ".inst 0x13510000\n"
        ".inst 0x0a000002\n"
        ".inst 0xe5902000\n"
        ".inst 0xe592200c\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe2440010\n"
        ".inst 0xe8bd8010\n"
        ".word 0x00420c4c @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00376c88, 68)
extern "C" __attribute__((naked)) void func_00376c88() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a06000\n"
        ".inst 0xe5914004\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe3540000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe1a00004\n"
        ".inst 0xeb000c8a\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe1a00005\n"
        ".inst 0xeb000b91\n"
        ".inst 0xe2860018\n"
        ".inst 0xe286101c\n"
        ".inst 0xe2842018\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xeafd22aa\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00377924, 68)
extern "C" __attribute__((naked)) void func_00377924() {
    asm volatile(
        ".arm\n"
        ".inst 0xedd11a13\n"
        ".inst 0xeddf0a0d\n"
        ".inst 0xed911a17\n"
        ".inst 0xeeb40ae1\n"
        ".inst 0xeef1fa10\n"
        ".inst 0xda000007\n"
        ".inst 0xee300a61\n"
        ".inst 0xedd10a14\n"
        ".inst 0xed912a16\n"
        ".inst 0xeec01a20\n"
        ".inst 0xee610a82\n"
        ".inst 0xeef40ac1\n"
        ".inst 0xeef1fa10\n"
        ".inst 0xcef00a41\n"
        ".inst 0xedc30a00\n"
        ".inst 0xe12fff1e\n"
        ".word 0x00000000 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0038e480, 68)
extern "C" __attribute__((naked)) void func_0038e480() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2800088\n"
        ".inst 0xebfcb1e4\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafc901c\n"
        ".inst 0x00421ee0\n"
        ".inst 0x00432fc8\n"
        ".inst 0xe1d000b0\n"
        ".inst 0xe1d110b0\n"
        ".inst 0xe0400001\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003bbd74, 68)
extern "C" __attribute__((naked)) void engine_func_003bbd74() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xebf98dad\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000009\n"
        ".inst 0xe284000c\n"
        ".inst 0xebfce4a2\n"
        ".inst 0xe1a01005\n"
        ".inst 0xebfcbee1\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a000003\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe3a00000\n"
        ".inst 0xeafcbedb\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003e46a4, 68)
extern "C" __attribute__((naked)) void func_003e46a4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe2814030\n"
        ".inst 0xed910a0c\n"
        ".inst 0xebfb1e82\n"
        ".inst 0xed840a00\n"
        ".inst 0xed940a01\n"
        ".inst 0xebfb1e7f\n"
        ".inst 0xed840a01\n"
        ".inst 0xed940a02\n"
        ".inst 0xebfb1e7c\n"
        ".inst 0xed840a02\n"
        ".inst 0xe595003c\n"
        ".inst 0xe3800b02\n"
        ".inst 0xe585003c\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003f6318, 68)
extern "C" __attribute__((naked)) void nn_sdk_func_003f6318() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4030\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe24dd00c\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe1a00000\n"
        ".inst 0xe28d2008\n"
        ".inst 0xe28d1004\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebf6256b\n"
        ".inst 0xe59f000c\n"
        ".inst 0xe1c040f0\n"
        ".inst 0xe28dd00c\n"
        ".inst 0xe8bd8030\n"
        ".word 0x040000a9 @ bounded tail data\n"
        ".word 0x0044e960 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003f752c, 68)
extern "C" __attribute__((naked)) void func_003f752c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe5900010\n"
        ".inst 0xeafb3343\n"
        ".inst 0xe2801020\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe5802000\n"
        ".inst 0xe5801008\n"
        ".inst 0xe590100c\n"
        ".inst 0xe3a01106\n"
        ".inst 0xe580100c\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe2801004\n"
        ".inst 0xe3a02000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe5802000\n"
        ".inst 0xe5801008\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00355f78, 72)
extern "C" __attribute__((naked)) void ui_func_00355f78() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4038\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe1b00001\n"
        ".inst 0xe1a02003\n"
        ".inst 0xe59d3010\n"
        ".inst 0x059f0028\n"
        ".inst 0x0a000008\n"
        ".inst 0xe5901000\n"
        ".inst 0xe591c000\n"
        ".inst 0xe1a0100d\n"
        ".inst 0xe12fff3c\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x1a000002\n"
        ".inst 0xe59d0000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8038\n"
        ".word 0xc8804465 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0037c424, 72)
extern "C" __attribute__((naked)) void func_0037c424() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe5900040\n"
        ".inst 0xe3500001\n"
        ".inst 0x0a00000b\n"
        ".inst 0xe5950008\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe3500000\n"
        ".inst 0xda000007\n"
        ".inst 0xe7950104\n"
        ".inst 0xe3500000\n"
        ".inst 0x15951040\n"
        ".inst 0x1bff8fb1\n"
        ".inst 0xe5950008\n"
        ".inst 0xe2844001\n"
        ".inst 0xe1500004\n"
        ".inst 0xcafffff7\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x00324010, 76)
extern "C" __attribute__((naked)) void engine_func_00324010() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe92d4010\n"
        ".inst 0xebfdcbd0\n"
        ".inst 0xe1b04000\n"
        ".inst 0x03a00001\n"
        ".inst 0x0a000007\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000005\n"
        ".inst 0xebfe77bb\n"
        ".inst 0xe3500000\n"
        ".inst 0x15940004\n"
        ".inst 0x1bfbf6cc\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".inst 0xe1a00004\n"
        ".inst 0xebfe80c2\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x00351b7c, 76)
extern "C" __attribute__((naked)) void nn_sdk_func_00351b7c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe59f0038\n"
        ".inst 0xe92d4010\n"
        ".inst 0xeb003a9e\n"
        ".inst 0xe3a00001\n"
        ".inst 0xeb003b11\n"
        ".inst 0xe59f0028\n"
        ".inst 0xeb003af8\n"
        ".inst 0xe59f0020\n"
        ".inst 0xe5900000\n"
        ".inst 0xef000019\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x0a000001\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafdce2b\n"
        ".inst 0xe8bd8010\n"
        ".word 0x004092a0 @ bounded tail data\n"
        ".word 0x00471bac @ bounded tail data\n"
        ".word 0x0044e9e8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00353160, 76)
extern "C" __attribute__((naked)) void func_00353160() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4008\n"
        ".inst 0xe1a02000\n"
        ".inst 0xe1a03001\n"
        ".inst 0xe3a01001\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfffc97\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe1500001\n"
        ".inst 0x03a00000\n"
        ".inst 0x0a000005\n"
        ".inst 0xe1b01fa0\n"
        ".inst 0x1a000003\n"
        ".inst 0xe5dd0000\n"
        ".inst 0xe3500000\n"
        ".inst 0x159f0008\n"
        ".inst 0x0affffff\n"
        ".inst 0xe8bd8008\n"
        ".word 0xd8a083fa @ bounded tail data\n"
        ".word 0xe0a13899 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0035f454, 76)
extern "C" __attribute__((naked)) void func_0035f454() {
    asm volatile(
        ".arm\n"
        ".inst 0xe3520000\n"
        ".inst 0xc59fc03c\n"
        ".inst 0xe3a00000\n"
        ".inst 0xda00000b\n"
        ".inst 0xe0813080\n"
        ".inst 0xe1d330b0\n"
        ".inst 0xe3530000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe3530040\n"
        ".inst 0x1153000c\n"
        ".inst 0x1a000001\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe12fff1e\n"
        ".inst 0xe2800001\n"
        ".inst 0xe1520000\n"
        ".inst 0xcafffff3\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe12fff1e\n"
        ".word 0x0000ff20 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00379a28, 76)
extern "C" __attribute__((naked)) void engine_func_00379a28() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe5910008\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe5911010\n"
        ".inst 0xe5902000\n"
        ".inst 0xe5922008\n"
        ".inst 0xe12fff32\n"
        ".inst 0xe1b06000\n"
        ".inst 0x0a000007\n"
        ".inst 0xe284100c\n"
        ".inst 0xe8910006\n"
        ".inst 0xebfd3165\n"
        ".inst 0xe5943010\n"
        ".inst 0xe8940007\n"
        ".inst 0xe585302c\n"
        ".inst 0xe285501c\n"
        ".inst 0xe8850047\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003972c8, 76)
extern "C" __attribute__((naked)) void func_003972c8() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe1a05000\n"
        ".inst 0xe2800008\n"
        ".inst 0xe1510000\n"
        ".inst 0xe1a04001\n"
        ".inst 0x0a00000b\n"
        ".inst 0xe5941000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfffff6\n"
        ".inst 0xe5941004\n"
        ".inst 0xe1a00005\n"
        ".inst 0xebfffff3\n"
        ".inst 0xe5950000\n"
        ".inst 0xe1a01004\n"
        ".inst 0xe5902000\n"
        ".inst 0xe1a00005\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe12fff12\n"
        ".inst 0xe8bd8070\n"
    );
}

// DECOMP_FUNC(0x003eb014, 76)
extern "C" __attribute__((naked)) void func_003eb014() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe2404044\n"
        ".inst 0xe5500038\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a00000c\n"
        ".inst 0xe5940064\n"
        ".inst 0xe1510000\n"
        ".inst 0x8a000009\n"
        ".inst 0xe1500002\n"
        ".inst 0x8a000007\n"
        ".inst 0xe5d4000d\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000004\n"
        ".inst 0xebfb4978\n"
        ".inst 0xe2841050\n"
        ".inst 0xebfb31c6\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c4000d\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x003f5e40, 76)
extern "C" __attribute__((naked)) void func_003f5e40() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4070\n"
        ".inst 0xe59f503c\n"
        ".inst 0xe5951004\n"
        ".inst 0xe3510000\n"
        ".inst 0x13500000\n"
        ".inst 0x0a00000a\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5900004\n"
        ".inst 0xe3500000\n"
        ".inst 0x112fff31\n"
        ".inst 0xe5951004\n"
        ".inst 0xe5940000\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe5951004\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4070\n"
        ".inst 0xe12fff11\n"
        ".inst 0xe8bd8070\n"
        ".word 0x0044e930 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x00311d20, 80)
extern "C" __attribute__((naked)) void camp_func_00311d20() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4030\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe24dd014\n"
        ".inst 0xe1a05001\n"
        ".inst 0xe3a0001f\n"
        ".inst 0xebfe8b27\n"
        ".inst 0xe4902004\n"
        ".inst 0xe59f3028\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe2420004\n"
        ".inst 0xe1cd40ba\n"
        ".inst 0xe1a021a0\n"
        ".inst 0xe58d3000\n"
        ".inst 0xe3a03008\n"
        ".inst 0xe28d0008\n"
        ".inst 0xe1cd50b8\n"
        ".inst 0xfafe8add\n"
        ".inst 0xe28dd014\n"
        ".inst 0xe8bd8030\n"
        ".word 0x001e15bc @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x0034f648, 80)
extern "C" __attribute__((naked)) void ui_func_0034f648() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f1038\n"
        ".inst 0xe3a04000\n"
        ".inst 0xe5804004\n"
        ".inst 0xe5804008\n"
        ".inst 0xe480100c\n"
        ".inst 0xe59f1028\n"
        ".inst 0xe3a03003\n"
        ".inst 0xe3a02020\n"
        ".inst 0xe4804034\n"
        ".inst 0xfafdda38\n"
        ".inst 0xe2400040\n"
        ".inst 0xe5804010\n"
        ".inst 0xe5804014\n"
        ".inst 0xe5804018\n"
        ".inst 0xe58040a0\n"
        ".inst 0xe8bd8010\n"
        ".inst 0x0042067c\n"
        ".inst 0x0034e01c\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x00357be4, 80)
extern "C" __attribute__((naked)) void engine_func_00357be4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d40f8\n"
        ".inst 0xe1a0c000\n"
        ".inst 0xe1a05002\n"
        ".inst 0xe59d001c\n"
        ".inst 0xe1a06003\n"
        ".inst 0xe1a04001\n"
        ".inst 0xe58d0000\n"
        ".inst 0xe59d3018\n"
        ".inst 0xe1a02006\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe1a0000c\n"
        ".inst 0xebffffc5\n"
        ".inst 0xe2101102\n"
        ".inst 0x4a000004\n"
        ".inst 0xe1a02006\n"
        ".inst 0xe1a01005\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd40f8\n"
        ".inst 0xea000856\n"
        ".inst 0xe8bd80f8\n"
    );
}

// DECOMP_FUNC(0x0038007c, 80)
extern "C" __attribute__((naked)) void func_0038007c() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5d000ca\n"
        ".inst 0xe3500000\n"
        ".inst 0x1a00000d\n"
        ".inst 0xe5d40090\n"
        ".inst 0xe3500004\n"
        ".inst 0x0a000008\n"
        ".inst 0xe5940134\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000003\n"
        ".inst 0xe5d410c9\n"
        ".inst 0xe3510000\n"
        ".inst 0x03a01001\n"
        ".inst 0x0bfff096\n"
        ".inst 0xe3a00004\n"
        ".inst 0xe5c40090\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5c400c5\n"
        ".inst 0xe8bd8010\n"
    );
}

// DECOMP_FUNC(0x0038b334, 80)
extern "C" __attribute__((naked)) void func_0038b334() {
    asm volatile(
        ".arm\n"
        ".inst 0xe59f1024\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe1a04000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe59f0018\n"
        ".inst 0xe5900000\n"
        ".inst 0xe2800088\n"
        ".inst 0xebfcbe37\n"
        ".inst 0xe1a00004\n"
        ".inst 0xe8bd4010\n"
        ".inst 0xeafc9c6f\n"
        ".inst 0x00421e0c\n"
        ".inst 0x00432fc8\n"
        ".inst 0xe3a01000\n"
        ".inst 0xe5801000\n"
        ".inst 0xe5801004\n"
        ".inst 0xe5801008\n"
        ".inst 0xe5c0100c\n"
        ".inst 0xe5c0100d\n"
        ".inst 0xe12fff1e\n"
    );
}

// DECOMP_FUNC(0x003ac930, 80)
extern "C" __attribute__((naked)) void engine_func_003ac930() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe59f4018\n"
        ".inst 0xe5940000\n"
        ".inst 0xe3500000\n"
        ".inst 0x0a000002\n"
        ".inst 0xebfc5e85\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe5840000\n"
        ".inst 0xe8bd8010\n"
        ".inst 0x0043d990\n"
        ".inst 0xe59f001c\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5900000\n"
        ".inst 0xe5901000\n"
        ".inst 0xe5911014\n"
        ".inst 0xe12fff31\n"
        ".inst 0xe3a00000\n"
        ".inst 0xe8bd8010\n"
        ".word 0x0043d9c8 @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003beaf0, 80)
extern "C" __attribute__((naked)) void ui_func_003beaf0() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd028\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb5465\n"
        ".inst 0xe1a01004\n"
        ".inst 0xebfb1022\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb5461\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a02004\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfa22b0\n"
        ".inst 0xe5dd001d\n"
        ".inst 0xeddf0a04\n"
        ".inst 0xe28dd028\n"
        ".inst 0xee000a10\n"
        ".inst 0xeeb80a40\n"
        ".inst 0xee200a20\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3c23d70a @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003bed80, 80)
extern "C" __attribute__((naked)) void ui_func_003bed80() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d4010\n"
        ".inst 0xe24dd028\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb53c1\n"
        ".inst 0xe1a01004\n"
        ".inst 0xebfb0f7e\n"
        ".inst 0xe1a04000\n"
        ".inst 0xebfb53bd\n"
        ".inst 0xe1a01000\n"
        ".inst 0xe1a02004\n"
        ".inst 0xe1a0000d\n"
        ".inst 0xebfa220c\n"
        ".inst 0xe5dd001e\n"
        ".inst 0xeddf0a04\n"
        ".inst 0xe28dd028\n"
        ".inst 0xee000a10\n"
        ".inst 0xeeb80a40\n"
        ".inst 0xee200a20\n"
        ".inst 0xe8bd8010\n"
        ".word 0x3c23d70a @ bounded tail data\n"
    );
}

// DECOMP_FUNC(0x003e51c4, 80)
extern "C" __attribute__((naked)) void func_003e51c4() {
    asm volatile(
        ".arm\n"
        ".inst 0xe92d41f0\n"
        ".inst 0xe1a06001\n"
        ".inst 0xe1a07000\n"
        ".inst 0xe59d4018\n"
        ".inst 0xe1a05003\n"
        ".inst 0xe1a02003\n"
        ".inst 0xed940a00\n"
        ".inst 0xebfffc9a\n"
        ".inst 0xed940a01\n"
        ".inst 0xe1a02005\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00007\n"
        ".inst 0xebfffcc3\n"
        ".inst 0xed940a02\n"
        ".inst 0xe1a02005\n"
        ".inst 0xe1a01006\n"
        ".inst 0xe1a00007\n"
        ".inst 0xebf90364\n"
        ".inst 0xe3a00001\n"
        ".inst 0xe8bd81f0\n"
    );
}
