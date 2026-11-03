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
extern "C" s32 battle_func_0029abc0(s16);

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
        cost = battle_func_0029abc0(f20);
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

extern "C" u8* camp_func_0026f25c(u32);
extern "C" u8* battle_func_002ae3f0(s16);
extern "C" u8* battle_func_002b6e60();
extern "C" void script_vm_func_002899c4(u32, u32, u32);
extern "C" u32 engine_func_002c583c(u32);
extern "C" void script_vm_func_002a755c(u32);
extern "C" void engine_func_002c4360(u32);
extern "C" void script_vm_func_00252630();
extern "C" void script_vm_func_00296a18(u8*, u32);
extern "C" void ui_func_0029eb14(u32);
extern "C" void camp_func_0029ea28();
extern "C" u8* camp_func_002a8a08();

// DECOMP_FUNC(0x0028d4f0, 156)
extern "C" u32 camp_func_0028d4f0(u8* ctx) {
    u32 r6 = *reinterpret_cast<u32*>(ctx + 0x2f34);
    if (r6 - 1 > 3) {
        r6 = 0;
        for (u32 i = 0; i < 12; ++i) {
            u8* obj = camp_func_0026f25c(i);
            if (*reinterpret_cast<u16*>(obj + 0x48) != 0) {
                ++r6;
            }
        }
    }
    if (static_cast<s32>(r6) < 1) {
        return 0;
    }
    s16 count = *reinterpret_cast<s16*>(ctx + 0xb4);
    if (count <= 0) {
        return 0;
    }
    for (s32 i = 0; i < count; ++i) {
        u16 item = *reinterpret_cast<u16*>(ctx + 0x8c + i * 2);
        u8* info = battle_func_002ae3f0(item);
        if (info[0x4b] == static_cast<u8>(r6)) {
            return item;
        }
    }
    return 0;
}

// DECOMP_FUNC(0x00290374, 156)
extern "C" void script_vm_func_00290374() {
    u8* r6 = battle_func_002b6e60();
    u8* r5 = r6 + 0x600;
    u16 flags = *reinterpret_cast<u16*>(r5 + 8);
    if ((flags & 1) != 0) {
        u8* r4 = battle_func_002b6e60();
        if ((*reinterpret_cast<u16*>(r4 + 0x608) & 1) != 0) {
            if (*reinterpret_cast<u16*>(r4 + 0x46) == 0x2a3) {
                script_vm_func_002899c4(0x262, 0, 1);
            }
            if (*reinterpret_cast<u16*>(r4 + 0x46) == 0x2a5) {
                script_vm_func_002899c4(0x263, 0, 1);
            }
            *reinterpret_cast<u16*>(r4 + 0x46) = 0;
        }
    }
    *reinterpret_cast<u16*>(r5 + 8) &= ~1;
    *reinterpret_cast<u16*>(r6 + 0x46) = 0;
    *reinterpret_cast<u16*>(r5 + 4) = 0;
}

// DECOMP_FUNC(0x002911ec, 192)
extern "C" void script_vm_func_002911ec(u32 arg) {
    if (engine_func_002c583c(1) != 0) {
        return;
    }
    u8* out = reinterpret_cast<u8*>(0x0044e098);

    u8* ch1 = reinterpret_cast<u8*>(0x004c53c4);
    u32 f1 = *reinterpret_cast<u32*>(ch1 + 0x1c);
    if ((f1 & 2) != 0) {
        if ((f1 & 0x20) != 0) {
            *reinterpret_cast<u32*>(ch1 + 0x1c) = (f1 & ~0x20) | 0x40;
            *reinterpret_cast<u32*>(ch1 + 4) = arg;
            *reinterpret_cast<u32*>(out + 4) = *reinterpret_cast<u32*>(ch1);
        } else if ((f1 & 0x400) == 0) {
            *reinterpret_cast<u32*>(ch1 + 8) = 30;
            *reinterpret_cast<u32*>(ch1 + 0x1c) = f1 | 8;
        }
    }

    u8* ch2 = reinterpret_cast<u8*>(0x004c53e4);
    u32 f2 = *reinterpret_cast<u32*>(ch2 + 0x1c);
    if ((f2 & 2) != 0) {
        if ((f2 & 0x20) != 0) {
            *reinterpret_cast<u32*>(ch2 + 0x1c) = (f2 & ~0x20) | 0x40;
            *reinterpret_cast<u32*>(ch2 + 4) = arg;
            *reinterpret_cast<u32*>(out + 4) = *reinterpret_cast<u32*>(ch2);
        } else if ((f2 & 0x400) == 0) {
            *reinterpret_cast<u32*>(ch2 + 8) = 30;
            *reinterpret_cast<u32*>(ch2 + 0x1c) = f2 | 8;
        }
    }
}

