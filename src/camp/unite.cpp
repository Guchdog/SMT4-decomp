#include "camp/unite.h"

extern "C" {
    void* AsdMem_Alloc(u32, u32, u32, u32, u32); // 0x002c4b84
    void  btlTalkBustUp_func_002959c4();
    void  script_vm_func_002c0128();
    void  camp_func_002976ac(u32);
}

namespace smt4::camp {

ButtonHelpManager g_ButtonHelpManager = {0, {0, 0, 0}, nullptr}; // 0x0043DA28
SortMenuManager g_SortMenuManager = {0, {0, 0, 0}, nullptr};     // 0x0043DD20

// DECOMP_FUNC(0x0028d974, 736)

// ============================================================================
// Unite: Mido Demon Fusion (Cathedral of Shadows) Engine
// ============================================================================

UniteWork* g_UniteWork = nullptr;

// DECOMP_FUNC(0x002e315c, 344)
void UniteEffect_Init(void* arg) {
    (void)arg;
    auto** const work_slot = reinterpret_cast<u8**>(0x0043DD90);
    u8* work = *work_slot;
    if (work == nullptr) {
        work = reinterpret_cast<u8*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x958, 1)
        );
        *work_slot = work;
    }
    ui::AsdMem_Zero(work, 0x958);

    using CreateCalc = void* (*)(const char*, u32, u32, u32, void*, void*, void*);
    using CreateDraw = void* (*)(const char*, u32, u32, u32, void*, u32, void*, void*);

    void* const calc_task = reinterpret_cast<CreateCalc>(0x002C5978)(
        "TMD CALC", 2, 0, 0,
        reinterpret_cast<void*>(0x00329DA4),
        nullptr,
        nullptr
    );
    *reinterpret_cast<void**>(work) = calc_task;

    reinterpret_cast<CreateDraw>(0x002C4C00)(
        "TMD DDRAW", 0xE7, 0, 0,
        reinterpret_cast<void*>(0x00330CFC),
        0,
        nullptr,
        calc_task
    );

    reinterpret_cast<CreateDraw>(0x002C4C00)(
        "TMD DDRAW", 0x6F, 0, 0,
        reinterpret_cast<void*>(0x0032B0B4),
        0,
        nullptr,
        calc_task
    );

    btlTalkBustUp_func_002959c4();
    script_vm_func_002c0128();
    camp_func_002976ac(0x25);
}

//
void Unite_DrawAndCalc_Decompiled(void* arg) {
    (void)arg;
    UniteWork* work = g_UniteWork;
    if (work == nullptr || work->state == 0) {
        return;
    }

    // State machine logic
    switch (work->state) {
        case 1: // Fusion formula selection (2-demon, special, search fusion)
            break;
        case 2: // Result preview & skill inheritance picking
            break;
        case 3: // Fusion cutscene & accident roll
            work->state = 4;
            break;
        case 4: // Fusion completed / Demon registered to compendium
            work->state = 0;
            break;
        default:
            break;
    }

    // Stereoscopic rendering pass for Mido Cathedral of Shadows fusion room
    ui::UiGpu_BeginPass(ui::g_AsdGpuState);
    ui::UiGpu_SetViewportParams(1, 0); // Upper screen 3D stage

    auto* layer = reinterpret_cast<u32*>(ui::g_AsdGpuState + 0x124C);
    const u32 old_depth = *layer;
    *layer = old_depth + 1;
    auto* layer_entry = reinterpret_cast<u32*>(ui::g_AsdGpuState + 0x124C + 8);
    layer_entry[*layer] = 1;

    // Draw fusion circle and preview demons
    ui::UiSprite_DrawPanelDirect(2, 0x0E, 0x30, 200, 120, 1);

    if (*layer > 0) {
        *layer = *layer - 1;
    }
}
extern "C" {
    void  func_002c3344(void* slot);                                            // 0x002c3344
    void  func_002c32f8(void* slot, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5,
                        u32 a6, u32 a7, u32 a8, u32 a9, u32 a10);               // 0x002c32f8
    void  func_002bdb2c(void* obj, s32 a1, s32 a2, void* slot, s32 a4, f32 f);  // 0x002bdb2c
    void  func_00262448(void* obj, s32 a1, s32 a2, s32 a3);                     // 0x00262448
    void  func_00296154(void* obj, s32 a1, s32 a2);                             // 0x00296154
    u32   func_002bda1c(u32 a0);                                                // 0x002bda1c
    void  func_002bda10(u32 handle, u32 color);                                 // 0x002bda10
    void  func_002bda00(u32 handle, s32 a1, u32 color, f32 a3);                 // 0x002bda00
    u32   func_002972f8(u32 a0, u32 a1);                                        // 0x002972f8
}

// DECOMP_FUNC(0x0028d974, 736)
void ButtonHelp_Init() {
    static constexpr u32 kStride = 0x8C;
    static constexpr u32 kTargetW = 0x004025A0;

    auto* const mgr = reinterpret_cast<u8*>(0x0043DA28);
    if (static_cast<s8>(mgr[0]) <= 0) {
        auto* work = *reinterpret_cast<u8**>(mgr + 0x04);
        if (work == nullptr) {
            work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, sizeof(ButtonHelpWork), 1));
            *reinterpret_cast<u8**>(mgr + 0x04) = work;
        }
        AsdMem_Zero(work, sizeof(ButtonHelpWork));

        void* const calc_task = AsdTask_CreateCalc(
            "ButtonHelp CALC",
            1,
            0,
            0,
            reinterpret_cast<void (*)(void*)>(0x001C0B38),
            0x002108CCu,
            0);
        *reinterpret_cast<void**>(work + 0x00) = calc_task;
        *reinterpret_cast<void**>(work + 0x08) = AsdTask_CreateDraw(
            "ButtonHelp DDRAW",
            0xE6,
            0,
            0,
            reinterpret_cast<void (*)(void*)>(0x002108D0),
            0,
            0,
            calc_task);

        auto* const w2 = *reinterpret_cast<u8**>(mgr + 0x04);
        func_002c3344(w2 + 0x14);
        func_002c32f8(
            w2 + 0x14,
            kTargetW - 0x4A,
            0x30,
            kTargetW - 0x18,
            0x0C,
            kTargetW - 0x0C,
            0x0C,
            0,
            0,
            kTargetW,
            0xA8);

        for (s32 i = 0; i < 6; ++i) {
            u8* const entry = w2 + 0x34 + (i * kStride);
            func_002bdb2c(entry, 0x12, 3, w2 + 0x14, 0x10, 1.0f);
            func_00262448(entry, 0x12, 0x11 + i, 3);
        }

        func_002bdb2c(w2 + 0x37C, 0x12, 0, w2 + 0x14, 0x10, 1.0f);
        func_002bdb2c(w2 + 0x408, 0x12, 1, w2 + 0x14, 0x10, 1.0f);

        auto* const w3 = *reinterpret_cast<u8**>(mgr + 0x04);
        w3[0x4C8] = 0;
        for (s32 i = 0; i < 2; ++i) {
            u8* const entry = w3 + 0x37C + (i * kStride);
            *reinterpret_cast<u16*>(entry + 0x3A) = 2;
            func_00296154(entry, 0x12, 0);
            entry[0x3C] = 1;
            *reinterpret_cast<u32*>(entry + 0x0C) = 0;
            *reinterpret_cast<u32*>(entry + 0x10) = 0;
            *reinterpret_cast<u32*>(entry + 0x14) = 0;
        }

        w2[0x4C5] = 0;
        w2[0x4C6] = 1;
        w2[0x4C4] = 1;
        w2[0x4C7] = 0;

        const u32 h = func_002bda1c(0);
        *reinterpret_cast<u32*>(work + 0x558) = h;
        func_002bda10(h, 0x323232FF);
        func_002bda00(*reinterpret_cast<u32*>(work + 0x558), 0, 0x646464FF, 0.0f);
        *reinterpret_cast<u32*>(work + 0x560) = func_002972f8(
            *reinterpret_cast<const u32*>(mgr + 0x0C),
            *reinterpret_cast<const u32*>(mgr + 0x08));
    }

    mgr[0] = static_cast<u8>(mgr[0] + 1);
}

