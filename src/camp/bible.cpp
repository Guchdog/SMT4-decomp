#include "camp/bible.h"
#include "ui/status_down.h"

extern "C" {
    u32   engine_func_002c583c(u32);
    void* AsdMem_Alloc(u32, u32, u32, u32, u32); // 0x002c4b84
    void  unite_func_0022e490(void*);
    void  camp_func_0029e01c(u32);
    void  engine_func_00240e1c(u32);
    void* AsdMemory_func_002c23f8(u32 size);
    void  unite_func_002333bc(void*);
    void  unite_func_00233804(void*, u32, u32, u32);
    u32   unite_func_0034232c(u32);
    void  unite_func_003a8cc0(void*);
    void  unite_func_003aad60(void*);
    void  unite_func_0022df7c(void*, u32);
    s32   unite_func_002338ac(void*);
    void  unite_func_00233600(void*);
    void  camp_func_002976ac(u32);
    void  unite_func_00232800(void*, u32, u32, u32);
}

namespace smt4::camp {

BibleMainManager g_BibleMainManager = {nullptr};

// DECOMP_FUNC(0x00269cc8, 352)
void bibleMain_Init() {
    engine_func_002c583c(0);

    auto* const work = reinterpret_cast<BibleMainWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(BibleMainWork), 1)
    );
    auto* const mgr = reinterpret_cast<BibleMainManager*>(0x0043DA10);
    mgr->work = work;

    work->flag_0d = 0;
    work->flag_0c = 0;
    work->state = 1;
    work->flag_14 = 1;

    using CreateCalc = void* (*)(const char*, u32, u32, u32, void*, void*, void*);
    using CreateDraw = void* (*)(const char*, u32, u32, u32, void*, u32, void*, void*);

    work->proc_task = reinterpret_cast<CreateCalc>(0x002C5978)(
        "BibleMainProc", 2, 0, 0,
        reinterpret_cast<void*>(0x001E4640),
        reinterpret_cast<void*>(0x002C9D40),
        work
    );

    work->draw_up_task = reinterpret_cast<CreateDraw>(0x002C4C00)(
        "BibleDrawUp", 0x6F, 1, 0,
        reinterpret_cast<void*>(0x0020EC04),
        0,
        mgr->work,
        work->proc_task
    );

    work->draw_down_task = reinterpret_cast<CreateDraw>(0x002C4C00)(
        "BibleDrawDown", 0xE6, 1, 0,
        reinterpret_cast<void*>(0x002C9DA4),
        0,
        mgr->work,
        work->proc_task
    );
}