// DECOMP_FUNC(0x002956c0, 160)
extern "C" u32 script_vm_func_002956c0(u8* ctx) {
    script_vm_func_002a755c(*reinterpret_cast<u32*>(ctx + 0x3574));
    engine_func_002c4360(*reinterpret_cast<u32*>(ctx + 0x3578));
    script_vm_func_00252630();

    ctx[0xd640] = 0;
    u32 count = *reinterpret_cast<u32*>(ctx + 0xcf78) + 1;
    *reinterpret_cast<u32*>(ctx + 0xcf78) = count;
    u32 limit = *reinterpret_cast<u32*>(ctx + 0xcf74);
    if (limit == count) {
        script_vm_func_00296a18(ctx, 20);
        return 0;
    }
    ui_func_0029eb14(1);
    camp_func_0029ea28();
    script_vm_func_00296a18(ctx, 9);
    return 1;
}

// DECOMP_FUNC(0x00296020, 168)
extern "C" u32 script_vm_func_00296020(u8* target) {
    s32 found_idx = -1;
    if (target != nullptr) {
        u8* base = camp_func_002a8a08() + 0x90;
        for (s32 i = 0; i < 24; ++i) {
            u8* entry = base + i * 0x604;
            if (entry == target || entry[0x4a] == target[0x4a]) {
                found_idx = i;
                break;
            }
        }
    }
    u8* slots = camp_func_002a8a08() + 0x9108;
    for (s32 i = 0; i < 3; ++i) {
        s8 val = static_cast<s8>(slots[i]);
        if (val >= 0 && val == found_idx) {
            return 1;
        }
    }
    return 0;
}

extern "C" s32 camp_func_002116ac();
extern "C" u8* camp_func_00310724(u32);
extern "C" u32 script_vm_func_002c0ba8(u32);
extern "C" u32 battle_func_002931cc(u32);
extern "C" void engine_func_00294848(u32, u32, u32, u32);
extern "C" u32 camp_func_003bcbe0(u8*);

// DECOMP_FUNC(0x002971e4, 160)
extern "C" u32 script_vm_func_002971e4(u8* ctx, s32 idx) {
    if (idx < 0) {
        return 0;
    }
    u8* obj_b0 = *reinterpret_cast<u8**>(ctx + 0xb0);
    s32 count = *reinterpret_cast<s32*>(obj_b0 + 8);
    if (idx >= count) {
        return 0;
    }
    const char* src_base = *reinterpret_cast<const char**>(ctx + 0xb4);
    const char* src = src_base + (idx << 5);
    u32 i = 0;
    while (true) {
        char c = src[i];
        reinterpret_cast<char*>(ctx)[i] = c;
        if (c == 0) {
            break;
        }
        ++i;
    }
    *reinterpret_cast<u32*>(ctx + 0x18) = *reinterpret_cast<const u32*>(src + 0x18);
    *reinterpret_cast<u32*>(ctx + 0x1c) = 0;
    *reinterpret_cast<u32*>(ctx + 0x20) = 0;
    *reinterpret_cast<u32*>(ctx + 0x24) = 0;
    *reinterpret_cast<u32*>(ctx + 0x28) = 0;
    *reinterpret_cast<u32*>(ctx + 0x2c) = 0;
    *reinterpret_cast<u32*>(ctx + 0x30) = 0;
    *reinterpret_cast<u32*>(ctx + 0x34) = 0;
    *reinterpret_cast<u32*>(ctx + 0x38) = 0;
    engine_func_002c4b30(ctx + 0x3c, 0x70);
    *reinterpret_cast<s32*>(ctx + 0xc8) = idx;
    *reinterpret_cast<u32*>(ctx + 0xcc) = 0;
    *reinterpret_cast<u32*>(ctx + 0xd0) = 0;
    return 1;
}

// DECOMP_FUNC(0x002994b4, 164)
extern "C" u32 engine_func_002994b4(u32 filter_type, u32 target_match) {
    u32 result = 0;
    u32 match_count = 0;
    s32 total = camp_func_002116ac();
    if (total <= 0) {
        return 0;
    }
    for (u32 i = 0; i < static_cast<u32>(total); ++i) {
        u8* entry = camp_func_00310724(i);
        if (entry == nullptr) {
            continue;
        }
        if (entry[1] != static_cast<u8>(filter_type)) {
            continue;
        }
        u16 f1 = *reinterpret_cast<u16*>(entry + 0x56);
        if (f1 != 0 && script_vm_func_002c0ba8(f1) == 0) {
            continue;
        }
        u16 f2 = *reinterpret_cast<u16*>(entry + 0x58);
        if (f2 != 0 && battle_func_002931cc(f2) == 0) {
            continue;
        }
        if (match_count != target_match) {
            ++match_count;
            continue;
        }
        result = entry[0];
        break;
    }
    return result;
}