extern "C" {
    void func_002af854(void* obj, s32 a1, s32 a2);                              // 0x002af854
    void func_002bf030(void* obj, s32 a1);                                      // 0x002bf030
    void func_002bdac0(void* obj, s32 a1, s32 a2);                              // 0x002bdac0
    void func_002c4450(void* obj, s32 a1, s32 a2);                              // 0x002c4450
}

// DECOMP_FUNC(0x0029e63c, 644)
void SortMenu_Init(s32 mode, u32 flag) {
    static constexpr u32 kStride = 0x8C;
    static constexpr u32 kTargetW = 0x00402DAC;

    auto* const mgr = reinterpret_cast<u8*>(0x0043DD20);
    if (static_cast<s8>(mgr[0]) <= 0) {
        auto* work = *reinterpret_cast<u8**>(mgr + 0x04);
        if (work == nullptr) {
            work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, sizeof(SortMenuWork), 1));
            *reinterpret_cast<u8**>(mgr + 0x04) = work;
        }
        AsdMem_Zero(work, sizeof(SortMenuWork));

        void* const calc_task = AsdTask_CreateCalc(
            "SORT CALC",
            2,
            0,
            0,
            reinterpret_cast<void (*)(void*)>(0x001A1E7C),
            0,
            0);
        *reinterpret_cast<void**>(work + 0x00) = calc_task;
        *reinterpret_cast<void**>(work + 0x04) = AsdTask_CreateDraw(
            "SORT DDRAW",
            0xE7,
            0,
            0,
            reinterpret_cast<void (*)(void*)>(0x001A25CC),
            0,
            0,
            calc_task);

        auto* const w2 = *reinterpret_cast<u8**>(mgr + 0x04);
        func_002c3344(w2 + 0x08);
        func_002c32f8(
            w2 + 0x08,
            kTargetW - 0x3C,
            0x18,
            kTargetW - 0x24,
            0x24,
            0,
            0,
            0,
            0,
            kTargetW,
            0xA8);

        for (s32 i = 0; i < 0x0D; ++i) {
            u8* const entry = w2 + 0x28 + (i * kStride);
            func_002bdb2c(entry, 0x1E, 0, w2 + 0x08, 1, 1.0f);
            func_002af854(entry, 0, 0);
        }

        func_002bdb2c(w2 + 0x5A0, 0x1E, 0, w2 + 0x08, 1, 1.0f);
        func_002bf030(w2 + 0x5A0, 0);

        u8* const entry_a = w2 + 0x62C;
        func_002bdb2c(entry_a, 0x1E, 0, w2 + 0x08, 1, 1.0f);
        func_002bdac0(entry_a, 0, 0);

        u8* const entry_b = w2 + 0x6B8;
        func_002bdb2c(entry_b, 0x1E, 0, w2 + 0x08, 1, 1.0f);
        func_002bf030(entry_b, 1);

        func_002c4450(w2 + 0x76C, 0x1A, -1);
        *reinterpret_cast<u32*>(w2 + 0x744) = 0;
        w2[0x74D] = 1;
        work[0x74E] = static_cast<u8>(flag);
        *reinterpret_cast<s32*>(work + 0x750) = mode;
    }

    mgr[0] = static_cast<u8>(mgr[0] + 1);
}

extern "C" {
    void* engine_func_002c54f0(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);   // 0x002c54f0
    u8*   func_002b9364(u32 demon_id);                                          // 0x002b9364
    u32   func_0026a904(u32 skill_id);                                          // 0x0026a904
    const u8* func_002840b8(u32 skill_id);                                      // 0x002840b8
    s32   func_002992d8(u32 val, s32 mapped);                                   // 0x002992d8
    void  func_002b7f0a(void* base, s32 count, s32 size, u32 comparator);       // 0x002b7f0a
    s32   func_00205404(u16* out, u8* demon, const u32* entry, const u16* idp); // 0x00205404
    const u8* func_0029ec14(u32 skill_id);                                      // 0x0029ec14
    s32   func_002ae3f0(u32 skill_id);                                          // 0x002ae3f0
    s32   func_0026a86c(const u8* info);                                        // 0x0026a86c
    void  func_001df7d0(void* ctx);                                             // 0x001df7d0
    void  func_001cfed0(void* ctx);                                             // 0x001cfed0
    s32   func_001d00f8(void* ctx);                                             // 0x001d00f8
    void  engine_func_002c5ff4(void* dst, const void* src, u32 size);           // 0x002c5ff4
    void  AsdMem_Free(void* ptr);                                               // 0x002c4360
}

namespace {
struct UniteSkillFilterCtx {
    u32 vtable;        // +0x00 (sp+0x58)
    u16* arr0;         // +0x04 (sp+0x5C)
    s32 count0;        // +0x08 (sp+0x60)
    u16* arr1;         // +0x0C (sp+0x64)
    s32 count1;        // +0x10 (sp+0x68)
    u16* arr2;         // +0x14 (sp+0x6C)
    s32 count2;        // +0x18 (sp+0x70)
    u16* arr3;         // +0x1C (sp+0x74)
    s32 count3;        // +0x20 (sp+0x78)
    u16* arr4;         // +0x24 (sp+0x7C)
    s32 count4;        // +0x28 (sp+0x80)
    u8 best_affinity;  // +0x2C (sp+0x84)
    u8 pad_2d[3];      // +0x2D..+0x2F
    u32 counts[22];    // +0x30..+0x87 (sp+0x88..sp+0xDF)
};
} // namespace

