#include "types.h"

// Batch 31 C: exact ARM bytes; post-return literal words are preserved as data.

extern "C" u32 func_002bf41c(void*);
extern "C" u32 func_002b756c(void*);
extern "C" void func_002b7510(void*, u32);
extern "C" void func_002b74c4(void*, u32);

// DECOMP_FUNC(0x00201040, 168)
extern "C" void battle_func_00201040(void) {
    void** p_global = reinterpret_cast<void**>(0x0043DED0);
    char* mgr = static_cast<char*>(*p_global);
    if (mgr == nullptr) {
        return;
    }
    s32 count = *reinterpret_cast<s32*>(mgr + 0x2C);
    if (count > 0) {
        void** items = reinterpret_cast<void**>(mgr + 0x04);
        for (s32 i = 0; i < count; ++i) {
            void* elem = items[i];
            if (func_002bf41c(elem) != 0) {
                if (func_002b756c(elem) != 4) {
                    func_002b7510(elem, 1);
                }
            }
        }
    }
    void** items2 = reinterpret_cast<void**>(mgr + 0x34);
    for (s32 i = 0; i < 10; ++i) {
        void* elem2 = items2[i];
        if (func_002bf41c(elem2) != 0) {
            func_002b74c4(elem2, 1);
        }
    }
}

extern "C" u32 script_vm_func_002546c4(void);
extern "C" void* Tbb_GetSubTable(void*, u32);
extern "C" u8* Tbb_GetPayloadData(void);
extern "C" u32 Tbb_GetRowCount(void*);

// DECOMP_FUNC(0x002010e8, 164)
extern "C" void camp_func_002010e8(void* tbb) {
    u32 outer_count = script_vm_func_002546c4();
    void* sub0 = Tbb_GetSubTable(tbb, 0);
    u8* payload = Tbb_GetPayloadData();
    u32 row_count = Tbb_GetRowCount(sub0);
    if (row_count == 0) {
        return;
    }
    for (u32 r = 0; r < row_count; ++r, payload += 0x2c) {
        if (payload[0x2a] == 0) {
            continue;
        }
        if (outer_count <= 1) {
            continue;
        }
        for (u32 idx = 1; idx < outer_count; ++idx) {
            Tbb_GetSubTable(tbb, idx);
            u32* first_word = reinterpret_cast<u32*>(Tbb_GetPayloadData());
            s16 target = *reinterpret_cast<s16*>(payload + 0x20);
            if (static_cast<s32>(*first_word) == static_cast<s32>(target)) {
                payload[0x2a] = static_cast<u8>(idx);
                break;
            }
        }
    }
}

extern "C" void* script_vm_func_002b49d8(u32);
extern "C" void* Tbb_GetGlobalSubTable(u32, u32);

// DECOMP_FUNC(0x0020118c, 168)
extern "C" void script_vm_func_0020118c(void) {
    script_vm_func_002b49d8(0x19);
    u32 outer_count = script_vm_func_002546c4();
    void* sub0 = Tbb_GetGlobalSubTable(0x19, 0);
    u8* payload = Tbb_GetPayloadData();
    u32 row_count = Tbb_GetRowCount(sub0);
    if (row_count == 0) {
        return;
    }
    for (u32 r = 0; r < row_count; ++r, payload += 0x2c) {
        if (payload[0x2a] == 0) {
            continue;
        }
        if (outer_count <= 1) {
            continue;
        }
        for (u32 idx = 1; idx < outer_count; ++idx) {
            Tbb_GetGlobalSubTable(0x19, idx);
            u32* first_word = reinterpret_cast<u32*>(Tbb_GetPayloadData());
            s16 target = *reinterpret_cast<s16*>(payload + 0x20);
            if (static_cast<s32>(*first_word) == static_cast<s32>(target)) {
                payload[0x2a] = static_cast<u8>(idx);
                break;
            }
        }
    }
}

extern "C" void ui_func_002bf460(u32, u32, s32, s32, s32, u32);

// DECOMP_FUNC(0x00212394, 168)
extern "C" void ui_func_00212394(const float* rect, s32 off_x, s32 off_y, u32 arg3, const char* text) {
    float fx = rect[0] + rect[2] + static_cast<float>(off_x);
    float fy = rect[1] + rect[3] + static_cast<float>(off_y);
    s32 cur_x = static_cast<s32>(fx);
    s32 cur_y = static_cast<s32>(fy);
    if (text == nullptr || *text == '\0') {
        return;
    }
    for (const char* p = text; *p != '\0'; ++p) {
        char c = *p;
        if (c != ' ') {
            ui_func_002bf460(2, 0x0D, static_cast<s32>(c) - 0x30, cur_x, cur_y, arg3);
        }
        cur_x += 7;
    }
}

extern "C" u32 engine_func_00296f60(u32);
extern "C" u32 engine_func_00289640(void);
extern "C" void ui_func_00254514(u32, u32);
extern "C" void script_vm_func_0028efe0(u32, u32, u32);
extern "C" void script_vm_func_002c0128(void);
extern "C" u32 ui_func_002544fc(u32);
extern "C" u32 script_vm_func_0025506c(void*, u32, u32, u32, u32);
extern "C" void engine_func_00348c74(u32);

// DECOMP_FUNC(0x002143cc, 160)
extern "C" u32 script_vm_func_002143cc(void) {
    u16 r5 = static_cast<u16>(engine_func_00296f60(0));
    if (engine_func_00289640() == 0) {
        ui_func_00254514(0, 0);
        script_vm_func_0028efe0(r5, 0, 1);
        script_vm_func_002c0128();
    }
    void* r4 = script_vm_func_002b49d8(0x1E);
    u32 cur_val = ui_func_002544fc(0);
    u32 check = script_vm_func_0025506c(r4, 0x10, cur_val, 6, 0);
    u32 next_val = ui_func_002544fc(0);
    ui_func_00254514(0, next_val + 1);
    if (check != 1) {
        return 0;
    }
    engine_func_00348c74(r5);
    return 1;
}

extern "C" void* camp_func_002ae818(void*);
extern "C" u32 camp_func_00282c44(void*);

// DECOMP_FUNC(0x00219570, 180)
extern "C" s32 func_00219570(void** a, void** b) {
    char* r8 = static_cast<char*>(camp_func_002ae818(*a));
    char* r7 = static_cast<char*>(camp_func_002ae818(*b));
    u32 r6 = camp_func_00282c44(*a);
    u32 r0 = camp_func_00282c44(*b);
    if (r6 != 2) {
        if (r0 == 2) {
            return -1;
        }
    } else {
        if (r0 != 2) {
            return 1;
        }
    }
    s32 diff = static_cast<s32>(*reinterpret_cast<u16*>(r7 + 0x26)) - static_cast<s32>(*reinterpret_cast<u16*>(r8 + 0x26));
    if (diff != 0) {
        return diff;
    }
    char* ra = static_cast<char*>(camp_func_002ae818(*a));
    char* rb = static_cast<char*>(camp_func_002ae818(*b));
    return static_cast<s32>(*reinterpret_cast<u16*>(rb + 0x24)) - static_cast<s32>(*reinterpret_cast<u16*>(ra + 0x24));
}

extern "C" s32 func_00219600(const u16* a, const u16* b) {
    s32 diff = static_cast<s32>(b[1]) - static_cast<s32>(a[1]);
    if (diff != 0) {
        return diff;
    }
    return static_cast<s32>(a[0]) - static_cast<s32>(b[0]);
}

extern "C" void engine_func_002502e8(void*, u32);
extern "C" void engine_func_00256c3c(void*);
extern "C" void func_00250108(void*, const float*, u32);
extern "C" void func_0024ffbc(void*, const float*, u32);
extern "C" void func_0024ff28(void*, const void*, u32);

// DECOMP_FUNC(0x0021a0a8, 172)
extern "C" void engine_func_0021a0a8(void* dst, const float* opt_vec3, u32 flag, float scale) {
    char stack_obj[0x40];
    if (flag != 0) {
        engine_func_002502e8(stack_obj, flag);
    } else {
        engine_func_00256c3c(stack_obj);
    }
    if (scale != 1.0f) {
        float scale_vec[3] = { scale, scale, scale };
        func_00250108(stack_obj, scale_vec, 2);
    }
    if (opt_vec3 != nullptr) {
        float tr_vec[3] = { opt_vec3[0], opt_vec3[1], opt_vec3[2] };
        func_0024ffbc(stack_obj, tr_vec, 2);
    }
    func_0024ff28(static_cast<char*>(dst) + 0x10, stack_obj, 0);
}

extern "C" u8* script_vm_func_0024f734(s32);
extern "C" void engine_func_002c4b30(void*, u32);
extern "C" s32 script_vm_func_0024f6fc(void);

// DECOMP_FUNC(0x0021bd04, 160)
extern "C" void script_vm_func_0021bd04(void) {
    if (script_vm_func_0024f734(0) == nullptr) {
        return;
    }
    engine_func_002c4b30(reinterpret_cast<void*>(0x004A0BE4), 0x400);
    s32 total = script_vm_func_0024f6fc();
    u32* p_out_count = reinterpret_cast<u32*>(0x00447604);
    *p_out_count = 0;
    if (total <= 0) {
        return;
    }
    s32 target0 = *reinterpret_cast<s32*>(0x0049F91C);
    s32 target1 = *reinterpret_cast<s32*>(0x0049F920);
    u32* out_arr = reinterpret_cast<u32*>(0x004A0BE4);
    for (s32 i = 0; i < total; ++i) {
        const char* item = reinterpret_cast<const char*>(script_vm_func_0024f734(i));
        s8 b0 = static_cast<s8>(item[0]);
        if (b0 == -1 || static_cast<s32>(b0) != target0) {
            continue;
        }
        s8 b1 = static_cast<s8>(item[1]);
        if (static_cast<s32>(b1) != target1) {
            continue;
        }
        u32 idx = *p_out_count;
        out_arr[idx] = i;
        *p_out_count = idx + 1;
    }
}

struct Vec3_0021de1c {
    float x;
    float y;
    float z;
};
extern "C" float engine_func_00287d54(Vec3_0021de1c target, Vec3_0021de1c entry);

// DECOMP_FUNC(0x0021de1c, 164)
extern "C" void script_vm_func_0021de1c(void) {
    s32 min_dist = 0x1869F;
    s32 best_idx = -1;
    char* base = *reinterpret_cast<char**>(0x00447A48);
    const Vec3_0021de1c* target_pos = reinterpret_cast<const Vec3_0021de1c*>(*reinterpret_cast<char**>(0x00447E88) + 0x1C);
    for (s32 i = 0; i < 24; ++i) {
        char* entry = base + i * 40;
        if (entry[0x1C] == 0) {
            continue;
        }
        if (*reinterpret_cast<u16*>(entry + 0x32) != 15) {
            continue;
        }
        const Vec3_0021de1c* entry_pos = reinterpret_cast<const Vec3_0021de1c*>(entry + 0x20);
        float dist_f = engine_func_00287d54(*target_pos, *entry_pos);
        s32 dist = static_cast<s32>(dist_f);
        if (dist < min_dist) {
            min_dist = dist;
            best_idx = i;
        }
    }
    if (best_idx != -1) {
        char* best_entry = base + best_idx * 40;
        *reinterpret_cast<u16*>(best_entry + 0x30) = 1;
        best_entry[0x1D] = 1;
    }
}

// DECOMP_FUNC(0x0021dec0, 156)
extern "C" void script_vm_func_0021dec0(void) {
    char* base = *reinterpret_cast<char**>(0x00447A78);
    base[0x17] = 0;
    for (s32 i = 0; i < 128; ++i) {
        char* slot = base + i * 404;
        if (slot[0x1D0] == 0) {
            continue;
        }
        u32 type = *reinterpret_cast<u32*>(slot + 0x1E4);
        if (type == 0x1D || type == 0x26 || type == 0x1E || type == 0x1F || type == 0x25) {
            continue;
        }
        u32 state = *reinterpret_cast<u32*>(slot + 0x1D4);
        if (state == 8 || state == 10 || state == 12 || state == 14 || state == 16) {
            *reinterpret_cast<u32*>(slot + 0x1D4) = 6;
            *reinterpret_cast<u32*>(slot + 0x1D8) = 1;
        }
    }
}

extern "C" void func_002d8590(void*, u32);

// DECOMP_FUNC(0x00221c60, 168)
extern "C" void battle_func_00221c60(u32 flag) {
    char* mgr = *reinterpret_cast<char**>(0x0043DED0);
    if (mgr == nullptr) {
        return;
    }
    mgr[0x5C] = static_cast<char>(flag);
    u32 arg1 = (flag != 0) ? 1 : 0;
    void** items = reinterpret_cast<void**>(mgr + 0x34);
    for (s32 i = 0; i < 10; ++i) {
        void* item = items[i];
        if (func_002bf41c(item) != 0) {
            func_002d8590(item, arg1);
        }
    }
}

extern "C" void func_002c4360(void*);
extern "C" void* func_002972f8(void*, void*);

// DECOMP_FUNC(0x0022a210, 160)
extern "C" u32 script_vm_func_0022a210(void* self_ptr) {
    char* self = static_cast<char*>(self_ptr);
    char* global_obj = *reinterpret_cast<char**>(0x00432FC8);
    u32* p_flags = reinterpret_cast<u32*>(global_obj + 0x754);
    u32 flags = *p_flags;
    u32 bit4 = (flags >> 4) & 1;
    *p_flags = flags & ~0x70u;
    if (bit4 != 0) {
        *reinterpret_cast<u32*>(self) = 1;
        void** p_f8 = reinterpret_cast<void**>(self + 8);
        if (*p_f8 != nullptr) {
            func_002c4360(*p_f8);
            *p_f8 = nullptr;
        }
        void** p_fc = reinterpret_cast<void**>(self + 0xC);
        if (*p_fc != nullptr) {
            func_002c4360(*p_fc);
            *p_fc = nullptr;
        }
        void** p_f10 = reinterpret_cast<void**>(self + 0x10);
        if (*p_f10 != nullptr) {
            func_002c4360(*p_f10);
            *p_f10 = nullptr;
        }
    } else {
        void* f10 = *reinterpret_cast<void**>(self + 0x10);
        void* fc = *reinterpret_cast<void**>(self + 0xC);
        char* res = static_cast<char*>(func_002972f8(f10, fc));
        *reinterpret_cast<void**>(self + 0x14) = res;
        *reinterpret_cast<u32*>(res + 0x108) = 2;
        *reinterpret_cast<u32*>(self) = 0;
    }
    return 0;
}

extern "C" char* func_00293c98(void);
extern "C" u32 func_0022a640(u32, u32, u32, u32, u32, u32, s32);

// DECOMP_FUNC(0x0022a76c, 184)
extern "C" u32 battle_func_0022a76c(u32 arg0, u32 arg1, u32 arg2) {
    char* base = func_00293c98();
    u32 flags = *reinterpret_cast<u32*>(base + 0x44A0);
    if ((flags & 0x140) != 0) {
        return 0;
    }
    if (arg1 != 0) {
        u32 a3 = *reinterpret_cast<u32*>(base + 0x2230);
        return func_0022a640(1, 0, arg0, a3, arg1, arg2, 13);
    }
    base = func_00293c98();
    flags = *reinterpret_cast<u32*>(base + 0x44A0);
    if ((flags & 0x140) != 0) {
        return 0;
    }
    u32 a3 = *reinterpret_cast<u32*>(base + 0x2230);
    return func_0022a640(0, 0, arg0, a3, 0, arg2, -1);
}

extern "C" void func_002af854(void*, u32, u32);
extern "C" void func_002333d4(void*, u32);
extern "C" u32 func_002337a0(void*);
extern "C" void func_002a6214(u32);