// DECOMP_FUNC(0x002998d8, 156)
extern "C" void ui_func_002998d8(u32 arg0, u32 arg1) {
    u8* obj = *reinterpret_cast<u8**>(0x0044E140 + 4);
    if (arg0 <= 2) {
        u32 target = *reinterpret_cast<u32*>(obj + 0x1E80);
        engine_func_00294848(target, arg0, arg1, 7);
    }
    *reinterpret_cast<u32*>(obj + 0x10) = 0;
    *reinterpret_cast<u32*>(obj + 0x12DC) = 6;
}

// DECOMP_FUNC(0x0029abc0, 176)
extern "C" s32 battle_func_0029abc0(s16 arg0) {
    u8* info = battle_func_002ae3f0(arg0);
    if (info == nullptr) {
        return 0;
    }
    u32 base_val = info[0x22];
    u32 sum = 0;
    for (u32 id = 12; id <= 15; ++id) {
        if (battle_func_002931cc(id) != 0) {
            u8* obj = static_cast<u8*>(camp_func_002ae818(reinterpret_cast<void*>(static_cast<uintptr_t>(id))));
            sum += *reinterpret_cast<u32*>(obj + 0x38);
        }
    }
    s32 diff = static_cast<s32>(base_val) - static_cast<s32>(sum);
    if (diff <= 0) {
        return 1;
    }
    return diff;
}

// DECOMP_FUNC(0x0029c49c, 156)
extern "C" s32 camp_func_0029c49c() {
    u8* ctx = camp_func_002a8a08();
    u32 count = 0;
    for (u32 i = 0; i < 24; ++i) {
        s8 val = static_cast<s8>(ctx[0x90F0 + i]);
        if (val < 0) {
            break;
        }
        ++count;
    }
    u8 max_count = ctx[0x910B];
    if (count >= max_count) {
        return -1;
    }
    u8* base = camp_func_002a8a08() + 0x90;
    for (s32 i = 0; i < 24; ++i) {
        u8* entry = base + i * 0x604;
        if (camp_func_003bcbe0(entry) == 0) {
            return i;
        }
    }
    return -1;
}

extern "C" void engine_func_0024db60(u8*, void*);
extern "C" void camp_func_0026aac0(u16, void*);
extern "C" void script_vm_func_0024d9e4(u8*, void*);
extern "C" void camp_func_0029df14(u16, void*);
extern "C" u8* battle_func_002b087c(u32);
extern "C" u32 camp_func_002883bc(u32, void*);
extern "C" void engine_func_002c20a8(u8*, const float*, const float*, const float*);
extern "C" void ui_func_001db28c(u8*, u32, float, float, float);

// DECOMP_FUNC(0x0029e19c, 172)
extern "C" void camp_func_0029e19c(s32 arg0, s32 arg1) {
    u8* r4 = *reinterpret_cast<u8**>(0x0044E140 + 4);
    if (arg0 < 0) {
        void* r0 = func_002b66ec();
        engine_func_0024db60(r4 + 0x1300, r0);
        r4[0x1E66] = 0;
    } else {
        u8 buf[0x610];
        if (arg1 != 0) {
            camp_func_0026aac0(static_cast<u16>(arg0), buf);
            script_vm_func_0024d9e4(r4 + 0x1300, buf);
            r4[0x1E66] = 6;
        } else {
            camp_func_0029df14(static_cast<u16>(arg0), buf);
            script_vm_func_0024d9e4(r4 + 0x1300, buf);
            r4[0x1E66] = 1;
        }
    }
    r4[0x1EB8] = 1;
}

// DECOMP_FUNC(0x0029ec6c, 156)
extern "C" u32 ui_func_0029ec6c(u32 entity_id) {
    if (entity_id > 0x500) {
        return 0;
    }
    u8* info = battle_func_002b087c(entity_id);
    if ((*reinterpret_cast<u16*>(info + 0x16) & 1) == 0) {
        return 0;
    }
    u8* r2 = *reinterpret_cast<u8**>(0x0043E2A8 + 4);
    u8* entry = r2 + 0xC1F8 + entity_id * 52;
    if ((entry[0x16] & 2) != 0) {
        return 1;
    }
    for (u32 i = 0; i < 3; ++i) {
        u16 sub_id = *reinterpret_cast<u16*>(info + 0x7C + i * 2);
        if (sub_id == 0) {
            continue;
        }
        u8* sub_entry = r2 + 0xC1F8 + sub_id * 52;
        if ((sub_entry[0x16] & 2) != 0) {
            return 1;
        }
    }
    return 0;
}