// DECOMP_FUNC(0x0029b3cc, 1676)
void Unite_Init(void* r0, void* r1, s32 r2, void* r3) {
    static constexpr u32 kVtable = 0x00420430;
    static constexpr u32 kComparator1 = 0x002C6C54;
    static constexpr u32 kComparator2 = 0x002DCA40;

    auto* const skills = static_cast<u16*>(r0);
    const s32 skill_count = static_cast<s32>(reinterpret_cast<intptr_t>(r1));
    const auto* const demon_entry = reinterpret_cast<const u32*>(
        static_cast<uintptr_t>(static_cast<u32>(r2)));
    const auto* const demon_id_ptr = static_cast<const u16*>(r3);

    UniteSkillFilterCtx ctx{};
    ctx.vtable = kVtable;
    AsdMem_Zero(ctx.counts, sizeof(ctx.counts));

    u32 demon_id = 0;
    if (demon_entry != nullptr) {
        demon_id = ((demon_entry[1] << 15) | (demon_entry[0] >> 17)) >> 17;
    } else if (demon_id_ptr != nullptr) {
        demon_id = *demon_id_ptr;
    }

    const u32 buf_bytes = static_cast<u32>(skill_count) << 1;
    ctx.arr0 = static_cast<u16*>(engine_func_002c54f0(0x100, 0x100, 0, buf_bytes, 1));
    ctx.arr1 = static_cast<u16*>(engine_func_002c54f0(0x100, 0x100, 0, buf_bytes, 1));
    ctx.arr4 = static_cast<u16*>(engine_func_002c54f0(0x100, 0x100, 0, buf_bytes, 1));

    u8* const demon = func_002b9364(demon_id);
    u32 cat_counts[7] = {};
    for (s32 i = 0; i < 8; ++i) {
        const u16 sk = *reinterpret_cast<const u16*>(demon + 0x3C + i * 2);
        if (sk != 0) {
            ++cat_counts[func_0026a904(sk)];
        }
    }

    u32 best_val = cat_counts[0];
    for (s32 i = 1; i < 7; ++i) {
        if (cat_counts[i] > best_val) {
            ctx.best_affinity = static_cast<u8>(i);
            best_val = cat_counts[i];
        }
    }
    if (ctx.best_affinity == 6) {
        ctx.best_affinity = 0;
    }

    for (s32 i = 0; i < skill_count; ++i) {
        const u16 s = skills[i];
        bool innate_match = false;
        for (s32 j = 0; j < 8; ++j) {
            if (*reinterpret_cast<const u16*>(demon + 0x4E + j * 4) == s) {
                ctx.arr4[ctx.count4++] = s;
                innate_match = true;
                break;
            }
        }
        if (innate_match) {
            continue;
        }

        const u8* const info = func_002840b8(s);
        if (info != nullptr) {
            const u32 flags = *reinterpret_cast<const u32*>(info + 0x38);
            if (((flags << 21) >> 27) == 5) {
                const u32 sub = (flags << 12) >> 28;
                if (sub == 5 || sub == 6) {
                    ctx.arr1[ctx.count1++] = s;
                    continue;
                }
                if (sub >= 1 && sub <= 4) {
                    s32 mapped = 0;
                    if (sub == 1) {
                        mapped = 5;
                    } else if (sub == 2) {
                        mapped = 1;
                    } else if (sub == 3) {
                        mapped = 3;
                    } else {
                        mapped = 4;
                    }
                    const u16 val = *reinterpret_cast<const u16*>(
                        demon + 0x6C + ((flags & 0xF800) >> 10));
                    if (func_002992d8(val >> 10, mapped) == 0) {
                        ctx.arr4[ctx.count4++] = s;
                        continue;
                    }
                }
            }
        }

        ctx.arr0[ctx.count0++] = s;
    }

    func_002b7f0a(ctx.arr1, ctx.count1, 2, kComparator1);
    func_002b7f0a(ctx.arr4, ctx.count4, 2, kComparator2);

    ctx.count2 = func_00205404(nullptr, demon, demon_entry, demon_id_ptr);
    ctx.arr2 = static_cast<u16*>(
        engine_func_002c54f0(0x100, 0x100, 0, static_cast<u32>(ctx.count2) << 1, 1));
    func_00205404(ctx.arr2, demon, demon_entry, demon_id_ptr);

    for (s32 i = 0; i < ctx.count2; ++i) {
        const u8 idx = func_0029ec14(ctx.arr2[i])[2];
        ++ctx.counts[idx];
    }

    ctx.arr3 = static_cast<u16*>(engine_func_002c54f0(0x100, 0x100, 0, buf_bytes, 1));
    ctx.count3 = 0;

    bool promoted = false;
    for (s32 i = 0; i < ctx.count1 && !promoted; ++i) {
        const u16 sk = ctx.arr1[i];
        if (sk == 0) {
            continue;
        }
        const u8* const info = func_002840b8(sk);
        for (s32 j = 0; j < 8; ++j) {
            const u16 dsk = *reinterpret_cast<const u16*>(demon + 0x3C + j * 2);
            if (dsk != 0 && func_002ae3f0(dsk) != 0 && func_0026a86c(info) != 0) {
                ctx.arr3[ctx.count3++] = sk;
                ctx.arr1[i] = 0;
                promoted = true;
                break;
            }
        }
    }

    func_001df7d0(&ctx);
    func_001cfed0(&ctx);
    func_001d00f8(&ctx);
    func_001df7d0(&ctx);
    func_001cfed0(&ctx);
    while (func_001d00f8(&ctx) != 0) {
    }

    for (s32 i = 0; i < ctx.count1; ++i) {
        if (ctx.arr1[i] != 0) {
            ctx.arr3[ctx.count3++] = ctx.arr1[i];
            ctx.arr1[i] = 0;
        }
    }
    for (s32 i = 0; i < ctx.count4; ++i) {
        if (ctx.arr4[i] != 0) {
            ctx.arr3[ctx.count3++] = ctx.arr4[i];
            ctx.arr4[i] = 0;
        }
    }

    engine_func_002c5ff4(skills, ctx.arr3, buf_bytes);

    ctx.vtable = kVtable;
    if (ctx.arr0 != nullptr) {
        AsdMem_Free(ctx.arr0);
        ctx.arr0 = nullptr;
    }
    if (ctx.arr1 != nullptr) {
        AsdMem_Free(ctx.arr1);
        ctx.arr1 = nullptr;
    }
    if (ctx.arr2 != nullptr) {
        AsdMem_Free(ctx.arr2);
        ctx.arr2 = nullptr;
    }
    if (ctx.arr3 != nullptr) {
        AsdMem_Free(ctx.arr3);
        ctx.arr3 = nullptr;
    }
    if (ctx.arr4 != nullptr) {
        AsdMem_Free(ctx.arr4);
        ctx.arr4 = nullptr;
    }
}

extern "C" {
    void  func_0030f5ec(s32 a0);                                                // 0x0030f5ec
    void* AsdMemory_func_002c23f8(u32 size);                                    // 0x002c23f8
    void* func_003c9ebc(void* p);                                               // 0x003c9ebc
    u32   func_0029b18c();                                                      // 0x0029b18c
    void* engine_func_002c34a4(u32 a0, u32 a1, u32 a2, u32 a3, u32 a4, u32 a5); // 0x002c34a4
    void  func_002bcf34(void* obj, void* buf, u32 size);                        // 0x002bcf34
    u32   func_002bce50(void* dst, const void* desc, u32 cb, void* arg,
                        u32 end, u32 a5, s32 a6, u32 a7);                       // 0x002bce50
    void  func_002c5468(u32 handle);                                            // 0x002c5468
    s32   func_002c0ba8(u32 id);                                                // 0x002c0ba8
    u8*   func_002a0fac();                                                      // 0x002a0fac
    void  func_002a043c();                                                      // 0x002a043c
    u8*   func_002a89e4(s32 idx);                                               // 0x002a89e4
    s32   func_0029ee4c(u8* demon, s32 flag);                                   // 0x0029ee4c
    void  func_002976ac(s32 id);                                                // 0x002976ac
    u32   func_002c5e2c(const char* path);                                      // 0x002c5e2c
    s32   func_002a0dd4();                                                      // 0x002a0dd4
    s32   func_002b8adc();                                                      // 0x002b8adc
    void  func_00294ad8(s32 a0, s32 a1, s32 a2, s32 a3,
                        f32 s0, f32 s1, f32 s2, f32 s3, f32 s4,
                        f32 s5, f32 s6, f32 s7, f32 s8,
                        u32 st0, u32 st1, u32 st2, u32 st3,
                        u32 st4, u32 st5, u32 st6, u32 st7);                    // 0x00294ad8
    u32   func_00263e48(const char* path);                                      // 0x00263e48
    void  func_002950bc(s32 a0);                                                // 0x002950bc
    u32   func_0029a2d0(const char* path, s32 a1);                              // 0x0029a2d0
    u32   func_00290a4c();                                                      // 0x00290a4c
}