// DECOMP_FUNC(0x0022b858, 180)
extern "C" void engine_func_0022b858(void* self_ptr) {
    char* self = static_cast<char*>(self_ptr);
    self[0x631] = 0;
    self[0x632] = 0;
    *reinterpret_cast<u32*>(self + 0xC58) = 0;
    *reinterpret_cast<u32*>(self + 0xC5C) = 0;
    *reinterpret_cast<u32*>(self + 0xCB8) = 0;

    for (s32 i = 0; i < 10; ++i) {
        func_002af854(self + 0x654 + i * 0x8C, 0, 0);
    }
    func_002333d4(self + 0xA8, 0);
    func_002333d4(self + 0xA8, 1);

    u32 idx = func_002337a0(self);
    char* obj = *reinterpret_cast<char**>(self + 0x530 + idx * 4);
    u16 val = *reinterpret_cast<u16*>(obj + 0x5A);
    u32 r1 = static_cast<u32>(val) + 1;
    u32 r2 = static_cast<u32>(val) + 2;
    *reinterpret_cast<u32*>(self + 0xC64) = r1;
    *reinterpret_cast<u32*>(self + 0xC60) = r2;

    u8* p_flag = reinterpret_cast<u8*>(self + 0xC78 + r1);
    if (*p_flag == 0) {
        func_002a6214(0x2A);
        *p_flag = 1;
    }
}

extern "C" s32 func_0024f7e8(void);
extern "C" void* func_0024f7a8(s32);

// DECOMP_FUNC(0x0022cc38, 180)
extern "C" void* func_0022cc38(void* self, s32 target_id) {
    (void)self;
    if (target_id >= 100) {
        char* table = reinterpret_cast<char*>(0x0044CE08);
        for (s32 i = 0; i < 999; ++i) {
            char* entry = table + i * 34;
            s16 id = *reinterpret_cast<s16*>(entry);
            if (id == -1) {
                break;
            }
            if (static_cast<s32>(id) == target_id) {
                return entry + 2;
            }
        }
    } else {
        s32 count = func_0024f7e8();
        for (s32 i = 0; i < count; ++i) {
            char* item = static_cast<char*>(func_0024f7a8(i));
            s16 id = *reinterpret_cast<s16*>(item + 0x20);
            if (id == -1) {
                break;
            }
            if (static_cast<s32>(id) == target_id) {
                return item;
            }
            count = func_0024f7e8();
        }
    }
    return *reinterpret_cast<void**>(0x0044CDF0 + 4);
}

extern "C" char* func_002b9364(u16);
extern "C" u32 func_001f48f4(void*, u32);
extern "C" u32 func_002992d8(u32, u32);

// DECOMP_FUNC(0x0022e4e8, 164)
extern "C" void camp_func_0022e4e8(u16* p_flags, char* src_obj, u32 index) {
    u16 sub_id = *reinterpret_cast<u16*>(src_obj + 0x46);
    char* res = func_002b9364(sub_id);
    u16 extra = *reinterpret_cast<u16*>(res + index * 2 + 0x6C);
    u16 flags = extra;
    if ((flags & 0x3FF) == 0) {
        flags = (flags & 0xFC00) | 1;
    }
    *p_flags = flags;
    u32 val = func_001f48f4(src_obj + 0x34, index);
    if (func_002992d8(flags >> 10, val) != 0) {
        *p_flags = (flags & 0x3FF) | static_cast<u16>((val << 10) & 0xFC00);
    }
}

extern "C" void func_0028c2a8(void);
extern "C" void func_0029a3c4(u32);
extern "C" void func_00292f44(u32);
extern "C" void* func_002b66ec(void);
extern "C" void func_0029c768(u32);
extern "C" void func_0029a384(void*);
extern "C" void func_0029a368(void*);
extern "C" void func_002306ec(u32);
extern "C" void func_0023077c(u32);
extern "C" void* func_0029a2d0(u32, u32);

// DECOMP_FUNC(0x002303c8, 164)
extern "C" void engine_func_002303c8(void* self_ptr) {
    char* self = static_cast<char*>(self_ptr);
    func_0028c2a8();
    u32 type = *reinterpret_cast<u32*>(self + 0x10);
    func_0029a3c4((type == 1) ? 3 : 7);
    func_00292f44(0);
    void* obj = func_002b66ec();
    func_0029c768(1);
    func_0029a384(obj);
    func_0029a368(obj);
    *reinterpret_cast<u32*>(self + 0x15D24) = 1;
    func_002306ec(1);
    func_0023077c(0);

    void** p_field15d48 = reinterpret_cast<void**>(self + 0x15D48);
    if (*p_field15d48 == nullptr) {
        *p_field15d48 = func_0029a2d0(0x00407738, 7);
    }
    *reinterpret_cast<u32*>(self + 0x15D28) = 0;
}

extern "C" void func_002b9008(void);
extern "C" void* func_002c4450(void*, u32, s32);
extern "C" u16 func_002b88c4(u32, u32);

// DECOMP_FUNC(0x00233804, 168)
extern "C" void unite_func_00233804(void* self_ptr, u32 arg1, u32 arg2, s32 arg3) {
    char* self = static_cast<char*>(self_ptr);
    *reinterpret_cast<u32*>(self + 4) = arg1;
    *reinterpret_cast<u32*>(self + 8) = arg2;
    *reinterpret_cast<s32*>(self + 12) = arg3;
    *reinterpret_cast<s16*>(self + 0x14) = -1;
    self[0x11] = 0;
    self[0x12] = 0;
    *reinterpret_cast<u16*>(self + 0x16) = 0;

    s16 count = *reinterpret_cast<s16*>(self + 0x30);
    if (count > 0) {
        for (s16 i = 0; i < count; ++i) {
            func_002b9008();
        }
        func_002c4450(self + 0x18, 0x18, -1);
        *reinterpret_cast<s16*>(self + 0x30) = 0;
    }
    if (arg3 > 0) {
        for (s32 i = 0; i < arg3; ++i) {
            u16 val = func_002b88c4(arg1, arg2 + static_cast<u32>(i));
            *reinterpret_cast<u16*>(self + 0x18 + i * 2) = val;
            *reinterpret_cast<u16*>(self + 0x30) += 1;
        }
    }
}

// DECOMP_FUNC(0x00237738, 172)
extern "C" void func_00237738(void* self_ptr, u32 arg1, u32 arg2, u32 arg3) {
    char* self = static_cast<char*>(self_ptr);
    *reinterpret_cast<void**>(self) = reinterpret_cast<void*>(0x00421500);
    *reinterpret_cast<u32*>(self + 4) = arg3;
    *reinterpret_cast<u32*>(self + 8) = arg1;
    *reinterpret_cast<u32*>(self + 0xC) = 0;
    *reinterpret_cast<u32*>(self + 0x10) = 0;
    *reinterpret_cast<u32*>(self + 0x14) = 0;
    *reinterpret_cast<u32*>(self + 0x18) = 0;
    *reinterpret_cast<u32*>(self + 0x1C) = arg2;
    *reinterpret_cast<u32*>(self + 0x20) = 0;
    *reinterpret_cast<u32*>(self + 0x24) = 0;
    *reinterpret_cast<u32*>(self + 0x28) = 0;
    *reinterpret_cast<u32*>(self + 0x2C) = 0;
    *reinterpret_cast<u32*>(self + 0x30) = 0;
    *reinterpret_cast<u32*>(self + 0x34) = 0;
    *reinterpret_cast<u32*>(self + 0x38) = 0;
    *reinterpret_cast<u32*>(self + 0x3C) = 0;
    *reinterpret_cast<u32*>(self + 0x40) = 0;
    *reinterpret_cast<u32*>(self + 0x44) = 0;
    *reinterpret_cast<u32*>(self + 0x48) = 0;
    *reinterpret_cast<u32*>(self + 0x4C) = 0;
    *reinterpret_cast<u32*>(self + 0x50) = 0;
    *reinterpret_cast<u32*>(self + 0x54) = 0;
    *reinterpret_cast<u32*>(self + 0x58) = 0;
    *reinterpret_cast<u32*>(self + 0x5C) = 0;
    *reinterpret_cast<u32*>(self + 0x60) = 0;
    self[0x64] = 0;
}

struct PatternLookupEntry_00238b30 {
    u16 id;
    u16 f2;
    u16 f4;
    u16 f6;
};
extern "C" PatternLookupEntry_00238b30* func_00238be8(u32);

// DECOMP_FUNC(0x00238b30, 184)
extern "C" u32 func_00238b30(const u16** p_arr, void** p_node, u32 start, u32 count) {
    u32 end = start + count;
    if (start >= end) {
        return 1;
    }
    const u16* arr = *p_arr;
    char* node = static_cast<char*>(*p_node);
    for (u32 i = start; i < end; ++i) {
        u16 val = arr[i];
        u16 target = *reinterpret_cast<u16*>(node + 0xA);
        if (val != target) {
            PatternLookupEntry_00238b30* lookup = func_00238be8(target);
            if (lookup == nullptr) {
                return 0;
            }
            if (lookup->f2 == 0) {
                return 0;
            }
            if (val != lookup->f2) {
                if (lookup->f4 == 0 || val != lookup->f4) {
                    if (lookup->f6 == 0 || val != lookup->f6) {
                        return 0;
                    }
                }
            }
        }
        node = *reinterpret_cast<char**>(node + 4);
        *p_node = node;
        arr = *p_arr;
    }
    return 1;
}

extern "C" char* func_00238e18(void*, void*);
extern "C" s32 func_003e0dbc(const char*, const char*);

// DECOMP_FUNC(0x0023963c, 188)
extern "C" void* engine_func_0023963c(void* self_ptr, u32 mode, u32 idx) {
    char* self = static_cast<char*>(self_ptr);
    if (mode == 0) {
        u32 count0 = *reinterpret_cast<u32*>(self + 0x210);
        if (idx < count0) {
            return *reinterpret_cast<void**>(self + 0x21C + idx * 4);
        }
        return nullptr;
    }
    u32 count = *reinterpret_cast<u32*>(self + 0x3C0);
    if (idx >= count) {
        return nullptr;
    }
    u32 max_c = *reinterpret_cast<u32*>(self + 0x560);
    if (max_c != count) {
        return *reinterpret_cast<void**>(self + 0x3CC + idx * 4);
    }
    char stack_buf[8];
    char* res_str = func_00238e18(stack_buf, self + 0x564 + idx * 8);
    for (u32 i = 0; i < count; ++i) {
        char* item = *reinterpret_cast<char**>(self + 0x3CC + i * 4);
        if (func_003e0dbc(res_str, item + 0x20) != 0) {
            return item;
        }
    }
    return nullptr;
}

// DECOMP_FUNC(0x0023abd4, 180)
extern "C" void engine_func_0023abd4(const void* src_ptr, float* out, float scale) {
    const char* src = static_cast<const char*>(src_ptr);
    const char* r2 = *reinterpret_cast<const char* const*>(*reinterpret_cast<const char* const*>(src + 4) + 0x10);
    u8 flag = *reinterpret_cast<const u8*>(src + 0x1C);
    float s1, s2;
    if (flag != 0) {
        const char* r0 = *reinterpret_cast<const char* const*>(*reinterpret_cast<const char* const*>(src + 8) + 0xC) + 0x14;
        s1 = static_cast<float>(*reinterpret_cast<const s32*>(r0));
        s2 = static_cast<float>(*reinterpret_cast<const s32*>(r0 + 4));
    } else {
        u16 w1 = *reinterpret_cast<const u16*>(r2 + 0x24);
        u16 w2 = *reinterpret_cast<const u16*>(r2 + 0x26);
        const float* f10 = reinterpret_cast<const float*>(src + 0x10);
        float ax = (f10[0] < 0.0f) ? -f10[0] : f10[0];
        float ay = (f10[1] < 0.0f) ? -f10[1] : f10[1];
        s1 = static_cast<float>(w1) + ax * 2.0f;
        s2 = static_cast<float>(w2) + ay * 2.0f;
    }
    float max_val = (s1 > s2) ? s1 : s2;
    float scaled = max_val * scale;
    out[0] = scaled;
    out[1] = scaled;
    u16 base_w = *reinterpret_cast<const u16*>(r2 + 0x24);
    out[2] = static_cast<float>(base_w) * scale * 0.5f;
}

// DECOMP_FUNC(0x0023bc5c, 160)
extern "C" void func_0023bc5c(void* unused, u32* dst, const u32* src) {
    (void)unused;
    u8 flag = *reinterpret_cast<const u8*>(reinterpret_cast<const char*>(src) + 8);
    u32 r5 = (flag != 0) ? 0 : 0x80000000u;
    u32 global_val = *reinterpret_cast<u32*>(0x0044E670);
    u32 ip = src[0] - (global_val << 3);

    dst[0] = 1;
    dst[1] = 0xF025F;
    dst[2] = r5 | ip;
    dst[3] = 0xF0227;
    dst[4] = src[1];
    dst[5] = 0xF0228;
    dst[6] = 0;
    dst[7] = 0x10245;
    dst[8] = 1;
    dst[9] = 0xF022F;
    dst[10] = 1;
    dst[11] = 0x10245;
    dst[12] = 1;
    dst[13] = 0xF0231;
    dst[14] = 0;
    dst[15] = 0x8025E;
    dst[16] = 0;
    dst[17] = 0x8025E;
}

extern "C" char* func_00226b2c(void*, s16, s16, u32);

// DECOMP_FUNC(0x0023c4c4, 192)
extern "C" u32 battle_func_0023c4c4(s32 arg0, u32 arg1, u32 arg2, u32 arg3, s32 arg4, u32 arg5, u32 arg6, u32 arg7) {
    void* mgr = *reinterpret_cast<void**>(0x00434290);
    char* obj1 = func_00226b2c(mgr, static_cast<s16>(arg0), 0, arg1);
    if (arg7 == 0) {
        obj1[5] = static_cast<char>(obj1[5] | 4);
    }
    obj1[4] = 0x21;
    *reinterpret_cast<u32*>(obj1 + 0x14) = arg2;
    *reinterpret_cast<u32*>(obj1 + 0x28) = arg5;
    *reinterpret_cast<u32*>(obj1 + 0x4C) = arg3;

    char* obj2 = func_00226b2c(mgr, static_cast<s16>(arg0 + arg4), 0, arg1);
    if (arg7 == 0) {
        obj2[5] = static_cast<char>(obj2[5] | 4);
    }
    obj2[4] = 0x22;
    *reinterpret_cast<u32*>(obj2 + 0x14) = arg2;
    *reinterpret_cast<u32*>(obj2 + 0x28) = arg6;
    *reinterpret_cast<u32*>(obj2 + 0x4C) = 0;
    return 1;
}

extern "C" char* func_002bf6d0(u32, u32);

// DECOMP_FUNC(0x0023e590, 164)
extern "C" void camp_func_0023e590(void* self_ptr, s32* out1, s32* out2) {
    char* self = static_cast<char*>(self_ptr);
    u8 flag22 = *reinterpret_cast<u8*>(self + 0x22);
    s32 val38 = *reinterpret_cast<s32*>(self + 0x38);
    if (flag22 != 0) {
        char* row = func_002bf6d0(0x19, val38 + 0x57);
        *out1 = static_cast<s32>(*reinterpret_cast<s16*>(row + 8));
        *out2 = static_cast<s32>(*reinterpret_cast<s16*>(row + 0xA));
        return;
    }
    s32 adj = val38;
    if (adj > 15) {
        adj -= 12;
    }
    char* row = func_002bf6d0(0x19, adj + 0x2D);
    *out1 = static_cast<s32>(*reinterpret_cast<s16*>(row + 8));
    *out2 = static_cast<s32>(*reinterpret_cast<s16*>(row + 0xA));

    u32 val3c = *reinterpret_cast<u32*>(self + 0x3C);
    if (val3c != 0) {
        if (static_cast<u32>(val38 - 4) <= 11) {
            *out1 -= 0x190;
        }
    } else {
        if (val38 > 15) {
            *out1 += 0x190;
        }
    }
}

extern "C" void func_002f8270(void*);
extern "C" u32 func_00323660(void*, void*);
extern "C" u32 func_00318df8(void*);
extern "C" void func_003243bc(void*, void*);
extern "C" void func_002473ac(void*);
extern "C" void func_0024736c(void*);
extern "C" void* func_0030ed58(u32, u32);

