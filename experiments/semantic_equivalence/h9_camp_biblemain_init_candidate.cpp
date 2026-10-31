#include <cstdint>

typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);

    extern void* g_BibleMainWork_0043da10;
}

struct BibleMainWork {
    void* proc_task;
    void* draw_up_task;
    void* draw_down_task;
    u8 flag_0c;
    u8 flag_0d;
    u8 pad[2];
    u32 state;
    u8 flag_14;
    u8 pad2[11];
};

extern "C" void h9_camp_biblemain_init_candidate() {
    BibleMainWork* work = static_cast<BibleMainWork*>(AsdMem_Alloc_002c4b84(0x100, 0x100, 0, 0x20, 1));
    g_BibleMainWork_0043da10 = work;
    if (!work) return;

    work->flag_0c = 0;
    work->flag_0d = 0;
    work->state = 1;
    work->flag_14 = 1;

    void* calc = AsdTask_Create_002c5978("BibleMainProc", 2, 0, 0, reinterpret_cast<void*>(0x001E4640), work, 0);
    work->proc_task = calc;

    work->draw_up_task = AsdTask_CreateDraw_002c4c00("BibleDrawUp", 0x6F, 1, 0, reinterpret_cast<void*>(0x0020EC04), work, reinterpret_cast<u32>(calc));
    work->draw_down_task = AsdTask_CreateDraw_002c4c00("BibleDrawDown", 0xE6, 1, 0, reinterpret_cast<void*>(0x002C9DA4), work, reinterpret_cast<u32>(calc));
}

extern "C" void h9_camp_biblemain_init_mutation() {
    g_BibleMainWork_0043da10 = reinterpret_cast<void*>(0xDEADBEEF);
}