// DECOMP_FUNC(0x001f2f58, 1704)
void Unite_Setup(void*) {
    static constexpr u32 kWorkSize = 0x95F8;
    static constexpr u32 kTargetW = 0x004031D0;

    auto** const mgr_slot = reinterpret_cast<u8**>(0x0043DD68);
    u8* work = *mgr_slot;
    if (work == nullptr) {
        work = static_cast<u8*>(AsdMem_Alloc(0x100, 0x100, 0, kWorkSize, 1));
        *mgr_slot = work;
    }
    AsdMem_Zero(work, kWorkSize);
    *reinterpret_cast<s32*>(work + 0x9460) = -1;
    func_0030f5ec(0);

    void* const calc_task = AsdTask_CreateCalc(
        "Unite Calc",
        2,
        0,
        0,
        reinterpret_cast<void (*)(void*)>(0x0017FE9C),
        0,
        0);
    *reinterpret_cast<void**>(work + 0x3F8) = calc_task;
    AsdTask_CreateDraw(
        "Unite DDraw",
        0xE6,
        0,
        0,
        reinterpret_cast<void (*)(void*)>(0x001ADC98),
        0,
        0,
        calc_task);

    void* p0 = AsdMemory_func_002c23f8(0x180);
    if (p0 != nullptr) {
        p0 = func_003c9ebc(p0);
    }
    *reinterpret_cast<void**>(work + 0x00) = p0;
    *reinterpret_cast<u32*>(work + 0x9464) = func_0029b18c();
    work[0x95E0] = 0;

    void* const buf = engine_func_002c34a4(0x100, 0x100, 0, 0x1000, 0x1000, 1);
    *reinterpret_cast<void**>(work + 0x95F0) = buf;
    auto* const obj18 = static_cast<u8*>(AsdMemory_func_002c23f8(0x18));
    if (obj18 != nullptr) {
        *reinterpret_cast<u32*>(obj18 + 0x00) = 0;
        *reinterpret_cast<u32*>(obj18 + 0x04) = 0;
        *reinterpret_cast<u32*>(obj18 + 0x08) = 0;
        *reinterpret_cast<u32*>(obj18 + 0x0C) = 0;
        obj18[0x10] = 0;
    }
    *reinterpret_cast<u8**>(work + 0x95E4) = obj18;
    func_002bcf34(obj18, buf, 0x1000);

    u8* cb_arg = work;
    const u32 desc[4] = {4, 0x003F70D0, 0x003F7218, 0x003F7194};
    const u32 end_addr = *reinterpret_cast<const u32*>(obj18 + 0x08) +
                         *reinterpret_cast<const u32*>(obj18 + 0x0C);
    const u32 handle = func_002bce50(
        work + 0x95E8, desc, 0x001DE238, &cb_arg, end_addr, 0x11, -2, 0);
    if ((handle & 0x07E00000) != 0x00600000 && static_cast<s32>(handle) < 0) {
        func_002c5468(handle);
    }

    if (func_002c0ba8(0x418) == 0) {
        u8* const st = func_002a0fac();
        *reinterpret_cast<s16*>(st + 0x1C) = -1;
        *reinterpret_cast<s16*>(st + 0x1E) = -1;
        *reinterpret_cast<s16*>(st + 0x20) = 0;
        *reinterpret_cast<s16*>(st + 0x22) = 0;
        *reinterpret_cast<s16*>(st + 0x24) = 0;
        *reinterpret_cast<s16*>(st + 0x26) = 0;
        *reinterpret_cast<s16*>(st + 0x28) = 0;
        *reinterpret_cast<s16*>(st + 0x2A) = -1;
        st[0x2F] = 0;
        st[0x30] = 0;
        st[0x31] = 0xFF;
        st[0x32] = 0;
        st[0x33] = 0;
        func_002a043c();
    }

    u8* const st2 = func_002a0fac();
    if (*reinterpret_cast<const s16*>(st2 + 0x1C) >= 0) {
        const u16 id0 = *reinterpret_cast<const u16*>(st2 + 0x20);
        if (id0 == 0) {
            *reinterpret_cast<s16*>(st2 + 0x1C) = -1;
        } else {
            u8* const d = func_002a89e4(*reinterpret_cast<const s16*>(st2 + 0x1C));
            if (*reinterpret_cast<const u16*>(d + 0x46) != id0 ||
                func_0029ee4c(d, 0x0A) != 0 ||
                func_0029ee4c(d, 2) != 0) {
                *reinterpret_cast<s16*>(st2 + 0x1C) = -1;
                *reinterpret_cast<u16*>(st2 + 0x20) = 0;
            }
        }
    }
    if (*reinterpret_cast<const s16*>(st2 + 0x1E) >= 0) {
        const u16 id1 = *reinterpret_cast<const u16*>(st2 + 0x22);
        if (id1 == 0) {
            *reinterpret_cast<s16*>(st2 + 0x1E) = -1;
        } else {
            u8* const d = func_002a89e4(*reinterpret_cast<const s16*>(st2 + 0x1E));
            if (*reinterpret_cast<const u16*>(d + 0x46) != id1) {
                *reinterpret_cast<s16*>(st2 + 0x1E) = -1;
                *reinterpret_cast<u16*>(st2 + 0x22) = 0;
            }
        }
    }

    func_002c4450(work + 0x438, 0x80, -1);
    func_002a043c();

    func_002c3344(work + 0x04);
    func_002c32f8(
        work + 0x04,
        kTargetW - 0x90,
        0x54,
        kTargetW - 0x3C,
        0x3C,
        0,
        0,
        0,
        0,
        kTargetW,
        0x16C);

    func_002bdb2c(work + 0x24, 0x24, 0, work + 0x04, 1, 1.0f);
    func_002bf030(work + 0x24, 0);

    func_002bdb2c(work + 0xB0, 0x24, 0, work + 0x04, 1, 1.0f);
    func_002bdac0(work + 0xB0, 0, 0);

    func_002bdb2c(work + 0x13C, 0x24, 0, work + 0x04, 1, 1.0f);
    func_002bf030(work + 0x13C, 1);

    func_002bdb2c(work + 0x1C8, 0x24, 0, work + 0x04, 1, 1.0f);
    func_002bdac0(work + 0x1C8, 1, 0);

    func_002bdb2c(work + 0x254, 0x24, 0, work + 0x04, 1, 1.0f);
    func_002bdac0(work + 0x254, 5, 0);

    func_002bdb2c(work + 0x2E0, 0x24, 0, work + 0x04, 1, 1.0f);
    func_002bf030(work + 0x2E0, 2);

    func_002bdb2c(work + 0x36C, 0x24, 0, work + 0x04, 1, 1.0f);
    func_002bf030(work + 0x36C, 3);

    func_002976ac(0x24);
    func_002976ac(0x22);
    *reinterpret_cast<s32*>(work + 0x434) = -1;
    *reinterpret_cast<s32*>(work + 0x478) = -1;
    *reinterpret_cast<u32*>(work + 0x424) = func_002c5e2c("unite/unite.mbm");
    *reinterpret_cast<u32*>(work + 0x428) = func_002c5e2c("unite/unite.bf");
    *reinterpret_cast<u32*>(work + 0x42C) = func_002972f8(
        *reinterpret_cast<const u32*>(work + 0x428),
        *reinterpret_cast<const u32*>(work + 0x424));

    if (func_002a0dd4() != 0 || func_002b8adc() != 0) {
        func_00294ad8(
            0, 0, 0, 0,
            0.0f, -1.0f, -565.0f, 1335.0f, 0.0f,
            -100.0f, 1500.0f, 1500.0f, 100.0f,
            0, 0, 0xFF, 0, 0, 0xFF, 0, 0);
    }

    *reinterpret_cast<u32*>(work + 0x95D0) = func_00263e48("camp/jakyou_all.bccam");
    func_002950bc(1);
    *reinterpret_cast<u32*>(work + 0x95C8) = func_0029a2d0("camp/jakyou_all.bam", 7);
    *reinterpret_cast<u32*>(work + 0x95CC) = func_0029a2d0("camp/jakyou_all_mido.bam", 7);
    *reinterpret_cast<u32*>(work + 0x95D8) = 0;
    *reinterpret_cast<u32*>(work + 0x95DC) = 0;
    *reinterpret_cast<u32*>(work + 0x41C) = func_00290a4c();
}

// DECOMP_FUNC(0x001de238, 5020)