// DECOMP_FUNC(0x00243234, 180)
extern "C" void ui_func_00243234(void* unused, u32 arg1, void* out_struct_ptr) {
    (void)unused;
    char* glob = reinterpret_cast<char*>(0x0044EA80);
    char* out = static_cast<char*>(out_struct_ptr);
    void* p_f3c = *reinterpret_cast<void**>(glob + 0x3C);
    if (p_f3c != nullptr) {
        char* obj40 = *reinterpret_cast<char**>(glob + 0x40);
        func_002f8270(obj40);
        u32 val8 = *reinterpret_cast<u32*>(obj40 + 8);
        *reinterpret_cast<u32*>(out + 0x100) = val8;
        *reinterpret_cast<u32*>(out + 0xFC) = func_00323660(obj40, out);
        *reinterpret_cast<u32*>(out + 0x104) = func_00318df8(obj40);
        func_003243bc(obj40, out + 0xC8);
        if (*reinterpret_cast<u32*>(out + 0x100) == 1) {
            func_002473ac(obj40);
            *reinterpret_cast<void**>(glob + 0x40) = nullptr;
            func_0024736c(p_f3c);
            *reinterpret_cast<void**>(glob + 0x3C) = nullptr;
        }
    } else {
        *reinterpret_cast<void**>(glob + 0x3C) = nullptr;
        char* new_obj = static_cast<char*>(func_0030ed58(0, arg1));
        *reinterpret_cast<void**>(glob + 0x40) = new_obj;
        *reinterpret_cast<u32*>(new_obj) = 0xBA;
        *reinterpret_cast<u32*>(new_obj + 4) = 0x1C;
        *reinterpret_cast<u32*>(out + 0x100) = 0;
    }
}

// DECOMP_FUNC(0x002432e8, 168)
extern "C" void ui_func_002432e8(void) {
    char* base = reinterpret_cast<char*>(0x004EA81C);
    float* v = reinterpret_cast<float*>(base + 0x100);
    const float* m = reinterpret_cast<const float*>(base + 0x140);

    float vx = v[0];
    float vy = v[1];
    float vz = v[2];

    float ox = vx * m[0] + vy * m[4] + vz * m[8]  + m[12];
    float oy = vx * m[1] + vy * m[5] + vz * m[9]  + m[13];
    float oz = vx * m[2] + vy * m[6] + vz * m[10] + m[14];
    float ow = vx * m[3] + vy * m[7] + vz * m[11] + m[15];

    v[0] = ox;
    v[1] = oy;
    v[2] = oz;
    v[3] = ow;
}

extern "C" char* func_00282b94(void*, s32);

// DECOMP_FUNC(0x0024558c, 164)
extern "C" u32 battle_func_0024558c(s32 arg0, u32 arg1, void* arg2, u32 arg3, u32 arg4, s32 arg5, s32 arg6) {
    void* mgr = *reinterpret_cast<void**>(0x00434290);
    char* obj1 = func_00226b2c(mgr, static_cast<s16>(arg0), 0, arg1);
    obj1[4] = 0x2C;
    *reinterpret_cast<void**>(obj1 + 0x14) = arg2;
    *reinterpret_cast<u32*>(obj1 + 0x28) = arg3;
    *reinterpret_cast<u32*>(obj1 + 0x4C) = arg4;
    if (arg5 >= 0) {
        char* base = func_00293c98();
        s16 val62 = *reinterpret_cast<s16*>(static_cast<char*>(arg2) + 0x62);
        char* sub_obj = func_00282b94(base, val62);
        if (sub_obj != nullptr && arg6 >= 0) {
            char* obj2 = func_00226b2c(mgr, static_cast<s16>(arg5), 0, arg1);
            obj2[4] = 6;
            *reinterpret_cast<void**>(obj2 + 0x18) = sub_obj;
            *reinterpret_cast<s32*>(obj2 + 0x28) = arg6;
        }
    }
    return 1;
}

extern "C" s32 func_00255398(s32, u32);
extern "C" u32 func_002934d4(void*);

// DECOMP_FUNC(0x002461ec, 180)
extern "C" void* battle_func_002461ec(s32 arg0, s32 arg1, u32 arg2, void* arg3, u32 arg4) {
    char* mgr = *reinterpret_cast<char**>(0x00434290);
    char* cur = *reinterpret_cast<char**>(mgr + 8);
    while (cur != nullptr) {
        cur = *reinterpret_cast<char**>(cur + 0xC);
    }
    char* obj = func_00226b2c(mgr, static_cast<s16>(arg0), static_cast<s16>(arg1), arg2);
    obj[4] = 7;
    *reinterpret_cast<u32*>(obj + 0x28) = arg4;
    *reinterpret_cast<void**>(obj + 0x14) = arg3;
    s16 val62 = *reinterpret_cast<s16*>(static_cast<char*>(arg3) + 0x62);
    s32 val = func_00255398(val62, 1);
    *reinterpret_cast<s16*>(obj + 0x24) = static_cast<s16>(val - 1);
    if (arg4 != 4) {
        if (arg4 != 3) {
            obj[5] = static_cast<char>(obj[5] | 4);
        } else {
            char* base = func_00293c98();
            if (func_002934d4(base) != 0) {
                obj[5] = static_cast<char>(obj[5] | 4);
            }
        }
    }
    return obj;
}

extern "C" void* func_002c0ec4(u32, u32);
extern "C" s32 func_002c0e4c(void*);
extern "C" char* func_002c0e9c(void*);

// DECOMP_FUNC(0x00246ab0, 168)
extern "C" void* camp_func_00246ab0(s32 target_id) {
    void* sub_tbl = func_002c0ec4(0x2E, 2);
    s32 count = func_002c0e4c(sub_tbl);
    if (count <= 0) {
        return nullptr;
    }
    for (s32 i = 0; i < count; ++i) {
        sub_tbl = func_002c0ec4(0x2E, 2);
        char* payload = func_002c0e9c(sub_tbl);
        s32 total = func_002c0e4c(sub_tbl);
        if (i >= total) {
            return nullptr;
        }
        char* row = payload + i * 44;
        s16 id = *reinterpret_cast<s16*>(row + 0x20);
        if (id == -1) {
            return nullptr;
        }
        if (static_cast<s32>(id) == target_id) {
            return row;
        }
        sub_tbl = func_002c0ec4(0x2E, 2);
        count = func_002c0e4c(sub_tbl);
    }
    return nullptr;
}

extern "C" s32 func_002ae3f0(s16);
extern "C" s32 func_001ee3ac(void);

extern "C" s32 func_002ae3f0(s16);
extern "C" s32 func_001ee3ac(void);

// DECOMP_FUNC(0x00247170, 164)
extern "C" s32 battle_func_00247170(const void* self) {
    const u8* bytes = static_cast<const u8*>(self);
    u32 flags = *reinterpret_cast<const u32*>(bytes);
    if (flags & 0x10) {
        s16 type = *reinterpret_cast<const s16*>(bytes + 0x220);
        if (type == 2 || type == 3) {
            s16 arg = *reinterpret_cast<const s16*>(bytes + 0x222);
            if (func_002ae3f0(arg) != 0 && func_001ee3ac() != 0) {
                return 1;
            }
        }
        return 0;
    }

    for (s32 i = 0; i < 5; ++i) {
        const u8* slot = bytes + 0x228 + (i * 8);
        s16 type = *reinterpret_cast<const s16*>(slot);
        if (type == 2 || type == 3) {
            s16 arg = *reinterpret_cast<const s16*>(slot + 2);
            if (func_002ae3f0(arg) != 0 && func_001ee3ac() != 0) {
                return 1;
            }
        }
    }
    return 0;
}

extern "C" float func_002b73a4(float);
extern "C" float func_002b740c(float);

// DECOMP_FUNC(0x00248650, 156)
extern "C" void ui_func_00248650(float angle) {
    float scaled_angle = angle * 40.743663787841796875f;
    float cos_val = func_002b73a4(scaled_angle);
    float sin_val = func_002b740c(scaled_angle);

    float mat[16];
    engine_func_00256c3c(mat);
    mat[5] = cos_val;
    mat[6] = sin_val;
    mat[9] = -sin_val;
    mat[10] = cos_val;

    float* dst = reinterpret_cast<float*>(0x004EA95C);
    for (s32 i = 0; i < 16; ++i) {
        dst[i] = mat[i];
    }
}

// DECOMP_FUNC(0x0024f9e8, 172)
extern "C" void engine_func_0024f9e8(void* dst, const float* opt_vec3, u32 flag, float scale) {
    float mat[16];
    if (flag != 0) {
        engine_func_002502e8(mat, flag);
    } else {
        engine_func_00256c3c(mat);
    }

    if (scale != 1.0f) {
        float scale_vec[3] = { scale, scale, scale };
        func_00250108(mat, scale_vec, 2);
    }

    if (opt_vec3 != nullptr) {
        float trans_vec[3] = { opt_vec3[0], opt_vec3[1], opt_vec3[2] };
        func_0024ffbc(mat, trans_vec, 2);
    }

    func_0024ff28(static_cast<u8*>(dst) + 0x18, mat, 0);
}

// DECOMP_FUNC(0x00250800, 192)
extern "C" void* battle_func_00250800(s32 arg0, u32 arg1, u32 arg2, u32 arg3, u32 arg4, u32 arg5, u32 arg6) {
    void* mgr = *reinterpret_cast<void**>(0x00434290);
    char* obj = func_00226b2c(mgr, static_cast<s16>(arg0), 0, arg1);
    if (arg4 != 0 && mgr != nullptr) {
        char* curr = *reinterpret_cast<char**>(static_cast<char*>(mgr) + 8);
        while (curr != nullptr) {
            u8 type = *(reinterpret_cast<u8*>(curr) + 4);
            char* next = *reinterpret_cast<char**>(curr + 0xC);
            if (type == 0x31) {
                s16 curr_id = *reinterpret_cast<s16*>(curr);
                s16 obj_id = *reinterpret_cast<s16*>(obj);
                if (curr_id == obj_id && *reinterpret_cast<u32*>(curr + 0x2C) == arg2) {
                    s16 f2 = *reinterpret_cast<s16*>(obj + 2);
                    if (f2 >= 0) {
                        *reinterpret_cast<s16*>(obj + 2) = -1;
                        break;
                    }
                }
            }
            curr = next;
        }
    }

    *(reinterpret_cast<u8*>(obj) + 4) = 0x31;
    *reinterpret_cast<u32*>(obj + 0x2C) = arg2;
    *reinterpret_cast<u32*>(obj + 0x4C) = arg5;
    if (arg3 != 0) {
        *reinterpret_cast<u32*>(obj + 0x28) = 1;
    }
    *reinterpret_cast<u16*>(obj + 0x24) = static_cast<u16>(arg6);

    return obj;
}

extern "C" s32 func_0027e658(void*);

// DECOMP_FUNC(0x002508c0, 160)
extern "C" s32 battle_func_002508c0(s32 arg0, u32 arg1, void* arg2) {
    char* p2 = static_cast<char*>(arg2);
    u32 flags = *reinterpret_cast<u32*>(p2 + 0x50);
    if ((flags & 0x81) == 0x81) {
        void* ctx = func_00293c98();
        s16 id = *reinterpret_cast<s16*>(p2 + 0x62);
        char* sub = func_00282b94(ctx, id);
        *reinterpret_cast<u32*>(sub) |= 0x240;

        void* mgr_7e = *reinterpret_cast<void**>(0x00435D48);
        if (func_0027e658(mgr_7e) == 0 || (*reinterpret_cast<u32*>(sub) & 0x10) == 0) {
            void* mgr_22 = *reinterpret_cast<void**>(0x00434290);
            char* obj = func_00226b2c(mgr_22, static_cast<s16>(arg0), 0, arg1);
            *(reinterpret_cast<u8*>(obj) + 4) = 0x24;
            *reinterpret_cast<u32*>(obj + 0x18) = reinterpret_cast<u32>(sub);
            *reinterpret_cast<u32*>(obj + 0x28) = 1;
        }
    }
    return 1;
}

extern "C" void* func_002b0824(void*);
extern "C" s32 func_0029ee4c(void*, u32);
extern "C" s32 func_0029ed08(void*);

// DECOMP_FUNC(0x00258308, 156)
extern "C" void camp_func_00258308(void* arg0, s32 arg1, s32 arg2, u32 arg3) {
    void* obj = func_002b0824(arg0);
    if (obj != nullptr) {
        if (func_0029ee4c(obj, 10) == 0) {
            if (func_0029ee4c(obj, 2) == 0) {
                ui_func_002bf460(2, 0x24, 0x5B, arg1, arg2, arg3);
                return;
            }
        }
    }

    if (func_0029ed08(arg0) != 0) {
        ui_func_002bf460(2, 0x24, 0x5A, arg1, arg2, arg3);
    }
}

extern "C" s32 func_002a8a1c(void);
extern "C" void* func_002a8a08(void);
extern "C" void* func_002a89e4(s32);

// DECOMP_FUNC(0x0025a378, 188)
extern "C" s32 camp_func_0025a378(s32 mode, u32 bit_index) {
    u32 mask = 1u << bit_index;
    if (mode == 0 || mode == 2 || mode == 3) {
        void* p = func_002b66ec();
        u16 f72 = *reinterpret_cast<u16*>(static_cast<char*>(p) + 0x72);
        if (f72 & mask) {
            return 1;
        }
    }

    s32 count;
    const s8* arr;
    if (mode == 0 || mode == 1) {
        count = func_002a8a1c();
        char* base = static_cast<char*>(func_002a8a08());
        arr = reinterpret_cast<const s8*>(base + 0x90F0);
    } else if (mode == 2 || mode == 3) {
        count = 3;
        char* base = static_cast<char*>(func_002a8a08());
        arr = reinterpret_cast<const s8*>(base + 0x9108);
    } else {
        return 0;
    }

    for (s32 i = 0; i < count; ++i) {
        s8 idx = arr[i];
        if (idx >= 0) {
            void* obj = func_002a89e4(idx);
            u16 f44 = *reinterpret_cast<u16*>(static_cast<char*>(obj) + 0x44);
            if (f44 & mask) {
                return 1;
            }
        }
    }

    return 0;
}

extern "C" void func_002c586c(void*);
extern "C" s32 func_0025461c(void*);
extern "C" s32 func_002545c4(void*);
extern "C" s32 func_0025456c(void*);
extern "C" s32 func_002a8730(s32, s32, s32);
extern "C" s32 func_003e0eac(void*);
extern "C" s32 func_003e0f14(void*);
extern "C" s32 func_003e0f80(void*);

// DECOMP_FUNC(0x0025c1dc, 184)
extern "C" s32 func_0025c1dc(void) {
    void* p_target = *reinterpret_cast<void**>(0x0043E2B4);
    u32 target = *reinterpret_cast<u32*>(static_cast<char*>(p_target) + 4);
    if (target == 0) {
        return -1;
    }

    char time_obj[16];
    func_002c586c(time_obj);
    *reinterpret_cast<u64*>(time_obj + 8) = *reinterpret_cast<u64*>(time_obj);

    void* time_ref = time_obj + 8;
    s32 f_61c = func_0025461c(time_ref);
    s32 f_5c4 = func_002545c4(time_ref);
    s32 f_56c = func_0025456c(time_ref);

    s32 days = func_002a8730(f_56c, f_5c4, f_61c);
    s32 hours = (days * 24) + func_003e0eac(time_ref);
    s32 minutes = (hours * 60) + func_003e0f14(time_ref);
    u32 total_seconds = static_cast<u32>((minutes * 60) + func_003e0f80(time_ref));

    if (target <= total_seconds) {
        return static_cast<s32>(total_seconds - target);
    }
    return 0;
}

extern "C" s32 func_002c0ba8(s16);