// DECOMP_FUNC(0x0029ed44, 184)
extern "C" u32 camp_func_0029ed44(u32 arg0, u16 arg1) {
    u8* item = reinterpret_cast<u8*>(func_002b9364(arg1));
    if (item == nullptr) {
        return 0;
    }
    if ((*reinterpret_cast<u32*>(item + 0x2C) & 0x200000) != 0) {
        return 0;
    }
    u16 req1 = *reinterpret_cast<u16*>(item + 0x36);
    if (req1 != 0 && script_vm_func_002c0ba8(req1) == 0) {
        return 0;
    }
    u16 f34 = *reinterpret_cast<u16*>(item + 0x34);
    if ((f34 & 1) != 0) {
        u8 stack_buf[0x38];
        u32 sub_arg;
        if ((f34 & ~1) == 0) {
            sub_arg = *reinterpret_cast<u16*>(item);
        } else {
            sub_arg = f34 >> 1;
        }
        if (camp_func_002883bc(sub_arg, stack_buf) == 0) {
            return 0;
        }
        if ((*reinterpret_cast<u16*>(stack_buf + 0x2E) & 0xFC) == 0) {
            return 0;
        }
    }
    if ((*reinterpret_cast<u16*>(item + 6) & 1) != 0) {
        return 1;
    }
    return 0;
}

// DECOMP_FUNC(0x002a0de8, 192)
extern "C" void camp_func_002a0de8() {
    u8* r4 = *reinterpret_cast<u8**>(0x0044E178);
    if (r4 == nullptr) {
        return;
    }
    const float* pos = reinterpret_cast<const float*>(r4 + 0x508);
    const float* dir = reinterpret_cast<const float*>(r4 + 0x514);
    float factor = *reinterpret_cast<const float*>(r4 + 0x52C);

    float target[3];
    target[0] = pos[0] + dir[0] * factor;
    target[1] = pos[1] + dir[1] * factor;
    target[2] = pos[2] + dir[2] * factor;

    float up[3] = { 0.0f, 1.0f, 0.0f };
    engine_func_002c20a8(r4, pos, target, up);

    const float* r5 = reinterpret_cast<const float*>(r4 + 0x530);
    ui_func_001db28c(r4, 0, r5[0], r5[1], r5[2]);
}

// DECOMP_FUNC(0x002a32bc, 192)
extern "C" void engine_func_002a32bc(u8* obj) {
    *reinterpret_cast<u32*>(obj + 0x00) = 0x00421e74;
    *reinterpret_cast<u32*>(obj + 0x04) = 0;
    obj[0x08] = 0;
    *reinterpret_cast<u32*>(obj + 0x0C) = 0;
    obj[0x10] = 0xFF;
    *reinterpret_cast<u32*>(obj + 0x14) = 0;
    *reinterpret_cast<u32*>(obj + 0x18) = 0;
    *reinterpret_cast<u32*>(obj + 0x1C) = 0;
    *reinterpret_cast<u32*>(obj + 0x20) = 0;
    for (u32 off = 0x30; off <= 0xB4; off += 4) {
        *reinterpret_cast<u32*>(obj + off) = 0;
    }
}

// DECOMP_FUNC(0x002a3ff8, 164)
extern "C" void engine_func_002a3ff8(void* obj) {
    u8* p = static_cast<u8*>(obj);
    engine_func_002c4b30(obj, 0x80);

    *reinterpret_cast<f32*>(p + 0x0C) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x1C) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x20) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x24) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x28) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x2C) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x44) = 5.0f;
    *reinterpret_cast<f32*>(p + 0x4C) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x5C) = 1.0f;
    *reinterpret_cast<f32*>(p + 0x60) = 1.0f;
    *reinterpret_cast<s32*>(p + 0x64) = -1;
    *reinterpret_cast<s32*>(p + 0x68) = 0x80;
    *reinterpret_cast<f32*>(p + 0x74) = 1.0f;
}

// DECOMP_FUNC(0x002a4e50, 160)
extern "C" u32 ui_func_002c6c10(u32, u32);

