#include <cstdint>

typedef uint32_t u32;
typedef int32_t  s32;
typedef int8_t   s8;
typedef uint8_t  u8;

extern "C" {
    void* AsdMem_Alloc_002c4b84(u32 heap, u32 flag, u32 unused, u32 size, u32 align);
    void  NameMain_Helper_003986c8(void* ptr, s32 mode);
    void* AsdTask_Create_002c5978(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);
    void* AsdTask_CreateDraw_002c4c00(const char* name, u32 prio, u32 f1, u32 f2, void* cb, void* work, u32 parent);

    extern void* g_NameMainManager_0044d180[];
}

extern "C" void h7_script_namemain_init_candidate(void* arg0, s32 arg1) {
    u8* work = static_cast<u8*>(AsdMem_Alloc_002c4b84(0x100, 0xB1, 0, 0x960, 1));
    g_NameMainManager_0044d180[1] = work;

    if (!work) return;

    if (arg0) {
        NameMain_Helper_003986c8(work + 0x10, static_cast<s32>(*static_cast<s8*>(arg0)));
    }

    void* proc_task = AsdTask_Create_002c5978("NameMainProc", 2, 0, 0, reinterpret_cast<void*>(0x0021F1AC), work, 0);
    *reinterpret_cast<void**>(work) = proc_task;

    u32 tag1 = 0x7A;
    u32 tag2 = 0xD8;
    if (arg0 && *static_cast<s32*>(arg0) == 1) {
        tag1 = 0x80;
        tag2 = 0xDE;
    }

    AsdTask_CreateDraw_002c4c00("NameDrawUp", tag1, 1, 0, reinterpret_cast<void*>(0x001D947C), work, 0);
    AsdTask_CreateDraw_002c4c00("NameDrawUp", tag2, 1, 0, reinterpret_cast<void*>(0x001FE08C), work, 0);

    void* draw_down = AsdTask_CreateDraw_002c4c00("NameDrawDown", 0xE6, 1, 0, reinterpret_cast<void*>(0x0021F1C4), work, 0);
    *reinterpret_cast<void**>(work + 8) = draw_down;
}

extern "C" void h7_script_namemain_init_mutation(void* arg0, s32 arg1) {
    g_NameMainManager_0044d180[1] = reinterpret_cast<void*>(0xDEADBEEF);
}