// DECOMP_FUNC(0x002646d4, 160)
extern "C" void script_vm_func_002646d4(void) {
    s32 count = *reinterpret_cast<s32*>(0x00447A2C);
    if (count <= 0) {
        return;
    }

    char* base = reinterpret_cast<char*>(0x004A1264);
    for (s32 i = 0; i < count; ++i) {
        char* elem = base + (i * 0x178);
        if (*reinterpret_cast<u8*>(elem + 0x164) == 0 && *reinterpret_cast<u32*>(elem + 0x12C) != 0) {
            s16 id1 = *reinterpret_cast<s16*>(elem + 0x160);
            if (id1 != 0) {
                if (func_002c0ba8(id1) == 0) {
                    *reinterpret_cast<u8*>(elem + 0x164) = 1;
                    continue;
                }
            }
            s16 id2 = *reinterpret_cast<s16*>(elem + 0x162);
            if (id2 != 0) {
                if (func_002c0ba8(id2) != 0) {
                    *reinterpret_cast<u8*>(elem + 0x164) = 1;
                }
            }
        }
    }
}

extern "C" void func_001e5d84(u32);
extern "C" void func_00280f3c(float, float, float, float, float, float, float);

// DECOMP_FUNC(0x00264900, 192)
extern "C" void script_vm_func_00264900(s32 arg0) {
    char* table = *reinterpret_cast<char**>(0x00447A78);
    for (s32 i = 0; i < 128; ++i) {
        char* item = table + (i * 404);
        if (*reinterpret_cast<u8*>(item + 0x1D0) != 0) {
            *reinterpret_cast<u32*>(item + 0x1D8) = 1;
        }
    }

    for (s32 k = 0; k < 3; ++k) {
        func_001e5d84(1);
        if (arg0 != 0) {
            float* obj = *reinterpret_cast<float**>(0x00447E88);
            func_00280f3c(obj[10], obj[11], obj[12], obj[19], obj[13], obj[14], obj[15]);
        }
    }

    for (s32 i = 0; i < 128; ++i) {
        char* item = table + (i * 404);
        if (*reinterpret_cast<u8*>(item + 0x1D0) != 0) {
            s32 val = *reinterpret_cast<s32*>(item + 0x214);
            if (val > 0) {
                *reinterpret_cast<s32*>(item + 0x214) = 0x10;
            }
        }
    }
}


// DECOMP_FUNC(0x0026ac34, 172)
extern "C" s32 script_vm_func_0026ac34(u16 arg0, u32 arg1, const u16* arg2, u16* arg3, u32 arg4) {
    if (arg4 != 0) {
        return 0;
    }

    s32 out_count = 0;
    char* base = func_002b9364(arg0);

    for (s32 i = 0; i < 8; ++i) {
        const char* entry = base + 0x4C + (i * 4);
        u16 threshold = *reinterpret_cast<const u16*>(entry);
        u16 val = *reinterpret_cast<const u16*>(entry + 2);
        if (val != 0 && threshold > arg1) {
            bool found = false;
            for (s32 j = 0; j < 8; ++j) {
                if (arg2[j] == val) {
                    found = true;
                    break;
                }
            }
            if (!found) {
                arg3[out_count++] = val;
            }
        }
    }

    return out_count;
}

extern "C" s32 func_00259018(s32, s32, void*, s32, u32);
extern "C" s32 func_0029ac70(u16, u32);
extern "C" void battle_func_0029abc0();

// DECOMP_FUNC(0x0026c8c0, 188)
extern "C" s32 script_vm_func_0026c8c0(s32 arg0, s32 arg1, s16 arg2, s32 arg3) {
    void* r4 = reinterpret_cast<void*>(func_002ae3f0(arg2));
    if (r4 == nullptr) {
        return 1;
    }

    s32 res = func_00259018(arg0, arg1, r4, arg3, 0);
    if (res != 0 || arg3 != 0) {
        return res;
    }

    char* p;
    s32 cost;
    u16 f20 = *reinterpret_cast<u16*>(static_cast<char*>(r4) + 0x20);
    if (arg0 < 0) {
        p = static_cast<char*>(func_002b66ec());
        cost = func_0029ac70(f20, 1);
    } else {
        p = static_cast<char*>(func_002a89e4(arg0));
        cost = reinterpret_cast<s32(*)(u16)>(battle_func_0029abc0)(f20);
    }

    s32 cur = *reinterpret_cast<u16*>(p + 0x2C);
    s32 new_val = cur - cost;
    if (new_val < 0) {
        new_val = 0;
    }
    *reinterpret_cast<u16*>(p + 0x2C) = static_cast<u16>(new_val);

    return res;
}

extern "C" s32 func_0027f6fc(const float*, const float*);

// DECOMP_FUNC(0x002711e0, 160)
extern "C" void script_vm_func_002711e0(float* vec) {
    float curr[3] = { vec[0], vec[1], vec[2] };
    float prev[3] = { vec[0], vec[1], vec[2] };

    curr[1] += 1.0f;
    if (func_0027f6fc(curr, prev) == 0) {
        prev[0] = curr[0];
        prev[1] = curr[1];
        prev[2] = curr[2];

        for (s32 iter = 1; iter < 6; ++iter) {
            curr[1] -= 15.0f;
            if (func_0027f6fc(curr, prev) != 0) {
                break;
            }
            prev[0] = curr[0];
            prev[1] = curr[1];
            prev[2] = curr[2];
        }
    }

    vec[0] = curr[0];
    vec[1] = curr[1];
    vec[2] = curr[2];
}

extern "C" void func_00287a3c(void*);

// DECOMP_FUNC(0x00275a8c, 188)
extern "C" void script_vm_func_00275a8c(void) {
    char* mgr = *reinterpret_cast<char**>(0x00448C20);
    if (reinterpret_cast<u8*>(mgr)[9] == 0 || reinterpret_cast<u8*>(mgr)[8] != 0) {
        return;
    }

    s32 count = *reinterpret_cast<s32*>(mgr + 4);
    reinterpret_cast<u8*>(mgr)[8] = 1;
    if (count <= 0) {
        return;
    }

    for (s32 i = 0; i < count; ++i) {
        char* item = mgr + (i * 32);
        if (*reinterpret_cast<u8*>(item + 0x0C) != 0) {
            s16 type = *reinterpret_cast<s16*>(item + 0x1C);
            if (type == 0) {
                func_00287a3c(*reinterpret_cast<void**>(item + 0x14));
                *reinterpret_cast<void**>(item + 0x14) = nullptr;
            } else if (type == 1) {
                if (*reinterpret_cast<void**>(item + 0x18) != nullptr) {
                    func_00287a3c(*reinterpret_cast<void**>(item + 0x14));
                    *reinterpret_cast<void**>(item + 0x18) = nullptr;
                    *reinterpret_cast<u16*>(item + 0x1E) = 0;
                    *reinterpret_cast<void**>(item + 0x14) = nullptr;
                }
            }
        }
    }
}

// DECOMP_FUNC(0x002760bc, 180)
extern "C" void script_vm_func_002760bc(void) {
    char* objA = reinterpret_cast<char*>(0x0049F91C);
    if (*reinterpret_cast<u8*>(objA + 0x284) != 0) {
        *reinterpret_cast<u8*>(objA + 0x284) = 0;
        return;
    }

    char* objB = *reinterpret_cast<char**>(0x00447E28);
    char* objC = *reinterpret_cast<char**>(0x00447E88);
    char* objD = *reinterpret_cast<char**>(0x004474F4);

    *reinterpret_cast<u8*>(objA + 0x2F8) = 1;
    *reinterpret_cast<u32*>(objA + 0x2FC) = *reinterpret_cast<u32*>(objB + 0x2C);
    *reinterpret_cast<u32*>(objA + 0x300) = *reinterpret_cast<u32*>(objB + 0x30);
    *reinterpret_cast<u32*>(objA + 0x304) = *reinterpret_cast<u32*>(objA + 8);

    *reinterpret_cast<float*>(objA + 0x308) = *reinterpret_cast<float*>(objC + 0x1C);
    *reinterpret_cast<float*>(objA + 0x30C) = *reinterpret_cast<float*>(objC + 0x20);
    *reinterpret_cast<float*>(objA + 0x310) = *reinterpret_cast<float*>(objC + 0x24);
    *reinterpret_cast<u32*>(objA + 0x314) = *reinterpret_cast<u32*>(objC + 0x4C);
    *reinterpret_cast<u32*>(objA + 0x318) = *reinterpret_cast<u32*>(objD + 0x18);

    *reinterpret_cast<u32*>(objA + 0x31C) = *reinterpret_cast<u32*>(objB + 0x2C);
    *reinterpret_cast<u32*>(objA + 0x320) = *reinterpret_cast<u32*>(objB + 0x30);
    *reinterpret_cast<float*>(objA + 0x324) = *reinterpret_cast<float*>(objC + 0x1C);
    *reinterpret_cast<float*>(objA + 0x328) = *reinterpret_cast<float*>(objC + 0x20);
    *reinterpret_cast<float*>(objA + 0x32C) = *reinterpret_cast<float*>(objC + 0x24);
    *reinterpret_cast<u32*>(objA + 0x330) = *reinterpret_cast<u32*>(objC + 0x4C);
    *reinterpret_cast<u32*>(objA + 0x334) = *reinterpret_cast<u32*>(objD + 0x18);
}

extern "C" void func_00296d8c(void*, u32, s32, u32, u32, s32, s32);
extern "C" float func_002594f0(void*);
extern "C" void func_002bdac0(void*, u32);
extern "C" s32 func_002bef7c(void*);

// DECOMP_FUNC(0x0027ea24, 192)
extern "C" void script_vm_func_0027ea24(s32 arg0, s32 arg1) {
    char* r4 = *reinterpret_cast<char**>(0x0043E128);
    if (arg0 == 0) {
        *reinterpret_cast<u8*>(r4 + 0x21) = 0;
        return;
    }

    *reinterpret_cast<u8*>(r4 + 0x21) = 1;
    void* sub_1b8 = *reinterpret_cast<void**>(r4 + 0x1B8);
    func_00296d8c(sub_1b8, 3, -1, 0, 3, arg0, arg1);
    float f = func_002594f0(sub_1b8);

    if (f > 630.0f) {
        *reinterpret_cast<u8*>(r4 + 0x22) = 1;
        *reinterpret_cast<s32*>(r4 + 0x14) = static_cast<s32>(f);
    } else {
        *reinterpret_cast<u8*>(r4 + 0x22) = 0;
    }

    char* d0 = r4 + 0xD0;
    func_002bdac0(d0, 2);
    s32 r0 = func_002bef7c(d0);
    *reinterpret_cast<s32*>(r4 + 0x18) = r0;
    s32 r1 = *reinterpret_cast<s32*>(r4 + 0x14);
    *reinterpret_cast<s32*>(r4 + 0x1C) = r0 + r1 + 0x2A;

    if (*reinterpret_cast<s32*>(r4 + 8) == 3) {
        *reinterpret_cast<s32*>(r4 + 8) = 2;
    }
    *reinterpret_cast<s32*>(r4 + 0x10) = 0x1E;
}

extern "C" void* func_002c34a4(u32, u32, u32, u32, u32, u32);

// DECOMP_FUNC(0x00282944, 172)
extern "C" void ui_func_00282944(u32 arg0, u32 arg1, u32 arg2, u32 arg3, u32 arg4, u32 arg5) {
    char* node = static_cast<char*>(func_002c34a4(0x10000, 0x100, 0, 0x68, 0x10, 1));
    *reinterpret_cast<void**>(node) = nullptr;
    *reinterpret_cast<u32*>(node + 4) = 5;
    *reinterpret_cast<u32*>(node + 8) = arg0;
    *reinterpret_cast<u32*>(node + 0x0C) = arg1;
    *reinterpret_cast<u32*>(node + 0x10) = arg2;
    *reinterpret_cast<u32*>(node + 0x14) = arg3;
    *reinterpret_cast<u32*>(node + 0x18) = arg4;
    *reinterpret_cast<u32*>(node + 0x1C) = arg5;

    char* list = reinterpret_cast<char*>(0x004EA7D4);
    char* head = *reinterpret_cast<char**>(list + 0x0C);
    char** p_tail = reinterpret_cast<char**>(list + 0x20);
    if (head == nullptr) {
        *reinterpret_cast<char**>(list + 0x0C) = node;
    } else {
        *reinterpret_cast<char**>(*p_tail) = node;
    }
    *p_tail = node;
}

// DECOMP_FUNC(0x002829f0, 160)
extern "C" void ui_func_002829f0(u32 arg0, u32 arg1, u32 arg2, u32 arg3) {
    char* node = static_cast<char*>(func_002c34a4(0x10000, 0x100, 0, 0x68, 0x10, 1));
    *reinterpret_cast<void**>(node) = nullptr;
    *reinterpret_cast<u32*>(node + 4) = 5;
    *reinterpret_cast<u32*>(node + 8) = arg0;
    *reinterpret_cast<u32*>(node + 0x0C) = arg1;
    *reinterpret_cast<u32*>(node + 0x10) = arg2;
    *reinterpret_cast<u32*>(node + 0x14) = arg3;
    *reinterpret_cast<u32*>(node + 0x18) = 0xFFFFC040;
    *reinterpret_cast<u32*>(node + 0x1C) = 0xC0000000;

    char* list = reinterpret_cast<char*>(0x004EA7D4);
    char* head = *reinterpret_cast<char**>(list + 0x0C);
    char** p_tail = reinterpret_cast<char**>(list + 0x20);
    if (head == nullptr) {
        *reinterpret_cast<char**>(list + 0x0C) = node;
    } else {
        *reinterpret_cast<char**>(*p_tail) = node;
    }
    *p_tail = node;
}

extern "C" s32 func_002c583c(u32);

// DECOMP_FUNC(0x002876d0, 192)
extern "C" s32 ui_func_002876d0(u32 arg0) {
    if (func_002c583c(1) != 0) {
        return 0;
    }

    const char* mgr = reinterpret_cast<const char*>(0x004C53C4);
    u32 flags1 = *reinterpret_cast<const u32*>(mgr + 0x1C);
    if ((flags1 & 1) != 0) {
        if (*reinterpret_cast<const u32*>(mgr + 0x0C) == arg0) {
            if ((flags1 & 0x30) != 0) {
                return 3;
            }
            if ((flags1 & 2) != 0 && (flags1 & 8) == 0) {
                return 1;
            }
        } else if (*reinterpret_cast<const u32*>(mgr + 0x10) == arg0) {
            return 3;
        }
    }

    u32 flags2 = *reinterpret_cast<const u32*>(mgr + 0x3C);
    if ((flags2 & 1) != 0) {
        if (*reinterpret_cast<const u32*>(mgr + 0x2C) == arg0) {
            if ((flags2 & 0x30) != 0) {
                return 3;
            }
            if ((flags2 & 2) != 0 && (flags2 & 8) == 0) {
                return 1;
            }
        } else if (*reinterpret_cast<const u32*>(mgr + 0x30) == arg0) {
            return 3;
        }
    }

    return 0;
}

extern "C" char* func_002c2b1c(void);

// DECOMP_FUNC(0x002891e0, 192)
extern "C" s32 engine_func_002891e0(s32 arg0) {
    char* p = func_002c2b1c();

    if ((static_cast<u32>(arg0 - 0x19) <= 5) || arg0 == 0x66) {
        if (func_002c0ba8(0x144) == 0) {
            return 3;
        }
    } else if ((static_cast<u32>(arg0 - 0x1F) <= 4) || arg0 == 0x67) {
        if (func_002c0ba8(0x15A) == 0) {
            return 3;
        }
    }

    char* p2 = func_002c2b1c();
    if (reinterpret_cast<u8*>(p2)[3] == 1) {
        if (reinterpret_cast<u8*>(p)[0xE3D] != 3) {
            return 1;
        }
        return 0;
    }

    if (arg0 == 0x18) {
        return 2;
    }
    if (arg0 >= 0x40) {
        return 0;
    }

    if (reinterpret_cast<u8*>(p)[0xE14 + arg0] == 3) {
        return 0;
    }
    return 1;
}