//
__attribute__((naked)) void Unite_DrawAndCalc(void*)
{
    asm volatile(
        ".word 0xE92D4FF0, 0xE24DD0AC, 0xE1A04000, 0xE2800C95\n"
        ".word 0xE58D007C, 0xE2840B25, 0xE2800064, 0xE58D0080\n"
        ".word 0xE2840A01, 0xE2800E39, 0xE58D0008, 0xE2840A06\n"
        ".word 0xE2800E1B, 0xE58D001C, 0xE2840A06, 0xE2800F85\n"
        ".word 0xE58D0060, 0xE2840C62, 0xE58D0084, 0xE2840B25\n"
        ".word 0xE58D0074, 0xE2840A09, 0xE2800E46, 0xE58D0078\n"
        ".word 0xE2840A09, 0xE2800E45, 0xE58D0088, 0xE2840A06\n"
        ".word 0xE2800E67, 0xE58D0068, 0xE2840B01, 0xE2800F6D\n"
        ".word 0xE58D0070, 0xE59D007C, 0xE5D000E0, 0xE3500000\n"
        ".word 0x1A0004B1, 0xEB030B36, 0xE1A01000, 0xE5940400\n"
        ".word 0xE281101C, 0xE58D1058, 0xE3500005, 0x0A000002\n"
        ".word 0xE3500006, 0x13500002, 0x1A0004A1, 0xE59D0074\n"
        ".word 0xE5D00050, 0xE3500000, 0x0A00049D, 0xE5940000\n"
        ".word 0xEB07AB9C, 0xE5941400, 0xE3A00F4B, 0xE58405B0\n"
        ".word 0xE3510005, 0x1A000071, 0xE59D0058, 0xE3E03000\n"
        ".word 0xE1D020F0, 0xE5940000, 0xE3520000, 0xA3A01001\n"
        ".word 0xB3E02000, 0xB3A01000, 0xEB07AB20, 0xE59D0058\n"
        ".word 0xE3E03000, 0xE1D020F2, 0xE5940000, 0xE3520000\n"
        ".word 0xA3A01001, 0xB3E02000, 0xB3A01000, 0xEB07ABEA\n"
        ".word 0xE59D0058, 0xE1D000F8, 0xE3500000, 0xC59D0058\n"
        ".word 0xD3A02000, 0xC3A01001, 0xD1A01002, 0xC1D020B8\n"
        ".word 0xE5940000, 0xEB07AB92, 0xE59D0058, 0xE1D020BA\n"
        ".word 0xE5940000, 0xE3520000, 0x03A02000, 0x13A01001\n"
        ".word 0x01A01002, 0xEB07AA8B, 0xE59D0058, 0xE1D001D5\n"
        ".word 0xE3500000, 0xBA000005, 0xE59F19B8, 0xE7911100\n"
        ".word 0xE5940000, 0xE6FF2071, 0xE3A01001, 0xEA000002\n"
        ".word 0xE3A02000, 0xE5940000, 0xE1A01002, 0xEB07AD60\n"
        ".word 0xE59D0058, 0xE1D001D4, 0xE3500000, 0xE5940000\n"
        ".word 0xC3A01000, 0xD3A01001, 0xE5C01142, 0xE59D0058\n"
        ".word 0xE1D001D6, 0xE3500000, 0xE5940000, 0xC3A01001\n"
        ".word 0xD3A01000, 0xE5C0117C, 0xE59D0058, 0xE1D001D7\n"
        ".word 0xE3500000, 0xE5940000, 0xC3A01001, 0xD3A01000\n"
        ".word 0xE5C0117D, 0xE59D0058, 0xE1D000FE, 0xE3500000\n"
        ".word 0xBA00000C, 0xE59D0058, 0xE1D010BE, 0xE1DD00B0\n"
        ".word 0xE2002B3F, 0xE3C10B3F, 0xE1800002, 0xE3C00B3F\n"
        ".word 0xE3800B05, 0xE1CD00B0, 0xE5940000, 0xE1A0200D\n"
        ".word 0xE3A01001, 0xEA000002, 0xE3A02000, 0xE5940000\n"
        ".word 0xE1A01002, 0xEB07ABA5, 0xE59D0058, 0xE1D000BC\n"
        ".word 0xE3500000, 0x0A00000C, 0xE3A00000, 0xE58D0090\n"
        ".word 0xE58D0094, 0xE58D0098, 0xE58D009C, 0xE59D0058\n"
        ".word 0xE28D3090, 0xE3A02000, 0xE3A01001, 0xE1D000BC\n"
        ".word 0xE1CD09B0, 0xE5940000, 0xEA000003, 0xE3A03000\n"
        ".word 0xE5940000, 0xE1A02003, 0xE1A01003, 0xEB07AB41\n"
        ".word 0xE5940400, 0xE3500002, 0x1A000029, 0xE5940000\n"
        ".word 0xE3A01001, 0xE5C0117D, 0xE5940000, 0xE3A01001\n"
        ".word 0xE5C01142, 0xE3E03000, 0xE5940000, 0xE1A02003\n"
        ".word 0xE3A01000, 0xEB07AAA9, 0xE3E03000, 0xE5940000\n"
        ".word 0xE1A02003, 0xE3A01000, 0xEB07AB77, 0xE3A02000\n"
        ".word 0xE5940000, 0xE1A01002, 0xEB07AB25, 0xE3A02000\n"
        ".word 0xE5940000, 0xE1A01002, 0xEB07AA22, 0xE3A02000\n"
        ".word 0xE5940000, 0xE1A01002, 0xEB07AD01, 0xE5940000\n"
        ".word 0xE3A01000, 0xE5C0117C, 0xE3A02000, 0xE5940000\n"
        ".word 0xE1A01002, 0xEB07AB69, 0xE3A03000, 0xE5940000\n"
        ".word 0xE1A02003, 0xE1A01003, 0xEB07AB16, 0xE3A00E7D\n"
        ".word 0xE58405B0, 0xE3A05000, 0xE58455B4, 0xE59D0068\n"
        ".word 0xE3A01DFA, 0xE5805000, 0xE59D0008, 0xEB03995D\n"
        ".word 0xE58455B8, 0xE59D0058, 0xE5D00013, 0xE3500000\n"
        ".word 0x15940400, 0x13500002, 0x0A00001A, 0xE59D0058\n"
        ".word 0xE1D000F0, 0xE3500000, 0xBA0000F2, 0xEB02FEA5\n"
        ".word 0xE1A09000, 0xE59D0080, 0xE5901000, 0xE1510009\n"
        ".word 0xB1A09001, 0xE249800A, 0xE358004C, 0xC3A0804C\n"
        ".word 0xCA000002, 0xE3580001, 0xB3A08001, 0xB3A0900B\n"
        ".word 0xE59D0058, 0xE1D000F0, 0xEB0328EF, 0xE1A06000\n"
        ".word 0xE3A0100A, 0xEB030206, 0xE3500000, 0xE320F000\n"
        ".word 0x1A0000C4, 0xEA00006E, 0xE3A08000, 0xEB0328F4\n"
        ".word 0xE3500000, 0xE320F000, 0xDA0001BC, 0xE2840E5B\n"
        ".word 0xE8900003, 0xE1510000, 0x2A0001B8, 0xE2886001\n"
        ".word 0xEB0328EB, 0xE1500006, 0xE320F000, 0xDA00005A\n"
        ".word 0xE2840E5B, 0xE8900003, 0xE1510000, 0x2A000056\n"
        ".word 0xEB0328DE, 0xE0800008, 0xE2800A09, 0xE1D00FD0\n"
        ".word 0xEB0328D1, 0xE1A05000, 0xE320F000, 0xEB0328D7\n"
        ".word 0xE0800006, 0xE2800A09, 0xE1D00FD0, 0xEB0328CA\n"
        ".word 0xE3550000, 0xE1A07000, 0x13570000, 0x0A000046\n"
        ".word 0xE3A0100A, 0xE1A00005, 0xEB0301DD, 0xE3500000\n"
        ".word 0xE320F000, 0x1A00003B, 0xE3A0100A, 0xE1A00007\n"
        ".word 0xEB0301D7, 0xE3500000, 0xE320F000, 0x1A000035\n"
        ".word 0xE3A01002, 0xE1A00005, 0xEB0301D1, 0xE3500000\n"
        ".word 0xE320F000, 0x1A00002F, 0xE3A01002, 0xE1A00007\n"
        ".word 0xEB0301CB, 0xE3500000, 0xE320F000, 0x1A000029\n"
        ".word 0xE5940000, 0xEB022DBD, 0xE5940000, 0xE2852034\n"
        ".word 0xE3A01000, 0xEB021099, 0xE5940000, 0xE2872034\n"
        ".word 0xE3A01001, 0xEB021095, 0xE59405B4, 0xE0840180\n"
        ".word 0xE2802A01, 0xE5921390, 0xE5920394, 0xE3C11103\n"
        ".word 0xE3811101, 0xE5821390, 0xE59D2070, 0xE3C00003\n"
        ".word 0xE3800001, 0xE5922000, 0xE0842182, 0xE2822A01\n"
        ".word 0xE5A21390, 0xE5820004, 0xE59D0070, 0xE1D724B6\n"
        ".word 0xE1D514B6, 0xE5900000, 0xE0840180, 0xE2803A01\n"
        ".word 0xE5940000, 0xE2833E39, 0xEB020FD1, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000003, 0xE59405B4, 0xE2801001\n"
        ".word 0xE59D0070, 0xE5801000, 0xE2866001, 0xEB032890\n"
        ".word 0xE1500006, 0xE320F000, 0xCAFFFFA4, 0xE2888001\n"
        ".word 0xEB03288B, 0xE1500008, 0xE320F000, 0xCAFFFF96\n"
        ".word 0xEA000152, 0xE3A01002, 0xE1A00006, 0xEB030190\n"
        ".word 0xE3500000, 0x03A05000, 0x028DA024, 0x1A00004D\n"
        ".word 0xE2840E5B, 0xE8900003, 0xE1510000, 0x2A000049\n"
        ".word 0xE1A00005, 0xEB030135, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000040, 0xE5940000, 0xEB022D78, 0xE5940000\n"
        ".word 0xE2862034, 0xE3A01000, 0xEB021054, 0xE59405B4\n"
        ".word 0xE0840180, 0xE2800A01, 0xE5901390, 0xE3C11103\n"
        ".word 0xE3811101, 0xE5801390, 0xE1A00005, 0xEB0347EA\n"
        ".word 0xE1B07000, 0xE320F000, 0x0A00000A, 0xE3A0100A\n"
        ".word 0xEB03016F, 0xE3500000, 0xE320F000, 0x1A000005\n"
        ".word 0xE3A01002, 0xE1A00007, 0xEB030169, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000031, 0xE28D1024, 0xE1A00005\n"
        ".word 0xEB02A6BF, 0xE59D0058, 0xE1D001D7, 0xE3500000\n"
        ".word 0xDA000003, 0xE1DD02B4, 0xE1500008, 0xA1590000\n"
        ".word 0xBA000018, 0xE59405B4, 0xE28A201C, 0xE0840180\n"
        ".word 0xE2800A01, 0xE5901394, 0xE3811003, 0xE5801394\n"
        ".word 0xE5940000, 0xE3A01001, 0xEB021028, 0xE59425B4\n"
        ".word 0xE1D614B6, 0xE5940000, 0xE0842182, 0xE2823A01\n"
        ".word 0xE2833E39, 0xE1A02005, 0xEB020F75, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000003, 0xE59405B4, 0xE59D1070\n"
        ".word 0xE2800001, 0xE5810000, 0xE2850001, 0xE6FF5070\n"
        ".word 0xE3550E4B, 0x9AFFFFB1, 0xE59405BC, 0xE350001E\n"
        ".word 0xAA0000FA, 0xE59F0420, 0xE3A01000, 0xEB0372C9\n"
        ".word 0xE59405BC, 0xE350001E, 0xBAFFFFF9, 0xEA0000F3\n"
        ".word 0xE59405B4, 0xE2872034, 0xE0840180, 0xE2800A01\n"
        ".word 0xE5901394, 0xE3C11003, 0xE3811001, 0xE5801394\n"
        ".word 0xE5940000, 0xE3A01001, 0xEB021000, 0xE320F000\n"
        ".word 0xE320F000, 0xEAFFFFD4, 0xE5940000, 0xE5D00118\n"
        ".word 0xE3500000, 0x13A00E7D, 0x158405B0, 0xE59D0058\n"
        ".word 0xE1D001D7, 0xE3500000, 0xC3A00E7D, 0xC58405B0\n"
        ".word 0xE59F03A8, 0xE5905000, 0xEB030971, 0xE280801C\n"
        ".word 0xE59F139C, 0xE28F0FE7, 0xE1A00000, 0xE3A00001\n"
        ".word 0xE3A01C01, 0xE58D0000, 0xE3A03C0A, 0xE3A02000\n"
        ".word 0xE1A00001, 0xEB039AB7, 0xE58D0000, 0xE5950000\n"
        ".word 0xE59D1000, 0xEB07AB65, 0xE1A0A000, 0xE320F000\n"
        ".word 0xEB02FD94, 0xE58D0004, 0xE59F038C, 0xE7901005\n"
        ".word 0xE59D0004, 0xE1510000, 0xB58D1004, 0xE59D0004\n"
        ".word 0xE240000A, 0xE350004C, 0xE58D0090, 0xC3A0004C\n"
        ".word 0xC58D0090, 0xD3500001, 0xAA000003, 0xE3A00001\n"
        ".word 0xE58D0090, 0xE3A0000B, 0xE58D0004, 0xE3A00000\n"
        ".word 0xE35A0000, 0xE58D000C, 0xDA0000A5, 0xE2850B01\n"
        ".word 0xE2800F6E, 0xE58D009C, 0xE2850B01, 0xE2800F6D\n"
        ".word 0xE2857B25, 0xE58D00A0, 0xE2850E5B, 0xE8900003\n"
        ".word 0xE1510000, 0x2A00009A, 0xE5D71050, 0xE3510000\n"
        ".word 0x0A000097, 0xE59D200C, 0xE59D1000, 0xE0811082\n"
        ".word 0xE1D110B0, 0xE1A00001, 0xE58D1014, 0xEB034752\n"
        ".word 0xE59D100C, 0xE1A0B000, 0xE2816001, 0xE15A0006\n"
        ".word 0xDA000082, 0xE59D0014, 0xE0801100, 0xE0811180\n"
        ".word 0xE58D10A4, 0xE2850E5B, 0xE8900003, 0xE1510000\n"
        ".word 0x2A00007A, 0xE5D71050, 0xE3510000, 0x0A000077\n"
        ".word 0xE5950000, 0xEB022CC1, 0xE35B0000, 0xE320F000\n"
        ".word 0x0A00000B, 0xE3A0100A, 0xE1A0000B, 0xEB0300C4\n"
        ".word 0xE3500000, 0xE320F000, 0x1A000005, 0xE3A01002\n"
        ".word 0xE1A0000B, 0xEB0300BE, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000025, 0xE320F000, 0xEB03880B, 0xE59D30A4\n"
        ".word 0xE1D821D7, 0xE0801103, 0xE2811903, 0xE3520000\n"
        ".word 0xE2811E17, 0xDA000005, 0xE1D100B0, 0xE59D2090\n"
        ".word 0xE1500002, 0xA59D2004, 0xA1520000, 0xBA000054\n"
        ".word 0xE281201C, 0xE5950000, 0xE3A01000, 0xEB020F7F\n"
        ".word 0xE59515B4, 0xE0851181, 0xE2811A01, 0xE5912390\n"
        ".word 0xE3822103, 0xE5812390, 0xE59D1000, 0xE0811086\n"
        ".word 0xE1D190B0, 0xE1A00009, 0xEB034713, 0xE3500000\n"
        ".word 0xE58D0020, 0x0A000015, 0xE3A0100A, 0xEB030098\n"
        ".word 0xE3500000, 0x0A00000B, 0xEA000010, 0xE5950000\n"
        ".word 0xE28B2034, 0xE3A01000, 0xEB020F68, 0xE59515B4\n"
        ".word 0xE0851181, 0xE2811A01, 0xE5912390, 0xE3C22103\n"
        ".word 0xE3822101, 0xEAFFFFE6, 0xE59D0020, 0xE3A01002\n"
        ".word 0xEB030087, 0xE3500000, 0xE320F000, 0x0A000063\n"
        ".word 0xE320F000, 0xEB0387D4, 0xE0892109, 0xE0822189\n"
        ".word 0xE1D811D7, 0xE0800102, 0xE2800903, 0xE3510000\n"
        ".word 0xE2800E17, 0xDA000005, 0xE1D010B0, 0xE59D2090\n"
        ".word 0xE1510002, 0xA59D2004, 0xA1520001, 0xBA00001C\n"
        ".word 0xE5953000, 0xE280201C, 0xE3A01001, 0xE1A00003\n"
        ".word 0xEB020F46, 0xE59515B4, 0xE0851181, 0xE2811A01\n"
        ".word 0xE1A00001, 0xED910AE4, 0xE5911394, 0xED800AE4\n"
        ".word 0xE3811003, 0xE5801394, 0xE59515B4, 0xE5950000\n"
        ".word 0xE1A02009, 0xE0851181, 0xE2813A01, 0xE59D1014\n"
        ".word 0xE2833E39, 0xEB020E8A, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000003, 0xE59515B4, 0xE59D00A0, 0xE2811001\n"
        ".word 0xE5801000, 0xE2866001, 0xE156000A, 0xBAFFFF80\n"
        ".word 0xE59515B8, 0xE59D009C, 0xE2811001, 0xE5801000\n"
        ".word 0xE59D000C, 0xE2800001, 0xE150000A, 0xE58D000C\n"
        ".word 0xBAFFFF60, 0xE59D0000, 0xEB03958E, 0xE59405BC\n"
        ".word 0xE350001E, 0xAA000005, 0xE59F004C, 0xE3A01000\n"
        ".word 0xEB0371D4, 0xE59405BC, 0xE350001E, 0xBAFFFFF9\n"
        ".word 0xE59D0074, 0xE5D00050, 0xE3500000, 0x0A000208\n"
        ".word 0xE59405B4, 0xE59415B0, 0xE1500001, 0x2A000061\n"
        ".word 0xE3500000, 0x0A00005F, 0xE5940400, 0xE3500002\n"
        ".word 0x0A000021, 0xEA00005B, 0x0040333C, 0x00989680\n"
        ".word 0x0043DD68, 0x000006D9, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x735C3638, 0x34736464, 0x6F72705C\n"
        ".word 0x6D617267, 0x6D61635C, 0x6E555C70, 0x5C657469\n"
        ".word 0x74696E55, 0x70632E65, 0x00000070, 0x00009464\n"
        ".word 0xE59D1020, 0xE5950000, 0xE2812034, 0xE3A01001\n"
        ".word 0xEB020EF2, 0xE59515B4, 0xE0851181, 0xE2812A01\n"
        ".word 0xE5921394, 0xED920AE4, 0xE3C11003, 0xE3811001\n"
        ".word 0xED820AE4, 0xE5821394, 0xEAFFFFAA, 0xE59F1790\n"
        ".word 0xE3A06000, 0xE24F0084, 0xE1A00000, 0xE3A00001\n"
        ".word 0xE58D0000, 0xE59405B4, 0xE3A01C01, 0xE3A02000\n"
        ".word 0xE1A03180, 0xE1A00001, 0xEB0399AE, 0xE1A09000\n"
        ".word 0xE59D0070, 0xE3A05000, 0xE5900000, 0xE3500000\n"
        ".word 0x9A000019, 0xE0847185, 0xE2871A01, 0xE2811E39\n"
        ".word 0xE8910003, 0xE1A01781, 0xE18108A0, 0xE1A008A0\n"
        ".word 0xEB03693D, 0xE1A08000, 0xE320F000, 0xEB035E1C\n"
        ".word 0xE5D01076, 0xE5D80003, 0xE241100A, 0xE1510000\n"
        ".word 0xAA000005, 0xE2871A01, 0xE2811E39, 0xE0890186\n"
        ".word 0xEC910A02, 0xE2866001, 0xEC800A02, 0xE2855001\n"
        ".word 0xE59405B4, 0xE1500005, 0x8AFFFFE5, 0xE3560000\n"
        ".word 0x11A00009, 0x13A01000, 0xE58465B4, 0x0A000007\n"
        ".word 0xE0842181, 0xECB00A02, 0xE2822A01, 0xE2822E39\n"
        ".word 0xE2566001, 0xEC820A02, 0xE2811001, 0x1AFFFFF7\n"
        ".word 0xE1A00009, 0xEB03951B, 0xE2840E5B, 0xE8900003\n"
        ".word 0xE1500001, 0x9A00018D, 0xE3510000, 0x0A00018B\n"
        ".word 0xE5940400, 0xE3500002, 0x0A000046, 0xE59D0058\n"
        ".word 0xE1D001D7, 0xE3500000, 0xDA0000A9, 0xE59F1674\n"
        ".word 0xE3A06000, 0xE24F0F69, 0xE1A00000, 0xE3A00001\n"
        ".word 0xE58D0000, 0xE59405B4, 0xE3A01C01, 0xE3A02000\n"
        ".word 0xE1A03180, 0xE1A00001, 0xEB039966, 0xE1A09000\n"
        ".word 0xE59D0070, 0xE3A05000, 0xE5900000, 0xE3500000\n"
        ".word 0x9A000019, 0xE0847185, 0xE2871A01, 0xE2811E39\n"
        ".word 0xE8910003, 0xE1A01781, 0xE18108A0, 0xE1A008A0\n"
        ".word 0xEB0368F5, 0xE1A08000, 0xE320F000, 0xEB035DD4\n"
        ".word 0xE5D01076, 0xE5D80003, 0xE241100A, 0xE1510000\n"
        ".word 0xAA000005, 0xE2870A01, 0xE2800E39, 0xE0891186\n"
        ".word 0xEC900A02, 0xE2866001, 0xEC810A02, 0xE2855001\n"
        ".word 0xE59405B4, 0xE1500005, 0x8AFFFFE5, 0xE3560000\n"
        ".word 0x11A00009, 0x13A01000, 0xE58465B4, 0x0A000007\n"
        ".word 0xE0842181, 0xECB00A02, 0xE2822A01, 0xE2822E39\n"
        ".word 0xE2566001, 0xEC820A02, 0xE2811001, 0x1AFFFFF7\n"
        ".word 0xE1A00009, 0xEB0394D3, 0xE59F358C, 0xE59415B4\n"
        ".word 0xE59D0008, 0xE3A02008, 0xFB0363B8, 0xE320F000\n"
        ".word 0xE320F000, 0xEA00006A, 0xE3A02001, 0xE3A01000\n"
        ".word 0xE2820E46, 0xEB02AA60, 0xE59F355C, 0xE59415B4\n"
        ".word 0xE59D0008, 0xE3A02008, 0xFB0363AC, 0xE59D0070\n"
        ".word 0xE3A05000, 0xE1A09005, 0xE5900000, 0xE3500000\n"
        ".word 0x83A0B000, 0x9A00005A, 0xE084A189, 0xE28A2A01\n"
        ".word 0xE59F0528, 0xE5921394, 0xE0000001, 0xE190000B\n"
        ".word 0x0A00004A, 0xE3550000, 0xC2050001, 0xD3A00000\n"
        ".word 0xC3500000, 0xE3A01000, 0xDA000013, 0xE5923394\n"
        ".word 0xE592C390, 0xE1A03783, 0xE18338AC, 0xE1A038A3\n"
        ".word 0xE084C181, 0xE28C6B25, 0xE2866038, 0xE3A07000\n"
        ".word 0xE596C000, 0xE5966004, 0xE1A06786, 0xE186C8AC\n"
        ".word 0xE0276007, 0xE023C8AC, 0xE19CC006, 0x0A000025\n"
        ".word 0xE2811001, 0xE1500001, 0xCAFFFFF0, 0xE1500005\n"
        ".word 0xAA00001F, 0xE2822E39, 0xE8920006, 0xE1A02782\n"
        ".word 0xE18218A1, 0xE1A028A1, 0xE0843180, 0xE2831B25\n"
        ".word 0xE2811038, 0xE3A07000, 0xE5916004, 0xE591C000\n"
        ".word 0xE1A01000, 0xE1A06786, 0xE186C8AC, 0xE0276007\n"
        ".word 0xE022C8AC, 0xE19CC006, 0x0A00000E, 0xE2831902\n"
        ".word 0xE2811D51, 0xE3A06000, 0xE8911008, 0xE2801001\n"
        ".word 0xE1A0C78C, 0xE18C38A3, 0xE026C006, 0xE02238A3\n"
        ".word 0xE193300C, 0x0A000003, 0xE2800002, 0xE1550000\n"
        ".word 0xCAFFFFE4, 0xE1A01000, 0xE1550001, 0xCA00000B\n"
        ".word 0xE3A02001, 0xE1A01002, 0xE2820E46, 0xEB02AA0A\n"
        ".word 0xE28A0C13, 0xE0841185, 0xE1C029D0, 0xE2810B25\n"
        ".word 0xE2855001, 0xE3550003, 0xE1C023F8, 0xAA000008\n"
        ".word 0xE59405B4, 0xE2899001, 0xE1500009, 0x8AFFFFA9\n"
        ".word 0xEA000003, 0xE59F33D8, 0xE59D0008, 0xE3A02008\n"
        ".word 0xFB03634A, 0xE59405B4, 0xE3A02000, 0xE3500000\n"
        ".word 0x9A00004B, 0xE59D0068, 0xE3A03000, 0xE5900000\n"
        ".word 0xE3500000, 0x12001001, 0x03A01000, 0x13510000\n"
        ".word 0xDA000011, 0xE084C182, 0xE28C5A01, 0xE595C390\n"
        ".word 0xE5955394, 0xE1A05785, 0xE185C8AC, 0xE1A0C8AC\n"
        ".word 0xE0845083, 0xE2855C62, 0xE3A06000, 0xE1D557B8\n"
        ".word 0xE0266006, 0xE025500C, 0xE1955006, 0x0A00001F\n"
        ".word 0xE2833001, 0xE1510003, 0xCAFFFFF4, 0xE1500001\n"
        ".word 0x9A000019, 0xE0843182, 0xE283CA01, 0xE28CCE39\n"
        ".word 0xE89C1008, 0xE1A0C78C, 0xE18C38A3, 0xE1A0C8A3\n"
        ".word 0xE0843081, 0xE2836C62, 0xE3A07000, 0xE1D657B8\n"
        ".word 0xE0277007, 0xE1A03001, 0xE025500C, 0xE1955007\n"
        ".word 0x0A00000A, 0xE1D657BA, 0xE3A06000, 0xE0266006\n"
        ".word 0xE025500C, 0xE1955006, 0xE2813001, 0x0A000003\n"
        ".word 0xE2811002, 0xE1500001, 0x8AFFFFEC, 0xE1A03001\n"
        ".word 0xE1500003, 0x8A00000E, 0xE0840182, 0xE2801A01\n"
        ".word 0xE2811E39, 0xE8910003, 0xE1A01781, 0xE18108A0\n"
        ".word 0xE0841083, 0xE2811C62, 0xE1A008A0, 0xE1C107B8\n"
        ".word 0xE59D0068, 0xE5900000, 0xE2801001, 0xE59D0068\n"
        ".word 0xE5801000, 0xE59405B4, 0xE2822001, 0xE1500002\n"
        ".word 0x8AFFFFB3, 0xE59D0058, 0xE1D001D7, 0xE3500000\n"
        ".word 0xDA000005, 0xE59D0068, 0xE59D1068, 0xE5900000\n"
        ".word 0xE350000A, 0x83A0000A, 0xE5810000, 0xE3A07001\n"
        ".word 0xE58D7004, 0xE59D0068, 0xE58D7000, 0xE1A03007\n"
        ".word 0xE3A0200A, 0xE5901000, 0xE59D001C, 0xEB0301DF\n"
        ".word 0xE58D7004, 0xE59D0068, 0xE58D7000, 0xE3A03004\n"
        ".word 0xE3A02001, 0xE5901000, 0xE59D0060, 0xEB0301D7\n"
        ".word 0xE5940400, 0xE3500002, 0x0A000006, 0xE59D0084\n"
        ".word 0xE3A01000, 0xE1D007F8, 0xEB02FB7D, 0xE3A00001\n"
        ".word 0xE320F000, 0xEB02F95C, 0xE51F0630, 0xE5905000\n"
        ".word 0xE5D50420, 0xE3500001, 0x0A000007, 0xEB0306F8\n"
        ".word 0xE2806011, 0xE5D60000, 0xE200107F, 0xE3510001\n"
        ".word 0xE1C773A0, 0x0A000005, 0xEA000015, 0xE320F000\n"
        ".word 0xEB0306EF, 0xE2806012, 0xE320F000, 0xEAFFFFF4\n"
        ".word 0xE59F01B0, 0xE3570000, 0xE7901005, 0x0A000007\n"
        ".word 0xE2850A06, 0xE59F31A0, 0xE3A02002, 0xE2800F9E\n"
        ".word 0xFB0362BA, 0xE320F000, 0xE320F000, 0xEA000004\n"
        ".word 0xE2850A06, 0xE59F3184, 0xE3A02002, 0xE2800F9E\n"
        ".word 0xFB0362B2, 0xE5D60000, 0xE200007F, 0xE3500002\n"
        ".word 0x1A000010, 0xE59F015C, 0xE3570000, 0xE7901005\n"
        ".word 0x0A000007, 0xE2850A06, 0xE59F3154, 0xE3A02002\n"
        ".word 0xE2800F9E, 0xFB0362A5, 0xE320F000, 0xE320F000\n"
        ".word 0xEA000004, 0xE2850A06, 0xE59F3138, 0xE3A02002\n"
        ".word 0xE2800F9E, 0xFB03629D, 0xE5D60000, 0xE200007F\n"
        ".word 0xE3500031, 0x1A000010, 0xE59F0108, 0xE3570000\n"
        ".word 0xE7901005, 0x0A000007, 0xE2850A06, 0xE59F3108\n"
        ".word 0xE3A02002, 0xE2800F9E, 0xFB036290, 0xE320F000\n"
        ".word 0xE320F000, 0xEA000004, 0xE2850A06, 0xE59F30EC\n"
        ".word 0xE3A02002, 0xE2800F9E, 0xFB036288, 0xE5D60000\n"
        ".word 0xE200007F, 0xE3500003, 0x1A000010, 0xE59F00B4\n"
        ".word 0xE3570000, 0xE7901005, 0x0A000007, 0xE2850A06\n"
        ".word 0xE59F30BC, 0xE3A02002, 0xE2800F9E, 0xFB03627B\n"
        ".word 0xE320F000, 0xE320F000, 0xEA000004, 0xE2850A06\n"
        ".word 0xE59F30A0, 0xE3A02002, 0xE2800F9E, 0xFB036273\n"
        ".word 0xE5940400, 0xE3500005, 0x1A00000A, 0xE59D0074\n"
        ".word 0xE5D00050, 0xE3500000, 0x0A000006, 0xE2840E5B\n"
        ".word 0xE8900003, 0xE1500001, 0xE59D1078, 0x93A0000C\n"
        ".word 0x83A00002, 0xE5810000, 0xE59D1088, 0xE3A00000\n"
        ".word 0xE5C10000, 0xE51F0800, 0xE3A01000, 0xEB036FC1\n"
        ".word 0xE320F000, 0xE320F000, 0xEAFFFB49, 0xE28DD0AC\n"
        ".word 0xE8BD8FF0, 0x00000894, 0x000008DB, 0x002DCF34\n"
        ".word 0x0001FFFC, 0x002D0498, 0x00006670, 0x00207280\n"
        ".word 0x002E4ABC, 0x001D1C78, 0x002C6E04, 0x00219624\n"
        ".word 0x002F2878, 0x001F643C, 0x002DCEAC\n");
}

} // namespace smt4::camp