// DECOMP_FUNC(0x003a9200, 948)
void bibleAnalyze_Init(BibleAnalyzeWork* work) {
    auto* const bytes = reinterpret_cast<u8*>(work);
    bytes[0x94] = 0;
    *reinterpret_cast<u16*>(bytes + 0xa5b0) = 0xFFFF;
    bytes[0xa6be] = 0xFF;

    unite_func_0022e490(bytes + 0x5a8);

    // Virtual call: work->vtable[8](work)
    void** vtable = *reinterpret_cast<void***>(work);
    reinterpret_cast<void(*)(BibleAnalyzeWork*)>(vtable[8])(work);

    camp_func_0029e01c(6);

    const u8 view_mode = bytes[0x5a4];
    if (view_mode == 1) {
        engine_func_00240e1c(0);
    }

    // Task context allocation (4 bytes)
    void* const ctx = AsdMem_Alloc(0x100, 0x100, 0, 4, 1);
    *reinterpret_cast<void**>(0x0043D990) = ctx;
    *reinterpret_cast<BibleAnalyzeWork**>(ctx) = work;

    using CreateCalc = void* (*)(const char*, u32, u32, u32, void*, void*, void*);
    using CreateDraw = void* (*)(const char*, u32, u32, u32, void*, u32, void*, void*);

    void* const calc_task = reinterpret_cast<CreateCalc>(0x002C5978)(
        "BIBLE ANALYZE CALC", 2, 0, 0,
        reinterpret_cast<void*>(0x003AC930),
        reinterpret_cast<void*>(0x003AC908),
        ctx
    );
    *reinterpret_cast<void**>(bytes + 0x04) = calc_task;

    void* const draw_up = reinterpret_cast<CreateDraw>(0x002C4C00)(
        "BIBLE ANALYZE UP", 0x6F, 1, 0,
        reinterpret_cast<void*>(0x003ACC4C),
        0,
        ctx,
        calc_task
    );
    *reinterpret_cast<void**>(bytes + 0x08) = draw_up;

    void* const draw_down = reinterpret_cast<CreateDraw>(0x002C4C00)(
        "BIBLE ANALYZE DOWN", 0xE6, 1, 0,
        reinterpret_cast<void*>(0x003AD00C),
        0,
        ctx,
        calc_task
    );
    *reinterpret_cast<void**>(bytes + 0x0C) = draw_down;

    u8* const sub = reinterpret_cast<u8*>(AsdMemory_func_002c23f8(0x68));
    if (sub != nullptr) {
        unite_func_002333bc(sub);
    }
    *reinterpret_cast<void**>(bytes + 0x590) = sub;

    u32 count_arg = *reinterpret_cast<const u32*>(bytes + 0x28);
    if (count_arg >= 10) {
        count_arg = 10;
    }

    if (view_mode != 0) {
        if (sub != nullptr) {
            *reinterpret_cast<void**>(sub) = reinterpret_cast<void*>(0x00421FDC);
            *reinterpret_cast<void**>(sub + 0x64) = bytes + 0xc8;
        }
        unite_func_00233804(bytes + 0x55c, 0x1C, 0x1030, count_arg);
        bytes[0x56c] = 1;

        u16 match_count = 0;
        const u32 target_demon = *reinterpret_cast<const u32*>(bytes + 0xa5b4);
        for (u32 id = 1; id < 60; ++id) {
            if (unite_func_0034232c(id) != 0) {
                *reinterpret_cast<u16*>(bytes + 0xa5ba + match_count * 2) = static_cast<u16>(id);
                if (target_demon == id) {
                    *reinterpret_cast<u16*>(bytes + 0xa6bc) = match_count;
                }
                match_count++;
            }
        }
        *reinterpret_cast<u16*>(bytes + 0xa6ba) = match_count;
    } else {
        if (sub != nullptr) {
            *reinterpret_cast<void**>(sub) = reinterpret_cast<void*>(0x0042207C);
            void** sub_vtable = *reinterpret_cast<void***>(sub);
            reinterpret_cast<void(*)(void*, void*)>(sub_vtable[2])(sub, bytes + 0x20);

            u16* flag_ptr = reinterpret_cast<u16*>(sub + 4);
            *flag_ptr |= 0x1000;
            *reinterpret_cast<void**>(sub + 0x64) = bytes + 0xc8;
        }
        unite_func_00233804(bytes + 0x55c, 0x1D, 0x40E, count_arg);
        bytes[0x56c] = 1;
    }

    unite_func_003a8cc0(work);
    unite_func_003aad60(bytes + 0x96);
    unite_func_0022df7c(bytes + 0x96, 0);

    const s32 num_items = unite_func_002338ac(bytes + 0x20);
    for (s32 i = 0; i < num_items; ++i) {
        const s16 item_id = *reinterpret_cast<const s16*>(bytes + 0x5a8 + i * 32 + 4);
        if (item_id != 0) {
            unite_func_0022df7c(bytes + 0x96, static_cast<u16>(item_id));
        }
    }

    unite_func_00233600(bytes + 0xdc);
    camp_func_002976ac(0x22);

    if (view_mode != 0) {
        unite_func_00232800(bytes + 0xc8, 0x140, 0, 0x1C);
    } else {
        unite_func_00232800(bytes + 0xc8, 0x140, 0, 0x1D);
    }

    *reinterpret_cast<u32*>(bytes + 0x14) = 0;
    *reinterpret_cast<u32*>(bytes + 0x18) = 0;
}

} // namespace smt4::camp