extern "C" void ui_func_002a4e50(void* obj, u32 arg1, u32 arg2, u32 arg3, u32 arg4, u32 arg5) {
    u8* p = static_cast<u8*>(obj);
    *reinterpret_cast<u32*>(p + 0x14) = arg5;

    u32 r6 = ui_func_002c6c10(arg1 + arg4 - 1, arg4) * arg4;
    *reinterpret_cast<u32*>(p + 0x18) = r6;

    u32 r7 = ui_func_002c6c10(arg2 + arg4 - 1, arg4) * arg4;
    *reinterpret_cast<u32*>(p + 0x1C) = r7;

    u32 r1 = ui_func_002c6c10((arg2 + arg3) - r7, r6) * r6;
    *reinterpret_cast<u32*>(p + 0x20) = r1;

    r1 = r1 + r7 - r6;
    *reinterpret_cast<u32*>(p + 0x2C) = 0;
    *reinterpret_cast<u32*>(p + 0x28) = arg4;

    u32 next_node = 0;
    if (r7 <= r1) {
        do {
            *reinterpret_cast<u32*>(r1) = next_node;
            next_node = r1;
            r1 -= r6;
        } while (r7 <= r1);
    }
    *reinterpret_cast<u32*>(p + 0x24) = next_node;
}

// DECOMP_FUNC(0x002a6fa0, 172)
extern "C" s32 func_002ac3b8(void*);
extern "C" void* func_002ac384(void*);
extern "C" s32 func_002ac350(void*);

extern "C" void* script_vm_func_002a6fa0(void* manager, s32 target_id, u32 target_tag) {
    if (target_id == -1) {
        return nullptr;
    }

    u8* mgr = static_cast<u8*>(manager);
    s32 count = *reinterpret_cast<s32*>(mgr + 0x310);
    if (count <= 0) {
        return nullptr;
    }

    u8* groups = *reinterpret_cast<u8**>(mgr + 0x318);
    for (s32 i = 0; i < count; ++i) {
        u8* group = groups + i * 80;
        if (!func_002ac3b8(group)) {
            continue;
        }

        u8* entries = static_cast<u8*>(func_002ac384(group));
        s32 num_entries = func_002ac350(group);
        for (s32 j = 0; j < num_entries; ++j) {
            u8* entry = entries + j * 64;
            s8 id = *reinterpret_cast<s8*>(entry);
            if (id == target_id) {
                u32 tag = *reinterpret_cast<u32*>(entry + 0x3C);
                if (tag == target_tag) {
                    return entry;
                }
            }
        }
    }

    return nullptr;
}

// DECOMP_FUNC(0x002a7094, 176)
extern "C" void* func_002a7094(void* manager, s32 target_id, u32 target_tag) {
    if (target_id == -1) {
        return nullptr;
    }

    u8* mgr = static_cast<u8*>(manager);
    s32 count = *reinterpret_cast<s32*>(mgr + 0x310);
    if (count <= 0) {
        return nullptr;
    }

    u8* groups = *reinterpret_cast<u8**>(mgr + 0x318);
    for (s32 i = 0; i < count; ++i) {
        u8* group = groups + i * 80;
        if (!func_002ac3b8(group)) {
            continue;
        }

        u8* entries = static_cast<u8*>(func_002ac384(group));
        s32 num_entries = func_002ac350(group);
        for (s32 j = 0; j < num_entries; ++j) {
            u8* entry = entries + j * 64;
            s8 id = *reinterpret_cast<s8*>(entry);
            if (id == target_id) {
                u32 tag = *reinterpret_cast<u32*>(entry + 0x3C);
                if (tag == target_tag) {
                    u8* data_table = *reinterpret_cast<u8**>(group + 0x4C);
                    return data_table + j * 16;
                }
            }
        }
    }

    return nullptr;
}

// DECOMP_FUNC(0x002a7e08, 180)
extern "C" void* func_001556f4(void*);
extern "C" u32 func_002a7dd8(void*);

extern "C" void* engine_func_002a7e08(void* context, void* archive_data, u32 enable_cwat) {
    u8* ctx = static_cast<u8*>(context);
    *reinterpret_cast<void**>(ctx + 0x00) = nullptr;
    *reinterpret_cast<void**>(ctx + 0x04) = nullptr;
    *reinterpret_cast<void**>(ctx + 0x08) = nullptr;
    ctx[0x0C] = 0;

    if (archive_data == nullptr) {
        return context;
    }

    u8* data = static_cast<u8*>(archive_data);
    if (*reinterpret_cast<u32*>(data) != 0x52415743) {
        return context;
    }

    if (*reinterpret_cast<u32*>(data + 8) != 0x01000000) {
        return context;
    }

    *reinterpret_cast<void**>(ctx + 0x00) = archive_data;
    u8* block = static_cast<u8*>(func_001556f4(archive_data));
    *reinterpret_cast<void**>(ctx + 0x04) = block + 8;
    ctx[0x0C] = 1;

    if (enable_cwat != 0) {
        u32 offset = func_002a7dd8(archive_data);
        if (*reinterpret_cast<u32*>(data + offset) == 0x54415743) {
            u32 off2 = func_002a7dd8(archive_data);
            *reinterpret_cast<void**>(ctx + 0x08) = data + off2 + 4;
        }
    }

    return context;
}