// DECOMP_FUNC(0x0028d4f0, 156)
extern "C" __attribute__((naked)) void camp_func_0028d4f0() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe2800b0b\n.inst 0xe2800fcd\n.inst 0xe5906000\n.inst 0xe2460001\n.inst 0xe3500003\n.inst 0x83a06000\n.inst 0x81a04006\n.inst 0x9a000007\n.inst 0xe1a00004\n.inst 0xebff874e\n.inst 0xe1d004b8\n.inst 0xe2844001\n.inst 0xe3500000\n.inst 0x12866001\n.inst 0xe354000c\n.inst 0xbafffff7\n.inst 0xe3560001\n.inst 0xba000010\n.inst 0xe1d50bf4\n.inst 0xe3a04000\n.inst 0xe3500000\n.inst 0xda00000c\n.inst 0xe0850084\n.inst 0xe1d078bc\n.inst 0xe1a00007\n.inst 0xeb0083a3\n.inst 0xe5d0004b\n.inst 0xe1500006\n.inst 0x1a000001\n.inst 0xe1a00007\n.inst 0xe8bd81f0\n.inst 0xe1d50bf4\n.inst 0xe2844001\n.inst 0xe1500004\n.inst 0xcafffff2\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x00290374, 156)
extern "C" __attribute__((naked)) void script_vm_func_00290374() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xeb009ab8\n.inst 0xe2805c06\n.inst 0xe1a06000\n.inst 0xe1d500b8\n.inst 0xe3a07000\n.inst 0xe3100001\n.inst 0x0a000016\n.inst 0xeb009ab1\n.inst 0xe1a04000\n.inst 0xe2800c06\n.inst 0xe1d000b8\n.inst 0xe3100001\n.inst 0x0a000010\n.inst 0xe1d404b6\n.inst 0xe2401c02\n.inst 0xe25110a3\n.inst 0x1a000003\n.inst 0xe59f0044\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xebffe57d\n.inst 0xe1d404b6\n.inst 0xe2401c02\n.inst 0xe25110a5\n.inst 0x1a000003\n.inst 0xe59f0028\n.inst 0xe3a02001\n.inst 0xe3a01000\n.inst 0xebffe575\n.inst 0xe1c474b6\n.inst 0xe1d500b8\n.inst 0xe3c00001\n.inst 0xe1c500b8\n.inst 0xe1c674b6\n.inst 0xe1c570b4\n.inst 0xe8bd81f0\n.word 0x00000262\n.word 0x00000263\n");
}

// DECOMP_FUNC(0x002911ec, 192)
extern "C" __attribute__((naked)) void script_vm_func_002911ec() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe3a00001\n.inst 0xeb00d18f\n.inst 0xe3500000\n.inst 0x1a00001f\n.inst 0xe59f0094\n.inst 0xe59f2094\n.inst 0xe3a0301e\n.inst 0xe590101c\n.inst 0xe3110002\n.inst 0x0a00000d\n.inst 0xe3110020\n.inst 0x0a000006\n.inst 0xe3c11020\n.inst 0xe3811040\n.inst 0xe580101c\n.inst 0xe5804004\n.inst 0xe5900000\n.inst 0xe5820004\n.inst 0xea000004\n.inst 0xe3110b01\n.inst 0x1a000002\n.inst 0xe5a03008\n.inst 0xe3811008\n.inst 0xe5801014\n.inst 0xe59f004c\n.inst 0xe590101c\n.inst 0xe3110002\n.inst 0x0a000007\n.inst 0xe3110020\n.inst 0x0a000006\n.inst 0xe3c11020\n.inst 0xe3811040\n.inst 0xe580101c\n.inst 0xe5804004\n.inst 0xe5900000\n.inst 0xe5820004\n.inst 0xe8bd8010\n.inst 0xe3110b01\n.inst 0x1afffffc\n.inst 0xe5a03008\n.inst 0xe3811008\n.inst 0xe5801014\n.inst 0xe8bd8010\n.word 0x004c53c4\n.word 0x0044e098\n.word 0x004c53e4\n");
}

// DECOMP_FUNC(0x002956c0, 160)
extern "C" __attribute__((naked)) void script_vm_func_002956c0() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe2800b0d\n.inst 0xe2800f5d\n.inst 0xe5900000\n.inst 0xeb0047a0\n.inst 0xe59f0074\n.inst 0xe7900004\n.inst 0xeb00bb1e\n.inst 0xebfef3d1\n.inst 0xe59f3068\n.inst 0xe2841b33\n.inst 0xe3a0c000\n.inst 0xe2811fde\n.inst 0xe7c3c004\n.inst 0xe5910000\n.inst 0xe59f2054\n.inst 0xe2800001\n.inst 0xe5810000\n.inst 0xe7921004\n.inst 0xe1510000\n.inst 0x1a000004\n.inst 0xe3a01014\n.inst 0xe1a00004\n.inst 0xeb0004bc\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.inst 0xe3a00001\n.inst 0xeb0024f7\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xeb0024b9\n.inst 0xe3a01009\n.inst 0xe1a00004\n.inst 0xeb0004b2\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.word 0x00003578\n.word 0x0000d640\n.word 0x0000cf74\n");
}

// DECOMP_FUNC(0x00296020, 168)
extern "C" __attribute__((naked)) void script_vm_func_00296020() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1b04000\n.inst 0xe3e06000\n.inst 0x0a00000d\n.inst 0xeb004a74\n.inst 0xe2800090\n.inst 0xe3a05000\n.inst 0xe1500004\n.inst 0x0a000009\n.inst 0xe5d0104a\n.inst 0xe5d4204a\n.inst 0xe1510002\n.inst 0x0a000005\n.inst 0xe2855001\n.inst 0xe2800b01\n.inst 0xe3550018\n.inst 0xe2800f81\n.inst 0xbafffff4\n.inst 0xe1a05006\n.inst 0xe320f000\n.inst 0xeb004a64\n.inst 0xe2800a09\n.inst 0xe2800f42\n.inst 0xe1d010d0\n.inst 0xe3510000\n.inst 0xba000001\n.inst 0xe1510005\n.inst 0x0a000009\n.inst 0xe1d010d1\n.inst 0xe3510000\n.inst 0xba000001\n.inst 0xe1510005\n.inst 0x0a000004\n.inst 0xe1d000d2\n.inst 0xe3500000\n.inst 0xba000003\n.inst 0xe1500005\n.inst 0x1a000001\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002971e4, 160)
extern "C" __attribute__((naked)) void script_vm_func_002971e4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe2515000\n.inst 0xe1a04000\n.inst 0xba000004\n.inst 0xe59400b0\n.inst 0xe5900008\n.inst 0xe1500005\n.inst 0xc3a00000\n.inst 0xca000001\n.inst 0xe3a00000\n.inst 0xe8bd8070\n.inst 0xe59410b4\n.inst 0xe0802285\n.inst 0xe19110d2\n.inst 0xe3510000\n.inst 0xe7c41000\n.inst 0x12800001\n.inst 0x1afffff8\n.inst 0xe59400b4\n.inst 0xe3a01018\n.inst 0xe0811285\n.inst 0xe3a06000\n.inst 0xe7900001\n.inst 0xe584601c\n.inst 0xe5846020\n.inst 0xe5846024\n.inst 0xe5846028\n.inst 0xe584602c\n.inst 0xe5846030\n.inst 0xe5846034\n.inst 0xe5840018\n.inst 0xe3a01070\n.inst 0xe284003c\n.inst 0xe5846038\n.inst 0xeb00b62f\n.inst 0xe28400c8\n.inst 0xe8800060\n.inst 0xe3a00001\n.inst 0xe58460d0\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002994b4, 164)
extern "C" __attribute__((naked)) void engine_func_002994b4() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a07000\n.inst 0xe3a09000\n.inst 0xe1a0a001\n.inst 0xe1a08009\n.inst 0xebfde077\n.inst 0xe2506000\n.inst 0xe3a04000\n.inst 0x9a00001d\n.inst 0xe1a00004\n.inst 0xeb01dc90\n.inst 0xe1b05000\n.inst 0xe320f000\n.inst 0x0a000015\n.inst 0xe5d50001\n.inst 0xe1500007\n.inst 0x1a000012\n.inst 0xe1d505b6\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xeb009da7\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000b\n.inst 0xe1d505b8\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xebffe729\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe158000a\n.inst 0x12888001\n.inst 0x1a000001\n.inst 0xe5d59000\n.inst 0xea000002\n.inst 0xe2844001\n.inst 0xe1540006\n.inst 0x3affffe1\n.inst 0xe1a00009\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x002998d8, 156)
extern "C" __attribute__((naked)) void ui_func_002998d8() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4088\n.inst 0xe3500000\n.inst 0xe2842000\n.inst 0xe594c004\n.inst 0xe5922004\n.inst 0xe2823d7a\n.inst 0x0a000004\n.inst 0xe3500001\n.inst 0x0a000007\n.inst 0xe3500002\n.inst 0x0a00000b\n.inst 0xea000010\n.inst 0xe5930000\n.inst 0xe1a02001\n.inst 0xe3a03007\n.inst 0xe3a01000\n.inst 0xea000003\n.inst 0xe5930000\n.inst 0xe1a02001\n.inst 0xe3a03007\n.inst 0xe3a01001\n.inst 0xebffebc4\n.inst 0xea000005\n.inst 0xe28ccd7a\n.inst 0xe1a02001\n.inst 0xe59c0000\n.inst 0xe3a03007\n.inst 0xe3a01002\n.inst 0xebffebbd\n.inst 0xe5940004\n.inst 0xe59f3014\n.inst 0xe3a02000\n.inst 0xe3a01006\n.inst 0xe5802010\n.inst 0xe7831000\n.inst 0xe8bd8010\n.word 0x0044e140\n.word 0x000012dc\n");
}

// DECOMP_FUNC(0x0029abc0, 176)
extern "C" __attribute__((naked)) void battle_func_0029abc0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xeb004e09\n.inst 0xe3500000\n.inst 0x15d05022\n.inst 0x13a04000\n.inst 0x0a000024\n.inst 0xe3a0000c\n.inst 0xebffe17a\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe3a0000c\n.inst 0xeb004f09\n.inst 0xe5904038\n.inst 0xe3a0000d\n.inst 0xebffe173\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3a0000d\n.inst 0xeb004f01\n.inst 0xe5900038\n.inst 0xe0844000\n.inst 0xe3a0000e\n.inst 0xebffe16a\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3a0000e\n.inst 0xeb004ef8\n.inst 0xe5900038\n.inst 0xe0844000\n.inst 0xe3a0000f\n.inst 0xebffe161\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000003\n.inst 0xe3a0000f\n.inst 0xeb004eef\n.inst 0xe5900038\n.inst 0xe0844000\n.inst 0xe0450004\n.inst 0xe3500000\n.inst 0xd3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x0029c49c, 156)
extern "C" __attribute__((naked)) void camp_func_0029c49c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xeb003158\n.inst 0xe1a04000\n.inst 0xeb003156\n.inst 0xe1a02000\n.inst 0xe3a01000\n.inst 0xe1a00001\n.inst 0xe0823000\n.inst 0xe2833a09\n.inst 0xe1d33fd0\n.inst 0xe3530000\n.inst 0xba000003\n.inst 0xe2800001\n.inst 0xe3500018\n.inst 0xe2811001\n.inst 0xbafffff6\n.inst 0xe59f0050\n.inst 0xe7d00004\n.inst 0xe1510000\n.inst 0xaa00000d\n.inst 0xeb003145\n.inst 0xe1a05000\n.inst 0xe3a04000\n.inst 0xe0840384\n.inst 0xe0800404\n.inst 0xe0850100\n.inst 0xe2800090\n.inst 0xeb0481b4\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000004\n.inst 0xe2844001\n.inst 0xe3540018\n.inst 0xbafffff4\n.inst 0xe3e00000\n.inst 0xe8bd8070\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.word 0x0000910b\n");
}

// DECOMP_FUNC(0x0029e19c, 172)
extern "C" __attribute__((naked)) void camp_func_0029e19c() {
    asm volatile(".arm\n.inst 0xe59f209c\n.inst 0xe92d4070\n.inst 0xe3500000\n.inst 0xe24dde61\n.inst 0xe5924004\n.inst 0xe3a05001\n.inst 0xaa000007\n.inst 0xeb00614b\n.inst 0xe1a01000\n.inst 0xe2840c13\n.inst 0xebfebe65\n.inst 0xe2840c1e\n.inst 0xe2800066\n.inst 0xe3a01000\n.inst 0xea00000b\n.inst 0xe3510000\n.inst 0xe1a0600d\n.inst 0xe6ff0070\n.inst 0xe1a01006\n.inst 0x0a000008\n.inst 0xebff3233\n.inst 0xe1a01006\n.inst 0xe2840c13\n.inst 0xebfebdf9\n.inst 0xe2840c1e\n.inst 0xe3a01006\n.inst 0xe2800066\n.inst 0xe5c01000\n.inst 0xea000006\n.inst 0xe320f000\n.inst 0xebffff3e\n.inst 0xe1a01006\n.inst 0xe2840c13\n.inst 0xebfebdef\n.inst 0xe59f0018\n.inst 0xe7c05004\n.inst 0xe2844b07\n.inst 0xe2844fae\n.inst 0xe5c45000\n.inst 0xe28dde61\n.inst 0xe8bd8070\n.word 0x0044e140\n.word 0x00001e66\n");
}

// DECOMP_FUNC(0x0029ec6c, 156)
extern "C" __attribute__((naked)) void ui_func_0029ec6c() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe3500c05\n.inst 0xe1a04000\n.inst 0x8a00001f\n.inst 0xeb0046fe\n.inst 0xe1a01000\n.inst 0xe1d001b6\n.inst 0xe2100001\n.inst 0x0a000016\n.inst 0xe59f006c\n.inst 0xe0843104\n.inst 0xe5902004\n.inst 0xe0830184\n.inst 0xe0820100\n.inst 0xe2800903\n.inst 0xe2800f7e\n.inst 0xe5d00016\n.inst 0xe2100002\n.inst 0x1a00000b\n.inst 0xe0813080\n.inst 0xe1d337bc\n.inst 0xe3530000\n.inst 0x0a000009\n.inst 0xe083c103\n.inst 0xe08c3183\n.inst 0xe0823103\n.inst 0xe2833903\n.inst 0xe2833f7e\n.inst 0xe5d33016\n.inst 0xe3130002\n.inst 0x0a000001\n.inst 0xe3a00001\n.inst 0xe8bd8010\n.inst 0xe2800001\n.inst 0xe3500003\n.inst 0x3affffee\n.inst 0xe3a00000\n.inst 0xe8bd8010\n.word 0x0043e2a8\n");
}

// DECOMP_FUNC(0x0029ed44, 184)
extern "C" __attribute__((naked)) void camp_func_0029ed44() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe24dd038\n.inst 0xe1a00001\n.inst 0xeb006983\n.inst 0xe1b04000\n.inst 0x0a000024\n.inst 0xe594002c\n.inst 0xe3100602\n.inst 0x1a000021\n.inst 0xe1d403b6\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xeb00878b\n.inst 0xe3500000\n.inst 0x0a00001b\n.inst 0xe1d403b4\n.inst 0xe3100001\n.inst 0x0a000014\n.inst 0xe3d01001\n.inst 0x0a000009\n.inst 0xe1a000a0\n.inst 0xe1a0100d\n.inst 0xebffa586\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000010\n.inst 0xe1dd02be\n.inst 0xe31000fc\n.inst 0x0a00000d\n.inst 0xea000008\n.inst 0xe1d400b0\n.inst 0xe1a0100d\n.inst 0xebffa57c\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000006\n.inst 0xe1dd02be\n.inst 0xe31000fc\n.inst 0x0a000003\n.inst 0xe1d400b6\n.inst 0xe3100001\n.inst 0x13a00001\n.inst 0x1a000000\n.inst 0xe3a00000\n.inst 0xe28dd038\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002a0de8, 192)
extern "C" __attribute__((naked)) void camp_func_002a0de8() {
    asm volatile(".arm\n.inst 0xe59f00ac\n.inst 0xe92d4030\n.inst 0xe24dd01c\n.inst 0xe5904000\n.inst 0xe3540000\n.inst 0x0a000024\n.inst 0xe2840b01\n.inst 0xe2800f42\n.inst 0xe2845b01\n.inst 0xe8900007\n.inst 0xe28dc010\n.inst 0xeddf0a21\n.inst 0xe28d300c\n.inst 0xe88d0007\n.inst 0xe2840b01\n.inst 0xe2800f45\n.inst 0xed950a4b\n.inst 0xec901a03\n.inst 0xe1a00004\n.inst 0xee211a00\n.inst 0xee611a80\n.inst 0xee220a00\n.inst 0xed9d2a00\n.inst 0xee321a01\n.inst 0xed8d1a00\n.inst 0xee011a10\n.inst 0xe2841b01\n.inst 0xe2811f42\n.inst 0xee311a21\n.inst 0xed8d1a01\n.inst 0xee012a10\n.inst 0xe1a0200d\n.inst 0xee310a00\n.inst 0xed8d0a02\n.inst 0xed9f0a0b\n.inst 0xedcd0a03\n.inst 0xec8c0a02\n.inst 0xeb008489\n.inst 0xe2855e13\n.inst 0xe3a01000\n.inst 0xec950a03\n.inst 0xe1a00004\n.inst 0xebfce8fd\n.inst 0xe28dd01c\n.inst 0xe8bd8030\n.word 0x0044e178\n.word 0x00000000\n.word 0x3f800000\n");
}

// DECOMP_FUNC(0x002a32bc, 192)
extern "C" __attribute__((naked)) void engine_func_002a32bc() {
    asm volatile(".arm\n.inst 0xe59f10b4\n.inst 0xe3a020ff\n.inst 0xe5801000\n.inst 0xe3a01000\n.inst 0xe5801004\n.inst 0xe5c01008\n.inst 0xe580100c\n.inst 0xe5c02010\n.inst 0xe5801014\n.inst 0xe5801018\n.inst 0xe580101c\n.inst 0xe5801020\n.inst 0xe58010b0\n.inst 0xe58010b4\n.inst 0xe5801030\n.inst 0xe5801034\n.inst 0xe5801038\n.inst 0xe580103c\n.inst 0xe5801040\n.inst 0xe5801044\n.inst 0xe5801048\n.inst 0xe580104c\n.inst 0xe5801050\n.inst 0xe5801054\n.inst 0xe5801058\n.inst 0xe580105c\n.inst 0xe5801060\n.inst 0xe5801064\n.inst 0xe5801068\n.inst 0xe580106c\n.inst 0xe5801070\n.inst 0xe5801074\n.inst 0xe5801078\n.inst 0xe580107c\n.inst 0xe5801080\n.inst 0xe5801084\n.inst 0xe5801088\n.inst 0xe580108c\n.inst 0xe5801090\n.inst 0xe5801094\n.inst 0xe5801098\n.inst 0xe580109c\n.inst 0xe58010a0\n.inst 0xe58010a4\n.inst 0xe58010a8\n.inst 0xe58010ac\n.inst 0xe12fff1e\n.word 0x00421e74\n");
}

// DECOMP_FUNC(0x002a3ff8, 164)
extern "C" __attribute__((naked)) void engine_func_002a3ff8() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe1a04000\n.inst 0xe3a01080\n.inst 0xeb0082c9\n.inst 0xe3a00000\n.inst 0xe5840000\n.inst 0xe5840004\n.inst 0xed9f0a1d\n.inst 0xe5840008\n.inst 0xe584000c\n.inst 0xed840a03\n.inst 0xe5840010\n.inst 0xe5840014\n.inst 0xe5840018\n.inst 0xe584001c\n.inst 0xed840a07\n.inst 0xe5840040\n.inst 0xe5840044\n.inst 0xe5840048\n.inst 0xeddf0a12\n.inst 0xe584004c\n.inst 0xed840a13\n.inst 0xedc40a11\n.inst 0xe5840050\n.inst 0xe5840054\n.inst 0xe59f2034\n.inst 0xe5840058\n.inst 0xe584005c\n.inst 0xed840a17\n.inst 0xe3e00000\n.inst 0xecd20a04\n.inst 0xe2842020\n.inst 0xe3a01080\n.inst 0xed840a18\n.inst 0xed840a1d\n.inst 0xecc20a04\n.inst 0xe1c406f4\n.inst 0xe8bd8010\n.word 0x3f800000\n.word 0x40a00000\n.word 0x00472520\n");
}

// DECOMP_FUNC(0x002a4e50, 160)
extern "C" __attribute__((naked)) void ui_func_002a4e50() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe1a04000\n.inst 0xe1a08002\n.inst 0xe1a09003\n.inst 0xe59d0024\n.inst 0xe59d5020\n.inst 0xe5840014\n.inst 0xe0810005\n.inst 0xe2400001\n.inst 0xe1a01005\n.inst 0xeb008764\n.inst 0xe0060590\n.inst 0xe0880005\n.inst 0xe2400001\n.inst 0xe1a01005\n.inst 0xe5846018\n.inst 0xeb00875e\n.inst 0xe0070590\n.inst 0xe0880009\n.inst 0xe1a01006\n.inst 0xe0400007\n.inst 0xe584701c\n.inst 0xeb008758\n.inst 0xe0010690\n.inst 0xe3a00000\n.inst 0xe5841020\n.inst 0xe0811007\n.inst 0xe0411006\n.inst 0xe584002c\n.inst 0xe1570001\n.inst 0xe5845028\n.inst 0x8a000005\n.inst 0xe5810000\n.inst 0xe1c421d8\n.inst 0xe1a00001\n.inst 0xe0411002\n.inst 0xe1530001\n.inst 0x9afffff9\n.inst 0xe5840024\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x002a6fa0, 172)
extern "C" __attribute__((naked)) void script_vm_func_002a6fa0() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe3710001\n.inst 0xe1a08000\n.inst 0xe1a04001\n.inst 0xe1a06002\n.inst 0x0a000022\n.inst 0xe5980310\n.inst 0xe3a07000\n.inst 0xe3500000\n.inst 0xda00001e\n.inst 0xe5980318\n.inst 0xe0871107\n.inst 0xe0809201\n.inst 0xe1a00009\n.inst 0xeb0014f6\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000012\n.inst 0xe1a00009\n.inst 0xeb0014e4\n.inst 0xe1a05000\n.inst 0xe1a00009\n.inst 0xeb0014d4\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0x9a00000a\n.inst 0xe0852300\n.inst 0xe1d230d0\n.inst 0xe1530004\n.inst 0x0592203c\n.inst 0x01520006\n.inst 0x1a000001\n.inst 0xe0850300\n.inst 0xe8bd87f0\n.inst 0xe2800001\n.inst 0xe1500001\n.inst 0x3afffff4\n.inst 0xe5980310\n.inst 0xe2877001\n.inst 0xe1500007\n.inst 0xcaffffe0\n.inst 0xe3a00000\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x002a7094, 176)
extern "C" __attribute__((naked)) void func_002a7094() {
    asm volatile(".arm\n.inst 0xe92d47f0\n.inst 0xe3710001\n.inst 0xe1a08000\n.inst 0xe1a04001\n.inst 0xe1a06002\n.inst 0x0a000023\n.inst 0xe5980310\n.inst 0xe3a07000\n.inst 0xe3500000\n.inst 0xda00001f\n.inst 0xe5980318\n.inst 0xe0871107\n.inst 0xe0809201\n.inst 0xe1a00009\n.inst 0xeb0014b9\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000013\n.inst 0xe1a00009\n.inst 0xeb0014a7\n.inst 0xe1a05000\n.inst 0xe1a00009\n.inst 0xeb001497\n.inst 0xe2501000\n.inst 0xe3a00000\n.inst 0x9a00000b\n.inst 0xe0852300\n.inst 0xe1d230d0\n.inst 0xe1530004\n.inst 0x0592203c\n.inst 0x01520006\n.inst 0x1a000002\n.inst 0xe599104c\n.inst 0xe0810200\n.inst 0xe8bd87f0\n.inst 0xe2800001\n.inst 0xe1500001\n.inst 0x3afffff3\n.inst 0xe5980310\n.inst 0xe2877001\n.inst 0xe1500007\n.inst 0xcaffffdf\n.inst 0xe3a00000\n.inst 0xe8bd87f0\n");
}

// DECOMP_FUNC(0x002a7e08, 180)
extern "C" __attribute__((naked)) void engine_func_002a7e08() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe3a00000\n.inst 0xe5840000\n.inst 0xe5840004\n.inst 0xe5840008\n.inst 0xe1b05001\n.inst 0xe1a06002\n.inst 0xe5c4000c\n.inst 0x0a00001e\n.inst 0xe5950000\n.inst 0xe59f1078\n.inst 0xe1500001\n.inst 0x1a00001a\n.inst 0xe5950008\n.inst 0xe3500401\n.inst 0x1a000017\n.inst 0xe1a00005\n.inst 0xe5845000\n.inst 0xebfab626\n.inst 0xe1a01000\n.inst 0xe2811008\n.inst 0xe3a00001\n.inst 0xe5841004\n.inst 0xe3560000\n.inst 0xe5c4000c\n.inst 0x0a00000d\n.inst 0xe3500000\n.inst 0x0a00000b\n.inst 0xe5946000\n.inst 0xe1a00006\n.inst 0xebffffd3\n.inst 0xe59f1028\n.inst 0xe7960000\n.inst 0xe1500001\n.inst 0x1a000004\n.inst 0xe5940000\n.inst 0xebffffcd\n.inst 0xe2800004\n.inst 0xe0800005\n.inst 0xe5840008\n.inst 0xe1a00004\n.inst 0xe8bd8070\n.word 0x52415743\n.word 0x54415743\n");
}

// DECOMP_FUNC(0x002ac614, 188)
extern "C" __attribute__((naked)) void engine_func_002ac614() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05000\n.inst 0xe1a04001\n.inst 0xe5900004\n.inst 0xe1a01002\n.inst 0xe1a06003\n.inst 0xebfa8286\n.inst 0xe1a01006\n.inst 0xebfa8291\n.inst 0xe1a06000\n.inst 0xe5950004\n.inst 0xebfa827e\n.inst 0xe5902000\n.inst 0xe5961000\n.inst 0xe1520001\n.inst 0x9a00001c\n.inst 0xe0800181\n.inst 0xe2900004\n.inst 0x0a000019\n.inst 0xe5901000\n.inst 0xe5841000\n.inst 0xe5900004\n.inst 0xe5840004\n.inst 0xe1a00006\n.inst 0xebfa82be\n.inst 0xed840a05\n.inst 0xe1a00006\n.inst 0xebfa828d\n.inst 0xe1a01000\n.inst 0xe2840008\n.inst 0xebffee4c\n.inst 0xe1a00006\n.inst 0xebfa8297\n.inst 0xe5c4000d\n.inst 0xe1a00006\n.inst 0xebfa82a9\n.inst 0xe5c4000e\n.inst 0xe1a00006\n.inst 0xebfa829b\n.inst 0xe5c4000f\n.inst 0xe1a00006\n.inst 0xebfa82ca\n.inst 0xe5c40010\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002ad4fc, 164)
extern "C" __attribute__((naked)) void func_002ad4fc() {
    asm volatile(".arm\n.inst 0xed9f3a23\n.inst 0xee715ac1\n.inst 0xee314a81\n.inst 0xee706ac0\n.inst 0xee704a80\n.inst 0xeddf0a21\n.inst 0xee326ac2\n.inst 0xed9f5a1d\n.inst 0xedc00a0e\n.inst 0xee623a82\n.inst 0xed9f0a1b\n.inst 0xee222a05\n.inst 0xed800a01\n.inst 0xed800a03\n.inst 0xeec30a26\n.inst 0xed800a04\n.inst 0xed800a07\n.inst 0xed800a08\n.inst 0xed800a09\n.inst 0xed800a0c\n.inst 0xed800a0d\n.inst 0xed800a0f\n.inst 0xeec31a25\n.inst 0xee240a21\n.inst 0xee621a21\n.inst 0xee831a06\n.inst 0xee223a20\n.inst 0xee640aa0\n.inst 0xee633a81\n.inst 0xee221a81\n.inst 0xed803a00\n.inst 0xedc00a02\n.inst 0xedc01a05\n.inst 0xed800a06\n.inst 0xed801a0a\n.inst 0xedc03a0b\n.inst 0xe12fff1e\n.word 0x3f800000\n.word 0x40000000\n.word 0x00000000\n.word 0xbf800000\n");
}

// DECOMP_FUNC(0x002aea7c, 176)
extern "C" __attribute__((naked)) void engine_func_002aea7c() {
    asm volatile(".arm\n.inst 0xe59f10a4\n.inst 0xe92d41f0\n.inst 0xe0800080\n.inst 0xe3a07000\n.inst 0xe5911000\n.inst 0xe0816180\n.inst 0xe5960004\n.inst 0xe3500000\n.inst 0x0a000012\n.inst 0xe5904004\n.inst 0xe3540000\n.inst 0x0a000008\n.inst 0xe284000c\n.inst 0xe8900021\n.inst 0xeb005629\n.inst 0xe1a00004\n.inst 0xe320f000\n.inst 0xeb005626\n.inst 0xe1b04005\n.inst 0xe320f000\n.inst 0x1afffff6\n.inst 0xe5960004\n.inst 0xe5900000\n.inst 0xeb005620\n.inst 0xe5960004\n.inst 0xe320f000\n.inst 0xeb00561d\n.inst 0xe5867004\n.inst 0xe5964000\n.inst 0xe5940000\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb005617\n.inst 0xe5847000\n.inst 0xe5940008\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xeb005612\n.inst 0xe5847008\n.inst 0xe1a00004\n.inst 0xeb00560f\n.inst 0xe5867000\n.inst 0xe8bd81f0\n.word 0x0044ea28\n");
}

// DECOMP_FUNC(0x002aeb78, 168)
extern "C" __attribute__((naked)) void engine_func_002aeb78() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a05000\n.inst 0xe24dd080\n.inst 0xe1a07002\n.inst 0xe1a08003\n.inst 0xe1a06001\n.inst 0xe1a00001\n.inst 0xebffe1bc\n.inst 0xe3700001\n.inst 0xe1a04000\n.inst 0x0a00001b\n.inst 0xe3a01080\n.inst 0xe1a0000d\n.inst 0xeb0057df\n.inst 0xe1a0300d\n.inst 0xe1a02007\n.inst 0xe1a01004\n.inst 0xe1a00005\n.inst 0xebffe17e\n.inst 0xe1b05000\n.inst 0x0a000011\n.inst 0xe1a01007\n.inst 0xe1a00006\n.inst 0xeb002ac5\n.inst 0xe1b04000\n.inst 0x0a00000c\n.inst 0xebfa801d\n.inst 0xe1a02005\n.inst 0xe1a01004\n.inst 0xe1a0000d\n.inst 0xebfa77bb\n.inst 0xe1a01008\n.inst 0xe1a00004\n.inst 0xebffe15b\n.inst 0xe1a00004\n.inst 0xebffe14e\n.inst 0xe28dd080\n.inst 0xe1a00004\n.inst 0xe8bd81f0\n.inst 0xe28dd080\n.inst 0xe3a00000\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002b0908, 176)
extern "C" __attribute__((naked)) void func_002b0908() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a06002\n.inst 0xe1a07000\n.inst 0xe1a00001\n.inst 0xed2d8b02\n.inst 0xe24dd040\n.inst 0xe1a08003\n.inst 0xeddd8a18\n.inst 0xe1cd46d4\n.inst 0xed9d8a1b\n.inst 0xe3540000\n.inst 0x13550000\n.inst 0x03a00000\n.inst 0x0a000019\n.inst 0xe1a01002\n.inst 0xebfffe0f\n.inst 0xe59f1064\n.inst 0xe3e0207c\n.inst 0xe5903004\n.inst 0xe0c1c691\n.inst 0xe5933000\n.inst 0xe58d8004\n.inst 0xe1a0c341\n.inst 0xe04c1fc1\n.inst 0xe387c902\n.inst 0xe0010291\n.inst 0xe58dc000\n.inst 0xedcd8a02\n.inst 0xe28dc010\n.inst 0xe0861181\n.inst 0xed8d8a03\n.inst 0xe0811101\n.inst 0xe3a02001\n.inst 0xe0831101\n.inst 0xe3a03000\n.inst 0xe88c0038\n.inst 0xe1cd22bc\n.inst 0xe1cd22be\n.inst 0xe1a0200d\n.inst 0xebfffbc9\n.inst 0xe28dd040\n.inst 0xecbd8b02\n.inst 0xe8bd81f0\n.word 0x10624dd3\n");
}