// DECOMP_FUNC(0x002ac614, 188)
extern "C" void* func_0014d04c(void*, u32);
extern "C" void* func_0014d080(void*, u32);
extern "C" void* func_0014d040(void*);
extern "C" f32 func_0014d174(void*);
extern "C" void* func_0014d0bc(void*);
extern "C" void func_002a7fc4(void*, void*);
extern "C" u32 func_0014d0f8(void*);
extern "C" u32 func_0014d14c(void*);
extern "C" u32 func_0014d120(void*);
extern "C" u32 func_0014d1e8(void*);

extern "C" s32 engine_func_002ac614(void* container, void* out_entry, u32 arg2, u32 arg3) {
    u8* c = static_cast<u8*>(container);
    void* handle = func_0014d04c(*reinterpret_cast<void**>(c + 4), arg2);
    void* item_info = func_0014d080(handle, arg3);

    u32* table = static_cast<u32*>(func_0014d040(*reinterpret_cast<void**>(c + 4)));
    u32 max_count = table[0];
    u32 index = *reinterpret_cast<u32*>(item_info);
    if (index >= max_count) {
        return 0;
    }

    u32* elem = table + 1 + index * 2;
    if (elem == nullptr) {
        return 0;
    }

    u8* out = static_cast<u8*>(out_entry);
    *reinterpret_cast<u32*>(out + 0x00) = elem[0];
    *reinterpret_cast<u32*>(out + 0x04) = elem[1];
    *reinterpret_cast<f32*>(out + 0x14) = func_0014d174(item_info);

    func_002a7fc4(out + 0x08, func_0014d0bc(item_info));

    out[0x0D] = static_cast<u8>(func_0014d0f8(item_info));
    out[0x0E] = static_cast<u8>(func_0014d14c(item_info));
    out[0x0F] = static_cast<u8>(func_0014d120(item_info));
    out[0x10] = static_cast<u8>(func_0014d1e8(item_info));

    return 1;
}

// DECOMP_FUNC(0x002ad4fc, 164)
extern "C" __attribute__((pcs("aapcs-vfp"))) void func_002ad4fc(f32* out, f32 left, f32 right, f32 top, f32 bottom, f32 near_val, f32 far_val) {
    f32 width = right - left;
    f32 height = bottom - top;
    f32 depth = far_val - near_val;

    out[0] = (2.0f * near_val) / width;
    out[1] = 0.0f;
    out[2] = (right + left) / width;
    out[3] = 0.0f;

    out[4] = 0.0f;
    out[5] = (2.0f * near_val) / height;
    out[6] = (bottom + top) / height;
    out[7] = 0.0f;

    out[8] = 0.0f;
    out[9] = 0.0f;
    out[10] = far_val / depth;
    out[11] = (near_val * far_val) / depth;

    out[12] = 0.0f;
    out[13] = 0.0f;
    out[14] = -1.0f;
    out[15] = 0.0f;
}

// DECOMP_FUNC(0x002aea7c, 176)
struct Part15_SlotNode {
    u8 pad[0x0C];
    void* payload;
    Part15_SlotNode* next;
};

struct Part15_ChildContainer {
    void* sub_obj;
    Part15_SlotNode* head;
};

struct Part15_PrimaryContainer {
    void* field_0;
    void* field_4;
    void* field_8;
};

struct Part15_ManagerSlot {
    Part15_PrimaryContainer* primary;
    Part15_ChildContainer* child;
    u8 pad[0x10];
};

extern "C" void engine_func_002aea7c(s32 slot_idx) {
    Part15_ManagerSlot* slots = *reinterpret_cast<Part15_ManagerSlot**>(0x0044EA28);
    Part15_ManagerSlot* slot = &slots[slot_idx];

    Part15_ChildContainer* child = slot->child;
    if (child != nullptr) {
        Part15_SlotNode* node = child->head;
        while (node != nullptr) {
            void* payload = node->payload;
            Part15_SlotNode* next = node->next;
            func_002c4360(payload);
            func_002c4360(node);
            node = next;
        }
        func_002c4360(child->sub_obj);
        func_002c4360(child);
        slot->child = nullptr;
    }

    Part15_PrimaryContainer* primary = slot->primary;
    if (primary->field_0 != nullptr) {
        func_002c4360(primary->field_0);
        primary->field_0 = nullptr;
    }
    if (primary->field_8 != nullptr) {
        func_002c4360(primary->field_8);
        primary->field_8 = nullptr;
    }
    func_002c4360(primary);
    slot->primary = nullptr;
}