// DECOMP_FUNC(0x002b5f90, 160)
extern "C" __attribute__((naked)) void func_002b5f90() {
    asm volatile(".arm\n.inst 0xe92d5ff0\n.inst 0xe3a04000\n.inst 0xe1a06004\n.inst 0xe1a07004\n.inst 0xe1a0b000\n.inst 0xe8905000\n.inst 0xe1a05fc3\n.inst 0xe089a29c\n.inst 0xe1a01fce\n.inst 0xe0209294\n.inst 0xe08a929e\n.inst 0xe020069c\n.inst 0xe022a291\n.inst 0xe0999000\n.inst 0xe022249e\n.inst 0xe0a20004\n.inst 0xe086239c\n.inst 0xe0246394\n.inst 0xe088639e\n.inst 0xe024459c\n.inst 0xe0218391\n.inst 0xe0922009\n.inst 0xe021159e\n.inst 0xe1a05fc0\n.inst 0xe0a42007\n.inst 0xe0900002\n.inst 0xe0a52fc2\n.inst 0xe0900006\n.inst 0xe0a11002\n.inst 0xe3530000\n.inst 0xaa000001\n.inst 0xe090000c\n.inst 0xe0a1100e\n.inst 0xe59d2028\n.inst 0xebfa08b3\n.inst 0xe59b2004\n.inst 0xe1a02fa2\n.inst 0xe0900002\n.inst 0xe2a11000\n.inst 0xe8bd9ff0\n");
}

// DECOMP_FUNC(0x002bb0b4, 188)
extern "C" __attribute__((naked)) void engine_func_002bb0b4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe1a04000\n.inst 0xe1a05001\n.inst 0xe590016c\n.inst 0xe3a07000\n.inst 0xe3500000\n.inst 0x0a000009\n.inst 0xe594116c\n.inst 0xe5946174\n.inst 0xee077fba\n.inst 0xe3550000\n.inst 0xe1a00004\n.inst 0x0a000013\n.inst 0xebfa4a76\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xea000014\n.inst 0xe3550000\n.inst 0x03a00000\n.inst 0x0a000019\n.inst 0xe3a01004\n.inst 0xe1a00004\n.inst 0xebffe80d\n.inst 0xe5941184\n.inst 0xe580100c\n.inst 0xe5c07004\n.inst 0xe5941170\n.inst 0xe3510000\n.inst 0x0584016c\n.inst 0x15810000\n.inst 0xe5840170\n.inst 0xe5807000\n.inst 0xeaffffe5\n.inst 0xe320f000\n.inst 0xebfa5cf2\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000007\n.inst 0xe594016c\n.inst 0xe5806008\n.inst 0xe5940174\n.inst 0xe2800001\n.inst 0xe5840174\n.inst 0xe584716c\n.inst 0xe1a00006\n.inst 0xe5847170\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002bf8d4, 176)
extern "C" __attribute__((naked)) void battle_func_002bf8d4() {
    asm volatile(".arm\n.inst 0xe92d4ff0\n.inst 0xe1a07000\n.inst 0xe1a09001\n.inst 0xe1a0a002\n.inst 0xe59f0094\n.inst 0xe1a0b003\n.inst 0xed2d8b02\n.inst 0xe24dd004\n.inst 0xe5906000\n.inst 0xed9d8a0c\n.inst 0xe3560000\n.inst 0x03a00000\n.inst 0x13a08000\n.inst 0x13a04001\n.inst 0x0a000018\n.inst 0xe0865104\n.inst 0xe5950630\n.inst 0xebfffebf\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a00000e\n.inst 0xe5950630\n.inst 0xebffdee0\n.inst 0xe1500007\n.inst 0xe320f000\n.inst 0x1a000009\n.inst 0xe0860104\n.inst 0xed8d8a00\n.inst 0xe5900630\n.inst 0xe1a0300b\n.inst 0xe1a0200a\n.inst 0xe1a01009\n.inst 0xebffbd04\n.inst 0xe3a08001\n.inst 0xe320f000\n.inst 0xea000002\n.inst 0xe2844001\n.inst 0xe3540004\n.inst 0xbaffffe7\n.inst 0xe1a00008\n.inst 0xe28dd004\n.inst 0xecbd8b02\n.inst 0xe8bd8ff0\n.word 0x0043dfc0\n");
}

// DECOMP_FUNC(0x002c1abc, 168)
extern "C" __attribute__((naked)) void ui_func_002c1abc() {
    asm volatile(".arm\n.inst 0xe59f209c\n.inst 0xe92d4010\n.inst 0xe1a01000\n.inst 0xe2804a01\n.inst 0xe7d20000\n.inst 0xed9f0a21\n.inst 0xe3500000\n.inst 0x1a000013\n.inst 0xeef00a40\n.inst 0xed941a73\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x1a00000e\n.inst 0xeef00a40\n.inst 0xed941a74\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x1a000009\n.inst 0xeef00a40\n.inst 0xed941a75\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x1a000004\n.inst 0xeef00a40\n.inst 0xed941a76\n.inst 0xeeb41a60\n.inst 0xeef1fa10\n.inst 0x0a000008\n.inst 0xeef00a40\n.inst 0xedc40a73\n.inst 0xedc40a74\n.inst 0xedc40a75\n.inst 0xed840a76\n.inst 0xe591052c\n.inst 0xe2811a01\n.inst 0xe2811f73\n.inst 0xebffd2ce\n.inst 0xe3a00000\n.inst 0xe5c401dc\n.inst 0xe8bd8010\n.word 0x3f800000\n.word 0x000011dc\n");
}

// DECOMP_FUNC(0x002c1d3c, 168)
extern "C" __attribute__((naked)) void ui_func_002c1d3c() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04001\n.inst 0xe59f1094\n.inst 0xe2805a01\n.inst 0xe24dd010\n.inst 0xe3a06000\n.inst 0xe7d11000\n.inst 0xe3510000\n.inst 0x059501e4\n.inst 0x01500004\n.inst 0x0a00000c\n.inst 0xe3540000\n.inst 0xe58541e4\n.inst 0x05c561e8\n.inst 0x0a000010\n.inst 0xe2840038\n.inst 0xe8900007\n.inst 0xe88d0007\n.inst 0xe5942034\n.inst 0xe5943030\n.inst 0xe1c401d4\n.inst 0xebf9da67\n.inst 0xe3a00003\n.inst 0xe5c501e9\n.inst 0xe3540000\n.inst 0xe5c561e8\n.inst 0x0a000004\n.inst 0xe5d501e9\n.inst 0xe3a04001\n.inst 0xe3500001\n.inst 0x0a000007\n.inst 0xea000003\n.inst 0xe5d501e9\n.inst 0xe3a04000\n.inst 0xe3500000\n.inst 0x0a000002\n.inst 0xe1a00004\n.inst 0xebfa0e3e\n.inst 0xe5c541e9\n.inst 0xe28dd010\n.inst 0xe8bd8070\n.word 0x000011e8\n");
}

// DECOMP_FUNC(0x002c31e8, 168)
extern "C" __attribute__((naked)) void engine_func_002c31e8() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a05001\n.inst 0xe5900000\n.inst 0xe1d031b0\n.inst 0xe590100c\n.inst 0xe0804203\n.inst 0xe5b4300c\n.inst 0xe1510003\n.inst 0x9a000014\n.inst 0xe5941000\n.inst 0xe1a03004\n.inst 0xe1a0c1a1\n.inst 0xe15c0002\n.inst 0xe2011007\n.inst 0x2a000007\n.inst 0xe195c0dc\n.inst 0xe1a0115c\n.inst 0xe3110001\n.inst 0x0a000003\n.inst 0xe1d310b6\n.inst 0xe0801201\n.inst 0xe281400c\n.inst 0xea000002\n.inst 0xe1d310b4\n.inst 0xe0801201\n.inst 0xe281400c\n.inst 0xe5931000\n.inst 0xe5943000\n.inst 0xe1510003\n.inst 0x8affffea\n.inst 0xe5941008\n.inst 0xe3510000\n.inst 0x12840008\n.inst 0x10811000\n.inst 0x0a000004\n.inst 0xe1a00005\n.inst 0xebff9d5d\n.inst 0xe3500000\n.inst 0x01a00004\n.inst 0x0a000000\n.inst 0xe3a00000\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002c6e04, 172)
extern "C" __attribute__((naked)) void camp_func_002c6e04() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe1a04000\n.inst 0xe1d000b0\n.inst 0xe1a05001\n.inst 0xebffc952\n.inst 0xe1a06000\n.inst 0xe1d500b0\n.inst 0xebffc94f\n.inst 0xe5d00003\n.inst 0xe5d61003\n.inst 0xe0500001\n.inst 0x1a000010\n.inst 0xe1d400b0\n.inst 0xebffc949\n.inst 0xe1a04000\n.inst 0xe1d500b0\n.inst 0xebffc946\n.inst 0xe1a01000\n.inst 0xe5d00002\n.inst 0xe5d42002\n.inst 0xe0500002\n.inst 0x1a000006\n.inst 0xe5d40003\n.inst 0xe5d12003\n.inst 0xe0500002\n.inst 0x1a000002\n.inst 0xe1d100b0\n.inst 0xe1d410b0\n.inst 0xe0400001\n.inst 0xe8bd8070\n.inst 0xe1d020b0\n.inst 0xe1d100b0\n.inst 0xe3520000\n.inst 0x0a000003\n.inst 0xe3500000\n.inst 0x03e00000\n.inst 0x0a000004\n.inst 0xea000002\n.inst 0xe3500000\n.inst 0x13a00001\n.inst 0x1a000000\n.inst 0xe0420000\n.inst 0xe12fff1e\n");
}

// DECOMP_FUNC(0x002ca6f4, 180)
extern "C" __attribute__((naked)) void script_vm_func_002ca6f4() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00001\n.inst 0xe59f50a0\n.inst 0xe5954000\n.inst 0xe5c40004\n.inst 0xe3a0003a\n.inst 0xebff689a\n.inst 0xeb01166c\n.inst 0xe594008c\n.inst 0xebfa20f6\n.inst 0xe594008c\n.inst 0xebff74de\n.inst 0xe3a06000\n.inst 0xe584608c\n.inst 0xe5940090\n.inst 0xebfa20f0\n.inst 0xe5940090\n.inst 0xebff74d8\n.inst 0xe5846090\n.inst 0xe5d40085\n.inst 0xe3500000\n.inst 0x0a000004\n.inst 0xe3a00000\n.inst 0xebff73ab\n.inst 0xe5940088\n.inst 0xe3a01000\n.inst 0xebff4782\n.inst 0xe5940088\n.inst 0xebfe6412\n.inst 0xe5846088\n.inst 0xe320f000\n.inst 0xebff6a38\n.inst 0xe3a00000\n.inst 0xe320f000\n.inst 0xebfeadb5\n.inst 0xe320f000\n.inst 0xe320f000\n.inst 0xebff1cb3\n.inst 0xe5950000\n.inst 0xe3500000\n.inst 0x0a000001\n.inst 0xebffe6f0\n.inst 0xe5856000\n.inst 0xe8bd8070\n.word 0x0044e300\n");
}

// DECOMP_FUNC(0x002d29f4, 160)
extern "C" __attribute__((naked)) void func_002d29f4() {
    asm volatile(".arm\n.inst 0xe59f0090\n.inst 0xe92d0030\n.inst 0xe3a0c000\n.inst 0xe1a0100c\n.inst 0xe5902000\n.inst 0xe59f0080\n.inst 0xe3a04014\n.inst 0xe3a05016\n.inst 0xe780c002\n.inst 0xe0810081\n.inst 0xe0820380\n.inst 0xe5f03034\n.inst 0xe3530000\n.inst 0x15903174\n.inst 0x13530000\n.inst 0x0a000010\n.inst 0xe353000b\n.inst 0xaa00000e\n.inst 0xe5d0307d\n.inst 0xe3530000\n.inst 0x1a00000b\n.inst 0xe5903084\n.inst 0xe3530000\n.inst 0x0a000006\n.inst 0xe3530002\n.inst 0x02800084\n.inst 0x08801020\n.inst 0x0a000004\n.inst 0xe3530004\n.inst 0x13530005\n.inst 0x1a000001\n.inst 0xe2800084\n.inst 0xe8801010\n.inst 0xe2811001\n.inst 0xe3510020\n.inst 0xbaffffe4\n.inst 0xe8bd0030\n.inst 0xe12fff1e\n.word 0x00447600\n.word 0x00003044\n");
}

// DECOMP_FUNC(0x002d4dac, 156)
extern "C" __attribute__((naked)) void script_vm_func_002d4dac() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xebfea31a\n.inst 0xebfea2ff\n.inst 0xe1d020f4\n.inst 0xe59f107c\n.inst 0xee002a10\n.inst 0xe5911000\n.inst 0xeeb80ac0\n.inst 0xed810a07\n.inst 0xe1d020f6\n.inst 0xee002a10\n.inst 0xeeb80ac0\n.inst 0xed810a08\n.inst 0xe1d020f8\n.inst 0xee002a10\n.inst 0xeeb80ac0\n.inst 0xed810a09\n.inst 0xe591201c\n.inst 0xedd10a08\n.inst 0xe5812028\n.inst 0xedc10a0b\n.inst 0xed810a0c\n.inst 0xe5812034\n.inst 0xedc10a0e\n.inst 0xed810a0f\n.inst 0xe1d020fa\n.inst 0xee002a10\n.inst 0xeeb80ac0\n.inst 0xed810a13\n.inst 0xed810a14\n.inst 0xe1d000fa\n.inst 0xe59f1014\n.inst 0xee000a10\n.inst 0xe5911000\n.inst 0xeeb80ac0\n.inst 0xed810a06\n.inst 0xe8bd8010\n.word 0x00447e88\n.word 0x004474f4\n");
}

// DECOMP_FUNC(0x002d65fc, 160)
extern "C" __attribute__((naked)) void camp_func_002d65fc() {
    asm volatile(".arm\n.inst 0xe59f1094\n.inst 0xe92d41f0\n.inst 0xe3500000\n.inst 0x03a05000\n.inst 0xe5916004\n.inst 0x01a07005\n.inst 0x13a04000\n.inst 0xe5c604c8\n.inst 0x0a000009\n.inst 0xe0640184\n.inst 0xe3a01000\n.inst 0xe0800100\n.inst 0xe0860100\n.inst 0xe2800fdf\n.inst 0xe5c0103c\n.inst 0xe2844001\n.inst 0xe3540002\n.inst 0xbafffff6\n.inst 0xe8bd81f0\n.inst 0xe0650185\n.inst 0xe3a01002\n.inst 0xe0800100\n.inst 0xe0864100\n.inst 0xe2840fdf\n.inst 0xe1c013ba\n.inst 0xe2840fdf\n.inst 0xe3a02000\n.inst 0xe3a01012\n.inst 0xebfefeb8\n.inst 0xe2840fdf\n.inst 0xe3a01001\n.inst 0xe5c0103c\n.inst 0xe5847388\n.inst 0xe2855001\n.inst 0xe584738c\n.inst 0xe3550002\n.inst 0xe5847390\n.inst 0xbaffffec\n.inst 0xe8bd81f0\n.word 0x0043da28\n");
}