// DECOMP_FUNC(0x002aeb78, 168)
extern "C" s32 func_002a728c(void*);
extern "C" s32 engine_func_002a71c0(void*, s32, u32, void*);
extern "C" void* func_002b96f0(void*, u32);
extern "C" void func_0014ec5c();
extern "C" void func_0014cae4(void*, void*, s32);
extern "C" void func_002a7170(void*, u32);
extern "C" void func_002a7144(void*);

extern "C" void* engine_func_002aeb78(void* arg0, void* arg1, u32 arg2, u32 arg3) {
    s32 handle = func_002a728c(arg1);
    if (handle == -1) {
        return nullptr;
    }

    u8 stack_buf[0x80];
    engine_func_002c4b30(stack_buf, sizeof(stack_buf));

    s32 res = engine_func_002a71c0(arg0, handle, arg2, stack_buf);
    if (res == 0) {
        return nullptr;
    }

    void* item = func_002b96f0(arg1, arg2);
    if (item == nullptr) {
        return nullptr;
    }

    func_0014ec5c();
    func_0014cae4(stack_buf, item, res);
    func_002a7170(item, arg3);
    func_002a7144(item);
    return item;
}

// DECOMP_FUNC(0x002b0908, 176)
extern "C" void* ui_func_002b0188(u32, s32);
extern "C" s32 ui_func_002af8d0(void*, void*, void*);

extern "C" __attribute__((pcs("aapcs"))) s32 func_002b0908(s32 arg0, void* arg1, s32 arg2, u32 arg3, f32 arg4, u32 arg5, u32 arg6, f32 arg7) {
    if (arg5 == 0 && arg6 == 0) {
        return 0;
    }

    void* obj = ui_func_002b0188(reinterpret_cast<u32>(arg1), arg2);
    u8* p4 = *reinterpret_cast<u8**>(static_cast<u8*>(obj) + 4);
    u8* r3 = *reinterpret_cast<u8**>(p4);

    s32 rem = arg2 % 1000;
    u8* entry = r3 + rem * 20;

    u8 packet[0x40];
    *reinterpret_cast<u32*>(packet + 0x00) = static_cast<u32>(arg0) | 0x8000;
    *reinterpret_cast<u32*>(packet + 0x04) = arg3;
    *reinterpret_cast<f32*>(packet + 0x08) = arg4;
    *reinterpret_cast<f32*>(packet + 0x0C) = arg7;
    *reinterpret_cast<u32*>(packet + 0x10) = 0;
    *reinterpret_cast<u32*>(packet + 0x14) = arg5;
    *reinterpret_cast<u32*>(packet + 0x18) = arg6;
    *reinterpret_cast<u16*>(packet + 0x2C) = 1;
    *reinterpret_cast<u16*>(packet + 0x2E) = 1;

    return ui_func_002af8d0(obj, entry, packet);
}

// DECOMP_FUNC(0x002b5f90, 160)
static s64 mul_high_s64(s64 a, s64 b) {
    u64 a_lo = static_cast<u32>(a);
    u64 a_hi = static_cast<u64>(a) >> 32;
    u64 b_lo = static_cast<u32>(b);
    u64 b_hi = static_cast<u64>(b) >> 32;

    u64 lo_lo = a_lo * b_lo;
    u64 c1 = a_lo * b_hi;
    u64 c2 = a_hi * b_lo;
    u64 hi_hi = a_hi * b_hi;

    u64 mid = (lo_lo >> 32) + static_cast<u32>(c1) + static_cast<u32>(c2);
    u64 u_hi = (c1 >> 32) + (c2 >> 32) + (mid >> 32) + hi_hi;

    s64 s_hi = static_cast<s64>(u_hi);
    if (a < 0) {
        s_hi -= b;
    }
    if (b < 0) {
        s_hi -= a;
    }
    return s_hi;
}

extern "C" __attribute__((pcs("aapcs"))) s64 func_002b5f90(const s64* a_ptr, s64 mul, u32 shift) {
    s64 a = *a_ptr;
    s64 hi = mul_high_s64(a, mul);
    s64 res = hi >> shift;
    if (a < 0) {
        res += 1;
    }
    return res;
}

// DECOMP_FUNC(0x002bb0b4, 188)
extern "C" void func_0014dac8(void*);
extern "C" void* func_002b5148(void*, u32);
extern "C" s32 func_0015250c(void*);