// DECOMP_FUNC(0x002de208, 156)
extern "C" __attribute__((naked)) void effGeometry_func_002de208() {
    asm volatile(".arm\n.inst 0xe92d40f0\n.inst 0xe1a06000\n.inst 0xe1a05001\n.inst 0xe59f0080\n.inst 0xe24dd00c\n.inst 0xe3a010dd\n.inst 0xe1a00000\n.inst 0xe3a01001\n.inst 0xe3a00010\n.inst 0xe1cd00f0\n.inst 0xe3a03058\n.inst 0xe3a02000\n.inst 0xe3a01c01\n.inst 0xe3a00801\n.inst 0xebff9497\n.inst 0xe3a01c03\n.inst 0xe3a07000\n.inst 0xe1c010b0\n.inst 0xe1a04000\n.inst 0xe1c070b2\n.inst 0xe1a02007\n.inst 0xe1a01005\n.inst 0xe1a00006\n.inst 0xebfc6191\n.inst 0xe1a01000\n.inst 0xe3150702\n.inst 0xe584100c\n.inst 0x0a000003\n.inst 0xe59fc020\n.inst 0xe2811040\n.inst 0xe89c100d\n.inst 0xe881100d\n.inst 0xe594000c\n.inst 0xe5807060\n.inst 0xe28dd00c\n.inst 0xe1a00004\n.inst 0xe8bd80f0\n.word 0x004145a8\n.word 0x00473808\n");
}

// DECOMP_FUNC(0x002df484, 160)
extern "C" __attribute__((naked)) void ui_func_002df484() {
    asm volatile(".arm\n.inst 0xe92d4010\n.inst 0xe59f4090\n.inst 0xe24dd048\n.inst 0xe5940004\n.inst 0xe59012b4\n.inst 0xe1a0000d\n.inst 0xebff3b3a\n.inst 0xe28d0010\n.inst 0xed9d0a03\n.inst 0xec901a02\n.inst 0xe5940004\n.inst 0xe2801044\n.inst 0xed800a10\n.inst 0xec811a02\n.inst 0xe280105c\n.inst 0xeddd0a00\n.inst 0xeddd2a01\n.inst 0xed9d2a02\n.inst 0xedc00a0d\n.inst 0xedc02a0e\n.inst 0xed802a0f\n.inst 0xed800a16\n.inst 0xedc00a13\n.inst 0xedc02a14\n.inst 0xed802a15\n.inst 0xec811a02\n.inst 0xe3a01000\n.inst 0xe59002b4\n.inst 0xebfef41c\n.inst 0xe5940004\n.inst 0xe59002b4\n.inst 0xebfe10ab\n.inst 0xe5940004\n.inst 0xe3a01000\n.inst 0xe58012b4\n.inst 0xe5c012b0\n.inst 0xebfe5de4\n.inst 0xe28dd048\n.inst 0xe8bd8010\n.word 0x004474f0\n");
}

// DECOMP_FUNC(0x002dfcf4, 160)
extern "C" __attribute__((naked)) void script_vm_func_002dfcf4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a01000\n.inst 0xe3a02001\n.inst 0xe59f7088\n.inst 0xe1a04001\n.inst 0xe5970000\n.inst 0xe5c02004\n.inst 0xe5801000\n.inst 0xe1c010ba\n.inst 0xe1c010bc\n.inst 0xe5801010\n.inst 0xe5971000\n.inst 0xe0840104\n.inst 0xe0815180\n.inst 0xe5f5001c\n.inst 0xe3500000\n.inst 0x0a000011\n.inst 0xe1d502f0\n.inst 0xe1d562f2\n.inst 0xe3500000\n.inst 0x0a000003\n.inst 0xebff8396\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000006\n.inst 0xe3560000\n.inst 0x0a000007\n.inst 0xe1a00006\n.inst 0xebff838f\n.inst 0xe3500000\n.inst 0xe320f000\n.inst 0x0a000002\n.inst 0xe595001c\n.inst 0xe6bf0070\n.inst 0xebfe9f78\n.inst 0xe2844001\n.inst 0xe3540018\n.inst 0xbaffffe4\n.inst 0xe8bd81f0\n.word 0x00447a48\n");
}

// DECOMP_FUNC(0x002e2750, 184)
extern "C" __attribute__((naked)) void ui_func_002e2750() {
    asm volatile(".arm\n.inst 0xe92d5ff0\n.inst 0xe2516000\n.inst 0xe1a07000\n.inst 0xe1a09002\n.inst 0xe1a0a003\n.inst 0xe3a04000\n.inst 0xc3a0b000\n.inst 0xda000024\n.inst 0xe0875284\n.inst 0xe1d500d6\n.inst 0xe3500000\n.inst 0xba00001d\n.inst 0xe0800180\n.inst 0xe3a01000\n.inst 0xe08a0180\n.inst 0xebfec545\n.inst 0xeebd0ac0\n.inst 0xe3590000\n.inst 0x01c5b0b4\n.inst 0xee108a10\n.inst 0x0a00000e\n.inst 0xe3590001\n.inst 0x0a000002\n.inst 0xe3590002\n.inst 0x1a00000a\n.inst 0xea000005\n.inst 0xe3a01004\n.inst 0xe3a00000\n.inst 0xebfed20f\n.inst 0xe1a00100\n.inst 0xe320f000\n.inst 0xea000002\n.inst 0xe1a01008\n.inst 0xe3a00000\n.inst 0xebfed209\n.inst 0xe1c500b4\n.inst 0xe1d500f4\n.inst 0xe1500008\n.inst 0xba000002\n.inst 0xe1a01008\n.inst 0xebff8e59\n.inst 0xe1c510b4\n.inst 0xe2844001\n.inst 0xe1540006\n.inst 0xbaffffda\n.inst 0xe8bd9ff0\n");
}

// DECOMP_FUNC(0x002eb300, 156)
extern "C" __attribute__((naked)) void ui_func_002eb300() {
    asm volatile(".arm\n.inst 0xe92d4ff0\n.inst 0xe24dd00c\n.inst 0xe3500005\n.inst 0xe1a0a003\n.inst 0xe1a0b001\n.inst 0xe28d1030\n.inst 0xe89103e0\n.inst 0xe59f1074\n.inst 0xe5911000\n.inst 0xaa000019\n.inst 0xe3a0c004\n.inst 0xe5913004\n.inst 0xe08c0200\n.inst 0xe3a01001\n.inst 0xe0834000\n.inst 0xe1a00002\n.inst 0xe5c4100f\n.inst 0xebfece48\n.inst 0xe5c40008\n.inst 0xe5c4a009\n.inst 0xe5c4500a\n.inst 0xe5c4600b\n.inst 0xe5c4700c\n.inst 0xe5c4800d\n.inst 0xe3a00000\n.inst 0xe5c4900e\n.inst 0xebfe4a82\n.inst 0xe89b100a\n.inst 0xe1a02000\n.inst 0xe88d100a\n.inst 0xe1a0300d\n.inst 0xe3a01000\n.inst 0xe1a00003\n.inst 0xebfddfe0\n.inst 0xe1cd00d0\n.inst 0xe1c400f0\n.inst 0xe28dd00c\n.inst 0xe8bd8ff0\n.word 0x00439c60\n");
}

// DECOMP_FUNC(0x002f0204, 180)
extern "C" __attribute__((naked)) void script_vm_func_002f0204() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xebfe9b53\n.inst 0xe59f709c\n.inst 0xe1a04000\n.inst 0xe5970000\n.inst 0xebfe3a5d\n.inst 0xe5900028\n.inst 0xe3a0100c\n.inst 0xe2800c01\n.inst 0xe1c014bc\n.inst 0xebfe8e98\n.inst 0xe3841801\n.inst 0xe2802a01\n.inst 0xe2822efd\n.inst 0xe1a00fc1\n.inst 0xe5820004\n.inst 0xe3a06001\n.inst 0xe3a05000\n.inst 0xe3a04004\n.inst 0xe5821000\n.inst 0xe320f000\n.inst 0xebfe8e8d\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7900181\n.inst 0xe3100001\n.inst 0x03100040\n.inst 0x1a000007\n.inst 0xe5970000\n.inst 0xebfe3a43\n.inst 0xe2851001\n.inst 0xe0800004\n.inst 0xe6af5071\n.inst 0xe1550006\n.inst 0xe5c04038\n.inst 0xaa000002\n.inst 0xe2844001\n.inst 0xe3540036\n.inst 0xbaffffea\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.word 0x0043427c\n");
}

// DECOMP_FUNC(0x002f03d0, 168)
extern "C" __attribute__((naked)) void engine_func_002f03d0() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9ae0\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfe9add\n.inst 0xe1a06000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe8e27\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000010\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510005\n.inst 0x1a00000c\n.inst 0xe28000cc\n.inst 0xe1d02eb8\n.inst 0xe1d01efa\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebff5746\n.inst 0xe1500006\n.inst 0xe320f000\n.inst 0xca000003\n.inst 0xe3a00001\n.inst 0xebfe76bf\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe1\n.inst 0xe3a00000\n.inst 0xebfe76b8\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f0478, 168)
extern "C" __attribute__((naked)) void engine_func_002f0478() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe9ab6\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfe9ab3\n.inst 0xe1a06000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe8dfd\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a000010\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510005\n.inst 0x1a00000c\n.inst 0xe28000cc\n.inst 0xe1d02ebc\n.inst 0xe1d01efe\n.inst 0xe3a00064\n.inst 0xe1600082\n.inst 0xebff571c\n.inst 0xe1500006\n.inst 0xe320f000\n.inst 0xca000003\n.inst 0xe3a00001\n.inst 0xebfe7695\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe1\n.inst 0xe3a00000\n.inst 0xebfe768e\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f3acc, 172)
extern "C" __attribute__((naked)) void script_vm_func_002f3acc() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a04000\n.inst 0xe59f0094\n.inst 0xe59f7094\n.inst 0xed2d8b04\n.inst 0xeeb08a41\n.inst 0xeef08a60\n.inst 0xeeb09a40\n.inst 0xe5906000\n.inst 0xe3a00065\n.inst 0xe0000094\n.inst 0xe0865100\n.inst 0xe5f501d0\n.inst 0xe3500000\n.inst 0x0a000014\n.inst 0xe5950014\n.inst 0xe350001d\n.inst 0x13500026\n.inst 0x0a000003\n.inst 0xe350001e\n.inst 0x1350001f\n.inst 0x13500025\n.inst 0x1a00000c\n.inst 0xe2850050\n.inst 0xeeb01a48\n.inst 0xeef00a68\n.inst 0xeeb00a49\n.inst 0xecd01a03\n.inst 0xebfe5084\n.inst 0xee100a10\n.inst 0xe1500007\n.inst 0xaa000003\n.inst 0xe3a00012\n.inst 0xe5850004\n.inst 0xecbd8b04\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe3540080\n.inst 0xbaffffe1\n.inst 0xecbd8b04\n.inst 0xe8bd81f0\n.word 0x00447a78\n.word 0x41200000\n");
}

// DECOMP_FUNC(0x002f6e70, 152)
extern "C" __attribute__((naked)) void engine_func_002f6e70() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe8038\n.inst 0xe1a06000\n.inst 0xe3a00001\n.inst 0xebfe8035\n.inst 0xe3a01001\n.inst 0xe1a05011\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe737e\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000b\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510006\n.inst 0x1a000007\n.inst 0xe2800c01\n.inst 0xe1d00cb6\n.inst 0xe1100005\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe5c1b\n.inst 0xe3a00001\n.inst 0xe8bd8070\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe6\n.inst 0xe3a00000\n.inst 0xebfe5c14\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002f7694, 160)
extern "C" __attribute__((naked)) void engine_func_002f7694() {
    asm volatile(".arm\n.inst 0xe52de004\n.inst 0xe24dd00c\n.inst 0xe3a00000\n.inst 0xebfe7e2e\n.inst 0xe6ff0070\n.inst 0xebfee473\n.inst 0xe1d025b8\n.inst 0xe3a01000\n.inst 0xe3520000\n.inst 0xe58d2000\n.inst 0xe1d025be\n.inst 0xc3a01001\n.inst 0xe58d2004\n.inst 0xe1d006b4\n.inst 0xe3520000\n.inst 0xc2811001\n.inst 0xe3500000\n.inst 0xc2811001\n.inst 0xe58d0008\n.inst 0xe3510000\n.inst 0xe3e00000\n.inst 0xda000003\n.inst 0xe2410001\n.inst 0xe6ff0070\n.inst 0xebff2534\n.inst 0xe79d0100\n.inst 0xe320f000\n.inst 0xebfe5a13\n.inst 0xe28dd00c\n.inst 0xe3a00001\n.inst 0xe49df004\n.inst 0xe3a00000\n.inst 0xe92d4010\n.inst 0xebfe7e10\n.inst 0xe6ff0070\n.inst 0xebff070f\n.inst 0xe5d00002\n.inst 0xebfe5a09\n.inst 0xe3a00001\n.inst 0xe8bd8010\n");
}

// DECOMP_FUNC(0x002f7d30, 164)
extern "C" __attribute__((naked)) void engine_func_002f7d30() {
    asm volatile(".arm\n.inst 0xe92d4070\n.inst 0xe3a00000\n.inst 0xebfe7c88\n.inst 0xe1a06000\n.inst 0xe3e05000\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe6fd1\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110001\n.inst 0x0a00000e\n.inst 0xe3110040\n.inst 0x1a00000c\n.inst 0xe3110008\n.inst 0x0a00000a\n.inst 0xe1d010f8\n.inst 0xe3510000\n.inst 0xba000007\n.inst 0xe590127c\n.inst 0xe3510000\n.inst 0x0a000004\n.inst 0xe1d114b6\n.inst 0xe1510006\n.inst 0x1a000001\n.inst 0xe1d050f8\n.inst 0xea000006\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe4\n.inst 0xe6ff0076\n.inst 0xebfe9074\n.inst 0xe3500000\n.inst 0xa280506d\n.inst 0xe1a00005\n.inst 0xebfe5861\n.inst 0xe3a00001\n.inst 0xe8bd8070\n");
}

// DECOMP_FUNC(0x002feda4, 152)
extern "C" __attribute__((naked)) void engine_func_002feda4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xebfe606b\n.inst 0xe1a06000\n.inst 0xe3a00001\n.inst 0xebfe6068\n.inst 0xe3a07001\n.inst 0xe1a05017\n.inst 0xe3a04000\n.inst 0xe320f000\n.inst 0xebfe53b1\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000b\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510006\n.inst 0x1a000007\n.inst 0xe2800c01\n.inst 0xe1d00cb6\n.inst 0xe1100005\n.inst 0x0a000003\n.inst 0xe3a00001\n.inst 0xebfe3c4e\n.inst 0xe1a00007\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe6\n.inst 0xe3a00000\n.inst 0xebfe3c47\n.inst 0xe1a00007\n.inst 0xe8bd81f0\n");
}

// DECOMP_FUNC(0x002ff0e4, 156)
extern "C" __attribute__((naked)) void engine_func_002ff0e4() {
    asm volatile(".arm\n.inst 0xe92d41f0\n.inst 0xe3a00000\n.inst 0xebfe5f9b\n.inst 0xe1a05000\n.inst 0xe3a00001\n.inst 0xebfe5f98\n.inst 0xe1a06000\n.inst 0xe3a04000\n.inst 0xe3a07002\n.inst 0xe320f000\n.inst 0xebfe52e1\n.inst 0xe2800d7f\n.inst 0xe0841204\n.inst 0xe5900000\n.inst 0xe0811304\n.inst 0xe7b01181\n.inst 0xe3110010\n.inst 0x13110001\n.inst 0x0a00000c\n.inst 0xe3110040\n.inst 0x01d01cbe\n.inst 0x01510005\n.inst 0x1a000008\n.inst 0xe0800086\n.inst 0xe2800c01\n.inst 0xe1d00fb2\n.inst 0xe1570520\n.inst 0x1a000003\n.inst 0xe3a00001\n.inst 0xebfe3b7d\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n.inst 0xe2844001\n.inst 0xe354006d\n.inst 0xbaffffe5\n.inst 0xe3a00000\n.inst 0xebfe3b76\n.inst 0xe3a00001\n.inst 0xe8bd81f0\n");
}