extern "C" u32 engine_func_002bb0b4(void* obj, u32 mode) {
    u8* self = static_cast<u8*>(obj);
    u8* head = *reinterpret_cast<u8**>(self + 0x16C);

    if (head == nullptr) {
        if (mode == 0) {
            return 0;
        }
        u8* packet = static_cast<u8*>(func_002b5148(self, 4));
        *reinterpret_cast<u32*>(packet + 0x0C) = *reinterpret_cast<u32*>(self + 0x184);
        packet[4] = 0;

        u8* tail = *reinterpret_cast<u8**>(self + 0x170);
        if (tail == nullptr) {
            *reinterpret_cast<u8**>(self + 0x16C) = packet;
        } else {
            *reinterpret_cast<u8**>(tail + 0) = packet;
        }
        *reinterpret_cast<u8**>(self + 0x170) = packet;
        *reinterpret_cast<u8**>(packet + 0) = nullptr;
    }

    u32 seq = *reinterpret_cast<u32*>(self + 0x174);
    asm volatile("mcr p15, 0, %0, c7, c10, 5" : : "r"(0) : "memory");

    if (mode == 0) {
        if (!func_0015250c(self)) {
            return 0;
        }
    } else {
        func_0014dac8(self);
    }

    head = *reinterpret_cast<u8**>(self + 0x16C);
    *reinterpret_cast<u32*>(head + 8) = seq;
    *reinterpret_cast<u32*>(self + 0x174) = seq + 1;
    *reinterpret_cast<u8**>(self + 0x16C) = nullptr;
    *reinterpret_cast<u8**>(self + 0x170) = nullptr;
    return seq;
}

// DECOMP_FUNC(0x002bf8d4, 176)
extern "C" u32 func_002bf41c(void*);
extern "C" s32 func_002b74b4(void*);
extern "C" __attribute__((pcs("aapcs"))) void func_002aed6c(void*, u32, u32, u32, f32);

extern "C" __attribute__((pcs("aapcs"))) s32 battle_func_002bf8d4(s32 target_id, u32 arg1, u32 arg2, u32 arg3, f32 arg4) {
    u8* party = *reinterpret_cast<u8**>(0x0043DFC0);
    if (party == nullptr) {
        return 0;
    }

    for (s32 i = 1; i < 4; ++i) {
        void* member = *reinterpret_cast<void**>(party + 0x630 + i * 4);
        if (!func_002bf41c(member)) {
            continue;
        }
        if (func_002b74b4(member) != target_id) {
            continue;
        }

        func_002aed6c(member, arg1, arg2, arg3, arg4);
        return 1;
    }

    return 0;
}

// DECOMP_FUNC(0x002c1abc, 168)
extern "C" void func_002b668c(void*, void*);

extern "C" void ui_func_002c1abc(void* obj) {
    u8* self = static_cast<u8*>(obj);
    u8 dirty = self[0x11DC];

    f32* scales = reinterpret_cast<f32*>(self + 0x11CC);
    if (dirty != 0 || scales[0] != 1.0f || scales[1] != 1.0f || scales[2] != 1.0f || scales[3] != 1.0f) {
        scales[0] = 1.0f;
        scales[1] = 1.0f;
        scales[2] = 1.0f;
        scales[3] = 1.0f;
        func_002b668c(*reinterpret_cast<void**>(self + 0x52C), scales);
    }

    self[0x11DC] = 0;
}

// DECOMP_FUNC(0x002c1d3c, 168)
extern "C" void func_00138734(u32, u32, u32, u32, u32, u32, u32);
extern "C" void func_001456d0(u32);

extern "C" void ui_func_002c1d3c(void* obj, void* new_target) {
    u8* self = static_cast<u8*>(obj);
    u8 dirty = self[0x11E8];
    void* current_target = *reinterpret_cast<void**>(self + 0x11E4);

    if (dirty != 0 || current_target != new_target) {
        *reinterpret_cast<void**>(self + 0x11E4) = new_target;
        if (new_target == nullptr) {
            self[0x11E8] = 0;
        } else {
            u8* t = static_cast<u8*>(new_target);
            u32 a0 = *reinterpret_cast<u32*>(t + 0x14);
            u32 a1 = *reinterpret_cast<u32*>(t + 0x18);
            u32 a2 = *reinterpret_cast<u32*>(t + 0x34);
            u32 a3 = *reinterpret_cast<u32*>(t + 0x30);
            u32 a4 = *reinterpret_cast<u32*>(t + 0x38);
            u32 a5 = *reinterpret_cast<u32*>(t + 0x3C);
            u32 a6 = *reinterpret_cast<u32*>(t + 0x40);
            func_00138734(a0, a1, a2, a3, a4, a5, a6);
            self[0x11E9] = 3;
        }
    }

    self[0x11E8] = 0;
    u8 expected_state = (new_target != nullptr) ? 1 : 0;
    if (self[0x11E9] != expected_state) {
        func_001456d0(expected_state);
        self[0x11E9] = expected_state;
    }
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
